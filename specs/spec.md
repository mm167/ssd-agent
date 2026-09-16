# SDD Agent --- Product Specification

**Product:** SDD Agent\
**Product version:** V1 semi-automatic\
**Specification revision:** V3\
**Phase:** SPEC\
**Specification status:** SPEC_READY\
**Encoding:** UTF-8

------------------------------------------------------------------------

# 1. Purpose

SDD Agent is a semi-automatic orchestration system for applying a strict
Spec-Driven Development workflow to software development tasks.

Its primary purpose is to ensure that development follows:

``` text
SPEC
  |
  v
PLAN
  |
  v
TASKS
  |
  v
CODE
```

At TASK execution level:

``` text
TASK SELECTED
      |
      v
READINESS
      |
      v
IMPLEMENTATION
      |
      v
VALIDATION
      |
      v
INDEPENDENT REVIEW
      |
      v
FIX / RE-REVIEW if required
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
      |
      v
CLOSED
```

SDD Agent coordinates this workflow without autonomously taking product,
substantial architecture, task-contract, or final commit-authorization
decisions that belong to a human.

------------------------------------------------------------------------

# 2. Problem Statement

A manually operated SDD workflow is effective but vulnerable to
procedural drift.

Common failure modes include:

-   starting CODE before verifying that a TASK is ready;
-   treating BUILD SUCCESS as TASK SUCCESS;
-   treating green tests as proof of SPEC compliance;
-   allowing implementation to silently resolve PRODUCT or ARCHITECTURE
    ambiguity;
-   reviewing a different candidate from the one eventually committed;
-   allowing the implementer to act as its own independent reviewer;
-   losing workflow state when an AI conversation disappears;
-   relying on conversation history as project truth;
-   treating every failure as a CODE defect;
-   committing before independent review;
-   allowing reviewer prose to override deterministic gates;
-   confusing task numeric order with dependency order;
-   declaring a TASK complete before PUSH and hosted CI;
-   reusing stale approvals, waivers, review evidence, remote evidence,
    or CI results after the candidate changes;
-   allowing human approval to bypass READY_TO_COMMIT.

SDD Agent V1 exists to make these constraints explicit, recoverable,
observable, and enforceable.

------------------------------------------------------------------------

# 3. Product Goal

V1 must orchestrate the lifecycle of one software TASK at a time from
task selection to verified closure.

The system must be able to:

-   identify the selected TASK;
-   determine whether dependencies permit execution;
-   inspect applicable SDD artifacts;
-   establish repository baseline and candidate identity;
-   perform READINESS;
-   prevent CODE when unresolved upstream decisions exist;
-   coordinate implementation;
-   collect validation evidence;
-   classify validation failures;
-   support narrowly controlled validation waivers;
-   coordinate independent review;
-   classify and route findings;
-   compute deterministic gates;
-   coordinate FIX and RE-REVIEW;
-   establish READY_TO_COMMIT;
-   present only an applicable READY_TO_COMMIT candidate to the Human
    Commit Gate;
-   prevent COMMIT without both applicable READY_TO_COMMIT and human
    approval for the same exact candidate;
-   coordinate COMMIT and PUSH;
-   verify expected remote Git state;
-   observe hosted CI;
-   classify CI failures;
-   recover from CI failures through the appropriate SDD route;
-   persist sufficient workflow evidence for restart and recovery;
-   declare the TASK CLOSED only when all closure requirements are
    satisfied.

------------------------------------------------------------------------

# 4. V1 Non-Goals

V1 is not intended to provide:

-   autonomous product decision-making;
-   autonomous substantial architecture decision-making;
-   autonomous rewriting of approved SPEC, PLAN, or TASKS without human
    approval;
-   autonomous selection of the next TASK;
-   autonomous production merge;
-   multi-repository orchestration;
-   a distributed orchestration platform;
-   a SaaS or multi-user platform;
-   a mandatory web dashboard;
-   Kubernetes deployment;
-   a complex vector database or RAG architecture;
-   autonomous issue prioritization;
-   autonomous product backlog selection.

V1 is a semi-automatic SDD orchestrator, not an autonomous software
organization.

------------------------------------------------------------------------

# 5. Actors

## 5.1 Human

The human retains authority over:

-   PRODUCT decisions;
-   substantial ARCHITECTURE decisions;
-   TASKS contract or decomposition decisions;
-   approval of proposed changes to authoritative SDD artifacts;
-   selection of the TASK to execute;
-   exceptional validation waivers where permitted;
-   final authorization to commit;
-   abandonment or restart decisions when required.

## 5.2 Orchestrator

SDD Agent coordinates the workflow.

It may:

-   inspect evidence;
-   launch agents;
-   request structured reports;
-   classify workflow conditions;
-   compute deterministic gates;
-   persist operational state;
-   block unauthorized transitions;
-   present decisions to the human;
-   execute authorized workflow actions.

It must not silently cross a human gate.

## 5.3 Implementer

The implementer performs CODE work for the selected TASK.

The implementer may make local implementation decisions compatible with
approved SPEC, PLAN, and TASKS.

The implementer must not silently resolve PRODUCT, substantial
ARCHITECTURE, or TASK-contract ambiguity.

The implementer is not its own independent reviewer.

## 5.4 Reviewer

The reviewer independently evaluates the exact candidate against the
applicable SDD contract.

The reviewer identifies findings but does not override deterministic
workflow gates.

The reviewer does not modify the candidate during review.

------------------------------------------------------------------------

# 6. Sources of Truth

Durable project truth is repository-based.

Authoritative project artifacts include, as applicable:

``` text
SPEC
PLAN
TASKS
CODE
TESTS
MIGRATIONS
PROJECT CONFIGURATION
GIT HISTORY
```

Operational workflow state may preserve:

-   current phase;
-   attempt;
-   baseline;
-   candidate identity;
-   validation evidence;
-   waivers;
-   reviews;
-   findings;
-   human decisions;
-   blockers;
-   approvals;
-   commit evidence;
-   push evidence;
-   remote-state evidence;
-   CI evidence.

Operational state never replaces required authoritative project
artifacts.

AI conversations are disposable execution contexts.

A conversation must never be the sole source of information required for
a future workflow transition.

------------------------------------------------------------------------

# 7. SDD Routing

Problems and decisions must be routed according to their nature.

``` text
PRODUCT        -> SPEC
ARCHITECTURE   -> PLAN
TASK CONTRACT
OR
DECOMPOSITION  -> TASKS
IMPLEMENTATION
DETAIL         -> CODE
ENVIRONMENT    -> ENVIRONMENT handling
```

The system must distinguish classification from routing.

A failure is not automatically a CODE problem.

------------------------------------------------------------------------

# 8. Task Selection

The human selects the next TASK.

SDD Agent may:

-   identify candidate executable tasks;
-   display dependency information;
-   explain why a TASK appears executable or blocked.

SDD Agent V1 must not autonomously choose which TASK the project should
execute next.

------------------------------------------------------------------------

# 9. Task Dependencies

A TASK with an unsatisfied mandatory dependency cannot proceed to
execution.

It becomes blocked with a dependency-related cause.

Task numeric order does not define execution order.

Dependencies and explicit execution constraints determine readiness.

Unless the TASK contract explicitly defines another acceptable
dependency state, a mandatory dependency is considered satisfied only
when the dependency TASK is CLOSED.

If READINESS discovers an incorrect, incomplete, or missing dependency
in TASKS, SDD Agent must not silently repair TASKS.

