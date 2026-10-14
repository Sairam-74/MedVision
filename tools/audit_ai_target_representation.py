"""Train/validation mask discretization and TRAIN-only loss-gradient diagnostic.

No image inference, training, threshold tuning, calibration or test annotations.
No original source, mask, manifest or checkpoint is modified.
"""
import argparse
import json
from pathlib import Path
import sys
import zipfile

import cv2
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import medvision_pipeline as p
from tools.evaluate_ai_baseline import save, write_csv

MANIFEST = ROOT/'experiments/data_v3_reliability_20261007/manifest.json'
MANIFEST_SHA = '4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318'


def overlap(predicted, target):
    predicted, target = predicted.astype(bool), target.astype(bool)
    tp = int(np.count_nonzero(predicted & target))
    fp = int(np.count_nonzero(predicted & ~target))
    fn = int(np.count_nonzero(~predicted & target))
    return dict(tp=tp, fp=fp, fn=fn, dice=2*tp/(2*tp+fp+fn), iou=tp/(tp+fp+fn))


def gradient_probe(foreground_count, probability):
    # Separate uniform foreground/background logits, not one shared scalar.
    target = torch.zeros((1, 1, 256, 256))
    target.reshape(-1)[:foreground_count] = 1
    initial = float(np.log(probability/(1-probability)))
    foreground = torch.tensor(initial, requires_grad=True)
    background = torch.tensor(initial, requires_grad=True)
    logits = torch.where(target > 0, foreground, background)
    components = p.loss_components(logits, target, torch.ones_like(target), p.LossConfig(mode='bce_dice'))
    result = {}
    for name in ('bce', 'dice', 'total'):
        fg, bg = torch.autograd.grad(components[name], (foreground, background), retain_graph=True)
        result[name] = dict(loss=float(components[name].detach()),
                           sum_foreground_logit_gradient=float(fg), sum_background_logit_gradient=float(bg))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if ROOT not in out.parents or out.exists() or p.sha(MANIFEST) != MANIFEST_SHA:
        raise ValueError('New workspace output and unchanged frozen manifest required')
    manifest = json.loads(MANIFEST.read_text())
    # Test/calibration rows are excluded before ANY annotation is rasterized.
    rows = [r for r in manifest['rows'] if r['split'] in ('train', 'val')]
    with zipfile.ZipFile(ROOT/'FracAtlas.zip') as archive:
        document = json.loads(archive.read('FracAtlas/Annotations/COCO JSON/COCO_fracture_masks.json'))
    allowed_aids = {aid for r in rows for aid in r['annotation_ids']}
    annotations = {a['id']: a for a in document['annotations'] if a['id'] in allowed_aids}
    del document
    out.mkdir()
    cv2.setNumThreads(1)
    torch.set_num_threads(1)
    results = []
    train_indices = {r['image_id']: i for i, r in enumerate(r for r in manifest['rows'] if r['split']=='train')}
    for row in rows:
        if not int(row['fractured']):
            continue
        h, w = row['height'], row['width']
        target = np.zeros((h, w), np.uint8)
        instance_counts = {256: [], 512: []}
        for aid in row['annotation_ids']:
            instance = p.legacy._rasterize_coco_segmentation(annotations[aid]['segmentation'], w, h)
            target |= instance
            for size in instance_counts:
                instance_counts[size].append(int(cv2.resize(instance, (size, size), interpolation=cv2.INTER_NEAREST).sum()))
        item = dict(image_id=row['image_id'], split=row['split'], native_pixels=int(target.sum()),
                    native_area_fraction=float(target.mean()), instances=len(row['annotation_ids']), resolutions={})
        if not target.any():
            raise ValueError('Positive source target vanished')
        for size in (256, 512):
            config = p.PreprocessConfig(size=size, resize='stretch')
            geometry = p.geometry((h, w), config)
            projected = p.project(target.astype(np.float32), geometry, cv2.INTER_NEAREST)
            # Label projection followed by the actual bilinear inverse/threshold
            # is a representation diagnostic, NOT a model result or hard ceiling.
            reconstructed = p.inverse(projected, geometry, probability=True) >= .5
            data = dict(projected_pixels=int(projected.sum()), projected_fraction=float(projected.mean()),
                        lost_instances=sum(v==0 for v in instance_counts[size]), instance_projected_pixels=instance_counts[size],
                        label_roundtrip=overlap(reconstructed, target))
            if row['split']=='train':
                augmentation = []
                for epoch in range(1, 13):
                    seed = np.random.SeedSequence([42, epoch, train_indices[row['image_id']]]).generate_state(1)[0]
                    _, augmented, _ = p.augment(np.zeros_like(projected), projected, np.ones_like(projected), int(seed), False)
                    count = int(augmented.sum())
                    augmentation.append(dict(epoch=epoch, pixels=count, empty=count==0,
                                             retained_fraction=count/max(int(projected.sum()), 1),
                                             registered_guard_fallback=count==0))
                data['augmentation_label_geometry_only'] = augmentation
            item['resolutions'][str(size)] = data
        results.append(item)
        if len(results) % 50 == 0:
            print(json.dumps(dict(positive_masks_reviewed=len(results), image_bytes_read=0, test_masks_rasterized=0)), flush=True)
    summary = {}
    for split in ('train', 'val'):
        subset = [r for r in results if r['split']==split]
        summary[split] = {}
        for size in ('256', '512'):
            counts = [r['resolutions'][size]['projected_pixels'] for r in subset]
            data = dict(positive_images=len(subset), positive_pixel_quantiles={str(q):float(np.quantile(counts, q)) for q in (0, .1, .5, .9, 1)},
                        empty_positive_images=sum(v==0 for v in counts), lost_annotation_instances=sum(r['resolutions'][size]['lost_instances'] for r in subset),
                        mean_label_roundtrip_dice=float(np.mean([r['resolutions'][size]['label_roundtrip']['dice'] for r in subset])),
                        mean_label_roundtrip_iou=float(np.mean([r['resolutions'][size]['label_roundtrip']['iou'] for r in subset])))
            if split=='train':
                augmented = [a for r in subset for a in r['resolutions'][size]['augmentation_label_geometry_only']]
                data['augmentation'] = dict(exposures=len(augmented), would_erase_target=sum(a['empty'] for a in augmented),
                                            retained_fraction_below_half=sum(a['retained_fraction']<.5 for a in augmented),
                                            note='Registered fallback preserves fully erased targets; partial clipping remains. Only label geometry simulated, no image quality or model training result.')
                train_n = sum(r['split']=='train' for r in rows)
                data['train_foreground_pixel_fraction_natural_images'] = sum(counts)/(train_n*int(size)**2)
            summary[split][size] = data
    ordered = sorted([r for r in results if r['split']=='train'], key=lambda r:r['resolutions']['256']['projected_pixels'])
    probes = []
    for index in sorted({0, len(ordered)//2, len(ordered)-1}):
        row = ordered[index]
        n = row['resolutions']['256']['projected_pixels']
        probes.append(dict(train_image_id=row['image_id'], foreground_pixels=n,
                           probabilities={str(prob):gradient_probe(n, prob) for prob in (.1, .01, .001)}))
    probes.append(dict(train_image_id='synthetic_empty_mask', foreground_pixels=0,
                       probabilities={str(prob):gradient_probe(0, prob) for prob in (.1, .01, .001)}))
    save(out/'per_positive_mask.json', results)
    save(out/'summary.json', summary)
    save(out/'train_loss_gradient_probes.json', probes)
    write_csv(out/'per_positive_mask.csv', [dict(image_id=r['image_id'], split=r['split'], native_pixels=r['native_pixels'],
        native_area_fraction=r['native_area_fraction'], pixels256=r['resolutions']['256']['projected_pixels'],
        pixels512=r['resolutions']['512']['projected_pixels'], roundtrip_dice256=r['resolutions']['256']['label_roundtrip']['dice'],
        roundtrip_dice512=r['resolutions']['512']['label_roundtrip']['dice']) for r in results])
    save(out/'completion.json', dict(status='completed_diagnostic_only', manifest_sha256=p.sha(MANIFEST), source_sha256=p.sha(__file__),
        image_bytes_read=0, train_positive_masks=sum(r['split']=='train' for r in results), validation_positive_masks=sum(r['split']=='val' for r in results),
        calibration_masks_rasterized=0, test_masks_rasterized=0, model_inference=False, model_trained=False,
        caveat='Label roundtrip is a resolution representation diagnostic, neither a measured model score nor a mathematical upper bound. Gradient probes use synthetic uniform logits and actual TRAIN foreground counts, not learned gradients.'))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
