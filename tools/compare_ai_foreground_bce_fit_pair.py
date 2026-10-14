"""Compare completed E13/E14 raw TRAIN-grid fits using saved CPU metadata only.

Both full training runs and both read-only fit completions are mandatory before
any fit cases or checkpoint bytes are read. Four unique completed .pt files are
streamed for SHA-256 identity; no arrays, images or model tensors are decoded.
Never trains, runs inference, reads CAL/test images or promotes a candidate.
"""
import argparse
import datetime
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# Frozen, standard-library-only metadata helpers; importing does not run main.
from tools.compare_ai_positive_dice_fit_pair import (
    MetadataReader, paired_transitions, sha, summarize, validate_case, workspace_path)


PROTOCOL = 'experiments/session_20261007_ai_loop_01/FOREGROUND_BCE_EXPERIMENT_PROTOCOL.json'
PROTOCOL_SHA = '250bcd50e0ba8463d6da746e469222b41a82b8114ec1add1aece6fd04850e523'
MANIFEST = 'experiments/data_v3_reliability_20261007/manifest.json'
MANIFEST_SHA = '4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318'
DEFAULT_OUT = 'experiments/AI_FOREGROUND_BCE_FIT_PAIR_E13_E14_20261009'
ARMS = {'E13': ('AI_LEARNING_FIT_E13_v3_foreground_BCE_reference', 'AI_E13_v3_foreground_BCE_reference', 1),
        'E14': ('AI_LEARNING_FIT_E14_v3_foreground_BCE5', 'AI_E14_v3_foreground_BCE5', 5)}
SMOKE_CONFIG_SHA = '9d659723853f608dee9a4dcc37ff0e4072216d1f159f909409cb78abd9821b07'
SMOKE_COMPLETION_SHA = '0a53dd320612836d55adac0fdf532322e493353f191b20aeee9142e90340af48'
ADAPTED_SOURCE = 'tools/compare_ai_positive_dice_fit_pair.py'
ADAPTED_SOURCE_SHA = '5e5a0a46dfdf2e0391741c76dff087111d5fa321d8eaa683957ba8c1a76547ce'
INITIAL_SNAPSHOT_SHA = '8fb8cbda71e14ae61a00e89dcaf9ad69a676f0e05ffa34bf4a2578fffea6741b'
REPLAY_CHECKS = {'validation_exact': True, 'model_parameter_exact': True, 'optimizer_state_exact': True}


def validate_grid_case(case, row):
    validate_case(case, row)
    if any(type(case[k]) is not bool for k in ('positive', 'prediction_present', 'review_alert_present', 'zero_overlap_positive')):
        raise ValueError('Explicit boolean saved source/mask flags required')
    if case['head_mask_group'] != 'reference_mask_only':
        raise ValueError('Independent unsupervised mask-only TRAIN fit required')
    if sum(case[k] for k in ('tp_pixels', 'fp_pixels', 'fn_pixels')) > 256 * 256:
        raise ValueError('Saved independent binary pixels exceed the grid')
    score = case['case_score']
    if not math.isfinite(score) or not 0 <= score <= 1 or case['prediction_present'] != (score >= .5):
        raise ValueError('Saved grid mask alert and maximum-pixel proxy disagree')


