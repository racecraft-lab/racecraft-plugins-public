---
description: "Task list for PRSG-005 — Vertical-slice sizing heuristics in PRD/grill-me"
---

# Tasks: Vertical-slice sizing heuristics in PRD/grill-me (PRSG-005)

**Input**: Design documents from `/specs/prsg-005-slice-sizing-heuristics/`

**Prerequisites**: plan.md (required), spec.md (17 FRs, US1+US2), data-model.md, contracts/estimate-spec-size.md, quickstart.md

**Tests**: TDD is explicitly requested for the estimator. The Layer-4 determinism + boundary
fixture/test (T004) is written and made to FAIL (RED) BEFORE the estimator implementation
(T005, GREEN). No other test tasks are generated (the skill-prose surfaces are exercised by
developer-local Layer 2/3/8 evals enumerated in Phase 5 as follow-ups, not CI gates).

**Reviewability**: Budget is ~200 production reviewable LOC, ~6 production files, ~8 total
files, single primary surface (docs/process) — all within budget (warn thresholds are >400
LOC, >6 production files, >15 total files, or >1 primary surface). A reviewability checkpoint
(T003) is included in the Foundational phase per the preset template. No split required.

**Advisory-only invariant (FR-011)**: NO task adds gate/threshold/exit-code/blocking logic —
that is PRSG-006. The `status` enum stays exactly `ok|warn`. A `warn` is informational; both
skills MUST continue the interview after surfacing it. This constraint is verified explicitly
in T018.

**Organization**: Tasks are grouped by user story to enable independent implementation and
testing of each story. Each Codex-mirror edit is paired with its Claude Code edit in the SAME
phase (FR-014) — mirrors are never deferred to the polish phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- Single-project Claude Code plugin marketplace. All production paths are under the
  `speckit-pro/` plugin. The shared script + reference doc are SINGLE runtime-agnostic copies
  under `speckit-pro/skills/speckit-coach/` (no per-skill copies), invoked/linked by all four
  skill surfaces (2 Claude Code + 2 Codex) via `${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/...`.
- All test commands run from the `speckit-pro/` directory.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the worktree and verification harness are ready before any edits.

- [x] T001 Confirm the baseline fast test suite is green before edits: from `speckit-pro/`, run `bash tests/run-all.sh` (Layers 1 + 4 + 5) and record the pre-change pass state so any later failure is attributable to PRSG-005 changes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared reference doc and the shared deterministic estimator (with its
Layer-4 test) are the single sources of truth that BOTH user stories depend on. They MUST be
complete before US1 or US2 work begins — both skills invoke the same estimator and link the
same doc.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 [P] Create the shared SPIDR + INVEST + vertical-slicing reference doc at `speckit-pro/skills/speckit-coach/references/slicing-heuristics.md` as the single source of truth (FR-010): canonical SPIDR (Spike, Path, Interface, Data, Rules) story-splitting text, INVEST (Independent, Negotiable, Valuable, Estimable, Small, Testable) story-quality text, and vertical-slicing (each slice cuts end-to-end through all layers) guidance. MUST include the FR-015 caveat that the estimate is an approximate *forward* guess made before implementation, NOT the authoritative reviewable-LOC count (PRSG-006 owns that). MUST document the FR-017 spike as a timebox-sized slice type (the INVEST "Estimable" escape hatch) and clarify that `status: ok` for a spike means LOC sizing is not applicable, not that the slice is small. MUST state the at-ceiling boundary rule (at exactly the ~400-LOC ceiling `status` is `ok`; `warn` only strictly over) so both skills stay consistent. References the ~400-LOC ceiling by value in prose. (FR-008, FR-010, FR-015, FR-017; SC-006.)

- [x] T003 Reviewability checkpoint: confirm the planned task/file scope stays within the spec's reviewability budget (~200 production LOC, ~6 production files, ~8 total files, single primary surface) and record the split decision (remains one spec — the four skill edits, shared doc, and shared script are tightly coupled around a single advisory sizing capability and a single shared constant). No ratified exception needed. (Plan Reviewability Budget; spec Split decision.)

