# Archival Report - G56R-005 Model Availability, Fallback, and Recovery Simulation

## Mode

- **archiveMode**: merged-spec cleanup sweep
- **dryRun**: false
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true
- **excludedCurrentSpec**: none

## Provenance

- **Source spec path**:
  `specs/g56r-005-model-availability-fallback-recovery/`
- **PR URL**:
  https://github.com/racecraft-lab/racecraft-plugins-public/pull/487
- **PR title**:
  `feat(g56r-005): Add model availability fallback and recovery simulation`
- **Merged at**: `2026-08-23T01:31:23Z`
- **Merge commit**: `85762d5a7033981da1fdf6a18b5913c83fc6d9a5`
- **Merge tree**: `098be1bdd1e448335a32f9178dd6dbd463b95f05`
- **Head branch**: `g56r-005-model-availability-fallback-recovery`
- **Base branch**: `main`
- **Cleanup branch**: `codex/archive-g56r-005-post-merge`
- **Workflow preserved**:
  `docs/ai/specs/.process/G56R-005-workflow.md`
- **Design concept preserved**:
  `docs/ai/specs/.process/G56R-005-design-concept.md`
- **Manual UAT preserved**:
  `docs/ai/specs/.process/G56R-005-manual-uat.md`
- **Retrospective preserved**:
  `docs/ai/specs/.process/G56R-005-retrospective.md`
- **CI runs**:
  [final PR Checks](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/32610266296)
  and
  [Container Preflight](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/32601363855);
  CodeQL completed successfully on the merged head
- **CI / metadata gates**: the final exact-head run passed title, release-note,
  workflow, docs, artifact-consistency, full-suite, plugin, and CodeQL checks.
  Linux amd64/arm64 and Windows x64 preflight checks passed; Windows ARM64 was
  skipped in its normal unlabelled-runner state. Earlier release-note failures
  were superseded by the final successful run.
- **Argos build/review URL**: N/A
- **Metadata gates**: pass
- **Artifact manifest**: N/A; committed repository evidence is canonical
- **Screenshot retention**: generated HTML review pages are planning exhaust
  recoverable from the merge commit; no remote screenshot retention is required
- **Expiration risk**: committed source and process evidence has no artifact
  retention dependency

## Feature Summary

G56R-005 shipped deterministic, repository-local evidence for preferred-model
absence, unsupported effort, probe failure, ordered fallback evaluation,
service-reroute attribution, strict-override rejection, optional-helper
degradation, bounded harness execution, and required-agent recovery in a
temporary fake home.

The feature deliberately makes no live model-availability claim and changes no
production route policy, installer, manifest, release version, or user-home
state. Route Resolution Reports and Recovery Records are closed, schema-bound,
and byte-stable. The corpus is bound to the current source roster so roster drift
forces explicit review instead of silently changing treatment.

All 25 tasks, 22 functional requirements, and 9 success criteria completed.
Focused verification passed 35/35, and the pre-merge authoritative suite passed
7663/7663. Manual UAT found one unsafe generated-title path; the remediated
static-title fill contract was retested successfully.

## Preserved Process Evidence

The workflow and design concept already lived under the durable
`docs/ai/specs/.process/` boundary and remain there. This cleanup moved the
manual UAT runbook and retrospective to the same boundary before removing the
active spec directory.

The implementation notes, PR-packet files, planning documents, checklists,
markdown contract, quickstart, and generated HTML review pages are historical
exhaust. No surviving live code, test, script, roadmap, or process record reads
their old active-spec paths. Every tracked byte remains recoverable through the
commands below.

## Canonical Shipped Artifacts

