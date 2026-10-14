"""One-time transparent technical recovery registration; no ML factor changes."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
session = ROOT/'experiments/session_20261007_ai_loop_01'
out = session/'presence_io_recovery_r2'
out.mkdir()
names = ['tools/train_ai_presence_candidate.py', 'tools/verify_ai_presence_model.py',
         'tools/queue_ai_presence.ps1', 'tools/record_ai_loop.py']
hashes = {}
for name in names:
    path = ROOT/name
    shutil.copy2(path, out/path.name)
    hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
old_protocol = session/'PRESENCE_EXPERIMENT_PROTOCOL.json'
protocol = json.loads(old_protocol.read_text())
protocol['reference'] = 'AI_E7_v3_presence_reference_r2'
protocol['candidate'] = 'AI_E8_v3_presence_supervision_r2'
protocol['technical_recovery'] = dict(
    failed_run='AI_E7_v3_presence_reference', failure='WinError5 atomic state replacement before first validation',
    old_protocol_sha256=hashlib.sha256(old_protocol.read_bytes()).hexdigest(),
    preserved='Failed run, initial epoch0 checkpoint, source snapshots, config, stdout/stderr and original queue retained',
    changes='Unique temporary artifacts, fsync and bounded PermissionError retry for JSON/checkpoints; fresh output identities only',
    ML_settings_changed=False, first_epoch_repeated=True, failed_epoch_validated=False,
    failed_epoch_weights_retained=False)
(session/'PRESENCE_EXPERIMENT_PROTOCOL_r2.json').write_text(json.dumps(protocol, indent=2))
trainer = ROOT/names[0]
source = trainer.read_text()
source = source.replace('candidate_loss, case_counts, atomic_save', 'candidate_loss, case_counts')
source = source.replace('from tools import ai_metrics as a', 'from tools import ai_metrics as a\nfrom tools.ai_atomic_io import json_atomic, atomic_save')
source = source.replace('PRESENCE_EXPERIMENT_PROTOCOL.json', 'PRESENCE_EXPERIMENT_PROTOCOL_r2.json')
start = source.index('def json_atomic(')
end = source.index('def validate(', start)
source = source[:start] + source[end:]
source = source.replace("sources = ['tools/train_ai_presence_candidate.py'", "sources = ['tools/ai_atomic_io.py','tools/train_ai_presence_candidate.py'")
trainer.write_text(source)
smoke = ROOT/names[1]
source = smoke.read_text().replace("['tools/verify_ai_presence_model.py'", "['tools/ai_atomic_io.py','tools/verify_ai_presence_model.py'")
smoke.write_text(source)
queue = (ROOT/names[2]).read_text()
queue = queue.replace('presence_queue.json', 'presence_queue_r2.json')
queue = queue.replace('AI_PRESENCE_MODEL_SMOKE_20261007', 'AI_PRESENCE_MODEL_SMOKE_20261007_r2')
queue = queue.replace('PRESENCE_EXPERIMENT_PROTOCOL.json', 'PRESENCE_EXPERIMENT_PROTOCOL_r2.json')
queue = queue.replace('AI_E7_v3_presence_reference', 'AI_E7_v3_presence_reference_r2')
queue = queue.replace('AI_E8_v3_presence_supervision', 'AI_E8_v3_presence_supervision_r2')
queue = queue.replace("$guardFiles = @(", "$guardFiles = @('tools/ai_atomic_io.py',")
(ROOT/'tools/queue_ai_presence_r2.ps1').write_text(queue)
registry = ROOT/names[3]
source = registry.read_text().replace("presence_path = session/'presence_queue.json'", "presence_path = session/'presence_queue_r2.json' if (session/'presence_queue_r2.json').exists() else session/'presence_queue.json'")
source = source.replace('Protocol: PRESENCE_EXPERIMENT_PROTOCOL.json; smoke: AI_PRESENCE_MODEL_SMOKE_20261007.', 'Technical recovery r2 protocol: PRESENCE_EXPERIMENT_PROTOCOL_r2.json; smoke: AI_PRESENCE_MODEL_SMOKE_20261007_r2. Original failed run retained; no validated epoch lost.')
registry.write_text(source)
state = json.loads((ROOT/'experiments/AI_E7_v3_presence_reference/state.json').read_text())
state.update(status='failed_before_validation', failure='WinError5 replacing state.json',
             validated_epochs=0, epoch1_weights_retained=False, recovery='AI_E7_v3_presence_reference_r2')
(ROOT/'experiments/AI_E7_v3_presence_reference/failure.json').write_text(json.dumps(state, indent=2))
# Preserve original final state separately, then mark the failed research job accurately.
shutil.copy2(ROOT/'experiments/AI_E7_v3_presence_reference/state.json', out/'failed_last_state.json')
(ROOT/'experiments/AI_E7_v3_presence_reference/state.json').write_text(json.dumps(state, indent=2))
report = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), preserved_source_hashes=hashes,
              protocol=protocol['technical_recovery'], no_CAL_test_inference=True, promotion=False)
(out/'registration.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
