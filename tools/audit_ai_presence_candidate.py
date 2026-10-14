"""Full frozen VAL audit of completed E7/E8: masks, head and review alerts."""
import os
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time
import cv2
import numpy as np
import psutil
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import medvision_pipeline as p
from tools import ai_metrics as a
from tools.ai_presence_model import PresenceAttentionUNet, CONTRACT, ARCHITECTURE, review_group
from tools.ai_validation_audit import inspect_case, summarize, MANIFEST, MANIFEST_SHA
from tools.evaluate_ai_baseline import save, sha, write_csv, panel, inspect_splits
from tools.ai_atomic_io import json_atomic


def combine_case(mask_case, head_score, supervised):
    case = dict(mask_case)
    head_positive = bool(head_score>=.5) if supervised else None
    alert = case['prediction_present'] or bool(head_positive)
    category = ('TP' if alert else 'FN') if case['positive'] else ('FP' if alert else 'TN')
    case.update(head_score=head_score if supervised else None,classifier_prediction_present=head_positive,
        review_alert_present=alert,review_alert_category=category,
        head_mask_group=review_group(head_positive,case['prediction_present']) if supervised else 'reference_mask_only')
    alert_case = dict(case,prediction_present=alert,category=category,
        case_score=max(case['case_score'],head_score) if supervised else case['case_score'])
    head_case = dict(case,prediction_present=head_positive,case_score=head_score) if supervised else None
    return case, alert_case, head_case