- `tests/speckit-pro/layer6-efficiency/contracts-codex-fallback/route-policy.schema.json`
- `tests/speckit-pro/layer6-efficiency/contracts-codex-fallback/route-resolution-report.schema.json`
- `tests/speckit-pro/layer6-efficiency/contracts-codex-fallback/recovery-record.schema.json`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex-fallback/fallback-recovery-corpus.json`
- `tests/speckit-pro/layer6-efficiency/lib/codex_route_fallback.py`
- `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py`
- `tests/speckit-pro/suite-manifest.json`
- `docs-site/src/content/docs/reference/tests.md`
- `docs/ai/specs/.process/G56R-005-workflow.md`
- `docs/ai/specs/.process/G56R-005-design-concept.md`
- `docs/ai/specs/.process/G56R-005-manual-uat.md`
- `docs/ai/specs/.process/G56R-005-retrospective.md`

## Recovery Commands

```text
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/.process/implementation-notes.md
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/.process/pr-packets/g56r-005-draft.json
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/.process/pr-packets/g56r-005-draft/body.md
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/.process/pr-packets/g56r-005-draft/validation.json
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/.process/uat-runbook.md
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/SPEC-MOC.md
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/artifacts/code-approaches.html
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/artifacts/implementation-plan.html
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/artifacts/module-map.html
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/artifacts/spec-explainer.html
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/checklists/data-integrity.md
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/checklists/error-handling.md
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/checklists/state-management.md
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/contracts/fallback-recovery-contract.md
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/data-model.md
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/plan.md
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/quickstart.md
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/research.md
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/retrospective.md
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/spec.md
git show 85762d5a7033981da1fdf6a18b5913c83fc6d9a5:specs/g56r-005-model-availability-fallback-recovery/tasks.md
git checkout 85762d5a7033981da1fdf6a18b5913c83fc6d9a5 -- specs/g56r-005-model-availability-fallback-recovery
```

## Impact Map

| Artifact | Sections Affected | Change Type |
|---|---|---|
| `.specify/memory/spec.md` | G56R-005 outcomes, behavior, cleanup | Append |
| `.specify/memory/plan.md` | Canonical architecture and G56R-006 dependency | Append |
| `.specify/memory/changelog.md` | Merged-feature provenance | Append |
| this archive report | Provenance, recovery, verification | Add |
| Codex routing roadmap and MOC | G56R-005 archived, G56R-006 ready, generated index | Update |
| G56R-005 workflow | Post and preserved-evidence status | Update |
| manual UAT and retrospective | Durable process-evidence paths | Relocate |
| active G56R-005 spec directory | Completed active residue | Remove |

## Cleanup Decision

- **cleanupApplied**: true
- **cleanupOperation**: relocate the UAT runbook and retrospective with
  `apply_patch`; remove the remaining tracked active-spec files with
  `apply_patch`; remove only the resulting empty G56R-005 directories with
  explicit `rmdir` paths; run runner operation `generate-spec-index-write`
  in apply mode
- **cleanupBranch**: `codex/archive-g56r-005-post-merge`
- **blockedBy**: none
- **Downstream state**: G56R-006 is ready because PR #487 supplies the
  deterministic fallback and recovery contracts it depends on. G56R-007 through
  G56R-010 remain blocked by G56R-006; G56R-011 remains blocked by those cohort
  specs.

## Verification Commands

- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- runner operation `generate-spec-index-write` in apply mode
- runner helper `generate-spec-index-check`
- final `find specs -mindepth 1 -maxdepth 4 -print` audit
- stale active-path `rg` scan outside archive/process evidence
- `python3 tests/speckit-pro/run-all.py --layer 1`
- `python3 tests/speckit-pro/run-all.py`
- release-readiness runner gate for
  `docs(g56r-005): archive post-merge state`
- `git diff --check`

## Verification Results

| Check | Result |
|---|---|
| Active spec inventory | G56R-005 absent; unrelated ART-008, ART-017, and BRAND-001 directories preserved |
| Shared autopilot state | valid JSON and intentionally unchanged because the single slot now belongs to ART-008 |
| `generate-spec-index-write` | one write applied to `docs/ai/specs/codex-gpt-5-6-agent-routing-roadmap-MOC.md` |
| `generate-spec-index-check` | exit 0 — index current, all in-scope maps up to date |
| Stale active-path scan | zero live references outside preserved process/archive evidence |
| Structural suite | 1511/1511 |
| Full deterministic suite | 14011/14011 (L1 1511, L4 12281, L5 219) |
| Release-readiness title gate | pass for `docs(g56r-005): archive post-merge state` |
| `git diff --check` | clean |

Docs reference generation and payload rebuilding were not required. This cleanup
changes no tracked source under `tests/speckit-pro/**`, no plugin source or
inventory, and no generated payload input. The existing docs reference and
payload evidence remain the merged PR #487 artifacts; the full suite validates
their contracts.

## Constitution Compliance

PASS by scope. The cleanup preserves durable evidence, changes no plugin version
or runtime payload, adds no active Bash or `jq` dependency, retains all merged
source through immutable git provenance, and leaves the Python-authoritative
structural and full suites as completion gates.

## Conflicts and Outstanding Items

- `.specify/feature.json` is absent and was not created.
- `docs/ai/specs/.process/autopilot-state.json` now belongs to ART-008 and was
  not overwritten. The older root `.specify/autopilot-state.json` remains an
  unrelated completed ART-001 archive record.
- `TODO-CODEX-WORKTREE-BINDING` remains a process-level follow-up recorded in
  the preserved retrospective; it does not affect shipped G56R-005 behavior or
  archive recovery.
- No live model-availability or real-user-home claim is made by this archive.
