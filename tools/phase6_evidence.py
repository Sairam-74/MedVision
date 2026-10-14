"""Validation-only Phase 6 evidence from a copied completed development epoch.

Never calls the final test while the selection/training gate is outstanding.
"""
import csv
import hashlib
import json
from pathlib import Path
import sys
import time
import zipfile
import cv2
import numpy as np
import psutil
import torch
from scipy.optimize import linear_sum_assignment
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import medvision_ai as m
from medvision_pipeline import sha
from tools.run_experiment import native_pair, policy_mask, summary


def region_recall(prediction, targets, threshold):
    n,labels=cv2.connectedComponents(prediction.astype(np.uint8),8)
    if n==1 or not targets: return 0,len(targets),n-1
    sizes=np.bincount(labels.ravel(),minlength=n)[1:]
    overlaps=[]
    for gt in targets:
        intersections=np.bincount(labels[gt.astype(bool)],minlength=n)[1:]
        union=sizes+int(gt.sum())-intersections
        overlaps.append(intersections/np.maximum(union,1))
    iou=np.array(overlaps)
    # Maximize number above threshold first, then overlap; one-to-one.
    cost=(iou>=threshold).astype(float)*2+iou/max(1,min(iou.shape))
    rows,cols=linear_sum_assignment(cost,maximize=True)
    matches=int((iou[rows,cols]>=threshold).sum())
    return matches,len(targets),n-1-matches


