# MedVision AI: Project Analysis and Completion Plan

Assessment date: 4 October 2026 | Project G41 / P47 | Framework decision: PyTorch

## 1. Overall assessment

MedVision has a substantial implementation foundation: Attention U-Net, preprocessing, training and evaluation functions, a saved model, an accessible dataset, a FastAPI service, a React interface, and academic documentation. It is ready for continued engineering and evaluation. It is not yet demonstrated to be a complete, reproducible final-year project with verified results and a reliable integrated demo.

The highest-priority work is to correct dataset coverage, establish model/checkpoint provenance, reproduce evaluation, remove misleading output fields, and test the real application with mocks disabled. A fresh architecture rewrite is unnecessary at this stage.

No percentage completion is assigned: code availability, scientific validation, and demo readiness are different milestones, and the supplied evidence does not support one defensible overall percentage.

## 2. Evidence and verification boundary

The reviewed local repository matches the GitHub HEAD returned for Sairam-74/MedVision: commit `1e310c280450f3efc8fbb123ed9815332119170b` (Initial commit: MedVision). The working tree was clean. This assessment did not change project source code.

Evidence reviewed:

- `medvision_ai.py`, `backend_service.py`, frontend API/configuration/results/tests, dependency manifests, Docker/Nginx configuration, CI workflow, README and PROJECT_STATUS.
- `best_model_threshold.json` and both uploaded checkpoint files.
- FracAtlas ZIP contents, COCO annotations, dataset CSV, and supplied split CSVs.
- Phase-I final report, Phase-II Review 1, Review 2, Review 0, the Review 2 template, VTU portal export, survey document and similarity/AI reports. The LaTeX source archive was inventoried, not compiled.

Checks performed: Python syntax compilation of both backend Python files passed; complete ZIP CRC checks of the dataset and uploaded checkpoint passed; checkpoint serialization metadata was inspected without executing pickle; both checkpoint SHA-256 values were compared.

Runtime limitation: the current workspace's default Python lacks PyTorch, OpenCV and FastAPI; frontend node_modules are absent. Training, model loading/forward inference, API execution, frontend build, browser testing and metric reproduction were not performed. This does not establish whether those prerequisites are installed on the team's computers or Colab. Existing automated tests and CI definitions were inspected, not certified as passing.

## 3. Objectives, outcomes and present progress

| Objective | Intended outcome | Current evidence | Remaining acceptance condition |
|---|---|---|---|
| Pixel-level fracture localization | Binary mask aligned to an input X-ray | Four-level PyTorch Attention U-Net with attention-gated skip connections | Load the supplied checkpoint strictly; demonstrate correct output shape and held-out segmentation quality |
| Consistent preprocessing | Reproducible grayscale, contrast-enhanced normalized inputs | CLAHE, Gaussian blur, 256×256 resize and [0,1] normalization implemented | Verify training/inference equivalence and image-mask alignment; quantify resize effects |
| Reproducible training | Traceable model trained on a documented split | Adam, scheduler, early stopping, augmentation, checkpoint saving and seeded splitting implemented | Save exact sample lists, environment, config, epoch logs and checkpoint hash together |
| Quantitative evaluation | Dice, IoU, precision and recall on untouched test data | Evaluation and validation threshold sweep implemented | Reproduce and export metrics; include normal-image errors and per-image results |
| Geometric feature analysis | Area, perimeter, compactness and aspect ratio from masks | Largest-component feature extraction implemented | Define units and area consistently; test empty, thin and multiple-component masks |
| Severity-oriented indicator | Transparent exploratory summary of mask geometry | Mild/Moderate/Severe derived from area cutoffs | Label as heuristic; avoid claiming clinically validated severity; fix empty-mask behavior |
| End-to-end application | Upload → processing → original/overlay → result | React workflow and FastAPI upload/inference functions present | Verify with mocks disabled and real weights, including failures and repeat uploads |
| Academic delivery | Consistent report, slides, experiments and reproducible demonstration | Multiple reports/slides, survey and source archive exist | Reconcile contradictions, update evidence, finish final artifacts and rehearse viva |

