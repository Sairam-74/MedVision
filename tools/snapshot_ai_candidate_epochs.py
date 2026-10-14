"""Preserve atomically completed research checkpoints without changing training.

No model inference, selection, calibration, test access or promotion.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import medvision_pipeline as p
from tools.evaluate_ai_baseline import save


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    run, out = Path(args.run).resolve(), Path(args.out).resolve()
    if ROOT not in run.parents or ROOT not in out.parents or out.exists():
        raise ValueError('Existing research run and new workspace output required')
    config = json.loads((run/'config.json').read_text())
    if config['smoke'] or config['manifest_sha256'] != '4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318':
        raise ValueError('Require full frozen-v3 research training')
    out.mkdir()
    save(out/'config.json', dict(run=str(run.relative_to(ROOT)), source_config_sha256=p.sha(run/'config.json'),
        helper_source_sha256=p.sha(__file__), purpose='Preserve completed epochs only; registered checkpoint selection unchanged',
        original_checkpoint_sha256=config['original_checkpoint_sha256'], first_observation_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
    seen = set()
    previous_epoch = -1
    while True:
        try:
            state = json.loads((run/'state.json').read_text())
        except json.JSONDecodeError:
            time.sleep(1)
            continue
        if state.get('status') not in ('training', 'completed'):
            raise ValueError('Unexpected trainer state; no partial checkpoint inferred')
        records = [json.loads(line) for line in (run/'epochs.jsonl').read_text().splitlines() if line.strip()]
        # last.pt is written by atomic replacement before the completed-epoch
        # record. Only read when at least one full new epoch is recorded.
        latest = records[-1]['epoch'] if records else -1
        if latest > previous_epoch:
            # Reading through an open handle observes an immutable completed file
            # even if the trainer subsequently replaces the path atomically.
            with (run/'last.pt').open('rb') as handle:
                checkpoint = torch.load(handle, map_location='cpu', weights_only=True)
                handle.seek(0)
                data = handle.read()
            epoch = int(checkpoint['epoch'])
            recorded = next((r for r in records if r['epoch']==epoch), None)
            if recorded is not None:
                if checkpoint['output_contract'] != p.CONTRACT or checkpoint['manifest_sha256'] != config['manifest_sha256']:
                    raise ValueError('Checkpoint contract/partition mismatch')
                if epoch not in seen:
                    name = f'epoch_{epoch:03d}_resume.pt'
                    with (out/name).open('xb') as handle:
                        handle.write(data)
                    digest = hashlib.sha256(data).hexdigest()
                    if p.sha(out/name) != digest:
                        raise ValueError('Snapshot copy changed bytes')
                    save(out/f'epoch_{epoch:03d}.json', dict(epoch=epoch, checkpoint=name, checkpoint_sha256=digest,
                        source_config_sha256=p.sha(run/'config.json'), measured_epoch_record=recorded,
                        registered_selection_changed=False, model_evaluated=False, test_evaluated=False))
                    seen.add(epoch)
                    print(json.dumps(dict(preserved_epoch=epoch, checkpoint=name, sha256=digest)),flush=True)
                previous_epoch = latest
            del checkpoint, data
        if p.sha(ROOT/'best_model.pt') != config['original_checkpoint_sha256']:
            raise ValueError('Protected original checkpoint changed')
        if state['status']=='completed':
            if latest >= 1 and latest not in seen:
                # A state/log update raced the first read; retry before completion.
                time.sleep(1)
                continue
            save(out/'completion.json', dict(status='completed_preservation_only', preserved_epochs=sorted(seen),
                inaccessible_prior_epochs=list(range(1, min(seen))) if seen else [],
                registered_selection_changed=False, model_evaluated=False, test_evaluated=False))
            break
        time.sleep(40)


if __name__=='__main__':
    main()
