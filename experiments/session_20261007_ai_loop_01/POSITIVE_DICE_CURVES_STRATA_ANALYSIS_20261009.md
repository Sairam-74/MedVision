# Completed E11/E12 positive Dice experiment: curves and technical strata

Created 9 October 2026 UTC from completed saved evidence. **Reject coefficient2 as balanced overall improvement at the registered operating point.** Against its matched coefficient1 continuation control, selected E12 adds three missed fracture cases and 12 normal alerts, worsens calibration diagnostics and instance localization, and fails all classification/positive-overlap target gates. More recovered fracture pixels and a small macro Dice increase do not compensate for these regressions.

No next intervention is selected here. Root/team are reviewing actual X-rays, GT and predicted masks separately; this analysis reads saved metadata and curves, not images. Production, original checkpoints, dataset, CAL/test and operating policy remain untouched by this work.

## Completed matched experiment and independent verification

E11 and E12 each completed 12 additional epochs, global31–42, from the same selected full E10/global30 model and Adam snapshot. Independently compared every configuration field: **the sole difference is positive-case Dice coefficient1 versus2**. BCE for all images, normal Dice, hard factor2, presence weight0, batch2, LR1e-4, seed42, optimizer state, no scheduler/weight decay, norm clipping10, source code, preprocessing, source weights, natural unique sampling, epoch seed schedule and common model-selection rule match. The training source resets seed42+global_epoch and uses the same DataLoader generator and dataset epoch in both arms.

Initial parameter metadata and full model/Adam snapshot file hashes match; the completed TRAIN-only smoke records exact coefficient1/original-loss parity and matched Adam initialization. This independent analysis hashes checkpoint bytes and reads recorded digests; it does not unpickle tensors or independently inspect Adam moments. Both arms retain the same scratch-origin AttentionUNet64PresenceGAP branch, with 31,388,070 parameters and BatchNorm layers. No transfer initialization is part of this experiment.

Verified all 463 native VAL IDs/labels/source archive members/groups/shapes/GT areas/annotation counts/flags against the frozen manifest: 83 positive,380 normal,422 conservative related groups. Verified all 2,808 unaugmented TRAIN grid-fit IDs/labels/groups/GT areas plus all cache source metadata and recorded image/decoded hashes:493 positive,2,315 normal. Each training epoch sees all2,808 unique sources. Current source hashes and native audit snapshots match their records. Completed audit/checkpoint hashes, recomputed aggregates and error transitions match the saved native pair. The independently completed TRAIN-pair helper's hashes, hard/ordinary summaries and pixel counts also match this analysis.

This is the registered coefficient comparison under the same initialization and selection strategy for one seed. Selected E11 is epoch9/global39; selected E12 is epoch3/global33. Thus selected-model differences estimate this strategy's result, not a same-epoch tensor effect or general clinical causal effect. The separate [E11 continuation report](E11_REFERENCE_INTERIM_ANALYSIS_20261008.md) compares E10/global30 with continued coefficient1; that improvement must not be attributed to coefficient2.

## Selected native VAL results

| Metric | E11 coefficient1 | E12 coefficient2 | Candidate minus reference |
|---|---:|---:|---:|
| TP / FN / TN / FP |67 /16 /241 /139|64 /19 /229 /151|−3 /+3 /−12 /+12|
| Accuracy |66.52%|63.28%|−3.24 pp|
| Precision |32.52%|29.77%|−2.76 pp|
| Sensitivity |80.72%|77.11%|−3.61 pp|
| Specificity |63.42%|60.26%|−3.16 pp|
| F1 |0.46367|0.42953|−0.03414|
| AUROC |0.80736|0.80165|−0.00571|
| Average precision |0.56410|0.60516|+0.04106|
| FPR / FNR |36.58% /19.28%|39.74% /22.89%|+3.16 /+3.61 pp|
| Positive macro Dice |0.37511|0.38332|+0.00821|
| Positive macro IoU |0.28417|0.28468|+0.00051|
| Mean positive precision, nonempty |0.61517|0.57946|−0.03571|
| Mean positive recall |0.38429|0.41531|+0.03102|
| Global pixel precision |0.31938|0.35048|+0.03110|
| Global pixel recall |0.22713|0.34629|+0.11916|
| Global Dice / IoU |0.26547 /0.15305|0.34837 /0.21092|+0.08290 /+0.05788|
| Native pixel TP / FP / FN |89,063 /189,799 /303,064|135,788 /251,647 /256,339|+46,725 /+61,848 /−46,725|
| IoU0.5 mask-instance matches /99 |30|26|−4|
| IoU0.5 instance precision / recall |0.10714 /0.30303|0.08280 /0.26263|−0.02434 /−0.04040|
| Component-box AP0.5 / AP0.5:0.95 |0.18935 /0.06662|0.15224 /0.06206|−0.03711 /−0.00456|
| Proxy Brier |0.27452|0.29269|+0.01817, worse|
| Proxy ECE |0.28046|0.31182|+0.03135, worse|

