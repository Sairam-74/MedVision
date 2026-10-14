# MedVision Project Status

## CURRENT SESSION — 6 October 2026: Working demo sign-in, signup and recovery

- Restored demo credential prefill for explicitly enabled loopback launches using the actual current demo password; no universal static password and no personal-account prefill. Browser confirmed the owner's real demo signs in without typing credentials. Signup-created accounts retain their email and a blank password on the sign-in page. Better credential/rate-limit/connectivity errors replace generic failures.
- Fixed signup's missing useState import; preserved the owner's current signup/recovery routes and links. Real signup persists salted password hashes, assigns only the ordinary technician role and returns a recovery code once. Duplicate addresses and invalid/short credentials are rejected; signup is rate-limited with a local account quota.
- Forgot Password now verifies email plus the saved recovery code, then routes to a ten-minute reset grant in a URL fragment. Single-use grants are stored as hashes. A successful reset revokes all previous sessions and recovery keys, returns a new code once and clears the used token from the visible URL. Invalid/expired/used grants fail clearly; no fallback demo-token or false-success screen. No email service is configured, so the UI does not claim to send messages. Shared demo recovery code: .local_demo/demo_recovery_code.txt. Lost personal code: owner-only local command `python tools/reissue_recovery.py --email address` using .venv-demo; not an HTTP endpoint.
- Passed 31 account-lifecycle checks, 16 actual-browser auth checks, 65 real original-inference API checks and 9 frontend tests; lint/typecheck/build and Bandit pass. Test accounts lived in separate disposable/private storage. No recovery codes/passwords were written into test reports, screenshots or videos. Evidence: `experiments/session_20261006_auth/verification.json`. Actual demo remains on localhost:8000; isolated test server stopped.
- Original checkpoint/dataset/manifests/active training source hashes remain unchanged; existing accounts and case history preserved. Source before this session is in `experiments/session_20261006_auth/before/`. Training remains active. Completion watcher was re-registered solely after updating the manuscript generator's auth description; training queue and validation/test selection protocol are unchanged. No final-result or completed-paper claim.

## CURRENT SESSION — 6 October 2026: Information-rich frontend and guarded research completion

- Rebuilt dashboard and sign-in with navy/blue/cyan styling, strong contrast, a persistent navigation rail, real case activity, workflow guidance and useful research context. Upload and result pages now explain the workflow, output, model identity, native dimensions and operating threshold. Fixed the global anchor-style override that suppressed intended link/button colours. Desktop, mobile and dark screenshots and a fresh real-inference video are in `experiments/session_20261006_completion_ui/browser/`.
- Added authenticated `/api/research` and `/research`: frozen-manifest counts, live completed-epoch metrics, queue status, historical-exposure caveat, normal false alarms, dataset provenance and expandable methodology. Queued runs have no invented metrics; final-test/model status is explicit. Scientific evidence is projected through a fixed whitelist without credentials, patient history, internal guards or arbitrary path access.
- Verification: **64** backend security checks, **65** actual original-model API checks, **65** actual logits-bundle API checks, **32** browser checks, **7** frontend tests; lint/typecheck/production build pass. Bandit across application and new research tools: zero findings. Native count/policy parity and saved-table reproduction passed on four validation images; smoke/final-test rejection and string-labelled normal parsing verified. Evidence: `experiments/session_20261006_completion_ui/verification.json`.
- New measured E2 development observation: best completed epoch 6, positive Dice 0.191464, sensitivity 0.972727, normal false-positive rate 0.942231 (473/502 normal cases falsely flagged). This supersedes the zero-Dice epoch-1 snapshot as latest training evidence, not as a final model. Live snapshot: `{"status": "training", "latest_epoch": 6, "current_epoch": 7, "batch": 800, "batches": 1408, "mean_train_loss": 0.9822001187503338, "smoke": false}`. E2 remains v1; its sources/environment/data were preserved.
- **Completion execution is active:** existing E2 → E3 → E4 training queue is unchanged. Separate source/artifact-guarded watcher waits for `completed_training_only`, calibrates both full v2 models on validation, freezes both operating points and the validation-only winner, evaluates each frozen model once on the reserved test, saves native per-case/subgroup/region/bootstrap results, regenerates the measured paper, and checks the selected model against the real API. It writes a verified deployment record only after those checks; the launcher selects it on the next launch. No current final-test access, finalist promotion or completed-paper claim. Process and protocol: `experiments/session_20261006_completion_ui/completion_watch_process.json`, `completion_watch.json`, `completion_protocol.json`. Do not launch duplicate watchers/trainers or alter guarded sources without inspecting/re-registering.
- Research manuscript rewritten from actual data and saved epoch records: `paper/MANUSCRIPT_DRAFT.md`. It replaces stale authentication/browser/audit descriptions and retains pending comparison markers. On successful final evaluation, the watcher generates `paper/MEASURED_RESEARCH_PAPER.md` and `controlled_results.csv`. Author agreement, guide/technical review, independent reproduction, venue/reference requirements and final formatting remain external outstanding steps; the institutional report remains deferred as requested.
- Original checkpoint, threshold, dataset ZIP, v1/v2 manifests and active source hashes reverified unchanged. Existing source and manuscript were snapshotted in `experiments/session_20261006_completion_ui/before/`. Current source/evidence package: `deliverables/MedVision_research_workspace_20261006.zip`. Deadline: 10 October 2026; keep the computer awake for CPU training. Completion time depends on training/evaluation, not queue registration.

