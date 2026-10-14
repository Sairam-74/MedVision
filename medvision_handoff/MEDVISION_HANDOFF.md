# MedVision AI — start here

## CURRENT SESSION — 6 October 2026: Working demo sign-in, signup and recovery

- Restored demo credential prefill for explicitly enabled loopback launches using the actual current demo password; no universal static password and no personal-account prefill. Browser confirmed the owner's real demo signs in without typing credentials. Signup-created accounts retain their email and a blank password on the sign-in page. Better credential/rate-limit/connectivity errors replace generic failures.
- Fixed signup's missing useState import; preserved the owner's current signup/recovery routes and links. Real signup persists salted password hashes, assigns only the ordinary technician role and returns a recovery code once. Duplicate addresses and invalid/short credentials are rejected; signup is rate-limited with a local account quota.
- Forgot Password now verifies email plus the saved recovery code, then routes to a ten-minute reset grant in a URL fragment. Single-use grants are stored as hashes. A successful reset revokes all previous sessions and recovery keys, returns a new code once and clears the used token from the visible URL. Invalid/expired/used grants fail clearly; no fallback demo-token or false-success screen. No email service is configured, so the UI does not claim to send messages. Shared demo recovery code: .local_demo/demo_recovery_code.txt. Lost personal code: owner-only local command `python tools/reissue_recovery.py --email address` using .venv-demo; not an HTTP endpoint.
- Passed 31 account-lifecycle checks, 16 actual-browser auth checks, 65 real original-inference API checks and 9 frontend tests; lint/typecheck/build and Bandit pass. Test accounts lived in separate disposable/private storage. No recovery codes/passwords were written into test reports, screenshots or videos. Evidence: `experiments/session_20261006_auth/verification.json`. Actual demo remains on localhost:8000; isolated test server stopped.
- Original checkpoint/dataset/manifests/active training source hashes remain unchanged; existing accounts and case history preserved. Source before this session is in `experiments/session_20261006_auth/before/`. Training remains active. Completion watcher was re-registered solely after updating the manuscript generator's auth description; training queue and validation/test selection protocol are unchanged. No final-result or completed-paper claim.

## CURRENT SESSION — 6 October 2026: Information-rich frontend and guarded research completion

- Rebuilt dashboard and sign-in with navy/blue/cyan styling, strong contrast, a persistent navigation rail, real case activity, workflow guidance and useful research context. Upload and result pages now explain the workflow, output, model identity, native dimensions and operating threshold. Fixed the global anchor-style override that suppressed intended link/button colours. Desktop, mobile and dark screenshots and a fresh real-inference video are in `../experiments/session_20261006_completion_ui/browser/`.
- Added authenticated `/api/research` and `/research`: frozen-manifest counts, live completed-epoch metrics, queue status, historical-exposure caveat, normal false alarms, dataset provenance and expandable methodology. Queued runs have no invented metrics; final-test/model status is explicit. Scientific evidence is projected through a fixed whitelist without credentials, patient history, internal guards or arbitrary path access.
- Verification: **64** backend security checks, **65** actual original-model API checks, **65** actual logits-bundle API checks, **32** browser checks, **7** frontend tests; lint/typecheck/production build pass. Bandit across application and new research tools: zero findings. Native count/policy parity and saved-table reproduction passed on four validation images; smoke/final-test rejection and string-labelled normal parsing verified. Evidence: `../experiments/session_20261006_completion_ui/verification.json`.
- New measured E2 development observation: best completed epoch 6, positive Dice 0.191464, sensitivity 0.972727, normal false-positive rate 0.942231 (473/502 normal cases falsely flagged). This supersedes the zero-Dice epoch-1 snapshot as latest training evidence, not as a final model. Live snapshot: `{"status": "training", "latest_epoch": 6, "current_epoch": 7, "batch": 800, "batches": 1408, "mean_train_loss": 0.9822001187503338, "smoke": false}`. E2 remains v1; its sources/environment/data were preserved.
- **Completion execution is active:** existing E2 → E3 → E4 training queue is unchanged. Separate source/artifact-guarded watcher waits for `completed_training_only`, calibrates both full v2 models on validation, freezes both operating points and the validation-only winner, evaluates each frozen model once on the reserved test, saves native per-case/subgroup/region/bootstrap results, regenerates the measured paper, and checks the selected model against the real API. It writes a verified deployment record only after those checks; the launcher selects it on the next launch. No current final-test access, finalist promotion or completed-paper claim. Process and protocol: `../experiments/session_20261006_completion_ui/completion_watch_process.json`, `completion_watch.json`, `completion_protocol.json`. Do not launch duplicate watchers/trainers or alter guarded sources without inspecting/re-registering.
- Research manuscript rewritten from actual data and saved epoch records: `../paper/MANUSCRIPT_DRAFT.md`. It replaces stale authentication/browser/audit descriptions and retains pending comparison markers. On successful final evaluation, the watcher generates `../paper/MEASURED_RESEARCH_PAPER.md` and `controlled_results.csv`. Author agreement, guide/technical review, independent reproduction, venue/reference requirements and final formatting remain external outstanding steps; the institutional report remains deferred as requested.
- Original checkpoint, threshold, dataset ZIP, v1/v2 manifests and active source hashes reverified unchanged. Existing source and manuscript were snapshotted in `../experiments/session_20261006_completion_ui/before/`. Current source/evidence package: `deliverables/MedVision_research_workspace_20261006.zip`. Deadline: 10 October 2026; keep the computer awake for CPU training. Completion time depends on training/evaluation, not queue registration.

