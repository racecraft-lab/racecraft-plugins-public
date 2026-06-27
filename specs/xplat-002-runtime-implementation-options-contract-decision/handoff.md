# Handoff: XPLAT-002

Status: Ready for downstream specs after verification
Selected runtime: Go native executable packaged as small per-platform binaries

## What Changed

- Added `runtime-decision.md` with the selected runtime and rejected options.
- Added evidence records for JavaScript/TypeScript, Python, and small
  per-platform binary candidates.
- Updated the `speckit-pro-runner` contract with the selected runtime.
- Updated quickstart validation and this handoff record.

## Why

XPLAT-004 needs one runtime and command contract. The selected Go native binary
model best satisfies the no-post-cache-install constraint: users should not need
Node, Python, Bash, `jq`, package restoration, or network setup after the plugin
cache is populated.

## Non-Goals

- No runner implementation.
- No helper ports.
- No active invocation-path changes.
- No generated-payload cutover or broad payload rebuild.
- No README, docs-site, marketplace metadata, changelog, release-note, or public
  support-claim changes.
- No selected supply-chain controls.

## XPLAT-003 Supply-Chain Implication Matrix

| Candidate | Dependency/bootstrap footprint | Artifact shape | XPLAT-003 implications |
|---|---|---|---|
| JavaScript/TypeScript | Source JS needs Node on user PATH unless bundling Node; npm/package restoration is out of bounds after cache population. | JS files plus possible `node_modules`, bundled runtime, or SEA/native artifact. | Decide whether bundled Node is acceptable; if not selected, record rejection in control rationale. Lockfile, vulnerability scan, SBOM, checksums, signatures, and provenance would be required if revived. |
| Python | Source Python needs Python on user PATH unless embedding Python; `pip`/virtualenv restoration is out of bounds after cache population. | Python files, wheels, virtualenv, or embedded runtime/native bundle. | Decide whether embedded Python is acceptable if revisited. Controls would need package lock discipline, vulnerability scan, SBOM, checksums, signatures, and provenance. |
| Go native binary | No user-side runtime dependency after artifact is built; build toolchain needed only in release/build environment. | Per-platform executable artifacts under the generated payload, plus metadata for version/runtime-info. | Choose first-release and deferred controls for native binaries: platform matrix, generated artifact integrity, vulnerability scan path, checksums/signatures, SBOM/provenance, consumer-local verification, and truthful docs. |

XPLAT-002 records implications only. XPLAT-003 chooses controls and acceptance
gates.

## XPLAT-004 Implementation Input Bundle

| XPLAT-001 row | Owner bucket | Active invocation mode | Runner helper input |
|---|---|---|---|
| `SRC-READ-001` | `xplat-005-read-only-helper` | Read-only/advisory installed skills, hooks, agents, and helper scripts. | Build read-only helper IDs, operations, and modes after the runner foundation exists. |
| `SRC-MUT-001` | `xplat-006-mutation-helper` | Mutation, install, archive, scaffold, PR packet, and rollback-capable helpers. | Build mutation-safe helper IDs, operations, modes, rollback diagnostics, and apply/write fixtures after runner foundation. |
| `GEN-ACT-001` | `xplat-007-cutover-guidance` | Generated Claude/Codex payloads that mirror active source behavior. | Do not edit in XPLAT-004 except where the runner foundation explicitly needs source/generator alignment after XPLAT-003 controls. |

Explicit exclusions for XPLAT-004: `GEN-DOC-001`, `DOC-001`, `TEST-001`,
`HIST-001`, `REPO-ONLY-001`, and `EXCL-001` are not implementation inputs for
the runner foundation unless a later spec deliberately promotes them.

## Compatibility Adapter Records

