# Feature Specification: Runtime Implementation Options and Contract Decision

**Feature Branch**: `codex/xplat-002-runtime-implementation-options-contract-decision`

**Created**: 2026-06-26

**Status**: Complete; amended 2026-06-28 after official Spec Kit Python
prerequisite confirmation

> Amendment: XPLAT no longer treats compiled per-platform binaries as a
> candidate, fallback, compatibility adapter, or downstream implementation
> input. The small per-platform binary evidence remains only to document the
> rejected historical path.

**Input**: User description: "Runtime Implementation Options and Contract Decision"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compare Runtime Candidates (Priority: P1)

Maintainers can review the historical JavaScript/TypeScript, Python, and small
per-platform binary comparison against the XPLAT-001 runtime rubric using
grounded documentation and lightweight probe evidence, with Python selected and
compiled binaries rejected for XPLAT.

**Why this priority**: The runtime choice is the primary decision this spike
must settle before later cross-platform implementation work can proceed.

**Independent Test**: Can be tested by reviewing the decision record and
confirming every candidate family is evaluated against the same rubric and
evidence expectations.

**Acceptance Scenarios**:

1. **Given** the XPLAT-001 runtime rubric, **When** a maintainer reviews the
   amended runtime comparison, **Then** Python is selected and
   JavaScript/TypeScript plus small per-platform binary options are retained
   only as rejected historical candidates.
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

## Clarifications

### Session 1: Candidate Scoring and Evidence

- Historical candidate comparison used a gate-first weighted evidence matrix:
  apply all XPLAT-001 must-have gates to each evaluated runtime family, then use
  evidence-backed 0-5 ratings against the weighted criteria to support
  selection and rejection rationale.
- The amended selected runtime is Python standard library only. Historical
  JavaScript/TypeScript and small per-platform binary records are retained as
  rejected evidence, not selectable XPLAT runtime families. Hybrid
  compatibility adapters may be documented as temporary migration notes, but
  they are not a fourth selectable runtime family.
- Required documentation evidence must come from runtime or toolchain
  maintainers, official plugin platform documentation, or repo-local
  source/manifests. Third-party material may be supplemental only.
- Required smoke probes are minimal and non-mutating: runtime
  version/availability, installed Claude plugin-cache invocation, installed
  Codex plugin-cache invocation, JSON stdin/stdout behavior, stderr/exit
  separation, path-with-spaces handling, and shell-free subprocess or
  missing-command behavior. Repo-local or generated-payload probes may be
  supplemental setup evidence, but they do not replace installed-cache evidence.
  If either host cache or runtime is unavailable, record a host-specific
  evidence-gap fallback plan. The fallback plan includes the missing probe,
  host/runtime scope, reason unavailable, substitute official or repo-local
  evidence consulted, gate or scoring effect, owner, and expiry/removal or
  follow-up condition. Evidence gaps explain missing proof; they do not count
  as probe passes.
- When official documentation and smoke probes conflict, record both. The
  installed-cache probe controls invocation-reliability scoring, official docs
  control general runtime claims, and unresolved conflict remains an evidence
  gap unless a bounded reproduction explains the difference.

### Session 2: Command Contract Envelope

- The canonical runner entrypoint is `speckit-pro-runner`, resolved relative to
  the installed plugin payload. The amended Python runner source path is
  `scripts/speckit_pro_runner.py`; XPLAT-004 may add a thin dispatch-only
  payload-relative launcher such as `scripts/speckit-pro-runner` if the product
  surfaces need a stable command target.
- Helper execution reads one versioned JSON request from stdin. The request
  includes `schema_version`, `request_id`, `helper_id`, `operation`, `mode`, and
  `inputs`. CLI arguments are limited to metadata/help behavior such as
  `--help` and `--version`; helper-specific arguments are not encoded in argv.
