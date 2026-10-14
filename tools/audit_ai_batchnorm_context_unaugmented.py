"""TRAIN-only E5 eval/batch-statistics context diagnostic; no weight fitting."""
import json
from pathlib import Path
import sys
import time
import cv2
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import medvision_pipeline as p
from tools.ai_cached_dataset import CachedReliabilityDataset
from tools.audit_ai_learning_fit import grid_case
from tools.ai_atomic_io import json_atomic


def main():
    out=ROOT/'experiments/AI_BATCHNORM_CONTEXT_E5_v3_unaugmented'
    if out.exists(): raise ValueError('Exclusive diagnostic required')
    specification=json.loads((ROOT/'experiments/AI_LEARNED_LOSS_GRADIENTS_E5_v3_unaugmented/config.json').read_text())
    checkpoint=ROOT/specification['checkpoint'];manifest=ROOT/'experiments/data_v3_reliability_20261007/manifest.json'
    if p.sha(checkpoint)!=specification['checkpoint_sha256'] or p.sha(manifest)!=specification['manifest_sha256']:
        raise ValueError('Frozen inputs changed')
    torch.set_num_threads(2);cv2.setNumThreads(1);p.seed_everything(42)
    config=p.PreprocessConfig(size=256,resize='stretch',clahe=True,blur_kernel=3,normalization='unit')
    data=CachedReliabilityDataset(ROOT/'experiments/AI_TRAIN_CACHE_v3_256_r2',manifest,config)
    by_id={r['image_id']:i for i,r in enumerate(data.rows)}
    ids=specification['ids'];indices=[by_id[v] for v in ids]
    state=torch.load(checkpoint,map_location='cpu',weights_only=True)
    model=p.LogitsAttentionUNet();model.load_state_dict(state,strict=True)
    out.mkdir();json_atomic(out/'config.json',dict(**specification,
        modes='stored BatchNorm eval stats vs current-input stats, batch1 vs batch2 on SAME16 TRAIN cases',
        pair_composition='Deliberately mixed positive/normal pairs; not natural TRAIN prevalence or clinical batching',
        never_apply_batch_statistics_to_validation=True,no_calibration_fit=True,
        no_checkpoint_saved=True))
    results={};maps={};started=time.perf_counter()
    with torch.inference_mode():
        for mode in ('eval','current_input_stats'):
            for batch_size in (1,2):
                name=f'{mode}_batch{batch_size}'
                model.load_state_dict(state,strict=True);model.train(mode!='eval')
                cases=[];probabilities={}
                for start in range(0,len(indices),batch_size):
                    ii=indices[start:start+batch_size]
                    tensors=[tuple(torch.from_numpy(data.arrays[n][i].astype(np.float32,copy=True)).unsqueeze(0) for n in ('image','target','valid')) for i in ii]
                    output=model(torch.stack([v[0] for v in tensors])).sigmoid().numpy()[:,0]
                    for i,items,prob in zip(ii,tensors,output):
                        if not np.isfinite(prob).all(): raise ValueError('Nonfinite diagnostic output')
                        cases.append(grid_case(data.rows[i],prob,items[1].numpy()[0]))
                        probabilities[data.rows[i]['image_id']]=prob.copy()
                results[name]=cases;maps[name]=probabilities
                json_atomic(out/'progress.json',dict(status='TRAIN_only_context_diagnostic',completed_mode=name))
                print(json.dumps(dict(completed_mode=name)),flush=True)
    comparisons={}
    reference=maps['eval_batch1']
    for name,values in maps.items():
        comparisons[name]=dict(max_abs_probability_delta=max(float(np.max(np.abs(values[i]-reference[i]))) for i in ids),
            changed_thresholded_pixels=sum(int(np.count_nonzero((values[i]>=.5)!=(reference[i]>=.5))) for i in ids),
            changed_case_decisions=sum(bool((values[i]>=.5).any())!=bool((reference[i]>=.5).any()) for i in ids),
            mean_positive_grid_dice=float(np.mean([c['dice'] for c in results[name] if c['positive']])))
    # Diagnostic in-memory batch-stat buffers are discarded; protected disk checkpoint unchanged.
    if p.sha(checkpoint)!=specification['checkpoint_sha256']: raise ValueError('Protected checkpoint changed')
    json_atomic(out/'per_case.json',results)
    report=dict(status='completed_TRAIN_only_context_diagnostic',cases_per_mode=16,comparisons=comparisons,
        elapsed_seconds=time.perf_counter()-started,no_optimizer_steps=True,no_checkpoint_saved=True,
        model_improvement_claim=False,validation_images_read=0,calibration_images_read=0,test_images_read=0,
        limitations='A deliberately balanced16-case sample only. Input-stat modes are diagnostics, never validation inference or a clinical candidate. No generalization/cause claim.')
    json_atomic(out/'completion.json',report);print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    main()