Classification is independent mask presence, not proof of fracture localization. Component-box AP uses connected-component enclosing boxes against polygon enclosing boxes, max-pixel component confidence and101-point interpolation; it is not canonical COCO mAP or a separate detection head. Actual mask-instance matching is a distinct measure. At loose IoU0.1, matches rise53→55, while IoU0.5 matches fall30→26; looser overlap is not improved adequate localization.

Confidence is an uncalibrated maximum-pixel proxy. Among E12's139 scores≥0.9, average score0.9710 contrasts with observed fracture fraction41.73%; this is not trustworthy90% clinical confidence. Reliability-bin data are preserved in DATA. No threshold optimization or calibration fit is performed here.

The original model on the same463 IDs has TP83/FN0, positive Dice0.50380, IoU0.37757, mask-instance recall35/99 and useful pixel recall0.73024. E12's fewer normal alerts than original do not establish overall improvement: case sensitivity, positive overlap and useful coverage are substantially worse. The frozen gates require TP≥79/TN≥342, positive Dice≥0.52379656 and IoU>0.37756859 with localization and coverage retained. Selected E12 fails the classification counts, Dice, IoU and instance-recall gates; FP pixels also rise against its matched control. Accuracy>90%, sensitivity≈95.2% and specificity≥90% are not achieved.

## All12 matched epoch curves

Every epoch pair uses the same global epoch and seed. The candidate objective includes an added positive Dice term, so raw loss scales cannot be compared across arms as a quality metric. Within-arm decreases and the saved base-Dice component remain useful diagnostics; all loss components, bootstrap intervals, pixel recall, selection keys and memory/wall values are in DATA.

| Global | E11 loss | E12 loss | E11 TP / TN | E12 TP / TN | E11 Dice / IoU | E12 Dice / IoU |
|---|---:|---:|---:|---:|---:|---:|
|31|0.954861|1.080242|76 /101|66 /191|0.38018 /0.27598|0.35214 /0.26019|
|32|0.954268|1.072957|74 /153|74 /162|0.39846 /0.28880|0.41543 /0.31412|
|33, E12 selected|0.953798|1.074662|79 /129|64 /229|0.41585 /0.30380|0.38332 /0.28468|
|34|0.951565|1.071464|73 /154|74 /77|0.41224 /0.30678|0.37453 /0.27703|
|35|0.953275|1.070703|76 /89|77 /88|0.40946 /0.29965|0.43575 /0.31249|
|36|0.952278|1.067756|74 /155|79 /79|0.45250 /0.33456|0.44431 /0.32165|
|37|0.952054|1.069699|77 /141|76 /155|0.45597 /0.34120|0.44805 /0.33319|
|38|0.948157|1.062042|72 /117|74 /105|0.42825 /0.32040|0.39888 /0.28570|
|39, E11 selected|0.947942|1.064178|67 /241|66 /207|0.37511 /0.28417|0.42755 /0.33510|
|40|0.948492|1.060564|78 /120|80 /106|0.45980 /0.34291|0.43245 /0.31861|
|41|0.946935|1.057759|72 /143|71 /194|0.43767 /0.33019|0.42900 /0.32165|
|42|0.947817|1.058417|75 /141|74 /112|0.44503 /0.33432|0.42252 /0.30651|

E11 total loss decreases0.95486→0.94782, E12's own objective1.08024→1.05842; recovered base-Dice loss falls approximately0.94610→0.93941 and0.94720→0.93644 respectively. There is continued learning and marked sensitivity/specificity/coverage variation, not a demonstrated plateau. E11 reaches its maximum Dice at global40; E12 at global37, both later than selected checkpoints. No epoch in either arm passes the joint gates. At global40 E12 attains TP80, but TN106 means normal specificity only27.89%.

Native/fit configs and trainer reproduction use CUDA. CPU timing prose in both audit artifacts is stale. E11 native median forward41.20ms/pipeline98.33ms versus E12 27.66ms/63.21ms reflects non-isolated conditions and cannot establish a speedup. E11 epoch6 includes the previously recorded8,637s nominal manual standby; E12 epoch8 has a530.13s wall outlier. Do not compare the full-run wall times as matched GPU throughput.

## Exact error transitions and coverage

