# MedVision AI — Phase 1 Scope and Research Protocol

Version 1.0 | Prepared 5 October 2026 | Execution baseline for subsequent work

## Decision and status

The planning deliverables for Phase 1 are prepared below. PyTorch is confirmed from the project discussion. The user confirmed access to a local NVIDIA GPU and requested proposed team responsibilities. Exact GPU specifications and deadline dates have not yet been supplied. Proposed assignments are not evidence of teammates accepting work.

The scope and protocol below are working decisions for development. Guide review, named-role acceptance, institutional deadline confirmation and hardware-budget verification remain open. Phase 1 must not be described as fully guide-approved until these occur. This phase does not claim new model performance or completion of later implementation work.

## 1. Project scope — tasks 1.1–1.4

**Working title:** MedVision AI: Reproducible Fracture-Region Segmentation and Geometric Analysis of Musculoskeletal Radiographs.

**Problem:** Build and evaluate a system that highlights annotated fracture regions in musculoskeletal X-rays while measuring missed findings and false positives. The intended academic outcome is a research prototype with an integrated demonstration and an original experimental paper.

**Primary task:** Binary semantic segmentation of all annotated fracture regions in an image.

**Secondary tasks:** Case-level suspected-fracture detection, region-level localization and descriptive geometric feature extraction. Each is evaluated separately; a case-detection accuracy is not a segmentation score.

**Inputs:** Decodable JPG/PNG X-rays within the server's documented size/dimension limits. Planned evaluation anatomy follows the supplied FracAtlas labels: hand, leg, hip and shoulder, including mixed images where appropriate. This is a dataset scope, not a claim of validated performance on every bone, age group, projection or imaging device.

**Outputs:** Original image, probability/mask output mapped to original coordinates, segmentation overlay, multiple-region summaries where present, model/configuration identifier and processing status. Region pixel area, perimeter, compactness and aspect ratio are descriptive measurements with stated units.

**Severity decision:** Any retained tier is labeled an experimental geometry-based indicator. Empty predictions return not applicable. Clinical severity classification, physical crack width and treatment recommendations are outside the current research claims because no suitable severity reference labels have been established.

### Five implementable objectives

| Objective | Completion evidence |
|---|---|
| O1. Build a reproducible labeled-image/mask pipeline including normal cases | Dataset audit, manifests, frozen split IDs and image/mask checks |
| O2. Train and compare fracture-region segmentation pipelines | Versioned baselines, configs, checkpoints, seeds and training logs |
| O3. Measure overlap, detection errors and localization performance | Per-case results, uncertainty estimates and failure analysis |
| O4. Produce aligned visualizations and transparent geometric summaries | Verified inverse transforms; empty/thin/multiple-mask tests |
| O5. Deliver a working local application and evidence-backed research paper | Real upload/inference demonstration, reproducibility package and manuscript |

### Feature decisions

| Feature | Working scope |
|---|---|
| Real upload, validation, processing status and failure handling | Required |
| Actual model inference; aligned original/overlay viewer | Required |
| No-region state; multiple-component handling; geometry with units | Required |
| Model/config/threshold provenance and downloadable result summary | Required; machine-readable export is sufficient initially |
| Local history and retrieval of saved results | Required minimal persistence for the demo |
| Clinical approval workflow, invitations, password-reset emails, admin/audit dashboards | Deferred; disable unfinished controls |
| Patient-identifiable uploads, hospital deployment, DICOM/PACS | Outside current scope |
| Network/shared deployment | Conditional; server-side access control is a prerequisite |
| PDF clinical report | Optional presentation feature; must not imply clinical validation |
| MedSAM, detector refinement, classifier head, ensembles, U-Net++ | Conditional experiments, not completion requirements |

Local demonstration uses appropriate research images. The final paper reports only evaluated capabilities. These choices narrow existing aspirational interface features into a deliverable core.

## 2. Academic requirements register — task 1.5

