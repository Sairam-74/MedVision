# Presence candidate native validation audit

Full463 frozen cases. Primary classification is conservative review-alert burden; masks always remain independent. Head-only gains do not authorize promotion.

{
  "classification": {
    "n": 463,
    "positive": 83,
    "normal": 380,
    "accuracy": 0.5896328293736501,
    "precision": 0.2816326530612245,
    "recall_sensitivity": 0.8313253012048193,
    "specificity": 0.5368421052631579,
    "f1": 0.42073170731707316,
    "false_positive_rate": 0.4631578947368421,
    "false_negative_rate": 0.1686746987951807,
    "auroc": 0.8144261255548509,
    "auprc_average_precision": 0.6174187406746432,
    "confusion_matrix": {
      "tn": 204,
      "fp": 176,
      "fn": 14,
      "tp": 69
    },
    "score_definition": "Independent mask presence, maximum pixel proxy"
  },
  "head_classification": null,
  "mask_classification": {
    "n": 463,
    "positive": 83,
    "normal": 380,
    "accuracy": 0.5896328293736501,
    "precision": 0.2816326530612245,
    "recall_sensitivity": 0.8313253012048193,
    "specificity": 0.5368421052631579,
    "f1": 0.42073170731707316,
    "false_positive_rate": 0.4631578947368421,
    "false_negative_rate": 0.1686746987951807,
    "auroc": 0.8144261255548509,
    "auprc_average_precision": 0.6174187406746432,
    "confusion_matrix": {
      "tn": 204,
      "fp": 176,
      "fn": 14,
      "tp": 69
    },
    "score_definition": "Maximum native bilinear inverse sigmoid pixel; uncalibrated case proxy, not a case probability"
  },
  "segmentation": {
    "n_positive": 83,
    "mean_positive_dice": 0.42442989097742484,
    "mean_positive_iou": 0.32311579848789174,
    "mean_positive_precision_nonempty": 0.5370754808326049,
    "mean_positive_recall": 0.4767275588659879,
    "global_dice": 0.22413946567868379,
    "global_iou": 0.12621456547225063,
    "global_pixel_precision": 0.14893756250125842,
    "global_pixel_recall": 0.45273597584456055,
    "pixel_counts": {
      "tp": 177530,
      "fp": 1014446,
      "fn": 214597
    },
    "empty_policy": "Normals excluded from positive macro Dice/IoU. Missed positive Dice/IoU/recall=0; empty prediction precision=null. Global metrics include normal false-positive pixels."
  },
  "mask_instance_localization": {
    "0.1": {
      "matches": 64,
      "gt": 99,
      "predicted": 436,
      "precision": 0.14678899082568808,
      "recall": 0.6464646464646465,
      "false_positive_regions": 372,
      "missed_regions": 35
    },
    "0.5": {
      "matches": 33,
      "gt": 99,
      "predicted": 436,
      "precision": 0.07568807339449542,
      "recall": 0.3333333333333333,
      "false_positive_regions": 403,
      "missed_regions": 66
    }
  },
  "four_groups_by_truth": {
    "reference_mask_only|normal": 380,
    "reference_mask_only|fracture": 83
  }
}

Raw confidence is uncalibrated. Localization AP is a component-box proxy, not canonical COCO detector mAP. Patient independence, clinical subtype labels, external generalization and radiologist adjudication remain unavailable. No CAL/test evaluation or promotion.
