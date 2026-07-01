# Feature Specification: Cross-Platform Runner Foundation

**Feature Branch**: `codex/xplat-004-cross-platform-runner-foundation`

**Created**: 2026-06-30

**Status**: Draft

**Input**: User description: "Create the minimal Python 3.11+ standard-library runner foundation for SpecKit Pro installed Claude Code and Codex workflows, preserving the XPLAT-002 command envelope and XPLAT-003 runtime decision while avoiding helper ports, public native-platform claims, and generated payload cutover."

## Clarifications

### Session 1 - Package and Entrypoint Shape

- XPLAT-004 locks the runner source package at `speckit-pro/speckit_pro_runner/` and the supported module invocation as `<python> -m speckit_pro_runner`.
- `<python>` means a discovered Python 3.11+ executable. Discovery starts with an explicit `SPECKIT_PRO_PYTHON` override when present, then may use the current Python interpreter or platform PATH candidates, and must reject candidates below Python 3.11.
- XPLAT-004 must not place runner source under `speckit-pro/scripts/` because that directory is copied into generated Claude/Codex payloads by the existing payload builder; generated payload propagation remains XPLAT-007 scope.
- Runner metadata uses `plugin_relative` paths rooted at `speckit-pro/` in `source_checkout` context for XPLAT-004. Installed-cache context is recorded as deferred to XPLAT-007.
- Layer 4 keeps `tests/speckit-pro/run-all.sh --layer 4` as the outer deterministic gate, but runner-specific tests use a Python stdlib test entrypoint such as `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py`. That Python test launches the runner with argv form and `shell=False`, not through a new shell launcher.
- Preflight and runtime-info requests use the XPLAT-002 JSON envelope with `schema_version: "1.0"`, `helper_id: "runner"`, `operation: "preflight"` or `"runtime-info"`, `mode: "read_only"`, and JSON inputs on stdin. CLI argv is reserved for command metadata such as `--help` and `--version`.

### Session 2 - Contract Fixture Matrix

- Invalid JSON, invalid envelope, unsupported schema version, and missing required fields are four separate contract fixture cases. Each returns one stdout JSON response with `status: "input_error"`, process `exit_code: 2`, `legacy_exit_code: null`, and line-delimited stderr JSON with `severity: "error"`, `source: "runner"`, a bounded `remediation` object, and one of the stable diagnostic codes `invalid_json`, `invalid_envelope`, `unsupported_schema_version`, or `missing_required_field`.
- Typed path fixtures accept only typed path objects. They preserve `kind`, `value`, and reader `display`; paths with spaces must not split, Windows separators must not imply POSIX-only behavior, and traversal is rejected only when it escapes the declared trust boundary.
- Missing prerequisite fixtures use test-controlled discovery for `specify` and operation tools after Python starts. A launched Python runtime below 3.11 returns `status: "missing_prerequisite"`, process `exit_code: 3`, diagnostic code `python_too_old`, and structured remediation. Missing or undiscoverable `specify` returns `status: "missing_prerequisite"`, process `exit_code: 3`, diagnostic code `specify_missing`, and structured remediation. Host-level failure to launch any Python 3.11+ executable is outside the runner stdout guarantee; discovery/preflight tests and runbook evidence must record diagnostic code `python_launcher_unavailable`, block downstream helper execution, and provide structured remediation without claiming a runner response was produced.
- Subprocess nonzero, timeout, and stderr-only failure fixtures stay distinct. All three return `status: "subprocess_failure"`, process `exit_code: 4`, captured subprocess fields, and diagnostic codes `subprocess_nonzero`, `subprocess_timeout`, or `subprocess_stderr_only_failure`; stderr-only failure is represented by an explicit fixture flag such as `stderr_is_failure: true`. XPLAT-004 fixture subprocesses must set an explicit timeout at or below 5 seconds and cap captured stdout and stderr at 16 KiB per stream, recording byte counts, limit, and truncation flags in the failure record.
- Runtime-info/preflight preserves the XPLAT-002 response envelope while using the XPLAT-003/XPLAT-004 Python source-checkout identity: `selected_runtime_name: "python-stdlib-runner"`, actual Python version, platform and architecture, `source_vs_installed_context: "source_checkout"`, `plugin_relative` plugin-root/path metadata, Python and `specify` prerequisite records, and runner checksum/manifest pointers with `verification_status`. Do not use `verified` unless current metadata was actually checked; preflight must fail closed with `status: "missing_prerequisite"`, process `exit_code: 3`, and one of `runner_metadata_missing`, `runner_metadata_incomplete`, `runner_metadata_mismatch`, or `runner_metadata_not_checked` when required source metadata is absent, incomplete, stale/mismatched, or skipped.
- XPLAT-002 controls durable envelope, status, exit, diagnostics, typed-path, subprocess, and runtime-info/preflight categories. XPLAT-003 supersedes stale Go/native-binary runtime identity, and XPLAT-004 controls the source package layout and source-checkout context until XPLAT-007.

