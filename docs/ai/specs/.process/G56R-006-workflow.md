# SpecKit Workflow: G56R-006 — Capability-aware Resolver, Materializer, Installer, and Strict Override

**Template Version**: 1.0.0
**Created**: 2026-08-24
**Purpose**: Execute the G56R-006 framework slice from human-approved scope through a capability-aware, byte-proven, rollback-safe Codex agent installation path without qualifying final production routes.

---

## Execution Contract

Run this workflow only from the registered feature worktree and branch named below. The planning stage owns the six SDD phases through Analyze; implementation begins only after those artifacts and gates are committed.

The human-approved decisions in the Design Concept are binding. If later artifacts conflict with that record, repair the later artifact rather than silently changing scope.

---

## Design Concept

This workflow was enriched from the required Grill Me interview. The complete Q&A log, Goals, Non-goals, Decisions, and Open Questions live at:

```text
docs/ai/specs/.process/G56R-006-design-concept.md
```

Re-read it before every phase. Once autopilot begins, later clarifications use `/speckit-clarify` and the consensus protocol; Grill Me is not part of the autonomous phase loop.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | 4 stories, 29 FRs, 9 success criteria, 13 acceptance scenarios, and 0 clarification markers |
| Clarify | `/speckit-clarify` | ✅ Complete | 15 questions resolved across roster, route, override, ownership, rollback, compatibility, and response boundaries; G2 passed with 0 markers |
| Plan | `/speckit-plan` | ✅ Complete | Six planning artifacts, two closed contracts, exact 8-authored/41-generated implementation path accounting, and G3 with 0 unresolved markers |
| Checklist | `/speckit-checklist` | ✅ Complete | 123 checks across error handling, state management, data integrity, and reliability; zero gaps; G4 passed |
| Tasks | `/speckit-tasks` | ✅ Complete | 53 dependency-ordered tasks, 14 RED→GREEN pairs, all 29 FRs and 13 scenarios mapped; G5 passed |
| Analyze | `/speckit-analyze` | ✅ Complete | One medium manifest/data-model naming drift remediated; zero unresolved findings; G6 passed |
| Confidence Gate | G6.5 | 🔄 In Progress | Advisory composite confidence before implementation |
| Implement | `/speckit-implement` | ⏳ Pending | Execute tasks with targeted and repository-wide verification |
| Post | Post-Implementation | ⏳ Pending | Canonical closeout, generated artifacts, PR, UAT boundary, and retrospective |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⏭️ Skipped | ⚠️ Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | Four stories and all requirements are testable; no clarification markers remain |
| G2 | After Clarify | Roster, manifest, snapshot, override, optional-helper, ownership, evidence, and failure semantics are unambiguous |
| G3 | After Plan | Constitution and reviewability gates pass; every changed/generated path and rollback boundary is declared |
| G4 | After Checklist | Every genuine gap is remediated or explicitly scoped out |
| G5 | After Tasks | Every FR has a vertical TDD task; dependency and parallel markers are sound |
| G6 | After Analyze | No unresolved finding remains at any severity and no Design Concept drift exists |
| G6.5 | Before Implement | Composite confidence meets the autonomous threshold or receives explicit disposition |
| G7 | After each implementation group | Focused RED→GREEN evidence and relevant broader gates pass |

---

## Prerequisites

### Worktree and Branch

- Worktree: use the registered checkout returned by `git rev-parse --show-toplevel` for the branch below. Do not encode a maintainer-specific absolute path in committed artifacts.
- Branch: `g56r-006-resolver-materializer-installer-strict-override`
- Base at scaffold: `origin/main` commit `5b648e8a7ad085c7e2ee720c6f2fa0c7b6bdbb52`
- Remote: `origin`
- Dependency: G56R-005 is complete/archived after PR #487; PR #500 merged its post-merge hygiene into this baseline.
- Never run this workflow from `main`, a detached checkout, or another feature worktree.

### Worktree Bootstrap

No bootstrap command was run. Root `AGENTS.md` states that the repository test suite needs no bootstrap and runs directly with `python3 tests/speckit-pro/run-all.py`. `docs-site/` is the only dependency-bearing surface and is not needed for scaffold.

