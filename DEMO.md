# MedVision local demonstration



## Current patched serving setup (6 October 2026)



The current demo is available at **http://localhost:8000/login**. Run one instance of `./Start-Demo.ps1`; if the recorded demo already owns port 8000, use that instance. Never stop a trainer to free the demo port.



```powershell

py -3.13 -m venv .venv-demo

./.venv-demo/Scripts/python.exe -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu

./.venv-demo/Scripts/python.exe -m pip install -r requirements-demo.lock.txt

./.venv-demo/Scripts/python.exe -m pip check

npm ci

$env:VITE_API_BASE_URL='/'

$env:VITE_USE_MOCKS='false'

npm run build

./Start-Demo.ps1

```



Only the preserved SHA-verified original checkpoint is accepted in legacy mode. New logits checkpoints require `MEDVISION_BUNDLE`; smoke bundles are not finalists. Default original threshold is .90, with unverified historical calibration provenance. The new demo runtime is torch2.14.1+cpu/Pillow12.3.0; the older E2 runtime is intentionally unchanged. A loopback HttpOnly cookie is not Secure because this demo uses HTTP; remote delivery needs TLS/Secure cookies and further operational work. No patient-identifying images.



Current checks (use these authenticated tools instead of historical unauthenticated scripts):



```powershell

./.venv-demo/Scripts/python.exe tools/verify_secure_api.py

./.venv-demo/Scripts/python.exe tools/verify_secure_api.py --real --out experiments/new_real_api_check.json

./.venv-demo/Scripts/python.exe tools/summarize_phase6.py

npm run test

npm run lint

node tools/browser_demo.mjs

```



`--real` uses two validation images, never the test. CI's default deterministic predictor is explicitly separate from the locally executed real-model tests. Browser recording requires Playwright Chromium; set `MEDVISION_BROWSER` to its executable if the cached revision differs. The script needs the launcher-generated password file and prepared fixtures from this session; they are not portable credentials. Video and screenshots are in `experiments/session_20261006_p6p7/browser/`.



Two controlled v2 loss runs are queued in a hidden PowerShell process **after E2 completes**, using the patched runtime. Do not run duplicate E3/E4 commands. Inspect `training_queue.json`, `queue_process.json`, run `state.json`/`epochs.jsonl` and logs in the session directory. If the machine sleeps or E2 stops before completion, the queue waits; it cannot guarantee the 10 October deadline. If guards fail it stops and preserves outputs. New-run source changes invalidate the queued guard hashes. E2 source/config/artifacts must remain unchanged while it runs. Final calibration/freeze/test is not automated by this queue.





## Historical execution details



Project completion deadline: **10 October 2026**. The user handles the 8 October poster; the institutional project report is deferred to a later session.



## Start the existing verified installation



From this folder in PowerShell:



```powershell

npm run build

./Start-Demo.ps1

```



Open **http://localhost:8000/login**. Use `demo.clinician@example.invalid` and the locally generated password in `.local_demo/demo_password.txt`, or your existing `MEDVISION_DEMO_PASSWORD` if that account was provisioned with it. SQLite preserves the original account hash; changing the environment later does not silently reset it. The launcher binds to loopback. Sessions, analyses, exports and images are protected server-side.



Upload `medvision_temp/IMG0000019.jpg` or another decodable research JPG/PNG. Wait for the results page. Compare the original image with its original-size overlay. Export the result JSON, then open History and revisit the result. Completed results/history survive a server restart; accounts persist in the private local SQLite database. Clinical review controls and unfinished audit/admin navigation are disabled.



The built frontend and API use port 8000. `.env.local` already specifies real inference and was preserved. For Vite development on port 5173, run `npm run dev` in another terminal while the backend runs. Both paths use real weights; mocked tests do not establish browser integration.



## Environment reproduction



The previous `.venv` is preserved but empty. `.venv-clean` is a separate clean CPU environment: dependency installation, `pip check`, strict checkpoint loading and real API regression checks pass there. The active E2 still uses it; serving now uses the separately installed patched `.venv-demo`. Exact versions/evidence are in `experiments/session_20261005/clean_environment.freeze.txt` and `clean_runtime_smoke.json`. `.venv-phase2` is the CUDA recovery environment and inherits system packages; its original evidence is in `cuda_runtime_smoke.json`. The manifest supports Python 3.13 rather than requiring NumPy 1.x.



The clean CPU setup was reproduced with:



