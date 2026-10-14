"""Register one bounded TRAIN-hard-weight factor after actual E8 failure review."""
import datetime
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.evaluate_ai_baseline import sha
from tools.ai_bounded_hard_weights import class_normalized_weights


def main():
    session = ROOT/'experiments/session_20261007_ai_loop_01'
    destination = session/'HARD_EXPERIMENT_PROTOCOL.json'
    if destination.exists():
        raise ValueError('Existing registration must never be overwritten')
    reviews = ['E8_all_normal_alert_sheets', 'E8_remaining_positive_sheets',
               'E8_remaining_head_mask_disagreement_sheets']
    expected = [259, 61, 225]
    for name, count in zip(reviews, expected):
        directory = session/name
        completed = json.loads((directory/'completion.json').read_text())
        if (not completed['status'].startswith('completed_actual_native_')
                or completed['total_selected_cases'] != count
                or sha(directory/'per_case_visual_review.json') != completed['per_case_review_sha256']):
            raise ValueError('Completed actual native failure review required: '+name)
    comparison_path = ROOT/'experiments/AI_E7_E8_PRESENCE_PAIR_r3/comparison.json'
    comparison = json.loads(comparison_path.read_text())
    if not comparison['decision'].startswith('REJECT'):
        raise ValueError('Review the previous pair before registering another factor')
    initial_run = 'experiments/AI_E7_v3_presence_reference_r2'
    run = ROOT/initial_run
    bundle = json.loads((run/'bundle.json').read_text())
    if bundle['epoch'] != 10 or bundle['global_epoch'] != 18 or bundle['presence_weight'] != 0:
        raise ValueError('The evidence-selected reference initializer changed')
    if sha(run/'best_model.pt') != bundle['checkpoint_sha256']:
        raise ValueError('Selected checkpoint differs from measured bundle')
    if json.loads((run/'state.json').read_text())['status'] != 'completed':
        raise ValueError('Completed full reference required')
    catalog = 'experiments/AI_TRAIN_HARD_REFRESH_E7_E8_v3_r2'
    manifest = 'experiments/data_v3_reliability_20261007/manifest.json'
    rows = [r for r in json.loads((ROOT/manifest).read_text())['rows'] if r['split'] == 'train']
    hp = json.loads((ROOT/catalog/'HARD_POSITIVE_SET.json').read_text())['image_ids']
    hn = json.loads((ROOT/catalog/'HARD_NEGATIVE_SET.json').read_text())['image_ids']
    weights = class_normalized_weights(rows, hp, hn, 2)
    if len(rows) != 2808 or len(hp) != 109 or len(hn) != 713:
        raise ValueError('Frozen TRAIN catalog membership changed')
    protected = {
        'best_model.pt': '922f30bf691b9979aee65d386bcf73d2643558c049a7d11ab013fea315f39b81',
        'FracAtlas.zip': '747119b26f2684e0e35a7688083b14b12a206149b0cfe5357824b69b3a5e6cf8',
        'BASELINE_MODEL_REPORT.md': '3d5e5e6149882d23cb5a145665f534d5f810e3815c913ba6bc66ccb2699dd12b',
        manifest: '4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318'}
    for path, digest in protected.items():
        if sha(ROOT/path) != digest:
            raise ValueError('Protected identity differs: '+path)
    reference, candidate = 'AI_E9_v3_hard_reference', 'AI_E10_v3_hard_weight2'
    audit_ids = ['AI_AUDIT_E9_v3_hard_reference', 'AI_AUDIT_E10_v3_hard_weight2']
    fit_ids = ['AI_LEARNING_FIT_E9_v3_hard_reference', 'AI_LEARNING_FIT_E10_v3_hard_weight2']
    pair_id = 'AI_E9_E10_HARD_PAIR'
    smoke_output = 'experiments/AI_HARD_MODEL_SMOKE_20261008'
    for name in [reference, candidate, *audit_ids, *fit_ids, pair_id, Path(smoke_output).name]:
        if (ROOT/'experiments'/name).exists():
            raise ValueError('Registered output already exists: '+name)
    paths = list(protected) + [
        'best_model_threshold.json', 'medvision_ai.py', 'medvision_pipeline.py',
        'tools/register_ai_hard_pair.py', 'tools/train_ai_hard_candidate.py',
        'tools/smoke_ai_hard_candidate.py', 'tools/ai_hard_example_loss.py',
        'tools/ai_bounded_hard_weights.py', 'tools/ai_presence_model.py',
        'tools/ai_cached_dataset.py', 'tools/ai_atomic_io.py',
        'tools/train_ai_presence_candidate.py', 'tools/train_reliability_candidate.py',
        'tools/cache_ai_training_inputs.py', 'tools/ai_metrics.py', 'tools/run_experiment.py',
        'tools/queue_ai_hard_pair.py', 'tools/audit_ai_presence_candidate.py',
        'tools/audit_ai_presence_train_fit.py', 'tools/ai_error_groups.py',
        'tools/analyze_ai_hard_pair.py', 'tools/analyze_ai_pair.py',
        'tools/ai_validation_audit.py', 'tools/evaluate_ai_baseline.py',
        'tools/audit_ai_learning_fit.py',
        str(comparison_path.relative_to(ROOT)),
        'experiments/AI_E7_E8_PRESENCE_PAIR_r3/completion.json',
        str((session/'LOOP_PROTOCOL.json').relative_to(ROOT)),
        initial_run+'/config.json', initial_run+'/bundle.json',
        initial_run+'/best_model.pt', initial_run+'/epoch_010_resume.pt',
        catalog+'/config.json', catalog+'/completion.json',
        catalog+'/HARD_POSITIVE_SET.json', catalog+'/HARD_NEGATIVE_SET.json',
        catalog+'/proposed_example_weights.json',
        'experiments/AI_TRAIN_CACHE_v3_256_r2/completion.json',
        'experiments/AI_TRAIN_CACHE_v3_256_r2/rows.json',
        'experiments/AI_TRAIN_CACHE_v3_256_r2/verification.json',
        'experiments/AI_LEARNING_FIT_E7_v3_presence_r2/config.json',
        'experiments/AI_LEARNING_FIT_E7_v3_presence_r2/train_cases.jsonl',
        'experiments/AI_LEARNING_FIT_E8_v3_presence_r2/config.json',
        'experiments/AI_LEARNING_FIT_E8_v3_presence_r2/train_cases.jsonl']
    for name in reviews:
        paths += [str((session/name/file).relative_to(ROOT))
                  for file in ('completion.json', 'per_case_visual_review.json')]
    result = dict(
        status='registered_after_completed_native_failure_analysis',
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        major_factor='bounded_within_class_hard_example_weighting',
        reference=reference, candidate=candidate, initial_run=initial_run,
        hard_catalog=catalog, smoke_output=smoke_output, audit_ids=audit_ids,
        fit_ids=fit_ids, pair_id=pair_id,
        evidence=[
            'E8 rejected: 94 extra normal alerts and 13 fewer case misses than E7; native false-positive pixels235568 to696136, IoU0.5 matched instances23 to19',
            'All259 E8 normal alerts,61 tagged positive segmentation failures and225 head/mask disagreements actually reviewed, including linked earlier reviews',
            'Both raw TRAIN fits remain poor; E7 positive Dice0.273254 and219/493 zero-overlap cases, E8 Dice0.252724 and224/493 zero-overlap cases; not a validation-only shift',
            '109 historical TRAIN hard positives and713 TRAIN hard negatives remain wrong in both selected checkpoints; catalogs contain no VAL/CAL/test cases'],
        initialization=dict(selected_epoch=10, global_epoch=18,
            snapshot=initial_run+'/epoch_010_resume.pt',
            optimizer='Restore exact selected full model and Adam independently in both arms; retain moments and step counters',
            reason='E7 is the unchanged normalBCE1 segmentation reference; reject E8 supervision rather than combining two interventions'),
        common_config=dict(additional_epochs=12, batch_size=2, lr=.0001, seed=42,
            global_epochs=list(range(19,31)), presence_weight=0, normal_bce_weight=1,
            segmentation_loss='Existing BCE+Dice; factor1 exact scalar/output-gradient parity',
            preprocessing='Unchanged CLAHE2/tile8/blur3/unit, stretch256',
            sampling='All2808 unique TRAIN images once per epoch with matched epoch-seeded shuffle and augmentation; no resampling or duplication',
            selection='Unchanged common feasible-first/minimum normalized TP79,TN342,Dice0.5237965563,IoU0.3775685933; earlier ties',
            masks='Independent native bilinear probabilities, fixed threshold0.5/all; no head gating'),
        factor=dict(reference=1,candidate=2,hard_positive_count=len(hp),hard_negative_count=len(hn),
            normalization='Each source-label class retains mean weight1 and its original total mass',
            minimum_weight=min(weights.values()),maximum_weight=max(weights.values()),
            no_duplicate_images=True,source_sampling_distribution_preserved=True),
        acceptance='Frozen LOOP_PROTOCOL unchanged: TP>=79,TN>=342 plus native Dice/IoU/localization improvement and fewer false-positive pixels without unacceptable useful-coverage loss; then independent calibration/robustness/final freeze',
        input_hashes={path:sha(ROOT/path) for path in paths},
        calibration_fit=False,test_images_read=0,promotion=False,
        limitations=['One seed cannot establish stable generalization',
                    'Source patient/study IDs and clinical subtype adjudications unavailable',
                    'Warm continuation alone cannot isolate weighting; only the matched two-arm comparison can'])
    with destination.open('x', encoding='utf-8') as handle:
        json.dump(result,handle,indent=2,allow_nan=False)
    print(json.dumps(dict(protocol=str(destination.relative_to(ROOT)),sha256=sha(destination),
                         reference=reference,candidate=candidate),indent=2))


if __name__ == '__main__':
    main()
