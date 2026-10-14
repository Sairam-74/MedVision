"""Scientific evaluation checks: one prediction must not recall two targets."""
import json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.phase6_evidence import region_recall

left=np.zeros((80,80),np.uint8);left[20:40,10:20]=1
right=np.zeros_like(left);right[20:40,40:50]=1
bridge=np.zeros_like(left);bridge[20:40,10:50]=1
checks=[]
for predicted,targets,threshold,expected,name in [
    (bridge,[left,right],.1,(1,2,0),'bridged prediction cannot match two fractures'),
    (left|right,[left,right],.5,(2,2,0),'two separate correct regions match twice'),
    (left|right,[bridge],.1,(1,1,1),'two fragments cannot match one target twice'),
    (np.zeros_like(left),[left],.5,(0,1,0),'missing prediction counts a missed target'),
    (left|right,[],.5,(0,0,2),'normal image counts both false-positive regions'),
    (np.zeros_like(left),[],.5,(0,0,0),'empty normal image has zero regions'),
]:
    actual=region_recall(predicted,targets,threshold)
    assert actual==expected,(name,actual,expected)
    checks.append(name)
out=ROOT/'experiments/session_20261006_p6p7/region_matching_checks.json'
out.write_text(json.dumps({'passed':len(checks),'checks':checks},indent=2))
print(f'{len(checks)} one-to-one region matching checks pass.')
