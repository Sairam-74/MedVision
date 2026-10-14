# Validation false-positive groups

Measured pixel placement and source metadata, not clinical causes. All463 validation cases remain unchanged.

143 normal cases falsely flagged.

## Nonexclusive technical groups

| Group | Cases | Representative IDs |
|---|---:|---|
| gradient_edge_enrichment_over2 | 134 | IMG0000990.jpg, IMG0001879.jpg, IMG0002072.jpg |
| other_FP_unadjudicated | 8 | IMG0001764.jpg, IMG0000170.jpg, IMG0002023.jpg |
| source_hardware_flag | 1 | IMG0000201.jpg |
| source_multiscan_flag | 13 | IMG0002072.jpg, IMG0002185.jpg, IMG0002200.jpg |

Border band:2% of shortest native image dimension; dominant means >50% of predicted pixels. Edge enrichment compares predicted area overlap with the highest10% Sobel-gradient pixels to their image prevalence; tag threshold2x. This cannot distinguish normal cortex, overlapping bone, casts, metal or acquisition artifacts without individual expert review.

Hardware/multiscan/view/anatomy fields are provider metadata. Their association with false-positive rate is not causation. Casts, subtle/nondisplaced clinical labels and paired study identities are unavailable.

Every flagged normal mask count reproduces saved native false-positive pixels. FP_pixel_diagnostics.json links actual review panels. error_groups.json contains all view/anatomy/quality strata and positive failures. No validation case was removed and no test image was decoded.
