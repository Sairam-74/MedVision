# Completed E13/E14 BatchNorm context diagnosis — 9 October 2026

Temporary batch-statistic inference did **not** produce consistent hard-target recovery and should not be adopted as an inference policy. It changed results with unrelated companion images. This is a negative/mixed diagnostic finding, not proof that BatchNorm causes the remaining errors or that GroupNorm would improve them.

## Scope and independent verification

The root executed [AI_BATCHNORM_CONTEXT_E13_E14_20261009](../AI_BATCHNORM_CONTEXT_E13_E14_20261009/completion.json) on CUDA. This independent analysis reads saved JSON and streams files for hashes only: no images, target arrays, checkpoint tensors or new inference were loaded here.

- Both selected checkpoints: E13 additional epoch 6/global 45; E14 additional epoch 11/global 50. This is not a same-epoch controlled training experiment.
- Exactly the same previously fixed 32 unique TRAIN sources, eight per hard-positive/ordinary-positive/hard-negative/ordinary-negative stratum; 64 ordered anchor records across two checkpoints. Sample identities/order match the earlier frozen diagnostic configuration and cached TRAIN rows. Positive grid target presence and target areas agree across contexts.
- 384 forwards and 768 repeated source presentations, not 768 independent images. Each anchor has two running-statistic controls and four temporary batch-statistic contexts with distinct-source companions.
- Independently rehashed all six recorded sources, all 16 recorded input files, and the three completion-bound output files. These include the queue JSON, selected checkpoint bytes, manifest, TRAIN row metadata and cache completion. All matched.
- The root's completion records all 189 old guards reverified, exact parameter/buffer digests unchanged, 26 BN modules per checkpoint restored, all module mode flags/BN eps/momentum unchanged, and gradients absent. This analysis verifies those saved assertions and digest equality; it does not reread model tensors or rerun every old guard.
- No augmentation, optimizer, new checkpoint, promotion or validation/calibration/test image reads. Saved execution duration: 24.797775 seconds for this diagnostic; this is not a deployment inference-latency benchmark.

## Hard-positive results: same eight TRAIN anchors

Companion labels specify the companion's sampling stratum, not the anchor's label. Dice/IoU are threshold-0.5 grid measurements. Any GT overlap is only a minimal overlap check, not adequate localization.

| Checkpoint | Statistical context / companion | Mean Dice | Mean IoU | Any GT overlap / 8 | Alerts / 8 | Global target pixel recall |
| --- | --- | --- | --- | --- | --- | --- |
| E13 | Running statistics | 0.180245 | 0.131744 | 5 | 5 | 0.121331 |
| E13 | Batch / hard positive | 0.151144 | 0.104360 | 3 | 6 | 0.111668 |
| E13 | Batch / ordinary positive | 0.159027 | 0.110677 | 5 | 6 | 0.115963 |
| E13 | Batch / hard negative | 0.231159 | 0.177005 | 5 | 8 | 0.153901 |
| E13 | Batch / ordinary negative | 0.233049 | 0.177259 | 5 | 8 | 0.147817 |
| E14 | Running statistics | 0.135713 | 0.093271 | 3 | 5 | 0.094846 |
| E14 | Batch / hard positive | 0.157357 | 0.113207 | 3 | 6 | 0.100215 |
| E14 | Batch / ordinary positive | 0.100419 | 0.078338 | 2 | 6 | 0.053686 |
| E14 | Batch / hard negative | 0.127882 | 0.096941 | 3 | 6 | 0.070508 |
| E14 | Batch / ordinary negative | 0.153892 | 0.113813 | 3 | 5 | 0.098783 |

For E14, no companion stratum increases the aggregate number of hard anchors with any GT overlap above 3/8. Three contexts increase alerts to 6/8 without useful aggregate target recovery. Target pixel recall stays approximately 5.4–10.0%. E13 has two contexts with better Dice, but neither increases its any-GT count above 5/8, and both increase alerts to all eight hard-positive cases. These improvements do not establish balanced reliability.

## Positive segmentation and normal alert burden together

The positive means below combine eight hard and eight ordinary positive anchors. Normal alerts combine eight hard and eight ordinary negatives. They are descriptive on the fixed balanced sample and are not prevalence-weighted population estimates.

