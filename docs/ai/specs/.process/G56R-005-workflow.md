# SpecKit Workflow: G56R-005 — Model Availability, Fallback, and Recovery Simulation

**Template Version**: 1.0.0
**Created**: 2026-08-22
**Purpose**: Executable workflow populated from the G56R technical roadmap,
current repository contracts, the mandatory blind-spot pass, and the
human-validated Grill Me design concept.

---

## Design Concept

This workflow was enriched from the required Grill Me interview. The complete
Q&A log, Goals, Non-goals, Decisions, and Open Questions live at:

```text
docs/ai/specs/.process/G56R-005-design-concept.md
```

The design concept is the source of truth for setup decisions. Re-read it
before every phase. Once autopilot begins, later clarifications use
`/speckit-clarify` and the consensus protocol; Grill Me is not part of the
autonomous phase loop.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | 4 stories, 22 requirements, 26 acceptance scenarios; G1 passed |
| Clarify | `/speckit-clarify` | ✅ Complete | 3 sessions resolved; G2 passed |
| Plan | `/speckit-plan` | ✅ Complete | 5 artifacts; G3 and reviewability estimator passed |
| Checklist | `/speckit-checklist` | ✅ Complete | Error handling, state management, and data integrity checklists; no gaps |
| Tasks | `/speckit-tasks` | ✅ Complete | 25 vertical TDD-first tasks; G5 passed |
| Analyze | `/speckit-analyze` | ✅ Complete | 4 findings remediated (0C/1H/3M); G6 passed with no unresolved findings |
| Confidence Gate | G6.5 | ✅ Complete | PASS: 0.99 ≥ 0.90 in advisory mode |
| Implement | `/speckit-implement` | ✅ Complete | T001-T025 complete; focused 33/33 after review remediation, Layer 4 5998/5998, full suite 7659/7659, generated checks current |
| Post | Post-Implementation | ⏳ Pending | Not run by the `stage=plan` handoff |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⏭️ Skipped | ⚠️ Blocked

G6.5 is advisory by default. Leaving it Pending until the gate runs does not
make later rows out of order.

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | Stories, requirements, and acceptance scenarios are testable; no clarification markers remain |
| G2 | After Clarify | Reason order, state transitions, reroute attribution, and no-write semantics are unambiguous |
| G3 | After Plan | Constitution and reviewability gates pass; every planned path is declared |
| G4 | After Checklist | Every genuine gap is remediated or explicitly scoped out |
| G5 | After Tasks | FR coverage, dependencies, RED→GREEN pairs, and state-fixture cleanup are complete |
| G6 | After Analyze | No CRITICAL/HIGH inconsistency or coverage finding remains |
| G6.5 | Before Implement | Composite confidence meets the autonomous threshold or receives explicit disposition |
| G7 | After each implementation group | Targeted tests pass and fake-home/state evidence is recorded |

---

## Prerequisites

### Worktree and Branch

- Worktree: use the registered checkout returned by
  `git rev-parse --show-toplevel` for the branch below. Do not encode a
  maintainer-specific absolute path in committed artifacts.
- Branch: `g56r-005-model-availability-fallback-recovery`
- Base at scaffold: `origin/main` commit `8859efc058`
- Remote: `origin`
- Never run this workflow from `main`, a detached checkout, or another feature
  worktree.

### Worktree Bootstrap

No bootstrap command was run. Root `AGENTS.md` states that the repository test
suite needs no bootstrap and runs directly with
`python3 tests/speckit-pro/run-all.py`. `docs-site/` is the only
dependency-bearing surface. If a later implementation changes a tracked
`.md`, `.py`, or `.sh` under `tests/speckit-pro/` and therefore invokes a docs
reference command, first run the documented
`pnpm --dir docs-site install --frozen-lockfile` once in this worktree.

### Runtime and Capability Context

- Installed SpecKit CLI: `specify 0.14.2`.
- Installed Codex agents: the required dry-run returned `status=ok`,
  `mutation_status=no_op`, and all eleven bundled agent files current.
