from __future__ import annotations

from sdd_agent.domain.models.enums import FindingSeverity
from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.models.review import Finding, ReviewReport
from sdd_agent.domain.policies.review_gate import ReviewGatePolicy


def _context(candidate_id: str = "cand-1") -> EvidenceContext:
    return EvidenceContext(task_id="T005", attempt_id="a1", candidate_id=candidate_id)


def _review(findings: list[Finding], candidate_id: str = "cand-1") -> ReviewReport:
    return ReviewReport(report_id="review-1", context=_context(candidate_id), findings=findings)


def test_passes_with_no_findings() -> None:
    decision = ReviewGatePolicy.evaluate(_review([]), _context())

    assert decision.passed


def test_passes_with_only_minor_findings() -> None:
    findings = [Finding(finding_id="f1", severity=FindingSeverity.MINOR, summary="style nit")]

    decision = ReviewGatePolicy.evaluate(_review(findings), _context())

    assert decision.passed


def test_blocker_finding_fails_gate() -> None:
    findings = [Finding(finding_id="f1", severity=FindingSeverity.BLOCKER, summary="broken invariant")]

    decision = ReviewGatePolicy.evaluate(_review(findings), _context())

    assert not decision.passed
    assert "BLOCKER=1" in decision.reasons


def test_important_finding_fails_gate() -> None:
    findings = [Finding(finding_id="f1", severity=FindingSeverity.IMPORTANT, summary="missing test")]

    decision = ReviewGatePolicy.evaluate(_review(findings), _context())

    assert not decision.passed
    assert "IMPORTANT=1" in decision.reasons


def test_review_for_a_different_candidate_does_not_apply() -> None:
    review = _review([], candidate_id="cand-1")

    decision = ReviewGatePolicy.evaluate(review, _context("cand-2"))

    assert not decision.passed
    assert any("does not apply" in reason for reason in decision.reasons)


def test_reviewer_prose_cannot_substitute_for_findings() -> None:
    # There is no "approved"/"looks good" field on ReviewReport at all; the
    # gate can only ever be driven by structured Finding severities.
    assert not hasattr(ReviewReport, "approved")
