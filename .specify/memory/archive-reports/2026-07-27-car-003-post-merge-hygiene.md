# Archival Report - CAR-003 Evaluation Runner, Fixtures, Scoring, and Statistical Analysis

## Mode

- **archiveMode**: merged-spec cleanup sweep
- **dryRun**: false
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true
- **excludedCurrentSpec**: none

## Provenance

- **Source spec path**: `specs/car-003-evaluation-runner-scoring/`
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/385
- **PR title**: `feat(car-003): add the evaluation platform that turns capability
  evidence into qualification evidence`
- **Merged at**: `2026-07-26T23:49:26Z`
- **Merge commit**: `9fab2083cd74fcaca28cb6589cf8705e0e8ddd3c`
- **Head branch**: `car-003-evaluation-runner-scoring`
- **Base branch**: `main`
- **Workflow preserved**: `docs/ai/specs/.process/CAR-003-workflow.md`
- **Design concept preserved**: `docs/ai/specs/.process/CAR-003-design-concept.md`
- **Additional process evidence preserved**:
  `docs/ai/specs/.process/CAR-003-size-exception.md`,
  `docs/ai/specs/.process/CAR-003-twin-handoff.md`, and
  `docs/ai/specs/.process/CAR-003-slice-{1,2,3}-pr-packet.md`
- **CI / metadata gates**: all required PR checks passed, including
  `validate-pr-title`, `validate-release-note`, `validate-workflows`,
  `validate-docs`, `artifact-consistency`, `test (speckit-pro)`,
  `validate-plugins`, CodeQL, and Linux/Windows container preflight.
- **Screenshot retention**: N/A
- **Expiration risk**: committed source and process evidence has no artifact
  retention dependency.

## Feature Summary

CAR-003 shipped the Claude-side evaluation platform that converts CAR-002
capability evidence into qualification evidence. It delivered the canonical
agent materializer as the single shipped production surface, a governed role
corpus, blinded two-scorer plus frozen-adjudicator scoring, closed experiment
policy and analysis-plan contracts, a statistical decision ladder, and a
calibration pilot with content-addressed offline replay.

It preserved the no-qualification boundary: the calibration partition is
non-eligible, and the spec emits only calibration-complete, inconclusive, or
invalid outcomes. It cannot select preferred routes, order fallbacks, or change
installed defaults.

## Canonical Shipped Artifacts

- `speckit-pro/speckit_pro_runner/materializer.py` (the sole shipped
  production file, mirrored into `dist/claude/` and `dist/codex/`)
- `docs/ai/research/claude-car-003-analysis-plan.json`
- `docs/ai/research/claude-car-003-calibration-completion.json`
- `docs/ai/research/claude-car-003-calibration-pilot.json`
- `docs/ai/research/claude-car-003-mandatory-observation-manifest.json`
- `docs/ai/research/claude-car-003-successor-capability-freeze.json`
- `docs/ai/research/claude-car-003-successor-freeze-collection.json`
- `tests/speckit-pro/layer6-efficiency/lib/claude_analysis_decision.py`
- `tests/speckit-pro/layer6-efficiency/lib/claude_experiment_policy.py`
- `tests/speckit-pro/layer6-efficiency/lib/claude_role_corpus.py`
- `tests/speckit-pro/layer6-efficiency/lib/claude_score_bundle.py`
- `tests/speckit-pro/layer6-efficiency/lib/claude_successor_freeze.py`
- `tests/speckit-pro/layer6-efficiency/lib/claude_treatment_runner.py`
- `tests/speckit-pro/layer6-efficiency/collect-successor-freeze.py`
- `tests/speckit-pro/layer6-efficiency/run-calibration-pilot.py`
- `tests/speckit-pro/layer6-efficiency/fixtures/car-003-*.json`
- `tests/speckit-pro/unit/test-analysis-decision-ladder.py`
- `tests/speckit-pro/unit/test-calibration-pilot-driver.py`
- `tests/speckit-pro/unit/test-canonical-agent-materializer.py`
- `tests/speckit-pro/unit/test-exact-treatment-runner.py`
- `tests/speckit-pro/unit/test-experiment-policy-partitions.py`
- `tests/speckit-pro/unit/test-role-corpus-governance.py`
- `tests/speckit-pro/unit/test-score-bundle-adjudication.py`
- `tests/speckit-pro/unit/test-successor-capability-freeze.py`
- `docs/ai/specs/.process/CAR-003-workflow.md`
- `docs/ai/specs/.process/CAR-003-design-concept.md`
- `docs/ai/specs/.process/CAR-003-size-exception.md`
- `docs/ai/specs/.process/CAR-003-twin-handoff.md`

## Recovery Commands

