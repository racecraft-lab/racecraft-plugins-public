---
description: "Task list for PRSG-006 — Plan-phase reviewability budget + gate threshold rework"
---

# Tasks: Plan-phase reviewability budget + gate threshold rework (PRSG-006)

**Input**: Design documents from `/specs/prsg-006-reviewability-budget/`

**Prerequisites**: plan.md (required), spec.md (FR-001…FR-015), contracts/ (estimator + gate JSON shapes)

**Tests**: TDD is REQUESTED for this feature (spec §Assumptions test coverage = L1/L3/L4/L8; plan §Test strategy). Every deterministic behavior gets an **L4 fixture asserting a KNOWN value** written **BEFORE** its implementation (red first). Required layers: **L1, L3, L4, L8**. **No L7** — PRSG-006 adds no new agent.

**Reviewability**: This task list stays within the spec's advisory budget (plan §Reviewability Budget: ~250–400 reviewable LOC, single primary surface = harness/adapter, ~11 files). No reviewability checkpoint task is required; if implementation drifts past 800 production LOC or a second primary surface appears, stop and split rather than adding tasks.

**Organization**: Tasks are grouped by user story (US1 = plan-phase estimator + autopilot wiring; US2 = gate rework) so each story is independently implementable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 or US2 (Setup / Foundational / Polish tasks carry no story label)
- All paths are repo-relative; shell paths are under `speckit-pro/`

## Scope guardrails (design-concept Non-goals — DO NOT generate tasks for these)

No split-PR emission (PRSG-007/008/009); no hard plan-phase block or re-slicing wiring (PRSG-010); no legacy-keyword migration of existing roadmaps (PRSG-011); no broadening of `is_production_file` to `.sh` plugin paths and no `is_excluded_generated()` `.process/` realignment (PRSG-001). These predicates are **reused as-is**; the known under-count of plugin `.sh` paths is recorded as a code comment, never fixed here.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the workspace and the two target script files before any change.

- [x] T001 Confirm the autopilot scripts directory `speckit-pro/skills/speckit-autopilot/scripts/` contains the existing `reviewability-gate.sh` (to rework) and does NOT yet contain `estimate-reviewable-loc.sh` (to create); confirm the L4 harness `speckit-pro/tests/layer4-scripts/test-reviewability-gate.sh` exists (to extend).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared per-file production-LOC constant + keep-in-sync comment markers, and confirm the reusable predicates both scripts depend on. Both user stories build on this.

**⚠️ CRITICAL**: No US1/US2 implementation may begin until the keep-in-sync marker convention and the reusable-predicate inventory are settled.

- [x] T002 Inventory the reusable gate functions/predicates that US1 and US2 both depend on, in `speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh`: `is_production_file` (:59), `is_excluded_generated` (:48), `surface_for_path` (:34), `emit_result` (:80), and the `WARN_LOC=400` (:19) / `BLOCK_LOC=800` (:22) constants. Record that they are reused as-is (no signature change) — this is the contract the estimator and the gate rework both rely on.
- [x] T003 Add the reciprocal keep-in-sync comment marker beside the gate's per-task `×40` heuristic at `speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh:199` — literal token `KEEP IN SYNC with estimate-reviewable-loc.sh` — noting the gate value is per-`tasks.md`-line while the estimator's is per-file (same magnitude, different unit). This is the gate half of the FR-007 drift-guard comment pair; the estimator half is added in T009.

**Checkpoint**: Foundation ready — US1 and US2 can now proceed in parallel (different files).

---

## Phase 3: User Story 1 - Preventive plan-phase reviewability budget (Priority: P1) 🎯 MVP

**Goal**: A deterministic standalone estimator (`estimate-reviewable-loc.sh`) projects each slice's production-LOC from `plan.md`'s `## Declared File Operations` block, emits a three-value status (`pass` / `over_budget` / `not_estimated`), applies the 1.5× greenfield allowance for all-`NEW` slices, never blocks, and is wired into the autopilot plan phase advisory-and-never-crash. Mirrored into the Codex surface (FR-015).