### Session 3 - Metadata and Claim Boundary

- Source-checkout runner metadata lives with the runner package at `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` and `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`. Archived XPLAT-003 examples under `speckit-pro/scripts/` are stale path examples for XPLAT-004; XPLAT-007 owns final installed-payload metadata placement.
- Checksum coverage includes runner implementation source files under `speckit-pro/speckit_pro_runner/**.py` and any future thin launchers. The checksum file and manifest file are not included in their own checksum set.
- The manifest keeps identities distinct: Python module/package `runner_name: "speckit_pro_runner"`, durable contract identity `runner_contract_id: "speckit-pro-runner"`, runtime identity `selected_runtime_name: "python-stdlib-runner"`, plus `contract_version`, `plugin_version`, `runner_version`, `source_revision`, `python_minimum_version`, `specify_required`, `checksum_algorithm`, and `runner_files[]`.
- Runtime-info/preflight emits typed `plugin_relative` path objects for the plugin root, runner package, manifest file, and checksum file, sets `source_vs_installed_context: "source_checkout"`, computes source-checkout checksums when metadata is present, and uses `verification_status` values such as `verified`, `mismatch`, `missing_metadata`, `incomplete_metadata`, or `not_checked`. Preflight readiness is not `ok` unless required metadata is present, complete, checked, and current.
- XPLAT-004 proves source-checkout runner invocation, local preflight/runtime-info, XPLAT-002 envelope fixtures, fail-closed prerequisite and metadata fixtures, manifest JSON validation, source checksum coverage, deterministic diagnostic/remediation records, and deterministic Windows/Linux runbook fixtures. Windows/Linux runbook fixture evidence must record the fixture context, launcher command family, expected status/diagnostic, and a non-claim statement that installed-cache launch proof, native UAT, release-readiness, and public platform claims remain XPLAT-007 responsibilities. XPLAT-007 owns generated payload propagation, active Claude/Codex cutover, installed-cache launch proof, consumer checksum guidance, native Windows/macOS/Linux UAT, release-readiness, and public claim audit.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Structured runner preflight (Priority: P1)

Maintainers can invoke the runner foundation preflight and receive a structured response that states whether the local environment satisfies the runner boundary before any helper ports depend on it.

**Why this priority**: This is the minimum usable foundation for later cross-platform helper work. Without preflight, downstream helper ports cannot fail closed or explain missing prerequisites consistently.

**Independent Test**: Can be tested by invoking the runner preflight in a local checkout and confirming the response is valid structured output with runtime, platform, plugin root, prerequisite, runner identity, and metadata-pointer fields.

**Acceptance Scenarios**:

1. **Given** a checkout with the required runtime and SpecKit prerequisite available, **When** the maintainer runs the runner preflight, **Then** the response reports success and includes runtime version, platform, plugin root, prerequisite status, runner identity, and metadata pointers.
2. **Given** a checkout where a required prerequisite is unavailable, **When** the maintainer runs the runner preflight, **Then** the response fails closed with a deterministic diagnostic and does not report the environment as usable.
3. **Given** the runner is invoked through its supported module-style entrypoint, **When** the maintainer sends a JSON request, **Then** the runner returns JSON on standard output without requiring shell quoting, Unix-only paths, `jq`, package installation, or virtual environment restore.

