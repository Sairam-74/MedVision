# Completed candidate validation audit

Run experiments\AI_E6_v3_normal_BCE2; epoch12; native threshold0.5/all.

No calibration/test access or promotion. Original checkpoint and baseline untouched.

## Classification

| Metric | Value |
|---|---:|
| n | 463 |
| positive | 83 |
| normal | 380 |
| accuracy | 0.49892008639308855 |
| precision | 0.23487544483985764 |
| recall_sensitivity | 0.7951807228915663 |
| specificity | 0.4342105263157895 |
| f1 | 0.3626373626373626 |
| false_positive_rate | 0.5657894736842105 |
| false_negative_rate | 0.20481927710843373 |
| auroc | 0.6979708306911858 |
| auprc_average_precision | 0.39020451693200536 |

## Segmentation/localization

{
  "n_positive": 83,
  "mean_positive_dice": 0.239208230587619,
  "mean_positive_iou": 0.16944611599256978,
  "mean_positive_precision_nonempty": 0.31198631788471837,
  "mean_positive_recall": 0.30647593684093155,
  "global_dice": 0.04210002175653762,
  "global_iou": 0.021502641720394632,
  "global_pixel_precision": 0.02978098205842594,
  "global_pixel_recall": 0.07180071762464711,
  "pixel_counts": {
    "tp": 28155,
    "fp": 917247,
    "fn": 363972
  },
  "empty_policy": "Normals excluded from positive macro Dice/IoU. Missed positive Dice/IoU/recall=0; empty prediction precision=null. Global metrics include normal false-positive pixels."
}

{
  "0.1": {
    "matches": 45,
    "gt": 99,
    "predicted": 594,
    "precision": 0.07575757575757576,
    "recall": 0.45454545454545453,
    "false_positive_regions": 549,
    "missed_regions": 54
  },
  "0.5": {
    "matches": 14,
    "gt": 99,
    "predicted": 594,
    "precision": 0.02356902356902357,
    "recall": 0.1414141414141414,
    "false_positive_regions": 580,
    "missed_regions": 85
  }
}

Component-box AP is a proxy, not canonical detector mAP. Clinical cause and patient independence remain unverified.

Every FP/FN/tagged mask error has a retained panel. See metrics.json for calibration/subgroups/timing and trainer reproduction.

Classification count targets pass: False. This alone NEVER authorizes promotion.
