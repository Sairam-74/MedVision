# Root full-panel follow-up, 9 October 2026

Actually viewed retained panels at original detail; no new inference, altered mask, dataset label change or clinical adjudication. These supplement the completed assistant-team contact-sheet reviews.

| Run / case | Actual retained-panel observation | Saved exact-pixel cross-check |
|---|---|---|
| E11 normal 0970 | No definite red region is resolvable on the retained foot/ankle panel. | Two predicted native pixels; box [181,179,182,181], maximum .54717. The unresolved display is consistent with a tiny alert, not evidence of an empty saved mask. |
| E11 normal 1263 | No definite red region is resolvable on the retained shoulder panel. | Two native predicted pixels; box [156,176,158,177], maximum .50246. |
| E11 normal 3917 | No definite red region is resolvable on the retained forearm/hand panel. | Two native predicted pixels; box [165,131,166,133], maximum .52380. |
| E11 positive 1365 | Small red point at the elbow/proximal forearm while green spans a substantially broader region. | Dice .014517; exact fine boundary is not established from the display. |
| E11 positive 1391 | Small red edge mark at the elbow versus a broad transverse green region. | Dice .031390; display does not justify calling the entire fracture localized. |
| E11 positive 2342 | Green lower-leg target reaches the lower retained-panel edge; red is a small separate-looking patch near that boundary. Whole target extent remains unavailable from this retained view. | Saved TP5357, Dice .218297. E12 loses the whole mask: FN43723, maximum .023989. |
| E11 positive 2480 | Cast-like covering is visible; tiny red dot approximates a small part of the green upper-arm band. This does not establish a cast-caused error. | Dice .162933. |
| E11 positive 2586 | Plate/screw-like structures visible in two source components; the red mask is not clearly resolved. | One TP pixel, zero FP, FN465; GT box [94,216,125,274]. A positive case alert conceals extremely poor coverage. |
| E11 positive 2587 | Tiny red spot lies in the upper component; green target in the other component is left unmarked. | TP26, FN553, zero FP; two GT boxes. Dice .085950; multiple annotated regions are not all covered. |
| E12 positive 2342 | Entire red mask absent despite retained green region near lower leg; hardware is visible but is not proven causal. | Complete miss versus the partially overlapping E11 prediction. |
| E12 positive 0019 | Combined wrist/hand source image, green transverse wrist target in upper component; red mask absent. | FN25249, maximum .472202; E11 Dice .599610/TP16906. Not exclusively a tiny-target failure. |
| E12 positive 0144 | Green target at elbow in a combined source image; red mask absent. | FN21290, maximum .095666; E11 also misses. |

A subsequent attempted E12 TP2502 panel path was absent: the saved E12 category is FN. No claim of viewing that absent panel is made; the attempt stopped before viewing 3797. Both cases remain covered by the E12 positive-review owner using actual index paths.

Tiny normal alerts coexist with tiny true-positive masks, so a size filter can remove real overlap as well as false alarms. The frozen .5/all policy remains unchanged. Most causal explanations (normal cortical structure, hardware, subtle fracture, annotation correctness, positioning) remain unadjudicated. Target size and exact stored overlap are technical facts; they do not establish clinical subtlety.
