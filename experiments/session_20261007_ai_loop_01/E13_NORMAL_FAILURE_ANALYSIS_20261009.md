# E13 normal-image failure review — 9 October 2026

All 176 E13 normal-image alerts were actually reviewed on 20 original-detail contact sheets. The existing recorder verified exact unique coverage and the linked retained-panel hashes. All 45 cases flagged for small, secondary or cropped marks received actual original-detail retained full-panel follow-up. Two additional panels were viewed to correct coarse anatomy descriptions: 47 unique full-panel views in total. Sheet generation alone was not counted as review.

This is a review of completed saved native VAL results. It performs no inference, training, tensor loading, source-image decoding, CAL/test image access, label changes or model promotion. The retained panels display the full source extent at their retained rendering resolution; viewing them does not recover the original native pixel resolution.

## Saved operating-point evidence

E13 is the foreground BCE coefficient-1 reference, selected at additional epoch 6 / global 45. E14 is the coefficient-5 candidate, selected at additional epoch 11 / global 50. Both audits cover the same 463 source IDs with the same source labels, groups, native shapes and nonexclusive flags. Of these, 380 have dataset normal labels. E14 is compared here through its saved metadata; its visual review is separate.

| Saved native VAL measure | E13 reference | E14 candidate |
| --- | ---: | ---: |
| Normal alerts / normal sources | 176 / 380 | 143 / 380 |
| Normal nonalerts | 204 | 237 |
| Normal false-positive rate | 46.32% | 37.63% |
| Specificity | 53.68% | 62.37% |
| Positive case alerts / missed case alerts | 69 / 14 | 70 / 13 |
| Total normal FP native pixels | 705,381 | 176,344 |
| Median FP native pixels per alerted normal source | 275.5 | 258 |
| Normal alerts with multiple saved mask components | 79 | 28 |
| FP masks containing at most 16 native pixels | 9 | 18 |
| FP masks containing at most 32 native pixels | 19 | 26 |
| Normal alerts with maximum-pixel score at least 0.90 | 53 | 37 |
| Normal alerts with maximum-pixel score at least 0.99 | 8 | 8 |

The same-ID normal transitions are 112 FP to FP, 64 FP to TN, 31 TN to FP and 173 TN to TN. E14 has 33 fewer normal alerts at its selected checkpoint, an 8.68 percentage-point lower normal false-positive rate. It also introduces 31 alerts on sources that E13 did not alert. This selected-model comparison has different selected epochs and does not establish a same-epoch causal effect or candidate acceptance.

The positive counts are **case mask alerts**, not proof of correctly localized fracture regions. This normal-only memo does not substitute for positive overlap, Dice/IoU, native failure review or final acceptance checks. Native FP-pixel totals vary with source resolution and are descriptive; they are not a clinical severity measure. Maximum-pixel scores are uncalibrated alert proxies, not fracture probabilities.

## Actual visible patterns

Individual ordered notes for every source are in `E13_all_normal_alert_sheets/per_case_visual_review.json` and CSV. Examples observed in the actual retained views include:

- **Broad transverse joint-region or forefoot bands:** 0071 shows a broad proximal forefoot band; 0149 and 0224 show broad knee/distal upper-leg regions; 1340 shows a distal-forearm band plus distal hand islands. These locations are observations, not a diagnosis of why the model fired.
- **Separated islands in a single source:** 0208 has multiple ankle/forefoot islands; 1764 has three hip/pelvic-side islands; 2820 has a larger metatarsal region plus two narrower strips. Stored component counts can include tiny islands that do not separately resolve in retained panels.
- **Shaft-region alerts away from an obvious joint centre:** 0811, 0922, 1647 and 2881 show upper-leg, lower-leg or forearm shaft marks. Their presence does not prove cortical shortcut learning or incorrect annotations.
- **Composite images:** 0216, 0219, 2072 and 2239 show masks concentrated in one component while another component appears unmarked. 3116 has separate hand-region islands in two components. These are composite-source observations, not linked study/patient multi-view consistency measurements.
- **Chest-side or crop-adjacent regions:** 2169 and 3571 show lateral chest/arm-side marks. 2066 shows a crop-adjacent forearm island at a bright source edge; anatomy outside the crop is unavailable.
- **Visible external objects:** 0545 has red over a bright marker/clip-like object above the pelvic outline. 0201 visibly contains ankle fixation wires alongside two red regions. Several forearm images have bright rings or bands separated from their red marks. These observations do not establish artifact/hardware causation.
- **Image appearance:** some sources have bright central anatomy with reduced visible detail, dim scanned contrast, large dark fields, scan separators or bright borders. These are descriptive visual notes, not validated image-quality grades or causal mechanisms.

