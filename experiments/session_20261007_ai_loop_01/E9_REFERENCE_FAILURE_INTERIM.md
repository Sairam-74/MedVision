# E9 completed reference: interim failure analysis

E9 completed all12 registered continuation epochs. This analysis uses its completed native VAL audit, saved per-case results, raw TRAIN grid fit and epoch logs; it does not run inference or read CAL/test data. E10 remains outside this analysis. No next factor is selected or implemented.

The registered selector chose **additional epoch9/global27**, checkpoint `770c791a49073ad36d77095fe9f900ac51c02024cf99b385780103d9e748144f`. Every epoch reports all2,808 unique TRAIN sources. Epoch10's larger Dice0.415302 came with TN99/380; epoch11 reached TP78 but TN74. Final epoch12 had Dice0.365483, TP76/TN105. The common balance rule retained epoch9. Selection must not be replaced by cherry-picking the largest Dice or recall.

## Same463 native validation comparison

Saved case IDs and source labels were independently checked to match exactly:83 fracture/380 normal. The original baseline uses its preserved inference policy; E7/E9 use the registered research policy. E7's audit was CPU and E9's was CUDA; small floating boundary differences remain a comparison limit. These are diagnostic development comparisons, not independent patient-level validation.

| Metric | Same-ID original | E7 selected | E9 selected |
|---|---:|---:|---:|
| TP / FN | 83 /0 | 61 /22 | 67 /16 |
| TN / FP | 43 /337 | 215 /165 | 171 /209 |
| Accuracy | 0.272138 | 0.596112 | 0.514039 |
| Sensitivity | 1.000000 | 0.734940 | 0.807229 |
| Specificity | 0.113158 | 0.565789 | 0.450000 |
| Precision / F1 | 0.197619 /0.330020 | 0.269912 /0.394822 | 0.242754 /0.373259 |
| AUROC / AUPRC | 0.601807 /0.215662 | 0.708402 /0.464962 | 0.785098 /0.592641 |
| Positive Dice / IoU | 0.503797 /0.377569 | 0.270492 /0.198868 | 0.359342 /0.265569 |
| Native GT-overlap pixels | 286345 | 52106 | 134900 |
| Native false-positive pixels | 2589612 | 235568 | 787579 |
| Native false-negative pixels | 105782 | 340021 | 257227 |
| Global pixel recall | 0.730235 | 0.132880 | 0.344021 |
| Mask-instance IoU0.5 matches /99 | 35 | 23 | 24 |
| Mask-instance IoU0.5 precision | 0.040936 | 0.068862 | 0.055814 |
| Positives with any GT overlap /83 | 77 | 46 | 56 |

E9 improves learning/ranking and positive overlap relative to E7, while producing44 extra normal alerts, more than three times its false-positive pixels and worse F1/calibration proxies. It still misses16 fractures by the case-alert definition and fails the frozen TP79/TN342 targets. Native Dice/IoU, instance recall and useful pixel coverage remain worse than the original. This is not balanced model improvement or a promotion result.

**A case TP is an image alert, not proof of fracture localization.** E9's67 positive-image alerts comprise56 with some GT overlap and11 with no GT overlap. Alongside16 empty misses,27/83 positives have no useful overlapping mask. The failure tags count16 complete empty misses,11 complete mislocalizations,19 under-segmentation and21 over-segmentation; tags can overlap. The56 uniquely tagged positives have a completed actual review recorded in `E9_all_positive_sheets/completion.json`. Normal-panel review is being handled by root and was incomplete when this memo was prepared; this memo does not claim to have reviewed those X-rays.

The separate component-box AP proxy is0.112039 atIoU0.5 and0.043043 across0.5:0.95. It is not canonical COCO detector mAP and must not be confused with mask-instance matching: box matching gives22 while mask matching gives24.

## Per-case transitions

Relative to E7,41 normal FP cases recover but85 become new FPs. Eight previously empty positive masks become image alerts while two new empty misses appear; those eight alerts are not automatically correctly localized. Twelve positives gain any GT overlap and two lose all overlap. Positive Dice rises by>0.02 in42 cases and falls by>0.02 in13.

Relative to the original,139 normal FPs recover and11 new FPs appear;16 new empty positive misses occur. One positive gains any overlap but22 lose all overlap. Dice gains>0.02 occur in25 positives and losses>0.02 in45. Exact transition IDs are retained in the accompanying `E9_REFERENCE_FAILURE_INTERIM_DATA.json`.

## Remaining anatomy/view weaknesses

The flags are nonexclusive source metadata; row counts and errors must not be summed across rows. Source frontal is not verified AP, and multiscan/view flags do not establish linked study views.