### Tests for the estimator (TDD — write FIRST, ensure it FAILS before T005) ⚠️

> **NOTE: T004 MUST be written and confirmed RED (failing, because `estimate-spec-size.sh`
> does not yet exist) BEFORE T005 implements the estimator. This is the gate-defining TDD
> ordering for G5.**

- [x] T004 Write the Layer-4 determinism + boundary unit test at `tests/speckit-pro/layer4-scripts/test-estimate-spec-size.sh` (using `tests/lib/assertions.sh` and the `test-<script-name>.sh` convention) plus its committed input→expected-JSON fixture set under `tests/speckit-pro/layer4-scripts/fixtures/`. The test MUST assert, against `contracts/estimate-spec-size.md`: (a) **byte-identical** stdout for repeated identical inputs (determinism, FR-007); (b) the **at-ceiling boundary** — `estimated_loc == ceiling` → `status: ok`, and strictly over → `status: warn` (FR-006, FR-008); (c) the **spike triple** — `--spike` → `{"estimated_loc":0,"suggested_slices":1,"status":"ok"}` (FR-017); (d) the **bad-input pin** — each missing/zero/negative/malformed numeric signal normalizes to `0` and `status` follows the same at-ceiling rule on the resulting `estimated_loc` (all-bad/absent → `estimated_loc:0` → `status: ok`), non-crashing (FR-016); (e) `status` is **never** any value other than `ok` or `warn`. Run `bash tests/run-all.sh --layer 4` and confirm this test FAILS (RED) because the script does not yet exist. (Verifies SC-003; FR-006, FR-007, FR-008, FR-016, FR-017.)

### Implementation of the estimator (GREEN — only after T004 is RED)

- [x] T005 Implement the shared deterministic estimator at `speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh` (single runtime-agnostic copy; bash + jq only) to make T004 pass (GREEN). Per `contracts/estimate-spec-size.md` and `data-model.md`: accept structured size signals (user stories, files/surfaces touched, functional requirements, new-vs-modify flag) and an OPTIONAL spike flag, and emit compact JSON `{estimated_loc, suggested_slices, status}` via `jq` where `status` is **exactly** `ok` or `warn`. Hardcode the ~400-LOC ceiling as a single constant with a "keep in sync with the documented ceiling in slicing-heuristics.md" comment (FR-008). At-ceiling → `ok`, strictly over → `warn` (FR-006). `suggested_slices = ceil(estimated_loc / ceiling)`, minimum `1` (non-spike). Spike → skip the LOC-threshold comparison and return `{"estimated_loc":0,"suggested_slices":1,"status":"ok"}` (FR-017). Each missing/zero/negative/malformed signal normalizes to `0`; `status` then follows the same at-ceiling rule — never a misleading `warn`, never a third status value, never a crash (FR-016). Deterministic: no clocks, randomness, or environment dependence (FR-007). **Script Safety (Constitution II)**: begin with `#!/usr/bin/env bash`, set `set -euo pipefail` as the first executable line, quote all variables, check command results, `chmod +x` the file, and confirm `bash -n` is clean. The script exits `0` on a successful estimate including `warn` — `warn` is NEVER expressed as a non-zero/blocking exit (FR-011). Run `bash tests/run-all.sh --layer 4` and confirm T004 now PASSES. (FR-006, FR-007, FR-008, FR-011, FR-016, FR-017; Constitution II; SC-003.)

**Checkpoint**: The shared estimator (byte-identical on fixtures, advisory-only) and the
shared reference doc exist. Both user stories can now begin (in parallel if staffed).

---

## Phase 3: User Story 1 - Catalog-level decomposition in speckit-prd (Priority: P1) 🎯 MVP

