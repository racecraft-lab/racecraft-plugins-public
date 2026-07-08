# Data Model: Plugin Source and Payload Bash Eradication

## Entity: Source Bash Inventory Record

Represents one live `.sh` file found under `speckit-pro/` before deletion.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `path` | string | Yes | Repo-relative path to the source `.sh` file. |
| `sha256` | string | Yes | Hash captured before deletion for traceability. |
| `surface` | enum | Yes | `skill`, `codex_skill`, `agent`, `codex_agent`, `hook`, `plugin_script`, `library`, or `install_support`. |
| `active_role` | enum | Yes | `active_behavior`, `active_guidance`, `inactive_provenance`, or `obsolete`. |
| `classification` | enum | Yes | `port_required`, `delete_only`, or `historical_archive_only`. |
| `python_helper_id` | string | Conditional | Required when active behavior is retained. |
| `python_operation` | string | Conditional | Required when active behavior is retained. |
| `delete_criteria` | string | Yes | Test or proof that must pass before removal. |
| `release_readiness_excluded` | boolean | Yes | Must be `true` for historical/inactive records. |

## Entity: Python Operation Ownership Record

Maps formerly shell-owned active behavior to runner/helper/gate ownership.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `helper_id` | string | Yes | Runner helper or gate helper ID. |
| `operation` | string | Yes | Operation ID exposed in active registries and outputs. |
| `mode` | array | Yes | Supported modes such as `read_only`, `dry_run`, or `apply`. |
| `module` | string | Yes | Python module that owns the behavior. |
| `previous_script_paths` | array | Yes | Legacy script paths retained only as provenance. |
| `promotion_status` | enum | Yes | `python_authoritative`, `golden_only`, `deferred`, or `out_of_scope`. |
| `active_output_policy` | enum | Yes | `python_operation_only` or `inactive_provenance_only`. |
| `tests` | array | Yes | Focused tests proving the operation before source deletion. |

## Entity: Active Instruction Finding

Represents a detected active source, generated payload, or installed-cache
instruction that mentions shell-oriented behavior.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `surface` | enum | Yes | `plugin_source`, `generated_payload`, or `installed_cache`. |
| `path` | string | Yes | Repo-relative path or proof-root-relative path. |
| `line` | integer | Yes | One-based line number when available. |
| `category` | enum | Yes | `script_file`, `bash`, `jq`, `shell_interpolation`, `git_bash`, `wsl`, `powershell_helper`, or `unix_only`. |
| `pattern` | string | Yes | Matched pattern or file suffix. |
| `reason` | string | Yes | Why the finding matters. |
| `classification` | enum | Yes | `blocking_active_runtime`, `allowlisted_historical`, `inactive_provenance`, or `nonblocking_policy`. |
| `active_role` | string | Yes | Current role of the file or instruction. |
| `remediation` | string | Yes | Concrete fix guidance. |

## Entity: Historical Allowlist Entry

Documents a permitted historical/archive mention. These entries cannot satisfy
release readiness.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `path` | string | Yes | Repo-relative path containing the reference. |
| `line_start` | integer | No | Optional one-based starting line. |
| `line_end` | integer | No | Optional one-based ending line. |
| `category` | enum | Yes | `historical_archive`, `negative_policy`, or `inactive_provenance`. |
| `reason` | string | Yes | Why the reference may remain. |
| `scope` | string | Yes | Boundaries of the allowed reference. |
| `release_readiness_excluded` | boolean | Yes | Must be `true`. |
| `owner` | string | Yes | Owning phase or feature, usually `XPLAT-009`. |

## Entity: Payload Rebuild Record

