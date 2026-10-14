# Positive-case Dice coefficient review

Recorded 8 October 2026, 09:37 UTC. This review inspected saved source and completed results only. It did not read model tensors, images, target arrays, CAL/test cases or frontend code, and did not run inference or training. Synthetic CPU loss fixtures were subsequently run in `.venv-phase2`. Root selected coefficient1 versus2 as the next controlled factor; no improvement is claimed and no full experiment was launched here.

## What the existing reduction does

`medvision_pipeline.py:220` computes BCE separately for every image, dividing the sum over valid pixels by that image's valid-pixel count. It computes per-image foreground Dice loss from valid TP, FP and FN with smooth1e-6, then takes the arithmetic batch mean of BCE+Dice. It rejects any image with zero valid pixels. `candidate_loss` retains this reduction when normal BCE weight1 is selected.

`ai_hard_example_loss.py:16` calls that unchanged base and adds batch means of `(hard_weight−1)*BCE` and `(hard_weight−1)*Dice`. Algebraically, the segmentation objective is `mean_i(w_i*(B_i+D_i))`. The base-plus-offset implementation preserves the earlier factor1 scalar and gradients exactly. It does not divide by the sum of sample weights or pool the batch into one Dice ratio. E10 keeps presence supervision0 and hard factor2; within-label weights preserve class mass493/2315 and the natural unique one-pass sampling.

The proposed objective is:

`L(c) = L_existing_hard2 + mean_i(w_i*(c−1)*positive_label_i*D_i)`, with `c=1` or `2`.

This isolates the coefficient of the **foreground Dice overlap term on source-positive images**. It does not restrict differentiation to foreground pixels: positive-image Dice also penalizes predicted probability on its valid background through FP. All-image BCE, its per-image valid-area normalization, and the existing normal-image Dice term remain identical. A new batch-Dice reduction, a positive-only averaging denominator, a changed smooth value, or multiplying the whole positive loss would introduce another change.

At fixed output logits, coefficient2 leaves normal BCE and the entire normal-image loss/output gradient unchanged. It changes positive-image overlap gradients. Shared parameters, BatchNorm, norm clipping10 and Adam combine those gradients, so normal predictions and the effective shared update may still change later. Preserving a direct normal loss term does not guarantee clinical specificity.

Explicit source labels must match nonempty targets, as enforced by the frozen cached dataset; erased-positive targets are rejected. Valid masking remains in all TP/FP/FN terms. A valid mask with no pixels remains an error, not a newly clamped denominator. Invalid target pixels have no loss gradient. Normal empty targets remain in the batch and retain BCE plus the original near-constant Dice term.

## Evidence supporting a test, and its limits

The corrected E5 raw TRAIN diagnostic sampled eight positives/eight normals, with stored evaluation statistics. Positive median Dice logit-gradient L2 was6.6411e-5 versus BCE2.5923e-4; normal medians were3.5437e-10 versus1.1979e-4. It supports separating positive overlap emphasis from normal BCE supervision, but it is one older checkpoint and16 cases, not E10 gradients or a causal population estimate. Ratios of medians are not median per-case ratios. Saved uniform-logit probes also show different behavior with annotation size and predicted probability; they are mathematical probes, not observed model performance.

E10's completed raw TRAIN fit still has mean positive Dice0.375129 and151/493 masks with no target overlap. The frozen hard109 subset has Dice0.058133, only23 cases touching any GT,41 empty masks and45 nonempty masks with no GT overlap. Ordinary positive Dice is0.465110. This is broad poor TRAIN fit, not evidence of validation domain shift alone. Hard membership was selected using E7/E8 outputs; it is not an independently adjudicated subtle-fracture set.

Compared with selected E9, E10 reduced TRAIN normal alerts1,233→1,143 and hard-normal alerts573→547, but source-positive alerts432→416 and any positive GT overlap350→342. Positive aggregate Dice increased0.353313→0.375129 while global pixel recall fell0.357801→0.350909. The ordinary-positive overlap losses are a caution against assuming that an overlap coefficient automatically repairs recall. Native E10 also remains below the frozen acceptance gates; the saved pair report does not establish radiologist reliability or a production candidate.

Longer continuation remains a live alternative explanation. E9 training total fell0.956365→0.945200 over12 additional epochs, and E10 fell0.966358→0.955818. The final four E10 totals were0.958625,0.957094,0.957334,0.955818: no established plateau. Those losses use different hard weighting and are not a between-arm quality ranking. Mean Dice-loss magnitude is inflated by82.44% normal sources with near-constant empty-target loss, so its value near1 does not prove that foreground gradients are too weak. Coefficient2 is an evidence-based hypothesis, not a demonstrated bottleneck or guaranteed gain.

## Proposed matched-control contract

