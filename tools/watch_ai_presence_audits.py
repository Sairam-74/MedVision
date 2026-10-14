"""Wait for registered full runs, audit only frozen VAL, compare; never promote."""
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


def main():
    session=ROOT/'experiments/session_20261007_ai_loop_01'
    record_path=session/'presence_audit_watch_r2.json'
    if record_path.exists():
        raise ValueError('Watcher registered already; never duplicate audit work')
    queue_path=session/'presence_queue_r2.json'
    queue=json.loads(queue_path.read_text(encoding='utf-8-sig'))
    if queue['run_ids']!=['AI_E7_v3_presence_reference_r2','AI_E8_v3_presence_supervision_r2']:
        raise ValueError('Unexpected pair')
    files=['tools/watch_ai_presence_audits.py','tools/audit_ai_presence_candidate.py',
           'tools/analyze_ai_presence_pair.py','tools/analyze_ai_pair.py','tools/ai_error_groups.py',
           'tools/ai_validation_audit.py','tools/evaluate_ai_baseline.py']
    guards={**{str(k):v.lower() for k,v in queue['guards'].items()},**{name:sha(ROOT/name) for name in files}}
    launcher=json.loads((session/'presence_queue_r2_process.json').read_text(encoding='utf-8-sig'))
    process=psutil.Process(launcher['pid'])
    if not any('queue_ai_presence_r2.ps1' in v for v in process.cmdline()):
        raise ValueError('Queue PID does not identify registered launcher')
    created=process.create_time()
    record=dict(status='registered',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                guards=guards,test_images_read=0,calibration_fit=False,promotion=False)

    def update(status,**extra):
        record.update(status=status,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**extra)
        json_atomic(record_path,record)

    def check():
        for name,digest in guards.items():
            if sha(ROOT/name)!=digest:
                raise ValueError('Frozen audit input changed: '+name)

    def run_tool(name,arguments,log):
        check()
        with (session/(log+'.log')).open('x') as stdout,(session/(log+'.stderr.log')).open('x') as stderr:
            result=subprocess.run([str(ROOT/'.venv-phase2/Scripts/python.exe'),'tools/'+name,*arguments],
                                  cwd=ROOT,stdout=stdout,stderr=stderr)
        if result.returncode:
            raise RuntimeError(name+' failed; preserve log/output and diagnose')

    try:
        update('waiting_for_reference')
        for run_id,audit_id in zip(queue['run_ids'],['AI_AUDIT_E7_v3_presence_r2','AI_AUDIT_E8_v3_presence_r2']):
            run=ROOT/'experiments'/run_id
            update('waiting_for_completed_training',current=run_id)
            while True:
                if (run/'state.json').exists():
                    state=json.loads((run/'state.json').read_text())
                    if state['status']=='completed' and state['epochs_finished']==12 and not state['smoke']:
                        break
                current=json.loads(queue_path.read_text(encoding='utf-8-sig'))
                if current['status']=='failed':
                    raise RuntimeError('Training queue failed: '+current.get('error','unknown'))
                if current['status']=='completed_training_only':
                    raise RuntimeError('Queue completed but run is not complete')
                try:
                    process=psutil.Process(launcher['pid'])
                    alive=process.create_time()==created and process.is_running()
                except psutil.NoSuchProcess:
                    alive=False
                if not alive:
                    raise RuntimeError('Incomplete run with no live registered queue; do not audit unfinished checkpoint')
                time.sleep(20)
            audit='experiments/'+audit_id
            update('running_native_validation_audit',current=run_id,audit=audit)
            run_tool('audit_ai_presence_candidate.py',['--run','experiments/'+run_id,'--out',audit,'--device','cpu'],audit_id)
            update('running_independent_mask_error_groups')
            run_tool('ai_error_groups.py',['--audit',audit,'--out',audit+'_error_groups'],audit_id+'_groups')
            subprocess.run([str(ROOT/'.venv-phase2/Scripts/python.exe'),'tools/record_ai_loop.py','--observation',
                'Completed full native independent-mask/presence/review-alert validation audit for '+run_id+'. No CAL/test/promotion.'],cwd=ROOT,check=True)
        update('comparing_matched_pair')
        run_tool('analyze_ai_presence_pair.py',['--reference','experiments/AI_AUDIT_E7_v3_presence_r2',
            '--candidate','experiments/AI_AUDIT_E8_v3_presence_r2','--out','experiments/AI_E7_E8_PRESENCE_PAIR_r2'],
            'presence_pair_r2_analysis')
        subprocess.run([str(ROOT/'.venv-phase2/Scripts/python.exe'),'tools/record_ai_loop.py','--observation',
            'E7/E8r2 training, full native masks/head/conservative alerts and matched analysis completed. Inspect failures and gates; continue targeted experiments if unmet. No automatic final test or promotion.'],cwd=ROOT,check=True)
        update('completed_validation_audits_only',next='Root inspect actual masks/curves and unmet gates; continue registered evidence-based intervention. No CAL/test/promotion.')
    except Exception as error:
        update('failed',error=str(error))
        raise


if __name__=='__main__':
    main()
