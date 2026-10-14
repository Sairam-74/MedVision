"""Refresh existing TRAIN hard catalogs using two completed raw-grid TRAIN fits."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.ai_atomic_io import json_atomic
from tools.evaluate_ai_baseline import sha
from tools.ai_bounded_hard_weights import class_normalized_weights,fixtures


def read_fit(path,rows):
    completion=json.loads((path/'completion.json').read_text())
    config=json.loads((path/'config.json').read_text())
    if completion['status']!='completed_read_only_TRAIN_fit' or completion['train_cases']!=2808:
        raise ValueError('Full TRAIN-fit completion required')
    if config['augmentation'] or config['validation_images_read'] or config['calibration_images_read'] or config['test_images_read']:
        raise ValueError('Require unaugmented TRAIN-only fit')
    cases=[json.loads(line) for line in (path/'train_cases.jsonl').read_text().splitlines() if line.strip()]
    if len(cases)!=2808 or {c['image_id'] for c in cases}!={r['image_id'] for r in rows}:
        raise ValueError('TRAIN membership changed')
    by_id={c['image_id']:c for c in cases}
    if any(bool(int(r['fractured']))!=by_id[r['image_id']]['positive'] for r in rows):
        raise ValueError('Explicit source labels differ')
    return by_id,config


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--reference-fit',required=True);ap.add_argument('--candidate-fit',required=True)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    ref,cand,out=[Path(v).resolve() for v in (args.reference_fit,args.candidate_fit,args.out)]
    if any(ROOT not in v.parents for v in (ref,cand,out)) or out.exists():
        raise ValueError('Workspace evidence and exclusive output required')
    manifest=ROOT/'experiments/data_v3_reliability_20261007/manifest.json'
    if sha(manifest)!='4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318':
        raise ValueError('Frozen split changed')
    rows=[r for r in json.loads(manifest.read_text())['rows'] if r['split']=='train']
    r,rc=read_fit(ref,rows);c,cc=read_fit(cand,rows)
    for key in ('manifest_sha256','cache','preprocess'):
        if rc[key]!=cc[key]: raise ValueError('Require matched TRAIN-fit geometry/data')
    old=ROOT/'experiments/AI_TRAIN_HARD_SETS_20261007'
    positives=set(json.loads((old/'HARD_POSITIVE_SET.json').read_text())['image_ids'])
    negatives=set(json.loads((old/'HARD_NEGATIVE_SET.json').read_text())['image_ids'])
    labels={row['image_id']:bool(int(row['fractured'])) for row in rows}
    if not positives<=set(labels) or not negatives<=set(labels) or any(not labels[i] for i in positives) or any(labels[i] for i in negatives):
        raise ValueError('Historical TRAIN catalogs invalid')
    hp=sorted(i for i in positives if r[i]['dice']<.2 and c[i]['dice']<.2)
    hn=sorted(i for i in negatives if r[i]['prediction_present'] and c[i]['prediction_present'])
    # This is a bounded proposed TRAIN-only weighting, never applied here.
    weights=class_normalized_weights(rows,hp,hn,factor=2.)
    summary=dict(historical_hard_positive=len(positives),historical_hard_negative=len(negatives),
        persistent_hard_positive=len(hp),persistent_hard_negative=len(hn),
        positive_class_total_weight=sum(weights[i] for i in labels if labels[i]),
        normal_class_total_weight=sum(weights[i] for i in labels if not labels[i]),
        minimum_weight=min(weights.values()),maximum_weight=max(weights.values()),
        raw_hard_factor=2.,weighting_applied=False,no_duplicate_samples=True,
        validation_images_read=0,calibration_images_read=0,test_images_read=0,
        clinical_subtle_nondisplaced_labels_available=False,
        scope='Existing historical TRAIN hard examples still wrong in BOTH selected models; grid diagnostic only',
        next='Root must first inspect matched native audits and then register one factor before any training')
    out.mkdir()
    json_atomic(out/'HARD_POSITIVE_SET.json',dict(image_ids=hp,criterion='Historical TRAIN hard-positive AND independent grid Dice<0.2 in BOTH current models'))
    json_atomic(out/'HARD_NEGATIVE_SET.json',dict(image_ids=hn,criterion='Historical TRAIN hard-negative AND independent grid mask alert in BOTH current models'))
    json_atomic(out/'proposed_example_weights.json',dict(factor=2.,mean_within_each_class=1.,weights=weights,applied=False))
    paths=[manifest,old/'HARD_POSITIVE_SET.json',old/'HARD_NEGATIVE_SET.json',ref/'train_cases.jsonl',cand/'train_cases.jsonl',ref/'config.json',cand/'config.json',Path(__file__),ROOT/'tools/ai_bounded_hard_weights.py']
    json_atomic(out/'config.json',dict(input_hashes={str(v.relative_to(ROOT)):sha(v) for v in paths},
        positive_dice_cutoff=.2,normal_mask_threshold=.5,hard_factor=2.,classifier_gating=False))
    json_atomic(out/'weight_fixtures.json',fixtures())
    json_atomic(out/'completion.json',dict(status='completed_TRAIN_hard_catalog_refresh_only',**summary))
    print(json.dumps(summary,indent=2))


if __name__=='__main__': main()
