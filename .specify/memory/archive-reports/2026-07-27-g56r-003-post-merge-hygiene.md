# Archival Report - G56R-003 Evaluation Runner, Fixtures, Scoring, and Statistical Analysis

## Mode

- **archiveMode**: merged-spec cleanup sweep
- **dryRun**: false
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true
- **excludedCurrentSpec**: none

## Provenance

- **Source spec path**: `specs/g56r-003-evaluation-runner-scoring/`
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/386
- **PR title**: `feat(g56r-003): add evaluation runner scoring`
- **Merged at**: `2026-07-27T03:11:13Z`
- **Merge commit**: `dcceef86daed97fe42e81a43c90e82556457dc48`
- **Head branch**: `g56r-003-evaluation-runner-scoring`
- **Base branch**: `main`
- **Workflow preserved**: `docs/ai/specs/.process/G56R-003-workflow.md`
- **Design concept preserved**: `docs/ai/specs/.process/G56R-003-design-concept.md`
- **CI / metadata gates**: all required PR checks passed, including
  `validate-pr-title`, `validate-release-note`, `validate-workflows`,
  `validate-docs`, `artifact-consistency`, `test (speckit-pro)`,
  `validate-plugins`, CodeQL, and Linux/Windows container preflight.
- **Screenshot retention**: N/A
- **Expiration risk**: committed source and process evidence has no artifact
  retention dependency.

## Feature Summary

G56R-003 shipped the Codex-side evaluation platform mirroring CAR-003. It
delivered the shipped canonical agent-materialization module, the twelve-role
governed qualification corpus with a single shared manifest, closed contract
schemas for role corpus, experiment policy, calibration protocol, score bundle,
analysis plan and decision, successor capability freeze, and environment; plus
blinded scoring with a frozen third adjudicator, a deterministic statistical
ladder (floors, then paired cluster-adjusted non-inferiority, then unweighted
raw Pareto), and content-addressed offline replay.

Like its twin, it preserves the no-qualification boundary: only non-eligible
calibration partitions are accepted, and outputs are limited to
calibration-complete, inconclusive, or invalid. It cannot produce final route
policy, defaults, aggregates, or release outputs.

## Canonical Shipped Artifacts

- `speckit-pro/speckit_pro_runner/agent_materialization.py` (mirrored into
  `dist/claude/` and `dist/codex/`)
- `docs/ai/research/codex-g56r-003-effort-ladder.json`
- `tests/speckit-pro/layer6-efficiency/contracts/` — nine closed schemas
  (`analysis-decision`, `analysis-plan`, `calibration-completion`,
  `calibration-protocol`, `environment-contract`, `experiment-policy`,
  `role-corpus`, `score-bundle`, `successor-capability-freeze`)