If implementation changes a tracked `.md`, `.py`, or `.sh` under `tests/speckit-pro/` and therefore invokes a docs reference command, first run `pnpm --dir docs-site install --frozen-lockfile` once in this worktree. The clone-level generated merge driver was already configured as `exit 0`.

### Runtime and Capability Context

- Official SpecKit CLI: `specify 0.14.2`.
- Reviewability preset: `speckit-pro-reviewability` v1.0.0 is enabled; `spec-template`, `plan-template`, and `tasks-template` all resolve to its project-local overlays.
- Installed Codex agents: the required `install-codex-agents` dry-run used user-scope destination `~/.codex/agents` and model `gpt-5.5`; it returned `status=ok`, `mutation_status=no_op`, and all 13 bundled TOMLs current, including `uat-runbook-author.toml`.
- Blind-spot pass: ran with five findings surfaced and two set aside. All five surfaced findings were resolved during the 14-question Grill Me interview.
- Roadmap tools: no tool count or explicit tool list was recorded. Use only repository-local Python 3.11 runner/helpers, Git, the official `specify` CLI, and the existing SpecKit commands unless Plan grounds another need.
- No external documentation, live model-availability claim, or live user-home mutation is part of this framework slice.

Capability path: codebase and spec context -> current repository files plus the read-only `codebase-analyst`; Evidence: `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md`, `docs/ai/specs/.process/G56R-006-design-concept.md`, `speckit-pro/speckit_pro_runner/helpers/install.py`, and `speckit-pro/speckit_pro_runner/agent_materialization.py`; Confidence: high (direct current-tree evidence and a fixed-shape analyst result).

### Reviewability and Split Decision

- Setup helper invocation: `reviewability-gate` in `setup` mode against the technical roadmap.
- Runner result: `status=warn`, `pass=true`, no blockers. The single warning was roadmap-wide aggregation across three primary surfaces; the helper reported 395 reviewable LOC, 2 production files, and 15 total files from the last roadmap budget record.
- G56R-006 entry budget: primary surface `harness/adapter`, projected 265 reviewable LOC, approximately 4 production files, approximately 10 total files, one suggested slice, status `ok`.
- Grill Me estimator inputs: 4 user stories, 10 files, 18 FR groups, `new_vs_modify=modify`.
- Estimator result: `estimated_loc=385`, `suggested_slices=1`, `status=ok`.
- Split decision: keep one thin vertical resolver/materializer/installer policy slice. It is end-to-end rather than horizontally layer-sliced. Re-run plan-phase authoritative reviewable-LOC evidence after Plan declares exact files.

### Constitution Validation

| Principle | Requirement for G56R-006 | Verification |
|-----------|---------------------------|--------------|
| I. Plugin structure | Runtime stays under `speckit-pro/`; repository-only tests stay under `tests/speckit-pro/` | ✅ Verified — Layer 1 passed 1511/1511 |
| II. Cross-platform runtime | Python 3.11+ stdlib, structured JSON/TOML parsing, path APIs, argv arrays, no active Bash or `jq` | ✅ Verified — Layer 4 passed 12282/12282, including active-path and Bash-confinement gates |
| III. Semantic versioning | No manual manifest or version edit | ✅ Verified — Layer 1 manifest checks passed; no version edit is in scope |
| IV. Test coverage | Focused unit coverage plus full Python-authoritative suite | ✅ Verified — full baseline passed 14012/14012 |
| V. Conventional commits | Lowercase scope and plain-English description | ✅ Verified for planning checkpoints; exact PR-title validation remains a later release-readiness gate |
| VI. KISS/YAGNI | Extend the existing materializer and installer; no parallel resolver or speculative qualification layer | ✅ Verified for G0; Plan and Analyze must re-check the one-framework boundary |

**Constitution Check:** ✅ Verified — G0 baseline 14012/14012, reviewability setup `warn` with `pass=true`, and no reviewability blockers.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | G56R-006 |
| **Name** | Capability-aware Resolver, Materializer, Installer, and Strict Override |
| **Branch** | `g56r-006-resolver-materializer-installer-strict-override` |
| **Stage** | `plan` |
| **Dependencies** | G56R-005 complete/archived; consumes G56R-003 materializer and G56R-005 contracts/reason ordering |
| **Enables** | G56R-007, G56R-008, G56R-009, G56R-010 |
| **Priority** | P1 |

