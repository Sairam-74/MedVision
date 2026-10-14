# Matched hard-example weighting

KEEP FOR DEVELOPMENT; full further gates required

{
  "reference": "experiments\\AI_AUDIT_E9_v3_hard_reference",
  "candidate": "experiments\\AI_AUDIT_E10_v3_hard_weight2",
  "factor": "Bounded per-source hard factor1 versus2; class total mass preserved; natural one-pass coverage",
  "all_other_configurations_matched": true,
  "initial_model_optimizer_matched": true,
  "metrics": {
    "classification": {
      "accuracy": {
        "reference": 0.5140388768898488,
        "candidate": 0.5356371490280778,
        "absolute_delta": 0.021598272138228958
      },
      "precision": {
        "reference": 0.2427536231884058,
        "candidate": 0.2518796992481203,
        "absolute_delta": 0.009126076059714522
      },
      "recall_sensitivity": {
        "reference": 0.8072289156626506,
        "candidate": 0.8072289156626506,
        "absolute_delta": 0.0
      },
      "specificity": {
        "reference": 0.45,
        "candidate": 0.4763157894736842,
        "absolute_delta": 0.02631578947368418
      },
      "f1": {
        "reference": 0.3732590529247911,
        "candidate": 0.3839541547277937,
        "absolute_delta": 0.010695101803002593
      },
      "auroc": {
        "reference": 0.7850982878883958,
        "candidate": 0.7852885225110969,
        "absolute_delta": 0.00019023462270117975
      },
      "auprc_average_precision": {
        "reference": 0.5926414243099495,
        "candidate": 0.5740392147714433,
        "absolute_delta": -0.01860220953850622
      },
      "false_positive_rate": {
        "reference": 0.55,
        "candidate": 0.5236842105263158,
        "absolute_delta": -0.026315789473684292
      },
      "false_negative_rate": {
        "reference": 0.1927710843373494,
        "candidate": 0.1927710843373494,
        "absolute_delta": 0.0
      }
    },
    "segmentation": {
      "mean_positive_dice": {
        "reference": 0.35934235628847794,
        "candidate": 0.37952753899387115,
        "absolute_delta": 0.020185182705393212
      },
      "mean_positive_iou": {
        "reference": 0.26556882623002753,
        "candidate": 0.28366748755665727,
        "absolute_delta": 0.01809866132662974
      },
      "global_pixel_precision": {
        "reference": 0.1462363912891242,
        "candidate": 0.2210863520389682,
        "absolute_delta": 0.07484996074984401
      },
      "global_pixel_recall": {
        "reference": 0.34402119721416785,
        "candidate": 0.42803734504382507,
        "absolute_delta": 0.08401614782965722
      },
      "global_dice": {
        "reference": 0.20523259440471137,
        "candidate": 0.29157220904882264,
        "absolute_delta": 0.08633961464411127
      },
      "global_iou": {
        "reference": 0.11435052462223638,
        "candidate": 0.17066697848932091,
        "absolute_delta": 0.05631645386708453
      }
    },
    "calibration": {
      "brier_score": {
        "reference": 0.4072090601840746,
        "candidate": 0.3627000717196485,
        "absolute_delta": -0.04450898846442608
      },
      "expected_calibration_error": {
        "reference": 0.4340871883559767,
        "candidate": 0.3985781925886298,
        "absolute_delta": -0.035508995767346896
      }
    }
  },
  "original_same_ID_comparison": {
    "classification": {
      "accuracy": {
        "reference": 0.27213822894168466,
        "candidate": 0.5356371490280778,
        "absolute_delta": 0.26349892008639314
      },
      "precision": {
        "reference": 0.1976190476190476,
        "candidate": 0.2518796992481203,
        "absolute_delta": 0.054260651629072704
      },
      "recall_sensitivity": {
        "reference": 1.0,
        "candidate": 0.8072289156626506,
        "absolute_delta": -0.19277108433734935
      },
      "specificity": {
        "reference": 0.11315789473684211,
        "candidate": 0.4763157894736842,
        "absolute_delta": 0.36315789473684207
      },
      "f1": {
        "reference": 0.33001988071570576,
        "candidate": 0.3839541547277937,
        "absolute_delta": 0.053934274012087946
      },
      "auroc": {
        "reference": 0.6018072289156626,
        "candidate": 0.7852885225110969,
        "absolute_delta": 0.1834812935954343
      },
      "auprc_average_precision": {
        "reference": 0.2156616190058667,
        "candidate": 0.5740392147714433,
        "absolute_delta": 0.3583775957655766
      },
      "false_positive_rate": {
        "reference": 0.8868421052631579,
        "candidate": 0.5236842105263158,
        "absolute_delta": -0.3631578947368421
      },
      "false_negative_rate": {
        "reference": 0.0,
        "candidate": 0.1927710843373494,
        "absolute_delta": 0.1927710843373494
      }
    },
    "segmentation": {
      "mean_positive_dice": {
        "reference": 0.5037965562512774,
        "candidate": 0.37952753899387115,
        "absolute_delta": -0.12426901725740624
      },
      "mean_positive_iou": {
        "reference": 0.3775685932913787,
        "candidate": 0.28366748755665727,
        "absolute_delta": -0.09390110573472144
      },
      "global_pixel_precision": {
        "reference": 0.09956511867180212,
        "candidate": 0.2210863520389682,
        "absolute_delta": 0.12152123336716608
      },
      "global_pixel_recall": {
        "reference": 0.7302353574224677,
        "candidate": 0.42803734504382507,
        "absolute_delta": -0.30219801237864263
      },
      "global_dice": {
        "reference": 0.17523723380427186,
        "candidate": 0.29157220904882264,
        "absolute_delta": 0.11633497524455078
      },
      "global_iou": {
        "reference": 0.09603288550741698,
        "candidate": 0.17066697848932091,
        "absolute_delta": 0.07463409298190393
      }
    },
    "calibration": {
      "brier_score": {
        "reference": 0.7387043871964329,
        "candidate": 0.3627000717196485,
        "absolute_delta": -0.3760043154767844
      },
      "expected_calibration_error": {
        "reference": 0.745993458819284,
        "candidate": 0.3985781925886298,
        "absolute_delta": -0.3474152662306542
      }
    }
  },
  "independent_mask_error_transitions": {
    "normal_FP_recovered": {
      "n": 56,
      "image_ids": [
        "IMG0000040.jpg",
        "IMG0000050.jpg",
        "IMG0000225.jpg",
        "IMG0000231.jpg",
        "IMG0000241.jpg",
        "IMG0000244.jpg",
        "IMG0000260.jpg",
        "IMG0000356.jpg",
        "IMG0000417.jpg",
        "IMG0000428.jpg",
        "IMG0000462.jpg",
        "IMG0000517.jpg",
        "IMG0000570.jpg",
        "IMG0000766.jpg",
        "IMG0000770.jpg",
        "IMG0000807.jpg",
        "IMG0000939.jpg",
        "IMG0001048.jpg",
        "IMG0001101.jpg",
        "IMG0001291.jpg",
        "IMG0001355.jpg",
        "IMG0001557.jpg",
        "IMG0001638.jpg",
        "IMG0001646.jpg",
        "IMG0001735.jpg",
        "IMG0001764.jpg",
        "IMG0001783.jpg",
        "IMG0001793.jpg",
        "IMG0001833.jpg",
        "IMG0001837.jpg",
        "IMG0001940.jpg",
        "IMG0001972.jpg",
        "IMG0002012.jpg",
        "IMG0002066.jpg",
        "IMG0002090.jpg",
        "IMG0002098.jpg",
        "IMG0002188.jpg",
        "IMG0002735.jpg",
        "IMG0002866.jpg",
        "IMG0002871.jpg",
        "IMG0002942.jpg",
        "IMG0003116.jpg",
        "IMG0003243.jpg",
        "IMG0003270.jpg",
        "IMG0003345.jpg",
        "IMG0003350.jpg",
        "IMG0003463.jpg",
        "IMG0003493.jpg",
        "IMG0003537.jpg",
        "IMG0003605.jpg",
        "IMG0003689.jpg",
        "IMG0003692.jpg",
        "IMG0003716.jpg",
        "IMG0003791.jpg",
        "IMG0003972.jpg",
        "IMG0004195.jpg"
      ]
    },
    "normal_new_FP": {
      "n": 46,
      "image_ids": [
        "IMG0000024.jpg",
        "IMG0000071.jpg",
        "IMG0000295.jpg",
        "IMG0000545.jpg",
        "IMG0000676.jpg",
        "IMG0000703.jpg",
        "IMG0000712.jpg",
        "IMG0000774.jpg",
        "IMG0000829.jpg",
        "IMG0000871.jpg",
        "IMG0000910.jpg",
        "IMG0000970.jpg",
        "IMG0000988.jpg",
        "IMG0001127.jpg",
        "IMG0001345.jpg",
        "IMG0001576.jpg",
        "IMG0001647.jpg",
        "IMG0001678.jpg",
        "IMG0001750.jpg",
        "IMG0001778.jpg",
        "IMG0001917.jpg",
        "IMG0002144.jpg",
        "IMG0002178.jpg",
        "IMG0002239.jpg",
        "IMG0002631.jpg",
        "IMG0002681.jpg",
        "IMG0002782.jpg",
        "IMG0002820.jpg",
        "IMG0002958.jpg",
        "IMG0003008.jpg",
        "IMG0003032.jpg",
        "IMG0003039.jpg",
        "IMG0003044.jpg",
        "IMG0003353.jpg",
        "IMG0003433.jpg",
        "IMG0003445.jpg",
        "IMG0003535.jpg",
        "IMG0003547.jpg",
        "IMG0003571.jpg",
        "IMG0003599.jpg",
        "IMG0003603.jpg",
        "IMG0003665.jpg",
        "IMG0003722.jpg",
        "IMG0003775.jpg",
        "IMG0003919.jpg",
        "IMG0003969.jpg"
      ]
    },
    "fracture_FN_recovered": {
      "n": 5,
      "image_ids": [
        "IMG0000471.jpg",
        "IMG0001710.jpg",
        "IMG0001948.jpg",
        "IMG0002086.jpg",
        "IMG0002392.jpg"
      ]
    },
    "fracture_new_FN": {
      "n": 5,
      "image_ids": [
        "IMG0001073.jpg",
        "IMG0002181.jpg",
        "IMG0002463.jpg",
        "IMG0002502.jpg",
        "IMG0002549.jpg"
      ]
    },
    "fracture_new_zero_overlap": {
      "n": 1,
      "image_ids": [
        "IMG0002834.jpg"
      ]
    },
    "fracture_Dice_gain_over_02": {
      "n": 27,
      "image_ids": [
        "IMG0000470.jpg",
        "IMG0000851.jpg",
        "IMG0001362.jpg",
        "IMG0001365.jpg",
        "IMG0001411.jpg",
        "IMG0001948.jpg",
        "IMG0002021.jpg",
        "IMG0002085.jpg",
        "IMG0002303.jpg",
        "IMG0002304.jpg",
        "IMG0002333.jpg",
        "IMG0002349.jpg",
        "IMG0002412.jpg",
        "IMG0002441.jpg",
        "IMG0002442.jpg",
        "IMG0002449.jpg",
        "IMG0002480.jpg",
        "IMG0002493.jpg",
        "IMG0002518.jpg",
        "IMG0002535.jpg",
        "IMG0002586.jpg",
        "IMG0003523.jpg",
        "IMG0003843.jpg",
        "IMG0004009.jpg",
        "IMG0004044.jpg",
        "IMG0004071.jpg",
        "IMG0004374.jpg"
      ]
    },
    "fracture_Dice_loss_over_02": {
      "n": 21,
      "image_ids": [
        "IMG0000019.jpg",
        "IMG0000190.jpg",
        "IMG0001041.jpg",
        "IMG0001198.jpg",
        "IMG0001367.jpg",
        "IMG0002323.jpg",
        "IMG0002402.jpg",
        "IMG0002409.jpg",
        "IMG0002463.jpg",
        "IMG0002472.jpg",
        "IMG0002516.jpg",
        "IMG0002549.jpg",
        "IMG0002558.jpg",
        "IMG0002606.jpg",
        "IMG0002834.jpg",
        "IMG0002849.jpg",
        "IMG0002934.jpg",
        "IMG0003111.jpg",
        "IMG0003342.jpg",
        "IMG0003927.jpg",
        "IMG0004207.jpg"
      ]
    }
  },
  "conservative_alert_error_transitions": {
    "normal_FP_recovered": {
      "n": 56,
      "image_ids": [
        "IMG0000040.jpg",
        "IMG0000050.jpg",
        "IMG0000225.jpg",
        "IMG0000231.jpg",
        "IMG0000241.jpg",
        "IMG0000244.jpg",
        "IMG0000260.jpg",
        "IMG0000356.jpg",
        "IMG0000417.jpg",
        "IMG0000428.jpg",
        "IMG0000462.jpg",
        "IMG0000517.jpg",
        "IMG0000570.jpg",
        "IMG0000766.jpg",
        "IMG0000770.jpg",
        "IMG0000807.jpg",
        "IMG0000939.jpg",
        "IMG0001048.jpg",
        "IMG0001101.jpg",
        "IMG0001291.jpg",
        "IMG0001355.jpg",
        "IMG0001557.jpg",
        "IMG0001638.jpg",
        "IMG0001646.jpg",
        "IMG0001735.jpg",
        "IMG0001764.jpg",
        "IMG0001783.jpg",
        "IMG0001793.jpg",
        "IMG0001833.jpg",
        "IMG0001837.jpg",
        "IMG0001940.jpg",
        "IMG0001972.jpg",
        "IMG0002012.jpg",
        "IMG0002066.jpg",
        "IMG0002090.jpg",
        "IMG0002098.jpg",
        "IMG0002188.jpg",
        "IMG0002735.jpg",
        "IMG0002866.jpg",
        "IMG0002871.jpg",
        "IMG0002942.jpg",
        "IMG0003116.jpg",
        "IMG0003243.jpg",
        "IMG0003270.jpg",
        "IMG0003345.jpg",
        "IMG0003350.jpg",
        "IMG0003463.jpg",
        "IMG0003493.jpg",
        "IMG0003537.jpg",
        "IMG0003605.jpg",
        "IMG0003689.jpg",
        "IMG0003692.jpg",
        "IMG0003716.jpg",
        "IMG0003791.jpg",
        "IMG0003972.jpg",
        "IMG0004195.jpg"
      ]
    },
    "normal_new_FP": {
      "n": 46,
      "image_ids": [
        "IMG0000024.jpg",
        "IMG0000071.jpg",
        "IMG0000295.jpg",
        "IMG0000545.jpg",
        "IMG0000676.jpg",
        "IMG0000703.jpg",
        "IMG0000712.jpg",
        "IMG0000774.jpg",
        "IMG0000829.jpg",
        "IMG0000871.jpg",
        "IMG0000910.jpg",
        "IMG0000970.jpg",
        "IMG0000988.jpg",
        "IMG0001127.jpg",
        "IMG0001345.jpg",
        "IMG0001576.jpg",
        "IMG0001647.jpg",
        "IMG0001678.jpg",
        "IMG0001750.jpg",
        "IMG0001778.jpg",
        "IMG0001917.jpg",
        "IMG0002144.jpg",
        "IMG0002178.jpg",
        "IMG0002239.jpg",
        "IMG0002631.jpg",
        "IMG0002681.jpg",
        "IMG0002782.jpg",
        "IMG0002820.jpg",
        "IMG0002958.jpg",
        "IMG0003008.jpg",
        "IMG0003032.jpg",
        "IMG0003039.jpg",
        "IMG0003044.jpg",
        "IMG0003353.jpg",
        "IMG0003433.jpg",
        "IMG0003445.jpg",
        "IMG0003535.jpg",
        "IMG0003547.jpg",
        "IMG0003571.jpg",
        "IMG0003599.jpg",
        "IMG0003603.jpg",
        "IMG0003665.jpg",
        "IMG0003722.jpg",
        "IMG0003775.jpg",
        "IMG0003919.jpg",
        "IMG0003969.jpg"
      ]
    },
    "fracture_FN_recovered": {
      "n": 5,
      "image_ids": [
        "IMG0000471.jpg",
        "IMG0001710.jpg",
        "IMG0001948.jpg",
        "IMG0002086.jpg",
        "IMG0002392.jpg"
      ]
    },
    "fracture_new_FN": {
      "n": 5,
      "image_ids": [
        "IMG0001073.jpg",
        "IMG0002181.jpg",
        "IMG0002463.jpg",
        "IMG0002502.jpg",
        "IMG0002549.jpg"
      ]
    },
    "fracture_new_zero_overlap": {
      "n": 1,
      "image_ids": [
        "IMG0002834.jpg"
      ]
    },
    "fracture_Dice_gain_over_02": {
      "n": 27,
      "image_ids": [
        "IMG0000470.jpg",
        "IMG0000851.jpg",
        "IMG0001362.jpg",
        "IMG0001365.jpg",
        "IMG0001411.jpg",
        "IMG0001948.jpg",
        "IMG0002021.jpg",
        "IMG0002085.jpg",
        "IMG0002303.jpg",
        "IMG0002304.jpg",
        "IMG0002333.jpg",
        "IMG0002349.jpg",
        "IMG0002412.jpg",
        "IMG0002441.jpg",
        "IMG0002442.jpg",
        "IMG0002449.jpg",
        "IMG0002480.jpg",
        "IMG0002493.jpg",
        "IMG0002518.jpg",
        "IMG0002535.jpg",
        "IMG0002586.jpg",
        "IMG0003523.jpg",
        "IMG0003843.jpg",
        "IMG0004009.jpg",
        "IMG0004044.jpg",
        "IMG0004071.jpg",
        "IMG0004374.jpg"
      ]
    },
    "fracture_Dice_loss_over_02": {
      "n": 21,
      "image_ids": [
        "IMG0000019.jpg",
        "IMG0000190.jpg",
        "IMG0001041.jpg",
        "IMG0001198.jpg",
        "IMG0001367.jpg",
        "IMG0002323.jpg",
        "IMG0002402.jpg",
        "IMG0002409.jpg",
        "IMG0002463.jpg",
        "IMG0002472.jpg",
        "IMG0002516.jpg",
        "IMG0002549.jpg",
        "IMG0002558.jpg",
        "IMG0002606.jpg",
        "IMG0002834.jpg",
        "IMG0002849.jpg",
        "IMG0002934.jpg",
        "IMG0003111.jpg",
        "IMG0003342.jpg",
        "IMG0003927.jpg",
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
    "false_positive_pixels": true,
    "useful_pixel_coverage_vs_matched": true
  },
  "validation_numerical_gate_pass": false,
  "original_pixel_recall": 0.7302353574224677,
  "candidate_pixel_recall": 0.42803734504382507,
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
