"""Matched reliability candidates; prospective calibration excluded from training/selection.

Derived from the preserved train_pipeline.py. Only the normal-image BCE factor
varies between registered experiments. No test inference or model promotion.
"""
import argparse
import hashlib
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

import cv2
import numpy as np
import numpy as np
import psutil
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import medvision_pipeline as p
from tools.run_experiment import summary
from tools.ai_metrics import classification


class ReliabilityDataset(p.FracDataset):
    """Preserve positive label visibility and carry explicit case labels."""
    def __getitem__(self, index):
        image, mask = self.native(index)
        x, y, valid, _ = p.prepare(image, self.config, mask)
        positive = bool(int(self.rows[index]['fractured']))
        if self.training:
            seed = np.random.SeedSequence([self.seed, self.epoch, index]).generate_state(1)[0]
            ax, ay, av = p.augment(x, y, valid, int(seed), self.elastic)
            # A measured epoch9 rotation completely erased IMG0002386's target.
            # Retain the unaugmented aligned pair rather than a false normal.
            if not positive or bool(ay.any()):
                x, y, valid = ax, ay, av
        if positive != bool(y.any()):
            raise ValueError('Preprocessing/augmentation lost the case label')
        return (*[torch.from_numpy(a.copy()).unsqueeze(0) for a in (x, y, valid)], torch.tensor(positive))


