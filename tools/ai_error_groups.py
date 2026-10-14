"""Measured validation error associations and FP edge/border diagnostics.

No diagnosis or causal attribution is inferred from these technical groups.
Reads only the fixed463 validation IDs, never test/calibration image bytes.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import zipfile

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import medvision_ai as m
from tools.evaluate_ai_baseline import save, sha, write_csv
from tools import ai_metrics as a


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    audit, out = Path(args.audit).resolve(), Path(args.out).resolve()
    if ROOT not in out.parents or out.exists() or not (audit/'completion.json').exists():
        raise ValueError('Completed audit and new workspace output required')
    manifest = json.loads((ROOT/'experiments/data_v3_reliability_20261007/manifest.json').read_text())
    if sha(ROOT/'experiments/data_v3_reliability_20261007/manifest.json') != '4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318':
        raise ValueError('Validation distribution changed')
    ids = {r['image_id'] for r in manifest['rows'] if r['split'] == 'val'}
    cases = [c for c in json.loads((audit/'per_case.json').read_text()) if c['image_id'] in ids]
    if len(cases) != 463 or {c['image_id'] for c in cases} != ids:
        raise ValueError('Require all463 validation cases, no exclusions')
    out.mkdir()
    cv2.setNumThreads(1)
    flags = {}
    for flag in cases[0]['flags']:
        subset = [c for c in cases if c['flags'][flag]]
        flags[flag] = dict(n=len(subset), classification=a.classification(subset), segmentation=a.segmentation(subset)) if subset else None
    false_positives = [c for c in cases if not c['positive'] and c['prediction_present']]
    diagnostics = []
    with zipfile.ZipFile(ROOT/'FracAtlas.zip') as archive:
        for index, c in enumerate(false_positives):
            image = m._decode_image_bytes(archive.read(c['source_member']))
            stem = Path(c['image_id']).stem
            mask = cv2.imread(str(audit/'masks'/f'{stem}_prediction.png'), cv2.IMREAD_GRAYSCALE)
            if mask is None or mask.shape != image.shape:
                raise ValueError('Native prediction missing or mismatched')
            mask = mask > 0
            if int(mask.sum()) != c['fp_pixels']:
                raise ValueError('Normal false-positive area does not reproduce saved counts')
            h, w = image.shape
            band = max(1, round(.02*min(h, w)))
            border = np.ones((h, w), bool)
            border[band:h-band, band:w-band] = False
            border_fraction = float(border[mask].mean())
            gray = image.astype(np.float32)/255
            gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
            gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
            gradient = np.hypot(gx, gy)
            cutoff = float(np.quantile(gradient, .90))
            edge = gradient >= cutoff
            fraction = float(edge[mask].mean()) if cutoff > 0 else None
            prevalence = float(edge.mean()) if cutoff > 0 else None
            enriched = fraction/prevalence if prevalence else None
            tags = []
            if border_fraction > .5:
                tags.append('border_dominant_predicted_area')
            if enriched is not None and enriched > 2:
                tags.append('gradient_edge_enrichment_over2')
            if c['flags']['hardware']:
                tags.append('source_hardware_flag')
            if c['flags']['multiscan']:
                tags.append('source_multiscan_flag')
            if not tags:
                tags.append('other_FP_unadjudicated')
            diagnostics.append(dict(image_id=c['image_id'], predicted_pixels=c['fp_pixels'],
                predicted_fraction=c['predicted_fraction'], native_shape=c['native_shape'],
                border_band_pixels=band, border_predicted_area_fraction=border_fraction,
                edge_gradient90_fraction=fraction, edge_enrichment=enriched,
                technical_tags=tags, source_flags=c['flags'],
                score=c['case_score'], review_panel=str(audit/c['review_panel']),
                clinical_cause='unadjudicated; edge alignment does not identify cortex vs artifact'))
            if (index+1) % 25 == 0:
                print(json.dumps(dict(reviewed_FP_masks=index+1, total=len(false_positives), test_images_read=0)), flush=True)
    groups = Counter(tag for d in diagnostics for tag in d['technical_tags'])
    representatives = {}
    # Deterministic high-area examples for each measured group, not diagnoses.
    for tag in groups:
        subset = sorted([d for d in diagnostics if tag in d['technical_tags']], key=lambda d: -d['predicted_fraction'])
        representatives[tag] = [d['image_id'] for d in subset[:3]]
    failures = [c for c in cases if c['positive'] and (not c['prediction_present'] or c['tp_pixels']==0 or c['dice'] < .2)]
    quality = {}
    # Descriptive strata; no selection/training/exclusion of these images.
    qcut = float(np.quantile([c['quality_contrast_p99_p01'] for c in cases], .25))
    for name, subset in [('lowest_validation_contrast_quartile', [c for c in cases if c['quality_contrast_p99_p01'] <= qcut]),
                         ('other_validation_contrast', [c for c in cases if c['quality_contrast_p99_p01'] > qcut]),
                         ('small_target_proxy', [c for c in cases if c['small_region_proxy']]),
                         ('multiple_annotations', [c for c in cases if c['fracture_count'] > 1])]:
        quality[name] = dict(n=len(subset), classification=a.classification(subset), segmentation=a.segmentation(subset)) if subset else None
    result = dict(scope='Fixed463 validation technical associations; no model/policy change',
        audit=str(audit.relative_to(ROOT)), source_metrics_sha256=sha(audit/'metrics.json'),
        FP_cases=len(false_positives), technical_groups=dict(groups), representative_ids=representatives,
        anatomy_view_hardware_strata=flags, quality_and_difficult_proxies=quality,
        quality_threshold=dict(contrast_p99_p01_cutoff=qcut, source='Validation25th percentile, descriptive only'),
        positive_failures=[{key:c[key] for key in ('image_id', 'category', 'dice', 'iou', 'tp_pixels', 'fp_pixels', 'fn_pixels',
                            'gt_fraction', 'segmentation_failure_tags', 'flags', 'review_panel')} for c in failures],
        clinical_cause='Pending expert annotation/cause review; technical tags are not causal evidence',
        unavailable=['casts ground-truth flag', 'clinical subtle/nondisplaced labels', 'paired study IDs'],
        patient_independence=False, test_images_read=0)
    save(out/'error_groups.json', result)
    save(out/'FP_pixel_diagnostics.json', diagnostics)
    write_csv(out/'FP_pixel_diagnostics.csv', [{key:value for key,value in d.items() if key not in ('source_flags','technical_tags','native_shape')} |
        {'tags':';'.join(d['technical_tags'])} for d in diagnostics])
    text = ['# Validation false-positive groups', '',
            'Measured pixel placement and source metadata, not clinical causes. All463 validation cases remain unchanged.', '',
            f'{len(false_positives)} normal cases falsely flagged.', '',
            '## Nonexclusive technical groups', '', '| Group | Cases | Representative IDs |', '|---|---:|---|']
    text += [f"| {tag} | {n} | {', '.join(representatives[tag])} |" for tag,n in groups.items()]
    text += ['', 'Border band:2% of shortest native image dimension; dominant means >50% of predicted pixels. Edge enrichment compares predicted area overlap with the highest10% Sobel-gradient pixels to their image prevalence; tag threshold2x. This cannot distinguish normal cortex, overlapping bone, casts, metal or acquisition artifacts without individual expert review.', '',
             'Hardware/multiscan/view/anatomy fields are provider metadata. Their association with false-positive rate is not causation. Casts, subtle/nondisplaced clinical labels and paired study identities are unavailable.', '',
             'Every flagged normal mask count reproduces saved native false-positive pixels. FP_pixel_diagnostics.json links actual review panels. error_groups.json contains all view/anatomy/quality strata and positive failures. No validation case was removed and no test image was decoded.']
    with (out/'ERROR_GROUPS.md').open('x',encoding='utf-8') as handle:
        handle.write('\n'.join(text)+'\n')
    save(out/'completion.json', dict(status='completed', test_images_read=0, source_sha256=sha(__file__)))
    print(json.dumps(dict(FP_cases=len(false_positives), technical_groups=dict(groups)), indent=2))


if __name__ == '__main__':
    main()
