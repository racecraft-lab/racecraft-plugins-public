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
| Clarify | `/speckit-clarify` | ✅ Complete | 3 sessions, 15 questions, 7 consensus items all resolved in Round 1 with 23 analyst dispatches. Spec grew 402 → 927 lines and 19 → 31 requirements. Zero markers, zero human-review flags |
| Plan | `/speckit-plan` | ✅ Complete | 5 artifacts, 1506 lines. Budget re-derived by hand at 515-745 LOC (midpoint ~630) over 7 production files: two warns, zero blocks, warn accepted with the split lever recorded, since superseded — the live figure's one home is `spec.md`'s Reviewability Budget superseding note |
| Checklist | `/speckit-checklist` | ✅ Complete | 3 domains, 143 items, **54 gaps found and 54 closed**. 8 consensus items across 24 analyst dispatches, all Round 1. Spec grew 31 → 48 requirements and 10 → 13 criteria. Those requirements moved the budget: the high end went 745 → ~775 → **810-830, which crosses the 800 block**, leaving it at **515-830 (midpoint ~630)** at that time, since superseded — the live figure's one home is `spec.md`'s Reviewability Budget superseding note — and still 7 production files |
| Tasks | `/speckit-tasks` | ✅ Complete | **109 tasks**, 6 phases (7/8/40/37/5/12). **54/54 requirements and 15/15 criteria covered**; the orchestrator added T080 after finding SC-003 uncovered, the trust-boundary remediation added T081–T087 for FR-007g, FR-012f, and SC-014, and the third remediation pass added T088–T093 for FR-004d, the captured-call fixture, and the fixed-shape commit subject, and the consumer-scoping pass added T094–T109 for the two scoped agents, the Layer 5 carve-out, the piped observation, and the payload regeneration their shipped bytes require |
| Analyze | `/speckit-analyze` | ✅ Complete | First pass: 6 findings, all remediated, zero unresolved for consensus. Caught a contradiction that would have stopped the feature on its own first write, and a fixture corpus that could not fail in the direction that mattered. **Scoped re-run 2026-08-22** against the consumer-scoping amendment the first pass never saw: **9 findings, 9 remediated, 1 flagged for consensus** (the SC-015 narrowing, tagged `[security]`), **and that item is now resolved** — routed to all three analysts on 2026-08-23 and recorded as CRL row 8. Both passes are tabled under [Phase 6](#phase-6-analyze) |
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
- G2 gate: PASS — 2026-08-20. Zero `[NEEDS CLARIFICATION]` markers, counted by
  loose grep for both the bare and colon forms; zero `HUMAN REVIEW NEEDED`; and
  a `## Clarifications` section carrying all three sessions with the decision,
  the reasoning, and the requirement id for each. Seven sub-items went to
  consensus across sessions 1 and 2 and every one resolved in Round 1, with no
  escalation, no escape-hatch keyword, and no human-review flag. Session 3
  returned zero unresolved items and verified all eight settled interview
  decisions are encoded.
- G3 gate: PASS — 2026-08-20. `plan.md`, `research.md`, and `data-model.md` all
  exist and are non-empty, plus `quickstart.md` and one contract. Zero `FAIL` in
  any constitutional gate section, zero `[TODO]`, zero `[NEEDS CLARIFICATION]`,
  and zero absolute-path leaks under `specs/`. The reviewability estimator
  returned `pass` with `projected: 0`, which is recorded below as an absent
  measurement rather than a budget verdict; the hand-derived figure carries two
  warns and zero blocks.
- G4 gate: PASS — 2026-08-20. Zero `[Gap]` markers across all four checklist
  files, counted with a loose grep for any bracketed marker containing `Gap`.
  Three domains ran sequentially with consensus after each: security (8 gaps),
  error-handling (30), state-management (16). All 54 closed. Full suite green at
  7659/7659 after remediation.

  **The runner's gap counter is not trustworthy and was not trusted.** It
  reported 4 against a true 8, then 21 against 30, then **0 against 16**. Its
  regex is the bare `[Gap]` literal, so every combined form — `[Coverage, Gap]`,
  `[Gap, Ambiguity]`, `[Conflict, Gap]` — is invisible to it. On the third
  domain every single marker was a combined form, so its zero before remediation
  and its zero after carried identical information: none.
- G5 gate: PASS — 2026-08-21 (counts as at the gate; the trust-boundary remediation grew them afterwards, see the Tasks row). Every one of the 48 requirements and all 13
  success criteria are referenced by at least one of the 80 tasks, cross-checked
  by the orchestrator with a trailing-boundary regex so a lettered child never
  satisfies its parent. Task ids are sequential with no duplicates.

  One repair: the executor verified requirement coverage but not criterion
  coverage, and **SC-003 was uncovered** — the clean-re-run convergence claim,
  which is the criterion the state-management domain spent its pass proving. The
  fixture corpus covered its no-second-reply half; nothing pinned the whole-run
  assertion or its interrupted-run qualifier. Added as T080.
- G6 gate: PASS — 2026-08-21. Zero `CRITICAL` findings, zero `[Gap]`, zero
  `[NEEDS CLARIFICATION]`, zero absolute-path leaks. Full suite green at
  7659/7659. Six findings raised and all six remediated; nothing routed to
  consensus.

  Two are worth naming because both were failures in a direction nothing tested.
  **FR-012b called three artifacts the sweep's "whole edit surface" while three
  other requirements oblige it to write a fourth**, the workflow file — so
  applying the membership test to every write would have stopped the run on its
  own first log row and taken the durable record and the skip key with it. Now
  scoped to the amendment surface, with the two write classes separated by which
  commit carries them. And **the author-association corpus pinned only the five
  excluded values**, so an allowlist that wrongly rejected a permitted reviewer
  would have passed every fixture; all eight values of the closed enum are now
  pinned in the direction the filter actually decides them.

  The manifest miscount is the subtlest: it declares eleven exporting entries,
  not ten, and the eleventh ships no template file. The skip is now conditional
  in both directions, because a bare name-skip would have left that entry's
  imperative prompt lead unregistered the day its file lands.

---

## Prerequisites

### Constitution Validation

**Before starting any workflow phase**, verify alignment with the project constitution (`.specify/memory/constitution.md`):

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| I. Plugin Structure Compliance | No new agent or skill directory; reference docs change in place in both `skills/speckit-autopilot/references/` and `codex-skills/speckit-autopilot/references/` | Layer 1 (`run-all.py --layer 1`) + Codex parity checks |
| II. Cross-Platform Runtime & Script Safety | The feedback helper is Python 3.11+ stdlib, `shell=False`, argument arrays; `gh` is invoked only from skill prose at the boundary the Copilot remediation loop and the corroboration read already use; comment text never reaches a shell | Layer 4 Bash-confinement and active-path guards |
| IV. Test Coverage Before Merge | Layer 4 golden fixtures for the comment parse: both surfaces, every `authorAssociation` value, every registered export sentence in both the verbatim and header-trimmed shapes, the empty-export and prompt-kind forms, a carriage-return body, an oversized body that truncates, already-logged ids, and each corroboration status the sweep stops on. Plus a test deriving the registry's expected set from the gallery manifest and templates | Layer 4 suite |
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

#### Implement-Stage Pre-Flight (recorded 2026-08-23)

The `--stage implement` run re-ran pre-flight in a fresh session. What it found:

| Field | Value |
|-------|-------|
| Stage | `implement` (argv) — explicit `--stage implement` |
| Draft PR corroboration | `match` — #464 recorded, #464 observed, OPEN and still a draft |
| `check-prerequisites` | `all_pass: true`, all 8 checks pass |
| Confidence-gate mode | `advisory`, unchanged; the recorded G6.5 verdict is read, not re-run |
| Atomicity route | `one-navigable-PR`, carried forward; layer plan stays `skipped` and `pr_marker_plan` stays null |
| Main sync | 11 commits merged from `origin/main`, generated artifacts regenerated, suite green |
| Live test count | **7912** passed of 7912 — L1 1469, L4 6251, L5 192 |

**Test-count drift, non-blocking.** The live count is 7912 against the recorded
G0 baseline of **7659**, a difference of 253 tests. Every one of them arrived
with the eleven merged `main` commits, not with this feature. The baseline stays
7659: G7 verifies that the count rose against the number recorded before any
planning ran, and replacing it here would compare the tree against itself. The
drift is recorded so a reader can see the tree moved underneath the spec.

**G6.5 was read, not re-run.** The recorded verdict is composite **0.80** in
`advisory` mode, below the 0.90 threshold and deliberately so. This run read it
and proceeded, which is what `advisory` means. The row stays `⏳ Pending` because
no phase of the main loop flips it.

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
| **Stage** | implement |
| **Draft PR** | [#464](https://github.com/racecraft-lab/racecraft-plugins-public/pull/464) |
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
| 2 | Helper envelope and hidden coupling | 5 returned, 5 answered; 3 sub-items routed to consensus, 8 analysts | Carried the blind-spot search the scaffold never ran, and changed the spec most. Found that the export lead is not on a comment's first line (it is line four), that an empty export carries no lead at all and would have been mistaken for feedback, that the runner's 32 KiB bound rejects a whole request over one oversized string, that a draft description has no editable region, that the runner cannot post the replies, and that an unescaped pipe in the disposition would break the log link. Consensus registered the prompt-kind variants, settled the own-reply marker plus author match, and mapped `skipped` to stop. Scope correction: ten templates export, not three |
| 3 | Settled-decision verification | 1 question, 15 consistency findings; 0 sub-items needed consensus | All eight settled interview decisions verified encoded, none partial or missing. Fixed two contradictions the spec had grown into: FR-015 required an artifact, section, and commit from all four reply classes when only `amended` has them, and its one-reply rule lacked the qualifier SC-002 and SC-003 already carried. Added SC-009 and SC-010 to cover the no-shell-argument boundary and the log-escaping rules, which had no verification at all. Corrected the empty-sentence count from two templates to three. Delivered the budget verdict below |

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
| `plan.md` | ✅ | 375 lines. Declared File Operations block complete: 22 entries across a production surface of 7, a test and fixture surface of 7, and 8 generated paths |
| `research.md` | ✅ | 291 lines. Decision rationales, including the accepted recognition degradation for the three serialization templates |
| `data-model.md` | ✅ | 348 lines. Envelope, swept-comment record, registry entry, log row |
| `contracts/` | ✅ | `sweep-pr-feedback.md`, 241 lines |
| `quickstart.md` | ✅ | 251 lines |

#### Reviewability budget, re-derived at Plan

**The estimator is an absent measurement, not a pass.** Run against this plan,
verbatim:

```json
{"tool":"estimate-reviewable-loc","status":"pass","projected":0,
 "declared_files":{"production":0,"new":4,"modified":18,"total_entries":22},
 "greenfield":false,"thresholds":{"warn":400,"block":800}}
```

It parsed all 22 declared entries — the block held 22 at that run and has
grown since, and none of the added paths is one the estimator counts, so the
verdict stands — and classified **none** of them as production, because it
counts a file as production only under `src/`, `app/`, `lib/`, or `scripts/`,
or with a JavaScript, TypeScript, or SQL extension. Every
path this slice touches fails both tests. Its `pass` carries no information
about this slice's size and MUST NOT be read as a budget verdict.

**Hand-derived figure at Plan: 515 to 745 reviewable LOC, midpoint ~630. Seven
production files.** (Superseded below; the live figure's one home is `spec.md`'s Reviewability Budget superseding note.) Plan corrected the spec's earlier 325 to 485 range upward
rather than corroborating it, because two of that range's anchors were measured
against the wrong precedent: the comparable corroboration behavior is 162 lines
rather than the 35 of one function body, and the comparable protocol entry is 58
lines rather than 15 to 25.

**Verdict at Plan: two warns, zero blocks.** Over the 400 LOC warn and over the
6 production-file warn; under the 800 LOC block and the 8-file block, on a
single primary surface. The 745 high end leaves roughly 55 lines of margin to
the block.

> **Superseded at Checklist (2026-08-20).** The trust-boundary and
> error-handling passes added requirements after this verdict was recorded and
> moved the high end to roughly **810 to 830, which crosses the 800 block**. The
> midpoint of about 630 still does not, and the production-file count is
> unchanged at 7, so it remains **two warns** — but the 55 lines of margin above
> no longer exist. The figure at that time was **515 to 830, midpoint near
> 630**, since superseded; the live figure's one home is `spec.md`'s
> Reviewability Budget superseding note, and the Phase 5 fallback evidence chain
> below points there. The paragraph above is kept as the Plan-time record, not
> as the current position.

> **Amended after the plan stage closed (2026-08-21).** A defect found in the
> committed draft artifacts was fixed on this branch rather than deferred, at the
> operator's direction: three of the four generated pages had been committed
> byte-identical to their shipped gallery templates. The repair added **80
> authored lines across two production files** —
> `references/phase-execution.md` and its Codex mirror
> `references/phase-execution-codex.md` — which are the on-disk verification
> post-condition described under "Artifact verification defect" below.
>
> **Both files were already inside the Declared File Operations block**
> (`plan.md` lines 241 and 242), so the production-file count is **unchanged at
> 7** and no new surface enters the slice. The reviewable range moves to **595 to
> 910**, since superseded in turn: the live figure's one home is `spec.md`'s
> Reviewability Budget superseding note, and it crosses the 800 block at the
> midpoint. The high end was already over the 800 block before this change; it
> is now over by more. The file-count warn is untouched, and T014 still forces
> the lever decision before implementation phase 3, now against the larger
> figure. Recorded, not hidden.

**The warn is accepted rather than re-sliced, and the reasoning is on the
record.** The only split lever that preserves a working checkpoint defers three
serialization-family registry rows, which saves 15 to 30 lines and costs
FR-007b. No split reaches 400 while still shipping a checkpoint: the parse
helper and the two phase-execution references are the irreducible core. The
split that would fit — records in one slice, consensus and replies and
stop-or-proceed in another — was rejected on merit, because it ships a
checkpoint that reads feedback and acts on none of it. Re-slicing remains the
operator's call.

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
| **Route** | `one-navigable-PR` | The change is modify-heavy across shared files rather than a set of independent additive capabilities, so it reviews as one navigable pull request. |
| **Releasable** | `true` | No destructive migration and nothing concurrency-sensitive. |
| **Signals** | `change-shape:modify-heavy` | The decisive finding: this slice edits existing references and helpers rather than adding separable surfaces. |
| **Warnings** | none | No release-safety risk attached. |

Recorded 2026-08-20 from the read-only classifier, which writes no file of its
own. Advisory: it wires no pull-request emission and no branch creation. Note
that the route speaks to **structural seams**, not to size — this slice's
reviewability crossing is a separate question, recorded in the Reviewability
Budget, and the classifier neither sees nor comments on it.

To produce the decision, run the classifier against the feature directory:

```text
runner helper atomicity-route specs/art-008-feedback-sweep
```

See the classifier script at
[`speckit-autopilot/scripts/atomicity-route`](../../speckit-autopilot/scripts/atomicity-route).

---

## Layer Plan

**When this is filled:** immediately after the Atomicity Route is recorded, and
always before Analyze or Implement continues. The layer planner runs only when
the route is exactly `split-PR`. On every other route the run records
`layer_plan.status = skipped` here and in `autopilot-state.json`, names the
route that caused the skip, and continues with the route as context.

| Field | Value |
|-------|-------|
| **Status** | `skipped` |
| **Reason** | The layer planner runs only on an exact `split-PR` route. The atomicity classifier returned `one-navigable-PR`, so the planner is skipped by rule rather than by choice. |
| **Helper invoked** | no |
| **Warnings** | none |

Mirrored in `autopilot-state.json` under `layer_plan`. The route travels forward
as implementation context.

### Tasks-phase reviewability gate

The runner's `reviewability-gate` supports **setup mode only** on the installed
runner; tasks mode is deferred and MUST NOT be invoked as an active helper.
Recorded per the deferred-helper contract:

| Field | Value |
|-------|-------|
| Helper id | `reviewability-gate` |
| Requested mode | `tasks` |
| Status | `deferred` |
| Invoked | no |
| Deferral reason | installed runner supports setup mode only |

**Fallback evidence chain, which is what the phase actually runs on.** The
setup-mode result recorded at scaffold returned `warn` with empty `blockers`.
The plan-phase estimator returned `pass` with `projected: 0` and is an **absent
measurement**, because it classifies none of this slice's paths as production.
The operator-facing figure is therefore the hand-derived one, whose only home
is `spec.md`'s Reviewability Budget superseding notes: at this writing 1120 to
1720 reviewable LOC, midpoint near 1420, over **twelve** production files and
twenty-two authored files. That is a size-only block on reviewable LOC at the
midpoint, a size-only block on production files at 12 against a block of 8, and
a warn on authored files at 22 against a warn of 15. Both blocks are recorded
as operator-accepted under the size-crossing rule and continue into marker
planning rather than stopping the run; the PRSG-013 precedent is cited in the
Trust boundary remediation section's budget consequence.

**No marker planning state is created.** House precedent is that pass-or-warn
evidence without a split demand creates none, and the atomicity route is
`one-navigable-PR`. `tasks.md` remains the task source and is not marker state.

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

The first pass raised six findings and closed all six. A **second, scoped pass**
ran on 2026-08-22 against the consumer-scoping amendment alone, which the first
pass never saw. Its findings are below.

#### Scoped re-run: the consumer-scoping amendment

| ID | Severity | Issue | Evidence | Resolution |
|----|----------|-------|----------|------------|
| A-1 | CRITICAL | Eleven tasks cite `FR-007h` and `FR-012g` as acceptance. Neither requirement exists in `spec.md`; both entered in `tasks.md` alone at commit `5d4f36606`. Traceability breaks for every task the amendment added. | `tasks.md` T095–T101, T103–T105, T107; `spec.md` requirement list runs FR-007g → FR-008 and FR-012f → FR-013 | Repointed all eleven citations to the requirements that carry the content: `FR-010a` (classifier, piped observation), `FR-008c` (tool scoping, Codex sandbox), `FR-011b` (analyst, structured edit). No requirement added, so 54/54 coverage and the budget are unchanged. |
| A-2 | HIGH | `tasks.md`'s superseding budget note says it repeats the spec's live figure and repeats the **superseded** one — 705–1080, "Production files stay at 7", "15 to 16" — while T014 in the same file says 12 production files. The file contradicts itself. | `tasks.md:20-31` against `tasks.md` T014 and `spec.md`'s second superseding note | Split into a first note kept as history and a second carrying the live 1120–1720 / ~1420, 12 production files, 22 authored files, both blocks operator-accepted. T014's stale quote of the live figure corrected with it. |
| A-3 | HIGH | SC-015 claimed that every tool call attributed to a scoped-agent dispatch names a tool on that agent's allowlist, "demonstrated by" a fixture. FR-008a's capture records the agent name, comment id, prompt, and returned record — not an agent's tool calls — and the corpus is a deterministic harness with no live agent, so no fixture can produce that evidence. A security criterion asserting unproducible evidence is the "rule nothing executes" defect the spec names elsewhere. | `spec.md` SC-015 against FR-008a's captured-dispatch paragraph | Narrowed to the two halves that are producible: the declaration pinned by Layer 5 equality, and the routing measured over the captured corpus. The dropped claim is recorded explicitly as what the criterion does not claim, alongside the harness-enforcement limit it already carried. **Flagged for consensus — this narrows a security criterion.** **Resolved 2026-08-23, CRL row 8**: all three analysts, 2-of-3 majority `narrowing correct and sufficient`, the codebase dissent answered. Three additions applied to SC-015 — the corrected reason, T098's binding probe named, and the platform assumption stated. |
| A-4 | MEDIUM | The consumer-scoping record said the sanitized block is "handed over by path under FR-004d's directory" and "the sanitized blocks are passed by path". FR-010a hands the block in the dispatch prompt, and the contract states nothing here is written to disk. | `ART-008-workflow.md` consumer-scoping section against `spec.md` FR-010a and `contracts/sweep-classifier-output.md:13-15` | Corrected both sentences to in-prompt transport, naming T097 as the fixture that goes red if an implementation spools a block to a file. |
| A-5 | MEDIUM | The contract bounds `edit.anchor` at 512 bytes. FR-011b stated no cap, its stop list named three fields rather than four, and the contract's own `malformed_record` budget list omitted the anchor — so the cap had no stop behind it. | `contracts/sweep-classifier-output.md:218` and its Validation table, against `spec.md` FR-011b item 2 | Cap and its stop added to FR-011b, the anchor added to the contract's `malformed_record` budget list, and T094's diagnostics extended. Stops rather than cuts, for the reason the `replacement` does: a cut anchor matches different bytes. |
| A-6 | MEDIUM | The design concept records Q13 but `question_count` and "Questions asked" both still read 12, and an unapplied authoring instruction block ("TWO COUNT SITES IN THE SAME FILE") sat committed in the document body. | `ART-008-design-concept.md:10`, `:18`, `:475-477` | Both counts set to 13; the instruction block removed. |
| A-7 | LOW | T095 specifies the allowlist comparison as an ordered tuple; FR-008c specifies equality over the parsed set. Ordered comparison adds a reorder failure mode no requirement asks for. | `tasks.md` T095 against `spec.md` FR-008c assertion 2 | T095 aligned to set equality, explicitly silent on ordering. |
| A-8 | LOW | `plan.md`'s trust-boundary mechanism 3 asserts "production files stay seven" in place, with no superseded marker or pointer, against the one-home rule the spec states. | `plan.md:139` | Marked as true through that pass and pointed at the live figure's home. |
| A-9 | LOW | Layer 1 requires a `Capability path:` marker in every non-excluded agent, and its subtest is worded as an output-format requirement, while FR-010a makes a fifth field in the classifier record malformed. A future editor could satisfy the subtest by breaking the contract. | `tests/speckit-pro/layer1-structural/validate-capability-pointer.py:92-98` (a substring search over whole file text) against `spec.md` FR-010a | T098 and T104 now state that the markers live in body prose and never in the returned record, with the substring-search mechanics cited. |

Nine findings, nine remediated, one flagged for consensus on category rather
than on doubt. **This supersedes the Phase 6.5 sentence reading "Analyze closed
all six it raised and routed nothing to consensus"** for the amendment surface;
the G6.5 verdict itself is not re-scored here, because the gate is terminal for
the plan stage and its recorded reasoning still holds.

#### Verdicts recorded as no-finding

- **F-1 is closed at the consumer layer.** Every consumer of reviewer text and
  its surface: the runner helper (deterministic code, no model);
  `sweep-classifier` (`Read`); `sweep-analyst` (`Read`, `Grep`, `Glob`), four
  dispatches per amended item including synthesis; the orchestrator, which
  keeps `Bash` but is never handed a body — construction rather than
  enforcement, with FR-008b's captured-dispatch fixture as the regression
  tripwire. The `anchor` never leaves: the contract makes anchor bytes on the
  `amendment` leg a red fixture. The Codex network residual is disclosed rather
  than closed.
- **The Layer 5 carve-out is exactly two names, not a pattern.** T095's three
  assertions match the validator's actual structure: the role tuples at
  `validate-tool-scoping.py:29-48`, the suite builder iterating
  `TEST_METHOD_ORDER` at `:49-59`, and `OPEN_EXECUTORS` at `:31` for the
  disjointness assertion. Exemption is by membership, so `tools:` on a
  non-member stays red on the unchanged rule.
- **The Layer 6 corpus does not restale.** `corpus-manifest.json` binds twelve
  named roles and no directory scan; `run-efficiency-benchmarks.py:247` reads a
  TOML per named role. `artifact-author` already ships on both platforms
  outside the corpus. T109's claim is correct and needs no task.
- **Codex parity is asymmetric by design and is disclosed as such.** The TOML
  format carries no tool allowlist and no network field, `validate-codex-agents.py:42`
  rejects every Claude-only field, and `sandbox_mode` is the only lever. FR-008c
  claims read-only filesystem and network per Codex defaults, and claims
  nothing about tools. SC-007 is parity of sweep outcome, not of enforcement
  strength.


#### Adversarial refutation of the scoping design

Run beside the scoped Analyze, read-only, against one claim: the summary's rule
that no agent holding `Bash` or the network reads reviewer text. **The claim was
broken.** The mechanism under it is sound — a Claude `tools:` allowlist is
honored for plugin agents, and the Layer 5 carve-out survived a deliberate
attempt to widen it — but the claim reached past what the mechanism covers.
Eleven attack lines, nine upheld, one refused, one left unproven.

Three findings needed a change beyond wording, and all three are fixed.

| ID | Finding | Fix |
|----|---------|-----|
| R-1 | T098 told the implementer to probe whether an empty `tools:` allowlist resolves. A bare `tools:` key is YAML null and reads as omitted, so the agent inherits the operator's whole surface, `Bash` included, and the dispatch succeeds. Nothing in the response separates that from a zero-tool resolution, and T098 itself concedes a subagent cannot see its own resolved surface. The implementer would then pin the inheriting form into T095 and the suite would report the boundary intact while it was off | Probe replaced. It now asks whether the allowlist **binds**, in a session with an MCP server connected, and stops the slice if a tool outside the allowlist is reachable |
| R-2 | T104 required the shipped `sweep-analyst.md` body to state that `Read`, `Grep`, and `Glob` "reach this repository and nothing else". They are permission-scoped and never path-scoped: a plugin agent cannot set `permissionMode`, inherits the parent session's, and the autopilot requires a permissive one. `spec.md` stated this residual for the classifier only, whose output is an enum; the analyst's is 8192 bytes of prose that the run pushes to a public remote | FR-011b now states the residual the way FR-010a states the classifier's, and T104 forbids the body from claiming a repository boundary it does not have |
| R-3 | The plan's redaction paragraph claimed all structured returns cross the FR-012f surface. Two per amended item do not: the three perspective records carry a `finding` of free prose and an `evidence` array, and FR-012f's leg set is closed at four with no leg among them | The paragraph now names the two that cross nothing. The `anchor` is bounded another way and is settled; the perspective `finding` is the one open decision, below |
| R-4 | `capability-discovery.md` states that the plugin never pins an agent availability allowlist. Both new agents pin one, both are required to carry the capability pointer to that file, and no task amended it | Amendment folded into T098, with the Codex mirror |

Refused: the `edit.anchor` attack. The contract admits only a verbatim excerpt
of the target file's committed bytes and stops the run on any match count other
than one, so bytes an attacker chose cannot survive it. Recorded as a disclosed
residual for the pre-check window rather than as a finding.

Already disclosed in existing spec text, no edit: reviewer-derived prose in the
Feedback Sweep Log's `Disposition` cells being re-read by later Bash-holding
runs; the amended artifacts being read on the next run by `implement-executor`
and `gate-validator`; the Codex variants' shell.

**Left unproven, and now folded into T098's replacement probe.** Whether a
`tools:` allowlist naming only built-in tools actually excludes the MCP tools
the session inherits. The documentation implies it; nothing demonstrates it.
`mcpServers` is ignored in plugin agents, so what a scoped agent could see is
the parent session's inherited set, which is exactly what the allowlist is
claimed to cut off. If it does not, `sweep-analyst` holds every installed MCP
server while reading reviewer text and the scoping buys nothing. T098's probe
answers it before any other implementation work depends on the answer, and
stops the slice on a bad answer rather than shipping a control that does not
bind.

**The summary's rule was rewritten rather than defended.** `plan.md` now states
what is enforced: no agent holding `Bash` or a network tool is ever handed a
reviewer comment *body*; reviewer-*derived* text still reaches the orchestrator,
bounded and named; the scoped agents' read tools are permission-scoped rather
than path-scoped; and on Codex the claim is a read-only filesystem and nothing
about the tool set.

---

## Phase 6.5: Confidence Gate

**When to run:** After Phase 6 commits and before Phase 7 begins. Gate semantics
are unchanged; this section records the verdict so a later session can read it.

| Field | Value |
|-------|-------|
| Mode | `advisory` — resolved at Step 0.6b from no flag and no local config |
| Threshold | 0.90 |
| Composite confidence | **0.80** |
| Verdict | below threshold, advisory. The plan stage ends here either way, because G6.5 is its terminal step |
| Evidence | the Phase 6 synthesis emit below, computed over the completed Analyze pass |

📊 Confidence: 0.80

- Task understanding: 0.90
- Approach clarity: 0.80
- Requirements alignment: 0.86
- Risk assessment: 0.68
- Completeness: 0.78

**Why each score, kept because a later run reads this rather than re-deriving
it.** Task understanding at 0.90: the Analyze catches were specific and
correctly scoped, held below 1.00 only because nothing in them is independently
confirmed. Approach clarity at 0.80: the fixes are concrete mechanisms, but one
interface question stays open, namely where the write-point path check gets its
resolved target. Requirements alignment at 0.86: full requirement, criterion and
task cross-referencing across three Clarify sessions and three checklist
domains, capped because two upstream defects are filed rather than fixed and
this slice guards only its own caller. Risk assessment at 0.68, the lowest:
the reviewability crossing is disclosed and gated by a blocking task, which
earns real credit, but no active gate can measure it and the estimate had
moved 330 to 830 across four revisions at this gate, since superseded — two
later passes took the high end to 1080 — which is itself a risk signal.
Completeness at 0.78: the planning artifacts are internally consistent and G0
through G6 all
passed, but no code exists and the remaining gates are deferred, so this
measures plan completeness rather than implementation readiness.

**The remediation loop was considered and declined, with the reason recorded.**
The procedure offers up to three focused rounds on the lowest criterion. For
`risk_assessment` that round would re-run Analyze against remaining open
findings, and there are none — Analyze closed all six it raised and routed
nothing to consensus. The facts behind the 0.68 are not a remediable gap: the
budget crossing is already disclosed, already reasoned through lever by lever,
and already gated by a blocking checkpoint before implementation phase 3; the
estimate drift is history that cannot be un-drifted; and the one thing that
would genuinely raise the score is a real measurement against real code, which
this stage by definition cannot produce. Iterating would re-score identical
evidence and inflate the number without changing anything a reader should act
on. A low score that is true is more useful here than a high one that is
manufactured.

**What this means for the next run.** A later `--stage implement` invocation
reads this recorded verdict rather than re-running the gate. The score is
advisory, so it does not block, but it is deliberately not a pass, and the
operator should treat the risk-assessment line as the thing to satisfy before
letting implementation run unattended.

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
| 1 - Setup (design-artifact corrections) | 7 | 7 | Commit `819eb3547`. Contract and data model corrected: `matched_lines`, bounded anchors with `anchors_dropped`, `self_login` precondition, explicit never-inferred `feature_dir`, and full request/response/diagnostics for both named surfaces. Also closed CHK049, whose deferral expired when the contract edit landed, and lengthened the example node id to twenty-one characters so it meets the token-run floor the spec states for it. T094's contract already existed from the analyze remediation and was marked complete on verification |
| 2 - Foundational (helper + registration) | 9 | 9 | Commit `ed1691cf4`. **76/76 on the harness.** Helper skeleton, three `read_only.py` touch points, registry entry, harness expectations, fixture-manifest record, canonical request fixture, and the operator's budget decision. **T110 added during implementation**: no shipped task owned the `HELPER_CASES` entry, without which every added helper raises `KeyError`. Two corrections the phase forced: registration row 6 gained its missing third clause, and row 2 was renamed `path_keys_by_helper` and narrowed to real path inputs, because every key it lists is rewritten by `normalize_path_input` and listing a reviewer comment body there would corrupt the bytes the golden envelope pins |
| 3 - User Story 1 | 28 | | In progress |
| 4 - User Story 2 | 30 | | |
| 5 - User Story 3 | 5 | | |
| 6 - Polish | 13 | | |

---

## Reviewability Checkpoint (T014)

**Recorded 2026-08-23, at the Phase 2 checkpoint, before any user-story work.**
T014 requires the operator's budget decision to be written here before Phase 3
of `tasks.md` may begin. Both halves of the budget are over a block, and both
are accepted.

| Half | Plan-time figure | Live figure | Threshold | Verdict |
|---|---|---|---|---|
| Reviewable LOC | 515-830, midpoint ~630 | **1120-1720, midpoint ~1420** | warn 400, block 800 | **over block, accepted** |
| Production files | 7 | **12** | warn 6, block 8 | **over block, accepted** |

**The decision is taken against the live figure, not the plan-time one.** Its
only home is `spec.md`'s second Reviewability Budget superseding note. Three
passes moved it after the plan closed: the artifact-verification repair took it
to 595-910, the trust-boundary remediation added 110 to 170 lines of helper code
and reference prose to reach 705-1080, and the consumer-scoping pass added 415 to
640. The midpoint now crosses the 800 block, not only the high end. The file
count reached 12 through the four sweep agent definitions across both platforms
plus the `install.py` edit that the closed `REQUIRED_CODEX_AGENT_NAMES` bundle
forces.

**Lever (b) is taken, and the decision is the operator's, recorded as such.**

**Reason.** The trust boundary is not separable from the feature. F-1 and F-2 are
the feature's own consumers reading attacker-controllable text, and a slice that
ships the reader without the scoping ships the vulnerability.

**Precedent.** PRSG-013 recorded a size-only block at 1800 reviewable LOC across
78 files and the run continued.

**The other two levers, and why they are not taken.** Lever (a), deferring the
serialization-family registry rows `feature-flags`, `prompt-tuner`, and
`triage-board`, saves 15 to 30 lines at the cost of FR-007b. It stays available
and unexercised. Lever (c), re-slicing, is refused for the same reason the plan
refused the read-path-only split: that split produces a checkpoint which reads
feedback and acts on none of it.

**The plan's rejected split is not silently revived.** Read-path-only 1a was
considered and rejected at plan time, and this acceptance does not reopen it.

---

## T098 Binding Probe: UNRUN, and why

**Recorded 2026-08-23. This gate is unmet, not passed, and not failed.**

T098's stop condition reads: *"If either tool is reachable, the scoping does not
hold and this task stops the slice rather than shipping a control that does not
bind."* The probe that would settle it did not run. **No result is claimed and
none was fabricated.**

**Why it could not run.** Claude Code loads plugin agents from the versioned
plugin cache, not from worktree source. `speckit-pro/agents/sweep-classifier.md`
exists in this branch but the runtime resolves no such agent, failing with
`Agent type 'speckit-pro:sweep-classifier' not found` and listing the twelve
agents the installed 2.27.0 cache carries. Staging the new definition into that
cache to make the probe possible was attempted and refused by the permission
classifier, which is correct: writing an agent definition into the plugin cache
is agent-config self-modification, and a control proved only after the prover
edited the control's own configuration would be worth little anyway.

**What this does and does not mean.**

- The stop condition is **not** triggered. It fires when a denied tool is
  *reachable*, and nothing here observed a reachable tool. An unrun probe is not
  evidence that the allowlist fails to bind.
- The stop condition is **not** discharged either. Nothing here observed the
  allowlist binding. The declaration half is pinned statically by Layer 5,
  which asserts `tools: Read` by equality and the four denials by membership,
  and that is a check on an enforcing control's configuration rather than on its
  enforcement.
- SC-015 already says exactly this, and says it deliberately. It was narrowed at
  Analyze consensus row 8 to claim only what a fixture can produce, on the
  ground that no committed fixture proves a negative over a model's tool use.
  This entry is that narrowing meeting its first real instance rather than a new
  discovery.

**How it gets discharged.** After this feature ships and the plugin cache
refreshes to the release carrying `sweep-classifier.md` and `sweep-analyst.md`,
dispatch each agent once with a probe that asks it to enumerate its tool surface
and attempt one `Bash` call, and record the verbatim result here. Two things must
hold: no tool named `mcp__*` is present, and the `Bash` attempt is refused. A
reachable tool at that point stops the slice, exactly as T098 states.

**The empty-allowlist question stays closed.** FR-008c forbids probing whether an
explicitly empty `tools:` list is accepted, because a bare `tools:` key is YAML
null, reads as omitted, and makes the agent inherit the operator's whole surface
including `Bash`. That probe would look like success at the exact moment it
disarmed the control. `Read` is the floor and stands.

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
| 5 | Clarify | Clarify S2 | Should the export registry recognize the three `PROMPT_LEAD` imperative variants beside the markdown leads? | `[security]` | 1 | **2 of 3 majority**, register with the kind recorded. All three high confidence, no escape hatch | Register. Codebase confirmed the lead line is the only differentiator between the two kinds and that `export_kinds` is an already-shipped closure-tested two-value vocabulary, so the field is its fourth appearance rather than a new enum. Spec-context showed the roadmap's "the prompt kind deliberately bypasses this sweep" sentence describes pasting into an agent, a different channel from pasting into the pull request, and that leaving the variants unregistered is the worse security posture because the imperative text then reaches the analysts as unlabelled free text that the security-keyword routing does not match. **Dissent, domain-researcher:** register but neutralize, excluding a recognized prompt paste from the automated amend path, on the grounds that a tag nothing consumes is inert telemetry while the research on marking untrusted spans works by changing how the model sees them. Answered inside the majority option rather than dismissed: FR-007c requires the registered lead to be carried as matched metadata rather than passed through as free text. Applied to `spec.md` FR-007b, FR-007c, FR-007d | codebase-analyst, spec-context-analyst, domain-researcher |
| 6 | Clarify | Clarify S2 | How does the sweep recognize its own reply, given that a conversation-surface reply is a new top-level comment from a trusted author? | `[security, codebase]` | 1 | **3 of 3 unanimous**, an anchored HTML-comment marker, with an author match as a second required filter. All high confidence, no escape hatch | Marker plus author, both required. Codebase and spec-context each searched for a bot identity and found none, so matching the author alone would exclude the operator's own genuine comments — the reviewer this checkpoint exists for. Codebase added the argument against a visible sentence: a reviewer quoting a rendered reply to disagree with it would copy that sentence into a genuine new comment and be silently skipped, which an HTML comment cannot cause. Domain established that GitHub exposes no writable metadata on a comment, so an in-body marker is the accepted answer rather than a workaround, and contributed the anchoring rule and the author-as-second-filter pairing. Spec-context found direct precedent for markers-as-contract in the packet schema, and showed FR-006 is load-bearing for convergence rather than hygiene. Applied to `spec.md` FR-006, FR-006a, FR-015, FR-015a | codebase-analyst, spec-context-analyst, domain-researcher |
| 7 | Clarify | Clarify S2 | Does corroboration status `skipped` stop the implement stage or let it proceed? | `[domain, codebase]` | 1 | **both-agree**, stop. Both high confidence, no escape hatch | Stop. Codebase found this is a vocabulary gap rather than an open question: User Story 3 and SC-006 already counted the unreachable-tool case as a fourth stop condition while FR-019 named only three by token, and nothing in the repository treats an unreachable tool as evidence of a clean state. Domain supplied the distinction that carries it, mapping `no_record` to a gate that does not apply and `skipped` to a gate that applies and could not be evaluated, with four standards lineages resolving that case toward deny. Two domain refinements taken: the stop must read differently from the three discrepancy stops, and the missing operator override is a gap to record rather than grounds to flip the default. One refinement declined: cause-differentiated retry, because no retry utility exists in the runner and the sweep has no second read point, which codebase established and which would be new machinery outside this slice. Applied to `spec.md` FR-019, FR-019a, FR-019b, SC-006, Assumptions, Non-Goals | codebase-analyst, domain-researcher |
| 8 | Analyze | Analyze scoped re-run | A-3: the SC-015 narrowing dropped the claim that every tool call attributed to a scoped-agent dispatch names a tool on that agent's allowlist. Was the narrowing correct, and is the narrowed criterion sufficient? | `[security]` | 1 | **2 of 3 majority**, narrowing correct and sufficient. All three high confidence, no escape hatch. Routed to all three analysts because `[security]` never runs single-routed | Correct, and sufficient, with three complementary additions all applied. Spec-context found the narrowing removed an internal contradiction rather than weakening the spec: FR-010a already carried the same limit ("no fixture proves a negative over a model's tool use, and this document claims none"), so the criterion asserting that negative was the half with no producer. It also established the project's discriminator, build the evidence when an instrument exists and narrow when none does, with R-1, R-2 and the Codex half as precedent. Domain grounded the declaration half in the vendor guarantee that `tools:` is enforced as an allowlist, making static equality a check on an enforcing control's configuration rather than a hint, and cited assurance-case practice that narrow-and-record is the discipline while asserting unevidenced is the defect. **Dissent, codebase-analyst: `narrowing correct but insufficient`.** Answered rather than dismissed, and it changed the edit twice. It proved the narrowing's stated reason false: the Layer 7 transcript harness does carry a `sidechain` scope and its grounding runner already asserts tools were not invoked, so an observer exists. The conclusion survives on attribution and cost instead, and the spec now says so. It also found, converging with spec-context independently, that the spec disclaimed a proof the feature does produce, namely T098's binding probe. Applied to `spec.md` SC-015: the corrected reason, the named binding probe, and the stated platform assumption | codebase-analyst, spec-context-analyst, domain-researcher |

---

## Artifact verification defect

**Found 2026-08-21, after the plan stage closed and draft PR #464 was open.**

### What shipped

Three of the four generated draft pages — `implementation-plan.html`,
`code-approaches.html`, and `module-map.html` — were committed **byte-identical
to their shipped gallery templates**. Each still carried the title
`NIMBUS-101 Offline Draft Sync` and the sample-content notice reading "This is
sample content … waiting to be filled with a real feature." Only
`spec-explainer.html` had been filled. The pull-request body linked all four as
though they were real.

### Two causes, and only one is an orchestration slip

1. **The gap count was read off a truncated report.** The `artifact-author`
   agent exhausted its budget composing its summary. The returned fragment was
   recorded as `gaps: 0` when the honest reading was *unknown*.
   `phase-execution.md` already ruled that a report which cannot be read as an
   outcome list is a whole-set gap; the run did not apply its own rule.
2. **Nothing verified the files on disk, and that is a product gap.** Even a run
   that had correctly recorded a whole-set gap would still have left three
   template copies in `artifacts/` to be committed and pushed. The contract
   trusted the report end to end.

### Why the verification that was run did not catch it

The check asked "is every fill region populated?" That question **cannot fail**
on these templates. They ship as complete worked examples, not blank scaffolds,
so an untouched page is populated prose. The test has to be positive: does the
page differ from its template, and does it name this feature.

### The fix

- `references/phase-execution.md` and its Codex mirror gain an on-disk
  post-condition: after the dispatch returns and **before the boundary commit**,
  a page byte-identical to its template, or carrying a `class="sample-notice"`
  element, is a gap regardless of the reported outcome, and the file is deleted.
  Fail-open is preserved — outcomes are converted, never blocked.
- The same references now state explicitly that a truncated summary is missing
  information, never evidence of success.
- The three pages were filled from the planning record and verified positively.
- `autopilot-state.json` carries the corrected record under
  `terminal_step.artifacts.as_first_recorded` rather than a silent overwrite.

### Recommended follow-up, deliberately not taken here

A repository assertion that no committed `specs/*/artifacts/*.html` is
byte-identical to a shipped template would catch this class in CI. It belongs in
`tests/speckit-pro/unit/test-artifact-gallery.py`, which is **not** in this
slice's Declared File Operations block, so it is left for its own change rather
than widened into this one.

---

## Trust boundary remediation

**Run 2026-08-21, after the plan stage closed, at the operator's direction.**
A review of the sweep against Anthropic's and OpenAI's published
prompt-injection guidance produced six findings (F-1 to F-6). Three remediation
passes, each adversarially verified, carried them into `spec.md`, `plan.md`,
and `tasks.md`. The review and its revision history are the published Claude
Code artifact titled "Sweep Trust Boundary Review", owned by the operator; its
URL carries a session-shaped identifier and is deliberately not recorded here.

### What changed in the contract

- **FR-004d.** Every sweep byproduct lives under
  `specs/<feature>/.process/feedback-sweep/`, whose first write is its own
  `.gitignore` containing `*`, so the directory ignores itself in any consumer
  repository; this repository's root `.gitignore` carries the entry as well.
  Removal before proceeding stays as hygiene. Four fixtures.
- **FR-012f.** One redaction surface, a second named surface of
  `sweep-pr-feedback`, runs on every outbound leg and **proceeds redacted
  rather than stopping**: a stop-and-discard here was a permanent livelock
  against FR-012a's batched bookkeeping commit. Six hit classes, tightened so
  the spec's own text matches none of them, pinned by a corpus-scan fixture.
  Any redaction event stops the run after publication so a human sees it.
- **FR-007g.** Analyst-payload shaping moved into that same surface so it has
  a producer and fixtures that can fail. Defined span order, bounded
  placeholder echo, both truncation and withheld-span counts reported to the
  reviewer in the reply's last line.
- **Disclosures.** The analysts' `disallowedTools` bounds repository writes
  and nothing else, including this repository, and the relaxation prerequisite
  is a policy reversal `validate-tool-scoping.py` forbids (plan item 7). There
  is no deterministic boundary on the forward path; the helper classifies and
  forwarding discipline is orchestrator prose. Quoting is the expected route
  for untrusted text, and the checkpoint gates merge, not disclosure.
- **Fixed shapes.** The amendment commit subject is built from ids alone;
  the reply marker stands alone on line 1.

### Findings ledger

| Pass | Against | Closed | Left |
|------|---------|--------|------|
| 1 | F-1..F-6 | applied | 2 blocking, 23 major, 14 minor found |
| 2 | 39 | 28 fixed, 6 dissolved, 4 accepted | 1 blocking, 11 major found |
| 3 | 35 | 30 fixed, 2 dissolved, 2 accepted | 2 major, 22 minor found |
| hand | 2 major | both fixed (consumer-repo ignore; owed-reply call count) | 22 minors disclosed |

The two pass-1 prescriptions that failed verification were the author's own:
a fail-closed stop in a convergence-invariant feature, and a fixture asserting
a hand-written string. Both are recorded in the review artifact, struck
through, with what replaced them.

### Consumer scoping: F-1 and F-2 mitigated rather than disclosed

**Run 2026-08-22, at the operator's direction, after the three passes above.**
F-1 (the consensus analysts and the orchestrator read reviewer-derived text
while inheriting the operator's full tool surface) and F-2 (a maintainer
quoting untrusted text launders it across the boundary) were left DISCLOSED.
The operator chose to mitigate both inside this slice rather than accept them
or defer them to a later one. The decision and its two rejected alternatives
are recorded as **Q13** in the design concept; this is what it changes.

- **Two scoped consumers, both platforms, used only by the sweep.**
  `sweep-classifier` takes one sanitized, delimited body — the FR-007g output,
  handed over **in the dispatch prompt**, never by path — plus the closed class
  vocabulary, and returns `{class, target, reason}` with the reason capped at
  512 bytes and passed through the FR-012f redaction surface before any use.
  `sweep-analyst` is dispatched three times per amended item with the
  perspective in the prompt and once more in a synthesis prompt, and returns a
  structured edit `{file, anchor, replacement}` against the three-file
  allowlist, also redacted before the write. Claude frontmatter pins
  `tools: Read` and `tools: Read, Grep, Glob`; both deny `Agent`, `TeamCreate`,
  `SendMessage`, and `Skill`. Codex pins `sandbox_mode = "read-only"`.
- **Classification leaves the orchestrator.** The orchestrator holds `Bash`, so
  the rule is that it is never handed a body: the `gh` read is piped into the
  runner, the sanitized blocks pass through the orchestrator unread and reach
  each agent in its dispatch prompt rather than through a file, and what comes
  back is an enum, a target, and bounded text. FR-010a and
  `contracts/sweep-classifier-output.md` both fix that transport — the contract
  says nothing here is written to disk — so an implementation that spools a
  block to `FR-004d`'s directory to hand it over fails T097 rather than
  satisfying this record. That is construction rather than
  enforcement — the orchestrator could read the file it wrote — and the plan's
  item 7 carries the residual rather than dissolving it.
- **Synthesis does not go to `consensus-synthesizer`,** which declares no
  `tools:` allowlist and inherits `Bash`. Routing sweep synthesis there would
  reopen F-1 one hop downstream. `sweep-analyst` synthesizes instead.
- **The Layer 5 carve-out is the only policy change.**
  `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py` gains
  `UNTRUSTED_INPUT_CONSUMERS = ("sweep-classifier", "sweep-analyst")` and three
  assertions: members are exempt from the repository-wide no-`tools:` rule,
  each pins exactly its stated allowlist, and the tuple's membership is
  asserted exactly so an open executor cannot be added to it. Members also deny
  the orchestration set and `Skill`, and a fourth assertion pins
  `sandbox_mode = "read-only"` on both TOMLs without folding them into
  `CODEX_READ_ONLY_ROLES`, which would pin model and effort values this design
  never specified. The rationale lives in the module docstring. No existing
  agent definition is edited, so the Layer 6 digest chain does not restale.
- **The Codex claim is bounded by what the loader honors.** The installer reads
  `name` and `model` and copies the rest byte-for-byte; Layer 1 forbids
  `tools`/`disallowedTools` in a TOML outright; no `network` field exists
  anywhere in the loader or the validators. The spec therefore claims only
  "read-only filesystem; network per Codex defaults", and records that
  `sandbox_mode = "read-only"` does not sandbox MCP server processes
  (`speckit-pro/codex-skills/install/SKILL.md:53-62`).
- **Ungoverned now, with a named deferral.** The Layer 6 corpus binds exactly
  twelve roles through a digest chain with no regeneration script, and
  `artifact-author` already shipped outside it on both platforms with a green
  suite. The two sweep agents ship the same way. Non-Goals gains an entry owned
  by no spec yet: they join the governed corpus under a future G56R spec,
  because a security boundary nothing digest-binds is a gap, and the reason it
  is deferred is that G56R qualification is its own workstream.
- **The seam.** The sweep carries its own dispatch inside its Phase 7 setup
  block in both phase-execution references and never emits a category-tagged
  consensus item, so `consensus-protocol.md`'s routing table is never consulted
  and Clarify, Checklist, and Analyze are unchanged. The **routing table** is
  untouched; the file itself stays MODIFIED for T058's `Sweep` `Type` value.
- **The installer is a production file.** `REQUIRED_CODEX_AGENT_NAMES` is a
  closed inventory, so two new TOMLs force a line into
  `speckit-pro/speckit_pro_runner/helpers/install.py`. Commit `1d58e5cbb`
  (#445) is the precedent and the ripple map, including
  `docs-site/src/content/docs/reference/agents.md`.

### Budget consequence, for T014

Live reviewable range **1120 to 1720, midpoint near 1420**, over the 800 block
at the midpoint; **production files 12**, over the 8-file block; authored files
**22**, a warn under the 25 block. The consumer-scoping pass added **415 to
640** reviewable lines and five production paths on top of the trust-boundary
remediation's 705-to-1080; the derivation's one home is `spec.md`'s second
Reviewability Budget superseding note.

**Both crossings are size-only and both are OPERATOR-ACCEPTED at the T014
lever, which is lever (b): accept the block explicitly.** The reason is that
the trust boundary is not separable from the feature — F-1 and F-2 are
properties of the agents the sweep dispatches, so mitigating them means
shipping those agents, and a slice that ships the sweep without them ships the
disclosed exposure. Precedent for a recorded block whose run continued:
`docs/ai/specs/.process/PRSG-013-workflow.md:570` records `status=block,
is_size_only=true, reviewable_loc=1800, total_files=78`, and the run continued
with the crossing captured as marker-planning input. The live midpoint of 1420
is under that 1800. Lever (a), deferring the three serialization-family
registry rows, saves 15 to 30 lines against a crossing this size and is not
taken; lever (c), re-slicing, is rejected on the ground recorded in the plan
and restated above.

### Sites deliberately left unchanged

- :37 Plan row and :38 Checklist row — dated plan-time and checklist-time
  records that already say "since superseded — the live figure's one home is
  `spec.md`'s Reviewability Budget superseding note". The pointer still
  resolves to the live figure, so the rows need no edit.
- :79 G0 gate ("L5 192") and the 7659/7659 suite counts — dated observations of
  runs that happened. The carve-out's new subtests will move the live L5 count;
  the record of that run does not move with it.
- :118 G5 gate — already carries "counts as at the gate; the trust-boundary
  remediation grew them afterwards, see the Tasks row", which now covers this
  pass too.
- :451 Specify Results, "Declared reviewability budget | ~330 reviewable LOC,
  7 production files, 10 total, within budget (projected); Plan re-derives" —
  explicitly a projection superseded by Plan.
- :668-669 Plan artifacts table, "22 entries across a production surface of 7"
  — a dated record of the block as the plan phase left it; the block was
  already at 24 before this pass.

---

---

## Lessons Learned

### What Worked Well

- Grounding the refilled pages in `plan.md`'s Declared File Operations block and
  the design concept's Q&A log, rather than in recollection, kept every module
  path and task ID checkable against a source.

### Challenges Encountered

- A fail-open agent plus a report-only contract produced a silent, plausible
  wrong answer. The pages looked finished; only a diff against the template
  showed they were not.
- The same truncation failure hit twice in one run, on the consensus
  synthesizers and again on the artifact author. Both times a partial reply was
  read as a complete one.

### Patterns to Reuse

- **Verify positively.** Ask what an artifact *is*, not whether something is
  missing from it. Emptiness checks pass on templates that ship populated.
- **A truncated agent summary is missing information, not a clean result.** When
  an agent dies mid-summary, record `unknown` and re-check the artifact on disk.
- **Diff generated output against its source template** before committing it.
  One `diff -q` per page would have caught this at the boundary commit.

---

## Project Structure Reference

```text
racecraft-plugins-public/
├── speckit-pro/                                   # Plugin source (ships to installers)
│   ├── agents/                                    # sweep-classifier.md, sweep-analyst.md (new, scoped consumers)
│   ├── codex-agents/                              # sweep-classifier.toml, sweep-analyst.toml (new, sandbox_mode read-only)
│   ├── skills/speckit-autopilot/references/       # phase-execution.md, consensus-protocol.md, workflow-file-protocol.md
│   ├── codex-skills/speckit-autopilot/references/ # phase-execution-codex.md, workflow-file-protocol-codex.md
│   └── speckit_pro_runner/helpers/                # read_only.py (new feedback helper), registry.py, install.py (codex agent inventory)
├── tests/speckit-pro/                             # Repository-only validation
│   ├── layer5-tool-scoping/                       # validate-tool-scoping.py (UNTRUSTED_INPUT_CONSUMERS carve-out)
│   └── unit/fixtures/read-only-helpers/           # helper request fixtures + harness manifests
├── docs/ai/specs/                                 # Roadmap, .process/ exhaust (this file, design concept)
└── specs/art-008-feedback-sweep/                  # CONTRACT artifacts: spec.md, plan.md, tasks.md, SPEC-MOC.md
```

---

Template based on SpecKit best practices. Populated from the ART-008 design concept on 2026-08-20.