Next session: inspect both queue and completion-watch states/logs; preserve failed output and never retune from reserved-test results. If completed, verify selected bundle in the browser, package its new weights separately, inspect measured manuscript/tables and complete human review/formatting. If waiting, monitor training; do not label it finished.

## CURRENT SESSION — 6 October 2026: Phase 6 development evidence and Phase 7 implementation

- **Phase 6 development evaluation executed:** 612 validation images from an immutable completed E2 epoch-1 copy; 19 thresholds × 3 policies; native counts, case confusion, one-to-one region matching, subgroup tables, 1,000 duplicate-group bootstrap replicates, exact table regeneration and failure panels. Positive Dice/sensitivity 0; all 110 positives and 137 regions missed. Do not promote this background-collapse checkpoint. Final model selection, freeze, matched comparisons and reserved-test evaluation remain pending. [Measured report](../experiments/P6_development_validation/PHASE6_REPORT.md).

- **Release follow-up:** 10 older results used 127.0.0.1 image URLs, incompatible with the current localhost Strict cookie. Owned image/overlay URLs now derive from UUID-bound saved paths; original history remains intact. API regression and an actual old-history browser revisit verify the fix. Signup/MFA/audit/approval claims are disabled in real builds; login-page copy now states research scope. Final package: `deliverables/MedVision_verified_demo_20261006.zip`.

- **Final reproduction verified:** isolated source copy hashes checked; fresh npm ci/lint/typecheck/7 tests/production build passed, plus 60 security and 61 real original-checkpoint API checks using temporary storage. Final browser rehearsal passed 28 checks. Mobile menu now follows actual header height; launcher disables proxy-header trust to protect IP rate limits. Evidence: `experiments/session_20261006_p6p7/clean_reproduction.json`.

- **Working real application:** transactional SQLite history, account-owned results/images/exports, salted password hashes, revocable 8-hour HttpOnly/SameSite Strict sessions, real refresh/logout, no default public password, origin/host checks, bounded upload sizes/dimensions/time, queue limits and inference timeout with retained worker lock, storage quota and explicit owned deletion. Public generated-files mount removed. Unsupported signup/reset/admin/audit/review/profile controls disabled or replaced. Production mocks forcibly disabled.

- **Frontend issues fixed:** overlapping upload race, authenticated reload restoration, login/logout/expiry cache clearing, expiry timer, API error handling, no-region/uncertain wording, aspect ratio, logout cancellation/placement and working dark palette. Clean npm install/build/lint/typecheck and 7 frontend tests pass.

- **Measured verification:** 60 security/CI checks, 61 real original-checkpoint API checks, 61 real logits-bundle API checks, 27 real browser checks. Browser covers distinct positive/normal validation uploads, protected images, original byte hashes, JSON export, deep-link reload, desktop/mobile/dark mode and logout. Two native masks exactly reproduce historical torch2.9.1 counts under torch2.14.1. [Video](../experiments/session_20261006_p6p7/browser/medvision_demo.webm).

- **Dependency fixes:** npm advisory count 12 → 0. A separate `.venv-demo` now uses torch2.14.1+cpu, Pillow12.3.0 and setuptools84.0.0. Its 40-package upstream-version audit has no known advisories or skipped entries; CPU local version normalized solely for advisory lookup. Bandit reports zero findings in the four application modules. The active `.venv-clean` training runtime was preserved; its older dependency advisories remain recorded, and it must not load untrusted checkpoints. [Security report](../experiments/session_20261006_p6p7/SECURITY_REVIEW.md).

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