**Goal**: `speckit-prd` decomposes an idea into a SPEC catalog of thin vertical slices *by
construction* (SPIDR + vertical slicing), populates each catalog entry's existing
`Projected reviewable LOC` field from the shared estimator, and adds a one-line INVEST/vertical-slice
rationale — so the roadmap is born PR-sized.

**Independent Test**: Run a `speckit-prd` interview on a fixture idea that would naively
become one fat spec; confirm the emitted catalog is multiple thin vertical slices, each
carrying a `Projected reviewable LOC` populated from the estimator plus a one-line INVEST/vertical-slice
rationale (SC-001).

### Implementation for User Story 1

- [x] T006 [US1] Edit `speckit-pro/skills/speckit-prd/SKILL.md` (Claude Code) to add catalog-level decomposition: instruct the skill to apply SPIDR story-splitting + vertical slicing so the emitted SPEC catalog is composed of thin, end-to-end (vertical) slices by construction rather than a few fat horizontal specs. Add a SHORT inline SPIDR/INVEST/vertical-slice summary plus a link to the shared `slicing-heuristics.md` (no duplicated guidance prose — FR-010). (FR-001, FR-010; US1 AS1; SC-001.)

- [x] T007 [US1] In `speckit-pro/skills/speckit-prd/SKILL.md` (Claude Code), wire the Projected reviewable LOC field population: for each catalog entry it drafts, the skill derives the estimator's size signals from that entry and invokes the SINGLE shared estimator via `${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/scripts/estimate-spec-size.sh` (FR-009), then populates that entry's EXISTING `Projected reviewable LOC` field with the returned `estimated_loc` and adds a one-line INVEST/vertical-slice rationale. MUST reuse the existing per-SPEC `Projected reviewable LOC` field — NO roadmap-template schema change and no new structured catalog fields (FR-012). When the estimator reports an entry over the ceiling, surface the size signal as ADVISORY text and continue the interview — nothing blocked or rejected (FR-011). (FR-002, FR-009, FR-011, FR-012; US1 AS2, AS3; SC-001.)

- [x] T008 [US1] In `speckit-pro/skills/speckit-prd/SKILL.md` (Claude Code), specify the estimator-unavailable degradation path (US1 AS5): when the estimator cannot produce a usable result for any reason — missing script, missing `jq`, a non-zero exit, or empty/unparseable output — the skill MUST treat the result as an ABSENT estimate, leave that entry's `Projected reviewable LOC` field unpopulated (or noted as unavailable), surface an advisory note, and CONTINUE the interview. The skill MUST NOT read the script's exit code as a gate or convert an unavailable estimate into a hard stop. (FR-011; US1 AS5; SC-004.)

- [x] T009 [P] [US1] Mirror the US1 edits into the Codex counterpart `speckit-pro/codex-skills/speckit-prd/SKILL.md` (FR-014), behavior-equivalent to T006–T008: same catalog decomposition (SPIDR + vertical slicing), same inline summary + link to the single shared `slicing-heuristics.md`, same invocation of the single shared `${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/scripts/estimate-spec-size.sh`, same Projected reviewable LOC field population + INVEST rationale, same advisory-only over-ceiling and unavailable-estimate behavior. `speckit-prd`'s catalog-decomposition prose carries across with no tool dependency (no `AskUserQuestion` involved here). The shared doc + script remain single copies — no Codex-specific second copy. (FR-014; SC-006.)

**Checkpoint**: `speckit-prd` (Claude Code + Codex mirror) emits a thin-vertical-slice catalog
with populated Projected reviewable LOC fields and INVEST rationale, degrading to advisory text when the estimator
is unavailable. US1 is independently testable.

---

## Phase 4: User Story 2 - Per-spec validation and split in grill-me (Priority: P2)

**Goal**: `grill-me` gains a dedicated slice-sizing branch in its design tree that runs the
shared estimator on a single spec's signals and, when over the ceiling or horizontally sliced,
asks a split question recommending N thin vertical slices — recording the chosen split in the
Design Concept doc for scaffold-spec/autopilot to act on later.