Proves generated payloads were rebuilt from source.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `surface` | enum | Yes | `claude` or `codex`. |
| `source_root` | string | Yes | Source plugin root used for the rebuild. |
| `output_root` | string | Yes | Generated payload root under `dist/**`. |
| `operation` | string | Yes | Must be `payload-gate/payload-completeness`. |
| `mode` | string | Yes | Must be `apply` for rebuild and `read_only` for post-check. |
| `source_tree_hash` | string | Yes | Hash of source tree inputs. |
| `output_tree_hash` | string | Yes | Hash of generated output tree. |
| `missing_files` | array | Yes | Must be empty for release readiness. |
| `extra_files` | array | Yes | Must be empty for release readiness. |
| `mismatched_files` | array | Yes | Must be empty for release readiness. |
| `path_leaks` | array | Yes | Must be empty for release readiness. |
| `script_file_count` | integer | Yes | Must be `0`. |

## Entity: Installed Cache Proof Record

Proves a bounded installed artifact derived from rebuilt payloads is Bash-free.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `product` | enum | Yes | `claude` or `codex`. |
| `surface` | string | Yes | Installed-cache proof surface. |
| `installed_root` | string | Yes | Bounded fixture or temporary installed root. |
| `source_payload_root` | string | Yes | Generated payload root used to create proof. |
| `source_payload_hash` | string | Yes | Hash tying proof to rebuilt payload. |
| `file_inventory` | array | Yes | Bounded inventory of installed files. |
| `source_derived` | boolean | Yes | Must be `true`. |
| `mutable_user_cache` | boolean | Yes | Must be `false` for required proof. |
| `script_file_count` | integer | Yes | Must be `0`. |
| `active_guidance_findings` | array | Yes | Must contain no blocking findings. |
| `allowlist_exclusion_state` | enum | Yes | `excluded_from_release_readiness` or `not_used`. |

## Entity: Zero-Bash Guard Request

Single runner request covering source, generated payloads, and installed-cache
proof.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `schema_version` | string | Yes | `1.0`. |
| `helper_id` | string | Yes | `active-path-guard`. |
| `operation` | string | Yes | `zero-bash-guard`. |
| `mode` | string | Yes | `read_only`. |
| `inputs.source_roots` | array | Yes | Includes `speckit-pro/`. |
| `inputs.generated_payload_roots` | array | Yes | Includes Claude and Codex payload roots. |
| `inputs.installed_cache_proofs` | array | Yes | Proof records or proof-root references. |
| `inputs.allowlist` | array | Yes | Historical allowlist entries. |
| `inputs.findings_limit` | integer | Yes | Bounded output limit. |

## Entity: Zero-Bash Guard Result

Runner result consumed by release readiness.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `status` | enum | Yes | `ok`, `validation_failure`, or `input_error`. |
| `blocking_count` | integer | Yes | Must be `0` for release readiness. |
| `classified_counts` | object | Yes | Counts by category and classification. |
| `findings` | array | Yes | Bounded finding list. |
| `scan_roots` | array | Yes | Roots and proof records scanned. |
| `allowlist_entries` | array | Yes | Entries applied, all release-readiness excluded. |
| `diagnostics` | array | Yes | Includes `zero_bash_guard_blocked` on blocking failure. |

## Relationships

- A `Source Bash Inventory Record` with `classification = port_required` must
  reference one `Python Operation Ownership Record`.
- A `Source Bash Inventory Record` may be deleted only after its ownership
  record tests pass or the record is proven `delete_only`.
- A `Historical Allowlist Entry` may classify an `Active Instruction Finding` as
  nonblocking only when the entry scope matches the path and category.
- A `Payload Rebuild Record` is required before each `Installed Cache Proof
  Record` for the same product.
- A `Zero-Bash Guard Result` must include all source roots, both generated
  payload roots, and all required installed-cache proof records before release
  readiness can pass.

## Invariants

- `speckit-pro/` has zero `.sh` files at the end of Slice 1.
- Generated Claude and Codex payload roots have zero `.sh` files after Slice 2
  rebuilds.
- Required installed-cache proof is bounded, source-derived, and not a mutable
  real user cache.
- Active registries expose Python operation IDs, not runnable `.sh` paths.
- Historical allowlist entries always carry release-readiness exclusion and
  cannot count as release-ready proof.
- XPLAT-008 native UAT remains out of scope and preserved as known release
  context.