### Success Criteria Summary

- [ ] A trusted versioned manifest explicitly activates route-aware mode; no-manifest calls preserve current static install behavior.
- [ ] The source bundle remains exactly 13 TOMLs; the route-aware destination requires 12 core agents and treats only `autopilot-fast-helper` as optional.
- [ ] One fresh batch snapshot and any bounded fallback probes join to every ordered per-agent resolution record.
- [ ] The canonical materializer emits exact final TOML for explicit model and effort while proving instructions, tools, skills, MCP, sandbox, mutation, and output contracts unchanged.
- [ ] Every required agent resolves and materializes before any write; any required miss yields complete attempts for all agents and zero mutation.
- [ ] A strict global override never falls back for required agents. A compatible helper override installs; an incompatible helper uses only a validated no-helper path.
- [ ] Optional-helper removal occurs only with managed-file proof and participates in the rollback-backed batch.
- [ ] The helper response contains a deterministic top-level routing block with snapshot, attempts, rejection reasons, route resolutions, and resolved policy IDs.
- [ ] Fake-home tests prove dry-run/no-op, apply, verification, rollback, previous-known-good preservation, managed removal, manual remediation, and restart guidance.
- [ ] No live model call, real-user-home write, final route aggregate, route qualification, plugin version change, or downstream cohort expansion enters this slice.

---

## Phase 1: Specify

**When to run:** Start from the Design Concept and roadmap. Specify WHAT and WHY; do not freeze implementation mechanics that belong in Plan.

### Specify Prompt

```text
/speckit-specify

Create G56R-006: Capability-aware Resolver, Materializer, Installer, and Strict Override.

Source of truth:
- docs/ai/specs/.process/G56R-006-design-concept.md
- docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md
- archived G56R-005 contracts and current shipped artifacts

Required user stories:
1. Route-aware dry-run/apply resolves and byte-proves the complete required roster from one fresh snapshot and a trusted policy manifest.
2. A strict global model override validates the complete required set before mutation; helper behavior follows Q8's compatible-install or validated no-helper decision.
3. An unavailable optional helper is safely omitted or removed only with managed-file proof, without failing the required roster.
4. Any unresolved route or filesystem failure returns complete structured evidence and preserves the previous known-good installation through zero-write or rollback.

Encode the Design Concept Goals, Non-goals, all Q1-Q14 decisions, the 12-required-plus-one-optional roster, static compatibility mode, manifest activation, one-batch snapshot, top-level routing response, deterministic-only acceptance boundary, and downstream roster-reconciliation open question.

Make every requirement and acceptance scenario objective. Keep final route qualification, final aggregates, live UAT, real-home mutation, per-agent overrides, arbitrary effort maps, Claude installation, payload release integration, and downstream cohort expansion out of scope.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 29 |
| User Stories | 4 |
| Acceptance Criteria | 13 scenarios |

### Files Generated

- [x] `specs/g56r-006-resolver-materializer-installer-strict-override/spec.md`

---

## Phase 2: Clarify

**When to run:** After Specify. Ask at most five questions per session and resolve only ambiguities that materially change behavior.

### Clarify Prompts

#### Session 1: Roster and Cross-spec Boundary

```text
/speckit-clarify

Validate that the spec consistently distinguishes:
- the strict 13-file bundled source inventory
- 12 required destination agents
- one optional fast helper
- the downstream roadmap's stale 11-agent cohort
- framework support in G56R-006 versus route qualification in G56R-007 through G56R-010

Do not expand G56R-006 into cohort qualification. Preserve the Design Concept's required downstream reconciliation before G56R-011 final composition.
```

#### Session 2: Resolution and Override Semantics

```text
/speckit-clarify

Make ordered preferred/fallback evaluation, one-batch snapshot binding, bounded probe use, all-agent diagnostic completion, required-agent strict override, and optional-helper override/no-helper behavior unambiguous. Ensure a required-agent miss always means zero writes and no silent fallback after an explicit override.
```

#### Session 3: State, Ownership, and Evidence

```text
/speckit-clarify

