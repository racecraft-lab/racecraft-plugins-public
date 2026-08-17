# SpecKit Workflow: ART-007 — Draft-PR Emission

**Template Version**: 1.0.0
**Created**: 2026-08-17
**Purpose**: Executable workflow for the ART-007 autopilot run. The prompts below are what each phase executes.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/ART-007-design-concept.md
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
| Specify | `/speckit-specify` | ✅ Complete | G1 pass — 12 FRs, 3 user stories, 12 acceptance scenarios, 8 success criteria, 3 colon-form markers routed to Clarify |
| Clarify | `/speckit-clarify` | ⏳ Pending | Sessions verify the settled Q1–Q7 decisions and pin the two protocol details |
| Plan | `/speckit-plan` | ⏳ Pending | |
| Checklist | `/speckit-checklist` | ⏳ Pending | error-handling, state-management |
| Tasks | `/speckit-tasks` | ⏳ Pending | |
| Analyze | `/speckit-analyze` | ⏳ Pending | |
| Confidence Gate | G6.5 | ⏳ Pending | Pre-Implement composite confidence |
| Implement | `/speckit-implement` | ⏳ Pending | |
| Post | Post-Implementation | ⏳ Pending | Canonical 12-item closeout |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⏭️ Skipped | ⚠️ Blocked

