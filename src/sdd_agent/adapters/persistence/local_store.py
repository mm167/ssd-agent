"""Local filesystem `PersistenceStore` implementation (TASKS T003; PLAN
Sections 63-71).

Layout under `root` (conceptually `.sdd/`, PLAN Section 65)::

    current.json
    attempts/<task_id>/<attempt_id>/attempt.json
    attempts/<task_id>/<attempt_id>/events.jsonl
    attempts/<task_id>/<attempt_id>/<category>/<report_id>.json

Two write strategies are used, matching PLAN Section 64/66-67:

- `current.json` is a mutable snapshot: writes go through
  `_atomic_replace_json`, which validates-then-writes-temp-then-atomically-
  replaces the target so a reader never observes a partially written file.
- the attempt record, category reports, and event-journal appends are
  append-only: `_atomic_create_json` uses `os.link` to atomically fail if
  the target already exists (never a check-then-write race), and
  `append_event` only ever opens `events.jsonl` in append mode, so a
  previously written line is never rewritten.

All reads validate persisted JSON through the requested Pydantic model and
check `schema_version` before trusting the data (PLAN Sections 69-70):
corrupt JSON, an incompatible schema version, or data that fails model
validation all raise `PersistenceError` explicitly rather than silently
defaulting missing fields or returning a partially valid object.

Path safety (T003-IR-001): every path built from an external/domain
identifier (`task_id`, `attempt_id`, `category`, `report_id`) is funneled
through `_attempt_dir`/`_category_dir`/`_report_path`, which reject any
component containing a path separator, drive qualifier, or NUL byte, or
equal to `.`/`..`, via `_validate_path_component`. As defense in depth, the
same helpers also resolve the constructed path and reject it via
`_ensure_within_root` if it would not be a descendant of the configured
`.sdd` root. Invalid identifiers are rejected outright rather than encoded,
since T002's identifier fields carry no encoding convention to reuse.

Secret rejection (T003-IR-002): every write path calls `_reject_secrets` on
the exact dict about to be persisted, reusing the repository's existing
secret-shaped-key/credential-bearing-value detectors
(`sdd_agent.configuration.secrets`) rather than a duplicate ruleset. The
check runs before any filesystem mutation -- including before the temporary
file used by the atomic-write helpers is created -- so rejected data never
touches disk, not even transiently.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from sdd_agent.configuration.secrets import find_secret_like_keys, find_secret_like_values
from sdd_agent.diagnostics.errors import PersistenceError
from sdd_agent.domain.models.attempt import Attempt
from sdd_agent.domain.models.event import WorkflowEvent
from sdd_agent.domain.models.schema import CURRENT_SCHEMA_VERSION
from sdd_agent.ports.persistence import PersistenceStore

ReportT = TypeVar("ReportT", bound=BaseModel)

_CURRENT_FILENAME = "current.json"
_ATTEMPT_FILENAME = "attempt.json"
_EVENTS_FILENAME = "events.jsonl"

_INVALID_PATH_COMPONENT_CHARS = frozenset("/\\:\x00")


class LocalPersistenceStore(PersistenceStore):
    """`PersistenceStore` backed by plain JSON/JSONL files under `root`."""

    def __init__(self, root: Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    # -- current pointer (mutable) ---------------------------------------

    def save_current(self, attempt: Attempt) -> None:
        path = self._ensure_within_root(self._root / _CURRENT_FILENAME)
        data = attempt.model_dump(mode="json")
        _reject_secrets(data, path=path)
        _atomic_replace_json(path, data)

    def load_current(self) -> Attempt | None:
        path = self._ensure_within_root(self._root / _CURRENT_FILENAME)
        if not path.is_file():
            return None
        return _read_model(path, Attempt)

    # -- attempt record (append-only) ------------------------------------

    def save_attempt_record(self, attempt: Attempt) -> None:
        path = self._attempt_dir(attempt.task_id, attempt.attempt_id) / _ATTEMPT_FILENAME
        data = attempt.model_dump(mode="json")
        _reject_secrets(data, path=path)
        _atomic_create_json(path, data)

    def load_attempt_record(self, task_id: str, attempt_id: str) -> Attempt | None:
        path = self._attempt_dir(task_id, attempt_id) / _ATTEMPT_FILENAME
        if not path.is_file():
            return None
        return _read_model(path, Attempt)

    # -- event journal (append-only) -------------------------------------

    def append_event(self, event: WorkflowEvent) -> None:
        path = self._attempt_dir(event.task_id, event.attempt_id) / _EVENTS_FILENAME
        data = event.model_dump(mode="json")
        _reject_secrets(data, path=path)
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(data, sort_keys=True)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def read_events(self, task_id: str, attempt_id: str) -> list[WorkflowEvent]:
        path = self._attempt_dir(task_id, attempt_id) / _EVENTS_FILENAME
        if not path.is_file():
            return []

        events: list[WorkflowEvent] = []
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            events.append(_parse_model_line(line, WorkflowEvent, path, line_number))
        return events

    # -- reports (append-only) -------------------------------------------

    def append_report(
        self,
        task_id: str,
        attempt_id: str,
        category: str,
        report_id: str,
        report: BaseModel,
    ) -> None:
        path = self._report_path(task_id, attempt_id, category, report_id)
        data = report.model_dump(mode="json")
        _reject_secrets(data, path=path)
        _atomic_create_json(path, data)

    def load_report(
        self,
        task_id: str,
        attempt_id: str,
        category: str,
        report_id: str,
        model_type: type[ReportT],
    ) -> ReportT:
        path = self._report_path(task_id, attempt_id, category, report_id)
        if not path.is_file():
            raise PersistenceError(
                f"Report not found: {path}",
                details={"path": str(path)},
                task_id=task_id,
                attempt_id=attempt_id,
            )
        return _read_model(path, model_type)

    def list_report_ids(self, task_id: str, attempt_id: str, category: str) -> list[str]:
        directory = self._category_dir(task_id, attempt_id, category)
        if not directory.is_dir():
            return []
        return sorted(p.stem for p in directory.glob("*.json"))

    def load_reports(
        self,
        task_id: str,
        attempt_id: str,
        category: str,
        model_type: type[ReportT],
    ) -> list[ReportT]:
        return [
            self.load_report(task_id, attempt_id, category, report_id, model_type)
            for report_id in self.list_report_ids(task_id, attempt_id, category)
        ]

    # -- paths (T003-IR-001: centralized path-component safety) ----------

    def _attempt_dir(self, task_id: str, attempt_id: str) -> Path:
        task_component = _validate_path_component(task_id, label="task_id")
        attempt_component = _validate_path_component(attempt_id, label="attempt_id")
        path = self._root / "attempts" / task_component / attempt_component
        return self._ensure_within_root(path)

    def _category_dir(self, task_id: str, attempt_id: str, category: str) -> Path:
        category_component = _validate_path_component(category, label="category")
        path = self._attempt_dir(task_id, attempt_id) / category_component
        return self._ensure_within_root(path)

    def _report_path(self, task_id: str, attempt_id: str, category: str, report_id: str) -> Path:
        report_component = _validate_path_component(report_id, label="report_id")
        path = self._category_dir(task_id, attempt_id, category) / f"{report_component}.json"
        return self._ensure_within_root(path)

    def _ensure_within_root(self, path: Path) -> Path:
        root_resolved = self._root.resolve()
        candidate_resolved = path.resolve()
        try:
            candidate_resolved.relative_to(root_resolved)
        except ValueError as exc:
            raise PersistenceError(
                f"Refusing to access a path outside the .sdd root: {path}",
                details={"path": str(path), "root": str(root_resolved)},
            ) from exc
        return path


def _validate_path_component(value: str, *, label: str) -> str:
    """Reject `value` if it cannot safely be used as a single path segment.

    Rejects (rather than encodes -- T003-IR-001) empty strings, `.`/`..`,
    and any value containing a path separator, drive-qualifier colon, or NUL
    byte. This blocks traversal (`../..`), absolute paths, and
    drive-qualified paths (`C:\\...`) at the identifier level, before any
    path is even constructed.
    """
    if not value:
        raise PersistenceError(f"{label} must not be empty.", details={label: value})
    if value in (".", ".."):
        raise PersistenceError(
            f"{label} must not be '.' or '..': {value!r}",
            details={label: value},
        )
    if any(char in _INVALID_PATH_COMPONENT_CHARS for char in value):
        raise PersistenceError(
            f"{label} must not contain path separators, drive qualifiers, or NUL: {value!r}",
            details={label: value},
        )
    return value


def _reject_secrets(data: dict[str, Any], *, path: Path) -> None:
    """Refuse to persist `data` if it contains secret-shaped keys or
    credential-bearing values (T003-IR-002; PLAN Section 78).

    Reuses the exact detectors the repository already applies to `sdd.yaml`
    (`sdd_agent.configuration.secrets`) instead of a second, potentially
    inconsistent ruleset. Must be called before any filesystem mutation for
    the write in question.
    """
    offending_keys = sorted(find_secret_like_keys(data))
    offending_values = sorted(find_secret_like_values(data))

    if not offending_keys and not offending_values:
        return

    messages = []
    if offending_keys:
        messages.append("secret-like key(s): " + ", ".join(offending_keys))
    if offending_values:
        messages.append("credential-bearing value(s) at: " + ", ".join(offending_values))

    raise PersistenceError(
        f"Refusing to persist data under .sdd/ that appears to contain secrets: {path}; "
        + "; ".join(messages),
        details={
            "path": str(path),
            "offending_keys": offending_keys,
            "offending_values": offending_values,
        },
    )


def _temp_path_for(path: Path) -> Path:
    return path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")


def _write_temp_file(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = _temp_path_for(path)
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, sort_keys=True, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    return tmp_path


def _atomic_replace_json(path: Path, data: dict[str, Any]) -> None:
    """Atomically write `data` to `path`, overwriting any existing content
    (PLAN Section 64: validate -> write temp -> flush -> atomic replace).
    """
    tmp_path = _write_temp_file(path, data)
    try:
        os.replace(tmp_path, path)
    finally:
        tmp_path.unlink(missing_ok=True)


def _atomic_create_json(path: Path, data: dict[str, Any]) -> None:
    """Atomically write `data` to `path`, refusing to overwrite an existing
    file (PLAN Section 67: historical evidence is append-only).

    `os.link` atomically fails with `FileExistsError` if `path` already
    exists, so there is no check-then-write race between the existence
    check and the write.
    """
    tmp_path = _write_temp_file(path, data)
    try:
        try:
            os.link(tmp_path, path)
        except FileExistsError as exc:
            raise PersistenceError(
                f"Refusing to overwrite existing append-only record: {path}",
                details={"path": str(path)},
            ) from exc
    finally:
        tmp_path.unlink(missing_ok=True)


def _check_schema_version(data: dict[str, Any], path: Path) -> None:
    version = data.get("schema_version")
    if version != CURRENT_SCHEMA_VERSION:
        raise PersistenceError(
            f"Incompatible schema_version in persisted state: {path}",
            details={
                "path": str(path),
                "found": version,
                "expected": CURRENT_SCHEMA_VERSION,
            },
        )


def _parse_json_text(text: str, path: Path) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PersistenceError(
            f"Corrupt persisted state (invalid JSON): {path}",
            details={"path": str(path)},
        ) from exc

    if not isinstance(data, dict):
        raise PersistenceError(
            f"Corrupt persisted state (expected a JSON object): {path}",
            details={"path": str(path)},
        )
    return data


def _validate_model(data: dict[str, Any], model_type: type[ReportT], path: Path) -> ReportT:
    _check_schema_version(data, path)
    try:
        return model_type.model_validate(data)
    except ValidationError as exc:
        raise PersistenceError(
            f"Corrupt or incompatible persisted state: {path}",
            details={"path": str(path), "errors": exc.errors()},
        ) from exc


def _read_model(path: Path, model_type: type[ReportT]) -> ReportT:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PersistenceError(
            f"Failed to read persisted state: {path}",
            details={"path": str(path)},
        ) from exc

    data = _parse_json_text(raw, path)
    return _validate_model(data, model_type, path)


def _parse_model_line(line: str, model_type: type[ReportT], path: Path, line_number: int) -> ReportT:
    location = f"{path}:{line_number}"
    try:
        data = json.loads(line)
    except json.JSONDecodeError as exc:
        raise PersistenceError(
            f"Corrupt event journal line (invalid JSON): {location}",
            details={"path": str(path), "line": line_number},
        ) from exc

    if not isinstance(data, dict):
        raise PersistenceError(
            f"Corrupt event journal line (expected a JSON object): {location}",
            details={"path": str(path), "line": line_number},
        )

    try:
        return _validate_model(data, model_type, path)
    except PersistenceError as exc:
        raise PersistenceError(
            f"Corrupt event journal line: {location}",
            details={"path": str(path), "line": line_number, **exc.details},
        ) from exc
