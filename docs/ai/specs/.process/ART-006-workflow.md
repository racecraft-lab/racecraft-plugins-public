# SpecKit Workflow: ART-006 — Autopilot Staging

**Template Version**: 1.0.0
**Created**: 2026-07-30
**Purpose**: Reusable template for executing SpecKit workflows. Copy-paste the prompts below into your AI coding agent.

---

## Prerequisite — Discharged 2026-08-03

**The bookkeeping-durability prerequisite has merged and shipped. Phase 1 may
start.**

ART-006 ships durable stage state, and the store it relies on was unenforced
when this workflow was scaffolded — it had already drifted on CAR-005 and
ART-001. That is fixed:

| Component | Landed in |
|---|---|
| Bookkeeping enforcement on both platforms | PR #416 (`ccc4e7d6`) |
| Codex phase guard made runnable (`resolved_python`, `--rule status-evidence`) | PR #417 (`a6704ce0`) |
| Released to consumers | speckit-pro 2.22.0, PR #408 (`70524e24`) |

What the prerequisite established that this spec now builds on:

- `speckit-pro/skills/speckit-autopilot/SKILL.md:438` stages the workflow file
  and `autopilot-state.json` on phases 1–6, so per-phase writes are durable
  instead of waiting for phase 7's `git add -A`.
- `speckit-pro/skills/speckit-autopilot/contracts/autopilot-state-status.schema.json`
  fixes the ownership split this spec depends on: `autopilot-state.json` is the
  in-flight pointer for one run; **the workflow file is the durable per-spec
  record, and it survives archive.**
- `tests/speckit-pro/layer1-structural/validate-workflow-status-evidence.py`
  gates every `docs/ai/specs/.process/*-workflow.md` in CI, whether or not an
  agent invokes anything.