The problem routes to:

``` text
TASKS_REQUIRED
```

and requires the applicable human/artifact decision before READINESS can
succeed.

------------------------------------------------------------------------

# 10. Baseline

At the beginning of an execution attempt, SDD Agent establishes an
identifiable Git baseline.

The baseline represents the repository state from which the candidate
for the active TASK is developed.

The baseline must remain identifiable throughout the attempt.

It must not silently change.

If repository history changes in a way that makes the established
baseline incompatible or ambiguous, sensitive workflow transitions must
stop until the situation is resolved.

------------------------------------------------------------------------

# 11. Pre-existing Repository Changes

A dirty repository at the beginning of a TASK cannot automatically be
attributed to that TASK.

Pre-existing changes must be exposed.

Execution is blocked until an explicit authorized resolution determines
how to proceed.

The exact technical actions available for resolving a dirty repository
belong to PLAN.

------------------------------------------------------------------------

# 12. Candidate

The candidate is the concrete repository state proposed to satisfy the
active TASK contract.

Conceptually:

``` text
TASK
=
required contract

candidate
=
concrete repository state proposed
to satisfy that contract
```

Baseline and candidate must remain distinguishable.

If external changes make candidate identity ambiguous, REVIEW and COMMIT
are forbidden until resolved.

------------------------------------------------------------------------

# 13. READINESS

READINESS is mandatory before CODE.

Its purpose is to determine whether implementation is authorized.

READINESS evaluates the applicable project context, including as
relevant:

-   SPEC;
-   PLAN;
-   TASKS;
-   TASK dependencies;
-   repository baseline;
-   existing code;
-   migrations;
-   tests;
-   project configuration;
-   known constraints.

READINESS must determine whether the TASK contract is sufficiently
complete and consistent to authorize CODE.

Possible conceptual outcomes include:

``` text
READY_FOR_CODE

SPEC_REQUIRED

PLAN_REQUIRED

TASKS_REQUIRED

BLOCKED
```

The technical representation belongs to PLAN.

------------------------------------------------------------------------

# 14. Artifact Ambiguity During READINESS

If READINESS discovers that the applicable contract is ambiguous or
insufficient to authorize CODE, CODE remains forbidden.

The ambiguity must be classified and routed.

``` text
PRODUCT       -> SPEC_REQUIRED
ARCHITECTURE  -> PLAN_REQUIRED
TASKS         -> TASKS_REQUIRED
```

CODE may resume only after the required decision or artifact change has
been resolved and READINESS succeeds again.

------------------------------------------------------------------------

# 15. IMPLEMENTATION

IMPLEMENTATION begins only after successful READINESS.

Only the active TASK is implemented.

The implementer may make local CODE decisions when they:

-   do not change approved product behavior;
-   do not modify substantial approved architecture;
-   do not alter the TASK contract;
-   remain compatible with applicable project artifacts.

The implementer must stop and route upstream when a required decision
exceeds CODE authority.

Implementation completion does not imply TASK success.

------------------------------------------------------------------------

# 16. Artifact Return During Implementation

If implementation discovers an unresolved issue requiring an upstream
artifact decision:

``` text
PRODUCT       -> SPEC_REQUIRED
ARCHITECTURE  -> PLAN_REQUIRED
TASKS         -> TASKS_REQUIRED
```

implementation stops.

The system must not allow the implementer to silently invent the missing
contract.

------------------------------------------------------------------------

# 17. Artifact Change Invalidation

Approved changes to SPEC, PLAN, or TASKS that affect the active TASK
invalidate dependent workflow proofs based on the previous contract.

The active TASK must pass READINESS again before CODE or FIX continues.

A gate is contextual evidence, not a permanent badge.

------------------------------------------------------------------------

# 18. VALIDATION

VALIDATION is mandatory after implementation and before REVIEW.

There is no valid direct transition:

``` text
IMPLEMENTATION
      |
      v
    REVIEW
```

without VALIDATION.

Expected validations derive from the active TASK and applicable project
contract.

The implementer may add useful validations.

The implementer must not silently remove, weaken, or skip required
validations.

The mechanism for discovering and executing validations belongs to PLAN.

------------------------------------------------------------------------

# 19. Validation Results

For every required validation, the workflow must preserve sufficient
evidence to distinguish outcomes such as:

``` text
GREEN
FAILED
NOT RUN
```

BUILD SUCCESS does not imply TASK success.

A large number of green tests does not independently prove compliance
with SPEC, PLAN, or TASKS.

Tests themselves may encode incorrect assumptions.

------------------------------------------------------------------------

# 20. Validation Failure

A validation failure is a transient result requiring classification.

VALIDATION_FAILED is not required to be a permanent lifecycle state.

A failed validation must be classified before routing.

``` text
CODE          -> FIX_REQUIRED
ENVIRONMENT   -> ENVIRONMENT_BLOCKED
PRODUCT       -> SPEC_REQUIRED
ARCHITECTURE  -> PLAN_REQUIRED
TASKS         -> TASKS_REQUIRED
```

The representation of the transient failure and resulting routing
belongs to PLAN.

------------------------------------------------------------------------

# 21. Insufficient Validation

If required validation evidence is missing or insufficient, REVIEW is
blocked unless the missing validation is covered by a currently
applicable waiver permitted by this SPEC.

Implementation being complete does not itself make the candidate ready
for review.

------------------------------------------------------------------------

# 22. Validation Waiver Policy

A validation waiver is a human-approved exceptional derogation allowing
the workflow to proceed despite an authorized missing validation result.

A waiver is never equivalent to successful validation.

## 22.1 FAILED Is Never Waivable

An executed validation whose result is:

``` text
FAILED
```

cannot be waived.

It must be classified and routed.

## 22.2 Waiver Eligibility

In V1, a required validation may be eligible for waiver only when:

``` text
result = NOT RUN
```

and the reason has been explicitly classified:

``` text
ENVIRONMENT
```

A validation skipped by convenience, omission, implementation choice, or
lack of completion is not automatically waiver-eligible.

## 22.3 Waiver Is Not GREEN

``` text
NOT RUN
+
APPROVED WAIVER
!=
GREEN
```

The validation remains NOT RUN.

## 22.4 Waiver Effect

A currently applicable waiver may allow progression toward
READY_FOR_REVIEW.

It does not erase the missing validation.

## 22.5 Exact Waiver Context

A waiver is never a reusable general authorization.

It applies only to the validation and context for which the human
approved it.

Its applicability must be determinable relative to at least:

``` text
TASK
+
attempt
+
candidate
+
validation obligation
+
validation evidence
+
ENVIRONMENT classification
+
applicable artifact contract
```

The technical representation belongs to PLAN.

## 22.6 Attempt Binding

A waiver from one execution attempt does not automatically apply to
another.

``` text
waiver(TASK, attempt A)
!=
waiver(TASK, attempt B)
```

A RESTART creating a new attempt therefore requires waiver applicability
to be established again.

## 22.7 Candidate Binding

A waiver is bound to the candidate context for which its validation
evidence was evaluated.

If the candidate changes materially:

``` text
Candidate A
   |
   v
Candidate B
```

a waiver applicable to Candidate A is not automatically applicable to
Candidate B.

Candidate B must obtain appropriate validation evidence.

If the validation remains NOT RUN, remains caused by ENVIRONMENT, and
remains waiver-eligible, a new human waiver is required.

## 22.8 Artifact Contract Binding

