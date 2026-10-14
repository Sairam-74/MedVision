"""Completed 256/512 native VAL comparison; metadata only, never promotes.

No image/array/checkpoint tensor loading, training, threshold fitting or CAL/test.
Both complete registered arms must pass provenance checks before any output.
"""
import argparse
from copy import deepcopy
import json
import math
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import ai_metrics as a
from tools.analyze_ai_pair import comparison, load, transitions
from tools.ai_atomic_io import json_atomic
from tools.evaluate_ai_baseline import sha

PROTOCOL = ROOT/'experiments/session_20261007_ai_loop_01/RESOLUTION_EXPERIMENT_PROTOCOL.json'
ORIGINAL = ROOT/'experiments/AI_BASELINE_20261007_v1'
PRIOR_E14 = ROOT/'experiments/AI_AUDIT_E14_v3_foreground_BCE5'
GLOBAL_EPOCHS = list(range(51, 63))
STRATA = ('hand', 'leg', 'hip', 'shoulder', 'mixed', 'hardware', 'multiscan',
          'frontal', 'lateral', 'oblique', 'small_region_proxy', 'multiple_fractures')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def workspace(value):
    path = Path(value)
    path = (path if path.is_absolute() else ROOT/path).resolve()
    require(ROOT in path.parents, 'Workspace input/output required: '+str(path))
    return path


def remember(path, bindings):
    path = workspace(path)
    name = path.relative_to(ROOT).as_posix()
    digest = sha(path)
    require(name not in bindings or bindings[name] == digest, 'Input changed during analysis: '+name)
    bindings[name] = digest
    return digest


def read(path, bindings):
    remember(path, bindings)
    return load(workspace(path))


def verify_hashes(values, bindings):
    for name, expected in values.items():
        require(remember(name, bindings) == expected, 'Recorded source/input hash mismatch: '+name)


def canonical_config(config):
    value = deepcopy(config)
    for key in ('input_size', 'cache', 'cache_completion_sha256'):
        value.pop(key)
    value['preprocess']['size'] = 256
    return value


def coverage(cases):
    positive = [c for c in cases if c['positive']]
    overlap = sum(c['tp_pixels'] > 0 for c in positive)
    return dict(positive_images=len(positive), any_GT_overlap_images=overlap,
                any_GT_overlap_fraction=a.ratio(overlap, len(positive)),
                empty_positive_masks=sum(not c['prediction_present'] for c in positive),
                nonempty_zero_GT_overlap=sum(c['prediction_present'] and c['tp_pixels'] == 0 for c in positive),
                native_GT_pixels=sum(c['tp_pixels']+c['fn_pixels'] for c in positive),
                interpretation='Any overlap is a minimal coverage check, not adequate fracture localization.')


def instance50(cases):
    matches = sum(c['mask_region_matches_iou50'] for c in cases)
    gt, predicted = sum(c['gt_instances'] for c in cases), sum(c['predicted_components'] for c in cases)
    return dict(matches=matches, gt=gt, predicted=predicted, precision=a.ratio(matches, predicted),
                recall=a.ratio(matches, gt), false_positive_regions=predicted-matches, missed_regions=gt-matches)


def safe_ge(value, target):
    return value is not None and target is not None and value >= target


def safe_gt(value, target):
    return value is not None and target is not None and value > target


def score_summary(cases):
    result = {}
    for name, subset in (('positive', [c for c in cases if c['positive']]),
                         ('normal', [c for c in cases if not c['positive']])):
        scores = sorted(c['case_score'] for c in subset)
        result[name] = dict(n=len(scores), minimum=min(scores) if scores else None,
                            median=statistics.median(scores) if scores else None,
                            maximum=max(scores) if scores else None,
                            exactly_one_count=sum(v == 1 for v in scores))
    result['interpretation'] = 'Saved maximum-pixel uncalibrated proxies, not calibrated fracture probabilities.'
    return result


