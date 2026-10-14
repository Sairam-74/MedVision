"""All three retained native-review columns; no inference or annotation changes."""
import json
from pathlib import Path
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
audit=ROOT/'experiments/AI_AUDIT_E6_v3'
out=ROOT/'experiments/session_20261007_ai_loop_01/E6_remaining_segmentation_sheets'
out.mkdir()
reviewed={'IMG0000144.jpg','IMG0000190.jpg','IMG0000319.jpg','IMG0000471.jpg',
          'IMG0000851.jpg','IMG0001041.jpg','IMG0001073.jpg','IMG0001198.jpg'}
all_cases=json.loads((audit/'per_case.json').read_text())
cases=[c for c in all_cases if c['category']=='TP' and c['segmentation_failure_tags'] and c['image_id'] not in reviewed]
index=[]
for start in range(0,len(cases),6):
    sheet=np.zeros((1500,1800,3),np.uint8)
    members=[]
    for j,c in enumerate(cases[start:start+6]):
        panel=cv2.imread(str(audit/c['review_panel']))
        if panel is None or panel.shape[0]!=454 or panel.shape[1]%3:
            raise ValueError('Three-column retained panel required')
        # Preserve original/GT/prediction and caption in their saved left-to-right order.
        scale=min(900/panel.shape[1],450/panel.shape[0])
        small=cv2.resize(panel,(round(panel.shape[1]*scale),round(panel.shape[0]*scale)),interpolation=cv2.INTER_AREA)
        tile=np.zeros((500,900,3),np.uint8)
        label=f"{c['image_id']} Dice={c['dice']:.3f} IoU={c['iou']:.3f}"
        cv2.putText(tile,label,(5,18),cv2.FONT_HERSHEY_SIMPLEX,.5,(255,255,255),1)
        cv2.putText(tile,'Original | annotation (green) | prediction (red)',(5,39),cv2.FONT_HERSHEY_SIMPLEX,.45,(255,255,255),1)
        tile[50:50+small.shape[0],:small.shape[1]]=small
        rr,cc=divmod(j,2);sheet[rr*500:(rr+1)*500,cc*900:(cc+1)*900]=tile
        members.append(dict(image_id=c['image_id'],panel=c['review_panel'],dice=c['dice'],iou=c['iou'],
                            case_score=c['case_score'],tags=c['segmentation_failure_tags']))
    name=f'sheet_{start//6+1:02d}.jpg'
    if not cv2.imwrite(str(out/name),sheet): raise RuntimeError('Sheet write failed')
    index.append(dict(sheet=name,cases=members))
(out/'index.json').write_text(json.dumps(dict(audit=str(audit.relative_to(ROOT)),images=len(cases),sheets=index,
    already_reviewed_ids=sorted(reviewed),scope='Actual retained GT/prediction panels; numeric TP means any mask, not correct location',
    clinical_adjudication=False),indent=2))
print(json.dumps(dict(images=len(cases),sheets=len(index))))
