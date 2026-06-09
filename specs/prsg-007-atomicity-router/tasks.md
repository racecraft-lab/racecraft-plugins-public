# Tasks: Atomicity-test router (read-only classifier) (PRSG-007)

**Input**: Design documents from `/specs/prsg-007-atomicity-router/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/routing-decision.schema.json, quickstart.md

**Tests**: TDD is explicitly requested (workflow Task Structure: "write the L4 test … before the script logic"). Layer-4 test tasks are therefore included and ordered BEFORE the script logic they cover.

**Reviewability**: This task list MUST preserve the spec's reviewability budget — ~400 reviewable LOC, **1 production file** (`scripts/atomicity-route.sh`, per the gate's `scripts/*` production taxonomy), ~10 total files, one primary surface (scheduler/runtime). Fixtures, the Layer-4 test, and the prose edits are harness/adapter and docs/process surfaces. If the script logic expands past 400 reviewable LOC during implementation, stop at the T021 checkpoint and split rather than adding tasks.

**Organization**: Tasks are grouped by user story (US1 = classifier core, US2 = hard-atomic override + releasability), each independently testable, with a shared Foundation phase and a final Polish phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2). Setup / Foundational / Polish tasks carry no story label.
- Every task names an exact, repo-rooted file path.

## Deliverable path discipline (read before implementing)

All paths are repo-rooted at this worktree
(`.worktrees/prsg-007-atomicity-router/`). **NEVER** write to `.specify/`, a plugin
cache, or a scaffolded `src/`. The only production file is
`speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh`. The test and its
fixtures live under repo-root `tests/speckit-pro/` (the payload guard forbids `tests/`
inside the plugin dir).

### Out-of-scope guardrails (FLAG and STOP if a task drifts here)

- **PR emission / branch creation / multi-PR rewrite** → PRSG-008 (layer-planner) /
  PRSG-009 (multi-PR emission). NOT this spec. The classifier is read-only (FR-011) and
  emits one JSON object; it wires nothing.
- **Editing or `source`-ing `reviewability-gate.sh`, or extracting a shared lib** →
  forbidden by FR-015. The two matchers are DUPLICATED (FR-014, D6), never shared/called.
- **LOC / sizing computation** → forbidden by FR-002; that is the gate's job, not the
  classifier's.
- **Emitting `branch-by-abstraction`** → reserved enum value, never emitted by the MVP
  (FR-001, SC-008, D8).
- **Deep implementation of the three advisory probes** (flag-system, release-cadence,
  consumer-locality) → out of scope; they are advisory hints only (FR-010).
- **`change_class` JSON field** → forbidden (recoverable from `route` + `signals`, FR-011a).
- **Writing the route into `SPEC-MOC.md`** → forbidden; the route is recorded only in the
  workflow file's `## Atomicity Route` section, and only by the SKILL (FR-013, Assumptions).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the production script stub and the Layer-4 test directory tree so every later task has a concrete target. No detector logic yet.

- [x] T001 Create the production script stub `speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh` with `#!/usr/bin/env bash`, `set -euo pipefail`, and a usage comment naming the single positional arg `<feature-dir>`; `chmod +x` it; confirm `bash -n` passes (constitution II; D1).
- [x] T002 [P] Create the Layer-4 fixture root `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/` and the ten per-class fixture subdirectories named exactly: `additive-multi-seam/`, `single-additive-seam/`, `hard-atomic-rename/`, `hard-atomic-version-pin/`, `hard-atomic-destructive-migration/`, `hard-atomic-mutual-exclusion/`, `hard-atomic-out-of-tree-contract/`, `concurrency/`, `modify-heavy/`, `out-of-scope-empty/` (plan.md Declared File Operations; D10).
- [x] T003 [P] Create the Layer-4 test stub `tests/speckit-pro/layer4-scripts/test-atomicity-route.sh` that sources `tests/speckit-pro/lib/assertions.sh`, resolves the script path and fixture root, and is registered by the Layer-4 runner (naming convention `test-<script-name>.sh`, mirroring `test-reviewability-gate.sh`); `chmod +x`; `bash -n` passes (plan Testing; D10).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The CLI contract, JSON emitter, exit-code contract, and the two DUPLICATED path matchers — the spine every detector in US1/US2 writes into. No routing decision is made yet; detectors are wired in the story phases.

**⚠️ CRITICAL**: No user-story detector work can begin until this phase is complete.

- [x] T004 Implement the CLI front door + exit-status contract in `atomicity-route.sh`: accept exactly one positional `<feature-dir>`; on missing arg, absent/unreadable dir, or a present-but-unreadable `tasks.md`/`plan.md`/`spec.md`, emit `{"error": <string>}` to stdout via `jq` and `exit 2`; never `exit 1` (advisory-only, no block) (FR-011a error path, FR-012, SC-006; D1).
- [x] T005 Implement the success JSON emitter in `atomicity-route.sh`: a single `jq` call that prints one flat object with keys `route` (string), `releasable` (boolean), `signals` (string[]), `hints` (string[]), `warnings` (string[]), every array defaulting to empty; `exit 0` on any completed classification (FR-011, FR-011a, SC-001; D2).
- [x] T006 Implement the input-shape short-circuit in `atomicity-route.sh`: BEFORE any detector or the hard-atomic override runs, if `tasks.md` is missing or empty emit `route: "out-of-scope"`, `releasable: true`, empty arrays, and `exit 0` (a missing/empty `tasks.md` is NOT an error) (FR-003, edge case "Conflicting signals / precedence"; D3).
- [x] T007 Duplicate the two path matchers `surface_for_path()` and `is_excluded_generated()` from `reviewability-gate.sh` into `atomicity-route.sh` verbatim-equivalent, under a `# KEEP IN SYNC with reviewability-gate.sh` comment marker; make NO call to and NO edit of the gate (FR-014, FR-015; D6). NOTE: do NOT duplicate `is_production_file` — it has no caller here (no LOC metric, FR-002) and would be dead code (D6 note).
- [x] T008 Verify reviewability budget against the planned task/file scope (1 production file, ~400 LOC, ~10 total files, one primary surface) and record the split decision (remains one spec) or an exception BEFORE implementing detectors (template Reviewability gate; plan Reviewability Budget).

**Checkpoint**: CLI + JSON emitter + exit codes + out-of-scope short-circuit + duplicated matchers are in place. The script runs end-to-end on an empty feature dir (→ `out-of-scope`) and on a missing dir (→ exit 2). User-story detectors can now be added.

---

## Phase 3: User Story 1 - Atomicity classifier emits a route (Priority: P1) 🎯 MVP

**Goal**: The `tasks.md`-shape and additive-vs-modify detectors decide the seam-driven route — `split-PR` for a proven additive multi-seam change, `one-navigable-PR` for modify-heavy or uncertain — emitting the `change-shape:*` decisive tokens, plus the three advisory probes as `hints[]`-only.

**Independent Test**: Run the script against `additive-multi-seam/` and confirm `.route == "split-PR"`; against `single-additive-seam/` and `modify-heavy/` and confirm `.route` is single-PR-style / `one-navigable-PR` and never `split-PR`; against `out-of-scope-empty/` and confirm `.route == "out-of-scope"`. Observable from the script's stdout alone.

### Tests for User Story 1 (write FIRST, ensure they FAIL before implementation) ⚠️

- [x] T009 [P] [US1] Author the US1 routing fixtures' content (TDD inputs): `additive-multi-seam/tasks.md` (multiple independent additive capabilities → `split-PR`), `single-additive-seam/tasks.md` (one indivisible additive capability → single-PR-style), `modify-heavy/tasks.md` (modify signals `UPDATE`/`DELETE`/`DROP`/`CHECK`, no hard-atomic signature, no proven additive seams → `one-navigable-PR`); `out-of-scope-empty/` keeps an absent/empty `tasks.md` (add `.gitkeep` so the empty dir is tracked) (FR-004, FR-005, FR-003, SC-002, SC-008; quickstart scenarios 1, 2, 8, 9).
- [x] T010 [US1] In `test-atomicity-route.sh`, add the US1 routing assertions (these MUST FAIL before T013-T016): `additive-multi-seam` → `.route == "split-PR"` AND `change-shape:additive-multi-seam` ∈ `.signals`; `single-additive-seam` → `.route` ∈ {`one-navigable-PR`, `single-atomic-PR`} AND `.route != "split-PR"`; `modify-heavy` → `.route == "one-navigable-PR"` AND `change-shape:modify-heavy` ∈ `.signals` AND `.route != "branch-by-abstraction"` AND `.releasable == true` AND `.warnings == []`; `out-of-scope-empty` → `.route == "out-of-scope"` (FR-002, FR-006, FR-011b, SC-002, SC-005, SC-008; quickstart 1, 2, 7, 8, 9).

### Implementation for User Story 1

- [x] T011 [US1] Implement the `tasks.md`-shape detector in `atomicity-route.sh`: read `tasks.md` STRUCTURE to count independent additive capabilities / surfaces (structural seams), with NO LOC/sizing metric computed or consulted anywhere (FR-002, FR-004; D7).
- [x] T012 [US1] Implement the additive-vs-modify detector in `atomicity-route.sh`: distinguish modify signals (`UPDATE`, `DELETE`, `DROP`, `CHECK`) from additive signals (`CREATE TABLE`, nullable column additions), reading the path-signalled reading from all three artifacts (`tasks.md` + `plan.md` + `spec.md`) (FR-005; D4 path-signalled read).
- [x] T013 [US1] Wire the US1 routing decision in `atomicity-route.sh` using T011 + T012: proven additive multi-seam → `route: "split-PR"` and push `change-shape:additive-multi-seam` to `signals[]`; modify-heavy non-hard-atomic → `route: "one-navigable-PR"` and push `change-shape:modify-heavy` to `signals[]` (NEVER `branch-by-abstraction`) (FR-004, FR-005, FR-011b, SC-002, SC-008; D7, D8).
- [x] T014 [US1] Implement the abstain rule in `atomicity-route.sh`: when splittability is uncertain / no decisive seam signal, route to `one-navigable-PR`, emit NO `change-shape:*` token (empty-or-no-shape `signals[]`), and NEVER auto-select `split-PR` (FR-006, FR-011b, SC-005).
- [x] T015 [US1] Implement the three advisory probes (flag-system, release-cadence, consumer-locality) in `atomicity-route.sh` as HINTS ONLY: each emits into `hints[]` (with a TODO referencing its deferred deep-implementation home) and MUST NOT appear in `signals[]`; each degrades silently (a probe that cannot run emits no hint and never causes a non-success exit or block — empty `hints[]` is a normal success) (FR-010, FR-011b, edge case "Advisory probe cannot run"). FLAG: do NOT deepen these into decisive detectors — that is out of scope (PRSG-010 US3 for consumer-locality).
- [x] T016 [US1] Confirm the FR-003 detector ORDER in `atomicity-route.sh`: after the input-shape short-circuit (T006), detectors run (1) `tasks.md` shape, (2) additive-vs-modify, (3) flag-system probe, (4) release cadence, (5) consumer locality (FR-003; D3).

**Checkpoint**: US1 is fully functional and independently testable — the seam-driven route + abstain + advisory hints all work; the US1 assertions (T010) pass. MVP boundary.

---

## Phase 4: User Story 2 - Hard-atomic override and releasability warning (Priority: P1)

**Goal**: A hard-atomic signature forces `single-atomic-PR` (overriding any split signal); destructive-migration and concurrency classes are marked `releasable: false` with the canonical CI-green warning — releasability computed INDEPENDENTLY of the route.

**Independent Test**: Run the script against each `hard-atomic-*/` fixture and confirm `.route == "single-atomic-PR"` with the matching `hard-atomic:*` token in `.signals` even though seams are present; against `hard-atomic-destructive-migration/` and `concurrency/` and confirm `.releasable == false` with the matching `releasability:*` token and CI-green warning.

### Tests for User Story 2 (write FIRST, ensure they FAIL before implementation) ⚠️

- [x] T017 [P] [US2] Author the US2 hard-atomic + releasability fixture content (TDD inputs), each fixture given APPARENT seams so the override is exercised: `hard-atomic-rename/` (described exported-symbol rename action), `hard-atomic-version-pin/` (global version/runtime bump action), `hard-atomic-destructive-migration/` (a `.sql`/migration path + destructive SQL verb), `hard-atomic-mutual-exclusion/` (an auth/payment/lock/mutex primitive being introduced), `hard-atomic-out-of-tree-contract/` (a `/api/vN` or public/MCP/webhook contract break), and `concurrency/` (a concurrency signature). Use action/intent phrasing per D4/D5; for the destructive-migration and out-of-tree fixtures include the per-fixture `plan.md`/`spec.md` only where the three-artifact path read requires it (FR-007, FR-008; D4, D5; quickstart 3, 4, 5).
- [x] T018 [US2] In `test-atomicity-route.sh`, add the US2 assertions (these MUST FAIL before T019-T022): each `hard-atomic-*` fixture → `.route == "single-atomic-PR"` AND its matching `hard-atomic:*` token ∈ `.signals`; `hard-atomic-destructive-migration` → ALSO `.releasable == false`, `releasability:destructive-migration` ∈ `.signals`, and the destructive-migration CI-green sentence ∈ `.warnings`; `concurrency` → `.releasable == false`, `releasability:concurrency` ∈ `.signals`, and the concurrency CI-green sentence ∈ `.warnings`; a non-risk fixture → `.releasable == true` AND `.warnings == []` (FR-007, FR-008, FR-009, FR-011b, SC-003, SC-004; quickstart 3, 4, 5, 6).

### Implementation for User Story 2

- [x] T019 [US2] Implement the keyword-based hard-atomic detectors (rename, version-pin, mutual-exclusion/auth/payment) in `atomicity-route.sh` with FR-007a HYGIENE: match a described ACTION/INTENT (e.g. a rename arrow / "rename … to …", "bump … to vN", "introduce/add … lock/mutex/auth"), NOT the bare class noun; use word-boundary / `\b` / `[^a-z0-9]` guards on short stems (`lock`, `acl`, `cas`, `otp`, `kms`, `mfa`, `mutex`) so `lock` never fires on "block"; read these keyword classes from `tasks.md` + `plan.md` ONLY (NOT `spec.md`) (FR-007, FR-007a, FR-014; D4, D5).
- [x] T020 [US2] Implement the path-signalled hard-atomic detectors (destructive-migration, out-of-tree-contract-break) in `atomicity-route.sh` using the duplicated `surface_for_path`/`is_excluded_generated` (T007) over all three artifacts: a `schema/migration` path + destructive SQL verb → `hard-atomic:destructive-migration`; an `/api/vN` / public-contract path or keyword → `hard-atomic:out-of-tree-contract-break` (FR-007, FR-014; D5, D6).
- [x] T021 [US2] Wire the hard-atomic OVERRIDE precedence in `atomicity-route.sh`: any hard-atomic signature sets `route: "single-atomic-PR"` and pushes its `hard-atomic:*` token, OVERRIDING any `change-shape:additive-multi-seam`/`split-PR` signal from US1 — and this runs AFTER the input-shape short-circuit but BEFORE the US1 split decision in precedence (FR-007, SC-003; D3). REVIEWABILITY CHECKPOINT: if the script has exceeded ~400 reviewable LOC at this point, stop and split per the template rule rather than adding more logic.
- [x] T022 [US2] Implement the releasability pass in `atomicity-route.sh`, computed INDEPENDENTLY of the route: a destructive-migration class (path-signalled — `schema/migration` path + destructive SQL verb, all three artifacts) → `releasable: false`, push `releasability:destructive-migration` to `signals[]` and the destructive-migration CI-green sentence to `warnings[]`; a concurrency signature — matching a described ACTION/INTENT involving concurrent state (`deadlock`/`mutex`/`semaphore`/`data-race`/`isolation`/`CAS`, with stem guards AND action-shaped phrasing per FR-007a(a), NOT a bare topic-noun occurrence, read from `tasks.md`+`plan.md` only) → `releasable: false`, push `releasability:concurrency` and the concurrency CI-green sentence; otherwise `releasable: true` and no warning (FR-007a, FR-008, FR-009, FR-011b, FR-014, SC-004; D4, D5). The two warning strings MUST be the exact canonical sentences from data-model.md Entity 3.

**Checkpoint**: US1 AND US2 both work independently — hard-atomic override forces `single-atomic-PR` over seams, and releasability is flagged orthogonally to the route; T018 passes.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: The error-path / read-only / dogfood self-check assertions, the workflow-template section, the SKILL + references documentation, the mandated Codex mirror, and full verification.

- [x] T023 In `test-atomicity-route.sh`, add the cross-cutting assertions: the error path (missing/unreadable dir) exits 2 with a top-level `{"error": ...}` and NO `.route` (FR-012, SC-006; quickstart 11); and read-only — after any successful run a fixture dir is unchanged, the script wrote no files (FR-011, SC-006; quickstart 10).
- [x] T024 In `test-atomicity-route.sh`, add the DOGFOOD self-check (load-bearing, FR-007a) — run the finished `atomicity-route.sh` against PRSG-007's OWN feature dir `specs/prsg-007-atomicity-router/` and assert ALL of: (1) `.route != "single-atomic-PR"` (its artifacts enumerate auth/payment/lock/mutex/rename only as VOCABULARY; the keyword detectors must not spuriously self-classify as hard-atomic); (2) the route is a non-split route (must not spuriously `split-PR` off its own vocabulary); (3) `.releasable == true` (its artifacts enumerate concurrency keywords only as vocabulary — the concurrency releasability probe must not fire on a tool that *implements* a concurrency detector without performing concurrent-state operations); and (4) neither `releasability:concurrency` nor `releasability:destructive-migration` ∈ `.signals` (no spurious releasability tokens) (FR-007a, FR-008; D4, D10; quickstart "Dogfood self-check").
- [x] T025 Add the `## Atomicity Route` section to `speckit-pro/skills/speckit-coach/templates/workflow-template.md` as a placeholder surfacing `route`, `releasable`, `signals`, and `warnings` (the record the SKILL fills after Tasks/G5); strip any literal `[[wikilink]]` from added frontmatter/comment blocks so whole-file Layer-1 lint passes (FR-013, data-model Entity 5; D9).
- [x] T026 Document the post-Tasks router step in `speckit-pro/skills/speckit-autopilot/SKILL.md` + `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`: after the Tasks phase / gate G5, the SKILL runs `atomicity-route.sh <feature-dir>` and records the emitted JSON into the workflow file's `## Atomicity Route` section — the SKILL records it, the script does not (FR-011, FR-013; D9). FLAG: this wires NO PR emission/branch creation (that is PRSG-008/009).
- [x] T027 MIRROR the T026 prose into `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` so the Claude and Codex SKILL prose stay in parity (the classifier script is shared — single `scripts/` dir — only the prose is mirrored); confirm `tests/speckit-pro/layer1-structural/validate-codex-skills.sh` stays green (FR-013; D9; constraint "explicit Codex-mirror tasks for every SKILL.md prose change").
- [x] T028 Validate every emitted object (success and error branches, across all fixtures + the dogfood run) against `specs/prsg-007-atomicity-router/contracts/routing-decision.schema.json` — confirm `branch-by-abstraction` is NEVER emitted by any fixture (FR-001, FR-011a, SC-001, SC-008; quickstart "Contract validation").
- [x] T029 Generate/update the PR review packet (what changed, why, non-goals, review order, scope budget, traceability mapping each FR/SC to changed files + Layer-4 fixtures + Layer-1 validation, verification evidence, known gaps naming PRSG-008/PRSG-009 and the deferred deep probes, rollback/flag notes) per spec §"PR Review Packet Requirements".
- [x] T030 Run full verification from the repo root: `bash tests/speckit-pro/run-all.sh --layer 4` (the classifier unit test: one fixture per change class + dogfood + error path) and `bash tests/speckit-pro/run-all.sh --layer 1` (structural validation of the new script, edited workflow template, and edited/mirrored SKILL files incl. `validate-codex-skills.sh`); both MUST pass with zero failures (SC-007; quickstart "Full verification").

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS both user stories. T004-T007 build the spine every detector writes into; T008 gates implementation on the budget check.
- **User Story 1 (Phase 3)**: Depends on Foundational. Delivers the MVP (seam-driven route).
- **User Story 2 (Phase 4)**: Depends on Foundational. Independently testable; its OVERRIDE (T021) sits above US1's split decision in runtime precedence but the US1 code (T013) must exist for the override to override something — so US2 implementation follows US1 in order.
- **Polish (Phase 5)**: Depends on US1 + US2 implementation complete.

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational — no dependency on US2. Fully testable alone.
- **US2 (P1)**: Can start after Foundational — its override is observable on the `hard-atomic-*` fixtures independently; the override semantics (beating split) require US1's split path to be present.

