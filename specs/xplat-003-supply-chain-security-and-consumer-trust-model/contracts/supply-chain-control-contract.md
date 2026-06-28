# Contract: Supply-Chain Control and Consumer Verification

This contract defines the evidence shapes XPLAT-004, XPLAT-007, and later release surfaces must implement or verify. It is a planning contract only; XPLAT-003 does not create runner artifacts, release automation, generated payload updates, or public claims.

## Control Decision Record

Every evaluated control uses this shape in downstream planning or release-readiness evidence.

```json
{
  "control_id": "runner-source-integrity",
  "classification": "first_release_required",
  "owner_surface": "XPLAT-004",
  "source_trace": ["XPLAT-001 supply-chain rubric", "XPLAT-003 FR-004"],
  "evidence_required": ["scripts/speckit-pro-runner.sha256", "scripts/speckit-pro-runner.manifest.json"],
  "acceptance_gate": "All packaged runner source and launcher files covered by the integrity claim have matching SHA-256 entries before release readiness passes.",
  "promotion_condition": null,
  "claim_boundary": "Docs may claim runner source verification only after runner files, checksum file, manifest, and verification guidance exist."
}
```

Required values for `classification`:

- `first_release_required`
- `deferred_hardening`
- `explicitly_not_claimed`
- `out_of_scope`

## Platform Capability Evidence Contract

XPLAT-004 and XPLAT-007 must keep official platform capability evidence
separate from runtime/toolchain assumptions:

```json
{
  "platform": "openai-codex",
  "official_docs_refs": [
    "https://developers.openai.com/codex/plugins",
    "https://developers.openai.com/codex/skills",
    "https://developers.openai.com/codex/subagents"
  ],
  "supported_surfaces": [
    "plugin skills",
    "skill scripts",
    "MCP servers",
    "lifecycle hooks",
    "custom agents via .codex/agents/*.toml"
  ],
  "runtime_guarantees": "none_found",
  "runtime_not_guaranteed": [
    "Go",
    "Rust",
    "Zig",
    "Node",
    "Python",
    "Bash",
    "jq",
    "package managers",
    "WSL",
    "Git Bash"
  ],
  "install_surface_distinctions": [
    "Codex plugin skills are not the same as Codex custom-agent TOML registration."
  ],
  "xplat_gate_effect": "Do not claim install completeness or native support until required plugin payload and custom-agent registrations are verified."
}
```

Contract rules:

- Official docs can prove plugin packaging or registration support, but they do
  not prove user-host runtime availability unless they explicitly guarantee that
  runtime for the installed surface.
- Local host probes and repository tooling are supplemental evidence only.
- Codex custom-agent TOML registration must be checked separately from plugin
  skill presence when agents are part of the release promise.

## Runtime Dependency Boundary Contract

Selected runtime evidence must identify whether the runtime is a build-time
toolchain, user dependency, bundled runtime, or self-contained artifact:

```json
{
  "runtime_shape": "go-native-artifact",
  "build_time_toolchain": {
    "name": "go",
    "version": "reported-by-build-environment"
  },
  "installed_user_runtime_dependency": "none",
  "bundled_runtime_payload": null,
  "official_runtime_guarantee_ref": null,
  "post_cache_setup_required": false,
  "prerequisite_diagnostics": "Missing executable or metadata fails closed with deterministic diagnostics.",
  "claim_effect": "Native support claim remains blocked until artifact, installed-cache, UAT, checksum, manifest, scan, source-to-dist, and claim-audit evidence pass."
}
```

Contract rules:

- First-release native-support claims require `post_cache_setup_required=false`.
- Go, Rust, and Zig are user-runtime-free only when maintainers ship
  self-contained per-platform artifacts; users must not be asked to install the
  build toolchain to run the plugin.
- Source scripts that rely on Node, Python, Bash, `jq`, package managers, WSL,
  Git Bash, or network restoration after cache population are not claimable
  native-support runtimes unless the runtime is officially guaranteed or bundled
  with matching supply-chain controls.

## Install Completeness Evidence Contract

XPLAT-007 and install/autoheal flows must record platform-specific install
completeness:

