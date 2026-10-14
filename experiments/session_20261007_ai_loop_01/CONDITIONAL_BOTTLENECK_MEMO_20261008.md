# Conditional bottleneck memo

Recorded 8 October 2026, 04:10 UTC. **No next intervention is selected.** E9 had ten completed epoch records and was training epoch11; E10 had not started. This memo uses existing JSON/Markdown evidence only and performs no inference, training, image reads, or changes to frozen inputs. Finish both arms, native audits, raw TRAIN fits and actual failure review before deciding.

## Observed evidence

E9's unchanged factor1 continuation is learning, but the observed checkpoints remain unreliable. Every completed epoch1–10 reports exactly2,808 unique TRAIN sources. Total augmented training loss moves0.956365→0.947709; BCE0.009193→0.009146 and mean Dice loss0.947172→0.938563. Epoch10 has native-validation Dice0.415302/IoU0.304284 and TP76/FN7/TN99/FP281. The current selection is epoch9: Dice0.359342/IoU0.265569 and TP67/FN16/TN171/FP209. Epoch10's better overlap and sensitivity coexist with much worse specificity, so overlap alone cannot select a reliable candidate. These are trainer validation records, not the completed independent native localization audit. All observed epochs fail TP79/TN342 and the original matched Dice floor0.523797.

Full unaugmented **TRAIN grid** results from previously selected models:

| Model | Positive Dice / IoU | Mask TP / FN | Normal TN / FP | Positive zero-overlap masks |
|---|---|---|---|---|
| E7 | 0.273254 / 0.196424 | 365 /128 | 1283 /1032 | 219 /493 |
| E8 | 0.252724 / 0.182737 | 406 /87 | 897 /1418 | 224 /493 |

Poor TRAIN fit contradicts a validation-domain-shift-only explanation. It does not separate optimization, feature representation, annotation ambiguity or stored BatchNorm statistics. GRID and native mask geometry differ; these rows are not final acceptance metrics. E8's native pair was rejected:13 fewer case misses but94 extra normal alerts, false-positive pixels235,568→696,136 and IoU0.5 matches23→19.

The corrected16-case E5 raw-input diagnostic measured normal Dice logit-gradient median3.54e-10 versus BCE1.20e-4; positive medians were Dice6.64e-5 versus BCE2.59e-4. Normal Dice loss is near1 while BCE supplies its gradient. Because82.44% of TRAIN cases are normal, the large mean Dice-loss scalar cannot itself prove stalled learning. These are eight positives/eight normals with frozen evaluation statistics, not full-TRAIN training gradients.

E8's16-case shared-gradient diagnostic measured bottleneck presence/segmentation norm-ratio medians19.57 for positives and62.59 for normals. This is compatible with a task-balance hypothesis, not causal proof. **E9/E10 have presence weight0**, so E8's head-gradient ratios cannot establish their current segmentation bottleneck. The corrected BatchNorm probe changed some cases under input statistics, but gave mixed positive Dice0.142621/0.173859 versus stored-stat0.156347; it does not justify changing inference statistics.

The target-representation audit lost zero positive images or annotation instances at256. TRAIN minimum/median foreground pixels40/226 become171/901 at512; annotation round-trip Dice0.926148→0.961536 (VAL0.931137→0.964198). Higher resolution preserves annotation geometry better, but these are target simulations, not trained-model gains or evidence that fracture image features survive resampling.

## Conditions for a subsequent experiment