### Within Each User Story

- TDD: fixture content (T009 / T017) and the failing assertions (T010 / T018) come BEFORE the detector logic they cover.
- Foundational spine (T004-T007) before any detector.
- Detectors (T011, T012, T019, T020) before the routing/override wiring (T013, T021).
- Routing wiring before abstain (T014) and releasability (T022).

### Parallel Opportunities

- **Setup**: T002 and T003 are [P] (different paths) — run together after T001.
- **US1 fixtures**: T009 is [P] (fixture files, independent of the test harness logic).
- **US2 fixtures**: T017 is [P] (fixture files).
- The two user stories' FIXTURE authoring (T009, T017) can proceed in parallel; the detector implementations (T011-T016, T019-T022) all share `atomicity-route.sh` and are therefore sequential within the file, NOT [P].

---

## Parallel Example: User Story 1

```bash
# After Foundational completes, author both stories' fixtures in parallel (different files):
Task: "T009 [US1] Author additive-multi-seam/ + single-additive-seam/ + modify-heavy/ + out-of-scope-empty/ fixtures"
Task: "T017 [US2] Author the hard-atomic-* + concurrency/ fixtures"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1: Setup (script stub + fixture tree + test stub).
2. Phase 2: Foundational (CLI + JSON emitter + exit codes + out-of-scope short-circuit + duplicated matchers + budget check).
3. Phase 3: User Story 1 — seam-driven route + abstain + advisory hints.
4. **STOP and VALIDATE**: the US1 assertions (T010) pass; `additive-multi-seam → split-PR`, `modify-heavy → one-navigable-PR`, `out-of-scope-empty → out-of-scope`.

### Incremental Delivery

1. Setup + Foundational → spine ready (runs on empty/missing dirs correctly).
2. US1 → seam-driven route (MVP).
3. US2 → hard-atomic override + releasability flag.
4. Polish → dogfood self-check, error/read-only assertions, template section, SKILL + Codex docs, schema validation, full L1+L4 verification.

---

## Notes

- [P] = different files, no dependencies. Detector tasks that all edit `atomicity-route.sh` are intentionally NOT [P].
- Every task names an exact file path; the only production file is `atomicity-route.sh`.
- TDD: the Layer-4 assertions (T010, T018, T023, T024) are authored to FAIL before the logic that satisfies them.
- The dogfood self-check (T024) is the single most failure-prone property — verify it empirically, do not assume it (D4 implement-phase coupling).
- Commit after each task or logical group.
- Do NOT expand the task list past the reviewability budget — split the spec instead (template rule).
