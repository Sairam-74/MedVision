# Completed candidate validation audit

Run experiments\AI_E5_v3_BCE_reference; epoch8; native threshold0.5/all.

No calibration/test access or promotion. Original checkpoint and baseline untouched.

## Classification

| Metric | Value |
|---|---:|
| n | 463 |
| positive | 83 |
| normal | 380 |
| accuracy | 0.5075593952483801 |
| precision | 0.22846441947565543 |
| recall_sensitivity | 0.7349397590361446 |
| specificity | 0.45789473684210524 |
| f1 | 0.3485714285714286 |
| false_positive_rate | 0.5421052631578948 |
| false_negative_rate | 0.26506024096385544 |
| auroc | 0.6537729866835764 |
| auprc_average_precision | 0.34165433296324915 |

## Segmentation/localization

{
  "n_positive": 83,
  "mean_positive_dice": 0.22021043804985097,
  "mean_positive_iou": 0.16080441645686508,
  "mean_positive_precision_nonempty": 0.3472931580492903,
  "mean_positive_recall": 0.2320424706013859,
  "global_dice": 0.052107512511645845,
  "global_iou": 0.026750712806965112,
  "global_pixel_precision": 0.04465618831892439,
  "global_pixel_recall": 0.06254351268849123,
  "pixel_counts": {
    "tp": 24525,
    "fp": 524671,
    "fn": 367602
  },
  "empty_policy": "Normals excluded from positive macro Dice/IoU. Missed positive Dice/IoU/recall=0; empty prediction precision=null. Global metrics include normal false-positive pixels."
}

{
  "0.1": {
    "matches": 36,
    "gt": 99,
    "predicted": 402,
    "precision": 0.08955223880597014,
    "recall": 0.36363636363636365,
    "false_positive_regions": 366,
    "missed_regions": 63
  },
  "0.5": {
    "matches": 12,
    "gt": 99,
    "predicted": 402,
    "precision": 0.029850746268656716,
    "recall": 0.12121212121212122,
    "false_positive_regions": 390,
    "missed_regions": 87
  }
}

Component-box AP is a proxy, not canonical detector mAP. Clinical cause and patient independence remain unverified.

Every FP/FN/tagged mask error has a retained panel. See metrics.json for calibration/subgroups/timing and trainer reproduction.

Classification count targets pass: False. This alone NEVER authorizes promotion.