A waiver is relative to the applicable contract defining the validation
obligation.

A relevant change to SPEC, PLAN, TASKS, or the validation obligation
invalidates automatic reuse of the previous waiver.

The applicable validation requirements must be evaluated again.

## 22.9 Evidence and Cause Binding

A waiver depends on the evidence and cause classification that justified
it.

If new validation evidence appears or the cause classification changes,
waiver applicability must be re-evaluated.

Example:

``` text
Validation X
NOT RUN
cause = ENVIRONMENT
waiver approved

        |
        v

environment repaired

        |
        v

Validation X
executed
FAILED
```

The old waiver cannot mask the new failure.

FAILED must be classified and routed.

## 22.10 Waiver Invalidation

A waiver becomes non-applicable when its relevant context changes,
including:

``` text
attempt changes
OR
candidate changes materially
OR
applicable artifact contract changes materially
OR
validation obligation changes
OR
validation evidence changes materially
OR
cause classification changes
```

A non-applicable waiver cannot satisfy a current workflow gate.

## 22.11 Historical Waivers

An invalidated or obsolete waiver remains part of workflow history.

It must not be deleted merely because it is no longer applicable.

Historical traceability does not imply current applicability.

## 22.12 Visibility

Applicable waivers must remain visible in workflow evidence.

They must be visible at least to:

-   REVIEW;
-   READY_TO_COMMIT evaluation where relevant;
-   Human Commit Gate.

The human must be able to distinguish GREEN validation from NOT RUN plus
applicable waiver.

## 22.13 Non-Waivable Validations

The applicable project contract may declare a validation non-waivable.

A non-waivable validation must achieve its required actual result.

## 22.14 Non-Waivable Closure Conditions

Conditions explicitly required by this SPEC for CLOSED cannot be
bypassed by a validation waiver.

Hosted CI GREEN applicable to the current expected commit is
non-waivable.

------------------------------------------------------------------------

# 23. Validation Evidence

The reviewer must receive sufficient evidence to understand:

-   expected validations;
-   validations executed;
-   results;
-   validations not run;
-   reasons for NOT RUN;
-   waiver eligibility;
-   applicable waivers;
-   relevant historical or invalidated waivers where necessary to
    understand the attempt.

The exact report format belongs to PLAN.

------------------------------------------------------------------------

# 24. READY_FOR_REVIEW

READY_FOR_REVIEW means:

-   implementation is complete for the active TASK scope;
-   the candidate is identifiable;
-   the candidate is stable for review;
-   required validations have the required result or a currently
    applicable waiver;
-   no obsolete waiver is being used as current gate evidence;
-   required validation evidence is available;
-   no unresolved condition prohibits review.

A relevant candidate modification after READY_FOR_REVIEW invalidates
this gate.

The candidate must return through VALIDATION before REVIEW.

------------------------------------------------------------------------

# 25. Independent Review

Initial review must be independent from implementation.

The initial reviewer must not receive the implementer's conversational
history as review context.

The reviewer reconstructs its judgment from authorized durable sources
and the exact candidate.

The reviewer may use:

-   SPEC;
-   PLAN;
-   TASKS;
-   baseline;
-   exact candidate;
-   relevant existing code;
-   migrations;
-   tests;
-   validation evidence;
-   applicable workflow evidence.

Reviewer independence does not mean loss of required durable evidence.

------------------------------------------------------------------------

# 26. Review Scope

Review evaluates SDD compliance, not merely code style or build success.

The reviewer compares the exact candidate against:

``` text
SPEC
+
PLAN
+
TASK contract
+
baseline/candidate
+
validation evidence
```

The reviewer may inspect relevant existing code to evaluate integration.

The reviewer must not penalize the current TASK merely because
functionality explicitly assigned to a future TASK is absent.

However, a genuine integration defect affecting the current TASK remains
reviewable.

------------------------------------------------------------------------

# 27. Reviewer Permissions

The reviewer may inspect and report.

The reviewer must not modify the candidate being reviewed.

The reviewer must not silently repair findings.

Reviewer and implementer are distinct roles.

------------------------------------------------------------------------

# 28. Review Findings

Review findings use exactly these severity classes:

``` text
BLOCKER
IMPORTANT
MINOR
```

## BLOCKER

An unacceptable issue requiring resolution before commit.

## IMPORTANT

A significant issue requiring resolution before commit.

## MINOR

A non-blocking issue.

MINOR findings remain visible but do not alone prohibit READY_TO_COMMIT.

------------------------------------------------------------------------

# 29. Finding Routing

Each actionable finding must be routable according to its nature.

Minimum routing:

``` text
PRODUCT       -> SPEC
ARCHITECTURE  -> PLAN
TASKS         -> TASKS
CODE          -> FIX
ENVIRONMENT   -> ENVIRONMENT handling
```

A reviewer finding does not automatically imply CODE.

------------------------------------------------------------------------

# 30. Deterministic Review Gate

Review gate computation is deterministic.

``` text
BLOCKER > 0
OR
IMPORTANT > 0
        |
        v
COMMIT FORBIDDEN
```

Only when:

``` text
BLOCKER = 0
AND
IMPORTANT = 0
```

may the candidate progress toward READY_TO_COMMIT.

Reviewer prose such as "looks good", "ready", or "approved" cannot
override structured findings and deterministic gates.

------------------------------------------------------------------------

# 31. MINOR Findings

MINOR findings do not alone block READY_TO_COMMIT.

They remain visible to the human.

The human may:

-   accept them;
-   request correction.

If the human requests a change that modifies the candidate, the existing
review proof no longer applies to the modified candidate.

The candidate must return through the appropriate correction lifecycle.

------------------------------------------------------------------------

# 32. FIX

A CODE finding requiring candidate modification routes to FIX.

Where practical, FIX should reuse the implementer context responsible
for the candidate.

However, session continuity is not required for recoverability.

If the original implementer session is unavailable, FIX must be
reconstructable from durable project and workflow evidence.

After a candidate-changing FIX:

``` text
FIX
 |
 v
VALIDATION
 |
 v
RE-REVIEW
```

is mandatory.

------------------------------------------------------------------------

# 33. RE-REVIEW

Where practical, RE-REVIEW should reuse the reviewer that produced the
findings.

If that reviewer context is unavailable, another appropriately
independent reviewer may perform RE-REVIEW using durable evidence
including the relevant previous findings.

RE-REVIEW must verify:

-   resolution of applicable findings;
-   exact current candidate;
-   applicable validation evidence;
-   absence of relevant regressions.

A previous review cannot authorize a changed candidate without the
required new review cycle.

------------------------------------------------------------------------

# 34. READY_TO_COMMIT

READY_TO_COMMIT describes the maturity of an exact candidate.

It means that the exact current candidate has satisfied all applicable
pre-commit workflow requirements, including:

-   applicable validation requirements;
-   applicable validation-waiver rules;
-   independent review requirements;
-   deterministic review gate requirements;
-   candidate-integrity requirements;
-   absence of unresolved conditions that invalidate commit readiness.

READY_TO_COMMIT is always relative to the exact current candidate and
its applicable workflow context.

READY_TO_COMMIT does not authorize COMMIT by itself.

``` text
READY_TO_COMMIT
!=
COMMIT AUTHORIZED
```

If a relevant change invalidates the conditions on which READY_TO_COMMIT
was established, READY_TO_COMMIT becomes non-applicable.

A stale, invalidated, or otherwise non-applicable READY_TO_COMMIT
cannot:

