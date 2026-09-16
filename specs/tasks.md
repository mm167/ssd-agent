# SDD Agent V1 --- TASKS

-   **Product:** SDD Agent
-   **Product Version:** V1 --- Semi-Automatic
-   **Tasks Revision:** V1
-   **Phase:** TASKS
-   **Specification Status:** SPEC_READY
-   **Plan Status:** PLAN_READY
-   **TASKS Status:** TASKS_READY
-   **Encoding:** UTF-8

------------------------------------------------------------------------

# 1. Purpose

This document decomposes the approved SDD Agent V1 SPEC and PLAN into
implementation TASKS.

This document does not define new PRODUCT behavior or new ARCHITECTURE.
It assigns approved responsibilities from `spec.md` and `plan.md` to
bounded TASKS with explicit dependencies, acceptance criteria,
validation expectations, and future-task boundaries.

CODE phase is authorized after TASKS_READY, but individual TASK
execution remains governed by dependency and readiness checks.

------------------------------------------------------------------------

# 2. Authority Boundaries

Mandatory routing remains:

``` text
PRODUCT        -> SPEC
ARCHITECTURE   -> PLAN
DECOMPOSITION  -> TASKS
IMPLEMENTATION -> CODE
```

TASKS may define:

``` text
scope
dependencies
deliverables
acceptance criteria
validation expectations
explicit exclusions
```

TASKS must not introduce:

``` text
new PRODUCT behavior
new architecture
implementation code
provider-specific implementation mechanics not required by PLAN
```

------------------------------------------------------------------------

# 3. Dependency Graph

Dependencies determine readiness. Task number does not determine
execution order.

``` text
T001 -> T002
T001 -> T008
T001 -> T017

T002 -> T003
T002 -> T004
T002 -> T005
T002 -> T006
T002 -> T007
T002 -> T008
T002 -> T014

T003 -> T008
T003 -> T012
T003 -> T017

T004 -> T011
T004 -> T012
T004 -> T013

T005 -> T006
T005 -> T007
T005 -> T011
T005 -> T012
T005 -> T013
T005 -> T014
T005 -> T016
T005 -> T017

T006 -> T011
T006 -> T012

T007 -> T008
T007 -> T009
T007 -> T010
T007 -> T011

T008 -> T009
T008 -> T010
T008 -> T011

T011 -> T016

T012 -> T013

T013 -> T016

T014 -> T015
T014 -> T016

T015 -> T016

T011 -> T017
T012 -> T017
T013 -> T017
T016 -> T017

T001 -> T018
T002 -> T018
T003 -> T018
T004 -> T018
T005 -> T018
T006 -> T018
T007 -> T018
T008 -> T018
T009 -> T018
T010 -> T018
T011 -> T018
T012 -> T018
T013 -> T018
T014 -> T018
T015 -> T018
T016 -> T018
T017 -> T018
```

------------------------------------------------------------------------

# 4. TASK Definitions

## T001 --- Project Foundation, Configuration, Diagnostics

Task ID: T001

Title: Project Foundation, Configuration, Diagnostics

Objective:
Establish the Python package skeleton, configuration loading,
provider-selection configuration, diagnostics boundaries,
timeouts/retry settings, logs/evidence separation, and workspace-lock
foundation.

Dependencies: NONE

SPEC Traceability:
Sources of truth, artifact routing, recoverability, human authority, V1
non-goals.

PLAN Traceability:
Sections 3, 6, 7, 76, 77, 78, 80, 81, 82, 83, 84, 98, 100, 101.

Scope:
- Python 3.13+ project layout.
- Pydantic configuration model.
- `sdd.yaml` parsing and validation.
- Provider names for agents and CI.
- Secret exclusion from committed configuration and `.sdd/`.
- Workspace lock primitive.
- Structured diagnostics and technical error surfaces.
- Timeout and retry configuration.

Deliverables:
- Package skeleton.
- Configuration model and loader.
- Diagnostics model.
- Workspace lock primitive.
- Timeout and retry configuration support.

Acceptance Criteria:
- Invalid configuration blocks sensitive operations with explainable
  errors.
- Secrets are not accepted in committed configuration.
- Provider mappings can express Claude Code, Codex, FakeAgentRunner,
  GitHub Actions, and Fake CI.
- Workspace locking prevents concurrent unsafe orchestration.

Validation Expectations:
- Unit tests for valid and invalid configuration.
- Unit tests for secret rejection.
- Unit tests for workspace lock acquisition and release.
- Unit tests for diagnostic formatting.

Explicit Exclusions / Future-Task Boundary:
- No workflow execution.
- No live provider calls.
- No concrete agent or CI adapter behavior beyond configuration names.

------------------------------------------------------------------------

## T002 --- Domain Models and Evidence Contracts

Task ID: T002

Title: Domain Models and Evidence Contracts

Objective:
Define the core Pydantic/domain models used across workflow, evidence,
reports, findings, candidate identity references, and statuses.