- Successful and failed invocations emit one versioned JSON response on stdout
  with `schema_version`, `request_id`, `helper_id`, `status`, `exit_code`,
  `data`, `diagnostics`, and `runtime`. Stderr diagnostics are deterministic
  line-delimited JSON objects with `severity`, `code`, `message`, `source`, and
  `details`.
- Runner exit codes use one common category map while preserving documented
  legacy helper codes in `legacy_exit_code` when parity requires it:
  `0=ok`, `1=expected helper/domain failure`, `2=input envelope/usage/schema
  error`, `3=missing prerequisite`, `4=subprocess failure or timeout`, and
  `5=unexpected internal failure`.
- Path values declare their kind, such as `repo_relative`, `plugin_relative`,
  `cache_relative`, `absolute`, or `temp`; reader-facing output prefers
  repo/plugin-relative display paths. Subprocesses use structured argv arrays
  with shell disabled, explicit cwd/env allowlists, captured stdout/stderr/exit,
  timeout handling, and missing executables reported as missing prerequisites.
  No globbing, shell interpolation, redirection, `.sh`, or `jq` fallback is
  part of the selected contract.
- The same runner exposes a `runtime-info` or `preflight` operation returning
  runner name/version, contract version, selected runtime name/version,
  platform/architecture, plugin root, source-vs-installed context, executable
  availability, capabilities, and prerequisite records with `id`, `required`,
  `available`, `version`, `path`, `remediation`, and `severity`.
- XPLAT-004 fixture parity must cover success, invalid JSON, missing required
  field, path with spaces, Windows separators, missing prerequisite,
  subprocess nonzero, subprocess timeout, stderr-only failure,
  runtime-info/preflight, and at least one read-only legacy-helper versus
  runner comparison. Each failure fixture must identify expected stdout
  `status`, process `exit_code`, stderr diagnostic `code`, and any required
  response fields such as null request identifiers for malformed JSON.

### Session 3: Packaging, Adapters, and Public-Claim Boundaries

- Installed-cache reliability is a pass/fail gate for the selected runtime.
  Initial plugin install or update may fetch payloads, but once the plugin cache
  is populated the selected runner must not require `npm install`,
  `pip install`, `uv`, `brew`, network package restoration, or any other
  per-user dependency setup.
- Temporary compatibility adapters are recorded as migration records, not
  runtime candidates. Adapter IDs use the owner-first format
  `xplat-005-compat-<legacy-helper-or-surface-slug>`,
  `xplat-006-compat-<legacy-helper-or-surface-slug>`, or
  `xplat-007-compat-<legacy-helper-or-surface-slug>`, with an explicit uppercase
  `removal_spec` field preserving traceability.
- Each adapter record includes `adapter_id`, `legacy_surface`,
  `xplat001_source_row`, `runner_helper_id`, `runner_operation`,
  `runner_mode`, `owner_bucket`, `owner_spec`, `removal_spec`,
  `removal_condition`, and `evidence`.
- XPLAT-003 receives a supply-chain implication matrix for the selected Python
  runtime and rejected historical runtime paths. The matrix records dependency
  and bootstrap footprint, manifest/lockfile impact, generated output shape,
  build/release path, vulnerability-scan path, checksum/signature/SBOM/
  provenance feasibility, consumer-local verification ideas, offline/update
  implications, distribution trust root, transitive/build-time/native
  dependencies, build environment inputs, runtime/install execution risk,
  maintenance posture, and evidence gaps. XPLAT-002 records feasibility only;
  XPLAT-003 chooses first-release, deferred, and not-claimed controls.
- The matrix separates evidence-backed facts from assumptions for vendored
  packages, embedded runtimes, native binaries, generated payload artifacts,
  lockfiles/manifests, and package-manager behavior. Unknown or unverified
  artifact assumptions are evidence gaps, not accepted controls or implicit
  permission for XPLAT-004 to build a new security model.
- XPLAT-004 receives only the selected runtime, the `speckit-pro-runner`
  contract, JSON/stderr/exit/path/subprocess/preflight requirements, fixture
  parity expectations, and compatibility-adapter records.
