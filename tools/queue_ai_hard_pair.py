"""Registered hard pair: sequential GPU train/native audit/TRAIN fit.

Never fits CAL, reads test pixels, promotes, or selects a next intervention.
Root must inspect the completed artifacts and actually review native images.
"""
import argparse
import datetime
import json
from pathlib import Path
import subprocess
import sys
import psutil

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.ai_atomic_io import json_atomic
from tools.evaluate_ai_baseline import sha


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--protocol',required=True);ap.add_argument('--record',required=True)
    args=ap.parse_args();protocol_path,record_path=Path(args.protocol).resolve(),Path(args.record).resolve()
    if ROOT not in protocol_path.parents or ROOT not in record_path.parents or record_path.exists():
        raise ValueError('Workspace protocol and exclusive queue record required')
    protocol=json.loads(protocol_path.read_text());session=record_path.parent
    if protocol['status']!='registered_after_completed_native_failure_analysis': raise ValueError('Full prior native failure analysis required')
    smoke=ROOT/protocol['smoke_output']
    smoke_completion=json.loads((smoke/'completion.json').read_text())
    smoke_config=json.loads((smoke/'config.json').read_text())
    if smoke_completion['status']!='passed_TRAIN_only_hard_smoke' or smoke_completion.get('full_matched_initialization') is not True:
        raise ValueError('Actual TRAIN-only GPU smoke must pass first')
    if smoke_config['protocol_sha256']!=sha(protocol_path):
        raise ValueError('Passed smoke belongs to a different registered protocol')
    initializer=ROOT/protocol['initial_run']
    initializer_bundle=json.loads((initializer/'bundle.json').read_text())
    initializer_snapshot=initializer/f"epoch_{initializer_bundle['epoch']:03d}_resume.pt"
    if smoke_config['initial_snapshot_sha256']!=sha(initializer_snapshot):
        raise ValueError('Passed smoke used a different selected full initializer')
    sources=['tools/queue_ai_hard_pair.py','tools/audit_ai_presence_candidate.py','tools/audit_ai_presence_train_fit.py',
        'tools/ai_error_groups.py','tools/analyze_ai_hard_pair.py','tools/analyze_ai_pair.py','tools/ai_validation_audit.py',
        'tools/evaluate_ai_baseline.py','tools/audit_ai_learning_fit.py']
    guards=dict(protocol['input_hashes'])
    guards.update({s:sha(ROOT/s) for s in sources})
    guards.update({str(protocol_path.relative_to(ROOT)):sha(protocol_path),str((smoke/'completion.json').relative_to(ROOT)):sha(smoke/'completion.json')})
    for s,digest in smoke_config['source_hashes'].items():
        if sha(ROOT/s)!=digest: raise ValueError('Smoke source differs: '+s)
        guards[s]=digest
    record=dict(status='registered',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),guards=guards,
        run_ids=[protocol['reference'],protocol['candidate']],single_factor='Within-class bounded hard example factor1 vs2',
        calibration_fit=False,test_images_read=0,promotion=False)
    json_atomic(record_path,record)

    def update(status,**extra):
        record.update(status=status,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**extra)
        json_atomic(record_path,record)

    def check():
        for source,digest in guards.items():
            if sha(ROOT/source)!=digest: raise ValueError('Frozen queue input changed: '+source)

    def other_workspace_trainer():
        names={'train_baseline.py','train_pipeline.py','train_reliability_candidate.py','train_ai_presence_candidate.py','train_ai_hard_candidate.py'}
        for proc in psutil.process_iter(['pid','name','cmdline']):
            if proc.info['name']!='python.exe': continue
            command=proc.info['cmdline'] or []
            if any(Path(v).name in names for v in command):
                try:
                    if Path(proc.cwd()).resolve()==ROOT: return proc.info['pid']
                except (psutil.NoSuchProcess,psutil.AccessDenied): continue
        return None

    def run_tool(name,arguments,log):
        check()
        with (session/(log+'.log')).open('x') as stdout,(session/(log+'.stderr.log')).open('x') as stderr:
            result=subprocess.run([str(ROOT/'.venv-phase2/Scripts/python.exe'),'tools/'+name,*arguments],cwd=ROOT,stdout=stdout,stderr=stderr)
        if result.returncode: raise RuntimeError(name+' failed; preserve full evidence and diagnose before continuing')

    try:
        for factor,name,audit,fit in zip((1,2),record['run_ids'],protocol['audit_ids'],protocol['fit_ids']):
            check()
            if other_workspace_trainer(): raise RuntimeError('Another workspace trainer is active; no duplicate GPU work')
            run='experiments/'+name
            if (ROOT/run).exists(): raise ValueError('Run exists; no automatic overwrite/restart')
            update('training',current=name,hard_factor=factor)
            run_tool('train_ai_hard_candidate.py',['--protocol',str(protocol_path),'--out',run,'--hard-factor',str(factor)],name)
            update('native_validation_audit',current=name,audit='experiments/'+audit)
            run_tool('audit_ai_presence_candidate.py',['--run',run,'--out','experiments/'+audit,'--device','cuda'],audit)
            update('independent_mask_error_groups')
            run_tool('ai_error_groups.py',['--audit','experiments/'+audit,'--out','experiments/'+audit+'_error_groups'],audit+'_groups')
            update('TRAIN_fit_read_only',current=name)
            run_tool('audit_ai_presence_train_fit.py',['--run',run,'--out','experiments/'+fit],fit)
            subprocess.run([str(ROOT/'.venv-phase2/Scripts/python.exe'),'tools/record_ai_loop.py','--observation',
                'Completed registered '+name+' training, full CUDA native VAL audit and raw TRAIN-fit. Actual image review and matched comparison required; no CAL/test/promotion.'],cwd=ROOT,check=True)
        update('comparing_matched_pair')
        left=ROOT/'experiments'/record['run_ids'][0]/'initial_parameters.json';right=ROOT/'experiments'/record['run_ids'][1]/'initial_parameters.json'
        if json.loads(left.read_text())!=json.loads(right.read_text()): raise ValueError('Matched model/optimizer initialization differs')
        run_tool('analyze_ai_hard_pair.py',['--reference','experiments/'+protocol['audit_ids'][0],
            '--candidate','experiments/'+protocol['audit_ids'][1],'--out','experiments/'+protocol['pair_id']],protocol['pair_id'])
        subprocess.run([str(ROOT/'.venv-phase2/Scripts/python.exe'),'tools/record_ai_loop.py','--observation',
            'Hard-example pair full training/native audits/TRAIN fits/paired analysis complete. Root must review actual FP/FN/native masks, original useful coverage and unmet gates, then continue evidence-based experiments. No automatic CAL/test/promotion.'],cwd=ROOT,check=True)
        update('completed_training_and_native_audits_only',next='Actual image review and evidence-based next intervention if gates unmet')
    except Exception as error:
        update('failed',error=str(error))
        raise


if __name__=='__main__': main()
