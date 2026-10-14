# E11 normal-alert visual failure analysis

Completed actual review: 8 October 2026. Resume verification and memo: 9 October 2026.

All 139 selected normal-label cases were actually reviewed on all 16 original-resolution contact sheets. The existing review completion, ordered observations and per-case records were verified on resume; completed views were not repeated. Coverage is 139 unique image IDs, no positive-label cases, and 139 independent-mask false positives against the dataset reference. The normal-alert subset contains 117,053 false-positive mask pixels. That number excludes positive cases and must not be presented as the full validation set's pixel error.

The source is the completed native validation audit `AI_AUDIT_E11_v3_positive_Dice_reference`, selected epoch 9 / global epoch 39. At the saved threshold and postprocessing, the complete 463-case validation set has TP 67, FN 16, TN 241 and FP 139. This memo analyzes the 139 normal alerts; it does not independently adjudicate fractures or compare the E12 intervention. The original dataset labels remain unchanged.

## Observed region patterns

Many visible red regions are compact rounded, short vertical or wedge-shaped patches near joint-adjacent bone margins. Clear distal forearm/wrist examples include `IMG0000432.jpg`, `IMG0002956.jpg`, `IMG0003322.jpg` and `IMG0004260.jpg`. Lower-leg/ankle examples include the broad horizontal band above the joint in `IMG0003314.jpg`, two connected lobes in `IMG0000642.jpg`, and separate ankle-margin and higher-shaft patches in `IMG0003582.jpg` and `IMG0003735.jpg`. These are observations of the predicted regions, not proof that a particular normal cortical structure caused the error.

The model also marks shafts away from a joint: a mid lower-leg region in `IMG0001646.jpg`, a small mid lower-leg patch in `IMG0002942.jpg`, proximal upper-leg patches below the hip in `IMG0002828.jpg` and `IMG0004178.jpg`, and the upper-arm shaft in `IMG0000963.jpg`. Some masks are fragmented or repeated across a source image, including combined elbow views in `IMG0000878.jpg`, three forearm/wrist patches in `IMG0001343.jpg`, and three distal lower-leg spots in `IMG0003969.jpg`.

Combined-view images do not always show matching red placement across their components. In `IMG0000295.jpg`, one component is marked around the knee and another around the proximal lower-leg shaft. `IMG0002072.jpg` has wrist marks in both components, whereas `IMG0001345.jpg` marks the frontal knee component while the side component is unmarked. `IMG0002200.jpg` marks the side ankle component while the brighter frontal foot component is largely unmarked. These are within-image observations; source images are not independently verified study-level AP/lateral pairs and cannot establish patient-level multi-view consistency.

Some marks occur at image edges or near a bright separator: the fingertip near the bottom in `IMG0001486.jpg`, distal leg/ankle beside a vertical separator in `IMG0002185.jpg`, and a partial upper-limb shaft near a crop boundary in `IMG0002702.jpg`. A few external bright bands or loops are spatially separate from the main mask, including `IMG0001750.jpg`, `IMG0001759.jpg`, `IMG0001833.jpg`, `IMG0001968.jpg` and `IMG0002098.jpg`. Hardware or artifacts therefore cannot be assigned as the cause merely because they are present.

## Unresolved small regions

Twenty-two observations explicitly request full-panel follow-up because exact extent or placement is unresolved at contact-sheet scale. Three have no definite red region resolvable on the sheet despite a saved alert: **`IMG0000970.jpg`, `IMG0001263.jpg`, `IMG0003917.jpg`**. This uncertainty is preserved in the completed per-case notes; completion counts actual views, not certainty about every boundary.

| Sheet | Image IDs requiring full-panel follow-up |
| --- | --- |
| 01 | IMG0000050.jpg; IMG0000260.jpg |
| 02 | IMG0000403.jpg; IMG0000619.jpg |
| 03 | IMG0000631.jpg; IMG0000705.jpg |
| 04 | IMG0000970.jpg; IMG0000985.jpg |
| 05 | IMG0001263.jpg |
| 06 | IMG0001355.jpg; IMG0001557.jpg |
| 07 | IMG0001764.jpg |
| 08 | IMG0001849.jpg; IMG0001879.jpg |
| 09 | IMG0002066.jpg; IMG0002187.jpg |
| 11 | IMG0003015.jpg |
| 13 | IMG0003465.jpg; IMG0003537.jpg |
| 14 | IMG0003605.jpg |
| 15 | IMG0003791.jpg; IMG0003917.jpg |

## Interpretation and limits

Observed false-positive regions span several anatomical areas, focal shaft marks, joint-adjacent patches, fragmented masks and a few boundary-adjacent locations. These observations support reviewing localization and suppression of normal-label regions rather than trusting a case alert alone. They do not establish the causal contribution of resolution, cortical overlap, positioning, preprocessing, annotation quality or loss balance. No clinical subtype, patient identity or expert correction is available here. A dataset normal label is a reference, not radiologist adjudication.

The displayed score is an uncalibrated mask confidence proxy derived from pixel predictions, not a validated probability of fracture. Presence supervision is disabled in this run. This review measured neither radiologist agreement nor generalization. It changed no labels, weights, threshold or production model, selected no next intervention, performed no new inference, and accessed no calibration or locked-test data.

## Evidence hashes

| Artifact | SHA-256 |
| --- | --- |
| Review completion | `4a86cbe65b97216bcedff7e50f428a88ccb4780962ca49db2c61e51f1896f3ac` |
| Per-case JSON | `54bfd5251c36dcf171f446ccc385537023c0092d2c9e50b35630b4113cd94816` |
| Per-case CSV | `a8f8aa5edc53b93a438b7705931271501e2b0db485cae883e9beb51f6750b793` |
| Actual sheet notes | `da945445f55708e330edad6cc6f744d1ee11c590457f849c230a1f75c184fe71` |
| Sheet index | `c1a501b6aebe17eadf91ea21863d8d4ab78cede88302b6931a2bd1705f64851a` |
| Review recorder | `e4d873893298f6ba94cf2bc2bc50189f4a02c3cd354f208ef2414b648aa2abc2` |
| Native audit per-case JSON | `846acc4ecc7fcc0e73b58c6fe4f46c9ae4cc84fecfce505603d9461927d81438` |
| Native audit config | `91d4cc19aa14357562d160b99983cc4a160c74dae49527b0fae58cd45ed5990c` |
| Native audit completion | `398fba55979290a4cf91671db51cc1b2379fb90ca00a93a9be8e7d5105f65d0a` |
| Selected checkpoint (audit provenance) | `c1703d13e5b4cdf35b600c48825ec93c3394570ab1df44d20e9a06b41abc2b84` |
| Frozen manifest (audit provenance) | `4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318` |

The ordered records and sheets are preserved in `E11_all_normal_alert_sheets/`. Checkpoint and manifest hashes above are recorded provenance; this memo did not load model tensors or decode dataset images.
