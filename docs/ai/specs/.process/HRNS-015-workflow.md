# SpecKit Workflow: HRNS-015 — Autopilot, Gate, and PR-Emission Repair

**Template Version**: 1.0.0
**Created**: 2026-09-24
**Purpose**: Reusable template for executing SpecKit workflows. Copy-paste the prompts below into your AI coding agent.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/HRNS-015-design-concept.md
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
| Specify | `/speckit-specify` | ✅ Complete | Current scoped baseline: 14 stories, 26 active FRs, 37 scenarios; historical removals preserved |
| Clarify | `/speckit-clarify` | ✅ Complete | Four sessions complete; ten consensus decisions recorded; G2 passed with zero markers |
| Plan | `/speckit-plan` | ✅ Complete | 2.37.1 re-plan: six artifacts reconciled, 18 increments preserved, G3 pass, advisory projected LOC 200 |
| Checklist | `/speckit-checklist` | ✅ Complete | API 24, error handling 21, state management 22; zero gaps; G4 passed |
| Tasks | `/speckit-tasks` | ✅ Complete | 31 unchecked tasks, 17 groups, current metadata, G5 pass; 18 pending-only v1 markers validated |
| Analyze | `/speckit-analyze` | ✅ Complete | All current findings resolved; 26 active FRs covered; G6 passed; final confidence synthesis 0.95 |
| Confidence Gate | G6.5 | ✅ Complete | Current autonomy ready; bounded re-plan advisory PASS, computed 0.94 ≥ 0.90, no deductions |
| Implement | `/speckit-implement` | 🔄 In Progress | T001–T004 and A1a marker checkpoint complete; A1b/T005 next; exact PR emission diff/LOC pending |
| Post | Post-Implementation | ⏳ Pending | Outside --stage plan; canonical 13-item closeout remains for implementation |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⏭️ Skipped | ⚠️ Blocked

