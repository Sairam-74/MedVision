"""Apply the local-service security replacement while retaining result semantics.

Reads the pre-session snapshot so it is idempotent and does not touch models.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if 'from app_store import Store' in (ROOT / 'backend_service.py').read_text(encoding='utf-8'):
    raise SystemExit('Migration already applied. Refusing to overwrite subsequent security fixes.')
old = (ROOT / 'experiments/session_20261006_p6p7/source_before/backend_service.py').read_text(encoding='utf-8-sig')
helpers = old[old.index('def _severity_to_frontend_tier'):old.index('def _url_for_generated_file')]
mask = old[old.index('def _mask_from_prediction'):old.index('async def _run_prediction_job')]
prefix = '''"""Authenticated, bounded local research service; not a clinical deployment."""
from __future__ import annotations
import asyncio
import base64
import io
import logging
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from app_store import Store
from medvision_ai import create_overlay
from medvision_serving import predict as predict_versioned, ready_bundle, assert_legacy_checkpoint

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
CHECKPOINT_PATH = Path(os.environ.get('MEDVISION_CHECKPOINT', BASE_DIR / 'best_model.pt')).resolve()
BUNDLE_PATH = os.environ.get('MEDVISION_BUNDLE')
GENERATED_DIR = Path(os.environ.get('MEDVISION_GENERATED_DIR', BASE_DIR / 'generated')).resolve()
UPLOAD_DIR = GENERATED_DIR / 'uploads'
OVERLAY_DIR = GENERATED_DIR / 'overlays'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OVERLAY_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
SUPPORTED_IMAGE_TYPES = {'image/jpeg': (b'\\xff\\xd8\\xff',), 'image/png': (b'\\x89PNG\\r\\n\\x1a\\n',)}
COOKIE = 'medvision_session'
store = Store(os.environ.get('MEDVISION_DB', BASE_DIR / '.local_demo/app.sqlite3'))
demo_user = {'id': 'user-1', 'name': 'Demo Researcher', 'email': 'demo.clinician@example.invalid',
             'role': 'clinician', 'status': 'active', 'organization': 'Local Research Demo'}
store.seed_user(demo_user, os.environ.get('MEDVISION_DEMO_PASSWORD', ''))
try:
    store.import_legacy_demo(GENERATED_DIR / 'history.json', demo_user['id'])
except (ValueError, KeyError, TypeError):
    logger.exception('Legacy history could not be imported; original file preserved')
store.mark_interrupted()
inference_lock = asyncio.Lock()
upload_lock = asyncio.Lock()
jobs: dict[str, asyncio.Task] = {}
TRUSTED_ORIGINS = {f'http://{host}:{port}' for host in ('localhost', '127.0.0.1')
                   for port in (8000, 8001, 5173, 5174, 5175)}
app = FastAPI(title='MedVision local research demo', version='0.2.0', docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=sorted(TRUSTED_ORIGINS), allow_credentials=True,
                   allow_methods=['GET', 'POST', 'DELETE', 'OPTIONS'], allow_headers=['Content-Type', 'Authorization'])
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['localhost', '127.0.0.1', 'testserver'])

@app.middleware('http')
async def access_control(request: Request, call_next):
    path = request.url.path
    if request.method in ('POST', 'DELETE', 'PUT', 'PATCH'):
        origin = request.headers.get('origin')
        if origin and origin not in TRUSTED_ORIGINS:
            return JSONResponse({'detail': 'Untrusted request origin'}, status_code=403)
        if request.headers.get('sec-fetch-site') == 'cross-site':
            return JSONResponse({'detail': 'Cross-site request rejected'}, status_code=403)
    protected = path == '/ready' or path.startswith('/analyses') or path.startswith('/generated')
    if protected and request.method != 'OPTIONS':
        user = await asyncio.to_thread(store.user_for_session, request.cookies.get(COOKIE))
        if not user:
            return JSONResponse({'detail': 'Sign in required'}, status_code=401,
                                headers={'Cache-Control': 'no-store'})
        request.state.user = user
    if path.startswith('/auth/') and request.method == 'POST':
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 16384:
                return JSONResponse({'detail': 'Request body too large'}, status_code=413)
        request._body = bytes(body)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Cache-Control'] = 'no-store'
    return response

def _predict_selected(image_path: str, checkpoint_path: str):
    return predict_versioned(image_path, checkpoint_path, BUNDLE_PATH)

def _safe_upload_name(filename: str):
    stem = re.sub(r'[^a-zA-Z0-9_-]+', '-', Path(filename).stem).strip('-')[:80] or 'xray'
    suffix = Path(filename).suffix.lower()
    return stem + (suffix if suffix in ('.jpg', '.jpeg', '.png') else '.png')

def _owned(request, case_id):
    record = store.get_case(case_id, request.state.user['id'])
    if not record:
        raise HTTPException(404, 'Analysis not found')
    return record

class LoginRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=8, max_length=256)

def _session(user, response):
    token, expires = store.session(user['id'])
    # Plain HTTP is deliberately limited to loopback by the launcher. A remote
    # deployment requires TLS and Secure cookies, not a relaxed host allowlist.
    response.set_cookie(COOKIE, token, max_age=8*3600, httponly=True, samesite='strict', path='/')
    return {'user': user, 'accessToken': '', 'expiresAt': datetime.fromtimestamp(expires, timezone.utc).isoformat()}

@app.post('/auth/login')
async def login(credentials: LoginRequest, request: Request, response: Response):
    user, limited = await asyncio.to_thread(store.login, credentials.identifier.strip().lower(),
                                           credentials.password, request.client.host if request.client else 'local')
    if limited:
        raise HTTPException(429, 'Too many attempts. Wait one minute.')
    if not user:
        raise HTTPException(401, 'Invalid credentials')
    store.revoke(request.cookies.get(COOKIE))
    return _session(user, response)

@app.post('/auth/refresh')
async def refresh(request: Request, response: Response):
    token = request.cookies.get(COOKIE)
    user = store.user_for_session(token)
    if not user:
        raise HTTPException(401, 'Session expired')
    store.revoke(token)
    return _session(user, response)

@app.post('/auth/logout')
async def logout(request: Request, response: Response):
    store.revoke(request.cookies.get(COOKIE))
    response.delete_cookie(COOKIE, path='/')
    return {'message': 'Signed out'}

@app.post('/auth/signup')
@app.post('/auth/forgot-password')
@app.post('/auth/reset-password')
async def unavailable_auth():
    raise HTTPException(501, 'Account provisioning and recovery are unavailable in this local demo')

@app.get('/health')
async def health():
    return {'status': 'ok'}

@app.get('/ready')
async def ready():
    acquired = False
    try:
        await asyncio.wait_for(inference_lock.acquire(), timeout=5)
        acquired = True
        if BUNDLE_PATH:
            return await asyncio.to_thread(ready_bundle, BUNDLE_PATH)
        assert_legacy_checkpoint(CHECKPOINT_PATH)
        from medvision_ai import _cached_inference_model, DEVICE
        stat = CHECKPOINT_PATH.stat()
        _, model_hash = await asyncio.to_thread(_cached_inference_model, str(CHECKPOINT_PATH), stat.st_size, stat.st_mtime_ns)
        return {'status': 'ready', 'modelSha256': model_hash, 'device': str(DEVICE),
                'outputContract': 'sigmoid-probabilities-v1', 'researchOnly': True}
    except asyncio.TimeoutError as exc:
        raise HTTPException(503, 'Model is busy; retry shortly') from exc
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        logger.exception('Readiness check failed')
        raise HTTPException(503, 'Model checkpoint or bundle unavailable or invalid') from exc
    finally:
        if acquired:
            inference_lock.release()
'''
suffix = '''
async def _run_prediction_job(case, owner):
    acquired = False
    result = None
    error = None
    try:
        await asyncio.wait_for(inference_lock.acquire(), timeout=30)
        acquired = True
        case['status'] = 'processing'
        store.save_case(case, owner)
        task = asyncio.create_task(asyncio.to_thread(_predict_selected, str(case['imagePath']), str(CHECKPOINT_PATH)))
        try:
            prediction = await asyncio.wait_for(asyncio.shield(task), timeout=60)
        except asyncio.TimeoutError:
            case['status'] = 'timed_out'
            error = 'Prediction exceeded the time limit. Retry after the service becomes available.'
            store.save_case(case, owner, error=error)
            # Python cannot cancel a running native inference thread. Retain
            # the lock until it exits so a timeout cannot cause overlapping work.
            await task
            return
        binary_mask = _mask_from_prediction(prediction)
        if binary_mask is not None:
            await asyncio.to_thread(create_overlay, str(case['imagePath']), binary_mask, str(case['overlayPath']), 'prediction')
        else:
            raise ValueError('Model returned no decodable mask')
        result = _result_from_prediction(case['id'], prediction, case['originalImageUrl'], case['overlayUrl'])
        case['status'] = 'completed'
    except asyncio.TimeoutError:
        case['status'] = 'timed_out'
        error = 'The inference queue was busy for too long. Please retry.'
    except Exception:
        logger.exception('Prediction failed for %s', case['id'])
        case['status'] = 'failed'
        error = 'Prediction failed. Please try again.'
    finally:
        if acquired:
            inference_lock.release()
        store.save_case(case, owner, result, error)

def _decode_image(image_bytes):
    try:
        with Image.open(io.BytesIO(image_bytes)) as header:
            width, height = header.size
            if max(width, height) > 8192 or width * height > 25_000_000:
                raise HTTPException(413, 'Image dimensions exceed the supported limit')
            if getattr(header, 'n_frames', 1) != 1:
                raise HTTPException(415, 'Animated images are unsupported')
            header.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise HTTPException(422, 'Image could not be decoded') from exc
    decoded = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    if decoded is None:
        raise HTTPException(422, 'Image could not be decoded')
    if max(decoded.shape) > 8192 or decoded.size > 25_000_000:
        raise HTTPException(413, 'Image dimensions exceed the supported limit')

@app.post('/analyses')
async def create_analysis(request: Request):
    owner = request.state.user['id']
    if len(jobs) >= 8:
        raise HTTPException(429, 'Prediction queue full; retry shortly')
    owned_cases = store.list_cases(owner)
    if sum(c['status'] in ('queued', 'processing') for c in owned_cases) >= 2:
        raise HTTPException(429, 'Two analyses are already in progress')
    if len(owned_cases) >= 100:
        raise HTTPException(409, 'History limit reached. Delete completed analyses to free space.')
    if upload_lock.locked():
        raise HTTPException(429, 'Another image upload is being checked; retry shortly')
    async with upload_lock:
        content_length = request.headers.get('content-length', '')
        if content_length.isdigit() and int(content_length) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, 'Upload request is too large (10 MB limit)')
        chunks = bytearray()
        async for chunk in request.stream():
            chunks.extend(chunk)
            if len(chunks) > MAX_UPLOAD_BYTES:
                raise HTTPException(413, 'Upload request is too large (10 MB limit)')
        if not request.headers.get('content-type', '').lower().startswith('multipart/form-data'):
            raise HTTPException(415, 'Multipart image upload required')
        from starlette.formparsers import MultiPartParser
        async def body_stream():
            yield bytes(chunks)
        try:
            form = await MultiPartParser(request.headers, body_stream(), max_files=1, max_fields=5).parse()
            try:
                upload = form.get('image')
                if upload is None or not hasattr(upload, 'read'):
                    raise HTTPException(400, 'Image file field was missing')
                filename = Path(upload.filename or 'xray.png').name[:255]
                image_bytes = await upload.read()
                signatures = SUPPORTED_IMAGE_TYPES.get(upload.content_type)
                if signatures is None or not any(image_bytes.startswith(s) for s in signatures):
                    raise HTTPException(415, 'Only valid JPEG and PNG images are supported')
            finally:
                await form.close()
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(400, 'Invalid multipart upload') from exc
        await asyncio.to_thread(_decode_image, image_bytes)
        # Recheck after awaiting decode, before reserving the job slot.
        owned_cases = store.list_cases(owner)
        if len(jobs) >= 8 or sum(c['status'] in ('queued', 'processing') for c in owned_cases) >= 2:
            raise HTTPException(429, 'Prediction queue full; retry shortly')
        if len(owned_cases) >= 100:
            raise HTTPException(409, 'History limit reached')
        case_id = 'ana-' + uuid.uuid4().hex
        image_path = UPLOAD_DIR / f'{case_id}-{_safe_upload_name(filename)}'
        overlay_path = OVERLAY_DIR / f'{case_id}-segmented.png'
        image_path.write_bytes(image_bytes)
        case = {'id': case_id, 'uploader': request.state.user['name'], 'uploadedBy': request.state.user['role'],
                'createdAt': datetime.now(timezone.utc).isoformat(), 'status': 'queued', 'fileName': filename,
                'imagePath': str(image_path), 'overlayPath': str(overlay_path),
                'originalImageUrl': '/generated/uploads/' + image_path.name,
                'overlayUrl': '/generated/overlays/' + overlay_path.name}
        store.save_case(case, owner)
        task = asyncio.create_task(_run_prediction_job(case, owner))
        jobs[case_id] = task
        task.add_done_callback(lambda _: jobs.pop(case_id, None))
        return {'analysisId': case_id, 'status': 'queued', 'message': 'Analysis queued.'}

@app.get('/analyses')
async def list_analyses(request: Request):
    return [_public_analysis(c) for c in store.list_cases(request.state.user['id'])]

@app.get('/analyses/{analysis_id}/status')
async def get_analysis_status(analysis_id: str, request: Request):
    case, result, error = _owned(request, analysis_id)
    return {'analysisId': analysis_id, 'status': case['status'],
            'progress': 100 if case['status'] == 'completed' else 70 if case['status'] == 'processing' else 25,
            'result': result if case['status'] == 'completed' else None, 'errorMessage': error}

@app.get('/analyses/{analysis_id}')
@app.get('/analyses/{analysis_id}/export')
async def get_analysis_result(analysis_id: str, request: Request):
    _, result, _ = _owned(request, analysis_id)
    if not result:
        raise HTTPException(404, 'Result not available')
    return result

@app.delete('/analyses/{analysis_id}')
async def delete_analysis(analysis_id: str, request: Request):
    case, _, _ = _owned(request, analysis_id)
    if analysis_id in jobs:
        raise HTTPException(409, 'An active analysis cannot be deleted')
    for key, directory in [('imagePath', UPLOAD_DIR), ('overlayPath', OVERLAY_DIR)]:
        path = Path(case.get(key, '')).resolve()
        # Delete only service-managed files belonging to this UUID case.
        if path.parent == directory.resolve() and path.name.startswith(analysis_id + '-'):
            path.unlink(missing_ok=True)
    store.delete_case(analysis_id, request.state.user['id'])
    return {'message': 'Analysis deleted'}

@app.get('/generated/{relative_path:path}')
async def owned_image(relative_path: str, request: Request):
    path = (GENERATED_DIR / relative_path).resolve()
    if path.parent not in (UPLOAD_DIR.resolve(), OVERLAY_DIR.resolve()) or not path.is_file():
        raise HTTPException(404, 'Image not found')
    case_id = path.name.split('-', 2)
    if len(case_id) < 3 or case_id[0] != 'ana':
        raise HTTPException(404, 'Image not found')
    case, _, _ = _owned(request, '-'.join(case_id[:2]))
    allowed = {Path(case.get(key, '')).resolve() for key in ('imagePath', 'overlayPath')}
    if path not in allowed:
        raise HTTPException(404, 'Image not found')
    return FileResponse(path)

# No general filesystem mount; only build assets are public.
DIST_DIR = BASE_DIR / 'dist'
if (DIST_DIR / 'assets').is_dir():
    app.mount('/assets', StaticFiles(directory=DIST_DIR / 'assets'), name='frontend-assets')

@app.get('/')
@app.get('/login')
@app.get('/dashboard')
@app.get('/upload')
@app.get('/history')
@app.get('/profile')
@app.get('/session-expired')
@app.get('/access-denied')
@app.get('/results/{analysis_id}')
async def frontend(analysis_id: str = ''):
    index = DIST_DIR / 'index.html'
    if not index.is_file():
        raise HTTPException(503, 'Build the frontend with npm run build first')
    return FileResponse(index)
'''
(ROOT / 'backend_service.py').write_text(prefix + '\n' + helpers + mask + suffix, encoding='utf-8')
