# MedVision Phase 3 dataset audit

Executed 6 October 2026. Read-only inspection preserved the original ZIP, checkpoint, threshold, active trainer and v1 manifest. This report supersedes earlier statements that candidate visual review or dataset licensing was unverified.

## Source, version and use terms

The local archive exactly matches **FracAtlas version 6**, DOI [10.6084/m9.figshare.22363012.v6](https://doi.org/10.6084/m9.figshare.22363012.v6), by published size **338,412,750 bytes** and MD5 **931dd40ad6e070bb0724d66cfbbef9f0**. Local SHA-256 is `747119b26f2684e0e35a7688083b14b12a206149b0cfe5357824b69b3a5e6cf8`. The provider's version-specific [API metadata](https://api.figshare.com/v2/articles/22363012/versions/6) specifies **CC BY 4.0**; records for versions 1–7 are saved in `figshare_versions.json`. Latest v7 differs in size/checksum and was not substituted. CC BY requires attribution, a license link and indication of changes; exclusions, grouping and mask union are documented here. This does not establish a license for the historical project checkpoint.

Cite Abedeen I, Rahman MA, Prottyasha FZ, Ahmed T, Chowdhury TM, Shatabda S. FracAtlas: A Dataset for Fracture Classification, Localization and Segmentation of Musculoskeletal Radiographs. Scientific Data 10, 521 (2023). [Article DOI](https://doi.org/10.1038/s41597-023-02432-4). [Official code/citation source](https://github.com/XLR8-07/FracAtlas).

## Integrity and revisions

The source CSV has 4,083 images: 717 fractured / 3,366 normal, with 922 COCO annotation instances. ZIP CRC passes. **59 normal JPEGs fail decoding** and are explicitly excluded, with no salvage or source edits. v1 has 4,024 images: 717 positive / 3,307 normal. Dimensions, polygon structure, label/mask presence and annotation counts were checked; no positive binary union vanishes at 256. This does not prove every individual instance survives resizing.

The deeper exact-decoded audit found **three contradictory case-label sets (seven images)**, all in training: IMG0002886/IMG0004243, IMG0002998/IMG0004280, and IMG0003034/IMG0004314/IMG0004341 (all .jpg). The same decoded content has both fractured and normal labels. `duplicate_label_audit.json` also records **17 exact-copy sets with differing native union masks**, including those three contradictions. The other **14 sets** retain provider positive annotations with differing region boundaries/counts; this uncertainty is disclosed rather than silently merged or clinically adjudicated.

**v2 quarantines all seven contradictory images** while preserving every remaining v1 split/group assignment. It contains **4,017 images: 714 fractured / 3,303 normal**, with 919 retained annotation instances. Train is **493 positive + 2,315 normal = 2,808**; validation **110 + 502 = 612** and test **111 + 486 = 597** are byte-for-byte unchanged in their ID files. v1 remains immutable for the active E2 run and historical measurements. v2 is a separately frozen revision for subsequent runs; do not resume E2 with changed data.

## Leakage checks and visual inspection

There are 78 decoded exact-duplicate groups and 306 perceptual candidate pairs (dHash Hamming distance <=4 AND 32x32 grayscale MAE <8), joined transitively into 3,756 v1 groups. **Zero known exact/candidate pairs or groups cross split boundaries**. All 217 non-exact candidate pairs were visually inspected in ten contact sheets; 89 exact candidate pairs are covered by decoded hashes. Many near candidates are visibly different projections or shapes, so grouping is conservative and may overgroup. Groups were retained unchanged. The screen can miss other related images; patient/study identifiers are unavailable, so patient independence is unverified. No exhaustive leakage-free claim is made.

Seventeen train/validation image-mask examples were reviewed across supplied anatomy/view labels, hardware, composites, multiple annotations and size/occupancy extrema. Native overlays and annotation crops show no evident systematic alignment shift in this sample. Broad fracture-region polygons are not physical crack widths or clinical severity. IMG0002572 retains five instances and IMG0000307 three in a composite image. See `annotation_review_selection.json`, `annotations_*.png`, and `visual_review.json`. No clinical relabeling or expert approval is claimed.

Test source images were inspected only where needed for duplicate/integrity auditing. No test model predictions, performance inspection, model/threshold selection or test qualitative failure selection was performed.

## Split distributions (v1, used by active E2)

Flags overlap and must not be added as mutually exclusive categories. These are metadata counts, not model metrics. v2 removes only the seven training contradictions; validation/test distributions remain unchanged.

| Flag | Train count (%) | Validation count (%) | Test count (%) |
|---|---|---|---|
| fractured | 496 (17.62%) | 110 (17.97%) | 111 (18.59%) |
| hand | 1051 (37.34%) | 237 (38.73%) | 222 (37.19%) |
| leg | 1571 (55.81%) | 340 (55.56%) | 334 (55.95%) |
| hip | 239 (8.49%) | 41 (6.70%) | 57 (9.55%) |
| shoulder | 235 (8.35%) | 54 (8.82%) | 54 (9.05%) |
| mixed | 271 (9.63%) | 58 (9.48%) | 65 (10.89%) |
| hardware | 65 (2.31%) | 11 (1.80%) | 23 (3.85%) |
| multiscan | 276 (9.80%) | 62 (10.13%) | 58 (9.72%) |
| frontal | 1748 (62.10%) | 384 (62.75%) | 343 (57.45%) |
| lateral | 1011 (35.91%) | 218 (35.62%) | 238 (39.87%) |
| oblique | 283 (10.05%) | 61 (9.97%) | 67 (11.22%) |

Hardware prevalence varies from 1.80% validation to 3.85% test; hip prevalence from 6.70% validation to 9.55% test. Rare positive validation subgroups are small (hip 7, oblique 6, hardware 10); any later subgroup scores must include denominators and uncertainty. Multi-fracture image counts are 103/26/42 (train/val/test). Native positive median foreground fractions are 0.344%/0.373%/0.405%; smallest positive 256 unions contain 40/48/45 pixels. The full width/height/aspect/occupancy quantiles are in `distributions.json`. Most images are already low-resolution: median native width 373 and height 454 in every split; enlargement cannot recover missing source detail.

## Reproducibility and execution status

`tools/phase3_review.py` regenerates metadata, native overlay/candidate sheets, duplicate-label checks and the new quarantine revision. It refuses to overwrite an existing data_v2 manifest. `tools/train_baseline_manifest.py` is an isolated copy of the verified trainer with explicit audited-subset manifest support; the running original trainer and medvision_ai.py hashes remain unchanged. A four-train/four-validation v2 smoke passed; this proves execution only, not performance. No competing full CPU run was launched.

Phase 3 computational audit is executed, with immutable manifests, explicit exclusions and no known cross-split duplicate leakage. Expert annotation/data-dictionary approval and patient independence remain unverified. Active E2 results use v1 with the disclosed contradictions; a future v2 run is a different protocol and must be named separately. The test remains reserved. See `DATA_DICTIONARY.md`, `duplicate_label_audit.json`, `experiments/data_v2/revision.json`, PROJECT_STATUS and the experiment registry.

v1 manifest SHA-256: `e931cd3d3dce044f7d8f43fefeda596d39d9dc8529453f5262441c1a64e20227`.
v2 manifest SHA-256: `19a950c34d96c0fc076fbb75bdeffbf2f0b262626817d61018eff31e907544bb`.

Exact subgroup counts for the quarantine revision are separately saved in `subgroups_v2.csv`; original active-run counts are in `subgroups.csv`.
