# Implementation Plan: Supply-Chain Security and Consumer Trust Model

**Branch**: XPLAT-003 feature branch | **Date**: 2026-06-27 | **Spec**: `specs/xplat-003-supply-chain-security-and-consumer-trust-model/spec.md`

**Input**: Feature specification from `specs/xplat-003-supply-chain-security-and-consumer-trust-model/spec.md`, setup design concept from `docs/ai/specs/.process/XPLAT-003-design-concept.md`, and plan prompt from `docs/ai/specs/.process/XPLAT-003-workflow.md`.

## Summary

XPLAT-003 is a decision spike that records a first-release supply-chain and
consumer-trust baseline for the amended Python standard-library
`speckit-pro-runner` selected by XPLAT-002 on 2026-06-28. Official Claude Code
and OpenAI Codex documentation is an explicit planning input: plugins and skills
can package scripts/executables and MCP/hook surfaces, but those docs do not by
themselves guarantee arbitrary user-host runtimes. The accepted runtime
prerequisite comes from official Spec Kit / `specify`, which requires Python
3.11+. The plan produces decision artifacts only: no runner implementation,
helper port, generated payload rebuild, release workflow edit, or public native
support claim.

The first-release baseline is:

- Source-to-dist integrity evidence for generated plugin payloads.
- Python standard-library build, test, eval, payload, and release-readiness gates
  for shipped plugin behavior; current Bash gates are transitional evidence
  only and must not remain the final release gate.
- Official platform capability evidence separating documented Claude/Codex
  plugin surfaces from undocumented user-runtime assumptions.
- Installed-user runtime dependency boundaries: official Spec Kit / `specify`
  and Python 3.11+ are allowed product prerequisites, but public claims must not
  require users to install Go, Rust, Zig, Node, Bash, `jq`, package managers,
  WSL, Git Bash, PowerShell helper scripts, `pip install`, virtualenv
  restoration, or network package restoration after plugin cache population.
- Codex install-completeness evidence that treats required custom-agent TOML
  registration as separate from plugin skill installation.
- Metadata propagation evidence proving checksum and runner manifest paths are present, equal, and fresh across source, generated Claude payload, and generated Codex payload roots before XPLAT-007 cutover.
- Source-integrity and generated-payload evidence for the packaged Python
  runner source and any thin launcher metadata.
- Runner preflight evidence for Python 3.11+, `specify`, plugin root,
  installed-cache context, and operation-specific prerequisites.
- Vulnerability scanning that fails readiness on unresolved actionable high or critical findings, with documented exceptions for non-actionable findings.
- Consumer-local verification through runner identity and preflight output plus
  Python standard-library checksum comparison.
- Closed consumer remediation for checksum mismatches: consumers do not rely on the runner file, record mismatch facts in a report, and wait for fresh maintainer evidence.
- Durable non-sensitive retention of release-readiness and public-claim audit summaries beyond scan evidence alone.
- Per-runner-file and per-platform claim readiness so partial publication cannot imply unsupported platform claims.
- Public docs and release notes limited to controls that are implemented and verified.
- Split ownership: XPLAT-004 owns runner source, preflight, prerequisite, and
  scan controls; XPLAT-007 owns generated payload cutover, consumer guidance,
  native UAT, and public claim readiness; release automation owns
  publication-time evidence only when a later spec wires it in.

## Technical Context

**Language and Version**: Not applicable for this phase. Downstream runner
implementation is described as Python 3.11+ standard-library source aligned with
official Spec Kit / `specify` prerequisites. Go, Rust, Zig, bundled Node,
embedded Python, and other runtime shapes are rejected for XPLAT.

**Primary Dependencies**: Existing repository Markdown and current SpecKit helper
scripts only. No new runtime dependency; current Bash validation scripts are
transitional for XPLAT-003 review and must be replaced by Python
standard-library gates before XPLAT-007 release readiness.

**Storage**: Checked-in specification artifacts under `specs/xplat-003-supply-chain-security-and-consumer-trust-model/`.

**Testing**: Static specification validation only for this phase: marker counts,
G7 task completion, spec-index freshness, diff whitespace, and diff scope
review. The current repo commands are Bash-backed; this plan records them as
current validation only, not as the XPLAT final gate.

**Target Platform**: Decision applies to future packaged Python runner source
and thin launch metadata for Windows, macOS, and Linux, but this phase does not
build or claim native platform support.

**Project Type**: Claude Code and Codex plugin marketplace decision artifact.

**Performance Goals**: Not applicable. Release-readiness evidence must be deterministic and reviewable, not performance-bound.

**Constraints**:

