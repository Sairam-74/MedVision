# Matched positive-case Dice weighting

REJECT as balanced overall improvement at registered operating point

{
  "reference": "experiments\\AI_AUDIT_E11_v3_positive_Dice_reference",
  "candidate": "experiments\\AI_AUDIT_E12_v3_positive_Dice2",
  "factor": "Positive-case Dice coefficient1 versus2; all-image BCE, normal Dice and hard factor2 unchanged",
  "all_other_configurations_matched": true,
  "initial_model_optimizer_matched": true,
  "metrics": {
    "classification": {
      "accuracy": {
        "reference": 0.6652267818574514,
        "candidate": 0.6328293736501079,
        "absolute_delta": -0.03239740820734349
      },
      "precision": {
        "reference": 0.32524271844660196,
        "candidate": 0.29767441860465116,
        "absolute_delta": -0.027568299841950805
      },
      "recall_sensitivity": {
        "reference": 0.8072289156626506,
        "candidate": 0.7710843373493976,
        "absolute_delta": -0.03614457831325302
      },
      "specificity": {
        "reference": 0.6342105263157894,
        "candidate": 0.6026315789473684,
        "absolute_delta": -0.03157894736842104
      },
      "f1": {
        "reference": 0.46366782006920415,
        "candidate": 0.42953020134228187,
        "absolute_delta": -0.03413761872692228
      },
      "auroc": {
        "reference": 0.8073557387444514,
        "candidate": 0.8016487000634116,
        "absolute_delta": -0.005707038681039833
      },
      "auprc_average_precision": {
        "reference": 0.5640968306229868,
        "candidate": 0.6051604275189888,
        "absolute_delta": 0.04106359689600203
      },
      "false_positive_rate": {
        "reference": 0.36578947368421055,
        "candidate": 0.3973684210526316,
        "absolute_delta": 0.03157894736842104
      },
      "false_negative_rate": {
        "reference": 0.1927710843373494,
        "candidate": 0.2289156626506024,
        "absolute_delta": 0.03614457831325299
      }
    },
    "segmentation": {
      "mean_positive_dice": {
        "reference": 0.375113809566179,
        "candidate": 0.3833219034105424,
        "absolute_delta": 0.008208093844363384
      },
      "mean_positive_iou": {
        "reference": 0.2841692169147649,
        "candidate": 0.28467616895570175,
        "absolute_delta": 0.00050695204093687
      },
      "global_pixel_precision": {
        "reference": 0.31938019522200944,
        "candidate": 0.35047943526010816,
        "absolute_delta": 0.03109924003809872
      },
      "global_pixel_recall": {
        "reference": 0.22712794579307213,
        "candidate": 0.3462857696613597,
        "absolute_delta": 0.11915782386828758
      },
      "global_dice": {
        "reference": 0.26546783926413103,
        "candidate": 0.3483699821181638,
        "absolute_delta": 0.08290214285403275
      },
      "global_iou": {
        "reference": 0.15304866941844839,
        "candidate": 0.21092495192412244,
        "absolute_delta": 0.05787628250567406
      }
    },
    "calibration": {
      "brier_score": {
        "reference": 0.27451683942151467,
        "candidate": 0.29269133401836156,
        "absolute_delta": 0.01817449459684689
      },
      "expected_calibration_error": {
        "reference": 0.28046054608861415,
        "candidate": 0.3118154425591383,
        "absolute_delta": 0.03135489647052414
      }
    }
  },
  "original_same_ID_comparison": {
    "classification": {
      "accuracy": {
        "reference": 0.27213822894168466,
        "candidate": 0.6328293736501079,
        "absolute_delta": 0.3606911447084233
      },
      "precision": {
        "reference": 0.1976190476190476,
        "candidate": 0.29767441860465116,
        "absolute_delta": 0.10005537098560355
      },
      "recall_sensitivity": {
        "reference": 1.0,
        "candidate": 0.7710843373493976,
        "absolute_delta": -0.22891566265060237
      },
      "specificity": {
        "reference": 0.11315789473684211,
        "candidate": 0.6026315789473684,
        "absolute_delta": 0.4894736842105263
      },
      "f1": {
        "reference": 0.33001988071570576,
        "candidate": 0.42953020134228187,
        "absolute_delta": 0.09951032062657611
      },
      "auroc": {
        "reference": 0.6018072289156626,
        "candidate": 0.8016487000634116,
        "absolute_delta": 0.19984147114774897
      },
      "auprc_average_precision": {
        "reference": 0.2156616190058667,
        "candidate": 0.6051604275189888,
        "absolute_delta": 0.38949880851312213
      },
      "false_positive_rate": {
        "reference": 0.8868421052631579,
        "candidate": 0.3973684210526316,
        "absolute_delta": -0.4894736842105263
      },
      "false_negative_rate": {
        "reference": 0.0,
        "candidate": 0.2289156626506024,
        "absolute_delta": 0.2289156626506024
      }
    },
    "segmentation": {
      "mean_positive_dice": {
        "reference": 0.5037965562512774,
        "candidate": 0.3833219034105424,
        "absolute_delta": -0.120474652840735
      },
      "mean_positive_iou": {
        "reference": 0.3775685932913787,
        "candidate": 0.28467616895570175,
        "absolute_delta": -0.09289242433567696
      },
      "global_pixel_precision": {
        "reference": 0.09956511867180212,
        "candidate": 0.35047943526010816,
        "absolute_delta": 0.25091431658830604
      },
      "global_pixel_recall": {
        "reference": 0.7302353574224677,
        "candidate": 0.3462857696613597,
        "absolute_delta": -0.383949587761108
      },
      "global_dice": {
        "reference": 0.17523723380427186,
        "candidate": 0.3483699821181638,
        "absolute_delta": 0.17313274831389192
      },
      "global_iou": {
        "reference": 0.09603288550741698,
        "candidate": 0.21092495192412244,
        "absolute_delta": 0.11489206641670546
      }
    },
    "calibration": {
      "brier_score": {
        "reference": 0.7387043871964329,
        "candidate": 0.29269133401836156,
        "absolute_delta": -0.4460130531780714
      },
      "expected_calibration_error": {
        "reference": 0.745993458819284,
        "candidate": 0.3118154425591383,
        "absolute_delta": -0.43417801626014574
      }
    }
  },
  "independent_mask_error_transitions": {
    "normal_FP_recovered": {
      "n": 51,
      "image_ids": [
        "IMG0000050.jpg",
        "IMG0000123.jpg",
        "IMG0000285.jpg",
        "IMG0000295.jpg",
        "IMG0000603.jpg",
        "IMG0000619.jpg",
        "IMG0000631.jpg",
        "IMG0001015.jpg",
        "IMG0001237.jpg",
        "IMG0001249.jpg",
        "IMG0001263.jpg",
        "IMG0001433.jpg",
        "IMG0001486.jpg",
        "IMG0001557.jpg",
        "IMG0001605.jpg",
        "IMG0001646.jpg",
        "IMG0001647.jpg",
        "IMG0001678.jpg",
        "IMG0001837.jpg",
        "IMG0001972.jpg",
        "IMG0002063.jpg",
        "IMG0002066.jpg",
        "IMG0002098.jpg",
        "IMG0002185.jpg",
        "IMG0002187.jpg",
        "IMG0002188.jpg",
        "IMG0002200.jpg",
        "IMG0002662.jpg",
        "IMG0002702.jpg",
        "IMG0002706.jpg",
        "IMG0002835.jpg",
        "IMG0002942.jpg",
        "IMG0002956.jpg",
        "IMG0002989.jpg",
        "IMG0003314.jpg",
        "IMG0003439.jpg",
        "IMG0003492.jpg",
        "IMG0003537.jpg",
        "IMG0003547.jpg",
        "IMG0003555.jpg",
        "IMG0003599.jpg",
        "IMG0003603.jpg",
        "IMG0003692.jpg",
        "IMG0003735.jpg",
        "IMG0003775.jpg",
        "IMG0003791.jpg",
        "IMG0003917.jpg",
        "IMG0003969.jpg",
        "IMG0003992.jpg",
        "IMG0004062.jpg",
        "IMG0004260.jpg"
      ]
    },
    "normal_new_FP": {
      "n": 63,
      "image_ids": [
        "IMG0000008.jpg",
        "IMG0000038.jpg",
        "IMG0000081.jpg",
        "IMG0000086.jpg",
        "IMG0000130.jpg",
        "IMG0000149.jpg",
        "IMG0000201.jpg",
        "IMG0000214.jpg",
        "IMG0000219.jpg",
        "IMG0000224.jpg",
        "IMG0000227.jpg",
        "IMG0000267.jpg",
        "IMG0000315.jpg",
        "IMG0000336.jpg",
        "IMG0000398.jpg",
        "IMG0000415.jpg",
        "IMG0000462.jpg",
        "IMG0000545.jpg",
        "IMG0000589.jpg",
        "IMG0000612.jpg",
        "IMG0000643.jpg",
        "IMG0000704.jpg",
        "IMG0000732.jpg",
        "IMG0000739.jpg",
        "IMG0000782.jpg",
        "IMG0000793.jpg",
        "IMG0001113.jpg",
        "IMG0001207.jpg",
        "IMG0001243.jpg",
        "IMG0001527.jpg",
        "IMG0001583.jpg",
        "IMG0001604.jpg",
        "IMG0001735.jpg",
        "IMG0001741.jpg",
        "IMG0001745.jpg",
        "IMG0001752.jpg",
        "IMG0001778.jpg",
        "IMG0001854.jpg",
        "IMG0001888.jpg",
        "IMG0002058.jpg",
        "IMG0002090.jpg",
        "IMG0002144.jpg",
        "IMG0002178.jpg",
        "IMG0002747.jpg",
        "IMG0002753.jpg",
        "IMG0002782.jpg",
        "IMG0002820.jpg",
        "IMG0002871.jpg",
        "IMG0002881.jpg",
        "IMG0002911.jpg",
        "IMG0002958.jpg",
        "IMG0002997.jpg",
        "IMG0003008.jpg",
        "IMG0003078.jpg",
        "IMG0003143.jpg",
        "IMG0003224.jpg",
        "IMG0003343.jpg",
        "IMG0003516.jpg",
        "IMG0003535.jpg",
        "IMG0003583.jpg",
        "IMG0003696.jpg",
        "IMG0003714.jpg",
        "IMG0003987.jpg"
      ]
    },
    "fracture_FN_recovered": {
      "n": 7,
      "image_ids": [
        "IMG0000471.jpg",
        "IMG0001948.jpg",
        "IMG0002303.jpg",
        "IMG0002374.jpg",
        "IMG0002584.jpg",
        "IMG0002619.jpg",
        "IMG0002732.jpg"
      ]
    },
    "fracture_new_FN": {
      "n": 10,
      "image_ids": [
        "IMG0000019.jpg",
        "IMG0001367.jpg",
        "IMG0001391.jpg",
        "IMG0002086.jpg",
        "IMG0002342.jpg",
        "IMG0002392.jpg",
        "IMG0002465.jpg",
        "IMG0002502.jpg",
        "IMG0002587.jpg",
        "IMG0003797.jpg"
      ]
    },
    "fracture_new_zero_overlap": {
      "n": 1,
      "image_ids": [
        "IMG0002586.jpg"
      ]
    },
    "fracture_Dice_gain_over_02": {
      "n": 21,
      "image_ids": [
        "IMG0000471.jpg",
        "IMG0001362.jpg",
        "IMG0001365.jpg",
        "IMG0002021.jpg",
        "IMG0002208.jpg",
        "IMG0002303.jpg",
        "IMG0002304.jpg",
        "IMG0002311.jpg",
        "IMG0002323.jpg",
        "IMG0002349.jpg",
        "IMG0002372.jpg",
        "IMG0002374.jpg",
        "IMG0002402.jpg",
        "IMG0002472.jpg",
        "IMG0002480.jpg",
        "IMG0002493.jpg",
        "IMG0002518.jpg",
        "IMG0002549.jpg",
        "IMG0002558.jpg",
        "IMG0003523.jpg",
        "IMG0004044.jpg"
      ]
    },
    "fracture_Dice_loss_over_02": {
      "n": 31,
      "image_ids": [
        "IMG0000019.jpg",
        "IMG0000470.jpg",
        "IMG0000851.jpg",
        "IMG0001198.jpg",
        "IMG0001367.jpg",
        "IMG0001391.jpg",
        "IMG0001411.jpg",
        "IMG0001933.jpg",
        "IMG0002085.jpg",
        "IMG0002086.jpg",
        "IMG0002333.jpg",
        "IMG0002342.jpg",
        "IMG0002397.jpg",
        "IMG0002441.jpg",
        "IMG0002442.jpg",
        "IMG0002449.jpg",
        "IMG0002524.jpg",
        "IMG0002535.jpg",
        "IMG0002553.jpg",
        "IMG0002587.jpg",
        "IMG0002606.jpg",
        "IMG0002647.jpg",
        "IMG0002831.jpg",
        "IMG0002834.jpg",
        "IMG0003111.jpg",
        "IMG0003217.jpg",
        "IMG0003342.jpg",
        "IMG0003843.jpg",
        "IMG0004009.jpg",
        "IMG0004071.jpg",
        "IMG0004207.jpg"
      ]
    }
  },
  "conservative_alert_error_transitions": {
    "normal_FP_recovered": {
      "n": 51,
      "image_ids": [
        "IMG0000050.jpg",
        "IMG0000123.jpg",
        "IMG0000285.jpg",
        "IMG0000295.jpg",
        "IMG0000603.jpg",
        "IMG0000619.jpg",
        "IMG0000631.jpg",
        "IMG0001015.jpg",
        "IMG0001237.jpg",
        "IMG0001249.jpg",
        "IMG0001263.jpg",
        "IMG0001433.jpg",
        "IMG0001486.jpg",
        "IMG0001557.jpg",
        "IMG0001605.jpg",
        "IMG0001646.jpg",
        "IMG0001647.jpg",
        "IMG0001678.jpg",
        "IMG0001837.jpg",
        "IMG0001972.jpg",
        "IMG0002063.jpg",
        "IMG0002066.jpg",
        "IMG0002098.jpg",
        "IMG0002185.jpg",
        "IMG0002187.jpg",
        "IMG0002188.jpg",
        "IMG0002200.jpg",
        "IMG0002662.jpg",
        "IMG0002702.jpg",
        "IMG0002706.jpg",
        "IMG0002835.jpg",
        "IMG0002942.jpg",
        "IMG0002956.jpg",
        "IMG0002989.jpg",
        "IMG0003314.jpg",
        "IMG0003439.jpg",
        "IMG0003492.jpg",
        "IMG0003537.jpg",
        "IMG0003547.jpg",
        "IMG0003555.jpg",
        "IMG0003599.jpg",
        "IMG0003603.jpg",
        "IMG0003692.jpg",
        "IMG0003735.jpg",
        "IMG0003775.jpg",
        "IMG0003791.jpg",
        "IMG0003917.jpg",
        "IMG0003969.jpg",
        "IMG0003992.jpg",
        "IMG0004062.jpg",
        "IMG0004260.jpg"
      ]
    },
    "normal_new_FP": {
      "n": 63,
      "image_ids": [
        "IMG0000008.jpg",
        "IMG0000038.jpg",
        "IMG0000081.jpg",
        "IMG0000086.jpg",
        "IMG0000130.jpg",
        "IMG0000149.jpg",
        "IMG0000201.jpg",
        "IMG0000214.jpg",
        "IMG0000219.jpg",
        "IMG0000224.jpg",
        "IMG0000227.jpg",
        "IMG0000267.jpg",
        "IMG0000315.jpg",
        "IMG0000336.jpg",
        "IMG0000398.jpg",
        "IMG0000415.jpg",
        "IMG0000462.jpg",
        "IMG0000545.jpg",
        "IMG0000589.jpg",
        "IMG0000612.jpg",
        "IMG0000643.jpg",
        "IMG0000704.jpg",
        "IMG0000732.jpg",
        "IMG0000739.jpg",
        "IMG0000782.jpg",
        "IMG0000793.jpg",
        "IMG0001113.jpg",
        "IMG0001207.jpg",
        "IMG0001243.jpg",
        "IMG0001527.jpg",
        "IMG0001583.jpg",
        "IMG0001604.jpg",
        "IMG0001735.jpg",
        "IMG0001741.jpg",
        "IMG0001745.jpg",
        "IMG0001752.jpg",
        "IMG0001778.jpg",
        "IMG0001854.jpg",
        "IMG0001888.jpg",
        "IMG0002058.jpg",
        "IMG0002090.jpg",
        "IMG0002144.jpg",
        "IMG0002178.jpg",
        "IMG0002747.jpg",
        "IMG0002753.jpg",
        "IMG0002782.jpg",
        "IMG0002820.jpg",
        "IMG0002871.jpg",
        "IMG0002881.jpg",
        "IMG0002911.jpg",
        "IMG0002958.jpg",
        "IMG0002997.jpg",
        "IMG0003008.jpg",
        "IMG0003078.jpg",
        "IMG0003143.jpg",
        "IMG0003224.jpg",
        "IMG0003343.jpg",
        "IMG0003516.jpg",
        "IMG0003535.jpg",
        "IMG0003583.jpg",
        "IMG0003696.jpg",
        "IMG0003714.jpg",
        "IMG0003987.jpg"
      ]
    },
    "fracture_FN_recovered": {
      "n": 7,
      "image_ids": [
        "IMG0000471.jpg",
        "IMG0001948.jpg",
        "IMG0002303.jpg",
        "IMG0002374.jpg",
        "IMG0002584.jpg",
        "IMG0002619.jpg",
        "IMG0002732.jpg"
      ]
    },
    "fracture_new_FN": {
      "n": 10,
      "image_ids": [
        "IMG0000019.jpg",
        "IMG0001367.jpg",
        "IMG0001391.jpg",
        "IMG0002086.jpg",
        "IMG0002342.jpg",
        "IMG0002392.jpg",
        "IMG0002465.jpg",
        "IMG0002502.jpg",
        "IMG0002587.jpg",
        "IMG0003797.jpg"
      ]
    },
    "fracture_new_zero_overlap": {
      "n": 1,
      "image_ids": [
        "IMG0002586.jpg"
      ]
    },
    "fracture_Dice_gain_over_02": {
      "n": 21,
      "image_ids": [
        "IMG0000471.jpg",
        "IMG0001362.jpg",
        "IMG0001365.jpg",
        "IMG0002021.jpg",
        "IMG0002208.jpg",
        "IMG0002303.jpg",
        "IMG0002304.jpg",
        "IMG0002311.jpg",
        "IMG0002323.jpg",
        "IMG0002349.jpg",
        "IMG0002372.jpg",
        "IMG0002374.jpg",
        "IMG0002402.jpg",
        "IMG0002472.jpg",
        "IMG0002480.jpg",
        "IMG0002493.jpg",
        "IMG0002518.jpg",
        "IMG0002549.jpg",
        "IMG0002558.jpg",
        "IMG0003523.jpg",
        "IMG0004044.jpg"
      ]
    },
    "fracture_Dice_loss_over_02": {
      "n": 31,
      "image_ids": [
        "IMG0000019.jpg",
        "IMG0000470.jpg",
        "IMG0000851.jpg",
        "IMG0001198.jpg",
        "IMG0001367.jpg",
        "IMG0001391.jpg",
        "IMG0001411.jpg",
        "IMG0001933.jpg",
        "IMG0002085.jpg",
        "IMG0002086.jpg",
        "IMG0002333.jpg",
        "IMG0002342.jpg",
        "IMG0002397.jpg",
        "IMG0002441.jpg",
        "IMG0002442.jpg",
        "IMG0002449.jpg",
        "IMG0002524.jpg",
        "IMG0002535.jpg",
        "IMG0002553.jpg",
        "IMG0002587.jpg",
        "IMG0002606.jpg",
        "IMG0002647.jpg",
        "IMG0002831.jpg",
        "IMG0002834.jpg",
        "IMG0003111.jpg",
        "IMG0003217.jpg",
        "IMG0003342.jpg",
        "IMG0003843.jpg",
        "IMG0004009.jpg",
        "IMG0004071.jpg",
        "IMG0004207.jpg"
      ]
    }
  },
  "original_instance_localization": {
    "precision": 0.04093567251461988,
    "recall": 0.35353535353535354
  },
  "validation_gate_checks": {
    "classification_counts": false,
    "native_positive_dice": false,
    "native_positive_iou": false,
    "instance_precision": true,
    "instance_recall": false,
    "false_positive_pixels": false,
    "useful_pixel_coverage_vs_matched": true
  },
  "validation_numerical_gate_pass": false,
  "original_pixel_recall": 0.7302353574224677,
  "candidate_pixel_recall": 0.3462857696613597,
  "manual_native_coverage_review_required": true,
  "decision": "REJECT as balanced overall improvement at registered operating point",
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
