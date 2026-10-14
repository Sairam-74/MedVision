# E9 fit on frozen TRAIN hard cases

Completed saved-result audit only. No image/model reads, inference, E10 result reads, calibration/test access or experiment changes.

All 2,808 unique sources and explicit labels match the frozen TRAIN manifest; recorded source versions and grid reference areas were verified. Hard catalog: 109 positive and 713 normal sources.

| Positive stratum | Model | Images / groups | Mean Dice / IoU | Mask alerts | Empty masks | Nonempty wrong-region masks | Any GT overlap | Dice <0.2 |
|---|---|---|---|---|---|---|---|---|
| hard positive | E7 | 109 / 109 | 0.005155 / 0.002795 | 52 | 57 | 47 | 5 | 109 |
| hard positive | E8 | 109 / 109 | 0.004106 / 0.002219 | 78 | 31 | 72 | 6 | 109 |
| hard positive | E9 | 109 / 109 | 0.024854 / 0.013915 | 78 | 31 | 57 | 21 | 105 |
| ordinary positive | E7 | 384 / 364 | 0.349355 / 0.251387 | 313 | 71 | 44 | 269 | 146 |
| ordinary positive | E8 | 384 / 364 | 0.323295 / 0.233978 | 328 | 56 | 65 | 263 | 169 |
| ordinary positive | E9 | 384 / 364 | 0.446548 / 0.330149 | 354 | 30 | 25 | 329 | 92 |

| Normal stratum | Model | Images / groups | FP / TN | FP rate | False-positive grid pixels |
|---|---|---|---|---|---|
| hard negative | E7 | 713 / 668 | 713 / 0 | 100.00% | 102831 |
| hard negative | E8 | 713 / 668 | 713 / 0 | 100.00% | 124586 |
| hard negative | E9 | 713 / 668 | 573 / 140 | 80.36% | 112523 |
| ordinary negative | E7 | 1602 / 1527 | 319 / 1283 | 19.91% | 24338 |
| ordinary negative | E8 | 1602 / 1527 | 705 / 897 | 44.01% | 75349 |
| ordinary negative | E9 | 1602 / 1527 | 660 / 942 | 41.20% | 76121 |

Ordinary continuation alone brings 4 / 109 frozen hard positives to Dice >=0.2 and correctly rejects 140 / 713 frozen hard normals. It leaves 88 hard positives without GT overlap and 573 hard normals with false mask alerts. A mask alert is not proof of fracture localization.

Exact same-ID transition lists, pixel overlap summaries, decoded-hash counts and source checksums are in analysis.json. The hard sets stay frozen for the later E9/E10 weighting comparison.

Limitations:

- Hard strata were selected using E7/E8 error outputs, so their low scores/high FP counts in those models are expected by construction
- E9 uses ordinary unweighted continuation from selected E7; changes cannot be attributed to hard weighting or compared as a controlled E8-versus-E9 ablation
- These are TRAIN fit results, not native VAL acceptance, clinical difficulty, or independent generalization
- Source groups are conservative related-image candidates, not proven patients or studies; inherited exact-source repetition remains
- Presence head and review union are deliberately excluded; empty/zero-overlap distinctions refer to independent binary masks
- Old fit-helper prose is verified against its preserved before-source; the documented head-score interpretation correction did not change these mask outputs
- Do not refresh the frozen running catalogs, infer an E10 outcome, or select a subsequent factor from this reference-only audit
