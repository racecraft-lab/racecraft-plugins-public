# SpecKit Workflow: PRSG-002 — MOC templates + scaffold-time skeleton + version-gated lints

**Template Version**: 1.0.0
**Created**: 2026-06-06
**Purpose**: Autopilot-executable workflow for PRSG-002. Phase prompts below encode the locked decisions from the Grill Me interview.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/PRSG-002-design-concept.md
```

The design concept is the **source of truth** for every scoping decision below.
Re-read it before each phase to disambiguate a prompt.

> **Note:** Grill Me is human-in-the-loop only and is **not** part of the
> autopilot loop. Once autopilot begins, clarifications happen via
> `/speckit-clarify` and the consensus protocol — never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | 19 FRs, 0 clarification markers. Contract dir=`specs/prsg-002-moc-templates`. Resolved spec_id↔dir join → decision (A): namespace-prefixed dirs, spec_id carries roadmap id. |
| Clarify | `/speckit-clarify` | ✅ Complete | Verify-not-reopen pass (2 sessions, 0 markers). Tightened FR-004/007/009/010/011/017/018 + 2 assumptions: SPEC-MOC lives in CONTRACT dir `specs/<branch>/`; MOC=exact filename; orphan checks `up:` well-formedness, stale-index resolves `up:` value; exact-segment = opaque-segment compare. R1 (create-new-feature numbering) resolved from primary source. |
| Plan | `/speckit-plan` | ✅ Complete | plan.md + research/data-model/quickstart + 3 contracts. Surfaces: MOC templates in skills/speckit-coach/templates/; shared normalizer tests/lib/moc-id-normalize.sh; lints tests/layer1-structural/validate-moc-{orphan,stale-index}.sh; scaffold-spec edit (CC+Codex); run-all.sh wiring; fixtures+L4 test. NOTE: update-agent-context.sh added a SPECKIT pointer block to CLAUDE.md → flag for self-review (may not belong on main). |
| Checklist | `/speckit-checklist` | ✅ Complete | data-integrity (20 items, 5 gaps closed) + error-handling (21 items, 10 gaps closed). Added FR-020..024 (3-way exit enum 0/1/2 + trap, total/safe marker parsing, scan-root robustness, exempt-before-content invariant, actionable output) + FR-011 non-regular-file target + total/symmetric ID grammar. Contracts + data-model synced. (error-handling executor socket-died mid-remediation; orchestrator completed it from primary evidence.) |
| Tasks | `/speckit-tasks` | ✅ Complete | 24 tasks (T001–T024) in 5 groups; all 24 FRs mapped; 10 [P]; RED-before-GREEN; Codex mirror paired (T007↔T008). +1 file beyond plan: tests/layer4-scripts/test-moc-lint-exit-codes.sh (subprocess driver for the 3-way exit contract). Reviewability gate: pass (transition exception). |
| Analyze | `/speckit-analyze` | ✅ Complete | 3 findings, 0 CRITICAL → G6 PASS. 1 MEDIUM (plan↔tasks Layer-4 count reconciled to 2 + manifest), 2 LOW (SC-004 coverage annotation; T008 codex-parity wording softened to existence-level). All 5 SCs covered; 24/24 FRs; Codex parity intact; 0 unresolved for consensus. Pre-Implement confidence 0.94 (advisory mode, ≥0.90 → G6.5 PASS). |
| Implement | `/speckit-implement` | ✅ Complete | 24 tasks via 5 TDD groups (A normalizer, B templates+scaffold, C1 orphan+gating+spec_id, C2 stale-index+exit-codes+wiring, D polish). New surfaces: 2 MOC templates, shared normalizer + version-gate helpers, orphan + stale-index Layer-1 lints, Layer-4 normalizer + exit-code drivers, scaffold-spec writes SPEC-MOC.md (CC+Codex), PRSG-002 marker. Suite 1551→1640 all green (G7 PASS); lints dogfood-green on real trees; script safety 55/55. |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | User stories clear, no `[NEEDS CLARIFICATION]` remain |
| G2 | After Clarify | Locked decisions reflected; no drift from the design concept |
| G3 | After Plan | Template/script/lint surfaces identified; Codex parity planned |
| G4 | After Checklist | All `[Gap]` markers addressed |
| G5 | After Tasks | Every FR maps to a task; L1+L4 fixtures enumerated |
| G6 | After Analyze | No `CRITICAL`; no contradiction with the design concept |
| G7 | After Implementation | `bash tests/run-all.sh` green; lints pass on this repo's real specs |

---

## Prerequisites

### Constitution Validation

This repo is a Claude Code plugin marketplace (bash + jq + markdown; no compiled runtime).

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Surgical edits | Touch only what PRSG-002 requires | Diff review; reviewability gate |
| Deterministic shell | Plain `bash` + `jq`, no new deps | `tests/run-all.sh --layer 1` / `--layer 4` |
| Codex parity | Every CC skill change mirrored in `codex-skills/` | `validate-codex-parity.sh`, `validate-codex-skills.sh` |
| Test-first | Layer-1/Layer-4 fixtures RED before GREEN | `bash tests/run-all.sh` |

**Constitution Check:** mark ✅ before G1.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | PRSG-002 |
| **Name** | MOC templates + scaffold-time skeleton + version-gated lints |
| **Branch** | `prsg-002-moc-templates` |
| **Dependencies** | PRSG-001 (`.process/` path) — ✅ complete |
| **Enables** | PRSG-003 (index/backlinks/status), PRSG-004 (roadmap-MOC home note), PRSG-011 (retro-migration) |
| **Priority** | P1 (Phase 2) |

### Success Criteria Summary

- [ ] `speckit-scaffold-spec` writes a minimal `SPEC-MOC.md` (carrying `up:`, `structureVersion: 1`, `spec_id`) on every new spec — mirrored in the Codex variant.
- [ ] Two MOC template shapes (`roadmap-moc-template.md`, `spec-moc-template.md`) live in the plugin templates dir.
- [ ] Orphan lint (Layer-1): every MOC in a version-gated spec has a valid `up:`; `.process/**` exempt; no-marker specs skipped.
- [ ] Stale-index lint (Layer-1): every relative link in a MOC resolves; `[[wikilinks]]` in a MOC are flagged as violations.
- [ ] Namespace-aware ID normalization joins `spec_id` ↔ dir across both `SPEC-` and `PRSG-` without `SPEC-002`/`PRSG-002` collision; exact-segment number match (`013a` ≠ `013a1`).
- [ ] Lints are version-gated (fire only at `structureVersion >= 1`), wired into `tests/run-all.sh`, and **green on this repo's existing legacy specs on day one**.
- [ ] `bash tests/run-all.sh` passes (L1 + L4 + L5).

---

## Phase 1: Specify

### Specify Prompt

```bash
/speckit-specify

## Feature: MOC templates + scaffold-time skeleton + version-gated lints (PRSG-002)

### Problem Statement
Spec artifacts have no navigation/traceability spine. When artifacts are collapsed
(`.process/`) or relocated, docs can become unreachable, and decomposition forces
you to memorize the directory tree. PRSG-002 introduces a Maps-of-Content (MOC)
layer: template shapes, a scaffold-time skeleton, and version-gated lints that keep
the map connected — without red-failing CI on the pre-existing legacy specs.

### Users
Plugin maintainers and any consuming project running speckit-pro; reviewers who
navigate specs.

### User Stories
- US1 — Templates + scaffold-time skeleton. Provide a roadmap-MOC and a spec-MOC
  template carrying the frontmatter join-key contract
  (`up`/`related`/`status`/`rank`/`spec_id`/`structureVersion`). `speckit-scaffold-spec`
  writes a MINIMAL `SPEC-MOC.md` on EVERY new spec at creation, carrying `up:`,
  `structureVersion: 1`, and `spec_id`. (A spec is only fleshed into a full
  navigation map when it later splits into multiple slices; the minimal marker file
  is written regardless of slice count, because it is the version-gate carrier.)
- US2 — Version-gated lints + namespace-aware ID normalization. Two Layer-1 lints:
  orphan (a MOC lacking a valid `up:`) and stale-index (a MOC relative link that
  does not resolve; a `[[wikilink]]` in a MOC is itself a violation). Each lint
  fires ONLY when the spec's `SPEC-MOC.md` has `structureVersion >= 1`; a spec with
  no marker is grandfathered/exempt. ID normalization joins doc IDs to dir IDs as
  `(namespace, number-suffix)`: lowercase, detect optional leading alpha prefix
  (`spec-`/`prsg-`); a dir with no prefix defaults to the legacy `spec` namespace;
  match both parts with exact-segment compare on the number-suffix.

### Constraints
- Relative `[]()` links only — never `[[wikilinks]]`.
- `structureVersion` is an integer; v1 = 1; the literal is hardcoded in the lint
  script(s) and stamped by scaffold-spec, with a "keep in sync" comment.
- Orphan lint v1 requires `up:` ONLY on MOC files; non-MOC docs
  (spec.md/plan.md/tasks.md/contracts) are NOT required to carry `up:`.
- `SPEC-MOC.md`'s `up:` points to the existing `*-technical-roadmap.md` (PRSG-004
  later repoints it to the roadmap-MOC home note).
- Lints hard-fail (exit nonzero) on violation in a version-gated spec; no-marker
  specs are silently skipped.

### Out of Scope
- Generated MOC content: down-index, backlinks, status integration (PRSG-003);
  PRD-derived roadmap-MOC home note (PRSG-004).
- Retro-migration/backfill of legacy specs and relocation of existing top-level
  exhaust into `.process/` (PRSG-011).
- Requiring `up:` on non-MOC docs in v1.
- Wikilink support.
```

---

## Phase 2: Clarify

Decisions are already locked in the design concept. Clarify should **verify
consistency, not reopen** them. Flag any spec wording that contradicts a locked
decision.

#### Session 1: MOC contract + scaffold-time skeleton

```bash
/speckit-clarify Focus on the MOC frontmatter contract and the scaffold-time skeleton:
confirm scaffold-spec ALWAYS writes a minimal SPEC-MOC.md (up: + structureVersion: 1 + spec_id);
confirm the three load-bearing fields (up, structureVersion, spec_id) are required while
status/rank/related ship in the template but are optional in v1; confirm Codex parity
(mirror the scaffold-spec change in codex-skills/speckit-scaffold-spec; templates + lints shared).
```

#### Session 2: Lints, version-gating, ID normalization

```bash
/speckit-clarify Focus on the two Layer-1 lints: orphan is MOC-only in v1 (.process/** exempt);
stale-index checks relative-link resolution AND flags [[wikilinks]] as violations; both are
version-gated (fire only at structureVersion >= 1, no-marker = exempt) and hard-fail; ID
normalization is namespace-aware (spec/prsg; no-prefix dir defaults to spec) with exact-segment
number compare; lints run in tests/run-all.sh against this repo's real spec trees and must be
green on existing legacy specs.
```

---

## Phase 3: Plan

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Runtime: bash + jq (deterministic shell); Markdown templates. No compiled build.
- Skill surface: speckit-pro/skills/speckit-scaffold-spec/SKILL.md (+ Codex mirror
  codex-skills/speckit-scaffold-spec/SKILL.md).
- Templates: add roadmap-moc-template.md + spec-moc-template.md to the plugin
  templates dir next to workflow-template.md; scaffold-spec reads the spec-MOC
  template and writes SPEC-MOC.md via token substitution (same mechanism as
  workflow-template.md).
- Lints: new Layer-1 shell scripts under speckit-pro/tests/layer1-structural/
  (orphan + stale-index), wired into run-all.sh; committed fixtures for the logic.
- Tests: Layer 1 (orphan, stale-index, wikilink rejection, version-gate,
  ID-normalization fixtures) + Layer 4 if any shared helper warrants unit coverage.

## Architecture Notes
- structureVersion: integer literal 1, hardcoded in the lint script(s) AND stamped
  by scaffold-spec, with a "keep in sync" comment. Lint fires for >= shipped version.
- Namespace-aware normalizer: normalize(id_or_dir) -> (namespace, number_suffix);
  lowercase; strip leading [a-z]+- only when the next segment starts with a digit;
  a dir with no alpha prefix => namespace 'spec'; exact-segment compare on
  number_suffix (013a != 013a1). Provide one shared helper used by both lints.
- Orphan lint: enumerate MOC files (SPEC-MOC.md / spec-MOCs) under version-gated
  specs; assert each has a non-empty up: resolving to an existing file. Exempt
  .process/**; skip specs whose SPEC-MOC.md is absent or lacks structureVersion.
- Stale-index lint: for each MOC, every relative []() link target must resolve;
  any [[wikilink]] is a violation.
- Codex parity: mirror the scaffold-spec skeleton-writing instructions in the Codex
  SKILL.md; templates and lint scripts are single shared copies (runtime-agnostic).
- Reviewability budget ~350 LOC, single primary surface (docs/process).
```

---

## Phase 4: Domain Checklists

### Recommended Domains

| Domain | Why |
|---|---|
| **data-integrity** | The ID-normalization join and the frontmatter contract are correctness-critical: a wrong join emits false orphan/stale hits or silently mis-links. Validate the namespace + exact-segment rules and the three required fields. |
| **error-handling** | The lints must behave correctly on malformed/missing frontmatter, absent SPEC-MOC.md (grandfathering), empty `up:`, and unreadable files — and never red-fail legacy specs. Validate the version-gate skip path and hard-fail path. |

#### 1. data-integrity Checklist

```bash
/speckit-checklist data-integrity

Focus on PRSG-002 requirements:
- Namespace-aware normalization: SPEC- vs PRSG- prefixes; no-prefix dir => 'spec';
  SPEC-002 vs PRSG-002 must NOT collide; 013a must NOT match 013a1.
- The three required frontmatter fields (up, structureVersion, spec_id) and the
  spec_id <-> directory join.
- Pay special attention to: exact-segment matching and cross-namespace collisions.
```

#### 2. error-handling Checklist

```bash
/speckit-checklist error-handling

Focus on PRSG-002 requirements:
- Version-gate skip: no SPEC-MOC.md or no structureVersion => spec is exempt (green).
- Malformed/empty up:, unreadable MOC, wikilink present => correct violation/exit code.
- Lints must be green on this repo's existing legacy specs on day one.
- Pay special attention to: never red-failing a grandfathered legacy spec.
```

---

## Phase 5: Tasks

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Small, testable chunks; each references a success criterion.
- TDD: write the Layer-1 fixture (RED) before the lint logic (GREEN).
- Mark parallel-safe tasks [P]; keep Codex-mirror edits paired with their CC edits.

## Implementation Phases
1. Foundation — roadmap-moc-template.md + spec-moc-template.md (frontmatter contract).
2. US1 — scaffold-spec writes minimal SPEC-MOC.md (CC) + Codex mirror.
3. US2 — shared namespace-aware normalizer; orphan lint; stale-index lint (incl.
   wikilink rejection); version-gating; wire into run-all.sh.
4. Tests + polish — L1 fixtures (orphan, stale, wikilink, version-gate,
   ID-normalization incl. SPEC-002/PRSG-002 + 013a/013a1), confirm green on real specs.

## Constraints
- Plugin templates dir for templates; layer1-structural/ for lint scripts.
- Bound by Non-goals: no generated MOC content, no up: on non-MOC docs, no retro-migration.
```

---

## Phase 6: Analyze

```bash
/speckit-analyze

Focus on:
1. Consistency with the design concept (docs/ai/specs/.process/PRSG-002-design-concept.md)
   — flag ANY drift from the 8 locked decisions + 3 recorded defaults.
2. Coverage — every success criterion maps to a task and a Layer-1 fixture.
3. Codex parity — scaffold-spec CC change has a matching Codex SKILL.md change.
4. Scope — nothing strays into PRSG-003/004/011 territory (no generated content,
   no retro-migration, no up: on non-MOC docs).
```

---

## Phase 7: Implement

```bash
/speckit-implement

## Approach: TDD-First (RED -> GREEN -> REFACTOR -> VERIFY)

Consult the design concept Q&A for the "why" behind each decision. Key invariants:
- scaffold-spec ALWAYS writes a minimal SPEC-MOC.md (up: + structureVersion: 1 + spec_id);
  mirror in codex-skills/speckit-scaffold-spec/SKILL.md.
- structureVersion literal 1 hardcoded in lint(s) + scaffold, "keep in sync" comment.
- Namespace-aware normalizer shared by both lints; exact-segment number compare;
  no-prefix dir => 'spec'; no SPEC-002/PRSG-002 collision.
- Orphan lint MOC-only; .process/** exempt; no-marker specs skipped; hard-fail.
- Stale-index: relative links must resolve; [[wikilinks]] are violations.
- SPEC-MOC.md up: -> existing *-technical-roadmap.md.

### Verification
1. `bash tests/run-all.sh` (L1 + L4 + L5) green.
2. Run the new lints against this repo's real spec trees — must be green (legacy
   specs grandfathered).
3. Confirm a freshly-scaffolded spec gets a valid SPEC-MOC.md that passes both lints.
```

---

## Post-Implementation Checklist

- [X] All tasks complete in tasks.md (24/24 [X])
- [X] `bash tests/run-all.sh` green (L1 + L4 + L5) — 1640/1640
- [X] New lints green on this repo's existing legacy specs (grandfathered) AND on PRSG-002's freshly-written marker
- [X] Codex parity: `validate-codex-parity.sh` (74/74) + `validate-codex-skills.sh` pass
- [X] Reviewability gate passes (transition exception; implementation surface ~350 LOC, bulk of diff is SDD process/spec markdown)
- [X] PR created with a plain-English body + UAT runbook — **PR #116** (https://github.com/racecraft-lab/racecraft-plugins-public/pull/116)

---

## Self-Review (auto-generated)

**Tests executed:** Yes. `bash tests/run-all.sh` (Layers 1, 4, 5) ran during Phase 7 and was re-run independently by the orchestrator after the final group, returning **1640/1640 passed, exit 0** (L1 387+419, L4 644, L5 190; +89 over the 1551 baseline). This repo has no BUILD/TYPECHECK/LINT/INTEGRATION step — `bash tests/run-all.sh` is the full verification. Both new lints were also run standalone and exit 0 on the real spec trees (dogfood).

**Edge cases:** All acceptance criteria have non-happy-path tests. orphan missing/empty/wikilink `up:` → `fixtures/moc/orphan/*`; stale-index absent target / directory target / broken symlink / wikilink → `fixtures/moc/stale/*`; version-gate no-marker / no-version / `<1` / quoted / decimal / text / no-fence → `fixtures/moc/gate/*`; `spec_id` mismatch / cross-namespace collision / `013a`-vs-`013a1` near-miss / absent / empty → `fixtures/moc/specid/*` + `test-moc-id-normalize.sh` (22 assertions); exit-2-on-internal-error / unreadable-marker-skip / missing-or-empty-scan-root / exempt-before-content / stdout-vs-stderr → `test-moc-lint-exit-codes.sh` (34 assertions, cases a–e). No `[edge-case-gap]`.

**Requirements matched:** FR-001..FR-024 each map to ≥1 `[X]` task and ≥1 fixture/test (FR→Task map in tasks.md; all 24 boxes now `[X]`), with implementation evidence in commits 8339282 / 5b8bfe5 / 7ea67ba / afb9816 and the green suite. No orphan FRs and no orphan tasks.

**Follow-up:** (1) Deferred-by-design per Non-goals — PRSG-003 (generated MOC content / down-index / backlinks), PRSG-004 (roadmap-MOC home note + repoint `up:`), PRSG-011 (retro-migration / relocation); all already tracked on the PR-size-governance roadmap and noted in the PR body Out-of-scope. (2) Cosmetic: under `set -E` the internal-error stderr line can print twice (documented in the stale-index lint); the exit code is always `2` on stderr, so the contract holds. (3) `update-agent-context.sh` added a `<!-- SPECKIT START -->…plan.md…<!-- SPECKIT END -->` pointer block to the repo's top-level `CLAUDE.md`; this is standard SpecKit behavior inside auto-managed markers, flagged in the PR body for the maintainer to keep or drop at merge. No silent deferrals.
```
