# Phase 6 development evaluation — 6 October 2026

Executed a complete **validation-only** evaluation of a copied completed E2 epoch-1 checkpoint, SHA `87ba501958afc8c80c31040b0b961acabaed548fc128155b28a1a4c9050e1f0f`. E2 continues training; the diagnostic uses v1 with seven contradictory training images. Validation is unchanged between v1 and v2. This is not the final selected model, a matched finalist comparison, or an independent test result.

| Measured outcome | Result |
|---|---:|
| Validation positives / normals | 110 / 502 |
| Positive Dice / IoU | 0 / 0 |
| Case TP / FN / FP / TN | 0 / 110 / 0 / 502 |
| Sensitivity / specificity | 0% / 100% |
| Pixel and case precision | Undefined (no predictions) |
| Annotated regions matched, IoU 0.10 / 0.50 | 0 / 137 at both |
| Warm forward median / p95 | 763.2 / 924.5 ms |

19 thresholds × all/largest/min16 policies were evaluated. Here min16 is the legacy 256-grid component filter, not the new pipeline's native-area filter. The best admissible setting was 0.10/all with zero Dice; it is **not adopted**. The false-positive and sensitivity margins compared against 0.50/all are validation rules, not evidence of utility. The normal specificity is achieved by predicting background everywhere; it does not make this a useful model. No successful positive examples exist for this checkpoint, so none are presented.

`per_case.csv` records exact native integer TP/FP/FN counts. `subgroups.csv` reports anatomy/view/hardware/multiscan subsets. `table_reproduction.json` independently recomputes saved metrics. `confidence_intervals.json` uses 1,000 exact-group resamples with seed 42. All-zero endpoints give degenerate intervals; they do not establish zero population error. Patient independence remains unknown. Region matching maximizes cardinality then IoU with one-to-one assignment. Dice excludes empty ground truth; undefined precision remains null.

Timing is CPU-only and concurrent with E2. It is not an isolated performance benchmark. The elapsed evaluation time includes the actual session/runtime conditions; use measured forward timings for per-image inference. No AUROC, clinical accuracy, clinical severity, or approved clinical workflow is claimed. Geometry tiers remain heuristic.

Final Phase 6 gates remain: finish training and separately run corrected v2 controlled comparisons; choose/calibrate on validation; freeze the selected checkpoint/preprocessing/postprocessing/code; run the reserved test once; report matched baselines and final region/subgroup CIs; obtain human/teammate review. The final test was not accessed for model evaluation or tuning. GPU remains blocked by Windows Code 43.