-   authorize entry into the Human Commit Gate;
-   contribute to COMMIT authorization.

------------------------------------------------------------------------

# 35. Human Commit Gate

The Human Commit Gate is a mandatory human interaction.

It is not another candidate maturity state.

## 35.1 Entry Precondition

The Human Commit Gate may only be entered for the exact current
candidate when that candidate has an applicable READY_TO_COMMIT.

Conceptually:

``` text
exact current candidate
        |
        v
applicable READY_TO_COMMIT?
        |
   +----+----+
   |         |
   NO        YES
   |         |
   v         v
GATE      HUMAN
FORBIDDEN COMMIT GATE
```

If READY_TO_COMMIT is:

-   absent;
-   stale;
-   invalidated;
-   associated with another candidate;
-   otherwise non-applicable to the exact current candidate;

entry into the Human Commit Gate is forbidden.

Human interaction cannot be used to bypass validation, review,
candidate-integrity, repository, or other requirements necessary to
establish READY_TO_COMMIT.

## 35.2 Information Presented to the Human

The human must be shown sufficient information to make the commit
decision, including as relevant:

-   TASK;
-   exact current candidate;
-   applicable READY_TO_COMMIT;
-   review status;
-   BLOCKER count;
-   IMPORTANT count;
-   MINOR findings;
-   validation evidence;
-   applicable waivers;
-   relevant NOT RUN validations;
-   repository conditions relevant to commit;
-   other exceptional conditions.

## 35.3 Human Decisions

The human may:

``` text
APPROVE COMMIT
REFUSE COMMIT
REQUEST CHANGE
```

## 35.4 Approval

Human approval applies only to the exact current candidate presented
through the Human Commit Gate.

Approval does not independently authorize COMMIT.

It is one of two mandatory COMMIT prerequisites:

``` text
1. applicable READY_TO_COMMIT(candidate)
AND
2. applicable HUMAN_APPROVAL(candidate)
```

Both must refer to the same exact current candidate.

## 35.5 Refusal

Human refusal does not automatically imply FIX.

COMMIT remains forbidden while the workflow waits for further authorized
human action.

## 35.6 Requested Change

A human-requested change must be classified before routing.

``` text
CODE
  -> FIX_REQUIRED

PRODUCT
  -> SPEC_REQUIRED

ARCHITECTURE
  -> PLAN_REQUIRED

TASKS
  -> TASKS_REQUIRED

ENVIRONMENT
or
REPOSITORY_MISMATCH
  -> BLOCKED
```

If the requested change modifies the candidate or otherwise invalidates
READY_TO_COMMIT, the candidate cannot return directly to the Human
Commit Gate.

The required workflow proofs must first be re-established.

------------------------------------------------------------------------

# 36. Candidate Integrity After Approval

Human approval is candidate-bound.

If the candidate changes after approval and before COMMIT:

``` text
approval(candidate A)
!=
approval(candidate B)
```

the previous approval becomes non-applicable to the new candidate.

Likewise, if any relevant event invalidates applicable READY_TO_COMMIT,
the existence of a previously recorded human approval does not preserve
COMMIT authorization.

The workflow must re-establish all invalidated prerequisites before
COMMIT.

Historical evidence remains traceable but cannot be used as currently
applicable authorization.

------------------------------------------------------------------------

# 37. COMMIT

COMMIT is authorized only when both mandatory prerequisites are
simultaneously satisfied for the exact current candidate.

``` text
COMMIT_ALLOWED(candidate)
=
READY_TO_COMMIT(candidate).applicable
AND
HUMAN_APPROVAL(candidate).applicable
```

Therefore:

``` text
READY_TO_COMMIT
+
NO HUMAN APPROVAL
-> COMMIT FORBIDDEN
```

``` text
HUMAN APPROVAL
+
NO APPLICABLE READY_TO_COMMIT
-> COMMIT FORBIDDEN
```

``` text
READY_TO_COMMIT(candidate A)
+
HUMAN_APPROVAL(candidate B)
-> COMMIT FORBIDDEN
```

``` text
STALE READY_TO_COMMIT(candidate A)
+
HUMAN_APPROVAL(candidate A)
-> COMMIT FORBIDDEN
```

``` text
READY_TO_COMMIT(candidate A)
+
STALE HUMAN_APPROVAL(candidate A)
-> COMMIT FORBIDDEN
```

Only:

``` text
APPLICABLE READY_TO_COMMIT(candidate A)
+
APPLICABLE HUMAN_APPROVAL(candidate A)
        |
        v
COMMIT(candidate A) AUTHORIZED
```

is valid.

If either prerequisite becomes absent or non-applicable before COMMIT,
COMMIT is forbidden.

The committed repository state must correspond to the exact candidate
for which both prerequisites are applicable.

------------------------------------------------------------------------

# 38. PUSH

After COMMIT, the expected commit is pushed to the expected remote
target.

PUSH alone does not close the TASK.

``` text
PUSHED
!=
CLOSED
```

The workflow continues through remote-state verification and hosted CI.

------------------------------------------------------------------------

# 39. Expected Remote Git State

For the active attempt, the workflow must be able to determine
conceptually:

``` text
current expected commit
+
expected remote target
```

The technical representation of the remote target belongs to PLAN.

The product-level requirement concerns the relationship between:

-   current expected commit;
-   expected remote target;
-   state actually published at that target.

## 39.1 Remote Presence Is Insufficient

The mere existence of the expected commit somewhere on the remote is
insufficient.

For example:

``` text
expected commit = C2

C2 exists somewhere on remote
```

does not by itself prove the expected remote state.

## 39.2 Expected Target Relationship

The expected remote target must correspond to the expected pushed state
for the current attempt.

Conceptually:

``` text
expected remote target
        |
        v
current expected pushed state
```

must hold before closure.

## 39.3 Remote Drift

If an incompatible external modification changes the expected remote
target before closure:

``` text
expected target -> C2
        |
        v
external change
        |
        v
expected target -> C3
```

the workflow has a REPOSITORY_MISMATCH.

The TASK cannot become CLOSED until the mismatch is explicitly resolved.

## 39.4 Remote Evidence Applicability

Remote-state evidence is relative to the current expected commit.

``` text
remote evidence(C1)
!=
remote evidence(C2)
```

Evidence from an obsolete expected commit cannot satisfy closure for the
current expected commit.

The mechanism used to verify remote state belongs to PLAN.

------------------------------------------------------------------------

# 40. Hosted CI

After PUSH, applicable hosted CI must be evaluated.

CI automates part of the Definition of Done.

CI does not itself define the Definition of Done.

``` text
CI GREEN
!=
TASK SUCCESS by itself
```

The CI result used for closure must apply to the current expected
commit.

------------------------------------------------------------------------

# 41. CI_FAILED Classification

CI failure must be classified before routing.

Minimum classifications:

``` text
CODE
ENVIRONMENT
PRODUCT
ARCHITECTURE
TASKS
```

CI failure does not automatically mean CODE defect.

------------------------------------------------------------------------

# 42. CI_FAILED --- CODE Recovery

When CI failure is classified as CODE and correction changes the
candidate, the proof cycle must restart.

Mandatory path:

