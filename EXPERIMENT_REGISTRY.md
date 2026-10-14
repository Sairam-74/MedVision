# MedVision experiment registry

## Report preparation and verified continuation state — 11 October 2026

Final report delivery verified: 79 pages, eight chapters, 21 figures, 30 tables and 19 cited references; Word fields and PDF pagination updated. `reports/phase_ii_20261011/Report_Verification_Checklist.md` records source checks, missing evidence, institutional signature placeholders and rendered QA. The 203-file protection inventory has zero changes. DOCX SHA-256: `b6ea7ed7ebec26c00f6657cf1cc6dffe98721ddc537c80c657996d8360b9d0f3`; PDF: `40d3d335a2a781b9066e1ceaa76de199e8fd125d3d610fba46fb0e55f77c2651`. No new experiment was registered and no AI acceptance status changed.

Documentation-only session: created the editable Major Project Phase-II report, matching Word-rendered PDF and verification checklist in `reports/phase_ii_20261011/`. The reference `report 2.docx`, application/model sources, original checkpoint, data archive, baseline and retained experiment records were preserved. No model training, new validation/calibration/test predictions, application changes or model promotion occurred during report preparation.

This addendum supersedes stale pending descriptions in older snapshots below. Completed evidence confirms E13/E14 pair audits and all four normal/positive failure-review memos; the frozen 32-TRAIN BatchNorm diagnostic is complete (384 forwards / 768 presentations, 189 preservation guards). Temporary batch-statistics inference is rejected as context dependent. The native-derived 512 TRAIN cache and discarded four-source, two-step resolution smoke are complete; cached/raw 256 model and optimizer outputs match exactly. Full 256-versus-512 candidate training remains pending; prepared tools and smoke weights are not E15/E16 performance results.

Latest E14 native VAL463: TP 70, FN 13, TN 237, FP 143; accuracy 66.31%, sensitivity 84.34%, specificity 62.37%, positive Dice 0.429107 and IoU 0.327273. Within-pair KEEP FOR DEVELOPMENT remains distinct from production acceptance. Any-target overlap falls from 63/83 to 61/83; all joint acceptance gates still fail. Production remains the preserved original checkpoint. Final reserved TEST597 evaluation, accepted candidate calibration, external validation and radiologist reader evaluation remain unperformed.

Next AI action after returning to model work: inspect completed failure/fit/normalization/resolution evidence, freeze and register one matched native-derived 256/512 comparison from the selected E14 full model/Adam initializer, require reference replay, then evaluate both on VAL463 without accessing CAL/test for selection. Do not restart old watchers. Report completion is not an instruction to launch training.


<!-- AI_LOOP_STATUS_BEGIN -->
## ACTIVE AI IMPROVEMENT LOOP - resumed 7 October 2026

Observed UTC: 2026-10-09T16:15:17.965031+00:00. E13/E14 completed. Actual positive reviews finished 51 and 52 cases; E13 normal review finished 176 alerts and 47 full panels; E14 all 143 alerts and 46 full panels viewed, final memo pending. Native joint acceptance still fails. Any-overlap positives fall 63 to 61 and six of seven added alerts are wrong-region. Hard TRAIN fit remains poor. New bounded frozen 32-TRAIN BatchNorm context diagnostic written and AST checked, independent review pending; no training factor chosen or candidate promoted. Original checkpoint/data/baseline preserved; no new VAL/CAL/test inference or frontend changes.

Frozen validation:463 images (83 fractures/380 normals). Required practical case counts:TP>=79 andTN>=342, plus meaningful native segmentation/localization improvement. At79/83, sensitivity rounds to95.2%. No accuracy-only success or production promotion.

