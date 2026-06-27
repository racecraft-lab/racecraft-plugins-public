# Implementation Plan: Supply-Chain Security and Consumer Trust Model

**Branch**: XPLAT-003 feature branch | **Date**: 2026-06-27 | **Spec**: `specs/xplat-003-supply-chain-security-and-consumer-trust-model/spec.md`

**Input**: Feature specification from `specs/xplat-003-supply-chain-security-and-consumer-trust-model/spec.md`, setup design concept from `docs/ai/specs/.process/XPLAT-003-design-concept.md`, and plan prompt from `docs/ai/specs/.process/XPLAT-003-workflow.md`.

## Summary

XPLAT-003 is a decision spike that records a conditional first-release supply-chain and consumer-trust baseline for the Go native `speckit-pro-runner` currently recorded by XPLAT-002. The runtime choice has been reopened for explicit maintainer re-approval on this PR, so these decision artifacts are blocked from final acceptance until maintainers re-approve Go or amend XPLAT-002 and regenerate the trust model. Official Claude Code and OpenAI Codex documentation is now an explicit planning input: plugins and skills can package scripts/executables and MCP/hook surfaces, but those docs do not guarantee arbitrary user-host runtimes. The plan produces decision artifacts only: no runner implementation, helper port, generated payload rebuild, release workflow edit, or public native-support claim.

The first-release baseline is:

- Source-to-dist integrity evidence for generated plugin payloads.
- Official platform capability evidence separating documented Claude/Codex
  plugin surfaces from undocumented user-runtime assumptions.
- Installed-user runtime dependency boundaries: build toolchains may exist in
  maintainer automation, but public native claims must not require users to
  install Go, Rust, Zig, Node, Python, Bash, `jq`, package managers, WSL, Git
  Bash, or network package restoration after plugin cache population.
- Codex install-completeness evidence that treats required custom-agent TOML
  registration as separate from plugin skill installation.
- Metadata propagation evidence proving checksum and runner manifest paths are present, equal, and fresh across source, generated Claude payload, and generated Codex payload roots before XPLAT-007 cutover.
- SHA-256 checksums for packaged runner artifacts in `scripts/speckit-pro-runner.sha256`.
- A runner artifact manifest at `scripts/speckit-pro-runner.manifest.json`.
- Vulnerability scanning that fails readiness on unresolved actionable high or critical findings, with documented exceptions for non-actionable findings.
- Consumer-local verification through runner identity and preflight output plus platform-native checksum comparison.
- Closed consumer remediation for checksum mismatches: consumers do not rely on the artifact, record mismatch facts in a report, and wait for fresh maintainer evidence.
- Durable non-sensitive retention of release-readiness and public-claim audit summaries beyond scan evidence alone.
- Per-artifact and per-platform claim readiness so partial artifact publication cannot imply unsupported platform claims.
- Public docs and release notes limited to controls that are implemented and verified.
- Split ownership: XPLAT-004 owns runner source and artifact controls, XPLAT-007 owns generated payload cutover, consumer guidance, native UAT, and public claim readiness, and release automation owns publication-time evidence only when a later spec wires it in.

## Technical Context

**Language and Version**: Not applicable for this phase. Downstream runner implementation is conditionally described as Go native binary per XPLAT-002, but that choice is reopened for explicit maintainer re-approval and XPLAT-003 does not add Go code. Go, Rust, Zig, bundled Node, embedded Python, or another runtime shape must be treated as a packaging and supply-chain decision before implementation, not as a user-install requirement.

**Primary Dependencies**: Existing repository Markdown and SpecKit helper scripts only. No new runtime dependency.

**Storage**: Checked-in specification artifacts under `specs/xplat-003-supply-chain-security-and-consumer-trust-model/`.

**Testing**: Static specification validation only for this phase: marker counts, G7 task completion, spec-index freshness, diff whitespace, and diff scope review.

**Target Platform**: Decision applies to future packaged native runner artifacts for Windows, macOS, and Linux, but this phase does not build or claim native platform support.

**Project Type**: Claude Code and Codex plugin marketplace decision artifact.

**Performance Goals**: Not applicable. Release-readiness evidence must be deterministic and reviewable, not performance-bound.

**Constraints**:

