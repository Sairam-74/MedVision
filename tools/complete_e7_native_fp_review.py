"""Record manually observed E7 FP contact panels, after all19 actual sheets were viewed."""
import csv
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.ai_atomic_io import json_atomic
from tools.evaluate_ai_baseline import sha

notes=[
['Distal lower-leg shaft compact patch','Small humeral-shaft patch','Tiny wrist-region patch','Mid-forearm shaft patch','Forearm-shaft patch below elbow','Patch near distal humerus/elbow in broad upper-limb field','Two distal lower-leg patches','Small distal lower-leg patch; hardware visible but not proven causal','Two compact ankle-adjacent patches'],
['Small distal-femur patch in composite knee views','Distal-femur and lower-leg patches','Distal-femur patch in knee views','Distal-forearm/wrist patch in paired views','Tiny midfoot patch; detailed anatomy unresolved at contact scale','Forefoot and ankle-adjacent patches in paired views','Distal-femur patch in knee views','Tiny lower-leg signal unresolved at contact scale','Compact wrist patch'],
['Compact wrist patch','Small distal-femur patch above knee','Small lower-leg patch above ankle','Tiny lower-leg patch; precise structure unresolved','Mid and distal lower-leg patches','Broad wrist patch','Small distal-lower-leg patch','Small pelvic-region signal; exact structure unresolved','Compact elbow-region patch'],
['Compact elbow patch','Small forearm-shaft patch','Two views with compact wrist patches','Compact wrist patch','Compact wrist patch in narrow lateral view','Small distal lower-leg patch above ankle','Compact ankle-adjacent patch','Small posterior elbow/tip patch','Small elbow patch'],
['Small distal lower-leg shaft patch','Compact ankle-adjacent patch','Two wrist-adjacent patches','Tiny elbow signal','Femoral-shaft patch below hip','Tiny lower-leg signal; detailed anatomy unresolved','Elbow and forearm patches in composite views','Small humeral-shaft patch','Small wrist-adjacent patch'],
['Elbow-adjacent patches','Two distal-femur patches','Proximal and distal lower-leg patches in paired knees','Compact wrist patch','Humeral-shaft and elbow patches','Distal lower-leg and forefoot patches','Tiny forearm signal; detailed anatomy unresolved','Elbow and distal-humerus patches in broad torso/limb image','Compact wrist patch in narrow view'],
['Tiny distal-humerus signal','Small mid-forearm patch','Small elbow patch; ring-like external object also visible away from prediction','Small distal-humerus patch','Compact wrist patch; external ring above predicted region','Mid lower-leg shaft patch','Wrist and hand patches','Compact wrist patch','Compact wrist patch'],
['Small elbow/tip patches','Compact wrist patch','Broad wrist patch','Compact wrist patch in broad shoulder/arm field','Compact wrist patch and tiny hand signal','Small distal-femur patch in composite knee views','Broad wrist and small forearm patches','Tiny elbow patch','Small lower-leg shaft patch'],
['Small wrist patch','Compact wrist patch','Knee-adjacent patch in broad pelvis/leg image','Tiny wrist signal','Broad distal-lower-leg patch above ankle','Several distal-lower-leg patches','Tiny elbow signal unresolved at contact scale','Lower-leg shaft patch','Distal-lower-leg patches'],
['Tiny knee-adjacent signal; detailed structure unresolved','Small lower-leg shaft patch above ankle','Broad wrist patch','Compact wrist patch in broad upper-limb image','Two lower-leg shaft patches','Small elbow patch','Broad wrist patch','Compact elbow patch','Compact wrist patch'],
['Compact elbow patch','Humeral-shaft patch in broad torso/arm image','Compact wrist patch; external band above region','Several humeral-shaft patches and tiny rib signal','Compact wrist patch','Small ankle/foot-region patch','Small mid lower-leg shaft patch','Both wrist regions marked in composite views','Small elbow patch'],
['Compact wrist patch; external band above predicted region','Tiny wrist signal in paired views','Forefoot and ankle patches in paired foot views','Lower-leg shaft and ankle-adjacent patches in composite views','Small distal-femur patch in paired knee views','Small knee-adjacent patch in paired knees','Mid and distal lower-leg patches','Tiny elbow patch','Broad distal-femur patch in broad limb views'],
['Tiny foot/ankle signal unresolved at contact scale','Broad distal-lower-leg patch','Several femoral-shaft patches in broad pelvis/leg field','Small wrist signal in broad banded forearm image','Several mid/distal lower-leg patches','Small wrist patch','Small ankle-adjacent patch','Broad wrist patch','Broad wrist patch'],
['Small distal-lower-leg signal','Small forefoot patch','Tiny elbow signal unresolved at contact scale','Small distal-lower-leg patch above ankle','Broad distal-humerus and elbow patches','Broad wrist patch','Tiny wrist signal in paired hands','Compact wrist patch','Broad distal-lower-leg and smaller shaft patches'],
['Small elbow patch','Tiny lower-leg shaft patch','Small wrist patch','Ankle and forefoot patches','Several distal-lower-leg patches','Broad wrist patch','Broad wrist patch; thin external object at thumb is visible away from patch','Two ankle-adjacent patches','Compact wrist patch'],
['Compact wrist patch','Small distal-femur patches in paired knees','Two rib-region patches in broad shoulder/torso field','Small elbow patch','Tiny foot/ankle signal unresolved at contact scale','Compact ankle-adjacent patch','Small wrist patch in banded forearm view','Broad elbow-region patches','Small femoral-shaft patch below hip'],
['Small wrist patch','Large distal-humerus and forearm patches in broad torso/limb field','Small mid lower-leg shaft patch','Tiny pelvic-region signal unresolved at contact scale','Distal-lower-leg patches','Broad distal-lower-leg patch above ankle','Two distal-femur patches in paired knees','Near-threshold tiny elbow signal unresolved at contact scale','Small elbow/distal-humerus patch'],
['Compact distal-lower-leg patch','Tiny lower-leg signal unresolved at contact scale','Broad elbow and small wrist patches in broad arm field','Near-threshold tiny forearm signal unresolved at contact scale','Compact distal-lower-leg patch','Two ankle-adjacent patches','Small proximal-femur signal in pelvis/spine field','Mid and distal lower-leg patches','Several femoral-shaft patches'],
['Small wrist signal in banded forearm view','Small wrist patch','Broad wrist patch']]


