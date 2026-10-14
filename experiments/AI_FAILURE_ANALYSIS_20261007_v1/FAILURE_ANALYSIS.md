# Evidence-based failure analysis — 7 October 2026

Full immutable baseline: 612 validation cases. FP=453, FN=2, TP=108, TN=49. All native masks and case-specific panels are retained in the baseline directory. No test inference.

## False positives and confidence

453/502 provider-labelled normal cases are flagged. The image decision is ANY mask pixel >=.90. Maximum sigmoid output is exactly1 for 497/612 cases. In the .90–1 score bin, mean score is .99966 but only19.25% of561 images are fractured. This score measures a selected segmentation pixel, not calibrated case probability.

Technical visual examples IMG0000008, IMG0000010, IMG0000024, IMG0000027, IMG0000030, IMG0000038 and IMG0000050 show predicted normal-region marks near joint/cortical margins or other foreground edges. This is an observation of prediction placement against provider labels, not independent clinical confirmation that every label is correct. Every FP panel is available; exhaustive expert causal adjudication remains pending. Normal anatomical ambiguity and insufficient negative training are hypotheses, not proven original-checkpoint history.

## False negatives

The TWO image-level misses are IMG0002316 (max score .002709) and IMG0003021 (max score .002847). Both actual original/reference/empty-prediction panels were inspected individually. Both show visible overlying immobilization/cast-like material and small annotated regions. This association does not prove the cast caused the miss or establish subtle/nondisplaced clinical labels. Their exact scores, masks, metadata and occupancy are in analysis.json and the baseline per_case.json.

Raising or lowering ordinary thresholds .05–.95 cannot recover these scores. Lowering a gate to .002 would need separate validation and likely worsen false positives; it has NOT been adopted.

## Segmentation and localization

Algorithmic tag counts (nonexclusive): {"over_segmentation_precision_below_0.5": 49, "under_segmentation_recall_below_0.5": 21, "complete_mislocalization": 9, "complete_empty_miss": 2}. There are 9 positive images flagged at regions with ZERO overlap with ground truth. These count as image-level TP but are localization failures. IMG0001073 marks regions on a composite radiograph while missing both supplied wrist-region targets; IMG0001382 is another reviewed zero-overlap positive. This explains why98.18% case sensitivity is not98.18% fracture localization.

Native mask matching at IoU.50 recovers45/137 annotated instances (32.85%); there are1135 predicted components across all images, with1090 unmatched at that IoU. Positive Dice=.482326, global pixel precision=.104595. Under/over segmentation tags are defined by recall/precision below.50; empty and zero-overlap misses are separated. Tags describe measured overlap and are not clinical causes.

## Threshold experiment and decision

Recomputed57 combinations:19 thresholds .05–.95 x all/largest/min16 filtering, from EXACT float32 maps and native integer counts. .90/all confusion and pixel counts reproduce the baseline exactly. Best specificity over this grid=0.115538 (threshold 0.95, policy min16); sensitivity there=0.981818. ZERO combinations satisfy accuracy>.90, sensitivity>=.95 and specificity>=.90. REJECT threshold/component filtering as a sufficient reliability fix. Production threshold remains.90.

## Primary measured bottleneck and next controlled experiment

The measured bottleneck is background/fracture discrimination combined with the any-pixel case rule and saturated case-score proxy. A scalar threshold cannot separate the present outputs. The normal-inclusive E2 experiment also remains worse in Dice than the original at its latest saved epoch, so changing loss alone is not an accepted improvement.

Next complete interrupted E2 under its unchanged protocol, then compare one negative-sampling factor in fresh matched runs with the same architecture/loss/preprocessing/seed and a prospective validation/calibration partition. Do not use these VALIDATION hard-positive/negative review lists for training. Training hard sets require TRAIN-only inference and bounded within-class weighting with representative sampling; no naive duplication. Geometry/resolution, classifier heads and further loss changes remain subsequent experiments only after analyzing this comparison.

## Boundaries

No reliable patient IDs, clinical subtle/nondisplaced labels or paired study identities. View/anatomy results are in the baseline report with denominators; frontal is not proven AP and rare view groups are small. FracAtlas is the EXISTING dataset. No new external dataset, no clinical reader study, no calibrated clinical confidence and no production promotion. All architecture/data histories and expert-review gaps must accompany future improvement claims.
