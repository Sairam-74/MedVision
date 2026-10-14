# Actual TRAIN hard-example persistence

Compared the preserved original/E2 TRAIN-only native hard catalogs with the completed E5 selected-checkpoint TRAIN grid diagnostic. No new image inference, labels, data membership, weighting or optimizer updates occurred. All2808 frozen TRAIN identities were checked; VAL/CAL/reserved TEST identities are excluded.

| TRAIN group | Cases | E5 case errors | Positive masks with zero overlap | Positive mean grid Dice |
|---|---:|---:|---:|---:|
| Historical hard positive |127|61 missed alerts|112|0.014873|
| Other positive |366|107 missed alerts|163|0.243237|
| Historical hard negative |1641|999 false alerts|—|—|
| Other normal |674|178 false alerts|—|—|

Of127 hard positives,124 still have E5 grid Dice below0.20. Historical hard normals have60.9% current grid false-alert frequency, versus26.4% for other normals. Thus the preserved catalogs concentrate persistent training errors. They are not exclusively difficult:642 historically hard normals are currently rejected correctly. Do not assume every old hard example remains an error or every remaining image is easy.

The historical catalogs use native masks at each source model's recorded threshold; E5 persistence uses the common256 grid at0.5 with nearest-projected targets. They are different geometries/operating points, so these are persistence diagnostics rather than identical native error definitions. Hard positive means model/annotation disagreement, not a verified subtle or nondisplaced clinical fracture.

This supports a future bounded within-class hardness emphasis while retaining natural one-pass coverage, class mass and every training case. Refresh against the selected completed model before finalizing weights, and evaluate a matched control. No hard weighting is applied to E7/E8. Independent native-mask and conservative-alert gates remain required.
