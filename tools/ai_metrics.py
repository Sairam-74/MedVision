"""Explicit research metrics; no inference, fitting, or test-set access."""
import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import (accuracy_score, average_precision_score, brier_score_loss,
                             confusion_matrix, precision_recall_curve, roc_auc_score, roc_curve)


def ratio(a, b):
    return float(a / b) if b else None


def classification(cases):
    y = np.array([c['positive'] for c in cases], dtype=int)
    pred = np.array([c['prediction_present'] for c in cases], dtype=int)
    score = np.array([c['case_score'] for c in cases], dtype=float)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel().tolist()
    return dict(n=len(cases), positive=int(y.sum()), normal=int((1-y).sum()),
                accuracy=float(accuracy_score(y, pred)), precision=ratio(tp, tp+fp),
                recall_sensitivity=ratio(tp, tp+fn), specificity=ratio(tn, tn+fp),
                f1=ratio(2*tp, 2*tp+fp+fn), false_positive_rate=ratio(fp, fp+tn),
                false_negative_rate=ratio(fn, fn+tp),
                auroc=float(roc_auc_score(y, score)) if len(set(y)) == 2 else None,
                auprc_average_precision=float(average_precision_score(y, score)) if y.sum() else None,
                confusion_matrix=dict(tn=tn, fp=fp, fn=fn, tp=tp),
                score_definition='maximum float32 model-grid sigmoid pixel output; uncalibrated proxy, NOT a case probability')


def segmentation(cases):
    positive = [c for c in cases if c['positive']]
    tp, fp, fn = [sum(c[k] for c in cases) for k in ('tp_pixels', 'fp_pixels', 'fn_pixels')]
    defined_precision = [c['segmentation_precision'] for c in positive if c['segmentation_precision'] is not None]
    return dict(n_positive=len(positive), mean_positive_dice=float(np.mean([c['dice'] for c in positive])) if positive else None,
                mean_positive_iou=float(np.mean([c['iou'] for c in positive])) if positive else None,
                mean_positive_precision_nonempty=float(np.mean(defined_precision)) if defined_precision else None,
                mean_positive_recall=float(np.mean([c['segmentation_recall'] for c in positive])) if positive else None,
                global_dice=ratio(2*tp, 2*tp+fp+fn), global_iou=ratio(tp, tp+fp+fn),
                global_pixel_precision=ratio(tp, tp+fp), global_pixel_recall=ratio(tp, tp+fn),
                pixel_counts=dict(tp=tp, fp=fp, fn=fn),
                empty_policy='Normals excluded from positive macro Dice/IoU. Missed positive Dice/IoU/recall=0; empty prediction precision=null. Global metrics include normal false-positive pixels.')


def calibration(cases, bins=10):
    y = np.array([c['positive'] for c in cases], dtype=float)
    score = np.array([c['case_score'] for c in cases], dtype=float)
    bucket = np.minimum((score*bins).astype(int), bins-1)
    curve, ece = [], 0.
    for i in range(bins):
        mask = bucket == i
        p, observed = (float(score[mask].mean()), float(y[mask].mean())) if mask.any() else (None, None)
        if mask.any():
            ece += float(mask.mean())*abs(p-observed)
        curve.append(dict(lower=i/bins, upper=(i+1)/bins, n=int(mask.sum()), mean_score=p, observed_fracture_fraction=observed))
    return dict(brier_score=float(brier_score_loss(y, score)), expected_calibration_error=ece,
                bins=bins, binning='equal-width; final bin includes 1', reliability_curve=curve,
                score_exactly_one_count=int((score == 1).sum()),
                interpretation='Diagnostics of treating maximum pixel output AS IF it were a case probability. The serving model does not expose a calibrated case probability; no clinical confidence claim.')


