# Completed E10 hard-weighting failure analysis

E9 and E10 completed their registered twelve additional epochs, native CUDA validation audits, raw TRAIN fit and paired analysis. All 199 E10 normal alerts and all 55 tagged positive segmentation failures were actually viewed, with individual observations and original panel hashes retained. Clinical causes and fracture subtypes remain unadjudicated.

| Native VAL463 measurement | Original unchanged model | E9 reference | E10 hard factor2 |
|---|---:|---:|---:|
| TP / FN | 83 / 0 | 67 / 16 | 67 / 16 |
| TN / FP | 43 / 337 | 171 / 209 | 181 / 199 |
| Accuracy | 27.21% | 51.40% | 53.56% |
| Sensitivity | 100.00% | 80.72% | 80.72% |
| Specificity | 11.32% | 45.00% | 47.63% |
| Precision | 19.76% | 24.28% | 25.19% |
| F1 | 0.330020 | 0.373259 | 0.383954 |
| AUROC | 0.601807 | 0.785098 | 0.785289 |
| Average precision | 0.215662 | 0.592641 | 0.574039 |
| Positive native Dice | 0.503797 | 0.359342 | 0.379528 |
| Positive native IoU | 0.377569 | 0.265569 | 0.283667 |
| Global pixel recall | 0.730235 | 0.344021 | 0.428037 |
| TP / FP / FN native pixels | 286345 / 2589612 / 105782 | 134900 / 787579 / 257227 | 167845 / 591338 / 224282 |
| Mask-IoU0.5 matches / GT regions | 35 / 99 | 24 / 99 | 28 / 99 |
| Predicted connected regions | 855 | 430 | 402 |
| Positive images with any GT overlap | 77 / 83 | 56 / 83 | 56 / 83 |

The original column uses the same 463 IDs. The immutable original 612-case baseline is a separate population and is not overwritten or used as a mismatched denominator. Original inference remains threshold0.90/all; research runs use their registered threshold0.50/all and native bilinear inversion.

E10 selected additional epoch12/global30; E9 selected additional epoch9/global27 under the identical frozen selection rule. Both restored the same initial full E7 global18 model/Adam and saw all 2,808 unique TRAIN sources once per epoch. The only registered training factor was bounded, within-class mean-normalized hard weights1 versus2. The selected-model comparison includes different selected epochs and one seed; it does not establish a universal hard-weighting effect.

E9 to E10 recovers 56 normal alerts but introduces 46 others, a net reduction of ten. It recovers five empty fracture masks but introduces five new empty masks. Positive Dice improves by more than0.02 in 27 cases and worsens by more than0.02 in 21. Native false-positive pixels fall by196241, but useful GT coverage remains far below the original model. E10 has16 empty misses and11 nonempty predictions with zero GT overlap. The tagged counts also include16 under-segmentation and21 over-segmentation cases; tags overlap and describe annotation metrics rather than clinical diagnoses.

Observed examples include empty metatarsal masks in IMG2533/2732/3797/3798, empty tibial hardware targets in IMG2342/2372/2374, empty composite hand targets in IMG1073/2181, elbow predictions displaced above or below the annotation in IMG1391/2465/2470/2501, and poor coverage of long femoral targets in IMG2535/3342. Cast wrist/shaft predictions often add regions outside small annotations, including IMG2349/2524/3843/4044/4374. These are actual panel observations; neither casting nor hardware is proven to cause a failure.

Normal alerts recur at ankle, wrist, knee, shoulder and hip margins and as isolated shaft islands. IMG2185 visibly marks a bright internal divider; IMG2187 marks a cropped humeral shaft edge. A single artifact explanation does not account for the full set. Tiny masks that remain unresolved at display scale are explicitly recorded without assigning a precise causal structure. No annotation was changed from these observations.

Saved raw TRAIN-grid comparison reinforces the fitting bottleneck:

| TRAIN subset | E9 | E10 |
|---|---:|---:|
| Hard positives109: mean Dice | 0.024854 | 0.058133 |
| Hard positives: any GT overlap / empty / wrong region | 21 / 31 / 57 | 23 / 41 / 45 |
| Ordinary positives384: mean Dice | 0.446548 | 0.465110 |
| Ordinary positives: any GT overlap / empty / wrong region | 329 / 30 / 25 | 319 / 36 / 29 |
| Hard negatives713: FP / TN | 573 / 140 | 547 / 166 |
| Ordinary negatives1602: FP / TN | 660 / 942 | 596 / 1006 |

Hard sets were selected from E7/E8 TRAIN errors; these are not independently labelled subtle or nondisplaced fracture cohorts. Exact IDs, labels, related groups, catalog memberships, saved per-ID target areas and source/configuration identities passed the comparison. These grid statistics are not native validation metrics. Higher mean Dice coexists with more empty TRAIN positive masks, so an aggregate Dice increase does not prove that difficult cases are reliable.

E10's maximum-pixel proxy remains severely uncalibrated: Brier0.362700 and ECE0.398578. In the highest bin,152 images have mean score0.964837 but fracture prevalence0.381579. These values are score diagnostics, not calibrated case probabilities. No new calibration fitting was performed. Audit device and reproduction fields show CUDA; the saved timing description still contains stale CPU wording. Reported medians are27.67ms forward/65.55ms full pipeline, not an isolated idle comparative benchmark.

Decision: retain E10 as a development checkpoint; reject it for production promotion and final reliability claims. TP67/TN181 fail TP79/TN342, positive Dice/IoU remain below the unchanged original, and instance recall28/99 remains below35/99. The reserved test and calibration partitions remain closed to this loop. No website or production bundle was changed.

Next controlled hypothesis: increase only positive-case Dice coefficient1 to2, preserving all-image BCE, normal Dice, hard factor2 weights, unique sampling, architecture, input resolution, preprocessing and optimizer protocol. Compare two equally continued arms from E10 global30 full model/Adam. This addresses persistent poor foreground fitting; it is a testable hypothesis, not an improvement claim. Higher resolution, transfer initialization and patch/global-local changes remain separate future experiments. Full curves/subgroup and independent factor reviews are recorded separately.

Evidence: AI_E9_E10_HARD_PAIR/comparison.json; AI_AUDIT_E10_v3_hard_weight2/metrics.json and per_case.json; AI_HARD_FIT_PAIR_E9_E10_20261008/analysis.json; E10_all_normal_alert_sheets/completion.json and per_case_visual_review.json; E10_all_positive_sheets/completion.json and per_case_visual_review.json. All56 frozen hard-pair guards and the E10 selected checkpoint/native audit hashes were verified unchanged after completion.