def main():
    out=Path('experiments/P6_development_validation')
    if out.exists(): raise ValueError('Never overwrite evidence; choose a new run ID')
    active=Path('experiments/E2_corrected_baseline')
    selected=json.loads((active/'best_validation.json').read_text())
    data=(active/'best_model.pt').read_bytes()
    if hashlib.sha256(data).hexdigest()!=selected['model_sha256']:
        raise RuntimeError('Checkpoint changed during snapshot; retry rather than mixing metadata')
    out.mkdir()
    (out/'candidate.pt').write_bytes(data)
    manifest=json.loads(Path('experiments/data_v1/manifest.json').read_text())
    rows=[r for r in manifest['rows'] if r['split']=='val']
    config=dict(scope='validation only; completed-epoch development snapshot, NOT final selected model',
                epoch=selected['epoch'],checkpoint_sha256=sha(out/'candidate.pt'),
                manifest_sha256=sha('experiments/data_v1/manifest.json'),split='val',
                output_contract='sigmoid-probabilities-v1',preprocess='CLAHE2/8x8+Gaussian3x3; stretch256; /255',
                thresholds=[round(i*.05,2) for i in range(1,20)],policies=['all','largest','min16'],
                selection='agreed validation Dice rank with sensitivity/FPR within 2 points of .5/all; <.005 Dice tie prefers simpler all policy',
                region_iou_thresholds=[.10,.50],empty_gt='exclude from positive Dice; undefined precision null; normals separate',
                final_test_authorized=False,gate='Full training/controlled finalist selection unfinished; preserve test',
                source_sha256={n:sha(n) for n in ['tools/phase6_evidence.py','medvision_ai.py','tools/run_experiment.py']})
    (out/'config.json').write_text(json.dumps(config,indent=2))
    torch.set_num_threads(2); cv2.setNumThreads(1); m.set_seed(42)
    model=m.AttentionUNet(); m._load_model_weights(model,str(out/'candidate.pt')); model.eval()
    cases={(t,p):[] for t in config['thresholds'] for p in config['policies']}
    probabilities={}; latency=[]; started=time.perf_counter()
    with zipfile.ZipFile('FracAtlas.zip') as z,torch.inference_mode():
        annotations={a['id']:a for a in json.loads(z.read('FracAtlas/Annotations/COCO JSON/COCO_fracture_masks.json'))['annotations']}
        for k,row in enumerate(rows):
            image,gt=native_pair(z,row,annotations)
            x=m._ensure_4d_tensor(m.preprocess_image_array(image))
            t0=time.perf_counter(); prob=model(x)[0,0].numpy(); latency.append((time.perf_counter()-t0)*1000)
            probabilities[row['image_id']]=prob.astype(np.float16)
            # Counts computed exactly at model grid using native nearest-source mapping.
            native_ys=np.minimum((np.arange(image.shape[0])*256/image.shape[0]).astype(int),255)
            native_xs=np.minimum((np.arange(image.shape[1])*256/image.shape[1]).astype(int),255)
            native_index=(native_ys[:,None]*256+native_xs[None,:]).ravel()
            weights=np.bincount(native_index,minlength=65536)
            foreground=np.bincount(native_index,weights=gt.ravel(),minlength=65536)
            for t,policy in cases:
                mask=policy_mask(prob,t,policy); flat=mask.ravel().astype(bool)
                tp=int(foreground[flat].sum()); fp=int(weights[flat].sum())-tp; fn=int(gt.sum())-tp
                positive=bool(int(row['fractured']))
                cases[(t,policy)].append(dict(image_id=row['image_id'],group=row['group'],positive=positive,
                    prediction_present=bool(mask.any()),tp_pixels=tp,fp_pixels=fp,fn_pixels=fn,
                    dice=2*tp/(2*tp+fp+fn) if positive else None,iou=tp/(tp+fp+fn) if positive else None,
                    precision=tp/(tp+fp) if tp+fp else None,recall=tp/(tp+fn) if tp+fn else None,
                    components=int(cv2.connectedComponents(mask,8)[0]-1)))
            if (k+1)%100==0:
                (out/'state.json').write_text(json.dumps(dict(status='validation',images=k+1,total=len(rows))))
                print(f'validation {k+1}/{len(rows)}',flush=True)
    comparisons={f'{t:.2f}/{policy}':summary(c) for (t,policy),c in cases.items()}
    baseline=comparisons['0.50/all']
    qualifying=[(t,p) for t,p in cases if comparisons[f'{t:.2f}/{p}']['case_sensitivity']>=baseline['case_sensitivity']-.02
                and comparisons[f'{t:.2f}/{p}']['normal_false_positive_rate']<=baseline['normal_false_positive_rate']+.02]
    winner=max(qualifying,key=lambda k:comparisons[f'{k[0]:.2f}/{k[1]}']['mean_positive_dice'])
    best_dice=comparisons[f'{winner[0]:.2f}/{winner[1]}']['mean_positive_dice']
    simpler=[k for k in qualifying if k[1]=='all' and best_dice-comparisons[f'{k[0]:.2f}/{k[1]}']['mean_positive_dice']<.005]
    if simpler: winner=max(simpler,key=lambda k:comparisons[f'{k[0]:.2f}/{k[1]}']['mean_positive_dice'])
    selected_cases=cases[winner]; measured=summary(selected_cases)
    measured['specificity']=1-measured['normal_false_positive_rate']
    measured['case_precision']=measured['case_true_positive']/(measured['case_true_positive']+measured['case_false_positive']) if measured['case_true_positive']+measured['case_false_positive'] else None
    subgroup={}
    for flag in ['hand','leg','hip','shoulder','mixed','hardware','multiscan','frontal','lateral','oblique']:
        subset=[c for r,c in zip(rows,selected_cases) if int(r[flag])]
        if subset: subgroup[flag]=summary(subset)
    regions={str(t):dict(matches=0,ground_truth_instances=0,false_positive_regions=0) for t in [.1,.5]}
    examples=[]
    with zipfile.ZipFile('FracAtlas.zip') as z:
        for row in rows:
            image,gt=native_pair(z,row,annotations)
            # Saved float16 maps are qualitative only. Exact raw probability is
            # recomputed for region/final selected counts, never threshold float16.
            with torch.inference_mode(): prob=model(m._ensure_4d_tensor(m.preprocess_image_array(image)))[0,0].numpy()
            native=cv2.resize(policy_mask(prob,*winner),(image.shape[1],image.shape[0]),interpolation=cv2.INTER_NEAREST)
            targets=[m._rasterize_coco_segmentation(annotations[aid]['segmentation'],row['width'],row['height']) for aid in row['annotation_ids']]
            for threshold in (.1,.5):
                hits,total,fp=region_recall(native,targets,threshold)
                for key,value in zip(['matches','ground_truth_instances','false_positive_regions'],[hits,total,fp]): regions[str(threshold)][key]+=value
        for values in regions.values(): values['recall']=values['matches']/values['ground_truth_instances'] if values['ground_truth_instances'] else None
    (out/'comparison.json').write_text(json.dumps(comparisons,indent=2))
    (out/'per_case.json').write_text(json.dumps(selected_cases,indent=2))
    with (out/'per_case.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(selected_cases[0])); writer.writeheader(); writer.writerows(selected_cases)
    np.savez_compressed(out/'probabilities_float16.npz',**probabilities)
    result=dict(selection=dict(threshold=winner[0],policy=winner[1]),metrics=measured,regions=regions,subgroups=subgroup,
                timing=dict(forward_median_ms=float(np.median(latency[1:])),forward_p95_ms=float(np.percentile(latency[1:],95)),
                            first_forward_ms=latency[0],elapsed_seconds=time.perf_counter()-started,
                            peak_process_rss_bytes=getattr(psutil.Process().memory_info(),'peak_wset',psutil.Process().memory_info().rss),
                            device='CPU; i5-13500HX; torch threads2; concurrent E2 training; NOT isolated final benchmark'),
                final_test_evaluated=False,final_bundle_frozen=False,limitation='Full E2 training still running; v1 contradictory training labels; final v2 comparisons pending')
    (out/'metrics.json').write_text(json.dumps(result,indent=2))
    (out/'state.json').write_text(json.dumps(dict(status='completed_validation_only',final_test_evaluated=False)))
    print(json.dumps(result['metrics'],indent=2))


if __name__=='__main__': main()
