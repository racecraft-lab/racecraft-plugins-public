# Research: Supply-Chain Security and Consumer Trust Model

## Source Inputs

- XPLAT-001 supply-chain rubric: `docs/ai/research/cross-platform-runtime-inventory.md`
- XPLAT-002 runtime decision: `specs/xplat-002-runtime-implementation-options-contract-decision/runtime-decision.md`
- XPLAT-002 handoff: `specs/xplat-002-runtime-implementation-options-contract-decision/handoff.md`
- XPLAT-002 runner contract: `specs/xplat-002-runtime-implementation-options-contract-decision/contracts/speckit-pro-runner-contract.md`
- XPLAT-003 design concept: `docs/ai/specs/.process/XPLAT-003-design-concept.md`
- XPLAT-003 finalized spec: `specs/xplat-003-supply-chain-security-and-consumer-trust-model/spec.md`

## Decision Method

Use the XPLAT-001 supply-chain rubric as a non-scoring template, then apply the XPLAT-002 handoff boundary: Go native binary is selected, no runner exists yet, and XPLAT-003 chooses controls without implementing them.

Controls are classified as:

- **First-release required**: must be implemented and verified before public cutover or claims rely on the native runner.
- **Deferred hardening**: desirable trust hardening that is not required for the first release unless promotion evidence appears.
- **Explicitly not claimed**: guarantees public docs and release notes must not imply before implementation and verification.
- **Out of scope**: implementation work that belongs to a downstream spec or release surface.

## XPLAT-001 Rubric Mapping

| Rubric criterion | XPLAT-003 decision |
|---|---|
| Dependency policy and lockfile discipline | First-release required for Go runner source and release inputs; XPLAT-004 owns concrete Go module/toolchain policy and pinned-input evidence. |
| Generated payload integrity | First-release required; XPLAT-007 owns source-to-dist gate and generated drift evidence. |
| Vulnerability scanning | First-release required; actionable high/critical findings block readiness unless a non-actionable exception record exists. |
| Provenance or attestation options | Deferred hardening; do not claim provenance or attestations until implemented and verified. |
| Checksums/signatures | SHA-256 checksums are first-release required; signatures are deferred hardening. |
| SBOM feasibility | Deferred hardening; keep a future path but do not require an SBOM for first release. |
| Consumer-local verification | First-release required; use runner identity/preflight plus platform-native checksum comparison. |
| Release automation and documentation truthfulness | First-release required as a claim boundary; release workflow edits are out of scope for XPLAT-003. |

## XPLAT-002 Handoff Implications

| Handoff input | XPLAT-003 implication |
|---|---|
| Go native binary selected | Trust model centers on per-platform executable artifacts and their release metadata. |
| No built runner exists | XPLAT-003 cannot validate installed-cache execution; XPLAT-004 must produce artifacts and preflight/version evidence. |
| Installed users receive packaged artifacts | First-release controls must avoid post-cache dependency installation, package restoration, `jq`, Bash, or source checkout requirements. |
| Runtime-info/preflight exists in contract | XPLAT-003 extends the evidence expected from runtime-info/preflight with artifact-integrity pointers. |
| XPLAT-007 owns generated payload cutover | Generated payload source-to-dist evidence and public support claims stay with XPLAT-007. |

## Control Decisions

