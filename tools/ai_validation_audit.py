"""Full native validation audit of completed candidates; no calibration/test access.

Outputs are exclusive, with exact float32 grid maps and per-error review panels.
The unchanged baseline and all production/application modules remain untouched.
"""
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import medvision_pipeline as p
from tools import ai_metrics as a
from tools.evaluate_ai_baseline import box, figures, inspect_splits, panel, save, sha, write_csv

MANIFEST = ROOT / 'experiments/data_v3_reliability_20261007/manifest.json'
MANIFEST_SHA = '4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318'


def inspect_case(row, image, target, mask, native_probability, instances, small_cutoff):
    truth, prediction = target.astype(bool), mask.astype(bool)
    tp, fp, fn = [int(v.sum()) for v in (truth & prediction, ~truth & prediction, truth & ~prediction)]
    positive = bool(int(row['fractured']))
    presence = bool(mask.any())
    category = ('TP' if presence else 'FN') if positive else ('FP' if presence else 'TN')
    precision, recall = a.ratio(tp, tp+fp), a.ratio(tp, tp+fn)
    errors = []
    if positive:
        if not presence:
            errors.append('complete_empty_miss')
        elif tp == 0:
            errors.append('complete_mislocalization')
        else:
            if recall < .5:
                errors.append('under_segmentation_recall_below_0.5')
            if precision < .5:
                errors.append('over_segmentation_precision_below_0.5')
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    regions = []
    for index in range(1, n):
        left, top, width, height, area = stats[index].tolist()
        regions.append(dict(box=[left, top, left+width, top+height], pixels=area,
                            score=float(native_probability[labels == index].max())))
    overlap = np.zeros((len(instances), n-1))
    sizes = stats[1:, cv2.CC_STAT_AREA]
    for index, instance in enumerate(instances):
        intersections = np.bincount(labels[instance.astype(bool)], minlength=n)[1:]
        overlap[index] = intersections / np.maximum(sizes + int(instance.sum()) - intersections, 1)
    h, w = image.shape
    return dict(image_id=row['image_id'], group=row['group'], positive=positive,
                prediction_present=presence, category=category,
                case_score=float(native_probability.max()),
                tp_pixels=tp, fp_pixels=fp, fn_pixels=fn,
                dice=a.ratio(2*tp, 2*tp+fp+fn) if positive else None,
                iou=a.ratio(tp, tp+fp+fn) if positive else None,
                segmentation_precision=precision, segmentation_recall=recall,
                native_shape=[h, w], gt_instances=len(instances), predicted_components=n-1,
                gt_fraction=float(target.mean()), predicted_fraction=float(mask.mean()),
                small_region_proxy=positive and float(target.mean()) <= small_cutoff,
                quality_std=float(image.std()),
                quality_contrast_p99_p01=float(np.quantile(image, .99)-np.quantile(image, .01)),
                segmentation_failure_tags=errors, gt_boxes=[box(instance) for instance in instances],
                regions=regions,
                mask_region_matches_iou10=a.matched_regions(overlap, .1),
                mask_region_matches_iou50=a.matched_regions(overlap, .5),
                flags={key: int(row[key]) for key in ('hand', 'leg', 'hip', 'shoulder', 'mixed',
                      'hardware', 'multiscan', 'frontal', 'lateral', 'oblique')},
                fracture_count=int(row['fracture_count']), source_member=row['member'])


