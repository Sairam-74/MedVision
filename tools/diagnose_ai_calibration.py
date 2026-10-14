"""Shadow calibration experiment; never changes serving or tunes from test data."""
import json
from pathlib import Path
import sys
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.ai_metrics import calibration, classification
from tools.evaluate_ai_baseline import save, sha


def main():
    out=ROOT/'experiments/AI_CALIBRATION_DIAGNOSTIC_20261007'
    if out.exists():raise ValueError('Never overwrite an experiment')
    baseline=ROOT/'experiments/AI_BASELINE_20261007_v1'
    rows=json.loads((ROOT/'experiments/data_v3_reliability_20261007/manifest.json').read_text())['rows']
    cases={c['image_id']:c for c in json.loads((baseline/'per_case.json').read_text())}
    fit=[cases[r['image_id']] for r in rows if r['split']=='calibration']
    val=[cases[r['image_id']] for r in rows if r['split']=='val']
    if {c['group'] for c in fit} & {c['group'] for c in val}:raise ValueError('Calibration leakage')
    # Predeclared regularized sigmoid mapping of the existing proxy only.
    model=LogisticRegression(C=1.,solver='lbfgs',max_iter=1000,random_state=42)
    model.fit(np.array([c['case_score'] for c in fit])[:,None],[int(c['positive']) for c in fit])
    predicted=model.predict_proba(np.array([c['case_score'] for c in val])[:,None])[:,1]
    mapped=[dict(c,case_score=float(p)) for c,p in zip(val,predicted)]
    raw,after=calibration(val),calibration(mapped)
    prevalence=float(np.mean([c['positive'] for c in fit]))
    constant_brier=float(brier_score_loss([c['positive'] for c in val],np.full(len(val),prevalence)))
    result=dict(scope='Historical model shadow diagnostic ONLY; fitting calibration149, evaluating validation463, disjoint duplicate groups. Original checkpoint exposure unknown; no independent clinical calibration claim.',
                fit_n=len(fit),eval_n=len(val),fit_groups=len({c['group'] for c in fit}),eval_groups=len({c['group'] for c in val}),
                model='Regularized logistic sigmoid mapping a*max-pixel-score+b, C=1 fixed, no test tuning',
                coefficients=dict(a=float(model.coef_[0,0]),b=float(model.intercept_[0])),
                baseline=raw,calibrated=after,constant_prevalence_brier=constant_brier,calibration_prevalence=prevalence,
                raw_classification=classification(val),mapped_ranking=classification(mapped),
                mask_and_case_decision_unchanged=True,production_modified=False,test_images_read=0,
                decision='REJECT calibration as a sufficient detection/segmentation fix; archival research artifact only. A lower Brier/ECE can largely reflect prevalence while errors and localization remain unchanged.',
                baseline_metrics_sha256=sha(baseline/'metrics.json'),manifest_sha256=sha(ROOT/'experiments/data_v3_reliability_20261007/manifest.json'),source_sha256=sha(__file__))
    out.mkdir();save(out/'metrics.json',result)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(6,5));ax.plot([0,1],[0,1],'--',color='gray')
    for label,data in [('Raw proxy',raw),('Sigmoid-mapped proxy',after)]:
        bins=[b for b in data['reliability_curve'] if b['n']]
        ax.scatter([b['mean_score'] for b in bins],[b['observed_fracture_fraction'] for b in bins],label=label)
    ax.set(xlim=(0,1),ylim=(0,1),xlabel='Case-score proxy',ylabel='Observed fracture fraction',title='Shadow calibration: unchanged errors');ax.legend();fig.tight_layout();fig.savefig(out/'reliability_comparison.png',dpi=160);plt.close(fig)
    (out/'CALIBRATION_DIAGNOSTIC.md').write_text(f'''# Calibration diagnostic — not a detection improvement

Fit sigmoid mapping using149 calibration cases only; assess463 separate validation cases. No test inference or application change. Original model exposure remains unknown.

Raw max-pixel Brier {raw['brier_score']:.6f} -> mapped {after['brier_score']:.6f}; ECE {raw['expected_calibration_error']:.6f} -> {after['expected_calibration_error']:.6f}. Calibration-prevalence-only Brier {constant_brier:.6f}. The prevalence-only comparator is essential: a numerically better calibration score does not establish useful discrimination.

All masks, case predictions, false positives and false negatives remain unchanged. No accuracy, recall, specificity, localization or Dice improvement is attributed to this mapping. Mapping is NOT served. REJECT it as a sufficient reliability improvement. Continue targeted negative-supervision comparison and later independent calibration of an accepted fresh model.

Full fit parameters, denominators, raw/mapped ranking metrics and lineage: metrics.json. Equal-width10-bin ECE is sensitive to binning/sample size. This is neither external nor clinical validation.
''')
    save(out/'completion.json',dict(status='completed_shadow_diagnostic',test_images_read=0,production_modified=False))
    print(json.dumps(dict(raw_brier=raw['brier_score'],mapped_brier=after['brier_score'],constant_brier=constant_brier,raw_ece=raw['expected_calibration_error'],mapped_ece=after['expected_calibration_error'],decision=result['decision']),indent=2))


if __name__=='__main__':main()
