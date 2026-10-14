"""One GT-foreground BCE coefficient over the frozen hard-factor2 loss.

Coefficient1 delegates without reconstructing the original arithmetic. Only
valid GT-positive pixel BCE receives the coefficient5 offset; background,
normal-image gradients, Dice, source weights and batch reduction are retained.
Running fixtures uses synthetic CPU tensors and reads no project dataset.
"""
import math
from pathlib import Path
import sys

import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.ai_hard_example_loss import hard_example_loss


def foreground_bce_loss(mask_logits, presence_logits, target, valid, positive,
                        example_weights, loss_config, presence_weight,
                        foreground_bce_coefficient):
    """Add mean_i[w_i*(k-1)*mean_valid(softplus(-z_i)*y_i)]."""
    coefficient = foreground_bce_coefficient
    if (isinstance(coefficient, bool) or not isinstance(coefficient, (int, float))
            or not math.isfinite(coefficient) or coefficient not in (1, 5)):
        raise ValueError('Registered foreground BCE coefficient 1 or 5 required')
    if presence_weight != 0 or loss_config.mode != 'bce_dice':
        raise ValueError('Frozen mask-only BCE+Dice objective required')
    if (mask_logits.ndim != 4 or mask_logits.shape[0] < 1 or mask_logits.shape[1] != 1
            or mask_logits.shape != target.shape or mask_logits.shape != valid.shape):
        raise ValueError('Matching nonempty B1HW logits/target/valid required')
    if (positive.ndim != 1 or len(positive) != len(mask_logits)
            or positive.dtype != torch.bool or presence_logits.shape != positive.shape):
        raise ValueError('One explicit boolean source label and head logit per image required')
    tensors = (mask_logits, presence_logits, target, valid, positive, example_weights)
    if any(t.device != mask_logits.device for t in tensors):
        raise ValueError('All loss tensors must share a device')
    if (not mask_logits.is_floating_point() or presence_logits.dtype != mask_logits.dtype
            or target.dtype != mask_logits.dtype or valid.dtype != mask_logits.dtype
            or example_weights.dtype != mask_logits.dtype):
        raise ValueError('Consistent floating output/target/valid/weight dtype required')
    if not all(bool(torch.isfinite(t).all()) for t in tensors):
        raise ValueError('Finite outputs, labels, weights and target/valid required')
    if not bool(((target == 0) | (target == 1)).all()) or not bool(((valid == 0) | (valid == 1)).all()):
        raise ValueError('Binary target and valid tensors required')
    dims = (1, 2, 3)
    counts = valid.sum(dims)
    if not bool((counts > 0).all()):
        raise ValueError('Every source image must contain valid pixels')
    if not torch.equal(positive, (target * valid).sum(dims) > 0):
        raise ValueError('Erased-positive, invalid-only target or source-label mismatch rejected')
    base = hard_example_loss(mask_logits, presence_logits, target, valid, positive,
                             example_weights, loss_config, presence_weight)
    if coefficient == 1:
        # Preserve exact base scalar and gradient graph, without a +0 reduction.
        return dict(base, foreground_bce_offset=mask_logits.new_zeros(()))
    per_source_foreground_bce = (F.softplus(-mask_logits) * target * valid).sum(dims) / counts
    offset = ((coefficient - 1) * example_weights * per_source_foreground_bce).mean()
    return dict(base, total=base['total'] + offset,
                segmentation_total=base['segmentation_total'] + offset,
                bce=base['bce'] + offset, foreground_bce_offset=offset)


def _output_gradients(loss, logits, head):
    return torch.autograd.grad(loss, (logits, head), retain_graph=True, allow_unused=True)


