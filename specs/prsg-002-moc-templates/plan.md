# Implementation Plan: MOC templates + scaffold-time skeleton + version-gated lints

**Branch**: `prsg-002-moc-templates` | **Date**: 2026-06-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/prsg-002-moc-templates/spec.md`

## Summary

PRSG-002 builds the navigation/traceability spine for spec artifacts (a Maps-of-Content layer) so collapsing or relocating artifacts never makes a document unreachable. It ships four things: (1) two MOC template shapes (roadmap-MOC, spec-MOC) carrying the frontmatter join-key contract; (2) a scaffold-time skeleton writer — `speckit-scaffold-spec` stamps a minimal `SPEC-MOC.md` into `specs/<branch-name>/` on every new spec via the same token-substitution it already uses for `workflow-template.md`; (3) two version-gated Layer-1 lints — orphan (a MOC lacking a valid `up:`) and stale-index (a MOC relative link that does not resolve, plus any wikilink); (4) a shared namespace-aware ID normalizer that joins doc IDs to directory names across the `SPEC-` and `PRSG-` conventions without collision. Version-gating (`structureVersion >= 1`) is the load-bearing safety property: the lints bite for every new spec from creation while pre-existing legacy specs (no marker) are grandfathered, so the first upgrade does not red-fail CI.

Technical approach: pure bash + jq deterministic shell and Markdown templates — no compiled build, no product code. The two lints are Layer-1 validators wired into `tests/run-all.sh`, exercised by committed fixtures (matching the existing 8 validators' pattern) and scanning this repo's real spec trees (`docs/ai/specs/`, `specs/`). The dangerous-edge logic — the namespace-aware normalizer with opaque whole-segment comparison (`013a` != `013a1`) — is extracted into one shared helper used by both lints and earns a dedicated Layer-4 unit test; a second Layer-4 driver covers the lints' 3-way exit-code contract (the trap→`2`, missing-root, and unreadable-marker behaviors that can only be observed across a process boundary).

## Technical Context

**Language/Version**: Bash (macOS/Linux), `jq` for JSON/frontmatter parsing. Markdown for templates. No compiled language.

**Primary Dependencies**: `jq` (already a repo dependency); `git` (for `git rev-parse --show-toplevel` to locate repo root from the worktree). No new dependency introduced (per CLAUDE.md "prefer plain bash + jq").

**Storage**: N/A (filesystem markdown only).

**Testing**: Shell test harness via `bash tests/run-all.sh` run from `speckit-pro/`. Layer 1 (structural/lint) + Layer 4 (script unit, via `tests/lib/assertions.sh`). There is NO build/typecheck/lint step in this repo (`detect-commands` returns N/A — no npm/cargo/etc.).

**Target Platform**: Developer machines + GitHub Actions CI (`bash tests/run-all.sh` on changed plugins). The shipped lint scripts are runtime-agnostic so any consuming project's checks can run them.

**Project Type**: Claude Code plugin (speckit-pro) inside a plugin marketplace repo, dogfooding SpecKit. Docs/process + plugin-shell change.

**Performance Goals**: N/A (deterministic linting over a small file tree; runs in well under a second).

**Constraints**: Constitution Script Safety (II) — `#!/usr/bin/env bash`, `set -euo pipefail`, quoted vars, `chmod +x`, `bash -n` clean. KISS/YAGNI (VI). No new preset, no project-local template copy, no shared version file.

