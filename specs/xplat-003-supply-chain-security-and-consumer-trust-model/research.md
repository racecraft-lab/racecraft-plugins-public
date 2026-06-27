# Research: Supply-Chain Security and Consumer Trust Model

## Source Inputs

- XPLAT-001 supply-chain rubric: `docs/ai/research/cross-platform-runtime-inventory.md`
- XPLAT-002 runtime decision: `specs/xplat-002-runtime-implementation-options-contract-decision/runtime-decision.md`
- XPLAT-002 handoff: `specs/xplat-002-runtime-implementation-options-contract-decision/handoff.md`
- XPLAT-002 runner contract: `specs/xplat-002-runtime-implementation-options-contract-decision/contracts/speckit-pro-runner-contract.md`
- XPLAT-003 design concept: `docs/ai/specs/.process/XPLAT-003-design-concept.md`
- XPLAT-003 finalized spec: `specs/xplat-003-supply-chain-security-and-consumer-trust-model/spec.md`
- Official Claude Code plugin docs: `https://code.claude.com/docs/en/plugins`
- Official Claude Code plugin reference: `https://code.claude.com/docs/en/plugins-reference`
- Official Claude Code skills docs: `https://docs.anthropic.com/en/docs/claude-code/skills`
- Official OpenAI Codex plugin docs: `https://developers.openai.com/codex/plugins`
- Official OpenAI Codex plugin build docs: `https://developers.openai.com/codex/plugins/build`
- Official OpenAI Codex skills docs: `https://developers.openai.com/codex/skills`
- Official OpenAI Codex hooks docs: `https://developers.openai.com/codex/hooks`
- Official OpenAI Codex MCP docs: `https://developers.openai.com/codex/mcp`
- Official OpenAI Codex subagents docs: `https://developers.openai.com/codex/subagents`

## Decision Method

Use the XPLAT-001 supply-chain rubric as a non-scoring template, then apply the XPLAT-002 handoff boundary as conditional source evidence: XPLAT-002 currently records Go native binary as selected, no runner exists yet, and XPLAT-003 chooses controls without implementing them. The runtime choice has been reopened for explicit maintainer re-approval on this PR, so Go-specific conclusions below are conditional until that decision is re-approved or amended.

Controls are classified as:

- **First-release required**: must be implemented and verified before public cutover or claims rely on the native runner.
- **Deferred hardening**: desirable trust hardening that is not required for the first release unless promotion evidence appears.
- **Explicitly not claimed**: guarantees public docs and release notes must not imply before implementation and verification.
- **Out of scope**: implementation work that belongs to a downstream spec or release surface.

Platform documentation evidence is used only for what each product officially
packages or registers. Runtime availability is not inferred from a local host
probe or from the existence of plugin `scripts/` support.

## Official Platform Documentation Findings

| Platform surface | Officially supported package/registration surface | Runtime implication for XPLAT |
|---|---|---|
| Claude Code plugins | Plugins can package skills, agents, hooks, MCP configuration, scripts, and `bin/` executables. Plugin `bin/` executables are exposed for plugin use while enabled. | Claude packaging supports executable/script payloads, but the docs do not guarantee Go, Rust, Zig, Node, Python, Bash, `jq`, or package managers on every user host. |
| Claude Code skills | Skills can include `SKILL.md` plus optional scripts, references, and assets. | Skill scripts are supported as packaged resources, but the script runtime remains a host or bundled-artifact concern. |
| OpenAI Codex plugins | Plugins can package skills, apps, MCP servers, lifecycle hooks, and install payloads. Hooks expose plugin root/data context to command scripts. | Codex packaging supports plugin script and MCP command surfaces, but the docs do not guarantee arbitrary language runtimes after install. |
| OpenAI Codex skills | Skills can include optional `scripts/`, references, and assets. | Codex skill scripts are supported as resources, but runtime availability still must be guaranteed, bundled, or diagnosed. |
| OpenAI Codex subagents | Custom subagents are documented as TOML files in `.codex/agents/` or `~/.codex/agents/`. | Codex install completeness cannot be inferred from plugin skill presence alone; required custom-agent TOML registrations must be validated or autohealed separately. |

Decision effect: official docs support a plugin-payload delivery model for
scripts and executables, but they do not select a runtime. A first-release
runtime must therefore either ship self-contained per-platform artifacts or
have explicit prerequisite diagnostics and no public native-support claim when
the runtime is absent.

## Runtime Candidate Reopen Implications

