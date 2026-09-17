"""Domain layer: workflow representation, evidence contracts, gates, routing (PLAN Section 100).

TASKS T002 owns `domain.models` (data contracts and model-level invariants).
TASKS T005 owns `domain.policies` (PLAN Section 11 "Gate Policies": Readiness,
ReadyForReview, ReviewGate, ReadyToCommit, HumanCommitGate,
CommitAuthorization, Closure), `domain.routing` (ProblemClassifier output
shape and RoutingPolicy), and `domain.workflow` (Phase transition
authorization). PLAN Section 100's package map is a responsibility map, not a
mandatory directory tree; T005 consolidates "gates" into `domain.policies`
without collapsing the underlying architectural boundaries.

TASKS T006 adds `domain.policies.waiver_eligibility` (whether a waiver may be
requested/granted for an obligation+result at all, SPEC Sections 22.1-22.2)
alongside T005's gate policies, without modifying any of them.
"""