def curves(cases):
    y = [int(c['positive']) for c in cases]
    score = [c['case_score'] for c in cases]
    fpr, tpr, rt = roc_curve(y, score)
    precision, recall, pt = precision_recall_curve(y, score)
    return dict(roc=dict(fpr=fpr.tolist(), tpr=tpr.tolist(), thresholds=[float(v) if np.isfinite(v) else None for v in rt]),
                precision_recall=dict(precision=precision.tolist(), recall=recall.tolist(), thresholds=pt.tolist()))


def matched_regions(iou, threshold):
    """One-to-one maximum-cardinality matching with IoU as secondary objective."""
    if not iou.size:
        return 0
    reward = (iou >= threshold).astype(float)*2 + iou/max(1, min(iou.shape))
    rows, cols = linear_sum_assignment(reward, maximize=True)
    return int((iou[rows, cols] >= threshold).sum())


def box_iou(a, b):
    if not len(a) or not len(b):
        return np.zeros((len(a), len(b)))
    a, b = np.array(a, float), np.array(b, float)
    inter = np.maximum(0, np.minimum(a[:, None, 2:], b[None, :, 2:]) - np.maximum(a[:, None, :2], b[None, :, :2])).prod(2)
    area_a = (a[:, 2:]-a[:, :2]).prod(1)
    area_b = (b[:, 2:]-b[:, :2]).prod(1)
    return inter/np.maximum(area_a[:, None]+area_b[None, :]-inter, 1)


def localization(cases):
    """Detection AP for boxes derived from .90 mask components, with grouped ties.

    Predictions absent below the segmentation gate cannot be recovered by AP.
    This is a component-box proxy, not a trained detector or COCO evaluator.
    """
    gt_count = sum(c['gt_instances'] for c in cases)
    predictions = [(p['score'], c['image_id'], p['box']) for c in cases for p in c['regions']]
    predictions.sort(key=lambda x: -x[0])
    targets = {c['image_id']: c['gt_boxes'] for c in cases}
    aps, per_threshold = [], []
    for threshold in np.arange(.5, .951, .05):
        threshold = round(float(threshold), 2)
        used = {k: set() for k in targets}
        tp = fp = 0
        points = []
        # Evaluate equal-score predictions as one batch; avoid order-created AP.
        start = 0
        while start < len(predictions):
            end = start+1
            while end < len(predictions) and predictions[end][0] == predictions[start][0]:
                end += 1
            grouped = {}
            for _, image, box in predictions[start:end]:
                grouped.setdefault(image, []).append(box)
            for image, boxes in grouped.items():
                remaining = [i for i in range(len(targets[image])) if i not in used[image]]
                iou = box_iou(boxes, [targets[image][i] for i in remaining])
                matched = 0
                if iou.size:
                    reward = (iou >= threshold).astype(float)*2+iou/max(1, min(iou.shape))
                    rr, cc = linear_sum_assignment(reward, maximize=True)
                    for r, col in zip(rr, cc):
                        if iou[r, col] >= threshold:
                            used[image].add(remaining[col]); matched += 1
                tp += matched; fp += len(boxes)-matched
            points.append((tp/gt_count if gt_count else 0., tp/(tp+fp)))
            start = end
        # 101 recall levels, interpolated precision envelope, one class.
        ap = float(np.mean([max([p for r, p in points if r >= level], default=0.) for level in np.linspace(0, 1, 101)])) if gt_count else None
        aps.append(ap)
        per_threshold.append(dict(iou=threshold, ap101=ap, tp=tp, fp=fp, fn=gt_count-tp, precision=ratio(tp, tp+fp), recall=ratio(tp, gt_count)))
    return dict(component_box_map50=aps[0], component_box_map50_95=float(np.mean(aps)) if gt_count else None,
                ground_truth_instances=gt_count, predicted_regions=len(predictions), by_iou=per_threshold,
                method='Native predicted connected-component enclosing boxes vs enclosing boxes of individual COCO polygon rasterizations; confidence=max pixel output per component; masks gated at baseline .90; one-to-one, equal-score batching, 101-point interpolated AP. Not canonical COCO mAP or a separately trained detection head.')
