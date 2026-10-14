"""Validation failure/threshold analysis from immutable float32 baseline output."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import sys
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import ai_metrics as a
from tools.evaluate_ai_baseline import save, sha


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--baseline',required=True); ap.add_argument('--out',required=True)
    args=ap.parse_args(); baseline=Path(args.baseline).resolve(); out=Path(args.out).resolve()
    if ROOT not in out.parents or out.exists(): raise ValueError('Use a new analysis run')
    if not (baseline/'completion.json').exists(): raise ValueError('Immutable completed baseline required')
    cases=json.loads((baseline/'per_case.json').read_text()); result=json.loads((baseline/'metrics.json').read_text())
    out.mkdir(); cv2.setNumThreads(1)
    arrays=np.load(baseline/'probabilities_float32.npz')
    comparisons={(round(t*.05,2),p):[] for t in range(1,20) for p in ('all','largest','min16')}
    for c in cases:
        prob=arrays[c['image_id']]; h,w=c['native_shape']
        if prob.dtype != np.float32: raise ValueError('Exact threshold analysis requires float32, never a quantized cache')
        target=cv2.imread(str(baseline/'masks'/f'{Path(c["image_id"]).stem}_reference.png'),cv2.IMREAD_GRAYSCALE)>0
        ys=np.minimum((np.arange(h)*256/h).astype(int),255); xs=np.minimum((np.arange(w)*256/w).astype(int),255)
        mapping=(ys[:,None]*256+xs[None,:]).ravel()
        weights=np.bincount(mapping,minlength=65536); gtweights=np.bincount(mapping,weights=target.ravel(),minlength=65536)
        for threshold in [round(t*.05,2) for t in range(1,20)]:
            raw=(prob>=threshold).astype(np.uint8)
            n,labels,stats,_=cv2.connectedComponentsWithStats(raw,8)
            labels=labels.ravel()
            areas=np.bincount(labels,weights=weights,minlength=n).astype(np.int64)
            intersections=np.bincount(labels,weights=gtweights,minlength=n).astype(np.int64)
            ids=np.arange(1,n)
            choices={'all':ids,'largest':np.array([1+np.argmax(stats[1:,cv2.CC_STAT_AREA])]) if n>1 else ids,
                     'min16':ids[stats[1:,cv2.CC_STAT_AREA]>=16]}
            for policy,keep in choices.items():
                tp=int(intersections[keep].sum()); pred=int(areas[keep].sum()); gt=int(target.sum()); fp=pred-tp; fn=gt-tp
                comparisons[threshold,policy].append(dict(image_id=c['image_id'],positive=c['positive'],prediction_present=pred>0,
                    case_score=c['case_score'],tp_pixels=tp,fp_pixels=fp,fn_pixels=fn,
                    dice=a.ratio(2*tp,2*tp+fp+fn) if c['positive'] else None,iou=a.ratio(tp,tp+fp+fn) if c['positive'] else None,
                    segmentation_precision=a.ratio(tp,tp+fp),segmentation_recall=a.ratio(tp,tp+fn)))
    table=[dict(threshold=t,policy=p,classification=a.classification(cc),segmentation=a.segmentation(cc)) for (t,p),cc in comparisons.items()]
    recorded=next(v for v in table if v['threshold']==.9 and v['policy']=='all')
    if recorded['classification']['confusion_matrix']!=result['classification']['confusion_matrix'] or recorded['segmentation']['pixel_counts']!=result['segmentation']['pixel_counts']:
        raise RuntimeError('Float32 cache failed exact baseline native integer reproduction')
    save(out/'threshold_policy_comparison.json',table)
    with (out/'threshold_policy_comparison.csv').open('x',newline='') as f:
        rows=[dict(threshold=v['threshold'],policy=v['policy'],**{k:v['classification'][k] for k in ('accuracy','precision','recall_sensitivity','specificity','f1','false_positive_rate','false_negative_rate')},positive_dice=v['segmentation']['mean_positive_dice'],positive_iou=v['segmentation']['mean_positive_iou']) for v in table]
        wr=csv.DictWriter(f,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)
    counts=Counter(c['category'] for c in cases)
    failure=Counter(tag for c in cases for tag in c['segmentation_failure_tags'])
    best_specificity=max(table,key=lambda v:v['classification']['specificity'])
    eligible=[v for v in table if v['classification']['recall_sensitivity']>=.95 and v['classification']['specificity']>=.90 and v['classification']['accuracy']>.90]
    fns=[c for c in cases if c['category']=='FN']
    positives=[c for c in cases if c['positive']]
    mislocated=[c for c in positives if c['prediction_present'] and c['tp_pixels']==0]
    baseline_hash=sha(baseline/'metrics.json')
    summary=dict(baseline_metrics_sha256=baseline_hash,scope='Validation-only diagnostics; no model, threshold or production change',
        counts=dict(counts),segmentation_tags=dict(failure),complete_mislocalization_image_ids=[c['image_id'] for c in mislocated],
        false_negatives=[dict(image_id=c['image_id'],score=c['case_score'],gt_fraction=c['gt_fraction'],flags=c['flags'],panel=str(baseline/c['review_panel'])) for c in fns],
        threshold_policy_combinations=len(table),balanced_target_combinations=len(eligible),
        highest_specificity_point=best_specificity,exact_native_baseline_reproduction=True,
        primary_observed_bottleneck='Background/fracture discrimination and case-score construction. Case presence accepts any saturated segmentation pixel; it does not establish a correctly localized fracture. Threshold/component filtering alone cannot resolve the observed error trade-off.',
        possible_causes_not_proven=['legacy positive-only training coverage','normal cortical/joint appearance ambiguity','cast/acquisition/contrast effects','original model training exposure and annotation noise'],
        clinical_review_status='Two missed-fracture and selected FP/mislocalization panels technically inspected; all case-specific panels generated. Expert cause attribution for the entire set remains pending.',
        decision='REJECT threshold-only fix for balanced reliability; preserve production baseline; no >90% or clinical improvement claim',test_images_read=0)
    save(out/'analysis.json',summary)
    save(out/'VALIDATION_HARD_POSITIVE_REVIEW_SET.json',dict(scope='VALIDATION errors for evaluation/review ONLY, forbidden as training examples',
         empty_miss=[c['image_id'] for c in fns],mislocalization=[c['image_id'] for c in mislocated],poor_overlap=[c['image_id'] for c in positives if c['dice']<.2]))
    save(out/'VALIDATION_HARD_NEGATIVE_REVIEW_SET.json',dict(scope='VALIDATION false positives for evaluation/review ONLY, forbidden as training examples',image_ids=[c['image_id'] for c in cases if c['category']=='FP']))
    # Dataset-group bootstrap, not a patient-independent confidence interval.
    groups={}
    for c in cases: groups.setdefault(c['group'],[]).append(c)
    keys=list(groups); rng=np.random.default_rng(42); intervals={k:[] for k in ('accuracy','recall_sensitivity','specificity','precision','f1','positive_dice')}
    for _ in range(1000):
        sample=[c for i in rng.integers(0,len(keys),len(keys)) for c in groups[keys[i]]]
        cm=Counter(c['category'] for c in sample); tp,fp,fn,tn=(cm[k] for k in ('TP','FP','FN','TN'))
        values=dict(accuracy=a.ratio(tp+tn,len(sample)),recall_sensitivity=a.ratio(tp,tp+fn),specificity=a.ratio(tn,tn+fp),
                    precision=a.ratio(tp,tp+fp),f1=a.ratio(2*tp,2*tp+fp+fn),positive_dice=float(np.mean([c['dice'] for c in sample if c['positive']])))
        for k,v in values.items():
            if v is not None: intervals[k].append(v)
    save(out/'group_bootstrap95.json',dict(replicates=1000,seed=42,unit='conservative duplicate groups, NOT patients',intervals={k:np.quantile(v,[.025,.975]).tolist() for k,v in intervals.items()}))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    all_points=[v for v in table if v['policy']=='all']; fig,ax=plt.subplots(figsize=(7,5))
    for key,label in [('recall_sensitivity','Sensitivity'),('specificity','Specificity'),('precision','Precision')]:
        ax.plot([v['threshold'] for v in all_points],[v['classification'][key] for v in all_points],label=label)
    ax.set(xlabel='Pixel probability threshold',ylabel='Image-level metric',ylim=(0,1),title='Validation threshold trade-off, unchanged model');ax.legend();fig.tight_layout();fig.savefig(out/'threshold_tradeoff.png',dpi=160);plt.close(fig)
    text=f'''# Evidence-based failure analysis — 7 October 2026

Full immutable baseline: {len(cases)} validation cases. FP={counts['FP']}, FN={counts['FN']}, TP={counts['TP']}, TN={counts['TN']}. All native masks and case-specific panels are retained in the baseline directory. No test inference.

## False positives and confidence

453/502 provider-labelled normal cases are flagged. The image decision is ANY mask pixel >=.90. Maximum sigmoid output is exactly1 for {result['calibration']['score_exactly_one_count']}/612 cases. In the .90–1 score bin, mean score is .99966 but only19.25% of561 images are fractured. This score measures a selected segmentation pixel, not calibrated case probability.

Technical visual examples IMG0000008, IMG0000010, IMG0000024, IMG0000027, IMG0000030, IMG0000038 and IMG0000050 show predicted normal-region marks near joint/cortical margins or other foreground edges. This is an observation of prediction placement against provider labels, not independent clinical confirmation that every label is correct. Every FP panel is available; exhaustive expert causal adjudication remains pending. Normal anatomical ambiguity and insufficient negative training are hypotheses, not proven original-checkpoint history.

## False negatives

The TWO image-level misses are IMG0002316 (max score .002709) and IMG0003021 (max score .002847). Both actual original/reference/empty-prediction panels were inspected individually. Both show visible overlying immobilization/cast-like material and small annotated regions. This association does not prove the cast caused the miss or establish subtle/nondisplaced clinical labels. Their exact scores, masks, metadata and occupancy are in analysis.json and the baseline per_case.json.

Raising or lowering ordinary thresholds .05–.95 cannot recover these scores. Lowering a gate to .002 would need separate validation and likely worsen false positives; it has NOT been adopted.

## Segmentation and localization

Algorithmic tag counts (nonexclusive): {json.dumps(dict(failure))}. There are {len(mislocated)} positive images flagged at regions with ZERO overlap with ground truth. These count as image-level TP but are localization failures. IMG0001073 marks regions on a composite radiograph while missing both supplied wrist-region targets; IMG0001382 is another reviewed zero-overlap positive. This explains why98.18% case sensitivity is not98.18% fracture localization.

Native mask matching at IoU.50 recovers45/137 annotated instances (32.85%); there are1135 predicted components across all images, with1090 unmatched at that IoU. Positive Dice=.482326, global pixel precision=.104595. Under/over segmentation tags are defined by recall/precision below.50; empty and zero-overlap misses are separated. Tags describe measured overlap and are not clinical causes.

## Threshold experiment and decision

Recomputed57 combinations:19 thresholds .05–.95 x all/largest/min16 filtering, from EXACT float32 maps and native integer counts. .90/all confusion and pixel counts reproduce the baseline exactly. Best specificity over this grid={best_specificity['classification']['specificity']:.6f} (threshold {best_specificity['threshold']}, policy {best_specificity['policy']}); sensitivity there={best_specificity['classification']['recall_sensitivity']:.6f}. ZERO combinations satisfy accuracy>.90, sensitivity>=.95 and specificity>=.90. REJECT threshold/component filtering as a sufficient reliability fix. Production threshold remains.90.

## Primary measured bottleneck and next controlled experiment

The measured bottleneck is background/fracture discrimination combined with the any-pixel case rule and saturated case-score proxy. A scalar threshold cannot separate the present outputs. The normal-inclusive E2 experiment also remains worse in Dice than the original at its latest saved epoch, so changing loss alone is not an accepted improvement.

Next complete interrupted E2 under its unchanged protocol, then compare one negative-sampling factor in fresh matched runs with the same architecture/loss/preprocessing/seed and a prospective validation/calibration partition. Do not use these VALIDATION hard-positive/negative review lists for training. Training hard sets require TRAIN-only inference and bounded within-class weighting with representative sampling; no naive duplication. Geometry/resolution, classifier heads and further loss changes remain subsequent experiments only after analyzing this comparison.

## Boundaries

No reliable patient IDs, clinical subtle/nondisplaced labels or paired study identities. View/anatomy results are in the baseline report with denominators; frontal is not proven AP and rare view groups are small. FracAtlas is the EXISTING dataset. No new external dataset, no clinical reader study, no calibrated clinical confidence and no production promotion. All architecture/data histories and expert-review gaps must accompany future improvement claims.
'''
    with (out/'FAILURE_ANALYSIS.md').open('x',encoding='utf-8') as f:f.write(text)
    if sha(baseline/'metrics.json')!=baseline_hash:raise RuntimeError('Baseline changed')
    save(out/'completion.json',dict(status='completed',baseline_unchanged=True,test_images_read=0,source_sha256=sha(__file__)))
    print(json.dumps(dict(status='completed',failure_tags=dict(failure),mislocalized_positive_count=len(mislocated),best_specificity=best_specificity['classification']['specificity'],balanced_target_combinations=len(eligible)),indent=2))


if __name__=='__main__':main()
