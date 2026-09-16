# SDD Agent V1 --- Architecture Plan

-   **Product:** SDD Agent
-   **Product Version:** V1 --- Semi-Automatic
-   **Plan Revision:** V1
-   **Phase:** PLAN
-   **Specification Status:** SPEC_READY
-   **Plan Status:** PLAN_READY
-   **Encoding:** UTF-8

------------------------------------------------------------------------

# 1. Purpose

This document defines the technical architecture for SDD Agent V1.

The authoritative product behavior is defined by `spec.md`.

This PLAN translates that approved product contract into an
implementable architecture without decomposing the work into
implementation TASKS.

The lifecycle remains:

``` text
SPEC -> PLAN -> TASKS -> CODE -> VALIDATION -> REVIEW -> COMMIT -> PUSH -> CI
```

At the artifact level:

``` text
SPEC_READY
    |
    v
PLAN
    |
    +-- architecture
    +-- technical boundaries
    +-- components
    +-- persistence
    +-- integrations
    +-- recovery
    |
    v
PLAN_REVIEW
    |
    v
PLAN_READY
    |
    v
TASKS
```

No implementation TASK decomposition is defined by this document.

------------------------------------------------------------------------

# 2. Architectural Goals

SDD Agent V1 shall provide a local semi-automatic orchestrator capable
of enforcing the approved SDD lifecycle.

The architecture shall prioritize:

1.  deterministic workflow gates;
2.  explicit human authority;
3.  exact candidate identity;
4.  recoverability without conversation history;
5.  provider-neutral agent execution;
6.  independent review;
7.  durable workflow evidence;
8.  Git integrity;
9.  explicit failure classification and routing;
10. simple local operation;
11. testability without requiring live LLM calls;
12. explainability of every allowed or refused transition.

The architecture shall avoid unnecessary distributed-system complexity.

------------------------------------------------------------------------

# 3. Technology Stack

## 3.1 Language

SDD Agent V1 shall use:

``` text
Python 3.13+
```

Python is selected because V1 is primarily a local orchestration
application interacting with:

-   subprocesses;
-   Git;
-   filesystem state;
-   JSON;
-   YAML;
-   Claude Code CLI;
-   Codex CLI;
-   validation commands;
-   hosted CI APIs.

The architecture does not require a server-side application framework.

------------------------------------------------------------------------

## 3.2 Structured Models

Pydantic shall be used for:

-   configuration models;
-   persistent state models;
-   reports;
-   evidence metadata;
-   human decisions;
-   validation results;
-   review findings;
-   classification results;
-   agent requests and results.

Persistent or agent-produced structured data shall not be trusted before
model validation.

------------------------------------------------------------------------

## 3.3 Workflow Technology

SDD Agent V1 shall implement its own deterministic workflow engine.

LangGraph shall not be the primary workflow engine for V1.

The central SDD lifecycle is predominantly governed by deterministic
rules such as:

``` text
BLOCKER > 0 -> review gate fails

IMPORTANT > 0 -> review gate fails

candidate changed -> dependent evidence invalidated

READY_TO_COMMIT not applicable -> Human Commit Gate forbidden

CI_FAILED -> CLASSIFY before ROUTE
```

LLMs participate in selected workflow activities but do not own the
state machine.

------------------------------------------------------------------------

# 4. Architectural Style

SDD Agent shall use a lightweight hexagonal architecture.

Conceptually:

``` text
                         CLI
                          |
                          v
                    Orchestrator
                          |
             +------------+------------+
             |                         |
             v                         v
       Workflow Core              ContextBuilder
             |
       Gate Policies
             |
       Routing Policies
             |
       Domain Models
             |
    +--------+----------+-----------+-----------+
    |                   |           |           |
    v                   v           v           v
AgentRunner        GitRepository ValidationRunner CIProvider
    |                   |                       |
+---+---+            Git CLI                Hosted CI
|       |
Claude  Codex
```

External systems shall be accessed through ports.

Provider-specific behavior shall remain in adapters.

------------------------------------------------------------------------

# 5. Core Architectural Rule

The most important architectural rule is:

> External tools and AI agents produce facts, evidence and analysis. The
> deterministic SDD Core owns workflow authorization.

The architecture therefore follows:

``` text
External system / Agent
          |
          v
        FACTS
          |
          v
Structured Evidence
          |
          v
Classification
          |
          v
Deterministic Routing
          |
          v
Deterministic Gates
          |
          v
Authorized Transition
          |
          v
Persistent Workflow State
```

An LLM statement such as:

``` text
Everything looks good and is ready to commit.
```

has no direct workflow authority.

------------------------------------------------------------------------

# 6. Main Components

The V1 architecture contains the following principal components:

``` text
CLI
Orchestrator
Workflow Core
Gate Policies
Routing Policy
Problem Classifier
Context Builder
Agent Runner
Git Repository
Validation Runner
CI Provider
Persistence
Configuration
Workspace Lock
```

------------------------------------------------------------------------

# 7. CLI

The CLI is the primary V1 human interface.

It shall remain thin.

It translates user intentions into requests to the Orchestrator but does
not implement workflow rules.

Conceptual commands include:

``` text
sdd status

sdd task list
sdd task select <task>

sdd readiness
sdd implement
sdd validate
sdd review
sdd fix

sdd approve-commit
sdd commit
sdd push
sdd ci
```

The final command syntax may be refined during implementation without
changing the architecture.

Commands shall express SDD intentions rather than permit direct state
manipulation.

Commands such as:

``` text
sdd state set READY_TO_COMMIT
```

shall not exist.

------------------------------------------------------------------------

# 8. Orchestrator

The Orchestrator is the central application service.

All workflow transitions pass through it.

Adapters shall never directly change workflow state.

The Orchestrator is responsible for:

-   loading configuration;
-   loading current workflow state;
-   reconciling persisted expectations with repository reality;
-   invoking policies;
-   checking gates;
-   launching external operations;
-   receiving structured results;
-   applying routing;
-   persisting significant facts;
-   determining the next authorized action.

Conceptually:

``` text
CLI / External Result
        |
        v
   Orchestrator
        |
        +--> reconcile
        +--> evaluate policies
        +--> authorize action
        +--> invoke port
        +--> validate result
        +--> persist evidence
        +--> recompute gates
```

------------------------------------------------------------------------

# 9. Workflow Representation

The implementation shall not create one enormous enum containing every
conceptual SPEC label.

Three concepts shall be separated.

## 9.1 Phase

A phase represents where the active attempt is in its lifecycle.

Conceptual phases include:

``` text
READINESS
IMPLEMENTATION
VALIDATION
REVIEW
FIX
RE_REVIEW
READY_TO_COMMIT
COMMIT
PUSH
CI
CLOSED
ABANDONED
```

The exact Python representation belongs to implementation.

------------------------------------------------------------------------

## 9.2 Condition

Conditions represent situations affecting progression.

Examples:

``` text
SPEC_REQUIRED
PLAN_REQUIRED
TASKS_REQUIRED
FIX_REQUIRED
ENVIRONMENT_BLOCKED
REPOSITORY_MISMATCH
```

A condition is not necessarily a workflow phase.

------------------------------------------------------------------------

## 9.3 Next Authorized Action

The state exposes what the user or orchestrator is currently allowed or
required to do.

Example:

``` text
phase:
  VALIDATION

condition:
  ENVIRONMENT_BLOCKED

next_authorized_action:
  RESOLVE_ENVIRONMENT
```

This prevents conceptual SPEC vocabulary from creating a combinatorial
state explosion.

------------------------------------------------------------------------

# 10. Attempt Model