| Run | State | Selected validation epoch | Accuracy | Sensitivity | Specificity | FP / FN | Positive Dice / IoU |
|---|---|---:|---:|---:|---:|---|---|
| AI_E10_v3_hard_weight2 | completed | 12 | 53.56% | 80.72% | 47.63% | 199 / 16 | 0.379528 / 0.283667 |
| AI_E11_v3_positive_Dice_reference | completed | 9 | 66.52% | 80.72% | 63.42% | 139 / 16 | 0.375114 / 0.284169 |
| AI_E12_v3_positive_Dice2 | completed | 3 | 63.28% | 77.11% | 60.26% | 151 / 19 | 0.383322 / 0.284676 |
| AI_E13_v3_foreground_BCE_reference | completed | 6 | 58.96% | 83.13% | 53.68% | 176 / 14 | 0.424430 / 0.323116 |
| AI_E14_v3_foreground_BCE5 | completed | 11 | 66.31% | 84.34% | 62.37% | 143 / 13 | 0.429107 / 0.327273 |
| AI_E5_v3_BCE_reference | completed | 8 | 50.76% | 73.49% | 45.79% | 206 / 22 | 0.220230 / 0.160818 |
| AI_E6_v3_normal_BCE2 | completed | 12 | 50.11% | 79.52% | 43.68% | 214 / 17 | 0.239207 / 0.169445 |
| AI_E7_v3_presence_reference | failed_before_validation | Pending | Pending | Pending | Pending | Pending | Pending |
| AI_E7_v3_presence_reference_r2 | completed | 10 | 59.61% | 73.49% | 56.58% | 165 / 22 | 0.270507 / 0.198882 |
| AI_E8_v3_presence_supervision_r2 | completed | 7 | 42.12% | 89.16% | 31.84% | 259 / 9 | 0.280566 / 0.208040 |
| AI_E9_v3_hard_reference | completed | 9 | 51.40% | 80.72% | 45.00% | 209 / 16 | 0.359342 / 0.265569 |

These are recorded checkpoint/default-threshold observations, not final accepted models. Full audits and error panels are retained separately; current live run files supersede this snapshot.

Active evidence/protocol: experiments/session_20261007_ai_loop_01/LOOP_PROTOCOL.json, LATEST_PROGRESS.json and loop_events.jsonl. Existing unchanged baseline is BASELINE_MODEL_REPORT.md; all older history below is retained.

E5/E6 decision: REJECT stronger normal BCE as an overall improvement at registered default point. Native CPU E6 audit FP215 differs from trainer GPU FP214 by one single-pixel normal alert (IMG0003056); both observations retained.

E7/E8 registered presence branch comparison: both start from known TRAIN-only E5 epoch8 weights, reset Adam equally, receive12 additional matched epochs, and retain independent unfiltered masks. The primary classification table for E8 uses conservative head+ OR mask+ review alerts. Head-only performance cannot hide mask false alarms or missed localization. Technical recovery r2 protocol: PRESENCE_EXPERIMENT_PROTOCOL_r2.json; smoke: AI_PRESENCE_MODEL_SMOKE_20261007_r2. Original failed run retained; no validated epoch lost. No performance gain claimed from smoke checks.

Do not edit frozen model/trainer/cache/protocol sources during the active pair. Do not restart old E3/E4 or automatic test/paper watchers. Reserved test597 remains closed; calibrate only after selection/gate passes on separate149 cases. Original checkpoint/threshold/data are preserved; website untouched.

E9/E10 bounded hard-example comparison registered after actual E8 native failure review: same selected E7 global18 full model/Adam restored independently,12 further matched epochs/global19-30,109 persistent hard fractures and713 persistent hard normals from TRAIN only. Factor1 versus2 within-class mean-normalized loss weights is the only intervention. All2808 source images appear once per epoch; no duplicated samples. HARD_EXPERIMENT_PROTOCOL.json and hard_queue.json contain frozen inputs/live progress.

Hard-example paired decision: KEEP FOR DEVELOPMENT; full further gates required. A smoke pass proves execution/parity only; it is not evidence of improved performance.

