# E13 completed positive native failure review — 9 October 2026

The selected coefficient-1 reference still fails to provide a useful mask in 20 of 83 positive validation images: 14 empty predictions and 6 nonempty predictions with zero annotated-pixel overlap. Positive case alerts therefore overstate useful localization. E14 improves several aggregate measurements, but its corresponding positive-case review shows this particular coverage count getting worse.

## Evidence and actual review coverage

E13 completed all 12 additional epochs. The selected checkpoint is additional epoch 6 / global epoch 45, SHA `dc2c51e01261ce471ad1198fe7d640c073c0bd1b57187ed31f979fadf257f670`. The native audit contains the frozen 463 unique validation IDs, including 83 positives. Completed audit case and metric hashes were independently rechecked, and E13/E14 IDs, source labels, and per-case target pixel areas agree exactly. This does not establish patient/study independence or annotation correctness.

All **51 selected positive segmentation failures across all 9 sheets** were actually viewed with `view_image` at original detail, comparing Original | green annotation | red independent prediction. Each case has an individual observation in exact index order. The other 32 positive cases were not visually reviewed in this selection. Four retained full panels were additionally viewed for 1391, 2342, 2392, and 2586. Generation alone was not counted as review.

- [Ordered case review](E13_all_positive_sheets/per_case_visual_review.json), SHA `f93c6d7b35faedf71340da390c1fc6314bf2ecd0533e8081f9584434031e53f8`.
- [Actual sheet notes](E13_all_positive_sheets/actual_sheet_notes.json), SHA `04131e3d0236661b6faae82267a9608cf3e329b2fb9a5dcfaf39bb0d311f3352`.
- [Selection index](E13_all_positive_sheets/index.json), SHA `17ec96c462aec62c3ea82a8007be14ec76c3bfb0a490ab1efe05af1e6aaad781`.
- [Completion](E13_all_positive_sheets/completion.json) validates exact selected membership and retained panel hashes.
- [Actual full-panel follow-up](E13_all_positive_sheets/actual_full_panel_followup.json), SHA `afc78d0871952253e15cfe5f83e262c5f205938acea9e453271f3fb8e0182047`.

Audit `per_case.json` SHA: `6431defac958f37527531aae7381b614fce07f74906cd39da9b71075598d188f`. Audit `metrics.json` SHA: `f9cded16423ba4a26066d577629dc328c82a12e52b8d7c9dd281b1097a2ea530`.

## Saved native measurements

| Measurement | E13 reference |
| --- | ---: |
| TP / FN / TN / FP images | 69 / 14 / 204 / 176 |
| Sensitivity / specificity | 83.13% / 53.68% |
| Mean positive Dice / IoU | 0.424430 / 0.323116 |
| Mean positive mask recall | 0.476728 |
| Global pixel precision / recall | 0.148938 / 0.452736 |
| Native TP / FP / FN pixels, including normal excess | 177530 / 1014446 / 214597 |
| Mask-instance IoU 0.5 matches | 33 / 99 annotations, among 436 predicted regions |
| Positives with any target overlap | 63 / 83 |

The automatically defined failure tags, checked against the actual panels, are 14 complete empty misses, 6 complete mislocalizations, 23 under-segmentations with target recall below 0.5, and 21 over-segmentations with precision below 0.5. Thirteen cases carry both under- and over-segmentation tags, giving 51 distinct selected failures. These descriptive thresholds are not radiologist adjudication or a clinical adequacy definition.

## Recurring observed errors

Empty predictions omit clearly displayed annotations in multiple contexts. Examples include elbow targets 0763, 1367, 1948, 2493, and 2502; two-component casted images 2463 and 2587; upper-arm targets 2584 and 2619; the foot target 2533; and the wrist band 4009. Cast, fixation, or overlapping components are visible in some originals, but this review does not establish why the model fails there.

Nonempty masks can identify a different region entirely. In 0144, green is at the elbow while red is on the lower torso/pelvic edge; in 2303, green is at the shoulder/proximal upper arm while red is lower on the chest/ribs. Full panels confirm a lower forearm trace rather than the green elbow band in 1391, and a shaft trace above the wrist annotation in the second component of 2392. In 2470 the red region lies higher on the casted upright forearm than the green elbow corner; in 3797 it lies in a different part of the foot. All six have TP pixels equal to zero.

Long or broad green regions often receive short rounded masks. Examples include 1365 (TP304/FN1474), 2535 (TP167/FN1230), and 3342 (TP754/FN2123). The masks cover only part of the displayed annotated length. Two displayed components can also receive unequal coverage: 1073 marks mostly one wrist target, whereas both components have green bands. Displayed components must not be treated as verified paired studies or AP/lateral labels.

Useful overlap coexists with substantial unrelated excess. In 0019 red extends around the wrist/hand beyond the small green distal forearm band. In 1041 it adds two separate higher forearm patches. In 2333 it marks only part of the elbow annotation and adds several distant patches across overlapping components. In 2349 multiple shaft and hand regions substantially exceed a small wrist target; in 2374 a separate upper shaft patch accompanies target overlap; 2602 and 3843 also combine incomplete long-target coverage with additional patches.

## Paired comparison and unresolved detail

E14's selected model increases macro Dice from 0.424430 to 0.429107 and global pixel recall from 0.452736 to 0.510075. Actual reviewed examples show large gains in 0190 and 2333, a recovered elbow overlap in 1391, and substantially more overlap in 2586. These gains do not remove the mixed behavior: 1073, 2086, 2181, 2342, and 2732 lose all annotated overlap; 2374, 2602, and 3342 lose substantial coverage. Across all 83 same-ID positives, three cases gain any target overlap and five lose it, reducing any-overlap coverage from 63 to 61. Nonzero overlap is necessary but insufficient for useful clinical localization. Full positive failure comparison is recorded in the [E14 analysis](E14_POSITIVE_FAILURE_ANALYSIS_20261009.md).

The full retained 2342 panel still truncates the green target at its lower display boundary. This is a limitation of the retained visualization; it is not evidence that the source target bitmap is truncated. The complete target extent cannot be adjudicated visually here. In 2586, the three saved overlapping pixels are too small to place reliably in the retained panel, although the near-total missed target is clear. Full panels resolve the qualitative placement of the tiny predictions in 1391 and 2392; exact per-pixel boundaries are not clinically adjudicated.

E13 fails every joint count/overlap target: TP69 versus minimum79, TN204 versus342, Dice0.424430 versus0.523797, and IoU0.323116 versus0.377569. Masks and case scores remain research decision-support outputs. No inference, GPU work, tensor/array loading, CAL/test access, label changes, guarded input changes, or production promotion were performed during this review. Clinical subtle/nondisplaced subtypes, failure causes, radiologist agreement, and external generalization remain unavailable. No next factor is selected here.
