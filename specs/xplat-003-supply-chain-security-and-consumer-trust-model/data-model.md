# Data Model: Supply-Chain Security and Consumer Trust Model

## Entity Overview

XPLAT-003 models security and trust decisions as reviewable records, not runtime objects. Downstream specs may translate these records into scripts, CI gates, release artifacts, docs, or generated payload checks.

## Security Control Decision

Represents one evaluated trust control.

| Field | Required | Notes |
|---|---|---|
| `control_id` | Yes | Stable kebab-case identifier, for example `sha256-checksums`. |
| `name` | Yes | Human-readable control name. |
| `classification` | Yes | `first_release_required`, `deferred_hardening`, `explicitly_not_claimed`, or `out_of_scope`. |
| `owner_surface` | Yes | `XPLAT-004`, `XPLAT-007`, `release-automation`, `docs-release-notes`, or future owner. |
| `source_trace` | Yes | XPLAT-001 rubric row, XPLAT-002 handoff section, or XPLAT-003 requirement reference. |
| `rationale` | Yes | Why the classification fits first release. |
| `evidence_required` | Yes | Evidence required before readiness or claims can pass. |
| `acceptance_gate` | Yes | Blocking rule applied by the owner surface. |
| `promotion_condition` | Conditional | Required for deferred controls. |
| `claim_boundary` | Conditional | Required when public wording could overstate the guarantee. |

Validation rules:

- Every first-release control must name an owner and acceptance gate.
- Deferred controls must include promotion conditions.
- Explicitly not claimed controls must include prohibited claim wording or a claim-boundary rule.
- No control may assign implementation work to XPLAT-003.

## Owner Assignment

Maps controls to the downstream spec or release surface that implements and verifies them.

| Field | Required | Notes |
|---|---|---|
| `owner_surface` | Yes | Downstream spec or release/docs surface. |
| `owned_controls` | Yes | List of `control_id` values. |
| `implementation_scope` | Yes | What that owner can change. |
| `blocked_when` | Yes | Conditions that fail readiness for that owner. |
| `handoff_evidence` | Yes | Inputs the owner receives from XPLAT-003. |

Known owners:

- XPLAT-004 owns runner source, stdlib-only dependency policy, prerequisite
  preflight/version, launcher metadata when needed, checksum, manifest, and
  applicable scan controls.
- XPLAT-007 owns generated-payload integrity, Python build/test/eval/release
  gates for shipped behavior, consumer guidance, native UAT, public claim
  readiness, and cutover evidence.
- Release automation owns publication-time evidence only after a later spec edits release automation; until downstream acceptance evidence exists, assigned release automation controls are not implemented and not claimable.
- Public docs and release notes own wording only after implementation evidence exists.

## Platform Capability Evidence

Records official Claude Code and OpenAI Codex documentation findings used to
separate supported plugin surfaces from runtime/toolchain assumptions.

| Field | Required | Notes |
|---|---|---|
| `platform` | Yes | `claude-code` or `openai-codex`. |
| `official_docs_refs` | Yes | Official documentation URLs used as evidence. |
| `supported_surfaces` | Yes | Skills, scripts, hooks, MCP servers, `bin/` executables, apps, agents, or custom-agent registration surfaces documented for the platform. |
| `runtime_guarantees` | Yes | Runtime guarantees found in docs; use `none_found` when no user-host runtime guarantee exists. |
| `runtime_not_guaranteed` | Yes | Runtime/tool families not guaranteed for all installed plugin hosts by Claude/Codex platform docs alone, for example Go, Rust, Zig, Node, Bash, `jq`, package managers, WSL, or Git Bash. Python is allowed only through the official Spec Kit / `specify` prerequisite boundary and must be verified by preflight. |
| `install_surface_distinctions` | Yes | Platform-specific distinctions such as Codex plugin skills versus `.codex/agents/*.toml` custom-agent registration. |
| `xplat_gate_effect` | Yes | How the finding affects XPLAT-004/XPLAT-007 readiness and claims. |

Validation rules:

- Official platform docs may prove packaging or registration support, but they
  must not be used as proof of arbitrary user-host runtime availability unless
  the docs explicitly guarantee that runtime for the installed surface.
- Local host probes and repository tooling are supplemental evidence only.
- Missing custom-agent registration for Codex is an install-completeness gap
  when Codex agents are part of the release promise.

## Runtime Dependency Boundary

