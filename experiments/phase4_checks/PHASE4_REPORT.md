# Phase 4 pipeline execution evidence

Executed 6 October 2026. All computational Phase 4 tasks implemented and checked. Full-model generalization, final calibration and clinical/expert approval are separate outstanding work. Historical serving and active E2 source/config/data were preserved.

## Implemented pipeline

`medvision_pipeline.py` supplies one preprocessing path for training, validation and opt-in serving: aspect-preserving letterbox or declared stretch, configurable size (multiple of 16), CLAHE, Gaussian blur (zero disables), and unit or image-only z-score normalization. Targets use nearest-neighbor interpolation. A valid-region mask excludes padding and out-of-frame augmentation regions from every loss. Native prediction probability maps remove padding and use bilinear inverse resizing before thresholding; raw/delivered masks and metrics are computed in native coordinates. Synthetic rectangle roundtrip IoU is 1.000000; image/mask dimension and padding checks pass.

Lazy data reads the explicit v2 manifest (2,808 train / 612 validation; no test prediction path in the trainer). Training-only weighted replacement sampling accepts a requested positive fraction; natural-prevalence shuffle remains available. A seeded 50% sampler drew 50.214% positives in 2,808 draws. Validation resampling is rejected.

The output contract is **binary-logits-v2**. AttentionUNet64 emits logits directly; BCEWithLogitsLoss receives logits. Sigmoid is applied exactly once for overlap losses and inference. Historical parameter names are retained, but logits checkpoints require their bundle metadata and cannot be selected through the legacy sigmoid backend path. `/ready` rejects that misuse and bad checksums with 503. The historical checkpoint remains the default; no smoke/overfit weights were promoted.

`tools/train_pipeline.py` supports immutable new-run directories, epoch-boundary optimizer resume, source/config/manifest checks, initial recovery checkpoints, epoch-local seeds, LR, individual loss terms, valid foreground occupancy, augmented nonempty prevalence, native raw and delivered precision/recall/Dice/case errors, memory/time and per-case counts. The four-training/four-validation smoke and resume to epoch 2 passed. Its zero tiny-validation Dice is not a performance result.

## Loss conventions and checks

- BCE + Dice: unweighted valid-pixel BCEWithLogits averaged per image, plus foreground soft Dice averaged per image. Empty-target Dice alone has weak gradients, so BCE remains present.
- Focal Tversky: TI=(TP+smooth)/(TP+0.7*FN+0.3*FP+smooth), loss=(1-TI)^0.75. This weights missed foreground more than false positives; it does not inherently suppress normal-case findings.
- Symmetric binary Unified Focal: two-class foreground/background focal CE with gamma=0.5 and class weights 0.7/0.3; two-class Tversky region loss exponent 1-gamma=0.5; mixture weight 0.5. This follows the symmetric convention in the [authors' implementation](https://github.com/mlyg/unified-focal-loss/blob/main/loss_functions.py), not the asymmetric variant. [Primary paper](https://arxiv.org/abs/2102.04525). The independent NumPy calculation agrees with PyTorch within 1e-6. Focal modulation is clamped at 1e-7 to avoid infinite fractional-power derivatives at saturated sigmoid values.

All three losses pass finite-value/gradient checks on empty, full, thin, multiple-region and extreme +/-100-logit cases. Padded logits can change arbitrarily without changing loss; their gradients are exactly zero. These checks caught and corrected the saturation-gradient issue before experiment execution. [PyTorch BCEWithLogitsLoss](https://pytorch.org/docs/stable/generated/torch.nn.BCEWithLogitsLoss.html) supplies the stable BCE term.

## Resize and augmentation inspection

All **919 annotation instances across 714 positive v2 images** were rasterized and checked structurally at letterbox 256 and 512. **Zero instances and zero positive unions vanished**. Minimum positive unions contain 33 pixels at 256 and 138 at 512. Test targets were included only for structural data integrity; no test predictions, failure selection or tuning occurred. Survival is not proof of boundary accuracy or clinical adequacy; resolution comparisons still require measured validation experiments.

Local RNGs drive paired flip/rotation for image, target and valid region. Strict torch deterministic algorithms are enabled; results across library versions/devices are not guaranteed identical. Replacement-sampled repetitions of an image receive the same augmentation within an epoch, documented as a reproducibility tradeoff. Conservative +/-15-degree rotation and horizontal flip preserve binary masks and valid-region alignment. The reviewed optional elastic candidate visibly bends straight hardware and anatomy: **disabled by default and not clinically approved**, not adopted on the strength of these checks. `augmentation_review.png` records three training examples with original, conservative and elastic-candidate views.

## Real learning and shared API inference

A fresh AttentionUNet64 memorized IMG0003183.jpg (largest positive training occupancy) and IMG0000000.jpg (normal), at letterbox 128, no augmentation, BCE+Dice, Adam 1e-3, seed 42. Fixed-threshold acceptance was positive grid Dice >=0.85 and zero normal foreground pixels. It **passed after 60 updates**: grid Dice **0.965251**, normal pixels **0**, total loss **1.625443 -> 0.817111**, approximately **88.06 seconds** alongside the active CPU job. Native positive Dice from the inverse/shared serving path is **0.913160**. Grid and native scores differ due to resize/interpolation; do not mix their coordinate systems. Native target/prediction overlays were inspected in `experiments/P4_overfit_128/native_overfit_examples.png`.

These are deliberately easy, repeatedly seen training cases: **memorization sanity only**, not a generalization score, model-selection result or improvement claim. The overfit model/bundle remains isolated and marked accordingly.

Real API multipart upload for both images returned native masks identical to direct bundle/evaluation inference, plus model/bundle/config provenance. Component policies all/largest/min_pixels pass empty/single-pixel/thin/multiple regressions; default all retains every finding. Minimum-component units are **native pixels**, different from E1's historical 256-grid min16. Raw and delivered masks are retained separately. New geometry has native pixel units and returns clinical severity not applicable. Historical real API and 422/415/413 upload/dimension regressions pass after the adapter change. `tools/predict_bundle.py` also executed real inference and exported native mask/overlay/probabilities.

## Existing full training and next experiments

E2 continues unchanged on v1. First measured epoch took **74.15 minutes**, training loss **1.135661**. At threshold 0.5, validation positive Dice and sensitivity are **0**, with no predicted findings: early collapse toward background, not improvement. Twelve epochs at that first-epoch duration project roughly **14.83 hours**, replacing the optimistic 9–10-hour step projection; later epochs and early stopping can differ. Current live state at recording: `{"status": "training", "latest_epoch": 1, "current_epoch": 2, "batch": 100, "batches": 1408, "mean_train_loss": 1.0396958458423615, "smoke": false}`. It also retains the seven v1 contradictory targets discovered in Phase 3.

Next full v2 experiment must use a new run ID and the logits pipeline. Treat E2 vs the new pipeline as different protocols, not a matched loss comparison. Matched BCE+Dice / focal-Tversky / symmetric Unified-Focal comparisons must use identical v2 data, geometry, preprocessing, sampler, augmentation, seed and budget. Keep test reserved until model/config selection and calibration are frozen. No second full CPU job was launched during Phase 4.

Evidence: `checks.json`, session `phase4_bundle_api.json` and `runtime_smoke.json`, `experiments/P4_trainer_smoke/`, `experiments/P4_overfit_128/`, `experiments/P4_bundle_cli/`, and `phase4_ledger.json`. Original ZIP/checkpoint/threshold hashes and active source hashes all passed preservation checks.
