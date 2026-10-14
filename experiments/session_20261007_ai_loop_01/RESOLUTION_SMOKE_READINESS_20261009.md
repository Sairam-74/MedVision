# Resolution smoke readiness — 9 October 2026

The new [tools/smoke_ai_resolution_pair.py](../../tools/smoke_ai_resolution_pair.py) is prepared for root review and execution. **This is a feasibility/parity tool, not a registered experiment, trained candidate, measured resolution improvement or GPU result.** No GPU step has been executed by its author.

Source SHA256: `10b9a1c3c257ff0e201f250c405d3e6ba57bb0be9a32ca12abe0fe25108161a9`.

Syntax-only AST parsing and compilation passed. The check read source and called `ast.parse` / `compile`; it did not import project modules or execute the tool. Existing foreground smoke/trainer, native preprocessing, augmentation/fallback, cached dataset, loss, weighting, atomic I/O and model/Adam digest APIs were read before implementation.

## Fixed contract

Root launch after read-only review:

```powershell
& '.venv/Scripts/python.exe' 'tools/smoke_ai_resolution_pair.py' --out 'experiments/AI_RESOLUTION_SMOKE_20261009'
```

The output must be a previously absent direct child of `experiments`, named `AI_RESOLUTION_SMOKE_*`. Existing outputs cannot be resumed or overwritten. The CLI does not require the later resolution experiment protocol: feasibility evidence precedes final registration.

Passed completion requires all actual checks and uses the queue contract:

- `status = passed_TRAIN_only_resolution_smoke`
- `full_matched_initialization = true`
- `cached256_vs_native256_exact = true`
- `input512_batch2_fp32_feasible = true`
- config includes `initial_snapshot_sha256` and `source_hashes`.

An OOM or another failure produces a failed completion with completed-arm/partial-step evidence, error, guard-verification outcome and memory counters. The tool raises after recording failure; it neither retries nor changes batch size, precision, loss, architecture or optimizer.

## Actual initializer and fixed TRAIN metadata

The full selected E14 snapshot is epoch 11 / global epoch 50:

- Full model + Adam snapshot: `experiments/AI_E14_v3_foreground_BCE5/epoch_011_resume.pt`, SHA `47c7b2b822c9e422466462f6253463076fff65098d4156158083ff11f14b3713`.
- Selected weights: SHA `eb7c48dbaa413d10c65b6f664d6baab8928316a57a09e0eb48fef97a8b8e72ce`.
- Original production checkpoint: SHA `922f30bf691b9979aee65d386bcf73d2643558c049a7d11ab013fea315f39b81`.

The four fixed sources are taken from the earlier frozen 32-source gradient diagnosis, not selected by new smoke performance. Their TRAIN indices, labels and group membership were checked in saved metadata; the runtime will additionally verify original archived bytes, decoded bytes and native mask counts.

| Source | TRAIN index | Fixed stratum | Native source shape H×W | Native annotation pixels |
|---|---:|---|---:|---:|
| IMG0002377.jpg | 1639 | hard positive | 2880×2304 | 4,262 |
| IMG0000371.jpg | 257 | hard negative | 454×373 | 0 |
| IMG0003628.jpg | 2501 | ordinary positive | 373×454 | 126 |
| IMG0001551.jpg | 1069 | ordinary negative | 373×454 | 0 |

They belong to four distinct deduplication groups. These groups are not verified patient identities. Each two-image batch has one positive and one normal, first hard pair then ordinary pair. The bounded smoke is not a representative full TRAIN epoch.

## What will be checked

Both resolutions call the unchanged native decoder/COCO rasterizer and preprocessing from original archived images and native aligned masks. The 512 branch cannot read/upscale cached 256 images or masks. The image-resolution factor changes only `PreprocessConfig.size`; CLAHE, native blur, stretch geometry and normalization remain fixed. Some selected original images are themselves smaller than 512, so resizing cannot create acquired detail; this limitation is recorded rather than labelled a resolution benefit.

Before any GPU step, raw256 unaugmented image/target/valid arrays must exactly equal the frozen cache, and raw256 augmented outputs must exactly equal the existing cached dataset outputs. Both use the unchanged positive-visibility fallback and `SeedSequence([42, 51, TRAIN_index])` augmentation. The GPU epoch seed is `42 + 51`, matching the next-epoch trainer semantics.

Three independently reloaded disposable arms perform two steps each:

1. Frozen cached256 data through the existing `WeightedTrainingDataset` and foreground trainer update.
2. Direct-native raw256 data through the same wrapper and update.
3. Direct-native raw512 data through the same wrapper and update.

Cached256 and raw256 must match per-step input, output, loss, output-gradient, parameter-gradient, resulting model and Adam digests; final model and optimizer digests must also match exactly. The tool stops before512 if this fails. This is exact parity of the bounded matched microbatches, not a claim to have replayed an entire old training epoch.

Each arm restores the same full E14 model and Adam snapshot independently. Settings remain architecture AttentionUNet64PresenceGAP, hard factor2, foreground BCE5, positive Dice1, presence weight0, normal BCE1, batch2, FP32, base seed42, learning rate1e-4 and norm clipping10. Training-mode BatchNorm remains the existing trainer's mode; no batch-statistics inference policy is introduced.

Runtime checks require finite logits/losses/output derivatives, zero invalid-pixel output gradients, actual nonzero encoder/decoder gradients, absent unsupervised-head gradients, finite post-update parameters/BN buffers/Adam, changed disposable model/Adam and exact full save/restore. Disposable snapshots are labelled smoke-only and explicitly unusable as candidate initializers.

Actual CUDA peak allocated/reserved bytes and per-step/two-step elapsed times will be recorded. Diagnostic digests and transfers affect these timings; they are not isolated inference latency or full-epoch throughput. GPU training peaks are taken before save/restore verification allocations. No memory or timing number has yet been measured for this smoke.

## Preservation and scope

The tool checks terminal E13/E14 completion, completed actual E14 normal/positive reviews and completed frozen TRAIN-only BN diagnosis. It verifies the prior queue guards, exact manifest/archive, E14 initializer, old objective/preprocessing sources and cache bytes, then hashes these and its own source for pre/post preservation checks.

Only the four specified TRAIN original image indices can be decoded through its native dataset. Dataset annotation and manifest metadata may contain other split records; no VAL/CAL/test image tensors or inference are accessed. There is no threshold optimization, calibration, model selection, experiment registration, full candidate training, promotion, frontend modification or accuracy claim.

The readiness artifact is independent of later registration/trainer/queue sources, which root owns. Actual feasibility remains pending execution and a passed completion.

