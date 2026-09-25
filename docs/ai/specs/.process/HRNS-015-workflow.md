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
| Specify | `/speckit-specify` | ✅ Complete | 14 user stories, 29 current functional requirements, 39 acceptance scenarios after Clarify; G1 passed |
| Clarify | `/speckit-clarify` | ✅ Complete | Four sessions complete; ten consensus decisions recorded; G2 passed with zero markers |
| Plan | `/speckit-plan` | ✅ Complete | G3 passed; advisory file-based estimate not estimated because the declared Slice A inventory is partial |
| Checklist | `/speckit-checklist` | ⏳ Pending | Run for each domain |
| Tasks | `/speckit-tasks` | ⏳ Pending | |
| Analyze | `/speckit-analyze` | ⏳ Pending | |
| Confidence Gate | G6.5 | ⏳ Pending | Pre-Implement composite confidence |
| Implement | `/speckit-implement` | ⏳ Pending | |
| Post | Post-Implementation | ⏳ Pending | Canonical 11-item closeout |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⏭️ Skipped | ⚠️ Blocked

G6.5 is advisory by default, so no phase of the main loop flips its row. Leaving
it Pending is legitimate and does not make the rows below it read as out of
order; record the verdict in [Phase 6.5](#phase-65-confidence-gate) when the
gate runs.

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
- [ ] Setup mode scopes to `inputs.spec_id`, fails closed on missing fields, honors the pragma, and checks per-slice budgets; #637 fixture (AC-16.9; Q6)
- [ ] `estimate-spec-size` accepts a required-refactor signal (AC-16.8)
- [ ] `detect-commands` honors a declared `commands` block in `.specify/quality-gates.json` (AC-16.8; Q9)
- [ ] One 13-item Post list on both hosts, sourced from `POST_STEPS`, and a completion-boundary check refuses pending rows on both hosts (AC-16.2; Q1)
- [ ] Every team-capable executor on both hosts carries a teardown obligation, proven by a structural test (AC-16.4)
- [ ] `speckit-resolve-pr` paginates threads and comments and replies/resolves only after verify, push, and a confirmed pushed SHA, on both hosts (AC-16.7)
- [ ] The blind-spot pass has no fixed deadline and fails open only on dispatch error, empty return, or operator abandonment (AC-16.8 amended; Q2)
- [ ] Tested request envelopes at the live-failure sites; the full sweep moves to HRNS-019 (AC-16.10 narrowed; Q8)
- [ ] The roadmap template and README link `.process/` workflow files; #638 fixture (AC-16.9)

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
| Acceptance Criteria | 39 scenarios after Clarify |

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
- #637: Reproduce the oversized-first/small-last roadmap, selected-entry `infra` pragma, and missing-budget pass from the issue; add failing-first fixtures for exact `inputs.spec_id` scoping, selected authored section only, greenfield LOC-only allowance, primary surfaces, and aggregate plus per-slice budget checks.
- #638: Reproduce the template link that resolves beside the roadmap instead of under `.process/`; verify new template/scaffold output and preserve existing legacy links only when their targets exist. Add failing-first fixtures for generated and existing roadmaps.

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
- speckit-pro/skills/speckit-scaffold-spec/SKILL.md and the Codex mirror: changed. Deadline removed; new fail-open reasons; inline envelopes (Q2, Q8); `inputs.spec_id` passed to setup gate and workflow-link updates preserve verified legacy targets (#637, #638).
- speckit-pro/skills/speckit-status/SKILL.md and the Codex mirror: changed. Inline envelopes for generate-spec-index-check and o5-topology (Q8; late blind-spot findings 8 and 10).
- speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md: changed. `.process/` workflow links (#638) and the slice-budget syntax (Q6); scaffold preserves existing verified legacy link targets.
- speckit-pro/skills/speckit-coach/templates/workflow-template.md: changed. 13-row Post table (Q1).
- speckit-pro/README.md: changed. Workflow path at :178 (evidence: #638).
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

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ✅ Complete | Four-slice architecture and module deltas; preliminary budget distinguished from Plan sizing stress check |
| `research.md` | ✅ Complete | Decisions, issue reproductions, and external documentation limitation |
| `data-model.md` | ✅ Complete | Runner, packet, roadmap, and workflow state entities |
| `contracts/` | ✅ Complete | `runner-and-roadmap.md` and `workflow-and-pr.md` |
| `quickstart.md` | ✅ Complete | Failing-first workflow and verification commands |

G3 passed with zero unresolved markers. No formal model is selected. The standalone `estimate-reviewable-loc` helper returned `not_estimated` (`projected: null`, zero parseable declared file operations) because Slice A’s ten named operations are a partial subset of its 16-file projection. The current size helper’s 1,932-LOC/five-slice stress check uses 77 provisional file touches and ignores the required-refactor input; it is not a refactor-inclusive estimate. Tasks must complete distinct file and refactor inventories before claiming the four-slice budget is qualified.

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

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| api-contracts | | | |
| error-handling | | | |
| state-management | | | |
| **Total** | | | |

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
- Small, complete behavioral units sized for the whole automated spec's
  two-hour budget, including startup, implementation, repairs and final checks
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
| **Total Tasks** | |
| **Phases** | |
| **Parallel Opportunities** | |
| **User Stories Covered** | |

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
| **Route** | | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | | `true`, or `false` for a destructive-migration or concurrency-sensitive change (a passing CI run does not prove such a change is safe to release). |
| **Signals** | | The decisive detector findings behind the route and releasability reading (may be empty when the classifier abstains). |
| **Warnings** | | Any release-safety warning attached to the change (empty when there is no releasability risk). |

Expected route from scoping: `split-PR`, four layers in stack order A → B → C1 → C2
(design concept Q11, Open Question 4).

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
| | | | |

---

## Phase 6.5: Confidence Gate

**When to run:** After Phase 6 commits and before Phase 7 begins. This section
records the verdict so a later session can read it.

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

The canonical closeout. Every row must reach Complete or an explicit
`Skipped` before the run may report completion.

This run uses the installed autopilot's 11-row list. The 13-row list is a
Slice C1 deliverable (see Own-Run Hazard).

| Canonical Item | Status | Evidence |
|---|---|---|
| Post: Doctor Extension Check | ⏳ Pending | |
| Post: Verify Implementation | ⏳ Pending | |
| Post: Verify Tasks Phantom Check | ⏳ Pending | |
| Post: Code Review | ⏳ Pending | |
| Post: Integration Suite | ⏳ Pending | |
| Post: Reviewability Diff Gate | ⏳ Pending | |
| Post: UAT Runbook Generation | ⏳ Pending | |
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
