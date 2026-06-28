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

- XPLAT-004 owns runner source, dependency, artifact, preflight/version, checksum, manifest, and applicable scan controls.
- XPLAT-007 owns generated-payload integrity, consumer guidance, native UAT, public claim readiness, and cutover evidence.
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
| `runtime_not_guaranteed` | Yes | Runtime/tool families not guaranteed for all installed plugin hosts, for example Go, Rust, Zig, Node, Python, Bash, `jq`, package managers, WSL, or Git Bash. |
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

Records whether a selected runtime is a build-time toolchain, an installed-user
runtime dependency, a bundled runtime, or a self-contained artifact.

| Field | Required | Notes |
|---|---|---|
| `runtime_shape` | Yes | Examples: `go-native-artifact`, `rust-native-artifact`, `zig-native-artifact`, `bundled-node`, `embedded-python`, `source-script`. |
| `build_time_toolchain` | Conditional | Required when maintainers build artifacts before release. |
| `installed_user_runtime_dependency` | Yes | Runtime the installed user must provide, or `none` for self-contained artifacts. |
| `bundled_runtime_payload` | Conditional | Required when the payload embeds Node, Python, or another runtime. |
| `official_runtime_guarantee_ref` | Conditional | Required when relying on a platform-provided runtime. |
| `post_cache_setup_required` | Yes | Must be `false` for first-release native-support claims. |
| `prerequisite_diagnostics` | Yes | Fail-closed diagnostic behavior when a runtime/executable/prerequisite is missing. |
| `claim_effect` | Yes | Whether public native-support claims are allowed, blocked, or conditional. |

Validation rules:

- First-release native-support claims require `post_cache_setup_required=false`.
- Go, Rust, and Zig are build-time toolchains when maintainers ship executable
  artifacts; they are not user runtime dependencies unless the user is asked to
  build from source.
- Source scripts that require Node, Python, Bash, `jq`, package managers, WSL,
  Git Bash, or network restoration after cache population are not valid for
  first-release native-support claims unless official docs guarantee the runtime
  or the payload bundles it with matching supply-chain controls.

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

## Binary Distribution Evidence

Records how compiled per-platform runner artifacts move from source or release
inputs into installed Claude Code and Codex marketplace payloads.

| Field | Required | Notes |
|---|---|---|
| `runtime_shape` | Yes | Selected runtime shape, for example `go-native-artifact`; conditional until runtime re-approval. |
| `distribution_mode` | Yes | `bundled-all-platforms`, `bundled-current-host`, `release-asset-download`, or `hybrid-manifest-plus-fetch`. |
| `source_artifact_paths` | Yes | Source or release-input paths produced by XPLAT-004. |
| `generated_claude_payload_paths` | Yes | Payload-relative paths under `dist/claude/speckit-pro`. |
| `generated_codex_payload_paths` | Yes | Payload-relative paths under `dist/codex/speckit-pro`. |
| `launcher_surface` | Yes | Documented launch surface such as Claude plugin `bin/`, Codex skill script, Codex plugin-bundled hook, or Codex plugin-bundled MCP command. |
| `post_install_download_required` | Yes | Whether the installed user must download an artifact after marketplace cache population. |
| `executable_permission_policy` | Yes | Unix executable-bit and Windows `.exe` expectations for the generated payload and installed cache. |
| `checksum_manifest_refs` | Yes | Manifest and checksum metadata that cover every generated artifact path. |
| `official_docs_refs` | Yes | Official Claude/Codex docs used to justify the launch and install surface. |
| `claim_effect` | Yes | Whether native-support claims are claimable, blocked, deferred, or require explicit repair/download wording. |

Validation rules:

- `bundled-all-platforms` is the preferred first-release model for
  no-post-cache-install claims because both marketplace payload roots can carry
  all claimed artifacts plus offline metadata.
- `release-asset-download` and `hybrid-manifest-plus-fetch` are not
  self-contained marketplace installs. They require explicit download,
  checksum verification, network/failure handling, and truthful wording before
  any platform claim can rely on them.
- A Claude plugin `bin/` launcher does not prove Codex launch support. Codex
  launch evidence must use a documented Codex surface such as skill scripts,
  plugin-bundled hooks, or plugin-bundled MCP commands.
