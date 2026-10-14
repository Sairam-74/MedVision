"""Read-only archive audit and reproducible grouped split; never edits source data."""
import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys
import zipfile

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from medvision_ai import _rasterize_coco_segmentation


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', default='FracAtlas.zip')
    parser.add_argument('--out', default='experiments/data_v1')
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'manifest.json').exists():
        raise SystemExit('Manifest exists; choose a new version directory instead of overwriting a frozen split.')
    rows, problems, exclusions, thumbs, perceptual = [], [], [], [], []
    with zipfile.ZipFile(args.archive) as z:
        bad = z.testzip()
        if bad:
            raise ValueError(f'Archive CRC failure: {bad}')
        labels = list(csv.DictReader(io.StringIO(z.read('FracAtlas/dataset.csv').decode())))
        coco = json.loads(z.read('FracAtlas/Annotations/COCO JSON/COCO_fracture_masks.json'))
        records = {r['file_name']: r for r in coco['images']}
        anns = defaultdict(list)
        for a in coco['annotations']:
            anns[a['image_id']].append(a)
        members = defaultdict(list)
        for n in z.namelist():
            if n.startswith('FracAtlas/images/') and n.lower().endswith(('.jpg', '.jpeg', '.png')):
                members[Path(n).name].append(n)
        if len({r['image_id'] for r in labels}) != len(labels):
            problems.append('duplicate CSV image IDs')
        for i, label in enumerate(labels):
            name = label['image_id']
            if len(members[name]) != 1:
                problems.append(f'{name}: unresolved or duplicate image member')
                continue
            data = z.read(members[name][0])
            im = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_GRAYSCALE)
            if im is None:
                exclusions.append({'image_id':name, 'fractured':int(label['fractured']), 'reason':'OpenCV decode failure; CRC-valid image bytes may be truncated'})
                continue
            h, w = im.shape
            rec = records.get(name)
            aa = anns[rec['id']] if rec else []
            mask = np.zeros((h, w), np.uint8)
            if rec and (rec['height'], rec['width']) != (h, w):
                problems.append(f'{name}: COCO dimension mismatch')
            for a in aa:
                seg = a.get('segmentation', [])
                if not isinstance(seg, list) or not seg:
                    problems.append(f'{name}: unsupported/empty segmentation {a["id"]}')
                    continue
                for poly in seg:
                    if len(poly) < 6 or len(poly) % 2 or not np.isfinite(poly).all():
                        problems.append(f'{name}: invalid polygon {a["id"]}')
                mask |= _rasterize_coco_segmentation(seg, w, h)
            positive = int(label['fractured'])
            if bool(mask.any()) != bool(positive):
                problems.append(f'{name}: fracture-label/mask disagreement')
            if int(label['fracture_count']) != len(aa):
                problems.append(f'{name}: fracture count differs from instance annotations')
            small = cv2.resize(im, (32, 32), interpolation=cv2.INTER_AREA)
            d = cv2.resize(im, (9, 8), interpolation=cv2.INTER_AREA)
            bits = np.packbits(d[:, 1:] > d[:, :-1]).tobytes()
            rows.append(dict(label, member=members[name][0], width=w, height=h,
                             sha256=digest(data), decoded_sha256=digest(str(im.shape).encode()+im.tobytes()),
                             mask_pixels=int(mask.sum()), mask_pixels_256=int(cv2.resize(mask, (256, 256), interpolation=cv2.INTER_NEAREST).sum()),
                             annotation_ids=[a['id'] for a in aa]))
            thumbs.append(small)
            perceptual.append(int.from_bytes(bits, 'big'))
            if (i + 1) % 500 == 0:
                print(f'audited {i+1}/{len(labels)}', flush=True)
        official = {}
        for split in ['train', 'val', 'test']:
            fn = 'valid' if split == 'val' else split
            entries = list(csv.reader(io.StringIO(z.read(f'FracAtlas/Utilities/Fracture Split/{fn}.csv').decode())))
            official[split] = [x[0] for x in entries if x and x[0].endswith(('.jpg', '.png'))]
    if problems:
        (out / 'audit_errors.json').write_text(json.dumps(problems, indent=2))
        raise SystemExit(f'{len(problems)} integrity issues; inspect audit_errors.json before freezing.')
    parents = list(range(len(rows)))
    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i
    def union(i, j):
        parents[find(j)] = find(i)
    exact = defaultdict(list)
    for i, r in enumerate(rows):
        exact[r['decoded_sha256']].append(i)
    for group in exact.values():
        for i in group[1:]:
            union(group[0], i)
    near = []
    for i in range(len(rows)):
        for j in range(i):
            distance = (perceptual[i] ^ perceptual[j]).bit_count()
            if distance <= 4:
                mae = float(np.abs(thumbs[i].astype(float)-thumbs[j]).mean())
                if mae < 8:
                    near.append({'a':rows[j]['image_id'], 'b':rows[i]['image_id'], 'dhash_distance':distance, 'thumbnail_mae':mae})
                    # Conservative grouping of candidate related images avoids leakage;
                    # it does not establish patient identity or image equivalence.
                    union(j, i)
    groups = defaultdict(list)
    for i in range(len(rows)):
        groups[find(i)].append(i)
    strata = defaultdict(list)
    for g, indices in groups.items():
        strata[max(int(rows[i]['fractured']) for i in indices)].append(g)
    rng = np.random.default_rng(42)
    for gs in strata.values():
        gs.sort(key=lambda g: min(rows[i]['image_id'] for i in groups[g]))
        rng.shuffle(gs)
        n = len(gs)
        for k, g in enumerate(gs):
            split = 'train' if k < int(.7*n) else 'val' if k < int(.85*n) else 'test'
            gid = min(rows[i]['image_id'] for i in groups[g])
            for i in groups[g]:
                rows[i].update(split=split, group=gid)
    manifest = {'protocol':'grouped-all-images-v1', 'seed':42, 'group_rule':'decoded exact duplicates OR dHash distance <=4 and 32x32 grayscale MAE <8; conservative related-image candidates',
                'patient_independence_verified':False, 'historical_checkpoint_exposure':'unknown; diagnostic only',
                'archive_sha256':hashlib.file_digest(open(args.archive,'rb'),'sha256').hexdigest(), 'exclusions':exclusions, 'rows':rows}
    encoded = json.dumps(manifest, indent=2).encode()
    (out/'manifest.json').write_bytes(encoded)
    (out/'manifest.sha256').write_text(digest(encoded)+'\n')
    for split in ['train','val','test']:
        (out/f'{split}.txt').write_text('\n'.join(r['image_id'] for r in rows if r['split']==split)+'\n')
    counts = {s:dict(Counter('fractured' if int(r['fractured']) else 'normal' for r in rows if r['split']==s)) for s in ['train','val','test']}
    official_sets = {s:set(v) for s,v in official.items()}
    report = {'source_images':len(labels), 'images':len(rows), 'exclusions':exclusions, 'positive_images':sum(int(r['fractured']) for r in rows), 'annotations':sum(len(r['annotation_ids']) for r in rows),
              'crc':'pass', 'integrity_errors':problems, 'exact_duplicate_groups':[[rows[i]['image_id'] for i in g] for g in exact.values() if len(g)>1],
              'near_duplicate_candidates':near, 'groups':len(groups), 'splits':counts, 'official_positive_split_sizes':{s:len(v) for s,v in official.items()},
              'official_overlap':{a+'_'+b:len(official_sets[a]&official_sets[b]) for a,b in [('train','val'),('train','test'),('val','test')]},
              'positive_masks_lost_at_256':[r['image_id'] for r in rows if int(r['fractured']) and not r['mask_pixels_256']],
              'manifest_sha256':digest(encoded), 'grouping_limitation':'No patient identifiers; perceptual candidate grouping is heuristic and requires visual review.'}
    (out/'audit.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ['near_duplicate_candidates','exact_duplicate_groups']}, indent=2))


if __name__ == '__main__':
    main()
