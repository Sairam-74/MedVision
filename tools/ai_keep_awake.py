"""Temporary idle-sleep request while workspace AI jobs run on AC power.

No persistent power settings, display requirement or away mode. Manual sleep is
respected. Request is cleared on exit and has a bounded eight-hour lease.
"""
import argparse
import ctypes
import datetime
import hashlib
import json
from pathlib import Path
import sys
import time

import psutil

ROOT = Path(__file__).resolve().parents[1]


def active_ai_work():
    found = []
    special = {'ai_validation_audit.py', 'ai_error_groups.py', 'analyze_ai_pair.py',
               'watch_ai_pair_audits.ps1', 'queue_ai_reliability.ps1'}
    for process in psutil.process_iter():
        try:
            if Path(process.cwd()).resolve()!=ROOT:
                continue
            for arg in process.cmdline()[1:]:
                try:
                    path = (ROOT/arg).resolve()
                except (OSError, ValueError):
                    continue
                name = path.name
                eligible = name in special or (name.endswith('.py') and (name.startswith('train_') or name.startswith('audit_ai_')))
                if eligible and path.parent==ROOT/'tools' and path.is_file():
                    found.append(dict(pid=process.pid, script=name))
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
            continue
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    if sys.platform!='win32':
        raise ValueError('Windows-only transient request')
    out = Path(args.out).resolve()
    if ROOT not in out.parents or out.exists():
        raise ValueError('New workspace output required')
    out.mkdir()
    function = ctypes.WinDLL('kernel32', use_last_error=True).SetThreadExecutionState
    function.argtypes = [ctypes.c_uint]
    function.restype = ctypes.c_uint
    continuous, system_required = 0x80000000, 0x00000001
    started = time.monotonic()
    source_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    previous = None
    try:
        while time.monotonic()-started < 8*3600:
            work = active_ai_work()
            battery = psutil.sensors_battery()
            plugged = battery is None or battery.power_plugged
            required = bool(work) and plugged
            flags = continuous | system_required if required else continuous
            returned = int(function(flags))
            if not returned:
                raise ctypes.WinError(ctypes.get_last_error())
            state = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                status='temporary_idle_sleep_request' if required else 'request_released',
                on_AC=plugged, active_workspace_AI_jobs=work, API_return_nonzero=True,
                persistent_power_settings_changed=False, display_required=False, away_mode=False,
                manual_sleep_respected=True, lease_hours=8, elapsed_seconds=time.monotonic()-started,
                source_sha256=source_sha)
            temporary = out/'state.tmp'
            temporary.write_text(json.dumps(state, indent=2))
            temporary.replace(out/'state.json')
            marker = required, tuple((r['pid'], r['script']) for r in work)
            if marker!=previous:
                print(json.dumps(state), flush=True)
                previous = marker
            if not work:
                break
            time.sleep(30)
    finally:
        function(continuous)
        (out/'completion.json').write_text(json.dumps(dict(status='temporary_request_released',
            persistent_power_settings_changed=False, elapsed_seconds=time.monotonic()-started), indent=2))


if __name__=='__main__':
    main()
