# SpecKit Workflow: ART-008 — Feedback Sweep

**Template Version**: 1.0.0
**Created**: 2026-08-20
**Purpose**: Executable workflow for the ART-008 autopilot run, slice 1 of 2 (the checkpoint). The prompts below are what each phase executes.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/ART-008-design-concept.md
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
| Specify | `/speckit-specify` | ✅ Complete | 19 FRs, 3 user stories, 11 acceptance scenarios, 9 edge cases, 8 success criteria. 3 `[NEEDS CLARIFICATION]` markers left for Clarify |
| Clarify | `/speckit-clarify` | 🔄 In Progress | 3 sessions. All three run: they carry the seven deferred Open Questions and the hidden-coupling search, which exist independent of the marker count |
| Plan | `/speckit-plan` | ⏳ Pending | |
| Checklist | `/speckit-checklist` | ⏳ Pending | Run for each domain |
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

This is the first spec whose plan stage runs with ART-007's draft-PR emission
shipped (speckit-pro 2.27.0). The plan stage therefore ends at an open draft
PR, and the feedback sweep this spec builds is what a later `--stage implement`
run will execute first, once ART-008 itself has shipped and the plugin cache
updates. This run's own implement stage still opens the pre-ART-008 way.

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

### Gate Record

Appended by the autopilot as each gate resolves. This is the durable verdict
store the Step 1.1 coverage guard reads when a Workflow Overview row claims a
terminal status.

- G0 gate: PASS — 2026-08-20. Suite 7659/7659 (L1 1469, L4 5998, L5 192), zero
  failures. TYPECHECK, BUILD, and LINT are `N/A` for this repository
  (`detect-commands` reports a Python test-runner stack with no build,
  typecheck, or lint entry point). Reviewability setup gate `warn` with empty
  `blockers`. Constitution principles I through VI verified below.
- G1 gate: PASS — 2026-08-20. Routing decision, not a pass/fail check.
  `specs/art-008-feedback-sweep/spec.md` carries **3** `[NEEDS CLARIFICATION]`
  markers (FR-010 classification granularity, FR-012 commit granularity,
  FR-014 Consensus Resolution Log type value), so the run routes to Clarify.
  Counted with a loose `grep -c "NEEDS CLARIFICATION"`, because the runner's
  own counter matches only the bare literal and misses the colon form the spec
  template prescribes. Zero `[Gap]` and zero `HUMAN REVIEW NEEDED`.

---

## Prerequisites

### Constitution Validation

**Before starting any workflow phase**, verify alignment with the project constitution (`.specify/memory/constitution.md`):

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| I. Plugin Structure Compliance | No new agent or skill directory; reference docs change in place in both `skills/speckit-autopilot/references/` and `codex-skills/speckit-autopilot/references/` | Layer 1 (`run-all.py --layer 1`) + Codex parity checks |
| II. Cross-Platform Runtime & Script Safety | The feedback helper is Python 3.11+ stdlib, `shell=False`, argument arrays; `gh` is invoked only from skill prose at the boundary the Copilot remediation loop and the corroboration read already use; comment text never reaches a shell | Layer 4 Bash-confinement and active-path guards |
| IV. Test Coverage Before Merge | Layer 4 golden fixtures for the comment parse: both surfaces, every `authorAssociation` value, all three export leads, already-logged ids, and each corroboration status the sweep stops on | Layer 4 suite |
| VI. KISS, Simplicity & YAGNI | One helper, one log table, no new phase row, no page-to-source mapping, no template edits (Design Concept Q1, Q6, Q9, Q10) | Code review against the design concept |

**Constitution Check:** ✅ Verified (initial, 2026-08-20). No conflicts
identified during scoping and none introduced by the baseline; verify again
after Plan and after Implement.

### Phase 0 Baseline (recorded 2026-08-20)

| Field | Value |
|-------|-------|
| Python | 3.11.0 |
| SpecKit CLI | `specify 0.14.2` on PATH (`check-prerequisites` reports 0.11.8 from its own resolution) |
| `check-prerequisites` | `all_pass: true`, all 8 checks pass |
| Test-count baseline (G0) | **7659** passed of 7659 — L1 1469, L4 5998, L5 192 |
| `UNIT_TEST` / `FULL_VERIFY` | `python3 tests/speckit-pro/run-all.py` |
| `BUILD` / `TYPECHECK` / `LINT` | `N/A` — `detect-commands` finds a test-runner-only Python stack |
| Preset | `speckit-pro-reviewability` v1.0.0 (spec, plan, and tasks templates) |
| Extensions | archive, git, verify, verify-tasks, retrospective, speckit-utils |
| Local settings | none — no `.claude/speckit-pro.local.md`; runner defaults apply |
| Confidence-gate mode | `advisory` (no flag in argv, no local config) |
| Archive sweep | dry-run, zero eligible previously merged specs, nothing written |
| Tier-2 relocation | no candidate. `specs/brand-001-racecraft-identity-system` is suppressed twice over: `non_speckit_namespace` (first segment `brand` is all-alpha and is neither `prsg` nor `spec`) and already-current (`structureVersion: 1`) |

