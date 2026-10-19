#!/usr/bin/env python3
"""Linux-only bounded worker supervision; no CUDA or systemd API in this module.

The worker script implements --worker OUT MARKER and --restore OUT. Restoration
is attempted only after every owned descendant has stopped. SIGKILL of this
supervisor, host failure, and a stuck kernel task require manual recovery.
"""
import argparse
import ctypes
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

interrupted = 0

def stop_requested(number, _frame):
    global interrupted
    interrupted = number


def descendants():
    """Find descendants, including children reparented to this Linux subreaper."""
    parents, states = {}, {}
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry / 'stat').read_text().rsplit(')', 1)[1].split()
            parents[int(entry.name)] = int(fields[1])
            states[int(entry.name)] = fields[0]
        except FileNotFoundError:
            continue
    owned = {os.getpid()}
    while True:
        more = {pid for pid, parent in parents.items() if parent in owned}
        if more <= owned:
            break
        owned |= more
    return {pid for pid in owned if pid != os.getpid() and states.get(pid) != 'Z'}


def drain():
    # No unrelated process IDs are read from persistent files. New child
    # process groups/sessions are still descendants of this subreaper.
    for sig, seconds in [(signal.SIGTERM, 2), (signal.SIGKILL, 5)]:
        deadline = time.monotonic() + seconds
        while True:
            live = descendants()
            if not live:
                return True
            for pid in live:
                try:
                    os.kill(pid, sig)
                except ProcessLookupError:
                    pass
            if time.monotonic() >= deadline:
                break
            time.sleep(.05)
    return not descendants()


def run(command, seconds, env):
    process = subprocess.Popen(command, start_new_session=True, env=env)
    deadline = time.monotonic() + seconds
    code = None
    try:
        while process.poll() is None:
            if interrupted:
                code = 128 + interrupted
                break
            if time.monotonic() >= deadline:
                code = 124
                break
            time.sleep(.05)
        if code is None:
            code = process.returncode
    finally:
        stopped = drain()
        if stopped:
            process.wait(timeout=2)
            # Reap adopted descendants only after Popen has reaped its child.
            while True:
                try:
                    pid, _ = os.waitpid(-1, os.WNOHANG)
                    if not pid:
                        break
                except ChildProcessError:
                    break
    return (code if code >= 0 else 128 - code), stopped


def main():
    global interrupted
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout', type=float, default=9000)
    parser.add_argument('--restore-timeout', type=float, default=1900)
    parser.add_argument('script', type=Path)
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    if sys.platform != 'linux' or not 0 < args.timeout <= 9000 or not 0 < args.restore_timeout <= 1900:
        parser.error('Linux required; timeout must be >0 and <=9000 (restore <=1900)')
    # Reparent orphan workers here so cleanup cannot miss a background child.
    if ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), 'Cannot become child subreaper; refusing to run')
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)  # Never reuse a previous pause marker.
    marker = out / 'pause-attempted'
    script = args.script.resolve()
    env = {**os.environ, 'OPENCODE_CARD_WORKER': '1'}
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, stop_requested)
    code, stopped = run(['bash', str(script), '--worker', str(out), str(marker)], args.timeout, env)
    if not stopped:
        print('Owned test processes remain; NOT restarting the service. Manual recovery required.', file=sys.stderr)
        return 125
    if marker.exists():
        interrupted = 0  # A previous termination requests cleanup, not its cancellation.
        restore_code, restored_stopped = run(['bash', str(script), '--restore', str(out)], args.restore_timeout, env)
        if restore_code or not restored_stopped:
            print('Service restoration failed or timed out; manual recovery required.', file=sys.stderr)
            return 125
    return code


if __name__ == '__main__':
    sys.exit(main())
