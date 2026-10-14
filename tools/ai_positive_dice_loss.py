"""One positive-case Dice coefficient over the frozen hard-factor2 objective.

Coefficient1 delegates to the existing loss without changing its arithmetic.
Coefficient2 retains all-image BCE, normal Dice, per-source weights and batch
reduction. Importing or running fixtures does not train or read project data.
"""
import math
from pathlib import Path
import sys

import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.ai_hard_example_loss import hard_example_loss


def positive_dice_loss(mask_logits, presence_logits, target, valid, positive,
                       example_weights, loss_config, presence_weight,
                       positive_dice_coefficient):
    """Preserve baseline plus a weighted per-source positive-Dice offset."""
    coefficient = positive_dice_coefficient
    if isinstance(coefficient, bool) or not isinstance(coefficient, (int, float)) or not math.isfinite(coefficient) or coefficient not in (1, 2):
        raise ValueError('Registered positive Dice coefficient1 or2 required')
    if presence_weight != 0 or loss_config.mode != 'bce_dice':
        raise ValueError('Frozen mask-only BCE+Dice objective required')
    if mask_logits.shape != target.shape or mask_logits.shape != valid.shape or mask_logits.ndim != 4:
        raise ValueError('Matching BCHW logits/target/valid required')
    if positive.ndim != 1 or len(positive) != len(mask_logits) or positive.dtype != torch.bool:
        raise ValueError('One explicit boolean positive source label per image required')
    if not all(bool(torch.isfinite(v).all()) for v in (mask_logits, presence_logits, target, valid)):
        raise ValueError('Finite outputs and target/valid tensors required')
    if not bool(((target == 0) | (target == 1)).all()) or not bool(((valid == 0) | (valid == 1)).all()):
        raise ValueError('Binary target/valid tensors required')
    dims = (1, 2, 3)
    if not torch.equal(positive, target.sum(dims) > 0):
        raise ValueError('Erased-positive or mislabeled target rejected like the frozen dataset')
    # The frozen base rejects zero-valid-pixel images and bounded weight errors.
    base = hard_example_loss(mask_logits, presence_logits, target, valid, positive,
                             example_weights, loss_config, presence_weight)
    if coefficient == 1:
        # No reconstructed reduction or +0: exact original scalar/gradient path.
        return dict(base, positive_dice_offset=mask_logits.new_zeros(()))
    probability = mask_logits.sigmoid()
    tp = (probability * target * valid).sum(dims)
    fn = ((1 - probability) * target * valid).sum(dims)
    fp = (probability * (1 - target) * valid).sum(dims)
    per_dice = 1 - (2 * tp + loss_config.smooth) / (2 * tp + fp + fn + loss_config.smooth)
    offset = ((coefficient - 1) * example_weights * positive.to(per_dice.dtype) * per_dice).mean()
    return dict(base, total=base['total'] + offset,
                segmentation_total=base['segmentation_total'] + offset,
                dice=base['dice'] + offset, positive_dice_offset=offset)


def _same_gradients(left, right, outputs):
    lg = torch.autograd.grad(left, outputs, retain_graph=True, allow_unused=True)
    rg = torch.autograd.grad(right, outputs, retain_graph=True, allow_unused=True)
    assert all((l is None and r is None) or (l is not None and r is not None and torch.equal(l, r))
               for l, r in zip(lg, rg))
    return lg


