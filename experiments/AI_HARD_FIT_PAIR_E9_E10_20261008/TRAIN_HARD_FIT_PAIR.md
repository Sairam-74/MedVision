# Completed E9/E10 TRAIN hard-fit comparison

Saved CPU analysis of the two completed selected models. No new images, arrays, model tensors, inference, GPU, calibration/test data or production changes.

The unchanged manifest supplies 2,808 unique TRAIN sources: 493 positive and 2,315 normal. The frozen hard sets contain 109 positive and 713 normal sources. All memberships, labels, groups, recorded source versions and shared grid metadata passed.

| Model | Hard factor | Selected additional / global epoch |
|---|---|---|
| E9 | 1 | 9 / 27 |
| E10 | 2 | 12 / 30 |

| Positive stratum | Model | Sources / groups / exact hashes | Dice / IoU | Alerts | Empty | Wrong region | Any GT overlap | Dice <0.2 |
|---|---|---|---|---|---|---|---|---|
| hard positive | E9 | 109 / 109 / 109 | 0.024854 / 0.013915 | 78 | 31 | 57 | 21 | 105 |
| hard positive | E10 | 109 / 109 / 109 | 0.058133 / 0.039171 | 68 | 41 | 45 | 23 | 98 |
| ordinary positive | E9 | 384 / 364 / 379 | 0.446548 / 0.330149 | 354 | 30 | 25 | 329 | 92 |
| ordinary positive | E10 | 384 / 364 / 379 | 0.465110 / 0.350258 | 348 | 36 | 29 | 319 | 98 |

| Normal stratum | Model | Sources / groups / exact hashes | FP / TN | FP rate | FP grid pixels |
|---|---|---|---|---|---|
| hard negative | E9 | 713 / 668 / 692 | 573 / 140 | 80.36% | 112523 |
| hard negative | E10 | 713 / 668 / 692 | 547 / 166 | 76.72% | 83740 |
| ordinary negative | E9 | 1602 / 1527 / 1577 | 660 / 942 | 41.20% | 76121 |
| ordinary negative | E10 | 1602 / 1527 / 1577 | 596 / 1006 | 37.20% | 57255 |

| Positive stratum | Model | TP / FP / FN grid pixels | Pixel precision / recall |
|---|---|---|---|
| hard positive | E9 | 859 / 19006 / 22954 | 0.0432 / 0.0361 |
| hard positive | E10 | 1350 / 12192 / 22463 | 0.0997 / 0.0567 |
| ordinary positive | E9 | 55885 / 66064 / 78893 | 0.4583 / 0.4146 |
| ordinary positive | E10 | 54301 / 48667 / 80477 | 0.5274 / 0.4029 |

Paired transitions are E9 reference to E10 candidate:

| Stratum | Alerts added / removed | FP pixels increased / decreased (cases) | GT overlap gained / lost | Dice gain / loss >0.02 | Dice0.2 crossed up / down |
|---|---|---|---|---|---|
| hard positive | 6 / 16 | 23 / 61 | 6 / 4 | 18 / 6 | 8 / 1 |
| ordinary positive | 12 / 18 | 116 / 237 | 12 / 22 | 161 / 100 | 13 / 19 |
| hard negative | 60 / 86 | 220 / 412 | not applicable | not applicable | not applicable |
| ordinary negative | 210 / 274 | 360 / 509 | not applicable | not applicable | not applicable |

Full exact source hashes, per-stratum differences, pixel counts and transition IDs are in analysis.json; per_case_changes.jsonl contains all 2,808 paired records. Normal-image Dice/IoU are intentionally not used as segmentation-quality evidence.

Limitations:

- This is an unaugmented TRAIN fit comparison, not native VAL acceptance, locked test performance or clinical generalization.
- Hard109/713 were selected from E7/E8 TRAIN errors and remain frozen; their selection prevents an independent difficult-case claim.
- Source groups are conservative related-image candidates, not proven patients/studies. Exact decoded-hash repetition is inherited source repetition, not new resampling.
- Masks are independent threshold0.5 grid outputs. A case alert can be a nonempty mask with no fracture overlap; any GT overlap alone does not prove adequate localization.
- Both use the same frozen cache metadata and identical saved per-case GT areas. The cache records array checksums, but this task does not reread/re-hash target arrays or verify new per-case target bitmaps.
- Initial parameter metadata and full optimizer snapshot identity match. No model/Adam tensors are reloaded in this CPU analysis; initializer restoration was separately exercised by the registered smoke.
- Selected additional/global epochs may differ under the common VAL selection rule; this compares selected models, not a guaranteed same-epoch estimate.
- One seed, no external validation and no expert subtle/nondisplaced labels. Dice0.2 and change0.02 are descriptive analysis cutoffs, not clinical adequacy criteria.
- No production promotion or subsequent intervention is selected from this report; native pair metrics and actual mask/failure reviews remain necessary.