Native normal alerts:51 E11 FPs recover,63 new FPs appear,88 persist. Fractures:seven E11 FNs recover,10 new FNs appear,nine persist. Across83 positives,21 Dice gains>0.02 and31 losses>0.02 coexist with the small positive average change. Seven positives lose all useful overlap and three regain some; this includes empty masks. The saved native pair's single new wrong-region case refers to a **nonempty** new zero-overlap mask, a narrower definition. The DATA file preserves IDs for both case and overlap transitions.

E12 has19 empty positives and seven nonempty masks wholly outside GT, so only57/83 positives have any GT overlap; E11 has61/83. Under-segmentation tags24→21 and over-segmentation14→14 do not offset empty misses16→19 or mislocalization6→7. Tags can overlap and are threshold-based technical mask errors, not expert causes.

## TRAIN hard-case fit and technical strata

The independent raw TRAIN grid comparison shows overall positive Dice0.37435→0.37179, IoU0.28111→0.27939, case FN101→95 and normal FP805→896. Grid pixel recall0.32683→0.33448 is a small gain with FP pixels120,564→135,077. TRAIN grid fit is neither native acceptance nor generalization evidence.

| Frozen TRAIN stratum | E11 | E12 |
|---|---:|---:|
|Hard positive109: Dice / IoU|0.07414 /0.05005|0.05370 /0.03611|
|Hard positive: any useful overlap / zero overlap|24 /85|22 /87|
|Hard positive: empty / nonempty wrong region|45 /40|52 /35|
|Hard positive: useful pixel recall|0.07005|0.05241|
|Hard positive: TP / FP / FN pixels|1,668 /6,034 /22,145|1,248 /8,596 /22,565|
|Ordinary positive384: Dice / IoU|0.45957 /0.34670|0.46208 /0.34845|
|Ordinary positive: any useful overlap / zero overlap|310 /74|316 /68|
|Hard normal713: FP / TN|434 /279|411 /302|
|Ordinary normal1,602: FP / TN|371 /1,231|485 /1,117|

Hard-normal rejection improves by23 cases, but ordinary-normal alerts increase114. Hard positives lose two useful-overlap cases and gain seven empty masks;14 empty cases recover but21 new empty cases appear. Their Dice<0.2 count rises92→97. Hard109/713 were chosen using historical E7/E8 TRAIN failures: this is a deliberately enriched training diagnostic, not an independent difficult clinical test.

Anatomy/view/quality flags overlap and may describe composite images. Frontal must not be renamed AP. Small-area cutoff0.0020550129324089714 is fixed from TRAIN native-mask area fraction; multiple annotations and small regions are not clinical subtle/nondisplaced labels. Each group's exact counts, IoU, pixel coverage and transitions are in DATA.

| Native VAL flag | Positive / normal | TP E11→E12 | FP E11→E12 | Dice E11→E12 |
|---|---:|---:|---:|---:|
|Hand|63 /118|53→49|57→50|0.43337→0.40846|
|Leg|18 /237|12→12|74→90|0.20023→0.28388|
|Hip|4 /29|4→4|9→15|0.33635→0.33856|
|Shoulder|7 /31|3→5|11→7|0.09601→0.27963|
|Mixed|9 /34|5→6|12→11|0.19880→0.25984|
|Hardware|7 /1|4→6|0→1|0.09407→0.23835|
|Multiscan|9 /37|6→4|19→14|0.18954→0.20677|
|Frontal|51 /246|41→37|95→101|0.34857→0.37455|
|Lateral|39 /122|31→30|48→54|0.37402→0.37597|
|Oblique|5 /37|2→3|13→10|0.12602→0.11397|
|Small region|12 /0|10→10|—|0.37644→0.33699|
|Larger positive region|71 /0|57→54|—|0.37489→0.39115|
|Multiple annotations|16 /0|13→10|—|0.39737→0.38475|

Small12 have exactly eight useful-overlap cases in each arm despite10 case alerts. Their pixel recall rises0.35810→0.76643 while macro overlap worsens; larger71 overlap cases fall53→49 and misses14→17. Multiple-annotation pixel recall rises0.18644→0.73707 but case misses increase3→6. Coverage pooled over larger GT areas cannot replace per-case and per-instance reliability.

## What the evidence does and does not identify

**Resolution remains plausible, not proven.** Hard109 targets are enriched for smaller areas:256-grid median131 pixels versus249.5 for ordinary384; native-small56/109 versus68/384. Their grid range40–1,774 pixels includes substantially larger targets. The saved geometry audit preserves every positive image and annotation instance at256, and TRAIN label round-trip Dice improves0.92615→0.96154 at512 (VAL0.93114→0.96420). This measures label geometry, not retained X-ray fracture detail or an actual model gain.