- One decision spike, not implementation.
- Use XPLAT-001 supply-chain rubric and the amended XPLAT-002 Python runner
  handoff as source evidence.
- Use official Claude Code and OpenAI Codex documentation as the authority for
  plugin, skill, hook, MCP, script, executable, and custom-agent surfaces.
- Do not infer user-host runtime availability from plugin `scripts/` support,
  local host probes, or repository tooling. The selected Python runtime must be
  verified through the official Spec Kit / `specify` prerequisite boundary and
  fail closed when missing. Non-Python runtimes and compiled binaries are not
  XPLAT fallback paths.
- Do not edit release automation in XPLAT-003.
- Do not build `speckit-pro-runner`, port helpers, change active invocation paths, or rebuild generated payloads.
- Do not claim signatures, SBOMs, provenance or attestations, reproducible builds, formal audit, marketplace-enforced verification, cryptographic trust-chain verification, or native platform support before those controls are implemented and verified.
- Do not treat Python support as public-ready, start XPLAT-004 runner
  implementation, or authorize XPLAT-007 public cutover until preflight,
  source-integrity, installed-cache invocation, and generated-payload evidence
  are implemented downstream.

## Python Confidence Boundary

XPLAT-003 treats Python as the correct implementation substrate, not as already
proven release support. Confidence is high because official Spec Kit /
`specify` requires Python 3.11+ and the selected runner uses only stdlib APIs:

- Python as the universal dependency: high, approximately 90%.
- Python stdlib runner behavior once launched: high, approximately 85-90%.
- Full Claude/Codex installed-plugin journey today: medium, approximately
  65-75%, because implementation and UAT proof remain downstream.

XPLAT-004 must close the interpreter-discovery and installed-cache launch gap
for Windows, macOS, and Linux. XPLAT-007 must close the generated-payload,
consumer guidance, active Python gate, and full workflow UAT gaps before public
support claims can pass.

**Scale and Scope**: One spec directory; 0 production LOC; decision records and contracts only.

**Reviewability Budget**: Setup gate returned warning status: `reviewable_loc=250`, `production_files=4`, `total_files=10`, `primary_surface_count=2`, warning `primary surfaces 2 exceeds warn threshold 1`, no blockers. After the official-doc/rejected-runtime additions, tasks-mode reviewability reports a size-only block (`reviewable_loc=1000`, `total_files=31`) because the task estimator counts task and file tokens broadly. The actual diff-mode PR gate remains warning-only with `reviewable_loc=0`, `production_files=0`, `total_files=24`, and no blockers. XPLAT-003 remains one decision spike because it records one security and trust model and assigns downstream controls without implementation changes.

## Declared File Operations

- NEW specs/xplat-003-supply-chain-security-and-consumer-trust-model/plan.md
- NEW specs/xplat-003-supply-chain-security-and-consumer-trust-model/research.md
- NEW specs/xplat-003-supply-chain-security-and-consumer-trust-model/data-model.md
- NEW specs/xplat-003-supply-chain-security-and-consumer-trust-model/contracts/supply-chain-control-contract.md
- NEW specs/xplat-003-supply-chain-security-and-consumer-trust-model/quickstart.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Result |
|---|---|---|
| Plugin Structure Compliance | No runner source files, generated payload changes, plugin invocation changes, or release workflow changes. | Pass: phase outputs are spec artifacts only. |
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
- XPLAT-002 amended Python runner handoff implications, with Go/Rust/Zig
  preserved only as rejected historical evidence.
- Official Claude Code and OpenAI Codex platform capability findings.
- Runtime amendment implications for Python stdlib source and rejected
  alternatives such as Go, Rust, Zig, bundled Node, embedded Python, source
  scripts, Bash, `jq`, package managers, WSL, and Git Bash.
- First-release versus deferred hardening decisions.
- Vulnerability actionability and exception policy.
- Scan evidence freshness and staleness blockers.
- Python runner source, prerequisite, preflight, and installed-cache evidence
  requirements.
- Python standard-library replacement requirement for active Bash build, test,
  eval, payload, and release-readiness gates that validate or publish shipped
  plugin behavior.
- Consumer-local verification boundary.
- Public claim allowed and prohibited language boundary.

Open research result: no deferred cryptographic hardening control is promoted to first-release required in XPLAT-003. Checksums, manifest, scan policy, source-to-dist evidence, consumer verification, official platform capability evidence, runtime dependency separation, Codex install-completeness evidence, and truthful claims are enough for the first public release baseline.

Runtime-decision status: the XPLAT-002 runtime choice has been amended to
Python. XPLAT-004 and XPLAT-007 must consume the amended Python contract and
must not consume stale Go/Rust/Zig/native-binary assumptions.

