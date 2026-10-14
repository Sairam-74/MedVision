"""Freeze one positive-case Dice factor after completed E9/E10 analysis.

Read saved evidence and hashes only; never optimize or open reserved images.
"""
import datetime
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.evaluate_ai_baseline import sha
from tools.ai_bounded_hard_weights import class_normalized_weights


def load(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))


def main():
    session = 'experiments/session_20261007_ai_loop_01'
    destination = ROOT/session/'POSITIVE_DICE_EXPERIMENT_PROTOCOL.json'
    if destination.exists():
        raise ValueError('Exclusive registration required; never overwrite a protocol')
    previous_queue = load(session+'/hard_queue.json')
    if previous_queue['status'] != 'completed_training_and_native_audits_only':
        raise ValueError('Previous pair must finish all training and audits first')
    guards = dict(previous_queue['guards'])
    for path, digest in guards.items():
        if sha(ROOT/path) != digest:
            raise ValueError('Previous frozen guard changed: '+path)
    reviews = [('E10_all_normal_alert_sheets',199), ('E10_all_positive_sheets',55)]
    for name, count in reviews:
        directory = ROOT/session/name
        completed = json.loads((directory/'completion.json').read_text())
        if (not completed['status'].startswith('completed_actual_native_') or
                completed['total_selected_cases'] != count or
                completed['actual_new_case_reviews'] != count):
            raise ValueError('Complete actual E10 native review required: '+name)
        for file, field in [('per_case_visual_review.json','per_case_review_sha256'),
                            ('index.json','index_sha256'),('actual_sheet_notes.json','notes_sha256')]:
            if sha(directory/file) != completed[field]:
                raise ValueError('Actual review identity mismatch: '+name+'/'+file)
            guards[(Path(session)/name/file).as_posix()] = sha(directory/file)
        guards[(Path(session)/name/'completion.json').as_posix()] = sha(directory/'completion.json')
    pair = load('experiments/AI_E9_E10_HARD_PAIR/comparison.json')
    if pair['validation_numerical_gate_pass'] or pair['promotion'] or pair['test_images_read']:
        raise ValueError('This registration is only for the rejected, unpromoted development pair')
    initial_run = 'experiments/AI_E10_v3_hard_weight2'
    bundle, config, state = [load(initial_run+'/'+f) for f in ('bundle.json','config.json','state.json')]
    if (state['status']!='completed' or state['epochs_finished']!=12 or bundle['epoch']!=12 or
            bundle['global_epoch']!=30 or bundle['presence_weight']!=0 or config['hard_factor']!=2):
        raise ValueError('Completed selected E10 full epoch12/global30 initializer required')
    if sha(ROOT/initial_run/'best_model.pt') != bundle['checkpoint_sha256']:
        raise ValueError('Selected E10 model changed')
    snapshot = initial_run+'/epoch_012_resume.pt'
    manifest, catalog = config['manifest'], config['hard_catalog']
    rows = [r for r in load(manifest)['rows'] if r['split']=='train']
    hp, hn = [load(catalog+'/'+f)['image_ids'] for f in ('HARD_POSITIVE_SET.json','HARD_NEGATIVE_SET.json')]
    weights = class_normalized_weights(rows,hp,hn,2)
    if len(rows)!=2808 or len(hp)!=109 or len(hn)!=713:
        raise ValueError('Frozen TRAIN membership/catalog changed')
    reference, candidate = 'AI_E11_v3_positive_Dice_reference', 'AI_E12_v3_positive_Dice2'
    audit_ids = ['AI_AUDIT_E11_v3_positive_Dice_reference','AI_AUDIT_E12_v3_positive_Dice2']
    fit_ids = ['AI_LEARNING_FIT_E11_v3_positive_Dice_reference','AI_LEARNING_FIT_E12_v3_positive_Dice2']
    pair_id, smoke_output = 'AI_E11_E12_POSITIVE_DICE_PAIR', 'experiments/AI_POSITIVE_DICE_SMOKE_20261008'
    for name in [reference,candidate,*audit_ids,*fit_ids,pair_id,Path(smoke_output).name]:
        if (ROOT/'experiments'/name).exists():
            raise ValueError('Exclusive experiment output already exists: '+name)
    paths = [session+'/hard_queue.json',session+'/HARD_EXPERIMENT_PROTOCOL.json',
        'tools/register_ai_positive_dice_pair.py','tools/train_ai_positive_dice_candidate.py',
        'tools/queue_ai_positive_dice_pair.py','tools/analyze_ai_positive_dice_pair.py',
        'tools/ai_positive_dice_loss.py','tools/smoke_ai_positive_dice.py',
        session+'/E10_COMPLETED_FAILURE_ANALYSIS.md',session+'/E10_NORMAL_FULL_PANEL_FOLLOWUP.md',
        session+'/E10_NEXT_FACTOR_REVIEW_20261008.md',session+'/POSITIVE_DICE_FACTOR_REVIEW_20261008.md',
        session+'/E10_CURVES_STRATA_ANALYSIS_20261008.md',session+'/E10_CURVES_STRATA_ANALYSIS_20261008_DATA.json',
        'tools/compare_ai_hard_fit_pair.py','experiments/AI_HARD_FIT_PAIR_E9_E10_20261008/analysis.json',
        'experiments/AI_HARD_FIT_PAIR_E9_E10_20261008/per_case_changes.jsonl',
        'experiments/AI_HARD_FIT_PAIR_E9_E10_20261008/TRAIN_HARD_FIT_PAIR.md',
        'experiments/AI_E9_E10_HARD_PAIR/comparison.json','experiments/AI_E9_E10_HARD_PAIR/completion.json',snapshot]
    for run,audit,fit in [('AI_E9_v3_hard_reference','AI_AUDIT_E9_v3_hard_reference','AI_LEARNING_FIT_E9_v3_hard_reference'),
                          ('AI_E10_v3_hard_weight2','AI_AUDIT_E10_v3_hard_weight2','AI_LEARNING_FIT_E10_v3_hard_weight2')]:
        paths += ['experiments/'+run+'/'+f for f in ('config.json','bundle.json','best_model.pt','state.json','epochs.jsonl')]
        paths += ['experiments/'+audit+'/'+f for f in ('metrics.json','per_case.json','completion.json')]
        paths += ['experiments/'+fit+'/'+f for f in ('config.json','train_cases.jsonl','completion.json')]
    for path in paths:
        guards[path] = sha(ROOT/path)
    result = dict(status='registered_after_completed_native_failure_analysis',
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        major_factor='positive_case_dice_coefficient', reference=reference,candidate=candidate,
        initial_run=initial_run,hard_catalog=catalog,smoke_output=smoke_output,
        audit_ids=audit_ids,fit_ids=fit_ids,pair_id=pair_id,
        initialization=dict(selected_epoch=12,global_epoch=30,snapshot=snapshot,snapshot_sha256=sha(ROOT/snapshot),
            optimizer='Independently restore identical selected full E10 model and Adam, including moments and step counters'),
        evidence=['E10 TP67/TN181, Dice0.379528/IoU0.283667 fails frozen acceptance and original useful coverage',
            'All199 normal alerts and55 positive segmentation failures actually reviewed; causes/subtypes unadjudicated',
            'TRAIN hard-positive Dice0.058133 and86/109 zero-overlap cases; poor foreground fitting persists',
            'Learning curves still improve, so identical continuation control is necessary to isolate coefficient effect'],
        common_config=dict(additional_epochs=12,batch_size=2,lr=.0001,seed=42,global_epochs=list(range(31,43)),
            hard_factor=2,presence_weight=0,normal_bce_weight=1,
            segmentation_loss='Per-source hard_weight * (valid-mean BCE + positive_case_coefficient * valid Dice); normal Dice coefficient1',
            preprocessing='Unchanged CLAHE2/tile8/blur3/unit, stretch256',
            sampling='Natural unique2808 one-pass shuffle; identical epoch seeds/augmentation; unchanged hard-factor2 source weights',
            selection='Unchanged feasible-first/minimum normalized TP79,TN342,Dice0.5237965563,IoU0.3775685933; earlier ties',
            masks='Independent native bilinear threshold0.5/all; no head gating'),
        factor=dict(reference=1,candidate=2,positive_label_source='Frozen manifest fracture label, consistent with nonempty target',
            hard_positive_count=len(hp),hard_negative_count=len(hn),minimum_hard_weight=min(weights.values()),maximum_hard_weight=max(weights.values()),
            all_image_BCE_unchanged=True,normal_Dice_unchanged=True,no_duplicate_images=True),
        acceptance='Frozen LOOP_PROTOCOL unchanged: TP79/TN342 and meaningful native Dice/IoU/localization with fewer FP pixels and retained useful coverage; then separate calibration/robustness/final freeze',
        input_hashes=guards,calibration_fit=False,test_images_read=0,promotion=False,
        limitations=['One seed, no external validation','No reliable patient/study IDs or expert clinical subtype adjudication',
            'Coefficient2 may expand masks or increase normal alerts; training/smoke success is not an improvement claim'])
    with destination.open('x',encoding='utf-8') as handle:
        json.dump(result,handle,indent=2,allow_nan=False)
    print(json.dumps(dict(protocol=str(destination.relative_to(ROOT)),sha256=sha(destination),
        initial_snapshot_sha256=sha(ROOT/snapshot),guard_count=len(guards),reference=reference,candidate=candidate),indent=2))


if __name__=='__main__': main()
