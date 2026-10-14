"""Complete the registered v2 comparison after training, without test-driven tuning.

Default performs full validation only. --final-test freezes BOTH operating points
and the validation-only winner before reading any test image. --smoke is always
validation-only and cannot publish, select a finalist or touch the reserved test.
Existing completed stages may be reused only if their recorded identity matches.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import sys
import time
import zipfile
import cv2
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import medvision_pipeline as p
import medvision_ai as m
from tools.run_experiment import native_pair, summary
from tools.phase6_evidence import region_recall

RUNS = ('E3_v2_logits_bce_dice', 'E4_v2_logits_focal_tversky')
THRESHOLDS = [round(i * .05, 2) for i in range(1, 20)]
POLICIES = ('all', 'largest', 'min_pixels')


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def save(path, value):
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')
    temporary.replace(path)


def counts(row, tp, predicted, gt, components):
    positive = bool(int(row['fractured']))
    if positive and gt == 0:
        raise ValueError('Positive eligible case has no native target pixels')
    fp, fn = predicted - tp, gt - tp
    return dict(image_id=row['image_id'], group=row['group'], positive=positive,
                prediction_present=predicted > 0, tp_pixels=tp, fp_pixels=fp, fn_pixels=fn,
                dice=2 * tp / (predicted + gt) if positive else None,
                iou=tp / (predicted + gt - tp) if positive else None,
                precision=tp / predicted if predicted else None,
                recall=tp / gt if gt else None, components=components)


def policy_counts(probability, target, row, thresholds, verify=False):
    """Exact native integer counts; label once per threshold, no float16 cache."""
    result = {}
    for threshold in thresholds:
        raw = (probability >= threshold).astype(np.uint8)
        n, labels, stats, _ = cv2.connectedComponentsWithStats(raw, 8)
        areas = stats[:, cv2.CC_STAT_AREA]
        intersections = np.bincount(labels[target.astype(bool)], minlength=n)
        ids = np.arange(1, n)
        choices = {'all': ids, 'largest': np.array([1 + np.argmax(areas[1:])]) if n > 1 else ids,
                   'min_pixels': ids[areas[1:] >= 16]}
        for policy, keep in choices.items():
            c = counts(row, int(intersections[keep].sum()), int(areas[keep].sum()), int(target.sum()), len(keep))
            if verify:
                _, mask = p.postprocess(probability, p.PostprocessConfig(threshold, policy, 16))
                require(c['tp_pixels'] == int((mask.astype(bool) & target.astype(bool)).sum()), 'Native intersections differ')
                require(c['tp_pixels'] + c['fp_pixels'] == int(mask.sum()), 'Native areas differ')
                require(c['components'] == cv2.connectedComponents(mask, 8)[0] - 1, 'Native component counts differ')
            result[(threshold, policy)] = c
    return result


def confidence(cases):
    groups = {}
    for c in cases:
        groups.setdefault(c['group'], []).append(c)
    values = list(groups.values())
    rng = np.random.default_rng(42)
    draws = {'positive_dice': [], 'positive_iou': [], 'sensitivity': [], 'false_positive_rate': [], 'pixel_precision': [], 'pixel_recall': []}
    for _ in range(1000):
        sampled = [c for i in rng.integers(0, len(values), len(values)) for c in values[i]]
        pos = [c for c in sampled if c['positive']]
        normal = [c for c in sampled if not c['positive']]
        tp, fp, fn = (sum(c[k] for c in sampled) for k in ('tp_pixels', 'fp_pixels', 'fn_pixels'))
        for key, value in [('positive_dice', np.mean([c['dice'] for c in pos]) if pos else None),
                           ('positive_iou', np.mean([c['iou'] for c in pos]) if pos else None),
                           ('sensitivity', np.mean([c['prediction_present'] for c in pos]) if pos else None),
                           ('false_positive_rate', np.mean([c['prediction_present'] for c in normal]) if normal else None),
                           ('pixel_precision', tp / (tp + fp) if tp + fp else None),
                           ('pixel_recall', tp / (tp + fn) if tp + fn else None)]:
            if value is not None:
                draws[key].append(float(value))
    return {'unit': 'duplicate/related-image groups; patient independence unknown', 'seed': 42, 'replicates': 1000,
            'intervals95': {k: np.quantile(v, [.025, .975]).tolist() if v else None for k, v in draws.items()},
            'limitation': 'Degenerate empirical intervals do not establish zero population error.'}


def evaluate(bundle, out, split, smoke=False):
    document = json.loads(bundle.read_text())
    checkpoint = (bundle.parent / document['checkpoint']).resolve()
    checkpoint_sha = p.sha(checkpoint)
    if checkpoint_sha != document['checkpoint_sha256']:
        raise ValueError('Checkpoint identity changed; preserve results and investigate')
    identity = {'bundle_sha256': p.sha(bundle), 'manifest_sha256': p.sha(ROOT / 'experiments/data_v2/manifest.json'),
                'checkpoint_sha256': checkpoint_sha,
                'archive_sha256': p.sha(ROOT / 'FracAtlas.zip'), 'split': split, 'smoke': smoke,
                'evaluator_sha256': p.sha(Path(__file__)), 'pipeline_sha256': p.sha(ROOT / 'medvision_pipeline.py')}
    if (out / 'completed.json').exists():
        old = json.loads((out / 'completed.json').read_text())
        if old['identity'] != identity:
            raise RuntimeError('Completed evaluation identity changed; do not reuse results')
        return old
    if out.exists():
        raise RuntimeError(f'Incomplete evaluation preserved at {out}; inspect before choosing a new output ID')
    out.mkdir(parents=True)
    save(out / 'identity.json', identity)
    model, prep, post, _ = p.load_bundle(str(bundle), p.sha(bundle), document['checkpoint_sha256'], 'cpu')
    manifest = json.loads((ROOT / 'experiments/data_v2/manifest.json').read_text())
    rows = [r for r in manifest['rows'] if r['split'] == split]
    if smoke:
        if split != 'val':
            raise ValueError('Smoke cannot read the test')
        rows = [r for label in (1, 0) for r in [r for r in rows if int(r['fractured']) == label][:2]]
    thresholds = [.5, .9] if smoke else THRESHOLDS
    all_cases = {(t, policy): [] for t in thresholds for policy in POLICIES} if split == 'val' else {(post.threshold, post.policy): []}
    times = []
    started = time.perf_counter()
    with zipfile.ZipFile(ROOT / 'FracAtlas.zip') as archive:
        annotations = {a['id']: a for a in json.loads(archive.read('FracAtlas/Annotations/COCO JSON/COCO_fracture_masks.json'))['annotations']}
        for i, row in enumerate(rows):
            image, target = native_pair(archive, row, annotations)
            start = time.perf_counter()
            probability, _, delivered, _ = p.predict_arrays(model, image, prep, post, 'cpu')
            times.append((time.perf_counter() - start) * 1000)
            if split == 'val':
                cc = policy_counts(probability, target, row, thresholds, verify=smoke)
                for key in all_cases:
                    all_cases[key].append(cc[key])
            else:
                all_cases[(post.threshold, post.policy)].append(counts(row, int((delivered.astype(bool) & target.astype(bool)).sum()), int(delivered.sum()), int(target.sum()), cv2.connectedComponents(delivered, 8)[0] - 1))
            if (i + 1) % 25 == 0:
                save(out / 'progress.json', {'images': i + 1, 'total': len(rows), 'split': split})
                print(f'{out.name}: {i + 1}/{len(rows)}', flush=True)
        comparison = {f'{t:.2f}/{policy}': summary(cases) for (t, policy), cases in all_cases.items()}
        if split == 'val':
            baseline = comparison['0.50/all']
            eligible = [k for k in all_cases if comparison[f'{k[0]:.2f}/{k[1]}']['case_sensitivity'] >= baseline['case_sensitivity'] - .02 and comparison[f'{k[0]:.2f}/{k[1]}']['normal_false_positive_rate'] <= baseline['normal_false_positive_rate'] + .02]
            best = max(eligible, key=lambda k: comparison[f'{k[0]:.2f}/{k[1]}']['mean_positive_dice'])
            best_dice = comparison[f'{best[0]:.2f}/{best[1]}']['mean_positive_dice']
            simple = [k for k in eligible if k[1] == 'all' and best_dice - comparison[f'{k[0]:.2f}/{k[1]}']['mean_positive_dice'] < .005]
            if simple:
                best = max(simple, key=lambda k: (comparison[f'{k[0]:.2f}/{k[1]}']['mean_positive_dice'], -k[0]))
            else:
                best = max(eligible, key=lambda k: (comparison[f'{k[0]:.2f}/{k[1]}']['mean_positive_dice'], -k[0]))
        else:
            best = (post.threshold, post.policy)
        selected = all_cases[best]
        metrics = comparison[f'{best[0]:.2f}/{best[1]}']
        metrics['specificity'] = 1 - metrics['normal_false_positive_rate']
        positives_predicted = metrics['case_true_positive'] + metrics['case_false_positive']
        metrics['case_precision'] = metrics['case_true_positive'] / positives_predicted if positives_predicted else None
        regions = {str(t): {'matches': 0, 'ground_truth_instances': 0, 'false_positive_regions': 0} for t in (.1, .5)}
        example_ids = {max((c for c in selected if c['positive']), key=lambda c: c['dice'])['image_id'], min((c for c in selected if c['positive']), key=lambda c: c['dice'])['image_id'], next(r['image_id'] for r in rows if not int(r['fractured']))}
        multiple = [r for r in rows if len(r['annotation_ids']) > 1]
        if multiple:
            example_ids.add(multiple[0]['image_id'])
        for row, c in zip(rows, selected):
            image, target = native_pair(archive, row, annotations)
            probability, _, _, _ = p.predict_arrays(model, image, prep, post, 'cpu')
            _, mask = p.postprocess(probability, p.PostprocessConfig(best[0], best[1], 16))
            require(int(mask.sum()) == c['tp_pixels'] + c['fp_pixels'], 'Recomputed selected prediction changed')
            require(int((mask.astype(bool) & target.astype(bool)).sum()) == c['tp_pixels'], 'Recomputed selected intersection changed')
            targets = [m._rasterize_coco_segmentation(annotations[a]['segmentation'], row['width'], row['height']) for a in row['annotation_ids']]
            for threshold in (.1, .5):
                matches, total, fp = region_recall(mask, targets, threshold)
                for key, value in zip(('matches', 'ground_truth_instances', 'false_positive_regions'), (matches, total, fp)):
                    regions[str(threshold)][key] += value
            if row['image_id'] in example_ids:
                overlay = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
                overlay[mask.astype(bool)] = (.5 * overlay[mask.astype(bool)] + .5 * np.array([30, 120, 255])).astype(np.uint8)
                overlay[cv2.morphologyEx(target, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(bool)] = [70, 255, 70]
                cv2.imwrite(str(out / (Path(row['image_id']).stem + '_prediction_orange_reference_green.png')), overlay)
    save(out / 'per_case.json', selected)
    save(out / 'comparison.json', comparison)
    save(out / 'confidence_intervals.json', confidence(selected))
    reproduced = summary(json.loads((out / 'per_case.json').read_text()))
    require(all(reproduced[k] == metrics[k] for k in reproduced), 'Saved count table reproduction failed')
    result = {'identity': identity, 'selection': {'threshold': best[0], 'policy': best[1], 'min_pixels': 16}, 'metrics': metrics, 'regions': regions,
              'subgroups': {flag: summary([c for r, c in zip(rows, selected) if int(r[flag])]) for flag in ('hand', 'leg', 'hip', 'shoulder', 'mixed', 'hardware', 'multiscan', 'frontal', 'lateral', 'oblique') if any(int(r[flag]) for r in rows)},
              'table_reproduction_passed': True, 'examples': sorted(example_ids), 'example_rule': 'highest and lowest positive Dice, first normal, first multi-instance; orange prediction, green reference boundary',
              'timing': {'warm_shared_inference_median_ms': float(np.median(times[1:])), 'warm_shared_inference_p95_ms': float(np.percentile(times[1:], 95)), 'first_ms': times[0], 'elapsed_seconds': time.perf_counter() - started, 'scope': 'CPU shared preprocessing+forward+native postprocessing; concurrent jobs may affect time; not request latency'},
              'smoke': smoke, 'test_evaluated': split == 'test'}
    save(out / 'completed.json', result)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--final-test', action='store_true')
    ap.add_argument('--smoke-bundle')
    args = ap.parse_args()
    out = Path(args.out).resolve()
    if not out.is_relative_to(ROOT / 'experiments'):
        raise ValueError('Completion output must stay within workspace experiments')
    out.mkdir(parents=True, exist_ok=True)
    lock = out / '.runner.lock'
    with lock.open('x') as f:
        f.write(str(__import__('os').getpid()))
    try:
        torch.set_num_threads(2)
        cv2.setNumThreads(1)
        if args.smoke_bundle:
            if args.final_test:
                raise ValueError('Smoke cannot access final test')
            evaluate(Path(args.smoke_bundle).resolve(), out / 'smoke_validation', 'val', True)
            return
        manifests = p.sha(ROOT / 'experiments/data_v2/manifest.json')
        validations = {}
        for run in RUNS:
            source = ROOT / 'experiments' / run
            state = json.loads((source / 'state.json').read_text())
            config = json.loads((source / 'config.json').read_text())
            if state['status'] != 'completed' or config['smoke'] or config['manifest_sha256'] != manifests:
                raise ValueError(f'{run} is not a completed registered full v2 run')
            expected = {'size': 256, 'resize': 'letterbox', 'blur': 0, 'normalization': 'unit',
                        'positive_fraction': .5, 'seed': 42, 'batch_size': 2, 'lr': .0001,
                        'epochs': 12, 'patience': 5, 'device': 'cpu', 'elastic': False,
                        'loss': 'bce_dice' if run == RUNS[0] else 'focal_tversky'}
            require(all(config.get(k) == v for k, v in expected.items()), 'Registered training protocol changed')
            for name, digest in config['source_hashes'].items():
                if p.sha(ROOT / name) != digest:
                    raise ValueError(f'Active training source changed: {name}')
            snapshot = out / run
            if not snapshot.exists():
                snapshot.mkdir()
                for name in ('bundle.json', 'best_model.pt', 'config.json', 'epochs.jsonl'):
                    shutil.copy2(source / name, snapshot / name)
            bundle = snapshot / 'bundle.json'
            validations[run] = evaluate(bundle, snapshot / 'validation', 'val')
        winner = max(RUNS, key=lambda name: validations[name]['metrics']['mean_positive_dice'])
        # Simpler BCE+Dice retained when Dice improvement is <.005 and neither
        # sensitivity nor FPR worsens >.02. This rule is registered before test.
        a, b = (validations[n]['metrics'] for n in RUNS)
        if b['mean_positive_dice'] - a['mean_positive_dice'] < .005 and a['case_sensitivity'] >= b['case_sensitivity'] - .02 and a['normal_false_positive_rate'] <= b['normal_false_positive_rate'] + .02:
            winner = RUNS[0]
        frozen = {'selected_run': winner, 'selection_scope': 'validation only; full v2 runs; historical E1 and v1 E2 excluded from independent comparison', 'manifest_sha256': manifests,
                  'evaluator_sha256': p.sha(Path(__file__)), 'pipelines': {}}
        for run in RUNS:
            bundle = out / run / 'bundle.json'
            document = json.loads(bundle.read_text())
            document['postprocess'] = validations[run]['selection']
            document['calibration_status'] = 'Frozen using full validation; research prototype; not clinical validation'
            calibrated = out / run / 'calibrated_bundle.json'
            if calibrated.exists():
                require(json.loads(calibrated.read_text()) == document, 'Calibrated bundle changed')
            else:
                save(calibrated, document)
            frozen['pipelines'][run] = {'bundle_sha256': p.sha(calibrated), 'checkpoint_sha256': document['checkpoint_sha256'], 'postprocess': document['postprocess']}
        freeze = out / 'FROZEN_SELECTION.json'
        if freeze.exists():
            require(json.loads(freeze.read_text()) == frozen, 'Frozen selection changed')
        else:
            save(freeze, frozen)
        if args.final_test:
            for run in RUNS:
                evaluate(out / run / 'calibrated_bundle.json', out / run / 'reserved_test', 'test')
        save(out / 'completion.json', {'validation_completed': True, 'selected_run': winner, 'frozen': frozen, 'final_test_evaluated': args.final_test, 'human_review_completed': False,
                                       'next': 'Verify frozen-model API/browser parity; regenerate manuscript, then human review. Do not tune on the test.'})
        print(json.dumps({'selected': winner, 'test_evaluated': args.final_test}))
    finally:
        lock.unlink()


if __name__ == '__main__':
    main()
