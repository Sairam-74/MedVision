"""Actual CUDA TRAIN-only gradient/restore smoke for a registered hard pair."""
import os
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
import argparse
import hashlib
import json
from pathlib import Path
import sys
import cv2
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import medvision_pipeline as p
from tools.ai_atomic_io import atomic_save,json_atomic
from tools.ai_cached_dataset import CachedReliabilityDataset
from tools.ai_presence_model import PresenceAttentionUNet,tensor_digest
from tools.ai_presence_model import balanced_presence_loss
from tools.train_reliability_candidate import candidate_loss
from tools.ai_bounded_hard_weights import class_normalized_weights
from tools.ai_hard_example_loss import hard_example_loss,fixtures


def optimizer_state_digest(state):
    """Hash actual Adam values/structure identically on CPU and CUDA."""
    digest=hashlib.sha256()
    def visit(value):
        if torch.is_tensor(value):
            digest.update(b'tensor:')
            digest.update(str(value.dtype).encode());digest.update(str(tuple(value.shape)).encode())
            digest.update(value.detach().cpu().contiguous().numpy().tobytes())
        elif isinstance(value,dict):
            digest.update(b'dict:')
            for key in sorted(value,key=lambda item:(type(item).__name__,repr(item))):
                visit(key);visit(value[key])
            digest.update(b':enddict')
        elif isinstance(value,(list,tuple)):
            digest.update((type(value).__name__+':').encode())
            for item in value: visit(item)
            digest.update(b':endsequence')
        elif value is None or isinstance(value,(bool,int,float,str)):
            digest.update((type(value).__name__+':'+repr(value)+';').encode())
        else:
            raise TypeError('Unsupported optimizer state value: '+type(value).__name__)
    visit(state)
    return digest.hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--protocol',required=True);ap.add_argument('--out',required=True)
    args=ap.parse_args();protocol_path,out=Path(args.protocol).resolve(),Path(args.out).resolve()
    if ROOT not in protocol_path.parents or ROOT not in out.parents or out.exists(): raise ValueError('Exclusive workspace smoke and registered protocol required')
    protocol=json.loads(protocol_path.read_text())
    if protocol['status']!='registered_after_completed_native_failure_analysis': raise ValueError('Completed native failure analysis required')
    for source,digest in protocol['input_hashes'].items():
        if p.sha(ROOT/source)!=digest: raise ValueError('Frozen protocol input changed: '+source)
    if not torch.cuda.is_available(): raise RuntimeError('CUDA required; no silent CPU smoke substitution')
    torch.set_num_threads(2);cv2.setNumThreads(1);p.seed_everything(42)
    run=ROOT/protocol['initial_run'];config=json.loads((run/'config.json').read_text());bundle=json.loads((run/'bundle.json').read_text())
    full_path=run/f"epoch_{bundle['epoch']:03d}_resume.pt"
    full=torch.load(full_path,map_location='cpu',weights_only=True)
    if tensor_digest(full['model_state_dict'])!=tensor_digest(torch.load(run/'best_model.pt',map_location='cpu',weights_only=True)):
        raise ValueError('Selected snapshot differs')
    snapshot_optimizer_digest=optimizer_state_digest(full['optimizer_state_dict'])
    del full
    data=CachedReliabilityDataset(ROOT/config['cache'],ROOT/config['manifest'],p.PreprocessConfig(**config['preprocess']))
    data.epoch=bundle['global_epoch']+1
    catalog=ROOT/protocol['hard_catalog']
    hp=set(json.loads((catalog/'HARD_POSITIVE_SET.json').read_text())['image_ids'])
    hn=set(json.loads((catalog/'HARD_NEGATIVE_SET.json').read_text())['image_ids'])
    groups=[hp,{r['image_id'] for r in data.rows if int(r['fractured'])}-hp,
            hn,{r['image_id'] for r in data.rows if not int(r['fractured'])}-hn]
    if any(not g for g in groups): raise ValueError('Hard and ordinary examples of both classes required')
    chosen=[sorted(g)[0] for g in groups]
    index={r['image_id']:i for i,r in enumerate(data.rows)}
    # Two actual batches, each positive/normal, identical across matched smoke arms.
    ordered=[chosen[0],chosen[2],chosen[1],chosen[3]]
    out.mkdir();fixture=fixtures();arms=[]
    source_names=['tools/smoke_ai_hard_candidate.py','tools/train_ai_hard_candidate.py','tools/ai_hard_example_loss.py',
                  'tools/ai_bounded_hard_weights.py','tools/ai_presence_model.py','tools/ai_cached_dataset.py','tools/ai_atomic_io.py']
    json_atomic(out/'config.json',dict(protocol_sha256=p.sha(protocol_path),initial_snapshot_sha256=p.sha(full_path),
        sample_ids=ordered,augmentation_global_epoch=data.epoch,source_hashes={s:p.sha(ROOT/s) for s in source_names},
        device='cuda',scope='Four real TRAIN cases; two optimizer steps per factor, discarded research smoke only',
        validation_images_read=0,calibration_images_read=0,test_images_read=0))
    for factor in (1,2):
        p.seed_everything(42)
        weights=class_normalized_weights(data.rows,hp,hn,factor)
        # Adam load_state_dict retains noncapturable step tensor references.
        # Reload each arm independently so prior smoke updates cannot mutate
        # another arm's initializer through the loaded snapshot dictionary.
        arm_full=torch.load(full_path,map_location='cpu',weights_only=True)
        model=PresenceAttentionUNet().to('cuda');model.load_state_dict(arm_full['model_state_dict'],strict=True)
        optimizer=torch.optim.Adam(model.parameters(),lr=.0001);optimizer.load_state_dict(arm_full['optimizer_state_dict'])
        initial_optimizer_digest=optimizer_state_digest(optimizer.state_dict())
        if initial_optimizer_digest!=snapshot_optimizer_digest:
            raise ValueError('Actual initialized optimizer differs from selected full snapshot')
        del arm_full
        initial=tensor_digest(model.state_dict());model.train();torch.cuda.reset_peak_memory_stats();measurements=[]
        for start in (0,2):
            batch_ids=ordered[start:start+2];pairs=[data[index[i]] for i in batch_ids]
            x,y,valid,positive=[torch.stack([v[j] for v in pairs]).to('cuda') for j in range(4)]
            sample_weights=torch.tensor([weights[i] for i in batch_ids],device='cuda')
            optimizer.zero_grad(set_to_none=True);output=model(x)
            loss=hard_example_loss(output['mask_logits'],output['presence_logits'],y,valid,positive,sample_weights,p.LossConfig(mode='bce_dice'),config['presence_weight'])
            if not all(torch.isfinite(v).all() for v in (*output.values(),*loss.values())): raise ValueError('Nonfinite smoke output/loss')
            parity=None
            if factor==1:
                baseline=candidate_loss(output['mask_logits'],y,valid,p.LossConfig(mode='bce_dice'),1.,positive)['total']
                if config['presence_weight']: baseline=baseline+balanced_presence_loss(output['presence_logits'],positive)
                if not torch.equal(baseline,loss['total']): raise ValueError('Actual CUDA neutral scalar parity failed')
                bg=torch.autograd.grad(baseline,tuple(output.values()),retain_graph=True,allow_unused=True)
                wg=torch.autograd.grad(loss['total'],tuple(output.values()),retain_graph=True,allow_unused=True)
                if not all((b is None and w is None) or (b is not None and w is not None and torch.equal(b,w)) for b,w in zip(bg,wg)):
                    raise ValueError('Actual CUDA neutral output-gradient parity failed')
                parity=dict(exact_scalar=True,exact_output_gradients=True)
            loss['total'].backward()
            encoder=float(model.enc1.block[0].weight.grad.norm());decoder=float(model.final[0].weight.grad.norm())
            if encoder<=0 or decoder<=0: raise ValueError('Missing real shared/decoder gradient')
            if not config['presence_weight'] and any(v.grad is not None for v in model.presence.parameters()): raise ValueError('Unsupervised head updated')
            grad=torch.nn.utils.clip_grad_norm_(model.parameters(),10,error_if_nonfinite=True);optimizer.step()
            measurements.append(dict(image_ids=batch_ids,weights=sample_weights.cpu().tolist(),loss=float(loss['total'].detach()),
                encoder_gradient_L2=encoder,decoder_gradient_L2=decoder,gradient_norm_before_clip=float(grad),neutral_cuda_parity=parity))
        final=tensor_digest(model.state_dict())
        final_optimizer_digest=optimizer_state_digest(optimizer.state_dict())
        if final==initial: raise ValueError('Actual optimizer steps did not change model')
        saved=out/f'factor{factor}_smoke_resume.pt'
        atomic_save(dict(model_state_dict=model.state_dict(),optimizer_state_dict=optimizer.state_dict(),factor=factor,smoke=True),saved)
        restored=torch.load(saved,map_location='cuda',weights_only=True)
        model.load_state_dict(restored['model_state_dict'],strict=True);optimizer.load_state_dict(restored['optimizer_state_dict'])
        if tensor_digest(model.state_dict())!=final: raise ValueError('Smoke full restore changed model')
        if optimizer_state_digest(optimizer.state_dict())!=final_optimizer_digest:
            raise ValueError('Smoke full restore changed optimizer state')
        arms.append(dict(factor=factor,initial_parameter_sha256=initial,final_parameter_sha256=final,
            initial_optimizer_state_sha256=initial_optimizer_digest,final_optimizer_state_sha256=final_optimizer_digest,
            measurements=measurements,full_restore_passed=True,checkpoint_sha256=p.sha(saved),
            cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved()))
        del model,optimizer,restored,output,loss,pairs,x,y,valid,positive
        torch.cuda.empty_cache()
    if arms[0]['initial_parameter_sha256']!=arms[1]['initial_parameter_sha256']: raise ValueError('Matched initial tensors differ')
    if arms[0]['initial_optimizer_state_sha256']!=arms[1]['initial_optimizer_state_sha256']:
        raise ValueError('Matched actual optimizer states differ')
    if arms[0]['final_parameter_sha256']==arms[1]['final_parameter_sha256']: raise ValueError('Actual weighting had no effect')
    json_atomic(out/'loss_fixtures.json',fixture)
    json_atomic(out/'completion.json',dict(status='passed_TRAIN_only_hard_smoke',arms=arms,full_matched_initialization=True,
        model_improvement_claim=False,validation_images_read=0,calibration_images_read=0,test_images_read=0,promotion=False))
    print(json.dumps(dict(status='passed_TRAIN_only_hard_smoke',arms=arms),indent=2),flush=True)


if __name__=='__main__': main()
