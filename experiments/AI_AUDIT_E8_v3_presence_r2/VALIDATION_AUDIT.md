# Presence candidate native validation audit

Full463 frozen cases. Primary classification is conservative review-alert burden; masks always remain independent. Head-only gains do not authorize promotion.

{
  "classification": {
    "n": 463,
    "positive": 83,
    "normal": 380,
    "accuracy": 0.42116630669546434,
    "precision": 0.2222222222222222,
    "recall_sensitivity": 0.891566265060241,
    "specificity": 0.31842105263157894,
    "f1": 0.3557692307692308,
    "false_positive_rate": 0.6815789473684211,
    "false_negative_rate": 0.10843373493975904,
    "auroc": 0.7135383639822447,
    "auprc_average_precision": 0.3723248816813759,
    "confusion_matrix": {
      "tn": 121,
      "fp": 259,
      "fn": 9,
      "tp": 74
    },
    "score_definition": "Conservative head+ OR mask+ review alerts; max uncalibrated head/mask proxy, not clinical probability"
  },
  "head_classification": {
    "n": 463,
    "positive": 83,
    "normal": 380,
    "accuracy": 0.755939524838013,
    "precision": 0.3880597014925373,
    "recall_sensitivity": 0.6265060240963856,
    "specificity": 0.7842105263157895,
    "f1": 0.4792626728110599,
    "false_positive_rate": 0.21578947368421053,
    "false_negative_rate": 0.37349397590361444,
    "auroc": 0.7806594800253646,
    "auprc_average_precision": 0.4794263909329902,
    "confusion_matrix": {
      "tn": 298,
      "fp": 82,
      "fn": 31,
      "tp": 52
    },
    "score_definition": "Supervised balanced-BCE presence sigmoid, uncalibrated"
  },
  "mask_classification": {
    "n": 463,
    "positive": 83,
    "normal": 380,
    "accuracy": 0.4298056155507559,
    "precision": 0.20521172638436483,
    "recall_sensitivity": 0.7590361445783133,
    "specificity": 0.35789473684210527,
    "f1": 0.3230769230769231,
    "false_positive_rate": 0.6421052631578947,
    "false_negative_rate": 0.24096385542168675,
    "auroc": 0.6705770450221941,
    "auprc_average_precision": 0.3506158517792417,
    "confusion_matrix": {
      "tn": 136,
      "fp": 244,
      "fn": 20,
      "tp": 63
    },
    "score_definition": "Maximum native bilinear inverse sigmoid pixel; uncalibrated case proxy, not a case probability"
  },
  "segmentation": {
    "n_positive": 83,
    "mean_positive_dice": 0.2805503402535848,
    "mean_positive_iou": 0.20802211426133904,
    "mean_positive_precision_nonempty": 0.3763587566497341,
    "mean_positive_recall": 0.3197335352626986,
    "global_dice": 0.11304596604997139,
    "global_iou": 0.05990923150010613,
    "global_pixel_precision": 0.08563532646030055,
    "global_pixel_recall": 0.1662650110805938,
    "pixel_counts": {
      "tp": 65197,
      "fp": 696136,
      "fn": 326930
    },
    "empty_policy": "Normals excluded from positive macro Dice/IoU. Missed positive Dice/IoU/recall=0; empty prediction precision=null. Global metrics include normal false-positive pixels."
  },
  "mask_instance_localization": {
    "0.1": {
      "matches": 43,
      "gt": 99,
      "predicted": 530,
      "precision": 0.08113207547169811,
      "recall": 0.43434343434343436,
      "false_positive_regions": 487,
      "missed_regions": 56
    },
    "0.5": {
      "matches": 19,
      "gt": 99,
      "predicted": 530,
      "precision": 0.035849056603773584,
      "recall": 0.1919191919191919,
      "false_positive_regions": 511,
      "missed_regions": 80
    }
  },
  "four_groups_by_truth": {
    "classifier+/mask+|normal": 67,
    "classifier+/mask+|fracture": 41,
    "classifier-/mask-|normal": 121,
    "classifier-/mask+|normal": 177,
    "classifier+/mask-|fracture": 11,
    "classifier-/mask-|fracture": 9,
    "classifier+/mask-|normal": 15,
    "classifier-/mask+|fracture": 22
  }
}

Raw confidence is uncalibrated. Localization AP is a component-box proxy, not canonical COCO detector mAP. Patient independence, clinical subtype labels, external generalization and radiologist adjudication remain unavailable. No CAL/test evaluation or promotion.
