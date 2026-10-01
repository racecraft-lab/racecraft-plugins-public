# SpecKit Workflow: HRNS-015 — Autopilot, Gate, and PR-Emission Repair

**Template Version**: 1.0.0
**Created**: 2026-10-01
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
| Specify | `/speckit-specify` | ⏳ Pending | |
| Clarify | `/speckit-clarify` | ⏳ Pending | Optional but recommended |
| Plan | `/speckit-plan` | ⏳ Pending | |
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

### Scope Budget and Split Decision

Setup reviewability gate (`reviewability-gate`, setup mode, 2026-10-01): **warn,
pass**. Primary surface harness/adapter (1); projected 390 reviewable LOC;
6 production files; 24 total files. Warning: total files 24 exceeds warn
threshold 15. Scaffold `estimate-spec-size` (3 stories, 6 files, 9 FRs,
modify): 225 LOC, 1 suggested slice, ok, so the Phase 6.5 verdict item stays in
HRNS-015 (move-back threshold 400 LOC not reached).

**Split decision (design concept Q5):** one spec, three user stories, emitted
as three split PRs in roadmap order: Slice A (PR emission), Slice B (gates and
counters), Slice C (workflow behavior). Each PR holds at most four production
files and ten authored files. Regenerated `dist/` and runner trust files follow
their sources and are not budgeted.

---

## Prerequisites

### Constitution Validation

**Before starting any workflow phase**, verify alignment with the project constitution (`.specify/memory/constitution.md`):

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| IV. Test Coverage Before Merge | New helper behavior has Layer 4 unit coverage; changed agents/skills pass Layer 1 | CI-suite runner request in `AGENTS.md`; `scripts/run-python-lint.py run ruff` and `run mypy` |
| VI. KISS, Simplicity & YAGNI | Repairs only; no schema redesign, no extra command slots | Code review |
| VII. Generated Artifact Contract | `dist/`, runner manifests, hashes, and the spec index regenerated and committed with sources | `python3 scripts/refresh-release-artifacts.py --check` |
| VIII. Two-Host Parity | Executor teardown text and skill changes ship in Claude agents and Codex TOML/overlays together | Layer 7 parity fixtures; Layer 1 mirror contracts |
| IX. Fail-Closed Gates and Red-First Fixes | Each fix starts with a failing fixture; git failure, invalid project-commands file, and blank verdict fail closed | Regression test in each fixing change; code review |
| X. Public-Repository Privacy | Fixtures carry no private data | Code review |

**Constitution Check:** ✅ / ❌ (mark before proceeding to G1)

### Quality Gates

Filled from `detect-commands` at Step 0.11. One row per slot; the operator answer column holds the missing-tool outcome (`install` by default, then `skip (spec)`, or a recorded operator `skip (repo)`) and is the record autopilot reads before it defaults. A `skip (repo)` answer is durable only once the operator adds it to `.specify/quality-gates.json` `skips`.

**Thresholds file:** `.specify/quality-gates.json` missing at scaffold time (2026-10-01) <!-- complexity N, CRAP N, mutation floor N; basis --> (G0 blocks unless present)

**Hardener:** not run <!-- not needed (score N ≥ floor F) | delegated: iteration k of cap: N → M ... floor reached / cap reached | fallback (reason): ... | rejected candidate: reason --> (fires once per spec when MUTATION is populated)

| Slot | Status | Tool | Command | Operator answer | G0 baseline | Final |
|------|--------|------|---------|-----------------|-------------|-------|
| COMPLEXITY | <!-- populated / unconfigured --> | <!-- e.g., radon + coverage.py --> | <!-- recorded with `{plugin_root}` and `{paths}` literal --> | <!-- blank until asked --> | <!-- baseline: N checked, V over ceiling (whole tree; exit 2 blocks) --> | <!-- pass / fail / n/a: no source files changed --> |
| MUTATION | | | | | <!-- deferred: runs on the spec diff at final verification --> | |
| DEPENDENCY_RULES | | | | | <!-- real run: pass / fail --> | |
| DEPENDENCY_AUDIT | <!-- off (not opted in) / populated (enforce) / unconfigured --> | | | <!-- off: never asked --> | <!-- off: not opted in / pass / fail --> | |

