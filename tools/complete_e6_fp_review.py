"""Join explicit visual notes to immutable saved E6 FP panel identities."""
import csv
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/session_20261007_ai_loop_01/E6_all_FP_sheets'
index=json.loads((out/'index.json').read_text())
notes=[]
for path in sorted(out.glob('visual_notes_*.json')):
    notes.extend(json.loads(path.read_text())['notes'])
assert len(notes)==len(index['sheets'])==24
rows=[]
for entry,values in zip(index['sheets'],notes):
    assert len(entry['cases'])==len(values)
    for case,note in zip(entry['cases'],values):
        rows.append(dict(**case,sheet=entry['sheet'],observed_mask_location=note,
                         clinical_cause='Unadjudicated; dataset-normal label defines FP'))
assert len(rows)==215 and len({r['image_id'] for r in rows})==215
with (out/'per_case_visual_review.csv').open('x',newline='',encoding='utf-8') as handle:
    writer=csv.DictWriter(handle,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
(out/'completion.json').write_text(json.dumps(dict(status='completed_contact_sheet_visual_review',
    images_reviewed=215,sheets_reviewed=24,no_new_inference=True,no_label_changes=True,
    clinical_adjudication=False,limitations='Tiny masks may be unresolved at contact-sheet scale; retain full native panels and pixel counts',
    observations='Repeated joint margins, shafts and wrists/ankles; internal divider marks in1355 and2185. Association is not cause proof.'),indent=2))
print(json.dumps(dict(reviewed_cases=215,individual_notes=215)))
