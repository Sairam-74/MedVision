# BatchNorm context research — 9 October 2026

BatchNorm is a plausible, unproven contributor to the remaining fit problem. The narrow next diagnostic should compare fixed running statistics with temporary batch statistics on the same previously fixed 32 TRAIN sources. This memo records primary-source research and a read-only implementation review. It contains no newly measured inference results, candidate training, normalization replacement, clinical improvement claim or promise of greater than 90% accuracy.

## Evidence from this project

The existing ConvBlock and AttentionGate use default `BatchNorm2d` in [medvision_ai.py](../../medvision_ai.py). Both completed E13/E14 configurations retain batch size 2. At 256 × 256 input, four pooling stages leave a 16 × 16 bottleneck. Consequently, there are spatial values as well as two images contributing to a channel's batch statistics; describing these statistics as calculated from only two scalar observations would be inaccurate. Their effective independence is not established by these dimensions.

The completed [TRAIN fit comparison](../AI_FOREGROUND_BCE_FIT_PAIR_E13_E14_20261009/TRAIN_FOREGROUND_BCE_FIT_PAIR.md) reports hard-positive mean grid Dice 0.139391 → 0.134691 and any-GT overlap 44/109 → 39/109 for E13 → E14, while ordinary-positive Dice improves 0.495670 → 0.530537. This establishes persistent poor fit on the reused hard TRAIN group. It does not identify normalization as the cause. The selected checkpoints also differ in global epoch, 45 versus 50. Annotation limitations, sparse targets, preprocessing, optimization and learned representations remain competing explanations.

This continues preserved earlier work. The corrected [E5 unaugmented diagnostic completion](../AI_BATCHNORM_CONTEXT_E5_v3_unaugmented/completion.json) records the same 16 TRAIN examples: stored-statistics mean positive grid Dice 0.156347; current-input batch 1, 0.142621; current-input batch 2, 0.173859. Stored-statistics outputs were exactly equal between batch sizes, while current-input modes changed three/two case decisions. Thus the earlier result did not establish a reliably superior batch-statistic inference policy. The [session record](SESSION_PROGRESS.md) explicitly corrects the first diagnostic's augmentation metadata: `CachedReliabilityDataset.__getitem__` still augmented examples, so those earlier outputs are retained as augmented-only. The corrected run accesses immutable raw cache arrays. Neither earlier run is a trained candidate or validation result.

The existing [loss/BatchNorm research record](RESEARCH_LOSS_BATCHNORM_20261007.md) is retained. The present investigation checks materially later selected E13/E14 models after intervening hard-example and loss experiments; it is not a repeated baseline or a reason to discard the prior negative/mixed evidence.

## Primary sources consulted

### Batch Normalization: Accelerating Deep Network Training by Reducing Internal Covariate Shift

