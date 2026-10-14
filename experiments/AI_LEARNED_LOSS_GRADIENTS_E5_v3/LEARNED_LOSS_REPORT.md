# Measured loss-gradient diagnostic

The completed E5 selected epoch8 checkpoint was evaluated on16 prespecified, unaugmented TRAIN examples: eight positives spanning annotation-area ranks and eight seeded normals. No optimizer step, validation inference, calibration fitting or test access occurred. Analytic derivatives for the existing BCE/Dice expressions matched autograd on a small fixture.

On these eight normal examples, mean Dice loss was0.99999998 while median Dice logit-gradient L2 was2.24e-10. Median normal BCE logit-gradient L2 was1.16e-4. Thus normal Dice contributes a nearly constant loss value with extremely weak gradient here; normal BCE remains active. A total training loss near1 does not by itself quantify effective normal-region learning. The small1e-6 smoothing and empty targets explain this mathematical behavior; this is not evidence that normal BCE is absent.

For the eight positive examples, mean Dice loss was0.882209, median soft Dice0.000852, median Dice logit-gradient L2 was5.51e-5, and median BCE gradient L2 was2.63e-4. Some positive masks are poorly fitted even on TRAIN under checkpoint evaluation. Individual actual cases, target/prediction masses and encoder/decoder gradient norms are retained in per_case.json.

This16-case diagnostic is not a whole-TRAIN gradient estimate, a training-mode SGD trajectory, a causal proof that one loss change will fix failures, or an improvement result. Positives were deliberately sampled across annotation areas and the sample is not prevalence-representative. Do not multiply sample median norms by class counts to assert aggregate gradient dominance. BatchNorm evaluation state and augmentation context also differ from training.

The current E7/E8 presence-supervision experiment remains frozen. After its completed native analysis, these findings may support a separately controlled positive-mask Dice reduction/weighting or hard-background objective experiment, with normal BCE preserved. Any such intervention must be measured against a matched reference and the independent-mask gate; it is not yet implemented or selected.
