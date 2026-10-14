"""Protocol-gated foreground-pixel BCE coefficient comparison, TRAIN/VAL only.

No default protocol: a completed native pair and an explicit evidence-based
registration are required before any optimizer step. Existing trainers intact.
"""
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
import psutil
import torch
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import medvision_pipeline as p
from tools.ai_atomic_io import atomic_save,json_atomic
from tools.ai_cached_dataset import CachedReliabilityDataset
from tools.ai_presence_model import PresenceAttentionUNet,CONTRACT,ARCHITECTURE,tensor_digest,selection_key
from tools.train_ai_presence_candidate import validate
from tools.ai_bounded_hard_weights import class_normalized_weights
from tools.ai_foreground_bce_loss import foreground_bce_loss
from tools.smoke_ai_hard_candidate import optimizer_state_digest


class WeightedTrainingDataset(Dataset):
    def __init__(self,data,weights):
        self.data,self.weights=data,weights
        if set(weights)!={r['image_id'] for r in data.rows}:
            raise ValueError('Exact unique TRAIN weight membership required')
    def __len__(self): return len(self.data)
    def __getitem__(self,index):
        row=self.data.rows[index]
        return (*self.data[index],torch.tensor(self.weights[row['image_id']],dtype=torch.float32),index)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--protocol',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--foreground-bce-coefficient',type=int,choices=[1,5],required=True)
    ap.add_argument('--resume',action='store_true')
    args=ap.parse_args()
    protocol_path,out=Path(args.protocol).resolve(),Path(args.out).resolve()
    if ROOT not in protocol_path.parents or ROOT not in out.parents or out.exists() and not args.resume:
        raise ValueError('Workspace registration and exclusive output/strict resume required')
    protocol=json.loads(protocol_path.read_text())
    if protocol['status']!='registered_after_completed_native_failure_analysis' or protocol['major_factor']!='foreground_pixel_bce_coefficient':
        raise ValueError('Native failure analysis and single-factor registration required')
    if out.name!=protocol['reference' if args.foreground_bce_coefficient==1 else 'candidate']:
        raise ValueError('Registered arm identity required')
    for source,digest in protocol['input_hashes'].items():
        if p.sha(ROOT/source)!=digest: raise ValueError('Registered input changed: '+source)
    if not torch.cuda.is_available(): raise RuntimeError('Registered CUDA training unavailable')
    common=protocol['common_config']
    if common['additional_epochs']!=12 or common['batch_size']!=2 or common['lr']!=.0001 or common['seed']!=42 or common['hard_factor']!=2 or common['global_epochs']!=list(range(40,52)):
        raise ValueError('Registered controlled continuation budget required')
    run=ROOT/protocol['initial_run']
    old=json.loads((run/'config.json').read_text());bundle=json.loads((run/'bundle.json').read_text())
    if json.loads((run/'state.json').read_text())['status']!='completed': raise ValueError('Completed initializer required')
    manifest=ROOT/old['manifest'];archive=ROOT/'FracAtlas.zip'
    if p.sha(manifest)!=old['manifest_sha256'] or p.sha(archive)!=old['archive_sha256']:
        raise ValueError('Frozen data identity changed')
    source_resume=run/f"epoch_{bundle['epoch']:03d}_resume.pt"
    if source_resume.relative_to(ROOT).as_posix()!=protocol['initialization']['snapshot'] or p.sha(source_resume)!=protocol['initialization']['snapshot_sha256']:
        raise ValueError('Registered selected full initializer changed')
    checkpoint=torch.load(source_resume,map_location='cpu',weights_only=True)
    if checkpoint['epoch']!=bundle['epoch'] or checkpoint['global_epoch']!=bundle['global_epoch'] or checkpoint['presence_weight']!=old['presence_weight']:
        raise ValueError('Selected full snapshot/optimizer mismatch')
    if (checkpoint['epoch']!=9 or checkpoint['global_epoch']!=39 or checkpoint['hard_factor']!=2 or
            checkpoint['presence_weight']!=0 or checkpoint['positive_dice_coefficient']!=1 or old['positive_dice_coefficient']!=1):
        raise ValueError('E11 epoch9/global39 hard-factor2 initializer required')
    selected=torch.load(run/'best_model.pt',map_location='cpu',weights_only=True)
    if tensor_digest(checkpoint['model_state_dict'])!=tensor_digest(selected):
        raise ValueError('Full snapshot does not reproduce selected model')
    torch.set_num_threads(2);cv2.setNumThreads(1);p.seed_everything(42)
    preprocess=p.PreprocessConfig(**old['preprocess']);post=p.PostprocessConfig(**old['postprocess'])
    if preprocess.size!=256 or old['normal_bce_weight']!=1. or old['loss']!='bce_dice':
        raise ValueError('Existing fixed objective/preprocessing required')
    data=CachedReliabilityDataset(ROOT/old['cache'],manifest,preprocess,seed=42,elastic=False)
    if len(data)!=2808 or sum(int(r['fractured']) for r in data.rows)!=493:
        raise ValueError('TRAIN distribution changed')
    catalog=ROOT/protocol['hard_catalog']
    if json.loads((catalog/'completion.json').read_text())['status']!='completed_TRAIN_hard_catalog_refresh_only':
        raise ValueError('Completed training-only hard catalog required')
    hp=json.loads((catalog/'HARD_POSITIVE_SET.json').read_text())['image_ids']
    hn=json.loads((catalog/'HARD_NEGATIVE_SET.json').read_text())['image_ids']
    weights=class_normalized_weights(data.rows,hp,hn,2)
    train=WeightedTrainingDataset(data,weights)
    val=p.FracDataset(archive,manifest,'val',preprocess)
    if len(val)!=463 or sum(int(r['fractured']) for r in val.rows)!=83:
        raise ValueError('Validation membership changed')
    loss_config=p.LossConfig(mode='bce_dice')
    start_global=bundle['global_epoch'];presence_weight=old['presence_weight']
    sources=['tools/train_ai_foreground_bce_candidate.py','tools/ai_foreground_bce_loss.py','tools/ai_hard_example_loss.py','tools/ai_bounded_hard_weights.py',
        'tools/train_ai_presence_candidate.py','tools/ai_presence_model.py','tools/ai_cached_dataset.py','tools/ai_atomic_io.py',
        'tools/train_reliability_candidate.py','tools/cache_ai_training_inputs.py','tools/ai_metrics.py',
        'tools/run_experiment.py','tools/smoke_ai_hard_candidate.py','medvision_pipeline.py','medvision_ai.py']
    config=dict(manifest=old['manifest'],manifest_sha256=old['manifest_sha256'],archive_sha256=old['archive_sha256'],
        original_checkpoint_sha256=p.sha(ROOT/'best_model.pt'),initial_checkpoint=str(source_resume.relative_to(ROOT)),
        initial_checkpoint_sha256=p.sha(source_resume),protocol_sha256=p.sha(protocol_path),
        cache=old['cache'],cache_completion_sha256=p.sha(ROOT/old['cache']/'completion.json'),
        output_contract=CONTRACT,architecture=ARCHITECTURE,preprocess=asdict(preprocess),postprocess=asdict(post),
        loss='bce_dice',loss_config=asdict(loss_config),normal_bce_weight=1.,presence_weight=presence_weight,
        class_weights=old['class_weights'],hard_factor=2,positive_dice_coefficient=1,foreground_bce_coefficient=args.foreground_bce_coefficient,hard_catalog=protocol['hard_catalog'],
        hard_positive_count=len(hp),hard_negative_count=len(hn),epochs=12,warm_start_epoch=start_global,
        batch_size=2,lr=.0001,seed=42,elastic=False,positive_fraction=None,
        optimizer='Selected full snapshot Adam restored identically in both arms; no scheduler/weight decay; norm clip10',
        sampling='Natural unique one-pass shuffle; bounded per-image loss weights normalized within each source-label class; no duplication',
        source_hashes={source:p.sha(ROOT/source) for source in sources},device='cuda',torch=torch.__version__,smoke=False,
        cublas_workspace_config=os.environ['CUBLAS_WORKSPACE_CONFIG'],
        selection='Common feasible-first/minimum-normalized TP,TN,Dice,IoU; conservative review alerts and independent masks; earlier ties',
        calibration_fit=False,test_evaluated=False,promotion=False)
    model=PresenceAttentionUNet().to('cuda')
    model.load_state_dict(checkpoint['model_state_dict'],strict=True)
    optimizer=torch.optim.Adam(model.parameters(),lr=.0001)
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    if any(group['lr']!=.0001 for group in optimizer.param_groups): raise ValueError('Initializer learning rate differs')
    initial=dict(full_parameter_sha256=tensor_digest(model.state_dict()),
        optimizer_state_sha256=optimizer_state_digest(optimizer.state_dict()),
        optimizer_snapshot_sha256=p.sha(source_resume),global_epoch=start_global,seed=42,
        total_parameters=sum(v.numel() for v in model.parameters()))
    if (initial['full_parameter_sha256']!=protocol['initialization']['model_parameter_sha256'] or
            initial['optimizer_state_sha256']!=protocol['initialization']['optimizer_state_sha256']):
        raise ValueError('Actual initialized model/Adam differs from registered selected snapshot')
    del checkpoint,selected
    first,best=1,(-1.,-1.,-1.)
    if args.resume:
        if json.loads((out/'config.json').read_text())!=config: raise ValueError('Resume config/code/data differs')
        resumed=torch.load(out/'last.pt',map_location='cuda',weights_only=True)
        if (resumed['output_contract']!=CONTRACT or resumed['manifest_sha256']!=old['manifest_sha256'] or
                resumed['hard_factor']!=2 or resumed['foreground_bce_coefficient']!=args.foreground_bce_coefficient or
                type(resumed['epoch']) is not int or not 0<=resumed['epoch']<=12 or
                resumed['global_epoch']!=39+resumed['epoch'] or resumed['presence_weight']!=0):
            raise ValueError('Resume identity mismatch')
        model.load_state_dict(resumed['model_state_dict'],strict=True);optimizer.load_state_dict(resumed['optimizer_state_dict'])
        if any(group['lr']!=.0001 for group in optimizer.param_groups):
            raise ValueError('Resumed Adam learning rate changed')
        first,best=resumed['epoch']+1,tuple(resumed['best_selection_key'])
        records=[json.loads(v) for v in (out/'epochs.jsonl').read_text().splitlines() if v.strip()] if (out/'epochs.jsonl').exists() else []
        if ([r['epoch'] for r in records]!=list(range(1,first)) or
                any(r['global_epoch']!=39+r['epoch'] or r['train_images_seen']!=2808 or
                    r['unique_train_images_seen']!=2808 for r in records)):
            raise ValueError('Checkpoint/log mismatch; no unrecorded epoch may be skipped')
    else:
        out.mkdir();json_atomic(out/'config.json',config);json_atomic(out/'initial_parameters.json',initial)
        json_atomic(out/'training_example_weights.json',dict(weights=weights,applied=True,factor=2,foreground_bce_coefficient=args.foreground_bce_coefficient,
            mean_within_each_class=1,positive_total=sum(weights[r['image_id']] for r in data.rows if int(r['fractured'])),
            normal_total=sum(weights[r['image_id']] for r in data.rows if not int(r['fractured']))))
        (out/'source_snapshot').mkdir()
        for source in sources: (out/'source_snapshot'/Path(source).name).write_bytes((ROOT/source).read_bytes())
        (out/'source_snapshot'/protocol_path.name).write_bytes(protocol_path.read_bytes())
        atomic_save(dict(model_state_dict=model.state_dict(),optimizer_state_dict=optimizer.state_dict(),epoch=0,
            global_epoch=start_global,best_selection_key=list(best),output_contract=CONTRACT,
            manifest_sha256=old['manifest_sha256'],presence_weight=presence_weight,hard_factor=2,foreground_bce_coefficient=args.foreground_bce_coefficient),out/'last.pt')
    started=time.perf_counter()
    for epoch in range(first,13):
        global_epoch=start_global+epoch;p.seed_everything(42+global_epoch);data.epoch=global_epoch
        loader=DataLoader(train,batch_size=2,shuffle=True,num_workers=0,generator=torch.Generator().manual_seed(42+global_epoch))
        sums,seen,seen_indices=Counter(),0,set();ep_start=time.perf_counter();model.train();torch.cuda.reset_peak_memory_stats()
        for batch,(x,y,valid,positive,example_weight,indices) in enumerate(loader,1):
            current=indices.tolist()
            if seen_indices.intersection(current) or len(current)!=len(set(current)): raise ValueError('Repeated source image within epoch')
            seen_indices.update(current)
            x,y,valid,positive,example_weight=[v.to('cuda') for v in (x,y,valid,positive,example_weight)]
            optimizer.zero_grad(set_to_none=True);output=model(x)
            components=foreground_bce_loss(output['mask_logits'],output['presence_logits'],y,valid,positive,example_weight,loss_config,presence_weight,args.foreground_bce_coefficient)
            if not all(torch.isfinite(v).all() for v in components.values()): raise RuntimeError('Nonfinite training loss')
            components['total'].backward();grad=torch.nn.utils.clip_grad_norm_(model.parameters(),10,error_if_nonfinite=True)
            if not presence_weight and any(v.grad is not None for v in model.presence.parameters()): raise RuntimeError('Unsupervised head received gradient')
            optimizer.step()
            for key,value in components.items(): sums[key]+=float(value.detach())*len(x)
            seen+=len(x)
            if batch==1 or batch%100==0 or batch==len(loader):
                state=dict(status='training',epoch=epoch,global_epoch=global_epoch,batch=batch,batches=len(loader),
                    loss_components={k:v/seen for k,v in sums.items()},gradient_norm=float(grad),elapsed_seconds=time.perf_counter()-ep_start,
                    unique_train_images_seen=len(seen_indices),smoke=False,test_evaluated=False,promotion=False)
                json_atomic(out/'state.json',state);print(json.dumps(state),flush=True)
        if seen!=2808 or seen_indices!=set(range(2808)): raise ValueError('Incomplete one-pass TRAIN coverage')
        json_atomic(out/'state.json',dict(status='validating',epoch=epoch,global_epoch=global_epoch,smoke=False,test_evaluated=False))
        metrics,cases=validate(model,val,preprocess,post,'cuda',bool(presence_weight))
        parity=None
        if args.foreground_bce_coefficient==1 and epoch<=3:
            expected=protocol['reference_replay_parity'][str(global_epoch)]
            actual_model_digest=tensor_digest(model.state_dict())
            actual_optimizer_digest=optimizer_state_digest(optimizer.state_dict())
            parity=dict(validation_exact=metrics==expected['validation'],
                        model_parameter_exact=actual_model_digest==expected['model_parameter_sha256'],
                        optimizer_state_exact=actual_optimizer_digest==expected['optimizer_state_sha256'])
            json_atomic(out/f'reference_replay_epoch_{epoch:03d}.json',dict(epoch=epoch,global_epoch=global_epoch,
                checks=parity,actual_model_parameter_sha256=actual_model_digest,
                actual_optimizer_state_sha256=actual_optimizer_digest,
                actual_validation=metrics,expected=expected))
            if not all(parity.values()):
                raise ValueError('Neutral control failed exact replay of prior E11 global40-42; preserve evidence, do not continue')
        key=selection_key(metrics);selected=key>best
        if selected: best=key
        snapshot=dict(model_state_dict=model.state_dict(),optimizer_state_dict=optimizer.state_dict(),epoch=epoch,global_epoch=global_epoch,
            best_selection_key=list(best),output_contract=CONTRACT,manifest_sha256=old['manifest_sha256'],presence_weight=presence_weight,hard_factor=2,foreground_bce_coefficient=args.foreground_bce_coefficient)
        atomic_save(snapshot,out/f'epoch_{epoch:03d}_resume.pt');atomic_save(snapshot,out/'last.pt')
        if selected:
            atomic_save(model.state_dict(),out/'best_model.pt')
            json_atomic(out/'best_validation.json',dict(epoch=epoch,global_epoch=global_epoch,metrics=metrics,selection_key=list(key)))
            json_atomic(out/'best_validation_cases.json',cases)
            json_atomic(out/'bundle.json',dict(output_contract=CONTRACT,architecture=ARCHITECTURE,checkpoint='best_model.pt',
                checkpoint_sha256=p.sha(out/'best_model.pt'),epoch=epoch,global_epoch=global_epoch,manifest_sha256=old['manifest_sha256'],
                preprocess=asdict(preprocess),postprocess=asdict(post),presence_weight=presence_weight,hard_factor=2,foreground_bce_coefficient=args.foreground_bce_coefficient,
                calibration_status='Unselected research; no calibration/freeze/promotion'))
        record=dict(epoch=epoch,global_epoch=global_epoch,loss_components={k:v/seen for k,v in sums.items()},validation=metrics,
            selection_key=list(key),best_selection_key=list(best),selected=selected,train_images_seen=seen,unique_train_images_seen=len(seen_indices),
            epoch_seconds=time.perf_counter()-ep_start,cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
            cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved(),process_rss_bytes=psutil.Process().memory_info().rss,
            reference_replay_parity=parity,smoke=False,test_evaluated=False,promotion=False)
        with (out/'epochs.jsonl').open('a',encoding='utf-8') as handle:
            handle.write(json.dumps(record,allow_nan=False)+'\n');handle.flush();os.fsync(handle.fileno())
        print(json.dumps(record),flush=True)
        for source,digest in protocol['input_hashes'].items():
            if p.sha(ROOT/source)!=digest: raise ValueError('Registered guard changed: '+source)
    json_atomic(out/'state.json',dict(status='completed',epochs_finished=12,elapsed_seconds=time.perf_counter()-started,
        best_selection_key=list(best),smoke=False,test_evaluated=False,promotion=False))


if __name__=='__main__': main()
