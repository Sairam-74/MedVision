"""Bounded metadata-only observation of the exact registered background queue."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import time

import psutil

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / 'experiments/session_20261007_ai_loop_01'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def processes(launch):
    try:
        outer = psutil.Process(launch['pid'])
        if (abs(outer.create_time() - launch['creation_time']) > .001
                or outer.cmdline() != launch['command'] or Path(outer.cwd()).resolve() != ROOT):
            raise ValueError('Recorded queue PID was reused or command changed')
        result = []
        for process in [outer, *outer.children(recursive=True)]:
            try:
                command = process.cmdline()
                result.append(dict(pid=process.pid, created=process.create_time(), parent=process.ppid(),
                                   script=Path(command[1]).name if len(command) > 1 else None,
                                   cpu_seconds=process.cpu_times().user + process.cpu_times().system))
            except psutil.NoSuchProcess:
                continue
        return result
    except psutil.NoSuchProcess:
        return []


def compact_observation(observation):
    """Project existing metadata for stdout; leave the saved observation intact."""
    roles = {
        'queue_ai_foreground_bce_pair.py': 'queue',
        'train_ai_foreground_bce_candidate.py': 'trainer',
        'audit_ai_presence_candidate.py': 'native_audit',
        'audit_ai_presence_train_fit.py': 'TRAIN_fit_audit',
        'ai_error_groups.py': 'metadata_audit',
        'analyze_ai_foreground_bce_pair.py': 'paired_analysis',
    }
    before = {(p['pid'], p['created']): p for p in observation['processes_before']}
    after = observation['processes_after']
    active = []
    for process in after:
        script = process['script']
        if script not in roles:
            continue  # Console hosts are retained only in the full saved record.
        if any(child['parent'] == process['pid'] and child['script'] == script for child in after):
            continue  # Observed same-script Python launcher; retain its actual child.
        prior = before.get((process['pid'], process['created']))
        active.append(dict(role=roles[script], script=script, pid=process['pid'],
                           creation_time=process['created'], parent=process['parent'],
                           cpu_seconds=process['cpu_seconds'],
                           cpu_delta_seconds=process['cpu_seconds'] - prior['cpu_seconds'] if prior else None))
    runs = {}
    for name, item in observation['runs'].items():
        result = {k: item[k] for k in ('status', 'state', 'complete_epochs', 'partial_record_observed') if k in item}
        if 'latest_epoch' in item:
            result.update(latest_epoch=item['latest_epoch'], latest_global_epoch=item['global_epoch'],
                          TP=item['confusion_matrix']['tp'], TN=item['confusion_matrix']['tn'],
                          FP=item['confusion_matrix']['fp'], FN=item['confusion_matrix']['fn'],
                          Dice=item['dice'], IoU=item['iou'], replay_parity=item['reference_replay_parity'])
        runs[name] = result
    return dict(utc=observation['utc'], observer_source_sha256=observation['observer_source_sha256'],
                wait_seconds=observation['wait_seconds'], queue=observation['queue'],
                processes=active, runs=runs,
                stderr={name: item for name, item in observation['stderr'].items() if item['bytes']})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wait-seconds', type=float, default=0)
    parser.add_argument('--compact', action='store_true', help='Print a compact view; always save the full observation')
    args = parser.parse_args()
    if not 0 <= args.wait_seconds <= 55:
        raise ValueError('Bounded wait 0-55 seconds required')
    protocol_path = SESSION / 'FOREGROUND_BCE_EXPERIMENT_PROTOCOL.json'
    if hashlib.sha256(protocol_path.read_bytes()).hexdigest() != '250bcd50e0ba8463d6da746e469222b41a82b8114ec1add1aece6fd04850e523':
        raise ValueError('Registered protocol identity changed')
    protocol = read(protocol_path)
    launch = read(SESSION / 'foreground_bce_queue_launch.json')
    before = processes(launch)
    started = time.monotonic()
    time.sleep(args.wait_seconds)
    after = processes(launch)
    queue = read(SESSION / 'foreground_bce_queue.json')
    runs = {}
    for name in (protocol['reference'], protocol['candidate']):
        run = ROOT / 'experiments' / name
        if not (run / 'state.json').exists():
            runs[name] = dict(status='not_started')
            continue
        state = read(run / 'state.json')
        path = run / 'epochs.jsonl'
        data = path.read_text() if path.exists() else ''
        lines = data.splitlines()
        partial = bool(data and not data.endswith('\n'))
        if partial:
            lines = lines[:-1]
        records = [json.loads(line) for line in lines if line.strip()]
        latest = records[-1] if records else None
        item = dict(state={k:state.get(k) for k in ('status','epoch','global_epoch','batch','batches')},
                    complete_epochs=len(records), partial_record_observed=partial)
        if latest:
            validation = latest['validation']
            item.update(latest_epoch=latest['epoch'], global_epoch=latest['global_epoch'],
                        unique_TRAIN_seen=latest['unique_train_images_seen'],
                        confusion_matrix=validation['classification']['confusion_matrix'],
                        accuracy=validation['classification']['accuracy'],
                        sensitivity=validation['classification']['recall_sensitivity'],
                        specificity=validation['classification']['specificity'],
                        auroc=validation['classification']['auroc'],
                        dice=validation['delivered']['mean_positive_dice'],
                        iou=validation['delivered']['mean_positive_iou'],
                        reference_replay_parity=latest['reference_replay_parity'])
        runs[name] = item
    stderr = {}
    for name in ('foreground_bce_queue', protocol['reference'], protocol['candidate']):
        path = SESSION / (name + '.stderr.log')
        if path.exists():
            stderr[name] = dict(bytes=path.stat().st_size, tail=path.read_text(errors='replace')[-1500:])
    observation = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                       observer_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                       wait_seconds=time.monotonic()-started, processes_before=before, processes_after=after,
                       queue={k:queue.get(k) for k in ('status','current','foreground_bce_coefficient','error')},
                       runs=runs, stderr=stderr, test_images_read=0, promotion=False)
    with (SESSION / 'foreground_bce_observations.jsonl').open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(observation, allow_nan=False) + '\n')
    print(json.dumps(compact_observation(observation) if args.compact else observation, allow_nan=False), flush=True)


if __name__ == '__main__':
    main()