Dependencies:
- T001

SPEC Traceability:
Candidate, validation evidence, waiver applicability, review findings,
human decisions, CI evidence, gate semantics.

PLAN Traceability:
Sections 9, 10, 12, 15, 18, 25, 26, 28, 31, 36, 39, 49, 62, 63, 64,
90A.

Scope:
- Attempt, phase, condition, and next authorized action models.
- Evidence applicability context.
- Readiness, validation, review, waiver, human decision, CI, and
  implementation report models.
- Severity, routing, validation result, CI status, and completion status
  closed value sets.
- Schema/version conventions for persisted structured data.

Deliverables:
- Validated model module.
- Shared schema/version conventions.
- Evidence identity model sufficient for applicability checks.

Acceptance Criteria:
- Models validate required identity fields.
- Unsupported statuses and severities are rejected.
- Evidence can carry enough identity for later applicability checks.
- ImplementationReport is candidate-bound in its model contract.

Validation Expectations:
- Unit tests for required and optional fields.
- Unit tests for invalid enum values.
- Unit tests for missing identity fields.
- Unit tests for schema version handling.

Explicit Exclusions / Future-Task Boundary:
- No persistence implementation.
- No gate policy behavior beyond model-level validation.

------------------------------------------------------------------------

## T003 --- Persistence, Event History, and Recovery Store

Task ID: T003

Title: Persistence, Event History, and Recovery Store

Objective:
Implement `.sdd/` persistence with atomic writes, append-only reports
and events, schema validation, and restart reconstruction primitives.

Dependencies:
- T002

SPEC Traceability:
Sources of truth, operational state, persistence and recovery, loss of
conversation, historical evidence.

PLAN Traceability:
Sections 65, 66, 67, 68, 69, 70, 71, 72, 73, 106.

Scope:
- JSON persistence under `.sdd/`.
- Atomic write strategy.
- Append-only event log.
- Append-only report storage.
- Current state snapshot storage.
- Schema version compatibility checks.
- Corrupt state detection.
- Recovery loader for process restart.

Deliverables:
- Persistence port and local filesystem adapter.
- Recovery loader.
- Append-only event and report APIs.

Acceptance Criteria:
- A fresh process can reconstruct active Attempt state from repository
  plus `.sdd/` evidence once related TASKS provide repository evidence.
- Corrupt or incompatible state is detected and blocks sensitive
  transitions.
- Historical reports remain append-only.

Validation Expectations:
- Persistence tests for atomic writes.
- Tests for schema validation and version mismatch.
- Tests for corrupt state detection.
- Tests for append-only history.
- Restart/recovery tests using persisted state fixtures.

Explicit Exclusions / Future-Task Boundary:
- No Git operations.
- No workflow policy implementation.
- No provider adapters.

------------------------------------------------------------------------

## T004 --- GitRepository, Baseline, Dirty Start, CandidateSnapshot

Task ID: T004

Title: GitRepository, Baseline, Dirty Start, CandidateSnapshot

Objective:
Implement repository inspection through `GitRepository`, including
dirty-start preflight, immutable baseline identity, candidate
snapshotting, candidate fingerprinting, and worktree/index distinction.

Dependencies:
- T002

SPEC Traceability:
Baseline, pre-existing repository changes, candidate identity,
repository mismatch, gate invalidation.

PLAN Traceability:
Sections 21, 22, 23, 24, 25, 26, 27, 30, 38, 96.3.

Scope:
- `GitRepository` port.
- Git CLI adapter for repository inspection.
- Clean-start checks.
- Baseline full SHA identity.
- CandidateSnapshot for tracked modifications, tracked deletions,
  file modes, binary content identities, and non-ignored untracked
  files.
- Ignored-file exclusion.
- Rename representation independent from Git rename heuristics.
- Candidate fingerprint calculation.
- Worktree/index divergence detection.

Deliverables:
- `GitRepository` port.
- Git CLI inspection adapter.
- Candidate snapshot and fingerprint service.

Acceptance Criteria:
- Dirty repository blocks new Attempt creation.
- CandidateSnapshot deterministically includes non-ignored untracked
  files.
- CandidateSnapshot excludes Git-ignored files.
- Worktree/index divergence is observable.
- Candidate identity changes when included candidate content or
  inclusion rules change.

Validation Expectations:
- Local temporary Git repository integration tests.
- Tests for dirty start, staged-only changes, untracked files, ignored
  files, binary files, file modes, and deletions.
- Tests for rename-as-delete/add behavior.
- Tests for worktree/index divergence.

Explicit Exclusions / Future-Task Boundary:
- No commit execution.
- No push execution.
- No remote verification.

------------------------------------------------------------------------

## T005 --- Workflow Core, Gates, Routing, and State Machine

Task ID: T005

Title: Workflow Core, Gates, Routing, and State Machine

