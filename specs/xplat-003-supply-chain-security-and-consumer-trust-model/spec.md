# Feature Specification: Supply-Chain Security and Consumer Trust Model

**Feature Branch**: `codex/xplat-003-supply-chain-security-and-consumer-trust-model`

**Created**: 2026-06-27

**Status**: Complete - runtime choice amended to Python standard-library runner

**Input**: User description: "Choose the practical first-release security baseline and deferred hardening backlog for the XPLAT runner before XPLAT-004 builds the runner and before XPLAT-007 makes public release claims."

## Runtime Choice Amendment Notice

XPLAT-002 originally recorded a Go native runner as the selected runtime. That
choice has now been amended on this PR: the active first-release runtime is a
Python standard-library runner aligned with the official Spec Kit / `specify`
prerequisite boundary.

The Go-native analysis remains preserved only as historical rejected evidence
explaining why the decision changed. It is not a downstream implementation
target, compatibility adapter, or contingency plan for XPLAT.

Downstream XPLAT-004 runner implementation, XPLAT-007 cutover, and public
support claims now depend on proving this Python model:

- SpecKit-Pro may require a healthy official Spec Kit / `specify` installation.
- The official Spec Kit prerequisite boundary includes Python 3.11+.
- The runner must use Python standard-library APIs for JSON, paths, filesystem,
  and subprocess behavior.
- The runner must not use Bash, Git Bash, WSL, PowerShell helper scripts, `jq`,
  Go, Rust, Zig, Node, `pip install`, virtualenv restoration, network package
  restoration, or plugin-only third-party Python packages after plugin install.
- Doctor/preflight must verify Python 3.11+, `specify`, installed plugin root,
  and any operation-specific tools before meaningful work continues.

Official platform documentation now constrains this decision explicitly:

- Claude Code plugins support packaged skills, agents, hooks, MCP servers,
  scripts, and `bin/` executables. Claude skills may include optional scripts.
  These docs support packaged executable/script surfaces, but they do not
  guarantee arbitrary plugin language runtimes by themselves.
- OpenAI Codex plugins support packaged skills, apps, MCP servers, lifecycle
  hooks, and skill `scripts/`. Codex custom subagents are documented as
  `.codex/agents/*.toml` or `~/.codex/agents/*.toml`, not as a generic Codex
  plugin `agents/` directory. Codex docs likewise do not guarantee arbitrary
  language runtimes on every installed plugin host by themselves.

Therefore the runtime decision must be reviewed as a packaging and dependency
contract, not as a preference for a language. The accepted prerequisite is the
official Spec Kit / `specify` environment. Every other implementation runtime
or package-restoration dependency must be removed from the XPLAT plan or
diagnosed as a non-XPLAT requirement.

## Clarifications

### Session 1: First-release Control Boundaries

- Q: What is the minimum first-release control baseline that blocks public
  cutover? A: The practical baseline is selected-runtime pinned release inputs,
  vulnerability scanning, generated payload source-to-dist integrity, published
  checksums, consumer-local verification, official platform capability evidence,
  installed-user runtime dependency separation, and truthful public claims.
- Q: Which controls stay deferred hardening, and what evidence can promote them
  to first-release required? A: Signatures, SBOMs, provenance/attestations,
  reproducible builds, formal audit, and cryptographic trust-chain verification
  stay deferred unless concrete first-release evidence shows enforced
  marketplace/install support, release automation that can produce and verify
  the runner file, a public claim that cannot be made truthfully without the
  control, or a blocking consumer/adoption requirement.
- Q: How should first-release controls be split across owner surfaces? A:
  XPLAT-004 owns runner source, dependency policy, runner-file preflight/version,
  checksum generation, and applicable scan controls. XPLAT-007 owns generated
  payload integrity, consumer verification guidance, release-note/docs claim
  boundaries, native support readiness, and cutover evidence. Release
  automation owns publication-time evidence only where later specs wire it in.
- Q: What evidence must exist before XPLAT-007 can make public supply-chain or
  native-support claims? A: Runner preflight/version evidence, checksums for
  each packaged runner file, consumer verification instructions, source-to-dist
  payload gate output, vulnerability scan results or exception records, and
  public-claim audit evidence.
- Q: How should high/critical vulnerability scan findings affect public cutover?
  A: Actionable high/critical findings block release readiness. Non-actionable
  exceptions must record the finding source and severity, affected
  artifact/version, rationale, compensating control, approving maintainer, and
  expiry or review condition.

### Session 2: Runner Source Integrity And Consumer Verification

- Q: What integrity metadata should first-release Python runner files use?
  A: XPLAT-004/XPLAT-007 may use SHA-256 metadata for runner source and launcher
  files, with stable payload-relative paths and 64 lowercase hexadecimal
  checksums so maintainers and consumers can use common SHA-256 verification
  tools when checksum guidance is provided.
