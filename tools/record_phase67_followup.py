"""Append the verified legacy-history correction without replaying finalization."""
import hashlib
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
S=ROOT/'experiments/session_20261006_p6p7'
ledger=json.loads((S/'session_finalized.json').read_text())
previous=dict(ledger['checks'])
for key,name in [('CI_security','secure_api_final.json'),('real_original','secure_api_real_final.json'),('real_bundle','secure_bundle_api.json'),('browser','browser/browser_checks.json')]:
    ledger['checks'][key]=json.loads((S/name).read_text())['checks_passed']
for name,expected in ledger['protected_hashes'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
for name,expected in ledger['active_source_guards'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
ledger['E2_state']=json.loads((ROOT/'experiments/E2_corrected_baseline/state.json').read_text())
ledger['queue_status']=json.loads((S/'training_queue.json').read_text())['status']
ledger['followup']='Legacy localhost/127 image-cookie issue fixed by deriving URLs from exact owned paths; data retained; source-copy checks pending package verification.'
(S/'session_finalized.json').write_text(json.dumps(ledger,indent=2))
checks=ledger['checks']
for name in ['PROJECT_STATUS.md','medvision_handoff/MEDVISION_HANDOFF.md']:
    p=ROOT/name;text=p.read_text(encoding='utf-8')
    text=text.replace(f"{previous['CI_security']} security/CI checks",f"{checks['CI_security']} security/CI checks")
    text=text.replace(f"{previous['real_original']} real original-checkpoint API checks",f"{checks['real_original']} real original-checkpoint API checks")
    text=text.replace(f"{previous['real_bundle']} real logits-bundle API checks",f"{checks['real_bundle']} real logits-bundle API checks")
    text=text.replace(f"{previous['browser']} real browser checks",f"{checks['browser']} real browser checks")
    marker='- **Working real application:**'
    note='- **Release follow-up:** 10 older results used 127.0.0.1 image URLs, incompatible with the current localhost Strict cookie. Owned image/overlay URLs now derive from UUID-bound saved paths; original history remains intact. API regression and an actual old-history browser revisit verify the fix. Signup/MFA/audit/approval claims are disabled in real builds; login-page copy now states research scope. Final package: `deliverables/MedVision_reproduction_20261006_r2.zip`.\n'
    if note not in text: text=text.replace(marker,note+marker,1)
    text=re.sub(r'(E2 preserved, latest state `).*?(`\. Matched v2)',lambda m:m.group(1)+json.dumps(ledger['E2_state'])+m.group(2),text,count=1)
    p.write_text(text,encoding='utf-8')
p=S/'SECURITY_REVIEW.md';text=p.read_text(encoding='utf-8')
for key in ['CI_security','real_original','real_bundle','browser']:
    text=text.replace(f"**{previous[key]}**",f"**{checks[key]}**")
text=text.replace('10MiB body/8192 dimension','10MiB image plus 64KiB multipart allowance/8192 dimension')
text=text.replace('no default public password','no default public password')
text+='\nRelease follow-up: existing history had 10 absolute 127.0.0.1 image links, which do not receive localhost Strict cookies. Result/status/export responses now reconstruct image URLs from exact case-owned managed paths and apply the research disclaimer. The original SQLite/history records remain preserved. Tests simulate an obsolete/external saved URL and prove the correct protected image remains accessible; the browser revisits an actual older case. Account switching also clears prior query data, and expiry clears displayed account state. Real MFA and signup/admin/audit/approval placeholders cannot be enabled in production. The exact 10MiB image limit now allows separate bounded multipart overhead; a compressed PNG-text bomb returns422 rather than an internal500.\n'
p.write_text(text,encoding='utf-8')
with (ROOT/'EXPERIMENT_REGISTRY.md').open('a',encoding='utf-8') as f:
    f.write(f"\nPhase 7 release follow-up: legacy image-origin/cookie mismatch fixed without rewriting history. Current checks: {checks['CI_security']} security/CI, {checks['real_original']} real original API, {checks['real_bundle']} real logits API, {checks['browser']} browser including old-case image revisit, 7 frontend. Source/evidence release r2 replaces the earlier package as the current deliverable; v1 remains preserved. E2 source/data unchanged, v2 runs still queued. No final test or final-model claim.\n")
print(json.dumps(checks,indent=2))
