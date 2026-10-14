# Completed E11/E12 TRAIN positive Dice comparison

Saved CPU analysis of the two completed selected models. Four completed checkpoint files were streamed for SHA256 byte identity; no tensors were loaded. No new images, target arrays, inference, GPU, calibration/test data or production changes.

The unchanged manifest supplies 2,808 unique TRAIN sources: 493 positive and 2,315 normal. The frozen hard sets contain 109 positive and 713 normal sources. All memberships, labels, groups, recorded source versions and shared grid metadata passed.

| Model | Positive Dice coefficient (hard factor 2 fixed) | Selected additional / global epoch |
|---|---|---|
| E11 | 1 | 9 / 39 |
| E12 | 2 | 3 / 33 |

| Positive stratum | Model | Sources / groups / exact hashes | Dice / IoU | Alerts | Empty | Wrong region | Any GT overlap | Dice <0.2 |
|---|---|---|---|---|---|---|---|---|
| hard positive | E11 | 109 / 109 / 109 | 0.074139 / 0.050047 | 64 | 45 | 40 | 24 | 92 |
| hard positive | E12 | 109 / 109 / 109 | 0.053695 / 0.036111 | 57 | 52 | 35 | 22 | 97 |
| ordinary positive | E11 | 384 / 364 / 379 | 0.459571 / 0.346696 | 328 | 56 | 18 | 310 | 100 |
| ordinary positive | E12 | 384 / 364 / 379 | 0.462077 / 0.348448 | 341 | 43 | 25 | 316 | 99 |

| Normal stratum | Model | Sources / groups / exact hashes | FP / TN | FP rate | FP grid pixels |
|---|---|---|---|---|---|
| hard negative | E11 | 713 / 668 / 692 | 434 / 279 | 60.87% | 54037 |
| hard negative | E12 | 713 / 668 / 692 | 411 / 302 | 57.64% | 51481 |
| ordinary negative | E11 | 1602 / 1527 / 1577 | 371 / 1231 | 23.16% | 27132 |
| ordinary negative | E12 | 1602 / 1527 / 1577 | 485 / 1117 | 30.27% | 38296 |

| Positive stratum | Model | TP / FP / FN grid pixels | Pixel precision / recall |
|---|---|---|---|
| hard positive | E11 | 1668 / 6034 / 22145 | 0.2166 / 0.0700 |
| hard positive | E12 | 1248 / 8596 / 22565 | 0.1268 / 0.0524 |
| ordinary positive | E11 | 50164 / 33361 / 84614 | 0.6006 / 0.3722 |
| ordinary positive | E12 | 51798 / 36704 / 82980 | 0.5853 / 0.3843 |

Paired transitions are E11 reference to E12 candidate:

| Stratum | Alerts added / removed | FP pixels increased / decreased (cases) | GT overlap gained / lost | Dice gain / loss >0.02 | Dice0.2 crossed up / down |
|---|---|---|---|---|---|
| hard positive | 14 / 21 | 41 / 35 | 9 / 11 | 13 / 17 | 5 / 10 |
| ordinary positive | 30 / 17 | 183 / 154 | 31 / 25 | 150 / 132 | 23 / 22 |
| hard negative | 109 / 132 | 266 / 276 | not applicable | not applicable | not applicable |
| ordinary negative | 289 / 175 | 387 / 273 | not applicable | not applicable | not applicable |

Full exact source hashes, per-stratum differences, pixel counts and transition IDs are in analysis.json; per_case_changes.jsonl contains all 2,808 paired records. Normal-image Dice/IoU are intentionally not used as segmentation-quality evidence.

Limitations:

- This is an unaugmented TRAIN fit comparison, not native VAL acceptance, locked test performance or clinical generalization.
- Hard109/713 were selected from E7/E8 TRAIN errors and remain frozen; their selection prevents an independent difficult-case claim.
- Source groups are conservative related-image candidates, not proven patients/studies. Exact decoded-hash repetition is inherited source repetition, not new resampling.
- Masks are independent threshold0.5 grid outputs. A case alert can be a nonempty mask with no fracture overlap; any GT overlap alone does not prove adequate localization.
- Both use the same frozen cache metadata and identical saved per-case GT areas. The cache records array checksums, but this task does not reread/re-hash target arrays or verify new per-case target bitmaps.
- Completed E10 full/best and selected E11/E12 best checkpoint files are streamed for SHA256 byte identity only. No checkpoint tensors are loaded or inspected. Initial model metadata and the registered smoke Adam digests match; this analysis does not independently inspect the current trainer Adam tensors.
- Coefficient1 is the matched ordinary continuation control with hard factor2 retained. No result here compares raw loss scalars across coefficients as a quality metric.
- Selected additional/global epochs may differ under the common VAL selection rule; this compares selected models, not a guaranteed same-epoch estimate.
- One seed, no external validation and no expert subtle/nondisplaced labels. Dice0.2 and change0.02 are descriptive analysis cutoffs, not clinical adequacy criteria.
- No production promotion or subsequent intervention is selected from this report; native pair metrics and actual mask/failure reviews remain necessary.
