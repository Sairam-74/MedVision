# Presence candidate native validation audit

Full463 frozen cases. Primary classification is conservative review-alert burden; masks always remain independent. Head-only gains do not authorize promotion.

{
  "classification": {
    "n": 463,
    "positive": 83,
    "normal": 380,
    "accuracy": 0.6328293736501079,
    "precision": 0.29767441860465116,
    "recall_sensitivity": 0.7710843373493976,
    "specificity": 0.6026315789473684,
    "f1": 0.42953020134228187,
    "false_positive_rate": 0.3973684210526316,
    "false_negative_rate": 0.2289156626506024,
    "auroc": 0.8016487000634116,
    "auprc_average_precision": 0.6051604275189888,
    "confusion_matrix": {
      "tn": 229,
      "fp": 151,
      "fn": 19,
      "tp": 64
    },
    "score_definition": "Independent mask presence, maximum pixel proxy"
  },
  "head_classification": null,
  "mask_classification": {
    "n": 463,
    "positive": 83,
    "normal": 380,
    "accuracy": 0.6328293736501079,
    "precision": 0.29767441860465116,
    "recall_sensitivity": 0.7710843373493976,
    "specificity": 0.6026315789473684,
    "f1": 0.42953020134228187,
    "false_positive_rate": 0.3973684210526316,
    "false_negative_rate": 0.2289156626506024,
    "auroc": 0.8016487000634116,
    "auprc_average_precision": 0.6051604275189888,
    "confusion_matrix": {
      "tn": 229,
      "fp": 151,
      "fn": 19,
      "tp": 64
    },
    "score_definition": "Maximum native bilinear inverse sigmoid pixel; uncalibrated case proxy, not a case probability"
  },
  "segmentation": {
    "n_positive": 83,
    "mean_positive_dice": 0.3833219034105424,
    "mean_positive_iou": 0.28467616895570175,
    "mean_positive_precision_nonempty": 0.5794580170116583,
    "mean_positive_recall": 0.4153064863746833,
    "global_dice": 0.3483699821181638,
    "global_iou": 0.21092495192412244,
    "global_pixel_precision": 0.35047943526010816,
    "global_pixel_recall": 0.3462857696613597,
    "pixel_counts": {
      "tp": 135788,
      "fp": 251647,
      "fn": 256339
    },
    "empty_policy": "Normals excluded from positive macro Dice/IoU. Missed positive Dice/IoU/recall=0; empty prediction precision=null. Global metrics include normal false-positive pixels."
  },
  "mask_instance_localization": {
    "0.1": {
      "matches": 55,
      "gt": 99,
      "predicted": 314,
      "precision": 0.1751592356687898,
      "recall": 0.5555555555555556,
      "false_positive_regions": 259,
      "missed_regions": 44
    },
    "0.5": {
      "matches": 26,
      "gt": 99,
      "predicted": 314,
      "precision": 0.08280254777070063,
      "recall": 0.26262626262626265,
      "false_positive_regions": 288,
      "missed_regions": 73
    }
  },
  "four_groups_by_truth": {
    "reference_mask_only|normal": 380,
    "reference_mask_only|fracture": 83
  }
}

Raw confidence is uncalibrated. Localization AP is a component-box proxy, not canonical COCO detector mAP. Patient independence, clinical subtype labels, external generalization and radiologist adjudication remain unavailable. No CAL/test evaluation or promotion.