```json
{
  "platform": "openai-codex",
  "plugin_version": "2.16.0",
  "payload_root": "installed Codex plugin cache root",
  "skills_status": "present",
  "scripts_status": "present_and_executable",
  "hooks_status": "present",
  "mcp_status": "not_applicable",
  "agent_registration_status": {
    "scope": ".codex/agents or ~/.codex/agents",
    "required_agents": ["phase-executor", "clarify-executor"],
    "status": "present"
  },
  "autoheal_action": "install or refresh missing TOML agents from the plugin payload when supported",
  "fail_closed_behavior": "Report install incomplete and do not claim full Codex readiness until required agents are present."
}
```

Contract rules:

- Claude Code plugin agents and Codex custom-agent TOML registrations are
  different install surfaces.
- Codex plugin skill installation alone is not a complete install when required
  Codex custom agents are missing.
- Autoheal must repair only documented local install surfaces and must fail
  closed when a required piece cannot be verified.

## Binary Distribution Evidence Contract

XPLAT-004 and XPLAT-007 must record how compiled artifacts reach installed
Claude Code and Codex marketplace payloads:

```json
{
  "runtime_shape": "python-stdlib-runner",
  "distribution_mode": "bundled-source",
  "source_artifact_paths": [
    "speckit-pro/scripts/speckit_pro_runner.py"
  ],
  "generated_claude_payload_paths": [
    "dist/claude/speckit-pro/scripts/speckit_pro_runner.py"
  ],
  "generated_codex_payload_paths": [
    "dist/codex/speckit-pro/scripts/speckit_pro_runner.py"
  ],
  "launcher_surface": {
    "claude-code": "skill or hook dispatches through discovered Python interpreter",
    "openai-codex": "skill script or hook dispatches through discovered Python interpreter"
  },
  "post_install_download_required": false,
  "executable_permission_policy": "Unix artifacts are executable after payload build/install; Windows artifacts use .exe paths.",
  "checksum_manifest_refs": [
    "scripts/speckit-pro-runner.sha256",
    "scripts/speckit-pro-runner.manifest.json"
  ],
  "official_docs_refs": [
    "https://code.claude.com/docs/en/plugins",
    "https://developers.openai.com/codex/plugins/build"
  ],
  "claim_effect": "Native-support claims remain blocked until artifacts and metadata are present, equal, fresh, executable, and UAT-verified in both generated payload roots."
}
```

Contract rules:

- First-release no-post-cache-install claims require
  `post_install_download_required=false`.
- `bundled-all-platforms` is claimable only when every claimed platform
  artifact and its metadata are present in both generated payload roots and the
  installed cache evidence confirms the current host can select the matching
  artifact.
- `release-asset-download` and `hybrid-manifest-plus-fetch` are not
  self-contained marketplace installs. They require explicit download,
  checksum verification before execution, network/failure handling, and public
  wording that does not imply offline installed-cache support.
- Claude Code's documented plugin `bin/` executable surface is Claude evidence
  only. Codex launcher evidence must use documented Codex surfaces such as skill
  scripts, plugin-bundled hooks, or plugin-bundled MCP commands.
- XPLAT-007 source-to-dist evidence must fail if `scripts/build-plugin-payloads.sh`
  does not copy the selected artifact source paths and metadata into both
  generated marketplace payload roots.

## Pinned Release Input Evidence Contract

For the selected Python runner, XPLAT-004 must record this evidence before
accepting the runner foundation:

```json
{
  "runtime_shape": "python-stdlib-runner",
  "python_minimum_version": "3.11",
  "python_discovery_order": ["py -3.11", "python3", "python"],
  "specify_discovery": {
    "required": true,
    "command": "specify",
    "version_probe": "specify --version"
  },
  "dependency_policy": "stdlib-only",
  "module_manifest_path": null,
  "dependency_snapshot": "none-stdlib-only",
  "target_os_arch_matrix": ["darwin/arm64", "linux/amd64", "windows/amd64"],
  "build_command_or_recipe": "payload packaging and validation recipe",
  "release_package_inputs": ["payload-relative input path"],
  "source_revision": "git-sha",
  "runner_source_paths": ["scripts/speckit_pro_runner.py"],
  "runner_source_integrity": ["sha256:<64 lowercase hex>"],
  "scan_evidence_refs": ["release-readiness scan evidence record"]
}
```