- Q: What fields must the runner source manifest include? A: Publish manifest
  metadata with `schema_version`, `plugin_name`, `plugin_version`,
  `runner_name`, `runner_version`, `contract_version`, `source_revision`,
  `python_minimum_version`, `specify_required`, `checksum_algorithm`, and runner
  file entries containing payload path, size, checksum when used, and
  verification metadata.
- Q: What source-to-dist evidence should prove generated Claude/Codex payload
  integrity? A: XPLAT-007 must replace the current Bash payload builder with a
  Python standard-library source-to-dist gate, for example
  `python3 scripts/build_plugin_payloads.py`, then verify no generated drift
  under `dist/claude/speckit-pro`, `dist/codex/speckit-pro`,
  `.claude-plugin/marketplace.json`, and
  `.agents/plugins/marketplace.json`, recording the command, exit status,
  source inputs, generated roots, and checksum/manifest paths. The current Bash
  builder is transitional evidence only and is not a final release gate.
- Q: How should compiled per-platform binaries be distributed through Claude
  and Codex marketplaces? A: They should not be distributed as part of XPLAT.
  Because SpecKit itself requires Python 3.11+, XPLAT must use Python
  standard-library runner source and must not carry a Go/Rust/Zig or native
  binary contingency path.
- Q: What extra `runtime-info` and `preflight` fields are required for consumer
  verification? A: Preserve the XPLAT-002 fields and add source-integrity
  pointers: runner source path, runner file ID, manifest path, checksum file
  path when used, checksum algorithm, expected checksum when used, and
  verification status. The response distinguishes installed-cache context from
  source-only context and does not claim external trust-chain verification.
- Q: What local consumer verification command shape should docs require? A: Use
  a two-step local path: run runner identity/preflight first, then compare the
  installed runner-file hash against the published checksum entry with a Python
  standard-library checksum command shape. OS-native hash commands may be
  supplemental only. The verification path must not rely on runner
  self-verification alone and must not require `jq`, Bash, PowerShell helper
  scripts, a source checkout, or network package restoration.

### Session 3: Vulnerability Policy And Public Claims

- Q: How should "actionable high/critical" be defined? A: A finding is
  actionable when scanner severity is high/critical, or CVSS is high/critical
  when available, and the finding affects the first-release trust boundary:
  runner source, stdlib prerequisite/preflight policy, build/release inputs,
  packaged runner files, integrity metadata, generated payloads, marketplace
  manifests, or release evidence. It must also be reachable, shipped, or capable
  of changing release output or public claims.
  False positives, unreachable code,
  non-shipped paths, repo-only/test/archive/docs-only paths, or already
  mitigated artifact-boundary findings are non-actionable only with an
  exception record.
- Q: What must a vulnerability exception record contain and when does it expire?
  A: It records scanner/source, tool version or vulnerability database
  timestamp, advisory ID when available, severity, affected
  artifact/dependency/version/platform, actionability classification,
  rationale, reachability or false-positive evidence, compensating control,
  approving maintainer, approval date, and expiry/review condition. It expires
  before each public release unless re-approved with current evidence, and
  immediately when the affected artifact, dependency graph, platform, toolchain,
  scanner version/database, advisory status, severity, exploitability, or
  compensating control changes.
- Q: How long should scan evidence be retained? A: Durable, non-sensitive
  release-readiness summaries and exception records are retained in the owning
  spec, PR packet, or release-readiness artifact. Raw scanner output is not
  committed by default; once automation exists, it is uploaded as CI artifacts
  with 30-day retention. Raw log excerpts may be committed only when necessary
  to support an exception record, and must be scoped or redacted to the relevant
  finding.
- Q: What is the exact release-blocking behavior? A: XPLAT-003 records policy,
  control ownership, and acceptance gates only. XPLAT-004 blocks
  runner-foundation readiness when required runner/source/dependency/artifact
  scan evidence is missing, stale, or has unresolved actionable high/critical
  findings. XPLAT-007 blocks public cutover and release-note/docs claims when
  scan evidence, exceptions, checksums, manifest, source-to-dist evidence,
  consumer verification guidance, public-claim audit, runtime preflight/version
  evidence, or native UAT evidence is missing or stale. Current release
  workflow implementation changes stay out of XPLAT-003.
- Q: What docs/release-note claims are allowed versus forbidden? A: Allowed
  claims are limited to implemented-and-verified controls for the release:
  packaged Python runner source files and any thin launchers, SHA-256 checksum
  file and manifest, local preflight/version plus checksum verification,
  source-to-dist payload gate, and vulnerability scanning with no unresolved
  actionable high/critical findings.
  Forbidden until implemented and verified: signed binaries/signatures, SBOMs,
  provenance/attestations, reproducible builds, formal audit/certification,
  marketplace-enforced verification, cryptographic trust-chain verification, and
  native Windows/macOS/Linux support. Roadmap wording may describe these as
  planned or deferred hardening, but not as provided, guaranteed, certified,
  enforced, or trusted today.

