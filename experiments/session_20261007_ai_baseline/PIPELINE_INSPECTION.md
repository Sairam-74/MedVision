# Current AI pipeline inspection — 7 October 2026

Scope: model reliability only. Application/frontend/authentication/report/dashboard sources were not edited. No production weight, preprocessing, mask policy or threshold was changed before baseline evaluation.

## Production model and output

- `best_model.pt`, SHA-256 `922f30bf691b9979aee65d386bcf73d2643558c049a7d11ab013fea315f39b81`, is the original serving checkpoint. `medvision_serving.py` verifies this identity; alternative models require an explicit versioned bundle. No final v2 deployment exists.
- `medvision_ai.AttentionUNet`: one grayscale input, encoder 64/128/256/512, 1024-channel bottleneck, max-pool downsampling, transposed-convolution upsampling, four attention gates, paired Conv/BatchNorm/ReLU blocks, final 1x1 convolution and sigmoid. Binary semantic segmentation; no classifier, detector, instance head, or view-fusion module.
- Preprocess: native grayscale uint8 -> CLAHE(clip=2, tiles=8x8) -> Gaussian 3x3 -> aspect-distorting 256x256 AREA resize -> float32 /255.
- Inference: eval/no-grad forward -> sigmoid probabilities -> >=0.90 -> all connected components retained -> nearest-neighbor native inverse resize. Case decision is any retained mask pixel, not clinical diagnosis. Locations are mask components in native coordinates; predicted regions are not verified fracture instances.
- Threshold comes from `best_model_threshold.json`; historical threshold/model/validation association is unverified. No calibrated case-confidence score is served. For baseline AUROC/AUPRC/Brier/ECE only, define the maximum float32 pixel score explicitly as an UNCALIBRATED proxy.
- Historical training provenance is not recoverable from the bare state dictionary. Legacy source defaults: Adam 1e-4, ReduceLROnPlateau(patience=5), max40 epochs, batch2, early stopping; selectable focal Tversky (FN coefficient .7, FP .3, exponent .75) or weighted BCE+Dice. Legacy augmentation uses horizontal flip, +/-15-degree rotation and optional elastic warp; these defaults are not proof of what trained the supplied checkpoint. The old positive-only loader finding is documented; the current loader has already been repaired to include normals via v1 manifest.

## Existing fresh experiment

- E2: original Attention U-Net sigmoid output, fresh seed42 initialization, v1 training2815/validation612, natural sampling, BCE+Dice, Adam1e-4, batch2, 12-epoch ceiling/patience5, no LR scheduler; horizontal flip .5 and rotation +/-15 .5, no elastic. Native positive validation Dice at .5 chooses checkpoints. No final test.
- Last fully saved epoch10: positive Dice .2517178873, sensitivity .90, specificity .2051792829, normal FPR .7948207171. Saved progress reports epoch11 batch300, but process inventory shows no live trainer/queue/watcher. The state is interrupted, not currently running or completed. Last optimizer checkpoint is epoch10. Preserve incomplete-epoch evidence and original run configuration on resume.
- E2 uses v1 with seven later-discovered contradictory training labels; it cannot be relabeled as v2 or counted as an accepted improvement.
- New logits pipeline exists (`medvision_pipeline.py`, `tools/train_pipeline.py`): same parameter architecture with identity replacing final sigmoid, letterbox/stretch, valid padding, native inversion, paired deterministic augmentation, optional training-only weighted sampler, BCE+Dice/focal Tversky/Unified Focal. Adam, native validation-Dice checkpoint selection, early stopping, resume; no scheduler. Older E3/E4 queue would change geometry/blur/sampling together relative to E2. These runs have NOT begun and are not one-factor ablations against E2.

## Dataset, annotations and leakage

- Current dataset ALREADY IS FracAtlas v6 (not new external data). Unchanged 338412750-byte ZIP contains 4083 CSV labels (717 fractures/3366 normals) and 922 COCO polygon instances. COCO image list covers positives only; explicit CSV normal labels supply empty masks.
- v1 excludes59 unreadable normal images: 4024 usable. v2 further quarantines7 contradictory exact-copy training images:4017 usable, train2808(493/2315), validation612(110/502), reserved test597(111/486). v1/v2 immutable; validation/test IDs unchanged.
- v2 polygon union masks preserve every eligible positive. Native masks and image dimensions are verified against manifest when evaluating. No physical pixel spacing or clinical severity labels. Fourteen additional exact-copy annotation boundary disagreements remain unadjudicated.
- No patient/study IDs in the source CSV. Images, members, encoded hashes, decoded hashes and conservative related-image groups must be split-disjoint; check recomputed for baseline. Existing audit reviewed217 near-candidate pairs. This reduces known duplicate leakage but does not establish patient independence.
- Provider frontal/lateral/oblique flags overlap; frontal is not proven AP. Hardware, multiscan and anatomy are available; clinical subtle/nondisplaced fracture labels, reliable paired studies, scanner/hospital identities and reader ratings are not.
- Existing splits are train/val/test only; a separately frozen calibration subset is required for FUTURE models. Earlier E2 uses all612 validation images, so retrospectively dividing them does not create independent calibration for E2. Never use reserved test for that purpose.

## Runtime and restrictions

- CPU baseline uses untouched model on patched `.venv-demo` torch2.14.1+cpu. Actual full validation masks/counts/probabilities and timings will be saved; cache is float32, not the earlier float16 qualitative cache.
- GPU recovered: RTX3050 6GB, Windows OK, NVIDIA driver616.92; `.venv-phase2` torch2.9.1+cu128 successfully executes CUDA. Separate two-TRAIN-image gradient/memory benchmark is execution evidence only, no saved new weights. This older runtime retains documented dependency limitations and is used only with trusted local artifacts. No driver or environment mutation.
- No test model inference, no patient identity assumption, no outside dataset download, no automatic deployment, no guessed clinical failure labels, no frontend changes. All candidates require validation comparison and balanced acceptance before test/final promotion.