Clarify managed-helper ownership proof, static-mode compatibility, manifest trust/provenance, rollback restoration of bytes and modes, no-op/restart guidance, and the exact top-level routing response fields. Preserve the no-live-call and fake-home-only acceptance boundary.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Roster and cross-spec boundary | 5 | Current 13-file static installer behavior is authoritative; route-aware policy separates 12 required agents from one optional helper; the named downstream cohort mismatch remains explicit and deferred; static responses omit policy-dependent routing data. |
| 2 | Resolution and override semantics | 5 | All 12 required agents receive complete ordered diagnostics from one snapshot; bounded probes remain child evidence; strict override evaluates one tuple per agent with no fallback; helper override requires a validated no-helper continuation; required misses have an exact zero-mutation response. |
| 3 | State, ownership, and evidence | 5 | Closed managed-helper proof, trusted-manifest activation, static response and restart compatibility, byte/mode rollback proof, and the exact top-level route-aware `routing` object; no item required routed consensus. |

### Consensus Resolution Log

| # | Type | Question/Gap/Finding | Categories | Round | Outcome | Resolution | Analysts Used |
|---|------|----------------------|------------|-------|---------|------------|---------------|
| 1 | Clarify | Which authority defines no-manifest static compatibility: the current 13-file installer or the older 10-file prose roster? | codebase, spec | 1 | both-agree | Preserve the current Python installer's route-agnostic 13-file copy/verify behavior; treat the older 10-file prose roster as stale, keep helper optionality route-aware only, and omit the policy-dependent routing block in static responses. | codebase-analyst, spec-context-analyst |
| 2 | Clarify | How should G56R-006 record the stale downstream 11-agent cohort without resolving downstream qualification here? | spec, codebase | 1 | both-agree | Name `artifact-author`, `sweep-analyst`, `sweep-classifier`, proposed `consensus-synthesizer`, and proposed `gate-validator` as downstream reconciliation inputs without assigning cohorts, changing aggregate counts, or qualifying routes. | codebase-analyst, spec-context-analyst |
| 3 | Clarify | If the strict helper override is incompatible and the no-helper continuation does not validate, may the required batch still mutate? | spec | 1 | agree | Fail the whole route-aware batch before mutation; helper omission is safe only through a validated no-helper continuation, and no alternate helper fallback may follow an explicit override miss. | spec-context-analyst |

---

## Phase 3: Plan

**When to run:** After Clarify. Produce the technical blueprint and exact changed/generated path inventory.

### Plan Prompt

```text
/speckit-plan

Plan G56R-006 from:
- specs/g56r-006-resolver-materializer-installer-strict-override/spec.md
- docs/ai/specs/.process/G56R-006-design-concept.md
- docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md
- .specify/memory/constitution.md

Tech stack and repository constraints:
- Python 3.11+ standard library only for active repository tooling
- structured JSON and tomllib parsing, deterministic UTF-8, pathlib-safe paths
- direct argv arrays with shell=False; no new Bash, jq, PowerShell, WSL, or package dependency
- extend speckit-pro/speckit_pro_runner/agent_materialization.py and helpers/install.py rather than creating parallel frameworks
- preserve unrelated user-owned agents and current static install behavior
- account for runner manifest/checksum metadata, generated release payloads, docs reference generation, and the Layer 6 source-digest corpus whenever their inputs change

Architecture decisions to preserve:
- Q3 chose “Extend materializer”: original source binding remains authoritative while the selected explicit route produces exact destination bytes and all non-route fields remain invariant.
- Q4 and Q12 chose one injectable runner-owned adapter and “One batch snapshot”.
- Q5 chose “Structured response”: routing evidence is top-level data, not a report file or mutation metadata.
- Q6-Q7 chose explicit route mode through one trusted versioned manifest path; absent input retains static compatibility.
- Q8 applies a compatible override to the helper, but optionality wins on incompatibility through the validated no-helper path.
- Q9 requires proven managed ownership before helper deletion.
- Q10-Q11 require a complete plan before mutation, exhaustive bounded diagnostics, and rollback-backed apply.

Plan the closed manifest/response data model, adapter injection boundary, resolver-to-G56R-005 contract mapping, extended materializer identity, complete mutation plan, managed deletion proof, rollback/verification state machine, backward-compatible request validation, and fake-home fixture matrix.

Quote and link the Design Concept for every decision that changes architecture. Declare every source, test, contract, generated, and documentation path as NEW or MODIFIED. Re-run the authoritative plan-phase reviewable-LOC estimator and preserve one vertical slice unless exact evidence now requires a split.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ✅ | One vertical slice; 4 production and 8 authored implementation files, 6 planning artifacts, and 41 generated follow-through paths |
| `research.md` | ✅ | Eight decisions with rejected alternatives and Design Concept provenance |
| `data-model.md` | ✅ | Nine closed entities plus static and route-aware state transitions |
| `contracts/` | ✅ | Versioned trusted-manifest contract and route-aware request/response contract |
| `quickstart.md` | ✅ | Deterministic fake-home, focused, structural, generated-artifact, and contract verification |

Plan-phase reviewability helper: `status=pass`, `projected=0`, `production=0`, `new=7`, `modified=48`, `total_entries=55`. The zero projection is a helper taxonomy limitation for `speckit-pro/**/*.py`; the manual authored count above is the planning evidence. The optional `speckit-utils validate` after-plan hook was accepted but deferred because `tasks.md` does not exist until Phase 5.

---

## Phase 4: Domain Checklists

**When to run:** After Plan. Validate requirement quality across both `spec.md` and `plan.md`.

### 1. Error Handling

```text
/speckit-checklist error-handling