Next session: inspect both queue and completion-watch states/logs; preserve failed output and never retune from reserved-test results. If completed, verify selected bundle in the browser, package its new weights separately, inspect measured manuscript/tables and complete human review/formatting. If waiting, monitor training; do not label it finished.

## CURRENT SESSION — 6 October 2026: Phase 6 development evidence and Phase 7 implementation

- **Phase 6 development evaluation executed:** 612 validation images from an immutable completed E2 epoch-1 copy; 19 thresholds × 3 policies; native counts, case confusion, one-to-one region matching, subgroup tables, 1,000 duplicate-group bootstrap replicates, exact table regeneration and failure panels. Positive Dice/sensitivity 0; all 110 positives and 137 regions missed. Do not promote this background-collapse checkpoint. Final model selection, freeze, matched comparisons and reserved-test evaluation remain pending. [Measured report](experiments/P6_development_validation/PHASE6_REPORT.md).

- **Release follow-up:** 10 older results used 127.0.0.1 image URLs, incompatible with the current localhost Strict cookie. Owned image/overlay URLs now derive from UUID-bound saved paths; original history remains intact. API regression and an actual old-history browser revisit verify the fix. Signup/MFA/audit/approval claims are disabled in real builds; login-page copy now states research scope. Final package: `deliverables/MedVision_verified_demo_20261006.zip`.

- **Final reproduction verified:** isolated source copy hashes checked; fresh npm ci/lint/typecheck/7 tests/production build passed, plus 60 security and 61 real original-checkpoint API checks using temporary storage. Final browser rehearsal passed 28 checks. Mobile menu now follows actual header height; launcher disables proxy-header trust to protect IP rate limits. Evidence: `experiments/session_20261006_p6p7/clean_reproduction.json`.

- **Working real application:** transactional SQLite history, account-owned results/images/exports, salted password hashes, revocable 8-hour HttpOnly/SameSite Strict sessions, real refresh/logout, no default public password, origin/host checks, bounded upload sizes/dimensions/time, queue limits and inference timeout with retained worker lock, storage quota and explicit owned deletion. Public generated-files mount removed. Unsupported signup/reset/admin/audit/review/profile controls disabled or replaced. Production mocks forcibly disabled.

- **Frontend issues fixed:** overlapping upload race, authenticated reload restoration, login/logout/expiry cache clearing, expiry timer, API error handling, no-region/uncertain wording, aspect ratio, logout cancellation/placement and working dark palette. Clean npm install/build/lint/typecheck and 7 frontend tests pass.

- **Measured verification:** 60 security/CI checks, 61 real original-checkpoint API checks, 61 real logits-bundle API checks, 27 real browser checks. Browser covers distinct positive/normal validation uploads, protected images, original byte hashes, JSON export, deep-link reload, desktop/mobile/dark mode and logout. Two native masks exactly reproduce historical torch2.9.1 counts under torch2.14.1. [Video](experiments/session_20261006_p6p7/browser/medvision_demo.webm).

- **Dependency fixes:** npm advisory count 12 → 0. A separate `.venv-demo` now uses torch2.14.1+cpu, Pillow12.3.0 and setuptools84.0.0. Its 40-package upstream-version audit has no known advisories or skipped entries; CPU local version normalized solely for advisory lookup. Bandit reports zero findings in the four application modules. The active `.venv-clean` training runtime was preserved; its older dependency advisories remain recorded, and it must not load untrusted checkpoints. [Security report](experiments/session_20261006_p6p7/SECURITY_REVIEW.md).

