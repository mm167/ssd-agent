from __future__ import annotations

from pathlib import Path

import pytest

from sdd_agent.adapters.persistence.local_store import LocalPersistenceStore
from sdd_agent.diagnostics.errors import PersistenceError
from sdd_agent.domain.models import WorkflowEvent


def _event(event_id: str, event_type: str = "ATTEMPT_STARTED") -> WorkflowEvent:
    return WorkflowEvent(event_id=event_id, task_id="T003", attempt_id="a1", event_type=event_type)


def test_read_events_returns_empty_list_when_missing(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")

    assert store.read_events("T003", "a1") == []


def test_append_and_read_events_round_trip_preserves_order(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")

    store.append_event(_event("e1", "ATTEMPT_STARTED"))
    store.append_event(_event("e2", "READINESS_COMPLETED"))
    store.append_event(_event("e3", "VALIDATION_COMPLETED"))

    events = store.read_events("T003", "a1")

    assert [event.event_id for event in events] == ["e1", "e2", "e3"]
    assert [event.event_type for event in events] == [
        "ATTEMPT_STARTED",
        "READINESS_COMPLETED",
        "VALIDATION_COMPLETED",
    ]


def test_appending_never_rewrites_previous_lines(tmp_path: Path) -> None:
    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)
    store.append_event(_event("e1"))

    path = root / "attempts" / "T003" / "a1" / "events.jsonl"
    first_write = path.read_text(encoding="utf-8")

    store.append_event(_event("e2"))
    second_write = path.read_text(encoding="utf-8")

    assert second_write.startswith(first_write)


def test_events_are_isolated_between_attempts(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")
    store.append_event(_event("e1"))

    assert store.read_events("T003", "a2") == []
    assert store.read_events("T004", "a1") == []


def test_corrupt_event_line_raises_persistence_error(tmp_path: Path) -> None:
    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)
    store.append_event(_event("e1"))

    path = root / "attempts" / "T003" / "a1" / "events.jsonl"
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("{not valid json\n")

    with pytest.raises(PersistenceError):
        store.read_events("T003", "a1")


def test_blank_lines_are_tolerated(tmp_path: Path) -> None:
    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)
    store.append_event(_event("e1"))

    path = root / "attempts" / "T003" / "a1" / "events.jsonl"
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("\n")

    events = store.read_events("T003", "a1")
    assert [event.event_id for event in events] == ["e1"]