def plots(out, cases, classification, calibration, prefix, label):
    import matplotlib.pyplot as plt
    curves = a.curves(cases)
    save(out/(prefix+'_curves.json'), curves)
    fig, axes = plt.subplots(1,3,figsize=(14,4))
    cm = classification['confusion_matrix']
    matrix = np.array([[cm['tn'],cm['fp']],[cm['fn'],cm['tp']]])
    axes[0].imshow(matrix,cmap='Blues')
    for (i,j), value in np.ndenumerate(matrix):
        axes[0].text(j,i,str(value),ha='center',va='center',color='white' if value>matrix.max()/2 else 'black')
    axes[0].set(xticks=[0,1],yticks=[0,1],xticklabels=['Normal','Alert'],yticklabels=['Normal','Fracture'],
        xlabel='Decision',ylabel='Reference',title=label+' confusion')
    axes[1].plot(curves['roc']['fpr'],curves['roc']['tpr'])
    axes[1].plot([0,1],[0,1],'--',color='gray')
    axes[1].set(xlabel='False-positive rate',ylabel='Sensitivity',title=label+' ROC',xlim=(0,1),ylim=(0,1))
    axes[2].plot(curves['precision_recall']['recall'],curves['precision_recall']['precision'])
    axes[2].set(xlabel='Recall',ylabel='Precision',title=label+' PR',xlim=(0,1),ylim=(0,1))
    fig.tight_layout();fig.savefig(out/(prefix+'_confusion_roc_pr.png'),dpi=150);plt.close(fig)
    bins = [b for b in calibration['reliability_curve'] if b['n']]
    fig, ax = plt.subplots(figsize=(6,5))
    ax.plot([0,1],[0,1],'--',color='gray')
    ax.scatter([b['mean_score'] for b in bins],[b['observed_fracture_fraction'] for b in bins],
        s=[20+150*b['n']/len(cases) for b in bins])
    ax.set(xlim=(0,1),ylim=(0,1),xlabel='Uncalibrated score',ylabel='Observed fracture fraction',
        title=label+' reliability diagnostic')
    fig.tight_layout();fig.savefig(out/(prefix+'_reliability.png'),dpi=150);plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--device',choices=['cpu','cuda'],default='cpu')
    args = ap.parse_args()
    run,out = Path(args.run).resolve(),Path(args.out).resolve()
    if ROOT not in run.parents or ROOT not in out.parents or out.exists():
        raise ValueError('Completed research run and exclusive workspace audit output required')
    state = json.loads((run/'state.json').read_text())
    config_run = json.loads((run/'config.json').read_text())
    bundle = json.loads((run/'bundle.json').read_text())
    if state['status']!='completed' or state['smoke'] or state['epochs_finished']!=12:
        raise ValueError('Full registered12-epoch pair arm required')
    if sha(MANIFEST)!=MANIFEST_SHA or bundle['manifest_sha256']!=MANIFEST_SHA:
        raise ValueError('Validation partition changed')
    if bundle['output_contract']!=CONTRACT or bundle['architecture']!=ARCHITECTURE:
        raise ValueError('Unknown research output contract')
    for source,digest in config_run['source_hashes'].items():
        if sha(ROOT/source)!=digest:
            raise ValueError('Registered training source changed: '+source)
    checkpoint = run/'best_model.pt'
    digest = sha(checkpoint)
    archive = ROOT/'FracAtlas.zip'
    if digest!=bundle['checkpoint_sha256'] or sha(archive)!=config_run['archive_sha256']:
        raise ValueError('Checkpoint/data identity differs')
    if args.device=='cuda' and not torch.cuda.is_available():
        raise ValueError('Requested CUDA unavailable')
    import matplotlib
    matplotlib.use('Agg')
    torch.set_num_threads(2);cv2.setNumThreads(1);p.seed_everything(42)
    preprocess = p.PreprocessConfig(**bundle['preprocess'])
    post = p.PostprocessConfig(**bundle['postprocess'])
    dataset = p.FracDataset(archive,MANIFEST,'val',preprocess)
    if len(dataset)!=463 or sum(int(r['fractured']) for r in dataset.rows)!=83:
        raise ValueError('Validation denominators changed')
    model = PresenceAttentionUNet().to(args.device)
    model.load_state_dict(torch.load(checkpoint,map_location=args.device,weights_only=True),strict=True)
    model.eval()
    supervised = bool(bundle['presence_weight'])
    manifest = json.loads(MANIFEST.read_text())
    sizes = [r['mask_pixels']/(r['width']*r['height']) for r in manifest['rows'] if r['split']=='train' and int(r['fractured'])]
    small_cutoff = float(np.quantile(sizes,.25))
    out.mkdir()
    for name in ('masks','failures','source_snapshot'):
        (out/name).mkdir()
    sources = list(config_run['source_hashes'])+['tools/audit_ai_presence_candidate.py','tools/ai_validation_audit.py','tools/evaluate_ai_baseline.py']
    for source in sources:
        (out/'source_snapshot'/Path(source).name).write_bytes((ROOT/source).read_bytes())
    config = dict(run=str(run.relative_to(ROOT)),epoch=bundle['epoch'],global_epoch=bundle['global_epoch'],
        output_contract=CONTRACT,architecture=ARCHITECTURE,presence_weight=bundle['presence_weight'],
        checkpoint_sha256=digest,manifest_sha256=MANIFEST_SHA,archive_sha256=config_run['archive_sha256'],
        preprocess=asdict(preprocess),postprocess=asdict(post),device=args.device,torch=torch.__version__,
        original_checkpoint_sha256=sha(ROOT/'best_model.pt'),source_hashes={s:sha(ROOT/s) for s in sources},
        scope='Full frozen463 VAL: independent masks, supervised head when enabled, conservative review union; no CAL/test/selection change',
        timing_context='CPU audit may overlap separate GPU training; not an isolated idle latency comparison',
        test_images_read=0,calibration_fit=False,promotion=False)
    save(out/'config.json',config);save(out/'split_audit.json',inspect_splits(manifest))
    masks,alerts,heads,cache,forward_ms,pipeline_ms = [],[],[],{},[],[]
    started = time.perf_counter()
    with torch.inference_mode():
        for i,row in enumerate(dataset.rows):
            begin = time.perf_counter()
            image,target = dataset.native(i)
            h,w = image.shape
            instances = [p.legacy._rasterize_coco_segmentation(dataset.annotations[aid]['segmentation'],w,h) for aid in row['annotation_ids']]
            x,_,_,geometry = p.prepare(image,preprocess)
            if args.device=='cuda': torch.cuda.synchronize()
            t0 = time.perf_counter()
            outputs = model(torch.from_numpy(x)[None,None].to(args.device))
            if not all(torch.isfinite(v).all() for v in outputs.values()):
                raise ValueError('Nonfinite audit outputs')
            grid = outputs['mask_logits'].sigmoid()[0,0].cpu().numpy()
            head_logit = float(outputs['presence_logits'][0]) if supervised else None
            head_score = float(outputs['presence_logits'].sigmoid()[0]) if supervised else None
            forward_ms.append((time.perf_counter()-t0)*1000)
            if grid.dtype!=np.float32 or not np.isfinite(grid).all():
                raise ValueError('Invalid native probability grid')
            native = p.inverse(grid,geometry,probability=True)
            _,mask = p.postprocess(native,post)
            pipeline_ms.append((time.perf_counter()-begin)*1000)
            case = inspect_case(row,image,target,mask,native,instances,small_cutoff)
            case,alert,head = combine_case(case,head_score,supervised)
            case['presence_logit'] = head_logit
            stem = Path(row['image_id']).stem
            for suffix,array in [('prediction',mask),('reference',target)]:
                if not cv2.imwrite(str(out/'masks'/f'{stem}_{suffix}.png'),array*255):
                    raise RuntimeError('Native mask write failed')
            if (case['category'] in ('FP','FN') or case['segmentation_failure_tags'] or
                alert['category'] in ('FP','FN') or supervised and
                (case['classifier_prediction_present']!=case['positive'] or case['classifier_prediction_present']!=case['prediction_present'])):
                filename = f"{case['category']}_{stem}.jpg"
                panel(image,target,mask,out/'failures'/filename,
                    f"{row['image_id']} mask{case['category']} alert{alert['category']} head={head_score} Dice={case['dice']}")
                case['review_panel'] = 'failures/'+filename
            cache[row['image_id']] = grid.copy()
            masks.append(case);alerts.append(dict(alert,presence_logit=head_logit))
            if head is not None: heads.append(dict(head,presence_logit=head_logit))
            if (i+1)%25==0:
                progress = dict(status='native_presence_audit',images=i+1,total=463,test_images_read=0)
                json_atomic(out/'progress.json', progress)
                print(json.dumps(progress),flush=True)
    timing = dict(forward_median_ms=float(np.median(forward_ms[1:])),forward_p95_ms=float(np.quantile(forward_ms[1:],.95)),
        pipeline_median_ms=float(np.median(pipeline_ms[1:])),full_inference_audit_seconds=time.perf_counter()-started,
        peak_process_rss_bytes=getattr(psutil.Process().memory_info(),'peak_wset',psutil.Process().memory_info().rss),
        context=config['timing_context'])
    result = summarize(masks,config,timing)
    result['mask_classification']=result['classification']
    result['mask_categories']=result['categories']
    result['classification']=a.classification(alerts)
    result['classification']['score_definition']='Conservative head+ OR mask+ review alerts; max uncalibrated head/mask proxy, not clinical probability' if supervised else 'Independent mask presence, maximum pixel proxy'
    result['categories']=dict(Counter(c['category'] for c in alerts))
    result['calibration']=a.calibration(alerts)
    result['calibration']['interpretation']='Uncalibrated review-score diagnostic; no clinical confidence claim'
    result['head_classification']=a.classification(heads) if supervised else None
    result['head_calibration']=a.calibration(heads) if supervised else None
    if supervised:
        result['head_classification']['score_definition']='Supervised balanced-BCE presence sigmoid, uncalibrated'
        result['head_calibration']['interpretation']='Learned presence raw sigmoid, TRAIN-weighted; no calibration fit'
    result['four_groups_by_truth']=dict(Counter(c['head_mask_group']+'|'+('fracture' if c['positive'] else 'normal') for c in masks))
    for flag,group in result['subgroups'].items():
        if group:
            if flag in masks[0]['flags']:
                ids={c['image_id'] for c in masks if c['flags'][flag]}
            elif flag=='small_region_proxy':
                ids={c['image_id'] for c in masks if c['small_region_proxy']}
            elif flag=='multiple_fractures':
                ids={c['image_id'] for c in masks if c['fracture_count']>1}
            else:
                raise ValueError('Unregistered subgroup: '+flag)
            group['mask_classification']=group['classification']
            group['mask_classification']['score_definition']=result['mask_classification']['score_definition']
            group['classification']=a.classification([c for c in alerts if c['image_id'] in ids])
            group['classification']['score_definition']=result['classification']['score_definition']
            group['head_classification']=a.classification([c for c in heads if c['image_id'] in ids]) if supervised else None
            if supervised:
                group['head_classification']['score_definition']=result['head_classification']['score_definition']
    cm=result['classification']['confusion_matrix']
    result['practical_classification_targets']['classification_counts_pass']=cm['tp']>=79 and cm['tn']>=342 and result['classification']['accuracy']>=.9
    result['mask_gated_by_classifier']=False
    result['small_region_definition']=dict(cutoff_fraction=small_cutoff,source='TRAIN25th percentile; not clinical subtlety')
    recorded=json.loads((run/'best_validation_cases.json').read_text())['delivered']
    by_id={c['image_id']:c for c in recorded}
    if set(by_id)!={c['image_id'] for c in masks}: raise ValueError('Trainer audit membership differs')
    keys=('tp_pixels','fp_pixels','fn_pixels','prediction_present','review_alert_present','classifier_prediction_present')
    differences=[dict(image_id=c['image_id'],audit={k:c[k] for k in keys},trainer={k:by_id[c['image_id']][k] for k in keys}) for c in masks if any(c[k]!=by_id[c['image_id']][k] for k in keys)]
    result['trainer_reproduction']=dict(differing_cases=differences,exact_counts=not differences,trainer_device=config_run['device'],audit_device=args.device,
        note='Boundary/device differences retained, never overwrite trainer evidence')
    save(out/'per_case.json',masks);save(out/'review_alert_cases.json',alerts);save(out/'head_cases.json',heads)
    np.savez_compressed(out/'probabilities_float32.npz',**cache)
    save(out/'metrics.json',result)
    write_csv(out/'failure_review.csv',[dict(image_id=c['image_id'],mask_category=c['category'],alert_category=c['review_alert_category'],
        head_mask_group=c['head_mask_group'],panel=c.get('review_panel',''),head_score=c['head_score'],mask_score=c['case_score'],
        dice=c['dice'],iou=c['iou'],tags=';'.join(c['segmentation_failure_tags']),clinical_cause='unadjudicated') for c in masks if c.get('review_panel')])
    plots(out,alerts,result['classification'],result['calibration'],'review_alert','Conservative review')
    if supervised: plots(out,heads,result['head_classification'],result['head_calibration'],'head','Presence head')
    (out/'VALIDATION_AUDIT.md').write_text('# Presence candidate native validation audit\n\nFull463 frozen cases. Primary classification is conservative review-alert burden; masks always remain independent. Head-only gains do not authorize promotion.\n\n'+json.dumps({k:result[k] for k in ['classification','head_classification','mask_classification','segmentation','mask_instance_localization','four_groups_by_truth']},indent=2)+'\n\nRaw confidence is uncalibrated. Localization AP is a component-box proxy, not canonical COCO detector mAP. Patient independence, clinical subtype labels, external generalization and radiologist adjudication remain unavailable. No CAL/test evaluation or promotion.\n')
    if sha(checkpoint)!=digest or sha(MANIFEST)!=MANIFEST_SHA or sha(ROOT/'best_model.pt')!=config['original_checkpoint_sha256']:
        raise RuntimeError('Protected audit inputs changed')
    save(out/'completion.json',dict(status='completed',metrics_sha256=sha(out/'metrics.json'),cases_sha256=sha(out/'per_case.json'),
        checkpoint_sha256=digest,independent_masks=True,calibration_fit=False,test_images_read=0,promotion=False))
    print(json.dumps(dict(classification=result['classification'],head=result['head_classification'],segmentation=result['segmentation']),indent=2),flush=True)


if __name__=='__main__':
    main()
