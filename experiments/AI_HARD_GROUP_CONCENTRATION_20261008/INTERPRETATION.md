# TRAIN objective concentration

This audit reads saved JSON metadata only. It does not decode images, inspect masks, run a model, or change the running experiment.

The 2,808 original TRAIN sources occupy 2,626 conservative related-image groups and 2,755 decoded-exact hash groups. The `excess_source_copies` statistic in the JSON means **source count minus distinct grouping keys**. For conservative groups it does not establish copied images: group members can have distinct decoded pixels, labels, and anatomy. No new resampling or file copies were introduced.

| Grouping / class | Reference objective-mass ESS | Factor2 ESS | Change |
|---|---:|---:|---:|
| Conservative groups, all sources | 2202.48 | 1945.91 | -11.65% |
| Conservative groups, fracture sources | 442.71 | 410.89 | -7.19% |
| Conservative groups, normal sources | 1827.22 | 1599.02 | -12.49% |
| Decoded-exact hash groups, all sources | 2698.45 | 2391.16 | -11.39% |

ESS is the algebraic concentration statistic `(sum group mass)^2 / sum(group mass^2)`. It is not a patient count, a statistical validation result, or a generalization estimate.

The largest existing related-image group, `IMG0001684.jpg`, has 13 source images and 12 distinct decoded hashes. Its effective objective mass rises from 13 to 16.874, or 0.463% to 0.601% of total TRAIN mass. The ten largest groups account for 2.35% of reference mass and 2.60% of candidate mass. These values show increased but bounded concentration.

All 109 hard positives have distinct decoded hashes and related-group IDs; two share exact decoded pixels with ordinary positives. The 713 hard negatives span 668 related groups and 692 decoded hashes. Forty-two hard-negative sources share a decoded hash with another hard negative, giving 21 redundant exact-pixel hard entries. This repetition is inherited from the source dataset.

Current TRAIN decoded-exact groups contain zero conflicting fracture/normal labels. Seven previously contradictory source cases remain quarantined. Ten conservative related-image groups contain both labels; this does not by itself establish contradictory annotations or a shared patient.

Seven previously documented exact-image mask-annotation variant groups retain at least two TRAIN sources. Hard positives `IMG0004233.jpg` and `IMG0004267.jpg` belong to variant pairs with `IMG0002905.jpg` and `IMG0002946.jpg`. Their different saved union-mask hashes indicate unresolved target ambiguity already documented in the historical audit. It is a concrete caution when interpreting hard-positive weighting, without proving a clinical cause or authorizing relabeling.

Keep the registered pair unchanged. Compare its measured outcomes before deciding whether this concentration or the existing annotation ambiguity requires a later controlled intervention.
