---
description: "Task list for PRSG-004 — Roadmap-MOC home note from PRD + coach the two-zone structure"
---

# Tasks: Roadmap-MOC home note from PRD + coach the two-zone structure

**Input**: Design documents from `/specs/prsg-004-roadmap-moc-home-note/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/roadmap-moc-index.md

**Tests**: This spec explicitly requests TDD (the Layer-4 determinism fixture is written RED before the generator is activated — see plan.md "Testing" and the Tasks Prompt). Test tasks are therefore included and ordered before the production change they guard. Layers 2/3/8 are developer-local AI evals (`claude -p` + `skill-creator`); their tasks are marked dev-local and are not part of the merge-blocking fast suite.

**Reviewability**: Budget = ~200 reviewable production LOC, ~6 production files, ~9 total files, exactly one primary surface (docs/process). This is well under the warn thresholds (400 LOC / 6 files / 15 total / one primary) and far under the block thresholds (800 / 8 / 25). No split. A reviewability checkpoint task (T009A) confirms the budget holds before implementation begins.

**Organization**: Tasks are grouped by user story. Story labels are FIXED by semantics (US1 = prd emits the home note; US2 = coach teaches; US3 = activate render_index) and are NOT renumbered by priority — downstream traceability binds to these labels. Execution-priority order is US3 (P2) → US1 (P1) → US2 (P3), because US1's INDEX-fill step depends on US3's activated renderer (see Dependencies).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths are included in each task. All paths are repo-root-relative within the worktree.

## Path Conventions

This is the **speckit-pro plugin SOURCE repo**, not a `src/`-tree application. There is no build/typecheck/lint/test framework; verification is the bash test layers run from the repo root (`bash tests/speckit-pro/run-all.sh` covers L1, L4, L5). Production files live under `speckit-pro/`; the test suite lives at the repo root under `tests/speckit-pro/` (a sibling of the plugin, never shipped to consumers).

Key paths used below:

- Generator (single shared, runtime-agnostic): `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh`
- Generator libs (reused unchanged): `speckit-pro/skills/speckit-autopilot/scripts/lib/moc-frontmatter.sh`, `.../lib/moc-id-normalize.sh`
- PRSG-002 template (the shape prd emits from): `speckit-pro/skills/speckit-coach/templates/roadmap-moc-template.md`
- prd skill: `speckit-pro/skills/speckit-prd/SKILL.md` (+ Codex mirror `speckit-pro/codex-skills/speckit-prd/SKILL.md`)
- coach skill: `speckit-pro/skills/speckit-coach/SKILL.md` (+ Codex mirror `speckit-pro/codex-skills/speckit-coach/SKILL.md`)
- NEW coach reference: `speckit-pro/skills/speckit-coach/references/roadmap-moc-guide.md`
- L4 test logic: `tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh`
- L4/L1 fixtures (note the cross-directory split — the test logic is in `layer4-scripts/` but its fixtures live under `layer1-structural/`): `tests/speckit-pro/layer1-structural/fixtures/spec-index/`
- L2 trigger evals: `tests/speckit-pro/layer2-trigger/evals/speckit-coach-trigger.json` (+ Codex mirror `tests/speckit-pro/layer2-trigger/codex-evals/speckit-coach-trigger.json`)
- Pinned regression guard: the existing PRSG-003 fixtures under `tests/speckit-pro/layer1-structural/fixtures/spec-index/` (`current-empty`, `determinism`, `legacy-skip`, `template-born`, `inject-missing-all`, `unbalanced-marker`, `prs-*`, etc.) exercised by the existing cases in `test-generate-spec-index.sh`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the working tree and toolchain before touching files. No project scaffolding is needed (existing repo).

- [X] T001 Confirm the feature worktree is on branch `prsg-004-roadmap-moc-home-note` and `bash` (3.2+) and `jq` are on `PATH`; confirm `bash tests/speckit-pro/run-all.sh --layer 4` runs (it will be GREEN on the existing PRSG-003 cases before any change — this is the pre-change baseline).
- [X] T002 [P] Read the byte-level contract `specs/prsg-004-roadmap-moc-home-note/contracts/roadmap-moc-index.md` and note the exact INDEX row format, the U+00B7 (`0xC2 0xB7`) separator framing, the empty-status byte form, and the empty/absent behavior table (FR-017a exit-2, FR-015a skip) — this contract is the source of truth the Phase-2 fixture pins.

---

## Phase 2: Foundational (Blocking Prerequisites) — US3 generator activation (TDD-first)

**Purpose**: The activated `render_index()` home-note path is the prerequisite for US1's INDEX fill. Per the TDD-first directive, the Layer-4 determinism fixture is authored RED (T003–T004) BEFORE the generator is activated (T005–T006); the fixture goes GREEN only after activation. This phase delivers User Story 3 (US3, Priority P2) and the byte-identical regression guard.

**⚠️ CRITICAL**: US1's emit-and-fill task (T012) depends on T006 (the activated renderer). No INDEX-fill work begins until this phase is GREEN.

> **NOTE: Tests in T003–T004 MUST be written and MUST FAIL (RED) before the generator activation in T005–T006.**

### Tests for User Story 3 (TDD — written RED first) ⚠️

- [X] T003 [P] [US3] Create the new home-note determinism fixture REPO_ROOT under `tests/speckit-pro/layer1-structural/fixtures/spec-index/roadmap-moc/` (new fixture dir): a `docs/ai/specs/<slug>-roadmap-MOC.md` home note carrying **only** the INDEX sentinel pair (byte-matching the generator's `INDEX_START`/`INDEX_END` constants and gated with `structureVersion: 1`), plus several `specs/<dir>/SPEC-MOC.md` dirs with varied frontmatter — at minimum: two normally-gated specs (non-empty `spec_id` + `status`), one gated spec with **empty/missing `status`** (FR-015), one gated spec with **absent/empty `spec_id`** (FR-015a), and one **legacy non-gated** dir (FR-016). Mirror the worked example in `contracts/roadmap-moc-index.md`. Also add a sibling fixture variant for the FR-017a case: a **gated home note that does NOT carry its INDEX sentinel pair** (all three GENERATED pairs absent).
- [X] T004 [US3] Add the home-note assertion group to `tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh` (alongside the existing PRSG-003 groups, following the same `assertions.sh` + captured-run style), asserting BOTH halves and every edge: (1) the home note's INDEX zone fills repo-wide with one `- [<spec_id>](../../../specs/<dir>/SPEC-MOC.md) · <status>` row per gated spec, normalized-ID ascending, and EVERY link is a relative `[]()` target — never a `[[wikilink]]` — so every in-scope spec is reachable from the home note (FR-012/FR-013/FR-014/SC-006); (2) **every** `specs/<dir>/SPEC-MOC.md` INDEX zone stays byte-identical/empty after the run (FR-018/SC-005); (3) the empty-status spec still emits a row with the exact frozen empty-status bytes (FR-015); (4) the absent/empty-`spec_id` gated spec is **SKIPPED** — no row (FR-015a); (5) the legacy non-gated dir is skipped (FR-016); (6) the FR-017a fixture (gated home note missing its INDEX pair) makes the generator **fail-safe exit 2 with no write and an actionable stderr line naming the offending home note** (FR-017a); (7) a second consecutive run over the same committed fixture is a **zero-byte diff** on the home note (SC-004/FR-019). This test MUST FAIL (RED) now, since `render_index` returns empty today.

### Implementation for User Story 3

- [X] T005 [US3] In `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh`, add **context-scoped** home-note signal threading through both call frames: `rebuild_map` gains a defaulted 4th arg (`local is_home="${4:-0}"`) and `render_index` gains a defaulted 2nd arg (`local is_home="${2:-0}"`); `rebuild_map` forwards `is_home` to `render_index`. The existing spec-MOC call site stays a 3-arg `rebuild_map "$moc" "$d" "$branch"` call (passes neither extra arg → `is_home=0` → `render_index` returns empty, byte-identical to today). Do NOT introduce a global or re-derive the signal by path-sniffing (research Decision 1).
- [X] T006 [US3] In `generate-spec-index.sh`, give `render_index` its real repo-wide body **guarded by `is_home=1` only** (when `is_home=0` it returns empty as before — FR-018): re-scan `$SPECS_DIR` (`find … -mindepth 1 -maxdepth 1 -type d | LC_ALL=C sort`), gate each `specs/<dir>/SPEC-MOC.md` via `moc_is_gated`, read `spec_id`/`status` via `moc_frontmatter_field`, **skip** rows whose `spec_id` is absent/empty (FR-015a), order by `moc_normalize(spec_id)` ascending (FR-013), and emit `- [<spec_id>](../../../specs/<dir>/SPEC-MOC.md) · <status>` per row — a relative `[]()` target, never a `[[wikilink]]`, so every in-scope spec is reachable — with the `PRS_SEP` U+00B7 framing and the contract's empty-status byte form (FR-012/FR-014/FR-015/FR-022/SC-006). Then teach `main()` to discover home notes via the glob `docs/ai/specs/*-roadmap-MOC.md` (0..N), gate each with `moc_is_gated`, append them to the SAME PASS-1/PASS-2 arrays as the `specs/` scan but **disjoint** from it, supply the home note's basename as the PASS-2 `in_branch` label, and pass `is_home=1` only on the home-note regeneration call (FR-011/FR-017). Add the FR-017a guard: a **discovered, gated** home note with all three GENERATED pairs absent (no INDEX pair) MUST **fail-safe exit 2, no write, actionable stderr** — it MUST NOT take the inject-if-missing path (FR-017a). Run T004 until GREEN. (bash+jq only; no new script, no lib extraction — FR-021.)
- [X] T007 [US3] Re-run the existing PRSG-003 contract fixtures as the byte-identical regression guard: `bash tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh` — every existing PRSG-003 case (`current-empty`, `determinism`, `legacy-skip`, `template-born`, `inject-missing-all`, `unbalanced-marker`, `prs-*`, `atomicity`, `skip-one-missing`, `stale-fill`, `symlinked-moc`) MUST still pass UNCHANGED, proving every per-spec SPEC-MOC.md is byte-identical to its pre-activation output (FR-018/SC-005). If any PRSG-003 case regresses, the activation broke the spec-MOC path — fix T005/T006, do not edit the PRSG-003 fixtures.

**Checkpoint**: `render_index` fills the home note's INDEX repo-wide while every spec-MOC INDEX stays empty/byte-identical; the L4 fixture (T004) is GREEN and the PRSG-003 guard (T007) is unchanged. US3 is independently complete and testable. US1's INDEX fill is now unblocked.

---

## Phase 3: User Story 1 - speckit-prd emits a roadmap-MOC home note (Priority: P1) 🎯 MVP

**Goal**: `speckit-prd`, when it authors a fresh PRD + technical-roadmap, ALSO writes the home note `docs/ai/specs/<slug>-roadmap-MOC.md` (curated epics zone auto-derived from roadmap phases + the INDEX sentinel pair from the template), invokes the generator to fill the INDEX, prints the >~10-epic advisory when applicable, adds the reciprocal roadmap↔home-note links, and updates its Output Contract to three files. Codex parity is a deliverable of this story.

**Independent Test**: Run `speckit-prd` against a fresh fixture roadmap and confirm a third file `docs/ai/specs/<slug>-roadmap-MOC.md` is written alongside the PRD and technical-roadmap, with an editable curated epics zone seeded from the roadmap's phases and a sentinel-bounded GENERATED INDEX zone filled by the generator, plus the reciprocal link on the technical-roadmap (Scenario D, quickstart.md).

> **NOTE**: T012 (emit-and-fill) depends on Phase 2 (T006) — the activated renderer must exist before prd can invoke it to fill the INDEX. The template prerequisite (T010) is the sentinel source.

### Implementation for User Story 1

- [X] T010 [US1] Modify the PRSG-002 template `speckit-pro/skills/speckit-coach/templates/roadmap-moc-template.md` to carry the **empty `GENERATED:INDEX` sentinel pair only** (NOT the PRS or BACKLINKS pairs), using the literal `INDEX_START`/`INDEX_END` byte strings from `generate-spec-index.sh` so a home note copied from this template byte-matches the generator constants (research Decision 3). Add a brief curated-epics-zone intro framing the two zones (curated = hand-edited; INDEX = machine-regenerated, never hand-edited). Keep frontmatter gated (`structureVersion: 1`).
- [X] T011 [US1] In `speckit-pro/skills/speckit-prd/SKILL.md`, add the home-note **curated-zone derivation** prose: derive one epic per roadmap phase/tier (epic title, the phase's member spec links, a one-line advisory "Why" placeholder per epic) as an editable scaffold, adding ZERO new interview questions (FR-003/SC-002); the no-phases/flat-catalog fallback emits a single "Specs" epic listing all specs + an advisory note to group them (FR-004); the home note's frontmatter `up:` is a relative `[]()` link to `<slug>-technical-roadmap.md` and prd adds a one-line reciprocal link from the technical-roadmap back to the home note (FR-006); prd MUST NOT change any spec-MOC's `up:`, the spec-MOC template, or scaffold-spec (FR-008); the home note is emitted ONLY for freshly authored roadmaps — no backfill onto legacy roadmaps (FR-007).
- [X] T012 [US1] In `speckit-pro/skills/speckit-prd/SKILL.md`, add the home-note **emit-and-fill** step: write `docs/ai/specs/<slug>-roadmap-MOC.md` from the PRSG-002 template (so it carries ONLY the INDEX sentinel pair — FR-002) with the curated zone filled around it, then **invoke the generator passing the consumer's repo root positionally** (`generate-spec-index.sh "$CONSUMER_REPO_ROOT"`, NOT relying on the default `PLUGIN_ROOT/..` which is wrong in a consumer install — research risk #2) to fill the INDEX zone (FR-001/FR-011). Print the one-line advisory when the derived scaffold yields >~10 epics, and STILL write the file (advisory only, never a block — FR-005/SC-003). Update the prd **Output Contract to three files** (PRD + technical-roadmap + roadmap-MOC home note — SC-001). (Depends on T006, T010.)
- [X] T013 [US1] Mirror the home-note emit step into the Codex variant `speckit-pro/codex-skills/speckit-prd/SKILL.md`: same two-zone model, same curated-zone derivation from phases, same >~10-epic advisory, same three-file Output Contract, same positional-repo-root generator invocation — **semantic equivalence**, allowed to differ only in Codex's own voice and its free-text Q&A interview mechanism (no `AskUserQuestion`), MUST NOT differ in the model or the emit step (FR-020/SC-008).
- [X] T014 [P] [US1] (dev-local, L3) Add/extend the developer-local L3 functional eval that runs `speckit-prd` on a **fresh fixture roadmap** (NOT this repo) and asserts: exactly three artifacts with both zones present (SC-001), zero new interview questions vs. the pre-PRSG-004 interview (SC-002), >~10-epic roadmap still writes the file + single advisory line (SC-003), and the reciprocal `up:`/roadmap links are relative `[]()` (FR-006). Marked dev-local (`claude -p` + `skill-creator`); not part of the merge-blocking fast suite. **DEV-LOCAL — not run here**: added eval case id 5 to BOTH `tests/speckit-pro/layer3-functional/evals/speckit-prd-evals.json` and `.../codex-evals/speckit-prd-evals.json` (the existing L3 prd eval harness `run-functional-evals.sh` is its home); the case asserts the three-artifact output, the curated-zone-from-phases derivation with zero new questions, the template-emits-only-INDEX-pair + positional-repo-root generator invocation, the >~10-epic advisory-not-block, the reciprocal `up:`/roadmap `[]()` links, and the FR-007/FR-008 no-backfill/no-spec-MOC-change guards. Running it requires `claude -p` + `skill-creator` and is intentionally NOT executed in this task (not merge-blocking).

**Checkpoint**: `speckit-prd` emits the home note as a third artifact with a filled INDEX and a curated epics zone; both Claude and Codex prd mirrors carry the same emit step. US1 is independently testable (Scenario D).

---

## Phase 4: User Story 2 - speckit-coach teaches the two-zone structure (Priority: P3) [P]

**Goal**: `speckit-coach` teaches the curated-vs-generated two-zone split (curated = hand-authored/editable; GENERATED INDEX = machine-regenerated, never hand-edited) and the advisory "cap epics below ~10" guardrail (warn, not block), via a new dedicated reference doc plus a description-surface change. Codex parity is a deliverable of this story. This story is independent of US1/US3 code and can be authored in parallel.

**Independent Test**: Ask `speckit-coach` how the roadmap-MOC home note is structured and confirm it distinguishes the curated zone (hand-edited) from the generated zone (never hand-edited, regenerated by the generator) and states the advisory ~10-epic cap (Scenario E, quickstart.md).

### Implementation for User Story 2

- [X] T015 [P] [US2] Create the NEW reference doc `speckit-pro/skills/speckit-coach/references/roadmap-moc-guide.md` teaching: the home note's two-zone model (curated epics zone = hand-authored/editable; GENERATED INDEX zone = machine-regenerated by `generate-spec-index.sh`, never hand-edited — FR-009), and the "cap epics below ~10" guardrail as an advisory navigability guideline that warns but never blocks (FR-010). Authored ONCE here; the Codex coach mirror links to this shared tree (no duplicate doc — FR-020/research Decision 7).
- [X] T016 [US2] In `speckit-pro/skills/speckit-coach/SKILL.md`, add the description-surface keyword cluster (e.g. "roadmap map / home note / Map of Content / navigation"), one routing-table row pointing at `references/roadmap-moc-guide.md`, and one References-list entry for the new guide (so the two-zone teaching is discoverable and routes correctly). Description measured at 751 chars (≤1024).
- [X] T017 [US2] Mirror the coach teaching surface into the Codex variant `speckit-pro/codex-skills/speckit-coach/SKILL.md`: the same description keyword cluster (in Codex's own voice), one routing-table row, and one References entry that links to the **shared** tree `../../skills/speckit-coach/references/roadmap-moc-guide.md` (no duplicate doc) — conveying the same two-zone split + cap-epics teaching (FR-020/SC-008). Codex description trimmed to fit and measured at 1009 chars (≤1024).
- [X] T018 [P] [US2] Add the new Layer-2 trigger case to `tests/speckit-pro/layer2-trigger/evals/speckit-coach-trigger.json` verifying the coach description surface triggers on a roadmap-MOC home-note query (e.g. "how is the roadmap home note / Map of Content structured?").
- [X] T019 [P] [US2] Add the mirrored Layer-2 trigger case to `tests/speckit-pro/layer2-trigger/codex-evals/speckit-coach-trigger.json` (the Codex mirror eval) verifying the Codex coach description surface triggers on the same roadmap-MOC home-note query.
- [X] T020 [P] [US2] (dev-local, L2/L3) Run the coach trigger + functional evals (`bash tests/speckit-pro/layer2-trigger/run-trigger-evals.sh speckit-coach` and the L3 content eval) to confirm the description triggers on roadmap-MOC queries and the answer correctly explains both zones (generated never hand-edited) and the advisory ~10-epic cap (SC-007). Marked dev-local (`claude -p` + `skill-creator`); not part of the merge-blocking fast suite. **DEV-LOCAL — run not executed here**: the eval cases were added by T018/T019; running them requires `claude -p` + `skill-creator` and is intentionally NOT executed in this task (not merge-blocking).

**Checkpoint**: `speckit-coach` (both Claude and Codex mirrors) teaches the two-zone split and the advisory epic cap; the new L2 trigger cases exist in both eval files. US2 is independently testable (Scenario E).

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Structural validation, parity, the pre-commit skill-quality gate, and the PR review packet. These run after the three stories are complete.

- [X] T021 Run Layer-1 structural validation: `bash tests/speckit-pro/run-all.sh --layer 1` — confirm `validate-codex-skills.sh` is GREEN (the prd emit step exists in BOTH `skills/speckit-prd` and `codex-skills/speckit-prd`; the coach teaching surface exists in BOTH `speckit-coach` mirrors), `validate-plugin-payload` confirms no `tests/`/`specs/` leaked under the plugin dir and the generator remains a single shared copy (not duplicated into `codex-skills/` — FR-021), and the new `references/roadmap-moc-guide.md` is well-formed.
- [X] T022 [P] (Optional belt-and-suspenders, research Decision 3) Add a Layer-1 assertion that the template's INDEX sentinel bytes in `roadmap-moc-template.md` equal the generator's `INDEX_START`/`INDEX_END` constants, pinning the prd→generator sentinel seam at L1 (not strictly required since L4 already fails if they drift, but cheap and catches the silent never-fills case at structural-test speed).
- [X] T023 (dev-local, L8) Run the Path A/B parity fixtures for the two changed skills: `bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run` (free structural check) and, developer-local, the budget-capped `--live` arm — confirm the prd/coach changes keep the Agent-Teams vs parallel-subagents fallback equivalent.
- [X] T024 Run `speckit-skill-reviewer` as a pre-commit gate against the two changed skills (`speckit-prd`, `speckit-coach`) and their Codex mirrors; resolve any findings before commit so the existing skill-quality gate stays green. (prd: applied the reviewer's budget-fitting description rewrite — now accurately says "three artifacts" and lists the home note in both mirrors, ≤1024. coach: clean except a PRE-EXISTING missing `license: MIT` in the Codex mirror, out of scope here.)
- [X] T025 Run the full fast suite as the constitution-IV "implementation complete" gate: `bash tests/speckit-pro/run-all.sh` (Layers 1, 4, 5) — zero failures, including the new home-note L4 case and the unchanged PRSG-003 cases.
- [ ] T026 Generate/update the PR review packet: what changed, why, non-goals, review order (generator `render_index` branch + the new contract → the L4 fixture → the prd emit step → the coach teaching), scope budget (~200 LOC, one primary surface), traceability (each FR/SC → changed files + verification evidence), verification evidence (`bash tests/speckit-pro/run-all.sh` green incl. new L4 fixture; PRSG-003 cases unchanged), known gaps (single-roadmap INDEX scope; navigation backfill + per-roadmap INDEX scoping deferred to PRSG-011; prd MUST pass the consumer repo root positionally — research risk #2), and rollback notes (revert is file-local; no feature flag — the epic cap is advisory, the home-note path is additive and new-roadmaps-only).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational / US3 (Phase 2)**: Depends on Setup. Delivers the activated renderer. **BLOCKS US1's emit-and-fill task (T012)** because prd cannot fill the INDEX until `render_index` is live.
- **US1 (Phase 3)**: T012 depends on Phase 2 (T006) and on T010 (template sentinel source). T011 (curated-zone prose) and T013 (Codex mirror) do not strictly depend on the renderer but live in this story; the Codex mirror (T013) depends on the Claude emit step (T012) it mirrors.
- **US2 (Phase 4)**: Independent of US1/US3 code — can be authored in parallel with Phases 2–3 (it is pure docs/coaching prose + eval cases).
- **Polish (Phase 5)**: Depends on US1, US2, US3 being complete.

### User Story Dependencies

- **User Story 3 (US3, P2)**: The enabling change. No dependency on other stories. Ordered FIRST in execution despite its P2 label because US1's INDEX fill consumes its output.
- **User Story 1 (US1, P1)**: Its **emit-and-fill** task (T012) depends on US3 (T006). Its curated-zone emission (T011) does not depend on US3 and frames what US3 fills.
- **User Story 2 (US2, P3)**: Independent of US1 and US3 — fully parallelizable.

### Within Each User Story

- US3: the L4 fixture/test (T003–T004) is written RED and MUST FAIL before the generator activation (T005–T006); the regression guard (T007) runs after activation.
- US1: the template sentinel source (T010) and curated-zone prose (T011) before the emit-and-fill (T012); the Claude emit step (T012) before its Codex mirror (T013).
- US2: the shared reference doc (T015) before the description-surface wiring (T016) and its Codex mirror (T017); the eval cases (T018/T019) are independent of each other.

### Parallel Opportunities

- **T002** (read the contract) runs parallel to T001.
- **T003** (build the fixture tree) is [P] within Phase 2 — it touches only the new fixture dir, disjoint from the test file T004 edits.
- **Entire US2 (Phase 4) runs in parallel with Phases 2–3** — it shares no files with the generator or prd work.
- Within US2: **T015** (new reference doc), **T018** and **T019** (the two eval files), and **T020** (dev-local evals) are mutually [P] — each touches a different file.
- **T014** (US1 dev-local L3 eval) is [P] — it touches only its eval fixture, not the prd SKILL.md.
- In Phase 5, **T022** is [P] (a new L1 assertion, independent of the other polish steps).

---

## Parallel Example: User Story 2 (authored in parallel with US3/US1)

```bash
# US2 shares no files with the generator (US3) or prd (US1) work, so it can be
# authored concurrently. Within US2, these touch different files and run together:
Task: "Create speckit-pro/skills/speckit-coach/references/roadmap-moc-guide.md"          # T015
Task: "Add L2 trigger case to tests/.../evals/speckit-coach-trigger.json"                # T018
Task: "Add L2 trigger case to tests/.../codex-evals/speckit-coach-trigger.json"          # T019
```

---

## Implementation Strategy

### MVP scope

US3 + US1 together are the MVP: US3 activates the deterministic INDEX renderer, and US1 makes `speckit-prd` emit the home note and fill it. US2 (coaching) ships independently and adds the teaching layer. Because US1's value (a navigable home note with a filled INDEX) requires US3's renderer, the MVP is the US3→US1 pair, not US1 alone.

### Recommended order (single implementer)

1. Phase 1 (Setup) → Phase 2 (US3, TDD-first: fixture RED → activate → GREEN → PRSG-003 guard).
2. Phase 3 (US1: template sentinel → curated-zone prose → emit-and-fill against the live renderer → Codex mirror).
3. Phase 4 (US2: shared reference doc → description wiring → Codex mirror → eval cases) — could also be done concurrently from the start.
4. Phase 5 (Polish: L1 structural + parity + skill-reviewer + full fast suite + PR packet).

### Parallel team strategy

- Developer A: Phase 2 (US3 generator activation) → Phase 3 (US1 prd emit).
- Developer B: Phase 4 (US2 coach teaching) from the start — no shared files.
- Both converge on Phase 5.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks.
- [Story] labels (US1/US2/US3) are FIXED by semantics and map to spec.md's fixed labels — do NOT renumber by priority.
- TDD: the L4 home-note fixture (T003–T004) MUST FAIL before the generator activation (T005–T006); verify RED before implementing GREEN.
- The generator stays a single shared copy referenced by path — never duplicated into `codex-skills/` (FR-021). US3 carries NO Codex-mirror task; only US1 and US2 do (those are skill-prose surfaces).
- Codex-mirror coupling: every skill-prose change carries its Codex mirror in the SAME story — T013 (prd), T017 (coach), T019 (coach L2 eval).
- The PRSG-003 fixtures are the byte-identical regression guard — re-run unchanged (T007); never edit them to make a regressed activation pass.
- Commit after each task or logical group (the `before_tasks`/`after_tasks` git hooks are optional and handled by the orchestrator).
- Reviewability: the task list stays within the ~200-LOC / ~6-production-file / ~9-total-file budget (T009A-equivalent confirmation folded into T021/T025); no split needed.
