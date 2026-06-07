# SpecKit Workflow: PRSG-003 — Generated index/PRs/backlinks + status integration + phase-gate regen

**Template Version**: 1.0.0
**Created**: 2026-06-06
**Purpose**: Autopilot-ready workflow for PRSG-003. Phase prompts below were populated from the Grill Me interview; the autopilot reads them phase by phase.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log (11 questions), Goals,
Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/PRSG-003-design-concept.md
```

Re-read it before each phase if you need to disambiguate a prompt. The
design concept doc is the **source of truth** for every scoping decision; if a
downstream artifact contradicts it, the downstream artifact is wrong unless
there is an explicit revision note.

> **Note:** Grill Me is human-in-the-loop only. It is **not** part of the
> autopilot loop. Once autopilot begins, clarifications happen via
> `/speckit-clarify` and the consensus protocol — never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | 2 stories, 20 FR, 10 SC; 0 markers; G1 pass; branch-aware (before_specify hook skipped) |
| Clarify | `/speckit-clarify` | ✅ Complete | 3 sessions + 1 consensus; SC-002/FR-008/FR-017/SC-010 tightened; roadmap L8→L1 bar settled; 0 markers; G2 pass |
| Plan | `/speckit-plan` | ✅ Complete | plan.md + research.md + data-model.md + 3 contracts + quickstart.md; 4 deferred decisions finalized; bash+jq only, reuses moc-id-normalize.sh; G3 pass |
| Checklist | `/speckit-checklist` | ✅ Complete | data-integrity (5 gaps→0, +SC-011) + error-handling (12 gaps→0, +FR-021/FR-022/SC-012, atomic writes); FR-022 fork resolved fail-safe via consensus; G4 pass |
| Tasks | `/speckit-tasks` | ✅ Complete | 26 tasks (8 [P]), 2 stories; TDD RED tests T005/T006 before generator; every FR→task; Codex mirrors paired (T016/T018); G5 pass; tasks-mode reviewability `block`→ratified exception (path-token over-count, deferred to pre-PR diff gate) |
| Analyze | `/speckit-analyze` | ✅ Complete | 0 CRITICAL; no design-concept drift; no PRSG-004/009/011 creep; T020 ruled DROP (roadmap-template INDEX is PRSG-004 scope; T019 alone satisfies FR-017); Codex mirror symmetry + PRS-format drift fixed; 0 unresolved → consensus skipped; G6 pass |
| Implement | `/speckit-implement` | ✅ Complete | TDD RED→GREEN; generator + status/autopilot wiring + Codex mirrors + dogfood; full suite 1659/1659; lint clean; 0 placeholder tests; G7 pass |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | User stories clear; no `[NEEDS CLARIFICATION]` markers remain |
| G2 | After Clarify | Sentinel format, ordering, PRS input contract, and the status/autopilot wiring all pinned |
| G3 | After Plan | `bash`+`jq` only; reuses `moc-id-normalize.sh`; no new dependency; Codex parity planned for the two mirrored skills |
| G4 | After Checklist | All `[Gap]` markers addressed |
| G5 | After Tasks | Every FR maps to a task; L1 determinism fixture + L4 enumerated; Codex SKILL.md edits paired |
| G6 | After Analyze | No `CRITICAL`; no contradiction with the design concept; no scope creep into PRSG-004/009/011 |
| G7 | After Implementation | `bash tests/run-all.sh` green; lints dogfood-green on real spec-MOCs; generator is deterministic (re-run = zero diff) |

---

## Prerequisites

### Constitution Validation

Verify alignment with `.specify/memory/constitution.md` (v1.1.0) before G1:

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| II. Script Safety | New `generate-spec-index.sh` is `set -euo pipefail`, `shellcheck`-clean, `bash -n`-clean | `shellcheck` + `bash -n` + script-safety suite |
| IV. Test Coverage Before Merge | Generator has an L1 determinism fixture + L4 unit tests; lints stay green | `bash tests/run-all.sh` |
| VI. KISS, Simplicity & YAGNI | No code for data that doesn't exist yet (PRS population, cross-spec graph, roadmap-MOC home note all deferred) | Code review against the design concept Non-goals |
| V. Conventional Commits | Public-readable PR title `feat(speckit-pro): …`; no internal IDs in title/body | `validate-pr-title` CI |
| I. Plugin Structure Compliance | Codex mirrors for `speckit-status` + `speckit-autopilot` SKILL.md stay in parity | `validate-codex-skills.sh` (L1) |

**Constitution Check:** ✅ / ❌ (mark before proceeding to G1)

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | PRSG-003 |
| **Name** | Generated index/PRs/backlinks + status integration + phase-gate regen |
| **Branch** | `prsg-003-spec-index` |
| **Dependencies** | PRSG-002 (MOC templates + version-gated lints + ID normalizer) — **merged on `main`, PR #116** |
| **Enables** | PRSG-004 (roadmap-MOC home note fills the dormant INDEX zone), PRSG-009 (multi-PR emission populates the PRS zone), PRSG-011 (retro-migration reuses `generate-spec-index.sh` for legacy backfill) |
| **Priority** | P1 · Phase 2 |
| **Budget** | ~350 production LOC (`bash`+`jq`) |

### Success Criteria Summary

- [ ] `generate-spec-index.sh` exists at `speckit-pro/skills/speckit-autopilot/scripts/`, is **deterministic** (same repo inputs → byte-identical output; re-run produces zero diff), and **reuses** `speckit-pro/tests/lib/moc-id-normalize.sh` for every ID join (no reinvented normalizer).
- [ ] Three sentinel-bounded zones — **INDEX**, **PRS**, **BACKLINKS** — each wrapped by an independent HTML-comment `START/END` pair; the whole zone is regenerated, never `sed`-patched; a file missing a pair skips that zone.
- [ ] `spec-moc-template.md` is updated so new specs are **born** with empty zones; the generator **injects-if-missing** into existing version-marked spec-MOCs, then fills them.
- [ ] **BACKLINKS** renders a per-spec reachability index over `specs/<branch>/**` (incl. its `.process/`) in canonical order — closing PRSG-002's deferred "non-MOC docs reachable" loop, dogfood-proven on `prsg-002` and `prsg-003`.
- [ ] `speckit-status` invokes the generator in **read-only `--check` mode** (regenerate in memory, diff, report staleness; writes nothing).
- [ ] `speckit-autopilot` runs regeneration as an **idempotent phase-gate step at every phase boundary**, committing only on a non-empty diff (the authoritative write path).
- [ ] The **roadmap INDEX** path is built and fixture-tested but **dormant** here (it activates when PRSG-004 supplies the home note); the **PRS** renderer reads a **repo-local committed source only** (never live `gh`).
- [ ] L1 determinism fixture + L4 unit tests pass; full suite green; Codex parity intact for both mirrored skills.

---

## Phase 1: Specify

**When to run:** Start of the feature. Focus on **WHAT** and **WHY**. Output: `specs/prsg-003-spec-index/spec.md`

### Specify Prompt

```bash
/speckit-specify

## Feature: Generated index/PRs/backlinks + status integration + phase-gate regen (PRSG-003)

### Problem Statement
PRSG-002 shipped the MOC navigation layer as STATIC markdown shapes (templates,
a scaffold-time skeleton, version-gated orphan/stale-index lints). Plain markdown
has no live engine: any generated block must be regenerated from the source tree
or it silently lies — the #1 risk in the PR-size-governance roadmap. PRSG-003
adds the engine: a deterministic generator that (re)writes sentinel-bounded zones
so the maps stay true, and closes the loop PRSG-002 explicitly deferred ("non-MOC
docs become reachable via the MOC down-index once PRSG-003 lands").

### Users
- Repo maintainers reading `speckit-status` (must trust the index isn't stale).
- The autopilot, which regenerates the maps as part of its phase gates.
- Downstream specs: PRSG-004 (roadmap home note), PRSG-009 (multi-PR emission),
  PRSG-011 (legacy backfill) all build on this engine.

### User Stories
- [US1] Generator. `generate-spec-index.sh` writes three sentinel-bounded zones —
  GENERATED INDEX (roadmap → spec-MOCs), GENERATED PRS (slice → PR# → merged SHA),
  GENERATED BACKLINKS (a spec's own-artifact reachability index) — between
  HTML-comment START/END pairs. Deterministic and fixture-tested. Reuses the
  canonical ID-normalization join (`moc-id-normalize.sh`) and always regenerates
  the WHOLE zone (never sed-patches — stale partial zones lie).
- [US2] Wire it. `speckit-status` invokes the generator in read-only `--check`
  mode (regenerate in memory, diff the committed file, report staleness, write
  nothing). The autopilot runs regeneration as an idempotent phase-gate step at
  every phase boundary, committing only when the diff is non-empty.

### Constraints
- `bash` + `jq` only; no new dependency (constitution II, CLAUDE.md rule 2).
- Deterministic: a pure function of committed repo files. Canonical ordering —
  normalized-ID order across specs; fixed artifact precedence (spec.md → plan.md
  → tasks.md → data-model → research → contracts/** → checklists/** → .process/**)
  then lexicographic path within a spec.
- Reuse `speckit-pro/tests/lib/moc-id-normalize.sh` (`moc_normalize` / `moc_id_match`).
- Discovery: only specs that already carry a `SPEC-MOC.md` (version-marked); legacy
  specs with no MOC are skipped.
- ~350 production LOC.

### Out of Scope (deferred by design — see design concept Non-goals)
- Populating the roadmap-level INDEX against a real roadmap-MOC home note — the
  home note is PRSG-004; PRSG-003's INDEX path is built+tested but DORMANT here.
- Live population of slice → PR# → merged SHA — PRSG-003 only RENDERS the PRS zone
  from a repo-local committed source; the writer is PRSG-009. Never call `gh` at
  generation time.
- Backfilling/injecting zones into legacy specs that lack a `SPEC-MOC.md` — PRSG-011.
- An inbound cross-spec citation graph (reverse `related:`/`depends-on`) — `related:`
  is empty in v1.
- `speckit-status` writing any file — it stays strictly read-only.
- Linking the cross-tree `docs/ai/specs/.process/` design-concept/workflow from the
  spec-MOC — that exhaust is roadmap-scoped (PRSG-004's domain).
```

### Files Generated
- [ ] `specs/prsg-003-spec-index/spec.md`

---

## Phase 2: Clarify

**When to run:** After Specify. Max 5 targeted questions per session. Seed the sessions from the design concept's Open Questions (the PRS input-contract shape, INDEX-activation timing, and the commit-message wording were the deliberate deferrals).

### Clarify Prompts

#### Session 1: Zone contract & determinism

```bash
/speckit-clarify Focus on the generated-zone contract and determinism: the exact
HTML-comment sentinel spelling for INDEX/PRS/BACKLINKS and where they're defined as
constants; the whole-zone-replace mechanism (never sed-patch); the canonical
ordering rule (normalized-ID across specs; fixed artifact precedence then path
within a spec); and the SHAPE of the repo-local committed source the PRS zone
renders from (a .process/ manifest vs. data carried in the spec-MOC body). No live
gh at generation time.
```

#### Session 2: Wiring & idempotency

```bash
/speckit-clarify Focus on wiring: speckit-status --check output (how staleness is
reported in the dashboard without writing); the autopilot phase-gate step running at
every boundary with commit-only-on-non-empty-diff and the fixed commit message; and
the inject-if-missing behavior — the fixed anchor where empty zones are inserted into
an existing version-marked spec-MOC, and proof it's idempotent.
```

#### Session 3: Codex parity & scope edges

```bash
/speckit-clarify Focus on parity and scope edges: mirroring the speckit-status and
speckit-autopilot SKILL.md changes into codex-skills/ (the generator script is a
single shared copy referenced by path — not duplicated); discovery skipping legacy
specs with no SPEC-MOC; and the enumeration boundary staying within specs/<branch>/**
(incl. its .process/) only.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Zone contract & determinism | | |
| 2 | Wiring & idempotency | | |
| 3 | Codex parity & scope edges | | |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/prsg-003-spec-index/plan.md`

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Runtime: Bash (macOS/Linux) + jq. No new dependency (constitution II; CLAUDE.md rule 2).
- Reused library: speckit-pro/tests/lib/moc-id-normalize.sh — source it and call
  moc_normalize / moc_id_match for EVERY ID join. Do not reinvent normalization.
- New script: speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh
  (sibling of reviewability-gate.sh / generate-pr-body.sh). Single shared,
  runtime-agnostic copy referenced by absolute plugin path from both speckit-status
  and speckit-autopilot (and their Codex mirrors).

## Surfaces to design
- generate-spec-index.sh: a `--check` (read-only diff) mode AND a write mode;
  sentinel constants for the three zones; whole-zone regeneration; inject-if-missing
  of empty zones into version-marked spec-MOCs at a fixed anchor; discovery limited to
  specs that carry a SPEC-MOC.md; canonical ordering.
- spec-moc-template.md: add the three empty GENERATED zones at a fixed anchor so new
  specs are born with them.
- speckit-status SKILL.md (+ codex-skills mirror): invoke the generator in --check
  mode and surface "index stale — run regen" read-only.
- speckit-autopilot references/phase-execution.md (+ codex-skills mirror): add the
  idempotent regen-and-commit-on-diff phase-gate step at every boundary (the write path).
- Tests: an L1 determinism fixture (the fixture-driven byte-stable assertion) wired
  into tests/run-all.sh next to the existing validate-moc-* lints (lines ~145-146),
  plus L4 unit tests for the generator's pure functions.

## Constraints
- The roadmap INDEX path is built but dormant (no roadmap-MOC home note exists; PRSG-004).
- The PRS zone renders from a repo-local committed source only — never `gh`.
- Stay within ~350 production LOC. Re-read docs/ai/specs/.process/PRSG-003-design-concept.md
  for any decision this prompt didn't capture.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ⏳ | Generator design, --check mode, sentinel constants, wiring |
| `research.md` | ⏳ | Repo-local PRS-source decision; reuse-vs-reinvent normalizer |
| `data-model.md` | ⏳ | Zone schemas (INDEX/PRS/BACKLINKS rows); frontmatter join keys |
| `contracts/` | ⏳ | Sentinel grammar; generator CLI contract (`--check` vs write) |
| `quickstart.md` | ⏳ | How to run the generator + interpret a staleness report |

---

## Phase 4: Domain Checklists

**Recommended domains (2):** mirror PRSG-002's choices — the risk here is identical (a script that rewrites doc files in place).

#### 1. data-integrity Checklist

Why: the generator overwrites regions of committed MOC files. A bug corrupts navigation maps or drops links. Whole-zone regen + idempotency + canonical ordering are the integrity guarantees.

```bash
/speckit-checklist data-integrity

Focus on PRSG-003 requirements:
- Whole-zone replacement never corrupts content OUTSIDE the sentinel pair.
- Re-running the generator with no source change produces a zero-byte diff (idempotent).
- Canonical ordering is stable across machines / filesystem enumeration order.
- inject-if-missing adds zones exactly once, at the fixed anchor, only to version-marked specs.
- Pay special attention to: malformed/partial sentinel pairs and files with no zones.
```

#### 2. error-handling Checklist

Why: real spec trees are messy — missing sentinels, empty PRS data, non-version-marked specs, malformed frontmatter, non-regular-file targets.

```bash
/speckit-checklist error-handling

Focus on PRSG-003 requirements:
- A spec-MOC with no zones and no marker is skipped silently (version-gating).
- Empty/absent PRS source renders an empty-but-valid PRS zone, not an error.
- Malformed frontmatter / unreadable file fails safe with an actionable message and a non-zero exit.
- --check mode never writes, even on error paths.
- Pay special attention to: exit-code contract (clean vs stale vs error) consumed by speckit-status and the autopilot gate.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| data-integrity | | | |
| error-handling | | | |
| **Total** | | | |

---

## Phase 5: Tasks

**When to run:** After checklists (all gaps resolved). Output: `specs/prsg-003-spec-index/tasks.md`

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Small, testable chunks; clear acceptance referencing FR-xxx.
- TDD: RED (failing L1 fixture / L4 unit test) before GREEN.
- Dependency order: normalizer-reuse + sentinel constants → zone renderers
  (BACKLINKS first, it's the v1-active zone; PRS renderer; dormant INDEX path)
  → inject-if-missing + template zones → status --check wiring → autopilot
  phase-gate step → Codex mirrors.
- Pair every SKILL.md edit with its codex-skills mirror task (speckit-status,
  speckit-autopilot).
- Mark parallel-safe tasks [P].

## Bound by the design concept Non-goals
Flag any task that would: populate the roadmap INDEX, write live PR/SHA data,
touch legacy non-MOC specs, build a cross-spec citation graph, or make
speckit-status write a file. Those belong to PRSG-004/009/011, not here.

## Constraints
- Tests live under speckit-pro/tests/ (L1 fixture next to validate-moc-*; L4 unit tests).
- The generator is one shared script; Codex consumes it by path (no duplicate).
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | 26 (T001–T026) |
| **Parallel Opportunities** | 8 [P]: T005∥T006, T015∥T017, T016∥T018, T019∥T020 |
| **User Stories Covered** | US1, US2 |

---

## Phase 6: Analyze

```bash
/speckit-analyze

Focus on:
1. Cross-artifact consistency across spec.md, plan.md, tasks.md, AND
   docs/ai/specs/.process/PRSG-003-design-concept.md. The design concept is the
   source of truth for scoping decisions — flag any drift.
2. Boundary integrity: no scope creep into PRSG-004 (roadmap INDEX population),
   PRSG-009 (live PR/SHA), or PRSG-011 (legacy backfill). The INDEX path must be
   present-but-dormant; the PRS renderer must read repo-local data only.
3. Contract integrity: confirm speckit-status remains read-only (--check only).
4. Coverage: every FR and both user stories have tasks; the L1 determinism fixture
   and L4 unit tests are present; Codex SKILL.md edits are paired.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| S1 | MEDIUM (scope) | T020 added a dormant INDEX zone to `roadmap-moc-template.md`, which plan.md/FR-017 never name (self-flagged "EXCEEDS plan.md") | **DROPPED.** Generator discovery is bounded to version-marked `SPEC-MOC.md` under `specs/` (FR-007) and never processes the roadmap template — an INDEX-only zone there would be orphaned/untested. Roadmap INDEX live population is PRSG-004 (FR-019). T020 → tombstone; T019 alone satisfies FR-017; 6 downstream references reconciled. |
| M1 | MEDIUM (parity) | Asymmetric Codex mirror: T018 touched Codex `SKILL.md` + `phase-execution-codex.md`, but T017 touched only the Claude reference, not the Claude `SKILL.md` (FR-020 risk not caught by parity validators) | Amended T017/T018 with a mirror-symmetry note: behavior lives in the reference file; any `SKILL.md` pointer is added on both runtimes or neither (default reference-only). |
| L1 | LOW (consistency) | plan.md D3 wrote the PRS plain-text render as shorthand, diverging from the canonical `PRSG-003 · PR#117 · abc1234` in the contract/data-model/T012 | Edited plan.md D3 to cite the canonical example string and point to the contract + data-model as the byte authority. |
| — | — | Coverage / TDD-order / Codex-pairs / contract read-only / boundary integrity audited | All 22 FR + 12 SC map to ≥1 task; T005/T006 RED before T014 GREEN; T016↔T015 & T018↔T017 paired; status read-only; PRSG-004/009/011 cleanly out of scope. No change needed. |

### Pre-Implement Confidence (G6.5 — advisory)

📊 Confidence: 0.98

- Task understanding: 0.97
- Approach clarity: 0.97
- Requirements alignment: 0.95
- Risk assessment: 1.00
- Completeness: 1.00

Composite 0.98 ≥ 0.90 threshold → G6.5 PASS (advisory). Clean Analyze
pass (0 CRITICAL / 0 HIGH); all required artifacts present and non-empty
(spec, plan, tasks, data-model, contracts, research, quickstart). The only
deduction was a minor tasks.md test-header label inconsistency (now fixed:
"until T014 GREEN").

---

## Phase 7: Implement

**When to run:** After tasks.md is analyzed (no gaps).

### Implement Prompt

```bash
/speckit-implement

## Approach: TDD-First
For each task: RED (write the failing L1 fixture / L4 unit test) → GREEN (minimum
code) → REFACTOR → VERIFY.

## Implementation Notes
- Source moc-id-normalize.sh; never reinvent the join. Reference the design concept
  Q&A log for the "why" behind each decision.
- Sentinel constants defined once; whole-zone regenerate; a missing pair skips the zone.
- Prove determinism: run the generator twice → second run yields a zero-byte diff.
- Dogfood: after wiring, the generator must produce a real BACKLINKS reachability index
  on this repo's own version-marked spec-MOCs (prsg-002, prsg-003) and the moc lints
  must stay green.
- shellcheck + bash -n clean (constitution II). Mirror speckit-status and
  speckit-autopilot SKILL.md changes into codex-skills/ and keep
  validate-codex-skills.sh green.

## Verification
- bash tests/run-all.sh  (Layers 1, 4, 5) green, including the new L1 determinism fixture.
- speckit-status reports a clean (non-stale) index after a regen; reports stale after a
  hand-edit to a source artifact.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Generator core (normalizer reuse, sentinels, zones) | T007–T014 | ✅ | 502-LOC bash+jq; reuses moc-id-normalize.sh; 3-way exit enum; atomic per-target write; commit `884faf1` |
| 2 - Template zones + inject-if-missing | T019 | ✅ | spec-moc-template zones byte-identical to generator output; commit `40c9f03` |
| 3 - status --check wiring (+ Codex mirror) | T015, T016 | ✅ | read-only freshness line; Codex mirror parity green; commits `40c9f03`/`330e82b` |
| 4 - autopilot phase-gate step (+ Codex mirror) | T017, T018 | ✅ | regen-and-commit-on-non-empty-diff at every boundary; level-symmetric mirror; commits `40c9f03`/`330e82b` |
| 5 - Tests (L1 fixture, L4) + dogfood | T003–T006, T021, T022 | ✅ | RED→GREEN; dogfooded on prsg-002+prsg-003 maps; suite wired; commits `0a63be3`/`79e7f80` |

---

## Post-Implementation Checklist

- [x] All tasks marked complete in tasks.md (25; T020 tombstoned by Analyze)
- [x] `shellcheck` + `bash -n` clean on `generate-spec-index.sh` (only SC1091 lib-sourcing info, matching sibling lints)
- [x] `bash tests/run-all.sh` green (1659/1659, incl. new L1 determinism fixture + L4)
- [x] MOC lints (`validate-moc-orphan.sh`, `validate-moc-stale-index.sh`) still green on real spec trees (prsg-002 + prsg-003)
- [x] Generator is idempotent (second run = zero diff) — verified live + empty-tree no-op (SC-012)
- [x] Codex parity: `validate-codex-skills.sh` (140/140) + `validate-codex-parity.sh` (74/74) green; `speckit-status` + `speckit-autopilot` mirrors updated
- [x] PR title is public-readable: `feat(speckit-pro): generate spec navigation maps and catch stale ones`
- [x] PR created: **#121** — https://github.com/racecraft-lab/racecraft-plugins-public/pull/121 (review-remediation loop scheduled; NOT merged — humans merge)

---

## Retrospective (#32 — FINAL)

**Outcome.** PRSG-003 shipped as PR #121: a deterministic spec-MOC navigation
generator (`generate-spec-index.sh`, ~518 LOC bash+jq) plus read-only status
wiring, autopilot phase-gate regeneration, Codex mirrors, and a live dogfood over
the prsg-002 + prsg-003 maps. All 7 phases passed their gates; final suite
1708/1708 + integration 210/210; lint clean.

**What worked.** TDD RED→GREEN held end-to-end (the generator was built to satisfy
failing tests). Empirical verification after every subagent — rather than trusting
self-reports — repeatedly paid off: it caught the GREEN gap (BACKLINKS ordering was
lexicographic, not bucket-precedence), the staleness the UAT-runbook addition
introduced, and the suite-wiring gap below. The adversarial code review found two
real defects that the test suite and gates had passed.

**What surprised us / lessons.**
1. **The reviewability "ratified exception" phrase auto-clears the diff-mode gate,
   not just the tasks-mode gate.** The diff-mode gate returns `pass: true` because
   it detects the phrase in `tasks.md` (which is in the diff) — it does not make an
   independent size judgment. The real ship-vs-split decision had to be made
   manually and documented honestly (composition: ~700 LOC code / ~1050 tests+
   fixtures / ~2850 SDD docs), anchored to the #116 precedent. *Tooling follow-up
   worth filing:* the gate conflates the two phases — a tasks-phase transition
   exception probably should NOT silently satisfy the pre-PR diff-mode gate.
2. **A new test can be created but never wired into the suite.** `test-generate-
   spec-index.sh` (49 assertions) ran green standalone but was absent from
   `run-all.sh`'s explicit layer-4 list — T022 only wired the L1 fixture. The
   tell was a suite count that didn't move (1659 → still 1659) after adding 13
   assertions. Lesson: when adding a test, wire it in AND confirm the aggregate
   count increases.
3. **Code review caught what tests + gates missed:** a non-integer `pr` in
   `prs.json` produced a corrupt row and exit 0 (a `printf '%012d'` failure outside
   the ERR trap), and a symlinked `SPEC-MOC.md` was followed and clobbered. Both
   are exactly the silent-failure modes the spec's own fail-safe FRs exist to
   prevent. Fixed test-first.
4. **Adding the UAT runbook made the dogfooded map stale** — the generator
   correctly flagged it, validating the staleness detection. A phase-gate regen is
   required after any artifact addition under a spec's tree.

**Follow-ups (all with landing places, none silent):** PRSG-004 (roadmap INDEX live
population), PRSG-009 (live PR#/SHA writing), PRSG-011 (legacy backfill); plus the
gate-conflation tooling note in lesson #1.

---

## Post-Implementation Results

### Doctor / Extension Health (#20)
`specify check`: Git, Claude Code, Codex CLI all available. Extension registry
intact — 7 enabled (verify, verify-tasks, checkpoint, retrospective,
speckit-utils, git, archive). `review` + `cleanup` not installed.

### Integration Suite (#24)
`bash tests/run-all.sh --integration` (Layer 7 replay) → **210/210 passed**,
exit 0. No regressions. Full unit/structural suite **1659/1659**.

### Reviewability Diff Gate (#26) — ship-as-one (honest exception)
`reviewability-gate.sh diff origin/main...HEAD` returns `pass: true` ONLY via the
ratified-exception phrase in tasks.md — it is NOT an independent size verdict.
Real diff: ~4464 added lines / 63 files. Composition: ~700 LOC production code
(generator + wiring) · ~1050 LOC tests + fixtures · **~2850 LOC SDD documentation
(~64%)**. Decision: **ship as one PR.** Splitting duplicates the SDD docs across
sub-specs and fragments a hard-coupled feature. Precedent: the comparable
predecessor autopilot PR (PRSG-002, #116) merged at 3858 additions / 71 files —
same profile. Size + composition stated plainly in the PR body (not behind a green
check). Full rationale: `specs/prsg-003-spec-index/tasks.md` §Reviewability Scope
Exception.

### Verify / Verify-Tasks (#21/#22)
The `verify` / `verify-tasks` SpecKit extensions register as skills, not headless
`specify` subcommands. Their intent — implementation-matches-spec and
phantom-completion detection — is covered by the Self-Review below (every `[x]`
task cross-walked to commit + passing-test evidence; no phantom completions).

### Code Review (#23)
`review` extension not installed; ran a dedicated adversarial code-review subagent
over the generator + wiring + tests instead (findings folded into the PR body /
acted on before PR open).

### Self-Review (auto-generated) (#27)

**Tests executed:** All applicable commands ran this session (2026-06-07) and
exited zero — UNIT/STRUCTURAL `bash tests/run-all.sh` → 1659/1659; INTEGRATION
`bash tests/run-all.sh --integration` → 210/210; LINT `shellcheck` + `bash -n` on
`generate-spec-index.sh` → clean (only SC1091 lib-sourcing info, matching sibling
lints). BUILD/TYPECHECK → N/A (bash + jq, no compile step). Evidence: workflow
§Implementation Progress + §Post-Implementation Results.

**Edge cases:** Every success criterion has a non-happy-path test. SC-001/SC-009
determinism + filesystem-order independence → `validate-spec-index-determinism.sh`
(runs the generator twice; asserts byte-identical + order-independent). FR-015/
FR-021 stale≠error + trap-disarm-before-deliberate-exit → L4 (a)/(c). FR-012
`--check` writes nothing incl. error path → L4 (b). FR-009 missing-one-pair skip →
L4 (d). FR-022 unbalanced/duplicated pair fail-safe exit 2, no partial write → L4
(e). FR-016/D6 atomic per-target write (no half-write across maps) → L4 (f).
FR-011 vs FR-016 PRS absent/empty vs malformed → L4 (g). FR-008/FR-017 template-
born ≡ inject-if-missing byte-identical → L4 (h) + the T019 `--check` exit-0
byte-identity proof on the real template. FR-005 canonical ordering → L4 (i) +
independent ground-truth inspection. SC-012 empty-tree no-op → verified manually
(no-`specs/` tree and non-version-marked legacy → exit 0, nothing written). No
`[edge-case-gap]` markers.

**Requirements matched:** All 22 FR (FR-001…FR-022) and 12 SC (SC-001…SC-012) map
to ≥1 task (confirmed at Analyze). US1 = T005–T014, US2 = T015–T018, cross-cutting
T019/T021/T022. Every `[x]` task has implementation evidence (6 Phase-7 commits +
passing tests). T020 dropped by Analyze (roadmap-template INDEX zone → PRSG-004);
FR-017 still covered by T019, FR-019 by T013. No orphans in either direction.

**Follow-up:** All deferrals have explicit landing places (no silent TODOs):
roadmap-level INDEX live population → PRSG-004; live slice→PR#→merged-SHA writing →
PRSG-009; backfilling zones into legacy specs lacking a map → PRSG-011; inbound
cross-spec citation graph → future (`related:` empty in v1). The in-scope cross-spec
edit — populating prsg-002's already-merged map with the zones its body said would
come "from a later spec" — is surfaced in the PR body, not a surprise diff.

### Post-Merge Integration (#118)

After the branch opened, `main` merged a change (#118) that relocated the whole
test suite out of the plugin directory to a repo-root sibling (`tests/speckit-pro/`),
because anything under `speckit-pro/` ships to plugin consumers. That moved the two
canonical MOC libs (`moc-id-normalize.sh`, `moc-frontmatter.sh`) out of the shipped
plugin — but PRSG-003's generator ships inside the plugin and sourced them by the
old `tests/lib/` path, so once `main` merged in, the shipped generator would fail
for consumers with a missing-file error.

Resolution: the two libs are now genuine runtime dependencies of a shipped script,
so they belong in the shipped tree. They moved (one canonical copy, git-tracked
rename — no duplication, FR-004 preserved) to
`speckit-pro/skills/speckit-autopilot/scripts/lib/`, co-located with the generator.
The generator, the two PRSG-002 lints, the normalizer's own unit test, and this
spec's Layer-4 test all source the libs from that one shipped home; `assertions.sh`
(test-only) stays in `tests/speckit-pro/lib/`. The generator contract was updated to
match.

Verification: full suite `bash tests/speckit-pro/run-all.sh` → 1712/1712; plus a
plugin-shaped check — copy `speckit-pro/` alone (no test tree anywhere) and run its
generator `--check` against fixture specs → libs resolve, exit 0, zero missing-file
errors (the actual consumer failure mode, proven fixed).

---

## Project Structure Reference

```
speckit-pro/
├── skills/
│   ├── speckit-autopilot/scripts/generate-spec-index.sh   # NEW — shared generator
│   ├── speckit-status/SKILL.md                            # EDIT — --check wiring
│   ├── speckit-autopilot/references/phase-execution.md    # EDIT — phase-gate regen step
│   └── speckit-coach/templates/spec-moc-template.md       # EDIT — empty zones at anchor
├── codex-skills/
│   ├── speckit-status/SKILL.md                            # MIRROR
│   └── speckit-autopilot/...                              # MIRROR
└── tests/
    ├── lib/moc-id-normalize.sh                            # REUSE (PRSG-002)
    ├── layer1-structural/  (determinism fixture, wired in run-all.sh)
    └── layer4-scripts/     (generator unit tests)
```

---

Populated from the PRSG-003 Grill Me interview (2026-06-06). Run with:
`/speckit-pro:speckit-autopilot docs/ai/specs/.process/PRSG-003-workflow.md`
