# Archival Report - CAR-004 Policy Controls and Adaptive Comparators

## Mode

- **archiveMode**: merged-spec cleanup sweep
- **dryRun**: false
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true
- **excludedCurrentSpec**: none

## Provenance

- **Source spec path**: `specs/car-004-policy-controls-comparators/`
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/401
- **PR title**: `feat(car-004): add the three routing policy controls and their
  comparison rules`
- **Merged at**: `2026-07-29T00:58:26Z`
- **Merge commit**: `8b224ce8d1fbaba89606772a4d51401ac754a70b`
- **Head branch**: `car-004-policy-controls-comparators`
- **Base branch**: `main`
- **Workflow preserved**: `docs/ai/specs/.process/CAR-004-workflow.md`
- **Design concept preserved**: `docs/ai/specs/.process/CAR-004-design-concept.md`
- **Additional process evidence preserved**:
  `docs/ai/specs/.process/CAR-004-twin-handoff.md` and
  `docs/ai/specs/.process/CAR-004-live-smoke-runbook.md`
- **CI / metadata gates**: every required PR check passed —
  `validate-pr-title`, `validate-release-note`, `validate-workflows`,
  `validate-docs`, `artifact-consistency`, `test (speckit-pro)`,
  `validate-plugins`, CodeQL over actions/javascript-typescript/python, the
  Linux amd64 and arm64 heavy container preflights, and the Windows x64
  advisory smoke. Only `Windows ARM64 advisory smoke` was skipped, which is its
  normal unlabelled-runner state.
- **Screenshot retention**: N/A
- **Expiration risk**: committed source and process evidence has no artifact
  retention dependency.

## Feature Summary

CAR-004 froze the three AC-2.17 policy controls — `unpinned`, `adaptive`, and
`orchestration-changing` — and the comparison rule CAR-011 will later apply to
them, as two additive content-addressed contracts with committed frozen
instances, standard-library validators, deterministic replay fixtures, a
reserved-partition guard, and a machine-verified twin-handoff record.

The point of the spec is ordering: the comparison rule is frozen *before*
anybody can see which side wins, so the yardstick cannot be authored after the
results are visible. No CAR-004 artifact states or implies which side wins;
CAR-011 owns the comparison and the answer. The reserved partition is guarded so
the final comparison cannot quietly reuse workload that selection already saw.

The change is validation assets only: zero production files, nothing under
`speckit-pro/` touched, no shipped default and no payload affected. The
comparison procedure runs in three ordered stages — eligibility floors, Pareto
dominance over eight frozen dimensions, then a materiality margin evaluated in
exact decimal rather than binary floating point.

A max-effort review of the branch reproduced fifteen defects by execution before
merge; fourteen were code and one was documentation, and all were fixed with
regression coverage in commit `f8ceca88`. The three that mattered most: the
shared fail-closed schema engine silently ignored six JSON Schema keywords that
sibling frozen contracts use, the FR-005a byte-drift guard was never called from
any consumer path, and a smoke record that relabelled an unevidenced run still
sealed as admitted.

## Known Gap Carried Forward

CAR-004 merged with task **T062** unrun. The three bounded live smokes are
developer-local, subscription-authenticated, and executable only by a person, so
six success criteria ship with no evidence behind them, automated or manual:

| Criterion | What is unproven |
|---|---|
| SC-009 | Each smoke completes inside all four declared bounds |
| SC-026 | Each smoke records its named observable read back |
| SC-027 | Every smoke record carries the frozen no-subagent-override proof |
| SC-029 | All four bounds evaluate over the whole parent-plus-children unit |
| SC-030 | Every accepted smoke records a subscription authentication mode |
| SC-031 | All three smoke-arm pairs record disjoint cache state |

This gap was named in the PR body and is restated here so archiving does not
bury it. The operator runbook that closes it is preserved — see the next section.

## Runbook Relocation Required By This Archive

`specs/car-004-policy-controls-comparators/.process/CAR-004-live-smoke-runbook.md`
was forward-looking operator evidence, not design exhaust: it is the only
instruction set for the six criteria above, and the preserved
`CAR-004-workflow.md` pointed at it. Deleting the spec folder would have deleted
the runbook and left a dangling pointer behind.