Focus on G56R-006 requirements:
- ordered preferred/fallback rejection reasons and terminal outcomes
- exhaustive all-required-agent diagnostics with zero writes
- strict override rejection and no silent fallback
- discovery-unavailable bounded probe behavior
- rollback failure and manual-remediation evidence
- Pay special attention to: whether every failure state has one deterministic response and previous-install guarantee
```

### 2. State Management

```text
/speckit-checklist state-management

Focus on G56R-006 requirements:
- one-batch snapshot lifecycle and identity joins
- plan-before-write transaction states
- prior bytes/modes capture, rollback, and restart guidance
- optional-helper present, omitted, safely removed, or preserved-unmanaged states
- Pay special attention to: preventing partial required-agent state across dry-run, apply, no-op, and failure
```

### 3. Data Integrity

```text
/speckit-checklist data-integrity

Focus on G56R-006 requirements:
- closed manifest and structured routing-response schemas
- 13-source versus 12-required-plus-one-optional roster validation
- original source binding and exact destination-byte digest
- non-route contract immutability
- stable ordering and identity joins among snapshots, attempts, route resolutions, and resolved policies
- Pay special attention to: parsed-equivalent TOML never substituting for exact-byte proof
```

### 4. Reliability

```text
/speckit-checklist reliability

Focus on G56R-006 requirements:
- bounded discovery/probe behavior and adapter injection
- deterministic complete diagnostics
- previous-known-good preservation and rollback verification
- managed-file ownership proof before deletion
- compatibility mode and no-helper degradation
- Pay special attention to: safe recovery when both an apply operation and rollback step fail
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| error-handling | 28 | 0 | Spec, plan, data model, contracts, quickstart, constitution, roadmap, and existing-test references all resolved; no remediation required |
| state-management | 28 | 0 | Spec, plan, data model, contracts, quickstart, Design Concept, roadmap, constitution, and existing-test references all resolved; no remediation required |
| data-integrity | 36 | 0 | Spec, plan, data model, contracts, quickstart, Design Concept, constitution, source, and test references all resolved; no remediation required |
| reliability | 31 | 0 | Spec, plan, research, data model, contracts, quickstart, constitution, source, and test references all resolved; no remediation required |
| **Total** | **123** | **0** | All four domains resolved with no remediation or routed consensus required; G4 passed |

---

## Phase 5: Tasks

**When to run:** After every checklist gap is resolved.

### Tasks Prompt

