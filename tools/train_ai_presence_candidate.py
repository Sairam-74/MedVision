"""Registered E7/E8 matched presence-supervision ablation, TRAIN/VAL only."""
import os
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time
import cv2
import numpy as np
import psutil
import torch
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import medvision_pipeline as p
from tools.ai_cached_dataset import CachedReliabilityDataset
from tools.ai_presence_model import PresenceAttentionUNet, CONTRACT, ARCHITECTURE, balanced_presence_loss, tensor_digest, review_group, selection_key
from tools.train_reliability_candidate import candidate_loss, case_counts
from tools.run_experiment import summary
from tools import ai_metrics as a
from tools.ai_atomic_io import json_atomic, atomic_save

MANIFEST = ROOT/'experiments/data_v3_reliability_20261007/manifest.json'
MANIFEST_SHA = '4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318'
INIT = ROOT/'experiments/AI_E5_v3_BCE_reference/best_model.pt'
INIT_SHA = '4bf4065a256c412c735895b26b42f3b5c1ef862f89376973236c66f43acb0ba7'
PROTOCOL = ROOT/'experiments/session_20261007_ai_loop_01/PRESENCE_EXPERIMENT_PROTOCOL_r2.json'


def validate(model, dataset, preprocess, post, device, supervised):
    masks, alerts, heads, groups = [], [], [], Counter()
    model.eval()
    with torch.inference_mode():
        for i, row in enumerate(dataset.rows):
            image, target = dataset.native(i)
            x, _, _, geometry = p.prepare(image, preprocess)
            outputs = model(torch.from_numpy(x)[None, None].to(device))
            if not all(torch.isfinite(v).all() for v in outputs.values()):
                raise RuntimeError('Nonfinite validation output')
            native = p.inverse(outputs['mask_logits'].sigmoid()[0,0].cpu().numpy(), geometry, probability=True)
            _, mask = p.postprocess(native, post)
            case = dict(case_counts(row, mask, target), case_score=float(native.max()))
            head_score = float(outputs['presence_logits'].sigmoid()[0]) if supervised else None
            head_positive = bool(head_score >= .5) if supervised else None
            mask_positive = case['prediction_present']
            alert = mask_positive or bool(head_positive)
            group = review_group(head_positive, mask_positive) if supervised else 'reference_mask_only'
            case.update(head_score=head_score, classifier_prediction_present=head_positive,
                        review_alert_present=alert, head_mask_group=group)
            masks.append(case)
            alerts.append(dict(case, prediction_present=alert,
                case_score=max(case['case_score'], head_score) if supervised else case['case_score']))
            if supervised:
                heads.append(dict(case, prediction_present=head_positive, case_score=head_score))
                groups[group+'|'+('fracture' if case['positive'] else 'normal')] += 1
    mask_cl = a.classification(masks)
    mask_cl['score_definition'] = 'Maximum native pixel sigmoid, uncalibrated case proxy'
    alert_cl = a.classification(alerts)
    alert_cl['score_definition'] = 'Conservative head+ OR independent mask+ alert; max of two uncalibrated scores, not a probability' if supervised else mask_cl['score_definition']
    head_cl, head_calibration = None, None
    if supervised:
        head_cl = a.classification(heads)
        head_cl['score_definition'] = 'Supervised presence sigmoid with TRAIN balanced BCE; uncalibrated'
        head_calibration = a.calibration(heads)
        head_calibration['interpretation'] = 'Uncalibrated learned presence output; no clinical probability claim or calibration fit'
    metrics = dict(raw=summary(masks), delivered=summary(masks), classification=alert_cl,
        mask_classification=mask_cl, head_classification=head_cl, head_calibration=head_calibration,
        four_groups_by_truth=dict(groups), mask_gated_by_classifier=False,
        calibration_fit=False, test_evaluated=False, promotion=False)
    return metrics, dict(raw=masks, delivered=masks, review_alert=alerts, head=heads)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--presence-weight', type=int, choices=[0,1], required=True)
    ap.add_argument('--cache', default='experiments/AI_TRAIN_CACHE_v3_256_r2')
    ap.add_argument('--resume', action='store_true')
    args = ap.parse_args()
    out = Path(args.out).resolve()
    if ROOT not in out.parents or out.exists() and not args.resume:
        raise ValueError('Exclusive workspace candidate directory or strict resume required')
    pair = ROOT/'experiments/AI_E5_E6_PAIR_ANALYSIS'
    if not (pair/'completion.json').exists() or not (ROOT/'experiments/AI_AUDIT_E6_v3/completion.json').exists():
        raise ValueError('Current pair must finish and be audited first')
    if not torch.cuda.is_available():
        raise RuntimeError('Registered GPU training requires CUDA; no silent CPU substitution')
    if p.sha(MANIFEST)!=MANIFEST_SHA or p.sha(INIT)!=INIT_SHA:
        raise ValueError('Frozen split/shared initializer changed')
    if json.loads((INIT.parent/'state.json').read_text())['status']!='completed':
        raise ValueError('Warm initializer training incomplete')
    protocol = json.loads(PROTOCOL.read_text())
    expected = protocol['candidate' if args.presence_weight else 'reference']
    if out.name!=expected:
        raise ValueError('Use the registered reference/candidate identity')
    torch.set_num_threads(2)
    cv2.setNumThreads(1)
    p.seed_everything(42)
    preprocess = p.PreprocessConfig(size=256, resize='stretch', clahe=True, blur_kernel=3, normalization='unit')
    post, loss_config = p.PostprocessConfig(), p.LossConfig(mode='bce_dice')
    train = CachedReliabilityDataset(ROOT/args.cache, MANIFEST, preprocess, seed=42, elastic=False)
    if len(train)!=2808 or sum(int(r['fractured']) for r in train.rows)!=493:
        raise ValueError('TRAIN distribution changed')
    archive = ROOT/'FracAtlas.zip'
    document = json.loads(MANIFEST.read_text())
    if p.sha(archive)!=document['archive_sha256']:
        raise ValueError('Original archive differs from manifest')
    val = p.FracDataset(archive, MANIFEST, 'val', preprocess)
    if len(val)!=463 or sum(int(r['fractured']) for r in val.rows)!=83:
        raise ValueError('Validation membership changed')
    sources = ['tools/ai_atomic_io.py','tools/train_ai_presence_candidate.py','tools/ai_presence_model.py','tools/ai_cached_dataset.py',
        'tools/cache_ai_training_inputs.py','tools/train_reliability_candidate.py','tools/ai_metrics.py',
        'tools/run_experiment.py','medvision_pipeline.py','medvision_ai.py']
    config = dict(manifest=str(MANIFEST.relative_to(ROOT)), manifest_sha256=MANIFEST_SHA,
        archive_sha256=document['archive_sha256'], original_checkpoint_sha256=p.sha(ROOT/'best_model.pt'),
        initial_checkpoint=str(INIT.relative_to(ROOT)), initial_checkpoint_sha256=INIT_SHA,
        protocol_sha256=p.sha(PROTOCOL), cache=str(Path(args.cache)), cache_completion_sha256=p.sha(ROOT/args.cache/'completion.json'),
        output_contract=CONTRACT, architecture=ARCHITECTURE, preprocess=asdict(preprocess), postprocess=asdict(post),
        loss='bce_dice', loss_config=asdict(loss_config), normal_bce_weight=1., presence_weight=args.presence_weight,
        class_weights=dict(positive=2808/(2*493), normal=2808/(2*2315)),
        epochs=12, warm_start_epoch=8, batch_size=2, lr=.0001, seed=42, elastic=False, positive_fraction=None,
        optimizer='Adam reset in both arms; no weight decay/scheduler; norm clip10',
        sampling='natural one-pass epoch shuffle; exact cache and online aligned augmentation/fallback',
        device='cuda', torch=torch.__version__, smoke=False,
        cublas_workspace_config=os.environ['CUBLAS_WORKSPACE_CONFIG'],
        source_hashes={s:p.sha(ROOT/s) for s in sources},
        selection='Common feasible-first/minimum-normalized TP,TN,Dice,IoU; conservative review alerts and independent masks; earlier ties',
        calibration_fit=False, test_evaluated=False, promotion=False)
    model = PresenceAttentionUNet()
    model.load_shared(torch.load(INIT, map_location='cpu', weights_only=True))
    initial = dict(full_parameter_sha256=tensor_digest(model.state_dict()),
        shared_parameter_sha256=tensor_digest({k:v for k,v in model.state_dict().items() if not k.startswith('presence.')}),
        added_parameters=sum(v.numel() for v in model.presence.parameters()),
        total_parameters=sum(v.numel() for v in model.parameters()), seed=42)
    model = model.to('cuda')
    optimizer = torch.optim.Adam(model.parameters(), lr=.0001)
    first, best = 1, (-1., -1., -1.)
    if args.resume:
        old = json.loads((out/'config.json').read_text())
        if old != config:
            raise ValueError('Resume code/config/cache/protocol differs')
        checkpoint = torch.load(out/'last.pt', map_location='cuda', weights_only=True)
        if checkpoint['output_contract']!=CONTRACT or checkpoint['manifest_sha256']!=MANIFEST_SHA:
            raise ValueError('Resume checkpoint contract/split mismatch')
        model.load_state_dict(checkpoint['model_state_dict'], strict=True)
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        first, best = checkpoint['epoch']+1, tuple(checkpoint['best_selection_key'])
        records = [json.loads(line) for line in (out/'epochs.jsonl').read_text().splitlines() if line.strip()] if (out/'epochs.jsonl').exists() else []
        if [r['epoch'] for r in records] != list(range(1, first)):
            raise ValueError('Checkpoint/log epoch mismatch; preserve evidence and recover before resume, never skip an unrecorded epoch')
    else:
        out.mkdir()
        json_atomic(out/'config.json', config)
        json_atomic(out/'initial_parameters.json', initial)
        (out/'source_snapshot').mkdir()
        for source in sources:
            (out/'source_snapshot'/Path(source).name).write_bytes((ROOT/source).read_bytes())
        (out/'source_snapshot'/'PRESENCE_EXPERIMENT_PROTOCOL_r2.json').write_bytes(PROTOCOL.read_bytes())
        atomic_save(dict(model_state_dict=model.state_dict(), optimizer_state_dict=optimizer.state_dict(), epoch=0,
            best_selection_key=list(best), output_contract=CONTRACT, manifest_sha256=MANIFEST_SHA), out/'last.pt')
    started = time.perf_counter()
    for epoch in range(first, 13):
        global_epoch = 8+epoch
        p.seed_everything(42+global_epoch)
        train.epoch = global_epoch
        loader = DataLoader(train, batch_size=2, shuffle=True, num_workers=0,
            generator=torch.Generator().manual_seed(42+global_epoch))
        model.train()
        sums, seen = Counter(), 0
        ep_start = time.perf_counter()
        torch.cuda.reset_peak_memory_stats()
        for batch, (x,y,valid,positive) in enumerate(loader,1):
            x,y,valid,positive = [v.to('cuda') for v in (x,y,valid,positive)]
            optimizer.zero_grad(set_to_none=True)
            outputs = model(x)
            components = candidate_loss(outputs['mask_logits'], y, valid, loss_config, 1., positive)
            case_loss = balanced_presence_loss(outputs['presence_logits'], positive)
            total = components['total']+case_loss if args.presence_weight else components['total']
            measured = dict(segmentation_total=components['total'], bce=components['bce'], dice=components['dice'],
                            presence_bce=case_loss, total=total)
            if not all(torch.isfinite(v).all() for v in measured.values()):
                raise RuntimeError('Nonfinite training component')
            total.backward()
            grad = torch.nn.utils.clip_grad_norm_(model.parameters(), 10, error_if_nonfinite=True)
            if not args.presence_weight and any(v.grad is not None for v in model.presence.parameters()):
                raise RuntimeError('Reference head must receive no supervision/update')
            optimizer.step()
            for key, value in measured.items():
                sums[key] += float(value.detach())*len(x)
            seen += len(x)
            if batch==1 or batch%100==0 or batch==len(loader):
                state = dict(status='training', epoch=epoch, global_epoch=global_epoch, batch=batch, batches=len(loader),
                    loss_components={k:v/seen for k,v in sums.items()}, gradient_norm=float(grad),
                    elapsed_seconds=time.perf_counter()-ep_start, smoke=False, test_evaluated=False, promotion=False)
                json_atomic(out/'state.json', state)
                print(json.dumps(state), flush=True)
        json_atomic(out/'state.json', dict(status='validating',epoch=epoch,global_epoch=global_epoch,smoke=False,test_evaluated=False))
        metrics, cases = validate(model, val, preprocess, post, 'cuda', bool(args.presence_weight))
        key = selection_key(metrics)
        selected = key > best
        if selected:
            best = key
        checkpoint = dict(model_state_dict=model.state_dict(), optimizer_state_dict=optimizer.state_dict(),
            epoch=epoch, global_epoch=global_epoch, best_selection_key=list(best), output_contract=CONTRACT,
            manifest_sha256=MANIFEST_SHA, presence_weight=args.presence_weight)
        atomic_save(checkpoint, out/f'epoch_{epoch:03d}_resume.pt')
        atomic_save(checkpoint, out/'last.pt')
        if selected:
            atomic_save(model.state_dict(), out/'best_model.pt')
            json_atomic(out/'best_validation.json', dict(epoch=epoch, global_epoch=global_epoch, metrics=metrics, selection_key=list(key)))
            json_atomic(out/'best_validation_cases.json', cases)
            json_atomic(out/'bundle.json', dict(output_contract=CONTRACT,architecture=ARCHITECTURE,
                checkpoint='best_model.pt',checkpoint_sha256=p.sha(out/'best_model.pt'),epoch=epoch,global_epoch=global_epoch,
                manifest_sha256=MANIFEST_SHA,preprocess=asdict(preprocess),postprocess=asdict(post),
                presence_weight=args.presence_weight,calibration_status='UNSELECTED research; no calibration/freeze/promotion'))
        record = dict(epoch=epoch,global_epoch=global_epoch,loss_components={k:v/seen for k,v in sums.items()},
            validation=metrics,selection_key=list(key),best_selection_key=list(best),selected=selected,
            train_images_seen=seen,epoch_seconds=time.perf_counter()-ep_start,
            cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved(),
            process_rss_bytes=psutil.Process().memory_info().rss,smoke=False,test_evaluated=False,promotion=False)
        with (out/'epochs.jsonl').open('a',encoding='utf-8') as handle:
            handle.write(json.dumps(record, allow_nan=False)+'\n')
        print(json.dumps(record), flush=True)
        if p.sha(ROOT/'best_model.pt')!=config['original_checkpoint_sha256'] or p.sha(MANIFEST)!=MANIFEST_SHA:
            raise RuntimeError('Protected original/split changed')
    json_atomic(out/'state.json', dict(status='completed',epochs_finished=12,elapsed_seconds=time.perf_counter()-started,
        best_selection_key=list(best),smoke=False,test_evaluated=False,promotion=False))


if __name__ == '__main__':
    main()
