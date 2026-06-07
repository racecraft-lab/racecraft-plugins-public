# Implementation Plan: Vertical-slice sizing heuristics in PRD/grill-me (PRSG-005)

**Branch**: `prsg-005-slice-sizing-heuristics` | **Date**: 2026-06-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/prsg-005-slice-sizing-heuristics/spec.md`

## Summary

Bake SPIDR + INVEST + vertical-slicing into the two scoping skills so the SPEC catalog is
born PR-sized. `speckit-prd` decomposes an idea into a catalog of thin vertical slices and
populates each entry's existing `Budget: ~N LOC` line from a deterministic estimator;
`grill-me` gains a slice-sizing branch that runs the same estimator on a single spec and,
when over the documented ceiling or horizontally sliced, asks a split question and records
the chosen split in the Design Concept doc. The sizing math lives in one shared,
runtime-agnostic bash+jq script (`estimate-spec-size.sh`); the SPIDR/INVEST/vertical-slicing
guidance lives in one shared reference doc (`slicing-heuristics.md`); both are invoked/linked
by all four skill surfaces (2 Claude Code + 2 Codex). The capability is **advisory-only** — it
never blocks, gates, or emits exit-code/threshold logic. The ~400-LOC ceiling is a single
documented constant, shared with PRSG-006 by documentation only (not a consumed artifact).

## Technical Context

**Language/Version**: Bash (POSIX-compatible `#!/usr/bin/env bash`, macOS/Linux) + `jq` for JSON; Markdown skill prose. No compiled build.

**Primary Dependencies**: `jq` (already a repo-wide dependency); `${CLAUDE_PLUGIN_ROOT}` plugin-root indirection (already used by existing shared scripts) for runtime-agnostic invocation by both Claude Code and Codex runtimes.

**Storage**: N/A — the estimator is a pure stdin/args → stdout JSON function; no persisted state.

**Testing**: `bash tests/run-all.sh` from `speckit-pro/` — Layer 1 (structural + `validate-codex-skills.sh`), Layer 4 (estimator determinism fixtures in `tests/layer4-scripts/`), Layer 5 (agent tool scoping — no change expected). Developer-local (`claude -p`, NOT CI gates): Layer 2 (trigger routing), Layer 3 (functional), Layer 8 (Codex parity).

**Target Platform**: Claude Code plugin marketplace consumers (and Codex CLI consumers) running the speckit-pro plugin on macOS/Linux.

**Project Type**: Claude Code plugin marketplace — single project; skill prose (docs/process) + one shared shell helper.

**Performance Goals**: N/A — the estimator runs once per catalog entry / per spec during an interactive interview; sub-second is inherent for a pure bash+jq function. No throughput target.

**Constraints**: Advisory-only (FR-011) — no gate/threshold/exit-code/blocking logic anywhere; `warn` is informational and both skills MUST continue. Estimator MUST be deterministic (FR-007) — no clocks, randomness, or environment dependence; identical inputs → byte-identical output. No technical-roadmap-template schema change (FR-012). Light trigger touch only (FR-013) — no over/under-trigger regression. Codex parity (FR-014) — every CC skill edit mirrored; shared doc + script are single copies.

**Scale/Scope**: ~6 production files (1 shared script, 1 shared reference doc, 2 CC SKILL.md edits, 2 Codex SKILL.md edits); ~200 production reviewable LOC; one L4 fixture set. Single feature surface.

