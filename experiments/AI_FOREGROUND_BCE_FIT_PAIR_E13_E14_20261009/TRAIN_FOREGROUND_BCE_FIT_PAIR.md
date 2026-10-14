# Completed E13/E14 TRAIN foreground BCE comparison

Saved CPU metadata analysis of both completed selected models. Four checkpoint files were streamed for byte identity; no tensors were loaded. No new images, target arrays, inference, GPU or CAL/test access.

All 2,808 unique TRAIN sources, source labels/groups, frozen hard 109/713 memberships, recorded versions and shared grid metadata passed. Both arms independently restored the selected E11 epoch 9 / global 39 full model and Adam. The coefficient-1 first three epochs passed the registered saved replay checks.

| Model | Foreground BCE coefficient (hard 2 / positive Dice 1 fixed) | Selected additional / global epoch |
| --- | --- | --- |
| E13 | 1 | 6 / 45 |
| E14 | 5 | 11 / 50 |

| Positive stratum | Model | Sources / groups / exact hashes | Dice / IoU | Alerts | Empty | Wrong region | Any GT overlap | Dice < 0.2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hard positive | E13 | 109 / 109 / 109 | 0.139391 / 0.098569 | 74 | 35 | 30 | 44 | 81 |
| hard positive | E14 | 109 / 109 / 109 | 0.134691 / 0.095127 | 70 | 39 | 31 | 39 | 82 |
| ordinary positive | E13 | 384 / 364 / 379 | 0.495670 / 0.370854 | 360 | 24 | 19 | 341 | 69 |
| ordinary positive | E14 | 384 / 364 / 379 | 0.530537 / 0.405471 | 358 | 26 | 11 | 347 | 63 |

| Normal stratum | Model | Sources / groups / exact hashes | FP / TN | FP rate | FP grid pixels |
| --- | --- | --- | --- | --- | --- |
| hard negative | E13 | 713 / 668 / 692 | 468 / 245 | 65.64% | 69550 |
| hard negative | E14 | 713 / 668 / 692 | 423 / 290 | 59.33% | 55160 |
| ordinary negative | E13 | 1602 / 1527 / 1577 | 629 / 973 | 39.26% | 76096 |
| ordinary negative | E14 | 1602 / 1527 / 1577 | 445 / 1157 | 27.78% | 35442 |

| Positive stratum | Model | TP / FP / FN grid pixels | Pixel precision / recall |
| --- | --- | --- | --- |
| hard positive | E13 | 3582 / 12780 / 20231 | 0.2189 / 0.1504 |
| hard positive | E14 | 2860 / 8677 / 20953 | 0.2479 / 0.1201 |
| ordinary positive | E13 | 59704 / 54103 / 75074 | 0.5246 / 0.4430 |
| ordinary positive | E14 | 63214 / 40758 / 71564 | 0.6080 / 0.4690 |

Paired transitions are E13 reference to E14 candidate:

| Stratum | Alerts added / removed | FP pixels increased / decreased (cases) | GT overlap gained / lost | Dice gain / loss > 0.02 | Dice 0.2 crossed up / down |
| --- | --- | --- | --- | --- | --- |
| hard positive | 11 / 15 | 33 / 50 | 8 / 13 | 20 / 26 | 10 / 11 |
| ordinary positive | 11 / 13 | 140 / 220 | 24 / 18 | 204 / 120 | 28 / 22 |
| hard negative | 85 / 130 | 230 / 323 | not applicable | not applicable | not applicable |
| ordinary negative | 161 / 345 | 262 / 526 | not applicable | not applicable | not applicable |

Exact artifact/source hashes, differences and transition IDs are in analysis.json. All 2,808 same-ID paired records are in per_case_changes.jsonl. Normal-image Dice/IoU are not used as segmentation-quality evidence.

Limitations:

- Unaugmented TRAIN grid fit is not native validation acceptance, locked-test performance or clinical generalization.
- Persistent hard 109/713 were selected from E7/E8 TRAIN errors. Their reused selection is not an independent difficult-case test.
- Related-image group IDs are conservative candidates, not verified patients/studies. Existing decoded-exact repetition is not new resampling.
- Independent threshold 0.5 grid masks can trigger a case alert with zero target overlap. Any target overlap does not establish adequate localization.
- Frozen cache metadata and same-ID saved target areas match. Stored array checksums are recorded; no target arrays or per-case target bitmaps were reread or decoded.
- Four unique completed checkpoint files (E11 selected full/best and E13/E14 selected best) are streamed for byte hashes only. No tensors or current Adam state are independently loaded.
- Actual initializer metadata matches the registered three-arm smoke model/Adam digests. First three E13 replay JSONs must pass exact prior E11 model/Adam/validation parity.
- Coefficient 1 is matched continuation with hard factor 2 and positive Dice coefficient 1 retained. Weighted raw loss scalars are not compared as quality metrics.
- Selected additional/global epochs may differ under the unchanged selection rule. This is a selected-model comparison, not necessarily a same-epoch effect.
- One seed; clinical subtle/nondisplaced labels, verified patient/view identifiers, radiologist adjudication and external validation are unavailable.
- Dice 0.2 and a Dice change of 0.02 are descriptive analysis cutoffs, not clinical adequacy thresholds.
- No promotion or next intervention is selected here. Completed native audits and actual failure reviews remain required.