- Independently reload the exact full E10 selected epoch12/global30 model and Adam for both arms. Retain moments, step counters, lr1e-4 and optimizer options; compare actual initialized model/optimizer digests. Never reuse a loaded mutable Adam dictionary across arms.
- Compare coefficient1 continuation against coefficient2 continuation under identical additional12 epochs, batch2, seed42, epoch shuffle/augmentation, stretch256 preprocessing, architecture, mask threshold0.5/all, presence0, normal BCE1, hard factor2 and frozen hard109/713 catalogs. All2,808 unique TRAIN sources must occur once per epoch. Identical full initialization and budget are what separate the coefficient from simply training longer.
- Coefficient1 must retain the existing hard loss's exact scalar and output gradients. Preserve original BCE, normal Dice, per-source weights, smooth, valid masking and batch arithmetic mean. Do not normalize by positives or sample-weight sum. Reject invalid/erased targets identically in both proposed arms.
- Run synthetic mixed, all-normal and all-positive batch2 fixtures in float32/float64, valid masks and finite extreme logits. Check independent coefficient2 formula/gradient agreement, coefficient1 exact parity, zero invalid-pixel gradients, unchanged normal output gradients, and erased-positive/zero-valid rejection. Then use three independently reloaded real TRAIN smoke arms: frozen original loss, coefficient1 and coefficient2. Require identical final model+actual Adam states for original/coefficient1, finite differing coefficient2 updates, and verified full restores. Smoke metrics are not validation results.
- Keep the common VAL selection rule and matched native audit/failure review. Inspect recall, specificity, FP pixels, useful GT coverage, localization and overlap together. Reject a Dice gain with unacceptable extra normal alerts or lost fractures. Keep CAL149/test597 untouched, the original baseline/checkpoint preserved, and production unchanged.

The new `ai_positive_dice_loss.py` synthetic fixtures passed all12 dtype/pattern/extreme combinations, with exact coefficient1 scalar/output-gradient parity, independent coefficient2 formula/gradient agreement, unchanged normal output gradients and zero invalid-pixel gradients. Erased-positive, zero-valid and invalid-coefficient inputs were rejected. This was a CPU-only tensor fixture, not a model/optimizer experiment. The initially attempted general `.venv` lacked torch; the actual passing run used the project's verified `.venv-phase2`.

## Source and evidence hashes

SHA256 values below identify the inspected files; previous frozen sources were not edited.

| Source or evidence | SHA256 |
|---|---|
| medvision_pipeline.py | e1c318b6673f3aa731619b19a61bf3c6196a9346c938c033b16f7911f56df86e |
| tools/train_reliability_candidate.py | 48d006df19115111e081ae899c0fccd1e5a7d657705bea40aeef5739929a7b36 |
| tools/ai_hard_example_loss.py | f99459644ec0c5dba8c09aeda44eb432bb89d48fb9c700785378497bf8870e3a |
| tools/ai_bounded_hard_weights.py | 817334e5e441bd89a76a6db0e578604cc0fa4887e97cd2e9049ec2b351cbcc6a |
| tools/ai_cached_dataset.py | 0cdf89276b3fae7bd1279712fb37224fa009952e4f261f1400e86d6f73dbf2b9 |
| tools/train_ai_hard_candidate.py | 82cfd00a2b31d3f69196b2eb6700cff5c8e90cdaaea56991eba0c8d3f3e43370 |
| AI_LEARNED_LOSS_GRADIENTS_E5_v3_unaugmented/completion.json | d966eda2631bc4a6d5da812f74ba0c0e86826441ce3d58b367f8ccf27a6e5232 |
| Same diagnostic config.json / per_case.json | 6b2a775c89bf74ad84896cd8c021625b3b4d460825ebdc407311b25f76f54be3 / bf1f76c07ab5aa8f59a076977eadf72d1fb73c640c3edb95766f480b8ecbf834 |
| AI_TARGET_REPRESENTATION_20261007/train_loss_gradient_probes.json | 68cbd1bc82844751f9eb9fb899827f110be87c936c8aa2dad370e36bd0804f34 |
| empty_mask_loss_gradient_audit.json | 101a1afde3337dd05d3fe8caf8622638f6be52bed729bdbd7cbac2ea2bdff288 |
| AI_HARD_FIT_PAIR_E9_E10_20261008/analysis.json | aa899af0e6ffd3b4c0d8772c6dd8c33f5227b40aef7852fe67562180640ef4fe |
| AI_LEARNING_FIT_E10_v3_hard_weight2/metrics.json | 380c2ac4bcba1ad2b12258488f62c24f02ab6913c8e03b7f52ab4d5262980fd6 |
| AI_E9_v3_hard_reference/epochs.jsonl | 3cdaec65e483c1e22235a99d228f300bb7dbf7391dd293ae0b3904225f6420da |
| AI_E10_v3_hard_weight2/epochs.jsonl | 9c182bc62a43c47937b242980a4273cdf2b81dc1286315bdd39ad28627bf2657 |
| AI_HARD_MODEL_SMOKE_20261008/loss_fixtures.json | a32a94b76218c1d30bf170595a6b58b8ed93df36646c310d18567bf2ed89982a |
| New tools/ai_positive_dice_loss.py, actual CPU fixtures | 5987dd74ff7ebea6008f1682f85d21b2e90ff3b2b40e09d48658aa9cc9e80d1e |

All experiment evidence paths are under `experiments/`. No new research search was needed for this source/reduction review. No external result or source supports a claim that coefficient2 will improve this project.
