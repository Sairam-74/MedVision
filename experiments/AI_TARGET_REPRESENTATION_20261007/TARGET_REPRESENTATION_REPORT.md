# Actual mask representation diagnostic

Frozen data v3; all493 TRAIN positives and83 validation positives. Normal masks are explicitly empty. No image inference or training, no calibration/test masks rasterized, no source data changed. Detailed counts are retained in per_positive_mask.json/CSV; configuration/source hashes in completion.json.

| Measurement | TRAIN256 | TRAIN512 | Validation256 | Validation512 |
|---|---:|---:|---:|---:|
| Positive images |493|493|83|83|
| Minimum projected target pixels |40|171|62|252|
| Median projected target pixels |226|901|237|938|
| Entire positive targets lost |0|0|0|0|
| Annotated instances lost |0|0|0|0|
| Mean label roundtrip Dice |0.926148|0.961536|0.931137|0.964198|
| Mean label roundtrip IoU |0.863633|0.926357|0.871801|0.931113|

Method: rasterize the existing native annotation, project with the registered nearest-neighbor stretch, inverse with the registered bilinear interpolation, threshold at0.5 and compare to the original native annotation. These are label representation scores, **not model results, achieved accuracy, or mathematical upper bounds**. They quantify discretization only; fracture-line image features may still be lost by image downsizing even when the label survives.512 improves representation fidelity but is not yet a trained candidate or demonstrated improvement.

Foreground occupies only0.086179% of all naturally sampled TRAIN grid pixels at256. This is severe pixel imbalance despite17.56% of TRAIN images being positive. At256 the median positive mask occupies226/65536 pixels. Source labels describe regions; surviving region pixels do not prove sufficient detail for the actual fracture line.

Registered augmentation geometry was simulated for12 epochs on each TRAIN positive:5916 exposures at each resolution. Exactly one would completely erase its positive target:IMG0002386. The already-registered fallback retains its original aligned image/mask. The same exposure is the only one retaining less than half the projected target area. Therefore this diagnostic provides no evidence of widespread target disappearance in E5/E6. It does not measure augmentation realism or image artifacts. No validation augmentation was performed.

TRAIN-only analytical gradient probes use actual smallest/median/largest TRAIN foreground counts but **synthetic uniform logits**. At probability0.01, the40-pixel mask has summed foreground gradient -0.001743 versus background +0.011067 for BCE+Dice. The226-pixel mask has -0.008478 versus +0.013728. The1964-pixel mask has -0.044403 versus +0.013303. These are sums over separate foreground/background scalar logits, not gradients of a learned network. They support inspecting sparse-target supervision and the pressure toward empty predictions; they do not prove the cause of every error or establish a better loss. Exact component values at0.1/0.01/0.001 are in train_loss_gradient_probes.json.

Combined with E5's22 empty misses,26 wrong-region positive masks and poor AUROC, the evidence supports investigating explicit fracture-presence supervision and sparse-region learning. Threshold changes cannot repair wrong regions. Higher resolution remains a later controlled option; it cannot be assumed to solve larger visible missed targets or weak case discrimination. E6 must finish before selecting the next intervention.