- XPLAT-007 source-to-dist evidence must fail when source artifacts or metadata
  exist but are missing, stale, unequal, or non-executable in either generated
  payload root for a claimed platform.

## Pinned Release Input Evidence

Records the exact build and release inputs XPLAT-004 must capture before runner foundation artifacts can be accepted.

| Field | Required | Notes |
|---|---|---|
| `runtime_shape` | Yes | Selected runtime shape, for example `go-native-artifact`; conditional until runtime re-approval. |
| `toolchain_name` | Yes | Go, Rust, Zig, bundled Node builder, embedded Python builder, or other selected build toolchain. |
| `toolchain_version` | Yes | Version used to build the runner artifact. |
| `toolchain_source` | Yes | Installation source, distribution, or pinned toolchain reference. |
| `go_toolchain_version` | Conditional | Required only if Go is explicitly re-approved. |
| `go_toolchain_source` | Conditional | Required only if Go is explicitly re-approved. |
| `module_manifest_path` | Yes | Go module manifest path, Cargo manifest, Zig build file, package manifest, or equivalent dependency manifest for the selected runtime shape. |
| `dependency_snapshot` | Yes | `go.sum` state or equivalent dependency checksum/snapshot evidence. |
| `target_os_arch_matrix` | Yes | Target platform matrix for produced artifacts. |
| `build_command_or_recipe` | Yes | Command or repeatable build recipe used by XPLAT-004. |
| `release_package_inputs` | Yes | Files, metadata, and package inputs included in the release artifact boundary. |
| `source_revision` | Yes | Source revision used to build artifacts. |
| `artifact_names_and_paths` | Yes | Generated artifact names and payload-relative paths. |
| `artifact_sha256_checksums` | Yes | SHA-256 checksums for produced artifacts. |
| `scan_evidence_refs` | Yes | References to first-release scan evidence that covers the pinned inputs. |

Validation rules:

- Unknown or unverified values are evidence gaps, not accepted controls.
- The evidence record must describe the exact source revision, dependency snapshot, toolchain, build inputs, and artifacts it covers.
- Recording pinned inputs does not implement reproducible builds, SBOMs, signatures, provenance, or formal audit.
- `go_toolchain_version` and `go_toolchain_source` are required only when Go is
  explicitly re-approved. If the runtime is amended, replace Go-specific fields
  with equivalent toolchain-specific fields instead of carrying stale Go
  evidence forward.

## Runner Artifact Manifest

Payload-relative JSON metadata for packaged native runner artifacts.

Top-level fields:

| Field | Required | Notes |
|---|---|---|
| `schema_version` | Yes | Manifest schema version. |
| `plugin_name` | Yes | Plugin package name. |
| `plugin_version` | Yes | Plugin release version. |
| `runner_name` | Yes | Expected `speckit-pro-runner`. |
| `runner_version` | Yes | Runner artifact version. |
| `contract_version` | Yes | Runner contract version from XPLAT-002. |
| `source_revision` | Yes | Source revision used to build artifacts. |
| `checksum_algorithm` | Yes | `sha256` for first release. |
| `artifacts` | Yes | Non-empty list of artifact entries. |

Artifact entry fields:

| Field | Required | Notes |
|---|---|---|
| `artifact_id` | Yes | Stable identifier for the packaged artifact. |
| `payload_path` | Yes | Payload-relative path to the artifact. |
| `os` | Yes | Target operating system. |
| `arch` | Yes | Target architecture. |
| `size_bytes` | Yes | Artifact size in bytes. |
| `sha256` | Yes | Lowercase SHA-256 hex digest. |
| `checksum_file` | Yes | Payload-relative checksum file path. |

Validation rules:

- `checksum_algorithm` must be `sha256` for first release.
- Each artifact entry must have exactly one matching checksum-file entry.
- `payload_path` and `checksum_file` must be payload-relative, not absolute.
- Manifest presence does not imply signing, provenance, SBOM, or trust-chain verification.

## Checksum Entry

One line in `scripts/speckit-pro-runner.sha256`.

