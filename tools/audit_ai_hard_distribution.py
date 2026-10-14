"""TRAIN-only hard-set composition and bounded weighting feasibility.

Creates no sampled/duplicated images and trains no candidate.
"""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import medvision_pipeline as p
from tools.evaluate_ai_baseline import save


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if ROOT not in out.parents or out.exists():
        raise ValueError('New workspace output required')
    manifest = ROOT/'experiments/data_v3_reliability_20261007/manifest.json'
    if p.sha(manifest)!='4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318':
        raise ValueError('Frozen data changed')
    document = json.loads(manifest.read_text())
    train = [r for r in document['rows'] if r['split']=='train']
    allowed = {r['image_id']:r for r in train}
    catalogs = {}
    for name, label in [('HARD_POSITIVE_SET', 1), ('HARD_NEGATIVE_SET', 0)]:
        path = ROOT/'experiments/AI_TRAIN_HARD_SETS_20261007'/(name+'.json')
        data = json.loads(path.read_text())
        ids = data['image_ids']
        if len(ids)!=data['n'] or len(set(ids))!=len(ids) or not set(ids)<=set(allowed):
            raise ValueError('Hard set identity, uniqueness or TRAIN-only membership failed')
        if any(int(allowed[i]['fractured'])!=label for i in ids):
            raise ValueError('Hard set labels mismatch source')
        catalogs[name] = dict(ids=set(ids), sha256=p.sha(path), definition=data['definition'])
    if catalogs['HARD_POSITIVE_SET']['ids'] & catalogs['HARD_NEGATIVE_SET']['ids']:
        raise ValueError('Hard catalogs overlap')
    all_hard = catalogs['HARD_POSITIVE_SET']['ids'] | catalogs['HARD_NEGATIVE_SET']['ids']
    weights = np.array([2. if r['image_id'] in all_hard else 1. for r in train])
    labels = np.array([int(r['fractured']) for r in train])
    weighting = {}
    for label in (0, 1):
        index = labels==label
        normalizer = float(weights[index].mean())
        weights[index] /= normalizer
        weighting[str(label)] = dict(class_images=int(index.sum()), hard_images=sum(r['image_id'] in all_hard for r in train if int(r['fractured'])==label),
            raw_hard_weight=2., raw_other_weight=1., within_class_normalizer=normalizer,
            normalized_hard_weight=2/normalizer, normalized_other_weight=1/normalizer,
            mean_class_weight=float(weights[index].mean()), class_total_weight=float(weights[index].sum()))
        if not np.isclose(weights[index].sum(), index.sum(), atol=1e-9):
            raise ValueError('Proposed weighting changes class mass')
    groups = {}
    for flag in ('hand','leg','hip','shoulder','mixed','hardware','multiscan','frontal','lateral','oblique'):
        rows = [r for r in train if int(r[flag])]
        groups[flag] = dict(train_images=len(rows), positive_images=sum(int(r['fractured']) for r in rows),
            hard_positive=sum(r['image_id'] in catalogs['HARD_POSITIVE_SET']['ids'] for r in rows),
            hard_negative=sum(r['image_id'] in catalogs['HARD_NEGATIVE_SET']['ids'] for r in rows))
    out.mkdir()
    result = dict(status='completed_distribution_diagnostic', train_images=len(train), train_positive=int(labels.sum()),
        catalogs={name:{key:value for key,value in data.items() if key!='ids'} | dict(n=len(data['ids']),
            conservative_groups=len({allowed[i]['group'] for i in data['ids']})) for name,data in catalogs.items()},
        proposed_bounded_weighting=weighting, nonexclusive_source_groups=groups,
        method='Uniform one-pass coverage of every TRAIN image; multiply per-image objective by fixed raw2/1 hardness weights normalized within each label class. No replacement sampling or new copies. Not applied yet.',
        rationale='Separate future hardness factor from current BCE1/2 and future case-head factor; preserve class prevalence/mass while emphasizing recurring training errors.',
        limitations='Algorithmic hard positives are not confirmed subtle/nondisplaced cases; group duplicates and missing patient IDs remain disclosed. Class normalization preserves class mass, not every anatomy/view prevalence.',
        training_distribution_modified=False, model_trained=False, validation_ids_in_catalog=0, calibration_ids_in_catalog=0, test_ids_in_catalog=0,
        manifest_sha256=p.sha(manifest), source_sha256=p.sha(__file__))
    save(out/'distribution.json', result)
    save(out/'proposed_train_weights.json', [dict(image_id=r['image_id'], positive=bool(int(r['fractured'])),
        hard=r['image_id'] in all_hard, proposed_objective_weight=float(w)) for r,w in zip(train,weights)])
    save(out/'completion.json', dict(status='completed_diagnostic_only', model_trained=False, weighting_applied=False, test_images_read=0))
    print(json.dumps({key:value for key,value in result.items() if key!='nonexclusive_source_groups'}, indent=2))


if __name__=='__main__':
    main()
