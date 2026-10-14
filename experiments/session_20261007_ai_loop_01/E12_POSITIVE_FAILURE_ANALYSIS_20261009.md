# E12 positive segmentation failure review

Completed on 9 October 2026. All 56 selected positive failure cases across ten original-detail JPG sheets were actually viewed as Original | green annotation | red independent prediction. Three ordered observation batches retain 18, 18 and 20 individual notes. Generation of these sheets is not counted as review; this record follows actual viewing.

Source: completed native audit `experiments/AI_AUDIT_E12_v3_positive_Dice2`, selected epoch 3/global epoch 33. Checkpoint SHA256: `c93ca3b3143cf3a096c72905f211d24ca8bd93fa871c93c15fbd4ce774c4904c`. Manifest SHA256: `4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318`. Both completed E11/E12 native audits have verified saved metrics/per-case hashes and exactly the same 463 unique IDs and source labels: 83 positive and 380 normal images. No model tensors or new predictions were loaded for this review.

The registered comparison changes positive-case Dice coefficient 1 to 2 with unchanged BCE, normal Dice, hard factor 2, model/full Adam initialization, data, seed, budget and selection. Both arms completed all 12 additional epochs. Their independently selected epochs differ: E11 epoch 9/global 39 versus E12 epoch 3/global 33. This is the registered selected-model comparison, not a same-training-epoch effect estimate.

| Saved native VAL measure | E11 reference | E12 Dice2 candidate |
|---|---:|---:|
| TP / FN / TN / FP | 67 / 16 / 241 / 139 | 64 / 19 / 229 / 151 |
| Accuracy | 66.52% | 63.28% |
| Sensitivity | 80.72% | 77.11% |
| Specificity | 63.42% | 60.26% |
| Precision | 32.52% | 29.77% |
| F1 | 0.463668 | 0.429530 |
| AUROC | 0.807356 | 0.801649 |
| AUPRC / average precision | 0.564097 | 0.605160 |
| Mean positive Dice | 0.375114 | 0.383322 |
| Mean positive IoU | 0.284169 | 0.284676 |
| Global pixel precision | 0.319380 | 0.350479 |
| Global pixel recall | 0.227128 | 0.346286 |
| Native false-positive pixels | 189,799 | 251,647 |
| Mask-instance IoU 0.5 matches | 30 / 99 | 26 / 99 |
| Mask-instance IoU 0.5 precision / recall | 0.107143 / 0.303030 | 0.082803 / 0.262626 |
| Brier / ECE of uncalibrated max-pixel proxy | 0.274517 / 0.280461 | 0.292691 / 0.311815 |

E12 improves mean Dice by 0.008208 and IoU by 0.000507, and aggregate target-pixel coverage increases. Nevertheless it adds three missed positive images, 12 normal alerts and 61,848 false-positive pixels against the matched reference, while instance matching and proxy calibration become worse. Native coverage remains below the E10 initializer's 0.428037 and the original same-ID model's 0.730235. These measured results and the actual masks support the completed pair analyzer's decision: **REJECT as balanced overall improvement at the registered operating point.** No claim of reliable 90% accuracy or promotion is warranted.

## Actual failure evidence

Saved tags identify 19 complete empty misses, seven complete mislocalizations, 21 cases with target recall below 0.5, and 14 with prediction precision below 0.5. Five cases have both under- and over-segmentation tags, so these are overlapping tags across 56 unique selected cases. There are 26/83 positive images with zero target-pixel overlap, compared with 22/83 for E11. Mean segmentation gains therefore coexist with more complete per-image failures.

