# MedVision Project Status

## DATA

- Dataset source: `FracAtlas.zip` in the workspace root.
- Extraction/cache location: `medvision_temp/` is used for extracted demo images.
- Total samples: 717.
- Class balance: 0 empty masks, 717 non-empty masks.
- Positive-pixel percentage across non-empty masks: average 0.495%, minimum 0.061%, maximum 2.997%.
- Split strategy: deterministic stratified split by mask positivity using a fixed seed (`seed=42`). Positive and negative indices are shuffled separately, then split 70/15/15.
- Current split sizes: train 501, validation 107, test 109.
- Augmentation: training-only augmentation is active. If `albumentations` is installed, the code uses `A.Compose` with horizontal flip, rotate, and elastic transform. If it is not installed, the script falls back to a local synchronized augmenter that applies flip, rotation, and elastic warp to image/mask pairs.

## ARCHITECTURE

AttentionUNet is a 4-level binary segmentation U-Net with attention-gated skip connections.

| Stage | Module | Output shape |
| --- | --- | --- |
| Input | Grayscale image | `1 x 256 x 256` |
| Encoder 1 | `ConvBlock(1 -> 64)` | `64 x 256 x 256` |
| Downsample | `MaxPool2d` | `64 x 128 x 128` |
| Encoder 2 | `ConvBlock(64 -> 128)` | `128 x 128 x 128` |
| Downsample | `MaxPool2d` | `128 x 64 x 64` |
| Encoder 3 | `ConvBlock(128 -> 256)` | `256 x 64 x 64` |
| Downsample | `MaxPool2d` | `256 x 32 x 32` |
| Encoder 4 | `ConvBlock(256 -> 512)` | `512 x 32 x 32` |
| Downsample | `MaxPool2d` | `512 x 16 x 16` |
| Bottleneck | `ConvBlock(512 -> 1024)` | `1024 x 16 x 16` |
| Up 4 | `ConvTranspose2d(1024 -> 512)` | `512 x 32 x 32` |
| Attention 4 | `AttentionGate(512, 512, 256)` | `512 x 32 x 32` |
| Decoder 4 | `ConvBlock(1024 -> 512)` | `512 x 32 x 32` |
| Up 3 | `ConvTranspose2d(512 -> 256)` | `256 x 64 x 64` |
| Attention 3 | `AttentionGate(256, 256, 128)` | `256 x 64 x 64` |
| Decoder 3 | `ConvBlock(512 -> 256)` | `256 x 64 x 64` |
| Up 2 | `ConvTranspose2d(256 -> 128)` | `128 x 128 x 128` |
| Attention 2 | `AttentionGate(128, 128, 64)` | `128 x 128 x 128` |
| Decoder 2 | `ConvBlock(256 -> 128)` | `128 x 128 x 128` |
| Up 1 | `ConvTranspose2d(128 -> 64)` | `64 x 256 x 256` |
| Attention 1 | `AttentionGate(64, 64, 32)` | `64 x 256 x 256` |
| Decoder 1 | `ConvBlock(128 -> 64)` | `64 x 256 x 256` |
| Output | `Conv2d(64 -> 1) + Sigmoid` | `1 x 256 x 256` |

- Total parameters: 31,387,045.
- Trainable parameters: 31,387,045.
- Input/output contract: grayscale `256 x 256` input, single-channel sigmoid mask output of the same spatial size.

## TRAINING PIPELINE

- Default loss mode: `focal_tversky`.
- Loss composition: `Dice + focal_tversky` by default.
- Legacy loss mode: `weighted_bce` remains available for compatibility, but its inverse-frequency weight is capped at 25.0 instead of using the raw imbalance ratio directly.
- Weighted BCE details: `pos_weight = min(25.0, max(1.0, (1 - pos_ratio) / (pos_ratio + 1e-6)))`, where `pos_ratio` is estimated from the current training split.
- Optimizer: `Adam`.
- Learning rate: `1e-4`.
- Scheduler: `ReduceLROnPlateau(patience=5)` on validation loss.
- Checkpoint criterion: best validation Dice, saving `best_model.pt` when validation Dice improves.
- Early stopping: patience 8 on validation Dice.
- Max epochs default: 40.
- Batch size default: 8.
- `--max-items` default: `None`, so plain `python medvision_ai.py` uses the full FracAtlas dataset.
- Run summary: the script now prints a one-line config summary at the start of the training run, including dataset size, split sizes, loss mode, epochs, and batch size.
- Loud warning behavior: if `--max-items` is set and the resulting training split contains fewer than 50 positive samples, the script prints a warning that the results are not meaningful.

## INFERENCE PIPELINE

- Image preprocessing: grayscale read, CLAHE contrast enhancement, `3 x 3` Gaussian blur, resize to `256 x 256`, normalize to `[0, 1]`.
- Inference wrapper: `run_medvision_inference` loads or uses the provided model, preprocesses the image, runs the network, thresholds the mask, and passes it to severity assessment.
- Threshold calibration: validation threshold is swept from `0.10` to `0.90` in steps of `0.05`, and the threshold with the best validation Dice is saved to metadata beside the checkpoint.
- Last calibrated threshold recorded in the earlier smoke run: `0.10`.
- Severity logic: the predicted mask is reduced to the largest connected component, then area, perimeter, compactness, and aspect ratio are computed. Severity tiers are heuristic and area-based: `<150` Mild, `<900` Moderate, otherwise Severe.

## LAST RUN RESULTS

- Status: training complete
- Epoch: 40/40
- Train loss: 0.6335
- Validation loss: 0.6333
- Validation Dice: 0.4526
- Validation IoU: 0.2925
- Validation predicted-positive ratio: 0.0076
- Best validation Dice so far: 0.4526
- Best validation loss so far: 0.6333
- Approach: focal_tversky-only objective (no extra Dice term) to lower the loss scale while keeping the sparse-foreground focus

## KNOWN ISSUES

- A tiny `--max-items` value can still be passed intentionally for smoke testing, but it now prints a loud warning when the training split has fewer than 50 positive samples.
- The project still contains a legacy `weighted_bce` option for compatibility, even though `focal_tversky` is the new default.
- Training on the full FracAtlas dataset is CPU-heavy and can take a while before the first epoch summary appears.
- The earlier smoke run with `--max-items 16` was not representative of real training quality and produced unstable metrics.

## LATEST TRAINING RUN

Status: training complete

- Dataset: FracAtlas (717 samples)
- Split: train 501 / val 107 / test 109
- Loss mode: focal_tversky
- Max epochs: 40
- Batch size: 8
- Max items: None
- Approach: focal_tversky-only objective (no extra Dice term) to lower the loss scale while keeping the sparse-foreground focus
- Epoch: 40/40
- Train loss: 0.6335
- Validation loss: 0.6333
- Validation Dice: 0.4526
- Validation IoU: 0.2925
- Validation predicted-positive ratio: 0.0076

