# MedVision AI — Remaining Tasks and Research Paper Roadmap

Prepared: 4 October 2026

Execution update 5 October 2026: checked tasks have evidence in PROJECT_STATUS.md and EXPERIMENT_REGISTRY.md. Project due 10 October; poster handled by user on 8 October; institutional report deferred. Clean CPU runtime and real inference are verified. E2 normal-inclusive training is running; calibration/final test/browser verification/manuscript review remain open. GPU has Windows Code 43. Original artifacts are preserved; historical checkpoint scores are diagnostic.


**Final deliverable:** A working, evaluated PyTorch fracture-segmentation research prototype and an original, submission-ready research paper supported by reproducible experiments.

This checklist covers outstanding execution and verification work. Existing code and documents are starting assets, not proof that each task is complete. All boxes begin unchecked. The earlier survey paper is related-work material; the final project paper must report MedVision's own methods, experiments and findings.

## How to use this checklist

- Assign a named owner and reviewer to each phase. Suggested roles below are not assignments to specific teammates.
- Track each task as Not started / In progress / Blocked / Done; attach evidence before marking Done.
- Record actual dates and compute availability before estimating a submission schedule. No deadline or GPU availability is assumed.
- Complete required tasks in order. Conditional experiments need a documented decision and rationale, not automatic implementation.
- Keep the final test set untouched during development. Record unsuccessful experiments as well as successful ones.

### Phase overview

| Phase | Outcome | Depends on | Suggested owner |
|---|---|---|---|
| 1 | Agreed scope and research questions | None | Whole team + guide |
| 2 | Runnable and traceable baseline | 1 | ML/backend owner |
| 3 | Audited dataset and frozen splits | 1; accessible dataset | Data/evaluation owner |
| 4 | Correct training and inference code | 2–3 | ML/backend owner |
| 5 | Measured baseline and controlled improvements | 4 | ML + evaluation owners |
| 6 | Locked final model and rigorous evaluation | 5 | Evaluation owner + reviewer |
| 7 | Working real application and reproducibility package | Stable output contract; final checks after 6 | Application owner |
| 8 | Consistent academic documents and paper evidence | Can start now; final values after 6–7 | Documentation owner |
| 9 | Original research paper, reviewed and submission-ready | 6–8 | All authors |

## Phase 1 — Freeze project scope and research plan

- [ ] **1.1** Confirm the main task: binary segmentation of annotated fracture regions in JPG/PNG musculoskeletal X-rays; document supported anatomy and input limitations.
- [ ] **1.2** Separate three outcomes: case-level fracture detection, region localization and pixel segmentation. State which are primary and secondary.
- [ ] **1.3** Confirm that geometric severity output remains an experimental indicator unless appropriate severity labels and expert validation become available.
- [ ] **1.4** Agree which application features are required for assessment: upload, results, overlays, history, export, review actions and access control. Remove unsupported promises from scope.
- [ ] **1.5** Confirm the institution's current report, literature, presentation and paper requirements with the guide; record actual submission dates.
- [ ] **1.6** Define research questions before choosing a final model. Suggested questions: Does preserving image detail improve segmentation? Which preprocessing helps? How do loss and negative sampling affect missed regions and false positives? Does refinement justify its cost?
- [ ] **1.7** Define the primary metric, secondary metrics, acceptable error trade-offs and selection rule. Avoid inventing a guaranteed accuracy target.
- [ ] **1.8** Assign team responsibilities, review duties and a compute budget; maintain one experiment tracker and issue list.

**Phase complete when:** A guide-reviewed scope and dated experiment protocol exist. Required features and optional research directions are clearly separated.

## Phase 2 — Establish a runnable baseline

- [x] **2.1** Confirm accessible copies of dataset and checkpoint. The latest FracAtlas upload failed; retry it or verify an earlier intact copy before data work.
- [ ] **2.2** Preserve the existing model, threshold metadata and repository commit as an immutable baseline; record hashes and provenance without overwriting them.
- [x] **2.3** Create a tested Python environment and install PyTorch, OpenCV, FastAPI and the remaining dependencies. Record exact package versions.
- [ ] **2.4** Install frontend dependencies from the lockfile; run the existing typecheck, lint, tests and production build. Record failures and fixes.
- [ ] **2.5** Verify available GPU/CPU, CUDA compatibility, RAM, VRAM and storage on the intended training machine; measure a representative batch's resource use.
- [ ] **2.6** Make dataset/checkpoint/config paths explicit and portable; remove reliance on a developer-specific Windows path.
- [x] **2.7** Strictly load the supplied weights into the intended architecture; verify finite output, expected shape and a real-image forward pass.
- [ ] **2.8** Resolve threshold provenance: bind calibration to model hash and split. Recalibrate on validation if the association cannot be recovered.
- [x] **2.9** Add evaluation-only and inference-only commands so assessing a checkpoint never retrains or overwrites it.
- [x] **2.10** Make research runs fail clearly when the real dataset is missing; allow synthetic data only through an explicit demo/test option.

