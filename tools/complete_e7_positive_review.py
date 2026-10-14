"""Join actual manually viewed E7 native positive panels to per-case evidence."""
import csv
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.ai_atomic_io import json_atomic
from tools.evaluate_ai_baseline import sha

notes=[
['Elbow annotation; no predicted mask','Wrist annotation partly covered by a tiny patch; separate finger annotation missed','Distal forearm annotation partly covered with extra wrist and shaft patches','Paired wrist annotations missed; red patch displaced from green targets','Elbow target partly covered by small patch; extra distal-forearm patch','Elbow annotation missed; predictions displaced toward wrist/forearm'],
['Broad elbow annotation covered only by tiny patch','Elbow annotation missed; prediction displaced to distal forearm/wrist','Shoulder/proximal-humerus annotation; no prediction','Wrist annotation overlapped with broader extra prediction','Small elbow annotation covered only partly','Mid-forearm annotation partly covered; extra elbow and shaft patches'],
['Small hand annotations in paired views; no predictions','Proximal-humerus annotation in broad shoulder field; no prediction','Proximal-humerus annotation; no prediction','Wrist annotation; no prediction','Forearm annotations partly covered by broader displaced patches','Elbow annotation missed; nearby red patch has zero reference overlap'],
['Lower-leg annotation near bottom of field; visible intramedullary hardware; no mask','Small wrist annotation in cast-like field; tiny shifted patch has zero overlap','Lower-leg annotation with external fixator; no prediction','Lower-leg annotation with external fixator; no prediction','Paired cast-like wrist annotations; no predictions','Cast-like forearm annotation partly covered by tiny patch plus false wrist region'],
['Paired elbow annotations missed; red patches displaced in elbow and forearm regions','Wrist annotation partly covered with extra forearm patch','Proximal-femur target has small overlap, while a larger false patch marks opposite knee','Paired cast-like forearm annotations missed; prediction detail visually unresolved even in full panel. Native PNG verifies only1 false pixel at normalized x0.8445/y0.3877','Elbow annotation missed; small adjacent prediction has zero overlap','Cast-like elbow/forearm annotation missed; prediction shifted to the opposite joint margin'],
['Lower-leg annotation partly covered by scattered patches with extra shaft signal','Cast-like distal-humerus annotation missed; small red patch shifted to elbow','Elbow annotation missed; red patch above reference','Elbow annotation missed; nearby patch on different side and extra shaft signal','Small elbow annotation missed; full native panel checked. Native PNG verifies3 false pixels at normalized x0.1762-0.1784/y0.3619-0.3646','Elbow annotation minimally covered; extra lower-forearm patches'],
['Elbow annotation minimally covered by small patch','Distal-forearm annotations partly covered with broader red region','Small forefoot annotation; no prediction','Long femoral-shaft annotation mostly missed; prediction concentrated near knee','Proximal-femur/hip annotation; no prediction','Elbow annotation partly covered by a smaller patch'],
['Humeral-shaft annotation with visible plate; no prediction','Lower-leg annotation with visible hardware in paired views; no prediction','Two annotations in paired elbow/shaft views; no predictions','Forearm-shaft annotation near plate minimally covered; extra wrist region','Cast-like forearm annotation partly overlapped with oversized irregular patch','Shoulder/proximal-humerus annotation; no prediction'],
['Small forefoot annotation; no prediction','Two forearm-shaft annotations partly covered; extra wrist patch','Forearm-shaft annotation missed; red patch displaced toward wrist','Wrist annotation partially covered; prediction outline differs and extra shaft signal','Large proximal-femur annotations almost entirely missed; only tiny distal patch','Lower-leg shaft annotation overlapped with several extra shaft patches'],
['Small forefoot annotation; no prediction','Small forefoot annotation; no prediction','Small proximal lower-leg annotation; no prediction','Cast-like lower-leg annotation partly covered by one of two patches','Wrist annotation almost entirely missed; only tiny wrist patch','Cast-like wrist annotation partly overlapped by larger patch and extra forearm region'],
['Cast-like wrist annotation partly overlapped by larger patch and extra forearm region']]


