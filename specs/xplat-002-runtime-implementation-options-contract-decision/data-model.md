# Data Model: Runtime Implementation Options and Contract Decision

## Runtime Candidate

Represents one selectable runtime family.

**Fields**:

- `candidate_id`: stable slug, one of `javascript-typescript`, `python`, or
  `small-per-platform-binary`.
- `candidate_name`: reader-facing name.
- `runtime_family`: runtime/toolchain family.
- `documentation_evidence`: list of `Evaluation Evidence` IDs.
- `probe_evidence`: list of `Evaluation Evidence` IDs.
- `must_have_gates`: list of `Rubric Gate Result` records.
- `weighted_scores`: list of `Weighted Criterion Result` records.
- `installed_cache_gate`: pass/fail result with rationale.
- `supply_chain_implications`: `Supply-Chain Implication Matrix` entry.
- `decision_status`: `selected`, `rejected`, or `pending-evidence`.
- `decision_rationale`: summary of selection or rejection.

**Validation rules**:

- Exactly three selectable candidate records are required.
- Every candidate must use the same must-have gates and weighted criteria.
- A candidate cannot be selected unless `installed_cache_gate` is `pass`.
- XPLAT-002 implementation must end with exactly one `selected` candidate.

## Evaluation Evidence

Represents a documentation source, probe result, conflict, or evidence gap.

**Fields**:

- `evidence_id`: stable slug.
- `candidate_id`: runtime candidate the evidence supports.
- `evidence_type`: `official_documentation`, `plugin_platform_documentation`,
  `repo_local_source`, `probe_result`, `documentation_probe_conflict`, or
  `evidence_gap`.
- `source`: path, command, or citation target.
- `scope`: behavior evaluated.
- `result`: observed or documented outcome.
- `reliability_effect`: how the evidence affects gate/scoring decisions.
- `captured_at`: date or implementation evidence timestamp.

**Validation rules**:

- Each candidate must have at least one documentation evidence record.
- Uncertain invocation behavior must have a probe result or evidence gap.
- Documentation/probe conflicts must be recorded as their own evidence item.

## Rubric Gate Result

Represents one XPLAT-001 must-have gate result for a candidate.

**Fields**:

- `gate_id`: `installed_cache_invocation`, `native_platform_behavior`,
  `filesystem_and_paths`, `json_handling`, `subprocess_behavior`, or
  `packaging_and_update_path`.
- `candidate_id`: runtime candidate.
- `status`: `pass`, `fail`, or `gap`.
- `evidence_ids`: supporting evidence.
- `rationale`: decision note.

**Validation rules**:

- Gate results are pass/fail before weighted scoring is used for selection.
- A `fail` on installed-cache invocation prevents selection.

## Weighted Criterion Result

Represents one 0-5 evidence-backed rating.

**Fields**:

- `criterion_id`: one of the XPLAT-001 weighted criteria.
- `candidate_id`: runtime candidate.
- `weight`: numeric weight from XPLAT-001.
- `rating`: integer from 0 through 5.
- `weighted_points`: `weight * rating / 5`.
- `evidence_ids`: supporting evidence.
- `rationale`: scoring explanation.

**Validation rules**:

- All candidates use identical weights.
- Ratings must be evidence-backed, not preference-only.
- Install reliability and installed-cache invocation reliability break close
  ties before maintainer ergonomics.

## Command Contract

Represents the selected runner command interface.

**Fields**:

- `entrypoint`: `speckit-pro-runner`.
- `default_payload_relative_path`: `scripts/speckit-pro-runner`.
- `schema_version`: contract schema version.
- `request_envelope`: `Runner Request`.
- `response_envelope`: `Runner Response`.
- `stderr_diagnostics`: list of `Diagnostic Event` records.
- `exit_code_map`: shared process exit-code categories.
- `path_rules`: allowed `Path Value` kinds.
- `subprocess_rules`: `Subprocess Result` requirements.
- `runtime_info_operation`: runtime-info or preflight operation.

**Validation rules**:

