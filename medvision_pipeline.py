"""Versioned research pipeline: geometry, logits losses, lazy data and serving.

Historical medvision_ai.py remains immutable while its E2 job runs.
"""
from dataclasses import asdict, dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
import zipfile

import cv2
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.data import Dataset, WeightedRandomSampler

import medvision_ai as legacy

CONTRACT = 'binary-logits-v2'


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


@dataclass(frozen=True)
class PreprocessConfig:
    size: int = 256
    resize: str = 'letterbox'
    clahe: bool = True
    clip_limit: float = 2.0
    tile_grid: int = 8
    blur_kernel: int = 0
    normalization: str = 'unit'

    def __post_init__(self):
        if self.size < 32 or self.size % 16:
            raise ValueError('Size must be >=32 and divisible by 16')
        if self.resize not in ('letterbox', 'stretch') or self.normalization not in ('unit', 'zscore'):
            raise ValueError('Unsupported geometry or normalization')
        if self.blur_kernel < 0 or (self.blur_kernel and self.blur_kernel % 2 == 0):
            raise ValueError('Blur kernel must be zero or positive odd')
        if self.clip_limit <= 0 or self.tile_grid < 1:
            raise ValueError('Invalid CLAHE parameters')


@dataclass(frozen=True)
class Geometry:
    height: int
    width: int
    resized_height: int
    resized_width: int
    top: int
    left: int
    size: int