E11/E12 positive-case Dice coefficient1 versus2: independently restore E10 selected epoch12/global30 full model and Adam, continue12 matched epochs/global31-42. Hard factor2, all-image BCE, normal Dice, architecture, resolution, preprocessing, sampling and selection are unchanged. POSITIVE_DICE_EXPERIMENT_PROTOCOL.json and positive_dice_queue.json freeze inputs and track progress. Actual E10 review covered199 normal alerts and55 positive segmentation failures; hard TRAIN fractures remain poorly fitted.

Positive-Dice paired decision: REJECT as balanced overall improvement at registered operating point. No new calibration/test access or production promotion.

E13/E14 foreground-pixel BCE coefficient 1 versus 5: independently restore the same selected E11 epoch 9 / global 39 full model and Adam, then continue 12 matched epochs / globals 40-51. Hard factor 2, presence weight 0, normal BCE weight 1 and positive-case Dice coefficient 1 remain fixed. Only annotated foreground-pixel BCE changes; background BCE, normal-image loss, Dice, architecture, resolution, preprocessing, sampling and selection remain unchanged. FOREGROUND_BCE_EXPERIMENT_PROTOCOL.json and foreground_bce_queue.json freeze inputs and track progress. The first three reference epochs must match the saved E11 globals 40-42 under the registered parity checks.

Foreground-BCE paired decision: KEEP FOR DEVELOPMENT; full further gates required. Passed smoke and reference replay establish execution/parity only; performance requires the full paired native audits and actual failure review. No calibration/test access or production promotion.

<!-- AI_LOOP_STATUS_END -->

## CURRENT AI SESSION - 7 October 2026: Immutable baseline and controlled GPU experiments

90% target follow-up (2026-10-07T04:02:22.295398+00:00): E5 latest completed epoch7, interim validation accuracy30.4536%, sensitivity86.7470%, specificity18.1579%, positive Dice0.200999. Still unaccepted. Balanced example target on463 cases: at least79 true positives and342 true negatives (90.93% accuracy); masks/localization must also improve. Details: experiments/session_20261007_ai_baseline/TARGET_90_PERCENT.md. Training protocol unchanged; reserved test closed.

Observed UTC: 2026-10-07T03:17:30.043994+00:00. AI only; no accepted new model. This section supersedes obsolete RUNNING E2, blocked CUDA and automatic test/promotion statuses in historical rows. Live files override progress snapshots.

