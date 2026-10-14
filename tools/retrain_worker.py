"""Separate-process candidate training and honest frozen-validation gates."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import traceback
import cv2
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from workflow_store import now
from medvision_pipeline import FracDataset, PreprocessConfig, sha
from medvision_serving import predict
from tools.train_pipeline import case_counts
from tools.run_experiment import summary


def acceptance(candidate,baseline,full_set,patient_independence,smoke,settings=None):
    settings=settings or {}
    min_tp=max(79,int(settings.get("minimum_true_positive",79)))
    min_tn=max(342,int(settings.get("minimum_true_negative",342)))
    checks={
        'not_smoke':not smoke,
        'frozen_463_validation':full_set and candidate['n_positive']==83 and candidate['n_normal']==380,
        'at_least_79_detected':candidate['case_true_positive']>=min_tp,
        'at_least_342_normals_rejected':candidate['case_true_negative']>=min_tn,
        'no_sensitivity_regression':candidate['case_false_negative']<=baseline['case_false_negative'],
        'no_specificity_regression':candidate['case_false_positive']<=baseline['case_false_positive'],
        'dice_improved':candidate['mean_positive_dice']>baseline['mean_positive_dice'],
        'iou_improved':candidate['mean_positive_iou']>baseline['mean_positive_iou'],
        'localization_improved':candidate.get('localized_positive',0)>baseline.get('localized_positive',0),
        'patient_partition_independence_verified':patient_independence,
    }
    return {'passed':all(checks.values()),'checks':checks,'failed':[k for k,v in checks.items() if not v],'minimum_true_positive':min_tp,'minimum_true_negative':min_tn}


def evaluate(ds,checkpoint,bundle,temporary_dir):
    cases=[]
    for i,row in enumerate(ds.rows):
        image,target=ds.native(i)
        # Existing serving contract reads a file; temporary native input stays local.
        tmp=Path(temporary_dir)/'evaluation-input.png';cv2.imwrite(str(tmp),image)
        try:
            prediction=predict(str(tmp),str(checkpoint),bundle)
            raw=base64.b64decode(prediction['mask_png_base64'])
            mask=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_GRAYSCALE)>0
            if mask.shape!=target.shape:raise ValueError('Native geometry mismatch in candidate evaluation')
            case=case_counts(row,mask,target)
            # An image-level signal only localizes if the delivered mask overlaps truth.
            case['localized']=bool(row['fractured'] and case['tp_pixels']>0 and case['iou']>=.1)
            cases.append(case)
        finally:tmp.unlink(missing_ok=True)
    metrics=summary(cases);metrics['localized_positive']=sum(r['localized'] for r in cases)
    tp,tn,fp,fn=[metrics[k] for k in ('case_true_positive','case_true_negative','case_false_positive','case_false_negative')]
    metrics.update(accuracy=(tp+tn)/(tp+tn+fp+fn),precision=tp/(tp+fp) if tp+fp else None,recall=tp/(tp+fn) if tp+fn else None,specificity=tn/(tn+fp) if tn+fp else None,f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,calibration=None,robustness=None,localization_definition='Positive mask/truth IoU >= 0.1; experimental, not clinical localization validation')
    return metrics,cases


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--job',required=True);ap.add_argument('--db',required=True);ap.add_argument('--root',required=True);a=ap.parse_args()
    root=Path(a.root).resolve();db=sqlite3.connect(a.db);db.row_factory=sqlite3.Row
    job=dict(db.execute('SELECT * FROM retraining_jobs WHERE id=?',(a.job,)).fetchone());config=json.loads(job['config'])
    candidate_id=a.job+'_candidate';out=root/'generated'/'candidates'/candidate_id;out.parent.mkdir(parents=True,exist_ok=True)
    # A retry uses a new immutable run directory rather than overwriting a failed candidate.
    if out.exists():out=out.with_name(out.name+'-'+now().replace(':','').replace('.',''))
    manifest=root/'experiments/data_v2/manifest.json';archive=root/'FracAtlas.zip'
    required=[manifest,archive,root/'best_model.pt']
    if not all(p.is_file() for p in required):
        with db:db.execute("UPDATE retraining_jobs SET status='blocked',error='Missing local frozen manifest, dataset archive or checkpoint',completed_at=? WHERE id=?",(now(),a.job))
        return
    settings=json.loads((root/'workflow_config.json').read_text(encoding='utf-8'))
    if sha(manifest)!=settings['frozen_manifest_sha256'] or sha(archive)!=settings['archive_sha256']:raise ValueError('Frozen dataset provenance changed')
    document=json.loads(manifest.read_text());rows=[]
    for feedback_id in json.loads(job['feedback_ids']):
        row=db.execute('SELECT f.*,c.payload FROM feedback f JOIN cases c ON c.id=f.analysis_id WHERE f.id=? AND f.confirmed=1',(feedback_id,)).fetchone()
        if not row:raise ValueError('Confirmed correction disappeared')
        case=json.loads(row['payload']);findings=json.loads(row['corrected_findings'])
        image=Path(case['imagePath']).resolve();mask=Path(row['corrected_mask_path']).resolve()
        if root not in image.parents or root not in mask.parents:raise ValueError('Correction points outside isolated clone')
        rows.append({'feedback_id':feedback_id,'image_path':str(image),'mask_path':str(mask),'image_sha256':sha(image),'mask_sha256':sha(mask),'fractured':int(findings['fracture_present'])})
    feedback_path=out.parent/(out.name+'-reviewed.json');feedback_path.write_text(json.dumps({'rows':rows},indent=2))
    args=[sys.executable,str(root/'tools/train_pipeline.py'),'--out',str(out),'--manifest',str(manifest),'--archive',str(archive),'--feedback-manifest',str(feedback_path),'--epochs',str(config['epochs']),'--device','cpu']
    if config['smoke']:args.append('--smoke')
    env=dict(__import__('os').environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PYTHONUTF8='1')
    subprocess.run(args,cwd=root,env=env,check=True)
    with db:db.execute("UPDATE retraining_jobs SET status='evaluating',candidate_id=? WHERE id=?",(candidate_id,a.job))
    production=dict(db.execute("SELECT * FROM model_versions WHERE status='production'").fetchone())
    ds=FracDataset(archive,manifest,'val',PreprocessConfig())
    if config['smoke']:ds.rows=[r for label in (1,0) for r in [r for r in ds.rows if int(r['fractured'])==label][:2]]
    import torch;torch.set_num_threads(2)
    candidate,cases=evaluate(ds,out/'best_model.pt',str(out/'bundle.json'),out)
    baseline,baseline_cases=evaluate(ds,root/'best_model.pt',production['bundle_path'],out)
    gates=acceptance(candidate,baseline,len(ds.rows)==463,document.get('patient_independence_verified',False),config['smoke'],settings)
    metrics={'bundle_sha256':sha(out/'bundle.json'),'evaluated_production_version':production['id'],'candidate':candidate,'baseline':baseline,'acceptance':gates,'manifest_sha256':sha(manifest),'archive_sha256':sha(archive),'reserved_test_evaluated':False,'validation_size':len(ds),'smoke':config['smoke']}
    (out/'workflow-evaluation.json').write_text(json.dumps({'metrics':metrics,'cases':cases,'baseline_cases':baseline_cases},indent=2))
    status='candidate_ready' if gates['passed'] else 'rejected'
    with db:
        db.execute('INSERT INTO model_versions(id,status,bundle_path,checkpoint_sha,dataset_version,training_config,metrics,created_at,trained_at,evaluated_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(candidate_id,status,str(out/'bundle.json'),sha(out/'best_model.pt'),sha(manifest),(out/'config.json').read_text(),json.dumps(metrics),job['created_at'],now(),now()))
        db.execute('UPDATE retraining_jobs SET status=?,candidate_id=?,completed_at=?,error=? WHERE id=?',(status,candidate_id,now(),None if gates['passed'] else 'Candidate rejected by validation gates: '+', '.join(gates['failed']),a.job))
    print(json.dumps(metrics),flush=True)

if __name__=='__main__':main()
