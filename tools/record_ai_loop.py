"""Resume-safe AI progress registry. Reads run evidence; never trains or promotes."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BEGIN = b'<!-- AI_LOOP_STATUS_BEGIN -->'
END = b'<!-- AI_LOOP_STATUS_END -->'


def json_read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', default='experiments/session_20261007_ai_loop_01')
    parser.add_argument('--observation', required=True)
    args = parser.parse_args()
    session = (ROOT/args.session).resolve()
    if ROOT not in session.parents or not session.is_dir():
        raise ValueError('Existing workspace session required')
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    runs = {}
    for run in sorted((ROOT/'experiments').glob('AI_E*')):
        if not run.is_dir() or not (run/'state.json').exists():
            continue
        state = json_read(run/'state.json')
        config = json_read(run/'config.json')
        records = [json.loads(line) for line in (run/'epochs.jsonl').read_text().splitlines() if line.strip()] if (run/'epochs.jsonl').exists() else []
        latest = records[-1] if records else None
        best = json_read(run/'best_validation.json') if (run/'best_validation.json').exists() else None
        runs[run.name] = dict(state=state, config_sha256=hashlib.sha256((run/'config.json').read_bytes()).hexdigest(),
                             dataset_version=config['manifest'], model_version=run.name,
                             loss=config.get('loss'), normal_bce_weight=config.get('normal_bce_weight'),
                             presence_weight=config.get('presence_weight'), output_contract=config.get('output_contract'),
                             hard_factor=config.get('hard_factor'), hard_catalog=config.get('hard_catalog'),
                             positive_dice_coefficient=config.get('positive_dice_coefficient'),
                             foreground_bce_coefficient=config.get('foreground_bce_coefficient'),
                             input_size=config.get('input_size',config.get('preprocess',{}).get('size')),
                             initial_checkpoint=config.get('initial_checkpoint'), sampling=config.get('sampling'),
                             completed_epochs=len(records), latest_complete_epoch=latest,
                             selected_checkpoint=best)
    audits = {}
    for run in sorted((ROOT/'experiments').glob('AI_AUDIT_*')):
        if (run/'completion.json').exists() and (run/'metrics.json').exists():
            audits[run.name] = json_read(run/'metrics.json')
    pair_path = ROOT/'experiments/AI_E5_E6_PAIR_ANALYSIS/comparison.json'
    pair_decision = json_read(pair_path)['decision'] if pair_path.exists() else 'Pending full paired analysis'
    presence_pair_path = ROOT/'experiments/AI_E7_E8_PRESENCE_PAIR_r3/comparison.json'
    if not presence_pair_path.exists(): presence_pair_path = ROOT/'experiments/AI_E7_E8_PRESENCE_PAIR_r2/comparison.json'
    presence_pair_decision = json_read(presence_pair_path)['decision'] if presence_pair_path.exists() else 'Pending full matched presence analysis'
    presence_path = session/'presence_queue_r2.json' if (session/'presence_queue_r2.json').exists() else session/'presence_queue.json'
    presence_queue = json_read(presence_path) if presence_path.exists() else None
    hard_protocol_path = session/'HARD_EXPERIMENT_PROTOCOL.json'
    hard_protocol = json_read(hard_protocol_path) if hard_protocol_path.exists() else None
    hard_queue_path = session/'hard_queue.json'
    hard_queue = json_read(hard_queue_path) if hard_queue_path.exists() else None
    hard_pair_path = ROOT/'experiments'/hard_protocol['pair_id']/'comparison.json' if hard_protocol else None
    hard_pair_decision = json_read(hard_pair_path)['decision'] if hard_pair_path and hard_pair_path.exists() else 'Pending full matched hard-example analysis'
    dice_protocol_path = session/'POSITIVE_DICE_EXPERIMENT_PROTOCOL.json'
    dice_protocol = json_read(dice_protocol_path) if dice_protocol_path.exists() else None
    dice_queue_path = session/'positive_dice_queue.json'
    dice_queue = json_read(dice_queue_path) if dice_queue_path.exists() else None
    dice_pair_path = ROOT/'experiments'/dice_protocol['pair_id']/'comparison.json' if dice_protocol else None
    dice_pair_decision = json_read(dice_pair_path)['decision'] if dice_pair_path and dice_pair_path.exists() else 'Pending full matched positive-Dice analysis'
    foreground_bce_protocol_path = session/'FOREGROUND_BCE_EXPERIMENT_PROTOCOL.json'
    foreground_bce_protocol = json_read(foreground_bce_protocol_path) if foreground_bce_protocol_path.exists() else None
    foreground_bce_queue_path = session/'foreground_bce_queue.json'
    foreground_bce_queue = json_read(foreground_bce_queue_path) if foreground_bce_queue_path.exists() else None
    foreground_bce_pair_path = ROOT/'experiments'/foreground_bce_protocol['pair_id']/'comparison.json' if foreground_bce_protocol else None
    foreground_bce_pair_decision = json_read(foreground_bce_pair_path)['decision'] if foreground_bce_pair_path and foreground_bce_pair_path.exists() else 'Pending full matched foreground-BCE analysis'
    resolution_protocol_path = session/'RESOLUTION_EXPERIMENT_PROTOCOL.json'
    resolution_protocol = json_read(resolution_protocol_path) if resolution_protocol_path.exists() else None
    resolution_queue_path = session/'resolution_queue.json'
    resolution_queue = json_read(resolution_queue_path) if resolution_queue_path.exists() else None
    resolution_pair_path = ROOT/'experiments'/resolution_protocol['pair_id']/'comparison.json' if resolution_protocol else None
    resolution_pair_decision = json_read(resolution_pair_path)['decision'] if resolution_pair_path and resolution_pair_path.exists() else 'Pending full matched resolution analysis'
    event = dict(utc=now, observation=args.observation, runs=runs, audits=audits,
                 normal_BCE_pair_decision=pair_decision, presence_queue=presence_queue, presence_pair_decision=presence_pair_decision,
                 hard_protocol_sha256=hashlib.sha256(hard_protocol_path.read_bytes()).hexdigest() if hard_protocol else None,
                 hard_queue=hard_queue, hard_pair_decision=hard_pair_decision,
                 positive_dice_protocol_sha256=hashlib.sha256(dice_protocol_path.read_bytes()).hexdigest() if dice_protocol else None,
                 positive_dice_queue=dice_queue, positive_dice_pair_decision=dice_pair_decision,
                 foreground_bce_protocol_sha256=hashlib.sha256(foreground_bce_protocol_path.read_bytes()).hexdigest() if foreground_bce_protocol else None,
                 foreground_bce_queue=foreground_bce_queue, foreground_bce_pair_decision=foreground_bce_pair_decision,
                 resolution_protocol_sha256=hashlib.sha256(resolution_protocol_path.read_bytes()).hexdigest() if resolution_protocol else None,
                 resolution_queue=resolution_queue,resolution_pair_decision=resolution_pair_decision,
                 acceptance_counts=dict(tp_min=79, tn_min=342, validation_n=463),
                 segmentation_localization_required=True, promotion=False, test_evaluated=False)
    with (session/'loop_events.jsonl').open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(event, allow_nan=False)+'\n')
    (session/'LATEST_PROGRESS.json').write_text(json.dumps(event, indent=2, allow_nan=False), encoding='utf-8')
    lines = [BEGIN.decode(), '## ACTIVE AI IMPROVEMENT LOOP - resumed 7 October 2026', '',
             f'Observed UTC: {now}. {args.observation}', '',
             'Frozen validation:463 images (83 fractures/380 normals). Required practical case counts:TP>=79 andTN>=342, plus meaningful native segmentation/localization improvement. At79/83, sensitivity rounds to95.2%. No accuracy-only success or production promotion.', '',
             '| Run | State | Selected validation epoch | Accuracy | Sensitivity | Specificity | FP / FN | Positive Dice / IoU |',
             '|---|---|---:|---:|---:|---:|---|---|']
    for name, info in runs.items():
        state, best = info['state'], info['selected_checkpoint']
        desc = state['status'] + (f" epoch{state.get('epoch')} batch{state.get('batch')}/{state.get('batches')}" if state['status'] == 'training' else '')
        if best:
            m = best['metrics']; c=m['classification']; s=m['delivered']; cm=c['confusion_matrix']
            lines.append(f"| {name} | {desc} | {best['epoch']} | {c['accuracy']:.2%} | {c['recall_sensitivity']:.2%} | {c['specificity']:.2%} | {cm['fp']} / {cm['fn']} | {s['mean_positive_dice']:.6f} / {s['mean_positive_iou']:.6f} |")
        else:
            lines.append(f'| {name} | {desc} | Pending | Pending | Pending | Pending | Pending | Pending |')
    if 'AI_E6_v3_normal_BCE2' not in runs:
        lines.append('| AI_E6_v3_normal_BCE2 | Queued after E5 | Pending | Pending | Pending | Pending | Pending | Pending |')
    lines += ['', 'These are recorded checkpoint/default-threshold observations, not final accepted models. Full audits and error panels are retained separately; current live run files supersede this snapshot.', '',
              f'Active evidence/protocol: {args.session}/LOOP_PROTOCOL.json, LATEST_PROGRESS.json and loop_events.jsonl. Existing unchanged baseline is BASELINE_MODEL_REPORT.md; all older history below is retained.', '',
              f'E5/E6 decision: {pair_decision}. Native CPU E6 audit FP215 differs from trainer GPU FP214 by one single-pixel normal alert (IMG0003056); both observations retained.', '',
              'E7/E8 registered presence branch comparison: both start from known TRAIN-only E5 epoch8 weights, reset Adam equally, receive12 additional matched epochs, and retain independent unfiltered masks. The primary classification table for E8 uses conservative head+ OR mask+ review alerts. Head-only performance cannot hide mask false alarms or missed localization. Technical recovery r2 protocol: PRESENCE_EXPERIMENT_PROTOCOL_r2.json; smoke: AI_PRESENCE_MODEL_SMOKE_20261007_r2. Original failed run retained; no validated epoch lost. No performance gain claimed from smoke checks.', '',
              'Do not edit frozen model/trainer/cache/protocol sources during the active pair. Do not restart old E3/E4 or automatic test/paper watchers. Reserved test597 remains closed; calibrate only after selection/gate passes on separate149 cases. Original checkpoint/threshold/data are preserved; website untouched.', '', END.decode()]
    if hard_protocol:
        lines[-1:-1] = [
            'E9/E10 bounded hard-example comparison registered after actual E8 native failure review: same selected E7 global18 full model/Adam restored independently,12 further matched epochs/global19-30,109 persistent hard fractures and713 persistent hard normals from TRAIN only. Factor1 versus2 within-class mean-normalized loss weights is the only intervention. All2808 source images appear once per epoch; no duplicated samples. HARD_EXPERIMENT_PROTOCOL.json and hard_queue.json contain frozen inputs/live progress.', '',
            f'Hard-example paired decision: {hard_pair_decision}. A smoke pass proves execution/parity only; it is not evidence of improved performance.', '']
    if dice_protocol:
        lines[-1:-1] = [
            'E11/E12 positive-case Dice coefficient1 versus2: independently restore E10 selected epoch12/global30 full model and Adam, continue12 matched epochs/global31-42. Hard factor2, all-image BCE, normal Dice, architecture, resolution, preprocessing, sampling and selection are unchanged. POSITIVE_DICE_EXPERIMENT_PROTOCOL.json and positive_dice_queue.json freeze inputs and track progress. Actual E10 review covered199 normal alerts and55 positive segmentation failures; hard TRAIN fractures remain poorly fitted.', '',
            f'Positive-Dice paired decision: {dice_pair_decision}. No new calibration/test access or production promotion.', '']
    if foreground_bce_protocol:
        lines[-1:-1] = [
            'E13/E14 foreground-pixel BCE coefficient 1 versus 5: independently restore the same selected E11 epoch 9 / global 39 full model and Adam, then continue 12 matched epochs / globals 40-51. Hard factor 2, presence weight 0, normal BCE weight 1 and positive-case Dice coefficient 1 remain fixed. Only annotated foreground-pixel BCE changes; background BCE, normal-image loss, Dice, architecture, resolution, preprocessing, sampling and selection remain unchanged. FOREGROUND_BCE_EXPERIMENT_PROTOCOL.json and foreground_bce_queue.json freeze inputs and track progress. The first three reference epochs must match the saved E11 globals 40-42 under the registered parity checks.', '',
            f'Foreground-BCE paired decision: {foreground_bce_pair_decision}. Passed smoke and reference replay establish execution/parity only; performance requires the full paired native audits and actual failure review. No calibration/test access or production promotion.', '']
    if resolution_protocol:
        lines[-1:-1] = [
            'E15/E16 resolution comparison: independently restore the same E14 selected epoch11/global50 full model and Adam; continue12 matched epochs/globals51-62 at native-derived256 versus512. Architecture, foregroundBCE5, positiveDice1, hard2, normalBCE1, presence0, FP32, batch2, optimizer, global shuffle/augmentation and selection remain fixed. The256 control must exactly replay saved E14 global51. RESOLUTION_EXPERIMENT_PROTOCOL.json and resolution_queue.json preserve the registered evidence and progress.', '',
            f'Resolution paired decision: {resolution_pair_decision}. GPU smoke establishes execution,256 parity and512 feasibility only. Actual native failure review and all original coverage gates remain required; no CAL/test or production promotion.', '']
    section = '\n'.join(lines).encode('utf-8')
    backup = session/'before'
    backup.mkdir(exist_ok=True)
    for name in ('PROJECT_STATUS.md', 'EXPERIMENT_REGISTRY.md'):
        path = ROOT/name
        original = path.read_bytes()
        if not (backup/name).exists():
            with (backup/name).open('xb') as handle:
                handle.write(original)
        newline = b'\r\n' if b'\r\n' in original[:200] else b'\n'
        block = section.replace(b'\n', newline)
        if BEGIN in original:
            first = original.index(BEGIN)
            last = original.index(END, first)+len(END)
            updated = original[:first]+block+original[last:]
        else:
            match = re.match(br'(#.*?\r?\n)(?:\r?\n)', original)
            if not match:
                raise ValueError('Unexpected document title')
            updated = original[:match.end()]+block+newline*2+original[match.end():]
        path.write_bytes(updated)
    print(json.dumps(dict(utc=now, run_states={key:value['state']['status'] for key,value in runs.items()}, observation=args.observation), indent=2))


if __name__ == '__main__':
    main()