The original evidence and the six-component scope remain recorded in the design
concept under "Hard dependency", marked discharged.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/ART-006-design-concept.md
```

Re-read it before each phase if you need to disambiguate a prompt. The
Specify and Clarify Prompts below were populated from that interview,
so the design concept doc is the source of truth for any decision
captured during scoping.

> **Note:** Grill Me is human-in-the-loop only. It is **not** part of
> the autopilot loop. Once the workflow file is populated and autopilot
> begins, clarifications happen via `/speckit-clarify` and the
> consensus protocol — never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | G1 pass — 14 FR, 3 user stories, 8 success criteria, 11 acceptance scenarios, 0 markers |
| Clarify | `/speckit-clarify` | ✅ Complete | G2 passed. 3 of 3 sessions resolved via 2-analyst consensus (Session 2 needed a Round 2 tiebreak); spec 22 → 31 normative items, 0 `[NEEDS CLARIFICATION]` markers |
| Plan | `/speckit-plan` | ✅ Complete | G3 passed. plan.md + research.md + data-model.md + quickstart.md + 2 contracts; 0 markers. Shared stage resolution sited as runner operation `resolve-autopilot-stage`. Re-estimate 430 reviewable LOC / 17 files — warn on both, block on neither; one slice, no split, rationale recorded in plan.md |
| Checklist | `/speckit-checklist` | ⏳ Pending | Run for each domain |
| Tasks | `/speckit-tasks` | ⏳ Pending | |
| Analyze | `/speckit-analyze` | ⏳ Pending | |
| Confidence Gate | G6.5 | ⏳ Pending | Plan stage's terminal step (design concept Q7) |
| Implement | `/speckit-implement` | ⏳ Pending | |
| Post | Post-Implementation | ⏳ Pending | |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates (SpecKit Best Practice)

Each phase requires **human review and approval** before proceeding:

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | All user stories clear, no `[NEEDS CLARIFICATION]` markers remain |
| G2 | After Clarify | Ambiguities resolved, decisions documented |
| G3 | After Plan | Architecture approved, constitution gates pass, dependencies identified |
| G4 | After Checklist | All `[Gap]` markers addressed |
| G5 | After Tasks | Task coverage verified, dependencies ordered |
| G6 | After Analyze | No `CRITICAL` issues, `WARNING` items reviewed |
| G6.5 | Before Implement | Composite confidence meets the autonomous implementation threshold |
| G7 | After Each Implementation Phase | Tests pass, manual verification complete |

---

## Prerequisites

### Constitution Validation

**Before starting any workflow phase**, verify alignment with the project constitution (`.specify/memory/constitution.md`):

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| I. Plugin Structure Compliance | Manifests, skills, agents keep their required shape | `python3 tests/speckit-pro/run-all.py --layer 1` — 1443/1443 |
| II. Cross-Platform Runtime & Script Safety | Python 3.11+ stdlib only; no new Bash or `jq` | Layer 1 `validate-scripts` + repo Bash-confinement tests pass |
| III. Semantic Versioning | Version and manifest drift blocked | Layer 1 `validate-plugin` / `validate-codex-plugin` pass at 2.22.1 |
| IV. Test Coverage Before Merge | New behavior ships with tests | `python3 tests/speckit-pro/run-all.py` — 7052/7052 baseline on this tree |
| V. Conventional Commits | `<type>(<lowercase-scope>): <description>` | Validated against the live release-readiness gate before PR creation |
| VI. KISS, Simplicity & YAGNI | Smallest change that satisfies the spec | Enforced at Plan/Analyze and the 382-LOC reviewability budget |

**Constitution Check:** ✅ — full suite 7052/7052 on the merged tree (2026-08-04), recorded before G1.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | ART-006 |
| **Name** | Autopilot Staging |
| **Branch** | `art-006-autopilot-staging` |
| **Dependencies** | None on the roadmap. The bookkeeping prerequisite is discharged (PRs #416/#417, released 2.22.0). |
| **Enables** | ART-007, ART-008, ART-009, ART-010, ART-011, ART-012 |
| **Priority** | P1 |
| **Stage** | plan |

**The `Stage` row is this spec's own deliverable and its authoritative store.**
Per the 2026-08-03 re-grill (Q9), the workflow file holds durable stage state and
`autopilot-state.json` mirrors it for the running session only — the split
`autopilot-state-status.schema.json` already states. This scalar table is the
right carrier because `speckit-status/SKILL.md:96` already parses it for Branch;
the Workflow Overview status table is not, because two parsers read that row
shape. Values are `plan`, `implement`, `full`.

### Reviewability Budget And Split Decision

The setup gate returned `status: warn`, `pass: true`, `blockers: []` — the
warning is `primary surfaces 3 exceeds warn threshold 1`, which the gate derives
from the roadmap document as a whole rather than from this spec. Recording the
budget and split decision as the warn path requires:

| Signal set | Reviewable LOC | Slices | Status |
|---|---|---|---|
| Roadmap-declared (3 stories, 6 files, 8 FRs, modify) | 217 | 1 | ok |
| **Adopted — honest count, `gh` deferred (3, 12, 14, modify)** | **382** | **1** | **ok** |
| If `gh` had stayed in scope (3, 14, 18, modify) | 452 | 2 | warn |
| **G3 re-estimate against real artifacts (2026-08-04)** | **430** | **1** | **warn** |

**Split decision: one slice, no split.** The work is vertical — one capability
cutting end-to-end through argv, resolution, the phase loop, durable state, and
both platforms. Deferring the `gh` limb to ART-007 is what keeps it under the
800 block ceiling. The roadmap's 217 reproduces exactly from "6 files, 8 FRs", so
it restates its own file count rather than measuring independently.

**The 18-LOC margin is consumed.** The G3 re-estimate against real artifacts is
430 LOC across 17 files, which warns on both dimensions and blocks on neither.
The growth over the ratified 382 is not new capability: it is the nine lettered
sub-requirements Clarify added, all of which *narrow* existing behaviour, plus
three test-registry files the registered-operation contract forces. The split
decision is unchanged — splitting would put argv parsing in one PR and the
resolution it feeds in another, a worse review unit than the whole vertical.
Two consequences to carry forward: the margin is no longer available as an
argument for rejecting scope (it was used that way at Clarify S1/Q4, where the
rehydration path was also rejected on independent grounds), and any further
growth should be met by deferring a limb rather than by re-arguing the split.
Re-check at the PR-time diff-mode gate, which measures the real diff.

### Success Criteria Summary

- [ ] `--stage plan|implement|full` parses and bounds the phase loop on **both**
      distributions
- [ ] A bare invocation resolves the stage from the workflow file's status table
- [ ] Explicit `--stage` overrides auto-detection; `--from-phase` still resumes
      **within** a stage
- [ ] Conflicting flags fail fast at pre-flight with a usage error, before any
      phase work
- [ ] Stage state is recorded durably in the workflow file and survives a fresh
      session or a different worktree
- [ ] The plan stage terminates with its own commit; per-phase staging includes
      the workflow file
- [ ] G6.5 runs as the plan stage's terminal step
- [ ] Out-of-stage task-list entries are marked `skipped:`, and the canonical
      list is not truncated
- [ ] Gate semantics G0–G7 and G6.5 are unchanged
- [ ] Golden fixtures pin stage resolution; the test is registered in
      `tests/speckit-pro/suite-manifest.json`
- [ ] The scaffold → autopilot chain contract is documented for ART-011
- [ ] Codex parity checks pass and the Codex body stays under the 8000-word cap

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/art-006-autopilot-staging/spec.md`

### Specify Prompt

```text
/speckit-specify First-class autopilot stages (plan, implement, full) with auto-detection and durable stage state, on both platforms
```

#### Detailed Prompt (for complex specs)

