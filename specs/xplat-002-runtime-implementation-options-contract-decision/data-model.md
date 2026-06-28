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
- `installed_cache_gate`: runtime-model viability and pass/fail/gap probe
  status with rationale.
- `reliability_tiebreaker`: `Reliability Tie-Breaker Result`, required when
  this candidate is part of a close-candidate comparison.
- `supply_chain_implications`: `Supply-Chain Implication Matrix` entry.
- `decision_status`: `selected`, `rejected`, or `pending-evidence`.
- `decision_rationale`: summary of selection or rejection.

**Validation rules**:

- Exactly three selectable candidate records are required.
- Every candidate must use the same must-have gates and weighted criteria.
- A candidate cannot be selected unless `installed_cache_gate` shows no
  post-cache dependency setup is required. If the runner artifact does not yet
  exist, installed-cache invocation proof remains a downstream acceptance item
  and cannot be counted as a probe pass.
- XPLAT-002 implementation must end with exactly one `selected` candidate.

## Evaluation Evidence

Represents a documentation source, probe result, conflict, or evidence gap.

**Fields**:

- `evidence_id`: stable slug.
- `candidate_id`: runtime candidate the evidence supports.
- `evidence_type`: `official_documentation`, `plugin_platform_documentation`,
  `repo_local_source`, `probe_result`, `documentation_probe_conflict`, or
  `evidence_gap`.
- `probe_status`: `pass`, `fail`, `gap`, or `not_applicable`.
- `source`: path, command, or citation target.
- `scope`: behavior evaluated.
- `result`: observed or documented outcome.
- `fallback_plan`: required when `evidence_type` is `evidence_gap`.
- `reliability_effect`: how the evidence affects gate/scoring decisions.
- `captured_at`: date or implementation evidence timestamp.

**Validation rules**:

- Each candidate must have at least one documentation evidence record.
- Uncertain invocation behavior must have installed Claude and installed Codex
  plugin-cache probe results or host-specific evidence gaps.
- Repo-local and generated-payload probe records may supplement setup evidence,
  but cannot satisfy the installed-cache gate by themselves.
- Documentation/probe conflicts must be recorded as their own evidence item.
- Evidence gaps must name the missing probe, host/runtime scope, reason
  unavailable, substitute official or repo-local evidence consulted, gate or
  scoring effect, owner, and expiry/removal or follow-up condition.
- Evidence gaps cannot be scored as installed-cache probe passes.

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
- A `fail` on installed-cache invocation prevents selection. A missing
  invocation probe can only support selection when the runtime model has no
  post-cache setup dependency, the missing artifact is explicitly out of
  XPLAT-002 scope, and the proof is assigned to XPLAT-004 acceptance.

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

## Reliability Tie-Breaker Result

Represents the ordered reliability comparison used only for close selectable
candidates.

**Fields**:

- `candidate_ids`: candidates compared.
- `close_reason`: `weighted_delta_le_five` or
  `non_reliability_score_lead`.
- `weighted_total_delta`: numeric difference between compared weighted totals.
- `reliability_inputs`: evidence-backed values for installed Claude cache probe,
  installed Codex cache probe, post-cache dependency setup burden, offline
  behavior after cache population, first-run/bootstrap failure diagnostics, and
  runtime-info/preflight completeness.
- `ordered_result`: selected candidate after applying the ordered inputs, or
  `unresolved`.
- `unresolved_reason`: required when `ordered_result` is `unresolved`.

**Validation rules**:

- Candidates are close only when they have no selection-blocking gate failures
  and weighted totals differ by five points or less, or when the leading score
  depends only on maintainer ergonomics or compatibility-adapter criteria while
  reliability criteria are tied or favor another candidate.
- Tie-breaker inputs must come from `Evaluation Evidence` records.
- Installed-cache probe pass/fail/gap values are compared before maintainer
  preference.
- Post-cache setup burden and offline behavior are compared before maintainer
  preference.
- First-run/bootstrap diagnostics and runtime-info/preflight completeness are
  compared before maintainer preference.