A TASK and an execution attempt are separate concepts.

Conceptually:

``` text
T032
 |
 +-- attempt-001
 |      ABANDONED
 |
 +-- attempt-002
        ACTIVE
```

An Attempt is the durable execution container for:

-   baseline;
-   candidate;
-   readiness;
-   validation;
-   waivers;
-   agent sessions;
-   reviews;
-   findings;
-   human decisions;
-   repository mismatches;
-   commit;
-   push;
-   CI;
-   closure.

`RESTART` creates a new Attempt.

It does not erase the previous Attempt.

V1 allows only one active execution of a TASK in the project context.

------------------------------------------------------------------------

# 11. Deterministic Gate Policies

Critical gates shall be implemented as deterministic policies and should
be pure functions whenever practical.

Examples include:

``` text
ReadinessPolicy
ReadyForReviewPolicy
ReviewGatePolicy
ReadyToCommitPolicy
HumanCommitGatePolicy
CommitAuthorizationPolicy
ClosurePolicy
```

Example conceptual rule:

``` python
review_passes =
    blocker_count == 0
    and important_count == 0
```

Commit authorization follows:

``` text
COMMIT_ALLOWED(candidate) =
    READY_TO_COMMIT(candidate).applicable
    AND
    HUMAN_APPROVAL(candidate).applicable
```

Both proofs must refer to the exact same current candidate.

Policies shall be unit-testable without invoking Claude, Codex or hosted
CI.

------------------------------------------------------------------------

# 12. Evidence Applicability

Evidence used by a gate shall contain sufficient identity to determine
whether it applies to the current workflow context.

A shared conceptual context includes, when applicable:

``` text
task_id
attempt_id
candidate_id
artifact_contract_identity
```

Different evidence types may require additional identifiers.

Examples:

``` text
ReadinessReport
ValidationReport
ReviewReport
ValidationWaiver
HumanDecision
CIResult
```

Historical evidence remains stored after invalidation but no longer
satisfies current gates.

------------------------------------------------------------------------

# 13. Agent Architecture

## 13.1 AgentRunner Port

The Core shall interact with AI coding agents through a provider-neutral
`AgentRunner` port.

Conceptually:

``` text
SDD Core
   |
   v
AgentRunner
   |
   +-- ClaudeCodeRunner
   |
   +-- CodexRunner
```

------------------------------------------------------------------------

# 14. Agent Role vs Provider

Role and provider shall be distinct.

Conceptual roles:

``` text
READINESS
IMPLEMENTER
REVIEWER
```

Conceptual providers:

``` text
CLAUDE_CODE
CODEX
```

A project may therefore configure:

``` text
READINESS   -> Codex
IMPLEMENTER -> Claude Code
REVIEWER    -> Codex
```

without hard-coding those relationships into the workflow.

------------------------------------------------------------------------

# 15. Agent Request and Result

Agent execution shall use structured application contracts.

Conceptually:

``` text
AgentRequest
 ├── role
 ├── provider
 ├── repository
 ├── task
 ├── attempt
 ├── context
 ├── instructions
 ├── expected_report_type
 └── session_policy
```

and:

``` text
AgentResult
 ├── execution_status
 ├── structured_report
 ├── session_reference
 └── diagnostics
```

The exact Pydantic schemas belong to implementation.

------------------------------------------------------------------------

# 16. Agent Session Policies

## 16.1 Initial Review

Initial REVIEW requires a new independent reviewer session.

The reviewer shall not inherit implementer conversational history.

Its context is reconstructed from authorized durable sources.

------------------------------------------------------------------------

## 16.2 FIX

FIX should reuse the active implementer session when available.

This is an efficiency optimization, not a correctness requirement.

------------------------------------------------------------------------

## 16.3 RE-REVIEW

RE-REVIEW should reuse the reviewer session that generated the findings
when available.

------------------------------------------------------------------------

## 16.4 Lost Sessions

Loss of an agent session shall not make the workflow unrecoverable.

A replacement session reconstructs its context from:

-   repository;
-   SPEC;
-   PLAN;
-   TASKS;
-   Attempt state;
-   exact candidate;
-   applicable reports;
-   findings;
-   required evidence.

Conversation history shall never be required as durable proof.

------------------------------------------------------------------------

# 17. Context Builder

A centralized `ContextBuilder` shall construct role-specific context.

The goal is:

> minimal sufficient authorized context.

It shall avoid giant prompts containing unrelated project history.

For IMPLEMENTER, context may include:

``` text
relevant SPEC
relevant PLAN
TASK contract
relevant repository code
baseline/candidate information
validation requirements
```

For REVIEWER:

``` text
SPEC
PLAN
TASK
baseline
exact candidate
candidate diff/content
validation evidence
applicable waivers
```

It shall not include implementer conversation history.

RE-REVIEW additionally includes:

``` text
previous findings
fix evidence
current candidate
```

------------------------------------------------------------------------

# 18. Structured Agent Outputs

Critical agent outputs shall be structured and validated.

For example, a review report conceptually contains:

``` text
candidate identity
findings
severity
routing
evidence
rationale
```

Severity is constrained to:

``` text
BLOCKER
IMPORTANT
MINOR
```

The Orchestrator shall reject or recover from structurally invalid
critical reports rather than infer workflow decisions from arbitrary
prose.

------------------------------------------------------------------------

# 19. Agent Permissions

Permissions differ by role.

## 19.1 IMPLEMENTER / FIX

Allowed:

``` text
read repository
modify candidate
run validations
inspect Git
```

Forbidden:

``` text
commit
push
silently modify approved SPEC/PLAN/TASKS
```

------------------------------------------------------------------------

## 19.2 REVIEWER

Allowed:

``` text
read repository
inspect diff
inspect evidence
run permitted inspection/tests
```

Forbidden:

``` text
modify candidate
commit
push
```

Where provider capabilities permit, adapters shall technically restrict
permissions.

The Core shall still verify repository state after execution.

------------------------------------------------------------------------

# 20. Workspace Verification After Agent Execution

Prompt instructions alone are insufficient.

The Orchestrator shall verify Git state after agent execution.

For a reviewer:

``` text
candidate_before = A

REVIEW

candidate_after must equal A
```

Unexpected candidate modification produces repository mismatch handling.

After implementation, unexpected commit or push activity shall also be
detected.

------------------------------------------------------------------------

# 21. GitRepository Port

Git operations shall be exposed through a domain-oriented
`GitRepository` port.

A Git CLI adapter shall provide the V1 implementation.

The Core shall not embed raw Git commands throughout workflow logic.

------------------------------------------------------------------------

# 22. Baseline

Every Attempt establishes an exact immutable Git baseline.

Conceptually:

``` text
baseline_sha = full Git commit SHA
```

A branch name alone is not a baseline identity because the branch can
move.

Unexpected incompatible baseline changes produce repository mismatch
handling.

------------------------------------------------------------------------

# 23. Candidate Identity Before Commit

Before COMMIT, the candidate does not necessarily have a commit SHA.

The candidate is therefore defined by an explicit `CandidateSnapshot`,
independent from Git staging/index state.

Conceptually:

``` text
CandidateSnapshot
 =
authorized repository worktree state
relative to baseline
```

The Git index is not the authority that defines the candidate.

A reviewer must never be able to review worktree Candidate A while a
different staged/index state B is later committed.

The snapshot shall deterministically represent all candidate changes
relative to the baseline, including at minimum:

``` text
path
entry type
content identity
file mode
deletion state
```

Tracked modifications and deletions are included.

Binary files are handled through their content identity and are not
dependent on textual diff rendering.

Rename detection is not part of candidate identity. A rename may be
represented canonically as:

``` text
delete old/path
+
add new/path
```

so Git rename heuristics cannot change candidate identity.

Ignored files are not implicitly part of the candidate. They may
contribute to environment or validation evidence where appropriate, but
they do not silently become content authorized for COMMIT.

All untracked files that are not ignored by Git are included in the
`CandidateSnapshot`.

Conceptually:

``` text
untracked AND not ignored by Git
-> INCLUDED in CandidateSnapshot

untracked AND ignored by Git
-> EXCLUDED from CandidateSnapshot
```

This is the deterministic V1 candidate-inclusion rule. SDD Agent does
not attempt to infer whether an untracked file is "relevant" to the
TASK.

Therefore, a non-ignored scratch file, generated file, new source file,
or other untracked file present in the worktree is part of the
candidate. If such a file must not belong to the candidate, it must be
removed, relocated, or excluded by the project's Git ignore rules before
the candidate can satisfy sensitive gates.

A change to Git ignore rules that changes whether a worktree file is
included also changes the `CandidateSnapshot` and therefore
`CandidateIdentity`.

For example:

``` text
Candidate A:
.gitignore excludes tmp.txt
-> tmp.txt excluded from CandidateSnapshot

.gitignore changes:
tmp.txt is no longer ignored
-> tmp.txt included in CandidateSnapshot

Candidate A != Candidate B
```

The candidate boundary is therefore deterministic and does not depend on
an LLM or TASKS/CODE deciding which untracked files are relevant.

Conceptually:

``` text
CandidateIdentity
 ├── baseline_sha
 └── content_fingerprint(CandidateSnapshot)
```

The fingerprint is calculated from a canonical representation of the
CandidateSnapshot and is independent from the current staging/index
arrangement.

The exact hash primitive, byte serialization and Git commands belong to
CODE, but TASKS/CODE must preserve these architectural properties:

``` text
same baseline + same canonical CandidateSnapshot
-> same CandidateIdentity

different candidate content/mode/path/deletion
-> different CandidateIdentity
```

This CandidateIdentity is the identity to which validation, review,
READY_TO_COMMIT and human approval are bound.

# 24. Candidate Recalculation

Candidate identity shall be recalculated before sensitive gates and
actions.

At minimum this applies before:

``` text
VALIDATION evidence acceptance
REVIEW
READY_TO_COMMIT
Human Commit Gate
COMMIT
```

Example:

``` text
review candidate = A

manual modification

current candidate = B

Human Commit Gate -> forbidden
```

Evidence associated with A remains historical but is not applicable to
B.

Recalculation reconstructs the actual current `CandidateSnapshot`; it
does not merely inspect a previously recorded fingerprint or the Git
index.

Any mismatch between the expected candidate and the reconstructed
current snapshot invalidates candidate-bound proofs and routes through
repository mismatch handling where applicable.

------------------------------------------------------------------------

# 25. Commit Restrictions

Implementer and reviewer agents shall not perform COMMIT or PUSH.

COMMIT belongs to the orchestrated lifecycle.

Before COMMIT, the Orchestrator verifies:

``` text
current candidate identity
READY_TO_COMMIT applicability
human approval applicability
same exact candidate
repository integrity
```

There shall be no generic force option allowing these gates to be
bypassed.

Immediately before COMMIT, the Orchestrator reconstructs the current
CandidateSnapshot and recalculates CandidateIdentity.

The commit operation must be constructed from the exact authorized
CandidateSnapshot rather than trusting arbitrary pre-existing
staging/index state.

After the commit is created, the Orchestrator verifies that the
resulting commit tree corresponds exactly to the authorized
CandidateSnapshot relative to the established baseline.

Conceptually:

``` text
authorized CandidateSnapshot A
        |
        v
COMMIT
        |
        v
created commit tree
        |
        v
corresponds exactly to A ?
   |              |
  NO             YES
   |              |
   v              v
REPOSITORY_     ExpectedCommit
MISMATCH        established
```

A commit containing omitted candidate content, additional staged
content, or otherwise differing from the authorized CandidateSnapshot is
not accepted as the expected commit.

------------------------------------------------------------------------

# 26. Post-Commit Identity

After successful COMMIT, workflow identity pivots from candidate
fingerprint to an immutable expected Git commit SHA.

Conceptually:

``` text
candidate fingerprint
        |
      COMMIT
        |
        v
ExpectedCommit SHA
```

The Orchestrator verifies that the created commit corresponds to the
candidate authorized for commit.

PUSH and hosted CI evidence shall then refer to this expected commit.

------------------------------------------------------------------------

# 27. Expected Remote Target

The workflow shall persist an explicit expected remote target.

Conceptually:

``` text
remote
target ref / branch
expected commit SHA
```

Example:

``` text
remote = origin
target = main
expected_commit = abc123...
```

A commit merely existing somewhere on a remote is insufficient.

------------------------------------------------------------------------

# 28. Remote Verification

Successful execution of `git push` and proof of expected remote state
are separate facts.

After PUSH, SDD Agent shall verify that the expected remote target
references the expected commit.

Conceptually:

``` text
expected remote target
        |
        v
observed remote commit
        |
        =
expected commit
```

Unexpected drift is treated as repository mismatch.

------------------------------------------------------------------------

# 29. Repository Mismatch

Repository mismatch shall be represented as structured workflow evidence
rather than a generic exception.

Potential categories include:

``` text
BASELINE_CHANGED
CANDIDATE_CHANGED
ARTIFACT_CHANGED
REMOTE_DRIFT
UNEXPECTED_COMMIT
```

The final set may be refined during implementation.

A mismatch record shall contain sufficient information such as:

``` text
expected
actual
detected_at
affected context/evidence
```

Mismatch causes blocking until explicit resolution.

Supported conceptual exits remain:

``` text
RESUME
RESTART
ABANDON
```

A new incompatible repository state shall not silently become the
baseline of the current Attempt.

------------------------------------------------------------------------

# 30. ValidationRunner Port

Project validation shall be executed through a `ValidationRunner` port.

The workflow Core shall not depend on Maven, Gradle, pytest, npm or
another particular validation technology.

Adapters/execution strategies may execute project-specific commands.

------------------------------------------------------------------------

# 31. Validation Discovery

Validation requirement discovery and validation execution are separate
responsibilities.

The system first determines:

``` text
What validations are required?
```

and only then executes them.

Validation requirements derive from applicable project contracts and
configuration.

An implementer may add validation but shall not silently remove required
validation.

------------------------------------------------------------------------

# 32. Validation Obligation

Every required validation shall be identifiable.

Conceptually:

``` text
ValidationObligation
 ├── id
 ├── description
 ├── execution reference
 ├── required
 └── waiver policy
```

This identity allows validation results and waivers to reference the
exact obligation.

------------------------------------------------------------------------

# 33. Validation Result

Validation execution shall produce a structured result.

Core statuses are:

``` text
PASSED
FAILED
NOT_RUN
```

Conceptually:

``` text
ValidationResult
 ├── obligation_id
 ├── candidate_id
 ├── status
 ├── command/execution reference
 ├── exit_code
 ├── timestamps
 └── evidence reference
```

Execution diagnostics such as timeout or missing executable shall be
retained so the failure can be classified correctly.

------------------------------------------------------------------------

# 34. Validation Failure Classification

A validation execution failure does not automatically mean CODE failure.

The flow is:

``` text
Validation evidence
       |
       v
CLASSIFY
       |
 +-----+------+----------+----------+
 |            |          |          |
CODE      ENVIRONMENT PRODUCT  ARCHITECTURE/TASKS
```