```text
/speckit-specify

## Feature: Autopilot Staging

### Problem Statement

Autopilot runs all seven SDD phases as one unbroken sequence. There is no
supported way to stop after planning, let a human review the result, and later
resume into implementation. The whole staged-review workflow the ART roadmap is
building depends on that boundary existing.

### Users

Maintainers running `/speckit-pro:speckit-autopilot` on either platform, and the
five downstream ART specs (ART-007, ART-008, ART-009, ART-010, ART-011, ART-012)
that consume the stage vocabulary.

### User Stories

- **US1 — Explicit staging.** As a maintainer I run `--stage plan` and autopilot
  executes specify through analyze plus G6.5, commits the stage boundary, and
  stops without touching implementation.
- **US2 — Resume into implementation.** As a maintainer I later run
  `--stage implement`, from a fresh session or a different worktree, and
  autopilot resumes at Phase 7 with the plan stage's state intact.
- **US3 — Bare invocation.** As a maintainer I run autopilot with no stage flag
  and it resolves the correct stage from the workflow file's status table.

### Constraints

- Both distributions in this slice. Claude `skills/` and Codex `codex-skills/`.
- Gate semantics G0-G7 and G6.5 are unchanged; only stage ownership of G6.5 is
  decided.
- Python 3.11+ standard library only. No new Bash dependency.
- The canonical task list is never truncated per stage; out-of-stage entries are
  marked `skipped:`, the only non-complete status the Codex pre-final audit
  already tolerates.
- Four Codex sentences are string-pinned by Layer 1 and must survive verbatim;
  Codex prose is additive only.
- The Codex autopilot body has roughly 390 words of headroom under an 8000-word
  cap.
- Stage resolution must be shared logic both platforms execute, not two prose
  descriptions — nothing in CI diffs the two SKILL.md variants.

### Out of Scope

- `gh` draft-PR corroboration — deferred to ART-007, which creates the draft PRs
  it would corroborate against. Amend the roadmap Scope line to record this.
- Draft-PR creation (ART-007), feedback sweep (ART-008), scaffold-side chain
  implementation (ART-011).
- Any change to what a gate passes or fails on.
- Per-agent user override features.
```

### Specify Results

<!-- Fill in after running the command -->

| Metric | Value |
|--------|-------|
| Functional Requirements | FR-001 through FR-014 (14) |
| User Stories | 3 (US1 explicit staging P1, US2 resume into implement P2, US3 bare invocation P3) |
| Acceptance Criteria | 11 acceptance scenarios, 8 measurable success criteria |
| `[NEEDS CLARIFICATION]` markers | 0 |
| Gate G1 | ✅ PASS — `validate-gate` reported `spec.md exists with 0 markers` |
| Codex word budget (re-measured) | 7673 of 8000; headroom 327, not the stale ~390 the prompt above records |

### Files Generated

- [x] `specs/art-006-autopilot-staging/spec.md`

### SpecKit Traceability Markers

Use these markers in spec.md for traceability through later phases:

| Marker | Purpose | Example |
|--------|---------|---------|
| `[US1]`, `[US2]` | User story reference | `[US1] User searches by query` |
| `[FR-001]` | Functional requirement | `[FR-001] API returns paginated results` |
| `[NEEDS CLARIFICATION]` | Flag for Clarify phase | `Auth method [NEEDS CLARIFICATION]` |
| `[P]` | Parallel-safe task | `[P] Can run alongside other tasks` |
| `[Gap]` | Missing coverage | `[Gap] No task covers error handling` |

---

## Phase 2: Clarify

**When to run:** When spec has areas that could be interpreted multiple ways. 10-20 minutes here saves hours of rework later.

**Best Practice:** Maximum 5 targeted questions per Clarify session.

### Clarify Prompts

Seeded from the design concept's Open Questions. Do not re-litigate anything in
its "Decisions settled by evidence" section, nor anything the 2026-08-03 re-grill
closed (Q9, Q10, Q11) — those have determinate answers cited in the design
concept.

#### Session 1: Stage State Representation

```text
/speckit-clarify Focus on the mechanics of stage state, NOT its location. The
location is settled by design-concept Q9 and must be treated as a given: the
workflow file is authoritative via a "Stage" row in "## Specification Context ->
Basic Information", and autopilot-state.json mirrors it for the running session
only. This matches the split stated in
speckit-pro/skills/speckit-autopilot/contracts/autopilot-state-status.schema.json
-- the state file is the in-flight pointer, the workflow file is the durable
per-spec record that survives archive. Do not reopen frontmatter, a status-table
column, or state-file-authoritative. Template ownership is also settled: PR #416
edited workflow-template.md directly, so speckit-coach ownership does not block
an edit. What is still open and must be settled here: the exact stage vocabulary
beyond plan/implement/full; whether the row is written once per stage transition
or refreshed per phase; how the mirror in autopilot-state.json is kept from
drifting from the authoritative row, given that undetected drift between these
two stores is what caused this spec's prerequisite; and precisely what a fresh
--stage implement session in a different worktree must read to reconstruct
context.
```

#### Session 2: Platform Parity And Enforcement Surface

```text
/speckit-clarify Focus on how the two distributions stay genuinely in step.
Stage resolution must be shared logic both platforms execute, because
validate-codex-parity.py:134 checks file existence only and the two argv
contracts have already silently diverged over --strict/--advisory. Settle: where
the shared logic physically lives and how each platform reaches it; the exact
allowed-tools grant on the Claude side, given the chosen narrow-plus-runner scope
and the documented Bash(${CLAUDE_SKILL_DIR}/...) idiom. Do NOT reopen where the
Codex stage prose lives -- design-concept Q10 settled it: the prose goes in
phase-execution-codex.md and SKILL.md gets only the argv line and a pointer,
roughly 60-80 words. Treat the budget as measured, not estimated: the Codex
autopilot SKILL.md body is 7690 of 8000 words (validate-codex-skills.py:168-171),
so headroom is 310 words, and the cap applies to the SKILL.md body alone while
referenced files are uncapped and still folded into runtime_doc at :235-242. What
is open here: exactly which pointer wording goes in SKILL.md, and whether any new
Codex-checked string is needed at all -- adding one requires the three-step
ritual: edit the SKILL.md, add the assertion to validate-codex-skills.py, update
CODEX-PARITY-NOTES.md.
```