def fixtures():
    """Synthetic CPU fixtures only, including batch2 and valid-pixel exclusion."""
    from medvision_pipeline import LossConfig
    config = LossConfig(mode='bce_dice')
    results = []
    for dtype in (torch.float32, torch.float64):
        for pattern in ('mixed', 'all_normal', 'all_positive'):
            for extreme in (False, True):
                values = [[[-2., 1., 0.], [2., -.5, 3.]], [[1., -1., 2.], [0., 3., -3.]]]
                logits = torch.tensor(values, dtype=dtype).unsqueeze(1)
                if extreme:
                    logits = logits * 400
                logits.requires_grad_()
                head = torch.tensor([-.4, .7], dtype=dtype, requires_grad=True)
                target = torch.zeros_like(logits)
                positive = torch.tensor([pattern != 'all_normal', pattern == 'all_positive'])
                if positive[0]: target[0, 0, 0, 0] = 1
                if positive[1]: target[1, 0, 1, 0] = 1
                valid = torch.ones_like(logits)
                valid[0, 0, 1, 2] = 0
                valid[1, 0, 0, 2] = 0
                weights = torch.tensor([1.6378737541528239, .7645310435931308], dtype=dtype)
                original = hard_example_loss(logits, head, target, valid, positive, weights, config, 0)
                neutral = positive_dice_loss(logits, head, target, valid, positive, weights, config, 0, 1)
                assert all(torch.equal(original[k], neutral[k]) for k in original)
                _same_gradients(original['total'], neutral['total'], (logits, head))
                candidate = positive_dice_loss(logits, head, target, valid, positive, weights, config, 0, 2)
                assert all(bool(torch.isfinite(v).all()) for v in candidate.values())
                cg = torch.autograd.grad(candidate['total'], (logits, head), retain_graph=True, allow_unused=True)
                og = torch.autograd.grad(original['total'], (logits, head), retain_graph=True, allow_unused=True)
                assert cg[1] is None and og[1] is None
                assert torch.equal(cg[0][~positive], og[0][~positive])
                assert torch.equal(original['bce'], candidate['bce'])
                assert torch.equal(cg[0][valid == 0], torch.zeros_like(cg[0][valid == 0]))
                terms = []
                for i in range(2):
                    z = logits[i, 0][valid[i, 0].bool()]
                    y = target[i, 0][valid[i, 0].bool()]
                    prob = z.sigmoid()
                    bce = F.binary_cross_entropy_with_logits(z, y)
                    dice = 1 - (2 * (prob * y).sum() + config.smooth) / (prob.sum() + y.sum() + config.smooth)
                    terms.append(weights[i] * (bce + (2 if positive[i] else 1) * dice))
                expected = torch.stack(terms).mean()
                tolerance = 2e-6 if dtype == torch.float32 else 1e-12
                assert torch.allclose(candidate['total'], expected, atol=tolerance, rtol=tolerance)
                eg = torch.autograd.grad(expected, logits, retain_graph=True)[0]
                assert torch.allclose(cg[0], eg, atol=tolerance, rtol=tolerance)
                results.append(dict(dtype=str(dtype), pattern=pattern, finite_extremes=extreme,
                                    coefficient1_exact_scalar_output_gradient_parity=True,
                                    coefficient2_independent_formula_gradient_parity=True,
                                    normal_output_gradients_unchanged=True, invalid_pixel_gradient_zero=True))
    # No valid pixels and an erased-positive target must be rejected, not clamped.
    logits = torch.zeros((2, 1, 2, 2), dtype=torch.float64, requires_grad=True)
    head = torch.zeros(2, dtype=torch.float64, requires_grad=True)
    target = torch.zeros_like(logits)
    valid = torch.ones_like(logits)
    weights = torch.ones(2, dtype=torch.float64)
    rejected = []
    for name, t, v, labels, coefficient in (
        ('erased_positive', target, valid, torch.tensor([True, False]), 1),
        ('no_valid_pixels', target, torch.zeros_like(valid), torch.tensor([False, False]), 2),
        ('invalid_coefficient', target, valid, torch.tensor([False, False]), 3)):
        try:
            positive_dice_loss(logits, head, t, v, labels, weights, config, 0, coefficient)
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError('Invalid fixture accepted: ' + name)
    return dict(status='positive_Dice_synthetic_CPU_parity_fixtures_passed', batch_size=2,
                cases=results, rejected_inputs=rejected, model_training_performed=False,
                dataset_reads=0, GPU_work_performed=False)


if __name__ == '__main__':
    import json
    print(json.dumps(fixtures(), indent=2))