---

## Formal Methods

Design concept Verification Gates: no formal model. The changes are
deterministic input validation, path-set predicates, and prose contracts with no
concurrency or state machine that ordinary fixtures cannot cover.

```json
{
  "schema_version": "1.0",
  "status": "none",
  "rationale": "HRNS-015 repairs deterministic helpers (packet rendering, an untracked-path set predicate, marker counting, a tracked-file walk, size arithmetic, command lookup) and prose contracts; there is no concurrency, protocol, or state machine whose risk exceeds what failing-first unit and Layer 1 fixtures cover.",
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
| **Dependencies** | none |
| **Enables** | HRNS-016, HRNS-032 |
| **Priority** | P1 |

### Success Criteria Summary

From the roadmap's Done When (`docs/ai/specs/harness-engineering-uplift-technical-roadmap.md`, ### HRNS-015), refined by the design concept:

- [ ] A final packet built with `release_note` passes `scripts/release_note_policy.py` for a `feat` and a `fix` title (repo-level test); without the input the body is byte-identical to today; a draft has no fence.
- [ ] Packet apply succeeds with only the current packet's three canonical files untracked, and refuses for a second packet, an unrelated file, a tracked edit, and a `git status` failure, each proven by a fixture.
- [ ] The final body carries the current Phase 6.5 verdict under Verification; a blank Verdict cell blocks finalization.
- [ ] A fixture with `[Gap]` and `[Gap, <ref>]` counts both in G1-G4 and `count-markers`.
- [ ] `refresh-release-artifacts.py --check` fails on a frozen pre-fix stale `SPEC-MOC.md` fixture and passes with an untracked file present; the tracked-only walk fails closed when git fails.
- [ ] `estimate-spec-size` fixtures cover a refactor count, a missing value, and an invalid value.
- [ ] A `.specify/project-commands.json` declared command wins over detection; an invalid file returns a diagnostic with no fallback; this repository ships its own file.
- [ ] Layer 1 structural tests pin `speckit-resolve-pr` paging (>100 threads, multi-page comments), stop-on-failed-page, and the pushed-SHA check before reply/resolve.
- [ ] The structural test fails when any of the eight executor definitions loses its teardown obligation.
- [ ] Each documented `speckit-status` envelope matches a passing fixture.

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/hrns-015-autopilot-gate-pr-emission-repair/spec.md`

### Specify Prompt

```text
/speckit-specify Repair the autopilot defects that main still has so the documented happy path stops producing a failing pull request or a silently wrong count. Three user stories, each shipped as its own split PR in this order. (A) PR emission: final packets accept an optional autopilot-drafted release note rendered as one release-note fence after Known Gaps; packet apply tolerates exactly the current packet's three untracked canonical files and still refuses everything else; the final body shows the current Phase 6.5 verdict and a blank verdict blocks finalization. (B) Gates and counters: [Gap] and [Gap, <ref>] count alike in G1-G4 and count-markers; the spec-index walk uses tracked files only and fails closed when git fails, with a release-artifact --check that catches a stale index; estimate-spec-size accepts required_refactor_files; detect-commands honors UNIT_TEST and FULL_VERIFY declared in .specify/project-commands.json before marker detection, errors on an invalid file, and this repository ships its own file. (C) Workflow behavior: speckit-resolve-pr pages every thread and comment and checks the pushed SHA before replying or resolving; four executors on both hosts state a team teardown obligation; speckit-status documents complete request envelopes for generate-spec-index-check and o5-topology. Every fix starts with a failing fixture.
```

#### Detailed Prompt (for complex specs)

