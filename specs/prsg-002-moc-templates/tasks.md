---
description: "Task list for MOC templates + scaffold-time skeleton + version-gated lints (PRSG-002)"
---

# Tasks: MOC templates + scaffold-time skeleton + version-gated lints

**Input**: Design documents from `specs/prsg-002-moc-templates/`

**Prerequisites**: plan.md (required), spec.md (FR-001..FR-024, US1/US2), research.md, data-model.md, contracts/ (frontmatter-join-key, id-normalization-grammar, lint-behavior)

**Tests**: TDD is explicitly requested. Layer-1 fixtures are written RED before the lint logic; the Layer-4 normalizer unit test is written RED before the helper. All verification is `bash tests/run-all.sh` run from `speckit-pro/` (Layers 1, 4, 5). There is NO build/typecheck/lint step in this repo.

**Reviewability**: Plan declares WITHIN budget (~350 reviewable LOC, single primary surface = the speckit-pro plugin shell, ≤15 total files). These tasks preserve that budget. No split required; no reviewability checkpoint task added.

**Context**: This is the speckit-pro plugin's OWN repo dogfooding SpecKit — a docs/process + plugin-shell change, NOT product code. All paths are repo-relative from the worktree root `.worktrees/prsg-002-moc-templates/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 or US2 (Setup / Foundational / Polish carry no story label)
- Every task names an exact file path.

## Architecture note (load-bearing — read before implementing)

Two house patterns split the verification, each used for what it can actually test:

- **Content rules (Layer 1, in-script predicate fixtures)** — mirror `tests/layer1-structural/validate-process-gitattributes.sh`: each rule is a **side-effect-free predicate function**, exercised against positive/negative `mktemp` or committed `fixtures/moc/` cases via `assert_exit_code` from `tests/lib/assertions.sh`. A negative fixture is a PASS of the assertion (not a polluted `FAIL_COUNT`), so the lint stays GREEN inside the Layer-1 list while scanning the real trees.
- **3-way exit-code contract (Layer 4, subprocess driver)** — mirror `tests/layer4-scripts/test-validate-gate.sh`: `output=$("$LINT" "$root" 2>/dev/null) || rc=$?; assert_eq "2" "$rc"`. Trap→`2`, stderr routing, missing/empty-root→`0`, zero-gated→`0`, and the unreadable-marker skip are only observable **across a process boundary** (a script cannot assert its own trap-driven exit from inside itself), so they live in a dedicated Layer-4 driver, NOT in a self-test block.
- **Scan-root override** — each lint takes an optional **positional scan-root arg defaulting to the two real trees** (`docs/ai/specs/`, `specs/`). The Layer-4 driver is the second caller that points a lint at a controlled fixture root. Justified by FR-015 ("the same lint scripts MUST be runnable in any consuming project's checks") — not a speculative add.

**Net file delta vs the plan's surface list: +1 Layer-4 driver** (`tests/layer4-scripts/test-moc-lint-exit-codes.sh`). FR-020/FR-022/FR-024 (and the FR-021 unreadable-marker case) have no other deterministic home; the plan named only `test-moc-id-normalize.sh` in Layer 4. Still within the ≤15-file reviewability budget.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the empty test surfaces so later RED tasks have a home. No logic yet.

- [X] T001 [P] Create the fixtures directory `speckit-pro/tests/layer1-structural/fixtures/moc/` (with positive and negative subtrees as needed by later fixture tasks) per plan.md Project Structure.
- [X] T002 [P] Confirm `speckit-pro/tests/lib/assertions.sh` provides `section`, `set_test`, `_pass`, `_fail`, `assert_exit_code`, `assert_eq`, `assert_contains`, `assert_file_exists`, `test_summary` (used by all new tests); note any missing helper in the task output rather than adding one speculatively.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared namespace-aware ID normalizer is the single piece of dangerous-edge logic both lints depend on (FR-017/FR-018/FR-019). It is built TDD: Layer-4 unit test RED first, then the helper GREEN. US2's `spec_id` check cannot be implemented until this exists.

