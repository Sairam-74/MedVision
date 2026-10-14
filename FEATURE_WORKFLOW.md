# MedVision radiologist workflow — isolated development

This is the independent feature clone of the preserved MedVision research prototype. It is not a clinically validated diagnostic service. Use synthetic or authorized de-identified research data.

## Preserved original and Git branches

- Original: `C:/Users/K SAIRAM/OneDrive/Desktop/MedVision/`
- Independent clone: `C:/Users/K SAIRAM/OneDrive/Desktop/MedVision-Feature-Development/`
- Repository: https://github.com/Sairam-74/MedVision
- Backup branch: `backup/pre-feature-development-2026-10-14`
- Backup/start commit: `500c76edccb0020415940286a95cf4aac82cc161`
- Feature branch: `feature/medvision-radiologist-workflow`

The original initially had no project-level Git metadata. With explicit authorization, its repository was established from existing GitHub history, without modifying the unrelated home-directory repository. The backup was explicitly approved for public publication and verified by matching `git ls-remote` to the local commit. Feature development occurred exclusively in the independent clone. Original tracked-file SHA-256 hashes were checked against the pre-feature manifest and all matched.

Secrets, account/password files, SQLite databases, uploaded images, corrected masks, generated candidates, environment directories and test screenshots are ignored. Required checkpoint/data binaries remain local: `best_model.pt` and the authorized de-identified `FracAtlas.zip`; see BACKUP_RECORD.json for hashes. The pre-existing public synthetic/example images are retained. No new patient images or private application state are committed.

## What changed

- Additive SQLite migration, with foreign-key enforcement, owned patients/studies, study images linked to existing cases, report versions, feedback, training jobs, model versions and model events. Existing authentication and analyses are retained.
- Patient-first intake with persistent backend identifiers, concurrent uniqueness, returning-patient search and distinct records for matching names. Each patient can have multiple studies.
- AP/lateral/oblique study uploads and independent per-image inference. View selection/comparison and saved image/result retrieval. No multi-view fusion claim.
- Shared-transform original/mask/overlay viewer: bounded 1–8x fit zoom, wheel zoom, drag pan, fit/reset, real brightness/contrast percentages, separate reset controls and overlay opacity. Display changes never alter stored input. Invalid native mask dimensions fail inference or hide overlay.
- Segmentation-only output with model identity and server timestamps. Bone, anatomical fracture position, subtype, displacement, angulation, heatmap, calibrated case confidence and clinical severity are explicitly unsupported/unavailable. Connected-region counts are mask measurements, not clinical classifications.
- Structured editable reports from persisted patient/examination and genuine outputs. Accept/reject/correct suggestions, revision conflict detection, save/finalize/reopen, original AI draft preservation, timestamps/reviewer IDs, JSON export and browser print/Save PDF. Regeneration retains prior revisions. Finalized reports must reopen before edits or additional views.
- Backend patient/name/identifier study search, date/body-part/laterality/analysis/report filters, validated pagination and account ownership on Dashboard/History. UI searches use POST bodies to keep names/identifiers out of request URLs; the feature launcher disables routine access logs. Prior studies reload persisted views/results/reports.
- Clinician feedback: correct/incorrect categories, comments, corrected findings, optional native binary-mask upload, separate human confirmation and training eligibility. Confirmed masks are immutable. Research permission, partition review and matching the documented train cohort are required for training. Unknown/held-out records remain review records and cannot enter routine retraining. Latest eligible correction per decoded image counts toward the threshold; duplicate uploads cannot inflate it.
- Persistent threshold-triggered jobs and authorized manual jobs, separate-process real training through tools/train_pipeline.py, reviewed train-mask overrides, frozen dataset hashes and reserved-test exclusion. Candidate artifacts never overwrite production. Missing/failed/interrupted jobs have honest states and authorized retry; retries create a new run directory. Worker PIDs identify surviving jobs after restart.
- Candidate/baseline validation records include confusion counts, accuracy/precision/recall/specificity/F1, Dice/IoU and explicitly experimental localization overlap. Calibration/robustness unavailable. Promotion requires 463 validation images, >=79/83 positive detections, >=342/380 normal rejections, no sensitivity/specificity regression, improved Dice/IoU/localization, and verified patient independence. Changed baseline/bundle blocks promotion. Admin-only promotion and checksum-verified retained-model rollback have audit events.
- Research screen displays registry/feedback/job state and traceable metrics. Feature sessions use `medvision_feature_session`, separate from the original service's cookie.

## Known scientific limits and unverified operations

A real one-epoch smoke candidate was trained and evaluated on **four validation images only**, while real production inference continued. The candidate was rejected and production was not promoted. This is execution evidence, not an accuracy-improvement experiment. No reserved test images were evaluated.

The frozen manifest says `patient_independence_verified=false`. Consequently, production promotion remains blocked. Full-budget feedback retraining and full 463-image candidate validation have not been executed in this feature task. A genuinely accepted candidate and live production promotion/rollback after such validation remain unverified. Gate logic and rollback were tested separately with clearly identified disposable fixtures; those fixtures are not model evaluation evidence.

Clinical finding heads require suitable expert annotations and validated methodology; they have not been fabricated. New external feedback cohorts need independently documented patient-level partitions and supervised annotation integration before training eligibility can expand beyond the documented cohort. PDF export uses the browser's Print/Save PDF facility rather than a server-side PDF generator.

