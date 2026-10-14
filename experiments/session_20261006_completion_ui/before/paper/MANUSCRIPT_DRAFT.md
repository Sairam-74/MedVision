# MedVision: auditing normal-case errors and delivered-mask semantics in fracture-region segmentation

**Experimental manuscript draft - not submission-ready.** Measured diagnostic results from 5 October 2026. Author order, affiliations, target venue, full training comparisons and independent final evaluation remain outstanding. The user deferred the institutional project report; this is a separate research manuscript source.

A fresh normal-inclusive Attention U-Net is now training in `experiments/E2_corrected_baseline/`. Its results are not included in the tables below; those tables concern the preserved historical checkpoint. Read the run's live `state.json` and `epochs.jsonl` before resuming work.

6 October audit addendum: the archive matches FracAtlas v6 (CC BY 4.0). Exact-decoded duplicate labels contradict in three sets comprising seven training images; the active E2 run uses the preserved v1 protocol with those targets. A separate v2 revision quarantines all seven (train 2,808; validation/test IDs unchanged). Fourteen additional same-positive exact-copy sets have different union annotations, retained as provider uncertainty. All 217 non-exact candidate pairs and 17 train/validation annotation examples were visually reviewed; patient independence remains unknown. See `experiments/phase3_review/DATASET_AUDIT.md`. Tables below remain v1 historical diagnostics; no v2 full-training or final-test performance result exists.

Phase 4 execution addendum (6 October): the new direct-logits, letterbox, padding-aware pipeline passed finite-gradient/alignment/component/API/resume checks. Two deliberately easy training images were memorized after 60 updates (grid Dice .965251; native Dice .913160; zero normal pixels); these are not validation/generalization scores and do not enter the comparison table. Active v1 E2 completed epoch 1 with validation positive Dice/sensitivity zero at .5, consistent with background collapse; later epochs remain pending. No v2 full training or final-test result exists. See `experiments/phase4_checks/PHASE4_REPORT.md`.

## Abstract

We audited a local FracAtlas fracture-segmentation prototype, repaired its delivered-mask semantics, and measured the error trade-offs of an existing Attention U-Net checkpoint. Of 4,083 archive images, 59 labelled normal images failed decoding, leaving 4,024 eligible images with 717 fractured and 3,307 normal cases. A versioned grouped split separated training, validation and test images; the historical model's prior data exposure is unknown, so its evaluation is diagnostic. On 110 positive and 502 normal validation images, the corrected all-component pipeline at threshold 0.90 achieved mean positive-image Dice 0.4823, while falsely flagging 453/502 normal images (90.24%). Across 19 thresholds and three component policies, filtering did not resolve this high normal-case error rate. The study demonstrates why positive-only overlap reporting does not establish case-detection reliability. Real-model upload, aligned overlay, result retrieval and export were verified. Normal-inclusive retraining and an independent final comparison remain necessary before performance conclusions beyond this diagnostic study.

## 1. Introduction and related work

FracAtlas supplies radiographs and labels for classification, localization and segmentation [1]. These tasks require distinct evaluations: an image-level finding does not measure mask overlap. Attention U-Net introduces gated skip features in a U-Net architecture [2]; that prior work does not establish performance on this project's radiographs. Metrics Reloaded emphasizes task-aware metric selection [3]. Unified Focal loss motivates examining foreground imbalance [4], but no Unified Focal experiment has been run here.

The present contribution is an implemented reproducibility and pipeline audit with measured negative findings, rather than a new architecture or a clinical diagnostic claim. We ask whether the original checkpoint handles explicitly labelled normal images, how delivered-mask policies change overlap and case errors, and whether the application displays truthful model output. A future controlled training study will ask whether including normals and comparing losses improves the observed trade-off.

## 2. Data and protocol

The unchanged archive SHA-256 is `747119b26f2684e0e35a7688083b14b12a206149b0cfe5357824b69b3a5e6cf8`. ZIP CRC validation passed, yet 59 images were unreadable by OpenCV; an independent Pillow check of IMG0004028.jpg reported truncated image data. All exclusions were labelled normal. No truncated-image salvage was used. The eligible positive images have 922 COCO annotations. Audits found no positive mask lost under nearest-neighbor resizing to 256x256.

We grouped decoded exact duplicates and conservative related-image candidates (64-bit dHash Hamming distance at most four and 32x32 grayscale mean absolute difference below eight). This is a leakage precaution, not verified patient identity. There are 78 exact-duplicate groups, 306 similar-image candidate pairs, and 3,756 final groups. Candidate groups were kept together using a deterministic group allocation with seed 42. Visual review of grouping and patient provenance remain limitations.

| Split | Fractured | Normal | Total |
|---|---:|---:|---:|
| Train | 496 | 2,319 | 2,815 |
| Validation | 110 | 502 | 612 |
| Test | 111 | 486 | 597 |

