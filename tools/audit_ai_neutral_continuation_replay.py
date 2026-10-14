"""CPU checkpoint-only integrity check; no inference or optimizer steps."""
import argparse
import json
from pathlib import Path
import sys
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.ai_presence_model import tensor_digest
from tools.smoke_ai_hard_candidate import optimizer_state_digest
from tools.evaluate_ai_baseline import sha
from tools.ai_atomic_io import json_atomic


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if ROOT not in out.parents or out.exists():
        raise ValueError('Exclusive workspace evidence required')
    old = ROOT/'experiments/AI_E7_v3_presence_reference_r2'
    new = ROOT/'experiments/AI_E9_v3_hard_reference'
    configs = [json.loads((run/'config.json').read_text()) for run in (old,new)]
    for key in ('manifest_sha256','cache','preprocess','postprocess','loss','loss_config',
                'normal_bce_weight','presence_weight','batch_size','lr','seed','elastic'):
        if configs[0][key] != configs[1][key]:
            raise ValueError('Replay configuration differs: '+key)
    if configs[1]['hard_factor'] != 1 or configs[1]['warm_start_epoch'] != 18:
        raise ValueError('Registered neutral continuation required')
    paths = [old/'epoch_011_resume.pt', new/'epoch_001_resume.pt']
    snapshots = [torch.load(path,map_location='cpu',weights_only=True) for path in paths]
    if any(s['global_epoch'] != 19 or s['presence_weight'] != 0 for s in snapshots):
        raise ValueError('Corresponding same-global-epoch snapshots required')
    models = [tensor_digest(s['model_state_dict']) for s in snapshots]
    optimizers = [optimizer_state_digest(s['optimizer_state_dict']) for s in snapshots]
    checks = dict(model_tensors_exactly_equal=models[0]==models[1],
                  actual_optimizer_state_exactly_equal=optimizers[0]==optimizers[1])
    result = dict(status='passed_exact_neutral_training_replay' if all(checks.values()) else 'replay_difference_requires_investigation',
                  checks=checks,global_epoch=19,model_digests=models,optimizer_digests=optimizers,
                  input_hashes={str(path.relative_to(ROOT)):sha(path) for path in paths},
                  source_sha256=sha(__file__),device='cpu',checkpoint_reads_only=True,
                  image_reads=0,inference_performed=False,optimizer_steps=0,
                  calibration_images_read=0,test_images_read=0,promotion=False,
                  scope='Known same-seed reference trajectory integrity; not a model improvement or clinical generalization result')
    out.mkdir()
    json_atomic(out/'completion.json',result)
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
