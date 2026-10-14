# Targeted research notes — 7 October 2026

Trigger: measured normal false alarms, saturated pixel scores, wrong-location image positives and failed threshold filtering. Published metrics below are not MedVision results. No external data or architecture was substituted.

## R1: On Calibration of Modern Neural Networks

- Authors/year: Chuan Guo, Geoff Pleiss, Yu Sun, Kilian Q. Weinberger; 2017.
- Source: ICML/PMLR70. [Official paper](https://proceedings.mlr.press/v70/guo17a/guo17a.pdf).
- Problem/method: neural confidence miscalibration; compare postprocessing calibrators including scalar temperature scaling.
- Dataset/result: image and text classification; simple temperature scaling often calibrates effectively. This is not fracture validation.
- Local insight/application: evaluate calibration separately from detection. Applied Brier/ECE/reliability diagnostics and a sigmoid-mapping shadow experiment on separate calibration/validation groups.
- Limitations: our regularized sigmoid maps a maximum-pixel proxy; it is not temperature scaling of a trained classifier. Historical model exposure is unknown. Its Brier is worse than constant prevalence and detection errors are unchanged.
- Access: full PDF definitions/calibration methods inspected.

## R2: Deep neural network improves fracture detection by clinicians

- Authors/year: Robert Lindsey, Aaron Daluiski, Sumit Chopra, Alexander Lachapelle, Michael Mozer, Serge Sicular, Douglas Hanel, Michael Gardner, Anurag Gupta, Robert Hotchkiss, Hollis Potter; 2018.
- Source: PNAS115(45). [Original article index](https://pubmed.ncbi.nlm.nih.gov/30348771/), [author-hosted paper](https://home.cs.colorado.edu/~mozer/Research/Selected%20Publications/reprints/LindseyPNAS2018.pdf).
- Problem/method: fracture presence plus location; simultaneous classification and conditional heat map.
- Dataset/result: 135409 expert-labelled radiographs; wrist reader assessment. Clinician sensitivity80.8%→91.5%, specificity87.5%→93.9% with assistance.
- Local insight/application: image probability and segmentation pixels are distinct outputs. A learned case head is a later controlled option if negative supervision fails; no head added yet.
- Limitations: different anatomy/data/reader population; heat maps differ from polygon masks. Gains cannot be transferred.
- Access: abstract and cached original methods inspected; direct PMC hit an access challenge.

## R3: FracAtlas: A Dataset for Fracture Classification, Localization and Segmentation of Musculoskeletal Radiographs

- Authors/year: Iftekharul Abedeen, Md. Ashiqur Rahman, Fatema Zohra Prottyasha, Tasnim Ahmed, Tareque Mohmud Chowdhury, Swakkhar Shatabda; 2023.
- Source: Scientific Data10,521. [Original paper](https://www.nature.com/articles/s41597-023-02432-4), [archive](https://pmc.ncbi.nlm.nih.gov/articles/PMC10404222/).
- Problem/method/dataset: documented fracture labels/masks; 4083 radiographs,717 positive images,922 regions. Technical validation used pretrained YOLOv8s/seg,600-pixel input, fracture-only80/12/8 splits.
- Result: localization box precision.807, recall.473, mAP50.562. This does not measure normal-image specificity.
- Local insight/application: evaluate normals explicitly and disclose split differences. Preserve existing FracAtlas v6; do not treat another download as independent external data.
- Limitations: our exclusions, grouped splits and models differ; source identities do not establish patient independence.
- Access: cached original data/validation sections and author metadata inspected; direct full-page requests unavailable.

## R4: Improving traumatic fracture detection on radiographs with artificial intelligence support: a multi-reader study

- Authors/year: Rikke Bachmann, Gozde Gunes, Stine Hangaard, Andreas Nexmann, Pavel Lisouski, Mikael Boesen, Michael Lundemann, Scott G Baginski; 2024.
- Source: BJR Open6(1),tzae011. [Original paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11096271/), [author institution](https://researchprofiles.ku.dk/en/publications/improving-traumatic-fracture-detection-on-radiographs-with-artifi/).
- Problem/method: actual aided reader benefit, including nonobvious cases; paired multi-reader assessment.
- Dataset/result:15 readers,340 exams; sensitivity72%→80%, specificity81%→85%; nonobvious sensitivity60%→71%.
- Local insight/application: require reader/correction measurements; do not equate a small-mask proxy with clinical subtle/nondisplaced labels. No reader benefit claimed here.
- Limitations: nonspecialist readers, separate commercial model/data, balanced prevalence.
- Access: institution abstract and cached original methods inspected; direct PMC hit an access challenge.

## Local decisions

Shadow calibration Brier=.148435 versus constant-prevalence=.147133: no error changes, no promotion. E5/E6 test normal-image BCE coefficient1 versus2 with all other factors matched. This hypothesis comes from our measured false alarms and analytic gradient checks; literature does not guarantee it works. Resolution, classifier head, view fusion and training-only hard mining remain later controlled experiments after learning-curve/error analysis. The reserved test stays closed.
