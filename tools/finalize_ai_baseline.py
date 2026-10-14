"""Finalize saved baseline measurements after plotting dependency failure.

No inference or training; existing metrics and masks remain byte-identical.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.evaluate_ai_baseline import figures, save, sha


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline', required=True)
    args = ap.parse_args()
    out = Path(args.baseline).resolve()
    if ROOT not in out.parents or (out/'completion.json').exists() or (out/'BASELINE_MODEL_REPORT.md').exists():
        raise ValueError('Completed baseline cannot be overwritten')
    result = json.loads((out/'metrics.json').read_text())
    cases = json.loads((out/'per_case.json').read_text())
    config = result['config']
    if len(cases) != 612 or config['split'] != 'val' or result['test_images_read'] != 0:
        raise ValueError('Full unchanged validation measurements required')
    metric_hash, case_hash = sha(out/'metrics.json'), sha(out/'per_case.json')
    if sha(ROOT/'best_model.pt') != config['checkpoint_sha256']:
        raise ValueError('Production checkpoint changed')
    if sha(ROOT/'experiments/data_v2/manifest.json') != config['manifest_sha256']:
        raise ValueError('Baseline manifest changed')
    figures(out, cases, result)
    cl, seg, cal, loc = (result[k] for k in ('classification','segmentation','calibration','localization'))
    lines = ['# BASELINE_MODEL_REPORT', '', 'Measured 7 October 2026. Unchanged original checkpoint on all 612 v2 validation images (110 fractures / 502 normals). Immutable diagnostic baseline. Historical model exposure is unknown: this is NOT independent test or clinical validation.', '',
             '## Classification', '', '| Metric | Result |', '|---|---:|']
    for key in ('accuracy','precision','recall_sensitivity','specificity','f1','auroc','auprc_average_precision','false_positive_rate','false_negative_rate'):
        lines.append(f'| {key} | {cl[key]:.6f} |')
    cm = cl['confusion_matrix']
    lines += ['', f'Confusion: TN={cm["tn"]}, FP={cm["fp"]}, FN={cm["fn"]}, TP={cm["tp"]}. Accuracy 25.65% accompanies sensitivity 98.18% and specificity 9.76%; no balanced reliability claim.', '',
              'Case rule: any native mask pixel retained after >=0.90 model-grid threshold and nearest-neighbor inverse resize. AUROC/AUPRC use maximum float32 sigmoid pixel output as an explicitly uncalibrated ranking proxy, not a clinical probability.', '',
              '## Segmentation', '', '| Metric | Result |', '|---|---:|']
    for key in ('mean_positive_dice','mean_positive_iou','mean_positive_precision_nonempty','mean_positive_recall','global_dice','global_iou','global_pixel_precision','global_pixel_recall'):
        lines.append(f'| {key} | {seg[key]:.6f} |')
    lines += ['', seg['empty_policy'], '', '## Localization', '',
              f'Component-box mAP@0.50 proxy={loc["component_box_map50"]:.6f}; mAP@0.50:0.95 proxy={loc["component_box_map50_95"]:.6f}.', '', loc['method'], '',
              f'Native mask instance matching: {json.dumps(result["mask_instance_localization"])}', '', '## Calibration', '',
              f'Uncalibrated maximum-pixel proxy Brier={cal["brier_score"]:.6f}; equal-width 10-bin ECE={cal["expected_calibration_error"]:.6f}. {cal["score_exactly_one_count"]}/612 scores equal exactly1. For the highest-score bin, mean score={cal["reliability_curve"][-1]["mean_score"]:.6f}, actual fracture fraction={cal["reliability_curve"][-1]["observed_fracture_fraction"]:.6f}.', '',
              'These are diagnostics of an invalid case-confidence interpretation, not evidence of calibrated clinical probabilities. Serving exposes no calibrated case-confidence score.', '',
              '## Subgroups and difficult cases', '', '| Subgroup | Fractures / normals | Sensitivity | Specificity | Positive Dice |', '|---|---:|---:|---:|---:|']
    def value(v): return f'{v:.6f}' if v is not None else 'undefined'
    for name, group in result['subgroups'].items():
        if group:
            c, s = group['classification'], group['segmentation']
            lines.append(f'| {name} | {c["positive"]} / {c["normal"]} | {value(c["recall_sensitivity"])} | {value(c["specificity"])} | {value(s["mean_positive_dice"])} |')
    lines += ['', 'Flags overlap. Provider frontal is not established as AP. Small-region proxy is defined using training positive union-mask occupancy <=training 25th percentile; it is not a clinical subtle/nondisplaced label. No reliable study IDs for cross-view agreement or fusion.', '',
              '## Runtime, lineage and limitations', '',
              f'CPU forward median {result["timing"]["forward_median_ms"]:.1f}ms / p95 {result["timing"]["forward_p95_ms"]:.1f}ms; decode/preprocess/forward/native-mask median {result["timing"]["decode_preprocess_forward_native_median_ms"]:.1f}ms. Full measurement pass {result["timing"]["elapsed_seconds"]:.1f}s; peak process RSS {result["timing"]["peak_rss_bytes"]}bytes. Parameters {result["architecture_parameter_count"]}.', '',
              f'Checkpoint SHA-256 `{config["checkpoint_sha256"]}`; manifest SHA-256 `{config["manifest_sha256"]}`. Python/torch/environment and source snapshots are in config.json/source_snapshot/.', '',
              'All native reference/predicted masks saved in masks/. Every false positive, false negative and algorithmically tagged positive segmentation failure has a original/reference/prediction panel in failures/ plus a failure_review.csv row. Clinical causes are unadjudicated; numerical failure tags describe overlap, not diagnosis.', '',
              'All metrics and subgroups: metrics.json; exact per-case counts: per_case.json; float32 probability cache: probabilities_float32.npz; confusion/ROC/PR: confusion_roc_pr.png and curves.json; calibration: reliability_curve.png; recomputed split overlap audit: split_audit.json.', '',
              'Known duplicate groups are disjoint. No patient/study identifiers are available, so patient independence remains unverified. Original training exposure is unknown. Current data is already FracAtlas; no external validation occurred. Clinical subtle/nondisplaced, reader agreement/correction and scanner/hospital shift measurements are unavailable.', '',
              'No model/threshold/preprocessing change, no training, no test inference, no candidate promotion and no >90% claim during this baseline. A separate validation/calibration partition is needed prospectively for new experiments; retrospective splitting does not erase older E2 validation exposure.', '',
              'Measurement finished successfully in the CPU demo runtime. Its missing matplotlib prevented plots/report only. Finalization used already-installed matplotlib3.10.6 in the existing research runtime; saved measurements/masks were neither rerun nor changed.']
    with (out/'BASELINE_MODEL_REPORT.md').open('x', encoding='utf-8') as f:
        f.write('\n'.join(lines)+'\n')
    if sha(out/'metrics.json') != metric_hash or sha(out/'per_case.json') != case_hash:
        raise RuntimeError('Immutable measurements changed')
    (out/'source_snapshot'/'finalize_ai_baseline.py').write_bytes(Path(__file__).read_bytes())
    save(out/'completion.json', dict(status='completed', baseline_immutable=True, test_images_read=0,
         report_sha256=sha(out/'BASELINE_MODEL_REPORT.md'), metrics_sha256=metric_hash, cases_sha256=case_hash,
         postprocessing_recovery='Saved exact measurements retained after missing matplotlib; figures/report only completed in existing research runtime',
         finalizer_sha256=sha(__file__)))
    print('Immutable BASELINE_MODEL_REPORT completed from preserved measurements')


if __name__=='__main__':
    main()