**Phase complete when:** A documented clean setup can load the existing model and produce a traceable prediction. A baseline smoke result is not yet a performance result.

## Phase 3 — Audit data and prevent leakage

- [x] **3.1** Verify archive integrity and authoritative dataset source, citation and use terms; record dataset version and checksum.
- [x] **3.2** Build one manifest joining dataset.csv, image files and COCO annotations. Include normals that the current loader omits.
- [x] **3.3** Audit missing/duplicate files, decoding failures, dimensions, fracture labels, annotation IDs and polygon validity. Record every exclusion and its reason.
- [x] **3.4** Visualize original image/mask pairs across anatomy, image size, hardware, multiple fractures and views; review alignment and annotation meaning.
- [x] **3.5** Verify zero masks only for explicitly labeled normal images; investigate positive labels without usable masks.
- [x] **3.6** Preserve all fracture instances in metadata even when training a binary union mask.
- [x] **3.7** Check exact and near duplicates and related views; group by patient/study where reliable identifiers exist. Document limitations when identifiers are absent.
- [x] **3.8** Select one split protocol, explaining the difference between the supplied fracture-only split and the earlier custom split. Allocate normals explicitly.
- [x] **3.9** Freeze and save train/validation/test IDs before augmentation or crop generation; keep derived images in their source split.
- [x] **3.10** Check fracture prevalence and anatomy/view/hardware distributions across splits; report subgroup counts rather than assuming balance.
- [x] **3.11** Replace repeated full-resolution dataset caches with shared or lazy loading; confirm practical memory use.
- [ ] **3.12** Technical audit report and data dictionary generated 6 October (`experiments/phase3_review/`); external approval outstanding. Generate a dataset-audit report and approved data dictionary for the paper.

**Phase complete when:** A reproducible manifest and immutable split files exist, with no known cross-split duplicate leakage and explicit remaining grouping limitations.

## Phase 4 — Correct the learning and output pipeline

- [x] **4.1** Consolidate preprocessing into one implementation shared by training, evaluation and serving.
- [x] **4.2** Add aspect-preserving resizing/padding and inverse-coordinate transforms; exclude padded areas from loss and metrics.
- [x] **4.3** Parameterize image size, normalization, CLAHE and blur so they can be tested independently.
- [x] **4.4** Verify mask interpolation, polygon conversion and small-region survival after resizing; test overlay alignment in original coordinates.
- [x] **4.5** Add controlled positive/normal sampling for training only; preserve a documented validation/test distribution.
- [x] **4.6** Seed every augmentation path, including the fallback random generator; record deterministic settings and remaining nondeterminism.
- [x] **4.7** Inspect augmented image/mask pairs; make elastic deformation optional and test its anatomical plausibility.
- [x] **4.8** Version the model output contract. For new BCE-based training, use logits directly with BCEWithLogitsLoss and apply sigmoid consistently elsewhere.
- [x] **4.9** Implement and verify the planned loss candidates; document actual FP/FN weighting and exponent conventions. Test empty-mask gradients and finite loss.
- [x] **4.10** Add structured epoch logs, learning-rate logs, loss components, precision/recall, foreground occupancy and checkpoint metadata.
- [x] **4.11** Run a tiny-subset overfit check to catch learning or label bugs before full training; inspect failures before scaling up.
- [x] **4.12** Replace contour-area-based fracture presence with an explicit, validated decision rule; distinguish pixel count from contour area.
- [x] **4.13** Return no-region/not-applicable for empty masks instead of Mild.
- [x] **4.14** Make component filtering configurable; preserve multiple findings unless validation justifies removal.
- [x] **4.15** Remove hardcoded confidence values from API and UI. Add a confidence field only if its meaning and validation are established.
- [x] **4.16** Evaluate raw masks and the exact final masks returned by the serving pipeline.

**Phase complete when:** Meaningful tests cover image/mask alignment, empty and thin masks, multiple components, loss behavior and the common inference path.

