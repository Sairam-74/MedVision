"""Create a reviewed-source reproduction archive, excluding credentials and weights."""
import hashlib
import argparse
import json
from pathlib import Path
import shutil
import zipfile
parser=argparse.ArgumentParser()
parser.add_argument('--release',default='MedVision_reproduction_20261006')
args=parser.parse_args()
assert args.release and all(c.isalnum() or c in '_-' for c in args.release), 'Use a plain release name'
ROOT=Path(__file__).resolve().parents[1]
SESSION=ROOT/'experiments/session_20261006_p6p7'
target=ROOT/'deliverables'/args.release
assert not target.exists(), 'Do not overwrite a deliverable; choose a new release ID'
target.mkdir(parents=True)
top=['README.md','DEMO.md','PROJECT_STATUS.md','EXPERIMENT_REGISTRY.md','requirements.txt','requirements-demo.txt','requirements-demo.lock.txt',
     'requirements-research.txt','package.json','package-lock.json','.npmrc','.gitignore','.env.example','index.html',
     'vite.config.ts','vitest.config.ts','tailwind.config.ts','postcss.config.js','eslint.config.js',
     'tsconfig.json','tsconfig.app.json','tsconfig.node.json','Start-Demo.ps1','medvision_ai.py','medvision_pipeline.py',
     'medvision_serving.py','backend_service.py','app_store.py','research_status.py','best_model_threshold.json']
files=[ROOT/name for name in top if (ROOT/name).is_file()]
for folder in ['src','public','tools','.github','medvision_handoff','experiments/data_v1','experiments/data_v2','experiments/phase3_review']:
    files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix.lower() in {'.py','.ps1','.mjs','.js','.ts','.tsx','.css','.html','.json','.txt','.csv','.md','.yml','.png','.sha256'})
for folder in ['experiments/P6_development_validation','experiments/E1_historical_validation']:
    files.extend(p for p in (ROOT/folder).glob('*') if p.is_file() and p.suffix.lower() in {'.json','.csv','.md','.svg','.png'})
for name in ['MANUSCRIPT_DRAFT.md','measured_results.csv','table_reproduction.json']:
    if (ROOT/'paper'/name).is_file(): files.append(ROOT/'paper'/name)
for name in ['SECURITY_REVIEW.md','clean_reproduction.json','clean_source_security.json','clean_source_real.json','session_finalized.json','secure_api_final.json','secure_api_real_final.json','secure_bundle_api.json','serving_parity.json',
             'region_matching_checks.json','npm_audit_before.json','npm_audit_after.json','python_audit.json','python_demo_audit_final.json','bandit_final.json','demo_environment.txt','demo_audit_upstream_versions.txt']:
    files.append(SESSION/name)
for name in ['browser_checks.json','medvision_demo.webm','desktop_dashboard.png','desktop_history.png','mobile_upload.png','mobile_dark_upload.png','IMG0000019.jpg_result.png','IMG0000008.jpg_result.png']:
    files.append(SESSION/'browser'/name)
inventory={}
auth_session=ROOT/'experiments/session_20261006_auth'
for name in ['SESSION_REPORT.md','verification.json','auth_checks.json','browser_auth_checks.json','real_api_checks.json','bandit.json','actual_demo_dashboard.png']:
    files.append(auth_session/name)
new_session=ROOT/'experiments/session_20261006_completion_ui'
for name in ['SESSION_REPORT.md','verification.json','completion_watch.json','completion_protocol.json','security_checks.json','real_api_checks.json','bundle_api_checks.json','bandit.json']:
    files.append(new_session/name)
for name in ['browser_checks.json','medvision_demo.webm','desktop_dashboard.png','desktop_research.png','mobile_dashboard.png','mobile_research.png','mobile_upload.png','mobile_dark_upload.png','IMG0000019.jpg_result.png','IMG0000008.jpg_result.png']:
    files.append(new_session/'browser'/name)
for source in sorted(set(files)):
    if '__pycache__' in source.parts or not source.is_file(): continue
    relative=source.relative_to(ROOT)
    assert '.local_demo' not in relative.parts and source.suffix not in ('.pt','.sqlite3','.npz')
    destination=target/relative;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
    inventory[relative.as_posix()]=hashlib.sha256(destination.read_bytes()).hexdigest()