```text
/speckit-tasks

Generate small, dependency-ordered, TDD-first tasks from:
- specs/g56r-006-resolver-materializer-installer-strict-override/spec.md
- specs/g56r-006-resolver-materializer-installer-strict-override/plan.md
- docs/ai/specs/.process/G56R-006-design-concept.md

Requirements:
- organize by the four user stories, not by technical layer
- each behavior-changing task starts with a focused failing test and names its RED→GREEN pair
- foundation may add closed schemas/fixtures and shared test builders, but each user-story slice must remain independently testable end to end
- order materializer proof, observation adapter, route planning, strict override, optional-helper ownership/removal, rollback, compatibility, response evidence, and generated-artifact verification by real dependencies
- use [P] only when files and state do not overlap; serialize installer, materializer, registry, shared fixtures, suite manifest, generated payload, runner metadata, and docs reference regeneration
- reference every FR and acceptance scenario
- preserve every Design Concept Non-goal, especially no route qualification, no live calls, no real-home writes, no per-agent override map, no Claude path, and no downstream cohort expansion
- use the Q&A “why” context to specify edge cases and rollback assertions
- include focused tests, Layer 1, relevant Layer 4/5 gates, full suite, generated-artifact checks, and release-readiness evidence
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | 53 |
| **Phases** | 7 |
| **Parallel Opportunities** | 4 setup-only `[P]` tasks |
| **User Stories Covered** | 4 of 4 |

**G5 gate:** ✅ PASS — `validate-gate G5`, 53 tasks found, 0 markers. All 29 functional requirements, 13 acceptance scenarios, and 9 success criteria are mapped; 14 focused RED→GREEN pairs are explicit.

**Tasks-mode reviewability:** deferred by the installed runner contract (`helper_id=reviewability-gate`, `requested_mode=tasks`). Fallback evidence proceeds: scaffold setup was `warn` with `pass=true` and no blockers; the plan estimator was `pass`; the operator-ratified workflow decision remains one vertical slice. No correctness or safety block exists, fingerprints are current, and no marker plan is required.

---

## Atomicity Route

The tasks-phase classifier fills this section after G5. The scaffold decision is one vertical slice, but the classifier still evaluates whether implementation tasks contain safely separable PR seams.

| Field | Value |
|-------|-------|
| **Route** | `one-navigable-PR` |
| **Releasable** | `true` |
| **Signals** | `change-shape:modify-heavy` |
| **Warnings** | None |

Run:

```text
runner helper atomicity-route specs/g56r-006-resolver-materializer-installer-strict-override
```

---

## Layer Plan

| Field | Value |
|-------|-------|
| **Status** | Skipped |
| **Reason** | Atomicity route is `one-navigable-PR`, not `split-PR`; `plan-layers-feature-dir` was not invoked |

---

## Phase 6: Analyze

**When to run:** Always after Tasks.

### Analyze Prompt

```text
/speckit-analyze

Analyze these four authorities together:
- specs/g56r-006-resolver-materializer-installer-strict-override/spec.md
- specs/g56r-006-resolver-materializer-installer-strict-override/plan.md
- specs/g56r-006-resolver-materializer-installer-strict-override/tasks.md
- docs/ai/specs/.process/G56R-006-design-concept.md

Remediate every finding at every severity. Explicitly flag:
1. drift from Design Concept Goals, Non-goals, Q1-Q14 decisions, or Open Questions
2. any roster count other than strict 13-source / 12-required / one optional
3. inferred route qualification, live availability, or final aggregate claims
4. missing manifest, snapshot, attempt, resolution, materialization, response, ownership, rollback, or static-compatibility coverage
5. strict override behavior that silently falls back or lets an optional-helper miss fail the required batch
6. partial-write paths, user-owned deletion risk, non-deterministic ordering, or unbounded probes
7. constitution, file-path, FR-task, TDD, generated-artifact, or reviewability inconsistencies

Finish only when no unresolved finding remains.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| A-001 | Medium | `data-model.md` named manifest fields `optional_helper_policy` and `no_helper_allowed`, drifting from the closed contract | Renamed them to the contract-authoritative `optional_helper` and `no_helper`; re-scan clean |

G6 passed with zero unresolved critical, high, medium, or low findings. Analyze consensus was not needed because the sole finding was resolved from direct contract evidence with high confidence.

📊 Confidence: 0.94

- Task understanding: 0.96 — all four authorities, seven explicit drift classes, and the plan-stage boundary were checked.
- Approach clarity: 0.94 — the one contract mismatch had a direct, minimal artifact correction.
- Requirements alignment: 0.95 — all 29 FRs, 13 scenarios, 9 success criteria, Q1-Q14 decisions, and Non-goals remain mapped.
- Risk assessment: 0.92 — rollback, ownership, strict override, deterministic-only validation, generated artifacts, and downstream roster drift were explicitly audited.
- Completeness: 0.94 — one medium finding was remediated; marker scan and G6 both report zero unresolved findings.

