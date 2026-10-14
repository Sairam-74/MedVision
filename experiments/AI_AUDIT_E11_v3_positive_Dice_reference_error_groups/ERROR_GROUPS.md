# Validation false-positive groups

Measured pixel placement and source metadata, not clinical causes. All463 validation cases remain unchanged.

139 normal cases falsely flagged.

## Nonexclusive technical groups

| Group | Cases | Representative IDs |
|---|---:|---|
| other_FP_unadjudicated | 15 | IMG0003002.jpg, IMG0004277.jpg, IMG0003599.jpg |
| gradient_edge_enrichment_over2 | 118 | IMG0000990.jpg, IMG0000878.jpg, IMG0002072.jpg |
| source_multiscan_flag | 19 | IMG0002072.jpg, IMG0001646.jpg, IMG0000295.jpg |

Border band:2% of shortest native image dimension; dominant means >50% of predicted pixels. Edge enrichment compares predicted area overlap with the highest10% Sobel-gradient pixels to their image prevalence; tag threshold2x. This cannot distinguish normal cortex, overlapping bone, casts, metal or acquisition artifacts without individual expert review.

Hardware/multiscan/view/anatomy fields are provider metadata. Their association with false-positive rate is not causation. Casts, subtle/nondisplaced clinical labels and paired study identities are unavailable.

Every flagged normal mask count reproduces saved native false-positive pixels. FP_pixel_diagnostics.json links actual review panels. error_groups.json contains all view/anatomy/quality strata and positive failures. No validation case was removed and no test image was decoded.