**Independent Test**: Run `estimate-reviewable-loc.sh` against an under-budget `plan.md` → silent `pass`; against an over-budget one → `over_budget` recorded, run continues (exit 0); against one with no parseable block → `not_estimated` with `projected: null`. Same `plan.md` twice → byte-identical stdout.

### Tests for User Story 1 (write FIRST — red before implementation) ⚠️

> Each fixture asserts a KNOWN expected value (parsed file count AND projected LOC), not merely two-run equality (FR-002). All live in `speckit-pro/tests/layer4-scripts/` (new estimator test file, e.g. `test-estimate-reviewable-loc.sh`) with fixtures under `speckit-pro/tests/layer4-scripts/fixtures/`.

- [x] T004 [P] [US1] Determinism + known-value fixture (FR-002, SC-001): a representative non-empty `## Declared File Operations` block; assert parsed planned-file count AND `projected` equal a hardcoded KNOWN expected value, then assert run-2 stdout is byte-identical to run-1. In `speckit-pro/tests/layer4-scripts/test-estimate-reviewable-loc.sh`.
- [x] T005 [P] [US1] Three-value status fixtures (FR-003, SC-002): under-budget block → `status:"pass"`, integer `projected`; over-budget block → `status:"over_budget"`, integer `projected`, **exit 0** (advisory, never blocks — FR-004, SC-002: an over-budget autonomous result must return exit 0 so the run proceeds); a `plan.md` with no/garbage block → `status:"not_estimated"`, `projected:null`, `declared_files` all zero (NOT a within-budget pass — vacuous-pass guard). In `test-estimate-reviewable-loc.sh`.
- [x] T006 [P] [US1] File-level error + errexit crash-safety fixture (FR-003 file-level path, spec Edge Cases): absent/unreadable `plan.md` and a usage error (missing/extra args) → **exit 2** (NOT `not_estimated`); assert the three content statuses keep exit 0 so the verdict is carried only in JSON `status`. In `test-estimate-reviewable-loc.sh`.
- [x] T007 [P] [US1] Greenfield + dedupe fixtures (FR-006, FR-008 no-double-counting): an all-`NEW` block → `greenfield:true` and the `thresholds.warn/block` scaled ×1.5 (400→600 / 800→1200); a block mixing `NEW` and `MODIFIED` → `greenfield:false`; a path listed twice → counted ONCE in `declared_files.*` and `projected`; the same path as both `NEW` and `MODIFIED` → de-duplicated to `MODIFIED` (so NOT greenfield). In `test-estimate-reviewable-loc.sh`.

### Implementation for User Story 1