```text
git show 9fab2083cd74fcaca28cb6589cf8705e0e8ddd3c:specs/car-003-evaluation-runner-scoring/spec.md
git show 9fab2083cd74fcaca28cb6589cf8705e0e8ddd3c:specs/car-003-evaluation-runner-scoring/plan.md
git show 9fab2083cd74fcaca28cb6589cf8705e0e8ddd3c:specs/car-003-evaluation-runner-scoring/tasks.md
git show 9fab2083cd74fcaca28cb6589cf8705e0e8ddd3c:specs/car-003-evaluation-runner-scoring/research.md
git show 9fab2083cd74fcaca28cb6589cf8705e0e8ddd3c:specs/car-003-evaluation-runner-scoring/data-model.md
git show 9fab2083cd74fcaca28cb6589cf8705e0e8ddd3c:specs/car-003-evaluation-runner-scoring/quickstart.md
git show 9fab2083cd74fcaca28cb6589cf8705e0e8ddd3c:specs/car-003-evaluation-runner-scoring/SPEC-MOC.md
git show 9fab2083cd74fcaca28cb6589cf8705e0e8ddd3c:specs/car-003-evaluation-runner-scoring/contracts/experiment-policy.schema.json
git show 9fab2083cd74fcaca28cb6589cf8705e0e8ddd3c:specs/car-003-evaluation-runner-scoring/contracts/score-bundle.schema.json
git show 9fab2083cd74fcaca28cb6589cf8705e0e8ddd3c:specs/car-003-evaluation-runner-scoring/checklists/requirements.md
git show 9fab2083cd74fcaca28cb6589cf8705e0e8ddd3c:specs/car-003-evaluation-runner-scoring/checklists/data-integrity.md
git show 9fab2083cd74fcaca28cb6589cf8705e0e8ddd3c:specs/car-003-evaluation-runner-scoring/checklists/error-handling.md
git show 9fab2083cd74fcaca28cb6589cf8705e0e8ddd3c:specs/car-003-evaluation-runner-scoring/checklists/llm-integration.md
git show 9fab2083cd74fcaca28cb6589cf8705e0e8ddd3c:specs/car-003-evaluation-runner-scoring/checklists/performance.md
git checkout 9fab2083cd74fcaca28cb6589cf8705e0e8ddd3c -- specs/car-003-evaluation-runner-scoring
```

## Reviewability And Size Exception

CAR-003 ran as `one-navigable-PR` with an operator-ratified three-slice review
order and roadmap Work Package A kept intact as slice 1. The final gate recorded
a size-only block: 81 files changed, 21,986 lines added, against the 800-LOC and
25-file thresholds. The composition explains it — one authored production source
file (`materializer.py`, 247 lines), 27 generated or regenerated artifacts, 38
repository-only harness files, and 32 specification and process documents. The
typed size exception is preserved at
`docs/ai/specs/.process/CAR-003-size-exception.md`. That decision is historical
record; this cleanup does not revisit it.

## Contract Relocation Required By This Archive

CAR-003 kept exactly one copy of each contract schema, spec-scoped, and pointed
live code at it. `CAR-003-twin-handoff.md` records that as deliberate: *"CAR-003
has no runtime-harness copy of this schema to keep in sync"*, with enforcement in
the library and the test pinning the schema to the library. Archiving the folder
would therefore have deleted load-bearing files, not design exhaust.

The nine schemas were **moved** - not copied - to
`tests/speckit-pro/layer6-efficiency/contracts-claude/`, so CAR-003 still has a
single source of truth and does not acquire the twin's two-copy shape. The `$id`
values stay under `.../car-003/...`, so no namespace collides with either
`g56r-003` or `g56r-003/runtime`.

Six call sites were repointed from
`REPO_ROOT / "specs" / "car-003-evaluation-runner-scoring" / "contracts"` to the
new root:

| Site | Kind |
|---|---|
| `tests/speckit-pro/layer6-efficiency/lib/claude_treatment_runner.py` | live Layer 6 library |
| `tests/speckit-pro/unit/test-experiment-policy-partitions.py` | test |
| `tests/speckit-pro/unit/test-role-corpus-governance.py` | test |
| `tests/speckit-pro/unit/test-score-bundle-adjudication.py` | test |
| `tests/speckit-pro/unit/test-analysis-decision-ladder.py` | test |
| `tests/speckit-pro/unit/test-successor-capability-freeze.py` | test |

`owning_spec="car-003-evaluation-runner-scoring"` record values were left
unchanged; they name the owning spec historically and are not filesystem paths.

Known follow-up, not fixed here: `car-003-additive-records.schema.json` couples a
repository-authored filename to a spec ID, which `AGENTS.md` disallows, and it
has no Codex mirror. Renaming it touches `$ref` resolution and belongs with
CAR-012 rather than an archive sweep.

## Changed Files and Impact

| Artifact | Change |
|---|---|
| `.specify/memory/{spec,plan,changelog}.md` | Append shipped behavior, architecture, provenance, and cleanup state |
| Claude routing roadmap and MOC | Mark CAR-003 archived and CAR-004 ready; repoint CAR-012 Key Files |
| `.specify/autopilot-state.json` | Record the completed archive sweep for the Claude lane |
| `tests/speckit-pro/layer6-efficiency/contracts-claude/` | New home for the nine relocated contract schemas |
| Six Claude-lane call sites | Repoint the contract root out of `specs/**` |
| `specs/car-003-evaluation-runner-scoring/` | Remove completed active spec residue |

## Cleanup Decision

- **cleanupApplied**: true
- **cleanupCommand**: `git rm -r specs/car-003-evaluation-runner-scoring`
- **cleanupBranch**: `chore/archive-merged-specs-20260727`
- **blockedBy**: none
- **Downstream state**: CAR-004 is ready. CAR-012 remains pending as the
  cross-platform reconciliation joint change with G56R-012; its source record,
  `docs/ai/specs/.process/CAR-003-twin-handoff.md`, is preserved outside
  `specs/**` and is unaffected by this cleanup.

## Verification Commands

- `python3 -m json.tool .specify/autopilot-state.json`
- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- runner operation `generate-spec-index-write` in apply mode
- runner helper `generate-spec-index-check`
- `pnpm --dir docs-site reference:check`
- `python3 tests/speckit-pro/run-all.py --layer 1`
- `python3 tests/speckit-pro/run-all.py`
- `git diff --check`
- final active-spec inventory audit

## Verification Results

Recorded in the companion G56R-003 report for this sweep; both specs were
archived in one cleanup branch and verified together.

## Constitution Compliance

PASS by scope. Cleanup preserves durable evidence, changes no plugin version or
runtime payload, keeps repository tooling on Python, and retains all merged
source through immutable git provenance.