Objective:
Implement deterministic workflow authorization, phase/condition/next
action handling, gate policies, invalidation, and routing
classification outputs.

Dependencies:
- T002

SPEC Traceability:
READINESS, VALIDATION, REVIEW, READY_TO_COMMIT, COMMIT authorization,
CLOSED, routing, deterministic gates.

PLAN Traceability:
Sections 5, 8, 9, 11, 12, 37, 42, 43, 44, 45, 46, 91, 92, 93, 95.

Scope:
- Phase, condition, and next-action transition authorization.
- ReadinessPolicy.
- ReadyForReviewPolicy.
- ReviewGatePolicy.
- ReadyToCommitPolicy.
- HumanCommitGatePolicy.
- CommitAuthorizationPolicy.
- ClosurePolicy.
- RoutingPolicy and problem classification output handling.
- Evidence invalidation rules.

Deliverables:
- Pure policy functions where practical.
- Transition authorization APIs for the Orchestrator.

Acceptance Criteria:
- Agents and adapters cannot directly authorize transitions.
- Gates reject stale or mismatched evidence.
- BLOCKER and IMPORTANT findings deterministically block commit
  readiness.
- Human approval is not equivalent to READY_TO_COMMIT.
- CLOSED cannot be manually assigned.

Validation Expectations:
- Unit tests for all gate policies.
- Unit tests for invalidation and stale evidence.
- Unit tests for severity count behavior.
- Unit tests for routing classes.
- Unit tests for closure requirements.

Explicit Exclusions / Future-Task Boundary:
- No concrete CLI.
- No live agents.
- No GitHub integration.
- No provider-specific implementation details.

------------------------------------------------------------------------

## T006 --- ValidationRunner, Obligations, Results, and Waivers

Task ID: T006

Title: ValidationRunner, Obligations, Results, and Waivers

Objective:
Implement validation obligation discovery/execution contracts, result
evidence, failure classification input, and waiver applicability rules.

Dependencies:
- T002
- T005

SPEC Traceability:
Validation, failed validation, insufficient validation, waiver policy,
waiver invalidation, validation evidence.

PLAN Traceability:
Sections 32, 33, 34, 35, 36, 39, 40, 41, 91, 96.5.

Scope:
- ValidationRunner port.
- Validation obligation contracts.
- Validation command result evidence.
- PASSED, FAILED, and NOT_RUN result handling.
- Waiver request and approval applicability.
- Non-waivable validation and closure condition support.

Deliverables:
- Validation port and contracts.
- Waiver policy support.
- Validation evidence APIs.

Acceptance Criteria:
- FAILED validation cannot be waived.
- NOT_RUN requires environment classification before waiver eligibility.
- Stale waivers do not satisfy current gates.
- Review is blocked when required validation evidence is missing and no
  applicable waiver exists.

Validation Expectations:
- Unit tests for PASSED, FAILED, and NOT_RUN.
- Unit tests for waiver eligibility.
- Unit tests for stale waiver invalidation.
- Unit tests for missing required validation.

Explicit Exclusions / Future-Task Boundary:
- No project-specific validation command catalog beyond generic runner
  contracts.
- No integrated review orchestration; that belongs to T011.

------------------------------------------------------------------------

## T007 --- AgentRunner Port, FakeAgentRunner, and Agent Evidence

Task ID: T007

Title: AgentRunner Port, FakeAgentRunner, and Agent Evidence

Objective:
Implement provider-neutral `AgentRunner` contracts, structured agent
requests/results, deterministic `FakeAgentRunner`, and
ImplementationReport handling.

Dependencies:
- T002
- T005

SPEC Traceability:
Implementer, reviewer, implementation completion not equal success,
lost agent session.

PLAN Traceability:
Sections 13, 15, 18, 90A, 91, 96.4, 97.

Scope:
- AgentRunner port.
- AgentRequest and AgentResult integration.
- FakeAgentRunner scripted outcomes for deterministic tests.
- Structured report validation hooks.
- ImplementationReport candidate binding.

Deliverables:
- AgentRunner port.
- FakeAgentRunner.
- Agent report validation hooks.

Acceptance Criteria:
- Core tests can run deterministically without live LLMs.
- FakeAgentRunner does not replace required concrete Claude Code and
  Codex adapters.
- Missing concrete providers cannot be represented as complete V1
  implementation.
- Stale ImplementationReport becomes non-applicable when candidate
  changes.

Validation Expectations:
- Unit tests for fake outcomes.
- Unit tests for invalid structured reports.
- Unit tests for ImplementationReport candidate binding.
- Unit tests for ImplementationReport invalidation.

Explicit Exclusions / Future-Task Boundary:
- No Claude Code process invocation; that belongs to T009.
- No Codex process invocation; that belongs to T010.
- No provider-specific prompt or CLI mechanics.

------------------------------------------------------------------------

## T008 --- ContextBuilder and Session Policy

Task ID: T008

Title: ContextBuilder and Session Policy

