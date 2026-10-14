"""Read-only exact TRAIN tensors with the unchanged reliability augmentation.

Used only by future research trainers. Existing trainers remain unchanged.
"""
import json
from pathlib import Path
import sys

import numpy as np
import torch
from torch.utils.data import Dataset

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import medvision_pipeline as p


class CachedReliabilityDataset(Dataset):
    def __init__(self, cache, manifest, config, seed=42, elastic=False, verify_hashes=True):
        self.cache = Path(cache).resolve()
        if ROOT not in self.cache.parents:
            raise ValueError('Workspace TRAIN cache required')
        metadata = json.loads((self.cache/'completion.json').read_text())
        if metadata['status'] != 'completed_exact_train_cache' or metadata['manifest_sha256'] != p.sha(manifest):
            raise ValueError('Incomplete or wrong-partition cache')
        from dataclasses import asdict
        if metadata['preprocess'] != asdict(config):
            raise ValueError('Cache preprocessing differs from requested run')
        for source in ('medvision_pipeline.py', 'medvision_ai.py', 'tools/cache_ai_training_inputs.py'):
            if metadata['source_hashes'][source] != p.sha(ROOT/source):
                raise ValueError('Cached preprocessing source changed')
        if metadata['rows_sha256'] != p.sha(self.cache/'rows.json'):
            raise ValueError('Cached row metadata changed')
        self.rows = json.loads((self.cache/'rows.json').read_text())
        document = json.loads(Path(manifest).read_text())
        if self.rows != [r for r in document['rows'] if r['split']=='train']:
            raise ValueError('Require exact TRAIN-only order/membership')
        if verify_hashes:
            for name in ('image', 'target', 'valid'):
                if metadata['cache_hashes'][name] != p.sha(self.cache/(name+'.npy')):
                    raise ValueError('Cached tensor bytes changed')
        self.arrays = {name:np.load(self.cache/(name+'.npy'), mmap_mode='r') for name in ('image', 'target', 'valid')}
        for name, array in self.arrays.items():
            expected_dtype = np.float32 if name=='image' else np.uint8
            if array.shape != tuple(metadata['shape']) or array.dtype != expected_dtype or array.flags.writeable:
                raise ValueError('Cache tensor shape/dtype/read-only contract mismatch')
        self.config, self.seed, self.elastic, self.epoch = config, seed, elastic, 0
        self.metadata = metadata

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        x, y, valid = [self.arrays[name][index].astype(np.float32, copy=True) for name in ('image', 'target', 'valid')]
        positive = bool(int(self.rows[index]['fractured']))
        seed = np.random.SeedSequence([self.seed, self.epoch, index]).generate_state(1)[0]
        ax, ay, av = p.augment(x, y, valid, int(seed), self.elastic)
        if not positive or bool(ay.any()):
            x, y, valid = ax, ay, av
        if positive != bool(y.any()):
            raise ValueError('Cached training pair lost explicit case label')
        return (*[torch.from_numpy(a.copy()).unsqueeze(0) for a in (x, y, valid)], torch.tensor(positive))