The resulting classification determines routing.

------------------------------------------------------------------------

# 35. Validation Waiver

A waiver is a separate durable object.

A waiver never changes:

``` text
NOT_RUN
```

into:

``` text
PASSED
```

Gate evaluation may accept:

``` text
PASSED
```

or, only where permitted by the SPEC:

``` text
NOT_RUN
+
eligible ENVIRONMENT cause
+
applicable human waiver
```

`FAILED` is never waivable.

------------------------------------------------------------------------

# 36. Waiver Applicability

A waiver shall be bound to its precise context.

Conceptually this includes:

``` text
task
attempt
candidate
validation obligation
environment classification
validation evidence
artifact contract identity
human decision
reason
```

A relevant candidate, contract, evidence or cause change invalidates its
applicability.

The obsolete waiver remains historical.

Waivers are not reusable across Attempts.

Hosted CI GREEN required for closure is non-waivable.

------------------------------------------------------------------------

# 37. Validation Evidence Storage

Structured summaries and raw execution evidence shall be stored
separately.

Example conceptual organization:

``` text
ValidationReport
      |
      +--> structured result
      |
      +--> evidence reference
                  |
                  +--> stdout
                  +--> stderr
                  +--> execution metadata
```

Large command logs shall not be embedded directly into the primary
workflow state.

------------------------------------------------------------------------

# 38. Reviewer Validation Package

The Context Builder shall provide the reviewer an explicit validation
package containing:

``` text
expected validations
executed validations
results
NOT_RUN validations
applicable waivers
evidence references
candidate identity
```

The reviewer shall not need implementer conversation history to
reconstruct validation status.

------------------------------------------------------------------------

# 39. Review Model

The reviewer evaluates the exact candidate against:

``` text
SPEC
PLAN
TASK contract
baseline
candidate
validation evidence
relevant repository integration context
```

Review findings shall be structured.

Conceptually:

``` text
Finding
 ├── id
 ├── severity
 ├── route
 ├── summary
 ├── evidence
 └── rationale
```

Severity:

``` text
BLOCKER
IMPORTANT
MINOR
```

Routing:

``` text
PRODUCT
ARCHITECTURE
TASKS
CODE
ENVIRONMENT
```

where applicable.

------------------------------------------------------------------------

# 40. Review Gate

The review gate is deterministic.

``` text
BLOCKER == 0
AND
IMPORTANT == 0
```

is required for review acceptance.

MINOR findings remain visible but do not independently block
READY_TO_COMMIT.

Reviewer prose cannot override this calculation.

------------------------------------------------------------------------

# 41. FIX and RE-REVIEW

A blocking CODE finding routes to FIX.

Candidate modification during FIX invalidates candidate-dependent
proofs.

The flow is:

``` text
FIX
 |
 v
VALIDATION
 |
 v
RE_REVIEW
```

RE-REVIEW verifies previous findings and relevant regressions.

Human-requested modifications after READY_TO_COMMIT follow
classification before routing.

------------------------------------------------------------------------

# 42. ProblemClassifier

Problem classification shall be represented by an explicit service.

Core classifications include:

``` text
PRODUCT
ARCHITECTURE
TASKS
CODE
ENVIRONMENT
REPOSITORY_MISMATCH
```

The applicable set may vary by problem type.

Classification describes the nature of a problem.

It does not itself decide the next workflow action.

------------------------------------------------------------------------

# 43. Deterministic and Agent-Assisted Classification

Classification shall be deterministic where the evidence permits.

Semantic classification may use an AI agent where necessary.

Example:

``` text
Evidence
   |
   v
ProblemClassifier
   |
   +-- deterministic rule
   |
   +-- agent-assisted analysis
```

Regardless of how classification is produced, it must become a validated
structured result before routing.

------------------------------------------------------------------------

# 44. Classification Report

Classification shall be durable and explainable.

Conceptually:

``` text
ClassificationReport
 ├── problem_id
 ├── classification
 ├── evidence
 ├── rationale
 ├── workflow/candidate context
 └── classifier metadata
```

This allows status output to explain why execution is blocked or routed.

------------------------------------------------------------------------

# 45. RoutingPolicy

Classification and routing shall be separate.

Conceptually:

``` text
PRODUCT      -> SPEC_REQUIRED
ARCHITECTURE -> PLAN_REQUIRED
TASKS        -> TASKS_REQUIRED
CODE         -> FIX_REQUIRED
ENVIRONMENT  -> ENVIRONMENT_BLOCKED
```

Repository mismatch follows its dedicated blocking/resolution rules.

Routing is deterministic.

An agent cannot override the route through free-form prose.

------------------------------------------------------------------------

# 46. Artifact Return

When workflow routes to:

``` text
SPEC_REQUIRED
PLAN_REQUIRED
TASKS_REQUIRED
```

the active CODE cycle is suspended.

After the required human decision and approved authoritative artifact
update:

``` text
artifact changes
      |
      v
dependent evidence invalidated
      |
      v
READINESS
```

The workflow does not return directly to FIX.

------------------------------------------------------------------------

# 47. CIProvider Port

Hosted CI shall be accessed through a provider-neutral `CIProvider`.

Conceptually:

``` text
CIProvider
   |
   +-- GitHubActionsAdapter
   |
   +-- future providers
```

V1 may implement only the provider required by the initial project.

------------------------------------------------------------------------

# 48. CI Identity

CI evidence must reference the expected commit SHA.

A CI GREEN result for commit A cannot satisfy closure for commit B.

------------------------------------------------------------------------

# 49. CI Status Model

The internal CI model shall normalize provider-specific statuses.

Conceptual statuses:

``` text
PENDING
RUNNING
GREEN
FAILED
CANCELLED
NOT_FOUND
```

Provider adapters translate external vocabulary into this model.

------------------------------------------------------------------------

# 50. CI Monitoring

V1 shall use simple polling.

No webhook server, queue or distributed callback infrastructure is
required.

Conceptually:

``` text
PUSH
 |
 v
CIProvider
 |
 +-- PENDING
 +-- RUNNING
 +-- GREEN
 +-- FAILED
```

Polling intervals and timeout are configurable.

------------------------------------------------------------------------

# 51. CI_FAILED

CI failure never routes directly to FIX.

The required sequence begins:

``` text
CI_FAILED
    |
    v
CLASSIFY
```

Then:

``` text
CODE         -> FIX
PRODUCT      -> SPEC_REQUIRED
ARCHITECTURE -> PLAN_REQUIRED
TASKS        -> TASKS_REQUIRED
ENVIRONMENT  -> ENVIRONMENT_BLOCKED
```

------------------------------------------------------------------------

# 52. CI CODE Recovery

A CODE correction after CI failure creates a new candidate requiring a
new proof cycle.

``` text
CI_FAILED
   |
CLASSIFY = CODE
   |
   v
FIX
   |
   v
VALIDATION
   |
   v
RE_REVIEW
   |
   v
READY_TO_COMMIT
   |
   v
HUMAN COMMIT GATE
   |
   v
COMMIT
   |
   v
PUSH
   |
   v
HOSTED CI
```

Previous review or approval evidence cannot authorize the changed
candidate.

------------------------------------------------------------------------

# 53. CI Environment Recovery

Environment-classified CI failure does not automatically create a new
CODE candidate.

The workflow remains blocked until the environment issue is resolved.

A new applicable CI verification for the current expected commit is then
required.

CI GREEN remains non-waivable for CLOSED.

------------------------------------------------------------------------

# 54. Human Decisions

Human decisions shall be represented as structured durable evidence.

Conceptually:

``` text
HumanDecision
 ├── decision_id
 ├── decision_type
 ├── task_id
 ├── attempt_id
 ├── context
 ├── choice
 ├── timestamp
 └── applicability
```

Relevant decision categories include:

-   PRODUCT;
-   ARCHITECTURE;
-   TASKS;
-   validation waiver;
-   repository mismatch resolution;
-   commit approval;
-   restart;
-   abandon.

------------------------------------------------------------------------

# 55. Human Commit Gate

Human Commit Gate is an interaction gate, not an independent candidate
maturity state.

Entry is allowed only when the exact current candidate has applicable
READY_TO_COMMIT.

Conceptually:

``` text
current candidate = A
       |
READY_TO_COMMIT(A)?
       |
       +-- NO --> gate entry forbidden
       |
       +-- YES
              |
              v
       Human Commit Gate
```

The user shall be shown relevant candidate, validation, review, MINOR
findings, waiver and repository information before approval.

------------------------------------------------------------------------

# 56. Commit Approval

Human commit approval is bound to the exact candidate.

Conceptually:

``` text
HumanApproval
    candidate_id = A
```

It is not a global:

``` text
approved = true
```

If candidate A changes to B, approval A remains historical but becomes
non-applicable.

------------------------------------------------------------------------

# 57. Approval and Commit Separation

Human approval and Git commit remain separate operations.

``` text
READY_TO_COMMIT
       |
approve-commit
       |
HumanApproval
       |
commit
```

Immediately before COMMIT, the Orchestrator recalculates candidate
identity and both required proofs.

------------------------------------------------------------------------

# 58. No Generic Gate Bypass

V1 shall not provide a generic:

``` text
--force
```

mechanism capable of bypassing deterministic gates.

Explicit exception mechanisms defined by the SPEC, such as eligible
validation waivers, remain available through their own controlled
workflows.

Human authority does not mean arbitrary mutation of gate semantics.

------------------------------------------------------------------------

# 59. Task Selection

SDD Agent may discover and present candidate executable TASKS.

Selection remains explicitly human.

Conceptually:

``` text
sdd task list

T031 CLOSED
T032 EXECUTABLE
T033 BLOCKED
T034 EXECUTABLE
```

The user selects:

``` text
sdd task select T032
```

Before starting the Attempt, repository and dependency preconditions are
checked.

For V1, creation of a new Attempt requires an acceptable clean
repository state.

The repository preflight occurs before the Attempt becomes active and
before its baseline is established. It detects at minimum pre-existing
tracked modifications, staged/index changes, deletions, and untracked
files that could otherwise be confused with TASK work.

If such pre-existing changes are present:

``` text
TASK selected
     |
     v
repository preflight
     |
     v
dirty pre-existing state
     |
     v
START BLOCKED
```

SDD Agent V1 shall not automatically:

``` text
stash
commit
delete
reset
or adopt
```

those pre-existing changes.

The human resolves the dirty state outside the new Attempt and retries
TASK selection. No pre-existing dirty state may be silently incorporated
into the candidate of the new Attempt.

Only after the repository satisfies the start precondition may the
Orchestrator establish the baseline SHA and create/activate the Attempt.

Task numeric order shall not be treated as dependency order.

------------------------------------------------------------------------

# 60. Dependency Handling

Mandatory dependencies are evaluated from the TASK contract.

Unless explicitly specified otherwise by the contract, dependency
satisfaction requires the dependency TASK to be CLOSED.

An incorrect or missing TASK dependency discovered during READINESS
routes to TASKS_REQUIRED rather than being silently repaired.

------------------------------------------------------------------------

# 61. STATUS

`sdd status` shall be the primary workflow diagnostic command.

It shall not merely print persisted `current.json`.

It reconciles:

``` text
persisted expected state
+
actual repository
+
applicable evidence
+
recomputed gates
```

Conceptual output:

``` text
Task:       T032
Attempt:    002
Phase:      REVIEW

Baseline:   ...
Candidate:  ...

Validation:
  3 PASSED
  1 NOT_RUN + applicable waiver

Review:
  BLOCKER:   1
  IMPORTANT: 0
  MINOR:     2

Condition:
  FIX_REQUIRED

Next authorized action:
  FIX
```

------------------------------------------------------------------------

# 62. Explainable Command Refusal

A refused action shall explain why it is refused.

Example:

``` text
COMMIT NOT AUTHORIZED

READY_TO_COMMIT:
  applicable

Human approval:
  missing

Required action:
  approve-commit
```

Another example:

``` text
COMMIT NOT AUTHORIZED

READY_TO_COMMIT:
  stale

Reason:
  candidate changed after review

Required action:
  VALIDATION
```

This behavior supports both usability and the pedagogical objective of
SDD Agent.

------------------------------------------------------------------------

# 63. Persistent Operational State

Operational state shall be stored locally under:

``` text
.sdd/
```

The repository remains the source of truth for authoritative SDD
artifacts and code.

`.sdd/` contains workflow execution state and evidence.

------------------------------------------------------------------------

# 64. Persistence Strategy

V1 shall use local JSON-based persistence rather than PostgreSQL or
another database.

Reasons include:

-   one local project;
-   one active task execution;
-   one orchestrator;
-   transparent inspection;
-   simple backup and debugging.

Pydantic validates persistent models.

Writes of mutable state shall be atomic.

Conceptually:

``` text
new model
   |
validate
   |
write temporary file
   |
flush
   |
atomic replace
   |
current file
```

------------------------------------------------------------------------

# 65. Persistence Layout

Conceptual layout:

``` text
.sdd/
├── current.json
│
└── attempts/
    └── T032/
        └── 002/
            ├── attempt.json
            ├── events.jsonl
            ├── readiness/
            ├── validation/
            ├── reviews/
            ├── decisions/
            └── evidence/
```

Exact filenames may be refined during implementation while preserving
these responsibilities.

------------------------------------------------------------------------

# 66. Current State vs History

Mutable current state and durable history shall remain distinct.

`current.json` answers:

``` text
Where is the workflow now?
```

Attempt evidence answers:

``` text
What happened and what proves it?
```

`current.json` is therefore a current snapshot/pointer, not absolute
proof that a gate remains applicable.

------------------------------------------------------------------------

# 67. Immutable Historical Reports

Significant reports shall be append-only or immutable once written.

Examples include:

-   readiness reports;
-   validation reports;
-   review reports;
-   findings;
-   waivers;
-   human decisions;
-   CI observations;
-   repository mismatches.

A new report shall not silently overwrite historical evidence.

------------------------------------------------------------------------

# 68. Event Journal

Each Attempt shall maintain a lightweight chronological event journal.

JSON Lines is the preferred V1 format:

``` text
events.jsonl
```

Conceptual events include:

``` text
ATTEMPT_STARTED
READINESS_COMPLETED
VALIDATION_COMPLETED
REVIEW_COMPLETED
HUMAN_APPROVAL_RECORDED
COMMIT_CREATED
PUSH_VERIFIED
CI_OBSERVED
ATTEMPT_CLOSED
```

This is not intended to implement full Event Sourcing.

The journal provides traceability and diagnostics.

------------------------------------------------------------------------

# 69. Persistent Schema Versioning

Persistent document formats shall carry schema version information.

Conceptually:

``` json
{
  "schema_version": 1
}
```

This prevents future versions of SDD Agent from silently misinterpreting
older persisted data.

------------------------------------------------------------------------

# 70. Persistence Validation

Persistent JSON shall always be validated through Pydantic before
entering the domain model.

Invalid or corrupt persistent data shall prevent sensitive workflow
transitions.

The application shall not continue by silently defaulting missing
critical fields.

