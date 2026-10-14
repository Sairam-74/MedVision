"""New-run/resumable training for binary-logits-v2; validation only, never test."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

import cv2
import numpy as np
import psutil
import torch
from torch.utils.data import DataLoader

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import medvision_pipeline as p
from tools.run_experiment import summary


def atomic_save(data,path):
    temporary = path.with_suffix('.tmp')
    torch.save(data,temporary)
    temporary.replace(path)


def case_counts(row, mask, target):
    mask,target = mask.astype(bool),target.astype(bool)
    tp,fp,fn = [int(v.sum()) for v in (mask&target,mask&~target,~mask&target)]
    positive = bool(int(row['fractured']))
    return dict(image_id=row['image_id'],group=row['group'],positive=positive,
                prediction_present=bool(mask.any()),tp_pixels=tp,fp_pixels=fp,fn_pixels=fn,
                dice=2*tp/(2*tp+fp+fn) if positive else None,
                iou=tp/(tp+fp+fn) if positive else None,
                components=int(cv2.connectedComponents(mask.astype(np.uint8),8)[0]-1))


def validate(model,dataset,preprocess,post,device):
    raw_cases,delivered_cases = [],[]
    for i,row in enumerate(dataset.rows):
        image,target = dataset.native(i)
        _,raw,delivered,_ = p.predict_arrays(model,image,preprocess,post,device)
        raw_cases.append(case_counts(row,raw,target))
        delivered_cases.append(case_counts(row,delivered,target))
    return {'raw':summary(raw_cases),'delivered':summary(delivered_cases)}, {'raw':raw_cases,'delivered':delivered_cases}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out',required=True)
    ap.add_argument('--manifest',default='experiments/data_v2/manifest.json')
    ap.add_argument('--archive',default='FracAtlas.zip')
    ap.add_argument('--epochs',type=int,default=12)
    ap.add_argument('--batch-size',type=int,default=2)
    ap.add_argument('--lr',type=float,default=1e-4)
    ap.add_argument('--size',type=int,default=256)
    ap.add_argument('--resize',choices=['letterbox','stretch'],default='letterbox')
    ap.add_argument('--no-clahe',action='store_true')
    ap.add_argument('--blur',type=int,default=0)
    ap.add_argument('--normalization',choices=['unit','zscore'],default='unit')
    ap.add_argument('--loss',choices=['bce_dice','focal_tversky','unified_focal_symmetric'],default='bce_dice')
    ap.add_argument('--positive-fraction',type=float,default=None)
    ap.add_argument('--elastic',action='store_true')
    ap.add_argument('--seed',type=int,default=42)
    ap.add_argument('--patience',type=int,default=5)
    ap.add_argument('--device',choices=['cpu','cuda'],default='cpu')
    ap.add_argument('--smoke',action='store_true')
    ap.add_argument('--resume',action='store_true')
    args = ap.parse_args()
    if args.epochs < 1 or args.batch_size < 1 or args.lr <= 0 or args.patience < 1:
        raise ValueError('Invalid training budget')
    if args.device=='cuda' and not torch.cuda.is_available():
        raise RuntimeError('Requested CUDA is unavailable; do not silently substitute')
    root = Path(__file__).resolve().parents[1]
    out = Path(args.out).resolve()
    if root not in out.parents or out==root or out.exists() and not args.resume:
        raise ValueError('Use a new workspace run directory or --resume')
    preprocess = p.PreprocessConfig(args.size,args.resize,not args.no_clahe,blur_kernel=args.blur,normalization=args.normalization)
    loss_config = p.LossConfig(mode=args.loss)
    post = p.PostprocessConfig()
    manifest = json.loads(Path(args.manifest).read_text(encoding='utf-8'))
    if p.sha(args.archive) != manifest['archive_sha256']:
        raise ValueError('Archive no longer matches manifest')
    sources = ['medvision_pipeline.py','medvision_ai.py','tools/train_pipeline.py','tools/run_experiment.py']
    config = dict(vars(args),preprocess=asdict(preprocess),loss_config=asdict(loss_config),
                  postprocess=asdict(post),output_contract=p.CONTRACT,architecture='AttentionUNet64',
                  manifest_sha256=p.sha(args.manifest),archive_sha256=p.sha(args.archive),
                  original_checkpoint_sha256=p.sha(root/'best_model.pt'),
                  source_hashes={s:p.sha(root/s) for s in sources},torch=torch.__version__,
                  sampling='natural shuffle' if args.positive_fraction is None else 'weighted replacement, training only',
                  selection='native positive delivered Dice on validation; threshold .5/all; earlier ties',
                  determinism='strict torch algorithms; epoch-seeded shuffle/sampler; local per-epoch/per-index augmentation RNG; no cross-version/device identity guarantee')
    torch.set_num_threads(2)
    cv2.setNumThreads(1)
    p.seed_everything(args.seed)
    train = p.FracDataset(args.archive,args.manifest,'train',preprocess,True,args.seed,args.elastic)
    val = p.FracDataset(args.archive,args.manifest,'val',preprocess)
    if args.smoke:
        for ds in (train,val):
            ds.rows = [r for label in (1,0) for r in [r for r in ds.rows if int(r['fractured'])==label][:2]]
    model = p.LogitsAttentionUNet().to(args.device)
    optimizer = torch.optim.Adam(model.parameters(),lr=args.lr)
    first,best,stale = 1,-1.,0
    if args.resume:
        old = json.loads((out/'config.json').read_text(encoding='utf-8'))
        for key in ('manifest_sha256','archive_sha256','preprocess','loss_config','postprocess','batch_size','lr','seed','elastic','positive_fraction','source_hashes','smoke','device'):
            if old[key] != config[key]:
                raise ValueError(f'Resume config changed: {key}')
        ck = torch.load(out/'last.pt',map_location=args.device,weights_only=True)
        if ck['output_contract'] != p.CONTRACT:
            raise ValueError('Checkpoint output contract mismatch')
        model.load_state_dict(ck['model_state_dict'],strict=True)
        optimizer.load_state_dict(ck['optimizer_state_dict'])
        first,best,stale = ck['epoch']+1,ck['best_validation_dice'],ck['stale_epochs']
    else:
        out.mkdir(parents=True)
        (out/'config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
        (out/'source_snapshot').mkdir()
        for source in sources:
            (out/'source_snapshot'/Path(source).name).write_bytes((root/source).read_bytes())
        atomic_save(dict(model_state_dict=model.state_dict(),optimizer_state_dict=optimizer.state_dict(),epoch=0,
                         best_validation_dice=best,stale_epochs=stale,output_contract=p.CONTRACT),out/'last.pt')
    started = time.perf_counter()
    completed = first-1
    for epoch in range(first,args.epochs+1):
        if stale >= args.patience:
            break
        p.seed_everything(args.seed+epoch)
        train.epoch = epoch
        sampler = None if args.positive_fraction is None else train.sampler(args.positive_fraction,epoch)
        loader = DataLoader(train,batch_size=args.batch_size,shuffle=sampler is None,sampler=sampler,num_workers=0,
                            generator=torch.Generator().manual_seed(args.seed+epoch))
        model.train()
        sums,seen,foreground,valid_pixels,seen_positive = {},0,0.,0.,0
        ep_start = time.perf_counter()
        for batch,(x,y,valid) in enumerate(loader,1):
            x,y,valid = [v.to(args.device) for v in (x,y,valid)]
            optimizer.zero_grad(set_to_none=True)
            components = p.loss_components(model(x),y,valid,loss_config)
            if not all(torch.isfinite(v) for v in components.values()):
                raise RuntimeError('Nonfinite loss component')
            components['total'].backward()
            grad = torch.nn.utils.clip_grad_norm_(model.parameters(),10,error_if_nonfinite=True)
            optimizer.step()
            for key,value in components.items():
                sums[key] = sums.get(key,0.)+float(value.detach())*len(x)
            seen += len(x)
            foreground += float((y*valid).sum())
            valid_pixels += float(valid.sum())
            seen_positive += int((y.flatten(1).sum(1)>0).sum())
            if batch==1 or batch%100==0 or batch==len(loader):
                state = dict(status='training',epoch=epoch,batch=batch,batches=len(loader),
                             loss_components={k:v/seen for k,v in sums.items()},gradient_norm=float(grad),
                             elapsed_seconds=time.perf_counter()-ep_start,test_evaluated=False,smoke=args.smoke)
                (out/'state.json').write_text(json.dumps(state,indent=2))
                print(json.dumps(state),flush=True)
        metrics,cases = validate(model,val,preprocess,post,args.device)
        score = metrics['delivered']['mean_positive_dice']
        if score > best:
            best,stale = score,0
            atomic_save(model.state_dict(),out/'best_model.pt')
            (out/'best_validation_cases.json').write_text(json.dumps(cases,indent=2))
            (out/'best_validation.json').write_text(json.dumps(dict(epoch=epoch,metrics=metrics),indent=2))
            bundle = dict(output_contract=p.CONTRACT,architecture='AttentionUNet64',checkpoint='best_model.pt',
                          checkpoint_sha256=p.sha(out/'best_model.pt'),preprocess=asdict(preprocess),postprocess=asdict(post),
                          manifest_sha256=config['manifest_sha256'],epoch=epoch,
                          calibration_status='UNSELECTED research checkpoint; default .5/all; smoke only' if args.smoke else 'UNSELECTED validation checkpoint; calibration and bundle freeze pending')
            (out/'bundle.json').write_text(json.dumps(bundle,indent=2))
        else:
            stale += 1
        atomic_save(dict(model_state_dict=model.state_dict(),optimizer_state_dict=optimizer.state_dict(),epoch=epoch,
                         best_validation_dice=best,stale_epochs=stale,output_contract=p.CONTRACT,
                         manifest_sha256=config['manifest_sha256']),out/'last.pt')
        record = dict(epoch=epoch,lr=optimizer.param_groups[0]['lr'],loss_components={k:v/seen for k,v in sums.items()},
                      valid_foreground_fraction=foreground/valid_pixels,augmented_nonempty_fraction=seen_positive/seen,
                      requested_positive_fraction=args.positive_fraction,validation=metrics,epoch_seconds=time.perf_counter()-ep_start,
                      peak_process_rss_bytes=getattr(psutil.Process().memory_info(),'peak_wset',psutil.Process().memory_info().rss),
                      best_validation_dice=best,stale_epochs=stale,device=args.device,torch=torch.__version__,smoke=args.smoke)
        with (out/'epochs.jsonl').open('a') as f:
            f.write(json.dumps(record)+'\n')
        print(json.dumps(record),flush=True)
        completed = epoch
        if p.sha(root/'best_model.pt') != config['original_checkpoint_sha256']:
            raise RuntimeError('Protected historical checkpoint changed')
    (out/'state.json').write_text(json.dumps(dict(status='completed',epochs_finished=completed,best_validation_dice=best,
                                                elapsed_seconds=time.perf_counter()-started,smoke=args.smoke,test_evaluated=False),indent=2))


if __name__=='__main__':
    main()
