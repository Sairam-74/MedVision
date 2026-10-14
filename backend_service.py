"""Authenticated, bounded local research service; not a clinical deployment."""
from __future__ import annotations
import asyncio
import base64
import io
import logging
import os
import re
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import ipaddress
import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app_store import Store
from research_status import snapshot as research_snapshot
from medvision_ai import create_overlay
from medvision_serving import predict as predict_versioned, ready_bundle, assert_legacy_checkpoint

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
CHECKPOINT_PATH = Path(os.environ.get('MEDVISION_CHECKPOINT', BASE_DIR / 'best_model.pt')).resolve()
BUNDLE_PATH = os.environ.get('MEDVISION_BUNDLE')
GENERATED_DIR = Path(os.environ.get('MEDVISION_GENERATED_DIR', BASE_DIR / 'generated')).resolve()
ORIGINAL_PROJECT_DIR = (BASE_DIR.parent / 'MedVision').resolve()
for selected_path in (GENERATED_DIR, Path(os.environ.get('MEDVISION_DB', BASE_DIR / '.local_demo/app.sqlite3')).resolve(), CHECKPOINT_PATH):
    if BASE_DIR != ORIGINAL_PROJECT_DIR and (selected_path == ORIGINAL_PROJECT_DIR or ORIGINAL_PROJECT_DIR in selected_path.parents):
        raise RuntimeError('Feature environment must not point to original project storage or model files')
if BASE_DIR != ORIGINAL_PROJECT_DIR and BUNDLE_PATH and ORIGINAL_PROJECT_DIR in Path(BUNDLE_PATH).resolve().parents:
    raise RuntimeError('Copy the immutable model bundle into this independent clone')
UPLOAD_DIR = GENERATED_DIR / 'uploads'
OVERLAY_DIR = GENERATED_DIR / 'overlays'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OVERLAY_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_REQUEST_BYTES = MAX_UPLOAD_BYTES + 64 * 1024  # Multipart headers/fields are separate from the image limit.
SUPPORTED_IMAGE_TYPES = {'image/jpeg': (b'\xff\xd8\xff',), 'image/png': (b'\x89PNG\r\n\x1a\n',)}
COOKIE = 'medvision_feature_session'
store = Store(os.environ.get('MEDVISION_DB', BASE_DIR / '.local_demo/app.sqlite3'))
demo_user = {'id': 'user-1', 'name': 'Demo Researcher', 'email': 'demo.clinician@example.invalid',
             'role': 'clinician', 'status': 'active', 'organization': 'Local Research Demo'}
store.seed_user(demo_user, os.environ.get('MEDVISION_DEMO_PASSWORD', ''))
store.seed_recovery(demo_user['id'], os.environ.get('MEDVISION_DEMO_RECOVERY_CODE', ''))
try:
    store.import_legacy_demo(GENERATED_DIR / 'history.json', demo_user['id'])
except (ValueError, KeyError, TypeError):
    logger.exception('Legacy history could not be imported; original file preserved')
store.mark_interrupted()
inference_lock = asyncio.Lock()
upload_lock = asyncio.Lock()
jobs: dict[str, asyncio.Task] = {}
INFERENCE_TIMEOUT = 60
QUEUE_TIMEOUT = 30
STORAGE_LIMIT_BYTES = 512 * 1024 * 1024
CASE_RESERVATION_BYTES = MAX_UPLOAD_BYTES + 3 * 25_000_000 + 1024 * 1024
TRUSTED_ORIGINS = {f'http://{host}:{port}' for host in ('localhost', '127.0.0.1')
                   for port in (8000, 8001, 5173, 5174, 5175)}
app = FastAPI(title='MedVision local research demo', version='0.2.0', docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=sorted(TRUSTED_ORIGINS), allow_credentials=True,
                   allow_methods=['GET', 'POST', 'DELETE', 'OPTIONS'], allow_headers=['Content-Type', 'Authorization'])
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['localhost', '127.0.0.1', 'testserver'])

async def _bounded_body(request, limit):
    try:
        async with asyncio.timeout(15):
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > limit:
                    raise HTTPException(413, 'Request body too large')
            return bytes(body)
    except asyncio.TimeoutError as exc:
        raise HTTPException(408, 'Upload took too long; retry') from exc

