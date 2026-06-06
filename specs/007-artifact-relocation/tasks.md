---
description: "Task list for Artifact relocation — tiering, .process/, collapse"
---

# Tasks: Artifact relocation — tiering, .process/, collapse

**Input**: Design documents from `/specs/007-artifact-relocation/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md

**Tests**: TDD requested for the deterministic scripts/lints — the Layer-1 lint and
the two Layer-4 extensions are written FIRST (RED), then the production change makes
them pass (GREEN). The redirect prose edits (US1) are not unit-tested in isolation;
they are covered by the existing Codex-parity validators and the end-to-end fixture
verification in Polish.

**Reviewability**: Projected reviewable LOC ≈ 250 (< 400 warn / 800 block); production
files ≈ 0 (every touched `.sh` lives at `speckit-pro/skills/.../scripts/…`, which does
NOT start with `scripts/`, and `.sh` is not a production extension match — see
plan.md Reviewability Budget); total files ≈ 12–14 (at/near the 15 warn line — warn
only). The mechanical gate computes ≥2 surfaces from filenames; plan.md RATIFIES a
`split exception` (the gate's sanctioned escape hatch) because this is one logical
surface artificially sharded by filename patterns. T009A records that decision before
implementation.

**Organization**: Tasks are grouped by user story. US1 (redirect) sequences before US2
(collapse/gate/lint) because US2 is inert until US1 actually writes under `.process/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

This is a Claude Code plugin marketplace (bash + `jq` + markdown). No compiled runtime,
no `src/`. Production change lives under `speckit-pro/skills/.../{scripts,templates,references}/`,
`speckit-pro/codex-skills/.../`, one NEW repo-root `.gitattributes`, and one NEW file in
the existing `speckit-pro/tests/layer1-structural/` array. Tests run via
`bash speckit-pro/tests/run-all.sh` from the `speckit-pro/` directory.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Record the pre-change test baseline so SC-007's "passing count ≥ baseline"
can be checked after implementation. The Foundation layer from the workflow prompt (the
repo-root `.gitattributes` rule + its guard lint) lands in Phase 2.

- [x] T001 Confirm the worktree baseline is green before any change: from
  `speckit-pro/`, run `bash tests/run-all.sh --layer 1` and record the passing count
  (expected baseline 765/765) so SC-007's "≥ baseline" can be checked at the end. Do
  NOT modify any file in this task.

**Checkpoint**: Baseline recorded — Foundation work can begin.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The repo-root collapse rule + its guard lint. EVERYTHING in US2 (gate arm,
consumer ensure-step) duplicates the `.process/` glob this phase establishes, and the
lint (FR-011/FR-012) guards that duplication. This MUST exist before US2's gate/ensure
tasks so the cross-file agreement is anchored.

**⚠️ CRITICAL**: No US2 work begins until the repo-root rule + lint are in place.

> **TDD (RED → GREEN)** — strict top-to-bottom order: write the lint (T002) so it FAILS
> against the current repo (no repo-root `.gitattributes` yet, or no `.process/` rule),
> register it in the runner (T003) and observe RED through `run-all.sh --layer 1`, then
> add the rule (T004) and observe GREEN. Writing precedes registering so the runner never
> references a not-yet-created script.

- [x] T002 Write the collapse-scope lint
  `speckit-pro/tests/layer1-structural/validate-process-gitattributes.sh` (FR-012/AC-2.4/SC-005),
  modeled on the existing `validate-pr-checks-sentinel.sh` (same `#!/usr/bin/env bash` +
  `set -euo pipefail` header, same pass/fail reporting convention). The lint MUST parse
  the repo-root `.gitattributes`, and for every line containing `linguist-generated`,
  assert its path pattern is scoped to `.process/` (contains the `.process/` segment);
  FAIL if any `linguist-generated` rule targets a path that could include a CONTRACT
  artifact (FR-012/AC-2.4/SC-005). The lint MUST cover BOTH a positive case (a
  `.process/`-scoped rule passes) and a negative case (a broadened rule such as
  `**/* linguist-generated=true` fails) per SC-005 — drive the negative case with a temp
  fixture inside the test, never by mutating the real repo-root file. The lint MUST NOT
  make the gate parse `.gitattributes` (it only validates the static file; the gate stays
  self-contained per FR-011). Run it now and confirm it FAILS (RED — no `.process/` rule
  exists yet).
