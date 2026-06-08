# SpecKit Workflow: PRSG-004 — Roadmap-MOC home note from PRD + coach the two-zone structure

**Template Version**: 1.0.0
**Created**: 2026-06-08
**Purpose**: Autopilot-ready workflow for PRSG-004. Prompts below are pre-populated from the Grill Me interview; `/speckit-pro:speckit-autopilot` executes them phase by phase.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log (9 questions), Goals,
Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/PRSG-004-design-concept.md
```

Re-read it before each phase if you need to disambiguate a prompt. The
design concept doc is the **source of truth** for every scoping decision
captured during this spec's grill-me session; if a downstream artifact
contradicts it, the downstream artifact is wrong unless an explicit
revision note says otherwise.

> **Note:** Grill Me is human-in-the-loop only. Once autopilot begins,
> clarifications happen via `/speckit-clarify` + the consensus protocol —
> never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | 22 FRs, 3 US, 13 acceptance scenarios, 8 SC + L4 deviation; 0 markers. G1 pass. |
| Clarify | `/speckit-clarify` | 🔄 In Progress | Design converged; only the recorded Open Questions need clarifying |
| Plan | `/speckit-plan` | ⏳ Pending | |
| Checklist | `/speckit-checklist` | ⏳ Pending | Domains: documentation-quality, error-handling |
| Tasks | `/speckit-tasks` | ⏳ Pending | |
| Analyze | `/speckit-analyze` | ⏳ Pending | |
| Implement | `/speckit-implement` | ⏳ Pending | |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | User stories clear, no `[NEEDS CLARIFICATION]` left for resolved branches |
| G2 | After Clarify | The 4 recorded Open Questions resolved (or explicitly deferred with defaults) |
| G3 | After Plan | Generator-extension approach approved; PRSG-003 byte-contract regression guard in place; constitution gates pass |
| G4 | After Checklist | All `[Gap]` markers addressed |
| G5 | After Tasks | Every FR + user story has a task; Codex-mirror tasks present |
| G6 | After Analyze | No `CRITICAL`; design-concept drift checked |
| G7 | After Each Implementation Phase | L1/L4 green in CI; L2/L3/L8 recorded passing before merge |

---

## Prerequisites

### Constitution Validation

Verify alignment with `.specify/memory/constitution.md` before G1:

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| II. Script Safety | The `generate-spec-index.sh` extension keeps `set -euo pipefail`, passes `bash -n`, stays `chmod +x` | `bash -n speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh` |
| IV. Test Coverage Before Merge | New deterministic logic (activated `render_index`) has a Layer-4 determinism fixture; skill changes pass Layer-1 | `bash tests/speckit-pro/run-all.sh --layer 1 && --layer 4` |
| V. Conventional Commits | PR title `feat(speckit-pro): …`, plain-English, public-readable | `validate-pr-title` CI check |
| VI. KISS / YAGNI | Extend the generator (don't refactor into a new lib); advisory cap (don't build a blocker) | Code review against design concept Non-goals |
| I. Plugin Structure | Codex mirrors for `speckit-prd` + `speckit-coach` stay in parity | `validate-codex-skills.sh` (L1) + L8 |

**Constitution Check:** ✅ (initial, pre-G1) — PROJECT_COMMANDS are N/A for this bash/markdown plugin repo, so the constitution gate maps to the bash test suite: baseline `bash tests/speckit-pro/run-all.sh` green (L1 861/861, L4 851/851, L5 190/190) before any phase work; restored a stale scaffold-installed reviewability preset (commit 6d733aa) to get there. Script Safety / Test-Coverage / KISS / Codex-parity principles re-verified at G7.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | PRSG-004 |
| **Name** | Roadmap-MOC home note from PRD + coach the two-zone structure |
| **Branch** | `prsg-004-roadmap-moc-home-note` |
| **Dependencies** | PRSG-002 (✅ MOC templates + frontmatter join-key contract), PRSG-003 (✅ `generate-spec-index.sh` + dormant `render_index()` stub) |
| **Enables** | Completes the Phase 2 navigation spine (roadmap-level home note). PRSG-011 Tier-0 reuses this generator for backfill but is not blocked by PRSG-004. |
| **Priority** | P2 |

### Success Criteria Summary

- [ ] `speckit-prd` emits a **third** artifact, `docs/ai/specs/<slug>-roadmap-MOC.md`, alongside the PRD and technical-roadmap.
- [ ] The home note has a **curated epics zone** (auto-derived from the roadmap's phase grouping + one-line advisory "Why" per epic) and a **sentinel-bounded GENERATED INDEX zone**.
- [ ] The GENERATED INDEX is produced by **activating `render_index()`** in `generate-spec-index.sh`; each row is `- [<spec_id>](rel/SPEC-MOC.md) · <status>`, normalized-ID ascending, fields read from SPEC-MOC frontmatter.
- [ ] The **spec-MOC code path stays byte-identical** — PRSG-003's contract fixtures (`specs/prsg-003-spec-index/contracts/`) pass unchanged.
- [ ] `prd` prints a **one-line advisory** when epics exceed ~10; it still writes the file (no block).
- [ ] `speckit-coach` **teaches** the curated/generated two-zone split and the cap guardrail.
- [ ] **New-roadmaps-only** — no backfill of existing roadmaps (that is PRSG-011 Tier-0).
- [ ] Codex mirrors for `speckit-prd` and `speckit-coach` updated in the same spec; the generator stays a single shared copy referenced by path.
- [ ] Tests **L1, L2, L3, L4, L8** recorded passing before merge (L4 is a deliberate addition to the roadmap's L1/L2/L3/L8 table — see Q8).

---

## Phase 1: Specify

**Focus:** WHAT and WHY. Output: `specs/prsg-004-roadmap-moc-home-note/spec.md`

### Specify Prompt

```bash
/speckit-specify