- **Ongoing experiments:** E2 preserved, latest state `{"status": "training", "latest_epoch": 3, "current_epoch": 4, "batch": 400, "batches": 1408, "mean_train_loss": 1.0036505642533302, "smoke": false}`. Matched v2 BCE+Dice/focal-Tversky runs are **queued**, not measured results: same architecture, letterbox256, blur0, 50% training sampler, seed42, Adam1e-4, batch2, 12-epoch ceilings/patience5, patched CPU runtime. Queue status `waiting_for_E2`; it starts only after E2 completes and rejects changed source/artifact hashes. GPU still Code43. Keep the machine awake; no deadline guarantee is implied by queuing.

- Original checkpoint, threshold, archive, both manifests and active source guards verified unchanged. Project deadline 10 October; user handles 8 October poster, institutional report later. The manuscript remains a measured draft, not a completed final paper. Phase 7's local implementation/rehearsal is done; final selected-model delivery and another teammate's independent reproduction/review remain open.

Next session: inspect E2 and `experiments/session_20261006_p6p7/training_queue.json`; do not start duplicates. Review E3/E4 learning curves, select/calibrate on validation, freeze the complete delivered bundle, then run the reserved test once. Regenerate final tables/figures, replace the diagnostic demo model only after that gate, and complete the research paper with human review.

## HISTORICAL SESSION - 6 October 2026: Phase 4 executed

- Implemented separate `medvision_pipeline.py` / `tools/train_pipeline.py`: configurable letterbox/stretch, padded-pixel exclusion, shared native transforms, explicit v2 manifest, deterministic paired augmentation, training-only controlled sampler, direct logits BCE+Dice / focal Tversky / symmetric Unified Focal, detailed epoch/checkpoint provenance and resume.

- Computational Phase 4 checks pass: empty/thin/multiple masks, padded loss/gradient exclusion, finite extreme-logit losses, independent UF reference, all 919 v2 instances survive letterbox 256 and 512. Elastic review shows hardware/anatomy bending; default off.

- Real two-training-image overfit passed after 60 updates: grid Dice 0.965251 / zero normal predicted pixels; native Dice 0.913160. This is **memorization sanity only**, not validation performance. Four-train/four-val trainer smoke and resume to epoch 2 pass.

- Opt-in `MEDVISION_BUNDLE` backend and real CLI use the exact shared native inference path. API masks match direct inference; bad bundles/logits-as-legacy selection return 503. Historical default upload/overlay/invalid-input regressions still pass. Original demo model remains selected; smoke weights not promoted.

- **E2 first full epoch:** train loss 1.135661; validation at .5 has positive Dice/sensitivity 0, no findings. This is background collapse, not improvement. Measured epoch 74.15 min; ~14.83 h for a 12-epoch ceiling at this rate (early stop/variation apply). Live state snapshot: `{"status": "training", "latest_epoch": 1, "current_epoch": 2, "batch": 100, "batches": 1408, "mean_train_loss": 1.0396958458423615, "smoke": false}`. E2 still uses v1; seven contradictory training targets disclosed. Do not change its source/data on resume.

- Original checkpoint, threshold, ZIP, v1/v2 manifest hashes and active trainer/medvision_ai.py hashes preserved. No test model evaluation/tuning. Evidence: `experiments/phase4_checks/PHASE4_REPORT.md`, `experiments/session_20261006/phase4_ledger.json`.

Next: assess E2 curves/validation; execute a separately named full v2 logits experiment with recorded sampling/config and compute budget, then matched comparisons. Select/calibrate/freeze on validation before final test. Working browser demo and final measured manuscript/package remain due 10 October; poster handled by user, institutional report later.

## HISTORICAL SESSION - 6 October 2026: Phase 3 executed

Phase 2 clean CPU setup and real inference remain verified; GPU is still blocked by Code 43. Project due 10 October; user handles 8 October poster; institutional report deferred.

- Completed Phase 3 source/version/license, subgroup distributions, sampled native annotation review (17 train/validation images), all 217 non-exact candidate-pair reviews and duplicate-label checks. Full evidence: `experiments/phase3_review/DATASET_AUDIT.md` and `DATA_DICTIONARY.md`. Patient independence and expert/guide approval remain unverified.

