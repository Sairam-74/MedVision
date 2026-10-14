"""Check two browser-native masks against saved historical 2.9.1 counts."""
import base64
import json
from pathlib import Path
import sys
import zipfile
import cv2
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.run_experiment import native_pair

manifest=json.loads((ROOT/'experiments/data_v2/manifest.json').read_text())
historical=json.loads((ROOT/'experiments/E1_historical_validation/per_case.json').read_text())
old=next(item['cases'] for item in historical if item['threshold']==.9 and item['policy']=='all')
lookup={case['image_id']:case for case in old}
inputs=json.loads((ROOT/'experiments/session_20261006_p6p7/browser_inputs/inputs.json').read_text())
checks=[]
with zipfile.ZipFile(ROOT/'FracAtlas.zip') as z:
    annotations={a['id']:a for a in json.loads(z.read('FracAtlas/Annotations/COCO JSON/COCO_fracture_masks.json'))['annotations']}
    for item in inputs:
        result=json.loads((ROOT/f"experiments/session_20261006_p6p7/browser/{item['id']}-result.json").read_text())
        encoded=np.frombuffer(base64.b64decode(result['maskPngBase64']),np.uint8)
        mask=cv2.imdecode(encoded,cv2.IMREAD_GRAYSCALE)>0
        row=next(row for row in manifest['rows'] if row['image_id']==item['id'])
        image,gt=native_pair(z,row,annotations)
        assert mask.shape==image.shape
        counts={'tp_pixels':int(np.logical_and(mask,gt).sum()),'fp_pixels':int(np.logical_and(mask,~gt.astype(bool)).sum()),'fn_pixels':int(np.logical_and(~mask,gt).sum())}
        assert all(counts[key]==lookup[item['id']][key] for key in counts), (item['id'],counts,lookup[item['id']])
        checks.append({'image_id':item['id'],'counts':counts,'historical_count_parity':True})
out=ROOT/'experiments/session_20261006_p6p7/serving_parity.json'
out.write_text(json.dumps({'from':'torch2.9.1+cpu historical validation','to':'torch2.14.1+cpu real browser serving','scope':'two validation examples; not an exhaustive cross-runtime guarantee','checks':checks},indent=2))
print('Two native browser masks exactly reproduce historical integer counts.')
