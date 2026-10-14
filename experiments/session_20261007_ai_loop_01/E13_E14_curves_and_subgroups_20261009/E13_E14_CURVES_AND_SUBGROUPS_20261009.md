# E13/E14 curves and subgroups — 9 October 2026

All 24 completed epoch records (12 per arm, globals 40–51) and both selected full native VAL audits were read and verified. E13/E14 recorded initial full model/Adam digests match the registered E11 epoch 9 / global 39 initializer. No model files, tensors, arrays or images were read. No threshold sweep, inference, GPU job, promotion or next-factor choice was performed.

The logs contain augmented TRAIN total/BCE/Dice/presence/foreground-offset losses. **VAL loss/components were not logged and are unavailable**; they cannot be recovered from saved thresholded masks. The VAL columns below are native inverse-mapped evaluation metrics, not TRAIN-grid fit metrics.

## Selection and curve findings

| Arm | Selected additional / global epoch | TRAIN total first → last | TRAIN change | Maximum native VAL AUROC (epoch / global) | Maximum native positive Dice (epoch) | Feasible epochs |
| --- | --- | --- | --- | --- | --- | --- |
| E13 | 6 / 45 | 0.948492 → 0.940376 | -0.856% | 0.8399176 (11 / 50) | 0.459799 (1) | 0 |
| E14 | 11 / 50 | 0.961056 → 0.949216 | -1.232% | 0.8506658 (12 / 51) | 0.467943 (1) | 0 |

Both arms use the unchanged feasible-first rule, then the minimum and mean of TP/79, TN/342, Dice/0.5237965563 and IoU/0.3775685933, with earlier ties retained. The feasibility condition also requires accuracy ≥0.90 and IoU strictly above its floor. E13 selects epoch 6; E14 selects epoch 11. Neither selected checkpoint nor any other saved epoch passes all gates.

TRAIN losses decrease modestly within each arm, while native VAL masks fluctuate: E13 TP ranges 69–82 and TN 77–204; E14 TP 70–82 and TN 44–237. Low-false-alert selection does not pick peak AUROC or peak positive Dice. E14 epoch 12 has maximum AUROC but is not selected. These facts do not prove that simply continuing longer would resolve the bottleneck.

TRAIN Dice loss includes weighted normal-image terms, so 1 minus this loss is not positive-case Dice. E14 total/BCE include the foreground coefficient-5 offset; cross-arm scalar loss differences are not quality differences. The base BCE column is saved BCE minus saved foreground offset. Presence BCE is logged but contributes no training objective because presence weight is zero.

## All saved TRAIN component rows

