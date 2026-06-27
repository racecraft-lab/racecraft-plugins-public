# Handoff: XPLAT-002

Status: In Review (PR #266 pending merge); ready for downstream specs after merge
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

| Field | JavaScript/TypeScript | Python | Go native binary |
|---|---|---|---|
| Decision status | Rejected | Rejected | Selected |
| Dependency footprint | Requires user-side Node unless Node is bundled. | Requires user-side Python unless Python is embedded. | No user-side runtime dependency after artifact build. |
| Bootstrap footprint | Source JS would require `npm install`, restored `node_modules`, or a bundled runtime; post-cache setup is out of bounds. | Source Python would require `pip install`, virtualenv restoration, or an embedded runtime; post-cache setup is out of bounds. | Build environment installs Go only before release; installed users receive platform artifacts. |
| Manifest/lockfile behavior | Would require package manifest and lockfile policy if dependencies or bundled Node are introduced. | Would require package manifest, lockfile, wheel, or virtualenv policy if dependencies or embedded Python are introduced. | Go module and release lock policy belong to XPLAT-003/XPLAT-004 once source exists. |
| Generated artifact types | JS files, `node_modules`, bundled Node, or SEA/native artifact. | Python source, wheels, virtualenv, or embedded runtime/native bundle. | Per-platform executable plus runtime-info/preflight metadata. |
| Artifact assumption type/status | External package manager or embedded runtime: unverified for installed-cache users. | External package manager or embedded runtime: unverified for installed-cache users. | Native binary: selected model, but artifact integrity controls are unverified until XPLAT-003. |
| Artifact origin evidence | Node local probe and official docs show runtime behavior; plugin platform docs do not guarantee Node in installed cache. | Python local probe and official docs show runtime behavior; plugin platform docs do not guarantee Python in installed cache. | Go official docs support static/native build model; local `go` toolchain is unavailable, so build evidence is deferred. |
| Build/release path | XPLAT-003 would need to decide whether to vendor dependencies, bundle Node, or forbid this path. | XPLAT-003 would need to decide whether to embed Python, vendor wheels, or forbid this path. | XPLAT-003 chooses controls; XPLAT-004 builds the runner; XPLAT-007 validates generated payload cutover. |
| Vulnerability-scan path | npm package and bundled-runtime scanning would be required if revived. | Python package, wheel, and embedded-runtime scanning would be required if revived. | Go module scan plus native artifact/release scan path required before public cutover. |
| Checksum/signature/SBOM/provenance feasibility | Feasible but expands artifact surface to packages and possible runtime bundle. | Feasible but expands artifact surface to packages and possible embedded interpreter. | Feasible and required for release controls, but not selected in XPLAT-002. |
| Consumer-local verification ideas | Runtime-info would need to report Node version/path and package availability. | Runtime-info would need to report Python version/path and package availability. | Runtime-info/preflight reports runner version, platform, architecture, plugin root, capabilities, and prerequisite state. |
| Offline/update implications | Offline users cannot rely on package restoration after cache population. | Offline users cannot rely on package restoration after cache population. | Offline users can run packaged artifacts; updates must replace signed/checksummed binaries. |
| Distribution trust root | Marketplace payload plus package/runtime supply chain if revived. | Marketplace payload plus package/runtime supply chain if revived. | Marketplace payload plus release-built native artifacts and their integrity metadata. |
| Transitive/build-time/native dependencies | npm package graph or bundled Node runtime; native npm modules possible. | Python package graph, wheels, or embedded interpreter; native wheels possible. | Go toolchain, modules, OS/arch cross-build inputs, and native artifact packaging. |
| Build environment inputs | Node toolchain, package manager, lockfile, bundler or SEA/native build if revived. | Python toolchain, package manager, lockfile, wheel/embedding tooling if revived. | Go toolchain, platform matrix, signing/checksum/SBOM/provenance tooling. |
| Runtime/install execution risk | Fails installed-cache gate unless runtime is bundled or guaranteed. | Fails installed-cache gate unless runtime is embedded or guaranteed. | Runtime model viable for no user-side runtime dependency; actual installed-cache invocation and artifact availability remain XPLAT-004/XPLAT-007 proof. |
| Maintenance posture | Higher churn from package/runtime dependency management if revived. | Higher churn from Python version/package/runtime embedding management if revived. | Smaller runtime surface but requires native release discipline. |
| Evidence gaps | No installed-cache Node guarantee; no bundled Node decision; no package restoration path. | No installed-cache Python guarantee; no embedded Python decision; no package restoration path. | Local Go unavailable; no built runner exists; platform artifact controls and UAT deferred. |

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

| adapter_id | legacy_surface | xplat001_source_row | runner_helper_id | runner_operation | runner_mode | owner_bucket | owner_spec | removal_spec | removal_condition | evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| `xplat-005-compat-read-only-helper-surface` | Read-only Bash/`.sh`/`jq` helper guidance and calls. | `SRC-READ-001` | `read-only-helper` | `invoke` | `read_only` | `xplat-005-read-only-helper` | `XPLAT-005` | `XPLAT-007` | Removed when read-only helper calls use the runner directly and generated payload cutover no longer needs legacy guidance. | XPLAT-001 `SRC-READ-001` plus `speckit-pro-runner` contract sections for dispatch, read-only mode, JSON I/O, paths, subprocess, and diagnostics. |
| `xplat-006-compat-mutation-helper-surface` | Mutation/install/PR-emission Bash helper guidance and calls. | `SRC-MUT-001` | `mutation-helper` | `invoke` | `mutation` | `xplat-006-mutation-helper` | `XPLAT-006` | `XPLAT-007` | Removed when mutation-capable helpers use the runner directly with rollback-safe fixtures and generated payload cutover no longer needs legacy guidance. | XPLAT-001 `SRC-MUT-001` plus `speckit-pro-runner` contract sections for mutation mode, rollback diagnostics, exit codes, paths, subprocess, and prerequisite records. |
| `xplat-007-compat-generated-payload-cutover` | Generated payload Bash/`.sh`/`jq` runtime references. | `GEN-ACT-001` | `generated-payload-cutover` | `verify-cutover` | `cutover` | `xplat-007-cutover-guidance` | `XPLAT-007` | `XPLAT-007` | Removed by final native release cutover after generated payloads point at the runner and native UAT passes. | XPLAT-001 `GEN-ACT-001` plus selected Go runner contract, runtime-info/preflight, fixture parity, and generated payload cutover expectations. |

Adapters are migration records only, not a fourth runtime candidate.

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
- `bash speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh diff origin/main...HEAD` passed with honored infra exception, `reviewable_loc=0`, `production_files=0`, `total_files=33`, and `primary_surface_count=5`.
- `git diff --name-only origin/main...HEAD` showed tracked XPLAT-002 workflow and feature artifacts, roadmap/spec-map refreshes, PR packet title tooling/tests, and Claude/Codex payload mirrors for XPLAT scope support; no README, docs-site runtime, marketplace metadata, changelog, release-note, active installed runtime invocation path, or public support-claim surface changed.
- `git diff --check` passed with no whitespace errors.
- `bash tests/speckit-pro/run-all.sh --layer 1` passed `1438/1438`.
- `bash tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh` passed `93/93`.
- `bash tests/speckit-pro/layer4-scripts/test-validate-pr-workflow-contract.sh` passed `17/17`.
- Broader `bash tests/speckit-pro/run-all.sh` was attempted; focused payload determinism now passes, but the full suite remains blocked by baseline DOC-014 privacy-scan terms already present on `origin/main`.

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