#### Session 3: Stage Boundary Semantics

```text
/speckit-clarify Focus on what exactly happens at the plan/implement seam.
Settle: what the plan-stage terminal commit stages and what its message says;
which paths per-phase staging adds now that it widens beyond `git add specs/`;
how the out-of-stage `skipped:` marker is worded so the Codex pre-final audit at
codex-skills/speckit-autopilot/SKILL.md:986-992 accepts it; how a --stage
implement run inherits the session-scoped CONFIDENCE_GATE_MODE that G6.5 may not
re-resolve (SKILL.md:336) and the G0 baseline that G7 compares against
(references/gate-validation.md:366); and the concrete shape of the scaffold ->
autopilot chain contract that ART-011 will consume, which is documentation only
per roadmap :454 and :459-460.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Stage State Representation | 5 asked, 4 routed to consensus | FR-001 pinned to literal `plan`/`implement`/`full`; FR-008 split into authority + at-rest meaning + write cadence; FR-010/SC-003 narrowed with a marker-evidence carve-out; new FR-012a (foreign state slot) and FR-014a (rule-key registration). Spec grew 22 → 27 normative items, 0 markers. |
| 2 | Platform Parity And Enforcement Surface | 3 asked, 3 routed to consensus | All three split 1-1 in Round 1 and were settled by a Round 2 tiebreak. FR-012 now names the shared substrate (a registered runner operation, not the phase-coverage guard); new FR-015a sites the argument-parity assertion in the unit test rather than the structural parity validator; FR-002 also repairs the stale Claude usage synopsis. Spec 27 → 30 normative items. |
| 3 | Stage Boundary Semantics | 5 asked, 5 resolved | FR-008b gained the no-empty-commit rationale; FR-009 requires a distinct post-gate terminal commit; new FR-009a enumerates the staged path set; FR-011 fixed four constraints on the out-of-stage `skipped:` marker; FR-010a preserves the test-count baseline and (settled after the S2 tiebreak) accepts the confidence-mode flags with an explicit diagnostic; FR-016 fixed the five-item scaffold chain contract. Spec 30 → 31 normative items. |

### Consensus Resolution Log

Two analysts were routed from the session's category tags (`[codebase]`,
`[spec]`); no `[domain]` or `[security]` tag appeared, so the domain researcher
was not in the union.

| Item | Categories | Round | codebase-analyst | spec-context-analyst | Resolution | Artifact edit |
|---|---|---|---|---|---|---|
| S1/Q1 stage-mirror enforcement + repair direction | `[codebase] [spec]` | 1 | partially | partially | Converged: two *different* checks (in-run mirror freshness, at-rest self-consistency) both extending shipped machinery; repair workflow → state. Both corrected the orchestrator's framing — the existing two-item list is the *state-wins* set, so a workflow-wins field needs its own clause. | FR-008 rewritten; FR-014 split |
| S1/Q2 literal tokens, at-rest meaning, absence | `[spec] [codebase]` | 1 | yes | yes | 2-of-2 agreement, both high confidence. Tokens are lowercase literals; the entry records last *resolved* stage; absence means "no run yet" and must not error. | FR-001, FR-008a, Key Entities, Assumptions, new edge case |
| S1/Q3 `--stage implement` against a foreign state slot | `[codebase]` | 1 | partially | not routed | Accepted. Parity gap confirmed (Codex covers only a *missing* file, Claude documents none). Re-init must precede the guard. Analyst correctly refused to endorse the `prior_run_note` field name — zero occurrences repo-wide. | FR-012 extended; new FR-012a; new edge case |
| S1/Q4 FR-010 scope vs marker evidence | `[codebase] [spec]` | 1 | yes, w/ framing correction | **no** on the remedy | Split resolved without Round 2: both agreed the contradiction is real and that the fix is a text carve-out. The rehydration path was rejected as scope creep against an 18-LOC margin, and the codebase analyst's framing correction was carried — marker evidence is *inside* the implement stage, governed by its own stricter rule, not outside it. | FR-010 and SC-003 narrowed |
| S1/Q5 write cadence + commit atomicity | — | not routed | — | — | Single-source, high confidence, no conflict. Promoted from an Assumption to a requirement. | FR-008b |
| S2/R1 substrate for shared stage resolution | `[codebase] [spec]` | 1 → **2** | A: phase-coverage guard | B: runner operation | 1-1 split → Round 2 tiebreak: **B**. The guard takes only a workflow path, a state path, two expected-commit arguments and a rule selector — it is a consistency checker over resolved inputs, not a resolver, and siting resolution there contradicts the opening-preparation directive to reach helper behaviour through the runner. The guard may still import the resolver as a library. | FR-012 extended |
| S2/R2 where the argument-parity assertion lives | `[codebase]` | 1 → **2** | A: structural parity validator | B: unit test | 1-1 split → Round 2 tiebreak: **B**. The structural validator's checks are existence-only by design and its counted baseline would need regenerating; this spec's own record already names it as unable to catch this class of divergence. | new FR-015a |
| S2/R3 stale Claude usage synopsis | `[spec]` | 1 → **2** | A: repair here | B: defer | 1-1 split → Round 2 tiebreak: **A**. The omission is stale documentation, not missing capability — the Claude side already resolves the confidence-mode flags from the invocation arguments — and the same synopsis line is edited anyway to add the stage argument, so the repair costs one line and changes no gate behaviour. | FR-002 extended |
| S3/Q1 terminal commit identity + empty-commit risk | `[codebase]` | 1 | yes | not routed | Accepted. The confidence-gate row always advances off pending, so the planning stage's terminal commit is non-empty regardless of whether `Stage` changed; it is a distinct commit taken *after* the gate resolves, not a renamed analysis-phase commit. | FR-008b, FR-009 |
| S3/Q2 staged path set | `[codebase]` | 1 | yes | not routed | Accepted. Enumerate the specification directory, workflow file, and state file explicitly — the workflow *directory* also holds untracked run byproducts, a failure that passes locally and fails only on a clean checkout. | new FR-009a |
| S3/Q3 out-of-stage entry marking | `[codebase] [spec]` | 1 | yes | yes | 2-of-2 agreement. Three of the four marker constraints were verified against the shipped validator: the marker occupies the **status** field with the entry **name byte-identical** (the guard matches checkpoints by exact name equality), must not contain `pending` in any casing, and reuses the existing `skipped: <reason>` shape. A planning-stage run marks the implementation phase *and every post-implementation entry*. | FR-011 |
| S3/Q4 baseline preservation + flag handling | `[spec]` | 1 (deferred) | not routed | yes | Baseline preservation accepted immediately: a post-planning recount would make the later increase check vacuous, so a differing count is a non-blocking drift diagnostic. The flag-handling half was deferred pending S2/R3 and settled with it — flags are **accepted** with an explicit diagnostic, not rejected, because FR-013 confines Codex changes to additive ones. | FR-010a |
| S3/Q5 scaffold-to-autopilot chain | `[spec]` | 1 | not routed | yes | Accepted. Five items the downstream scaffold-integration spec cannot derive: handoff artifact, entry precondition, per-platform invocation form + closed stage vocabulary, workflow-observable completion signal, and the fact that this spec ships no scaffold-side code. | FR-016 |

**Bug found during consensus, outside this spec's scope.** The store-precedence
documentation names `autopilot-state.json.workflow_file` as the authority and
quotes a failure message for a mismatch. That check is inert under every
invocation the phase loop issues: its error key is absent from the guard's
rule-to-problem-key map, and its body short-circuits unless a v2 marker-plan
schema and an expected-head-commit argument are both supplied. Verified by
direct execution against a state file naming a different specification — the
guard exits 0 and reports `pass`, with and without the scoping flag. ART-006
does not fix this; FR-014a exists so this specification does not reproduce it.
Worth its own issue against the plugin.

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/art-006-autopilot-staging/plan.md`

