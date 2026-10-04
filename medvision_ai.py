"""MedVision AI: end-to-end fracture detection prototype.

This single-file script contains:
1. X-ray preprocessing with CLAHE, Gaussian blur, resizing, and normalization.
2. An Attention U-Net segmentation model in PyTorch.
3. Severity assessment using contour geometry.
4. End-to-end inference that returns a mask, features, and severity tier.

"""

from __future__ import annotations

import base64
import argparse
import importlib
import importlib.util
import json
import math
import random
import os
import re
import sys
import time
import traceback
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

import cv2
import numpy as np
from sklearn.metrics import f1_score, jaccard_score, precision_score, recall_score
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset, Subset

A: Any = None
if importlib.util.find_spec("albumentations") is not None:
    A = importlib.import_module("albumentations")


IMAGE_SIZE = 256
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def set_seed(seed: int = 42) -> None:
    """Make the demo deterministic enough for a live presentation."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def preprocess_image(image_path: str) -> np.ndarray:
    """Load a grayscale X-ray, enhance it, resize it, and normalize it.

    Why this order?
    - CLAHE boosts local contrast around bone edges and faint fracture lines.
    - Gaussian blur suppresses scanner noise that can trigger false positives.
    - Resizing standardizes all inputs to a fixed tensor shape.
    - Normalization to [0, 1] stabilizes optimization and inference.
    """

    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"Could not read image at: {image_path}")

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(image)
    denoised = cv2.GaussianBlur(enhanced, (3, 3), 0)
    resized = cv2.resize(denoised, (IMAGE_SIZE, IMAGE_SIZE), interpolation=cv2.INTER_AREA)
    normalized = resized.astype(np.float32) / 255.0
    return normalized


def preprocess_image_array(image: np.ndarray) -> np.ndarray:
    """Apply the same preprocessing pipeline to an already-loaded image array."""

    if image.ndim == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(image)
    denoised = cv2.GaussianBlur(enhanced, (3, 3), 0)
    resized = cv2.resize(denoised, (IMAGE_SIZE, IMAGE_SIZE), interpolation=cv2.INTER_AREA)
    normalized = resized.astype(np.float32) / 255.0
    return normalized


def _decode_image_bytes(image_bytes: bytes) -> np.ndarray:
    """Decode image bytes from the zip archive into a grayscale numpy array."""

    buffer = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError("Failed to decode image bytes from FracAtlas archive")
    return image


def _rasterize_coco_segmentation(segmentation: List[List[float]], width: int, height: int) -> np.ndarray:
    """Convert COCO polygon segmentations into a binary mask."""

    mask = np.zeros((height, width), dtype=np.uint8)
    polygon_points: List[np.ndarray] = []

    for polygon in segmentation:
        if len(polygon) < 6:
            continue
        points = np.array(polygon, dtype=np.float32).reshape(-1, 2)
        points[:, 0] = np.clip(points[:, 0], 0, width - 1)
        points[:, 1] = np.clip(points[:, 1], 0, height - 1)
        polygon_points.append(points.astype(np.int32))

    if polygon_points:
        cv2.fillPoly(mask, polygon_points, 1)

    return mask


def _extract_zip_member(zip_file: zipfile.ZipFile, member_name: str, output_dir: Path) -> Path:
    """Extract one archive member to a temporary directory for downstream OpenCV reads."""

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / Path(member_name).name
    with zip_file.open(member_name) as source, open(output_path, "wb") as destination:
        destination.write(source.read())
    return output_path


class FracAtlasZipDataset(Dataset):
    """Real FracAtlas dataset reader backed directly by the zip archive.

    The dataset uses the COCO polygon annotations inside the archive to build a
    binary fracture mask for each image. Images with no annotations receive an
    all-zero mask, which keeps the training loop honest and lets the demo use
    both positive and negative samples.
    """

    def __init__(self, zip_path: str, max_items: Optional[int] = None, transform: Optional[Any] = None) -> None:
        self.zip_path = Path(zip_path)
        if not self.zip_path.exists():
            raise FileNotFoundError(f"FracAtlas zip not found: {zip_path}")
        self.transform = transform

        with zipfile.ZipFile(self.zip_path, "r") as zf:
            coco_json = json.loads(zf.read("FracAtlas/Annotations/COCO JSON/COCO_fracture_masks.json"))
            self.image_records = coco_json["images"]
            self.annotations = coco_json.get("annotations", [])

            self.image_member_map = {
                Path(name).name: name
                for name in zf.namelist()
                if name.lower().startswith("fracatlas/images/") and name.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))
            }

        self.annotation_index: Dict[int, List[dict]] = {}
        for annotation in self.annotations:
            self.annotation_index.setdefault(int(annotation["image_id"]), []).append(annotation)

        if max_items is not None:
            self.image_records = self.image_records[:max_items]

        self._cache: List[Tuple[np.ndarray, np.ndarray]] = []
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            for record in self.image_records:
                image_member = self.image_member_map.get(record["file_name"])
                if image_member is None:
                    raise FileNotFoundError(f"Could not resolve FracAtlas image in zip: {record['file_name']}")

                image = _decode_image_bytes(zf.read(image_member))
                height = int(record["height"])
                width = int(record["width"])
                mask = np.zeros((height, width), dtype=np.uint8)
                for annotation in self.annotation_index.get(int(record["id"]), []):
                    segmentation = annotation.get("segmentation", [])
                    if segmentation:
                        mask |= _rasterize_coco_segmentation(segmentation, width, height)

                self._cache.append((image, mask))

    def __len__(self) -> int:
        return len(self.image_records)

    def __getitem__(self, index: int) -> Tuple[torch.Tensor, torch.Tensor]:
        image, mask = self._cache[index]

        preprocessed_image = preprocess_image_array(image)
        resized_mask = cv2.resize(mask, (IMAGE_SIZE, IMAGE_SIZE), interpolation=cv2.INTER_NEAREST).astype(np.float32)

        if self.transform is not None:
            augmented = self.transform(image=preprocessed_image, mask=resized_mask)
            preprocessed_image = augmented["image"]
            resized_mask = augmented["mask"]

        preprocessed_image = np.asarray(preprocessed_image, dtype=np.float32)
        resized_mask = np.asarray(resized_mask, dtype=np.float32)

        image_tensor = torch.from_numpy(preprocessed_image).unsqueeze(0)
        mask_tensor = torch.from_numpy(resized_mask).unsqueeze(0)
        return image_tensor, mask_tensor


def first_fracatlas_member(zip_path: str) -> Tuple[Optional[str], Optional[np.ndarray]]:
    """Return a random real FracAtlas image path and a rasterized mask for demo use."""

    archive_path = Path(zip_path)
    if not archive_path.exists():
        return None, None

    with zipfile.ZipFile(archive_path, "r") as zf:
        coco_json = json.loads(zf.read("FracAtlas/Annotations/COCO JSON/COCO_fracture_masks.json"))
        image_records = coco_json["images"]
        annotations = coco_json.get("annotations", [])
        annotation_index: Dict[int, List[dict]] = {}
        for annotation in annotations:
            annotation_index.setdefault(int(annotation["image_id"]), []).append(annotation)

        image_member_map = {
            Path(name).name: name
            for name in zf.namelist()
            if name.lower().startswith("fracatlas/images/") and name.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))
        }

        eligible_records = [
            record
            for record in image_records
            if image_member_map.get(record["file_name"]) is not None
        ]
        if not eligible_records:
            return None, None

        chosen_record = random.SystemRandom().choice(eligible_records)
        file_name = chosen_record["file_name"]
        image_member = image_member_map[file_name]

        extracted_dir = archive_path.parent / "medvision_temp"
        extracted_path = _extract_zip_member(zf, image_member, extracted_dir)

        height = int(chosen_record["height"])
        width = int(chosen_record["width"])
        mask = np.zeros((height, width), dtype=np.uint8)
        for annotation in annotation_index.get(int(chosen_record["id"]), []):
            segmentation = annotation.get("segmentation", [])
            if segmentation:
                mask |= _rasterize_coco_segmentation(segmentation, width, height)

        return str(extracted_path), mask

    return None, None


class ConvBlock(nn.Module):
    """Two Conv-BN-ReLU layers used throughout the encoder and decoder."""

    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class AttentionGate(nn.Module):
    """Spatial attention gate for skip connections.

    Why this works:
    - x is the encoder feature map carrying fine spatial detail.
    - g is the decoder gating signal, which encodes coarse semantic context.
    - We project both to a lower-dimensional shared space, add them, pass through
      a non-linearity, and predict a single-channel attention mask alpha.
    - alpha acts like a learned soft mask, suppressing irrelevant background and
      preserving features that are useful for the current decoding stage.
    """

    def __init__(self, in_channels_x: int, in_channels_g: int, inter_channels: int) -> None:
        super().__init__()
        self.theta_x = nn.Sequential(
            nn.Conv2d(in_channels_x, inter_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(inter_channels),
        )
        self.phi_g = nn.Sequential(
            nn.Conv2d(in_channels_g, inter_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(inter_channels),
        )
        self.psi = nn.Sequential(
            nn.Conv2d(inter_channels, 1, kernel_size=1, bias=True),
            nn.Sigmoid(),
        )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor, g: torch.Tensor) -> torch.Tensor:
        target_size = x.shape[2:]
        if g.shape[2:] != target_size:
            g = F.interpolate(g, size=target_size, mode="bilinear", align_corners=False)

        theta_x = self.theta_x(x)
        phi_g = self.phi_g(g)
        alpha = self.psi(self.relu(theta_x + phi_g))
        return x * alpha


class AttentionUNet(nn.Module):
    """A 4-level Attention U-Net for binary fracture segmentation."""

    def __init__(self, in_channels: int = 1, out_channels: int = 1) -> None:
        super().__init__()
        self.enc1 = ConvBlock(in_channels, 64)
        self.enc2 = ConvBlock(64, 128)
        self.enc3 = ConvBlock(128, 256)
        self.enc4 = ConvBlock(256, 512)

        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.bottleneck = ConvBlock(512, 1024)

        self.up4 = nn.ConvTranspose2d(1024, 512, kernel_size=2, stride=2)
        self.att4 = AttentionGate(512, 512, 256)
        self.dec4 = ConvBlock(1024, 512)

        self.up3 = nn.ConvTranspose2d(512, 256, kernel_size=2, stride=2)
        self.att3 = AttentionGate(256, 256, 128)
        self.dec3 = ConvBlock(512, 256)

        self.up2 = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        self.att2 = AttentionGate(128, 128, 64)
        self.dec2 = ConvBlock(256, 128)

        self.up1 = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
        self.att1 = AttentionGate(64, 64, 32)
        self.dec1 = ConvBlock(128, 64)

        self.final = nn.Sequential(
            nn.Conv2d(64, out_channels, kernel_size=1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        e4 = self.enc4(self.pool(e3))

        b = self.bottleneck(self.pool(e4))

        d4 = self.up4(b)
        s4 = self.att4(e4, d4)
        d4 = self.dec4(torch.cat([d4, s4], dim=1))

        d3 = self.up3(d4)
        s3 = self.att3(e3, d3)
        d3 = self.dec3(torch.cat([d3, s3], dim=1))

        d2 = self.up2(d3)
        s2 = self.att2(e2, d2)
        d2 = self.dec2(torch.cat([d2, s2], dim=1))

        d1 = self.up1(d2)
        s1 = self.att1(e1, d1)
        d1 = self.dec1(torch.cat([d1, s1], dim=1))

        return self.final(d1)


def dice_loss(prediction: torch.Tensor, target: torch.Tensor, smooth: float = 1e-6) -> torch.Tensor:
    """Soft Dice loss for overlap quality."""

    prediction = prediction.contiguous().view(prediction.size(0), -1)
    target = target.contiguous().view(target.size(0), -1)
    intersection = (prediction * target).sum(dim=1)
    dice = (2.0 * intersection + smooth) / (prediction.sum(dim=1) + target.sum(dim=1) + smooth)
    return 1.0 - dice.mean()


def _probabilities_to_logits(prediction: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    """Convert the current Sigmoid model output to logits without changing the architecture."""

    prediction = prediction.clamp(min=eps, max=1.0 - eps)
    return torch.logit(prediction)


def focal_tversky_loss(
    prediction: torch.Tensor,
    target: torch.Tensor,
    alpha: float = 0.7,
    beta: float = 0.3,
    gamma: float = 0.75,
    smooth: float = 1e-6,
) -> torch.Tensor:
    """Focal Tversky loss, useful when small foreground structures are easy to miss."""

    prediction = prediction.contiguous().view(prediction.size(0), -1)
    target = target.contiguous().view(target.size(0), -1)
    true_positive = (prediction * target).sum(dim=1)
    false_negative = ((1.0 - prediction) * target).sum(dim=1)
    false_positive = (prediction * (1.0 - target)).sum(dim=1)
    tversky = (true_positive + smooth) / (
        true_positive + alpha * false_negative + beta * false_positive + smooth
    )
    return torch.pow(1.0 - tversky, gamma).mean()


def combined_dice_bce_loss(
    prediction: torch.Tensor,
    target: torch.Tensor,
    pos_weight: Optional[torch.Tensor] = None,
    loss_mode: str = "weighted_bce",
) -> torch.Tensor:
    """Combine Dice with an imbalance-aware segmentation loss.

    ``focal_tversky`` is the default because this dataset's foreground occupies
    only about 0.5% of pixels. Focal Tversky is a more standard fit than a raw
    inverse-frequency BCE weight at that scale, and returning it without an extra
    Dice term keeps the loss scale lower while preserving the imbalance focus.
    The model architecture still returns probabilities, so the legacy
    ``weighted_bce`` branch converts them back to logits without changing the head.
    """

    dice = dice_loss(prediction, target)
    normalized_mode = loss_mode.lower().strip()
    if normalized_mode == "weighted_bce":
        logits = _probabilities_to_logits(prediction)
        bce = F.binary_cross_entropy_with_logits(logits, target, pos_weight=pos_weight)
        return bce + dice
    if normalized_mode == "focal_tversky":
        return focal_tversky_loss(prediction, target)
    raise ValueError("loss_mode must be either 'weighted_bce' or 'focal_tversky'")


def assess_severity(binary_mask: torch.Tensor | np.ndarray, threshold: float = 0.5) -> Tuple[np.ndarray, Dict[str, float], str]:
    """Extract the largest fracture component and compute severity heuristics.

    The reasoning is simple and review-friendly:
    - The largest connected component is a robust proxy for the main fracture line.
    - Area measures spread of fractured pixels.
    - Perimeter and compactness describe shape complexity and fragmentation.
    - Aspect ratio tells us whether the component is elongated or compact.
    - Severity tiers use area thresholds as a transparent heuristic baseline.
    """

    if isinstance(binary_mask, torch.Tensor):
        mask_np = binary_mask.detach().cpu().numpy()
    else:
        mask_np = np.asarray(binary_mask)

    mask_np = np.squeeze(mask_np)
    if mask_np.ndim != 2:
        raise ValueError(f"Expected a 2D mask after squeeze, got shape {mask_np.shape}")

    binary = (mask_np >= threshold).astype(np.uint8)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    if num_labels <= 1:
        features = {"area": 0.0, "perimeter": 0.0, "compactness": 0.0, "aspect_ratio": 0.0}
        return binary, features, "Mild"

    largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    largest_component = (labels == largest_label).astype(np.uint8)

    contours, _ = cv2.findContours(largest_component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        area = float(largest_component.sum())
        perimeter = 0.0
        x = y = 0
        w = h = 1
    else:
        contour = max(contours, key=cv2.contourArea)
        area = float(cv2.contourArea(contour))
        perimeter = float(cv2.arcLength(contour, True))
        x, y, w, h = cv2.boundingRect(contour)

    compactness = float((4.0 * math.pi * area) / (perimeter ** 2 + 1e-6))
    aspect_ratio = float(w / (h + 1e-6))

    # Transparent area heuristics for a live demo. These are intentionally simple.
    if area < 150.0:
        severity = "Mild"
    elif area < 900.0:
        severity = "Moderate"
    else:
        severity = "Severe"

    features = {
        "area": area,
        "perimeter": perimeter,
        "compactness": compactness,
        "aspect_ratio": aspect_ratio,
    }
    return largest_component.astype(np.uint8), features, severity


def _ensure_4d_tensor(image: np.ndarray | torch.Tensor) -> torch.Tensor:
    if isinstance(image, np.ndarray):
        tensor = torch.from_numpy(image)
    else:
        tensor = image
    if tensor.ndim == 2:
        tensor = tensor.unsqueeze(0).unsqueeze(0)
    elif tensor.ndim == 3:
        tensor = tensor.unsqueeze(0)
    return tensor.float()


def run_medvision_inference(
    image_path: str,
    model: Optional[nn.Module] = None,
    threshold: float = 0.5,
) -> Tuple[np.ndarray, Dict[str, float], str]:
    """Run preprocessing, forward pass, and severity estimation in one call."""

    start_time = time.perf_counter()
    processed = preprocess_image(image_path)
    input_tensor = _ensure_4d_tensor(processed).to(DEVICE)

    if model is None:
        model = AttentionUNet().to(DEVICE)

    model.eval()

    with torch.no_grad():
        predicted_mask = model(input_tensor)

    binary_mask = (predicted_mask.squeeze(0).squeeze(0).cpu() >= threshold).float()
    mask_np, feature_dict, severity = assess_severity(binary_mask, threshold=threshold)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    print(f"MedVision AI inference time: {elapsed_ms:.2f} ms")
    return mask_np, feature_dict, severity


def generate_mock_xray_image(size: int = IMAGE_SIZE) -> np.ndarray:
    """Create a synthetic grayscale X-ray-like image for the demo if needed."""

    image = np.zeros((size, size), dtype=np.uint8)
    cv2.rectangle(image, (40, 35), (215, 225), 75, thickness=-1)
    cv2.line(image, (60, 75), (200, 170), 160, thickness=5)
    cv2.line(image, (75, 180), (185, 95), 140, thickness=3)
    noise = np.random.normal(loc=0.0, scale=12.0, size=(size, size)).astype(np.float32)
    image = np.clip(image.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    return image


def generate_mock_fracture_mask(size: int = IMAGE_SIZE) -> np.ndarray:
    """Create a synthetic fracture mask aligned with the demo image geometry."""

    mask = np.zeros((size, size), dtype=np.uint8)
    cv2.line(mask, (60, 75), (200, 170), 1, thickness=5)
    cv2.line(mask, (75, 180), (185, 95), 1, thickness=3)
    return mask


def _apply_elastic_warp(image: np.ndarray, mask: np.ndarray, alpha: float = 8.0, sigma: float = 12.0) -> Tuple[np.ndarray, np.ndarray]:
    """Apply the same elastic warp to an image/mask pair."""

    random_state = np.random.RandomState()
    height, width = image.shape[:2]
    dx = cv2.GaussianBlur((random_state.rand(height, width).astype(np.float32) * 2.0 - 1.0), (0, 0), sigma) * alpha
    dy = cv2.GaussianBlur((random_state.rand(height, width).astype(np.float32) * 2.0 - 1.0), (0, 0), sigma) * alpha

    grid_x, grid_y = np.meshgrid(np.arange(width), np.arange(height))
    map_x = (grid_x + dx).astype(np.float32)
    map_y = (grid_y + dy).astype(np.float32)

    warped_image = cv2.remap(image, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
    warped_mask = cv2.remap(mask, map_x, map_y, interpolation=cv2.INTER_NEAREST, borderMode=cv2.BORDER_REFLECT_101)
    return warped_image, warped_mask


class _FallbackTrainingTransform:
    """Local augmentation path that mirrors the requested training-only geometry changes."""

    def __call__(self, *, image: np.ndarray, mask: np.ndarray) -> Dict[str, np.ndarray]:
        transformed_image = np.asarray(image, dtype=np.float32)
        transformed_mask = np.asarray(mask, dtype=np.float32)

        if random.random() < 0.5:
            transformed_image = np.fliplr(transformed_image)
            transformed_mask = np.fliplr(transformed_mask)

        if random.random() < 0.5:
            angle = random.uniform(-15.0, 15.0)
            center = (transformed_image.shape[1] / 2.0, transformed_image.shape[0] / 2.0)
            matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            transformed_image = cv2.warpAffine(
                transformed_image,
                matrix,
                (transformed_image.shape[1], transformed_image.shape[0]),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REFLECT_101,
            )
            transformed_mask = cv2.warpAffine(
                transformed_mask,
                matrix,
                (transformed_mask.shape[1], transformed_mask.shape[0]),
                flags=cv2.INTER_NEAREST,
                borderMode=cv2.BORDER_REFLECT_101,
            )

        if random.random() < 0.3:
            transformed_image, transformed_mask = _apply_elastic_warp(transformed_image, transformed_mask)

        return {"image": transformed_image.astype(np.float32), "mask": transformed_mask.astype(np.float32)}


def _build_training_transform() -> Optional[object]:
    """Build Albumentations augmentation for the training split only."""

    if A is None:
        print("Albumentations is not installed; using a local synchronized augmentation fallback.")
        return _FallbackTrainingTransform()

    return A.Compose(
        [
            A.HorizontalFlip(p=0.5),
            A.Rotate(limit=15, border_mode=cv2.BORDER_REFLECT_101, p=0.5),
            A.ElasticTransform(alpha=1.0, sigma=50.0, border_mode=cv2.BORDER_REFLECT_101, p=0.3),
        ]
    )


def _compute_split_lengths(total_items: int) -> Tuple[int, int, int]:
    """Compute a deterministic 70/15/15 split for the available dataset size."""

    if total_items <= 0:
        raise ValueError("Dataset must contain at least one item")

    if total_items < 3:
        train_len = 1 if total_items >= 1 else 0
        val_len = 1 if total_items >= 2 else 0
        test_len = total_items - train_len - val_len
        return train_len, val_len, test_len

    train_len = max(1, int(total_items * 0.70))
    val_len = max(1, int(total_items * 0.15))
    test_len = total_items - train_len - val_len

    if test_len < 1:
        test_len = 1
        overflow = train_len + val_len + test_len - total_items
        while overflow > 0 and train_len > 1:
            train_len -= 1
            overflow -= 1
        while overflow > 0 and val_len > 1:
            val_len -= 1
            overflow -= 1

    return train_len, val_len, total_items - train_len - val_len


def _split_indices(indices: List[int], seed: int) -> Tuple[List[int], List[int], List[int]]:
    """Split a list of indices into train/val/test with deterministic shuffling."""

    if not indices:
        return [], [], []

    rng = np.random.default_rng(seed)
    shuffled = np.array(indices, dtype=np.int64)
    rng.shuffle(shuffled)
    n = len(shuffled)
    if n <= 3:
        train_len = max(1, int(round(n * 0.70)))
        val_len = max(1, int(round(n * 0.15)))
        test_len = n - train_len - val_len
        if test_len < 0:
            test_len = 0
        if test_len == 0 and n > 2:
            test_len = 1
            val_len = max(1, val_len - 1)
    else:
        train_len = max(1, int(n * 0.70))
        val_len = max(1, int(n * 0.15))
        test_len = n - train_len - val_len

    if test_len < 0:
        test_len = 0

    return (
        shuffled[:train_len].tolist(),
        shuffled[train_len : train_len + val_len].tolist(),
        shuffled[train_len + val_len : train_len + val_len + test_len].tolist(),
    )


def _is_positive_mask(mask_tensor: torch.Tensor) -> bool:
    """Return True if the tensor contains any positive pixels."""

    return bool(mask_tensor.detach().cpu().sum().item() > 0.0)


def _build_dataset_splits(
    dataset_zip: Path,
    seed: int = 42,
    verbose: bool = True,
    max_items: Optional[int] = None,
) -> Tuple[Subset, Subset, Subset, str, Dict[str, int]]:
    """Create stratified train/validation/test subsets from either the real or fallback dataset."""

    if dataset_zip.exists():
        base_dataset = FracAtlasZipDataset(str(dataset_zip), max_items=max_items)
        train_dataset = FracAtlasZipDataset(str(dataset_zip), max_items=max_items, transform=_build_training_transform())
        val_dataset = FracAtlasZipDataset(str(dataset_zip), max_items=max_items)
        test_dataset = FracAtlasZipDataset(str(dataset_zip), max_items=max_items)
        source_label = "real FracAtlas"
        if verbose:
            print(f"Using real FracAtlas zip at: {dataset_zip}")
    else:
        fallback_length = max_items if max_items is not None else 60
        base_dataset = MockFractureDataset(length=fallback_length)
        train_dataset = base_dataset
        val_dataset = base_dataset
        test_dataset = base_dataset
        source_label = "synthetic fallback"
        if verbose:
            print(f"FracAtlas.zip not found at {dataset_zip}; using synthetic fallback dataset.")

    positive_indices: List[int] = []
    negative_indices: List[int] = []
    for idx in range(len(base_dataset)):
        _, mask_tensor = base_dataset[idx]
        if _is_positive_mask(mask_tensor):
            positive_indices.append(idx)
        else:
            negative_indices.append(idx)

    pos_train, pos_val, pos_test = _split_indices(positive_indices, seed)
    neg_train, neg_val, neg_test = _split_indices(negative_indices, seed + 1)

    train_indices = pos_train + neg_train
    val_indices = pos_val + neg_val
    test_indices = pos_test + neg_test

    train_subset = Subset(train_dataset, train_indices)
    val_subset = Subset(val_dataset, val_indices)
    test_subset = Subset(test_dataset, test_indices)

    positive_counts = {
        "train": sum(1 for idx in train_indices if idx in set(pos_train)),
        "val": sum(1 for idx in val_indices if idx in set(pos_val)),
        "test": sum(1 for idx in test_indices if idx in set(pos_test)),
    }
    if verbose:
        print(
            f"Stratified split positive counts -> train={positive_counts['train']} val={positive_counts['val']} test={positive_counts['test']}"
        )
    return train_subset, val_subset, test_subset, source_label, positive_counts


def diagnose_dataset(dataset_zip: Optional[str] = None) -> None:
    """Inspect FracAtlas mask quality before training to surface label issues early."""

    base_dir = Path(__file__).resolve().parent
    resolved_zip = Path(dataset_zip) if dataset_zip is not None else base_dir / "FracAtlas.zip"
    if not resolved_zip.exists():
        print("FracAtlas.zip is not available; dataset diagnosis skipped.")
        return

    dataset = FracAtlasZipDataset(str(resolved_zip))
    empty_mask_count = 0
    non_empty_mask_count = 0
    positive_pixel_percentages: List[float] = []

    for idx in range(len(dataset)):
        _, mask_tensor = dataset[idx]
        mask_array = mask_tensor.squeeze().cpu().numpy()
        positive_pixels = float(np.count_nonzero(mask_array > 0.0))
        total_pixels = float(mask_array.size)
        if total_pixels <= 0.0:
            continue
        if positive_pixels <= 0.0:
            empty_mask_count += 1
        else:
            non_empty_mask_count += 1
            positive_pixel_percentages.append((positive_pixels / total_pixels) * 100.0)

    print("\n=== FracAtlas dataset diagnosis ===")
    print(f"Total samples: {len(dataset)}")
    print(f"Empty masks: {empty_mask_count}")
    print(f"Non-empty masks: {non_empty_mask_count}")
    if positive_pixel_percentages:
        print(f"Positive-pixel percentage (non-empty masks) -> avg={np.mean(positive_pixel_percentages):.3f}% min={np.min(positive_pixel_percentages):.3f}% max={np.max(positive_pixel_percentages):.3f}%")
    else:
        print("Positive-pixel percentage (non-empty masks) -> avg=N/A min=N/A max=N/A")

    empty_ratio = empty_mask_count / max(1, len(dataset))
    if empty_ratio > 0.90:
        print("WARNING: more than 90'%' of masks are empty. This is likely a data/parsing issue, not a training issue.")
        print("Please verify whether the COCO JSON contains populated 'segmentation' entries for fracture-labeled images instead of only bounding boxes.")


def _estimate_positive_pixel_ratio(dataset: Dataset, indices: Optional[List[int]] = None) -> Tuple[float, int, int]:
    """Estimate foreground/background pixel ratio from the dataset over a given index set."""

    if indices is None:
        dataset_length_fn = getattr(dataset, "__len__", None)
        indices = list(range(cast(int, dataset_length_fn()))) if callable(dataset_length_fn) else []
    else:
        indices = list(indices)

    total_pixels = 0
    positive_pixels = 0
    for idx in indices:
        _, mask_tensor = dataset[idx]
        mask_array = mask_tensor.squeeze().cpu().numpy()
        positive_pixels += int(np.count_nonzero(mask_array > 0.0))
        total_pixels += int(mask_array.size)

    if total_pixels <= 0:
        return 0.0, 0, 0
    positive_ratio = positive_pixels / max(1, total_pixels)
    return positive_ratio, positive_pixels, total_pixels


def _collect_binary_metrics(predictions: List[np.ndarray], targets: List[np.ndarray]) -> Dict[str, float]:
    """Compute pixel-level Dice, IoU, precision, and recall from flattened masks."""

    flat_predictions = np.concatenate(predictions, axis=0).ravel()
    flat_targets = np.concatenate(targets, axis=0).ravel()
    return {
        "dice": float(f1_score(flat_targets, flat_predictions, zero_division=0)),
        "iou": float(jaccard_score(flat_targets, flat_predictions, zero_division=0)),
        "precision": float(precision_score(flat_targets, flat_predictions, zero_division=0)),
        "recall": float(recall_score(flat_targets, flat_predictions, zero_division=0)),
    }


def _evaluate_segmentation_model(
    model: nn.Module,
    data_loader: DataLoader,
    threshold: float = 0.5,
    pos_weight: Optional[torch.Tensor] = None,
    loss_mode: str = "weighted_bce",
    heartbeat_stage: Optional[str] = None,
    epoch_index: Optional[int] = None,
    total_epochs: Optional[int] = None,
    log_every: int = 10,
) -> Tuple[float, Dict[str, float], float]:
    """Evaluate a segmentation model over an entire split."""

    model.eval()
    total_loss = 0.0
    prediction_batches: List[np.ndarray] = []
    target_batches: List[np.ndarray] = []
    positive_pixels_total = 0
    total_pixels_seen = 0

    with torch.no_grad():
        total_batches = max(1, len(data_loader))
        stage_start = time.perf_counter()
        for batch_index, (images, masks) in enumerate(data_loader, start=1):
            images = images.to(DEVICE)
            masks = masks.to(DEVICE)

            outputs = model(images)
            loss = combined_dice_bce_loss(outputs, masks, pos_weight=pos_weight, loss_mode=loss_mode)
            total_loss += loss.item()

            if heartbeat_stage is not None and log_every > 0 and (batch_index % log_every == 0 or batch_index == total_batches):
                running_loss = total_loss / batch_index
                elapsed_seconds = time.perf_counter() - stage_start
                display_epoch = epoch_index if epoch_index is not None else 1
                display_total_epochs = total_epochs if total_epochs is not None else 1
                _log_heartbeat(heartbeat_stage, display_epoch, display_total_epochs, batch_index, total_batches, running_loss, elapsed_seconds)

            predicted_binary = (outputs.detach().cpu() >= threshold).numpy().astype(np.uint8).reshape(images.size(0), -1)
            target_binary = masks.detach().cpu().numpy().astype(np.uint8).reshape(images.size(0), -1)
            prediction_batches.append(predicted_binary)
            target_batches.append(target_binary)

            positive_pixels_total += int(np.count_nonzero(predicted_binary > 0))
            total_pixels_seen += int(predicted_binary.size)

    metrics = _collect_binary_metrics(prediction_batches, target_batches)
    average_loss = total_loss / max(1, len(data_loader))
    positive_ratio = positive_pixels_total / max(1, total_pixels_seen)
    return average_loss, metrics, positive_ratio


def _calibrate_threshold(
    model: nn.Module,
    data_loader: DataLoader,
    pos_weight: Optional[torch.Tensor] = None,
    loss_mode: str = "weighted_bce",
) -> Tuple[float, float]:
    """Sweep thresholds and choose the one that maximizes validation Dice."""

    best_threshold = 0.5
    best_dice = -1.0
    print("\nValidation threshold sweep:")
    for threshold in np.arange(0.1, 0.9001, 0.05):
        threshold_value = float(round(threshold, 2))
        _, metrics, _ = _evaluate_segmentation_model(
            model,
            data_loader,
            threshold=threshold_value,
            pos_weight=pos_weight,
            loss_mode=loss_mode,
        )
        print(f"  threshold={threshold_value:.2f} dice={metrics['dice']:.4f}")
        if metrics["dice"] > best_dice:
            best_dice = metrics["dice"]
            best_threshold = threshold_value
    return best_threshold, best_dice


def _threshold_metadata_path(checkpoint_path: str | Path) -> Path:
    checkpoint_file = Path(checkpoint_path)
    return checkpoint_file.with_name(f"{checkpoint_file.stem}_threshold.json")


def _save_calibrated_threshold(checkpoint_path: str | Path, threshold: float, val_dice: float) -> Path:
    metadata_path = _threshold_metadata_path(checkpoint_path)
    payload = {
        "checkpoint_path": str(Path(checkpoint_path)),
        "calibrated_threshold": float(threshold),
        "validation_dice_at_threshold": float(val_dice),
    }
    metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return metadata_path


def _load_calibrated_threshold(checkpoint_path: str | Path, default: float = 0.5) -> float:
    metadata_path = _threshold_metadata_path(checkpoint_path)
    if not metadata_path.exists():
        print(
            f"WARNING: calibrated threshold metadata not found at {metadata_path}; "
            f"falling back to threshold={default:.2f}."
        )
        return default

    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    return float(payload.get("calibrated_threshold", default))


def _load_model_weights(model: nn.Module, checkpoint_path: str | Path) -> None:
    checkpoint = torch.load(checkpoint_path, map_location=DEVICE)
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model.load_state_dict(checkpoint)


def _update_project_status_file(
    status_line: str,
    train_loss: float,
    val_loss: float,
    val_dice: float,
    val_iou: float,
    val_pred_pos: float,
    epoch_number: int,
    total_epochs: int,
    best_val_dice: float,
    best_val_loss: float,
    train_split_size: int,
    val_split_size: int,
    test_split_size: int,
    dataset_total: int,
    loss_mode: str,
    batch_size: int,
    max_epochs: int,
    max_items: Optional[int],
    approach_note: str,
) -> Path:
    """Update the two status sections atomically after each epoch."""

    status_path = Path(__file__).resolve().parent / "PROJECT_STATUS.md"
    current_text = status_path.read_text(encoding="utf-8") if status_path.exists() else ""

    last_run_section = (
        "## LAST RUN RESULTS\n\n"
        f"- Status: {status_line}\n"
        f"- Epoch: {epoch_number}/{total_epochs}\n"
        f"- Train loss: {train_loss:.4f}\n"
        f"- Validation loss: {val_loss:.4f}\n"
        f"- Validation Dice: {val_dice:.4f}\n"
        f"- Validation IoU: {val_iou:.4f}\n"
        f"- Validation predicted-positive ratio: {val_pred_pos:.4f}\n"
        f"- Best validation Dice so far: {best_val_dice:.4f}\n"
        f"- Best validation loss so far: {best_val_loss:.4f}\n"
        f"- Approach: {approach_note}\n"
    )

    latest_run_section = (
        "## LATEST TRAINING RUN\n\n"
        f"Status: {status_line}\n\n"
        f"- Dataset: FracAtlas ({dataset_total} samples)\n"
        f"- Split: train {train_split_size} / val {val_split_size} / test {test_split_size}\n"
        f"- Loss mode: {loss_mode}\n"
        f"- Max epochs: {max_epochs}\n"
        f"- Batch size: {batch_size}\n"
        f"- Max items: {max_items if max_items is not None else 'None'}\n"
        f"- Approach: {approach_note}\n"
        f"- Epoch: {epoch_number}/{total_epochs}\n"
        f"- Train loss: {train_loss:.4f}\n"
        f"- Validation loss: {val_loss:.4f}\n"
        f"- Validation Dice: {val_dice:.4f}\n"
        f"- Validation IoU: {val_iou:.4f}\n"
        f"- Validation predicted-positive ratio: {val_pred_pos:.4f}\n"
    )

    def replace_section(text: str, heading: str, replacement: str) -> str:
        pattern = rf"(?ms)^## {re.escape(heading)}\n.*?(?=^## |\Z)"
        if re.search(pattern, text):
            return re.sub(pattern, replacement.rstrip() + "\n\n", text, count=1)
        if text and not text.endswith("\n"):
            text += "\n"
        return text + "\n" + replacement.rstrip() + "\n"

    updated_text = replace_section(current_text, "LAST RUN RESULTS", last_run_section)
    updated_text = replace_section(updated_text, "LATEST TRAINING RUN", latest_run_section)

    temp_path = status_path.with_suffix(".tmp")
    temp_path.write_text(updated_text, encoding="utf-8")
    os.replace(temp_path, status_path)
    return status_path


def _format_duration(seconds: float) -> str:
    minutes, remaining_seconds = divmod(max(0.0, seconds), 60.0)
    hours, minutes = divmod(int(minutes), 60)
    if hours > 0:
        return f"{hours:d}h {minutes:02d}m {remaining_seconds:04.1f}s"
    if minutes > 0:
        return f"{minutes:d}m {remaining_seconds:04.1f}s"
    return f"{remaining_seconds:.1f}s"


def _log_heartbeat(stage: str, epoch_index: int, total_epochs: int, batch_index: int, total_batches: int, running_loss: float, elapsed_seconds: float) -> None:
    print(
        f"Epoch {epoch_index}/{total_epochs} | {stage} batch {batch_index}/{total_batches} | "
        f"running_loss={running_loss:.4f} | elapsed={elapsed_seconds:.1f}s"
    )
    sys.stdout.flush()


def save_mock_image(image: np.ndarray, output_path: str) -> str:
    """Persist a temporary grayscale image to disk for the demo pipeline."""

    cv2.imwrite(output_path, image)
    return output_path


def create_overlay(image_path: str, binary_mask: np.ndarray, output_path: str, mode: str = "prediction") -> str:
    """Overlay either the model prediction or the ground truth mask on the original image."""

    original = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if original is None:
        raise FileNotFoundError(f"Could not read image for overlay: {image_path}")

    normalized_mode = mode.lower().strip()
    if normalized_mode not in {"prediction", "ground_truth"}:
        raise ValueError("mode must be either 'prediction' or 'ground_truth'")

    original = cv2.resize(original, (IMAGE_SIZE, IMAGE_SIZE), interpolation=cv2.INTER_AREA)
    if binary_mask.shape != original.shape:
        binary_mask = cv2.resize(binary_mask.astype(np.uint8), (IMAGE_SIZE, IMAGE_SIZE), interpolation=cv2.INTER_NEAREST)

    overlay = cv2.cvtColor(original, cv2.COLOR_GRAY2BGR)
    overlay_color = (0, 0, 255) if normalized_mode == "prediction" else (0, 255, 0)
    overlay[binary_mask > 0] = overlay_color
    blended = cv2.addWeighted(overlay, 0.55, cv2.cvtColor(original, cv2.COLOR_GRAY2BGR), 0.45, 0)
    cv2.imwrite(output_path, blended)
    return output_path


def create_before_after_comparison(
    image_path: str,
    binary_mask: np.ndarray,
    output_path: str,
) -> str:
    """Create a clean side-by-side result image labeled only Before and After."""

    original = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if original is None:
        raise FileNotFoundError(f"Could not read image for comparison: {image_path}")

    original = cv2.resize(original, (IMAGE_SIZE, IMAGE_SIZE), interpolation=cv2.INTER_AREA)
    mask = np.asarray(binary_mask, dtype=np.uint8)
    if mask.shape != original.shape:
        mask = cv2.resize(mask, (IMAGE_SIZE, IMAGE_SIZE), interpolation=cv2.INTER_NEAREST)

    before = cv2.cvtColor(original, cv2.COLOR_GRAY2BGR)
    after = before.copy()
    after[mask > 0] = (0, 0, 255)
    after = cv2.addWeighted(after, 0.55, before, 0.45, 0)

    label_bar_height = 42
    gap_width = 10
    canvas_height = IMAGE_SIZE + label_bar_height
    canvas_width = (IMAGE_SIZE * 2) + gap_width
    canvas = np.full((canvas_height, canvas_width, 3), 255, dtype=np.uint8)

    canvas[label_bar_height:, :IMAGE_SIZE] = before
    canvas[label_bar_height:, IMAGE_SIZE + gap_width:] = after

    def draw_centered_label(text: str, x_start: int) -> None:
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.8
        thickness = 2
        text_size, _ = cv2.getTextSize(text, font, scale, thickness)
        x = x_start + (IMAGE_SIZE - text_size[0]) // 2
        y = 28
        cv2.putText(canvas, text, (x, y), font, scale, (20, 20, 20), thickness, cv2.LINE_AA)

    draw_centered_label("Before", 0)
    draw_centered_label("After", IMAGE_SIZE + gap_width)

    cv2.imwrite(output_path, canvas)
    return output_path


class MockFractureDataset(Dataset):
    """Tiny synthetic dataset used to demonstrate the training loop structure."""

    def __init__(self, length: int = 8) -> None:
        self.length = length

    def __len__(self) -> int:
        return self.length

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        image = generate_mock_xray_image()
        mask = generate_mock_fracture_mask().astype(np.float32)
        image = image.astype(np.float32) / 255.0
        return torch.from_numpy(image).unsqueeze(0), torch.from_numpy(mask).unsqueeze(0)


def train_model(
    model: nn.Module,
    epochs: int = 40,
    batch_size: int = 8,
    dataset_zip: Optional[str] = None,
    seed: int = 42,
    checkpoint_path: Optional[str] = None,
    patience: int = 8,
    loss_mode: str = "weighted_bce",
    max_items: Optional[int] = None,
    log_every: int = 10,
) -> Tuple[str, float, float]:
    """Train the Attention U-Net with imbalance-aware loss, val-Dice checkpointing, and early stopping."""

    set_seed(seed)
    base_dir = Path(__file__).resolve().parent
    resolved_zip = Path(dataset_zip) if dataset_zip is not None else base_dir / "FracAtlas.zip"
    train_subset, val_subset, test_subset, source_label, positive_counts = _build_dataset_splits(
        resolved_zip,
        seed=seed,
        max_items=max_items,
    )

    total_items = len(train_subset) + len(val_subset) + len(test_subset)
    run_summary = (
        f"Run config | dataset={source_label} ({total_items} samples) "
        f"split=train {len(train_subset)} / val {len(val_subset)} / test {len(test_subset)} "
        f"loss_mode={loss_mode} epochs={epochs} batch_size={batch_size}"
    )
    print(run_summary)
    if loss_mode.lower().strip() == "weighted_bce":
        print("Run config note | weighted_bce is still available, but the default Focal Tversky path is better suited to ~0.5% foreground occupancy.")

    approach_note = (
        "focal_tversky-only objective (no extra Dice term) to lower the loss scale while keeping the sparse-foreground focus"
        if loss_mode.lower().strip() == "focal_tversky"
        else "weighted_bce + Dice with a capped pos_weight"
    )

    if max_items is not None and positive_counts["train"] < 50:
        print(
            f"WARNING: --max-items={max_items} leaves only {positive_counts['train']} positive training samples; "
            "results will not be meaningful."
        )

    print(f"Training on {source_label} data with {len(train_subset)} train / {len(val_subset)} val samples")

    train_loader = DataLoader(train_subset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_subset, batch_size=batch_size, shuffle=False)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5)
    checkpoint_file = Path(checkpoint_path) if checkpoint_path is not None else base_dir / "best_model.pt"

    if hasattr(train_subset, "indices"):
        pos_ratio, pos_pixels, total_pixels = _estimate_positive_pixel_ratio(
            train_subset.dataset,
            indices=list(train_subset.indices),
        )
    else:
        pos_ratio, pos_pixels, total_pixels = _estimate_positive_pixel_ratio(train_subset)
    neg_ratio = max(0.0, 1.0 - pos_ratio)
    raw_pos_weight = neg_ratio / (pos_ratio + 1e-6)
    capped_pos_weight = min(25.0, max(1.0, raw_pos_weight))
    pos_weight = torch.tensor([capped_pos_weight], device=DEVICE)
    print(
        f"Training foreground pixels: {pos_pixels:,}/{total_pixels:,} "
        f"({pos_ratio * 100.0:.4f}%); raw_pos_weight={raw_pos_weight:.2f}; capped_pos_weight={pos_weight.item():.2f}; loss_mode={loss_mode}"
    )

    best_val_dice = -1.0
    best_state = None
    best_epoch = 0
    stale_epochs = 0
    best_val_loss = float("inf")
    background_collapse_epochs = 0
    previous_epoch_duration: Optional[float] = None
    model.train()

    for epoch in range(epochs):
        epoch_number = epoch + 1
        if previous_epoch_duration is None:
            print(f"Epoch {epoch_number}/{epochs} starting | ETA unavailable yet")
        else:
            remaining_epochs = epochs - epoch
            eta_seconds = previous_epoch_duration * remaining_epochs
            print(
                f"Epoch {epoch_number}/{epochs} starting | previous_epoch={_format_duration(previous_epoch_duration)} | ETA~{_format_duration(eta_seconds)}"
            )
        sys.stdout.flush()

        epoch_start = time.perf_counter()
        try:
            model.train()
            train_loss_total = 0.0
            total_train_batches = max(1, len(train_loader))
            for batch_index, (images, masks) in enumerate(train_loader, start=1):
                images = images.to(DEVICE)
                masks = masks.to(DEVICE)

                optimizer.zero_grad(set_to_none=True)
                outputs = model(images)
                loss = combined_dice_bce_loss(outputs, masks, pos_weight=pos_weight, loss_mode=loss_mode)
                loss.backward()
                optimizer.step()
                train_loss_total += loss.item()

                if log_every > 0 and (batch_index % log_every == 0 or batch_index == total_train_batches):
                    running_loss = train_loss_total / batch_index
                    elapsed_seconds = time.perf_counter() - epoch_start
                    _log_heartbeat("train", epoch_number, epochs, batch_index, total_train_batches, running_loss, elapsed_seconds)

            train_loss = train_loss_total / max(1, len(train_loader))
            val_loss, val_metrics, positive_ratio_val = _evaluate_segmentation_model(
                model,
                val_loader,
                threshold=0.5,
                pos_weight=pos_weight,
                loss_mode=loss_mode,
                heartbeat_stage="val",
                epoch_index=epoch_number,
                total_epochs=epochs,
                log_every=log_every,
            )
            scheduler.step(val_loss)

            if val_metrics["dice"] > best_val_dice + 1e-6:
                best_val_dice = val_metrics["dice"]
                best_val_loss = val_loss
                best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
                best_epoch = epoch_number
                stale_epochs = 0
                torch.save(model.state_dict(), checkpoint_file)
            else:
                stale_epochs += 1

            if positive_ratio_val < 1e-4:
                background_collapse_epochs += 1
            else:
                background_collapse_epochs = 0

            if background_collapse_epochs >= 3:
                print(
                    "WARNING: validation predicted-positive pixels have stayed near 0% for "
                    f"{background_collapse_epochs} epochs; the model may be collapsing to background-only predictions."
                )

            print(
                f"Epoch {epoch_number:03d}/{epochs:03d} | "
                f"train_loss={train_loss:.4f} | val_loss={val_loss:.4f} | "
                f"val_dice={val_metrics['dice']:.4f} | val_iou={val_metrics['iou']:.4f} | "
                f"val_pred_pos={positive_ratio_val * 100.0:.4f}%"
            )

            status_line = "training complete" if (epoch_number == epochs or stale_epochs >= patience) else f"epoch {epoch_number}/{epochs} complete"
            status_path = _update_project_status_file(
                status_line=status_line,
                train_loss=train_loss,
                val_loss=val_loss,
                val_dice=val_metrics["dice"],
                val_iou=val_metrics["iou"],
                val_pred_pos=positive_ratio_val,
                epoch_number=epoch_number,
                total_epochs=epochs,
                best_val_dice=best_val_dice,
                best_val_loss=best_val_loss,
                train_split_size=len(train_subset),
                val_split_size=len(val_subset),
                test_split_size=len(test_subset),
                dataset_total=total_items,
                loss_mode=loss_mode,
                batch_size=batch_size,
                max_epochs=epochs,
                max_items=max_items,
                approach_note=approach_note,
            )
            print(f"Updated PROJECT_STATUS.md: {status_path}")

            if stale_epochs >= patience:
                print(f"Early stopping triggered at epoch {epoch_number} with patience {patience}.")
                previous_epoch_duration = time.perf_counter() - epoch_start
                break
        except Exception:
            traceback.print_exc()
            raise

        previous_epoch_duration = time.perf_counter() - epoch_start

    if best_state is not None:
        model.load_state_dict(best_state)
    print(f"Best checkpoint saved to: {checkpoint_file} at epoch {best_epoch} with val_dice={best_val_dice:.4f}")
    return str(checkpoint_file), best_val_dice, best_val_loss


def train_mock_model(model: nn.Module, epochs: int = 1, batch_size: int = 2) -> Tuple[str, float, float]:
    """Backward-compatible alias for older call sites."""

    return train_model(model, epochs=epochs, batch_size=batch_size)


def load_first_image_from_zip(zip_path: str) -> Optional[str]:
    """Backward-compatible helper retained for older call sites."""

    archive = Path(zip_path)
    if not archive.exists():
        return None

    temp_dir = Path.cwd() / "medvision_temp"
    temp_dir.mkdir(exist_ok=True)

    with zipfile.ZipFile(archive, "r") as zf:
        image_members = [name for name in zf.namelist() if name.lower().startswith("fracatlas/images/") and name.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))]
        if not image_members:
            return None

        chosen_member = image_members[0]
        extracted_path = temp_dir / Path(chosen_member).name
        with zf.open(chosen_member) as src, open(extracted_path, "wb") as dst:
            dst.write(src.read())
    return str(extracted_path)


def predict_from_checkpoint(image_path: str, checkpoint_path: str = "best_model.pt") -> Dict[str, Any]:
    """Load a trained checkpoint and return a JSON-serializable prediction payload."""

    model = AttentionUNet().to(DEVICE)
    checkpoint_file = Path(checkpoint_path)
    if not checkpoint_file.exists() and not checkpoint_file.is_absolute():
        checkpoint_file = Path(__file__).resolve().parent / checkpoint_file
    if not checkpoint_file.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_file}")

    _load_model_weights(model, checkpoint_file)
    model.eval()
    threshold = _load_calibrated_threshold(checkpoint_file)

    processed = preprocess_image(image_path)
    input_tensor = _ensure_4d_tensor(processed).to(DEVICE)
    with torch.no_grad():
        predicted_mask = model(input_tensor)

    prob_mask = predicted_mask.squeeze(0).squeeze(0).cpu().numpy()
    binary_mask = (prob_mask >= threshold).astype(np.uint8)
    mask_np, feature_dict, severity = assess_severity(binary_mask, threshold=threshold)

    _, encoded_image = cv2.imencode(".png", (mask_np * 255).astype(np.uint8))
    png_b64 = base64.b64encode(encoded_image.tobytes()).decode("ascii")
    return {
        "mask_png_base64": png_b64,
        "mask_shape": list(mask_np.shape),
        "calibrated_threshold": float(threshold),
        "severity_features": feature_dict,
        "severity_tier": severity,
    }


def main() -> None:
    """Entry point for the Phase-I review demo."""

    parser = argparse.ArgumentParser(description="Train and evaluate MedVision Attention U-Net on FracAtlas.")
    parser.add_argument("--dataset-zip", default=None, help="Path to FracAtlas.zip; defaults to this script's directory.")
    parser.add_argument("--max-epochs", type=int, default=40, help="Maximum number of training epochs.")
    parser.add_argument("--batch-size", type=int, default=8, help="Training/evaluation batch size.")
    parser.add_argument("--patience", type=int, default=8, help="Early-stopping patience measured on validation Dice.")
    parser.add_argument("--log-every", type=int, default=10, help="Print a progress heartbeat every N batches during train and validation.")
    parser.add_argument(
        "--max-items",
        type=int,
        default=None,
        help="Optional cap on the dataset size for smoke runs; omit it to use the full FracAtlas dataset.",
    )
    parser.add_argument(
        "--loss-mode",
        choices=["weighted_bce", "focal_tversky"],
        default="focal_tversky",
        help="Class-imbalance-aware loss term to combine with Dice; focal_tversky is the default for FracAtlas sparsity.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic splitting/training.")
    args = parser.parse_args()

    set_seed(args.seed)
    base_dir = Path(__file__).resolve().parent
    dataset_zip = str(Path(args.dataset_zip)) if args.dataset_zip is not None else str(base_dir / "FracAtlas.zip")

    diagnose_dataset(dataset_zip)

    model = AttentionUNet().to(DEVICE)
    best_checkpoint_path, best_val_dice, best_val_loss = train_model(
        model,
        epochs=args.max_epochs,
        batch_size=args.batch_size,
        dataset_zip=dataset_zip,
        checkpoint_path=str(base_dir / "best_model.pt"),
        patience=args.patience,
        loss_mode=args.loss_mode,
        seed=args.seed,
        max_items=args.max_items,
        log_every=max(1, args.log_every),
    )

    inference_model = AttentionUNet().to(DEVICE)
    _load_model_weights(inference_model, best_checkpoint_path)
    inference_model.eval()

    image_path, gt_mask = first_fracatlas_member(dataset_zip)
    mock_image_path = save_mock_image(generate_mock_xray_image(), str(base_dir / "mock_xray.png"))
    print(f"Saved mock X-ray to: {mock_image_path}")

    if image_path is None or gt_mask is None:
        image_path = mock_image_path
        gt_mask = generate_mock_fracture_mask()
        print("Using synthetic overlay comparison example because FracAtlas data was unavailable.")
    else:
        print(f"Using real FracAtlas image for overlay comparison: {image_path}")

    train_subset, val_subset, test_subset, _, _ = _build_dataset_splits(
        Path(dataset_zip), seed=args.seed, verbose=False, max_items=args.max_items
    )
    if hasattr(train_subset, "indices"):
        pos_ratio, _, _ = _estimate_positive_pixel_ratio(train_subset.dataset, indices=list(train_subset.indices))
    else:
        pos_ratio, _, _ = _estimate_positive_pixel_ratio(train_subset)
    pos_weight = torch.tensor([max(1.0, (1.0 - pos_ratio) / (pos_ratio + 1e-6))], device=DEVICE)
    val_loader = DataLoader(val_subset, batch_size=args.batch_size, shuffle=False)
    val_threshold, threshold_val_dice = _calibrate_threshold(
        inference_model,
        val_loader,
        pos_weight=pos_weight,
        loss_mode=args.loss_mode,
    )
    threshold_metadata = _save_calibrated_threshold(best_checkpoint_path, val_threshold, threshold_val_dice)
    print(f"Calibrated validation threshold: {val_threshold:.2f} (val Dice={threshold_val_dice:.4f})")
    print(f"Saved calibrated threshold metadata to: {threshold_metadata}")

    mask, feature_dict, severity = run_medvision_inference(image_path, model=inference_model, threshold=val_threshold)
    print("Extracted fracture geometry:")
    print(feature_dict)
    print(f"Final severity tier: {severity}")

    overlay_path = create_overlay(image_path, mask, str(base_dir / "segmentation_overlay_prediction.png"), mode="prediction")
    print(f"Saved predicted overlay to: {overlay_path}")

    comparison_path = create_before_after_comparison(image_path, mask, str(base_dir / "before_after_result.png"))
    print(f"Saved clean Before/After comparison to: {comparison_path}")

    gt_overlay_path = create_overlay(image_path, gt_mask, str(base_dir / "segmentation_overlay_ground_truth.png"), mode="ground_truth")
    print(f"Saved ground-truth comparison overlay to: {gt_overlay_path}")

    test_loader = DataLoader(test_subset, batch_size=args.batch_size, shuffle=False)
    test_loss, test_metrics, _ = _evaluate_segmentation_model(
        inference_model,
        test_loader,
        threshold=val_threshold,
        pos_weight=pos_weight,
        loss_mode=args.loss_mode,
    )

    print("\nHeld-out test-set evaluation:")
    print(f"{'Metric':<12}{'Score':>12}")
    print(f"{'Dice':<12}{test_metrics['dice']:>12.4f}")
    print(f"{'IoU':<12}{test_metrics['iou']:>12.4f}")
    print(f"{'Precision':<12}{test_metrics['precision']:>12.4f}")
    print(f"{'Recall':<12}{test_metrics['recall']:>12.4f}")
    print(f"{'Loss':<12}{test_loss:>12.4f}")
    print(f"Best val dice seen: {best_val_dice:.4f}; best val loss: {best_val_loss:.4f}")


if __name__ == "__main__":
    main()
