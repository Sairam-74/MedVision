"""After both GPU arms finish, diagnose TRAIN fit without changing the experiment."""
import datetime
import json
from pathlib import Path
import subprocess
import sys
import time
import psutil

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.ai_atomic_io import json_atomic
from tools.evaluate_ai_baseline import sha


def read(path):
    started=time.monotonic()
    while True:
        try: return json.loads(path.read_text(encoding='utf-8-sig'))
        except (json.JSONDecodeError,PermissionError):
            if time.monotonic()-started>=30: raise
            time.sleep(.1)


def main():
    session=ROOT/'experiments/session_20261007_ai_loop_01'
    record_path=session/'presence_train_fit_watch_r2.json'
    if record_path.exists(): raise ValueError('Never duplicate a registered diagnostic')
    queue_path=session/'presence_queue_r2.json'
    queue=read(queue_path)
    if queue['run_ids']!=['AI_E7_v3_presence_reference_r2','AI_E8_v3_presence_supervision_r2']:
        raise ValueError('Unexpected pair')
    launcher=read(session/'presence_queue_r2_process.json')
    process=psutil.Process(launcher['pid'])
    if not any('queue_ai_presence_r2.ps1' in v for v in process.cmdline()):
        raise ValueError('Require live registered queue')
    created=process.create_time()
    files=['tools/watch_ai_presence_train_fit.py','tools/audit_ai_presence_train_fit.py',
           'tools/audit_ai_learning_fit.py']
    guards={**{k:v.lower() for k,v in queue['guards'].items()},**{name:sha(ROOT/name) for name in files}}
    record=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),guards=guards,
                scope='TRAIN-only read-only model-fit diagnostics after both GPU arms complete',
                no_optimizer_steps=True,validation_images_read=0,calibration_images_read=0,test_images_read=0)

    def update(status,**extra):
        record.update(status=status,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**extra)
        json_atomic(record_path,record)

    try:
        update('waiting_for_both_GPU_runs')
        while True:
            current=read(queue_path)
            if current['status']=='failed': raise RuntimeError('Training queue failed; do not diagnose unfinished checkpoints')
            if current['status']=='completed_training_only': break
            try:
                process=psutil.Process(launcher['pid'])
                alive=process.is_running() and process.create_time()==created
            except psutil.NoSuchProcess: alive=False
            if not alive: raise RuntimeError('Queue ended without a completed pair')
            time.sleep(20)
        for run_id,short in zip(queue['run_ids'],('E7','E8')):
            for name,digest in guards.items():
                if sha(ROOT/name)!=digest: raise ValueError('Frozen diagnostic input changed: '+name)
            output='experiments/AI_LEARNING_FIT_'+short+'_v3_presence_r2'
            update('running_read_only_TRAIN_fit',current=run_id,output=output)
            with (session/(short+'_TRAIN_fit_r2.log')).open('x') as stdout,(session/(short+'_TRAIN_fit_r2.stderr.log')).open('x') as stderr:
                completed=subprocess.run([str(ROOT/'.venv-phase2/Scripts/python.exe'),
                    'tools/audit_ai_presence_train_fit.py','--run','experiments/'+run_id,'--out',output],
                    cwd=ROOT,stdout=stdout,stderr=stderr)
            if completed.returncode: raise RuntimeError('TRAIN-fit diagnostic failed; retain artifacts/logs and diagnose')
        update('completed_TRAIN_fit_diagnostics_only')
        subprocess.run([str(ROOT/'.venv-phase2/Scripts/python.exe'),'tools/record_ai_loop.py','--observation',
            'Full unaugmented TRAIN-fit diagnostics completed for E7/E8 selected checkpoints; independent head/mask/union saved. No optimizer, CAL/test, or promotion.'],cwd=ROOT,check=True)
    except Exception as error:
        update('failed',error=str(error));raise


if __name__=='__main__': main()
