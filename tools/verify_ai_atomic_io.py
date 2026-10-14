"""Windows actual deny-delete sharing-lock recovery and persistent-error checks."""
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import sys
import threading
import time
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.ai_atomic_io import json_atomic, atomic_save, replace_with_retry

out = ROOT/'experiments/session_20261007_ai_loop_01/presence_io_recovery_r2/io_fixture'
out.mkdir()
path = out/'state.json'
json_atomic(path, dict(value='old'))
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
create = kernel.CreateFileW
create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                  wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
create.restype = wintypes.HANDLE
close = kernel.CloseHandle
close.argtypes = [wintypes.HANDLE]
close.restype = wintypes.BOOL

def lock():
    handle = create(str(path), 0x80000000, 1|2, None, 3, 0x80, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    return handle

handle = lock()
try:
    probe = out/'probe.tmp'
    probe.write_text('replacement')
    try:
        probe.replace(path)
    except PermissionError:
        sharing_failure_reproduced = True
    else:
        raise AssertionError('Fixture did not reproduce Windows replacement failure')
finally:
    close(handle)

handle = lock()
def release():
    time.sleep(.6)
    close(handle)
thread = threading.Thread(target=release)
thread.start()
started = time.monotonic()
json_atomic(path, dict(value='new'))
elapsed = time.monotonic()-started
thread.join()
assert elapsed >= .5 and json.loads(path.read_text())['value']=='new'

handle = lock()
pending = out/'persistent.tmp'
pending.write_text('do not delete existing destination')
try:
    try:
        replace_with_retry(pending, path, timeout=.25, delay=.05)
    except PermissionError:
        assert pending.exists() and json.loads(path.read_text())['value']=='new'
    else:
        raise AssertionError('Persistent lock should fail without deleting old destination')
finally:
    close(handle)
checkpoint = dict(model_state_dict=dict(weight=torch.arange(4.)), optimizer_state_dict={}, epoch=0)
atomic_save(checkpoint, out/'checkpoint.pt')
restored = torch.load(out/'checkpoint.pt', weights_only=True)
assert torch.equal(restored['model_state_dict']['weight'], checkpoint['model_state_dict']['weight'])
report = dict(status='passed', actual_Windows_sharing_error_reproduced=True,
              recovered_after_lock_release_seconds=elapsed, persistent_error_preserves_old_and_pending=True,
              weights_only_checkpoint_restore=True, dataset_images_read=0, model_performance_claim=False)
json_atomic(out/'completion.json', report)
print(json.dumps(report, indent=2))
