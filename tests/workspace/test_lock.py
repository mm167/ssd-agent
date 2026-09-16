from __future__ import annotations

from pathlib import Path

import pytest

from sdd_agent.diagnostics.errors import WorkflowViolation
from sdd_agent.workspace.lock import WorkspaceLock, WorkspaceLockConflictError


def test_acquire_creates_lock_file(tmp_path: Path) -> None:
    lock = WorkspaceLock(tmp_path / ".sdd" / "workspace.lock")

    lock.acquire()
    try:
        assert lock.lock_path.exists()
        assert lock.is_held
    finally:
        lock.release()


def test_conflicting_acquire_raises(tmp_path: Path) -> None:
    lock_path = tmp_path / ".sdd" / "workspace.lock"
    first = WorkspaceLock(lock_path)
    second = WorkspaceLock(lock_path)

    first.acquire()
    try:
        with pytest.raises(WorkspaceLockConflictError):
            second.acquire()
        assert not second.is_held
    finally:
        first.release()


def test_release_allows_reacquisition(tmp_path: Path) -> None:
    lock_path = tmp_path / ".sdd" / "workspace.lock"
    first = WorkspaceLock(lock_path)
    first.acquire()
    first.release()

    assert not first.is_held

    second = WorkspaceLock(lock_path)
    second.acquire()
    second.release()


def test_context_manager_releases_on_exit(tmp_path: Path) -> None:
    lock_path = tmp_path / ".sdd" / "workspace.lock"

    with WorkspaceLock(lock_path):
        pass

    second = WorkspaceLock(lock_path)
    second.acquire()
    second.release()


def test_double_acquire_on_same_instance_is_rejected(tmp_path: Path) -> None:
    lock_path = tmp_path / ".sdd" / "workspace.lock"
    lock = WorkspaceLock(lock_path)
    lock.acquire()
    try:
        with pytest.raises(WorkflowViolation):
            lock.acquire()
    finally:
        lock.release()


def test_release_without_acquire_is_a_no_op(tmp_path: Path) -> None:
    lock = WorkspaceLock(tmp_path / ".sdd" / "workspace.lock")

    lock.release()  # must not raise
