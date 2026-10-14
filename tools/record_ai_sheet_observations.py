"""Append actual viewed-sheet notes; completion remains a separate coverage check."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.ai_atomic_io import json_atomic
from tools.evaluate_ai_baseline import sha

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--directory',required=True);ap.add_argument('--batch',required=True)
    args=ap.parse_args();directory,batch_path=Path(args.directory).resolve(),Path(args.batch).resolve()
    if ROOT not in directory.parents or ROOT not in batch_path.parents: raise ValueError('Workspace actual notes required')
    index=json.loads((directory/'index.json').read_text());batch=json.loads(batch_path.read_text());dest=directory/'actual_sheet_notes.json'
    current=json.loads(dest.read_text()) if dest.exists() else dict(actually_viewed=True,index_sha256=sha(directory/'index.json'),sheets=[])
    if current['index_sha256']!=sha(directory/'index.json'): raise ValueError('Index changed during actual review')
    start=len(current['sheets'])
    for offset,observed in enumerate(batch):
        sheet=index['sheets'][start+offset]
        if observed['sheet']!=sheet['sheet'] or len(observed['notes'])!=len(sheet['cases']): raise ValueError('Actual observation order/count differs')
        if any(not isinstance(n,str) or not n.strip() for n in observed['notes']): raise ValueError('Actual note required for each case')
    current['sheets'].extend(batch);json_atomic(dest,current)
    print(json.dumps(dict(actual_sheets_recorded=len(current['sheets']),total_sheets=len(index['sheets']),review_completed=False)))

if __name__=='__main__': main()
