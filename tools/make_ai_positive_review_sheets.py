"""Native original/GT/prediction contact sheets of completed positive-case failures."""
import argparse
import json
from pathlib import Path
import sys
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.evaluate_ai_baseline import sha
from tools.ai_atomic_io import json_atomic


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--audit',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--exclude-reviewed')
    args=ap.parse_args()
    audit,out=Path(args.audit).resolve(),Path(args.out).resolve()
    if ROOT not in audit.parents or ROOT not in out.parents or out.exists():
        raise ValueError('Completed workspace audit and exclusive sheets required')
    if not (audit/'completion.json').exists(): raise ValueError('Full audit must finish first')
    cases=json.loads((audit/'per_case.json').read_text())
    exclude=set()
    if args.exclude_reviewed:
        reviewed_path=Path(args.exclude_reviewed).resolve()
        if ROOT not in reviewed_path.parents: raise ValueError('Workspace actual review record required')
        reviewed=json.loads(reviewed_path.read_text())
        for row in reviewed['rows']:
            panel=audit/'failures'/row['panel']
            if sha(panel)!=row['panel_sha256']: raise ValueError('Previously viewed panel identity changed')
            exclude.add(row['image_id'])
    tagged=[c for c in cases if c['positive'] and c['segmentation_failure_tags']]
    selected=[c for c in tagged if c['image_id'] not in exclude]
    if any(not c.get('review_panel') for c in selected): raise ValueError('Every positive failure requires actual retained panel')
    out.mkdir();index=[]
    for start in range(0,len(selected),6):
        sheet=np.zeros((1500,1800,3),np.uint8);members=[]
        for j,c in enumerate(selected[start:start+6]):
            panel=cv2.imread(str(audit/c['review_panel']))
            if panel is None or panel.shape[0]!=454 or panel.shape[1]%3:
                raise ValueError('Three-column retained panel required')
            scale=min(900/panel.shape[1],450/panel.shape[0])
            small=cv2.resize(panel,(round(panel.shape[1]*scale),round(panel.shape[0]*scale)),interpolation=cv2.INTER_AREA)
            tile=np.zeros((500,900,3),np.uint8)
            label=f"{c['image_id']} {c['category']} Dice={c['dice']:.3f} IoU={c['iou']:.3f}"
            cv2.putText(tile,label,(5,18),cv2.FONT_HERSHEY_SIMPLEX,.5,(255,255,255),1)
            cv2.putText(tile,'Original | annotation (green) | prediction (red)',(5,39),cv2.FONT_HERSHEY_SIMPLEX,.45,(255,255,255),1)
            tile[50:50+small.shape[0],:small.shape[1]]=small
            rr,cc=divmod(j,2);sheet[rr*500:(rr+1)*500,cc*900:(cc+1)*900]=tile
            members.append(dict(image_id=c['image_id'],panel=c['review_panel'],category=c['category'],
                dice=c['dice'],iou=c['iou'],case_score=c['case_score'],tags=c['segmentation_failure_tags']))
        name=f'sheet_{start//6+1:02d}.jpg'
        if not cv2.imwrite(str(out/name),sheet): raise RuntimeError('Sheet write failed')
        index.append(dict(sheet=name,cases=members))
    json_atomic(out/'index.json',dict(audit=str(audit.relative_to(ROOT)),images=len(selected),sheets=index,
        previously_reviewed_tagged_positive_ids=sorted(exclude&{c['image_id'] for c in tagged}),
        total_tagged_positive_cases=len(tagged),source_sha256=sha(__file__),
        scope='Actual complete native original/GT/prediction panels; image-positive does not prove correct localization',
        inference_performed=False,clinical_adjudication=False))
    print(json.dumps(dict(images=len(selected),sheets=len(index),tagged_positive_total=len(tagged))))


if __name__=='__main__': main()
