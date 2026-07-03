# Implementation Plan: XPLAT-006 Mutation, Install, and PR-Emission Helper Port

**Branch**: `codex/xplat-006-mutation-install-pr-emission-helper-port` | **Date**: 2026-07-03 | **Spec**: `specs/xplat-006-mutation-install-pr-emission-helper-port/spec.md`

**Input**: Feature specification from `specs/xplat-006-mutation-install-pr-emission-helper-port/spec.md`

## Summary

Port SpecKit Pro mutation-capable, install, doctor, PR-emission, restack,
migration, relocation, and deferred mixed write/apply helpers onto the
Python 3.11+ standard-library runner. Keep one XPLAT-006 workflow with three
implementation slices: shared mutation safety first, manifest-driven
install/doctor second, and PR/restack/relocation plus Codex autopilot
phase-coverage hardening third. Deterministic proof uses fake repositories,
fake CLIs, fake Claude/Codex homes, golden fixtures, Bash-reference comparison,
and PR packet traceability before any helper is marked Python-authoritative.

## Technical Context

**Language/Version**: Python 3.11+ standard library for promoted runner helper execution; existing Bash helpers remain source-checkout references until XPLAT-007.

**Primary Dependencies**: Python standard library only for new runner helper logic; existing shell Layer 1/4 gates remain temporary validation and Bash-reference evidence.

**Storage**: Checked-in repository files only: runner helper modules, committed install inventory, fixture inputs/outputs, JSON schemas, manifest/checksum metadata, and Plan artifacts.

**Testing**: Python `unittest`/standard-library subprocess tests, golden fixture tests, source-checkout Bash-reference comparison, `bash tests/speckit-pro/run-all.sh --layer 4`, `bash tests/speckit-pro/run-all.sh --layer 1`, and scope-audit diff checks.

**Target Platform**: Source checkout proof on local macOS plus deterministic Windows-style path fixtures. Native Windows/macOS/Linux installed-cache UAT remains XPLAT-008.

**Project Type**: Plugin runner package plus deterministic test harness.

**Performance Goals**: Deterministic helper runs complete within existing Layer 4 expectations; no network, package restore, or real GitHub/user-home mutation is required for acceptance.

**Constraints**: Python 3.11+ standard library only for promoted helper execution; no new runtime dependency; no `shell=True`, shell command strings, `os.system`, package install, virtualenv restore, `jq`, Bash, PowerShell, Node, Go, Rust, or Zig in promoted execution paths. No active Claude/Codex cutover, generated-payload selection/cutover, public platform claims, native matrix UAT, or repo-local release-gate migration lands in XPLAT-006; phase-coverage hardening may update autopilot instructions and generated mirrors only.

**Scale/Scope**: One workflow with three internal slices covering mutation primitives, install/doctor, PR-emission/restack/migration/relocation, deferred mixed write modes, and Codex autopilot phase-coverage validation.

**Reviewability Budget**: Setup reviewability warning recorded: `status=warn`, `pass=true`, two primary surfaces (`docs/process`, `harness/adapter`), no blockers. Plan keeps the accepted three-slice strategy and requires split before implementation if Tasks proves the helper matrix cannot stay reviewable.

## Declared File Operations

The plan-phase reviewability estimator parses this block. Fixture payloads may
expand under the declared fixture roots during implementation; the source,
test, and contract surfaces below are the review order anchors.