def check_cases(cases, rows, bindings_name):
    require(len(cases) == 463 and len({c['image_id'] for c in cases}) == 463,
            'Exact unique 463 native cases required: '+bindings_name)
    require({c['image_id']: c['positive'] for c in cases} ==
            {key: bool(int(row['fractured'])) for key, row in rows.items()},
            'Frozen VAL source labels/IDs differ: '+bindings_name)
    for c in cases:
        row = rows[c['image_id']]
        require(isinstance(c['positive'], bool) and isinstance(c['prediction_present'], bool), 'Boolean label/decision required')
        require(c['native_shape'] == [row['height'], row['width']] and c['source_member'] == row['member'],
                'Native source geometry/member differs: '+c['image_id'])
        require(all(isinstance(c[k], int) and c[k] >= 0 for k in
                    ('tp_pixels', 'fp_pixels', 'fn_pixels', 'gt_instances', 'predicted_components', 'mask_region_matches_iou50')),
                'Nonnegative integer native counts required')
        require(bool(c['tp_pixels']+c['fn_pixels']) == c['positive'], 'Native GT/source label mismatch')
        require(bool(c['tp_pixels']+c['fp_pixels']) == c['prediction_present'], 'Native mask/decision mismatch')
        require(c['mask_region_matches_iou50'] <= min(c['gt_instances'], c['predicted_components']), 'Invalid instance matches')
        require(math.isfinite(c['case_score']) and 0 <= c['case_score'] <= 1, 'Finite probability proxy required')
        require(all(math.isfinite(c[k]) and 0 <= c[k] <= 1 for k in ('dice', 'iou')), 'Finite native overlap required')


def check_same_GT(left, right):
    l, r = [{c['image_id']: c for c in records} for records in (left, right)]
    require(set(l) == set(r), 'Same native IDs required')
    keys = ('positive', 'native_shape', 'source_member', 'gt_instances', 'gt_boxes', 'flags',
            'fracture_count', 'small_region_proxy')
    for name in l:
        require(all(l[name][key] == r[name][key] for key in keys), 'Native GT/stratum differs: '+name)
        require(l[name]['tp_pixels']+l[name]['fn_pixels'] == r[name]['tp_pixels']+r[name]['fn_pixels'],
                'Native GT area differs: '+name)


def check_recomputed(metrics, cases):
    classification, segmentation, calibration = a.classification(cases), a.segmentation(cases), a.calibration(cases)
    for family, keys, computed in (
            ('classification', ('n', 'positive', 'normal', 'confusion_matrix', 'accuracy', 'precision',
                                'recall_sensitivity', 'specificity', 'f1', 'auroc', 'auprc_average_precision',
                                'false_positive_rate', 'false_negative_rate'), classification),
            ('segmentation', ('n_positive', 'pixel_counts', 'mean_positive_dice', 'mean_positive_iou',
                              'global_pixel_precision', 'global_pixel_recall', 'global_dice', 'global_iou'), segmentation),
            ('calibration', ('brier_score', 'expected_calibration_error'), calibration)):
        for key in keys:
            stored, value = metrics[family][key], computed[key]
            require(stored == value or isinstance(stored, (int, float)) and isinstance(value, (int, float)) and
                    math.isclose(stored, value, rel_tol=1e-12, abs_tol=1e-12), 'Saved aggregate differs: '+family+'.'+key)
    require(metrics['mask_instance_localization']['0.5'] == instance50(cases), 'Native instance counts differ')


def audit(directory, rows, bindings):
    directory = workspace(directory)
    completed = read(directory/'completion.json', bindings)
    require(completed['status'] == 'completed' and not completed['test_images_read'] and
            not completed['calibration_fit'] and not completed['promotion'] and completed['independent_masks'],
            'Full native mask-only audit required')
    require(remember(directory/'metrics.json', bindings) == completed['metrics_sha256'] and
            remember(directory/'per_case.json', bindings) == completed['cases_sha256'], 'Native completion hash binding differs')
    metrics, cases = read(directory/'metrics.json', bindings), read(directory/'per_case.json', bindings)
    audit_config = read(directory/'config.json', bindings)
    require(metrics['config'] == audit_config and not metrics['test_images_read'], 'Native configuration binding differs')
    require(not audit_config['calibration_fit'] and not audit_config['promotion'] and not audit_config['test_images_read'],
            'Native audit must not fit calibration or promote')
    verify_hashes(audit_config['source_hashes'], bindings)
    check_cases(cases, rows, directory.name)
    check_recomputed(metrics, cases)
    return dict(directory=directory, completion=completed, config=audit_config, metrics=metrics, cases=cases)