Phase 4 completion evidence (6 October): `experiments/phase4_checks/PHASE4_REPORT.md`. New versioned pipeline checked; historical/E2 pipeline preserved. Elastic deformation visually reviewed and disabled by default. Overfit scores are training memorization only.

## Phase 5 — Run baseline and improvement experiments

- [x] **5.1** Evaluate the preserved original checkpoint on explicitly identified data, checking possible training overlap before treating any result as held out.
- [ ] **5.2** Train a corrected Attention U-Net baseline using the frozen protocol; save per-case validation predictions and failure examples.
- [ ] **5.3** Compare aspect-preserving 256 and 512 inputs under matched settings; log memory and training/inference cost.
- [ ] **5.4** Compare normalized original images, CLAHE only and CLAHE+blur at the chosen resolution.
- [ ] **5.5** Compare current focal Tversky, BCE-plus-Dice and a documented Unified Focal variant with sampling and other settings fixed.
- [ ] **5.6** Compare representative positive/normal sampling settings; assess false-positive changes as well as fracture recall.
- [ ] **5.7** Test conservative augmentation versus elastic deformation; retain only settings supported by validation evidence.
- [ ] **5.8** Compare plain U-Net with Attention U-Net using the same protocol; measure whether attention contributes.
- [ ] **5.9** Compare a modest pretrained residual-encoder U-Net if compute permits; separate the effect of pretraining from architecture where feasible.
- [ ] **5.10** Diagnose underfitting versus overfitting from curves and predictions; tune learning rate, regularization and training duration within a predefined budget.
- [ ] **5.11** Review false positives and missed regions by anatomy, hardware, image size and annotation size; prioritize changes from these errors.
- [ ] **5.12** Repeat promising configurations across seeds or suitable development folds; state when resource limits leave only preliminary evidence.
- [ ] **5.13** Test interactions among the best preprocessing, resolution and loss settings rather than assuming individually helpful changes always combine well.
- [x] **5.14** Maintain a complete experiment ledger, including unsuccessful runs, code version, configuration, seed, runtime and exclusion decisions.

### Conditional experiments — decide explicitly

- [ ] **5.C1** Decide whether small-target errors justify predicted-region refinement or overlapping tiles. If used, evaluate proposal misses, end-to-end recall and added latency; never use ground-truth test boxes for an automatic-system comparison.
- [ ] **5.C2** Decide whether a case-classification head or separate classifier is needed to meet scope. Evaluate its effect on missed fractures before using it to suppress segmentation.
- [ ] **5.C3** Decide whether MedSAM is worth a refinement/annotation experiment. Distinguish automatic predicted prompts from human-assisted operation.
- [ ] **5.C4** Decide whether ensembling/test-time augmentation offers enough gain for its computational cost; compare fairly with non-ensemble baselines.
- [ ] **5.C5** Decide whether compatible external data can support additional evaluation; verify label definitions and grouping before combining datasets.

**Phase complete when:** The chosen approach is supported by controlled comparisons and failure analysis. “Not pursued” is acceptable for conditional work when the reason is recorded. Higher complexity is not required for completion.

## Phase 6 — Freeze the model and produce final evidence

6 October update: development counterparts of 6.3–6.8 and 6.10–6.13 table regeneration/claim audit executed; final checkboxes remain open because the selected full model and matched comparisons are unfinished. See `experiments/P6_development_validation/PHASE6_REPORT.md`. No teammate review is claimed. Test remains reserved.

- [ ] **6.1** Select weights using the agreed development rule; calibrate threshold and component filtering on validation only.
- [ ] **6.2** Freeze weights, preprocessing, output resolution, threshold, postprocessing and code version before final testing.
- [ ] **6.3** Export per-positive-image Dice, IoU, precision and recall plus global pixel metrics; document empty-ground-truth conventions.
- [ ] **6.4** Evaluate normals separately: specificity, false-positive cases and false-positive regions per image.
- [ ] **6.5** Evaluate case-level sensitivity/precision/confusion matrix if detection is claimed; use PR-AUC/AUROC only with a defined continuous score.
- [ ] **6.6** Evaluate region-level recall with a predefined one-to-one matching rule, including multiple-fracture images.
- [ ] **6.7** Report subgroup counts and results for relevant anatomy, views, hardware and small regions without overstating small subgroups.
- [ ] **6.8** Estimate uncertainty using suitable confidence intervals and paired comparisons; resample patient/study clusters when identifiers permit.
- [ ] **6.9** Compare the chosen system with baselines on the same final protocol; disclose dataset, compute, seed and pretraining differences.
- [ ] **6.10** Measure warm inference, complete request latency and peak memory on named hardware; verify any timing claim in the slides.
- [ ] **6.11** Assemble representative successes, failures and multi-fracture/normal examples without selecting only attractive overlays.
- [ ] **6.12** Audit severity wording, measurement units and unsupported clinical claims. Do not infer clinical severity validity from segmentation quality.
- [ ] **6.13** Review all final numbers with another teammate; regenerate tables from saved outputs and retain the full result archive.

