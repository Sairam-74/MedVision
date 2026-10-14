"""Persist the measured session ledger and final source hashes for reliable resumption."""
import hashlib
import json
from pathlib import Path
import shutil
import re


def sha(path):
    with open(path,'rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    session = Path('experiments/session_20261005')
    before = json.loads((session/'artifacts.json').read_text())
    originals = {f:sha(f) for f in ['best_model.pt','best_model_threshold.json','FracAtlas.zip']}
    assert all(v==before[k]['sha256'] for k,v in originals.items())
    # Revise only identified stale phrases; retain all other handoff/status text.
    updates = {
        'DEMO.md': [('Full training, clean-environment setup, patient-independent validation', 'Full training, patient-independent validation')],
        'medvision_handoff/MEDVISION_HANDOFF.md': [('Continue MedVision toward 8 October 2026.', 'Continue MedVision toward 10 October 2026.')],
        'tools/build_evidence.py': [('The recovery environment inherits global packages; clean-environment reproduction is outstanding.', 'The recovery environment inherits global packages. A separate clean CPU installation from the pinned requirements reproduced strict loading, API checks and table/figure regeneration.')],
    }
    for filename,pairs in updates.items():
        path = Path(filename)
        text = path.read_text(encoding='utf-8')
        for old,new in pairs:
            text = text.replace(old,new)
        path.write_text(text,encoding='utf-8')
    checklist = Path('medvision_handoff/MedVision_Master_Todo_and_Research_Paper_Roadmap.md')
    text = checklist.read_text(encoding='utf-8')
    completed_tasks = ['2.1','2.3','2.7','2.9','2.10','3.2','3.3','3.5','3.6','3.8','3.9','3.11','4.1','4.12','4.13','4.15','4.16','5.1','5.14','7.1','7.2','7.4','7.10']
    for task in completed_tasks:
        text = text.replace(f'- [ ] **{task}**',f'- [x] **{task}**')
    note = '\nExecution update 5 October 2026: checked tasks have evidence in PROJECT_STATUS.md and EXPERIMENT_REGISTRY.md. Project due 10 October; poster handled by user on 8 October; institutional report deferred. Clean CPU runtime and real inference are verified. E2 normal-inclusive training is running; calibration/final test/browser verification/manuscript review remain open. GPU has Windows Code 43. Original artifacts are preserved; historical checkpoint scores are diagnostic.\n'
    if 'Execution update 5 October 2026:' not in text:
        text = text.replace('Prepared: 4 October 2026','Prepared: 4 October 2026\n'+note)
    checklist.write_text(text,encoding='utf-8')
    files = [Path(f) for f in ['medvision_ai.py','backend_service.py','requirements.txt','requirements-research.txt','Start-Demo.ps1','DEMO.md','PROJECT_STATUS.md','EXPERIMENT_REGISTRY.md','eslint.config.js','.env.example','.gitignore']]
    files += list(Path('tools').glob('*.py'))
    files += [Path(f) for f in ['src/pages/ResultsPage.tsx','src/pages/DashboardPage.tsx','src/pages/LoginPage.tsx','src/components/layout/AppShell.tsx','src/types/analysis.ts','src/utils/env.ts']]
    files += [Path('README.md'),checklist,Path('medvision_handoff/MEDVISION_HANDOFF.md')]
    destination = session/'source_final'
    for f in files:
        target = destination/f
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(f,target)
    ledger = {'session':'2026-10-05','project_deadline':'2026-10-10','poster_user_managed':'2026-10-08','institutional_report':'deferred by user',
              'original_hashes_unchanged':originals,'final_source_sha256':{str(f):sha(f) for f in files},
              'runs':[
                  {'id':'P2-clean','status':'passed','command':'python -m venv .venv-clean; .venv-clean/Scripts/python.exe -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cpu; .venv-clean/Scripts/python.exe -m pip install -r requirements.txt; .venv-clean/Scripts/python.exe tools/verify_runtime.py','evidence':'clean_runtime_smoke.json'},
                  {'id':'E0','status':'completed_sanity','command':'.venv-phase2/Scripts/python.exe tools/run_experiment.py learning-sanity --out experiments/E0_learning_cpu --steps 12','evidence':'experiments/E0_learning_cpu/metrics.json'},
                  {'id':'E1','status':'completed_diagnostic','command':'.venv-phase2/Scripts/python.exe tools/run_experiment.py evaluate --out experiments/E1_historical_validation','evidence':'experiments/E1_historical_validation/metrics.json'},
                  {'id':'paper-evidence','status':'reproduced','command':'.venv-clean/Scripts/python.exe tools/build_evidence.py','evidence':'paper/table_reproduction.json'},
                  {'id':'Demo-HTTP','status':'passed','command':'.venv-phase2/Scripts/python.exe tools/check_demo_http.py','evidence':'demo_http.json'}],
              'test_model_evaluation_performed':False,'gpu_blocker':'RTX3050 Windows device Code 43; CUDA device_count=0',
              'browser_blocker':'No browser connected; visual end-to-end UI verification not performed',
              'next':'Normal-inclusive training in a new run directory after compute recovery/budget; controlled comparison; frozen final evaluation; browser demonstration; manuscript review'}
    (session/'session_ledger.json').write_text(json.dumps(ledger,indent=2))
    e2_state = json.loads(Path('experiments/E2_corrected_baseline/state.json').read_text())
    ledger['runs'] += [
        {'id':'E0-clean-cpu','status':'completed_sanity','evidence':'experiments/E0_learning_clean_cpu/metrics.json'},
        {'id':'E2-resume-smoke','status':'passed_execution_only','evidence':'experiments/E2_training_smoke_final/state.json'},
        {'id':'E2-normal-inclusive','status':e2_state['status'],'state_at_session_end':e2_state,
         'command':'.venv-clean/Scripts/python.exe tools/train_baseline.py --out experiments/E2_corrected_baseline --epochs 12 --batch-size 2 --loss bce_dice --patience 5',
         'process':json.loads((session/'E2_process.json').read_text()),'evidence':'experiments/E2_corrected_baseline/'}]
    ledger['next'] = 'Inspect active E2 baseline state/logs first; do not launch a duplicate. After completion, validation-only calibration/comparison, bundle freeze, final test, browser demonstration and manuscript review.'
    (session/'session_ledger.json').write_text(json.dumps(ledger,indent=2))
    serving = {'model_sha256':originals['best_model.pt'],'threshold':.9,'postprocessing':'all-components-v1',
               'input':'grayscale CLAHE2.0/8x8 + Gaussian3x3, stretch256, float32/255','mask_mapping':'threshold on model grid then nearest-neighbor inverse stretch to original dimensions',
               'geometry_units':'256x256 model-grid pixels; heuristic only','original_threshold_calibration_provenance':'unverified',
               'current_diagnostic_validation':'experiments/E1_historical_validation/metrics.json',
               'source_sha256':sha('medvision_ai.py'),'independent_final_test':False}
    Path('experiments/serving_bundle.json').write_text(json.dumps(serving,indent=2))
    print('Original artifacts unchanged; final source snapshot, serving bundle and session ledger saved.')


if __name__=='__main__':
    main()