**The G0 baseline is preserved, not recomputed.** A later `--stage implement`
run compares its post-implementation count against 7659; recapturing the
baseline after planning would compare the tree against itself.

#### Doctor Health Check (2026-08-20)

Verdict: **warnings, zero failures. Nothing blocks Specify.** Structure,
templates (5 of 5), constitution (996 words), and the Python runner (6 of 6
required files, valid manifest) all pass. Three warnings, each expected:

1. Agent config, verbatim `no command files registered`, checked at
   `.claude/commands/speckit.*.md`. A stale check pattern that predates the
   slash-command-to-skills migration. `.specify/init-options.json` carries
   `"ai_skills": true` and 27 `speckit-*` skills are registered under
   `.claude/skills/`, so registration is present where this version of the
   check no longer looks.
2. `specs/art-008-feedback-sweep` reports `spec ✗ plan ✗ tasks ✗`. That is the
   correct pre-Specify state for this run.
3. `specs/brand-001-racecraft-identity-system` reports the same shape. Unrelated
   to this run and not archive-eligible.

The shipped doctor implements structure, templates, agent config, runner,
constitution, and features. It has no scripts, extensions, or git check, so
those three are reported here as not implemented rather than as passes.

### Feature State (namespaced branch)

| Field | Value |
|-------|-------|
| Feature dir | `specs/art-008-feedback-sweep` — pinned at run time in `.specify/feature.json` (gitignored, so it is never committed), as the ART-007 and ART-012 runs did |
| `ON_FEATURE_BRANCH` | **false**, and the scaffold-time prediction of `true` was wrong. `check-prerequisites` reports `worktree=true,feature=false`: the flag is defined as `^[0-9]{3}-` against the branch name, which `art-008-feedback-sweep` does not match. The value is a naming heuristic, not a statement about whether a branch exists. The Specify subagent is therefore told explicitly not to create a feature branch, because the branch does exist and is checked out here; the `feature.json` pin gives the vendored `check-prerequisites.sh` its feature directory |
| `before_specify` → `speckit.git.feature` (`optional: false`) | **SKIP**: the branch already exists and is checked out in this worktree; the hook's purpose is satisfied |

### Reviewability Setup Gate (recorded at scaffold time, 2026-08-20)

Runner helper `reviewability-gate` in setup mode against the technical roadmap
returned `status: "warn", pass: true` with the single warning
`primary surfaces 3 exceeds warn threshold 1` and empty `blockers`. That
count comes from the helper's whole-roadmap scan (the figures it reports are
the roadmap's last entry, ART-020: 40 LOC, 3 production files, 5 total);
ART-008's own budget is one primary surface (harness/adapter). Warnings may
proceed when the workflow records the scope budget and split decision, which
the rest of this subsection does.

**Scope budget (whole ART-008, before the split):** the roadmap entry declares
150 reviewable LOC, ~4 production files, ~7 total files. The scoping interview
grew that: a deterministic read-only helper plus its registry entry, the Codex
reference mirrors, the trust filter, and the Feedback Sweep Log protocol put
the whole spec at ~9 production files and ~14 total. Runner
`estimate-spec-size` with the post-interview signals (3 user stories, 14
files, 18 FRs, modify-weighted) returned
`{"estimated_loc":452,"suggested_slices":2,"status":"warn"}`, verbatim; with
production files alone (9) it returned
`{"estimated_loc":352,"suggested_slices":1,"status":"ok"}`.

**Split decision (grill-me slice-sizing, Design Concept Q12):** two vertical
slices along a Path seam, stacked in this order:

| Slice | Branch | Scope | Status |
|---|---|---|---|
| 1, the checkpoint | `art-008-feedback-sweep` (from `main`) | read both comment surfaces, trust filter, export recognition (helper plus fixtures), classify, consensus-amend, Feedback Sweep Log and CRL rows, per-comment replies, stop-or-proceed, unreadable-PR stop; amendments commit and push | **this workflow** |
| 2, artifact freshness | `art-008-feedback-sweep-slice-2` (from slice 1) | whole-set regeneration after amendments, stale-page detection on a clean sweep, draft-description refresh with the Resume block wording | scaffold separately once slice 1's plan stage has opened its draft PR |

Slice 1's stop report states that draft pages regenerate once slice 2 lands.
Each slice re-measures and re-declares at its own Plan phase, which is where
the gate can read one spec's number.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | ART-008 |
| **Name** | Feedback Sweep (slice 1 of 2: the checkpoint) |
| **Branch** | `art-008-feedback-sweep` |
| **Stage** | plan |
| **Dependencies** | ART-007 (Draft-PR Emission): complete, PR #445, archived 2026-08-18 |
| **Enables** | The trusted human checkpoint the staged workflow exists for; ART-008 slice 2 (artifact freshness) stacks on this branch |
| **Priority** | P1 |

### Success Criteria Summary

- [ ] A `--stage implement` run on a feature whose workflow file carries a
      `Draft PR` row reads, before any task work, every unresolved review
      thread and every PR-level conversation comment on that pull request
      (Q2), acting only on comments whose `authorAssociation` is OWNER,
      MEMBER, or COLLABORATOR and listing every other author's comment as
      "not swept: untrusted author" (Q3).