Evidence: supplied CSEP23605 Review 2 Template.pptx, actual slide XML numbers below. These are template requirements, pending confirmation for the current review.

| Requirement observed | Location | Action |
|---|---|---|
| At least 4–5 achievable objectives | Slide 6 | Five objectives specified above |
| At least 10 recent papers from past three years, including four Scopus/SCI journal papers | Slide 4 | Build verified literature matrix; confirm date window and indexing criteria with guide |
| Minimum 20 referenced papers | Slide 19 | Expand verified bibliography; do not count references without reading relevant material |
| At least two objectives completed for this review | Slide 16 | Map future evidence to O1–O5; do not assert completion now |
| Report/paper plagiarism material and acceptance if any or submission proof | Slide 2 | Confirm exact final requirements and obtain checks on final versions |
| July–October 2026 timeline in template | Slide 23 | Historical template schedule; replace with actual team deadlines |

User indicated that actual dates exist but did not provide them. Record separately: next review date, final project/report date and paper-submission date. Publication acceptance is externally determined and is not a promised project outcome.

Guide contact or submission has not been performed. The team can take this document to the guide; no approval is implied.

## 3. Research questions and hypotheses — task 1.6

| ID | Research question | Controlled comparison | Main evidence |
|---|---|---|---|
| RQ1 | Does preserving image geometry/detail improve fracture-region segmentation? | Aspect-preserving 256 vs 512; original implementation retained as historical reference | Positive-case Dice, small-region recall, memory and latency |
| RQ2 | Which preprocessing is beneficial? | Normalization only vs CLAHE vs CLAHE+blur | Same model/split/resolution and error metrics |
| RQ3 | How do losses and negative sampling alter the error trade-off? | Focal Tversky vs BCE+Dice vs Unified Focal; sampler tested separately | Dice, case sensitivity and normal-case false positives |
| RQ4 | Does attention/pretraining justify added complexity? | Plain U-Net vs Attention U-Net; pretrained residual encoder if feasible | Matched protocol and reported pretraining/compute differences |
| RQ5 | Do remaining small-region errors justify refinement? | Predicted-region refinement or tiling vs selected single-stage baseline | End-to-end region recall and extra latency; conditional |

Hypotheses are testable, not assumed true. Null and negative results remain reportable. Image enlargement cannot recreate missing source detail, and an architectural upgrade is not a prerequisite for a valid paper.

**Paper positioning:** Applied experimental/reproducibility study of fracture segmentation and pipeline choices. Claim methodological novelty only if later work establishes a distinct contribution against verified related work. The earlier survey paper supplies background, not experimental evidence for this manuscript.

## 4. Evaluation protocol — task 1.7

### Data separation

Use a proposed 70/15/15 train/validation/test allocation over eligible labeled images, preserving groups and balancing key labels as feasible. Actual counts and final manifest are Phase 3 outputs. Split groups rather than individual derived crops. Prefer reliable patient/study groups; otherwise group identified duplicates/related views and disclose that patient independence is unverified.

Audit the supplied official fracture split before finalizing this custom protocol. Any protocol change must be recorded before experiments; do not mix official and custom results in one comparison. If historical checkpoint training overlap cannot be excluded, its result is a diagnostic reference rather than an independent held-out claim. Models for the new comparison are trained under the frozen new protocol.

No test inspection for model/threshold selection. Tune only on validation. Preserve exact IDs, hashes and exclusions. Normal images receive zero masks only when the dataset explicitly labels them normal.

### Metrics and conventions

**Primary metric:** Mean per-image Dice on ground-truth-positive test images, using final delivered masks mapped to original image coordinates and valid image pixels. Include completely missed positive images as Dice=0. Report mean, median and uncertainty, along with sample count.

**Secondary metrics:** Per-positive-image IoU, pixel precision/recall, global pixel overlap; case sensitivity, specificity and precision; normal-case false-positive rate; region recall and false-positive regions per image; latency and peak memory.

