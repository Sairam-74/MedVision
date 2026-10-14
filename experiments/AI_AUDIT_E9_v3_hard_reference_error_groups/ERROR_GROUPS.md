# Validation false-positive groups

Measured pixel placement and source metadata, not clinical causes. All463 validation cases remain unchanged.

209 normal cases falsely flagged.

## Nonexclusive technical groups

| Group | Cases | Representative IDs |
|---|---:|---|
| gradient_edge_enrichment_over2 | 171 | IMG0003582.jpg, IMG0000208.jpg, IMG0000219.jpg |
| source_multiscan_flag | 27 | IMG0000008.jpg, IMG0002072.jpg, IMG0002271.jpg |
| other_FP_unadjudicated | 28 | IMG0000040.jpg, IMG0003555.jpg, IMG0000902.jpg |
| source_hardware_flag | 1 | IMG0000201.jpg |

Border band:2% of shortest native image dimension; dominant means >50% of predicted pixels. Edge enrichment compares predicted area overlap with the highest10% Sobel-gradient pixels to their image prevalence; tag threshold2x. This cannot distinguish normal cortex, overlapping bone, casts, metal or acquisition artifacts without individual expert review.

Hardware/multiscan/view/anatomy fields are provider metadata. Their association with false-positive rate is not causation. Casts, subtle/nondisplaced clinical labels and paired study identities are unavailable.

Every flagged normal mask count reproduces saved native false-positive pixels. FP_pixel_diagnostics.json links actual review panels. error_groups.json contains all view/anatomy/quality strata and positive failures. No validation case was removed and no test image was decoded.