### Session 4: Runtime Decision Amendment

- Q: Should XPLAT-003 continue as if the XPLAT-002 Go runtime decision is
  accepted? A: No. XPLAT-002 is amended on this PR. The active first-release
  runtime is now a Python standard-library runner aligned with the official
  Spec Kit / `specify` prerequisite boundary.
- Q: Why was Go selected originally? A: XPLAT-002 selected Go because Python was
  evaluated only against Claude/Codex platform runtime guarantees. The amended
  decision recognizes that SpecKit-Pro can require the official Spec Kit /
  `specify` prerequisite boundary, which includes Python 3.11+.
- Q: Could Go, Rust, or Zig still satisfy the same XPLAT goal? A: No. Once the
  official Spec Kit prerequisite boundary is accepted, compiled binaries add a
  second implementation/distribution model without improving the XPLAT user
  journey. They remain rejected historical candidates, not XPLAT fallbacks.
- Q: What confidence level do we have that Python will work consistently across
  Windows, macOS, and Linux? A: Planning confidence is high, but not complete
  release evidence. Python as the universal dependency is approximately 90%
  confidence because it is already required by official Spec Kit / `specify`.
  Python stdlib runner behavior after launch is approximately 85-90%
  confidence. The full Claude/Codex installed-plugin user journey remains
  approximately 65-75% confidence until XPLAT-004 proves interpreter discovery
  and installed-cache launch, and XPLAT-007 proves generated payload cutover and
  platform UAT.
- Q: What do official Claude Code and OpenAI Codex docs change? A: They confirm
  plugin/skill/hook/MCP/script packaging surfaces, but they do not guarantee
  arbitrary user-host runtimes. They also make Codex custom-agent installation a
  separate `.codex/agents/*.toml` completeness concern rather than a generic
  bundled plugin-agent surface.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Maintainer Reviews Trust Baseline (Priority: P1)

A maintainer can read one decision record that separates first-release controls
from deferred hardening for the selected Python runner model and its generated
plugin payloads.

**Why this priority**: XPLAT-004 cannot build a release-ready runner until maintainers agree which controls block first release and which controls are documented follow-up hardening.

**Independent Test**: A reviewer can inspect the specification and confirm every evaluated trust control is categorized as first-release, deferred hardening, or explicitly out of scope, with rationale.

**Acceptance Scenarios**:

1. **Given** XPLAT-002 is amended to a Python standard-library runner, **When**
   a maintainer reads the XPLAT-003 specification, **Then** the first-release
   baseline includes Python/stdlib prerequisite verification, generated-payload
   integrity, source integrity, vulnerability scanning, consumer-local
   verification, and truthful public claims.
2. **Given** heavier controls such as signing, provenance, reproducible builds, SBOMs, or audit are evaluated, **When** the maintainer reviews their status, **Then** each control is identified as deferred hardening unless explicitly moved into the first-release baseline with rationale.
3. **Given** a downstream plan references the XPLAT-003 decision, **When** the maintainer checks the plan, **Then** no downstream work can claim a stronger guarantee than the controls this specification requires.

---

### User Story 2 - Implementer Maps Controls To Owner Specs (Priority: P1)

An implementer can see which selected controls belong to XPLAT-004, XPLAT-007,
release automation, and public documentation for the amended Python runner.

**Why this priority**: The runner foundation, generated payload cutover, and release-readiness work have different owners and acceptance gates.

**Independent Test**: A planner can map each first-release control to a downstream owner spec and verify that no control is left ownerless.

**Acceptance Scenarios**:

1. **Given** XPLAT-004 owns the runner foundation, **When** an implementer reviews the control map, **Then** runner source, stdlib dependency policy, runner-file preflight/version, checksum generation, and applicable vulnerability-scan controls are assigned to XPLAT-004 acceptance gates.
2. **Given** XPLAT-007 owns generated payload cutover and public release readiness, **When** an implementer reviews the control map, **Then** source-to-dist payload integrity, consumer-facing verification guidance, and public docs or release-note claim boundaries are assigned to XPLAT-007 acceptance gates.
3. **Given** a control belongs to release automation rather than the runner itself, **When** the implementer reviews the handoff, **Then** the specification identifies the earliest downstream surface that must implement and verify the control before public release.

---

### User Story 3 - Consumer Understands Local Verification And Limits (Priority: P2)

A consumer or reviewer can understand what they can verify locally after install and which trust guarantees the project intentionally does not claim for first release.

**Why this priority**: Public trust depends on accurate verification guidance and avoiding unsupported security claims.