| Field | Required | Notes |
|---|---|---|
| `sha256` | Yes | 64 lowercase hexadecimal characters. |
| `separator` | Yes | Two spaces between digest and path. |
| `payload_path` | Yes | Payload-relative artifact path. |

Validation rules:

- Entries use common SHA-256 checksum file format: `<64 lowercase hex><two spaces><payload-relative path>`.
- The checksum file must include every packaged runner artifact and no stale artifact path.
- Consumers must be able to verify with platform-native SHA-256 tools.

## Runtime Integrity Evidence

Additional runtime-info/preflight fields required for consumer verification.

| Field | Required | Notes |
|---|---|---|
| `executable_path` | Yes | Typed path to the running or inspected executable. |
| `artifact_id` | Yes | Matches manifest artifact entry when running from a packaged artifact. |
| `artifact_manifest_path` | Yes | Payload-relative or typed path to manifest. |
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

Downstream XPLAT-007 guidance requirements for local checksum verification after native UAT and before public release claims.

| Field | Required | Notes |
|---|---|---|
| `target_platform` | Yes | Windows, macOS, Linux, or a narrower artifact target. |
| `sha256_command_shape` | Yes | Platform-native command shape for hashing the installed runner artifact. |
| `runner_path_source` | Yes | How the consumer locates the installed artifact path from preflight/runtime-info or documented payload-relative paths. |
| `checksum_metadata_source` | Yes | Installed payload path or release-provided offline metadata path. |
| `comparison_rule` | Yes | How computed and expected hashes are compared. |
| `unavailable_state` | Yes | Closed failure state when artifact or checksum metadata is missing. |
| `mismatch_state` | Yes | Closed failure state when the computed checksum differs from the expected checksum. |
| `mismatch_remediation` | Yes | Consumer-facing stop-use/report guidance for a checksum mismatch. |
| `reporting_fields` | Yes | Artifact path, platform, preflight or identity output, metadata source, expected checksum, computed checksum, plugin version or release boundary, and reporting path. |
| `prohibited_remediation` | Yes | Disallowed instructions such as source checkout repair, package restoration, network fetches, Bash, `jq`, or runner self-verification alone. |
| `maintainer_reacceptance_rule` | Yes | Fresh XPLAT-004 and XPLAT-007 evidence required before accepting the affected artifact again. |
| `native_uat_evidence_ref` | Yes | Evidence required before the platform guidance becomes public support wording. |

Validation rules:

- Guidance must include separate command shapes for each target platform artifact that XPLAT-007 intends to claim after UAT.
- Guidance must not require Bash, `jq`, a source checkout, package-manager restoration, or network access after plugin cache population.
- Guidance must fail closed when metadata is unavailable or when the computed checksum does not match the expected checksum, and must not imply native support before XPLAT-007 UAT evidence exists.
- Mismatch remediation must tell consumers not to rely on the artifact for native-runner claims and must collect enough facts for maintainer investigation without asking consumers to repair the artifact locally.

## Artifact Claim Readiness

Represents per-artifact and per-platform readiness for public claims.

| Field | Required | Notes |
|---|---|---|
| `artifact_id` | Yes | Matches the runner artifact manifest entry. |
| `target_platform` | Yes | Platform or OS/architecture target covered by the claim. |
| `payload_path` | Yes | Payload-relative artifact path. |
| `claim_status` | Yes | `claimable`, `not_claimable`, `deferred`, or `blocked`. |
| `publication_status` | Yes | `published`, `unpublished`, or `excluded`. |
| `required_evidence_status` | Yes | Per-artifact status for checksum, manifest, preflight/runtime-info, native UAT, source-to-dist, scan, exception, release-automation, and public-claim audit evidence. |
| `blockers` | Yes | Missing, stale, mismatched, unpublished, or unsupported evidence that blocks the claim. |
| `owner_surface` | Yes | XPLAT-004, XPLAT-007, release automation, or docs/release notes owner. |
| `follow_up` | Conditional | Required when the artifact/platform is deferred, excluded, or blocked. |

Validation rules:

- A public claim is valid only when every artifact/platform in the claim set is `claimable`.
- One ready artifact/platform does not imply support for any other platform.
- Missing, stale, mismatched, unpublished, or unsupported evidence must either exclude that artifact/platform from claims or block the claim set.