def fixtures():
    """Synthetic batch2 CPU scalar/analytic-gradient and rejection checks."""
    from medvision_pipeline import LossConfig
    config = LossConfig(mode='bce_dice')
    results = []
    for dtype in (torch.float32, torch.float64):
        for pattern in ('mixed', 'all_normal', 'all_positive'):
            for extreme in (False, True):
                values = [[[-2., 1., 0.], [2., -.5, 3.]], [[1., -1., 2.], [-2., 3., -3.]]]
                logits = torch.tensor(values, dtype=dtype).unsqueeze(1)
                if extreme:
                    logits *= 400
                logits.requires_grad_()
                head = torch.tensor([-.4, .7], dtype=dtype, requires_grad=True)
                target = torch.zeros_like(logits)
                positive = torch.tensor([pattern != 'all_normal', pattern == 'all_positive'])
                if positive[0]:
                    target[0, 0, 0, 0] = 1
                if positive[1]:
                    target[1, 0, 1, 0] = 1
                valid = torch.ones_like(logits)
                valid[0, 0, 1, 2] = 0
                valid[1, 0, 0, 2] = 0
                weights = torch.tensor([1.6378737541528239, .7645310435931308], dtype=dtype)
                original = hard_example_loss(logits, head, target, valid, positive, weights, config, 0)
                neutral = foreground_bce_loss(logits, head, target, valid, positive, weights, config, 0, 1)
                assert all(torch.equal(original[k], neutral[k]) for k in original)
                og = _output_gradients(original['total'], logits, head)
                ng = _output_gradients(neutral['total'], logits, head)
                assert og[1] is None and ng[1] is None and torch.equal(og[0], ng[0])
                candidate = foreground_bce_loss(logits, head, target, valid, positive, weights, config, 0, 5)
                assert all(bool(torch.isfinite(v).all()) for v in candidate.values())
                cg = _output_gradients(candidate['total'], logits, head)
                assert cg[1] is None and bool(torch.isfinite(cg[0]).all())
                background = (target == 0) & valid.bool()
                assert torch.equal(cg[0][background], og[0][background])
                assert torch.equal(cg[0][~positive], og[0][~positive])
                assert torch.equal(original['dice'], candidate['dice'])
                assert torch.equal(original['presence_bce'], candidate['presence_bce'])
                assert torch.equal(cg[0][valid == 0], torch.zeros_like(cg[0][valid == 0]))
                # Independent weighted positive/negative log-loss and Dice.
                terms = []
                for i in range(2):
                    z = logits[i, 0][valid[i, 0].bool()]
                    y = target[i, 0][valid[i, 0].bool()]
                    prob = z.sigmoid()
                    bce_i = ((1 - y) * F.softplus(z) + 5 * y * F.softplus(-z)).mean()
                    dice_i = 1 - (2 * (prob * y).sum() + config.smooth) / (prob.sum() + y.sum() + config.smooth)
                    terms.append(weights[i] * (bce_i + dice_i))
                expected = torch.stack(terms).mean()
                eg = torch.autograd.grad(expected, logits, retain_graph=True)[0]
                tolerance = 2e-6 if dtype == torch.float32 else 1e-12
                assert torch.allclose(candidate['total'], expected, atol=tolerance, rtol=tolerance)
                assert torch.allclose(cg[0], eg, atol=tolerance, rtol=tolerance)
                counts = valid.sum((1, 2, 3)).view(-1, 1, 1, 1)
                analytic_offset = 4 * weights.view(-1, 1, 1, 1) * (logits.sigmoid() - 1) * target * valid / counts / len(logits)
                assert torch.allclose(cg[0] - og[0], analytic_offset, atol=tolerance, rtol=tolerance)
                results.append(dict(dtype=str(dtype), pattern=pattern, finite_extremes=extreme,
                    coefficient1_exact_scalar_output_gradient_parity=True,
                    coefficient5_independent_scalar_gradient_parity=True,
                    coefficient5_analytic_offset_gradient_parity=True,
                    normal_and_positive_background_gradients_exactly_unchanged=True,
                    Dice_and_presence_unchanged=True, invalid_pixel_gradient_zero=True))
    logits = torch.zeros((2, 1, 2, 2), dtype=torch.float64, requires_grad=True)
    head = torch.zeros(2, dtype=torch.float64, requires_grad=True)
    target, valid = torch.zeros_like(logits), torch.ones_like(logits)
    weights, labels = torch.ones(2, dtype=torch.float64), torch.tensor([False, False])
    invalid_target = target.clone()
    invalid_target[0, 0, 0, 0] = 1
    hidden = valid.clone()
    hidden[0, 0, 0, 0] = 0
    nonbinary_target, nonbinary_valid = target.clone(), valid.clone()
    nonbinary_target[0, 0, 0, 0] = .5
    nonbinary_valid[0, 0, 0, 0] = .5
    nonfinite_logits = logits.detach().clone()
    nonfinite_logits[0, 0, 0, 0] = float('nan')
    rejected = []
    bad_inputs = [
        ('erased_positive', logits, target, valid, torch.tensor([True, False]), weights, 1),
        ('positive_only_in_invalid_area', logits, invalid_target, hidden, torch.tensor([True, False]), weights, 5),
        ('source_label_mismatch', logits, invalid_target, valid, labels, weights, 5),
        ('no_valid_pixels', logits, target, torch.zeros_like(valid), labels, weights, 5),
        ('nonbinary_target', logits, nonbinary_target, valid, labels, weights, 5),
        ('nonbinary_valid', logits, target, nonbinary_valid, labels, weights, 5),
        ('nonfinite_output', nonfinite_logits, target, valid, labels, weights, 5),
        ('invalid_weight', logits, target, valid, labels, torch.tensor([.49, 1.], dtype=torch.float64), 5),
        ('invalid_coefficient', logits, target, valid, labels, weights, 10),
        ('boolean_coefficient', logits, target, valid, labels, weights, True)]
    for name, z, t, v, source_labels, w, coefficient in bad_inputs:
        try:
            foreground_bce_loss(z, head, t, v, source_labels, w, config, 0, coefficient)
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError('Invalid fixture accepted: ' + name)
    return dict(status='foreground_BCE_synthetic_CPU_parity_fixtures_passed', batch_size=2,
                cases=results, rejected_inputs=rejected, model_training_performed=False,
                dataset_reads=0, GPU_work_performed=False)


if __name__ == '__main__':
    import json
    print(json.dumps(fixtures(), indent=2))