------------------------------------------------------------------------

# 71. Gate Reconstruction

Persistent gate badges shall not be treated as unquestionable truth.

The architecture shall persist the facts required to recompute gates.

For example:

``` text
candidate
+
validation evidence
+
waivers
+
review
+
findings
        |
        v
ReadyToCommitPolicy
        |
        v
PASS / FAIL
```

The system therefore distinguishes:

> remembering that a gate passed

from:

> proving that the gate is still applicable.

------------------------------------------------------------------------

# 72. Recovery

After process restart, SDD Agent loads persisted state and verifies it
against repository reality.

Conceptually:

``` text
persistent expected state
          +
actual repository
          |
          v
reconciliation
```

If compatible:

``` text
RESUME
```

may proceed.

If incompatible:

``` text
REPOSITORY_MISMATCH
```

blocks sensitive progression until explicit resolution.

------------------------------------------------------------------------

# 73. RESUME

RESUME continues the current Attempt only when actual repository and
workflow state are compatible with persisted expectations.

Agent session continuity is optional.

Lost sessions are reconstructed when necessary.

------------------------------------------------------------------------

# 74. RESTART

RESTART creates a new Attempt for the same TASK.

A new appropriate baseline is established.

Previous Attempt history is preserved.

An incompatible repository state cannot silently become the new baseline
of the existing Attempt.

------------------------------------------------------------------------

# 75. ABANDON

ABANDON stops the active Attempt through an explicit human decision.

ABANDONED is not CLOSED.

Existing candidate work is not automatically destroyed.

Candidate disposition remains an explicit human concern.

------------------------------------------------------------------------

# 76. Project Configuration

Project configuration shall be versionable in the repository.

Preferred conceptual file:

``` text
sdd.yaml
```

Example:

``` yaml
agents:
  readiness: codex
  implementer: claude-code
  reviewer: codex

git:
  remote: origin
  target_branch: main

ci:
  provider: github-actions
```

The exact schema will be defined through implementation tasks.

Configuration and operational state remain distinct:

``` text
sdd.yaml = desired project configuration
.sdd/    = observed operational workflow state
```

------------------------------------------------------------------------

# 77. Configuration Validation

Configuration shall be parsed and validated through Pydantic.

Invalid configuration shall prevent sensitive operations and produce an
explainable configuration error.

------------------------------------------------------------------------

# 78. Secrets

Secrets shall not be stored in `.sdd/` or committed project
configuration.

Examples include:

``` text
API keys
Claude credentials
Codex credentials
GitHub tokens
provider secrets
```

Provider authentication shall use the normal environment, CLI or
credential mechanisms of the external provider.

Non-secret provider/session metadata may be persisted where required for
recovery.

------------------------------------------------------------------------

# 79. Explicit Agent Workspace

Every agent execution shall receive an explicit repository workspace
path.

Agent behavior shall not depend on an implicit shell current directory.

This protects against running the correct TASK against the wrong
repository.

------------------------------------------------------------------------

# 80. External Operation Timeouts

External operations shall have configurable timeouts.

This applies to categories such as:

``` text
Claude Code
Codex
validation commands
Git network operations
CI polling
```

Timeout is execution evidence.

It shall not automatically be classified as a CODE defect.

------------------------------------------------------------------------

# 81. Retry Policy

Retries shall be bounded and restricted to eligible technical/transient
failures.

Examples:

``` text
temporary provider failure
network timeout
CI API unavailable
```

Retries shall not be used for:

``` text
BLOCKER findings
IMPORTANT findings
validation FAILED
SPEC_REQUIRED
PLAN_REQUIRED
TASKS_REQUIRED
human decisions
```

Technical retry and workflow transition are separate concepts.

------------------------------------------------------------------------

# 82. Human Waiting States

The system shall never automatically substitute an AI decision for a
required human decision.

When the workflow requires:

``` text
PRODUCT decision
ARCHITECTURE decision
TASKS decision
validation waiver decision
repository mismatch decision
commit approval
```

it waits for explicit human input.

Absence of a response is never approval.

------------------------------------------------------------------------

# 83. Logs vs Evidence

Operational logs and SDD evidence are distinct.

Examples of logs:

``` text
Launching Codex
Process started
Retry 1/3
Polling CI
```

Examples of durable evidence:

``` text
ReviewReport
ValidationReport
HumanDecision
ClassificationReport
CIResult
```

Logs aid diagnosis but do not automatically satisfy workflow gates.

------------------------------------------------------------------------

# 84. Correlation

Operational logs, reports and evidence shall be correlatable by:

``` text
task_id
attempt_id
```

and, where applicable:

``` text
candidate_id
agent execution
validation id
review id
```

Conceptual log prefix:

``` text
[T032/002][VALIDATION]
[T032/002][REVIEW][codex]
[T032/002][COMMIT]
```

------------------------------------------------------------------------

# 85. Execution Model

V1 shall operate as:

``` text
one local project
one active task execution
one local orchestrator
```

It shall not introduce distributed infrastructure such as:

``` text
Kafka
Redis distributed locks
distributed workers
distributed transactions
```

unless the architecture is revised in a later version.

------------------------------------------------------------------------

# 86. Workspace Lock

A lightweight local workspace lock shall prevent two SDD Agent processes
from concurrently orchestrating the same project state.

Conceptually:

``` text
SDD Agent process A
       |
       v
workspace lock
       |
       X
SDD Agent process B
```

The lock shall be recoverable after abnormal process termination.

The lock itself is not workflow truth.

------------------------------------------------------------------------

# 87. Technical Error Model

Technical errors and SDD problem classifications shall remain distinct.

Conceptual technical error families include:

``` text
ConfigurationError
PersistenceError
AgentExecutionError
GitOperationError
ValidationExecutionError
CIProviderError
WorkflowViolation
```

These are not equivalent to:

``` text
PRODUCT
ARCHITECTURE
TASKS
CODE
ENVIRONMENT
REPOSITORY_MISMATCH
```

For example:

``` text
AgentExecutionError
       |
       v
context/evidence
       |
       v
classification
       |
       v
ENVIRONMENT
```

where appropriate.

------------------------------------------------------------------------

# 88. Source of Truth Boundaries

Authoritative repository artifacts remain the durable
product/development truth.

Conceptually:

``` text
SPEC
PLAN
TASKS
CODE
TESTS
MIGRATIONS
```

Operational state contains:

``` text
active task
attempt
phase
baseline
candidate identity
reports
findings
waivers
human decisions
agent session references
commit/push/CI evidence
next authorized action
```

Operational state shall never substitute for an authoritative artifact
change.

For example:

``` text
Human architecture decision
```

must ultimately be reflected in approved `plan.md` where the
architecture contract changes.

------------------------------------------------------------------------

# 89. Artifact Identity

Because gates depend on approved SPEC/PLAN/TASKS contracts, the
implementation shall maintain sufficient artifact identity to detect
relevant changes.

The exact representation may use content hashes, Git identities or
another deterministic repository-derived mechanism.

The architecture requires only that SDD Agent can determine whether
evidence was produced against the currently applicable artifact
contract.

------------------------------------------------------------------------

# 90. Artifact Change Invalidation

An approved change to SPEC, PLAN or TASKS affecting the active TASK
invalidates dependent evidence.

The workflow returns through READINESS before further CODE/FIX
progression.

Conceptually:

``` text
artifact contract A
      |
  evidence
      |
artifact changes -> B
      |
      X
old dependent evidence no longer applicable
      |
      v
READINESS
```

------------------------------------------------------------------------

# 90A. Implementation Completion Evidence