Expected final outcome: a reproducible research prototype for fracture segmentation and geometric analysis of JPG/PNG X-rays. Demonstrated diagnostic accuracy, clinical severity grading and unrestricted “any X-ray” performance are not established outcomes.

## 4. Prerequisite checklist

| Prerequisite | Status | Evidence / action |
|---|---|---|
| Project problem and team identified | Satisfied | Portal and project documents identify MedVision and the four-person team |
| Source repository available | Satisfied | Current GitHub commit confirmed and local source readable |
| Framework selected | Satisfied, documents inconsistent | User confirms PyTorch; code and Phase-I report use it; slides still specify TensorFlow/Keras |
| Dataset bytes accessible | Satisfied | ZIP is 338,412,750 bytes and passes archive CRC validation |
| Ground-truth segmentation annotations | Satisfied for annotated subset | 717 COCO image records and 922 annotations |
| Normal X-rays included in loader | Not satisfied | CSV lists 3,366 normal images, but loader selects only COCO image records |
| Model weights accessible | Satisfied as an artifact | 125,659,839-byte checkpoint; valid ZIP structure and recognizable tensor keys |
| Runtime checkpoint compatibility | Unverified | Needs strict state-dict load and a real forward pass |
| Checkpoint at backend's expected path | Not satisfied in this workspace | Backend expects repository-root best_model.pt; uploaded file is outside that location |
| Threshold metadata available | Partial | JSON contains threshold 0.90 and validation Dice 0.458659; hash binding to uploaded model absent |
| Reproducible environment | Partial | Manifests exist; Python requirements are ranges and contain a 3.13.7 comment while CI selects 3.11 |
| Runnable dependencies here | Not satisfied | Missing PyTorch/OpenCV/FastAPI and frontend installed packages |
| Training GPU, memory and disk | Unverified for team environment | Slides name hardware/Colab; no current resource or successful-run evidence was checked |
| Immutable split and leakage checks | Not satisfied | Seeded split code exists, but persisted manifests and duplicate/group leakage audit are absent from reviewed evidence |
| Reproduced final test results | Not satisfied | Validation numbers recorded; no verified final test output connected to supplied checkpoint |
| Severity reference labels | Not established | Reviewed CSV describes fracture presence/count/anatomy, not severity ground truth |
| Dataset citation and use terms | Pending verification | Repository explicitly leaves citation/license marked TO VERIFY |
| Real frontend/backend configuration | Not satisfied by defaults | Mocks default true; frontend example URL uses port 8080 while README backend uses 8000 |
| Final institutional checklist | Partial | Template and survey reports available; current final submission deadlines/requirements need guide confirmation |

Decision: prerequisites are sufficient to start completing the project, but insufficient to claim that final evaluation, integrated demonstration and submission readiness are complete.

## 5. Dataset and experimental design findings

The archive contains 4,083 X-ray images. Its dataset CSV labels 717 as fractured and 3,366 as non-fractured. All 717 COCO image records have annotations. The current loader uses the COCO images list as its sample universe, so the normal images never enter its train/validation/test split. The class description says images without annotations receive zero masks, but that path cannot include the omitted normal images.

The repository documents a 501/107/109 custom split of the 717-image subset. The archive separately supplies fracture split CSVs with 574 train, 82 validation and 61 test entries. These are different protocols. Select and name one protocol, save exact IDs, and avoid directly comparing results from different splits as though they were identical experiments.

The current model can be assessed as a positive-case segmentation model, but a fracture/no-fracture application also needs normal-image evaluation. Build normal examples from explicit dataset labels, not an assumption that every missing annotation implies normal. Preserve a truly untouched test set. If an earlier test set has already guided model changes, record that limitation and establish a new independent evaluation plan.

The CSV has no explicit patient identifier among its inspected columns. Do not claim patient-independent splitting without further provenance. Audit exact/near duplicates and related views as far as metadata permits, and state any remaining grouping limitation.

The dataset cache is instantiated four times during split construction, each storing decoded images and masks at original resolution. This creates avoidable memory pressure. A shared cache or lazy loading should precede expansion to all images.

## 6. Model, checkpoint and metric findings

Both uploads, best_model.pt and best_model(1).pt, are byte-identical:

