# E9/E10 completed curves, strata, fit and gate analysis — 8 October 2026

E10 hard-example factor 2 is a useful development result, but it has not reached the frozen reliability targets and is not ready for promotion. Both arms used the same selected E7 model/Adam state, natural unique one-pass TRAIN coverage and twelve additional epochs; only the bounded within-class hard-example factor differed. The selected snapshots are E9 additional epoch 9/global epoch 27 and E10 additional epoch 12/global epoch 30. The shared selection rule and total budgets match; the selected training ages differ.

## Evidence and scope

Before analysis, all 18 unique recorded source hashes were verified against current files. Native completion hashes and selected-checkpoint hashes were checked without loading models. Both native audits have exactly the frozen 463 VAL IDs, agreeing labels, duplicate groups and archive member paths; each selected trainer result reproduces the native audit score, decision and pixel counts exactly. Both TRAIN-fit files have exactly 2,808 unique TRAIN IDs with agreeing labels/groups. Only hard_factor differs in training configuration; initialization metadata is identical. Each arm completed global epochs 19–30 and saw 2,808 unique TRAIN sources in each epoch. Source/input SHA256 values, all per-ID transitions and full subgroup results are in the accompanying DATA.json.

No source radiographs or mask arrays were read, and no new predictions, model loads, CUDA work, calibration fit, reserved-test access, promotion or new experimental factor were performed for this analysis. Paired curves and E10 confusion/ROC/PR/reliability plots were actually viewed.

## Selected native VAL comparison

| Metric | E9 factor1 | E10 factor2 |
|---|---:|---:|
| Accuracy | 0.5140 | 0.5356 |
| Precision | 0.2428 | 0.2519 |
| Sensitivity | 0.8072 | 0.8072 |
| Specificity | 0.4500 | 0.4763 |
| F1 | 0.3733 | 0.3840 |
| False-positive rate | 0.5500 | 0.5237 |
| False-negative rate | 0.1928 | 0.1928 |
| AUROC | 0.7851 | 0.7853 |
| Average precision/AUPRC | 0.5926 | 0.5740 |
| Positive Dice | 0.3593 | 0.3795 |
| Positive IoU | 0.2656 | 0.2837 |
| Pixel precision | 0.1462 | 0.2211 |
| Pixel recall | 0.3440 | 0.4280 |

E9: native TP/FN/TN/FP = 67/16/171/209; native pixel TP/FP/FN = 134,900/787,579/257,227. Mask-instance IoU0.5 matches 24/99 among 430 predicted regions; precision 0.0558 and recall 0.2424.

E10: native TP/FN/TN/FP = 67/16/181/199; native pixel TP/FP/FN = 167,845/591,338/224,282. Mask-instance IoU0.5 matches 28/99 among 402 predicted regions; precision 0.0697 and recall 0.2828.

E10 reduces normal alerts by 10 while retaining the same total of 67 detected fractures and 16 misses. Case changes include 56 recovered normal false positives, 46 new normal false positives, 5 recovered fractures and 5 different fractures becoming misses. The recovered fractures are IMG0000471, IMG0001710, IMG0001948, IMG0002086 and IMG0002392; the new misses are IMG0001073, IMG0002181, IMG0002463, IMG0002502 and IMG0002549 (all .jpg). Paired positive Dice increases by 0.020185 and IoU by 0.018099, while mask-instance matches rise 24→28. Average precision decreases 0.592641→0.574039; AUROC changes only 0.785098→0.785289.

## Curves and stability

| Arm | Epochs | First→last TRAIN objective | Maximum saved AUROC (epoch) | Maximum positive Dice (epoch) | Selected epoch |
|---|---:|---|---|---|---|
| E9 | 12 | 0.956365→0.945200 | 0.798637 (10) | 0.415302 (10) | 9 |
| E10 | 12 | 0.966358→0.955818 | 0.806420 (10) | 0.405541 (8) | 12 |

The within-arm TRAIN objective falls, while VAL case counts and localization fluctuate substantially. Absolute loss values across arms are not directly comparable: E10 weights harder examples more, and the logs describe different augmented objectives. E9 TP varies 63–78 and TN 65–171. E10 TP varies 59–82 and TN 27–231; its epoch 5 reaches 79 TP with only 35 TN, and epoch 9 reaches 82 TP with only 27 TN. None of the 24 epochs meets both frozen case-count requirements. Higher-Dice epochs are retained but were not selected because the shared rule also requires normal rejection.