Contract rules:

- Unknown or unverified fields are evidence gaps, not accepted controls.
- The record must cover the exact source revision, prerequisite boundary,
  dependency policy, release inputs, and runner files it claims to represent.
- The record does not implement or imply reproducible builds, SBOMs, signatures, provenance, formal audit, marketplace-enforced verification, or native support claims.
- If the runtime decision changes to Go, Rust, Zig, bundled Node, embedded
  Python, or another runtime shape, regenerate this contract for that runtime
  instead of preserving stale Python-specific evidence.

## Checksum File Contract

First-release runner source and launcher files may use one payload-relative
checksum file when XPLAT-004/XPLAT-007 choose checksum metadata for source
payload integrity:

```text
scripts/speckit-pro-runner.sha256
```

Line format:

```text
<64 lowercase hexadecimal sha256><two spaces><payload-relative artifact path>
```

Example:

```text
0000000000000000000000000000000000000000000000000000000000000000  scripts/speckit_pro_runner.py
```

Contract rules:

- Use SHA-256 for first release.
- Include every packaged runner source or launcher file covered by the source
  integrity claim.
- Use payload-relative paths.
- Do not use absolute source-checkout paths.
- Do not imply signing, provenance, or trust-chain verification.
- A computed checksum that does not match the corresponding entry is a closed verification failure for that artifact and blocks any claim that depends on it until fresh evidence re-accepts the artifact.

## Runner Artifact Manifest Contract

First-release runner artifacts must have one payload-relative manifest:

```text
scripts/speckit-pro-runner.manifest.json
```

Required shape:

```json
{
  "schema_version": "1.0",
  "plugin_name": "speckit-pro",
  "plugin_version": "0.0.0",
  "runner_name": "speckit-pro-runner",
  "runner_version": "0.0.0",
  "contract_version": "1.0",
  "source_revision": "git-sha",
  "checksum_algorithm": "sha256",
  "artifacts": [
    {
      "artifact_id": "speckit-pro-runner-darwin-arm64",
      "payload_path": "scripts/speckit-pro-runner",
      "os": "darwin",
      "arch": "arm64",
      "size_bytes": 0,
      "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
      "checksum_file": "scripts/speckit-pro-runner.sha256"
    }
  ]
}
```

Contract rules:

- `artifacts` must be non-empty after XPLAT-004 builds artifacts.
- `sha256` must match the corresponding checksum file entry.
- `payload_path` and `checksum_file` must be payload-relative.
- `source_revision` must identify the source used to build the artifact.
- Manifest publication does not satisfy SBOM, provenance, signatures, reproducibility, formal audit, or marketplace-enforced verification.

## Runtime-Info and Preflight Contract Additions

XPLAT-002 already defines runtime-info/preflight. XPLAT-003 requires runner
source-integrity pointers in that evidence when the runner is packaged.

Required additional fields:

```json
{
  "runtime": {
    "executable_path": {
      "kind": "plugin_relative",
      "value": "scripts/speckit_pro_runner.py"
    },
    "runner_file_id": "speckit-pro-runner-python-source",
    "artifact_manifest_path": {
      "kind": "plugin_relative",
      "value": "scripts/speckit-pro-runner.manifest.json"
    },
    "checksum_file_path": {
      "kind": "plugin_relative",
      "value": "scripts/speckit-pro-runner.sha256"
    },
    "checksum_algorithm": "sha256",
    "expected_checksum": "0000000000000000000000000000000000000000000000000000000000000000",
    "verification_status": "not_checked",
    "source_vs_installed_context": "installed_plugin_cache"
  }
}
```

Allowed `verification_status` values:

- `verified`
- `mismatch`
- `missing_metadata`
- `source_only_context`
- `not_checked`

Contract rules:

- Installed-cache and source-only contexts must be distinguishable.
- Consumer guidance must not rely on runner self-verification alone.
- Runtime-info/preflight must not claim external cryptographic trust-chain verification.