Prepared 5 October 2026. **Latest user correction: completed project due 10 October 2026. User handles the poster on 8 October; institutional project report will be worked on later.** Exact submission time remains unknown. This supersedes the original 8 October project target and earlier documents saying the deadline is unknown.

## Executed session update - 5 October 2026

Phase 2 and initial correctness/diagnostic experiments have now been executed. Read the top of `PROJECT_STATUS.md` and `EXPERIMENT_REGISTRY.md` before resuming; the older audit documents below describe pre-execution findings.

- Originals preserved: checkpoint SHA matches this handoff, ZIP CRC passes. Dataset/image audit excludes 59 unreadable normal images, leaving 4,024 eligible (717 fractured/3,307 normal) and 922 annotations.

- Frozen grouped manifests are in `experiments/data_v1`; train 2,815, validation 612, test 597. Patient grouping is unknown; conservative perceptual candidate visual review remains open. Do not replace splits or inspect test performance during tuning.

- `.venv-phase2` works with inherited system dependencies and CUDA-enabled torch 2.9.1+cu128. A separate clean `.venv-clean` installation now reproduces the pinned CPU runtime, API regressions and measured paper table/figures. `Start-Demo.ps1` defaults to the clean CPU environment. GPU remains unavailable: **Windows RTX 3050 Code 43**, zero CUDA devices. No driver/device change performed. User was asked about GPU recovery/alternate compute.

- Strict checkpoint forward and actual ASGI/socket HTTP inference pass. Lazy loader includes normals; components preserved; thin/empty semantics fixed; confidence/94% dashboard claims removed; native overlays, cached model/concurrency, history and export implemented. Local loopback demo: `Start-Demo.ps1`, see `DEMO.md`. No browser connected for visual UI verification.

- E0 two-image 12-step BCE+Dice sanity: finite gradients, loss 1.66445 -> 1.46616; ~6.40 s/step and ~2.50 h/full CPU epoch. This is not a trained final model.

- Clean CPU repeat is much faster: **1.972 s/step, ~46.27 min/full epoch projection**. A fresh normal-inclusive E2 baseline is now **running in the background**, PID 36928 at launch; full train 2,815/val 612, BCE+Dice, batch 2, 12-epoch ceiling/patience 5. Recovery/resume tests passed and first optimizer update was verified. Inspect `experiments/E2_corrected_baseline/state.json` and session `E2_training.log`/`E2_process.json` before any new training. No model-performance results are available yet; do not launch a duplicate or overwrite its checkpoint. Original checkpoint still powers the demo.

- E1 unchanged model, 57 validation threshold/policy comparisons: at .9/all, mean positive Dice .482326, sensitivity 108/110, **normal false positives 453/502 (90.24%)**. Threshold/filtering does not solve this. Historical model exposure unknown; diagnostic only. Original .9 threshold retained; no final test evaluated.

- `paper/MANUSCRIPT_DRAFT.md` and measured figures/tables exist; exact principal-table reproduction passes. Draft is not submission-ready; new normal-inclusive training, controlled comparison, final evaluation and author/guide review remain needed. Institutional report is deferred.

- Git resolves to the user's home directory rather than a project-local repository. Preserve source snapshots and scope all operations; no Git reset/pull/commit was performed.

Next execution: resolve GPU or budget feasible CPU training; inspect grouping candidates; run corrected baseline in a new run directory; validate/select and freeze; final test once; verify real browser demo; finalize measured paper and project package by 10 October. Preserve writing/verification time and all originals. No publication/submission claim or guarantee.

## Context and goals

Continue Adarsh's MedVision project: https://github.com/Sairam-74/MedVision. PyTorch Attention U-Net, FastAPI backend, React frontend, FracAtlas X-rays. User requested a detailed project/prerequisite audit, post-2020 research with source links and explanations of usefulness, an implementation checklist ending in an original research paper, and execution of Phase 1. Four enclosed documents preserve that work. Research proposals are hypotheses, not measured gains.

Phase 1 scope/protocol planning is prepared. Guide approval and proposed team-role acceptance remain unverified. No new training results or backend improvements were verified in this planning session. Read the included documents before changing code. Local code may be newer than the audited checkout (1e310c280450f3efc8fbb123ed9815332119170b); inspect current git status and diff before applying findings.

