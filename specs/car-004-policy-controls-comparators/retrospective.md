---
feature: CAR-004 Policy Controls and Adaptive Comparators
feature_dir: specs/car-004-policy-controls-comparators
branch: car-004-policy-controls-comparators
pull_request: 401
date: 2026-07-28
completion_rate: 98
spec_adherence: 95.8
total_requirements: 106
functional_requirements: 75
non_functional_requirements: 0
success_criteria: 31
implemented: 97
partial: 9
not_implemented: 0
modified: 0
unspecified: 0
findings_critical: 0
findings_significant: 4
findings_minor: 4
findings_positive: 5
spec_modified: false
spec_change_confirmation: not requested, not granted
---

# Retrospective: CAR-004 Policy Controls and Adaptive Comparators

**Scope**: `origin/main...HEAD` — 13 commits, 38 changed files, +19,129 / -9.
**Method**: artifact read plus independent re-derivation. Every claim below carries a
`file:line` or commit citation. Two findings were reproduced by execution rather than
by reading (see G1 gate probe and the marker-form check).

**Spec is read-only in this run.** No confirmation to modify `spec.md` was requested or
granted, and `spec.md` was not touched. Candidate spec edits are listed under
[Proposed Spec Changes](#proposed-spec-changes) as proposals only.

---

## Executive Summary

CAR-004 delivered its full declared surface. 63 of 64 tasks are complete, an independent
verification session found zero phantom completions across all 63
(`verify-tasks-report.md:17-23`), and the repository suite reports 4909/4909
(`verify-tasks-report.md:104-114`). Spec adherence is **95.8%**; nothing was dropped,
nothing was silently redefined, and the architecture matched the plan exactly — all 15
declared file operations landed and none were added (`plan.md:191-207`,
`verify-tasks-report.md:37-41`).

The interesting story is not the output. It is that **the quality of this run was
produced almost entirely by adversarial review passes, not by the gates**. Three separate
audit rounds caught 82 defects that the phase gates let through:

| Round | Commit | Found | Applied |
|---|---|---|---|
| Four-lens adversarial review of the Specify output | `1ab5ee9b` | 6 | 6 |
| Three checklist domains over spec + plan | `2a7fd18e` | 57 gaps / 135 items | 57 |
| Three-lens audit over the *remediated* artifacts | `e404cae4` | 19 | 19 |

One of the six Specify findings was a hard contradiction with a governing product
requirement. Three of the nineteen post-remediation findings would have blocked
implementation outright. Meanwhile the gate that exists specifically to catch unresolved
ambiguity — G1 — **cannot fail in this repository**, and reported `pass: true, markers: 0`
against a spec carrying five real markers. That is reproduced below.

The two durable risks that ship with the PR are (1) seven frozen numerics inside a content
address that no live run has ever tested, and (2) T062, the three developer-local live
smokes, which has never been executed and cannot be executed by an agent — leaving six
success criteria with no evidence of any kind.

---

## Proposed Spec Changes

**Status: PROPOSALS ONLY. `spec.md` was not modified. No confirmation was requested or
granted in this run.** Each item below would need its own explicit approval.

Two of the three are hash-relevant: `smoke_bounds` and every control's `cancellation_bounds`
sit inside the registry content address, so changing a value moves `registry_digest`, every
recorded `{id, digest}` binding, and the twin-handoff `sha256` entries with it. The correct
sequencing is **run T062 first, then amend once if a bound proves unlivable** — not amend
speculatively.

| # | Target | Proposed change | Rationale | Confirmation |
|---|---|---|---|---|
| P1 | FR-014a / Assumptions (`spec.md:1891-1901`) | Make each control's per-objective `cancellation_bounds.max_duration_ms` strictly less than the run-level `max_duration_seconds`. | All three controls freeze `max_duration_ms: 1800000` (`fixtures-controls/policy-control-registry.json:37,196,236`), exactly equal to `max_duration_seconds: 1800` (`:352`). Inside a five-objective smoke the run ceiling always binds first, so the per-objective cancellation-breach path is unreachable by the smoke as bounded. | **Not granted** |
| P2 | Assumptions (`spec.md:1912-1950`) | Either record a defensible basis for the "just under twice the per-attempt allowance" headroom, or mark the seven derived ceilings explicitly as provisional-pending-T062. | The *basis* (attempts, not input) is argued from two repository instances; the *doubling* is invented and no repo artifact settles it. The only test pinning the values compares the fixture to `synthetic_smoke_bounds()`, whose literals are the same numbers — a change detector, not a validity check. | **Not granted** |
| P3 | Assumptions (`spec.md:1867-1869`) | Record that the registry-serialization clarification resolved at **split / medium confidence**, and name the dissenting position. | The workflow overview records "1 split at medium confidence" (`CAR-004-workflow.md:38`) but the split and the dissent are written down nowhere. The spec records only the outcome, so a future reader cannot tell a settled decision from a contested one. | **Not granted** |

---

## Requirement Coverage

**Legend**: `I` implemented and machine-verified · `P` partial (machinery delivered, the
evidence the requirement demands has not been produced) · `N` not implemented ·
`M` modified · `U` unspecified.

### Functional requirements (75)

All 75 FRs have a delivered, verified artifact. Three are partial: their declarative half
is frozen and validator-tested, but the requirement's live-execution half has never run.

| Status | Count | IDs |
|---|---|---|
| I | 72 | FR-001, 002, 002a, 002b, 002c, 003, 004, 005, 005a, 006, 007, 008, 009, 010, 010a, 010b, 010c, 011, 011a, 011b, 012, 012a, 013, 014, 014a, 015, 015a, 016, 016a, 016b, 016c, 016d, 016e, 017, 017a, 018, 019, 020, 021, 021a, 021b, 021c, 021d, 021e, 022, 023, 024, 024a, 025, 025a, 025b, 025c, 025d, 026, 026a, 027, 028, 029, 030a, 030b, 030c, 031a, 032a, 033, 034, 034a, 035, 035a, 036, 036a, 037, 037a |
| P | 3 | FR-030, FR-031, FR-032 |
| N / M / U | 0 | — |

| ID | Status | Evidence | Gap |
|---|---|---|---|
| FR-030 | P | Bounds frozen and machine-checked as an identity (`SC-017`, T041); `validate_smoke_record` at `claude_policy_controls.py:2083` | "Each control MUST have exactly one bounded live smoke **run**." No run has occurred (T062). |
| FR-031 | P | `evaluate_demonstration` at `claude_policy_controls.py:2294`, negative controls tested | The three demonstrations — real escalation, real inherit resolution, real parallel child dispatch — have never been observed. |
| FR-032 | P | `evaluate_cache_isolation` at `claude_policy_controls.py:2404`; seeded shared/unobserved pairs tested | No arm pair has ever been observed live, so `observed_disjoint` has never been recorded from a real run. |

### Success criteria (31)

| Status | Count | IDs |
|---|---|---|
| I | 25 | SC-001 … SC-008, SC-010 … SC-025, SC-028 |
| P | 6 | SC-009, SC-026, SC-027, SC-029, SC-030, SC-031 |
| N / M / U | 0 | — |

The six partial SCs are exactly T062's SC tag set (`tasks.md:205`). For each, the *refusal*
path is machine-tested (a seeded `api_key` observation, a missing observable, a seeded
shared cache root all fail closed) while the *positive* observation has never been made.
They are the only criteria in the feature with no live or synthetic affirmative evidence.

### Non-functional requirements

The spec declares **zero** NFR-prefixed requirements. Performance, determinism, and
stdlib-only constraints were carried as plan Technical Context and constitution gates
instead (`plan.md:111-116`, `plan.md:213-220`) and are verified — but they are not
addressable by ID from `spec.md`, which is itself a minor traceability gap (see F8).

### Adherence calculation

```
Spec Adherence = ((97 IMPLEMENTED + 0 MODIFIED + (9 PARTIAL x 0.5)) / (106 - 0 UNSPECIFIED)) x 100
               = (97 + 4.5) / 106 x 100
               = 95.8%
```

---

## Architecture Drift

| Plan element | Planned | Delivered | Drift |
|---|---|---|---|
| Declared file operations | 15 (`plan.md:191-207`) | 15, all present, none added (`verify-tasks-report.md:37-41`) | None |
| Production LOC | 0 | 0 — no path under `src/`, `app/`, `lib/`, `scripts/`, no `.ts/.js/.sql` suffix (`plan.md:172-176`) | None |
| Validator modules | 2 (`claude_policy_controls.py`, `claude_control_comparison.py`) | 2 | None |
| Layer 4 registrations | 3 | 3 at `suite-manifest.json:122-124` | None |
| Partition registry | Reuse the frozen CAR-003 builder | Reused `build_partition_registry_entry` / `register_partitions` | None — **removed** a file rather than adding one (`plan.md:222-226`) |
| Replay fixture cases | "a small closed case set" | 9 cases, incl. both bound-breach paths and the excluded-non-scorable streak | None |
| Commit scope | `speckit-pro` (`plan.md:219`) | `car-004` on 13 of 13 feature commits | **Minor** — see F7 |
| Reviewability diff-mode gate | Authoritative diff-mode reading at PR time | Diff mode **deferred** on the runner (`read_only.py:851-852`); three-link fallback chain recorded instead (`plan.md:160-189`) | Documented deferral, not a workaround |

No architectural drift. The plan was unusually predictive: task generation produced 64 tasks
against the same fifteen file operations and added none (`plan.md:252-260`).

---

## Findings

### SIGNIFICANT

#### F1 — The G1 gate cannot fail on unresolved clarifications in this repository

**Reproduced by execution.** The Specify-phase spec (`1ab5ee9b`) carries five
`[NEEDS CLARIFICATION: ...]` markers at lines 257, 281, 306, 362 and 498. Running the
authoritative helper against that exact file returns:

```
G1           -> {"gate":"G1","pass":true,"reason":"spec.md exists with 0 markers","markers":0,"details":[]}
count-markers-> {"type":"clarifications","total":0,"spec":0,"plan":0,"details":[]}
```

Root cause: the gate matches `r"\[NEEDS CLARIFICATION\]"` — a literal `]` immediately after
`CLARIFICATION` — while the spec template mandates the *parameterized* form
`[NEEDS CLARIFICATION: specific question]` (`.specify/templates/spec-template.md:98-99`;
stated as a requirement in `speckit-pro/skills/speckit-coach/references/sdd-methodology.md:91`).
The two forms are mutually exclusive.

Blast radius is wider than G1. The same pattern appears at six call sites in
`speckit-pro/speckit_pro_runner/helpers/read_only.py` — lines 716, 749, 750, 758, 775, 781
and 787 — covering **G1, G2, G3, and both `count-markers clarifications` and
`count-markers all`**. Every ambiguity gate in the workflow is blind to the marker form the
templates actually emit.

Why no test caught it: the only coverage is
`test-speckit-pro-read-only-helpers.py:1508-1525`, and it asserts that the Python helper
*matches a Bash reference* for each gate. Both implementations carry the same regex, so
parity holds while both are wrong. No test asserts the positive behavior "a spec containing
markers fails G1."

On this run the miss was harmless — Clarify ran anyway on the workflow's seeded sessions and
all five markers were resolved (`CAR-004-workflow.md:38`). It was harmless by routing luck,
not by gate enforcement.

#### F2 — Upstream roadmap drift produced the run's single material spec defect, and is still unfixed

The Specify output mandated API-key authentication for the live smoke runs. PRD `AC-2.19`
has forbidden that outright since its 2026-07-26 amendment: "forbid any supported path
requiring API-key authentication" — an unqualified prohibition, not one scoped to scored
work (`docs/prd-claude-agent-routing.md:502-524`). Caught by the four-lens adversarial
review and corrected in the same commit (`1ab5ee9b`).

The root cause is upstream of this spec. The grill-me interview recommended the API-key
smoke by reasoning from `docs/ai/specs/claude-agent-routing-technical-roadmap.md`, which
still carries the **pre-amendment** wording. Verified stale, today:

| Line | Section | Stale text |
|---|---|---|
| 159-160 | **Qualification and release-decision rule** (program-wide, §136-172) | "scored campaigns run API-key-authenticated with at least one subscription-authenticated installed smoke row" |
| 339 | CAR-002 | "API-key-authenticated. Record probed model IDs…" |
| 359-360 | CAR-002 | "Record the authentication mode of every run (API-key for scored campaigns, subscription for installed smoke)" |
| 1110 | **Local Development Setup** (program-wide, §1104-1112) | "a dedicated API-key-authenticated environment, plus one subscription-authenticated installed smoke row" |

Two of the four sit in **program-wide** sections that every remaining spec's scoping will
read. CAR-004's design concept flags this explicitly and declines to fix it:
"The roadmap's stale authentication wording is a separate, wider drift that also affects
CAR-005 through CAR-011 and is **not** corrected here"
(`CAR-004-design-concept.md:50-51`).

The correction cost this run one adversarial review pass and one revision note. The next
seven specs inherit the same trap with no guarantee an adversarial pass catches it again.

#### F3 — Checklist remediation outgrew verification, and a post-remediation audit found 19 real defects

Measured growth of `spec.md`:

| Commit | Phase | Lines | Δ |
|---|---|---|---|
| `1ab5ee9b` | Specify (post-correction) | 505 | — |
| `01105f64` | Clarify + Plan | 862 | +357 |
| `2a7fd18e` | **Checklist remediation + Tasks** | 1,883 | **+1,021 (+118%)** |
| `e404cae4` | Post-audit reconciliation | 1,991 | +108 |

Requirement counts grew with it: 36 FRs / 23 scenarios / 12 measurable outcomes at Specify
(`CAR-004-workflow.md:37`) became 75 / 45 / 31 — a 2.1x and 2.6x expansion.

Three checklist domains ran over 135 items, found 57 gaps and remediated all 57, escalating
12 to consensus (`2a7fd18e`). The three-lens audit that ran immediately *after* that
remediation then found **19 more defects, all reproduced against their citations and all
applied** (`e404cae4`). Three of the nineteen would have blocked implementation:

1. A frozen candidate-plane pairing that **four artifacts** told the implementer to import
   from a module where it does not exist — now derived live from the frozen `failure_code`
   enum instead.
2. A `signal_precedence` array frozen at three members in `research.md` while the contracts
   fixed it at five, with terminal state ranked third — making the two trailing sources
   unreachable.
3. An environment-contract binding still pointing at the **Codex-side** document.

The signal is clean: a remediation pass that more than doubles a spec is itself a new
authoring event with a fresh defect rate, and nothing in the workflow re-verifies it. The
checklist phase self-certified ("57 of 57 remediated") and the gate accepted that.

#### F4 — T062 has never run; six success criteria ship with no evidence, and the PR body does not say so

T062 is the three developer-local live smokes. It requires an operator on a subscription
path, is explicitly never CI, and **cannot be executed by an agent**. Its unmarked state is
honest bookkeeping, not a phantom (`verify-tasks-report.md:165-169`).

The consequence is under-stated in the shipped artifacts. SC-009, SC-026, SC-027, SC-029,
SC-030 and SC-031 have no affirmative evidence of any kind. The self-review identified this
precisely and made it recommendation #2 for the human reviewer: "If it is not run before
merge, say in the PR body which six SCs are unevidenced" (`CAR-004-workflow.md:811, 820-822`).

**That recommendation was not carried into the PR body.** The body notes the smoke is
outstanding at lines 71, 79, 89 and 135 of
`.process/pr-packets/car-004-slice-1/body.md`, but names none of the six criteria; the only
SC reference is the blanket line 66, "Success criteria SC-001 through SC-031 are mapped to
expected outcomes in quickstart.md". A reviewer reading the PR body alone would conclude the
success criteria are uniformly evidenced.

This is the one finding with an open action before merge.

### MINOR

#### F5 — The frozen numerics rest on an invented derivation and a change-detector test

`fixtures-controls/policy-control-registry.json` freezes seven judgement-call ceilings —
`max_cache_read_tokens: 1200000`, `ephemeral_5m: 160000`, `ephemeral_1h: 40000`,
`max_cached_input_tokens: 150000`, `max_input_tokens: 800000`, `max_output_tokens: 50000`,
`max_duration_seconds: 1800`. The derivation at `spec.md:1912-1950` is "per-attempt
allowance from the frozen CAR-003 campaign budget, carried over five attempts, sit just
under twice that, round down". The *basis* is genuinely argued from two repository
instances; the *doubling* is not settled anywhere. Cost if wrong is high: `smoke_bounds` is
hash-relevant, so the first smoke that trips a diagnostic ceiling forces a new
`registry_digest` and moves every recorded binding with it. See P1/P2.

#### F6 — Twin-handoff categories 7 and 8 can go stale silently

`test-twin-handoff-completeness.py:56-57` splits `DERIVED_CATEGORIES = (1..6)` from
`AUTHORED_CATEGORIES = (7, 8)`. Categories 1-6 (146 of 167 members) diff to zero in both
directions with negative controls. The 21 authored entries are presence-checked only. If a
decision semantic changes in `claude_policy_controls.py`, nothing forces the matching prose
to move and the suite stays green.

#### F7 — Plan and delivery disagree on the commit scope

`plan.md:219` states "Commits and the PR title use the `speckit-pro` scope". All 13 feature
commits use `car-004` (`feat(car-004)`, `fix(car-004)`, `chore(car-004)`, `docs(car-004)`).
The PR title validated clean against the release-readiness gate
(`.process/pr-packets/car-004-slice-1/validation.json` — `status: passed`, `exit_code: 0`),
so the constitution principle holds; only the plan's own prediction was wrong.

#### F8 — Workflow bookkeeping is stale, and the spec declares no NFR IDs

Every per-phase Results table in `CAR-004-workflow.md` is empty (Specify 215-219, Clarify
274-277, Plan 340-346, Checklist 429-434, Tasks 485-490, Analysis 582-584, Implementation
630-635). The Success Criteria checkboxes at `:96-102` are all unticked. Both autopilot
state files still name the previous spec: `docs/ai/specs/.process/autopilot-state.json`
points at `G56R-003-workflow.md` and `.specify/autopilot-state.json` at `CAR-003`. The
"Lessons Learned" section (`:837-849`) is three empty bullets.

Separately, `spec.md` declares zero `NFR-` IDs; determinism, stdlib-only and suite-cost
constraints live only in plan Technical Context, so they cannot be cited by ID from the spec.

A minor inconsistency in the same family: the requirements checklist records **three**
clarification markers carried into Clarify
(`checklists/requirements.md` iteration-2 table), while the workflow overview and the
Specify-era spec both show **five** (`CAR-004-workflow.md:38`).

### POSITIVE

| # | What improved | Why it is better | Reusable? |
|---|---|---|---|
| V1 | **Anti-transcription discipline.** Frozen enums, the failure-plane derivation, the effort ladder and the candidate-plane pairing are read live from committed bytes rather than restated in Python (`plan.md:32-61`; `claude_policy_controls.py:607-620, 760`). | A mirrored enum and its consumer cannot drift apart silently; a membership change fails closed instead of being absorbed. | **Constitution candidate** for any contract-mirroring work. |
| V2 | **Import-time contract refusal.** `claude_control_comparison.py:122-130` refuses to import at all if its verdict enum disagrees with the committed schema's `messaging_map` required set. | Turns a class of drift into a load failure rather than a test failure — impossible to skip. | Yes. |
| V3 | **Mutation-proven freezing.** Verification seeded two byte-level mutations into the committed registry (a numeric, and the `frozen_at` timestamp alone); each failed 21 assertions and confirmed the timestamp sits inside the digest preimage (`verify-tasks-report.md:88-95`). | Proves content-addressing against shipped bytes, not against a re-derivation of the same code. | Yes. |
| V4 | **The design concept was corrected by annotation, not by edit.** Q10/Q15 keep their original answers; a dated revision note supersedes them (`CAR-004-design-concept.md:23-51`). | The record of what was actually asked and chosen stays honest, so the *reason* the wrong answer looked right stays visible — which is what made F2's root cause traceable at all. | Yes — adopt as the standing rule for correcting interview artifacts. |
| V5 | **Deferred helpers were recorded, never faked.** `generate-uat-skeleton` (deferred) was not invoked and no skeleton was fabricated (`CAR-004-workflow.md:654-664`); reviewability diff mode was recorded as deferred with its exact runner diagnostic rather than worked around (`plan.md:160-189`). | Preserves the difference between "checked" and "unavailable". | Yes. |

---

## Constitution Compliance

`.specify/memory/constitution.md` — no violations.

| Principle | Verdict | Evidence |
|---|---|---|
| I. Plugin Structure Compliance | Pass | Every asset under `tests/speckit-pro/` except the twin-handoff record in `docs/ai/specs/.process/`. Nothing under `speckit-pro/` changed. |
| II. Cross-Platform Runtime & Script Safety | Pass | Stdlib-only confirmed by import resolution across all six new Python files; no new Bash or `jq` dependency (`verify-tasks-report.md:96-98`). |
| III. Semantic Versioning | Pass (not engaged) | No plugin manifest or version field touched. |
| IV. Test Coverage Before Merge | Pass | Three Layer 4 modules registered at `suite-manifest.json:122-124`; 342 test methods, 616 assertions; suite 4909/4909. |
| V. Conventional Commits | Pass | PR title validated by the release-readiness gate (`validation.json`, `status: passed`). See F7 for the plan-vs-delivery scope note. |
| VI. KISS, Simplicity & YAGNI | Pass | Control set closed at three; one shared schema engine rather than two; the frozen partition builder reused rather than duplicated, which removed a file. |

---

## Unspecified Implementations

One artifact landed outside the plan's fifteen declared file operations:

| Artifact | Origin | Assessment |
|---|---|---|
| `.process/CAR-004-live-smoke-runbook.md` (312 lines, commit `39c8de17`) | Written during the UAT step after `generate-uat-skeleton` was found deferred | **Positive and correctly scoped.** It is process output under `.process/`, which `plan.md:232-234` already excludes from the estimator, so it does not breach the declared file set. It is also the single best mitigation available for F4 short of running T062: a plain-English operator runbook with numbered steps, the four bounds, the observable that proves each control, and the seal procedure. |

No scope creep. No requirement was implemented that the spec does not carry, and no
implemented behavior lacks a requirement.

---

## Task Execution Analysis

| Metric | Value |
|---|---|
| Tasks generated | 64 across 4 phases, 8 groups |
| Completed | 63 (98.4%) |
| Open | 1 — T062, operator-only, cannot be agent-executed |
| Parallel-marked | 18 |
| RED→GREEN TDD pairs | 25 |
| Tasks added during implementation | 0 |
| Tasks dropped | 0 |
| Phantom completions | 0 of 63 (independent session) |
| Dead public symbols | 0 of 44 scanned |
| Stubs / `TODO` / `NotImplementedError` | 0 across six new Python files |

Task fidelity was effectively perfect: the generated task list covered all fifteen declared
file operations, added none, and every one that was marked complete survived a five-layer
independent verification in a separate agent session (`verify-tasks-report.md:33-114`).

One task-generation defect was caught late, by the three-lens audit rather than by G5:
parallel-safe `[P]` markers had been placed on tasks sharing a file, a lost-edit hazard
(`e404cae4` commit body). G5's coverage check verifies that every file operation has a task;
it does not verify that `[P]` markers are disjoint by file.

---

## Lessons Learned

1. **The gates did not produce this run's quality; adversarial review did.** 82 defects were
   caught across three audit rounds. The phase gates caught the count of artifacts, not their
   correctness — and the one gate aimed squarely at ambiguity was structurally incapable of
   firing.

2. **A gate that has never been observed failing is not a passing gate.** G1 has returned
   `pass` on every spec in this repository, and the reason is a regex, not spec quality. The
   parity test suite made this invisible because it tests Python-against-Bash agreement, not
   behavior-against-template.

3. **Stale upstream context is a defect factory with a long tail.** One line of superseded
   roadmap prose propagated through the grill-me interview into the Specify output and was
   caught only by an adversarial pass. Four such lines are still live, two of them in
   program-wide sections, and seven specs remain to be scoped against them.

4. **Remediation is authoring.** The checklist pass more than doubled the spec and was
   self-certified complete; an audit immediately after found 19 defects, 3 blocking. Large
   remediation deltas need the same verification as the original authoring.

5. **"Split / medium confidence" must survive into the artifact.** The registry-serialization
   clarification resolved on a split vote and invented numerics no repo artifact settles.
   `spec.md` records only the outcome. Confidence that is not written down is confidence a
   future reader cannot discount.

6. **Correct interview artifacts by annotation, not by edit.** Leaving the wrong Q10/Q15
   answers in place with a dated revision note is the only reason the roadmap root cause was
   traceable at all.

7. **Agent-unrunnable tasks need a louder contract than an unticked box.** T062 is honestly
   unticked in three places, and the PR body still reads as complete because it never names
   the six criteria that ship unevidenced.

---

## Recommendations

### CRITICAL — before this PR merges

| # | Action | Owner |
|---|---|---|
| R1 | Either execute T062's three live smokes, or amend the PR body to name **SC-009, SC-026, SC-027, SC-029, SC-030, SC-031** as shipping without evidence. The self-review already asked for this (`CAR-004-workflow.md:820-822`) and it was not done. | Human operator |

### HIGH — process fixes this run argues for

| # | Action | Rationale | Where |
|---|---|---|---|
| R2 | **Fix the clarification-marker regex** to `\[NEEDS CLARIFICATION(:[^\]]*)?\]` at all six call sites, and add a positive regression test: a fixture spec containing a parameterized marker must fail G1, G2 and G3 and must be counted by `count-markers`. | F1. Without the test the fix regresses on the next refactor. | `speckit-pro/speckit_pro_runner/helpers/read_only.py:716,749,750,758,775,781,787`; `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` |
| R3 | **Stop relying on parity tests for correctness.** Every gate whose only coverage is `assert_helper_matches_bash_reference` needs at least one behavior test that asserts the failing case. Audit the other six gates for the same shape. | F1. Parity between two copies of a wrong rule is not verification. | `test-speckit-pro-read-only-helpers.py:1508-1525` |
| R4 | **Correct the roadmap's four stale authentication lines before CAR-005 is scoped**, and add a scoping precondition: grill-me must reconcile the roadmap section it reads against the PRD amendment log before recommending anything derived from it. | F2. Two of the four lines are program-wide; CAR-005 through CAR-011 inherit the trap. | `docs/ai/specs/claude-agent-routing-technical-roadmap.md:159-160, 339, 359-360, 1110` |
| R5 | **Re-verify after large checklist remediation.** Make an audit pass mandatory — not optional — whenever remediation grows an artifact beyond a threshold (this run: +118% in one commit, 19 defects found immediately after, 3 blocking). Treat "N of N gaps remediated" as an input to verification, not as verification. | F3 | Workflow / autopilot checklist phase |
| R6 | **Extend the G5 task check to `[P]` disjointness by file.** The audit caught parallel markers on tasks sharing a file; the gate did not. | Task Execution Analysis | Gate G5 |
| R7 | **Require split-confidence outcomes to be written into the spec**, with the dissent named — not just into the workflow overview. | F5, P3 | Clarify consensus protocol |

### MEDIUM

| # | Action | Rationale |
|---|---|---|
| R8 | Promote the anti-transcription rule (V1) and import-time contract refusal (V2) to constitution candidates for contract-mirroring work. | Both converted whole classes of drift into hard failures on this run. |
| R9 | Adopt correction-by-annotation (V4) as the standing rule for design-concept and interview artifacts. | It is what made F2's root cause traceable. |
| R10 | Derive twin-handoff categories 7 and 8, or add a drift check that fails when the semantics they describe change. | F6 — 21 of 167 entries can go stale with a green suite. |

### LOW

| # | Action |
|---|---|
| R11 | Backfill the empty Results tables and Lessons Learned in `CAR-004-workflow.md`, tick the Success Criteria boxes, and advance both `autopilot-state.json` files off CAR-003/G56R-003 (F8). |
| R12 | Reconcile the three-vs-five clarification-marker count between `checklists/requirements.md` and `CAR-004-workflow.md:38` (F8). |
| R13 | Align `plan.md:219`'s commit-scope claim with the `car-004` scope actually used (F7). |
| R14 | Consider whether determinism / stdlib-only / suite-cost constraints should carry `NFR-` IDs in `spec.md` rather than living only in plan Technical Context (F8). |

---

## File Traceability Appendix

### Delivered — all 15 declared operations present

| File | Op | Covers |
|---|---|---|
| `tests/speckit-pro/layer6-efficiency/contracts-claude/policy-control-registry.schema.json` | NEW | FR-001…FR-018, FR-030a |
| `tests/speckit-pro/layer6-efficiency/contracts-claude/control-comparison.schema.json` | NEW | FR-019…FR-025d |
| `tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py` | NEW | FR-001…FR-018, FR-026…FR-033 |
| `tests/speckit-pro/layer6-efficiency/lib/claude_control_comparison.py` | NEW | FR-019…FR-024a |
| `tests/speckit-pro/layer6-efficiency/fixtures-controls/policy-control-registry.json` | NEW | FR-002…FR-002c, FR-030a |
| `tests/speckit-pro/layer6-efficiency/fixtures-controls/control-comparison.json` | NEW | FR-021…FR-024a |
| `tests/speckit-pro/layer6-efficiency/fixtures-controls/partition-registry-entries.json` | NEW | FR-025…FR-025d |
| `tests/speckit-pro/layer6-efficiency/fixtures-controls/control-replay.json` | NEW | FR-028, FR-029, FR-012a, FR-014a |
| `tests/speckit-pro/layer6-efficiency/run-control-smoke.py` | NEW | FR-030…FR-033 (operator path) |
| `tests/speckit-pro/unit/test-policy-control-contracts.py` | NEW | SC-001…SC-007, SC-012, SC-014, SC-021…SC-025 |
| `tests/speckit-pro/unit/test-control-comparison-dominance.py` | NEW | SC-008, SC-016, SC-019 |
| `tests/speckit-pro/unit/test-twin-handoff-completeness.py` | NEW | SC-011, SC-013 |
| `tests/speckit-pro/suite-manifest.json` | MODIFIED | Layer 4 registration (`:122-124`) |
| `docs/ai/specs/.process/CAR-004-twin-handoff.md` | NEW | FR-034…FR-037a |
| `docs-site/src/content/docs/reference/tests.md` | MODIFIED | Generated reference regen (CI `validate-docs`) |

### Referenced but unexecuted

| File | Status |
|---|---|
| `specs/car-004-policy-controls-comparators/quickstart.md` §5 | Sections 1-4 walked clean (T061); §5 never run |
| `.process/CAR-004-live-smoke-runbook.md` | Authored, never executed |
| `tests/speckit-pro/layer6-efficiency/results/` | Empty and untracked, as designed (T003, T060) |

### Evidence commits

| Commit | Role |
|---|---|
| `1ab5ee9b` | Specify + six adversarial corrections, incl. the AC-2.19 authentication fix |
| `01105f64` | Clarify (5 markers, 2 sessions) + Plan |
| `2a7fd18e` | Checklist remediation (135 items / 57 gaps) + Tasks (64) |
| `e404cae4` | Three-lens audit — 19 findings, 3 implementation-blocking |
| `3c5415f6` | Implementation — 11,657 insertions across 17 files |
| `39c8de17` | Post-implementation verification, live-smoke runbook, PR packet |

---

## Self-Assessment Checklist

| Item | Result | Note |
|---|---|---|
| Evidence completeness | **PASS** | Every finding carries a `file:line` or commit citation. F1 was reproduced by executing the real gate helper; the marker-form mismatch was reproduced by running the regex. |
| Coverage integrity | **PASS** | All 75 FR IDs and all 31 SC IDs are enumerated by status. 0 NFR IDs exist in `spec.md` and that absence is itself reported (F8). No ID is missing. |
| Metrics sanity | **PASS** | `completion_rate` 63/64 = 98.4% → 98. `spec_adherence` = (97 + 0 + 9x0.5)/106 = 95.75% → 95.8%. Counts reconcile: 97 + 9 = 106. |
| Severity consistency | **PASS** | 0 CRITICAL (no constitution violation, no breaking change, no security issue). 4 SIGNIFICANT — one blind gate, one live upstream drift, one under-verified remediation, one undisclosed evidence gap with a pre-merge action. 4 MINOR, 5 POSITIVE. |
| Constitution review | **PASS** | All six principles reviewed individually against delivered evidence. **No violations.** |
| Human Gate readiness | **PASS** | Three spec changes are proposed and populated under Proposed Spec Changes. No confirmation was requested or granted; `spec.md` was **not** modified. |
| Actionability | **PASS** | 14 recommendations, prioritized CRITICAL/HIGH/MEDIUM/LOW, each traced to a numbered finding and pointing at a specific file or gate. |