``` text
CI_FAILED
   |
   v
CLASSIFY = CODE
   |
   v
FIX
   |
   v
VALIDATION
   |
   v
RE-REVIEW
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

The system must not allow:

``` text
CI_FAILED
-> FIX
-> PUSH
-> GREEN
-> CLOSED
```

without the required validation, review, READY_TO_COMMIT, human
authorization, commit, and push cycle.

------------------------------------------------------------------------

# 43. CI_FAILED --- Artifact Recovery

When CI failure is classified:

``` text
PRODUCT       -> SPEC_REQUIRED
ARCHITECTURE  -> PLAN_REQUIRED
TASKS         -> TASKS_REQUIRED
```

the corresponding SDD artifact decision is required.

If an approved artifact change affects the active TASK, READINESS must
run again before CODE or FIX resumes.

------------------------------------------------------------------------

# 44. CI_FAILED --- Environment Recovery

A CI failure classified ENVIRONMENT does not trigger CODE FIX merely
because CI is red.

The workflow remains blocked until the relevant environment problem is
resolved.

After resolution, a new applicable CI verification must be obtained for
the unchanged expected commit or for the subsequently authorized
expected commit, depending on the resolved workflow context.

The technical rerun mechanism belongs to PLAN.

------------------------------------------------------------------------

# 45. Current Expected Commit

At any point after COMMIT where commit-specific evidence matters, the
workflow must identify the current expected commit.

If a new correction cycle produces a new commit:

``` text
C1 -> obsolete for current closure
C2 -> current expected commit
```

old CI or remote evidence associated with C1 cannot close the workflow
for C2.

------------------------------------------------------------------------

# 46. CLOSED

A TASK may become CLOSED only when all applicable closure conditions are
satisfied.

V1 requires at minimum:

``` text
applicable review gate satisfied
+
applicable READY_TO_COMMIT established
+
applicable human commit approval
+
current expected candidate committed
+
current expected commit pushed
+
expected remote target corresponds
to current expected pushed state
+
no unresolved repository mismatch
affecting closure
+
hosted CI GREEN applicable
to current expected commit
```

Hosted CI GREEN for the current expected commit is non-waivable.

Therefore:

``` text
READY_TO_COMMIT != CLOSED

COMMITTED != CLOSED

PUSHED != CLOSED

old remote evidence != current remote evidence

