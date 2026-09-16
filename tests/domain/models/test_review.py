from __future__ import annotations

import pytest
from pydantic import ValidationError

from sdd_agent.domain.models import EvidenceContext, Finding, FindingRoute, FindingSeverity, ReviewReport


def _context_with_candidate() -> EvidenceContext:
    return EvidenceContext(task_id="T002", attempt_id="a1", candidate_id="c1")


def test_finding_minimal() -> None:
    finding = Finding(finding_id="f1", severity=FindingSeverity.MINOR, summary="Nit.")

    assert finding.route is None


def test_finding_rejects_unsupported_severity() -> None:
    with pytest.raises(ValidationError):
        Finding(finding_id="f1", severity="CRITICAL", summary="x")


def test_finding_rejects_unsupported_route() -> None:
    with pytest.raises(ValidationError):
        Finding(finding_id="f1", severity=FindingSeverity.BLOCKER, route="repository_mismatch", summary="x")


def test_finding_accepts_valid_route() -> None:
    finding = Finding(finding_id="f1", severity=FindingSeverity.BLOCKER, route=FindingRoute.CODE, summary="x")

    assert finding.route is FindingRoute.CODE


def test_review_report_empty_findings() -> None:
    report = ReviewReport(report_id="r1", context=_context_with_candidate())

    assert report.findings == []


def test_review_report_requires_candidate_id() -> None:
    with pytest.raises(ValidationError):
        ReviewReport(report_id="r1", context=EvidenceContext(task_id="T002", attempt_id="a1"))


def test_review_report_carries_findings() -> None:
    report = ReviewReport(
        report_id="r1",
        context=_context_with_candidate(),
        findings=[
            Finding(finding_id="f1", severity=FindingSeverity.BLOCKER, route=FindingRoute.CODE, summary="x"),
            Finding(finding_id="f2", severity=FindingSeverity.MINOR, summary="y"),
        ],
    )

    assert len(report.findings) == 2


def test_review_report_is_frozen() -> None:
    report = ReviewReport(report_id="r1", context=_context_with_candidate())

    with pytest.raises(ValidationError):
        report.findings = []  # type: ignore[misc]