- If ordered reliability inputs do not produce a winner, the decision record
  must remain unresolved for that comparison rather than selecting by narrative
  preference.

## Command Contract

Represents the selected runner command interface.

**Fields**:

- `entrypoint`: `speckit-pro-runner`.
- `runner_source_path`: `scripts/speckit_pro_runner.py`.
- `optional_launcher_path`: `scripts/speckit-pro-runner`, only if XPLAT-004
  needs a thin dispatch-only launcher.
- `schema_version`: contract schema version.
- `request_envelope`: `Runner Request`.
- `response_envelope`: `Runner Response`.
- `stderr_diagnostics`: list of `Diagnostic Event` records.
- `exit_code_map`: shared process exit-code categories.
- `path_rules`: allowed `Path Value` kinds.
- `subprocess_rules`: `Subprocess Result` requirements.
- `helper_dispatch`: `Helper Dispatch` requirements.
- `runtime_info_operation`: runtime-info or preflight operation.

**Validation rules**:

- Helper-specific arguments are not encoded in argv.
- `helper_id`, `operation`, and `mode` resolve to runner-owned implementations
  under the installed plugin payload/cache root.
- The contract must not require source checkout paths for installed Claude or
  Codex invocation.
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
- `status` is one of `ok`, `expected_failure`, `input_error`,
  `missing_prerequisite`, `subprocess_failure`, or `internal_failure`.
- `request_id` and `helper_id` may be `null` only for input validation
  failures where the malformed envelope prevents reading those identifiers.
- `legacy_exit_code` is present only when parity requires a documented helper
  code.
- Failure responses must still carry the shared process `exit_code` category
  expected by the command contract.

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
- XPLAT-004 fixture diagnostics use stable codes for malformed input and
  subprocess failures: `invalid_json`, `invalid_envelope`,
  `unsupported_schema_version`, `missing_required_field`,
  `missing_prerequisite`, `subprocess_nonzero`, `subprocess_timeout`,
  `subprocess_stderr_only_failure`, and `internal_failure`.

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

## Helper Dispatch

**Fields**:

- `helper_id`
- `operation`
- `mode`
- `implementation_ref`
- `source_row_ids`
- `adapter_id`

**Validation rules**:

- `implementation_ref` is resolved relative to the installed plugin
  payload/cache root unless XPLAT-004 deliberately records another installed
  payload convention.
- Dispatch must not depend on paths under the repository authoring checkout.
- `source_row_ids` trace back to XPLAT-001 inventory rows when the helper
  replaces or adapts an inventoried active runtime surface.

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
- `artifact_assumption_type`: one of `none`, `source_only`, `generated_payload`,
  `vendored_package`, `embedded_runtime`, `native_binary`, `platform_specific`,
  `external_package_manager`, or `unknown`.
- `artifact_assumption_status`: `evidence_backed`, `unverified`, or
  `not_applicable`.
- `artifact_origin_evidence`
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
- `unknown` or `unverified` artifact assumptions must also appear in
  `evidence_gaps`.
- Artifact assumption fields classify the handoff for XPLAT-003 only; they do
  not approve vendoring, embedding, binary distribution, lockfile policy,
  checksums, signatures, SBOMs, provenance, or vulnerability-scan controls.

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

## XPLAT-004 Implementation Input Bundle

**Fields**:

- `bundle_id`
- `selected_runtime_candidate_id`
- `xplat001_row_ids`
- `owner_buckets`
- `active_invocation_modes`
- `runner_helper_ids`
- `runner_operations`
- `runner_modes`
- `adapter_records`
- `fixture_expectations`
- `explicit_exclusions`
- `evidence_ids`

**Validation rules**:

- Every included active-runtime input traces to an XPLAT-001 row ID.
- Inputs for generated payload cutover remain explicitly excluded from
  XPLAT-004 unless needed to prove the runner contract.
- The bundle must use installed plugin payload/cache paths as the integration
  target and must not require a source checkout.
