# E5 full training-fit diagnostic

The selected E5 epoch8 checkpoint was evaluated on all2808 unaugmented TRAIN grids. The matching463 validation grid maps were reused from the completed native audit. No new validation X-ray inference, calibration, reserved test evaluation, retraining, threshold tuning or promotion occurred.

| Metric, grid threshold0.5/all | TRAIN | Validation |
|---|---:|---:|
| Fracture images |493|83|
| Normal images |2315|380|
| TP / FN |325 /168|61 /22|
| TN / FP |1138 /1177|171 /209|
| Accuracy |52.10%|50.11%|
| Sensitivity |65.92%|73.49%|
| Specificity |49.16%|45.00%|
| AUROC, max-pixel proxy |0.640410|0.653710|
| Positive Dice |0.184409|0.218315|
| Positive IoU |0.128709|0.158995|
| Positive soft Dice |0.172864|0.201050|
| Positive cases without any target overlap |275 /493|48 /83|

These are grid diagnostics against nearest projected256 labels, not native segmentation acceptance results. Native validation differs slightly because bilinear probability inversion and thresholding occur at the original image geometry; the completed native report remains unchanged. Do not combine grid pixel counts with native pixel counts.

Both partitions perform poorly. Validation sensitivity and positive Dice are higher than training at this selected checkpoint, while specificity is somewhat lower. This evidence does not support an explanation based only on overfitting or validation domain shift. It supports investigating inadequate learning of fracture-specific appearance and the use of a single segmentation maximum for image decisions. It does not prove a cause or guarantee that adding supervision will help.

The separately completed label representation audit found no disappeared positive targets at256, a validation mean roundtrip label Dice0.931137 and only one erased augmented training exposure covered by the existing fallback. Sparse supervision remains important: the unaugmented training foreground occupies0.086179% of all grid pixels. Representation statistics and synthetic uniform-logit gradients are diagnostics, not measured candidate improvements or theoretical performance ceilings.

All206 native E5 false-positive contact panels and all69 tagged positive failures were visually inspected as technical reviews. Repeated wrist/ankle overlays, shaft/elbow errors and isolated image-decision triggers are documented. Internal bright dividers are also marked in some cases; a low outer-border-band statistic cannot rule out internal acquisition artifacts. Clinical causes and annotation disagreements require expert adjudication.

Elapsed4372.13 seconds includes the shared Modern Standby pause and concurrent GPU training. It is not an idle inference-time benchmark. Patient independence remains unverified because reliable patient identifiers are unavailable.

Next intervention remains conditional on completing and auditing E6. Original data/checkpoint/baseline and application files are preserved.
