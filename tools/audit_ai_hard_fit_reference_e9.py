"""Frozen hard catalogs against completed E7/E8/E9 raw TRAIN-grid outputs.

CPU JSON/source-hash analysis only. Never opens images, mask arrays, checkpoint
tensors, E10 results, calibration cases, or reserved-test predictions.
"""
import argparse
from collections import Counter
import datetime
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parents[1]
MANIFEST_SHA='4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318'
OLD_FIT_HELPER_SHA='19eb9dcac7af389ab807f3000acf520a29edb8ed7e39037b8282a463cf465d2f'


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle,'sha256').hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True)
    args=ap.parse_args();out=Path(args.out).resolve()
    if ROOT not in out.parents or out.exists(): raise ValueError('Exclusive workspace evidence required')
    inputs=[]
    def read(relative,lines=False):
        path=(ROOT/relative).resolve()
        if ROOT not in path.parents or path.suffix not in ('.json','.jsonl'):
            raise ValueError('Only saved workspace metadata/results may be read')
        digest=sha(path);raw=path.read_text()
        if sha(path)!=digest: raise ValueError('Completed metadata changed while reading')
        inputs.append(dict(path=str(path.relative_to(ROOT)),sha256=digest))
        return [json.loads(line) for line in raw.splitlines() if line.strip()] if lines else json.loads(raw)
    protocol=read('experiments/session_20261007_ai_loop_01/HARD_EXPERIMENT_PROTOCOL.json')
    if protocol['reference']!='AI_E9_v3_hard_reference' or protocol['factor']['reference']!=1:
        raise ValueError('Registered unchanged continuation reference required')
    document=read('experiments/data_v3_reliability_20261007/manifest.json')
    if inputs[-1]['sha256']!=MANIFEST_SHA: raise ValueError('Frozen TRAIN manifest changed')
    rows=[r for r in document['rows'] if r['split']=='train'];allowed={r['image_id']:r for r in rows}
    if len(rows)!=len(allowed) or len(rows)!=2808 or sum(int(r['fractured']) for r in rows)!=493:
        raise ValueError('Exact unique TRAIN2808/493 membership required')
    catalog=protocol['hard_catalog']
    hard_positive=read(catalog+'/HARD_POSITIVE_SET.json')['image_ids']
    hard_negative=read(catalog+'/HARD_NEGATIVE_SET.json')['image_ids']
    catalog_completion=read(catalog+'/completion.json')
    if catalog_completion['status']!='completed_TRAIN_hard_catalog_refresh_only':
        raise ValueError('Frozen completed hard catalog required')
    for name,n,label in ((hard_positive,109,1),(hard_negative,713,0)):
        if len(name)!=len(set(name)) or len(name)!=n or not set(name)<=set(allowed):
            raise ValueError('Hard catalog uniqueness/count/TRAIN membership changed')
        if any(int(allowed[i]['fractured'])!=label for i in name):
            raise ValueError('Hard catalog labels differ from explicit TRAIN source labels')
    for entry in inputs:
        expected=next((d for p,d in protocol['input_hashes'].items() if (ROOT/p).resolve()==(ROOT/entry['path']).resolve()),None)
        if entry['path'].endswith('HARD_EXPERIMENT_PROTOCOL.json'): continue
        if expected!=entry['sha256']: raise ValueError('Input is not identical to frozen registration: '+entry['path'])
    sets={'hard_positive':set(hard_positive),
          'ordinary_positive':{i for i,r in allowed.items() if int(r['fractured'])}-set(hard_positive),
          'hard_negative':set(hard_negative),
          'ordinary_negative':{i for i,r in allowed.items() if not int(r['fractured'])}-set(hard_negative)}
    if set.union(*sets.values())!=set(allowed) or sum(len(v) for v in sets.values())!=2808:
        raise ValueError('Hard/ordinary strata do not form an exact unique TRAIN partition')
    sources_verified=[];fits={};metadata={}
    for model,directory in (('E7','AI_LEARNING_FIT_E7_v3_presence_r2'),
                            ('E8','AI_LEARNING_FIT_E8_v3_presence_r2'),
                            ('E9','AI_LEARNING_FIT_E9_v3_hard_reference')):
        prefix='experiments/'+directory
        config=read(prefix+'/config.json');completed=read(prefix+'/completion.json')
        if (completed['status']!='completed_read_only_TRAIN_fit' or completed['train_cases']!=2808
                or not completed['model_tensors_unchanged'] or config['augmentation'] or config['mask_gated']
                or not config['no_optimizer_steps'] or config['validation_images_read']
                or config['calibration_images_read'] or config['test_images_read']
                or config['manifest_sha256']!=MANIFEST_SHA):
            raise ValueError('Completed unaugmented ungated TRAIN-only fit required')
        bundle=read(str(Path(config['run'])/'bundle.json'))
        run_config=read(str(Path(config['run'])/'config.json'))
        if config['checkpoint_sha256']!=bundle['checkpoint_sha256'] or config['epoch']!=bundle['epoch']:
            raise ValueError('Saved fit is not the selected completed model metadata')
        if model=='E9' and (run_config['hard_factor']!=1 or run_config['presence_weight']!=0):
            raise ValueError('E9 is not the unchanged mask-only continuation')
        metadata[model]=dict(fit_directory=prefix,checkpoint_sha256=config['checkpoint_sha256'],
            selected_epoch=config['epoch'],global_epoch=bundle['global_epoch'],
            presence_weight=run_config['presence_weight'],preprocess=config['preprocess'],cache=config['cache'])
        for source,digest in config['source_hashes'].items():
            source_path=ROOT/source;verified_path=source_path
            if sha(source_path)!=digest:
                if source.replace('\\','/')=='tools/audit_ai_presence_train_fit.py' and digest==OLD_FIT_HELPER_SHA:
                    verified_path=ROOT/'experiments/session_20261007_ai_loop_01/audit_ai_presence_train_fit_completed_r2_source.py'
                else: raise ValueError('Recorded source changed without preserved version: '+source)
            if sha(verified_path)!=digest: raise ValueError('Recorded source hash is not verifiable')
            sources_verified.append(dict(model=model,original_source=source,verified_source=str(verified_path.relative_to(ROOT)),sha256=digest))
        cases=read(prefix+'/train_cases.jsonl',True)
        by_id={c['image_id']:c for c in cases}
        if len(cases)!=len(by_id) or set(by_id)!=set(allowed): raise ValueError('Completed fit coverage is not exact unique TRAIN membership')
        for image_id,case in by_id.items():
            if case['positive']!=bool(int(allowed[image_id]['fractured'])) or case['group']!=allowed[image_id]['group']:
                raise ValueError('Source group or explicit labels differ')
            if case['prediction_present']!=bool(case['tp_pixels']+case['fp_pixels']):
                raise ValueError('Saved grid alert and mask pixel counts disagree')
            if case['zero_overlap_positive']!=bool(case['positive'] and case['tp_pixels']==0):
                raise ValueError('Saved zero-overlap flag disagrees with grid pixels')
            if not case['positive'] and (case['tp_pixels'] or case['fn_pixels']):
                raise ValueError('Normal source has nonempty reference pixels')
        fits[model]=by_id
    if any(metadata[m]['preprocess']!=metadata['E7']['preprocess'] or metadata[m]['cache']!=metadata['E7']['cache'] for m in ('E8','E9')):
        raise ValueError('Completed fit geometries differ')
    if any(len({fits[m][i]['tp_pixels']+fits[m][i]['fn_pixels'] for m in fits})!=1 for i in allowed):
        raise ValueError('Same-ID saved TRAIN reference masks differ in grid area')
    if any(fits[m][i]['dice']>=.2 for i in hard_positive for m in ('E7','E8')) or any(not fits[m][i]['prediction_present'] for i in hard_negative for m in ('E7','E8')):
        raise ValueError('Persistent hard catalog does not reproduce its recorded definition')
    def summary(ids,model):
        cases=[fits[model][i] for i in sorted(ids)]
        positive=cases[0]['positive']
        if any(c['positive']!=positive for c in cases): raise ValueError('Single-source-label stratum required')
        tp,fp,fn=[sum(c[k] for c in cases) for k in ('tp_pixels','fp_pixels','fn_pixels')]
        alerts=sum(c['prediction_present'] for c in cases)
        value=dict(images=len(cases),conservative_groups=len({allowed[i]['group'] for i in ids}),
            distinct_decoded_hashes=len({allowed[i]['decoded_sha256'] for i in ids}),
            mask_alerts=alerts,mask_alert_rate=alerts/len(cases),
            empty_masks=len(cases)-alerts,pixel_counts=dict(tp=tp,fp=fp,fn=fn))
        if positive:
            value.update(mean_Dice=statistics.mean(c['dice'] for c in cases),median_Dice=statistics.median(c['dice'] for c in cases),
                mean_IoU=statistics.mean(c['iou'] for c in cases),
                GT_overlap_masks=sum(c['tp_pixels']>0 for c in cases),
                zero_GT_overlap_masks=sum(c['tp_pixels']==0 for c in cases),
                nonempty_wrong_region_masks=sum(c['prediction_present'] and c['tp_pixels']==0 for c in cases),
                masks_Dice_below_0_2=sum(c['dice']<.2 for c in cases),
                pixel_precision=tp/(tp+fp) if tp+fp else None,pixel_recall=tp/(tp+fn))
        else:
            value.update(normal_FP=alerts,normal_TN=len(cases)-alerts,false_positive_rate=alerts/len(cases),
                positive_Dice=None,positive_IoU=None,zero_GT_overlap_not_applicable=True)
        return value
    summaries={name:{m:summary(ids,m) for m in fits} for name,ids in sets.items()}
    transitions={}
    for name,ids in sets.items():
        positive='positive' in name
        changes={}
        for old in ('E7','E8'):
            predicates={'mask_alert_gained':lambda l,r:not l['prediction_present'] and r['prediction_present'],
                        'mask_alert_removed':lambda l,r:l['prediction_present'] and not r['prediction_present']}
            if positive:
                predicates.update(GT_overlap_gained=lambda l,r:l['tp_pixels']==0 and r['tp_pixels']>0,
                    GT_overlap_lost=lambda l,r:l['tp_pixels']>0 and r['tp_pixels']==0,
                    Dice_gain_gt_0_02=lambda l,r:r['dice']-l['dice']>.02,
                    Dice_loss_gt_0_02=lambda l,r:l['dice']-r['dice']>.02,
                    cross_Dice_0_2_up=lambda l,r:l['dice']<.2 and r['dice']>=.2,
                    cross_Dice_0_2_down=lambda l,r:l['dice']>=.2 and r['dice']<.2)
            changes[old+'_to_E9']={key:dict(n=len(chosen:=[i for i in sorted(ids) if pred(fits[old][i],fits['E9'][i])]),image_ids=chosen)
                for key,pred in predicates.items()}
        transitions[name]=changes
    result=dict(status='completed_saved_TRAIN_grid_hard_fit_reference_analysis',
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256=sha(__file__),
        protocol_sha256=sha(ROOT/'experiments/session_20261007_ai_loop_01/HARD_EXPERIMENT_PROTOCOL.json'),
        read_metadata=inputs,verified_recorded_source_hashes=sources_verified,
        exact_unique_TRAIN_coverage_and_labels_verified=True,same_grid_reference_areas_verified=True,
        hard_positive_sources=109,hard_negative_sources=713,ordinary_positive_sources=384,ordinary_negative_sources=1602,
        persistent_definition_reproduced_in_E7_E8=True,model_metadata=metadata,
        summaries=summaries,same_ID_transitions=transitions,
        scope='Frozen hard109/713 and ordinary TRAIN cases; saved unaugmented independent-mask grid outputs only',
        limitations=['Hard strata were selected using E7/E8 error outputs, so their low scores/high FP counts in those models are expected by construction',
            'E9 uses ordinary unweighted continuation from selected E7; changes cannot be attributed to hard weighting or compared as a controlled E8-versus-E9 ablation',
            'These are TRAIN fit results, not native VAL acceptance, clinical difficulty, or independent generalization',
            'Source groups are conservative related-image candidates, not proven patients or studies; inherited exact-source repetition remains',
            'Presence head and review union are deliberately excluded; empty/zero-overlap distinctions refer to independent binary masks',
            'Old fit-helper prose is verified against its preserved before-source; the documented head-score interpretation correction did not change these mask outputs',
            'Do not refresh the frozen running catalogs, infer an E10 outcome, or select a subsequent factor from this reference-only audit'],
        new_image_reads=0,new_mask_array_reads=0,new_model_reads=0,new_predictions=0,
        inference_performed=False,GPU_work_performed=False,E10_results_read=False,
        calibration_images_read=0,test_images_read=0,model_trained=False,promotion=False)
    out.mkdir()
    (out/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    lines=['# E9 fit on frozen TRAIN hard cases','',
        'Completed saved-result audit only. No image/model reads, inference, E10 result reads, calibration/test access or experiment changes.','',
        'All 2,808 unique sources and explicit labels match the frozen TRAIN manifest; recorded source versions and grid reference areas were verified. Hard catalog: 109 positive and 713 normal sources.','',
        '| Positive stratum | Model | Images / groups | Mean Dice / IoU | Mask alerts | Empty masks | Nonempty wrong-region masks | Any GT overlap | Dice <0.2 |',
        '|---|---|---|---|---|---|---|---|---|']
    for name in ('hard_positive','ordinary_positive'):
        for model,s in summaries[name].items():
            lines.append(f"| {name.replace('_',' ')} | {model} | {s['images']} / {s['conservative_groups']} | {s['mean_Dice']:.6f} / {s['mean_IoU']:.6f} | {s['mask_alerts']} | {s['empty_masks']} | {s['nonempty_wrong_region_masks']} | {s['GT_overlap_masks']} | {s['masks_Dice_below_0_2']} |")
    lines+=['','| Normal stratum | Model | Images / groups | FP / TN | FP rate | False-positive grid pixels |',
        '|---|---|---|---|---|---|']
    for name in ('hard_negative','ordinary_negative'):
        for model,s in summaries[name].items():
            lines.append(f"| {name.replace('_',' ')} | {model} | {s['images']} / {s['conservative_groups']} | {s['normal_FP']} / {s['normal_TN']} | {s['false_positive_rate']:.2%} | {s['pixel_counts']['fp']} |")
    hp9=summaries['hard_positive']['E9'];hn9=summaries['hard_negative']['E9']
    lines+=['',f"Ordinary continuation alone brings {109-hp9['masks_Dice_below_0_2']} / 109 frozen hard positives to Dice >=0.2 and correctly rejects {hn9['normal_TN']} / 713 frozen hard normals. It leaves {hp9['zero_GT_overlap_masks']} hard positives without GT overlap and {hn9['normal_FP']} hard normals with false mask alerts. A mask alert is not proof of fracture localization.",'',
        'Exact same-ID transition lists, pixel overlap summaries, decoded-hash counts and source checksums are in analysis.json. The hard sets stay frozen for the later E9/E10 weighting comparison.','',
        'Limitations:','']+[f'- {v}' for v in result['limitations']]
    (out/'HARD_FIT_REFERENCE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (out/'source_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (out/'completion.json').write_text(json.dumps(dict(status=result['status'],analysis_sha256=sha(out/'analysis.json'),
        report_sha256=sha(out/'HARD_FIT_REFERENCE.md'),new_image_reads=0,inference_performed=False,GPU_work_performed=False,
        E10_results_read=False,calibration_images_read=0,test_images_read=0),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],summaries=summaries,
        transition_counts={name:{pair:{k:v['n'] for k,v in d.items()} for pair,d in pairs.items()} for name,pairs in transitions.items()}),indent=2))


if __name__=='__main__':main()