- **Empty targets persist or newly appear.** IMG0000019 has a broad distal-forearm band without red; IMG0001367 and IMG0001391 leave elbow annotations unmarked; IMG0002086 leaves two shaft patches unmarked. IMG0001073, IMG0002181, IMG0002392, IMG0002463 and IMG0002587 show no prediction in either annotated component of their composite images. Foot targets IMG0002533, IMG0003797 and IMG0003798 remain empty.
- **Wrong-region masks are counted as positive alerts.** IMG0002470 marks a cast-covered segment above the green elbow corner; IMG0002501 marks above the elbow and adds a farther shaft patch while its proximal-forearm target is unmarked. IMG0002619 marks a lower upper-arm shaft region instead of the proximal target; IMG0002732 marks the opposite metatarsal side from its lateral-foot annotation. IMG0002584 has scattered marks away from its shaft target, and IMG0002586 marks the second plated component while the green annotation is in the first. IMG0001948's nonempty zero-overlap mask is too small to localize confidently at sheet scale and remains explicitly unresolved. For IMG0002501, max-pixel score 0.999392 accompanies zero target overlap; this proxy does not represent a 99.94% reliable localized diagnosis.
- **Partial coverage remains visible.** IMG0000190, IMG0001365, IMG0002397, IMG0002516 and IMG0004009 reduce broad green bands/polygons to smaller patches. IMG0002535 and IMG0003342 leave most of long femoral annotations uncovered. IMG0002553 predicts only a tiny part of the elbow target.
- **Extra and oversized regions remain visible.** IMG0002304 adds separated shoulder-region patches; IMG0002349 and IMG0002442 expand compact annotations into wider rounded masks. IMG0002480 adds a second elbow-area patch outside the target. IMG0002524 connects two targets with a broad region through unannotated area. IMG0002549 adds a mark on the opposite pelvic side. IMG0002606, IMG0003843, IMG0004044 and IMG0004374 add separate regions beyond the green annotations.

Actual sheets show hardware, casts and overlapping anatomy in several errors, but their causal role is unadjudicated. No clinical cause, subtle/nondisplaced subtype, acquisition-view label, annotation defect or patient/study linkage is inferred from these appearances.

## Same-ID changes that matter for reliability

Saved decisions show seven E11-empty images becoming E12 positive alerts: IMG0000471, IMG0001948, IMG0002303, IMG0002374, IMG0002584, IMG0002619 and IMG0002732. Only three regain any target overlap: IMG0000471, IMG0002303 and IMG0002374. Four gains are nonempty wrong-region predictions, so they cannot be described as four newly localized fractures.

Ten E11 positive alerts become E12 empty misses: IMG0000019, IMG0001367, IMG0001391, IMG0002086, IMG0002342, IMG0002392, IMG0002465, IMG0002502, IMG0002587 and IMG0003797. Four of these were already zero-overlap E11 alerts; their disappearance changes alert counts without losing useful target coverage. Six had some E11 overlap and become empty, and IMG0002586 separately loses its small E11 overlap while retaining a wrong-region positive alert. Thus seven images newly lose all target overlap while three regain overlap, a net four additional zero-overlap images. These are saved per-case comparisons, not expert fracture adjudication.

## Retained full-panel follow-up required

| Case | Retained E12 panel | Remaining uncertainty |
|---|---|---|
| IMG0001948 | `failures/TP_IMG0001948.jpg` | Nonempty zero-overlap mask is not clearly resolved on the sheet; exact location/extent. |
| IMG0002333 | `failures/TP_IMG0002333.jpg` | Tiny elbow mask and fine boundary alignment. |
| IMG0002342 | `failures/FN_IMG0002342.jpg` | Annotation is truncated at the sheet boundary; complete green extent. |
| IMG0002402 | `failures/TP_IMG0002402.jpg` | Tiny marks in two components; exact component-specific alignment. |
| IMG0002553 | `failures/TP_IMG0002553.jpg` | Tiny elbow prediction and fine overlap. |
| IMG0002586 | `failures/TP_IMG0002586.jpg` | Fine extent of the tiny second-component plated-region mark. |

All ten sheets were viewed, but these fine details remain unresolved pending root's retained full-panel review. No additional full native panels were viewed by this reviewer for E12. Review completion does not certify every boundary or clinical interpretation.

## Retained evidence and scope

`E12_all_positive_sheets/actual_batch_01.json`, `actual_batch_02.json` and `actual_batch_03.json` contain exact ordered observations. The completed recorder verified all 56 selected cases, retained panel hashes, audit case identity and unique coverage before writing per-case JSON/CSV and completion.

- Per-case review SHA256: `a19cfb552efba9c73f7ec45d88ac1fdfb87ace38af8fd65539568fcba1d90018`.
- Notes SHA256: `2df2e545e5cbe013b2792f80914cdca6ba0b05c4275912b7559fe8fdd00e5355`.
- Index SHA256: `359195c7297ca65a1ad6b22025b25bd16ad85a0a74c0a35910649c6ccee219b9`.

No inference, checkpoint tensor loading, GPU work, CAL/test access, data/label edits, production changes, guarded training-source edits or root status updates were performed. Proxy calibration values are saved validation diagnostics; no calibrator was fitted. This review selects no next factor and makes no generalization or clinical-safety claim.