| Stratum | E7 TP /positive; FP /normal | E9 TP /positive; FP /normal | E9 positive Dice; positives touching GT |
|---|---|---|---|
| Hand | 54 /63;74 /118 | 56 /63;81 /118 | 0.410538;47 /63 |
| Leg | 6 /18;87 /237 | 8 /18;116 /237 | 0.182888;7 /18 |
| Hip | 3 /4;9 /29 | 4 /4;16 /29 | 0.382681;4 /4 |
| Shoulder | 2 /7;10 /31 | 5 /7;14 /31 | 0.180061;3 /7 |
| Hardware | 1 /7;1 /1 | 3 /7;1 /1 | 0.038472;1 /7 |
| Frontal | 36 /51;109 /246 | 42 /51;133 /246 | 0.347781;35 /51 |
| Lateral | 30 /39;59 /122 | 31 /39;82 /122 | 0.359144;25 /39 |
| Oblique | 1 /5;10 /37 | 3 /5;12 /37 | 0.123209;1 /5 |
| Small native-mask proxy | 10 /12;no normals | 11 /12;no normals | 0.273206;8 /12 |
| Multiple annotations | 13 /16;no normals | 13 /16;no normals | 0.391444;11 /16 |

Leg global pixel recall is0.019619 despite8 image alerts; hardware recall of GT pixels is0.001785 despite3 alerts. These pixel-weighted summaries can be dominated by large annotated regions, but they demonstrate why case recall alone is inadequate. Hardware/hip/oblique sample sizes are tiny. Small-mask proxy uses the TRAIN25th-percentile native area fraction0.002055; it is not an expert subtle/nondisplaced label. Multiple annotations do not establish multiple clinical fractures.

Existing FP technical tags show edge enrichment in171/209 cases, source multiscan27 and hardware1. They are observed associations, not clinical causes or proof of shortcut learning. Neither these tags nor the subgroup tables justify relabeling or changing the active hard pair.

## TRAIN fit and score trust

Raw, unaugmented TRAIN **grid** fit changes from E7 Dice0.273254/IoU0.196424 to E9 Dice0.353313/IoU0.260231. Zero-overlap positive masks fall219→143/493; TP365→432, FN128→61, but normal FP1032→1233 and TN1283→1082. TRAIN AUROC rises0.727581→0.809035. This supports continued learning with an FP/coverage tradeoff, rather than a validation-only problem or a demonstrated plateau. TRAIN grid pixel counts and geometry must not be compared directly with native VAL counts.

I actually inspected the saved E9 confusion/ROC/PR and reliability plots. ROC ranking is better than chance, but precision drops toward the positive prevalence at high recall. The197-case highest proxy-score bin averages0.975209 while its observed fracture fraction is0.319797. Maximum-pixel sigmoid is not calibrated fracture probability. Its diagnostic Brier/ECE worsen from E7's0.319183/0.348326 to E9's0.407209/0.434087; they remain below the original0.738704/0.745993. This does not constitute a calibrated-confidence improvement.

No threshold sweep was run. A monotone single-score classifier attainingTP79/83 andTN342/380 requires AUROC at least `(79/83)*(342/380)=0.8566265`, because the ROC area afterFPR0.1 alone must be at least0.9×that sensitivity. E9's selected AUROC0.785098 and maximum across all12 epochs0.798637 fall below this necessary bound. Threshold adjustment or monotone calibration of these score rankings cannot by itself deliver the frozen target. This mathematical bound neither selects a different model nor replaces later calibration.

E9 is the unchanged factor1 continuation reference; its gains cannot be attributed to hard weighting. Finish E10, compare matched native metrics and raw TRAIN fit, review its actual failures and the remaining E9 normals, then determine one subsequent intervention. Patient/study independence, expert clinical subtype labels, radiologist corrections and external validation remain unverified. Original exposure is unknown. No new CAL/test predictions, promotion, or production changes occurred.

Evidence: completed `AI_E9_v3_hard_reference/epochs.jsonl`, `best_validation.json`, `bundle.json`; `AI_AUDIT_E9_v3_hard_reference/{metrics.json,per_case.json,review_alert_confusion_roc_pr.png,review_alert_reliability.png}`; E7 equivalents; preserved `AI_BASELINE_20261007_v1/per_case.json`; `AI_LEARNING_FIT_E9_v3_hard_reference/metrics.json`; E7 TRAIN metrics; E9 `error_groups.json`. The companion JSON records input hashes, all exact transition IDs and three-model subgroup summaries. All paths are under `experiments/`.
