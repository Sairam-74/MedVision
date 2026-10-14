"""Resumable normal-inclusive training with native validation; no test access."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
import time
import zipfile

import cv2
import numpy as np
import psutil
import torch
from torch.utils.data import DataLoader, Subset

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import medvision_ai as m
from tools.run_experiment import native_pair, policy_mask, summary


def sha(path):
    with open(path,'rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def save_atomic(payload,path):
    temporary = path.with_suffix('.tmp')
    torch.save(payload,temporary)
    temporary.replace(path)


def validate(model, rows, annotations, archive):
    model.eval()
    cases = []
    with zipfile.ZipFile(archive) as z, torch.inference_mode():
        for row in rows:
            image,gt = native_pair(z,row,annotations)
            x = m._ensure_4d_tensor(m.preprocess_image_array(image)).to(m.DEVICE)
            prob = model(x)[0,0].cpu().numpy()
            assert np.isfinite(prob).all()
            mask = policy_mask(prob,.5,'all')
            pred = cv2.resize(mask,(image.shape[1],image.shape[0]),interpolation=cv2.INTER_NEAREST).astype(bool)
            target = gt.astype(bool)
            tp = int(np.count_nonzero(pred & target))
            fp = int(np.count_nonzero(pred & ~target))
            fn = int(np.count_nonzero(~pred & target))
            positive = bool(int(row['fractured']))
            cases.append({'image_id':row['image_id'],'group':row['group'],'positive':positive,
                          'prediction_present':bool(pred.any()),'tp_pixels':tp,'fp_pixels':fp,'fn_pixels':fn,
                          'dice':2*tp/(2*tp+fp+fn) if positive else None,
                          'iou':tp/(tp+fp+fn) if positive else None,
                          'components':int(cv2.connectedComponents(mask,connectivity=8)[0]-1)})
    return summary(cases),cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out',required=True)
    parser.add_argument('--archive',default='FracAtlas.zip')
    parser.add_argument('--manifest',default='experiments/data_v1/manifest.json')
    parser.add_argument('--epochs',type=int,default=12)
    parser.add_argument('--batch-size',type=int,default=2)
    parser.add_argument('--lr',type=float,default=1e-4)
    parser.add_argument('--loss',choices=['bce_dice','focal_tversky'],default='bce_dice')
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--patience',type=int,default=5)
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--smoke',action='store_true',help='Four train/four val cases; not performance evidence.')
    args = parser.parse_args()
    torch.set_num_threads(4)
    cv2.setNumThreads(1)
    m.set_seed(args.seed)
    out = Path(args.out).resolve()
    protected = Path('best_model.pt').resolve()
    if out == protected.parent or protected.parent not in out.parents:
        raise ValueError('Use a new run directory inside the project workspace.')
    manifest = json.loads(Path(args.manifest).read_text())
    archive_hash = sha(args.archive)
    assert archive_hash==manifest['archive_sha256']
    config = dict(vars(args),architecture='AttentionUNet64',output_contract='sigmoid-probabilities-v1',
                  preprocessing='CLAHE2/8x8+Gaussian3x3; stretch256; normalize255',augmentation='horizontal flip .5; rotate +-15 deg .5; no elastic',
                  sampling='natural prevalence, shuffle training only',selection='native-coordinate mean positive validation Dice at .5; earlier epoch tie',
                  manifest_sha256=sha(args.manifest),archive_sha256=archive_hash,original_checkpoint_sha256=sha(protected),
                  source_sha256=sha(__file__),medvision_source_sha256=sha('medvision_ai.py'),torch=torch.__version__,device=str(m.DEVICE),threads=4)
    first_epoch,best,stale = 1,-1.0,0
    if out.exists() and not args.resume:
        raise ValueError('Run directory exists; choose a new ID or explicitly --resume.')
    out.mkdir(parents=True,exist_ok=True)
    if args.resume:
        old = json.loads((out/'config.json').read_text())
        for key in ['loss','seed','batch_size','lr','manifest_sha256','archive_sha256','source_sha256','medvision_source_sha256','smoke']:
            assert old[key]==config[key],f'Resume config mismatch: {key}'
        if old['device'] != str(m.DEVICE) or old['torch'] != torch.__version__:
            print('Resume changes compute environment; recorded in epoch logs.',flush=True)
    else:
        (out/'config.json').write_text(json.dumps(config,indent=2))
        (out/'source_snapshot').mkdir()
        for source in ['medvision_ai.py','tools/train_baseline.py','tools/run_experiment.py','requirements.txt']:
            (out/'source_snapshot'/Path(source).name).write_bytes(Path(source).read_bytes())
    dataset = m.FracAtlasZipDataset(args.archive)
    assert {r['image_id'] for r in dataset.image_records}=={r['image_id'] for r in manifest['rows']}
    indices = [i for i,r in enumerate(dataset.image_records) if r['split']=='train']
    val_rows = [r for r in manifest['rows'] if r['split']=='val']
    if args.smoke:
        indices = [i for label in [1,0] for i in [j for j in indices if int(dataset.image_records[j]['fractured'])==label][:2]]
        val_rows = [r for label in [1,0] for r in [v for v in val_rows if int(v['fractured'])==label][:2]]
    with zipfile.ZipFile(args.archive) as z:
        annotations = {a['id']:a for a in json.loads(z.read('FracAtlas/Annotations/COCO JSON/COCO_fracture_masks.json'))['annotations']}
    model = m.AttentionUNet().to(m.DEVICE)
    optimizer = torch.optim.Adam(model.parameters(),lr=args.lr)
    if args.resume:
        checkpoint = torch.load(out/'last.pt',map_location=m.DEVICE,weights_only=True)
        model.load_state_dict(checkpoint['model_state_dict'],strict=True)
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        first_epoch = checkpoint['epoch']+1
        best,stale = checkpoint['best_validation_dice'],checkpoint['stale_epochs']
    else:
        save_atomic({'model_state_dict':model.state_dict(),'optimizer_state_dict':optimizer.state_dict(),'epoch':0,
                     'best_validation_dice':best,'stale_epochs':stale},out/'last.pt')
    completed_epoch = first_epoch-1
    (out/'state.json').write_text(json.dumps({'status':'training','latest_epoch':completed_epoch,'smoke':args.smoke},indent=2))
    print(json.dumps({'status':'training_start','run':str(out),'device':str(m.DEVICE),'train_images':len(indices),'val_images':len(val_rows),'epochs_ceiling':args.epochs,'smoke':args.smoke}),flush=True)
    started = time.perf_counter()
    for epoch in range(first_epoch,args.epochs+1):
        if stale >= args.patience:
            break
        # Epoch-local RNGs make an epoch-boundary resume reproducible without
        # depending on previous augmentation-generator state.
        m.set_seed(args.seed+epoch)
        if m.A is not None:
            dataset.transform = m.A.Compose([m.A.HorizontalFlip(p=.5),m.A.Rotate(limit=15,border_mode=cv2.BORDER_REFLECT_101,p=.5)],seed=args.seed+epoch)
        else:
            raise RuntimeError('Pinned Albumentations is required for this declared conservative training config.')
        generator = torch.Generator().manual_seed(args.seed+epoch)
        loader = DataLoader(Subset(dataset,indices),batch_size=args.batch_size,shuffle=True,num_workers=0,generator=generator)
        model.train()
        total_loss,seen = 0.0,0
        epoch_start = time.perf_counter()
        for batch,(images,targets) in enumerate(loader,1):
            images,targets = images.to(m.DEVICE),targets.to(m.DEVICE)
            optimizer.zero_grad(set_to_none=True)
            probability = model(images)
            if args.loss=='bce_dice':
                # Preserve existing sigmoid contract; use stable clipped BCE.
                loss = torch.nn.functional.binary_cross_entropy(probability.clamp(1e-6,1-1e-6),targets)+m.dice_loss(probability,targets)
            else:
                loss = m.focal_tversky_loss(probability,targets)
            if not torch.isfinite(loss):
                raise RuntimeError('Nonfinite training loss')
            loss.backward()
            grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(),max_norm=10,error_if_nonfinite=True)
            optimizer.step()
            total_loss += float(loss.detach())*len(images)
            seen += len(images)
            if batch==1 or batch%100==0 or batch==len(loader):
                print(json.dumps({'epoch':epoch,'batch':batch,'batches':len(loader),'mean_train_loss':total_loss/seen,
                                  'gradient_norm':float(grad_norm),'elapsed_seconds':time.perf_counter()-epoch_start}),flush=True)
                (out/'state.json').write_text(json.dumps({'status':'training','latest_epoch':completed_epoch,'current_epoch':epoch,
                                                        'batch':batch,'batches':len(loader),'mean_train_loss':total_loss/seen,'smoke':args.smoke},indent=2))
        metrics,cases = validate(model,val_rows,annotations,args.archive)
        improved = metrics['mean_positive_dice'] > best
        if improved:
            best,stale = metrics['mean_positive_dice'],0
            save_atomic(model.state_dict(),out/'best_model.pt')
            (out/'best_validation_cases.json').write_text(json.dumps(cases,indent=2))
            (out/'best_validation.json').write_text(json.dumps({'epoch':epoch,'threshold':.5,'policy':'all','metrics':metrics,'model_sha256':sha(out/'best_model.pt')},indent=2))
        else:
            stale += 1
        save_atomic({'model_state_dict':model.state_dict(),'optimizer_state_dict':optimizer.state_dict(),'epoch':epoch,
                     'best_validation_dice':best,'stale_epochs':stale},out/'last.pt')
        log = {'epoch':epoch,'train_loss':total_loss/seen,'lr':optimizer.param_groups[0]['lr'],'validation':metrics,
               'epoch_seconds':time.perf_counter()-epoch_start,'elapsed_run_seconds':time.perf_counter()-started,
               'best_validation_dice':best,'stale_epochs':stale,'device':str(m.DEVICE),'torch':torch.__version__,
               'peak_process_rss_bytes':getattr(psutil.Process().memory_info(),'peak_wset',psutil.Process().memory_info().rss)}
        with open(out/'epochs.jsonl','a') as f:
            f.write(json.dumps(log)+'\n')
        completed_epoch = epoch
        (out/'state.json').write_text(json.dumps({'status':'training','latest_epoch':epoch,'best_validation_dice':best,'smoke':args.smoke},indent=2))
        print(json.dumps(log),flush=True)
        assert sha(protected)==config['original_checkpoint_sha256']
    state = {'status':'completed','epochs_finished':completed_epoch,
             'best_validation_dice':best,'smoke':args.smoke,'elapsed_seconds':time.perf_counter()-started,
             'test_evaluated':False,'next':'validation-only threshold/policy calibration, bundle freeze, then final test'}
    (out/'state.json').write_text(json.dumps(state,indent=2))
    print(json.dumps(state),flush=True)


if __name__=='__main__':
    main()
