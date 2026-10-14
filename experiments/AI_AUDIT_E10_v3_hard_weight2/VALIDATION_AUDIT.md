# Presence candidate native validation audit

Full463 frozen cases. Primary classification is conservative review-alert burden; masks always remain independent. Head-only gains do not authorize promotion.

{
  "classification": {
    "n": 463,
    "positive": 83,
    "normal": 380,
    "accuracy": 0.5356371490280778,
    "precision": 0.2518796992481203,
    "recall_sensitivity": 0.8072289156626506,
    "specificity": 0.4763157894736842,
    "f1": 0.3839541547277937,
    "false_positive_rate": 0.5236842105263158,
    "false_negative_rate": 0.1927710843373494,
    "auroc": 0.7852885225110969,
    "auprc_average_precision": 0.5740392147714433,
    "confusion_matrix": {
      "tn": 181,
      "fp": 199,
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
    "accuracy": 0.5356371490280778,
    "precision": 0.2518796992481203,
    "recall_sensitivity": 0.8072289156626506,
    "specificity": 0.4763157894736842,
    "f1": 0.3839541547277937,
    "false_positive_rate": 0.5236842105263158,
    "false_negative_rate": 0.1927710843373494,
    "auroc": 0.7852885225110969,
    "auprc_average_precision": 0.5740392147714433,
    "confusion_matrix": {
      "tn": 181,
      "fp": 199,
      "fn": 16,
      "tp": 67
    },
    "score_definition": "Maximum native bilinear inverse sigmoid pixel; uncalibrated case proxy, not a case probability"
  },
  "segmentation": {
    "n_positive": 83,
    "mean_positive_dice": 0.37952753899387115,
    "mean_positive_iou": 0.28366748755665727,
    "mean_positive_precision_nonempty": 0.4830857485336443,
    "mean_positive_recall": 0.4385768165947919,
    "global_dice": 0.29157220904882264,
    "global_iou": 0.17066697848932091,
    "global_pixel_precision": 0.2210863520389682,
    "global_pixel_recall": 0.42803734504382507,
    "pixel_counts": {
      "tp": 167845,
      "fp": 591338,
      "fn": 224282
    },
    "empty_policy": "Normals excluded from positive macro Dice/IoU. Missed positive Dice/IoU/recall=0; empty prediction precision=null. Global metrics include normal false-positive pixels."
  },
  "mask_instance_localization": {
    "0.1": {
      "matches": 57,
      "gt": 99,
      "predicted": 402,
      "precision": 0.1417910447761194,
      "recall": 0.5757575757575758,
      "false_positive_regions": 345,
      "missed_regions": 42
    },
    "0.5": {
      "matches": 28,
      "gt": 99,
      "predicted": 402,
      "precision": 0.06965174129353234,
      "recall": 0.2828282828282828,
      "false_positive_regions": 374,
      "missed_regions": 71
    }
  },
  "four_groups_by_truth": {
    "reference_mask_only|normal": 380,
    "reference_mask_only|fracture": 83
  }
}

Raw confidence is uncalibrated. Localization AP is a component-box proxy, not canonical COCO detector mAP. Patient independence, clinical subtype labels, external generalization and radiologist adjudication remain unavailable. No CAL/test evaluation or promotion.