- XPLAT-004 also receives a traceable implementation input bundle derived from
  XPLAT-001 rows. The bundle maps row IDs and owner buckets to runner helper
  inputs, compatibility-adapter records, fixture parity expectations, and
  explicit exclusions so implementation does not infer work from source
  checkout paths.
- XPLAT-002 must not edit README, docs-site pages, marketplace metadata,
  changelog, release notes, or similar public surfaces to claim native support.
  It may use decision-record, target, candidate-evidence, and handoff wording
  only; XPLAT-007 owns public support claims after native UAT.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The decision record MUST preserve the historical evaluation of
  JavaScript/TypeScript, Python, and small per-platform binary runner options,
  identify Python as the amended selected runtime, and label compiled binaries
  as rejected historical evidence only.
- **FR-002**: The evaluation MUST apply the XPLAT-001 runtime rubric to every
  candidate family using a gate-first weighted evidence matrix: all must-have
  gates are evaluated before evidence-backed weighted criteria ratings are used
  for selection and rejection rationale.
- **FR-003**: The evaluation MUST record runtime-specific supply-chain
  implications relevant to XPLAT-003 without selecting final supply-chain
  controls.
- **FR-004**: The evidence base MUST cite documentation from runtime or
  toolchain maintainers, official plugin platform documentation, or repo-local
  source/manifests for each evaluated runtime family; third-party material MAY
  be used only as supplemental evidence.
- **FR-005**: Where invocation behavior is uncertain, the evidence base MUST
  include lightweight smoke probe results for runtime availability, installed
  Claude plugin-cache invocation, installed Codex plugin-cache invocation, JSON
  input/output, stderr/exit separation, path-with-spaces handling, and
  shell-free subprocess or missing-command behavior, or explicitly record a
  host/runtime-specific evidence-gap fallback plan when a probe cannot be
  completed. Each fallback plan MUST include the missing probe, reason
  unavailable, substitute official or repo-local evidence consulted, gate or
  scoring effect, owner, and expiry/removal or follow-up condition. Repo-local
  and generated-payload probes MAY be recorded as supplemental setup evidence,
  but MUST NOT substitute for the installed-cache invocation evidence required
  by the XPLAT-001 gate, and evidence gaps MUST NOT be counted as
  installed-cache probe passes.
- **FR-006**: The final decision MUST select exactly one canonical runtime and
  MUST NOT leave XPLAT-004 with a ranked shortlist.
- **FR-007**: The decision rationale MUST explain rejected options, including
  rubric gate failures, weighted criteria results, evidence gaps,
  documentation/probe conflicts, or tie-breakers that drove each rejection.
- **FR-008**: The decision MUST define "otherwise close" objectively before
  applying the install-reliability tie-breaker. Candidates are close only when
  they have no selection-blocking gate failures and their weighted totals differ
  by five points or less, or when the leading score depends only on maintainer
  ergonomics or compatibility-adapter criteria while reliability criteria are
  tied or favor another candidate.
- **FR-008a**: For close candidates, the decision MUST apply measurable
  reliability tie-breaker inputs before maintainer preference: installed Claude
  cache probe status, installed Codex cache probe status, post-cache dependency
  setup burden, offline behavior after cache population, first-run/bootstrap
  failure diagnostics, and runtime-info/preflight completeness. If those inputs
  do not produce a winner, the decision record MUST mark the item unresolved
  rather than hiding the tie in narrative rationale.
- **FR-009**: The command contract MUST define the canonical entrypoint as
  `speckit-pro-runner`, plugin-cache-relative by default, with Python runner
  source at `scripts/speckit_pro_runner.py` and any thin dispatch-only launcher
  convention deferred to XPLAT-004.
- **FR-010**: The command contract MUST require structured JSON input through
  standard input using a versioned envelope with `schema_version`, `request_id`,
  `helper_id`, `operation`, `mode`, and `inputs`.