### Plan Prompt

```text
/speckit-plan

## Tech Stack
- Runtime: Python 3.11+ standard library only. No new Bash or jq dependency.
- Surfaces: Claude skill files under speckit-pro/skills/, Codex mirrors under
  speckit-pro/codex-skills/, shared references, and the runner under
  speckit-pro/speckit_pro_runner/.
- Testing: repository suite via `python3 tests/speckit-pro/run-all.py`. Layer 1
  structural, Layer 4 unit with golden fixtures, Codex parity validators.
- Docs: docs-site (Node >= 22.12, pnpm) for reference regeneration.

## Constraints
- Both distributions land in this slice; parity comes from shared logic, not
  from a parity test -- validate-codex-parity.py:134 checks existence only.
- Codex prose is additive only. Four sentences are string-pinned by
  tests/speckit-pro/layer1-structural/validate-codex-skills.py at :292, :295,
  :306-310 and :313-318.
- Claude's anti-stall line at skills/speckit-autopilot/SKILL.md:50-51 says "do
  not stop early, complete all 7 phases" -- unpinned prose that a --stage plan
  run contradicts verbatim, so it must be reworded to bind to the resolved stage.
- Codex body headroom is 329 words, re-measured 2026-08-04 after PR #419 removed
  the effort gate: the SKILL.md body is 7671 of the 8000-word cap at
  validate-codex-skills.py:168-171. Measure with `structural_helpers.body` from
  tests/speckit-pro/lib/ -- it is a module-level function, and a hand-rolled
  frontmatter regex gives a slightly different count. The cap applies
  to the SKILL.md body alone; referenced files are uncapped and still folded into
  runtime_doc at :235-242. Per design-concept Q10, stage prose goes in
  phase-execution-codex.md and SKILL.md carries only the argv line and a pointer.
- Declared budget 382 reviewable LOC, one slice. Re-estimate at G3.

## Decisions fixed by the 2026-08-03 re-grill (do not re-derive)
- Q9 -- Durable stage state lives in the workflow file, in the "Stage" row of
  "## Specification Context -> Basic Information". autopilot-state.json mirrors
  it for the running session only. This is the split already stated by
  speckit-pro/skills/speckit-autopilot/contracts/autopilot-state-status.schema.json,
  which PR #416 shipped: the state file is the in-flight pointer for one run, the
  workflow file is the durable per-spec record and survives archive. Plan the
  mirror-consistency mechanism, not the location.
- Q10 -- Codex stage prose lives in phase-execution-codex.md. See the budget
  constraint above.
- Q11 -- Verification extends the shipped CI gate rather than adding a second
  one: put stage-field assertions into
  tests/speckit-pro/layer1-structural/validate-workflow-status-evidence.py, which
  PR #416 added and which already scans every docs/ai/specs/.process/*-workflow.md
  for status-versus-evidence contradiction. Add
  tests/speckit-pro/unit/test-autopilot-stage-resolution.py with golden fixtures
  for argv and auto-detect resolution, and register it in
  tests/speckit-pro/suite-manifest.json -- the manifest is the only dispatch
  roster. Do not name any file with "art" in it: test-unit-layout.py:122-141
  derives live spec families from docs/ai/specs/**/*.md, so art-006 in a tracked
  script filename is a hard failure.

## Architecture Notes
- Stage resolution is shared logic executed by both platforms, reached on Claude
  through a narrow allowed-tools grant covering the bundled validator and
  `python3 -m speckit_pro_runner`, using the documented
  Bash(${CLAUDE_SKILL_DIR}/...) idiom.
- G6.5 is the plan stage's terminal step. It runs "After Phase 6 commits and
  before Phase 7 begins" (references/phase-execution.md:565) and its strict-mode
  STOP already directs operators to resume with --from-phase implement (:622).
- The plan stage closes with its own commit, and per-phase staging widens beyond
  `git add specs/` (SKILL.md:413) so the workflow file reaches git as it changes.
- Durable per-spec state lives in the workflow file, which survives archive;
  autopilot-state.json is a current-in-flight pointer, not per-spec history.
- Conflicting flags fail fast at pre-flight, following the exact precedent at
  speckit_pro_runner/helpers/read_only.py:980-981 and the rationale at
  references/phase-execution.md:575.
- Editing either SKILL.md dirties 84 generated mirrors. Account for the
  generated-artifact contract; regenerate rather than hand-edit.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ✅ | Technical context, execution flow, reviewability governance, alternatives-rejected table |
| `research.md` | ✅ | Decision rationales |
| `data-model.md` | ✅ | Stage entity, state contract, workflow-file entry |
| `contracts/` | ✅ | `stage-invocation.md` (argv surface + `resolve-autopilot-stage`), `scaffold-autopilot-chain.md` (FR-016 five-item handoff contract) |
| `quickstart.md` | ✅ | Developer onboarding incl. regeneration step |

**G3 verification (orchestrator, independent of the executor's self-report).**
`[NEEDS CLARIFICATION]` markers across all Phase 3 artifacts: **0**. Absolute
`/Users/` or `/home/` paths: **0**. No new tracked script or test filename
carries a live spec-family token — the only `art` substrings are the existing
`scripts/refresh-release-artifacts.py`, and the new test is
`tests/speckit-pro/unit/test-autopilot-stage-resolution.py`. Round 2 tiebreak
outcomes are honoured: the resolver is a registered runner operation beside
`resolve-confidence-mode` (plan.md:17, plan.md:191) with the guard permitted to
import it as a library (plan.md:415), and the argument-parity assertion is sited
in the unit test rather than the structural parity validator (plan.md:362-364).

**Scope budget and split decision (required to proceed on a `warn` posture).**
Projected 430 reviewable LOC against 400 warn / 800 block, and 17 files against
15 warn / 25 block — warn on two dimensions, block on none. **One slice, no
split.** The 48-LOC growth over the ratified 382 comes from the nine lettered
sub-requirements Clarify added, which *narrow* existing behaviour rather than add
capability, plus three test-registry files the registered-operation contract
forces. Splitting would put argv parsing in one PR and the resolution it feeds in
another — a worse review unit than the whole vertical. Recorded at
plan.md:140-160.

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan` — validates both spec AND plan together. Run multiple times for different domains.