`SHA-256: 922f30bf691b9979aee65d386bcf73d2643558c049a7d11ab013fea315f39b81`

Static inspection finds 174 tensor storage entries and parameter names matching the broad Attention U-Net naming scheme. This supports the presence of a plausible PyTorch state dictionary, not proof of successful loading, training provenance or predictive quality.

| Evidence location | Recorded value | Interpretation |
|---|---|---|
| PROJECT_STATUS last run | 40 epochs; validation Dice 0.4526; IoU 0.2925 | Documented validation results, not reproduced test results |
| Threshold JSON | Threshold 0.90; validation Dice 0.4586593828436439 | Separate recorded calibration result; checkpoint association needs confirmation |
| Status inference section | Older threshold 0.10 | Stale historical reference that conflicts with current metadata |
| Evaluation implementation | Flattened global pixel Dice/IoU/precision/recall | Micro aggregation; does not describe distribution across cases |

The default CLI loss is focal_tversky, and that branch returns focal Tversky alone. The alternate weighted_bce branch returns BCE plus Dice. Slides and parts of the report describe Dice+BCE; part of PROJECT_STATUS describes Dice+focal Tversky. The final methods section must describe the actual chosen run.

Evaluation thresholds raw masks, whereas application inference keeps only the largest connected component. Evaluate the exact mask returned by the application as well as the raw mask, otherwise the reported metric does not directly describe the displayed output.

Add a separate evaluation-only command. The present main entry point begins training before calibration/evaluation, making it unsuitable for a safe, repeatable check of existing weights without possible checkpoint replacement.

## 7. Feature and output correctness findings

1. Confidence is hardcoded to 0.86 or 0.74. It is not calculated from model output. Remove it or explicitly replace it with a justified, separately validated measure. A pixel probability average alone is not proof of calibrated case confidence.
2. Severity uses only area (<150, <900, otherwise severe); perimeter, compactness and aspect ratio are displayed features rather than inputs to the tier rule.
3. The main area computation uses contour area, whereas slides call it pixel count. Thin nonempty masks can have zero contour area. Because fractureStatus tests area > 0, a nonempty prediction can be reported as no fracture.
4. Empty masks return Mild, creating a contradictory no-fracture plus low-severity output. Return a separate no-region/not-applicable state.
5. Largest-component filtering discards additional predicted regions. The CSV includes multi-fracture cases, so this design choice must be evaluated and documented.
6. Area is measured on a resized 256×256 image, not in physical units. Aspect-ratio distortion and original image dimensions matter. Do not describe thresholds as anatomical fracture severity.
7. Results images use square object-cover styling; verify that non-square X-rays are not cropped and that overlay alignment is preserved in the final viewer.

## 8. Application and delivery findings

The backend genuinely contains uploaded-image persistence and inference dispatch. Its module docstring claiming uploads still use the demo image is stale. Correct the docstring rather than treating it as current behavior.

The frontend defaults to mock mode. Its tests use mocked APIs, so even passing them would not prove that the supplied model works through FastAPI. Explicit real-mode testing is required.

Authentication is demo-only: accounts/passwords live in memory, access tokens are static, analysis routes do not enforce authorization, and refresh returns a demo session. Reset endpoints report success without implementing a reset. The frontend requests /users and /audit-logs, but corresponding backend routes were not found. Approval actions on the result page resolve locally without durable server storage.

For an assessed local prototype, implement the required core workflow and clearly disable unfinished controls. Durable history, review storage and PDF export should be completed if retained as project claims. Full hospital identity integration and clinical deployment are separate scope, not prerequisites for finishing an honest student research demo.

Docker currently packages the frontend only. Compose provides a runtime VITE_API_BASE_URL, but the application reads Vite build-time configuration; there is no demonstrated runtime substitution. Nginx has no API proxy. Consolidate ports, API routing and model configuration before claiming one-command deployment.

## 9. Documentation and academic readiness

The Phase-I report already specifies PyTorch but still describes the older loss and threshold. Phase-II slides retain TensorFlow/Keras and claims including <200 ms inference, clean segmentation, convergence within 50 epochs and no overfitting. Those claims need run-specific evidence; the recorded 40-epoch validation summary alone does not support them.