Objective:
Implement role-specific context construction and session policy rules
for implementation, review, fix, re-review, and lost-session recovery.

Dependencies:
- T001
- T002
- T003
- T007

SPEC Traceability:
Independent review, conversation not durable truth, lost session
recoverability.

PLAN Traceability:
Sections 16, 17, 19, 20, 72, 106.

Scope:
- ContextBuilder service.
- Initial independent reviewer context.
- Implementer and reviewer session references.
- Session reuse policy for FIX and RE-REVIEW.
- Replacement-session context from durable evidence.

Deliverables:
- ContextBuilder service.
- Session policy evaluator.

Acceptance Criteria:
- Initial reviewer context excludes implementer conversational history.
- Lost implementer sessions can be replaced from durable evidence.
- Lost reviewer sessions can be replaced from durable evidence.
- Provider session identifiers are treated as non-authoritative
  optimization metadata.

Validation Expectations:
- Unit tests for context inclusion and exclusion.
- Unit tests for initial review independence.
- Unit tests for lost-session reconstruction.
- Unit tests for session reuse policy decisions.

Explicit Exclusions / Future-Task Boundary:
- No provider-specific prompt syntax.
- No Claude Code or Codex invocation.

------------------------------------------------------------------------

## T009 --- Claude Code Adapter

Task ID: T009

Title: Claude Code Adapter

Objective:
Implement the concrete Claude Code `AgentRunner` adapter behind the
provider-neutral port.

Dependencies:
- T007
- T008

SPEC Traceability:
Agent execution as implementation/review aid, no autonomous authority,
lost session recoverability.

PLAN Traceability:
Sections 13, 15, 16, 19, 20, 78, 79, 96.4, 97, 101; PLAN-098.

Scope:
- Claude Code invocation adapter.
- Request/result translation.
- Session reference handling.
- Adapter diagnostics.
- External credential boundary.

Deliverables:
- Claude Code adapter.
- Adapter-level tests with subprocess fakes or stubs.

Acceptance Criteria:
- Adapter satisfies `AgentRunner` without leaking Claude-specific
  details into Core.
- Credentials are supplied through external provider mechanisms.
- Structured outputs are validated before use.
- Missing Claude Code adapter means V1 is incomplete.

Validation Expectations:
- Adapter tests using fake process responses.
- Tests for malformed provider output.
- Tests for diagnostic mapping.
- Normal test run does not require live Claude Code.

Explicit Exclusions / Future-Task Boundary:
- No Core workflow rule changes.
- No Codex adapter; that belongs to T010.
- No live integration test requirement for every run.

------------------------------------------------------------------------

## T010 --- Codex Adapter

Task ID: T010

Title: Codex Adapter

Objective:
Implement the concrete Codex `AgentRunner` adapter behind the
provider-neutral port.

Dependencies:
- T007
- T008

SPEC Traceability:
Independent review and agent execution as non-authoritative evidence.

PLAN Traceability:
Sections 13, 15, 16, 19, 20, 78, 79, 96.4, 97, 101; PLAN-098.

Scope:
- Codex invocation adapter.
- Request/result translation.
- Session reference handling.
- Adapter diagnostics.
- External credential boundary.

Deliverables:
- Codex adapter.
- Adapter-level tests with subprocess fakes or stubs.

Acceptance Criteria:
- Adapter satisfies `AgentRunner` without leaking Codex-specific details
  into Core.
- Credentials are supplied through external provider mechanisms.
- Structured outputs are validated before use.
- Missing Codex adapter means V1 is incomplete.

Validation Expectations:
- Adapter tests using fake process responses.
- Tests for malformed provider output.
- Tests for diagnostic mapping.
- Normal test run does not require live Codex.

Explicit Exclusions / Future-Task Boundary:
- No Core workflow rule changes.
- No Claude Code adapter; that belongs to T009.
- No live integration test requirement for every run.

------------------------------------------------------------------------

## T011 --- Implementation, Review, FIX, and RE-REVIEW Orchestration

Task ID: T011

Title: Implementation, Review, FIX, and RE-REVIEW Orchestration

Objective:
Wire AgentRunner, ContextBuilder, Git verification, validation evidence,
and gates into implementation, review, FIX, and RE-REVIEW orchestration.

Dependencies:
- T004
- T005
- T006
- T007
- T008

SPEC Traceability:
Implementation, independent review, reviewer must not modify candidate,
FIX/RE-REVIEW, non-CODE findings.

PLAN Traceability:
Sections 19, 20, 37, 43, 44, 45, 46, 90A, 91, 92, 103, 104.

Scope:
- Orchestrator actions for implement, review, fix, and re-review.
- Post-agent repository verification.
- Unexpected reviewer modification detection.
- Unexpected implementer commit detection.
- Unexpected implementer push detection.
- Finding classification and routing.
- Candidate-changing FIX return through validation and RE-REVIEW.