- [ ] Artifact-exported markdown blocks are recognized by their lead
      sentence (the three shipped leads) inside a read-only runner helper
      that the orchestrator feeds with the live `gh` observation, and Layer 4
      golden fixtures pin that parse (Q10; roadmap verification).
- [ ] Every trusted comment is classified amended, answered, deferred, or no
      action; amended items route through the existing category-routed
      consensus machinery, and each amendment to `spec.md`, `plan.md`, or
      `tasks.md` is committed and pushed (Q5; roadmap scope).
- [ ] Every handled comment gets one row in the workflow file's Feedback
      Sweep Log (comment id, surface, author, class, disposition, commit);
      every amendment additionally gets a Consensus Resolution Log row linked
      by number; a re-run skips any id already logged (Q6).
- [ ] Every handled comment gets one reply on the pull request naming the
      class, the artifact and section touched, and the amending commit; the
      sweep never resolves a thread (Q4, Q5).
- [ ] A sweep with at least one amendment stops before Phase 7 task work
      with a re-review report shaped like the plan-stage stop report and
      stating that draft pages regenerate once slice 2 lands; a sweep with
      nothing to act on proceeds directly into Phase 7 (roadmap; Q12).
- [ ] A present `Draft PR` row that cannot be read (`gh` unreachable, or
      corroboration `pr_closed`, `pr_missing`, `identity_mismatch`) stops
      with a report naming the status and the resume path; `no_record`
      proceeds because no draft PR was ever opened (Q7).
- [ ] No new Workflow Overview row, no edit to `WORKFLOW_PHASE_GATE_IDS`,
      `AUTOPILOT_STAGE_PHASES`, the workflow template, any shipped gallery
      template, or any governed Layer 6 corpus agent definition (Q1, Q10;
      Non-goals).
- [ ] Both platforms carry identical behavior
      (`speckit-pro/skills/speckit-autopilot/` and
      `speckit-pro/codex-skills/speckit-autopilot/`), proven by the parity
      checks.

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/art-008-feedback-sweep/spec.md`

### Specify Prompt

```text
/speckit-specify Open the autopilot implement stage with a draft-PR feedback
sweep that reads trusted review comments, amends the planning artifacts
through consensus, records and replies to every comment, and stops for
re-review whenever it changed anything.
```

#### Detailed Prompt (for complex specs)

```text
/speckit-specify

## Feature: Feedback Sweep, slice 1 of 2: the checkpoint (ART-008)

### Problem Statement
ART-007 ends the plan stage at an open draft PR whose body indexes the
planning artifacts, and the gallery's draft-stage pages export a reader's
objections as markdown meant to be pasted into a PR comment. Nothing reads
those comments back. A `--stage implement` run today starts Phase 7 task
work without looking at the pull request, so the checkpoint the staged
workflow exists for is decoration: feedback left on the draft is ignored
unless a human re-edits the plan by hand. The roadmap's key decision
(2026-07-28) is "sweep + amend + re-review": the checkpoint's value is the
human confirming plan changes.

### Users
- The autopilot orchestrator, which runs the sweep as the first Phase 7
  setup step of the implement stage, ahead of "Open the Implementation-Notes
  Record", in both platform variants (Design Concept Q1).
- The reviewer (a write-capable account on this repository) who left
  comments or pasted an exported markdown block on the draft PR, and who
  resolves threads when satisfied with the amendments (Q3, Q4).
- The existing category-routed consensus machinery (codebase-analyst,
  spec-context-analyst, domain-researcher, consensus-synthesizer), which
  amends spec.md / plan.md / tasks.md for substantive items.
- ART-008 slice 2 (artifact freshness) and ART-010 (final writeup), which
  read the Feedback Sweep Log and the Consensus Resolution Log rows this
  slice writes.

### User Stories
- As the orchestrator opening the implement stage, when the workflow file
  carries a Draft PR row and corroboration reports `match`, I read every
  unresolved review thread and every PR-level conversation comment on that
  pull request, keep only comments whose authorAssociation is OWNER,
  MEMBER, or COLLABORATOR, recognize exported markdown blocks by their lead
  sentence, skip any comment id already in the Feedback Sweep Log, and
  classify each remaining comment as amended, answered, deferred, or no
  action.
- As the orchestrator, for each amended item I route it through the
  category-routed consensus protocol, apply the resulting edit to spec.md /
  plan.md / tasks.md, commit and push, write the Feedback Sweep Log row and
  the Consensus Resolution Log row, post one reply on the comment naming the
  class, the artifact and section touched, and the commit, and then stop
  with a re-review report; when no item was amended I write the log rows and
  replies and proceed directly into Phase 7.
- As the orchestrator, when a Draft PR row is present but the pull request
  cannot be read (gh unreachable, or corroboration pr_closed, pr_missing, or
  identity_mismatch), I stop before any task work with a report naming the
  status and the resume path; when the row is absent (no_record) I proceed,
  because no draft PR was ever opened.