---

## Phase 6.5: Confidence Gate

| Field | Value |
|-------|-------|
| Mode | advisory |
| Composite confidence | Pending |
| Verdict | Pending |
| Evidence | Pending |

---

## Phase 7: Implement

**When to run:** Only after G6 is clean and the confidence gate has a disposition.

### Implement Prompt

```text
/speckit-implement

Execute tasks.md in strict RED→GREEN→REFACTOR order.

Before each implementation group, re-read:
- specs/g56r-006-resolver-materializer-installer-strict-override/tasks.md
- specs/g56r-006-resolver-materializer-installer-strict-override/plan.md
- docs/ai/specs/.process/G56R-006-design-concept.md

Use the Q&A log for the “why” behind roster, materializer, snapshot, override, optional-helper, ownership, structured-response, and rollback edge cases. Make the smallest change that satisfies the current failing test. Keep Python 3.11 stdlib, structured data, deterministic ordering, safe paths, and shell=False.

Never mutate a real user home in tests or implementation verification. Use temporary fake homes and injectable observation/probe fixtures. Preserve unrelated agents. Verify exact destination bytes, modes, response identities, no-op/restart guidance, exhaustive failure evidence, rollback, and previous-known-good state.

After focused tests pass, run the relevant Layer 1/4/5 checks, generated runner/payload/reference consistency required by the changed paths, the full deterministic suite, git diff --check, and the exact final release-readiness title gate.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Foundation | Pending | 0 | |
| User Story 1 | Pending | 0 | |
| User Story 2 | Pending | 0 | |
| User Story 3 | Pending | 0 | |
| User Story 4 | Pending | 0 | |
| Polish and verification | Pending | 0 | |

---

## Post-Implementation Checklist

| Canonical Item | Status | Evidence |
|---|---|---|
| Post: Doctor Extension Check | ⏳ Pending | |
| Post: Verify Implementation | ⏳ Pending | |
| Post: Verify Tasks Phantom Check | ⏳ Pending | |
| Post: Code Review | ⏳ Pending | |
| Post: Integration Suite | ⏳ Pending | |
| Post: Reviewability Diff Gate | ⏳ Pending | |
| Post: Self-Review | ⏳ Pending | |
| Post: UAT Runbook Generation | ⏳ Pending | |
| Post: PR Body Generation | ⏳ Pending | |
| Post: PR Creation | ⏳ Pending | |
| Post: Review Remediation | ⏳ Pending | |
| Post: Retrospective | ⏳ Pending | |

- [ ] All tasks complete and every FR mapped.
- [ ] Focused tests pass with explicit RED→GREEN evidence.
- [ ] Layer 1 and relevant Layer 4/5 gates pass.
- [ ] Full `python3 tests/speckit-pro/run-all.py` suite passes.
- [ ] Runner manifest/checksum, release payload, docs reference, and Layer 6 corpus contracts are current for every changed input.
- [ ] Fake-home manual/deterministic verification is complete; live installed UAT is explicitly deferred to G56R-011.
- [ ] Exact PR title passes the release-readiness gate.
- [ ] Draft/final PR packet, review remediation, and retrospective are complete.

---

## Lessons Learned

### What Worked Well

- Pending.

### Challenges Encountered

- Pending.

### Patterns to Reuse

- Pending.

---

## Project Structure Reference

```text
speckit-pro/
├── codex-agents/                                  # strict 13-file source bundle
├── codex-skills/install/SKILL.md                  # user-facing install contract
└── speckit_pro_runner/
    ├── agent_materialization.py                   # canonical byte-proof materializer
    └── helpers/
        ├── install.py                             # install planning/apply/rollback owner
        └── registry.py                            # runner helper registration
tests/speckit-pro/
├── layer6-efficiency/contracts-codex-fallback/    # G56R-005 contracts to consume
├── layer6-efficiency/fixtures-codex-fallback/     # deterministic fallback corpus
└── unit/                                          # focused materializer/installer tests
specs/g56r-006-resolver-materializer-installer-strict-override/
└── SPEC-MOC.md                                    # contract navigation marker
```

---

Populated from the shared SpecKit workflow template v1.0.0 using the G56R-006 roadmap entry and Design Concept.
