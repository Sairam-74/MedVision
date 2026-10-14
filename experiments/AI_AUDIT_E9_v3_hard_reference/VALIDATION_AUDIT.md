# Presence candidate native validation audit

Full463 frozen cases. Primary classification is conservative review-alert burden; masks always remain independent. Head-only gains do not authorize promotion.

{
  "classification": {
    "n": 463,
    "positive": 83,
    "normal": 380,
    "accuracy": 0.5140388768898488,
    "precision": 0.2427536231884058,
    "recall_sensitivity": 0.8072289156626506,
    "specificity": 0.45,
    "f1": 0.3732590529247911,
    "false_positive_rate": 0.55,
    "false_negative_rate": 0.1927710843373494,
    "auroc": 0.7850982878883958,
    "auprc_average_precision": 0.5926414243099495,
    "confusion_matrix": {
      "tn": 171,
      "fp": 209,
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
    "accuracy": 0.5140388768898488,
    "precision": 0.2427536231884058,
    "recall_sensitivity": 0.8072289156626506,
    "specificity": 0.45,
    "f1": 0.3732590529247911,
    "false_positive_rate": 0.55,
    "false_negative_rate": 0.1927710843373494,
    "auroc": 0.7850982878883958,
    "auprc_average_precision": 0.5926414243099495,
    "confusion_matrix": {
      "tn": 171,
      "fp": 209,
      "fn": 16,
      "tp": 67
    },
    "score_definition": "Maximum native bilinear inverse sigmoid pixel; uncalibrated case proxy, not a case probability"
  },
  "segmentation": {
    "n_positive": 83,
    "mean_positive_dice": 0.35934235628847794,
    "mean_positive_iou": 0.26556882623002753,
    "mean_positive_precision_nonempty": 0.4481060329038986,
    "mean_positive_recall": 0.43061548413319173,
    "global_dice": 0.20523259440471137,
    "global_iou": 0.11435052462223638,
    "global_pixel_precision": 0.1462363912891242,
    "global_pixel_recall": 0.34402119721416785,
    "pixel_counts": {
      "tp": 134900,
      "fp": 787579,
      "fn": 257227
    },
    "empty_policy": "Normals excluded from positive macro Dice/IoU. Missed positive Dice/IoU/recall=0; empty prediction precision=null. Global metrics include normal false-positive pixels."
  },
  "mask_instance_localization": {
    "0.1": {
      "matches": 57,
      "gt": 99,
      "predicted": 430,
      "precision": 0.1325581395348837,
      "recall": 0.5757575757575758,
      "false_positive_regions": 373,
      "missed_regions": 42
    },
    "0.5": {
      "matches": 24,
      "gt": 99,
      "predicted": 430,
      "precision": 0.05581395348837209,
      "recall": 0.24242424242424243,
      "false_positive_regions": 406,
      "missed_regions": 75
    }
  },
  "four_groups_by_truth": {
    "reference_mask_only|normal": 380,
    "reference_mask_only|fracture": 83
  }
}

Raw confidence is uncalibrated. Localization AP is a component-box proxy, not canonical COCO detector mAP. Patient independence, clinical subtype labels, external generalization and radiologist adjudication remain unavailable. No CAL/test evaluation or promotion.