| Experiment | Status / factor | Actual measurement / decision | Evidence |
|---|---|---|---|
| AI-BASELINE-20261007-v1 | COMPLETE; unchanged original .90/all; v2 validation612 | Accuracy25.65%; precision19.25%; sensitivity98.18%; specificity9.76%; F1 .321908; AUROC .585386; AP .210279; FP453/FN2; positive Dice .482326, IoU .361818; proxy Brier .751677/ECE .756843. Diagnostic only; unknown historical exposure. NEVER overwrite. | BASELINE_MODEL_REPORT.md; experiments/AI_BASELINE_20261007_v1/ |
| AI-THRESHOLD-20261007 | COMPLETE;19 thresholds x3 policies, cached unchanged probabilities | Best specificity11.55%; zero balanced acceptance points. REJECT as sufficient fix; production remains .90/all. | experiments/AI_FAILURE_ANALYSIS_20261007_v1/ |
| AI-CALIBRATION-20261007 | COMPLETE shadow sigmoid mapping; fit149/evaluate463 | Brier .738704 -> .148435; ECE .745993 -> .029344; constant prevalence Brier .147133 is better. Errors unchanged; REJECT as sufficient fix, never served. | experiments/AI_CALIBRATION_DIAGNOSTIC_20261007/ |
| AI-DATA-v3-20261007 | FROZEN prospective split, groups/seed42 | Train2808/validation463/calibration149/reserved-test597; train/test IDs unchanged; patient IDs unavailable; exact bytes reproduced. Old E2/original exposure not erased. | experiments/data_v3_reliability_20261007/; tools/freeze_reliability_partition.py |
| E2-corrected-baseline | COMPLETE12 epochs; preserved original v1 protocol, GPU resume epoch11 | Selected epoch11: Dice .260319/IoU .186706; sensitivity90%, specificity11.35%; FP445/FN11 at default .5/all. Not accepted at recorded default point; no threshold optimization/final test. | experiments/E2_corrected_baseline/; experiments/session_20261007_ai_baseline/E2_REFERENCE_COMPARISON.json; E2_interrupted_snapshot/ |
| AI-TRAIN-HARD-20261007 | COMPLETE TRAIN-only original and frozen E2epoch10 errors | 127 recurring hard positives,1641 recurring hard negatives; unique TRAIN IDs only. Catalogued, no current sampling change. Clinical subtle labels unavailable. | experiments/AI_TRAIN_HARD_SETS_20261007/HARD_POSITIVE_SET.json; HARD_NEGATIVE_SET.json |
| AI-E5-v3-BCE-reference | RUNNING; fresh normal BCE weight1 | Real epoch1 accuracy82.07%, sensitivity0%, specificity100%, Dice0, FN83/FP0: unacceptable early collapse, training continues. Matched reference, not accepted model. | experiments/AI_E5_v3_BCE_reference/; experiments/session_20261007_ai_baseline/RELIABILITY_EXPERIMENT_PROTOCOL.json |
| AI-E6-v3-normal-BCE2 | QUEUED; only normal-image BCE coefficient2 vs1 | No full training/evaluation results yet. Same architecture/initialization/data/preprocess/augmentation/loss except normal BCE term/seed/optimizer. No automatic promotion/test. | experiments/session_20261007_ai_baseline/reliability_queue.json |
| AI-AUGMENTATION-GUARD | PASSED technical fix common toE5/E6 | One of5916 planned positive transforms erased its119 target pixels; actual case reproduced and guard preserves aligned119pixels. Original shared pipeline unchanged. | experiments/session_20261007_ai_baseline/augmentation_label_audit.json; augmentation_guard_check.json |
| AI-GPU-20261007 | RECOVERED; execution benchmark, not performance | RTX3050 6GB; CUDA operation/gradients/smoke/resume pass. Median two-image step .19583s, peak allocated1.302GB. Driver/env unchanged. | experiments/session_20261007_ai_baseline/gpu_benchmark.json; experiments/AI_normal_loss_GPU_smoke_20261007_r2/ |

E5 snapshot at 2026-10-07T03:17:30.043994+00:00: training, epoch 2, batch 500/1404; 1 completed validation epoch(s). Live state files supersede this snapshot.

Configuration/model provenance, acceptance gates, clinical-label gaps, research matrix and resume instructions: [experiments/session_20261007_ai_baseline/SESSION_REPORT.md](experiments/session_20261007_ai_baseline/SESSION_REPORT.md). Snapshot: [experiments/session_20261007_ai_baseline/session_close_training_snapshot.json](experiments/session_20261007_ai_baseline/session_close_training_snapshot.json). Original model remains current. No external dataset added, no reserved-test predictions, no new >90% or radiologist-reliability claim. Do not promote an accuracy-only or Dice-only winner.



Last updated: 7 October 2026. Project deadline: 10 October; poster on 8 October managed by user. Report deferred. Original checkpoint/data/threshold remain unchanged. Patient independence and historical model exposure are unverified.



| Run | Status | Data/config | Measured outcome | Evidence |

|---|---|---|---|---|

| UI-signup-redirect-20261007 | Completed | Real isolated auth backend + rebuilt production frontend | 20 browser auth checks, 9 frontend tests; lint/typecheck/build pass; real signup automatically redirects, persisted account login and duplicate rejection verified | `experiments/session_20261007_signup_redirect/verification.json` |