**Best Practice:** Don't guess which domains to check. Analyze the spec first, then generate enriched prompts with spec-specific focus areas.

### Step 1: Analyze Spec for Recommended Domains

Before running any checklists, read `spec.md` and `plan.md` and identify which domains apply. Look for these signals:

| Signal in Your Spec/Plan | Recommended Domain |
|---|---|
| API endpoints, REST routes, request/response models | **api-contracts** |
| User-facing UI, components, forms, layouts | **ux** |
| Keyboard navigation, screen readers, WCAG, ARIA | **accessibility** |
| Auth, tokens, secrets, input validation, user roles | **security** |
| Response time budgets, caching, query performance | **performance** |
| Database schemas, migrations, data validation | **data-integrity** |
| LLM prompts, model calls, embeddings, token limits | **llm-integration** |
| SSE, WebSocket, streaming, real-time events | **streaming-protocol** |
| Error handling, retries, fallbacks, degradation | **error-handling** |
| State lifecycle, sessions, caching, persistence | **state-management** |

**Target: 2-4 domains.** Prioritize domains where the spec has the most complexity or risk.

<!-- After analyzing, fill in the recommended domains and enriched prompts below -->

### Step 2: Run Enriched Checklist Prompts

For each domain, include spec-specific focus areas in the prompt — not just the bare domain name.

Recommended domains, from the spec's own signals: this spec is entirely about
state lifecycle across a resumable boundary, error/degradation behaviour on
conflicting or missing inputs, and a contract two platforms must satisfy
identically.

#### 1. state-management Checklist

