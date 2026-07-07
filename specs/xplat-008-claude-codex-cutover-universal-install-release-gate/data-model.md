# Data Model: Claude/Codex Cutover and Universal Install Release Gate

## InstalledRuntimeSurface

Represents a Claude or Codex source or generated path that can affect installed user workflow execution.

| Field | Type | Required | Notes |
|---|---|---|---|
| `surface_id` | string | yes | Stable identifier, for example `claude.skill.speckit-status`. |
| `product` | enum | yes | `claude` or `codex`. |
| `path` | string | yes | Repo-relative source or generated payload path. |
| `category` | enum | yes | `skill`, `agent`, `hook`, `install_guidance`, `generated_payload`, `release_gate`, `archive_provenance`, `ci_dispatch_glue`, `upstream_spec_kit_helper`, `test_fixture`, `docs_prose`. |
| `active_runtime` | boolean | yes | `true` only when the path can affect installed workflow execution. |
| `allowed_shell_context` | enum | yes | `none`, `archive`, `ci_dispatch`, `upstream_helper`, `test_fixture`, or `docs_non_runtime`. |
| `runner_invocation_required` | boolean | yes | `true` for active installed-runtime behavior. |
| `guard_status` | enum | yes | `pass`, `fail`, or `not_applicable`. |
| `evidence` | array[string] | yes | Paths or gate output records proving classification. |

**Validation rules**:

- `active_runtime=true` requires `runner_invocation_required=true`.
- `active_runtime=true` requires `allowed_shell_context=none`.
- Any prohibited shell-only runtime term in an active runtime surface is blocking.

## InterpreterResolutionRecord

Captures how an installed surface found or failed to find Python `>=3.11`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `platform` | enum | yes | `windows`, `macos`, or `linux`. |
| `attempted_candidates` | array[string] | yes | Windows: `py -V:3`, `py -3`, `python`, `python3`; macOS/Linux: `python3`, `python`. |
| `resolved_executable` | string or null | yes | Absolute executable path when accepted. |
| `version` | string or null | yes | Resolved Python version. |
| `accepted` | boolean | yes | `true` only for Python `>=3.11`. |
| `cache_root` | string | yes | Installed plugin cache root used during resolution. |
| `failure_code` | string or null | yes | Required when `accepted=false`. |
| `diagnostic` | string | yes | User-facing remediation text; no shell fallback. |

## RunnerInvocationRecord

Captures the installed-runtime command contract for one operation.

| Field | Type | Required | Notes |
|---|---|---|---|
| `schema_version` | string | yes | Must be `1.0`. |
| `request_id` | string | yes | Correlates request and response. |
| `product` | enum | yes | `claude` or `codex`. |
| `platform` | enum | yes | `windows`, `macos`, or `linux`. |
| `surface_path` | string | yes | Links to the installed-runtime source or generated payload path. |
| `operation` | enum | yes | `preflight`, `scaffold`, `status`, `autopilot-dry-run`, `doctor`, `update`, or `autoheal`. |
| `interpreter_resolution` | InterpreterResolutionRecord | yes | Platform discovery result used for invocation. |
| `invocation` | object | yes | Contains argv `[resolved_python, "-m", "speckit_pro_runner"]`, stdin/stdout/stderr modes, and `shell_used=false`. |
| `runner_request` | object | yes | Runner request envelope. |
| `runner_response` | object or null | yes | Runner response envelope on success. |
| `status` | enum | yes | `pass`, `fail`, or `blocked`. |
| `diagnostics` | array[object] | yes | Structured user-facing diagnostic and remediation records. |

## PayloadInventoryItem

Represents one expected file in a generated Claude or Codex payload.

| Field | Type | Required | Notes |
|---|---|---|---|
| `payload_surface` | enum | yes | `claude` or `codex`. |
| `path` | string | yes | Payload-relative normalized POSIX path. |
| `source_path` | string | yes | Repo-relative source path or generated metadata source. |
| `kind` | enum | yes | `manifest`, `skill`, `agent`, `hook`, `runner`, `install_guidance`, `trust_metadata`, `checksum`, `version_metadata`, `docs`. |
| `transform` | enum | yes | `none`, `claude_guard_strip`, `codex_overlay`, `path_normalization`, or `manifest_rewrite`. |
| `sha256` | string | yes | Expected digest after transform. |
| `required` | boolean | yes | Missing required items block release. |

## PayloadCompletenessResult

Aggregates the payload gate for Claude or Codex.

| Field | Type | Required | Notes |
|---|---|---|---|
| `payload_surface` | enum | yes | `claude` or `codex`. |
| `plugin_version` | string | yes | Must match release source of truth. |
| `runner_version` | string | yes | Independent runner contract version. |
| `expected_files` | array[PayloadInventoryItem] | yes | Source-derived expected files. |
| `actual_files` | array[PayloadInventoryItem] | yes | Generated payload files found during comparison. |
| `missing_paths` | array[string] | yes | Blocking when non-empty. |
| `extra_paths` | array[string] | yes | Blocking unless explicitly allowed. |
| `mismatched_paths` | array[string] | yes | Blocking digest or transform mismatches. |
| `path_leaks` | array[string] | yes | Blocking absolute, traversal, or opposite-platform leaks. |
| `file_tree_hash` | string | yes | Deterministic tree digest. |
| `status` | enum | yes | `pass` or `fail`. |

## NativeUATRow

Represents one required product/platform installed-plugin journey.