**Independent Test**: A reviewer can compare draft public wording or release notes against this specification and identify whether every claim is allowed, deferred, or forbidden until implemented.

**Acceptance Scenarios**:

1. **Given** the plugin has a packaged Python runner, **When** a consumer follows the documented local verification path, **Then** they can confirm the runner version, Python/specify prerequisite state, and preflight output.
2. **Given** public documentation or release notes mention supply-chain controls, **When** a reviewer audits the wording, **Then** the wording claims only controls that have implementation and verification evidence.
3. **Given** signing, provenance, reproducible builds, audit, or native support claims are not yet implemented and verified, **When** public wording is reviewed, **Then** those claims are rejected or rewritten as deferred, non-guaranteed roadmap language.

### Edge Cases

- A vulnerability scan reports a high or critical finding that is not actionable because it is unreachable, false positive, or already mitigated by the packaged runner-file boundary.
- A vulnerability scan reports a high or critical finding in repo-only, test, archive, docs-only, or other non-shipped paths that are outside the XPLAT runtime trust boundary.
- Vulnerability scan evidence was clean when produced, but a source revision, dependency snapshot, toolchain, build input, generated artifact, scanner version, vulnerability database timestamp, advisory status, severity, exploitability, or release boundary changed before readiness review.
- A vulnerability exception was approved for one release but the affected runner file, dependency policy, platform, scanner database, advisory status, severity, exploitability, or compensating control changed before the next release.
- Generated Claude and Codex payloads drift from their source inputs after the runner or verification metadata changes.
- Checksum or runner manifest metadata exists in XPLAT-004 outputs but is not present, equal, and fresh in both generated Claude and Codex payload roots before XPLAT-007 cutover.
- Published checksum metadata is missing, stale, or does not match a packaged
  runner source or launcher file.
- A public release or trust claim depends on release automation that has not yet recorded downstream acceptance evidence proving the publication gate is implemented and wired into the release path.
- Consumer checksum guidance exists for one platform family but not for every target runner file that XPLAT-007 intends to claim after UAT.
- Public release wording is prepared before XPLAT-007 native-platform UAT or before the selected controls are implemented.
- A downstream implementation attempts to add signing, SBOM, provenance, reproducible-build, or audit language without corresponding implementation evidence.
- A marketplace install path does not automatically enforce checksums, so consumer-local verification must remain manual and clearly documented.
- A consumer computes a packaged runner source or launcher hash that differs
  from the matching published checksum entry.
- Only some platform runner files have current checksum, manifest, scan,
  preflight, native UAT, source-to-dist, and claim-audit evidence while another
  intended or claimed runner file is missing, stale, mismatched, or
  unpublished.
- Release-readiness or public-claim audit evidence exists only in expiring
  logs, raw workflow output, or unretained generated artifacts without a
  durable non-sensitive summary.
- A downstream implementation assumes a user-installed Go, Rust, Zig, Node,
  Bash, `jq`, package manager, WSL, Git Bash, or network restoration step, or
  assumes Python without verifying the official Spec Kit / `specify`
  prerequisite boundary before workflow execution.
- A downstream implementation ships runner source or launchers in source or
  release assets but does not prove those files and metadata were copied into
  both generated marketplace payload roots before install or claim readiness.
- A downstream implementation keeps Bash-based tests, evals, payload builders,
  or release-readiness checks as active gates for shipped plugin behavior after
  claiming pure Python cutover.
- A runtime alternative such as Rust, Zig, bundled Node, embedded Python, a
  native binary, or a source-script package is substituted into XPLAT. That is
  out of scope; XPLAT is Python stdlib only.
- A Codex install is treated as complete because plugin skills are present, even
  though required Codex custom-agent TOML files are missing from `.codex/agents/`
  or `~/.codex/agents/`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The specification MUST record that XPLAT-002 has been amended from the original Go native runner model to a Python standard-library runner aligned with official Spec Kit / `specify` prerequisites.
