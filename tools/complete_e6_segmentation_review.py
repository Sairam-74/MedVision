"""Join retained image/mask notes; no new inference or annotation changes."""
import csv
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
session=ROOT/'experiments/session_20261007_ai_loop_01'
out=session/'E6_remaining_segmentation_sheets'
index=json.loads((out/'index.json').read_text())
notes=[]
for path in sorted(out.glob('visual_notes_*.json')):
    notes.extend(json.loads(path.read_text())['notes'])
assert len(notes)==len(index['sheets'])==8
rows=[]
for entry,values in zip(index['sheets'],notes):
    assert len(entry['cases'])==len(values)
    for case,note in zip(entry['cases'],values):
        rows.append(dict(**case,sheet=entry['sheet'],observed_mask_geometry=note,clinical_cause='Unadjudicated'))
assert len(rows)==44 and len({r['image_id'] for r in rows})==44
with (out/'per_case_visual_review.csv').open('x',newline='',encoding='utf-8') as handle:
    writer=csv.DictWriter(handle,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
cases=json.loads((ROOT/'experiments/AI_AUDIT_E6_v3/per_case.json').read_text())
tagged={c['image_id'] for c in cases if c['positive'] and c['segmentation_failure_tags']}
reviewed={r['image_id'] for r in rows}|set(index['already_reviewed_ids'])
fn=json.loads((session/'E6_FN_VISUAL_REVIEW.json').read_text())
# Verify FN review coverage from native audit identities and existing explicit review artifact.
fn_ids={c['image_id'] for c in cases if c['category']=='FN'}
text=json.dumps(fn)
assert all(image_id in text for image_id in fn_ids)
assert tagged==reviewed|fn_ids and len(tagged)==69
(out/'completion.json').write_text(json.dumps(dict(status='completed_retained_segmentation_contact_review',
    images_reviewed_here=44,earlier_individual_TP_reviewed=8,earlier_individual_FN_reviewed=17,
    all_tagged_positive_failures_reviewed=69,clinical_adjudication=False,no_new_inference=True,
    limitations='Coarse panel geometry only; clinical fracture subtype labels unavailable. Tiny boundaries retain numerical counts/full native panels.'),indent=2))
print(json.dumps(dict(reviewed_here=44,all_tagged_positive_failures=69)))
