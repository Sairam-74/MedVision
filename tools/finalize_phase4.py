"""Finish Phase 4 resume records from actual tests and training artifacts."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from medvision_pipeline import sha


def main():
    root=Path(__file__).resolve().parents[1]
    session=root/'experiments/session_20261006'
    out=root/'experiments/phase4_checks'
    checks=json.loads((out/'checks.json').read_text())
    overfit=json.loads((root/'experiments/P4_overfit_128/result.json').read_text())
    api=json.loads((session/'phase4_bundle_api.json').read_text())
    legacy=json.loads((session/'runtime_smoke.json').read_text())
    smoke=json.loads((root/'experiments/P4_trainer_smoke/state.json').read_text())
    assert overfit['acceptance_passed'] and smoke['epochs_finished']==2 and smoke['smoke']
    assert api['invalid_bundle_status']==503 and api['logits_as_legacy_rejected_status']==503
    assert all(s['pipeline_api_masks_identical'] for s in api['samples'])
    assert legacy['invalid_upload_statuses']==[422,415,413] and legacy['oversized_dimensions_status']==413
    for s in ('256','512'):
        assert not checks['letterbox_annotation_survival'][s]['lost_instances']
    active=root/'experiments/E2_corrected_baseline'
    config=json.loads((active/'config.json').read_text())
    assert sha(root/'medvision_ai.py')==config['medvision_source_sha256']
    assert sha(root/'tools/train_baseline.py')==config['source_sha256']
    originals={name:sha(root/name) for name in ['best_model.pt','best_model_threshold.json','FracAtlas.zip']}
    assert originals['best_model.pt']==config['original_checkpoint_sha256']
    assert originals['FracAtlas.zip']==config['archive_sha256']
    assert originals['best_model_threshold.json']=='02d33de4874bcb22816225b8c0834123388f90505a16a3953b7e452a103e3830'
    state=json.loads((active/'state.json').read_text())
    epochs=[json.loads(line) for line in (active/'epochs.jsonl').read_text().splitlines()]
    first=epochs[0]
    positive_native=next(s['native_positive_dice'] for s in api['samples'] if s['native_positive_dice'] is not None)
    report=f'''# Phase 4 pipeline execution evidence

Executed 6 October 2026. All computational Phase 4 tasks implemented and checked. Full-model generalization, final calibration and clinical/expert approval are separate outstanding work. Historical serving and active E2 source/config/data were preserved.

## Implemented pipeline

`medvision_pipeline.py` supplies one preprocessing path for training, validation and opt-in serving: aspect-preserving letterbox or declared stretch, configurable size (multiple of 16), CLAHE, Gaussian blur (zero disables), and unit or image-only z-score normalization. Targets use nearest-neighbor interpolation. A valid-region mask excludes padding and out-of-frame augmentation regions from every loss. Native prediction probability maps remove padding and use bilinear inverse resizing before thresholding; raw/delivered masks and metrics are computed in native coordinates. Synthetic rectangle roundtrip IoU is {checks['letterbox_roundtrip']['iou']:.6f}; image/mask dimension and padding checks pass.

Lazy data reads the explicit v2 manifest (2,808 train / 612 validation; no test prediction path in the trainer). Training-only weighted replacement sampling accepts a requested positive fraction; natural-prevalence shuffle remains available. A seeded 50% sampler drew {checks['seeded_sampler_and_augmentation']['sampled_positive_fraction']*100:.3f}% positives in 2,808 draws. Validation resampling is rejected.

The output contract is **binary-logits-v2**. AttentionUNet64 emits logits directly; BCEWithLogitsLoss receives logits. Sigmoid is applied exactly once for overlap losses and inference. Historical parameter names are retained, but logits checkpoints require their bundle metadata and cannot be selected through the legacy sigmoid backend path. `/ready` rejects that misuse and bad checksums with 503. The historical checkpoint remains the default; no smoke/overfit weights were promoted.

`tools/train_pipeline.py` supports immutable new-run directories, epoch-boundary optimizer resume, source/config/manifest checks, initial recovery checkpoints, epoch-local seeds, LR, individual loss terms, valid foreground occupancy, augmented nonempty prevalence, native raw and delivered precision/recall/Dice/case errors, memory/time and per-case counts. The four-training/four-validation smoke and resume to epoch 2 passed. Its zero tiny-validation Dice is not a performance result.

## Loss conventions and checks

- BCE + Dice: unweighted valid-pixel BCEWithLogits averaged per image, plus foreground soft Dice averaged per image. Empty-target Dice alone has weak gradients, so BCE remains present.
- Focal Tversky: TI=(TP+smooth)/(TP+0.7*FN+0.3*FP+smooth), loss=(1-TI)^0.75. This weights missed foreground more than false positives; it does not inherently suppress normal-case findings.
- Symmetric binary Unified Focal: two-class foreground/background focal CE with gamma=0.5 and class weights 0.7/0.3; two-class Tversky region loss exponent 1-gamma=0.5; mixture weight 0.5. This follows the symmetric convention in the [authors' implementation](https://github.com/mlyg/unified-focal-loss/blob/main/loss_functions.py), not the asymmetric variant. [Primary paper](https://arxiv.org/abs/2102.04525). The independent NumPy calculation agrees with PyTorch within 1e-6. Focal modulation is clamped at 1e-7 to avoid infinite fractional-power derivatives at saturated sigmoid values.

All three losses pass finite-value/gradient checks on empty, full, thin, multiple-region and extreme +/-100-logit cases. Padded logits can change arbitrarily without changing loss; their gradients are exactly zero. These checks caught and corrected the saturation-gradient issue before experiment execution. [PyTorch BCEWithLogitsLoss](https://pytorch.org/docs/stable/generated/torch.nn.BCEWithLogitsLoss.html) supplies the stable BCE term.

## Resize and augmentation inspection

All **919 annotation instances across 714 positive v2 images** were rasterized and checked structurally at letterbox 256 and 512. **Zero instances and zero positive unions vanished**. Minimum positive unions contain 33 pixels at 256 and 138 at 512. Test targets were included only for structural data integrity; no test predictions, failure selection or tuning occurred. Survival is not proof of boundary accuracy or clinical adequacy; resolution comparisons still require measured validation experiments.

Local RNGs drive paired flip/rotation for image, target and valid region. Strict torch deterministic algorithms are enabled; results across library versions/devices are not guaranteed identical. Replacement-sampled repetitions of an image receive the same augmentation within an epoch, documented as a reproducibility tradeoff. Conservative +/-15-degree rotation and horizontal flip preserve binary masks and valid-region alignment. The reviewed optional elastic candidate visibly bends straight hardware and anatomy: **disabled by default and not clinically approved**, not adopted on the strength of these checks. `augmentation_review.png` records three training examples with original, conservative and elastic-candidate views.

## Real learning and shared API inference

A fresh AttentionUNet64 memorized IMG0003183.jpg (largest positive training occupancy) and IMG0000000.jpg (normal), at letterbox 128, no augmentation, BCE+Dice, Adam 1e-3, seed 42. Fixed-threshold acceptance was positive grid Dice >=0.85 and zero normal foreground pixels. It **passed after {overfit['final']['step']} updates**: grid Dice **{overfit['final']['positive_grid_dice']:.6f}**, normal pixels **0**, total loss **1.625443 -> {overfit['final']['loss_components']['total']:.6f}**, approximately **{overfit['final']['elapsed_seconds']:.2f} seconds** alongside the active CPU job. Native positive Dice from the inverse/shared serving path is **{positive_native:.6f}**. Grid and native scores differ due to resize/interpolation; do not mix their coordinate systems. Native target/prediction overlays were inspected in `experiments/P4_overfit_128/native_overfit_examples.png`.

These are deliberately easy, repeatedly seen training cases: **memorization sanity only**, not a generalization score, model-selection result or improvement claim. The overfit model/bundle remains isolated and marked accordingly.

Real API multipart upload for both images returned native masks identical to direct bundle/evaluation inference, plus model/bundle/config provenance. Component policies all/largest/min_pixels pass empty/single-pixel/thin/multiple regressions; default all retains every finding. Minimum-component units are **native pixels**, different from E1's historical 256-grid min16. Raw and delivered masks are retained separately. New geometry has native pixel units and returns clinical severity not applicable. Historical real API and 422/415/413 upload/dimension regressions pass after the adapter change. `tools/predict_bundle.py` also executed real inference and exported native mask/overlay/probabilities.

## Existing full training and next experiments

E2 continues unchanged on v1. First measured epoch took **{first['epoch_seconds']/60:.2f} minutes**, training loss **{first['train_loss']:.6f}**. At threshold 0.5, validation positive Dice and sensitivity are **0**, with no predicted findings: early collapse toward background, not improvement. Twelve epochs at that first-epoch duration project roughly **{first['epoch_seconds']*12/3600:.2f} hours**, replacing the optimistic 9–10-hour step projection; later epochs and early stopping can differ. Current live state at recording: `{json.dumps(state)}`. It also retains the seven v1 contradictory targets discovered in Phase 3.

Next full v2 experiment must use a new run ID and the logits pipeline. Treat E2 vs the new pipeline as different protocols, not a matched loss comparison. Matched BCE+Dice / focal-Tversky / symmetric Unified-Focal comparisons must use identical v2 data, geometry, preprocessing, sampler, augmentation, seed and budget. Keep test reserved until model/config selection and calibration are frozen. No second full CPU job was launched during Phase 4.

Evidence: `checks.json`, session `phase4_bundle_api.json` and `runtime_smoke.json`, `experiments/P4_trainer_smoke/`, `experiments/P4_overfit_128/`, `experiments/P4_bundle_cli/`, and `phase4_ledger.json`. Original ZIP/checkpoint/threshold hashes and active source hashes all passed preservation checks.
'''
    (out/'PHASE4_REPORT.md').write_text(report,encoding='utf-8')
    (out/'augmentation_review.json').write_text(json.dumps(dict(reviewed=True,reviewer='Codex technical visual QA',
                                                              ids=checks['augmentation_examples']['train_ids'],
                                                              conservative='Paired masks aligned in inspected examples; not clinical approval',
                                                              elastic='Visible bending of hardware/anatomy; disabled by default, not adopted'),indent=2))
    documents=['PROJECT_STATUS.md','EXPERIMENT_REGISTRY.md','medvision_handoff/MEDVISION_HANDOFF.md',
               'medvision_handoff/MedVision_Master_Todo_and_Research_Paper_Roadmap.md','DEMO.md','paper/MANUSCRIPT_DRAFT.md']
    backup=session/'phase4_documents_before'; backup.mkdir(exist_ok=True)
    for name in documents:
        dest=backup/Path(name).name
        if not dest.exists(): dest.write_bytes((root/name).read_bytes())
    def before(name): return (backup/Path(name).name).read_text(encoding='utf-8')
    update=f'''## CURRENT SESSION - 6 October 2026: Phase 4 executed

- Implemented separate `medvision_pipeline.py` / `tools/train_pipeline.py`: configurable letterbox/stretch, padded-pixel exclusion, shared native transforms, explicit v2 manifest, deterministic paired augmentation, training-only controlled sampler, direct logits BCE+Dice / focal Tversky / symmetric Unified Focal, detailed epoch/checkpoint provenance and resume.
- Computational Phase 4 checks pass: empty/thin/multiple masks, padded loss/gradient exclusion, finite extreme-logit losses, independent UF reference, all 919 v2 instances survive letterbox 256 and 512. Elastic review shows hardware/anatomy bending; default off.
- Real two-training-image overfit passed after 60 updates: grid Dice 0.965251 / zero normal predicted pixels; native Dice 0.913160. This is **memorization sanity only**, not validation performance. Four-train/four-val trainer smoke and resume to epoch 2 pass.
- Opt-in `MEDVISION_BUNDLE` backend and real CLI use the exact shared native inference path. API masks match direct inference; bad bundles/logits-as-legacy selection return 503. Historical default upload/overlay/invalid-input regressions still pass. Original demo model remains selected; smoke weights not promoted.
- **E2 first full epoch:** train loss {first['train_loss']:.6f}; validation at .5 has positive Dice/sensitivity 0, no findings. This is background collapse, not improvement. Measured epoch {first['epoch_seconds']/60:.2f} min; ~{first['epoch_seconds']*12/3600:.2f} h for a 12-epoch ceiling at this rate (early stop/variation apply). Live state snapshot: `{json.dumps(state)}`. E2 still uses v1; seven contradictory training targets disclosed. Do not change its source/data on resume.
- Original checkpoint, threshold, ZIP, v1/v2 manifest hashes and active trainer/medvision_ai.py hashes preserved. No test model evaluation/tuning. Evidence: `experiments/phase4_checks/PHASE4_REPORT.md`, `experiments/session_20261006/phase4_ledger.json`.

Next: assess E2 curves/validation; execute a separately named full v2 logits experiment with recorded sampling/config and compute budget, then matched comparisons. Select/calibrate/freeze on validation before final test. Working browser demo and final measured manuscript/package remain due 10 October; poster handled by user, institutional report later.

'''
    (root/'PROJECT_STATUS.md').write_text(before('PROJECT_STATUS.md').replace('# MedVision Project Status\n','# MedVision Project Status\n\n'+update,1),encoding='utf-8')
    handoff=before('MEDVISION_HANDOFF.md'); head,tail=handoff.split('\n',1)
    (root/documents[2]).write_text(head+'\n\n'+update+tail,encoding='utf-8')
    roadmap=before(documents[3])
    for item in ['4.2','4.3','4.4','4.5','4.6','4.7','4.8','4.9','4.10','4.11','4.14']:
        roadmap=roadmap.replace(f'- [ ] **{item}**',f'- [x] **{item}**')
    roadmap=roadmap.replace('## Phase 5 — Run baseline', 'Phase 4 completion evidence (6 October): `experiments/phase4_checks/PHASE4_REPORT.md`. New versioned pipeline checked; historical/E2 pipeline preserved. Elastic deformation visually reviewed and disabled by default. Overfit scores are training memorization only.\n\n## Phase 5 — Run baseline',1)
    (root/documents[3]).write_text(roadmap,encoding='utf-8')
    registry=before('EXPERIMENT_REGISTRY.md')
    rows='''| P4-pipeline-checks | Passed | Letterbox 256/512, 919 instances; padding/gradients, 3 loss modes, seeded sampler | No annotation lost; requested 50% sampler drew 50.21%; extreme logits finite | `experiments/phase4_checks/checks.json` |
| P4-logits-trainer-smoke | Passed execution/resume | Four train/four val; letterbox128, controlled sampler; direct logits BCE+Dice | Epoch 1 then resume epoch 2; tiny validation Dice 0, not performance | `experiments/P4_trainer_smoke/` |
| P4-real-overfit | Passed memorization only | AttentionUNet64, two training images, letterbox128, BCE+Dice, Adam1e-3, no augmentation | 60 updates; grid Dice .965251, native Dice .913160, normal mask empty; not generalization | `experiments/P4_overfit_128/` |
| P4-bundle-API | Passed | Real multipart uploads; shared native evaluation/serving; explicit contract | Native masks equal; invalid bundles and logits-as-legacy return 503; historical default regressions pass | `phase4_bundle_api.json`, `runtime_smoke.json` in 6 October session |
'''
    registry=registry.replace('| E3-controlled-comparison |',rows+'| E3-controlled-comparison |',1)
    registry+=f'\nPhase 4 E2 update: epoch 1 train loss {first["train_loss"]:.6f}; at .5 validation positive Dice/sensitivity 0 and no predictions. Epoch {first["epoch_seconds"]/60:.2f} min. Background collapse; no improvement claim. Continued unchanged into epoch 2. No v2 full run or final test executed.\n'
    (root/'EXPERIMENT_REGISTRY.md').write_text(registry,encoding='utf-8')
    demo=before('DEMO.md')
    demo+='''
## New Phase 4 logits pipeline (6 October)

The default demo still uses the original historical sigmoid model. New logits weights require a versioned bundle; they cannot be passed as a legacy checkpoint. No smoke/overfit bundle is a selected demo model. Use the same native transform for training, validation and serving. See `experiments/phase4_checks/PHASE4_REPORT.md` for measured checks and limitations.

After checking the existing full CPU job status, start a **new**, explicitly named v2 run (example config, not yet executed):

```powershell
.\\.venv-clean\\Scripts\\python.exe tools/train_pipeline.py --out experiments/E3_v2_logits_bce --epochs 12 --size 256 --loss bce_dice --positive-fraction 0.5
```

Preprocessing flags include `--resize letterbox|stretch`, `--size 256|512`, `--no-clahe`, `--blur 0|3`, and `--normalization unit|zscore`. Loss choices: `bce_dice`, `focal_tversky`, `unified_focal_symmetric`. Omit `--positive-fraction` for natural sampling. Elastic is off; inspected candidate bends hardware/anatomy and has no clinical plausibility approval. Exact flags/source/manifest must match on `--resume`; do not resume E2 using this trainer.

Versioned real inference command (replace paths with the selected/frozen bundle when available):

```powershell
.\\.venv-clean\\Scripts\\python.exe tools/predict_bundle.py --image path/to/xray.jpg --bundle experiments/SELECTED_RUN/bundle.json --out experiments/NEW_INFERENCE
```

For an explicitly selected new backend bundle, set `$env:MEDVISION_BUNDLE` to its absolute bundle.json path before `Start-Demo.ps1`. Leave it unset for the historical default. Bundle metadata/checksum, preprocessing, output contract, threshold and component policy are verified. Unselected research bundles disclose their status; clinical severity is unavailable. Clear the variable with `Remove-Item Env:MEDVISION_BUNDLE` when returning to the historical demo.

Measured E2 epoch 1 took 74.15 minutes and predicted no validation findings at .5. Earlier 9–10-hour projection is superseded by actual timing (~14.83h for 12 comparable epochs, early stopping/variation applies). E2 remains a v1 run with the seven contradictory training targets. No test evaluation performed.
'''
    (root/'DEMO.md').write_text(demo,encoding='utf-8')
    paper=before('MANUSCRIPT_DRAFT.md')
    note='Phase 4 execution addendum (6 October): the new direct-logits, letterbox, padding-aware pipeline passed finite-gradient/alignment/component/API/resume checks. Two deliberately easy training images were memorized after 60 updates (grid Dice .965251; native Dice .913160; zero normal pixels); these are not validation/generalization scores and do not enter the comparison table. Active v1 E2 completed epoch 1 with validation positive Dice/sensitivity zero at .5, consistent with background collapse; later epochs remain pending. No v2 full training or final-test result exists. See `experiments/phase4_checks/PHASE4_REPORT.md`.\n\n'
    (root/documents[-1]).write_text(paper.replace('## Abstract\n',note+'## Abstract\n',1),encoding='utf-8')
    source_files=['medvision_pipeline.py','medvision_serving.py','backend_service.py','tools/train_pipeline.py','tools/verify_pipeline.py',
                  'tools/overfit_pipeline.py','tools/predict_bundle.py','tools/verify_bundle_api.py','tools/verify_runtime_phase4.py','tools/finalize_phase4.py']
    snapshot=session/'phase4_source'; snapshot.mkdir(exist_ok=True)
    for name in source_files:
        (snapshot/name.replace('/','__')).write_bytes((root/name).read_bytes())
    ledger=dict(recorded_utc=datetime.now(timezone.utc).isoformat(),original_sha256=originals,
                active_source_hashes_preserved=True,v1_manifest_sha256=sha(root/'experiments/data_v1/manifest.json'),
                v2_manifest_sha256=sha(root/'experiments/data_v2/manifest.json'),E2_live_state=state,E2_first_epoch=first,
                phase4_checks='passed',overfit=overfit,trainer_resume=smoke,bundle_api=api,test_evaluated=False,
                source_sha256={name:sha(root/name) for name in source_files},
                report_sha256=sha(out/'PHASE4_REPORT.md'),
                next='Separate full v2 logits experiment; matched comparisons, validation selection/calibration, frozen final test, browser demo and final manuscript.')
    (session/'phase4_ledger.json').write_text(json.dumps(ledger,indent=2))
    print(json.dumps({'Phase4':'executed and checked','originals_preserved':True,'active_sources_preserved':True,
                      'overfit_grid_dice':overfit['final']['positive_grid_dice'],'overfit_native_dice':positive_native,
                      'E2_state':state,'E2_first_validation':first['validation']},indent=2))


if __name__=='__main__':
    main()
