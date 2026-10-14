"""Produce read-only Phase 3 metadata and visual audit evidence; never run a model."""
import csv
import hashlib
import json
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from medvision_ai import _rasterize_coco_segmentation


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    out = ROOT / 'experiments/phase3_review'
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / 'experiments/data_v1/manifest.json'
    original_hash = sha(manifest_path)
    m = json.loads(manifest_path.read_text())
    a = json.loads((manifest_path.parent / 'audit.json').read_text())
    rows = m['rows']
    lookup = {r['image_id']: r for r in rows}
    flags = ['fractured', 'hand', 'leg', 'hip', 'shoulder', 'mixed', 'hardware',
             'multiscan', 'frontal', 'lateral', 'oblique']
    for r in rows:
        assert all(r[f] in ('0', '1') for f in flags)
        assert int(r['fracture_count']) == len(r['annotation_ids'])
    groups = defaultdict(set)
    for r in rows:
        groups[r['group']].add(r['split'])
    assert all(len(s) == 1 for s in groups.values())
    assert all(lookup[p['a']]['group'] == lookup[p['b']]['group'] for p in a['near_duplicate_candidates'])
    assert all(len({lookup[i]['split'] for i in g}) == 1 for g in a['exact_duplicate_groups'])
    summary = {}
    table = []
    for split in ('train', 'val', 'test'):
        rr = [r for r in rows if r['split'] == split]
        pp = [r for r in rr if int(r['fractured'])]
        summary[split] = {'images': len(rr), 'groups': len({r['group'] for r in rr}),
                          'fracture_prevalence': len(pp)/len(rr),
                          'annotation_instances': sum(len(r['annotation_ids']) for r in rr),
                          'multiple_fracture_images': sum(int(r['fracture_count']) > 1 for r in rr)}
        for field in flags:
            count = sum(int(r[field]) for r in rr)
            positive = sum(int(r[field]) for r in pp)
            table.append({'split': split, 'field': field, 'flagged_images': count,
                          'percentage_of_split': 100*count/len(rr), 'fractured_flagged_images': positive})
        for field, values in [('width', [r['width'] for r in rr]),
                              ('height', [r['height'] for r in rr]),
                              ('aspect_width_over_height', [r['width']/r['height'] for r in rr]),
                              ('positive_native_mask_fraction', [r['mask_pixels']/(r['width']*r['height']) for r in pp]),
                              ('positive_mask_pixels_256', [r['mask_pixels_256'] for r in pp])]:
            summary[split][field] = dict(zip(['min', 'p25', 'median', 'p75', 'max'],
                                              np.percentile(values, [0, 25, 50, 75, 100]).tolist()))
    with (out / 'subgroups.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(table[0]))
        writer.writeheader()
        writer.writerows(table)
    summary['checks'] = {'manifest_sha256': original_hash, 'cross_split_group_overlap': 0,
                         'cross_split_known_duplicate_pairs': 0, 'patient_independence_verified': False,
                         'test_predictions_or_performance_inspection': False,
                         'metadata_flags_are_nonexclusive': True,
                         'source_csv_fields': list(rows[0])[:13]}
    (out / 'distributions.json').write_text(json.dumps(summary, indent=2))
    selected = []
    eligible = [r for r in rows if r['split'] != 'test']
    def select(reason, candidates):
        if candidates:
            r = candidates[0]
            selected.append({'image_id': r['image_id'], 'reason': reason, 'split': r['split']})
    for field in flags[1:]:
        for positive in (1, 0):
            select(f'{field}=1, fractured={positive}',
                   [r for r in eligible if int(r[field]) and int(r['fractured']) == positive])
    select('multiple fracture annotations', sorted(eligible, key=lambda r: -int(r['fracture_count'])))
    positives = [r for r in eligible if int(r['fractured'])]
    select('smallest positive native occupancy', sorted(positives, key=lambda r: r['mask_pixels']/(r['width']*r['height'])))
    select('smallest positive 256 mask', sorted(positives, key=lambda r: r['mask_pixels_256']))
    select('widest aspect ratio', sorted(eligible, key=lambda r: -r['width']/r['height']))
    select('tallest aspect ratio', sorted(eligible, key=lambda r: r['width']/r['height']))
    unique = {}
    for entry in selected:
        unique.setdefault(entry['image_id'], {'image_id':entry['image_id'], 'split':entry['split'], 'reasons':[]})['reasons'].append(entry['reason'])
    selected = list(unique.values())
    (out / 'annotation_review_selection.json').write_text(json.dumps(selected, indent=2))
    near = [p for p in a['near_duplicate_candidates'] if lookup[p['a']]['decoded_sha256'] != lookup[p['b']]['decoded_sha256']]
    (out / 'nonexact_pairs.json').write_text(json.dumps(near, indent=2))
    exact = defaultdict(list)
    for r in rows:
        exact[r['decoded_sha256']].append(r)
    conflicts = [[r['image_id'] for r in group] for group in exact.values()
                 if len({r['fractured'] for r in group}) > 1]
    conflict_ids = {i for group in conflicts for i in group}
    cv2.setNumThreads(1)
    with zipfile.ZipFile(ROOT / 'FracAtlas.zip') as z:
        coco = json.loads(z.read('FracAtlas/Annotations/COCO JSON/COCO_fracture_masks.json'))
        anns = {ann['id']:ann for ann in coco['annotations']}
        annotation_variants = []
        for group in exact.values():
            if len(group) < 2:
                continue
            hashes = []
            for r in group:
                mask = np.zeros((r['height'], r['width']), np.uint8)
                for aid in r['annotation_ids']:
                    mask |= _rasterize_coco_segmentation(anns[aid]['segmentation'], r['width'], r['height'])
                hashes.append(hashlib.sha256(mask.tobytes()).hexdigest())
            if len(set(hashes)) > 1:
                annotation_variants.append({'image_ids':[r['image_id'] for r in group],
                                            'union_mask_sha256':hashes,
                                            'case_label_conflict':bool(conflict_ids.intersection(r['image_id'] for r in group))})
        (out / 'duplicate_label_audit.json').write_text(json.dumps({
            'contradictory_case_label_groups':conflicts,
            'contradictory_case_label_images':len(conflict_ids),
            'exact_duplicate_union_mask_variants':annotation_variants,
            'action':'Quarantine every image with a contradictory exact-decoded case label in data_v2; retain other provider annotation variants and disclose them. No label guessing.',
        }, indent=2))
        def load(r):
            return cv2.imdecode(np.frombuffer(z.read(r['member']), np.uint8), cv2.IMREAD_GRAYSCALE)
        def thumb(im, size):
            im = Image.fromarray(im)
            im.thumbnail(size)
            canvas = Image.new('RGB', size, 'black')
            canvas.paste(im, ((size[0]-im.width)//2, (size[1]-im.height)//2))
            return canvas
        for start in range(0, len(near), 24):
            sheet = Image.new('RGB', (1440, 1920), 'white')
            draw = ImageDraw.Draw(sheet)
            for k, pair in enumerate(near[start:start+24]):
                x, y = (k%3)*480, (k//3)*240
                for j, key in enumerate(('a', 'b')):
                    r = lookup[pair[key]]
                    sheet.paste(thumb(load(r), (236, 195)), (x+j*240, y+40))
                    draw.text((x+j*240+3, y+18), f"{r['image_id']} {r['split']}", fill='black')
                draw.text((x+3,y+3), f"Pair {start+k+1}: dHash {pair['dhash_distance']}, MAE {pair['thumbnail_mae']:.2f}", fill='black')
            sheet.save(out / f'duplicates_{start//24+1:02d}.png')
        for start in range(0, len(selected), 8):
            sheet = Image.new('RGB', (1600, 1600), 'white')
            draw = ImageDraw.Draw(sheet)
            for k, entry in enumerate(selected[start:start+8]):
                r = lookup[entry['image_id']]
                im = load(r)
                mask = np.zeros(im.shape, np.uint8)
                for aid in r['annotation_ids']:
                    mask |= _rasterize_coco_segmentation(anns[aid]['segmentation'], r['width'], r['height'])
                overlay = cv2.cvtColor(im, cv2.COLOR_GRAY2RGB)
                overlay[mask.astype(bool)] = (0.5*overlay[mask.astype(bool)] + np.array([127,0,0])).astype(np.uint8)
                x, y = (k%2)*800, (k//2)*400
                sheet.paste(thumb(overlay, (390, 330)), (x,y+60))
                if mask.any():
                    yy, xx = np.where(mask)
                    pad = max(20, int(max(xx.max()-xx.min(), yy.max()-yy.min())*.3))
                    crop = overlay[max(0,yy.min()-pad):min(r['height'],yy.max()+pad+1),
                                   max(0,xx.min()-pad):min(r['width'],xx.max()+pad+1)]
                else:
                    crop = im
                sheet.paste(thumb(crop, (390,330)), (x+400,y+60))
                draw.text((x+4,y+4), f"{r['image_id']} {r['split']} {r['width']}x{r['height']} instances={len(r['annotation_ids'])}", fill='black')
                draw.text((x+4,y+20), ', '.join(f for f in flags[1:] if int(r[f])), fill='black')
                draw.text((x+4,y+36), 'Native annotation union (red); right: annotation bounding crop / normal image', fill='black')
            sheet.save(out / f'annotations_{start//8+1:02d}.png')
    assert sha(manifest_path) == original_hash
    revision_dir = ROOT / 'experiments/data_v2'
    if revision_dir.exists():
        raise RuntimeError('data_v2 already exists; never overwrite a frozen revision')
    revision_dir.mkdir()
    revision = dict(m)
    revision.update(protocol='grouped-all-images-v2-label-quarantine',
                    parent_manifest_sha256=original_hash,
                    revision_reason='Exact-decoded duplicate case-label contradictions; exclude all 7 affected images, retain remaining v1 split/group assignments.',
                    rows=[r for r in rows if r['image_id'] not in conflict_ids],
                    exclusions=m['exclusions'] + [dict(image_id=i, fractured=int(lookup[i]['fractured']),
                                                       reason='Contradictory fractured/normal labels within exact-decoded duplicate set; quarantined without relabeling')
                                                  for i in sorted(conflict_ids)])
    encoded = json.dumps(revision, indent=2).encode()
    (revision_dir / 'manifest.json').write_bytes(encoded)
    revision_hash = hashlib.sha256(encoded).hexdigest()
    (revision_dir / 'manifest.sha256').write_text(revision_hash+'\n')
    revision_counts = {}
    for split in ('train', 'val', 'test'):
        rr = [r for r in revision['rows'] if r['split'] == split]
        (revision_dir / f'{split}.txt').write_text('\n'.join(r['image_id'] for r in rr)+'\n')
        revision_counts[split] = dict(Counter('fractured' if int(r['fractured']) else 'normal' for r in rr))
        if split != 'train':
            assert (revision_dir / f'{split}.txt').read_bytes() == (manifest_path.parent / f'{split}.txt').read_bytes()
    (revision_dir / 'revision.json').write_text(json.dumps({
        'parent_manifest_sha256':original_hash, 'manifest_sha256':revision_hash,
        'quarantined_ids':sorted(conflict_ids), 'splits':revision_counts,
        'active_E2_run_uses':'data_v1; do not change its manifest or trainer during execution',
        'new_training_ready':False,
        'next_requirement':'Explicit manifest support in loader/trainer, followed by new-run smoke. Never resume E2 with changed data.',
        'annotation_disagreement_groups_retained':len(annotation_variants)-len(conflicts),
    }, indent=2))
    print(json.dumps({'selected_annotation_images':len(selected), 'nonexact_pairs':len(near), 'split_summary':summary}, indent=2))


if __name__ == '__main__':
    main()
