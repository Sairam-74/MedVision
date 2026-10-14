# E14 completed positive native failure review — 9 October 2026

Foreground BCE coefficient 5 improves several selected-model validation aggregates versus the matched continuation, but it does not reliably recover missed annotated regions. Six of its seven newly positive fracture alerts contain **zero target overlap**. Positives with any target overlap fall from 63 to 61 out of 83, despite case FN falling from 14 to 13. Nonzero overlap is necessary but insufficient for useful clinical localization. The pair's recorded decision is **KEEP FOR DEVELOPMENT; full further gates required**, with no promotion.

## Evidence and actual review coverage

E14 completed all 12 additional epochs. Its selected checkpoint is additional epoch 11 / global epoch 50, SHA `eb7c48dbaa413d10c65b6f664d6baab8928316a57a09e0eb48fef97a8b8e72ce`. The frozen native audit contains all 463 unique validation IDs and 83 positives. Completed case and metric hashes were independently rechecked. E13/E14 IDs, source labels, and native per-case target areas agree; selected epochs differ under the unchanged selection rule, so this is not a same-epoch comparison.

All **52 selected positive segmentation failures across all 9 sheets** were actually viewed at original detail with Original | green annotation | red independent prediction. Every selected case has an individual ordered note; the other 31 positives were not visually reviewed in this selection. Eight full retained panels were additionally viewed for 0763, 1367, 2342, 2397, 2493, 2584, 2586, and 3797. Generation was not counted as review.

- [Ordered case review](E14_all_positive_sheets/per_case_visual_review.json), SHA `31b9ff9746061949c4f02b4d5264f11fd824cdb1de4067a36e2e67f6bfad4374`.
- [Actual sheet notes](E14_all_positive_sheets/actual_sheet_notes.json), SHA `2b1f123f9379f7fdb9d8e18e18e66b25d290e7fff90aa08b71b2a2a46bf82419`.
- [Selection index](E14_all_positive_sheets/index.json), SHA `5dce0715c5b5efa19d742975bf93055b5ec251aeec28e65c542cb55d3d28a292`.
- [Completion](E14_all_positive_sheets/completion.json) validates exact selected membership and retained native panel hashes.
- [Actual full-panel follow-up](E14_all_positive_sheets/actual_full_panel_followup.json), SHA `de0722040e88d5a8c6cad6dc649b7237e0692bdac207f6ce577462f5e8bcc518`.

Audit `per_case.json` SHA: `deb8a2525742fdea7fa5fc95ab9596ef8192e9c7476be6aa64c27ed7f6147f66`. Audit `metrics.json` SHA: `7675188a0d760309b718ad257903d2b3d970bd19c350615ea0d78573277f2392`.

Correction: the sheet-07 note called the displayed components in 2586 “forearm/hand”; that wording was incorrect. The subsequently viewed full retained original shows plated lower-leg/ankle and foot components. The full-panel follow-up explicitly corrects the anatomy wording while preserving completed sheet evidence. The first/second-component mask observations and saved pixel measurements remain unchanged.

## Measured selected-model comparison

| Measurement | E13 reference | E14 coefficient 5 |
| --- | ---: | ---: |
| TP / FN / TN / FP images | 69 / 14 / 204 / 176 | 70 / 13 / 237 / 143 |
| Accuracy | 58.96% | 66.31% |
| Sensitivity / specificity | 83.13% / 53.68% | 84.34% / 62.37% |
| Positive Dice / IoU | 0.424430 / 0.323116 | 0.429107 / 0.327273 |
| Mean positive mask recall | 0.476728 | 0.480403 |
| Global pixel precision / recall | 0.148938 / 0.452736 | 0.367863 / 0.510075 |
| Global TP / FP / FN pixels | 177530 / 1014446 / 214597 | 200014 / 343705 / 192113 |
| Mask-instance IoU 0.5 matches | 33/99, 436 predictions | 34/99, 285 predictions |
| Positives with any target overlap | 63/83 | 61/83 |
| Positive images with zero target overlap | 20 | 22 |

E14 has 13 empty misses, 9 complete mislocalizations, 19 under-segmentations with recall below 0.5, and 20 over-segmentations with precision below 0.5. Nine carry both under/over tags, giving 52 distinct selected failures. E13 has 51 distinct failures; 45 IDs fail in both models. Seven IDs newly meet a failure tag (2323, 2397, 2449, 2518, 2524, 2558, 2606), while six leave that tag selection (1041, 1198, 2303, 2304, 2472, 2553). Leaving the descriptive selection is not proof of clinical adequacy; these latter E14 panels were not part of the actual failure-only visual selection.