---

### User Story 2 - Contract fixture runway for helper ports (Priority: P2)

Helper-port implementers can use contract fixtures that exercise the shared runner envelope, typed path handling, subprocess behavior, diagnostics, and preflight behavior before porting production helpers in later XPLAT work.

**Why this priority**: XPLAT-005 and XPLAT-006 need stable primitives and failing examples before moving real helper behavior out of Bash-backed flows.

**Independent Test**: Can be tested by running the runner contract fixture suite and confirming it covers valid requests, validation failures, path normalization, subprocess outcomes, diagnostics, and preflight responses without calling real production helpers.

**Acceptance Scenarios**:

1. **Given** a valid contract fixture request, **When** the fixture is executed, **Then** it returns a successful structured response that conforms to the runner envelope.
2. **Given** an invalid or incomplete request fixture, **When** the fixture is executed, **Then** it returns a deterministic validation diagnostic and a non-success outcome.
3. **Given** path and subprocess fixture cases, **When** the fixture suite runs, **Then** it verifies platform-neutral path handling and explicit subprocess result capture without shell-specific parsing.

---

### User Story 3 - Inspectable runner identity and source metadata (Priority: P3)

Release reviewers can inspect the runner source identity, checksum coverage, and manifest metadata while clearly seeing that XPLAT-004 does not switch installed workflows or make public native-platform support claims.

**Why this priority**: Reviewers need integrity evidence before XPLAT-007 cutover, but the foundation should not overstate support before native installed-cache UAT and payload propagation are complete.

**Independent Test**: Can be tested by reviewing the runner metadata manifest and confirming every runner source file is listed with integrity information while active plugin skills, hooks, generated payloads, and public docs remain unchanged by the runner.

**Acceptance Scenarios**:

1. **Given** the runner source files are present, **When** the reviewer inspects runner metadata, **Then** every runner-owned source file has checksum coverage and an identity pointer.
2. **Given** generated payload, skill, hook, or public documentation surfaces, **When** the reviewer compares XPLAT-004 changes, **Then** none of those surfaces are switched to the runner or claim public native-platform support.

---

### Edge Cases