To achieve TP≥79 and TN≥342 with a monotone cutoff on one case score, at least 79×342 of 83×380 positive/negative pairs must be ranked correctly. Thus AUROC≥0.856626506 is necessary. All saved epoch AUROCs, including the selected scores, fall below that bound. A cutoff alone cannot achieve those counts for these saved scores; an AUROC above the bound would still not prove that a valid cutoff exists. No threshold search or policy change was performed.

## TRAIN versus VAL fit

| Arm/data | TP/FN/TN/FP | Positive Dice | Positive IoU | AUROC | Positive zero-overlap masks |
|---|---|---:|---:|---:|---:|
| E9 TRAIN256 grid | 432/61/1082/1233 | 0.3533 | 0.2602 | 0.8090 | 143/493 |
| E9 VAL native | 67/16/171/209 | 0.3593 | 0.2656 | 0.7851 | 27/83 |
| E10 TRAIN256 grid | 416/77/1172/1143 | 0.3751 | 0.2815 | 0.8053 | 151/493 |
| E10 VAL native | 67/16/181/199 | 0.3795 | 0.2837 | 0.7853 | 27/83 |

TRAIN masks use the 256 grid; VAL masks use native inverse probabilities. Their macro similarity does not establish a controlled generalization gap, and their pooled pixel counts have different scales. TRAIN performance itself remains poor: E10 has 1,143 normal alerts, 77 fracture misses and 151/493 zero-overlap fracture masks. E10 TRAIN zero-overlap count increases 143→151 versus E9, despite higher mean Dice; TRAIN sensitivity also decreases 87.63%→84.38%. This argues against a validation-only overfitting/domain-shift explanation. Weighting improves some spatial precision but does not resolve lesion-versus-normal separation or coverage.

## Native performance by source subgroup

Flags are nonexclusive, so rows must not be summed. Frontal is not a verified AP label. Small_region_proxy is the frozen TRAIN-area cutoff, not a clinical subtle/nondisplaced diagnosis; multiple_fractures means annotation-count>1. Small subgroup denominators limit interpretation.

| Source flag | Fractures/normals | E9 TP / FP | E10 TP / FP | E9 Dice | E10 Dice |
|---|---:|---:|---:|---:|---:|
| hand | 63/118 | 56/81 | 56/63 | 0.4105 | 0.4304 |
| leg | 18/237 | 8/116 | 8/124 | 0.1829 | 0.1889 |
| hip | 4/29 | 4/16 | 3/16 | 0.3827 | 0.2861 |
| shoulder | 7/31 | 5/14 | 6/16 | 0.1801 | 0.2343 |
| mixed | 9/34 | 6/18 | 6/20 | 0.2357 | 0.1997 |
| hardware | 7/1 | 3/1 | 4/1 | 0.0385 | 0.0704 |
| multiscan | 9/37 | 7/27 | 5/26 | 0.2175 | 0.2305 |
| frontal | 51/246 | 42/133 | 41/134 | 0.3478 | 0.3603 |
| lateral | 39/122 | 31/82 | 31/74 | 0.3591 | 0.3812 |
| oblique | 5/37 | 3/12 | 2/11 | 0.1232 | 0.1681 |
| small_region_proxy | 12/0 | 11/0 | 10/0 | 0.2732 | 0.3381 |
| multiple_fractures | 16/0 | 13/0 | 12/0 | 0.3914 | 0.3889 |

The net normal-rejection gain is concentrated in the hand flag: 81→63 FP with 56/63 fracture detections unchanged. Leg detections remain poor at 8/18 fractures, while FP increase from 116 to 124 among 237 normals. Hip detections decrease from 4 to 3 among 4 fractures; shoulder detections rise from 5 to 6 among 7, but FP increase from 14 to 16 among 31 normals. Multi-scan fracture detections decrease from 7 to 5 among 9. Frontal detections decrease from 42 to 41 among 51 fractures, with FP increasing from 133 to 134 among 246 normals. Lateral detections stay at 31/39 with FP falling from 82 to 74 among 122 normals; oblique detections decrease from 3 to 2 among 5 fractures, with FP falling from 12 to 11 among 37 normals. Small-region detections decrease from 11 to 10 among 12 despite mean Dice improvement, and multiple-annotation detections decrease from 13 to 12 among 16. These regressions prevent a claim of uniform difficult-case or view reliability improvement.