Deliverables:
- Orchestrator workflows for agent-driven phases.
- Repository verification integration after agent execution.

Acceptance Criteria:
- REVIEW requires applicable validation evidence.
- Initial REVIEW uses independent reviewer context.
- Reviewer repository modification causes repository mismatch handling.
- Implementer commit or push activity is detected.
- Blocking findings route correctly.
- Candidate-changing FIX requires validation and RE-REVIEW.

Validation Expectations:
- Scenario tests using FakeAgentRunner.
- Tests with temporary Git repositories for unexpected repository
  changes.
- Tests for review gating and re-review routing.
- Tests for non-CODE finding routing.

Explicit Exclusions / Future-Task Boundary:
- No human commit approval; that belongs to T012.
- No commit/push/remote verification; that belongs to T013.
- No hosted CI closure; that belongs to T016.

------------------------------------------------------------------------

## T012 --- Human Decisions and Commit Approval Gate

Task ID: T012

Title: Human Decisions and Commit Approval Gate

Objective:
Implement structured human decisions, validation waiver approvals, and
candidate-bound human commit approval.

Dependencies:
- T003
- T004
- T005
- T006

SPEC Traceability:
Human authority, waiver approval, Human Commit Gate, COMMIT requires
approval and READY_TO_COMMIT.

PLAN Traceability:
Sections 52, 53, 54, 55, 56, 57, 58, 59, 92, 93.

Scope:
- HumanDecision model use.
- Waiver approval/refusal capture.
- Human Commit Gate entry.
- Commit approval capture.
- Commit refusal and requested-change handling.
- Approval applicability and stale approval invalidation.

Deliverables:
- Human decision services.
- Human Commit Gate integration.
- Candidate-bound approval evidence.

Acceptance Criteria:
- Human Commit Gate cannot be entered without applicable
  READY_TO_COMMIT.
- Approval for Candidate A cannot authorize Candidate B.
- Approval alone cannot authorize COMMIT.
- Requested CODE change routes candidate back to FIX.

Validation Expectations:
- Unit tests for approval, refusal, and requested change.
- Unit tests for candidate mismatch.
- Unit tests for stale approval invalidation.
- Unit tests for waiver decision visibility.

Explicit Exclusions / Future-Task Boundary:
- No actual Git commit.
- No push.
- No remote verification.

------------------------------------------------------------------------

## T013 --- Commit, Push, and Remote Verification

Task ID: T013

Title: Commit, Push, and Remote Verification

Objective:
Implement orchestrated commit, push, expected commit identity, expected
remote target verification, and remote drift handling.

Dependencies:
- T004
- T005
- T012

SPEC Traceability:
Commit, push, expected remote Git state, remote drift, current expected
commit.

PLAN Traceability:
Sections 29, 30, 31, 60, 61, 62, 63, 64, 93, 94.

Scope:
- Commit authorization execution through GitRepository.
- Commit tree verification against authorized CandidateSnapshot.
- Expected commit SHA evidence.
- Push execution.
- Expected remote target evidence.
- Remote mismatch and drift detection.

Deliverables:
- Commit orchestration.
- Push orchestration.
- Remote verification evidence.

Acceptance Criteria:
- COMMIT occurs only with applicable READY_TO_COMMIT and human approval
  for the same candidate.
- Committed tree matches authorized CandidateSnapshot.
- PUSH alone does not close the TASK.
- Remote drift blocks closure.

Validation Expectations:
- Git integration tests with local repositories and local remotes.
- Tests for commit tree match.
- Tests for stale approval rejection.
- Tests for push verification.
- Tests for remote drift.

Explicit Exclusions / Future-Task Boundary:
- No hosted CI provider calls.
- No CI closure.

------------------------------------------------------------------------

## T014 --- CIProvider Port, Fake CI, CI Evidence, and Expected Commit Rules

Task ID: T014

Title: CIProvider Port, Fake CI, CI Evidence, and Expected Commit Rules

Objective:
Implement provider-neutral `CIProvider`, fake CI adapter, normalized CI
status model, and expected-commit applicability rules.

Dependencies:
- T002
- T005

SPEC Traceability:
Hosted CI, current expected commit, CI failure classification, CLOSED
conditions.

PLAN Traceability:
Sections 47, 48, 49, 50, 51, 95, 96.6, 97; PLAN-097.

Scope:
- CIProvider port.
- FakeCIProvider.
- CIResult evidence.
- Provider-neutral CI status model.
- Expected commit binding.
- CI polling contract boundary.

Deliverables:
- CIProvider port.
- Fake CI adapter.
- CI evidence policy integration.

Acceptance Criteria:
- CI GREEN for commit B cannot satisfy expected commit A.
- Fake CI enables deterministic Core tests.
- Fake CI does not replace the concrete GitHub Actions adapter required
  for V1.
- CI statuses use the provider-neutral model.

