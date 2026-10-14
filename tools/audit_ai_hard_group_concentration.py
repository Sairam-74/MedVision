"""TRAIN metadata only: existing related-group and decoded-exact concentration.

Reads JSON metadata and saved historical label-audit metadata only. Opens no
images, masks, model tensors, or predictions, and never changes training.
"""
import argparse
from collections import defaultdict
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


def effective_n(values):
    return math.fsum(values)**2/math.fsum(v*v for v in values)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',required=True)
    args=ap.parse_args();out=Path(args.out).resolve()
    if ROOT not in out.parents or out.exists():
        raise ValueError('Exclusive workspace evidence output required')
    inputs=[]
    def read(relative,registered=False):
        path=(ROOT/relative).resolve()
        if ROOT not in path.parents or path.suffix!='.json':
            raise ValueError('Only workspace JSON metadata is permitted')
        digest=sha(path)
        if registered:
            expected=next((d for name,d in protocol['input_hashes'].items() if (ROOT/name).resolve()==path),None)
            if expected is None or expected!=digest:
                raise ValueError('Registered metadata changed: '+relative)
        value=json.loads(path.read_text())
        if sha(path)!=digest: raise ValueError('Metadata changed while reading')
        inputs.append(dict(path=str(path.relative_to(ROOT)),sha256=digest))
        return value
    protocol=read('experiments/session_20261007_ai_loop_01/HARD_EXPERIMENT_PROTOCOL.json')
    if protocol['status']!='registered_after_completed_native_failure_analysis' or protocol['major_factor']!='bounded_within_class_hard_example_weighting':
        raise ValueError('Registered one-factor hard-weight pair required')
    manifest=read('experiments/data_v3_reliability_20261007/manifest.json',True)
    rows=[r for r in manifest['rows'] if r['split']=='train']
    by_id={r['image_id']:r for r in rows}
    if len(rows)!=2808 or len(by_id)!=2808 or sum(int(r['fractured']) for r in rows)!=493:
        raise ValueError('Frozen unique TRAIN membership differs')
    catalog=protocol['hard_catalog']
    hp=read(catalog+'/HARD_POSITIVE_SET.json',True)['image_ids']
    hn=read(catalog+'/HARD_NEGATIVE_SET.json',True)['image_ids']
    proposed=read(catalog+'/proposed_example_weights.json',True)
    if len(hp)!=109 or len(set(hp))!=109 or len(hn)!=713 or len(set(hn))!=713:
        raise ValueError('Unique109/713 hard membership required')
    if sha(ROOT/'tools/ai_bounded_hard_weights.py')!=protocol['input_hashes']['tools/ai_bounded_hard_weights.py']:
        raise ValueError('Frozen weighting definition changed')
    weights=class_normalized_weights(rows,hp,hn,2)
    if set(proposed['weights'])!=set(by_id) or any(not math.isclose(proposed['weights'][i],weights[i],rel_tol=1e-12,abs_tol=1e-12) for i in by_id):
        raise ValueError('Registered weights differ')
    hard=set(hp)|set(hn)
    partitions={}
    for field in ('group','decoded_sha256','sha256'):
        groups=defaultdict(list)
        for row in rows:
            key=row.get(field)
            if not isinstance(key,str) or not key:
                raise ValueError('Complete saved '+field+' metadata required')
            groups[key].append(row)
        partitions[field]=dict(groups)
    if len(partitions['group'])!=2626:
        raise ValueError('Expected2626 conservative source groups')

    def group_records(field,members):
        records=[]
        for key,group in members.items():
            mass=math.fsum(weights[r['image_id']] for r in group)
            labels=sorted({int(r['fractured']) for r in group})
            records.append(dict(group_key=key,group_definition=field,source_images=len(group),
                image_ids=sorted(r['image_id'] for r in group),source_labels=labels,
                hard_image_ids=sorted(r['image_id'] for r in group if r['image_id'] in hard),
                reference_objective_mass=len(group),candidate_objective_mass=mass,
                reference_share=len(group)/2808,candidate_share=mass/2808,
                mass_ratio=mass/len(group),
                unique_decoded_hashes=len({r['decoded_sha256'] for r in group}),
                unique_encoded_hashes=len({r['sha256'] for r in group}),
                conservative_group_ids=sorted({r['group'] for r in group})))
        return sorted(records,key=lambda r:(-r['candidate_objective_mass'],-r['source_images'],r['group_key']))

    summaries={};records_by_type={}
    for field,members in partitions.items():
        records=group_records(field,members);records_by_type[field]=records
        duplicate=[r for r in records if r['source_images']>1]
        classes={}
        for label,name in ((1,'fracture'),(0,'normal')):
            selected=[r for r in rows if int(r['fractured'])==label]
            class_group_masses=[];class_reference=[]
            for group in members.values():
                subset=[r for r in group if int(r['fractured'])==label]
                if subset:
                    class_reference.append(len(subset))
                    class_group_masses.append(math.fsum(weights[r['image_id']] for r in subset))
            natural_ess=effective_n(class_reference);weighted_ess=effective_n(class_group_masses)
            classes[name]=dict(source_images=len(selected),group_entries=len(class_reference),
                source_reference_ESS=float(len(selected)),
                source_candidate_ESS=effective_n([weights[r['image_id']] for r in selected]),
                group_reference_ESS=natural_ess,group_candidate_ESS=weighted_ess,
                group_ESS_change_percent=100*(weighted_ess/natural_ess-1),
                total_reference_mass=len(selected),total_candidate_mass=math.fsum(weights[r['image_id']] for r in selected))
        natural_ess=effective_n([r['reference_objective_mass'] for r in records])
        weighted_ess=effective_n([r['candidate_objective_mass'] for r in records])
        summaries[field]=dict(unique_groups=len(records),multi_source_groups=len(duplicate),
            sources_in_multi_source_groups=sum(r['source_images'] for r in duplicate),
            excess_source_copies=sum(r['source_images']-1 for r in duplicate),
            max_source_images=max(r['source_images'] for r in records),
            max_candidate_group_mass=records[0]['candidate_objective_mass'],
            max_candidate_group_share=records[0]['candidate_share'],
            reference_group_ESS=natural_ess,candidate_group_ESS=weighted_ess,
            group_ESS_change_percent=100*(weighted_ess/natural_ess-1),
            top10_reference_group_mass_share=math.fsum(sorted((r['reference_objective_mass'] for r in records),reverse=True)[:10])/2808,
            top10_candidate_group_mass_share=math.fsum(r['candidate_objective_mass'] for r in records[:10])/2808,
            label_classes=classes,
            contradictory_source_label_groups=[r for r in records if len(r['source_labels'])>1],
            largest_candidate_groups=records[:12])

    hard_membership={}
    for name,ids in (('hard_positive',set(hp)),('hard_negative',set(hn))):
        classes={}
        for field,members in partitions.items():
            shared_all=[];shared_hard=[]
            for key,group in members.items():
                selected=ids&{r['image_id'] for r in group}
                if not selected: continue
                if len(group)>1: shared_all.extend(sorted(selected))
                if len(selected)>1: shared_hard.extend(sorted(selected))
            represented={by_id[i][field] for i in ids}
            classes[field]=dict(hard_sources=len(ids),distinct_group_keys=len(represented),
                hard_sources_sharing_key_with_another_TRAIN_source=len(shared_all),
                hard_sources_sharing_key_with_another_hard_source=len(shared_hard),
                excess_hard_entries_over_distinct_keys=len(ids)-len(represented),
                sharing_other_TRAIN_source_ids=sorted(shared_all),
                sharing_other_hard_source_ids=sorted(shared_hard))
        hard_membership[name]=classes

    # Historical metadata documents earlier quarantine/annotation disagreement;
    # no masks or images are reread and no labels are adjudicated here.
    historical=read('experiments/phase3_review/duplicate_label_audit.json')
    revision=read('experiments/data_v2/revision.json')
    quarantine=[r for r in manifest['exclusions'] if 'Contradictory' in r['reason']]
    quarantine_ids={r['image_id'] for r in quarantine}
    if len(quarantine_ids)!=7 or quarantine_ids!=set(revision['quarantined_ids']) or quarantine_ids&set(by_id):
        raise ValueError('Historical seven-case quarantine is not preserved')
    annotation_variants=[]
    for saved in historical['exact_duplicate_union_mask_variants']:
        ids=[i for i in saved['image_ids'] if i in by_id]
        if len(ids)<2: continue
        decoded={by_id[i]['decoded_sha256'] for i in ids}
        if len(decoded)!=1: raise ValueError('Historical exact variants do not match saved decoded hash metadata')
        annotation_variants.append(dict(image_ids=ids,source_labels=sorted({int(by_id[i]['fractured']) for i in ids}),
            historical_union_mask_hashes=saved['union_mask_sha256'],
            hard_image_ids=sorted(set(ids)&hard),
            reference_mass=len(ids),candidate_mass=math.fsum(weights[i] for i in ids),
            note='Saved earlier union-mask disagreement; no new mask inspection or adjudication'))
    result=dict(status='completed_TRAIN_metadata_group_concentration_audit',
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        protocol_sha256=sha(ROOT/'experiments/session_20261007_ai_loop_01/HARD_EXPERIMENT_PROTOCOL.json'),
        read_metadata=inputs,source_sha256=sha(__file__),TRAIN_sources=2808,conservative_source_groups=2626,
        group_summaries=summaries,hard_membership=hard_membership,
        historical_quarantine=dict(case_ids=sorted(quarantine_ids),source_labels={r['image_id']:r['fractured'] for r in quarantine},
            excluded_from_current_TRAIN=True,labels_changed=False,
            historical_conflict_groups=historical['contradictory_case_label_groups']),
        retained_TRAIN_annotation_variant_groups=annotation_variants,
        count_retained_TRAIN_annotation_variant_groups=len(annotation_variants),
        no_new_resampling_or_source_duplication=True,class_masses_preserved=True,
        interpretation='Repeated source files/groups are inherited dataset composition. Bounded factor2 multiplies loss per original source once; it does not create new copies. ESS here is the algebraic objective-mass concentration statistic (sum mass)^2/sum mass^2, not a measured number of independent patients or a generalization estimate.',
        limitations=['Conservative group IDs reflect related-image candidates, not proven patient or study identities',
            'Decoded hashes are saved exact-pixel metadata; no pixels were decoded or reverified in this audit',
            'Existing duplicate labels/mask disagreements are metadata findings, not new expert clinical adjudication',
            'Full-epoch source coverage remains the trainer runtime assertion; this audit verifies source metadata and fixed weight concentration',
            'No cause, accuracy, reliability, or external-generalization claim follows from concentration alone'],
        new_image_reads=0,new_mask_reads=0,new_model_reads=0,new_prediction_reads=0,
        inference_performed=False,model_trained=False,weights_modified=False,
        calibration_images_read=0,test_images_read=0,promotion=False)
    out.mkdir()
    (out/'concentration.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    for field,records in records_by_type.items():
        (out/(field+'_TRAIN_group_masses.json')).write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    (out/'source_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (out/'completion.json').write_text(json.dumps(dict(status=result['status'],
        concentration_sha256=sha(out/'concentration.json'),new_image_reads=0,inference_performed=False,
        model_trained=False,weights_modified=False,test_images_read=0),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],summary={k:{key:v for key,v in d.items() if key not in ('largest_candidate_groups','contradictory_source_label_groups','label_classes')} for k,d in summaries.items()},
        hard_membership_summary={name:{field:{key:v for key,v in data.items() if not key.endswith('_ids')} for field,data in groups.items()} for name,groups in hard_membership.items()},
        current_exact_label_conflicts=len(summaries['decoded_sha256']['contradictory_source_label_groups']),
        current_related_group_mixed_labels=len(summaries['group']['contradictory_source_label_groups']),
        quarantine_cases=len(quarantine_ids),retained_TRAIN_annotation_variant_groups=len(annotation_variants)),indent=2))


if __name__=='__main__':main()
