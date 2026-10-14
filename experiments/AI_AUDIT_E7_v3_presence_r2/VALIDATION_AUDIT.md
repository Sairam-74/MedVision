# Presence candidate native validation audit

Full463 frozen cases. Primary classification is conservative review-alert burden; masks always remain independent. Head-only gains do not authorize promotion.

{
  "classification": {
    "n": 463,
    "positive": 83,
    "normal": 380,
    "accuracy": 0.5961123110151187,
    "precision": 0.26991150442477874,
    "recall_sensitivity": 0.7349397590361446,
    "specificity": 0.5657894736842105,
    "f1": 0.3948220064724919,
    "false_positive_rate": 0.4342105263157895,
    "false_negative_rate": 0.26506024096385544,
    "auroc": 0.7084020291693089,
    "auprc_average_precision": 0.46496228608826173,
    "confusion_matrix": {
      "tn": 215,
      "fp": 165,
      "fn": 22,
      "tp": 61
    },
    "score_definition": "Independent mask presence, maximum pixel proxy"
  },
  "head_classification": null,
  "mask_classification": {
    "n": 463,
    "positive": 83,
    "normal": 380,
    "accuracy": 0.5961123110151187,
    "precision": 0.26991150442477874,
    "recall_sensitivity": 0.7349397590361446,
    "specificity": 0.5657894736842105,
    "f1": 0.3948220064724919,
    "false_positive_rate": 0.4342105263157895,
    "false_negative_rate": 0.26506024096385544,
    "auroc": 0.7084020291693089,
    "auprc_average_precision": 0.46496228608826173,
    "confusion_matrix": {
      "tn": 215,
      "fp": 165,
      "fn": 22,
      "tp": 61
    },
    "score_definition": "Maximum native bilinear inverse sigmoid pixel; uncalibrated case proxy, not a case probability"
  },
  "segmentation": {
    "n_positive": 83,
    "mean_positive_dice": 0.27049169577436155,
    "mean_positive_iou": 0.19886843089650547,
    "mean_positive_precision_nonempty": 0.39608595584650896,
    "mean_positive_recall": 0.3345399152059524,
    "global_dice": 0.15329780332773857,
    "global_iou": 0.08301165374903416,
    "global_pixel_precision": 0.18112863866738044,
    "global_pixel_recall": 0.13288041884389495,
    "pixel_counts": {
      "tp": 52106,
      "fp": 235568,
      "fn": 340021
    },
    "empty_policy": "Normals excluded from positive macro Dice/IoU. Missed positive Dice/IoU/recall=0; empty prediction precision=null. Global metrics include normal false-positive pixels."
  },
  "mask_instance_localization": {
    "0.1": {
      "matches": 44,
      "gt": 99,
      "predicted": 334,
      "precision": 0.1317365269461078,
      "recall": 0.4444444444444444,
      "false_positive_regions": 290,
      "missed_regions": 55
    },
    "0.5": {
      "matches": 23,
      "gt": 99,
      "predicted": 334,
      "precision": 0.0688622754491018,
      "recall": 0.23232323232323232,
      "false_positive_regions": 311,
      "missed_regions": 76
    }
  },
  "four_groups_by_truth": {
    "reference_mask_only|normal": 380,
    "reference_mask_only|fracture": 83
  }
}

Raw confidence is uncalibrated. Localization AP is a component-box proxy, not canonical COCO detector mAP. Patient independence, clinical subtype labels, external generalization and radiologist adjudication remain unavailable. No CAL/test evaluation or promotion.