def validate_run(item, size, protocol, protocol_sha, train_rows, bindings):
    run = workspace(item['config']['run'])
    config = read(run/'config.json', bindings)
    state, bundle = read(run/'state.json', bindings), read(run/'bundle.json', bindings)
    initial = read(run/'initial_parameters.json', bindings)
    remember(run/'epochs.jsonl', bindings)
    epochs = [json.loads(v) for v in (run/'epochs.jsonl').read_text(encoding='utf-8-sig').splitlines() if v.strip()]
    require(config['input_size'] == size and config['preprocess']['size'] == size, 'Exact registered resolution required')
    require(config['protocol_sha256'] == protocol_sha, 'Registered resolution protocol hash differs')
    require(config['foreground_bce_coefficient'] == 5 and config['hard_factor'] == 2 and
            config['positive_dice_coefficient'] == 1 and config['normal_bce_weight'] == 1 and
            config['presence_weight'] == 0 and config['warm_start_epoch'] == 50 and config['epochs'] == 12 and
            config['batch_size'] == 2 and config['seed'] == 42 and config['lr'] == .0001,
            'Fixed loss/seed/global initializer/budget required')
    require(not config['smoke'] and not config['calibration_fit'] and not config['test_evaluated'] and
            not config['promotion'] and state['status'] == 'completed' and state['epochs_finished'] == 12 and not state['smoke'],
            'Both full completed research arms required')
    require([r['epoch'] for r in epochs] == list(range(1, 13)) and
            [r['global_epoch'] for r in epochs] == GLOBAL_EPOCHS and
            all(r['train_images_seen'] == 2808 and r['unique_train_images_seen'] == 2808 and
                not r['smoke'] and not r['test_evaluated'] and not r['promotion'] and
                not r['validation']['calibration_fit'] and not r['validation']['test_evaluated'] and
                not r['validation']['promotion'] for r in epochs), 'Exact full global51-62 natural unique TRAIN budget required')
    require(remember(run/'best_model.pt', bindings) == bundle['checkpoint_sha256'] ==
            item['completion']['checkpoint_sha256'] == item['config']['checkpoint_sha256'], 'Selected checkpoint bindings differ')
    require(bundle['epoch'] in range(1, 13) and bundle['global_epoch'] == 50+bundle['epoch'] and
            item['config']['epoch'] == bundle['epoch'] and item['config']['global_epoch'] == bundle['global_epoch'],
            'Selected native epoch differs from completed bundle')
    require(item['config']['preprocess'] == config['preprocess'] and item['config']['postprocess'] == config['postprocess'],
            'Audit preprocessing/postprocessing differs from training')
    require(config['postprocess'] == {'threshold': .5, 'policy': 'all', 'min_pixels': 16}, 'Independent registered mask policy required')
    require(item['metrics']['trainer_reproduction']['exact_counts'] and
            not item['metrics']['trainer_reproduction']['differing_cases'], 'Selected trainer/native counts must reproduce exactly')
    verify_hashes(config['source_hashes'], bindings)
    init = protocol['initialization']
    require(init['selected_epoch'] == 11 and init['global_epoch'] == 50 and
            workspace(config['initial_checkpoint']) == workspace(init['snapshot']) and
            config['initial_checkpoint_sha256'] == init['snapshot_sha256'] == remember(init['snapshot'], bindings),
            'Exact selected E14 full initializer required')
    require(initial['global_epoch'] == 50 and initial['seed'] == 42 and
            initial['full_parameter_sha256'] == init['model_parameter_sha256'] and
            initial['optimizer_state_sha256'] == init['optimizer_state_sha256'] and
            initial['optimizer_snapshot_sha256'] == init['snapshot_sha256'], 'Saved full model/Adam initializer digests differ')
    cache = protocol['caches'][str(size)]
    cache_path = workspace(cache['path'])
    require(workspace(config['cache']) == cache_path and config['cache_completion_sha256'] == cache['completion_sha256'] ==
            remember(cache_path/'completion.json', bindings), 'Registered resolution cache binding differs')
    metadata = read(cache_path/'completion.json', bindings)
    cache_rows = read(cache_path/'rows.json', bindings)
    require(metadata['status'] == 'completed_exact_train_cache' and metadata['train_images'] == 2808 and
            metadata['train_positive_images'] == 493 and metadata['preprocess'] == config['preprocess'] and
            metadata['shape'] == [2808, size, size] and metadata['image_dtype'] == 'float32' and
            metadata['target_dtype'] == 'uint8' and metadata['valid_dtype'] == 'uint8' and
            metadata['manifest_sha256'] == config['manifest_sha256'] and
            metadata['archive_sha256'] == config['archive_sha256'] and cache_rows == train_rows and
            remember(cache_path/'rows.json', bindings) == metadata['rows_sha256'], 'Exact native TRAIN cache contract differs')
    verify_hashes(metadata['source_hashes'], bindings)
    require(set(metadata['cache_hashes']) == {'image', 'target', 'valid'}, 'All three cache arrays required')
    for name, digest in metadata['cache_hashes'].items():
        require(remember(cache_path/(name+'.npy'), bindings) == digest, 'Immutable resolution cache array bytes differ')
    if size == 512:
        require(metadata['builder'] == 'tools/cache_ai_resolution_inputs.py' and
                remember(cache_path/'target_representation.json', bindings) == metadata['target_representation_sha256'],
                'Native-derived512 cache producer/target representation binding required')
    return dict(run=run, config=config, state=state, bundle=bundle, initial=initial, epochs=epochs)


