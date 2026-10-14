"""Unchanged production-model audit, validation ONLY, immutable outputs.

Never fits, tunes, trains, promotes a model, or reads test image bytes.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import zipfile

import cv2
import numpy as np
import psutil
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import medvision_ai as m
from tools import ai_metrics as metrics


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save(path, data):
    # Final evidence uses exclusive creation, never replacement.
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(data, f, indent=2, allow_nan=False)


def write_csv(path, rows):
    if not rows:
        return
    with path.open('x', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def box(mask):
    ys, xs = np.nonzero(mask)
    return [int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1)]


def panel(image, target, predicted, path, title):
    # Readable offline review artifact; native masks separately retained.
    h, w = image.shape
    size = (max(1, round(w*384/h)), 384)
    gray = cv2.resize(image, size, interpolation=cv2.INTER_AREA)
    base = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    gt = cv2.resize(target, size, interpolation=cv2.INTER_NEAREST).astype(bool)
    pred = cv2.resize(predicted, size, interpolation=cv2.INTER_NEAREST).astype(bool)
    truth, guess = base.copy(), base.copy()
    truth[gt] = (truth[gt]*.5+np.array([0, 255, 0])*.5).astype(np.uint8)
    guess[pred] = (guess[pred]*.5+np.array([0, 0, 255])*.5).astype(np.uint8)
    tiles = []
    for label, tile in zip(('Original', 'Ground truth (green)', 'Prediction (red)'), (base, truth, guess)):
        header = np.zeros((30, size[0], 3), np.uint8)
        cv2.putText(header, label, (5, 20), cv2.FONT_HERSHEY_SIMPLEX, .45, (255, 255, 255), 1)
        tiles.append(np.vstack((header, tile)))
    joined = np.hstack(tiles)
    caption = np.zeros((40, joined.shape[1], 3), np.uint8)
    cv2.putText(caption, title, (5, 25), cv2.FONT_HERSHEY_SIMPLEX, .45, (255, 255, 255), 1)
    if not cv2.imwrite(str(path), np.vstack((caption, joined)), [cv2.IMWRITE_JPEG_QUALITY, 90]):
        raise RuntimeError('Failure panel could not be saved')


def inspect_splits(manifest):
    rows = manifest['rows']
    result = {'patient_independence_verified': False, 'patient_ids_available': False,
              'limitation': 'No reliable patient/study identifiers in supplied CSV. Duplicate-group independence does not establish patient independence.',
              'splits': {s: dict(images=sum(r['split']==s for r in rows), positives=sum(int(r['fractured']) for r in rows if r['split']==s)) for s in ('train','val','test')}}
    for field in ('image_id', 'member', 'sha256', 'decoded_sha256', 'group'):
        seen, violations = {}, []
        for r in rows:
            identity = r[field]
            if identity in seen and seen[identity] != r['split']:
                violations.append(identity)
            seen[identity] = r['split']
        result[field+'_cross_split_count'] = len(set(violations))
        if violations:
            raise ValueError(f'Cross-split leakage found: {field}')
    return result


def figures(out, cases, result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    data = metrics.curves(cases)
    save(out/'curves.json', data)
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    cm = result['classification']['confusion_matrix']
    matrix = np.array([[cm['tn'], cm['fp']], [cm['fn'], cm['tp']]])
    axes[0].imshow(matrix, cmap='Blues')
    for (i, j), n in np.ndenumerate(matrix):
        axes[0].text(j, i, str(n), ha='center', va='center', color='white' if n > matrix.max()/2 else 'black')
    axes[0].set(xticks=[0,1], yticks=[0,1], xticklabels=['Normal','Fracture'], yticklabels=['Normal','Fracture'], xlabel='Predicted', ylabel='Reference', title='Image-level confusion')
    axes[1].plot(data['roc']['fpr'], data['roc']['tpr']); axes[1].plot([0,1], [0,1], '--', color='gray')
    axes[1].set(xlabel='False-positive rate', ylabel='Sensitivity', title='ROC: max-pixel score', xlim=(0,1), ylim=(0,1))
    axes[2].plot(data['precision_recall']['recall'], data['precision_recall']['precision'])
    axes[2].set(xlabel='Recall', ylabel='Precision', title='Precision-recall: max-pixel score', xlim=(0,1), ylim=(0,1))
    fig.tight_layout(); fig.savefig(out/'confusion_roc_pr.png', dpi=160); plt.close(fig)
    curve = result['calibration']['reliability_curve']
    valid = [b for b in curve if b['n']]
    fig, ax = plt.subplots(figsize=(6,5))
    ax.plot([0,1], [0,1], '--', color='gray')
    ax.scatter([b['mean_score'] for b in valid], [b['observed_fracture_fraction'] for b in valid], s=[20+150*b['n']/len(cases) for b in valid])
    ax.set(xlim=(0,1), ylim=(0,1), xlabel='Uncalibrated max-pixel score', ylabel='Observed fracture fraction', title='Proxy reliability; not clinical case confidence')
    fig.tight_layout(); fig.savefig(out/'reliability_curve.png', dpi=160); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = Path(args.out).resolve()
    if ROOT not in out.parents or out.exists():
        raise ValueError('Use a new output directory in the workspace; baseline cannot be overwritten')
    checkpoint, archive = ROOT/'best_model.pt', ROOT/'FracAtlas.zip'
    manifest_path = ROOT/'experiments/data_v2/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    leakage = inspect_splits(manifest)
    if sha(archive) != manifest['archive_sha256']:
        raise ValueError('Archive changed after audit')
    checkpoint_hash = sha(checkpoint)
    if checkpoint_hash != '922f30bf691b9979aee65d386bcf73d2643558c049a7d11ab013fea315f39b81':
        raise ValueError('Original model changed; identify actual production lineage first')
    threshold = m._load_calibrated_threshold(checkpoint)
    out.mkdir(parents=True)
    for name in ('masks', 'failures', 'source_snapshot'):
        (out/name).mkdir()
    sources = ['medvision_ai.py', 'medvision_serving.py', 'tools/evaluate_ai_baseline.py', 'tools/ai_metrics.py']
    for source in sources:
        (out/'source_snapshot'/Path(source).name).write_bytes((ROOT/source).read_bytes())
    torch.set_num_threads(4); cv2.setNumThreads(1); m.set_seed(42)
    config = dict(scope='Unchanged original model, diagnostic validation baseline; prior training exposure unknown. NOT independent locked-test performance.',
                  split='val', test_images_read=0, checkpoint_sha256=checkpoint_hash,
                  manifest_sha256=sha(manifest_path), archive_sha256=sha(archive), threshold=threshold,
                  threshold_metadata_sha256=sha(ROOT/'best_model_threshold.json'), policy='all-components-v1',
                  architecture='Attention U-Net 64/128/256/512/1024, 4 gated skip connections, sigmoid head',
                  preprocessing='grayscale CLAHE clip2 tile8x8 -> Gaussian3x3 -> stretch256 AREA -> float32 /255',
                  inverse='threshold model grid then native nearest-neighbor resize, same as original serving',
                  source_hashes={s:sha(ROOT/s) for s in sources}, python=sys.version, torch=torch.__version__,
                  device='cpu', threads=4, platform=platform.platform(), seed=42)
    save(out/'config.json', config); save(out/'split_audit.json', leakage)
    model = m.AttentionUNet().cpu(); m._load_model_weights(model, str(checkpoint)); model.eval()
    parameter_count = sum(p.numel() for p in model.parameters())
    rows = [r for r in manifest['rows'] if r['split']=='val']
    training_sizes = [r['mask_pixels']/(r['width']*r['height']) for r in manifest['rows'] if r['split']=='train' and int(r['fractured'])]
    small_cutoff = float(np.quantile(training_sizes, .25))
    cases, latencies, pipeline_latencies, probabilities = [], [], [], {}
    started = time.perf_counter()
    with zipfile.ZipFile(archive) as z, torch.inference_mode():
        annotations = {a['id']:a for a in json.loads(z.read('FracAtlas/Annotations/COCO JSON/COCO_fracture_masks.json'))['annotations']}
        for index, row in enumerate(rows):
            t0 = time.perf_counter()
            image = m._decode_image_bytes(z.read(row['member']))
            h, w = image.shape
            if (h, w) != (row['height'], row['width']):
                raise ValueError('Native dimensions differ from manifest')
            instances = [m._rasterize_coco_segmentation(annotations[aid]['segmentation'], w, h) for aid in row['annotation_ids']]
            gt = np.zeros((h, w), np.uint8)
            for instance in instances:
                gt |= instance
            positive = bool(int(row['fractured']))
            if positive != bool(gt.any()):
                raise ValueError('Case label and native mask presence disagree')
            x = m._ensure_4d_tensor(m.preprocess_image_array(image))
            start = time.perf_counter(); prob = model(x)[0,0].numpy(); latencies.append((time.perf_counter()-start)*1000)
            if prob.shape != (256,256) or not np.isfinite(prob).all():
                raise RuntimeError('Invalid model output')
            grid, _, _ = m.assess_severity((prob >= threshold).astype(np.uint8), threshold)
            native = cv2.resize(grid, (w,h), interpolation=cv2.INTER_NEAREST)
            pipeline_latencies.append((time.perf_counter()-t0)*1000)
            target, pred = gt.astype(bool), native.astype(bool)
            tp, fp, fn = [int(a.sum()) for a in (pred & target, pred & ~target, ~pred & target)]
            presence = bool(pred.any())
            label = ('TP' if presence else 'FN') if positive else ('FP' if presence else 'TN')
            recall, precision = metrics.ratio(tp, tp+fn), metrics.ratio(tp, tp+fp)
            errors = []
            if positive:
                if not presence: errors.append('complete_empty_miss')
                elif tp == 0: errors.append('complete_mislocalization')
                else:
                    if recall < .5: errors.append('under_segmentation_recall_below_0.5')
                    if precision < .5: errors.append('over_segmentation_precision_below_0.5')
            n, labels, stats, _ = cv2.connectedComponentsWithStats(native, 8)
            # Map unthresholded scores with identical nearest interpolation.
            native_prob = cv2.resize(prob, (w,h), interpolation=cv2.INTER_NEAREST)
            regions = []
            for k in range(1, n):
                left, top, width, height, area = stats[k].tolist()
                regions.append(dict(box=[left,top,left+width,top+height], pixels=area, score=float(native_prob[labels==k].max())))
            iou = np.zeros((len(instances), n-1))
            predicted_sizes = stats[1:,cv2.CC_STAT_AREA]
            for k, instance in enumerate(instances):
                intersections = np.bincount(labels[instance.astype(bool)], minlength=n)[1:]
                iou[k] = intersections/np.maximum(predicted_sizes+int(instance.sum())-intersections, 1)
            c = dict(image_id=row['image_id'], group=row['group'], positive=positive, prediction_present=presence,
                     category=label, case_score=float(prob.max()), tp_pixels=tp, fp_pixels=fp, fn_pixels=fn,
                     dice=metrics.ratio(2*tp, 2*tp+fp+fn) if positive else None,
                     iou=metrics.ratio(tp, tp+fp+fn) if positive else None,
                     segmentation_precision=precision, segmentation_recall=recall,
                     native_shape=[h,w], gt_instances=len(instances), predicted_components=n-1,
                     gt_fraction=float(gt.mean()), predicted_fraction=float(native.mean()),
                     small_region_proxy=positive and float(gt.mean()) <= small_cutoff,
                     quality_std=float(image.std()), quality_contrast_p99_p01=float(np.quantile(image,.99)-np.quantile(image,.01)),
                     segmentation_failure_tags=errors, gt_boxes=[box(v) for v in instances], regions=regions,
                     mask_region_matches_iou10=metrics.matched_regions(iou, .1), mask_region_matches_iou50=metrics.matched_regions(iou, .5),
                     flags={k:int(row[k]) for k in ('hand','leg','hip','shoulder','mixed','hardware','multiscan','frontal','lateral','oblique')},
                     fracture_count=int(row['fracture_count']), source_member=row['member'])
            stem = Path(row['image_id']).stem
            if not cv2.imwrite(str(out/'masks'/f'{stem}_prediction.png'), native*255):
                raise RuntimeError('Native prediction save failed')
            cv2.imwrite(str(out/'masks'/f'{stem}_reference.png'), gt*255)
            if label in ('FP','FN') or errors:
                filename = f'{label}_{stem}.jpg'
                panel(image, gt, native, out/'failures'/filename, f'{row["image_id"]} {label} score={c["case_score"]:.6f} Dice={c["dice"]} threshold={threshold}')
                c['review_panel'] = 'failures/'+filename
            probabilities[row['image_id']] = prob.copy()  # Exact float32, not quantized.
            cases.append(c)
            if (index+1)%25 == 0:
                state = dict(status='running_validation', images=index+1, total=len(rows), median_forward_ms=float(np.median(latencies)), test_images_read=0)
                (out/'progress.json').write_text(json.dumps(state, indent=2))
                print(json.dumps(state), flush=True)
    save(out/'per_case.json', cases)
    np.savez_compressed(out/'probabilities_float32.npz', **probabilities)
    groups = {}
    for flag in cases[0]['flags']:
        subset = [c for c in cases if c['flags'][flag]]
        groups[flag] = dict(classification=metrics.classification(subset), segmentation=metrics.segmentation(subset)) if subset else None
    for name, subset in [('small_region_proxy', [c for c in cases if c['small_region_proxy']]),
                         ('multiple_fractures', [c for c in cases if c['fracture_count']>1])]:
        groups[name] = dict(classification=metrics.classification(subset), segmentation=metrics.segmentation(subset)) if subset else None
    region_counts = {str(t):dict(matches=sum(c[key] for c in cases), gt=sum(c['gt_instances'] for c in cases), predicted=sum(c['predicted_components'] for c in cases)) for t,key in ((.1,'mask_region_matches_iou10'),(.5,'mask_region_matches_iou50'))}
    for v in region_counts.values():
        v.update(precision=metrics.ratio(v['matches'],v['predicted']), recall=metrics.ratio(v['matches'],v['gt']), false_positive_regions=v['predicted']-v['matches'], missed_regions=v['gt']-v['matches'])
    result = dict(config=config, classification=metrics.classification(cases), segmentation=metrics.segmentation(cases),
                  calibration=metrics.calibration(cases), localization=metrics.localization(cases), mask_instance_localization=region_counts,
                  subgroups=groups, small_region_definition=dict(cutoff_fraction=small_cutoff, source='25th percentile of positive training union-mask occupancy; SIZE proxy, not clinical subtle/nondisplaced labels'),
                  timing=dict(forward_median_ms=float(np.median(latencies[1:])), forward_p95_ms=float(np.quantile(latencies[1:],.95)),
                              decode_preprocess_forward_native_median_ms=float(np.median(pipeline_latencies[1:])), elapsed_seconds=time.perf_counter()-started,
                              peak_rss_bytes=getattr(psutil.Process().memory_info(), 'peak_wset', psutil.Process().memory_info().rss)),
                  architecture_parameter_count=parameter_count, test_images_read=0,
                  unavailable=['clinical subtle/nondisplaced fracture labels','patient/study IDs and paired-view fusion','external independent data','radiologist reader/correction measurements','clinical calibration'])
    save(out/'metrics.json', result)
    write_csv(out/'failure_review.csv', [dict(image_id=c['image_id'], category=c['category'], panel=c.get('review_panel',''), case_score=c['case_score'], dice=c['dice'], iou=c['iou'],
        segmentation_precision=c['segmentation_precision'], segmentation_recall=c['segmentation_recall'], gt_fraction=c['gt_fraction'], predicted_fraction=c['predicted_fraction'],
        anatomy_flags=';'.join(k for k in ('hand','leg','hip','shoulder','mixed') if c['flags'][k]), view_flags=';'.join(k for k in ('frontal','lateral','oblique') if c['flags'][k]),
        hardware=c['flags']['hardware'], quality_std=c['quality_std'], failure_tags=';'.join(c['segmentation_failure_tags']), technical_review='pending', clinical_cause='unadjudicated') for c in cases if c.get('review_panel')])
    figures(out, cases, result)
    cl, seg, cal = result['classification'], result['segmentation'], result['calibration']
    lines = ['# BASELINE_MODEL_REPORT', '', 'Measured 7 October 2026. Original checkpoint unchanged. Full v2 validation: 612 images. Immutable diagnostic baseline, NOT independent test or clinical validation.', '',
             '## Measured classification', '', '| Metric | Result |', '|---|---:|']
    for k in ('accuracy','precision','recall_sensitivity','specificity','f1','auroc','auprc_average_precision','false_positive_rate','false_negative_rate'):
        lines.append(f'| {k} | {cl[k]:.6f} |')
    lines += ['', f'Confusion matrix (reference rows, prediction columns): TN={cl["confusion_matrix"]["tn"]}, FP={cl["confusion_matrix"]["fp"]}, FN={cl["confusion_matrix"]["fn"]}, TP={cl["confusion_matrix"]["tp"]}.', '',
              '## Segmentation and localization', '', '| Metric | Result |', '|---|---:|']
    for k in ('mean_positive_dice','mean_positive_iou','global_pixel_precision','global_pixel_recall','global_dice','global_iou'):
        lines.append(f'| {k} | {seg[k]:.6f} |')
    loc = result['localization']
    lines += [f'| Component-box mAP@0.50 proxy | {loc["component_box_map50"]:.6f} |', f'| Component-box mAP@0.50:0.95 proxy | {loc["component_box_map50_95"]:.6f} |', '', loc['method'], '',
              f'Native mask one-to-one region precision/recall: {json.dumps(region_counts)}.', '', '## Calibration and timing', '',
              f'Uncalibrated max-pixel proxy Brier={cal["brier_score"]:.6f}; equal-width 10-bin ECE={cal["expected_calibration_error"]:.6f}. {cal["score_exactly_one_count"]} images have max sigmoid output exactly 1. These diagnostics do not turn pixel scores into calibrated clinical probabilities.', '',
              f'CPU forward median={result["timing"]["forward_median_ms"]:.1f} ms; p95={result["timing"]["forward_p95_ms"]:.1f} ms. Decode/preprocess/forward/native-mask median={result["timing"]["decode_preprocess_forward_native_median_ms"]:.1f} ms.', '',
              '## Scope and integrity', '', 'No training, checkpoint/threshold change or test inference. Patient IDs are unavailable: grouped duplicates are disjoint, but patient independence is unverified. Historical model training exposure is unknown, so this baseline is diagnostic. FracAtlas is already the current dataset, not newly added external evidence. View flags are nonexclusive; frontal is not proven AP. Clinical subtle/nondisplaced and radiologist-agreement results are unavailable.', '',
              'All native reference/predicted masks are in masks/. Every false positive, false negative and algorithmically tagged positive segmentation failure has a original/reference/prediction panel and a failure_review.csv row. Causes require individual technical/expert review; tags are numerical descriptions, not clinical diagnoses.', '',
              'Full metrics/subgroups: metrics.json. Confusion/ROC/PR: confusion_roc_pr.png and curves.json. Calibration: reliability_curve.png. Exact probability cache: probabilities_float32.npz. Split audit: split_audit.json. Source/config hashes: config.json.', '',
              f'Checkpoint SHA-256: `{checkpoint_hash}`', f'Manifest SHA-256: `{config["manifest_sha256"]}`', '', 'No candidate accepted and no >90% claim. This is the reference for subsequent evidence-based experiments.']
    with (out/'BASELINE_MODEL_REPORT.md').open('x', encoding='utf-8') as f:
        f.write('\n'.join(lines)+'\n')
    if sha(checkpoint) != checkpoint_hash or sha(manifest_path) != config['manifest_sha256']:
        raise RuntimeError('Protected baseline inputs changed during evaluation')
    save(out/'completion.json', dict(status='completed', baseline_immutable=True, test_images_read=0,
        report_sha256=sha(out/'BASELINE_MODEL_REPORT.md'), metrics_sha256=sha(out/'metrics.json'), cases_sha256=sha(out/'per_case.json')))
    print(json.dumps(dict(status='completed', classification=cl, segmentation=seg, calibration_brier=cal['brier_score'], calibration_ece=cal['expected_calibration_error']), indent=2), flush=True)


if __name__ == '__main__':
    main()
