"""Matched E5/E6 validation decision and error transitions; never reads test pixels."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.evaluate_ai_baseline import save, sha, write_csv


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def comparison(left, right):
    metrics = {}
    for family, keys in [('classification', ('accuracy', 'precision', 'recall_sensitivity', 'specificity', 'f1', 'auroc',
                                             'auprc_average_precision', 'false_positive_rate', 'false_negative_rate')),
                         ('segmentation', ('mean_positive_dice', 'mean_positive_iou', 'global_pixel_precision',
                                           'global_pixel_recall', 'global_dice', 'global_iou')),
                         ('calibration', ('brier_score', 'expected_calibration_error'))]:
        metrics[family] = {key: dict(reference=left[family][key], candidate=right[family][key],
                                    absolute_delta=right[family][key]-left[family][key]
                                    if right[family][key] is not None and left[family][key] is not None else None)
                           for key in keys}
    return metrics


def transitions(left, right):
    l = {c['image_id']: c for c in left}
    r = {c['image_id']: c for c in right}
    if set(l) != set(r) or len(l) != 463:
        raise ValueError('Comparisons must use the EXACT same463 frozen validation IDs')
    result = {}
    for name, condition in [
        ('normal_FP_recovered', lambda a,b: not a['positive'] and a['prediction_present'] and not b['prediction_present']),
        ('normal_new_FP', lambda a,b: not a['positive'] and not a['prediction_present'] and b['prediction_present']),
        ('fracture_FN_recovered', lambda a,b: a['positive'] and not a['prediction_present'] and b['prediction_present']),
        ('fracture_new_FN', lambda a,b: a['positive'] and a['prediction_present'] and not b['prediction_present']),
        ('fracture_new_zero_overlap', lambda a,b: a['positive'] and a['tp_pixels']>0 and b['prediction_present'] and b['tp_pixels']==0),
        ('fracture_Dice_gain_over_02', lambda a,b: a['positive'] and b['dice']-a['dice'] > .02),
        ('fracture_Dice_loss_over_02', lambda a,b: a['positive'] and a['dice']-b['dice'] > .02),
    ]:
        ids = sorted(key for key in l if condition(l[key], r[key]))
        result[name] = dict(n=len(ids), image_ids=ids)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference', required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    left_dir, right_dir, out = [Path(v).resolve() for v in (args.reference, args.candidate, args.out)]
    if ROOT not in out.parents or out.exists():
        raise ValueError('Use a new workspace output directory')
    for directory in (left_dir, right_dir):
        if not (directory/'completion.json').exists():
            raise ValueError('Both FULL audits must finish before deciding')
    left, right = load(left_dir/'metrics.json'), load(right_dir/'metrics.json')
    lc, rc = load(left_dir/'per_case.json'), load(right_dir/'per_case.json')
    left_run, right_run = [ROOT/result['config']['run'] for result in (left, right)]
    conf_left, conf_right = [load(run/'config.json') for run in (left_run, right_run)]
    for key in ('manifest_sha256', 'archive_sha256', 'preprocess', 'loss_config', 'postprocess', 'batch_size',
                'lr', 'seed', 'elastic', 'positive_fraction', 'source_hashes', 'device', 'torch', 'epochs', 'patience'):
        if conf_left[key] != conf_right[key]:
            raise ValueError('Uncontrolled pair factor: '+key)
    if conf_left['normal_bce_weight'] != 1 or conf_right['normal_bce_weight'] != 2:
        raise ValueError('Expected the registered single-factor BCE1/BCE2 pair')
    init_left, init_right = [load(run/'initial_parameters.json')['parameter_sha256'] for run in (left_run, right_run)]
    if init_left != init_right:
        raise ValueError('Matched initialization differed')
    original_dir = ROOT/'experiments/AI_BASELINE_20261007_v1'
    all_original = load(original_dir/'per_case.json')
    ids = {c['image_id'] for c in lc}
    original_cases = [c for c in all_original if c['image_id'] in ids]
    from tools import ai_metrics as a
    # Existing original score/postprocess scope is preserved, not relabelled.
    original = dict(classification=a.classification(original_cases), segmentation=a.segmentation(original_cases),
                    calibration=a.calibration(original_cases))
    metrics = comparison(left, right)
    counts = right['classification']['confusion_matrix']
    target_counts = counts['tp'] >= 79 and counts['tn'] >= 342 and right['classification']['accuracy'] >= .9
    development_keep = (right['classification']['specificity'] > left['classification']['specificity']
                        and right['classification']['recall_sensitivity'] >= left['classification']['recall_sensitivity']
                        and right['segmentation']['mean_positive_dice'] >= left['segmentation']['mean_positive_dice']
                        and right['segmentation']['mean_positive_iou'] >= left['segmentation']['mean_positive_iou'])
    segmentation_target = right['segmentation']['mean_positive_dice'] >= max(
        original['segmentation']['mean_positive_dice'], left['segmentation']['mean_positive_dice'])+.02
    localization_target = all(right['mask_instance_localization']['0.5'][key] is not None and
                              right['mask_instance_localization']['0.5'][key] >
                              a.ratio(sum(c['mask_region_matches_iou50'] for c in original_cases),
                                      sum(c['predicted_components' if key=='precision' else 'gt_instances'] for c in original_cases))
                              for key in ('precision', 'recall'))
    out.mkdir()
    result = dict(reference=str(left_dir.relative_to(ROOT)), candidate=str(right_dir.relative_to(ROOT)),
                  factor='Normal-image BCE coefficient1 ->2 only', initialization_matched=True,
                  config_factors_matched=True, same463_validation_ids=True,
                  metrics=metrics, original_same_ID_comparison=comparison(original, right),
                  reference_to_candidate_errors=transitions(lc, rc), original_to_candidate_errors=transitions(original_cases, rc),
                  decision='KEEP DEVELOPMENT CANDIDATE; not production' if development_keep else 'REJECT stronger normal BCE as an overall improvement at registered default point',
                  practical_classification_target_pass=target_counts,
                  positive_dice_target_pass=segmentation_target, native_localization_target_pass=localization_target,
                  final_success=False, promotion=False, test_images_read=0,
                  limitations=['No clinical cause adjudication', 'Original historical exposure unknown',
                               'Default threshold decision only; improved discriminative scores require validation operating-point evaluation',
                               'No test/calibration/external/radiologist success claim'])
    save(out/'comparison.json', result)
    rows = []
    for family, values in metrics.items():
        for key, values in values.items():
            rows.append(dict(family=family, metric=key, **values))
    write_csv(out/'comparison.csv', rows)
    # Matched learning curves, not an accuracy-only cherry-picked epoch.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    for run, label in ((left_run, 'normal BCE1'), (right_run, 'normal BCE2')):
        epochs = [json.loads(line) for line in (run/'epochs.jsonl').read_text().splitlines() if line.strip()]
        xx = [v['epoch'] for v in epochs]
        ys = [[v['loss_components']['total'] for v in epochs],
              [v['validation']['classification']['recall_sensitivity'] for v in epochs],
              [v['validation']['classification']['specificity'] for v in epochs],
              [v['validation']['classification']['auroc'] for v in epochs],
              [v['validation']['delivered']['mean_positive_dice'] for v in epochs],
              [v['validation']['delivered']['mean_positive_iou'] for v in epochs]]
        for ax, yy, title in zip(axes.ravel(), ys, ('Training loss', 'Validation sensitivity', 'Validation specificity',
                                                   'Validation AUROC', 'Positive native Dice', 'Positive native IoU')):
            ax.plot(xx, yy, marker='o', label=label)
            ax.set(title=title, xlabel='Epoch'); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(out/'paired_learning_curves.png', dpi=150); plt.close(fig)
    report = ['# Controlled normal-supervision result', '', result['decision'], '',
              '## Matched default operating points', '', '| Metric | BCE1 | BCE2 | Change |', '|---|---:|---:|---:|']
    for family, values in metrics.items():
        for key, v in values.items():
            report.append(f"| {family}.{key} | {v['reference']} | {v['candidate']} | {v['absolute_delta']} |")
    report += ['', '## Error transitions', '', json.dumps(result['reference_to_candidate_errors'], indent=2), '',
               'Inspect retained actual masks and panels before assigning causes. View and hardware associations are not causal proof.', '',
               f'Classification counts pass: {target_counts}; Dice target pass: {segmentation_target}; native localization target pass: {localization_target}.', '',
               'No final success/promotion/test access. Original comparison uses the SAME463 IDs but unknown original exposure remains. Next intervention requires recorded failure analysis, not random technique selection.']
    with (out/'PAIR_ANALYSIS.md').open('x', encoding='utf-8') as handle:
        handle.write('\n'.join(report)+'\n')
    save(out/'completion.json', dict(status='completed', comparison_sha256=sha(out/'comparison.json'), test_images_read=0))
    print(json.dumps({key: result[key] for key in ('decision', 'practical_classification_target_pass', 'positive_dice_target_pass', 'native_localization_target_pass')}, indent=2))


if __name__ == '__main__':
    main()