**CRITICAL**: No US2 lint work that calls the normalizer can begin until T004 is GREEN.

- [X] T003 [US2] Write the Layer-4 unit test `speckit-pro/tests/layer4-scripts/test-moc-id-normalize.sh` (RED — helper does not exist yet) that `source`s `tests/lib/assertions.sh` and `tests/lib/moc-id-normalize.sh` and asserts the canonical grammar table from `contracts/id-normalization-grammar.md`: `prsg-002-moc-templates`→`(prsg,002)`; `PRSG-002`→`(prsg,002)` and **matches** `prsg-002-moc-templates`; `002-pr-checks-workflow`→`(spec,002)`; `SPEC-002`→`(spec,002)`; `PRSG-002` does **NOT** match `SPEC-002` and does **NOT** match `002-pr-checks-workflow`; `006a-uat-skeleton`→`(spec,006a)`; `013a`→`(spec,013a)` and `013a1`→`(spec,013a1)` do **NOT** match each other; degenerate totality inputs (empty, lone `-`, all-alpha `prsg`, trailing-dash `prsg-`, leading-dash) each yield an empty number-suffix that never matches a well-formed directory. Make the script `chmod +x` and `bash -n` clean. Covers FR-017, FR-018.
- [X] T004 [US2] Implement the shared normalizer `speckit-pro/tests/lib/moc-id-normalize.sh` (GREEN for T003): `#!/usr/bin/env bash` + `set -euo pipefail`, quoted vars, `chmod +x`. Provide a sourceable function that reduces a value to `(namespace, number-suffix)` — lowercase, split on `-`, all-alpha first segment ⇒ that is the namespace and the next segment is the number-suffix, else namespace `spec` and the first segment is the number-suffix; compare the number-suffix as an **opaque whole segment** (byte-equality, NO `[0-9]+[a-z]*` sub-parse so `013a1` is never truncated to `013a`); grammar is **total** (any input yields a defined pair; missing/empty selected segment ⇒ empty number-suffix). Provide a match helper requiring BOTH namespace equality AND exact-segment number-suffix equality. Covers FR-017, FR-018.

**Checkpoint**: Normalizer GREEN under `bash tests/run-all.sh --layer 4`. US2 lints can now consume it.

---

## Phase 3: User Story 1 — Templates + scaffold-time skeleton (Priority: P1) 🎯 MVP

**Goal**: Reusable roadmap-MOC and spec-MOC template shapes carrying the six-field frontmatter contract; `speckit-scaffold-spec` (Claude + Codex) writes a minimal `SPEC-MOC.md` into `specs/<branch-name>/` on every new spec; and PRSG-002's own marker is written so the dogfooded lints have something to pass.

**Independent Test**: Both template shapes exist and carry `up`, `related`, `status`, `rank`, `spec_id`, `structureVersion`. `specs/prsg-002-moc-templates/SPEC-MOC.md` exists with a non-empty relative `up:` resolving to the existing `*-technical-roadmap.md`, `structureVersion: 1`, and `spec_id: PRSG-002`. Delivers a connected map for the new spec regardless of whether US2 lints exist.

### Implementation for User Story 1

