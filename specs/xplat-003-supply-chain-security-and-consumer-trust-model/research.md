# Research: Supply-Chain Security and Consumer Trust Model

## Source Inputs

- XPLAT-001 supply-chain rubric: `docs/ai/research/cross-platform-runtime-inventory.md`
- XPLAT-002 runtime decision: `specs/xplat-002-runtime-implementation-options-contract-decision/runtime-decision.md`
- XPLAT-002 handoff: `specs/xplat-002-runtime-implementation-options-contract-decision/handoff.md`
- XPLAT-002 runner contract: `specs/xplat-002-runtime-implementation-options-contract-decision/contracts/speckit-pro-runner-contract.md`
- XPLAT-003 design concept: `docs/ai/specs/.process/XPLAT-003-design-concept.md`
- XPLAT-003 finalized spec: `specs/xplat-003-supply-chain-security-and-consumer-trust-model/spec.md`
- XPLAT-003 platform user journeys and gaps:
  `specs/xplat-003-supply-chain-security-and-consumer-trust-model/platform-user-journeys.md`
- Official Claude Code plugin docs: `https://code.claude.com/docs/en/plugins`
- Official Claude Code plugin marketplace docs: `https://code.claude.com/docs/en/plugin-marketplaces`
- Official Claude Code plugin reference: `https://code.claude.com/docs/en/plugins-reference`
- Official Claude Code skills docs: `https://docs.anthropic.com/en/docs/claude-code/skills`
- Official OpenAI Codex plugin docs: `https://developers.openai.com/codex/plugins`
- Official OpenAI Codex plugin build docs: `https://developers.openai.com/codex/plugins/build`
- Official OpenAI Codex skills docs: `https://developers.openai.com/codex/skills`
- Official OpenAI Codex hooks docs: `https://developers.openai.com/codex/hooks`
- Official OpenAI Codex MCP docs: `https://developers.openai.com/codex/mcp`
- Official OpenAI Codex subagents docs: `https://developers.openai.com/codex/subagents`
- Official Spec Kit installation docs:
  `https://github.com/github/spec-kit/blob/main/docs/installation.md`
- Official Spec Kit package metadata:
  `https://github.com/github/spec-kit/blob/main/pyproject.toml`

## Decision Method

Use the XPLAT-001 supply-chain rubric as a non-scoring template, then apply the
amended XPLAT-002 handoff boundary: the active runtime is a Python
standard-library runner aligned with official Spec Kit / `specify`
prerequisites. No runner exists yet, and XPLAT-003 chooses controls without
implementing them. Go/Rust/Zig and other compiled-binary conclusions are
preserved only as historical rejected evidence; they are not downstream
implementation criteria, compatibility adapters, or fallback paths for XPLAT.

Controls are classified as:

- **First-release required**: must be implemented and verified before public cutover or claims rely on the selected Python runner.
- **Deferred hardening**: desirable trust hardening that is not required for the first release unless promotion evidence appears.
- **Explicitly not claimed**: guarantees public docs and release notes must not imply before implementation and verification.
- **Out of scope**: implementation work that belongs to a downstream spec or release surface.

Platform documentation evidence is used only for what each product officially
packages or registers. Runtime availability is not inferred from a local host
probe or from the existence of plugin `scripts/` support.

## Official Platform Documentation Findings

| Platform surface | Officially supported package/registration surface | Runtime implication for XPLAT |
|---|---|---|
| Claude Code plugins | Plugins can package skills, agents, hooks, MCP configuration, scripts, and `bin/` executables. Plugin `bin/` executables are exposed for plugin use while enabled. | Claude packaging supports executable/script payloads, but the docs do not by themselves guarantee Go, Rust, Zig, Node, Bash, `jq`, or package managers on every user host. Python is allowed only through the official Spec Kit prerequisite boundary. |
| Claude Code skills | Skills can include `SKILL.md` plus optional scripts, references, and assets. | Skill scripts are supported as packaged resources, but the script runtime remains a host or bundled-artifact concern. |
| OpenAI Codex plugins | Plugins can package skills, apps, MCP servers, lifecycle hooks, and install payloads. Hooks expose plugin root/data context to command scripts. | Codex packaging supports plugin script and MCP command surfaces, but the docs do not guarantee arbitrary language runtimes after install. |
| OpenAI Codex skills | Skills can include optional `scripts/`, references, and assets. | Codex skill scripts are supported as resources, but runtime availability still must be guaranteed, bundled, or diagnosed. |
| OpenAI Codex subagents | Custom subagents are documented as TOML files in `.codex/agents/` or `~/.codex/agents/`. | Codex install completeness cannot be inferred from plugin skill presence alone; required custom-agent TOML registrations must be validated or autohealed separately. |