- MODIFIED speckit-pro/speckit_pro_runner/__main__.py
- MODIFIED speckit-pro/speckit_pro_runner/helpers/registry.py
- NEW speckit-pro/speckit_pro_runner/helpers/mutation.py
- NEW speckit-pro/speckit_pro_runner/helpers/install.py
- NEW speckit-pro/speckit_pro_runner/helpers/pr_emission.py
- NEW speckit-pro/speckit_pro_runner/helpers/promotion.py
- NEW speckit-pro/speckit_pro_runner/install_inventory.json
- MODIFIED speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- MODIFIED speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/task-list-canonical-codex.md
- NEW speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py
- MODIFIED dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md
- MODIFIED dist/codex/speckit-pro/skills/speckit-autopilot/references/phase-execution-codex.md
- MODIFIED dist/codex/speckit-pro/skills/speckit-autopilot/references/task-list-canonical-codex.md
- NEW dist/codex/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py
- NEW dist/claude/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py
- NEW tests/speckit-pro/layer4-scripts/test-autopilot-phase-coverage.py
- MODIFIED tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py
- MODIFIED tests/speckit-pro/run-all.sh
- NEW tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py
- NEW tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/fixture-manifest.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/bash-reference-manifest.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/promotion-records.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/install-inventory-fixtures.json
- MODIFIED specs/xplat-006-mutation-install-pr-emission-helper-port/plan.md
- NEW specs/xplat-006-mutation-install-pr-emission-helper-port/research.md
- NEW specs/xplat-006-mutation-install-pr-emission-helper-port/data-model.md
- NEW specs/xplat-006-mutation-install-pr-emission-helper-port/quickstart.md
- NEW specs/xplat-006-mutation-install-pr-emission-helper-port/contracts/mutation-helper-request.schema.json
- NEW specs/xplat-006-mutation-install-pr-emission-helper-port/contracts/mutation-helper-result.schema.json
- NEW specs/xplat-006-mutation-install-pr-emission-helper-port/contracts/doctor-preflight-result.schema.json
- NEW specs/xplat-006-mutation-install-pr-emission-helper-port/contracts/helper-promotion-record.schema.json
- NEW specs/xplat-006-mutation-install-pr-emission-helper-port/contracts/autopilot-phase-coverage-report.schema.json

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Plan disposition | Verification |
| --- | --- | --- |
| I. Plugin Structure Compliance | Runner helper ports stay under `speckit-pro/`; tests stay under repo-level `tests/speckit-pro/`; no plugin payload test directories are introduced. | `bash tests/speckit-pro/run-all.sh --layer 1` |
| II. Script Safety | Promoted helper logic is Python standard-library code. Existing Bash helpers are reference-only until XPLAT-007. Any touched shell scripts keep existing safety conventions. | Python tests, shell syntax gates for touched Bash references, code review |
| III. Semantic Versioning | No manual plugin version edits in XPLAT-006. | Diff review |
| IV. Test Coverage Before Merge | Each promoted helper needs golden fixture coverage, Bash-reference comparison when Bash-backed, and a promotion record before Python is authoritative. | Focused Python tests, Layer 4, Layer 1 |
| V. Conventional Commits | Implementation and later PR title must use the repo's conventional commit pattern. | PR title and commit review |
| VI. KISS, Simplicity & YAGNI | Extend the explicit helper registry with small modules and shared mutation primitives; avoid a generic mutation framework beyond the common request/result, path, atomic-write, and promotion-record model. | Plan review, complexity tracking, code review |

**Initial Gate Result**: PASS with reviewability warning. The warning is accepted
for planning only because the workflow remains one roadmap item with three
ordered slices and explicit non-goals. Implementation must split before coding
if Tasks cannot keep each PR review packet understandable.

**Post-Design Gate Result**: PASS. Research, data model, contracts, and
quickstart preserve Python-only promoted execution, deterministic fixtures, and
deferred active cutover boundaries.

## Project Structure

### Documentation (this feature)

```text
specs/xplat-006-mutation-install-pr-emission-helper-port/
+-- SPEC-MOC.md
+-- spec.md
+-- plan.md
+-- research.md
+-- data-model.md
+-- quickstart.md
+-- contracts/
|   +-- mutation-helper-request.schema.json
|   +-- mutation-helper-result.schema.json
|   +-- doctor-preflight-result.schema.json
|   +-- helper-promotion-record.schema.json
|   +-- autopilot-phase-coverage-report.schema.json
+-- checklists/
```

### Source Code (repository root)