Validation Expectations:
- Unit tests for normalized statuses.
- Unit tests for expected_commit mismatch.
- Unit tests for fake CI deterministic sequences.
- Unit tests for closure rejection on stale CI.

Explicit Exclusions / Future-Task Boundary:
- No GitHub Actions API or CLI implementation; that belongs to T015.
- No production hosted CI closure using fake CI.

------------------------------------------------------------------------

## T015 --- GitHub Actions CI Adapter

Task ID: T015

Title: GitHub Actions CI Adapter

Objective:
Implement the concrete V1 GitHub Actions adapter behind `CIProvider`.

Dependencies:
- T014

SPEC Traceability:
Hosted CI must be evaluated for the current expected commit.

PLAN Traceability:
Sections 47, 48, 49, 50, 78, 79, 96.6, 97, 101; PLAN-097.

Scope:
- GitHub Actions adapter.
- Provider-specific state translation into provider-neutral CI statuses.
- Expected commit filtering.
- External credential boundary.
- Adapter diagnostics.

Deliverables:
- GitHub Actions CI adapter.
- Adapter translation tests.

Acceptance Criteria:
- Adapter maps GitHub-specific workflow states into the single
  provider-neutral CI model.
- Core does not import GitHub-specific implementation.
- Credentials are supplied through external provider mechanisms.
- Missing GitHub Actions adapter means V1 is incomplete.

Validation Expectations:
- Adapter tests with mocked or stubbed GitHub responses.
- Tests for wrong-commit workflow data.
- Tests for provider-state translation.
- Normal test run does not require live GitHub Actions.

Explicit Exclusions / Future-Task Boundary:
- No redesign of CIProvider.
- Exact REST endpoint, CLI, SDK, HTTP library, and authentication
  mechanics remain CODE-level implementation details within this TASK.
- No additional CI providers.

------------------------------------------------------------------------

## T016 --- CI Closure and CI Failure Recovery

Task ID: T016

Title: CI Closure and CI Failure Recovery

Objective:
Wire CIProvider, remote evidence, closure policy, CI failure
classification, and full recovery routes.

Dependencies:
- T005
- T011
- T013
- T014
- T015

SPEC Traceability:
CI_FAILED classification, CODE recovery, artifact recovery, environment
recovery, CLOSED.

PLAN Traceability:
Sections 50, 51, 95, 102, 104.

Scope:
- Post-push CI monitoring orchestration.
- Closure check.
- CI failure classification.
- CI CODE failure recovery path.
- CI environment and artifact routing.
- Enforcement that corrected CI failures return through validation,
  RE-REVIEW, READY_TO_COMMIT, Human Commit Gate, COMMIT, PUSH, and CI.

Deliverables:
- CI orchestration.
- Closure workflow.
- CI failure recovery routing.

Acceptance Criteria:
- CI GREEN alone does not close the TASK.
- Fake CI cannot satisfy production hosted CI closure.
- CI CODE failure cannot bypass validation, re-review, human gate,
  commit, push, and expected-commit CI.
- Hosted CI GREEN applies only to the current expected commit.

Validation Expectations:
- Workflow scenario tests with FakeCIProvider and local Git remote.
- Tests for wrong-commit CI evidence.
- Tests for CI CODE failure full recovery cycle.
- Tests for CI artifact and environment routing.

Explicit Exclusions / Future-Task Boundary:
- No new CI providers beyond GitHub Actions and Fake CI.
- No provider-specific GitHub implementation; that belongs to T015.

------------------------------------------------------------------------

## T017 --- CLI Integration

Task ID: T017

Title: CLI Integration

Objective:
Provide the thin intent-oriented CLI that invokes Orchestrator actions
without bypassing workflow rules.

Dependencies:
- T001
- T003
- T005
- T011
- T012
- T013
- T016

SPEC Traceability:
Human-selected task, explicit human gates, observable workflow state.

PLAN Traceability:
Sections 7, 8, 74, 75, 76, 77, 80, 85.

Scope:
- `sdd status`.
- Task selection/list commands as applicable to the TASKS artifact.
- Readiness command.
- Implement command.
- Validate command.
- Review command.
- Fix command.
- Approve-commit command.
- Commit command.
- Push command.
- CI command.
- Explainable refused transitions.

Deliverables:
- CLI commands.
- Orchestrator integration.
- User-facing diagnostics for refused transitions.

Acceptance Criteria:
- CLI cannot directly set workflow state.
- Forbidden transitions produce clear diagnostics.
- Human approval remains explicit and candidate-bound.
- CLI respects workspace locking.

Validation Expectations:
- CLI tests for command routing.
- CLI tests for refused transitions.
- CLI tests for invalid configuration.
- CLI tests for workspace lock handling.

Explicit Exclusions / Future-Task Boundary:
- No web dashboard.
- No autonomous task selection.
- No direct state mutation command.

------------------------------------------------------------------------

## T018 --- End-to-End Scenario and Compliance Test Suite