**Phase complete when:** Final results are traceable to frozen inputs and code, include uncertainty and errors, and describe the exact delivered model. If final testing leads to further tuning, disclose that and revise the evaluation design rather than reusing it as an untouched test.

## Phase 7 — Finish the real application and reproducibility package

6 October update: local implementation, isolated dependency installation, lockfile reproduction, real original/bundle API tests and recorded browser rehearsal executed. Source version uses a SHA-256 snapshot because the Git root is the user's home directory; no home-wide Git action was performed. Final selected-model delivery and another teammate's independent reproduction remain open. See `experiments/session_20261006_p6p7/SECURITY_REVIEW.md`.

- [x] **7.1** Disable mocks in the real-demo configuration; align API URL, ports, CORS and launch instructions.
- [x] **7.2** Use maintained multipart handling and validate actual image decoding, dimensions and size; provide clear invalid-input errors.
- [x] **7.3** Load the model once per worker; bound concurrency, handle timeouts/job failures, use robust IDs and clean temporary data.
- [x] **7.4** Add readiness checks for model/config availability and expose model version in results.
- [x] **7.5** Test distinct uploaded images through queue → inference → result; confirm original image, mask and overlay belong to the same case.
- [x] **7.6** Preserve viewer aspect ratio and provide sensible no-region, uncertain and failed-analysis states.
- [x] **7.7** Implement durable history/review storage and downloadable results if retained in scope; otherwise disable those controls and remove their completion claims.
- [x] **7.8** Resolve demo authentication/reset/admin/audit placeholders. Before shared deployment, implement server-side authorization, safe credentials/sessions and protected image access.
- [x] **7.9** Complete integration tests and CI for the backend and real inference path; do not rely only on mocked frontend tests.
- [x] **7.10** Repair Docker/backend routing if container delivery is required; otherwise provide a tested local launch procedure.
- [x] **7.11** Package source commit, dependencies, configs, split IDs, data retrieval instructions, checkpoint hash, threshold and evaluation commands.
- [x] **7.12** Rehearse a clean-environment reproduction and record a demonstration video using appropriate research examples.

**Phase complete when:** The application delivers the evaluated pipeline, required features work, and another teammate can reproduce the demo from instructions.

## Phase 8 — Prepare consistent documents and paper materials

- [ ] **8.1** Reconcile report, slides, README and diagrams to PyTorch, the actual loss, chosen split, architecture and threshold.
- [ ] **8.2** Remove unsupported claims about accuracy, speed, clinical severity, no overfitting or completed modules.
- [ ] **8.3** Update DFDs and architecture diagrams to actual storage, preprocessing and inference behavior; remove nonexistent patch/database/report stages or implement them.
- [ ] **8.4** Expand and verify the literature review using relevant post-2020 sources; check author names, year, venue, DOI and task/metric comparability.
- [ ] **8.5** Build a related-work matrix covering data, task, method, evaluation, limitations and relevance. Check the guide's reference-count/recency requirements.
- [ ] **8.6** Maintain a reference manager/BibTeX database; cite the dataset, base architecture, loss methods and reused code appropriately.
- [ ] **8.7** Generate paper figures: architecture, preprocessing/crop examples, learning curves, qualitative comparisons and failure cases.
- [ ] **8.8** Generate paper tables: dataset/splits, implementation settings, baseline comparisons, ablations, subgroup results and efficiency.
- [ ] **8.9** Complete the project report, final presentation and viva notes using only verified results; update obsolete Phase-I/Phase-II statements.
- [ ] **8.10** Record authorship contributions and obtain agreement on author order, affiliations and corresponding author before submission.

**Phase complete when:** There is one consistent account of the project and every proposed paper claim maps to saved evidence.

## Phase 9 — Write and finalize the original research paper

### Positioning and venue

