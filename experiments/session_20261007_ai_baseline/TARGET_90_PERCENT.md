# Reaching greater than 90% accuracy without sacrificing fracture detection

7 October 2026. This is a target and decision sequence, not a achieved result. Current GPU training is unchanged.

On the prospective validation set (83 fractures,380 normals,463 total), predicting every image normal yields380/463 =82.0734% accuracy and zero sensitivity. A useful example target is at least79/83 detected fractures and342/380 correct normals: sensitivity95.1807%, specificity90%, accuracy421/463 =90.9287%. That allows at most4 image misses and38 false-positive normal cases. Segmentation/localization/calibration gates must additionally pass; counts alone do not establish radiologist reliability.

Latest observed COMPLETE E5 epoch was6 at .50/all: TP75,FN8,TN65,FP315; sensitivity90.3614%, specificity17.1053%, accuracy30.2376%, positive Dice .213616, IoU .151835, AUROC .616487. Epoch7 was underway at the progress check. E6 had not started. This is an interim reference-model observation, not a final candidate or matched historical improvement comparison.

Subsequent snapshot while recording this follow-up: epoch7 completed, TP72,FN11,TN69,FP311; accuracy30.4536%, sensitivity86.7470%, specificity18.1579%. Epoch8 is training. These fluctuations reinforce that neither more epochs nor stronger normal penalties should be assumed to meet the goal. See target_90_progress_snapshot.json and live state for exact observation time.

The main quantitative gap is normal-image specificity while preserving sensitivity and correct fracture localization. Steps:

1. Finish the frozen matched BCE1/BCE2 experiment and inspect native failures/learning curves. Stronger normal supervision is a tested hypothesis, not a guaranteed cure. No parallel architecture/sampler/preprocessing changes.
2. If normal-loss weighting fails, diagnose why. A separately supervised fracture-presence output alongside segmentation is a candidate because an isolated saturated mask pixel currently decides the entire image. Validate jointly; do not implement a hard negative classifier gate that automatically suppresses an actual fracture.
3. Evaluate bounded representative TRAIN-only hard mining using catalogued127 hard positives/1641 hard negatives, without validation leakage or naive duplication. Keep a uniform representative component.
4. Test resolution/global-local changes only after actual errors show small targets are the unresolved problem. Compare recall,FPR,Dice,IoU,latency and memory; no assumption that larger images work better.
5. Choose operating point on validation, calibrate only on separate calibration cases after selection, freeze entire protocol, then final reserved-test evaluation. Reject higher accuracy coupled with lower sensitivity, poor localization or worse segmentation.

Evidence-backed hypothesis: Lindsey et al.2018 investigate fracture detection and localization jointly ([primary publication](https://pubmed.ncbi.nlm.nih.gov/30348771/)). Our proposed case head is an experiment adapted to the observed any-pixel bottleneck; their results do not predict MedVision performance. Original methods/limitations are recorded in RESEARCH_NOTES.md. The author PDF fetch timed out during this follow-up; primary PubMed abstract was rechecked.

No >90% guarantee on existing data or by the deadline. No new weights promoted, no test images inferred and no website changes.
