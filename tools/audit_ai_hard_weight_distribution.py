"""Registered hard-example objective mass using TRAIN JSON metadata only.

No archive, image, mask tensor, checkpoint, or prediction is opened. This audit
does not train, change weights, or alter any frozen experiment source.
"""
import argparse
import csv
import datetime
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.ai_bounded_hard_weights import class_normalized_weights


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def quantile(values,q):
    ordered=sorted(values)
    index=(len(ordered)-1)*q
    low,high=math.floor(index),math.ceil(index)
    return ordered[low]+(ordered[high]-ordered[low])*(index-low)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--protocol',default='experiments/session_20261007_ai_loop_01/HARD_EXPERIMENT_PROTOCOL.json')
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    protocol_path,out=Path(args.protocol).resolve(),Path(args.out).resolve()
    if ROOT not in protocol_path.parents or ROOT not in out.parents or out.exists():
        raise ValueError('Registered workspace protocol and exclusive evidence output required')
    opened=[]
    def read(path,registered=True):
        path=Path(path).resolve()
        if ROOT not in path.parents or path.suffix!='.json':
            raise ValueError('Only workspace JSON metadata may be opened')
        digest=sha(path)
        if registered:
            expected=next((d for s,d in protocol['input_hashes'].items() if (ROOT/s).resolve()==path),None)
            if expected is None or digest!=expected:
                raise ValueError('Metadata missing from registration or changed: '+str(path.relative_to(ROOT)))
        opened.append(dict(path=str(path.relative_to(ROOT)),sha256=digest))
        return json.loads(path.read_text())
    protocol=read(protocol_path,registered=False)
    if protocol['status']!='registered_after_completed_native_failure_analysis' or protocol['major_factor']!='bounded_within_class_hard_example_weighting':
        raise ValueError('Registered one-factor hard-example experiment required')
    helper='tools/ai_bounded_hard_weights.py'
    if sha(ROOT/helper)!=protocol['input_hashes'][helper]:
        raise ValueError('Frozen weight definition changed')
    manifest_path=ROOT/'experiments/data_v3_reliability_20261007/manifest.json'
    if sha(manifest_path)!='4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318':
        raise ValueError('Frozen v3 metadata changed')
    document=read(manifest_path)
    rows=[r for r in document['rows'] if r['split']=='train']
    ids=[r['image_id'] for r in rows]
    if len(rows)!=2808 or len(set(ids))!=2808 or sum(int(r['fractured']) for r in rows)!=493:
        raise ValueError('Exactly 2808 unique TRAIN sources with493 positives required')
    catalog=ROOT/protocol['hard_catalog']
    hp_doc=read(catalog/'HARD_POSITIVE_SET.json');hn_doc=read(catalog/'HARD_NEGATIVE_SET.json')
    hp,hn=hp_doc['image_ids'],hn_doc['image_ids']
    completion=read(catalog/'completion.json')
    proposed=read(catalog/'proposed_example_weights.json')
    if completion['status']!='completed_TRAIN_hard_catalog_refresh_only':
        raise ValueError('Completed TRAIN-only catalog required')
    if (len(hp)!=109 or len(hn)!=713 or len(set(hp))!=109 or len(set(hn))!=713
            or protocol['factor']['hard_positive_count']!=109 or protocol['factor']['hard_negative_count']!=713
            or protocol['factor']['reference']!=1 or protocol['factor']['candidate']!=2):
        raise ValueError('Registered unique109/713 hard catalogs required')
    weights=class_normalized_weights(rows,hp,hn,2)
    reference=class_normalized_weights(rows,hp,hn,1)
    if (proposed['factor']!=2 or proposed['mean_within_each_class']!=1
            or set(proposed['weights'])!=set(ids)
            or any(not math.isclose(proposed['weights'][i],weights[i],rel_tol=1e-12,abs_tol=1e-12) for i in ids)):
        raise ValueError('Proposed weights differ from registered within-class definition')
    if not all(v==1 for v in reference.values()):
        raise ValueError('Neutral reference is not exact natural objective mass')
    hard=set(hp)|set(hn)
    # Native mask area is already saved metadata. No native masks are opened.
    sizes=[r['mask_pixels']/(r['width']*r['height']) for r in rows if int(r['fractured'])]
    small_cutoff=quantile(sizes,.25)
    source_flags=('hand','leg','hip','shoulder','mixed','frontal','lateral','oblique','hardware','multiscan')
    for row in rows:
        if any(key not in row or int(row[key]) not in (0,1) for key in source_flags):
            raise ValueError('Source flags must be explicit binary metadata')
    predicates={name:(lambda r,key=name:bool(int(r[key]))) for name in source_flags}
    predicates.update(multiple_annotation_ids=lambda r:len(r['annotation_ids'])>1,
        source_fracture_count_above_one=lambda r:int(r['fracture_count'])>1,
        small_native_mask_proxy=lambda r:bool(int(r['fractured'])) and r['mask_pixels']/(r['width']*r['height'])<=small_cutoff,
        no_source_anatomy_flag=lambda r:not any(int(r[key]) for key in ('hand','leg','hip','shoulder','mixed')),
        no_source_view_flag=lambda r:not any(int(r[key]) for key in ('frontal','lateral','oblique')))
    classes={};table=[]
    for label,name,expected in ((1,'fracture',493),(0,'normal',2315)):
        selected=[r for r in rows if int(r['fractured'])==label]
        mass=math.fsum(weights[r['image_id']] for r in selected)
        if len(selected)!=expected or not math.isclose(mass,expected,rel_tol=1e-12,abs_tol=1e-9):
            raise ValueError('Original source-label class mass was not preserved')
        by_flag={}
        for flag,predicate in predicates.items():
            flagged=[r for r in selected if predicate(r)]
            count=len(flagged);weighted=math.fsum(weights[r['image_id']] for r in flagged)
            record=dict(label_class=name,flag=flag,source_images=count,
                source_share_within_class=count/expected,weighted_objective_mass=weighted,
                weighted_share_within_class=weighted/mass,
                share_change_percentage_points=100*(weighted/mass-count/expected),
                objective_mass_ratio=weighted/count if count else None,
                hard_images=sum(r['image_id'] in hard for r in flagged),
                conservative_groups=len({r['group'] for r in flagged}))
            by_flag[flag]=record;table.append(record)
        hard_rows=[r for r in selected if r['image_id'] in hard]
        classes[name]=dict(source_images=expected,weighted_objective_mass=mass,
            mean_weight=mass/expected,hard_images=len(hard_rows),
            hard_source_share=len(hard_rows)/expected,
            hard_weighted_share=math.fsum(weights[r['image_id']] for r in hard_rows)/mass,
            hard_weight=weights[hard_rows[0]['image_id']],
            ordinary_weight=weights[next(r['image_id'] for r in selected if r['image_id'] not in hard)],
            nonexclusive_flags=by_flag)
    by_id={r['image_id']:r for r in rows}
    if any(i not in by_id or not int(by_id[i]['fractured']) for i in hp) or any(i not in by_id or int(by_id[i]['fractured']) for i in hn):
        raise ValueError('Non-TRAIN case or incorrect source label in catalogs')
    annotation_count_disagreements=[r['image_id'] for r in rows
        if (len(r['annotation_ids'])>1)!=(int(r['fracture_count'])>1)]
    largest=sorted((r for r in table if r['source_images']),
        key=lambda r:abs(r['share_change_percentage_points']),reverse=True)
    result=dict(status='completed_TRAIN_metadata_objective_mass_audit',
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        protocol_sha256=sha(protocol_path),read_metadata=opened,
        frozen_weight_helper_sha256=sha(ROOT/helper),source_sha256=sha(__file__),
        unique_TRAIN_images=2808,unique_source_groups=len({r['group'] for r in rows}),
        no_duplicate_samples=True,hard_positive_count=109,hard_negative_count=713,
        all_hard_cases_in_TRAIN_and_source_label_correct=True,
        reference_exact_unit_weights=True,proposed_weights_match_registered_definition=True,
        class_masses_preserved=True,classes=classes,
        small_native_mask_definition=dict(cutoff_fraction=small_cutoff,percentile=25,
            source='Frozen TRAIN positive native mask_pixels/(width*height) metadata',
            clinical_subtle_or_nondisplaced_label=False),
        multiple_annotation_vs_source_count_disagreement_ids=annotation_count_disagreements,
        largest_absolute_share_shifts=largest[:12],
        available_fields=sorted(set.intersection(*(set(r) for r in rows))),
        missing_reliability_metadata=['patient identifiers','study identifiers','expert subtle fracture labels',
            'expert nondisplaced fracture labels','radiologist correction/adjudication'],
        interpretation='All source images remain sampled once; the bounded loss weighting changes effective within-class objective emphasis. Class mass preservation does not preserve every anatomy/view share or imply a measured model gain.',
        limitations=['Flags are source metadata and nonexclusive; subgroup masses must not be summed across flags',
            'Frontal does not establish verified AP; combined view flags may reflect composite images rather than linked study views',
            'Conservative duplicate groups are not patient/study identifiers',
            'Multiple annotated regions do not prove multiple clinical fractures',
            'Small annotated mask fraction is not an expert subtle/nondisplaced diagnosis',
            'This audit cannot infer cause, external generalization, accuracy, or reliability improvement'],
        new_image_reads=0,new_mask_tensor_reads=0,new_checkpoint_reads=0,new_prediction_reads=0,
        inference_performed=False,model_trained=False,weights_modified=False,
        validation_images_read=0,calibration_images_read=0,test_images_read=0,promotion=False)
    out.mkdir()
    (out/'distribution.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    with (out/'subgroup_mass.csv').open('x',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(table[0]));writer.writeheader();writer.writerows(table)
    # These are small TRAIN metadata records, not new samples or predictions.
    per_case=[dict(image_id=r['image_id'],label_class='fracture' if int(r['fractured']) else 'normal',
        hard=r['image_id'] in hard,reference_weight=1.,candidate_weight=weights[r['image_id']],
        conservative_group=r['group']) for r in rows]
    (out/'verified_TRAIN_weights.json').write_text(json.dumps(per_case,indent=2)+'\n',encoding='utf-8')
    (out/'source_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (out/'completion.json').write_text(json.dumps(dict(status=result['status'],
        distribution_sha256=sha(out/'distribution.json'),subgroup_mass_sha256=sha(out/'subgroup_mass.csv'),
        verified_weights_sha256=sha(out/'verified_TRAIN_weights.json'),
        new_image_reads=0,inference_performed=False,model_trained=False,weights_modified=False,
        calibration_images_read=0,test_images_read=0),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],class_summary={k:{key:v for key,v in d.items() if key!='nonexclusive_flags'} for k,d in classes.items()},
        largest_absolute_share_shifts=largest[:8]),indent=2))


if __name__=='__main__':main()