| Checkpoint | Statistical context / companion | Mean positive Dice / IoU | Positive any GT / 16 | Positive alerts / 16 | Normal alerts / 16 |
| --- | --- | --- | --- | --- | --- |
| E13 | Running statistics | 0.361566 / 0.261480 | 13 | 13 | 12 |
| E13 | Batch / hard positive | 0.296231 / 0.205636 | 11 | 14 | 16 |
| E13 | Batch / ordinary positive | 0.323569 / 0.233763 | 12 | 13 | 13 |
| E13 | Batch / hard negative | 0.345128 / 0.249974 | 13 | 16 | 16 |
| E13 | Batch / ordinary negative | 0.388231 / 0.283651 | 13 | 16 | 15 |
| E14 | Running statistics | 0.305580 / 0.223935 | 10 | 12 | 10 |
| E14 | Batch / hard positive | 0.301093 / 0.218250 | 11 | 14 | 14 |
| E14 | Batch / ordinary positive | 0.270080 / 0.200639 | 8 | 12 | 8 |
| E14 | Batch / hard negative | 0.309323 / 0.226069 | 11 | 14 | 11 |
| E14 | Batch / ordinary negative | 0.342090 / 0.253290 | 11 | 13 | 13 |

The E14 ordinary-positive companion reduces normal alerts from 10 to 8 but also reduces positive overlap from 10 to 8 and positive Dice. Its other contexts increase normal alerts while failing to repair the hard-positive overlap count. The E13 best sampled positive Dice occurs with increased normal alerts, 12 → 15. No context supplies consistent target recovery and reduced normal marking together.

## Companion dependence and denominator clarification

Running-statistic controls are exactly equal with the two different companions: saved maximum absolute logit difference is zero and changed valid-mask pixel count is zero for all 64 anchor records. Temporary batch statistics show substantial context dependence.

| Checkpoint | Unique anchors with an alert different from eval in any context / 32 | Unique anchors whose alert varies between the four companions / 32 | Alert flips across all 128 anchor/context comparisons | Anchors whose any-GT decision varies between companions / 32 |
| --- | --- | --- | --- | --- |
| E13 | 12 | 8 | 29 | 3 |
| E14 | 12 | 11 | 23 | 4 |

These counts were independently recomputed from `per_case.json`. An earlier informal E14 count of 16/32 alert changes is not supported by the saved fields; neither the unique-anchor nor case/context denominator yields that number. The checked values above supersede that wording. Different companion strata are not repeated independent patient cohorts, and their output ranges must not become a tuned selection rule.

## Continuity, decision and limitations

The corrected [E5 unaugmented diagnostic](../AI_BATCHNORM_CONTEXT_E5_v3_unaugmented/completion.json) previously showed mixed batch-statistic changes: positive Dice 0.156347 with running statistics versus 0.142621/0.173859 with batch 1/2. Earlier mislabeled augmented checks remain preserved and explicitly corrected in [SESSION_PROGRESS.md](SESSION_PROGRESS.md). The later E13/E14 probe checks substantially changed weights after further training; it does not erase or repeat that earlier baseline. Primary sources, exact flags and restoration requirements are recorded in [BN_CONTEXT_RESEARCH_20261009.md](BN_CONTEXT_RESEARCH_20261009.md).

Decision: **reject adopting temporary batch-statistic inference on this evidence**. Keep the existing evaluation semantics. No normalization candidate is trained or selected by this diagnostic. BatchNorm remains an unproven contributor; poor hard-positive fit persists even when current-batch statistics are used. This weakens a simple running-statistic-mismatch explanation without ruling out historical training effects or other interactions. A GroupNorm, frozen-BN or population-statistic candidate would be a different controlled experiment requiring separate evidence.

This sample cannot establish native localization, clinical accuracy, calibrated fracture probabilities, performance on subtle/nondisplaced fractures, radiologist agreement, external generalization or locked-test acceptance. It contains reused exploratory TRAIN cases and no clinical adjudication. No 90% claim or production promotion is warranted.

## Artifact bindings

| Artifact | SHA-256 |
| --- | --- |
| Diagnostic source | `04d48e8f5cbdf044e4689aa4f237a1816e0e5d1cf0c89acfc28aa82836123009` |
| Config | `b6235bd096a174e2c29377d7f7aa51469ec77e4f1f73ac676b7c1b2351944859` |
| Per-case JSON | `3b214e4ea3f15a7fef1884d40de1e52d791fd276b34c780108e08d8fd48c258f` |
| Summary JSON | `b7c232a09eb03fdc1ef73b61365f5db02528a62ad0ba15e9728ed1c30ebecaf2` |
| Completion JSON | `8e49474ab93210e0d1fac8401599b533755ce31c6bd1666889ad7f7fc40a83d6` |
| E13 model state before and after | `c40f72404b42020abcf79359ad3aec970a21b957689d8587977c4692a2ecd19d` |
| E14 model state before and after | `56d3d964dc5d6b2284fce42138c0d8f6a96c3984db4ecb862e5a4de0d5b02baa` |

Checkpoint file-byte hashes and state-dictionary tensor digests are different quantities; the table's last two rows are the latter, as saved by the executed diagnostic.