def candidate_loss(logits, target, valid, config, normal_bce_weight, positive=None):
    components = p.loss_components(logits, target, valid, config)
    # Per-image penalty: retain the same positive loss and Dice; strengthen only
    # BCE on explicitly empty normal masks. Keep natural sampling unchanged.
    dims = (1, 2, 3)
    normal = (target.sum(dims) == 0).to(logits.dtype) if positive is None else (~positive).to(logits.dtype)
    per_image_bce = (F.binary_cross_entropy_with_logits(logits, target, reduction='none')*valid).sum(dims)/valid.sum(dims)
    offset = ((normal_bce_weight-1)*normal*per_image_bce).mean()
    components['normal_bce_offset'] = offset
    components['weighted_bce'] = components['bce']+offset
    components['total'] = components['total']+offset
    return components


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
        probability,raw,delivered,_ = p.predict_arrays(model,image,preprocess,post,device)
        raw_cases.append(dict(case_counts(row,raw,target),case_score=float(probability.max())))
        delivered_cases.append(dict(case_counts(row,delivered,target),case_score=float(probability.max())))
    return {'raw':summary(raw_cases),'delivered':summary(delivered_cases),'classification':dict(classification(delivered_cases),score_definition='maximum native bilinear inverse sigmoid output; uncalibrated case-score proxy')}, {'raw':raw_cases,'delivered':delivered_cases}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out',required=True)
    ap.add_argument('--manifest',default='experiments/data_v3_reliability_20261007/manifest.json')
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
    ap.add_argument('--normal-bce-weight',type=float,default=1.)
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
    if not 1 <= args.normal_bce_weight <= 4 or args.loss != 'bce_dice' or args.positive_fraction is not None:
        raise ValueError('Registered ablation requires BCE+Dice, natural sampling, normal BCE weight in [1,4]')
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
    if not manifest.get('calibration_partition_protocol') or not any(r['split']=='calibration' for r in manifest['rows']):
        raise ValueError('Prospectively frozen calibration partition required')
    if p.sha(args.archive) != manifest['archive_sha256']:
        raise ValueError('Archive no longer matches manifest')
    sources = ['medvision_pipeline.py','medvision_ai.py','tools/train_reliability_candidate.py','tools/run_experiment.py','tools/ai_metrics.py']
    config = dict(vars(args),preprocess=asdict(preprocess),loss_config=asdict(loss_config),
                  postprocess=asdict(post),output_contract=p.CONTRACT,architecture='AttentionUNet64',
                  manifest_sha256=p.sha(args.manifest),archive_sha256=p.sha(args.archive),
                  original_checkpoint_sha256=p.sha(root/'best_model.pt'),
                  source_hashes={s:p.sha(root/s) for s in sources},torch=torch.__version__,
                  sampling='natural shuffle' if args.positive_fraction is None else 'weighted replacement, training only',
                  selection='0.4 native positive Dice + 0.3 image sensitivity + 0.3 image specificity on validation at .5/all; earlier ties. No accuracy-only selection. Calibration and test excluded.',
                  augmentation_guard='Explicit case label retained; if rotation erases entire positive target, retain unaugmented pair. Same rule in both matched runs.',
                  determinism='strict torch algorithms; epoch-seeded shuffle/sampler; local per-epoch/per-index augmentation RNG; no cross-version/device identity guarantee')
    torch.set_num_threads(2)
    cv2.setNumThreads(1)
    p.seed_everything(args.seed)
    train = ReliabilityDataset(args.archive,args.manifest,'train',preprocess,True,args.seed,args.elastic)
    val = p.FracDataset(args.archive,args.manifest,'val',preprocess)
    if args.smoke:
        for ds in (train,val):
            ds.rows = [r for label in (1,0) for r in [r for r in ds.rows if int(r['fractured'])==label][:2]]
    model = p.LogitsAttentionUNet().to(args.device)
    initial_digest = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        initial_digest.update(name.encode())
        initial_digest.update(str(tensor.dtype).encode())
        initial_digest.update(str(tuple(tensor.shape)).encode())
        initial_digest.update(tensor.detach().cpu().numpy().tobytes())
    optimizer = torch.optim.Adam(model.parameters(),lr=args.lr)
    first,best,stale = 1,-1.,0
    if args.resume:
        old = json.loads((out/'config.json').read_text(encoding='utf-8'))
        for key in ('manifest_sha256','archive_sha256','preprocess','loss_config','postprocess','batch_size','lr','seed','elastic','positive_fraction','normal_bce_weight','source_hashes','smoke','device'):
            if old[key] != config[key]:
                raise ValueError(f'Resume config changed: {key}')
        ck = torch.load(out/'last.pt',map_location=args.device,weights_only=True)
        if ck['output_contract'] != p.CONTRACT:
            raise ValueError('Checkpoint output contract mismatch')
        model.load_state_dict(ck['model_state_dict'],strict=True)
        optimizer.load_state_dict(ck['optimizer_state_dict'])
        first,best,stale = ck['epoch']+1,ck['best_validation_score'],ck['stale_epochs']
    else:
        out.mkdir(parents=True)
        (out/'config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
        (out/'source_snapshot').mkdir()
        for source in sources:
            (out/'source_snapshot'/Path(source).name).write_bytes((root/source).read_bytes())
        (out/'initial_parameters.json').write_text(json.dumps(dict(seed=args.seed,parameter_sha256=initial_digest.hexdigest(),
            rule='Sorted state names, dtype, shape and tensor bytes; both matched runs must agree'),indent=2))
        atomic_save(dict(model_state_dict=model.state_dict(),optimizer_state_dict=optimizer.state_dict(),epoch=0,
                         best_validation_score=best,stale_epochs=stale,output_contract=p.CONTRACT),out/'last.pt')
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
        for batch,(x,y,valid,positive) in enumerate(loader,1):
            x,y,valid = [v.to(args.device) for v in (x,y,valid)]
            positive = positive.to(args.device)
            optimizer.zero_grad(set_to_none=True)
            components = candidate_loss(model(x),y,valid,loss_config,args.normal_bce_weight,positive)
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
        score = .4*metrics['delivered']['mean_positive_dice']+.3*metrics['classification']['recall_sensitivity']+.3*metrics['classification']['specificity']
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
                         best_validation_score=best,stale_epochs=stale,output_contract=p.CONTRACT,
                         manifest_sha256=config['manifest_sha256']),out/'last.pt')
        record = dict(epoch=epoch,lr=optimizer.param_groups[0]['lr'],loss_components={k:v/seen for k,v in sums.items()},
                      valid_foreground_fraction=foreground/valid_pixels,augmented_nonempty_fraction=seen_positive/seen,
                      requested_positive_fraction=args.positive_fraction,normal_bce_weight=args.normal_bce_weight,validation=metrics,epoch_seconds=time.perf_counter()-ep_start,
                      peak_process_rss_bytes=getattr(psutil.Process().memory_info(),'peak_wset',psutil.Process().memory_info().rss),
                      best_validation_score=best,stale_epochs=stale,device=args.device,torch=torch.__version__,smoke=args.smoke)
        with (out/'epochs.jsonl').open('a') as f:
            f.write(json.dumps(record)+'\n')
        print(json.dumps(record),flush=True)
        completed = epoch
        if p.sha(root/'best_model.pt') != config['original_checkpoint_sha256']:
            raise RuntimeError('Protected historical checkpoint changed')
    (out/'state.json').write_text(json.dumps(dict(status='completed',epochs_finished=completed,best_validation_score=best,
                                                elapsed_seconds=time.perf_counter()-started,smoke=args.smoke,test_evaluated=False),indent=2))


if __name__=='__main__':
    main()