| Arm | Additional / global epoch | Total | BCE incl. offset | Base BCE derived | Dice loss | Foreground offset | Presence BCE diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E13 | 1 / 40 | 0.948492 | 0.009092 | 0.009092 | 0.939399 | 0.000000 | 0.912839 |
| E13 | 2 / 41 | 0.946935 | 0.008433 | 0.008433 | 0.938502 | 0.000000 | 0.912766 |
| E13 | 3 / 42 | 0.947817 | 0.008405 | 0.008405 | 0.939413 | 0.000000 | 0.913327 |
| E13 | 4 / 43 | 0.946179 | 0.008843 | 0.008843 | 0.937336 | 0.000000 | 0.912560 |
| E13 | 5 / 44 | 0.947563 | 0.008878 | 0.008878 | 0.938685 | 0.000000 | 0.913864 |
| E13 | 6 / 45 | 0.943793 | 0.008499 | 0.008499 | 0.935294 | 0.000000 | 0.910543 |
| E13 | 7 / 46 | 0.942390 | 0.008344 | 0.008344 | 0.934046 | 0.000000 | 0.913105 |
| E13 | 8 / 47 | 0.943204 | 0.008239 | 0.008239 | 0.934965 | 0.000000 | 0.913706 |
| E13 | 9 / 48 | 0.943837 | 0.008190 | 0.008190 | 0.935647 | 0.000000 | 0.916806 |
| E13 | 10 / 49 | 0.940845 | 0.008427 | 0.008427 | 0.932418 | 0.000000 | 0.912404 |
| E13 | 11 / 50 | 0.941302 | 0.007946 | 0.007946 | 0.933356 | 0.000000 | 0.915218 |
| E13 | 12 / 51 | 0.940376 | 0.008231 | 0.008231 | 0.932145 | 0.000000 | 0.914566 |
| E14 | 1 / 40 | 0.961056 | 0.021191 | 0.008850 | 0.939864 | 0.012341 | 0.912930 |
| E14 | 2 / 41 | 0.958722 | 0.019394 | 0.008222 | 0.939328 | 0.011173 | 0.913407 |
| E14 | 3 / 42 | 0.957562 | 0.019735 | 0.008285 | 0.937827 | 0.011450 | 0.913152 |
| E14 | 4 / 43 | 0.956791 | 0.019494 | 0.008302 | 0.937296 | 0.011193 | 0.913289 |
| E14 | 5 / 44 | 0.957329 | 0.019365 | 0.008220 | 0.937964 | 0.011145 | 0.913306 |
| E14 | 6 / 45 | 0.953326 | 0.018644 | 0.008051 | 0.934682 | 0.010593 | 0.911145 |
| E14 | 7 / 46 | 0.951267 | 0.018323 | 0.008016 | 0.932944 | 0.010307 | 0.913157 |
| E14 | 8 / 47 | 0.952133 | 0.018738 | 0.008245 | 0.933396 | 0.010493 | 0.912262 |
| E14 | 9 / 48 | 0.951665 | 0.018522 | 0.008017 | 0.933143 | 0.010506 | 0.912971 |
| E14 | 10 / 49 | 0.949583 | 0.018520 | 0.008069 | 0.931063 | 0.010451 | 0.910859 |
| E14 | 11 / 50 | 0.949564 | 0.017674 | 0.007741 | 0.931890 | 0.009933 | 0.912447 |
| E14 | 12 / 51 | 0.949216 | 0.018029 | 0.007888 | 0.931187 | 0.010141 | 0.913013 |

## All saved native VAL metric rows

TP/FN count case mask alerts on source-positive images; an alert is not proof of target overlap. Dice/IoU are positive-source macro overlap measures and include missed positives as zero. An asterisk marks an epoch that established a new best when encountered, not all final selected models.

| Arm | Additional / global epoch | TP / FN | TN / FP | Positive Dice | Positive IoU | AUROC | New best |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E13 | 1 / 40 | 78 / 5 | 120 / 260 | 0.459799 | 0.342909 | 0.8320545 | * |
| E13 | 2 / 41 | 72 / 11 | 143 / 237 | 0.437669 | 0.330191 | 0.7746037 | * |
| E13 | 3 / 42 | 75 / 8 | 141 / 239 | 0.445028 | 0.334323 | 0.8085289 |  |
| E13 | 4 / 43 | 79 / 4 | 88 / 292 | 0.442342 | 0.326788 | 0.8064680 |  |
| E13 | 5 / 44 | 73 / 10 | 122 / 258 | 0.448636 | 0.335638 | 0.8163760 |  |
| E13 | 6 / 45 | 69 / 14 | 204 / 176 | 0.424430 | 0.323116 | 0.8144261 | * |
| E13 | 7 / 46 | 69 / 14 | 201 / 179 | 0.446464 | 0.342029 | 0.8070704 |  |
| E13 | 8 / 47 | 77 / 6 | 127 / 253 | 0.394869 | 0.290948 | 0.7957197 |  |
| E13 | 9 / 48 | 81 / 2 | 92 / 288 | 0.422611 | 0.315048 | 0.8204819 |  |
| E13 | 10 / 49 | 77 / 6 | 134 / 246 | 0.440086 | 0.322080 | 0.8275840 |  |
| E13 | 11 / 50 | 82 / 1 | 77 / 303 | 0.393263 | 0.276591 | 0.8399176 |  |
| E13 | 12 / 51 | 75 / 8 | 152 / 228 | 0.452368 | 0.342268 | 0.8245086 |  |
| E14 | 1 / 40 | 81 / 2 | 104 / 276 | 0.467943 | 0.345209 | 0.8417565 | * |
| E14 | 2 / 41 | 74 / 9 | 171 / 209 | 0.466101 | 0.354270 | 0.8272353 | * |
| E14 | 3 / 42 | 76 / 7 | 121 / 259 | 0.429732 | 0.319526 | 0.8024096 |  |
| E14 | 4 / 43 | 82 / 1 | 44 / 336 | 0.417626 | 0.299436 | 0.8044705 |  |
| E14 | 5 / 44 | 75 / 8 | 144 / 236 | 0.432936 | 0.322608 | 0.8240647 |  |
| E14 | 6 / 45 | 73 / 10 | 226 / 154 | 0.434426 | 0.333204 | 0.8423906 | * |
| E14 | 7 / 46 | 77 / 6 | 161 / 219 | 0.463534 | 0.347325 | 0.8481294 |  |
| E14 | 8 / 47 | 73 / 10 | 195 / 185 | 0.428813 | 0.320627 | 0.8420894 |  |
| E14 | 9 / 48 | 77 / 6 | 139 / 241 | 0.465389 | 0.347467 | 0.8163602 |  |
| E14 | 10 / 49 | 79 / 4 | 104 / 276 | 0.463391 | 0.340421 | 0.8305010 |  |
| E14 | 11 / 50 | 70 / 13 | 237 / 143 | 0.429107 | 0.327273 | 0.8342105 | * |
| E14 | 12 / 51 | 77 / 6 | 175 / 205 | 0.448503 | 0.336407 | 0.8506658 |  |