- **FR-011**: The command contract MUST define structured diagnostic behavior on
  standard error as deterministic line-delimited JSON without mixing diagnostics
  into successful JSON output.
- **FR-012**: The command contract MUST define explicit exit-code categories for
  success, expected helper/domain failures, input envelope or schema errors,
  missing prerequisites, subprocess failures or timeouts, and unexpected
  internal failures, with `legacy_exit_code` available when parity requires
  preserving a helper-specific code.
- **FR-013**: The command contract MUST define path-handling expectations that
  classify path values as repo-relative, plugin-relative, cache-relative,
  absolute, or temporary and preserve behavior across Windows, macOS, and Linux.
- **FR-014**: The command contract MUST define subprocess rules covering when
  subprocesses are allowed, how shell-specific behavior is avoided through
  structured argv execution with shell disabled, and how prerequisites are
  reported.
- **FR-015**: The command contract MUST define runtime version reporting so
  diagnostics and verification can identify the selected runtime environment,
  contract version, platform/architecture, plugin root, source-vs-installed
  context, executable availability, capabilities, and prerequisite state.
- **FR-016**: The selected runtime model MUST be viable for installed-cache
  reliability by requiring no per-user dependency installation, network package
  restoration, `npm install`, `pip install`, `uv`, `brew`, or equivalent setup
  after plugin-cache population. Because XPLAT-002 does not build
  `speckit-pro-runner`, actual installed Claude/Codex cache invocation proof
  MUST remain an XPLAT-004 acceptance item and MUST NOT be counted as passed in
  XPLAT-002 evidence.
- **FR-017**: The handoff MUST provide XPLAT-003 a per-candidate supply-chain
  implication matrix for selected and rejected candidates, including dependency
  footprint, manifest/lockfile behavior, generated artifact types, build/release
  path, vulnerability-scan path, checksum/signature/SBOM/provenance feasibility,
  consumer-local verification ideas, offline/update implications, distribution
  trust root, transitive/build-time/native dependencies, build environment
  inputs, runtime/install execution risk, maintenance posture, assumption status,
  and evidence gaps, without selecting first-release controls. The matrix MUST
  classify whether each candidate's dependency/artifact assumptions are
  evidence-backed, unverified, or not applicable for vendored packages, embedded
  runtimes, native binaries, generated payload artifacts, lockfiles/manifests,
  and package-manager behavior.
- **FR-018**: The handoff MUST identify what XPLAT-004 can build from the
  selected runtime, `speckit-pro-runner` command contract, fixture parity
  expectations, and compatibility-adapter records without reopening the language
  or packaging choice.
- **FR-018b**: The XPLAT-004 handoff MUST include a traceable implementation
  input bundle derived from XPLAT-001 inventory rows. The bundle MUST record
  source row IDs, owner buckets, active invocation mode, selected runner helper
  IDs, runner operations/modes, adapter records if needed, fixture expectations,
  and explicit exclusions, and MUST NOT require source-checkout paths when an
  installed plugin-cache path is the integration target.
- **FR-018a**: The XPLAT-004 handoff MUST define fixture parity expectations for
  success, invalid JSON, missing required field, path-with-spaces, Windows
  separator, missing-prerequisite, subprocess-nonzero, subprocess-timeout,
  stderr-only failure, runtime-info or preflight, and at least one read-only
  legacy-helper comparison. For each failure fixture, the handoff MUST specify
  expected stdout `status`, process `exit_code`, stderr diagnostic `code`, and
  required response-field behavior so fixture authors can test from the
  requirement text alone.
- **FR-019**: The work MUST avoid changing README, docs-site pages, marketplace
  metadata, changelog, release notes, or other public support-claim surfaces
  beyond decision-record, target, candidate-evidence, and handoff wording.
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

- **Runtime Candidate**: A runtime family under historical evaluation, including
  its documentation evidence, probe evidence, rubric results, install
  reliability, installed-cache invocation reliability, and rejection or
  selection rationale. Python is the amended selected runtime; JavaScript/
  TypeScript and small per-platform binary records are rejected historical
  evidence only; hybrid compatibility adapters are temporary migration notes,
  not selectable runtime families.
