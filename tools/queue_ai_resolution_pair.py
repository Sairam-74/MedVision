"""Registered 256/512 pair: train, native VAL audit, raw TRAIN fit, compare.

Never accesses CAL/test images or promotes. Actual failure review follows.
"""
import argparse
import datetime
import json
from pathlib import Path
import subprocess
import sys

import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.ai_atomic_io import json_atomic
from tools.evaluate_ai_baseline import sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--protocol',required=True)
    parser.add_argument('--record',required=True)
    args = parser.parse_args()
    protocol_path,record_path = Path(args.protocol).resolve(),Path(args.record).resolve()
    if ROOT not in protocol_path.parents or ROOT not in record_path.parents or record_path.exists():
        raise ValueError('Exclusive workspace queue record and registered protocol required')
    protocol = json.loads(protocol_path.read_text())
    if protocol['status'] != 'registered_after_completed_native_failure_analysis' or protocol['major_factor'] != 'input_resolution':
        raise ValueError('Completed prior failure analysis and resolution registration required')
    smoke = ROOT/protocol['smoke_output']
    completion = json.loads((smoke/'completion.json').read_text())
    config = json.loads((smoke/'config.json').read_text())
    if completion['status'] != 'passed_TRAIN_only_resolution_smoke' or not all(completion.get(k) is True for k in (
            'full_matched_initialization','cached256_vs_native256_exact','input512_batch2_fp32_feasible')):
        raise ValueError('Passed exact256 parity and512 batch2 FP32 smoke required')
    if config['initial_snapshot_sha256'] != protocol['initialization']['snapshot_sha256']:
        raise ValueError('Smoke and registered full initializer differ')
    session = record_path.parent
    guards = dict(protocol['input_hashes'])
    guards[str(protocol_path.relative_to(ROOT))] = sha(protocol_path)
    for file in ('completion.json','config.json'):
        guards[str((smoke/file).relative_to(ROOT))] = sha(smoke/file)
    for name,digest in config['source_hashes'].items():
        if sha(ROOT/name) != digest:
            raise ValueError('Smoke source changed: '+name)
        guards[name] = digest
    record = dict(status='registered',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),guards=guards,
        run_ids=[protocol['reference'],protocol['candidate']],single_factor='Native-derived input resolution256 vs512',
        calibration_fit=False,test_images_read=0,promotion=False)

    def check():
        for name,digest in guards.items():
            if sha(ROOT/name) != digest:
                raise ValueError('Frozen queue input changed: '+name)

    def update(status,**extra):
        record.update(status=status,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**extra)
        json_atomic(record_path,record)

    def other_trainer():
        names = {'train_baseline.py','train_pipeline.py','train_reliability_candidate.py','train_ai_presence_candidate.py',
                 'train_ai_hard_candidate.py','train_ai_positive_dice_candidate.py','train_ai_foreground_bce_candidate.py',
                 'train_ai_resolution_candidate.py'}
        for process in psutil.process_iter(['pid','name','cmdline']):
            if process.info['name'] != 'python.exe':
                continue
            if any(Path(v).name in names for v in process.info['cmdline'] or []):
                try:
                    if Path(process.cwd()).resolve() == ROOT:
                        return process.pid
                except (psutil.NoSuchProcess,psutil.AccessDenied):
                    continue
        return None

    def run_tool(name,arguments,log):
        check()
        with (session/(log+'.log')).open('x') as stdout,(session/(log+'.stderr.log')).open('x') as stderr:
            result = subprocess.run([str(ROOT/'.venv-phase2/Scripts/python.exe'),'tools/'+name,*arguments],
                                    cwd=ROOT,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:
            raise RuntimeError(name+' failed; preserve evidence and diagnose before continuing')

    def record_progress(observation):
        subprocess.run([str(ROOT/'.venv-phase2/Scripts/python.exe'),'tools/record_ai_loop.py',
                        '--observation',observation],cwd=ROOT,check=True,creationflags=subprocess.CREATE_NO_WINDOW)

    check()
    json_atomic(record_path,record)
    try:
        for size,name,audit,fit in zip((256,512),record['run_ids'],protocol['audit_ids'],protocol['fit_ids']):
            if other_trainer():
                raise RuntimeError('Another workspace trainer is active; no duplicate GPU work')
            run = 'experiments/'+name
            if (ROOT/run).exists():
                raise ValueError('Run exists; no automatic overwrite/restart')
            update('training',current=name,input_size=size)
            run_tool('train_ai_resolution_candidate.py',['--protocol',str(protocol_path),'--out',run,'--input-size',str(size)],name)
            update('native_validation_audit',current=name,audit='experiments/'+audit)
            run_tool('audit_ai_presence_candidate.py',['--run',run,'--out','experiments/'+audit,'--device','cuda'],audit)
            update('independent_mask_error_groups')
            run_tool('ai_error_groups.py',['--audit','experiments/'+audit,'--out','experiments/'+audit+'_error_groups'],audit+'_groups')
            update('TRAIN_fit_read_only',current=name)
            run_tool('audit_ai_presence_train_fit.py',['--run',run,'--out','experiments/'+fit],fit)
            record_progress('Completed registered '+name+' training, native CUDA VAL463 audit and raw TRAIN fit. '+
                            'Actual failure review and matched comparison remain required; no CAL/test/promotion.')
        update('comparing_matched_pair')
        run_tool('analyze_ai_resolution_pair.py',['--reference','experiments/'+protocol['audit_ids'][0],
            '--candidate','experiments/'+protocol['audit_ids'][1],'--out','experiments/'+protocol['pair_id']],protocol['pair_id'])
        update('completed_training_and_native_audits_only',next='Actual failure review and continue if all gates unmet')
        record_progress('Resolution pair completed training, native VAL audits, raw TRAIN fits and paired analysis. '+
                        'Root must review actual FP/FN/masks, original coverage and remaining gates. No automatic CAL/test/promotion.')
    except Exception as error:
        update('failed',error=str(error))
        raise


if __name__ == '__main__':
    main()