The mask-instance measure differs from component-box localization: both models match 33/99 boxes at IoU 0.5, while mask IoU 0.5 matches increase 33→34. Neither is a separate trained detector or canonical COCO evaluation. E14 mask-instance recall 34/99 remains below the original model's 35/99 and misses 65 annotation instances.

## Alert recovery is not fracture-region recovery

| Newly positive E14 image | E14 TP pixels | Actually observed result |
| --- | ---: | --- |
| 0763 | 0 | Small superior elbow-edge sliver separate from the green inferior wedge |
| 1367 | 0 | Three off-target pixels, too tiny to locate reliably visually |
| 2465 | 0 | Small red region below the green outer-elbow target |
| 2493 | 0 | Tiny red upper-arm speck superior to the green elbow wedge |
| 2584 | 0 | Tiny elbow trace far below the green upper-arm shaft target |
| 2619 | 0 | Middle upper-arm patch below the proximal green band |
| 4009 | 140 | Thin central part of the green wrist band; FN868 still remains |

Conversely, E14 removes six old fracture alerts. Two (0144, 2392) already had zero overlap in E13, so their newly empty masks remove unrelated excess without reducing target coverage. Four (1073, 2181, 2342, 2732) lose annotated overlap. Image 2086 stays an alert but changes from TP196 to TP0, with red only below the shaft targets near the wrist. Across all 83 saved positive records, any overlap is gained in 1391, 2303, 4009 and lost in 1073, 2086, 2181, 2342, 2732. Thus a small image-level sensitivity gain coexists with a net loss of two nonzero-overlap positives.

## Visible gains, regressions, and remaining bottleneck

Some improvements are substantial. In 0190 red moves from predominantly lower rib-region excess to the annotated shoulder/proximal upper arm; Dice rises .021→.605, although target recall remains below 0.5. In 2333 red covers much more of the green elbow region, reducing FN23419→6802, with persistent added lower-component excess. In 1391 red moves into the green elbow band instead of the lower shaft. In 2586 overlap rises TP3→142, but most target remains missed and the second plated component acquires an unannotated red spot. In 2349 distant shaft/hand patches disappear, though the remaining wrist mask is still much larger than its tiny annotation.

Other images regress materially. In 2374 reducing excess also reduces recovered target TP29739→9523. Long green strips in 2535 and 3342 still receive short patches; 3342 loses target coverage despite almost eliminating excess. Plate-associated target 2602 drops TP203→45. The casted lower-leg target 3843 has less overlap and continued lower ankle-region excess. In 2442 all target pixels are marked, but excess thickening plus a new inferior patch makes FP477→687. These are actual spatial observations, not inferred clinical causes.

The completed unaugmented TRAIN fit also qualifies the foreground hypothesis: fixed hard positives have Dice .139391→.134691 and any-overlap 44→39/109, while ordinary positive Dice increases .495670→.530537. Those selected reused TRAIN hard cases are not an independent difficult-case test, and their grid measurements cannot be combined with native validation pixels. Nevertheless, stronger foreground weighting has not demonstrated hard-target recovery across this project. The remaining evidence-supported problem is inadequate annotated-region coverage with wrong-region responses, especially on persistent hard cases; no particular clinical cause is proven and no next factor is selected here.

## Uncertainty and acceptance gaps

Full panels resolve the qualitative tiny wrong-region placement in 0763, 2493, 2584 and confirm severe under-coverage in 2397. E14's three off-target pixels in 1367 and two in 3797 are too small for reliable fine visual placement. Both retained 2342 panels cut the green region at the lower visualization boundary; this does not establish a defect in the source target bitmap. Exact borders and clinical subtype remain unadjudicated.

Maximum native pixel scores remain uncalibrated case proxies: the completely mislocalized 2470 mask has score .949, while 2086 has .753 and 2619 .718. A high maximum score does not establish correct fracture-region placement. Whole-audit Brier .291743→.237469 and ECE .329343→.266454 improve, but this was not calibration fitting and these scores are not validated clinical probabilities.

E14 still fails combined acceptance: TP70 versus 79, TN237 versus 342, Dice .429107 versus .523797, IoU .327273 versus .377569, and original mask-instance recall. Global pixel recall .510075 remains below original .730235. Mean positive Dice remains below original .503797. A selected development gain therefore does not establish 90% accuracy or radiologist reliability.

No new inference, GPU work, tensor/array loading, CAL/test access, guarded-input changes, labels, data, or production model changes occurred in this review. Patient/study independence, clinical subtle/nondisplaced labels, clinical causes, radiologist correction rates, and external generalization are not available. A future factor remains contingent on the completed paired evidence and wider review.
