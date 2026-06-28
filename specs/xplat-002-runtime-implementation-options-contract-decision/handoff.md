# Handoff: XPLAT-002

Status: Amended 2026-06-28; ready for downstream specs after PR #267 update
Selected runtime: Python standard-library runner aligned with official Spec Kit
/ `specify` prerequisites

## What Changed

- Amended `runtime-decision.md` so Python is selected and the previous Go
  native-binary choice is rejected historical evidence, not a fallback.
- Kept evidence records for JavaScript/TypeScript, Python, and the rejected
  small per-platform binary path so reviewers can trace why compiled binaries
  are no longer valid XPLAT candidates.
- Updated the `speckit-pro-runner` contract with the selected runtime.
- Updated quickstart validation and this handoff record.

## Why

XPLAT-004 needs one runtime and command contract. The amended Python model best
fits the user journey because SpecKit-Pro may require the official Spec Kit /
`specify` prerequisite boundary, and official Spec Kit requires Python 3.11+.
That lets SpecKit-Pro avoid a second user-facing implementation toolchain and
avoid per-platform Go/Rust/Zig binary distribution in XPLAT.

The selected model still preserves the no-post-cache-install constraint for
plugin-only dependencies: users should not need Node, Bash, `jq`, Go, Rust, Zig,
`pip install`, virtualenv restoration, package restoration, or network setup
after the plugin cache is populated.

## Non-Goals

- No runner implementation.
- No helper ports.
- No active invocation-path changes.
- No generated-payload cutover or broad payload rebuild.
- No README, docs-site, marketplace metadata, changelog, release-note, or public
  support-claim changes.
- No selected supply-chain controls.

## XPLAT-003 Supply-Chain Implication Matrix

| Field | JavaScript/TypeScript | Python | Native binary (rejected evidence only) |
|---|---|---|---|
| Decision status | Rejected | Selected | Rejected historical candidate |
| Dependency footprint | Requires user-side Node unless Node is bundled. | Requires official Spec Kit prerequisite: Python 3.11+ and `specify`; no plugin-only third-party packages. | No user-side runtime dependency after artifact build, but adds maintainer build toolchain. |
| Bootstrap footprint | Source JS would require `npm install`, restored `node_modules`, or a bundled runtime; post-cache setup is out of bounds. | Uses existing Spec Kit prerequisite; no `pip install`, virtualenv restoration, or embedded runtime allowed after plugin install. | Rejected: build environment and installed platform artifacts are not XPLAT work. |
| Manifest/lockfile behavior | Would require package manifest and lockfile policy if dependencies or bundled Node are introduced. | Python source integrity and stdlib-only policy required; no package lockfile unless plugin-only dependencies are introduced later. | Rejected: would require Go module and release lock policy. |
| Generated output types | JS files, `node_modules`, bundled Node, or SEA/native artifact. | Python source runner plus optional thin launcher metadata. | Rejected path: per-platform executable metadata is not an XPLAT output. |
| Assumption type/status | External package manager or embedded runtime: unverified for installed-cache users. | Product prerequisite: verified by doctor/preflight before workflow execution. | Rejected native binary path; not XPLAT evidence. |
| Origin evidence | Node local probe and official docs show runtime behavior; plugin platform docs do not guarantee Node in installed cache. | Python local probe plus official Spec Kit prerequisite boundary; XPLAT-004 must prove installed-cache launch. | Historical Go docs support static/native build mechanics, but XPLAT rejects this path because Spec Kit already requires Python. |
| Build/release path | Rejected for XPLAT unless a future non-XPLAT initiative deliberately introduces and owns Node packaging controls. | XPLAT-003 chooses Python source integrity and prerequisite verification controls; XPLAT-004 builds the runner. | Rejected: native artifact controls are not part of XPLAT. |
| Vulnerability-scan path | npm package and bundled-runtime scanning would be required outside XPLAT if Node packaging were ever introduced. | Python source/static scan and stdlib-only verification; dependency scanning remains small unless packages are added. | Rejected: would require Go module scan plus native artifact/release scan path. |
| Checksum/signature/SBOM/provenance feasibility | Feasible but expands output surface to packages and possible runtime bundle. | Feasible for source payloads and generated manifests; no native artifact matrix for first release. | Rejected: each platform executable would need verification that XPLAT no longer accepts. |
| Consumer-local verification ideas | Runtime-info would need to report Node version/path and package availability. | Runtime-info/preflight reports Python path/version, `specify` path/version, platform, plugin root, capabilities, and prerequisite state. | Runtime-info/preflight reports runner version, platform, architecture, plugin root, capabilities, and artifact state. |
| Offline/update implications | Offline users cannot rely on package restoration after cache population. | Offline users can run if official Spec Kit prerequisites are already installed; updates replace Python source payloads. | Rejected: packaged executable update semantics are not an XPLAT path. |
| Distribution trust root | Marketplace payload plus package/runtime supply chain if a future non-XPLAT initiative introduces it. | Marketplace payload plus official Spec Kit prerequisite and Python source integrity. | Rejected: release-built native artifacts and integrity metadata are not an XPLAT trust root. |
| Transitive/build-time/native dependencies | npm package graph or bundled Node runtime; native npm modules possible. | No plugin-only Python dependency graph for first release. | Rejected: Go toolchain, modules, OS/arch cross-build inputs, and native artifact packaging are not XPLAT inputs. |
| Build environment inputs | Node toolchain, package manager, lockfile, bundler, or SEA/native build would be non-XPLAT work. | Python syntax/test/lint tooling and release manifest generation. | Rejected: Go toolchain, platform matrix, signing/checksum/SBOM/provenance tooling are not XPLAT inputs. |
| Runtime/install execution risk | Fails installed-cache gate unless runtime is bundled or guaranteed. | Must preflight Python 3.11+ and `specify`; unsupported installs fail closed with remediation. | Rejected: generated artifact availability would remain a separate proof burden. |
| Maintenance posture | Higher churn from package/runtime dependency management if a future non-XPLAT initiative introduces it. | Best first-release ergonomics if stdlib-only and prerequisite checks are reliable. | Rejected: smaller user runtime surface is outweighed by native release discipline and duplicated implementation model. |
| Evidence gaps | No installed-cache Node guarantee; no bundled Node decision; no package restoration path. | Windows/macOS/Linux installed-cache launch and exact interpreter discovery must be proven in XPLAT-004. | Historical only: local Go unavailable; no built runner exists; platform artifact controls are not XPLAT work. |

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
| `xplat-007-compat-generated-payload-cutover` | Generated payload Bash/`.sh`/`jq` runtime references. | `GEN-ACT-001` | `generated-payload-cutover` | `verify-cutover` | `cutover` | `xplat-007-cutover-guidance` | `XPLAT-007` | `XPLAT-007` | Removed by final Python-runner release cutover after generated payloads point at the runner and Windows/macOS/Linux UAT passes. | XPLAT-001 `GEN-ACT-001` plus selected Python runner contract, runtime-info/preflight, fixture parity, and generated payload cutover expectations. |

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
- Windows Python launcher discovery and installed-cache invocation remain
  XPLAT-004 proof items.
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
