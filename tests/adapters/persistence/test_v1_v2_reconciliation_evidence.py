from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from sdd_agent.adapters.persistence.local_store import LocalPersistenceStore
from sdd_agent.domain.models import CIResult, CIStatus, HumanDecision, ReviewReport
from sdd_agent.domain.policies.closure import ClosurePolicy


_REPO_ROOT = Path(__file__).resolve().parents[3]
_RECONCILIATION_ATTEMPT = "v1-v2-reconciliation"
_RATIFICATION_ID = "human-v1-v2-recovery-ratification-001"
_CI_ID = "ci-v1-v2-recovery-001"
_RECONCILIATION_CAVEAT = (
    "must not itself be treated as durable closing evidence until this reconciliation "
    "candidate has completed independent review, human approval, commit, push, and "
    "Hosted CI GREEN for the exact resulting commit"
)
_HISTORICAL_EVIDENCE_CAVEAT = (
    "It does not claim the historical implementation commit contained this "
    "reconciliation evidence."
)

_HISTORICAL_COMMITS = {
    "T003": "d919d0e8de237beb53586e901f11b521fe1fd3ec",
    "T004": "fc6228fb5356c973589c75c6f0fadd06b9353648",
    "T006": "2d3c91c071ea04b3abb15f6a337e61a39f366436",
    "T007": "661233fac88bf19e9cf1d9a61563db60165b4b47",
}

_REQUIRED_RECONCILIATION_FILES = tuple(
    Path(".sdd")
    / "attempts"
    / task_id
    / _RECONCILIATION_ATTEMPT
    / relative
    for task_id in ("T003", "T004", "T006", "T007")
    for relative in (
        Path("decisions") / f"{_RATIFICATION_ID}.json",
        Path("ci") / f"{_CI_ID}.json",
        Path("events.jsonl"),
    )
)

_REQUIRED_T005_FILES = (
    Path(".sdd/attempts/T005/001/attempt.json"),
    Path(".sdd/attempts/T005/001/ci/ci-recovery-001.json"),
    Path(".sdd/attempts/T005/001/decisions/decision-recovery-001.json"),
    Path(".sdd/attempts/T005/001/events.jsonl"),
    Path(".sdd/attempts/T005/001/implementation/impl-recovery-001.json"),
    Path(".sdd/attempts/T005/001/reviews/review-recovery-001.json"),
)

_REQUIRED_EVIDENCE_FILES = _REQUIRED_RECONCILIATION_FILES + _REQUIRED_T005_FILES


def _copy_required_evidence(tmp_path: Path) -> LocalPersistenceStore:
    for relative_path in _REQUIRED_EVIDENCE_FILES:
        source = _REPO_ROOT / relative_path
        assert source.is_file(), f"missing fixed reconciliation fixture: {relative_path}"
        target = tmp_path / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return LocalPersistenceStore(tmp_path / ".sdd")