| P2-runtime | Completed on CPU | Original checkpoint; Python 3.13.7 / torch 2.9.1+cu128; real positive + normal uploads | Strict load, finite output; native overlays; invalid-input regressions pass | `experiments/session_20261005/cuda_runtime_smoke.json` |

| P2-clean-reproduction | Completed | New isolated `.venv-clean`; pinned manifest; torch 2.9.1+cpu | `pip check`, strict load, real API regressions, exact paper-table and figure regeneration pass | `clean_runtime_smoke.json`, `clean_environment.freeze.txt`, `clean_paper_evidence.log` in session folder |

| P2-CUDA | Blocked by device | RTX 3050 6 GB; CUDA wheel installed | Windows PnP Code 43; zero CUDA devices, init fails | `cuda_diagnostic.log`, `gpu_inventory.txt` in session directory |

| D1-audit | Completed; visual review and label contradictions documented on 6 October | All 4,083 source images; 59 normal decode failures excluded | 4,024 eligible, 717 positives, 922 annotations; no positive mask lost at 256 | `experiments/data_v1/audit.json` |

| D1-split | Frozen v1 | Conservative duplicate/related-image grouping, seed 42 | Train 2,815 / val 612 / test 597; disjoint groups; patient independence unknown | `experiments/data_v1/manifest.json`, split ID files and hash |

| D2-phase3-review | Completed technical audit | FracAtlas v6 CC BY 4.0; 17 annotation examples; all 217 non-exact pairs | Zero known cross-split candidates; 7 contradictory case-label images quarantined; 14 other exact-mask disagreement groups disclosed | `experiments/phase3_review/DATASET_AUDIT.md` |

| D2-quarantine-split | Frozen v2 | Same assignments, remove 7 contradictory training images | 4,017 eligible; train 2,808, val 612, test 597; v1 preserved | `experiments/data_v2/` |

| E2-v2-manifest-smoke | Passed execution only | Four train/four val, isolated explicit-manifest trainer | Finite training/checkpoint/native validation; no test; not a full experiment | `experiments/E2_v2_manifest_smoke/` |

| E0-learning-cpu | Completed sanity only | Fresh Attention U-Net; one training positive + one training normal; BCE + Dice; 12 steps | Loss 1.66445 -> 1.46616, finite gradients; median step 6.40 s; ~2.50 h/full epoch | `experiments/E0_learning_cpu/config.json`, `metrics.json`, isolated `sanity_model.pt` |

| E0-learning-clean-cpu | Completed sanity only | Same two-image/12-step config in clean CPU wheel environment | Median step 1.972 s; ~46.27 min/full epoch projection; peak 2.13 GiB. Use this newer compute estimate | `experiments/E0_learning_clean_cpu/metrics.json` |

| E1-historical-validation | Completed diagnostic | Original checkpoint; 612 validation images; 19 thresholds x all/largest/min16 policies | At .90/all: positive Dice .482326; sensitivity 108/110; normal FP 453/502; global Dice .182614 | `experiments/E1_historical_validation/` |

| E1-selection-screen | Completed diagnostic, not adopted | Same validation outputs, sensitivity/FPR comparison margins | Best qualifying Dice .482962 at .80/all, but normal FP 456/502. Tiny difference; retain .90/all serving. Lowest FPR remains 88.45% | `comparison.json`, `per_case.json` in E1 directory |

| Demo-HTTP | Completed | Real localhost server; built frontend/assets/login/upload/history/export | Actual socket upload-to-result succeeds; original-size output and history/export verified | `experiments/session_20261005/demo_http.json` |

| Paper-evidence | Draft generated | Saved integer per-case counts; no test evaluation | Principal table reproduces; measured CSV/plots/manuscript draft | `paper/table_reproduction.json`, `paper/MANUSCRIPT_DRAFT.md` |

| E2-trainer-smoke | Passed execution/resume only | Four train + four val images, one epoch then optimizer/epoch resume to epoch 2 | Checkpoint recovery/resume and native metrics logging pass. Tiny validation scores are not performance results | `experiments/E2_training_smoke_final/`, session smoke logs |

