"""Read-only, deliberately bounded projection of recorded research evidence."""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def read_json(path, fallback=None):
    try:
        if path.stat().st_size > 8_000_000:
            return fallback
        return json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        return fallback


def snapshot(root: Path, active_bundle_path=None):
    manifest = read_json(root / 'experiments/data_v2/manifest.json', {})
    counts = Counter(r['split'] for r in manifest.get('rows', []))
    queue = read_json(root / 'experiments/session_20261006_p6p7/training_queue.json', {})
    runs = []
    for name, label in [('E2_corrected_baseline', 'E2 · Natural sampling'),
                        ('E3_v2_logits_bce_dice', 'E3 · Balanced BCE + Dice'),
                        ('E4_v2_logits_focal_tversky', 'E4 · Balanced focal Tversky')]:
        folder = root / 'experiments' / name
        state = read_json(folder / 'state.json', {})
        epochs = []
        try:
            for line in (folder / 'epochs.jsonl').read_text(encoding='utf-8').splitlines()[-100:]:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue  # A concurrent append can leave the last line incomplete.
                metric = row['validation'].get('delivered', row['validation'])
                epochs.append({'epoch': row['epoch'], 'dice': metric['mean_positive_dice'],
                               'sensitivity': metric['case_sensitivity'],
                               'falsePositiveRate': metric['normal_false_positive_rate']})
        except (OSError, KeyError, TypeError):
            pass
        runs.append({'id': name, 'label': label, 'status': state.get('status', 'queued' if name in queue.get('runs', []) else 'not_started'),
                     'epoch': state.get('current_epoch', state.get('epochs_finished', state.get('latest_epoch', 0))),
                     'batch': state.get('batch'), 'batches': state.get('batches'), 'epochs': epochs,
                     'dataset': 'v1 · seven contradictory train images retained' if name.startswith('E2') else 'v2 · contradictory train images quarantined'})
    original = read_json(root / 'experiments/E1_historical_validation/metrics.json', {})
    development = read_json(root / 'experiments/P6_development_validation/metrics.json', {})
    completion = read_json(root / 'experiments/FINAL_v2_20261006/completion.json', {})
    active = read_json(Path(active_bundle_path), {}) if active_bundle_path else {}
    return {'updatedAt': datetime.now(timezone.utc).isoformat(),
            'dataset': {'available': bool(counts), 'total': sum(counts.values()), 'train': counts['train'], 'validation': counts['val'], 'test': counts['test'],
                        'version': 'FracAtlas v6 · audited split v2', 'quarantined': 7,
                        'patientIndependenceVerified': manifest.get('patient_independence_verified', False)},
            'runs': runs, 'queueStatus': queue.get('status', 'not_available'),
            'historical': original.get('baseline'), 'development': development.get('metrics'),
            'delivery': {'model': 'Frozen v2 research model' if active else 'Original diagnostic checkpoint', 'threshold': active.get('postprocess', {}).get('threshold', .9),
                         'finalModelFrozen': bool(completion.get('frozen')), 'reservedTestEvaluated': bool(completion.get('final_test_evaluated')),
                         'priorCheckpointExposure': 'Unknown; historical metrics are diagnostic only'},
            'limits': ['Research prototype; predictions are not a diagnosis.',
                       'Historical checkpoint training exposure is unknown.',
                       'Patient independence and expert annotation review remain unverified.',
                       'Final comparisons, model freeze and reserved-test evaluation remain pending.']}
