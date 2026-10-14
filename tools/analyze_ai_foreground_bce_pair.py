"""Completed matched foreground-pixel BCE audits; never auto-promotes."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import ai_metrics as a
from tools.analyze_ai_pair import comparison,transitions,load
from tools.ai_atomic_io import json_atomic
from tools.evaluate_ai_baseline import sha


def main():
    ap=argparse.ArgumentParser()
    for name in ('reference','candidate','out'): ap.add_argument('--'+name,required=True)
    args=ap.parse_args();left_dir,right_dir,out=[Path(v).resolve() for v in (args.reference,args.candidate,args.out)]
    if any(ROOT not in v.parents for v in (left_dir,right_dir,out)) or out.exists(): raise ValueError('Completed workspace native audits and exclusive output required')
    for directory in (left_dir,right_dir):
        if not (directory/'completion.json').exists(): raise ValueError('Both native audits must finish')
        completed=load(directory/'completion.json')
        if (completed['status']!='completed' or completed['test_images_read'] or completed['calibration_fit'] or
                completed['promotion'] or not completed['independent_masks'] or
                sha(directory/'metrics.json')!=completed['metrics_sha256'] or
                sha(directory/'per_case.json')!=completed['cases_sha256']):
            raise ValueError('Completed native audit identity mismatch')
    left,right=[load(v/'metrics.json') for v in (left_dir,right_dir)]
    runs=[ROOT/m['config']['run'] for m in (left,right)];configs=[load(r/'config.json') for r in runs]
    if configs[0]['foreground_bce_coefficient']!=1 or configs[1]['foreground_bce_coefficient']!=5 or any(c['hard_factor']!=2 for c in configs): raise ValueError('Registered foreground BCE1 versus5, hard factor2 required')
    if {k:v for k,v in configs[0].items() if k!='foreground_bce_coefficient'}!={k:v for k,v in configs[1].items() if k!='foreground_bce_coefficient'}:
        raise ValueError('Uncontrolled configuration difference')
    if load(runs[0]/'initial_parameters.json')!=load(runs[1]/'initial_parameters.json'):
        raise ValueError('Model/optimizer initializations differ')
    all_records=[]
    for run,directory,config in zip(runs,(left_dir,right_dir),configs):
        state,bundle=load(run/'state.json'),load(run/'bundle.json')
        records=[json.loads(v) for v in (run/'epochs.jsonl').read_text().splitlines() if v.strip()]
        if (state['status']!='completed' or state['epochs_finished']!=12 or state['smoke'] or
                [r['epoch'] for r in records]!=list(range(1,13)) or
                [r['global_epoch'] for r in records]!=list(range(40,52)) or
                any(r['train_images_seen']!=2808 or r['unique_train_images_seen']!=2808 for r in records) or
                sha(run/'best_model.pt')!=bundle['checkpoint_sha256'] or
                sha(run/'best_model.pt')!=load(directory/'completion.json')['checkpoint_sha256']):
            raise ValueError('Full matched budget/model identity required before comparison')
        for source,digest in config['source_hashes'].items():
            if sha(ROOT/source)!=digest: raise ValueError('Training source changed: '+source)
        all_records.append(records)
    lc,rc=[load(v/'per_case.json') for v in (left_dir,right_dir)]
    la,ra=[load(v/'review_alert_cases.json') for v in (left_dir,right_dir)]
    ids={c['image_id'] for c in lc}
    labels={r['image_id']:bool(int(r['fractured'])) for r in load(ROOT/configs[0]['manifest'])['rows'] if r['split']=='val'}
    for cases in (lc,rc,la,ra):
        if (len(cases)!=463 or len({c['image_id'] for c in cases})!=463 or
                {c['image_id']:bool(c['positive']) for c in cases}!=labels):
            raise ValueError('Exact unique463 frozen IDs and labels required')
    if len(ids)!=463 or ids!={c['image_id'] for c in rc}: raise ValueError('Exact same463 required')
    original_cases=[c for c in load(ROOT/'experiments/AI_BASELINE_20261007_v1/per_case.json') if c['image_id'] in ids]
    if len(original_cases)!=463 or sum(c['positive'] for c in original_cases)!=83: raise ValueError('Same-ID original reference required')
    original=dict(classification=a.classification(original_cases),segmentation=a.segmentation(original_cases),calibration=a.calibration(original_cases))
    original_matches=sum(c['mask_region_matches_iou50'] for c in original_cases)
    original_loc=dict(precision=a.ratio(original_matches,sum(c['predicted_components'] for c in original_cases)),
                      recall=a.ratio(original_matches,sum(c['gt_instances'] for c in original_cases)))
    cm=right['classification']['confusion_matrix'];seg=right['segmentation'];base=original['segmentation'];matched=left['segmentation'];loc=right['mask_instance_localization']['0.5']
    checks=dict(classification_counts=cm['tp']>=79 and cm['tn']>=342 and right['classification']['accuracy']>=.9,
        native_positive_dice=seg['mean_positive_dice']>=max(base['mean_positive_dice'],matched['mean_positive_dice'])+.02,
        native_positive_iou=seg['mean_positive_iou']>max(base['mean_positive_iou'],matched['mean_positive_iou']),
        instance_precision=loc['precision'] is not None and loc['precision']>max(original_loc['precision'],left['mask_instance_localization']['0.5']['precision']),
        instance_recall=loc['recall'] is not None and loc['recall']>max(original_loc['recall'],left['mask_instance_localization']['0.5']['recall']),
        false_positive_pixels=seg['pixel_counts']['fp']<min(base['pixel_counts']['fp'],matched['pixel_counts']['fp']),
        useful_pixel_coverage_vs_matched=seg['global_pixel_recall']>=matched['global_pixel_recall'])
    development_keep=(right['classification']['recall_sensitivity']>=left['classification']['recall_sensitivity'] and
        right['classification']['specificity']>=left['classification']['specificity'] and
        seg['mean_positive_dice']>matched['mean_positive_dice'] and seg['mean_positive_iou']>matched['mean_positive_iou'] and
        seg['pixel_counts']['fp']<=matched['pixel_counts']['fp'] and seg['global_pixel_recall']>=matched['global_pixel_recall'] and
        loc['precision']>=left['mask_instance_localization']['0.5']['precision'] and
        loc['recall']>=left['mask_instance_localization']['0.5']['recall'])
    result=dict(reference=str(left_dir.relative_to(ROOT)),candidate=str(right_dir.relative_to(ROOT)),
        factor='Foreground-pixel BCE coefficient1 versus5; background BCE, Dice and hard factor2 unchanged',
        all_other_configurations_matched=True,initial_model_optimizer_matched=True,
        metrics=comparison(left,right),original_same_ID_comparison=comparison(original,right),
        independent_mask_error_transitions=transitions(lc,rc),conservative_alert_error_transitions=transitions(la,ra),
        original_instance_localization=original_loc,matched_instance_localization=left['mask_instance_localization']['0.5'],
        uncalibrated_proxy_regressions={k:right['calibration'][k]>left['calibration'][k] for k in ('brier_score','expected_calibration_error')},
        calibration_gate_still_required=True,validation_gate_checks=checks,validation_numerical_gate_pass=all(checks.values()),
        original_pixel_recall=base['global_pixel_recall'],candidate_pixel_recall=seg['global_pixel_recall'],
        manual_native_coverage_review_required=True,
        decision='KEEP FOR DEVELOPMENT; full further gates required' if development_keep else 'REJECT as balanced overall improvement at registered operating point',
        final_success=False,promotion=False,calibration_fit=False,test_images_read=0,
        limitations=['Numerical checks never substitute for actual FP/FN/GT/mask inspection',
            'Original useful coverage must be assessed even when candidate exceeds an underfit matched reference',
            'No patient/study IDs or expert clinical subtype adjudication',
            'One seed and no external validation; component-box AP remains a proxy'])
    out.mkdir();json_atomic(out/'comparison.json',result)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,4,figsize=(16,7))
    titles=['Training loss','Segmentation loss','Review sensitivity','Review specificity','Review AUROC','Positive native Dice','Positive native IoU','Mask specificity']
    for records,label in zip(all_records,('Reference: foreground BCE1','Candidate: foreground BCE5')):
        series=[[r['loss_components'][k] for r in records] for k in ('total','segmentation_total')]
        series+=[[r['validation']['classification'][k] for r in records] for k in ('recall_sensitivity','specificity','auroc')]
        series+=[[r['validation']['delivered'][k] for r in records] for k in ('mean_positive_dice','mean_positive_iou')]
        series+=[[r['validation']['mask_classification']['specificity'] for r in records]]
        for ax,values,title in zip(axes.ravel(),series,titles):
            ax.plot(range(1,13),values,marker='o',label=label);ax.set(title=title,xlabel='Additional epoch');ax.legend(fontsize=7)
    fig.tight_layout();fig.savefig(out/'paired_learning_curves.png',dpi=150);plt.close(fig)
    (out/'PAIR_ANALYSIS.md').write_text('# Matched foreground-pixel BCE weighting\n\n'+result['decision']+'\n\n'+json.dumps(result,indent=2)+'\n\nInspect actual masks and original coverage. No automatic calibration, test evaluation or promotion.\n',encoding='utf-8')
    json_atomic(out/'completion.json',dict(status='completed',comparison_sha256=sha(out/'comparison.json'),test_images_read=0,promotion=False))
    print(json.dumps(dict(decision=result['decision'],validation_gate_checks=checks),indent=2))


if __name__=='__main__': main()