def validate_saved_metrics(metrics, cases):
    if (not metrics['no_optimizer_steps'] or metrics['model_improvement_claim']
            or any(metrics[k] for k in ('validation_images_read', 'calibration_images_read', 'test_images_read'))
            or metrics['head_classification'] is not None or metrics['uncalibrated_head_diagnostic'] is not None):
        raise ValueError('Completed TRAIN-only mask metrics required')
    positive = [c for c in cases if c['positive']]
    normal = [c for c in cases if not c['positive']]
    cm = dict(tp=sum(c['prediction_present'] for c in positive), fn=sum(not c['prediction_present'] for c in positive),
              fp=sum(c['prediction_present'] for c in normal), tn=sum(not c['prediction_present'] for c in normal))
    for name in ('mask_classification', 'conservative_review_classification'):
        m = metrics[name]
        if m['n'] != 2808 or m['positive'] != 493 or m['normal'] != 2315 or m['confusion_matrix'] != cm:
            raise ValueError('Completed fit metrics differ from the exact saved cases')
    s = metrics['independent_grid_segmentation']
    if (s['n_positive'] != 493 or s['pixel_counts'] != {k: sum(c[k + '_pixels'] for c in cases) for k in ('tp', 'fp', 'fn')}
            or not math.isclose(s['mean_positive_dice'], sum(c['dice'] for c in positive) / 493, rel_tol=1e-12, abs_tol=1e-12)
            or not math.isclose(s['mean_positive_iou'], sum(c['iou'] for c in positive) / 493, rel_tol=1e-12, abs_tol=1e-12)
            or metrics['positive_zero_overlap_masks'] != sum(c['tp_pixels'] == 0 for c in positive)):
        raise ValueError('Completed fit overlap metrics disagree with saved grid pixels')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default=DEFAULT_OUT)
    args = parser.parse_args()
    out = workspace_path(args.out)
    if out != workspace_path(DEFAULT_OUT) or out.exists():
        raise ValueError('Registered new exclusive foreground TRAIN-fit output required')
    reader = MetadataReader()
    # Gate BOTH arms before any case results or checkpoint-file bytes are read.
    for fit, run, _ in ARMS.values():
        marker = workspace_path('experiments/' + fit + '/completion.json')
        state_path = workspace_path('experiments/' + run + '/state.json')
        if not marker.exists() or not state_path.exists():
            raise ValueError('WAIT: both full runs and completed raw TRAIN fits are required; no partial cases read')
        done, state = reader.read(marker), reader.read(state_path)
        if (done['status'] != 'completed_read_only_TRAIN_fit' or done['train_cases'] != 2808
                or not done['model_tensors_unchanged'] or not done['no_optimizer_steps']
                or any(done[k] for k in ('validation_images_read', 'calibration_images_read', 'test_images_read'))):
            raise ValueError('Completed unchanged TRAIN-only fit required')
        if (state['status'] != 'completed' or state['epochs_finished'] != 12
                or state['smoke'] or state['test_evaluated'] or state['promotion']):
            raise ValueError('WAIT: both registered 12-epoch runs must finish before case or checkpoint reads')
    reader.record(__file__)
    protocol = reader.read(PROTOCOL)
    if reader.record(PROTOCOL) != PROTOCOL_SHA:
        raise ValueError('Registered foreground-BCE protocol identity changed')
    common, factor = protocol['common_config'], protocol['factor']
    if ((protocol['reference'], protocol['candidate']) != (ARMS['E13'][1], ARMS['E14'][1])
            or protocol['major_factor'] != 'foreground_pixel_bce_coefficient'
            or factor['reference'] != 1 or factor['candidate'] != 5
            or common['additional_epochs'] != 12 or common['global_epochs'] != list(range(40, 52))
            or common['batch_size'] != 2 or common['seed'] != 42 or common['lr'] != .0001
            or common['hard_factor'] != 2 or common['presence_weight'] != 0
            or common['normal_bce_weight'] != 1 or common['positive_dice_coefficient'] != 1
            or not all(factor[k] for k in ('background_BCE_unchanged', 'normal_image_loss_unchanged', 'Dice_unchanged', 'no_duplicate_images'))
            or protocol['calibration_fit'] or protocol['test_images_read'] or protocol['promotion']):
        raise ValueError('Exact registered single foreground BCE factor and global 40-51 contract required')
    protocol_hashes = {workspace_path(p): digest for p, digest in protocol['input_hashes'].items()}

    def registered_read(path):
        value = reader.read(path)
        if reader.record(path) != protocol_hashes.get(workspace_path(path)):
            raise ValueError('Frozen registered metadata identity changed: ' + str(path))
        return value

    if (reader.record(ADAPTED_SOURCE) != ADAPTED_SOURCE_SHA
            or protocol_hashes.get(workspace_path(ADAPTED_SOURCE)) != ADAPTED_SOURCE_SHA):
        raise ValueError('Frozen imported comparator provenance changed')
    initializer = protocol['initialization']
    if (protocol['initial_run'] != 'experiments/AI_E11_v3_positive_Dice_reference'
            or initializer['selected_epoch'] != 9 or initializer['global_epoch'] != 39
            or initializer['snapshot'] != 'experiments/AI_E11_v3_positive_Dice_reference/epoch_009_resume.pt'
            or initializer['snapshot_sha256'] != INITIAL_SNAPSHOT_SHA
            or protocol_hashes.get(workspace_path(initializer['snapshot'])) != INITIAL_SNAPSHOT_SHA):
        raise ValueError('Exact selected full E11 epoch 9/global 39 initializer required')
    init_run = protocol['initial_run']
    init_config = registered_read(init_run + '/config.json')
    init_state = registered_read(init_run + '/state.json')
    init_bundle = registered_read(init_run + '/bundle.json')
    if (init_state['status'] != 'completed' or init_state['epochs_finished'] != 12 or init_state['smoke']
            or init_bundle['epoch'] != 9 or init_bundle['global_epoch'] != 39
            or init_bundle['hard_factor'] != 2 or init_bundle['presence_weight'] != 0 or init_bundle['positive_dice_coefficient'] != 1
            or init_config['hard_factor'] != 2 or init_config['normal_bce_weight'] != 1
            or init_config['presence_weight'] != 0 or init_config['positive_dice_coefficient'] != 1 or init_config['loss'] != 'bce_dice'
            or init_bundle['checkpoint_sha256'] != protocol_hashes.get(workspace_path(init_run + '/best_model.pt'))):
        raise ValueError('Frozen selected E11 configuration/bundle identity changed')
    checkpoint_file_hashes = {}
    for name, expected in ((initializer['snapshot'], INITIAL_SNAPSHOT_SHA),
                           (init_run + '/best_model.pt', init_bundle['checkpoint_sha256'])):
        digest = reader.record(name)  # Checkpoint byte hashing only; no tensors.
        if digest != expected:
            raise ValueError('Completed selected E11 checkpoint-file identity changed')
        checkpoint_file_hashes[name] = digest
    smoke_path = protocol['smoke_output']
    smoke_config = reader.read(smoke_path + '/config.json')
    smoke_done = reader.read(smoke_path + '/completion.json')
    if (reader.record(smoke_path + '/config.json') != SMOKE_CONFIG_SHA
            or reader.record(smoke_path + '/completion.json') != SMOKE_COMPLETION_SHA
            or smoke_config['protocol_sha256'] != PROTOCOL_SHA
            or smoke_config['initial_snapshot_sha256'] != INITIAL_SNAPSHOT_SHA
            or smoke_config['selected_checkpoint_sha256'] != init_bundle['checkpoint_sha256']
            or smoke_config['initial_parameter_sha256'] != initializer['model_parameter_sha256']
            or smoke_config['initial_optimizer_state_sha256'] != initializer['optimizer_state_sha256']
            or smoke_config['coefficients'] != [1, 5] or smoke_config['hard_factor'] != 2
            or smoke_config['positive_dice_coefficient'] != 1
            or smoke_done['status'] != 'passed_TRAIN_only_foreground_bce_smoke'
            or not all(smoke_done[k] for k in ('full_matched_initialization', 'coefficient1_exact_model_optimizer_parity',
                'coefficient5_finite_updates', 'normal_and_positive_background_output_gradients_preserved',
                'Dice_and_presence_preserved', 'coefficient5_analytic_offset_gradient_parity'))
            or any(smoke_done[k] for k in ('validation_images_read', 'calibration_images_read', 'test_images_read', 'promotion'))):
        raise ValueError('Actual full model/Adam and neutral-parity smoke identity changed')
    smoke_models = {arm['initial_parameter_sha256'] for arm in smoke_done['arms']}
    smoke_optimizers = {arm['initial_optimizer_state_sha256'] for arm in smoke_done['arms']}
    if (len(smoke_done['arms']) != 3 or smoke_models != {initializer['model_parameter_sha256']}
            or smoke_optimizers != {initializer['optimizer_state_sha256']}
            or not all(arm['full_restore_passed'] for arm in smoke_done['arms'])):
        raise ValueError('Three smoke arms did not independently restore the same full initializer')
    for source, digest in smoke_config['source_hashes'].items():
        if reader.record(source) != digest or protocol_hashes.get(workspace_path(source)) != digest:
            raise ValueError('Frozen smoke source identity changed')
    manifest = registered_read(MANIFEST)
    if reader.record(MANIFEST) != MANIFEST_SHA:
        raise ValueError('Frozen TRAIN manifest identity changed')
    train_rows = [r for r in manifest['rows'] if r['split'] == 'train']
    rows = {r['image_id']: r for r in train_rows}
    if (len(train_rows) != len(rows) or len(rows) != 2808
            or any(int(r['fractured']) not in (0, 1) for r in train_rows)
            or sum(int(r['fractured']) for r in train_rows) != 493):
        raise ValueError('Exact unique TRAIN 2808 with 493 explicit positive labels required')
    catalog = protocol['hard_catalog']
    if registered_read(catalog + '/completion.json')['status'] != 'completed_TRAIN_hard_catalog_refresh_only':
        raise ValueError('Registered completed TRAIN-only hard catalog required')
    hp = registered_read(catalog + '/HARD_POSITIVE_SET.json')['image_ids']
    hn = registered_read(catalog + '/HARD_NEGATIVE_SET.json')['image_ids']
    for ids, count, label in ((hp, 109, 1), (hn, 713, 0)):
        if (len(ids) != len(set(ids)) or len(ids) != count or not set(ids) <= set(rows)
                or any(int(rows[i]['fractured']) != label for i in ids)):
            raise ValueError('Frozen hard count/unique TRAIN membership/source labels changed')
    strata = {'hard_positive': set(hp),
              'ordinary_positive': {i for i, r in rows.items() if int(r['fractured'])} - set(hp),
              'hard_negative': set(hn),
              'ordinary_negative': {i for i, r in rows.items() if not int(r['fractured'])} - set(hn)}
    if set.union(*strata.values()) != set(rows) or sum(map(len, strata.values())) != 2808:
        raise ValueError('Four hard/ordinary strata must partition the exact TRAIN sources')
    fits, configs, fit_configs, initializations, model_metadata = {}, {}, {}, {}, {}
    verified_sources, replay_evidence = [], []
    for arm, (fit, run, coefficient) in ARMS.items():
        prefix, run_prefix = 'experiments/' + fit, 'experiments/' + run
        config, fit_config = reader.read(run_prefix + '/config.json'), reader.read(prefix + '/config.json')
        bundle = reader.read(run_prefix + '/bundle.json')
        if (config['foreground_bce_coefficient'] != coefficient or config['positive_dice_coefficient'] != 1
                or config['hard_factor'] != 2 or config['presence_weight'] != 0 or config['normal_bce_weight'] != 1
                or config['protocol_sha256'] != PROTOCOL_SHA or config['manifest_sha256'] != MANIFEST_SHA
                or config['hard_catalog'] != catalog or config['hard_positive_count'] != 109 or config['hard_negative_count'] != 713
                or config['epochs'] != 12 or config['warm_start_epoch'] != 39 or config['batch_size'] != 2
                or config['lr'] != .0001 or config['seed'] != 42 or config['elastic']
                or config['positive_fraction'] is not None or config['smoke'] or config['calibration_fit'] or config['test_evaluated'] or config['promotion']):
            raise ValueError('Registered foreground BCE arm or fixed common configuration changed')
        unchanged_keys = ('manifest', 'manifest_sha256', 'archive_sha256', 'original_checkpoint_sha256',
                          'cache', 'cache_completion_sha256', 'output_contract', 'architecture', 'preprocess', 'postprocess',
                          'loss', 'loss_config', 'normal_bce_weight', 'presence_weight', 'class_weights', 'hard_factor',
                          'positive_dice_coefficient', 'batch_size', 'lr', 'seed', 'elastic', 'positive_fraction',
                          'optimizer', 'sampling', 'device', 'torch', 'cublas_workspace_config', 'selection')
        if any(config[k] != init_config[k] for k in unchanged_keys):
            raise ValueError('Declared common configuration differs from frozen E11 initializer')
        epochs = reader.read(run_prefix + '/epochs.jsonl', lines=True)
        if ([r['epoch'] for r in epochs] != list(range(1, 13))
                or [r['global_epoch'] for r in epochs] != list(range(40, 52))
                or any(r['train_images_seen'] != 2808 or r['unique_train_images_seen'] != 2808
                       or r['smoke'] or r['test_evaluated'] or r['promotion'] for r in epochs)):
            raise ValueError('Complete global 40-51 unique natural TRAIN epoch coverage required')
        if arm == 'E13':
            for record in epochs[:3]:
                replay = reader.read(run_prefix + f"/reference_replay_epoch_{record['epoch']:03d}.json")
                expected = protocol['reference_replay_parity'][str(record['global_epoch'])]
                if (record['reference_replay_parity'] != REPLAY_CHECKS or replay['checks'] != REPLAY_CHECKS
                        or replay['epoch'] != record['epoch'] or replay['global_epoch'] != record['global_epoch']
                        or replay['expected'] != expected or replay['actual_validation'] != expected['validation']
                        or record['validation'] != expected['validation']
                        or replay['actual_model_parameter_sha256'] != expected['model_parameter_sha256']
                        or replay['actual_optimizer_state_sha256'] != expected['optimizer_state_sha256']):
                    raise ValueError('Saved neutral-control model/Adam/metrics replay did not pass exactly')
                replay_evidence.append(replay)
        elif any(r['reference_replay_parity'] is not None for r in epochs):
            raise ValueError('Candidate must not be mislabeled as a neutral replay')
        if (workspace_path(fit_config['run']) != workspace_path(run_prefix)
                or fit_config['augmentation'] or fit_config['mask_gated'] or not fit_config['no_optimizer_steps']
                or any(fit_config[k] for k in ('validation_images_read', 'calibration_images_read', 'test_images_read'))
                or fit_config['manifest_sha256'] != MANIFEST_SHA
                or fit_config['checkpoint_sha256'] != bundle['checkpoint_sha256'] or fit_config['epoch'] != bundle['epoch']
                or bundle['global_epoch'] != 39 + bundle['epoch'] or not 1 <= bundle['epoch'] <= 12
                or bundle['foreground_bce_coefficient'] != coefficient or bundle['hard_factor'] != 2 or bundle['presence_weight'] != 0
                or bundle['manifest_sha256'] != MANIFEST_SHA or bundle['checkpoint'] != 'best_model.pt'):
            raise ValueError('Completed raw fit does not use the final selected bundle identity')
        checkpoint_name = run_prefix + '/best_model.pt'
        digest = reader.record(checkpoint_name)  # Stream completed bytes only.
        if digest != bundle['checkpoint_sha256']:
            raise ValueError('Completed selected checkpoint byte identity differs from fit/bundle')
        checkpoint_file_hashes[checkpoint_name] = digest
        for k in ('preprocess', 'output_contract'):
            if fit_config[k] != config[k] or bundle[k] != config[k]:
                raise ValueError('Fit/run/bundle output geometry or contract differs')
        if fit_config['cache'] != config['cache'] or bundle['postprocess'] != config['postprocess'] or bundle['architecture'] != config['architecture']:
            raise ValueError('Fit/run/bundle cache, architecture or threshold differs')
        if any(fit_config['source_hashes'].get(s) != d for s, d in config['source_hashes'].items()):
            raise ValueError('Completed fit uses different recorded training sources')
        for source, source_digest in fit_config['source_hashes'].items():
            if reader.record(source) != source_digest or protocol_hashes.get(workspace_path(source)) != source_digest:
                raise ValueError('Completed fit source differs from frozen registration: ' + source)
            verified_sources.append(dict(arm=arm, source=source, sha256=source_digest))
        if (workspace_path(config['initial_checkpoint']) != workspace_path(initializer['snapshot'])
                or config['initial_checkpoint_sha256'] != INITIAL_SNAPSHOT_SHA):
            raise ValueError('Registered initial full snapshot identity differs')
        initial = reader.read(run_prefix + '/initial_parameters.json')
        if (initial['optimizer_snapshot_sha256'] != INITIAL_SNAPSHOT_SHA or initial['global_epoch'] != 39 or initial['seed'] != 42
                or initial['full_parameter_sha256'] != initializer['model_parameter_sha256']
                or initial['optimizer_state_sha256'] != initializer['optimizer_state_sha256']
                or initial['total_parameters'] != 31388070):
            raise ValueError('Actual initial full model/Adam metadata differs from registered smoke')
        weights = reader.read(run_prefix + '/training_example_weights.json')
        if (weights['factor'] != 2 or weights['foreground_bce_coefficient'] != coefficient or not weights['applied']
                or weights['mean_within_each_class'] != 1 or not math.isclose(weights['positive_total'], 493, rel_tol=1e-12)
                or not math.isclose(weights['normal_total'], 2315, rel_tol=1e-12) or set(weights['weights']) != set(rows)):
            raise ValueError('Saved frozen hard-factor2 TRAIN weight metadata differs')
        for image_id, row in rows.items():
            count, hard = (493, strata['hard_positive']) if int(row['fractured']) else (2315, strata['hard_negative'])
            expected_weight = (2 if image_id in hard else 1) / ((count + len(hard)) / count)
            value = weights['weights'][image_id]
            if not math.isfinite(value) or not math.isclose(value, expected_weight, rel_tol=1e-12):
                raise ValueError('Hard-factor2 weights differ from registered within-class normalization')
        cases = reader.read(prefix + '/train_cases.jsonl', lines=True)
        by_id = {c['image_id']: c for c in cases}
        if len(cases) != len(by_id) or set(by_id) != set(rows):
            raise ValueError('Exact unique 2808 TRAIN-fit case IDs required')
        for image_id, case in by_id.items():
            validate_grid_case(case, rows[image_id])
        validate_saved_metrics(reader.read(prefix + '/metrics.json'), cases)
        fits[arm], configs[arm], fit_configs[arm], initializations[arm] = by_id, config, fit_config, initial
        model_metadata[arm] = dict(run=run_prefix, fit=prefix, hard_factor=2, positive_dice_coefficient=1,
            foreground_bce_coefficient=coefficient, checkpoint_sha256=digest, selected_epoch=bundle['epoch'],
            selected_global_epoch=bundle['global_epoch'], cases_sha256=reader.record(prefix + '/train_cases.jsonl'))
    if {k: v for k, v in configs['E13'].items() if k != 'foreground_bce_coefficient'} != {k: v for k, v in configs['E14'].items() if k != 'foreground_bce_coefficient'}:
        raise ValueError('Uncontrolled training configuration difference beyond foreground BCE coefficient')
    ignored_fit = {'run', 'checkpoint_sha256', 'epoch'}
    if {k: v for k, v in fit_configs['E13'].items() if k not in ignored_fit} != {k: v for k, v in fit_configs['E14'].items() if k not in ignored_fit}:
        raise ValueError('Uncontrolled raw TRAIN-fit configuration difference')
    if initializations['E13'] != initializations['E14']:
        raise ValueError('Actual full model/Adam initialization metadata differs between arms')
    if any(fits['E13'][i]['tp_pixels'] + fits['E13'][i]['fn_pixels'] != fits['E14'][i]['tp_pixels'] + fits['E14'][i]['fn_pixels'] for i in rows):
        raise ValueError('Same-ID saved grid target areas differ')
    if len(checkpoint_file_hashes) != 4:
        raise ValueError('Exactly four unique completed checkpoint-file byte hashes required')
    cache = configs['E13']['cache']
    cache_done = registered_read(str(Path(cache) / 'completion.json'))
    cache_rows = registered_read(str(Path(cache) / 'rows.json'))
    cache_verification = registered_read(str(Path(cache) / 'verification.json'))
    if (cache_done['status'] != 'completed_exact_train_cache' or cache_done['manifest_sha256'] != MANIFEST_SHA
            or cache_done['shape'] != [2808, 256, 256] or not cache_done['all_written_tensors_bit_exact']
            or cache_done['preprocess'] != configs['E13']['preprocess'] or cache_rows != train_rows
            or configs['E13']['cache_completion_sha256'] != reader.record(Path(cache) / 'completion.json')
            or not all(all(v['exact_float32_parity'].values()) for v in cache_verification)):
        raise ValueError('Frozen shared TRAIN-grid cache metadata differs')
    summaries = {name: {arm: summarize([fits[arm][i] for i in sorted(ids)], rows) for arm in ARMS} for name, ids in strata.items()}
    changes = {name: paired_transitions(ids, fits['E13'], fits['E14'], 'positive' in name) for name, ids in strata.items()}
    for name, transition in changes.items():
        if 'positive' in name:
            transition['wrong_region_to_any_GT_overlap'] = transition.pop('wrong_region_to_useful_overlap')
            transition['any_GT_overlap_to_wrong_region'] = transition.pop('useful_overlap_to_wrong_region')
    deltas = {}
    for name, arms in summaries.items():
        left, right = arms['E13'], arms['E14']
        keys = ['mask_alerts', 'empty_masks'] + (['mean_Dice', 'mean_IoU', 'any_GT_overlap', 'zero_GT_overlap',
            'nonempty_wrong_region', 'Dice_below_0_2', 'pixel_recall'] if 'positive' in name else ['normal_FP', 'normal_TN', 'false_positive_rate'])
        deltas[name] = {k: right[k] - left[k] for k in keys}
        deltas[name]['pixel_counts'] = {k: right['pixel_counts'][k] - left['pixel_counts'][k] for k in ('tp', 'fp', 'fn')}
    limitations = [
        'Unaugmented TRAIN grid fit is not native validation acceptance, locked-test performance or clinical generalization.',
        'Persistent hard 109/713 were selected from E7/E8 TRAIN errors. Their reused selection is not an independent difficult-case test.',
        'Related-image group IDs are conservative candidates, not verified patients/studies. Existing decoded-exact repetition is not new resampling.',
        'Independent threshold 0.5 grid masks can trigger a case alert with zero target overlap. Any target overlap does not establish adequate localization.',
        'Frozen cache metadata and same-ID saved target areas match. Stored array checksums are recorded; no target arrays or per-case target bitmaps were reread or decoded.',
        'Four unique completed checkpoint files (E11 selected full/best and E13/E14 selected best) are streamed for byte hashes only. No tensors or current Adam state are independently loaded.',
        'Actual initializer metadata matches the registered three-arm smoke model/Adam digests. First three E13 replay JSONs must pass exact prior E11 model/Adam/validation parity.',
        'Coefficient 1 is matched continuation with hard factor 2 and positive Dice coefficient 1 retained. Weighted raw loss scalars are not compared as quality metrics.',
        'Selected additional/global epochs may differ under the unchanged selection rule. This is a selected-model comparison, not necessarily a same-epoch effect.',
        'One seed; clinical subtle/nondisplaced labels, verified patient/view identifiers, radiologist adjudication and external validation are unavailable.',
        'Dice 0.2 and a Dice change of 0.02 are descriptive analysis cutoffs, not clinical adequacy thresholds.',
        'No promotion or next intervention is selected here. Completed native audits and actual failure reviews remain required.']
    reader.assert_unchanged()
    result = dict(status='completed_saved_TRAIN_grid_foreground_BCE_fit_pair_comparison',
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), source_sha256=sha(__file__),
        protocol_sha256=PROTOCOL_SHA, manifest_sha256=MANIFEST_SHA, verified_input_hashes=reader.inputs,
        verified_recorded_sources=verified_sources, unique_TRAIN_count=2808, positive_sources=493, normal_sources=2315,
        hard_positive_count=109, hard_negative_count=713, exact_unique_membership_labels_groups_verified=True,
        shared_frozen_grid_cache_verified=True, same_ID_grid_target_areas_verified=True,
        only_training_config_difference='foreground_bce_coefficient 1 versus 5', hard_factor=2, positive_dice_coefficient=1,
        full_global40_51_unique_epoch_coverage_verified=True, initial_metadata_equal=True,
        initializer_snapshot_sha256=INITIAL_SNAPSHOT_SHA, actual_smoke_initial_model_digest=initializer['model_parameter_sha256'],
        actual_smoke_initial_optimizer_digest=initializer['optimizer_state_sha256'], reference_replay_evidence=replay_evidence,
        adapted_source_sha256=ADAPTED_SOURCE_SHA, completed_checkpoint_file_byte_hashes=checkpoint_file_hashes,
        model_metadata=model_metadata, initial_parameters=initializations['E13'], registered_grid_array_checksums=cache_done['cache_hashes'],
        summaries=summaries, candidate_minus_reference=deltas, same_ID_transitions=changes, limitations=limitations,
        new_image_reads=0, new_mask_array_reads=0, checkpoint_tensor_loads=0, checkpoint_file_byte_reads_performed=True,
        unique_checkpoint_files_byte_hashed=4, new_predictions=0, GPU_work_performed=False, inference_performed=False,
        calibration_images_read=0, test_images_read=0, model_trained=False, promotion=False, next_factor_selected=False)
    lines = ['# Completed E13/E14 TRAIN foreground BCE comparison', '',
        'Saved CPU metadata analysis of both completed selected models. Four checkpoint files were streamed for byte identity; no tensors were loaded. No new images, target arrays, inference, GPU or CAL/test access.', '',
        'All 2,808 unique TRAIN sources, source labels/groups, frozen hard 109/713 memberships, recorded versions and shared grid metadata passed. Both arms independently restored the selected E11 epoch 9 / global 39 full model and Adam. The coefficient-1 first three epochs passed the registered saved replay checks.', '',
        '| Model | Foreground BCE coefficient (hard 2 / positive Dice 1 fixed) | Selected additional / global epoch |', '| --- | --- | --- |']
    for arm, item in model_metadata.items():
        lines.append(f"| {arm} | {item['foreground_bce_coefficient']} | {item['selected_epoch']} / {item['selected_global_epoch']} |")
    lines += ['', '| Positive stratum | Model | Sources / groups / exact hashes | Dice / IoU | Alerts | Empty | Wrong region | Any GT overlap | Dice < 0.2 |', '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for name in ('hard_positive', 'ordinary_positive'):
        for arm, s in summaries[name].items():
            lines.append(f"| {name.replace('_', ' ')} | {arm} | {s['images']} / {s['conservative_related_groups']} / {s['distinct_decoded_hashes']} | {s['mean_Dice']:.6f} / {s['mean_IoU']:.6f} | {s['mask_alerts']} | {s['empty_masks']} | {s['nonempty_wrong_region']} | {s['any_GT_overlap']} | {s['Dice_below_0_2']} |")
    lines += ['', '| Normal stratum | Model | Sources / groups / exact hashes | FP / TN | FP rate | FP grid pixels |', '| --- | --- | --- | --- | --- | --- |']
    for name in ('hard_negative', 'ordinary_negative'):
        for arm, s in summaries[name].items():
            lines.append(f"| {name.replace('_', ' ')} | {arm} | {s['images']} / {s['conservative_related_groups']} / {s['distinct_decoded_hashes']} | {s['normal_FP']} / {s['normal_TN']} | {s['false_positive_rate']:.2%} | {s['pixel_counts']['fp']} |")
    lines += ['', '| Positive stratum | Model | TP / FP / FN grid pixels | Pixel precision / recall |', '| --- | --- | --- | --- |']
    for name in ('hard_positive', 'ordinary_positive'):
        for arm, s in summaries[name].items():
            precision = f"{s['pixel_precision']:.4f}" if s['pixel_precision'] is not None else 'undefined'
            p = s['pixel_counts']
            lines.append(f"| {name.replace('_', ' ')} | {arm} | {p['tp']} / {p['fp']} / {p['fn']} | {precision} / {s['pixel_recall']:.4f} |")
    lines += ['', 'Paired transitions are E13 reference to E14 candidate:', '',
        '| Stratum | Alerts added / removed | FP pixels increased / decreased (cases) | GT overlap gained / lost | Dice gain / loss > 0.02 | Dice 0.2 crossed up / down |', '| --- | --- | --- | --- | --- | --- |']
    for name, t in changes.items():
        positive = 'positive' in name
        overlap = f"{t['GT_overlap_gained']['n']} / {t['GT_overlap_lost']['n']}" if positive else 'not applicable'
        dice = f"{t['Dice_gain_gt_0_02']['n']} / {t['Dice_loss_gt_0_02']['n']}" if positive else 'not applicable'
        crossing = f"{t['cross_Dice_0_2_up']['n']} / {t['cross_Dice_0_2_down']['n']}" if positive else 'not applicable'
        lines.append(f"| {name.replace('_', ' ')} | {t['mask_alert_gained']['n']} / {t['mask_alert_removed']['n']} | {t['FP_grid_pixels_increased']['n']} / {t['FP_grid_pixels_decreased']['n']} | {overlap} | {dice} | {crossing} |")
    lines += ['', 'Exact artifact/source hashes, differences and transition IDs are in analysis.json. All 2,808 same-ID paired records are in per_case_changes.jsonl. Normal-image Dice/IoU are not used as segmentation-quality evidence.', '', 'Limitations:', ''] + ['- ' + v for v in limitations]
    out.mkdir()  # All checks passed; never overwrite previous evidence.
    (out / 'analysis.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    report = out / 'TRAIN_FOREGROUND_BCE_FIT_PAIR.md'
    report.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    selected_keys = ('prediction_present', 'tp_pixels', 'fp_pixels', 'fn_pixels', 'dice', 'iou', 'zero_overlap_positive')
    with (out / 'per_case_changes.jsonl').open('x', encoding='utf-8') as stream:
        for stratum, ids in strata.items():
            for image_id in sorted(ids):
                record = dict(image_id=image_id, stratum=stratum, positive=bool(int(rows[image_id]['fractured'])),
                    conservative_related_group=rows[image_id]['group'], decoded_sha256=rows[image_id]['decoded_sha256'],
                    **{arm: {k: fits[arm][image_id][k] for k in selected_keys} for arm in ARMS})
                stream.write(json.dumps(record, allow_nan=False) + '\n')
    (out / 'source_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (out / 'adapted_source_snapshot.py').write_bytes(workspace_path(ADAPTED_SOURCE).read_bytes())
    completion = dict(status=result['status'], analysis_sha256=sha(out / 'analysis.json'), report_sha256=sha(report),
        per_case_sha256=sha(out / 'per_case_changes.jsonl'), source_sha256=sha(__file__), adapted_source_sha256=ADAPTED_SOURCE_SHA,
        new_image_reads=0, new_mask_array_reads=0, checkpoint_tensor_loads=0, checkpoint_file_byte_reads_performed=True,
        unique_checkpoint_files_byte_hashed=4, inference_performed=False, GPU_work_performed=False,
        calibration_images_read=0, test_images_read=0, promotion=False)
    (out / 'completion.json').write_text(json.dumps(completion, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=result['status'], summaries=summaries, candidate_minus_reference=deltas,
        paired_transition_counts={s: {k: v['n'] for k, v in t.items()} for s, t in changes.items()}), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