## Generated Payload Source-to-Dist Evidence Contract

XPLAT-007 owns this evidence before public cutover. The first-release evidence record must include:

```json
{
  "command": "bash scripts/build-plugin-payloads.sh",
  "exit_status": 0,
  "source_inputs": ["speckit-pro"],
  "generated_roots": [
    "dist/claude/speckit-pro",
    "dist/codex/speckit-pro"
  ],
  "marketplace_manifests": [
    ".claude-plugin/marketplace.json",
    ".agents/plugins/marketplace.json"
  ],
  "checksum_manifest_paths": [
    "scripts/speckit-pro-runner.sha256",
    "scripts/speckit-pro-runner.manifest.json"
  ],
  "metadata_flow": {
    "producer_spec": "XPLAT-004",
    "producer_outputs": [
      "scripts/speckit-pro-runner.sha256",
      "scripts/speckit-pro-runner.manifest.json"
    ],
    "source_metadata_paths": [
      "speckit-pro/scripts/speckit-pro-runner.sha256",
      "speckit-pro/scripts/speckit-pro-runner.manifest.json"
    ],
    "generated_claude_metadata_paths": [
      "dist/claude/speckit-pro/scripts/speckit-pro-runner.sha256",
      "dist/claude/speckit-pro/scripts/speckit-pro-runner.manifest.json"
    ],
    "generated_codex_metadata_paths": [
      "dist/codex/speckit-pro/scripts/speckit-pro-runner.sha256",
      "dist/codex/speckit-pro/scripts/speckit-pro-runner.manifest.json"
    ],
    "equality_rule": "source and generated metadata are byte-identical or have a documented canonical digest match",
    "freshness_rule": "metadata covers the current artifact IDs, versions, platforms, source revision, and checksums",
    "failure_rule": "missing, stale, or unequal metadata fails XPLAT-007 public cutover"
  },
  "drift_result": "clean"
}
```

Contract rules:

- `exit_status` must be `0`.
- `drift_result` must be `clean`.
- Evidence must record source inputs, generated roots, marketplace manifests, and checksum/manifest paths.
- Evidence must record how XPLAT-004-produced checksum and manifest metadata propagates into source, generated Claude, and generated Codex payload roots.
- Metadata must be present, equal, and fresh across source and generated roots before XPLAT-007 cutover passes.
- Missing, stale, or unequal metadata blocks public cutover and release-claim readiness.
- XPLAT-003 does not run the rebuild or update generated payloads.

## Release Automation Acceptance Contract

Release automation controls are assigned but not implemented by XPLAT-003. Any public claim that depends on release automation evidence must use this acceptance record before it becomes claimable:

```json
{
  "control_id": "publication-time-checksum-verification",
  "implementing_surface": "XPLAT-007 or later release automation spec",
  "publication_gate_location": ".github/workflows/release.yml or release-readiness artifact",
  "release_inputs": ["runner source manifest", "checksum file", "source-to-dist evidence"],
  "generated_outputs": ["release readiness summary"],
  "latest_pass_fail_evidence": "pass evidence with timestamp or release boundary",
  "claim_dependency_mapping": [
    "sha256-local-verification"
  ],
  "status": "accepted"
}
```

Contract rules:

- `status` is `assigned_not_implemented` until the downstream implementing surface records current pass/fail evidence.
- Public cutover and release claims fail when a claim depends on release automation whose acceptance evidence is missing, stale, or not wired into the publication path.
- This contract does not authorize XPLAT-003 to edit release workflows.

## Scan Evidence Freshness Contract

Runner/source/artifact and cutover scan evidence must include:

```json
{
  "scanner": "scanner-name",
  "scanner_version_or_db_timestamp": "version-or-db-timestamp",
  "scan_target": "runner-source-or-artifact",
  "target_source_revision": "git-sha",
  "dependency_snapshot": "go.sum or equivalent dependency snapshot",
  "toolchain_build_input_snapshot": "toolchain and build inputs covered by scan",
  "generated_artifact_identifier": "artifact-id-if-applicable",
  "run_timestamp": "YYYY-MM-DDTHH:MM:SSZ",
  "freshness_expiry": "YYYY-MM-DDTHH:MM:SSZ or release-boundary",
  "result": "pass",
  "actionable_high_critical_count": 0,
  "exception_records": [],
  "retention_location": "spec, PR packet, release readiness artifact, or CI artifact"
}
```

