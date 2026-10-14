"""Compare completed E9/E10 saved raw TRAIN-grid masks, using CPU metadata only.

No image, array, model or reserved-split prediction reads. Both TRAIN-fit
completion markers and completed training states are required before cases
are read. Does not train, select a subsequent factor, or promote a model.
"""
import argparse
import datetime
import hashlib
import json
import math
from pathlib import Path
import statistics


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = 'experiments/session_20261007_ai_loop_01/HARD_EXPERIMENT_PROTOCOL.json'
PROTOCOL_SHA = '168f04c50f01dbe72b5339219807e9bdcd78d35817680770c51417c9b0ed7e2e'
MANIFEST = 'experiments/data_v3_reliability_20261007/manifest.json'
MANIFEST_SHA = '4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318'
DEFAULT_OUT = 'experiments/AI_HARD_FIT_PAIR_E9_E10_20261008'
ARMS = {'E9': ('AI_LEARNING_FIT_E9_v3_hard_reference', 'AI_E9_v3_hard_reference', 1),
        'E10': ('AI_LEARNING_FIT_E10_v3_hard_weight2', 'AI_E10_v3_hard_weight2', 2)}


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def workspace_path(relative):
    path = (ROOT / relative).resolve()
    if ROOT not in path.parents:
        raise ValueError('Workspace metadata/source path required')
    return path


class MetadataReader:
    def __init__(self):
        self.inputs = {}

    def record(self, path):
        path = workspace_path(path)
        digest = sha(path)
        name = str(path.relative_to(ROOT))
        if name in self.inputs and self.inputs[name] != digest:
            raise ValueError('Input changed during comparison: ' + name)
        self.inputs[name] = digest
        return digest

    def read(self, path, lines=False):
        path = workspace_path(path)
        if path.suffix not in ('.json', '.jsonl'):
            raise ValueError('Only saved JSON metadata/results may be read')
        digest = self.record(path)
        raw = path.read_text(encoding='utf-8')
        if sha(path) != digest:
            raise ValueError('Metadata changed during read')
        return [json.loads(v) for v in raw.splitlines() if v.strip()] if lines else json.loads(raw)

    def assert_unchanged(self):
        for name, digest in self.inputs.items():
            if sha(workspace_path(name)) != digest:
                raise ValueError('Completed input/source changed before output: ' + name)