```text
speckit-pro/
+-- speckit_pro_runner/
|   +-- __main__.py
|   +-- envelope.py
|   +-- runtime.py
|   +-- speckit-pro-runner.manifest.json
|   +-- speckit-pro-runner.sha256
|   +-- install_inventory.json
|   +-- helpers/
|       +-- registry.py
|       +-- read_only.py
|       +-- mutation.py
|       +-- install.py
|       +-- pr_emission.py
|       +-- promotion.py
+-- skills/
    +-- speckit-autopilot/
        +-- scripts/
            +-- validate-autopilot-phase-coverage.py

tests/speckit-pro/layer4-scripts/
+-- test-speckit-pro-mutation-helpers.py
+-- test-autopilot-phase-coverage.py
+-- fixtures/
    +-- mutation-helpers/
        +-- fixture-manifest.json
        +-- bash-reference-manifest.json
        +-- promotion-records.json
        +-- install-inventory-fixtures.json
```

**Structure Decision**: Use the existing XPLAT-004/XPLAT-005 runner package and
helper registry. Add mutation-capable helper modules beside `read_only.py`
instead of overloading the accepted read-only mode. Keep fixture and promotion
evidence under Layer 4 test fixtures. Keep schemas in this spec's CONTRACT
artifacts for reviewer traceability; do not move them into active runtime gates
in XPLAT-006.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Reviewability warning: multiple primary surfaces | XPLAT-006 must connect runner mutation semantics, fake harness proof, install doctor proof, PR-emission proof, and workflow hardening before XPLAT-007 can migrate gates. | Splitting mutation safety away from install/PR helpers would leave no single PR packet proving the promotion boundary and deferred cutover scope. |
| Shared mutation primitives | Atomic writes, approval evidence, path-boundary checks, dirty-worktree guards, and partial-failure records must be consistent across helper groups. | Per-helper ad hoc mutation handling would create inconsistent safety semantics and make parity evidence harder to review. |

## Implementation Slices

### Slice 1: Mutation Safety Foundation

Scope:
- Add mutation-capable dispatch separate from XPLAT-005 `read_only`.
- Define helper id, operation, mode, input, boundary context, and approval evidence request schema.
- Define stable result shape under `data.mutation` with planned, applied, skipped, no-op, dirty-worktree, failure, rollback, and remediation fields.
- Implement atomic write primitives using complete content generation, same-directory temp files, validation, flush/fsync, and `os.replace`.
- Add path-boundary checks for repo, plugin, fake-home, fake-cache, and temp fixture roots.
- Add dirty-worktree guard using argv-list subprocess calls only.
- Add promotion records and fixture metadata before any named helper becomes Python-authoritative.

Acceptance proof:
- Golden fixtures for dry-run, apply, no-op, invalid helper/mode, malformed JSON, path escape, symlink rejection, dirty worktree, write failure, and partial failure.
- Bash-reference comparison harness uses source-checkout Bash helpers only as references.
- Python tests prove dry-run leaves repository, home, cache, network, and GitHub state unchanged.

### Slice 2: Install Completeness and Doctor/Preflight

Scope:
- Add committed generated install inventory under `speckit-pro/speckit_pro_runner/`.
- Port `install-codex-agents`, `install-curated-set` check/install/upgrade, doctor install completeness, `project-fixup apply`, and `ensure-reviewability-preset` write behavior.
- Verify expected Claude agents, Codex agents, runner files, generated payload files, plugin version metadata, marketplace version metadata, runner manifest, and checksums from the inventory.
- Keep doctor/preflight read-only by default; make repair a separate apply-mode operation.
- Limit safe repair to fake homes/caches by default or explicitly approved declared boundaries.

Acceptance proof:
- Fake Claude home, fake Codex home, fake plugin cache, fake `gh`, and fake `specify` fixtures.
- Deterministic cases for complete install, missing agent, stale cache, downgrade refusal, missing runner file, checksum mismatch, missing generated payload, malformed inventory, path escape, symlink rejection, missing fake CLI, real-home refusal, safe repair, unsafe manual remediation, and blocked repair.

