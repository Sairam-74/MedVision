"""Protocol-gated native-derived 256/512 resolution comparison, TRAIN/VAL only.

Independent full selected E14 model/Adam restoration in both arms. Resolution
is the only changed factor; the canonical cached dataset, objective, sampling,
global augmentation schedule and native validation/selection remain unchanged.
No default protocol or output and no production/checkpoint overwrite.
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
sys.path.insert(0, str(ROOT))
import medvision_pipeline as p
from tools.ai_atomic_io import atomic_save, json_atomic
from tools.ai_cached_dataset import CachedReliabilityDataset
from tools.ai_presence_model import PresenceAttentionUNet, CONTRACT, ARCHITECTURE, tensor_digest, selection_key
from tools.train_ai_presence_candidate import validate
from tools.ai_bounded_hard_weights import class_normalized_weights
from tools.ai_foreground_bce_loss import foreground_bce_loss
from tools.smoke_ai_hard_candidate import optimizer_state_digest

SOURCES = [
    'tools/train_ai_resolution_candidate.py', 'tools/train_ai_foreground_bce_candidate.py',
    'tools/cache_ai_resolution_inputs.py', 'tools/ai_foreground_bce_loss.py',
    'tools/ai_positive_dice_loss.py', 'tools/ai_hard_example_loss.py',
    'tools/ai_bounded_hard_weights.py', 'tools/train_ai_presence_candidate.py',
    'tools/ai_presence_model.py', 'tools/ai_cached_dataset.py', 'tools/ai_atomic_io.py',
    'tools/train_reliability_candidate.py', 'tools/cache_ai_training_inputs.py',
    'tools/ai_metrics.py', 'tools/run_experiment.py', 'tools/smoke_ai_hard_candidate.py',
    'medvision_pipeline.py', 'medvision_ai.py',
]


class WeightedTrainingDataset(Dataset):
    def __init__(self, data, weights):
        self.data, self.weights = data, weights
        if set(weights) != {r['image_id'] for r in data.rows}:
            raise ValueError('Exact unique TRAIN weight membership required')
    def __len__(self): return len(self.data)
    def __getitem__(self, index):
        row = self.data.rows[index]
        return (*self.data[index], torch.tensor(self.weights[row['image_id']], dtype=torch.float32), index)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--protocol', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--input-size', type=int, choices=[256, 512], required=True)
    ap.add_argument('--resume', action='store_true')
    args = ap.parse_args()
    protocol_path, out = Path(args.protocol).resolve(), Path(args.out).resolve()
    if ROOT not in protocol_path.parents or ROOT not in out.parents or out.exists() and not args.resume:
        raise ValueError('Workspace registration and exclusive output/strict resume required')
    protocol = json.loads(protocol_path.read_text())
    if (protocol['status'] != 'registered_after_completed_native_failure_analysis'
            or protocol['major_factor'] != 'input_resolution'):
        raise ValueError('Completed native failure analysis and single resolution-factor registration required')
    expected_arm = 'AI_E15_v3_resolution256_reference' if args.input_size == 256 else 'AI_E16_v3_resolution512'
    if out.name != expected_arm or out.name != protocol['reference' if args.input_size == 256 else 'candidate']:
        raise ValueError('Registered resolution arm identity required')
    if protocol['initial_run'] != 'experiments/AI_E14_v3_foreground_BCE5':
        raise ValueError('Registered selected E14 initializer required')
    for source, digest in protocol['input_hashes'].items():
        if p.sha(ROOT/source) != digest: raise ValueError('Registered input changed: ' + source)
    if not set(SOURCES) <= set(protocol['input_hashes']):
        raise ValueError('Every common trainer/cache/loss source must be registered')
    if not torch.cuda.is_available(): raise RuntimeError('Registered CUDA training unavailable')
    common = protocol['common_config']
    required_common = dict(additional_epochs=12, batch_size=2, lr=.0001, seed=42,
        hard_factor=2, presence_weight=0, normal_bce_weight=1, positive_dice_coefficient=1,
        foreground_bce_coefficient=5, global_epochs=list(range(51, 63)))
    if any(common.get(k) != v for k, v in required_common.items()):
        raise ValueError('Registered matched resolution continuation budget/objective required')
    run = ROOT/protocol['initial_run']
    old = json.loads((run/'config.json').read_text()); bundle = json.loads((run/'bundle.json').read_text())
    if json.loads((run/'state.json').read_text())['status'] != 'completed':
        raise ValueError('Completed initializer required')
    if (bundle['epoch'] != 11 or bundle['global_epoch'] != 50 or bundle['output_contract'] != CONTRACT
            or bundle['architecture'] != ARCHITECTURE or old['output_contract'] != CONTRACT
            or old['architecture'] != ARCHITECTURE or old['hard_factor'] != 2
            or old['presence_weight'] != 0 or old['foreground_bce_coefficient'] != 5
            or old['positive_dice_coefficient'] != 1):
        raise ValueError('E14 selected epoch11/global50 hard2/foreground5/Dice1 initializer required')
    manifest = ROOT/old['manifest']; archive = ROOT/'FracAtlas.zip'
    if p.sha(manifest) != old['manifest_sha256'] or p.sha(archive) != old['archive_sha256']:
        raise ValueError('Frozen data identity changed')
    source_resume = run/f"epoch_{bundle['epoch']:03d}_resume.pt"
    initialization = protocol['initialization']
    if (initialization['selected_epoch'] != 11 or initialization['global_epoch'] != 50
            or source_resume.relative_to(ROOT).as_posix() != initialization['snapshot']
            or p.sha(source_resume) != initialization['snapshot_sha256']):
        raise ValueError('Registered selected full initializer changed')
    checkpoint = torch.load(source_resume, map_location='cpu', weights_only=True)
    if (checkpoint['epoch'] != 11 or checkpoint['global_epoch'] != 50 or checkpoint['output_contract'] != CONTRACT
            or checkpoint['manifest_sha256'] != old['manifest_sha256'] or checkpoint['hard_factor'] != 2
            or checkpoint['presence_weight'] != 0 or checkpoint['foreground_bce_coefficient'] != 5):
        raise ValueError('Selected full snapshot/optimizer identity mismatch')
    # Historical E14 full snapshots did not save the positive Dice field; the
    # frozen E14 config and unchanged foreground loss establish coefficient1.
    if checkpoint.get('positive_dice_coefficient', 1) != 1:
        raise ValueError('Initializer positive Dice coefficient changed')
    if p.sha(run/'best_model.pt') != bundle['checkpoint_sha256']:
        raise ValueError('Selected model file changed')
    selected = torch.load(run/'best_model.pt', map_location='cpu', weights_only=True)
    if tensor_digest(checkpoint['model_state_dict']) != tensor_digest(selected):
        raise ValueError('Full snapshot does not reproduce selected model')
    torch.set_num_threads(2); cv2.setNumThreads(1); p.seed_everything(42)
    preprocess = p.PreprocessConfig(**dict(old['preprocess'], size=args.input_size))
    post = p.PostprocessConfig(**old['postprocess'])
    canonical_preprocess = p.PreprocessConfig(size=256, resize='stretch', clahe=True, blur_kernel=3, normalization='unit')
    if old['preprocess'] != asdict(canonical_preprocess) or old['normal_bce_weight'] != 1. or old['loss'] != 'bce_dice':
        raise ValueError('Only input size may change existing preprocessing/objective')
    if set(protocol['caches']) != {'256', '512'}:
        raise ValueError('Both registered resolution caches required')
    registered_cache = protocol['caches'][str(args.input_size)]
    cache = (ROOT/registered_cache['path']).resolve()
    if ROOT not in cache.parents or p.sha(cache/'completion.json') != registered_cache['completion_sha256']:
        raise ValueError('Registered TRAIN cache completion identity changed')
    data = CachedReliabilityDataset(cache, manifest, preprocess, seed=42, elastic=False)
    if (len(data) != 2808 or sum(int(r['fractured']) for r in data.rows) != 493
            or len({r['image_id'] for r in data.rows}) != 2808
            or data.metadata['shape'] != [2808, args.input_size, args.input_size]
            or data.metadata['archive_sha256'] != old['archive_sha256']
            or data.metadata['original_checkpoint_sha256'] != old['original_checkpoint_sha256']):
        raise ValueError('TRAIN distribution/data identity changed')
    if args.input_size == 512 and (data.metadata.get('builder') != 'tools/cache_ai_resolution_inputs.py'
            or data.metadata['source_hashes'].get('tools/cache_ai_resolution_inputs.py') != p.sha(ROOT/'tools/cache_ai_resolution_inputs.py')):
        raise ValueError('Registered native-derived512 producer binding required')
    catalog = ROOT/protocol['hard_catalog']
    if protocol['hard_catalog'] != old['hard_catalog'] or json.loads((catalog/'completion.json').read_text())['status'] != 'completed_TRAIN_hard_catalog_refresh_only':
        raise ValueError('Frozen completed training-only hard catalog required')
    hp = json.loads((catalog/'HARD_POSITIVE_SET.json').read_text())['image_ids']
    hn = json.loads((catalog/'HARD_NEGATIVE_SET.json').read_text())['image_ids']
    if len(hp) != 109 or len(set(hp)) != 109 or len(hn) != 713 or len(set(hn)) != 713:
        raise ValueError('Frozen unique hard109/713 membership required')
    weights = class_normalized_weights(data.rows, hp, hn, 2)
    train = WeightedTrainingDataset(data, weights)
    val = p.FracDataset(archive, manifest, 'val', preprocess)
    if (len(val) != 463 or sum(int(r['fractured']) for r in val.rows) != 83
            or len({r['image_id'] for r in val.rows}) != 463
            or {r['image_id'] for r in data.rows} & {r['image_id'] for r in val.rows}):
        raise ValueError('Validation membership changed or overlaps TRAIN')
    loss_config = p.LossConfig(mode='bce_dice')
    if asdict(loss_config) != old['loss_config']: raise ValueError('Initializer loss configuration changed')
    start_global = bundle['global_epoch']; presence_weight = old['presence_weight']
    config = dict(manifest=old['manifest'], manifest_sha256=old['manifest_sha256'], archive_sha256=old['archive_sha256'],
        original_checkpoint_sha256=p.sha(ROOT/'best_model.pt'), initial_checkpoint=str(source_resume.relative_to(ROOT)),
        initial_checkpoint_sha256=p.sha(source_resume), protocol_sha256=p.sha(protocol_path),
        input_size=args.input_size, cache=registered_cache['path'], cache_completion_sha256=p.sha(cache/'completion.json'),
        output_contract=CONTRACT, architecture=ARCHITECTURE, preprocess=asdict(preprocess), postprocess=asdict(post),
        loss='bce_dice', loss_config=asdict(loss_config), normal_bce_weight=1., presence_weight=presence_weight,
        class_weights=old['class_weights'], hard_factor=2, positive_dice_coefficient=1, foreground_bce_coefficient=5,
        hard_catalog=protocol['hard_catalog'], hard_positive_count=len(hp), hard_negative_count=len(hn), epochs=12,
        warm_start_epoch=start_global, batch_size=2, lr=.0001, seed=42, elastic=False, positive_fraction=None,
        optimizer='Selected full snapshot Adam restored identically in both arms; no scheduler/weight decay; norm clip10',
        sampling='Natural unique one-pass shuffle; bounded per-image loss weights normalized within each source-label class; no duplication',
        source_hashes={source:p.sha(ROOT/source) for source in SOURCES}, device='cuda', torch=torch.__version__, smoke=False,
        cublas_workspace_config=os.environ['CUBLAS_WORKSPACE_CONFIG'],
        selection='Common feasible-first/minimum-normalized TP,TN,Dice,IoU; conservative review alerts and independent masks; earlier ties',
        calibration_fit=False, test_evaluated=False, promotion=False)
    if config['original_checkpoint_sha256'] != old['original_checkpoint_sha256']:
        raise ValueError('Protected original checkpoint changed')
    model = PresenceAttentionUNet().to('cuda')
    model.load_state_dict(checkpoint['model_state_dict'], strict=True)
    if any(v.dtype != torch.float32 for v in model.parameters()): raise ValueError('FP32 model required')
    optimizer = torch.optim.Adam(model.parameters(), lr=.0001)
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    if any(group['lr'] != .0001 for group in optimizer.param_groups): raise ValueError('Initializer learning rate differs')
    initial = dict(full_parameter_sha256=tensor_digest(model.state_dict()),
        optimizer_state_sha256=optimizer_state_digest(optimizer.state_dict()),
        optimizer_snapshot_sha256=p.sha(source_resume), global_epoch=start_global, seed=42,
        input_size=args.input_size, foreground_bce_coefficient=5, positive_dice_coefficient=1, hard_factor=2,
        total_parameters=sum(v.numel() for v in model.parameters()))
    if (initial['full_parameter_sha256'] != initialization['model_parameter_sha256']
            or initial['optimizer_state_sha256'] != initialization['optimizer_state_sha256']):
        raise ValueError('Actual initialized model/Adam differs from registered selected snapshot')
    del checkpoint, selected
    first, best = 1, (-1., -1., -1.)
    if args.resume:
        if json.loads((out/'config.json').read_text()) != config: raise ValueError('Resume config/code/data differs')
        if json.loads((out/'initial_parameters.json').read_text()) != initial:
            raise ValueError('Recorded full initial model/Adam identity changed')
        resumed = torch.load(out/'last.pt', map_location='cuda', weights_only=True)
        if (resumed['output_contract'] != CONTRACT or resumed['manifest_sha256'] != old['manifest_sha256']
                or resumed['hard_factor'] != 2 or resumed['foreground_bce_coefficient'] != 5
                or resumed['positive_dice_coefficient'] != 1 or resumed['input_size'] != args.input_size
                or type(resumed['epoch']) is not int or not 0 <= resumed['epoch'] <= 12
                or resumed['global_epoch'] != 50 + resumed['epoch'] or resumed['presence_weight'] != 0):
            raise ValueError('Resume identity mismatch')
        model.load_state_dict(resumed['model_state_dict'], strict=True)
        optimizer.load_state_dict(resumed['optimizer_state_dict'])
        if any(group['lr'] != .0001 for group in optimizer.param_groups): raise ValueError('Resumed Adam learning rate changed')
        first, best = resumed['epoch'] + 1, tuple(resumed['best_selection_key'])
        records = [json.loads(v) for v in (out/'epochs.jsonl').read_text().splitlines() if v.strip()] if (out/'epochs.jsonl').exists() else []
        if ([r['epoch'] for r in records] != list(range(1, first))
                or any(r['global_epoch'] != 50 + r['epoch'] or r['train_images_seen'] != 2808
                    or r['unique_train_images_seen'] != 2808 or r['input_size'] != args.input_size for r in records)):
            raise ValueError('Checkpoint/log mismatch; no unrecorded epoch may be skipped')
        if args.input_size == 256 and records and records[0]['reference_replay_parity'] != dict(
                validation_exact=True, model_parameter_exact=True, optimizer_state_exact=True):
            raise ValueError('Cannot resume a failed neutral reference replay')
    else:
        out.mkdir(); json_atomic(out/'config.json', config); json_atomic(out/'initial_parameters.json', initial)
        json_atomic(out/'training_example_weights.json', dict(weights=weights, applied=True, factor=2,
            input_size=args.input_size, foreground_bce_coefficient=5, positive_dice_coefficient=1,
            mean_within_each_class=1, positive_total=sum(weights[r['image_id']] for r in data.rows if int(r['fractured'])),
            normal_total=sum(weights[r['image_id']] for r in data.rows if not int(r['fractured']))))
        (out/'source_snapshot').mkdir()
        for source in SOURCES: (out/'source_snapshot'/Path(source).name).write_bytes((ROOT/source).read_bytes())
        (out/'source_snapshot'/protocol_path.name).write_bytes(protocol_path.read_bytes())
        atomic_save(dict(model_state_dict=model.state_dict(), optimizer_state_dict=optimizer.state_dict(), epoch=0,
            global_epoch=start_global, best_selection_key=list(best), output_contract=CONTRACT,
            manifest_sha256=old['manifest_sha256'], presence_weight=presence_weight, hard_factor=2,
            input_size=args.input_size, foreground_bce_coefficient=5, positive_dice_coefficient=1), out/'last.pt')
    started = time.perf_counter()
    for epoch in range(first, 13):
        global_epoch = start_global + epoch; p.seed_everything(42 + global_epoch); data.epoch = global_epoch
        loader = DataLoader(train, batch_size=2, shuffle=True, num_workers=0,
            generator=torch.Generator().manual_seed(42 + global_epoch))
        sums, seen, seen_indices = Counter(), 0, set(); ep_start = time.perf_counter()
        model.train(); torch.cuda.reset_peak_memory_stats()
        for batch, (x, y, valid, positive, example_weight, indices) in enumerate(loader, 1):
            current = indices.tolist()
            if seen_indices.intersection(current) or len(current) != len(set(current)):
                raise ValueError('Repeated source image within epoch')
            seen_indices.update(current)
            x, y, valid, positive, example_weight = [v.to('cuda') for v in (x, y, valid, positive, example_weight)]
            optimizer.zero_grad(set_to_none=True); output = model(x)
            components = foreground_bce_loss(output['mask_logits'], output['presence_logits'], y, valid,
                positive, example_weight, loss_config, presence_weight, 5)
            if not all(torch.isfinite(v).all() for v in components.values()): raise RuntimeError('Nonfinite training loss')
            components['total'].backward()
            grad = torch.nn.utils.clip_grad_norm_(model.parameters(), 10, error_if_nonfinite=True)
            if not presence_weight and any(v.grad is not None for v in model.presence.parameters()):
                raise RuntimeError('Unsupervised head received gradient')
            optimizer.step()
            for key, value in components.items(): sums[key] += float(value.detach()) * len(x)
            seen += len(x)
            if batch == 1 or batch % 100 == 0 or batch == len(loader):
                state = dict(status='training', epoch=epoch, global_epoch=global_epoch, input_size=args.input_size,
                    batch=batch, batches=len(loader), loss_components={k:v/seen for k,v in sums.items()},
                    gradient_norm=float(grad), elapsed_seconds=time.perf_counter()-ep_start,
                    unique_train_images_seen=len(seen_indices), smoke=False, test_evaluated=False, promotion=False)
                json_atomic(out/'state.json', state); print(json.dumps(state), flush=True)
        if seen != 2808 or seen_indices != set(range(2808)): raise ValueError('Incomplete one-pass TRAIN coverage')
        json_atomic(out/'state.json', dict(status='validating', epoch=epoch, global_epoch=global_epoch,
            input_size=args.input_size, smoke=False, test_evaluated=False))
        metrics, cases = validate(model, val, preprocess, post, 'cuda', bool(presence_weight))
        parity = None
        if args.input_size == 256 and epoch == 1:
            expected = protocol['reference_replay_parity']['51']
            actual_model_digest = tensor_digest(model.state_dict())
            actual_optimizer_digest = optimizer_state_digest(optimizer.state_dict())
            parity = dict(validation_exact=metrics == expected['validation'],
                model_parameter_exact=actual_model_digest == expected['model_parameter_sha256'],
                optimizer_state_exact=actual_optimizer_digest == expected['optimizer_state_sha256'])
            json_atomic(out/'reference_replay_epoch_001.json', dict(epoch=epoch, global_epoch=global_epoch,
                checks=parity, actual_model_parameter_sha256=actual_model_digest,
                actual_optimizer_state_sha256=actual_optimizer_digest, actual_validation=metrics, expected=expected))
            if not all(parity.values()):
                raise ValueError('Neutral256 control failed exact E14 global51 replay; preserve evidence, do not continue')
        key = selection_key(metrics); selected = key > best
        if selected: best = key
        snapshot = dict(model_state_dict=model.state_dict(), optimizer_state_dict=optimizer.state_dict(),
            epoch=epoch, global_epoch=global_epoch, best_selection_key=list(best), output_contract=CONTRACT,
            manifest_sha256=old['manifest_sha256'], presence_weight=presence_weight, hard_factor=2,
            input_size=args.input_size, foreground_bce_coefficient=5, positive_dice_coefficient=1)
        atomic_save(snapshot, out/f'epoch_{epoch:03d}_resume.pt'); atomic_save(snapshot, out/'last.pt')
        if selected:
            atomic_save(model.state_dict(), out/'best_model.pt')
            json_atomic(out/'best_validation.json', dict(epoch=epoch, global_epoch=global_epoch,
                metrics=metrics, selection_key=list(key)))
            json_atomic(out/'best_validation_cases.json', cases)
            json_atomic(out/'bundle.json', dict(output_contract=CONTRACT, architecture=ARCHITECTURE,
                checkpoint='best_model.pt', checkpoint_sha256=p.sha(out/'best_model.pt'),
                epoch=epoch, global_epoch=global_epoch, manifest_sha256=old['manifest_sha256'],
                preprocess=asdict(preprocess), postprocess=asdict(post), input_size=args.input_size,
                presence_weight=presence_weight, hard_factor=2, foreground_bce_coefficient=5,
                positive_dice_coefficient=1, calibration_status='Unselected research; no calibration/freeze/promotion'))
        record = dict(epoch=epoch, global_epoch=global_epoch, input_size=args.input_size,
            loss_components={k:v/seen for k,v in sums.items()}, validation=metrics,
            selection_key=list(key), best_selection_key=list(best), selected=selected,
            train_images_seen=seen, unique_train_images_seen=len(seen_indices), epoch_seconds=time.perf_counter()-ep_start,
            cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(), cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved(),
            process_rss_bytes=psutil.Process().memory_info().rss, reference_replay_parity=parity,
            smoke=False, test_evaluated=False, promotion=False)
        with (out/'epochs.jsonl').open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(record, allow_nan=False) + '\n'); handle.flush(); os.fsync(handle.fileno())
        print(json.dumps(record), flush=True)
        for source, digest in protocol['input_hashes'].items():
            if p.sha(ROOT/source) != digest: raise ValueError('Registered guard changed: ' + source)
    json_atomic(out/'state.json', dict(status='completed', epochs_finished=12,
        input_size=args.input_size, elapsed_seconds=time.perf_counter()-started,
        best_selection_key=list(best), smoke=False, test_evaluated=False, promotion=False))


if __name__ == '__main__': main()