## Generated Payload Evidence

Records source-to-dist integrity for generated Claude/Codex payloads.

| Field | Required | Notes |
|---|---|---|
| `command` | Yes | Expected first-release command: `bash scripts/build-plugin-payloads.sh`. |
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

Release-readiness summary for runner/source/artifact or cutover trust boundaries.

| Field | Required | Notes |
|---|---|---|
| `scanner` | Yes | Tool or source name. |
| `scanner_version_or_db_timestamp` | Yes | Tool version or vulnerability database timestamp. |
| `scan_target` | Yes | Source, module, artifact, generated payload, manifest, or release evidence target. |
| `artifact_or_dependency` | Conditional | Required when finding affects a concrete artifact or dependency. |
| `target_source_revision` | Yes | Source revision the scan covers. |
| `dependency_snapshot` | Conditional | Required for source/module/dependency scans. |
| `toolchain_build_input_snapshot` | Conditional | Required when scan evidence covers build or release inputs. |
| `generated_artifact_identifier` | Conditional | Required when scan evidence covers a concrete generated artifact. |
| `run_timestamp` | Yes | When the scan evidence was produced. |
| `freshness_expiry` | Yes | Expiry timestamp or release boundary for the evidence. |
| `result` | Yes | `pass`, `fail`, or `pass_with_exceptions`. |
| `actionable_high_critical_count` | Yes | Count after actionability classification. |
| `exception_records` | Conditional | Required for non-actionable high/critical findings. |
| `retention_location` | Yes | Durable summary, PR packet, spec artifact, release readiness artifact, or CI artifact. |

Validation rules:

- Missing, stale, or unresolved actionable high/critical evidence fails readiness.
- Evidence is stale when it is older than 7 calendar days at readiness review, predates the source revision, dependency snapshot, toolchain, build input, generated artifact, scanner version, or vulnerability database timestamp it claims to cover, or crosses a public release boundary without re-approval.
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
| `affected_artifact_dependency_version_platform` | Yes | Concrete affected surface. |
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
- Changed artifact, dependency graph, platform, toolchain, scanner/database, advisory status, severity, exploitability, or compensating control immediately invalidates the exception.

## Public Claim Boundary

Classifies release-note/docs wording.

| Field | Required | Notes |
|---|---|---|
| `claim_id` | Yes | Stable identifier. |
| `claim_text_or_pattern` | Yes | Wording or wording family under review. |
| `classification` | Yes | `allowed_after_verification`, `deferred_roadmap_only`, or `forbidden_until_implemented`. |
| `required_evidence` | Conditional | Required for allowed claims. |
| `artifact_claim_readiness_refs` | Conditional | Required when a claim names platform or artifact availability. |
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
| `artifact_claim_readiness_refs` | Conditional | Required when release readiness includes platform or artifact claims. |
| `consumer_verification_status` | Yes | Whether guidance and metadata are current. |
| `public_claim_audit_status` | Yes | Whether wording has passed claim-boundary review. |
| `public_claim_audit_refs` | Conditional | Required when public wording or release notes make supply-chain or native-runner claims. |
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
- A first-release runner artifact requires `Pinned Release Input Evidence`.
- A first-release checksum control requires one `Runner Artifact Manifest` and one or more `Checksum Entry` records.
- `Runtime Integrity Evidence` references the manifest and checksum file.
- `Consumer Verification Guidance` references runtime integrity evidence, checksum metadata, and XPLAT-007 native UAT evidence.
- `Artifact Claim Readiness` references the manifest, checksum entry, runtime integrity evidence, generated payload evidence, scan evidence, native UAT evidence, release automation evidence, and public claim audit evidence for one artifact/platform.
- `Generated Payload Evidence` references generated roots and checksum/manifest paths.
- `Binary Distribution Evidence` references pinned release inputs, generated
  payload evidence, install completeness evidence, artifact manifest, and
  checksum entries.
- `Vulnerability Scan Evidence` may include zero or more `Vulnerability Exception Record` records.
- `Public Claim Boundary` consumes artifact claim readiness and release-readiness evidence before wording is allowed.
- `Release-Readiness Evidence` aggregates all first-release control results and artifact/platform claim readiness records.

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
