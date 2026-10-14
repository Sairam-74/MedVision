# Presence candidate native validation audit

Full463 frozen cases. Primary classification is conservative review-alert burden; masks always remain independent. Head-only gains do not authorize promotion.

{
  "classification": {
    "n": 463,
    "positive": 83,
    "normal": 380,
    "accuracy": 0.6630669546436285,
    "precision": 0.3286384976525822,
    "recall_sensitivity": 0.8433734939759037,
    "specificity": 0.6236842105263158,
    "f1": 0.47297297297297297,
    "false_positive_rate": 0.3763157894736842,
    "false_negative_rate": 0.1566265060240964,
    "auroc": 0.8342105263157895,
    "auprc_average_precision": 0.6406167762349088,
    "confusion_matrix": {
      "tn": 237,
      "fp": 143,
      "fn": 13,
      "tp": 70
    },
    "score_definition": "Independent mask presence, maximum pixel proxy"
  },
  "head_classification": null,
  "mask_classification": {
    "n": 463,
    "positive": 83,
    "normal": 380,
    "accuracy": 0.6630669546436285,
    "precision": 0.3286384976525822,
    "recall_sensitivity": 0.8433734939759037,
    "specificity": 0.6236842105263158,
    "f1": 0.47297297297297297,
    "false_positive_rate": 0.3763157894736842,
    "false_negative_rate": 0.1566265060240964,
    "auroc": 0.8342105263157895,
    "auprc_average_precision": 0.6406167762349088,
    "confusion_matrix": {
      "tn": 237,
      "fp": 143,
      "fn": 13,
      "tp": 70
    },
    "score_definition": "Maximum native bilinear inverse sigmoid pixel; uncalibrated case proxy, not a case probability"
  },
  "segmentation": {
    "n_positive": 83,
    "mean_positive_dice": 0.42910650030210395,
    "mean_positive_iou": 0.32727252480132546,
    "mean_positive_precision_nonempty": 0.5325632724117076,
    "mean_positive_recall": 0.4804030401631189,
    "global_dice": 0.42745067030259254,
    "global_iou": 0.2718201980886942,
    "global_pixel_precision": 0.36786281148902283,
    "global_pixel_recall": 0.5100745421763867,
    "pixel_counts": {
      "tp": 200014,
      "fp": 343705,
      "fn": 192113
    },
    "empty_policy": "Normals excluded from positive macro Dice/IoU. Missed positive Dice/IoU/recall=0; empty prediction precision=null. Global metrics include normal false-positive pixels."
  },
  "mask_instance_localization": {
    "0.1": {
      "matches": 64,
      "gt": 99,
      "predicted": 285,
      "precision": 0.22456140350877193,
      "recall": 0.6464646464646465,
      "false_positive_regions": 221,
      "missed_regions": 35
    },
    "0.5": {
      "matches": 34,
      "gt": 99,
      "predicted": 285,
      "precision": 0.11929824561403508,
      "recall": 0.3434343434343434,
      "false_positive_regions": 251,
      "missed_regions": 65
    }
  },
  "four_groups_by_truth": {
    "reference_mask_only|normal": 380,
    "reference_mask_only|fracture": 83
  }
}

Raw confidence is uncalibrated. Localization AP is a component-box proxy, not canonical COCO detector mAP. Patient independence, clinical subtype labels, external generalization and radiologist adjudication remain unavailable. No CAL/test evaluation or promotion.