| Control | Classification | Owner | Rationale | Acceptance gate |
|---|---|---|---|---|
| Pinned Go/release inputs | First-release required | XPLAT-004 | Native artifacts need a stable source, toolchain, module/dependency snapshot, build input, source revision, artifact path, and checksum boundary before checksums mean anything. | Runner readiness fails if pinned input evidence is missing, stale, unknown, or unverified. |
| Generated payload source-to-dist gate | First-release required | XPLAT-007 | Marketplace installs consume generated Claude/Codex payloads; source and dist must reconcile before cutover. | Public cutover fails if rebuild/drift evidence or checksum/manifest metadata propagation evidence is missing, stale, or unequal across source and generated roots. |
| SHA-256 checksum file | First-release required | XPLAT-004 creates; XPLAT-007 verifies/docs | Checksums are the minimum practical artifact integrity control consumers can verify without marketplace enforcement. | Each packaged runner artifact has a matching entry in `scripts/speckit-pro-runner.sha256`. |
| Runner artifact manifest | First-release required | XPLAT-004 creates; XPLAT-007 verifies/docs | Consumers and maintainers need artifact identity, platform, version, source revision, and checksum metadata. | Manifest includes all required top-level and artifact fields. |
| Vulnerability scans | First-release required | XPLAT-004 for runner/source/artifacts; XPLAT-007 for cutover/public readiness | Actionable high/critical findings and stale evidence must block release readiness before native artifacts are publicly claimed. | Readiness fails on missing/stale evidence or unresolved actionable high/critical findings. |
| Vulnerability exceptions | First-release required when used | Owning downstream surface | Non-actionable findings need durable rationale, approval, and expiry to avoid silently weakening the gate. | Exception records include all required fields and expire before each public release or on changed evidence. |
| Runtime-info/preflight artifact-integrity fields | First-release required | XPLAT-004 | Consumer verification starts with identity/preflight evidence and needs pointers to checksum and manifest metadata. | Preflight/runtime-info includes artifact ID, manifest path, checksum path, expected checksum, algorithm, and verification status. |
| Consumer-local verification guide | First-release required | XPLAT-007 | Consumers must be able to verify without `jq`, Bash, source checkout, or network package restoration. | Guidance uses identity/preflight first, then platform-native SHA-256 comparison with Windows, macOS, and Linux command shapes for each target platform artifact claimed after UAT. |
| Public claim audit | First-release required | XPLAT-007 and docs/release surfaces | Public trust depends on avoiding unimplemented guarantees. | Release notes/docs claim only implemented and verified controls. |
| Release automation publication evidence | First-release required when a public claim depends on automation | XPLAT-007 or later release automation surface | Publication-time checks cannot support public trust claims until a downstream surface proves the gate is implemented and wired into the release path. | Claims depending on release automation fail unless current acceptance evidence names the control ID, gate location, release inputs/outputs, pass/fail evidence, and claim dependency mapping. |
| Signatures | Deferred hardening | Future release/security surface | Useful hardening but not required without marketplace/install enforcement or a concrete first-release requirement. | Promote only with implementation, verification, and public-claim need. |
| SBOM | Deferred hardening | Future release/security surface | Useful for dependency transparency but not first-release blocking under the chosen practical baseline. | Promote if consumer/adoption or release automation requires it. |
| Provenance/attestations | Deferred hardening | Future release/security surface | Stronger trust evidence, but no first-release marketplace or automation support is selected here. | Promote if automation can produce/verify it or claims require it. |
| Reproducible builds | Deferred hardening | Future release/security surface | Strong hardening, but first release relies on controlled inputs plus checksums. | Promote with reproducible build process and verification evidence. |
| Formal third-party audit | Deferred hardening | Future governance/security surface | Out of scope for first-release runner foundation. | Promote only through explicit security/governance decision. |
| Marketplace-enforced verification | Explicitly not claimed | Future marketplace/release surface | Current first-release path is manual consumer-local verification. | Do not claim marketplace enforcement until implemented and verified. |
| Cryptographic trust-chain verification | Explicitly not claimed | Future release/security surface | Checksums alone do not provide a cryptographic trust chain. | Do not claim external trust-chain verification. |
| Native Windows/macOS/Linux support | Explicitly not claimed | XPLAT-007 | Native support claims require built artifacts and UAT evidence, which do not exist in XPLAT-003. | Do not claim support before XPLAT-007 UAT passes. |

## Vulnerability Policy

An actionable finding must meet all of these conditions:

