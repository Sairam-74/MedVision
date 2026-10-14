"""Preserve mislabeled augmented diagnostics and register corrected raw-cache runs."""
import datetime
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.ai_atomic_io import json_atomic
from tools.evaluate_ai_baseline import sha


def main():
    session=ROOT/'experiments/session_20261007_ai_loop_01'
    record=session/'UNAugmented_DIAGNOSTIC_CORRECTION.json'
    if record.exists(): raise ValueError('Correction already registered')
    specifications=[
        ('audit_ai_learned_loss_gradients.py','audit_ai_learned_loss_gradients_unaugmented.py',
         'AI_LEARNED_LOSS_GRADIENTS_E5_v3','AI_LEARNED_LOSS_GRADIENTS_E5_v3_unaugmented'),
        ('audit_ai_batchnorm_context.py','audit_ai_batchnorm_context_unaugmented.py',
         'AI_BATCHNORM_CONTEXT_E5_v3_r2','AI_BATCHNORM_CONTEXT_E5_v3_unaugmented')]
    records=[]
    for old,new,old_out,new_out in specifications:
        source=ROOT/'tools'/old; destination=ROOT/'tools'/new
        text=source.read_text()
        text=text.replace(old_out,new_out)
        text=text.replace(";data.training=False",'').replace('    data.training=False\n','')
        if old.startswith('audit_ai_learned'):
            needle='        x,y,valid,positive=data[index]'
            replacement="        x,y,valid=[torch.from_numpy(data.arrays[name][index].astype(np.float32,copy=True)).unsqueeze(0) for name in ('image','target','valid')]\n        positive=bool(int(data.rows[index]['fractured']))"
            assert text.count(needle)==1
            text=text.replace(needle,replacement)
        else:
            text=text.replace('AI_LEARNED_LOSS_GRADIENTS_E5_v3/config.json','AI_LEARNED_LOSS_GRADIENTS_E5_v3_unaugmented/config.json')
            needle='                    tensors=[data[i] for i in ii]'
            replacement="                    tensors=[tuple(torch.from_numpy(data.arrays[n][i].astype(np.float32,copy=True)).unsqueeze(0) for n in ('image','target','valid')) for i in ii]"
            assert text.count(needle)==1
            text=text.replace(needle,replacement)
        assert 'data.training=False' not in text
        assert 'data[index]' not in text and 'data[i]' not in text
        with destination.open('x',encoding='utf-8') as handle: handle.write(text)
        records.append(dict(preserved_source=old,source_sha256=sha(source),
                            preserved_output=old_out,corrected_source=new,
                            corrected_source_sha256=sha(destination),corrected_output=new_out))
    json_atomic(record,dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        issue='CachedReliabilityDataset.__getitem__ always augments; assigning training=False has no effect',
        affected='16-case E5 gradient and BatchNorm context diagnostics were augmented despite metadata claiming otherwise',
        unaffected='Full E5 TRAIN-fit reads raw arrays directly; E5/E6 and E7/E8 training intentionally augment; native validation uses its own loader',
        correction='Read exact cached tensors directly in new exclusive diagnostics; preserve old outputs and source files',
        pending_tool='Presence TRAIN-fit corrected before first run',records=records,
        optimizer_steps=0,calibration_images_read=0,test_images_read=0))
    with (session/'SESSION_PROGRESS.md').open('a',encoding='utf-8') as handle:
        handle.write('\n\nDiagnostic correction: CachedReliabilityDataset always augments in __getitem__; setting training=False did not disable it. Earlier16-case gradient and BatchNorm checks were augmented despite unaugmented metadata. Preserve these measurements as augmented-only diagnostics; do not cite them as unaugmented. Corrected raw-cache-only tools/outputs are separately registered in UNAugmented_DIAGNOSTIC_CORRECTION.json. Full E5 TRAIN-fit and actual candidate training/validation are unaffected. Presence TRAIN-fit was corrected before any run. No model or protected loader changed.\n')
    print(json.dumps(records,indent=2))


if __name__=='__main__': main()