Records the Python-only runtime boundary for XPLAT.

| Field | Required | Notes |
|---|---|---|
| `runtime_shape` | Yes | Must be `python-stdlib-runner` for XPLAT. |
| `build_time_toolchain` | Conditional | Must be `null` for the Python stdlib runner. |
| `installed_user_runtime_dependency` | Yes | Official Spec Kit / `specify` prerequisite boundary, including Python 3.11+. |
| `bundled_runtime_payload` | Conditional | Must be `null`; bundled runtimes are out of XPLAT scope. |
| `official_runtime_guarantee_ref` | Yes | Official Spec Kit package metadata and installation docs proving the Python prerequisite. |
| `post_cache_setup_required` | Yes | Must be `false` for first-release native-support claims. |
| `prerequisite_diagnostics` | Yes | Fail-closed diagnostic behavior when a runtime/executable/prerequisite is missing. |
| `claim_effect` | Yes | Whether public native-support claims are allowed, blocked, or conditional. |

Validation rules:

- First-release native-support claims require `post_cache_setup_required=false`.
- Go, Rust, Zig, bundled Node, embedded Python, and native binaries are not
  XPLAT runtime shapes, fallbacks, or compatibility adapters.
- Source scripts that require Node, Bash, `jq`, package managers, WSL, Git
  Bash, or network restoration after cache population are not valid for
  first-release support claims unless official docs guarantee the runtime or the
  payload bundles it with matching supply-chain controls. Python is allowed only
  through the official Spec Kit / `specify` prerequisite boundary and must be
  verified by preflight.

## Install Completeness Evidence

Records whether a Claude Code or Codex install has every required platform
surface for the release promise.

| Field | Required | Notes |
|---|---|---|
| `platform` | Yes | `claude-code` or `openai-codex`. |
| `plugin_version` | Yes | Installed plugin version under review. |
| `payload_root` | Yes | Installed payload/cache root inspected. |
| `skills_status` | Yes | Present/missing/stale status for required skills. |
| `scripts_status` | Yes | Present/missing/stale/executable status for required scripts or executables. |
| `hooks_status` | Conditional | Required when hooks are part of the platform payload. |
| `mcp_status` | Conditional | Required when MCP servers/config are part of the platform payload. |
| `agent_registration_status` | Conditional | Required when Claude plugin agents or Codex custom-agent TOML files are part of the release promise. |
| `autoheal_action` | Conditional | Required when the install can be repaired automatically. |
| `fail_closed_behavior` | Yes | User-facing blocked or repair-required state when required pieces are missing. |

Validation rules:

- Codex skills present in the plugin cache do not prove Codex custom agents are
  installed; `.codex/agents/*.toml` or `~/.codex/agents/*.toml` must be checked
  when those agents are required.
- Claude Code plugin agents and Codex custom-agent TOML registrations are
  different install surfaces and must not be collapsed into one generic "agents"
  check.
- Autoheal must repair only documented local install surfaces and must fail
  closed when a required platform surface cannot be verified.

## Runner File Distribution Evidence

Records how selected runner files move from source or release inputs into
installed Claude Code and Codex marketplace payloads. For the selected
first-release runtime, these are Python source and thin launcher files.

| Field | Required | Notes |
|---|---|---|
| `runtime_shape` | Yes | Selected runtime shape, currently `python-stdlib-runner`. |
| `distribution_mode` | Yes | Must be `bundled-source` for XPLAT. |
| `source_runner_paths` | Yes | Source or release-input runner file paths produced by XPLAT-004. |
| `generated_claude_payload_paths` | Yes | Payload-relative paths under `dist/claude/speckit-pro`. |
| `generated_codex_payload_paths` | Yes | Payload-relative paths under `dist/codex/speckit-pro`. |
| `launcher_surface` | Yes | Documented launch surface such as Claude skill script, Claude hook command, Codex skill script, Codex plugin-bundled hook, or Codex plugin-bundled MCP command. |
| `post_install_download_required` | Yes | Whether the installed user must download a runner file after marketplace cache population. |
| `launch_metadata_policy` | Yes | Interpreter discovery, argv shape, executable-bit needs for optional thin launchers, and Windows command behavior. |
| `checksum_manifest_refs` | Yes | Manifest and checksum metadata that cover every generated runner file path. |
| `official_docs_refs` | Yes | Official Claude/Codex docs used to justify the launch and install surface. |
| `claim_effect` | Yes | Whether native-support claims are claimable, blocked, deferred, or require explicit repair/download wording. |