| E2-corrected-training | **RUNNING** | Fresh Attention U-Net; BCE+Dice; natural sampling; conservative augmentation; batch 2; Adam 1e-4; seed 42; 12-epoch ceiling, patience 5 | PID 36928 verified; first optimizer update executed. Full train 2,815 / val 612. Estimated ceiling ~9-10 h, variable. No test accessed; no result claimed yet | `experiments/E2_corrected_baseline/`, `E2_process.json`, `E2_training.log` in session directory |

| P4-pipeline-checks | Passed | Letterbox 256/512, 919 instances; padding/gradients, 3 loss modes, seeded sampler | No annotation lost; requested 50% sampler drew 50.21%; extreme logits finite | `experiments/phase4_checks/checks.json` |

| P4-logits-trainer-smoke | Passed execution/resume | Four train/four val; letterbox128, controlled sampler; direct logits BCE+Dice | Epoch 1 then resume epoch 2; tiny validation Dice 0, not performance | `experiments/P4_trainer_smoke/` |

| P4-real-overfit | Passed memorization only | AttentionUNet64, two training images, letterbox128, BCE+Dice, Adam1e-3, no augmentation | 60 updates; grid Dice .965251, native Dice .913160, normal mask empty; not generalization | `experiments/P4_overfit_128/` |

| P4-bundle-API | Passed | Real multipart uploads; shared native evaluation/serving; explicit contract | Native masks equal; invalid bundles and logits-as-legacy return 503; historical default regressions pass | `phase4_bundle_api.json`, `runtime_smoke.json` in 6 October session |

| E3-controlled-comparison | Not run | Matched loss/architecture/preprocessing comparison | Choose after compute recovery and corrected baseline | No claimed result |

| Final-test | Not run | Freeze new model/config before one test pass | Test set remains unused for model evaluation/tuning | No claimed result |



Original checkpoint SHA-256: `922f30bf691b9979aee65d386bcf73d2643558c049a7d11ab013fea315f39b81`.



Archive SHA-256: `747119b26f2684e0e35a7688083b14b12a206149b0cfe5357824b69b3a5e6cf8`.



Split manifest SHA-256: `e931cd3d3dce044f7d8f43fefeda596d39d9dc8529453f5262441c1a64e20227`.



Safe commands and environment limitations are in `DEMO.md`. Run directories are immutable: use new IDs instead of overwriting. `tools/run_experiment.py evaluate` defaults to validation and never trains. `--final-test` is an explicit access guard, not proof that a model was frozen. Probability cache is float16 for qualitative reuse; exact table regeneration uses saved integer counts rather than approximate probabilities.



Update this file and `PROJECT_STATUS.md` after each session with completed/failed runs, commands, hashes, exclusions, decisions and next actions. Do not convert historical validation numbers into final test claims.



6 October session: E2 continues on immutable v1; seven contradictory training targets discovered later. Do not relabel its results as v2. New-run command: `.\.venv-clean\Scripts\python.exe tools/train_baseline_manifest.py --out experiments/E3_v2_bce_dice --epochs 12 --loss bce_dice`; launch only after verifying the existing full CPU job status and compute budget. v2 manifest SHA: `19a950c34d96c0fc076fbb75bdeffbf2f0b262626817d61018eff31e907544bb`.



Phase 4 E2 update: epoch 1 train loss 1.135661; at .5 validation positive Dice/sensitivity 0 and no predictions. Epoch 74.15 min. Background collapse; no improvement claim. Continued unchanged into epoch 2. No v2 full run or final test executed.



## 6 October: Phase 6 / Phase 7 / security session



| Run | Status | Actual result / limit | Evidence |

|---|---|---|---|

| P6-development-validation | Complete, development only | Frozen epoch-1 E2 copy; 612 val, 110 positives/502 normals; Dice/sensitivity 0; region recall 0/137 at IoU .10/.50. No test; no promotion | `experiments/P6_development_validation/` |

