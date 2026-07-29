# Archival Report - G56R-004 Policy Controls and Adaptive Comparators

## Mode

- **archiveMode**: merged-spec cleanup sweep
- **dryRun**: false
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true
- **excludedCurrentSpec**: none

## Provenance

- **Source spec path**:
  `specs/g56r-004-policy-controls-adaptive-comparators/`
- **PR URL**:
  https://github.com/racecraft-lab/racecraft-plugins-public/pull/403
- **PR title**:
  `feat(g56r-004): add policy controls and adaptive comparators`
- **Merged at**: `2026-07-29T19:36:55Z`
- **Merge commit**: `77e7dfff017597c6c93118a30eeb2b1c08d734de`
- **Head branch**: `g56r-004-policy-controls-adaptive-comparators`
- **Base branch**: `main`
- **Cleanup branch**: `codex/archive-g56r-004-post-merge`
- **Workflow preserved**:
  `docs/ai/specs/.process/G56R-004-workflow.md`
- **Design concept preserved**:
  `docs/ai/specs/.process/G56R-004-design-concept.md`
- **Operator runbook preserved**:
  `docs/ai/specs/.process/G56R-004-live-smoke-runbook.md`
- **CI runs**:
  [PR Checks](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/30479771646),
  [Container Preflight](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/30479680702),
  and CodeQL runs
  [30479676370](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/30479676370)
  and
  [30479676853](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/30479676853)
- **CI / metadata gates**: every required PR check passed, including title,
  release-note, workflow, docs, artifact-consistency, plugin, full-suite,
  CodeQL, and Linux amd64/arm64 container checks. Windows x64 advisory smoke
  passed; Windows ARM64 advisory smoke was skipped in its normal unlabelled
  runner state.
- **Argos build/review URL**: N/A
- **Metadata gates**: pass
- **Artifact manifest**: N/A; committed repository evidence is canonical
- **Screenshot retention**: N/A
- **Expiration risk**: committed source and process evidence has no artifact
  retention dependency

## Feature Summary

G56R-004 shipped the Codex-local policy-control and adaptive-comparison harness
mirroring CAR-004 without changing production routing. It freezes exactly
`unpinned`, `adaptive`, and `justified_high_effort`, validates their inherited,
ladder, and parent-plus-children semantics, and evaluates comparison evidence
only after eligibility floors pass.

The comparison contract is direction-aware across eight dimensions, uses
predeclared margins and claim classes, and fails closed on empty or malformed
handoffs. Deterministic replay produces no scored outcome evidence. Reserved
G56R-011 objectives, frozen G56R-003/CAR-003/CAR-004 drift, raw captures,
missing exact-treatment evidence, and invalid cache observations are rejected.

Post-merge review remediation made twin reconciliation evidence-derived rather
than expected-value-derived, separated the six divergence buckets, rejected
cyclic spawn relationships and malformed cache maps, and preserved the closed
privacy boundary.

## Known Gap Carried Forward

The three operator-authorized ChatGPT sign-in smokes were not run. SC-014,
SC-015, and SC-016 remain partial for live observation. Deterministic planning,
authorization-withheld/refusal handling, bounds, sealing, exact-treatment
read-back rules, cache-isolation validation, and privacy checks pass, but this
archive claims no live or off-box result.

The procedure that may close this gap is preserved at
`docs/ai/specs/.process/G56R-004-live-smoke-runbook.md`.

## Runbook Relocation

The feature `quickstart.md` was forward-looking operator evidence rather than
pure planning exhaust: it contains the only committed G56R-004 live-smoke
procedure. It was moved to
`docs/ai/specs/.process/G56R-004-live-smoke-runbook.md`, updated to use `main`
at or after the merge commit, and given direct git recovery commands.

No contract relocation was required. The two machine contracts, four fixtures,
three helpers, and three focused owners were authored directly under
`tests/speckit-pro/`. A repository-wide exact-path search found no live code,
test, or script reader of the active spec directory before removal. The PR
packet and remaining spec-local documents are historical exhaust recoverable
from git.

