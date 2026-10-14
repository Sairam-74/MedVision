"""Research-only shared Attention U-Net with an independent presence output.

Existing application/model modules and mask output parameters remain unchanged.
"""
import math
from pathlib import Path
import sys
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import medvision_pipeline as p

CONTRACT = 'medvision.shared_unet_presence_logits.v1'
ARCHITECTURE = 'AttentionUNet64PresenceGAP'


class PresenceAttentionUNet(p.LogitsAttentionUNet):
    output_contract = CONTRACT

    def __init__(self, train_prior=493/2808):
        super().__init__()
        self.presence = nn.Linear(1024, 1)
        with torch.no_grad():
            self.presence.bias.fill_(math.log(train_prior/(1-train_prior)))

    def forward(self, x):
        # Same encoder/decoder operations and state names as the preserved model.
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        e4 = self.enc4(self.pool(e3))
        b = self.bottleneck(self.pool(e4))
        presence = self.presence(b.mean(dim=(2, 3))).squeeze(1)
        d4 = self.up4(b)
        d4 = self.dec4(torch.cat([d4, self.att4(e4, d4)], dim=1))
        d3 = self.up3(d4)
        d3 = self.dec3(torch.cat([d3, self.att3(e3, d3)], dim=1))
        d2 = self.up2(d3)
        d2 = self.dec2(torch.cat([d2, self.att2(e2, d2)], dim=1))
        d1 = self.up1(d2)
        d1 = self.dec1(torch.cat([d1, self.att1(e1, d1)], dim=1))
        return dict(mask_logits=self.final(d1), presence_logits=presence)

    def load_shared(self, state):
        missing, unexpected = self.load_state_dict(state, strict=False)
        if set(missing) != {'presence.weight', 'presence.bias'} or unexpected:
            raise ValueError('Only the two registered presence-head tensors may be new')


def tensor_digest(state):
    import hashlib
    digest = hashlib.sha256()
    for name, tensor in sorted(state.items()):
        digest.update(name.encode())
        digest.update(str(tensor.dtype).encode())
        digest.update(str(tuple(tensor.shape)).encode())
        digest.update(tensor.detach().cpu().numpy().tobytes())
    return digest.hexdigest()


def balanced_presence_loss(logits, positive, n_positive=493, n_normal=2315):
    import torch.nn.functional as F
    if logits.ndim != 1 or logits.shape != positive.shape:
        raise ValueError('Explicit case labels must align with presence logits')
    total = n_positive+n_normal
    weights = torch.where(positive.bool(), total/(2*n_positive), total/(2*n_normal))
    return (F.binary_cross_entropy_with_logits(logits, positive.to(logits.dtype), reduction='none')*weights).mean()


def review_group(head_positive, mask_positive):
    return ('classifier+' if head_positive else 'classifier-')+'/'+('mask+' if mask_positive else 'mask-')


def selection_key(metrics, dice_floor=.5237965562512774, iou_floor=.3775685932913787):
    c, s = metrics['classification'], metrics['delivered']
    counts = c['confusion_matrix']
    ratios = (counts['tp']/79, counts['tn']/342, s['mean_positive_dice']/dice_floor,
              s['mean_positive_iou']/iou_floor)
    feasible = counts['tp']>=79 and counts['tn']>=342 and c['accuracy']>=.9 and ratios[2]>=1 and ratios[3]>1
    # Common rule in BOTH arms; all-normal collapse has a zero bottleneck score.
    return (int(feasible), min(ratios), sum(ratios)/len(ratios))