IMPLEMENTATION and FIX completion shall be represented by a structured
`ImplementationReport` or equivalent validated model.

Conceptually:

``` text
ImplementationReport
 ├── report_id
 ├── task_id
 ├── attempt_id
 ├── candidate_id
 ├── implementation_role
 ├── completion_status
 ├── changed_paths
 ├── task_scope_summary
 ├── validations_run_by_agent
 ├── known_limitations
 └── timestamp
```

The closed completion statuses are:

``` text
COMPLETED
INCOMPLETE
FAILED
```

`COMPLETED` means only that the implementer declares implementation of
the active TASK scope complete for the exact referenced candidate.

It does not prove:

``` text
TASK correctness
validation success
review success
READY_TO_COMMIT
```

The Orchestrator, not the implementer, owns READY_FOR_REVIEW.

An ImplementationReport is candidate-bound. If the candidate changes
after the report is produced, that report remains historical but becomes
non-applicable to the changed candidate.

A candidate-changing FIX therefore requires a new applicable
implementation-completion report before READY_FOR_REVIEW can be
established again.

The structured report is one input to deterministic READY_FOR_REVIEW
evaluation; it is never itself a workflow gate.

------------------------------------------------------------------------

# 91. READY_FOR_REVIEW Architecture

READY_FOR_REVIEW shall be computed from facts, not directly assigned by
an agent.

The policy verifies at minimum:

``` text
candidate identifiable
candidate stable
applicable ImplementationReport(candidate).completion_status = COMPLETED
required validation obligations accounted for
required validation results acceptable
eligible NOT_RUN validations have applicable waivers
required evidence available
no unresolved condition prohibits review
```

The implementation-completion fact is therefore owned by structured,
candidate-bound evidence, while gate authority remains deterministic in
`ReadyForReviewPolicy`.

Candidate modification invalidates READY_FOR_REVIEW and makes the
previous ImplementationReport non-applicable to the changed candidate.

------------------------------------------------------------------------

# 92. READY_TO_COMMIT Architecture

READY_TO_COMMIT is candidate-specific.

It is derived from the applicable review and validation evidence for the
exact current candidate.

At minimum:

``` text
READY_FOR_REVIEW applicable
review applies to current candidate
BLOCKER == 0
IMPORTANT == 0
no unresolved blocking routing
repository integrity valid
```

MINOR findings remain visible.

READY_TO_COMMIT is not human approval.

------------------------------------------------------------------------

# 93. COMMIT Authorization Architecture

COMMIT is permitted only when:

``` text
current candidate = C

READY_TO_COMMIT(C).applicable
AND
HUMAN_APPROVAL(C).applicable
AND
repository still represents C
```

Any candidate modification invalidates the relevant prerequisite
evidence.

No stale combination may authorize COMMIT.

------------------------------------------------------------------------

# 94. PUSH Architecture

PUSH occurs only after an orchestrated successful COMMIT.

The expected commit SHA and expected remote target are known before
remote verification.

PUSH success does not itself prove closure.

------------------------------------------------------------------------

# 95. CLOSED Architecture

CLOSED is computed from current applicable evidence.

At minimum, closure requires:

``` text
review gate satisfied
READY_TO_COMMIT applicable for committed candidate lineage
human commit approval applicable to committed candidate
expected commit created
push performed
expected remote target verified
no unresolved closure-relevant repository mismatch
hosted CI GREEN for current expected commit
```

CI GREEN for an older commit cannot close the Attempt.

CLOSED is not manually assignable.

------------------------------------------------------------------------

# 96. Testing Strategy

The architecture is designed to support strong automated testing.

## 96.1 Unit Tests

Pure policies shall receive extensive unit tests.

Examples:

``` text
review gate
READY_FOR_REVIEW
READY_TO_COMMIT
commit authorization
waiver applicability
routing
closure
evidence invalidation
```

These tests require no live agent.

------------------------------------------------------------------------

## 96.2 Persistence Tests

Test:

``` text
atomic writes
schema validation
schema version handling
corrupt state detection
append-only report behavior
restart/recovery
```

------------------------------------------------------------------------

## 96.3 Git Integration Tests

Test:

``` text
baseline identity
dirty repository blocks Attempt creation
staged/index-only pre-existing changes
candidate snapshot canonicalization
candidate fingerprint
tracked modifications
deletions
file modes
binary files
deterministic untracked-file inclusion
ignored-file exclusion
rename represented independently from Git rename heuristics
worktree/index divergence
candidate modification
commit tree exactly matches authorized CandidateSnapshot
unexpected commit
remote target identity where practical
```

Temporary local Git repositories should be preferred for deterministic
tests.

------------------------------------------------------------------------

## 96.4 Agent Adapter Tests

Agent adapters shall be tested separately from workflow policies.

Use fake/stub AgentRunner implementations for most Core tests.

Live Claude/Codex integration tests shall not be required for every test
run.

------------------------------------------------------------------------

## 96.5 Validation Tests

Test:

``` text
PASSED
FAILED
NOT_RUN
timeout
missing command
evidence capture
waiver behavior
```

------------------------------------------------------------------------

## 96.6 Workflow Scenario Tests

High-value scenario tests shall cover complete deterministic sequences
such as:

``` text
happy path

review CODE blocker -> FIX -> VALIDATION -> RE_REVIEW

validation environment NOT_RUN -> waiver -> REVIEW

candidate changed after review

candidate changed after human approval

repository mismatch

artifact change -> READINESS

CI FAILED -> CODE correction full proof cycle

CI FAILED -> ENVIRONMENT recovery

restart and recovery

dirty repository blocks new Attempt until human cleanup

ImplementationReport invalidated by candidate change

worktree candidate differs from staging/index before commit

abandon

dependency blocked
```

------------------------------------------------------------------------

# 97. Provider Test Doubles

Ports shall permit deterministic fake implementations:

``` text
FakeAgentRunner
FakeGitRepository where useful
FakeValidationRunner
FakeCIProvider
```

This keeps the Core test suite fast and independent from external
credentials and network availability.

------------------------------------------------------------------------

# 98. Security and Safety Boundaries

V1 safety relies on multiple layers:

``` text
role instructions
+
provider permissions where supported
+
explicit workspace
+
Git verification
+
deterministic gates
+
human gates
+
no generic force bypass
```

No single LLM prompt is considered sufficient enforcement.

------------------------------------------------------------------------

# 99. Architectural Non-Goals

V1 architecture explicitly excludes:

-   web dashboard;
-   SaaS platform;
-   multi-user orchestration;
-   multi-repository workflow;
-   distributed workers;
-   message broker;
-   Kubernetes deployment;
-   database server;
-   autonomous product decisions;
-   autonomous architecture decisions;
-   autonomous TASK contract rewriting;
-   autonomous commit approval;
-   autonomous merge to production;
-   vector database/RAG infrastructure unless a later demonstrated
    requirement justifies it;
-   LangGraph as the central workflow engine.

------------------------------------------------------------------------

# 100. Proposed Package Responsibilities

The exact Python package names may be refined during TASKS/CODE, but the
architecture should preserve boundaries equivalent to:

``` text
sdd_agent/
│
├── cli/
│
├── application/
│   └── orchestration
│
├── domain/
│   ├── workflow
│   ├── gates
│   ├── routing
│   ├── models
│   └── policies
│
├── ports/
│   ├── agents
│   ├── git
│   ├── validation
│   ├── ci
│   └── persistence
│
├── adapters/
│   ├── agents/
│   │   ├── claude_code
│   │   └── codex
│   ├── git/
│   ├── validation/
│   ├── ci/
│   └── persistence/
│
├── context/
│
├── configuration/
│
└── diagnostics/
```

