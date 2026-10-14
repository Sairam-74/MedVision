# E11 reference continuation: completed interim analysis

Finalized 9 October 2026 UTC after interruption; the assigned filename retains the 8 October reference-stage date. This report compares selected E10/global30 with continued E11/global39, both using positive Dice coefficient1 and hard factor2. It is not the final E11/E12 factor comparison and supplies no evidence of a coefficient2 effect.

**Continuation reduced normal alerts but did not produce balanced reliability.** Native VAL false positives fell199→139 with unchanged aggregate case misses16. Useful fracture-pixel recall fell42.80%→22.71%, while mean positive Dice remained approximately0.38. Selected E11 is research evidence, not a replacement for production.

## Independent scope and identity checks

Read every saved row:463 unique VAL images,83 positive/380 normal in422 conservative related groups;2,808 unique TRAIN images,493 positive/2,315 normal. Each VAL ID, label, source archive member, group, native shape, GT pixel count, annotation count and metadata flag matches the frozen manifest. Each TRAIN ID, label, group and GT grid area matches the manifest; all cache metadata rows, source members and image/decoded hashes match it. These checks establish exact membership, not patient independence: patient/study IDs remain unavailable.

Both completed native audits and read-only TRAIN-fit completions passed. Recomputed classification, Dice/IoU and pixel aggregates match the saved metrics. Current sources and native source snapshots match their recorded hashes. The reference uses unchanged stretch256/CLAHE2/tile8/blur3/unit preprocessing, threshold0.5/all independent masks, BCE+Dice, normal BCE1, presence weight0, batch2, Adam1e-4, clipping10, seed42, natural unique sampling and frozen109 hard-positive/713 hard-negative catalogs. Logged presence BCE contributes nothing to the objective.

E11 restored the selected full E10/global30 model/Adam snapshot. Its initial metadata records the full parameter digest and optimizer snapshot identity; the completed TRAIN-only smoke records exact coefficient1/original hard-loss model/optimizer parity. This subagent verified checkpoint file-byte hashes, not checkpoint tensors. No new image, mask array, model tensor, inference, GPU, CAL/test, threshold policy or guarded-source work occurred.

## Selected native VAL comparison

All rates below describe independent mask presence; a case alert does not guarantee localization on the fracture.

| Metric | E10/global30 | E11/global39 |
|---|---:|---:|
| TP / FN / TN / FP |67 /16 /181 /199|67 /16 /241 /139|
| Accuracy |53.56%|66.52%|
| Precision |25.19%|32.52%|
| Sensitivity |80.72%|80.72%|
| Specificity |47.63%|63.42%|
| F1 |0.38395|0.46367|
| AUROC / average precision |0.78529 /0.57404|0.80736 /0.56410|
| FPR / FNR |52.37% /19.28%|36.58% /19.28%|
| Positive macro Dice / IoU |0.37953 /0.28367|0.37511 /0.28417|
| Mean positive precision, nonempty / recall |0.48309 /0.43858|0.61517 /0.38429|
| Global pixel precision / recall |0.22109 /0.42804|0.31938 /0.22713|
| Global Dice / IoU |0.29157 /0.17067|0.26547 /0.15305|
| Native pixel TP / FP / FN |167,845 /591,338 /224,282|89,063 /189,799 /303,064|
| Mask-instance IoU0.5 matches /99 |28|30|
| Mask-instance precision / recall |0.06965 /0.28283|0.10714 /0.30303|
| Component-box AP0.5 / AP0.5:0.95 |0.12514 /0.04550|0.18935 /0.06662|
| Proxy Brier / ECE |0.36270 /0.39858|0.27452 /0.28046|

Mask-instance IoU is distinct from component-box AP. Box AP uses enclosing boxes of predicted components and individual polygon rasterizations, max-pixel confidence and101-point interpolation; it is not canonical COCO mAP or a trained detection head. Calibration values use an uncalibrated maximum-pixel proxy, not a fracture probability. E11's138 scores≥0.9 average0.9761 but only40.58% have fracture labels.

Native FP pixels decreased401,539, but useful TP pixels also decreased78,782. Empty misses remain16; under-segmentation tags rise16→24, over-segmentation21→14 and complete mislocalization11→6. Tags overlap and are mathematical mask failures, not adjudicated clinical causes. Cases with any GT overlap rise56→61, while Dice<0.2 positives rise29→37: finding a few pixels can coexist with losing substantial coverage.

Exact transitions show94 recovered normal FPs and34 new normal FPs; six recovered fracture FNs and six new FNs. Seven positives regain some overlap and two lose all overlap. Twenty-eight positive Dice gains>0.02 and25 losses>0.02 are recorded with IDs in the DATA file. Identical aggregate FN counts do not mean identical missed images.

## All twelve E11 epochs

Every epoch sees2,808 unique TRAIN sources. Selection is the frozen feasible-first/minimum-normalized TP/TN/Dice/IoU rule, not maximum Dice. The final selected checkpoint is epoch9/global39; later epoch10 reaches higher Dice with many more normal alerts.

