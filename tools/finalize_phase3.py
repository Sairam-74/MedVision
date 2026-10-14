"""Record the 6 October Phase 3 session from measured artifacts."""
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    out = ROOT / 'experiments/phase3_review'
    session = ROOT / 'experiments/session_20261006'
    m = json.loads((ROOT / 'experiments/data_v1/manifest.json').read_text())
    revision = json.loads((ROOT / 'experiments/data_v2/revision.json').read_text())
    labels = json.loads((out / 'duplicate_label_audit.json').read_text())
    distributions = json.loads((out / 'distributions.json').read_text())
    versions = json.loads((out / 'figshare_versions.json').read_text(encoding='utf-8-sig'))
    assert any(v['version'] == 6 and v['license']['name'] == 'CC BY 4.0' and
               any(f['computed_md5'] == '931dd40ad6e070bb0724d66cfbbef9f0' and f['size'] == 338412750 for f in v['files']) for v in versions)
    assert sha(ROOT / 'experiments/data_v1/manifest.json') == 'e931cd3d3dce044f7d8f43fefeda596d39d9dc8529453f5262441c1a64e20227'
    config = json.loads((ROOT / 'experiments/E2_corrected_baseline/config.json').read_text())
    assert sha(ROOT / 'medvision_ai.py') == config['medvision_source_sha256']
    assert sha(ROOT / 'tools/train_baseline.py') == config['source_sha256']
    smoke = json.loads((ROOT / 'experiments/E2_v2_manifest_smoke/state.json').read_text())
    assert smoke['status'] == 'completed' and smoke['smoke'] and not smoke['test_evaluated']
    revision['new_training_ready'] = True
    revision['next_requirement'] = 'Use tools/train_baseline_manifest.py in a NEW run; never resume E2 with changed data. Four-case train/val smoke passed; no full v2 run launched.'
    (ROOT / 'experiments/data_v2/revision.json').write_text(json.dumps(revision, indent=2))
    visual = {
        'reviewer':'Codex visual audit; not a radiologist or guide approval',
        'annotation_sheets_reviewed':['annotations_01.png','annotations_02.png','annotations_03.png'],
        'annotation_images_reviewed':17, 'annotation_selection':'Metadata coverage and extrema, train/validation only',
        'duplicate_sheets_reviewed':[f'duplicates_{i:02d}.png' for i in range(1,11)],
        'nonexact_pairs_reviewed':217, 'exact_candidate_pairs_verified_by_hash':89,
        'duplicate_review_scope':'Integrity/leakage review only; includes some test source-image pairs. No test predictions, performance review, or tuning.',
        'observations':[
            'Sampled native union overlays show no evident systematic shift or transposition; this is sampled technical QA, not clinical re-annotation.',
            'Masks describe broad polygonal fracture regions, including hardware and multiple-view images; they are not crack centerlines, widths, or clinical severity.',
            'IMG0002572 has five separate annotation instances, retained in the union; IMG0000307 has three across a composite image.',
            'Very similar copies occur among candidates, but many pairs differ visibly in projection/anatomical shape. dHash/MAE candidates do not prove patient identity.',
            'All candidate groups retained conservatively. No regrouping or reassignment after training launch; no exhaustive patient-level independence claim.',
            'Exact-decoded contradictory case labels affect seven training images; quarantine all seven in v2 without deciding which provider label is clinically correct.',
        ], 'human_clinical_or_guide_review':'Not performed; data dictionary is documented for technical use, not guide-approved.'}
    (out / 'visual_review.json').write_text(json.dumps(visual, indent=2))
    field_notes = {
        'image_id':'Provider JPEG filename; image identifier only, not patient/study identity.',
        'hand':'Provider binary hand-region presence flag.', 'leg':'Provider binary leg-region presence flag.',
        'hip':'Provider binary hip-region presence flag.', 'shoulder':'Provider binary shoulder-region presence flag.',
        'mixed':'Provider binary mixed-anatomy flag; anatomy labels are nonexclusive.',
        'hardware':'Provider binary hardware presence flag; not device brand or treatment outcome.',
        'multiscan':'Provider binary multiple-view/composite-image flag; not a reliable patient identifier.',
        'fractured':'Provider binary image-level fracture label; normals receive zero masks. Contradictory exact copies are quarantined in v2.',
        'fracture_count':'Provider number of fracture annotation instances, checked against COCO IDs; not connected-component count.',
        'frontal':'Provider binary frontal-view flag.', 'lateral':'Provider binary lateral-view flag.',
        'oblique':'Provider binary oblique-view flag; view labels are nonexclusive.',
        'member':'Unique image path inside unchanged ZIP archive.',
        'width':'Decoded native width in pixels, checked against available COCO record.',
        'height':'Decoded native height in pixels, checked against available COCO record.',
        'sha256':'SHA-256 of original encoded image bytes.',
        'decoded_sha256':'SHA-256 of Python shape-string bytes followed by grayscale uint8 decoded bytes; OpenCV-specific identity check.',
        'mask_pixels':'Foreground pixels in native binary union of every COCO polygon; not physical area.',
        'mask_pixels_256':'Foreground pixels after nearest-neighbor stretch to 256 x 256; not proof of instance-level survival.',
        'annotation_ids':'All original COCO annotation IDs; individual polygons/instances remain in the unchanged archive.',
        'split':'Frozen train/val/test assignment. Derived augmentations remain in source split.',
        'group':'Minimum filename in conservative connected duplicate-candidate group; not patient ID.'}
    dictionary = '# MedVision data dictionary\n\nVerified 6 October 2026. Provider fields retain their supplied meaning; technical documentation is not clinical or guide approval. No patient IDs, demographics, physical pixel spacing or clinical severity labels are available in the joined manifest.\n\n| Field | Stored type | Meaning / limitation |\n|---|---|---|\n'
    for key in m['rows'][0]:
        sample = m['rows'][0][key]
        dictionary += f'| `{key}` | {type(sample).__name__} | {field_notes[key]} |\n'
    dictionary += '\nCSV numeric labels are stored as strings and converted explicitly at use. COCO segmentation lists contain alternating native x/y pixel coordinates. Training uses a binary union, not instance segmentation. `exclusions` is an explicit image-ID/reason ledger; `archive_sha256`, protocol, seed and grouping rules are manifest-level provenance. Missing patient identity cannot be reconstructed reliably from filename numbering.\n'
    (out / 'DATA_DICTIONARY.md').write_text(dictionary, encoding='utf-8')
    table = list(csv.DictReader((out / 'subgroups.csv').open()))
    report = '''# MedVision Phase 3 dataset audit

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
'''
    for field in ['fractured','hand','leg','hip','shoulder','mixed','hardware','multiscan','frontal','lateral','oblique']:
        entries = [next(r for r in table if r['field']==field and r['split']==split) for split in ['train','val','test']]
        report += '| '+field+' | '+' | '.join(f"{r['flagged_images']} ({float(r['percentage_of_split']):.2f}%)" for r in entries)+' |\n'
    report += '''
Hardware prevalence varies from 1.80% validation to 3.85% test; hip prevalence from 6.70% validation to 9.55% test. Rare positive validation subgroups are small (hip 7, oblique 6, hardware 10); any later subgroup scores must include denominators and uncertainty. Multi-fracture image counts are 103/26/42 (train/val/test). Native positive median foreground fractions are 0.344%/0.373%/0.405%; smallest positive 256 unions contain 40/48/45 pixels. The full width/height/aspect/occupancy quantiles are in `distributions.json`. Most images are already low-resolution: median native width 373 and height 454 in every split; enlargement cannot recover missing source detail.

## Reproducibility and execution status

`tools/phase3_review.py` regenerates metadata, native overlay/candidate sheets, duplicate-label checks and the new quarantine revision. It refuses to overwrite an existing data_v2 manifest. `tools/train_baseline_manifest.py` is an isolated copy of the verified trainer with explicit audited-subset manifest support; the running original trainer and medvision_ai.py hashes remain unchanged. A four-train/four-validation v2 smoke passed; this proves execution only, not performance. No competing full CPU run was launched.

Phase 3 computational audit is executed, with immutable manifests, explicit exclusions and no known cross-split duplicate leakage. Expert annotation/data-dictionary approval and patient independence remain unverified. Active E2 results use v1 with the disclosed contradictions; a future v2 run is a different protocol and must be named separately. The test remains reserved. See `DATA_DICTIONARY.md`, `duplicate_label_audit.json`, `experiments/data_v2/revision.json`, PROJECT_STATUS and the experiment registry.
'''
    report += f"\nv1 manifest SHA-256: `{revision['parent_manifest_sha256']}`.\nv2 manifest SHA-256: `{revision['manifest_sha256']}`.\n"
    # Verify computed v2 counts rather than trusting prose.
    v2 = json.loads((ROOT / 'experiments/data_v2/manifest.json').read_text())
    assert len(v2['rows']) == 4017 and sum(len(r['annotation_ids']) for r in v2['rows']) == 919
    v2_table = []
    for split in ['train','val','test']:
        rr = [r for r in v2['rows'] if r['split']==split]
        for field in ['fractured','hand','leg','hip','shoulder','mixed','hardware','multiscan','frontal','lateral','oblique']:
            count = sum(int(r[field]) for r in rr)
            v2_table.append(dict(split=split, field=field, flagged_images=count,
                                 percentage_of_split=100*count/len(rr),
                                 fractured_flagged_images=sum(int(r[field]) for r in rr if int(r['fractured']))))
    with (out / 'subgroups_v2.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f,fieldnames=list(v2_table[0]))
        writer.writeheader()
        writer.writerows(v2_table)
    report += '\nExact subgroup counts for the quarantine revision are separately saved in `subgroups_v2.csv`; original active-run counts are in `subgroups.csv`.\n'
    (out / 'DATASET_AUDIT.md').write_text(report, encoding='utf-8')
    state = json.loads((ROOT / 'experiments/E2_corrected_baseline/state.json').read_text())
    update = f'''## CURRENT SESSION - 6 October 2026: Phase 3 executed

Phase 2 clean CPU setup and real inference remain verified; GPU is still blocked by Code 43. Project due 10 October; user handles 8 October poster; institutional report deferred.

- Completed Phase 3 source/version/license, subgroup distributions, sampled native annotation review (17 train/validation images), all 217 non-exact candidate-pair reviews and duplicate-label checks. Full evidence: `experiments/phase3_review/DATASET_AUDIT.md` and `DATA_DICTIONARY.md`. Patient independence and expert/guide approval remain unverified.
- Original ZIP matches **FracAtlas v6** by published size and MD5; authoritative version metadata specifies CC BY 4.0. Latest v7 is different and was not downloaded/substituted.
- **New finding:** three exact-decoded sets have fractured/normal label contradictions affecting seven training images. Seventeen exact-copy sets have different union masks; fourteen same-positive annotation disagreements remain documented. No known duplicate/group crosses splits.
- Frozen separate **data_v2** quarantines all seven contradictory images: 4,017 eligible (714 positive / 3,303 normal), train 2,808 (493/2,315), validation 612 and test 597 unchanged. v2 SHA `{revision['manifest_sha256']}`. Existing v1 and E2 are preserved; E2 cannot be represented as training on v2.
- New `tools/train_baseline_manifest.py` consumes audited subset manifests without modifying active trainer/loader source. Four-case train/validation v2 smoke passed; not performance evidence. No duplicate full training job launched.
- E2 snapshot: `{json.dumps(state)}`. Still uses v1 with the disclosed seven contradictory targets. Read live state/logs before continuing; historical model remains the demo model. No test evaluation or tuning performed.

Next: inspect E2 validation when available, keep its protocol/label-noise caveat; use v2 for a separately named new training experiment via the isolated trainer. Never change data/config on E2 resume. Preserve validation/test IDs; select/freeze on validation before final test. Final demo/browser check, measured paper and project packaging remain outstanding.

'''
    paths = ['PROJECT_STATUS.md','EXPERIMENT_REGISTRY.md','medvision_handoff/MEDVISION_HANDOFF.md',
             'medvision_handoff/MedVision_Master_Todo_and_Research_Paper_Roadmap.md','README.md','paper/MANUSCRIPT_DRAFT.md']
    backup = session / 'documents_before'
    backup.mkdir(exist_ok=True)
    for name in paths:
        target = ROOT / name
        snapshot = backup / Path(name).name
        if not snapshot.exists():
            snapshot.write_bytes(target.read_bytes())
    def original_document(name):
        return (backup / Path(name).name).read_text(encoding='utf-8')
    status = ROOT / 'PROJECT_STATUS.md'
    status.write_text(original_document('PROJECT_STATUS.md').replace('# MedVision Project Status\n', '# MedVision Project Status\n\n'+update, 1), encoding='utf-8')
    handoff = ROOT / 'medvision_handoff/MEDVISION_HANDOFF.md'
    text = original_document('MEDVISION_HANDOFF.md')
    head, tail = text.split('\n',1)
    handoff.write_text(head+'\n\n'+update+tail, encoding='utf-8')
    registry = ROOT / 'EXPERIMENT_REGISTRY.md'
    text = original_document('EXPERIMENT_REGISTRY.md').replace('Last updated: 5 October 2026.', 'Last updated: 6 October 2026.')
    text = text.replace('Completed with documented exclusions; visual group review pending', 'Completed; visual review and label contradictions documented on 6 October')
    text = text.replace('| E0-learning-cpu |', '| D2-phase3-review | Completed technical audit | FracAtlas v6 CC BY 4.0; 17 annotation examples; all 217 non-exact pairs | Zero known cross-split candidates; 7 contradictory case-label images quarantined; 14 other exact-mask disagreement groups disclosed | `experiments/phase3_review/DATASET_AUDIT.md` |\n| D2-quarantine-split | Frozen v2 | Same assignments, remove 7 contradictory training images | 4,017 eligible; train 2,808, val 612, test 597; v1 preserved | `experiments/data_v2/` |\n| E2-v2-manifest-smoke | Passed execution only | Four train/four val, isolated explicit-manifest trainer | Finite training/checkpoint/native validation; no test; not a full experiment | `experiments/E2_v2_manifest_smoke/` |\n| E0-learning-cpu |', 1)
    text += '\n6 October session: E2 continues on immutable v1; seven contradictory training targets discovered later. Do not relabel its results as v2. New-run command: `.\\.venv-clean\\Scripts\\python.exe tools/train_baseline_manifest.py --out experiments/E3_v2_bce_dice --epochs 12 --loss bce_dice`; launch only after verifying the existing full CPU job status and compute budget. v2 manifest SHA: `'+revision['manifest_sha256']+'`.\n'
    registry.write_text(text, encoding='utf-8')
    roadmap = ROOT / paths[3]
    text = original_document(paths[3])
    for item in ['3.1','3.4','3.7','3.10']:
        text = text.replace(f'- [ ] **{item}**', f'- [x] **{item}**')
    text = text.replace('- [ ] **3.12** Generate', '- [ ] **3.12** Technical audit report and data dictionary generated 6 October (`experiments/phase3_review/`); external approval outstanding. Generate')
    roadmap.write_text(text, encoding='utf-8')
    readme = ROOT / 'README.md'
    text = original_document('README.md').replace('- **License and redistribution terms: TO VERIFY with the dataset provider before sharing the archive or derived images.**', '- Dataset **CC BY 4.0**, verified from [FracAtlas v6 provider metadata](https://api.figshare.com/v2/articles/22363012/versions/6). Attribute the dataset/paper, link the license and identify changes. The preserved archive matches v6; see [data audit](experiments/phase3_review/DATASET_AUDIT.md).')
    text = text.replace('- Confirmed dataset licensing and an approved model distribution location.', '- An approved model distribution location and verified historical checkpoint permissions.')
    readme.write_text(text, encoding='utf-8')
    paper = ROOT / 'paper/MANUSCRIPT_DRAFT.md'
    text = original_document('MANUSCRIPT_DRAFT.md')
    insert = '6 October audit addendum: the archive matches FracAtlas v6 (CC BY 4.0). Exact-decoded duplicate labels contradict in three sets comprising seven training images; the active E2 run uses the preserved v1 protocol with those targets. A separate v2 revision quarantines all seven (train 2,808; validation/test IDs unchanged). Fourteen additional same-positive exact-copy sets have different union annotations, retained as provider uncertainty. All 217 non-exact candidate pairs and 17 train/validation annotation examples were visually reviewed; patient independence remains unknown. See `experiments/phase3_review/DATASET_AUDIT.md`. Tables below remain v1 historical diagnostics; no v2 full-training or final-test performance result exists.\n\n'
    paper.write_text(text.replace('## Abstract\n', insert+'## Abstract\n',1), encoding='utf-8')
    originals = {name:sha(ROOT / name) for name in ['FracAtlas.zip','best_model.pt','best_model_threshold.json']}
    assert originals['best_model.pt'] == config['original_checkpoint_sha256']
    assert originals['FracAtlas.zip'] == config['archive_sha256']
    assert originals['best_model_threshold.json'] == '02d33de4874bcb22816225b8c0834123388f90505a16a3953b7e452a103e3830'
    ledger = {'recorded_utc':datetime.now(timezone.utc).isoformat(), 'original_sha256':originals,
              'active_source_hashes_preserved':True, 'active_training_state_snapshot':state,
              'v1_manifest_sha256':revision['parent_manifest_sha256'], 'v2_manifest_sha256':revision['manifest_sha256'],
              'completed':'Phase 3 technical audit and quarantine revision; isolated v2 trainer smoke',
              'test_evaluated':False, 'report':'experiments/phase3_review/DATASET_AUDIT.md',
              'artifacts_sha256':{str(p.relative_to(ROOT)):sha(p) for p in out.iterdir() if p.is_file()},
              'remaining':'Expert approval, patient independence unavailable; E2 validation, separate v2 training, final test, browser demo, final manuscript.'}
    (session / 'session_ledger.json').write_text(json.dumps(ledger, indent=2))
    print(json.dumps({'originals_preserved':True,'v2_smoke_passed':True,'phase3_report_written':True,'E2_state':state}, indent=2))


if __name__ == '__main__':
    main()