## Uncalibrated confidence diagnostics

Both models have presence supervision disabled; the case score is the maximum native sigmoid pixel, not a probability that the whole image has a fracture. These saved calibration diagnostics are on VAL only and do not represent fitting a calibrator.

| Diagnostic | E9 | E10 |
|---|---:|---:|
| Brier | 0.407209 | 0.362700 |
| ECE (10 equal-width bins) | 0.434087 | 0.398578 |

E9: normal-score median 0.686889, false-positive median 0.940997, and false-negative median 0.058009. 134/380 normals have scores≥0.9. The 0.9–1.0 bin contains 197 images with mean score 0.975209 but observed fracture fraction 0.319797.

E10: normal-score median 0.615553, false-positive median 0.892922, and false-negative median 0.039756. 94/380 normals have scores≥0.9. The 0.9–1.0 bin contains 152 images with mean score 0.964837 but observed fracture fraction 0.381579.

For context, a constant equal to observed VAL prevalence has in-sample Brier 0.147129. This is a descriptive reference, not a fitted/deployed model. E10 lowers Brier/ECE relative to E9, but the proxy remains strongly overconfident and cannot be presented to radiologists as clinical confidence. Calibration alone cannot repair localization, missing masks or below-bound ranking.

## Frozen acceptance and remaining bottleneck

| Gate | E10 evidence | Result |
|---|---|---|
| TP≥79 and TN≥342 | TP67, TN181:12 additional fractures and161 additional normals required | FAIL |
| Accuracy≥90% | 248/463=53.56% | FAIL |
| Native Dice≥max(original, matched)+0.02 | Required0.523797; measured0.379528 | FAIL |
| Native IoU improves beyond original | Required>0.377569; measured0.283667 | FAIL |
| Mask-instance IoU0.5 precision improves | 28/402=0.069652 vs original35/855=0.040936 | PASS numerically |
| Mask-instance IoU0.5 recall improves | 28/99 vs original35/99 | FAIL |
| Fewer FP pixels | 591,338 vs E9 787,579 and original 2,589,612 | PASS numerically |
| Useful coverage preserved | Pixel recall 0.428037 vs E9 0.344021, but original 0.730235 | LARGE COVERAGE LOSS STILL UNRESOLVED |
| Calibration/robustness/final freeze | Not performed; candidate fails earlier gates | NOT PASSED |

The best supported remaining bottleneck is inadequate learned lesion-versus-normal separation and spatial coverage. Evidence combines poor TRAIN fit, below-bound VAL ranking, many zero-overlap masks, failure churn and subgroup regressions. This is more specific than merely choosing a threshold, and it does not prove that one loss, BatchNorm behavior, architecture, resolution or annotation mechanism caused the problem. Those mechanisms need separate controlled evidence before selecting the next factor. Existing actual mask reviews should guide that investigation; this analysis did not repeat them. E10 can be retained for development comparison, but neither the balanced final objective nor radiologist trust is established.

## Timing interpretation and metadata correction

The completed native audits ran CUDA, as both device fields and exact trainer reproduction show. Their inherited timing_context/context text incorrectly says CPU audit; leave the frozen JSON unchanged and use this correction when reporting. E9 observed median/p95 forward interval is 30.258/68.466 ms; E10 is 27.669/59.726 ms. These intervals include host-to-device transfer, finite-output checks, sigmoid and a synchronized CPU probability copy, not pure GPU-kernel forward time. Native pipeline medians are 75.706 ms and 65.552 ms, but the timer stops before inspect_case, mask/panel writing and progress work. The whole audit intervals of 56.275 s and 66.852 s include these artifact operations.

Per-epoch seconds also include full VAL validation and checkpoint serialization; state elapsed includes guard hashes. There was no isolated runtime benchmark, so the observed intervals do not support a claim that hard-example weighting speeds inference. No numerical timing values or frozen sources were modified.

Patient/study independence, expert subtle/nondisplaced/multiple-fracture adjudication, paired-study fusion, radiologist agreement and external validation remain unavailable. This development VAL has been evaluated repeatedly; it is not a new independent clinical test. The original checkpoint, dataset, immutable baseline and reserved test remain preserved.
