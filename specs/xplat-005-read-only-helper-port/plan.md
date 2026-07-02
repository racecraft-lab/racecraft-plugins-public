# Implementation Plan: XPLAT-005 Read-Only Helper Port

**Branch**: `codex/xplat-005-read-only-helper-port` | **Date**: 2026-07-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/xplat-005-read-only-helper-port/spec.md`, Phase 3 prompt from `docs/ai/specs/.process/XPLAT-005-workflow.md`, and accepted design decisions from `docs/ai/specs/.process/XPLAT-005-design-concept.md`.

## Summary

Port the read-only and advisory helper surface onto the XPLAT-004 Python runner by adding a small helper registry/dispatch layer plus bounded per-helper module targets. XPLAT-005 preserves current JSON stdout, stderr diagnostics, and exit-code semantics through deterministic golden fixtures and source-checkout Bash-reference comparisons. Active Claude Code, Codex, install, generated payload, public docs, mutation-helper, and native installed-plugin cutover work remains deferred.

## Technical Context

**Language/Version**: Python 3.11+ standard library through `speckit-pro/speckit_pro_runner/`

**Primary Dependencies**: Existing XPLAT-004 runner envelope, diagnostics, typed path, runtime-info, and preflight primitives; current Bash helper scripts remain temporary source-checkout references only

**Storage**: Checked-in fixture, contract, and evidence files only; ported helpers must not write repository or user-local state

**Testing**: Python standard-library Layer 4 helper tests, golden fixture comparisons, source-checkout Bash-reference comparisons, local runtime-info smoke, and existing shell-layer gates during migration

**Target Platform**: Source-checkout Python runner on Python 3.11+; local macOS smoke only; Windows/no-Bash/path behavior covered by deterministic fixtures; installed-cache and full native matrix proof deferred to XPLAT-007

**Project Type**: CLI helper runner package with parity fixtures and internal contract artifacts

**Performance Goals**: Deterministic helper invocation with no network, no package restore, no virtualenv restore, no shell dependency for promoted Python helper execution, and stable comparison output after explicit normalization

**Constraints**: Read-only/advisory helper behavior only; preserve stdout JSON schema, stderr diagnostics, and exit-code semantics; every promoted Bash-backed helper requires golden fixture parity plus source-checkout Bash-reference comparison before `python_authoritative` status; normalization is explicit and limited to environment-sensitive fields

**Scale/Scope**: One workflow with two internal slices covering registry/dispatch plus sixteen in-scope helper or mode ports; out-of-scope mutation, persistence, stack, relocation, install, autoheal, and active cutover helpers stay unported

**Reviewability Budget**: setup reviewability warning recorded as `status=warn`, `pass=true`; two primary surfaces `docs/process` and `harness/adapter`; supporting test fixture surface; projected reviewable LOC 250; projected production files 4; projected total files 10; no blockers

## Declared File Operations

- MODIFIED speckit-pro/speckit_pro_runner/__main__.py
- NEW speckit-pro/speckit_pro_runner/helpers/__init__.py
- NEW speckit-pro/speckit_pro_runner/helpers/registry.py
- NEW speckit-pro/speckit_pro_runner/helpers/read_only.py
- NEW tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py
- NEW tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/synthetic-paths.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/normalization-cases.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/smoke-runtime-info-request.json

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Plan Evidence |
|---|---|---|
| I. Plugin Structure Compliance | PASS | No plugin manifest, command, skill, agent, or hook layout changes are planned. Runner code stays under the existing `speckit-pro/` plugin package. |
| II. Script Safety | PASS | No new Bash scripts are planned. Existing Bash helpers are invoked only by parity tests as source-checkout references. |
| III. Semantic Versioning | PASS | No manual version edits are planned; active release/version changes remain outside this phase. |
| IV. Test Coverage Before Merge | PASS | Each promoted helper requires golden fixture parity, Bash-reference comparison, and an authoritative Python Layer 4 command before release-gate promotion. |
| V. Conventional Commits | PASS | Commit/PR behavior is outside this phase, but the planned scope supports a conventional `feat(speckit-pro): ...` change if later committed by the orchestrator. |
| VI. KISS, Simplicity & YAGNI | PASS | The runner gains one explicit registry and one bounded read-only helper module, not a generic helper framework. Mutation and active cutover work is deferred. |

## Project Structure

### Documentation (this feature)

```text
specs/xplat-005-read-only-helper-port/
+-- plan.md
+-- research.md
+-- data-model.md
+-- quickstart.md
+-- contracts/
|   +-- helper-promotion-record.schema.json
|   +-- read-only-helper-request.schema.json
+-- tasks.md
```

### Source Code (repository root)

```text
speckit-pro/
+-- speckit_pro_runner/
|   +-- __main__.py
|   +-- helpers/
|       +-- __init__.py
|       +-- registry.py
|       +-- read_only.py
+-- skills/speckit-autopilot/scripts/
    +-- check-prerequisites.sh
    +-- detect-commands.sh
    +-- detect-presets.sh
    +-- count-markers.sh
    +-- validate-gate.sh
    +-- reviewability-gate.sh
    +-- estimate-reviewable-loc.sh
    +-- resolve-confidence-mode.sh
    +-- confidence-gate.sh
    +-- generate-spec-index.sh
    +-- o5-topology.sh
    +-- atomicity-route.sh
    +-- plan-layers.sh
    +-- validate-pr-workflow-contract.sh
    +-- validate-pr-packet.sh