- **FR-002**: The specification MUST define the first-release control baseline as Python prerequisite evidence, stdlib-only policy, vulnerability scanning, generated-payload integrity, runner source integrity, consumer-local verification, and truthful public claims.
- **FR-003**: The specification MUST require generated Claude and Codex payload integrity to include a Python standard-library source-to-dist gate that replaces the current Bash payload builder, checks generated payload and marketplace-manifest drift, and records command, exit status, source inputs, generated roots, checksum/manifest paths, and metadata propagation from XPLAT-004-produced checksum and manifest outputs into source and generated Claude/Codex payload roots.
- **FR-004**: The specification MUST require first-release runner source integrity metadata for packaged Python runner source and launcher files where XPLAT-004/XPLAT-007 choose checksum-backed verification.
- **FR-005**: The specification MUST require consumer-local verification guidance that lets a consumer confirm runner version, Python/specify prerequisite state, and preflight output without requiring `jq`, Bash, source checkout, or network package restoration.
- **FR-006**: The specification MUST require vulnerability scans for the Python runner source and generated payload boundary before public release.
- **FR-007**: The vulnerability policy MUST fail release readiness on actionable high or critical findings, where actionability requires high/critical severity plus first-release trust-boundary scope and reachable, shipped, or release-affecting relevance.
- **FR-008**: The vulnerability policy MUST define exception handling for non-actionable findings, including scanner/source, tool version or vulnerability database timestamp, advisory ID when available, severity, affected runner file/dependency policy/version/platform, actionability classification, rationale, reachability or false-positive evidence, compensating control, approving maintainer, approval date, and expiry or review condition.
- **FR-009**: The specification MUST classify signatures, provenance or attestations, reproducible builds, SBOMs, formal audit, and cryptographic trust-chain verification as deferred hardening unless concrete first-release evidence promotes a control into a release requirement.
- **FR-010**: The specification MUST assign runner source, stdlib-only dependency policy, prerequisite preflight/version, source integrity, manifest, and applicable vulnerability controls to XPLAT-004.
- **FR-011**: The specification MUST assign generated-payload source-to-dist integrity, public docs or release-note claim boundaries, consumer-facing verification guidance, runtime-info/preflight evidence, and native support claim readiness to XPLAT-007.
- **FR-012**: The specification MUST identify any release-automation-owned controls and assign them to the earliest downstream spec or release surface that can implement and verify them before public release.
- **FR-013**: Public docs and release notes MUST claim only controls that are implemented and verified.
- **FR-014**: Public docs and release notes MUST NOT claim signing, provenance, reproducible builds, audit, or native Windows/macOS/Linux support before those guarantees have implementation and verification evidence.
- **FR-015**: The specification MUST document the deferred hardening backlog with rationale and promotion conditions, including enforced marketplace/install support, release automation that can produce and verify the runner file, required truthful public claims, or blocking consumer/adoption requirements.
- **FR-016**: The specification MUST preserve XPLAT-001 supply-chain rubric traceability for dependency policy, lockfile discipline, generated payload integrity, vulnerability scanning, provenance, checksums or signatures, SBOM feasibility, consumer-local verification, and release-claim truthfulness.
- **FR-017**: The specification MUST preserve XPLAT-002 handoff traceability for the amended Python runner, including official Spec Kit prerequisite evidence, Python 3.11+ and `specify` preflight, stdlib-only dependency policy, source integrity, and installed-cache verification gaps.
- **FR-018**: The specification MUST exclude runner implementation, helper porting, active invocation path changes, generated payload rebuilds, release automation changes, and public native support claims from XPLAT-003 implementation scope.
- **FR-019**: The first-release runner source manifest MUST identify plugin and runner versions, contract version, source revision, Python minimum version, `specify` prerequisite state, checksum algorithm when used, and per-file payload path, platform applicability, size, checksum, and checksum file when used.
- **FR-020**: Runtime-info or preflight evidence used for consumer verification MUST include runner source-integrity pointers and MUST distinguish installed-cache context from source-only context without claiming external trust-chain verification.
- **FR-021**: Vulnerability exception records MUST expire before each public release unless re-approved from current scan evidence, and MUST expire immediately when the affected runner file, dependency policy, platform, scanner version/database, advisory status, severity, exploitability, or compensating control changes.
- **FR-022**: Scan evidence retention MUST keep durable non-sensitive release-readiness summaries and exception records in spec, PR-packet, or release-readiness artifacts; raw scanner output MUST NOT be committed by default and, once automation exists, MUST be retained as CI artifacts for 30 days.
- **FR-023**: XPLAT-004 readiness MUST fail when required runner/source/dependency-policy scan evidence is missing, stale, or has unresolved actionable high/critical findings.
- **FR-024**: XPLAT-007 public cutover and release-claim readiness MUST fail when scan evidence, exceptions, checksums, manifest, source-to-dist evidence, consumer verification guidance, public-claim audit, runtime preflight/version evidence, or native UAT evidence is missing or stale.
- **FR-025**: Public docs and release notes MUST NOT claim signed binaries, SBOMs, provenance or attestations, reproducible builds, formal audit or certification, marketplace-enforced verification, cryptographic trust-chain verification, or native Windows/macOS/Linux support until each claim is implemented and verified.
- **FR-026**: Vulnerability scan evidence MUST define freshness and staleness for release-readiness review. Evidence is stale when it is older than 7 calendar days at readiness review, predates the source revision, dependency manifest or sum state, toolchain, build input, generated artifact, scanner version or vulnerability database timestamp it claims to cover, or crosses a public release boundary without re-approval.
- **FR-027**: XPLAT-004 Python runner evidence MUST include Python minimum version policy, interpreter discovery order, `specify` discovery and version evidence, stdlib-only dependency policy, source revision, payload source path, generated Claude/Codex payload paths, checksum or source-integrity metadata where applicable, and first-release scan inputs. Unknown or unverified fields are evidence gaps, not accepted controls. Go/Rust/Zig/native-binary evidence is not an XPLAT fallback.
- **FR-028**: XPLAT-007 consumer-local checksum guidance MUST include separate Windows, macOS, and Linux Python standard-library SHA-256 command shapes for every target runner file it intends to claim after UAT, MUST describe how consumers locate checksum metadata from the installed payload or release-provided offline metadata, and MUST fail closed when metadata is unavailable. This guidance MUST NOT require Bash, `jq`, PowerShell helper scripts, source checkout paths, package-manager restoration, or network access after plugin cache population, and MUST NOT imply native platform support before XPLAT-007 UAT evidence exists.
- **FR-029**: Release-automation-owned publication controls MUST remain `assigned_not_implemented` and `not_claimable` until the earliest downstream implementing surface records acceptance evidence with the implementing spec or release surface, control ID, publication gate location, release inputs, generated outputs, latest pass/fail evidence, and claim-dependency mapping. XPLAT-007 public cutover and release-claim readiness MUST fail when a public claim relies on release automation whose acceptance evidence is missing, stale, or not wired into the publication path.
- **FR-030**: XPLAT-007 source-to-dist evidence MUST prove runner source, launcher, checksum, and manifest metadata propagation from XPLAT-004 runtime outputs to checked-in source metadata paths, generated Claude payload metadata paths, generated Codex payload metadata paths, and final cutover evidence. Missing, stale, or unequal metadata across those locations MUST fail public cutover and release-claim readiness.
- **FR-031**: Consumer-local checksum guidance MUST define a computed-versus-published checksum mismatch as a closed verification failure. The guidance MUST tell consumers not to rely on the runner file for support claims, MUST require recording the runner file path, platform, runner identity or preflight output, checksum metadata source, expected checksum, computed checksum, plugin version or release boundary, and reporting path, and MUST NOT instruct consumers to repair the failure through source checkout, package restoration, network fetches, Bash, `jq`, or runner self-verification alone.
- **FR-032**: Release-readiness evidence and public-claim audit evidence MUST retain durable, non-sensitive summaries beyond vulnerability scan summaries and exception records. These records MUST include release boundary, control or claim IDs, evidence references, pass/fail/blocked status, timestamp or source revision, owner surface, known gaps, and approval/status, while raw logs and large generated artifacts MUST NOT be committed by default.
- **FR-033**: Public cutover and release claims MUST be evaluated per claimed runner file and platform. If any claimed runner source or launcher is missing, stale, mismatched, unpublished, or lacks required checksum, manifest, runtime-info/preflight, native UAT, source-to-dist, scan, exception, release-automation, or claim-audit evidence, that file/platform MUST be excluded from claims or the claim set MUST remain blocked; one passing platform MUST NOT imply Windows/macOS/Linux support for other platforms.
- **FR-034**: XPLAT-003 MUST label Go-specific and compiled-binary controls as rejected historical controls and MUST NOT let downstream XPLAT-004 or XPLAT-007 consume stale Go/Rust/Zig/native-binary assumptions while Python is the selected runtime.
- **FR-035**: The specification MUST separate official platform packaging support from runtime/toolchain selection. Claude Code and Codex plugin support for skills, scripts, hooks, MCP servers, and install payloads MUST NOT be treated as proof that user hosts provide Go, Rust, Zig, Node, Bash, `jq`, package managers, WSL, Git Bash, or network restoration after plugin cache population. Python is allowed only through the official Spec Kit / `specify` prerequisite boundary and must be verified by preflight.
- **FR-036**: The selected first-release runtime MUST require no user-side build toolchain or package restoration after plugin cache population except the documented SpecKit-Pro prerequisite boundary verified by preflight.
- **FR-037**: Go, Rust, Zig, or another native-build toolchain MUST NOT be treated as an XPLAT runtime, fallback, or compatibility adapter. Compiled binaries are rejected for this XPLAT lane because SpecKit already requires Python.
- **FR-038**: XPLAT-007 install-completeness and source-to-dist readiness MUST distinguish Claude Code plugin agents from Codex custom-agent TOML installation. A Codex install that has plugin skills but lacks required `.codex/agents/*.toml` or `~/.codex/agents/*.toml` agent registrations MUST remain incomplete until autoheal or explicit install guidance repairs it.
- **FR-039**: XPLAT-004/XPLAT-007 MUST record runner-file distribution and install-model evidence for each claimed platform and runtime surface, including distribution mode, runner source path, generated Claude payload path, generated Codex payload path, launcher surface, post-install download requirement, launch metadata policy, checksum/manifest metadata, and official-doc basis. Native-support claims MUST fail when runner files exist only in source or release assets but are missing, stale, or unverifiable in generated marketplace payload roots. Native artifact fields such as executable permission or Windows `.exe` behavior are out of scope.
- **FR-040**: XPLAT-007 MUST replace active Bash-based build, test, eval, payload, and release-readiness gates that validate or publish shipped plugin behavior with Python standard-library gates. Remaining Bash may be historical/archive text, unrelated shell wrappers that dispatch to Python without validation logic, or temporary parity evidence that is explicitly outside the final release gate.

