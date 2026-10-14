"""Research artifact writes that tolerate temporary Windows sharing locks.

The old destination remains intact until replacement succeeds. Persistent
permission errors still fail the run; no destination is deleted to bypass locks.
"""
import json
import os
from pathlib import Path
import time
import uuid


def replace_with_retry(temporary, destination, timeout=30., delay=.1):
    deadline = time.monotonic() + timeout
    while True:
        try:
            os.replace(temporary, destination)
            return
        except PermissionError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(delay)


def _temporary(path):
    path = Path(path)
    return path.with_name(path.name + '.pending.' + uuid.uuid4().hex)


def json_atomic(path, document):
    temporary = _temporary(path)
    with temporary.open('x', encoding='utf-8') as handle:
        json.dump(document, handle, indent=2, allow_nan=False)
        handle.flush()
        os.fsync(handle.fileno())
    replace_with_retry(temporary, path)


def atomic_save(document, path):
    import torch
    temporary = _temporary(path)
    with temporary.open('xb') as handle:
        torch.save(document, handle)
        handle.flush()
        os.fsync(handle.fileno())
    replace_with_retry(temporary, path)