Why this domain: the whole spec is durable state that must survive a session
boundary, a worktree change, and an archive sweep. The store it builds on has
already failed twice in this repository.

```text
/speckit-checklist state-management

Focus on Autopilot Staging requirements:
- Stage state is written where it survives a fresh session, a different
  worktree, and the archive sweep that deletes specs/<id>/
- The workflow file is the per-spec store; autopilot-state.json is a
  current-in-flight pointer and must not be read as per-spec history
- Every state write reaches git -- per-phase staging plus the plan-stage
  terminal commit -- rather than living in the working tree
- Resume reconstructs everything a --stage implement run needs, including
  session-scoped CONFIDENCE_GATE_MODE and the G0 baseline G7 compares against
- Pay special attention to: the case where two specs are in flight at once,
  which is how ART-001's record was silently overwritten by a different spec
```

#### 2. error-handling Checklist

Why this domain: stage resolution is a decision made from possibly-conflicting
inputs, and the failure mode is silent -- resolving the wrong stage re-runs
finished work or skips unfinished work without any error.

```text
/speckit-checklist error-handling

Focus on Autopilot Staging requirements:
- Conflicting flags (--stage plan with --from-phase implement, repeated
  --stage) fail fast at pre-flight rather than clamping silently
- A status table that disagrees with itself produces a logged, visible outcome
  rather than a silently-wrong stage
- The Stop-hook enforcement path is fail-open at runtime and never strands an
  operator in a continuation loop; Claude has no stop_hook_active field, so the
  re-entry guard must be explicit
- Missing or unreadable stage state degrades to a defined answer, not a crash
- Pay special attention to: whether any failure mode can silently resolve
  `plan` on finished work, which is the flagship failure this spec must prevent
```

#### 3. api-contracts Checklist

Why this domain: `--stage` is a public invocation contract consumed by six
downstream specs and mirrored across two platforms whose argv contracts have
already silently diverged.

```text
/speckit-checklist api-contracts

Focus on Autopilot Staging requirements:
- The argv surface is specified identically for both distributions, including
  flag names, values, precedence against --from-phase, and error text
- The stage vocabulary is closed and stated once, not restated per platform
- The scaffold -> autopilot chain contract is precise enough for ART-011 to
  build against, and stays documentation-only per roadmap :454 and :459-460
- The out-of-stage task marker uses `skipped:`, which the Codex pre-final audit
  at codex-skills/speckit-autopilot/SKILL.md:986-992 already tolerates
- Pay special attention to: anything specified only in prose, since nothing in
  CI diffs the two SKILL.md variants and prose cannot be golden-fixtured
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| state-management | | | |
| error-handling | | | |
| api-contracts | | | |
| **Total** | | | |

### Addressing Gaps

When checklist identifies `[Gap]` items:

1. Review the gap — is it a genuine missing requirement?
2. Update `spec.md` or `plan.md` to address it
3. Re-run the checklist to verify coverage
4. If the gap is intentionally out of scope, document why

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output: `specs/art-006-autopilot-staging/tasks.md`

### Tasks Prompt

```text
/speckit-tasks

## Task Structure
- Small, testable chunks (1-2 hours each)
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: foundation → components → integration → validation
- Mark parallel-safe tasks explicitly with [P]
- Organize by user story, not by technical layer

## Implementation Phases
1. Foundation — shared stage-resolution logic and its golden fixtures
2. US1 Explicit staging — argv, bounded loop, plan-stage terminal commit
3. US2 Resume into implementation — durable state read back on a fresh session
4. US3 Bare invocation — auto-detect from the status table
5. Polish — Codex mirrors, parity notes, generated-artifact regeneration

## Constraints
- Read the design concept's "Non-goals" and "Decisions settled by evidence"
  before generating tasks. Flag any task that crosses a Non-goal; do not
  generate tasks that re-open a settled decision.
- No tracked script or test filename may embed a live spec ID
  (tests/speckit-pro/unit/test-unit-layout.py:273-294) and `art` is a live
  family. Use test-autopilot-stage-resolution.py with a matching fixtures
  directory whose fixture_id matches the directory name.
- Register the new test in tests/speckit-pro/suite-manifest.json. The manifest
  is the only dispatch roster; an unregistered file silently never runs.
- Every edit to either SKILL.md requires a generated-artifact regeneration task
  covering the 84 mirrors, plus a separate docs-reference regeneration task --
  refresh-release-artifacts.py does not regenerate docs-site reference pages.
- Adding any Codex-checked string requires all three steps as one task: edit the
  Codex SKILL.md, add the assertion to validate-codex-skills.py, and update
  tests/speckit-pro/layer1-structural/CODEX-PARITY-NOTES.md.
- Layer 2 trigger evals are default:false and live_only:true, so CI will not run
  them. If the autopilot description changes, the re-run is a named manual task.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | |
| **Phases** | |
| **Parallel Opportunities** | |
| **User Stories Covered** | |

---

## Atomicity Route

**When this is filled:** After the Tasks phase / gate G5, the autopilot SKILL runs
the read-only atomicity classifier and records its decision here. This is a
**placeholder** until then — leave the cells blank during scoping. The classifier
emits one machine-readable decision; the SKILL is what writes it into this section
(the script never writes a file of its own). This route is recorded only here in the
workflow file — never in the spec map. It is read downstream by the layer-planner and
multi-PR emission work that builds on top of it; recording it now wires no PR creation
or branch splitting on its own.