## Necessary bound for a fixed scalar cutoff

For one fixed case-score ranking on 83 positives and 380 normals, a cutoff achieving TP ≥79 and TN ≥342 strictly ranks each selected true positive above every selected true negative. This supplies at least 79×342 = 27,018 strictly concordant positive–normal pairs. AUROC counts concordant pairs plus half of ties out of all 83×380 = 31,540 pairs; the remaining pair contributions cannot be negative. Therefore:

`AUROC ≥ (79 × 342) / (83 × 380) = 13509 / 15770 = 0.8566265060240964`

The maximum saved AUROC is E14 epoch 12 / global 51: **0.8506658211794547**, below the necessary bound by 0.0059606848446417. Thus none of these 24 fixed native VAL rankings can reach both TP ≥79 and TN ≥342 through a scalar cutoff alone. These integer targets correspond to sensitivity 95.18% and specificity 90.00%. No new thresholds were evaluated here.

This is a **necessary, not sufficient** condition. AUROC above the bound would not guarantee such an operating point, accurate localization, Dice/IoU gates, clinical reliability or test-set generalization. Strictly monotone calibration preserves score order, so it cannot repair this ranking limitation. New scoring functions/models and different postprocessing mechanisms are outside this proof.

## Selected full native subgroup classification

The same-ID subgroup memberships and exact denominators were cross-checked against both saved per-case audits. Flags overlap; do not add rows. Entries are E13 → E14. TP/FN remain case-alert measures.

| Source subgroup | Positive / normal | TP / FN | TN / FP | Recall | FPR | AUROC |
| --- | --- | --- | --- | --- | --- | --- |
| hand | 63 / 118 | 51/12 → 54/9 | 48/70 → 56/62 | 80.95% → 85.71% | 59.32% → 52.54% | 0.764326 → 0.768227 |
| leg | 18 / 237 | 15/3 → 13/5 | 143/94 → 167/70 | 83.33% → 72.22% | 39.66% → 29.54% | 0.802860 → 0.806142 |
| hip | 4 / 29 | 4/0 → 4/0 | 16/13 → 19/10 | 100.00% → 100.00% | 44.83% → 34.48% | 1.000000 → 0.870690 |
| shoulder | 7 / 31 | 5/2 → 5/2 | 23/8 → 21/10 | 71.43% → 71.43% | 25.81% → 32.26% | 0.811060 → 0.741935 |
| mixed | 9 / 34 | 6/3 → 6/3 | 25/9 → 25/9 | 66.67% → 66.67% | 26.47% → 26.47% | 0.754902 → 0.692810 |
| hardware | 7 / 1 | 6/1 → 6/1 | 0/1 → 0/1 | 85.71% → 85.71% | 100.00% → 100.00% | 0.428571 → 0.714286 |
| multiscan | 9 / 37 | 7/2 → 4/5 | 17/20 → 24/13 | 77.78% → 44.44% | 54.05% → 35.14% | 0.705706 → 0.585586 |
| frontal | 51 / 246 | 42/9 → 41/10 | 124/122 → 147/99 | 82.35% → 80.39% | 49.59% → 40.24% | 0.795951 → 0.795632 |
| lateral | 39 / 122 | 31/8 → 32/7 | 70/52 → 76/46 | 79.49% → 82.05% | 42.62% → 37.70% | 0.811896 → 0.826818 |
| oblique | 5 / 37 | 5/0 → 3/2 | 20/17 → 26/11 | 100.00% → 60.00% | 45.95% → 29.73% | 0.800000 → 0.718919 |
| small region proxy | 12 / 0 | 9/3 → 10/2 | 0/0 → 0/0 | 75.00% → 83.33% | undefined → undefined | undefined → undefined |
| multiple fractures | 16 / 0 | 13/3 → 11/5 | 0/0 → 0/0 | 81.25% → 68.75% | undefined → undefined | undefined → undefined |

