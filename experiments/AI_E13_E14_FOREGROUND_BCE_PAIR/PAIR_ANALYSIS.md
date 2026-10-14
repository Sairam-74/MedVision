# Matched foreground-pixel BCE weighting

KEEP FOR DEVELOPMENT; full further gates required

{
  "reference": "experiments\\AI_AUDIT_E13_v3_foreground_BCE_reference",
  "candidate": "experiments\\AI_AUDIT_E14_v3_foreground_BCE5",
  "factor": "Foreground-pixel BCE coefficient1 versus5; background BCE, Dice and hard factor2 unchanged",
  "all_other_configurations_matched": true,
  "initial_model_optimizer_matched": true,
  "metrics": {
    "classification": {
      "accuracy": {
        "reference": 0.5896328293736501,
        "candidate": 0.6630669546436285,
        "absolute_delta": 0.07343412526997839
      },
      "precision": {
        "reference": 0.2816326530612245,
        "candidate": 0.3286384976525822,
        "absolute_delta": 0.047005844591357704
      },
      "recall_sensitivity": {
        "reference": 0.8313253012048193,
        "candidate": 0.8433734939759037,
        "absolute_delta": 0.012048192771084376
      },
      "specificity": {
        "reference": 0.5368421052631579,
        "candidate": 0.6236842105263158,
        "absolute_delta": 0.08684210526315794
      },
      "f1": {
        "reference": 0.42073170731707316,
        "candidate": 0.47297297297297297,
        "absolute_delta": 0.052241265655899816
      },
      "auroc": {
        "reference": 0.8144261255548509,
        "candidate": 0.8342105263157895,
        "absolute_delta": 0.01978440076093857
      },
      "auprc_average_precision": {
        "reference": 0.6174187406746432,
        "candidate": 0.6406167762349088,
        "absolute_delta": 0.023198035560265562
      },
      "false_positive_rate": {
        "reference": 0.4631578947368421,
        "candidate": 0.3763157894736842,
        "absolute_delta": -0.08684210526315789
      },
      "false_negative_rate": {
        "reference": 0.1686746987951807,
        "candidate": 0.1566265060240964,
        "absolute_delta": -0.01204819277108432
      }
    },
    "segmentation": {
      "mean_positive_dice": {
        "reference": 0.42442989097742484,
        "candidate": 0.42910650030210395,
        "absolute_delta": 0.004676609324679115
      },
      "mean_positive_iou": {
        "reference": 0.32311579848789174,
        "candidate": 0.32727252480132546,
        "absolute_delta": 0.004156726313433723
      },
      "global_pixel_precision": {
        "reference": 0.14893756250125842,
        "candidate": 0.36786281148902283,
        "absolute_delta": 0.21892524898776441
      },
      "global_pixel_recall": {
        "reference": 0.45273597584456055,
        "candidate": 0.5100745421763867,
        "absolute_delta": 0.05733856633182616
      },
      "global_dice": {
        "reference": 0.22413946567868379,
        "candidate": 0.42745067030259254,
        "absolute_delta": 0.20331120462390875
      },
      "global_iou": {
        "reference": 0.12621456547225063,
        "candidate": 0.2718201980886942,
        "absolute_delta": 0.14560563261644355
      }
    },
    "calibration": {
      "brier_score": {
        "reference": 0.29174333748266923,
        "candidate": 0.23746908789731308,
        "absolute_delta": -0.05427424958535615
      },
      "expected_calibration_error": {
        "reference": 0.3293434943972768,
        "candidate": 0.26645433203795965,
        "absolute_delta": -0.06288916235931713
      }
    }
  },
  "original_same_ID_comparison": {
    "classification": {
      "accuracy": {
        "reference": 0.27213822894168466,
        "candidate": 0.6630669546436285,
        "absolute_delta": 0.39092872570194387
      },
      "precision": {
        "reference": 0.1976190476190476,
        "candidate": 0.3286384976525822,
        "absolute_delta": 0.13101945003353457
      },
      "recall_sensitivity": {
        "reference": 1.0,
        "candidate": 0.8433734939759037,
        "absolute_delta": -0.15662650602409633
      },
      "specificity": {
        "reference": 0.11315789473684211,
        "candidate": 0.6236842105263158,
        "absolute_delta": 0.5105263157894737
      },
      "f1": {
        "reference": 0.33001988071570576,
        "candidate": 0.47297297297297297,
        "absolute_delta": 0.1429530922572672
      },
      "auroc": {
        "reference": 0.6018072289156626,
        "candidate": 0.8342105263157895,
        "absolute_delta": 0.23240329740012688
      },
      "auprc_average_precision": {
        "reference": 0.2156616190058667,
        "candidate": 0.6406167762349088,
        "absolute_delta": 0.4249551572290421
      },
      "false_positive_rate": {
        "reference": 0.8868421052631579,
        "candidate": 0.3763157894736842,
        "absolute_delta": -0.5105263157894737
      },
      "false_negative_rate": {
        "reference": 0.0,
        "candidate": 0.1566265060240964,
        "absolute_delta": 0.1566265060240964
      }
    },
    "segmentation": {
      "mean_positive_dice": {
        "reference": 0.5037965562512774,
        "candidate": 0.42910650030210395,
        "absolute_delta": -0.07469005594917344
      },
      "mean_positive_iou": {
        "reference": 0.3775685932913787,
        "candidate": 0.32727252480132546,
        "absolute_delta": -0.05029606849005325
      },
      "global_pixel_precision": {
        "reference": 0.09956511867180212,
        "candidate": 0.36786281148902283,
        "absolute_delta": 0.2682976928172207
      },
      "global_pixel_recall": {
        "reference": 0.7302353574224677,
        "candidate": 0.5100745421763867,
        "absolute_delta": -0.220160815246081
      },
      "global_dice": {
        "reference": 0.17523723380427186,
        "candidate": 0.42745067030259254,
        "absolute_delta": 0.2522134364983207
      },
      "global_iou": {
        "reference": 0.09603288550741698,
        "candidate": 0.2718201980886942,
        "absolute_delta": 0.1757873125812772
      }
    },
    "calibration": {
      "brier_score": {
        "reference": 0.7387043871964329,
        "candidate": 0.23746908789731308,
        "absolute_delta": -0.5012352992991198
      },
      "expected_calibration_error": {
        "reference": 0.745993458819284,
        "candidate": 0.26645433203795965,
        "absolute_delta": -0.4795391267813244
      }
    }
  },
  "independent_mask_error_transitions": {
    "normal_FP_recovered": {
      "n": 64,
      "image_ids": [
        "IMG0000008.jpg",
        "IMG0000024.jpg",
        "IMG0000030.jpg",
        "IMG0000079.jpg",
        "IMG0000123.jpg",
        "IMG0000130.jpg",
        "IMG0000133.jpg",
        "IMG0000149.jpg",
        "IMG0000219.jpg",
        "IMG0000221.jpg",
        "IMG0000244.jpg",
        "IMG0000336.jpg",
        "IMG0000417.jpg",
        "IMG0000462.jpg",
        "IMG0000494.jpg",
        "IMG0000619.jpg",
        "IMG0000659.jpg",
        "IMG0000705.jpg",
        "IMG0000766.jpg",
        "IMG0000793.jpg",
        "IMG0000811.jpg",
        "IMG0000825.jpg",
        "IMG0000837.jpg",
        "IMG0000871.jpg",
        "IMG0000922.jpg",
        "IMG0000937.jpg",
        "IMG0000998.jpg",
        "IMG0001082.jpg",
        "IMG0001243.jpg",
        "IMG0001450.jpg",
        "IMG0001527.jpg",
        "IMG0001557.jpg",
        "IMG0001606.jpg",
        "IMG0001636.jpg",
        "IMG0001646.jpg",
        "IMG0001683.jpg",
        "IMG0001722.jpg",
        "IMG0001750.jpg",
        "IMG0001854.jpg",
        "IMG0002058.jpg",
        "IMG0002063.jpg",
        "IMG0002066.jpg",
        "IMG0002100.jpg",
        "IMG0002187.jpg",
        "IMG0002188.jpg",
        "IMG0002239.jpg",
        "IMG0002782.jpg",
        "IMG0002820.jpg",
        "IMG0002911.jpg",
        "IMG0003029.jpg",
        "IMG0003036.jpg",
        "IMG0003108.jpg",
        "IMG0003116.jpg",
        "IMG0003143.jpg",
        "IMG0003270.jpg",
        "IMG0003343.jpg",
        "IMG0003439.jpg",
        "IMG0003535.jpg",
        "IMG0003540.jpg",
        "IMG0003571.jpg",
        "IMG0003581.jpg",
        "IMG0003689.jpg",
        "IMG0003845.jpg",
        "IMG0003992.jpg"
      ]
    },
    "normal_new_FP": {
      "n": 31,
      "image_ids": [
        "IMG0000081.jpg",
        "IMG0000374.jpg",
        "IMG0000403.jpg",
        "IMG0000428.jpg",
        "IMG0000631.jpg",
        "IMG0000643.jpg",
        "IMG0000704.jpg",
        "IMG0000807.jpg",
        "IMG0000970.jpg",
        "IMG0001039.jpg",
        "IMG0001230.jpg",
        "IMG0001433.jpg",
        "IMG0001583.jpg",
        "IMG0001678.jpg",
        "IMG0001793.jpg",
        "IMG0001949.jpg",
        "IMG0002023.jpg",
        "IMG0002090.jpg",
        "IMG0002271.jpg",
        "IMG0002706.jpg",
        "IMG0002735.jpg",
        "IMG0002753.jpg",
        "IMG0003151.jpg",
        "IMG0003281.jpg",
        "IMG0003350.jpg",
        "IMG0003353.jpg",
        "IMG0003445.jpg",
        "IMG0003465.jpg",
        "IMG0003537.jpg",
        "IMG0003591.jpg",
        "IMG0003987.jpg"
      ]
    },
    "fracture_FN_recovered": {
      "n": 7,
      "image_ids": [
        "IMG0000763.jpg",
        "IMG0001367.jpg",
        "IMG0002465.jpg",
        "IMG0002493.jpg",
        "IMG0002584.jpg",
        "IMG0002619.jpg",
        "IMG0004009.jpg"
      ]
    },
    "fracture_new_FN": {
      "n": 6,
      "image_ids": [
        "IMG0000144.jpg",
        "IMG0001073.jpg",
        "IMG0002181.jpg",
        "IMG0002342.jpg",
        "IMG0002392.jpg",
        "IMG0002732.jpg"
      ]
    },
    "fracture_new_zero_overlap": {
      "n": 1,
      "image_ids": [
        "IMG0002086.jpg"
      ]
    },
    "fracture_Dice_gain_over_02": {
      "n": 28,
      "image_ids": [
        "IMG0000190.jpg",
        "IMG0000470.jpg",
        "IMG0001041.jpg",
        "IMG0001198.jpg",
        "IMG0001362.jpg",
        "IMG0001365.jpg",
        "IMG0001391.jpg",
        "IMG0001411.jpg",
        "IMG0001933.jpg",
        "IMG0002085.jpg",
        "IMG0002208.jpg",
        "IMG0002303.jpg",
        "IMG0002304.jpg",
        "IMG0002311.jpg",
        "IMG0002333.jpg",
        "IMG0002349.jpg",
        "IMG0002441.jpg",
        "IMG0002472.jpg",
        "IMG0002501.jpg",
        "IMG0002535.jpg",
        "IMG0002549.jpg",
        "IMG0002553.jpg",
        "IMG0002586.jpg",
        "IMG0002647.jpg",
        "IMG0002834.jpg",
        "IMG0003798.jpg",
        "IMG0004009.jpg",
        "IMG0004207.jpg"
      ]
    },
    "fracture_Dice_loss_over_02": {
      "n": 27,
      "image_ids": [
        "IMG0000019.jpg",
        "IMG0000319.jpg",
        "IMG0000471.jpg",
        "IMG0001073.jpg",
        "IMG0002086.jpg",
        "IMG0002181.jpg",
        "IMG0002323.jpg",
        "IMG0002342.jpg",
        "IMG0002374.jpg",
        "IMG0002397.jpg",
        "IMG0002442.jpg",
        "IMG0002449.jpg",
        "IMG0002480.jpg",
        "IMG0002516.jpg",
        "IMG0002518.jpg",
        "IMG0002524.jpg",
        "IMG0002558.jpg",
        "IMG0002602.jpg",
        "IMG0002606.jpg",
        "IMG0002732.jpg",
        "IMG0002934.jpg",
        "IMG0003111.jpg",
        "IMG0003342.jpg",
        "IMG0003843.jpg",
        "IMG0003927.jpg",
        "IMG0004044.jpg",
        "IMG0004071.jpg"
      ]
    }
  },
  "conservative_alert_error_transitions": {
    "normal_FP_recovered": {
      "n": 64,
      "image_ids": [
        "IMG0000008.jpg",
        "IMG0000024.jpg",
        "IMG0000030.jpg",
        "IMG0000079.jpg",
        "IMG0000123.jpg",
        "IMG0000130.jpg",
        "IMG0000133.jpg",
        "IMG0000149.jpg",
        "IMG0000219.jpg",
        "IMG0000221.jpg",
        "IMG0000244.jpg",
        "IMG0000336.jpg",
        "IMG0000417.jpg",
        "IMG0000462.jpg",
        "IMG0000494.jpg",
        "IMG0000619.jpg",
        "IMG0000659.jpg",
        "IMG0000705.jpg",
        "IMG0000766.jpg",
        "IMG0000793.jpg",
        "IMG0000811.jpg",
        "IMG0000825.jpg",
        "IMG0000837.jpg",
        "IMG0000871.jpg",
        "IMG0000922.jpg",
        "IMG0000937.jpg",
        "IMG0000998.jpg",
        "IMG0001082.jpg",
        "IMG0001243.jpg",
        "IMG0001450.jpg",
        "IMG0001527.jpg",
        "IMG0001557.jpg",
        "IMG0001606.jpg",
        "IMG0001636.jpg",
        "IMG0001646.jpg",
        "IMG0001683.jpg",
        "IMG0001722.jpg",
        "IMG0001750.jpg",
        "IMG0001854.jpg",
        "IMG0002058.jpg",
        "IMG0002063.jpg",
        "IMG0002066.jpg",
        "IMG0002100.jpg",
        "IMG0002187.jpg",
        "IMG0002188.jpg",
        "IMG0002239.jpg",
        "IMG0002782.jpg",
        "IMG0002820.jpg",
        "IMG0002911.jpg",
        "IMG0003029.jpg",
        "IMG0003036.jpg",
        "IMG0003108.jpg",
        "IMG0003116.jpg",
        "IMG0003143.jpg",
        "IMG0003270.jpg",
        "IMG0003343.jpg",
        "IMG0003439.jpg",
        "IMG0003535.jpg",
        "IMG0003540.jpg",
        "IMG0003571.jpg",
        "IMG0003581.jpg",
        "IMG0003689.jpg",
        "IMG0003845.jpg",
        "IMG0003992.jpg"
      ]
    },
    "normal_new_FP": {
      "n": 31,
      "image_ids": [
        "IMG0000081.jpg",
        "IMG0000374.jpg",
        "IMG0000403.jpg",
        "IMG0000428.jpg",
        "IMG0000631.jpg",
        "IMG0000643.jpg",
        "IMG0000704.jpg",
        "IMG0000807.jpg",
        "IMG0000970.jpg",
        "IMG0001039.jpg",
        "IMG0001230.jpg",
        "IMG0001433.jpg",
        "IMG0001583.jpg",
        "IMG0001678.jpg",
        "IMG0001793.jpg",
        "IMG0001949.jpg",
        "IMG0002023.jpg",
        "IMG0002090.jpg",
        "IMG0002271.jpg",
        "IMG0002706.jpg",
        "IMG0002735.jpg",
        "IMG0002753.jpg",
        "IMG0003151.jpg",
        "IMG0003281.jpg",
        "IMG0003350.jpg",
        "IMG0003353.jpg",
        "IMG0003445.jpg",
        "IMG0003465.jpg",
        "IMG0003537.jpg",
        "IMG0003591.jpg",
        "IMG0003987.jpg"
      ]
    },
    "fracture_FN_recovered": {
      "n": 7,
      "image_ids": [
        "IMG0000763.jpg",
        "IMG0001367.jpg",
        "IMG0002465.jpg",
        "IMG0002493.jpg",
        "IMG0002584.jpg",
        "IMG0002619.jpg",
        "IMG0004009.jpg"
      ]
    },
    "fracture_new_FN": {
      "n": 6,
      "image_ids": [
        "IMG0000144.jpg",
        "IMG0001073.jpg",
        "IMG0002181.jpg",
        "IMG0002342.jpg",
        "IMG0002392.jpg",
        "IMG0002732.jpg"
      ]
    },
    "fracture_new_zero_overlap": {
      "n": 1,
      "image_ids": [
        "IMG0002086.jpg"
      ]
    },
    "fracture_Dice_gain_over_02": {
      "n": 28,
      "image_ids": [
        "IMG0000190.jpg",
        "IMG0000470.jpg",
        "IMG0001041.jpg",
        "IMG0001198.jpg",
        "IMG0001362.jpg",
        "IMG0001365.jpg",
        "IMG0001391.jpg",
        "IMG0001411.jpg",
        "IMG0001933.jpg",
        "IMG0002085.jpg",
        "IMG0002208.jpg",
        "IMG0002303.jpg",
        "IMG0002304.jpg",
        "IMG0002311.jpg",
        "IMG0002333.jpg",
        "IMG0002349.jpg",
        "IMG0002441.jpg",
        "IMG0002472.jpg",
        "IMG0002501.jpg",
        "IMG0002535.jpg",
        "IMG0002549.jpg",
        "IMG0002553.jpg",
        "IMG0002586.jpg",
        "IMG0002647.jpg",
        "IMG0002834.jpg",
        "IMG0003798.jpg",
        "IMG0004009.jpg",
        "IMG0004207.jpg"
      ]
    },
    "fracture_Dice_loss_over_02": {
      "n": 27,
      "image_ids": [
        "IMG0000019.jpg",
        "IMG0000319.jpg",
        "IMG0000471.jpg",
        "IMG0001073.jpg",
        "IMG0002086.jpg",
        "IMG0002181.jpg",
        "IMG0002323.jpg",
        "IMG0002342.jpg",
        "IMG0002374.jpg",
        "IMG0002397.jpg",
        "IMG0002442.jpg",
        "IMG0002449.jpg",
        "IMG0002480.jpg",
        "IMG0002516.jpg",
        "IMG0002518.jpg",
        "IMG0002524.jpg",
        "IMG0002558.jpg",
        "IMG0002602.jpg",
        "IMG0002606.jpg",
        "IMG0002732.jpg",
        "IMG0002934.jpg",
        "IMG0003111.jpg",
        "IMG0003342.jpg",
        "IMG0003843.jpg",
        "IMG0003927.jpg",
        "IMG0004044.jpg",
        "IMG0004071.jpg"
      ]
    }
  },
  "original_instance_localization": {
    "precision": 0.04093567251461988,
    "recall": 0.35353535353535354
  },
  "matched_instance_localization": {
    "matches": 33,
    "gt": 99,
    "predicted": 436,
    "precision": 0.07568807339449542,
    "recall": 0.3333333333333333,
    "false_positive_regions": 403,
    "missed_regions": 66
  },
  "uncalibrated_proxy_regressions": {
    "brier_score": false,
    "expected_calibration_error": false
  },
  "calibration_gate_still_required": true,
  "validation_gate_checks": {
    "classification_counts": false,
    "native_positive_dice": false,
    "native_positive_iou": false,
    "instance_precision": true,
    "instance_recall": false,
    "false_positive_pixels": true,
    "useful_pixel_coverage_vs_matched": true
  },
  "validation_numerical_gate_pass": false,
  "original_pixel_recall": 0.7302353574224677,
  "candidate_pixel_recall": 0.5100745421763867,
  "manual_native_coverage_review_required": true,
  "decision": "KEEP FOR DEVELOPMENT; full further gates required",
  "final_success": false,
  "promotion": false,
  "calibration_fit": false,
  "test_images_read": 0,
  "limitations": [
    "Numerical checks never substitute for actual FP/FN/GT/mask inspection",
    "Original useful coverage must be assessed even when candidate exceeds an underfit matched reference",
    "No patient/study IDs or expert clinical subtype adjudication",
    "One seed and no external validation; component-box AP remains a proxy"
  ]
}

Inspect actual masks and original coverage. No automatic calibration, test evaluation or promotion.
