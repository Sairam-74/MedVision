"""Record seven E8 native panels actually viewed, before full audit completion."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.ai_atomic_io import json_atomic
from tools.evaluate_ai_baseline import sha

panels=[
('TP_IMG0000144.jpg','Elbow annotation in broad upper-limb field completely missed; predicted wrist patch has zero GT overlap. Classifier positive and image alert positive do not establish localization success.'),
('FN_IMG0000190.jpg','Proximal-humerus/shoulder annotation; no independent mask. Classifier score about0.827 recovers the case alert but not fracture localization.'),
('FP_IMG0000201.jpg','Source-normal ankle with visible medial fixation wire/screws; false predicted patches on distal fibula/ankle. Hardware association visible, causal explanation unadjudicated.'),
('FN_IMG0000471.jpg','Anterior-knee/patellar-region annotation with visible fixation loops; no mask and classifier score about0.084. Both outputs miss this source-positive case.'),
('TP_IMG0000851.jpg','Wrist annotation only partly covered; separate small little-finger/metacarpal annotation missed. Classifier positive, but multi-annotation coverage incomplete.'),
('TN_IMG0000902.jpg','Source-normal shoulder/upper-arm image has no independent mask, but classifier score about0.710 produces a false case alert. No specific erroneous fracture region is offered.'),
('TP_IMG0000019.jpg','Distal-radius/wrist annotation substantially overlaps prediction, with broader extra red area and differing outline; positive classifier and mask agree on case but not exact annotation boundary.')]

def main():
    session=ROOT/'experiments/session_20261007_ai_loop_01';dest=session/'E8_EARLY_NATIVE_PANEL_REVIEW.json'
    if dest.exists(): raise ValueError('Actual earlier review record already exists; never overwrite')
    directory=ROOT/'experiments/AI_AUDIT_E8_v3_presence_r2/failures'
    rows=[dict(image_id=Path(name).stem.split('_',1)[1]+'.jpg',panel=name,panel_sha256=sha(directory/name),visual_note=note) for name,note in panels]
    json_atomic(dest,dict(status='actual_early_full_native_panel_review',rows=rows,
        actually_viewed=True,clinical_adjudication=False,new_inference=False,no_label_changes=True,
        scope='Original/reference/prediction native panels; expert clinical fracture subtype and cause not available'))
    print(json.dumps(dict(actual_panels_reviewed=len(rows))))

if __name__=='__main__': main()