Full specificity, accuracy, precision, F1, AUPRC and confusion matrices are preserved unchanged in the metadata JSON. Specificity is 1 minus FPR only where normals exist. The all-positive proxy/multiple-fracture strata have no normal denominator: specificity/FPR/AUROC are undefined; AUPRC=1 is not useful evidence of normal/fracture discrimination.

## Selected full native subgroup segmentation

Positive-source macro Dice/IoU include empty positive masks as zero. Precision averages nonempty positive masks only; recall averages all positive sources. Values are E13 → E14; normal-mask Dice is excluded.

| Source subgroup | Positive sources | Dice | IoU | Positive precision (nonempty) | Positive recall |
| --- | --- | --- | --- | --- | --- |
| hand | 63 | 0.441841 → 0.442171 | 0.339101 → 0.340396 | 0.551036 → 0.521674 | 0.506415 → 0.509683 |
| leg | 18 | 0.359554 → 0.340855 | 0.269612 → 0.252307 | 0.494861 → 0.530535 | 0.388706 → 0.342974 |
| hip | 4 | 0.412480 → 0.361217 | 0.287596 → 0.227493 | 0.485608 → 0.730166 | 0.447124 → 0.249061 |
| shoulder | 7 | 0.171650 → 0.354060 | 0.121933 → 0.259473 | 0.259139 → 0.512116 | 0.192894 → 0.370251 |
| mixed | 9 | 0.214641 → 0.255515 | 0.155744 → 0.172128 | 0.284282 → 0.544859 | 0.274580 → 0.222015 |
| hardware | 7 | 0.333705 → 0.284164 | 0.247348 → 0.204749 | 0.556730 → 0.367410 | 0.366020 → 0.276324 |
| multiscan | 9 | 0.292907 → 0.257338 | 0.216499 → 0.196967 | 0.587697 → 0.566016 | 0.282109 → 0.269185 |
| frontal | 51 | 0.379022 → 0.405197 | 0.284503 → 0.307835 | 0.497721 → 0.575905 | 0.420631 → 0.423833 |
| lateral | 39 | 0.446258 → 0.427674 | 0.345829 → 0.328119 | 0.575923 → 0.467380 | 0.507821 → 0.520167 |
| oblique | 5 | 0.356443 → 0.229621 | 0.250895 → 0.165900 | 0.583367 → 0.477808 | 0.356032 → 0.223207 |
| small region proxy | 12 | 0.354306 → 0.370510 | 0.248484 → 0.266661 | 0.420735 → 0.436630 | 0.541112 → 0.480184 |
| multiple fractures | 16 | 0.462921 → 0.361540 | 0.353774 → 0.282914 | 0.569007 → 0.559766 | 0.514782 → 0.413560 |

## What remains to diagnose

Aggregate normal alerts decrease and global overlap improves, but the selected candidate is mixed across source strata: leg recall 15/18 → 13/18, multiscan 7/9 → 4/9, oblique 5/5 → 3/5, and source multiple-fracture case alerts 13/16 → 11/16. Their Dice also falls. Shoulder positive Dice increases substantially while shoulder normal alerts increase 8 →10. These small and overlapping strata support explicit failure review, not a clinical subgroup-success claim.

The small-region proxy has 12 positives and no normals; its occupancy cutoff is 0.0020550129324089714 (about 0.2055%), frozen from the positive TRAIN 25th percentile. It is annotation-size metadata, not clinically subtle or nondisplaced fracture status. The multiple-fractures stratum is the source fracture_count >1 condition; no expert clinical subtype confirmation is available. Source view flags are not validated AP/study links, and related-image groups are not proven patients.

