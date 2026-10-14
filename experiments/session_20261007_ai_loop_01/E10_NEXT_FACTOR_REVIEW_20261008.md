# Next controlled factor after completed E9/E10

Recorded 8 October 2026, 09:34 UTC. Recommendation: **positive-image Dice coefficient 1 versus 2**, keeping the accepted-for-development E10 hard weights and all-image BCE fixed. This selects exactly one experimental factor. It is a learning hypothesis, not a claim of the primary cause or a registration, training result, clinical improvement or promotion. This review changes no frozen source, dataset, checkpoint, production code, CAL or reserved TEST data.

## Completed evidence and remaining gap

The saved native pair reports matched configurations and initial model/optimizer metadata, with hard factor 1 versus 2 as the only training difference. Both completed 12 epochs, each seeing all 2,808 unique TRAIN sources once. Their selected checkpoints differ: E9 additional epoch 9/global 27, E10 additional epoch 12/global 30. Thus the selected-model comparison includes the common selection rule; it is not a guaranteed same-epoch treatment-effect estimate.

| Native VAL result | E9 reference | E10 hard weighting |
|---|---:|---:|
| TP / FN out of 83 fractures | 67 / 16 | 67 / 16 |
| TN / FP out of 380 normals | 171 / 209 | 181 / 199 |
| Accuracy | 51.40% | 53.56% |
| Positive Dice | 0.359342 | 0.379528 |
| Positive IoU | 0.265569 | 0.283667 |
| Global pixel precision / recall | 0.146236 / 0.344021 | 0.221086 / 0.428037 |

E10 has 28/99 matched mask instances at IoU 0.5 among 402 predicted regions: precision 0.069652, recall 0.282828. It has 591,338 false-positive pixels. Its normal case count improves by ten, while five prior fracture misses recover and five new misses appear. AUROC is essentially unchanged (0.785098 to 0.785289), and average precision decreases (0.592641 to 0.574039). These findings support KEEP FOR DEVELOPMENT under the recorded pair decision, not balanced final reliability.

The TP79/TN342 practical targets are unmet by 12 detected fractures and 161 correctly rejected normals. E10 is below the original same-ID positive Dice 0.503797, the required Dice floor at least 0.523797, original IoU 0.377569 and original instance recall 35/99. Original useful pixel recall was 0.730235, versus E10's 0.428037. Lower FP burden does not excuse that useful-coverage gap. Brier/ECE in this pair use an uncalibrated maximum-pixel case proxy; they do not establish calibrated clinical confidence. No calibration fitting or reserved-test predictions occurred.

The current completion records confirm that root actually reviewed all 199 E10 normal alerts and all 55 tagged positive failures. This reviewer read those completion records and all 55 saved positive per-case observations; I did not personally re-view their images. There is no expert clinical adjudication or relabeling. Native failure counts are 16 empty misses, 11 nonempty wrong-region cases, 16 under-segmentation and 21 over-segmentation tags; categories can overlap.

## Why shape-loss weighting is justified now

The newly completed saved **unaugmented TRAIN grid** comparison separates the frozen hard catalogs from ordinary images:

| TRAIN group | E9 | E10 |
|---|---:|---:|
| Hard positive mean Dice, 109 cases | 0.024854 | 0.058133 |
| Hard positive zero-GT-overlap cases | 88 | 86 |
| Hard positive useful pixel recall | 0.036073 | 0.056692 |
| Ordinary positive mean Dice, 384 cases | 0.446548 | 0.465110 |
| Ordinary positive zero-GT-overlap cases | 55 | 65 |
| Hard normal FP cases, 713 cases | 573 | 547 |
| Ordinary normal FP cases, 1,602 cases | 660 | 596 |

Hard weighting helps some shape learning and normal rejection, but it does not resolve the hard-positive learning problem. E10's hard-positive median Dice is still zero; 98/109 have Dice below 0.2, and 45 nonempty masks have no GT overlap. It also loses useful overlap in ten additional ordinary-positive cases despite their better mean Dice. Aggregate overlap improvement therefore coexists with important regressions. E10's entire TRAIN positive Dice is 0.375129, with 151/493 zero-overlap cases. These are poor TRAIN fits, not merely unseen-validation failures.

**Hard TRAIN cases are error-selected model examples, not clinically subtle or nondisplaced fractures.** The hard catalogs were chosen from earlier E7/E8 TRAIN errors and are not independent difficult-case validation. Mask area is an annotation-size proxy; it is not fracture conspicuity. Missing patient/study identifiers and expert subtype labels prevent clinical subtlety, patient independence or multi-view study-level claims.

The corrected E5 raw-input derivative diagnostic already showed useful positive Dice supervision alongside near-zero normal Dice derivatives; BCE still supplied normal-image gradients. Natural TRAIN prevalence is only 493/2808 fracture images. This supports testing the **relative positive overlap contribution**, without removing normal images or simultaneously changing sampling. The diagnostic is only 16 eval-mode cases from E5, so it does not prove that E10's TRAIN gradients or Adam dynamics are dominated by background. E8's presence-gradient ratios are irrelevant to attributing E10's current objective because both hard arms use presence weight 0.

