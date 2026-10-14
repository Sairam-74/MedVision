# AI reliability session - 7 October 2026

Scope: AI inspection, immutable baseline, leakage checks, technical failure analysis and actual controlled GPU training. No website or unrelated application changes. This session supersedes earlier UI work, the obsolete GPU Code43 status, interrupted E2 status and automatic E3/E4/test/paper-watcher instructions. Project submission remains 10 October. No new model is accepted or served.

## Measured unchanged baseline

[Immutable report](../../BASELINE_MODEL_REPORT.md), [full evidence](../AI_BASELINE_20261007_v1/), [pipeline inspection](PIPELINE_INSPECTION.md).

The original Attention U-Net checkpoint was strictly loaded and evaluated at its existing .90 threshold/all-components policy on all 612 v2 validation images, without changing its preprocessing, weights or policy. Original training exposure is unknown: these are diagnostic validation measurements, not independent clinical or locked-test results.

| Metric | Original model |
|---|---:|
| Accuracy | 25.6536% |
| Precision | 19.2513% |
| Sensitivity | 98.1818% |
| Specificity | 9.7610% |
| F1 | 0.321908 |
| AUROC | 0.585386 |
| AUPRC (average precision) | 0.210279 |
| False-positive rate | 90.2390% |
| False-negative rate | 1.8182% |
| Positive-image mean Dice | 0.482326 |
| Positive-image mean IoU | 0.361818 |
| Positive-image segmentation precision (nonempty predictions) | 0.450753 |
| Positive-image segmentation recall | 0.621012 |
| Global segmentation Dice, including normal false marks | 0.182614 |
| Global segmentation IoU | 0.100481 |
| Global pixel precision | 0.104595 |
| Global pixel recall | 0.718685 |
| Mask-instance recall at IoU .50 | 45/137 = 32.8467% |
| Mask-instance precision at IoU .50 | 45/1135 = 3.9648% |
| Component-box AP proxy at .50 | 0.017832 |
| Component-box AP proxy at .50:.95 | 0.005221 |
| Max-pixel proxy Brier score | 0.751677 |
| Max-pixel proxy 10-bin ECE | 0.756843 |
| CPU forward median | 403.2 ms |
| CPU decode/preprocess/forward/native-mask median | 411.7 ms |

Confusion: TN49, FP453, FN2, TP108. Macro Dice/IoU exclude normals and include missed positives as zero; global metrics include normal false-positive pixels. A component-box AP proxy is not canonical detector COCO mAP. Maximum pixel sigmoid is not a clinical fracture probability. Nine image-level true positives have zero intersection with the annotated fracture: image sensitivity must not be confused with useful localization.

All native reference/predicted masks, per-case metadata and error panels are saved. The two actual image misses were individually inspected. Both show overlying cast-like material and small annotated targets; association does not establish a clinical cause or subtle/nondisplaced labels. Sample false-positive and segmentation panels were also inspected. Exhaustive radiologist adjudication of every error remains pending; the collected technical error list is not expert diagnosis.

The evaluator's measurement pass completed under the existing CPU demo runtime, which lacks matplotlib. The separate finalizer used the existing phase2 plotting runtime to produce figures/report from saved measurements. No measurements were replaced, and native cached counts exactly reproduce the baseline. Never overwrite either baseline report copy or its evidence directory.

## Leakage and dataset integrity

Current data is already FracAtlas v6, not a new external dataset. Existing v2 quarantine excludes 59 unreadable normal images and seven contradictory training images. Eligible v2: 4017, with 919 instances. Fourteen remaining exact-copy positive mask-boundary disagreements remain disclosed. Dataset ZIP and v1/v2 manifests were preserved.

Known image/member/encoded-hash/decoded-hash/conservative-group cross-split overlaps are zero. Patient/study identifiers are absent, so patient independence is unverified. No patient-level or external-generalization claim is justified.

Prospective fresh-model partition: [v3 manifest](../data_v3_reliability_20261007/manifest.json), SHA256 `4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318`.

