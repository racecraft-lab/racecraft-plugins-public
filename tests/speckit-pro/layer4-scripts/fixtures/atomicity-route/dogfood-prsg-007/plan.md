# Implementation Plan: Atomicity-test router (read-only classifier) (PRSG-007)

**Branch**: `prsg-007-atomicity-router` | **Date**: 2026-06-08 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/prsg-007-atomicity-router/spec.md`

## Summary

Ship the read-only "brain" of the PR-Size Governance split engine: a stack-agnostic
classifier (`atomicity-route.sh <feature-dir>`) that reads a feature's `tasks.md`,
`plan.md`, and `spec.md`, applies an ordered set of detectors, and emits exactly one
machine-readable routing decision (a single JSON object) to stdout. It changes nothing
and blocks nothing — it classifies (`route`) and flags release risk (`releasable`),
emitting a controlled `signals[]` vocabulary, advisory `hints[]`, and canonical
`warnings[]`. The speckit-autopilot SKILL (not the script) records the decision into the
workflow file's `## Atomicity Route` section after the Tasks phase / gate G5. Technical
approach: plain `bash` + `jq`, mirroring the `reviewability-gate.sh` interface family,
duplicating (not sharing) the two path matchers it needs, and adding one Layer-4 test with
one fixture per change class.

## Technical Context

**Language/Version**: bash (`#!/usr/bin/env bash`, `set -euo pipefail`), POSIX-ERE `grep -E` for prose matching; `jq` for JSON emission (constitution II + VI).

**Primary Dependencies**: `jq` (already a project dependency); standard POSIX text tools (`grep`, `sed`, `sort`, `wc`). No new dependency introduced.

**Storage**: N/A — the classifier is read-only and writes no files (FR-011). The route is recorded by the autopilot SKILL into the workflow file.

**Testing**: Layer 4 shell unit tests (`tests/speckit-pro/layer4-scripts/test-atomicity-route.sh`) using the shared `tests/speckit-pro/lib/assertions.sh` library, plus one fixture per change class under `tests/speckit-pro/layer4-scripts/fixtures/`. Layer 1 structural validation (`bash tests/speckit-pro/run-all.sh --layer 1`) covers the new script, the edited workflow template, and the edited/mirrored SKILL files.

**Target Platform**: macOS/Linux developer shells and CI (GitHub Actions), the same surface as the existing autopilot scripts.

**Project Type**: CLI script + plugin documentation (a speckit-pro plugin component; single bash CLI invoked by the speckit-autopilot skill).

**Performance Goals**: N/A — single short-lived invocation over a few small Markdown files per feature directory; no throughput target.

**Constraints**: ~400 reviewable LOC budget (one `scripts/atomicity-route.sh`); no LOC/sizing computation (FR-002); no internal call to or edit of `reviewability-gate.sh` (FR-015); stack-agnostic detection (FR-014); MUST NOT emit `branch-by-abstraction` in the MVP (FR-001, SC-008).

**Scale/Scope**: 1 new production script + a bounded SKILL edit + a workflow-template section + a Codex SKILL mirror + a references doc; one Layer-4 test with one fixture per change class. Projected total ~10 files.

**Reviewability Budget**: Primary surface = scheduler/runtime (the new classifier script the autopilot runs after Tasks). Secondary surfaces = harness/adapter (Layer-4 fixtures and unit test) and docs/process (workflow-template section + SKILL/Codex/references prose). Projected reviewable LOC ~400 (`scripts/atomicity-route.sh`, plain `bash` + `jq`). Projected production files = 1 (`scripts/atomicity-route.sh`). Projected total files ~10. Budget result: within budget (warn line at 400 LOC / 6 production files / 15 total files; this sits at or under each). Split decision: remains one spec — one structural seam (classify-and-emit); PR emission / layer-planner / multi-PR rewrite are downstream specs (PRSG-008, PRSG-009).

## Declared File Operations

The plan-phase reviewability estimator (`estimate-reviewable-loc.sh`) parses this
block to project the slice's production-LOC footprint before `tasks.md` exists.

- NEW speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh
- NEW tests/speckit-pro/layer4-scripts/test-atomicity-route.sh
- NEW tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/additive-multi-seam/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/single-additive-seam/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/hard-atomic-rename/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/hard-atomic-version-pin/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/hard-atomic-destructive-migration/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/hard-atomic-mutual-exclusion/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/hard-atomic-out-of-tree-contract/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/concurrency/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/modify-heavy/tasks.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/out-of-scope-empty/.gitkeep
- MODIFIED speckit-pro/skills/speckit-coach/templates/workflow-template.md
- MODIFIED speckit-pro/skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/phase-execution.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/SKILL.md

