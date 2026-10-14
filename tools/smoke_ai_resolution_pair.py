"""TRAIN-only 256/512 CUDA feasibility smoke; no experiment or candidate training.

Four fixed original TRAIN sources and native COCO masks are independently
prepared at each size. A cached-256 old-trainer arm must exactly match raw256
inputs, logits, losses, gradients and final model/Adam state after two updates.
512 uses the same E14 initializer, batch2, FP32, Adam, loss and augmentation.
An OOM is a failed preserved smoke, never permission to change another factor.
Only the root agent should execute this reviewed tool.
"""
import os
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys
import time
import zipfile

import cv2
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import medvision_pipeline as p
from tools.ai_atomic_io import atomic_save, json_atomic
from tools.ai_cached_dataset import CachedReliabilityDataset
from tools.ai_presence_model import PresenceAttentionUNet, CONTRACT, ARCHITECTURE, tensor_digest
from tools.ai_bounded_hard_weights import class_normalized_weights
from tools.ai_foreground_bce_loss import foreground_bce_loss
from tools.train_reliability_candidate import ReliabilityDataset
from tools.train_ai_foreground_bce_candidate import WeightedTrainingDataset
from tools.smoke_ai_hard_candidate import optimizer_state_digest

RUN = ROOT/'experiments/AI_E14_v3_foreground_BCE5'
SNAPSHOT = RUN/'epoch_011_resume.pt'
SNAPSHOT_SHA = '47c7b2b822c9e422466462f6253463076fff65098d4156158083ff11f14b3713'
BEST_SHA = 'eb7c48dbaa413d10c65b6f664d6baab8928316a57a09e0eb48fef97a8b8e72ce'
ORIGINAL_SHA = '922f30bf691b9979aee65d386bcf73d2643558c049a7d11ab013fea315f39b81'
SAMPLE_CONFIG = ROOT/'experiments/AI_FOREGROUND_GRADIENTS_E11_E12_20261009/config.json'
SAMPLE_SHA = 'a0b32cc3df630b59e5533e584c1ee4ef1ff1d256fa1b88c17ee466b99bb03bbe'
SESSION = ROOT/'experiments/session_20261007_ai_loop_01'
FIXED = (
    ('IMG0002377.jpg', 1639, 'hard_positive'),
    ('IMG0000371.jpg', 257, 'hard_negative'),
    ('IMG0003628.jpg', 2501, 'ordinary_positive'),
    ('IMG0001551.jpg', 1069, 'ordinary_negative'),
)
GLOBAL_EPOCH = 51
SOURCE_NAMES = (
    'tools/smoke_ai_resolution_pair.py', 'tools/train_ai_foreground_bce_candidate.py',
    'tools/ai_foreground_bce_loss.py', 'tools/ai_hard_example_loss.py',
    'tools/ai_bounded_hard_weights.py', 'tools/ai_presence_model.py',
    'tools/ai_cached_dataset.py', 'tools/ai_atomic_io.py',
    'tools/train_reliability_candidate.py', 'tools/smoke_ai_hard_candidate.py',
    'tools/cache_ai_training_inputs.py', 'medvision_pipeline.py', 'medvision_ai.py',
)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def workspace(path):
    path = Path(path).resolve()
    if ROOT not in path.parents:
        raise ValueError('Workspace input/output required')
    return path


def verify(hashes):
    for name, expected in hashes.items():
        path = workspace(ROOT/name)
        if p.sha(path) != expected:
            raise ValueError('Protected smoke input changed: '+name)