Contract rules:

- Readiness fails when required scan evidence is missing, stale, or has unresolved actionable high/critical findings.
- Evidence is stale when it is older than 7 calendar days at readiness review.
- Evidence is stale immediately when it predates the source revision, dependency snapshot, toolchain, build input, generated artifact, scanner version, or vulnerability database timestamp it claims to cover.
- Evidence must be re-approved at each public release boundary.
- XPLAT-003 records this policy only and does not implement scanner automation.

## Vulnerability Exception Contract

Use this shape only for non-actionable high/critical findings. Unresolved actionable high/critical findings block readiness.

```json
{
  "scanner_or_source": "scanner-name",
  "tool_version_or_db_timestamp": "version-or-db-timestamp",
  "advisory_id": "CVE-or-advisory-if-available",
  "severity": "high",
  "affected_artifact_dependency_version_platform": "artifact-or-dependency",
  "actionability_classification": "false_positive",
  "rationale": "Finding does not affect shipped artifact boundary.",
  "reachability_or_false_positive_evidence": "Evidence summary.",
  "compensating_control": "Boundary or mitigation summary.",
  "approving_maintainer": "maintainer-or-role",
  "approval_date": "YYYY-MM-DD",
  "expiry_or_review_condition": "Expires before the next public release or immediately when evidence inputs change."
}
```

Required actionability criteria for blocking findings:

- High/critical scanner severity or high/critical CVSS when available.
- First-release trust-boundary scope.
- Reachable, shipped, or capable of changing release output or public claims.

Exception expiry triggers:

- Each public release boundary.
- Artifact, dependency graph, platform, toolchain, scanner version/database, advisory status, severity, exploitability, or compensating control changes.

## Consumer-Local Checksum Guidance Contract

XPLAT-007 must provide platform-specific command shapes for every platform artifact it intends to claim after native UAT passes:

```json
{
  "target_platform": "windows",
  "sha256_command_shape": "Get-FileHash -Algorithm SHA256 <runner-path>",
  "runner_path_source": "runtime-info/preflight executable_path or documented payload-relative path",
  "checksum_metadata_source": "installed payload checksum file or release-provided offline metadata",
  "comparison_rule": "computed lowercase SHA-256 equals matching payload-relative checksum entry",
  "unavailable_state": "verification metadata unavailable",
  "mismatch_state": "verification failed",
  "mismatch_remediation": "Do not rely on the artifact for native-runner claims; record and report the mismatch details.",
  "reporting_fields": [
    "artifact_path",
    "target_platform",
    "runner_identity_or_preflight_output",
    "checksum_metadata_source",
    "expected_checksum",
    "computed_checksum",
    "plugin_version_or_release_boundary",
    "reporting_path"
  ],
  "prohibited_remediation": [
    "source checkout repair",
    "package restoration",
    "network replacement fetch",
    "Bash or jq requirement",
    "runner self-verification alone"
  ],
  "maintainer_reacceptance_rule": "Fresh XPLAT-004 checksum/manifest/artifact evidence and XPLAT-007 source-to-dist, claim-audit, and consumer-guidance evidence are required before accepting the affected artifact again.",
  "native_uat_evidence_ref": "XPLAT-007 native UAT evidence"
}
```

Required command shapes:

| Platform | SHA-256 command shape |
|---|---|
| Windows | `Get-FileHash -Algorithm SHA256 <runner-path>` |
| macOS | `/usr/bin/shasum -a 256 <runner-path>` |
| Linux | `sha256sum <runner-path>` |

Contract rules:

- Guidance must not require Bash, `jq`, a source checkout, package-manager restoration, or network access after plugin cache population.
- Guidance must fail closed when artifact or checksum metadata is unavailable or when the computed checksum differs from the expected checksum.
- Consumer-facing mismatch remediation must tell users not to rely on the artifact, must identify the facts to record/report, and must not ask consumers to repair the artifact through source checkout, package restoration, network fetches, Bash, `jq`, or runner self-verification alone.
- Command shapes are downstream guidance requirements, not current public native-support claims.

