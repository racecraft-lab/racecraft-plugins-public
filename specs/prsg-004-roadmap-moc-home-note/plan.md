# Implementation Plan: Roadmap-MOC home note from PRD + coach the two-zone structure

**Branch**: `prsg-004-roadmap-moc-home-note` | **Date**: 2026-06-08 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/prsg-004-roadmap-moc-home-note/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

`speckit-prd` gains a third output artifact — a roadmap-MOC "home note" at
`docs/ai/specs/<slug>-roadmap-MOC.md` — emitted only when it authors a fresh PRD +
technical-roadmap. The home note carries two zones: a **human-curated epics zone**
(auto-scaffolded from the roadmap's existing phase/tier grouping, zero new interview
questions) and a **sentinel-bounded GENERATED INDEX zone**. The INDEX is filled
deterministically by activating the deliberately dormant `render_index()` in the single
shared `generate-spec-index.sh`, which already runs against every spec-MOC's
present-but-empty INDEX zone today. Activation is **context-scoped**: the discovery site
(`main()`) knows whether a target is the home note or a spec-MOC and threads that signal
in, so the repo-wide INDEX render applies **only** to the home note while every spec-MOC
INDEX continues to render empty — keeping the per-spec-MOC code path byte-identical so the
pinned PRSG-003 contracts stay green. `speckit-coach` teaches the curated-vs-generated
two-zone split and the advisory "cap epics below ~10" guardrail. Codex parity is mandatory
for both skills; the generator stays a single shared copy referenced by path.

## Technical Context

**Language/Version**: Bash (macOS/Linux, bash 3.2-compatible per the existing libs) + `jq`
for any JSON; Markdown for the SKILL.md skill prose and the coach reference doc. No language
runtime, no compiled artifact.

**Primary Dependencies**: The existing single shared generator
`speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh` and its co-located
libs `lib/moc-frontmatter.sh` (the total/safe `moc_frontmatter_field` + `moc_is_gated`
version gate) and `lib/moc-id-normalize.sh` (`moc_normalize` for ID ordering). The PRSG-002
`roadmap-moc-template.md` (the shape `speckit-prd` emits from). No new dependency, no new
script, no library extraction (FR-021, constitution VI).

**Storage**: N/A — pure functions of committed files on disk. The home note and spec-MOCs
are Markdown files in the working tree; no database, no network, no `gh`.