The runbook was **moved** — not copied — to
`docs/ai/specs/.process/CAR-004-live-smoke-runbook.md`, alongside the workflow,
design-concept, and twin-handoff records it belongs with. Three references
inside it were repointed at git provenance because their targets are archived:
the prerequisite branch note now names `main` at or after `8b224ce8`, and the
`tasks.md` and `quickstart.md` pointers became `git show` commands against the
merge commit. The workflow file's pointer was repointed to the new path.

The PR packet under `.process/pr-packets/` is exhaust and was removed with the
folder, matching the CAR-003 precedent.

No code relocation was needed. Unlike CAR-003, CAR-004 never kept contract
schemas inside its spec folder — both JSON Schema documents were authored
directly into `tests/speckit-pro/layer6-efficiency/contracts-claude/`, and the
spec-folder `contracts/` directory held only the three Markdown design
documents. A tree-wide search for the bare directory name found zero readers
outside `specs/**` before removal.

## Canonical Shipped Artifacts

- `tests/speckit-pro/layer6-efficiency/contracts-claude/policy-control-registry.schema.json`
- `tests/speckit-pro/layer6-efficiency/contracts-claude/control-comparison.schema.json`
- `tests/speckit-pro/layer6-efficiency/fixtures-controls/policy-control-registry.json`
- `tests/speckit-pro/layer6-efficiency/fixtures-controls/control-comparison.json`
- `tests/speckit-pro/layer6-efficiency/fixtures-controls/control-replay.json`
- `tests/speckit-pro/layer6-efficiency/fixtures-controls/partition-registry-entries.json`
- `tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py`
- `tests/speckit-pro/layer6-efficiency/lib/claude_control_comparison.py`
- `tests/speckit-pro/layer6-efficiency/run-control-smoke.py`
- `tests/speckit-pro/unit/test-policy-control-contracts.py`
- `tests/speckit-pro/unit/test-control-comparison-dominance.py`
- `tests/speckit-pro/unit/test-twin-handoff-completeness.py`
- `tests/speckit-pro/suite-manifest.json` (three new Layer 4 registrations)
- `docs/ai/specs/.process/CAR-004-workflow.md`
- `docs/ai/specs/.process/CAR-004-design-concept.md`
- `docs/ai/specs/.process/CAR-004-twin-handoff.md`
- `docs/ai/specs/.process/CAR-004-live-smoke-runbook.md`

Per-run smoke evidence stays operator-only under the existing `layer6-efficiency`
gitignore; nothing from `results/` is or was committed.

## Recovery Commands

```text
git show 8b224ce8d1fbaba89606772a4d51401ac754a70b:specs/car-004-policy-controls-comparators/spec.md
git show 8b224ce8d1fbaba89606772a4d51401ac754a70b:specs/car-004-policy-controls-comparators/plan.md
git show 8b224ce8d1fbaba89606772a4d51401ac754a70b:specs/car-004-policy-controls-comparators/tasks.md
git show 8b224ce8d1fbaba89606772a4d51401ac754a70b:specs/car-004-policy-controls-comparators/research.md
git show 8b224ce8d1fbaba89606772a4d51401ac754a70b:specs/car-004-policy-controls-comparators/data-model.md
git show 8b224ce8d1fbaba89606772a4d51401ac754a70b:specs/car-004-policy-controls-comparators/quickstart.md
git show 8b224ce8d1fbaba89606772a4d51401ac754a70b:specs/car-004-policy-controls-comparators/retrospective.md
git show 8b224ce8d1fbaba89606772a4d51401ac754a70b:specs/car-004-policy-controls-comparators/verify-tasks-report.md
git show 8b224ce8d1fbaba89606772a4d51401ac754a70b:specs/car-004-policy-controls-comparators/SPEC-MOC.md
git show 8b224ce8d1fbaba89606772a4d51401ac754a70b:specs/car-004-policy-controls-comparators/contracts/policy-control-registry.md
git show 8b224ce8d1fbaba89606772a4d51401ac754a70b:specs/car-004-policy-controls-comparators/contracts/control-comparison.md
git show 8b224ce8d1fbaba89606772a4d51401ac754a70b:specs/car-004-policy-controls-comparators/contracts/validator-api.md
git show 8b224ce8d1fbaba89606772a4d51401ac754a70b:specs/car-004-policy-controls-comparators/checklists/requirements.md
git show 8b224ce8d1fbaba89606772a4d51401ac754a70b:specs/car-004-policy-controls-comparators/checklists/data-integrity.md
git show 8b224ce8d1fbaba89606772a4d51401ac754a70b:specs/car-004-policy-controls-comparators/checklists/error-handling.md
git show 8b224ce8d1fbaba89606772a4d51401ac754a70b:specs/car-004-policy-controls-comparators/checklists/llm-integration.md
git checkout 8b224ce8d1fbaba89606772a4d51401ac754a70b -- specs/car-004-policy-controls-comparators
```