def useful_transitions(left, right):
    l, r = [{c['image_id']: c for c in records} for records in (left, right)]
    result = transitions(left, right)
    for name, condition in (
            ('positive_GT_overlap_gained', lambda x, y: x['positive'] and x['tp_pixels'] == 0 and y['tp_pixels'] > 0),
            ('positive_GT_overlap_lost', lambda x, y: x['positive'] and x['tp_pixels'] > 0 and y['tp_pixels'] == 0),
            ('new_positive_alert_with_GT', lambda x, y: x['positive'] and not x['prediction_present'] and y['prediction_present'] and y['tp_pixels'] > 0),
            ('new_positive_alert_without_GT', lambda x, y: x['positive'] and not x['prediction_present'] and y['prediction_present'] and y['tp_pixels'] == 0)):
        ids = sorted(key for key in l if condition(l[key], r[key]))
        result[name] = dict(n=len(ids), image_ids=ids)
    return result


def subset(cases, name):
    return [c for c in cases if c['small_region_proxy'] if name == 'small_region_proxy'] if name == 'small_region_proxy' else (
        [c for c in cases if c['fracture_count'] > 1] if name == 'multiple_fractures' else [c for c in cases if c['flags'][name]])


def subgroup_comparison(left, right):
    result = {}
    for name in STRATA:
        l, r = subset(left, name), subset(right, name)
        require({c['image_id'] for c in l} == {c['image_id'] for c in r}, 'Frozen subgroup membership differs: '+name)
        if not l:
            result[name] = None
            continue
        lm, rm = [dict(classification=a.classification(c), segmentation=a.segmentation(c), calibration=a.calibration(c)) for c in (l, r)]
        result[name] = dict(n=len(l), metrics=comparison(lm, rm), reference_coverage=coverage(l), candidate_coverage=coverage(r),
                            reference_instance_iou50=instance50(l), candidate_instance_iou50=instance50(r),
                            limitation='Source flags/proxies may overlap; small counts and no clinical subtype adjudication.')
    return result


def time_memory(item, training):
    epochs = training['epochs']
    timing = item['metrics']['timing']
    warnings = []
    device = item['config']['device']
    if device == 'cuda' and ('CPU' in timing['context'] or 'CPU' in item['config']['timing_context']):
        warnings.append('Actual audit device is CUDA but timing context retains stale CPU wording.')
    return dict(audit_device=device, saved_native_audit_timing=timing,
                total_saved_epoch_seconds=sum(r['epoch_seconds'] for r in epochs),
                median_saved_epoch_seconds=statistics.median(r['epoch_seconds'] for r in epochs),
                peak_cuda_allocated_bytes=max(r['cuda_peak_allocated_bytes'] for r in epochs),
                peak_cuda_reserved_bytes=max(r['cuda_peak_reserved_bytes'] for r in epochs),
                peak_process_rss_bytes=max(r['process_rss_bytes'] for r in epochs),
                isolated_latency_comparison=False, metadata_warnings=warnings,
                limitations=['Reported epoch peaks/durations include recorded implementation overhead.',
                             'Audit timing is not an isolated deployment benchmark; no latency acceptance claim.'])