- `tests/speckit-pro/layer6-efficiency/lib/codex_successor_capability.py`
- `tests/speckit-pro/layer6-efficiency/lib/qualification_contracts.py`
- `tests/speckit-pro/layer6-efficiency/lib/qualification_corpus.py`
- `tests/speckit-pro/layer6-efficiency/lib/qualification_environment.py`
- `tests/speckit-pro/layer6-efficiency/lib/qualification_replay.py`
- `tests/speckit-pro/layer6-efficiency/lib/qualification_scoring.py`
- `tests/speckit-pro/layer6-efficiency/lib/qualification_statistics.py`
- `tests/speckit-pro/layer6-efficiency/lib/treatment_trace_json_schema.py`
- `tests/speckit-pro/layer6-efficiency/run-codex-qualification.py`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex/` — twelve per-role
  fixtures plus `corpus-manifest.json`
- `tests/speckit-pro/unit/test-agent-materialization.py`
- `tests/speckit-pro/unit/test-codex-qualification-contracts.py`
- `tests/speckit-pro/unit/test-codex-qualification-corpus.py`
- `tests/speckit-pro/unit/test-codex-qualification-scoring.py`
- `tests/speckit-pro/unit/test-codex-qualification-statistics.py`
- `tests/speckit-pro/unit/test-codex-successor-capability.py`
- `docs/ai/specs/.process/G56R-003-workflow.md`
- `docs/ai/specs/.process/G56R-003-design-concept.md`

## Recovery Commands

```text
git show dcceef86daed97fe42e81a43c90e82556457dc48:specs/g56r-003-evaluation-runner-scoring/spec.md
git show dcceef86daed97fe42e81a43c90e82556457dc48:specs/g56r-003-evaluation-runner-scoring/plan.md
git show dcceef86daed97fe42e81a43c90e82556457dc48:specs/g56r-003-evaluation-runner-scoring/tasks.md
git show dcceef86daed97fe42e81a43c90e82556457dc48:specs/g56r-003-evaluation-runner-scoring/research.md
git show dcceef86daed97fe42e81a43c90e82556457dc48:specs/g56r-003-evaluation-runner-scoring/data-model.md
git show dcceef86daed97fe42e81a43c90e82556457dc48:specs/g56r-003-evaluation-runner-scoring/quickstart.md
git show dcceef86daed97fe42e81a43c90e82556457dc48:specs/g56r-003-evaluation-runner-scoring/SPEC-MOC.md
git show dcceef86daed97fe42e81a43c90e82556457dc48:specs/g56r-003-evaluation-runner-scoring/verify-tasks-report.md
git show dcceef86daed97fe42e81a43c90e82556457dc48:specs/g56r-003-evaluation-runner-scoring/contracts/calibration-protocol.schema.json
git show dcceef86daed97fe42e81a43c90e82556457dc48:specs/g56r-003-evaluation-runner-scoring/contracts/environment-contract.schema.json
git show dcceef86daed97fe42e81a43c90e82556457dc48:specs/g56r-003-evaluation-runner-scoring/checklists/requirements.md
git show dcceef86daed97fe42e81a43c90e82556457dc48:specs/g56r-003-evaluation-runner-scoring/checklists/data-integrity.md
git show dcceef86daed97fe42e81a43c90e82556457dc48:specs/g56r-003-evaluation-runner-scoring/checklists/error-handling.md
git show dcceef86daed97fe42e81a43c90e82556457dc48:specs/g56r-003-evaluation-runner-scoring/checklists/llm-integration.md
git show dcceef86daed97fe42e81a43c90e82556457dc48:specs/g56r-003-evaluation-runner-scoring/checklists/performance.md
git checkout dcceef86daed97fe42e81a43c90e82556457dc48 -- specs/g56r-003-evaluation-runner-scoring
```

## Contract Relocation Required By This Archive

G56R-003 carries two tiers by design: runtime contracts already in the test tree
at `tests/speckit-pro/layer6-efficiency/contracts/` (`$id` under
`.../g56r-003/runtime/...`), and specification-side copies that lived in the spec
folder (`$id` under `.../g56r-003/...`). Its library reads the runtime tier
through a test-tree-relative path, so no library reached into `specs/**`; only
the parity assertions did.

The nine specification-side schemas were **moved** to
`tests/speckit-pro/layer6-efficiency/contracts-codex-specification/`, preserving
the runtime-versus-specification pair that
`test_runtime_and_specification_contracts_have_distinct_schema_ids` and the
score-taxonomy divergence check exist to guard. That pair is the standing
evidence CAR-012 and G56R-012 reconcile, so it was preserved rather than
collapsed.

Two call sites were repointed:

| Site | Constant |
|---|---|
| `tests/speckit-pro/unit/test-codex-qualification-contracts.py` | `SPEC_CONTRACT_DIR` |
| `tests/speckit-pro/unit/test-codex-qualification-scoring.py` | `SPEC_SCORE_BUNDLE_SCHEMA_PATH` |

`tests/speckit-pro/layer6-efficiency/contracts/` was left untouched, so the ten
or so existing readers of the shared and runtime tiers are unaffected.

The duplicate-`$id` collision described in `CAR-003-twin-handoff.md` §4 was
already closed before merge: all nine runtime schemas carry `/runtime/` in their
`$id`, verified against the committed files during this sweep.

## Changed Files and Impact

| Artifact | Change |
|---|---|
| `.specify/memory/{spec,plan,changelog}.md` | Append shipped behavior, architecture, provenance, and cleanup state |
| Codex routing roadmap and MOC | Mark G56R-003 archived and G56R-004 ready; repoint G56R-012 Key Files |
| `docs/ai/specs/.process/autopilot-state.json` | Record the completed archive sweep for the Codex lane |
| `tests/speckit-pro/layer6-efficiency/contracts-codex-specification/` | New home for the nine relocated specification schemas |
| Two Codex-lane call sites | Repoint the specification contract paths out of `specs/**` |
| `specs/g56r-003-evaluation-runner-scoring/` | Remove completed active spec residue |

## Cleanup Decision

- **cleanupApplied**: true
- **cleanupCommand**: `git rm -r specs/g56r-003-evaluation-runner-scoring`
- **cleanupBranch**: `chore/archive-merged-specs-20260727`
- **blockedBy**: none
- **Downstream state**: G56R-004 is ready. G56R-012 remains pending as the
  cross-platform reconciliation joint change with CAR-012.

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

Results for the whole 2026-07-27 sweep, covering both CAR-003 and G56R-003:

- PASS: both `autopilot-state.json` files parse as valid JSON.
- PASS: SpecKit index write then check reported exit 0; both `GENERATED:INDEX`
  blocks are correctly empty now that no active spec remains.
- PASS: `pnpm --dir docs-site reference:check` reports pages current.
- PASS: the ten test files touched by the contract relocation all passed,
  including `test-analysis-decision-ladder` 314/314,
  `test-successor-capability-freeze` 201/201,
  `test-score-bundle-adjudication` 162/162, `test-role-corpus-governance`
  111/111, `test-experiment-policy-partitions` 91/91, and
  `test-exact-treatment-runner` 75/75.
- PASS: full deterministic suite `4240/4240` (L1 1428/1428, L4 2626/2626,
  L5 186/186), zero failures.
- PASS: `git diff --check` found no whitespace errors.
- PASS: active spec inventory contains only `specs/.gitkeep`.
- PASS: the PR title validated against the live release-readiness gate, exit 0.

## Constitution Compliance

PASS by scope. Cleanup preserves durable evidence, changes no plugin version or
runtime payload, keeps repository tooling on Python, and retains all merged
source through immutable git provenance.
