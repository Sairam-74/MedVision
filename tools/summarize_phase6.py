"""Reproduce development tables and figures from saved integer counts, not caches."""
from collections import defaultdict
import csv
import json
from pathlib import Path
import sys
import zipfile
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.run_experiment import summary, native_pair

def main():
    out = ROOT / 'experiments/P6_development_validation'
    cases = json.loads((out/'per_case.json').read_text())
    measured = json.loads((out/'metrics.json').read_text())
    rows = {r['image_id']: r for r in json.loads((ROOT/'experiments/data_v1/manifest.json').read_text())['rows'] if r['split']=='val'}
    reproduced = summary(cases)
    for key, value in reproduced.items():
        assert value == measured['metrics'][key], key
    # Resample exact duplicate groups, not pixels, preserving all members.
    groups = defaultdict(list)
    for case in cases: groups[case['group']].append(case)
    blocks = list(groups.values()); rng = np.random.default_rng(42)
    samples = defaultdict(list)
    for _ in range(1000):
        chosen = [case for index in rng.integers(0, len(blocks), len(blocks)) for case in blocks[index]]
        positive = [c for c in chosen if c['positive']]
        normal = [c for c in chosen if not c['positive']]
        for key, value in {'positive_dice': np.mean([c['dice'] for c in positive]),
                           'case_sensitivity': np.mean([c['prediction_present'] for c in positive]),
                           'normal_fpr': np.mean([c['prediction_present'] for c in normal]),
                           'normal_specificity': np.mean([not c['prediction_present'] for c in normal])}.items():
            samples[key].append(float(value))
    ci = {key: np.quantile(value, [.025, .975]).tolist() for key,value in samples.items()}
    assert not any(c['prediction_present'] for c in cases), 'These failure panels require exactly empty saved masks'
    ci['region_recall_iou_0.10'] = [0., 0.]
    ci['region_recall_iou_0.50'] = [0., 0.]
    (out/'confidence_intervals.json').write_text(json.dumps({'replicates':1000, 'seed':42, 'sampling_unit':'exact duplicate group',
        'intervals':ci, 'limitation':'Degenerate zero-event bootstrap intervals do not establish zero population risk. Patient independence is unknown.'},indent=2))
    (out/'table_reproduction.json').write_text(json.dumps({'passed':True,'source':'saved integer counts','reproduced_metrics':reproduced},indent=2))
    with (out/'subgroups.csv').open('w',newline='') as handle:
        writer=csv.writer(handle); writer.writerow(['subgroup','positive_n','normal_n','positive_Dice','case_sensitivity','normal_FPR'])
        for name,metrics in measured['subgroups'].items():
            writer.writerow([name,metrics['n_positive'],metrics['n_normal'],metrics['mean_positive_dice'],metrics['case_sensitivity'],metrics['normal_false_positive_rate']])
    comparisons=json.loads((out/'comparison.json').read_text())
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="440" viewBox="0 0 900 440">',
         '<rect width="900" height="440" fill="white"/>',
         '<text x="40" y="30" font-family="Arial" font-size="20">Completed epoch-1 validation: threshold sweep (all regions)</text>',
         '<path d="M70 70V350H850" fill="none" stroke="#222"/>']
    for value in [0,.25,.5,.75,1]:
        y=350-value*280; svg.append(f'<text x="25" y="{y+5}" font-family="Arial" font-size="14">{value}</text>')
    for metric,color,label in [('mean_positive_dice','#2563eb','Positive Dice'),('normal_false_positive_rate','#dc2626','Normal false-positive rate')]:
        points=[]
        for i in range(1,20):
            t=round(i*.05,2); v=comparisons[f'{t:.2f}/all'][metric]
            points.append(f'{70+(t-.05)/.9*780:.1f},{350-v*280:.1f}')
        svg.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="3"/>')
        svg.append(f'<text x="{80 if color=="#2563eb" else 300}" y="415" fill="{color}" font-family="Arial">{label}</text>')
    for t in [.05,.25,.5,.75,.95]:
        svg.append(f'<text x="{70+(t-.05)/.9*780-10:.1f}" y="375" font-family="Arial">{t}</text>')
    svg.append('<text x="420" y="397" font-family="Arial">Probability threshold</text></svg>')
    (out/'threshold_sweep.svg').write_text('\n'.join(svg))
    positive=[c for c in cases if c['positive']]
    chosen=[max(positive,key=lambda c:len(rows[c['image_id']]['annotation_ids'])),
            min(positive,key=lambda c:rows[c['image_id']]['mask_pixels']),
            sorted(positive,key=lambda c:rows[c['image_id']]['mask_pixels'])[len(positive)//2],
            next(c for c in cases if not c['positive'])]
    canvas=Image.new('RGB',(1200,1840),'#f1f5f9'); draw=ImageDraw.Draw(canvas)
    try: font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',19)
    except OSError: font=ImageFont.load_default()
    with zipfile.ZipFile(ROOT/'FracAtlas.zip') as z:
        annotations={a['id']:a for a in json.loads(z.read('FracAtlas/Annotations/COCO JSON/COCO_fracture_masks.json'))['annotations']}
        for i,case in enumerate(chosen):
            row=rows[case['image_id']]; image,gt=native_pair(z,row,annotations)
            native=cv2.cvtColor(image,cv2.COLOR_GRAY2RGB)
            truth=native.copy(); truth[gt.astype(bool)]=(truth[gt.astype(bool)]*.5+np.array([0,255,100])*.5).astype(np.uint8)
            y=i*460
            draw.text((15,y+4),f"{row['image_id']} | {image.shape[1]} x {image.shape[0]} | {len(row['annotation_ids'])} GT regions | {'FALSE NEGATIVE' if case['positive'] else 'normal: no predicted region'}",fill='#0f172a',font=font)
            for j,(array,title) in enumerate([(native,'Original'),(truth,'Ground truth (green)'),(native,'Prediction: EMPTY')]):
                panel=Image.fromarray(array); panel.thumbnail((380,370)); x=j*400
                draw.rectangle((x+10,y+65,x+390,y+445),fill='black')
                canvas.paste(panel,(x+10+(380-panel.width)//2,y+65+(380-panel.height)//2))
                draw.text((x+15,y+34),title,fill='#0f172a',font=font)
    canvas.save(out/'development_failure_panels.png')
    report=f'''# Phase 6 development evaluation — 6 October 2026

Executed a complete **validation-only** evaluation of a copied completed E2 epoch-1 checkpoint, SHA `{json.loads((out/'config.json').read_text())['checkpoint_sha256']}`. E2 continues training; the diagnostic uses v1 with seven contradictory training images. Validation is unchanged between v1 and v2. This is not the final selected model, a matched finalist comparison, or an independent test result.

| Measured outcome | Result |
|---|---:|
| Validation positives / normals | 110 / 502 |
| Positive Dice / IoU | 0 / 0 |
| Case TP / FN / FP / TN | 0 / 110 / 0 / 502 |
| Sensitivity / specificity | 0% / 100% |
| Pixel and case precision | Undefined (no predictions) |
| Annotated regions matched, IoU 0.10 / 0.50 | 0 / 137 at both |
| Warm forward median / p95 | {measured['timing']['forward_median_ms']:.1f} / {measured['timing']['forward_p95_ms']:.1f} ms |

19 thresholds × all/largest/min16 policies were evaluated. Here min16 is the legacy 256-grid component filter, not the new pipeline's native-area filter. The best admissible setting was 0.10/all with zero Dice; it is **not adopted**. The false-positive and sensitivity margins compared against 0.50/all are validation rules, not evidence of utility. The normal specificity is achieved by predicting background everywhere; it does not make this a useful model. No successful positive examples exist for this checkpoint, so none are presented.

`per_case.csv` records exact native integer TP/FP/FN counts. `subgroups.csv` reports anatomy/view/hardware/multiscan subsets. `table_reproduction.json` independently recomputes saved metrics. `confidence_intervals.json` uses 1,000 exact-group resamples with seed 42. All-zero endpoints give degenerate intervals; they do not establish zero population error. Patient independence remains unknown. Region matching maximizes cardinality then IoU with one-to-one assignment. Dice excludes empty ground truth; undefined precision remains null.

Timing is CPU-only and concurrent with E2. It is not an isolated performance benchmark. The elapsed evaluation time includes the actual session/runtime conditions; use measured forward timings for per-image inference. No AUROC, clinical accuracy, clinical severity, or approved clinical workflow is claimed. Geometry tiers remain heuristic.

Final Phase 6 gates remain: finish training and separately run corrected v2 controlled comparisons; choose/calibrate on validation; freeze the selected checkpoint/preprocessing/postprocessing/code; run the reserved test once; report matched baselines and final region/subgroup CIs; obtain human/teammate review. The final test was not accessed for model evaluation or tuning. GPU remains blocked by Windows Code 43.
'''
    (out/'PHASE6_REPORT.md').write_text(report,encoding='utf-8')
    print('Exact tables, clustered confidence intervals, threshold plot and failure panels generated.')

if __name__=='__main__': main()