- [X] T005 [P] [US1] Create the spec-MOC template `speckit-pro/skills/speckit-coach/templates/spec-moc-template.md` carrying all six contract fields (`up`, `related`, `status`, `rank`, `spec_id`, `structureVersion`) per `contracts/frontmatter-join-key-contract.md`, consumable by the scaffold via the SAME token-substitution mechanism it already uses for `workflow-template.md` (no new preset, no project-local copy). Stamp `structureVersion: 1` with a "keep in sync with the lint scripts' hardcoded literal" comment. Covers FR-001, FR-002, FR-003, FR-016.
- [X] T006 [P] [US1] Create the roadmap-MOC template `speckit-pro/skills/speckit-coach/templates/roadmap-moc-template.md` carrying all six contract fields (roadmap-level shape; its instance filename is defined later by PRSG-004, out of scope here). Single shared runtime-agnostic copy (not duplicated per runtime). Covers FR-001, FR-003.
- [X] T007 [US1] Edit the Claude scaffold skill `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` to add a step that writes a minimal `SPEC-MOC.md` into the CONTRACT dir `specs/<branch-name>/` (branch-named, NOT auto-numbered; creating the dir if absent) on EVERY new spec regardless of slice count, by token-substituting `spec-moc-template.md`. The written marker carries a non-empty relative `[]()` `up:` pointing at the existing `*-technical-roadmap.md` (from `specs/<branch-name>/` this resolves as `../../docs/ai/specs/<roadmap-filename>.md`), `structureVersion: 1` (with a "keep in sync" comment), and a `spec_id` namespace-matching the directory. NOT redirected to `.process/`, NOT written to `docs/ai/specs/`. Covers FR-004, FR-005, FR-006, FR-007, FR-016.
- [X] T008 [US1] Mirror the same skeleton-writing step into the Codex scaffold skill `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md` (runtime parity; templates and lint scripts stay single shared copies, NOT duplicated). Keep paired with T007 (same commit). Note: `tests/layer1-structural/validate-codex-parity.sh` enforces that the Codex `SKILL.md` exists (file-level mirror), not content equivalence of the skeleton step — the behavioral mirror is guaranteed by keeping T007/T008 paired in one commit. Covers FR-008.
- [X] T009 [US1] Write PRSG-002's own marker `specs/prsg-002-moc-templates/SPEC-MOC.md` with `up: "[roadmap](../../docs/ai/specs/pr-size-governance-technical-roadmap.md)"`, `spec_id: PRSG-002`, `structureVersion: 1` (the deterministic "test" of the FR-004..008 prompt edits and what keeps the dogfooded lints GREEN on this spec). This is the marker the US2 lints will gate on for this repo. Covers FR-004, FR-005, FR-007.
- [X] T010 [US1] Verify the marker's `up:` resolves: from `specs/prsg-002-moc-templates/`, confirm `../../docs/ai/specs/pr-size-governance-technical-roadmap.md` exists as a regular file (so the dogfooded stale-index will not red on PRSG-002 itself). If it does not resolve, fix the relative path in T009 before proceeding. Guards SC-002/SC-005 for PRSG-002's own marker.

**Checkpoint**: Both templates carry the six fields; PRSG-002's marker exists and its `up:` resolves. US1 is independently demonstrable (a connected map for the new spec) even with no lints present.

---

## Phase 4: User Story 2 — Version-gated lints + namespace-aware ID normalization (Priority: P2)

**Goal**: Two version-gated Layer-1 lints — orphan (a MOC lacking a valid `up:`) and stale-index (a MOC relative link that does not resolve, plus any wikilink) — plus the `spec_id` join check, firing ONLY for specs carrying `structureVersion >= 1`, with a 3-way exit-code contract, scanning this repo's real trees while grandfathering legacy specs.

**Independent Test**: Run the lints against fixtures. A version-marked MOC missing `up:` fails (orphan); one with a non-resolving relative link fails (stale-index); one with a `[[wikilink]]` fails; one with a relative link to a directory or broken symlink fails; a no-marker / malformed-version directory is silently skipped; an absent/empty `spec_id` in a gated marker fails; `PRSG-002`↔`prsg-002-moc-templates` matches while `PRSG-002`↔`SPEC-002` and `013a`↔`013a1` do not; a missing/empty scan root and a zero-gated scan both exit `0`; an internal failure exits `2` to stderr. The full Layer-1 run is GREEN on the real trees (all legacy specs lack the marker → skipped).

