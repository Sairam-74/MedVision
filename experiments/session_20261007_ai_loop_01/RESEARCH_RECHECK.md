# Targeted source recheck during E6 execution

Trigger: E5's weak max-pixel discrimination and26 nonempty wrong-region positive masks. This follows existing R2 research; no generic search or external data substitution.

Robert Lindsey and colleagues,2018, *Deep neural network improves fracture detection by clinicians*, PNAS115:11591-11596, DOI10.1073/pnas.1806905115. [Primary PubMed record](https://pubmed.ncbi.nlm.nih.gov/30348771/), PMCID PMC6233134.

The primary record's Figure2 caption describes a U-Net extension with separate image fracture probability and conditional spatial heatmap, using aspect-preserving1024x512 preprocessing. Its135409 expert-labeled radiographs and wrist reader experiment differ substantially from this project's small mixed-anatomy dataset. Reported aided clinician sensitivity91.5%/specificity93.9% are published reader results, not MedVision scores.

Relevant local inference: investigate whether explicit case supervision improves discrimination while retaining the existing spatial decoder. A small shared-feature presence branch is a controlled hypothesis, not a guarantee. Preserve independent unfiltered mask metrics and all four classifier/mask disagreement groups; do not adopt the paper's display gating to conceal incorrect masks. No head is implemented or trained yet, and no resolution/preprocessing replacement is justified by this paper alone.

Access on7October: PubMed abstract and figure captions successfully read again. Linked PMC and EuropePMC full texts were unavailable (403/timeout), so this recheck does not claim full-text or supplementary-method access. Earlier cached notes are preserved separately. No research insight has produced a newly measured local gain.
