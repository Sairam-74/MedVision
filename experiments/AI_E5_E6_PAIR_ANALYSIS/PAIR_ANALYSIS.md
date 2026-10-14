# Controlled normal-supervision result

REJECT stronger normal BCE as an overall improvement at registered default point

## Matched default operating points

| Metric | BCE1 | BCE2 | Change |
|---|---:|---:|---:|
| classification.accuracy | 0.5075593952483801 | 0.49892008639308855 | -0.008639308855291572 |
| classification.precision | 0.22846441947565543 | 0.23487544483985764 | 0.006411025364202211 |
| classification.recall_sensitivity | 0.7349397590361446 | 0.7951807228915663 | 0.06024096385542166 |
| classification.specificity | 0.45789473684210524 | 0.4342105263157895 | -0.023684210526315752 |
| classification.f1 | 0.3485714285714286 | 0.3626373626373626 | 0.014065934065934038 |
| classification.auroc | 0.6537729866835764 | 0.6979708306911858 | 0.0441978440076094 |
| classification.auprc_average_precision | 0.34165433296324915 | 0.39020451693200536 | 0.04855018396875621 |
| classification.false_positive_rate | 0.5421052631578948 | 0.5657894736842105 | 0.023684210526315752 |
| classification.false_negative_rate | 0.26506024096385544 | 0.20481927710843373 | -0.060240963855421714 |
| segmentation.mean_positive_dice | 0.22021043804985097 | 0.239208230587619 | 0.018997792537768038 |
| segmentation.mean_positive_iou | 0.16080441645686508 | 0.16944611599256978 | 0.008641699535704706 |
| segmentation.global_pixel_precision | 0.04465618831892439 | 0.02978098205842594 | -0.014875206260498455 |
| segmentation.global_pixel_recall | 0.06254351268849123 | 0.07180071762464711 | 0.00925720493615588 |
| segmentation.global_dice | 0.052107512511645845 | 0.04210002175653762 | -0.010007490755108227 |
| segmentation.global_iou | 0.026750712806965112 | 0.021502641720394632 | -0.00524807108657048 |
| calibration.brier_score | 0.3782743110515753 | 0.39225085494333606 | 0.013976543891760784 |
| calibration.expected_calibration_error | 0.4063812043480364 | 0.4335064006278887 | 0.027125196279852326 |

## Error transitions