Validation rules:

- `bundled-source` is the selected first-release model because both marketplace
  payload roots can carry the Python runner source plus offline metadata.
- `release-asset-download` and `hybrid-manifest-plus-fetch` are not
  XPLAT runtime models. They may be unrelated release repair flows only and must
  not support pure-Python XPLAT claims.
- A Claude plugin `bin/` launcher does not prove Codex launch support. Codex
  launch evidence must use a documented Codex surface such as skill scripts,
  plugin-bundled hooks, or plugin-bundled MCP commands.
- XPLAT-007 source-to-dist evidence must fail when source runner files or metadata
  exist but are missing, stale, unequal, or non-executable in either generated
  payload root for a claimed platform.

## Pinned Release Input Evidence

Records the exact build and release inputs XPLAT-004 must capture before runner foundation files can be accepted.

| Field | Required | Notes |
|---|---|---|
| `runtime_shape` | Yes | Selected runtime shape, currently `python-stdlib-runner`. |
| `python_minimum_version` | Yes | Minimum supported Python version, currently `3.11`. |
| `python_discovery_order` | Yes | Ordered interpreter lookup such as `py -3.11`, `python3`, then `python`, subject to XPLAT-004 validation. |
| `specify_discovery` | Yes | How the runner finds and validates the official `specify` command. |
| `dependency_policy` | Yes | First release is stdlib-only; plugin-only packages require reopening controls. |
| `module_manifest_path` | Conditional | Only required if plugin-only Python packages or a different runtime are introduced. |
| `dependency_snapshot` | Conditional | `none-stdlib-only` for the selected Python runner, or equivalent checksum/snapshot evidence if dependencies are introduced. |
| `target_os_arch_matrix` | Yes | Target platform matrix for preflight and installed-cache launch evidence. |
| `build_command_or_recipe` | Conditional | Packaging or validation recipe used by XPLAT-004. Must not be a native build recipe. |
| `release_package_inputs` | Yes | Files, metadata, and package inputs included in the release artifact boundary. |
| `source_revision` | Yes | Source revision used to package runner files. |
| `runner_source_paths` | Yes | Generated runner source and launcher payload-relative paths. |
| `runner_source_integrity` | Conditional | Checksum or source-integrity metadata where required by XPLAT-004/XPLAT-007. |
| `scan_evidence_refs` | Yes | References to first-release scan evidence that covers the pinned inputs. |

Validation rules:

- Unknown or unverified values are evidence gaps, not accepted controls.
- The evidence record must describe the exact source revision, prerequisite
  boundary, dependency policy, package inputs, and runner files it covers.
- Recording pinned inputs does not implement reproducible builds, SBOMs, signatures, provenance, or formal audit.
- Go/Rust/Zig/native-binary fields are rejected historical analysis and must not
  be carried into XPLAT pinned-input evidence.

## Runner File Manifest

Payload-relative JSON metadata for packaged runner source and launcher files.

Top-level fields:

| Field | Required | Notes |
|---|---|---|
| `schema_version` | Yes | Manifest schema version. |
| `plugin_name` | Yes | Plugin package name. |
| `plugin_version` | Yes | Plugin release version. |
| `runner_name` | Yes | Expected `speckit-pro-runner`. |
| `runner_version` | Yes | Runner source/package version. |
| `contract_version` | Yes | Runner contract version from XPLAT-002. |
| `source_revision` | Yes | Source revision used to package runner files. |
| `checksum_algorithm` | Yes | `sha256` for first release. |
| `runner_files` | Yes | Non-empty list of runner source or launcher file entries. |

Runner file entry fields:

| Field | Required | Notes |
|---|---|---|
| `runner_file_id` | Yes | Stable identifier for the packaged runner file. |
| `payload_path` | Yes | Payload-relative path to the runner source or launcher file. |
| `os` | Conditional | Target operating system only when a file is platform-specific. |
| `arch` | Conditional | Target architecture only when a file is architecture-specific. |
| `size_bytes` | Yes | File size in bytes. |
| `sha256` | Yes | Lowercase SHA-256 hex digest. |
| `checksum_file` | Yes | Payload-relative checksum file path. |

Validation rules:

