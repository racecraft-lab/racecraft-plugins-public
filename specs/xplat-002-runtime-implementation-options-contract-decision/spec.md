# Feature Specification: Runtime Implementation Options and Contract Decision

**Feature Branch**: `codex/xplat-002-runtime-implementation-options-contract-decision`

**Created**: 2026-06-26

**Status**: Draft

**Input**: User description: "Runtime Implementation Options and Contract Decision"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compare Runtime Candidates (Priority: P1)

Maintainers can compare JavaScript/TypeScript, Python, and small per-platform
binary runner candidates against the XPLAT-001 runtime rubric using grounded
documentation and lightweight probe evidence.

**Why this priority**: The runtime choice is the primary decision this spike
must settle before later cross-platform implementation work can proceed.

**Independent Test**: Can be tested by reviewing the decision record and
confirming every candidate family is evaluated against the same rubric and
evidence expectations.

**Acceptance Scenarios**:

1. **Given** the XPLAT-001 runtime rubric, **When** a maintainer reviews the
   runtime comparison, **Then** JavaScript/TypeScript, Python, and small
   per-platform binary options are each evaluated against the same criteria.
2. **Given** invocation behavior is uncertain for a candidate, **When** the
   evidence is reviewed, **Then** the record identifies official documentation
   and any lightweight repo-local or installed-cache probe used to reduce that
   uncertainty.

---

### User Story 2 - Read the Selected Command Contract (Priority: P2)

Implementers of XPLAT-004 through XPLAT-007 can read one selected runtime
decision and a precise command contract covering the entrypoint, dispatch
shape, input/output behavior, diagnostics, exit codes, paths, subprocesses,
prerequisites, and runtime version reporting.

**Why this priority**: Later implementation specs need a stable handoff that
does not reopen the runtime, package, or command-shape decision.

**Independent Test**: Can be tested by asking an implementer to identify the
selected runtime, command contract fields, and implementation boundaries without
consulting any hidden rationale.

**Acceptance Scenarios**:

1. **Given** the decision record, **When** an implementer looks for the
   canonical runtime, **Then** exactly one runtime option is selected rather
   than a ranked shortlist.
2. **Given** the command contract section, **When** an implementer prepares
   XPLAT-004 planning, **Then** the entrypoint name, dispatch shape, JSON
   stdin/stdout behavior, stderr diagnostics, exit-code mapping, path handling,
   subprocess rules, prerequisite reporting, and runtime version reporting are
   all explicitly defined.

---

### User Story 3 - Review Rejections and Handoff (Priority: P3)

Reviewers can see rejected options, tie-breaker rationale, evidence gaps, and
the exact handoff to XPLAT-003 and XPLAT-004 without any hidden change to public
support claims.

**Why this priority**: The decision needs to be reviewable and bounded so
rejected options are not revisited later without new evidence.

**Independent Test**: Can be tested by tracing every rejection and follow-up
handoff item to a stated criterion, tie-breaker, evidence gap, or downstream
spec responsibility.

**Acceptance Scenarios**:

1. **Given** two runtime candidates appear close, **When** a reviewer checks the
   tie-breaker rationale, **Then** install reliability and installed-cache
   invocation reliability explain the final selection.
2. **Given** the decision record names downstream work, **When** a reviewer
   checks the handoff, **Then** runtime-specific supply-chain implications are
   recorded for XPLAT-003 and the build-ready command contract is recorded for
   XPLAT-004.

---

### Edge Cases

- Official documentation and lightweight probe evidence conflict or describe
  different execution contexts.
- A candidate satisfies portability goals but requires per-user dependency
  installation or network fetches from the public installed plugin cache.
- A candidate has strong local behavior but weak installed-cache invocation
  reliability.
- Runtime evidence is incomplete for one operating system family or plugin host
  surface.
- Shell-specific behavior appears in a candidate contract through quoting,
  path, environment, or subprocess assumptions.
- A rejected option leaves a supply-chain implication that belongs in XPLAT-003
  even though it is not selected for XPLAT-004.
- A decision statement could be mistaken for a new public support claim.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The decision record MUST evaluate JavaScript/TypeScript, Python,
  and small per-platform binary runner options before selecting a runtime.
- **FR-002**: The evaluation MUST apply the XPLAT-001 runtime rubric to every
  candidate family using the same criteria.
- **FR-003**: The evaluation MUST record runtime-specific supply-chain
  implications relevant to XPLAT-003 without selecting final supply-chain
  controls.
- **FR-004**: The evidence base MUST cite official runtime documentation for
  each candidate family.
- **FR-005**: Where invocation behavior is uncertain, the evidence base MUST
  include lightweight repo-local or installed-cache smoke probe results, or
  explicitly record why that probe could not be completed.
- **FR-006**: The final decision MUST select exactly one canonical runtime and
  MUST NOT leave XPLAT-004 with a ranked shortlist.
- **FR-007**: The decision rationale MUST explain rejected options, including
  the rubric criteria, evidence gaps, or tie-breakers that drove each rejection.
