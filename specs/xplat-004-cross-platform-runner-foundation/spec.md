# Feature Specification: Cross-Platform Runner Foundation

**Feature Branch**: `codex/xplat-004-cross-platform-runner-foundation`

**Created**: 2026-06-30

**Status**: Draft

**Input**: User description: "Create the minimal Python 3.11+ standard-library runner foundation for SpecKit Pro installed Claude Code and Codex workflows, preserving the XPLAT-002 command envelope and XPLAT-003 runtime decision while avoiding helper ports, public native-platform claims, and generated payload cutover."

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

- **FR-001**: The runner foundation MUST expose a module-oriented invocation path that accepts JSON input and returns JSON output through standard streams.
- **FR-002**: The runner foundation MUST preserve the durable command-envelope expectations selected by XPLAT-002, including deterministic success and failure shapes for later helper ports.
- **FR-003**: The preflight response MUST report runtime version, platform details, plugin root, prerequisite status, runner identity, and metadata pointers.
- **FR-004**: The preflight behavior MUST fail closed when the required Python 3.11+ runtime boundary is not satisfied.
- **FR-005**: The preflight behavior MUST fail closed when the official SpecKit `specify` prerequisite is missing or unavailable.
- **FR-006**: The runner foundation MUST validate incoming request shape before executing a requested action and return deterministic diagnostics for validation failures.
- **FR-007**: The runner foundation MUST provide platform-neutral typed path handling for runner-owned inputs and outputs without relying on Unix-only paths or shell quoting.
- **FR-008**: The runner foundation MUST provide a subprocess-result primitive that records command outcome, exit status, standard output, standard error, and timeout diagnostics for fixture use.
- **FR-009**: Contract fixtures MUST cover at least valid envelope handling, invalid envelope handling, typed path behavior, subprocess behavior, diagnostics, and preflight behavior.
- **FR-010**: Runner source metadata MUST identify runner-owned source files and provide checksum coverage for each file.
- **FR-011**: XPLAT-004 MUST NOT port real production helper behavior beyond runtime-info, preflight, and contract smoke fixtures.
- **FR-012**: XPLAT-004 MUST NOT switch active Claude Code skills, Codex skills, hooks, generated payloads, public docs, or install behavior to the runner.
- **FR-013**: XPLAT-004 MUST NOT copy runner files into `dist/**` or make public native-platform support claims.
- **FR-014**: The implementation plan MUST record the accepted two-slice approach: Slice 1 for runner and preflight core, and Slice 2 for parity fixtures plus metadata.

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
- **Diagnostic**: A deterministic failure or warning record with enough context for maintainers and downstream implementers to identify the unmet condition.
- **Typed Path**: A path value that is interpreted relative to an explicit trust boundary and normalized without shell-specific assumptions.
- **Subprocess Result**: A captured external-process outcome used by fixtures to prove result handling before real helper ports.
- **Runner Metadata Manifest**: A reviewer-facing source inventory that identifies runner-owned files and checksum coverage.
- **Contract Fixture**: A bounded test input and expected outcome proving runner primitives without porting production helper behavior.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer can run the preflight on a valid local environment and receive a structured success response containing all required report fields in under 5 seconds.
- **SC-002**: Missing runtime or missing `specify` prerequisite cases produce deterministic non-success diagnostics in 100% of covered preflight fixtures.
- **SC-003**: Contract fixtures cover 100% of the required primitive categories: envelope success, envelope validation failure, typed paths, subprocess outcomes, diagnostics, and preflight.
- **SC-004**: Reviewers can account for checksum coverage for 100% of runner-owned source files listed in the runner metadata manifest.
- **SC-005**: Active plugin skills, hooks, generated payloads, public docs, and install behavior have zero runner cutover or public native-platform support claims in XPLAT-004.
- **SC-006**: The final review packet identifies both planned PR slices, their changed surfaces, their verification evidence, and their deferred follow-up boundaries.

## Assumptions

- XPLAT-002 remains the controlling source for the command envelope, diagnostics, exit behavior, path handling, subprocess expectations, and preflight contract.
- XPLAT-003 remains the controlling source for the Python 3.11+ standard-library runtime decision and the official SpecKit `specify` prerequisite boundary.
- Local runner execution plus deterministic runbook evidence is sufficient for XPLAT-004; full native installed-cache UAT remains deferred to XPLAT-007.
- Existing Bash-backed test, eval, release, and documentation gates remain in place during XPLAT-004.
- Helper-port implementers in XPLAT-005 and XPLAT-006 will consume the runner primitives but will not depend on production helper behavior being ported in this feature.