## Runner File Claim Readiness Contract

XPLAT-007 must evaluate public cutover and release claims per claimed runner
file and platform:

```json
{
  "runner_file_id": "speckit-pro-runner-python-source",
  "target_platform": "windows/amd64",
  "payload_path": "scripts/speckit_pro_runner.py",
  "claim_status": "blocked",
  "publication_status": "unpublished",
  "required_evidence_status": {
    "checksum": "missing",
    "manifest": "current",
    "runtime_preflight": "missing",
    "native_uat": "missing",
    "source_to_dist": "current",
    "scan": "current",
    "exception": "not_applicable",
    "release_automation": "assigned_not_implemented",
    "public_claim_audit": "blocked"
  },
  "blockers": ["source integrity missing", "native UAT missing"],
  "owner_surface": "XPLAT-007",
  "follow_up": "Exclude this runner file/platform from public claims or keep the claim set blocked."
}
```

Contract rules:

- A public claim is valid only when every runner file/platform in the claim set is `claimable`.
- A missing, stale, mismatched, unpublished, or unsupported claimed runner file blocks the claim set unless that runner file/platform is explicitly excluded or deferred.
- One claimable runner file/platform does not imply native support for any other platform.
- Unclaimed or deferred platforms must be recorded as `not_claimable`, `deferred`, `excluded`, or `blocked`, not silently omitted from the claim audit.

## Release-Readiness and Public-Claim Audit Retention Contract

Durable release-readiness and public-claim audit summaries must use this shape
or an equivalent release artifact:

```json
{
  "release_boundary": "release-candidate-or-public-release",
  "control_or_claim_ids": ["runner-source-local-verification"],
  "evidence_refs": ["runner source manifest", "checksum file", "source-to-dist evidence"],
  "artifact_claim_readiness_refs": ["speckit-pro-runner-python-source"],
  "status": "blocked",
  "recorded_at": "YYYY-MM-DDTHH:MM:SSZ",
  "source_revision": "git-sha",
  "owner_surface": "XPLAT-007",
  "known_gaps": ["native UAT missing"],
  "approval_status": "blocked",
  "retention_location": "spec, PR packet, release-readiness artifact, release record, or durable release artifact"
}
```

Contract rules:

- Durable summaries must be non-sensitive and retained in an owning spec, PR packet, release-readiness artifact, release record, or durable release artifact.
- Raw logs, raw scanner output, and large generated artifacts are not committed by default and may support but not replace the durable summary.
- Public claims cannot rely on evidence that exists only in expiring logs or unretained generated artifacts.

## Public Claim Audit Contract

Before public docs or release notes claim a supply-chain control, XPLAT-007 or the owning release/docs surface must record:

```json
{
  "claim_id": "runner-source-local-verification",
  "surface": "release-notes",
  "claim_text_or_pattern": "Consumers can verify packaged runner source files with SHA-256 checksums.",
  "classification": "allowed_after_verification",
  "required_evidence": [
    "runner source manifest",
    "checksum file",
    "consumer verification guidance",
    "runner file claim readiness",
    "current release-readiness evidence"
  ],
  "status": "blocked_until_evidence_exists",
  "retention_location": "release-readiness artifact or release record"
}
```

Contract rules:

- Public claim audit records must reference the retained release-readiness evidence and runner file claim readiness records that make the claim true.
- Platform or native-support wording is allowed only for runner-file/platform records with `claim_status: claimable`.
- Claims remain blocked when release-readiness or public-claim audit evidence exists only in expiring logs or unretained generated artifacts.

Claims that remain forbidden until implemented and verified:

- Signed binaries or signatures.
- SBOMs.
- Provenance or attestations.
- Reproducible builds.
- Formal audit or certification.
- Marketplace-enforced verification.
- Cryptographic trust-chain verification.
- Native Windows/macOS/Linux support.

Roadmap language may identify these as future or deferred hardening. It must not describe them as provided, guaranteed, certified, enforced, trusted, or supported today.