- [x] T003 Register the new Layer-1 lint in the runner: add
  `validate-process-gitattributes.sh` to the Layer-1 validator array in
  `speckit-pro/tests/run-all.sh` (alongside the existing structural validators —
  EXTEND the array, do NOT renumber or replace any existing entry, per FR-015). Re-run
  `bash tests/run-all.sh --layer 1` and confirm the new lint reports RED there (the
  script now exists, so no missing-file error — it fails on the absent `.process/` rule).
- [x] T004 Create the NEW repo-root collapse rule file `.gitattributes` at the worktree
  root containing exactly one rule: `**/.process/** linguist-generated=true` (FR-007).
  Use `linguist-generated=true` ONLY — do NOT add `-diff` (FR-008: relocated artifacts
  stay diffable and loadable on demand). Re-run the lint (T002) and confirm it now PASSES
  (GREEN). This dogfoods the rule in this plugin repo AND gives the lint its target.
- [x] T009A Verify the reviewability budget against the planned task/file scope and
  record the split decision in plan.md: confirm the ratified `split exception` is
  present (the gate greps changed `.md` for the phrase `split exception`; plan.md
  already carries it in the Constitution Check + Complexity Tracking). No new split is
  warranted (each half still touches `.sh` + `.md`). This task only confirms the
  exception text is in place before implementation proceeds — do NOT add a feature flag
  or abstraction.

**Checkpoint**: Repo-root `.gitattributes` exists and is lint-clean; the `.process/`
anchor is established. US1 and US2 can now proceed (US1 first — US2 is inert until US1
writes under `.process/`).

---

## Phase 3: User Story 1 - Tier and redirect speckit-pro-authored exhaust (Priority: P1) 🎯 MVP

**Goal**: Classify every speckit-pro-authored artifact as CONTRACT or EXHAUST, and
redirect the three authored EXHAUST artifacts (design-concept doc, workflow file, UAT
runbook) into `.process/` — design-concept + workflow under `docs/ai/specs/.process/`,
UAT runbook under `specs/<NNN>/.process/`. No deletion; every redirected file still
exists and is readable. Each Claude-skill prose edit is mirrored identically into its
Codex counterpart (FR-006/AC-1.4) in this same story.

**Independent Test**: Scaffold a brand-new spec and run through UAT-runbook generation;
confirm design-concept + workflow land under `docs/ai/specs/.process/`, the UAT runbook
lands under `specs/<NNN>/.process/`, every redirected file exists and is readable, the
PR body still renders its UAT section from the relocated runbook, and the Codex skill
redirects to the identical paths.

> **No isolated unit tests here**: these are markdown/prose path-string edits. They are
> covered by the existing Codex-parity validators (`validate-codex-skills.sh` + Layer-8)
> run in Polish, and by the end-to-end fixture verification (T021). Each SKILL.md edit
> is paired with its Codex mirror IN THIS STORY (see T011/T012).

### Implementation for User Story 1

- [x] T010 [US1] (Taxonomy / AC-1.1) Add the CONTRACT-vs-EXHAUST artifact taxonomy note
  to `specs/007-artifact-relocation/spec.md` is ALREADY present (Key Entities); instead,
  surface the taxonomy where authors see it: add a short "Artifact tiering (CONTRACT vs
  EXHAUST)" note to `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` stating the
  CONTRACT set stays at its existing location and the three authored EXHAUST artifacts go
  to `.process/`. This satisfies FR-001/AC-1.1 at the authoring surface (documentation,
  not a new artifact file). [paired Codex mirror: T011 covers the same SKILL.md region.]
- [x] T011 [US1] (Redirect, scaffold — FR-002/AC-1.2) In
  `speckit-pro/skills/speckit-scaffold-spec/SKILL.md`, repoint the four scaffold
  touchpoints for the design-concept doc and the workflow file to
  `docs/ai/specs/.process/` instead of directly in `docs/ai/specs/` (FR-002): (1) the
  `mkdir`/directory-prep step, (2) the grill-me `output_path`, (3) the workflow `Write`
  target, and (4) the `git add` path. Ensure the redirect CREATES
  `docs/ai/specs/.process/` when absent (FR-014). Both files MUST still exist and be
  readable after the run — no deletion (FR-004/AC-1.2). Edit ONLY the
  design-concept + workflow paths — do NOT touch the CONTRACT set and do NOT redirect any
  extension-authored exhaust (Non-goal).