- Scanner severity is high/critical, or CVSS is high/critical when available.
- The finding affects the first-release trust boundary: runner source, Go modules/toolchain, build/release inputs, packaged runner artifacts, integrity metadata, generated payloads, marketplace manifests, or release evidence.
- The finding is reachable, shipped, or capable of changing release output or public claims.

Findings may be treated as non-actionable only with an exception record when they are false positives, unreachable, non-shipped, repo-only/test/archive/docs-only, or already mitigated at the artifact boundary.

Scan evidence is stale when it is older than 7 calendar days at readiness review, predates the source revision, dependency manifest or sum state, toolchain, build input, generated artifact, scanner version or vulnerability database timestamp it claims to cover, or crosses a public release boundary without re-approval.

Exception records expire before each public release unless re-approved from current evidence. They expire immediately when the affected artifact, dependency graph, platform, toolchain, scanner version/database, advisory status, severity, exploitability, or compensating control changes.

Durable, non-sensitive summaries and exception records are retained in the owning spec, PR packet, or release-readiness artifact. Raw scanner output is not committed by default; after automation exists, raw output is retained as a 30-day CI artifact unless a scoped/redacted excerpt is required to support an exception.

## Consumer Verification Boundary

The first-release consumer path is:

1. Run runner identity/preflight from the installed plugin payload.
2. Locate the artifact manifest and checksum file from runtime-info/preflight output or documented payload-relative paths.
3. Compute SHA-256 for the installed artifact using platform-native tooling for the target platform, for example Windows `Get-FileHash -Algorithm SHA256`, macOS `/usr/bin/shasum -a 256`, or Linux `sha256sum`.
4. Compare the computed hash to the matching payload-relative entry in `scripts/speckit-pro-runner.sha256`.

This path does not rely on runner self-verification alone and does not require `jq`, Bash, source checkout, or network package restoration. If artifact or checksum metadata is unavailable, guidance must fail closed with an explicit unavailable state rather than instructing consumers to fetch dependencies or clone source.

A computed checksum mismatch is also a closed verification failure. Consumer
guidance should tell users not to rely on the affected artifact for native-runner
claims, record the artifact path, platform, runner identity/preflight output,
metadata source, expected checksum, computed checksum, plugin version or release
boundary, and reporting path, and wait for maintainer remediation backed by
fresh XPLAT-004 and XPLAT-007 evidence. Local source checkout repair, package
restoration, network replacement fetches, Bash, `jq`, and runner
self-verification alone are rejected remediation paths because they would move
trust outside the installed payload and release evidence boundary.

## Public Claim Boundary

Allowed after implementation and verification:

- Packaged native runner artifacts.
- SHA-256 checksum file and artifact manifest.
- Local runner preflight/version plus checksum verification.
- Generated payload source-to-dist gate.
- Vulnerability scanning with no unresolved actionable high/critical findings.

Forbidden until implemented and verified:

- Signed binaries or signatures.
- SBOMs.
- Provenance or attestations.
- Reproducible builds.
- Formal audit or certification.
- Marketplace-enforced verification.
- Cryptographic trust-chain verification.
- Native Windows/macOS/Linux support.

Roadmap wording may describe deferred items as planned or future hardening, but must not state or imply that they are provided, guaranteed, certified, enforced, trusted, or supported today.

Artifact and platform claims are evaluated per claimed artifact. A platform with
complete current evidence may be claimable for that platform only; missing,
stale, mismatched, unpublished, or unsupported artifacts must be excluded from
claims or keep the claim set blocked. One passing artifact does not imply native
Windows/macOS/Linux support for any other platform.

## Result

No deferred control is promoted to first-release required in XPLAT-003. The practical first-release baseline is sufficient for XPLAT-004 and XPLAT-007 planning because it gives every required control an owner, evidence shape, and release-readiness gate while preserving truthful public claims.

Release automation remains assigned but not implemented in XPLAT-003. Any public claim that relies on release automation remains blocked until XPLAT-007 or a later release automation surface records current acceptance evidence.