**Reviewability Budget**: Primary surface = docs/process (two skill SKILL.md prose surfaces + one shared reference doc) with a small harness/adapter component (one bash+jq script + its fixtures). Secondary surface = Codex skill mirrors (prose parity only; no second script/doc copy). Projected reviewable LOC ~200 (script + skill/doc prose), excluding fixtures. Projected production files ~6. Projected total files ~8 (production + the estimator's fixtures + spec/checklist). **Budget result: within budget** (warn thresholds are >400 LOC, >6 production files, >15 total files, or >1 primary surface; all are clear).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluated against `.specify/memory/constitution.md` v1.1.0.

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Plugin Structure Compliance** | PASS | No new plugin, command, agent, or hook. The shared reference doc lands under the existing `speckit-pro/skills/speckit-coach/references/` (sibling to existing reference docs); the shared script lands under the existing `speckit-pro/skills/speckit-coach/scripts/` (sibling to `ensure-reviewability-preset.sh` / `project-fixup.sh`). Skill edits stay within existing `SKILL.md` files. Layer-1 structural validation (incl. `validate-codex-skills.sh`) is the gate. |
| **II. Script Safety** | PASS | `estimate-spec-size.sh` will begin with `#!/usr/bin/env bash`, set `set -euo pipefail` as the first executable line, quote all variables, check command results, be `chmod +x`, and pass `bash -n`. This is the only new script. Verified by `validate-scripts.sh` (run inside Layer 1). |
| **III. Semantic Versioning** | PASS | No manual version edit. The change is `feat(speckit-pro): …`; release-please bumps the minor version on the next release PR. Not touched in this plan. |
| **IV. Test Coverage Before Merge** | PASS | The one new bash script gets a Layer-4 unit test `tests/layer4-scripts/test-estimate-spec-size.sh` with a committed fixture set asserting byte-identical output for identical inputs and correct `ok`/`warn` status at and around the ceiling (incl. the spike and zero/negative/malformed cases). No implementation is complete until `bash tests/run-all.sh` is green. Test uses `tests/lib/assertions.sh` and the `test-<script-name>.sh` naming convention. |
| **V. Conventional Commits** | PASS | Commits/PR title follow `feat(speckit-pro): …` (scope = plugin dir). PR title doubles as the squash commit subject; written plain-English per repo policy. Enforced by CI `validate-pr-title`. |
| **VI. KISS, Simplicity & YAGNI** | PASS | The estimator is a pure function of its inputs; the ceiling is a single hardcoded constant with a "keep in sync with the documented ceiling" comment. No structured catalog schema, no gate engine, no second script/doc copy, no template change, no speculative flags. Guidance prose lives once (shared doc), summarized inline — no duplication. Master-plan entry exists (PR-size-governance roadmap, PRSG-005). |

**Constitution Check result: PASS — no violations. Complexity Tracking table left empty (nothing to justify).**

PR review packet source (per the project constitution's plan requirements): the PR description MUST carry what changed, why, non-goals, review order, scope budget, traceability (each FR/SC → changed files + verification evidence), verification evidence (`bash tests/run-all.sh` green; estimator byte-identical on fixtures; developer-local L2/L3/L8 recorded), known gaps, and rollback notes (the feature is additive and advisory-only — rollback = revert the skill edits and remove the shared script + doc; no data migration, no flag needed). Deferred work names its follow-up spec: PRSG-006 (plan-phase budget gate + authoritative reviewable-LOC count) and PRSG-007/008/009 (split-PR engine).

## Project Structure

### Documentation (this feature)

```text
specs/prsg-005-slice-sizing-heuristics/
├── spec.md              # Feature spec (already present)
├── SPEC-MOC.md          # Spec map-of-content (already present)
├── plan.md              # This file (/speckit-plan output)
├── data-model.md        # Phase 1 output — estimator input/output entities
├── quickstart.md        # Phase 1 output — how to run/verify the estimator
├── contracts/
│   └── estimate-spec-size.md   # Phase 1 output — estimator CLI contract
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

`research.md` is intentionally omitted: there are no open unknowns to resolve. Every HOW
decision (shared homes, estimator contract, division of labor, advisory-only, Codex
adaptation) is already locked by the Clarify phase and recorded in the Design Concept
(`docs/ai/specs/.process/PRSG-005-design-concept.md`, Q1–Q10) and spec Assumptions.

### Source Code (repository root)

All paths are under the `speckit-pro/` plugin. Six production surfaces, one test surface:

```text
speckit-pro/
├── skills/
│   ├── speckit-coach/
│   │   ├── references/
│   │   │   └── slicing-heuristics.md          # NEW — shared SPIDR+INVEST+vertical-slicing doc (single source of truth)
│   │   └── scripts/
│   │       └── estimate-spec-size.sh          # NEW — shared deterministic bash+jq estimator (single copy)
│   ├── speckit-prd/
│   │   └── SKILL.md                           # EDIT (CC) — catalog decomposition + Budget-line population + inline summary/link + trigger phrase(s)
│   └── grill-me/
│       └── SKILL.md                           # EDIT (CC) — slice-sizing design-tree branch + split sub-interview + inline summary/link + trigger phrases
├── codex-skills/
│   ├── speckit-prd/
│   │   └── SKILL.md                           # EDIT (Codex mirror) — behavior-equivalent prose; free-text Q&A loop instead of AskUserQuestion
│   └── grill-me/
│       └── SKILL.md                           # EDIT (Codex mirror) — behavior-equivalent prose; free-text split loop instead of AskUserQuestion
└── tests/
    └── layer4-scripts/
        ├── test-estimate-spec-size.sh         # NEW — Layer-4 determinism + boundary unit test
        └── fixtures/                          # NEW — committed input→expected-JSON fixture set
```

**Structure Decision**: Single-project plugin layout. The estimator and the shared
reference doc are placed under `speckit-pro/skills/speckit-coach/` (scripts/ and
references/) because that is where the existing cross-skill shared runtime scripts
(`ensure-reviewability-preset.sh`, `project-fixup.sh`) and shared reference docs already
live — the same shared-asset placement PRSG-002 used. Both are invoked/linked by all four
skill surfaces via `${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/...`, keeping them
runtime-agnostic (single copy for Claude Code and Codex).

## Locked Homes & Edit Surfaces (G3 checklist)

These are the Plan-phase HOW decisions the G3 gate requires, all pinned here:

- **Shared script home** (single copy): `speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh`, invoked via `${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/scripts/estimate-spec-size.sh`. (FR-006, FR-009; Clarify S2 LOCKED.)
- **Shared reference-doc home** (single copy): `speckit-pro/skills/speckit-coach/references/slicing-heuristics.md`. (FR-010, FR-015; Clarify S2 LOCKED.)
- **Claude Code skill surface 1**: `speckit-pro/skills/speckit-prd/SKILL.md` (US1).
- **Claude Code skill surface 2**: `speckit-pro/skills/grill-me/SKILL.md` (US2).
- **Codex mirror 1**: `speckit-pro/codex-skills/speckit-prd/SKILL.md` (FR-014).
- **Codex mirror 2**: `speckit-pro/codex-skills/grill-me/SKILL.md` (FR-014).

### Estimator contract (the single home for the sizing math)

`estimate-spec-size.sh` is a pure function of its inputs (no clocks/randomness/env dependence) and emits compact JSON via `jq`:

- **Inputs** (structured size signals; supplied as args/JSON by the calling skill): number of user stories, number of files/surfaces touched, number of functional requirements, a new-vs-modify flag, and an **optional spike flag** (FR-006, FR-017).
- **Output**: `{estimated_loc, suggested_slices, status}` where `status` is **exactly `ok` or `warn`** — no third value is ever introduced (FR-006, FR-017).
- **Ceiling constant**: the documented ~400-LOC ceiling is a **single hardcoded constant** in the script, carrying a "keep in sync with the documented ceiling in slicing-heuristics.md" comment. It is shared with PRSG-006 by documentation only, never as a consumed artifact (FR-008; Q3).
- **At-ceiling boundary rule**: at exactly the ceiling, `status` is `ok`; `warn` applies only when `estimated_loc` is **strictly greater than** the ceiling (Edge Cases; Clarify S1 LOCKED).
- **Spike rule** (FR-017): when the spike flag is set, the estimator **skips** the LOC-threshold comparison and returns `status: ok`, `suggested_slices: 1`, `estimated_loc: 0`. Here `ok` means "LOC sizing is not applicable to a research slice" (the INVEST "Estimable" escape hatch), not "trivially small" — so a spike never trips a misleading `warn`, preserving the advisory-only invariant.
- **suggested_slices formula**: `ceil(estimated_loc / ceiling)` for a non-spike slice (documented in the script and the shared doc); the L4 fixtures pin the integer-rounding behavior at and around the ceiling.
- **Robustness** (FR-016): each malformed, missing, zero, or negative size signal normalizes to `0`, and `status` then follows the same at-ceiling boundary rule as normal inputs on the resulting `estimated_loc` — not a separate code path, and never a misleading `warn` or a third status value (all-bad/absent input → `estimated_loc: 0` → `ok`). This is exercised by L4 fixtures, never by raising a hard error that could read as a block.

### Division of labor (Q1 — no duplicated guidance prose)

- **`speckit-prd` (US1)** owns **catalog-level decomposition**: it applies SPIDR story-splitting + vertical slicing to emit thin vertical slices by construction, derives the estimator's size signals from each catalog entry it is drafting, populates that entry's existing `Budget: ~N LOC` line from the estimator output, and adds a one-line INVEST/vertical-slice rationale. It carries only a short inline summary + a link to `slicing-heuristics.md`.
- **`grill-me` (US2)** owns **per-spec validation/split**: a dedicated slice-sizing design-tree branch derives size signals from the single spec it is scoping, runs the estimator, and when over the ceiling or horizontally sliced asks a split question (via `AskUserQuestion` in Claude Code) recommending N thin vertical slices; the chosen split is written into the Design Concept doc (Goals / Open Questions). It carries only a short inline summary + a link to `slicing-heuristics.md`.
- The canonical SPIDR + INVEST + vertical-slicing guidance — including the FR-015 "forward estimate ≠ authoritative reviewable-LOC count" caveat and the FR-017 spike-as-timebox-slice-type note — lives **once** in `slicing-heuristics.md`. Neither skill duplicates the guidance prose (FR-010).

### Codex-parity plan (FR-014)

- The shared **script** and shared **reference doc** are single, runtime-agnostic copies — there is **no** Codex-specific second copy. Both Codex skill mirrors invoke the same `${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/scripts/estimate-spec-size.sh` and link the same `slicing-heuristics.md`.
- Each Claude Code `SKILL.md` edit is mirrored, behavior-equivalent, in its `codex-skills/<skill>/SKILL.md` counterpart. The one runtime difference: Codex variants have no `AskUserQuestion` tool, so the `grill-me` split question is adapted to a **free-text question-and-answer loop** that asks the same question, offers the same recommended N-slice split, and records the same outcome in the Design Concept doc — behavior-equivalent, not tool-identical. `speckit-prd`'s catalog-decomposition prose carries across with no tool dependency.
- Parity is verified by `validate-codex-skills.sh` (Layer 1, CI) and by the developer-local Layer-8 parity fixtures + Layer-2 trigger evals before merge.

## Phase 0: Outline & Research

No research tasks. The Technical Context has **zero `NEEDS CLARIFICATION`** markers: the
runtime (bash+jq+Markdown), the shared homes, the estimator contract, the division of labor,
the advisory-only invariant, and the Codex adaptation are all locked by the Clarify phase and
the Design Concept (Q1–Q10). `research.md` is therefore intentionally not generated.

**Output**: none (no unknowns to resolve).

## Phase 1: Design & Contracts

Generated alongside this plan:

- **`data-model.md`** — the estimator's input entity (size signals incl. the optional spike flag) and output entity (`{estimated_loc, suggested_slices, status}`), with validation/boundary rules (at-ceiling → `ok`; `warn` only strictly over; spike → `ok`/1/0; robustness on malformed/zero/negative). Plus the Documented LOC Ceiling constant and the Shared slicing-heuristics reference as entities.
- **`contracts/estimate-spec-size.md`** — the estimator CLI contract: invocation path, accepted args/JSON keys, the exact output JSON shape and the `ok`/`warn` enum, determinism guarantee, and the spike/at-ceiling behaviors. This is the contract the L4 fixtures pin.
- **`quickstart.md`** — how to invoke the estimator and run its Layer-4 test; how a maintainer triggers the new sizing/slicing behavior in each skill; how to verify the advisory-only and Codex-parity invariants.

The agent context file (`CLAUDE.md`) `<!-- SPECKIT START -->`/`<!-- SPECKIT END -->` plan
reference is updated to point at this plan.

**Output**: data-model.md, contracts/estimate-spec-size.md, quickstart.md, updated agent context.

## Post-Design Constitution Re-Check

Re-evaluated after Phase 1: **still PASS, no new violations.** The design introduces no new
script beyond `estimate-spec-size.sh`, no schema change, no gate/exit-code logic, and no
duplicated guidance. The reviewability budget is unchanged (~200 LOC, ~6 production files,
single primary surface) and remains within budget. Complexity Tracking remains empty.

## Complexity Tracking

> No constitution violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |
