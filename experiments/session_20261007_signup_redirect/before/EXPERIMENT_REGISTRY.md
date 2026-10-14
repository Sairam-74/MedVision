# MedVision experiment registry



Last updated: 6 October 2026. Project deadline: 10 October; poster on 8 October managed by user. Report deferred. Original checkpoint/data/threshold remain unchanged. Patient independence and historical model exposure are unverified.



| Run | Status | Data/config | Measured outcome | Evidence |

|---|---|---|---|---|

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