- **Evaluation Evidence**: A cited documentation source, lightweight probe
  result, documentation/probe conflict, or explicitly recorded evidence gap used
  to support candidate scoring. Evidence gaps include the missing probe,
  host/runtime scope, reason unavailable, substitute evidence, gate or scoring
  effect, owner, and expiry/removal or follow-up condition.
- **Command Contract**: The selected runtime-facing command agreement covering
  entrypoint, dispatch, JSON input/output, diagnostics, exit codes, paths,
  subprocesses, prerequisites, and runtime version reporting. The canonical
  entrypoint is `speckit-pro-runner`; helpers are selected through JSON stdin
  fields rather than helper-specific CLI arguments.
- **Path Value**: A contract field that records a path plus its kind
  (`repo_relative`, `plugin_relative`, `cache_relative`, `absolute`, or `temp`)
  so outputs can remain readable without assuming POSIX separators.
- **Subprocess Result**: A structured subprocess outcome containing argv, cwd,
  captured stdout/stderr, exit code, timeout state, and missing-prerequisite
  diagnostics without shell interpolation.
- **Runtime Info**: The preflight/runtime-info response describing runner,
  contract, selected runtime, platform, plugin root, source-vs-installed
  context, capabilities, and prerequisite records.
- **XPLAT-004 Implementation Input Bundle**: A handoff artifact derived from
  XPLAT-001 inventory rows that maps row IDs, owner buckets, invocation modes,
  runner helper IDs, operations, modes, adapter records, fixture expectations,
  and exclusions into build-ready inputs for XPLAT-004 without assuming a source
  checkout.
- **Compatibility Adapter Record**: A temporary migration record, not a runtime
  candidate, with `adapter_id`, `legacy_surface`, `xplat001_source_row`,
  `runner_helper_id`, `runner_operation`, `runner_mode`, `owner_bucket`,
  `owner_spec`, `removal_spec`, `removal_condition`, and `evidence`. IDs use
  `xplat-005-compat-*`, `xplat-006-compat-*`, or `xplat-007-compat-*` according
  to the owning removal spec.
- **Supply-Chain Implication Matrix**: A per-candidate handoff artifact for
  XPLAT-003 covering selected and rejected candidates, dependency and bootstrap
  footprint, manifests/lockfiles, generated artifacts, build/release path,
  vulnerability scanning, checksum/signature/SBOM/provenance feasibility,
  consumer-local verification, offline/update behavior, distribution trust root,
  transitive/build-time/native dependencies, build inputs, install execution
  risk, maintenance posture, assumption status, and evidence gaps. It identifies
  artifact assumptions without treating them as selected controls.
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
  evidence gap, documentation/probe conflict, or objective install-reliability
  tie-breaker.
- **SC-007**: The decision record names all runtime-specific handoff items for
  XPLAT-003 and XPLAT-004 and contains no public support-claim, release-note, or
  public documentation promise changes.
- **SC-008**: The completed spike has a pass or warn reviewability result with
  no non-size blockers, or an honored named `infra` exception whose overage is
  limited to XPLAT PR-packet tooling support plus synced payload mirrors and
  does not add runner implementation or public support-claim surfaces.

## Assumptions

- XPLAT-001 runtime inventory and rubrics are available and are the
  authoritative baseline for this decision.
- Lightweight smoke probes are non-mutating. Repo-local state may establish
  setup context, but installed Claude and Codex plugin-cache invocation evidence
  or host-specific evidence gaps are required for the installed-cache gate.
- The public installed plugin cache must be usable without asking each user to
  install extra dependencies or fetch packages from the network.
- This phase records decision evidence and a command contract only; runner
  implementation, helper porting, and native release-readiness UAT remain out of
  scope.
- Runtime version reporting includes enough information for future diagnostics
  and verification to identify the selected runtime environment and command
  contract version.