> **TDD**: All `fixtures/moc/` cases (T011–T014) are written RED before their lint logic, and the Layer-4 exit-code driver (T020) is written RED before any exit-code behavior is finalized. Build the lints (T015–T019) to turn them GREEN.

### Fixtures for User Story 2 (RED — write before the lint logic) ⚠️

- [X] T011 [P] [US2] Add orphan-lint fixtures under `speckit-pro/tests/layer1-structural/fixtures/moc/`: a version-gated `SPEC-MOC.md` with a valid relative `up:` (PASS), one with missing/empty `up:` (VIOLATION), one whose `up:` is a `[[wikilink]]` form (VIOLATION — ill-formed for orphan), and a non-MOC doc (`spec.md`/`plan.md`/`tasks.md` or a file under `contracts/`) inside a gated spec carrying no `up:` (must NOT be required to). Covers FR-009, FR-010 (+ AC US2-1, US2-5).
- [X] T012 [P] [US2] Add stale-index fixtures under `fixtures/moc/`: a gated MOC whose every relative `[]()` target (incl. `up:` and a body link) resolves (PASS); one with a relative link whose target is absent (VIOLATION); one with a `[[wikilink]]` (VIOLATION in its own right); one with a relative link targeting a **directory** (VIOLATION — not a regular file); one with a relative link to a **broken symlink** (VIOLATION — distinct from absent). Covers FR-011, FR-012 (+ AC US2-2, US2-3).
- [X] T013 [P] [US2] Add version-gate / parsing fixtures under `fixtures/moc/`: a directory with NO `SPEC-MOC.md` (SKIP); a marker with no `structureVersion` (SKIP); `structureVersion: 0` / `< 1` (SKIP); a non-bare-integer `structureVersion` — quoted `"1"`, decimal `1.0`, and non-numeric text (each SKIP, treated as absence); and a marker with NO `---` frontmatter fence / unparseable frontmatter (SKIP, no readable version). Covers FR-013, FR-021 (no-fence/unparseable/malformed) (+ AC US2-4).
- [X] T014 [P] [US2] Add `spec_id`-join fixtures under `fixtures/moc/`: a gated marker whose `spec_id` namespace-matches its directory (PASS, incl. a `(prsg,002)` and a `(spec,006a)` case); one whose `spec_id` mismatches the directory (VIOLATION, incl. a `(prsg,002)`-vs-`(spec,002)` collision case and a `013a`-vs-`013a1` near-miss); and one with an ABSENT or EMPTY `spec_id` in a gated marker (VIOLATION). Covers FR-019 (+ AC US2-6, US2-7).

### Implementation for User Story 2 (GREEN)

