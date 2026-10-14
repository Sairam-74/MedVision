"""Registered real TRAIN-only CUDA smoke of positive Dice coefficient1/2.

Three independently reloaded E10 model+Adam arms prove old-loss/coefficient1
optimizer neutrality and finite coefficient2 updates. Smoke snapshots are
discarded research artifacts, never training initializers or production.
"""
import os
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
import argparse
import json
from pathlib import Path
import sys

import cv2
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import medvision_pipeline as p
from tools.ai_atomic_io import atomic_save, json_atomic
from tools.ai_cached_dataset import CachedReliabilityDataset
from tools.ai_presence_model import PresenceAttentionUNet, tensor_digest
from tools.ai_bounded_hard_weights import class_normalized_weights
from tools.ai_hard_example_loss import hard_example_loss
from tools.ai_positive_dice_loss import positive_dice_loss, fixtures
from tools.smoke_ai_hard_candidate import optimizer_state_digest


def finite_state(value):
    if torch.is_tensor(value):
        return bool(torch.isfinite(value).all())
    if isinstance(value, dict):
        return all(finite_state(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return all(finite_state(v) for v in value)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--protocol', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    protocol_path, out = Path(args.protocol).resolve(), Path(args.out).resolve()
    if ROOT not in protocol_path.parents or ROOT not in out.parents or out.exists():
        raise ValueError('Registered workspace protocol and new exclusive smoke output required')
    protocol = json.loads(protocol_path.read_text(encoding='utf-8'))
    if (protocol['status'] != 'registered_after_completed_native_failure_analysis'
            or protocol['major_factor'] != 'positive_case_dice_coefficient'
            or protocol['factor']['reference'] != 1 or protocol['factor']['candidate'] != 2):
        raise ValueError('Completed failure analysis and coefficient1 versus2 registration required')
    common = protocol['common_config']
    if common['hard_factor'] != 2 or common['presence_weight'] != 0 or common['normal_bce_weight'] != 1:
        raise ValueError('Frozen hard-factor2 and mask-only all-image BCE required')
    guards = {str((ROOT / source).resolve()): digest for source, digest in protocol['input_hashes'].items()}
    for source, digest in guards.items():
        source_path = Path(source)
        if ROOT not in source_path.parents or p.sha(source_path) != digest:
            raise ValueError('Registered input changed: ' + source)
    guards[str(protocol_path)] = p.sha(protocol_path)
    if not torch.cuda.is_available():
        raise RuntimeError('Actual registered CUDA smoke required; no CPU substitution')
    torch.set_num_threads(2)
    cv2.setNumThreads(1)
    p.seed_everything(42)
    run = (ROOT / protocol['initial_run']).resolve()
    if ROOT not in run.parents or run.name != 'AI_E10_v3_hard_weight2':
        raise ValueError('Completed selected E10 initializer required')
    config = json.loads((run / 'config.json').read_text())
    state = json.loads((run / 'state.json').read_text())
    bundle = json.loads((run / 'bundle.json').read_text())
    if (state['status'] != 'completed' or state['epochs_finished'] != 12 or state['smoke']
            or bundle['epoch'] != 12 or bundle['global_epoch'] != 30
            or config['hard_factor'] != 2 or config['presence_weight'] != 0
            or config['normal_bce_weight'] != 1 or config['loss'] != 'bce_dice'
            or config['batch_size'] != 2 or config['lr'] != .0001
            or config['preprocess']['size'] != 256):
        raise ValueError('Selected E10 epoch12/global30 fixed objective and runtime required')
    snapshot = (ROOT / protocol['initialization']['snapshot']).resolve()
    if (snapshot != run / 'epoch_012_resume.pt'
            or protocol['initialization']['selected_epoch'] != 12
            or protocol['initialization']['global_epoch'] != 30
            or guards.get(str(snapshot)) != p.sha(snapshot)):
        raise ValueError('Registered exact selected full snapshot required')
    full = torch.load(snapshot, map_location='cpu', weights_only=True)
    if full['epoch'] != 12 or full['global_epoch'] != 30 or full['hard_factor'] != 2 or full['presence_weight'] != 0:
        raise ValueError('Full snapshot metadata differs from selected E10')
    if p.sha(run / 'best_model.pt') != bundle['checkpoint_sha256']:
        raise ValueError('Selected best checkpoint identity changed')
    selected = torch.load(run / 'best_model.pt', map_location='cpu', weights_only=True)
    initial_model_digest = tensor_digest(full['model_state_dict'])
    if initial_model_digest != tensor_digest(selected):
        raise ValueError('Selected full snapshot does not reproduce E10 best parameters')
    snapshot_optimizer_digest = optimizer_state_digest(full['optimizer_state_dict'])
    del full, selected
    data = CachedReliabilityDataset(ROOT / config['cache'], ROOT / config['manifest'],
                                    p.PreprocessConfig(**config['preprocess']), seed=42, elastic=False)
    if len(data) != 2808 or sum(int(r['fractured']) for r in data.rows) != 493:
        raise ValueError('Frozen unique TRAIN2808/493 required')
    data.epoch = 31
    catalog = ROOT / protocol['hard_catalog']
    if json.loads((catalog / 'completion.json').read_text())['status'] != 'completed_TRAIN_hard_catalog_refresh_only':
        raise ValueError('Frozen TRAIN-only hard catalog required')
    hp = set(json.loads((catalog / 'HARD_POSITIVE_SET.json').read_text())['image_ids'])
    hn = set(json.loads((catalog / 'HARD_NEGATIVE_SET.json').read_text())['image_ids'])
    if len(hp) != 109 or len(hn) != 713:
        raise ValueError('Registered109/713 hard membership required')
    weights = class_normalized_weights(data.rows, hp, hn, 2)
    positives = {r['image_id'] for r in data.rows if int(r['fractured'])}
    normals = {r['image_id'] for r in data.rows if not int(r['fractured'])}
    groups = [hp, hn, positives - hp, normals - hn]
    if any(not group for group in groups):
        raise ValueError('Hard and ordinary examples of both source labels required')
    ordered = [sorted(group)[0] for group in groups]
    indices = {r['image_id']: i for i, r in enumerate(data.rows)}
    fixture_results = fixtures()
    source_names = ['tools/smoke_ai_positive_dice.py', 'tools/ai_positive_dice_loss.py',
                    'tools/ai_hard_example_loss.py', 'tools/ai_bounded_hard_weights.py',
                    'tools/ai_presence_model.py', 'tools/ai_cached_dataset.py', 'tools/ai_atomic_io.py',
                    'tools/smoke_ai_hard_candidate.py', 'tools/train_reliability_candidate.py',
                    'medvision_pipeline.py', 'medvision_ai.py']
    if any(guards.get(str(ROOT / source)) != p.sha(ROOT / source) for source in source_names):
        raise ValueError('All smoke and objective sources must be bound into registration')
    out.mkdir()
    json_atomic(out / 'config.json', dict(protocol_sha256=p.sha(protocol_path),
        initial_snapshot_sha256=p.sha(snapshot), selected_checkpoint_sha256=bundle['checkpoint_sha256'],
        sample_ids=ordered, hard_factor=2, coefficients=[1, 2], augmentation_global_epoch=31,
        source_hashes={source: p.sha(ROOT / source) for source in source_names},
        device='cuda', batch_size=2, seed=42,
        scope='Four actual TRAIN sources; two discarded optimizer steps in each of three independent arms',
        validation_images_read=0, calibration_images_read=0, test_images_read=0))
    arms = []
    for name, coefficient in (('original_hard_loss', None), ('coefficient1', 1), ('coefficient2', 2)):
        p.seed_everything(42)
        arm_full = torch.load(snapshot, map_location='cpu', weights_only=True)
        model = PresenceAttentionUNet().to('cuda')
        model.load_state_dict(arm_full['model_state_dict'], strict=True)
        optimizer = torch.optim.Adam(model.parameters(), lr=.0001)
        optimizer.load_state_dict(arm_full['optimizer_state_dict'])
        initial = tensor_digest(model.state_dict())
        initial_optimizer = optimizer_state_digest(optimizer.state_dict())
        if initial != initial_model_digest or initial_optimizer != snapshot_optimizer_digest:
            raise ValueError('Actual initial model or Adam differs from independently reloaded selected snapshot')
        del arm_full
        model.train()
        torch.cuda.reset_peak_memory_stats()
        measurements = []
        for start in (0, 2):
            batch_ids = ordered[start:start + 2]
            pairs = [data[indices[image_id]] for image_id in batch_ids]
            x, target, valid, positive = [torch.stack([pair[j] for pair in pairs]).to('cuda') for j in range(4)]
            example_weights = torch.tensor([weights[i] for i in batch_ids], dtype=torch.float32, device='cuda')
            optimizer.zero_grad(set_to_none=True)
            output = model(x)
            baseline = hard_example_loss(output['mask_logits'], output['presence_logits'], target, valid,
                                         positive, example_weights, p.LossConfig(mode='bce_dice'), 0)
            loss = baseline if coefficient is None else positive_dice_loss(output['mask_logits'], output['presence_logits'],
                target, valid, positive, example_weights, p.LossConfig(mode='bce_dice'), 0, coefficient)
            if not all(bool(torch.isfinite(v).all()) for v in (*output.values(), *loss.values())):
                raise ValueError('Nonfinite actual smoke output/loss')
            parity = None
            if coefficient == 1:
                if not all(torch.equal(baseline[k], loss[k]) for k in baseline):
                    raise ValueError('Actual CUDA coefficient1 scalar/component neutrality failed')
                bg = torch.autograd.grad(baseline['total'], tuple(output.values()), retain_graph=True, allow_unused=True)
                ng = torch.autograd.grad(loss['total'], tuple(output.values()), retain_graph=True, allow_unused=True)
                if not all((b is None and n is None) or (b is not None and n is not None and torch.equal(b, n)) for b, n in zip(bg, ng)):
                    raise ValueError('Actual CUDA coefficient1 output-gradient neutrality failed')
                parity = dict(exact_scalar_components=True, exact_output_gradients=True)
            if coefficient == 2:
                bg = torch.autograd.grad(baseline['total'], output['mask_logits'], retain_graph=True)[0]
                ng = torch.autograd.grad(loss['total'], output['mask_logits'], retain_graph=True)[0]
                if not torch.equal(baseline['bce'], loss['bce']) or not torch.equal(bg[~positive], ng[~positive]):
                    raise ValueError('Coefficient2 changed BCE or normal output gradients')
                parity = dict(all_image_BCE_unchanged=True, normal_output_gradients_unchanged=True)
            loss['total'].backward()
            encoder = float(model.enc1.block[0].weight.grad.norm())
            decoder = float(model.final[0].weight.grad.norm())
            if encoder <= 0 or decoder <= 0:
                raise ValueError('Actual shared/decoder gradient missing')
            if any(parameter.grad is not None for parameter in model.presence.parameters()):
                raise ValueError('Unsupervised head acquired a gradient')
            grad = torch.nn.utils.clip_grad_norm_(model.parameters(), 10, error_if_nonfinite=True)
            optimizer.step()
            if not finite_state(model.state_dict()) or not finite_state(optimizer.state_dict()):
                raise ValueError('Nonfinite model or Adam after actual update')
            measurements.append(dict(image_ids=batch_ids, frozen_example_weights=example_weights.cpu().tolist(),
                losses={k: float(v.detach()) for k, v in loss.items()}, parity=parity,
                encoder_gradient_L2=encoder, decoder_gradient_L2=decoder,
                gradient_norm_before_clip=float(grad)))
        final = tensor_digest(model.state_dict())
        final_optimizer = optimizer_state_digest(optimizer.state_dict())
        if final == initial or final_optimizer == initial_optimizer:
            raise ValueError('Actual smoke optimizer steps did not change model and Adam')
        saved = out / (name + '_smoke_resume.pt')
        atomic_save(dict(model_state_dict=model.state_dict(), optimizer_state_dict=optimizer.state_dict(),
                         coefficient=coefficient, hard_factor=2, smoke=True), saved)
        restored = torch.load(saved, map_location='cuda', weights_only=True)
        model.load_state_dict(restored['model_state_dict'], strict=True)
        optimizer.load_state_dict(restored['optimizer_state_dict'])
        if tensor_digest(model.state_dict()) != final or optimizer_state_digest(optimizer.state_dict()) != final_optimizer:
            raise ValueError('Saved full model/Adam restore changed actual state')
        arms.append(dict(name=name, coefficient=coefficient, initial_parameter_sha256=initial,
            initial_optimizer_state_sha256=initial_optimizer, final_parameter_sha256=final,
            final_optimizer_state_sha256=final_optimizer, full_restore_passed=True,
            smoke_checkpoint_sha256=p.sha(saved), measurements=measurements,
            cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
            cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved()))
        del model, optimizer, restored, output, baseline, loss, pairs, x, target, valid, positive
        if coefficient is not None:
            del bg, ng
        torch.cuda.empty_cache()
    for field in ('initial_parameter_sha256', 'initial_optimizer_state_sha256'):
        if len({arm[field] for arm in arms}) != 1:
            raise ValueError('Smoke arm initializations differ')
    for field in ('final_parameter_sha256', 'final_optimizer_state_sha256'):
        if arms[0][field] != arms[1][field]:
            raise ValueError('Coefficient1 is not exactly optimizer/model neutral against frozen original loss')
    if arms[1]['final_parameter_sha256'] == arms[2]['final_parameter_sha256']:
        raise ValueError('Coefficient2 produced no actual parameter effect')
    for source, digest in guards.items():
        if p.sha(source) != digest:
            raise ValueError('Registered input changed during smoke: ' + source)
    json_atomic(out / 'loss_fixtures.json', fixture_results)
    completion = dict(status='passed_TRAIN_only_positive_dice_smoke', arms=arms,
        full_matched_initialization=True, coefficient1_exact_model_optimizer_parity=True,
        coefficient2_finite_updates=True, negative_BCE_and_normal_output_gradients_preserved=True,
        model_improvement_claim=False, validation_images_read=0,
        calibration_images_read=0, test_images_read=0, promotion=False)
    json_atomic(out / 'completion.json', completion)
    print(json.dumps(completion, indent=2), flush=True)


if __name__ == '__main__':
    main()