This is a responsibility map, not a mandatory final directory tree.

TASKS/CODE may refine names without collapsing architectural boundaries.

------------------------------------------------------------------------

# 101. Dependency Direction

Dependencies shall point inward.

Conceptually:

``` text
CLI
 |
 v
Application
 |
 v
Domain / Ports
 ^
 |
Adapters
```

The domain shall not import:

``` text
Claude Code SDK/CLI implementation
Codex implementation
Git CLI implementation
GitHub implementation
filesystem JSON implementation
```

Provider-specific details remain outside the Core.

------------------------------------------------------------------------

# 102. Typical Happy Path

Conceptually:

``` text
Human selects TASK
       |
       v
Repository pre-check
       |
       v
Attempt created
       |
       v
Baseline established
       |
       v
READINESS
       |
       v
READY_FOR_CODE
       |
       v
IMPLEMENTATION
       |
       v
Candidate fingerprint
       |
       v
VALIDATION
       |
       v
READY_FOR_REVIEW
       |
       v
Independent REVIEW
       |
BLOCKER=0 IMPORTANT=0
       |
       v
READY_TO_COMMIT
       |
       v
Human Commit Gate
       |
       v
HumanApproval(candidate)
       |
       v
COMMIT
       |
       v
ExpectedCommit SHA
       |
       v
PUSH
       |
       v
Remote verification
       |
       v
Hosted CI
       |
      GREEN
       |
       v
CLOSED
```

------------------------------------------------------------------------

# 103. CODE Finding Path

``` text
REVIEW
   |
blocking CODE finding
   |
   v
FIX_REQUIRED
   |
   v
FIX
   |
candidate changes
   |
   v
VALIDATION
   |
   v
RE_REVIEW
   |
   v
READY_TO_COMMIT
```

------------------------------------------------------------------------

# 104. Non-CODE Finding Path

``` text
REVIEW / VALIDATION / CI / READINESS
            |
            v
        CLASSIFY
            |
     +------+------+------+
     |             |      |
 PRODUCT      ARCHITECTURE TASKS
     |             |      |
     v             v      v
SPEC_REQUIRED PLAN_REQUIRED TASKS_REQUIRED
     |
human decision + approved artifact change
     |
     v
READINESS
```

------------------------------------------------------------------------

# 105. Repository Mismatch Path

``` text
expected repository state
          !=
actual repository state
          |
          v
REPOSITORY_MISMATCH
          |
          v
BLOCKED
          |
   explicit resolution
    /       |       \
RESUME   RESTART   ABANDON
```

------------------------------------------------------------------------

# 106. Recovery Principle

A fresh SDD Agent process with no prior conversational context must be
capable of reconstructing the next safe action from:

``` text
repository
+
SPEC
+
PLAN
+
TASKS
+
.sdd operational state
+
durable reports/evidence
```

This is a mandatory architectural property.

------------------------------------------------------------------------

# 107. Architectural Decision Summary

The PLAN incorporates the accepted architecture decisions PLAN-001
through PLAN-094.

The principal decisions are:

``` text
Python 3.13+
Pydantic
deterministic custom workflow engine
no LangGraph at workflow core
lightweight hexagonal architecture
local CLI application
central Orchestrator
Phase / Condition / NextAction separation
Attempt model
candidate identity and fingerprint
provider-neutral AgentRunner
Claude Code + Codex adapters
independent initial reviewer session
implementer continuity for FIX where possible
reviewer continuity for RE-REVIEW where possible
ContextBuilder
structured agent reports
GitRepository port
exact baseline SHA
candidate recalculation
commit/push protection
expected remote verification
ValidationRunner
structured validation obligations/results
strict waiver model
ProblemClassifier
deterministic RoutingPolicy
CIProvider
expected-commit CI identity
CI polling
structured HumanDecision
candidate-bound commit approval
thin intent-oriented CLI
JSON persistence under .sdd/
atomic writes
append-only historical reports
events.jsonl
schema versioning
gate reconstruction
restart reconciliation
versioned sdd.yaml configuration
explicit workspaces
role permissions
timeouts
bounded technical retries
logs/evidence separation
single local orchestrator
workspace lock
structured technical errors
CandidateSnapshot independent from Git index/staging
deterministic untracked-file inclusion and ignored-file exclusion
commit tree verification against authorized CandidateSnapshot
clean repository required before new Attempt
no silent adoption of pre-existing dirty state
structured candidate-bound ImplementationReport
all non-ignored untracked files included in CandidateSnapshot
Git ignore rule changes participate in CandidateIdentity
```

------------------------------------------------------------------------

# 108. PLAN Review Requirements

Before this PLAN may become PLAN_READY, an independent reviewer shall
examine at minimum:

## Architecture vs SPEC

Verify that every major SPEC invariant has a viable architectural
realization.

## Deterministic Authority

Verify that no agent, adapter or CLI command can directly bypass
deterministic gates.

## Candidate Integrity

Verify baseline, fingerprint, review, approval, commit, push, remote and
CI identities form a coherent chain.

## Validation

Verify PASSED / FAILED / NOT_RUN and waiver semantics match the SPEC.

## Agent Independence

Verify initial reviewer independence and FIX / RE-REVIEW continuity
rules.

## Recovery

Verify loss of process or agent session does not destroy workflow
recoverability.

## Persistence

Verify current snapshots are not mistaken for durable proof and gates
remain reconstructible.

## Human Gates

Verify required PRODUCT / ARCHITECTURE / TASKS / waiver / repository /
commit decisions remain human-controlled.

## CI Recovery

Verify CI CODE correction cannot bypass VALIDATION, RE-REVIEW,
READY_TO_COMMIT or a new applicable Human Commit Gate.

## SPEC / PLAN Boundary

Verify this document does not silently change approved product behavior.

## PLAN / TASKS Boundary

Verify this document provides sufficient architecture for later TASK
decomposition without prematurely becoming an implementation task list.

------------------------------------------------------------------------

# 109. PLAN Review Severity

Independent PLAN review shall use:

``` text
BLOCKER
IMPORTANT
MINOR
```

Gate:

``` text
BLOCKER > 0
OR
IMPORTANT > 0
    ->
PLAN_NEEDS_FIXES
```

Otherwise:

``` text
PLAN_READY
```

MINOR findings alone do not block PLAN_READY.

------------------------------------------------------------------------

# 110. Current PLAN State

Current status:

``` text
SPEC = SPEC_READY

PLAN architecture discovery = COMPLETE

PLAN-001 through PLAN-096 = ACCEPTED

plan.md consolidation = COMPLETE

Independent PLAN Review #1 = COMPLETED
Initial gate = PLAN_NEEDS_FIXES

Independent PLAN Re-review #1 = COMPLETED
Re-review gate = PLAN_NEEDS_FIXES

PLAN-R002 = RESOLVED
PLAN-R003 = RESOLVED
PLAN-R004 = RESOLVED
PLAN-R001 = PARTIALLY_RESOLVED in Re-review #1

PLAN-095 untracked-file inclusion rule = integrated
PLAN-096 Git-ignore candidate identity rule = integrated

Independent PLAN Re-review #2 of remaining PLAN-R001 = COMPLETED
Re-review #2 gate = PLAN_READY

PLAN-R001 = RESOLVED

BLOCKER = 0
IMPORTANT = 0

PLAN status = PLAN_READY
```

TASKS may begin because independent PLAN re-review confirmed:

``` text
BLOCKER = 0
IMPORTANT = 0
```

and therefore:

``` text
PLAN_READY
```

------------------------------------------------------------------------

# End of Architecture Plan
