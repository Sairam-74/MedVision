"""Validate/join actual per-image observations with retained native panels.

This tool cannot view images. It records observations supplied AFTER actual
viewing and checks exact selection coverage; never infers a clinical cause.
"""
import argparse
import csv
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.ai_atomic_io import json_atomic
from tools.evaluate_ai_baseline import sha


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--directory',required=True);ap.add_argument('--notes',required=True)
    ap.add_argument('--earlier-panel-review')
    args=ap.parse_args();directory,notes_path=Path(args.directory).resolve(),Path(args.notes).resolve()
    if ROOT not in directory.parents or ROOT not in notes_path.parents or (directory/'completion.json').exists():
        raise ValueError('Exclusive completion of workspace actual review required')
    index=json.loads((directory/'index.json').read_text());notes=json.loads(notes_path.read_text());audit=ROOT/index['audit']
    if not notes['actually_viewed'] or notes['index_sha256']!=sha(directory/'index.json'):
        raise ValueError('Actual viewing declaration with matching sheet index required')
    if len(notes['sheets'])!=len(index['sheets']): raise ValueError('Every sheet needs actual observations')
    full={c['image_id']:c for c in json.loads((audit/'per_case.json').read_text())};rows=[]
    def append_case(image_id,panel,note,sheet):
        if not isinstance(note,str) or not note.strip(): raise ValueError('Nonempty actual per-image observation required')
        c=full[image_id]
        if c['review_panel']!=panel: raise ValueError('Linked retained panel differs')
        rows.append(dict(image_id=image_id,panel=panel,panel_sha256=sha(audit/panel),sheet=sheet,
            observed_note=note,positive=c['positive'],mask_category=c['category'],alert_category=c['review_alert_category'],
            head_mask_group=c['head_mask_group'],head_score=c['head_score'],dice=c['dice'],iou=c['iou'],
            tp_pixels=c['tp_pixels'],fp_pixels=c['fp_pixels'],fn_pixels=c['fn_pixels'],
            source_view_flags=json.dumps(c['flags'],sort_keys=True),clinical_cause='Unadjudicated',clinical_subtype='Unavailable'))
    for sheet,observed in zip(index['sheets'],notes['sheets']):
        if sheet['sheet']!=observed['sheet'] or len(sheet['cases'])!=len(observed['notes']):
            raise ValueError('Actual per-sheet/per-case observations must match order')
        for c,note in zip(sheet['cases'],observed['notes']): append_case(c['image_id'],c['panel'],note,sheet['sheet'])
    selection=index.get('selection','positive_segmentation_errors')
    if selection=='positive_segmentation_errors':
        required={i for i,c in full.items() if c['positive'] and c['segmentation_failure_tags']}
    elif selection=='normal_alerts': required={i for i,c in full.items() if not c['positive'] and c['review_alert_present']}
    else: required={i for i,c in full.items() if c['classifier_prediction_present'] is not None and c['classifier_prediction_present']!=c['prediction_present']}
    if args.earlier_panel_review:
        earlier=json.loads(Path(args.earlier_panel_review).read_text())
        if not earlier['actually_viewed']: raise ValueError('Earlier actual viewing required')
        for r in earlier['rows']:
            if r['image_id'] not in required: continue
            panel='failures/'+r['panel']
            if sha(audit/panel)!=r['panel_sha256']: raise ValueError('Earlier actual panel changed')
            append_case(r['image_id'],panel,r['visual_note'],'Earlier full native panel')
    own_ids=[r['image_id'] for r in rows]
    if len(own_ids)!=len(set(own_ids)): raise ValueError('Duplicate actual review case')
    previous=set(index.get('previously_reviewed_selected_ids',[]))
    if set(own_ids)&previous or set(own_ids)|previous!=required: raise ValueError('Incomplete/duplicate selected-case visual coverage')
    for folder in index.get('excluded_review_directories',[]):
        prior=ROOT/folder;completion=json.loads((prior/'completion.json').read_text());prior_rows=prior/'per_case_visual_review.json'
        if completion['audit']!=index['audit'] or sha(prior_rows)!=completion['per_case_review_sha256']: raise ValueError('Prior completed actual review changed')
    with (directory/'per_case_visual_review.csv').open('x',newline='',encoding='utf-8') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0]) if rows else ['image_id']);writer.writeheader();writer.writerows(rows)
    json_atomic(directory/'per_case_visual_review.json',rows)
    result=dict(status='completed_actual_native_'+selection+'_review',audit=index['audit'],selection=selection,
        actual_new_case_reviews=len(rows),previously_reviewed_selected_cases=len(previous),total_selected_cases=len(required),
        actual_sheets_reviewed=len(index['sheets']),per_case_review_sha256=sha(directory/'per_case_visual_review.json'),
        index_sha256=sha(directory/'index.json'),notes_sha256=sha(notes_path),
        new_inference=False,no_label_changes=True,clinical_adjudication=False)
    json_atomic(directory/'completion.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__': main()