| Split | Images | Fractures | Normals |
|---|---:|---:|---:|
| Train | 2808 | 493 | 2315 |
| Validation | 463 | 83 | 380 |
| Calibration | 149 | 27 | 122 |
| Reserved test | 597 | 111 | 486 |

Validation/calibration were split by existing groups, stratified by group fracture label, seed42, without model outputs. Train/test assignments are unchanged. The exact manifest bytes are reproducible with `tools/freeze_reliability_partition.py`. The old checkpoint's unknown exposure and E2's historical use of all612 validation images are not erased by this prospective partition. No test image predictions were computed this session.

## Failure analysis and rejected shortcuts

[Failure analysis](../AI_FAILURE_ANALYSIS_20261007_v1/FAILURE_ANALYSIS.md) contains per-case evidence and all57 threshold/component-policy combinations (.05-.95; all/largest/min16). Best specificity is only11.55%; no point meets accuracy>90%, sensitivity>=95%, specificity>=90%. Threshold/filtering alone is rejected as sufficient correction. Production remains .90.

Nonexclusive segmentation tags:49 over-segmented positives,21 under-segmented positives,9 zero-overlap mislocalizations and2 empty misses. These are measured overlap categories, not proven clinical causes. The primary observed bottleneck is background/fracture discrimination, compounded by the ANY-pixel case rule and saturated score proxy (497/612 exactly1).

[Shadow calibration diagnostic](../AI_CALIBRATION_DIAGNOSTIC_20261007/CALIBRATION_DIAGNOSTIC.md): regularized sigmoid mapping fitted on149 calibration cases, evaluated on463 validation cases. Brier .738704 -> .148435 and ECE .745993 -> .029344, but constant calibration-prevalence Brier is better (.147133). Masks and errors do not improve. Rejected as a sufficient reliability fix; mapping is not served. Historical exposure limits this diagnostic.

## Actual completed training and mining

The RTX3050 6GB now works (driver616.92; torch2.9.1+cu128, runtimeCUDA12.8). Real CUDA tensor/gradient tests passed. Two-training-image benchmark median step .19583s, peak allocated1.302GB: hardware execution only, not validation performance. No driver or dependency changes were needed.

E2 was first snapshotted, then resumed from saved epoch10 on CUDA under its original data/code/config. It finished12 epochs. Best epoch11, .50/all, all612 old validation cases: positive Dice .260319, IoU .186706, sensitivity90%, specificity11.3546%, accuracy25.4902%, FP445, FN11. Not accepted at this recorded default operating point. Its different threshold/data/preprocessing make this descriptive, not an isolated causal comparison to the original. No E2 threshold optimization or final-test evaluation was performed.

[Training-only hard sets](../AI_TRAIN_HARD_SETS_20261007/): two frozen model snapshots (original .90 and preserved E2 epoch10 .50) evaluated all2808 training images. HARD_POSITIVE_SET has127 positives with Dice<.20 in BOTH; HARD_NEGATIVE_SET has1641 normals marked by BOTH. Unique train IDs only, no validation/calibration/test cases and no image duplication. These algorithmic difficult cases are not clinically labelled subtle fractures. They are catalogued for future bounded, representative mining; the current paired experiment does not introduce sampling as a second factor.

## Controlled GPU experiments executing

[Frozen protocol](RELIABILITY_EXPERIMENT_PROTOCOL.json), [live queue](reliability_queue.json).

- AI_E5_v3_BCE_reference: fresh matched reference, normal-image BCE coefficient1, running.
- AI_E6_v3_normal_BCE2: fresh candidate, only normal-image BCE coefficient2, sequentially queued.
- Same architecture, initial parameter digest, train distribution, preprocessing, augmentation, Adam1e-4, batch2, seed42,12 epoch ceiling/patience12 and463 validation IDs. No original checkpoint is used as initialization. Neither run reads calibration/test for training or checkpoint selection.
- Selection score .4 positive native Dice + .3 sensitivity + .3 specificity at .50/all; full metric logging. This score does not authorize promotion.
- E5 epoch1 is a real background-collapse observation: accuracy82.0734%, sensitivity0%, specificity100%, Dice0, FN83, FP0. This apparently higher accuracy is unacceptable. Training continues; it is not a final candidate result.
- Auditing5916 planned positive augmentations found one real target erasure (IMG0002386, epoch9,119 pixels ->0). The new trainer retains the aligned original image/mask when augmentation erases the entire positive target and carries source class labels explicitly. Same guard in BOTH runs. Existing pipeline/E2 sources are unchanged.
- Analytic loss/gradient and metric fixtures, actual erasure-case check, GPU smoke and checkpoint resume passed. Smoke metrics are not performance claims.

