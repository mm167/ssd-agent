from __future__ import annotations

from sdd_agent.diagnostics.logs import LogLevel, OperationalLogEvent, format_log_event


def test_operational_log_event_formats_with_correlation() -> None:
    event = OperationalLogEvent(
        level=LogLevel.INFO,
        message="Launching Codex",
        task_id="T001",
        attempt_id="001",
    )

    assert format_log_event(event) == "[T001/001][INFO] Launching Codex"


def test_operational_log_event_formats_without_correlation() -> None:
    event = OperationalLogEvent(level=LogLevel.WARNING, message="Retry 1/3")

    assert format_log_event(event) == "[-][WARNING] Retry 1/3"