- `checksum_algorithm` must be `sha256` for first release.
- Each runner file entry must have exactly one matching checksum-file entry when
  checksum metadata is required.
- `payload_path` and `checksum_file` must be payload-relative, not absolute.
- Manifest presence does not imply signing, provenance, SBOM, or trust-chain verification.

## Checksum Entry

One line in `scripts/speckit-pro-runner.sha256`.

| Field | Required | Notes |
|---|---|---|
| `sha256` | Yes | 64 lowercase hexadecimal characters. |
| `separator` | Yes | Two spaces between digest and path. |
| `payload_path` | Yes | Payload-relative runner source or launcher path. |

Validation rules:

- Entries use common SHA-256 checksum file format: `<64 lowercase hex><two spaces><payload-relative path>`.
- The checksum file must include every packaged runner source or launcher file
  covered by the integrity claim and no stale paths.
- Consumers must be able to verify with a Python standard-library SHA-256
  command shape. OS-native SHA-256 tools may be supplemental only.

## Runtime Integrity Evidence

Additional runtime-info/preflight fields required for consumer verification.

| Field | Required | Notes |
|---|---|---|
| `runner_path` | Yes | Typed path to the running or inspected runner source or launcher file. |
| `runner_file_id` | Yes | Matches manifest runner file entry when running from a packaged file. |
| `runner_manifest_path` | Yes | Payload-relative or typed path to manifest. |
| `checksum_file_path` | Yes | Payload-relative or typed path to checksum file. |
| `checksum_algorithm` | Yes | `sha256` for first release. |
| `expected_checksum` | Yes | Expected digest from checksum metadata when available. |
| `verification_status` | Yes | `verified`, `mismatch`, `missing_metadata`, `source_only_context`, or `not_checked`. |
| `source_vs_installed_context` | Yes | Distinguishes installed cache from source-only context. |

Validation rules:

- Installed-cache context and source-only context must be distinct.
- The runner must not claim external trust-chain verification.
- Consumer docs must not rely on runner self-verification alone.

## Consumer Verification Guidance

Downstream XPLAT-007 guidance requirements for local checksum verification after
platform UAT and before public release claims.

| Field | Required | Notes |
|---|---|---|
| `target_platform` | Yes | Windows, macOS, Linux, or a narrower runner file target. |
| `sha256_command_shape` | Yes | Python standard-library command shape for hashing the installed runner file, using the preflight-discovered interpreter where possible. |
| `runner_path_source` | Yes | How the consumer locates the installed runner file path from preflight/runtime-info or documented payload-relative paths. |
| `checksum_metadata_source` | Yes | Installed payload path or release-provided offline metadata path. |
| `comparison_rule` | Yes | How computed and expected hashes are compared. |
| `unavailable_state` | Yes | Closed failure state when runner file or checksum metadata is missing. |
| `mismatch_state` | Yes | Closed failure state when the computed checksum differs from the expected checksum. |
| `mismatch_remediation` | Yes | Consumer-facing stop-use/report guidance for a checksum mismatch. |
| `reporting_fields` | Yes | Runner file path, platform, preflight or identity output, metadata source, expected checksum, computed checksum, plugin version or release boundary, and reporting path. |
| `prohibited_remediation` | Yes | Disallowed instructions such as source checkout repair, package restoration, network fetches, Bash, `jq`, PowerShell helper scripts, or runner self-verification alone. |
| `maintainer_reacceptance_rule` | Yes | Fresh XPLAT-004 and XPLAT-007 evidence required before accepting the affected runner file again. |
| `native_uat_evidence_ref` | Yes | Evidence required before the platform guidance becomes public support wording. |

Validation rules:

- Guidance must include separate command shapes for each target platform or
  platform-specific runner file that XPLAT-007 intends to claim after UAT.
- Guidance must not require Bash, `jq`, PowerShell helper scripts, a source checkout, package-manager restoration, or network access after plugin cache population.
- Guidance must fail closed when metadata is unavailable or when the computed checksum does not match the expected checksum, and must not imply native support before XPLAT-007 UAT evidence exists.
- Mismatch remediation must tell consumers not to rely on the runner file for support claims and must collect enough facts for maintainer investigation without asking consumers to repair the runner file locally.

## Runner File Claim Readiness

Represents per-runner-file and per-platform readiness for public claims.

