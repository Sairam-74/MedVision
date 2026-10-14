# E12 retained positive-panel follow-up, 9 October 2026

Actually viewed five retained E12 audit panels at original detail using `view_image`: IMG0001948, IMG0002333, IMG0002402, IMG0002553 and IMG0002586. Each displayed Original | green annotation | independent red prediction. Their current hashes agree with the completed E12 review index. This supplements the immutable 56-case sheet review; its notes, completion and analysis are preserved.

The sixth pending case, E12 FN IMG0002342, was already actually viewed by root and is recorded in [E11_E12_ROOT_FULL_PANEL_FOLLOWUP_20261009.md](E11_E12_ROOT_FULL_PANEL_FOLLOWUP_20261009.md). I read that record but did not claim another view of this panel. Root records an absent red mask and green lower-leg target near the retained panel boundary. The complete target extent remains unavailable from the truncated retained view; hardware causality is unadjudicated.

## Five actual additional observations

| Case / retained panel | Actual retained-panel observation | Saved native-pixel cross-check |
|---|---|---|
| IMG0001948 / `failures/TP_IMG0001948.jpg` | The green annotation is beside the upper elbow in the bent-arm image. A minute red speck is visible on the lower foreground forearm that crosses the image, far from the annotated elbow. Its detailed shape remains too small to delineate confidently even here; the green target is unmarked. | TP 0, FP 6, FN 402; Dice 0, IoU 0; max-pixel score 0.509727. This is a nonempty wrong-region mask, not an empty saved prediction. |
| IMG0002333 / `failures/TP_IMG0002333.jpg` | Green spans a broad elbow patch at the outer end of the upper horizontal limb. Red is a tiny mark at part of its lower/outer corner, with most green area uncovered. The retained view resolves partial target coverage without establishing every fine boundary. | TP 930, FP 0, FN 26,890; Dice 0.064696, IoU 0.033429. Derived target-pixel recall is 3.34%; all saved predicted pixels overlap GT, but almost all GT pixels remain uncovered. |
| IMG0002402 / `failures/TP_IMG0002402.jpg` | In the first component, red is a narrow patch at one side of the green elbow/proximal-forearm band. In the second, red is a minute point near the joint above most of the green patch. Both green regions are largely unmarked. Component-specific exact pixel attribution is not available from the aggregate counts and is not inferred. | Aggregate TP 151, FP 22, FN 891; Dice 0.248560, IoU 0.141917. Derived target-pixel recall is 14.49%. |
| IMG0002553 / `failures/TP_IMG0002553.jpg` | Green covers a small wedge around the outer elbow bend. Red is a much smaller thin horizontal mark at the lower part of that wedge; most annotated extent is uncovered. | TP 31, FP 9, FN 305; Dice 0.164894, IoU 0.089855. Derived target-pixel recall is 9.23%. |
| IMG0002586 / `failures/TP_IMG0002586.jpg` | Green is an elongated patch beside the fixation in the first forearm component. Tiny red marks lie on the plate in the second component; the first-component green target remains unmarked. This resolves the different-component error, though the tiny mark's precise shape is not established visually. | TP 0, FP 29, FN 466; Dice 0, IoU 0; max-pixel score 0.804467. Plate/screws are observed context only, not a proven cause. |

TP/FP/FN here are **pixels**, except where a case category is explicitly named. Derived target-pixel recall is TP/(TP+FN), calculated from completed saved metadata; it is not a new inference result. Maximum-pixel scores are uncalibrated proxies and do not establish reliable fracture localization. These panels establish technical mask placement and coverage, not subtle/nondisplaced subtype, acquisition-view labels, annotation correctness or clinical failure causes.

## Verified retained-panel hashes

| Case | SHA256 |
|---|---|
| IMG0001948 | `86ac8a63e5e73ea1aa9e4b01b3ee93a4a784a32e7b3122d5676d14d68251d2d5` |
| IMG0002333 | `b2f7b50b2ddc741a9504f822e22a02e3e2fa6012981c6658e690bf497ab6b357` |
| IMG0002402 | `94544ec94842172e27b87a90d67f4a838a9e0091ca6c2a9970ebda5c47987b87` |
| IMG0002553 | `4890d2b68ac789ce479579c2f59071171d9fc31c2be2a50aa0c3ae138312732a` |
| IMG0002586 | `66d86aedda8f189ace4851ecaa6c0043ac79e54399a1a5e405e06534262b8217` |

No new inference, model tensor loading, GPU work, CAL/test access, mask alteration, label change, production change or guarded-source edit was performed. This new follow-up is the only review artifact written for this task. All five requested additional panels were actually viewed; remaining uncertainty concerns fine display boundaries and the truncated extent of root-reviewed IMG0002342, not missing selected-panel review.
