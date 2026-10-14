# BASELINE_MODEL_REPORT

Measured 7 October 2026. Unchanged original checkpoint on all 612 v2 validation images (110 fractures / 502 normals). Immutable diagnostic baseline. Historical model exposure is unknown: this is NOT independent test or clinical validation.

## Classification

| Metric | Result |
|---|---:|
| accuracy | 0.256536 |
| precision | 0.192513 |
| recall_sensitivity | 0.981818 |
| specificity | 0.097610 |
| f1 | 0.321908 |
| auroc | 0.585386 |
| auprc_average_precision | 0.210279 |
| false_positive_rate | 0.902390 |
| false_negative_rate | 0.018182 |

Confusion: TN=49, FP=453, FN=2, TP=108. Accuracy 25.65% accompanies sensitivity 98.18% and specificity 9.76%; no balanced reliability claim.

Case rule: any native mask pixel retained after >=0.90 model-grid threshold and nearest-neighbor inverse resize. AUROC/AUPRC use maximum float32 sigmoid pixel output as an explicitly uncalibrated ranking proxy, not a clinical probability.

## Segmentation

| Metric | Result |
|---|---:|
| mean_positive_dice | 0.482326 |
| mean_positive_iou | 0.361818 |
| mean_positive_precision_nonempty | 0.450753 |
| mean_positive_recall | 0.621012 |
| global_dice | 0.182614 |
| global_iou | 0.100481 |
| global_pixel_precision | 0.104595 |
| global_pixel_recall | 0.718685 |

Normals excluded from positive macro Dice/IoU. Missed positive Dice/IoU/recall=0; empty prediction precision=null. Global metrics include normal false-positive pixels.

## Localization

Component-box mAP@0.50 proxy=0.017832; mAP@0.50:0.95 proxy=0.005221.

Native predicted connected-component enclosing boxes vs enclosing boxes of individual COCO polygon rasterizations; confidence=max pixel output per component; masks gated at baseline .90; one-to-one, equal-score batching, 101-point interpolated AP. Not canonical COCO mAP or a separately trained detection head.

Native mask instance matching: {"0.1": {"matches": 99, "gt": 137, "predicted": 1135, "precision": 0.08722466960352424, "recall": 0.7226277372262774, "false_positive_regions": 1036, "missed_regions": 38}, "0.5": {"matches": 45, "gt": 137, "predicted": 1135, "precision": 0.039647577092511016, "recall": 0.3284671532846715, "false_positive_regions": 1090, "missed_regions": 92}}

## Calibration

Uncalibrated maximum-pixel proxy Brier=0.751677; equal-width 10-bin ECE=0.756843. 497/612 scores equal exactly1. For the highest-score bin, mean score=0.999663, actual fracture fraction=0.192513.

These are diagnostics of an invalid case-confidence interpretation, not evidence of calibrated clinical probabilities. Serving exposes no calibrated case-confidence score.

## Subgroups and difficult cases

| Subgroup | Fractures / normals | Sensitivity | Specificity | Positive Dice |
|---|---:|---:|---:|---:|
| hand | 77 / 160 | 0.987013 | 0.068750 | 0.490305 |
| leg | 30 / 310 | 0.966667 | 0.093548 | 0.461011 |
| hip | 7 / 34 | 1.000000 | 0.264706 | 0.547235 |
| shoulder | 12 / 42 | 0.916667 | 0.404762 | 0.451056 |
| mixed | 15 / 43 | 0.933333 | 0.372093 | 0.468505 |
| hardware | 10 / 1 | 1.000000 | 0.000000 | 0.490316 |
| multiscan | 12 / 50 | 1.000000 | 0.060000 | 0.282234 |
| frontal | 69 / 315 | 0.985507 | 0.126984 | 0.460849 |
| lateral | 52 / 166 | 0.961538 | 0.078313 | 0.484457 |
| oblique | 6 / 55 | 1.000000 | 0.000000 | 0.191172 |
| small_region_proxy | 19 / 0 | 0.894737 | undefined | 0.238379 |
| multiple_fractures | 26 / 0 | 1.000000 | undefined | 0.438043 |

Flags overlap. Provider frontal is not established as AP. Small-region proxy is defined using training positive union-mask occupancy <=training 25th percentile; it is not a clinical subtle/nondisplaced label. No reliable study IDs for cross-view agreement or fusion.

## Runtime, lineage and limitations

CPU forward median 403.2ms / p95 470.1ms; decode/preprocess/forward/native-mask median 411.7ms. Full measurement pass 282.1s; peak process RSS 928059392bytes. Parameters 31387045.

Checkpoint SHA-256 `922f30bf691b9979aee65d386bcf73d2643558c049a7d11ab013fea315f39b81`; manifest SHA-256 `19a950c34d96c0fc076fbb75bdeffbf2f0b262626817d61018eff31e907544bb`. Python/torch/environment and source snapshots are in config.json/source_snapshot/.

All native reference/predicted masks saved in masks/. Every false positive, false negative and algorithmically tagged positive segmentation failure has a original/reference/prediction panel in failures/ plus a failure_review.csv row. Clinical causes are unadjudicated; numerical failure tags describe overlap, not diagnosis.

All metrics and subgroups: metrics.json; exact per-case counts: per_case.json; float32 probability cache: probabilities_float32.npz; confusion/ROC/PR: confusion_roc_pr.png and curves.json; calibration: reliability_curve.png; recomputed split overlap audit: split_audit.json.

Known duplicate groups are disjoint. No patient/study identifiers are available, so patient independence remains unverified. Original training exposure is unknown. Current data is already FracAtlas; no external validation occurred. Clinical subtle/nondisplaced, reader agreement/correction and scanner/hospital shift measurements are unavailable.

No model/threshold/preprocessing change, no training, no test inference, no candidate promotion and no >90% claim during this baseline. A separate validation/calibration partition is needed prospectively for new experiments; retrospective splitting does not erase older E2 validation exposure.

Measurement finished successfully in the CPU demo runtime. Its missing matplotlib prevented plots/report only. Finalization used already-installed matplotlib3.10.6 in the existing research runtime; saved measurements/masks were neither rerun nor changed.
