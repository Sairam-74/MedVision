"""Security and real-upload integration checks. CI uses a deterministic predictor.

--real uses the original checkpoint and distinct validation X-rays; no test data.
"""
import argparse
import asyncio
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import zipfile
import struct
import zlib
import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--real', action='store_true')
    parser.add_argument('--bundle')
    parser.add_argument('--archive', default=str(ROOT / 'FracAtlas.zip'))
    parser.add_argument('--out', default='experiments/session_20261006_p6p7/secure_api.json')
    args = parser.parse_args()
    checks = []
    def check(condition, name):
        assert condition, name
        checks.append(name)
    with tempfile.TemporaryDirectory(prefix='medvision-api-') as temporary:
        folder = Path(temporary)
        os.environ['MEDVISION_DB'] = str(folder / 'app.sqlite3')
        os.environ['MEDVISION_GENERATED_DIR'] = str(folder / 'generated')
        os.environ['MEDVISION_DEMO_PASSWORD'] = 'test-only-password-123'
        os.environ['OMP_NUM_THREADS'] = '2'
        os.environ['MKL_NUM_THREADS'] = '2'
        if args.bundle:
            os.environ['MEDVISION_BUNDLE'] = str(Path(args.bundle).resolve())
        else:
            os.environ.pop('MEDVISION_BUNDLE', None)
        import backend_service as b
        from fastapi.testclient import TestClient
        inputs = []
        if args.real:
            manifest = json.loads((ROOT / 'experiments/data_v2/manifest.json').read_text())
            with zipfile.ZipFile(args.archive) as z:
                for positive in (1, 0):
                    row = next(r for r in manifest['rows'] if r['split'] == 'val' and int(r['fractured']) == positive)
                    inputs.append((row['image_id'], z.read(row['member'])))
        else:
            for color in (80, 160):
                buffer = io.BytesIO()
                Image.new('L', (120, 240), color).save(buffer, format='PNG')
                inputs.append((f'fixture-{color}.png', buffer.getvalue()))
            def predict(image, checkpoint):
                shape = cv2.imread(image, 0).shape
                mask = np.zeros(shape, np.uint8)
                mask[20:40, 30:40] = 255
                encoded = cv2.imencode('.png', mask)[1]
                return {'mask_png_base64': base64.b64encode(encoded).decode(), 'mask_shape': list(shape),
                        'mask_present': True, 'severity_tier': 'Not applicable', 'severity_features': {'area': 200},
                        'model_sha256': 'test-double-not-real-model'}
            b._predict_selected = predict
        other = {**b.demo_user, 'id': 'user-2', 'email': 'second@example.invalid'}
        b.store.seed_user(other, 'test-only-password-456')
        request_times = []
        case_ids = []
        with TestClient(b.app) as client, TestClient(b.app) as second:
            check(client.get('/api/research').status_code == 401, 'research evidence requires a session')
            for path in ('/analyses', '/ready', '/generated/history.json'):
                check(client.get(path).status_code == 401, 'unauthenticated ' + path)
            check(client.post('/auth/refresh').status_code == 401, 'refresh requires valid session')
            check(client.post('/auth/login', json={'identifier': b.demo_user['email'], 'password': 'wrong-password'}).status_code == 401, 'wrong password rejected')
            response = client.post('/auth/login', json={'identifier': b.demo_user['email'], 'password': os.environ['MEDVISION_DEMO_PASSWORD']})
            check(response.status_code == 200, 'login')
            evidence_response = client.get('/api/research')
            check(evidence_response.status_code == 200, 'authenticated research evidence')
            evidence = evidence_response.json()
            check(len(evidence['runs']) == 3 and isinstance(evidence['delivery']['reservedTestEvaluated'], bool), 'live research reports explicit experiment and reserved-test state')
            check('guards' not in evidence and 'password' not in json.dumps(evidence).lower(), 'research projection excludes internal guards and credentials')
            check(response.json()['accessToken'] == '', 'no shared bearer credential in JSON')
            check('httponly' in response.headers['set-cookie'].lower() and 'samesite=strict' in response.headers['set-cookie'].lower(), 'HttpOnly Strict cookie')
            check(client.post('/auth/refresh').status_code == 200, 'authenticated refresh')
            check(client.post('/auth/login', json={}, headers={'Origin': 'https://untrusted.invalid'}).status_code == 403, 'cross-origin POST denied')
            check(client.get('/health', headers={'Host': 'evil.invalid'}).status_code == 400, 'untrusted host denied')
            check(client.post('/auth/login', content=b'x' * 16385).status_code == 413, 'auth body bounded')
            check(client.post('/auth/signup', json={}).status_code == 422, 'signup rejects missing credentials')
            selected_bundle = b.BUNDLE_PATH
            selected_checkpoint = b.CHECKPOINT_PATH
            b.BUNDLE_PATH = str(folder / 'missing-bundle.json')
            check(client.get('/ready').status_code == 503, 'invalid bundle fails readiness')
            b.BUNDLE_PATH = None
            b.CHECKPOINT_PATH = folder / 'unknown.pt'
            b.CHECKPOINT_PATH.write_bytes(b'not an approved model')
            check(client.get('/ready').status_code == 503, 'unrecognized legacy checkpoint rejected before loading')
            b.BUNDLE_PATH = selected_bundle
            b.CHECKPOINT_PATH = selected_checkpoint
            check(client.post('/analyses', files={'image': ('fake.png', b'fake-data', 'image/png')}).status_code == 415, 'invalid image signature rejected')
            check(client.post('/analyses', files={'image': ('corrupt.png', b'\x89PNG\r\n\x1a\ncorrupt', 'image/png')}).status_code == 422, 'corrupt image rejected')
            def png_chunk(kind, data):
                return struct.pack('!I', len(data))+kind+data+struct.pack('!I', zlib.crc32(kind+data)&0xffffffff)
            text_bomb = b'\x89PNG\r\n\x1a\n'+png_chunk(b'IHDR', struct.pack('!IIBBBBB',1,1,8,0,0,0,0))
            text_bomb += png_chunk(b'zTXt', b'comment\x00\x00'+zlib.compress(b'x'*(1024*1024+1)))
            text_bomb += png_chunk(b'IDAT',zlib.compress(b'\x00\x80'))+png_chunk(b'IEND',b'')
            check(client.post('/analyses',files={'image':('text-bomb.png',text_bomb,'image/png')}).status_code == 422, 'compressed PNG metadata bomb rejected with clear error')
            oversized = io.BytesIO(); Image.new('L', (8193, 1)).save(oversized, format='PNG')
            check(client.post('/analyses', files={'image': ('large.png', oversized.getvalue(), 'image/png')}).status_code == 413, 'dimensions bounded')
            check(client.post('/analyses', content=b'x', headers={'Content-Length': str(b.MAX_REQUEST_BYTES+1)}).status_code == 413, 'multipart request size bounded')
            too_large = b'\x89PNG\r\n\x1a\n' + b'x'*(b.MAX_UPLOAD_BYTES-7)
            check(client.post('/analyses', files={'image':('oversized.png',too_large,'image/png')}).status_code == 413, 'actual file bytes bounded independently of multipart headers')
            check(client.get('/generated/history.json').status_code == 404, 'history JSON is not a public image')
            check(client.get('/generated/uploads/%2e%2e/%2e%2e/best_model.pt').status_code == 404, 'traversal cannot retrieve model files')
            original_limit = b.STORAGE_LIMIT_BYTES
            b.STORAGE_LIMIT_BYTES = 0
            check(client.post('/analyses', files={'image': ('limited.png', inputs[0][1], 'image/png')}).status_code == 409, 'storage budget enforced before upload')
            b.STORAGE_LIMIT_BYTES = original_limit
            second.post('/auth/login', json={'identifier': other['email'], 'password': 'test-only-password-456'})
            readiness = client.get('/ready') if args.real else None
            if args.real: check(readiness.status_code == 200, 'real model readiness')
            for filename, image_bytes in inputs:
                started = time.perf_counter()
                uploaded = client.post('/analyses', files={'image': (filename, image_bytes, 'image/jpeg' if image_bytes[:2] == b'\xff\xd8' else 'image/png')})
                check(uploaded.status_code == 200, 'multipart upload ' + filename)
                case_id = uploaded.json()['analysisId']; case_ids.append(case_id)
                for _ in range(350):
                    status = client.get(f'/analyses/{case_id}/status').json()
                    if status['status'] in ('completed', 'failed', 'timed_out'): break
                    time.sleep(.2)
                check(status['status'] == 'completed', 'inference completed ' + filename)
                request_times.append((time.perf_counter()-started)*1000)
                result = client.get(f'/analyses/{case_id}').json()
                original = client.get(result['originalImageUrl'])
                check(hashlib.sha256(original.content).digest() == hashlib.sha256(image_bytes).digest(), 'original bytes belong to upload ' + filename)
                check(client.get(result['overlayUrl']).status_code == 200, 'protected overlay ' + filename)
                check(second.get(f'/analyses/{case_id}').status_code == 404, 'other account cannot read result')
                check(second.get(result['originalImageUrl']).status_code == 404, 'other account cannot read image')
                check(second.delete(f'/analyses/{case_id}').status_code == 404, 'other account cannot delete')
                check(client.get(f'/analyses/{case_id}/export').json() == result, 'export equals persisted result')
                check(result['metrics']['dice'] is None and result['metrics']['iou'] is None, 'no fabricated per-upload accuracy')
                if args.real:
                    image_path = folder / filename
                    image_path.write_bytes(image_bytes)
                    direct = b._predict_selected(str(image_path), str(b.CHECKPOINT_PATH))
                    check(result['maskPngBase64'] == direct['mask_png_base64'], 'API mask exactly equals direct inference')
                    check(result['outputContract'] == direct.get('output_contract', 'sigmoid-probabilities-v1'), 'output contract matches selected inference')
            check(case_ids[0] != case_ids[1], 'distinct uploads get distinct cases')
            saved_case, saved_result, saved_error = b.store.get_case(case_ids[0], 'user-1')
            old_result = {**saved_result, 'originalImageUrl':'http://127.0.0.1:8000/legacy-image.png', 'imageUrl':'https://untrusted.invalid/image.png'}
            b.store.save_case(saved_case, 'user-1', old_result, saved_error)
            restored = client.get(f'/analyses/{case_ids[0]}').json()
            check(restored['originalImageUrl'].startswith('/generated/uploads/') and restored['imageUrl'] == restored['originalImageUrl'], 'legacy image URLs reconstructed from owned paths')
            check(client.get(restored['originalImageUrl']).status_code == 200, 'legacy image remains accessible with current session host')
            check(len(client.get('/analyses').json()) == 2, 'durable owned history')
            from app_store import Store
            reloaded = Store(folder / 'app.sqlite3')
            check(len(reloaded.list_cases('user-1')) == 2, 'history survives storage reopen')
            check(client.delete(f'/analyses/{case_ids[0]}').status_code == 200, 'owned completed deletion')
            check(client.get(f'/analyses/{case_ids[0]}').status_code == 404, 'deleted result unavailable')
            if not args.real:
                original_predict = b._predict_selected
                b.INFERENCE_TIMEOUT = .03
                def slow(*arguments):
                    time.sleep(.25); return original_predict(*arguments)
                b._predict_selected = slow
                uploaded = client.post('/analyses', files={'image': ('slow.png', inputs[0][1], 'image/png')})
                slow_id = uploaded.json()['analysisId']
                time.sleep(.10)
                check(client.get(f'/analyses/{slow_id}/status').json()['status'] == 'timed_out', 'inference timeout visible')
                check(b.inference_lock.locked(), 'timed-out worker retains inference lock')
                check(client.delete(f'/analyses/{slow_id}').status_code == 409, 'still-running timed-out job cannot be deleted')
                time.sleep(.3)
                check(not b.inference_lock.locked(), 'worker completion releases lock')
            token = client.cookies.get(b.COOKIE)
            check(client.post('/auth/logout').status_code == 200, 'logout')
            client.cookies.set(b.COOKIE, token)
            check(client.get('/analyses').status_code == 401, 'revoked session cannot read history')
            check(client.post('/auth/refresh').status_code == 401, 'revoked session cannot refresh')
            token, _ = b.store.session('user-1', ttl=-1)
            client.cookies.set(b.COOKIE, token)
            check(client.get('/analyses').status_code == 401, 'expired session rejected')
            client.cookies.clear()
            check(client.get('/analyses', headers={'Authorization': 'Bearer legacy-shared-token'}).status_code == 401, 'bearer strings cannot bypass cookie authentication')
            for _ in range(5):
                client.post('/auth/login', json={'identifier':'missing@example.invalid','password':'incorrect-password'})
            check(client.post('/auth/login',json={'identifier':'missing@example.invalid','password':'incorrect-password'}).status_code == 429, 'password guessing rate limited')
            encoded = b.store.connect()
            with encoded as db:
                check(db.execute('SELECT password_hash FROM users LIMIT 1').fetchone()[0].startswith('pbkdf2_sha256$600000$'), 'salted password hash persisted')
        report = {'mode': ('real logits bundle / validation uploads' if args.bundle else 'real original checkpoint / validation uploads') if args.real else 'CI deterministic predictor',
                  'checks_passed': len(checks), 'checks': checks, 'case_ids': case_ids,
                  'upload_to_completed_ms': request_times, 'final_test_accessed': False}
        report['bundle'] = args.bundle
        destination = Path(args.out); destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2))
        print(json.dumps({k:v for k,v in report.items() if k != 'checks'}, indent=2))

if __name__ == '__main__': main()