- One decision spike, not implementation.
- Use XPLAT-001 supply-chain rubric and XPLAT-002 Go runner handoff as conditional source evidence while the runtime choice is reopened.
- Use official Claude Code and OpenAI Codex documentation as the authority for
  plugin, skill, hook, MCP, script, executable, and custom-agent surfaces.
- Do not infer user-host runtime availability from plugin `scripts/` support,
  local host probes, or repository tooling. A selected runtime must be bundled,
  self-contained as per-platform artifacts, officially guaranteed for the
  installed surface, or diagnosed as missing without support claims.
- Do not edit release automation in XPLAT-003.
- Do not build `speckit-pro-runner`, port helpers, change active invocation paths, or rebuild generated payloads.
- Do not claim signatures, SBOMs, provenance or attestations, reproducible builds, formal audit, marketplace-enforced verification, cryptographic trust-chain verification, or native platform support before those controls are implemented and verified.
- Do not treat XPLAT-003 as final, start XPLAT-004 runner implementation, or authorize XPLAT-007 public cutover until the reopened runtime choice is explicitly re-approved or amended.

**Scale and Scope**: One spec directory; 0 production LOC; decision records and contracts only.

**Reviewability Budget**: Setup gate returned warning status: `reviewable_loc=250`, `production_files=4`, `total_files=10`, `primary_surface_count=2`, warning `primary surfaces 2 exceeds warn threshold 1`, no blockers. After the official-doc/runtime-reopen additions, tasks-mode reviewability reports a size-only block (`reviewable_loc=1000`, `total_files=31`) because the task estimator counts task and file tokens broadly. The actual diff-mode PR gate remains warning-only with `reviewable_loc=0`, `production_files=0`, `total_files=24`, and no blockers. XPLAT-003 remains one decision spike because it records one security and trust model and assigns downstream controls without implementation changes.

## Declared File Operations

- MODIFIED specs/xplat-003-supply-chain-security-and-consumer-trust-model/plan.md
- NEW specs/xplat-003-supply-chain-security-and-consumer-trust-model/research.md
- NEW specs/xplat-003-supply-chain-security-and-consumer-trust-model/data-model.md
- NEW specs/xplat-003-supply-chain-security-and-consumer-trust-model/contracts/supply-chain-control-contract.md
- NEW specs/xplat-003-supply-chain-security-and-consumer-trust-model/quickstart.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Result |
|---|---|---|
| Plugin Structure Compliance | No runner artifacts, generated payload changes, plugin invocation changes, or release workflow changes. | Pass: phase outputs are spec artifacts only. |
| Script Safety | Future commands are recorded as policy or verification commands only; no helper implementation lands here. | Pass: contracts describe evidence shapes and do not add scripts. |
| Test Coverage Before Merge | Static validation must prove marker cleanliness, G7 task completion, spec-map freshness, whitespace health, and diff scope. | Pass via Phase 7 validation commands in `quickstart.md`. |
| Conventional Commits | No commit in this phase. | Not applicable. |
| KISS, Simplicity, YAGNI | First release uses the minimum truthful trust baseline; heavier controls remain deferred unless promotion evidence appears. | Pass. |
| Reviewability | Setup warning for two primary surfaces is recorded and accepted. | Warning status, not blocking. |

## Project Structure

### Documentation (this feature)

