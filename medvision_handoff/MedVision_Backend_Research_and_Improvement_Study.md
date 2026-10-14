# MedVision: Research-Based Backend Improvement Study

4 October 2026 | Target: PyTorch fracture segmentation backend | Research and experiment design

## 1. Main recommendation

Keep Attention U-Net as a baseline. First repair data coverage and result semantics, then test detail-preserving inputs, loss functions and training choices under one fixed evaluation protocol. Only then compare a pretrained residual U-Net or add a region-refinement stage. A new architecture alone cannot correct omitted normal images, distorted inputs, inappropriate component filtering or misleading metrics.

This is a targeted literature review, not an exhaustive systematic review. The core reading list contains nine post-2020 research papers and one textbook, plus official PyTorch documentation. Sources were selected for direct fracture-X-ray relevance, experimental usefulness or validation methodology. Full-text sections were inspected where accessible; abstract-only and book-preview access are explicitly identified below. No source establishes an improvement already achieved on MedVision. All proposed gains require experiments; no retraining or new accuracy measurement was performed for this study.

## 2. What may be limiting the current backend

| Finding | Evidence status | Likely consequence | What to do |
|---|---|---|---|
| Loader includes only 717 COCO image records and omits 3,366 labeled normal images | Confirmed from code and supplied archive | No normal-case training/evaluation; deployment false positives remain unmeasured | Construct a manifest from dataset.csv plus annotations; include explicitly labeled normals |
| Every image is forced into 256×256 | Confirmed implementation; performance impact unmeasured | Small structures may lose detail; non-square anatomy is stretched | Compare aspect-preserving 256/512 inputs and native-detail crops |
| CLAHE and Gaussian blur always applied | Confirmed implementation; harm is a hypothesis | Enhancement may alter useful contrast; blur may soften subtle evidence | Compare raw normalization, CLAHE only and CLAHE+blur |
| Focal Tversky-only default training | Confirmed code | Trade-offs depend on foreground sparsity and normal examples | Compare against BCEWithLogits+Dice and a documented Unified Focal implementation |
| Only largest connected component retained | Confirmed code | Additional true fracture regions can be discarded | Test all-component output and validation-selected filtering |
| Detection status depends on contour area >0 | Confirmed code | A thin nonempty mask can have zero contour area and be reported negative | Separate foreground presence, component confidence and geometric area |
| Empty mask returns Mild | Confirmed code | Contradictory severity output | Use no-region/not-applicable state |
| Validation uses raw masks, serving filters components | Confirmed code | Metrics do not directly measure delivered masks | Evaluate the full deployed inference path |
| Threshold records conflict and confidence is hardcoded | Confirmed code/metadata | Outputs are difficult to interpret and reproduce | Bind calibration to model hash; remove fabricated confidence |
| No verified final run-linked test report | Evidence gap | Current improvement claims cannot be audited | Export per-case results and immutable experiment manifests |

The current code has train/eval mode switching, synchronized mask augmentation, Adam, a scheduler and early stopping. These are not missing. Nor is false-negative weighting absent: the implemented Tversky denominator is TP + 0.7 FN + 0.3 FP. Increasing model complexity or recall weighting without diagnosing failures would be premature.

## 3. Sources studied and how each helps

The contributions below mean “helped select a defensible experiment or avoid an error,” not “already improved our measured result.” IDs link the research to the proposed pipeline.

### S1. Abedeen et al. — FracAtlas (2023)

**Source:** *FracAtlas: A Dataset for Fracture Classification, Localization and Segmentation of Musculoskeletal Radiographs*, Scientific Data 10, 521.