Decision effect: official docs support a plugin-payload delivery model for
scripts and executables, but they do not select a runtime. The first-release
runtime is selected from the product prerequisite boundary instead: SpecKit-Pro
requires official Spec Kit / `specify`, and that environment requires Python
3.11+. The runner must verify this prerequisite and fail closed when it is
absent.

## Python Runner Distribution And Installation Model

The amended runtime model avoids per-platform binary distribution for XPLAT:

| Distribution shape | Marketplace/install behavior | XPLAT consequence |
|---|---|---|
| Python stdlib runner source in generated plugin payloads | Claude and Codex install the runner source with the plugin payload. The user supplies the official Spec Kit prerequisite environment. | Preferred first-release model. XPLAT-004 implements the runner and preflight; XPLAT-007 proves the runner source is present, fresh, and equal in both Claude and Codex payload roots. |
| Thin payload-local launcher | A launcher may provide a stable command target for Claude/Codex, but it only locates Python and dispatches to the runner source. | Allowed only if the launcher contains no helper logic and no Bash/PowerShell implementation behavior. |
| Plugin-only Python package dependencies | Would require `pip install`, vendored wheels, virtualenv restoration, or bundled Python. | Not allowed in XPLAT; the runner must remain stdlib-only. |
| Compiled Go/Rust/Zig/native artifacts | Would add a second implementation and distribution model even though SpecKit already requires Python. | Rejected for XPLAT. Not a fallback. |

Repository-specific implication: this project does not install directly from
`speckit-pro/`. Claude installs come from `.claude-plugin/marketplace.json`
pointing at `./dist/claude/speckit-pro`; Codex installs come from
`.agents/plugins/marketplace.json` pointing at `./dist/codex/speckit-pro`.
XPLAT-007 must prove the Python runner source and any launcher/preflight
metadata are copied into both generated payload roots.

## Rejected Runtime Candidate Implications

| Runtime shape | User install impact | XPLAT-003 consequence |
|---|---|---|
| Python stdlib source runner | Users install official Spec Kit / `specify`, which requires Python 3.11+. They do not install plugin-only Python dependencies. | Selected first-release model. XPLAT-004 owns interpreter/specify preflight, stdlib-only enforcement, runner source integrity, and installed-cache launch proof. |
| Rejected Go native-binary path | Users would not install Go if maintainers built and shipped per-platform executables, but XPLAT would gain a second implementation/distribution model. | Rejected for XPLAT because SpecKit already requires Python. Not a fallback. |
| Rejected Rust native-binary path | Users would not install Rust if maintainers built and shipped per-platform executables, but XPLAT would gain a second implementation/distribution model. | Rejected for XPLAT because SpecKit already requires Python. Not a fallback. |
| Rejected Zig native-binary path | Users would not install Zig if maintainers built and shipped per-platform executables, but XPLAT would gain a second implementation/distribution model. | Rejected for XPLAT because SpecKit already requires Python. Not a fallback. |
| Node source script | Users need Node unless a runtime is bundled or the platform officially guarantees it. | Rejected for XPLAT because Node is not part of the SpecKit prerequisite boundary. |
| Bundled Node or embedded Python | Users do not install the interpreter, but the payload now ships a larger runtime artifact. | Rejected for XPLAT because bundled runtimes add supply-chain surface that the SpecKit Python prerequisite avoids. |
| Bash, `jq`, package-manager restoration, WSL, or Git Bash dependency | Requires user environment setup or platform-specific shell assumptions. | Not acceptable for first-release native-support claims after plugin cache population. |

## XPLAT-001 Rubric Mapping

| Rubric criterion | XPLAT-003 decision |
|---|---|
| Dependency policy and lockfile discipline | First-release required for Python runner source, stdlib-only policy, and official Spec Kit prerequisite verification; XPLAT-004 owns concrete preflight and source-integrity evidence. |
| Generated payload integrity | First-release required; XPLAT-007 owns source-to-dist gate and generated drift evidence. |
| Vulnerability scanning | First-release required; actionable high/critical findings block readiness unless a non-actionable exception record exists. |
| Provenance or attestation options | Deferred hardening; do not claim provenance or attestations until implemented and verified. |
| Checksums/signatures | SHA-256 checksums are first-release required; signatures are deferred hardening. |
| SBOM feasibility | Deferred hardening; keep a future path but do not require an SBOM for first release. |
| Consumer-local verification | First-release required; use runner identity/preflight plus Python standard-library checksum comparison. OS-native checksum commands may be supplemental only. |
| Release automation and documentation truthfulness | First-release required as a claim boundary; release workflow edits are out of scope for XPLAT-003. |

## XPLAT-002 Handoff Implications

