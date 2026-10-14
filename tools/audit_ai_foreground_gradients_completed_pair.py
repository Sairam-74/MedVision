"""TRAIN-only output-gradient diagnosis after the rejected E11/E12 pair.

Frozen selected models, raw unaugmented TRAIN tensors, no optimizer steps.
Exploratory foreground-BCE10 derivatives are mathematical probes, not a
trained candidate or a selected intervention. All prior sources stay intact.
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
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import medvision_pipeline as p
from tools.ai_atomic_io import json_atomic
from tools.ai_cached_dataset import CachedReliabilityDataset
from tools.ai_presence_model import PresenceAttentionUNet, tensor_digest
from tools.ai_bounded_hard_weights import class_normalized_weights

ARMS = {'E11': 'AI_E11_v3_positive_Dice_reference', 'E12': 'AI_E12_v3_positive_Dice2'}


def distribution(values):
    v = values.detach().float().cpu().numpy().reshape(-1)
    if not len(v):
        return None
    return dict(n=len(v), mean=float(v.mean()), minimum=float(v.min()), maximum=float(v.max()),
                q10=float(np.quantile(v, .1)), median=float(np.median(v)), q90=float(np.quantile(v, .9)))


def gradient_summary(gradient, foreground, background):
    return dict(foreground_L2=float(torch.linalg.vector_norm(gradient[foreground])),
                background_L2=float(torch.linalg.vector_norm(gradient[background])),
                foreground_abs_sum=float(gradient[foreground].abs().sum()),
                background_abs_sum=float(gradient[background].abs().sum()),
                invalid_abs_sum=float(gradient[~(foreground | background)].abs().sum()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if ROOT not in out.parents or out.exists():
        raise ValueError('Exclusive new workspace diagnostic output required')
    pair = ROOT / 'experiments/AI_E11_E12_POSITIVE_DICE_PAIR'
    completion = json.loads((pair / 'completion.json').read_text())
    if completion['status'] != 'completed' or p.sha(pair / 'comparison.json') != completion['comparison_sha256']:
        raise ValueError('Completed matched pair identity required')
    sources = ['tools/audit_ai_foreground_gradients_completed_pair.py', 'tools/ai_cached_dataset.py',
               'tools/ai_presence_model.py', 'tools/ai_bounded_hard_weights.py',
               'tools/ai_atomic_io.py', 'medvision_pipeline.py', 'medvision_ai.py']
    source_hashes = {name: p.sha(ROOT / name) for name in sources}
    configs, bundles, checkpoint_hashes = {}, {}, {}
    for arm, name in ARMS.items():
        run = ROOT / 'experiments' / name
        state = json.loads((run / 'state.json').read_text())
        if state['status'] != 'completed' or state['epochs_finished'] != 12:
            raise ValueError('Both completed full models required')
        configs[arm] = json.loads((run / 'config.json').read_text())
        bundles[arm] = json.loads((run / 'bundle.json').read_text())
        checkpoint_hashes[arm] = p.sha(run / 'best_model.pt')
        if checkpoint_hashes[arm] != bundles[arm]['checkpoint_sha256']:
            raise ValueError('Selected checkpoint identity mismatch')
    differences = [k for k in configs['E11'] if configs['E11'][k] != configs['E12'][k]]
    if differences != ['positive_dice_coefficient']:
        raise ValueError('Registered single factor required')
    config = configs['E11']
    protocol_path = ROOT/'experiments/session_20261007_ai_loop_01/POSITIVE_DICE_EXPERIMENT_PROTOCOL.json'
    if p.sha(protocol_path) != config['protocol_sha256']:
        raise ValueError('Registered completed protocol changed')
    registered = json.loads(protocol_path.read_text())
    registered_hashes = {str((ROOT/name).resolve()):digest for name,digest in registered['input_hashes'].items()}
    manifest = ROOT / config['manifest']
    if p.sha(manifest) != config['manifest_sha256'] or config['presence_weight'] != 0 or config['hard_factor'] != 2:
        raise ValueError('Frozen mask-only TRAIN configuration required')
    data = CachedReliabilityDataset(ROOT / config['cache'], manifest,
                                   p.PreprocessConfig(**config['preprocess']), seed=42, elastic=False)
    if len(data) != 2808 or sum(int(r['fractured']) for r in data.rows) != 493:
        raise ValueError('Exact TRAIN membership required')
    catalog = ROOT / config['hard_catalog']
    if p.sha(data.cache/'completion.json') != config['cache_completion_sha256']:
        raise ValueError('Registered TRAIN cache identity changed')
    for name in ('completion.json','HARD_POSITIVE_SET.json','HARD_NEGATIVE_SET.json','proposed_example_weights.json'):
        if p.sha(catalog/name) != registered_hashes.get(str((catalog/name).resolve())):
            raise ValueError('Registered hard catalog changed: '+name)
    hp = set(json.loads((catalog / 'HARD_POSITIVE_SET.json').read_text())['image_ids'])
    hn = set(json.loads((catalog / 'HARD_NEGATIVE_SET.json').read_text())['image_ids'])
    if len(hp) != 109 or len(hn) != 713:
        raise ValueError('Unchanged persistent TRAIN hard sets required')
    rows = {r['image_id']: r for r in data.rows}
    indices = {r['image_id']: i for i, r in enumerate(data.rows)}
    positive_ids = {i for i, r in rows.items() if int(r['fractured'])}
    normal_ids = set(rows) - positive_ids
    strata = dict(hard_positive=hp, ordinary_positive=positive_ids-hp,
                  hard_negative=hn, ordinary_negative=normal_ids-hn)
    weights = class_normalized_weights(data.rows, hp, hn, 2)
    input_paths = [protocol_path,manifest,data.cache/'completion.json',data.cache/'rows.json',
                   pair/'comparison.json',pair/'completion.json',ROOT/'best_model.pt']
    input_paths += [catalog/name for name in ('completion.json','HARD_POSITIVE_SET.json',
                                             'HARD_NEGATIVE_SET.json','proposed_example_weights.json')]
    input_paths += [ROOT/'experiments'/name/file for name in ARMS.values()
                   for file in ('config.json','state.json','bundle.json')]
    input_hashes = {str(path.relative_to(ROOT)):p.sha(path) for path in input_paths}
    samples = []
    rng = np.random.default_rng(42)
    for name, ids in strata.items():
        ordered = sorted(ids)
        if 'positive' in name:
            ordered.sort(key=lambda i: (int(data.arrays['target'][indices[i]].sum()), i))
            selected = [ordered[int(v)] for v in np.linspace(0, len(ordered)-1, 8).round()]
        else:
            selected = [ordered[int(v)] for v in rng.choice(len(ordered), 8, replace=False)]
        if len(set(selected)) != 8:
            raise ValueError('Unique size-spanning/seeded sample required')
        samples.extend(dict(image_id=i, stratum=name, train_index=indices[i]) for i in selected)
    if len({v['image_id'] for v in samples}) != 32:
        raise ValueError('32 distinct TRAIN sources required')
    if not torch.cuda.is_available():
        raise RuntimeError('Verified CUDA runtime required')
    torch.set_num_threads(2)
    cv2.setNumThreads(1)
    p.seed_everything(42)
    out.mkdir()
    json_atomic(out / 'config.json', dict(samples=samples, checkpoint_hashes=checkpoint_hashes,
        selected_epochs={a:dict(epoch=b['epoch'],global_epoch=b['global_epoch']) for a,b in bundles.items()},
        source_hashes=source_hashes, input_hashes=input_hashes, preprocess=asdict(data.config), manifest_sha256=config['manifest_sha256'],
        cache_completion_sha256=p.sha(data.cache / 'completion.json'), hard_factor=2,
        augmentation=False, batch_size=2, device='cuda', eval_statistics=True, no_optimizer_steps=True,
        scope='32 TRAIN sources: eight size-spanning hard/ordinary positives plus eight seeded hard/ordinary normals',
        validation_images_read=0, calibration_images_read=0, test_images_read=0))
    results, unchanged = [], {}
    started = time.perf_counter()
    for arm, name in ARMS.items():
        run = ROOT / 'experiments' / name
        model = PresenceAttentionUNet().to('cuda')
        model.load_state_dict(torch.load(run/'best_model.pt', map_location='cpu', weights_only=True), strict=True)
        model.eval()
        before = tensor_digest(model.state_dict())
        for start in range(0, len(samples), 2):
            batch = samples[start:start+2]
            arrays = [torch.from_numpy(np.stack([data.arrays[k][v['train_index']].astype(np.float32, copy=True)
                        for v in batch])).unsqueeze(1).to('cuda') for k in ('image','target','valid')]
            x, target, valid = arrays
            with torch.no_grad():
                logits = model(x)['mask_logits']
            for j, sample in enumerate(batch):
                z = logits[j:j+1].detach().requires_grad_(True)
                y, v = target[j:j+1], valid[j:j+1]
                fg, bg = (y.bool() & v.bool()), (~y.bool() & v.bool())
                w = weights[sample['image_id']]
                n = v.sum()
                probability = z.sigmoid()
                bce = w * (F.binary_cross_entropy_with_logits(z,y,reduction='none')*v).sum()/n/2
                tp = (probability*y*v).sum()
                fp = (probability*(1-y)*v).sum()
                fn = ((1-probability)*y*v).sum()
                dice = w*(1-(2*tp+1e-6)/(2*tp+fp+fn+1e-6))/2
                # The extra term changes GT-positive pixels only. Normal and
                # positive-image background output gradients stay unchanged.
                fg_offset = 9*w*(F.softplus(-z)*y*v).sum()/n/2
                explicit_positive = bool(int(rows[sample['image_id']]['fractured']))
                if bool(fg.any()) != explicit_positive or int(n) <= 0:
                    raise ValueError('Explicit label/nonempty valid target mismatch')
                terms = dict(BCE1=bce, Dice1=dice, Dice2=(2 if explicit_positive else 1)*dice,
                             baseline=bce+dice,
                             foreground_BCE10_probe=bce+fg_offset+dice)
                gradients = {k: torch.autograd.grad(loss,z,retain_graph=True)[0] for k,loss in terms.items()}
                if not torch.equal(gradients['baseline'][bg],gradients['foreground_BCE10_probe'][bg]):
                    raise ValueError('Probe changed background/normal output gradients')
                if not all(bool(torch.isfinite(g).all()) for g in gradients.values()):
                    raise ValueError('Finite output gradients required')
                if any(bool(g[~v.bool()].any()) for g in gradients.values()):
                    raise ValueError('Invalid-pixel loss gradient')
                qmask=(probability>=.5)&v.bool()
                record=dict(**sample, arm=arm, positive=bool(int(rows[sample['image_id']]['fractured'])),
                    hard_weight=w, target_pixels=int(fg.sum()),valid_pixels=int(n),
                    mask_TP=int((qmask&fg).sum()),mask_FP=int((qmask&bg).sum()),mask_FN=int((~qmask&fg).sum()),
                    foreground_logits=distribution(z[fg]),foreground_probability=distribution(probability[fg]),
                    background_probability=distribution(probability[bg]),
                    gradients={k:gradient_summary(g,fg,bg) for k,g in gradients.items()},
                    mathematical_probe_not_training=True)
                results.append(record)
        after = tensor_digest(model.state_dict())
        unchanged[arm] = dict(before_sha256=before,after_sha256=after,exactly_unchanged=before==after)
        if not unchanged[arm]['exactly_unchanged']:
            raise ValueError('Frozen model/statistics changed during evaluation')
        del model, logits, arrays, x, target, valid
        torch.cuda.empty_cache()
    for name,digest in source_hashes.items():
        if p.sha(ROOT/name) != digest:
            raise ValueError('Diagnostic source changed while running')
    for name,digest in input_hashes.items():
        if p.sha(ROOT/name) != digest:
            raise ValueError('Frozen diagnostic input changed while running: '+name)
    for name,digest in data.metadata['cache_hashes'].items():
        if p.sha(data.cache/(name+'.npy')) != digest:
            raise ValueError('TRAIN cache array bytes changed during read-only diagnosis')
    for arm,name in ARMS.items():
        if p.sha(ROOT/'experiments'/name/'best_model.pt') != checkpoint_hashes[arm]:
            raise ValueError('Selected checkpoint changed while running')
    summary={}
    for arm in ARMS:
        summary[arm]={}
        for stratum in strata:
            subset=[r for r in results if r['arm']==arm and r['stratum']==stratum]
            summary[arm][stratum]=dict(n=len(subset),target_pixels=[r['target_pixels'] for r in subset],
                zero_overlap=sum(r['positive'] and r['mask_TP']==0 for r in subset),
                foreground_probability_medians=[r['foreground_probability']['median'] for r in subset if r['positive']],
                median_gradient_L2={k:{area:float(np.median([r['gradients'][k][area+'_L2'] for r in subset]))
                    for area in ('foreground','background')} for k in results[0]['gradients']})
    json_atomic(out/'per_case.json',results)
    json_atomic(out/'summary.json',dict(summary=summary, model_tensors_and_eval_statistics_unchanged=unchanged,
        elapsed_seconds=time.perf_counter()-started, actual_unique_TRAIN_sources=32, model_evaluations=64,
        validation_images_read=0, calibration_images_read=0,test_images_read=0,
        no_optimizer_steps=True, model_trained=False, factor_selected=False, improvement_claim=False,
        limitations=['Size-spanning and model-selected hard strata are not population-representative.',
                    'Eval-statistics output gradients do not establish shared-parameter training gradients or causality.',
                    'Foreground-BCE10 is an untrained mathematical probe, not measured model improvement.',
                    'Selected E11/E12 epochs differ; this is a diagnosis, not another controlled training result.']))
    json_atomic(out/'completion.json',dict(status='completed_TRAIN_only_frozen_foreground_gradient_diagnosis',
        per_case_sha256=p.sha(out/'per_case.json'),summary_sha256=p.sha(out/'summary.json'),
        config_sha256=p.sha(out/'config.json'),source_sha256=p.sha(Path(__file__)),
        no_optimizer_steps=True, model_tensors_unchanged=all(v['exactly_unchanged'] for v in unchanged.values()),
        validation_images_read=0,calibration_images_read=0,test_images_read=0,promotion=False))
    print(json.dumps(dict(status='completed_TRAIN_only_foreground_gradient_diagnosis',summary=summary),indent=2))


if __name__ == '__main__':
    main()
