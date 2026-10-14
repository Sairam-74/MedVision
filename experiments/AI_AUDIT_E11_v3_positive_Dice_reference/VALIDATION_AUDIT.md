# Presence candidate native validation audit

Full463 frozen cases. Primary classification is conservative review-alert burden; masks always remain independent. Head-only gains do not authorize promotion.

{
  "classification": {
    "n": 463,
    "positive": 83,
    "normal": 380,
    "accuracy": 0.6652267818574514,
    "precision": 0.32524271844660196,
    "recall_sensitivity": 0.8072289156626506,
    "specificity": 0.6342105263157894,
    "f1": 0.46366782006920415,
    "false_positive_rate": 0.36578947368421055,
    "false_negative_rate": 0.1927710843373494,
    "auroc": 0.8073557387444514,
    "auprc_average_precision": 0.5640968306229868,
    "confusion_matrix": {
      "tn": 241,
      "fp": 139,
      "fn": 16,
      "tp": 67
    },
    "score_definition": "Independent mask presence, maximum pixel proxy"
  },
  "head_classification": null,
  "mask_classification": {
    "n": 463,
    "positive": 83,
    "normal": 380,
    "accuracy": 0.6652267818574514,
    "precision": 0.32524271844660196,
    "recall_sensitivity": 0.8072289156626506,
    "specificity": 0.6342105263157894,
    "f1": 0.46366782006920415,
    "false_positive_rate": 0.36578947368421055,
    "false_negative_rate": 0.1927710843373494,
    "auroc": 0.8073557387444514,
    "auprc_average_precision": 0.5640968306229868,
    "confusion_matrix": {
      "tn": 241,
      "fp": 139,
      "fn": 16,
      "tp": 67
    },
    "score_definition": "Maximum native bilinear inverse sigmoid pixel; uncalibrated case proxy, not a case probability"
  },
  "segmentation": {
    "n_positive": 83,
    "mean_positive_dice": 0.375113809566179,
    "mean_positive_iou": 0.2841692169147649,
    "mean_positive_precision_nonempty": 0.6151658270157593,
    "mean_positive_recall": 0.38428575129346454,
    "global_dice": 0.26546783926413103,
    "global_iou": 0.15304866941844839,
    "global_pixel_precision": 0.31938019522200944,
    "global_pixel_recall": 0.22712794579307213,
    "pixel_counts": {
      "tp": 89063,
      "fp": 189799,
      "fn": 303064
    },
    "empty_policy": "Normals excluded from positive macro Dice/IoU. Missed positive Dice/IoU/recall=0; empty prediction precision=null. Global metrics include normal false-positive pixels."
  },
  "mask_instance_localization": {
    "0.1": {
      "matches": 53,
      "gt": 99,
      "predicted": 280,
      "precision": 0.18928571428571428,
      "recall": 0.5353535353535354,
      "false_positive_regions": 227,
      "missed_regions": 46
    },
    "0.5": {
      "matches": 30,
      "gt": 99,
      "predicted": 280,
      "precision": 0.10714285714285714,
      "recall": 0.30303030303030304,
      "false_positive_regions": 250,
      "missed_regions": 69
    }
  },
  "four_groups_by_truth": {
    "reference_mask_only|normal": 380,
    "reference_mask_only|fracture": 83
  }
}

Raw confidence is uncalibrated. Localization AP is a component-box proxy, not canonical COCO detector mAP. Patient independence, clinical subtype labels, external generalization and radiologist adjudication remain unavailable. No CAL/test evaluation or promotion.
