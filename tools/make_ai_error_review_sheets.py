"""Contact sheets of already retained validation panels; no inference or relabeling."""
import argparse
import json
from pathlib import Path
import cv2
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit', required=True)
    parser.add_argument('--category', choices=['FP', 'FN', 'TP'], required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    audit, out = Path(args.audit).resolve(), Path(args.out).resolve()
    if root not in audit.parents or root not in out.parents or out.exists():
        raise ValueError('Existing audit and exclusive workspace review output required')
    if not (audit/'completion.json').exists():
        raise ValueError('Full audit required')
    cases = [c for c in json.loads((audit/'per_case.json').read_text())
             if c['category'] == args.category and c.get('review_panel')]
    out.mkdir()
    index = []
    for start in range(0, len(cases), 9):
        sheet = np.zeros((3*500, 3*614, 3), np.uint8)
        members = []
        for j, case in enumerate(cases[start:start+9]):
            panel = cv2.imread(str(audit/case['review_panel']))
            if panel is None or panel.shape[1] % 3 or panel.shape[0] != 454:
                raise ValueError('Unexpected saved three-column panel geometry')
            # Original and predicted overlay; ground truth remains in linked full panel.
            width = panel.shape[1]//3
            pair = np.concatenate([panel[70:, :width], panel[70:, 2*width:]], axis=1)
            tile = np.zeros((500, 614, 3), np.uint8)
            scale = min(614/pair.shape[1], 455/pair.shape[0])
            small = cv2.resize(pair, (round(pair.shape[1]*scale), round(pair.shape[0]*scale)), interpolation=cv2.INTER_AREA)
            tile[45:45+small.shape[0], :small.shape[1]] = small
            label = f"{case['image_id']} {case['category']} score={case['case_score']:.4f}"
            cv2.putText(tile, label, (5, 18), cv2.FONT_HERSHEY_SIMPLEX, .45, (255,255,255), 1)
            cv2.putText(tile, 'Original | unfiltered predicted mask', (5, 37), cv2.FONT_HERSHEY_SIMPLEX, .45, (255,255,255), 1)
            rr, cc = divmod(j, 3)
            sheet[rr*500:(rr+1)*500, cc*614:(cc+1)*614] = tile
            members.append(dict(image_id=case['image_id'], panel=case['review_panel'], case_score=case['case_score']))
        name = f"sheet_{start//9+1:02d}.jpg"
        if not cv2.imwrite(str(out/name), sheet):
            raise RuntimeError('Sheet write failed')
        index.append(dict(sheet=name, cases=members))
    (out/'index.json').write_text(json.dumps(dict(audit=str(audit.relative_to(root)), category=args.category,
        images=len(cases), sheets=index, inference_performed=False, clinical_adjudication=False), indent=2))
    print(json.dumps(dict(images=len(cases), sheets=len(index))))


if __name__ == '__main__':
    main()