| Field | Type | Required | Notes |
|---|---|---|---|
| `product` | enum | yes | `claude` or `codex`. |
| `platform` | enum | yes | `windows`, `macos`, or `linux`. |
| `operator` | string | yes | Human operator. |
| `date` | string | yes | ISO date. |
| `host_version` | string | yes | OS and product host version. |
| `plugin_version_or_latest_tag` | string | yes | Installed plugin version or latest tag. |
| `installed_cache_path` | string | yes | Installed cache root. |
| `interpreter_resolution` | InterpreterResolutionRecord | yes | Must be accepted. |
| `runner_invocation_ids` | array[string] | yes | Request IDs linking this UAT row to aggregate runner invocation records. |
| `install_result` | enum | yes | `pass` or `fail`. |
| `bundled_agent_verification` | enum | yes | `pass` or `fail`. |
| `first_use` | enum | yes | `pass` or `fail`. |
| `scaffold_status` | enum | yes | `pass` or `fail`. |
| `autopilot_dry_run` | enum | yes | `pass` or `fail`. |
| `latest_tag_update` | enum | yes | `pass` or `fail`. |
| `incomplete_install_repair` | enum | yes | `pass` or `fail`. |
| `expected_result` | string | yes | Non-empty, reviewer-readable. |
| `actual_result` | string | yes | Non-empty, reviewer-readable. |
| `evidence_link` | string | yes | Feature-local evidence path; raw HTML anchors are invalid. |
| `operator_notes` | string | yes | May include limitations but not placeholders. |
| `status` | enum | yes | `pass` or `fail`. |

**Validation rules**:

- The full matrix requires exactly six product/platform combinations.
- Placeholder-only, smoke-only, empty expected/actual fields, raw HTML anchors, missing evidence links, or `status=fail` block release.
- Public support claims are allowed only for passing rows.

## InstallHealthFinding

Represents stale, missing, incomplete, unsafe, or untrusted installed-cache state.

| Field | Type | Required | Notes |
|---|---|---|---|
| `finding_id` | string | yes | Stable finding identifier. |
| `installed_cache_path` | string | yes | Trusted cache root. |
| `artifact_path` | string | yes | Path under installed cache. |
| `artifact_kind` | enum | yes | `generated_payload`, `bundled_agent`, `hook`, `runner_file`, `manifest`, `checksum`, `unknown`, `extra`. |
| `source_identity` | string or null | yes | Required for trusted repair. |
| `release_channel_or_tag` | string or null | yes | Required for trusted repair. |
| `expected_digest` | string or null | yes | Required for trusted repair. |
| `actual_digest` | string or null | yes | Present when artifact exists. |
| `classification` | enum | yes | `trusted_missing`, `trusted_stale`, `unsafe_unknown`, `unsafe_extra`, `unsafe_mismatch`, `unsafe_trust_root_change`, `unsafe_out_of_cache`. |
| `repair_allowed` | boolean | yes | `true` only for trusted missing/stale artifacts. |

## RepairAction

Represents the outcome of doctor/autoheal.

| Field | Type | Required | Notes |
|---|---|---|---|
| `action_id` | string | yes | Stable action identifier. |
| `finding_id` | string | yes | Links to `InstallHealthFinding`. |
| `action_type` | enum | yes | `autoheal_refresh` or `manual_remediation`. |
| `target_path` | string | yes | Installed-cache path. |
| `source_path` | string or null | yes | Source path used for trusted refresh. |
| `digest_verified` | boolean | yes | `true` required for autoheal. |
| `status` | enum | yes | `completed`, `skipped`, or `blocked`. |
| `message` | string | yes | User-facing result. |
| `manual_steps` | array[string] | yes | Required when action type is `manual_remediation`. |

**State transitions**:

- `trusted_missing` or `trusted_stale` -> `autoheal_refresh` -> `completed` when digest verifies.
- Any unsafe classification -> `manual_remediation` -> `blocked` until the user repairs manually.
- Broad reinstall or wipe-copy is never a valid transition.

## ReleaseReadinessGateRecord

Aggregates final public release readiness.

| Field | Type | Required | Notes |
|---|---|---|---|
| `feature_id` | string | yes | `XPLAT-008`. |
| `status` | enum | yes | `pass` or `fail`. |
| `checks` | array[object] | yes | One row per blocker class. |
| `blocking_count` | integer | yes | Number of failing checks. |
| `payload_results` | array[PayloadCompletenessResult] | yes | Claude and Codex. |
| `uat_rows` | array[NativeUATRow] | yes | Six rows. |
| `repair_actions` | array[RepairAction] | yes | Doctor/autoheal evidence. |
| `public_claim_results` | array[object] | yes | Supported and rejected claims. |
| `runner_invocations` | array[RunnerInvocationRecord] | yes | Active installed-runtime invocation evidence for first-use, update, doctor, and autoheal journeys. |
| `traceability` | array[object] | yes | Requirement/success criterion to evidence mapping. |

**Blocking classes**:

- Active shell runtime dependency.
- Incomplete generated payload.
- Missing bundled agent, hook, runner file, manifest, checksum, or trust record.
- Stale version metadata.
- Unsafe public claim.
- Incomplete, placeholder-only, smoke-only, or failing UAT row.
- Unsafe repair claim or broad autoheal behavior.

## Relationships

- `InstalledRuntimeSurface` produces `RunnerInvocationRecord`.
- `RunnerInvocationRecord` includes `InterpreterResolutionRecord`.
- `PayloadInventoryItem` rolls up into `PayloadCompletenessResult`.
- `NativeUATRow` uses `RunnerInvocationRecord`, `InterpreterResolutionRecord`, and `RepairAction` evidence.
- `InstallHealthFinding` produces `RepairAction`.
- `ReleaseReadinessGateRecord` aggregates payload results, UAT rows, repair actions, public claim results, runner invocation records, and traceability evidence.