## Feature: Roadmap-MOC home note from PRD + coach the two-zone structure (PRSG-004)

### Problem Statement
A decomposed project scatters its specs across the technical-roadmap and per-spec
SPEC-MOC.md files, so there is no single navigable "home" for the whole spec tree.
PRSG-002 shipped the MOC templates and PRSG-003 the per-spec index generator (with a
deliberately dormant render_index() stub), but the roadmap-level home note — the one
map that makes decomposition add traceability instead of cognitive load — does not
exist yet. PRSG-004 fills exactly that gap.

### Users
Maintainers and contributors navigating a multi-spec project; the speckit-prd author
producing a new PRD + roadmap.

### User Stories
[US1] speckit-prd emits a roadmap-MOC home note. When speckit-prd authors a new PRD and
technical-roadmap, it ALSO writes docs/ai/specs/<slug>-roadmap-MOC.md containing
(a) a human-curated epics zone auto-derived from the roadmap's phase/tier grouping with
a one-line advisory "Why" per epic, and (b) a sentinel-bounded GENERATED INDEX zone.
It prints a one-line advisory if the epic count exceeds ~10, but still writes the file.

[US2] speckit-coach teaches the two-zone structure. speckit-coach explains the
curated-vs-generated two-zone split, that the generated zone is regenerated (never
hand-edited), and the "cap epics below ~10" guardrail.

[US3 — enabling] Activate render_index() in generate-spec-index.sh so the home note's
GENERATED INDEX zone is produced deterministically (link + status per spec, normalized-ID
order), keeping the existing per-spec-MOC path byte-identical.

### Constraints
- Separate home-note file (NOT zones injected into the prose technical-roadmap).
- File path convention: docs/ai/specs/<slug>-roadmap-MOC.md.
- INDEX rows: `- [<spec_id>](rel/SPEC-MOC.md) · <status>`, normalized-ID ascending, read
  from each SPEC-MOC's PRSG-002 frontmatter via the existing moc-frontmatter lib. Relative
  []() links only — never [[wikilinks]].
