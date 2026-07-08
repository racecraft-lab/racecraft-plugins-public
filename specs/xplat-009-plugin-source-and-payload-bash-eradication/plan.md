# Implementation Plan: Plugin Source and Payload Bash Eradication

**Branch**: `codex/xplat-009-plugin-source-and-payload-bash-eradication` | **Date**: 2026-07-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/xplat-009-plugin-source-and-payload-bash-eradication/spec.md`

## Summary

XPLAT-009 removes the remaining plugin-source Bash substrate while preserving
the XPLAT-008 installed-runtime contract: direct Python 3.11+
`speckit_pro_runner` invocation with no Bash, Git Bash, WSL,
PowerShell-specific command language, or `jq` runtime path. The implementation
uses two vertical slices: first port active plugin-source script behavior to
Python runner/helper/gate operations and delete live `.sh` files, then rebuild
Claude/Codex payloads from source and prove source, generated payloads, and a
bounded installed-cache artifact pass one Python-backed zero-Bash guard.

## Technical Context

**Language/Version**: Python 3.11+ standard library for runner/helper/gate
implementation; Markdown and JSON for skill, agent, payload, fixture, and
evidence artifacts.

**Primary Dependencies**: Existing `speckit-pro/speckit_pro_runner/` package,
existing helper and gate registries, existing payload-completeness operation,
existing Layer 1 and Layer 4 shell/Python test harnesses. No new runtime
dependency is planned.

**Storage**: Checked-in repository files only. Required installed-cache proof
uses a bounded source-derived fixture or temporary root plus committed evidence;
mutable real user cache state is supplemental only and cannot satisfy release
readiness.

**Testing**: Focused runner/helper/gate tests, Layer 1 structural validation,
focused Layer 4 tests, payload-completeness apply/read-only evidence,
installed-cache proof, active-instruction no-shell/no-`jq` guard, release
readiness fixture coverage, and spec-index checks.

**Target Platform**: Claude Code and Codex plugin source and generated plugin
payloads. Installed-runtime behavior remains the cross-platform Python runner
contract from XPLAT-008.

**Project Type**: Plugin/runtime tooling with generated payload artifacts.

**Performance Goals**: Guard scans must be deterministic and bounded. Findings
returned through the runner envelope must be capped while still reporting
blocking counts and classified counts for the full scan.

**Constraints**: No live Bash fallback, Python wrapper around live `.sh` files,
hidden shell dispatch, staged deprecation path, active `jq` requirement, Git
Bash/WSL guidance, or PowerShell-specific command-language requirement may
remain in in-scope source, generated payloads, or installed-cache proof.

**Scale/Scope**: The authoritative live source baseline is 35 `.sh` files under
`speckit-pro/`. Generated payload baseline is zero `.sh` files under
`dist/claude/speckit-pro` and `dist/codex/speckit-pro`. In-scope active
surfaces are `speckit-pro/skills/**`, `speckit-pro/codex-skills/**`,
`speckit-pro/agents/**`, `speckit-pro/codex-agents/**`, `speckit-pro/hooks/**`,
`speckit-pro/codex-hooks.json`, `speckit-pro/scripts/**`, generated Claude and
Codex payload mirrors, and bounded installed-cache proof. Repository-wide
`tests/**`, top-level `scripts/**`, `.specify/**`, hooks outside the plugin
package, and GitHub workflow dispatch glue remain XPLAT-010 scope.

**Reviewability Budget**: Primary surface `harness/adapter`; secondary surfaces
`docs/process`, `seed/config`, and `scheduler/runtime`. Setup warned at
approximately 527-700 projected reviewable LOC, 20 production files, and 30
total files, above the advisory warning thresholds. The accepted split decision
is one XPLAT-009 workflow with two vertical PR-ready slices. Child specs are not
created unless Tasks or later evidence proves either slice cannot remain
reviewable.

## Declared File Operations

The parser-compatible declarations below are the planned hand-authored source,
test, fixture, and contract surface for XPLAT-009. Generated payload output and
deleted `.sh` files are reviewed separately in the review packet and are not
manual source-of-truth edits.

- MODIFIED speckit-pro/speckit_pro_runner/helpers/registry.py
- MODIFIED speckit-pro/speckit_pro_runner/helpers/read_only.py
- MODIFIED speckit-pro/speckit_pro_runner/helpers/install.py
- MODIFIED speckit-pro/speckit_pro_runner/helpers/pr_emission.py
- MODIFIED speckit-pro/speckit_pro_runner/gates/registry.py
- MODIFIED speckit-pro/speckit_pro_runner/gates/active_path_guard.py
- MODIFIED speckit-pro/speckit_pro_runner/gates/payloads.py
- MODIFIED speckit-pro/speckit_pro_runner/gates/release.py
- MODIFIED speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- MODIFIED speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256
- MODIFIED speckit-pro/skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/skills/speckit-install/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-install/SKILL.md
- MODIFIED speckit-pro/skills/**
- MODIFIED speckit-pro/codex-skills/**
- MODIFIED speckit-pro/agents/**
- MODIFIED speckit-pro/codex-agents/**
- MODIFIED speckit-pro/hooks/hooks.json
- MODIFIED speckit-pro/codex-hooks.json
- MODIFIED speckit-pro/scripts/**
- MODIFIED speckit-pro/README.md
- MODIFIED README.md
- MODIFIED tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py
- MODIFIED tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py
- MODIFIED tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py
- NEW tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/allowlist.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/zero-bash-guard-cases.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache-proof.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/requests/zero-bash-guard.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/requests/payload-completeness-apply.json
- NEW docs/ai/specs/.process/XPLAT-009-source-inventory.md
- NEW docs/ai/specs/.process/XPLAT-009-zero-bash-guard-result.json
- NEW docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json
- NEW docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|---|---|---|
| Plugin Structure Compliance | PASS | Source cleanup preserves plugin directories, generated payloads are rebuilt from source, and Layer 1 structural validation remains required. |
| Script Safety | PASS | The plan removes plugin Bash scripts instead of adding or retaining live shell implementations. |
| Semantic Versioning | PASS | Version metadata remains release-please managed; no manual version bump is planned. |
| Test Coverage Before Merge | PASS | Each slice requires focused tests before source deletion, payload rebuild, or guard tightening. |
| Conventional Commits | PASS | PR title and commits stay within the existing Conventional Commit pattern. |
| KISS, Simplicity & YAGNI | PASS | The plan extends direct runner/helper/gate operations and explicit allowlists instead of adding wrapper layers. |

**Primary review surface**: `harness/adapter`

**Secondary review surfaces**: `docs/process`, `seed/config`,
`scheduler/runtime`

**Budget decision**: Warning accepted. Two vertical slices are sufficient
because Slice 1 can end with source-level behavior/guidance cleanup and Slice 2
can independently validate source-derived payload/cache proof and release
guards. No child spec is created during Plan.

**PR review packet source**: The PR packet must use this plan, `research.md`,
`data-model.md`, contract schemas, guard evidence under
`docs/ai/specs/.process/`, and payload/cache proof artifacts to describe what
changed, why, non-goals, review order, scope budget, traceability,
verification, known gaps, and rollback notes.

## Project Structure

### Documentation (this feature)

```text
specs/xplat-009-plugin-source-and-payload-bash-eradication/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── historical-allowlist-entry.schema.json
│   ├── installed-cache-proof.schema.json
│   ├── zero-bash-guard-request.schema.json
│   └── zero-bash-guard-result.schema.json
└── tasks.md
```

### Source Code (repository root)

```text
speckit-pro/
├── speckit_pro_runner/
│   ├── helpers/
│   └── gates/
├── skills/
├── codex-skills/
├── agents/
├── codex-agents/
├── hooks/
└── scripts/

dist/
├── claude/speckit-pro/
└── codex/speckit-pro/

tests/speckit-pro/layer4-scripts/
├── test-speckit-pro-read-only-helpers.py
├── test-speckit-pro-mutation-helpers.py
├── test-speckit-pro-gates.py
└── fixtures/xplat-009-zero-bash/

docs/ai/specs/.process/
├── XPLAT-009-source-inventory.md
├── XPLAT-009-zero-bash-guard-result.json
├── XPLAT-009-payload-completeness-result.json
└── XPLAT-009-installed-cache-proof.json
```

**Structure Decision**: XPLAT-009 stays inside the existing plugin runner,
plugin source, generated payload, Layer 4 fixture, and process-evidence layout.
No new package, service, or external dependency is introduced.

## Phase 0: Research and Decisions

Research is recorded in [research.md](./research.md). Key decisions:

1. Keep one workflow with two vertical slices; do not create child specs during
   Plan.
2. Treat the 35 live `.sh` files under `speckit-pro/` as the authoritative
   baseline.
3. Port active behavior before deleting scripts; classify delete-only only when
   no active owner remains.
4. Active registries and active outputs expose Python helper/gate operation IDs
   after shell removal; legacy `.sh` names may remain only as inactive
   provenance or allowlisted historical/archive references.
5. Add one Python runner guard contract for source, generated payloads, and
   bounded installed-cache proof.
6. Require historical allowlist entries to include path, reason, scope,
   category, and release-readiness exclusion.
7. Rebuild generated payloads through `payload-gate/payload-completeness` apply
   mode; do not hand-edit `dist/**` as source of truth.
8. Require bounded, source-derived installed-cache proof; mutable real user
   cache evidence cannot satisfy release readiness.
9. Preserve XPLAT-008 native UAT as out-of-scope blocker context.

## Phase 1: Design and Contracts

Design artifacts:

- [data-model.md](./data-model.md) defines inventory records, operation
  ownership records, active-instruction findings, allowlist entries, payload
  rebuild records, installed-cache proof records, and guard results.
- [contracts/zero-bash-guard-request.schema.json](./contracts/zero-bash-guard-request.schema.json)
  defines the runner request envelope for the single zero-Bash guard.
- [contracts/zero-bash-guard-result.schema.json](./contracts/zero-bash-guard-result.schema.json)
  defines the bounded guard result and finding shape.
- [contracts/historical-allowlist-entry.schema.json](./contracts/historical-allowlist-entry.schema.json)
  defines the release-readiness-excluded allowlist entry shape.
- [contracts/installed-cache-proof.schema.json](./contracts/installed-cache-proof.schema.json)
  defines required source-derived installed-cache proof.
- [quickstart.md](./quickstart.md) defines maintainer verification flow for the
  two slices.

## Implementation Strategy

### Slice 1: Active Plugin-Source Bash Removal

1. Write or tighten tests for Python ownership of active helper/gate behavior
   before deleting source scripts.
2. Inventory all 35 live `.sh` files and classify each as Python-owned port,
   delete-only obsolete, or historical/inactive provenance.
3. Promote active read-only helper records and active mutation helper records to
   Python operation IDs. Registry records must not expose runnable `.sh` paths
   as active behavior after the script is removed.
4. Port remaining active behavior into `speckit_pro_runner.helpers.*` or
   `speckit_pro_runner.gates.*`. For command-plan-only live behavior, either
   implement bounded Python semantics or explicitly keep it out of release
   readiness until a Python operation owns it.
5. Remove live `.sh` files under `speckit-pro/` after their active behavior is
   ported or confirmed obsolete.
6. Update active source guidance in skills, agents, hooks, README, and install
   docs to point at Python runner/helper/gate operation IDs.
7. Run source-level guard proof and Layer 1/Layer 4 focused checks.

### Slice 2: Payload Rebuild and Zero-Bash Proof

1. Rebuild Claude and Codex payloads from cleaned source through
   `payload-gate/payload-completeness` apply mode.
2. Produce payload completeness evidence with source roots, transform records,
   file-tree hashes, and zero missing/extra/mismatched/path-leaking files.
3. Extract or copy rebuilt payloads into a bounded source-derived installed-cache
   fixture or temporary root. Do not use mutable real user cache state as the
   required proof.
4. Run `active-path-guard/zero-bash-guard` across `speckit-pro/`,
   `dist/claude/speckit-pro`, `dist/codex/speckit-pro`, and installed-cache
   proof roots or records.
5. Wire the zero-Bash result into release readiness so missing roots, missing
   installed-cache proof, blocking findings, or allowlist evidence misuse block
   readiness.
6. Preserve XPLAT-008 native UAT gaps as known release context and avoid public
   native-platform readiness overclaims.

## Guard Architecture

The selected guard is a Python runner operation:

- `helper_id`: `active-path-guard`
- `operation`: `zero-bash-guard`
- `mode`: `read_only`
- Inputs: source roots, generated payload roots, installed-cache proof records
  or roots, and historical allowlist entries.
- Blocking categories: retained `.sh` files, active Bash guidance, active `jq`
  requirements, shell interpolation guidance, Git Bash or WSL dependency,
  PowerShell-specific command-language dependency, and Unix-only active
  assumptions.
- Output: runner JSON envelope with `status`, `blocking_count`,
  `classified_counts`, bounded `findings`, and `zero_bash_guard_blocked` when
  blocking findings are present.

Historical/archive references are allowed only through explicit allowlist
entries with path, reason, scope, category, and `release_readiness_excluded:
true`. Allowlisted entries never count as active behavior or release-ready
proof.

## Non-goals

- Repository-wide Bash cleanup under top-level `tests/**`, top-level
  `scripts/**`, `.specify/**`, hooks outside the plugin package, and GitHub
  workflow dispatch glue. XPLAT-010 owns this.
- Completing XPLAT-008 native operator UAT rows or changing public
  native-platform release readiness claims.
- Rewriting historical/archive prose solely to remove old Bash wording.
- Adding a new runtime dependency, package manager requirement, shell fallback,
  Git Bash/WSL workaround, PowerShell-specific command language, or `jq` path.

## Rollback and Safety

- Slice 1 rollback is a normal git revert of source/registry/guidance changes
  before payload rebuild. Tests must prove Python ownership before script
  deletion to reduce partial-removal risk.
- Slice 2 rollback is a normal git revert of generated payload, proof fixture,
  and release-readiness guard changes. Payloads are regenerated from source
  instead of manually edited, so drift can be repaired by rerunning the runner
  payload-completeness apply operation.
- If zero-Bash proof fails, keep the failure as blocking evidence and do not
  count allowlist entries or mutable real cache scans as release-ready proof.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Reviewability warning across several surfaces | XPLAT-009 must remove source scripts, update active guidance, rebuild payloads, and add proof gates in one dependency that unblocks XPLAT-010 | Child specs would duplicate guard/payload work and were rejected by the accepted Design Concept unless later evidence proves the two-slice plan is not reviewable |
| New zero-Bash guard contract | One runner operation must cover source, generated payloads, and bounded installed-cache proof with a reusable release-readiness result | Simple independent scans would not provide runner-envelope findings, release-readiness integration, or allowlist misuse blocking |
