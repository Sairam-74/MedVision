# E14 normal failure analysis — actual saved-panel review

Date: 9 October 2026. Scope: the completed E14 foreground-BCE5 candidate, selected epoch 11 / global epoch 50. This is a technical visual review of normal-labelled validation images; it is not radiologist adjudication of diagnoses, labels, clinical anatomy, fracture subtypes or causal mechanisms.

## Completed coverage and evidence

All **16 contact sheets were actually viewed**, covering **all 143 E14 normal-image alerts**, with one ordered observation for every selected image. Generation alone was not counted as viewing. All **46 flagged tiny, unclear or composite cases were then actually viewed in their retained individual original / ground-truth / prediction panels** using local `view_image` at original detail. Approximate alert locations were resolved for 37 of those follow-ups; nine remain unresolved. Across the 143 reviewed images, 134 have an approximately visible mask location and nine do not.

The individual panels are retained audit renders, not a new inference or a full-resolution diagnostic workstation examination. Even the larger panel retains display scaling. Clinical cause and subtype remain **Unadjudicated / Unavailable** for every image, including those whose mask location is clear.

Review records:

- [Completed review and hashes](E14_all_normal_alert_sheets/completion.json): exact 143-case membership, 16 sheets and unchanged retained-panel hashes.
- [Final per-case observations](E14_all_normal_alert_sheets/per_case_visual_review_final.json): every original sheet note plus full-panel refinement where performed. **Full-panel refinements take precedence** over tentative sheet descriptions.
- [Full-panel follow-ups](E14_all_normal_alert_sheets/full_panel_followup_review.json): all 46 actual follow-ups, source paths/hashes, visibility decisions and remaining limits.
- [Saved-metadata comparison](E14_all_normal_alert_sheets/normal_review_metadata.json): exact 463 E13/E14 IDs and labels independently matched, normal false-positive counts, transitions and non-exclusive metadata strata.
- [Sheet index](E14_all_normal_alert_sheets/index.json) and [actual ordered sheet notes](E14_all_normal_alert_sheets/actual_sheet_notes.json).

This review performed no new inference, optimizer steps, model/tensor loading, threshold change, dataset/label change, CAL/test access, production promotion or website work. It wrote only this report and its new E14 review directory. It did not modify old reviews or frozen sources.

## What the completed measurements show

E14 remains unreliable as a normal-image discriminator despite its improvement over the selected E13 matched reference. It alerts on **143 / 380 normal images: FPR 37.63%, specificity 62.37%**. Its overall completed 463-case audit is TP 70, TN 237, FP 143, FN 13: accuracy **66.31%**, sensitivity **84.34%**, precision **32.86%** and F1 **47.30%**. These are development-validation measurements; the requested 90%+ reliability targets have not been met.

The selected checkpoints are E13 epoch 6 / global 45 and E14 epoch 11 / global 50 under the registered matched continuation/factor protocol. This report compares their saved selected outputs; it does not call differently selected epochs a same-epoch anatomical causal experiment.

| Normal-image measure | E13 selected reference | E14 selected candidate |
|---|---:|---:|
| Normal denominator | 380 | 380 |
| Normal images with alerts | 176 | 143 |
| FPR | 46.32% | 37.63% |
| False-positive native pixels on normal images | 705,381 | 176,344 |

The count falls by 33 alerts (**18.75%**) and the summed native normal false-positive pixels fall by approximately **75.00%**. This is not uniform recovery: **112 normal alerts persist, 64 previously alerted normal images recover, and 31 previously unalerted normal images acquire an alert**. The metadata evidence preserves the IDs for all 143 persistent/new E14 alerts. No E13 panels were newly visually reviewed as part of this task.

Among the 143 E14 normal alerts, native false-positive pixel counts range from 1 to 18,695 (median 258); predicted image fraction has median **0.1299%**, maximum **0.7824%**. Components range from 1 to 4 (median 1). Native pixel counts are affected by original image dimensions, so their normalized image fraction is also reported. Compact masks can still generate many case-level false alerts.

The uncalibrated maximum-pixel score ranges from **0.50269 to 0.99883**, median **0.81269**. **37 normal alerts have score ≥0.90**, while 17 have score ≤0.55. Eighteen alerts have ≤16 native predicted pixels under the saved current policy. Near-threshold specks are therefore one visible part of the problem; confidently scored anatomical patches remain too. This review neither applies a size filter nor claims what its effect on missed fractures would be.

## Visible patterns and actual examples

The recurring visible output is localized red foreground at bony ends and overlapping joint projections in normal-labelled images. The examples below are observed geometry, not a diagnosis that a specific cortical structure caused the failure. Every case has a separate final note in the linked 143-case record.