- The relative link from the home note to a spec-MOC resolves as
  ../../../specs/<dir>/SPEC-MOC.md (home note in docs/ai/specs/, spec tree in repo-root specs/).
- Curated zone is auto-derived from roadmap phases; ZERO new questions in the prd interview.
- The cap is advisory (warn), never a block or CI lint.
- Codex parity mandatory for speckit-prd + speckit-coach; the generator is single-copy by path.

### Out of Scope
- Backfilling existing/legacy roadmaps (new-roadmaps-only; PRSG-011 Tier-0 owns backfill).
- Changing spec-MOC `up:`, the spec-MOC template, or scaffold-spec (PRSG-002 territory; the
  home note is a downward index, cross-linked with the roadmap — see Q9).
- A new generate-roadmap-moc.sh script or a lib/moc-zones.sh extraction refactor (extend the
  existing generator — Q3).
- Table/dashboard rendering or H1-parsing in the INDEX (link + status only — Q4).
```

### SpecKit Traceability Markers
Use `[US1]`/`[US2]`/`[US3]`, `[FR-xxx]`, `[NEEDS CLARIFICATION]`, `[P]`, `[Gap]` in spec.md.

---

## Phase 2: Clarify

The design converged in grill-me; only the recorded **Open Questions** need clarifying.
Keep to ≤5 questions per session.

### Clarify Prompts

#### Session 1: Generator + emission mechanics

```bash
/speckit-clarify Focus on the open questions recorded in the design concept doc:
(1) How does the extended generate-spec-index.sh main() DISCOVER the home note —
    default: filename glob docs/ai/specs/*-roadmap-MOC.md gated on the PRSG-002 frontmatter
    contract (moc_is_gated + structureVersion). Confirm or refine.
(2) The home note's OWN up: frontmatter value — default: points at the technical-roadmap
    (mutual cross-link); confirm the roadmap-side link is a one-line link prd adds.
(3) No-phases fallback for the curated scaffold — default: a single "Specs" epic + advisory note.
```

#### Session 2: Coach teaching surface

```bash
/speckit-clarify Focus on documentation placement:
(4) Where speckit-coach teaches the two-zone split — default: a new references/ section, not
    inline in SKILL.md. Confirm the reference file name/home and how the SKILL.md description
    surface changes (this drives the L2 trigger eval).
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Generator + emission | 3 | |
| 2 | Coach teaching surface | 1 | |

---

## Phase 3: Plan

**Output:** `specs/prsg-004-roadmap-moc-home-note/plan.md`

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Skills: Markdown SKILL.md (speckit-prd, speckit-coach) + their codex-skills/ mirrors.
- Deterministic logic: bash + jq only (scripts-first mandate). Extend
  speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh — a single shared,
  runtime-agnostic copy. Reuse lib/moc-frontmatter.sh + lib/moc-id-normalize.sh.
- Tests: tests/speckit-pro/ (Layer 1 structural, Layer 4 script determinism); Layer 2/3/8
  developer-local via claude -p + skill-creator.

## Architecture Notes (from the design concept — treat as decided)
- Extend generate-spec-index.sh: give render_index() a real body for the roadmap-MOC case and
  add a home-note discovery + regeneration path to main(). The spec-MOC path MUST stay
  byte-identical — re-run PRSG-003's contract fixtures as a regression guard. The roadmap-MOC
  INDEX is an ADDITIVE path with its own L4 fixture.
- render_index output contract: one line per in-scope spec, `- [<spec_id>](rel/SPEC-MOC.md) · <status>`,
  normalized-ID ascending, fields from SPEC-MOC frontmatter; whole-zone regen; U+00B7 separator
  consistent with render_prs.
- speckit-prd: after writing the technical-roadmap, derive epics from its phase/tier grouping,
  write docs/ai/specs/<slug>-roadmap-MOC.md from the PRSG-002 roadmap-moc-template (curated zone
  pre-filled + GENERATED INDEX sentinels), then invoke the generator to fill the INDEX. Print a
  one-line advisory if epics > ~10. Add the home note to the prd Output Contract (now 3 files).
- speckit-coach: teach the two-zone split + the cap guardrail (new references section).
- Codex parity: mirror the prd emit step + coach teaching in codex-skills/; generator stays
  single-copy referenced by path.

## Constraints
- KISS/YAGNI: no new script, no lib extraction, no enforced block (constitution VI).
- New-roadmaps-only; no backfill (PRSG-011 owns it).
- Budget ~200 production LOC.

## Reviewability
Reuse the roadmap's per-SPEC budget line; reviewability preset already installed.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ⏳ | Generator-extension design + emission flow |
| `research.md` | ⏳ | Only if a discovery-mechanism decision needs rationale |
| `data-model.md` | ⏳ | Likely N/A (no new data entities) |
| `contracts/` | ⏳ | render_index roadmap-MOC INDEX output contract (mirrors PRSG-003 contract style) |
| `quickstart.md` | ⏳ | Optional |

---

## Phase 4: Domain Checklists

**Target domains (2):**

#### 1. documentation-quality Checklist

Why: PRSG-004 is mostly a skill-prose + template-emission change; the home note's structure,
the curated/generated split, and coach's teaching must be unambiguous and consistent.

```bash
/speckit-checklist documentation-quality

Focus on PRSG-004 requirements:
- The roadmap-moc-template's two zones are clearly delineated (curated vs sentinel-bounded).
- The prd emit step and the coach teaching describe the SAME two-zone model with no drift.
- Relative-link rules (never wikilinks) and the ../../../specs/<dir>/SPEC-MOC.md path are stated.
- Pay special attention to: the Codex mirrors saying exactly what the Claude variants say.
```

#### 2. error-handling Checklist

Why: the activated render_index path and home-note discovery must fail safe like the rest of
generate-spec-index.sh (exit 2 on malformed input, never a partial write).

```bash
/speckit-checklist error-handling

Focus on PRSG-004 requirements:
- Home-note discovery: absent home note => clean no-op; malformed/unbalanced markers => exit 2.
- A SPEC-MOC missing the status/spec_id frontmatter field => defined behavior (skip vs fail-safe).
- render_index stays deterministic (same committed inputs => byte-identical INDEX).
- Pay special attention to: the spec-MOC path remaining byte-identical (no regression to PRSG-003).
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| documentation-quality | | | |
| error-handling | | | |
| **Total** | | | |

---

## Phase 5: Tasks

**Output:** `specs/prsg-004-roadmap-moc-home-note/tasks.md`

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Small, testable chunks; acceptance criteria reference FR-xxx.
- Organize by user story (US1 prd emit / US2 coach teach / US3 generator activation).
- Mark parallel-safe tasks [P]. The generator activation (US3) is the dependency for US1's
  INDEX fill, so order US3 before the US1 emit-and-fill task.
- EVERY skill change carries its Codex-mirror task in the same story (Codex parity is a
  deliverable, not a follow-up).

## Implementation Phases
1. Foundation: activate render_index() in generate-spec-index.sh + home-note discovery in main()
   (+ L4 determinism fixture; re-run PRSG-003 contract fixtures as regression guard).
2. US1: speckit-prd emits the home note (curated zone from phases + advisory Why + GENERATED
   sentinels), invokes the generator to fill the INDEX, prints the >~10 advisory, updates the
   prd Output Contract; mirror in codex-skills/speckit-prd. (+ L2/L3)
3. US2: speckit-coach teaches the two-zone split + cap; mirror in codex-skills/speckit-coach. (+ L2/L3)
4. Polish: L1 structural (template + scoping), L8 parity fixtures for both skills, run
   speckit-skill-reviewer as a pre-commit gate.

## Constraints
- bash+jq only for the generator; no new script, no lib extraction.
- Production LOC budget ~200; relocate process artifacts to .process/ (PRSG-001 contract).
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | |
| **Phases** | |
| **Parallel Opportunities** | |
| **User Stories Covered** | |

---

## Phase 6: Analyze

```bash
/speckit-analyze

Focus on:
1. Design-concept drift — every spec/plan/tasks decision matches PRSG-004-design-concept.md
   (separate file, docs/ai/specs/<slug>-roadmap-MOC.md path, extend-not-new-script, link+status
   INDEX, auto-derived curated zone, advisory cap, new-roadmaps-only, up:-unchanged, L1/L2/L3/L4/L8).
2. Coverage — every FR + US1/US2/US3 has a task; each mirrored-skill change has a Codex task.
3. Regression guard — a task re-runs PRSG-003's contract fixtures to prove the spec-MOC path is
   byte-identical.
4. Constitution — Script Safety (II), Test Coverage (IV), KISS/YAGNI (VI), Codex parity (I).
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| | | | |

---

## Phase 7: Implement

```bash
/speckit-implement

## Approach: TDD-First (RED → GREEN → REFACTOR → VERIFY)

### Pre-Implementation Setup
1. Confirm you are in the worktree on branch prsg-004-roadmap-moc-home-note.
2. Baseline green: `bash tests/speckit-pro/run-all.sh` (Layers 1,4,5) passes before changes.
3. Capture PRSG-003 contract-fixture output BEFORE touching generate-spec-index.sh, to diff after.

### Implementation Notes
- Foundation first: write the L4 determinism fixture for the roadmap-MOC INDEX (RED), then
  activate render_index() + home-note discovery (GREEN). Re-run PRSG-003's fixtures — they MUST
  be byte-identical (REFACTOR only if green).
- Keep the spec-MOC zone-set (INDEX/PRS/BACKLINKS) unchanged; the roadmap-MOC needs only INDEX.
- Mirror every speckit-prd / speckit-coach edit into codex-skills/ in the SAME task; run
  speckit-skill-reviewer before commit.
- Reserve LLM reasoning for the curated "Why" advisory text only — all index/zone logic is the script.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Foundation (generator) | | | |
| 2 - US1 (prd emit) | | | |
| 3 - US2 (coach teach) | | | |
| 4 - Polish (L1/L8/parity) | | | |

---

## Post-Implementation Checklist

- [ ] All tasks complete in tasks.md
- [ ] `bash tests/speckit-pro/run-all.sh` (L1/4/5) green
- [ ] Layer 4 determinism fixture for the roadmap-MOC INDEX passes; PRSG-003 contract fixtures unchanged
- [ ] Layer 2 + Layer 3 evals recorded passing (developer-local, `claude -p`)
- [ ] Layer 8 parity green for speckit-prd + speckit-coach; `validate-codex-skills.sh` green
- [ ] `speckit-skill-reviewer` run on both changed SKILL.md files
- [ ] PR title `feat(speckit-pro): …`, plain-English, public-readable
- [ ] PR created (not merged — humans merge)

---

## Project Structure Reference

```
racecraft-plugins-public/
├── speckit-pro/
│   ├── skills/
│   │   ├── speckit-prd/SKILL.md              # US1: emit the home note
│   │   ├── speckit-coach/
│   │   │   ├── SKILL.md                       # US2: teach the two-zone split
│   │   │   ├── references/                    # US2: new two-zone guide section
│   │   │   └── templates/roadmap-moc-template.md  # PRSG-002 template the home note fills
│   │   └── speckit-autopilot/scripts/
│   │       ├── generate-spec-index.sh         # US3: activate render_index()
│   │       └── lib/{moc-frontmatter.sh, moc-id-normalize.sh}
│   └── codex-skills/{speckit-prd, speckit-coach}/SKILL.md  # parity mirrors
├── tests/speckit-pro/{layer1-structural, layer4-*}/        # L1 + L4 fixtures
└── docs/ai/specs/<slug>-roadmap-MOC.md         # the emitted artifact (in consumer projects)
```

---

Populated from the PRSG-004 Grill Me interview (2026-06-08). Source of truth for scoping
decisions: `docs/ai/specs/.process/PRSG-004-design-concept.md`.