**Independent Test**: Run a `grill-me` interview on a fixture single spec that is fat or
horizontally sliced; confirm the slice-sizing branch triggers, the estimator runs on that
spec's signals, a split question recommending N vertical slices is asked, and the chosen split
is recorded in the Design Concept document (SC-002).

### Implementation for User Story 2

- [x] T010 [US2] Edit `speckit-pro/skills/grill-me/SKILL.md` (Claude Code) to add a dedicated slice-sizing branch to its design tree that derives the single spec's size signals and runs the SINGLE shared estimator via `${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/scripts/estimate-spec-size.sh` (FR-009). Add a SHORT inline SPIDR/INVEST/vertical-slice summary plus a link to the shared `slicing-heuristics.md` (no duplicated guidance prose — FR-010). (FR-003, FR-009, FR-010; US2 AS1; SC-002.)

- [x] T011 [US2] In `speckit-pro/skills/grill-me/SKILL.md` (Claude Code), implement the split sub-interview: when the estimator reports the single spec is over the documented ceiling OR the spec is horizontally sliced (cuts by layer rather than end-to-end), ask a split question via `AskUserQuestion` that recommends N thin vertical slices (and recommends re-slicing a horizontal spec into vertical slices). When the estimate is at/under the ceiling, surface the size estimate as an advisory note and do NOT force a split. When the estimate is borderline OR the estimator is unavailable, degrade to an advisory note and continue — the branch NEVER blocks the interview, and the script's exit code is never read as a gate. (FR-004, FR-011; US2 AS1, AS2, AS4, AS5; SC-002, SC-004.)

- [x] T012 [US2] In `speckit-pro/skills/grill-me/SKILL.md` (Claude Code), record the chosen split: when the maintainer chooses a split in the slice-sizing branch, write the chosen split into the Design Concept document (Goals / Open Questions) so `speckit-scaffold-spec` and `speckit-autopilot` can act on it later. (FR-005; US2 AS3; SC-002.)

- [x] T013 [P] [US2] Mirror the US2 edits into the Codex counterpart `speckit-pro/codex-skills/grill-me/SKILL.md` (FR-014), behavior-equivalent to T010–T012: same slice-sizing design-tree branch, same inline summary + link to the single shared `slicing-heuristics.md`, same invocation of the single shared `${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/scripts/estimate-spec-size.sh`, same over-ceiling/horizontal split recommendation, same at/under-ceiling advisory behavior, same borderline/unavailable degradation, and the same chosen-split recording in the Design Concept doc. The one runtime difference: Codex has no `AskUserQuestion`, so the split question is adapted to a **free-text question-and-answer loop** that asks the same question, offers the same recommended N-slice split, and records the same outcome — behavior-equivalent, not tool-identical. Shared doc + script remain single copies. (FR-014; SC-006.)

**Checkpoint**: `grill-me` (Claude Code + Codex mirror) runs the estimator on a single spec,
asks the split question when warranted, records the split in the Design Concept doc, and never
blocks. US1 and US2 are both independently functional.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Trigger-phrase touch, full verification, advisory-only invariant confirmation, the
PR review packet, and enumeration of the developer-local eval surfaces as follow-ups.

- [x] T014 [P] Light trigger touch on the two Claude Code skill descriptions: add a few sizing/slicing trigger phrases to the `description` frontmatter of `speckit-pro/skills/speckit-prd/SKILL.md` (e.g. "right-size the catalog") and `speckit-pro/skills/grill-me/SKILL.md` (e.g. slice-sizing/split phrasing). Keep ALL existing trigger phrases intact — additive only, no rewrites that would cause over-trigger or under-trigger regression. (FR-013; US1 AS4; SC-005.)

