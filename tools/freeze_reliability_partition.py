"""Reproduce the prospective calibration partition without reading image pixels.

Existing manifests are verified, never rewritten. Train/test assignments preserved.
"""
import hashlib
import json
from pathlib import Path
from sklearn.model_selection import train_test_split


def main():
    parent=Path('experiments/data_v2/manifest.json')
    m=json.loads(parent.read_text())
    groups={}
    for r in m['rows']:
        if r['split']=='val':groups.setdefault(r['group'],[]).append(r)
    keys=sorted(groups);labels=[int(any(int(r['fractured']) for r in groups[k])) for k in keys]
    _,cal=train_test_split(keys,test_size=.25,stratify=labels,random_state=42)
    cal=set(cal);new=json.loads(json.dumps(m))
    for r in new['rows']:
        if r['split']=='val' and r['group'] in cal:r['split']='calibration'
    new['version']='data_v3_reliability_20261007'
    new['parent_manifest_sha256']=hashlib.sha256(parent.read_bytes()).hexdigest()
    new['calibration_partition_protocol']={'seed':42,'fraction_of_previous_validation_groups':.25,
        'stratification':'group any-positive label; no model outputs used','prospective_only':True,
        'prior_E2_validation_exposure':'all original validation images; these calibration images are NOT independent of E2 model selection',
        'fresh_model_rule':'fresh candidates train on train only, select/check thresholds on val only; calibrate on calibration only after model selection; reserved test once after acceptance/freeze',
        'patient_independence_verified':False}
    encoded=(json.dumps(new,indent=2)+'\n').encode()
    # Original creation used Path.write_text on Windows, with CRLF newlines.
    encoded=encoded.replace(b'\n',b'\r\n')
    path=Path('experiments/data_v3_reliability_20261007/manifest.json')
    if not path.exists():raise ValueError('Expected frozen manifest missing; register a new version deliberately')
    if path.read_bytes()!=encoded:raise ValueError('Seeded manifest recipe does not reproduce frozen bytes')
    for role in ('train','test'):
        if [r['image_id'] for r in new['rows'] if r['split']==role]!=[r['image_id'] for r in m['rows'] if r['split']==role]:
            raise ValueError('Existing train/test assignments changed')
    print('Exact frozen v3 manifest bytes reproduced; train/test IDs unchanged; no image pixels read')


if __name__=='__main__':main()