| P7-security-CI | Passed | 58 checks, deterministic predictor; auth/ownership/traversal/limits/timeout/persistence/session tests | `secure_api_final.json` in this session |

| P7-real-original-API | Passed | 59 checks; two distinct val X-rays; exact direct inference masks, protected original/overlay/export | `secure_api_real_final.json` |

| P7-real-logits-API | Passed, smoke bundle only | 59 checks; native masks equal shared inference; not a selected model | `secure_bundle_api.json` |

| P7-browser | Passed | 25 checks; actual login/upload/result/history/export/reload/mobile/dark/logout; original model predicts a region on normal example | `browser/browser_checks.json`, `browser/medvision_demo.webm` |

| P7-runtime-parity | Passed for two images | torch2.14.1 browser-native integer counts equal archived torch2.9.1 counts; not exhaustive | `serving_parity.json` |

| P7-dependency-security | Passed known-advisory scan | npm 0; 40 Python upstream versions 0/skipped0; Bandit0. Training environment retained separately | `SECURITY_REVIEW.md` and audit JSONs |

| P7-patched-trainer-smoke | Passed execution only | Four train/four val, one epoch; torch2.14.1+cpu; Dice0 is not performance evidence | `experiments/P7_patched_trainer_smoke/` |

| E3-v2-logits-BCE+Dice | **QUEUED after E2** | letterbox256, blur0, sampler.5, batch2, seed42, Adam1e-4, 12 epochs/patience5; no result claimed | `training_queue.json`, `queue_process.json` |

| E4-v2-logits-focal-Tversky | **QUEUED after E3** | Same controlled settings, loss changed only; no result claimed | same queue record |



Local demo uses `.venv-demo` and the preserved original .90/all checkpoint. Final-test/model-freeze and final-paper gates remain open. The active E2 is v1, not the new v2 runs. See current PROJECT_STATUS and DEMO instructions; historical unauthenticated verification scripts are archival and must not be used as current API tests.



Phase 7 release follow-up: legacy image-origin/cookie mismatch fixed without rewriting history. Current checks: 60 security/CI, 61 real original API, 61 real logits API, 27 browser including old-case image revisit, 7 frontend. Source/evidence release r2 replaces the earlier package as the current deliverable; v1 remains preserved. E2 source/data unchanged, v2 runs still queued. No final test or final-model claim.



### P7_FINAL_REPRODUCTION — 6 October 2026



Executed isolated current-source copy with 220 file SHA checks, fresh npm ci (0 advisories), lint/typecheck, 7 frontend tests and production build. Temporary-storage backend checks: 60 stub/security and 61 real original-checkpoint checks; no test split access. Final browser: 28 checks, original and normal validation examples, legacy-history image revisit, mobile first-link navigation, persistence/logout/export. Normal example also predicted a region: false positive remains disclosed; no new model performance claim. Original artifact and active source hashes reverified. E2 remains active; E3/E4 waiting for E2. Evidence: `experiments/session_20261006_p6p7/clean_reproduction.json`; release `deliverables/MedVision_verified_demo_20261006.zip`.


## P8_UI_AND_COMPLETION_PROTOCOL — 6 October 2026

- Rebuilt dashboard and sign-in with navy/blue/cyan styling, strong contrast, a persistent navigation rail, real case activity, workflow guidance and useful research context. Upload and result pages now explain the workflow, output, model identity, native dimensions and operating threshold. Fixed the global anchor-style override that suppressed intended link/button colours. Desktop, mobile and dark screenshots and a fresh real-inference video are in `experiments/session_20261006_completion_ui/browser/`.
- Added authenticated `/api/research` and `/research`: frozen-manifest counts, live completed-epoch metrics, queue status, historical-exposure caveat, normal false alarms, dataset provenance and expandable methodology. Queued runs have no invented metrics; final-test/model status is explicit. Scientific evidence is projected through a fixed whitelist without credentials, patient history, internal guards or arbitrary path access.
- Verification: **64** backend security checks, **65** actual original-model API checks, **65** actual logits-bundle API checks, **32** browser checks, **7** frontend tests; lint/typecheck/production build pass. Bandit across application and new research tools: zero findings. Native count/policy parity and saved-table reproduction passed on four validation images; smoke/final-test rejection and string-labelled normal parsing verified. Evidence: `experiments/session_20261006_completion_ui/verification.json`.

