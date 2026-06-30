# Research: Cross-Platform Runner Foundation

## Decision 1: Source Package and Invocation

**Decision**: Put runner source under `speckit-pro/speckit_pro_runner/` and invoke it as `<python> -m speckit_pro_runner` from the package context.

**Rationale**: This matches the clarified XPLAT-004 boundary, keeps runner files out of generated payload mirrors, and supports module-style JSON stdin/stdout execution without shell launchers.

**Alternatives considered**:

- `speckit-pro/scripts/`: rejected because current payload build copies that tree into generated payloads.
- Direct script path: rejected because it weakens the package/module boundary and installed-payload parity.
- Full runner framework: rejected as too broad for a foundation slice.

## Decision 2: Runtime Substrate

**Decision**: Use Python 3.11+ standard library only.

**Rationale**: XPLAT-003 supersedes older native-binary wording and aligns the runner with official Spec Kit / `specify` prerequisites. Stdlib-only execution avoids package restore, virtual environment, and platform-specific dependency risk.

**Alternatives considered**:

- Go/Rust/Zig/native binaries: rejected by the current cross-platform runtime decision.
- Node or npm restore: rejected as an extra installed-plugin runtime substrate.
- Bash, Git Bash, WSL, PowerShell, or `jq`: rejected as required runner substrates.

## Decision 3: Envelope Ownership

**Decision**: The runner owns request parsing, deterministic validation, response construction, diagnostics, typed path rendering, and fixture-only subprocess result capture.

**Rationale**: XPLAT-002 requires stable JSON request/response semantics, status/exit-code behavior, typed paths, diagnostics, and subprocess records before real helper ports consume the runner.

**Alternatives considered**:

- Let each future helper validate envelopes: rejected because it would duplicate cross-platform contract behavior.
- Validate only happy paths in XPLAT-004: rejected because downstream helper ports need failing examples before migration.

## Decision 4: Preflight and Prerequisites

**Decision**: Preflight reports Python runtime details, platform details, plugin root, `specify` prerequisite status, runner identity, source-checkout context, and metadata pointers. Missing Python 3.11+ or missing `specify` fails closed.

**Rationale**: XPLAT-003 requires fail-closed prerequisite behavior and runner identity/preflight metadata before installed workflows can rely on the runner.

**Alternatives considered**:

- Warn-only missing prerequisites: rejected because it weakens later cutover safety.
- Python-only preflight: rejected because official Spec Kit / `specify` is part of the selected runtime boundary.

## Decision 5: Metadata Placement

**Decision**: Store `speckit-pro-runner.manifest.json` and `speckit-pro-runner.sha256` under `speckit-pro/speckit_pro_runner/` with `plugin_relative` source-checkout paths.

**Rationale**: Metadata travels with the source package for XPLAT-004 while avoiding generated payload propagation. The manifest keeps runner module identity, durable contract identity, and selected runtime identity distinct.

**Alternatives considered**:

- Metadata under `speckit-pro/scripts/`: rejected because that path is stale for XPLAT-004 and collides with payload-copy behavior.
- Metadata under `dist/**`: rejected because payload propagation and installed-cache proof are XPLAT-007 scope.

## Decision 6: Contract Fixture Shape

**Decision**: Use one compact Python stdlib fixture matrix consumed by `test-speckit-pro-runner.py`.

**Rationale**: A compact fixture file keeps review size bounded while covering valid envelopes, validation failures, typed paths, subprocess outcomes, diagnostics, runtime-info, and preflight.

**Alternatives considered**:

- Many per-case fixture files: rejected because it increases review noise without improving the foundation contract.
- Real helper parity fixtures: rejected because helper ports are XPLAT-005/XPLAT-006 scope.

## Decision 7: Two-Slice Delivery

**Decision**: Keep one XPLAT-004 spec/workflow but plan two reviewable PR slices.

**Rationale**: The accepted setup warning estimates roughly 420 reviewable LOC and suggests two slices. Slice 1 proves runner/preflight core; Slice 2 adds contract fixture parity and metadata.

**Alternatives considered**:

- One large PR: rejected because it concentrates runner, fixtures, metadata, and review evidence in one review.
- Child specs: rejected during scaffolding because the scope remains one foundation feature.