def main():
    session=ROOT/'experiments/session_20261007_ai_loop_01'
    out=session/'E7_remaining_positive_sheets'
    index=json.loads((out/'index.json').read_text());audit=ROOT/index['audit']
    full={c['image_id']:c for c in json.loads((audit/'per_case.json').read_text())}
    if len(notes)!=len(index['sheets']): raise ValueError('Actually reviewed sheets differ')
    rows=[]
    for sheet,observations in zip(index['sheets'],notes):
        if len(sheet['cases'])!=len(observations): raise ValueError('Actual case notes differ')
        for case,note in zip(sheet['cases'],observations):
            c=full[case['image_id']]
            rows.append(dict(image_id=c['image_id'],category=c['category'],dice=c['dice'],iou=c['iou'],
                panel=c['review_panel'],sheet=sheet['sheet'],observed_mask_note=note,
                tp_pixels=c['tp_pixels'],fp_pixels=c['fp_pixels'],fn_pixels=c['fn_pixels'],
                tags=';'.join(c['segmentation_failure_tags']),clinical_cause='Unadjudicated',
                clinical_subtle_nondisplaced_type='Unavailable',view_flags=json.dumps(c['flags'],sort_keys=True)))
    early=json.loads((session/'E7_EARLY_NATIVE_PANEL_REVIEW.json').read_text())
    for row in early['rows']:
        c=full[row['image_id']]
        if not c['positive'] or not c['segmentation_failure_tags']: continue
        if sha(audit/'failures'/row['panel'])!=row['panel_sha256']: raise ValueError('Actual early panel changed')
        rows.append(dict(image_id=c['image_id'],category=c['category'],dice=c['dice'],iou=c['iou'],
            panel=c['review_panel'],sheet='Earlier full native panel',observed_mask_note=row['visual_note'],
            tp_pixels=c['tp_pixels'],fp_pixels=c['fp_pixels'],fn_pixels=c['fn_pixels'],
            tags=';'.join(c['segmentation_failure_tags']),clinical_cause='Unadjudicated',
            clinical_subtle_nondisplaced_type='Unavailable',view_flags=json.dumps(c['flags'],sort_keys=True)))
    expected={i for i,c in full.items() if c['positive'] and c['segmentation_failure_tags']}
    if len(rows)!=len(expected)!=64 or {r['image_id'] for r in rows}!=expected:
        raise ValueError('Complete unique tagged-positive review required')
    if len(rows)!=64 or len({r['image_id'] for r in rows})!=64: raise ValueError('Review duplicate/missing case')
    with (out/'per_case_visual_review.csv').open('x',newline='',encoding='utf-8') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    json_atomic(out/'visual_notes.json',dict(notes=notes,actual_sheet_viewing=True,clinical_adjudication=False))
    json_atomic(out/'completion.json',dict(status='completed_actual_native_positive_failure_review',
        tagged_positive_cases_reviewed=64,remaining_sheet_cases=61,earlier_full_panel_cases=3,sheets_reviewed=11,
        complete_empty_misses_reviewed=sum(r['category']=='FN' for r in rows),
        wrong_region_image_positives_reviewed=sum(r['category']=='TP' and r['tp_pixels']==0 for r in rows),
        source_sha256=sha(__file__),index_sha256=sha(out/'index.json'),no_new_inference=True,
        no_label_changes=True,clinical_adjudication=False,
        limitations='Annotation overlap observations only; casts/hardware do not prove failure cause. Tiny1/3-pixel signals separately checked in actual full panels/native PNGs.'))
    print(json.dumps(dict(positive_failure_cases=64,empty_misses=22,wrong_region_positives=15)))


if __name__=='__main__': main()
