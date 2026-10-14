"""Retained native panels for presence-alert FP and head/mask disagreements.

Sheet creation is not a visual review. Human/agent observations must be saved
separately after actually viewing the images. No inference or label edits.
"""
import argparse
import json
from pathlib import Path
import sys
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.ai_atomic_io import json_atomic
from tools.evaluate_ai_baseline import sha


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--audit',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--selection',choices=['normal_alerts','head_mask_disagreements'],required=True)
    ap.add_argument('--exclude-reviewed-directory',action='append',default=[])
    args=ap.parse_args()
    audit,out=Path(args.audit).resolve(),Path(args.out).resolve()
    if ROOT not in audit.parents or ROOT not in out.parents or out.exists():
        raise ValueError('Completed workspace native audit and exclusive output required')
    if not (audit/'completion.json').exists(): raise ValueError('Full native audit required')
    cases=json.loads((audit/'per_case.json').read_text())
    if args.selection=='normal_alerts':
        selected=[c for c in cases if not c['positive'] and c['review_alert_present']]
        count,columns,tile_w,tile_h=9,3,614,500
    else:
        selected=[c for c in cases if c['classifier_prediction_present'] is not None and c['classifier_prediction_present']!=c['prediction_present']]
        count,columns,tile_w,tile_h=6,2,900,500
    total_selected=len(selected);excluded=set();excluded_directories=[]
    for folder in args.exclude_reviewed_directory:
        directory=Path(folder).resolve()
        if ROOT not in directory.parents: raise ValueError('Workspace actual review required')
        completion=json.loads((directory/'completion.json').read_text())
        if not completion['status'].startswith('completed_actual_native') or completion['audit']!=str(audit.relative_to(ROOT)):
            raise ValueError('Completed actual review of same native audit required')
        reviewed_path=directory/'per_case_visual_review.json'
        if sha(reviewed_path)!=completion['per_case_review_sha256']: raise ValueError('Actual review record changed')
        for row in json.loads(reviewed_path.read_text()):
            if sha(audit/row['panel'])!=row['panel_sha256']: raise ValueError('Actual reviewed native panel changed')
            excluded.add(row['image_id'])
        excluded_directories.append(str(directory.relative_to(ROOT)))
    previous=sorted(excluded&{c['image_id'] for c in selected})
    selected=[c for c in selected if c['image_id'] not in excluded]
    out.mkdir();index=[]
    for start in range(0,len(selected),count):
        sheet=np.zeros((3*tile_h,columns*tile_w,3),np.uint8);members=[]
        for j,c in enumerate(selected[start:start+count]):
            if not c.get('review_panel'): raise ValueError('Actual retained panel required')
            source=audit/c['review_panel'];panel=cv2.imread(str(source))
            if panel is None or panel.shape[0]!=454 or panel.shape[1]%3:
                raise ValueError('Complete three-column native panel required')
            if args.selection=='normal_alerts':
                w=panel.shape[1]//3
                displayed=np.concatenate([panel[70:,:w],panel[70:,2*w:]],axis=1)
                caption='Original | independent predicted mask'
            else:
                displayed=panel;caption='Original | reference (green) | independent mask (red)'
            scale=min(tile_w/displayed.shape[1],445/displayed.shape[0])
            small=cv2.resize(displayed,(round(displayed.shape[1]*scale),round(displayed.shape[0]*scale)),interpolation=cv2.INTER_AREA)
            tile=np.zeros((tile_h,tile_w,3),np.uint8)
            head='NA' if c['head_score'] is None else f"{c['head_score']:.3f}"
            cv2.putText(tile,f"{c['image_id']} mask{c['category']} alert{c['review_alert_category']} head={head}",(5,18),cv2.FONT_HERSHEY_SIMPLEX,.43,(255,255,255),1)
            cv2.putText(tile,caption,(5,37),cv2.FONT_HERSHEY_SIMPLEX,.42,(255,255,255),1)
            tile[50:50+small.shape[0],:small.shape[1]]=small
            rr,cc=divmod(j,columns);sheet[rr*tile_h:(rr+1)*tile_h,cc*tile_w:(cc+1)*tile_w]=tile
            members.append(dict(image_id=c['image_id'],positive=c['positive'],mask_category=c['category'],
                alert_category=c['review_alert_category'],head_mask_group=c['head_mask_group'],head_score=c['head_score'],
                panel=c['review_panel'],panel_sha256=sha(source),dice=c['dice'],iou=c['iou']))
        name=f'sheet_{start//count+1:02d}.jpg'
        if not cv2.imwrite(str(out/name),sheet): raise RuntimeError('Sheet write failed')
        index.append(dict(sheet=name,cases=members))
    json_atomic(out/'index.json',dict(audit=str(audit.relative_to(ROOT)),selection=args.selection,images=len(selected),sheets=index,
        total_selected_cases=total_selected,previously_reviewed_selected_ids=previous,
        excluded_review_directories=excluded_directories,
        source_sha256=sha(__file__),inference_performed=False,clinical_adjudication=False,
        visual_review_completed=False,scope='All selected actual retained native panels, including classifier-only normal alerts'))
    print(json.dumps(dict(images=len(selected),sheets=len(index),visual_review_completed=False)))


if __name__=='__main__': main()