old CI GREEN != current CI GREEN
```

------------------------------------------------------------------------

# 47. BLOCKED

BLOCKED represents a workflow condition preventing an authorized
transition.

A blocked condition must expose at least:

-   affected phase;
-   cause;
-   reason;
-   required resolution or routing.

Examples include:

``` text
TASK_DEPENDENCY
ENVIRONMENT
REPOSITORY_MISMATCH
```

The technical representation of BLOCKED and its causes belongs to PLAN.

------------------------------------------------------------------------

# 48. Repository Mismatch

SDD Agent must not silently absorb repository changes that invalidate or
make ambiguous the expected workflow context.

Relevant mismatch may affect:

-   baseline;
-   candidate;
-   applicable artifacts;
-   validations;
-   waivers;
-   review;
-   READY_TO_COMMIT;
-   human approval;
-   expected commit;
-   expected remote target;
-   CI;
-   closure evidence.

Sensitive transitions remain blocked until the mismatch is understood
and explicitly resolved.

------------------------------------------------------------------------

# 49. Repository Mismatch Resolution

Repository mismatch has explicit functional exits.

## 49.1 Compatible State

If the actual repository state is demonstrated to remain compatible with
the expected workflow context, RESUME may be allowed.

The technical compatibility proof belongs to PLAN.

## 49.2 Incompatible State Adopted as New Baseline

An incompatible external repository state cannot silently become the
baseline of the same attempt.

If the human decides to adopt that repository state as a new baseline,
the workflow uses RESTART and creates a new attempt.

Previous attempt history remains preserved.

## 49.3 Abandon

The human may choose ABANDON.

ABANDONED is not CLOSED.

------------------------------------------------------------------------

# 50. External Changes During Active Execution

External modifications affecting baseline, candidate, applicable
artifacts, expected commit, remote target, or other gate evidence must
not be silently incorporated.

When such a modification can invalidate workflow evidence, sensitive
transitions are blocked until explicit resolution.

------------------------------------------------------------------------

# 51. Persistence and Recovery

SDD Agent must survive orchestrator restart without requiring previous
AI conversations.

Persisted workflow state alone is not blindly trusted.

On recovery, the system must compare expected persisted state with
actual repository and artifact state before resuming.

If incompatible:

``` text
BLOCKED
```

until explicit resolution.

------------------------------------------------------------------------

# 52. Minimum Recoverable Information

The system must preserve enough durable information to recover at least:

-   active TASK;
-   execution attempt;
-   current workflow phase;
-   baseline identity;
-   candidate identity;
-   READINESS result;
-   expected validations;
-   validation evidence;
-   validation results;
-   waivers;
-   waiver applicability context;
-   reviews;
-   findings;
-   human decisions;
-   blockers;
-   classification/routing;
-   availability of relevant agent continuity;
-   READY_TO_COMMIT applicability;
-   human commit approval;
-   current expected commit;
-   expected remote target;
-   relevant remote-state evidence;
-   commit state;
-   push state;
-   hosted CI state;
-   next authorized or required action.

The persistence format belongs to PLAN.

------------------------------------------------------------------------

# 53. Durable Workflow Evidence

Any information required to authorize a future transition must be
recoverable independently of an AI conversation.

Examples include:

``` text
readiness result
validation evidence
waiver decision
review findings
READY_TO_COMMIT evidence
human approval
expected commit
remote evidence
CI result
```

Conversation continuity may improve efficiency but cannot be a
correctness dependency.

------------------------------------------------------------------------

# 54. Traceability

The system must preserve significant workflow history.

This includes, as relevant:

-   READINESS outcomes;
-   classifications;
-   validation results;
-   waivers;
-   waiver invalidation;
-   findings;
-   FIX;
-   RE-REVIEW;
-   READY_TO_COMMIT establishment and invalidation;
-   artifact decisions;
-   human approvals/refusals;
-   abandon;
-   restart;
-   commit;
-   push;
-   remote mismatch;
-   CI. 

The system is not required to preserve every model token, hidden
reasoning step, or raw conversation log.

------------------------------------------------------------------------

# 55. STATUS

STATUS must reflect both expected workflow state and relevant actual
reality.

It must not present an invalid gate as valid merely because the gate was
previously achieved.

STATUS must make clear:

``` text
where the TASK is
why it is there
what blocks it
what evidence applies
what action is currently authorized or required
```

------------------------------------------------------------------------

# 56. RESUME

RESUME continues an existing execution attempt.

It is permitted only when actual repository, artifact, and workflow
state remain compatible with the attempt's expected context.

RESUME does not silently establish a new baseline.

------------------------------------------------------------------------

# 57. RESTART

RESTART creates a new execution attempt for the same TASK.

It is appropriate when the previous attempt cannot safely continue under
its existing baseline/context and the human chooses to start a new
attempt.

RESTART:

-   establishes an appropriate new baseline;
-   preserves previous attempt history;
-   does not silently carry candidate-bound READY_TO_COMMIT, approvals,
    or waivers into the new attempt.

------------------------------------------------------------------------

# 58. ABANDON

The human may explicitly abandon an active execution attempt.

ABANDONED is distinct from CLOSED.

Abandonment stops the active workflow.

It does not automatically destroy candidate changes.

The human decides what should happen to existing work.

------------------------------------------------------------------------

# 59. Single Active Execution

V1 permits only one active execution attempt for a given TASK in the
project context at a time.

Previous completed, restarted, or abandoned attempts may remain in
history.

------------------------------------------------------------------------

# 60. Agent Context Independence

Agent conversations are execution aids, not durable truth.

## 60.1 New TASK

A new TASK requires a new implementer context.

Conversational history from the previous TASK's implementer must not be
required.

## 60.2 Initial Review

Initial REVIEW requires an independent reviewer context.

The reviewer must not receive implementer conversational history as
review authority.

## 60.3 FIX

FIX should reuse the relevant implementer context when available.

Recoverability without that context remains mandatory.

## 60.4 RE-REVIEW

RE-REVIEW should reuse the reviewer that raised the findings when
available.

If unavailable, another reviewer must be able to reconstruct the
required context from durable evidence.

------------------------------------------------------------------------

# 61. Functional Permissions

The product conceptually distinguishes permissions by role and phase.

## READINESS

May inspect.

Must not implement.

## IMPLEMENTATION

May modify CODE within authorized TASK scope.

Must not silently rewrite approved product or architecture contracts.

## REVIEW

May inspect and report.

Must not modify candidate.

## Human Commit Gate

May only be entered for the exact current candidate with applicable
READY_TO_COMMIT.

The human decides whether that exact candidate may be committed.

The technical enforcement mechanism belongs to PLAN.

------------------------------------------------------------------------

# 62. Conceptual Lifecycle Vocabulary

Names used by this SPEC describe product semantics.

They do not require every term to become a persistent technical enum
state.

Concepts such as:

``` text
BLOCKED
SPEC_REQUIRED
PLAN_REQUIRED
TASKS_REQUIRED
VALIDATION_FAILED
FIX_REQUIRED
CI_FAILED
```

may technically be represented as:

-   states;
-   phases;
-   results;
-   conditions;
-   causes;
-   routing decisions;

as determined by PLAN.

SPEC defines their meaning and required behavior, not their storage
representation.

------------------------------------------------------------------------

# 63. Core Product Invariants

## INV-01 --- SPEC Before PLAN

PLAN must not define unresolved PRODUCT behavior.

## INV-02 --- PLAN Before TASKS

TASK decomposition must derive from an approved architectural plan.

## INV-03 --- TASKS Before CODE

CODE executes an approved TASK contract.

## INV-04 --- One TASK at a Time

V1 works on one active TASK execution at a time.

## INV-05 --- READINESS Before CODE

CODE cannot begin before successful READINESS.

## INV-06 --- Failure Must Be Classified

A failure is not automatically CODE.

## INV-07 --- BUILD SUCCESS Is Not TASK SUCCESS

Build success alone cannot satisfy the task lifecycle.

## INV-08 --- Tests GREEN Do Not Prove SPEC Compliance

Tests may themselves encode incorrect assumptions.

## INV-09 --- Repository Is Durable Truth

Conversations are not authoritative project state.

## INV-10 --- Initial Reviewer Is Independent

The implementer cannot act as its own independent reviewer.

## INV-11 --- Reviewer Does Not Modify Candidate

Review observes and reports.

## INV-12 --- Review Exact Candidate

Review evidence applies to the exact candidate reviewed.

## INV-13 --- Candidate Change Invalidates Dependent Review Proof

A modified candidate must obtain applicable validation and review again.

## INV-14 --- BLOCKER and IMPORTANT Prevent Commit

Reviewer prose cannot override deterministic finding counts.

## INV-15 --- MINOR Alone Does Not Block Commit Readiness

MINOR remains visible to the human.

## INV-16 --- Human Commit Authorization Is Mandatory

READY_TO_COMMIT alone cannot authorize COMMIT.

## INV-17 --- Human Approval Is Candidate-Bound

Approval for Candidate A does not authorize Candidate B.

## INV-18 --- CI GREEN Alone Is Not CLOSED

Closure requires the full applicable lifecycle.

## INV-19 --- Current CI Evidence Only

CI GREEN for an obsolete commit cannot close the current expected
commit.

## INV-20 --- PRODUCT Decisions Are Human

V1 cannot silently decide product behavior.

## INV-21 --- Substantial Architecture Decisions Are Human

V1 cannot silently alter approved architectural contract.

## INV-22 --- TASK Contract Changes Are Human-Gated

Task scope, dependency, or decomposition changes require applicable
human approval.

## INV-23 --- Operational State Does Not Replace Artifacts

Required artifact changes must exist in authoritative artifacts.

## INV-24 --- Task Number Is Not Execution Order

Dependencies determine readiness.

## INV-25 --- Future Scope Is Not Automatically a Current Defect

Review must respect explicitly deferred TASK scope.

## INV-26 --- Restart Must Be Recoverable

Loss of conversation cannot destroy required workflow knowledge.

## INV-27 --- CI Failure Requires Classification

CI_FAILED does not automatically route to CODE.

## INV-28 --- Waiver Is Context-Bound

A validation waiver applies only to the exact validation and context
approved by the human.

## INV-29 --- Waiver Does Not Automatically Survive Context Change

Relevant changes to attempt, candidate, applicable contract, validation
obligation, evidence, or cause invalidate automatic waiver reuse.

## INV-30 --- Obsolete Waiver Is Historical Evidence Only

A non-applicable waiver remains traceable but cannot satisfy a current
gate.

## INV-31 --- Remote Evidence Is Commit-Bound

Remote-state evidence applies only to the expected commit/context to
which it relates.

## INV-32 --- Remote Drift Blocks Closure

Incompatible drift of the expected remote target before closure prevents
CLOSED until explicitly resolved.

## INV-33 --- Human Commit Gate Requires READY_TO_COMMIT

The Human Commit Gate may only be entered for the exact current
candidate with an applicable READY_TO_COMMIT.

Human approval cannot bypass the maturity gate.

## INV-34 --- COMMIT Requires Two Applicable Proofs

COMMIT requires both:

``` text
applicable READY_TO_COMMIT(candidate)
AND
applicable HUMAN_APPROVAL(candidate)
```

for the same exact candidate.

Neither condition is sufficient alone.

## INV-35 --- Invalidated Commit Prerequisite Forbids COMMIT

If either READY_TO_COMMIT or human approval becomes non-applicable
before COMMIT, COMMIT is forbidden until all required prerequisites have
been re-established.

------------------------------------------------------------------------

# 64. User Stories --- Core Paths

## US-01 --- Select a TASK

As a human, I want to select the TASK to execute so that task
prioritization remains under human control.

## US-02 --- Check Dependencies

As a human, I want SDD Agent to detect unsatisfied mandatory
dependencies so that CODE does not begin prematurely.

## US-03 --- Run READINESS

As a human, I want READINESS to evaluate the applicable SDD contract
before implementation so that CODE starts only when authorized.

## US-04 --- Route Product Ambiguity

As a human, I want unresolved PRODUCT questions detected during
execution to route to SPEC so that implementers do not invent product
behavior.

## US-05 --- Route Architecture Ambiguity

As a human, I want substantial architectural ambiguity routed to PLAN.

## US-06 --- Route Task Contract Ambiguity

As a human, I want task-scope or dependency ambiguity routed to TASKS.

## US-07 --- Implement One TASK

As a human, I want the implementer to modify only the active TASK scope.

## US-08 --- Validate Before Review

As a human, I want required validations executed before review so that
review receives explicit evidence.

## US-09 --- Independent Review

As a human, I want a reviewer independent from implementation to
evaluate the exact candidate against SPEC, PLAN, TASKS, and validation
evidence.

## US-10 --- Fix Blocking Findings

As a human, I want BLOCKER and IMPORTANT findings to prevent commit and
route to correction.

## US-11 --- Re-review Fixes

As a human, I want candidate-changing fixes to be validated and reviewed
again.

## US-12 --- Human Commit Approval

As a human, I want only the exact current candidate with applicable
READY_TO_COMMIT to be presented for explicit commit authorization.

## US-13 --- Commit Only With Both Gates

As a human, I want COMMIT to require both applicable READY_TO_COMMIT and
applicable human approval for the same exact candidate.

## US-14 --- Push and CI

As a human, I want an approved commit pushed and verified by hosted CI.

## US-15 --- Close Only After Complete Success

As a human, I want CLOSED to mean that all required review, readiness,
approval, Git, remote, and CI conditions are satisfied.

------------------------------------------------------------------------

# 65. User Stories --- Failure and Negative Paths

## US-16 --- Dependency Not Closed

Given a TASK has an unsatisfied mandatory dependency, when READINESS
evaluates it, then execution is blocked and CODE is forbidden.

## US-17 --- Dirty Repository at Start

Given pre-existing repository changes exist before the TASK attempt,
when execution begins, then SDD Agent exposes them and blocks until
explicit resolution.

## US-18 --- Validation Failure Classified CODE

Given required validation executes and fails, when the failure is
classified CODE, then the workflow routes to FIX rather than REVIEW.

## US-19 --- Validation Failure Classified Environment

Given required validation cannot complete because of environment
failure, when classified ENVIRONMENT, then CODE is not automatically
blamed.

## US-20 --- Waiver Accepted

Given a required validation is NOT RUN because of ENVIRONMENT and is
waiver-eligible, when the human approves an applicable waiver, then
REVIEW may proceed while the validation remains NOT RUN.

## US-21 --- Waiver Refused

Given a waiver-eligible NOT RUN validation, when the human refuses the
waiver, then READY_FOR_REVIEW remains forbidden.

## US-22 --- Non-CODE Review Finding

Given REVIEW identifies a PRODUCT, ARCHITECTURE, or TASKS issue, then
the issue routes to the corresponding upstream artifact rather than
being silently fixed as CODE.

## US-23 --- Human Commit Gate Before READY_TO_COMMIT

Given the exact current candidate does not have applicable
READY_TO_COMMIT, when an attempt is made to enter the Human Commit Gate,
then Human Commit Gate entry is forbidden.

## US-24 --- Human Refuses Commit

Given a candidate is READY_TO_COMMIT, when the human refuses commit
without requesting a change, then COMMIT remains forbidden and the
workflow awaits further human action.

## US-25 --- Human Requests CODE Change

Given a candidate is READY_TO_COMMIT, when the human requests a CODE
change, then the candidate routes to FIX and must pass VALIDATION and
RE-REVIEW again before a new applicable READY_TO_COMMIT and Human Commit
Gate can authorize COMMIT.

## US-26 --- Approval Without READY_TO_COMMIT

Given a human approval exists for a candidate but applicable
READY_TO_COMMIT is absent, stale, or invalidated, then COMMIT is
forbidden.

## US-27 --- READY_TO_COMMIT Without Approval

Given applicable READY_TO_COMMIT exists for a candidate but applicable
human approval does not exist, then COMMIT is forbidden.

## US-28 --- Commit Preconditions Refer to Different Candidates

Given READY_TO_COMMIT applies to Candidate A and human approval applies
to Candidate B, then COMMIT is forbidden for both candidates until both
applicable prerequisites refer to the same exact current candidate.

## US-29 --- CI Failure Classified CODE

Given the current expected commit fails hosted CI because of CODE, when
the candidate is corrected, then the new candidate passes FIX,
VALIDATION, RE-REVIEW, READY_TO_COMMIT, Human Commit Gate, COMMIT, PUSH,
and hosted CI again.

## US-30 --- CI Failure Classified Artifact

Given hosted CI failure exposes a PRODUCT, ARCHITECTURE, or TASKS issue,
then the workflow routes upstream and performs READINESS again after any
applicable approved artifact change.

## US-31 --- Repository Mismatch

Given repository reality no longer matches the expected attempt context,
then sensitive transitions remain blocked until compatible RESUME,
RESTART, or ABANDON is explicitly chosen as applicable.

## US-32 --- Lost Agent Session

Given an implementer or reviewer session is unavailable, then the
workflow can reconstruct required context from durable project and
workflow evidence.

## US-33 --- Waiver Invalidated by Candidate Change

Given Candidate A has an eligible NOT RUN validation and an applicable
human waiver, when Candidate A changes materially into Candidate B, then
the old waiver does not automatically apply to Candidate B.

Candidate B must obtain new applicable validation evidence and, if still
eligible and necessary, a new human waiver.

## US-34 --- Waiver Invalidated by Contract Change

Given an applicable waiver exists, when SPEC, PLAN, TASKS, or the
relevant validation obligation changes materially, then the old waiver
cannot automatically satisfy the new context.

## US-35 --- Waiver Invalidated by New Evidence

Given a validation was NOT RUN for ENVIRONMENT and waived, when it later
executes and returns FAILED, then the waiver no longer applies and
FAILED must be classified and routed.

## US-36 --- Remote Drift Before Closure

Given current expected commit C2 was pushed and the expected remote
target corresponded to C2, when an incompatible external change causes
that target to point to another state, then REPOSITORY_MISMATCH blocks
CLOSED even if CI(C2) is GREEN.

## US-37 --- Artifact Ambiguity During READINESS

Given a TASK is evaluated during READINESS and the applicable SPEC,
PLAN, or TASKS contract is ambiguous or insufficient to authorize CODE,
when READINESS evaluates the ambiguity, then CODE remains forbidden.

The issue is classified and routed:

``` text
PRODUCT       -> SPEC_REQUIRED
ARCHITECTURE  -> PLAN_REQUIRED
TASKS         -> TASKS_REQUIRED
```

CODE may resume only after the required decision or artifact correction
is resolved and READINESS succeeds again.

------------------------------------------------------------------------

# 66. Conceptual Task Lifecycle

The normal lifecycle is:

``` text
TASK SELECTED
      |
      v
  READINESS
      |
      +-----------------------------+
      |                             |
      | READY                       | NOT READY
      v                             v
