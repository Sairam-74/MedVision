# E11 positive segmentation failure review

Completed on 9 October 2026 after resuming the six sheets already recorded on 8 October. All 52 selected positive failure cases across all nine original-detail JPG sheets were actually viewed as Original | green annotation | red independent prediction. Sheets 1–6 contain 36 prior observations; sheets 7–9 add 16 observations. No prior observation was claimed as a new view during resumption.

The source is the completed native audit `experiments/AI_AUDIT_E11_v3_positive_Dice_reference`, selected epoch 9/global epoch 39 of the coefficient1 continuation reference. Checkpoint SHA256: `c1703d13e5b4cdf35b600c48825ec93c3394570ab1df44d20e9a06b41abc2b84`. Dataset manifest SHA256: `4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318`. Metrics below are saved native VAL results, not new inference or independent clinical adjudication.

| Saved native VAL measure | E10 initializer | E11 selected reference |
|---|---:|---:|
| TP / FN / TN / FP | 67 / 16 / 181 / 199 | 67 / 16 / 241 / 139 |
| Accuracy | 53.56% | 66.52% |
| Sensitivity | 80.72% | 80.72% |
| Specificity | 47.63% | 63.42% |
| Precision | 25.19% | 32.52% |
| F1 | 0.383954 | 0.463668 |
| AUROC | 0.785289 | 0.807356 |
| AUPRC / average precision | 0.574039 | 0.564097 |
| Mean positive Dice | 0.379528 | 0.375114 |
| Mean positive IoU | 0.283667 | 0.284169 |
| Global pixel precision | 0.221086 | 0.319380 |
| Global pixel recall | 0.428037 | 0.227128 |

E11 has 60 fewer normal alerts with the same number of positive case alerts, but useful foreground coverage remains a major weakness: native global pixel recall falls by 20.09 percentage points against the initializer. The reduced false-positive burden therefore does not establish balanced segmentation improvement. E11 still misses 16/83 fracture-labelled images, marks 139/380 normal-labelled images, and fails the frozen TP79 / TN342 and original coverage/Dice requirements. These are validation observations; no promotion is justified by this review.

## Numerical tags and actual appearance

Saved per-case tags identify 16 complete empty misses, six complete mislocalizations, 24 cases with target pixel recall below 0.5, and 14 with prediction pixel precision below 0.5. Eight cases have both under- and over-segmentation tags, so these are overlapping tags across 52 unique selected cases. There are 22/83 positive images with zero target-pixel overlap: 16 empty masks plus six nonempty wrong-region masks. At native mask-instance IoU 0.5, 30/99 annotated instances match among 280 predicted regions; precision 0.107143 and recall 0.303030 are mask-instance proxies, not adjudicated clinical detection accuracy.

The visible findings support the following recurring errors:

- **Whole targets left empty.** Examples include elbow targets IMG0000144 and IMG0000763, shoulder/upper-arm targets IMG0001710, IMG0002303 and IMG0002619, the knee target with visible wire hardware IMG0000471, and lateral-foot targets IMG0002732 and IMG0003798. Both annotated components in IMG0001073, IMG0002181 and IMG0002463 remain unmarked. Casts, hardware and overlap are visible context; their causal role is unproven.
- **Small predictions inside or near much longer targets.** IMG0001367, IMG0002516 and IMG0004009 show compact red patches that leave most of the green band/polygon uncovered. The long femoral annotations in IMG0002535 and IMG0003342 are reduced to small red regions near one end. This is a spatial coverage problem even where the image is counted as a positive alert.
- **Nonempty masks at the wrong region.** IMG0002502 marks the distal forearm/wrist while the green target is beside the elbow; IMG0003797 marks the ankle and central foot instead of the lateral metatarsal target. IMG0002465, IMG0002470 and IMG0002501 visibly displace prediction to an adjacent but unannotated part of the elbow/limb. IMG0002392 marks only a displaced region in one component of a composite wrist image. Saved zero overlap supports these six complete mislocalization tags. IMG0002502's maximum-pixel score is 0.991872 despite zero target overlap; it is an uncalibrated pixel proxy and must not be presented as a 99% reliable localized diagnosis.
- **Extra patches beyond the target.** IMG0002409 and IMG0003523 add separate shaft marks away from the annotation. IMG0002524 broadens and connects two distal-forearm targets and adds another spot. IMG0003843 includes several shaft patches and a separate broad ankle patch. IMG0004044 and IMG0004374 visibly expand a compact green target into a larger rounded red region.

Clinical causes, subtle/nondisplaced status, view adjudication and annotation correctness remain unadjudicated. Composite images were inspected as their displayed components; component appearance does not establish AP/lateral/oblique labels or patient/study linkage. No causal claim about hardware, casts, resolution, loss, architecture or image quality follows from these sheets alone.

## Full-panel details still unresolved

All sheets have been viewed, but fine detail in the following retained panels requires root follow-up. The notes explicitly preserve uncertainty rather than describing unseen pixels:

| Case | Retained panel | Unresolved detail |
|---|---|---|
| IMG0001365 | `failures/TP_IMG0001365.jpg` | Very small red point; exact overlap within the elbow/proximal-forearm target. |
| IMG0001391 | `failures/TP_IMG0001391.jpg` | Tiny elbow mark; fine boundary alignment. |
| IMG0002342 | `failures/TP_IMG0002342.jpg` | Green lower-leg target is truncated by the sheet boundary; complete target extent and red coverage. |
| IMG0002480 | `failures/TP_IMG0002480.jpg` | Minute red point against a short green band. |
| IMG0002586 | `failures/TP_IMG0002586.jpg` | Metadata confirms a nonempty very-low-overlap mask, but red extent is not clearly resolved on the sheet. |
| IMG0002587 | `failures/TP_IMG0002587.jpg` | Nonempty prediction and component-specific overlap are not clearly resolved at sheet scale. |

No additional full native panels were viewed by this reviewer during E11 review; full-panel follow-up is pending. Completion certifies actual selected-sheet/case review, not resolution of every tiny boundary or radiologist adjudication.

## Retained review evidence

`E11_all_positive_sheets/actual_batch_01.json`, `actual_batch_02.json` and `actual_batch_03.json` contain ordered individual observations. `actual_sheet_notes.json` and `per_case_visual_review.json`/`.csv` retain all 52 notes and linked panel hashes. The PowerShell recorder checks exact ordered membership, unique coverage, completed-audit case identity and retained native-panel hashes before completion.

- Per-case review SHA256: `54f5240173b31a5db8f949713b49c50c780b0b264456c36cbf45ef5946493f37`.
- Notes SHA256: `c9da5fe014028064da65cb193aaa8707138954577c8450a21e08f0e50090b55f`.
- Index SHA256: `712a956b8bc54718cceb71713a3c1df4fb162c9ee6510804bbf7a31eb2cc657b`.

No inference, checkpoint tensor loading, GPU work, CAL/test access, data/label edits, training-source edits, production changes or root status updates were performed. This review records observed failure evidence and remaining detail uncertainty; it selects no next experiment.
