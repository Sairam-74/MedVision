# Foreground-pixel BCE factor review, 9 October 2026

Proposed single-factor comparison: foreground-pixel BCE coefficient 1 versus 5, starting independently from selected E11 epoch 9/global 39 full model and Adam. This is a targeted hypothesis after the rejected E11/E12 positive-Dice experiment, not a proven primary clinical failure cause or a promise of 90% accuracy.

## Evidence motivating the hypothesis

The completed TRAIN-only diagnostic `experiments/AI_FOREGROUND_GRADIENTS_E11_E12_20261009` evaluated 32 unique raw, unaugmented TRAIN sources with both selected frozen models: eight hard positives, eight ordinary positives, eight hard negatives and eight ordinary negatives. Positives span cached target area; normals were seeded. These strata are deliberately selected and not population-representative. There was no optimizer step, validation/calibration/test image access or model-statistics change; before/after full model tensor hashes agree exactly.

For E11's eight hard positives, six have zero target overlap. The per-case foreground-probability medians range from 0.00007414 to 0.00223707. Median output-gradient foreground L2 is 0.000146721 for BCE1, 0.000054454 for Dice1, and 0.000206106 for their baseline total. Ordinary-positive baseline foreground L2 median is 0.000807389; ordinary Dice1 is 0.000792780. E12 still has seven/eight hard positives with zero overlap. These observations support investigating weak foreground learning signals in confidently suppressed targets. They do not establish the shared-parameter gradient, optimizer response, population-wide mechanism or an adjudicated medical cause.

The untrained foreground-BCE10 mathematical probe raises E11 hard-positive foreground-gradient L2 median to 0.001665650 while preserving background derivatives at the same frozen outputs. It is not a trained candidate and was not selected as the next coefficient. Root selected the more moderate coefficient 5 for a controlled comparison. The existing median norms cannot simply be added or scaled to predict a future model's median gradient or clinical performance; coefficient 5's benefit remains unmeasured on candidate validation.

The actual E11/E12 mask reviews also show whole-target misses, very small partial masks and nonempty predictions at unrelated regions. E12's mean Dice gain 0.008208 accompanied three extra FN, 12 extra FP, 61,848 extra false-positive pixels and four extra zero-overlap positive images. Increasing Dice alone did not establish balanced reliability. Foreground BCE is a different, isolated training hypothesis that must still be rejected if it trades better coverage for excessive normal alerts or poorer localization.

## Exact objective and invariants

New module: `tools/ai_foreground_bce_loss.py`, public API `foreground_bce_loss(..., foreground_bce_coefficient)`.

Start with the unchanged `hard_example_loss` using presence weight 0, Dice coefficient 1, normal BCE coefficient 1 and unchanged hard-factor 2 source weights. For batch size B, source weight w, valid-pixel count n and binary target y, add:

`offset = mean_i [ w_i * (k - 1) * sum_j(valid_ij * y_ij * softplus(-z_ij)) / n_i ]`

Only valid GT-positive BCE receives coefficient k. There is no foreground-area normalization, per-batch weight renormalization, target duplication, class resampling or change to Dice. The additive output-gradient change is:

`(k - 1) * w_i * (sigmoid(z_ij) - 1) * y_ij * valid_ij / (B * n_i)`.

Normal-image and positive-image background output gradients remain exactly unchanged at the same outputs. Shared encoder/decoder parameter gradients and subsequent predictions can still change through foreground learning; preserved local background derivatives do not guarantee unchanged false-positive performance after training.

Coefficient 1 returns the original scalar/component graph directly, plus a zero diagnostic field, preserving exact output-gradient arithmetic. Coefficient 5 changes only total, segmentation_total and BCE through the foreground offset; Dice and presence components remain unchanged. Explicit source labels must agree with nonempty valid target foreground. Erased-positive, invalid-only targets, zero-valid images, nonbinary masks, nonfinite values, invalid weights and unregistered coefficients are rejected.

The future matched pair must retain selected E11 full-model/full-Adam initialization, 12 additional global epochs 40–51, seed 42 and identical epoch augmentation/shuffle seeds, BS2, Adam 1e-4, hard factor 2 and the same 109/713 hard catalog, natural unique 2808 one-pass coverage, fixed 256 preprocessing and native 0.5/all independent masks, and unchanged feasible-first selection. No production replacement, CAL/test fitting or new data is included.

## Verification completed and pending

Synthetic CPU fixtures ran successfully on 9 October with no dataset or checkpoint reads and no GPU work. Twelve fixtures cover float32/float64, mixed/all-positive/all-normal batches, finite ordinary logits and extreme logits up to ±1200, per-source weights and invalid-pixel exclusion. They demonstrate coefficient 1 exact old-loss scalar/output-gradient parity; coefficient 5 independent weighted log-loss/Dice scalar and gradient agreement; analytic foreground offset agreement; exact unchanged normal/background derivatives; unchanged Dice/presence; zero invalid-pixel gradients. Ten bad-input fixtures are rejected.

New `tools/smoke_ai_foreground_bce.py` is a protocol-gated GPU smoke preparation, **not yet executed by this reviewer**. It will independently reload the selected E11 epoch 009 full snapshot in three arms (old loss, coefficient 1, coefficient 5), use the same four actual TRAIN hard/ordinary positive/negative sources and two BS2 discarded steps at augmentation global 40, and verify full model/Adam initialization and restore. Required evidence includes exact old-loss/coefficient 1 final model+Adam parity, coefficient 5 finite updates and analytic offset, unchanged background/normal derivatives and Dice/presence, nonzero shared/decoder gradients, absent unsupervised head gradients, and frozen guards before/after. Smoke updates are discarded artifacts and must never initialize the full experiment.

Actual protocol registration, GPU smoke, matched training and validation evaluation remain root-owned. Training success or derivative parity is not evidence of fracture-model improvement. Frozen sensitivity, specificity, native Dice/IoU, localization, useful original coverage, calibration, robustness and generalization gates still apply; the locked test remains untouched until a suitable final candidate is frozen. No clinical subtype, view interpretation or causal claim is fabricated.