def _check_storage(cases):
    used = 0
    for case in cases:
        for key in ('imagePath', 'overlayPath'):
            path = Path(case.get(key, '')).resolve()
            if path.parent in (UPLOAD_DIR.resolve(), OVERLAY_DIR.resolve()) and path.is_file():
                used += path.stat().st_size
    active = sum(c['status'] in ('queued', 'processing') for c in cases)
    if used + (active + 1) * CASE_RESERVATION_BYTES > STORAGE_LIMIT_BYTES:
        raise HTTPException(409, 'Local storage limit reached. Delete completed analyses to free space.')
    if shutil.disk_usage(GENERATED_DIR).free < CASE_RESERVATION_BYTES:
        raise HTTPException(503, 'Insufficient local storage for an analysis')

@app.middleware('http')
async def access_control(request: Request, call_next):
    path = request.url.path
    if request.method in ('POST', 'DELETE', 'PUT', 'PATCH'):
        origin = request.headers.get('origin')
        if origin and origin not in TRUSTED_ORIGINS:
            return JSONResponse({'detail': 'Untrusted request origin'}, status_code=403)
        if request.headers.get('sec-fetch-site') == 'cross-site':
            return JSONResponse({'detail': 'Cross-site request rejected'}, status_code=403)
    protected = path in ('/ready', '/api/research') or path.startswith(('/analyses', '/generated', '/patients', '/studies', '/reports', '/models', '/retraining', '/feedback'))
    if protected and request.method != 'OPTIONS':
        user = await asyncio.to_thread(store.user_for_session, request.cookies.get(COOKIE))
        if not user:
            return JSONResponse({'detail': 'Sign in required'}, status_code=401,
                                headers={'Cache-Control': 'no-store'})
        request.state.user = user
    if (path.startswith('/analyses/') and path.endswith('/feedback') or path.startswith('/auth/') or path.startswith(('/patients','/studies','/reports','/models','/retraining','/feedback')) and not path.endswith(('/images','/mask')))  and request.method == 'POST':
        try:
            request._body = await _bounded_body(request, 16384 if path.startswith('/auth/') else 65536)
        except HTTPException as exc:
            return JSONResponse({'detail': exc.detail}, status_code=exc.status_code)
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
    case, result, error = record
    if result:
        result = dict(result)
        # Legacy history stored absolute 127.0.0.1 URLs, which do not receive
        # localhost's Strict cookie. Derive owned URLs from the saved paths;
        # never trust a persisted Host header or expose an arbitrary file.
        for key, fields, directory in [('imagePath', ('imageUrl', 'originalImageUrl'), UPLOAD_DIR),
                                       ('overlayPath', ('overlayUrl',), OVERLAY_DIR)]:
            path = Path(case.get(key, '')).resolve()
            url = '/generated/' + path.relative_to(GENERATED_DIR).as_posix() if path.parent == directory.resolve() and path.name.startswith(case_id + '-') else None
            for field in fields:
                result[field] = url
        result['disclaimer'] = 'Research prototype. Highlighted regions and geometry tiers are not a diagnosis or clinically validated severity assessment.'
    return case, result, error

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

class SignupRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=256)

    @field_validator('email')
    @classmethod
    def email_valid(cls, value):
        value = value.strip().lower()
        if not re.fullmatch(r'[A-Za-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+', value):
            raise ValueError('Enter a valid email')
        return value

    @field_validator('name')
    @classmethod
    def name_valid(cls, value):
        value = value.strip()
        if len(value) < 2 or any(ord(c) < 32 for c in value):
            raise ValueError('Enter your name')
        return value

class RecoveryRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    recoveryCode: str = Field(min_length=20, max_length=128)

class ResetRequest(BaseModel):
    token: str = Field(min_length=20, max_length=128)
    password: str = Field(min_length=12, max_length=256)

def _auth_limit(request, scope, limit=5, window=60):
    if not store.allow_auth_attempt(scope, request.client.host if request.client else 'local', limit, window):
        raise HTTPException(429, 'Too many attempts. Wait before trying again.')

@app.get('/auth/demo-credentials')
async def demo_credentials(request: Request):
    if request.headers.get('origin') and request.headers['origin'] not in TRUSTED_ORIGINS:
        raise HTTPException(403, 'Untrusted request origin')
    if request.headers.get('sec-fetch-site') == 'cross-site':
        raise HTTPException(403, 'Cross-site request rejected')
    try:
        local = bool(request.client and ipaddress.ip_address(request.client.host).is_loopback)
    except ValueError:
        local = False
    password = os.environ.get('MEDVISION_DEMO_PASSWORD', '')
    enabled = os.environ.get('MEDVISION_DEMO_PREFILL') == '1' and local
    if enabled:
        _auth_limit(request, 'demo-prefill', 30)
    if not enabled or not await asyncio.to_thread(store.credentials_match, demo_user['email'], password):
        return {'enabled': False}
    return {'enabled': True, 'email': demo_user['email'], 'password': password}