Within TRAIN, hard-small56 Dice0.03883→0.04220 but zero overlap49→51; hard-larger53 Dice0.11144→0.06584 with36 zero-overlap cases in both arms. Ordinary-small68 achieve Dice0.47602→0.44162 under the same256 conversion. Area alone cannot explain the extreme hard-set failure. Native VAL misses and coverage failures span smaller and larger masks; no clinical subtlety or nondisplacement cause can be inferred from these fields.

**Foreground optimization/representation remains unresolved.** Poor hard-positive TRAIN fit rules out an explanation based solely on validation domain shift. The extra positive Dice coefficient did not resolve it; network responses also worsened on ordinary normals despite unchanged normal supervision. Nominal batch2 with493/2,808 positives means two uniform distinct sources are both normal with probability67.96%; that is sampling context, not a measured batch log or proof of deficient gradients. Loss scalar magnitudes do not establish gradient competition. Earlier presence-head gradient ratios do not diagnose these presence-weight0 runs.

**LR, BatchNorm and initialization have not been isolated.** Both use the same LR/Adam/scratch-origin architecture; later overlap/loss improvement contradicts a claimed settled plateau. BatchNorm at batch2 is observed in source, but the earlier project probe had mixed results and does not establish a cause or justify changing inference statistics. A compatible pretrained initialization has not been compared. Changing encoder, normalization, LR, sampling and resolution together would prevent interpretation.

The existing [primary-source research memo](RESEARCH_SPARSE_FRACTURE_20261008.md) supplies separable loss/exposure/initialization hypotheses and explicit full-text access limits; no new paper access, external data or weight download occurs here. Published nnU-Net or transfer results do not transfer numerically to this fracture task. Actual completed E12 mask review, the paired TRAIN-fit evidence and hardware feasibility must be integrated before choosing one registered next factor. This report identifies unresolved mechanisms and requests no new intervention.

## Reproducibility and limits

Full checks, both configurations, all24 epoch records, strata, same-ID transition lists and current/input/snapshot hashes are in [DATA](POSITIVE_DICE_CURVES_STRATA_ANALYSIS_20261009_DATA.json), SHA256`8aef75c97fa4cc659a6a33c06eb126db4805f9acca4e3cb9c39668b3bca322f9`.

- Manifest:`4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318`; protocol:`4685bbe07f9a9c9b0690645692882198c3ba2f01a5a9482ef30027450618344c`.
- Full initializer:`655c2ddf756989e30bf1cdb070076af05cb544c88a435b4bd93909e85edbc7b6`; recorded initial parameter digest:`dbd1d7298b3d2ef0775eacbe926daa30697616adbdc7f3276ddb6397f57d03f4`; recorded smoke Adam digest:`2dfbaf6909f6685833c0bd4117ab269ca1f56e4b694eb3e0ddae184092f5635d`.
- E11 selected weights:`c1703d13e5b4cdf35b600c48825ec93c3394570ab1df44d20e9a06b41abc2b84`; E12:`c93ca3b3143cf3a096c72905f211d24ca8bd93fa871c93c15fbd4ce774c4904c`.
- Native comparison:`ba7cfe88be4e50e514d89ec5bf5020e6355a95a073b3f98bbceebc49c08c8061`; independent TRAIN-helper analysis:`66d5cc3ab8120d6e53027af92f4962c65d985ad0a2d4efbd0a03da3ca9817dde`.
- E12 native metrics:`e948b6a57fc9ca69a1a4ae2f423cdce9c9c7097cbeec1e5496b9ba7bdf910dbf`; native cases:`18fd3ba0edd6ddb1c567ffc7c88918c6289a5a1250f7e8d2391e38689a0e8ac5`.
- E12 TRAIN cases:`35ff7914bd12c5b2f41a063e9920efd810adf18cf10513c2f7b60c0c1e1bd291`; curves:`99c824c6cc5c6b3959a6c9b4e374c58797eaa04476972cf88c9c4e8e6cbf1872`.
- Target-geometry summary:`51ff8f862e08c396fc83b5422e328cfc2a703415e4eb703717d24b79669cd790`.

No new images, mask arrays, model tensors, predictions or GPU work were used. No CAL/test images were read and no production/status/registry/source files modified by this subagent. Original archive/cache-array hashes are preserved metadata rather than independently reread arrays. Repeated VAL selection, one seed, unavailable patient/study IDs, unadjudicated clinical subtypes and absent external/radiologist validation limit every reliability claim. Coefficient2 is rejected; this is not a completed clinically reliable model.