- [x] T015 [P] Light trigger touch on the two Codex mirror descriptions: add the equivalent sizing/slicing trigger phrases to the `description` frontmatter of `speckit-pro/codex-skills/speckit-prd/SKILL.md` and `speckit-pro/codex-skills/grill-me/SKILL.md`, keeping all existing phrases intact (additive only). Paired with T014 so CC and Codex descriptions stay in parity. (FR-013, FR-014; SC-005, SC-006.)

- [x] T016 Run the full fast verification suite: from `speckit-pro/`, run `bash tests/run-all.sh` and confirm Layer 1 (structural, including `validate-scripts.sh` for the new estimator and `validate-codex-skills.sh` for both mirrors), Layer 4 (the estimator determinism + boundary test from T004), and Layer 5 (agent tool scoping — no change expected) are all GREEN. (Constitution I, II, IV; SC-003, SC-006; G7 precondition.)

- [x] T017 Confirm the single-source-of-truth + single-copy invariants by inspection: SPIDR + INVEST + vertical-slicing guidance exists in exactly ONE document (`slicing-heuristics.md`); both Claude Code skills and both Codex mirrors carry only a short inline summary + a link (no duplicated guidance prose); the estimator script and reference doc are SINGLE runtime-agnostic copies referenced by all four surfaces via `${CLAUDE_PLUGIN_ROOT}` (no per-skill copies); and the ~400-LOC ceiling appears as one hardcoded constant in the script, referenced by value in the doc. (FR-008, FR-009, FR-010, FR-014; SC-006.)

- [x] T018 Confirm the advisory-only invariant by inspection across all five changed surfaces (the estimator script + the four SKILL.md edits): NO gate, threshold, exit-code-as-control-flow, or blocking/rejecting logic anywhere; `status` enum is exactly `ok|warn` with no third value; the script exits `0` even on `warn`; and both skills (and both mirrors) surface a `warn` or an unavailable estimate as advisory text and continue the interview. Nothing strays into PRSG-006 (gate/threshold), PRSG-007/008/009 (split engine), or roadmap-template-schema territory. (FR-011, FR-012, FR-017; SC-004.)

- [x] T019 Generate or update the PR review packet: PR description with what changed, why, non-goals, review order, scope budget (~200 LOC), traceability (each FR/SC → changed files + verification evidence), verification evidence (`bash tests/run-all.sh` green; estimator byte-identical on fixtures; developer-local L2/L3/L8 recorded), known gaps, and rollback notes (additive + advisory-only — rollback = revert the skill edits and remove the shared script + doc; no data migration, no flag). Name deferred work: PRSG-006 (plan-phase budget gate + authoritative reviewable-LOC count) and PRSG-007/008/009 (split-PR engine). (Spec PR Review Packet Requirements; plan PR review packet source.)

- [x] T020 Run quickstart.md validation: exercise the estimator directly per `quickstart.md` (normal signals → `ok|warn`; `--spike` → `{"estimated_loc":0,"suggested_slices":1,"status":"ok"}`) and confirm the documented invariants hold (advisory-only; single source of truth; forward-estimate caveat present in the shared doc). (Quickstart; SC-001, SC-003, SC-004.)

### Developer-local follow-up evals (NOT CI gates — recorded before merge)

> These require `claude -p` and the `skill-creator` plugin; they are developer-local per the
> plan's Testing section, enumerated here so the G5 gate sees the L2/L3 (and L8) surfaces.

- [ ] T021 [P] Layer 2 (trigger routing) — developer-local follow-up: run the trigger evals for `speckit-prd` and `grill-me` and confirm the newly added sizing/slicing phrases route to the correct skill AND every existing trigger phrase for both skills still routes unchanged (no over-trigger or under-trigger regression). Record the result. (FR-013; SC-005.)