| Runtime shape | User install impact | XPLAT-003 consequence |
|---|---|---|
| Go native artifact | Users do not install Go if maintainers build and ship per-platform executables. | Current controls remain applicable only if Go is explicitly re-approved. Go module/toolchain evidence remains a build-time/release concern. |
| Rust native artifact | Users do not install Rust if maintainers build and ship per-platform executables. | Viable same runtime model, but XPLAT-002 must be amended and XPLAT-003 controls regenerated for Cargo/crate/toolchain/artifact evidence. |
| Zig native artifact | Users do not install Zig if maintainers build and ship per-platform executables. | Viable same runtime model, but XPLAT-002 must be amended and XPLAT-003 controls regenerated for Zig/toolchain/artifact evidence. |
| Node or Python source script | Users need Node or Python unless a runtime is bundled or the platform officially guarantees it. | Not acceptable for no-post-cache-install claims without a bundled runtime, official guarantee, or fail-closed prerequisite behavior. |
| Bundled Node or embedded Python | Users do not install the interpreter, but the payload now ships a larger runtime artifact. | Treat as native/runtime-bundle packaging with expanded vulnerability, license, checksum, manifest, and update controls. |
| Bash, `jq`, package-manager restoration, WSL, or Git Bash dependency | Requires user environment setup or platform-specific shell assumptions. | Not acceptable for first-release native-support claims after plugin cache population. |

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
| Go native binary recorded by XPLAT-002 | Trust model currently centers on per-platform executable artifacts and their release metadata, but this premise is reopened and conditional until explicit maintainer re-approval. |
| No built runner exists | XPLAT-003 cannot validate installed-cache execution; XPLAT-004 must produce artifacts and preflight/version evidence. |
| Installed users receive packaged artifacts | First-release controls must avoid post-cache dependency installation, package restoration, `jq`, Bash, or source checkout requirements. |
| Runtime-info/preflight exists in contract | XPLAT-003 extends the evidence expected from runtime-info/preflight with artifact-integrity pointers. |
| XPLAT-007 owns generated payload cutover | Generated payload source-to-dist evidence and public support claims stay with XPLAT-007. |

## Control Decisions

Runtime-decision status: conditional. The controls below are valid as the
trust model for the Go native runner recorded by XPLAT-002, but they must not
be treated as final acceptance criteria for XPLAT-004 or XPLAT-007 until the
runtime choice is explicitly re-approved. If the runtime choice changes, the
control matrix must be rerun against the amended runtime's dependency,
packaging, installed-cache, artifact, and consumer-verification shape.

| Control | Classification | Owner | Rationale | Acceptance gate |
|---|---|---|---|---|
| Official platform capability evidence | First-release required | XPLAT-003 records; XPLAT-004/XPLAT-007 consume | Runtime and install claims must separate official Claude/Codex support from repository assumptions. | Readiness planning fails if a selected runtime assumes a user-host runtime that official docs do not guarantee and the payload does not bundle or diagnose. |
| Installed-user runtime dependency boundary | First-release required | XPLAT-004 and XPLAT-007 | Build-time toolchains may exist in maintainer automation, but installed users must not install toolchains or restore packages after cache population for native claims. | Public support claims fail if the runner depends on user-installed Go, Rust, Zig, Node, Python, Bash, `jq`, package managers, WSL, Git Bash, or post-cache network restoration. |
| Codex custom-agent install completeness | First-release required when Codex agents are part of the release promise | XPLAT-007 / install skill owner | Official Codex docs register custom subagents through `.codex/agents/*.toml` or `~/.codex/agents/*.toml`, not by generic plugin `agents/` bundling. | Codex install-completeness validation fails when required TOML agents are absent even if plugin skills are installed. |
| Selected-runtime pinned release inputs | First-release required | XPLAT-004 | Native artifacts need a stable source, toolchain, module/dependency snapshot, build input, source revision, artifact path, and checksum boundary before checksums mean anything. Go-specific fields apply only if Go is re-approved. | Runner readiness fails if pinned input evidence is missing, stale, unknown, or unverified. |
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

The path also does not require users to install the implementation toolchain.
If Go remains selected, consumers verify the packaged executable; they do not
install Go. If Rust, Zig, bundled Node, embedded Python, or another runtime
shape is selected instead, the verification path must be regenerated for that
artifact shape and must preserve the same no-post-cache-install boundary.

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

No deferred cryptographic hardening control is promoted to first-release
required in XPLAT-003. The official-doc research adds three first-release
boundary controls: platform capability evidence, installed-user runtime
dependency separation, and Codex custom-agent install completeness when Codex
agents are part of the release promise.

The practical first-release baseline is sufficient for XPLAT-004 and XPLAT-007
planning only if maintainers explicitly re-approve the Go native runner
decision. Until then, this research is a conditional analysis and not a final
runtime acceptance record. If the runtime changes to Rust, Zig, bundled Node,
embedded Python, or another shape, the control matrix must be regenerated rather
than edited opportunistically.

Release automation remains assigned but not implemented in XPLAT-003. Any public claim that relies on release automation remains blocked until XPLAT-007 or a later release automation surface records current acceptance evidence.
