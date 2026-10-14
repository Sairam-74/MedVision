"""Real two-training-image memorization check, not generalization evidence."""
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time
import cv2
import numpy as np
import torch
from PIL import Image, ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import medvision_pipeline as p


def main():
    out=Path('experiments/P4_overfit_128')
    if out.exists(): raise ValueError('Choose a new run rather than overwrite')
    out.mkdir(parents=True)
    torch.set_num_threads(2); cv2.setNumThreads(1); p.seed_everything(42)
    preprocess=p.PreprocessConfig(size=128,clahe=True)
    dataset=p.FracDataset('FracAtlas.zip','experiments/data_v2/manifest.json','train',preprocess)
    pos=max((i for i,r in enumerate(dataset.rows) if int(r['fractured'])),key=lambda i:dataset.rows[i]['mask_pixels']/(dataset.rows[i]['width']*dataset.rows[i]['height']))
    neg=next(i for i,r in enumerate(dataset.rows) if not int(r['fractured']))
    examples=[dataset[i] for i in (pos,neg)]
    x,y,v=[torch.stack([example[k] for example in examples]) for k in range(3)]
    model=p.LogitsAttentionUNet()
    optimizer=torch.optim.Adam(model.parameters(),lr=1e-3)
    config=dict(seed=42,train_ids=[dataset.rows[i]['image_id'] for i in (pos,neg)],preprocess=asdict(preprocess),
                loss=asdict(p.LossConfig()),augmentation=False,architecture='AttentionUNet64',output_contract=p.CONTRACT,
                lr=.001,max_steps=200,acceptance='fixed .5 grid positive Dice >=.85 and zero predicted normal pixels',
                source_hashes={name:p.sha(name) for name in ['medvision_pipeline.py','tools/overfit_pipeline.py']},
                manifest_sha256=p.sha('experiments/data_v2/manifest.json'),scope='train-only memorization sanity; not performance')
    (out/'config.json').write_text(json.dumps(config,indent=2))
    logs=[]; started=time.perf_counter(); success=False
    for step in range(201):
        if step%20==0:
            model.eval()
            with torch.inference_mode():
                logits=model(x); loss=p.loss_components(logits,y,v,p.LossConfig())
                masks=(logits.sigmoid()>=.5)*v.bool()
                tp=int((masks[0]&y[0].bool()).sum()); fp=int((masks[0]&~y[0].bool()).sum()); fn=int((~masks[0]&y[0].bool()).sum())
                dice=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.
                normal_pixels=int(masks[1].sum())
                log=dict(step=step,loss_components={key:float(value) for key,value in loss.items()},
                         positive_grid_dice=dice,normal_grid_predicted_pixels=normal_pixels,
                         elapsed_seconds=time.perf_counter()-started)
                logs.append(log); print(json.dumps(log),flush=True)
                (out/'progress.json').write_text(json.dumps(log,indent=2))
                success=dice>=.85 and normal_pixels==0
                if success: break
        if step==200: break
        model.train(); optimizer.zero_grad(set_to_none=True)
        loss=p.loss_components(model(x),y,v,p.LossConfig())['total']
        if not torch.isfinite(loss): raise RuntimeError('Nonfinite overfit loss')
        loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),10,error_if_nonfinite=True); optimizer.step()
    torch.save(model.state_dict(),out/'model.pt')
    (out/'steps.json').write_text(json.dumps(logs,indent=2))
    (out/'result.json').write_text(json.dumps(dict(acceptance_passed=success,final=logs[-1],test_evaluated=False,
                                                 original_checkpoint_sha256=p.sha('best_model.pt'),
                                                 note='Two deliberately easy training cases; not a validation/generalization score'),indent=2))
    bundle=dict(output_contract=p.CONTRACT,architecture='AttentionUNet64',checkpoint='model.pt',checkpoint_sha256=p.sha(out/'model.pt'),
                preprocess=asdict(preprocess),postprocess=asdict(p.PostprocessConfig()),
                calibration_status='MEMORIZATION SANITY ONLY; not a selected or calibrated model')
    (out/'bundle.json').write_text(json.dumps(bundle,indent=2))
    sheet=Image.new('RGB',(1200,700),'white'); draw=ImageDraw.Draw(sheet)
    for k,i in enumerate((pos,neg)):
        image,mask=dataset.native(i)
        _,_,pred,_=p.predict_arrays(model,image,preprocess,p.PostprocessConfig())
        for j,region in enumerate((mask,pred)):
            visual=cv2.cvtColor(image,cv2.COLOR_GRAY2RGB)
            visual[region.astype(bool)]=(visual[region.astype(bool)]*.5+np.array([127,0,0])).astype(np.uint8)
            im=Image.fromarray(visual); im.thumbnail((580,310)); sheet.paste(im,(j*600+(600-im.width)//2,k*350+35))
            draw.text((j*600+5,k*350+5),f'{dataset.rows[i]["image_id"]}: {"target" if j==0 else "prediction"}',fill='black')
    sheet.save(out/'native_overfit_examples.png')
    print(json.dumps({'acceptance_passed':success,'steps':logs[-1]['step']}))


if __name__=='__main__':
    main()