def summarize(cases, config, timings=None):
    cl = a.classification(cases)
    cl['score_definition'] = 'Maximum native bilinear inverse sigmoid pixel; uncalibrated case proxy, not a case probability'
    loc = a.localization(cases)
    loc['method'] = loc['method'].replace('baseline .90', f"native threshold {config['postprocess']['threshold']}")
    regions = {}
    for cutoff, key in ((.1, 'mask_region_matches_iou10'), (.5, 'mask_region_matches_iou50')):
        matches = sum(c[key] for c in cases)
        gt = sum(c['gt_instances'] for c in cases)
        predicted = sum(c['predicted_components'] for c in cases)
        regions[str(cutoff)] = dict(matches=matches, gt=gt, predicted=predicted,
                                   precision=a.ratio(matches, predicted), recall=a.ratio(matches, gt),
                                   false_positive_regions=predicted-matches, missed_regions=gt-matches)
    groups = {}
    for flag in cases[0]['flags']:
        subset = [c for c in cases if c['flags'][flag]]
        groups[flag] = dict(classification=a.classification(subset), segmentation=a.segmentation(subset)) if subset else None
    for name, subset in [('small_region_proxy', [c for c in cases if c['small_region_proxy']]),
                         ('multiple_fractures', [c for c in cases if c['fracture_count'] > 1])]:
        groups[name] = dict(classification=a.classification(subset), segmentation=a.segmentation(subset)) if subset else None
    cm = cl['confusion_matrix']
    count_targets_pass = cm['tp'] >= 79 and cm['tn'] >= 342 and cl['accuracy'] >= .90
    return dict(config=config, classification=cl, segmentation=a.segmentation(cases),
                localization=loc, mask_instance_localization=regions,
                calibration=a.calibration(cases), subgroups=groups,
                categories=dict(Counter(c['category'] for c in cases)),
                segmentation_failure_counts=dict(Counter(t for c in cases for t in c['segmentation_failure_tags'])),
                practical_classification_targets=dict(tp_min=79, tn_min=342,
                    sensitivity_rounding='79/83=95.1807%, approximately95.2%; user practical count rule',
                    classification_counts_pass=count_targets_pass,
                    promotion_accepted=False,
                    reason='Native localization/segmentation comparison, calibration, robustness and freeze still required even if case counts pass'),
                timing=timings, test_images_read=0,
                unavailable=['patient/study independence', 'clinical subtle/nondisplaced labels',
                             'paired-study fusion', 'external generalization', 'radiologist adjudication'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
    args = parser.parse_args()
    run, out = Path(args.run).resolve(), Path(args.out).resolve()
    if ROOT not in run.parents or ROOT not in out.parents or out.exists():
        raise ValueError('Use an existing research run and NEW workspace output directory')
    state = json.loads((run/'state.json').read_text())
    if state['status'] != 'completed' or state['smoke']:
        raise ValueError('Full completed training required; never read a live checkpoint')
    train_config = json.loads((run/'config.json').read_text())
    bundle = json.loads((run/'bundle.json').read_text())
    if train_config['manifest_sha256'] != MANIFEST_SHA or sha(MANIFEST) != MANIFEST_SHA:
        raise ValueError('Frozen validation distribution changed')
    archive = ROOT/'FracAtlas.zip'
    if sha(archive) != train_config['archive_sha256']:
        raise ValueError('Dataset changed')
    checkpoint = run/'best_model.pt'
    checkpoint_hash = sha(checkpoint)
    if checkpoint_hash != bundle['checkpoint_sha256']:
        raise ValueError('Selected checkpoint hash mismatch')
    if bundle['output_contract'] != p.CONTRACT or bundle['architecture'] != 'AttentionUNet64':
        raise ValueError('Unsupported architecture; register its output contract explicitly')
    if args.device == 'cuda' and not torch.cuda.is_available():
        raise ValueError('Requested CUDA unavailable')
    # Plotting is checked BEFORE writing evidence, unlike the old CPU evaluator.
    import matplotlib
    matplotlib.use('Agg')
    manifest = json.loads(MANIFEST.read_text())
    leakage = inspect_splits(manifest)
    preprocess = p.PreprocessConfig(**bundle['preprocess'])
    post = p.PostprocessConfig(**bundle['postprocess'])
    dataset = p.FracDataset(str(archive), str(MANIFEST), 'val', preprocess)
    if len(dataset) != 463 or sum(int(r['fractured']) for r in dataset.rows) != 83:
        raise ValueError('Validation denominators changed')
    torch.set_num_threads(2)
    cv2.setNumThreads(1)
    p.seed_everything(42)
    model = p.LogitsAttentionUNet().to(args.device)
    model.load_state_dict(torch.load(checkpoint, map_location=args.device, weights_only=True), strict=True)
    model.eval()
    out.mkdir()
    for name in ('masks', 'failures', 'source_snapshot'):
        (out/name).mkdir()
    sources = ['medvision_ai.py', 'medvision_pipeline.py', 'tools/ai_metrics.py',
               'tools/evaluate_ai_baseline.py', 'tools/ai_validation_audit.py']
    for source in sources:
        (out/'source_snapshot'/Path(source).name).write_bytes((ROOT/source).read_bytes())
    config = dict(scope='Full frozen463 validation, selected completed candidate; no calibration/test/promotion',
                  run=str(run.relative_to(ROOT)), checkpoint_sha256=checkpoint_hash,
                  manifest_sha256=MANIFEST_SHA, archive_sha256=sha(archive),
                  preprocess=asdict(preprocess), postprocess=asdict(post),
                  epoch=bundle['epoch'], torch=torch.__version__, device=args.device,
                  source_hashes={source: sha(ROOT/source) for source in sources},
                  original_checkpoint_sha256=sha(ROOT/'best_model.pt'),
                  test_images_read=0, model_selection='Existing frozen checkpoint score; audit does not reselect')
    save(out/'config.json', config)
    save(out/'split_audit.json', leakage)
    sizes = [r['mask_pixels']/(r['width']*r['height']) for r in manifest['rows'] if r['split'] == 'train' and int(r['fractured'])]
    small_cutoff = float(np.quantile(sizes, .25))
    cases, cache, latencies, totals = [], {}, [], []
    start = time.perf_counter()
    with torch.inference_mode():
        for index, row in enumerate(dataset.rows):
            total_start = time.perf_counter()
            image, target = dataset.native(index)
            h, w = image.shape
            instances = [p.legacy._rasterize_coco_segmentation(dataset.annotations[aid]['segmentation'], w, h)
                         for aid in row['annotation_ids']]
            x, _, _, geometry = p.prepare(image, preprocess)
            if args.device == 'cuda':
                torch.cuda.synchronize()
            t0 = time.perf_counter()
            grid = model(torch.from_numpy(x)[None, None].to(args.device)).sigmoid()[0, 0].cpu().numpy()
            latencies.append((time.perf_counter()-t0)*1000)
            if grid.dtype != np.float32 or not np.isfinite(grid).all():
                raise ValueError('Invalid probability map')
            native = p.inverse(grid, geometry, probability=True)
            _, delivered = p.postprocess(native, post)
            totals.append((time.perf_counter()-total_start)*1000)
            c = inspect_case(row, image, target, delivered, native, instances, small_cutoff)
            stem = Path(row['image_id']).stem
            for suffix, mask in [('prediction', delivered), ('reference', target)]:
                if not cv2.imwrite(str(out/'masks'/f'{stem}_{suffix}.png'), mask*255):
                    raise RuntimeError('Cannot save native mask')
            if c['category'] in ('FP', 'FN') or c['segmentation_failure_tags']:
                filename = f"{c['category']}_{stem}.jpg"
                panel(image, target, delivered, out/'failures'/filename,
                      f"{row['image_id']} {c['category']} score={c['case_score']:.6f} Dice={c['dice']}")
                c['review_panel'] = 'failures/'+filename
            cache[row['image_id']] = grid.copy()
            cases.append(c)
            if (index+1) % 25 == 0:
                progress = dict(status='validation_audit', images=index+1, total=len(dataset), test_images_read=0)
                (out/'progress.json').write_text(json.dumps(progress, indent=2))
                print(json.dumps(progress), flush=True)
    save(out/'per_case.json', cases)
    np.savez_compressed(out/'probabilities_float32.npz', **cache)
    timing = dict(forward_median_ms=float(np.median(latencies[1:])),
                  forward_p95_ms=float(np.quantile(latencies[1:], .95)),
                  pipeline_median_ms=float(np.median(totals[1:])),
                  full_audit_seconds=time.perf_counter()-start,
                  peak_rss_bytes=getattr(psutil.Process().memory_info(), 'peak_wset', psutil.Process().memory_info().rss))
    result = summarize(cases, config, timing)
    result['small_region_definition'] = dict(cutoff_fraction=small_cutoff, source='Training25th percentile; not clinical subtle/nondisplaced')
    # Compare the audit counts to the trainer without hiding device rounding.
    recorded = json.loads((run/'best_validation_cases.json').read_text())['delivered']
    by_id = {c['image_id']: c for c in recorded}
    differences = [{key: c[key] for key in ('image_id', 'tp_pixels', 'fp_pixels', 'fn_pixels', 'prediction_present')}
                   for c in cases if any(c[key] != by_id[c['image_id']][key] for key in
                       ('tp_pixels', 'fp_pixels', 'fn_pixels', 'prediction_present'))]
    result['trainer_reproduction'] = dict(exact_native_case_counts=not differences,
                                         differing_cases=differences,
                                         trainer_device=train_config['device'], audit_device=args.device,
                                         note='CPU/GPU rounding may change near-threshold pixels; discrepancies retained, never overwrite trainer data')
    save(out/'metrics.json', result)
    write_csv(out/'failure_review.csv', [dict(image_id=c['image_id'], category=c['category'],
        panel=c.get('review_panel', ''), score=c['case_score'], dice=c['dice'], iou=c['iou'],
        precision=c['segmentation_precision'], recall=c['segmentation_recall'],
        flags=';'.join(key for key, value in c['flags'].items() if value),
        failure_tags=';'.join(c['segmentation_failure_tags']), clinical_cause='unadjudicated')
        for c in cases if c.get('review_panel')])
    figures(out, cases, result)
    report = ['# Completed candidate validation audit', '',
              f"Run {config['run']}; epoch{config['epoch']}; native threshold{post.threshold}/{post.policy}.", '',
              'No calibration/test access or promotion. Original checkpoint and baseline untouched.', '',
              '## Classification', '', '| Metric | Value |', '|---|---:|']
    for key, value in result['classification'].items():
        if isinstance(value, (float, int)) or value is None:
            report.append(f'| {key} | {value} |')
    report += ['', '## Segmentation/localization', '', json.dumps(result['segmentation'], indent=2), '',
               json.dumps(result['mask_instance_localization'], indent=2), '',
               'Component-box AP is a proxy, not canonical detector mAP. Clinical cause and patient independence remain unverified.', '',
               'Every FP/FN/tagged mask error has a retained panel. See metrics.json for calibration/subgroups/timing and trainer reproduction.', '',
               f"Classification count targets pass: {result['practical_classification_targets']['classification_counts_pass']}. This alone NEVER authorizes promotion."]
    with (out/'VALIDATION_AUDIT.md').open('x', encoding='utf-8') as handle:
        handle.write('\n'.join(report)+'\n')
    if sha(checkpoint) != checkpoint_hash or sha(MANIFEST) != MANIFEST_SHA or sha(ROOT/'best_model.pt') != config['original_checkpoint_sha256']:
        raise RuntimeError('Protected inputs changed')
    save(out/'completion.json', dict(status='completed', metrics_sha256=sha(out/'metrics.json'),
         cases_sha256=sha(out/'per_case.json'), checkpoint_sha256=checkpoint_hash, test_images_read=0))
    print(json.dumps(dict(classification=result['classification'], segmentation=result['segmentation']), indent=2), flush=True)


if __name__ == '__main__':
    main()