- [x] T008 [P] [US1] Create `speckit-pro/skills/speckit-autopilot/scripts/estimate-reviewable-loc.sh` skeleton: `#!/usr/bin/env bash` + `set -euo pipefail` as first executable line, `chmod +x`, `bash -n` clean. Parse argv (exactly one `<plan.md>`; missing/extra args or unreadable file → exit 2 per `contracts/estimate-reviewable-loc.output.md`). Emit the contract JSON object to stdout via `jq` (fields `tool`, `status`, `projected`, `declared_files{production,new,modified,total_entries}`, `greenfield`, `thresholds{...}`). Makes T006 pass.
- [x] T009 [US1] Declare the per-file constant `PROD_LOC_PER_FILE=40` in `estimate-reviewable-loc.sh` with the FR-007 keep-in-sync comment block (literal token `KEEP IN SYNC with reviewability-gate.sh`, noting per-file vs per-task unit; "deliberately NOT a shared variable"). This is the estimator half of the drift-guard pair (gate half = T003). Add the documented known-limitation code comment that `is_production_file` does not match `.sh` plugin paths and broadening it is PRSG-001 (do not fix here — spec §Assumptions).
- [x] T010 [US1] Implement the declared-files parser in `estimate-reviewable-loc.sh`: count only lines matching the grammar `^[[:space:]]*[-*][[:space:]]+(NEW|MODIFIED)[[:space:]]+([^[:space:]]+)[[:space:]]*$` (POSIX ERE via `grep -E`); de-duplicate by repo-relative path before counting (estimator counterpart to the gate's `sort -u`); same path NEW+MODIFIED → treat as MODIFIED. Zero matching entries → `status:"not_estimated"`, `projected:null`. Makes T005 (`not_estimated` arm) pass.
- [x] T011 [US1] Implement production-LOC projection + budget verdict in `estimate-reviewable-loc.sh`: `projected` = (declared entries passing `is_production_file` & not `is_excluded_generated`) × `PROD_LOC_PER_FILE`; `status:"pass"` when ≤ applied budget else `status:"over_budget"`; all three statuses return exit 0. Reuse the gate's `is_production_file` / `is_excluded_generated` predicate definitions (no signature change). Makes T004 + T005 (pass/over_budget arms) pass.
- [x] T012 [US1] Implement greenfield detection + threshold scaling in `estimate-reviewable-loc.sh`: `greenfield:true` iff every non-excluded declared entry is `NEW` and none `MODIFIED` (FR-006, same file-set rule as the gate's diff-mode `A`-status detector); when true scale ONLY `thresholds.warn`/`.block` ×1.5 and report `base_warn`/`base_block`/`greenfield_multiplier`. Makes T007 pass.
- [x] T013 [US1] Register the new estimator test in the L4 runner so `bash tests/run-all.sh --layer 4` executes `test-estimate-reviewable-loc.sh` (match how `test-reviewability-gate.sh` is registered); confirm T004–T007 are green.
- [x] T014 [US1] Wire the plan-phase budget step into the Claude autopilot in `speckit-pro/skills/speckit-autopilot/SKILL.md` and `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` (FR-004, FR-005, SC-002): after `plan.md` exists, invoke `estimate-reviewable-loc.sh <plan.md>` guarded against `errexit` (`code=0; estimate-reviewable-loc.sh "$plan" || code=$?`). Branch on JSON `status`: `pass` → log "within budget" + record (silent); `over_budget` autonomous → record over-budget note and CONTINUE (advisory, non-blocking — FR-004, SC-002); `over_budget` interactive → surface the decision to the human (FR-005); `not_estimated` → record "not estimated (no declared production files)" and continue; non-zero exit → record "estimator could not run (exit N)" and continue. **No hard block, no re-slicing** (that is PRSG-010). Advisory-and-never-crash for every outcome.
- [x] T015 [P] [US1] Mirror ONLY the plan-phase budget instruction (T014 wording) into the Codex surface: `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` and `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md` (FR-015). The scripts and roadmap template stay single-copy (runtime-agnostic) — do NOT create a Codex copy of any `.sh` or the template.

**Checkpoint**: US1 fully functional — estimator passes its L4 fixtures and the plan phase invokes it advisory-and-never-crash on both Claude and Codex surfaces.

---

## Phase 4: User Story 2 - Reworked reviewability gate: correct metrics + typed exceptions (Priority: P2)

**Goal**: Rework `reviewability-gate.sh` (topology unchanged — no 4th mode): LOC counts production files only (FR-008), 1.5× greenfield allowance (FR-009), primary-surface-count becomes a warning not a block (FR-010), and a single shared `match_exception_pragma` honors only `Reviewability-Exception: {refactor|infra|upgrade}` on added Markdown lines, replacing the legacy three-phrase keyword at all three modes (FR-011/012/013). The roadmap template's Reviewability Contract is updated to match (FR-014).

**Independent Test**: Production-under-400-but-total-over-400 slice → no warn. Multi-surface slice → warning, not block, surface data retained in JSON. Block-sized slice with a valid added-line pragma → flipped to `exception`; with an unknown/missing/legacy pragma → stays `block` (fail-closed).

### Tests for User Story 2 (write FIRST — red before implementation) ⚠️

> All extend `speckit-pro/tests/layer4-scripts/test-reviewability-gate.sh`; the existing assertions on the legacy `transition_exception` key update in lockstep (FR-013 removes the old semantics).

- [x] T016 [P] [US2] Production-only metric fixture (FR-008, SC-003): a `diff`-mode slice whose production additions < 400 but whose total additions (with docs/tests) > 400 → `status` within-budget, no warn (proves `reviewable_loc` counts production files only); plus a no-double-counting assertion that a path appearing twice in the measured input contributes LOC once. In `test-reviewability-gate.sh`.
- [x] T017 [P] [US2] Greenfield fixture (FR-009): all non-excluded changed paths add-status `A` → `greenfield:true`, ONLY `thresholds.warn/block.reviewable_loc` scaled ×1.5 (other six threshold literals unchanged); one MODIFIED non-excluded file → no multiplier; a modified *excluded* lockfile alone still greenfield; assert `--no-renames` pins the boolean against an ambient `diff.renames` config. Cross-check the file-set rule agrees with the estimator's plan-mode greenfield (T007). In `test-reviewability-gate.sh`.
- [x] T018 [P] [US2] Surface-as-warning fixture (FR-010, SC-004): a multi-surface slice → a `warn` (never a surface-attributable `block`); `primary_surface_count` and `primary_surfaces` still present in the JSON output. In `test-reviewability-gate.sh`.
- [x] T019 [P] [US2] Typed-exception bypass list (FR-011/012, SC-005) — each case MUST NOT flip a `block`: class outside the set; partial/extended (`refactoring`, `ref`, `refactor,infra`); case variant (`Refactor`, `REVIEWABILITY-EXCEPTION:`); trailing content (`refactor # ok`); no space after colon (`Reviewability-Exception:refactor`); pragma on a context/removed diff line; pragma only in PR body / commit message; the `+++ b/<path>` header resembling the pragma. Plus the POSITIVE: a valid `Reviewability-Exception: refactor`|`infra`|`upgrade` on an ADDED `+` line of a committed `.md` flips `block` → `exception` (`exception_honored:true`, `exception_class` set). In `test-reviewability-gate.sh`.
- [x] T020 [P] [US2] Legacy-removal fixture (FR-013, SC-006) at ALL THREE modes (`setup`, `tasks`, `diff`): a document carrying only a legacy phrase (`split exception` / `transition exception` / `ratified exception`) and no typed pragma → stays `block` in each mode (legacy honored by no mode). In `test-reviewability-gate.sh`.
- [x] T021 [P] [US2] Fenced-code known-limitation fixture (spec §Edge Cases / contracts): a valid pragma inside a fenced code block in a committed `.md` WOULD flip the block (line-scoped, not Markdown-aware) — assert the residual as documented behavior (recorded, NOT asserted-away; section-scoping is PRSG-010). In `test-reviewability-gate.sh`.

### Implementation for User Story 2

- [x] T022 [US2] FR-008 production-only LOC: in `speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh`, gate `reviewable_loc_from_numstat` (:67) so it sums additions for production files only (`is_production_file` & not `is_excluded_generated`); keep warn=400/block=800 numbers. Preserve the existing `sort -u` path-dedupe so a path counts once. Makes T016 pass.
- [x] T023 [US2] FR-009 greenfield allowance: add a helper in `reviewability-gate.sh` using `git diff --name-status --no-renames "$range"`; greenfield iff every non-excluded changed path is add-status `A` (a modified non-excluded file disqualifies; a modified *excluded* lockfile does not). Pass the boolean into `emit_result` (:80) and scale ONLY the two `reviewable_loc` threshold literals (:130-131) ×1.5; report `greenfield` + applied thresholds in JSON. Makes T017 pass.
- [x] T024 [US2] FR-010 surface→warning: in `reviewability-gate.sh emit_result`, keep the surface-count warning (:90-92 region) and DELETE the surface-count blocker line (:97 region) so a surface count > 1 never contributes to `block`; keep `primary_surface_count` + `primary_surfaces` in the JSON. Makes T018 pass.
- [x] T025 [US2] FR-011/012 single shared matcher: add one function `match_exception_pragma` to `reviewability-gate.sh` — POSIX ERE via `grep -E`, canonical `^[[:space:]]*Reviewability-Exception:[[:space:]]+(refactor|infra|upgrade)[[:space:]]*$` (line-anchored, case-sensitive, exact enum, no trailing content, trailing `[[:space:]]*$` absorbs CRLF). Implement ONCE; never bash `[[ =~ ]]` over multi-line strings, never BRE. Update the JSON to `exception_honored` (boolean) + `exception_class` (matched class | null), updating the legacy `transition_exception` key (:133) in lockstep. Makes the positive arm of T019 pass.
- [x] T026 [US2] FR-012 diff-mode added-lines isolation: in `reviewability-gate.sh` `diff` mode (replacing the legacy grep at :231), read the pragma ONLY from added Markdown lines: `git diff "$range" -- '*.md' | grep '^+' | grep -v '^+++' | sed 's/^+//'` then apply `match_exception_pragma`. Never read from PR description or commit messages. Makes the context/removed-line and `+++`-header arms of T019 pass.
- [x] T027 [US2] FR-011/013 apply the shared matcher at `setup` and `tasks` modes, replacing the legacy `grep -Eiq 'transition exception|split exception|ratified exception'` at :160 (setup) and :201 (tasks) with `match_exception_pragma`. No mode retains the legacy matcher or silently loses its exception path. Makes T020 pass at all three modes.
- [x] T028 [P] [US2] FR-014 roadmap-template update: in `speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md`, update the `## Reviewability Contract` block to advertise the production-LOC thresholds, surface-count-as-a-warning wording, and the `Reviewability-Exception: <class>` pragma replacing the legacy `split exception` keyword. Keep the literal placeholder `Reviewability-Exception: <class>` (do NOT substitute a concrete class — `<class>` deliberately fails the matcher so the template example is never honored as a live exception). Single-copy (not mirrored to Codex).

**Checkpoint**: US2 fully functional — the gate passes the reworked metric/greenfield/surface/exception fixtures, honors only the typed pragma at all three modes, and the template matches.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: L1 structural guards (drift guard, template↔gate consistency, Codex-skills validation), the optional preset plan-template stub, and the developer-local L3/L8 records.

- [x] T029 [P] L1 keep-in-sync comment-presence assert (FR-007): add a structural check (in `speckit-pro/tests/layer1-structural/`, e.g. extend `validate-scripts.sh`) that the keep-in-sync comment marker is present in BOTH `estimate-reviewable-loc.sh` and `reviewability-gate.sh`. **Comment-presence only** — NOT a numeric value-equality check (the two constants differ in unit and the estimator's value is tunable; equality would false-fail on a legitimate tune). Matches the repo's comment-only keep-in-sync precedents.
- [x] T030 [P] L1 script-exists + template-vocabulary asserts (SC-007, FR-014): assert `estimate-reviewable-loc.sh` exists, is executable, and is `bash -n` clean; and assert the roadmap template's `## Reviewability Contract` advertises the production-LOC thresholds, surface-as-warning wording, and `Reviewability-Exception: <class>` vocabulary the gate honors (template↔gate consistency, so `setup`-mode parsing does not fail). In `speckit-pro/tests/layer1-structural/`.
- [x] T031 [P] L1 Codex-skills validation (FR-015): run/extend `speckit-pro/tests/layer1-structural/validate-codex-skills.sh` so it passes after the Codex mirror edit (T015); confirm the mirrored plan-phase wording is present in the Codex SKILL.md + phase-execution-codex.md.
- [x] T032 [P] [US1] Optional reviewability-preset plan-template stub (plan §Decision 1, spec §Deferred): add a `## Declared File Operations` stub (with the entry-grammar comment prompting `STATUS  repo-relative-path`, STATUS ∈ {NEW, MODIFIED}) to the reviewability-preset plan-template at `.specify/presets/speckit-pro-reviewability/templates/plan-template.md` so autopilot plan runs emit the block the estimator parses. Bounded to the reviewability preset ONLY — do NOT touch the general SpecKit `plan-template.md`. (Estimator degrades gracefully to `not_estimated` without it, so this is the authorized minor plan-tooling surface note, not a hard dependency.)
- [x] T033 L3 functional eval (developer-local, `claude -p`): record that the autopilot plan phase auto-approves under budget (silent pass) and records/surfaces when over budget. Note as developer-local before merge (not CI).
- [x] T034 L8 Codex Path-A/Path-B parity (developer-local): record parity around the mirrored plan-phase wording (T015). Note as developer-local before merge (not CI).
- [x] T035 Run `bash tests/run-all.sh --layer 1` and `bash tests/run-all.sh --layer 4` from `speckit-pro/` and confirm green (L1 drift-guard + template-vocab + codex-skills; L4 estimator + reworked gate fixtures) before merge.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup. T003 (gate keep-in-sync marker) and T002 (predicate inventory) gate both stories. T003 and T009 form the FR-007 comment pair the L1 guard (T029) asserts.
- **US1 (Phase 3)** and **US2 (Phase 4)**: Both depend only on Foundational. They touch largely disjoint files (estimator + autopilot wiring vs. the gate + roadmap template) and can proceed in parallel.
- **Polish (Phase 5)**: Depends on US1 + US2 (L1 guards reference both scripts; codex-skills validation references the US1 mirror; the L4 runner gate is over both stories' fixtures).

### User Story Dependencies

- **US1 (P1)** — independently testable via the estimator's own L4 fixtures and the plan-phase wiring; no dependency on US2.
- **US2 (P2)** — independently testable via the gate's L4 fixtures; composes with US1 but does not require it. The only soft coupling: T017 cross-checks that US2's diff-mode greenfield file-set rule agrees with US1's plan-mode rule (same rule, two inputs).

### Within Each User Story (TDD ordering)

- US1: T004–T007 (L4 fixtures, red) **before** T008–T013 (estimator impl, green) → T014 (wiring) → T015 (Codex mirror).
- US2: T016–T021 (L4 fixtures, red) **before** T022–T027 (gate impl, green) → T028 (template).

### Parallel Opportunities

- Foundational: T002 and T003 touch the same gate file — run sequentially.
- US1 L4 fixtures T004/T005/T006/T007 are `[P]` (independent fixture cases in the new test file). Estimator impl T008 is `[P]` to US2's work; T009–T012 are sequential within the one new script.
- US2 L4 fixtures T016–T021 are `[P]`. Gate impl T022–T027 edit the one gate file — sequential among themselves but `[P]` to all US1 work.
- T015 (Codex mirror), T028 (roadmap template), and the L1 asserts T029/T030/T031/T032 are `[P]` — distinct files.

---

## Parallel Example: User Story 1 L4 fixtures (red first)

```bash
# Author all four estimator L4 fixtures together (same new test file, independent cases):
Task: "Determinism + known-value fixture (T004)"
Task: "Three-value status fixtures (T005)"
Task: "File-level error + errexit crash-safety fixture (T006)"
Task: "Greenfield + dedupe fixtures (T007)"
# Then implement estimate-reviewable-loc.sh to make them pass (T008→T012).
```

## Parallel Example: cross-file Polish

```bash
# Distinct files — run in parallel:
Task: "L1 keep-in-sync comment-presence assert (T029)"
Task: "L1 script-exists + template-vocabulary asserts (T030)"
Task: "L1 Codex-skills validation (T031)"
Task: "Reviewability-preset plan-template stub (T032)"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup → Phase 2 Foundational (keep-in-sync markers + predicate inventory).
2. Phase 3 US1: write the four L4 fixtures (red), implement `estimate-reviewable-loc.sh` (green), wire the plan phase advisory-and-never-crash, mirror to Codex.
3. **STOP and VALIDATE**: estimator L4 fixtures green; plan phase never blocks/crashes on any status. This is the headline preventive-sizing value, independently shippable.

### Incremental Delivery

1. Foundation ready.
2. US1 (estimator + wiring) → test independently → the preventive plan-phase budget (MVP).
3. US2 (gate rework + template) → test independently → the detective gate becomes correct.
4. Polish: L1 guards + preset stub + developer-local L3/L8 records → full green before merge.

---

## Notes

- `[P]` = different files, no dependency on incomplete tasks.
- Every deterministic behavior has an L4 fixture asserting a KNOWN value written BEFORE its implementation (TDD red first) — FR-002.
- **No L7 tasks** (no new agent) and **no out-of-scope tasks** (split-PR, hard block, re-slicing, legacy migration, `is_*`/`.process/` realignment are PRSG-007/008/009/010/011/001).
- Reused predicates (`is_production_file`, `is_excluded_generated`) are NOT modified — the plugin-`.sh` under-count is a documented known limitation (PRSG-001), recorded as a code comment per T009.
- Do not expand past the advisory reviewability budget; if it grows past 800 production LOC or a second primary surface, split rather than add tasks.
