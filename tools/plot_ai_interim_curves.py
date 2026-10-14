"""Plot actual completed E5/E6 epochs without changing selection or training."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.evaluate_ai_baseline import save


def captured_records(path):
    for _ in range(10):
        raw = path.read_bytes()
        if raw.endswith(b'\n'):
            return raw, [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
        time.sleep(.1)
    raise ValueError('Completed-epoch log is not complete; retry later')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if ROOT not in out.parents or out.exists():
        raise ValueError('New workspace figure directory required')
    runs = [('AI_E5_v3_BCE_reference', 'BCE1 reference', '#2563eb'),
            ('AI_E6_v3_normal_BCE2', 'Normal BCE2 (interim)', '#d97706')]
    captured, configs, digests = [], [], []
    for name, label, color in runs:
        path = ROOT/'experiments'/name
        raw, records = captured_records(path/'epochs.jsonl')
        config = json.loads((path/'config.json').read_text())
        if config['smoke'] or config['manifest_sha256']!='4fb850caf0050e29350002a56a8462c93d49365958ebe721e06be2c49480a318':
            raise ValueError('Require full matched frozen-v3 runs')
        configs.append(config)
        digests.append(json.loads((path/'initial_parameters.json').read_text())['parameter_sha256'])
        captured.append((name, label, color, raw, records))
    common = ('preprocess','postprocess','loss_config','lr','seed','batch_size','device','epochs','patience','source_hashes')
    if digests[0]!=digests[1] or any(configs[0][key]!=configs[1][key] for key in common):
        raise ValueError('Pair is not matched')
    out.mkdir()
    figure, axes = plt.subplots(2, 3, figsize=(12, 8), constrained_layout=True)
    fields = [('Sensitivity', 'classification', 'recall_sensitivity', 79/83),
              ('Specificity', 'classification', 'specificity', .9),
              ('Positive native Dice', 'delivered', 'mean_positive_dice', .5237965562512774),
              ('Positive native IoU', 'delivered', 'mean_positive_iou', .3775685932913787),
              ('AUROC: max-pixel score', 'classification', 'auroc', 79*342/(83*380)),
              ('F1', 'classification', 'f1', None)]
    for axis, (title, block, key, target) in zip(axes.flat, fields):
        for name, label, color, raw, records in captured:
            axis.plot([r['epoch'] for r in records], [r['validation'][block][key] for r in records],
                      marker='o', markersize=4, color=color, label=label)
        if target is not None:
            axis.axhline(target, color='#b91c1c', linestyle='--', linewidth=1.2,
                         label='Necessary score-ranking bound' if key=='auroc' else 'Required target/reference')
        axis.set_title(title)
        axis.set_xlabel('Completed epoch')
        axis.set_xlim(.5, 12.5)
        axis.set_ylim(0, 1)
        axis.grid(alpha=.2)
    axes[0, 0].legend(fontsize=8, loc='lower right')
    axes[1, 1].legend(fontsize=7, loc='lower right')
    e6_n = len(captured[1][4])
    figure.suptitle(f'Matched validation learning curves — E6 interim through epoch{e6_n}\n'
                   '463 frozen images:83 fractures/380 normals; threshold0.5/all; no test evaluation', fontsize=12)
    figure.savefig(out/'learning_curves.png', dpi=160)
    plt.close(figure)
    for name, _, _, raw, _ in captured:
        (out/(name+'_epochs.jsonl')).write_bytes(raw)
    save(out/'provenance.json', dict(status='interim_measured_epochs_only',
        counts={name:len(records) for name,_,_,_,records in captured},
        captured_log_sha256={name:hashlib.sha256(raw).hexdigest() for name,_,_,raw,_ in captured},
        initial_parameters_sha256=digests[0], threshold=.5, policy='all',
        dice_target='Same-ID original diagnostic Dice0.5037965563 + registered0.02 gain. Original threshold/preprocessing differ from this matched pair.',
        iou_target='Same-ID original diagnostic IoU; candidate must improve, not merely equal.',
        auroc_bound='Necessary, not sufficient, for any single threshold on the current scalar score to achieveTP79/TN342.',
        candidate_accepted=False, selection_changed=False, test_evaluated=False))
    print(json.dumps(dict(completed_epochs={name:len(records) for name,_,_,_,records in captured}, output=str(out))))


if __name__=='__main__':
    main()