- Preset: `speckit-pro-reviewability` v1.0.0 is installed and enabled. The
  installed CLI resolved its `spec-template`, `plan-template`, and
  `tasks-template` overlays successfully.
- Agent surface: the mandatory read-only `codebase-analyst` blind-spot pass
  surfaced five findings; all five were resolved during Grill Me, while two
  lower-impact findings were set aside by the analyst.
- Capability path: repository files, runner helpers, Git state, and the
  codebase analyst provided direct local evidence. No external documentation or
  live model capability claim is needed for this deterministic simulation.
- Tools: repository-local Python 3.11 runner/helpers, Git, and the existing
  SpecKit commands. No new external tool or dependency is declared.

### Tooling TODO

- [ ] **TODO-CODEX-WORKTREE-BINDING:** Fix same-task worktree adoption so the
  Codex UI task root, sandbox write scope, phase-agent working directory, and
  autopilot workflow authority bind to one registered feature worktree without
  requiring a new task. This is tracked process debt and is out of scope for
  G56R-005 feature behavior.

### Grounded Source Truth

Use these sources in order:

1. `docs/ai/specs/.process/G56R-005-design-concept.md` — human-approved scope
   and decisions.
2. `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md` — goal,
   dependency, budget, reason vocabulary, and non-goals.
3. Current Codex contracts and fixtures under
   `tests/speckit-pro/layer6-efficiency/contracts-codex-specification/` and
   `tests/speckit-pro/layer6-efficiency/fixtures-codex/`.
4. `speckit-pro/codex-agents/` plus the current installer's required Codex
   agent set — roster authority.
5. Existing pure Claude fallback resolver and tests — behavior-shape evidence
   only, never a contract or import dependency.
6. G56R-004's deterministic evidence and operator-only live-smoke boundary.
7. `.specify/memory/constitution.md`, root `AGENTS.md`, and
   `tests/speckit-pro/suite-manifest.json` — runtime, testing, simplicity, and
   test-registration rules.

The Codex reason `capability_discovery_unavailable` intentionally differs from
Claude's frozen `capability_probe_unavailable`. Preserve both and defer their
cross-platform reconciliation to CAR-012/G56R-012.

### Constitution Validation

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| I. Plugin Structure Compliance | Keep simulation work on the declared repository/test surface; do not add install-facing payload changes | ✅ Layer 1 baseline `1469/1469` |
| II. Cross-Platform Runtime & Script Safety | Python 3.11+ standard library, structured JSON, UTF-8 determinism, `shell=False`, no active Bash or `jq` | ✅ Layer 4 baseline `5998/5998` |
| III. Semantic Versioning | No plugin version or release-artifact changes for repository-only simulation | ✅ Layer 1 version/manifest checks passed |
| IV. Test Coverage Before Merge | Register new test paths through the suite manifest and pass targeted plus full tests | ✅ Full baseline `7659/7659` |
| V. Conventional Commits | Repository-valid lowercase scope and plain-English description | ✅ Commit policy recorded; PR title gate remains terminal evidence |
| VI. KISS, Simplicity & YAGNI | One Codex-local resolver, one bounded state model, no speculative shared framework | ✅ Design boundary recorded; re-check at G3 and G6 |