Registered before any final-test access: E3/E4 native threshold .05–.95 × all/largest/minimum16 policies; validation-only admissibility and simplest-policy tie rule; fixed validation-only between-run choice; both frozen before test. Four-case smoke verifies exact native policy counts and table regeneration, with no final split access. Initial smoke exposed string `0` truthiness; explicit integer labels fixed it; unsuccessful output remains preserved. Source-guarded completion watcher is active, waiting for the unchanged training queue. Final results, selected-model API, measured manuscript and deployment record are future outputs, not current achievements. Current E2 epoch-6 best: Dice 0.191464, sensitivity 0.972727, normal FPR 0.942231. Original model/data/sources unchanged.

Final package follow-up: all 247 archived file identities verified; the actual packaged source also passed 64 temporary-storage security/API checks using the separately installed patched Python runtime. No original dataset/checkpoint/history was copied or changed. Evidence: `experiments/session_20261006_completion_ui/packaged_security.json`; ZIP SHA-256 `30268a7699d6d36387df1357e9d07e9bc8fba891ceaba4e868261ad55d92992c`. Training and completion watcher remain active; final test not yet evaluated.

## AUTH_LIFECYCLE_20261006

- Restored demo credential prefill for explicitly enabled loopback launches using the actual current demo password; no universal static password and no personal-account prefill. Browser confirmed the owner's real demo signs in without typing credentials. Signup-created accounts retain their email and a blank password on the sign-in page. Better credential/rate-limit/connectivity errors replace generic failures.
- Fixed signup's missing useState import; preserved the owner's current signup/recovery routes and links. Real signup persists salted password hashes, assigns only the ordinary technician role and returns a recovery code once. Duplicate addresses and invalid/short credentials are rejected; signup is rate-limited with a local account quota.
- Forgot Password now verifies email plus the saved recovery code, then routes to a ten-minute reset grant in a URL fragment. Single-use grants are stored as hashes. A successful reset revokes all previous sessions and recovery keys, returns a new code once and clears the used token from the visible URL. Invalid/expired/used grants fail clearly; no fallback demo-token or false-success screen. No email service is configured, so the UI does not claim to send messages. Shared demo recovery code: .local_demo/demo_recovery_code.txt. Lost personal code: owner-only local command `python tools/reissue_recovery.py --email address` using .venv-demo; not an HTTP endpoint.
- Passed 31 account-lifecycle checks, 16 actual-browser auth checks, 65 real original-inference API checks and 9 frontend tests; lint/typecheck/build and Bandit pass. Test accounts lived in separate disposable/private storage. No recovery codes/passwords were written into test reports, screenshots or videos. Evidence: `experiments/session_20261006_auth/verification.json`. Actual demo remains on localhost:8000; isolated test server stopped.
- Original checkpoint/dataset/manifests/active training source hashes remain unchanged; existing accounts and case history preserved. Source before this session is in `experiments/session_20261006_auth/before/`. Training remains active. Completion watcher was re-registered solely after updating the manuscript generator's auth description; training queue and validation/test selection protocol are unchanged. No final-result or completed-paper claim.


Current authentication source/evidence release: `deliverables/MedVision_auth_enabled_20261006.zip` (257 file identities verified). This supersedes earlier application packages; original historical packages are preserved. No credentials, recovery secrets, private account database, dataset ZIP or model weights are included.
