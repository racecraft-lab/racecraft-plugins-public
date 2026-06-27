# Contract: Supply-Chain Control and Consumer Verification

This contract defines the evidence shapes XPLAT-004, XPLAT-007, and later release surfaces must implement or verify. It is a planning contract only; XPLAT-003 does not create runner artifacts, release automation, generated payload updates, or public claims.

## Control Decision Record

Every evaluated control uses this shape in downstream planning or release-readiness evidence.

```json
{
  "control_id": "sha256-checksums",
  "classification": "first_release_required",
  "owner_surface": "XPLAT-004",
  "source_trace": ["XPLAT-001 supply-chain rubric", "XPLAT-003 FR-004"],
  "evidence_required": ["scripts/speckit-pro-runner.sha256", "scripts/speckit-pro-runner.manifest.json"],
  "acceptance_gate": "All packaged runner artifacts have matching SHA-256 entries before release readiness passes.",
  "promotion_condition": null,
  "claim_boundary": "Docs may claim SHA-256 checksum verification only after artifacts, checksum file, manifest, and verification guidance exist."
}
```

Required values for `classification`:

- `first_release_required`
- `deferred_hardening`
- `explicitly_not_claimed`
- `out_of_scope`

## Checksum File Contract

First-release runner artifacts must have one payload-relative checksum file:

```text
scripts/speckit-pro-runner.sha256
```

Line format:

```text
<64 lowercase hexadecimal sha256><two spaces><payload-relative artifact path>
```

Example:

```text
0000000000000000000000000000000000000000000000000000000000000000  scripts/speckit-pro-runner
```

Contract rules:

- Use SHA-256 for first release.
- Include every packaged runner artifact.
- Use payload-relative artifact paths.
- Do not use absolute source-checkout paths.
- Do not imply signing, provenance, or trust-chain verification.

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

XPLAT-002 already defines runtime-info/preflight. XPLAT-003 requires artifact-integrity pointers in that evidence when the runner is packaged.

Required additional fields:

```json
{
  "runtime": {
    "executable_path": {
      "kind": "plugin_relative",
      "value": "scripts/speckit-pro-runner"
    },
    "artifact_id": "speckit-pro-runner-darwin-arm64",
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
  "drift_result": "clean"
}
```

Contract rules:

- `exit_status` must be `0`.
- `drift_result` must be `clean`.
- Evidence must record source inputs, generated roots, marketplace manifests, and checksum/manifest paths.
- XPLAT-003 does not run the rebuild or update generated payloads.

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

## Public Claim Audit Contract

Before public docs or release notes claim a supply-chain control, XPLAT-007 or the owning release/docs surface must record:

```json
{
  "claim_id": "sha256-local-verification",
  "surface": "release-notes",
  "claim_text_or_pattern": "Consumers can verify packaged runner artifacts with SHA-256 checksums.",
  "classification": "allowed_after_verification",
  "required_evidence": [
    "runner artifact manifest",
    "checksum file",
    "consumer verification guidance",
    "current release-readiness evidence"
  ],
  "status": "blocked_until_evidence_exists"
}
```

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
