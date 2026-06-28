# Contract: Supply-Chain Control and Consumer Verification

This contract defines the evidence shapes XPLAT-004, XPLAT-007, and later release surfaces must implement or verify. It is a planning contract only; XPLAT-003 does not create runner source, launchers, release automation, generated payload updates, or public claims.

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
    "Python from Claude/Codex platform docs alone",
    "Bash",
    "jq",
    "package managers",
    "WSL",
    "Git Bash"
  ],
  "install_surface_distinctions": [
    "Codex plugin skills are not the same as Codex custom-agent TOML registration."
  ],
  "xplat_gate_effect": "Python is allowed only through the official Spec Kit / specify prerequisite boundary and preflight. Do not claim install completeness or native support until required plugin payload, prerequisite, and custom-agent registrations are verified."
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

Selected runtime evidence must identify the Python-only XPLAT runtime boundary:

```json
{
  "runtime_shape": "python-stdlib-runner",
  "build_time_toolchain": null,
  "installed_user_runtime_dependency": "official Spec Kit / specify prerequisite boundary, including Python 3.11+",
  "bundled_runtime_payload": null,
  "official_runtime_guarantee_ref": "https://github.com/github/spec-kit/blob/main/pyproject.toml",
  "post_cache_setup_required": false,
  "prerequisite_diagnostics": "Missing Python 3.11+, specify, runner file, or metadata fails closed with deterministic diagnostics.",
  "claim_effect": "Support claims remain blocked until prerequisite preflight, installed-cache launch, UAT, checksum, manifest, scan, source-to-dist, and claim-audit evidence pass."
}
```

Contract rules:

- First-release support claims require `post_cache_setup_required=false` beyond
  the documented official Spec Kit / `specify` prerequisite boundary.
- Go, Rust, Zig, bundled Node, embedded Python, and native binaries are not
  XPLAT runtime shapes, fallbacks, or compatibility adapters.
- Source scripts that rely on Node, Bash, `jq`, package managers, WSL, Git
  Bash, or network restoration after cache population are not claimable support
  runtimes unless the runtime is officially guaranteed or bundled with matching
  supply-chain controls. Python is allowed only through the official Spec Kit /
  `specify` prerequisite boundary and must be verified by preflight.

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

## Runner File Distribution Evidence Contract

XPLAT-004 and XPLAT-007 must record how selected runner files reach installed
Claude Code and Codex marketplace payloads. For the active runtime, these files
are Python source plus any thin launch metadata:

```json
{
  "runtime_shape": "python-stdlib-runner",
  "distribution_mode": "bundled-source",
  "source_runner_paths": [
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
  "launch_metadata_policy": "The runner is invoked through Python 3.11+ discovered by preflight; any thin launcher contains dispatch only and no Bash or PowerShell helper logic.",
  "checksum_manifest_refs": [
    "scripts/speckit-pro-runner.sha256",
    "scripts/speckit-pro-runner.manifest.json"
  ],
  "official_docs_refs": [
    "https://code.claude.com/docs/en/plugins",
    "https://developers.openai.com/codex/plugins/build"
  ],
  "claim_effect": "Support claims remain blocked until runner files and metadata are present, equal, fresh, launchable through documented platform surfaces, and UAT-verified in both generated payload roots."
}
```

Contract rules:

- First-release no-post-cache-install claims require
  `post_install_download_required=false`.
- `bundled-source` is the selected first-release model.
- `release-asset-download` and `hybrid-manifest-plus-fetch` are not
  XPLAT runtime models. They may be unrelated repair/update flows only and must
  not support pure-Python XPLAT claims.
- Claude Code's documented plugin `bin/` executable surface is Claude evidence
  only. Codex launcher evidence must use documented Codex surfaces such as skill
  scripts, plugin-bundled hooks, or plugin-bundled MCP commands.