- [X] T015 [US2] Implement the orphan lint `speckit-pro/tests/layer1-structural/validate-moc-orphan.sh` (GREEN for T011): `#!/usr/bin/env bash` + `set -euo pipefail`, quoted vars, `chmod +x`, `bash -n` clean; `source tests/lib/assertions.sh` and `tests/lib/moc-id-normalize.sh`. Resolve repo root via `REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"`. Accept an optional **positional scan-root arg** defaulting to the two real trees. Factor the `up:`-validity rule into a **side-effect-free predicate** (present + non-empty + well-formed relative `[]()` link; a `[[wikilink]]` is "not well-formed" here too) and exercise the T011 fixtures via `assert_exit_code`. Scope the `up:` requirement to MOC files ONLY (filename exactly `SPEC-MOC.md`); do NOT require `up:` on non-MOC docs; `.process/**` exempt. Do NOT resolve the `up:` target (that is stale-index's job). Hardcode the gate literal `1` with a "keep in sync" comment. Covers FR-009, FR-010, FR-016.
- [X] T016 [US2] Implement the stale-index lint `speckit-pro/tests/layer1-structural/validate-moc-stale-index.sh` (GREEN for T012): same safety header, repo-root idiom, scan-root arg, and `assertions.sh`/normalizer sourcing as T015. Factor the resolution rule into a **side-effect-free predicate**: collect every relative `[]()` target in a gated MOC — INCLUDING the frontmatter `up:` value plus any body links — and assert each resolves to an existing **regular readable file** (a directory or broken symlink at the path = NOT resolving = VIOLATION, distinct from absent — FR-011), resolved relative to the MOC's own directory; and assert NO `[[wikilink]]` appears anywhere (any wikilink = VIOLATION — FR-012). Exercise the T012 fixtures via `assert_exit_code`. Covers FR-011, FR-012.
- [X] T017 [US2] Implement the shared version-gating predicate used by BOTH lints (in whichever lint/helper the implementer chooses, kept consistent across both): a **total, safe** marker read that yields gated ONLY on an unambiguous bare integer `structureVersion >= 1`; no `SPEC-MOC.md` / no `structureVersion` / `< 1` / non-bare-integer (`"1"`, `1.0`, text) / no `---` fence / unparseable frontmatter all ⇒ NOT gated (SKIP); never crashes the lint. Exercise the T013 fixtures via `assert_exit_code`. The exempt/skip decision MUST be evaluated BEFORE any read of the spec's body content (exempt-before-content invariant). Covers FR-013, FR-021 (no-fence/unparseable/malformed), FR-023.
- [X] T018 [US2] Implement the `spec_id` join check inside the orphan lint (or a shared step run by the gated path) using the T004 normalizer (GREEN for T014): for each version-gated `SPEC-MOC.md`, an ABSENT or EMPTY `spec_id` is a VIOLATION; otherwise `normalize(spec_id)` MUST equal `normalize(containing-directory-name)` (both sides reduced with the SAME grammar — symmetric), else VIOLATION. Exercise the T014 fixtures via `assert_exit_code`. Covers FR-019.
- [X] T019 [US2] Implement the hard-fail-on-violation behavior in both lints: each lint exits nonzero (`1`) when it finds a content violation in a version-gated spec and exits `0` when there are no violations among the specs it is allowed to check (including a scan that finds zero version-gated specs). Output (stdout) on a violation MUST name the offending spec/file path AND which rule failed (orphan: missing/ill-formed `up:`; stale-index: the specific unresolved link or the wikilink; `spec_id`: mismatch or absent join key). Covers FR-014, FR-024 (stdout content-violation half).

### Layer-4 exit-code contract driver (RED — write before finalizing exit behavior) ⚠️

- [X] T020 [US2] Write the Layer-4 subprocess driver `speckit-pro/tests/layer4-scripts/test-moc-lint-exit-codes.sh` (NEW file beyond the plan's surface list; mirrors `test-validate-gate.sh`). `source tests/lib/assertions.sh`; invoke each lint as a subprocess with `output=$("$LINT" "$root" 2>err) || rc=$?` and assert the 3-way enum: (a) **FR-020** trap→`2` — prepend a temp dir to `PATH` containing a `jq`/`find` stub that exits nonzero, run a lint, assert `rc == 2` AND `2 != 1`; (b) **FR-021 unreadable** — `chmod 000` a committed/temp `SPEC-MOC.md` at runtime (restore via `trap ... EXIT`), assert the lint SKIPS it (no content violation) and emits a stderr warning, guarding the root-bypasses-read-bits flake; (c) **FR-022** — a nonexistent scan root AND an empty/markerless tree each exit `0`; (d) **FR-023** — a fixture with deliberately broken body content but NO marker exits `0` (skipped before content read); (e) **FR-024** — assert a content violation routes path+rule to **stdout** with exit `1`, while an internal error routes to **stderr** with exit `2` (the two classes never conflated). Make it `chmod +x` and `bash -n` clean. Covers FR-020, FR-021 (unreadable), FR-022, FR-023, FR-024 (exit-2/stderr half).

### Wire-up (LAST in US2, so the suite is not red for wiring reasons while building)

- [X] T021 [US2] Wire both lints into `speckit-pro/tests/run-all.sh` by appending `validate-moc-orphan.sh` and `validate-moc-stale-index.sh` to the Layer-1 **runtime-agnostic** validator list (the block ending at `validate-process-gitattributes.sh`, lines ~137-144). The new Layer-4 tests (`test-moc-id-normalize.sh`, `test-moc-lint-exit-codes.sh`) run via the existing Layer-4 discovery; confirm both are picked up. Covers FR-015 (deterministic structural layer + scans real trees).

**Checkpoint**: Both lints GREEN against fixtures AND the real trees; the exit-code driver and normalizer unit test pass; all legacy specs skipped; PRSG-002's marker passes.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Full-suite verification, script-safety confirmation, and the PR review packet.

- [X] T022 [P] Run `bash tests/run-all.sh` from `speckit-pro/` and confirm Layers 1, 4, 5 are GREEN with zero failures — specifically that the dogfooded lints stay green on the real spec trees (legacy specs exempt, PRSG-002's marker resolves) per quickstart.md. Covers SC-001, SC-002, SC-003, SC-005 end-to-end; SC-004 (ID-join: `PRSG-002`≠`SPEC-002`, `013a`≠`013a1`) is verified at the unit/fixture level by T003/T004 (normalizer) and T014/T018 (`spec_id` join) rather than the full-suite scan.
- [X] T023 [P] Confirm Script Safety (constitution II) on every new bash file (`tests/lib/moc-id-normalize.sh`, `validate-moc-orphan.sh`, `validate-moc-stale-index.sh`, `test-moc-id-normalize.sh`, `test-moc-lint-exit-codes.sh`): `#!/usr/bin/env bash` + `set -euo pipefail`, quoted vars, `chmod +x`, `bash -n` clean — and that `validate-scripts.sh` (already in the Layer-1 run) passes on them.
- [X] T024 Generate/update the PR review packet (review order: contracts → templates → shared normalizer → lints → fixtures → scaffold edits CC then Codex → run-all.sh wiring → Layer-4 tests) with scope budget (~350 reviewable LOC / single surface), FR-001..FR-024 traceability, verification evidence (`bash tests/run-all.sh` green), non-goals (PRSG-003 generated content, PRSG-004 home note, PRSG-011 backfill/relocation, `up:` on non-MOC docs, wikilink support), and rollback (revert the PR; version-gating means removing the lints/marker has no effect on legacy specs). Per plan.md "PR review packet source".

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup. The normalizer (T004) BLOCKS the US2 `spec_id` check (T018) and the normalizer unit test (T003 is its RED gate).
- **US1 (Phase 3)**: Depends on Setup only — independent of US2 and of the normalizer. Can run in parallel with Phase 2.
- **US2 (Phase 4)**: Depends on Foundational (normalizer) AND on US1's PRSG-002 marker (T009/T010) for the dogfooded real-tree scan to be exercised green. The fixtures (T011–T014, T020) are RED gates for the lint logic (T015–T019); wiring (T021) is LAST.
- **Polish (Phase 5)**: Depends on US1 + US2 complete.

### User Story Dependencies

- **US1 (P1)**: Independently testable — templates + a written marker deliver a connected map with no lints present.
- **US2 (P2)**: Independently testable against fixtures; for the real-tree dogfood scan to be meaningful it relies on US1 having written PRSG-002's marker.

### Within Each User Story

- Fixtures / unit tests (RED) MUST be written and FAIL before the implementation that turns them GREEN.
- Normalizer before the `spec_id` check (T004 → T018).
- Both lints implemented before wiring them into `run-all.sh` (T015/T016 → T021).
- Keep Codex-mirror edits (T008) paired with their Claude edits (T007).

---

## Parallel Opportunities

- **Setup**: T001, T002 are independent files/checks → parallel.
- **US1**: T005 and T006 are two distinct template files → parallel. T007 (Claude) and T008 (Codex) touch different files but are a paired mirror — do them together but NOT independently of each other (T008 must reflect T007).
- **US2 fixtures**: T011, T012, T013, T014 add distinct fixture sets under `fixtures/moc/` → parallel (RED, before any lint logic).
- The normalizer unit test (T003) can be written in parallel with US1 template tasks (different files).
- **Polish**: T022 and T023 are independent verification passes → parallel.

### [P] parallel-safe tasks

T001, T002, T003, T005, T006, T011, T012, T013, T014, T022, T023.

### Codex-mirror pairing

T008 (`codex-skills/speckit-scaffold-spec/SKILL.md`) is paired with T007 (`skills/speckit-scaffold-spec/SKILL.md`) — same skeleton-writing behavior, different runtime file; `validate-codex-parity.sh` independently guards the mirror. Neither is marked [P]; they are a coupled pair.

---

## Parallel Example: US2 fixtures (RED, before lint logic)

```bash
# Launch the four fixture sets together (different fixture subtrees, no logic yet):
Task: "Add orphan-lint fixtures under tests/layer1-structural/fixtures/moc/ (T011)"
Task: "Add stale-index fixtures under tests/layer1-structural/fixtures/moc/ (T012)"
Task: "Add version-gate/parsing fixtures under tests/layer1-structural/fixtures/moc/ (T013)"
Task: "Add spec_id-join fixtures under tests/layer1-structural/fixtures/moc/ (T014)"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup → Phase 3 US1 (templates + scaffold edits + PRSG-002 marker).
2. **STOP and VALIDATE**: both templates carry the six fields; `specs/prsg-002-moc-templates/SPEC-MOC.md` exists and its `up:` resolves. This is a shippable increment: every new spec is born parent-linked even with no lints.

### Incremental Delivery

1. Setup + Foundational (normalizer) → normalizer GREEN.
2. US1 → connected map for new specs (MVP).
3. US2 → enforcement turned on (fixtures GREEN, exit-code driver GREEN, real trees green, legacy grandfathered).
4. Polish → full-suite green + PR packet.

---

## FR → Task Coverage Map

| FR | Task(s) | FR | Task(s) |
|----|---------|----|---------|
| FR-001 | T005, T006 | FR-013 | T013, T017 |
| FR-002 | T005 | FR-014 | T019 |
| FR-003 | T005, T006 | FR-015 | T021 |
| FR-004 | T007, T009 | FR-016 | T005, T007, T015 |
| FR-005 | T007, T009 | FR-017 | T003, T004 |
| FR-006 | T007 | FR-018 | T003, T004 |
| FR-007 | T007, T009, T010 | FR-019 | T014, T018 |
| FR-008 | T008 | FR-020 | T020 |
| FR-009 | T011, T015 | FR-021 | T013, T017 (no-fence/unparseable/malformed) + T020 (unreadable) |
| FR-010 | T011, T015 | FR-022 | T020 |
| FR-011 | T012, T016 | FR-023 | T017, T020 |
| FR-012 | T012, T016 | FR-024 | T019 (stdout) + T020 (stderr/exit-2) |

All FR-001..FR-024 map to at least one task and at least one fixture/test.

---

## Notes

- [P] = different files, no dependencies on incomplete tasks.
- [Story] label maps each task to US1 or US2; Setup/Foundational/Polish carry no story label.
- RED-before-GREEN is enforced: T003 before T004; T011–T014 + T020 before T015–T019; the suite wiring (T021) is LAST so the Layer-1 run is not red for wiring reasons mid-build.
- Verify fixtures/tests FAIL before implementing the logic that satisfies them.
- Commit after each task or logical group; keep T007/T008 (Codex mirror) in one commit.
- Bound by non-goals: no generated MOC content (PRSG-003), no PRD-derived home note (PRSG-004), no retro-migration/backfill (PRSG-011), no `up:` on non-MOC docs, no wikilink support.