def geometry(shape, config):
    h, w = shape
    if min(h, w) < 1:
        raise ValueError('Empty image')
    if config.resize == 'letterbox':
        scale = config.size / max(h, w)
        rh, rw = max(1, round(h*scale)), max(1, round(w*scale))
    else:
        rh = rw = config.size
    return Geometry(h, w, rh, rw, (config.size-rh)//2, (config.size-rw)//2, config.size)


def project(array, g, interpolation):
    resized = cv2.resize(array, (g.resized_width, g.resized_height), interpolation=interpolation)
    canvas = np.zeros((g.size, g.size), dtype=array.dtype)
    canvas[g.top:g.top+g.resized_height, g.left:g.left+g.resized_width] = resized
    return canvas


def inverse(array, g, probability=False):
    if array.shape != (g.size, g.size):
        raise ValueError('Inverse input shape differs from declared geometry')
    crop = array[g.top:g.top+g.resized_height, g.left:g.left+g.resized_width]
    return cv2.resize(crop, (g.width, g.height), interpolation=cv2.INTER_LINEAR if probability else cv2.INTER_NEAREST)


def prepare(image, config, target=None):
    if image.ndim != 2 or image.dtype != np.uint8:
        raise ValueError('Expected decoded grayscale uint8')
    g = geometry(image.shape, config)
    enhanced = image
    if config.clahe:
        enhanced = cv2.createCLAHE(config.clip_limit, (config.tile_grid, config.tile_grid)).apply(enhanced)
    if config.blur_kernel:
        enhanced = cv2.GaussianBlur(enhanced, (config.blur_kernel, config.blur_kernel), 0)
    x = project(enhanced.astype(np.float32), g, cv2.INTER_AREA) / 255
    valid = project(np.ones(image.shape, np.uint8), g, cv2.INTER_NEAREST).astype(np.float32)
    if config.normalization == 'zscore':
        pixels = x[valid.astype(bool)]
        x = (x-float(pixels.mean())) / max(float(pixels.std()), 1e-6)
        x *= valid
    y = None
    if target is not None:
        if target.shape != image.shape or not np.isin(target, [0,1]).all():
            raise ValueError('Target must be an aligned native binary mask')
        y = project(target.astype(np.float32), g, cv2.INTER_NEAREST)
    return x.astype(np.float32), y, valid, g


def seed_everything(seed, deterministic=True):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = deterministic
    torch.use_deterministic_algorithms(deterministic)


def augment(x, y, valid, seed, elastic=False):
    """Local RNG; identical maps for image, target and valid region. No reflect labels."""
    rng = np.random.default_rng(seed)
    if rng.random() < .5:
        x, y, valid = [np.fliplr(a).copy() for a in (x, y, valid)]
    if rng.random() < .5:
        angle = float(rng.uniform(-15, 15))
        size = x.shape[0]
        matrix = cv2.getRotationMatrix2D(((size-1)/2, (size-1)/2), angle, 1)
        x = cv2.warpAffine(x, matrix, (size,size), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        y, valid = [cv2.warpAffine(a, matrix, (size,size), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT) for a in (y,valid)]
    if elastic:
        # Optional research candidate only. Small deformation, scaled with size.
        size = x.shape[0]
        sigma, amplitude = 8*size/256, 2*size/256
        dx, dy = [cv2.GaussianBlur(rng.normal(size=x.shape).astype(np.float32), (0,0), sigma) for _ in range(2)]
        dx, dy = [d/max(float(d.std()),1e-6)*amplitude for d in (dx,dy)]
        xx, yy = np.meshgrid(np.arange(size,dtype=np.float32), np.arange(size,dtype=np.float32))
        x = cv2.remap(x, xx+dx, yy+dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        y, valid = [cv2.remap(a, xx+dx, yy+dy, cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT) for a in (y,valid)]
    valid = (valid > .5).astype(np.float32)
    return (x*valid).astype(np.float32), (y*valid).astype(np.float32), valid


class FracDataset(Dataset):
    def __init__(self, archive, manifest, split, config, training=False, seed=42, elastic=False):
        self.archive = Path(archive)
        document = json.loads(Path(manifest).read_text(encoding='utf-8'))
        if split not in ('train','val','test') or (training and split != 'train'):
            raise ValueError('Augmentation/sampling permitted on training only')
        self.rows = [r for r in document['rows'] if r['split']==split]
        if not self.rows:
            raise ValueError('Empty split')
        self.config, self.training, self.seed, self.elastic, self.epoch = config, training, seed, elastic, 0
        with zipfile.ZipFile(self.archive) as z:
            self.annotations = {a['id']:a for a in json.loads(z.read('FracAtlas/Annotations/COCO JSON/COCO_fracture_masks.json'))['annotations']}

    def native(self, index):
        row = self.rows[index]
        with zipfile.ZipFile(self.archive) as z:
            image = legacy._decode_image_bytes(z.read(row['member']))
        mask = np.zeros(image.shape,np.uint8)
        for aid in row['annotation_ids']:
            mask |= legacy._rasterize_coco_segmentation(self.annotations[aid]['segmentation'], row['width'], row['height'])
        if image.shape != (row['height'], row['width']) or bool(mask.any()) != bool(int(row['fractured'])):
            raise ValueError('Decoded data no longer matches frozen manifest')
        return image, mask

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        image, mask = self.native(index)
        x, y, valid, _ = prepare(image,self.config,mask)
        if self.training:
            rng_seed = np.random.SeedSequence([self.seed,self.epoch,index]).generate_state(1)[0]
            x, y, valid = augment(x,y,valid,int(rng_seed),self.elastic)
        return tuple(torch.from_numpy(a.copy()).unsqueeze(0) for a in (x,y,valid))

    def sampler(self, positive_fraction, epoch):
        if not self.training:
            raise ValueError('Sampler cannot alter validation/test distribution')
        if not 0 < positive_fraction < 1:
            raise ValueError('Requested positive fraction must be between zero and one')
        positives = sum(int(r['fractured']) for r in self.rows)
        negatives = len(self.rows)-positives
        if not positives or not negatives:
            raise ValueError('Both classes required for controlled sampling')
        weights = [positive_fraction/positives if int(r['fractured']) else (1-positive_fraction)/negatives for r in self.rows]
        return WeightedRandomSampler(weights, len(self.rows), replacement=True,
                                     generator=torch.Generator().manual_seed(self.seed+epoch))


class LogitsAttentionUNet(legacy.AttentionUNet):
    output_contract = CONTRACT

    def __init__(self):
        super().__init__()
        # Parameter names stay final.0.*; no numerical logit(sigmoid()) roundtrip.
        self.final[1] = nn.Identity()


@dataclass(frozen=True)
class LossConfig:
    mode: str = 'bce_dice'
    delta: float = .7  # FN weight in foreground Tversky denominator
    focal_exponent: float = .75
    unified_gamma: float = .5
    unified_weight: float = .5
    smooth: float = 1e-6

    def __post_init__(self):
        if self.mode not in ('bce_dice','focal_tversky','unified_focal_symmetric'):
            raise ValueError('Unknown loss')
        if not 0 < self.delta < 1 or not 0 <= self.unified_gamma < 1 or not 0 <= self.unified_weight <= 1 or self.focal_exponent <= 0 or self.smooth <= 0:
            raise ValueError('Invalid loss parameters')


def loss_components(logits, target, valid, config):
    if logits.shape != target.shape or logits.shape != valid.shape or logits.ndim != 4:
        raise ValueError('Expected matching BCHW logits/target/valid tensors')
    dims = (1,2,3)
    n = valid.sum(dims)
    if bool((n <= 0).any()):
        raise ValueError('No valid pixels in a batch image')
    p = logits.sigmoid()
    bce = (F.binary_cross_entropy_with_logits(logits,target,reduction='none')*valid).sum(dims)/n
    tp = (p*target*valid).sum(dims)
    fn = ((1-p)*target*valid).sum(dims)
    fp = (p*(1-target)*valid).sum(dims)
    dice = 1-(2*tp+config.smooth)/(2*tp+fp+fn+config.smooth)
    ti = (tp+config.smooth)/(tp+config.delta*fn+(1-config.delta)*fp+config.smooth)
    ft = (1-ti).clamp(min=1e-7).pow(config.focal_exponent)
    # Binary two-class symmetric Unified Focal, author convention:
    # focal CE exponent gamma; class Tversky exponent (1-gamma).
    # Fractional powers have infinite derivatives at exactly zero; sigmoid can
    # saturate there for finite extreme logits. Clamp focal modulation only.
    q = p.clamp(1e-7,1-1e-7)
    focal_ce = (config.delta*target*(1-q).pow(config.unified_gamma)*F.softplus(-logits)
                +(1-config.delta)*(1-target)*q.pow(config.unified_gamma)*F.softplus(logits))
    focal_ce = (focal_ce*valid).sum(dims)/n
    bg_tp = ((1-p)*(1-target)*valid).sum(dims)
    bg_ti = (bg_tp+config.smooth)/(bg_tp+config.delta*fp+(1-config.delta)*fn+config.smooth)
    unified_region = ((1-ti).clamp(min=1e-7).pow(1-config.unified_gamma)
                      +(1-bg_ti).clamp(min=1e-7).pow(1-config.unified_gamma))/2
    uf = config.unified_weight*focal_ce+(1-config.unified_weight)*unified_region
    total = {'bce_dice':bce+dice,'focal_tversky':ft,'unified_focal_symmetric':uf}[config.mode]
    return {key:value.mean() for key,value in {'total':total,'bce':bce,'dice':dice,'focal_tversky':ft,
                                              'unified_focal_ce':focal_ce,'unified_region':unified_region}.items()}


@dataclass(frozen=True)
class PostprocessConfig:
    threshold: float = .5
    policy: str = 'all'
    min_pixels: int = 16  # native pixels, explicitly different from historical min16 on 256

    def __post_init__(self):
        if not 0 < self.threshold < 1 or self.policy not in ('all','largest','min_pixels') or self.min_pixels < 1:
            raise ValueError('Invalid postprocessing')


def postprocess(probability, config):
    if probability.ndim != 2 or not np.isfinite(probability).all():
        raise ValueError('Expected finite native probability map')
    raw = (probability >= config.threshold).astype(np.uint8)
    if config.policy == 'all' or not raw.any():
        return raw, raw.copy()
    n, ids, stats, _ = cv2.connectedComponentsWithStats(raw,8)
    areas = stats[1:,cv2.CC_STAT_AREA]
    keep = [int(np.argmax(areas))+1] if config.policy=='largest' else (np.flatnonzero(areas>=config.min_pixels)+1).tolist()
    return raw, np.isin(ids,keep).astype(np.uint8)


def predict_arrays(model, image, preprocess, post, device='cpu'):
    """Shared native output path for evaluation and versioned-bundle serving."""
    x, _, _, g = prepare(image,preprocess)
    model.eval()
    with torch.inference_mode():
        logits = model(torch.from_numpy(x).unsqueeze(0).unsqueeze(0).to(device))
        if not torch.isfinite(logits).all():
            raise RuntimeError('Nonfinite model output')
        probability = inverse(logits.sigmoid()[0,0].cpu().numpy(),g,probability=True)
    raw, delivered = postprocess(probability,post)
    return probability, raw, delivered, g


@lru_cache(maxsize=2)
def load_bundle(bundle_path, bundle_sha, checkpoint_sha, device='cpu'):
    path = Path(bundle_path)
    document = json.loads(path.read_text(encoding='utf-8'))
    if sha(path) != bundle_sha or document['output_contract'] != CONTRACT or document['architecture'] != 'AttentionUNet64':
        raise ValueError('Bundle identity/contract mismatch')
    checkpoint = (path.parent / document['checkpoint']).resolve()
    if sha(checkpoint) != checkpoint_sha or checkpoint_sha != document['checkpoint_sha256']:
        raise ValueError('Checkpoint checksum mismatch')
    model = LogitsAttentionUNet().to(device)
    model.load_state_dict(torch.load(checkpoint,map_location=device,weights_only=True),strict=True)
    model.eval()
    return model, PreprocessConfig(**document['preprocess']), PostprocessConfig(**document['postprocess']), document


def predict_bundle(image_path,bundle_path,device='cpu'):
    path = Path(bundle_path).resolve()
    document = json.loads(path.read_text(encoding='utf-8'))
    model, preprocess, post, document = load_bundle(str(path),sha(path),document['checkpoint_sha256'],device)
    image = cv2.imread(str(image_path),cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError('Image decode failed')
    probability, raw, delivered, g = predict_arrays(model,image,preprocess,post,device)
    return {'probability':probability,'raw_mask':raw,'mask':delivered,
            'metadata':dict(output_contract=CONTRACT,checkpoint_sha256=document['checkpoint_sha256'],
                            bundle_sha256=sha(path),geometry=asdict(g),preprocess=asdict(preprocess),
                            postprocess=asdict(post),component_area_units='native pixels',
                            calibration_status=document['calibration_status'])}
