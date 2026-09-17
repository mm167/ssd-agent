from __future__ import annotations

from pathlib import Path

import pytest

from sdd_agent.adapters.persistence.local_store import LocalPersistenceStore
from sdd_agent.configuration.models import AgentProvider, AgentRole
from sdd_agent.diagnostics.errors import PersistenceError
from sdd_agent.domain.models import AgentExecutionStatus, AgentResult, EvidenceContext


@pytest.mark.parametrize(
    ("diagnostics", "session_reference"),
    [
        (("provider rejected ghp_bareProviderCredential",), None),
        ((), "provider-session-sk-live-bareProviderCredential"),
        (("provider rejected sk-ant-bareProviderCredential",), None),
        ((), "https://user:hunter2@example.invalid/session/1"),
    ],
)
def test_agent_result_secret_bearing_evidence_is_not_persisted(
    tmp_path: Path,
    diagnostics: tuple[str, ...],
    session_reference: str | None,
) -> None:
    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)
    result = AgentResult(
        execution_id="exec-1",
        request_id="req-1",
        role=AgentRole.IMPLEMENTER,
        provider=AgentProvider.FAKE,
        context=EvidenceContext(task_id="T007", attempt_id="attempt-1", candidate_id="cand-1"),
        execution_status=AgentExecutionStatus.PROVIDER_ERROR,
        session_reference=session_reference,
        diagnostics=diagnostics or ("provider rejected request",),
    )

    with pytest.raises(PersistenceError) as excinfo:
        store.append_report("T007", "attempt-1", "agent-results", "exec-1", result)

    for secret in ("ghp_bareProviderCredential", "sk-live-bareProviderCredential", "sk-ant-bareProviderCredential", "hunter2"):
        assert secret not in str(excinfo.value)
    assert not (root / "attempts" / "T007" / "attempt-1" / "agent-results" / "exec-1.json").exists()


def test_agent_result_normal_free_text_evidence_is_persisted(tmp_path: Path) -> None:
    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)
    result = AgentResult(
        execution_id="exec-1",
        request_id="req-1",
        role=AgentRole.IMPLEMENTER,
        provider=AgentProvider.FAKE,
        context=EvidenceContext(task_id="T007", attempt_id="attempt-1", candidate_id="cand-1"),
        execution_status=AgentExecutionStatus.PROVIDER_ERROR,
        session_reference="fake-session-2026-09-17",
        diagnostics=("provider rejected the request",),
    )

    store.append_report("T007", "attempt-1", "agent-results", "exec-1", result)

    assert (root / "attempts" / "T007" / "attempt-1" / "agent-results" / "exec-1.json").exists()