- XPLAT-007 source-to-dist evidence must use a Python standard-library payload
  builder and fail if it does not copy the selected runner file paths and
  metadata into both generated marketplace payload roots. The current Bash
  payload builder is transitional only and is not the final release gate.

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
- Go/Rust/Zig/native-binary evidence is rejected historical analysis and must
  not be carried into this contract as an XPLAT alternative.

## Checksum File Contract

First-release runner source and launcher files may use one payload-relative
checksum file when XPLAT-004/XPLAT-007 choose checksum metadata for source
payload integrity:

```text
scripts/speckit-pro-runner.sha256
```

Line format:

```text
<64 lowercase hexadecimal sha256><two spaces><payload-relative runner file path>
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
- A computed checksum that does not match the corresponding entry is a closed verification failure for that runner file and blocks any claim that depends on it until fresh evidence re-accepts the runner file.

## Runner File Manifest Contract

First-release runner source and launcher files must have one payload-relative manifest:

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
  "runner_files": [
    {
      "runner_file_id": "speckit-pro-runner-python-source",
      "payload_path": "scripts/speckit_pro_runner.py",
      "os": null,
      "arch": null,
      "size_bytes": 0,
      "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
      "checksum_file": "scripts/speckit-pro-runner.sha256"
    }
  ]
}
```

Contract rules:

- `runner_files` must be non-empty after XPLAT-004 adds runner files.
- `sha256` must match the corresponding checksum file entry.
- `payload_path` and `checksum_file` must be payload-relative.
- `source_revision` must identify the source used to package the runner file.
- Manifest publication does not satisfy SBOM, provenance, signatures, reproducibility, formal audit, or marketplace-enforced verification.

## Runtime-Info and Preflight Contract Additions

XPLAT-002 already defines runtime-info/preflight. XPLAT-003 requires runner
source-integrity pointers in that evidence when the runner is packaged.

Required additional fields:

```json
{
  "runtime": {
    "runner_path": {
      "kind": "plugin_relative",
      "value": "scripts/speckit_pro_runner.py"
    },
    "runner_file_id": "speckit-pro-runner-python-source",
    "runner_manifest_path": {
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
  "command": "python3 scripts/build_plugin_payloads.py",
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

- `command` must be a Python standard-library command before XPLAT-007 can pass.
  Bash payload-builder output may be retained only as transitional parity
  evidence before final cutover.
- `exit_status` must be `0`.
- `drift_result` must be `clean`.
- Evidence must record source inputs, generated roots, marketplace manifests, and checksum/manifest paths.
- Evidence must record how XPLAT-004-produced checksum and manifest metadata propagates into source, generated Claude, and generated Codex payload roots.
- Metadata must be present, equal, and fresh across source and generated roots before XPLAT-007 cutover passes.
- Missing, stale, or unequal metadata blocks public cutover and release-claim readiness.
- XPLAT-003 does not run the rebuild or update generated payloads.

## Python Build/Test/Eval Gate Evidence Contract

XPLAT-007 must record Python standard-library replacements for active
build/test/eval/payload/release-readiness gates that validate or publish shipped
plugin behavior:

```json
{
  "gate_id": "layer4-helper-tests",
  "gate_type": "test",
  "python_command": "python3 tests/speckit-pro/run_all.py --layer 4",
  "replaced_bash_paths": [
    "tests/speckit-pro/run-all.sh",
    "tests/speckit-pro/layer4-scripts/*.sh"
  ],
  "covered_plugin_behavior": "Helper script JSON output, exit semantics, and fixture behavior for shipped plugin helpers.",
  "parity_evidence_ref": "Bash-vs-Python fixture parity evidence until cutover",
  "platform_matrix": ["windows", "macos", "linux"],
  "release_gate_status": "blocked",
  "prohibited_runtime_dependencies": [
    "Bash",
    "jq",
    "Git Bash",
    "WSL",
    "PowerShell helper scripts",
    "package restoration"
  ]
}
```

Contract rules:

- XPLAT-007 cannot pass while a shipped-behavior build, test, eval, payload, or
  release-readiness gate is Bash-only.
- Temporary Bash parity evidence must be outside the final release gate.
- Unrelated shell wrappers may remain only when they dispatch to Python gates and
  contain no validation, eval, payload publication, or release-readiness logic.
- This contract covers the top-level test runner, Layer 1 structural checks,
  Layer 2/3 eval runners, Layer 4 helper tests, Layer 5 tool scoping, Layer 6
  efficiency checks, Layer 7 integration checks, Layer 8 parity checks, payload
  builders, marketplace/version sync checks, and any UAT-support gate used for
  public release readiness.

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

Runner/source/runner-file and cutover scan evidence must include:

```json
{
  "scanner": "scanner-name",
  "scanner_version_or_db_timestamp": "version-or-db-timestamp",
  "scan_target": "runner-source-or-runner-file",
  "target_source_revision": "git-sha",
  "dependency_snapshot": "none-stdlib-only or equivalent dependency snapshot",
  "build_input_snapshot": "build inputs covered by scan",
  "generated_runner_file_identifier": "runner-file-id-if-applicable",
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
- Evidence is stale immediately when it predates the source revision, dependency snapshot, build input, generated runner file, scanner version, or vulnerability database timestamp it claims to cover.
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
  "affected_runner_file_dependency_policy_version_platform": "runner-file-or-dependency-policy",
  "actionability_classification": "false_positive",
  "rationale": "Finding does not affect shipped runner-file boundary.",
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
- Runner file, dependency policy, platform, scanner version/database, advisory status, severity, exploitability, or compensating control changes.

## Consumer-Local Checksum Guidance Contract

XPLAT-007 must provide Python standard-library command shapes for every runner
file it intends to claim after native UAT passes:

```json
{
  "target_platform": "windows",
  "sha256_command_shape": "<python> -c \"import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())\" <runner-path>",
  "runner_path_source": "runtime-info/preflight runner_path or documented payload-relative path",
  "checksum_metadata_source": "installed payload checksum file or release-provided offline metadata",
  "comparison_rule": "computed lowercase SHA-256 equals matching payload-relative checksum entry",
  "unavailable_state": "verification metadata unavailable",
  "mismatch_state": "verification failed",
  "mismatch_remediation": "Do not rely on the runner file for support claims; record and report the mismatch details.",
  "reporting_fields": [
    "runner_file_path",
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
    "PowerShell helper script requirement",
    "runner self-verification alone"
  ],
  "maintainer_reacceptance_rule": "Fresh XPLAT-004 checksum/manifest/runner-file evidence and XPLAT-007 source-to-dist, claim-audit, and consumer-guidance evidence are required before accepting the affected runner file again.",
  "native_uat_evidence_ref": "XPLAT-007 native UAT evidence"
}
```

Required command shape family:

| Platform | SHA-256 command shape |
|---|---|
| Windows | `<python> -c "import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())" <runner-path>` |
| macOS | `<python> -c "import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())" <runner-path>` |
| Linux | `<python> -c "import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())" <runner-path>` |

Contract rules:

- The `<python>` placeholder must resolve to the preflight-discovered Python
  3.11+ interpreter from the official Spec Kit / `specify` prerequisite
  boundary, or guidance must fail closed.
- OS-native checksum commands may be supplemental cross-checks only; they are
  not the required first-release path.
- Guidance must not require Bash, `jq`, PowerShell helper scripts, a source checkout, package-manager restoration, or network access after plugin cache population.
- Guidance must fail closed when runner-file or checksum metadata is unavailable or when the computed checksum differs from the expected checksum.
- Consumer-facing mismatch remediation must tell users not to rely on the runner file, must identify the facts to record/report, and must not ask consumers to repair the runner file through source checkout, package restoration, network fetches, Bash, `jq`, PowerShell helper scripts, or runner self-verification alone.
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
  "runner_file_claim_readiness_refs": ["speckit-pro-runner-python-source"],
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