def finite_state(value):
    if torch.is_tensor(value):
        return bool(torch.isfinite(value).all())
    if isinstance(value, dict):
        return all(finite_state(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return all(finite_state(v) for v in value)
    return True


def add_guard(guards, path, expected=None):
    path = workspace(path)
    name = str(path.relative_to(ROOT))
    actual = p.sha(path)
    if expected is not None and actual != expected:
        raise ValueError('Expected smoke input hash differs: '+name)
    if name in guards and guards[name] != actual:
        raise ValueError('Conflicting input hash: '+name)
    guards[name] = actual


class TrainOnlyNativeDataset(ReliabilityDataset):
    """Record exactly which original TRAIN images are decoded; no other split."""
    def __init__(self, archive, manifest, config):
        super().__init__(archive, manifest, 'train', config, training=True, seed=42, elastic=False)
        self.epoch = GLOBAL_EPOCH
        self.native_reads = []

    def native(self, index):
        if type(index) is not int or index not in {item[1] for item in FIXED}:
            raise ValueError('Only four fixed TRAIN source indices may be decoded')
        row = self.rows[index]
        if row['split'] != 'train' or (row['image_id'], index) not in {
                (item[0], item[1]) for item in FIXED}:
            raise ValueError('TRAIN source identity mismatch')
        self.native_reads.append(row['image_id'])
        return super().native(index)


def run_arm(name, size, data, weights, expected_model, expected_optimizer, out):
    """Two disposable old-trainer-semantic BS2 steps from an independent reload."""
    arm_dir = out/name
    arm_dir.mkdir()
    json_atomic(out/'state.json', dict(status='smoke_initializing', arm=name, size=size))
    p.seed_everything(42)
    full = torch.load(SNAPSHOT, map_location='cpu', weights_only=True)
    model = PresenceAttentionUNet().to('cuda')
    model.load_state_dict(full['model_state_dict'], strict=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=.0001)
    optimizer.load_state_dict(full['optimizer_state_dict'])
    initial = tensor_digest(model.state_dict())
    initial_optimizer = optimizer_state_digest(optimizer.state_dict())
    if initial != expected_model or initial_optimizer != expected_optimizer:
        raise ValueError('Independent model/Adam restore differs from selected E14 snapshot')
    if any(g['lr'] != .0001 or g['weight_decay'] != 0 for g in optimizer.param_groups):
        raise ValueError('Frozen Adam learning rate/weight decay changed')
    if any(t.is_floating_point() and t.dtype != torch.float32 for t in model.state_dict().values()):
        raise ValueError('FP32 model required; no AMP or alternate precision')
    del full
    train = WeightedTrainingDataset(data, weights)
    p.seed_everything(42+GLOBAL_EPOCH)
    model.train()  # Preserve original trainer BN mode; no batch-stat inference policy.
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    training_start = time.perf_counter()
    steps = []
    for step, start in enumerate((0, 2), 1):
        batch_ids = [item[0] for item in FIXED[start:start+2]]
        indices = [item[1] for item in FIXED[start:start+2]]
        cpu_start = time.perf_counter()
        pairs = [train[index] for index in indices]
        x, y, valid, positive, example_weight = [
            torch.stack([pair[j] for pair in pairs]).to('cuda') for j in range(5)]
        if [pair[5] for pair in pairs] != indices or x.shape != (2, 1, size, size):
            raise ValueError('Exact fixed mixed-source batch2 identity/shape required')
        if any(t.dtype != torch.float32 for t in (x, y, valid, example_weight)) or positive.dtype != torch.bool:
            raise ValueError('Original FP32 training tensor dtypes required')
        if torch.is_autocast_enabled():
            raise ValueError('AMP is not permitted in this single-factor smoke')
        torch.cuda.synchronize()
        preparation_seconds = time.perf_counter()-cpu_start
        json_atomic(out/'state.json', dict(status='smoke_step', arm=name, size=size, step=step,
            image_ids=batch_ids, global_augmentation_epoch=GLOBAL_EPOCH, batch_size=2))
        begin, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        begin.record()
        step_start = time.perf_counter()
        optimizer.zero_grad(set_to_none=True)
        output = model(x)
        if output['mask_logits'].shape != y.shape or output['presence_logits'].shape != positive.shape:
            raise ValueError('Original model output contract differs')
        components = foreground_bce_loss(output['mask_logits'], output['presence_logits'],
            y, valid, positive, example_weight, p.LossConfig(mode='bce_dice'), 0, 5)
        if not all(bool(torch.isfinite(t).all()) for t in (*output.values(), *components.values())):
            raise ValueError('Nonfinite smoke logits or loss')
        output_gradient = torch.autograd.grad(components['total'], output['mask_logits'], retain_graph=True)[0]
        if not bool(torch.isfinite(output_gradient).all()) or bool(output_gradient[~valid.bool()].any()):
            raise ValueError('Nonfinite or invalid-pixel mask derivative')
        derivative_sha = tensor_digest({'mask_output_gradient': output_gradient})
        del output_gradient
        components['total'].backward()
        gradients = {n: q.grad for n, q in model.named_parameters() if q.grad is not None}
        if not gradients or not finite_state(gradients):
            raise ValueError('Finite actual gradients required')
        if any(q.grad is not None for q in model.presence.parameters()):
            raise ValueError('Unsupervised presence head acquired a gradient')
        encoder_norm = float(model.enc1.block[0].weight.grad.norm())
        decoder_norm = float(model.final[0].weight.grad.norm())
        if encoder_norm <= 0 or decoder_norm <= 0:
            raise ValueError('Encoder/decoder update gradient missing')
        gradient_sha = tensor_digest(gradients)
        grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 10, error_if_nonfinite=True)
        optimizer.step()
        end.record()
        torch.cuda.synchronize()
        wall_seconds = time.perf_counter()-step_start
        # Measure training peak before any save/restore verification allocations.
        peak_allocated = torch.cuda.max_memory_allocated()
        peak_reserved = torch.cuda.max_memory_reserved()
        if not finite_state(model.state_dict()) or not finite_state(optimizer.state_dict()):
            raise ValueError('Nonfinite parameters, BN buffers or Adam after update')
        record = dict(step=step, image_ids=batch_ids, train_indices=indices,
            losses={k: float(v.detach()) for k, v in components.items()},
            input_tensor_sha256=tensor_digest(dict(image=x, target=y, valid=valid,
                                                    positive=positive, example_weight=example_weight)),
            output_tensor_sha256=tensor_digest(output), output_gradient_sha256=derivative_sha,
            parameter_gradient_sha256=gradient_sha,
            encoder_gradient_L2=encoder_norm, decoder_gradient_L2=decoder_norm,
            gradient_norm_before_clip=float(grad_norm), valid_pixels=int(valid.sum()),
            foreground_pixels=int(y.sum()), example_weights=example_weight.cpu().tolist(),
            source_preparation_and_transfer_seconds=preparation_seconds,
            measured_cuda_interval_milliseconds=begin.elapsed_time(end),
            measured_step_wall_seconds=wall_seconds,
            cuda_peak_allocated_bytes=peak_allocated, cuda_peak_reserved_bytes=peak_reserved,
            model_parameter_sha256=tensor_digest(model.state_dict()),
            optimizer_state_sha256=optimizer_state_digest(optimizer.state_dict()),
            mask_invalid_pixel_derivatives_zero=True, supervised_head_gradients_absent=True)
        steps.append(record)
        json_atomic(arm_dir/f'step_{step:02d}.json', record)
        print(json.dumps(dict(arm=name, size=size, step=step, finite_update=True,
            cuda_peak_allocated_bytes=peak_allocated, cuda_peak_reserved_bytes=peak_reserved)), flush=True)
        del pairs, x, y, valid, positive, example_weight, output, components, gradients
    torch.cuda.synchronize()
    measured_two_step_elapsed = time.perf_counter()-training_start
    allocated, reserved = torch.cuda.max_memory_allocated(), torch.cuda.max_memory_reserved()
    final_model = tensor_digest(model.state_dict())
    final_optimizer = optimizer_state_digest(optimizer.state_dict())
    if final_model == initial or final_optimizer == initial_optimizer:
        raise ValueError('Two actual smoke steps did not change model and Adam')
    optimizer.zero_grad(set_to_none=True)
    saved = arm_dir/'discarded_smoke_resume.pt'
    atomic_save(dict(model_state_dict=model.state_dict(), optimizer_state_dict=optimizer.state_dict(),
        smoke=True, disposable=True, usable_as_candidate_initializer=False, input_size=size,
        epoch=0, initial_global_epoch=50, augmentation_global_epoch=GLOBAL_EPOCH,
        hard_factor=2, foreground_bce_coefficient=5, positive_dice_coefficient=1,
        presence_weight=0, batch_size=2, output_contract=CONTRACT), saved)
    reloaded = torch.load(saved, map_location='cpu', weights_only=True)
    model.load_state_dict(reloaded['model_state_dict'], strict=True)
    optimizer.load_state_dict(reloaded['optimizer_state_dict'])
    if tensor_digest(model.state_dict()) != final_model or optimizer_state_digest(optimizer.state_dict()) != final_optimizer:
        raise ValueError('Discarded full model/Adam save-restore changed smoke state')
    result = dict(name=name, size=size, initial_parameter_sha256=initial,
        initial_optimizer_sha256=initial_optimizer, final_parameter_sha256=final_model,
        final_optimizer_sha256=final_optimizer, steps=steps, finite_two_steps=True,
        full_model_optimizer_save_restore=True, smoke_checkpoint_sha256=p.sha(saved),
        measured_two_step_elapsed_seconds=measured_two_step_elapsed,
        two_step_peak_allocated_bytes=allocated, two_step_peak_reserved_bytes=reserved,
        timing_scope='Bounded two-step run includes diagnostics/CPU digests; CUDA intervals also include parity diagnostic transfers. Not isolated inference throughput.',
        model_improvement_claim=False, reusable_training_state=False)
    json_atomic(arm_dir/'result.json', result)
    del model, optimizer, reloaded, train
    torch.cuda.empty_cache()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = workspace(args.out)
    if out.exists() or out.parent != ROOT/'experiments' or not out.name.startswith('AI_RESOLUTION_SMOKE_'):
        raise ValueError('Exclusive NEW experiments/AI_RESOLUTION_SMOKE_* directory required')
    config, state, bundle = [read(RUN/name) for name in ('config.json', 'state.json', 'bundle.json')]
    if (state['status'] != 'completed' or state['epochs_finished'] != 12 or state['smoke']
            or bundle['epoch'] != 11 or bundle['global_epoch'] != 50
            or config['hard_factor'] != 2 or config['foreground_bce_coefficient'] != 5
            or config['positive_dice_coefficient'] != 1 or config['presence_weight'] != 0
            or config['normal_bce_weight'] != 1 or config['loss'] != 'bce_dice'
            or config['batch_size'] != 2 or config['lr'] != .0001 or config['seed'] != 42
            or config['elastic'] or config['preprocess']['size'] != 256):
        raise ValueError('Completed selected E14 epoch11/global50 unchanged objective required')
    queue_path = SESSION/'foreground_bce_queue.json'
    queue = read(queue_path)
    if queue['status'] != 'completed_training_and_native_audits_only':
        raise ValueError('Earlier pair must be terminal; do not overlap training')
    guards = dict(queue['guards'])
    verify(guards)
    for name in SOURCE_NAMES:
        add_guard(guards, ROOT/name)
    for name, digest in config['source_hashes'].items():
        add_guard(guards, ROOT/name, digest)
    for path in (queue_path, RUN/'config.json', RUN/'state.json', RUN/'bundle.json'):
        add_guard(guards, path)
    add_guard(guards, SNAPSHOT, SNAPSHOT_SHA)
    add_guard(guards, RUN/'best_model.pt', BEST_SHA)
    add_guard(guards, ROOT/'best_model.pt', ORIGINAL_SHA)
    if bundle['checkpoint_sha256'] != BEST_SHA:
        raise ValueError('Completed selected E14 checkpoint identity changed')
    pair = ROOT/'experiments/AI_E13_E14_FOREGROUND_BCE_PAIR'
    pair_completion = read(pair/'completion.json')
    if pair_completion['status'] != 'completed':
        raise ValueError('Completed E13/E14 comparison required')
    add_guard(guards, pair/'completion.json')
    add_guard(guards, pair/'comparison.json', pair_completion['comparison_sha256'])
    bn = ROOT/'experiments/AI_BATCHNORM_CONTEXT_E13_E14_20261009'
    bn_completion = read(bn/'completion.json')
    if bn_completion['status'] != 'completed_TRAIN_only_frozen_BN_context_diagnosis':
        raise ValueError('Completed frozen TRAIN-only BN diagnosis required')
    add_guard(guards, bn/'completion.json')
    for name in ('config', 'per_case', 'summary'):
        add_guard(guards, bn/(name+'.json'), bn_completion[name+'_sha256'])
    for dirname, status in (('E14_all_normal_alert_sheets', 'completed_actual_native_normal_alerts_review'),
                            ('E14_all_positive_sheets', 'completed_actual_native_positive_segmentation_errors_review')):
        folder = SESSION/dirname
        completion = read(folder/'completion.json')
        if completion['status'] != status:
            raise ValueError('Completed actual E14 failure review required')
        add_guard(guards, folder/'completion.json')
        add_guard(guards, folder/'per_case_visual_review.json', completion['per_case_review_sha256'])
    manifest, archive = workspace(ROOT/config['manifest']), ROOT/'FracAtlas.zip'
    add_guard(guards, manifest, config['manifest_sha256'])
    add_guard(guards, archive, config['archive_sha256'])
    add_guard(guards, SAMPLE_CONFIG, SAMPLE_SHA)
    sample_by_id = {s['image_id']: s for s in read(SAMPLE_CONFIG)['samples']}
    preprocess = p.PreprocessConfig(**config['preprocess'])
    preprocess512 = replace(preprocess, size=512)
    if {k for k, v in asdict(preprocess).items() if v != asdict(preprocess512)[k]} != {'size'}:
        raise ValueError('Only input size may differ')
    torch.set_num_threads(2)
    cv2.setNumThreads(1)
    cache = CachedReliabilityDataset(ROOT/config['cache'], manifest, preprocess, seed=42, elastic=False)
    cache.epoch = GLOBAL_EPOCH
    if len(cache) != 2808 or sum(int(r['fractured']) for r in cache.rows) != 493:
        raise ValueError('Exact unchanged TRAIN2808/493 required')
    add_guard(guards, cache.cache/'completion.json', config['cache_completion_sha256'])
    add_guard(guards, cache.cache/'rows.json', cache.metadata['rows_sha256'])
    for name, digest in cache.metadata['cache_hashes'].items():
        add_guard(guards, cache.cache/(name+'.npy'), digest)
    catalog = workspace(ROOT/config['hard_catalog'])
    hard_positive = set(read(catalog/'HARD_POSITIVE_SET.json')['image_ids'])
    hard_negative = set(read(catalog/'HARD_NEGATIVE_SET.json')['image_ids'])
    if len(hard_positive) != 109 or len(hard_negative) != 713:
        raise ValueError('Unchanged109/713 TRAIN hard examples required')
    for name in ('completion.json', 'HARD_POSITIVE_SET.json', 'HARD_NEGATIVE_SET.json'):
        add_guard(guards, catalog/name)
    weights = class_normalized_weights(cache.rows, hard_positive, hard_negative, 2)
    raw256, raw512 = [TrainOnlyNativeDataset(archive, manifest, pp) for pp in (preprocess, preprocess512)]
    if raw256.rows != cache.rows or raw512.rows != cache.rows:
        raise ValueError('Raw/cache TRAIN order differs')
    selected_rows = []
    for image_id, index, stratum in FIXED:
        row = cache.rows[index]
        if row['image_id'] != image_id or row['split'] != 'train' or sample_by_id[image_id] != dict(
                image_id=image_id, train_index=index, stratum=stratum):
            raise ValueError('Previously fixed four TRAIN sample identities differ')
        positive = bool(int(row['fractured']))
        expected_stratum = ('hard_positive' if image_id in hard_positive else 'ordinary_positive') if positive else (
                            'hard_negative' if image_id in hard_negative else 'ordinary_negative')
        if expected_stratum != stratum:
            raise ValueError('Frozen hard/ordinary stratum differs')
        selected_rows.append(dict(row, train_index=index, stratum=stratum))
    if len({r['group'] for r in selected_rows}) != 4 or sum(int(r['fractured']) for r in selected_rows) != 2:
        raise ValueError('Four distinct TRAIN groups with two positives/two normals required')
    out.mkdir()
    arms, parity, input_checks = [], None, []
    current_arm = 'preprocessing'
    try:
        json_atomic(out/'state.json', dict(status='smoke_preprocessing', selected_TRAIN_ids=[r['image_id'] for r in selected_rows]))
        for row in selected_rows:
            index = row['train_index']
            with zipfile.ZipFile(archive) as z:
                source_sha = hashlib.sha256(z.read(row['member'])).hexdigest()
            image, target = raw256.native(index)
            decoded_sha = hashlib.sha256(str(image.shape).encode()+image.tobytes()).hexdigest()
            if source_sha != row['sha256'] or decoded_sha != row['decoded_sha256'] or int(target.sum()) != row['mask_pixels']:
                raise ValueError('Original TRAIN bytes/native mask differ from frozen manifest')
            prepared256, prepared512 = p.prepare(image, preprocess, target), p.prepare(image, preprocess512, target)
            raw_cache_exact = {name: bool(np.array_equal(value, cache.arrays[name][index].astype(np.float32)))
                               for name, value in zip(('image', 'target', 'valid'), prepared256[:3])}
            augmented256, cached256 = raw256[index], cache[index]
            augmented_exact = all(torch.equal(a, b) for a, b in zip(augmented256, cached256))
            if not all(raw_cache_exact.values()) or not augmented_exact:
                raise ValueError('Native256 preprocessing/augmentation differs from unchanged old cache path')
            if any(not np.isfinite(v).all() for prep in (prepared256, prepared512) for v in prep[:3]):
                raise ValueError('Nonfinite raw preprocessing')
            if any(bool(prep[1].any()) != bool(int(row['fractured'])) for prep in (prepared256, prepared512)):
                raise ValueError('Native target disappeared under one resolution')
            input_checks.append(dict(image_id=row['image_id'], train_index=index, group=row['group'],
                stratum=row['stratum'], native_shape=list(image.shape), original_byte_sha256=source_sha,
                decoded_sha256=decoded_sha, native_target_pixels=int(target.sum()),
                unaugmented_target_pixels={str(size): int(prep[1].sum()) for size, prep in ((256, prepared256), (512, prepared512))},
                raw256_cache_bit_exact=raw_cache_exact, augmented256_cache_bit_exact=augmented_exact,
                augmentation_seed=int(np.random.SeedSequence([42, GLOBAL_EPOCH, index]).generate_state(1)[0]),
                preprocessing512_direct_from_original_image_and_native_mask=True))
        if not torch.cuda.is_available():
            raise RuntimeError('Actual CUDA required; no CPU/AMP/batch-size substitute')
        full = torch.load(SNAPSHOT, map_location='cpu', weights_only=True)
        if (full['epoch'] != 11 or full['global_epoch'] != 50 or full['hard_factor'] != 2
                or full['foreground_bce_coefficient'] != 5 or full['presence_weight'] != 0
                or full['manifest_sha256'] != config['manifest_sha256'] or full['output_contract'] != CONTRACT):
            raise ValueError('Selected full E14 model/Adam snapshot metadata differs')
        selected = torch.load(RUN/'best_model.pt', map_location='cpu', weights_only=True)
        initial_model, initial_optimizer = tensor_digest(full['model_state_dict']), optimizer_state_digest(full['optimizer_state_dict'])
        if initial_model != tensor_digest(selected) or not finite_state(full):
            raise ValueError('Full E14 snapshot differs from selected best or contains nonfinite state')
        del full, selected
        json_atomic(out/'config.json', dict(initial_run=str(RUN.relative_to(ROOT)), initial_snapshot_sha256=SNAPSHOT_SHA,
            initial_checkpoint_sha256=BEST_SHA, initial_parameter_sha256=initial_model,
            initial_optimizer_sha256=initial_optimizer, original_checkpoint_sha256=ORIGINAL_SHA,
            preprocess_by_size={'256': asdict(preprocess), '512': asdict(preprocess512)},
            selected_TRAIN_rows=selected_rows, input_checks=input_checks, global_augmentation_epoch=GLOBAL_EPOCH,
            registered_experiment=False, model_architecture=ARCHITECTURE, batch_size=2, precision='fp32',
            seed=42, learning_rate=.0001, gradient_clip_norm=10, hard_factor=2,
            foreground_bce_coefficient=5, positive_dice_coefficient=1, presence_weight=0, normal_bce_weight=1,
            loss='bce_dice', optimizer='Full selected E14 Adam snapshot independently restored for each discarded arm',
            source_hashes={n: p.sha(ROOT/n) for n in SOURCE_NAMES}, all_protected_input_hashes=guards,
            CUDA_device_name=torch.cuda.get_device_name(0), CUDA_total_memory_bytes=torch.cuda.get_device_properties(0).total_memory,
            scope='Four fixed TRAIN sources; two mixed batch2 discarded steps in cached256/raw256/raw512',
            validation_images_read=0, calibration_images_read=0, test_images_read=0, promotion=False,
            timing_limit='Bounded smoke timings include diagnostic transfers; do not extrapolate whole-epoch throughput or clinical latency'))
        for name, size, data in (('legacy_cached256', 256, cache), ('raw256', 256, raw256), ('raw512', 512, raw512)):
            current_arm = name
            arm = run_arm(name, size, data, weights, initial_model, initial_optimizer, out)
            arms.append(arm)
            if name == 'raw256':
                fields = ('input_tensor_sha256', 'output_tensor_sha256', 'output_gradient_sha256',
                          'parameter_gradient_sha256', 'model_parameter_sha256', 'optimizer_state_sha256', 'losses')
                parity = dict(per_step_exact=all(
                    arms[0]['steps'][i][f] == arm['steps'][i][f] for i in range(2) for f in fields),
                    final_model_exact=arms[0]['final_parameter_sha256'] == arm['final_parameter_sha256'],
                    final_optimizer_exact=arms[0]['final_optimizer_sha256'] == arm['final_optimizer_sha256'])
                json_atomic(out/'control256_parity.json', parity)
                if not all(parity.values()):
                    raise ValueError('256 control failed exact old-trainer-path parity; stop before512')
        verify(guards)
        completion = dict(status='passed_TRAIN_only_resolution_smoke', arms=arms,
            exact256_cached_raw_training_parity=parity, actual_unique_TRAIN_sources=4,
            full_matched_initialization=True, cached256_vs_native256_exact=all(parity.values()),
            input512_batch2_fp32_feasible=True,
            actual_TRAIN_native_reads={'raw256': raw256.native_reads, 'raw512': raw512.native_reads},
            original_guard_count_verified=len(guards), source_sha256=p.sha(Path(__file__)),
            guards_unchanged=True, raw512_from_native_sources=True, batch_size=2, fp32=True,
            additional_factors_changed=False, fixed_model_optimizer_initialization=True,
            registered_experiment=False, smoke_states_disposable=True, model_improvement_claim=False,
            validation_images_read=0, calibration_images_read=0, test_images_read=0, promotion=False)
        json_atomic(out/'completion.json', completion)
        json_atomic(out/'state.json', dict(status=completion['status'], model_improvement_claim=False))
        print(json.dumps(completion, indent=2), flush=True)
    except Exception as error:
        try:
            verify(guards)
            guard_result = dict(guards_unchanged=True, verified_count=len(guards))
        except Exception as guard_error:
            guard_result = dict(guards_unchanged=False, verification_error=str(guard_error))
        oom = isinstance(error, torch.cuda.OutOfMemoryError)
        failure = dict(status='failed_CUDA_OOM_resolution_smoke' if oom else 'failed_resolution_smoke',
            failed_arm=current_arm, error_type=type(error).__name__, error=str(error), completed_arms=arms,
            saved_input_checks=input_checks, exact256_cached_raw_training_parity=parity,
            guard_verification=guard_result, source_sha256=p.sha(Path(__file__)),
            no_retry_with_changed_batch_precision_optimizer_loss=True, partial_artifacts_preserved=True,
            registered_experiment=False, model_improvement_claim=False,
            validation_images_read=0, calibration_images_read=0, test_images_read=0, promotion=False)
        if torch.cuda.is_initialized():
            failure['cuda_peak_allocated_bytes_at_failure'] = torch.cuda.max_memory_allocated()
            failure['cuda_peak_reserved_bytes_at_failure'] = torch.cuda.max_memory_reserved()
        json_atomic(out/'completion.json', failure)
        json_atomic(out/'state.json', dict(status=failure['status'], failed_arm=current_arm, error=str(error)))
        print(json.dumps(failure, indent=2), flush=True)
        raise


if __name__ == '__main__':
    main()