- [x] T012 [US1] (Codex mirror of T010+T011 — FR-002/FR-006/AC-1.2/AC-1.4) Apply the
  IDENTICAL taxonomy note and the IDENTICAL four-touchpoint redirect to
  `docs/ai/specs/.process/` in
  `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`, so both coding agents write
  to the same paths with zero drift (FR-006/AC-1.4/SC-006). This is the paired mirror for
  T010 and T011 in the same story.
- [x] T013 [P] [US1] (Redirect, workflow template self-refs) In
  `speckit-pro/skills/speckit-coach/templates/workflow-template.md`, repoint the
  design-concept-doc and workflow self-references to `docs/ai/specs/.process/` so the
  template's own pointers match where scaffold-spec now writes. [P]: independent file
  from T011/T014. (No Codex mirror owed — this is a coach template, not a paired
  Claude/Codex SKILL.md; confirm there is no codex-skills counterpart of this template
  before marking done.)
- [x] T014 [US1] (Redirect, UAT runbook generator output) In
  `speckit-pro/skills/speckit-autopilot/references/post-implementation.md`, repoint the
  UAT-runbook generator output path (≈ L564) and its `git add` path (≈ L590) to the
  feature's own `specs/<NNN>/.process/` directory (FR-003), creating that directory when
  absent (FR-014). This is a Claude reference file; confirm whether a Codex counterpart
  of this reference exists — if it does, pair a mirror task; if it does not, note "no
  Codex counterpart" when marking done (the parity mandate applies to mirrored skills,
  not to Claude-only references).
- [x] T015 [US1] (Redirect, PR-body read path — AC-1.3/FR-005) In
  `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh`, repoint the
  UAT-runbook READ path (≈ L179) and the `./uat-runbook.md` link (≈ L188) to
  `specs/<NNN>/.process/`, while KEEPING the `## UAT Runbook` section heading so the PR
  body still renders that section from the relocated file (FR-005/AC-1.3). Do NOT remove
  the section; only repoint the source path. (This `.sh` lives under
  `speckit-pro/skills/.../scripts/`, so it counts zero production files per the gate
  heuristic — see plan.md.)
- [x] T016 [US1] (Out-of-scope guardrail note — AC-1.1 boundary) In
  `specs/007-artifact-relocation/spec.md`, confirm the "Out of Scope" entry stating
  extension-authored exhaust (retrospective report, verify-tasks report) is NOT
  redirected by this feature and stays review-visible (its post-merge cleanup is owned by
  the `archive` extension). The entry already exists; this task verifies it is intact and
  adds nothing that would redirect extension exhaust (Non-goal enforcement). No `git mv`
  sweep is added.

**Checkpoint**: All three authored EXHAUST artifacts redirect to `.process/` in BOTH the
Claude and Codex skills; the PR body still renders its UAT section; the CONTRACT set and
extension-authored exhaust are untouched. US1 is independently demonstrable via T021's
fixture even before US2's collapse ships.

---

## Phase 4: User Story 2 - Collapse, align the gate, and lint the collapse rule (Priority: P2)

**Goal**: Collapse relocated exhaust out of the review diff (achieved by the repo-root
rule from Phase 2 + the consumer ensure-step here), align the reviewability gate's
diff-mode LOC accounting so `.process/` lines drop out while CONTRACT lines stay counted,
and ensure the collapse rule reaches consuming projects idempotently. The collapse-scope
lint (FR-012) already landed in Phase 2 as the Foundation guard.

**Independent Test**: In a repo containing both a `.process/` file and a contract
artifact with known line counts, confirm the gate counts only the contract lines as
reviewable and excludes the `.process/` lines (diff-mode); confirm the repo-root collapse
rule exists and is `.process/`-scoped; confirm scaffolding into a consuming project writes
the same rule idempotently (twice ≠ duplicate); confirm the lint fails if the rule is
broadened.