- Authors/year/source: Sergey Ioffe and Christian Szegedy, 2015, ICML/PMLR 37:448–456. [Proceedings and original paper](https://proceedings.mlr.press/v37/ioffe15.html), [PDF](https://proceedings.mlr.press/v37/ioffe15.pdf).
- Problem/method: the authors frame changing layer-input distributions as an optimization difficulty. BN normalizes training minibatches and learns scale/shift; its inference procedure uses fixed population estimates rather than the current test batch.
- Datasets/result: MNIST and ImageNet. The ImageNet experiment reached comparable accuracy with 14 times fewer training steps; its reported ensemble top-5 test error was 4.82%.
- Project insight: training and evaluation intentionally use different statistical contexts. A frozen-context comparison can investigate their effect without learning new weights.
- Limitations: these are the authors' results on different tasks. Their causal framing and numerical gains do not establish the explanation for this fracture model or expected clinical benefit.

### Group Normalization

- Authors/year/source: Yuxin Wu and Kaiming He, 2018, ECCV, pp. 3–19. [Original proceedings PDF](https://www.ecva.net/papers/eccv_2018/papers_ECCV/papers/Yuxin_Wu_Group_Normalization_ECCV_2018_paper.pdf).
- Problem/method: small per-worker batches can impair BN; GN computes statistics within channel groups of each image without using other batch members.
- Datasets/result: ImageNet, COCO and Kinetics. Table 2 reports ImageNet ResNet-50 top-1 validation error at two images per worker: BN 34.7%, GN 24.1%, a **10.6 percentage-point** difference. At 32 images, BN 23.6% and GN 24.1%. Evaluation uses 224 × 224 center crops and median error over the final five epochs.
- Project insight: batch size 2 warrants investigating statistical context before considering a separately controlled normalization experiment.
- Limitations: GN was not universally better. Different architecture, data, training and normalization axes prevent extrapolating these gains to fracture detection or converting existing BN weights into a proven GN model.

### Rethinking "Batch" in BatchNorm — previously recorded, primary source rechecked

- Authors/year/source: Yuxin Wu and Justin Johnson, 2021, author technical report. [Original preprint](https://arxiv.org/abs/2105.07576), [full PDF](https://arxiv.org/pdf/2105.07576).
- Problem/method: examines normalization-batch construction, exponential moving averages and population-statistic estimation; PreciseBN aggregates statistics under fixed weights.
- Dataset/result: ImageNet ResNet-50, among other visual-recognition experiments. Table 2 uses 10,000 samples: for a model trained with normalization batch size 2, EMA error is 35.5%, whereas sufficiently large PreciseBN forwarding batches yield 32.0%. Small forwarding batches remain worse. These are top-1 validation errors, not fracture accuracies.
- Project insight: distinguish running-statistic quality from training optimization and from using the current patient's batch. Recomputing fixed population statistics is a different intervention from the temporary no-buffer-update diagnostic.
- Limitations: nonmedical tasks and different data/architecture; no transferable gain. The paper also explains that arbitrary minibatch inference loses independent predictions. No population-statistic fitting or PreciseBN candidate is performed here.

### BatchNorm2d — official PyTorch documentation

- Authors/year/source: PyTorch Contributors; version 2.9 documentation, accessed 9 October 2026; no publication year asserted. [Official API documentation](https://docs.pytorch.org/docs/2.9/generated/torch.nn.BatchNorm2d.html).
- Problem/method: specifies NCHW normalization, channel-wise statistics over N/H/W, running estimates and affine parameters. Default tracking uses running estimates at evaluation; constructing with tracking disabled creates absent statistics buffers. BN momentum controls averaging, separately from optimizer momentum.
- Dataset/result: software contract, not an empirical fracture study; no clinical metrics.
- Project insight: distinguish statistical mode from gradient recording and verify the existing buffers before changing flags.
- Limitations: generic API behavior supplies implementation guidance, not evidence that small batches caused this checkpoint's failures.

### _BatchNorm.forward — official PyTorch v2.9.1 implementation

- Authors/year/source: PyTorch Contributors; pinned v2.9.1 source, accessed 9 October 2026. [Official repository source](https://raw.githubusercontent.com/pytorch/pytorch/v2.9.1/torch/nn/modules/batchnorm.py).
- Problem/method/result: inspect the actual branches governing batch statistics, buffer arguments and the batch counter; no dataset or empirical gain.
- Project insight: with an already loaded module's non-null running buffers, changing tracking alone while leaving evaluation mode still uses those buffers. The temporary diagnostic requires **both** `training=True` and `track_running_stats=False` on each BN2d. This uses batch statistics without passing running buffers or incrementing the counter. Momentum zero alone still permits counter changes.
- Limitations: this is a version-specific software contract, not an acceptance test for a medical model.

### Module and inference_mode — official PyTorch documentation

- Authors/year/source: PyTorch Contributors; version 2.9 documentation, accessed 9 October 2026. [Module](https://docs.pytorch.org/docs/2.9/generated/torch.nn.Module.html), [inference_mode](https://docs.pytorch.org/docs/2.9/generated/torch.autograd.grad_mode.inference_mode.html).
- Problem/method: module mode and gradient recording are distinct. Evaluation changes modules such as BN/dropout; inference mode suppresses autograd work and has restrictions on subsequent autograd use of its tensors.
- Dataset/result: software behavior, without experimental clinical results.
- Project insight: keep non-BN modules in evaluation mode; use inference mode only for this read-only diagnostic and metric calculation. It does not independently prevent a training-mode BN from modifying tracked buffers.
- Limitations: disabling gradients alone is insufficient protection; saved state and flags must be checked independently.

## Temporary flags and restoration requirements

Use an isolated strict-loaded copy of each selected checkpoint. Put that copy in evaluation mode before capturing its baseline. Capture all module training flags and BN tracking flags, plus BN configuration (`eps`, `momentum`, `affine`, `num_features`). Retain exact parameter/buffer digests and explicit counter values. Only the two BN flags above should temporarily change. Do not call whole-model `train()`, reset statistics, replace buffers, run an optimizer or write a new checkpoint.

For each temporary context, an inner `try/finally` restores BN flags even if a forward or metric calculation fails. An outer `finally` protects the entire diagnostic. Restoring captured training flags by direct assignment avoids recursive restoration changing child-specific flags. Non-BN modules remain at their recorded evaluation setting. Exact before/after tensor digests must include affine parameters, running mean, running variance and `num_batches_tracked`; independently verify metadata and all flags. All parameter gradients must remain absent. These are protection requirements for this diagnostic, not a proposed production policy.

The implementation detail was checked against the pinned [official BN forward source](https://raw.githubusercontent.com/pytorch/pytorch/v2.9.1/torch/nn/modules/batchnorm.py); the separation of mode, buffers and autograd is documented by [Module](https://docs.pytorch.org/docs/2.9/generated/torch.nn.Module.html) and [inference_mode](https://docs.pytorch.org/docs/2.9/generated/torch.autograd.grad_mode.inference_mode.html).

## Read-only review of the proposed diagnostic

[audit_ai_batchnorm_context_completed_pair.py](../../tools/audit_ai_batchnorm_context_completed_pair.py) was read without executing it. At the reviewed revision, the fixed 32 unique TRAIN sources comprise eight each of hard positive, ordinary positive, hard negative and ordinary negative. Cached images/targets/validity maps are read-only and byte-verified. Each anchor is paired with four distinct-source companion choices, one from each stratum. Running-statistics evaluation is repeated with two companions to detect numerical or implementation dependence in the control.

The planned count is 2 checkpoints × 32 anchors × (2 running-statistic forwards + 4 temporary batch-statistic forwards) = **384 forwards / 768 source presentations**, involving only **32 unique sources**. Repeated presentations must not be described as independent observations. No augmentation, optimizer, backpropagation, validation/calibration/test image reads, new checkpoint or factor selection occurs. The tool verifies its own/input/old guard hashes, the TRAIN cache bytes, model state digests, absent gradients and BN flag restoration.

No blocking forward/restoration defect was found. The root incorporated the review's recording improvements before execution: the completed queue JSON is bound in before/after input hashes, changed-mask pixel counts intersect validity and are labeled accordingly, and all module training flags plus BN `eps`/`momentum` are checked unchanged. These revised sections were independently read back. Reviewed tool SHA-256: `04d48e8f5cbdf044e4689aa4f237a1816e0e5d1cf0c89acfc28aa82836123009`. The separate completed-diagnostic analysis will report actual outputs; the paper results above remain literature findings only.

## Interpretation boundaries

If batch-statistic context changes foreground probabilities or overlap, that demonstrates a **checkpoint/context interaction on selected TRAIN cases**. Even consistent improvement would not establish primary causation, population performance, reduced native false negatives or robust localization. If it remains poor in both contexts, running-statistic mismatch becomes a weaker sole explanation; the diagnostic still cannot rule out the effects BN had during past training.

If an anchor's result changes with an unrelated companion image, that is evidence of context dependence. It is not a deployable radiologist-assistance result: unrelated patient batching should not silently change an image's fracture region or confidence. The procedure is neither calibrated case probability nor a multi-view study-combination method. Its companions are diagnostic controls, not additional views of the same patient.

Per-batch BN also differs from GN's per-image channel-group statistics. Changing inference context does not train or evaluate a GN candidate. Any future normalization change requires its own registered single-factor comparison, complete training, native validation/error review and acceptance gates; no such factor is selected here. The selected 32 TRAIN examples are exploratory and reused, not a held-out difficult-case benchmark. No locked-test claim, clinical subtype attribution, radiologist agreement or greater-than-90% accuracy claim follows from this research.

Document scope: primary-source browsing, saved text/metadata inspection and read-only tool review only. No inference, model tensor loads, CUDA execution, calibration/test access, production or dataset changes were conducted by this research task.
