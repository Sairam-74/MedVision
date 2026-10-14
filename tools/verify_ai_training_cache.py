"""Actual TRAIN tensor and augmentation parity; no model or test evaluation."""
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

import cv2
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import medvision_pipeline as p
from tools.ai_cached_dataset import CachedReliabilityDataset
from tools.train_reliability_candidate import ReliabilityDataset
from tools.evaluate_ai_baseline import save


def main():
    cache = ROOT/'experiments/AI_TRAIN_CACHE_v3_256_r2'
    manifest = ROOT/'experiments/data_v3_reliability_20261007/manifest.json'
    config = p.PreprocessConfig(size=256, resize='stretch', clahe=True, blur_kernel=3, normalization='unit')
    cv2.setNumThreads(1)
    torch.set_num_threads(1)
    cached = CachedReliabilityDataset(cache, manifest, config)
    direct = ReliabilityDataset(ROOT/'FracAtlas.zip', manifest, 'train', config, True, 42, False)
    if direct.rows != cached.rows:
        raise ValueError('Membership/order differs')
    indices = [i for label in (0, 1) for i in [j for j, r in enumerate(direct.rows) if int(r['fractured'])==label][:8]]
    erased = next(i for i, r in enumerate(direct.rows) if r['image_id']=='IMG0002386.jpg')
    if erased not in indices:
        indices.append(erased)
    comparisons, times = [], {'direct':[], 'cached':[]}
    for epoch in (1, 9, 12):
        direct.epoch = cached.epoch = epoch
        for i in indices:
            start = time.perf_counter()
            expected = direct[i]
            times['direct'].append(time.perf_counter()-start)
            start = time.perf_counter()
            actual = cached[i]
            times['cached'].append(time.perf_counter()-start)
            exact = [torch.equal(a, b) and a.dtype==b.dtype and a.shape==b.shape for a, b in zip(actual, expected)]
            if not all(exact):
                raise ValueError('Actual augmented TRAIN tensors differ')
            comparisons.append(dict(epoch=epoch, image_id=direct.rows[i]['image_id'],
                                    image_target_valid_case_label_exact=exact, projected_positive_pixels=int(actual[1].sum())))
    result = dict(status='passed', comparison_count=len(comparisons), unique_train_images=len(indices),
        comparisons=comparisons, preprocessing=asdict(config), train_ids_exact=True,
        cache_completion_sha256=p.sha(cache/'completion.json'), loader_source_sha256=p.sha(ROOT/'tools/ai_cached_dataset.py'),
        verification_source_sha256=p.sha(__file__), direct_source_sha256=p.sha(ROOT/'tools/train_reliability_candidate.py'),
        descriptive_CPU_input_read_median_ms={name:float(np.median(values)*1000) for name, values in times.items()},
        timing_caveat='Sequential CPU input reads during another GPU experiment, warm OS cache. Not inference latency or full training throughput.',
        current_training_modified=False, model_trained=False, validation_images_read=0, calibration_images_read=0, test_images_read=0)
    save(ROOT/'experiments/session_20261007_ai_loop_01/TRAIN_CACHE_AUGMENTATION_PARITY.json', result)
    print(json.dumps({key:value for key,value in result.items() if key!='comparisons'}, indent=2))


if __name__ == '__main__':
    main()