> **TDD (RED → GREEN)** for the two deterministic Layer-4 extensions, in strict
> top-to-bottom order (each test immediately precedes the implementation that makes it
> pass):
> - T017 extends the gate test FIRST (diff-mode assertion) → RED → T018 adds the gate
>   arm → GREEN.
> - T019 extends the ensure-step test FIRST (idempotency + safe-write) → RED → T020
>   folds the ensure-step into the existing script → GREEN.
> **Diff-mode is mandatory**: markdown is never a `production_file`, so a tasks-mode gate
> test would be vacuous — the new assertions MUST exercise diff-mode (changed-files)
> accounting.

### Gate exclusion: test then implement (RED → GREEN)

- [x] T017 [P] [US2] (Gate exclusion test — SC-003/AC-2.2/FR-010) EXTEND
  `speckit-pro/tests/layer4-scripts/test-reviewability-gate.sh` with ADDITIVE
  diff-mode assertions (append new assertions; preserve every existing one per FR-015):
  given a change that adds known line counts to BOTH a `specs/<NNN>/.process/…` file and
  a CONTRACT artifact (e.g. `spec.md`), assert the gate's reviewable-LOC total EXCLUDES
  the `.process/` lines and INCLUDES the contract lines. Add the no-false-exclusion case
  (a path with NO `/.process/` segment is counted) and the no-op case (a change with zero
  `.process/` paths leaves the count identical to pre-feature) per FR-010. Run now and
  confirm the new assertions FAIL (RED — the gate has no `.process/` arm yet). [P]:
  different file from T019.