### Slice 3: PR-Emission, Restack, Relocation, Mixed Writes, and Autopilot Hardening

Scope:
- Port `generate-pr-body`, `generate-uat-skeleton`, `final-reviewability-backstop`, PR-packet output, workflow-contract output, `multi-pr-emission`, `restack`, `migrate-structure`, `relocate-process-artifacts`, generated-index write/regenerate modes, `plan-layers` marker-plan output, and deferred write modes for mixed helpers.
- Keep candidate PR emission as dry-run command capture.
- Allow fake PR/restack fixtures to exercise apply paths.
- Keep live GitHub or live repo mutation exceptional and blocked without structured approval evidence tied to prior dry-run output and clean-worktree checks.
- Include `detect-stack-manager` only as decision and command-plan support; mutating command execution remains owned by apply paths.
- Ship and maintain the Python standard-library validator `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`.

Autopilot phase-coverage proof:
- `tests/speckit-pro/layer4-scripts/test-autopilot-phase-coverage.py` must include one passing complete workflow/state fixture.
- Missing Phase 6.5 in workflow and missing Phase 6.5 in state must fail deterministically.
- Missing canonical Post items must fail deterministically.
- Collapsed later phases must fail deterministically.
- Malformed `autopilot-state.json` must return deterministic `input_error`.
- Validator output must be referenced in the PR packet and G6.5 evidence before implementation advances.

## Helper and Mode Matrix

| Group | Classification | Notes |
| --- | --- | --- |
| Mutation request/result model, registry extension, atomic writes, path guards, dirty guard, fixture harness, failure classes, promotion records | Slice 1 | Shared foundation only; no named helper promoted by Slice 1 alone. |
| `install-curated-set`, `install-codex-agents`, doctor install checks, safe repair, `project-fixup apply`, `ensure-reviewability-preset` | Slice 2 | Fake Claude/Codex homes and fake plugin caches by default. |
| `generate-pr-body`, `generate-uat-skeleton`, `final-reviewability-backstop`, PR packet/workflow-contract outputs | Slice 3 | Atomic generated outputs; preserve existing output contracts. |
| `multi-pr-emission`, `restack`, split-PR state, `migrate-structure`, `relocate-process-artifacts` | Slice 3 | Fake repositories and fake `gh` by default; live apply requires structured approval. |
| Generated-index write/regenerate modes, `plan-layers` marker-plan output, `validate-pr-packet` persistence/workflow-event upserts, `validate-pr-workflow-contract` workflow-event write mode | Slice 3 | Deferred write/apply modes only. |
| `detect-stack-manager` detect/link/sync/restack command-plan and evidence-persistence behavior | Slice 3 support | Emits decisions and command plans only; no mutating execution in detector. |
| XPLAT-005 read-only/advisory modes | Already accepted | Do not re-port. |
| Active repo-local gate migration, generated-payload selection/cutover, active Claude/Codex invocation cutover, native installed-cache UAT, release-readiness migration, update/autoheal proof, public claims | Out of scope | XPLAT-007 and XPLAT-008 own these surfaces; XPLAT-006 may only update the autopilot phase-coverage hardening source and generated mirror. |

## Safety Model

- Dry-run mode reports planned write, delete, copy, command, PR action, install repair, migration, relocation, or generated-output operations and performs no mutation.
- Apply mode requires explicit mode selection, valid inputs, satisfied boundary checks, clean-worktree checks where required, and approval evidence for live mutation.
- Approval evidence for live mutation must include approval id, approver, timestamp, channel, dry-run result id, dry-run hash, allowed boundaries, allowed operations, and optional expiration.
- Path resolution rejects external absolute paths, traversal, symlinks, directories where a file is required, devices, and writes outside declared repo/plugin/fake-home/fake-cache/temp boundaries.
- Generated JSON and Markdown are UTF-8 LF with one final newline. Targeted host-file edits preserve existing line endings or report explicit LF normalization.
- Multi-operation helpers preflight before the first write and report partial failure with rollback/manual remediation notes instead of promising global rollback.
- Subprocess use is argv-list only with captured stdout/stderr and bounded fixture inputs.