- Original ZIP matches **FracAtlas v6** by published size and MD5; authoritative version metadata specifies CC BY 4.0. Latest v7 is different and was not downloaded/substituted.

- **New finding:** three exact-decoded sets have fractured/normal label contradictions affecting seven training images. Seventeen exact-copy sets have different union masks; fourteen same-positive annotation disagreements remain documented. No known duplicate/group crosses splits.

- Frozen separate **data_v2** quarantines all seven contradictory images: 4,017 eligible (714 positive / 3,303 normal), train 2,808 (493/2,315), validation 612 and test 597 unchanged. v2 SHA `19a950c34d96c0fc076fbb75bdeffbf2f0b262626817d61018eff31e907544bb`. Existing v1 and E2 are preserved; E2 cannot be represented as training on v2.

- New `tools/train_baseline_manifest.py` consumes audited subset manifests without modifying active trainer/loader source. Four-case train/validation v2 smoke passed; not performance evidence. No duplicate full training job launched.

- E2 snapshot: `{"status": "training", "latest_epoch": 0, "current_epoch": 1, "batch": 1100, "batches": 1408, "mean_train_loss": 1.1594376328858462, "smoke": false}`. Still uses v1 with the disclosed seven contradictory targets. Read live state/logs before continuing; historical model remains the demo model. No test evaluation or tuning performed.

Next: inspect E2 validation when available, keep its protocol/label-noise caveat; use v2 for a separately named new training experiment via the isolated trainer. Never change data/config on E2 resume. Preserve validation/test IDs; select/freeze on validation before final test. Final demo/browser check, measured paper and project packaging remain outstanding.

## CURRENT VERIFIED STATUS - 5 October 2026 session

**Deadline correction from user:** completed project due **10 October 2026**; user handles the 8 October poster. Institutional project report will be worked on later. Exact submission time remains unspecified. This section supersedes the historical figures below, which are preserved as prior records.

### Completed with evidence

- Read the handoff and four supporting documents; preserved existing source snapshots under `experiments/session_20261005/source_snapshot/`. Git resolves to `C:/Users/K SAIRAM`, not a dedicated MedVision repository; no pull, reset, checkout or commit was performed.

- Preserved original dataset, checkpoint and threshold JSON. Checkpoint SHA-256 remains `922f30bf691b9979aee65d386bcf73d2643558c049a7d11ab013fea315f39b81`; dataset SHA-256 `747119b26f2684e0e35a7688083b14b12a206149b0cfe5357824b69b3a5e6cf8`. Archive CRC passes. See `artifacts.json` in the session folder.

- Working `.venv-phase2`: Python 3.13.7, torch 2.9.1+cu128, NumPy 2.3.2, OpenCV 4.13.0, FastAPI 0.136.1. Original empty `.venv` preserved. Recovery environment inherits system packages. A separate **clean `.venv-clean` CPU environment** now reproduces pinned dependency installation, `pip check`, strict checkpoint loading, real API regressions and measured table/figure generation. Its exact transitive versions and evidence are in `clean_environment.freeze.txt`, `clean_runtime_smoke.json`, and `clean_paper_evidence.log`.

- GPU inventory: RTX 3050 6 GB laptop GPU; Windows PnP reports **Code 43**, CUDA sees zero devices, and initialization fails. CUDA wheel installation succeeded; execution uses CPU. No driver/device settings were changed.

- Audited all 4,083 CSV-labelled images: **4,024 usable (717 fractured, 3,307 normal)**; 59 decode failures, all normal, explicitly excluded. 922 polygon annotations checked; dimensions/labels/masks agree for eligible images; no positive union mask vanishes at 256. Exclusions and audit are in `experiments/data_v1/`.

- Frozen grouped split: train **496 positive + 2,319 normal = 2,815**; validation **110 + 502 = 612**; test **111 + 486 = 597**. Manifest SHA-256 `e931cd3d3dce044f7d8f43fefeda596d39d9dc8529453f5262441c1a64e20227`. 78 decoded exact-duplicate groups, 306 perceptual candidate pairs, 3,756 final groups. No sample/group overlap; patient independence unverified and candidate visual review outstanding. Test images received integrity checks but no model evaluation/tuning or qualitative selection.

- Strict historical checkpoint load and finite real-image output verified. Lazy loader now includes audited normals and uses frozen IDs. Preprocessing is shared, fallback/Albumentations seed paths corrected, and research execution fails if real data is absent.