- The runtime prerequisite is missing, too old, or resolves to an unsupported executable.
- The SpecKit `specify` prerequisite is missing or not discoverable from the runner environment.
- The plugin root cannot be found from the invocation context.
- The JSON request is malformed, missing required fields, or names an unsupported runner action.
- Paths contain spaces, Windows-style separators, relative traversal segments, or non-existent targets.
- A subprocess fixture exits non-zero, writes to standard error, emits large but bounded output, or exceeds its configured timeout.
- Runner metadata is absent, stale, incomplete, or does not cover all runner-owned source files.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The runner foundation MUST expose `speckit-pro/speckit_pro_runner/` through `<python> -m speckit_pro_runner`, accepting JSON input and returning JSON output through standard streams.
- **FR-002**: The runner foundation MUST preserve the durable command-envelope expectations selected by XPLAT-002, including the wire-status vocabulary `ok`, `expected_failure`, `input_error`, `missing_prerequisite`, `subprocess_failure`, and `internal_failure` plus the 0-5 exit-code map for later helper ports. Natural-language "success" or "non-success" wording in XPLAT-004 artifacts is descriptive only and MUST NOT introduce alternate wire values.
- **FR-003**: The preflight response MUST report runtime version, platform details, plugin root, prerequisite status, runner identity, source-checkout context, and typed metadata pointers for the runner package, manifest file, and checksum file.
- **FR-004**: The preflight behavior MUST fail closed when the required Python 3.11+ runtime boundary is not satisfied, using `python_too_old` when the runner starts under an older interpreter and `python_launcher_unavailable` in discovery/runbook evidence when no Python 3.11+ launcher can start the runner.
- **FR-005**: The preflight behavior MUST fail closed when the official SpecKit `specify` prerequisite is missing or unavailable, using diagnostic code `specify_missing`.
- **FR-006**: The runner foundation MUST validate incoming request shape before executing a requested action and return deterministic diagnostics for validation failures, using `invalid_json`, `invalid_envelope`, `unsupported_schema_version`, or `missing_required_field` as applicable.
- **FR-007**: The runner foundation MUST provide platform-neutral typed path handling for runner-owned inputs and outputs without relying on Unix-only paths or shell quoting.
- **FR-008**: The runner foundation MUST provide a subprocess-result primitive that records command outcome, exit status, standard output, standard error, and timeout diagnostics for fixture use, using diagnostic codes `subprocess_nonzero`, `subprocess_timeout`, and `subprocess_stderr_only_failure` for the distinct failure categories.
- **FR-009**: Contract fixtures MUST cover at least valid envelope handling, invalid envelope handling, typed path behavior, subprocess behavior, diagnostics, and preflight behavior through a Python stdlib Layer 4 test entrypoint.
- **FR-010**: Runner source metadata MUST identify runner-owned Python source files, keep manifest and checksum files under `speckit-pro/speckit_pro_runner/`, and provide checksum coverage for each covered source file. Missing, incomplete, mismatched, or unchecked metadata in preflight MUST fail closed with deterministic diagnostics and remediation.
- **FR-011**: XPLAT-004 MUST NOT port real production helper behavior beyond runtime-info, preflight, and contract smoke fixtures.
- **FR-012**: XPLAT-004 MUST NOT switch active Claude Code skills, Codex skills, hooks, generated payloads, public docs, or install behavior to the runner.
- **FR-013**: XPLAT-004 MUST NOT copy runner files into `dist/**` or make public native-platform support claims.
- **FR-014**: The implementation plan MUST record the accepted two-slice approach: Slice 1 for runner and preflight core, and Slice 2 for parity fixtures plus metadata.
- **FR-015**: Plugin root detection MUST start from the resolved runner package file location and walk ancestors to the nearest directory containing `.claude-plugin/plugin.json` or `.codex-plugin/plugin.json`; if neither anchor is found, preflight MUST fail closed with diagnostic code `plugin_root_missing` instead of guessing from the process working directory.
- **FR-016**: Runner metadata path values MUST be `plugin_relative` values rooted at the detected plugin root, for example `speckit_pro_runner/...`; metadata MUST NOT store absolute source-checkout paths or repo-root-relative paths that would break after XPLAT-007 copies runner files into generated payload roots.
- **FR-017**: XPLAT-005 and XPLAT-006 helper ports MUST extend the same `speckit-pro/speckit_pro_runner/` package, `<python> -m speckit_pro_runner` module entrypoint, JSON stdin/stdout envelope, diagnostic model, typed-path rules, subprocess-result rules, and dispatch contract rather than choosing a new package path, launcher, or helper-specific CLI argument model.
- **FR-018**: XPLAT-004 MUST leave future helper IDs, helper operations, compatibility-adapter records, and row-level XPLAT-001 mappings as downstream handoff inputs for XPLAT-005/XPLAT-006 unless needed for runner-foundation contract fixtures; the foundation may define the extension rule but MUST NOT implement real helper ports.
- **FR-019**: Every failure diagnostic written in the stdout response `diagnostics` array or as a line-delimited stderr JSON record MUST use the strict Diagnostic shape: `severity`, `source`, `code`, `message`, `remediation`, and optional bounded `details`.
- **FR-020**: Contract fixtures for every non-`ok` case MUST assert expected status, exit code, diagnostic code, and remediation object presence.
- **FR-021**: Contract fixture subprocess records MUST use an explicit timeout no greater than 5 seconds, cap captured stdout and stderr at 16 KiB per stream, and record `timeout_seconds`, `duration_ms`, `stdout`/`stderr` byte counts, stream limits, and truncation flags so failure records remain deterministic and bounded.
- **FR-022**: Windows/Linux runbook fixtures MUST identify `source_checkout` versus installed-cache context, the launcher command family being exercised, expected status/exit/diagnostic outcomes, metadata verification expectations, and explicit non-claim language that public platform readiness remains deferred to XPLAT-007 unless native installed-cache UAT is actually performed there.