| Field | Required | Notes |
|---|---|---|
| `runner_file_id` | Yes | Matches the runner source manifest entry. |
| `target_platform` | Yes | Platform or OS/architecture target covered by the claim. |
| `payload_path` | Yes | Payload-relative runner source or launcher path. |
| `claim_status` | Yes | `claimable`, `not_claimable`, `deferred`, or `blocked`. |
| `publication_status` | Yes | `published`, `unpublished`, or `excluded`. |
| `required_evidence_status` | Yes | Per-runner-file status for checksum or source-integrity metadata, manifest, preflight/runtime-info, platform UAT, source-to-dist, scan, exception, release-automation, and public-claim audit evidence. |
| `blockers` | Yes | Missing, stale, mismatched, unpublished, or unsupported evidence that blocks the claim. |
| `owner_surface` | Yes | XPLAT-004, XPLAT-007, release automation, or docs/release notes owner. |
| `follow_up` | Conditional | Required when the runner file/platform is deferred, excluded, or blocked. |

Validation rules:

- A public claim is valid only when every runner file/platform in the claim set is `claimable`.
- One ready runner file/platform does not imply support for any other platform.
- Missing, stale, mismatched, unpublished, or unsupported evidence must either exclude that runner file/platform from claims or block the claim set.

## Generated Payload Evidence

Records source-to-dist integrity for generated Claude/Codex payloads.

| Field | Required | Notes |
|---|---|---|
| `command` | Yes | Expected first-release command: Python standard-library payload builder, for example `python3 scripts/build_plugin_payloads.py`. The current Bash builder is transitional only. |
| `exit_status` | Yes | Numeric command status. |
| `source_inputs` | Yes | Source roots used to generate payloads. |
| `generated_roots` | Yes | Generated roots checked for drift. |
| `marketplace_manifests` | Yes | Marketplace manifests checked for drift. |
| `checksum_manifest_paths` | Yes | Checksum and runner manifest paths considered by the gate. |
| `metadata_flow` | Yes | Producer, source, generated Claude, and generated Codex metadata path mapping. |
| `equality_rule` | Yes | How source and generated checksum/manifest metadata equivalence is verified. |
| `freshness_rule` | Yes | How metadata is tied to current artifact IDs, versions, platforms, source revision, and checksums. |
| `drift_result` | Yes | `clean` or `drift_detected`. |
| `recorded_at` | Yes | Evidence timestamp or release boundary. |

Validation rules:

- XPLAT-007 owns this evidence before public cutover.
- Evidence must cover `dist/claude/speckit-pro`, `dist/codex/speckit-pro`, `.claude-plugin/marketplace.json`, and `.agents/plugins/marketplace.json`.
- Evidence must prove checksum and runner manifest metadata is present, equal, and fresh across source paths and both generated payload roots.
- Missing, stale, or unequal metadata fails XPLAT-007 public cutover and release-claim readiness.
- XPLAT-003 must not run a payload rebuild as an implementation action.

## Python Gate Evidence

Records that an active build, test, eval, payload, or release-readiness gate for
shipped plugin behavior has a Python standard-library implementation before
XPLAT-007 cutover.

| Field | Required | Notes |
|---|---|---|
| `gate_id` | Yes | Stable gate identifier, for example `layer4-helper-tests` or `payload-builder`. |
| `gate_type` | Yes | `build`, `test`, `eval`, `payload`, `release-readiness`, or `uat-support`. |
| `python_command` | Yes | Python standard-library command that runs the gate. |
| `replaced_bash_paths` | Yes | Bash scripts or shell command paths removed from the active gate. |
| `covered_plugin_behavior` | Yes | Shipped plugin behavior validated or published by the gate. |
| `parity_evidence_ref` | Conditional | Required when the gate replaces an existing Bash behavior with parity expectations. |
| `platform_matrix` | Yes | Windows, macOS, Linux, or narrower matrix the gate supports. |
| `release_gate_status` | Yes | `active`, `blocked`, `temporary_parity_only`, or `historical_archive_only`. |
| `prohibited_runtime_dependencies` | Yes | Must include Bash, `jq`, Git Bash, WSL, PowerShell helper scripts, and package restoration unless explicitly out of shipped-behavior scope. |

Validation rules:

- XPLAT-007 cannot pass while a shipped-behavior gate is Bash-only.
- Temporary Bash parity evidence must be outside the final release gate.
- Unrelated shell wrappers may remain only when they dispatch to Python gates and
  contain no validation or payload publication logic.