Failures are not confined to tiny regions. Root's saved observations include an empty annotated elbow region in IMG0000144; empty tibial hardware regions in IMG0002342, IMG0002372 and IMG0002374; severe proximal forearm/elbow undercoverage in IMG0001367; and proximal femoral undercoverage in IMG0003342. These are annotation-relative observations, not claims about clinical fracture visibility or metal causing the miss. The native small-region proxy detects 10/12 fractures, while the leg flag detects 8/18 and has Dice 0.188919; flags are nonexclusive, with small denominators. This weakens a resolution-only explanation and favors addressing broadly inadequate shape learning first.

## Learning continues; plateau is unproven

E9's augmented weighted total loss falls from 0.956365 at epoch 1 to 0.945200 at epoch 12; Dice loss falls 0.947172 to 0.936466. E10's total falls 0.966358 to 0.955818, and Dice loss 0.957135 to 0.946829. Both curves fluctuate but continue improving through the completed budget. Raw losses between the two arms have different weighting and should not be treated as directly equivalent objectives. High mean normal Dice constants also make a large loss scalar insufficient evidence of stalled optimization.

Native trainer validation fluctuates sharply. E10 epoch 9 obtains TP82 but TN27; epoch 12 obtains TP67/TN181. E9 reaches Dice 0.415302 at epoch 10 with TP76/TN99. No observed epoch satisfies balanced targets. Continued learning has not produced stable clinical reliability, yet it is premature to declare an architecture/initialization plateau. A candidate must be compared with an equally continued control, rather than only the earlier selected E10 checkpoint.

## Exact proposed contrast and matched control

Use E10's selected full `epoch_012_resume.pt` (global epoch 30) as the common initializer. Its selected `best_model.pt` checkpoint SHA256 recorded by the bundle is `bfbba05a924f75ed3a4261977b31bf7d7c2af9c940cfdbfc4ec2d153324c2348`; this is a file hash, not a model-tensor digest. The full snapshot exists, but this review does not load its tensors. Before registration/launch, verify snapshot/model tensor identity and restore the exact same model, Adam moments, steps and learning rate in each arm.

- Reference: positive-image Dice coefficient **c=1**, reproducing E10's existing weighted BCE+Dice exactly.
- Candidate: coefficient **c=2** on the positive-image Dice component only. Normal-image Dice and all-image BCE retain their existing coefficients.
- Keep the frozen hard catalog of 109 positives/713 negatives and hard factor 2 in both arms. Its within-class-normalized per-source weights remain unchanged; do not refresh mining, resample images or change class weights during this contrast.
- Use the same additional 12-epoch budget (global epochs 31–42), seed 42, matched shuffle/augmentation, batch size 2, Adam learning rate 1e-4, architecture, 256 resolution, preprocessing, native inverse transform, threshold 0.5/all policy and existing common selection rule.

For per-source weight w_i and the existing explicit TRAIN positive flag, the proposed mathematical contrast is:

`L_c = L_existing_E10 + (c - 1) * mean_i(w_i * positive_i * DiceLoss_i)`

Keep the batch denominator unchanged. Do not divide by the number of positive images in the current batch or normalize by batch weights; those would create an additional reduction change. The overlap objective mass for positives intentionally increases; BCE/source sampling masses stay fixed. Use an exact c=1 compatibility path and record unscaled BCE/Dice, the added positive-Dice term and total separately. A higher candidate total-loss scalar alone is not a failed experiment.

Meaningful checks before training: exact reference scalar/output-gradient parity with the existing hard loss; independent manual calculation of the c=2 increment; finite losses/gradients for all-normal, all-positive, mixed, tiny-target and near-empty-prediction inputs; zero gradients on invalid augmentation pixels; unchanged all-normal loss/gradient at identical logits; identical initial full model/Adam state; real CUDA training/checkpoint reload. No positive flag may come from a model prediction. The existing aligned target-erasure fallback must remain active. These are requested checks for future implementation, not tests performed by this memo.

Expected benefit: stronger annotation-relative shape supervision could improve useful overlap and coverage on hard positives, including those with nonempty wrong-region masks. Expected failure/tradeoff: it may expand masks and raise normal alerts, trade precision/specificity for recall, amplify ambiguous annotations, or fail because the unresolved issue is feature learning rather than loss balance. Preserved normal BCE does **not** guarantee preserved normal predictions after shared-weight updates.

Evaluate every arm with native VAL classification, mask precision/recall, Dice/IoU, IoU-0.5 instance matching, FP pixels and actual case/mask review under the unchanged thresholds. Compare TRAIN hard and ordinary groups, including regained/lost useful overlap, not just case-alert counts. Reject a candidate that improves Dice while reducing reliable fracture localization or worsening normal rejection. Retain only measured balanced development improvement; all original floors, practical count targets, calibration/robustness/freeze requirements and reserved-test restrictions remain binding. This is one seed and does not establish clinical generalization.