## Canonical Shipped Artifacts

- `tests/speckit-pro/layer6-efficiency/contracts-codex-specification/control-comparison.schema.json`
- `tests/speckit-pro/layer6-efficiency/contracts-codex-specification/policy-control-registry.schema.json`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/control-comparison.json`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/partition-registry-entries.json`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/policy-control-registry.json`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/replay-cases.json`
- `tests/speckit-pro/layer6-efficiency/lib/codex_control_comparison.py`
- `tests/speckit-pro/layer6-efficiency/lib/codex_control_smoke.py`
- `tests/speckit-pro/layer6-efficiency/lib/codex_policy_controls.py`
- `tests/speckit-pro/unit/test-control-comparison-dominance.py`
- `tests/speckit-pro/unit/test-policy-control-contracts.py`
- `tests/speckit-pro/unit/test-twin-handoff-completeness.py`
- `docs-site/src/content/docs/reference/tests.md`
- `docs/ai/specs/.process/G56R-004-workflow.md`
- `docs/ai/specs/.process/G56R-004-design-concept.md`
- `docs/ai/specs/.process/G56R-004-live-smoke-runbook.md`

`tests/speckit-pro/suite-manifest.json` remains the authoritative owner map and
did not require a G56R-004 change.

## Recovery Commands

```text
git show 77e7dfff017597c6c93118a30eeb2b1c08d734de:specs/g56r-004-policy-controls-adaptive-comparators/spec.md
git show 77e7dfff017597c6c93118a30eeb2b1c08d734de:specs/g56r-004-policy-controls-adaptive-comparators/plan.md
git show 77e7dfff017597c6c93118a30eeb2b1c08d734de:specs/g56r-004-policy-controls-adaptive-comparators/tasks.md
git show 77e7dfff017597c6c93118a30eeb2b1c08d734de:specs/g56r-004-policy-controls-adaptive-comparators/research.md
git show 77e7dfff017597c6c93118a30eeb2b1c08d734de:specs/g56r-004-policy-controls-adaptive-comparators/data-model.md
git show 77e7dfff017597c6c93118a30eeb2b1c08d734de:specs/g56r-004-policy-controls-adaptive-comparators/quickstart.md
git show 77e7dfff017597c6c93118a30eeb2b1c08d734de:specs/g56r-004-policy-controls-adaptive-comparators/retrospective.md
git show 77e7dfff017597c6c93118a30eeb2b1c08d734de:specs/g56r-004-policy-controls-adaptive-comparators/verify-tasks-report.md
git show 77e7dfff017597c6c93118a30eeb2b1c08d734de:specs/g56r-004-policy-controls-adaptive-comparators/SPEC-MOC.md
git show 77e7dfff017597c6c93118a30eeb2b1c08d734de:specs/g56r-004-policy-controls-adaptive-comparators/.process/pr-review-traceability.md
git show 77e7dfff017597c6c93118a30eeb2b1c08d734de:specs/g56r-004-policy-controls-adaptive-comparators/contracts/control-comparison.md
git show 77e7dfff017597c6c93118a30eeb2b1c08d734de:specs/g56r-004-policy-controls-adaptive-comparators/contracts/policy-control-registry.md
git show 77e7dfff017597c6c93118a30eeb2b1c08d734de:specs/g56r-004-policy-controls-adaptive-comparators/contracts/smoke-replay.md
git show 77e7dfff017597c6c93118a30eeb2b1c08d734de:specs/g56r-004-policy-controls-adaptive-comparators/checklists/data-integrity.md
git show 77e7dfff017597c6c93118a30eeb2b1c08d734de:specs/g56r-004-policy-controls-adaptive-comparators/checklists/error-handling.md
git show 77e7dfff017597c6c93118a30eeb2b1c08d734de:specs/g56r-004-policy-controls-adaptive-comparators/checklists/llm-integration.md
git show 77e7dfff017597c6c93118a30eeb2b1c08d734de:specs/g56r-004-policy-controls-adaptive-comparators/checklists/performance.md
git checkout 77e7dfff017597c6c93118a30eeb2b1c08d734de -- specs/g56r-004-policy-controls-adaptive-comparators
```