## Release Automation Acceptance Evidence

Records when a release-automation-owned publication control is actually implemented and allowed to support public claims.

| Field | Required | Notes |
|---|---|---|
| `control_id` | Yes | Release automation control being accepted. |
| `implementing_surface` | Yes | Downstream spec, workflow, or release surface that implements the control. |
| `publication_gate_location` | Yes | Workflow, release step, or release-readiness artifact where the gate is enforced. |
| `release_inputs` | Yes | Inputs covered by the automation gate. |
| `generated_outputs` | Yes | Outputs or artifacts produced or verified by the gate. |
| `latest_pass_fail_evidence` | Yes | Current pass/fail evidence and timestamp or release boundary. |
| `claim_dependency_mapping` | Yes | Public claims that rely on this automation evidence. |
| `status` | Yes | `accepted`, `blocked`, or `assigned_not_implemented`. |

Validation rules:

- Assigned release automation controls are `assigned_not_implemented` until this evidence exists.
- Public claims that depend on release automation are not claimable when evidence is missing, stale, or not wired into the publication path.
- XPLAT-003 may define this record shape but must not edit release workflows.

## Vulnerability Scan Evidence

Release-readiness summary for runner/source/runner-file or cutover trust boundaries.

| Field | Required | Notes |
|---|---|---|
| `scanner` | Yes | Tool or source name. |
| `scanner_version_or_db_timestamp` | Yes | Tool version or vulnerability database timestamp. |
| `scan_target` | Yes | Source, runner file, generated payload, manifest, or release evidence target. |
| `runner_file_or_dependency_policy` | Conditional | Required when finding affects a concrete runner file or dependency policy. |
| `target_source_revision` | Yes | Source revision the scan covers. |
| `dependency_snapshot` | Conditional | Required for source/module/dependency scans. |
| `build_input_snapshot` | Conditional | Required when scan evidence covers build or release inputs. |
| `generated_runner_file_identifier` | Conditional | Required when scan evidence covers a concrete generated runner file. |
| `run_timestamp` | Yes | When the scan evidence was produced. |
| `freshness_expiry` | Yes | Expiry timestamp or release boundary for the evidence. |
| `result` | Yes | `pass`, `fail`, or `pass_with_exceptions`. |
| `actionable_high_critical_count` | Yes | Count after actionability classification. |
| `exception_records` | Conditional | Required for non-actionable high/critical findings. |
| `retention_location` | Yes | Durable summary, PR packet, spec artifact, release readiness artifact, or CI artifact. |

Validation rules:

- Missing, stale, or unresolved actionable high/critical evidence fails readiness.
- Evidence is stale when it is older than 7 calendar days at readiness review, predates the source revision, dependency snapshot, build input, generated runner file, scanner version, or vulnerability database timestamp it claims to cover, or crosses a public release boundary without re-approval.
- Raw scanner output is not committed by default.
- Once automation exists, raw output is retained as CI artifacts for 30 days.

## Vulnerability Exception Record

Documents a non-actionable high/critical finding.

| Field | Required | Notes |
|---|---|---|
| `scanner_or_source` | Yes | Scanner/source that reported the finding. |
| `tool_version_or_db_timestamp` | Yes | Current evidence version. |
| `advisory_id` | Conditional | Required when available. |
| `severity` | Yes | Scanner severity or CVSS severity. |
| `affected_runner_file_dependency_policy_version_platform` | Yes | Concrete affected surface. |
| `actionability_classification` | Yes | Why it is not actionable. |
| `rationale` | Yes | Maintainer-readable explanation. |
| `reachability_or_false_positive_evidence` | Yes | Evidence supporting the classification. |
| `compensating_control` | Yes | Mitigation or boundary that prevents release impact. |
| `approving_maintainer` | Yes | Person or role approving the exception. |
| `approval_date` | Yes | Date approved. |
| `expiry_or_review_condition` | Yes | Must expire before each public release or when evidence changes. |

Validation rules:

- Exceptions are not permanent.
- Re-approval requires current scan evidence.
- Changed runner file, dependency policy, platform, scanner/database, advisory status, severity, exploitability, or compensating control immediately invalidates the exception.

## Public Claim Boundary

Classifies release-note/docs wording.