{
  "normal_FP_recovered": {
    "n": 55,
    "image_ids": [
      "IMG0000123.jpg",
      "IMG0000374.jpg",
      "IMG0000403.jpg",
      "IMG0000417.jpg",
      "IMG0000517.jpg",
      "IMG0000537.jpg",
      "IMG0000624.jpg",
      "IMG0000631.jpg",
      "IMG0000684.jpg",
      "IMG0000705.jpg",
      "IMG0000709.jpg",
      "IMG0000711.jpg",
      "IMG0000830.jpg",
      "IMG0000873.jpg",
      "IMG0000902.jpg",
      "IMG0000910.jpg",
      "IMG0000919.jpg",
      "IMG0000970.jpg",
      "IMG0001434.jpg",
      "IMG0001511.jpg",
      "IMG0001604.jpg",
      "IMG0001638.jpg",
      "IMG0001644.jpg",
      "IMG0001646.jpg",
      "IMG0001750.jpg",
      "IMG0001793.jpg",
      "IMG0001797.jpg",
      "IMG0001807.jpg",
      "IMG0001949.jpg",
      "IMG0001972.jpg",
      "IMG0002066.jpg",
      "IMG0002198.jpg",
      "IMG0002247.jpg",
      "IMG0002639.jpg",
      "IMG0002667.jpg",
      "IMG0002702.jpg",
      "IMG0002735.jpg",
      "IMG0002835.jpg",
      "IMG0002871.jpg",
      "IMG0002881.jpg",
      "IMG0002920.jpg",
      "IMG0002958.jpg",
      "IMG0002989.jpg",
      "IMG0003036.jpg",
      "IMG0003091.jpg",
      "IMG0003189.jpg",
      "IMG0003413.jpg",
      "IMG0003508.jpg",
      "IMG0003597.jpg",
      "IMG0003689.jpg",
      "IMG0003709.jpg",
      "IMG0003791.jpg",
      "IMG0003919.jpg",
      "IMG0003992.jpg",
      "IMG0004060.jpg"
    ]
  },
  "normal_new_FP": {
    "n": 64,
    "image_ids": [
      "IMG0000040.jpg",
      "IMG0000149.jpg",
      "IMG0000170.jpg",
      "IMG0000174.jpg",
      "IMG0000219.jpg",
      "IMG0000224.jpg",
      "IMG0000244.jpg",
      "IMG0000336.jpg",
      "IMG0000398.jpg",
      "IMG0000428.jpg",
      "IMG0000462.jpg",
      "IMG0000494.jpg",
      "IMG0000545.jpg",
      "IMG0000575.jpg",
      "IMG0000589.jpg",
      "IMG0000704.jpg",
      "IMG0000712.jpg",
      "IMG0000854.jpg",
      "IMG0000937.jpg",
      "IMG0000988.jpg",
      "IMG0000998.jpg",
      "IMG0001015.jpg",
      "IMG0001095.jpg",
      "IMG0001109.jpg",
      "IMG0001113.jpg",
      "IMG0001230.jpg",
      "IMG0001249.jpg",
      "IMG0001291.jpg",
      "IMG0001345.jpg",
      "IMG0001435.jpg",
      "IMG0001633.jpg",
      "IMG0001833.jpg",
      "IMG0001854.jpg",
      "IMG0001879.jpg",
      "IMG0001917.jpg",
      "IMG0001940.jpg",
      "IMG0002023.jpg",
      "IMG0002091.jpg",
      "IMG0002115.jpg",
      "IMG0002187.jpg",
      "IMG0002271.jpg",
      "IMG0002631.jpg",
      "IMG0002828.jpg",
      "IMG0003029.jpg",
      "IMG0003033.jpg",
      "IMG0003056.jpg",
      "IMG0003108.jpg",
      "IMG0003136.jpg",
      "IMG0003143.jpg",
      "IMG0003144.jpg",
      "IMG0003176.jpg",
      "IMG0003224.jpg",
      "IMG0003345.jpg",
      "IMG0003353.jpg",
      "IMG0003488.jpg",
      "IMG0003555.jpg",
      "IMG0003591.jpg",
      "IMG0003605.jpg",
      "IMG0003696.jpg",
      "IMG0003716.jpg",
      "IMG0003745.jpg",
      "IMG0003753.jpg",
      "IMG0003775.jpg",
      "IMG0004178.jpg"
    ]
  },
  "fracture_FN_recovered": {
    "n": 13,
    "image_ids": [
      "IMG0000019.jpg",
      "IMG0001710.jpg",
      "IMG0002303.jpg",
      "IMG0002333.jpg",
      "IMG0002449.jpg",
      "IMG0002463.jpg",
      "IMG0002472.jpg",
      "IMG0002480.jpg",
      "IMG0002549.jpg",
      "IMG0002584.jpg",
      "IMG0002619.jpg",
      "IMG0003342.jpg",
      "IMG0003843.jpg"
    ]
  },
  "fracture_new_FN": {
    "n": 8,
    "image_ids": [
      "IMG0001367.jpg",
      "IMG0001948.jpg",
      "IMG0002304.jpg",
      "IMG0002516.jpg",
      "IMG0002518.jpg",
      "IMG0002533.jpg",
      "IMG0002553.jpg",
      "IMG0004009.jpg"
    ]
  },
  "fracture_new_zero_overlap": {
    "n": 2,
    "image_ids": [
      "IMG0002342.jpg",
      "IMG0002834.jpg"
    ]
  },
  "fracture_Dice_gain_over_02": {
    "n": 28,
    "image_ids": [
      "IMG0000019.jpg",
      "IMG0000319.jpg",
      "IMG0000470.jpg",
      "IMG0001073.jpg",
      "IMG0001391.jpg",
      "IMG0002181.jpg",
      "IMG0002208.jpg",
      "IMG0002323.jpg",
      "IMG0002402.jpg",
      "IMG0002412.jpg",
      "IMG0002441.jpg",
      "IMG0002472.jpg",
      "IMG0002480.jpg",
      "IMG0002493.jpg",
      "IMG0002587.jpg",
      "IMG0002602.jpg",
      "IMG0002647.jpg",
      "IMG0002831.jpg",
      "IMG0002934.jpg",
      "IMG0003111.jpg",
      "IMG0003217.jpg",
      "IMG0003342.jpg",
      "IMG0003523.jpg",
      "IMG0003819.jpg",
      "IMG0003843.jpg",
      "IMG0004044.jpg",
      "IMG0004071.jpg",
      "IMG0004374.jpg"
    ]
  },
  "fracture_Dice_loss_over_02": {
    "n": 20,
    "image_ids": [
      "IMG0000851.jpg",
      "IMG0001041.jpg",
      "IMG0001198.jpg",
      "IMG0001411.jpg",
      "IMG0001933.jpg",
      "IMG0001948.jpg",
      "IMG0002311.jpg",
      "IMG0002342.jpg",
      "IMG0002397.jpg",
      "IMG0002409.jpg",
      "IMG0002442.jpg",
      "IMG0002524.jpg",
      "IMG0002553.jpg",
      "IMG0002558.jpg",
      "IMG0002606.jpg",
      "IMG0002834.jpg",
      "IMG0002849.jpg",
      "IMG0003927.jpg",
      "IMG0004009.jpg",
      "IMG0004207.jpg"
    ]
  }
}

Inspect retained actual masks and panels before assigning causes. View and hardware associations are not causal proof.

Classification counts pass: False; Dice target pass: False; native localization target pass: False.

No final success/promotion/test access. Original comparison uses the SAME463 IDs but unknown original exposure remains. Next intervention requires recorded failure analysis, not random technique selection.