DFDs describe a central database, multiple stores, reports and patch extraction. Current code resizes whole images and stores users/analysis state in memory. Update diagrams to implemented behavior or implement the claimed modules.

The Review 2 template requests at least 20 references, at least 10 recent papers from the past three years including four indexed journal papers, and review/publication-related evidence. The inspected survey bibliography contains 18 entries, with listed years no later than 2020, so it does not satisfy that template's recent-literature requirement as supplied. Verify bibliographic accuracy and current guide requirements before finalizing.

The supplied DrillBit summary records 1% similarity for the May 2026 survey submission; the AI report records 0% detected AI text. These relate to that submitted survey version, not the future final project report, and neither proves technical correctness or authorship. Obtain checks for final submitted versions if required. No publication acceptance or submission proof was established by this review.

## 10. Prioritized completion checklist

Suggested roles: ML/data owner, application owner, documentation/evaluation owner, with cross-review by another teammate. Assign people when the team agrees responsibilities.

### Milestone A — Reproducible baseline (blocking)

- [ ] A1. Agree core scope and guide-approved success criteria: segmentation, heuristic features, integrated local demo and measured evaluation. Clarify whether classification comparisons, U-Net++ or publication are required.
- [ ] A2. Establish a tested Python environment (CI currently uses 3.11), install backend/frontend dependencies and record exact versions and hardware. Done: clean setup, imports, build and existing tests pass.
- [ ] A3. Configure checkpoint and dataset paths explicitly; verify checksum; strict-load weights and run a real-image forward pass. Done: finite 1×1×256×256 output and saved traceable smoke result.
- [ ] A4. Associate threshold JSON with checkpoint hash, run ID and split; reproduce calibration if provenance cannot be recovered. Done: one consistent model/threshold/config bundle.
- [ ] A5. Add evaluation-only execution and explicit synthetic-demo mode; missing real dataset must fail clearly in research runs. Done: evaluation never retrains or overwrites weights.

### Milestone B — Correct data and experiment protocol (blocking)

- [ ] B1. Create an image/mask manifest covering labeled positives and normals; audit decoding, dimensions, masks and annotation mapping. Done: class counts and exclusions exported.
- [ ] B2. Select the split protocol, check duplicates/related views, save immutable sample IDs and hashes. Done: no sample overlap and documented grouping limits.
- [ ] B3. Reduce duplicated caches and confirm memory use on the intended machine. Done: full dataset loading and one training batch fit measured resources.
- [ ] B4. Preserve the current checkpoint as a baseline; evaluate it before retraining. Done: its scope, split and limitations are explicit.

### Milestone C — Model evaluation and improvement (blocking)

- [ ] C1. Produce baseline evaluation on the frozen protocol: global and per-case Dice/IoU/precision/recall, empty-mask policy, normal-image false positives and case-level detection results where claimed.
- [ ] C2. Compare Attention U-Net with plain U-Net under the same preprocessing/split/budget. Add a classifier only if needed to fulfill the earlier promised classifier comparison; do not compare classification accuracy directly to segmentation Dice.
- [ ] C3. Run controlled improvements to loss, augmentation, resolution or learning rate based on observed failures. Done: configurations and epoch curves saved, validation used for selection.
- [ ] C4. Calibrate threshold using validation only; freeze preprocessing, weights, postprocessing and threshold before final testing.
- [ ] C5. Report final test results with per-case outputs, uncertainty intervals where feasible, representative successes/failures and anatomy breakdowns where sample sizes support them.
- [ ] C6. Benchmark warm inference and full request latency on named hardware, including model loading. Remove unsupported timing claims.

### Milestone D — Honest and correct result semantics (blocking)

- [ ] D1. Remove hardcoded confidence from API/UI or implement and validate a clearly defined alternative.
- [ ] D2. Fix empty-mask severity and separate mask presence from contour area. Test empty, single-pixel, thin-line and disconnected-region examples.
- [ ] D3. Decide multi-component policy; align evaluation and delivered masks. Preserve multiple findings where required.
- [ ] D4. Define area/length units, geometric formulas and threshold rationale; label tiers as experimental geometry heuristics. Clinical severity validation requires separate appropriate labels and expert work.

