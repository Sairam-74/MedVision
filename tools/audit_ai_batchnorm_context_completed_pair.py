"""Frozen E13/E14 TRAIN-only normalization-context diagnosis, not training.

Compare running-statistics evaluation against temporary batch-statistics BN.
All parameters/buffers and checkpoint/cache bytes must remain unchanged.
No validation/calibration/test image tensors are loaded; no candidate is made.
"""
import os
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

import cv2
import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import medvision_pipeline as p
from tools.ai_atomic_io import json_atomic
from tools.ai_cached_dataset import CachedReliabilityDataset
from tools.ai_presence_model import PresenceAttentionUNet, tensor_digest

ARMS = {'E13': 'AI_E13_v3_foreground_BCE_reference', 'E14': 'AI_E14_v3_foreground_BCE5'}
SAMPLE_CONFIG = 'experiments/AI_FOREGROUND_GRADIENTS_E11_E12_20261009/config.json'
SAMPLE_SHA = 'a0b32cc3df630b59e5533e584c1ee4ef1ff1d256fa1b88c17ee466b99bb03bbe'
PROTOCOL = 'experiments/session_20261007_ai_loop_01/FOREGROUND_BCE_EXPERIMENT_PROTOCOL.json'
PROTOCOL_SHA = '250bcd50e0ba8463d6da746e469222b41a82b8114ec1add1aece6fd04850e523'
STRATA = ('hard_positive', 'ordinary_positive', 'hard_negative', 'ordinary_negative')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def verify(hashes):
    for name, digest in hashes.items():
        if p.sha(ROOT/name) != digest:
            raise ValueError('Frozen diagnostic input changed: '+name)


def describe(logits, target, valid):
    q = logits.sigmoid()
    fg, bg = target.bool() & valid.bool(), ~target.bool() & valid.bool()
    mask = (q >= .5) & valid.bool()
    tp, fp, fn = int((mask & fg).sum()), int((mask & bg).sum()), int((~mask & fg).sum())
    return dict(mask_TP=tp, mask_FP=fp, mask_FN=fn, predicted_positive=bool(tp+fp),
                any_target_overlap=bool(tp), target_pixels=int(fg.sum()),
                grid_dice=2*tp/(2*tp+fp+fn) if tp+fn else None,
                grid_iou=tp/(tp+fp+fn) if tp+fn else None,
                grid_precision=tp/(tp+fp) if tp+fp else 0.,
                grid_recall=tp/(tp+fn) if tp+fn else None,
                max_pixel_probability_proxy=float(q[valid.bool()].max()),
                foreground_probability_mean=float(q[fg].mean()) if bool(fg.any()) else None,
                foreground_probability_median=float(q[fg].median()) if bool(fg.any()) else None)


