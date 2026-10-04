"""Minimal MedVision backend API for local frontend integration.

This server is intentionally small: it provides the web-facing API contract and
keeps the PyTorch prediction runtime server-side. Install python-multipart later
to parse and persist real browser multipart uploads; until then, uploaded jobs
run against the local demo X-ray so the end-to-end UI can exercise a real model
call instead of browser-only mock data.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from medvision_ai import create_overlay, predict_from_checkpoint


logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
CHECKPOINT_PATH = BASE_DIR / "best_model.pt"
DEMO_IMAGE_PATH = BASE_DIR / "medvision_temp" / "IMG0000019.jpg"
if not DEMO_IMAGE_PATH.exists():
    DEMO_IMAGE_PATH = BASE_DIR / "mock_xray.png"
GENERATED_DIR = BASE_DIR / "generated"
UPLOAD_DIR = GENERATED_DIR / "uploads"
OVERLAY_DIR = GENERATED_DIR / "overlays"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OVERLAY_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
SUPPORTED_IMAGE_TYPES = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
}

app = FastAPI(title="MedVision AI Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.mount("/generated", StaticFiles(directory=GENERATED_DIR), name="generated")


mock_user = {
    "id": "user-1",
    "name": "Demo Clinician",
    "email": "demo.clinician@example.invalid",
    "role": "clinician",
    "status": "active",
    "organization": "Demo Imaging Organization",
}
users_by_email: dict[str, dict[str, Any]] = {
    mock_user["email"]: {
        "user": mock_user,
        "password": os.environ.get("MEDVISION_DEMO_PASSWORD", ""),
    }
}

LOCAL_ACCESS_TOKEN = os.environ.get("MEDVISION_LOCAL_ACCESS_TOKEN", "")


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=1)
    password: str = Field(min_length=8)
    otp: str | None = None


class SignupRequest(BaseModel):
    name: str = Field(min_length=2)
    email: str = Field(min_length=3)
    password: str = Field(min_length=8)

analyses: list[dict[str, Any]] = [
    {
        "id": "ana-demo",
        "uploader": mock_user["name"],
        "createdAt": "2026-08-20T00:00:00.000Z",
        "status": "completed",
        "fileName": DEMO_IMAGE_PATH.name,
        "uploadedBy": mock_user["role"],
    }
]
results: dict[str, dict[str, Any]] = {}
job_errors: dict[str, str] = {}


def _severity_to_frontend_tier(severity: str) -> str:
    normalized = severity.lower()
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
    fracture_status = "fracture" if area > 0 else "no_fracture"
    severity_tier = str(prediction.get("severity_tier", "Mild"))
    return {
        "id": f"res-{analysis_id}",
        "analysisId": analysis_id,
        "fractureStatus": fracture_status,
        "severity": _severity_to_frontend_tier(severity_tier),
        "confidence": 0.86 if fracture_status == "fracture" else 0.74,
        "region": "Uploaded X-ray",
        "type": "AI segmentation finding" if fracture_status == "fracture" else "No connected fracture mask detected",
        "recommendation": "Review highlighted evidence before clinical use.",
        "imageUrl": original_image_url,
        "originalImageUrl": original_image_url,
        "overlayUrl": overlay_url,
        "maskPngBase64": prediction.get("mask_png_base64"),
        "maskShape": prediction.get("mask_shape", [256, 256]),
        "calibratedThreshold": prediction.get("calibrated_threshold", 0.5),
        "severityFeatures": {
            "area": area,
            "perimeter": float(features.get("perimeter", 0.0)),
            "compactness": float(features.get("compactness", 0.0)),
            "aspectRatio": float(features.get("aspect_ratio", 0.0)),
        },
        "metrics": {
            "dice": None,
            "iou": None,
        },
        "disclaimer": "AI-assisted result - requires clinician review before clinical use.",
    }


def _url_for_generated_file(request: Request, path: Path) -> str:
    relative_path = path.relative_to(GENERATED_DIR).as_posix()
    return f"{str(request.base_url).rstrip('/')}/generated/{relative_path}"


def _safe_upload_name(filename: str) -> str:
    stem = Path(filename).stem or "uploaded-xray"
    suffix = Path(filename).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png"}:
        suffix = ".png"
    safe_stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", stem).strip("-") or "uploaded-xray"
    return f"{safe_stem[:80]}{suffix}"


def _extract_uploaded_image(body: bytes, content_type: str) -> tuple[str, bytes]:
    boundary_match = re.search(r'boundary="?([^";]+)"?', content_type)
    if not boundary_match:
        raise HTTPException(status_code=400, detail="Multipart boundary missing")

    boundary = ("--" + boundary_match.group(1)).encode("utf-8")
    for part in body.split(boundary):
        if b'name="image"' not in part or b"\r\n\r\n" not in part:
            continue

        header_bytes, file_bytes = part.split(b"\r\n\r\n", 1)
        if file_bytes.endswith(b"\r\n"):
            file_bytes = file_bytes[:-2]
        content_type_match = re.search(rb"(?:^|\r\n)Content-Type:\s*([^\r\n]+)", header_bytes, re.IGNORECASE)
        uploaded_content_type = content_type_match.group(1).decode("ascii", errors="ignore").strip().lower() if content_type_match else ""
        signatures = SUPPORTED_IMAGE_TYPES.get(uploaded_content_type)
        if signatures is None or not any(file_bytes.startswith(signature) for signature in signatures):
            raise HTTPException(status_code=415, detail="Only valid JPEG and PNG images are supported")
        disposition = header_bytes.decode("utf-8", errors="ignore")
        filename_match = re.search(r'filename="([^"]+)"', disposition)
        filename = filename_match.group(1) if filename_match else "uploaded-xray.png"
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded image was empty")
        return filename, file_bytes

    raise HTTPException(status_code=400, detail="Image file field was missing")


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


async def _run_prediction_job(analysis_id: str) -> None:
    analysis = next((item for item in analyses if item["id"] == analysis_id), None)
    if analysis is None:
        return

    analysis["status"] = "processing"
    image_path = Path(analysis.get("imagePath", DEMO_IMAGE_PATH))
    overlay_url = str(analysis.get("overlayUrl", "/segmentation_overlay_prediction.png"))
    try:
        prediction = await asyncio.to_thread(
            predict_from_checkpoint,
            str(image_path),
            str(CHECKPOINT_PATH),
        )
        overlay_path = analysis.get("overlayPath")
        binary_mask = _mask_from_prediction(prediction)
        if overlay_path and binary_mask is not None:
            await asyncio.to_thread(create_overlay, str(image_path), binary_mask, str(overlay_path), "prediction")

        results[analysis_id] = _result_from_prediction(
            analysis_id,
            prediction,
            original_image_url=str(analysis.get("originalImageUrl", "/mock_xray.png")),
            overlay_url=overlay_url,
        )
        analysis["status"] = "completed"
    except Exception:  # pragma: no cover - defensive for local service
        logger.exception("Prediction job failed for analysis %s", analysis_id)
        job_errors[analysis_id] = "Prediction failed. Please try again."
        analysis["status"] = "failed"


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def _session_for_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "user": user,
        "accessToken": LOCAL_ACCESS_TOKEN,
        "expiresAt": (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat().replace("+00:00", "Z"),
    }


@app.post("/auth/login")
async def login(request: LoginRequest) -> dict[str, Any]:
    account = users_by_email.get(request.identifier.strip().lower())
    if account is None or account["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return _session_for_user(account["user"])


@app.post("/auth/refresh")
async def refresh() -> dict[str, Any]:
    return _session_for_user(mock_user)


def _slugify_user_id(email: str) -> str:
    safe = "".join(char.lower() if char.isalnum() else "-" for char in email)
    return "user-" + "-".join(part for part in safe.split("-") if part)


@app.post("/auth/signup")
async def signup(request: SignupRequest) -> dict[str, str]:
    email = request.email.strip().lower()
    if email in users_by_email:
        raise HTTPException(status_code=409, detail="An account already exists for this email")

    users_by_email[email] = {
        "user": {
            "id": _slugify_user_id(email),
            "name": request.name.strip(),
            "email": email,
            "role": "clinician",
            "status": "active",
            "organization": "Demo Organization",
        },
        "password": request.password,
    }
    return {"message": "Account created successfully."}


@app.post("/auth/forgot-password")
async def forgot_password() -> dict[str, str]:
    return {"message": "Password reset email sent."}


@app.post("/auth/reset-password")
async def reset_password() -> dict[str, str]:
    return {"message": "Password has been reset."}


@app.get("/analyses")
async def list_analyses() -> list[dict[str, Any]]:
    return [_public_analysis(analysis) for analysis in analyses]


@app.post("/analyses")
async def create_analysis(request: Request) -> dict[str, str]:
    analysis_id = f"ana-{int(time.time() * 1000)}"
    content_type = request.headers.get("content-type", "")
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Uploaded image is too large")
    body = await request.body()
    if len(body) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Uploaded image is too large")
    original_filename, image_bytes = _extract_uploaded_image(body, content_type)
    upload_path = UPLOAD_DIR / f"{analysis_id}-{_safe_upload_name(original_filename)}"
    overlay_path = OVERLAY_DIR / f"{analysis_id}-segmented.png"
    upload_path.write_bytes(image_bytes)
    original_image_url = _url_for_generated_file(request, upload_path)
    overlay_url = _url_for_generated_file(request, overlay_path)

    analyses.insert(
        0,
        {
            "id": analysis_id,
            "uploader": mock_user["name"],
            "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            "status": "queued",
            "fileName": original_filename,
            "uploadedBy": mock_user["role"],
            "imagePath": upload_path,
            "overlayPath": overlay_path,
            "originalImageUrl": original_image_url,
            "overlayUrl": overlay_url,
        },
    )
    asyncio.create_task(_run_prediction_job(analysis_id))
    return {
        "analysisId": analysis_id,
        "status": "queued",
        "message": "Analysis queued for prediction.",
    }


@app.get("/analyses/{analysis_id}/status")
async def get_analysis_status(analysis_id: str) -> dict[str, Any]:
    analysis = next((item for item in analyses if item["id"] == analysis_id), None)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    status = analysis["status"]
    progress = 100 if status == "completed" else 70 if status == "processing" else 25
    return {
        "analysisId": analysis_id,
        "status": status,
        "progress": progress,
        "result": results.get(analysis_id) if status == "completed" else None,
        "errorMessage": job_errors.get(analysis_id),
    }


@app.get("/analyses/{analysis_id}")
async def get_analysis_result(analysis_id: str) -> dict[str, Any]:
    if analysis_id == "ana-demo" and analysis_id not in results:
        prediction = await asyncio.to_thread(
            predict_from_checkpoint,
            str(DEMO_IMAGE_PATH),
            str(CHECKPOINT_PATH),
        )
        results[analysis_id] = _result_from_prediction(analysis_id, prediction)

    result = results.get(analysis_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return result