| Epoch / global | TRAIN total loss | VAL Dice / IoU | TP / TN |
|---|---:|---:|---:|
|1 /31|0.954861|0.38018 /0.27598|76 /101|
|2 /32|0.954268|0.39846 /0.28880|74 /153|
|3 /33|0.953798|0.41585 /0.30380|79 /129|
|4 /34|0.951565|0.41224 /0.30678|73 /154|
|5 /35|0.953275|0.40946 /0.29965|76 /89|
|6 /36|0.952278|0.45250 /0.33456|74 /155|
|7 /37|0.952054|0.45597 /0.34120|77 /141|
|8 /38|0.948157|0.42825 /0.32040|72 /117|
|9 /39 selected|0.947942|0.37511 /0.28417|67 /241|
|10 /40|0.948492|0.45980 /0.34291|78 /120|
|11 /41|0.946935|0.43767 /0.33019|72 /143|
|12 /42|0.947817|0.44503 /0.33432|75 /141|

Loss and later maximum overlap still improve; the curves do not establish a plateau. No epoch simultaneously passes the registered TP79/TN342 and Dice≥0.52379656/IoU>0.37756859 gates. Reported epoch6 wall9,005.605s includes manual standby10:17:15–12:41:12 UTC; subtracting that nominal pause leaves368.605s, not an exact GPU runtime. Native audit config and trainer reproduction both say CUDA; saved CPU timing prose is stale. Median forward41.20ms/pipeline98.33ms was not an isolated idle latency comparison.

## Technical strata and TRAIN fit

Flags overlap. Frontal is the dataset flag, not verified AP. Small means native GT area fraction≤0.0020550129324089714, fixed from TRAIN's25th percentile; it is not clinical subtlety. Multiple means multiple annotations/fracture_count metadata, not expert subtype adjudication. Small and multiple groups have no normals, so their FPR/specificity are unavailable.

| VAL stratum | Positive / normal | TP E10→E11 | FP E10→E11 | Dice E10→E11 |
|---|---:|---:|---:|---:|
|Hand|63 /118|56→53|63→57|0.43036→0.43337|
|Leg|18 /237|8→12|124→74|0.18892→0.20023|
|Hip|4 /29|3→4|16→9|0.28611→0.33635|
|Shoulder|7 /31|6→3|16→11|0.23429→0.09601|
|Mixed|9 /34|6→5|20→12|0.19966→0.19880|
|Hardware|7 /1|4→4|1→0|0.07039→0.09407|
|Multiscan|9 /37|5→6|26→19|0.23054→0.18954|
|Frontal|51 /246|41→41|134→95|0.36031→0.34857|
|Lateral|39 /122|31→31|74→48|0.38116→0.37402|
|Oblique|5 /37|2→2|11→13|0.16814→0.12602|
|Small area|12 /0|10→10|—|0.33806→0.37644|
|Multiple annotations|16 /0|12→13|—|0.38885→0.39737|

Small-area pixel recall falls86.49%→35.81%; multiple-annotation pixel recall70.59%→18.64%. Full counts/IoU/precision/recall for all strata are preserved in DATA. Tiny strata and overlapping flags do not establish causal anatomy/view effects.

Unaugmented TRAIN grid fit changes TP416→392, FN77→101, normal FP1,143→805, positive Dice0.37513→0.37435 and pixel recall0.35091→0.32683. Across the109 frozen hard positives, Dice0.05813→0.07414 and useful pixel recall0.05669→0.07005 improve modestly, but85/109 still have zero overlap,45 empty masks and40 nonempty wrong-region masks. Hard-positive overlap is observed on24/109, versus310/384 ordinary positives. Hard-normal alerts547→434 and ordinary-normal alerts596→371 decline. Exact hard-case transitions and all2,808 TRAIN checks are saved; these grid diagnostics do not substitute for native VAL acceptance.

The strongest unresolved evidence is poor useful foreground fitting on TRAIN alongside the selected VAL coverage loss. This does not identify clinical subtlety, initialization, resolution or BatchNorm as the cause. No next factor is selected by this interim record; assess the completed matched E11/E12 pair and actual mask reviews separately. The90% accuracy,95.2% sensitivity and90% specificity targets remain unmet. No model was promoted, no calibration fitted and no final/generalization success claimed.

## Evidence hashes

Full input/current-source/snapshot checks are in [DATA](E11_REFERENCE_INTERIM_ANALYSIS_20261008_DATA.json), SHA256`16001328c59516769558f3f40dfe4ca71007644ca418425f840f274155e05c92`.

- Frozen manifest:`4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318`.
- E10 selected weights:`bfbba05a924f75ed3a4261977b31bf7d7c2af9c940cfdbfc4ec2d153324c2348`; full initializer:`655c2ddf756989e30bf1cdb070076af05cb544c88a435b4bd93909e85edbc7b6`.
- E11 selected weights:`c1703d13e5b4cdf35b600c48825ec93c3394570ab1df44d20e9a06b41abc2b84`; initial parameter digest recorded:`dbd1d7298b3d2ef0775eacbe926daa30697616adbdc7f3276ddb6397f57d03f4`.
- E11 native metrics:`b76674549a726b8ec5e0399a42f1cf9294401920aa6db7b00ac307037b09b091`; cases:`846acc4ecc7fcc0e73b58c6fe4f46c9ae4cc84fecfce505603d9461927d81438`.
- E11 TRAIN cases:`6746041f1d3edab4182f98ad5633dcef8f093a52a8e4fcc55d4fd13b0747e863`; curves:`38f11d6ee1191b5fb990a400c1aed9b6619db45e9cb0c73dcd58911bf785b898`.

VAL is repeatedly used for selection; untouched CAL/test predictions, external validation, patient/study independence and expert radiologist adjudication are absent. Original checkpoint/archive identities are preserved in frozen configs; archive/cache arrays were not reread or independently rehashed here.