- **FR-008**: When candidates are otherwise close, the decision MUST use install
  reliability and installed-cache invocation reliability as the deciding
  tie-breaker.
- **FR-009**: The command contract MUST define the canonical entrypoint name and
  dispatch shape for future runtime commands.
- **FR-010**: The command contract MUST require structured JSON input through
  standard input and structured JSON output through standard output.
- **FR-011**: The command contract MUST define structured diagnostic behavior on
  standard error without mixing diagnostics into successful JSON output.
- **FR-012**: The command contract MUST define explicit exit-code categories for
  success, user/input errors, missing prerequisites, runtime failures, and
  unexpected internal failures.
- **FR-013**: The command contract MUST define path-handling expectations that
  avoid Unix-only assumptions and preserve behavior across Windows, macOS, and
  Linux.
- **FR-014**: The command contract MUST define subprocess rules covering when
  subprocesses are allowed, how shell-specific behavior is avoided, and how
  prerequisites are reported.
- **FR-015**: The command contract MUST define runtime version reporting so
  diagnostics and verification can identify the selected runtime environment.
- **FR-016**: The decision record MUST optimize for no per-user dependency
  installation and no network fetch from the public installed plugin cache.
- **FR-017**: The handoff MUST identify what XPLAT-003 must resolve about
  runtime-specific supply-chain implications.
- **FR-018**: The handoff MUST identify what XPLAT-004 can build from the
  selected runtime and command contract without reopening the language or
  packaging choice.
- **FR-019**: The decision record MUST avoid changing public support claims,
  public documentation promises, or release notes beyond the decision record
  itself.
- **FR-020**: The work MUST remain a research and decision spike and MUST NOT
  build the runner or port helper behavior.

### Reviewability Notes *(if applicable)*

- This spike may discuss runtime family names and command-contract behavior
  because those are the decision subject, but it does not authorize production
  runner implementation or public support-claim changes.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process, harness/adapter
- **Secondary surfaces, if any**: N/A
- **Projected reviewable LOC**: 250
- **Projected production files**: 4
- **Projected total files**: 10
- **Budget result**: warning accepted
- **Split decision**: This remains one research and decision spike because the
  advisory estimate is `status=ok` with `suggested_slices=1`; implementation,
  supply-chain controls, and native release-readiness gates remain in follow-up
  XPLAT specs.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Runtime Candidate**: A candidate runtime family under evaluation, including
  its documentation evidence, probe evidence, rubric results, install
  reliability, installed-cache invocation reliability, and rejection or
  selection rationale.
- **Evaluation Evidence**: A cited documentation source, lightweight probe
  result, or explicitly recorded evidence gap used to support candidate scoring.
- **Command Contract**: The selected runtime-facing command agreement covering
  entrypoint, dispatch, JSON input/output, diagnostics, exit codes, paths,
  subprocesses, prerequisites, and runtime version reporting.
- **Decision Record**: The reviewable artifact that selects the canonical
  runtime, explains rejected options, records tie-breakers, and prevents later
  specs from reopening the same decision.
- **Handoff Item**: A downstream responsibility assigned to XPLAT-003 or
  XPLAT-004 with enough context for that spec to proceed independently.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer can identify the selected runtime and the reason each
  rejected option was rejected within 5 minutes of reading the decision record.
- **SC-002**: The decision record evaluates 100% of the named candidate
  families against the XPLAT-001 runtime rubric.
- **SC-003**: Every candidate family has at least one official documentation
  source recorded and every uncertain invocation behavior has either probe
  evidence or a documented evidence gap.
- **SC-004**: The selected command contract covers all required contract fields
  with zero unresolved placeholders or clarification markers.
- **SC-005**: An XPLAT-004 implementer can identify the selected runtime,
  command entrypoint, input/output contract, diagnostic contract, exit-code
  mapping, path rules, subprocess rules, prerequisite reporting, and runtime
  version reporting without reopening runtime selection.
- **SC-006**: Reviewers can trace every rejected option to a rubric result,
  evidence gap, or install-reliability tie-breaker.
- **SC-007**: The decision record names all runtime-specific handoff items for
  XPLAT-003 and XPLAT-004 and contains no public support-claim, release-note, or
  public documentation promise changes.
- **SC-008**: The completed spike remains within the accepted reviewability
  warning budget of 250 reviewable LOC, 4 production files, and 10 total files.

## Assumptions

- XPLAT-001 runtime inventory and rubrics are available and are the
  authoritative baseline for this decision.
- Lightweight smoke probes are non-mutating and may use only repo-local state or
  the installed plugin cache already available to the reviewer.
- The public installed plugin cache must be usable without asking each user to
  install extra dependencies or fetch packages from the network.
- This phase records decision evidence and a command contract only; runner
  implementation, helper porting, and native release-readiness UAT remain out of
  scope.
- Runtime version reporting includes enough information for future diagnostics
  and verification to identify the selected runtime environment and command
  contract version.