Task ID: T018

Title: End-to-End Scenario and Compliance Test Suite

Objective:
Build the deterministic scenario suite proving the approved SPEC/PLAN
safety cases across the integrated V1 workflow.

Dependencies:
- T001
- T002
- T003
- T004
- T005
- T006
- T007
- T008
- T009
- T010
- T011
- T012
- T013
- T014
- T015
- T016
- T017

SPEC Traceability:
Full lifecycle and negative-path user stories US-16 through US-37.

PLAN Traceability:
Sections 96.1 through 96.6, 102, 103, 104, 105, 106.

Scope:
- Integrated deterministic workflow scenario tests.
- Fake providers for deterministic coverage.
- Local Git repositories and local remotes.
- Persistence restart scenarios.
- Compliance mapping for critical scenarios.

Deliverables:
- End-to-end scenario test suite.
- Compliance coverage report mapping scenarios to SPEC and PLAN
  obligations.

Acceptance Criteria:
- All critical scenarios listed in this document are covered.
- Scenario tests are deterministic.
- Normal scenario suite does not require live Claude Code, Codex, or
  GitHub Actions.
- Integrated tests prove that individual TASK contracts compose into the
  approved lifecycle.

Validation Expectations:
- Automated scenario suite.
- Coverage checks for critical scenario mapping.
- Process crash/recovery tests.
- Integrated closure and negative-path tests.

Explicit Exclusions / Future-Task Boundary:
- No new functionality beyond proving integrated behavior.
- No live provider dependency in the normal suite.

------------------------------------------------------------------------

# 5. SPEC -> TASKS Traceability

``` text
Task selection and dependency readiness:
T005, T017, T018

Sources of truth and recoverability:
T001, T002, T003, T008, T018

Artifact routing and authority boundaries:
T005, T011, T016, T017, T018

Baseline and dirty repository handling:
T004, T018

Candidate identity and invalidation:
T002, T004, T005, T011, T012, T013, T018

READINESS:
T005, T017, T018

IMPLEMENTATION and FIX:
T007, T008, T011, T018

VALIDATION:
T006, T011, T018

Waivers:
T006, T012, T018

Independent REVIEW and RE-REVIEW:
T007, T008, T011, T018

Problem classification and routing:
T005, T011, T016, T018

READY_TO_COMMIT:
T005, T011, T012, T018

Human Commit Gate and approval:
T012, T017, T018

COMMIT:
T012, T013, T018

PUSH and remote state:
T013, T018

Hosted CI and expected commit:
T014, T015, T016, T018

CLOSED:
T005, T013, T016, T018

CLI and human interaction:
T001, T017, T018
```

------------------------------------------------------------------------

# 6. PLAN -> TASKS Traceability

``` text
Python 3.13+ and package foundation:
T001

Pydantic structured models:
T001, T002

Deterministic custom workflow engine:
T005

Hexagonal ports/adapters and dependency direction:
T001, T004, T006, T007, T009, T010, T014, T015

Thin CLI:
T017

Central Orchestrator:
T005, T011, T012, T013, T016, T017

Phase / Condition / NextAction:
T002, T005

Attempt model:
T002, T003, T005

Evidence applicability:
T002, T003, T005

AgentRunner:
T007

FakeAgentRunner:
T007

Claude Code adapter:
T009

Codex adapter:
T010

AgentRole != AgentProvider and role/provider mapping:
T001, T007, T008, T009, T010

ContextBuilder:
T008

Session policies and lost sessions:
T008

Structured agent outputs:
T002, T007, T011

Agent permissions and post-agent verification:
T008, T011

GitRepository:
T004, T013

Baseline:
T004

CandidateSnapshot:
T004

CandidateIdentity:
T004

Dirty-start preflight:
T004

Worktree/index divergence:
T004, T013

Commit tree verification:
T013

ValidationRunner:
T006

ValidationObligation:
T006

Waivers:
T006, T012

ProblemClassifier and RoutingPolicy:
T005, T011, T016

ImplementationReport:
T002, T007, T011

HumanDecision:
T012

Human commit approval:
T012

Commit and push:
T013

Remote verification:
T013

CIProvider:
T014

Fake CI:
T014

GitHub Actions adapter:
T015

CI evidence and expected_commit:
T014, T016

CI closure and failure recovery:
T016

Persistence under .sdd:
T003

Atomic writes:
T003

Append-only reports and events:
T003

Restart reconciliation:
T003, T008, T018

Configuration:
T001

Secrets boundary:
T001, T009, T010, T015

Workspace locking:
T001, T017

Timeouts and bounded retries:
T001, T009, T010, T015

Logs/evidence separation:
T001, T003

Diagnostics:
T001, T017

Testing strategy:
T001, T002, T003, T004, T005, T006, T007, T008, T009, T010, T011,
T012, T013, T014, T015, T016, T017, T018
```

------------------------------------------------------------------------