| Completed hard-pair outcome and actual failure evidence | Hypothesis justified for consideration | Required control and limit |
|---|---|---|
| E10 improves hard-case learning or normal rejection, but both selected arms still have poor raw TRAIN overlap/coverage and failures span small and larger targets; masks are present in the inputs and label ambiguity does not explain most reviewed failures | One segmentation-loss factor, such as a fixed positive-image overlap coefficient, could test whether useful foreground learning is too weak relative to background supervision | Preserve all-image BCE, architecture, size, sampling, chosen hardness factor and optimizer initialization. Factor1 must reproduce scalar/gradient behavior; include all-normal batches, tiny targets and invalid pixels. Reject reduced normal rejection, excess FP pixels or worse localization even if Dice rises. A batch-Dice reduction is a different factor and must not be combined. |
| Remaining FN/under-segmentation is concentrated in small-target strata and actual paired native/prepared-image review shows loss of useful fracture detail; larger targets fit substantially better | A256-versus-higher-resolution comparison is more targeted than another general loss change | Existing geometry evidence supports feasibility, not superiority. Keep preprocessing policy, loss, model and source coverage matched; account explicitly for any batch/memory change. Compare small-target recall, native Dice/IoU, FP burden, latency and memory. No ground-truth-dependent inference crops. |
| Both arms plateau with broadly poor TRAIN discrimination/localization across target sizes after verified gradients and reasonable targeted loss/exposure experiments, without a specific resampling explanation | Initialization or feature learning deserves a separate controlled study | E9's current increasing overlap is evidence against declaring a plateau now. Preserve architecture in an initialization comparison; a new encoder needs its own scratch control. TRAIN-only reconstruction pretraining is a hypothesis, not a proven remedy. Original checkpoint exposure is unknown, so it cannot supply a clean independent pretraining comparator. |

If E10 improves both native case balance and segmentation/localization, retain it only for development and investigate the **remaining** failures before introducing another factor. If its gains occur only on repeatedly represented groups, or losses concentrate in deprioritized normal hip/leg cases, inspect that weighting effect first. Existing concentration and two hard-positive annotation-variant pairs are cautions, not permission to relabel or silently deduplicate a running experiment.

## Research and verification limits

The existing `RESEARCH_SPARSE_FRACTURE_20261008.md` records relevant primary sources: nnU-Net's explicit batch-Dice/exposure controls, Kervadec/de Bruijne's Dice-gradient analysis, Eelbode et al.'s overlap-loss results, and Tajbakhsh et al.'s initialization comparisons. They motivate separable hypotheses; they do not identify MedVision's cause or transfer published gains. This memo reviewed the project research records, not additional full papers. Preserve their access limitations, particularly abstract-only material. No new internet research was performed here.

Patient/study identifiers, expert subtle/nondisplaced labels, independent radiologist corrections and external validation remain unavailable. Frontal is not verified AP; mask-area size and multiple annotations are proxies. CAL149 and reserved TEST597 remain excluded. The TP79/TN342, native Dice/IoU/localization, useful-coverage and subsequent calibration/robustness/freeze gates remain unchanged.

Evidence paths: `AI_E9_v3_hard_reference/epochs.jsonl` (completed records1–10), `AI_LEARNING_FIT_E7_v3_presence_r2/metrics.json`, `AI_LEARNING_FIT_E8_v3_presence_r2/metrics.json`, `AI_LEARNED_LOSS_GRADIENTS_E5_v3_unaugmented/completion.json`, `AI_SHARED_LOSS_GRADIENTS_E8_v3_r2/completion.json`, `AI_BATCHNORM_CONTEXT_E5_v3_unaugmented/completion.json`, `AI_TARGET_REPRESENTATION_20261007/summary.json`, `AI_E7_E8_PRESENCE_PAIR_r3/comparison.json`, `AI_HARD_DISTRIBUTION_20261008/distribution.json` and `AI_HARD_GROUP_CONCENTRATION_20261008/concentration.json` (all under `experiments/`). Correct the E8 TRAIN-fit head-score prose using the existing `TRAIN_FIT_SCORE_METADATA_NOTE.md`; its numerical metrics were unchanged.

The first10 E9 records, joined with LF and a final LF and encoded UTF-8, have SHA256 `d8296c971f1f704d3fb981c3c1e65ad474375abb042e5166542372a33f64f538`. Stable E7/E8 TRAIN metric hashes are `91af5a7fdf0ad9e3b49bc3435fe56b5ef648e7d024c8e170eae26f051d5cbc3e` / `9330e6bef52625d825598b07e67ae9239c2280172d0d847207a519131b7dc70d`; resolution summary `51ff8f862e08c396fc83b5422e328cfc2a703415e4eb703717d24b79669cd790`; sparse-research record `202564f00c0d1492dde83add6a391f9223a03d8bf7ed36b1db1d0001f50ecdd9`.