The manifest SHA-256 is `e931cd3d3dce044f7d8f43fefeda596d39d9dc8529453f5262441c1a64e20227`. The supplied official positive-only allocation (574/82/61) differs from this protocol and was not mixed into the comparison. The test split has not been used for predictions, performance tuning or qualitative case selection in this session. Dataset integrity checks examined all image bytes and annotation structure before splitting. Historical checkpoint exposure to these images cannot be excluded.

## 3. Methods

The preserved checkpoint SHA-256 is `922f30bf691b9979aee65d386bcf73d2643558c049a7d11ab013fea315f39b81`. It strictly loads into the four-level Attention U-Net with 31,387,045 parameters and a single sigmoid output channel. Its training records mention 40 epochs and a focal Tversky-only objective, but training provenance and historical validation scores were not independently reproduced. No retraining claim is made for this checkpoint.

To preserve its input contract, preprocessing remains grayscale CLAHE (clip limit 2, 8x8 tiles), 3x3 Gaussian blur, square resize to 256x256 and normalization to [0,1]. This introduces aspect distortion; the correction in this session maps masks back by nearest-neighbor inverse scaling and preserves original viewer dimensions. Aspect-preserving training is outstanding.

We compared all connected regions, the largest region only, and retaining regions of at least 16 model-grid pixels. The 0.05-0.95 probability threshold grid has step 0.05, yielding 57 configurations on one set of validation probabilities. The original serving threshold 0.90 was retained. Its old calibration record is unverified. The best feasible positive-Dice candidate was threshold 0.80 with all components, subject to sensitivity/FPR within two percentage points of the corrected baseline. Its very small difference is not treated as established improvement, and it was not adopted for serving.

Metrics use delivered binary masks resized to the native image dimensions against native polygon-union targets. Primary mean Dice and mean IoU include only ground-truth-positive images, including missed images with zero overlap. Normal images are reported separately through false-positive cases. Empty/empty masks do not inflate the primary score. Pixel-global overlap is reported separately because it weights native-size images differently. Undefined precision is reported as null where its denominator is zero. A predicted case is positive if at least one native mask pixel survives. Geometry uses model-grid pixel count, not contour area, and an empty delivered mask has no applicable tier.

Uncertainty is estimated by 1,000 bootstrap draws over duplicate/related-image groups, with seed 42. These intervals do not quantify selection bias, historical checkpoint exposure or external-domain uncertainty. Image-level and pixel-level errors are distinct. Instance matching and external validation have not been implemented in this experiment.

## 4. Measured results

| Policy | Threshold | Positive Dice | Positive IoU | Case sensitivity | Normal FPR | Global Dice |
|---|---:|---:|---:|---:|---:|---:|
| all | 0.80 | 0.4830 | 0.3618 | 0.9818 | 0.9084 | 0.1801 |
| all | 0.90 | 0.4823 | 0.3618 | 0.9818 | 0.9024 | 0.1826 |
| largest | 0.90 | 0.4794 | 0.3632 | 0.9818 | 0.9024 | 0.2043 |
| min16 | 0.90 | 0.4811 | 0.3610 | 0.9818 | 0.8904 | 0.1829 |
| min16 | 0.95 | 0.4816 | 0.3618 | 0.9818 | 0.8845 | 0.1866 |


At the retained threshold, 108/110 positive cases were flagged and 453/502 normal cases were falsely flagged. Mean positive Dice's group-bootstrap 95% interval was [0.4227, 0.5375]. Threshold 0.80 changed mean Dice by 0.000636 and increased normal false positives to 456/502. Even the lowest-FPR configuration in the tested grid falsely flagged 444/502 normal cases. Threshold/component policy changes alone did not solve the normal-case failure.

![Threshold and normal-case error trade-offs](figures/threshold_tradeoffs.png)

![Rank-selected validation successes and failures](figures/validation_examples.png)

CPU forward latency in this diagnostic run had median 505.4 ms and 95th percentile 1209.5 ms, including output transfer to CPU and excluding preprocessing/postprocessing. First forward latency was 1117.8 ms. The run took 501.4 seconds for inference and all comparisons; figures and cache compression were separate work. Concurrent local verification work may affect these measurements, so they are not a controlled benchmark or support for a sub-200 ms claim.

A separate two-training-image sanity check ran 12 Adam updates with unweighted BCE plus Dice from fresh random initialization. Loss fell from 1.6645 to 1.4662; gradients remained finite. This verifies execution, not generalization or successful overfitting. Median two-image step time was 6.40 seconds, giving a rough full-epoch projection of 2.50 hours. The 16 GB Windows host has an RTX 3050 6 GB device, but Windows reports Code 43 and CUDA initialization fails. Python 3.13.7 and PyTorch 2.9.1+cu128 therefore executed on CPU with four torch threads. The sanity run peak process memory was 2.52 GiB; diagnostic evaluation peak was 1.18 GiB.

## 5. Application verification

