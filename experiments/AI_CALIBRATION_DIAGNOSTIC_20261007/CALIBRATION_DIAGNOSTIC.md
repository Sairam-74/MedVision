# Calibration diagnostic — not a detection improvement

Fit sigmoid mapping using149 calibration cases only; assess463 separate validation cases. No test inference or application change. Original model exposure remains unknown.

Raw max-pixel Brier 0.738704 -> mapped 0.148435; ECE 0.745993 -> 0.029344. Calibration-prevalence-only Brier 0.147133. The prevalence-only comparator is essential: a numerically better calibration score does not establish useful discrimination.

All masks, case predictions, false positives and false negatives remain unchanged. No accuracy, recall, specificity, localization or Dice improvement is attributed to this mapping. Mapping is NOT served. REJECT it as a sufficient reliability improvement. Continue targeted negative-supervision comparison and later independent calibration of an accepted fresh model.

Full fit parameters, denominators, raw/mapped ranking metrics and lineage: metrics.json. Equal-width10-bin ECE is sensitive to binning/sample size. This is neither external nor clinical validation.