Do not edit guarded sources or launch a duplicate trainer/queue. Hidden PowerShell7 queue PID26660 (snapshot; verify command line before acting) runs E5 then E6 and stops at `completed_training_only`. Python environment launcher and its child are one training job, not duplicate independent runs. Old E3/E4 and completion/test/paper watchers were not live and were not restarted. There is NO automatic final test or promotion.

## Research and evidence limits

[Research matrix](RESEARCH_NOTES.md) records primary sources, authors/year, methods, dataset/results, application and limitations: Guo2017 calibration, Lindsey2018 conditional fracture localization/reader study, Abedeen2023 current FracAtlas provenance, Bachmann2024 difficult fracture/reader evaluation. Calibration was tested rather than assumed useful. A future case classifier is a hypothesis if matched loss weighting fails, not a preapproved replacement. No published number is presented as a local result. No external data was downloaded.

Anatomy/view subgroup tables and denominators are in the baseline report. Frontal is not proven AP; view flags can overlap. No clinical subtle/nondisplaced, paired-study, independent external or AI/radiologist-correction labels are available. Small-mask and multiple-instance analyses are labelled proxies. No new >90% result, clinically calibrated probability, validated uncertainty band, external reliability or improved production model is claimed.

## Resume and remaining work

1. Read PROJECT_STATUS.md, EXPERIMENT_REGISTRY.md, this report, frozen protocol and live queue/run states. Verify the recorded process command lines before launching anything; inspect logs if no matching trainer is live. Preserve failed evidence. Do not reuse a run directory for a fresh run.
2. Let E5/E6 finish unchanged; verify matching initial parameter hashes, guarded data/source/checkpoint hashes and full epoch logs. If interrupted, the trainer supports `--resume` using last completed epoch and identical registered arguments/runtime; record device/runtime changes. Inspect queue state before any manual resume, because E6 may already be running.
3. Compare selected checkpoints on the SAME463 validation IDs, including native masks, all FP/FN, region matching, score/calibration diagnostics, learning curves and resolution/robustness/latency. Evaluate threshold choices only there. Compare original same-ID reference from original_model_matched_v3_reference.json. Reject sensitivity/FPR/Dice trade-offs outside the protocol; never force a winner.
4. Diagnose failed controlled experiments before choosing another single factor (loss, learned case confidence, resolution/global-local or representative hard mining). Do not start arbitrary architecture/sampling/augmentation changes together.
5. Only after validation acceptance select and freeze the model/protocol, fit calibration on the149 separate calibration cases, then freeze full operating policy. Reserve the597 test cases for one final evaluation after all tuning/selection. No automatic old watcher may access them.
6. External generalization, patient identity verification and clinical difficult-case/radiologist adjudication remain unmeasured; document rather than fabricate. Final old/new comparisons and promotion require evidence. Maintain registry and status after every session.

Verification evidence: [verification.json](verification.json). Original checkpoint SHA256 `922f30bf691b9979aee65d386bcf73d2643558c049a7d11ab013fea315f39b81`; dataset SHA256 `747119b26f2684e0e35a7688083b14b12a206149b0cfe5357824b69b3a5e6cf8`. Baseline report SHA256 `3d5e5e6149882d23cb5a145665f534d5f810e3815c913ba6bc66ccb2699dd12b`. Website untouched; original checkpoint/threshold/data/manifests and guarded original training/inference sources preserved.