| Handoff input | XPLAT-003 implication |
|---|---|
| Python stdlib runner recorded by amended XPLAT-002 | Trust model centers on Python source payload integrity, official Spec Kit prerequisite verification, and installed-cache launch evidence. |
| No built runner exists | XPLAT-003 cannot validate installed-cache execution; XPLAT-004 must produce runner source, launcher metadata where used, and preflight/version evidence. |
| Installed users receive packaged runner files | First-release controls must avoid post-cache dependency installation, package restoration, `jq`, Bash, PowerShell helper scripts, or source checkout requirements. |
| Runtime-info/preflight exists in contract | XPLAT-003 extends the evidence expected from runtime-info/preflight with runner source-integrity pointers. |
| XPLAT-007 owns generated payload cutover | Generated payload source-to-dist evidence and public support claims stay with XPLAT-007. |

## Control Decisions

Runtime-decision status: amended to Python. The controls below are the active
trust model for the Python standard-library runner. Go/Rust/Zig/native-binary
controls are rejected historical analysis and are not XPLAT controls.

| Control | Classification | Owner | Rationale | Acceptance gate |
|---|---|---|---|---|
| Official platform and product-prerequisite evidence | First-release required | XPLAT-003 records; XPLAT-004/XPLAT-007 consume | Runtime and install claims must separate Claude/Codex platform support from the official Spec Kit / `specify` prerequisite boundary. | Readiness planning fails if the runner assumes Python/specify without preflight or assumes any other user-host runtime not in the documented prerequisite boundary. |
| Installed-user runtime dependency boundary | First-release required | XPLAT-004 and XPLAT-007 | Python 3.11+ and `specify` are allowed product prerequisites; every other implementation runtime, package manager, shell, or restoration step is disallowed unless bundled or fail-closed. | Public support claims fail if the runner depends on user-installed Go, Rust, Zig, Node, Bash, `jq`, package managers, WSL, Git Bash, PowerShell helper scripts, `pip install`, virtualenv restoration, or post-cache network restoration. |
| Codex custom-agent install completeness | First-release required when Codex agents are part of the release promise | XPLAT-007 / install skill owner | Official Codex docs register custom subagents through `.codex/agents/*.toml` or `~/.codex/agents/*.toml`, not by generic plugin `agents/` bundling. | Codex install-completeness validation fails when required TOML agents are absent even if plugin skills are installed. |
| Selected-runtime source and prerequisite evidence | First-release required | XPLAT-004 | Python runner readiness needs a stable source path, source revision, stdlib-only policy, Python minimum version, interpreter discovery order, `specify` discovery/version evidence, generated payload paths, and scan inputs. | Runner readiness fails if prerequisite, source-integrity, payload, scan, or installed-cache launch evidence is missing, stale, unknown, or unverified. |
| Generated payload source-to-dist gate | First-release required | XPLAT-007 | Marketplace installs consume generated Claude/Codex payloads; source and dist must reconcile before cutover. | Public cutover fails if rebuild/drift evidence or checksum/manifest metadata propagation evidence is missing, stale, or unequal across source and generated roots. |
| Python build/test/eval/release-readiness gates | First-release required | XPLAT-007 | A pure Python runtime claim is incomplete if the active gates that validate or publish shipped plugin behavior still require Bash or `jq`. | Public cutover fails if shipped-behavior build, test, eval, payload, or release-readiness gates remain Bash-only, except for historical/archive text or temporary parity evidence outside the final release gate. |
| Runner source integrity metadata | First-release required | XPLAT-004 creates; XPLAT-007 verifies/docs | Checksums or equivalent source-integrity metadata are the minimum practical integrity control consumers can verify without marketplace enforcement. | Each packaged runner source or launcher file covered by the claim has matching integrity metadata. |
| Runner source manifest | First-release required | XPLAT-004 creates; XPLAT-007 verifies/docs | Consumers and maintainers need runner identity, prerequisite boundary, source revision, payload path, and integrity metadata. | Manifest includes all required top-level and runner source fields. |
| Vulnerability scans | First-release required | XPLAT-004 for runner/source; XPLAT-007 for cutover/public readiness | Actionable high/critical findings and stale evidence must block release readiness before Python runner support is publicly claimed. | Readiness fails on missing/stale evidence or unresolved actionable high/critical findings. |
| Vulnerability exceptions | First-release required when used | Owning downstream surface | Non-actionable findings need durable rationale, approval, and expiry to avoid silently weakening the gate. | Exception records include all required fields and expire before each public release or on changed evidence. |
| Runtime-info/preflight source-integrity fields | First-release required | XPLAT-004 | Consumer verification starts with identity/preflight evidence and needs pointers to runner source integrity and manifest metadata. | Preflight/runtime-info includes runner source path, manifest path, integrity metadata path, expected checksum if used, algorithm, and verification status. |
| Consumer-local verification guide | First-release required | XPLAT-007 | Consumers must be able to verify without `jq`, Bash, PowerShell helper scripts, source checkout, or network package restoration. | Guidance uses identity/preflight first, then Python standard-library source-integrity comparison where XPLAT-004/XPLAT-007 require checksums. |
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
- The finding affects the first-release trust boundary: runner source,
  prerequisite/preflight behavior, release inputs, packaged runner files,
  integrity metadata, generated payloads, marketplace manifests, or release
  evidence.