- [ ] T022 [P] Layer 3 (functional) — developer-local follow-up: run a `speckit-prd` interview on a would-be-fat fixture idea and confirm the emitted catalog is multiple thin vertical slices, each with a populated `Projected reviewable LOC` from the estimator + a one-line INVEST/vertical-slice rationale; run a `grill-me` interview on a fat/horizontal single spec and confirm the slice-sizing branch triggers, asks the split question, and records the chosen split in the Design Concept doc. Record the result. (SC-001, SC-002.)

- [ ] T023 [P] Layer 8 (Codex parity) — developer-local follow-up: confirm both `codex-skills/` mirrors behave equivalently to their Claude Code counterparts (the free-text Q&A loop standing in for `AskUserQuestion` in `grill-me`). Record the result. (FR-014; SC-006.)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup. BLOCKS both user stories (both call the shared
  estimator and link the shared doc). Within Phase 2, the TDD ordering is strict: **T004 (RED)
  before T005 (GREEN)**.
- **User Stories (Phase 3, Phase 4)**: Both depend on Foundational completion. Once Foundational
  is done, US1 and US2 can proceed in parallel (different SKILL.md files) or sequentially in
  priority order (P1 → P2).
- **Polish (Phase 5)**: Depends on both user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2). No dependency on US2.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2). No dependency on US1.

### Within Each Phase / User Story

- **Phase 2 (TDD)**: T004 MUST be written and FAIL before T005 implements the estimator.
- **US1**: T006 → T007 → T008 are sequential edits to the same file
  (`speckit-pro/skills/speckit-prd/SKILL.md`). T009 (Codex mirror, different file) is `[P]` and
  can run alongside once T006–T008 land.
- **US2**: T010 → T011 → T012 are sequential edits to the same file
  (`speckit-pro/skills/grill-me/SKILL.md`). T013 (Codex mirror, different file) is `[P]` and can
  run alongside once T010–T012 land.

### Codex-mirror pairing (FR-014)

- US1 CC edits (T006–T008) ↔ US1 Codex mirror (T009) — same phase.
- US2 CC edits (T010–T012) ↔ US2 Codex mirror (T013) — same phase.
- CC trigger touch (T014) ↔ Codex trigger touch (T015) — same phase.

---

## Parallel Opportunities

The `[P]` tasks (different files, no dependency on incomplete work in the same phase):

- **T002** — shared reference doc (independent of the estimator test/impl in Phase 2).
- **T009** — US1 Codex mirror (`codex-skills/speckit-prd/SKILL.md`), parallel to the polish/US2
  work once the US1 CC edits T006–T008 are in place.
- **T013** — US2 Codex mirror (`codex-skills/grill-me/SKILL.md`), parallel once the US2 CC edits
  T010–T012 are in place.
- **T014** — Claude Code trigger touch (two CC SKILL.md `description` fields).
- **T015** — Codex trigger touch (two Codex SKILL.md `description` fields).
- **T021, T022, T023** — the three developer-local follow-up evals (L2, L3, L8) are mutually
  independent.

> NOT parallel-safe (deliberately omitted `[P]`): T004 before T005 (TDD ordering); T006/T007/T008
> (same file); T010/T011/T012 (same file); the verification/inspection tasks T016–T020 (depend on
> all edits landing).

### Parallel Example: User Stories after Foundational