# 7. Critical Scenario -> TASKS Coverage

``` text
1. Dirty repository before Attempt:
T004, T018

2. Candidate changes after validation:
T005, T006, T018

3. Candidate changes after review:
T004, T005, T011, T018

4. Candidate changes after human approval:
T005, T012, T018

5. Worktree/index divergence:
T004, T013, T018

6. Reviewer unexpectedly modifies repository:
T011, T018

7. Implementer unexpectedly commits:
T011, T018

8. Implementer unexpectedly pushes:
T011, T018

9. Lost implementer session:
T008, T018

10. Lost reviewer session:
T008, T018

11. FAILED validation:
T006, T005, T018

12. NOT_RUN validation:
T006, T012, T018

13. Stale waiver:
T006, T012, T018

14. CI evidence for wrong commit:
T014, T016, T018

15. Remote drift:
T013, T018

16. Process crash/recovery:
T003, T018

17. Non-CODE problem routing:
T005, T011, T016, T018

18. CI CODE failure:
T011, T016, T018

19. Stale ImplementationReport:
T007, T011, T018

20. Missing Codex concrete adapter:
T010, T018

21. Missing Claude Code concrete adapter:
T009, T018

22. Missing GitHub Actions concrete adapter:
T015, T018
```

------------------------------------------------------------------------

# 8. TASKS Decision History

The following TASKS-level decomposition decisions were human-approved
before `tasks.md` consolidation:

``` text
TASKS-D001 = ACCEPTED
V1 decomposition = T001 through T018

TASKS-D002 = ACCEPTED
The proposed dependency graph is the official decomposition basis.

TASKS-D003 = ACCEPTED
T011 / T012 / T013 / T016 remain separate:
- implementation/review orchestration
- human decisions/approval
- commit/push/remote verification
- CI/closure

TASKS-D004 = ACCEPTED
Each TASK contains focused validation.
T018 provides integrated E2E/compliance scenarios.

TASKS-D005 = ACCEPTED
Concrete provider adapters remain separate TASKS:
T009 = Claude Code
T010 = Codex
T015 = GitHub Actions

TASKS-D006 = ACCEPTED
Provider-neutral ports/fakes precede concrete provider adapters:
T007 = AgentRunner + FakeAgentRunner
T014 = CIProvider + Fake CI

TASKS-D007 = ACCEPTED
CODE remains forbidden until TASKS_READY.
```

This decision history is not an independent TASKS review.

------------------------------------------------------------------------

# 9. TASKS Review Finding History

The independent TASKS review produced:

``` text
BLOCKER = 0
IMPORTANT = 1
MINOR = 0

Final gate = TASKS_NEEDS_FIXES
Required routing = TASKS_FIX
```

Finding:

``` text
TASKS-R001
Severity = IMPORTANT
Routing = TASKS_FIX
Status = RESOLVED

Correction:
T011 added as explicit dependency of T016.

Independent TASKS RE-REVIEW:
TASKS-R001 = RESOLVED
Critical Scenario S18 = PASS
Cross-Task Scenario K = PASS
New findings = NONE

Current unresolved findings:

BLOCKER = 0
IMPORTANT = 0
MINOR = 0

Required Routing = NONE

Final Gate = TASKS_READY
```

This preserves TASKS-R001 as historical review evidence and records the
completed independent re-review result.

------------------------------------------------------------------------

# 10. TASKS Review Requirements

Before TASKS may become TASKS_READY, an independent reviewer shall
verify at minimum:

-   every approved SPEC responsibility needed for V1 is assigned to one
    or more TASKS;
-   every approved PLAN responsibility needed for V1 is assigned to one
    or more TASKS;
-   dependencies are explicit and machine-friendly;
-   task number is not used as readiness authority;
-   acceptance criteria are observable without dictating unnecessary
    CODE mechanics;
-   validation expectations are meaningful for each TASK;
-   future-task boundaries are explicit enough for later CODE reviews;
-   concrete provider adapters required by PLAN-097 and PLAN-098 are
    represented;
-   no TASK introduces new PRODUCT behavior or new ARCHITECTURE.

------------------------------------------------------------------------

# 11. Current TASKS State

Current status:

``` text
SPEC = SPEC_READY
PLAN = PLAN_READY

TASKS decomposition discovery = COMPLETE
TASKS decomposition proposal = HUMAN_APPROVED

TASKS-D001 through TASKS-D007 = ACCEPTED

tasks.md consolidation = COMPLETE

TASKS status = TASKS_READY

Independent TASKS Review = COMPLETED

TASKS-R001 = RESOLVED

Independent TASKS RE-REVIEW = COMPLETED

Current unresolved findings:

BLOCKER = 0
IMPORTANT = 0
MINOR = 0

Required Routing = NONE

Final Gate = TASKS_READY

CODE phase = AUTHORIZED

Initial ready TASK = T001
```

------------------------------------------------------------------------

# End of TASKS
