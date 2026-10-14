"""Verify production frontend assets and actual inference over a live socket."""
import json
from pathlib import Path
import re
import time
import zipfile

import httpx


def main():
    evidence = {}
    with httpx.Client(base_url='http://localhost:8000',timeout=60) as client:
        page = client.get('/login')
        assert page.status_code==200
        assets = re.findall(r'(?:src|href)="(/assets/[^"]+)"',page.text)
        assert assets
        for asset in assets:
            assert client.get(asset).status_code==200,asset
        ready = client.get('/ready')
        assert ready.status_code==200
        login = client.post('/auth/login',json={'identifier':'demo.clinician@example.invalid','password':'password123'})
        assert login.status_code==200
        evidence.update(page_status=page.status_code,assets_checked=assets,readiness=ready.json(),login_status=login.status_code)
        with zipfile.ZipFile('FracAtlas.zip') as z:
            member = next(n for n in z.namelist() if n.endswith('IMG0000019.jpg') and n.startswith('FracAtlas/images/'))
            start = time.perf_counter()
            queued = client.post('/analyses',files={'image':('live-demo.jpg',z.read(member),'image/jpeg')})
        assert queued.status_code==200,queued.text
        aid = queued.json()['analysisId']
        for _ in range(300):
            status = client.get(f'/analyses/{aid}/status').json()
            if status['status'] in ['completed','failed']:
                break
            time.sleep(.1)
        assert status['status']=='completed',status
        result = client.get(f'/analyses/{aid}').json()
        assert client.get(result['overlayUrl']).status_code==200
        assert client.get(f'/analyses/{aid}/export').json()==result
        assert any(a['id']==aid for a in client.get('/analyses').json())
        evidence.update(analysis_id=aid,mask_shape=result['maskShape'],model_sha256=result['modelSha256'],
                        elapsed_seconds=time.perf_counter()-start,history_and_export='pass')
    Path('experiments/session_20261005/demo_http.json').write_text(json.dumps(evidence,indent=2))
    print(json.dumps(evidence,indent=2))


if __name__=='__main__':
    main()