| adapter_id | legacy_surface | xplat001_source_row | runner_helper_id | runner_operation | runner_mode | owner_bucket | owner_spec | removal_spec | removal_condition |
|---|---|---|---|---|---|---|---|---|---|
| `xplat-005-compat-read-only-helper-surface` | Read-only Bash/`.sh`/`jq` helper guidance and calls. | `SRC-READ-001` | `read-only-helper` | `invoke` | `read_only` | `xplat-005-read-only-helper` | `XPLAT-005` | `XPLAT-007` | Removed when read-only helper calls use the runner directly and generated payload cutover no longer needs legacy guidance. |
| `xplat-006-compat-mutation-helper-surface` | Mutation/install/PR-emission Bash helper guidance and calls. | `SRC-MUT-001` | `mutation-helper` | `invoke` | `mutation` | `xplat-006-mutation-helper` | `XPLAT-006` | `XPLAT-007` | Removed when mutation-capable helpers use the runner directly with rollback-safe fixtures and generated payload cutover no longer needs legacy guidance. |
| `xplat-007-compat-generated-payload-cutover` | Generated payload Bash/`.sh`/`jq` runtime references. | `GEN-ACT-001` | `generated-payload-cutover` | `verify-cutover` | `cutover` | `xplat-007-cutover-guidance` | `XPLAT-007` | `XPLAT-007` | Removed by final native release cutover after generated payloads point at the runner and native UAT passes. |

Evidence for each adapter is the XPLAT-001 row plus the selected
`speckit-pro-runner` contract. Adapters are migration records only, not a fourth
runtime candidate.

## Fixture Expectations for XPLAT-004

XPLAT-004 must implement fixture parity for: success, invalid JSON, missing
required field, path with spaces, Windows separators, missing prerequisite,
subprocess nonzero, subprocess timeout, stderr-only failure,
runtime-info/preflight, and at least one read-only legacy-helper comparison.

Each failure fixture must assert stdout `status`, process `exit_code`, stderr
diagnostic `code`, and required response fields.

## Verification Evidence

- `bash speckit-pro/skills/speckit-autopilot/scripts/count-markers.sh gaps specs/xplat-002-runtime-implementation-options-contract-decision` passed with `total=0`.
- `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh "$PWD"` regenerated XPLAT-002 after adding decision artifacts.
- `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"` passed with `spec-index: index current`.
- `bash speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh diff origin/main...HEAD` passed with warn status, no blockers, `reviewable_loc=0`, `production_files=0`, `total_files=21`, and `primary_surface_count=4`.
- `git diff --name-only` showed only tracked XPLAT-002 feature files; `git status --short` additionally showed the new XPLAT-002 decision/evidence/handoff files as untracked.
- `git diff --check` passed with no whitespace errors.
- `bash tests/speckit-pro/run-all.sh --layer 1` passed `1438/1438`.
- Broader `bash tests/speckit-pro/run-all.sh` was not run because no source, generator script, durable probe script, active invocation path, or generated payload changed unexpectedly.

## Known Gaps

- Installed Claude/Codex `speckit-pro-runner` cache invocation is not run because
  the runner does not exist in XPLAT-002.
- Go build-tool probing is unavailable on this host because `go` is not
  installed.
- Native Windows/macOS/Linux release-readiness UAT is deferred to XPLAT-007.

## Rollback / Flags

Rollback is document-only: revert the XPLAT-002 feature-directory artifacts.
There is no runtime flag because no active invocation path changes in this
spike.

## PR Review Packet

Review order:

1. `runtime-decision.md`
2. `evidence/*.md`
3. `contracts/speckit-pro-runner-contract.md`
4. `handoff.md`
5. `quickstart.md`
6. `SPEC-MOC.md` and `tasks.md`

Scope budget: final reviewability result is recorded in `quickstart.md`.

Traceability:

| Requirement / success criterion | Files |
|---|---|
| Evaluate all three candidates | `runtime-decision.md`, `evidence/*.md` |
| Select one runtime and contract | `runtime-decision.md`, `contracts/speckit-pro-runner-contract.md` |
| Explain rejections and tie-breaker | `runtime-decision.md` |
| Hand off XPLAT-003 implications | `handoff.md` |
| Hand off XPLAT-004 inputs and adapters | `handoff.md`, contract |
| Keep public claims unchanged | `quickstart.md`, final diff scope review |
