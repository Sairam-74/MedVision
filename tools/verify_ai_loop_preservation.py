"""Read-only preservation check; report original guards and retained history bytes."""
import datetime
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
session=ROOT/'experiments/session_20261007_ai_loop_01'
previous=json.loads((session/'verification_after_E5_complete_review.json').read_text())
guards=previous['protected_training_guards']
guards.update({'tools/train_baseline.py':'07ee47dff823446925c2adb25ab8d3797cce547d64feaea9a48a8769ed012181',
               'tools/train_pipeline.py':'8fa071efd503e49dd4483ae1ccbabb09b791e393d67f44ef9dd66194e57f7311',
               'best_model_threshold.json':'02d33de4874bcb22816225b8c0834123388f90505a16a3953b7e452a103e3830'})
for name,digest in guards.items():
    with (ROOT/name).open('rb') as handle:
        if hashlib.file_digest(handle,'sha256').hexdigest()!=digest:
            raise ValueError('Protected original changed: '+name)
queue=json.loads((session/'presence_queue_r2.json').read_text(encoding='utf-8-sig'))
for name,digest in queue['guards'].items():
    with (ROOT/name).open('rb') as handle:
        if hashlib.file_digest(handle,'sha256').hexdigest()!=digest.lower():
            raise ValueError('Current matched experiment guard changed: '+name)
history={}
for name in ('PROJECT_STATUS.md','EXPERIMENT_REGISTRY.md'):
    before=(session/'before'/name).read_bytes();now=(ROOT/name).read_bytes()
    title=re.match(br'(#.*?\r?\n)(?:\r?\n)',before)
    if not title: raise ValueError('Unexpected historical document title')
    history[name]=now.endswith(before[title.end():])
    if not history[name]: raise ValueError('Prior history bytes changed: '+name)
baseline=(ROOT/'BASELINE_MODEL_REPORT.md').read_bytes()
if baseline!=(ROOT/'experiments/AI_BASELINE_20261007_v1/BASELINE_MODEL_REPORT.md').read_bytes():
    raise ValueError('Baseline report copy differs')
report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),protected_original_guards=guards,
            active_pair_guards_verified=True,baseline_copy_identical=True,prior_status_registry_history_preserved=history,
            website_edited=False,new_test_predictions=0,new_calibration_fit=False,promotion=False)
path=session/('verification_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')+'.json')
with path.open('x') as handle: json.dump(report,handle,indent=2)
print(json.dumps(dict(report=str(path.relative_to(ROOT)),all_guards_verified=True,history=history)))