def aggregate(records):
    tp = sum(r['mask_TP'] for r in records)
    fp = sum(r['mask_FP'] for r in records)
    fn = sum(r['mask_FN'] for r in records)
    positive = [r for r in records if r['target_pixels']]
    return dict(n=len(records), alerts=sum(r['predicted_positive'] for r in records),
                any_target_overlap=sum(r['any_target_overlap'] for r in positive),
                TP_pixels=tp, FP_pixels=fp, FN_pixels=fn,
                mean_positive_grid_dice=float(np.mean([r['grid_dice'] for r in positive])) if positive else None,
                mean_positive_grid_iou=float(np.mean([r['grid_iou'] for r in positive])) if positive else None,
                global_pixel_recall=tp/(tp+fn) if tp+fn else None,
                global_pixel_precision=tp/(tp+fp) if tp+fp else 0.)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if ROOT not in out.parents or out.exists():
        raise ValueError('Exclusive NEW workspace output required')
    if p.sha(ROOT/SAMPLE_CONFIG) != SAMPLE_SHA or p.sha(ROOT/PROTOCOL) != PROTOCOL_SHA:
        raise ValueError('Exact completed protocol and previously fixed TRAIN sample required')
    queue_path = ROOT/'experiments/session_20261007_ai_loop_01/foreground_bce_queue.json'
    queue = read_json(queue_path)
    if queue['status'] != 'completed_training_and_native_audits_only':
        raise ValueError('Previous queue must be terminal')
    guards = queue['guards']
    verify(guards)
    pair = ROOT/'experiments/AI_E13_E14_FOREGROUND_BCE_PAIR'
    completion = read_json(pair/'completion.json')
    if completion['status'] != 'completed' or p.sha(pair/'comparison.json') != completion['comparison_sha256']:
        raise ValueError('Completed paired result required')
    configs, bundles, checkpoint_hashes = {}, {}, {}
    input_paths = [ROOT/SAMPLE_CONFIG, ROOT/PROTOCOL, queue_path, pair/'completion.json', pair/'comparison.json']
    for arm, name in ARMS.items():
        run = ROOT/'experiments'/name
        state = read_json(run/'state.json')
        if state['status'] != 'completed' or state['epochs_finished'] != 12:
            raise ValueError('Both completed 12-epoch runs required')
        configs[arm] = read_json(run/'config.json')
        bundles[arm] = read_json(run/'bundle.json')
        checkpoint_hashes[arm] = p.sha(run/'best_model.pt')
        if checkpoint_hashes[arm] != bundles[arm]['checkpoint_sha256']:
            raise ValueError('Selected checkpoint hash mismatch')
        input_paths += [run/name for name in ('state.json','config.json','bundle.json','best_model.pt')]
    if [k for k in configs['E13'] if configs['E13'][k] != configs['E14'][k]] != ['foreground_bce_coefficient']:
        raise ValueError('Only registered foreground coefficient may differ')
    config = configs['E13']
    if (config['foreground_bce_coefficient'], configs['E14']['foreground_bce_coefficient']) != (1,5):
        raise ValueError('Exact coefficient pair required')
    if config['protocol_sha256'] != PROTOCOL_SHA or config['presence_weight'] != 0 or config['hard_factor'] != 2:
        raise ValueError('Frozen mask-only configuration required')
    manifest = ROOT/config['manifest']
    data = CachedReliabilityDataset(ROOT/config['cache'], manifest,
                                   p.PreprocessConfig(**config['preprocess']), seed=42, elastic=False)
    if len(data) != 2808 or sum(int(r['fractured']) for r in data.rows) != 493:
        raise ValueError('Exact TRAIN membership required')
    if p.sha(data.cache/'completion.json') != config['cache_completion_sha256']:
        raise ValueError('Exact registered TRAIN cache required')
    sample_config = read_json(ROOT/SAMPLE_CONFIG)
    if sample_config['preprocess'] != asdict(data.config) or sample_config['manifest_sha256'] != p.sha(manifest):
        raise ValueError('Sample configuration differs from frozen TRAIN partition')
    samples = sample_config['samples']
    if len(samples) != 32 or len({r['image_id'] for r in samples}) != 32:
        raise ValueError('Same 32 distinct previously fixed TRAIN sources required')
    catalog = ROOT/config['hard_catalog']
    hp = set(read_json(catalog/'HARD_POSITIVE_SET.json')['image_ids'])
    hn = set(read_json(catalog/'HARD_NEGATIVE_SET.json')['image_ids'])
    if len(hp) != 109 or len(hn) != 713:
        raise ValueError('Unchanged hard membership required')
    cohorts = {k:[s for s in samples if s['stratum']==k] for k in STRATA}
    for sample in samples:
        row = data.rows[sample['train_index']]
        positive = bool(int(row['fractured']))
        expected = ('hard_positive' if row['image_id'] in hp else 'ordinary_positive') if positive else (
                    'hard_negative' if row['image_id'] in hn else 'ordinary_negative')
        if row['image_id'] != sample['image_id'] or row['split'] != 'train' or expected != sample['stratum']:
            raise ValueError('TRAIN-only sample identity/stratum mismatch')
    if any(len(c) != 8 for c in cohorts.values()):
        raise ValueError('Eight fixed samples per stratum required')
    sources = ['tools/audit_ai_batchnorm_context_completed_pair.py','tools/ai_cached_dataset.py',
               'tools/ai_presence_model.py','tools/ai_atomic_io.py','medvision_ai.py','medvision_pipeline.py']
    source_hashes = {name:p.sha(ROOT/name) for name in sources}
    input_paths += [manifest, data.cache/'completion.json', data.cache/'rows.json']
    input_hashes = {str(path.relative_to(ROOT)):p.sha(path) for path in input_paths}
    if not torch.cuda.is_available():
        raise RuntimeError('Verified CUDA required')
    torch.set_num_threads(2)
    cv2.setNumThreads(1)
    p.seed_everything(42)
    out.mkdir()
    json_atomic(out/'config.json',dict(samples=samples, samples_config_sha256=SAMPLE_SHA,
        selected_epochs={a:dict(epoch=b['epoch'],global_epoch=b['global_epoch']) for a,b in bundles.items()},
        checkpoint_hashes=checkpoint_hashes, source_hashes=source_hashes, input_hashes=input_hashes,
        completed_queue_guard_count=len(guards), completed_protocol_sha256=PROTOCOL_SHA,
        conditions=['running_statistics_eval','temporary_BN_batch_statistics_with_four_partner_strata'],
        partners='cohort[index mod 8]; next member if identical to anchor',
        batch_size=2, augmentation=False, no_optimizer_steps=True, BN_running_buffers_updates=False,
        whole_model_remains_eval_except_temporary_BN_flags=True, CUDA=True,
        validation_images_read=0, calibration_images_read=0, test_images_read=0, model_trained=False))
    records, invariants, summaries = [], {}, {}
    started = time.perf_counter()

    def infer(model, anchor, partner):
        x = torch.from_numpy(np.stack([data.arrays['image'][s['train_index']].astype(np.float32,copy=True)
                                     for s in (anchor,partner)])).unsqueeze(1).to('cuda')
        with torch.inference_mode():
            logits = model(x)['mask_logits'][0:1]
        if not bool(torch.isfinite(logits).all()):
            raise ValueError('Finite diagnostic output required')
        return logits

    for arm, run_name in ARMS.items():
        model = PresenceAttentionUNet().to('cuda')
        model.load_state_dict(torch.load(ROOT/'experiments'/run_name/'best_model.pt', map_location='cpu', weights_only=True), strict=True)
        model.eval()
        before = tensor_digest(model.state_dict())
        module_modes = [(module,module.training) for module in model.modules()]
        BN_metadata = [(module,module.eps,module.momentum) for module in model.modules()
                       if isinstance(module,nn.BatchNorm2d)]
        flags = [(module, module.training, module.track_running_stats) for module in model.modules()
                 if isinstance(module,nn.BatchNorm2d)]
        if not flags or any(training or not track for _,training,track in flags):
            raise ValueError('Expected frozen evaluation BatchNorm required')
        arm_records = []
        try:
            for index, anchor in enumerate(samples):
                partners = {}
                for name, cohort in cohorts.items():
                    partner = cohort[index % 8]
                    if partner['image_id'] == anchor['image_id']:
                        partner = cohort[(index+1) % 8]
                    if partner['image_id'] == anchor['image_id']:
                        raise ValueError('Distinct partner required')
                    partners[name] = partner
                y, v = [torch.from_numpy(data.arrays[k][anchor['train_index']].astype(np.float32,copy=True)).unsqueeze(0).unsqueeze(0).to('cuda')
                        for k in ('target','valid')]
                baseline = infer(model,anchor,partners['ordinary_negative'])
                repeated = infer(model,anchor,partners['hard_positive'])
                eval_delta = float((baseline-repeated).abs().max())
                baseline_record = describe(baseline,y,v)
                batch_records, logits_list = {}, []
                for module,_,_ in flags:
                    module.training = True
                    module.track_running_stats = False
                try:
                    for name, partner in partners.items():
                        logits = infer(model,anchor,partner)
                        logits_list.append(logits)
                        batch_records[name] = dict(partner_image_id=partner['image_id'], **describe(logits,y,v),
                                                   max_abs_logit_change_from_eval=float((logits-baseline).abs().max()))
                finally:
                    for module,training,track in flags:
                        module.training, module.track_running_stats = training,track
                span = torch.stack(logits_list).amax(dim=0)-torch.stack(logits_list).amin(dim=0)
                record = dict(arm=arm, **anchor, running_statistics=baseline_record,
                              alternate_eval_partner_max_abs_logit_delta=eval_delta,
                              alternate_eval_partner_valid_mask_pixels_changed=int((((baseline.sigmoid()>=.5) != (repeated.sigmoid()>=.5)) & v.bool()).sum()),
                              batch_statistics=batch_records, max_logit_span_across_batch_partners=float(span.max()),
                              partner_changes_alert=len({r['predicted_positive'] for r in batch_records.values()})>1,
                              partner_changes_any_target_overlap=len({r['any_target_overlap'] for r in batch_records.values()})>1)
                arm_records.append(record)
                records.append(record)
        finally:
            for module,training,track in flags:
                module.training, module.track_running_stats = training,track
        after = tensor_digest(model.state_dict())
        restored = all(module.training == training and module.track_running_stats == track for module,training,track in flags)
        restored = restored and all(module.training == training for module,training in module_modes)
        restored = restored and all(module.eps == eps and module.momentum == momentum for module,eps,momentum in BN_metadata)
        if before != after or not restored or any(param.grad is not None for param in model.parameters()):
            raise ValueError('Model weights/buffers/flags/gradients must remain unchanged')
        invariants[arm] = dict(before_sha256=before,after_sha256=after,exactly_unchanged=True,
                               BN_modules=len(flags),BN_flags_restored=restored,parameter_gradients_absent=True,
                               all_module_training_flags_and_BN_eps_momentum_unchanged=True)
        summaries[arm] = {}
        for stratum in STRATA:
            subset = [r for r in arm_records if r['stratum']==stratum]
            summaries[arm][stratum] = dict(
                running_statistics=aggregate([r['running_statistics'] for r in subset]),
                batch_statistics_by_partner={k:aggregate([r['batch_statistics'][k] for r in subset]) for k in STRATA},
                partner_changes_alert=sum(r['partner_changes_alert'] for r in subset),
                partner_changes_any_target_overlap=sum(r['partner_changes_any_target_overlap'] for r in subset),
                max_alternate_eval_partner_logit_delta=max(r['alternate_eval_partner_max_abs_logit_delta'] for r in subset),
                max_BN_batch_partner_logit_span=max(r['max_logit_span_across_batch_partners'] for r in subset))
        print(json.dumps(dict(arm=arm, frozen_model_exactly_unchanged=True, unique_TRAIN_sources=32)),flush=True)
        del model, baseline, repeated, logits, logits_list, span, y, v
        torch.cuda.empty_cache()
    verify(source_hashes)
    verify(input_hashes)
    verify(guards)
    for name,digest in data.metadata['cache_hashes'].items():
        if p.sha(data.cache/(name+'.npy')) != digest:
            raise ValueError('Read-only TRAIN cache changed')
    json_atomic(out/'per_case.json',records)
    json_atomic(out/'summary.json',dict(summary=summaries, frozen_model_invariants=invariants,
        actual_unique_TRAIN_sources=32, forward_calls=384, source_presentations=768,
        elapsed_seconds=time.perf_counter()-started, no_optimizer_steps=True,
        validation_images_read=0, calibration_images_read=0, test_images_read=0,
        model_trained=False, factor_selected=False, improvement_claim=False,
        limitations=['32 selected reused TRAIN sources are exploratory, not population-representative.',
                    'Temporary batch-statistics inference depends on partner images and is not deployable.',
                    'Differences do not prove normalization is the primary bottleneck or that a replacement helps.',
                    'Grid measurements are not native validation localization, clinical reliability or calibration.',
                    'The two selected checkpoint epochs differ; no new controlled training comparison occurred.']))
    json_atomic(out/'completion.json',dict(status='completed_TRAIN_only_frozen_BN_context_diagnosis',
        config_sha256=p.sha(out/'config.json'), per_case_sha256=p.sha(out/'per_case.json'),
        summary_sha256=p.sha(out/'summary.json'),source_sha256=p.sha(Path(__file__)),
        completed_queue_guards_verified_unchanged=len(guards), model_tensors_and_buffers_unchanged=True,
        BN_flags_restored=True, no_optimizer_steps=True, model_trained=False, promotion=False,
        validation_images_read=0, calibration_images_read=0, test_images_read=0))
    print(json.dumps(dict(status='completed_TRAIN_only_BN_context_diagnosis', elapsed_seconds=time.perf_counter()-started)),flush=True)


if __name__ == '__main__':
    main()
