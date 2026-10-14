"""Safe evaluation-only and learning-sanity entry points with immutable run output."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import zipfile

import cv2
import numpy as np
import psutil
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import medvision_ai as m


def sha(path):
    with open(path,'rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def policy_mask(prob, threshold, policy):
    binary = (prob >= threshold).astype(np.uint8)
    if policy == 'all':
        return m.assess_severity(binary)[0]
    n, labels, stats, _ = cv2.connectedComponentsWithStats(binary,8)
    if n <= 1:
        return binary
    if policy == 'largest':
        return (labels == (1+np.argmax(stats[1:,cv2.CC_STAT_AREA]))).astype(np.uint8)
    keep = np.where(stats[:,cv2.CC_STAT_AREA] >= 16)[0]
    keep = keep[keep != 0]
    return np.isin(labels,keep).astype(np.uint8)


def native_pair(z, row, annotation_index):
    image = m._decode_image_bytes(z.read(row['member']))
    h,w = image.shape
    gt = np.zeros((h,w),np.uint8)
    for aid in row['annotation_ids']:
        gt |= m._rasterize_coco_segmentation(annotation_index[aid]['segmentation'],w,h)
    return image,gt


def summary(cases):
    positives = [c for c in cases if c['positive']]
    normals = [c for c in cases if not c['positive']]
    tp = sum(c['tp_pixels'] for c in cases)
    fp = sum(c['fp_pixels'] for c in cases)
    fn = sum(c['fn_pixels'] for c in cases)
    values = np.array([c['dice'] for c in positives])
    rng = np.random.default_rng(42)
    # Group resampling rather than falsely asserting independent patients.
    groups = {}
    for c in positives:
        groups.setdefault(c['group'],[]).append(c['dice'])
    gs = list(groups.values())
    boot = [np.mean([v for idx in rng.integers(0,len(gs),len(gs)) for v in gs[idx]]) for _ in range(1000)] if gs else []
    return {'n_positive':len(positives),'n_normal':len(normals),
            'mean_positive_dice':float(values.mean()) if len(values) else None,
            'median_positive_dice':float(np.median(values)) if len(values) else None,
            'positive_dice_group_bootstrap95':np.quantile(boot,[.025,.975]).tolist() if boot else None,
            'mean_positive_iou':float(np.mean([c['iou'] for c in positives])) if positives else None,
            'case_sensitivity':sum(c['prediction_present'] for c in positives)/len(positives) if positives else None,
            'normal_false_positive_rate':sum(c['prediction_present'] for c in normals)/len(normals) if normals else None,
            'case_true_positive':sum(c['prediction_present'] for c in positives),
            'case_false_negative':sum(not c['prediction_present'] for c in positives),
            'case_false_positive':sum(c['prediction_present'] for c in normals),
            'case_true_negative':sum(not c['prediction_present'] for c in normals),
            'global_dice':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,
            'global_iou':tp/(tp+fp+fn) if tp+fp+fn else None,
            'pixel_precision':tp/(tp+fp) if tp+fp else None,
            'pixel_recall':tp/(tp+fn) if tp+fn else None,
            'mean_regions_per_normal':float(np.mean([c['components'] for c in normals])) if normals else None}


def evaluate(args, config, out, rows, annotations):
    if args.split == 'test' and not args.final_test:
        raise ValueError('Test access requires --final-test after freezing the selected model/config.')
    selected = [r for r in rows if r['split']==args.split]
    if args.limit:
        selected = selected[:args.limit]
    model = m.AttentionUNet().to(m.DEVICE)
    m._load_model_weights(model,args.checkpoint)
    model.eval()
    thresholds = [round(x*.05,2) for x in range(1,20)]
    policies = ['all','largest','min16']
    cases = {(t,p):[] for t in thresholds for p in policies}
    latencies = []
    arrays = {}
    with zipfile.ZipFile(args.archive) as z, torch.inference_mode():
        for idx,row in enumerate(selected):
            image,gt = native_pair(z,row,annotations)
            processed = m.preprocess_image_array(image)
            x = m._ensure_4d_tensor(processed).to(m.DEVICE)
            if m.DEVICE.type=='cuda':
                torch.cuda.synchronize()
            start = time.perf_counter()
            prob = model(x)[0,0].cpu().numpy()
            latencies.append((time.perf_counter()-start)*1000)
            assert prob.shape == (256,256) and np.isfinite(prob).all()
            arrays[row['image_id']] = prob.astype(np.float16)
            for t in thresholds:
                for p in policies:
                    mask256 = policy_mask(prob,t,p)
                    pred = cv2.resize(mask256,(image.shape[1],image.shape[0]),interpolation=cv2.INTER_NEAREST).astype(bool)
                    target = gt.astype(bool)
                    tp = int(np.count_nonzero(pred & target))
                    fp = int(np.count_nonzero(pred & ~target))
                    fn = int(np.count_nonzero(~pred & target))
                    positive = bool(int(row['fractured']))
                    c = {'image_id':row['image_id'],'group':row['group'],'positive':positive,
                         'prediction_present':bool(pred.any()),'tp_pixels':tp,'fp_pixels':fp,'fn_pixels':fn,
                         'dice':2*tp/(2*tp+fp+fn) if positive else None,
                         'iou':tp/(tp+fp+fn) if positive else None,
                         'components':int(cv2.connectedComponents(mask256,connectivity=8)[0]-1)}
                    cases[t,p].append(c)
            if idx in [0,1,2,3,4,5]:
                image_path = out/f'example_{row["image_id"]}'
                cv2.imwrite(str(image_path),image)
                m.create_overlay(str(image_path),policy_mask(prob,.9,'all'),str(out/f'overlay_{row["image_id"]}.png'),'prediction')
                cv2.imwrite(str(out/f'ground_truth_{row["image_id"]}.png'),gt*255)
            if (idx+1)%25==0:
                print(f'evaluated {idx+1}/{len(selected)}; forward {np.median(latencies):.1f} ms',flush=True)
    table = [{'threshold':t,'policy':p,**summary(cc)} for (t,p),cc in cases.items()]
    (out/'comparison.json').write_text(json.dumps(table,indent=2))
    # Select against corrected historical baseline solely on validation.
    baseline = next(r for r in table if r['threshold']==.9 and r['policy']=='all')
    qualifying = [r for r in table if r['case_sensitivity'] >= baseline['case_sensitivity']-.02 and r['normal_false_positive_rate'] <= baseline['normal_false_positive_rate']+.02]
    winner = max(qualifying,key=lambda r:(r['mean_positive_dice'],-r['threshold']))
    result = {'scope':'historical checkpoint diagnostic; unknown prior exposure; no independent test claim',
              'split':args.split,'baseline':baseline,'validation_selected':winner,
              'forward_latency_ms':{'median':float(np.median(latencies[1:])), 'p95':float(np.quantile(latencies[1:],.95)), 'first':latencies[0]},
              'elapsed_seconds':time.perf_counter()-config['started_monotonic'], 'peak_process_rss_bytes':psutil.Process().memory_info().peak_wset,
              'checkpoint_sha256':sha(args.checkpoint),'manifest_sha256':config['manifest_sha256']}
    (out/'metrics.json').write_text(json.dumps(result,indent=2))
    (out/'per_case.json').write_text(json.dumps([{'threshold':t,'policy':p,'cases':cc} for (t,p),cc in cases.items()],indent=2))
    np.savez_compressed(out/'probabilities_float16.npz',**arrays)
    print(json.dumps(result,indent=2),flush=True)


def learning_sanity(args, config, out, rows, annotations):
    training = [r for r in rows if r['split']=='train']
    pair = [next(r for r in training if int(r['fractured'])==v) for v in [1,0]]
    xs,ys = [],[]
    with zipfile.ZipFile(args.archive) as z:
        for r in pair:
            image,gt = native_pair(z,r,annotations)
            xs.append(m.preprocess_image_array(image))
            ys.append(cv2.resize(gt,(256,256),interpolation=cv2.INTER_NEAREST))
    x = torch.from_numpy(np.array(xs)[:,None]).float().to(m.DEVICE)
    y = torch.from_numpy(np.array(ys)[:,None]).float().to(m.DEVICE)
    model = m.AttentionUNet().to(m.DEVICE)
    optimizer = torch.optim.Adam(model.parameters(),lr=1e-4)
    logs = []
    for step in range(args.steps):
        start = time.perf_counter()
        optimizer.zero_grad(set_to_none=True)
        probability = model(x)
        # Numerically stable BCE from probabilities is retained for checkpoint
        # compatibility; logits-based new training is a separate experiment.
        loss = torch.nn.functional.binary_cross_entropy(probability.clamp(1e-6,1-1e-6),y)+m.dice_loss(probability,y)
        assert torch.isfinite(loss)
        loss.backward()
        assert all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None)
        optimizer.step()
        log = {'step':step+1,'bce_plus_dice':float(loss.detach()),'seconds':time.perf_counter()-start}
        logs.append(log)
        print(json.dumps(log),flush=True)
    result = {'scope':'two-training-image learning sanity, not validation/test performance', 'sample_ids':[r['image_id'] for r in pair],
              'steps':logs,'median_step_seconds':float(np.median([r['seconds'] for r in logs[1:]])),
              'peak_process_rss_bytes':psutil.Process().memory_info().peak_wset,
              'estimated_full_epoch_seconds':float(np.median([r['seconds'] for r in logs[1:]]))*len(training)/2}
    (out/'metrics.json').write_text(json.dumps(result,indent=2))
    torch.save(model.state_dict(),out/'sanity_model.pt')
    print(json.dumps(result,indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode',choices=['evaluate','learning-sanity'])
    parser.add_argument('--archive',default='FracAtlas.zip')
    parser.add_argument('--manifest',default='experiments/data_v1/manifest.json')
    parser.add_argument('--checkpoint',default='best_model.pt')
    parser.add_argument('--out',required=True)
    parser.add_argument('--split',choices=['val','test'],default='val')
    parser.add_argument('--final-test',action='store_true')
    parser.add_argument('--limit',type=int)
    parser.add_argument('--steps',type=int,default=12)
    args = parser.parse_args()
    out = Path(args.out)
    if out.exists():
        raise SystemExit('Run output exists; use a new run ID.')
    manifest = json.loads(Path(args.manifest).read_text())
    assert sha(args.archive)==manifest['archive_sha256'], 'Archive changed since audit'
    out.mkdir(parents=True)
    m.set_seed(42)
    torch.set_num_threads(4)
    config = dict(vars(args),seed=42,threads=4,python=sys.version,torch=torch.__version__,device=str(m.DEVICE),platform=platform.platform(),
                  manifest_sha256=sha(args.manifest),checkpoint_sha256=sha(args.checkpoint),code_sha256=sha(__file__),
                  started_monotonic=time.perf_counter(),cpu=platform.processor())
    (out/'config.json').write_text(json.dumps(config,indent=2))
    with zipfile.ZipFile(args.archive) as z:
        annotations = {a['id']:a for a in json.loads(z.read('FracAtlas/Annotations/COCO JSON/COCO_fracture_masks.json'))['annotations']}
    if args.mode=='evaluate':
        evaluate(args,config,out,manifest['rows'],annotations)
    else:
        learning_sanity(args,config,out,manifest['rows'],annotations)
    assert sha(args.checkpoint)==config['checkpoint_sha256'], 'Input checkpoint changed'


if __name__=='__main__':
    main()