The decision answers "can this change be split into multiple small PRs safely?" by
inspecting the change's structural seams (independent additive capabilities), not its
line count. Surface the four fields the SKILL extracts from the emitted decision:

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | | `true`, or `false` for a destructive-migration or concurrency-sensitive change (a passing CI run does not prove such a change is safe to release). |
| **Signals** | | The decisive detector findings behind the route and releasability reading (may be empty when the classifier abstains). |
| **Warnings** | | Any release-safety warning attached to the change (empty when there is no releasability risk). |

To produce the decision, run the classifier against the feature directory:

```text
runner helper atomicity-route specs/art-006-autopilot-staging
```

See the classifier script at
[`speckit-autopilot/scripts/atomicity-route`](../../speckit-autopilot/scripts/atomicity-route).

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```text
/speckit-analyze

Focus on:
1. Constitution alignment — verify coding standards compliance
2. Coverage gaps — ensure all FRs and user stories have tasks
3. Consistency between task file paths and actual project structure
4. Verify P1 user stories have complete task coverage
5. Cross-artifact drift against docs/ai/specs/.process/ART-006-design-concept.md.
   The design concept is the source of truth for every scoping decision made
   during grill-me. If spec.md, plan.md, or tasks.md contradicts its Goals,
   Non-goals, or Q&A log, the downstream artifact is wrong unless it carries an
   explicit revision note. Check specifically that: the gh limb is still
   deferred to ART-007; G6.5 is still owned by the plan stage; the out-of-stage
   marker is still `skipped:`; both distributions are still in scope; and no
   task re-opens anything under "Decisions settled by evidence"
6. Parity drift — any requirement satisfied on one distribution but not the
   other, given that no CI check diffs the two SKILL.md variants
```

### Analyze Severity Levels

| Severity | Meaning | Action Required |
|----------|---------|-----------------|
| `CRITICAL` | Blocks implementation, violates constitution | **Must fix before G6 gate** |
| `HIGH` | Significant gap, impacts quality | Should fix |
| `MEDIUM` | Improvement opportunity | Review and decide |
| `LOW` | Minor inconsistency | Note for future |

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| | | | |

---

## Phase 6.5: Confidence Gate

**When to run:** After Phase 6 commits and before Phase 7 begins. Gate semantics
are unchanged; this section records the verdict so a later session can read it.

For ART-006 this gate is also the **plan stage's terminal step** — the stage
boundary is a real commit, so a fresh `--stage implement` session reconstructs
context by reading this section and the `Stage` row in Specification Context.

| Field | Value |
|-------|-------|
| Mode | <!-- advisory (default) or strict --> |
| Composite confidence | <!-- 0.00-1.00 --> |
| Verdict | <!-- proceed / remediate / stop --> |
| Evidence | <!-- what the score was computed from --> |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed (no coverage gaps).

### Implement Prompt

```text
/speckit-implement

## Approach: TDD-First

For each task, follow this cycle:

1. **RED**: Write failing test defining expected behavior
2. **GREEN**: Implement minimum code to make test pass
3. **REFACTOR**: Clean up while tests still pass
4. **VERIFY**: Manual verification of acceptance criteria

### Pre-Implementation Setup

Before starting any task:
1. Confirm the bookkeeping-durability prerequisite PR has merged. ART-006's
   durable stage state is not durable without it.
2. Verify the suite is green from the worktree: `python3 tests/speckit-pro/run-all.py`
3. Read the design concept's Q&A log for the "why" behind each decision — it
   informs test specifications and edge-case handling. Any decision recorded
   there but absent from tasks.md is a gap to surface before coding, not to
   silently drop.
4. docs-site is already bootstrapped in this worktree
   (`pnpm --dir docs-site install --frozen-lockfile`, Node v22.22.2).
3. Create a clean branch or verify you're on the right one

### Implementation Notes
<!-- Add project-specific implementation guidance -->
<!-- e.g., naming conventions, patterns to follow, tools to use -->
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Foundation | | | |
| 2 - User Story 1 | | | |
| 3 - User Story 2 | | | |
| 4 - Polish | | | |

---

## Post-Implementation Checklist

The canonical closeout. Every row must reach Complete or an explicit
`Skipped` before the run may report completion.

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

<!-- Populate with your project's quality gates from the constitution -->

- [ ] All tasks marked complete in tasks.md
- [ ] Linting passes: <!-- e.g., `scripts/lint` -->
- [ ] Tests pass: <!-- e.g., `pytest` -->
- [ ] Build succeeds: <!-- e.g., `npm run build` -->
- [ ] Manual verification complete
- [ ] PR created and reviewed
- [ ] Merged to main branch

---

## Lessons Learned

### What Worked Well

-

### Challenges Encountered

-

### Patterns to Reuse

-

---

## Project Structure Reference

<!-- Populate with your project's directory structure for quick reference during implementation -->

```
project/
├── src/                    # Source code
├── tests/                  # Test files
├── docs/                   # Documentation
└── specs/                  # SpecKit specifications
```

---

Template based on SpecKit best practices. Populate the prompts above with your project-specific tech stack, domains, and constraints.
