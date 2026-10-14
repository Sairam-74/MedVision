"""Native-derived 512-pixel TRAIN cache; preserve the canonical 256 cache.

This separate producer uses the unchanged pipeline and canonical cache format.
Only original TRAIN images/annotations are decoded. No VAL/CAL/test images.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import medvision_pipeline as p
from tools.ai_atomic_io import json_atomic

MANIFEST = ROOT/'experiments/data_v3_reliability_20261007/manifest.json'
MANIFEST_SHA = '4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318'
ORIGINAL_SHA = '922f30bf691b9979aee65d386bcf73d2643558c049a7d11ab013fea315f39b81'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out',required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if ROOT not in out.parents or out.exists():
        raise ValueError('Exclusive NEW workspace cache required')
    if p.sha(MANIFEST) != MANIFEST_SHA or p.sha(ROOT/'best_model.pt') != ORIGINAL_SHA:
        raise ValueError('Protected manifest/checkpoint mismatch')
    manifest = json.loads(MANIFEST.read_text())
    if p.sha(ROOT/'FracAtlas.zip') != manifest['archive_sha256']:
        raise ValueError('Protected dataset mismatch')
    sources = ['medvision_pipeline.py','medvision_ai.py','tools/cache_ai_training_inputs.py',
               'tools/cache_ai_resolution_inputs.py','tools/ai_atomic_io.py']
    source_hashes = {name:p.sha(ROOT/name) for name in sources}
    config = p.PreprocessConfig(size=512,resize='stretch',clahe=True,blur_kernel=3,normalization='unit')
    dataset = p.FracDataset(ROOT/'FracAtlas.zip',MANIFEST,'train',config)
    if len(dataset) != 2808 or sum(int(r['fractured']) for r in dataset.rows) != 493:
        raise ValueError('Exact TRAIN membership required')
    cv2.setNumThreads(1)
    out.mkdir()
    shape = (len(dataset),config.size,config.size)
    arrays = {name:np.lib.format.open_memmap(out/(name+'.npy'),mode='w+',dtype=dtype,shape=shape)
              for name,dtype in [('image',np.float32),('target',np.uint8),('valid',np.uint8)]}
    started = time.perf_counter()
    target_counts = []
    for i,row in enumerate(dataset.rows):
        image,target = dataset.native(i)
        x,y,valid,_ = p.prepare(image,config,target)
        if not np.isfinite(x).all() or not np.isin(y,[0,1]).all() or not np.isin(valid,[0,1]).all():
            raise ValueError('Prepared tensor contract mismatch')
        if bool(y.any()) != bool(int(row['fractured'])):
            raise ValueError('Target/source-label mismatch')
        for name,value in [('image',x),('target',y),('valid',valid)]:
            arrays[name][i] = value
            if not np.array_equal(arrays[name][i].astype(np.float32),value):
                raise ValueError('Serialization changed a tensor')
        target_counts.append(dict(train_index=i,image_id=row['image_id'],source_positive=bool(int(row['fractured'])),
                                  target_pixels_512=int(y.sum()),valid_pixels_512=int(valid.sum())))
        if (i+1)%100 == 0 or i+1 == len(dataset):
            progress = dict(status='building_native_512_TRAIN_cache',images_completed=i+1,total=len(dataset),
                            validation_images_read=0,calibration_images_read=0,test_images_read=0)
            json_atomic(out/'progress.json',progress)
            print(json.dumps(dict(cached=i+1,total=len(dataset),elapsed_seconds=time.perf_counter()-started)),flush=True)
    for array in arrays.values():
        array.flush()
    del arrays
    arrays = {name:np.load(out/(name+'.npy'),mmap_mode='r') for name in ('image','target','valid')}
    verification = []
    indices = [i for label in (0,1) for i in [j for j,r in enumerate(dataset.rows) if int(r['fractured'])==label][:8]]
    for i in indices:
        image,target = dataset.native(i)
        expected = p.prepare(image,config,target)[:3]
        exact = {name:bool(np.array_equal(arrays[name][i].astype(np.float32),value))
                 for name,value in zip(('image','target','valid'),expected)}
        if not all(exact.values()):
            raise ValueError('Independent native re-decode/cache parity failed')
        verification.append(dict(train_index=i,image_id=dataset.rows[i]['image_id'],exact_float32_parity=exact))
    json_atomic(out/'rows.json',dataset.rows)
    json_atomic(out/'verification.json',verification)
    json_atomic(out/'target_representation.json',target_counts)
    result = dict(status='completed_exact_train_cache',train_images=len(dataset),train_positive_images=493,
        preprocess=asdict(config),manifest_sha256=p.sha(MANIFEST),archive_sha256=manifest['archive_sha256'],
        original_checkpoint_sha256=p.sha(ROOT/'best_model.pt'),source_hashes=source_hashes,
        builder='tools/cache_ai_resolution_inputs.py',canonical_cache_format_dependency='tools/cache_ai_training_inputs.py',
        input_source='Original native TRAIN X-rays and annotations; never rescale cached256 inputs',
        cache_hashes={name:p.sha(out/(name+'.npy')) for name in ('image','target','valid')},
        rows_sha256=p.sha(out/'rows.json'),target_representation_sha256=p.sha(out/'target_representation.json'),
        verification_sha256=p.sha(out/'verification.json'),
        shape=shape,image_dtype='float32',target_dtype='uint8',valid_dtype='uint8',
        contract='Convert binary target/valid to float32 before unchanged online augmentation; exact float32 image bytes.',
        stored_bytes=sum((out/(name+'.npy')).stat().st_size for name in ('image','target','valid')),
        elapsed_seconds=time.perf_counter()-started,all_written_tensors_bit_exact=True,independent_redecode_cases=len(verification),
        validation_images_read=0,calibration_images_read=0,test_images_read=0,current_trainer_modified=False,model_trained=False)
    if result['original_checkpoint_sha256'] != ORIGINAL_SHA or p.sha(MANIFEST) != MANIFEST_SHA:
        raise ValueError('Protected checkpoint/manifest changed during creation')
    if p.sha(ROOT/'FracAtlas.zip') != result['archive_sha256']:
        raise ValueError('Protected archive changed during creation')
    for name,digest in source_hashes.items():
        if p.sha(ROOT/name) != digest:
            raise ValueError('Cache producer/dependency source changed')
    json_atomic(out/'completion.json',result)
    print(json.dumps(dict(status=result['status'],size=512,TRAIN_sources=2808,
                         stored_bytes=result['stored_bytes'],elapsed_seconds=result['elapsed_seconds'])),flush=True)


if __name__ == '__main__':
    main()