```text
specs/xplat-003-supply-chain-security-and-consumer-trust-model/
|-- SPEC-MOC.md
|-- checklists/
|   `-- requirements.md
|-- contracts/
|   `-- supply-chain-control-contract.md
|-- data-model.md
|-- plan.md
|-- quickstart.md
|-- research.md
`-- spec.md
```

### Source Code (repository root)

```text
No source-code changes in XPLAT-003.
No changes under the source plugin tree, generated payload roots, docs site, workflow directory, or release metadata.
```

**Structure Decision**: XPLAT-003 keeps all phase outputs inside the XPLAT-003 spec directory. Downstream implementation specs may use this plan as input, but this phase does not create implementation files.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Setup reviewability warning: two primary surfaces | The decision must assign controls to both process documentation surfaces and future runner ownership without implementing either surface. | Splitting the decision would scatter one trust model across multiple specs and make first-release claims harder to audit. |

## Phase 0 Research

`research.md` records:

- XPLAT-001 supply-chain rubric mapping.
- XPLAT-002 Go native runner handoff implications, now labeled conditional because the runtime choice is reopened on this PR.
- Official Claude Code and OpenAI Codex platform capability findings.
- Runtime reopen implications for Go, Rust, Zig, bundled Node, embedded Python,
  source scripts, Bash, `jq`, package managers, WSL, and Git Bash.
- First-release versus deferred hardening decisions.
- Vulnerability actionability and exception policy.
- Scan evidence freshness and staleness blockers.
- Conditional pinned release input evidence requirements, with Go-specific
  fields applying only if Go is re-approved.
- Consumer-local verification boundary.
- Public claim allowed and prohibited language boundary.

Open research result: no deferred cryptographic hardening control is promoted to first-release required in XPLAT-003. Checksums, manifest, scan policy, source-to-dist evidence, consumer verification, official platform capability evidence, runtime dependency separation, Codex install-completeness evidence, and truthful claims are enough for the first public release baseline.

Runtime-decision blocker: the above result is conditional on explicit
maintainer re-approval of the XPLAT-002 Go runtime choice. If maintainers amend
the runtime decision, this plan, research, data model, and contract must be
regenerated for the selected runtime before XPLAT-004 or XPLAT-007 consume them.

## Phase 1 Design Artifacts

`data-model.md` defines the decision entities: control decision, owner assignment, artifact manifest, checksum entry, source-to-dist evidence, vulnerability scan evidence, exception record, public claim boundary, and release-readiness evidence.

`contracts/supply-chain-control-contract.md` defines the normative evidence shapes for downstream specs:

- Control decision records.
- Pinned release input evidence records, with Go-specific fields applying only
  if Go is re-approved.
- Platform capability evidence records.
- Runtime dependency boundary records.
- Install completeness evidence records for Claude and Codex.
- SHA-256 checksum file format.
- Runner artifact manifest fields.
- Runtime-info and preflight artifact-integrity fields.
- Source-to-dist evidence record.
- Generated payload metadata propagation rules.
- Release automation acceptance evidence records for publication controls.
- Scan evidence freshness rules.
- Vulnerability exception record.
- Consumer-local checksum guidance records.
- Public claim audit record.

`quickstart.md` gives a reviewer path and static validation commands for this phase.

## First-Release Evidence Contracts

XPLAT-003 defines evidence contracts only. XPLAT-004 records and implements runner build evidence. XPLAT-007 consumes accepted evidence for final cutover, release-readiness gating, consumer-local verification guidance, and public wording after native UAT passes.

### Platform Capability and Runtime Boundary Gate

XPLAT-004 and XPLAT-007 must treat official platform documentation as a gate
for runtime and install claims:

- Claude Code support for plugin skills, agents, hooks, MCP servers, scripts,
  and `bin/` executables does not prove that a user host has any particular
  language runtime or package manager.
- OpenAI Codex support for plugin skills, apps, MCP servers, hooks, and skill
  `scripts/` does not prove that a user host has any particular language runtime
  or package manager.
- Codex custom subagents are installed as `.codex/agents/*.toml` or
  `~/.codex/agents/*.toml`; required Codex agent registrations are an install
  completeness gate separate from plugin skill presence.

The selected runner must either ship as self-contained per-platform artifacts,
bundle the required runtime, rely on a runtime officially guaranteed for the
installed surface, or fail closed through prerequisite diagnostics without
public native-support claims.

### Scan Evidence Freshness Gate

Required scan evidence records include:

| Field | Required |
|---|---|
| Scan tool or command | Yes |
| Scanner version or vulnerability database timestamp | Yes |
| Scan scope | Yes |
| Target source revision | Yes |
| Dependency manifest or sum snapshot | Yes |
| Toolchain and build input snapshot | Yes |
| Generated artifact identifier, when applicable | Yes |
| Run timestamp | Yes |
| Result and severity summary | Yes |
| Actionable high and critical count | Yes |
| Exception record references, when applicable | Conditional |
| Owner surface | Yes |
| Freshness expiry | Yes |

Readiness fails when evidence is missing, stale, predates the source, dependency, toolchain, build input, scanner database, or artifact it covers, crosses a public release boundary without re-approval, or has unresolved actionable high and critical findings. The default freshness window is 7 calendar days before readiness review unless a stricter source, dependency, artifact, or scanner change invalidates the evidence sooner.

### Pinned Release Input Evidence

If Go is re-approved, XPLAT-004 must record:

- Selected build toolchain version.
- Selected build toolchain source or installation method.
- Selected runtime dependency manifest and checksum/snapshot state, such as Go
  module manifest plus `go.sum` when Go is re-approved.
- Target OS and architecture matrix.
- Build command or repeatable build recipe.
- Release package input list.
- Source revision used to build artifacts.
- Generated artifact names and payload-relative paths.
- Generated artifact SHA-256 checksums.
- First-release vulnerability scan inputs and evidence references.

Unknown or unverified values are evidence gaps and cannot be treated as accepted controls.

If the runtime is amended to Rust, Zig, bundled Node, embedded Python, or another
shape, this evidence section must be regenerated for that runtime's toolchain,
dependency graph, artifact format, build inputs, scan path, checksum/manifest
metadata, and consumer verification behavior.

### Generated Payload Metadata Propagation Gate

XPLAT-007 must prove that checksum and runner artifact manifest metadata produced by XPLAT-004 flows into the payloads that public installs consume:

```text
XPLAT-004 runtime artifact outputs
-> source checksum and manifest paths
-> generated Claude metadata paths
-> generated Codex metadata paths
-> XPLAT-007 cutover evidence
```

The gate must record producer evidence refs, source metadata paths, generated Claude metadata paths, generated Codex metadata paths, equality rule, freshness rule, and failure rule. Missing metadata, stale metadata, or unequal source/generated metadata fails public cutover and release-claim readiness. XPLAT-003 does not create metadata files or rebuild payloads.

### Consumer-Local Checksum Verification Guidance

XPLAT-007 must provide platform-specific command shapes for every platform artifact it intends to claim after native UAT passes:

| Platform | SHA-256 command shape |
|---|---|
| Windows | `Get-FileHash -Algorithm SHA256 <runner-path>` |
| macOS | `shasum -a 256 <runner-path>` |
| Linux | `sha256sum <runner-path>` |

Guidance must describe metadata lookup from the installed payload or release-provided offline metadata. If checksum metadata is unavailable, guidance must fail closed with an explicit "verification metadata unavailable" state instead of instructing users to fetch dependencies, clone the source repository, run Bash, use `jq`, or restore packages from the network.

These command shapes are XPLAT-007 guidance requirements, not current public native-support claims.

### Checksum Mismatch Remediation

XPLAT-007 consumer guidance must treat a computed checksum that differs from
the matching published checksum entry as a closed verification failure. The
consumer-facing path must say not to rely on that artifact for native-runner
claims and must collect enough information for maintainers to investigate:
artifact path, target platform, runner identity or preflight output, checksum
metadata source, expected checksum, computed checksum, plugin version or release
boundary, and reporting path.

The guidance must not ask consumers to repair a mismatch by cloning source,
restoring packages, fetching replacement dependencies from the network, running
Bash or `jq`, or trusting runner self-verification alone. Maintainers may accept
the artifact again only after fresh XPLAT-004 artifact, checksum, and manifest
evidence and XPLAT-007 source-to-dist, claim-audit, and consumer-guidance
evidence are current for the affected artifact.

### Release-Readiness and Claim-Audit Retention

XPLAT-007 or the owning release surface must retain durable, non-sensitive
summaries for release-readiness evidence and public-claim audit evidence. These
summaries are distinct from raw scan logs and must include release boundary,
control or claim IDs, evidence references, pass, fail, or blocked status,
timestamp or source revision, owner surface, known gaps, and approval status.

Allowed durable locations are the owning spec, PR packet, release-readiness
artifact, release record, or other release artifact designed for audit. Raw logs
and large generated artifacts are not committed by default; once automation
exists, they may remain short-retention CI or release artifacts that support the
durable summary rather than replacing it.

### Partial Artifact Publication Gate

Public cutover and release claims are evaluated per claimed artifact and
platform. A platform artifact may be ready only for its own claim scope when its
checksum, manifest, runtime-info and preflight, native UAT, source-to-dist, scan,
exception, release-automation, and claim-audit evidence are current.

If an intended platform artifact is missing, stale, mismatched, unpublished, or
lacks required evidence, XPLAT-007 must either exclude that artifact and platform
from public claims with an explicit deferred or not claimable record or keep the
claim set blocked. One passing platform never implies Windows, macOS, and Linux
support for other platforms.

### Release Automation Acceptance Evidence

Release automation controls are not implemented by XPLAT-003 and are not accepted merely because XPLAT-003 assigns them. Any public release or trust claim that relies on release automation must have downstream acceptance evidence before it is claimable.

Required acceptance evidence includes:

- Implementing spec or release surface.
- Control ID.
- Publication or release gate location.
- Release inputs and generated outputs covered by the gate.
- Latest pass or fail evidence and evidence timestamp or release boundary.
- Claim-dependency mapping that names which public claims rely on the automation.

Until this record exists and is current, the release automation control remains assigned but not implemented, and XPLAT-007 public cutover and release-claim readiness fail for any claim that depends on it.

## Downstream Handoff

| Surface | Owns | Acceptance gate from XPLAT-003 |
|---|---|---|
| XPLAT-004 | Runner source, Go module and toolchain policy, pinned build input evidence, native artifact build inputs, checksum generation, manifest generation, applicable runner vulnerability scans, and runtime-info plus preflight artifact-integrity fields. | Runner-foundation readiness fails when required evidence is missing, stale, or has unresolved actionable high and critical findings. Unknown or unverified pinned input fields remain evidence gaps. |
| XPLAT-007 | Generated payload source-to-dist gate, checksum and manifest metadata propagation evidence, generated drift evidence, consumer verification guidance, checksum mismatch remediation, native UAT evidence, per-artifact claim readiness, public docs and release-note claim boundaries, and public claim audit. | Public cutover and claims fail when evidence, checksums, manifest, metadata propagation, scan summaries and exceptions, consumer guidance, mismatch remediation, preflight and version evidence, public-claim audit, per-artifact readiness, or native UAT evidence is missing or stale. Consumer checksum guidance must cover each claimed target platform without pre-UAT native support claims. Partial readiness may be claimed only for explicitly ready artifacts and platforms. |
| Release automation | Publication-time evidence once later specs wire it in. | Not edited in XPLAT-003. Any claim depending on release automation fails until the earliest downstream implementing surface records acceptance evidence with control ID, gate location, release inputs and outputs, current pass or fail evidence, and claim-dependency mapping. |
| Public docs and release notes | Implemented-and-verified claim wording only. | Claims about unimplemented signing, SBOMs, provenance, reproducibility, audit, marketplace-enforced verification, cryptographic trust-chain verification, or native platform support are rejected or rewritten as deferred roadmap language. |

## Re-check After Design

| Check | Result |
|---|---|
| First-release controls have owners | Pass: all baseline controls map to XPLAT-004, XPLAT-007, or later release and docs surfaces. |
| Release automation claim gate is explicit | Pass: assigned release automation controls are not claimable until downstream acceptance evidence proves the gate is implemented and wired into publication. |
| Source-to-dist metadata flow is explicit | Pass: XPLAT-007 must prove checksum and manifest metadata presence, equality, and freshness across source, generated Claude payload, and generated Codex payload roots. |
| Checksum mismatch remediation is explicit | Pass: consumer guidance must fail closed, tell consumers not to rely on mismatched artifacts, collect mismatch facts, and require fresh maintainer evidence before re-acceptance. |
| Release-readiness and claim-audit retention is explicit | Pass: public-claim evidence needs durable non-sensitive summaries beyond scan output and short-retention logs. |
| Partial artifact publication is deterministic | Pass: claims are evaluated per artifact and platform; incomplete, stale, mismatched, or unpublished claimed artifacts are excluded or block the claim set. |
| Deferred controls remain explicit | Pass: signatures, SBOM, provenance and attestations, reproducible builds, formal audit, marketplace-enforced verification, and cryptographic trust-chain verification remain deferred unless promotion evidence appears. |
| No implementation scope slipped in | Pass: plan artifacts describe controls and evidence only. |
| Public claim boundary is strict | Pass: only implemented-and-verified controls may be claimed. |