## Install a fresh isolated environment

The current clone already has its own `.venv-feature` and `node_modules`. Python dependency files were physically copied into a newly created virtual environment from the installed serving environment, and `pip check` passed. They are not links to original source or writable application state.

For a fresh installation, use PowerShell inside this clone:

```powershell
Set-Location -LiteralPath 'C:\Users\K SAIRAM\OneDrive\Desktop\MedVision-Feature-Development'
py -3.13 -m venv .venv-feature
.\.venv-feature\Scripts\python.exe -m pip install --upgrade pip
.\.venv-feature\Scripts\python.exe -m pip install torch==2.14.1+cpu --index-url https://download.pytorch.org/whl/cpu
.\.venv-feature\Scripts\python.exe -m pip install -r requirements-demo.lock.txt
.\.venv-feature\Scripts\python.exe -m pip check
npm.cmd ci
```

The large binaries are deliberately not on GitHub. Obtain the owner-authorized checkpoint/archive locally, copy them into this clone, and verify their hashes against BACKUP_RECORD.json. Do not configure paths back to the original project. Training uses the committed frozen manifest and workflow_config.json hashes; dataset changes require a separately documented protocol and evaluation, not casual editing.

## Migrate and run

```powershell
$env:MEDVISION_DB = Join-Path $PWD '.feature_data/app.sqlite3'
$env:MEDVISION_GENERATED_DIR = Join-Path $PWD '.feature_data/storage'
$env:MEDVISION_CHECKPOINT = Join-Path $PWD 'best_model.pt'
Remove-Item Env:MEDVISION_BUNDLE -ErrorAction SilentlyContinue
.\.venv-feature\Scripts\python.exe tools/setup_feature.py
$env:VITE_API_BASE_URL = '/'
$env:VITE_USE_MOCKS = 'false'
npm.cmd run build
.\Start-Feature.ps1 -Port 8001
```

Migration is additive/idempotent and runs during setup/service initialization. The served frontend and backend are both at http://localhost:8001/login. The original can continue at port 8000. Use `feature.clinician@example.invalid` or `feature.admin@example.invalid`; generated passwords live only in `.feature_data/clinician_password.txt` and `.feature_data/admin_password.txt`. Setup does not reset existing account passwords. The feature database/storage/candidates are inside this clone; no original database, upload or model directory is used.

For a separate frontend development process, leave the feature backend on 8001 and use a second PowerShell terminal:

```powershell
$env:VITE_API_BASE_URL = 'http://localhost:8001'
$env:VITE_USE_MOCKS = 'false'
npm.cmd run dev -- --port 5174
```

Restart only this clone's server when Python code changes. The locally launched background test service PID is recorded in `.feature_data/server.pid`; verify its executable/command before stopping it. `Start-Feature.ps1` runs in the foreground, so Ctrl+C stops that instance. Do not launch a second instance on an occupied port.

## Run verification

```powershell
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run test
$env:VITE_API_BASE_URL = '/'; $env:VITE_USE_MOCKS = 'false'
npm.cmd run build
.\.venv-feature\Scripts\python.exe tools/verify_auth.py
.\.venv-feature\Scripts\python.exe tools/verify_secure_api.py --out test-results/baseline-security.json
.\.venv-feature\Scripts\python.exe tools/verify_workflow.py
.\.venv-feature\Scripts\python.exe tools/verify_workflow.py --real
.\.venv-feature\Scripts\python.exe tools/verify_job_policy.py
.\.venv-feature\Scripts\python.exe tools/verify_retraining.py
node tools/browser_workflow.mjs
```

Browser tests require the feature server on 8001, local generated accounts and Chrome at the installed path, or `MEDVISION_BROWSER` pointing to another compatible browser. They create only synthetic patient records and synthetic gradient images. `verify_retraining.py` uses known de-identified training-cohort annotations and a four-image validation smoke; its candidate is deliberately ineligible for promotion. Test results and screenshots stay local in test-results. A fresh browser test creates a synthetic gradient fixture automatically.

## Retry training safely

Use an admin account on Research. Inspect the job state and its local log under the configured storage's `training_logs/<job-id>.log`. Fix missing authorized artifacts or environment problems first, then choose **Retry safely** for failed/interrupted/blocked jobs (`POST /retraining/jobs/{id}/retry`). Retries retain the same job audit record and create a fresh candidate output directory instead of overwriting the failed run. Rejected scientifically evaluated candidates are retained and require a new job/experiment, not forced promotion. Production remains available throughout training. `MEDVISION_FEEDBACK_THRESHOLD` may set a positive distinct-image threshold; default 10. Do not lower validation targets or use the reserved test set for tuning.

## Recovery and later review

Return to `C:/Users/K SAIRAM/OneDrive/Desktop/MedVision/` and run its unchanged Start-Demo.ps1 for the preserved pre-feature application. Its backup branch and local artifacts remain available. To recover elsewhere, clone the backup branch and restore owner-authorized local artifacts; do not reset or overwrite existing work.

Review the feature branch against the backup branch on GitHub. The GitHub default branch still contains the older initial state; this feature branch also includes the separately preserved local pre-feature updates. Inspect both parts before choosing a PR base. No automatic merge or force push was used. Merge only after review and resolving the scientific/operational limits above; retain the backup branch for recovery.
