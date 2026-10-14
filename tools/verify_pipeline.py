"""Meaningful Phase 4 geometry/loss/data/contract checks; no test predictions."""
from dataclasses import asdict
import json
from pathlib import Path
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw
import torch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import medvision_pipeline as p


def main():
    out=Path('experiments/phase4_checks')
    out.mkdir(parents=True,exist_ok=True)
    cv2.setNumThreads(1)
    torch.set_num_threads(2)
    p.seed_everything(42)
    checks={}
    image=np.full((320,640),120,np.uint8)
    target=np.zeros(image.shape,np.uint8)
    target[80:160,100:300]=1
    target[200:280,400:520]=1
    pc=p.PreprocessConfig(size=128,clahe=False)
    x,y,v,g=p.prepare(image,pc,target)
    restored=p.inverse(y,g).astype(bool)
    iou=float(np.sum(restored&target.astype(bool))/np.sum(restored|target.astype(bool)))
    assert iou>.98 and g.top==32 and g.left==0 and not v[:32].any()
    assert np.isin(y,[0,1]).all() and np.array_equal(p.inverse(v,g),np.ones(image.shape))
    checks['letterbox_roundtrip']={'iou':iou,'geometry':asdict(g),'padding_valid_pixels':int(v.sum())}
    parameter_cases=[]
    for resize in ('letterbox','stretch'):
        for normalization in ('unit','zscore'):
            config=p.PreprocessConfig(size=256,resize=resize,clahe=True,blur_kernel=3,normalization=normalization)
            pixels=np.arange(320*640,dtype=np.uint8).reshape(320,640)
            xx,yy,vv,_=p.prepare(pixels,config,target)
            assert np.isfinite(xx).all() and xx.shape==(256,256) and not xx[vv==0].any()
            assert np.isin(yy,[0,1]).all()
            if normalization=='zscore': assert abs(float(xx[vv.astype(bool)].mean()))<1e-5
            parameter_cases.append(asdict(config))
    checks['preprocessing_parameters']=parameter_cases
    polygon=p.legacy._rasterize_coco_segmentation([[10,10,30,10,30,30,10,30],[70,70,80,70,80,80,70,80]],100,100)
    assert polygon[20,20] and polygon[75,75] and not polygon[50,50]
    checks['polygon_instances_union']='pass'
    probability=np.zeros((40,40),np.float32)
    probability[3,3]=1
    probability[10:20,15]=1
    probability[25:30,25:30]=1
    raw,delivered=p.postprocess(probability,p.PostprocessConfig())
    assert delivered.sum()==36 and cv2.connectedComponents(delivered,8)[0]-1==3
    assert p.postprocess(probability,p.PostprocessConfig(policy='largest'))[1].sum()==25
    assert p.postprocess(probability,p.PostprocessConfig(policy='min_pixels',min_pixels=10))[1].sum()==35
    assert not p.postprocess(np.zeros((40,40),np.float32),p.PostprocessConfig())[1].any()
    checks['empty_single_thin_multiple_components']='pass; native all/largest/min_pixels'
    loss_results={}
    for mode in ('bce_dice','focal_tversky','unified_focal_symmetric'):
        for case in ('empty','full','thin','multiple','extreme_negative','extreme_positive'):
            truth=torch.zeros((2,1,16,16))
            if case=='full': truth[:]=1
            if case=='thin': truth[:,:,8,3:13]=1
            if case=='multiple': truth[:,:,2:5,2:5]=1; truth[:,:,10:14,10:14]=1
            logits=torch.full_like(truth,-100. if case=='extreme_negative' else 100. if case=='extreme_positive' else .3,requires_grad=True)
            valid=torch.ones_like(truth); valid[:,:,:2]=0
            values=p.loss_components(logits,truth,valid,p.LossConfig(mode=mode))
            values['total'].backward()
            assert all(torch.isfinite(t) for t in values.values()) and torch.isfinite(logits.grad).all(), (mode,case)
            assert not logits.grad[:,:,:2].any()
            alternate=logits.detach().clone(); alternate[:,:,:2]=999
            assert torch.allclose(values['total'].detach(),p.loss_components(alternate,truth,valid,p.LossConfig(mode=mode))['total'])
            loss_results[mode+'/'+case]={'loss':float(values['total'].detach()),'gradient_norm':float(logits.grad.norm())}
    checks['loss_finite_gradients_and_padding_exclusion']=loss_results
    # Independent numpy calculation of author's two-class symmetric UF convention.
    logits=torch.tensor([[[[-.8,.2],[1.1,-1.3]]]])
    truth=torch.tensor([[[[0.,1.],[1.,0.]]]])
    valid=torch.ones_like(truth)
    config=p.LossConfig(mode='unified_focal_symmetric')
    prob=1/(1+np.exp(-logits.numpy().astype(np.float64)))
    yy=truth.numpy().astype(np.float64)
    ce=np.mean(-config.delta*yy*(1-prob)**config.unified_gamma*np.log(prob)
               -(1-config.delta)*(1-yy)*prob**config.unified_gamma*np.log(1-prob))
    losses=[]
    for pp,tt in [(prob,yy),(1-prob,1-yy)]:
        tp=float((pp*tt).sum()); fn=float(((1-pp)*tt).sum()); fp=float((pp*(1-tt)).sum())
        ti=(tp+config.smooth)/(tp+config.delta*fn+(1-config.delta)*fp+config.smooth)
        losses.append((1-ti)**(1-config.unified_gamma))
    expected=config.unified_weight*ce+(1-config.unified_weight)*np.mean(losses)
    actual=float(p.loss_components(logits,truth,valid,config)['total'])
    assert abs(actual-expected)<1e-6
    checks['unified_focal_independent_reference']={'numpy':expected,'torch':actual}
    training=p.FracDataset('FracAtlas.zip','experiments/data_v2/manifest.json','train',p.PreprocessConfig(),True)
    training.epoch=1
    aa=training[0]; np.random.seed(123); np.random.normal(size=100); bb=training[0]
    assert all(torch.equal(a,b) for a,b in zip(aa,bb))
    ids1=list(training.sampler(.5,1)); ids2=list(training.sampler(.5,1))
    assert ids1==ids2
    sampled_positive=sum(int(training.rows[i]['fractured']) for i in ids1)/len(ids1)
    assert abs(sampled_positive-.5)<.04
    checks['seeded_sampler_and_augmentation']={'sampled_positive_fraction':sampled_positive,'images':len(ids1),'seed':42,'epoch':1}
    val=p.FracDataset('FracAtlas.zip','experiments/data_v2/manifest.json','val',p.PreprocessConfig())
    try: val.sampler(.5,1)
    except ValueError: pass
    else: raise AssertionError('Validation resampling was accepted')
    checks['validation_sampling_guard']='pass'
    # Structural survival audit of annotation masks at each candidate geometry.
    # Includes test targets solely for data integrity, never predictions/tuning.
    survival={}
    import zipfile
    manifest=json.loads(Path('experiments/data_v2/manifest.json').read_text())
    for size in (256,512):
        lost_instances=[]; lost_unions=[]; minimum=None
        for row in manifest['rows']:
            if not int(row['fractured']): continue
            geom=p.geometry((row['height'],row['width']),p.PreprocessConfig(size=size))
            union=np.zeros((row['height'],row['width']),np.uint8)
            for aid in row['annotation_ids']:
                instance=p.legacy._rasterize_coco_segmentation(training.annotations[aid]['segmentation'],row['width'],row['height'])
                small=p.project(instance,geom,cv2.INTER_NEAREST)
                if not small.any(): lost_instances.append({'image_id':row['image_id'],'annotation_id':aid})
                union |= instance
            small=p.project(union,geom,cv2.INTER_NEAREST)
            if not small.any(): lost_unions.append(row['image_id'])
            pixels=int(small.sum()); minimum=pixels if minimum is None else min(minimum,pixels)
        survival[str(size)]={'lost_instances':lost_instances,'lost_positive_unions':lost_unions,'minimum_union_pixels':minimum,
                             'positive_images':714,'annotation_instances':919,'scope':'data integrity only; no test model predictions'}
    checks['letterbox_annotation_survival']=survival
    chosen=[next(i for i,r in enumerate(training.rows) if int(r['fracture_count'])>=3),
            next(i for i,r in enumerate(training.rows) if int(r['hardware']) and int(r['fractured'])),
            next(i for i,r in enumerate(training.rows) if not int(r['fractured']))]
    sheet=Image.new('RGB',(1200,900),'white'); draw=ImageDraw.Draw(sheet)
    selection=[]
    for k,index in enumerate(chosen):
        image,mask=training.native(index)
        xx,yy,vv,_=p.prepare(image,training.config,mask)
        selection.append(training.rows[index]['image_id'])
        for j,mode in enumerate(('unaugmented','conservative','elastic_candidate')):
            ax,ay,av=(xx,yy,vv) if j==0 else p.augment(xx,yy,vv,44,elastic=j==2)
            visual=np.repeat(np.uint8(np.clip(ax,0,1)*255)[...,None],3,axis=2)
            visual[ay.astype(bool)]=(visual[ay.astype(bool)]*.5+np.array([127,0,0])).astype(np.uint8)
            sheet.paste(Image.fromarray(visual).resize((256,256)),(j*400+70,k*300+35))
            draw.text((j*400+5,k*300+5),f'{training.rows[index]["image_id"]} {mode}',fill='black')
            assert np.isin(ay,[0,1]).all() and not ay[av==0].any()
    sheet.save(out/'augmentation_review.png')
    checks['augmentation_examples']={'train_ids':selection,'seed':44,'elastic':'optional and disabled by default; requires clinical plausibility review'}
    (out/'checks.json').write_text(json.dumps(checks,indent=2))
    print(json.dumps({'checks':'PASS','letterbox_survival':survival,'sampled_positive_fraction':sampled_positive},indent=2))


if __name__=='__main__':
    main()
