"""Meaningful regression checks plus real-model HTTP upload smoke; no training."""
import asyncio
import base64
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import zipfile
import importlib.metadata as metadata

import cv2
import httpx
import numpy as np
import psutil
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import medvision_ai as m
import backend_service as b


async def main():
    torch.set_num_threads(4)
    m.set_seed(42)
    out = Path('experiments/session_20261006')
    before = hashlib.file_digest(open('best_model.pt','rb'),'sha256').hexdigest()
    evidence = {'python':sys.version, 'platform':platform.platform(), 'torch':torch.__version__, 'cuda_build':torch.version.cuda,
                'cuda_available':torch.cuda.is_available(), 'ram_bytes':psutil.virtual_memory().total,
                'disk_free_bytes':psutil.disk_usage('.').free,
                'packages':{p:metadata.version(p) for p in ['torch','numpy','opencv-python-headless','scikit-learn','fastapi','uvicorn','httpx','python-multipart']}}
    if torch.cuda.is_available():
        prop = torch.cuda.get_device_properties(0)
        evidence.update(gpu=prop.name, vram_bytes=prop.total_memory)
    checks = []
    for name, points in [('empty',[]),('single',[(2,3)]),('thin',[(2,i) for i in range(2,10)]),('multiple',[(2,3),(12,13)])]:
        a = np.zeros((16,20),np.uint8)
        for y,x in points:
            a[y,x] = 1
        mask, features, tier = m.assess_severity(a)
        assert np.array_equal(a,mask)
        assert features['area'] == len(points)
        assert (tier == 'Not applicable') == (not points)
        result = b._result_from_prediction(name, {'mask_present':bool(mask.any()),'severity_features':features,'severity_tier':tier})
        assert (result['fractureStatus']=='fracture') == bool(points)
        assert 'confidence' not in result
        checks.append({'case':name,'pixels':len(points),'components':features['component_count'],'tier':tier})
    evidence['mask_regressions'] = checks
    transport = httpx.ASGITransport(app=b.app)
    async with httpx.AsyncClient(transport=transport, base_url='http://127.0.0.1:8000') as client:
        ready = await client.get('/ready')
        assert ready.status_code==200,ready.text
        evidence['readiness'] = ready.json()
        samples = []
        with zipfile.ZipFile('FracAtlas.zip') as z:
            for name in ['IMG0000019.jpg','IMG0000000.jpg']:
                member = next(n for n in z.namelist() if n.startswith('FracAtlas/images/') and n.endswith(name))
                data = z.read(member)
                native = cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_GRAYSCALE)
                start = time.perf_counter()
                response = await client.post('/analyses', files={'image':(name,data,'image/jpeg')})
                assert response.status_code==200,response.text
                ident = response.json()['analysisId']
                for _ in range(300):
                    status = (await client.get(f'/analyses/{ident}/status')).json()
                    if status['status'] in ['completed','failed']:
                        break
                    await asyncio.sleep(.1)
                assert status['status']=='completed',status
                result = status['result']
                mask = cv2.imdecode(np.frombuffer(base64.b64decode(result['maskPngBase64']),np.uint8),cv2.IMREAD_GRAYSCALE)
                assert mask.shape == native.shape
                for key in ['originalImageUrl','overlayUrl']:
                    image_response = await client.get(result[key])
                    assert image_response.status_code==200
                    image = cv2.imdecode(np.frombuffer(image_response.content,np.uint8),cv2.IMREAD_GRAYSCALE)
                    assert image.shape==native.shape
                    if key=='originalImageUrl':
                        assert image_response.content == data
                samples.append({'file':name,'native_shape':list(native.shape),'request_seconds':time.perf_counter()-start,'result':result})
        evidence['real_api_samples'] = samples
        invalid = await client.post('/analyses',files={'image':('fake.jpg',b'\xff\xd8\xffbad','image/jpeg')})
        unsupported = await client.post('/analyses',files={'image':('fake.txt',b'hello','text/plain')})
        oversized = await client.post('/analyses',content=b'x',headers={'content-length':str(b.MAX_UPLOAD_BYTES+1)})
        _, wide_png = cv2.imencode('.png',np.zeros((2,9000),np.uint8))
        too_wide = await client.post('/analyses',files={'image':('wide.png',wide_png.tobytes(),'image/png')})
        assert too_wide.status_code==413
        assert (invalid.status_code,unsupported.status_code,oversized.status_code)==(422,415,413)
        evidence['invalid_upload_statuses'] = [invalid.status_code,unsupported.status_code,oversized.status_code]
        evidence['oversized_dimensions_status'] = too_wide.status_code
    after = hashlib.file_digest(open('best_model.pt','rb'),'sha256').hexdigest()
    assert before==after
    evidence['original_checkpoint_unchanged'] = before
    (out/'runtime_smoke.json').write_text(json.dumps(evidence,indent=2))
    print(json.dumps({k:v for k,v in evidence.items() if k!='real_api_samples'},indent=2))
    print('Real API upload -> prediction -> native overlay PASS',flush=True)


if __name__=='__main__':
    asyncio.run(main())