The full-panel supplement explicitly corrects coarse sheet wording for 0024 and 0130 (flexed knee/lower-leg rather than elbow), 0050 (side-on hand/wrist rather than foot/ankle), 2066 (crop-adjacent forearm location), and a few proximal/distal location descriptions. Initial batch notes remain preserved; the final per-case notes append the actual full-panel findings. Dataset flags support the corrections but remain source metadata, not expert anatomy adjudication.

## Marks that remain unresolved

| Source ID | Saved native FP pixels | Actual retained full-panel result |
| --- | ---: | --- |
| IMG0000079.jpg | 21 | No definite red region resolves visually |
| IMG0000642.jpg | 1 | No definite red region resolves visually |
| IMG0001450.jpg | 2 | No definite red region resolves visually |
| IMG0002639.jpg | 2 | No definite red region resolves visually |

All four were actually viewed at original retained-panel detail. Their exact stored boxes, pixel counts, scores and panel hashes are in `full_panel_actual_notes.json`; no visual location is invented. Other cases, including 0370, 0494, 0598, 3143 and 3270, resolve only as faint traces. Secondary single-pixel islands in 0837 and 1340 cannot all be distinguished separately. Native pixel boundaries were not independently decoded or clinically assessed. No minimum-mask filter or threshold change is selected by this review.

## Source-flag strata

These are **nonexclusive source flags** across the same 380 normal sources. Counts must not be added across rows. The `hand` flag includes the dataset's upper-extremity sources; `leg` includes its lower-extremity sources. They are not precise clinician-assigned anatomy or verified patient/study/view records.

| Source flag | Normal sources | E13 normal alerts | E14 normal alerts |
| --- | ---: | ---: | ---: |
| Hand | 118 | 70 | 62 |
| Leg | 237 | 94 | 70 |
| Hip | 29 | 13 | 10 |
| Shoulder | 31 | 8 | 10 |
| Mixed | 34 | 9 | 9 |
| Frontal | 246 | 122 | 99 |
| Lateral | 122 | 52 | 46 |
| Oblique | 37 | 17 | 11 |
| Multiscan | 37 | 20 | 13 |
| Hardware | 1 | 1 | 1 |

E13's 176 alerted normal sources represent 165 distinct conservative related-image groups. Groups are not proven patients; this is not a patient-independent clinical estimate. The one normal hardware-flagged source does not support a subgroup reliability claim. Shoulder-flagged alerts increase from 8 to 10 despite the aggregate normal-alert reduction. Clinical causes, fracture subtypes, expert annotation corrections and external generalization are not established here.

## Integrity and reproducibility

Both completed audit case/metric hashes were verified before comparison and rechecked unchanged afterward. The 176 review IDs exactly match E13's normal-alert IDs. Every source has a nonempty actual note and matching retained panel hash. The recorder completion includes the frozen generator/recorder provenance. All saved input hashes and paired transition IDs are in `normal_saved_pair_metadata.json`.

| Evidence | SHA-256 |
| --- | --- |
| E13 completed per-case audit | `6431defac958f37527531aae7381b614fce07f74906cd39da9b71075598d188f` |
| E13 completed metrics | `f9cded16423ba4a26066d577629dc328c82a12e52b8d7c9dd281b1097a2ea530` |
| E14 completed per-case audit | `deb8a2525742fdea7fa5fc95ab9596ef8192e9c7476be6aa64c27ed7f6147f66` |
| E14 completed metrics | `7675188a0d760309b718ad257903d2b3d970bd19c350615ea0d78573277f2392` |
| E13 actual review completion | `e35599d5c82de715aa205f9c5e22302d0072aabc5f0ba6934bbdaaadfb251510` |
| E13 final individual review notes | `217546615b3435e16ef217665f3f05ebd9503cdceb421cb7c90357d5dc6afa02` |
| E13 sheet index | `8431967dbcd6a899b7b25173b1684b422664080f5c247e5c0debbb425c90f48e` |
| E13 actual sheet notes | `babb00d01569fb87d8d493fccf01bd57bcc8a79e53ef3c32f6d7768c164754cf` |
| E13 47 full-panel follow-up notes | `52be9076f3c00e70c042e5a62dce75fb8a5aaa600db5ce3983f76d361d3adbdd` |
| E13 full-panel follow-up completion | `a6ff3c28c034571f4af5549ca7d51a3069504abbe090d930ab0d2a331a1945d4` |
| Saved normal pair metadata | `92cacaa4134d438b8d2f426ecec27e33b7f25dc86634439b888b624585f072f8` |

The review establishes heterogeneous normal-image mask failures and honest visibility limits. It does not identify a proven clinical cause, select another intervention, or promote E14. Dataset normal labels remain reference labels without radiologist adjudication; remaining false alerts and positive localization failures require the complete paired failure analysis.