@app.post('/auth/signup', status_code=201)
async def signup_account(credentials: SignupRequest, request: Request):
    _auth_limit(request, 'signup', 10, 600)
    try:
        _, code = await asyncio.to_thread(store.create_user, credentials.name, credentials.email, credentials.password)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {'message': 'Account created. Save your recovery code before signing in.', 'recoveryCode': code}

@app.post('/auth/forgot-password')
async def recover_account(credentials: RecoveryRequest, request: Request):
    _auth_limit(request, 'recovery')
    token = await asyncio.to_thread(store.recovery_grant, credentials.email.strip().lower(), credentials.recoveryCode.strip())
    if not token:
        raise HTTPException(400, 'Email or recovery code is incorrect')
    return {'message': 'Recovery verified. Choose a new password within 10 minutes.', 'resetUrl': '/reset-password#token=' + token}

@app.post('/auth/reset-password')
async def reset_account(credentials: ResetRequest, request: Request, response: Response):
    _auth_limit(request, 'reset', 10)
    changed = await asyncio.to_thread(store.reset_password, credentials.token, credentials.password)
    if not changed:
        raise HTTPException(400, 'Reset link is expired or already used. Start account recovery again.')
    response.delete_cookie(COOKIE, path='/')
    # Only the explicitly shared local demo account has an on-disk prefill.
    # Other accounts and their recovery codes are never saved in plaintext.
    if changed[0] == demo_user['id'] and os.environ.get('MEDVISION_DEMO_PREFILL') == '1':
        private = BASE_DIR / '.local_demo'
        private.mkdir(exist_ok=True)
        (private / 'demo_password.txt').write_text(credentials.password, encoding='utf-8')
        (private / 'demo_recovery_code.txt').write_text(changed[1], encoding='utf-8')
        os.environ['MEDVISION_DEMO_PASSWORD'] = credentials.password
        os.environ['MEDVISION_DEMO_RECOVERY_CODE'] = changed[1]
    return {'message': 'Password updated. Existing sessions were signed out.', 'recoveryCode': changed[1]}

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

def _severity_to_frontend_tier(severity: str) -> str:
    normalized = severity.lower()
    if normalized == "not applicable":
        return "not_applicable"
    if normalized == "mild":
        return "low"
    if normalized == "severe":
        return "high"
    return "moderate"


def _result_from_prediction(
    analysis_id: str,
    prediction: dict[str, Any],
    original_image_url: str = "/mock_xray.png",
    overlay_url: str = "/segmentation_overlay_prediction.png",
) -> dict[str, Any]:
    features = prediction.get("severity_features", {})
    area = float(features.get("area", 0.0))
    fracture_status = "fracture" if prediction.get("mask_present", area > 0) else "no_fracture"
    severity_tier = str(prediction.get("severity_tier", "Not applicable"))
    return {
        "id": f"res-{analysis_id}",
        "analysisId": analysis_id,
        "fractureStatus": fracture_status,
        "fracturePresence": "Positive segmentation signal — radiologist review required" if fracture_status == "fracture" else "Negative segmentation signal — fracture not excluded",
        "bone": "Feature not supported by the current model",
        "location": "Not determined",
        "fractureType": "Feature not supported by the current model",
        "displacement": "Feature not supported by the current model",
        "angulation": "Feature not supported by the current model",
        "confidence": None,
        "severity": "not_applicable",
        "region": "Uploaded X-ray",
        "type": "AI segmentation finding" if fracture_status == "fracture" else "No predicted region",
        "recommendation": "Research output only. Compare with the original image; do not use for clinical decisions.",
        "imageUrl": original_image_url,
        "originalImageUrl": original_image_url,
        "overlayUrl": overlay_url,
        "maskPngBase64": prediction.get("mask_png_base64"),
        "maskShape": prediction.get("mask_shape", [256, 256]),
        "calibratedThreshold": prediction.get("calibrated_threshold", 0.5),
        "modelSha256": prediction.get("model_sha256"),
        "bundleSha256": prediction.get("bundle_sha256"),
        "outputContract": prediction.get("output_contract", "sigmoid-probabilities-v1"),
        "preprocessing": prediction.get("preprocessing"),
        "geometryTransform": prediction.get("geometry_transform"),
        "rawMaskPngBase64": prediction.get("raw_mask_png_base64"),
        "postprocessing": prediction.get("postprocessing"),
        "thresholdProvenance": prediction.get("threshold_provenance"),
        "geometryUnits": prediction.get("geometry_units"),
        "severityFeatures": {
            "area": area,
            "perimeter": float(features.get("perimeter", 0.0)),
            "compactness": float(features.get("compactness", 0.0)),
            "aspectRatio": float(features.get("aspect_ratio", 0.0)),
            "componentCount": int(features.get("component_count", 0)),
        },
        "metrics": {
            "dice": None,
            "iou": None,
        },
        "disclaimer": "Research prototype. Highlighted regions and geometry tiers are not a diagnosis or clinically validated severity assessment.",
    }