## Changed Files and Impact

| Artifact | Change |
|---|---|
| `.specify/memory/{spec,plan,changelog}.md` | Append shipped behavior, architecture, provenance, and cleanup state |
| `.specify/memory/archive-reports/2026-07-29-g56r-004-post-merge-hygiene.md` | This report |
| `.specify/autopilot-state.json` | Move project archive state to G56R-004 |
| `docs/ai/specs/.process/autopilot-state.json` | Mark G56R-004 completed/archived and record the applied sweep |
| Codex routing roadmap and MOC | Mark G56R-004 complete/archived and G56R-005 ready |
| `docs/ai/specs/.process/G56R-004-live-smoke-runbook.md` | Preserve the operator-only procedure from the feature quickstart |
| `docs/ai/specs/.process/G56R-004-workflow.md` | Record the preserved runbook location |
| `specs/g56r-004-policy-controls-adaptive-comparators/` | Remove completed active spec residue |

## Cleanup Decision

- **cleanupApplied**: true
- **cleanupOperation**: move the forward-looking quickstart with `apply_patch`,
  then remove the remaining tracked files under
  `specs/g56r-004-policy-controls-adaptive-comparators/` with `apply_patch`;
  remove the resulting empty directories with explicit `rmdir` arguments
- **cleanupBranch**: `codex/archive-g56r-004-post-merge`
- **blockedBy**: none
- **Downstream state**: G56R-005 is ready because PR #403 provides the
  canonical control, comparison, replay, smoke-validation, and test evidence.
  G56R-012 remains the separate cross-platform reconciliation joint change with
  CAR-012.

## Verification Commands

- `python3 -m json.tool .specify/autopilot-state.json`
- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- SpecKit runner operation `generate-spec-index-write` in apply mode
- SpecKit runner helper `generate-spec-index-check`
- final `find specs -mindepth 1 -maxdepth 4 -print` audit
- stale active-path and roadmap-status `rg` scans
- `python3 tests/speckit-pro/run-all.py --layer 1`
- `python3 tests/speckit-pro/run-all.py`
- release-readiness runner gate for
  `docs(g56r-004): archive post-merge state`
- `python3 scripts/compose-release-notes.py --validate-pr`
- `git diff --check`

## Verification Results

All checks ran from the cleanup branch after the active-spec removal and before
commit.

| Check | Result |
|---|---|
| Active spec inventory | `specs/.gitkeep` only |
| `.specify/autopilot-state.json` | valid JSON |
| `docs/ai/specs/.process/autopilot-state.json` | valid JSON |
| `generate-spec-index-write` (apply) | one write applied to `docs/ai/specs/codex-gpt-5-6-agent-routing-roadmap-MOC.md` |
| `generate-spec-index-check` | exit 0 — index current, all in-scope maps up to date |
| Stale active-path scan outside archive/process evidence | zero live code, test, or script references |
| `python3 tests/speckit-pro/run-all.py --layer 1` | 1428/1428 |
| `python3 tests/speckit-pro/run-all.py` | 5345/5345 (L1 1428, L4 3731, L5 186) |
| G56R-004 focused owners within the full suite | 730/730 policy, 172/172 comparison, 201/201 twin |
| Release-readiness title gate | pass for `docs(g56r-004): archive post-merge state` |
| Release-note validation | pass — non-releasable conventional-commit type |
| `git diff --check` | clean |

Docs reference generation was not required: this cleanup changed no tracked
`.md`, `.py`, or `.sh` under `tests/speckit-pro/`, no plugin inventory, and no
generated docs reference page. The existing reference page remains the merged
PR #403 artifact and the full suite validates its structural contract.

## Constitution Compliance

PASS by scope. The cleanup preserves durable evidence, changes no plugin
version or runtime payload, adds no active Bash or `jq` dependency, retains all
merged source through immutable git provenance, and leaves the full
Python-authoritative suite as the completion gate.