G6.5 completed in default advisory mode. Its warning is recorded in [Phase 6.5](#phase-65-confidence-gate); this plan-only handoff does not approve implementation.

### Phase Gates

Use `references/gate-validation.md` from the installed `speckit-autopilot` skill as the authority for active criteria and escalation behavior.

| Gate | Checkpoint |
|------|------------|
| G1 | After Specify |
| G2 | After Clarify |
| G3 | After Plan |
| G4 | After Checklist |
| G5 | After Tasks |
| G6 | After Analyze |
| G6.5 | Before Implement |
| G7 | After Each Implementation Phase |

### Scaffold Record (2026-09-24)

| Item | Value |
|------|-------|
| Reviewability setup gate (raw) | `status: warn`, `blockers: []`, `reviewable_loc: 245`, `production_files: 3`, `total_files: 12`, `primary_surfaces: [UI, docs/process, harness/adapter, scheduler/runtime]`, warning `primary surfaces 4 exceeds warn threshold 1` |
| Why the raw gate differs from this spec | Setup mode reads the **last** roadmap entry (HRNS-038's 245/3/12) and unions every entry's surfaces. That is #637, which this spec fixes. HRNS-015's own roadmap budget was 292 LOC / 9 production / 20 total |
| Budget re-estimate (grill Q11) | `estimate-spec-size`: whole 1,362 LOC, 4 suggested slices. Slice A 282, B 410, C1 335, C2 415 (C1 + C2 replace C at 750 LOC and about 30 files) |
| Split decision | Accepted: four slices A, B, C1, C2, stack order A → B → C1 → C2, each at most 4 production files and under 25 total files (grill Q6, Q11) |
| Blind-spot pass | did not run — wait deadline expired. The analyst returned 11 findings after 18.1 minutes; they grounded the interview (design concept Q&A) |
| Bootstrap | `pnpm --dir docs-site install --frozen-lockfile` (operator-approved); merge driver already configured |

### Own-Run Hazard

This run executes from the **installed** speckit-pro plugin, which still has
every defect this spec fixes. Expect, and do not stop on:

- The final PR bodies carry no `release-note` fence. Add each slice PR's fence
  by hand with `gh pr edit` until Slice A ships in a release.
- The installed Post list has 11 rows. Use it for this run; the 13-row list is
  a deliverable, not this run's checklist.
- The installed gap counter misses `[Coverage, Gap]` forms and counts quoted
  markers. When a checklist or spec describes a marker, quote it in prose
  ("the Gap marker") or verify G4 manually, and record the workaround.
- The installed setup gate reads the last roadmap entry; record raw output as above.
- `test-privacy-scan` fails 1 of 11 in this worktree. `dynamic_local_pattern`
  (`tests/speckit-pro/unit/test-privacy-scan.py:195`) turns every word of
  `str(REPO_ROOT)` into a local identity term, and this worktree's directory
  name contains "autopilot" and "emission", so every tracked use of those words
  is flagged. It passes on CI's neutral checkout path. Confirm the rest of the
  suite is green, treat this one failure as environmental, and prove the scan on
  CI; do not edit files to avoid the words.
- Every `generate-spec-index-write` apply rewrites
  `specs/formal-001-selective-formal-methods/SPEC-MOC.md`, because `main` is
  stale on it (its backlinks miss three tracked files). The regeneration is
  correct and Slice B owns it: commit it once when it first appears, then stop
  restoring it.

---

## Prerequisites

### Constitution Validation

**Before starting any workflow phase**, verify alignment with the project constitution (`.specify/memory/constitution.md`):

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| I. Plugin Structure Compliance | Agent, skill, and template edits keep valid frontmatter and layout on both hosts | `python3 tests/speckit-pro/run-all.py --layer 1` |
| II. Cross-Platform Runtime & Script Safety | Runner, guard, and refresh-script changes stay Python 3.11+ stdlib, `shell=False`, no Bash or `jq` | `python3 tests/speckit-pro/run-all.py --layer 4` (Bash-confinement and active-path guards) |
| III. Semantic Versioning | No manual version edits; release-please owns versions | Layer 1 semantic-version check |
| IV. Test Coverage Before Merge | Every changed helper, gate, and script lands with Layer 4 unit coverage and a failing-first fixture | `python3 tests/speckit-pro/run-all.py` (Layers 1, 4, 5, zero failures) |
| V. Conventional Commits | Each slice PR title is `<type>(speckit-pro): <plain English>` | `validate-pr-title` gate |
| VI. KISS, Simplicity & YAGNI | Reuse `POST_STEPS`, `inputs.body`-adjacent rendering, tested fixture envelopes; no new abstraction without a second caller | Plan and code review |

**Constitution Check:** ✅ G1 verified the specification and its 16/16 requirements checklist items. Implementation-specific checks remain pending. G0 retains the documented worktree-path privacy-scan exception; CI proof is pending.

### Quality Gates

Filled from `detect-commands` at Step 0.11. One row per slot; the operator answer column holds the one-time missing-tool decision (`install`, `skip (spec)`, `skip (repo)`, or `unanswered`) and is the record that stops the question from firing again. A `skip (repo)` answer is durable only once the operator adds it to `.specify/quality-gates.json` `skips`.

**Detected-command caveat (grill Q9):** for this repository `detect-commands`
reports `FULL_VERIFY: mypy . && ruff check && python3 tests/speckit-pro/run-all.py`.
AGENTS.md runs ruff and mypy only through `scripts/run-python-lint.py` in a
virtual environment, with mypy limited to the `mypy.ini` allowlist. Use the
AGENTS.md Commands table as the effective PROJECT_COMMANDS and record the
override source.

**Thresholds file:** `.specify/quality-gates.json` present and valid: complexity 15, CRAP 30, mutation floor 60; basis `percentile-90`, 1,858 measured functions (2026-09-25).

**G0 verification:** pinned Ruff passed; pinned mypy passed on 47 source files. The full quick suite passed 8,908/8,912 with a temporary `.venv` under this worktree; after removing that environment, the focused privacy scan passed 10/11. Its sole remaining failure is the path-sensitive `dynamic_local_pattern` case documented in Own-Run Hazard. CI proof remains pending; no complete green suite is claimed.

**Hardener:** not run (MUTATION is unconfigured).

| Slot | Status | Tool | Command | Operator answer | G0 baseline | Final |
|------|--------|------|---------|-----------------|-------------|-------|
| COMPLEXITY | unconfigured | N/A | N/A | n/a: no configured signal | n/a: no command discovered | n/a |
| MUTATION | unconfigured | N/A | N/A | n/a: no configured signal | n/a: runs only on a populated spec diff | n/a |
| DEPENDENCY_RULES | unconfigured | N/A | N/A | n/a: no configured signal | n/a: no command discovered | n/a |
| DEPENDENCY_AUDIT | off | N/A | N/A | n/a: not opted in | off: not opted in | n/a |

---

## Formal Methods

Decided during scaffold (design concept, Verification Gates): no formal model.

```json
{
  "schema_version": "1.0",
  "status": "none",
  "rationale": "HRNS-015 repairs deterministic parsers, guards, and skill prose. Failing-first fixtures are the acceptance contract, and no concurrent or stateful protocol in scope justifies a model.",
  "models": []
}
```

## Formal Checkpoints

<!-- Independent of app-language slots, confidence flags, and skip-and-log.
An explicit operator waiver is recorded separately and is never a passing check. -->

| Checkpoint | Status | Evidence or setup gap |
|---|---|---|
| Plan model authoring and G3 | disabled | No selected model |
| Planning reconciliation | disabled | No selected model |
| Final model and optional trace checks | disabled | No selected model |
| Post integration | disabled | No selected model |

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | HRNS-015 |
| **Name** | Autopilot, Gate, and PR-Emission Repair |
| **Branch** | `hrns-015-autopilot-gate-pr-emission-repair` |
| **Stage** | `implement` |
| **Draft PR** | [#685](https://github.com/racecraft-lab/racecraft-plugins-public/pull/685) — refreshed after bounded 2.38.0 Tasks re-plan; native draft packet passed; four current artifacts; architecture-viewer template absent; previews unqualified (0/4 verified); implementation0/31 |
| **Dependencies** | None |
| **Enables** | HRNS-016 (needs Slice A's packet release-note and untracked-packet repairs) |
| **Priority** | P1 |

### Success Criteria Summary

From PRD §3.16 (AC-16.1 to AC-16.10) as amended by the design concept:

- [ ] A final packet emitted with `release_note` passes `compose-release-notes.py --validate-pr` for a `feat` title (AC-16.1; Q3)
- [ ] `validate-pr-packet-write` apply succeeds when only this packet's canonical files are untracked, and blocks on any other change (AC-16.3; Q7)
- [ ] The G6.5 verdict appears in the final PR body
- [ ] The gap counter counts every Gap-token tag form and ignores code spans and fences, with fixtures (AC-16.5 widened; Q4, Q5)
- [ ] The spec-index walk excludes untracked files; `refresh-release-artifacts.py --check` fails on spec-index drift; formal-001 is regenerated (AC-16.6; Q10)
- [ ] Setup mode checks per-slice budgets and applies the greenfield allowance to LOC only (AC-16.9; Q6). `inputs.spec_id` scoping, fail-closed fields, and the pragma shipped on `main` in #694 (rescope 2026-09-26)
- [ ] `estimate-spec-size` accepts a required-refactor signal (AC-16.8)
- [ ] `detect-commands` honors a declared `commands` block in `.specify/quality-gates.json` (AC-16.8; Q9)
- [ ] One 13-item Post list on both hosts, sourced from `POST_STEPS`, and a completion-boundary check refuses pending rows on both hosts (AC-16.2; Q1)
- [ ] Every team-capable executor on both hosts carries a teardown obligation, proven by a structural test (AC-16.4)
- [ ] `speckit-resolve-pr` paginates threads and comments and replies/resolves only after verify, push, and a confirmed pushed SHA, on both hosts (AC-16.7)
- [ ] The blind-spot pass has no fixed deadline and fails open only on dispatch error, empty return, or operator abandonment (AC-16.8 amended; Q2)
- [ ] Tested request envelopes at the live-failure sites; the full sweep moves to HRNS-019 (AC-16.10 narrowed; Q8)
- [ ] Updates to existing roadmaps keep verified legacy workflow links and repair broken ones (AC-16.9). The template and README `.process/` links shipped on `main` in #698 (rescope 2026-09-26)

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/hrns-015-autopilot-gate-pr-emission-repair/spec.md`

### Specify Prompt

```text
/speckit-specify Repair the SpecKit Pro defects observed in live autopilot and scaffold runs so the documented happy path stops producing a failing pull request or a silently wrong artifact, on both Claude Code and Codex, shipped as four review slices (PR emission; gates and counters; autopilot Post list and team teardown; resolve-pr, scaffold, request envelopes, and template links), each with failing-first fixtures.
```

#### Detailed Prompt (for complex specs)

```text
/speckit-specify

## Feature: Autopilot, Gate, and PR-Emission Repair

Source: docs/ai/specs/harness-engineering-uplift-technical-roadmap.md § HRNS-015,
PRD docs/prd-harness-engineering-uplift.md §3.16, and the design concept at
docs/ai/specs/.process/HRNS-015-design-concept.md (read it first; it is the
source of truth for every decision below).

### Problem Statement
Live autopilot runs produce final pull requests that fail this repository's
release-note check, block on their own untracked packet files, undercount
checklist gaps, pass reviewability budgets they should not, detect the wrong
test command, finish with Post steps still pending, leave agent teammates
running after the parent returns, resolve review threads before the fix is
verified and pushed, and discard a blind-spot analysis that took longer than
five minutes. In the scaffold that produced this workflow, the blind-spot
analyst returned 11 findings after 18.1 minutes and the pass was recorded as
"did not run"; the reviewability gate reported the last roadmap entry's budget
instead of this spec's.

### Users
Operators who run /speckit-pro:speckit-scaffold-spec, /speckit-pro:speckit-autopilot,
and /speckit-pro:speckit-resolve-pr on Claude Code or Codex, in this repository
or any host repository, and the reviewers of the pull requests those runs open.

### User Stories (grouped by slice; each slice is one reviewable PR)
Slice A, PR emission:
- As an operator, a final packet built with a release note produces a body that
  passes the host's release-note gate (optional `release_note` field rendered as
  a "## Release note" section with one release-note fence inside editable
  markers). (grill Q3)
- As an operator in a host that does not ignore packets, validating the packet
  succeeds when the only untracked files are that packet's canonical files
  (<id>.json, <id>/body.md, <id>/validation.json); any other change still
  blocks. The same exemption covers refreshing that packet. (grill Q7)
- As a reviewer, the final PR body shows the recorded G6.5 confidence verdict.
Slice B, gates and counters:
- As an operator, G4 counts every bracket tag whose comma-separated tokens
  include Gap, and ignores markers inside inline code spans and fenced blocks.
  (grill Q4, Q5)
- As a contributor, a stale spec index fails the required artifact-consistency
  check; the refresh script regenerates it; untracked files never become
  backlinks or home-index entries. (grill Q10)
- As an operator, setup mode checks only the named spec's roadmap entry, fails
  closed on a missing section or budget field, honors a typed exception
  pragma, and accepts an over-budget total only when every declared slice
  budget is under the block line. (grill Q6)
- As an operator, spec-size estimation accounts for required refactors.
- As an operator, a host's declared quality-gate commands override detected
  defaults. (grill Q9)
Slice C1, autopilot Post list and team teardown:
- As an operator on either host, autopilot tracks one 13-item Post list and
  refuses to report completion while any Post row is pending, in progress, or
  missing. (grill Q1)
- As an operator, every executor that can form a team tears it down before it
  returns.
Slice C2, resolve-pr, scaffold, envelopes, templates:
- As a PR author, resolve-pr reads every thread and comment page, and replies
  and resolves only after full verification, a push, and a confirmed pushed SHA.
- As an operator, the scaffold blind-spot pass waits for the analyst and fails
  open only on a dispatch error, an empty return, or my choice to abandon it,
  each recorded with its own reason. (grill Q2)
- As an operator, the skills that failed live show a complete, tested request
  envelope for each runner helper they tell me to call. (grill Q8)
- As an operator, roadmaps generated from the template link workflow files
  where scaffold writes them.

### Constraints
- Both hosts in the same PR for every behavior change (Claude skills/agents and
  Codex codex-skills/codex-agents).
- Each slice at most 4 production files and under 25 total files.
- Python 3.11+ standard library only; no Bash or jq.
- Generated outputs (dist/, reference pages, spec index) are regenerated, never
  hand-edited.
- Tests never read a specs/<feature>/ path at run time; freeze fixture prose
  under the test's own fixtures/ tree (the pre-fix ART-007 SPEC-MOC.md comes
  from git history at b12f1bba1^).
- Templates must not gain a literal Reviewability-Exception example
  (validate-spec-lifecycle-contracts.py forbids it).
- The PRD (AC-16.2, AC-16.5, AC-16.8, AC-16.10), the HRNS-015 roadmap entry
  (budget, slices, stale #642 line), and the HRNS-019 entry are amended to match
  the design concept in Slice A.

### Out of Scope
- Redesigning the packet schema beyond one optional field, or the
  post-implementation sequence beyond unifying it at 13 rows.
- Changing any host's release-note policy; defaulting to the release-note/skip
  label; a fence in draft PR bodies.
- The remaining 58 bare helper call sites and self-describing runner errors
  (HRNS-019).
- Parsing AGENTS.md or CLAUDE.md tables in the runner.
- A new Reviewability-Exception class.
- Writing ignore rules into host repositories.
- Removing Agent or SendMessage from the open executors.
- Autopilot wall-clock budgets (already removed by #642).
```

### Specify Results

<!-- Fill in after running the command -->

| Metric | Value |
|--------|-------|
| Functional Requirements | 29 (FR-001 through FR-029 after Clarify) |
| User Stories | 14 |
| Acceptance Criteria | 40 scenarios after Clarify |

### Files Generated

- [x] `specs/hrns-015-autopilot-gate-pr-emission-repair/spec.md`

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

Session focuses come from the design concept's Open Questions and the four
slices' main surfaces.

#### Session 1: Gap Counting and Estimation Focus

```text
/speckit-clarify Focus on Slice B counting and estimation: the exact Gap-token grammar (case, whitespace, token separators, nested brackets); where the code-span and fence skip lives and whether [NEEDS CLARIFICATION] counting shares it (design concept Open Question 1); the shape and weight of the required-refactor signal in estimate-spec-size, calibrated against the 292-to-1,362 LOC drift in grill Q11 (Open Question 2).
```

#### Session 2: Reviewability Gate and Spec Index Focus

```text
/speckit-clarify Focus on Slice B gates: how setup mode locates the entry for inputs.spec_id (heading forms such as "### HRNS-015:"); the fail-closed diagnostic for a missing section or budget field; the slice-budget syntax in roadmap entries and the template without a literal pragma example (Open Question 3); how refresh-release-artifacts.py orders the spec-index step and what --check reports; which spec-index paths count as untracked.
```

#### Session 3: PR Emission Focus

```text
/speckit-clarify Focus on Slice A: where the "## Release note" section sits relative to the eight required headings and the UAT Runbook heading; how the editable markers and protected fingerprint treat it; exactly which paths the dirty-worktree exemption covers for validate-pr-packet-write and pr-packet-output; where the G6.5 verdict renders (Open Question 8); which prose replaces "commit the packet" in post-implementation on both hosts.
```

#### Session 4: Workflow Behavior Focus

```text
/speckit-clarify Focus on Slices C1 and C2: when and how the completion-boundary Post check runs on each host and what it reads; the teardown clause wording and whether Codex spawn_agent children can outlive the parent (Open Question 6); how resolve-pr confirms the pushed SHA and paginates threads and comments on each host; how the blind-spot pass records operator abandonment versus dispatch error versus empty return; which live-failure call sites get inline envelopes (grill Q8 list).
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Gap counting and estimation | 4 | Exact case-sensitive `Gap` token grammar; each tag counted across G4 and `count-markers`; code examples excluded for gap and clarification markers; refactor input shape and weight deferred to Plan |
| 2 | Reviewability gate and spec index | 5 | Exact case-sensitive `### <spec_id>:` section; missing fields block with diagnostics; ordered `Slices:` plus budget table selected in Round 2; refresh/check and source-index membership defined; Plan must reconcile 1,362 versus 1,442 LOC |
| 3 | PR emission | 5 | Release note after required headings in fourth editable field; exact current-packet untracked exemption; both-host Post prose updated in plan; G6.5 Phase 6.5 `Verdict` field selected by Round 2 for protected Verification line |
| 4 | Workflow behavior | 5 | Shared 13-row persisted completion check; explicit executor child/team teardown; complete thread/comment pagination and exact pushed-head confirmation; Design Concept blind-spot reasons; named inline envelope sites |

G2 passed: the runner reported zero clarification markers; the spec has no human-review marker and documents the four sessions’ decisions.

### Consensus Resolution Log

| # | Type | Question/Gap/Finding | Categories | Round | Outcome | Resolution | Analysts Used |
|---|------|----------------------|------------|-------|---------|------------|---------------|
| 1 | Clarify | Gap token grammar | [spec] | 1 | high-confidence | Added exact token, case, whitespace, and bracket boundaries to spec | spec-context-analyst |
| 2 | Clarify | Clarification marker code exclusion | [codebase, spec] | 1 | both-agree | Added shared code-visibility rule for counts and details | codebase-analyst, spec-context-analyst |
| 3 | Clarify | Required-refactor signal weight | [codebase, spec] | 1 | both-agree | Confirmed required signal and left input shape and weight to Plan; Q11 does not calibrate weight | codebase-analyst, spec-context-analyst |
| 4 | Clarify | Named roadmap section grammar | [codebase, spec] | 1 | both-agree | Added complete case-sensitive heading and next-entry boundary | codebase-analyst, spec-context-analyst |
| 5 | Clarify | Per-slice budget syntax | [codebase, spec] | 1→2 | 2/3 | Selected ordered ID list and four-column Markdown table; Plan to reconcile values | codebase-analyst, spec-context-analyst, domain-researcher |
| 6 | Clarify | G6.5 verdict source and placement | [spec, codebase] | 1→2 | 2/3 | Phase 6.5 `Verdict` field supplies protected Verification line; absent verdict blocks final emission | codebase-analyst, spec-context-analyst, domain-researcher |
| 7 | Clarify | Persisted 13-row completion boundary | [codebase] | 1 | high-confidence | New shared rule reads workflow and state, requires each Post row exactly once and completed, and runs before success on both hosts | codebase-analyst |
| 8 | Clarify | Team-capable executor teardown | [codebase, domain] | 1 | both-agree | Collect or stop children, confirm team cleanup before clean result; Codex lifetime remains HRNS-017 | codebase-analyst, domain-researcher |
| 9 | Clarify | Resolve-pr feedback and pushed head | [codebase, domain] | 1 | both-agree | Exhaust thread/comment pages; verify, commit, push, compare fresh PR head SHA, then serial reply/resolve | codebase-analyst, domain-researcher |
| 10 | Clarify | Scaffold blind-spot durable reason | [spec] | 1 | high-confidence | Record distinct reason in Design Concept `Blind-spot pass` line and operator status; elapsed time never implies abandonment | spec-context-analyst |
| 11 | Checklist | Per-slice result shape | [codebase] | 1→2 | 3/3 | Ordered `slice_results` rows report slice ID, counts, status, pass, warnings, and blockers; complete row sums populate existing top-level fields, malformed or over-line slices block, and no-split callers keep the existing shape | codebase-analyst, spec-context-analyst, domain-researcher |
| 12 | Checklist | Declared command scope and provenance | [codebase] | 1→2 | 3/3 | Limit declarations to the four existing quality slots, reject malformed declarations, preserve string-valued commands, and add `command_sources` plus quality-gate provenance | codebase-analyst, spec-context-analyst, domain-researcher |
| 13 | Checklist | Legacy 11-row Post resume policy | [codebase, spec] | 1 | both-agree | Preserve only exact-name canonical statuses; missing or renamed rows start pending and never inherit completion from row position or predecessor | codebase-analyst, spec-context-analyst |
| 14 | Checklist | Optional-extension Post skip | [codebase, spec] | 1→2 | 2/3 | Accept only a reason-coded skip for an optional Post extension verified absent in both persisted records; all other skips and incomplete rows block. Spec-context dissented because Q1 did not ratify skip policy | codebase-analyst, spec-context-analyst, domain-researcher |
| 15 | Analyze | H1 C1 path-cap conflict | [codebase, spec] | 1 | owner-ratified revision | C1a/C1b planned paths recorded at 24/22; actual LOC and final diffs remain unqualified | codebase-analyst, spec-context-analyst |
| 16 | Analyze | H2 advisory atomicity route | [codebase, spec, domain] | 1→2 | supported route | Preserve one-navigable-PR advice; derive a current marker plan only after scope and safety validation | codebase-analyst, spec-context-analyst, domain-researcher |
| 17 | Analyze | H3 A path-cap conflict | [codebase, spec, domain] | 1→2 | 3/3; human review needed | At least 31 paths blocks one A PR; provisional boundaries need complete inventory and owner ratification | codebase-analyst, spec-context-analyst, domain-researcher |
| 18 | Analyze | H4 B path-cap conflict | [codebase, spec, domain] | 1→2 | 3/3; human review needed | At least 28 paths blocks one B PR; provisional partitions need complete inventory and owner ratification | codebase-analyst, spec-context-analyst, domain-researcher |
| 19 | Analyze | H5 C2 path-cap conflict | [codebase, spec] | 1 | both-agree; human review needed | At least 30 paths blocks one C2 PR; provisional boundaries need complete inventory and owner ratification | codebase-analyst, spec-context-analyst |
| 20 | Analyze | H8 repeated production paths across ordered PRs | [codebase] | 1→2 | 3/3 | Spec clarifies exact base/head diff counting; issue #675 and PR #676 document the installed validator gap; candidate overlap alone does not prove repeated changed paths | codebase-analyst, spec-context-analyst, domain-researcher |
| 21 | Analyze | Parent workflow/state proposal projection | [spec] | 1→2 | 3/3 | Record 19 increments and 33 tasks as proposed; reconcile Phase 7 rows; retain H3–H7 open and G6 not_run until owner acceptance and qualification | spec-context-analyst, codebase-analyst, domain-researcher |
| 22 | Finding | Existing release-note fence collision | [security] | 1 | 3/3 | Accepted existing-note and unclosed enclosing-fence rejection; preserve headings, closed examples and no-note bodies; exact guarded exception approved; native implementation qualification pending | codebase-analyst, spec-context-analyst, domain-researcher |
| 23 | Finding | Host-visible fence line separators | [security] | 1 | 3/3 | Accepted runtime and schema alignment with splitlines boundaries; preserve harmless separators and inline fences; exact guarded exception approved; native implementation qualification pending | codebase-analyst, spec-context-analyst, domain-researcher |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/hrns-015-autopilot-gate-pr-emission-repair/plan.md`

### Plan Prompt

```text
/speckit-plan

## Tech Stack
- Runner and repository tooling: Python 3.11+ standard library only
  (speckit-pro/speckit_pro_runner/, scripts/, tests/speckit-pro/); no Bash, no jq
- Plugin surfaces: Markdown skills and agents for Claude Code
  (speckit-pro/skills/, speckit-pro/agents/*.md) and Codex
  (speckit-pro/codex-skills/, speckit-pro/codex-agents/*.toml)
- Contracts: runner JSON Schema under speckit-pro/speckit_pro_runner/contracts/; active PR packet schema under speckit-pro/skills/speckit-autopilot/contracts/
- Testing: Layer 1 structural, Layer 4 unit, Layer 5 tool scoping
  (tests/speckit-pro/suite-manifest.json)
- Generated outputs: dist/ via scripts/refresh-release-artifacts.py; docs reference
  pages via pnpm --dir docs-site reference:generate

## Decisions from the design concept (quote, do not reinterpret)
- Q1: "13 on both hosts". POST_STEPS in validate-autopilot-phase-coverage.py is
  the single source; the existing guard runs again at the completion boundary.
- Q2: "Remove it; await the reply". No fixed deadline; fail open only on
  dispatch error, empty return, or operator abandonment, each with its own reason.
- Q3: "Optional release_note field". Rendered as "## Release note" with one
  release-note fence inside editable markers; one optional schema property.
- Q4: "Any tag with a Gap token". Q5: "Skip code spans and fences".
- Q6: "Per-slice budgets". inputs.spec_id, section-scoped, fail closed,
  line-anchored pragma, per-slice budgets.
- Q7: "Exempt this packet's files". Exactly the canonical packet paths.
- Q8: "Failure sites now, rest to HRNS-019".
- Q9: "Declared commands in config". A per-slot commands block in
  .specify/quality-gates.json; source: declared.
- Q10: "Inside refresh-release-artifacts". Plain run regenerates the spec
  index; --check fails on drift; the AGENTS.md special case is removed.
- Q11: "Four slices: A, B, C1, C2". Stack order A → B → C1 → C2.

## Tracked issue acceptance
- #637: Named-entry scoping, the selected-entry pragma, and missing-budget blocking shipped on `main` in #694 (rescope 2026-09-26). Add failing-first fixtures for the greenfield LOC-only allowance and aggregate plus per-slice budget checks.
- #638: The new-template link fix shipped on `main` in #698 (rescope 2026-09-26). Preserve existing legacy links only when their targets exist and repair broken ones; add failing-first fixtures for existing roadmaps.

## Module and Interface Deltas (verbatim from the design concept)
- speckit-pro/speckit_pro_runner/helpers/pr_emission.py: changed. Optional release_note input rendered as a fenced section in editable markers; confidence verdict carried into the body (Q3; evidence: HRNS-025 Pending).
- speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json: changed. One optional release_note property and a fourth final-body editable field under additionalProperties: false (Q3).
- speckit-pro/speckit_pro_runner/helpers/read_only.py: changed. packet_body_structure_failures and the protected fingerprint accept the release-note section; gap-token matching with code-span skipping; spec-index untracked exclusion for backlinks and the home index; reviewability_gate per-entry scoping, fail-closed fields, exact selected-section pragma, greenfield LOC-only allowance, aggregate declared slices; estimate_spec_size refactor signal; detect_commands declared commands (Q3 to Q6, #637, Q9, Q10).
- speckit-pro/speckit_pro_runner/helpers/mutation.py: changed. The dirty-worktree guard exempts exactly the canonical paths of the packet under validation (Q7).
- speckit-pro/speckit_pro_runner/helpers/registry.py: changed if needed. reviewability-gate required args gain spec_id (Q6).
- scripts/refresh-release-artifacts.py: changed. Regenerates the spec index; --check fails on spec-index drift (Q10).
- speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py: changed. POST_STEPS becomes 13 items and the single source; a completion-boundary rule refuses pending, in-progress, or missing Post rows (Q1).
- speckit-pro/speckit_pro_runner/formal/lifecycle.py: reviewed. Its hardcoded Post-name subset (:153) must stay consistent with 13 items (evidence).
- speckit-pro/skills/speckit-autopilot/SKILL.md, references/task-list-canonical.md, references/post-implementation.md, references/gate-validation.md, references/phase-execution.md, references/prerequisites.md, references/agent-teams-integration.md, and the Codex mirrors under speckit-pro/codex-skills/speckit-autopilot/: changed prose (Q1, Q3, Q4, Q7, Q8, Q9).
- speckit-pro/agents/{phase,analyze,checklist,implement}-executor.md and speckit-pro/codex-agents/{phase,analyze,checklist,implement}-executor.toml: changed. Teardown obligation (evidence: PRD AC-16.4).
- speckit-pro/skills/speckit-resolve-pr/SKILL.md and speckit-pro/codex-skills/speckit-resolve-pr/SKILL.md: changed. Pagination; verify, push, confirm SHA, then reply and resolve (evidence).
- speckit-pro/skills/speckit-scaffold-spec/SKILL.md and the Codex mirror: changed. Deadline removed; new fail-open reasons; inline envelopes (Q2, Q8); workflow-link updates preserve verified legacy targets (#638; `inputs.spec_id` already passed on `main` by #694).
- speckit-pro/skills/speckit-status/SKILL.md and the Codex mirror: changed. Inline envelopes for generate-spec-index-check and o5-topology (Q8; late blind-spot findings 8 and 10).
- speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md: changed. The slice-budget syntax (Q6); scaffold preserves existing verified legacy link targets. The `.process/` links already shipped in #698.
- speckit-pro/skills/speckit-coach/templates/workflow-template.md: changed. 13-row Post table (Q1).
- speckit-pro/README.md: unchanged. The workflow path fix shipped on `main` in #698 (rescope 2026-09-26).
- AGENTS.md (root): changed. The spec index joins the refresh command; the "freshness: no PR check" row goes (Q10).
- specs/formal-001-selective-formal-methods/SPEC-MOC.md: regenerated (Q10).
- docs/prd-harness-engineering-uplift.md and docs/ai/specs/harness-engineering-uplift-technical-roadmap.md: changed. AC and entry amendments (Goals, Slice A).
- dist/** and docs-site/src/content/docs/reference/**: regenerated, never hand-edited (evidence: AGENTS.md Editing Boundaries).
- .github/workflows/pr-checks.yml: unchanged. The check rides the existing required artifact-consistency job instead of a new step (Q10; this replaces the roadmap's listed workflow delta).
- The packet schema's other properties, phase-execution draft emission, and multi-pr-emission: unchanged grey boxes (Q3).

## Constraints
- Group the plan by slice (A, B, C1, C2); state each slice's production files,
  total files, and projected LOC against the per-slice budget (at most 4
  production files, under 25 total files).
- Both hosts in the same slice for every behavior change.
- Every behavior change starts with a failing fixture (roadmap Done When).
- Reuse existing mechanisms named in the design concept: POST_STEPS, the tested
  fixture envelopes (validate-spec-lifecycle-contracts.py:578 and
  tests/speckit-pro/unit/fixtures/read-only-helpers/requests/), issue #637's
  repro cases (multi, pragma, nobudget).
- Record the design concept's Open Questions 3 and 8 as plan decisions.

## Architecture Notes
- Design concept: docs/ai/specs/.process/HRNS-015-design-concept.md. Re-read
  its Q&A log whenever a planning choice depends on why a decision was made.
- The installed plugin running this autopilot still has the defects (see Own-Run
  Hazard above); do not rely on the fixed behavior during this run.
```

### Plan Results

Current advisory estimator: pass, projected 200 reviewable LOC from 55 declared entries (5 recognized production files). This coarse file-based signal does not qualify the eighteen candidate increments, generated fan-out, or actual diffs. Optional traceability hook is deferred until Tasks; optional Git hooks are covered by the parent phase checkpoint.

Artifact reconciliation: plan/research/quickstart now distinguish approved scope, candidate delivery, and unavailable evidence; data-model and both contracts retain substantive definitions with scope/baseline updates. Requirements checklist counts are current; API and error checklists reference #694 baseline and add FR-025 coverage; state checklist separates C1a Post behavior from C1b teardown. Custom checkbox states are retained. G3 after checklist reconciliation passed with zero markers. This artifact gate does not ratify the delivery proposal or qualify implementation diffs.

Current 2.37.0 Plan executor result consumed: six design files written and checked; 26 active requirements, 29 historical IDs, 14 stories, 37 scenarios. Candidate unions are A 39, B 36, C1a 29, C1b 29, C2 34 total paths. The eighteen-increment alternative remains unratified; actual diffs and LOC remain unqualified. G3 passed for the reconciled artifact set. Official-source research and independent source audit were unavailable; no such verification is claimed.

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ✅ Complete | Six-artifact 2.37.0 regeneration; approved five groups and unratified eighteen-increment alternative |
| `research.md` | ✅ Complete | Decisions, issue reproductions, and external documentation limitation |
| `data-model.md` | ✅ Complete | Runner, packet, roadmap, and workflow state entities |
| `contracts/` | ✅ Complete | `runner-and-roadmap.md` and `workflow-and-pr.md` |
| `quickstart.md` | ✅ Complete | Failing-first workflow and verification commands |

The earlier Plan gate result is superseded by the explicit 2.37.0 resume; current G3 passed (zero unresolved markers). No formal model is selected. The standalone `estimate-reviewable-loc` helper returned `not_estimated` (`projected: null`, zero parseable declared file operations) because Slice A’s ten named operations are a partial subset of its 16-file projection. The current size helper’s 1,932-LOC/five-slice stress check uses 77 provisional file touches and ignores the required-refactor input; it is not a refactor-inclusive estimate. Tasks must complete distinct file and refactor inventories before claiming any revised slice budget is qualified.

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
| Personal data (PII), consent, retention, deletion | **privacy** |
| New third-party packages or dependency upgrades | **supply-chain** |

**Target: 2-4 domains.** Prioritize domains where the spec has the most complexity or risk.

Recommended from the design tree: **api-contracts**, **error-handling**, **state-management**.

### Step 2: Run Enriched Checklist Prompts

For each domain, include spec-specific focus areas in the prompt — not just the bare domain name.

#### 1. api-contracts Checklist

Why this domain: every slice changes a runner helper's request or response contract (packet schema field, reviewability-gate `spec_id`, estimate-spec-size signal, detect-commands declared source) or the request envelopes skills show.

```text
/speckit-checklist api-contracts

Focus on Autopilot, Gate, and PR-Emission Repair requirements:
- The optional release_note packet property, its schema entry, and the body structure and fingerprint rules
- reviewability-gate inputs (spec_id), outputs (status exception, exception_class, per-slice results), and fail-closed diagnostics
- estimate-spec-size's refactor input and detect-commands' declared-command source field
- Inline request envelopes: each must match a passing fixture byte for byte
- Pay special attention to: backward compatibility for callers that omit the new optional inputs
```

#### 2. error-handling Checklist

Why this domain: the spec changes several fail-closed and fail-open boundaries (dirty-worktree guard, missing budget fields, blind-spot pass outcomes, completion refusal, resolve-pr failure after partial work).

```text
/speckit-checklist error-handling

Focus on Autopilot, Gate, and PR-Emission Repair requirements:
- The dirty-worktree exemption: exactly the canonical packet paths, and every other change still blocks
- Setup gate fail-closed paths: missing section, missing budget field, malformed or mis-cased pragma
- Blind-spot pass: dispatch error, empty return, operator abandonment, each with its own recorded reason
- resolve-pr: what happens when full verification or the push fails after fixes are committed
- Pay special attention to: no path that passes on nothing (a gate never passes vacuously)
```

#### 3. state-management Checklist

Why this domain: the Post list lives in autopilot state and task lists on two hosts, the spec index is a generated state surface, and team lifetime outlived its parent in a live run.

```text
/speckit-checklist state-management

Focus on Autopilot, Gate, and PR-Emission Repair requirements:
- The 13-row Post list in autopilot state, task lists, and the workflow template on both hosts, and resume from a partially completed Post sequence
- Spec-index regeneration inside refresh-release-artifacts.py, including tracked-only selection and the formal-001 baseline
- Team lifetime: teardown before an executor returns, on both hosts
- Pay special attention to: state written by an older plugin version (11 Post rows) being read by the new guard
```

### Checklist Results

Current approved-plan rerun: all three named executors completed requirements review; 67 reviewer-owned checkboxes remain unchecked. The prior pass recorded eleven repaired gaps; the current API pass verified the approved FR-024 correction. Error-handling and state-management found no new gaps.

| Checklist | `/speckit-checklist` | ⏳ Pending | Revalidate after current re-plan |
|-----------|-------|------|-----------------|
| api-contracts | 24 | FR-024 correction verified; 0 remaining | Current contract and specification references in each item |
| error-handling | 21 | 0 new; 0 remaining | Current failure-boundary requirements in each item |
| state-management | 22 | 0 new; 0 remaining | Current migration, index and teardown requirements in each item |
| **Total** | 67 | 0 remaining | All three selected domains; parent G4 passed |

### Addressing Gaps

When checklist identifies `[Gap]` items:

1. Review the gap — is it a genuine missing requirement?
2. Update `spec.md` or `plan.md` to address it
3. Re-run the checklist to verify coverage
4. If the gap is intentionally out of scope, document why

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output: `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md`

### Tasks Prompt

```text
/speckit-tasks

Read spec.md, plan.md, and docs/ai/specs/.process/HRNS-015-design-concept.md.

## Task Structure
- Small, complete behavioral units under the current execution-control contract;
  no wall-clock run limit. Preserve shared corrective counters and checkpoint completed work every 45 minutes.
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: foundation → components → integration → validation
- Mark parallel-safe tasks explicitly with [P]
- Organize by user story, not by technical layer
- Keep related test and implementation checkboxes in one closed TDD unit;
  each unit must fit an adjacent batch of at most four tasks

## Execution Metadata
Produce `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` alongside tasks.md.
Use `schema_version: task-execution.v1`, `fingerprints` from runner helper
`validate-task-execution` (`action: fingerprints`, `tasks_file: <tasks.md>`),
and `tasks` keyed by every task ID. Each entry contains `capability_group`,
`depends_on` (task IDs), `owns` (repo-relative paths including shared fixtures
and generated inputs), and `tdd_unit`. Fingerprints bind spec, plan and task
definitions, excluding checkbox completion. Validate the completed sidecar.
Do not guess fingerprints or omit ownership to force parallel execution.

## Implementation Phases
1. Slice A: PR emission, plus the PRD and roadmap amendments (docs only)
2. Slice B: gates and counters, including the formal-001 regeneration
3. Slice C1: autopilot Post list and team teardown
4. Slice C2: resolve-pr, scaffold deadline, request envelopes, template links
5. Per slice: regenerate dist/ and reference pages, run the quick suite

## Constraints
- Each slice's tasks own at most 4 production files and under 25 total files;
  flag any task that pushes a slice over.
- Every behavior task starts with a failing fixture (RED) before the fix.
- Tests never open a specs/<feature>/ path; freeze fixture prose under the
  test's own fixtures/ tree.
- Flag any task that crosses a design-concept Non-goal: the 58-site envelope
  sweep, self-describing runner errors, parsing agent-doc tables, a new
  exception class, host ignore rules, removing Agent or SendMessage from open
  executors, a draft-PR fence, or packet-schema changes beyond release_note.
- Both hosts in the same task group for every behavior change.
- Test files go under tests/speckit-pro/ (layer1-structural, unit, layer5-tool-scoping);
  never under speckit-pro/.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | 31 |
| **Phases** | 17 user-story-oriented groups; 21 closed units, at most 3 adjacent tasks each |
| **Parallel Opportunities** | None; shared ownership and approved ordering require sequential execution |
| **User Stories Covered** | 14 of 14; 26 active FRs, 37 acceptance scenarios, 11 success criteria |

Approved-plan regeneration removed shipped B2a implementation work and renumbered remaining tasks contiguously. The sidecar binds every current definition and ownership path to native fingerprints. Parent G5 passed with zero markers and 31 tasks; parent validate-task-execution returned status ok and outer/helper exit 0 (detailed stdout truncated). The inventory retains eighteen approved increments. C2b2 now counts 16 candidate paths after six shipped-link exclusions; the upstream conservative 22-before-exclusions number remains explicitly documented.

Tasks-phase reviewability: helper `reviewability-gate`, requested mode `tasks`, is registry-deferred and was not invoked. The fallback evidence is the scaffold setup warn/pass, current Plan estimator pass/projected 200 (advisory whole-Plan estimate), and owner approval of eighteen increments. Candidate counts are not per-PR actual-diff or LOC proof. Atomicity-route freshly returned one-navigable-PR, releasable true, change-shape:modify-heavy, no warnings; the conditional layer planner was skipped.

Post-G5 marker boundary remains pending the explicit owner timing decision documented below. No Analyze or implementation dispatch has occurred in this resume. The current v2 planned-checkpoint requirement is tracked in issue #740; no invented commit or evidence was persisted.

---

## Atomicity Route

**When this is filled:** After the Tasks phase / gate G5, autopilot runs the
read-only `atomicity-route` runner helper and records its decision here. Leave
the cells blank during scoping. The helper writes nothing itself; autopilot
records the route only in this workflow file, never in the spec map, and runs
the layer planner only when the route is `split-PR`.

The decision answers "can this change be split into multiple small PRs safely?" by
inspecting the change's structural seams (independent additive capabilities), not its
line count. Surface the four fields the SKILL extracts from the emitted decision:

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | `one-navigable-PR` | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | `true` | `true`, or `false` for a destructive-migration or concurrency-sensitive change (a passing CI run does not prove such a change is safe to release). |
| **Signals** | `change-shape:modify-heavy` | The decisive detector findings behind the route and releasability reading (may be empty when the classifier abstains). |
| **Warnings** | None | Any release-safety warning attached to the change (empty when there is no releasability risk). |

Original scoping expected `split-PR` and four layers (design concept Q11, Open Question 4). The user subsequently ratified five ordered PR slices, A → B → C1a → C1b → C2, after the C1 budget breach, then directed resolution of further path-cap blockers while preserving scope.

Actual classifier result: `one-navigable-PR` (`change-shape:modify-heavy`), releasable `true`, no warnings. Preserve this advisory result; the layer planner remains skipped because the route is not `split-PR`. Before multi-PR emission, derive and validate a current `pr_marker_plan` from tasks, reviewability, declared scope, and hazard evidence. The marker plan, when validated, supplies PR membership and order. No `split-PR` classifier result or separate-run mode is inferred. Multi-PR emission remains pending a story-compatible allocation with complete path accounting, a current marker plan, and per-slice budget qualification.

To produce the decision, run the classifier against the feature directory:

```text
runner helper atomicity-route specs/hrns-015-autopilot-gate-pr-emission-repair
```


---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```text
/speckit-analyze

Cross-check spec.md, plan.md, tasks.md, AND
docs/ai/specs/.process/HRNS-015-design-concept.md. The design concept is the
source of truth for scoping decisions; a downstream artifact that contradicts
it is wrong unless it carries an explicit revision note.

Focus on:
1. Constitution alignment: Python 3.11+ stdlib, no Bash or jq, Layer 4 coverage
   for every changed helper, conventional commit titles per slice
2. Coverage gaps: every Goal and every roadmap Done When line has an FR and a
   task, including the five bullets the roadmap left without Done When lines
3. Drift from the design concept's Goals, Non-goals, decisions Q1 to Q11,
   Module and Interface Deltas, and Verification Gates
4. Per-slice budgets: at most 4 production files and under 25 total files
5. Both-host parity: every behavior change touches Claude and Codex surfaces
6. Consistency between task file paths and actual project structure
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
| H1 | HIGH | Original C1 requires at least 29 changed paths, above the 24-path maximum. | User ratified C1a/C1b. The current proposal further divides C1 into C1a1/C1a2/C1b1/C1b2 at 24/21/21/21 candidate paths including recurring process paths. Owner acceptance of the changed PR count and actual diff/LOC gates remain outstanding. |
| H2 | HIGH | Advisory one-navigable-PR route differs from the user's multi-PR direction. | Preserve the classifier result. Derive and validate a current pr_marker_plan from tasks, scope, reviewability, and hazard evidence only after a compliant allocation is ratified. |
| H3 | HIGH | Candidate allocation corrected: A1a/A1b/A2/A3 each list 24 candidate paths. Owner acceptance of the changed PR count and exact per-increment diff/LOC qualification remain outstanding. | |
| H4 | HIGH | Candidate allocation corrected: six one-story B increments list 18–23 candidate paths. Owner acceptance of the changed PR count and exact per-increment diff/LOC qualification remain outstanding. | |
| H5 | HIGH | Candidate allocation corrected: five one-story C2 increments list 14–22 candidate paths. Owner acceptance of the changed PR count and exact per-increment diff/LOC qualification remain outstanding. | |
| H6 | HIGH | Planning identity defect corrected: all 19 proposed increments name one story with unique sequential part IDs where needed. A current persisted marker plan remains unvalidated pending product-contract repair and T002 qualification. | |
| H7 | HIGH | Planning inventory omission corrected: six recurring tracked workflow/process/evidence candidates are included in every proposed increment. Exact base/head changed paths, generated outputs, reviewable LOC, and marker fingerprints remain unqualified. | |
| M1 | MEDIUM | Preliminary design-concept size figures were presented as a qualified Plan budget. | Spec and Plan now label them preliminary and retain the refactor-inclusive not_estimated verdict. |
| M2 | MEDIUM | Plan named nonexistent test layer directories. | Corrected the named structural and tool-scoping directories and listed the Tasks sidecar. |
| L1 | LOW | Requirements checklist had stale scenario and FR counts. | Corrected to 40 scenarios and 29 FRs. |
| L2 | LOW | Workflow had a stale acceptance-scenario count. | Corrected both references to 40. |
| L3 | LOW | Plan described Tasks as a later phase after Tasks had completed. | Updated the structure diagram. |

### Final Analyze checkpoint — planning review handoff

> Superseded by "Current Analyze Evidence — 2.37.1" below. Its 19-increment count and `owner_ratification=pending` are historical; the eighteen-increment order is ratified.

The planning proposal contains 19 ordered, one-story increments and 33 tasks covering all 29 requirements and 14 stories. Each candidate inventory lists 14–24 paths, including six recurring tracked workflow/process/evidence candidates. This corrects the original grouped path-cap, mixed-story, and omitted-path planning defects. The proposal changes the previously ratified five-PR count; owner_ratification remains pending.

The owner's instruction to finish the plan stage authorizes completion of the draft planning review handoff. It does not ratify 19 implementation PRs or supply measured delivery evidence. H3–H7 retain outstanding qualification conditions: actual base/head diffs, reviewable LOC, generated outputs, current marker fingerprints, and installed repeated-path validator support. T002 remains open and blocks behavior tasks. The current spec expressly withholds G6 pending that qualification; this projection does not override it. G6 and G6.5 must record their actual deterministic outcomes.

The execution-control bug that had blocked FR-026 was reproduced and filed as issue #673; the source repair is PR #674. This same HRNS-015 ledger was bound once to the 29 approved spec invariants without changing its run identity or earlier dispatch. Its original Tasks corrective cycle remains in the unresolved family. The FR-026 Analyze corrective cycle used reservation 420e70c8bf1b436493f77ef2df90f5d9; the global corrective count is two. The later Analyze worker result was not delivered, so one read-only reconciliation recorded an unknown outcome. A recovered Codex host `task_complete` event then established that the worker turn failed with an authentication error and no final Analyze result. The parent recorded that genuine failure against the original dispatch, clearing the unknown outcome. The next FR-026 corrective reservation was denied with `failure_family_budget_exhausted` and `checkpoint_required`; no worker was launched. The operator then explicitly authorized one retry. Issue #677 and PR #678 record the missing SpecKit Pro recovery path and repair. The guarded `authorize-corrective-retry` action reserved dispatch `hrns015-analyze-auth-recovery-20260926` on the original FR-026 reservation, retained the failed dispatch and two consumed cycles, and returned `continue` on the same run. The retry returned its Analyze result and was completed in that ledger without resetting counters.

The 33-task sidecar validated before the accepted Round 2 spec clarification; a fresh `validate-task-execution` now rejects stale source fingerprints. A same-reservation Tasks-producer dispatch was denied with `corrective_cycle_already_closed`, while the live ledger status still reports `continue` and retains two consumed cycles. Issue #679 records this separate SpecKit Pro orchestration gap; repair PR #680 is ready for required review and adds one operator-approved metadata continuation under the same reservation without resetting counters. Its final local suite passed 8,960/8,960 checks; the CI-equivalent suite passed all six groups; generated-artifact consistency, reference freshness, docs quality, Ruff, and mypy passed. GitHub CI passed on head `98193af799434a0d93bd1bd4747a8a006d5a9f6d`, including the required suite and both Linux container architectures. Copilot reported no findings; required review is still outstanding. The owner subsequently directed completion of the plan stage without stopping. The parent observed that fresh native instruction and used it for exactly one metadata continuation under the original completed Analyze reservation. The guarded action returned continue on the original run with both corrective cycles preserved. The Tasks producer now owns source-bound metadata reconciliation only; task definitions remain unchanged. The metadata producer completed, sidecar validation passed, and G5 returned pass with 33 tasks and zero markers. The dedicated final Analyze synthesis is complete. Actual per-PR diffs, reviewable LOC, and marker fingerprints remain unqualified. The shared-path product gap is issue #675 with repair PR #676; it is not yet in the installed validator. The authorized Tasks metadata continuation completed. It changed only spec_sha256 in task-execution.json, preserving all 33 task entries and spec/plan/tasks bytes. Installed sidecar validation returned valid=true with no errors; G5 returned pass=true with 33 tasks and zero markers. Both consumed corrective cycles remain recorded. PR #680's local and CI evidence qualifies its metadata-continuation repair, not HRNS-015 implementation.

Issue #682 tracks the reproduced G6 false pass. The installed G6 helper returned pass=true, markers=0, reason="0 CRITICAL/HIGH findings" despite the five open HIGH rows above. This mechanical result does not qualify the current spec’s G6 conditions. The parent retains the five findings, pending owner ratification, and T002 gates.

This dedicated final Analyze synthesis completes the planning analysis. The operator's latest direction governs the timing of the plan-only draft handoff while all unqualified requirements remain visible. Retain owner_ratification=pending, T002 qualification outstanding, and Phase 7 skipped outside this stage-plan request. No implementation PR count, marker plan, behavior task, or implementation result is approved by this handoff.

---

### Pre-Implement Confidence

📊 Confidence: 0.93

- Task understanding: 0.94
- Approach clarity: 0.84
- Requirements alignment: 0.97
- Risk assessment: 0.96
- Completeness: 0.94


## Phase 6.5: Confidence Gate

### Autonomy Boundary Preflight

Status: ready. The user approved the exact implementation scope: bounded source/test/docs edits and verification, commits and normal feature/stack pushes, eighteen increment PRs and review replies, public-documentation research, offline local HAL delegation, the existing private record refresh, T011 root agent guidance and inventory-generated runner trust outputs. The current execution boundary and planning fingerprints are preserved. No ledger reset, private-repository export, cloud delegation, deployment, credential change, main push or force push is authorized. Private record digest: `sha256:18a8beac92995f4b37a1cc199e72318e518d8c6d83903009d47c9cb0e2e40285`.

**When to run:** After Phase 6 commits and before Phase 7 begins. Analyze checkpoint: `de3950bd`.

| Field | Value |
| --- | --- |
| Mode | advisory (default; native mode resolver) |
| Composite confidence | 0.95; threshold 0.90 |
| Verdict | PASS — proceed to plan-stage artifact and draft handoff |
| Evidence | Native confidence-gate exit 0, computed from all five current criteria; no open CRITICAL/HIGH deductions; recommended_action=proceed. |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed (no coverage gaps).

### Implement Prompt

```text
/speckit-implement

Read tasks.md, plan.md, and docs/ai/specs/.process/HRNS-015-design-concept.md.
Consult the design concept's Q&A log for the "why" behind each decision when
writing tests, handling edge cases, or refactoring. Surface any design-concept
decision missing from tasks.md as a gap before coding; do not drop it.

## Approach: TDD-First

For each task, follow this cycle:

1. **RED**: Write failing test defining expected behavior
2. **GREEN**: Implement minimum code to make test pass
3. **REFACTOR**: Clean up while tests still pass
4. **VERIFY**: Manual verification of acceptance criteria

### Pre-Implementation Setup

Before starting any task:
1. From the worktree root, run `python3 tests/speckit-pro/run-all.py` and confirm it passes on the unchanged branch
2. Confirm docs-site dependencies are installed (`pnpm --dir docs-site install --frozen-lockfile`, done at scaffold)
3. Confirm the branch is `hrns-015-autopilot-gate-pr-emission-repair`, never main

### Verification Gates (verbatim from the design concept)
- Failing-first fixtures, one per acceptance criterion: release-note fence passes the policy validator; untracked packet exemption (and a non-packet file still blocks); every gap-marker form plus a quoted marker; untracked-file exclusion; refresh --check fails on the pre-fix ART-007 SPEC-MOC.md (from b12f1bba1^) and passes with an untracked file present; #637 (multi, pragma, nobudget, per-slice) and #638; Post-list refusal with a pending row on both hosts; teardown clause on every team-capable executor; resolve-pr pagination and ordering on both hosts; declared commands override detection; inline envelopes at the named sites (roadmap Done When; Q1 to Q10).
- Quick suite: python3 tests/speckit-pro/run-all.py passes (AGENTS.md Commands).
- CI suite: the run-default-suite.json runner request passes (AGENTS.md Commands).
- Generated artifacts: python3 scripts/refresh-release-artifacts.py --check passes, now including the spec index (Q10).
- Docs reference: pnpm --dir docs-site reference:generate, then reference:check and validate:quality, after any test-tree or reference-input change (AGENTS.md Commands).
- Python lint: ruff F rules and the mypy ratchet through scripts/run-python-lint.py (AGENTS.md Commands).
- PR title and release-note fence gates on every slice PR (AGENTS.md Commands).
- Per-slice reviewability budget: at most 4 production files and under 25 total files per slice (Q6, Q11).
- Formal methods: none. The changes are deterministic parsers, guards, and prose; failing-first fixtures are the acceptance contract, and no concurrent or stateful protocol here justifies a model (evidence: roadmap Done When).

### Implementation Notes
- Commit generated outputs with their source: after any runner .py or plugin
  source edit, run python3 scripts/refresh-release-artifacts.py; after test-tree
  or reference-input edits, run pnpm --dir docs-site reference:generate.
- Regenerate the spec index with untracked files moved aside until Slice B
  ships; commit only this spec's index files and formal-001's regenerated map.
- Privacy: no home paths, temp paths, raw UUIDs, or local identity terms in
  committed files (test-privacy-scan.py).
- Files listed in active_path_guard.py must not instruct bash, sh, or jq.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Slice A: PR emission | | | |
| 2 - Slice B: gates and counters | | | |
| 3 - Slice C1: Post list and teardown | | | |
| 4 - Slice C2: resolve-pr, scaffold, envelopes, templates | | | |

---

## Post-Implementation Checklist

The installed 2.38.0 canonical closeout has thirteen distinct Post rows. Every row must reach Complete or an allowed explicit Skipped result before the implementation run may report completion. Historical own-run notes remain provenance; installed runtime authority governs this invocation.

| Canonical Item | Status | Evidence |
|---|---|---|
| Post: Doctor Extension Check | ⏳ Pending | |
| Post: Verify Implementation | ⏳ Pending | |
| Post: Verify Tasks Phantom Check | ⏳ Pending | |
| Post: Code Review | ⏳ Pending | |
| Post: Integration Suite | ⏳ Pending | |
| Post: Reviewability Diff Gate | ⏳ Pending | |
| Post: UAT Runbook Generation | ⏳ Pending | |
| Post: Final Reviewability Backstop | ⏳ Pending | |
| Post: PR Packet/Body Generation | ⏳ Pending | |
| Post: PR Body Generation | ⏳ Pending | |
| Post: PR Creation | ⏳ Pending | |
| Post: Review Remediation | ⏳ Pending | |
| Post: Retrospective | ⏳ Pending | |

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

```
racecraft-plugins-public/
├── speckit-pro/                     # Plugin source (installs from dist/)
│   ├── speckit_pro_runner/          # Python runner: helpers/, gates/, contracts/, formal/
│   ├── skills/                      # Claude skills (autopilot, scaffold, status, resolve-pr, coach)
│   ├── codex-skills/                # Codex overrides of skills/
│   ├── agents/                      # Claude agents (*.md)
│   └── codex-agents/                # Codex agents (*.toml)
├── scripts/                         # Repository tooling (refresh-release-artifacts.py, compose-release-notes.py)
├── tests/speckit-pro/               # Layers 1, 4, 5, 6, 7; suite-manifest.json
├── dist/                            # Generated plugin payloads (never hand-edit)
├── docs-site/                       # Astro/Starlight docs; generated reference pages
├── docs/ai/specs/                   # Roadmaps, MOCs, .process/ workflow exhaust
└── specs/                           # Per-feature contract artifacts
```

---

### Plan publication recovery

Issue #684 tracks the native packet apply refusal when only this run’s private execution ledger was untracked. The rejected apply made no writes. A command-scoped Git exclusion removed only that exact private file from status; the identical apply then succeeded and the packet validator passed. No ledger relocation, deletion, staging, global ignore, repository ignore, or persistent Git configuration change occurred. The draft was created through gh-stack from the validated packet.

### Plan handoff structural checks

Ripwire quality-delta returned exit 2 for canonical process-state verbosity. Its test-gate returned exit 4 for five planning-document symbols without mapped tests. These are reported advisory limits for this documentation handoff; no runtime or complete-suite pass is claimed. The phase/status guard and artifact record validation passed.

## Artifact Review Handoff

```json
{
  "schema_version": "1.0",
  "feature_dir": "specs/hrns-015-autopilot-gate-pr-emission-repair",
  "input_hashes": {
    "specs/hrns-015-autopilot-gate-pr-emission-repair/spec.md": "18c93677aaaee5f73aa8399b2cea052cc58ed2724fe6e74d93be96a47eae7e58",
    "specs/hrns-015-autopilot-gate-pr-emission-repair/plan.md": "8381e50f0c0daf7491b6fb6f6e431adea30a89277d0b3073fd476194e6a8d759",
    "specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md": "c5373d4f33f0ec316c2421d3e690888fc5844fb1989fd5f5db9b4a8d4d1f7d46",
    "docs/ai/specs/.process/HRNS-015-design-concept.md": "2179b6c3fb8ab3b5bfe0a326ccf1af68b3b0ce7160286745a01713d4264ccba2"
  },
  "manifest_sha256": "c90a240c9ae6d007e6aa1586612891de78337d2c0f7892ec121fb4fe316d25a0",
  "template_hashes": {
    "implementation-plan": "781bd0ea88a97bd5d0b38d4791b96bf04479042f544994488d5a7b7444c088b9",
    "spec-explainer": "b8a4c87b550aeae38ff3dc645367676439b88292107e821e188a5553b053f555",
    "code-approaches": "28631395c17a39b03060704aef3cf0462a7e0212fb2fa139219af93290b05e03",
    "module-map": "9cb043012178506be09a0e5b987df67507c34e2ca12f6ea198bfdab3a1c528e5",
    "architecture-viewer": null
  },
  "generation_error": null,
  "pages": [
    {
      "id": "implementation-plan",
      "generation": "generated",
      "path": "specs/hrns-015-autopilot-gate-pr-emission-repair/artifacts/implementation-plan.html",
      "sha256": "43cc71f3246b74cca5b30ddc321562329f96fe462e50df85a2a97dc6dc16993d",
      "expected_title": "Implementation Plan \u2014 HRNS-015 Autopilot, Gate, and PR-Emission Repair",
      "expected_content": "Eighteen approved review increments repair packet emission, gates, completion and scaffold flows on Claude Code and Codex.",
      "preview": {
        "status": "unavailable",
        "blocker": "Current 2.38.0 preview-isolation-session observe_codex returned missing_prerequisite: preview_boundary_unavailable; no isolated observation was produced.",
        "observation": null
      }
    },
    {
      "id": "spec-explainer",
      "generation": "generated",
      "path": "specs/hrns-015-autopilot-gate-pr-emission-repair/artifacts/spec-explainer.html",
      "sha256": "9d2c15aed91814c9768b2085708a8453eaf6e509077c301b699eab1d6f132979",
      "expected_title": "Spec Explainer \u2014 HRNS-015 Autopilot, Gate, and PR-Emission Repair",
      "expected_content": "All implementation checkpoints remain pending.",
      "preview": {
        "status": "unavailable",
        "blocker": "Current 2.38.0 preview-isolation-session observe_codex returned missing_prerequisite: preview_boundary_unavailable; no isolated observation was produced.",
        "observation": null
      }
    },
    {
      "id": "code-approaches",
      "generation": "generated",
      "path": "specs/hrns-015-autopilot-gate-pr-emission-repair/artifacts/code-approaches.html",
      "sha256": "a3862645012b57c3e35105f1d76942216c21d7da769306805138a3a90af9ccbb",
      "expected_title": "Code Approaches \u2014 HRNS-015 Autopilot, Gate, and PR-Emission Repair",
      "expected_content": "How should a supplied release note reach a final PR without separating its body from the validated packet?",
      "preview": {
        "status": "unavailable",
        "blocker": "Current 2.38.0 preview-isolation-session observe_codex returned missing_prerequisite: preview_boundary_unavailable; no isolated observation was produced.",
        "observation": null
      }
    },
    {
      "id": "module-map",
      "generation": "generated",
      "path": "specs/hrns-015-autopilot-gate-pr-emission-repair/artifacts/module-map.html",
      "sha256": "2fd57d9a2e74d03cbd27533264bb7a8ab3503b7d42c8d323d1f3595db88e0d9d",
      "expected_title": "Module Map \u2014 HRNS-015 Autopilot, Gate, and PR-Emission Repair",
      "expected_content": "Fourteen stories cover 26 active requirements in eighteen ordered increments.",
      "preview": {
        "status": "unavailable",
        "blocker": "Current 2.38.0 preview-isolation-session observe_codex returned missing_prerequisite: preview_boundary_unavailable; no isolated observation was produced.",
        "observation": null
      }
    },
    {
      "id": "architecture-viewer",
      "generation": "gap",
      "reason": "The selected entry is planned in the shipped manifest, but templates/architecture-viewer.html is absent."
    }
  ]
}
```

## PR Marker Plan Evidence

- Schema version: pr-marker-plan.v1
- Plan status: checkpointing
- Fingerprint status: Current
- Reviewability: planned candidate budgets pass; actual diffs and LOC are unmeasured.
- Warnings: implementation evidence pending.
- Final marker_split: pending
- Packet validation: pending implementation emission
- PR mappings: pending implementation emission
- T001 and T002 are prerequisites assigned to the first story marker; T031 folds into the final marker. No extra delivery increment is introduced.

| Source | SHA-256 |
| --- | --- |
| Feature spec | `sha256:18c93677aaaee5f73aa8399b2cea052cc58ed2724fe6e74d93be96a47eae7e58` |
| Plan declared scope | `sha256:8381e50f0c0daf7491b6fb6f6e431adea30a89277d0b3073fd476194e6a8d759` |
| Tasks | `sha256:91cc48b1ff3352e299b31537323760edf4a84f5909c6600fc7b7cb575d0e03e3` |
| Reviewability | `sha256:4efa6739751bbef3183ebc677bde97f4971dfc61554ecf27a147af5d65aabefc` |
| Hazard route | `sha256:f4259204cb8f92f1978ddf3b70195aba948d317567082f50f585fb0f4e0ef9c4` |

| Review order | Marker | Increment | Tasks | Implementation checkpoint |
| --- | --- | --- | --- | --- |
| 1 | `us1-part1` | A1a | T001, T002, T003, T004 | complete at `5a89c0b706d905760157e1b6d2f7579039c1ee26`; evidence `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/checkpoints/us1-part1.json` |
| 2 | `us1-part2` | A1b | T005 | complete at `33ce117a0ba41769a21e2aab7dcca3bb880440b0`; evidence `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/checkpoints/us1-part2.json` |
| 3 | `us2` | A2 | T006, T007 | complete at `ed24ecd831d0b9f98e300fdc772f29839bd09d9a`; evidence `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/checkpoints/us2.json` |
| 4 | `us3` | A3 | T008, T009 | complete at `c60a3398b1e07412ec3cbb4468f3ca8a16a4687d`; evidence `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/checkpoints/us3.json` |
| 5 | `us4` | B1a | T010 | complete at `a1aa6bd265aa15d4a7005b5c0f0be77af786cb04`; evidence `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/checkpoints/us4.json` |
| 6 | `us5` | B1b | T011 | Pending |
| 7 | `us6` | B2b | T012, T013 | Pending |
| 8 | `us7` | B3a | T014 | Pending |
| 9 | `us8` | B3b | T015, T016 | Pending |
| 10 | `us9` | C1a1 | T017 | Pending |
| 11 | `us10-part1` | C1a2 | T018 | Pending |
| 12 | `us10-part2` | C1b1 | T019 | Pending |
| 13 | `us10-part3` | C1b2 | T020, T021 | Pending |
| 14 | `us11` | C2a1 | T022, T023 | Pending |
| 15 | `us12` | C2a2 | T024 | Pending |
| 16 | `us13-part1` | C2a3 | T025 | Pending |
| 17 | `us13-part2` | C2b1 | T026, T027 | Pending |
| 18 | `us14` | C2b2 | T028, T029, T030, T031 | Pending |


## Current Analyze Evidence — 2.37.1

Owner ratification, 2026-09-27: the owner confirmed the eighteen-increment order A1a → A1b → A2 → A3 → B1a → B1b → B2b → B3a → B3b → C1a1 → C1a2 → C1b1 → C1b2 → C2a1 → C2a2 → C2a3 → C2b1 → C2b2 as the delivery count, with owner_ratification=ratified. Unverified artifact previews stay unavailable; implementation proceeds with an explicit `--stage implement`. T002 remains the first implementation gate: actual per-increment diffs, LOC and checkpoint evidence still block each PR emission.

The current review supersedes the historical nineteen-increment analysis. All 26 active FRs, 31 unchecked tasks, fourteen stories, 37 scenarios and eleven success criteria remain represented. Candidate sets contain 14–24 total and 0–2 production paths. Roadmap Done When items and five formerly uncovered scope bullets map to requirements and tasks. Constitution rules, paired-host delivery and formal selection none remain explicit.

### Analysis Results

| ID | Severity | Issue | Resolution |
| --- | --- | --- | --- |
| H1 | HIGH | Original C1 exceeds the path cap. | Approved C1a1/C1a2/C1b1/C1b2 candidates are 24/21/21/21 paths and at most two production paths. |
| H2 | HIGH | Advisory route differs from delivery direction. | Preserve one-navigable-PR as advisory; explicit eighteen-increment owner authority governs delivery. |
| H3 | HIGH | A allocation and approval outstanding. | Approval recorded; all four A sets contain 24 candidate paths. Actual emission evidence remains mandatory later. |
| H4 | HIGH | B allocation and approval outstanding. | Five remaining B sets contain 22/23/23/18/22 paths; shipped B2a retired. |
| H5 | HIGH | C2 allocation and approval outstanding. | Five C2 sets contain 14/14/14/21/16 paths; six shipped C2b2 exclusions documented. |
| H6 | HIGH | Story identities and marker record outstanding. | Eighteen ordered markers cover fourteen stories and all 31 tasks including folded T031. Every checkpoint is exactly pending; checksum declarations corrected and guard passes. |
| H7 | HIGH | Recurring evidence and qualifications outstanding. | Six recurring evidence paths included, current hashes match, checksum declarations corrected. Approved timing requires actual diff/LOC/checkpoint evidence before implementation PR emission. |
| H8 | HIGH | Nine A/B increments name nonexistent speckit-pro-runner.manifest.sha256 instead of speckit-pro-runner.sha256 in inventory, task ownership and marker declarations. | Corrected all 96 derived checksum references to generator-owned speckit-pro-runner.sha256 paths under the explicit guarded exception. Native metadata and regenerated marker guard pass; counts unchanged. |
| M3 | MEDIUM | C1b candidate group union says 29 although distinct teardown tests produce 30; individual increments remain 21/2. | Corrected C1b union to 30 total / 4 production, matching Plan and distinct rows; each increment remains 21 total / 2 production. |

### Consensus Resolution Log

| Item | Route | Agreement | Confidence | Resolution |
| --- | --- | --- | --- | --- |
| H8 | codebase analyst | Accept exact checksum substitution | High | Applied under explicit guarded exception; generator and payload verifier agree. Native task metadata and planned-marker validation pass. |
| M3 | codebase analyst | Accept independently counted union | High | Applied 30/4 union, preserving both 21/2 increments. |

The ordinary FR-026 reserve was refused with failure_family_budget_exhausted. The user explicitly approved the exact H8/M3 correction; authorize-corrective-exception retained the same run and two ordinary cycles. No implementation evidence was fabricated. Current schema and phase-coverage checks pass with all eighteen checkpoints pending-only.

### Pre-Implement Confidence — current 2.37.1 Analyze

Named consensus-synthesizer final result: H8 and M3 resolved, no dissent or flags; all current coverage preserved. Actual implementation qualification remains pending.

📊 Confidence: 0.95

- Task understanding: 0.96
- Approach clarity: 0.95
- Requirements alignment: 0.96
- Risk assessment: 0.93
- Completeness: 0.95

## Plan Stage Completion — 2.37.1

Planning complete. Current G3, G4, G5, G6 and G6.5 passed; confidence is 0.95 against 0.90 with no deductions. The Analyze checkpoint precedes the distinct plan-stage boundary commit. Draft #685, its packet, validation receipt and four refreshed artifacts are pushed. All eighteen pr-marker-plan.v1 checkpoints remain exactly pending, and all 31 implementation tasks remain unchecked. Implementation and Post are outside this stage.

The workflow-only Artifact Review Handoff records the architecture-viewer missing-template gap and four unavailable previews (preview_boundary_unavailable), with zero fabricated observations. Manual review remains possible from the generated files.

Structural diagnostics: ripwire quality-delta returned 2 for the required gate-record JSON growing from 50 to 75 lines; this is an advisory planning-data verbosity finding. Its test-gate returned 0 with no changed call-graph symbols or selected tests. No implementation verification is claimed. Native planning, metadata, phase coverage, title and draft packet validation passed. All native worker final results were consumed; no owned worker remains running.

## Implementation Startup — 2.38.0

Stage: implement, resolved from explicit invocation. Draft PR corroboration: match (#685 open draft). Planning phases and the recorded advisory G6.5 verdict are retained; no confidence gate was rerun. Native prerequisites, agent registrations, formal selection none, current task metadata and the implementation autonomy receipt pass. Archive Sweep has no eligible merged candidate and performs no cleanup. The isolated feedback capture at the exact current head observed zero comments: no amendment, no sweep-log row and no reply.

Offline HAL inventory delegation failed because the production-model endpoint was unavailable, with zero token usage, no findings or repository changes, and completed cleanup. Continue through the native installed executor fallback without a cloud export. The unchanged-branch baseline suite and all 31 tasks remain pending.

### Implementation routing checkpoint

The native journal froze T001 and T002 as implementation batches, requiring ordered RED/GREEN/refactor evidence for procedural inventory checks. Direct evaluation of the installed scheduler confirms changing only each leading verb to Verify routes both to orchestrator-direct with verification evidence. No requirement, stable task ID, dependency, owner, increment budget or implementation checkpoint changes. The ordinary FR-026 corrective reserve refused failure_family_budget_exhausted; two corrective cycles and the epoch exception are already spent. A bounded operator-approved Tasks re-plan is requested. The original native journal and its parent-retained partition identity are preserved, with zero task reports or completed tasks. The baseline suite remains owned and in flight; no replacement or implementation dispatch has started. Feedback sweep: no comments observed, no amendment, no row and no reply; private state removed. Artifacts are current as of 72a4e956.

### Baseline result and public-record normalization

The owned baseline completed with native exit1: 9445/9448 passed, with three privacy checks failing. Two findings were parent public-bookkeeping serialization defects: a raw runner envelope contained an interpreter path, and a delegation identity was copied as a raw UUID. The state now uses the helper result projection and an opaque identity digest. The third dynamic-local-term finding includes common autopilot prose in repository files; its original failed result is retained pending focused diagnosis. No test or requirement is weakened, and the baseline is not marked passing. Every startup native dispatch is settled; all31 tasks and thirteen Post rows remain pending.

### Approved bounded routing re-plan — 2.38.0

The operator ordered the exact two-word Tasks re-plan and approved a fresh allowance. Native begin-replan-epoch preserved the run, clocks, consumed events and prior ledger history in epoch 2. One ordinary FR-026 correction owns T001 Confirm → Verify and T002 Recheck → Verify with no requirement, task-ID, dependency, ownership or budget change. The original task journal remains unchanged; a source-bound successor and downstream planning gates are pending. All eighteen marker checkpoints remain exactly pending.

The focused privacy verification now passes 10/11 checks. Both parent public-serialization defects are cleared. The remaining dynamic local case derives autopilo and utopilot from the bound worktree path and matches existing autopilot prose; this is the documented Own-Run Hazard exception. No privacy rule was weakened; neutral-checkout CI proof remains pending. The original 9445/9448 baseline failure is retained.

### Analyze after the bounded routing re-plan

Current Analyze found zero Critical, High, Medium or Low findings. It verified all26 active requirements,31 pending tasks, unchanged task ownership/dependencies and eighteen ordered planned markers. Every checkpoint remains exactly pending. Native source/metadata validation and successor lineage are current. Actual diff/LOC/checkpoint evidence and any tracked journal path contributions remain mandatory before emission.

### Pre-Implement Confidence — bounded routing re-plan

The named synthesizer finds no unresolved planning finding. Actual diff budgets, LOC, checkpoints, journal contributions and CI remain unqualified before emission. The documented privacy-check exception remains a verification limitation.

📊 Confidence: 0.94

- Task understanding: 0.96
- Approach clarity: 0.95
- Requirements alignment: 0.96
- Risk assessment: 0.91
- Completeness: 0.94

The artifact author refreshed only T001/T002 verbs in Implementation Plan and validated all four existing pages against the current shipped templates. The selected Architecture Viewer template remains absent; no preview proof is claimed.

### Bounded re-plan documentation verification

The full docs command exited1 at Playwright web-server startup after reference/check/build, internal links, safe-install aids and docs quality passed. Focused diagnostic smoke then passed88 tests with native exit0 against the exact same-worktree preview server; its process and cwd were independently verified. The remaining gallery check passed4 tests with native exit0. The owned leftover preview server was stopped. The initial failed aggregate result remains recorded; no aggregate rerun or authored fix was substituted. Spec index dry-run/apply both returned no-op; local journals were restored byte-identically and do not enter generated backlinks.

### Bounded planning re-plan stage boundary

G5 and G6 passed on the current sources. Native advisory G6.5 computed0.94 from the five new canonical criterion lines, above0.90, with zero deductions. The refreshed autonomy/phase coverage guard passed all error arrays empty. The ledger checkpoint preserved the run and one consumed ordinary correction in epoch2. The draft artifact handoff is in progress; implementation remains0/31 and all13 Post rows remain pending.

### Bounded re-plan handoff complete; implementation resumes

The native draft packet/body and validation receipt are committed and pushed, and draft#685 was refreshed from that validated body. Native apply first refused the two untracked local journals. Only those journals were stashed using the helper-recommended remedy; their exact byte hashes were retained and verified after restoration. The stash remains a recovery backup. No source change was hidden, no ignore rule changed, and the initial refusal remains recorded. The existing run and original journal are preserved.

Planning gates and artifact refresh are complete. Stage implement resumes at T001; no task completion or actual increment evidence is claimed. All13 Post rows remain pending. The initial feedback sweep proceeded with zero comments: no sweep commit, no row, no reply; its private state was removed. Pages were current as of72a4e956 before the bounded task-word refresh at1c9bfb60. The validated draft description refresh completed. Continue the existing implementation stage from current native journal evidence.

### T001 native partial result and timing clarification

T001 current candidate checks pass for all18 markers:14–24 planned paths and0–2 production paths, current native verification route, no definition or requirement changes. Every implementation checkpoint remains pending. T001 also names reconciliation against a first actual implementation checkpoint; native B002/T002 depends on T001, and B003/T003–T004 depends on T002. The operator is asked whether the already-approved before-emission timing also governs this prerequisite.

The original journal is unchanged. The successor retains one native unfinished T001 report and returns checkpoint_required/unfinished_task_results; no completion or checkpoint proof was supplied. The bounded attempt is settled as failed in the ledger with no extra corrective cycle consumed. The mandatory implementation-notes header and separate T001 entry are present. T001 remains unchecked, implementation0/31, all13 Post rows pending, and no source batch has been dispatched.

The native external-approval wait is active for the pending timing question; the run, epoch2 allowance and one spent ordinary correction remain unchanged. Resume requires the actual operator reply event matched to this wait. Ripwire test-gate returned0 with zero changed/impacted executable symbols (not suite proof). Its range quality-delta returned2 for expanded JSON bookkeeping gate evidence; required evidence/history was retained.

### T001 approved timing resolution

The operator approved completing candidate-inventory verification now. T001 is complete from its retained candidate checks; the successor journal preserves the earlier unfinished report and appends the native completion. Actual per-increment diff, LOC and checkpoint reconciliation remain mandatory before PR emission. Every implementation checkpoint remains exactly pending. Implementation is1/31; T002 is in progress.

### T002 native candidate verification

The installed phase/autonomy guard passes53 rows with all error arrays empty. Eighteen candidate sets remain within four production and24 total paths; Q11/five-group provenance and shipped #676 support are preserved. Marker fingerprints are current and every v1 implementation checkpoint remains exactly pending. Native journal evidence completes T002; implementation is2/31. Actual diff, LOC and checkpoint qualification remains mandatory before emission. The first source batch is T003/T004.


### Approved FR-001 correction checkpoint

The exact operator-approved three-file correction passed native RED (203 tests, 40 assertion failures), GREEN and distinct refactor (203/203 each), independent A1a review, Ruff, mypy across 50 files, and documentation reference/quality checks. Release and reference generators were refreshed. Native task completion recording remains blocked by unfinished-report RED reuse handling; original journal history is preserved and only T001/T002 remain complete. No increment checkpoint or PR emission is qualified. Ripwire structural quality/impact diagnostics returned nonzero and remain recorded separately from behavioral proofs. Final full-suite and committed artifact checks remain pending.


### Checkpoint allocation re-plan approval wait

Native FR-026 reconciliation reserve refused failure_family_budget_exhausted after the two ordinary cycles and the completed FR-001 exception. All dispatches settled before the operator request. The private six-file candidate retains 31 task IDs, 18 increments, planned 15–24 total/0–2 production paths and exactly pending checkpoints; it adds the schema planning baseline, two immutable proof paths per increment and the grounded candidate reallocations. The native patch apply-check passes, but no planning correction was applied. Actual native successor acceptance, full required verification, publication accounting and PR-base authority remain pending. Implementation remains2/31 with all13 Post steps pending.


### Implement-stage 2.38.1 resumption and A1a checkpoint

The operator declined the proposed Tasks re-plan. Installed SpecKit Pro 2.38.1 closed the external wait against the original event, then opened implement-stage epoch 3 under the same run ID. The previous allowance and dispatch history remain archived; no successor journal or new planning correction was created. The status-evidence guard passes with all public-state event IDs stored as SHA-256 digests.

Native task-results accepted the existing routing-epoch2 T003/T004 completion report with its original RED, GREEN and refactor observations; T001–T004 are journal-complete. The shipped marker-checkpoint schema resolves from the installed plugin, and marker evidence plus implementation notes remain outside the counted path budget. A1a source behavior and the focused privacy scan pass. The initial quick suite passed 9,456/9,458 checks; two privacy checks found local paths in implementation notes and public worktree-slug false positives. The notes were redacted. The merge from main supersedes the local checkout-leaf scanner fix with the repository's public worktree-name fix, which derives identity terms from the path above the main checkout while retaining user, home and Git identity scanning. The full quick suite rerun passed 9,459/9,459, with toolchain preflight passing. Actual A1a diff/LOC measurement and marker checkpoint remain pending before T005.


### A1a origin/main integration

The A1a source checkpoint was committed as `6639c94cb3ab2c8683217a6e4174555eac59cd57` after the quick suite passed 9,459/9,459, artifact consistency, docs quality, Ruff and mypy passed, and independent source review found no actionable defects. The requested non-rebase merge of origin/main brought SpecKit Pro 2.38.1 and its own public-worktree privacy fix. The release manifest version was aligned with the merged plugin source, and release payloads plus docs reference pages were regenerated. Merged-tree A1a gates and the marker checkpoint remain pending before T005.

A1a marker checkpoint, 2026-09-28T15:10:30Z: the existing routing-epoch2 journal records T001–T004 complete, including the original T003 RED and later GREEN/refactor observations. The A1a source delta (`82095a3e..6639c94c`) touched 21 paths, of which 20 count against the 24-path limit; 2 are production paths and authored non-process changes total 357 lines. The post-merge source commit `5a89c0b706d905760157e1b6d2f7579039c1ee26` passed the 10,106/10,106 quick suite, six CI suite layers, full docs validation (88 smoke and 4 gallery tests), artifact consistency, Ruff, mypy, host parity and independent critical/high review. The first marker evidence is committed under `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/checkpoints/us1-part1.json` and `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/verification/us1-part1.json`. The final emitted PR base/head diff and reviewable LOC remain mandatory before PR emission.

Operator instruction, 2026-09-28: do not refresh or reinstall the installed SpecKit Pro plugin. Issue #812 is the operator-reported upstream fix for installed 2.38.1 pending-marker checkpoint binding and checkbox-only `tasks.md` autonomy fingerprint staleness. Record only those installed-cache guard errors as known upstream defects and continue other implementation units; all other gates remain mandatory. The branch-local guard correction has RED→GREEN proof, full phase-coverage tests and independent review; the installed cache remains unchanged.

A1b marker checkpoint, 2026-09-28T18:21:09Z: T005 is complete in the existing routing-epoch2 journal. The source checkpoint `33ce117a0ba41769a21e2aab7dcca3bb880440b0` passed the final 10,110/10,110 quick suite, six CI dispatches, 151/151 focused read-only tests, artifact consistency, reference-mode docs validation, pinned Ruff and mypy, privacy scan and host parity. Independent re-review found no critical/high defect after a red-first fenced-heading correction. The marker evidence is committed at `241edeef15a54f6e084872427cd71517e5678311`. Its source delta touched 21 paths; with the three tracked workflow/state/tasks updates, A1b is 24 paths and 2 production paths, with 292 authored non-process changed lines. The emitted PR base/head diff and reviewable LOC remain mandatory before PR emission. Installed-cache issue #812 remains limited to the two operator-identified false positives.

A3 marker checkpoint, 2026-09-28T21:17:52Z: T008/T009 are complete in the original routing-epoch2 journal. The source checkpoint `c60a3398b1e07412ec3cbb4468f3ca8a16a4687d` passed 10,111/10,111 quick suite tests, six CI dispatches, artifact consistency, reference-mode docs validation, pinned Ruff and mypy, privacy scan and host parity. The independent audit found a stale verdict label bypass, corrected red-first before this checkpoint. The source delta touched 18 paths; four tracked process updates bring the marker to 22 budget-counted paths, 2 production paths and 204 authored non-process changed lines. The marker evidence is `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/checkpoints/us3.json` and paired verification report. Final emitted PR base/head diff and reviewable LOC remain mandatory before PR emission.

B1a marker checkpoint, 2026-09-28T23:26:57Z: T010 is complete in the original routing-epoch2 journal. The source checkpoint `a1aa6bd265aa15d4a7005b5c0f0be77af786cb04` passed 10,118/10,118 quick suite tests, six CI dispatches, artifact consistency, full docs validation, pinned Ruff and mypy, privacy 14/14 and host parity. Independent review found paragraph, heading and blockquote false negatives; each was corrected red-first and the reviewer confirmed those repros at the committed head. The source delta touched 18 paths; four tracked process updates bring the marker to its 22-path cap, one production path and 497 authored non-process changed lines. Ambiguous unclosed fences count markers conservatively and can overcount; a visible marker is not hidden. The marker evidence is `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/checkpoints/us4.json` and its paired verification report. Final emitted PR base/head diff and reviewable LOC remain mandatory before PR emission.