def _mask_from_prediction(prediction: dict[str, Any]) -> np.ndarray | None:
    mask_b64 = prediction.get("mask_png_base64")
    if not mask_b64:
        return None

    mask_bytes = base64.b64decode(mask_b64)
    encoded = np.frombuffer(mask_bytes, dtype=np.uint8)
    decoded = cv2.imdecode(encoded, cv2.IMREAD_GRAYSCALE)
    if decoded is None:
        return None
    return (decoded > 0).astype(np.uint8)


def _public_analysis(analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in analysis.items()
        if key not in {"imagePath", "overlayPath", "originalImageUrl", "overlayUrl"}
    }



async def _run_prediction_job(case, owner):
    acquired = False
    result = None
    error = None
    try:
        await asyncio.wait_for(inference_lock.acquire(), timeout=QUEUE_TIMEOUT)
        acquired = True
        case['status'] = 'processing'
        case['analysisStartedAt'] = datetime.now(timezone.utc).isoformat()
        store.save_case(case, owner)
        task = asyncio.create_task(asyncio.to_thread(_predict_selected, str(case['imagePath']), str(CHECKPOINT_PATH)))
        try:
            prediction = await asyncio.wait_for(asyncio.shield(task), timeout=INFERENCE_TIMEOUT)
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
            original = cv2.imread(str(case['imagePath']), cv2.IMREAD_GRAYSCALE)
            if original is None or binary_mask.shape != original.shape:
                raise ValueError('Model mask is not aligned to the native image')
            await asyncio.to_thread(create_overlay, str(case['imagePath']), binary_mask, str(case['overlayPath']), 'prediction')
        else:
            raise ValueError('Model returned no decodable mask')
        prediction = dict(prediction, mask_present=bool(binary_mask.any()))
        result = _result_from_prediction(case['id'], prediction, case['originalImageUrl'], case['overlayUrl'])
        result['severityFeatures']['componentCount'] = int(cv2.connectedComponents(binary_mask.astype(np.uint8), 8)[0] - 1)
        case['status'] = 'completed'
        case['analysisCompletedAt'] = datetime.now(timezone.utc).isoformat()
        result['analysisCompletedAt'] = case['analysisCompletedAt']
        result['modelVersion'] = workflow_current_version()
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
        with Image.open(io.BytesIO(image_bytes), formats=['JPEG', 'PNG']) as header:
            width, height = header.size
            if max(width, height) > 8192 or width * height > 25_000_000:
                raise HTTPException(413, 'Image dimensions exceed the supported limit')
            if getattr(header, 'n_frames', 1) != 1:
                raise HTTPException(415, 'Animated images are unsupported')
            header.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, ValueError, SyntaxError) as exc:
        raise HTTPException(422, 'Image could not be decoded') from exc
    try:
        decoded = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    except cv2.error as exc:
        raise HTTPException(422, 'Image could not be decoded') from exc
    if decoded is None:
        raise HTTPException(422, 'Image could not be decoded')
    if max(decoded.shape) > 8192 or decoded.size > 25_000_000:
        raise HTTPException(413, 'Image dimensions exceed the supported limit')

