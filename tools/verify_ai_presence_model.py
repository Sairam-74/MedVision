"""Actual TRAIN-only CPU mask parity and CUDA gradient/checkpoint smoke checks."""
import os
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
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
from tools.ai_presence_model import PresenceAttentionUNet, balanced_presence_loss, CONTRACT, tensor_digest, review_group, selection_key
from tools.ai_cached_dataset import CachedReliabilityDataset
from tools.train_ai_presence_candidate import MANIFEST, MANIFEST_SHA, INIT, INIT_SHA
from tools.train_reliability_candidate import candidate_loss


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = Path(args.out).resolve()
    if ROOT not in out.parents or out.exists():
        raise ValueError('Exclusive workspace smoke output required')
    if not torch.cuda.is_available() or p.sha(MANIFEST)!=MANIFEST_SHA or p.sha(INIT)!=INIT_SHA:
        raise ValueError('CUDA and immutable known shared initializer/split required')
    torch.set_num_threads(2)
    cv2.setNumThreads(1)
    p.seed_everything(42)
    config = p.PreprocessConfig(size=256, resize='stretch', clahe=True, blur_kernel=3, normalization='unit')
    dataset = CachedReliabilityDataset(ROOT/'experiments/AI_TRAIN_CACHE_v3_256_r2', MANIFEST, config)
    dataset.epoch = 9
    positive = [i for i,r in enumerate(dataset.rows) if int(r['fractured'])][:2]
    normal = [i for i,r in enumerate(dataset.rows) if not int(r['fractured'])][:2]
    indices = [positive[0], normal[0], positive[1], normal[1]]
    pairs = [[torch.stack([dataset[i][j] for i in indices[start:start+2]]) for j in range(4)] for start in (0,2)]
    original_sha = p.sha(ROOT/'best_model.pt')
    state = torch.load(INIT, map_location='cpu', weights_only=True)
    base = p.LogitsAttentionUNet()
    base.load_state_dict(state, strict=True)
    base.eval()
    p.seed_everything(42)
    model = PresenceAttentionUNet()
    model.load_shared(state)
    model.eval()
    if sum(v.numel() for v in model.presence.parameters())!=1025:
        raise AssertionError('Unexpected added parameter count')
    if tensor_digest({k:v for k,v in model.state_dict().items() if not k.startswith('presence.')})!=tensor_digest(base.state_dict()):
        raise AssertionError('Shared initializer tensor names/values differ')
    with torch.inference_mode():
        reference = base(pairs[0][0])
        extended = model(pairs[0][0])
    if not torch.equal(reference, extended['mask_logits']) or extended['presence_logits'].shape != (2,):
        raise AssertionError('Initial CPU mask-forward parity/output shape failed')
    initial_cpu_parity = dict(exact_tensor_equal=True,max_absolute_difference=float((reference-extended['mask_logits']).abs().max()),
        mask_shape=list(reference.shape),presence_shape=list(extended['presence_logits'].shape),
        original_shared_tensors_equal=True,added_parameters=1025)
    del base, state, reference, extended
    # Deterministic hand-calculated objective and selection fixtures; not measured model performance.
    zero = torch.tensor([0.,0.])
    labels = torch.tensor([True,False])
    actual = float(balanced_presence_loss(zero, labels))
    expected = np.log(2)*(2808/(2*493)+2808/(2*2315))/2
    if not np.isclose(actual, expected, rtol=1e-6):
        raise AssertionError('Balanced case BCE fixture failed')
    fixture_good = dict(classification=dict(confusion_matrix=dict(tp=79,tn=342),accuracy=421/463),
        delivered=dict(mean_positive_dice=.524,mean_positive_iou=.39))
    fixture_normal = dict(classification=dict(confusion_matrix=dict(tp=0,tn=380),accuracy=380/463),
        delivered=dict(mean_positive_dice=0.,mean_positive_iou=0.))
    if selection_key(fixture_good)[0]!=1 or selection_key(fixture_normal)[1]!=0:
        raise AssertionError('All-normal/feasible-count selection fixture failed')
    four_groups = [review_group(c,m) for c,m in ((True,True),(True,False),(False,True),(False,False))]
    if len(set(four_groups))!=4:
        raise AssertionError('Disagreement group fixture failed')
    out.mkdir()
    json_config = dict(scope='4 actual TRAIN tensors only; no validation/calibration/test inference or metric claims',
        source_hashes={name:p.sha(ROOT/name) for name in ['tools/ai_atomic_io.py','tools/verify_ai_presence_model.py','tools/ai_presence_model.py',
            'tools/train_ai_presence_candidate.py','tools/ai_cached_dataset.py','medvision_pipeline.py','medvision_ai.py']},
        manifest_sha256=MANIFEST_SHA,initial_checkpoint_sha256=INIT_SHA,preprocess=asdict(config),
        train_ids=[dataset.rows[i]['image_id'] for i in indices],device='cuda',torch=torch.__version__,
        cublas_workspace_config=os.environ['CUBLAS_WORKSPACE_CONFIG'],output_contract=CONTRACT)
    (out/'config.json').write_text(json.dumps(json_config,indent=2))
    model = model.to('cuda')
    optimizer = torch.optim.Adam(model.parameters(), lr=.0001)
    checks = []
    started = time.perf_counter()
    torch.cuda.reset_peak_memory_stats()
    for batch, tensors in enumerate(pairs,1):
        model.train()
        x,y,valid,label = [t.to('cuda') for t in tensors]
        optimizer.zero_grad(set_to_none=True)
        outputs = model(x)
        segmentation = candidate_loss(outputs['mask_logits'],y,valid,p.LossConfig(mode='bce_dice'),1.,label)['total']
        case_loss = balanced_presence_loss(outputs['presence_logits'], label)
        encoder = model.enc1.block[0].weight
        decoder = model.final[0].weight
        head = model.presence.weight
        case_grads = torch.autograd.grad(case_loss,(encoder,head,decoder),retain_graph=True,allow_unused=True)
        mask_grads = torch.autograd.grad(segmentation,(encoder,head,decoder),retain_graph=True,allow_unused=True)
        if case_grads[2] is not None or mask_grads[1] is not None:
            raise AssertionError('Presence loss must bypass decoder; mask loss must bypass presence parameters')
        required = [case_grads[0],case_grads[1],mask_grads[0],mask_grads[2]]
        if not all(v is not None and bool(torch.isfinite(v).all()) and float(v.norm())>0 for v in required):
            raise AssertionError('Intended shared/head/decoder gradient path missing/nonfinite')
        total = segmentation+case_loss
        total.backward()
        norm = torch.nn.utils.clip_grad_norm_(model.parameters(),10,error_if_nonfinite=True)
        optimizer.step()
        torch.cuda.synchronize()
        checks.append(dict(batch=batch,segmentation_loss=float(segmentation.detach()),presence_loss=float(case_loss.detach()),
            total_gradient_norm_before_clip=float(norm),presence_to_encoder_grad_norm=float(case_grads[0].norm()),
            presence_head_grad_norm=float(case_grads[1].norm()),segmentation_to_encoder_grad_norm=float(mask_grads[0].norm()),
            segmentation_decoder_grad_norm=float(mask_grads[2].norm()),presence_to_decoder_gradient=None,mask_to_presence_gradient=None,
            all_required_gradients_finite_nonzero=True))
    torch.save(dict(model_state_dict=model.state_dict(),optimizer_state_dict=optimizer.state_dict(),output_contract=CONTRACT),out/'train_only_smoke_checkpoint.pt')
    saved = torch.load(out/'train_only_smoke_checkpoint.pt', map_location='cpu', weights_only=True)
    restored = PresenceAttentionUNet()
    restored.load_state_dict(saved['model_state_dict'],strict=True)
    restored_optimizer = torch.optim.Adam(restored.parameters(),lr=.0001)
    restored_optimizer.load_state_dict(saved['optimizer_state_dict'])
    if tensor_digest(restored.state_dict())!=tensor_digest(model.state_dict()):
        raise AssertionError('Checkpoint model restore differs')
    if p.sha(ROOT/'best_model.pt')!=original_sha or p.sha(INIT)!=INIT_SHA or p.sha(MANIFEST)!=MANIFEST_SHA:
        raise AssertionError('Protected sources/checkpoints/split changed')
    report = dict(status='passed_TRAIN_only_smoke',cpu_mask_forward_parity=initial_cpu_parity,cuda_steps=checks,
        class_BCE_fixture=dict(actual=actual,expected=float(expected),passed=True),
        four_groups=four_groups,all_normal_fixture_rejected=True,feasible_fixture_recognized=True,
        strict_weights_only_model_optimizer_restore=True,model_checkpoint_sha256=p.sha(out/'train_only_smoke_checkpoint.pt'),
        elapsed_cuda_and_restore_seconds=time.perf_counter()-started,cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
        cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved(),validation_images_read=0,calibration_images_read=0,test_images_read=0,
        performance_improvement_claim=False,promotion=False)
    (out/'completion.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)


if __name__=='__main__':
    main()