### Reviewability Notes *(if applicable)*

- XPLAT-003 is a decision spike. It may create or update specification artifacts and downstream handoff language, but it does not change runtime behavior, generated payloads, runner source, release automation, or public docs.
- Any later implementation PR that crosses more than one owner surface must carry its own reviewability budget and traceability back to the XPLAT-003 control map.
- The accepted setup reviewability warning remains in force for this decision spike: two primary surfaces were reported with no blockers because the same trust model spans docs/process evidence and future runner ownership. Tasks-mode reviewability is a coarse planning signal; the post-update tasks-mode result is a size-only block caused by estimator task/file-token counts, while the actual diff-mode PR gate remains warning-only with 0 production LOC and no blockers.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: future runner/security ownership handoff only; no implementation files
- **Projected reviewable LOC**: 0 production/runtime LOC; setup gate recorded 250 projected reviewable LOC for decision artifacts
- **Projected production files**: 0 runtime production files; setup gate path classification reported 4 production-file tokens because contract paths are classified as API-like review inputs
- **Projected total files**: 8-10 spec artifacts for the decision spike, plus task/checklist process artifacts generated by SpecKit
- **Budget result**: accepted setup warning, no blockers; tasks-mode warning is advisory unless a later real diff-mode gate blocks on actual changed files
- **Split decision**: This remains one decision-spike spec because it records one security/trust model and assigns downstream controls without implementation changes.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Security Control Decision**: A trust or verification control evaluated by XPLAT-003, including first-release or deferred classification, rationale, owner surface, and evidence requirement.
- **First-Release Baseline**: The minimum set of controls that must be implemented and verified before public release claims can rely on the selected Python runner.
- **Runner File Manifest**: A payload-relative JSON record that identifies runner source files, optional thin launchers, platform dimensions when applicable, source revision, checksums, and the checksum file used for verification.
- **Deferred Hardening Item**: A control intentionally not required for first release, with rationale and a future condition that can promote it into a release gate.
- **Owner Assignment**: The downstream spec or release surface responsible for implementing and verifying a selected control.
- **Verification Exception**: A documented exception for a non-actionable vulnerability finding or control gap, including scan provenance, affected runner file or dependency policy, actionability classification, rationale, approval, and review condition.
- **Public Claim Boundary**: A rule that identifies which supply-chain and native support statements may appear in public docs or release notes.
- **Release-Readiness Evidence**: Durable non-sensitive evidence that a required control passed, was excepted, or is not yet claimable for a specific release boundary.
- **Pinned Release Input Evidence**: A downstream record of the exact selected
  runtime prerequisite boundary, dependency snapshot or stdlib-only policy,
  source revision, target platform evidence, payload paths, and integrity
  metadata used to package first-release runner files.
