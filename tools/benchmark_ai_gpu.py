"""Measured GPU feasibility on two TRAIN images; never a performance experiment."""
import json
from pathlib import Path
import sys
import time
import zipfile
import numpy as np
import cv2
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import medvision_ai as m
from tools.run_experiment import native_pair


def main():
    out = ROOT/'experiments/session_20261007_ai_baseline/gpu_benchmark.json'
    if out.exists():
        raise ValueError('Preserve benchmark evidence')
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable')
    torch.set_num_threads(2); cv2.setNumThreads(1); m.set_seed(42)
    rows = json.loads((ROOT/'experiments/data_v2/manifest.json').read_text())['rows']
    pair = [next(r for r in rows if r['split']=='train' and int(r['fractured'])==label) for label in (1,0)]
    with zipfile.ZipFile(ROOT/'FracAtlas.zip') as z:
        annotations = {a['id']:a for a in json.loads(z.read('FracAtlas/Annotations/COCO JSON/COCO_fracture_masks.json'))['annotations']}
        native = [native_pair(z, r, annotations) for r in pair]
    x = torch.from_numpy(np.array([m.preprocess_image_array(image) for image,_ in native])[:,None]).cuda()
    y = torch.from_numpy(np.array([cv2.resize(gt,(256,256),interpolation=cv2.INTER_NEAREST) for _,gt in native])[:,None]).float().cuda()
    model = m.AttentionUNet().cuda()
    m._load_model_weights(model, str(ROOT/'best_model.pt'))
    model.train(); optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    timings, losses = [], []
    torch.cuda.reset_peak_memory_stats()
    for step in range(5):
        torch.cuda.synchronize(); start = time.perf_counter()
        optimizer.zero_grad(set_to_none=True)
        p = model(x)
        loss = torch.nn.functional.binary_cross_entropy(p.clamp(1e-6,1-1e-6), y)+m.dice_loss(p,y)
        if not torch.isfinite(loss): raise RuntimeError('Nonfinite loss')
        loss.backward()
        if not all(torch.isfinite(v.grad).all() for v in model.parameters() if v.grad is not None):
            raise RuntimeError('Nonfinite gradients')
        torch.nn.utils.clip_grad_norm_(model.parameters(),10,error_if_nonfinite=True)
        optimizer.step(); torch.cuda.synchronize()
        timings.append(time.perf_counter()-start); losses.append(float(loss.detach()))
    result = dict(scope='GPU execution/memory feasibility on TWO training images, NOT generalization or candidate model; no weights saved',
                  torch=torch.__version__, cuda_build=torch.version.cuda, gpu=torch.cuda.get_device_name(0),
                  sample_ids=[r['image_id'] for r in pair], split='train', batch_size=2, input_size=256,
                  step_seconds=timings, losses=losses, median_step_seconds=float(np.median(timings[1:])),
                  peak_allocated_bytes=torch.cuda.max_memory_allocated(), peak_reserved_bytes=torch.cuda.max_memory_reserved(),
                  projected_training_only_epoch_seconds=float(np.median(timings[1:]))*1404,
                  test_images_read=0, original_weights_overwritten=False)
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