## Contracts and Data Model

Contract artifacts are required because the runner exposes structured helper
request/result shapes and reviewer-facing promotion/doctor proof records.

- `contracts/mutation-helper-request.schema.json`
- `contracts/mutation-helper-result.schema.json`
- `contracts/doctor-preflight-result.schema.json`
- `contracts/helper-promotion-record.schema.json`
- `contracts/autopilot-phase-coverage-report.schema.json`

The data model defines mutation requests/results, approval evidence,
planned/applied operations, install inventory, safe repair records, parity
fixtures, Bash-reference comparisons, promotion records, scope audits, and
autopilot phase coverage reports.

## PR Packet Traceability Requirements

The final PR packet must map:
- Slice 1 mutation primitives to changed files, fixture ids, Bash-reference evidence, promotion records, and rollback/manual remediation notes.
- Slice 2 install/doctor helpers to inventory records, fake-home fixture ids, repair classifications, and no-real-home proof.
- Slice 3 PR/restack/migration/relocation helpers to fake `gh`/fake repo fixture ids, command-capture evidence, approval-boundary proof, and known live-coverage limits.
- Autopilot phase-coverage hardening to `validate-autopilot-phase-coverage.py`, `test-autopilot-phase-coverage.py`, the passing workflow/state fixture, and failing fixtures for missing Phase 6.5, missing Post items, collapsed later phases, and malformed state JSON.
- Scope audit evidence proving no active Claude/Codex invocation behavior, hook, generated-payload selection/cutover, install guidance, public docs, release gate, or native UAT cutover changes landed, with allowed phase-coverage hardening source/mirror changes listed separately.

Known gaps in the PR packet must separate unpromoted in-scope helpers,
XPLAT-007/XPLAT-008 deferred cutover work, and live mutation coverage limits.

## Verification Plan

Focused proof:
- `python3 tests/speckit-pro/layer4-scripts/test-autopilot-phase-coverage.py`
- `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py`
- Runner fixture command for each promoted helper group, using fake repos/homes/caches and no network.
- Bash-reference comparison command for each Bash-backed promoted helper, using explicit argv-list subprocess calls.

Repository gates:
- `bash tests/speckit-pro/run-all.sh --layer 4`
- `bash tests/speckit-pro/run-all.sh --layer 1`
- `bash tests/speckit-pro/run-all.sh`

Scope audit:
- Review `git diff --name-only origin/main...HEAD` for forbidden active-cutover surfaces.
- Confirm no active Claude/Codex invocation behavior, hooks, generated-payload selection/cutover, public docs claims, repo-local release gates, or native UAT artifacts changed, and separately identify allowed phase-coverage hardening source/mirror changes.
- Confirm runner manifest/checksum metadata is updated after runner-owned Python files change.

## Phase Gate Alignment

- G3 passes when `plan.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md` exist with no unresolved clarification markers.
- G4 checklists must run integration, error-handling, reliability, and security domains because the feature writes state, repairs installs, plans PR actions, and validates autopilot state.
- G5 tasks must preserve the three-slice order and avoid XPLAT-007/XPLAT-008 cutover scope.
- G6 analysis must verify no drift across roadmap, design concept, spec, plan, tasks, and XPLAT-005 contracts.
- G6.5 must run the phase-coverage validator before implementation advances.
- G7 requires Python mutation-helper tests, Bash-reference comparisons, source-checkout proof, spec-index check, diff hygiene, relevant repo gates, and PR packet evidence.

## Out-of-Scope Boundaries

XPLAT-006 does not change active Claude Code or Codex invocation behavior,
generated-payload selection/cutover, install guidance, public documentation
claims, repo-local release-readiness gates, native matrix UAT,
installed-cache launch proof, update/autoheal proof, or public
native-platform support claims. The only allowed skill/payload changes are the
autopilot phase-coverage hardening source and generated mirror.