- The finding is reachable, shipped, or capable of changing release output or public claims.

Findings may be treated as non-actionable only with an exception record when they are false positives, unreachable, non-shipped, repo-only/test/archive/docs-only, or already mitigated at the artifact boundary.

Scan evidence is stale when it is older than 7 calendar days at readiness review, predates the source revision, dependency manifest or sum state, toolchain, build input, generated artifact, scanner version or vulnerability database timestamp it claims to cover, or crosses a public release boundary without re-approval.

Exception records expire before each public release unless re-approved from current evidence. They expire immediately when the affected artifact, dependency graph, platform, toolchain, scanner version/database, advisory status, severity, exploitability, or compensating control changes.

Durable, non-sensitive summaries and exception records are retained in the owning spec, PR packet, or release-readiness artifact. Raw scanner output is not committed by default; after automation exists, raw output is retained as a 30-day CI artifact unless a scoped/redacted excerpt is required to support an exception.

## Consumer Verification Boundary

The first-release consumer path is:

1. Run runner identity/preflight from the installed plugin payload.
2. Locate the runner source manifest and checksum file from runtime-info/preflight output or documented payload-relative paths.
3. Compute SHA-256 for the installed runner file using a Python standard-library
   checksum command shape that XPLAT-004/XPLAT-007 provide through the
   preflight-discovered interpreter. OS-native checksum commands may be listed
   as optional cross-checks only.
4. Compare the computed hash to the matching payload-relative entry in `scripts/speckit-pro-runner.sha256`.

This path does not rely on runner self-verification alone and does not require
`jq`, Bash, PowerShell helper scripts, source checkout, or network package
restoration. If runner-file or checksum metadata is unavailable, guidance must
fail closed with an explicit unavailable state rather than instructing consumers
to fetch dependencies or clone source.

The path also does not require users to install an implementation toolchain.
Go/Rust/Zig/native binaries are not XPLAT alternatives, so consumer guidance
does not include compiled-binary verification paths.

A computed checksum mismatch is also a closed verification failure. Consumer
guidance should tell users not to rely on the affected runner file for support
claims, record the runner file path, platform, runner identity/preflight output,
metadata source, expected checksum, computed checksum, plugin version or release
boundary, and reporting path, and wait for maintainer remediation backed by
fresh XPLAT-004 and XPLAT-007 evidence. Local source checkout repair, package
restoration, network replacement fetches, Bash, `jq`, PowerShell helper scripts,
and runner self-verification alone are rejected remediation paths because they
would move trust outside the installed payload and release evidence boundary.

## Public Claim Boundary

Allowed after implementation and verification:

- Packaged Python runner source files and any thin launchers.
- SHA-256 checksum file and runner source manifest.
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

Runner-file and platform claims are evaluated per claimed runner file. A
platform with complete current evidence may be claimable for that platform only;
missing, stale, mismatched, unpublished, or unsupported runner files must be
excluded from claims or keep the claim set blocked. One passing runner file does
not imply native Windows/macOS/Linux support for any other platform.

## Result

No deferred cryptographic hardening control is promoted to first-release
required in XPLAT-003. The official-doc research adds three first-release
boundary controls: platform capability evidence, installed-user runtime
dependency separation, and Codex custom-agent install completeness when Codex
agents are part of the release promise.

The practical first-release baseline is sufficient for XPLAT-004 and XPLAT-007
planning with the amended Python runner decision. The platform user-journey
supplement records the Windows-first install/use/update/repair path for Claude
Code and Codex and makes clear that universal install requires payload
completeness, Codex custom-agent registration completeness, Python
runner/preflight files, platform-compatible hooks/scripts, scaffold/autopilot
autoheal, Python build/test/eval/release-readiness gates, and UAT runbook
quality evidence. Until those gaps are closed, this research is a planning
baseline and not a public support acceptance record. Go/Rust/Zig/native-binary
paths are rejected for XPLAT rather than deferred.

Release automation remains assigned but not implemented in XPLAT-003. Any public claim that relies on release automation remains blocked until XPLAT-007 or a later release automation surface records current acceptance evidence.