def _raw_json(relative_path: Path) -> dict[str, object]:
    return json.loads((_REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def test_v1_v2_reconciliation_inventory_is_fixed_and_git_trackable() -> None:
    assert len(_REQUIRED_EVIDENCE_FILES) == 18
    for relative_path in _REQUIRED_EVIDENCE_FILES:
        assert (_REPO_ROOT / relative_path).is_file(), relative_path
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", relative_path.as_posix()],
            cwd=_REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert result.stdout.splitlines() == [relative_path.as_posix()]


def test_future_or_unrelated_sdd_evidence_remains_ignored() -> None:
    for relative_path in (
        ".sdd/current.json",
        ".sdd/attempts/T008/future/events.jsonl",
        ".sdd/attempts/T003/v1-v2-reconciliation/extra.json",
    ):
        result = subprocess.run(
            ["git", "check-ignore", "-v", relative_path],
            cwd=_REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert result.stdout.strip()


def test_v1_v2_reconciliation_evidence_is_reconstructible_from_isolated_sdd(
    tmp_path: Path,
) -> None:
    store = _copy_required_evidence(tmp_path)

    for task_id, expected_commit in _HISTORICAL_COMMITS.items():
        decision = store.load_report(
            task_id,
            _RECONCILIATION_ATTEMPT,
            "decisions",
            _RATIFICATION_ID,
            HumanDecision,
        )
        ci_result = store.load_report(
            task_id,
            _RECONCILIATION_ATTEMPT,
            "ci",
            _CI_ID,
            CIResult,
        )
        events = store.read_events(task_id, _RECONCILIATION_ATTEMPT)

        assert "RECOVERY_RATIFICATION_CURRENT" in decision.choice
        assert "not contemporaneous historical gate evidence" in decision.choice
        assert ci_result.expected_commit == expected_commit
        assert ci_result.status is CIStatus.GREEN
        assert [event.event_type for event in events] == ["RECOVERY_RATIFICATION_RECORDED"]
        assert events[0].payload["not_historical_gate_evidence"] is True
        assert events[0].payload["current_decision"] is True


def test_reconciliation_timestamps_are_persisted_and_stable(tmp_path: Path) -> None:
    store = _copy_required_evidence(tmp_path)

    decision_path = (
        Path(".sdd/attempts/T003/v1-v2-reconciliation/decisions")
        / f"{_RATIFICATION_ID}.json"
    )
    ci_path = Path(".sdd/attempts/T003/v1-v2-reconciliation/ci") / f"{_CI_ID}.json"
    event_path = Path(".sdd/attempts/T003/v1-v2-reconciliation/events.jsonl")
    assert "decided_at" in _raw_json(decision_path)
    assert "observed_at" in _raw_json(ci_path)
    event_line = json.loads((_REPO_ROOT / event_path).read_text(encoding="utf-8").splitlines()[0])
    assert "occurred_at" in event_line

    first_decision = store.load_report(
        "T003", _RECONCILIATION_ATTEMPT, "decisions", _RATIFICATION_ID, HumanDecision
    )
    second_decision = store.load_report(
        "T003", _RECONCILIATION_ATTEMPT, "decisions", _RATIFICATION_ID, HumanDecision
    )
    assert second_decision.decided_at == first_decision.decided_at

    first_ci = store.load_report("T003", _RECONCILIATION_ATTEMPT, "ci", _CI_ID, CIResult)
    second_ci = store.load_report("T003", _RECONCILIATION_ATTEMPT, "ci", _CI_ID, CIResult)
    assert second_ci.observed_at == first_ci.observed_at

    first_event = store.read_events("T003", _RECONCILIATION_ATTEMPT)[0]
    second_event = store.read_events("T003", _RECONCILIATION_ATTEMPT)[0]
    assert second_event.occurred_at == first_event.occurred_at


def test_ratification_caveat_is_consistent_for_t004_t006_t007(tmp_path: Path) -> None:
    store = _copy_required_evidence(tmp_path)

    for task_id in ("T004", "T006", "T007"):
        decision = store.load_report(
            task_id,
            _RECONCILIATION_ATTEMPT,
            "decisions",
            _RATIFICATION_ID,
            HumanDecision,
        )
        events = store.read_events(task_id, _RECONCILIATION_ATTEMPT)

        assert _RECONCILIATION_CAVEAT in decision.choice
        assert _HISTORICAL_EVIDENCE_CAVEAT in decision.choice
        assert _RECONCILIATION_CAVEAT in events[0].payload["candidate_lifecycle_caveat"]


def test_closure_policy_with_reconciliation_evidence_keeps_t003_pending_until_new_commit(
    tmp_path: Path,
) -> None:
    store = _copy_required_evidence(tmp_path)
    ci_result = store.load_report(
        "T003",
        _RECONCILIATION_ATTEMPT,
        "ci",
        _CI_ID,
        CIResult,
    )

    decision = ClosurePolicy.evaluate(
        review_gate_satisfied=True,
        ready_to_commit_applicable=True,
        human_commit_approval_applicable=True,
        commit_created=False,
        pushed=False,
        remote_target_verified=False,
        repository_mismatch=False,
        expected_commit=ci_result.expected_commit,
        ci_result=ci_result,
    )

    assert not decision.passed
    assert "current expected candidate is not committed" in decision.reasons
    assert "current expected commit is not pushed" in decision.reasons


def test_closure_policy_accepts_human_ratified_historical_reconciliation_tasks(
    tmp_path: Path,
) -> None:
    store = _copy_required_evidence(tmp_path)

    for task_id in ("T004", "T006", "T007"):
        ci_result = store.load_report(
            task_id,
            _RECONCILIATION_ATTEMPT,
            "ci",
            _CI_ID,
            CIResult,
        )

        decision = ClosurePolicy.evaluate(
            review_gate_satisfied=True,
            ready_to_commit_applicable=True,
            human_commit_approval_applicable=True,
            commit_created=True,
            pushed=True,
            remote_target_verified=True,
            repository_mismatch=False,
            expected_commit=ci_result.expected_commit,
            ci_result=ci_result,
        )

        assert decision.passed


def test_t005_existing_recovery_evidence_remains_reconstructible(tmp_path: Path) -> None:
    store = _copy_required_evidence(tmp_path)

    decision = store.load_report("T005", "001", "decisions", "decision-recovery-001", HumanDecision)
    ci_result = store.load_report("T005", "001", "ci", "ci-recovery-001", CIResult)
    review = store.load_report("T005", "001", "reviews", "review-recovery-001", ReviewReport)

    assert "RECOVERY_APPROVAL" in decision.choice
    assert ci_result.expected_commit == "989efbef11060675f1b05a8d9854aa3f4e7e719e"
    assert ci_result.status is CIStatus.GREEN
    assert review.report_id == "review-recovery-001"
    assert review.findings == []
