"""Real inference using the same binary-logits-v2 native path as validation."""
import argparse
import json
from pathlib import Path
import sys
import cv2
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from medvision_pipeline import predict_bundle
from medvision_ai import create_overlay

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--image',required=True)
    ap.add_argument('--bundle',required=True)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    out=Path(args.out)
    if out.exists():
        raise ValueError('Use a new output directory')
    prediction=predict_bundle(args.image,args.bundle)
    out.mkdir(parents=True)
    np.savez_compressed(out/'probability.npz',probability=prediction['probability'])
    for key in ('mask','raw_mask'):
        if not cv2.imwrite(str(out/f'{key}.png'),prediction[key]*255):
            raise RuntimeError('Could not save mask')
    create_overlay(args.image,prediction['mask'],str(out/'overlay.png'),'prediction')
    (out/'prediction.json').write_text(json.dumps(prediction['metadata'],indent=2))
    print(json.dumps({'native_shape':prediction['mask'].shape,'predicted_pixels':int(prediction['mask'].sum()),
                      'calibration_status':prediction['metadata']['calibration_status']}))

if __name__=='__main__':
    main()
