"""Exclusive hidden launch of the registered foreground BCE pair; no resume."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import psutil

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / 'experiments/session_20261007_ai_loop_01'


def main():
    if sys.platform != 'win32':
        raise ValueError('Registered Windows runtime required')
    protocol = SESSION / 'FOREGROUND_BCE_EXPERIMENT_PROTOCOL.json'
    if hashlib.sha256(protocol.read_bytes()).hexdigest() != '250bcd50e0ba8463d6da746e469222b41a82b8114ec1add1aece6fd04850e523':
        raise ValueError('Registered protocol changed')
    smoke = json.loads((ROOT / 'experiments/AI_FOREGROUND_BCE_SMOKE_20261009/completion.json').read_text())
    if (smoke['status'] != 'passed_TRAIN_only_foreground_bce_smoke'
            or not smoke['coefficient1_exact_model_optimizer_parity']
            or not smoke['coefficient5_finite_updates']):
        raise ValueError('Actual matched CUDA smoke required')
    record = SESSION / 'foreground_bce_queue.json'
    launch = SESSION / 'foreground_bce_queue_launch.json'
    stdout, stderr = [SESSION / ('foreground_bce_queue.' + suffix) for suffix in ('stdout.log', 'stderr.log')]
    if any(p.exists() for p in (record, launch, stdout, stderr)):
        raise ValueError('Exclusive outputs required; inspect existing jobs before any resume')
    eligible = {'queue_ai_foreground_bce_pair.py', 'queue_ai_positive_dice_pair.py',
                'train_reliability_candidate.py', 'train_ai_presence_candidate.py',
                'train_ai_hard_candidate.py', 'train_ai_positive_dice_candidate.py',
                'train_ai_foreground_bce_candidate.py'}
    for process in psutil.process_iter(['name', 'cmdline']):
        if process.info['name'] != 'python.exe':
            continue
        if any(Path(value).name in eligible for value in (process.info['cmdline'] or [])):
            try:
                if Path(process.cwd()).resolve() == ROOT:
                    raise RuntimeError('Existing workspace queue/trainer PID ' + str(process.pid))
            except psutil.NoSuchProcess:
                continue
    command = [str(ROOT / '.venv-phase2/Scripts/python.exe'), 'tools/queue_ai_foreground_bce_pair.py',
               '--protocol', str(protocol), '--record', str(record)]
    with stdout.open('x') as output, stderr.open('x') as error:
        child = subprocess.Popen(command, cwd=ROOT, stdout=output, stderr=error,
                                 stdin=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
    evidence = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    pid=child.pid, creation_time=psutil.Process(child.pid).create_time(),
                    command=command, cwd=str(ROOT), stdout=str(stdout.relative_to(ROOT)),
                    stderr=str(stderr.relative_to(ROOT)), hidden=True,
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    calibration_fit=False, test_images_read=0, promotion=False)
    with launch.open('x', encoding='utf-8') as handle:
        json.dump(evidence, handle, indent=2, allow_nan=False)
    print(json.dumps(evidence), flush=True)


if __name__ == '__main__':
    main()
