# Root full-panel follow-up — 9 October 2026

Both retained E14 panels below were actually viewed at original detail during the preceding continuation. This note preserves those observations; it does not count generated panels as reviewed or replace the other completed reviews. Original | green annotation | red prediction panels use the unchanged selected epoch 11 / global 50 checkpoint.

| Image | Actual spatial observation | Native saved counts |
| --- | --- | --- |
| IMG0000763.jpg | Elbow/forearm projection. The small red patch is above/right of the green lower elbow-region patch and visibly disjoint. No clinical cause is inferred. | TP0, FP87, FN574, Dice0 |
| IMG0004009.jpg | Hand/wrist projection. A thin central red band is contained in the broad green distal-forearm/wrist band. This recovers part of the target while leaving most unmarked. | TP140, FP0, FN868, Dice0.2439024390 |

Sources: `experiments/AI_AUDIT_E14_v3_foreground_BCE5/failures/TP_IMG0000763.jpg`, SHA `8218147e4e5e5cac11c2487ae64af0030e0a9c28cf0de54b6afe9b2200e02bb1`; `TP_IMG0004009.jpg`, SHA `34a3995a8bb1049a7d5d3bc740431a122d0e5b42695c04ee961bf63dc372d838`.

Audit per-case SHA `deb8a2525742fdea7fa5fc95ab9596ef8192e9c7476be6aa64c27ed7f6147f66`; selected model SHA `eb7c48dbaa413d10c65b6f664d6baab8928316a57a09e0eb48fef97a8b8e72ce`.

These two observations support the distinction between image alerts and useful annotated-region recovery. They do not establish clinical subtype, annotation correctness, normalization failure, resolution causality, or radiologist agreement. No new inference, training, CAL/test access, production promotion or protected-input edit occurred for this follow-up.
