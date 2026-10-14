"""Freeze a single resolution factor only after actual failures and GPU smoke."""
import datetime
import json
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.evaluate_ai_baseline import sha
from tools.ai_presence_model import tensor_digest
from tools.smoke_ai_hard_candidate import optimizer_state_digest

SESSION = 'experiments/session_20261007_ai_loop_01'


def load(name):
    return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))


def main():
    destination = ROOT/SESSION/'RESOLUTION_EXPERIMENT_PROTOCOL.json'
    if destination.exists():
        raise ValueError('Exclusive NEW registration required')
    previous = load(SESSION+'/foreground_bce_queue.json')
    if previous['status'] != 'completed_training_and_native_audits_only':
        raise ValueError('Prior full pair must be terminal')
    guards = dict(previous['guards'])
    for name,digest in guards.items():
        if sha(ROOT/name) != digest:
            raise ValueError('Prior guard changed: '+name)
    pair = 'experiments/AI_E13_E14_FOREGROUND_BCE_PAIR'
    completed,comparison = load(pair+'/completion.json'),load(pair+'/comparison.json')
    if (completed['status'] != 'completed' or sha(ROOT/pair/'comparison.json') != completed['comparison_sha256'] or
            comparison['promotion'] or comparison['test_images_read'] or comparison['validation_numerical_gate_pass']):
        raise ValueError('Completed unpromoted prior pair with unmet gates required')
    paths = [SESSION+'/foreground_bce_queue.json',pair+'/completion.json',pair+'/comparison.json']
    for name,count in [('E13_all_normal_alert_sheets',176),('E14_all_normal_alert_sheets',143),
                       ('E13_all_positive_sheets',51),('E14_all_positive_sheets',52)]:
        directory = ROOT/SESSION/name
        done = load(SESSION+'/'+name+'/completion.json')
        if (not done['status'].startswith('completed_actual_native_') or done['total_selected_cases'] != count or
                done['actual_new_case_reviews'] != count):
            raise ValueError('Actual exhaustive native case review required: '+name)
        for file,field in [('per_case_visual_review.json','per_case_review_sha256'),
                           ('actual_sheet_notes.json','notes_sha256'),('index.json','index_sha256')]:
            if sha(directory/file) != done[field]:
                raise ValueError('Actual review changed: '+name+'/'+file)
        paths += [str(path.relative_to(ROOT)).replace('\\','/') for path in directory.glob('*.json')]
    diagnostic = 'experiments/AI_BATCHNORM_CONTEXT_E13_E14_20261009'
    dc = load(diagnostic+'/completion.json')
    if (dc['status'] != 'completed_TRAIN_only_frozen_BN_context_diagnosis' or
            not dc['model_tensors_and_buffers_unchanged'] or not dc['BN_flags_restored'] or not dc['no_optimizer_steps'] or
            any(dc[k] for k in ('validation_images_read','calibration_images_read','test_images_read'))):
        raise ValueError('Completed frozen TRAIN diagnosis required')
    for file,field in [('config.json','config_sha256'),('summary.json','summary_sha256'),('per_case.json','per_case_sha256')]:
        if sha(ROOT/diagnostic/file) != dc[field]:
            raise ValueError('Frozen diagnostic changed')
        paths.append(diagnostic+'/'+file)
    paths.append(diagnostic+'/completion.json')
    initial_run = 'experiments/AI_E14_v3_foreground_BCE5'
    config,bundle,state = [load(initial_run+'/'+file) for file in ('config.json','bundle.json','state.json')]
    if (state['status'] != 'completed' or state['epochs_finished'] != 12 or bundle['epoch'] != 11 or bundle['global_epoch'] != 50 or
            config['foreground_bce_coefficient'] != 5 or config['positive_dice_coefficient'] != 1 or config['hard_factor'] != 2 or
            config['presence_weight'] != 0 or config['normal_bce_weight'] != 1 or config['batch_size'] != 2 or
            config['preprocess']['size'] != 256 or config['lr'] != .0001):
        raise ValueError('Exact selected E14 initializer/configuration required')
    snapshot = initial_run+'/epoch_011_resume.pt'
    full = torch.load(ROOT/snapshot,map_location='cpu',weights_only=True)
    if full['epoch'] != 11 or full['global_epoch'] != 50 or full['foreground_bce_coefficient'] != 5 or full['hard_factor'] != 2:
        raise ValueError('Selected full snapshot metadata mismatch')
    model_digest = tensor_digest(full['model_state_dict'])
    optimizer_digest = optimizer_state_digest(full['optimizer_state_dict'])
    if (sha(ROOT/initial_run/'best_model.pt') != bundle['checkpoint_sha256'] or
            model_digest != tensor_digest(torch.load(ROOT/initial_run/'best_model.pt',map_location='cpu',weights_only=True))):
        raise ValueError('Selected full snapshot and best weights differ')
    del full
    replay_snapshot = initial_run+'/epoch_012_resume.pt'
    full = torch.load(ROOT/replay_snapshot,map_location='cpu',weights_only=True)
    records = [json.loads(line) for line in (ROOT/initial_run/'epochs.jsonl').read_text().splitlines() if line.strip()]
    if full['epoch'] != 12 or full['global_epoch'] != 51 or records[-1]['global_epoch'] != 51 or len(records) != 12:
        raise ValueError('Saved full reference replay required')
    replay = {'51':dict(model_parameter_sha256=tensor_digest(full['model_state_dict']),
        optimizer_state_sha256=optimizer_state_digest(full['optimizer_state_dict']),validation=records[-1]['validation'],
        original_full_snapshot=replay_snapshot,original_full_snapshot_sha256=sha(ROOT/replay_snapshot))}
    del full
    caches = {}
    for size,name in [(256,'AI_TRAIN_CACHE_v3_256_r2'),(512,'AI_TRAIN_CACHE_v3_512_r1')]:
        path = 'experiments/'+name
        cache = load(path+'/completion.json')
        if (cache['status'] != 'completed_exact_train_cache' or cache['train_images'] != 2808 or cache['train_positive_images'] != 493 or
                cache['preprocess'] != {**config['preprocess'],'size':size} or cache['manifest_sha256'] != config['manifest_sha256']):
            raise ValueError('Exact native-derived TRAIN cache required')
        if size == 512 and (cache['builder'] != 'tools/cache_ai_resolution_inputs.py' or cache['independent_redecode_cases'] != 16):
            raise ValueError('Independently verified native512 producer required')
        for file,digest in cache['source_hashes'].items():
            if sha(ROOT/file) != digest:
                raise ValueError('Cache dependency changed')
        for file,digest in cache['cache_hashes'].items():
            if sha(ROOT/path/(file+'.npy')) != digest:
                raise ValueError('Cached tensor changed')
            guards[path+'/'+file+'.npy'] = digest
        if sha(ROOT/path/'rows.json') != cache['rows_sha256']:
            raise ValueError('Cached TRAIN order changed')
        caches[str(size)] = dict(path=path,completion_sha256=sha(ROOT/path/'completion.json'))
        paths += [path+'/completion.json',path+'/rows.json']
        if size == 512:
            for file,key in [('verification.json','verification_sha256'),('target_representation.json','target_representation_sha256')]:
                if sha(ROOT/path/file) != cache[key]:
                    raise ValueError('512 independent verification changed')
                paths.append(path+'/'+file)
    smoke_output = 'experiments/AI_RESOLUTION_SMOKE_20261009'
    smoke,smoke_config = load(smoke_output+'/completion.json'),load(smoke_output+'/config.json')
    if smoke['status'] != 'passed_TRAIN_only_resolution_smoke' or not all(smoke.get(k) is True for k in (
            'full_matched_initialization','cached256_vs_native256_exact','input512_batch2_fp32_feasible')):
        raise ValueError('Actual CUDA parity/feasibility smoke required')
    if smoke_config['initial_snapshot_sha256'] != sha(ROOT/snapshot):
        raise ValueError('GPU smoke used a different initializer')
    for name,digest in smoke_config['source_hashes'].items():
        if sha(ROOT/name) != digest:
            raise ValueError('Smoke source changed')
    paths += [snapshot,replay_snapshot,smoke_output+'/config.json',smoke_output+'/completion.json']
    paths += ['tools/'+name for name in ('register_ai_resolution_pair.py','queue_ai_resolution_pair.py',
        'train_ai_resolution_candidate.py','analyze_ai_resolution_pair.py','smoke_ai_resolution_pair.py',
        'cache_ai_resolution_inputs.py','audit_ai_batchnorm_context_completed_pair.py')]
    paths += [SESSION+'/'+name for name in ('E13_NORMAL_FAILURE_ANALYSIS_20261009.md','E14_NORMAL_FAILURE_ANALYSIS_20261009.md',
        'E13_POSITIVE_FAILURE_ANALYSIS_20261009.md','E14_POSITIVE_FAILURE_ANALYSIS_20261009.md',
        'ROOT_E14_FULL_PANEL_FOLLOWUP_20261009.md','BN_CONTEXT_RESEARCH_20261009.md','BN_CONTEXT_DIAGNOSIS_20261009.md',
        'E13_E14_COMPLETED_FAILURE_AND_RESOLUTION_FACTOR_20261009.md')]
    curves = SESSION+'/E13_E14_curves_and_subgroups_20261009'
    paths += [str(path.relative_to(ROOT)).replace('\\','/') for path in (ROOT/curves).iterdir() if path.is_file()]
    fit_pair = 'experiments/AI_FOREGROUND_BCE_FIT_PAIR_E13_E14_20261009'
    paths += [str(path.relative_to(ROOT)).replace('\\','/') for path in (ROOT/fit_pair).iterdir() if path.is_file()]
    for run,audit,fit in [('AI_E13_v3_foreground_BCE_reference','AI_AUDIT_E13_v3_foreground_BCE_reference','AI_LEARNING_FIT_E13_v3_foreground_BCE_reference'),
                          ('AI_E14_v3_foreground_BCE5','AI_AUDIT_E14_v3_foreground_BCE5','AI_LEARNING_FIT_E14_v3_foreground_BCE5')]:
        paths += ['experiments/'+run+'/'+f for f in ('config.json','bundle.json','state.json','epochs.jsonl','best_model.pt')]
        paths += ['experiments/'+audit+'/'+f for f in ('metrics.json','per_case.json','completion.json')]
        paths += ['experiments/'+fit+'/'+f for f in ('config.json','metrics.json','train_cases.jsonl','completion.json')]
    reference,candidate = 'AI_E15_v3_resolution256_reference','AI_E16_v3_resolution512'
    audits = ['AI_AUDIT_E15_v3_resolution256_reference','AI_AUDIT_E16_v3_resolution512']
    fits = ['AI_LEARNING_FIT_E15_v3_resolution256_reference','AI_LEARNING_FIT_E16_v3_resolution512']
    pair_id = 'AI_E15_E16_RESOLUTION_PAIR'
    for name in (reference,candidate,*audits,*fits,pair_id):
        if (ROOT/'experiments'/name).exists():
            raise ValueError('Exclusive future run already exists: '+name)
    for name in paths:
        guards[name] = sha(ROOT/name)
    result = dict(status='registered_after_completed_native_failure_analysis',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        major_factor='input_resolution',reference=reference,candidate=candidate,initial_run=initial_run,
        hard_catalog=config['hard_catalog'],smoke_output=smoke_output,audit_ids=audits,fit_ids=fits,pair_id=pair_id,caches=caches,
        initialization=dict(selected_epoch=11,global_epoch=50,snapshot=snapshot,snapshot_sha256=sha(ROOT/snapshot),
                            model_parameter_sha256=model_digest,optimizer_state_sha256=optimizer_digest),reference_replay_parity=replay,
        common_config=dict(additional_epochs=12,batch_size=2,lr=.0001,seed=42,global_epochs=list(range(51,63)),hard_factor=2,
            presence_weight=0,normal_bce_weight=1,positive_dice_coefficient=1,foreground_bce_coefficient=5,
            precision='FP32; no AMP',preprocessing='Same CLAHE2/tile8/blur3/unit/stretch; onlynative-derived inputsize changes',
            sampling='Same2808 uniqueTRAIN sources once/epoch; sameglobalshuffle/augmentationalgorithm/hard109+713',
            masks='Independent native bilinear threshold.5/all; no classifier gating',selection='Unchanged feasible-first bottleneck rule'),
        factor=dict(reference=256,candidate=512,target='Native-derived input resolution, resulting spatial/annotation sampling and relative receptive field'),
        acceptance='TP>=79 andTN>=342 plusoriginal/matched segmentation, localization and useful coverage; CAL/robustness/freeze before TEST597 once',
        evidence='Actual complete E13/E14 failure/curve/TRAIN fit review; frozen BNcontext repair rejected; persistent small/narrow-target undercoverage',
        input_hashes=guards,calibration_fit=False,test_images_read=0,promotion=False,
        limitations=['Resolution causality remains a hypothesis; higher fidelity is not proof of learned model gain.',
                     'One seed; reused hardTRAIN strata; no patient/study/clinicalsubtype or externalvalidation.',
                     'GPU smoke proves execution/parity/feasibility only; no clinical improvement is claimed.'])
    destination.open('x',encoding='utf-8').write(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps(dict(protocol=str(destination.relative_to(ROOT)),sha256=sha(destination),guard_count=len(guards),
                         reference=reference,candidate=candidate,model_digest=model_digest,optimizer_digest=optimizer_digest)))


if __name__ == '__main__':
    main()