- **Consumer Verification Guidance**: A downstream XPLAT-007 record of platform-specific checksum command shapes, metadata lookup behavior, unsupported states, and no-network/no-source-checkout verification constraints.
- **Runner File Claim Readiness**: A per-runner-file and per-platform release-claim
  record showing whether a packaged runner file is claimable, blocked,
  deferred, excluded, or unpublished for a release boundary.
- **Platform Capability Evidence**: Official Claude Code or OpenAI Codex
  documentation evidence identifying what a plugin, skill, hook, MCP server,
  script, executable, or custom-agent surface can package or register, and what
  runtime availability the platform does or does not guarantee.
- **Runtime Dependency Boundary**: The line between the official Spec Kit /
  `specify` prerequisite boundary and disallowed plugin-only runtime
  dependencies after plugin cache population.
- **Install Completeness Evidence**: Surface-specific proof that a Claude Code
  or Codex install has the expected plugin payload, skills, scripts, hooks,
  MCP metadata, and required agent/subagent registration for that platform.
- **Runner File Distribution Evidence**: Surface-specific proof that selected
  runner files and metadata are present in source and generated Claude and
  Codex payload roots, and that the launcher surface is documented for that
  platform.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of evaluated supply-chain controls are classified as first-release, deferred hardening, or out of scope.
