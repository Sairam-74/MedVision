"""TRAIN-only hard examples, repeated errors in two frozen model snapshots.

Catalog only: no duplication, resampling, parameter update or test access.
"""
import json
from pathlib import Path
import sys
import time
import zipfile
import cv2
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import medvision_ai as m
from tools.run_experiment import native_pair
from tools.evaluate_ai_baseline import save, sha


def main():
    out=ROOT/'experiments/AI_TRAIN_HARD_SETS_20261007'
    if out.exists():raise ValueError('Never overwrite a mining catalog')
    if not torch.cuda.is_available():raise RuntimeError('CUDA explicitly required')
    torch.set_num_threads(2);cv2.setNumThreads(1);m.set_seed(42)
    manifest_path=ROOT/'experiments/data_v3_reliability_20261007/manifest.json'
    manifest=json.loads(manifest_path.read_text()); rows=[r for r in manifest['rows'] if r['split']=='train']
    blocked={r['image_id'] for r in manifest['rows'] if r['split']!='train'}
    if len(rows)!=2808 or blocked & {r['image_id'] for r in rows}:raise ValueError('Training partition mismatch')
    snapshot=ROOT/'experiments/session_20261007_ai_baseline/E2_interrupted_snapshot'
    epoch=json.loads((snapshot/'best_validation.json').read_text())
    if sha(snapshot/'best_model.pt') != epoch['model_sha256']:raise ValueError('Frozen E2 snapshot mismatch')
    identities={'production_original':(ROOT/'best_model.pt',.9),'E2_completed_epoch10':(snapshot/'best_model.pt',.5)}
    models={}
    for key,(path,threshold) in identities.items():
        model=m.AttentionUNet().cuda();m._load_model_weights(model,str(path));model.eval();models[key]=model
    out.mkdir();save(out/'config.json',dict(scope='TRAIN ONLY hard-case catalog; historical original exposure unknown; no sampling or model changes',
        samples=len(rows),manifest_sha256=sha(manifest_path),models={key:dict(checkpoint_sha256=sha(path),threshold=threshold) for key,(path,threshold) in identities.items()},
        positive_rule='ground truth fracture AND native Dice<.20 in BOTH models at their recorded thresholds; includes empty or wrong-region misses',
        negative_rule='explicit ground truth normal AND nonempty native mask in BOTH models at their recorded thresholds',
        scores='algorithmic difficulty, not clinically adjudicated subtle/nondisplaced labels',torch=torch.__version__,device='cuda',source_sha256=sha(__file__),test_images_read=0))
    records=[];started=time.perf_counter()
    with zipfile.ZipFile(ROOT/'FracAtlas.zip') as z,torch.inference_mode():
        annotations={a['id']:a for a in json.loads(z.read('FracAtlas/Annotations/COCO JSON/COCO_fracture_masks.json'))['annotations']}
        for index,row in enumerate(rows):
            if row['image_id'] in blocked:raise ValueError('Validation/calibration/test image forbidden')
            image,gt=native_pair(z,row,annotations);h,w=image.shape
            x=m._ensure_4d_tensor(m.preprocess_image_array(image)).cuda()
            model_stats={}
            for key,model in models.items():
                prob=model(x)[0,0].cpu().numpy()
                if not np.isfinite(prob).all():raise RuntimeError('Nonfinite mining output')
                native=cv2.resize((prob>=identities[key][1]).astype(np.uint8),(w,h),interpolation=cv2.INTER_NEAREST).astype(bool)
                target=gt.astype(bool);tp=int((native & target).sum());pred=int(native.sum());g=int(gt.sum())
                model_stats[key]=dict(prediction_present=pred>0,case_score=float(prob.max()),predicted_fraction=pred/(h*w),tp_pixels=tp,fp_pixels=pred-tp,fn_pixels=g-tp,
                    dice=2*tp/(pred+g) if g else None,iou=tp/(pred+g-tp) if g else None)
            positive=bool(int(row['fractured']))
            hard_positive=positive and all(v['dice']<.2 for v in model_stats.values())
            hard_negative=not positive and all(v['prediction_present'] for v in model_stats.values())
            records.append(dict(image_id=row['image_id'],group=row['group'],split='train',positive=positive,hard_positive=hard_positive,hard_negative=hard_negative,
                                models=model_stats,flags={k:int(row[k]) for k in ('hand','leg','hip','shoulder','hardware','multiscan','frontal','lateral','oblique')}))
            if (index+1)%100==0:
                state=dict(status='mining_training_only',images=index+1,total=len(rows),elapsed_seconds=time.perf_counter()-started,test_images_read=0)
                (out/'progress.json').write_text(json.dumps(state,indent=2));print(json.dumps(state),flush=True)
    save(out/'per_training_case.json',records)
    common=dict(scope='TRAIN ONLY. Representative distribution retained; catalog not yet used in either matched E5/E6 run. No duplication.',
                proposed_future_use='After current loss comparison: bounded within-class emphasis, preserve class prevalence and uniform coverage, no validation/calibration/test membership',
                test_images_read=0)
    for name,key in [('HARD_POSITIVE_SET','hard_positive'),('HARD_NEGATIVE_SET','hard_negative')]:
        selected=[r for r in records if r[key]]
        save(out/(name+'.json'),dict(common,definition=json.loads((out/'config.json').read_text())['positive_rule' if key=='hard_positive' else 'negative_rule'],
                                   n=len(selected),image_ids=[r['image_id'] for r in selected],cases=selected))
    save(out/'completion.json',dict(status='completed_training_catalog',images=len(records),hard_positive=sum(r['hard_positive'] for r in records),hard_negative=sum(r['hard_negative'] for r in records),
                                  test_images_read=0,training_distribution_modified=False,elapsed_seconds=time.perf_counter()-started))
    print((out/'completion.json').read_text(),flush=True)


if __name__=='__main__':main()
