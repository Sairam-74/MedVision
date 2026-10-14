"""Read-only sampled TRAIN diagnostic of shared encoder task gradients.

Stored BatchNorm statistics, raw unaugmented inputs and no optimizer steps.
These local derivatives do not establish a cause or a population estimate.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time
import cv2
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import medvision_pipeline as p
from tools.ai_cached_dataset import CachedReliabilityDataset
from tools.ai_presence_model import PresenceAttentionUNet, CONTRACT, balanced_presence_loss, tensor_digest
from tools.ai_atomic_io import json_atomic


def gradient_summary(left, right):
    ln, rn = float(left.norm()), float(right.norm())
    return dict(segmentation_L2=ln, presence_L2=rn,
                presence_to_segmentation_norm_ratio=rn/ln if ln else None,
                cosine=float((left.flatten() @ right.flatten()) / (left.norm()*right.norm())) if ln and rn else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    run, out = Path(args.run).resolve(), Path(args.out).resolve()
    if ROOT not in run.parents or ROOT not in out.parents or out.exists():
        raise ValueError('Completed workspace run and exclusive diagnostic required')
    config = json.loads((run/'config.json').read_text())
    state = json.loads((run/'state.json').read_text())
    bundle = json.loads((run/'bundle.json').read_text())
    if state['status'] != 'completed' or state['epochs_finished'] != 12 or config['presence_weight'] != 1 or bundle['output_contract'] != CONTRACT:
        raise ValueError('Completed supervised presence experiment required')
    for source, digest in config['source_hashes'].items():
        if p.sha(ROOT/source) != digest:
            raise ValueError('Training source changed: '+source)
    manifest, checkpoint = ROOT/config['manifest'], run/'best_model.pt'
    if p.sha(manifest) != config['manifest_sha256'] or p.sha(checkpoint) != bundle['checkpoint_sha256']:
        raise ValueError('Frozen membership or selected checkpoint changed')
    torch.set_num_threads(2); cv2.setNumThreads(1); p.seed_everything(42)
    preprocess = p.PreprocessConfig(**config['preprocess'])
    data = CachedReliabilityDataset(ROOT/config['cache'], manifest, preprocess)
    positives = sorted([i for i,r in enumerate(data.rows) if int(r['fractured'])],
        key=lambda i:(data.rows[i]['mask_pixels']/(data.rows[i]['width']*data.rows[i]['height']),data.rows[i]['image_id']))
    normals = [i for i,r in enumerate(data.rows) if not int(r['fractured'])]
    pos = [positives[i] for i in np.linspace(0,len(positives)-1,8,dtype=int)]
    neg = np.random.default_rng(42).choice(normals,size=8,replace=False).tolist()
    chosen = [i for pair in zip(pos,neg) for i in pair]
    model = PresenceAttentionUNet()
    model.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=True),strict=True)
    model.eval()
    before = tensor_digest(model.state_dict())
    parameters = dict(first_encoder_conv=model.enc1.block[0].weight,
                      last_encoder_conv=model.enc4.block[0].weight,
                      bottleneck_conv=model.bottleneck.block[0].weight)
    out.mkdir()
    json_atomic(out/'config.json', dict(run=str(run.relative_to(ROOT)), checkpoint_sha256=p.sha(checkpoint),
        epoch=bundle['epoch'], manifest_sha256=p.sha(manifest), preprocess=asdict(preprocess),
        sample_ids=[data.rows[i]['image_id'] for i in chosen],
        sampling='8 area-rank-spanning TRAIN positives and8 seeded TRAIN normals; same prespecified sample as E5',
        augmentation=False, batchnorm='eval; frozen stored running statistics', device='cpu',
        source_hashes={str(Path(__file__).relative_to(ROOT)):p.sha(__file__)},
        no_optimizer_steps=True, validation_images_read=0, calibration_images_read=0, test_images_read=0))
    rows = []; started = time.perf_counter()
    for order,index in enumerate(chosen,1):
        x,y,valid = [torch.from_numpy(data.arrays[name][index].astype(np.float32,copy=True))[None,None]
                     for name in ('image','target','valid')]
        positive = torch.tensor([bool(int(data.rows[index]['fractured']))])
        outputs = model(x)
        segmentation = p.loss_components(outputs['mask_logits'],y,valid,p.LossConfig(mode='bce_dice'))
        presence = balanced_presence_loss(outputs['presence_logits'],positive)
        sg = torch.autograd.grad(segmentation['total'],tuple(parameters.values()),retain_graph=True)
        hg = torch.autograd.grad(presence,tuple(parameters.values()))
        row = dict(image_id=data.rows[index]['image_id'],positive=bool(positive[0]),
            segmentation_loss=float(segmentation['total'].detach()), presence_loss=float(presence.detach()),
            gradients={name:gradient_summary(s,h) for name,s,h in zip(parameters,sg,hg)})
        if not all(torch.isfinite(g).all() for g in (*sg,*hg)):
            raise ValueError('Nonfinite task gradient')
        rows.append(row)
        json_atomic(out/'progress.json',dict(status='TRAIN_only_shared_gradient_diagnostic',images=order,total=16))
        print(json.dumps(dict(images=order,total=16)),flush=True)
        del outputs,segmentation,presence,sg,hg
    groups = {}
    for positive,name in ((True,'fracture'),(False,'normal')):
        selected = [r for r in rows if r['positive']==positive]
        groups[name] = dict(n=len(selected), encoder_gradients={
            layer:{key:float(np.median([r['gradients'][layer][key] for r in selected if r['gradients'][layer][key] is not None]))
                for key in ('segmentation_L2','presence_L2','presence_to_segmentation_norm_ratio','cosine')}
            for layer in parameters})
    if tensor_digest(model.state_dict()) != before or p.sha(checkpoint) != bundle['checkpoint_sha256']:
        raise ValueError('Diagnostic changed model buffers/tensors or checkpoint')
    json_atomic(out/'per_case.json',rows)
    result = dict(status='completed_read_only_TRAIN_shared_gradient_diagnostic',images=16,groups=groups,
        elapsed_seconds=time.perf_counter()-started,model_tensors_unchanged=True,no_optimizer_steps=True,
        validation_images_read=0,calibration_images_read=0,test_images_read=0,model_improvement_claim=False,
        limitations='Sampled eval-mode local gradients; not training-mode dynamics, whole-TRAIN gradient estimates, or proof of causation. Negative cosine alone does not establish harmful task interference.')
    json_atomic(out/'completion.json',result)
    print(json.dumps(result,indent=2),flush=True)


if __name__ == '__main__': main()