- **SC-002**: 100% of first-release controls have a named downstream owner surface before XPLAT-004 planning begins.
- **SC-003**: 100% of consumer-facing verification claims map to an implemented control requirement and a verification evidence expectation.
- **SC-004**: The first-release baseline can be reviewed without unresolved clarification markers.
- **SC-005**: A downstream XPLAT-004 planner can identify all runner/source/runner-file controls in under 10 minutes using this specification.
- **SC-006**: A downstream XPLAT-007 planner can identify all generated-payload, docs, release-note, consumer verification, and native support claim gates in under 10 minutes using this specification.
- **SC-007**: Public wording review rejects 100% of signing, provenance, reproducible-build, audit, or native support claims that lack implementation and verification evidence.
- **SC-008**: Vulnerability-scan release readiness fails for 100% of actionable high or critical findings unless a documented exception record exists.
- **SC-009**: The decision record leaves 0 first-release controls without an owner or acceptance gate.
- **SC-010**: 100% of vulnerability exceptions include expiry or re-approval conditions tied to public release boundaries and changed evidence inputs.
- **SC-011**: 100% of raw scanner output retention rules avoid committed raw logs by default and identify the CI artifact retention period once automation exists.
- **SC-012**: Reviewers can determine whether XPLAT-004 or XPLAT-007 readiness is blocked by stale scan evidence without relying on narrative judgment.
- **SC-013**: Reviewers can verify that XPLAT-004 pinned-input evidence covers the selected Python prerequisite policy, stdlib-only dependency snapshot, build inputs, source revision, target matrix, runner file paths, and checksums before runner files are accepted.
- **SC-014**: Reviewers can verify that XPLAT-007 checksum guidance covers Windows, macOS, and Linux command shapes and metadata lookup behavior without Bash, `jq`, source checkout paths, package restoration, post-cache network access, or pre-UAT native support claims.
- **SC-015**: Reviewers can verify that consumer-facing checksum mismatch guidance fails closed and identifies the exact facts consumers must record/report without relying on source checkout, package restoration, network repair, Bash, `jq`, or runner self-verification alone.
- **SC-016**: 100% of release-readiness and public-claim audit evidence needed for public claims has a durable non-sensitive retention location and evidence reference.
- **SC-017**: 100% of claimed runner files and platforms have per-file readiness status, and partial readiness cannot imply unsupported platform claims.
- **SC-018**: Reviewers can identify that the runtime decision was amended from Go to Python, why Python is now selected through the official Spec Kit / `specify` prerequisite boundary, and which XPLAT-004 proof items remain before implementation readiness.
- **SC-019**: Reviewers can identify official Claude Code and OpenAI Codex platform support findings separately from repository assumptions and can verify that no first-release runtime claim depends on an undocumented user-host runtime.
- **SC-020**: Reviewers can distinguish Claude bundled plugin agents from Codex custom-agent TOML registration and can identify a missing Codex agent registration as an install-completeness failure, not a successful full install.
- **SC-021**: Reviewers can identify whether runner source and any launcher metadata are bundled in both generated marketplace payload roots, whether any post-install download is required, and which documented Claude or Codex surface launches the runner.
- **SC-022**: Reviewers can identify that active Bash-based build, test, eval,
  payload, and release-readiness gates for shipped plugin behavior have Python
  standard-library replacement requirements before XPLAT-007 can pass.

## Assumptions

- XPLAT-002 is merged, but this PR amends the settled source truth: the active
  first-release `speckit-pro-runner` contract is the Python standard-library
  runner, not the original rejected Go-native analysis.
- Compiled binaries are not a fallback for XPLAT. They are rejected historical
  candidates because SpecKit itself requires Python and the plugin's core value
  is SpecKit workflow automation.
- Official Claude Code and OpenAI Codex docs support packaged plugin/skill
  script surfaces, but do not guarantee arbitrary language runtimes for all
  installed plugin hosts. XPLAT-003 therefore allows Python only through the
  official Spec Kit / `specify` prerequisite boundary, and requires preflight to
  diagnose missing prerequisites before support claims.
- The first public release can rely on published checksums and manual consumer-local checksum verification even if the plugin marketplace does not enforce checksum verification automatically.
- Signatures, SBOMs, provenance attestations, reproducible builds, and formal third-party audit improve trust but are not required for the first release unless this decision record explicitly promotes them.
- Generated Claude and Codex payloads remain source-derived artifacts, so their integrity gate must compare source inputs and generated outputs before public release.
- A release-asset download path is not treated as a self-contained marketplace
  install unless downstream evidence proves explicit download, checksum
  verification, failure behavior, and truthful claims for that path.
- Native Windows/macOS/Linux support claims remain blocked until XPLAT-007 implements cutover and captures UAT evidence.
- XPLAT-003 records the model and acceptance gates; XPLAT-004, XPLAT-007, and release automation surfaces implement the selected controls.
