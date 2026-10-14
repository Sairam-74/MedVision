"""Compare historical TRAIN hard catalogs with completed E5 TRAIN grid errors."""
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.evaluate_ai_baseline import sha,save

out=ROOT/'experiments/AI_HARD_SET_PERSISTENCE_E5_v3'
if out.exists(): raise ValueError('Exclusive diagnostic output required')
catalog=ROOT/'experiments/AI_TRAIN_HARD_SETS_20261007'
fit=ROOT/'experiments/AI_LEARNING_FIT_E5_v3'
paths=[catalog/'HARD_POSITIVE_SET.json',catalog/'HARD_NEGATIVE_SET.json',fit/'train_cases.jsonl',
       ROOT/'experiments/data_v3_reliability_20261007/manifest.json']
cases=[json.loads(line) for line in paths[2].read_text().splitlines() if line.strip()]
manifest=json.loads(paths[3].read_text())
train={r['image_id'] for r in manifest['rows'] if r['split']=='train'}
if len(cases)!=2808 or {c['image_id'] for c in cases}!=train or sha(paths[3])!='4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318':
    raise ValueError('Full frozen TRAIN fit evidence required')
positive=set(json.loads(paths[0].read_text())['image_ids']);negative=set(json.loads(paths[1].read_text())['image_ids'])
if not positive<=train or not negative<=train or positive&negative:
    raise ValueError('Catalog membership invalid')
groups={};rows=[]
for label,name,hard in ((True,'fracture',positive),(False,'normal',negative)):
    for selected,suffix in ((True,'catalog_hard'),(False,'other')):
        subset=[c for c in cases if c['positive']==label and (c['image_id'] in hard)==selected]
        errors=[c['image_id'] for c in subset if not c['prediction_present']] if label else [c['image_id'] for c in subset if c['prediction_present']]
        zero=[c['image_id'] for c in subset if c['zero_overlap_positive']] if label else []
        groups[name+'_'+suffix]=dict(n=len(subset),case_errors=len(errors),case_error_fraction=len(errors)/len(subset),
            zero_overlap_masks=len(zero) if label else None,
            mean_positive_grid_dice=float(np.mean([c['dice'] for c in subset])) if label else None,
            grid_Dice_below_02=sum(c['dice']<.2 for c in subset) if label else None,
            error_image_ids=errors,zero_overlap_image_ids=zero)
        rows.extend(dict(image_id=c['image_id'],positive=label,historical_hard=selected,
            E5_grid_prediction=c['prediction_present'],E5_grid_Dice=c['dice'],E5_zero_overlap=c['zero_overlap_positive']) for c in subset)
out.mkdir()
save(out/'comparison.json',dict(groups=groups,input_hashes={str(v.relative_to(ROOT)):sha(v) for v in paths},
    scope='Read-only TRAIN metadata comparison; historical native masks vs E5 grid diagnostic have different thresholds/geometries',
    no_new_inference=True,weighting_applied=False,test_images_read=0,calibration_images_read=0,
    clinical_difficult_subtypes_available=False,model_improvement_claim=False))
save(out/'per_training_case.json',rows)
save(out/'completion.json',dict(status='completed_TRAIN_catalog_diagnostic',training_cases=2808,new_inference=False,model_trained=False))
print(json.dumps({k:{x:y for x,y in v.items() if not x.endswith('_ids')} for k,v in groups.items()},indent=2))
