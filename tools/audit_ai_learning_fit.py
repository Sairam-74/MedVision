"""Unaugmented TRAIN/validation grid-fit diagnostic for a completed candidate.

This distinguishes learning fit from generalization on a matched grid protocol.
It does not replace the native validation audit or select/train/promote a model.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

import cv2
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import medvision_pipeline as p
from tools import ai_metrics as a
from tools.ai_cached_dataset import CachedReliabilityDataset
from tools.evaluate_ai_baseline import save


def grid_case(row, probability, target):
    if probability.shape != (256, 256) or probability.dtype != np.float32 or not np.isfinite(probability).all():
        raise ValueError('Unexpected grid contract')
    predicted, target = probability >= .5, target.astype(bool)
    positive = bool(int(row['fractured']))
    if positive != bool(target.any()):
        raise ValueError('Source label/grid target mismatch')
    tp, fp, fn = [int(np.count_nonzero(x)) for x in (predicted&target, predicted&~target, ~predicted&target)]
    mass = float(probability.sum(dtype=np.float64))
    intersection = float(probability[target].sum(dtype=np.float64))
    return dict(image_id=row['image_id'], group=row['group'], positive=positive, prediction_present=bool(predicted.any()),
        case_score=float(probability.max()), tp_pixels=tp, fp_pixels=fp, fn_pixels=fn,
        dice=a.ratio(2*tp, 2*tp+fp+fn) if positive else None, iou=a.ratio(tp, tp+fp+fn) if positive else None,
        segmentation_precision=a.ratio(tp, tp+fp), segmentation_recall=a.ratio(tp, tp+fn) if positive else None,
        soft_dice=(2*intersection+1e-6)/(mass+int(target.sum())+1e-6),
        mean_predicted_probability=mass/probability.size, zero_overlap_positive=positive and tp==0)


def summarize(cases):
    positive = [c for c in cases if c['positive']]
    return dict(classification=a.classification(cases), segmentation=a.segmentation(cases),
                mean_positive_soft_dice=float(np.mean([c['soft_dice'] for c in positive])),
                positive_no_target_overlap=sum(c['zero_overlap_positive'] for c in positive),
                protocol='256x256 grid threshold0.5/all; nearest projected labels. Diagnostic only, not native acceptance metrics.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--audit', required=True)
    parser.add_argument('--cache', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    run, audit, out = [Path(v).resolve() for v in (args.run, args.audit, args.out)]
    if ROOT not in run.parents or ROOT not in audit.parents or ROOT not in out.parents or out.exists():
        raise ValueError('Existing workspace research evidence and new output required')
    state = json.loads((run/'state.json').read_text())
    config = json.loads((run/'config.json').read_text())
    bundle = json.loads((run/'bundle.json').read_text())
    if state['status']!='completed' or state['smoke'] or not (audit/'completion.json').exists():
        raise ValueError('Full completed training and full completed native audit required')
    native_metrics = json.loads((audit/'metrics.json').read_text())
    checkpoint = run/bundle['checkpoint']
    digest = p.sha(checkpoint)
    if digest != bundle['checkpoint_sha256'] or digest != native_metrics['config']['checkpoint_sha256']:
        raise ValueError('Require the same selected checkpoint as native audit')
    preprocess = p.PreprocessConfig(**bundle['preprocess'])
    if preprocess.size != 256:
        raise ValueError('Registered diagnostic is256 only')
    manifest = ROOT/config['manifest']
    if p.sha(manifest) != '4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318':
        raise ValueError('Frozen partition changed')
    cached = CachedReliabilityDataset(args.cache, manifest, preprocess)
    torch.set_num_threads(2)
    cv2.setNumThreads(1)
    torch.use_deterministic_algorithms(True)
    model = p.LogitsAttentionUNet()
    model.load_state_dict(torch.load(checkpoint, map_location='cpu', weights_only=True), strict=True)
    model.eval()
    out.mkdir()
    save(out/'config.json', dict(run=str(run.relative_to(ROOT)), native_audit=str(audit.relative_to(ROOT)),
        checkpoint_sha256=digest, selected_epoch=bundle['epoch'], preprocess=asdict(preprocess),
        manifest_sha256=p.sha(manifest), cache_completion_sha256=p.sha(Path(args.cache)/'completion.json'),
        source_hashes={source:p.sha(ROOT/source) for source in ['tools/audit_ai_learning_fit.py','tools/ai_cached_dataset.py','tools/ai_metrics.py','medvision_pipeline.py','medvision_ai.py']},
        scope='Full unaugmented TRAIN grid predictions vs already saved validation grid predictions; no new validation image inference',
        device='cpu', inference_batch_size=1, validation_images_read=0, calibration_images_read=0, test_images_read=0))
    started = time.perf_counter()
    train = []
    with torch.inference_mode(), (out/'train_cases.jsonl').open('x', encoding='utf-8') as handle:
        for i, row in enumerate(cached.rows):
            x = torch.from_numpy(cached.arrays['image'][i].copy())[None, None]
            probability = model(x).sigmoid()[0, 0].numpy()
            case = grid_case(row, probability, cached.arrays['target'][i])
            train.append(case)
            handle.write(json.dumps(case)+'\n')
            if (i+1) % 50 == 0:
                handle.flush()
                progress = dict(status='train_grid_fit', completed=i+1, total=len(cached), elapsed_seconds=time.perf_counter()-started,
                                validation_images_read=0, calibration_images_read=0, test_images_read=0)
                temporary = out/'progress.tmp'
                temporary.write_text(json.dumps(progress, indent=2))
                temporary.replace(out/'progress.json')
                print(json.dumps(progress), flush=True)
    document = json.loads(manifest.read_text())
    val_rows = [r for r in document['rows'] if r['split']=='val']
    if len(val_rows)!=463 or sum(int(r['fractured']) for r in val_rows)!=83:
        raise ValueError('Validation membership changed')
    val = []
    with np.load(audit/'probabilities_float32.npz', allow_pickle=False) as probabilities:
        if set(probabilities.files) != {r['image_id'] for r in val_rows}:
            raise ValueError('Saved validation grid membership differs')
        for row in val_rows:
            native = cv2.imread(str(audit/'masks'/(Path(row['image_id']).stem+'_reference.png')), cv2.IMREAD_GRAYSCALE)
            if native is None or native.shape!=(row['height'], row['width']):
                raise ValueError('Saved native annotation unavailable')
            geometry = p.geometry(native.shape, preprocess)
            target = p.project((native>0).astype(np.float32), geometry, cv2.INTER_NEAREST)
            val.append(grid_case(row, probabilities[row['image_id']], target))
    result = dict(train=summarize(train), validation=summarize(val), selected_epoch=bundle['epoch'],
        native_validation_report_unchanged=True, new_validation_image_inference=False,
        interpretation='Compare matched grid fit only. A train/validation gap alone cannot prove overfitting or clinical generalization; no patient independence is established.',
        threshold_tuned=False, calibration_evaluated=False, test_evaluated=False, promotion=False)
    if p.sha(checkpoint)!=digest or p.sha(ROOT/'best_model.pt')!=config['original_checkpoint_sha256']:
        raise ValueError('Protected checkpoint changed')
    save(out/'validation_grid_cases.json', val)
    save(out/'metrics.json', result)
    save(out/'completion.json', dict(status='completed_grid_fit_diagnostic', train_images=len(train), validation_cached_grids=len(val),
        elapsed_seconds=time.perf_counter()-started, model_trained=False, test_images_read=0, promotion=False))
    print(json.dumps(result, indent=2), flush=True)


if __name__=='__main__':
    main()