G6.5 is advisory by default, so no phase of the main loop flips its row. Leaving
it Pending is legitimate and does not make the rows below it read as out of
order; record the verdict in [Phase 6.5](#phase-65-confidence-gate) when the
gate runs.

Note the self-reference in this spec's subject: ART-007 *builds* the plan-stage
draft-PR emission, so this run's own plan stage still ends the pre-ART-007 way
(G6.5 → boundary commit → STOP, no draft PR). The draft-PR behavior this spec
ships takes effect for later specs' runs.

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
| I. Plugin Structure Compliance | `agents/artifact-author.md` carries valid agent frontmatter; the Codex mirror lands in `codex-agents/` | Layer 1 (`run-all.py --layer 1`) + Codex parity checks |
| II. Cross-Platform Runtime & Script Safety | Draft-packet and corroboration helper logic stays Python 3.11+ stdlib; no new Bash or `jq`; `gh` is invoked only as the existing PR-creation boundary already does | Layer 4 Bash-confinement and active-path guards |
| IV. Test Coverage Before Merge | Layer 4 golden fixtures for the draft-mode packet path, including the fail-open artifact-generation branch and the corroboration discrepancy cases; Layer 5 agent verification for `artifact-author` on both platforms | Layer 4 + Layer 5 suites |
| VI. KISS, Simplicity & YAGNI | Draft mode extends `pr-packet.schema.json` with a third `mode` value and conditional relaxation — no sibling schema, no parallel validator family (Design Concept Q1) | Code review against Design Concept Q1 |

**Constitution Check:** ✅ (no conflicts identified during scoping; verify again after Plan)

### Feature State (namespaced branch)

| Field | Value |
|-------|-------|
| Feature dir | pinned via `.specify/feature.json` (gitignored) to `specs/art-007-draft-pr-emission` |
| `ON_FEATURE_BRANCH` | expected **true** — the runner's `check-prerequisites` recognizes namespaced worktree branches (`worktree=true,feature=true`, per the ART-012 run). The `feature.json` pin still serves the vendored `check-prerequisites.sh` path the `/speckit-*` phase commands call internally, whose `^[0-9]{3}-` regex does not match this repo's namespaced spec IDs. |
| `before_specify` → `speckit.git.feature` (`optional: false`) | **SKIP** — the branch already exists and is checked out in this worktree; the hook's purpose is satisfied |

### Reviewability Setup Gate (recorded at scaffold time)

Runner helper `reviewability-gate` in setup mode against the technical roadmap
returned `status: "warn", pass: true` with the single warning
`primary surfaces 3 exceeds warn threshold 1`. That count comes from the
helper's whole-roadmap scan; ART-007's own recorded budget is one primary
surface (harness/adapter). Warnings may proceed when the workflow records the
scope budget and split decision, which the rest of this subsection does.

**Scope budget:** projected ~287 reviewable LOC (modify-weighted), ~10
production files, ~14 total files, one primary surface (harness/adapter).
The roadmap entry's declared 217 LOC / ~6 production files predates the
scoping interview's Q5 decision to absorb the gh corroboration limb ART-006
deferred here (costed at ~70 LOC when ART-006 estimated it) plus the packet
schema, both agent definitions, and the workflow-template row. See the
roadmap entry's scaffold amendment note.

**Known file-count tension (recorded, not resolved here):** ~10 production
files sits above the PR-time warn threshold (6) and near the block threshold
(8). The LOC projection — the primary sizing signal — stays well under the
400 warn ceiling, and the scope has no horizontal seam to re-slice: every
file serves the one vertical capability (generate → commit → draft PR →
stop report), and the platform mirrors are parity obligations, not layers.
If the PR-time diff gate warns or blocks on file count, normal PRSG layer
planning and marker-split emission govern, and Design Concept Q2 already
fixes the draft-PR semantics for a split (the draft becomes the first slice
PR). The Plan phase should still look for legitimate surface trims — e.g.
whether the `workflow-template.md` row addition can ride the
workflow-file-protocol change, and whether the Codex side shares reference
docs or mirrors them per file (verify in-tree; do not assume).

**Split decision (grill-me slice-sizing):** one vertical slice, no split.
Advisory `estimate-spec-size` with the enriched post-interview signals
(3 user stories, 10 production files, 12 FRs, modify-weighted) returned
`{"estimated_loc": 327, "status": "ok", "suggested_slices": 1}` — verbatim
output, no hand adjustment. 327 sits under the 400 warn ceiling and the
slice is end-to-end (artifact generation → commit → draft PR → stop
report), so no split question was warranted.

### Phase 0 Prerequisites (recorded at run time, 2026-08-17)

Stage resolution (Step 0.6c): `Stage: plan (argv) — explicit --stage plan`.
The state slot was reclaimed from
`docs/ai/specs/.process/ART-003-slice-3-workflow.md` (prior status:
`completed_archived`).

| Check | Result |
|-------|--------|
| `check-prerequisites` | `all_pass: true` — CLI `specify 0.11.8`, project initialized, constitution present, all SpecKit commands installed, workflow file exists, `branch: art-007-draft-pr-emission` (`worktree=true,feature=true`) |
| `detect-commands` | stack `python`; `UNIT_TEST` / `FULL_VERIFY` = `python3 tests/speckit-pro/run-all.py`; `BUILD` / `TYPECHECK` / `LINT` = `N/A` (evidence: `tests/speckit-pro/run-all.py`) |
| `detect-presets` | `speckit-pro-reviewability` v1.0.0 resolves spec/plan/tasks templates; 18 hook events configured |
| `resolve-confidence-mode` | `advisory` (no `--strict` / `--advisory` flag, no local config file) |
| Settings | no `.claude/speckit-pro.local.md` — defaults: consensus `tier-a`, gate-failure `stop`, auto-commit on |
| Extensions installed | `archive`, `git`, `verify` per `.specify/extensions.yml`; hooks also reference `verify-tasks` and `retrospective` |
| `PROJECT_IMPLEMENTATION_AGENT` | none detected in `.claude/agents/` (only `plugin-release-auditor`, `speckit-skill-reviewer`) → fallback `speckit-pro:phase-executor` |
| `AGENT_TEAMS_AVAILABLE` | **true** — `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` set and Claude Code 2.1.234 ≥ 2.1.32 |
| Archive sweep | **no-op, no mutations** — `specs/art-007-draft-pr-emission` excluded as the current target; `specs/brand-001-racecraft-identity-system` not proven merged (its only merged PR #432 is scaffold provenance, not implementation merge provenance; dir holds only SPEC-MOC.md, status "pending") and left in active specs |
| Tier-2 relocation | no candidate surfaced — `brand-001-racecraft-identity-system` suppressed (`non_speckit_namespace`); the current target suppressed (frozen/in-flight, named by `.specify/feature.json`) |

**G0 test-count baseline (preserve; do not recompute):** `python3
tests/speckit-pro/run-all.py` → **7399/7399 passed** (L1 1447, L4 5766,
L5 186), toolchain preflight ok, exit 0. G7 verifies the count *increased*
against this number, so a later `--stage implement` run in a fresh session
MUST read it from here rather than re-measuring a tree that already contains
this spec's additions.

**Constitution validation:** the only runnable `PROJECT_COMMANDS` gate for
this stack is the test suite, and it passes at the baseline above.
`TYPECHECK`, `LINT`, and `BUILD` are `N/A` for a Markdown-plus-stdlib-Python
surface, so no principle has an unrun check. Principles I, II, IV, and VI
show no conflict with this spec's scope; re-verify after Plan.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | ART-007 |
| **Name** | Draft-PR Emission |
| **Branch** | `art-007-draft-pr-emission` |
| **Stage** | plan |
| **Dependencies** | ART-002 (Draft-PR Template Set) — complete, PRs #425/#427/#430; ART-006 (Autopilot Staging) — complete, PR #422 |
| **Enables** | ART-008 (Feedback Sweep); ART-010 (Final-PR Writeup, Companions & Ready Flip) |
| **Priority** | P1 |

### Success Criteria Summary

- [ ] A `--stage plan` run whose G6.5 resolves pass or warn ends with:
      committed `specs/<branch>/artifacts/*.html` selected per the gallery
      manifest routing, an open draft PR (`gh pr create --draft`) whose body
      carries the Artifacts index table (artifact, purpose, copy-paste open
      command), and a stop report showing the draft-PR URL, the artifact
      index, and resume instructions.
- [ ] The draft packet validates against `pr-packet.schema.json` with
      `mode: "draft"`; the implementation-evidence requirements
      (`verification_evidence`, `scope_evidence.changed_files`,
      `uat.how_to_uat`) are conditionally relaxed for draft mode only —
      `single` and `split` validation is unchanged (Q1).
- [ ] The draft PR's title is final-shape conventional
      (`<type>(<lowercase-scope>): <plain English description>`),
      self-validated locally against the release-readiness gate shape,
      decoupled from implementation evidence in draft mode (Q6).
- [ ] The draft-PR identity (number + URL) is recorded as a row on the
      workflow file's status surface — workflow file only, no state-file
      mirror (Q4).
- [ ] Stage auto-detect corroborates the workflow file's draft-PR row via
      `gh`; on disagreement it logs a discrepancy and the workflow file wins
      (the inherited OQ-4 contract, Q5).
- [ ] A strict-mode G6.5 block opens **no** draft PR: the run takes the
      boundary commit and STOPs per the existing terminal-step contract, and
      the stop report names the blocked gate instead of a URL (Q3).
- [ ] Artifact generation is fail-open: a generation failure logs a gap and
      never blocks the draft PR; a zero-artifact failure still opens the PR
      with a gap-marked index (roadmap mandate).
- [ ] Both platforms carry identical behavior
      (`speckit-pro/skills/speckit-autopilot/` and
      `speckit-pro/codex-skills/speckit-autopilot/`; `agents/` and
      `codex-agents/`), proven by the parity checks.
- [ ] None of the twelve governed Layer 6 corpus agent definitions is
      edited; `artifact-author` ships outside the corpus with membership
      tracked as an ART-009 deferral (Q7).

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/art-007-draft-pr-emission/spec.md`

### Specify Prompt

```text
/speckit-specify End the autopilot plan stage at a committed draft artifact
set and an open draft PR whose body indexes the artifacts, then stop for
human review.
```

#### Detailed Prompt (for complex specs)

```text
/speckit-specify

## Feature: Draft-PR Emission (ART-007)

### Problem Statement
The plan stage (ART-006) ends at the G6.5 boundary commit and STOPs, but
nothing durable reaches a human reviewer: the planning artifacts sit on an
unpushed-to-PR branch with no review surface, no early feedback channel, and
no recorded hand-off. ART-002 shipped four draft-stage HTML templates with
fill-regions and manifest routing, but nothing authors them. ART-008 (feedback
sweep) and ART-010 (ready flip) both presuppose a draft PR that does not yet
exist, and ART-006's stage auto-detect carries a deferred gh-corroboration
limb with no draft PR to corroborate against.

### Users
- The autopilot orchestrator (plan-stage terminal step), which dispatches
  artifact generation, commits, opens the draft PR, and stops.
- The `artifact-author` subagent (new, both platforms), which reads spec.md /
  plan.md / tasks.md / the design concept and fills the ART-002 templates.
- The human reviewer, who receives a draft PR indexing the planning
  artifacts and reviews before implementation starts.
- ART-008's feedback sweep and ART-010's ready flip (downstream consumers,
  out of scope here), which find the PR through the workflow file's
  draft-PR row.

### User Stories
- As the autopilot orchestrator, when G6.5 resolves pass or warn on a plan
  stage, I generate the draft artifacts, commit them review-visible under
  specs/<branch>/artifacts/, open a draft PR whose body indexes them, record
  the PR identity in the workflow file, and stop with a report carrying the
  URL, the index, and resume instructions.
- As the artifact-author subagent, I select templates per the gallery
  manifest routing (implementation-plan and spec-explainer always;
  code-approaches on competing_approaches; module-map on brownfield_change),
  fill the fill-regions from the planning artifacts, and fail open — a
  generation failure logs a gap and never blocks the draft PR.
- As stage auto-detect, I corroborate the workflow file's draft-PR row via
  gh, log a discrepancy when they disagree, and treat the workflow file as
  authoritative (the inherited OQ-4 contract).

### Constraints
- Draft-PR creation goes through the existing packet machinery: extend
  pr-packet.schema.json with mode "draft" and conditionally relax the
  implementation-evidence requirements for draft mode only (Design Concept
  Q1). single/split validation is byte-for-byte unchanged.
- No draft PR on a strict-mode G6.5 block: the existing terminal-step
  contract (boundary commit, non-terminal blocked row, STOP) is preserved
  unchanged; emission runs only on pass or warn (Q3).
- Final-shape conventional title, self-validated against the
  release-readiness gate shape; minimal body — Artifacts index table plus a
  resume/status block; no release-note fence at draft time (pr-checks.yml
  skips every job while a PR is draft; ART-010 adds the fence at flip) (Q6).
- Draft-PR identity lives in the workflow file only (Q4).
- When a later marker-split is required, the draft PR becomes the first
  slice PR of the stack (Q2 — the OQ-1 resolution; encode as settled, do
  not re-open).
- Fail-open everywhere in generation: gap-marked index row, stop-report
  note, workflow-file note; zero artifacts still opens the PR.
- Platform parity: identical instructions in both skill variants; the agent
  ships as agents/artifact-author.md + the codex-agents mirror.
- Do not edit any of the twelve governed Layer 6 corpus agent definitions;
  artifact-author ships outside the corpus (tracked ART-009 deferral, Q7).
- Reviewability budget: ~287 reviewable LOC (modify-weighted), ~10
  production files, ~14 total files, primary surface harness/adapter.
  Advisory estimate-spec-size (3 user stories, 10 production files, 12 FRs,
  modify-weighted) returned {"estimated_loc": 327, "status": "ok",
  "suggested_slices": 1} — one vertical slice, no split.

### Out of Scope
- Reading or acting on PR feedback (ART-008); flipping the draft to ready
  and the final writeup (ART-010).
- Layer 6 corpus membership for artifact-author (tracked deferral to
  ART-009, which already opens the corpus for its rename surgery).
- Any hosting layer for artifacts — committed review-visible and opened
  locally over file:// (roadmap Key Decision, 2026-07-28).
- A state-file mirror of the draft-PR identity.
- Changes to G6.5 semantics, gate thresholds, or the boundary-commit
  contract.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | FR-001 through FR-012 (12) |
| User Stories | 3 (US1 orchestrator emission P1; US2 artifact-author generation P2; US3 auto-detect corroboration P3) |
| Acceptance Criteria | 12 acceptance scenarios (US1=4, US2=5, US3=3) + 7 edge cases |
| Success Criteria | SC-001 through SC-008 (8) |
| `[NEEDS CLARIFICATION]` markers | 3 — all colon form, at FR-007 (re-entry with an existing draft-PR row: NEW fork, not from the design concept), FR-009 (row name/format/placement — clarify session focus 1), FR-011 (discrepancy log format and per-class behavior — clarify session focus 2) |

**G1 PASS (routing: Clarify required).** Runner `validate-gate` returned
`{"gate":"G1","pass":true,"reason":"spec.md exists with 0 markers","markers":0}`.
That helper counts only the bare literal; an independent
`/usr/bin/grep -c "NEEDS CLARIFICATION"` shows **3** colon-form markers
(spec.md lines 201, 213, 223), so Clarify runs on real input. A privacy grep
(`/(Users|home)/`) confirms no absolute path leaked into either authored file.

The spec's own Reviewability Budget re-derives the figures this workflow
records under the Reviewability Setup Gate: primary surface harness/adapter,
~287 projected reviewable LOC (modify-weighted), ~10 production files, ~14
total files, within budget, one slice, no exception claimed.

### Files Generated

- [x] `specs/art-007-draft-pr-emission/spec.md`
- [x] `specs/art-007-draft-pr-emission/checklists/requirements.md`

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

The Design Concept interview settled every major fork (Q1–Q7) and left two
protocol-level details deliberately open. Sessions 1 and 2 pin those two
details; session 3 verifies the settled decisions were encoded rather than
re-opened.

### Clarify Prompts

#### Session 1: Draft-PR Row Protocol

```text
/speckit-clarify Focus on the draft-PR row: exact row name, columns, and
placement on the workflow file's status surface (against
references/workflow-file-protocol.md); when the row is written (after gh pr
create succeeds); which commit carries it (its own bookkeeping commit after
the boundary commit, following the existing post-implementation PR-creation
pattern); and what the row reads before any PR exists.
```

#### Session 2: Corroboration Discrepancy Classes

```text
/speckit-clarify Focus on gh corroboration: enumerate the discrepancy
classes (PR closed vs PR missing vs URL/number mismatch vs gh unavailable),
the log sink and format for each, and what stage auto-detect does next in
each class given the workflow file always wins (Design Concept Q5, the
inherited OQ-4 contract). gh-unavailable must degrade to the workflow file
without logging a false discrepancy.
```

#### Session 3: Settled-Decision Verification

```text
/speckit-clarify Verify spec.md encodes the settled interview decisions
without re-opening them: draft becomes the first slice PR on a later
marker-split (Q2, the OQ-1 resolution stated as settled); no draft PR on a
strict-mode G6.5 block and the stop report names the blocked gate (Q3);
mode "draft" conditionally relaxes only the implementation-evidence
requirements while single/split validation is unchanged (Q1); the
fail-open zero-artifact case still opens the PR with a gap-marked index.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Draft-PR row protocol + FR-007 re-entry | 5 | All accepted, 0 to consensus. FR-007 rewritten: refresh-in-place with a dual existence test (workflow record OR live head-branch query); closed/merged PR routes to FR-011, never a second PR. FR-009 rewritten: single `Draft PR` linked row in Basic Information (never Workflow Overview), absent-before-creation is the legal empty state, no template placeholder. NEW FR-013: emission order = artifacts → boundary commit → push → create/refresh → record → separate bookkeeping commit; boundary-commit contract untouched. **Spec defect fixed:** the assumption that the boundary step pushes was false (the shipped boundary block has no push; the only shipped push lives in the post-G7 PR Creation Protocol) — the terminal step owns its push. Markers 3 → 1 |
| 2 | Corroboration discrepancy classes (FR-011) | 5 | Q1-Q3 accepted directly; Q4+Q5 through consensus. FR-011 rewritten as four paragraphs: closed six-status vocabulary (`match`, `no_record`, `skipped`, `pr_closed` carrying merged, `pr_missing`, `identity_mismatch` — only the last three are discrepancies), precedence order, classification inside the stage-resolution helper from one orchestrator-supplied by-branch observation; three sinks by role (envelope always, run-report line always, workflow file discrepancies-only); success-gated classification (only exit-0 + parseable JSON may assert a discrepancy — everything else is `skipped`, never a false `pr_missing`); `pr_closed` at emission = log + no reopen + no second PR + operator-actionable stop report (consensus overrode the executor's reopen recommendation). SC-001 gained the closed-or-merged carve-out; US3 scenario 4 and a new edge case added. Markers 1 → 0 |
| 3 | | | |

### Consensus Resolution Log

| # | Item | Categories | Analysts | Round | Outcome | Artifacts Edited |
|---|------|-----------|----------|-------|---------|------------------|
| 1 | How is "could not check" separated from "checked and the PR is missing", so gh-unavailable never logs a false discrepancy? (Session 2 Q4) | `[security]` | codebase-analyst, spec-context-analyst, domain-researcher (all 3, mandatory for `[security]`) | 1 | **3-of-3 AGREE, high confidence → success-gated classification.** Only an exit-0, parseable by-branch observation may produce a discrepancy; every other outcome is `skipped` with reason, degrades to the workflow file, and is never a discrepancy. Domain researcher strengthened the case empirically on gh v2.96.0: exit 4 does not fire for an invalid/revoked token (only for zero credentials), so exit-code mapping is even less reliable than proposed — the only safe discriminator is exit 0 plus parseable JSON, collapsed uniformly. Codebase analyst grounded the shape in `git_worktree_status` (unavailable never resolves to "clean") and `runner_identity_mismatch` (classification only after successful parse); spec-context analyst grounded it in the OQ-4 wording ("discrepancy" presupposes two known values) and ART-012's shipped fail-open sentence naming ART-007 as its precedent. | spec.md FR-011 paragraph 3, US3 scenario 4, gh assumption amendment |
| 2 | Emission-time behavior when the recorded draft PR is closed or merged (Session 2 Q5) | `[spec]`, `[codebase]` | spec-context-analyst, codebase-analyst | 1 | **2-of-2 PREFER B refined (0.90, 0.83; synthesizer 0.87), overriding the executor's reopen recommendation.** No `gh pr reopen` (zero shipped uses; mutation vocabulary is create/edit/comment-resolve only), no second PR, `Draft PR` row left intact as the durable pointer; discrepancy logged, stop report names the closed PR and the operator resume path (`gh pr reopen <number>` manually if the close was unintended). OQ-4 authority is epistemic, not actuation; closed and merged stay one response class, matching FR-007's existing tail sentence. Executor's dissenting Option A recorded for visibility. | spec.md FR-011 paragraph 4, SC-001 carve-out, new edge case; FR-007 tail kept verbatim |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/art-007-draft-pr-emission/plan.md`

### Plan Prompt

```text
/speckit-plan

## Tech Stack
- Runtime: speckit-pro plugin skills (Markdown SKILL.md + reference docs)
  plus Python 3.11+ stdlib runner helpers (`speckit_pro_runner/helpers/`)
  for draft-packet validation and stage-resolution corroboration parsing.
  No new Bash, no `jq` (constitution II).
- PR boundary: `gh pr create --draft` at the same trust boundary the
  existing post-implementation PR-creation step already uses.
- Agent: `speckit-pro/agents/artifact-author.md` (new) + the
  `speckit-pro/codex-agents/` mirror; templates and routing are ART-002's
  shipped `speckit-pro/artifact-gallery/manifest.json` (stage: draft-pr).
- Test suite: `python3 tests/speckit-pro/run-all.py` (Layer 4 golden
  fixtures + Layer 5 agent verification), Python 3.11+ stdlib only.
- Platforms: Claude Code (`speckit-pro/skills/`) and Codex CLI
  (`speckit-pro/codex-skills/`) — identical behavior, proven by
  validate-codex-skills / validate-codex-parity.

## Constraints
- Reviewability budget ~287 reviewable LOC (modify-weighted), ~10 production
  files, ~14 total files, primary surface harness/adapter (see the
  Reviewability Setup Gate in this workflow for the estimator output and the
  recorded file-count tension). Look for legitimate surface trims: whether
  the workflow-template.md row can ride the workflow-file-protocol change,
  and whether the Codex skill shares reference docs or mirrors them per file
  — verify in-tree, do not assume.
- Do not edit any of the twelve governed Layer 6 corpus agent definitions
  (that restales the hand-maintained digest chain). artifact-author ships
  outside the corpus; corpus membership is a tracked ART-009 deferral (Q7).
- Committed artifacts land under `specs/<branch>/artifacts/` and are NOT
  marked `merge=generated` (sibling per-feature artifacts are not marked
  either; revisit only on a real merge conflict).
- Plugin source changes must account for the generated artifact contract
  (payload regeneration) before the work is called done.
- Reference the Design Concept doc
  (docs/ai/specs/.process/ART-007-design-concept.md) if planning needs
  context beyond this prompt — it is the source of truth for every scoping
  decision (Q1–Q7) captured during grill-me.

## Architecture Notes
- **Emission sequence (Q3 notes):** artifact generation runs after G6.5
  resolves pass/warn and before the stage-boundary commit, so the artifacts
  ride the boundary commit's existing `git add specs/` enumeration; the
  boundary push is what makes `gh pr create --draft` possible; the draft-PR
  row write lands after PR creation as its own bookkeeping commit, following
  the existing post-implementation PR-creation pattern. On a strict-mode
  block the sequence short-circuits before generation: boundary commit,
  STOP, no PR (Q3).
- **Packet draft mode (Q1):** extend the `mode` enum with `"draft"` and
  conditionally relax `verification_evidence`,
  `scope_evidence.changed_files`, and `uat.how_to_uat` for draft mode only,
  using the same conditional pattern the schema already carries for
  `split_slice`. One schema, one validator family; ART-010 upgrades the same
  packet in place. Title validation in draft mode checks the conventional
  shape only, decoupled from diff/marker-split evidence.
- **Template routing:** manifest-driven, `stage: draft-pr` filter —
  implementation-plan + spec-explainer always; code-approaches on
  `competing_approaches` (producer: the design concept's "Alternatives
  offered" blocks); module-map on `brownfield_change` (producer: the
  primary-surface field). Signal producers per the ART-001 workflow's
  routing record.
- **artifact-author frontmatter:** mirror `uat-runbook-author`'s pattern
  (the closest shipped analogue: content-authoring, fail-open, PR-time
  dispatch) — verify its actual frontmatter by disk read before authoring,
  never from memory.
- **Fail-open sinks (Q6 notes):** a generation failure appears as a gap row
  in the PR body's Artifacts index, in the stop report, and as a note on the
  workflow file's draft-PR row; zero artifacts still opens the PR.
- **Corroboration (Q5):** auto-detect reads the draft-PR row, corroborates
  via `gh`, logs a discrepancy on disagreement, workflow file wins; the
  discrepancy classes and log sink come from Clarify session 2.
- **Draft body composition (Q6):** Artifacts index table (artifact, purpose,
  copy-paste `open` command) + resume/status block. No release-note fence,
  no verification sections — ART-010 owns the final body.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ⏳ | Technical context, execution flow |
| `research.md` | ⏳ | Decision rationales (if needed) |
| `data-model.md` | ⏳ | Entities and types |
| `contracts/` | ⏳ | Schema/contract specifications |
| `quickstart.md` | ⏳ | Developer onboarding |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan` — validates both spec AND plan together. Run multiple times for different domains.

**Best Practice:** Don't guess which domains to check. Analyze the spec first, then generate enriched prompts with spec-specific focus areas.

### Step 1: Analyze Spec for Recommended Domains

Signals in this spec: fail-open generation, gh failure paths, and discrepancy
handling (**error-handling**); the workflow-file draft-PR row lifecycle, stage
state interplay, and re-entry after a strict block (**state-management**).
No API endpoints, no user-facing UI authored here (the HTML templates shipped
in ART-002 and are filled, not designed), no database, no LLM prompt surface
beyond the agent definition the L5 suite already verifies.

**Target: 2-4 domains.** Two domains carry this spec's risk; a third is not
justified.

### Step 2: Run Enriched Checklist Prompts

#### 1. error-handling Checklist

Why this domain: the roadmap's one hard mandate is fail-open ("generation
failure logs a gap, never blocks the draft PR"), and the spec adds three new
external failure surfaces: artifact generation, `gh pr create`, and `gh`
corroboration.

```text
/speckit-checklist error-handling

Focus on Draft-PR Emission requirements:
- Fail-open artifact generation: partial set, zero-artifact set, and
  malformed-template cases each still open the draft PR with a gap-marked
  index; the gap reaches all three sinks (PR body index, stop report,
  workflow-file row note).
- gh pr create failure: what the stop report shows, what the workflow file
  records, and how a re-run recovers without a duplicate PR.
- Corroboration failure classes: PR closed, PR missing, URL/number mismatch,
  gh unavailable — each logs per Clarify session 2 and never blocks stage
  resolution (workflow file wins).
- Pay special attention to: the strict-mode G6.5 block path — it must
  short-circuit emission entirely, not fail open into a PR (Q3).
```

#### 2. state-management Checklist

Why this domain: the spec writes new durable state (the draft-PR row) into
the workflow file that three later specs and stage auto-detect read, beside
the stage state ART-006 shipped.

```text
/speckit-checklist state-management

Focus on Draft-PR Emission requirements:
- Draft-PR row lifecycle: absent before creation, written once after gh pr
  create succeeds, carried by its own bookkeeping commit, never mirrored
  into the state file (Q4).
- Re-entry: a plan stage re-run after a strict block emits the PR on the
  passing run; a re-run when the row already exists must not open a second
  PR.
- Stage auto-detect: the corroboration limb reads the row without changing
  the workflow-file-is-authoritative contract (Q5 / OQ-4).
- Pay special attention to: interrupted emission (artifacts committed but
  no PR opened; PR opened but row not yet written) — each intermediate
  state must resume to the correct terminal state.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
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

**When to run:** After checklists complete (all gaps resolved). Output: `specs/art-007-draft-pr-emission/tasks.md`

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
1. Foundation: pr-packet.schema.json draft mode + Layer 4 fixture skeletons
2. User Story 1 (P1): plan-stage terminal-step emission sequence
   (phase-execution.md both platforms), draft packet path
   (post-implementation.md), workflow-file draft-PR row
   (workflow-file-protocol.md + workflow-template.md)
3. User Story 2 (P1): artifact-author agent (both platforms) + manifest
   routing + fail-open branches
4. User Story 3 (P2): gh corroboration limb in stage auto-detect
   (SKILL.md both platforms + runner helper)
5. Polish: stop report wording, payload regeneration, parity verification

## Constraints
- Tests live under tests/speckit-pro/ (repository-only), never inside the
  shipped plugin directory; name them for durable capability, never for the
  spec ID.
- TDD: every new helper branch and fixture path gets its failing test first.
- The design concept's Non-goals bound generation: no corpus files, no
  state-file mirror, no release-note fence at draft time, no hosting layer.
  Flag any task that would cross those boundaries instead of silently
  emitting it.
- Payload regeneration and parity checks are explicit tail tasks, not
  assumptions.
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
runner helper atomicity-route specs/art-007-draft-pr-emission
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
1. Constitution alignment — stdlib-only helpers, no new Bash/jq, plugin
   structure for the new agent files
2. Coverage gaps — every FR and user story has tasks; the fail-open
   branches and every corroboration discrepancy class have test tasks
3. Design-concept drift — spec.md/plan.md/tasks.md against the settled
   Q1–Q7 decisions (draft schema mode, slice-1 semantics, no PR on strict
   block, workflow-row-only identity, corroboration limb in scope,
   final-shape title + minimal body, corpus deferral to ART-009); the
   design concept wins unless a revision note says otherwise
4. Roadmap consistency — the ART-007 scaffold amendment and the ART-009
   corpus-membership deferral note stay accurate
5. Budget re-derivation — the spec's declared budget still matches the
   Reviewability Setup Gate record in this workflow
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
1. Run `python3 tests/speckit-pro/run-all.py` and record the passing
   baseline before any change.
2. Verify the worktree is on `art-007-draft-pr-emission` and clean.
3. Re-read the Design Concept doc for the Q1–Q7 decisions before touching
   the surfaces they govern.

### Implementation Notes
- Shipped-byte changes require the payload/proof regeneration ritual before
  completion (`scripts/refresh-release-artifacts.py`; rsync with
  --checksum; release-readiness last).
- A tracked .md/.py/.sh change under tests/speckit-pro/ additionally
  requires `pnpm --dir docs-site reference:generate` (deps are installed in
  this worktree).
- Do not touch the twelve governed corpus agent definitions; artifact-author
  stays outside the corpus in this spec (Q7).
- Bracket-class regex boundaries, not \b, in anything grep-adjacent
  (BSD/GNU portability); helpers stay stdlib-only, shell=False, argument
  arrays (constitution II).
- Both skill variants and both agent surfaces change together; parity checks
  are part of done, not a follow-up.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Foundation | | | |
| 2 - User Story 1 | | | |
| 3 - User Story 2 | | | |
| 4 - User Story 3 | | | |
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
| Post: Self-Review | ⏳ Pending | |
| Post: UAT Runbook Generation | ⏳ Pending | |
| Post: PR Body Generation | ⏳ Pending | |
| Post: PR Creation | ⏳ Pending | |
| Post: Review Remediation | ⏳ Pending | |
| Post: Retrospective | ⏳ Pending | |

- [ ] All tasks marked complete in tasks.md
- [ ] Full suite passes above the recorded baseline:
      `python3 tests/speckit-pro/run-all.py`
- [ ] Payload/proof regeneration complete and `artifact-consistency`-clean
- [ ] `pnpm --dir docs-site reference:generate` run if the test tree changed
- [ ] Codex parity checks pass (validate-codex-skills /
      validate-codex-parity)
- [ ] PR created (this run's own PR follows the pre-ART-007 path) and the
      PR title passes the release-readiness gate; exactly one non-empty
      release-note fence in the body
- [ ] Merged to main branch (human merges; Claude never merges)

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
├── speckit-pro/                      # Plugin source (ships to installers)
│   ├── agents/                       # Claude agent definitions (+ artifact-author.md, new)
│   ├── codex-agents/                 # Codex mirrors
│   ├── artifact-gallery/             # ART-001/002 templates + manifest.json (routing)
│   ├── skills/speckit-autopilot/     # Autopilot skill + references + contracts
│   └── codex-skills/speckit-autopilot/  # Codex mirror
├── speckit_pro_runner/               # Python 3.11+ stdlib runner + helpers
├── tests/speckit-pro/                # Repository-only validation (L1/L4/L5/L6)
├── docs/ai/specs/                    # Roadmaps + .process/ scaffold exhaust
└── specs/                            # Per-feature CONTRACT artifacts
    └── art-007-draft-pr-emission/    # This spec (+ artifacts/ at plan stage)
```

---

Populated from the ART-007 roadmap entry and the Design Concept interview (2026-08-17).