### Reviewability Notes *(if applicable)*

- The runtime substrate and module-style invocation are inherited constraints from XPLAT-003 and the XPLAT-004 design concept, not open implementation exploration for this phase.
- Public support claims, generated payload cutover, release automation, signatures, SBOMs, provenance, reproducible builds, and formal audit evidence remain deferred to later roadmap work.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: docs/process, seed/config
- **Projected reviewable LOC**: Approximately 420 LOC excluding generated, lock, vendor, and `.process` artifacts
- **Projected production files**: 3-6 runner-owned source or metadata files
- **Projected total files**: 8-12 files including tests, fixtures, metadata, and process artifacts
- **Budget result**: warning accepted
- **Split decision**: Keep one XPLAT-004 spec and one workflow, but plan two reviewable PR slices. Slice 1 delivers the runner and preflight core. Slice 2 delivers contract fixture parity, metadata, and review evidence. This records the forward-estimator warning without creating child specs or extra branches.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Runner Request Envelope**: A structured invocation request that names the runner action, carries bounded input data, and supports deterministic validation.
- **Runner Response Envelope**: A structured response that records success or failure, diagnostics, and action-specific payload data.
- **Preflight Report**: The runtime and environment status reported before downstream helper ports rely on the runner.
- **Diagnostic**: A deterministic failure or warning record with enough context and structured remediation for maintainers and downstream implementers to identify the unmet condition and next action.
- **Typed Path**: A path value that is interpreted relative to an explicit trust boundary and normalized without shell-specific assumptions.
- **Subprocess Result**: A captured external-process outcome used by fixtures to prove result handling before real helper ports.
- **Runner Metadata Manifest**: A reviewer-facing source inventory that identifies runner-owned files and checksum coverage.
- **Contract Fixture**: A bounded test input and expected outcome proving runner primitives without porting production helper behavior.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer can run the preflight on a valid local environment and receive a structured success response containing all required report fields in under 5 seconds.
- **SC-002**: Missing runtime, too-old runtime, missing `specify`, and metadata-readiness prerequisite cases produce deterministic non-success diagnostics with structured remediation in 100% of covered preflight fixtures.
- **SC-003**: Contract fixtures cover 100% of the required primitive categories: envelope success, envelope validation failure, typed paths, subprocess outcomes, diagnostics, remediation records, and preflight.
- **SC-004**: Reviewers can account for checksum coverage for 100% of runner-owned source files listed in the source-checkout runner metadata manifest.
- **SC-005**: Active plugin skills, hooks, generated payloads, public docs, and install behavior have zero runner cutover or public native-platform support claims in XPLAT-004.
- **SC-006**: The final review packet identifies both planned PR slices, their changed surfaces, their verification evidence, and their deferred follow-up boundaries.
- **SC-007**: Reliability fixtures include explicit timeout/output bounds and at least one Windows-oriented and one Linux-oriented source-checkout runbook fixture whose expected records cannot be read as installed-cache proof or public platform readiness.

## Assumptions

- XPLAT-002 remains the controlling source for the command envelope, diagnostics, exit behavior, path handling, subprocess expectations, and preflight contract.
- XPLAT-003 remains the controlling source for the Python 3.11+ standard-library runtime decision and the official SpecKit `specify` prerequisite boundary.
- Local source-checkout runner execution plus deterministic runbook evidence is sufficient for XPLAT-004; generated payload propagation, installed-cache launch proof, public claim audit, and full native installed-cache UAT remain deferred to XPLAT-007.
- Existing Bash-backed test, eval, release, and documentation gates remain in place during XPLAT-004.
- Helper-port implementers in XPLAT-005 and XPLAT-006 will consume the runner primitives and the stable module/dispatch contract, but will not depend on production helper behavior being ported in this feature.