## Why the other four factors are deferred

Batch Dice is a different reduction with batch-composition-dependent coupling of normal predictions into the positive denominator. At the current natural batch size 2, many batches are all normal; it is not the same question as a fixed useful overlap coefficient and would complicate attribution now. Foreground-patch learning changes context, resolution exposure and sampling/inference requirements; there is no completed prepared-image evidence that a crop policy is the dominant remedy. Higher resolution preserved annotation geometry in the prior target audit but lost no target at 256; it has no measured image-feature or trained-model advantage yet, while substantial larger-target failures remain. Transfer initialization needs a compatible encoder or same-architecture TRAIN-only pretraining and a scratch control; continuing learning and untested targeted loss balance do not yet justify that larger intervention. None is rejected permanently; none is combined with the recommended factor.

The existing primary-source memo supplies relevant, limited support: [Kervadec/de Bruijne](https://arxiv.org/pdf/2304.04319) motivates examining gradient/reduction behavior, and [Eelbode et al.](https://arxiv.org/pdf/2010.13499) motivates overlap-sensitive supervision. Neither demonstrates positive-Dice coefficient 2 is optimal for FracAtlas or will achieve 90% accuracy. nnU-Net's current official code shows exposure/reduction choices, not fracture-specific superiority. Access limits from the existing research memo remain in force. No new browsing was necessary for these already verified sources.

## Evidence identity

All paths below are under `experiments/` unless prefixed `tools/`. These hashes identify the inspected current evidence; they do not replace metric-scope or tensor verification.

| Evidence | SHA256 |
|---|---|
| AI_E9_E10_HARD_PAIR/comparison.json | e5a6642653e48ceedb7656908d029e24571bbf3c9347b6301b75b64859c33f4c |
| AI_HARD_FIT_PAIR_E9_E10_20261008/analysis.json | aa899af0e6ffd3b4c0d8772c6dd8c33f5227b40aef7852fe67562180640ef4fe |
| AI_E9_v3_hard_reference/epochs.jsonl | 3cdaec65e483c1e22235a99d228f300bb7dbf7391dd293ae0b3904225f6420da |
| AI_E10_v3_hard_weight2/epochs.jsonl | 9c182bc62a43c47937b242980a4273cdf2b81dc1286315bdd39ad28627bf2657 |
| AI_AUDIT_E10_v3_hard_weight2/metrics.json | 2af8e24e675e8cd8e4fdad89c19033646b9ce13ddde41bd961386f3109053ba9 |
| session_20261007_ai_loop_01/E10_all_normal_alert_sheets/completion.json | ef6cf66f9601a9af9335f4aaa0de46f5cf34943ef33d055596cb9b6c0bf29dca |
| session_20261007_ai_loop_01/E10_all_positive_sheets/completion.json | 911a8fe3e75efd5ca12199ce7cc7cec6142a2e13619e0a0c4e95e7f48bdc6ff5 |
| session_20261007_ai_loop_01/E10_all_positive_sheets/per_case_visual_review.json | f3dd91ff85118497f63086eb05dd38f0a928e83a71038f3f7d5057c1d608ce3f |
| session_20261007_ai_loop_01/CONDITIONAL_BOTTLENECK_MEMO_20261008.md | 9e113533345d7fab431e575d4ada7ca1c1131a58d5cf23461bf3e50890c04a76 |
| session_20261007_ai_loop_01/RESEARCH_SPARSE_FRACTURE_20261008.md | 202564f00c0d1492dde83add6a391f9223a03d8bf7ed36b1db1d0001f50ecdd9 |
| AI_E10_v3_hard_weight2/bundle.json | 7e48fec557562c85b5ad32f0ecbf75ac07bbc65416637b433879088aad098bfb |
| AI_TARGET_REPRESENTATION_20261007/summary.json | 51ff8f862e08c396fc83b5422e328cfc2a703415e4eb703717d24b79669cd790 |
| AI_LEARNED_LOSS_GRADIENTS_E5_v3_unaugmented/completion.json | d966eda2631bc4a6d5da812f74ba0c0e86826441ce3d58b367f8ccf27a6e5232 |
| AI_LEARNING_FIT_E10_v3_hard_weight2/metrics.json | 380c2ac4bcba1ad2b12258488f62c24f02ab6913c8e03b7f52ab4d5262980fd6 |
| AI_HARD_DISTRIBUTION_20261008/distribution.json | 8605d158828775d6bd0ca20f092bcc1c86b8daf32483d1f40c0111c4bf2a6636 |
| tools/ai_hard_example_loss.py | f99459644ec0c5dba8c09aeda44eb432bb89d48fb9c700785378497bf8870e3a |

This memo selects a future controlled factor only. It performs no inference, optimizer step, image-array read, external-data download, calibration/test access or production promotion.