**Testing**: The repository has no language test framework. Verification is the bash test
layers run from the repo root: `bash tests/speckit-pro/run-all.sh` (Layers 1, 4, 5). The
spec adopts the final set **L1, L2, L3, L4, L8** (a deliberate, adjudicated deviation from
the roadmap catalog's terse "Tests: L1" — see spec.md "Test Coverage Note"). The **new
Layer-4 determinism fixture is the unit test** for the activated `render_index` home-note
path (SC-004 / SC-005). Layers 2/3/8 are developer-local AI evals (`claude -p` +
`skill-creator`).

**Target Platform**: The speckit-pro plugin itself — consumed by Claude Code and Codex CLI
installs of the plugin. The generator is runtime-agnostic and invoked by path.

**Project Type**: Claude Code plugin marketplace (skill prose + shared bash tooling). This is
the speckit-pro plugin SOURCE repo, not a language application. No build/typecheck/lint
framework; `PROJECT_COMMANDS` are N/A.

**Performance Goals**: N/A — the generator runs over a handful of spec dirs at phase
boundaries; determinism and idempotence (zero-byte second-run diff) are the only
"performance" constraints (SC-004).

**Constraints**: Determinism (no network, no `gh`, no nondeterministic input — pure function
of committed files). The per-spec-MOC code path MUST remain byte-identical (SC-005 / FR-018;
the PRSG-003 contracts in `specs/prsg-003-spec-index/contracts/` are the pinned regression
guard). New-roadmaps-only; no backfill (PRSG-011 owns it). ~200 production-LOC budget.
KISS/YAGNI per constitution VI: no new script, no lib extraction, no enforced block.

**Scale/Scope**: ~6 production files; ~200 reviewable production LOC. The INDEX is repo-wide
over all gated specs under a single roadmap (PRSG-004 assumes one roadmap; per-roadmap
scoping for coexisting roadmaps is deferred to PRSG-011).

**Reviewability Budget**: Primary surface = **docs/process** (the `speckit-prd` +
`speckit-coach` skill prose, including their Codex mirrors, plus the coach reference doc).
Secondary surface = **harness/adapter** (the additive `render_index` body + `main()`
home-note discovery in the single shared generator script, and the template's empty INDEX
pair). Projected reviewable production LOC: **~200** (per the roadmap per-SPEC catalog
budget). Projected production files: **~6**. Projected total files: **~9** (production +
the L4 fixture/contract + the L2 eval cases). **Budget result: within budget** (well under
the 400-LOC / 6-production-file / 15-total-file warn thresholds and the 800/8/25 block
thresholds; exactly one primary surface). **Split decision: remains one spec** — US1/US2/US3
are tightly coupled around a single artifact (the home note) and a single generator
activation; the curated zone, the coaching of it, and the INDEX renderer that fills it churn
the same files and are not independently shippable as value.

## Declared File Operations

The plan-phase reviewability estimator (`estimate-reviewable-loc.sh`) parses this
block to project the slice's production-LOC footprint before `tasks.md` exists.
Production files only (the L4 fixture, the new contract doc, and the L2 eval cases
live in the test-plan narrative below, not in this estimator block — consistent with
the spec's "production ~5-6 vs total ~7-9" split).

- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh
- MODIFIED speckit-pro/skills/speckit-coach/templates/roadmap-moc-template.md
- MODIFIED speckit-pro/skills/speckit-prd/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-prd/SKILL.md
- MODIFIED speckit-pro/skills/speckit-coach/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-coach/SKILL.md
- NEW speckit-pro/skills/speckit-coach/references/roadmap-moc-guide.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution v1.1.0 — evaluated against all six principles:

- **I. Plugin Structure Compliance** — PASS. No new plugin, no manifest change. The new
  coach reference doc lives under the existing `skills/speckit-coach/references/` tree; the
  modified generator stays under `skills/speckit-autopilot/scripts/`. Quality gate: Layer 1
  structural validation (`bash tests/speckit-pro/run-all.sh --layer 1`), including
  `validate-codex-skills.sh` for the Codex mirrors.
- **II. Script Safety** — PASS. The generator already begins with `#!/usr/bin/env bash` +
  `set -euo pipefail` and carries the `set -E` ERR-trap → exit-2 discipline; the additive
  `render_index` body and `main()` discovery follow the same total/quoted/guarded style and
  reuse the bash-3.2-safe libs. No new script introduced. Quality gate: `bash -n` +
  `validate-scripts.sh`.
- **III. Semantic Versioning** — PASS / N/A. No manual version edit; release-please bumps
  `plugin.json` on the next release PR from the `feat(speckit-pro):` commit.
- **IV. Test Coverage Before Merge** — PASS. The modified generator gets a new Layer-4
  determinism fixture (the home-note INDEX path) added to the existing
  `tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh` (or a sibling), and the
  existing PRSG-003 cases stay green as the byte-identical regression guard. Skill-prose and
  template changes are covered by Layer 1 + the Codex-parity Layer 1 check. Quality gate:
  `bash tests/speckit-pro/run-all.sh`.
- **V. Conventional Commits** — PASS. Landed as `feat(speckit-pro): …` so release-please
  promotes it; PR title plain-English per the public-readability rule.
- **VI. KISS, Simplicity & YAGNI** — PASS. The design extends the existing generator in
  place (no new `generate-roadmap-moc.sh`, no `lib/moc-zones.sh` extraction), reuses the
  frontmatter accessor / ID-normalizer / sentinel framing / whole-zone regen / atomic write,
  and adds the home note to the SAME PASS-1/PASS-2 arrays so the diff / `--check` / atomic
  write / idempotence machinery covers it with zero new code. The only genuinely new logic
  is the `render_index` home-note body. No speculative flexibility, no enforced block (the
  epic cap is advisory only). Master-plan entry exists (the PR-Size Governance roadmap,
  PRSG-004). Quality gate: plan + code review.

**No constitution violations** → Complexity Tracking table left empty.

For all specs, the generated plan MUST also define:

- **Primary / secondary review surfaces**: Primary = docs/process (the two skills' prose +
  Codex mirrors + the new coach reference). Secondary = harness/adapter (the additive
  `render_index` + `main()` discovery in the single shared generator, and the template's
  empty INDEX pair). Exactly one primary surface (the Constitution Check blocks on more than
  one primary — satisfied).
- **Within the reviewability budget?** Yes. ~200 reviewable LOC, ~6 production files, ~9
  total files, one primary surface — all under the warn thresholds (400 LOC / 6 files / 15
  total / one primary) and far under the block thresholds (800 / 8 / 25 / one primary). No
  split exception needed.
- **Split decision**: Remains one spec (see Reviewability Budget above). No deferred-work
  split; the only out-of-scope follow-ups are PRSG-011 (navigation backfill onto legacy
  roadmaps + per-roadmap INDEX scoping) — named, not split out of this spec.
- **PR review packet source**: The PR description MUST include what changed, why, non-goals,
  review order (start with the generator's `render_index` branch + the new contract, then the
  L4 fixture, then the prd emit step, then the coach teaching), scope budget (~200 LOC, one
  primary surface), traceability (each FR/SC mapped to changed files + verification), verification
  evidence (`bash tests/speckit-pro/run-all.sh` green incl. the new L4 fixture; PRSG-003 cases
  unchanged), known gaps (single-roadmap INDEX scope; backfill deferred to PRSG-011; prd MUST pass the
  consumer repo root positionally when invoking the generator, since its default `REPO_ROOT`
  is the plugin's parent — see research.md "Residual risk 2"), and
  rollback/flag notes (revert is file-local; no feature flag — the epic cap is advisory, the
  home-note path is additive and new-roadmaps-only).

## Project Structure

### Documentation (this feature)

```text
specs/prsg-004-roadmap-moc-home-note/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── roadmap-moc-index.md   # The roadmap-MOC INDEX output contract (mirrors PRSG-003 style)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
speckit-pro/skills/speckit-autopilot/scripts/
├── generate-spec-index.sh           # MODIFIED — activate render_index for the home note;
│                                     #   add home-note discovery to main(); spec-MOC path
│                                     #   stays byte-identical (additive 4th param defaulting
│                                     #   to empty output)
└── lib/
    ├── moc-frontmatter.sh            # REUSED unchanged — moc_frontmatter_field, moc_is_gated
    └── moc-id-normalize.sh           # REUSED unchanged — moc_normalize

speckit-pro/skills/speckit-coach/
├── templates/roadmap-moc-template.md # MODIFIED — add the empty GENERATED:INDEX sentinel pair
│                                      #   (the shape prd emits from); curated-zone intro
├── references/roadmap-moc-guide.md   # NEW — two-zone split + cap-epics guardrail teaching
└── SKILL.md                          # MODIFIED — description keyword cluster + routing-table
                                       #   row + References-list entry

speckit-pro/skills/speckit-prd/SKILL.md          # MODIFIED — emit the home note (3rd artifact);
                                                  #   derive curated zone from phases; advisory
                                                  #   if epics > ~10; Output Contract now 3 files
speckit-pro/codex-skills/speckit-prd/SKILL.md    # MODIFIED — mirror the emit step (parity)
speckit-pro/codex-skills/speckit-coach/SKILL.md  # MODIFIED — mirror the teaching surface +
                                                  #   description cluster (links to the shared
                                                  #   references tree; no duplicate doc)

tests/speckit-pro/                                # (test tree — does NOT ship to consumers)
├── layer4-scripts/test-generate-spec-index.sh    # MODIFIED — add the home-note INDEX cases
│                                                  #   (existing PRSG-003 cases stay green)
├── layer1-structural/fixtures/spec-index/<new>/   # NEW fixture REPO_ROOT: docs/ai/specs/
│                                                  #   <slug>-roadmap-MOC.md + several
│                                                  #   specs/*/SPEC-MOC.md (varied status)
├── layer2-trigger/.../speckit-coach-trigger.json  # MODIFIED — new roadmap-MOC-home-note case
└── layer2-trigger/.../codex-evals/...-trigger.json# MODIFIED — Codex mirror eval case
```

**Structure Decision**: This is a plugin-source repo, not a `src/`-tree application. The
production change spans two skill prose surfaces (`speckit-prd`, `speckit-coach`) with their
Codex mirrors, one shared bash generator, and one template — all in their existing
directories. The new artifact is a single coach reference doc. Tests live at the repo root
under `tests/speckit-pro/` (a sibling of the plugin, never shipped to consumers). No new
top-level directories are created.

## Complexity Tracking

> No constitution violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none)    | —          | —                                    |
