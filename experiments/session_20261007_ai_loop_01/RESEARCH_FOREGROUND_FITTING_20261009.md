# Targeted research after the rejected positive-Dice experiment

9 October 2026. Specific local failure: persistent zero-overlap TRAIN fractures, suppressed GT-pixel probabilities, and failure of coefficient2 to improve balanced detection. Research motivates separable hypotheses; published metrics are never transferred to this project. No external dataset or pretrained model weights were downloaded.

## BCEWithLogitsLoss documentation

Authors: PyTorch contributors. Source/version: current official2.14 documentation, consulted9 October2026; installed training runtime remains2.9.1+cu128. [Official documentation](https://docs.pytorch.org/docs/2.14/generated/torch.nn.BCEWithLogitsLoss.html).

Problem: weighting positive targets in stable binary logit loss. Method: positive weight multiplies the target-positive BCE contribution; the background term stays unchanged. Dataset/result: software documentation, no fracture dataset or clinical result. Relevant insight: foreground-pixel weighting is different from a whole-image or Dice multiplier and can trade recall against precision. Applied locally: a separate additive foreground softplus loss with valid-pixel and per-image hard-weight reductions, tested against the existing objective. Limitation: unchanged direct background derivatives do not guarantee fewer false alarms after shared-parameter training. No recommended coefficient or90% claim comes from this source. A2.9 documentation fetch failed; the local installed implementation and synthetic scalar/gradient fixtures establish runtime compatibility.

## Artificial intelligence in fracture detection: transfer learning from deep convolutional neural networks

D H Kim and T MacKinnon,2018, Clinical Radiology73(5):439-445; DOI10.1016/j.crad.2017.11.015. [Primary PubMed abstract](https://pubmed.ncbi.nlm.nih.gov/29269036/).

Problem: fracture classification with moderate training data. Method/dataset: retrained top layer of pretrained Inceptionv3 on1,389 lateral-wrist radiographs (695 fractures/694 normals), eightfold augmentation,80/10/10 split; additional100 balanced images for final testing. Published result: AUROC.954, sensitivity.90 and specificity.88 at the reported balanced cutoff. Relevant insight: pretrained features deserve a controlled initialization study if verified local foreground recovery remains poor. Application here: retained as a conditional alternative; no architecture or pretrained-weight change implemented. Limitations: abstract-only access, restricted wrist anatomy, different data/labels/splits and no local segmentation evidence. The result does not meet this project's simultaneous95.2% sensitivity/90% specificity target and cannot predict MedVision performance. Full publisher access returned403.

## Convolutional Neural Networks for Automated Fracture Detection and Localization on Wrist Radiographs

Yee Liang Thian, Yiting Li, Pooja Jagmohan, David Sia, Vincent Ern Yao Chan and Robby T Tan,2019, Radiology: Artificial Intelligence1:e180001; DOI10.1148/ryai.2019180001. [Primary RSNA article](https://pubs.rsna.org/doi/10.1148/ryai.2019180001).

Problem: detecting/localizing radius and ulna fractures. Method/dataset: COCO-pretrained Inception-ResNetv2/Faster R-CNN;7,356 training studies;524 consecutive wrist studies/1,048 images for testing. Published per-image sensitivity/specificity: frontal95.7%/82.5%, lateral96.7%/86.4%. Relevant insight: detection must be assessed by both overlap and per-view errors; high sensitivity can retain substantial false alarms. Application here: preserve actual region matching and separate view-flag analysis; feature initialization remains a future controlled hypothesis. Limitations: wrist-specific box localization, larger and clinically adjudicated dataset, no MedVision Dice gain, no causal comparison proving pretraining alone is sufficient. Source access used indexed primary abstract/method excerpts; a subsequent PMC open encountered a browser challenge. No claim of full-text or source-code reproduction.

Existing detailed segmentation-gradient/nnU-Net/FracAtlas research remains in RESEARCH_SPARSE_FRACTURE_20261008.md. The dataset paper was rediscovered but is not counted as a new insight. Secondary reviews, unrelated repositories and an unreviewed accuracy claim were not used as evidence. The next registered intervention uses the current project's measured error/gradient evidence and only the relevant BCE weighting formula; pretrained architecture/resolution/external-data changes are not bundled into it.