def main():
    parser = argparse.ArgumentParser()
    for name in ('reference', 'candidate', 'out'):
        parser.add_argument('--'+name, required=True)
    args = parser.parse_args()
    left_dir, right_dir, out = [workspace(v) for v in (args.reference, args.candidate, args.out)]
    require(not out.exists() and left_dir != right_dir and all(d not in out.parents for d in (left_dir, right_dir)),
            'Separate completed native audits and exclusive new output required')
    bindings = {}
    protocol = read(PROTOCOL, bindings)
    protocol_sha = remember(PROTOCOL, bindings)
    require(protocol['major_factor'] == 'input_resolution' and not protocol['calibration_fit'] and
            not protocol['test_images_read'] and not protocol['promotion'] and
            protocol['common_config']['global_epochs'] == GLOBAL_EPOCHS and
            protocol['common_config']['foreground_bce_coefficient'] == 5 and
            protocol['common_config']['hard_factor'] == 2 and protocol['common_config']['positive_dice_coefficient'] == 1,
            'Registered resolution-only protocol required')
    verify_hashes(protocol['input_hashes'], bindings)
    manifest_path = ROOT/'experiments/data_v3_reliability_20261007/manifest.json'
    manifest = read(manifest_path, bindings)
    rows = {r['image_id']: r for r in manifest['rows'] if r['split'] == 'val'}
    train_rows = [r for r in manifest['rows'] if r['split'] == 'train']
    require(len(rows) == 463 and sum(int(r['fractured']) for r in rows.values()) == 83 and
            len(train_rows) == 2808 and len({r['image_id'] for r in train_rows}) == 2808 and
            sum(int(r['fractured']) for r in train_rows) == 493, 'Exact frozen TRAIN/VAL membership required')
    left, right = [audit(directory, rows, bindings) for directory in (left_dir, right_dir)]
    train_left, train_right = [validate_run(item, size, protocol, protocol_sha, train_rows, bindings)
                              for item, size in ((left, 256), (right, 512))]
    require(train_left['run'].name == protocol['reference'] and train_right['run'].name == protocol['candidate'] and
            [left_dir.name, right_dir.name] == protocol['audit_ids'], 'Registered arm/audit identity differs')
    require(canonical_config(train_left['config']) == canonical_config(train_right['config']),
            'Only resolution and derived cache/preprocess size may differ')
    require(train_left['initial'] == train_right['initial'], 'Complete saved model/Adam initialization differs')
    require(all(v['config']['manifest_sha256'] == remember(manifest_path, bindings) for v in (left, right)) and
            all(t['config']['manifest_sha256'] == remember(manifest_path, bindings) for t in (train_left, train_right)),
            'Registered frozen manifest binding differs')
    require(all(t['run'] not in out.parents for t in (train_left, train_right)), 'Cannot write inside a completed training run')
    replay = read(train_left['run']/'reference_replay_epoch_001.json', bindings)
    expected = protocol['reference_replay_parity']['51']
    require(replay['epoch'] == 1 and replay['global_epoch'] == 51 and replay['expected'] == expected and
            all(replay['checks'].get(k) is True for k in ('validation_exact', 'model_parameter_exact', 'optimizer_state_exact')) and
            replay['actual_validation'] == expected['validation'] == train_left['epochs'][0]['validation'] and
            replay['actual_model_parameter_sha256'] == expected['model_parameter_sha256'] and
            replay['actual_optimizer_state_sha256'] == expected['optimizer_state_sha256'] and
            remember(expected['original_full_snapshot'], bindings) == expected['original_full_snapshot_sha256'],
            'Exact old E14epoch12/global51 replay is required')
    lc, rc = left['cases'], right['cases']
    check_same_GT(lc, rc)
    alerts = []
    for item in (left, right):
        cases = read(item['directory']/'review_alert_cases.json', bindings)
        check_cases(cases, rows, item['directory'].name+' review alerts')
        require({c['image_id']: (c['prediction_present'], c['case_score']) for c in cases} ==
                {c['image_id']: (c['prediction_present'], c['case_score']) for c in item['cases']},
                'Mask-only conservative alerts must equal independent mask decisions')
        check_same_GT(cases, item['cases'])
        alerts.append(cases)
    original_all = read(ORIGINAL/'per_case.json', bindings)
    original_cases = [c for c in original_all if c['image_id'] in rows]
    check_cases(original_cases, rows, 'preserved original same-ID reference')
    check_same_GT(original_cases, lc)
    original = dict(classification=a.classification(original_cases), segmentation=a.segmentation(original_cases),
                    calibration=a.calibration(original_cases))
    original_loc = instance50(original_cases)
    prior = audit(PRIOR_E14, rows, bindings)
    check_same_GT(prior['cases'], lc)
    require(prior['config']['epoch'] == 11 and prior['config']['global_epoch'] == 50 and
            prior['completion']['checkpoint_sha256'] == protocol['initialization'].get('best_checkpoint_sha256',
                prior['completion']['checkpoint_sha256']), 'Preserved selected E14 comparison must be global50')
    l, r = left['metrics'], right['metrics']
    base, matched, seg = original['segmentation'], l['segmentation'], r['segmentation']
    cm, loc, matched_loc = r['classification']['confusion_matrix'], r['mask_instance_localization']['0.5'], l['mask_instance_localization']['0.5']
    old_coverage, left_coverage, right_coverage = [coverage(v) for v in (original_cases, lc, rc)]
    checks = dict(classification_counts=cm['tp'] >= 79 and cm['tn'] >= 342 and r['classification']['accuracy'] >= .9,
                  native_positive_dice=seg['mean_positive_dice'] >= max(base['mean_positive_dice'], matched['mean_positive_dice'])+.02,
                  native_positive_iou=seg['mean_positive_iou'] > max(base['mean_positive_iou'], matched['mean_positive_iou']),
                  instance_precision=safe_gt(loc['precision'], max(original_loc['precision'], matched_loc['precision'])),
                  instance_recall=safe_gt(loc['recall'], max(original_loc['recall'], matched_loc['recall'])),
                  false_positive_pixels=seg['pixel_counts']['fp'] < min(base['pixel_counts']['fp'], matched['pixel_counts']['fp']),
                  useful_pixel_coverage_vs_matched=safe_ge(seg['global_pixel_recall'], matched['global_pixel_recall']),
                  useful_pixel_coverage_vs_original=safe_ge(seg['global_pixel_recall'], base['global_pixel_recall']),
                  positive_any_GT_coverage_vs_matched=right_coverage['any_GT_overlap_images'] >= left_coverage['any_GT_overlap_images'],
                  positive_any_GT_coverage_vs_original=right_coverage['any_GT_overlap_images'] >= old_coverage['any_GT_overlap_images'])
    development_checks = dict(
        recall=safe_ge(r['classification']['recall_sensitivity'], l['classification']['recall_sensitivity']),
        specificity=safe_ge(r['classification']['specificity'], l['classification']['specificity']),
        positive_dice=safe_gt(seg['mean_positive_dice'], matched['mean_positive_dice']),
        positive_iou=safe_gt(seg['mean_positive_iou'], matched['mean_positive_iou']),
        false_positive_pixels=seg['pixel_counts']['fp'] <= matched['pixel_counts']['fp'],
        useful_pixel_recall=safe_ge(seg['global_pixel_recall'], matched['global_pixel_recall']),
        instance_precision=safe_ge(loc['precision'], matched_loc['precision']),
        instance_recall=safe_ge(loc['recall'], matched_loc['recall']),
        positive_any_GT_non_decrease=right_coverage['any_GT_overlap_images'] >= left_coverage['any_GT_overlap_images'])
    result = dict(reference=left_dir.relative_to(ROOT).as_posix(), candidate=right_dir.relative_to(ROOT).as_posix(),
        factor='Native-derived model input resolution256 versus512; foreground BCE5/Dice1/hard2 and all other factors fixed',
        all_other_configurations_matched=True, initial_model_optimizer_matched=True, reference_global51_replay_exact=True,
        same463_validation_ids_and_labels=True, native_GT_areas_and_subgroups_matched=True,
        protocol_sha256=protocol_sha, input_and_source_hashes=bindings,
        metrics=comparison(l, r), original_same_ID_comparison=comparison(original, r),
        prior_E14_selected_same_ID_comparison=dict(metrics=comparison(prior['metrics'], r),
            prior_coverage=coverage(prior['cases']), limitation='Additional historical comparison; not the matched causal resolution control.'),
        independent_mask_error_transitions=useful_transitions(lc, rc),
        conservative_alert_error_transitions=transitions(*alerts),
        original_instance_localization=original_loc, matched_instance_localization=matched_loc,
        candidate_instance_localization=loc, original_coverage=old_coverage, matched_coverage=left_coverage,
        candidate_coverage=right_coverage, native_component_box_proxy={'reference': l['localization'], 'candidate': r['localization']},
        subgroups=subgroup_comparison(lc, rc),
        uncalibrated_scores={'reference': score_summary(lc), 'candidate': score_summary(rc)},
        uncalibrated_proxy_regressions={k: r['calibration'][k] > l['calibration'][k] for k in ('brier_score', 'expected_calibration_error')},
        calibration_gate_still_required=True,
        time_memory={'reference': time_memory(left, train_left), 'candidate': time_memory(right, train_right)},
        validation_gate_checks=checks, validation_numerical_gate_pass=all(checks.values()),
        development_checks=development_checks,
        manual_native_coverage_review_required=True,
        decision='KEEP FOR DEVELOPMENT; full further gates required' if all(development_checks.values()) else
                 'REJECT as balanced overall improvement at registered operating point',
        final_success=False, promotion=False, calibration_fit=False, test_images_read=0,
        limitations=['Numerical checks never substitute for actual FP/FN/GT/mask inspection.',
                     'Increased alerts with no target overlap are not useful fracture recovery.',
                     'Original historical training exposure unknown; same-ID comparison is preserved.',
                     'Uncalibrated maximum pixel proxies; no clinical confidence claim.',
                     'No verified patient/study identifiers, clinical subtle/nondisplaced labels or expert adjudication.',
                     'Source view/anatomy flags overlap; small-region and multiple-annotation groups are proxies.',
                     'One seed, selected epochs may differ, no external validation or locked-test success.',
                     'Component-box AP is a proxy, not canonical detector mAP.',
                     'Saved timing may include contention and stale context wording; no isolated speed comparison.'])
    verify_hashes(bindings.copy(), {})
    out.mkdir()
    json_atomic(out/'comparison.json', result)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 4, figsize=(16, 7))
    titles = ('Training loss', 'Segmentation loss', 'Review sensitivity', 'Review specificity',
              'Review AUROC', 'Positive native Dice', 'Positive native IoU', 'Mask specificity')
    for training, label in ((train_left, 'Reference:256'), (train_right, 'Candidate:512')):
        epochs = training['epochs']
        series = [[v['loss_components'][k] for v in epochs] for k in ('total', 'segmentation_total')]
        series += [[v['validation']['classification'][k] for v in epochs] for k in ('recall_sensitivity', 'specificity', 'auroc')]
        series += [[v['validation']['delivered'][k] for v in epochs] for k in ('mean_positive_dice', 'mean_positive_iou')]
        series += [[v['validation']['mask_classification']['specificity'] for v in epochs]]
        for ax, values, title in zip(axes.ravel(), series, titles):
            ax.plot(GLOBAL_EPOCHS, values, marker='o', label=label)
            ax.set(title=title, xlabel='Global epoch')
            ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(out/'paired_learning_curves.png', dpi=150)
    plt.close(fig)
    (out/'PAIR_ANALYSIS.md').write_text('# Controlled model input resolution comparison\n\n'+result['decision']+
        '\n\n'+json.dumps(result, indent=2)+'\n\nActual native mask review remains required. '+
        'No calibration fitting, test evaluation, clinical improvement declaration or promotion.\n', encoding='utf-8')
    verify_hashes(bindings.copy(), {})
    json_atomic(out/'completion.json', dict(status='completed', comparison_sha256=sha(out/'comparison.json'),
        curves_sha256=sha(out/'paired_learning_curves.png'), report_sha256=sha(out/'PAIR_ANALYSIS.md'),
        source_sha256=sha(Path(__file__)), protocol_sha256=protocol_sha, source_and_input_hashes_reverified=True,
        test_images_read=0, calibration_fit=False, promotion=False, final_success=False))
    print(json.dumps(dict(decision=result['decision'], validation_gate_checks=checks,
                         development_checks=development_checks), indent=2))


if __name__ == '__main__':
    main()
