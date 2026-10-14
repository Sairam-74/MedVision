"""Bounded TRAIN example emphasis without resampling or changing pixel loss.

Prepared for a future registered matched experiment. Importing this module does
not train a model or apply weights to any existing experiment.
"""
import torch
import torch.nn.functional as F

from tools.ai_presence_model import balanced_presence_loss
from tools.train_reliability_candidate import candidate_loss


def hard_example_loss(mask_logits, presence_logits, target, valid, positive,
                      example_weights, loss_config, presence_weight):
    if loss_config.mode != 'bce_dice' or presence_weight not in (0, 1):
        raise ValueError('Registered BCE+Dice objective and fixed presence factor required')
    if example_weights.shape != positive.shape or example_weights.ndim != 1:
        raise ValueError('One explicit weight per batch source image required')
    if not bool(torch.isfinite(example_weights).all()) or not bool(((example_weights >= .5) & (example_weights <= 2)).all()):
        raise ValueError('Finite bounded example weights in[0.5,2] required')
    base = candidate_loss(mask_logits, target, valid, loss_config, 1., positive)
    dims = (1, 2, 3)
    n = valid.sum(dims)
    probability = mask_logits.sigmoid()
    bce = (F.binary_cross_entropy_with_logits(mask_logits, target, reduction='none') * valid).sum(dims) / n
    tp = (probability * target * valid).sum(dims)
    fn = ((1 - probability) * target * valid).sum(dims)
    fp = (probability * (1 - target) * valid).sum(dims)
    dice = 1 - (2 * tp + loss_config.smooth) / (2 * tp + fp + fn + loss_config.smooth)
    # Use baseline plus per-image offset so the factor1 reference reproduces
    # its exact scalar reduction and gradient; never normalize by batch weights.
    bce_offset = ((example_weights - 1) * bce).mean()
    dice_offset = ((example_weights - 1) * dice).mean()
    segmentation = base['total'] + bce_offset + dice_offset
    class_weights = torch.where(positive.bool(), 2808 / (2 * 493), 2808 / (2 * 2315))
    per_presence = F.binary_cross_entropy_with_logits(presence_logits, positive.to(presence_logits.dtype), reduction='none') * class_weights
    presence = balanced_presence_loss(presence_logits, positive) + ((example_weights - 1) * per_presence).mean()
    total = segmentation + presence if presence_weight else segmentation
    return dict(total=total, segmentation_total=segmentation,
                bce=base['bce'] + bce_offset, dice=base['dice'] + dice_offset,
                presence_bce=presence)


def fixtures():
    from medvision_pipeline import LossConfig
    config = LossConfig(mode='bce_dice')
    logits = torch.tensor([[[[-2., 1.], [0., 2.]]], [[[1., -1.], [2., 0.]]]], dtype=torch.float64, requires_grad=True)
    head = torch.tensor([-.4, .7], dtype=torch.float64, requires_grad=True)
    target = torch.tensor([[[[1., 0.], [0., 0.]]], [[[0., 0.], [0., 0.]]]], dtype=torch.float64)
    valid = torch.tensor([[[[1., 1.], [1., 0.]]], [[[1., 1.], [1., 1.]]]], dtype=torch.float64)
    positive = torch.tensor([True, False])
    unit = torch.ones(2, dtype=torch.float64)
    for presence_weight in (0, 1):
        base = candidate_loss(logits, target, valid, config, 1., positive)['total']
        if presence_weight:
            base = base + balanced_presence_loss(head, positive)
        candidate = hard_example_loss(logits, head, target, valid, positive, unit, config, presence_weight)['total']
        assert torch.equal(base, candidate)
        bg = torch.autograd.grad(base, (logits, head), retain_graph=True, allow_unused=True)
        cg = torch.autograd.grad(candidate, (logits, head), retain_graph=True, allow_unused=True)
        assert all((x is None and y is None) or (x is not None and y is not None and torch.equal(x, y)) for x, y in zip(bg, cg))
    weights = torch.tensor([1.6, 2/3], dtype=torch.float64)
    measured = hard_example_loss(logits, head, target, valid, positive, weights, config, 1)['total']
    # Independent per-source calculation, including invalid-pixel exclusion.
    terms = []
    for i in range(2):
        zi = logits[i, 0][valid[i, 0].bool()]
        yi = target[i, 0][valid[i, 0].bool()]
        pi = zi.sigmoid()
        bce_i = F.binary_cross_entropy_with_logits(zi, yi)
        dice_i = 1 - (2 * (pi * yi).sum() + config.smooth) / (pi.sum() + yi.sum() + config.smooth)
        # Existing presence helper intentionally constructs float32 class
        # constants even for a float64 probe; preserve that exact objective.
        cw = float(torch.tensor(2808/(2*(493 if positive[i] else 2315)), dtype=torch.float32))
        presence_i = F.binary_cross_entropy_with_logits(head[i], positive[i].to(head.dtype)) * cw
        terms.append(weights[i] * (bce_i + dice_i + presence_i))
    expected = torch.stack(terms).mean()
    assert torch.allclose(measured, expected, atol=1e-12, rtol=1e-12)
    mg = torch.autograd.grad(measured, (logits, head), retain_graph=True)
    eg = torch.autograd.grad(expected, (logits, head), retain_graph=True)
    assert all(torch.allclose(x, y, atol=1e-12, rtol=1e-12) for x, y in zip(mg, eg))
    assert mg[0][0, 0, 1, 1] == 0  # invalid pixel cannot acquire a gradient
    for bad in (torch.tensor([.49, 1.]), torch.tensor([1., 2.01]), torch.tensor([float('nan'), 1.])):
        try:
            hard_example_loss(logits, head, target, valid, positive, bad, config, 1)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid example weight accepted')
    return dict(status='weighted_scalar_gradient_and_neutral_parity_fixtures_passed',
                unit_weights_exact_scalar_and_gradient_parity=True,
                weighted_total=float(measured.detach()), independently_calculated_total=float(expected.detach()),
                invalid_pixel_gradient=0, model_training_performed=False)


if __name__ == '__main__':
    import json
    print(json.dumps(fixtures(), indent=2))
