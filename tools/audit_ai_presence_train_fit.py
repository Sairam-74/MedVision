"""Full unaugmented TRAIN fit of a completed selected presence candidate only."""
import os
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time
import cv2
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import medvision_pipeline as p
from tools import ai_metrics as a
from tools.ai_cached_dataset import CachedReliabilityDataset
from tools.ai_presence_model import PresenceAttentionUNet,CONTRACT,review_group,tensor_digest
from tools.audit_ai_learning_fit import grid_case
from tools.ai_atomic_io import json_atomic


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--run',required=True);ap.add_argument('--out',required=True)
    args=ap.parse_args()
    run,out=Path(args.run).resolve(),Path(args.out).resolve()
    if ROOT not in run.parents or ROOT not in out.parents or out.exists():
        raise ValueError('Completed workspace run and exclusive diagnostic required')
    state=json.loads((run/'state.json').read_text());config=json.loads((run/'config.json').read_text())
    bundle=json.loads((run/'bundle.json').read_text())
    if state['status']!='completed' or state['epochs_finished']!=12 or state['smoke'] or bundle['output_contract']!=CONTRACT:
        raise ValueError('Full registered run required; do not diagnose unfinished best weights')
    for source,digest in config['source_hashes'].items():
        if p.sha(ROOT/source)!=digest: raise ValueError('Training source changed: '+source)
    checkpoint=run/'best_model.pt';manifest=ROOT/config['manifest']
    if p.sha(checkpoint)!=bundle['checkpoint_sha256'] or p.sha(manifest)!=config['manifest_sha256']:
        raise ValueError('Checkpoint/data identity changed')
    if not torch.cuda.is_available(): raise ValueError('CUDA required for this registered read-only diagnostic')
    torch.set_num_threads(2);cv2.setNumThreads(1);p.seed_everything(42)
    preprocess=p.PreprocessConfig(**config['preprocess'])
    data=CachedReliabilityDataset(ROOT/config['cache'],manifest,preprocess)
    if len(data)!=2808 or sum(int(r['fractured']) for r in data.rows)!=493:
        raise ValueError('TRAIN membership changed')
    model=PresenceAttentionUNet().to('cuda')
    model.load_state_dict(torch.load(checkpoint,map_location='cuda',weights_only=True),strict=True);model.eval()
    before=tensor_digest(model.state_dict());supervised=bool(config['presence_weight'])
    out.mkdir()
    json_atomic(out/'config.json',dict(run=str(run.relative_to(ROOT)),checkpoint_sha256=p.sha(checkpoint),
        epoch=bundle['epoch'],manifest_sha256=p.sha(manifest),cache=config['cache'],preprocess=asdict(preprocess),
        output_contract=CONTRACT,source_hashes={**config['source_hashes'],'tools/audit_ai_presence_train_fit.py':p.sha(__file__),
        'tools/audit_ai_learning_fit.py':p.sha(ROOT/'tools/audit_ai_learning_fit.py')},
        scope='All2808 unaugmented TRAIN grid predictions; not native validation acceptance or model selection',
        mask_gated=False,device='cuda',inference_batch_size=1,augmentation=False,no_optimizer_steps=True,
        validation_images_read=0,calibration_images_read=0,test_images_read=0))
    masks,heads,alerts=[],[],[];started=time.perf_counter()
    with (out/'train_cases.jsonl').open('x') as stream,torch.inference_mode():
        for i,row in enumerate(data.rows):
            # This dataset's __getitem__ ALWAYS augments. Read the immutable
            # tensors directly for a genuinely unaugmented TRAIN-fit audit.
            x,y,valid=[torch.from_numpy(data.arrays[name][i].astype('float32',copy=True)).unsqueeze(0)
                       for name in ('image','target','valid')]
            output=model(x[None].to('cuda'))
            if not all(torch.isfinite(v).all() for v in output.values()): raise ValueError('Nonfinite TRAIN diagnostic')
            grid=output['mask_logits'].sigmoid()[0,0].cpu().numpy()
            case=grid_case(row,grid,y.numpy()[0])
            logit=float(output['presence_logits'][0]) if supervised else None
            score=float(output['presence_logits'].sigmoid()[0]) if supervised else None
            head_positive=score>=.5 if supervised else None
            alert=case['prediction_present'] or bool(head_positive)
            case.update(head_score=score,presence_logit=logit,classifier_prediction_present=head_positive,
                review_alert_present=alert,head_mask_group=review_group(head_positive,case['prediction_present']) if supervised else 'reference_mask_only')
            masks.append(case)
            alerts.append(dict(case,prediction_present=alert,case_score=max(case['case_score'],score) if supervised else case['case_score']))
            if supervised: heads.append(dict(case,prediction_present=head_positive,case_score=score))
            stream.write(json.dumps(case,allow_nan=False)+'\n')
            if (i+1)%100==0 or i+1==len(data):
                stream.flush()
                progress=dict(status='TRAIN_only_presence_fit',images=i+1,total=2808,elapsed_seconds=time.perf_counter()-started)
                json_atomic(out/'progress.json',progress);print(json.dumps(progress),flush=True)
    result=dict(mask_classification=a.classification(masks),conservative_review_classification=a.classification(alerts),
        independent_grid_segmentation=a.segmentation(masks),head_classification=a.classification(heads) if supervised else None,
        uncalibrated_head_diagnostic=a.calibration(heads) if supervised else None,
        positive_zero_overlap_masks=sum(c['zero_overlap_positive'] for c in masks),
        scope='TRAIN grid fit only; no validation or clinical performance claim',no_optimizer_steps=True,
        model_improvement_claim=False,validation_images_read=0,calibration_images_read=0,test_images_read=0)
    for key in ('mask_classification','conservative_review_classification','head_classification'):
        if result[key] is not None: result[key]['score_definition']='Uncalibrated TRAIN '+key+' diagnostic, not clinical confidence'
    if result['uncalibrated_head_diagnostic'] is not None:
        result['uncalibrated_head_diagnostic']['interpretation']='TRAIN diagnostic treating the supervised presence sigmoid as an uncalibrated case score; balanced TRAIN weighting, not maximum-pixel output or clinical confidence'
    json_atomic(out/'metrics.json',result)
    if tensor_digest(model.state_dict())!=before or p.sha(checkpoint)!=bundle['checkpoint_sha256']:
        raise ValueError('Read-only diagnostic changed model tensors/checkpoint')
    json_atomic(out/'completion.json',dict(status='completed_read_only_TRAIN_fit',train_cases=2808,
        elapsed_seconds=time.perf_counter()-started,model_tensors_unchanged=True,no_optimizer_steps=True,
        validation_images_read=0,calibration_images_read=0,test_images_read=0))
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    main()