| Observed pattern | Actual reviewed examples | What can be concluded |
|---|---|---|
| Distal forearm/wrist patches, from small wedges to broad bands | IMG0000260, IMG0000432, IMG0001224, IMG0001320, IMG0003003, IMG0003322 | The model creates compact or broad masks in distal forearm projections even when the dataset labels the image normal. |
| Ankle/distal lower-leg bony-end masks | IMG0000050, IMG0000208, IMG0000630, IMG0002826, IMG0003582, IMG0003583 | Multiple images show rounded, triangular or transverse foreground immediately above/around the ankle. |
| Elbow bony-end/overlap masks | IMG0000589, IMG0000878, IMG0000990, IMG0002667, IMG0003529, IMG0004060 | The masks often cover joint-end projections, sometimes as two touching or separated lobes. |
| Hip/pelvis and shoulder alerts | IMG0001249, IMG0001764, IMG0001879, IMG0003353, IMG0003445, IMG0003987 | False foreground is not confined to one anatomical region. Bilateral hip masks and superior shoulder-overlap masks are visible examples. |
| Shaft or distal digit/forefoot alerts | IMG0000963, IMG0001633, IMG0001647, IMG0001778, IMG0001986, IMG0001486, IMG0003015 | The failure also includes small shaft sites and distal digit/forefoot projections rather than only major joint ends. |
| Several disconnected masks or inconsistent marks across projections within one image | IMG0000174, IMG0000285, IMG0001249, IMG0001879, IMG0002072, IMG0003151 | Fragmentation and unequal marking across composite views are visible. These are not established paired-patient/study comparisons. |

For example, IMG0000285 has three separate islands in the lateral ankle/foot projection but no conspicuous foreground in its neighbouring frontal projection. IMG0002072 marks distal forearm/wrist regions in both displayed projections. IMG0003151 marks two distal upper-arm regions in one projection while its adjacent lateral projection appears unmarked at retained resolution. Such examples show inconsistency of false alerts within retained composite images; they do not establish reliable multi-view clinical fusion.

The full-panel follow-ups corrected tentative geometry from the sheets. IMG0001371 shows another hand placed across the wrist within the same image, rather than an assumed separate X-ray view. IMG0002185 is better described as ankle/foot-like projections, with a forefoot-tip patch and another patch at the lower-leg/border interface; its exact clinical context remains unadjudicated. IMG0003445's broad lobes lie at the superior shoulder/acromial-distal clavicular overlap, rather than being assigned exclusively to the humeral head. IMG0003788 has a bent long limb with a red upper long-bone-end patch at its middle joint; this technical review cannot certify its clinical limb/species context.

## Image quality, hardware and artifacts

Quality and presentation are heterogeneous: some narrow films show clear bony contours; others have very bright low-detail hindfoot regions, subdued pelvis detail, streaks, wide body context, unusual limb positioning, overlapping hands or clipped neighbouring views. These are visible properties. The review does not assign a causal quality category without a controlled comparison or annotation.

IMG0000201 contains visible thin bright hardware-like objects near the ankle, but its red patch is on another distal bony contour. IMG0000545 is a stronger spatial association: the retained panel shows a red strip immediately beneath/overlapping a bright clip-like object above the displayed left iliac crest. IMG0002185 has a red island partly meeting a bright vertical border at the limb edge. These cases justify retaining an artifact/border hypothesis for those examples; they do not prove the cause or explain the whole normal-alert set.

Many visible external objects are remote from the masks: wrist/forearm bands or rings in IMG0000081, IMG0001109, IMG0001833, IMG0001968, IMG0002098 and IMG0003224; bright image borders in IMG0000638, IMG0000782, IMG0001946, IMG0002269 and IMG0003529. Their coexistence should not be counted as artifact-caused failures. No expert relabelling was performed, and the absence of a visible fracture on these retained panels is not independently certified.

## Unresolved tiny overlays

All nine unresolved images were actually viewed both in sheets and individually. The saved native counts confirm that these are small measured masks even when red JPEG/display marks cannot be placed confidently.

| Image | Saved maximum-pixel score | Native FP pixels | Components |
|---|---:|---:|---:|
| IMG0000224.jpg | 0.51140 | 32 | 2 |
| IMG0000241.jpg | 0.50587 | 5 | 1 |
| IMG0000643.jpg | 0.50322 | 2 | 1 |
| IMG0001433.jpg | 0.50806 | 2 | 1 |
| IMG0001678.jpg | 0.50269 | 1 | 1 |
| IMG0001745.jpg | 0.50426 | 1 | 1 |
| IMG0002753.jpg | 0.51383 | 1 | 1 |
| IMG0003085.jpg | 0.51978 | 2 | 1 |
| IMG0003553.jpg | 0.51442 | 5 | 1 |