**Constitution Check:** ✅ Verified for G0. Toolchain preflight passed; the
authoritative execution-root-permitted suite passed `7659/7659` (`L1
1469/1469`, `L4 5998/5998`, `L5 192/192`). An earlier cross-worktree sandbox
run failed only because temporary fixture writes were denied; it is not the
baseline of record.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | G56R-005 |
| **Name** | Model Availability, Fallback, and Recovery Simulation |
| **Branch** | `g56r-005-model-availability-fallback-recovery` |
| **Dependencies** | G56R-004 complete and archived after PR #403 |
| **Enables** | G56R-006 capability-aware resolver, materializer, installer, and strict override |
| **Priority** | P1 |
| **Stage** | `implement` |
| **Draft PR** | [#487](https://github.com/racecraft-lab/racecraft-plugins-public/pull/487) |

### Reviewability Budget and Split Decision

The setup reviewability helper scanned the series-wide roadmap and returned a
non-blocking warning because the roadmap spans three primary surfaces. Its
aggregate estimate was 395 reviewable LOC, two production files, and fifteen
total files; that is context, not the target-spec budget.

The G56R-005 roadmap entry declares one harness/adapter surface, approximately
242 reviewable LOC, approximately three production files, approximately ten
total files, `status: ok`, and one suggested slice. The Grill Me estimator used
four vertical user stories, ten files, eighteen functional-requirement groups,
and `new_vs_modify: modify`:

```json
{"estimated_loc":385,"suggested_slices":1,"status":"ok"}
```

**Split decision:** keep one thin vertical slice. The plan-phase authoritative
reviewable-LOC check must re-slice if concrete paths push the implementation
over the reviewability ceiling.

### Success Criteria Summary

- [ ] Deterministic fixtures cover preferred model absent, unsupported effort,
  unavailable discovery, exact-invocation probe success/failure, treatment
  failure, approved/unapproved reroutes, and no safe required route.
- [ ] Ordered reasons use the Codex-local closed vocabulary and terminate in a
  single outcome without losing earlier applicable diagnostics.
- [ ] Optional-helper loss continues only through an explicitly validated
  no-helper route; every required-agent failure is all-or-nothing.
- [ ] Strict incompatible overrides stop before writes and never fall back.
- [ ] A bounded non-recursive state machine proves retry exhaustion,
  cancellation, loop rejection, and separate harness controls.
- [ ] Fake-home fixtures prove atomic no-write, rollback, and
  previous-known-good preservation for every failure boundary.
- [ ] Fallback changes only explicit model and effort; all other agent contract
  bytes remain identical.
- [ ] Reports are byte-stable, targeted tests pass, Layer 4 passes, and the
  complete repository suite passes. Live reroute smoke remains explicitly
  unrun and no live claim is made.

---

## Phase 1: Specify

**Output:** `specs/g56r-005-model-availability-fallback-recovery/spec.md`

### Specify Prompt

```text
/speckit-specify

## Feature: G56R-005 Model Availability, Fallback, and Recovery Simulation

### Problem Statement

G56R-006 cannot safely install real route policies until route availability,
fallback exhaustion, strict overrides, service reroute attribution, and
filesystem recovery semantics have deterministic, bounded, fail-closed proof.
G56R-005 creates that proof without wiring production routing or making live
availability claims.

### Users and Consumers

- G56R-006 maintainers need a frozen simulation contract before production
  resolver and installer wiring.
- Evaluation maintainers need stable reason ordering and service-reroute
  attribution.
- Release reviewers need evidence that failures cannot partially replace a
  required Codex agent install.
- Cross-platform maintainers need explicit preservation of frozen Claude
  behavior while the Codex reason vocabulary remains locally authoritative.

### Four Vertical User Stories

1. Resolve a fixture policy through qualified preferred and fallback routes,
   producing byte-stable ordered diagnostics and one terminal outcome.
2. Distinguish approved and unapproved service reroutes from plugin reasons and
   scoring eligibility through deterministic replay.
3. Exercise optional-helper degradation, strict override rejection, exhaustion,
   rollback, atomic no-write, and previous-known-good preservation in fake homes.
4. Enforce retry, time, fan-out, context, cancellation, and escalation bounds
   through one non-recursive sequential harness state machine.

### Required Scenario Matrix

- Preferred model absent; effort unsupported; discovery unavailable.
- Exact invocation availability-probe success and failure; treatment-probe
  failure; approved and unapproved service reroute; no safe route.
- Optional helper unavailable; validated no-helper continuation; incompatible
  strict override; bounded retry; fallback exhaustion.
- Loop, unqualified-adjacent, generic substitution, inherited model/effort,
  partial required installation, and non-route treatment mutation rejection.
- Atomic no-write, rollback, previous-known-good preservation, cancellation,
  and every declared harness budget.

### Frozen Decisions

- Codex-local resolver and reason vocabulary; no Claude import or shared-core
  extraction.
- Ordered applicable reasons plus one terminal outcome.
- Strict override never falls back.
- Service reroutes are separately attributed evidence.
- Fallback may change model and effort only.
- Pure resolution plus fake-home state adapter; no production installer wiring.

### Out of Scope

- Live model/service qualification or claims.
- Production resolver/installer integration, payloads, versions, or release
  artifacts.
- Frozen Claude/G56R-004 contract edits or early CAR-012/G56R-012 reconciliation.
- Production checkpoint/resume scheduling.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 22 |
| User Stories | 4 |
| Acceptance Scenarios | 26 |
| Success Criteria | 9 |
| Unresolved Markers | 0 |

### Files Generated

- [x] `specs/g56r-005-model-availability-fallback-recovery/spec.md`

**Gate G1:** ✅ PASS — runner `validate-gate` returned `pass=true`,
`markers=0`, and `spec.md exists with 0 markers`. The required phase-boundary
spec-index regeneration updated the feature `SPEC-MOC.md` and the G56R roadmap
MOC.

---

## Phase 2: Clarify

Run at most five targeted questions per session. Do not reopen choices already
settled in the Design Concept without contradictory repository evidence.

### Clarify Session 1: Resolution Contract

```text
/speckit-clarify Focus on deterministic resolution: exact reason ordering,
terminal outcomes, strict override rejection, qualified fallback eligibility,
validated no-helper continuation, loop detection, and treatment immutability.
```

### Clarify Session 2: State and Recovery

```text
/speckit-clarify Focus on fake-home state: pre-state identity, write boundary,
atomic no-write, rollback trigger and result, previous-known-good preservation,
required-agent completeness, cleanup, and byte-stable evidence.
```

### Clarify Session 3: Bounds and Attribution

```text
/speckit-clarify Focus on service-reroute attribution and separate harness
controls: approved versus unapproved evidence, scoring eligibility, time,
retry, fan-out, context growth, cancellation, escalation/de-escalation, and
terminal precedence.
```

### Clarify Results

| Session | Focus | Questions | Key Outcomes |
|---------|-------|-----------|--------------|
| 1 | Resolution contract | 5 resolved | Fixed diagnostic order; exhaustion is details under `no_safe_route`; loop detection on arrival; explicit no-helper proof; canonical non-route treatment comparison |
| 2 | State and recovery | 5 resolved | Canonical state IDs; temporary-root write boundary; rollback matrix; conditional helper and roster identity; deterministic Recovery Record |
| 3 | Bounds and attribution | 5 resolved | Separate service attribution; approved/unapproved reroute rules; terminal precedence; deterministic budget counters; scoring eligibility split from route qualification |

Sessions 1 and 3 reported zero unresolved-for-consensus items, so their
mandatory consensus steps were skipped with evidence. Session 2 routed the
helper-roster tension to `codebase-analyst` and `spec-context-analyst`.
Consensus was qualified agreement: validate the helper in bundled-source
integrity, exclude it from required-core destination completeness, bind the
current 10-core-plus-helper roster identity, and fail closed for re-review when
the roadmap's future 11-core-plus-helper roster arrives. The current installer's
all-11 label remains present-state implementation evidence.

---

## Phase 3: Plan

**Output:** `specs/g56r-005-model-availability-fallback-recovery/plan.md`

### Plan Prompt

```text
/speckit-plan

## Tech Stack

- Runtime: Python 3.11+ standard library only.
- Data: canonical structured JSON and JSON Schema following existing Codex
  contract patterns.
- Testing: unittest-compatible repository tests registered through
  tests/speckit-pro/suite-manifest.json.
- Filesystem proof: temporary fake homes only; never write the maintainer's
  installed Codex agents.

## Architecture Constraints

- Create the minimum Codex-local resolver/state adapter needed by G56R-005.
- Reuse existing parsing, schema, digest, and canonical serialization utilities
  only when their contract is platform-neutral.
- Do not import or modify the Claude fallback resolver, and do not extract a
  cross-platform framework.
- Derive required agents from speckit-pro/codex-agents and the installer's
  required set; avoid a second hand-maintained roster.
- Keep the resolver pure. Place fake-home transition/rollback assertions at a
  narrow adapter boundary that cannot reach a real home.
- Use a bounded sequential state machine. Cancellation is terminal.
- Keep service reroute attribution separate from plugin reason ordering.
- Verify non-route treatment bytes before and after every selected fallback.

## Reviewability and Verification

- Declare every add/modify/delete path and estimated reviewable LOC.
- Preserve one vertical slice only if the concrete plan remains at or below the
  repository ceiling.
- Plan RED→GREEN pairs for every scenario family and state transition.
- Require targeted tests, Layer 4, the full repository suite, scope checks, and
  generated-artifact checks appropriate to the final changed paths.
- Record live smoke as unrun; do not substitute synthetic replay for a live
  availability claim.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ⏳ | Architecture and reviewability packet |
| `research.md` | ⏳ | Existing-contract reuse decisions |
| `data-model.md` | ⏳ | Route, diagnostic, reroute, state, and budget records |
| `contracts/` | ⏳ | Codex-local simulation schemas if required |
| `quickstart.md` | ⏳ | Deterministic replay and verification commands |

---

## Phase 4: Domain Checklists

### 1. Error Handling

```text
/speckit-checklist error-handling

Focus on G56R-005 requirements:
- Stable ordering for simultaneous route failures.
- Exhaustion, loop rejection, strict override, treatment failure, and no-safe-route outcomes.
- Cancellation precedence and prohibition on post-cancel retries.
- Approved versus unapproved service reroute disposition.
- Pay special attention to fail-closed behavior without losing diagnostic evidence.
```

### 2. State Management

```text
/speckit-checklist state-management

Focus on G56R-005 requirements:
- Fake-home pre-state and previous-known-good identity.
- Atomic no-write, rollback completeness, and cleanup.
- Required-agent all-or-nothing behavior and optional-helper qualification.
- Pay special attention to proving unchanged bytes after every rejected route.
```

### 3. Data Integrity

```text
/speckit-checklist data-integrity

Focus on G56R-005 requirements:
- Closed reason and terminal-outcome vocabularies.
- Byte-stable canonical reports and content/digest bindings.
- Model/effort-only deltas with every other treatment field identical.
- Roster derivation and schema completeness.
- Pay special attention to invented, missing, duplicate, or reordered evidence.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| error-handling | 11 | 0 | FR-003, FR-007, FR-010, FR-012, FR-013, FR-016, FR-017 |
| state-management | 11 | 0 | FR-015, FR-016, FR-017, FR-018 |
| data-integrity | 12 | 0 | FR-001, FR-006, FR-008, FR-009, FR-011, FR-016, FR-018, FR-022 |
| **Total** | 34 | 0 | All gaps resolved or absent |

Every genuine `[Gap]` must update `spec.md` or `plan.md`, then be rechecked.

All three checklist domains reported zero unresolved-for-consensus items, so
their mandatory consensus steps were skipped with evidence rather than
dispatched.

---

## Phase 5: Tasks

### Tasks Prompt

```text
/speckit-tasks

## Task Structure

- Organize by the four vertical user stories, not by schema/module/test layers.
- Use strict RED → GREEN → REFACTOR → VERIFY task pairs.
- Make every task small, testable, dependency-ordered, and FR-traceable.
- Mark only truly independent fixture/test work [P].
- Put shared contract/fixture foundations before their consuming stories.
- Include suite-manifest registration and every changed-surface verification gate.
- Include explicit fake-home cleanup and a guard against real-home writes.
- Finish with targeted tests, Layer 4, full suite, artifact/reference checks when
  triggered, scope review, and live-smoke-unrun evidence.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| Total Tasks | 25 |
| Phases | 6 |
| Parallel Opportunities | 1 safe `[P]` foundation group |
| User Stories Covered | 4/4 |

G5 recheck passed with 25 tasks after the layer-planner repair. The planner now
returns `status=ok`, 6 increments, 25 tasks, and 0 errors. Its 36 warnings are
expected `reference_not_found` notices for declared NEW implementation paths.
The reconciliation boundary regenerated the feature `SPEC-MOC.md`.

---

## Atomicity Route

The autopilot fills this after Tasks by running the read-only classifier against
`specs/g56r-005-model-availability-fallback-recovery`. Do not pre-decide the
result from LOC alone.

| Field | Value |
|-------|-------|
| Route | `one-navigable-PR` |
| Releasable | `true` |
| Signals | `change-shape:modify-heavy` |
| Warnings | None |

```text
runner helper atomicity-route specs/g56r-005-model-availability-fallback-recovery
```

The layer plan orders Foundation → US1 → US2 → US3 → US4 → Polish with
declared dependency edges and one safe parallel foundation group.

### Plan Results

- Artifacts created: `plan.md`, `research.md`, `data-model.md`,
  `quickstart.md`, and `contracts/fallback-recovery-contract.md`.
- G3 passed with zero unresolved markers.
- Plan reviewability estimator passed with 10 declared file entries, 0
  projected production LOC, and no split required.
- Spec index regenerated after plan artifacts were added; touched
  `specs/g56r-005-model-availability-fallback-recovery/SPEC-MOC.md`.

---

## Phase 6: Analyze

### Analyze Prompt

```text
/speckit-analyze

Focus on:
1. Constitution and one-slice reviewability alignment.
2. Complete traceability across every route, reroute, bound, state, and rejection requirement.
3. Consistent reason ordering and terminal outcomes across spec, plan, schemas, and tasks.
4. Complete RED→GREEN coverage for fake-home failure and rollback states.
5. No production installer, live qualification, frozen-contract edit, or payload scope leak.
6. Correct declaration of generated-artifact and docs-reference duties for the concrete file plan.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| A-001 | MEDIUM | `spec.md` projected 900 reviewable LOC while the accepted one-slice estimate was 385 | Restored the approved 385-LOC estimate |
| A-002 | HIGH | FR-019 and FR-020 safety boundaries were not explicitly bound to implementation and review tasks | Bound the no-shared-Claude-core rule to T006 and the complete no-scope-leak proof to T024/T025 |
| A-003 | MEDIUM | SC-004, SC-005, and SC-007 were testable but not named in `tasks.md` | Added explicit success-criterion traceability to T006, T008-T010, and T017-T018 |
| A-004 | MEDIUM | T024 did not name the concrete generated-artifact, docs-reference, spec-index, and release-artifact checks | Added the exact conditional reference commands and release-artifact check |

G6 passed after one remediation loop. The authoritative marker helper reported
zero gaps, clarifications, and severity markers; the G6 validator reported
`0 CRITICAL/HIGH findings`. All 22 functional requirements and all 9 success
criteria now trace into `tasks.md`. The phase-boundary spec-index regeneration
was current (`stale_map_count: 0`) and changed no files.

### Consensus Resolution Log

| Item | Round | Routed Categories | Outcome | Analysts Used |
|------|-------|-------------------|---------|---------------|
| Analyze clean-pass synthesis | N/A | None | Zero unresolved items; confidence record emitted | consensus-synthesizer |

📊 Confidence: 0.99

- Task understanding: 0.98
- Approach clarity: 0.97
- Requirements alignment: 0.99
- Risk assessment: 1.00
- Completeness: 1.00

---

## Phase 6.5: Confidence Gate

| Field | Value |
|-------|-------|
| Mode | advisory |
| Composite confidence | 0.99 |
| Verdict | PASS |
| Evidence | Task understanding 0.98; approach clarity 0.97; requirements alignment 0.99; risk assessment 1.00; completeness 1.00; threshold 0.90 |

### Draft Artifact Generation

| Outcome | Page | Detail |
|---------|------|--------|
| Generated | Implementation Plan | `specs/g56r-005-model-availability-fallback-recovery/artifacts/implementation-plan.html` |
| Generated | Spec Explainer | `specs/g56r-005-model-availability-fallback-recovery/artifacts/spec-explainer.html` |
| Generated | Code Approaches | `specs/g56r-005-model-availability-fallback-recovery/artifacts/code-approaches.html` |
| Generated | Module Map | `specs/g56r-005-model-availability-fallback-recovery/artifacts/module-map.html` |

All four draft-stage review pages were generated from the shipped templates,
validated for fill-region integrity, and browser-checked with no console errors
or warnings. The draft PR packet was regenerated in `draft` mode and its
read-only validation passed with `pr_blocked: false`. The exact title
`feat(g56r-005): Add model availability fallback and recovery simulation` also
passed the repository release-readiness title check.

---

## Phase 7: Implement

### Implement Prompt

```text
/speckit-implement

For every task:
1. RED: add the smallest deterministic failing test.
2. GREEN: implement only the behavior required by that test.
3. REFACTOR: preserve stable report bytes and keep the resolver/state boundary narrow.
4. VERIFY: run the focused test and record the observable fixture/state result.

Before implementation, confirm the branch/worktree and a clean relevant
baseline. Never write outside temporary fake homes. Do not broaden scope into
production routing, live qualification, or cross-platform reconciliation.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Shared contract foundation | T001-T004 | 4/4 | Schemas, roster-bound corpus, RED tests, and Layer 4 registration complete |
| Resolver and reroute stories | T005-T011 | 7/7 | Deterministic route resolution, attribution, scoring, and treatment digest complete |
| Recovery and bounds stories | T012-T019 | 8/8 | Fake-home recovery and bounded sequential harness complete |
| Cross-cutting verification | T020-T025 | 6/6 | Traceability, focused, full suite, generated artifacts, scope, and PR packet evidence complete |

---

## Post-Implementation Checklist

| Canonical Item | Status | Evidence |
|---|---|---|
| Post: Doctor Extension Check | ✅ Complete | 3 PASS, 2 non-blocking WARN, 0 FAIL; templates and runner are healthy |
| Post: Verify Implementation | ✅ Complete | 22/22 FRs and 8/9 SCs verified; SC-008 awaits the scheduled packet refresh |
| Post: Verify Tasks Phantom Check | ✅ Complete | 24 verified, T025 partial only because the plan-stage packet is intentionally stale until Post emission |
| Post: Code Review | ✅ Complete | One important declaration-source schema mismatch found and remediated RED→GREEN; 33/33 focused tests pass |
| Post: Integration Suite | ✅ Complete | Authoritative exact-worktree run passed 7659/7659: L1 1469, L4 5998, L5 192 |
| Post: Reviewability Diff Gate | ✅ Complete (WARN) | 471 reviewable runtime LOC, 0 production files, 13 implementation-delta files, one cohesive simulation surface; above the 400-LOC warning but below file-count limits, so no split |
| Post: Self-Review | ✅ Complete | Four-question audit found no edge-case, traceability, tidiness, or silent-deferral defect |
| Post: UAT Runbook Generation | ⏭️ Skipped | `generate-uat-skeleton` is deferred and no committed source-derived skeleton exists; fail-open by contract |
| Post: Final Reviewability Backstop | ⏳ Pending | |
| Post: PR Packet/Body Generation | ⏳ Pending | |
| Post: PR Body Generation | ⏳ Pending | |
| Post: PR Creation | ⏳ Pending | |
| Post: Review Remediation | ⏳ Pending | |
| Post: Retrospective | ⏳ Pending | |

### Parallel Post-Implementation Evidence

- **Doctor:** templates 5/5, Python runner PASS, feature discovery PASS;
  missing command registration and constitution were non-blocking repository
  warnings.
- **Verify chain:** all 25 completed task rows reference existing files; all 22
  FRs and all 9 SCs have traceability evidence. T025/SC-008 remains partial
  only until the mandatory implementation-era PR packet refresh below.
- **Independent review:** the route-policy schema allowed only `local` even
  though the fail-closed resolver intentionally handles four non-local
  declaration sources. A new focused test first failed, the schema was expanded
  to the closed five-value enum, and the focused suite passed 33/33.
- **Integration:** the final authoritative suite passed 7659/7659. Earlier
  unprivileged cross-worktree fixture failures were sandbox artifacts and are
  superseded by the exact-worktree-permitted run.

### Reviewability Diff Gate

Status: **WARN**. The implementation delta contains 13 files, including six
generated/process bookkeeping surfaces, four contracts/fixtures, one focused
test, one manifest registration, and one 471-line deterministic simulation
runtime. It changes zero production files and remains one cohesive review
surface. The runtime exceeds the 400-LOC warning threshold, but total files are
below the 15-file warning and 25-file block thresholds. Splitting contracts,
runtime, and their deterministic proof would make either slice unverifiable, so
the one-slice plan remains current.

### Self-Review (auto-generated)

**Tests executed:** The repository has no separate build, typecheck, or lint
command for this test-only Python surface. Focused verification passed 33/33;
the full deterministic suite passed 7659/7659; docs reference, spec-index, and
release-artifact consistency checks pass.

**Edge cases:** The 32-row required-scenario corpus and focused tests cover
absence, unsupported effort, unavailable discovery, probe/treatment failure,
exhaustion, strict override, reroute attribution, optional-helper loss,
fake-home traversal/symlink/write/rollback/cleanup failures, cancellation,
bounded retry, fan-out, HITL, and recursion. No `[edge-case-gap]` markers.

**Requirements matched:** Every `FR-001` through `FR-022` appears in both
`spec.md` and a completed task; the corpus traceability table also maps all nine
success criteria. No orphan requirement or completed task was found.

**Follow-up & tidiness:** No TODO, FIXME, debug logging, breakpoint, temporary
fixture, or orphaned implementation file was found. The separate Codex task
worktree-binding bug is explicitly tracked as `TODO-CODEX-WORKTREE-BINDING` in
autopilot state and will be included as a known gap in the PR packet; it is out
of scope for G56R-005 feature behavior. Live reroute smoke remains intentionally
unrun because this spec makes no live availability claim.

- [ ] Every task is complete or explicitly skipped with rationale.
- [ ] Focused unit tests pass.
- [ ] `python3 tests/speckit-pro/run-all.py --layer 4` passes.
- [ ] `python3 tests/speckit-pro/run-all.py` passes.
- [ ] Triggered docs references and generated artifacts are current.
- [ ] The final diff contains no production installer, payload, version, live
  capture, frozen Claude contract, or unrelated change.
- [ ] Live reroute smoke is explicitly recorded as unrun.
- [ ] PR title passes the repository release-readiness gate.

---

## Lessons Learned

### What Worked Well

- Pending

### Challenges Encountered

- Pending

### Patterns to Reuse

- Pending

---

## Project Structure Reference

```text
speckit-pro/
├── codex-agents/                         # Required Codex agent source roster
└── speckit_pro_runner/                   # Existing route-agnostic installer/helper code

tests/speckit-pro/
├── layer6-efficiency/
│   ├── contracts-codex-specification/    # Codex-local contracts
│   ├── fixtures-codex/                   # Deterministic fixture corpus
│   └── lib/                              # Repository simulation helpers
├── unit/                                 # Focused registered tests
└── suite-manifest.json                   # Test registration authority

specs/g56r-005-model-availability-fallback-recovery/
└── SPEC-MOC.md                           # Spec-level navigation marker
```

---

Template based on SpecKit best practices and populated for the repository's
Python-authoritative, reviewability-gated workflow.