## Important audit findings to verify locally

- Supplied FracAtlas audit: 4,083 images, 717 fractured and 3,366 normal; COCO has 717 positive images and 922 annotations. Existing loader omitted normals. Check image/mask alignment, duplicates and split leakage before experiments.

- Existing custom split was 501/107/109 positive images; official positive split CSVs were 574/82/61. Freeze a documented split and keep test data out of tuning. Historical checkpoint exposure may make it diagnostic only.

- Documented validation Dice 0.4526 and IoU 0.2925 are historical, not reproduced test scores. Threshold JSON uses 0.9 and validation Dice 0.4586593828436439; checkpoint association needs verification.

- Preserve original checkpoint. The audited checkpoint SHA256 was 922f30bf691b9979aee65d386bcf73d2643558c049a7d11ab013fea315f39b81. Static archive inspection did not establish successful inference.

- Training entry point also trains before evaluation: create a safe evaluation-only path before running it.

- Largest-component filtering discards multiple fractures. Contour area may be zero for a thin nonempty mask; case presence should follow surviving mask pixels. Empty masks must not return Mild severity.

- Match evaluator and served postprocessing. Preserve/invert image transforms for original-coordinate overlays.

- Geometry-based severity is not clinically validated. Hardcoded confidence and default mock mode must not appear as real predictions.

- Check frontend/backend port mismatch, actual API connectivity, upload validation and error handling. Prioritize local real-inference demo over unfinished admin/auth workflows.

- Verify actual loss code: default focal Tversky; do not describe an unimplemented combination. Keep manuscript architecture, loss, epochs and measured latency consistent with experiments.

## First local work session

1. Read existing AGENTS.md instructions and all enclosed documents. Inspect current repository changes without overwriting user work or pulling blindly.

2. Inventory Python, dependency versions, NVIDIA GPU/VRAM, CUDA and torch CUDA availability; determine a compatible environment from actual package constraints. Screenshot showed Python 3.13.7, but compatibility has not been checked.

3. Validate local FracAtlas.zip, extracted annotations and checkpoint; do not require a new upload to ChatGPT if the local copy is usable.

4. Run safe model-load/forward and real API inference smoke checks. Record exact commands, errors and measured outputs.

5. Execute Phase 2 prerequisites and data validation, then core correctness fixes and a reproducible baseline. Update the master checklist only on evidence.

6. Maintain PROJECT_STATUS.md, experiment/run registry and this handoff after each session so new chats can resume. Preserve existing status content and distinguish completed, blocked and proposed work.

## Deadline plan (target, not completion guarantee)

| Date | Priority and evidence |

|---|---|

| Oct 5 | Local environment/data/checkpoint validation; freeze scope and split; unblock real inference |

| Oct 6 | Restore GPU/confirm compute; inspect grouped data; train normal-inclusive baseline in a new run directory |

| Oct 7 | Run a feasible matched comparison; save validation results and failure analysis |

| Oct 8 | Poster handled by user; continue validation-only selection and freeze final model/config |

| Oct 9 | Final evaluation after freeze; browser demo verification; reconcile measured manuscript and reproducibility package |

| Oct 10 | Completed project delivery; exact time unknown. Institutional report deferred to a later session |

Aim for a defensible working prototype and complete experimental manuscript. Do not promise accuracy gains or publication acceptance. If hardware/time prevents multiple seeds or broad ablations, report exactly what ran and its limitations; never invent results. Preserve final verification/writing time rather than starting an unfinishable experiment. Confirm the deadline time and guide format while progressing with executable tasks.

## Evidence and source continuity

The enclosed research study includes source links and how each source informs proposed improvements. It does not demonstrate those improvements already worked on this project. Use verified primary references in the final paper and check bibliographic details. Research paper outcome is an original experimental manuscript, not only a literature survey.

## VS Code starter prompt

Read medvision_handoff/MEDVISION_HANDOFF.md and all four supporting documents. Continue MedVision toward 10 October 2026. Inspect my current code and preserve local changes, dataset and original checkpoint. Begin with Phase 2: verify prerequisites, GPU, dataset, splits, model loading and real inference; then implement the highest-priority pipeline correctness fixes, establish a reproducible baseline and run feasible controlled improvements. Keep PROJECT_STATUS.md and the experiment registry current. Finish with a working demo and a research paper supported only by measured results. Do the work rather than only proposing another plan; ask when essential information is genuinely missing.