IMPLEMENTATION             CLASSIFY / ROUTE / BLOCK
      |
      v
 VALIDATION
      |
      +-----------------------------+
      |                             |
      | ACCEPTABLE                  | FAILED / INSUFFICIENT
      v                             v
READY_FOR_REVIEW           CLASSIFY / ROUTE
      |
      v
INDEPENDENT REVIEW
      |
      +-------------------------------------+
      |                                     |
      | BLOCKER=0                           | BLOCKER>0
      | AND IMPORTANT=0                     | OR IMPORTANT>0
      v                                     v
READY_TO_COMMIT                       CLASSIFY FINDINGS
      |                                     |
      v                                     v
HUMAN COMMIT GATE                    FIX / ARTIFACT ROUTE
      |                                     |
      | APPROVED                            v
      v                                 VALIDATION
   COMMIT                                  |
      |                                     v
      v                                 RE-REVIEW
    PUSH                                    |
      |                                     v
      v                              READY_TO_COMMIT
REMOTE STATE CHECK
      |
      v
HOSTED CI
   /     \
GREEN   FAILED
 |         |
 |      CLASSIFY
 |       /  |  \
 |      /   |   \
 |   CODE  ENV  ARTIFACT
 |     |     |      |
 |     v     v      v
 |    FIX  BLOCK  SPEC/PLAN/TASKS
 |     |
 |     v
 | VALIDATION
 |     |
 |     v
 | RE-REVIEW
 |     |
 |     v
 | READY_TO_COMMIT
 |     |
 |     v
 | HUMAN COMMIT GATE
 |     |
 |     v
 |   COMMIT
 |     |
 |     v
 |    PUSH
 |     |
 |     v
 | HOSTED CI
 |
 v