Note: the only production file (per the gate's `is_production_file` taxonomy: `scripts/*`)
is `atomicity-route.sh`. Fixtures, the test, and the prose edits are harness/adapter and
docs/process surfaces. Each fixture directory needs at least a `tasks.md` (or, for the
out-of-scope case, an empty/absent `tasks.md`); per-fixture `plan.md`/`spec.md` are added
at implement time where a detector requires the three-artifact read.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|-----------|-------|--------|
| I. Plugin Structure Compliance | New script lives under `speckit-pro/skills/speckit-autopilot/scripts/`; test lives in repo-root `tests/speckit-pro/layer4-scripts/` (NOT inside the plugin dir, per the payload guard). No new plugin, command, agent, or hook. | PASS |
| II. Script Safety | `atomicity-route.sh` begins with `#!/usr/bin/env bash` + `set -euo pipefail`; all variables quoted; JSON via `jq`; `chmod +x`; passes `bash -n`. | PASS (enforced at implement time) |
| III. Semantic Versioning | No manual version edit; release-please bumps `plugin.json` on the `feat(speckit-pro):` commit. | PASS |
| IV. Test Coverage Before Merge | New bash script gets a Layer-4 unit test (`test-atomicity-route.sh`) using `tests/speckit-pro/lib/assertions.sh`, naming convention `test-<script-name>.sh`; Layer 1 covers edited SKILL/template/Codex files. SC-007 requires one fixture per change class. | PASS (enforced at implement time) |
| V. Conventional Commits | Commit/PR title `feat(speckit-pro): <plain-English>` (squash subject is public-readable). | PASS |
| VI. KISS, Simplicity & YAGNI | DUPLICATE the two needed matchers (`surface_for_path`, `is_excluded_generated`) rather than extract a shared lib — "three similar lines beat a premature abstraction" and the spec mandates duplication (FR-014/015). No speculative `branch-by-abstraction` emission (reserved enum). No LOC machinery. | PASS |

**Reviewability budget (constitution + spec):** within budget (see Technical Context above). Primary surface = scheduler/runtime; secondaries = harness/adapter + docs/process. No threshold (400 LOC / 6 production files / 15 total files / 1 primary surface) is exceeded, so no split exception is required.

**PR review packet source:** the PR description draws what-changed / why / non-goals / review-order / scope-budget / traceability / verification / known-gaps / rollback from this plan and spec §"PR Review Packet Requirements". Traceability maps each FR/SC to changed files + Layer-4 fixtures and Layer-1 validation. Deferred work names PRSG-008 (layer-planner), PRSG-009 (multi-PR emission), and the deep implementation of the three contextual probes (PRSG-010 US3 for the consumer-locality probe / `branch-by-abstraction`).

**Result:** No constitution violations. Complexity Tracking table below is empty.

## Project Structure

### Documentation (this feature)

```text
specs/prsg-007-atomicity-router/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (decisions: contract, hygiene, dup-not-share)
├── data-model.md        # Phase 1 output (JSON contract + signals vocabulary + change classes)
├── quickstart.md        # Phase 1 output (runnable validation scenarios)
├── contracts/
│   └── routing-decision.schema.json   # Phase 1 output (the stable JSON contract for PRSG-008)
├── spec.md              # Finalized through Clarify
├── SPEC-MOC.md          # Roadmap map note (route is NOT stored here — FR per spec Assumptions)
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
speckit-pro/skills/speckit-autopilot/
├── scripts/
│   ├── atomicity-route.sh            # NEW — the read-only classifier (the only production file)
│   └── reviewability-gate.sh         # UNCHANGED — source of the two matchers we DUPLICATE (never edited)
├── references/
│   └── phase-execution.md            # MODIFIED — document the post-Tasks router step + recording
└── SKILL.md                          # MODIFIED — invoke the classifier after Tasks/G5, record the route

speckit-pro/codex-skills/speckit-autopilot/
└── SKILL.md                          # MODIFIED — MIRROR of the prose (script is shared, single scripts/ dir)

speckit-pro/skills/speckit-coach/templates/
└── workflow-template.md              # MODIFIED — add the "## Atomicity Route" section (route, releasable, signals, warnings)

tests/speckit-pro/layer4-scripts/
├── test-atomicity-route.sh           # NEW — Layer-4 unit test (uses lib/assertions.sh)
└── fixtures/atomicity-route/         # NEW — one fixture dir per change class
    ├── additive-multi-seam/          #   → split-PR
    ├── single-additive-seam/         #   → one-navigable-PR | single-atomic-PR (single-PR-style)
    ├── hard-atomic-rename/           #   → single-atomic-PR
    ├── hard-atomic-version-pin/      #   → single-atomic-PR
    ├── hard-atomic-destructive-migration/   # → single-atomic-PR + releasable:false + CI-green warning
    ├── hard-atomic-mutual-exclusion/ #   → single-atomic-PR
    ├── hard-atomic-out-of-tree-contract/    # → single-atomic-PR
    ├── concurrency/                  #   → releasable:false + CI-green warning (route per other detectors)
    ├── modify-heavy/                 #   → one-navigable-PR (never branch-by-abstraction; SC-008)
    └── out-of-scope-empty/           #   → out-of-scope (missing/empty tasks.md)
```

**Structure Decision**: This is a single-bash-CLI plugin component, not a multi-project
app — no `src/`/`backend/`/`frontend/` layout applies. The production code is one script
in the existing `speckit-autopilot/scripts/` directory; the test and its fixtures live in
the repo-root `tests/speckit-pro/` tree (the payload guard forbids `tests/` inside the
plugin dir). The classifier script is SHARED (single `scripts/` dir, used by both the
Claude Code skill and its Codex mirror); only prose is mirrored into `codex-skills/`.

## Complexity Tracking

> No constitution violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |
