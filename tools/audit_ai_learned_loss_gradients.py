"""Read-only learned-gradient diagnostic on16 fixed TRAIN examples, not a model experiment."""
from collections import defaultdict
import json
from pathlib import Path
import sys
import time
import cv2
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import medvision_pipeline as p
from tools.ai_cached_dataset import CachedReliabilityDataset
from tools.ai_atomic_io import json_atomic


def main():
    out=ROOT/'experiments/AI_LEARNED_LOSS_GRADIENTS_E5_v3'
    if out.exists(): raise ValueError('Exclusive diagnostic output required')
    manifest=ROOT/'experiments/data_v3_reliability_20261007/manifest.json'
    checkpoint=ROOT/'experiments/AI_E5_v3_BCE_reference/best_model.pt'
    if p.sha(manifest)!='4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318' or p.sha(checkpoint)!='4bf4065a256c412c735895b26b42f3b5c1ef862f89376973236c66f43acb0ba7':
        raise ValueError('Frozen TRAIN/selected E5 weights changed')
    torch.set_num_threads(2);cv2.setNumThreads(1);p.seed_everything(42)
    config=p.PreprocessConfig(size=256,resize='stretch',clahe=True,blur_kernel=3,normalization='unit')
    data=CachedReliabilityDataset(ROOT/'experiments/AI_TRAIN_CACHE_v3_256_r2',manifest,config)
    data.training=False
    positives=sorted([i for i,r in enumerate(data.rows) if int(r['fractured'])],
                     key=lambda i:(data.rows[i]['mask_pixels']/(data.rows[i]['width']*data.rows[i]['height']),data.rows[i]['image_id']))
    normals=[i for i,r in enumerate(data.rows) if not int(r['fractured'])]
    pos=[positives[i] for i in np.linspace(0,len(positives)-1,8,dtype=int)]
    neg=np.random.default_rng(42).choice(normals,size=8,replace=False).tolist()
    chosen=[v for pair in zip(pos,neg) for v in pair]
    out.mkdir()
    json_atomic(out/'config.json',dict(checkpoint=str(checkpoint.relative_to(ROOT)),checkpoint_sha256=p.sha(checkpoint),
        manifest_sha256=p.sha(manifest),sampling='8 TRAIN positives spanning native annotation-area ranks plus8 seeded TRAIN normals; no outcome selection',
        ids=[data.rows[i]['image_id'] for i in chosen],augmentation=False,device='cpu',
        scope='Sampled learned gradient magnitudes, not proof of causal optimization failure or whole-dataset estimates',
        no_optimizer_steps=True,validation_images_read=0,calibration_images_read=0,test_images_read=0))
    # Explicit small analytic derivative check for the existing BCE and Dice formula.
    z=torch.tensor([[[[-2.,-.3,.7,2.]]]],requires_grad=True)
    y=torch.tensor([[[[0.,1.,1.,0.]]]])
    v=torch.ones_like(y);cfg=p.LossConfig(mode='bce_dice')
    comp=p.loss_components(z,y,v,cfg);q=z.sigmoid().detach()
    denom=q.sum()+y.sum()+cfg.smooth;numerator=2*(q*y).sum()+cfg.smooth
    for name,expected in [('bce',(q-y)/4),('dice',(numerator-2*y*denom)/(denom**2)*q*(1-q))]:
        measured=torch.autograd.grad(comp[name],z,retain_graph=True)[0]
        if not torch.allclose(measured,expected,atol=1e-7,rtol=1e-5): raise AssertionError('Analytic derivative fixture failed: '+name)
    model=p.LogitsAttentionUNet()
    model.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=True),strict=True);model.eval()
    rows=[];started=time.perf_counter()
    for order,index in enumerate(chosen,1):
        x,y,valid,positive=data[index]
        z=model(x[None]);y=y[None];valid=valid[None]
        comp=p.loss_components(z,y,valid,cfg)
        grads={name:torch.autograd.grad(comp[name],z,retain_graph=True)[0] for name in ('bce','dice','total')}
        encoder=model.enc1.block[0].weight;decoder=model.final[0].weight
        weight_grads=torch.autograd.grad(comp['total'],(encoder,decoder))
        with torch.no_grad():
            probability=z.sigmoid();normal_mass=float((probability*(1-y)*valid).sum())
            row=dict(image_id=data.rows[index]['image_id'],positive=bool(positive),
                target_pixels=int(y.sum()),valid_pixels=int(valid.sum()),predicted_probability_mass=float((probability*valid).sum()),
                background_probability_mass=normal_mass,soft_dice=1-float(comp['dice']),
                losses={name:float(comp[name]) for name in ('bce','dice','total')},
                logit_gradient_L2={name:float(g.norm()) for name,g in grads.items()},
                logit_gradient_L1={name:float(g.abs().sum()) for name,g in grads.items()},
                encoder_first_conv_total_gradient_L2=float(weight_grads[0].norm()),
                decoder_output_total_gradient_L2=float(weight_grads[1].norm()))
        if not all(np.isfinite(v) for v in row['logit_gradient_L2'].values()): raise ValueError('Nonfinite measured gradient')
        rows.append(row)
        json_atomic(out/'progress.json',dict(status='TRAIN_only_gradient_diagnostic',images=order,total=16))
        print(json.dumps(dict(images=order,total=16)),flush=True)
        del z,comp,grads,weight_grads
    groups={}
    for label,name in ((True,'fracture'),(False,'normal')):
        cases=[r for r in rows if r['positive']==label]
        groups[name]=dict(n=len(cases),median_soft_dice=float(np.median([r['soft_dice'] for r in cases])),
            mean_losses={key:float(np.mean([r['losses'][key] for r in cases])) for key in ('bce','dice','total')},
            median_logit_gradient_L2={key:float(np.median([r['logit_gradient_L2'][key] for r in cases])) for key in ('bce','dice','total')})
    json_atomic(out/'per_case.json',rows)
    result=dict(status='completed_read_only_TRAIN_diagnostic',images=16,groups=groups,
        analytic_derivative_fixtures_passed=True,elapsed_seconds=time.perf_counter()-started,
        checkpoint_sha256=p.sha(checkpoint),no_optimizer_steps=True,model_improvement_claim=False,
        validation_images_read=0,calibration_images_read=0,test_images_read=0,
        limitations='One checkpoint and16 explicitly sampled cases. These norms are not a full TRAIN population estimate, SGD trajectory, or proof of architecture/loss causation.')
    json_atomic(out/'completion.json',result)
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    main()
