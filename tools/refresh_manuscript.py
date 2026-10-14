"""Regenerate a research manuscript from saved measurements; never infer results."""
import argparse
import csv
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research_status import snapshot


def refresh(final_dir=None):
    evidence = snapshot(ROOT)
    manifest = json.loads((ROOT / 'experiments/data_v2/manifest.json').read_text())
    positive = sum(int(r['fractured']) for r in manifest['rows'])
    historical = evidence['historical']
    e2 = evidence['runs'][0]['epochs']
    measured = []
    final = None
    if final_dir:
        final_dir = Path(final_dir).resolve()
        final = json.loads((final_dir / 'completion.json').read_text())
        for name in final['frozen']['pipelines']:
            for split, directory in [('validation', 'validation'), ('reserved test', 'reserved_test')]:
                path = final_dir / name / directory / 'completed.json'
                if path.exists():
                    result = json.loads(path.read_text())
                    if result['smoke']:
                        raise ValueError('Smoke results cannot enter the final experiment table')
                    measured.append({'run': name, 'split': split, 'threshold': result['selection']['threshold'],
                                     'policy': result['selection']['policy'], **result['metrics']})
        if final['final_test_evaluated'] and len([r for r in measured if r['split'] == 'reserved test']) != 2:
            raise ValueError('Final completion claims test results without both saved comparison rows')
    final_ready = bool(final and final['final_test_evaluated'])
    table = '\n'.join(f"| {r['run']} | {r['split']} | {r['threshold']:.2f}/{r['policy']} | {r['mean_positive_dice']:.4f} | {r['mean_positive_iou']:.4f} | {r['case_sensitivity']:.4f} | {r['normal_false_positive_rate']:.4f} |" for r in measured)
    training = '\n'.join(f"| {r['epoch']} | {r['dice']:.4f} | {r['sensitivity']:.4f} | {r['falsePositiveRate']:.4f} |" for r in e2)
    last = e2[-1] if e2 else None
    status = 'Measured manuscript; author/guide review and venue formatting outstanding.' if final_ready else 'Development manuscript. Full v2 training, final comparison and reserved-test results remain pending.'
    draft = f'''# Auditing data and failure modes in an Attention U-Net fracture-segmentation prototype

**Status:** {status}

## Abstract

This project develops a reproducible fracture-segmentation research workflow and a local application for inspecting musculoskeletal radiographs. We audit FracAtlas v6, preserve all fracture instances in a binary union target, and explicitly include normal images. Of 4,083 source images, 59 decode failures and seven training images in contradictory exact-duplicate label groups are excluded from a separate v2 manifest. The resulting 4,017 images include {positive} positive and {4017-positive} normal cases, with fixed training/validation/test splits of 2,808/612/597. An original checkpoint with unknown training exposure achieves mean positive Dice {historical['mean_positive_dice']:.4f} on diagnostic validation, but falsely flags {historical['case_false_positive']}/502 normal images. Fresh v1 E2 training and matched v2 BCE+Dice/focal-Tversky runs examine imbalance and preprocessing changes. {('Both v2 operating points were selected on validation, frozen, and evaluated on the reserved test. Final measured results are reported below.' if final_ready else 'The controlled v2 comparison is ongoing; no final held-out performance is claimed.')} The application provides protected case history, native-size original/overlay inspection and traceable exports. We distinguish software verification from model generalisation and clinical validation.

## 1. Introduction

Pixel-level localisation makes model output inspectable, but image-level sensitivity alone cannot establish correct fracture localisation. A model can highlight normal anatomy or predict a region far from an annotated fracture. We therefore report positive-case mask overlap together with normal-case false alarms, case confusion and one-to-one region matching. The contribution is a documented audit and reproducible engineering study, rather than a claim of a new architecture or clinically validated diagnosis.

Attention U-Net provides the segmentation backbone [2]. FracAtlas supplies fracture labels and localisation annotations [1]. Our evaluation separates several failure modes in line with task-specific metric selection [3]. We compare BCE+Dice with focal Tversky under a controlled protocol; the broader implemented loss family follows documented imbalance-aware formulations [4]. Implementing a loss does not establish that it improves this dataset.

## 2. Data audit and split protocol

The owner-provided ZIP exactly matches FracAtlas **v6**, 338,412,750 bytes, published MD5 `931dd40ad6e070bb0724d66cfbbef9f0`, SHA-256 `747119b26f2684e0e35a7688083b14b12a206149b0cfe5357824b69b3a5e6cf8`. The dataset is CC BY 4.0 and requires attribution. We join dataset metadata, archive images and COCO annotations. Decode failures are excluded with explicit image IDs; missing data is never replaced with synthetic training images.

Grouping checks cover exact decoded copies and reviewed near-duplicate candidates. No known group spans the frozen splits, but absent reliable patient identifiers prevent a claim of patient-level independence. The audit reviewed 217 non-exact candidate pairs and identified seven contradictory exact-copy training labels. V2 quarantines all seven while preserving the validation and test assignments. Fourteen same-positive exact-copy annotation disagreements remain documented; no expert relabelling is invented. Full evidence and data dictionary: `experiments/phase3_review/`.

V2 SHA-256 is `19a950c34d96c0fc076fbb75bdeffbf2f0b262626817d61018eff31e907544bb`. Training contains 493 positive and 2,315 normal images; validation 110/502; reserved test 111/486. Data augmentation and weighted replacement sampling apply only to training. E2 remains on preserved v1, containing the seven contradictory training images; it is not represented as a v2 baseline.

## 3. Methods and registered experiments

The architecture is AttentionUNet64. Historical inference uses sigmoid probabilities, a stretched 256 × 256 input, CLAHE clip limit 2 with an 8 × 8 tile grid, Gaussian kernel 3 and unit scaling. Its retained threshold is .90, with historical calibration provenance unverified. Fresh E2 uses natural sampling, BCE+Dice, conservative augmentation, seed 42, Adam 1e-4, batch 2, a 12-epoch ceiling and patience 5. E2 weights are saved separately from the original checkpoint.

The matched v2 runs use a binary-logits output contract, 256 × 256 letterboxing, CLAHE, no Gaussian blur, unit scaling, padded-pixel loss exclusion and a 50% requested training positive fraction. E3 uses BCE+Dice; E4 changes only the loss to focal Tversky (false-negative weight .7, false-positive weight .3, exponent .75). Architecture, split, preprocessing, sampler, seed, optimiser, learning rate, batch size and stopping rule are otherwise matched. Each run records its exact configuration, code hashes and completed-epoch checkpoints. A single seed cannot establish robustness across random initialisation.

Operating points are selected exclusively on validation over thresholds .05–.95 in .05 increments and policies all/largest/minimum16 native pixels. A candidate must remain within two percentage points of its own .50/all sensitivity and normal false-positive rate. Positive Dice ranks admissible candidates; an all-components policy is preferred within .005 Dice. Across full v2 runs, the simpler BCE+Dice model is retained for improvements smaller than .005 when sensitivity and false alarms remain within two points. Both configurations, source identity and validation-only winner are frozen before the reserved test is read. No test-driven retuning or automatic clinical endorsement is permitted.

Evaluation and serving share the same native inverse probability transform and component policy. Positive Dice and IoU exclude normal cases. Empty predictions on positive images score zero overlap. Normal images are evaluated through case false-positive rate and false-positive region counts, rather than a favourable empty-mask Dice. Pixel precision is undefined when there are no predicted pixels; case precision is undefined when no cases are flagged. Saved integer TP/FP/FN counts reproduce the reported tables exactly.

Region matching maximises admissible one-to-one matches at IoU .10 and .50. A single predicted component cannot count as recovery of multiple ground-truth instances. Uncertainty uses 1,000 duplicate/related-image-group bootstrap replicates with seed 42; these groups are not verified independent patients. Degenerate intervals do not establish zero population error. Qualitative examples follow an explicit best/worst positive, first normal and first multi-instance rule, rather than displaying only attractive outputs.

## 4. Measured results

### 4.1 Original-checkpoint diagnostic

On all 612 validation images, the retained .90/all checkpoint produces mean positive Dice {historical['mean_positive_dice']:.4f}, IoU {historical['mean_positive_iou']:.4f}, sensitivity {historical['case_sensitivity']:.4f} and normal false-positive rate {historical['normal_false_positive_rate']:.4f}. TP/FN/FP/TN are {historical['case_true_positive']}/{historical['case_false_negative']}/{historical['case_false_positive']}/{historical['case_true_negative']}. Positive Dice's grouped 95% interval is [0.4227, 0.5375]. Exposure to these images during the checkpoint's original development is unknown; these are diagnostic observations, not independent test results. Threshold/policy changes in the historical grid do not solve its normal-case failure.

### 4.2 E2 development trajectory

| Completed epoch | Positive Dice | Sensitivity | Normal false-positive rate |
|---:|---:|---:|---:|
{training}

{('The latest completed epoch is '+str(last['epoch'])+'. Its results replace an all-zero epoch-1 snapshot as the latest development observation; the historical snapshot remains archived.' if last else 'No completed epoch result is available.')}
The epoch-1 Phase 6 snapshot missed all 110 positive cases and all 137 annotated regions, demonstrating background collapse. Later records must be interpreted alongside their normal false alarms. A decrease in training loss or increase in positive Dice alone does not establish a useful detection operating point. These v1 records are not the matched v2 final comparison.

### 4.3 Controlled v2 comparison

| Run | Split | Threshold/policy | Positive Dice | Positive IoU | Sensitivity | Normal false-positive rate |
|---|---|---|---:|---:|---:|---:|
{table if table else '| E3 / E4 | Pending full training | Unselected | — | — | — | — |'}

{('The winner was selected on validation before either reserved-test row was available. Per-case counts, grouped intervals, subgroup tables, one-to-one region counts and rank-selected examples are archived under '+str(final_dir.relative_to(ROOT) if final_dir.is_relative_to(ROOT) else final_dir)+'. No final test tuning was performed.' if final_ready else 'No reserved-test result has been produced. Queued training and smoke tests are not reported as final model performance.')}

### 4.4 Runtime and application evidence

The CPU-only host has an Intel i5-13500HX and an RTX 3050 6 GB device reporting Windows Code 43; CUDA is unavailable. E2's original PyTorch 2.9.1+cpu environment is preserved. Serving and v2 training use an isolated patched PyTorch 2.14.1+cpu environment with Pillow 12.3.0. Historical diagnostic warm-forward median/p95 were 505.4/1209.5 ms; the epoch-1 Phase 6 run measured 763.2/924.5 ms while E2 was concurrent. These runs measure different session conditions and do not support a speedup claim. Full request latency and shared inference timing are recorded separately; training and browser work can affect both.

Application verification covers distinct positive and normal validation uploads, original-byte integrity, native mask/overlay ownership, JSON export, session restoration, logout revocation, other-account isolation, malformed and oversized inputs, metadata decompression bombs, queue/time limits, persistence and mobile/dark layouts. The recorded normal example receives a false-positive region; the demonstration deliberately exposes this behaviour. Serving masks exactly matched direct shared inference, and two examples reproduced historical native counts across runtime versions. This is limited parity evidence, not exhaustive cross-version equivalence.

## 5. Application and reproducibility

The local FastAPI/React application stores account-owned cases transactionally in SQLite. Sessions use hashed random tokens with eight-hour expiry and HttpOnly/SameSite Strict cookies; passwords use salted PBKDF2-SHA256 with 600,000 iterations. Images and exports require ownership checks. The service uses maintained multipart parsing, actual JPEG/PNG decoding, dimensional and byte bounds, bounded inference concurrency and a timeout that retains the worker lock until native execution exits. Persistent histories are preserved; explicit deletion is restricted to owned, inactive cases.

The dashboard shows real case activity and recorded training progress. A Research page explains the dataset, metrics and pending delivery gates. Results display original/overlay, model identity, native dimensions and operating threshold, without invented confidence, upload accuracy, clinical severity or approval actions. Local signup creates account-owned research access and a single-display recovery code. Recovery verifies that code, issues a ten-minute single-use reset token and revokes prior sessions; a rotated recovery code replaces the old one. No email-delivery service is configured or claimed. The explicitly shared loopback demo supports credential prefill; personal accounts do not. Admin/audit placeholders remain disabled. The launcher binds loopback and disables forwarded-IP trust. Remote deployment would need TLS, Secure cookies and operational controls.

Source snapshots preserve the owner's existing changes because the parent Git root is the user home. Source/evidence packages exclude private databases, credentials, uploaded history, original weights and dataset ZIP. Reproduction instructions specify provider retrieval, exact archive/checkpoint hashes, lockfiles, split IDs and research examples. Tests and source-copy reproduction are documented in `experiments/session_20261006_p6p7/` , `experiments/session_20261006_completion_ui/` and `experiments/session_20261006_auth/`. Another teammate's independent reproduction has not been claimed.

## 6. Limitations and discussion

This is a single-dataset, single-seed research study on a CPU-constrained host. Unknown historical checkpoint exposure, unverified patient independence, annotation disagreements, label noise retained in E2, and lack of expert validation restrict interpretation. No external-site generalisation, calibrated probability reliability, clinical severity grading, diagnostic accuracy or prospective patient benefit is established. High normal false-positive rates can make a superficially sensitive model unsuitable for screening. Pixel-area geometry depends on image resolution and cannot establish anatomical or clinical severity.

The controlled v2 comparison isolates the loss change between E3 and E4; it does not isolate every change from historical preprocessing or from E2. Independent architecture baselines, repeated seeds and optional higher-resolution experiments remain beyond currently measured evidence. The study reports failure rather than presenting negative findings as completion of a successful diagnostic system.

## 7. Conclusion

The project provides an audited dataset protocol, explicit normal-case evaluation, native evaluation/serving consistency and a working research interface with protected reproducible outputs. Historical performance reveals a substantial false-alarm failure despite high image-level sensitivity. {('The final controlled results above quantify the selected v2 operating point on the frozen reserved test; author review is required before submission.' if final_ready else 'The full v2 comparison and reserved-test measurements must finish before a final model-performance conclusion can be drawn.')}

## References

1. Abedeen I, Rahman MA, Prottyasha FZ, et al. FracAtlas: A Dataset for Fracture Classification, Localization and Segmentation of Musculoskeletal Radiographs. Scientific Data 10, 521 (2023). https://doi.org/10.1038/s41597-023-02432-4 . Dataset v6: https://doi.org/10.6084/m9.figshare.22363012.v6 .
2. Oktay O, Schlemper J, Le Folgoc L, et al. Attention U-Net: Learning Where to Look for the Pancreas. arXiv:1804.03999 (2018). https://arxiv.org/abs/1804.03999 .
3. Maier-Hein L, Reinke A, Godau P, et al. Metrics reloaded: recommendations for image analysis validation. Nature Methods 21, 195–212 (2024). https://doi.org/10.1038/s41592-023-02151-z .
4. Yeung M, Sala E, Schonlieb CB, Rundo L. Unified Focal loss: Generalising Dice and cross entropy-based losses to handle class imbalanced medical image segmentation. Computerized Medical Imaging and Graphics 95, 102026 (2022). https://arxiv.org/abs/2102.04525 .

## Author and submission statement

AI tools assisted implementation and drafting. Author agreement, guide review, venue formatting, reference-count requirements, originality checks and independent technical review remain outstanding. No submission, acceptance or clinical endorsement is claimed. The institutional project report is separate and deferred at the owner's request. Completed project target: 10 October 2026; poster handled separately by the owner.
'''
    paper = ROOT / 'paper'
    paper.mkdir(exist_ok=True)
    destination = paper / ('MEASURED_RESEARCH_PAPER.md' if final_ready else 'MANUSCRIPT_DRAFT.md')
    destination.write_text(draft, encoding='utf-8')
    if measured:
        with (paper / 'controlled_results.csv').open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(measured[0]))
            writer.writeheader(); writer.writerows(measured)
    print(destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--final-dir')
    refresh(parser.parse_args().final_dir)
