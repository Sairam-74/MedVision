# Resolution trainer readiness — 9 October 2026

New source `tools/train_ai_resolution_candidate.py` is ready for independent review, protocol registration and the separate CUDA feasibility/parity smoke. It has not been imported or executed, and no training, inference, array/image/tensor reading, calibration/test access or production change was performed by this preparation.

Source SHA256: `536da80ef35814697693c307021405fff32cf417487e7fb6c5369808c08e8609` (309 lines).

## Matched experiment contract

- Required CLI: `--protocol`, `--out`, `--input-size {256,512}`; optional strict `--resume`.
- Protocol status must be `registered_after_completed_native_failure_analysis`; `major_factor` must be `input_resolution`.
- Registered identities are `AI_E15_v3_resolution256_reference` and `AI_E16_v3_resolution512`.
- Both arms independently restore the selected E14 epoch 11 / global 50 full model and Adam, verify registered model/optimizer digests, and confirm the full snapshot reproduces the selected model.
- Twelve additional epochs use globals 51–62, batch 2, FP32 parameters, LR 0.0001, seed 42, hard factor 2, foreground BCE coefficient 5, positive Dice coefficient 1, presence weight 0, and normal BCE weight 1. There is no new AMP, scheduler, weight decay, sampling, model, objective, normalization policy, augmentation or threshold change.
- Preprocessing derives the initializer configuration and changes only `size`. Online augmentation and shuffle retain the exact global-epoch/index RNG schedule. The native validation and feasible-first selection functions are imported unchanged.
- Protocol `caches` must contain exactly `256` and `512`, each with `path` and `completion_sha256`. The canonical dataset verifies exact ordered TRAIN rows, array hashes, dtype/read-only contract and preprocessing. This trainer also checks the requested shape and the registered native 512 cache producer binding. The 512 cache is not enlarged from the 256 cache.
- Frozen hard catalogs must have exactly 109 unique positive and 713 unique normal TRAIN IDs. Class-normalized hard-factor-2 weights preserve source-label masses. Every epoch must visit all 2,808 unique TRAIN indices once, without duplication. Native VAL remains the exact 463 unique source IDs with 83 positives, disjoint from TRAIN.
- The 256 reference's first epoch/global 51 must match `reference_replay_parity['51']` exactly for model tensors, Adam state and the entire native validation metrics object. A mismatch saves replay evidence and aborts before epoch snapshot/logging. No replay assertion is imposed after this first epoch or on 512.
- Both configs have the same 18 source hashes, including this trainer and the new native cache producer. Permitted paired config differences are `input_size`, `preprocess.size`, `cache` and its completion hash only.
- Every new snapshot, `last.pt`, bundle and config records input size and foreground/Dice/hard factors. Strict resume checks original config and initializer metadata, objective/input size, globals 50 + additional epoch, exact preceding epoch coverage and successful reference replay.

Historical E14 full snapshots and bundle did not store `positive_dice_coefficient`. Their frozen config declares coefficient 1 and the unchanged foreground-loss source implements the hard BCE+Dice objective. Absence is tolerated only for that verified historical initializer; new snapshot/resume fields are mandatory. This avoids treating a missing legacy field as a changed loss factor.

## Actual verification performed

The complete new source was read. `ast.parse` and `compile` passed without executing imports or main. A CPU-only isolated AST configuration assignment fixture used saved E14 JSON metadata and inert hash/type stubs; it confirmed that the two configurations differ only in the four allowed keys, with preprocessing differing only in size and all source hashes identical. No dummy config or output was written. The first fixture lacked the isolated `CONTRACT` stub and stopped with `NameError`; supplying the constant in the fixture made all checks pass. This was a fixture setup correction, not a trainer change.

Saved initializer metadata confirms selected epoch 11/global 50 and the requested foreground 5/Dice 1/hard 2/presence 0/normal 1/batch 2/LR/seed. Existing 256 cache metadata matches initializer preprocessing and the frozen canonical producer. Actual checkpoint/tensor restoration, exact GPU replay and 512 batch-2 memory feasibility remain the separate smoke's responsibility; these static checks are not CUDA results or evidence of improved model performance.

Adaptation source SHA256: `tools/train_ai_foreground_bce_candidate.py` = `d3da11520384ffc6de9e0f2f6d200a707f3fe039c9f1b25988730ad92fec06ff`.

Canonical cache class SHA256: `tools/ai_cached_dataset.py` = `0cdf89276b3fae7bd1279712fb37224fa009952e4f261f1400e86d6f73dbf2b9`.

Native cache producer observed SHA256: `tools/cache_ai_resolution_inputs.py` = `3c630aa7bc9168ae7cd6c223f44c0aacd2803e672f0a29663818b85079d4d332`.

## Comparison limits

Resolution is the intervention; effects of a finer target representation and the existing size-dependent augmentation geometry are consequences of that intervention, not independently isolated causes. Native VAL overlap is the common evaluation space. Raw 256/512 TRAIN-grid pixel counts, target areas and Dice/IoU must not be treated as measurements on identical grids without an explicitly compatible comparison. Timing and memory require actual controlled observations. No claim that resolution caused the current failures or will satisfy the acceptance gates is made here.

No protected source/protocol, original data/checkpoint, prior review, PROJECT_STATUS or registry file was edited. Only the new trainer and this new readiness note were created for this task. Registration, smoke, queue launch, later candidate analysis and any promotion remain gated by the parent workflow.