- Helper-specific arguments are not encoded in argv.
- Stderr diagnostics must not corrupt stdout JSON.
- The contract must not include shell fallback, `.sh`, `jq`, globbing,
  interpolation, or redirection behavior.

## Runner Request

**Fields**:

- `schema_version`
- `request_id`
- `helper_id`
- `operation`
- `mode`
- `inputs`

**Validation rules**:

- The runner reads one versioned JSON request from stdin.
- CLI arguments are limited to metadata/help behavior such as `--help` and
  `--version`.

## Runner Response

**Fields**:

- `schema_version`
- `request_id`
- `helper_id`
- `status`
- `exit_code`
- `legacy_exit_code`
- `data`
- `diagnostics`
- `runtime`

**Validation rules**:

- The runner writes one versioned JSON response to stdout.
- `legacy_exit_code` is present only when parity requires a documented helper
  code.

## Diagnostic Event

**Fields**:

- `severity`
- `code`
- `message`
- `source`
- `details`

**Validation rules**:

- Stderr is line-delimited JSON.
- Messages are deterministic enough for fixture assertions.

## Path Value

**Fields**:

- `kind`: `repo_relative`, `plugin_relative`, `cache_relative`, `absolute`, or
  `temp`.
- `value`: raw path value.
- `display`: reader-facing repo/plugin-relative display path when available.

**Validation rules**:

- Contract behavior must preserve Windows, macOS, and Linux path semantics.
- Reader-facing output should prefer relative display paths when possible.

## Subprocess Result

**Fields**:

- `argv`
- `cwd`
- `env`
- `stdout`
- `stderr`
- `exit_code`
- `timed_out`
- `missing_prerequisite`

**Validation rules**:

- Subprocesses use structured argv arrays with shell disabled.
- cwd and env are explicit allowlists.
- Missing executables are reported as missing prerequisites.

## Runtime Info

**Fields**:

- `runner_name`
- `runner_version`
- `contract_version`
- `selected_runtime_name`
- `selected_runtime_version`
- `platform`
- `architecture`
- `plugin_root`
- `source_vs_installed_context`
- `capabilities`
- `prerequisites`

**Validation rules**:

- `prerequisites` records include `id`, `required`, `available`, `version`,
  `path`, `remediation`, and `severity`.
- The runtime-info or preflight operation must support installed-cache support
  diagnostics.

## Compatibility Adapter Record

Temporary migration evidence, not a runtime candidate.

**Fields**:

- `adapter_id`
- `legacy_surface`
- `xplat001_source_row`
- `runner_helper_id`
- `runner_operation`
- `runner_mode`
- `owner_bucket`
- `owner_spec`
- `removal_spec`
- `removal_condition`
- `evidence`

**Validation rules**:

- `adapter_id` uses an owner-first prefix such as
  `xplat-005-compat-<legacy-helper-or-surface-slug>`.
- `owner_spec` and `removal_spec` must be explicit uppercase spec IDs.

## Supply-Chain Implication Matrix

Per-candidate handoff to XPLAT-003.

**Fields**:

- `candidate_id`
- `dependency_footprint`
- `bootstrap_footprint`
- `manifest_lockfile_impact`
- `generated_artifact_shape`
- `build_release_path`
- `vulnerability_scan_path`
- `checksum_signature_sbom_provenance_feasibility`
- `consumer_local_verification`
- `offline_update_implications`
- `distribution_trust_root`
- `transitive_build_time_native_dependencies`
- `build_environment_inputs`
- `runtime_install_execution_risk`
- `maintenance_posture`
- `evidence_gaps`

**Validation rules**:

- The matrix records implications only.
- XPLAT-003 chooses controls; XPLAT-002 must not overclaim guarantees.

## Handoff Item

**Fields**:

- `handoff_id`
- `target_spec`: `XPLAT-003` or `XPLAT-004`.
- `source_evidence`
- `required_action`
- `boundary`

**Validation rules**:

- XPLAT-003 receives runtime-specific supply-chain implications.
- XPLAT-004 receives only the selected runtime, command contract, fixture
  parity expectations, and compatibility adapter records.