## Phase 1 Design Artifacts

`data-model.md` defines the decision entities: control decision, owner assignment, artifact manifest, checksum entry, source-to-dist evidence, vulnerability scan evidence, exception record, public claim boundary, and release-readiness evidence.

`contracts/supply-chain-control-contract.md` defines the normative evidence shapes for downstream specs:

- Control decision records.
- Python runner source, prerequisite, preflight, and installed-cache evidence
  records.
- Platform capability evidence records.
- Runtime dependency boundary records.
- Install completeness evidence records for Claude and Codex.
- SHA-256 checksum file format.
- Runner file manifest fields.
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

XPLAT-003 defines evidence contracts only. XPLAT-004 records and implements
runner source, prerequisite, and installed-cache evidence. XPLAT-007 consumes
accepted evidence for final cutover, Python release-readiness gating,
consumer-local verification guidance, and public wording after native UAT
passes.

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

The selected Python runner must ship runner source and launcher metadata in the
plugin payloads, rely only on the official Spec Kit / `specify` prerequisite
boundary, and fail closed through prerequisite diagnostics when Python or
`specify` is unavailable. A non-Python runtime must not be introduced as an
XPLAT fallback.

### Scan Evidence Freshness Gate

Required scan evidence records include:

| Field | Required |
|---|---|
| Scan tool or command | Yes |
| Scanner version or vulnerability database timestamp | Yes |
| Scan scope | Yes |
| Target source revision | Yes |
| Dependency manifest or sum snapshot | Yes |
| Build input snapshot | Yes |
| Generated runner-file identifier, when applicable | Yes |
| Run timestamp | Yes |
| Result and severity summary | Yes |
| Actionable high and critical count | Yes |
| Exception record references, when applicable | Conditional |
| Owner surface | Yes |
| Freshness expiry | Yes |

Readiness fails when evidence is missing, stale, predates the source,
dependency policy, build input, scanner database, or runner file it covers,
crosses a public release boundary without re-approval, or has unresolved
actionable high and critical findings. The default freshness window is 7
calendar days before readiness review unless a stricter source, dependency
policy, runner file, or scanner change invalidates the evidence sooner.

### Pinned Release Input Evidence

For the selected Python runner, XPLAT-004 must record:

- Python minimum version policy.
- Interpreter discovery order and exact interpreter used.
- `specify` discovery and version evidence.
- Stdlib-only dependency policy.
- Runner source path and source revision.
- Generated Claude and Codex payload paths.
- Runner preflight output for Windows, macOS, and Linux installed-cache
  contexts.
- Release package input list.
- Source revision used to package the runner.
- Generated runner source and launcher payload-relative paths.
- Source-integrity metadata or checksums for runner payload files where
  XPLAT-004/XPLAT-007 require them.
- First-release vulnerability scan inputs and evidence references.

Unknown or unverified values are evidence gaps and cannot be treated as accepted controls.

Compiled binaries, bundled runtimes, and alternate source-script runtimes are
out of scope for XPLAT and must not be represented as pinned-input alternatives.

### Generated Payload Metadata Propagation Gate

XPLAT-007 must prove that checksum and runner file manifest metadata produced
by XPLAT-004 flows into the payloads that public installs consume:

```text
XPLAT-004 runner file outputs
-> source checksum and manifest paths
-> generated Claude metadata paths
-> generated Codex metadata paths
-> XPLAT-007 cutover evidence
```

The gate must record producer evidence refs, source metadata paths, generated Claude metadata paths, generated Codex metadata paths, equality rule, freshness rule, and failure rule. Missing metadata, stale metadata, or unequal source/generated metadata fails public cutover and release-claim readiness. XPLAT-003 does not create metadata files or rebuild payloads.

### Consumer-Local Checksum Verification Guidance

XPLAT-007 must provide platform-specific command shapes for every runner file it
intends to claim after native UAT passes:

| Platform | SHA-256 command shape |
|---|---|
| Windows | `<python> -c "import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())" <runner-path>` |
| macOS | `<python> -c "import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())" <runner-path>` |
| Linux | `<python> -c "import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())" <runner-path>` |

Guidance must describe metadata lookup from the installed payload or
release-provided offline metadata and resolve `<python>` from the preflight
interpreter. If checksum metadata or the interpreter is unavailable, guidance
must fail closed with an explicit "verification metadata unavailable" state
instead of instructing users to fetch dependencies, clone the source repository,
run Bash, use `jq`, use PowerShell helper scripts, or restore packages from the
network.

These command shapes are XPLAT-007 guidance requirements, not current public native-support claims.

