"""Register a single foreground-BCE factor after completed actual failure review."""
import datetime
import json
from pathlib import Path
import sys

import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.evaluate_ai_baseline import sha
from tools.ai_presence_model import tensor_digest
from tools.smoke_ai_hard_candidate import optimizer_state_digest


def load(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))


def main():
    session='experiments/session_20261007_ai_loop_01'
    destination=ROOT/session/'FOREGROUND_BCE_EXPERIMENT_PROTOCOL.json'
    if destination.exists(): raise ValueError('Exclusive registration required')
    previous=load(session+'/positive_dice_queue.json')
    if previous['status']!='completed_training_and_native_audits_only':
        raise ValueError('Prior full pair must be terminal')
    guards=dict(previous['guards'])
    for path,digest in guards.items():
        if sha(ROOT/path)!=digest: raise ValueError('Previous guard changed: '+path)
    pair='experiments/AI_E11_E12_POSITIVE_DICE_PAIR'
    pair_complete=load(pair+'/completion.json')
    comparison=load(pair+'/comparison.json')
    if (pair_complete['status']!='completed' or sha(ROOT/pair/'comparison.json')!=pair_complete['comparison_sha256'] or
            comparison['validation_numerical_gate_pass'] or comparison['promotion'] or comparison['test_images_read'] or
            not comparison['decision'].startswith('REJECT')):
        raise ValueError('Rejected complete unpromoted pair required')
    paths=[session+'/positive_dice_queue.json',pair+'/comparison.json',pair+'/completion.json']
    for name,count in [('E11_all_normal_alert_sheets',139),('E11_all_positive_sheets',52),
                       ('E12_all_normal_alert_sheets',151),('E12_all_positive_sheets',56)]:
        directory=ROOT/session/name
        completed=load(str(directory.relative_to(ROOT))+'/completion.json')
        if (not completed['status'].startswith('completed_actual_native_') or
                completed['total_selected_cases']!=count or completed['actual_new_case_reviews']!=count):
            raise ValueError('Actual exhaustive native case review required: '+name)
        for file,field in [('per_case_visual_review.json','per_case_review_sha256'),
                           ('actual_sheet_notes.json','notes_sha256'),('index.json','index_sha256')]:
            if sha(directory/file)!=completed[field]: raise ValueError('Actual review identity changed')
            paths.append((Path(session)/name/file).as_posix())
        paths.append((Path(session)/name/'completion.json').as_posix())
    diagnosis='experiments/AI_FOREGROUND_GRADIENTS_E11_E12_20261009'
    dc=load(diagnosis+'/completion.json')
    ds=load(diagnosis+'/summary.json')
    if (dc['status']!='completed_TRAIN_only_frozen_foreground_gradient_diagnosis' or not dc['model_tensors_unchanged'] or
            not dc['no_optimizer_steps'] or any(dc[k] for k in ('validation_images_read','calibration_images_read','test_images_read')) or
            ds['actual_unique_TRAIN_sources']!=32 or any(not v['exactly_unchanged'] for v in ds['model_tensors_and_eval_statistics_unchanged'].values())):
        raise ValueError('Actual frozen TRAIN-only foreground diagnosis required')
    for file,field in [('config.json','config_sha256'),('summary.json','summary_sha256'),('per_case.json','per_case_sha256')]:
        if sha(ROOT/diagnosis/file)!=dc[field]: raise ValueError('Diagnosis identity changed')
        paths.append(diagnosis+'/'+file)
    paths.append(diagnosis+'/completion.json')
    initial_run='experiments/AI_E11_v3_positive_Dice_reference'
    config,bundle,state=[load(initial_run+'/'+f) for f in ('config.json','bundle.json','state.json')]
    if (state['status']!='completed' or state['epochs_finished']!=12 or bundle['epoch']!=9 or bundle['global_epoch']!=39 or
            config['hard_factor']!=2 or config['positive_dice_coefficient']!=1 or config['presence_weight']!=0 or
            config['batch_size']!=2 or config['lr']!=.0001 or config['preprocess']['size']!=256):
        raise ValueError('Selected E11 full epoch9/global39 initializer required')
    if sha(ROOT/initial_run/'best_model.pt')!=bundle['checkpoint_sha256']:
        raise ValueError('Selected initializer changed')
    snapshot=initial_run+'/epoch_009_resume.pt'
    full=torch.load(ROOT/snapshot,map_location='cpu',weights_only=True)
    if full['epoch']!=9 or full['global_epoch']!=39 or full['positive_dice_coefficient']!=1:
        raise ValueError('Selected full checkpoint metadata differs')
    model_digest=tensor_digest(full['model_state_dict'])
    optimizer_digest=optimizer_state_digest(full['optimizer_state_dict'])
    if model_digest!=tensor_digest(torch.load(ROOT/initial_run/'best_model.pt',map_location='cpu',weights_only=True)):
        raise ValueError('Full snapshot and selected model differ')
    del full
    records=[json.loads(v) for v in (ROOT/initial_run/'epochs.jsonl').read_text().splitlines() if v.strip()]
    replay={}
    for epoch,global_epoch in ((10,40),(11,41),(12,42)):
        source=initial_run+f'/epoch_{epoch:03d}_resume.pt'
        full=torch.load(ROOT/source,map_location='cpu',weights_only=True)
        record=records[epoch-1]
        if full['epoch']!=epoch or full['global_epoch']!=global_epoch or record['global_epoch']!=global_epoch:
            raise ValueError('Original control replay metadata mismatch')
        replay[str(global_epoch)]=dict(model_parameter_sha256=tensor_digest(full['model_state_dict']),
            optimizer_state_sha256=optimizer_state_digest(full['optimizer_state_dict']),validation=record['validation'],
            original_full_snapshot=source,original_full_snapshot_sha256=sha(ROOT/source))
        paths.append(source)
        del full
    reference,candidate='AI_E13_v3_foreground_BCE_reference','AI_E14_v3_foreground_BCE5'
    audits=['AI_AUDIT_E13_v3_foreground_BCE_reference','AI_AUDIT_E14_v3_foreground_BCE5']
    fits=['AI_LEARNING_FIT_E13_v3_foreground_BCE_reference','AI_LEARNING_FIT_E14_v3_foreground_BCE5']
    pair_id='AI_E13_E14_FOREGROUND_BCE_PAIR'
    smoke_output='experiments/AI_FOREGROUND_BCE_SMOKE_20261009'
    for name in (reference,candidate,*audits,*fits,pair_id,Path(smoke_output).name):
        if (ROOT/'experiments'/name).exists(): raise ValueError('Exclusive run exists: '+name)
    paths += [snapshot,'tools/register_ai_foreground_bce_pair.py','tools/train_ai_foreground_bce_candidate.py',
        'tools/queue_ai_foreground_bce_pair.py','tools/analyze_ai_foreground_bce_pair.py',
        'tools/ai_foreground_bce_loss.py','tools/smoke_ai_foreground_bce.py','tools/smoke_ai_hard_candidate.py',
        'tools/audit_ai_foreground_gradients_completed_pair.py','tools/compare_ai_positive_dice_fit_pair.py',
        'experiments/AI_POSITIVE_DICE_FIT_PAIR_E11_E12_20261008/analysis.json',
        'experiments/AI_POSITIVE_DICE_FIT_PAIR_E11_E12_20261008/completion.json',
        'experiments/AI_POSITIVE_DICE_FIT_PAIR_E11_E12_20261008/per_case_changes.jsonl']
    paths += [session+'/'+name for name in ('E11_NORMAL_FAILURE_ANALYSIS_20261008.md',
        'E11_POSITIVE_FAILURE_ANALYSIS_20261008.md','E12_NORMAL_FAILURE_ANALYSIS_20261009.md',
        'E12_POSITIVE_FAILURE_ANALYSIS_20261009.md','E11_E12_NORMAL_FULL_PANEL_FOLLOWUP_20261009.md',
        'E11_E12_ROOT_FULL_PANEL_FOLLOWUP_20261009.md','E12_POSITIVE_FULL_PANEL_FOLLOWUP_20261009.md',
        'E11_REFERENCE_INTERIM_ANALYSIS_20261008.md','E11_REFERENCE_INTERIM_ANALYSIS_20261008_DATA.json',
        'POSITIVE_DICE_CURVES_STRATA_ANALYSIS_20261009.md','POSITIVE_DICE_CURVES_STRATA_ANALYSIS_20261009_DATA.json',
        'E11_E12_COMPLETED_FAILURE_AND_NEXT_FACTOR_20261009.md','FOREGROUND_BCE_FACTOR_REVIEW_20261009.md',
        'RESEARCH_FOREGROUND_FITTING_20261009.md')]
    for run,audit,fit in [('AI_E11_v3_positive_Dice_reference','AI_AUDIT_E11_v3_positive_Dice_reference','AI_LEARNING_FIT_E11_v3_positive_Dice_reference'),
                          ('AI_E12_v3_positive_Dice2','AI_AUDIT_E12_v3_positive_Dice2','AI_LEARNING_FIT_E12_v3_positive_Dice2')]:
        paths += ['experiments/'+run+'/'+f for f in ('config.json','bundle.json','state.json','epochs.jsonl','best_model.pt')]
        paths += ['experiments/'+audit+'/'+f for f in ('metrics.json','per_case.json','completion.json')]
        paths += ['experiments/'+fit+'/'+f for f in ('config.json','metrics.json','train_cases.jsonl','completion.json')]
    for path in paths: guards[path]=sha(ROOT/path)
    result=dict(status='registered_after_completed_native_failure_analysis',
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        major_factor='foreground_pixel_bce_coefficient',reference=reference,candidate=candidate,
        initial_run=initial_run,hard_catalog=config['hard_catalog'],smoke_output=smoke_output,
        audit_ids=audits,fit_ids=fits,pair_id=pair_id,
        initialization=dict(selected_epoch=9,global_epoch=39,snapshot=snapshot,snapshot_sha256=sha(ROOT/snapshot),
            model_parameter_sha256=model_digest,optimizer_state_sha256=optimizer_digest,
            optimizer='Independently restore identical selected full E11 model and Adam, including moments and step counters'),
        reference_replay_parity=replay,
        evidence=['Completed positive Dice2 rejected:3 more FN,12 more FP,lower instance recall and worse proxy calibration',
            'Actual139/151 normal alerts and52/56 positive failures reviewed; clinical causes/subtypes remain unadjudicated',
            'Current frozen TRAIN gradient probe: suppressed hard-target probabilities, weaker hard vs ordinary foreground recovery',
            'BCE foreground-only weight5 is a moderate hypothesis; mathematical derivatives are not trained results'],
        common_config=dict(additional_epochs=12,batch_size=2,lr=.0001,seed=42,global_epochs=list(range(40,52)),
            hard_factor=2,presence_weight=0,normal_bce_weight=1,positive_dice_coefficient=1,
            segmentation_loss='Existing hard2 BCE+Dice plus mean_i(w_i*(k-1)*mean_valid(softplus(-logit)*target))',
            preprocessing='Unchanged CLAHE2/tile8/blur3/unit, stretch256',
            sampling='Natural unique2808 once per epoch; identical global-epoch seeds/augmentation; fixed109/713 hard sets',
            selection='Unchanged feasible-first/minimum normalized TP79,TN342,Dice.5237965563,IoU.3775685933; earlier ties',
            masks='Independent native bilinear threshold.5/all; no head gating'),
        factor=dict(reference=1,candidate=5,target='Annotated foreground pixels only; explicit source labels stay consistent',
            background_BCE_unchanged=True,normal_image_loss_unchanged=True,Dice_unchanged=True,no_duplicate_images=True),
        acceptance='Original LOOP_PROTOCOL unchanged; TP79/TN342 and native overlap/localization/useful coverage, then separate CAL/robustness/freeze',
        input_hashes=guards,calibration_fit=False,test_images_read=0,promotion=False,
        limitations=['One seed; no patient/study IDs, clinical subtype adjudication or external validation',
            'Foreground weighting may increase false alarms through shared updates; reject an unbalanced gain',
            'No claim that output-gradient imbalance proves the primary clinical cause or will yield90%'])
    destination.open('x',encoding='utf-8').write(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps(dict(protocol=str(destination.relative_to(ROOT)),sha256=sha(destination),guard_count=len(guards),
        initializer_model_digest=model_digest,initializer_optimizer_digest=optimizer_digest,reference=reference,candidate=candidate)))


if __name__=='__main__': main()