```powershell

py -3.13 -m venv .venv-clean

./.venv-clean/Scripts/python.exe -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cpu

./.venv-clean/Scripts/python.exe -m pip install -r requirements.txt

./.venv-clean/Scripts/python.exe -m pip check

```



CUDA install command used in the recovery environment:



```powershell

./.venv-phase2/Scripts/python.exe -m pip install 'torch==2.9.1+cu128' --index-url https://download.pytorch.org/whl/cu128

```



This matches [PyTorch's versioned wheel instructions](https://pytorch.org/get-started/previous-versions/). Installation succeeded, but Windows reports RTX 3050 device **Code 43** and CUDA sees zero devices. CPU inference works. Driver/device recovery is required before GPU experiments; no drivers or device settings were changed. The patched launcher currently rejects `-UseCuda`; recover the driver and validate a separately patched CUDA environment before selecting it.



## Safe verification and experiments



```powershell

./.venv-phase2/Scripts/python.exe tools/verify_runtime.py

./.venv-phase2/Scripts/python.exe tools/run_experiment.py evaluate --out experiments/E1_repeat_unique_id

./.venv-phase2/Scripts/python.exe tools/run_experiment.py learning-sanity --out experiments/E0_repeat_unique_id --steps 12

```



Evaluation defaults to validation and never trains. Existing experiment directories cannot be overwritten. Test access requires an explicit `--final-test`; do not use it until model/configuration selection is frozen. The historical checkpoint has unknown training exposure, so its results are diagnostic, not independently held-out scores. The legacy training CLI now refuses root checkpoint overwrites and requires real data.



Original artifacts remain `best_model.pt`, `best_model_threshold.json`, and `FracAtlas.zip`. Their before-session hashes are recorded in `experiments/session_20261005/artifacts.json`. The original threshold 0.9 is retained; its historical calibration provenance is unverified. The serving policy now preserves all components and uses pixel presence, with descriptive geometry measured on the 256x256 model grid. Mask images and overlays are mapped to original dimensions by nearest-neighbor inverse scaling of the historical square-stretch transform.



## Evidence and limits



Exact check logs, measured results and remaining limitations are indexed in `EXPERIMENT_REGISTRY.md`. The clean CPU setup and real API work; final model evaluation remains pending; actual desktop/mobile browser verification and a video are now recorded in the 6 October Phase 6/7 session.



## Running corrected baseline and resumption



A fresh normal-inclusive baseline is running in the background in `experiments/E2_corrected_baseline/`. Launch process identity is recorded in `experiments/session_20261005/E2_process.json` (PID 36928 at launch). The 12-epoch ceiling projects roughly 9-10 hours from the clean CPU step benchmark, with early stopping and real epoch times determining actual duration. Training continues while the machine stays awake. Do not launch a second copy.



Read `state.json` and `epochs.jsonl` in the run directory and `experiments/session_20261005/E2_training.log` / `.stderr.log` for progress. Checkpoints are atomic: `last.pt` includes model/optimizer and last completed epoch; `best_model.pt` is selected by native-coordinate mean positive validation Dice at threshold .5, with earlier-epoch ties. An initial epoch-0 checkpoint allows recovery even before the first epoch completes. If interrupted, work from the last completed epoch; partial-epoch work is replayed deterministically.



After confirming the original process has stopped, resume from the project root:



```powershell

.\.venv-clean\Scripts\python.exe tools/train_baseline.py --out experiments/E2_corrected_baseline --epochs 12 --batch-size 2 --loss bce_dice --patience 5 --resume

```



Do not change model/preprocessing/trainer source during a resumable run: source/config hashes are checked. A restored GPU can use `.venv-phase2` with the same resume command only after the CPU process stops; compute-environment changes are logged. Select/calibrate on validation, freeze the bundle, and then perform the final test. The demo continues using the original checkpoint until those checks pass. The fresh model is not claimed to improve anything yet.



To regenerate paper evidence in the clean environment:



```powershell

.\.venv-clean\Scripts\python.exe -m pip install -r requirements-research.txt

.\.venv-clean\Scripts\python.exe tools/build_evidence.py

```



Safe inference-only CLI (choose a new output directory):



```powershell

.\.venv-clean\Scripts\python.exe tools/predict.py --image medvision_temp/IMG0000019.jpg --out experiments/new_inference_id

```



Automated real-model API verification covers two different uploaded dataset images, original byte retrieval, native-size masks/overlays, empty/thin/multiple-mask semantics, and invalid upload responses. The current session used installed Playwright/Chromium for actual browser verification; the previous lack-of-browser limitation has been resolved. Frontend typechecking, tests, lint, build and HTTP asset delivery are recorded separately. Full training, patient-independent validation and clinical severity validation remain outstanding.



## New Phase 4 logits pipeline (6 October)



The default demo still uses the original historical sigmoid model. New logits weights require a versioned bundle; they cannot be passed as a legacy checkpoint. No smoke/overfit bundle is a selected demo model. Use the same native transform for training, validation and serving. See `experiments/phase4_checks/PHASE4_REPORT.md` for measured checks and limitations.



After checking the existing full CPU job status, start a **new**, explicitly named v2 run (example config, not yet executed):



```powershell

.\.venv-clean\Scripts\python.exe tools/train_pipeline.py --out experiments/E3_v2_logits_bce --epochs 12 --size 256 --loss bce_dice --positive-fraction 0.5

```



Preprocessing flags include `--resize letterbox|stretch`, `--size 256|512`, `--no-clahe`, `--blur 0|3`, and `--normalization unit|zscore`. Loss choices: `bce_dice`, `focal_tversky`, `unified_focal_symmetric`. Omit `--positive-fraction` for natural sampling. Elastic is off; inspected candidate bends hardware/anatomy and has no clinical plausibility approval. Exact flags/source/manifest must match on `--resume`; do not resume E2 using this trainer.



Versioned real inference command (replace paths with the selected/frozen bundle when available):



```powershell

.\.venv-clean\Scripts\python.exe tools/predict_bundle.py --image path/to/xray.jpg --bundle experiments/SELECTED_RUN/bundle.json --out experiments/NEW_INFERENCE

```



For an explicitly selected new backend bundle, set `$env:MEDVISION_BUNDLE` to its absolute bundle.json path before `Start-Demo.ps1`. Leave it unset for the historical default. Bundle metadata/checksum, preprocessing, output contract, threshold and component policy are verified. Unselected research bundles disclose their status; clinical severity is unavailable. Clear the variable with `Remove-Item Env:MEDVISION_BUNDLE` when returning to the historical demo.



Measured E2 epoch 1 took 74.15 minutes and predicted no validation findings at .5. Earlier 9–10-hour projection is superseded by actual timing (~14.83h for 12 comparable epochs, early stopping/variation applies). E2 remains a v1 run with the seven contradictory training targets. No test evaluation performed.


## Current research workspace and completion workflow

The real dashboard now includes case activity and experiment progress. Open Research for frozen split counts, live validation records and methodology. The original diagnostic model remains active until controlled v2 evaluation and selected-model API verification finish. `tools/watch_completion.ps1` is already running; do not start a duplicate. Its durable state is `experiments/session_20261006_completion_ui/completion_watch.json`. Successful execution produces `experiments/FINAL_v2_20261006/FROZEN_SELECTION.json`, per-model validation/reserved_test outputs, `paper/MEASURED_RESEARCH_PAPER.md` and a verified `deployment.json`. Start-Demo.ps1 selects that bundle on its next launch after verifying its recorded hash and completed test/API flags. You can explicitly set MEDVISION_BUNDLE to another trusted, verified research bundle. Original best_model.pt is never overwritten.

Current source/evidence package: `deliverables/MedVision_research_workspace_20261006.zip`. Updated browser video: `experiments/session_20261006_completion_ui/browser/medvision_demo.webm`. Final browser review of the future selected model and independent human reproduction are still required.

## Sign-in, signup and account recovery

Start-Demo.ps1 explicitly enables demo prefill only for the loopback demo account. Open `/login` and click Sign in; use your own email/password for a personal account. `/signup` creates a persistent account and displays a recovery code once: save it privately. `/forgot-password` checks email plus that code and opens `/reset-password` with a ten-minute grant in the URL fragment. Successful reset invalidates old sessions and rotates the recovery code. No email is sent. The local owner can read the shared demo recovery code from `.local_demo/demo_recovery_code.txt`; for a lost personal code, run `.venv-demo/Scripts/python.exe tools/reissue_recovery.py --email address`. The owner command prints a replacement privately and invalidates prior codes/grants without deleting case history.

Current authentication source/evidence release: `deliverables/MedVision_auth_enabled_20261006.zip` (257 file identities verified). This supersedes earlier application packages; original historical packages are preserved. No credentials, recovery secrets, private account database, dataset ZIP or model weights are included.