source_files={name:digest for name,digest in inventory.items() if not name.startswith(('experiments/','paper/','medvision_handoff/')) and not name.endswith('.md')}
source_id=hashlib.sha256(json.dumps(source_files,sort_keys=True).encode()).hexdigest()
manifest={'source_snapshot_sha256':source_id,'git_commit':None,'reason':'Parent Git root is user home; preserved isolated source snapshot instead of home-wide Git changes.',
          'files':inventory,'model_sha256':'922f30bf691b9979aee65d386bcf73d2643558c049a7d11ab013fea315f39b81',
          'archive_sha256':'747119b26f2684e0e35a7688083b14b12a206149b0cfe5357824b69b3a5e6cf8',
          'excluded':'weights, dataset archive, private database, credentials, uploaded-image history, environment folders; provided separately by owner/retrieval',
          'final_test_evaluated':False,'final_model_frozen':False}
(target/'SOURCE_MANIFEST.json').write_text(json.dumps(manifest,indent=2))
(target/'REPRODUCTION.md').write_text('''# Reproduce the local research demonstration

This is a source/evidence package for the original diagnostic model. It is not the final trained-model release. Read PROJECT_STATUS and DEMO first; final selection/test/paper gates remain open.

1. Verify each file against SOURCE_MANIFEST.json. It records a source snapshot ID rather than a Git commit because the working Git root is the owner's home directory.
2. Obtain FracAtlas **v6**, DOI https://doi.org/10.6084/m9.figshare.22363012.v6. Verify 338,412,750 bytes, MD5 931dd40ad6e070bb0724d66cfbbef9f0, and the archive SHA in SOURCE_MANIFEST. Do not substitute another version. License CC BY 4.0: https://creativecommons.org/licenses/by/4.0/. Attribute Abedeen et al., Scientific Data 10,521 (2023), DOI https://doi.org/10.1038/s41597-023-02432-4. Manifest exclusions/grouping and example resize/overlay changes are described in the data audit.
3. Get the original best_model.pt from the project owner and verify its exact SHA. The model is excluded here; its redistribution permissions are unverified. Retain included original best_model_threshold.json (.90). Put both the model and dataset ZIP at the project root. No private credentials/database/history are packaged.
4. Use Python3.13 and Node22. Create .venv-demo and install torch2.14.1 from the official CPU index first; then install requirements-demo.lock.txt, run pip check and npm ci. Set VITE_API_BASE_URL=/ and VITE_USE_MOCKS=false for npm run build. See DEMO for exact PowerShell commands.
5. Run Start-Demo.ps1. It generates a new password in .local_demo/demo_password.txt, creates hashed SQLite account storage, and binds loopback port8000. Sign in as demo.clinician@example.invalid. Upload research JPG/PNG, compare original/overlay, export JSON and revisit History after restarting. No diagnosis or clinical severity is validated.
6. Run tools/verify_secure_api.py for deterministic-predictor security checks; --real additionally requires the archive/model and tests two validation uploads. New logits checkpoints need a separately provided/generated versioned bundle; --bundle selects it. CI does not have patient data or pretrained weights.
7. Run npm run lint, npm run typecheck, npm run test and npm run build. Tests use explicit mocks; real API/browser checks are separate. Recorded real video is in experiments/session_20261006_p6p7/browser/medvision_demo.webm. Browser fixtures/password paths are workspace-specific; generate your own input selections/session before rerecording.
8. Regenerate development tables with tools/summarize_phase6.py. Saved integer counts reproduce without the model; qualitative panels need the dataset. They show a failed epoch-1 E2 snapshot, not the finalist. Do not run historical root-output finalization scripts over newer status files. Use new experiment IDs. Do not start duplicate queued trainers.

Current software supports a local demonstration with durable account-owned results. Final calibrated-model selection, reserved-test evaluation, matched final comparisons, final paper and another teammate's review/reproduction are not claimed complete. A remote deployment additionally needs TLS/Secure cookies and operational controls.
''',encoding='utf-8')
archive=ROOT/'deliverables'/(args.release+'.zip')
assert not archive.exists()
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for item in sorted(target.rglob('*')):
        if item.is_file(): z.write(item,item.relative_to(target).as_posix())
with zipfile.ZipFile(archive) as z:
    for name,digest in inventory.items(): assert hashlib.sha256(z.read(name)).hexdigest()==digest,name
record={'package':str(archive.relative_to(ROOT)),'package_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
        'source_snapshot_sha256':source_id,'files':len(inventory),'size_bytes':archive.stat().st_size,'inventory_verified':True}
existing=SESSION/'reproduction_package.json'
if existing.exists() and not (SESSION/'reproduction_package_v1.json').exists(): shutil.copy2(existing,SESSION/'reproduction_package_v1.json')
existing.write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))