### Constraints
- The sweep is a Phase 7 setup step inside references/phase-execution.md
  (Claude) and references/phase-execution-codex.md (Codex). It adds no
  Workflow Overview row and edits neither WORKFLOW_PHASE_GATE_IDS in the
  coverage guard, AUTOPILOT_STAGE_PHASES in read_only.py, nor the workflow
  template (Q1).
- Two comment surfaces: review threads with isResolved false (the GraphQL
  reviewThreads shape the Copilot remediation loop and speckit-resolve-pr
  already query) and PR-level conversation comments. Review summary bodies
  are not read. PR-level comments have no resolved state; the Feedback
  Sweep Log decides "already handled" there (Q2, Q6).
- Trust filter: only OWNER / MEMBER / COLLABORATOR authorAssociation
  values are acted on; every other author's comment is reported as "not
  swept: untrusted author" and never reaches consensus. SECURITY.md names
  prompt injection reaching a write or execute tool as in scope (Q3).
- The comment parse is deterministic: the orchestrator takes the live gh
  observation and hands the JSON to a new read-only runner helper that
  filters, recognizes the three shipped export leads ("Objections recorded
  while reviewing this plan.", "The approach chosen while reviewing these
  options.", "Objections recorded while reading this module map."), and
  reports candidates; Layer 4 golden fixtures pin the parse. No gallery
  template is edited (Q10). Pattern: resolve-autopilot-stage's
  pr_observation input and corroborate_draft_pr's closed vocabulary.
- Classification vocabulary is closed: amended, answered, deferred, no
  action. Only amended routes through consensus and produces a Consensus
  Resolution Log row (Q5 notes).
- The sweep never calls resolveReviewThread; the operator resolves, and
  convergence is the clean re-run (Q4).
- One reply per handled comment via gh api, naming class, artifact and
  section, and commit; replies use a fixed template per class and stay
  public-readable English (Q5).
- Durable record: a Feedback Sweep Log table in the workflow file (comment
  id, surface, author, class, disposition, commit) plus the mandated
  Consensus Resolution Log rows for amendments; the workflow file is the
  sole store, no state-file mirror (Q6, following the Draft PR row rule).
- Stop-or-proceed: any amendment stops for re-review with a report shaped
  like the plan-stage stop report, which states that draft pages regenerate
  once slice 2 lands; no amendment proceeds into Phase 7. An unreadable
  Draft PR row stops with status and resume path; no_record proceeds (Q7).
- Out of this slice and owned by slice 2 (artifact freshness, stacked on
  this branch): whole-set regeneration after amendments (Q9), stale-page
  detection on a clean sweep (Q8), and the draft-description refresh with
  the Resume block wording (Q11). Specify those as named non-goals with the
  slice-2 owner, not as silent omissions.
- Platform parity: identical behavior in both skill variants.
- Reviewability budget for this slice: re-derive at Plan from the Declared
  File Operations block; the whole-spec advisory estimate was
  {"estimated_loc":452,"suggested_slices":2,"status":"warn"} (3 stories,
  14 files, 18 FRs, modify-weighted), which is why the spec is two slices.

### Out of Scope
- Artifact regeneration, stale-page detection, and the draft-description
  refresh (ART-008 slice 2).
- Post-implementation review remediation (the existing /loop machinery).
- The ready flip and the final writeup (ART-010).
- Resolving review threads, reading review summary bodies, a state-file
  mirror of the sweep record, a new Workflow Overview row, gallery-template
  edits, and edits to any of the twelve governed Layer 6 corpus agent
  definitions.
- An operator override flag to skip the sweep (no concrete case surfaced;
  Clarify may revisit, Design Concept Open Questions).
```

### Specify Results

<!-- Fill in after running the command -->

| Metric | Value |
|--------|-------|
| Functional Requirements | 19 — FR-001 through FR-019 |
| User Stories | 3 — P1 read and classify, P2 amend/record/reply/stop, P3 unreadable-PR stop |
| Acceptance Criteria | 11 acceptance scenarios, plus 9 edge cases and 8 success criteria |
| `[NEEDS CLARIFICATION]` markers | 3 — FR-010, FR-012, FR-014 |
| Declared reviewability budget | ~330 reviewable LOC, 7 production files, 10 total, within budget (projected); Plan re-derives |

Two requirements the design concept did not name came out of the Specify pass
and are kept: **FR-006**, which excludes the sweep's own replies from the
candidate set (a trusted author with a new comment id passes both the trust
filter and the already-logged check, so without this every run would sweep the
previous run's output), and **FR-010's** open question about a single export
block carrying several objections with different dispositions. The spec carries
`one class per comment` as a working default in Assumptions so the surrounding
requirements stay coherent while that stays open.

### Files Generated

- [x] `specs/art-008-feedback-sweep/spec.md`
- [x] `specs/art-008-feedback-sweep/checklists/requirements.md`

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

The Design Concept interview settled every major fork (Q1 through Q12) and
left seven items deliberately open. Sessions 1 and 2 pin the protocol-level
and helper-level details; session 3 verifies the settled decisions were
encoded rather than re-opened and closes the remaining small items. The
blind-spot pass did not run at scaffold (wait deadline expired), so session 2
also carries the hidden-coupling search that pass would have done.

### Clarify Prompts

#### Session 1: Feedback Sweep Log and Commit Protocol

```text
/speckit-clarify Focus on the durable record: the exact Feedback Sweep Log
column set and its placement in the workflow file (beside the Consensus
Resolution Log, per references/workflow-file-protocol.md); the CRL Type
value for sweep amendments and how aggregate-crl treats it; commit
granularity inside the sweep (one commit per amendment or one per run) and
whether the log write is its own bookkeeping commit, following the Draft PR
row rule "the separate bookkeeping commit, never the stage-boundary commit";
and what a re-run reads from the log to skip handled ids (Design Concept Q6,
Open Questions 1 and 3).
```

#### Session 2: Helper Envelope and Hidden Coupling

```text
/speckit-clarify Focus on the read-only helper: its name and envelope
(surfaces read, trusted and untrusted counts, per-comment class candidates,
recognized exports with template id and anchors), mirroring
resolve-autopilot-stage's pr_observation input and corroborate_draft_pr's
closed vocabulary; the exact gh reads the orchestrator issues for both
surfaces and for authorAssociation; the fixed reply template per class; and
a hidden-coupling search of helpers/pr_emission.py and
resolve-autopilot-stage's input contracts that the sweep reuses, since the
scaffold blind-spot pass did not run (Design Concept Q2, Q3, Q5, Q10, Open
Questions 2, 4, and 7). Comment text must never reach a shell argument.
```

#### Session 3: Settled-Decision Verification

```text
/speckit-clarify Verify spec.md encodes the settled interview decisions
without re-opening them: Phase 7 setup step, no new phase row (Q1); two
comment surfaces, review bodies excluded (Q2); OWNER / MEMBER / COLLABORATOR
trust filter with untrusted comments reported and never routed (Q3); the
operator resolves threads, the sweep never does (Q4); one reply per handled
comment (Q5); Feedback Sweep Log plus CRL rows, no state-file mirror (Q6);
stop on an unreadable Draft PR row, proceed on no_record (Q7); slice 2 owns
regeneration, stale-page detection, and description refresh (Q8, Q9, Q11,
Q12). Then decide whether an operator override to skip the sweep is needed
(Open Question 5; default no flag) and whether exported blocks inside review
threads need their own acceptance scenario (Open Question 6).
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Feedback Sweep Log and commit protocol | 5 returned, 5 answered; 4 sub-items routed to consensus | All 3 spec markers cleared. One commit per amendment (FR-012); log writes ride a separate bookkeeping commit, per amendment, with the zero-amendment case covered (FR-012a); `Sweep` as the CRL `Type`, counted in the escape-rate metric with `Type` as the source discriminator (FR-014); one class per comment with `amended` dominant (FR-010); the log's column set, placement, and bidirectional `CRL #` link (FR-013, FR-014); comment id as the sole skip key (FR-009). SC-002 and SC-003 qualified after consensus found both falsified by the spec's own edge case. Consensus resolved all 4 items in Round 1 |
| 2 | | | |
| 3 | | | |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/art-008-feedback-sweep/plan.md`

### Plan Prompt

```text
/speckit-plan

## Tech Stack
- Runtime: speckit-pro plugin skills (Markdown SKILL.md + reference docs)
  plus Python 3.11+ stdlib runner helpers (`speckit_pro_runner/helpers/`)
  for the deterministic comment parse. No new Bash, no `jq`
  (constitution II); `shell=False`, argument arrays, and comment text never
  interpolated into a command.
- PR boundary: `gh api graphql` for review threads and `gh api` REST for
  PR-level comments and replies, at the same trust boundary the Copilot
  remediation loop, speckit-resolve-pr, and ART-007's corroboration read
  already use. The orchestrator takes the observation; the helper
  classifies it.
- Consensus: the existing category-routed protocol in
  `references/consensus-protocol.md` (Tier A routing, two rounds, escape
  hatch) and its Consensus Resolution Log schema.
- Test suite: `python3 tests/speckit-pro/run-all.py` (Layer 4 golden
  fixtures for the helper; Layer 1 structure and Codex parity).
- Platforms: Claude Code (`speckit-pro/skills/`) and Codex CLI
  (`speckit-pro/codex-skills/`), identical behavior, proven by
  validate-codex-skills / validate-codex-parity.

## Constraints
- This plan covers slice 1 only (the checkpoint). Slice 2 (artifact
  freshness) is a separate spec stacked on this branch; record the
  two-slice topology in the plan the way ART-005's slice-topology contract
  did, and name the slice-2 hooks this slice leaves (the Feedback Sweep Log
  row shape slice 2 reads, and the stop-report sentence about regeneration).
- Re-derive the reviewability budget from the Declared File Operations
  block and record the runner's `estimate-spec-size` output verbatim; the
  whole-spec advisory estimate was 452 / warn / 2 slices, which is why this
  is slice 1. Expected production surface: phase-execution.md,
  phase-execution-codex.md, consensus-protocol.md,
  workflow-file-protocol.md and its Codex mirror, read_only.py, registry.py,
  and possibly one line in each SKILL.md. Both SKILL.md files are already
  past the documented 500-line guidance (ART-019), so prefer
  references-only changes and verify the 8000-word cap before adding a
  line.
- No new Workflow Overview row; no edits to WORKFLOW_PHASE_GATE_IDS,
  AUTOPILOT_STAGE_PHASES, the workflow template, any gallery template, or
  any governed Layer 6 corpus agent definition (Q1, Q10; Non-goals).
- Plugin source changes must account for the generated artifact contract
  (payload regeneration) before the work is called done; the read-only
  helper harness manifests under tests/speckit-pro/unit/fixtures/
  read-only-helpers/ list every helper and must gain the new entry.
- Reference the Design Concept doc
  (docs/ai/specs/.process/ART-008-design-concept.md) if planning needs
  context beyond this prompt; it is the source of truth for every scoping
  decision (Q1 through Q12).

## Architecture Notes
- **Sweep sequence (Q1, Q7):** Phase 7 setup, before "Open the
  Implementation-Notes Record": read the Step 0.6c corroboration status;
  `no_record` proceeds with a one-line note; anything other than `match`
  stops with the status and resume path; on `match`, take the gh
  observation for both surfaces, hand it to the helper, then classify,
  consensus-amend, commit and push per amendment, write the Feedback Sweep
  Log and CRL rows, reply per comment, and stop-or-proceed.
- **Helper shape (Q2, Q3, Q10):** one read-only operation, registered like
  `resolve-autopilot-stage`, taking the raw observation plus the already
  logged comment ids; it applies the authorAssociation allowlist, recognizes
  export blocks by the lead-sentence registry, and returns a closed-vocabulary
  envelope (trusted items, untrusted items with reason, recognized exports
  with template id and anchors, skipped ids). Classification into amended /
  answered / deferred / no action is orchestrator judgment over the
  envelope, with category tags for consensus routing.
- **Records (Q6):** Feedback Sweep Log table placement and columns from
  Clarify session 1; CRL rows use the existing column set with the Type
  value session 1 fixes. Replies (Q5) follow the remediation loop's
  `gh api repos/<owner>/<repo>/pulls/<n>/comments` (threads) and
  `issues/<n>/comments` (PR-level) write paths with a fixed template per
  class.
- **Stop report (Q7, Q12):** mirror the plan-stage stop report's shape:
  counts by class, amended artifacts and commits, the draft PR URL, the
  sentence that draft pages regenerate once slice 2 lands, and resume
  instructions (resolve threads, re-run `--stage implement`).
- **Security (Q3):** the allowlist is enforced in the helper (fixture-pinned)
  before any text reaches an analyst; untrusted comments are reported, never
  routed; no comment text is passed as a shell argument anywhere.
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

Signals in this spec: untrusted public comment text routed toward agents
that edit artifacts, and outward writes to a public pull request
(**security**); `gh` failure paths, corroboration discrepancies, and
partial progress when a push or reply fails mid-sweep (**error-handling**);
the Feedback Sweep Log lifecycle, idempotent re-runs, and convergence with
operator-resolved threads (**state-management**). No API endpoints, no UI,
no database, no LLM prompt surface beyond the consensus protocol the suite
already covers.

**Target: 2-4 domains.** Three domains carry this spec's risk.

### Step 2: Run Enriched Checklist Prompts

#### 1. security Checklist

Why this domain: the sweep is the first shipped path where text written by
an arbitrary GitHub account can reach the consensus analysts and, through
them, a write tool. SECURITY.md names exactly that path.

```text
/speckit-checklist security

Focus on Feedback Sweep requirements:
- The authorAssociation allowlist (OWNER, MEMBER, COLLABORATOR) is enforced
  in the deterministic helper before any comment text reaches an analyst,
  with a fixture per association value including MANNEQUIN, CONTRIBUTOR,
  FIRST_TIME_CONTRIBUTOR, FIRST_TIMER, and NONE.
- Untrusted comments are reported ("not swept: untrusted author") and never
  routed, replied to, or logged as handled in a way that a re-run would
  treat as trusted.
- Comment text never reaches a shell argument; gh reads and writes use
  argument arrays, and reply bodies are passed through --body-file or an
  equivalent that never inlines untrusted text into a command.
- Pay special attention to: an exported markdown block authored by a trusted
  account but quoting untrusted text, and a trusted comment that instructs
  the sweep to change files outside spec.md / plan.md / tasks.md.
```

#### 2. error-handling Checklist

Why this domain: the sweep has five external failure surfaces (two gh reads,
gh replies, git push, and consensus itself) and three corroboration
discrepancy classes that must stop cleanly.

```text
/speckit-checklist error-handling

Focus on Feedback Sweep requirements:
- Each corroboration status (match, no_record, skipped, pr_closed,
  pr_missing, identity_mismatch) has one specified behavior and one
  report shape; only no_record proceeds.
- A gh read that fails mid-sweep (one surface readable, the other not)
  stops rather than sweeping half the feedback silently.
- A reply or push that fails after an amendment was committed leaves a
  recoverable state: the Feedback Sweep Log row records what landed, and a
  re-run neither duplicates the amendment nor re-posts the reply.
- Consensus [HUMAN REVIEW] outcomes surface in the stop report and the log
  instead of being applied or dropped.
- Pay special attention to: the boundary between "nothing to act on" (proceed)
  and "could not read" (stop), which must never collapse into each other.
```

#### 3. state-management Checklist

Why this domain: the spec writes new durable state (the Feedback Sweep Log)
that re-runs, slice 2, and ART-010 read, beside the Stage and Draft PR rows
ART-006 and ART-007 shipped.

```text
/speckit-checklist state-management

Focus on Feedback Sweep requirements:
- Feedback Sweep Log lifecycle: absent before the first sweep, appended per
  handled comment, carried by the commit Clarify session 1 fixes, never
  mirrored into the state file.
- Idempotency: a re-run skips every logged id, including ids whose threads
  the operator has not yet resolved, and handles new comments on an already
  logged thread as new items.
- Convergence: the loop ends when a run finds no trusted, unlogged comment;
  the operator resolving threads is not a precondition for proceeding.
- Pay special attention to: interrupted sweeps (amendment committed but log
  row not yet written; log row written but reply not posted), each of which
  must resume to the correct terminal state.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| security | | | |
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

**When to run:** After checklists complete (all gaps resolved). Output: `specs/art-008-feedback-sweep/tasks.md`

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
1. Foundation: the read-only helper skeleton, its registry entry, the
   read-only-helper harness manifest entries, and the Layer 4 fixture
   skeletons (both surfaces, every authorAssociation value, the three
   export leads, logged-id skipping)
2. User Story 1 (P1): read, filter, recognize, classify (helper branches
   green; orchestrator prose for the gh reads and the Phase 7 setup slot in
   both phase-execution variants)
3. User Story 2 (P2): consensus-amend, commit and push, Feedback Sweep Log
   and CRL rows (workflow-file-protocol.md both platforms,
   consensus-protocol.md), replies per comment, stop-or-proceed and the
   re-review report
4. User Story 3 (P3): the unreadable-PR stop for every non-match
   corroboration status, and the no_record pass-through
5. Polish: stop-report wording, payload regeneration, parity verification,
   docs-site reference regeneration if the test tree changed

## Constraints
- Tests live under tests/speckit-pro/ (repository-only), never inside the
  shipped plugin directory; name them for durable capability, never for the
  spec ID.
- TDD: every helper branch and fixture path gets its failing test first.
- The design concept's Non-goals bound generation: no regeneration, no
  stale-page detection, no description refresh (slice 2); no thread
  resolution; no new phase row; no template edits; no corpus files; no
  state-file mirror. Flag any task that would cross those boundaries
  instead of silently emitting it.
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
runner helper atomicity-route specs/art-008-feedback-sweep
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
1. Constitution alignment — stdlib-only helper, shell=False and argument
   arrays, no new Bash/jq, no comment text in a command
2. Coverage gaps — every FR and user story has tasks; every corroboration
   status, every authorAssociation value, each export lead, and the
   logged-id skip have fixture tasks
3. Design-concept drift — spec.md/plan.md/tasks.md against the settled
   Q1 through Q12 decisions; the design concept wins unless a revision
   note says otherwise
4. Slice boundary — no regeneration, stale-page, or description-refresh
   work leaked into this slice; the slice-2 hooks (log row shape, stop
   report sentence) are named
5. Roadmap consistency — the ART-008 scaffold amendment (budget progression
   and two-slice split) stays accurate
6. Budget re-derivation — the spec's declared budget still matches the
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
2. Verify the worktree is on `art-008-feedback-sweep` and clean.
3. Re-read the Design Concept doc for the Q1 through Q12 decisions before
   touching the surfaces they govern.

### Implementation Notes
- Shipped-byte changes require the payload/proof regeneration ritual before
  completion (`scripts/refresh-release-artifacts.py`; rsync with
  --checksum; release-readiness last).
- A tracked .md/.py/.sh change under tests/speckit-pro/ additionally
  requires `pnpm --dir docs-site reference:generate` (deps are installed in
  this worktree).
- The helper stays stdlib-only, shell=False, argument arrays; never
  interpolate comment text into a command (constitution II, Q3).
- Do not touch the twelve governed corpus agent definitions, any gallery
  template, the workflow template, WORKFLOW_PHASE_GATE_IDS, or
  AUTOPILOT_STAGE_PHASES.
- Bracket-class regex boundaries, not \b, in anything grep-adjacent
  (BSD/GNU portability).
- Both skill variants change together; parity checks are part of done, not
  a follow-up.
- Report deviations from plan, discovered edge cases, and surprises in every
  task result; the orchestrator appends them to the implementation-notes
  record (ART-012).
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
- [ ] PR title passes the release-readiness gate; exactly one non-empty
      release-note fence in the body
- [ ] Merged to main branch (human merges; Claude never merges)

---

## Consensus Resolution Log

One row per consensus resolution, across every phase that runs consensus. The
`Round` and `Categories` columns are what make the Round-2 escape-rate metric
computable from this table alone.

`Type` carries the canonical vocabulary from
`references/consensus-protocol.md` §Logging: `Clarify`, `Gap`, `Finding`. The
`Sweep` value this spec adds is for the feature being built and does not appear
in this table, because no feedback sweep runs against ART-008's own workflow.

| # | Type | Phase / Session | Item | Categories | Round | Outcome | Resolution | Analysts Used |
|---|------|-----------------|------|------------|-------|---------|------------|---------------|
| 1 | Clarify | Clarify S1 | Do `Type: Sweep` rows count toward the Round-2 escape-rate metric, or are they excluded from its denominator? | `[spec, domain]` | 1 | **both-agree**, include. High confidence from each, no escape hatch | Include. Spec-context found no project record tying the 10% threshold to any phase-specific calibration, so the exclude case had no basis in this repository's history; every occurrence of the figure is one generic sentence over "consensus items". Domain-researcher reached the same answer through fail-safe asymmetry, SPC rational subgrouping, SRE error-budget practice, and the Wald selection-bias structure, and proposed stratified source-tagging rather than exclusion. That refinement needed no new field: the `Type` column already is the discriminator. Applied to `spec.md` FR-014 | spec-context-analyst, domain-researcher |
| 2 | Clarify | Clarify S1 | When one comment's objections diverge across classes, which class wins? | `[spec]` | 1 | **high-confidence**, confirm amended-dominance. No escape hatch | Confirmed, and shown not to be invented. The roadmap's 2026-07-28 decision fixed that amendments always stop for re-review three weeks before the four-class vocabulary existed, and FR-003 plus SC-007 forbid any tie-break that is not a fixed explicit rule, leaving amended-dominance as the only rule satisfying both. A full four-level order was rejected as structure with no behavioral consequence. Applied to `spec.md` FR-010 and Assumptions | spec-context-analyst |
| 3 | Clarify | Clarify S1 | How is the Feedback Sweep Log to Consensus Resolution Log link represented on disk? | `[codebase, spec]` | 1 | **both-agree**, confirm the `CRL #` column. High confidence from each, no escape hatch | Confirmed, and made bidirectional. Codebase traced both Markdown table readers to their anchors and found neither is anchored near these tables, so a new table and a new column are invisible to both; it also found the same row-number reference already used as prose in ART-007 and ART-012 with no instance of a row ever being reordered. Its refinement, adopted: the Consensus Resolution Log row's item text also names the comment id, keying the reverse direction on an immutable GitHub id. Spec-context confirmed no machine consumer exists but that this argues for a structured field, and that the mandatory-column list is a floor the committed corpus already varies above. Applied to `spec.md` FR-014 and Key Entities | codebase-analyst, spec-context-analyst |
| 4 | Clarify | Clarify S1 | Bookkeeping cadence, and does the spec accept re-processing after an interrupted run or add a detection-and-repair rule? | `[codebase, spec]` | 1 | **both-agree**, per-amendment cadence and accept re-processing. High confidence from each, no escape hatch | Confirmed. Codebase separated two hazard classes: existing batching precedents batch local unpushed work, while this window spans pushed commits and posted replies, and the only precedent for recording an external side effect pairs the record tightly with the single action. It showed every candidate live witness is closed by FR-006, FR-012, or FR-016, so the `Draft PR` repair rule cannot port. Spec-context established that SC-003 **and** SC-002 are both falsified as written by the spec's own edge case, and that FR-017 backstops the worse branch because any re-amendment stops the run before task work. Consensus also found three defects in the orchestrator's own first-pass text, all fixed: FR-012a's rationale over-claimed cadence as forced when only the ordering is, the borrowed `Draft PR` rules silently dropped `repair`, and a run with zero amendments but handled comments had no commit to carry its rows. The synthesizer additionally corrected the orchestrator's own fix, which would have mandated an empty commit on a comment-free sweep. Applied to `spec.md` FR-012a, SC-002, SC-003, and an edge case | codebase-analyst, spec-context-analyst |

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

```text
racecraft-plugins-public/
├── speckit-pro/                                   # Plugin source (ships to installers)
│   ├── skills/speckit-autopilot/references/       # phase-execution.md, consensus-protocol.md, workflow-file-protocol.md
│   ├── codex-skills/speckit-autopilot/references/ # phase-execution-codex.md, workflow-file-protocol-codex.md
│   └── speckit_pro_runner/helpers/                # read_only.py (new feedback helper), registry.py
├── tests/speckit-pro/                             # Repository-only validation
│   └── unit/fixtures/read-only-helpers/           # helper request fixtures + harness manifests
├── docs/ai/specs/                                 # Roadmap, .process/ exhaust (this file, design concept)
└── specs/art-008-feedback-sweep/                  # CONTRACT artifacts: spec.md, plan.md, tasks.md, SPEC-MOC.md
```

---

Template based on SpecKit best practices. Populated from the ART-008 design concept on 2026-08-20.