@app.post('/studies/{study_id}/images')
@app.post('/analyses')
async def create_analysis(request: Request, study_id: str | None = None):
    if study_id and not workflow.study(request.state.user["id"], study_id):
        raise HTTPException(404, "Study not found")
    if study_id:
        report=workflow.report(request.state.user['id'],study_id)
        if report and report['status']=='final':raise HTTPException(409,'Reopen the report before adding a study view')
    view_type = None
    owner = request.state.user['id']
    if len(jobs) >= 8:
        raise HTTPException(429, 'Prediction queue full; retry shortly')
    owned_cases = store.list_cases(owner)
    _check_storage(owned_cases)
    if sum(c['status'] in ('queued', 'processing') for c in owned_cases) >= 2:
        raise HTTPException(429, 'Two analyses are already in progress')
    if len(owned_cases) >= 100:
        raise HTTPException(409, 'History limit reached. Delete completed analyses to free space.')
    if upload_lock.locked():
        raise HTTPException(429, 'Another image upload is being checked; retry shortly')
    async with upload_lock:
        content_length = request.headers.get('content-length', '')
        if content_length.isdigit() and int(content_length) > MAX_REQUEST_BYTES:
            raise HTTPException(413, 'Upload request is too large (10 MB limit)')
        body = await _bounded_body(request, MAX_REQUEST_BYTES)
        if not request.headers.get('content-type', '').lower().startswith('multipart/form-data'):
            raise HTTPException(415, 'Multipart image upload required')
        from starlette.formparsers import MultiPartParser
        async def body_stream():
            yield body
        try:
            form = await MultiPartParser(request.headers, body_stream(), max_files=1, max_fields=5).parse()
            try:
                upload = form.get('image')
                if upload is None or not hasattr(upload, 'read'):
                    raise HTTPException(400, 'Image file field was missing')
                filename = Path(upload.filename or 'xray.png').name[:255]
                if study_id:
                    view_type = form.get('view_type')
                    if view_type not in ('AP', 'Lateral', 'Oblique'):
                        raise HTTPException(422, 'Select AP, Lateral or Oblique')
                image_bytes = await upload.read()
                if len(image_bytes) > MAX_UPLOAD_BYTES:
                    raise HTTPException(413, 'Image is too large (10 MB limit)')
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
        _check_storage(owned_cases)
        if len(jobs) >= 8 or sum(c['status'] in ('queued', 'processing') for c in owned_cases) >= 2:
            raise HTTPException(429, 'Prediction queue full; retry shortly')
        if len(owned_cases) >= 100:
            raise HTTPException(409, 'History limit reached')
        case_id = 'ana-' + uuid.uuid4().hex
        image_path = UPLOAD_DIR / f'{case_id}-xray'
        image_path = image_path.with_suffix('.png' if upload.content_type == 'image/png' else '.jpg')
        overlay_path = OVERLAY_DIR / f'{case_id}-segmented.png'
        image_path.write_bytes(image_bytes)
        case = {'id': case_id, 'uploader': request.state.user['name'], 'uploadedBy': request.state.user['role'],
                'createdAt': datetime.now(timezone.utc).isoformat(), 'status': 'queued', 'fileName': filename,
                'imagePath': str(image_path), 'overlayPath': str(overlay_path),
                'originalImageUrl': '/generated/uploads/' + image_path.name,
                'overlayUrl': '/generated/overlays/' + overlay_path.name}
        if study_id:
            case.update(studyId=study_id, viewType=view_type)
        store.save_case(case, owner)
        if study_id:
            workflow.attach(owner, study_id, case_id, view_type)
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
    with store.connect() as db:
        if db.execute('SELECT 1 FROM study_images WHERE analysis_id=?', (analysis_id,)).fetchone() or db.execute('SELECT 1 FROM feedback WHERE analysis_id=?', (analysis_id,)).fetchone():
            raise HTTPException(409, 'Study or feedback analysis must be retained for audit history')
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
@app.get('/api/research')
async def research_evidence():
    return await asyncio.to_thread(research_snapshot, BASE_DIR, BUNDLE_PATH)

DIST_DIR = BASE_DIR / 'dist'
if (DIST_DIR / 'assets').is_dir():
    app.mount('/assets', StaticFiles(directory=DIST_DIR / 'assets'), name='frontend-assets')

from workflow_api import install
workflow, workflow_current_version = install(app, store, globals())

@app.get('/')
@app.get('/login')
@app.get('/signup')
@app.get('/forgot-password')
@app.get('/reset-password')
@app.get('/dashboard')
@app.get('/upload')
@app.get('/history')
@app.get('/profile')
@app.get('/research')
@app.get('/session-expired')
@app.get('/access-denied')
@app.get('/studies/{analysis_id}')
@app.get('/results/{analysis_id}')
async def frontend(analysis_id: str = ''):
    index = DIST_DIR / 'index.html'
    if not index.is_file():
        raise HTTPException(503, 'Build the frontend with npm run build first')
    return FileResponse(index)
