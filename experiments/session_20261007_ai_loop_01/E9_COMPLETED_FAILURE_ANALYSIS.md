# E9 completed reference failure analysis

8 October 2026. E9 completed its registered 12 additional epochs (global epochs 19-30), full CUDA native audit of 463 validation images and unaugmented TRAIN-grid fit. Every epoch saw all 2,808 distinct source entries once. All 209 normal alerts and 56 tagged positive segmentation failures were actually inspected and individually recorded. The original model, dataset and frozen validation cohort remain unchanged. E10's hard-weighting effect is pending its full matched results; no subsequent intervention is selected here.

| Native frozen VAL463 | Original model, same IDs | E7 selected reference | E9 selected reference |
|---|---:|---:|---:|
| TP / FN |83 /0|61 /22|67 /16|
| TN / FP |43 /337|215 /165|171 /209|
| Positive Dice |0.503797|0.270492|0.359342|
| Positive IoU |0.377569|0.198868|0.265569|
| Useful GT-overlap positive images |77 /83|46 /83|56 /83|
| False-positive pixels, all images |2589612|235568|787579|
| Mask-instance IoU0.5 matches |35 /99|23 /99|24 /99|
| Predicted connected regions |855|334|430|

E9's selected additional epoch 9 (global epoch 27) has accuracy 51.40%, sensitivity 80.72%, specificity 45.00%, precision 24.28%, F1 0.373259, AUROC 0.785098 and AUPRC 0.592641. It fails TP79/TN342, the original matched Dice improvement floor 0.523797, original IoU and original instance recall. Better mask-instance precision (24/430) does not compensate for lower recall (24/99 versus original 35/99). No clinical improvement or promotion is accepted. Original historical training exposure and patient independence remain unknown; this comparison cannot establish external clinical generalization.

The original comparison preserves its existing threshold and inverse-mask policy; E7/E9 preserve the registered research policy. E7's native audit used CPU and E9's used CUDA, so small floating-point boundary differences remain possible. E9 is an unchanged continuation reference: its gains over E7 cannot be attributed to hard-example weighting.

## What failed

Six fewer empty fracture misses than E7 coexist with44 extra normal alerts and552011 extra false-positive pixels. Per-case transitions include41 recovered E7 normal alerts but85 new alerts;8 prior empty fracture masks became alerts and2 new empty misses appeared. Among67 positive alerts,11 have zero GT overlap;16 other fractures have empty masks. Case sensitivity therefore overstates useful localization.

Unaugmented TRAIN-grid Dice improves0.273254 to0.353313 and positive zero-overlap counts improve219 to143 of493, while normal false alarms increase1032 to1233 of2315. Continued learning is observed; a pure validation-domain-shift explanation or demonstrated learning plateau is unsupported. TRAIN-grid figures and native VAL figures have different geometry and are not interchangeable.

Actual normal-panel observations repeatedly place masks at distal radius/wrist, distal tibia/ankle, distal femur/knee, elbow and shafts; other patches occur on projected chest or pelvic structures. IMG0002185 visibly marks an internal white divider, IMG0002702 a bright truncated crop and IMG0002271 a lower image edge. Tiny masks remain unresolved where recorded, rather than assigned invented anatomical causes. Visible hardware/rings do not prove causation.

Actual positive review documents empty masks, elbow targets displaced toward superior distal humerus, excessive wrist/shaft regions, targets missed across composite views and incomplete elongated annotation coverage. For example,1391/2465/2501/2502 show displaced elbow masks;2349/2524/3843/4044/4374 have broad or additional wrist/shaft patches;1073/2181/2586 have composite-view failures;2535/3342 under-cover long femoral annotations. Clinical subtle/nondisplaced subtypes and acquisition-quality causes remain unadjudicated.

Strata expose the alert/localization gap: leg8/18 alerts but7/18 with any GT overlap and pixel recall0.01962; hardware3/7 alerts but1/7 with overlap and pixel recall0.001785; oblique3/5 alerts but1/5 with overlap. Small-mask proxy11/12 alerts yields8/12 with overlap and Dice0.273206. These flags overlap, samples are small, frontal is not verified AP and multiple annotations do not establish clinical fracture subtype or shared study.

## Confidence and next decision

The actually viewed ROC/PR/confusion/reliability plots confirm unreliable maximum-pixel confidence. Brier0.407209 and ECE0.434087 are proxy-score diagnostics. In the highest bin,197 cases average0.9752 while the observed fracture fraction is0.3198. No clinical probability or calibration success is claimed.

The largest logged E9 score AUROC is0.798637, below the necessary ordering bound(79*342)/(83*380)=0.856627 for a single monotone cutoff to satisfy both count targets. This is a mathematical diagnostic on saved scores, not another threshold experiment or evidence that arbitrary score combinations cannot work.

Finish E10's unchanged matched12-epoch budget, full native audit, raw TRAIN fit and actual failure review. Evaluate its class-normalized bounded hardness factor against E9 and the original same-ID masks, including FP burden and useful fracture coverage. Only then identify one next factor from the observed remaining failure; the conditional memo and research notes preserve separable loss, resolution and initialization hypotheses. No CAL149 or reserved TEST597 inference, filtering, promotion or website work is performed here.

## Evidence

- Native audit:`experiments/AI_AUDIT_E9_v3_hard_reference/completion.json`, metrics SHA03d3ad34519abb72c6a864fcdc40f905bc05d1ef5c0c216034f43bad6395751c; selected checkpoint SHA770c791a49073ad36d77095fe9f900ac51c02024cf99b385780103d9e748144f.
- Actual normal209/209 review:`E9_all_normal_alert_sheets/completion.json`, case-review SHA6b4bb2d5d14536cf8678f1d43fe2f5cea245b88bf8fe59bff534d776b5ac8b24.
- Actual positive56/56 review:`E9_all_positive_sheets/completion.json`, case-review SHAa0ef28e9e7c1c04959e57a83eec1b81934e0337ac98db617c7548099eab73b53.
- Numeric transitions/strata and actually viewed curves:`E9_REFERENCE_FAILURE_INTERIM_DATA.json` and`E9_REFERENCE_FAILURE_INTERIM.md`. Their earlier normal-review-in-progress snapshot is superseded by the completed normal review above.
- Tiny-mask/divider full-panel follow-up:`E9_NORMAL_FULL_PANEL_FOLLOWUP.md`.
- Training-only diagnostics:`experiments/AI_LEARNING_FIT_E9_v3_hard_reference/`; matched live protocol:`HARD_EXPERIMENT_PROTOCOL.json`.
