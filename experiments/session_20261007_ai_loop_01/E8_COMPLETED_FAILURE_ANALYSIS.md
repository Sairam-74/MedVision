# E7/E8 completed failure analysis — 8 October 2026

E8 is rejected as an overall reliability improvement. Both arms completed the same 12-epoch continuation. The paired numerical analysis is `experiments/AI_E7_E8_PRESENCE_PAIR_r3/comparison.json`; all native masks and per-case scores remain in the corresponding audit folders. Neither arm meets the frozen validation or segmentation/localization gates.

| Native frozen VAL metric | E7 reference | E8 presence supervision |
|---|---:|---:|
| Detected fractures /83 | 61 | 74 |
| Missed case alerts | 22 | 9 |
| Correctly rejected normals /380 | 215 | 121 |
| False case alerts | 165 | 259 |
| Accuracy | 59.61% | 42.12% |
| Sensitivity | 73.49% | 89.16% |
| Specificity | 56.58% | 31.84% |
| Positive Dice | 0.270492 | 0.280550 |
| Positive IoU | 0.198868 | 0.208022 |
| False-positive native pixels | 235568 | 696136 |
| Pixel recall | 0.132880 | 0.166265 |
| Mask instances matched at IoU0.5 /99 | 23 | 19 |

Primary E8 classification is the conservative union of classifier-positive and independently mask-positive alerts. E8 masks alone produce TP63/FN20/TN136/FP244. The classifier alone produces TP52/FN31/TN298/FP82. A positive classifier is therefore not proof of useful localization, and using negative classifier decisions to erase masks would remove 22 fracture-mask-positive cases. Nine of those cases outside the tagged mask failures were actually reviewed separately and have meaningful reference/prediction overlap. All 225 head/mask disagreements are covered by linked actual reviews.

Actual review is complete for all 259 normal alerts, all 61 unique tagged positive segmentation failures (56 new cases plus five previously viewed native panels), and all 225 disagreements (nine newly viewed plus 216 covered by the other completed reviews). Evidence: `E8_all_normal_alert_sheets/completion.json`, `E8_remaining_positive_sheets/completion.json`, and `E8_remaining_head_mask_disagreement_sheets/completion.json`, with individual observations and panel hashes. Sheet creation alone was not counted as inspection. Additional full-panel checks and unresolved tiny predictions are disclosed in `E8_NORMAL_FULL_PANEL_FOLLOWUP.md`.

Repeated observations include false wrist/ankle/distal-femoral patches, occasional shaft and rib/iliac patches, and a false patch on an internal white divider in a composite image. Fracture-mask errors include 20 empty masks and 18 nonempty masks with zero reference overlap, alongside nonexclusive under- and over-segmentation tags. Elbow/proximal-forearm annotations can be missed while nearby distal-humeral or wrist regions are predicted; classifier-positive empty shoulder/cast/hardware examples also occur. Visible hardware, casts and overlapping anatomy are associations, not adjudicated causes. Clinical subtle/nondisplaced subtype labels, patient IDs and expert annotation corrections are unavailable. No label was changed.

Poor fitting also occurs on unaugmented TRAIN data. E7 TRAIN Dice is0.273254 with219/493 zero-overlap positives; E8 TRAIN Dice is0.252724 with224/493 zero-overlap positives. These raw 256-grid diagnostics establish that a validation-only domain shift or overfitting-only explanation is insufficient; they are not native validation acceptance metrics. The persistent hard catalogs contain109 historical TRAIN fractures and713 historical TRAIN normals that remain wrong in both selected checkpoints.

The E8 classifier reliability curve was actually inspected. Its raw weighted-BCE sigmoid is overconfident across the displayed bins; native head Brier0.165879/ECE0.170178 are diagnostics, with no calibration fit. Its best head AUROC across all12 epochs is0.812429 (epoch4), below the necessary0.856627 single-score ranking bound for the requested TP79/TN342 operating point. Threshold sweeping alone cannot meet that pair of counts for these saved single scores. The 16-case frozen-BatchNorm TRAIN gradient probe also found large presence/segmentation encoder gradient ratios; it does not establish population gradients or a causal training mechanism.

The next registered one-factor comparison is E9/E10 bounded hard-example loss weighting, initialized from E7's selected global18 full model/Adam snapshot. E8's supervised branch is not combined with the intervention. Both arms receive12 further matched epochs/global19–30 and the same natural one-pass2808-image shuffle. Factor1 versus2 is normalized within each class to preserve its total weight; no image is duplicated or resampled. The exact loss reference, actual CUDA gradients, independent optimizer initializations and full restores passed before launch. Future outcomes must be measured before retaining this factor.

Original checkpoint/archive/baseline/history hashes passed preservation verification on8October. No frontend changes, calibration-set predictions, reserved-test predictions or promotion occurred. External validation, clinical reader agreement and a final improved-model claim remain unproved.
