# Archival Report - G56R-001 Candidate Route Baseline and Role Contracts

## Mode

- **archiveMode**: multi-PRD post-merge cleanup sweep
- **dryRun**: false
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true

## Provenance

- **Source spec path**: `specs/g56r-001-candidate-route-baseline/`
- **Source PRD**: `docs/prd-codex-gpt-5-6-agent-routing.md`
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/360
- **PR title**: `docs(speckit-pro): align G56R official-source route evidence`
- **Merged at**: `2026-07-16T15:52:57Z`
- **Merge commit**: `191642962e55df21000a5303f36e9010a14898d2`
- **Head branch**: `g56r-001-candidate-route-baseline`
- **Base branch**: `main`
- **Foundation PR**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/362, merged as `f2e664d5afbb9525f6486506425dc47c2f8bed12`
- **Workflow file preserved**: `docs/ai/specs/.process/G56R-001-workflow.md`
- **Design concept preserved**: `docs/ai/specs/.process/G56R-001-design-concept.md`
- **CI and review state**: all PR checks passed and all three review threads are resolved.

## Feature Summary

G56R-001 shipped the current official-OpenAI-documentation candidate-route
baseline for twelve named Codex/parity roles. The canonical Markdown report and
schema-v2 planning manifest preserve source records, effort-surface evidence,
project inputs, role contracts, provisional candidate routes, fixture backlog,
traceability, decisions, and strict downstream go/no-go boundaries.

The evidence package remains planning-only. It does not qualify routes, select
preferred models, order fallbacks, mutate agent TOML, change installers, rebuild
runtime payloads, or establish runtime availability. G56R-002 is ready only for
capability discovery and telemetry profiling under the preserved authority and
invalidation rules.

## Canonical Shipped Artifacts

- `docs/ai/research/codex-agent-route-candidates.md`
- `docs/ai/research/codex-agent-route-candidate-manifest.json`
- `docs/ai/research/agent-route-candidate-manifest.schema.json`
- `docs/ai/specs/agent-routing-parity-contract.md`
- `docs/ai/specs/.process/G56R-001-workflow.md`
- `docs/ai/specs/.process/G56R-001-design-concept.md`
- `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md`
- `docs/ai/specs/codex-gpt-5-6-agent-routing-roadmap-MOC.md`
- `docs/prd-codex-gpt-5-6-agent-routing.md`
- `tests/speckit-pro/unit/test-agent-route-research-parity.py`

The canonical report and manifest retain historical project-input references to
the raw G56R-001 spec package. Those references are provenance records, not live
active-spec dependencies; the exact source remains available through the merge
commit recovery commands below.

## Recovery Commands

```text
git show 191642962e55df21000a5303f36e9010a14898d2:specs/g56r-001-candidate-route-baseline/spec.md
git show 191642962e55df21000a5303f36e9010a14898d2:specs/g56r-001-candidate-route-baseline/plan.md
git show 191642962e55df21000a5303f36e9010a14898d2:specs/g56r-001-candidate-route-baseline/tasks.md
git show 191642962e55df21000a5303f36e9010a14898d2:specs/g56r-001-candidate-route-baseline/research.md
git show 191642962e55df21000a5303f36e9010a14898d2:specs/g56r-001-candidate-route-baseline/data-model.md
git show 191642962e55df21000a5303f36e9010a14898d2:specs/g56r-001-candidate-route-baseline/quickstart.md
git show 191642962e55df21000a5303f36e9010a14898d2:specs/g56r-001-candidate-route-baseline/retrospective.md
git show 191642962e55df21000a5303f36e9010a14898d2:specs/g56r-001-candidate-route-baseline/verify-tasks-report.md
git show 191642962e55df21000a5303f36e9010a14898d2:specs/g56r-001-candidate-route-baseline/SPEC-MOC.md
git show 191642962e55df21000a5303f36e9010a14898d2:specs/g56r-001-candidate-route-baseline/contracts/codex-agent-route-candidates.contract.md
git show 191642962e55df21000a5303f36e9010a14898d2:specs/g56r-001-candidate-route-baseline/checklists/requirements.md
git show 191642962e55df21000a5303f36e9010a14898d2:specs/g56r-001-candidate-route-baseline/checklists/llm-integration.md
git show 191642962e55df21000a5303f36e9010a14898d2:specs/g56r-001-candidate-route-baseline/checklists/reliability.md
git show 191642962e55df21000a5303f36e9010a14898d2:specs/g56r-001-candidate-route-baseline/checklists/data-integrity.md
git show 191642962e55df21000a5303f36e9010a14898d2:specs/g56r-001-candidate-route-baseline/checklists/observability.md
git show 191642962e55df21000a5303f36e9010a14898d2:specs/g56r-001-candidate-route-baseline/checklists/error-handling.md
git show 191642962e55df21000a5303f36e9010a14898d2:specs/g56r-001-candidate-route-baseline/checklists/security.md
git checkout 191642962e55df21000a5303f36e9010a14898d2 -- specs/g56r-001-candidate-route-baseline
```

## Cleanup Decision

- **cleanupApplied**: true
- **cleanupCommand**: `git rm -r specs/g56r-001-candidate-route-baseline`
- **cleanupBranch**: `codex/archive-merged-specs-2026-07-16`
- **blockedBy**: none
- **Downstream state**: G56R-002 is ready for capability discovery and telemetry profiling. Qualification, route selection, fallback policy, resolver behavior, installation, and release remain blocked by their later roadmap specifications.

## Verification Commands

- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- SpecKit runner operation `generate-spec-index-write` in apply mode
- SpecKit runner helper `generate-spec-index-check`
- `find specs -mindepth 1 -maxdepth 4 -print`
- `python3 tests/speckit-pro/unit/test-agent-route-research-parity.py`
- `python3 tests/speckit-pro/run-all.py --layer 1`
- `python3 tests/speckit-pro/run-all.py`
- `pnpm --dir docs-site reference:check`
- `git diff --check`

## Verification Results

- PASS: `autopilot-state.json` parses as valid JSON.
- PASS: SpecKit index write/check reports all in-scope maps current.
- PASS: active-spec inventory contains only `specs/.gitkeep`.
- PASS: shared CAR/G56R research parity passed `18/18`.
- PASS: focused spec-index tests passed `18/18`.
- PASS: Layer 1 passed `1428/1428`.
- PASS: the full deterministic suite passed `2821/2821`.
- PASS: docs reference pages are current.
- PASS: staged diff whitespace check is clean.

## Feature Status

`Complete / Archived`. The active G56R-001 folder is removed after this report,
project-memory updates, roadmap reconciliation, completed archive state, and
index regeneration. The raw spec package remains recoverable from the merge
commit above.