- [ ] **9.1** Reassess novelty against verified literature after experiments. Using Attention U-Net alone is not a new architecture contribution; define the actual contribution supported by results.
- [ ] **9.2** Choose an honest paper type: applied comparative study, reproducible pipeline study or methodological paper only if a distinct method is developed and justified.
- [ ] **9.3** Shortlist suitable journals/conferences with the guide; verify current scope, review process, indexing claims, fees, deadlines and manuscript rules from official sources before choosing.
- [ ] **9.4** Select the target venue and template; obtain team agreement on any publication charges. Do not assume acceptance or mandatory paid publication.

### Manuscript drafting

- [ ] **9.5** Write a precise title and contribution statement without unsupported “novel,” “state-of-the-art” or clinical-readiness claims.
- [ ] **9.6** Draft the Introduction: problem, gap, research questions and measured contribution.
- [ ] **9.7** Draft Related Work using the verified literature matrix; distinguish classification, detection and segmentation evidence.
- [ ] **9.8** Draft Data and Methods: provenance, inclusion/exclusion, labels, splits, leakage controls, preprocessing, architecture, loss, training, calibration and postprocessing.
- [ ] **9.9** Draft Experimental Setup: hardware/software, seeds, budgets, baselines, ablations, metrics, matching rules and statistical analysis.
- [ ] **9.10** Draft Results from generated tables, including negative findings, uncertainty, subgroup counts and efficiency.
- [ ] **9.11** Draft Discussion explaining observed gains and trade-offs without presenting hypotheses as established mechanisms.
- [ ] **9.12** Draft Limitations: dataset size/domain, annotation ambiguity, grouping limits, normal-image errors, severity validity, external validation and deployment scope.
- [ ] **9.13** Write Conclusion and future work grounded in the final evidence.
- [ ] **9.14** Write Abstract last; verify every number and claimed contribution against final results.

### Transparency, review and final package

- [ ] **9.15** Add appropriate data/code availability, dataset-use/ethics statements, funding, conflicts, contributions and AI-assistance disclosure as required by the venue. Do not invent approvals or imply new patient recruitment.
- [ ] **9.16** Confirm permissions for figures/data/code and permitted sharing of checkpoints; exclude sensitive information and unlicensed redistributed material.
- [ ] **9.17** Independently reproduce the principal table from saved outputs and inspect all equations, captions, units, metric denominators and citations.
- [ ] **9.18** Obtain a technical review from teammates and the guide; seek appropriate domain review if retaining clinical interpretation claims.
- [ ] **9.19** Perform language, originality and reference checks on the final manuscript. Earlier survey similarity reports do not cover this new paper.
- [ ] **9.20** Format to the target template; verify page/word limits, readable figures, supplementary files and anonymous-review requirements where applicable.
- [ ] **9.21** Prepare cover letter, supplementary experimental details and reproducibility links; confirm every author's approval of the exact final version.
- [ ] **9.22** Deliver the final paper package: manuscript PDF, editable source, bibliography, figures/tables, supplementary material and experiment/reproducibility index.

**Final completion condition:** An original, technically reviewed, submission-ready research paper exists alongside the functioning project and reproducible evidence. A positive result or new accuracy record is not required for an honest paper; sound methods and accurate reporting are required.

**After this endpoint, if the team wants submission:** Obtain explicit authorization to submit the approved manuscript, retain submission proof, track the editorial decision and respond to reviewers with a point-by-point response and versioned revisions. Acceptance/publication depends on external review and cannot be guaranteed.

## Research paper outline and evidence checklist

| Paper section | Evidence needed |
|---|---|
| Abstract | Frozen task, dataset protocol, actual main results and limitations |
| Introduction | Clear research questions and justified contribution |
| Related Work | Verified post-2020 sources and fair task comparisons |
| Data | Manifest, split IDs, exclusions, label definitions and leakage audit |
| Methods | Versioned preprocessing/model/loss/inference specification |
| Experiments | Baselines, controlled ablations, hardware, seeds and selection rules |
| Results | Regenerable tables, uncertainty, qualitative evidence and failure analysis |
| Discussion | Evidence-based interpretation, scope and trade-offs |
| Limitations | Known data, label, generalization and clinical interpretation limits |
| Reproducibility | Code/config/model references and evaluation instructions |

## Immediate execution queue

1. Complete 1.1–1.8: agree the research scope and responsibilities.
2. Complete 2.1–2.10: get the supplied model running reproducibly.
3. Complete 3.1–3.12: establish the correct all-image dataset protocol.
4. Complete Phase 4 and train the corrected baseline before adding architecture complexity.

Paper preparation can start with the outline, reference database and methods notes now. Final claims, abstract and results must wait for the frozen experiments.
