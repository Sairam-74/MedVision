"""Verify native output equality across evaluation, bundle CLI and real API."""
import asyncio
import base64
import json
from pathlib import Path
import sys
import zipfile
import cv2
import httpx
import numpy as np
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import medvision_pipeline as p
import backend_service as b


async def main():
    torch.set_num_threads(2); cv2.setNumThreads(1)
    session=Path('experiments/session_20261006')
    b.HISTORY_PATH=session/'phase4_api_history.json'
    bundle=Path('experiments/P4_overfit_128/bundle.json').resolve()
    b.BUNDLE_PATH=str(bundle)
    dataset=p.FracDataset('FracAtlas.zip','experiments/data_v2/manifest.json','train',p.PreprocessConfig(size=128))
    ids=json.loads(Path('experiments/P4_overfit_128/config.json').read_text())['train_ids']
    evidence={'contract':p.CONTRACT,'bundle_sha256':p.sha(bundle),'samples':[],
              'scope':'Two memorized training images only; path equivalence, not generalization','test_evaluated':False}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=b.app),base_url='http://127.0.0.1:8000') as client:
        ready=await client.get('/ready'); assert ready.status_code==200,ready.text
        assert ready.json()['outputContract']==p.CONTRACT
        evidence['ready']=ready.json()
        for name in ids:
            index=next(i for i,r in enumerate(dataset.rows) if r['image_id']==name)
            image,target=dataset.native(index)
            with zipfile.ZipFile('FracAtlas.zip') as z: data=z.read(dataset.rows[index]['member'])
            image_path=session/name
            image_path.write_bytes(data)
            direct=p.predict_bundle(image_path,bundle)
            posted=await client.post('/analyses',files={'image':(name,data,'image/jpeg')})
            assert posted.status_code==200,posted.text
            analysis_id=posted.json()['analysisId']
            for _ in range(100):
                status=(await client.get(f'/analyses/{analysis_id}/status')).json()
                if status['status'] in ('completed','failed'): break
                await asyncio.sleep(.05)
            assert status['status']=='completed',status
            result=(await client.get(f'/analyses/{analysis_id}')).json()
            delivered=cv2.imdecode(np.frombuffer(base64.b64decode(result['maskPngBase64']),np.uint8),cv2.IMREAD_GRAYSCALE)>0
            raw=cv2.imdecode(np.frombuffer(base64.b64decode(result['rawMaskPngBase64']),np.uint8),cv2.IMREAD_GRAYSCALE)>0
            assert delivered.shape==image.shape and np.array_equal(delivered,direct['mask'].astype(bool))
            assert np.array_equal(raw,direct['raw_mask'].astype(bool))
            assert result['outputContract']==p.CONTRACT and result['bundleSha256']==p.sha(bundle)
            assert result['severity']=='not_applicable' and 'confidence' not in result
            assert result['severityFeatures']['area']==int(delivered.sum())
            tp=int((delivered&target.astype(bool)).sum()); fp=int((delivered&~target.astype(bool)).sum()); fn=int((~delivered&target.astype(bool)).sum())
            evidence['samples'].append({'image_id':name,'native_shape':list(image.shape),'pipeline_api_masks_identical':True,
                                        'native_positive_dice':2*tp/(2*tp+fp+fn) if target.any() else None,
                                        'normal_predicted_pixels':int(delivered.sum()) if not target.any() else None})
        # Wrong metadata/checksum must fail readiness without falling back to random weights.
        invalid=json.loads(bundle.read_text()); invalid['checkpoint_sha256']='0'*64
        bad=bundle.parent/'invalid_bundle_check.json'; bad.write_text(json.dumps(invalid))
        b.BUNDLE_PATH=str(bad)
        rejected=await client.get('/ready'); assert rejected.status_code==503
        evidence['invalid_bundle_status']=rejected.status_code
        # Explicitly forbid sending logits through the historical sigmoid contract.
        historical_checkpoint=b.CHECKPOINT_PATH
        b.BUNDLE_PATH=None
        b.CHECKPOINT_PATH=bundle.parent/'model.pt'
        wrong_contract=await client.get('/ready'); assert wrong_contract.status_code==503
        evidence['logits_as_legacy_rejected_status']=wrong_contract.status_code
        b.CHECKPOINT_PATH=historical_checkpoint
        # Default legacy path is still explicitly selectable; never auto-promote smoke weights.
        b.BUNDLE_PATH=None
        legacy_ready=await client.get('/ready'); assert legacy_ready.status_code==200
        assert legacy_ready.json()['modelSha256']=='922f30bf691b9979aee65d386bcf73d2643558c049a7d11ab013fea315f39b81'
        evidence['historical_default_ready']=legacy_ready.json()
    (session/'phase4_bundle_api.json').write_text(json.dumps(evidence,indent=2))
    print(json.dumps(evidence,indent=2))


if __name__=='__main__':
    asyncio.run(main())