tests/speckit-pro/layer4-scripts/
+-- test-speckit-pro-read-only-helpers.py
+-- fixtures/read-only-helpers/
    +-- fixture-manifest.json
    +-- bash-reference-manifest.json
    +-- synthetic-paths.json
    +-- normalization-cases.json
    +-- smoke-runtime-info-request.json
```

**Structure Decision**: Extend the existing runner package with a narrow helper registry. Keep helper behavior grouped by read-only/advisory domain in `helpers/read_only.py`, with per-helper registry entries pointing at explicit callable targets. This satisfies the reusable XPLAT-006 extension point without creating one file per helper or a broad plugin framework during XPLAT-005.

## Implementation Slices

### Slice 1 - Foundational Registry And Status Helpers

Build the registry/dispatch path and promote prerequisite, detection, marker, validation, reviewability, and confidence helpers only after parity is accepted. This slice owns `check-prerequisites`, `detect-commands`, `detect-presets`, `count-markers`, `validate-gate`, `reviewability-gate`, `estimate-reviewable-loc`, `resolve-confidence-mode`, and `confidence-gate`.

### Slice 2 - Planning, Index, Topology, And Late PR-Packet Validation

Add read-only/advisory ports for `generate-spec-index --check`, `o5-topology`, `atomicity-route`, `plan-layers <feature-dir>`, `validate-pr-workflow-contract`, and `validate-pr-packet` validation-only behavior. This slice excludes write/regenerate modes, marker-plan output, validation-result persistence, workflow-event upserts, PR body generation, PR emission, split state, restack, relocation, install repair, autoheal, and active Claude/Codex cutover.

**Reviewability split decision**: Remain one XPLAT-005 workflow with two internal slices. Planning does not prove a child-spec split is required because the accepted implementation surface is four production files, ten total planned files, and the only reviewability warning is the already accepted surface warning.

## Helper Promotion Matrix Plan

Status values are target promotion states. `python_authoritative` applies only after the helper has passed the listed golden fixture parity and Bash-reference comparison. Golden-only cases are limited to runner envelope, registry dispatch, typed-path/subprocess safety, malformed request, synthetic Windows/no-Bash/path, and normalization unit tests.

| Helper id | Slice | Bash script path | Runner operation/module | Fixture ids | Bash comparison ids | Normalized fields | Status | Authoritative test command | Deferred follow-up |
|---|---:|---|---|---|---|---|---|---|---|
| helper-registry-dispatch | 1 | N/A | `helper.dispatch` / `speckit_pro_runner.helpers.registry` | `golden.registry.valid`, `golden.registry.unknown-helper`, `golden.registry.malformed-request` | N/A | none | `python_authoritative` | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py --helper helper-registry-dispatch` | XPLAT-006 may reuse registry for mutation helpers |
| check-prerequisites | 1 | `speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh` | `helper.check-prerequisites` / `speckit_pro_runner.helpers.read_only:check_prerequisites` | `golden.check-prerequisites.valid`, `golden.check-prerequisites.missing-spec`, `golden.check-prerequisites.no-bash` | `bash.check-prerequisites.valid`, `bash.check-prerequisites.missing-spec` | repo absolute paths, command executable paths, branch metadata | `python_authoritative` | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py --helper check-prerequisites` | Installed-cache proof in XPLAT-007 |
| detect-commands | 1 | `speckit-pro/skills/speckit-autopilot/scripts/detect-commands.sh` | `helper.detect-commands` / `speckit_pro_runner.helpers.read_only:detect_commands` | `golden.detect-commands.available`, `golden.detect-commands.missing`, `golden.detect-commands.windows-paths` | `bash.detect-commands.available`, `bash.detect-commands.missing` | executable paths, repo root, platform identity | `python_authoritative` | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py --helper detect-commands` | Active command invocation cutover in XPLAT-007 |
| detect-presets | 1 | `speckit-pro/skills/speckit-autopilot/scripts/detect-presets.sh` | `helper.detect-presets` / `speckit_pro_runner.helpers.read_only:detect_presets` | `golden.detect-presets.reviewability`, `golden.detect-presets.none`, `golden.detect-presets.path-spaces` | `bash.detect-presets.reviewability`, `bash.detect-presets.none` | repo absolute paths, preset path separators | `python_authoritative` | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py --helper detect-presets` | Preset install repair remains out of scope |
| count-markers | 1 | `speckit-pro/skills/speckit-autopilot/scripts/count-markers.sh` | `helper.count-markers` / `speckit_pro_runner.helpers.read_only:count_markers` | `golden.count-markers.clean`, `golden.count-markers.needs-clarification`, `golden.count-markers.gaps` | `bash.count-markers.clean`, `bash.count-markers.needs-clarification` | repo absolute paths only if emitted | `python_authoritative` | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py --helper count-markers` | None |
| validate-gate | 1 | `speckit-pro/skills/speckit-autopilot/scripts/validate-gate.sh` | `helper.validate-gate` / `speckit_pro_runner.helpers.read_only:validate_gate` | `golden.validate-gate.g3-pass`, `golden.validate-gate.g3-fail`, `golden.validate-gate.usage` | `bash.validate-gate.g3-pass`, `bash.validate-gate.g3-fail` | repo absolute paths only if emitted | `python_authoritative` | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py --helper validate-gate` | None |
| reviewability-gate | 1 | `speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh` | `helper.reviewability-gate` / `speckit_pro_runner.helpers.read_only:reviewability_gate` | `golden.reviewability-gate.pass`, `golden.reviewability-gate.warn`, `golden.reviewability-gate.block` | `bash.reviewability-gate.pass`, `bash.reviewability-gate.warn`, `bash.reviewability-gate.block` | repo absolute paths, branch metadata, temp paths | `python_authoritative` | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py --helper reviewability-gate` | Final mutation/backstop behavior remains unchanged |
| estimate-reviewable-loc | 1 | `speckit-pro/skills/speckit-autopilot/scripts/estimate-reviewable-loc.sh` | `helper.estimate-reviewable-loc` / `speckit_pro_runner.helpers.read_only:estimate_reviewable_loc` | `golden.estimate-reviewable-loc.typical`, `golden.estimate-reviewable-loc.not-estimated`, `golden.estimate-reviewable-loc.bad-input` | `bash.estimate-reviewable-loc.typical`, `bash.estimate-reviewable-loc.not-estimated` | repo absolute paths only if emitted | `python_authoritative` | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py --helper estimate-reviewable-loc` | None |
| resolve-confidence-mode | 1 | `speckit-pro/skills/speckit-autopilot/scripts/resolve-confidence-mode.sh` | `helper.resolve-confidence-mode` / `speckit_pro_runner.helpers.read_only:resolve_confidence_mode` | `golden.resolve-confidence-mode.default`, `golden.resolve-confidence-mode.explicit`, `golden.resolve-confidence-mode.invalid` | `bash.resolve-confidence-mode.default`, `bash.resolve-confidence-mode.invalid` | environment variable ordering if emitted | `python_authoritative` | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py --helper resolve-confidence-mode` | None |
| confidence-gate | 1 | `speckit-pro/skills/speckit-autopilot/scripts/confidence-gate.sh` | `helper.confidence-gate` / `speckit_pro_runner.helpers.read_only:confidence_gate` | `golden.confidence-gate.pass`, `golden.confidence-gate.warn`, `golden.confidence-gate.block` | `bash.confidence-gate.pass`, `bash.confidence-gate.block` | repo absolute paths only if emitted | `python_authoritative` | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py --helper confidence-gate` | None |
| generate-spec-index-check | 2 | `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh` | `helper.generate-spec-index-check` / `speckit_pro_runner.helpers.read_only:generate_spec_index_check` | `golden.generate-spec-index-check.fresh`, `golden.generate-spec-index-check.stale`, `golden.generate-spec-index-check.malformed` | `bash.generate-spec-index-check.fresh`, `bash.generate-spec-index-check.stale` | repo absolute paths, temp paths, path separators | `python_authoritative` | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py --helper generate-spec-index-check` | Write/regenerate mode deferred |
| o5-topology | 2 | `speckit-pro/skills/speckit-autopilot/scripts/o5-topology.sh` | `helper.o5-topology` / `speckit_pro_runner.helpers.read_only:o5_topology` | `golden.o5-topology.valid-parent`, `golden.o5-topology.invalid-topology`, `golden.o5-topology.mixed-child-states` | `bash.o5-topology.valid-parent`, `bash.o5-topology.invalid-topology` | repo absolute paths, child spec paths | `python_authoritative` | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py --helper o5-topology` | None |
| atomicity-route | 2 | `speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh` | `helper.atomicity-route` / `speckit_pro_runner.helpers.read_only:atomicity_route` | `golden.atomicity-route.single-additive`, `golden.atomicity-route.hard-atomic`, `golden.atomicity-route.context-conflict` | `bash.atomicity-route.single-additive`, `bash.atomicity-route.hard-atomic` | repo absolute paths only if emitted | `python_authoritative` | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py --helper atomicity-route` | Mutation routing remains out of scope |
| plan-layers-feature-dir | 2 | `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh` | `helper.plan-layers-feature-dir` / `speckit_pro_runner.helpers.read_only:plan_layers_feature_dir` | `golden.plan-layers.valid-real`, `golden.plan-layers.dependency-cycle`, `golden.plan-layers.malformed-task` | `bash.plan-layers.valid-real`, `bash.plan-layers.dependency-cycle` | repo absolute paths, feature-dir absolute path | `python_authoritative` | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py --helper plan-layers-feature-dir` | `marker-plan` output mode deferred |
| validate-pr-workflow-contract | 2 | `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-workflow-contract.sh` | `helper.validate-pr-workflow-contract` / `speckit_pro_runner.helpers.read_only:validate_pr_workflow_contract` | `golden.validate-pr-workflow-contract.valid`, `golden.validate-pr-workflow-contract.missing`, `golden.validate-pr-workflow-contract.invalid` | `bash.validate-pr-workflow-contract.valid`, `bash.validate-pr-workflow-contract.invalid` | repo absolute paths, workflow path | `python_authoritative` | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py --helper validate-pr-workflow-contract` | Workflow-event mutation remains out of scope |
| validate-pr-packet-read-only | 2 | `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh` | `helper.validate-pr-packet-read-only` / `speckit_pro_runner.helpers.read_only:validate_pr_packet_read_only` | `golden.validate-pr-packet.valid-single`, `golden.validate-pr-packet.invalid-missing-evidence`, `golden.validate-pr-packet.invalid-protected-edit` | `bash.validate-pr-packet.valid-single`, `bash.validate-pr-packet.invalid-missing-evidence` | repo absolute paths, packet path, feature-dir path | `python_authoritative` | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py --helper validate-pr-packet-read-only` | PR body, PR emission, persistence, and restack deferred |
| detect-stack-manager | N/A | `speckit-pro/skills/speckit-autopilot/scripts/detect-stack-manager.sh` | N/A | N/A | N/A | N/A | `out_of_scope` | N/A | XPLAT-006 |
| generate-spec-index-write | N/A | `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh` | N/A | N/A | N/A | N/A | `out_of_scope` | N/A | XPLAT-006 or later mutation-helper work |
| plan-layers-marker-plan | N/A | `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh` | N/A | N/A | N/A | N/A | `out_of_scope` | N/A | XPLAT-006 |
| validate-pr-packet-persistence | N/A | `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh` | N/A | N/A | N/A | N/A | `out_of_scope` | N/A | XPLAT-006 |

## Contracts And Data Artifacts

- `contracts/read-only-helper-request.schema.json` defines the runner request envelope for promoted read-only helper operations.
- `contracts/helper-promotion-record.schema.json` defines the helper promotion record shape used by the parity manifest and PR review packet.
- `data-model.md` defines helper registry entries, helper invocation results, parity fixtures, Bash-reference comparisons, normalization rules, promotion records, source-checkout smoke evidence, and scope-audit records.

## Verification Plan

1. Run the local source-checkout runtime smoke:

   ```bash
   printf '%s\n' '{"schema_version":"1.0","request_id":"xplat-005-smoke","helper_id":"runner","operation":"runtime-info","mode":"read_only","inputs":{}}' | PYTHONPATH=speckit-pro python3 -m speckit_pro_runner
   ```

2. Run per-helper parity tests:

   ```bash
   python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py
   ```

3. Run the focused script layer:

   ```bash
   bash tests/speckit-pro/run-all.sh --layer 4
   ```

4. Run the default deterministic gate before PR handoff:

   ```bash
   bash tests/speckit-pro/run-all.sh
   ```

5. Confirm scope audit has zero active Claude Code or Codex skill, hook, generated payload, install, marketplace/public docs, mutation-helper, PR-emission, split-state, restack, relocation, install repair, or autoheal cutover edits.

## Phase 1 Design Recheck

| Principle | Status | Recheck Evidence |
|---|---|---|
| I. Plugin Structure Compliance | PASS | Contracts and data artifacts do not introduce active plugin layout changes. |
| II. Script Safety | PASS | No new Bash scripts are introduced by the design. |
| III. Semantic Versioning | PASS | No version file changes are planned. |
| IV. Test Coverage Before Merge | PASS | The promotion matrix gives every in-scope helper a fixture set, Bash comparison set, and authoritative Python test command. |
| V. Conventional Commits | PASS | No commit is produced in this phase. |
| VI. KISS, Simplicity & YAGNI | PASS | The registry pattern is explicit and bounded to read-only helper dispatch; deferred mutation and cutover work is recorded. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Reviewability surface warning: `docs/process` plus `harness/adapter` | Helper parity must be planned and reviewed with process evidence so maintainers can distinguish promoted, Bash-reference-only, and out-of-scope helpers. | A code-only plan would hide the migration proof and could be mistaken for active cutover or installed-platform support. |