- Corrected delivered semantics: preserve all components, pixel-based presence and area, empty tier not applicable, original-size mask/overlay inversion of the historical stretch, no invented confidence or dashboard accuracy. Checkpoint is cached; concurrent inference bounded. Geometry remains a 256-grid heuristic, not clinical severity.

- Real ASGI and socket HTTP upload/inference checks pass; original bytes, native masks/overlays, history/export and readiness verified. Empty/single-pixel/thin/multiple-mask regressions and 422/415/413 invalid-upload cases pass. Existing frontend tests (4), typecheck, lint, production build pass. First frontend run timed out on a lazy route; subsequent runs passed without weakening assertions.

- Local demo available via `Start-Demo.ps1` and `DEMO.md`, with built frontend served on port 8000, persistent result history and JSON export. Unfinished review controls/audit-admin navigation disabled; password-reset API no longer claims to send emails. Demo authentication remains temporary and API authorization is not implemented.

### Measured experiments (diagnostic, not independent test results)

- E0: 12 updates on one fractured and one normal training image, fresh Attention U-Net initialization, unweighted BCE + Dice. Finite gradients; loss **1.66445 -> 1.46616**. Median two-image step **6.40 s**, peak process memory **2.52 GiB**, approximate full CPU epoch **2.50 h**. This is an execution sanity check, not successful overfitting/generalization evidence.

- E0 clean-environment repeat: median step **1.972 s**, peak **2.13 GiB**, projected full epoch **46.27 minutes**. Use this newer CPU budget estimate; neither benchmark is a full-epoch measurement.

- **E2 corrected baseline is RUNNING in the background**, verified PID **36928** at launch. Fresh Attention U-Net (no historical weights loaded), BCE + Dice, natural-prevalence sampling, no elastic deformation, batch 2, Adam 1e-4, seed 42, max 12 epochs / patience 5. Full train 2,815 and validation 612; no test access. Start/initial-checkpoint recovery and optimizer/epoch resume smoke checks pass. First real optimizer update verified. Source/config/checkpoints/logs are isolated in `experiments/E2_corrected_baseline/`; process record `experiments/session_20261005/E2_process.json`; log `E2_training.log`. Maximum projected duration roughly 9-10 h plus variability; results are not yet available. Original checkpoint remains the demo model until validation selection/calibration and bundle freeze.

- E1: unchanged historical checkpoint, full validation set, **19 thresholds x 3 component policies**, native-coordinate metrics. Retained all-component threshold **0.90**: positive mean Dice **0.482326**, mean IoU **0.361818**, case sensitivity **108/110 = 98.18%**, normal false-positive rate **453/502 = 90.24%**, global Dice **0.182614**. Group-bootstrap positive Dice interval **[0.422685, 0.537538]**.

- Largest-only at 0.90: mean Dice **0.479370**, same case errors. Best qualifying Dice candidate all-components at 0.80: **0.482962**, with **456/502** normal false positives; not adopted. Lowest observed normal FPR was still **444/502 = 88.45%** at threshold 0.95/minimum 16 pixels. Filtering/calibration did not solve normal-case errors; no reliable improvement claim.

- CPU forward timing in E1: median **505.4 ms**, p95 **1,209.5 ms**, first **1,117.8 ms**, excluding preprocessing/postprocessing. Concurrent checks may affect timing; not a controlled benchmark. Full diagnostic comparison **501.4 s**. Historical checkpoint exposure is unknown, so these scores cannot be labelled independently held out.

- Generated `paper/MANUSCRIPT_DRAFT.md`, measured CSV table and figures. Principal table reproduces exactly from saved per-case counts. Draft explicitly states unfinished training/final evaluation/reference/author-review requirements; it is not submission-ready. Institutional report remains deferred.

### Next session - execution order

1. **Inspect the running E2 job first; do not launch a duplicate.** Read `state.json`, `epochs.jsonl`, `best_validation.json`, `E2_training.log` and stderr. Check process identity via `E2_process.json` before taking any action. New clean CPU benchmark projects 46 min/epoch, not the older 2.5 h estimate. Check user response about Code 43 recovery; re-run CUDA initialization before GPU work. Resume only at an epoch boundary with the exact config; commands are in DEMO.md.

2. Inspect perceptual duplicate groups and training/validation image-mask examples; retain frozen group integrity. Clean CPU setup is verified. Confirm frontend clean installation if needed and establish source versioning without using the parent home-directory Git repository.

