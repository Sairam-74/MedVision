# MedVision data dictionary

Verified 6 October 2026. Provider fields retain their supplied meaning; technical documentation is not clinical or guide approval. No patient IDs, demographics, physical pixel spacing or clinical severity labels are available in the joined manifest.

| Field | Stored type | Meaning / limitation |
|---|---|---|
| `image_id` | str | Provider JPEG filename; image identifier only, not patient/study identity. |
| `hand` | str | Provider binary hand-region presence flag. |
| `leg` | str | Provider binary leg-region presence flag. |
| `hip` | str | Provider binary hip-region presence flag. |
| `shoulder` | str | Provider binary shoulder-region presence flag. |
| `mixed` | str | Provider binary mixed-anatomy flag; anatomy labels are nonexclusive. |
| `hardware` | str | Provider binary hardware presence flag; not device brand or treatment outcome. |
| `multiscan` | str | Provider binary multiple-view/composite-image flag; not a reliable patient identifier. |
| `fractured` | str | Provider binary image-level fracture label; normals receive zero masks. Contradictory exact copies are quarantined in v2. |
| `fracture_count` | str | Provider number of fracture annotation instances, checked against COCO IDs; not connected-component count. |
| `frontal` | str | Provider binary frontal-view flag. |
| `lateral` | str | Provider binary lateral-view flag. |
| `oblique` | str | Provider binary oblique-view flag; view labels are nonexclusive. |
| `member` | str | Unique image path inside unchanged ZIP archive. |
| `width` | int | Decoded native width in pixels, checked against available COCO record. |
| `height` | int | Decoded native height in pixels, checked against available COCO record. |
| `sha256` | str | SHA-256 of original encoded image bytes. |
| `decoded_sha256` | str | SHA-256 of Python shape-string bytes followed by grayscale uint8 decoded bytes; OpenCV-specific identity check. |
| `mask_pixels` | int | Foreground pixels in native binary union of every COCO polygon; not physical area. |
| `mask_pixels_256` | int | Foreground pixels after nearest-neighbor stretch to 256 x 256; not proof of instance-level survival. |
| `annotation_ids` | list | All original COCO annotation IDs; individual polygons/instances remain in the unchanged archive. |
| `split` | str | Frozen train/val/test assignment. Derived augmentations remain in source split. |
| `group` | str | Minimum filename in conservative connected duplicate-candidate group; not patient ID. |

CSV numeric labels are stored as strings and converted explicitly at use. COCO segmentation lists contain alternating native x/y pixel coordinates. Training uses a binary union, not instance segmentation. `exclusions` is an explicit image-ID/reason ledger; `archive_sha256`, protocol, seed and grouping rules are manifest-level provenance. Missing patient identity cannot be reconstructed reliably from filename numbering.
