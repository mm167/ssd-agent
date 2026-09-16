from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pytest

from sdd_agent.workspace.lock import WorkspaceLock, WorkspaceLockConflictError

_HELPER_SCRIPT = """
import sys
import time
from pathlib import Path

from sdd_agent.workspace.lock import WorkspaceLock

lock = WorkspaceLock(Path(sys.argv[1]))
lock.acquire()
print("LOCKED", flush=True)
time.sleep(30)
"""


def test_lock_is_recoverable_after_abnormal_process_termination(tmp_path: Path) -> None:
    lock_path = tmp_path / ".sdd" / "workspace.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    process = subprocess.Popen(
        [sys.executable, "-c", _HELPER_SCRIPT, str(lock_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 10
        line = ""
        while time.monotonic() < deadline and not line:
            line = process.stdout.readline()

        assert line.strip() == "LOCKED", (
            f"helper process did not report acquiring the lock; stderr={process.stderr.read()}"
        )

        # The lock is genuinely held cross-process.
        conflicting = WorkspaceLock(lock_path)
        with pytest.raises(WorkspaceLockConflictError):
            conflicting.acquire()

        # Simulate abnormal termination (not a graceful lock.release()).
        process.kill()
        process.wait(timeout=10)

        # A fresh lock must become acquirable again shortly after: the OS
        # releases the underlying file lock when the crashed process's
        # handle closes, though that release is not always instantaneous.
        recovered = WorkspaceLock(lock_path)
        acquire_deadline = time.monotonic() + 5
        last_error: WorkspaceLockConflictError | None = None
        while time.monotonic() < acquire_deadline:
            try:
                recovered.acquire()
                break
            except WorkspaceLockConflictError as exc:
                last_error = exc
                time.sleep(0.1)
        else:
            raise AssertionError("lock was not released after process termination") from last_error
        recovered.release()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)