## Reviewability

CAR-004 ran as a single slice. The setup-mode reviewability gate read clean at
250 reviewable LOC, zero production files, one primary surface
(`harness/fixtures`), no warnings and no blockers. Diff-mode reviewability was
deferred on the authoritative runner, which supports setup mode only; the
deferral and the direct measurement are recorded in the archived `plan.md` under
"Reviewability Budget". The realized change set was 33 files, dominated by
declarative JSON, with production files at zero. That decision is historical
record; this cleanup does not revisit it.

## Changed Files and Impact

| Artifact | Change |
|---|---|
| `.specify/memory/{spec,plan,changelog}.md` | Append shipped behavior, architecture, provenance, and cleanup state |
| `.specify/memory/archive-reports/2026-07-28-car-004-post-merge-hygiene.md` | This report |
| `.specify/autopilot-state.json` | Move the Claude lane from CAR-003 to CAR-004 archived, and record this sweep |
| `.specify/feature.json` | No repository change — gitignored local state; the stale worktree copy naming the removed directory was deleted |
| Claude routing roadmap and MOC | Mark CAR-004 complete and archived, and CAR-005 ready |
| `docs/ai/specs/.process/CAR-004-live-smoke-runbook.md` | New home for the operator runbook that closes the six unevidenced criteria |
| `docs/ai/specs/.process/CAR-004-workflow.md` | Repoint the runbook reference at the preserved path |
| `specs/car-004-policy-controls-comparators/` | Remove completed active spec residue |

## Cleanup Decision

- **cleanupApplied**: true
- **cleanupCommand**: `git rm -r specs/car-004-policy-controls-comparators`
- **cleanupBranch**: `chore/archive-merged-specs-20260728`
- **blockedBy**: none
- **Downstream state**: CAR-005 (Model Availability, Fallback, and Recovery
  Simulation) is ready; its dependency on CAR-004 is satisfied by canonical
  contract, fixture, and validator paths under `tests/speckit-pro/`. CAR-012
  remains pending as the cross-platform reconciliation joint change with
  G56R-012, unaffected by this cleanup. The roadmap's smoke-authentication
  prose for CAR-005 through CAR-011 still predates the 2026-07-26 PRD AC-2.19
  amendment that forbids API-key authentication; CAR-004 corrected it inside its
  own spec, and correcting the roadmap belongs to whoever scaffolds CAR-005.

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

All run from the cleanup branch after the removal, before commit.

| Check | Result |
|---|---|
| Active spec inventory | `specs/.gitkeep` only |
| `python3 -m json.tool .specify/autopilot-state.json` | parses |
| `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json` | parses |
| `generate-spec-index-write` (apply) | one planned write applied, `docs/ai/specs/claude-agent-routing-roadmap-MOC.md` |
| `generate-spec-index-check` | exit 0 — index current, all in-scope maps up to date |
| `pnpm --dir docs-site reference:check` | reference pages are current |
| `python3 tests/speckit-pro/run-all.py --layer 1` | 1428/1428 |
| `python3 tests/speckit-pro/run-all.py` | 4948/4948 (L1 1428, L4 3334, L5 186) |
| `git diff --check` and `git diff --cached --check` | clean |

Layers 7 and 8 were not re-run: nothing under `tests/speckit-pro/` changed in
this cleanup, and both were green on the merge commit.

The generated index zone in the roadmap MOC is now empty, which is the correct
rendering when no active spec remains. `.specify/feature.json` needed no
repository change — it is gitignored local state — but the stale copy naming the
removed directory was deleted from the worktree.

## Constitution Compliance

PASS by scope. Cleanup preserves durable evidence, changes no plugin version or
runtime payload, keeps repository tooling on Python, and retains all merged
source through immutable git provenance.
