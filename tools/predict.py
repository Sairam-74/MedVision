"""Inference only: save native-coordinate output without training."""
import argparse
import base64
import json
from pathlib import Path
import sys
import cv2
import numpy as np
import torch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from medvision_ai import predict_from_checkpoint, create_overlay

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', required=True)
    parser.add_argument('--checkpoint', default='best_model.pt')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out)
    if out.exists():
        raise SystemExit('Output directory exists; choose a new path.')
    torch.set_num_threads(4)
    result = predict_from_checkpoint(args.image, args.checkpoint)
    out.mkdir(parents=True)
    (out/'prediction.json').write_text(json.dumps(result, indent=2))
    png = base64.b64decode(result['mask_png_base64'])
    (out/'mask.png').write_bytes(png)
    mask = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_GRAYSCALE)>0
    create_overlay(args.image, mask.astype(np.uint8), str(out/'overlay.png'), 'prediction')
    print(json.dumps({k:v for k,v in result.items() if k!='mask_png_base64'}, indent=2))

if __name__=='__main__':
    main()
