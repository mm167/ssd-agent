"""Local workspace lock primitive (PLAN Sections 6, 85, 86).

A lightweight local workspace lock prevents two SDD Agent processes from
concurrently orchestrating the same project state. The lock itself is not
workflow truth (PLAN Section 86).

Recoverability after abnormal process termination (PLAN Section 86) is
achieved by relying on the operating system's own file-lock semantics
(`fcntl.flock` on POSIX, `msvcrt.locking` on Windows) rather than a
liveness-checked PID file: both hold the lock only for the lifetime of the
open file handle, and the OS releases it automatically -- even after a
crash or SIGKILL -- when the holding process exits.
"""

from __future__ import annotations

import io
import json
import os
import platform
import socket
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import TracebackType

from sdd_agent.diagnostics.errors import WorkflowViolation

_IS_WINDOWS = platform.system() == "Windows"

if _IS_WINDOWS:
    import msvcrt
else:
    import fcntl


class WorkspaceLockConflictError(WorkflowViolation):
    """Raised when a workspace lock is already held by another process/handle."""


class _LockUnavailable(Exception):
    """Internal signal that the OS-level lock could not be acquired."""


@dataclass(frozen=True)
class WorkspaceLockInfo:
    """Diagnostic metadata recorded alongside the lock (not enforcement truth)."""

    pid: int
    hostname: str
    acquired_at: str


class WorkspaceLock:
    """A recoverable, OS-native exclusive lock over a single workspace path."""

    def __init__(self, lock_path: Path) -> None:
        self._lock_path = Path(lock_path)
        self._file: io.BufferedRandom | None = None

    @property
    def lock_path(self) -> Path:
        return self._lock_path

    @property
    def is_held(self) -> bool:
        return self._file is not None

    def acquire(self) -> None:
        if self._file is not None:
            raise WorkflowViolation(
                "WorkspaceLock.acquire() called while already held by this instance.",
                details={"lock_path": str(self._lock_path)},
            )

        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        handle = open(self._lock_path, "a+b")

        try:
            _lock_exclusive_nonblocking(handle)
        except _LockUnavailable as exc:
            handle.close()
            raise WorkspaceLockConflictError(
                f"Workspace lock already held: {self._lock_path}",
                details={"lock_path": str(self._lock_path)},
            ) from exc

        info = WorkspaceLockInfo(
            pid=os.getpid(),
            hostname=socket.gethostname(),
            acquired_at=datetime.now(timezone.utc).isoformat(),
        )
        _write_lock_metadata(handle, info)

        self._file = handle

    def release(self) -> None:
        if self._file is None:
            return
        handle = self._file
        self._file = None
        try:
            _unlock(handle)
        finally:
            handle.close()

    def __enter__(self) -> "WorkspaceLock":
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.release()


def _lock_exclusive_nonblocking(handle: io.BufferedRandom) -> None:
    if _IS_WINDOWS:
        # msvcrt.locking locks a byte range starting at the current file
        # position; ensure at least one byte exists so the lock region [0, 1)
        # is well defined and stable across the lifetime of this handle.
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise _LockUnavailable from exc
    else:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise _LockUnavailable from exc


def _write_lock_metadata(handle: io.BufferedRandom, info: WorkspaceLockInfo) -> None:
    # On Windows the first byte is the locked region placeholder; metadata is
    # written after it so the locked byte range never has to be re-locked.
    handle.seek(1 if _IS_WINDOWS else 0)
    handle.truncate()
    handle.write(json.dumps(asdict(info)).encode("utf-8"))
    handle.flush()
    os.fsync(handle.fileno())


def _unlock(handle: io.BufferedRandom) -> None:
    if _IS_WINDOWS:
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
    else:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