```text
/speckit-specify

## Feature: Autopilot, Gate, and PR-Emission Repair

### Problem Statement
Live autopilot runs on main still hit defects that produce a failing pull request
or a silently wrong count: final PR bodies fail this repository's release-note gate,
packet apply refuses because of the packet's own untracked files, the PR body omits
the G6.5 verdict, `[Gap, <ref>]` markers go uncounted, the spec index includes
untracked files and can go stale undetected, the size estimator ignores required
refactors, detect-commands ignores a repository's documented test command,
speckit-resolve-pr reads only the first page of threads and can reply against a
stale head, executors leave teams running, and speckit-status shows incomplete
request envelopes. Each repair needs a failing-first fixture (constitution IX).

### Users
- The autopilot operator, who needs the happy path to produce a mergeable PR.
- Host repositories running speckit-pro, which need correct counts and their own
  declared test commands.
- Reviewers, who need the PR body to state the release note and G6.5 verdict.

### User Stories
- US1 (P1, Slice A, PR emission): As an operator, the final PR body autopilot emits
  passes the release-note gate, applies cleanly, and states the G6.5 verdict.
  - Optional `release_note` input on final (single and split) packets; `build_packet_body`
    renders it as one ```release-note fence after Known Gaps. Drafts never carry one.
    The note is protected body content, not a new editable field. Without the input the
    body is byte-identical to today. (Design concept Q3: autopilot drafts the note from
    spec.md's summary at PR Body Generation.)
  - The helper checks the note's structure only (non-empty, no nested fence, final-only).
    A repo-level test feeds a built final packet through `scripts/release_note_policy.py`
    for `feat` and `fix` titles. The runner does not vendor the policy (Q4: "Shape check
    + repo test"; host policy stays the host's).
  - `pr-packet-output` and `validate-pr-packet-write` apply succeed when the only
    untracked paths are the current packet's three canonical files (packet JSON,
    `body.md`, `validation.json`). A second packet, an unrelated file, a tracked edit,
    or a `git status` failure still refuses. Canonical paths move to a shared
    `pr_contract.py`.
  - The final body shows the current Phase 6.5 verdict under Verification, read from
    the workflow file. A blank Verdict cell (empty or still the template comment) blocks
    finalization; any recorded value (proceed, remediate, stop) renders as recorded
    (Q2: "Blank Verdict cell"; G6.5 stays advisory).
- US2 (P1, Slice B, gates and counters): As an operator, gates and counters report the
  true state of the spec.
  - G1-G4 and `count-markers` count `[Gap]` and `[Gap, <ref>]` alike with one shared pattern.
  - The spec-index walk uses tracked paths only (`git ls-files --cached`) and fails closed
    with a diagnostic when git fails (Q6). `refresh-release-artifacts.py` refreshes and
    `--check`s the spec index so `artifact-consistency` catches a stale tracked map.
    Update the AGENTS.md freshness row.
  - `estimate-spec-size` accepts `required_refactor_files` and adds 40 LOC per distinct
    file. A missing or invalid value adds nothing.
  - `detect-commands` reads `.specify/project-commands.json` first (Q1). The file may
    declare only `UNIT_TEST` and `FULL_VERIFY` (Q7). Bad JSON, an unknown key, or an
    empty or non-string value returns an input diagnostic with no marker fallback (Q8:
    "Error, no fallback"). `.specify/quality-gates.json` holds thresholds only;
    thresholds and the four quality slots are unchanged. This repository adds its own
    `.specify/project-commands.json` pointing at its documented quick and CI suites (Q9).
- US3 (P2, Slice C, workflow behavior, no production files): As an operator, PR review
  remediation and team-forming executors behave safely on large PRs and both hosts.
  - `speckit-resolve-pr` pages through every review thread and every thread's comments
    with `pageInfo` and cursors, and blocks mutation on a failed page. After verify and
    push, it compares the PR's fresh `headRefOid` with the pushed SHA before any reply
    or resolve; a mismatch leaves threads unresolved. Proof is a Layer 1 prose contract
    (Q10).
  - phase-, analyze-, checklist-, and implement-executor on both hosts state a teardown
    obligation for any team they form: collect each teammate result, request graceful
    shutdown, and report unconfirmed cleanup as unresolved. One Layer 1 structural test
    covers all eight definitions.
  - `speckit-status` shows the complete request envelope for `generate-spec-index-check`
    and `o5-topology`, each matched by a passing fixture.

### Constraints
- Every bug fix starts red: a fixture observed failing before the fix (constitution IX).
- Fail closed on missing or unparseable evidence (constitution IX).
- Two-host parity for every agent and skill change (constitution VIII).
- Regenerated `dist/`, runner manifests, hashes, and the spec index are committed with
  their sources (constitution VII).
- Each split PR: at most four production files and ten authored files.

### Out of Scope
- Post-list completion refusal and a single Post count (HRNS-018).
- Slice-row budget parsing and greenfield aggregation in the setup gate.
- Markdown-visibility rules for markers; code-span and fence exclusion for `[Gap]`.
- Legacy roadmap-link repair (#699 fixed the template).
- Redesigning the PR-packet schema or the post-implementation sequence.
- Changing any host repository's release-note policy, or vendoring this repository's
  policy into the runner (Q4).
- Making G6.5 a hard gate (Q2).
- Command slots other than UNIT_TEST and FULL_VERIFY in project-commands.json (Q7).
- Runtime child lifetime (HRNS-017); the broad status envelope sweep (HRNS-019);
  re-invoking estimate-spec-size at G3/G5 (ART-015).
- Already fixed: #637, #638, #531, #568, #896, #994.
```

### Specify Results

<!-- Fill in after running the command -->

| Metric | Value |
|--------|-------|
| Functional Requirements | <!-- e.g., FR-001 through FR-020 --> |
| User Stories | <!-- Count --> |
| Acceptance Criteria | <!-- Count --> |

### Files Generated

- [ ] `specs/hrns-015-autopilot-gate-pr-emission-repair/spec.md`

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

#### Session 1: Blind-spot sweep (callers and existing fixtures)

```text
/speckit-clarify Focus on blast radius, because the scaffold blind-spot pass did not run (wait deadline expired): find every caller and fixture of the G1-G4 counters, count-markers, _spec_index_walk_regular_files, estimate_spec_size, detect_commands, git_worktree_status, dirty_worktree_diagnostic, and build_packet_body. Which existing golden fixtures change output, which consumers assume marker-only detect-commands output, and does any caller rely on the filesystem walk including untracked files?
```

#### Session 2: PR packet contract (Slice A)

```text
/speckit-clarify Focus on the final PR packet: how the Phase 6.5 verdict renders under Verification (verdict only, or verdict plus mode and composite confidence); exactly what "blank" means for the Verdict cell; whether pr-packet.schema.json must record release_note or the input stays transient; how split packets carry the note; and the structural checks on the note (non-empty, no nested fence, final-only). Decisions already made: autopilot drafts the note (design concept Q3), the runner does not vendor release_note_policy.py (Q4), and only a blank verdict blocks (Q2).
```

#### Session 3: Command declaration and gate inputs (Slice B)

```text
/speckit-clarify Focus on .specify/project-commands.json and gate inputs: the file's exact schema and path resolution relative to repo_root; how declared commands interact with SINGLE_FILE_TEST and the other slots detect-commands fills; the diagnostic code for an invalid file (no fallback, Q8); what this repository's own file declares; the boundary with ART-015 for where required_refactor_files comes from; and the diagnostic when the tracked-only walk's git call fails (fail closed, Q6).
```

#### Session 4: Workflow-behavior contracts (Slice C)

```text
/speckit-clarify Focus on speckit-resolve-pr and executor teardown: the GraphQL page size and cursor loop for threads and per-thread comments; what "blocks mutation on a failed page" reports to the operator; the exact headRefOid comparison point after verify and push; the wording each of the eight executor definitions must carry so one Layer 1 test can pin it on both hosts; and which fixture backs each speckit-status envelope.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Blind-spot sweep | | |
| 2 | PR packet contract | | |
| 3 | Command declaration and gate inputs | | |
| 4 | Workflow-behavior contracts | | |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/hrns-015-autopilot-gate-pr-emission-repair/plan.md`

### Plan Prompt

```text
/speckit-plan

## Tech Stack
- Runtime: Python 3.11+ stdlib-only runner `speckit-pro/speckit_pro_runner/` (one JSON request on stdin, one JSON response on stdout); helper ids in `helpers/registry.py`
- Plugin surfaces: Claude skills and agents (`speckit-pro/skills/`, `speckit-pro/agents/`), Codex overlays and TOML (`speckit-pro/codex-skills/`, `speckit-pro/codex-agents/`)
- Repo tooling: `scripts/refresh-release-artifacts.py`, `scripts/release_note_policy.py`
- Testing: `tests/speckit-pro/` layers declared in `suite-manifest.json` (Layer 1 structural, Layer 4 unit, Layer 7 parity); ruff and mypy via `scripts/run-python-lint.py`

## Design Concept
Re-read docs/ai/specs/.process/HRNS-015-design-concept.md. Decisions that drive planning:
- Q1 "New .specify file": host repositories declare commands in `.specify/project-commands.json`.
- Q2 "Blank Verdict cell": only an empty or template-comment Verdict cell blocks the final packet.
- Q3 "Autopilot drafts it": autopilot drafts the release note from spec.md's summary at PR Body Generation.
- Q4 "Shape check + repo test": structural note check in the helper; a repo-level test runs release_note_policy.py.
- Q5 "Three PRs, A/B/C": three split PRs in roadmap order, each <= 4 production / 10 authored files.
- Q6 "Fail closed": tracked-only walk returns a diagnostic when git fails.
- Q7 "UNIT_TEST, FULL_VERIFY only"; Q8 "Error, no fallback" on an invalid file; Q9 this repo ships its own file.
- Q10 "Layer 1 prose contract" for speckit-resolve-pr paging and SHA check.

## Module and Interface Deltas (carry verbatim from the design concept)
- `speckit-pro/speckit_pro_runner/helpers/pr_packet.py`: changed. Optional `release_note` input on final (single and split) packets, rendered as one ```release-note fence after Known Gaps; drafts never carry one; structural check only (non-empty, no nested fence, final-only). Reads the Phase 6.5 Verdict row from the workflow file, renders it under Verification, and blocks finalization when the cell is blank or still the template comment (Q2, Q3, Q4; roadmap Module and Interface Deltas).
- `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json`: changed only if the packet records the note (roadmap).
- `speckit-pro/speckit_pro_runner/helpers/pr_contract.py`: new. Canonical packet paths (`<feature>/.process/pr-packets/<id>.json`, `<id>/body.md`, `<id>/validation.json`) shared by `pr_packet.py` and `mutation.py` (evidence: `canonical_packet_paths` in `pr_packet.py`).
- `speckit-pro/speckit_pro_runner/helpers/mutation.py`: changed. Packet apply succeeds when the only untracked paths are the current packet's three canonical files; a second packet, an unrelated file, a tracked edit, or a `git status` failure still refuses (roadmap).
- `speckit-pro/speckit_pro_runner/helpers/read_only.py`: changed. One shared `[Gap]` / `[Gap, <ref>]` pattern for G1-G4 and `count-markers`; tracked-only spec-index walk that fails closed on git failure (Q6); `estimate-spec-size` accepts `required_refactor_files` (+40 LOC per distinct file, missing or invalid adds nothing); `detect-commands` reads `.specify/project-commands.json` first (Q1, Q7, Q8).
- `.specify/project-commands.json`: new interface. JSON object with optional string keys `UNIT_TEST` and `FULL_VERIFY` only. Unknown keys, bad JSON, empty or non-string values return an input diagnostic with no marker fallback (Q1, Q7, Q8). This repository adds its own copy in Slice B (Q9).
- `scripts/refresh-release-artifacts.py`: changed. Refreshes and `--check`s the spec index so `artifact-consistency` catches a stale tracked map; `AGENTS.md` freshness row updated (roadmap).
- Autopilot packet guidance (`speckit-autopilot` post-implementation reference): changed. States the untracked-packet outcome and that autopilot drafts the release note from `spec.md`'s summary at PR Body Generation (Q3; roadmap).
- `speckit-pro/skills/speckit-resolve-pr/SKILL.md`: changed. Paged GraphQL for threads and comments (`pageInfo`, cursors), block mutation on a failed page, compare fresh `headRefOid` with the pushed SHA before any reply or resolve (roadmap; Q10).
- Four executor definitions in `speckit-pro/agents/` (phase-, analyze-, checklist-, implement-executor) and their generated Codex TOML: changed. Teardown obligation text (roadmap).
- `speckit-pro/skills/speckit-status/SKILL.md`: changed. Complete request envelopes for `generate-spec-index-check` and `o5-topology` (roadmap).
- Grey box: internal structure of the shared Gap pattern and of the project-commands loader is the implementer's choice.

## Constraints
- Constitution IX: each fix starts with a fixture observed failing; gates fail closed.
- Constitution VIII: Claude and Codex surfaces change together.
- Constitution VII: regenerate dist/, runner manifests and hashes, and the spec index; never hand-edit them.
- Reviewability: plan the three slices as separately reviewable PRs (A, B, C) with <= 4 production and <= 10 authored files each. Do not exceed by moving work between slices without recording it.
- Without `release_note`, the final body must stay byte-identical to today.

## Architecture Notes
- Extract canonical packet paths into `helpers/pr_contract.py` and import from both `pr_packet.py` and `mutation.py`; do not duplicate the path formulas.
- Keep the runner free of imports from repo-root `scripts/` (the plugin ships without them).
- New helper inputs go through the existing strict-input and registry contracts; update fixture manifests accordingly.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ⏳ | Technical context, execution flow |
| `research.md` | ⏳ | Decision rationales (if needed) |
| `data-model.md` | ⏳ | Entities and types |
| `contracts/` | ⏳ | API specifications |
| `quickstart.md` | ⏳ | Developer onboarding |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan` — validates both spec AND plan together. Run multiple times for different domains.

**Best Practice:** Don't guess which domains to check. Analyze the spec first, then generate enriched prompts with spec-specific focus areas.

### Step 1: Analyze Spec for Recommended Domains

Before running any checklists, read `spec.md` and `plan.md` and identify which domains apply. Match them against the signal table in the speckit-coach skill's `references/checklist-domains-guide.md`. That guide is the single list of checklist domains; do not keep a second copy here.

**Target: 2-4 domains.** Prioritize domains where the spec has the most complexity or risk.

Recommended from the design tree (interface, errors, verification, rollout branches): api-contract, error-handling, testing.

### Step 2: Run Enriched Checklist Prompts

For each domain, include spec-specific focus areas in the prompt — not just the bare domain name.

#### 1. api-contract Checklist

Why this domain: the spec changes three runner request contracts (final packet input, estimate-spec-size input, detect-commands source) and adds a new `.specify/project-commands.json` interface.

```text
/speckit-checklist api-contract

Focus on Autopilot, Gate, and PR-Emission Repair requirements:
- release_note input: final-only, structural checks, placement after Known Gaps, byte-identical body when absent
- required_refactor_files: accepted types, distinct-file counting, missing and invalid values
- .specify/project-commands.json: allowed keys (UNIT_TEST, FULL_VERIFY only), path resolution, precedence over marker detection
- speckit-status request envelopes for generate-spec-index-check and o5-topology match runnable fixtures
- Pay special attention to: whether pr-packet.schema.json changes and whether registry and fixture manifests stay in sync
```

#### 2. error-handling Checklist

Why this domain: several decisions are fail-closed rules (git failure, invalid command file, blank verdict, failed review page, SHA mismatch).

```text
/speckit-checklist error-handling

Focus on Autopilot, Gate, and PR-Emission Repair requirements:
- Packet apply refusals: second packet, unrelated untracked file, tracked edit, git status failure
- Tracked-only spec-index walk fails closed when git is missing, errors, or times out (Q6)
- Invalid project-commands.json returns a diagnostic with no fallback (Q8)
- Blank Phase 6.5 Verdict blocks finalization with an actionable diagnostic (Q2)
- Pay special attention to: speckit-resolve-pr behavior on a failed page and on a headRefOid mismatch (no reply, no resolve)
```

#### 3. testing Checklist

Why this domain: every fix must start red, and Slice C is proven only by Layer 1 prose contracts.

```text
/speckit-checklist testing

Focus on Autopilot, Gate, and PR-Emission Repair requirements:
- Each Done When item maps to a fixture observed failing before the fix
- Repo-level test runs a built packet through scripts/release_note_policy.py for feat and fix titles
- Frozen pre-fix stale SPEC-MOC.md fixture for refresh-release-artifacts --check
- One Layer 1 test pins all eight executor definitions' teardown obligation across both hosts
- Pay special attention to: Layer 1 contract coverage for speckit-resolve-pr (>100 threads, multi-page comments, failed page, SHA mismatch) and suite-manifest layer registration
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| api-contract | | | |
| error-handling | | | |
| testing | | | |
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
- Small, complete behavioral units
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: foundation → components → integration → validation
- Mark parallel-safe tasks explicitly with [P]
- Organize by user story, not by technical layer
- Keep related test and implementation checkboxes in one closed TDD unit;
  each unit must fit an adjacent batch of at most four tasks
- Write a setup or foundation gate task as a candidate check that can finish
  before source work starts. Attach any reconciliation against the actual diff,
  actual LOC, or an implementation checkpoint to the emission step. G5 rejects
  a gate task that waits on evidence only its own dependents produce.
- Open a check-only task (one that changes no code) with a verification verb:
  `verify`, `run`, `check`, `build`, `lint`, `confirm`, `recheck`. The scheduler
  routes only these to verification; any other leading verb routes the task
  as implementation or research work. Open implementation work with
  `Implement`, `Add`, or `Create`
- When tasks.md includes a requirement coverage table, fill every row's task
  cell from the task list above, for every requirement. G5 fails a row whose
  task cell is blank or a placeholder such as `()`
- Every fix task pair starts with a failing fixture (RED) before the implementation (constitution IX)

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
1. Foundation: `helpers/pr_contract.py` shared canonical packet paths
2. US1 / Slice A (P1): release_note, untracked-packet apply exemption, Phase 6.5 verdict
3. US2 / Slice B (P1): shared Gap pattern, tracked-only spec index + --check, required_refactor_files, project-commands.json (+ this repo's file)
4. US3 / Slice C (P2): speckit-resolve-pr paging and SHA check, executor teardown (8 definitions), speckit-status envelopes
5. Polish: regenerate dist/ and runner trust files, AGENTS.md freshness row, packet guidance

## Constraints
- Bound tasks by the design concept Non-goals; flag any task that touches PR-packet schema redesign, Post-list completion (HRNS-018), runtime child lifetime (HRNS-017), the broad envelope sweep (HRNS-019), G3/G5 re-invocation (ART-015), extra command slots, or vendoring release_note_policy.py.
- Keep each story's tasks within its slice's budget: <= 4 production files and <= 10 authored files.
- Unit tests in tests/speckit-pro/unit/ with fixtures under tests/speckit-pro/unit/fixtures/; structural tests in Layer 1; register layers in tests/speckit-pro/suite-manifest.json.
- Claude agent and Codex TOML changes land in the same task unit (constitution VIII).
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

To produce the decision, send the complete read-only runner request:

```json
{
  "schema_version": "1.0",
  "request_id": "atomicity-route-HRNS-015",
  "helper_id": "atomicity-route",
  "operation": "atomicity-route",
  "mode": "read_only",
  "inputs": {
    "feature_dir": "specs/hrns-015-autopilot-gate-pr-emission-repair",
    "workflow_file": "docs/ai/specs/.process/HRNS-015-workflow.md"
  }
}
```

The workflow path excludes this exact workflow and its sibling
`autopilot-state.json` from change classification. If an older workflow has
the positional instruction, replace only that instruction and preserve all
phase status and operator-authored content.


---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```text
/speckit-analyze

Focus on:
1. Constitution alignment — principles IV, VII, VIII, IX (tests before merge, regenerated artifacts, two-host parity, fail-closed and red-first)
2. Coverage gaps — ensure all FRs and user stories have tasks, and every roadmap Done When item has a failing-first fixture task
3. Consistency between task file paths and actual project structure
4. Verify P1 user stories (US1, US2) have complete task coverage
5. Cross-check spec.md, plan.md, and tasks.md against docs/ai/specs/.process/HRNS-015-design-concept.md: Goals, Non-goals, decisions Q1-Q10, Module and Interface Deltas, and Verification Gates. The design concept is the source of truth for scoping decisions; a downstream artifact that contradicts it is wrong unless it carries an explicit revision note.
6. Slice budgets: each of Slice A, B, C within 4 production and 10 authored files
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

Read tasks.md, plan.md, and docs/ai/specs/.process/HRNS-015-design-concept.md. Consult the design concept's Q&A log for the "why" behind each decision when writing tests and handling edge cases. Surface any design-concept decision not reflected in tasks.md as a gap before coding; do not drop it silently.

## Approach: TDD-First

For each task, follow this cycle:

1. **RED**: Write failing test defining expected behavior
2. **GREEN**: Implement minimum code to make test pass
3. **REFACTOR**: Clean up while tests still pass
4. **VERIFY**: Manual verification of acceptance criteria

### Pre-Implementation Setup

Before starting any task:
1. Work from the worktree on branch hrns-015-autopilot-gate-pr-emission-repair
2. Run the quick suite `python3 tests/speckit-pro/run-all.py` and confirm it passes before changes
3. No docs-site commands are expected; if one becomes necessary, run `pnpm --dir docs-site install --frozen-lockfile` first

### Verification Gates (carry verbatim from the design concept)
- Quick suite: `python3 tests/speckit-pro/run-all.py` passes (evidence: `AGENTS.md` Commands table).
- CI suite: the `run-ci-suite.json` runner request in `AGENTS.md` passes, including layers 6 and 7 (evidence: `AGENTS.md`).
- `python3 scripts/refresh-release-artifacts.py --check` passes after regeneration; fails on a frozen pre-fix stale `SPEC-MOC.md` fixture and passes with an untracked file present (roadmap Done When).
- Unit fixtures, each failing first: `release_note` present/absent (absent body byte-identical, draft has no fence); a repo-level test feeds a built final packet through `scripts/release_note_policy.py` for a `feat` and a `fix` title (Q4); packet apply success and each refusal case; Phase 6.5 verdict present and blank; `[Gap]` and `[Gap, <ref>]` in G1-G4 and `count-markers`; `estimate-spec-size` refactor count, missing, invalid; `detect-commands` declared command wins, and invalid file errors (Q8); tracked-only walk fails closed on git failure (Q6).
- Layer 1 structural tests: one test fails when any of the eight executor definitions loses its teardown obligation; one asserts `speckit-resolve-pr` SKILL.md carries paged thread and comment queries, stop-on-failed-page, and the `headRefOid` check before reply/resolve (Q10); each documented `speckit-status` envelope matches a passing fixture.
- Reviewability: each split PR within 4 production files and 10 authored files (Q5; roadmap budget).
- Formal methods: none. The changes are deterministic input validation, path-set predicates, and prose contracts with no concurrency or state machine that ordinary fixtures cannot cover (evidence: roadmap Scope; no question needed).

### Implementation Notes
- Python changes also pass `scripts/run-python-lint.py run ruff` and `run mypy` (constitution IV).
- Regenerate dist/ and runner trust files with `python3 scripts/refresh-release-artifacts.py`; never hand-edit them.
- Codex TOML for the four executors is generated; edit the Claude source and regenerate.
- At PR Body Generation, draft the release note from spec.md's summary and pass it as `release_note` (Q3).
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Foundation | | | |
| 2 - US1 Slice A | | | |
| 3 - US2 Slice B | | | |
| 4 - US3 Slice C | | | |
| 5 - Polish | | | |

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
├── speckit-pro/
│   ├── speckit_pro_runner/helpers/   # pr_packet.py, mutation.py, read_only.py, (new) pr_contract.py
│   ├── skills/                       # speckit-autopilot, speckit-resolve-pr, speckit-status
│   ├── agents/                       # Claude executor definitions
│   ├── codex-skills/, codex-agents/  # Codex overlays and generated TOML
│   └── dist/                         # generated payloads (regenerate, never hand-edit)
├── scripts/                          # refresh-release-artifacts.py, release_note_policy.py
├── tests/speckit-pro/                # run-all.py, suite-manifest.json, unit/, layer tests
├── .specify/                         # SpecKit config; (new) project-commands.json
├── docs/ai/specs/                    # roadmaps; .process/ workflow and design concept
└── specs/hrns-015-autopilot-gate-pr-emission-repair/
```

---