### Milestone E — Real integrated application (blocking for demo)

- [ ] E1. Set mocks false in the real-demo configuration, reconcile ports/API URL/CORS and add readiness checks for model availability.
- [ ] E2. Use maintained multipart parsing and validate successful image decoding, dimensions and size. Test invalid content, oversized uploads and unreadable images.
- [ ] E3. Load/reuse the model once and bound concurrent inference work. Define timeouts, job failures, collision-resistant IDs and cleanup.
- [ ] E4. Verify upload → queued → processing → result using distinct normal/fracture images. Confirm the displayed image and overlay belong to the uploaded case.
- [ ] E5. Preserve image aspect ratio and overlay alignment; display meaningful failure/no-region states.
- [ ] E6. Implement durable history/review/report export if kept in the assessed scope; otherwise remove or visibly disable unfinished controls and revise claims.
- [ ] E7. For any shared/network deployment, implement server-side access control, secure credential/session handling and protected image access. Keep the interim demo local and limited to appropriate research images.
- [ ] E8. Add meaningful backend/inference and real integration tests; retain frontend tests and run CI. Package tested launch commands; repair Docker routing if Docker is part of delivery.

### Milestone F — Final academic package (blocking for submission)

- [ ] F1. Update report, slides, diagrams, README and status to one PyTorch method, one split, one chosen loss, one checkpoint and one final metric table.
- [ ] F2. Verify dataset source, citation/use terms and all references. Meet guide-approved recent-paper and reference-count requirements.
- [ ] F3. Include reproducible experiment tables, learning curves, held-out overlays, failure analysis, limitations, latency and application screenshots.
- [ ] F4. Finish final report, paper if required, presentation and final-version similarity checks. Collect actual submission/acceptance evidence where required; do not promise acceptance.
- [ ] F5. Prepare a reproducibility bundle: source commit, dependency versions, configuration, split IDs, data retrieval instructions, checkpoint hash, threshold, evaluation outputs and launch steps.
- [ ] F6. Rehearse a fresh-machine demo and viva. Each teammate should explain the architecture, split, loss, metrics, false positives, severity limitations and their contribution.

Dependency order: A → B → C; D can proceed after baseline output inspection; E follows a loadable model and stable result contract; F must use frozen C/E evidence. Documentation cleanup can begin immediately, but final numbers and screenshots come last.

## 11. Definition of complete

The project is complete for its agreed academic scope when a fresh environment can load a versioned model, run the intended dataset protocol, reproduce exported test metrics, process a real uploaded X-ray through the application, display truthful aligned outputs, and support every report/presentation result with saved evidence. Required institutional deliverables must be checked against the current guide-approved checklist.

Clinical deployment, expert-validated clinical severity, DICOM/PACS integration, external multi-hospital validation and advanced model variants are future work unless explicitly added to the assessed scope.

Immediate next action: establish the runnable environment and strictly load the supplied checkpoint, then freeze the data/split protocol before further training. The dataset and model do not need to be uploaded again.

## 12. Evidence index

- Repository: https://github.com/Sairam-74/MedVision/tree/1e310c280450f3efc8fbb123ed9815332119170b
- Source functions: FracAtlasZipDataset; _build_dataset_splits; combined_dice_bce_loss; assess_severity; _evaluate_segmentation_model; predict_from_checkpoint; _result_from_prediction; create_analysis.
- Repository records: PROJECT_STATUS.md; best_model_threshold.json; requirements.txt; .env.example; src/utils/env.ts; src/pages/ResultsPage.tsx; src/App.test.tsx; .github/workflows/ci.yml; Dockerfile; docker-compose.yml; nginx.conf.
- Dataset: FracAtlas/dataset.csv; Annotations/COCO JSON/COCO_fracture_masks.json; Utilities/Fracture Split/*.csv.
- Academic sources: Phase_I_report_final.pdf (objectives, requirements, implementation and results); Phase-II_Review_1.pptx (objectives, requirements, implementation/results); CSEP23605 Review 2 Template.pptx (literature and submission checklist); Major Proj Survey Paper.docx (bibliography); supplied DrillBit summaries (version-specific reported checks).