**Links:** [Journal article](https://www.nature.com/articles/s41597-023-02432-4) · [Dataset](https://doi.org/10.6084/m9.figshare.22363012)

**Read:** Full-text dataset methods, labeling, distribution and annotation descriptions.

**Useful finding:** The dataset provides image-level labels and fracture-region instances; some images contain multiple fractures, views or hardware. Its annotation task must guide what we claim the model learns.

**Contribution to MedVision:** Supports using normals, preserving multiple findings and auditing anatomy/view subgroups. Treat masks as annotated fracture regions; do not automatically interpret them as exact physical crack widths. This is the most directly relevant source because it describes our actual data. It also corrects the repository's provisional dataset attribution: the paper is by Abedeen and colleagues.

### S2. Till et al. — Practical fracture-pipeline optimization (2023)

**Source:** *Development and optimization of AI algorithms for wrist fracture detection in children using a freely available dataset*, Frontiers in Pediatrics 11:1291804.

**Link:** [Full article](https://www.frontiersin.org/journals/pediatrics/articles/10.3389/fped.2023.1291804/full)

**Read:** Methods, ablations, results and discussion.

**Useful finding:** YOLOv7 experiments on pediatric wrist radiographs showed strong effects from image preparation and input size; unedited inputs were beneficial in their setting. Effects varied with train/test resolution and configuration.

**Contribution:** Makes our preprocessing/resolution ablation a priority. It does not prove that CLAHE is harmful on FracAtlas or that one resolution is universally best. Detection mAP gains cannot be transferred numerically to our segmentation Dice.

### S3. Fracture detection using YOLOv8 (2023)

**Source:** *Fracture detection in pediatric wrist trauma X-ray images using YOLOv8 algorithm*, Scientific Reports.

**Link:** [Journal article](https://www.nature.com/articles/s41598-023-47460-7)

**Read:** Accessible article material and indexed resolution-comparison/application sections; some repeat page retrievals failed.

**Useful finding:** The work compares 640- and 1024-pixel detection settings and selects a 1024-pixel YOLOv8s configuration for its application.

**Contribution:** Provides a fracture-specific reason to test resolution explicitly and consider a detector as a region proposal module. It is pediatric wrist bounding-box detection, not proof that YOLOv8 will outperform Attention U-Net on FracAtlas masks. Proposed detector-refinement experiments must report missed proposals as failures.

### S4. Russe et al. — Compare tasks fairly (2024)

**Source:** *AI-based X-ray fracture analysis of the distal radius: accuracy between representative classification, detection and segmentation deep learning models for clinical practice*, BMJ Open 14:e076954.

**Links:** [DOI](https://doi.org/10.1136/bmjopen-2023-076954) · [Accessible abstract](https://pubmed.ncbi.nlm.nih.gov/38262641/)

**Read:** Abstract and publication metadata; full-text mirror was inaccessible during this review.

**Useful finding:** The study aligns different model outputs to compare fracture detection. A segmentation model's reported case-classification accuracy is not a mask-overlap score.

**Contribution:** Separates our case detection, regional localization and pixel segmentation evaluations. Prevents comparing a paper's approximately 94% detection accuracy with our 0.45 Dice as though both measure the same outcome.

### S5. Oude Nijhuis et al. — External validation and difficult fractures (2025)

**Source:** *An open source convolutional neural network to detect and localize distal radius fractures on plain radiographs*, European Journal of Trauma and Emergency Surgery 51:26.

**Links:** [Full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC11742337/) · [DOI](https://doi.org/10.1007/s00068-024-02731-4)

**Read:** Full-text methods, results and limitations.

**Useful finding:** Strong bone localization coexisted with much weaker fracture segmentation, and external evaluation exposed generalization limitations. Subtle fractures remained challenging.

**Contribution:** Motivates difficult-case review and anatomy/domain-specific testing rather than relying on attractive overlays. Its pretrained ResNet-50 Mask R-CNN offers a comparison direction. The paper has an abstract/body discrepancy in external accuracy, so that number is not used as a MedVision target. AP50 is not Dice.

### S6. Yeung et al. — Unified Focal loss (2022)

**Source:** *Unified Focal loss: Generalising Dice and cross entropy-based losses to handle class imbalanced medical image segmentation*, Computerized Medical Imaging and Graphics 95:102026. Author manuscript posted in 2021.

**Links:** [DOI](https://doi.org/10.1016/j.compmedimag.2021.102026) · [Author manuscript](https://arxiv.org/abs/2102.04525) · [Author implementation](https://github.com/mlyg/unified-focal-loss)

**Read:** Manuscript loss definitions, motivation and study design.

**Useful finding:** Distribution-based, overlap-based and compound losses behave differently under imbalance; no naming convention substitutes for checking formulas.

**Contribution:** Justifies a controlled three-way loss comparison. The current alpha/beta names reverse the paper's FP/FN convention, but the actual FN weight is already larger. Its gamma=0.75 exponent is not automatically a bug: reciprocal conventions exist. The studied datasets were not FracAtlas, so improvement remains a hypothesis.

### S7. Isensee et al. — nnU-Net Revisited (2024)

**Source:** *nnU-Net Revisited: A Call for Rigorous Validation in 3D Medical Image Segmentation*, MICCAI 2024.

**Links:** [Conference paper](https://papers.miccai.org/miccai-2024/paper/2847_paper.pdf) · [Author manuscript](https://arxiv.org/abs/2404.09556)

**Read:** Full-text validation pitfalls, baseline design and benchmark description.

**Useful finding:** Architecture comparisons can be confounded by training configuration, pretraining, compute and ensembling.

**Contribution:** Supports keeping a well-tuned U-Net baseline and matching training budgets when comparing models. A residual encoder is a reasonable candidate, not a guaranteed upgrade. Its primary experiments concern 3D segmentation, so only its experimental-design lesson transfers directly to our 2D task.

### S8. Maier-Hein et al. — Metrics Reloaded (2024)

**Source:** *Metrics reloaded: recommendations for image analysis validation*, Nature Methods 21:195–212.

**Links:** [Journal article](https://www.nature.com/articles/s41592-023-02151-z) · [Author manuscript](https://arxiv.org/abs/2206.01653)

**Read:** Journal abstract, accessible figure descriptions and author-manuscript abstract. Full manuscript retrieval exceeded the retrieval size limit.

**Useful finding:** Metric choice must match the task and target properties; image-, object- and pixel-level evaluation are distinct.

**Contribution:** Informs a multi-level evaluation plan: normal-image false positives, fracture-region recall and mask overlap, with explicit empty-mask handling. Detailed metric choices below are our proposed protocol, not a claimed verbatim prescription from this paper.

### S9. Ma et al. — MedSAM (2024)

**Source:** *Segment anything in medical images*, Nature Communications 15:654.

**Link:** [Full article](https://www.nature.com/articles/s41467-024-44824-z)

**Read:** Prompting, architecture, training and evaluation sections.

**Useful finding:** MedSAM is a promptable medical segmentation model; bounding boxes specify targets. It is not an automatic fracture finder simply because it supports medical images.

**Contribution:** Useful as a later refinement/annotation experiment. Evaluate with predicted boxes or openly label human-assisted operation. Ground-truth fracture boxes at test time would provide privileged localization and invalidate comparison with our automatic pipeline. No reviewed result proves a MedSAM benefit for our fracture masks.

### S10. Bishop & Bishop — Deep Learning: Foundations and Concepts (2024 edition)

**Source:** Springer textbook; first published online November 2023, copyright/citation year 2024.

**Links:** [Book](https://www.bishopbook.com/) · [Publisher](https://link.springer.com/book/10.1007/978-3-031-45468-4) · [Gradient Descent](https://link.springer.com/chapter/10.1007/978-3-031-45468-4_7) · [Regularization](https://link.springer.com/chapter/10.1007/978-3-031-45468-4_9) · [Convolutional Networks](https://link.springer.com/chapter/10.1007/978-3-031-45468-4_10)

**Read:** Publisher's two-page previews for these three chapters, not the entire book.

**Contribution:** Reinforces that lower training loss is not the same as better generalization, and gives the conceptual basis for regularization and task-specific image modeling. It supports investigating learning curves and controlled regularization instead of selecting a loss merely because its numerical value is smaller. It contains no MedVision-specific performance evidence.

### S11. Official PyTorch loss documentation (implementation reference)

**Link:** [BCEWithLogitsLoss](https://docs.pytorch.org/docs/stable/generated/torch.nn.BCEWithLogitsLoss.html)

**Read:** Loss definition and numerical-stability explanation. This is documentation, not a dated research paper.

**Contribution:** For new training code, emit raw logits and use BCEWithLogitsLoss directly; apply sigmoid for overlap loss and inference. This avoids converting clipped sigmoid probabilities back into logits. Version and test the changed output contract so existing checkpoints are not silently interpreted incorrectly.

## 4. Proposed next pipeline

### 4.1 Data and target contract

Create a single manifest with image ID, file path, fracture label, all polygons/instances, anatomy/view/hardware fields, native dimensions and split. Build zero masks only for explicitly labeled normals; flag positives without usable annotations for review. Retain instance IDs even if training a binary union mask.

Freeze train/validation/test IDs before augmentation or crop generation. Keep crops and related images together. Use patient/study grouping where reliable identifiers exist; otherwise document that patient independence is unverified and audit duplicates/near duplicates. FracAtlas's supplied fracture-only split and the current custom split are different protocols; report which one is used and how normals are allocated.

Use a balanced positive/normal training sampler as an initial experiment, not a fixed natural prevalence estimate. Include difficult normal regions such as joints and hardware-bearing images when labels permit. Select hard negatives only from training data. Validation/test should retain a documented representative distribution; class rebalancing in training does not justify balanced-test-only accuracy claims.

### 4.2 Detail-preserving preprocessing

A direct check of the 717 COCO records found median width 373 and height 454 pixels; width/height ratios ranged from about 0.40 to 1.74. These are annotation-metadata measurements, not a full image-quality audit. A square stretch changes geometry. Larger source images also lose substantial detail at 256.

Proposed comparison: aspect-preserving resizing plus padding at 256 and 512, with a valid-pixel mask to exclude padding from losses and metrics. Record the exact inverse transform. Compare three preprocessing variants at the chosen size: normalized grayscale; CLAHE without blur; existing CLAHE+blur. This isolates the preprocessing question raised by S2.

Do not assume 1024 is necessary or feasible. Many source images are smaller, and upsampling cannot restore information. Inspect original-versus-model-input crops of small fracture annotations. Measure annotation survival after resizing and positive pixel counts; use nearest-neighbor mask resizing and test polygon-coordinate conversion.

### 4.3 Model and training

Candidate order:

1. Corrected existing Attention U-Net, preserving a comparable baseline.
2. Plain U-Net under the same data/training protocol to measure attention's contribution.
3. A modest pretrained residual-encoder U-Net, with pretraining and normalization explicitly recorded.
4. Optional full-image plus regional refinement only if error analysis shows remaining small-region misses.

For grayscale with an RGB-pretrained encoder, test a documented channel replication or first-layer adaptation; do not silently mix normalization schemes. If high resolution forces tiny batches, compare an appropriate normalization choice while acknowledging checkpoint incompatibility; gradient accumulation does not increase BatchNorm's per-forward sample count.

Start augmentation conservatively: synchronized modest rotations/flips and mild intensity changes. Ablate elastic warps because anatomical plausibility is not guaranteed. Avoid copying detector mosaic/CutMix recipes into fine fracture-mask learning without checking labels and image realism. Fix the fallback augmentation RNG: its unseeded RandomState prevents full reproducibility despite the global seed.

Use a tiny training-subset overfit check to detect learning/label bugs before a full run. Log loss components, learning rate, gradient finiteness, foreground occupancy, and per-epoch precision/recall. Low train and validation performance can reflect underfitting or a representation/label problem; strong training with weak validation suggests a different intervention. Forty epochs alone proves neither adequate nor inadequate training.

### 4.4 Loss and sampling experiment

Compare the current focal Tversky objective against BCEWithLogits+soft Dice and a faithfully implemented Unified Focal variant. Use the same split, resolution, augmentation, seeds and training budget. Initial equal BCE/Dice weighting is a test setting, not a proven optimum. Record each term and tune on validation only.

Explicitly test empty masks. A foreground-overlap-only loss can provide weak suppression gradients on empty targets depending on smoothing/reduction; a pixelwise term is worth testing when normal images are added. Confirm behavior with numerical tests. Avoid simultaneously maximizing positive sampling, BCE weights and FN penalties: that could increase false positives.

Current Tversky formula:

TI = (TP + epsilon) / (TP + 0.7 FN + 0.3 FP + epsilon)

Loss = mean((1 - TI)^0.75)

This already favors recall. The priority is a measured precision/recall trade-off, not a blanket instruction to increase alpha or replace gamma.

### 4.5 Optional region refinement

A candidate two-branch design processes the full image for context and selected high-resolution regions for detail. Proposals can come from a detector or a coarse segmentation model; training can use label-derived crops with jitter, but final evaluation must use predicted proposals.

Keep a full-image fallback or evaluate overlapping tiles so a missed proposal does not silently eliminate all chances to detect a fracture. Report proposal recall and end-to-end region recall separately. Merge overlapping regional probability maps in original coordinates before thresholding. Include false-positive proposals in refinement training.

This architecture is our synthesis of the small-target problem and detection/refinement literature, not a published guarantee for MedVision. Implement it only if its gains justify extra latency and complexity.

### 4.6 Postprocessing, confidence and serving

Restore probability maps to original coordinates, then apply the validation-selected threshold and component policy. Avoid unconditional largest-component selection. Compare no filtering against size/probability-based filtering; a minimum-size rule can remove genuine small fractures.

Separate fields: suspected region present; individual component masks; pixel area; contour perimeter; model/config version; quality warnings; and optional experimental geometric indicator. An empty mask is not Mild. Contour area should not decide whether a mask exists.

Remove 86%/74% confidence. If a case probability is later required, define and validate its derivation, calibration and reliability separately; mean/max pixel probability is not automatically a case probability. Abstention/uncertain output needs a measured policy too.

Load the model once per serving worker, use evaluation/inference mode and bounded job concurrency, and reuse the exact evaluation preprocessing/postprocessing module. These changes improve serving reliability and latency; they do not themselves improve learned segmentation accuracy.

## 5. How we will measure a genuine improvement

“Accuracy” needs three separate definitions:

| Task | Main measurements | Reporting requirement |
|---|---|---|
| Fracture present in the image | Sensitivity, specificity, precision, confusion matrix; PR-AUC/AUROC only with a continuous defined score | Include normals and denominator counts; freeze decision rule on validation |
| Fracture region found | One-to-one matched region recall and false-positive regions/image | Predefine overlap/matching rule and handle multiple instances |
| Mask quality | Per-positive-image Dice/IoU and precision/recall, plus global pixel metrics | Report raw and delivered-mask scores; define empty-ground-truth behavior |
| Generalization | Anatomy/view/hardware/size subgroup results and external data where compatible | Counts and uncertainty; no claims from very small groups |
| Runtime | Warm model latency, full request latency, peak memory | Hardware, image size and batching disclosed |

Normal cases should be reported separately so thousands of empty masks cannot make average overlap look excellent. An all-background model can have high pixel accuracy on sparse targets while finding no fractures; therefore pixel accuracy is not the headline metric.

Choose the primary development metric and acceptable false-positive behavior before experiments. Use validation for tuning, then lock weights, threshold and postprocessing before final test evaluation. Repeat promising comparisons over three seeds if resources permit; a single seed is a preliminary result. Use paired bootstrap intervals over images, or patient/study clusters when available, and state the independence limitation.

Do not optimize repeatedly against the test set. Do not claim gains by comparing different splits or a raw-mask baseline against a refined-mask model without showing both stages. Clinical severity requires separate labels and expert validation; better mask overlap alone does not validate area-based severity.

## 6. Practical experiment sequence

| Experiment | Change | Question answered | Advance only when |
|---|---|---|---|
| E0 | Strict checkpoint load; tiny-set learning check; inverse-transform and mask tests | Is the pipeline functioning correctly? | Outputs, gradients and alignment are correct |
| E1 | Frozen all-image protocol, normals included, corrected output semantics | Does the baseline handle negatives and multiple regions? | Complete baseline metrics and failure gallery exist |
| E2 | 256 vs 512, aspect preserved | Does retaining spatial detail help? | Positive-case improvement does not hide excessive normal false positives |
| E3 | Raw vs CLAHE vs CLAHE+blur | Is preprocessing helping or erasing evidence? | Best variant is repeatable on validation |
| E4 | Three loss choices, sampler fixed | Which loss yields the best intended error trade-off? | Numerical behavior and empty-mask handling verified |
| E5 | Plain vs attention vs pretrained residual U-Net | Is architectural/pretraining complexity worthwhile? | Equal-budget comparison supports it |
| E6 | Predicted-region refinement or overlapping tiles | Are remaining errors resolution-limited? | End-to-end benefit survives proposal errors and latency cost |
| E7 | Threshold/component policy; optional ensemble | Can inference trade-offs improve reliably? | Selection uses validation and complete deployed masks |
| E8 | Locked final evaluation and real API smoke run | Does the shipped pipeline match the evaluated one? | Saved per-case outputs reproduce final report |

Early experiments should isolate one change at a time. Later test interactions between winning settings, especially resolution and preprocessing. Preserve the old checkpoint rather than overwriting it. Save config, environment, split IDs, seed, model hash, training curves, predictions, metrics and runtime in each run folder.

## 7. Code changes mapped to your repository

| Current location | Proposed change | Priority |
|---|---|---|
| FracAtlasZipDataset | Join CSV and COCO; negatives; annotation audit; shared/lazy cache | First |
| preprocess_image / preprocess_image_array | One shared parameterized preprocessing function with inverse transform | First |
| _build_dataset_splits | Persist IDs; grouping/duplicate audit; sampling only in training | First |
| Loss functions / train_model | Logits contract, loss ablations, seeded augmentation and structured logs | Next |
| _evaluate_segmentation_model | Per-case and normal-case metrics; deployed postprocessing; evaluation-only command | First |
| assess_severity | Multi-component handling, empty state, pixel-area/contour distinction | First |
| predict_from_checkpoint | Reusable predictor and model/config/threshold bundle | Next |
| backend_service._result_from_prediction | Remove fabricated confidence; truthful geometric output | First |

## 8. What not to do yet

- Do not replace the entire backend with a transformer because a paper reports a larger percentage.
- Do not add aggressive sharpening, synthetic fracture generation or super-resolution without checking whether they invent misleading patterns.
- Do not train only fracture-centered crops and then evaluate only known fracture locations.
- Do not turn detection boxes into supposedly precise segmentation ground truth without labeling them as weak supervision.
- Do not merge unrelated datasets without aligning tasks, labels, patient groups and evaluation domains.
- Do not describe lower focal-Tversky loss than Dice+BCE as a quality improvement: their scales differ.

## 9. Recommended decision

The most useful immediate references are S1 for data correctness, S2 for preprocessing/detail preservation, S6 for imbalance-aware training, S7 for fair model comparison and S8 for evaluation design. S4 and S5 keep performance interpretation realistic. S9 is a later option; S10 supplies conceptual grounding rather than an accuracy claim.

Begin with E0–E3 using the existing architecture. The strongest current hypothesis is that data coverage, input representation and postprocessing offer more actionable opportunities than an immediate architecture replacement. The size of any benefit remains unknown until the experiments are run.