def main():
    out=ROOT/'experiments/session_20261007_ai_loop_01/E7_all_FP_sheets'
    index=json.loads((out/'index.json').read_text())
    audit=ROOT/index['audit']
    cases={c['image_id']:c for c in json.loads((audit/'per_case.json').read_text())}
    if len(notes)!=len(index['sheets']) or index['images']!=165:
        raise ValueError('Actual reviewed sheet/case count differs')
    rows=[]
    for entry,observations in zip(index['sheets'],notes):
        if len(entry['cases'])!=len(observations): raise ValueError('Each actually viewed case needs one note')
        for case,note in zip(entry['cases'],observations):
            full=cases[case['image_id']]
            if full['category']!='FP' or full['positive']: raise ValueError('Require dataset-normal mask false alarm')
            rows.append(dict(**case,sheet=entry['sheet'],observed_mask_location=note,
                mask_detail_resolved_at_contact_scale='unresolved' not in note,
                dataset_view_flags=json.dumps(full['flags'],sort_keys=True),
                image_quality='No expert quality rating; source image retained',
                clinical_cause='Unadjudicated; dataset-normal label defines FP'))
    if len(rows)!=165 or len({r['image_id'] for r in rows})!=165: raise ValueError('Incomplete/duplicate review')
    with (out/'per_case_visual_review.csv').open('x',newline='',encoding='utf-8') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    json_atomic(out/'visual_notes.json',dict(notes=notes,actual_sheet_viewing=True,clinical_adjudication=False))
    json_atomic(out/'completion.json',dict(status='completed_actual_contact_sheet_visual_review',
        images_reviewed=165,sheets_reviewed=19,individual_notes=165,source_sha256=sha(__file__),
        index_sha256=sha(out/'index.json'),no_new_inference=True,no_label_changes=True,
        clinical_adjudication=False,limitations='Some tiny masks unresolved at contact scale; actual full native panels and pixel counts retained. Anatomy and visible hardware association are not cause proof.'))
    print(json.dumps(dict(reviewed_cases=165,individual_notes=165)))


if __name__=='__main__': main()