Their anatomical mask sites and clinical causes remain unresolved. Other follow-ups resolve approximate sites but retain faint-boundary limitations; IMG0000216 retains a clipped adjacent projection and IMG0001583 retains overlapping hands/cropped distal context. The report does not replace missing context with guessed findings.

## Source-metadata strata and trust limitations

The following are saved dataset flags, not independent radiologist labels. They overlap and must not be summed; `frontal` is not automatically a verified AP acquisition. The hardware group has only one normal image, so no robust hardware subgroup conclusion is supported.

| Non-exclusive source flag | Normal denominator | E13 alerts | E14 alerts | E14 FPR |
|---|---:|---:|---:|---:|
| hand | 118 | 70 | 62 | 52.54% |
| leg | 237 | 94 | 70 | 29.54% |
| hip | 29 | 13 | 10 | 34.48% |
| shoulder | 31 | 8 | 10 | 32.26% |
| mixed | 34 | 9 | 9 | 26.47% |
| multiscan | 37 | 20 | 13 | 35.14% |
| frontal | 246 | 122 | 99 | 40.24% |
| lateral | 122 | 52 | 46 | 37.70% |
| oblique | 37 | 17 | 11 | 29.73% |
| hardware | 1 | 1 | 1 | 100% (n=1) |

The hand-flag subgroup still has particularly high normal-alert burden. Shoulder-flag alerts increase from 8 to 10 while overall alerts decrease, so the overall improvement is not uniform across strata. No scanner/hospital/age/subtle-fracture domain conclusion can be inferred from these flags.

E14's saved score-proxy Brier score is **0.23747** and equal-width 10-bin ECE is **0.26645**. These improve over E13's proxy diagnostics but remain uncalibrated. In the full 463-case score ≥0.90 bin, mean score is **0.96816**, while observed fracture fraction is **0.58889** (53 / 90 cases). A score of 0.97 must not be presented as a 97% fracture probability. No calibration fitting was performed or claimed here.

## Development implication

The matched pair's saved decision is **KEEP FOR DEVELOPMENT; full further gates required**, with **final_success=false, promotion=false, calibration_fit=false**. Its acceptance checks still fail classification counts, positive Dice, positive IoU and instance recall. The model has fewer normal-image alerts and fewer normal FP pixels than the selected matched reference, but continued anatomical false alerts, 31 newly alerted normals and uncalibrated high scores remain material weaknesses.

The actual examples support a persistent normal-anatomy/joint-end false-foreground problem with some border/object associations and tiny score-crossing masks. They do not establish whether resolution, initialization, optimization, preprocessing or annotation is the dominant causal bottleneck. Next-factor selection must combine this completed normal review with completed positive-failure, TRAIN-fit, paired curve and coverage evidence. No new intervention is selected in this report.

## Reproducibility hashes

- E14 checkpoint (recorded completed audit): `eb7c48dbaa413d10c65b6f664d6baab8928316a57a09e0eb48fef97a8b8e72ce`.
- E13 checkpoint (recorded completed audit): `dc2c51e01261ce471ad1198fe7d640c073c0bd1b57187ed31f979fadf257f670`.
- Original checkpoint preserved in audit provenance: `922f30bf691b9979aee65d386bcf73d2643558c049a7d11ab013fea315f39b81`.
- E14 completed cases: `deb8a2525742fdea7fa5fc95ab9596ef8192e9c7476be6aa64c27ed7f6147f66`.
- E14 completed metrics: `7675188a0d760309b718ad257903d2b3d970bd19c350615ea0d78573277f2392`.
- Matched pair comparison: `8dd82016e38299aa888fce6e2d0d6d139d5451a3d73ab62e1e7b49967b32080f`.
- Actual review completion: `f88700df04b7739c388f0f8912da1d390aaf75e4f58fefadef68d67df2452f97`.
- Original ordered 143-case review: `da19f5a1ccc6472562f29f6f067da81efeaa16e708d7eb2abddb1557fe9d2c57`.
- Actual sheet notes: `74c3464e53ccc3c927e60ddeca289f3f09687b09cf43756e59b12f316f7e8a2c`.
- Actual 46-panel follow-up review: `71821ea74fa3f96a56bb7d2fbc5fa5273a68439cf704dabb07dba763789d0113`.
- Metadata comparison: `eb604f37f8b46f1e3566020033761e1d65fd362a5fc97297181c941cb6016506`.

Each retained panel hash is recorded in the index, per-case review and follow-up review. Final supplemental per-case/report hashes are returned to the parent agent for session tracking. No published or local 90%+ success is inferred from these development results.