**Scale/Scope**: ~350 reviewable LOC across one primary surface (the speckit-pro plugin shell + docs/process). Two new lint scripts, one shared helper, two new templates, two skill-file edits (Claude + Codex mirror), one `run-all.sh` wiring edit, committed fixtures, two Layer-4 tests (the normalizer unit test + the lints' exit-code driver).

**Reviewability Budget**: Primary surface = speckit-pro plugin shell (templates + tests + scaffold skill). Projected reviewable LOC ~350. Production (shipped, non-test) files: 2 templates + 1 shared helper + 2 lint scripts + 2 skill edits + 1 run-all.sh edit ≈ 5 new files + 3 edits. Total files incl. fixtures + two Layer-4 tests ≈ 12-15. **Budget result: WITHIN budget** — under the 400 reviewable-LOC / 6 production-file / 15 total-file warn thresholds, single primary surface. No split required.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution v1.1.0. Gate evaluation:

- **I. Plugin Structure Compliance** — PASS. No new plugin; adds skill behavior, templates, and Layer-1 tests inside the existing `speckit-pro/` layout. New templates live in the established `skills/speckit-coach/templates/` dir; new lints live in `tests/layer1-structural/`. Quality gate `bash tests/run-all.sh --layer 1` continues to pass (the new lints are appended to the Layer-1 list and stay green because every legacy spec is version-gate-exempt).
- **II. Script Safety** — PASS (by design). Every new bash script (the two lints + the shared normalizer + the two Layer-4 tests) MUST begin with `#!/usr/bin/env bash` + `set -euo pipefail`, quote all variables, check command results, be `chmod +x`, and pass `bash -n`. `validate-scripts.sh` (already in the Layer-1 run) enforces this on the new scripts automatically.
- **III. Semantic Versioning** — N/A to this change. No `plugin.json` version edit; release-please handles the bump from the `feat(speckit-pro):` commit. NOTE: the feature's own `structureVersion` literal (`1`) is an internal document-schema version, NOT the plugin semver — deliberately a hardcoded integer with a "keep in sync" comment, no semver string (FR-016, KISS).
- **IV. Test Coverage Before Merge** — PASS (split stated explicitly to honor the principle, not skip it). Principle IV requires Layer-4 unit tests for new bash scripts. Reconciliation with the existing pattern: the **two lints are Layer-1 validators exercised by committed fixtures** (mirroring the 8 existing Layer-1 validators, which are fixture/tree-exercised rather than 1:1 Layer-4 tested). The **shared namespace-aware normalizer helper gets a dedicated Layer-4 unit test** — it is the reusable logic carrying the dangerous edge cases (`PRSG-002`!=`SPEC-002`, `013a`!=`013a1`, opaque-segment compare, no-prefix→`spec`), so it is the unit that genuinely warrants isolated coverage. A **second Layer-4 driver** covers the lints' 3-way exit-code contract (trap→`2`, missing/empty scan root, zero-gated, and the unreadable-marker skip per FR-020/FR-022/FR-024) — behaviors a script cannot assert about its own trap-driven exit from inside itself, so they require a subprocess driver (mirrors `test-validate-gate.sh`). `bash tests/run-all.sh` (Layers 1, 4, 5) MUST pass with zero failures.
- **V. Conventional Commits** — PASS. Work lands as `feat(speckit-pro): ...` with a public-readable, plain-English description (per CLAUDE.md PR-title rules). Squash-merge uses the PR title as the commit subject.
- **VI. KISS, Simplicity & YAGNI** — PASS. Single shared normalizer (no per-lint duplication, no premature abstraction). Hardcoded integer version literal copied verbatim with a "keep in sync" comment (mirrors the repo's existing `extract_heading_section` verbatim-copy pattern) instead of a shared version file. No new preset/plumbing — the scaffold reuses its existing token-substitution path. `status`/`rank`/`related` are carried in templates but unenforced in v1 (no speculative lint surface).

**Result: All gates PASS. No Complexity Tracking entries required** (no justified violations).

### Required plan declarations (per template)

- **Primary review surface**: the speckit-pro plugin shell — `skills/speckit-coach/templates/` (2 new templates), `tests/layer1-structural/` (2 lints + shared helper + fixtures), `tests/layer4-scripts/` (2 tests: normalizer unit test + exit-code driver), `tests/run-all.sh` (wiring), and the scaffold skill (`skills/speckit-scaffold-spec/SKILL.md` + Codex mirror). No secondary surface.
- **Reviewability budget verdict**: WITHIN budget (see Technical Context → Reviewability Budget). ~350 reviewable LOC, single primary surface, ≤15 total files. No warn/block threshold crossed; no split exception needed.
- **Split decision**: none required — feature fits in one PR within budget. (Sibling specs PRSG-003 generated MOC content, PRSG-004 PRD-derived roadmap-MOC home note, PRSG-011 legacy backfill/relocation are independently scoped in the roadmap and are explicit non-goals here.)
- **PR review packet source**:
  - *What changed*: two MOC templates; scaffold writes `SPEC-MOC.md` (Claude + Codex); two version-gated Layer-1 lints + shared normalizer; fixtures + two Layer-4 tests (normalizer unit test + exit-code driver); `run-all.sh` wiring.
  - *Why*: build the navigation spine so artifact collapse/relocation never orphans a document; make the contract enforced (not advisory) for new specs while grandfathering legacy specs.
  - *Non-goals*: generated MOC content (PRSG-003), PRD-derived home note (PRSG-004), legacy backfill/relocation (PRSG-011), `up:` on non-MOC docs, wikilink support.
  - *Review order*: contracts/ → templates → shared normalizer → lints → fixtures → scaffold skill edits (Claude then Codex) → run-all.sh wiring → Layer-4 tests (normalizer unit test + exit-code driver).
  - *Scope budget*: ~350 reviewable LOC / single surface (within constitution budget).
  - *Traceability*: FR-001..FR-019 mapped to surfaces in this plan and in `contracts/`; tasks.md (next phase) will map each FR to a task.
  - *Verification*: `bash tests/run-all.sh` from `speckit-pro/` (Layers 1, 4, 5) green; the dogfooded lints scan real spec trees and stay green (legacy specs exempt; PRSG-002's own marker resolves).
  - *Known gaps*: none blocking; `status`/`rank`/`related` carried-but-unenforced by design.
  - *Rollback/flags*: no runtime flag. Rollback = revert the PR; version-gating means removing the lints/marker has no effect on legacy specs. New scaffolds simply stop writing the marker.

## Project Structure

### Documentation (this feature)

```text
specs/prsg-002-moc-templates/
├── plan.md              # This file (/speckit-plan output)
├── spec.md              # Feature spec (already present)
├── research.md          # Phase 0 output — settled-decision record
├── data-model.md        # Phase 1 output — entities (MOC, normalized ID, version gate)
├── quickstart.md        # Phase 1 output — how to run/verify the lints + scaffold
├── contracts/           # Phase 1 output — frontmatter contract, ID grammar, lint exit codes
│   ├── frontmatter-join-key-contract.md
│   ├── id-normalization-grammar.md
│   └── lint-behavior-contract.md
├── checklists/
│   └── requirements.md  # Spec quality checklist (already present)
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

This feature touches the `speckit-pro/` plugin and (for the dogfooded scan + this spec's own marker) the repo-root spec trees. Concrete paths:

```text
speckit-pro/
├── skills/
│   ├── speckit-coach/templates/
│   │   ├── workflow-template.md             # existing — unchanged, shown for sibling context
│   │   ├── roadmap-moc-template.md          # NEW — roadmap-MOC shape (full frontmatter contract)
│   │   └── spec-moc-template.md             # NEW — spec-MOC shape; scaffold reads this + token-substitutes
│   └── speckit-scaffold-spec/
│       └── SKILL.md                         # EDIT — add "write minimal SPEC-MOC.md into specs/<branch-name>/" step
├── codex-skills/
│   └── speckit-scaffold-spec/
│       └── SKILL.md                         # EDIT — mirror the skeleton-writing step (runtime parity; templates/lints stay single-copy)
└── tests/
    ├── lib/
    │   └── moc-id-normalize.sh              # NEW — shared namespace-aware normalizer (sourced by both lints + Layer-4 test)
    ├── layer1-structural/
    │   ├── validate-moc-orphan.sh          # NEW — orphan lint (MOC must have present + well-formed relative up:)
    │   ├── validate-moc-stale-index.sh     # NEW — stale-index lint (all relative targets incl. up: must resolve; wikilink = violation)
    │   └── fixtures/                        # NEW — committed fixtures exercising both lints + normalizer
    │       └── moc/                         #   positive + negative fixtures (orphan, stale, wikilink, no-marker skip, spec_id mismatch, ID-normalization cases)
    ├── layer4-scripts/
    │   ├── test-moc-id-normalize.sh        # NEW — Layer-4 unit test for the shared normalizer (SPEC-002/PRSG-002, 013a/013a1, 006a, no-prefix→spec)
    │   └── test-moc-lint-exit-codes.sh     # NEW — Layer-4 subprocess driver for the lints' 3-way exit-code contract (trap→2, missing/empty root, zero-gated, unreadable-marker skip; FR-020/022/024)
    └── run-all.sh                          # EDIT — append the two lints to the Layer-1 runtime-agnostic list

# Repo-root spec trees scanned by the dogfooded lints (FR-015) — not modified except this spec's own marker:
docs/ai/specs/                              # scanned tree (legacy specs here carry no SPEC-MOC.md → exempt)
specs/
└── prsg-002-moc-templates/
    └── SPEC-MOC.md                          # NEW (written by scaffold during this feature's own bootstrap):
                                             #   up: ../../docs/ai/specs/pr-size-governance-technical-roadmap.md
                                             #   structureVersion: 1 ; spec_id: PRSG-002
```

**Structure Decision**: Single-surface change inside the existing `speckit-pro/` plugin tree. Templates go in the established `skills/speckit-coach/templates/` dir (where the scaffold already reads `workflow-template.md`). The two lints follow the existing Layer-1 validator idiom and reach repo root the same way `validate-process-gitattributes.sh` does — `REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"` (layer1-structural → tests → speckit-pro → repo root). The shared normalizer lives in `tests/lib/` (alongside `assertions.sh`) so both lints and the Layer-4 test can `source` a single copy.

### Repo-root resolution for the dogfooded scan (load-bearing detail)

`bash tests/run-all.sh` runs from `speckit-pro/`, but FR-015's scan targets (`docs/ai/specs/`, `specs/`) live one level up at repo root. The lints MUST resolve repo root explicitly. Mirror the established idiom from `validate-process-gitattributes.sh`:

```bash
# layer1-structural -> tests -> speckit-pro -> repo root
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
```

(In a worktree this is correct; `.git` being a file does not affect path-walking with `cd`/`pwd`. `git rev-parse --show-toplevel` is an equivalent fallback that also returns the worktree top, but the `dirname` walk matches existing style and needs no git invocation.) The stale-index lint resolves each relative link **relative to the MOC file's own directory**, so PRSG-002's own `up: ../../docs/ai/specs/pr-size-governance-technical-roadmap.md` resolves from `specs/prsg-002-moc-templates/` (verified: the target exists at that relative path).

## Phase 0: Outline & Research

No open NEEDS CLARIFICATION exist — the spec carries zero markers and the design concept (`docs/ai/specs/.process/PRSG-002-design-concept.md`) resolved all 8 design questions plus the maintainer's `spec_id`↔directory decision. `research.md` therefore records the **already-settled** decisions in Decision / Rationale / Alternatives form (sourced from the Q&A log), rather than manufacturing unknowns. See `research.md`.

## Phase 1: Design & Contracts

**Prerequisites**: research.md complete.

- **data-model.md** — captures the entities: MOC file (identified by exact filename `SPEC-MOC.md` in v1), frontmatter join-key contract (enforced vs carried fields), normalized ID `(namespace, number-suffix)`, version gate (`structureVersion >= shipped`), and spec tree. Includes the enforced-field validation rules and the version-gate state condition.
- **contracts/** — three contract docs other specs (PRSG-003/004) consume:
  - `frontmatter-join-key-contract.md` — the six fields, which three are load-bearing/enforced in v1 (`up`, `structureVersion`, `spec_id`) vs carried-unenforced (`status`, `rank`, `related`).
  - `id-normalization-grammar.md` — the exact split/compare grammar (lowercase, split on `-`, all-alpha first segment = namespace else `spec`, opaque whole-segment number compare, both parts must agree), with the canonical examples.
  - `lint-behavior-contract.md` — orphan vs stale-index division of labor, the version gate, exit-code semantics (nonzero on violation in a version-gated spec; success/skip otherwise), and the MOC-only scope.
- **quickstart.md** — how a maintainer runs and verifies the feature: `bash tests/run-all.sh` from `speckit-pro/`, what the lints check, and how to scaffold a spec that gets a marker.
- **Agent context update** — update the plan reference inside the existing `<!-- SPECKIT START -->` / `<!-- SPECKIT END -->` markers in the repo `CLAUDE.md` (lines 419-422) to point at this plan. The block is a generic placeholder; only the reference text inside the markers is touched (the hand-maintained body above is left untouched, per the surgical-edit rule). `.specify/scripts/bash/update-agent-context.sh` exists and targets exactly this marker block.

**Output**: data-model.md, contracts/*, quickstart.md, updated agent-context reference.

## Complexity Tracking

No constitution violations to justify. Table intentionally empty.