For normal images, do not average empty/empty Dice=1 into the primary score. Report normal cases separately. Mark undefined precision as not defined with denominators stated rather than silently interpreting it as perfect. Describe every aggregation in the results table.

**Case decision:** Initially, a case is positive if at least one component remains after the frozen probability threshold and optional component filter. Do not use contour area to test mask presence. This is a model-output rule, not a clinical diagnosis. Remove hardcoded confidence; PR-AUC/AUROC are optional until a continuous case score is explicitly defined.

**Region matching:** Preserve ground-truth instance masks for a supplementary one-to-one maximum-IoU matching analysis. Predefine IoU≥0.10 as a permissive localization check and report IoU≥0.50 alongside it. These are proposed research conventions, not clinical acceptance standards. One prediction cannot count as multiple true-positive instances. Discuss merged/overlapping instances and region-vs-crack annotation limitations.

### Selection and acceptable research trade-offs

1. Select checkpoints by validation positive-case Dice at a fixed 0.5 threshold within each run; retain a documented deterministic tie rule (earlier epoch).
2. On the saved checkpoint, select probability threshold from a fixed 0.05–0.95 grid with step 0.05, evaluating the actual serving postprocessing. Tune component filtering on validation only and record its candidates before running.
3. Rank configurations by validation mean positive-case Dice. For a proposed winner, require case sensitivity no more than 2 percentage points below the corrected baseline and normal-case false-positive rate no more than 2 points above it. These are provisional engineering comparison margins, not evidence of acceptable clinical performance.
4. If a higher-Dice model violates those margins, report the trade-off and retain the qualifying baseline unless the research objective is explicitly revised before further testing. Report absolute error rates even when all models satisfy relative margins.
5. If finalists differ by less than 0.005 Dice, prefer lower measured latency, then lower parameter count. This is a declared practical tie rule, not statistical equivalence.
6. Repeat baseline and finalist with three seeds where resources permit; report mean and variation. Use paired bootstrap intervals over independent cases/groups, with grouping limitations disclosed. No superiority claim from a tiny unsupported difference.
7. Freeze the complete bundle before one final evaluation. Any subsequent tuning changes the status of that test set and must be disclosed.

No guaranteed target accuracy or Dice is set. A working prototype and a defensible paper can report modest results honestly. Stronger clinical error thresholds would require expert requirements and appropriate validation beyond this scope.

## 5. Team responsibilities — task 1.8

Names are drawn from the supplied project roster. This allocation is a proposal requested by the user, not an inference about each person's expertise or an accepted assignment.

| Proposed owner | Workstream | Main deliverables | Proposed reviewer |
|---|---|---|---|
| K Sairam | ML/backend | Runtime, training, losses, predictor and model bundles | Harsha K N |
| Harsha K N | Data and evaluation | Manifest, splits, annotation audit, metrics and failure analysis | Adarsh |
| Sunay Awasthi | Application/integration | Real API/UI, uploads, persistence, exports and demo tests | K Sairam |
| Rajput Adarsh Singh Thakur | Coordination and paper integration | Issue tracking, experiment comparisons, literature matrix, report/paper consistency | Sunay Awasthi; guide for academic review |
| All four | Research review and viva | Experiment interpretation, manuscript review and authorship approval | Cross-review |

Every author reviews methods and results. Proposed coordination responsibility does not establish author order. Confirm author order and contributions separately when actual work is known.

### Compute budget proposal

User-confirmed environment: local NVIDIA GPU. Exact model, VRAM, host RAM, operating system and weekly availability remain unknown.

- Begin with an environment/batch benchmark and tiny-subset learning check; do not promise training durations before measurements.
- Initial planning ceiling: 24 GPU-hours for the first experiment cycle, subject to measured feasibility and team confirmation; this is not authorization for paid compute.
- Allocate up to 2 hours to diagnostics, 10 to controlled screening, 10 to repeated baseline/finalist runs and 2 to final evaluation/latency. If measurements show these allocations are infeasible, narrow the experiment set and revise the budget explicitly.
- Start with 256/512 experiments at a batch size that fits. Do not commit to 1024, ensembling or refinement before memory/latency evidence.
- Keep each run resumable and distinct; preserve original weights and record wall time, peak memory and early-stopping behavior. No fixed epoch count is treated as guaranteed convergence.

### Experiment tracker — ready to use

| Run ID | Hypothesis/change | Owner | Split hash | Config/commit | Seed | GPU/time | Validation results | Decision | Evidence path |
|---|---|---|---|---|---|---|---|---|---|
| E0 | Runtime and learning sanity checks | Proposed ML owner | Pending | Pending | 42 | Pending | Not run | Pending | Pending |
| E1 | Corrected Attention U-Net baseline | Proposed ML owner | Pending | Pending | 42 | Pending | Not run | Pending | Pending |
| E2 | Aspect-preserving resolution comparison | Proposed ML owner | E1 split | Pending | 42 | Pending | Not run | Pending | Pending |
| E3 | Preprocessing ablation | Proposed ML owner | E1 split | Pending | 42 | Pending | Not run | Pending | Pending |

Extend the same tracker for losses, architecture and repeats. Store per-run config, metrics, predictions and model hash; the table is an index, not a substitute for evidence.

### Initial issue register

| ID | Issue / next action | Priority | Dependency | Status |
|---|---|---|---|---|
| P1-01 | Supply actual review/report/paper dates | High | User/team | Awaiting dates |
| P1-02 | Confirm guide's current requirements and scope | High | Guide review | Prepared for review |
| P1-03 | Confirm or revise proposed team allocation | High | Team | Proposed |
| P1-04 | Supply GPU model/VRAM and available hours | High | User/team | Awaiting details |
| P2-01 | Verify accessible dataset/checkpoint and preserve originals | High | Artifact access | Not started this phase |
| P2-02 | Establish environment and strict checkpoint load | High | P1-04; weights | Not started |
| P3-01 | Build full manifest including normal cases | High | Dataset access | Not started |
| P4-01 | Correct mask/empty-result/confidence semantics | High | Reproducible baseline | Not started |

## 6. Phase 1 completion register

| Roadmap task | Deliverable prepared | Current status |
|---|---|---|
| 1.1 Main task and scope | Section 1 | Defined as working scope |
| 1.2 Primary/secondary outcomes | Sections 1 and 4 | Defined |
| 1.3 Severity boundary | Section 1 | Defined |
| 1.4 Required application features | Feature table | Defined; guide acceptance pending |
| 1.5 Institutional requirements and dates | Section 2 | Template checked; current confirmation/dates pending |
| 1.6 Research questions | Section 3 | Defined |
| 1.7 Metrics and selection rules | Section 4 | Defined as protocol v1.0; pre-run review pending |
| 1.8 Owners, budget and tracker | Section 5 | Proposed owners/budget; tracker initialized |

Phase 1 technical planning is ready. Final closure requires current dates, GPU specifications, team acceptance of roles and guide review. No source-code change, training run, message to the guide or manuscript submission was performed in this phase.

## 7. Review handoff

Use this checklist in the team/guide review:

- [ ] Accept or revise O1–O5 and required application features.
- [ ] Confirm that experimental geometric summaries satisfy the intended severity-related objective.
- [ ] Confirm current literature/report/paper requirements and actual dates.
- [ ] Accept or revise research questions and the provisional evaluation trade-offs before experiments.
- [ ] Confirm role assignments and hardware/time budget.
- [ ] Record changes as protocol v1.1 before Phase 3 split freeze and Phase 5 experiments.

Preparation for Phase 2 can proceed with reversible environment checks while these external confirmations are collected. Final experimental and academic claims must follow the agreed protocol and evidence.