CLOSURE CHECK
 |
 v
CLOSED
```

Human Commit Gate entry is permitted only when READY_TO_COMMIT is
currently applicable to the exact candidate presented.

COMMIT requires both applicable READY_TO_COMMIT and applicable human
approval for that same candidate.

This diagram is conceptual.

PLAN determines the technical state-machine representation.

------------------------------------------------------------------------

# 67. Gate Semantics

A gate is evidence valid in a particular context.

Gate applicability may depend on:

``` text
TASK
attempt
SPEC
PLAN
TASKS
baseline
candidate
validation obligations
validation evidence
applicable waivers
review evidence
READY_TO_COMMIT
human decisions
human approval
expected commit
expected remote target
remote evidence
CI result
```

A relevant change to a gate precondition invalidates dependent gate
evidence.

Examples:

``` text
candidate changes
-> previous candidate review no longer sufficient

candidate changes
-> previous READY_TO_COMMIT no longer sufficient

candidate changes
-> previous candidate approval no longer sufficient

attempt changes
-> previous attempt waiver no longer sufficient

expected commit changes
-> old CI result no longer sufficient

expected remote state changes incompatibly
-> closure blocked
```

Workflow gates are contextual proofs, not permanent labels.

------------------------------------------------------------------------

# 68. Gate Invalidation

The system must prevent stale evidence from authorizing later workflow
transitions.

Examples of invalidation include:

-   candidate modification after review;
-   candidate modification after READY_TO_COMMIT;
-   candidate modification after human approval;
-   applicable artifact change;
-   new attempt after RESTART;
-   validation evidence changing;
-   waiver context changing;
-   repository mismatch;
-   expected commit changing;
-   incompatible remote target drift.

If READY_TO_COMMIT becomes non-applicable:

``` text
Human Commit Gate entry -> FORBIDDEN
COMMIT                  -> FORBIDDEN
```

If human approval becomes non-applicable:

``` text
COMMIT -> FORBIDDEN
```

When a gate becomes invalid, the workflow returns to the appropriate
earlier proof step.

------------------------------------------------------------------------

# 69. Safety Principles

SDD Agent V1 must prevent or reject the following workflow shortcuts:

-   BUILD SUCCESS = TASK SUCCESS;
-   tests GREEN = SPEC compliance proven;
-   reviewer says "ready" = deterministic gate passed;
-   every failure = CODE defect;
-   conversation history = project truth;
-   task number = execution order;
-   missing future-task functionality = automatically current-task
    defect;
-   reviewed candidate differs from committed candidate;
-   CI GREEN alone = CLOSED;
-   validation waiver = GREEN;
-   operational workflow state replaces authoritative SDD artifacts;
-   old CI GREEN = current CI GREEN;
-   approval for Candidate A = approval for Candidate B;
-   external repository changes silently become accepted
    baseline/candidate;
-   CI_FAILED -\> FIX -\> PUSH -\> GREEN -\> CLOSED without the required
    validation, review, READY_TO_COMMIT, human gate, commit, and push
    cycle;
-   waiver for one attempt automatically reused in another;
-   waiver for Candidate A automatically reused for Candidate B;
-   obsolete waiver used as current gate evidence;
-   new FAILED validation hidden by an old waiver;
-   commit merely existing somewhere on remote = expected remote state
    confirmed;
-   old remote evidence used for a new expected commit;
-   CLOSED while a relevant repository mismatch remains unresolved;
-   Human Commit Gate entered without applicable READY_TO_COMMIT;
-   human approval treated as equivalent to READY_TO_COMMIT;
-   human approval without applicable READY_TO_COMMIT used to authorize
    COMMIT;
-   READY_TO_COMMIT without applicable human approval used to authorize
    COMMIT;
-   READY_TO_COMMIT for one candidate combined with approval for another
    candidate;
-   stale READY_TO_COMMIT combined with current approval to authorize
    COMMIT;
-   current READY_TO_COMMIT combined with stale approval to authorize
    COMMIT.

The only valid COMMIT authorization is:

``` text
APPLICABLE READY_TO_COMMIT(candidate)
AND
APPLICABLE HUMAN_APPROVAL(candidate)
-> COMMIT(candidate)
```

------------------------------------------------------------------------

# 70. SPEC / PLAN Boundary

This SPEC defines required product behavior.

It intentionally does not select the technical implementation
architecture.

The following belong to PLAN unless a future product requirement makes
them product-significant:

-   implementation language;
-   application framework;
-   LangGraph;
-   n8n;
-   provider abstraction design;
-   AgentRunner abstraction;
-   Claude Code runner implementation;
-   Codex runner implementation;
-   CLI design;
-   API design;
-   process/session management;
-   structured report schemas;
-   JSON Schema;
-   technical state-machine representation;
-   persistence technology;
-   `.sdd/` directory layout;
-   Git library;
-   worktrees;
-   sandbox strategy;
-   exact Git commands;
-   remote-state verification implementation;
-   hosted CI provider integration;
-   webhook versus polling;
-   classes/modules/packages;
-   prompt templates;
-   token optimization mechanisms.

SPEC determines what behavior must be guaranteed.

PLAN determines how the system will guarantee it.

------------------------------------------------------------------------

# 71. Specification Acceptance Gate

The specification itself must be independently reviewed before PLAN
begins.

Findings use:

``` text
BLOCKER
IMPORTANT
MINOR
```

The SPEC gate is deterministic:

``` text
if BLOCKER > 0:
    SPEC_NEEDS_FIXES

else if IMPORTANT > 0:
    SPEC_NEEDS_FIXES

else:
    SPEC_READY
```

MINOR findings alone do not block SPEC_READY.

Reviewer prose cannot override this rule.

------------------------------------------------------------------------

# 72. Current Specification State

This document is the complete standalone product specification for:

``` text
SDD Agent
V1 semi-automatic
Specification revision V3
```

It is intended to be independently understandable without access to:

-   previous specification revisions;
-   previous AI conversations;
-   previous review reports.

The following product decisions are incorporated into the normative
contract:

``` text
SPEC-001 through SPEC-083
SPEC-084
SPEC-085
SPEC-086
```

In particular:

``` text
SPEC-084
Human Commit Gate entry requires an applicable
READY_TO_COMMIT for the exact current candidate.

SPEC-085
COMMIT requires both applicable READY_TO_COMMIT
and applicable human approval for the same
exact current candidate.

SPEC-086
If either COMMIT prerequisite becomes
non-applicable, COMMIT is forbidden.
```

Independent SPEC review has been completed.

The review produced:

``` text
BLOCKER = 0
IMPORTANT = 0
```

which deterministically yielded:

``` text
SPEC_READY
```

Current specification gate:

``` text
SPEC = SPEC_READY
```

This status records the already-achieved independent SPEC gate. Any
future product-level change affecting this specification remains subject
to the applicable SDD invalidation, review, and approval rules.

------------------------------------------------------------------------

# End of Specification