The evidence narrows the remaining problem to insufficient case-score separation together with inconsistent useful region overlap. A threshold-only or calibration-only explanation cannot meet the stated fixed-score count gates for these records. The curves alone do not establish batch-normalization context, input resolution, preprocessing, annotations or architecture as the cause. A bounded TRAIN-only normalization-context diagnosis can test whether identical inputs are materially sensitive to batch/evaluation context. Only an actual material, controlled finding would justify a subsequent matched intervention; a null result would leave other evidence-based hypotheses open. A TRAIN diagnostic itself does not establish native VAL/test improvement.

Validation loss was not logged, so a loss-gap overfitting diagnosis is unsupported. Inference speed is also not inferred from saved CPU audit timing, epoch duration or overlap with other processes. No timing comparison is made here. Repeated VAL selection is not a locked-test evaluation, and no next factor or promotion is selected by this memo.

## Provenance and limits

Every saved JSON/source input was byte-hashed before use and rechecked unchanged before writing. All 24 exact numerical rows, full selected classification/segmentation subgroup objects, verified membership IDs/hashes, initializer metadata and the rational bound are in `curves_and_subgroups_metadata.json`. Model SHA values are recorded metadata only; no checkpoint-file bytes or tensors were read.

- `experiments/session_20261007_ai_loop_01/FOREGROUND_BCE_EXPERIMENT_PROTOCOL.json`: `250bcd50e0ba8463d6da746e469222b41a82b8114ec1add1aece6fd04850e523`
- `experiments/AI_E13_v3_foreground_BCE_reference/epochs.jsonl`: `4196acb270c09d10cdbb818bd09dd50e33272fe4657a07d9498e63b4e974f1c2`
- `experiments/AI_AUDIT_E13_v3_foreground_BCE_reference/metrics.json`: `f9cded16423ba4a26066d577629dc328c82a12e52b8d7c9dd281b1097a2ea530`
- `experiments/AI_AUDIT_E13_v3_foreground_BCE_reference/per_case.json`: `6431defac958f37527531aae7381b614fce07f74906cd39da9b71075598d188f`
- `experiments/AI_E14_v3_foreground_BCE5/epochs.jsonl`: `38312f772baea1ac4b415d4999c1f2af5e679ea0b84dc772b1e499631e9abf19`
- `experiments/AI_AUDIT_E14_v3_foreground_BCE5/metrics.json`: `7675188a0d760309b718ad257903d2b3d970bd19c350615ea0d78573277f2392`
- `experiments/AI_AUDIT_E14_v3_foreground_BCE5/per_case.json`: `deb8a2525742fdea7fa5fc95ab9596ef8192e9c7476be6aa64c27ed7f6147f66`

Additional limits:

- VAL loss/components were not logged; no missing values are fabricated.
- TRAIN loss averages augmented weighted all-image batches, including normal Dice terms; 1-DiceLoss is not positive segmentation Dice.
- E14 BCE includes the coefficient-specific foreground offset; its larger loss scalar is not directly comparable to E13 quality.
- presence_BCE is diagnostic because presence_weight is zero and the head receives no optimization gradient.
- Epoch VAL metrics use native inverse-mapped masks in evaluation mode; raw TRAIN grid-fit metrics are a different context.
- Selected native checkpoints differ in additional/global epoch; subgroup comparisons are selected-model results, not same-epoch effects.
- Repeated VAL measurements and selection are not locked-test evidence.
- Anatomy/view flags overlap and are source metadata; verified patient/study identifiers are unavailable.
- small_region_proxy is TRAIN-derived annotation occupancy, not clinical subtle/nondisplaced fracture status.
- multiple_fractures is the source fracture_count>1 stratum; no expert clinical subtype confirmation.
- Single-class subgroup specificity/FPR/AUROC are undefined; AUPRC=1 in all-positive sets is not discrimination evidence.
- AUROC bound is necessary only for a fixed scalar cutoff and not sufficient for required overlap/Dice or clinical reliability.
- No CPU/audit timing metadata is used as GPU inference performance. No new inference, tensors, images or CAL/test access.
- The curves do not establish BN, image resolution, annotation or domain-shift causality; targeted TRAIN-only diagnosis remains necessary.