def validate_case(case, row):
    if case['positive'] != bool(int(row['fractured'])) or case['group'] != row['group']:
        raise ValueError('Saved fit source group or source label differs')
    tp, fp, fn = (case[k] for k in ('tp_pixels', 'fp_pixels', 'fn_pixels'))
    if any(type(v) is not int or v < 0 for v in (tp, fp, fn)):
        raise ValueError('Nonnegative integer grid pixel counts required')
    if case['prediction_present'] != bool(tp + fp):
        raise ValueError('Independent mask alert and pixel counts disagree')
    if case['zero_overlap_positive'] != bool(case['positive'] and tp == 0):
        raise ValueError('Zero-overlap flag and pixel counts disagree')
    if not case['positive']:
        if tp or fn or case['dice'] is not None or case['iou'] is not None:
            raise ValueError('Normal source reference mask or overlap values changed')
    else:
        if tp + fn <= 0:
            raise ValueError('Positive source has no represented grid target')
        for key, expected in (('dice', 2 * tp / (2 * tp + fp + fn)),
                              ('iou', tp / (tp + fp + fn))):
            if not math.isclose(case[key], expected, rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError('Saved ' + key + ' disagrees with independent binary pixels')
    if any(case.get(k) is not None for k in ('head_score', 'presence_logit', 'classifier_prediction_present')):
        raise ValueError('Unsupervised mask-only fit required; head scores must be absent')
    if case['review_alert_present'] != case['prediction_present']:
        raise ValueError('Mask-only review alert differs from independent mask')


def summarize(cases, rows):
    positive = cases[0]['positive']
    if any(c['positive'] != positive for c in cases):
        raise ValueError('One source-label class per stratum required')
    tp, fp, fn = (sum(c[k] for c in cases) for k in ('tp_pixels', 'fp_pixels', 'fn_pixels'))
    alerts = sum(c['prediction_present'] for c in cases)
    ids = [c['image_id'] for c in cases]
    result = dict(images=len(cases), conservative_related_groups=len({rows[i]['group'] for i in ids}),
                  distinct_decoded_hashes=len({rows[i]['decoded_sha256'] for i in ids}),
                  mask_alerts=alerts, empty_masks=len(cases) - alerts, mask_alert_rate=alerts / len(cases),
                  pixel_counts=dict(tp=tp, fp=fp, fn=fn))
    if positive:
        result.update(mean_Dice=statistics.mean(c['dice'] for c in cases),
                      median_Dice=statistics.median(c['dice'] for c in cases),
                      mean_IoU=statistics.mean(c['iou'] for c in cases),
                      any_GT_overlap=sum(c['tp_pixels'] > 0 for c in cases),
                      zero_GT_overlap=sum(c['tp_pixels'] == 0 for c in cases),
                      nonempty_wrong_region=sum(c['prediction_present'] and c['tp_pixels'] == 0 for c in cases),
                      Dice_below_0_2=sum(c['dice'] < .2 for c in cases),
                      pixel_precision=tp / (tp + fp) if tp + fp else None,
                      pixel_recall=tp / (tp + fn))
    else:
        result.update(normal_FP=alerts, normal_TN=len(cases) - alerts,
                      false_positive_rate=alerts / len(cases),
                      overlap_metrics_not_applicable=True)
    return result


def paired_transitions(ids, left, right, positive):
    predicates = {
        'mask_alert_gained': lambda l, r: not l['prediction_present'] and r['prediction_present'],
        'mask_alert_removed': lambda l, r: l['prediction_present'] and not r['prediction_present'],
        'FP_grid_pixels_increased': lambda l, r: r['fp_pixels'] > l['fp_pixels'],
        'FP_grid_pixels_decreased': lambda l, r: r['fp_pixels'] < l['fp_pixels']}
    if positive:
        predicates.update(
            GT_overlap_gained=lambda l, r: l['tp_pixels'] == 0 and r['tp_pixels'] > 0,
            GT_overlap_lost=lambda l, r: l['tp_pixels'] > 0 and r['tp_pixels'] == 0,
            Dice_gain_gt_0_02=lambda l, r: r['dice'] - l['dice'] > .02,
            Dice_loss_gt_0_02=lambda l, r: l['dice'] - r['dice'] > .02,
            cross_Dice_0_2_up=lambda l, r: l['dice'] < .2 <= r['dice'],
            cross_Dice_0_2_down=lambda l, r: r['dice'] < .2 <= l['dice'],
            wrong_region_to_useful_overlap=lambda l, r: l['prediction_present'] and l['tp_pixels'] == 0 and r['tp_pixels'] > 0,
            useful_overlap_to_wrong_region=lambda l, r: l['tp_pixels'] > 0 and r['prediction_present'] and r['tp_pixels'] == 0)
    return {name: dict(n=len(chosen := [i for i in sorted(ids) if pred(left[i], right[i])]), image_ids=chosen)
            for name, pred in predicates.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default=DEFAULT_OUT)
    args = parser.parse_args()
    out = workspace_path(args.out)
    if out.exists():
        raise ValueError('New exclusive output directory required')
    reader = MetadataReader()
    # Check both completion markers before opening any E10 case/run metadata.
    for fit, _, _ in ARMS.values():
        marker = workspace_path('experiments/' + fit + '/completion.json')
        if not marker.exists():
            raise ValueError('WAIT: both completed TRAIN-fit markers are required; no partial results read')
        done = reader.read(marker)
        if (done['status'] != 'completed_read_only_TRAIN_fit' or done['train_cases'] != 2808
                or not done['model_tensors_unchanged'] or not done['no_optimizer_steps']
                or any(done[k] for k in ('validation_images_read', 'calibration_images_read', 'test_images_read'))):
            raise ValueError('Completed unchanged TRAIN-only fit required')
    protocol = reader.read(PROTOCOL)
    if reader.inputs[str(workspace_path(PROTOCOL).relative_to(ROOT))] != PROTOCOL_SHA:
        raise ValueError('Registered hard-pair protocol changed')
    if (protocol['reference'], protocol['candidate']) != (ARMS['E9'][1], ARMS['E10'][1]):
        raise ValueError('Registered E9/E10 pair required')
    protocol_hashes = {workspace_path(p): digest for p, digest in protocol['input_hashes'].items()}

    def registered_read(path):
        value = reader.read(path)
        if reader.inputs[str(workspace_path(path).relative_to(ROOT))] != protocol_hashes.get(workspace_path(path)):
            raise ValueError('Frozen registered metadata changed: ' + str(path))
        return value

    manifest = registered_read(MANIFEST)
    if reader.inputs[str(workspace_path(MANIFEST).relative_to(ROOT))] != MANIFEST_SHA:
        raise ValueError('Frozen TRAIN manifest changed')
    train_rows = [r for r in manifest['rows'] if r['split'] == 'train']
    rows = {r['image_id']: r for r in train_rows}
    if len(train_rows) != len(rows) or len(rows) != 2808 or sum(int(r['fractured']) for r in train_rows) != 493:
        raise ValueError('Exact unique TRAIN2808 with493 explicit positive labels required')
    catalog = protocol['hard_catalog']
    catalog_done = registered_read(catalog + '/completion.json')
    if catalog_done['status'] != 'completed_TRAIN_hard_catalog_refresh_only':
        raise ValueError('Registered completed hard catalog required')
    hard_positive = registered_read(catalog + '/HARD_POSITIVE_SET.json')['image_ids']
    hard_negative = registered_read(catalog + '/HARD_NEGATIVE_SET.json')['image_ids']
    for ids, expected, label in ((hard_positive, 109, 1), (hard_negative, 713, 0)):
        if len(ids) != len(set(ids)) or len(ids) != expected or not set(ids) <= set(rows):
            raise ValueError('Frozen hard catalog count/uniqueness/TRAIN membership changed')
        if any(int(rows[i]['fractured']) != label for i in ids):
            raise ValueError('Frozen hard source labels changed')
    strata = {'hard_positive': set(hard_positive),
              'ordinary_positive': {i for i, r in rows.items() if int(r['fractured'])} - set(hard_positive),
              'hard_negative': set(hard_negative),
              'ordinary_negative': {i for i, r in rows.items() if not int(r['fractured'])} - set(hard_negative)}
    if set.union(*strata.values()) != set(rows) or sum(map(len, strata.values())) != 2808:
        raise ValueError('Hard and ordinary strata do not uniquely partition TRAIN')
    fits, configs, fit_configs, initializations, model_metadata = {}, {}, {}, {}, {}
    verified_sources = []
    for arm, (fit, run, factor) in ARMS.items():
        prefix, run_prefix = 'experiments/' + fit, 'experiments/' + run
        state = reader.read(run_prefix + '/state.json')
        if state['status'] != 'completed' or state['epochs_finished'] != 12 or state['smoke'] or state['test_evaluated'] or state['promotion']:
            raise ValueError('Both full registered training runs must complete')
        config = reader.read(run_prefix + '/config.json')
        fit_config = reader.read(prefix + '/config.json')
        bundle = reader.read(run_prefix + '/bundle.json')
        if (config['hard_factor'] != factor or config['presence_weight'] != 0
                or config['protocol_sha256'] != PROTOCOL_SHA or config['manifest_sha256'] != MANIFEST_SHA
                or config['hard_catalog'] != catalog or config['hard_positive_count'] != 109 or config['hard_negative_count'] != 713
                or config['epochs'] != 12 or config['smoke'] or config['calibration_fit'] or config['test_evaluated'] or config['promotion']):
            raise ValueError('Registered mask-only hard factor and dataset configuration required')
        if (workspace_path(fit_config['run']) != workspace_path(run_prefix)
                or fit_config['augmentation'] or fit_config['mask_gated'] or not fit_config['no_optimizer_steps']
                or any(fit_config[k] for k in ('validation_images_read', 'calibration_images_read', 'test_images_read'))
                or fit_config['manifest_sha256'] != MANIFEST_SHA
                or fit_config['checkpoint_sha256'] != bundle['checkpoint_sha256'] or fit_config['epoch'] != bundle['epoch']
                or bundle['global_epoch'] != config['warm_start_epoch'] + bundle['epoch']
                or not 1 <= bundle['epoch'] <= 12 or bundle['hard_factor'] != factor or bundle['presence_weight'] != 0
                or bundle['manifest_sha256'] != MANIFEST_SHA):
            raise ValueError('Completed fit is not the selected final bundle metadata')
        for key in ('preprocess', 'output_contract'):
            if fit_config[key] != config[key] or bundle[key] != config[key]:
                raise ValueError('Fit/run/bundle output geometry or contract changed')
        if fit_config['cache'] != config['cache'] or bundle['postprocess'] != config['postprocess']:
            raise ValueError('Fit/run/bundle cache or threshold configuration changed')
        if any(fit_config['source_hashes'].get(s) != d for s, d in config['source_hashes'].items()):
            raise ValueError('Completed fit uses different recorded training sources')
        for source, digest in fit_config['source_hashes'].items():
            if reader.record(source) != digest:
                raise ValueError('Recorded completed fit source hash changed: ' + source)
            if source in config['source_hashes'] and protocol_hashes.get(workspace_path(source)) != digest:
                raise ValueError('Training source is not identical to frozen registration')
            verified_sources.append(dict(arm=arm, source=source, sha256=digest))
        if config['initial_checkpoint_sha256'] != protocol_hashes.get(workspace_path(config['initial_checkpoint'])):
            raise ValueError('Registered initial full snapshot identity changed')
        initial = reader.read(run_prefix + '/initial_parameters.json')
        if initial['optimizer_snapshot_sha256'] != config['initial_checkpoint_sha256'] or initial['global_epoch'] != 18 or initial['seed'] != config['seed']:
            raise ValueError('Full warm initialization metadata differs')
        cases = reader.read(prefix + '/train_cases.jsonl', lines=True)
        by_id = {c['image_id']: c for c in cases}
        if len(cases) != len(by_id) or set(by_id) != set(rows):
            raise ValueError('Completed fit does not have exact unique2808 TRAIN IDs')
        for image_id, case in by_id.items():
            validate_case(case, rows[image_id])
        fits[arm], configs[arm], fit_configs[arm], initializations[arm] = by_id, config, fit_config, initial
        model_metadata[arm] = dict(run=run_prefix, fit=prefix, hard_factor=factor,
                                  checkpoint_sha256=bundle['checkpoint_sha256'], selected_epoch=bundle['epoch'],
                                  selected_global_epoch=bundle['global_epoch'],
                                  cases_sha256=reader.inputs[str(workspace_path(prefix + '/train_cases.jsonl').relative_to(ROOT))])
    if {k: v for k, v in configs['E9'].items() if k != 'hard_factor'} != {k: v for k, v in configs['E10'].items() if k != 'hard_factor'}:
        raise ValueError('Uncontrolled training configuration difference beyond hard factor')
    ignored_fit = {'run', 'checkpoint_sha256', 'epoch'}
    if {k: v for k, v in fit_configs['E9'].items() if k not in ignored_fit} != {k: v for k, v in fit_configs['E10'].items() if k not in ignored_fit}:
        raise ValueError('Uncontrolled TRAIN-fit configuration difference')
    if initializations['E9'] != initializations['E10']:
        raise ValueError('Initial full model/optimizer snapshot metadata differs')
    if any(fits['E9'][i]['tp_pixels'] + fits['E9'][i]['fn_pixels'] != fits['E10'][i]['tp_pixels'] + fits['E10'][i]['fn_pixels'] for i in rows):
        raise ValueError('Same-ID saved grid target areas differ')
    cache = configs['E9']['cache']
    cache_completion = registered_read(str(Path(cache) / 'completion.json'))
    cache_rows = registered_read(str(Path(cache) / 'rows.json'))
    cache_verification = registered_read(str(Path(cache) / 'verification.json'))
    if (cache_completion['status'] != 'completed_exact_train_cache'
            or cache_completion['manifest_sha256'] != MANIFEST_SHA
            or cache_completion['shape'] != [2808, 256, 256]
            or not cache_completion['all_written_tensors_bit_exact']
            or cache_completion['preprocess'] != configs['E9']['preprocess']
            or configs['E9']['cache_completion_sha256'] != reader.inputs[str(workspace_path(Path(cache) / 'completion.json').relative_to(ROOT))]
            or cache_rows != train_rows
            or not all(all(v['exact_float32_parity'].values()) for v in cache_verification)):
        raise ValueError('Frozen shared grid cache metadata is not identical')
    summaries = {name: {arm: summarize([fits[arm][i] for i in sorted(ids)], rows) for arm in ARMS} for name, ids in strata.items()}
    changes = {name: paired_transitions(ids, fits['E9'], fits['E10'], 'positive' in name) for name, ids in strata.items()}
    deltas = {}
    for name, arms in summaries.items():
        left, right = arms['E9'], arms['E10']
        keys = ['mask_alerts', 'empty_masks'] + (['mean_Dice', 'mean_IoU', 'any_GT_overlap', 'zero_GT_overlap', 'nonempty_wrong_region', 'Dice_below_0_2', 'pixel_recall'] if 'positive' in name else ['normal_FP', 'normal_TN', 'false_positive_rate'])
        deltas[name] = {k: right[k] - left[k] for k in keys}
        deltas[name]['pixel_counts'] = {k: right['pixel_counts'][k] - left['pixel_counts'][k] for k in ('tp', 'fp', 'fn')}
    limitations = [
        'This is an unaugmented TRAIN fit comparison, not native VAL acceptance, locked test performance or clinical generalization.',
        'Hard109/713 were selected from E7/E8 TRAIN errors and remain frozen; their selection prevents an independent difficult-case claim.',
        'Source groups are conservative related-image candidates, not proven patients/studies. Exact decoded-hash repetition is inherited source repetition, not new resampling.',
        'Masks are independent threshold0.5 grid outputs. A case alert can be a nonempty mask with no fracture overlap; any GT overlap alone does not prove adequate localization.',
        'Both use the same frozen cache metadata and identical saved per-case GT areas. The cache records array checksums, but this task does not reread/re-hash target arrays or verify new per-case target bitmaps.',
        'Initial parameter metadata and full optimizer snapshot identity match. No model/Adam tensors are reloaded in this CPU analysis; initializer restoration was separately exercised by the registered smoke.',
        'Selected additional/global epochs may differ under the common VAL selection rule; this compares selected models, not a guaranteed same-epoch estimate.',
        'One seed, no external validation and no expert subtle/nondisplaced labels. Dice0.2 and change0.02 are descriptive analysis cutoffs, not clinical adequacy criteria.',
        'No production promotion or subsequent intervention is selected from this report; native pair metrics and actual mask/failure reviews remain necessary.']
    reader.assert_unchanged()
    result = dict(status='completed_saved_TRAIN_grid_hard_fit_pair_comparison',
                  created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), source_sha256=sha(__file__),
                  protocol_sha256=PROTOCOL_SHA, manifest_sha256=MANIFEST_SHA,
                  verified_input_hashes=reader.inputs, verified_recorded_sources=verified_sources,
                  unique_TRAIN_count=2808, positive_sources=493, normal_sources=2315,
                  hard_positive_count=109, hard_negative_count=713,
                  exact_unique_membership_labels_groups_verified=True,
                  shared_frozen_grid_cache_verified=True, same_ID_grid_target_areas_verified=True,
                  only_training_config_difference='hard_factor1 versus2', initial_metadata_equal=True,
                  model_metadata=model_metadata, initial_parameters=initializations['E9'],
                  registered_grid_array_checksums=cache_completion['cache_hashes'],
                  summaries=summaries, candidate_minus_reference=deltas, same_ID_transitions=changes,
                  limitations=limitations, new_image_reads=0, new_mask_array_reads=0, new_model_reads=0,
                  new_predictions=0, GPU_work_performed=False, inference_performed=False,
                  calibration_images_read=0, test_images_read=0, model_trained=False, promotion=False,
                  next_factor_selected=False)
    lines = ['# Completed E9/E10 TRAIN hard-fit comparison', '',
             'Saved CPU analysis of the two completed selected models. No new images, arrays, model tensors, inference, GPU, calibration/test data or production changes.', '',
             'The unchanged manifest supplies 2,808 unique TRAIN sources: 493 positive and 2,315 normal. The frozen hard sets contain 109 positive and 713 normal sources. All memberships, labels, groups, recorded source versions and shared grid metadata passed.', '',
             '| Model | Hard factor | Selected additional / global epoch |', '|---|---|---|']
    for arm, item in model_metadata.items():
        lines.append(f"| {arm} | {item['hard_factor']} | {item['selected_epoch']} / {item['selected_global_epoch']} |")
    lines += ['', '| Positive stratum | Model | Sources / groups / exact hashes | Dice / IoU | Alerts | Empty | Wrong region | Any GT overlap | Dice <0.2 |', '|---|---|---|---|---|---|---|---|---|']
    for name in ('hard_positive', 'ordinary_positive'):
        for arm, s in summaries[name].items():
            lines.append(f"| {name.replace('_', ' ')} | {arm} | {s['images']} / {s['conservative_related_groups']} / {s['distinct_decoded_hashes']} | {s['mean_Dice']:.6f} / {s['mean_IoU']:.6f} | {s['mask_alerts']} | {s['empty_masks']} | {s['nonempty_wrong_region']} | {s['any_GT_overlap']} | {s['Dice_below_0_2']} |")
    lines += ['', '| Normal stratum | Model | Sources / groups / exact hashes | FP / TN | FP rate | FP grid pixels |', '|---|---|---|---|---|---|']
    for name in ('hard_negative', 'ordinary_negative'):
        for arm, s in summaries[name].items():
            lines.append(f"| {name.replace('_', ' ')} | {arm} | {s['images']} / {s['conservative_related_groups']} / {s['distinct_decoded_hashes']} | {s['normal_FP']} / {s['normal_TN']} | {s['false_positive_rate']:.2%} | {s['pixel_counts']['fp']} |")
    lines += ['', '| Positive stratum | Model | TP / FP / FN grid pixels | Pixel precision / recall |', '|---|---|---|---|']
    for name in ('hard_positive', 'ordinary_positive'):
        for arm, s in summaries[name].items():
            precision = f"{s['pixel_precision']:.4f}" if s['pixel_precision'] is not None else 'undefined'
            p = s['pixel_counts']
            lines.append(f"| {name.replace('_', ' ')} | {arm} | {p['tp']} / {p['fp']} / {p['fn']} | {precision} / {s['pixel_recall']:.4f} |")
    lines += ['', 'Paired transitions are E9 reference to E10 candidate:', '',
              '| Stratum | Alerts added / removed | FP pixels increased / decreased (cases) | GT overlap gained / lost | Dice gain / loss >0.02 | Dice0.2 crossed up / down |', '|---|---|---|---|---|---|']
    for name, t in changes.items():
        get = lambda key: t[key]['n']
        positive = 'positive' in name
        overlap = f"{get('GT_overlap_gained')} / {get('GT_overlap_lost')}" if positive else 'not applicable'
        dice = f"{get('Dice_gain_gt_0_02')} / {get('Dice_loss_gt_0_02')}" if positive else 'not applicable'
        crossing = f"{get('cross_Dice_0_2_up')} / {get('cross_Dice_0_2_down')}" if positive else 'not applicable'
        lines.append(f"| {name.replace('_', ' ')} | {get('mask_alert_gained')} / {get('mask_alert_removed')} | {get('FP_grid_pixels_increased')} / {get('FP_grid_pixels_decreased')} | {overlap} | {dice} | {crossing} |")
    lines += ['', 'Full exact source hashes, per-stratum differences, pixel counts and transition IDs are in analysis.json; per_case_changes.jsonl contains all 2,808 paired records. Normal-image Dice/IoU are intentionally not used as segmentation-quality evidence.', '', 'Limitations:', ''] + ['- ' + v for v in limitations]
    out.mkdir()
    (out / 'analysis.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    (out / 'TRAIN_HARD_FIT_PAIR.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    selected_keys = ('prediction_present', 'tp_pixels', 'fp_pixels', 'fn_pixels', 'dice', 'iou', 'zero_overlap_positive')
    with (out / 'per_case_changes.jsonl').open('x', encoding='utf-8') as stream:
        for stratum, ids in strata.items():
            for image_id in sorted(ids):
                case = dict(image_id=image_id, stratum=stratum, positive=bool(int(rows[image_id]['fractured'])),
                            conservative_related_group=rows[image_id]['group'], decoded_sha256=rows[image_id]['decoded_sha256'],
                            **{arm: {k: fits[arm][image_id][k] for k in selected_keys} for arm in ARMS})
                stream.write(json.dumps(case, allow_nan=False) + '\n')
    (out / 'source_snapshot.py').write_bytes(Path(__file__).read_bytes())
    completion = dict(status=result['status'], analysis_sha256=sha(out / 'analysis.json'),
                      report_sha256=sha(out / 'TRAIN_HARD_FIT_PAIR.md'),
                      per_case_sha256=sha(out / 'per_case_changes.jsonl'), source_sha256=sha(__file__),
                      new_image_reads=0, new_mask_array_reads=0, new_model_reads=0,
                      inference_performed=False, GPU_work_performed=False,
                      calibration_images_read=0, test_images_read=0, promotion=False)
    (out / 'completion.json').write_text(json.dumps(completion, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=result['status'], summaries=summaries,
                         candidate_minus_reference=deltas,
                         paired_transition_counts={s: {k: v['n'] for k, v in t.items()} for s, t in changes.items()}), indent=2))


if __name__ == '__main__':
    main()