Real-model API checks uploaded distinct positive and normal dataset images, checked exact original byte retrieval, native-size masks/overlays, successful polling and result access. Socket-level localhost verification checked login, frontend assets, upload-to-result, history and JSON export. Regression checks covered empty, single-pixel, thin and multiple-region masks; invalid/unsupported/oversized uploads returned 422/415/413. Four existing frontend tests, typechecking, lint and the production build passed. A first UI test run timed out while loading a lazy route; subsequent runs passed without weakening its assertions. Browser visual interaction was not verified because no browser was connected.

The service retains all predicted components, returns no applicable geometry tier for empty output, removes invented confidence and accuracy values, and caches model weights while bounding inference concurrency. Completed history is stored locally. Authentication is a temporary demo mechanism; endpoints are not suitable for shared deployment. No clinical severity labels or expert validation support the area-derived tiers.

## 6. Discussion and limitations

Normal-case evaluation changes the interpretation of the preserved model: moderate positive-case overlap coexists with very high false-positive case rates. Omitting normals from the earlier loader is a plausible contributor, but this study does not isolate it experimentally; normal-inclusive controlled retraining is required to test that hypothesis. Preserving all components slightly changed positive overlap without resolving case errors. A small validation threshold difference is not evidence of a reliable learned improvement.

Limits include unknown historical training exposure, heuristic duplicate grouping, unavailable patient IDs, unreadable normal-image exclusions, no independent test evaluation, no external validation, native polygon rasterization conventions, a single historical model, no matched architecture/loss comparisons, and uncontrolled CPU timing conditions. The recovery environment inherits global packages. A separate clean CPU installation from the pinned requirements reproduced strict loading, API checks and table/figure regeneration. Severity, clinical confidence and suitability for patient care were not validated.

## 7. Conclusion and work required before finalization

We established executable, traceable real inference and identified a substantial normal-image failure hidden by positive-only metrics. The current project is a functioning local research prototype, while the empirical study remains preliminary. Before finalization, run a corrected normal-inclusive baseline and a feasible controlled comparison, freeze selection on validation, evaluate new models once on the untouched test split, inspect grouped-image leakage candidates, and reconcile the final manuscript with those measured results. Project delivery is targeted for 10 October 2026. The user handles the 8 October poster; the institutional project report is scheduled separately.

## References verified for this draft

1. Abedeen I, Rahman MA, Prottyasha FZ, et al. FracAtlas: A Dataset for Fracture Classification, Localization and Segmentation of Musculoskeletal Radiographs. Scientific Data 10, 521 (2023). https://doi.org/10.1038/s41597-023-02432-4
2. Oktay O, Schlemper J, Le Folgoc L, et al. Attention U-Net: Learning Where to Look for the Pancreas. arXiv:1804.03999 (2018). https://arxiv.org/abs/1804.03999
3. Maier-Hein L, Reinke A, Godau P, et al. Metrics reloaded: recommendations for image analysis validation. Nature Methods 21, 195-212 (2024). https://doi.org/10.1038/s41592-023-02151-z
4. Yeung M, Sala E, Schonlieb CB, Rundo L. Unified Focal loss: Generalising Dice and cross entropy-based losses to handle class imbalanced medical image segmentation. Computerized Medical Imaging and Graphics 95, 102026 (2022); author manuscript: https://arxiv.org/abs/2102.04525

The existing handoff research matrix contains further candidate references. Current institutional reference-count and recency requirements have not been satisfied by this four-reference draft. Author agreement, guide review, venue formatting, final-version originality checks, dataset redistribution terms and a final PDF package remain outstanding. No submission or acceptance is claimed. Source and experiment artifacts are local; dataset/checkpoint redistribution remains subject to provider terms. AI tools assisted implementation and drafting; author technical review is still required.

## 6 October measured development and application addendum

A completed epoch-1 snapshot of the fresh v1 E2 baseline was evaluated on all 612 validation images (110 positive, 502 normal). Positive Dice and IoU were 0; case TP/FN/FP/TN were 0/110/0/502. One-to-one region matching recovered 0 of 137 annotated regions at both IoU >= .10 and >= .50. No predictions were produced at the admissible .10/all setting; therefore pixel/case precision is undefined. Specificity 100% results from background collapse and does not establish utility. This checkpoint was not promoted. The threshold/policy sweep, exact native counts, subgroup results, clustered-bootstrap conventions and negative examples are archived in `experiments/P6_development_validation/`. Degenerate all-zero bootstrap intervals are not zero population-risk claims. Training/controlled comparisons remain unfinished; no independent final test was performed.

The working local application now uses authenticated account-owned SQLite history, protected images, bounded upload/inference work and a patched CPU serving runtime. Real original and logits-bundle API tests, exact evaluation/serving mask comparisons, browser evidence, current dependency audits and source provenance are recorded in `experiments/session_20261006_p6p7/`. Browser demonstration includes a normal image with a false-positive region, consistent with the historical model's high normal false-positive rate; this application demonstration is not a clinical-validation study. Two examples exactly reproduce historical native integer counts after the torch runtime update, but exhaustive cross-runtime equivalence is not claimed. Final model comparison/test tables and human review are still required before this draft becomes a final paper.
