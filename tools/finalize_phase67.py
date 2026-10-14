"""Record this completed implementation session; never modify model/data artifacts."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
SESSION=ROOT/'experiments/session_20261006_p6p7'

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(name): return json.loads((SESSION/name).read_text(encoding='utf-8-sig'))
def main():
    assert not (SESSION/'session_finalized.json').exists(), 'Session already recorded; append later work separately'
    security=read('secure_api_final.json'); real=read('secure_api_real_final.json'); bundle=read('secure_bundle_api.json')
    browser=read('browser/browser_checks.json'); npm=read('npm_audit_after.json'); python=read('python_demo_audit_final.json')
    frontend=7
    assert '7 passed' in (SESSION/'frontend_tests.log').read_text(encoding='utf-8'), 'Frontend tests not yet verified'
    assert npm['metadata']['vulnerabilities']['total']==0
    assert not any(d.get('vulns') or d.get('skip_reason') for d in python['dependencies'])
    assert not read('bandit_final.json')['results']
    protected={'best_model.pt':'922f30bf691b9979aee65d386bcf73d2643558c049a7d11ab013fea315f39b81',
               'FracAtlas.zip':'747119b26f2684e0e35a7688083b14b12a206149b0cfe5357824b69b3a5e6cf8',
               'best_model_threshold.json':'02d33de4874bcb22816225b8c0834123388f90505a16a3953b7e452a103e3830',
               'experiments/data_v1/manifest.json':'e931cd3d3dce044f7d8f43fefeda596d39d9dc8529453f5262441c1a64e20227',
               'experiments/data_v2/manifest.json':'19a950c34d96c0fc076fbb75bdeffbf2f0b262626817d61018eff31e907544bb'}
    for path,expected in protected.items(): assert sha(ROOT/path)==expected,path
    active=json.loads((ROOT/'experiments/E2_corrected_baseline/config.json').read_text())
    guard=active.get('source_hashes',active.get('code_sha256',{}))
    if active.get('source_sha256'):
        guard={'tools/train_baseline.py':active['source_sha256'],'medvision_ai.py':active['medvision_source_sha256']}
    if isinstance(guard,dict):
        for path,expected in guard.items(): assert sha(ROOT/path)==expected,path
    backup=SESSION/'documents_before_finalize'; backup.mkdir(exist_ok=True)
    docs=['PROJECT_STATUS.md','EXPERIMENT_REGISTRY.md','DEMO.md','README.md','medvision_handoff/MEDVISION_HANDOFF.md',
          'medvision_handoff/MedVision_Master_Todo_and_Research_Paper_Roadmap.md','paper/MANUSCRIPT_DRAFT.md']
    for name in docs:
        target=backup/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    live=json.loads((ROOT/'experiments/E2_corrected_baseline/state.json').read_text())
    queue=read('training_queue.json')
    summary=f'''## CURRENT SESSION — 6 October 2026: Phase 6 development evidence and Phase 7 implementation

- **Phase 6 development evaluation executed:** 612 validation images from an immutable completed E2 epoch-1 copy; 19 thresholds × 3 policies; native counts, case confusion, one-to-one region matching, subgroup tables, 1,000 duplicate-group bootstrap replicates, exact table regeneration and failure panels. Positive Dice/sensitivity 0; all 110 positives and 137 regions missed. Do not promote this background-collapse checkpoint. Final model selection, freeze, matched comparisons and reserved-test evaluation remain pending. [Measured report](experiments/P6_development_validation/PHASE6_REPORT.md).
- **Working real application:** transactional SQLite history, account-owned results/images/exports, salted password hashes, revocable 8-hour HttpOnly/SameSite Strict sessions, real refresh/logout, no default public password, origin/host checks, bounded upload sizes/dimensions/time, queue limits and inference timeout with retained worker lock, storage quota and explicit owned deletion. Public generated-files mount removed. Unsupported signup/reset/admin/audit/review/profile controls disabled or replaced. Production mocks forcibly disabled.
- **Frontend issues fixed:** overlapping upload race, authenticated reload restoration, login/logout/expiry cache clearing, expiry timer, API error handling, no-region/uncertain wording, aspect ratio, logout cancellation/placement and working dark palette. Clean npm install/build/lint/typecheck and {frontend} frontend tests pass.
- **Measured verification:** {security['checks_passed']} security/CI checks, {real['checks_passed']} real original-checkpoint API checks, {bundle['checks_passed']} real logits-bundle API checks, {browser['checks_passed']} real browser checks. Browser covers distinct positive/normal validation uploads, protected images, original byte hashes, JSON export, deep-link reload, desktop/mobile/dark mode and logout. Two native masks exactly reproduce historical torch2.9.1 counts under torch2.14.1. [Video](experiments/session_20261006_p6p7/browser/medvision_demo.webm).
- **Dependency fixes:** npm advisory count 12 → 0. A separate `.venv-demo` now uses torch2.14.1+cpu, Pillow12.3.0 and setuptools84.0.0. Its {len(python['dependencies'])}-package upstream-version audit has no known advisories or skipped entries; CPU local version normalized solely for advisory lookup. Bandit reports zero findings in the four application modules. The active `.venv-clean` training runtime was preserved; its older dependency advisories remain recorded, and it must not load untrusted checkpoints. [Security report](experiments/session_20261006_p6p7/SECURITY_REVIEW.md).
- **Ongoing experiments:** E2 preserved, latest state `{json.dumps(live)}`. Matched v2 BCE+Dice/focal-Tversky runs are **queued**, not measured results: same architecture, letterbox256, blur0, 50% training sampler, seed42, Adam1e-4, batch2, 12-epoch ceilings/patience5, patched CPU runtime. Queue status `{queue['status']}`; it starts only after E2 completes and rejects changed source/artifact hashes. GPU still Code43. Keep the machine awake; no deadline guarantee is implied by queuing.
- Original checkpoint, threshold, archive, both manifests and active source guards verified unchanged. Project deadline 10 October; user handles 8 October poster, institutional report later. The manuscript remains a measured draft, not a completed final paper. Phase 7's local implementation/rehearsal is done; final selected-model delivery and another teammate's independent reproduction/review remain open.

Next session: inspect E2 and `experiments/session_20261006_p6p7/training_queue.json`; do not start duplicates. Review E3/E4 learning curves, select/calibrate on validation, freeze the complete delivered bundle, then run the reserved test once. Regenerate final tables/figures, replace the diagnostic demo model only after that gate, and complete the research paper with human review.

'''
    for name in ['PROJECT_STATUS.md','medvision_handoff/MEDVISION_HANDOFF.md']:
        path=ROOT/name;text=path.read_text(encoding='utf-8');first,rest=text.split('\n',1)
        section=summary.replace('](experiments/','](../experiments/') if name.startswith('medvision_handoff/') else summary
        path.write_text(first+'\n\n'+section+rest.replace('## CURRENT SESSION','## HISTORICAL SESSION'),encoding='utf-8')
    registry=ROOT/'EXPERIMENT_REGISTRY.md'
    with registry.open('a',encoding='utf-8') as f:
        f.write(f'''\n## 6 October: Phase 6 / Phase 7 / security session

| Run | Status | Actual result / limit | Evidence |
|---|---|---|---|
| P6-development-validation | Complete, development only | Frozen epoch-1 E2 copy; 612 val, 110 positives/502 normals; Dice/sensitivity 0; region recall 0/137 at IoU .10/.50. No test; no promotion | `experiments/P6_development_validation/` |
| P7-security-CI | Passed | {security['checks_passed']} checks, deterministic predictor; auth/ownership/traversal/limits/timeout/persistence/session tests | `secure_api_final.json` in this session |
| P7-real-original-API | Passed | {real['checks_passed']} checks; two distinct val X-rays; exact direct inference masks, protected original/overlay/export | `secure_api_real_final.json` |
| P7-real-logits-API | Passed, smoke bundle only | {bundle['checks_passed']} checks; native masks equal shared inference; not a selected model | `secure_bundle_api.json` |
| P7-browser | Passed | {browser['checks_passed']} checks; actual login/upload/result/history/export/reload/mobile/dark/logout; original model predicts a region on normal example | `browser/browser_checks.json`, `browser/medvision_demo.webm` |
| P7-runtime-parity | Passed for two images | torch2.14.1 browser-native integer counts equal archived torch2.9.1 counts; not exhaustive | `serving_parity.json` |
| P7-dependency-security | Passed known-advisory scan | npm 0; {len(python['dependencies'])} Python upstream versions 0/skipped0; Bandit0. Training environment retained separately | `SECURITY_REVIEW.md` and audit JSONs |
| P7-patched-trainer-smoke | Passed execution only | Four train/four val, one epoch; torch2.14.1+cpu; Dice0 is not performance evidence | `experiments/P7_patched_trainer_smoke/` |
| E3-v2-logits-BCE+Dice | **QUEUED after E2** | letterbox256, blur0, sampler.5, batch2, seed42, Adam1e-4, 12 epochs/patience5; no result claimed | `training_queue.json`, `queue_process.json` |
| E4-v2-logits-focal-Tversky | **QUEUED after E3** | Same controlled settings, loss changed only; no result claimed | same queue record |

Local demo uses `.venv-demo` and the preserved original .90/all checkpoint. Final-test/model-freeze and final-paper gates remain open. The active E2 is v1, not the new v2 runs. See current PROJECT_STATUS and DEMO instructions; historical unauthenticated verification scripts are archival and must not be used as current API tests.
''')
    roadmap=ROOT/'medvision_handoff/MedVision_Master_Todo_and_Research_Paper_Roadmap.md'
    text=roadmap.read_text(encoding='utf-8')
    for number in ['7.3','7.5','7.6','7.7','7.8','7.9','7.11','7.12']:
        text=text.replace(f'- [ ] **{number}**',f'- [x] **{number}**')
    text=text.replace('## Phase 6 — Freeze the model and produce final evidence','''## Phase 6 — Freeze the model and produce final evidence

6 October update: development counterparts of 6.3–6.8 and 6.10–6.13 table regeneration/claim audit executed; final checkboxes remain open because the selected full model and matched comparisons are unfinished. See `experiments/P6_development_validation/PHASE6_REPORT.md`. No teammate review is claimed. Test remains reserved.''')
    text=text.replace('## Phase 7 — Finish the real application and reproducibility package','''## Phase 7 — Finish the real application and reproducibility package

6 October update: local implementation, isolated dependency installation, lockfile reproduction, real original/bundle API tests and recorded browser rehearsal executed. Source version uses a SHA-256 snapshot because the Git root is the user's home directory; no home-wide Git action was performed. Final selected-model delivery and another teammate's independent reproduction remain open. See `experiments/session_20261006_p6p7/SECURITY_REVIEW.md`.''')
    roadmap.write_text(text,encoding='utf-8')
    demo=ROOT/'DEMO.md';text=demo.read_text(encoding='utf-8')
    text=text.replace('Use the local account `demo.clinician@example.invalid` with `password123` (unless you set `MEDVISION_DEMO_PASSWORD` yourself). This is temporary local demo authentication; the API is not authenticated. The launcher binds to loopback.',
                      'Use `demo.clinician@example.invalid` and the locally generated password in `.local_demo/demo_password.txt`, or your existing `MEDVISION_DEMO_PASSWORD` if that account was provisioned with it. SQLite preserves the original account hash; changing the environment later does not silently reset it. The launcher binds to loopback. Sessions, analyses, exports and images are protected server-side.')
    text=text.replace('temporary accounts do not.','accounts persist in the private local SQLite database.')
    text=text.replace('`Start-Demo.ps1` uses it by default.','The active E2 still uses it; serving now uses the separately installed patched `.venv-demo`.')
    text=text.replace('After restoring CUDA, `./Start-Demo.ps1 -UseCuda` selects the recovery environment.','The patched launcher currently rejects `-UseCuda`; recover the driver and validate a separately patched CUDA environment before selecting it.')
    text=text.replace('final model evaluation and browser verification remain pending.','final model evaluation remains pending; actual desktop/mobile browser verification and a video are now recorded in the 6 October Phase 6/7 session.')
    text=text.replace('Browser verification requires a connected browser; none was available during this session.','The current session used installed Playwright/Chromium for actual browser verification; the previous lack-of-browser limitation has been resolved.')
    text=text.replace('~9-10 hours','~14.83 hours at the measured first-epoch rate')
    patched='''## Current patched serving setup (6 October 2026)

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

'''
    demo.write_text('# MedVision local demonstration\n\n'+patched+'\n## Historical execution details\n'+text.split('\n',1)[1],encoding='utf-8')
    paper=ROOT/'paper/MANUSCRIPT_DRAFT.md'
    with paper.open('a',encoding='utf-8') as f:
        f.write('''\n## 6 October measured development and application addendum

A completed epoch-1 snapshot of the fresh v1 E2 baseline was evaluated on all 612 validation images (110 positive, 502 normal). Positive Dice and IoU were 0; case TP/FN/FP/TN were 0/110/0/502. One-to-one region matching recovered 0 of 137 annotated regions at both IoU >= .10 and >= .50. No predictions were produced at the admissible .10/all setting; therefore pixel/case precision is undefined. Specificity 100% results from background collapse and does not establish utility. This checkpoint was not promoted. The threshold/policy sweep, exact native counts, subgroup results, clustered-bootstrap conventions and negative examples are archived in `experiments/P6_development_validation/`. Degenerate all-zero bootstrap intervals are not zero population-risk claims. Training/controlled comparisons remain unfinished; no independent final test was performed.

The working local application now uses authenticated account-owned SQLite history, protected images, bounded upload/inference work and a patched CPU serving runtime. Real original and logits-bundle API tests, exact evaluation/serving mask comparisons, browser evidence, current dependency audits and source provenance are recorded in `experiments/session_20261006_p6p7/`. Browser demonstration includes a normal image with a false-positive region, consistent with the historical model's high normal false-positive rate; this application demonstration is not a clinical-validation study. Two examples exactly reproduce historical native integer counts after the torch runtime update, but exhaustive cross-runtime equivalence is not claimed. Final model comparison/test tables and human review are still required before this draft becomes a final paper.
''')
    report=f'''# Frontend, backend and security review — 6 October 2026

Scope: source inspection, dependency audits, actual multipart/model inference, application persistence/auth/ownership tests and desktop/mobile browser QA. The existing source was snapshotted before implementation. Original data, checkpoints, split manifests and active training source guards are preserved.

| Finding | Implemented fix | Verification |
|---|---|---|
| Unauthenticated analyses, exports and static generated files/history JSON | Server-side session checks, exact owned image routes, no public generated-directory mount | Anonymous requests denied; other-account result/image/export/delete denied; traversal rejected |
| Shared bearer token, plaintext accounts, unrestricted refresh | Salted PBKDF2-SHA256 (600,000 iterations), token hashes in SQLite, 8-hour revocable HttpOnly/Strict cookies, real refresh/logout | Valid/invalid/expired/revoked sessions; no bearer credential in response; rate-limited guesses |
| Password123 default and temporary-account placeholders | Launcher-generated private local password; persisted account hash; disable signup/reset/admin/audit/review placeholders | Browser login; API 501 for unsupported provisioning; no published default/password prefill |
| Unbounded jobs, hanging workers, storage exhaustion | 8 tracked jobs, 2 active per account, single inference lock, 30s queue/60s inference deadlines; retain lock until timed-out thread exits; 100-case/512MiB quota and owned deletion | Timeout/lock lifecycle, active delete409, quota409, persistence reopen |
| Malformed, oversized or slow uploads | Maintained multipart parser, actual JPEG/PNG decode and format restriction, 10MiB body/8192 dimension/25M-pixel limits, 15s body-read deadline, one upload-validation slot | Invalid signature415, decode422, size/dimensions413; origin403/host400 |
| Unknown/misinterpreted checkpoints | SHA-approved legacy model only; explicit logits bundle with strict hash/contract loading | Unknown legacy / invalid bundle503; direct API masks exactly match both inference paths |
| Session reload and cached cross-account UI data | Deduplicated cookie refresh on startup; clear query cache on logout/expiry; protected image requests | Real browser protected deep-link reload and logout denial |
| Overlapping uploads, missing errors, misleading status | Disable concurrent intake; track own job; explicit errors; no-region/uncertain states; remove fake review/profile interactions | Frontend 6 tests plus actual uploads/browser |
| Dark theme/mobile layout did not work correctly | Dark tokens, intake colours, logout dialog cancellation and footer placement, aspect preservation | Visually reviewed desktop/mobile/dark screenshots; no page overflow/runtime exceptions |
| Vulnerable frontend dependencies | Compatible patched router, Vitest and Tailwind/PostCSS migration, explicit testing peer and lockfile | npm advisory count 12 before → 0; clean npm ci/build/lint/typecheck/test |
| Older Python serving dependencies | Separate .venv-demo: torch2.14.1+cpu, Pillow12.3.0, setuptools84.0.0; exact runtime lock | {len(python['dependencies'])} upstream package versions audited; 0 known advisories, 0 skips; pip check passes |

Executed checks: **{security['checks_passed']}** deterministic-predictor security/backend checks; **{real['checks_passed']}** actual original-checkpoint API checks; **{bundle['checks_passed']}** actual logits-bundle API checks; **{browser['checks_passed']}** browser checks; **{frontend}** frontend tests. Bandit reports zero findings for backend_service/app_store/medvision_serving/medvision_pipeline. CI configuration was updated; no remote GitHub Actions run is claimed.

The initial pinned Python audit reported 41 advisory records across torch2.9.1 and Pillow12.0.0. The serving runtime is patched; the active training runtime is preserved. Torch's official [weights-only loader advisory](https://github.com/pytorch/pytorch/security/advisories/GHSA-63cw-57p8-fm3p) confirms <=2.9.1 is affected and >=2.10.0 patched. The new runtime also restricts legacy weights to the preserved hash and offers no checkpoint-upload endpoint. Pillow's [12.3.0 release notes](https://pillow.readthedocs.io/en/stable/releasenotes/12.3.0.html) document its security fixes. Password storage follows a salted standard-library PBKDF2 implementation; [OWASP password-storage guidance](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) provides the algorithm/work-factor context.

`python_demo_audit_final.json` audits the installed freeze with `torch2.14.1+cpu` mapped to its upstream `2.14.1` identifier only for advisory lookup. This is not a binary-wheel integrity audit. Original CPU-wheel freeze and the normalized audit inputs are both retained. Automated scans are bounded evidence, not proof of absence of vulnerabilities.

The server is loopback-only HTTP. Remote deployment still needs TLS/Secure cookies, managed provisioning/recovery, operational monitoring and a human security review; no shared deployment was performed. Local SQLite/history/credential files are private application files excluded from source packaging, not encrypted medical-record storage. Only research images are appropriate. Legacy single-demo-user history was imported to that same account without altering its original JSON or claiming verified patient ownership. Timed-out native threads cannot be killed safely: their lock remains occupied until completion; a permanently hung worker requires server recovery.

Actual browser upload-to-visible-result timings (two examples only, concurrent E2, not a p95 benchmark): {', '.join(f'{v:.1f} ms' for v in browser['upload_to_visible_result_ms'])}. Phase 6 forward timing is measured separately on 612 validation images. Original normal example has a predicted region; it is a known false positive, not a normal-case success. Smoke logits weights were never promoted.

Reproduction uses a content-addressed source snapshot because the parent Git root is the user's home directory. No home-wide Git operation, checkpoint overwrite, dataset replacement or driver change occurred. Phase 6 final research gates, delivery of the eventual selected model and independent teammate reproduction/review remain open.
'''
    (SESSION/'SECURITY_REVIEW.md').write_text(report,encoding='utf-8')
    ledger={'protected_hashes':protected,'active_source_guards':guard,'E2_state':live,'queue_status':queue['status'],
            'checks':{'CI_security':security['checks_passed'],'real_original':real['checks_passed'],'real_bundle':bundle['checks_passed'],'browser':browser['checks_passed'],'frontend':frontend},
            'final_test_evaluated':False,'final_selected_model_frozen':False,'source_snapshot':'to be packaged separately'}
    (SESSION/'session_finalized.json').write_text(json.dumps(ledger,indent=2))
    print(json.dumps(ledger['checks'],indent=2))

if __name__=='__main__': main()
