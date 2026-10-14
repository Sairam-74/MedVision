"""Explicit opt-in adapter for new logits bundles; historical default preserved."""
import base64
import json
from pathlib import Path
from functools import lru_cache
import cv2
from medvision_pipeline import load_bundle, predict_bundle, sha
from medvision_ai import predict_from_checkpoint, assess_severity

ORIGINAL_CHECKPOINT_SHA256='922f30bf691b9979aee65d386bcf73d2643558c049a7d11ab013fea315f39b81'

@lru_cache(maxsize=4)
def _verify_original(path, size, modified):
    if sha(path) != ORIGINAL_CHECKPOINT_SHA256:
        raise ValueError('Unrecognized legacy checkpoint; select an explicit versioned model bundle')


def assert_legacy_checkpoint(checkpoint_path):
    checkpoint=Path(checkpoint_path).resolve()
    bundle=checkpoint.parent/'bundle.json'
    if bundle.is_file():
        document=json.loads(bundle.read_text(encoding='utf-8'))
        declared=(bundle.parent/document.get('checkpoint','')).resolve()
        if declared==checkpoint and document.get('output_contract')=='binary-logits-v2':
            raise ValueError('Logits checkpoints require MEDVISION_BUNDLE; legacy sigmoid inference is incompatible')
    stat=checkpoint.stat()
    _verify_original(str(checkpoint),stat.st_size,stat.st_mtime_ns)


def ready_bundle(bundle_path):
    path=Path(bundle_path).resolve()
    document=json.loads(path.read_text(encoding='utf-8'))
    _,_,_,document=load_bundle(str(path),sha(path),document['checkpoint_sha256'],'cpu')
    return {'status':'ready','modelSha256':document['checkpoint_sha256'],'device':'cpu',
            'outputContract':document['output_contract'],'bundleSha256':sha(path),
            'calibrationStatus':document['calibration_status']}


def predict(image_path,checkpoint_path,bundle_path=None):
    if not bundle_path:
        assert_legacy_checkpoint(checkpoint_path)
        return predict_from_checkpoint(image_path,checkpoint_path)
    result=predict_bundle(image_path,bundle_path)
    metadata=result['metadata']
    mask=result['mask']
    _,features,_=assess_severity(mask)
    def encoded(region):
        ok,data=cv2.imencode('.png',region*255)
        if not ok: raise RuntimeError('Mask encoding failed')
        return base64.b64encode(data.tobytes()).decode('ascii')
    return dict(mask_png_base64=encoded(mask),raw_mask_png_base64=encoded(result['raw_mask']),
                mask_shape=list(mask.shape),mask_present=bool(mask.any()),
                severity_features=features,severity_tier='Not applicable',
                model_sha256=metadata['checkpoint_sha256'],bundle_sha256=metadata['bundle_sha256'],
                output_contract=metadata['output_contract'],preprocessing=metadata['preprocess'],
                calibrated_threshold=metadata['postprocess']['threshold'],
                postprocessing=metadata['postprocess'],threshold_provenance=metadata['calibration_status'],
                geometry_units='native image pixels; clinical severity unavailable',
                geometry_transform=metadata['geometry'])