| Field | Required | Notes |
|---|---|---|
| `claim_id` | Yes | Stable identifier. |
| `claim_text_or_pattern` | Yes | Wording or wording family under review. |
| `classification` | Yes | `allowed_after_verification`, `deferred_roadmap_only`, or `forbidden_until_implemented`. |
| `required_evidence` | Conditional | Required for allowed claims. |
| `runner_file_claim_readiness_refs` | Conditional | Required when a claim names platform or runner file availability. |
| `prohibited_terms` | Conditional | Required for forbidden/deferred claims. |
| `owner_surface` | Yes | XPLAT-007, docs, release notes, or marketplace metadata owner. |

Validation rules:

- Allowed claims require implementation and verification evidence.
- Deferred roadmap wording must avoid guarantee language.
- Native support claims require XPLAT-007 native UAT evidence.

## Release-Readiness Evidence

Aggregates evidence at a release boundary.

| Field | Required | Notes |
|---|---|---|
| `release_boundary` | Yes | PR, release candidate, or public release. |
| `retention_location` | Yes | Owning spec, PR packet, release-readiness artifact, release record, or other durable non-sensitive audit location. |
| `evidence_refs` | Yes | Durable references to source evidence, summaries, or external artifact IDs. |
| `recorded_at` | Yes | Evidence timestamp or release boundary timestamp. |
| `source_revision` | Yes | Source revision covered by the evidence. |
| `owner_surface` | Yes | XPLAT-004, XPLAT-007, release automation, docs, or release-note owner. |
| `control_results` | Yes | Control decision IDs and pass/fail/exception status. |
| `runner_file_claim_readiness_refs` | Conditional | Required when release readiness includes platform or runner file claims. |
| `consumer_verification_status` | Yes | Whether guidance and metadata are current. |
| `public_claim_audit_status` | Yes | Whether wording has passed claim-boundary review. |
| `public_claim_audit_refs` | Conditional | Required when public wording or release notes make supply-chain or native support claims. |
| `release_automation_acceptance_status` | Conditional | Required when public claims depend on release automation evidence. |
| `known_gaps` | Yes | Deferred controls or non-claims. |
| `approval_status` | Yes | `ready`, `blocked`, or `ready_with_recorded_exceptions`. |

Validation rules:

- Public cutover cannot be `ready` when any first-release control is missing, stale, or unresolved.
- `ready_with_recorded_exceptions` requires valid exception records.
- Deferred controls must not be described as implemented guarantees.
- Release-readiness and public-claim audit summaries must be durable and non-sensitive; raw logs and large generated artifacts are supporting evidence only and are not committed by default.

## Relationships

- A `Security Control Decision` has one `Owner Assignment`.
- A first-release runner file requires `Pinned Release Input Evidence`.
- A first-release checksum control requires one runner source manifest and one
  or more `Checksum Entry` records when checksum metadata is required.
- `Runtime Integrity Evidence` references the manifest and checksum file.
- `Consumer Verification Guidance` references runtime integrity evidence, checksum metadata, and XPLAT-007 native UAT evidence.
- `Runner File Claim Readiness` references the manifest, checksum entry,
  runtime integrity evidence, generated payload evidence, scan evidence, native
  UAT evidence, release automation evidence, and public claim audit evidence for
  one runner file/platform.
- `Generated Payload Evidence` references generated roots and checksum/manifest paths.
- `Runner File Distribution Evidence` references pinned release inputs, generated payload
  evidence, install completeness evidence, runner source manifest, and checksum
  entries where required.
- `Python Gate Evidence` references generated payload evidence, release-readiness
  evidence, and any parity evidence used to retire Bash gates.
- `Vulnerability Scan Evidence` may include zero or more `Vulnerability Exception Record` records.
- `Public Claim Boundary` consumes runner file claim readiness and release-readiness evidence before wording is allowed.
- `Release-Readiness Evidence` aggregates all first-release control results and runner-file/platform claim readiness records.

## State Transitions

```text
deferred_hardening -> first_release_required
  Allowed only when promotion evidence exists and the owner surface can implement and verify the control.

first_release_required -> ready
  Allowed only when required evidence is present, current, and clean or validly excepted.

ready -> blocked
  Triggered by stale/missing evidence, checksum mismatch, source-to-dist drift, unresolved actionable high/critical finding, expired exception, or unsupported public claim.

explicitly_not_claimed -> allowed_after_verification
  Allowed only after a later spec implements and verifies the control and updates the claim boundary.
```