- [x] T018 [US2] (Gate arm — FR-010/AC-2.2/SC-003) In
  `speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh`, add ONE `case`
  arm to `is_excluded_generated()` (lines ≈ 48–57):
  `*/.process/*|*.process/*) return 0 ;;` (the arm pinned in plan.md line 237) so any
  path carrying the `/.process/` segment is excluded from reviewable-LOC accounting.
  HARDCODE the `.process/` glob — the gate MUST NOT parse `.gitattributes` (FR-011); the
  duplication with the repo-root rule is intentional and guarded by T002's lint. Leave
  the pre-existing dead-code arm (`docs/ai/workflows/*/exports/*`, ≈ L54) UNTOUCHED
  (CLAUDE.md rule 3 — mention, don't delete). Do NOT add a flag/option (Non-goal).
  Re-run T017 and confirm GREEN.

### Consumer ensure-step: test then implement (RED → GREEN)

- [x] T019 [P] [US2] (Consumer ensure-step idempotency + safe-write test —
  SC-004/AC-2.3/FR-009) EXTEND
  `speckit-pro/tests/layer4-scripts/test-ensure-reviewability-preset.sh` with ADDITIVE
  assertions (preserve existing ones per FR-015) over a temp consumer repo:
  (a) **create branch** — no repo-root `.gitattributes` → ensure-step CREATES it
  containing exactly the rule (FR-009a);
  (b) **append branch** — pre-existing `.gitattributes` WITHOUT the rule → ensure-step
  appends exactly one copy and PRESERVES all pre-existing lines byte-for-byte (FR-009c);
  (c) **idempotency** — running the ensure-step TWICE leaves exactly one copy of the rule
  (FR-009 / SC-004), including when the rule is already present with differing surrounding
  blank lines (whitespace/trailing-newline-tolerant match, FR-009b);
  (d) **no-trailing-newline** — a pre-existing file whose last byte is NOT `\n` does NOT
  get the rule concatenated onto the final line (newline normalized first, FR-009 edge
  case);
  (e) **both branches converge** on the single-rule end state.
  Run now and confirm these FAIL (RED — no ensure-step arm exists yet). [P]: different
  file from T017.
- [x] T020 [US2] (Consumer ensure-step — FR-009/AC-2.3/SC-004; consensus-pinned
  safe-write) FOLD an idempotent `.process/`-rule ensure-step INTO the existing
  `speckit-pro/skills/speckit-coach/scripts/ensure-reviewability-preset.sh` (reuse its
  `PROJECT_ROOT=${1:-$PWD}`; do NOT create a new script or a flag — Non-goal). The
  ensure-step MUST implement the consensus-pinned safe-write mechanism from plan.md
  ("Consensus resolution — consumer `.gitattributes` safe-write") EXACTLY:
  1. **Presence guard** — detect with `grep -qxF "$rule" "$file"` (fixed-string `-F`
     because the rule contains `*` glob metacharacters; whole-line `-x`); short-circuit
     if already present (FR-009b).
  2. **Trailing-newline normalize** — if the existing file's last byte is not `\n`, add
     one BEFORE appending, so the rule never concatenates onto the last existing line
     (FR-009 edge case / git-lfs#167).
  3. **Same-directory temp file** — copy existing content (if any) into
     `mktemp "${file}.XXXXXX"` (SAME DIR keeps `mv` atomic on macOS where `/tmp` is a
     separate filesystem), append the rule to the temp, then atomically `mv` it over the
     target; `trap 'rm -f "$tmp"' EXIT` to avoid orphaned temps.
  4. **Atomic rename** — the final `mv` is the single commit point; an interrupted run
     leaves the original intact (no partial/truncated file — Edge Case / FR-009c).
  Both the create branch (no file) and the append branch (existing file) MUST converge on
  exactly one copy of the rule. Keep `#!/usr/bin/env bash` + `set -euo pipefail`, quote
  all variables (constitution II). Re-run T019 and confirm GREEN.

**Checkpoint**: The gate excludes `.process/` lines in diff-mode (CONTRACT lines still
counted); the consumer ensure-step writes the rule idempotently and corruption-safely;
the repo-root rule + lint from Phase 2 guard the collapse scope. US1 + US2 both work.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Prove the whole pathway green, confirm Codex parity, verify collapse on a
real fixture diff, and assemble the PR review packet. No new behavior is added here.

- [x] T021 Verify collapse + UAT rendering + zero-data-loss on a REAL fixture
  diff (cross-cutting US1 + US2): scaffold (or stage) a fixture change that places a file
  under
  `specs/<NNN>/.process/` AND a CONTRACT artifact, then (a) run the reviewability gate in
  diff-mode and confirm the `.process/` lines are excluded while the contract lines are
  counted, (b) run
  `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh` against the fixture
  and confirm the PR body still renders the `## UAT Runbook` section sourced from the
  relocated `specs/<NNN>/.process/` runbook, and (c) confirm all three redirected EXHAUST
  artifacts (design-concept doc + workflow under `docs/ai/specs/.process/`, UAT runbook
  under `specs/<NNN>/.process/`) STILL EXIST and are READABLE at their new locations after
  the run — zero data loss, no deletion (FR-004/SC-002).
  (SC-001/SC-002/SC-003/FR-004/FR-005/AC-1.3/AC-2.1/AC-2.2)
- [x] T022 Run the Codex-parity validators: from `speckit-pro/`, run
  `bash tests/layer1-structural/validate-codex-skills.sh` and the Layer-8 parity
  fixtures (`bash tests/layer8-parity/run-parity-fixtures.sh --dry-run`) and confirm zero
  drift between the scaffold-spec Claude SKILL.md and its Codex mirror in the redirect
  targets (FR-006/SC-006/AC-1.4).
- [x] T023 Run the full deterministic suite green: from `speckit-pro/`, run
  `bash tests/run-all.sh` (Layers 1, 4, 5) and confirm ZERO failures, with the passing
  count ≥ the T001 baseline (the new Layer-1 lint + the extended Layer-4 assertions add
  to the count; nothing previously passing regresses) — SC-007/FR-015.
- [x] T024 Assemble the PR review packet per plan.md's "PR review packet source":
  *what changed* (redirect of three authored exhaust artifacts into `.process/`;
  repo-root + consumer collapse rule; gate diff-mode exclusion; collapse-scope lint),
  *why* (~32% of a feature PR is exhaust burying the contract artifacts), *review order*
  (US1 before US2), *scope budget* (PASS via the ratified `split exception`),
  *traceability* (FR-001…FR-015 → tasks; SC-001…SC-007 → tests), *verification*
  (`bash speckit-pro/tests/run-all.sh` green + new lint + extended L4), *known gaps*
  (pre-existing dead-code gate arm left untouched), *rollback* (revert the single squash
  commit; the consumer `.gitattributes` append is additive + idempotent). Non-goals:
  extension-authored exhaust, `-diff`, legacy migration, moving the CONTRACT set.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 baseline — no dependencies, run first.
- **Foundational (Phase 2)**: T002 (write lint) → T003 (register lint, observe RED) →
  T004 (add rule, observe GREEN); T009A confirms the split exception. Strict order —
  writing the lint precedes registering it so the runner never references a missing file.
  BLOCKS US2 (the gate arm + ensure-step duplicate this phase's `.process/` glob and are
  guarded by its lint).
- **US1 (Phase 3)**: depends on Phase 2 only for the established `.process/` anchor
  convention. Sequenced BEFORE US2 because US2 is inert until US1 writes under
  `.process/`.
- **US2 (Phase 4)**: depends on Phase 2 (repo-root rule + lint) and on US1 having
  established the `.process/` write locations. Within US2: T017 (RED) → T018 (GREEN);
  T019 (RED) → T020 (GREEN).
- **Polish (Phase 5)**: depends on US1 + US2 complete.

### User Story Dependencies

- **US1 (P1)**: the source-side redirect. Independently demonstrable via T021's fixture
  even before collapse (exhaust at least segregated into `.process/`).
- **US2 (P2)**: depends on US1 (nothing to collapse until exhaust is under `.process/`)
  and on the Phase-2 Foundation rule/lint.

### Within Each User Story

- **US1**: each Claude SKILL.md edit (T010, T011) is paired with its Codex mirror (T012)
  in the same story. Prose edits, no internal RED/GREEN.
- **US2**: tests (T017, T019) are written and MUST FAIL before their implementation
  (T018, T020). Diff-mode only.

---

## Parallel Opportunities

- **T013** [P] — `workflow-template.md` is an independent file from the scaffold-spec
  SKILL.md edits (T011/T012) and the autopilot files (T014/T015); can run alongside them.
- **T017** [P] and **T019** [P] — the two Layer-4 test extensions touch different test
  files (`test-reviewability-gate.sh` vs `test-ensure-reviewability-preset.sh`) and can
  be written in parallel.
- NOT parallel: T011 and T012 are the same logical edit in two files but must stay
  byte-identical, so author T011 first then mirror — do not mark [P]. T018 depends on
  T017 (RED→GREEN, same gate); T020 depends on T019 (RED→GREEN, same script). T002→T003→T004
  is a strict RED/GREEN chain.

### Parallel example

```bash
# US2 tests — write both failing tests together (different files):
Task: "T017 Extend test-reviewability-gate.sh with diff-mode .process/ exclusion assertions"
Task: "T019 Extend test-ensure-reviewability-preset.sh with idempotency + safe-write assertions"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 (T001 baseline) → Phase 2 (T002–T004 repo-root rule + lint, T009A exception).
2. Phase 3 (US1 redirect + Codex mirror) → demonstrate via T021 fixture that exhaust now
   lands under `.process/` and the PR body still renders its UAT section. This is a
   shippable increment: exhaust is segregated even before collapse accounting lands.

### Incremental Delivery

1. Foundation (repo-root rule + lint) → US1 (redirect) → US2 (collapse/gate/ensure) →
   Polish (parity + full suite + PR packet). US2 is inert until US1 ships, so the order
   is load-bearing, not cosmetic.

---

## Notes

- **Non-goals enforced by construction** (design-concept §Non-goals; plan.md Constraints):
  no task redirects extension-authored exhaust (T016 verifies the boundary), no task adds
  `-diff` (T004 uses `linguist-generated=true` ONLY), no task migrates a legacy
  `specs/<NNN>/` directory (FR-013 — every redirect is new-spec write-path only), no task
  makes the gate parse `.gitattributes` (T018 hardcodes the glob; T002 lints the static
  file; FR-011), and no task adds a flag/abstraction for a single call site (T020 folds
  into the existing script; constitution VI).
- **Diff-mode mandate**: markdown is never a `production_file`, so the L4 gate assertions
  (T017) MUST exercise diff-mode (changed-files) accounting — a tasks-mode test would be
  vacuous.
- **Codex parity**: every Claude SKILL.md prose edit that redirects exhaust is mirrored
  identically in the same story (T010/T011 → T012); guarded in Polish by T022.
- **Additive test changes only** (FR-015): the two L4 extensions APPEND assertions; the
  new L1 lint is REGISTERED alongside existing validators — nothing is renumbered or
  replaced.
- [P] tasks = different files, no dependencies on incomplete tasks.
- Commit policy: the orchestrator owns commits (autopilot). Do not commit from within a
  phase.
