"""Reviewed corrections override train-only images; held-out partitions remain frozen."""
import json
from pathlib import Path
import hashlib
import cv2
import numpy as np
from medvision_pipeline import FracDataset

class ReviewedDataset(FracDataset):
    def __init__(self,*args,feedback_manifest=None,**kwargs):
        super().__init__(*args,**kwargs)
        if not feedback_manifest:return
        if not self.training:raise ValueError('Feedback can only modify training data')
        feedback=json.loads(Path(feedback_manifest).read_text(encoding='utf-8'))
        document=json.loads(Path(args[1]).read_text(encoding='utf-8'))
        known={r['decoded_sha256']:r for r in document['rows']}
        reviewed=[]; replaced=set()
        for r in feedback['rows']:
            image=cv2.imread(r['image_path'],cv2.IMREAD_GRAYSCALE);mask=cv2.imread(r['mask_path'],cv2.IMREAD_GRAYSCALE)
            if image is None or mask is None or image.shape!=mask.shape or not set(np.unique(mask)).issubset({0,255}):raise ValueError('Invalid reviewed mask')
            digest=hashlib.sha256(str(image.shape).encode()+image.tobytes()).hexdigest()
            source=known.get(digest)
            if not source or source['split']!='train':raise ValueError('Reviewed images must match the documented training cohort; held-out/unknown images cannot enter routine retraining')
            if hashlib.sha256(Path(r['mask_path']).read_bytes()).hexdigest()!=r['mask_sha256'] or hashlib.sha256(Path(r['image_path']).read_bytes()).hexdigest()!=r['image_sha256']:raise ValueError('Reviewed annotation changed')
            if bool(mask.any())!=bool(r['fractured']):raise ValueError('Reviewed label disagrees with segmentation')
            replaced.add(digest); reviewed.append(dict(r,feedback=True,image_id=r['feedback_id'],group=source['group'],decoded_sha256=digest))
        self.rows=reviewed+[r for r in self.rows if r['decoded_sha256'] not in replaced]

    def native(self,index):
        row=self.rows[index]
        if row.get('feedback'):
            return cv2.imread(row['image_path'],cv2.IMREAD_GRAYSCALE),(cv2.imread(row['mask_path'],cv2.IMREAD_GRAYSCALE)>0).astype(np.uint8)
        return super().native(index)