3. Evaluate the completed fresh E2 baseline using validation only; diagnose curves and normal errors before extending training or choosing a matched focal-Tversky/loss/architecture comparison. Do not treat smoke scores as performance. Historical pretraining exposure requires diagnostic labelling for the old model; E2 starts fresh under frozen groups.

4. Select only on validation; freeze complete model/preprocessing/threshold/component bundle. Keep test set untouched until final evaluation. Preserve original checkpoint/threshold/data and all run artifacts.

5. Verify the UI in a connected browser. No browser was available during this session; HTTP/ASGI checks are not a browser visual demonstration. Complete final latency/failure analysis, manuscript and project packaging by 10 October. Work on institutional report later as requested.

Evidence index: [EXPERIMENT_REGISTRY.md](EXPERIMENT_REGISTRY.md), `experiments/session_20261005/`, `experiments/data_v1/`, `experiments/E0_learning_cpu/`, `experiments/E1_historical_validation/`, [DEMO.md](DEMO.md), [manuscript draft](paper/MANUSCRIPT_DRAFT.md).

## HISTORICAL STATUS - preserved, not current verification

## DATA

- Dataset source: `FracAtlas.zip` in the workspace root.

- Extraction/cache location: `medvision_temp/` is used for extracted demo images.

- Total samples: 717.

- Class balance: 0 empty masks, 717 non-empty masks.

- Positive-pixel percentage across non-empty masks: average 0.495%, minimum 0.061%, maximum 2.997%.

- Split strategy: deterministic stratified split by mask positivity using a fixed seed (`seed=42`). Positive and negative indices are shuffled separately, then split 70/15/15.

- Current split sizes: train 501, validation 107, test 109.

- Augmentation: training-only augmentation is active. If `albumentations` is installed, the code uses `A.Compose` with horizontal flip, rotate, and elastic transform. If it is not installed, the script falls back to a local synchronized augmenter that applies flip, rotation, and elastic warp to image/mask pairs.

## ARCHITECTURE

AttentionUNet is a 4-level binary segmentation U-Net with attention-gated skip connections.

| Stage | Module | Output shape |

| --- | --- | --- |

| Input | Grayscale image | `1 x 256 x 256` |

| Encoder 1 | `ConvBlock(1 -> 64)` | `64 x 256 x 256` |

| Downsample | `MaxPool2d` | `64 x 128 x 128` |

| Encoder 2 | `ConvBlock(64 -> 128)` | `128 x 128 x 128` |

| Downsample | `MaxPool2d` | `128 x 64 x 64` |

| Encoder 3 | `ConvBlock(128 -> 256)` | `256 x 64 x 64` |

| Downsample | `MaxPool2d` | `256 x 32 x 32` |

| Encoder 4 | `ConvBlock(256 -> 512)` | `512 x 32 x 32` |

| Downsample | `MaxPool2d` | `512 x 16 x 16` |

| Bottleneck | `ConvBlock(512 -> 1024)` | `1024 x 16 x 16` |

| Up 4 | `ConvTranspose2d(1024 -> 512)` | `512 x 32 x 32` |

| Attention 4 | `AttentionGate(512, 512, 256)` | `512 x 32 x 32` |

| Decoder 4 | `ConvBlock(1024 -> 512)` | `512 x 32 x 32` |

| Up 3 | `ConvTranspose2d(512 -> 256)` | `256 x 64 x 64` |

| Attention 3 | `AttentionGate(256, 256, 128)` | `256 x 64 x 64` |

| Decoder 3 | `ConvBlock(512 -> 256)` | `256 x 64 x 64` |

| Up 2 | `ConvTranspose2d(256 -> 128)` | `128 x 128 x 128` |

| Attention 2 | `AttentionGate(128, 128, 64)` | `128 x 128 x 128` |

| Decoder 2 | `ConvBlock(256 -> 128)` | `128 x 128 x 128` |

| Up 1 | `ConvTranspose2d(128 -> 64)` | `64 x 256 x 256` |

| Attention 1 | `AttentionGate(64, 64, 32)` | `64 x 256 x 256` |

| Decoder 1 | `ConvBlock(128 -> 64)` | `64 x 256 x 256` |

| Output | `Conv2d(64 -> 1) + Sigmoid` | `1 x 256 x 256` |

- Total parameters: 31,387,045.

- Trainable parameters: 31,387,045.