### Checksum Mismatch Remediation

XPLAT-007 consumer guidance must treat a computed checksum that differs from
the matching published checksum entry as a closed verification failure. The
consumer-facing path must say not to rely on that runner file for support claims
and must collect enough information for maintainers to investigate: runner file
path, target platform, runner identity or preflight output, checksum metadata
source, expected checksum, computed checksum, plugin version or release
boundary, and reporting path.

The guidance must not ask consumers to repair a mismatch by cloning source,
restoring packages, fetching replacement dependencies from the network, running
Bash or `jq`, or trusting runner self-verification alone. Maintainers may accept
the runner file again only after fresh XPLAT-004 runner-file, checksum, and
manifest evidence and XPLAT-007 source-to-dist, claim-audit, and
consumer-guidance evidence are current for the affected runner file.

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

### Partial Runner-File Publication Gate

Public cutover and release claims are evaluated per claimed runner file and
platform. A platform runner file may be ready only for its own claim scope when
its checksum, manifest, runtime-info and preflight, native UAT, source-to-dist,
scan, exception, release-automation, and claim-audit evidence are current.

If an intended platform runner file is missing, stale, mismatched, unpublished,
or lacks required evidence, XPLAT-007 must either exclude that runner file and
platform from public claims with an explicit deferred or not claimable record or
keep the claim set blocked. One passing platform never implies Windows, macOS,
and Linux support for other platforms.

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
| XPLAT-004 | Python runner source, stdlib-only dependency policy, official Spec Kit / `specify` prerequisite preflight, pinned input evidence, checksum generation, manifest generation, applicable runner vulnerability scans, runtime-info plus preflight source-integrity fields, and Python test/eval runner patterns. | Runner-foundation readiness fails when required evidence is missing, stale, or has unresolved actionable high and critical findings. Unknown or unverified pinned input fields remain evidence gaps. |
| XPLAT-007 | Generated payload source-to-dist gate, checksum and manifest metadata propagation evidence, generated drift evidence, Python replacements for active Bash build/test/eval/release-readiness gates, consumer verification guidance, checksum mismatch remediation, native UAT evidence, per-runner-file claim readiness, public docs and release-note claim boundaries, and public claim audit. | Public cutover and claims fail when evidence, checksums, manifest, metadata propagation, scan summaries and exceptions, consumer guidance, mismatch remediation, preflight and version evidence, public-claim audit, per-runner-file readiness, native UAT evidence, or active Python test/eval gate evidence is missing or stale. Consumer checksum guidance must cover each claimed target platform without pre-UAT native support claims. Partial readiness may be claimed only for explicitly ready runner files and platforms. |
| Release automation | Publication-time evidence once later specs wire it in. | Not edited in XPLAT-003. Any claim depending on release automation fails until the earliest downstream implementing surface records acceptance evidence with control ID, gate location, release inputs and outputs, current pass or fail evidence, and claim-dependency mapping. |
| Public docs and release notes | Implemented-and-verified claim wording only. | Claims about unimplemented signing, SBOMs, provenance, reproducibility, audit, marketplace-enforced verification, cryptographic trust-chain verification, or native platform support are rejected or rewritten as deferred roadmap language. |

## Re-check After Design

| Check | Result |
|---|---|
| First-release controls have owners | Pass: all baseline controls map to XPLAT-004, XPLAT-007, or later release and docs surfaces. |
| Release automation claim gate is explicit | Pass: assigned release automation controls are not claimable until downstream acceptance evidence proves the gate is implemented and wired into publication. |
| Source-to-dist metadata flow is explicit | Pass: XPLAT-007 must prove checksum and manifest metadata presence, equality, and freshness across source, generated Claude payload, and generated Codex payload roots. |
| Checksum mismatch remediation is explicit | Pass: consumer guidance must fail closed, tell consumers not to rely on mismatched runner files, collect mismatch facts, and require fresh maintainer evidence before re-acceptance. |
| Release-readiness and claim-audit retention is explicit | Pass: public-claim evidence needs durable non-sensitive summaries beyond scan output and short-retention logs. |
| Partial runner-file publication is deterministic | Pass: claims are evaluated per runner file and platform; incomplete, stale, mismatched, or unpublished claimed runner files are excluded or block the claim set. |
| Deferred controls remain explicit | Pass: signatures, SBOM, provenance and attestations, reproducible builds, formal audit, marketplace-enforced verification, and cryptographic trust-chain verification remain deferred unless promotion evidence appears. |
| No implementation scope slipped in | Pass: plan artifacts describe controls and evidence only. |
| Public claim boundary is strict | Pass: only implemented-and-verified controls may be claimed. |