```bash
# Once Phase 2 (T001–T005) completes, US1 and US2 can run in parallel:
# Developer A — US1 (speckit-prd): T006 → T007 → T008, then T009 [P] (Codex mirror)
# Developer B — US2 (grill-me):    T010 → T011 → T012, then T013 [P] (Codex mirror)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001).
2. Complete Phase 2: Foundational (T002–T005) — CRITICAL; the shared estimator (TDD: T004 RED →
   T005 GREEN) and shared doc block both stories.
3. Complete Phase 3: User Story 1 (T006–T009) — `speckit-prd` catalog decomposition + Budget
   population + Codex mirror.
4. **STOP and VALIDATE**: run a `speckit-prd` interview on a fixture fat idea; confirm a
   thin-vertical-slice catalog with populated Projected reviewable LOC fields (SC-001).

### Incremental Delivery

1. Setup + Foundational → shared estimator + doc ready (estimator byte-identical on fixtures).
2. Add User Story 1 → test independently → MVP (the roadmap front door is now PR-sizing).
3. Add User Story 2 → test independently → `grill-me` per-spec safety net live.
4. Polish: trigger phrases (CC + Codex paired), full suite green, advisory-only confirmed, PR
   review packet, developer-local L2/L3/L8 recorded.

---

## Requirement → Task Traceability

Every functional requirement maps to at least one task (G5):

| FR | Requirement (short) | Task(s) |
|----|---------------------|---------|
| FR-001 | speckit-prd SPIDR + vertical-slice catalog decomposition | T006, T009 |
| FR-002 | Populate Projected reviewable LOC field + INVEST rationale per entry | T007, T009 |
| FR-003 | grill-me slice-sizing design-tree branch | T010, T013 |
| FR-004 | grill-me split question recommending N vertical slices | T011, T013 |
| FR-005 | Record chosen split in Design Concept doc | T012, T013 |
| FR-006 | Shared estimator: signals in → `{estimated_loc, suggested_slices, status: ok\|warn}` | T004, T005 |
| FR-007 | Estimator deterministic (byte-identical) | T004, T005 |
| FR-008 | Single source-of-truth ~400-LOC ceiling constant | T002, T004, T005, T017 |
| FR-009 | Both skills invoke the SAME single estimator copy via `${CLAUDE_PLUGIN_ROOT}` | T007, T010, T017 |
| FR-010 | Canonical guidance in ONE doc; skills carry inline summary + link | T002, T006, T010, T017 |
| FR-011 | Advisory-only — no block/gate/exit-code/threshold; `warn` informational | T005, T007, T008, T011, T013, T018 |
| FR-012 | No roadmap-template schema change; reuse existing `Projected reviewable LOC` field | T007, T018 |
| FR-013 | Light trigger touch; no over/under-trigger regression | T014, T015, T021 |
| FR-014 | Every CC skill edit mirrored in Codex; shared doc + script single copies | T009, T013, T015, T017, T023 |
| FR-015 | Doc states estimate is a forward guess, NOT authoritative reviewable-LOC | T002 |
| FR-016 | Predictable, non-crashing on malformed/missing/zero/negative; bad → `0` → `ok` | T004, T005 |
| FR-017 | Optional spike flag → skip LOC threshold → `ok`/1/0; no third status | T002, T004, T005, T018 |

Edge cases: at-ceiling boundary (T004, T005); bad-input status pin (T004, T005); spike (T002,
T004, T005); estimator-unavailable mid-interview (T008 for prd US1 AS5, T011/T013 for grill-me
US2 AS5); existing-trigger-phrase regression (T014, T015, T021).

---

## Notes

- `[P]` tasks = different files, no dependencies on incomplete tasks.
- `[Story]` label maps a task to its user story (US1/US2) for traceability. Setup, Foundational,
  and Polish tasks carry no story label.
- TDD is scoped to the estimator only: T004 (Layer-4 fixture/test) is written and confirmed RED
  before T005 implements the estimator (GREEN). The skill-prose surfaces are validated by the
  developer-local L2/L3/L8 evals (T021–T023), enumerated as follow-ups — not CI gates.
- Each Codex-mirror edit (T009, T013, T015) is paired with its Claude Code edit in the SAME
  phase — mirrors are never deferred to the polish phase as a separate workstream (FR-014).
- The `before_tasks` / `after_tasks` git-commit hooks in `.specify/extensions.yml` are optional;
  committing is handled by the orchestrator, not within this phase.
- Avoid: adding any gate/threshold/exit-code/blocking logic (PRSG-006); adding structured catalog
  fields or a roadmap-template schema change (Q4/Q9 rejected); creating a second/per-skill copy
  of the script or doc; introducing a third `status` value.