- Input/output contract: grayscale `256 x 256` input, single-channel sigmoid mask output of the same spatial size.

## TRAINING PIPELINE

- Default loss mode: `focal_tversky`.

- Loss composition: `Dice + focal_tversky` by default.

- Legacy loss mode: `weighted_bce` remains available for compatibility, but its inverse-frequency weight is capped at 25.0 instead of using the raw imbalance ratio directly.

- Weighted BCE details: `pos_weight = min(25.0, max(1.0, (1 - pos_ratio) / (pos_ratio + 1e-6)))`, where `pos_ratio` is estimated from the current training split.

- Optimizer: `Adam`.

- Learning rate: `1e-4`.

- Scheduler: `ReduceLROnPlateau(patience=5)` on validation loss.

- Checkpoint criterion: best validation Dice, saving `best_model.pt` when validation Dice improves.

- Early stopping: patience 8 on validation Dice.

- Max epochs default: 40.

- Batch size default: 8.

- `--max-items` default: `None`, so plain `python medvision_ai.py` uses the full FracAtlas dataset.

- Run summary: the script now prints a one-line config summary at the start of the training run, including dataset size, split sizes, loss mode, epochs, and batch size.

- Loud warning behavior: if `--max-items` is set and the resulting training split contains fewer than 50 positive samples, the script prints a warning that the results are not meaningful.

## INFERENCE PIPELINE

- Image preprocessing: grayscale read, CLAHE contrast enhancement, `3 x 3` Gaussian blur, resize to `256 x 256`, normalize to `[0, 1]`.

- Inference wrapper: `run_medvision_inference` loads or uses the provided model, preprocesses the image, runs the network, thresholds the mask, and passes it to severity assessment.

- Threshold calibration: validation threshold is swept from `0.10` to `0.90` in steps of `0.05`, and the threshold with the best validation Dice is saved to metadata beside the checkpoint.

- Last calibrated threshold recorded in the earlier smoke run: `0.10`.

- Severity logic: the predicted mask is reduced to the largest connected component, then area, perimeter, compactness, and aspect ratio are computed. Severity tiers are heuristic and area-based: `<150` Mild, `<900` Moderate, otherwise Severe.

## LAST RUN RESULTS

- Status: training complete

- Epoch: 40/40

- Train loss: 0.6335

- Validation loss: 0.6333

- Validation Dice: 0.4526

- Validation IoU: 0.2925

- Validation predicted-positive ratio: 0.0076

- Best validation Dice so far: 0.4526

- Best validation loss so far: 0.6333

- Approach: focal_tversky-only objective (no extra Dice term) to lower the loss scale while keeping the sparse-foreground focus

## KNOWN ISSUES

- A tiny `--max-items` value can still be passed intentionally for smoke testing, but it now prints a loud warning when the training split has fewer than 50 positive samples.

- The project still contains a legacy `weighted_bce` option for compatibility, even though `focal_tversky` is the new default.

- Training on the full FracAtlas dataset is CPU-heavy and can take a while before the first epoch summary appears.

- The earlier smoke run with `--max-items 16` was not representative of real training quality and produced unstable metrics.

## LATEST TRAINING RUN

Status: training complete

- Dataset: FracAtlas (717 samples)

- Split: train 501 / val 107 / test 109

- Loss mode: focal_tversky

- Max epochs: 40

- Batch size: 8

- Max items: None

- Approach: focal_tversky-only objective (no extra Dice term) to lower the loss scale while keeping the sparse-foreground focus

- Epoch: 40/40

- Train loss: 0.6335

- Validation loss: 0.6333

- Validation Dice: 0.4526

- Validation IoU: 0.2925

- Validation predicted-positive ratio: 0.0076


Final package follow-up: all 247 archived file identities verified; the actual packaged source also passed 64 temporary-storage security/API checks using the separately installed patched Python runtime. No original dataset/checkpoint/history was copied or changed. Evidence: `experiments/session_20261006_completion_ui/packaged_security.json`; ZIP SHA-256 `30268a7699d6d36387df1357e9d07e9bc8fba891ceaba4e868261ad55d92992c`. Training and completion watcher remain active; final test not yet evaluated.

Current authentication source/evidence release: `deliverables/MedVision_auth_enabled_20261006.zip` (257 file identities verified). This supersedes earlier application packages; original historical packages are preserved. No credentials, recovery secrets, private account database, dataset ZIP or model weights are included.
