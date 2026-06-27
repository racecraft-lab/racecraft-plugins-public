# Feature Specification: Supply-Chain Security and Consumer Trust Model

**Feature Branch**: `codex/xplat-003-supply-chain-security-and-consumer-trust-model`

**Created**: 2026-06-27

**Status**: Draft

**Input**: User description: "Choose the practical first-release security baseline and deferred hardening backlog for the XPLAT Go native runner before XPLAT-004 builds the runner and before XPLAT-007 makes public release claims."

## Clarifications

### Session 1: First-release Control Boundaries

- Q: What is the minimum first-release control baseline that blocks public
  cutover? A: The practical baseline is pinned Go/release inputs,
  vulnerability scanning, generated payload source-to-dist integrity, published
  checksums, consumer-local verification, and truthful public claims.
- Q: Which controls stay deferred hardening, and what evidence can promote them
  to first-release required? A: Signatures, SBOMs, provenance/attestations,
  reproducible builds, formal audit, and cryptographic trust-chain verification
  stay deferred unless concrete first-release evidence shows enforced
  marketplace/install support, release automation that can produce and verify
  the artifact, a public claim that cannot be made truthfully without the
  control, or a blocking consumer/adoption requirement.
- Q: How should first-release controls be split across owner surfaces? A:
  XPLAT-004 owns runner source, dependency, artifact, preflight/version,
  checksum generation, and applicable scan controls. XPLAT-007 owns generated
  payload integrity, consumer verification guidance, release-note/docs claim
  boundaries, native support readiness, and cutover evidence. Release
  automation owns publication-time evidence only where later specs wire it in.
- Q: What evidence must exist before XPLAT-007 can make public supply-chain or
  native-support claims? A: Runner preflight/version evidence, checksums for
  each packaged artifact, consumer verification instructions, source-to-dist
  payload gate output, vulnerability scan results or exception records, and
  public-claim audit evidence.
- Q: How should high/critical vulnerability scan findings affect public cutover?
  A: Actionable high/critical findings block release readiness. Non-actionable
  exceptions must record the finding source and severity, affected
  artifact/version, rationale, compensating control, approving maintainer, and
  expiry or review condition.

### Session 2: Artifact Integrity And Consumer Verification

- Q: What checksum filename and algorithm should first-release runner artifacts
  use? A: Use SHA-256 and publish one stable payload-relative checksum file at
  `scripts/speckit-pro-runner.sha256`. Entries use 64 lowercase hexadecimal
  characters, two spaces, and the payload-relative artifact path so maintainers
  and consumers can use common SHA-256 verification tools.
- Q: What fields must the runner artifact manifest include? A: Publish
  `scripts/speckit-pro-runner.manifest.json` with `schema_version`,
  `plugin_name`, `plugin_version`, `runner_name`, `runner_version`,
  `contract_version`, `source_revision`, `checksum_algorithm`, and
  `artifacts[]` entries containing `artifact_id`, `payload_path`, `os`, `arch`,
  `size_bytes`, `sha256`, and `checksum_file`.
- Q: What source-to-dist evidence should prove generated Claude/Codex payload
  integrity? A: XPLAT-007 must run `bash scripts/build-plugin-payloads.sh`,
  then verify no generated drift under `dist/claude/speckit-pro`,
  `dist/codex/speckit-pro`, `.claude-plugin/marketplace.json`, and
  `.agents/plugins/marketplace.json`, recording the command, exit status,
  source inputs, generated roots, and checksum/manifest paths.
- Q: What extra `runtime-info` and `preflight` fields are required for consumer
  verification? A: Preserve the XPLAT-002 fields and add artifact-integrity
  pointers: `executable_path`, `artifact_id`, `artifact_manifest_path`,
  `checksum_file_path`, `checksum_algorithm`, `expected_checksum`, and
  `verification_status`. The response distinguishes installed-cache context
  from source-only context and does not claim external trust-chain verification.
- Q: What local consumer verification command shape should docs require? A: Use
  a two-step local path: run runner identity/preflight first, then compare the
  installed artifact hash against the published checksum entry with
  platform-native SHA-256 tooling. The verification path must not rely on
  runner self-verification alone and must not require `jq`, Bash, a source
  checkout, or network package restoration.

### Session 3: Vulnerability Policy And Public Claims

- Q: How should "actionable high/critical" be defined? A: A finding is
  actionable when scanner severity is high/critical, or CVSS is high/critical
  when available, and the finding affects the first-release trust boundary:
  runner source, Go modules/toolchain, build/release inputs, packaged runner
  artifacts, integrity metadata, generated payloads, marketplace manifests, or
  release evidence. It must also be reachable, shipped, or capable of changing
  release output or public claims. False positives, unreachable code,
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
  packaged native runner artifacts, SHA-256 checksum file and manifest, local
  preflight/version plus checksum verification, source-to-dist payload gate, and
  vulnerability scanning with no unresolved actionable high/critical findings.
  Forbidden until implemented and verified: signed binaries/signatures, SBOMs,
  provenance/attestations, reproducible builds, formal audit/certification,
  marketplace-enforced verification, cryptographic trust-chain verification, and
  native Windows/macOS/Linux support. Roadmap wording may describe these as
  planned or deferred hardening, but not as provided, guaranteed, certified,
  enforced, or trusted today.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Maintainer Reviews Trust Baseline (Priority: P1)

A maintainer can read one decision record that separates first-release controls from deferred hardening for the selected native runner and its generated plugin payloads.

**Why this priority**: XPLAT-004 cannot build a release-ready runner until maintainers agree which controls block first release and which controls are documented follow-up hardening.

**Independent Test**: A reviewer can inspect the specification and confirm every evaluated trust control is categorized as first-release, deferred hardening, or explicitly out of scope, with rationale.

**Acceptance Scenarios**:

1. **Given** XPLAT-002 selected the native runner model, **When** a maintainer reads the XPLAT-003 specification, **Then** the first-release baseline includes pinned release inputs, vulnerability scanning, generated-payload integrity, checksums, consumer-local verification, and truthful public claims.
2. **Given** heavier controls such as signing, provenance, reproducible builds, SBOMs, or audit are evaluated, **When** the maintainer reviews their status, **Then** each control is identified as deferred hardening unless explicitly moved into the first-release baseline with rationale.
3. **Given** a downstream plan references the XPLAT-003 decision, **When** the maintainer checks the plan, **Then** no downstream work can claim a stronger guarantee than the controls this specification requires.

---

### User Story 2 - Implementer Maps Controls To Owner Specs (Priority: P1)

An implementer can see which selected controls belong to XPLAT-004, XPLAT-007, release automation, and public documentation without reopening the runtime decision.

**Why this priority**: The runner foundation, generated payload cutover, and release-readiness work have different owners and acceptance gates.

**Independent Test**: A planner can map each first-release control to a downstream owner spec and verify that no control is left ownerless.

**Acceptance Scenarios**:

1. **Given** XPLAT-004 owns the runner foundation, **When** an implementer reviews the control map, **Then** runner source, dependency, artifact, preflight/version, checksum generation, and applicable vulnerability-scan controls are assigned to XPLAT-004 acceptance gates.
2. **Given** XPLAT-007 owns generated payload cutover and public release readiness, **When** an implementer reviews the control map, **Then** source-to-dist payload integrity, consumer-facing verification guidance, and public docs or release-note claim boundaries are assigned to XPLAT-007 acceptance gates.
3. **Given** a control belongs to release automation rather than the runner itself, **When** the implementer reviews the handoff, **Then** the specification identifies the earliest downstream surface that must implement and verify the control before public release.

---

### User Story 3 - Consumer Understands Local Verification And Limits (Priority: P2)

A consumer or reviewer can understand what they can verify locally after install and which trust guarantees the project intentionally does not claim for first release.

**Why this priority**: Public trust depends on accurate verification guidance and avoiding unsupported security claims.

**Independent Test**: A reviewer can compare draft public wording or release notes against this specification and identify whether every claim is allowed, deferred, or forbidden until implemented.

**Acceptance Scenarios**:

1. **Given** the plugin has packaged native runner artifacts, **When** a consumer follows the documented local verification path, **Then** they can confirm the runner version or preflight output and compare packaged artifact checksums against published checksums.
2. **Given** public documentation or release notes mention supply-chain controls, **When** a reviewer audits the wording, **Then** the wording claims only controls that have implementation and verification evidence.
3. **Given** signing, provenance, reproducible builds, audit, or native support claims are not yet implemented and verified, **When** public wording is reviewed, **Then** those claims are rejected or rewritten as deferred, non-guaranteed roadmap language.

### Edge Cases

- A vulnerability scan reports a high or critical finding that is not actionable because it is unreachable, false positive, or already mitigated by the packaged artifact boundary.
- A vulnerability scan reports a high or critical finding in repo-only, test, archive, docs-only, or other non-shipped paths that are outside the XPLAT runtime trust boundary.
- Vulnerability scan evidence was clean when produced, but a source revision, dependency snapshot, toolchain, build input, generated artifact, scanner version, vulnerability database timestamp, advisory status, severity, exploitability, or release boundary changed before readiness review.
- A vulnerability exception was approved for one release but the affected artifact, dependency graph, platform, toolchain, scanner database, advisory status, severity, exploitability, or compensating control changed before the next release.
- Generated Claude and Codex payloads drift from their source inputs after the runner or verification metadata changes.
- Checksum or runner manifest metadata exists in XPLAT-004 outputs but is not present, equal, and fresh in both generated Claude and Codex payload roots before XPLAT-007 cutover.
- Published checksum metadata is missing, stale, or does not match a packaged runner artifact.
- A public release or trust claim depends on release automation that has not yet recorded downstream acceptance evidence proving the publication gate is implemented and wired into the release path.
- Consumer checksum guidance exists for one platform family but not for every target platform artifact that XPLAT-007 intends to claim after UAT.
- Public release wording is prepared before XPLAT-007 native-platform UAT or before the selected controls are implemented.
- A downstream implementation attempts to add signing, SBOM, provenance, reproducible-build, or audit language without corresponding implementation evidence.
- A marketplace install path does not automatically enforce checksums, so consumer-local verification must remain manual and clearly documented.
- A consumer computes a packaged runner artifact hash that differs from the
  matching published checksum entry.
- Only some platform artifacts have current checksum, manifest, scan,
  preflight, native UAT, source-to-dist, and claim-audit evidence while another
  intended or claimed platform artifact is missing, stale, mismatched, or
  unpublished.
- Release-readiness or public-claim audit evidence exists only in expiring
  logs, raw workflow output, or unretained generated artifacts without a
  durable non-sensitive summary.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The specification MUST record XPLAT-002's selected native runner model as the runtime context and MUST NOT reopen runtime selection.
- **FR-002**: The specification MUST define the first-release control baseline as pinned release inputs, vulnerability scanning, generated-payload integrity, published checksums, consumer-local verification, and truthful public claims.
- **FR-003**: The specification MUST require generated Claude and Codex payload integrity to include a source-to-dist gate that runs `bash scripts/build-plugin-payloads.sh`, checks generated payload and marketplace-manifest drift, and records command, exit status, source inputs, generated roots, checksum/manifest paths, and metadata propagation from XPLAT-004-produced checksum and manifest outputs into source and generated Claude/Codex payload roots.
- **FR-004**: The specification MUST require first-release binary artifact integrity to include SHA-256 checksums for packaged runner artifacts in `scripts/speckit-pro-runner.sha256`.
- **FR-005**: The specification MUST require consumer-local verification guidance that lets a consumer confirm runner version or preflight output and compare packaged artifact checksums against the published checksum source using platform-native SHA-256 tooling without requiring `jq`, Bash, source checkout, or network package restoration.
- **FR-006**: The specification MUST require vulnerability scans for the native runner source, dependencies, and release artifacts where applicable before public release.
- **FR-007**: The vulnerability policy MUST fail release readiness on actionable high or critical findings, where actionability requires high/critical severity plus first-release trust-boundary scope and reachable, shipped, or release-affecting relevance.
- **FR-008**: The vulnerability policy MUST define exception handling for non-actionable findings, including scanner/source, tool version or vulnerability database timestamp, advisory ID when available, severity, affected artifact/dependency/version/platform, actionability classification, rationale, reachability or false-positive evidence, compensating control, approving maintainer, approval date, and expiry or review condition.
- **FR-009**: The specification MUST classify signatures, provenance or attestations, reproducible builds, SBOMs, formal audit, and cryptographic trust-chain verification as deferred hardening unless concrete first-release evidence promotes a control into a release requirement.
- **FR-010**: The specification MUST assign runner source, dependency, artifact, preflight/version, checksum, manifest, and applicable vulnerability controls to XPLAT-004.
- **FR-011**: The specification MUST assign generated-payload source-to-dist integrity, public docs or release-note claim boundaries, consumer-facing verification guidance, runtime-info/preflight evidence, and native support claim readiness to XPLAT-007.
- **FR-012**: The specification MUST identify any release-automation-owned controls and assign them to the earliest downstream spec or release surface that can implement and verify them before public release.
- **FR-013**: Public docs and release notes MUST claim only controls that are implemented and verified.
- **FR-014**: Public docs and release notes MUST NOT claim signing, provenance, reproducible builds, audit, or native Windows/macOS/Linux support before those guarantees have implementation and verification evidence.
- **FR-015**: The specification MUST document the deferred hardening backlog with rationale and promotion conditions, including enforced marketplace/install support, release automation that can produce and verify the artifact, required truthful public claims, or blocking consumer/adoption requirements.
- **FR-016**: The specification MUST preserve XPLAT-001 supply-chain rubric traceability for dependency policy, lockfile discipline, generated payload integrity, vulnerability scanning, provenance, checksums or signatures, SBOM feasibility, consumer-local verification, and release-claim truthfulness.
- **FR-017**: The specification MUST preserve XPLAT-002 handoff traceability for native runner artifact assumptions, Go module and release input policy, artifact origin evidence, build environment inputs, and installed-cache verification gaps.
- **FR-018**: The specification MUST exclude runner implementation, helper porting, active invocation path changes, generated payload rebuilds, release automation changes, and public native support claims from XPLAT-003 implementation scope.
- **FR-019**: The first-release artifact manifest MUST identify plugin and runner versions, contract version, source revision, checksum algorithm, and per-artifact payload path, platform, architecture, size, SHA-256 checksum, and checksum file.
- **FR-020**: Runtime-info or preflight evidence used for consumer verification MUST include artifact-integrity pointers and MUST distinguish installed-cache context from source-only context without claiming external trust-chain verification.
- **FR-021**: Vulnerability exception records MUST expire before each public release unless re-approved from current scan evidence, and MUST expire immediately when the affected artifact, dependency graph, platform, toolchain, scanner version/database, advisory status, severity, exploitability, or compensating control changes.
- **FR-022**: Scan evidence retention MUST keep durable non-sensitive release-readiness summaries and exception records in spec, PR-packet, or release-readiness artifacts; raw scanner output MUST NOT be committed by default and, once automation exists, MUST be retained as CI artifacts for 30 days.
- **FR-023**: XPLAT-004 readiness MUST fail when required runner/source/dependency/artifact scan evidence is missing, stale, or has unresolved actionable high/critical findings.
- **FR-024**: XPLAT-007 public cutover and release-claim readiness MUST fail when scan evidence, exceptions, checksums, manifest, source-to-dist evidence, consumer verification guidance, public-claim audit, runtime preflight/version evidence, or native UAT evidence is missing or stale.
- **FR-025**: Public docs and release notes MUST NOT claim signed binaries, SBOMs, provenance or attestations, reproducible builds, formal audit or certification, marketplace-enforced verification, cryptographic trust-chain verification, or native Windows/macOS/Linux support until each claim is implemented and verified.
- **FR-026**: Vulnerability scan evidence MUST define freshness and staleness for release-readiness review. Evidence is stale when it is older than 7 calendar days at readiness review, predates the source revision, dependency manifest or sum state, toolchain, build input, generated artifact, scanner version or vulnerability database timestamp it claims to cover, or crosses a public release boundary without re-approval.
- **FR-027**: XPLAT-004 pinned Go and release input evidence MUST include Go toolchain version and source, Go module/dependency manifest and `go.sum` or equivalent dependency snapshot state, target OS/architecture matrix, build command or repeatable build recipe, release/package input list, source revision used to build artifacts, generated artifact names and paths, generated artifact SHA-256 checksums, and any first-release scan inputs. Unknown or unverified fields are evidence gaps, not accepted controls.
- **FR-028**: XPLAT-007 consumer-local checksum guidance MUST include separate Windows, macOS, and Linux SHA-256 command shapes for every target platform artifact it intends to claim after UAT, MUST describe how consumers locate checksum metadata from the installed payload or release-provided offline metadata, and MUST fail closed when metadata is unavailable. This guidance MUST NOT require Bash, `jq`, source checkout paths, package-manager restoration, or network access after plugin cache population, and MUST NOT imply native platform support before XPLAT-007 UAT evidence exists.
- **FR-029**: Release-automation-owned publication controls MUST remain `assigned_not_implemented` and `not_claimable` until the earliest downstream implementing surface records acceptance evidence with the implementing spec or release surface, control ID, publication gate location, release inputs, generated outputs, latest pass/fail evidence, and claim-dependency mapping. XPLAT-007 public cutover and release-claim readiness MUST fail when a public claim relies on release automation whose acceptance evidence is missing, stale, or not wired into the publication path.
- **FR-030**: XPLAT-007 source-to-dist evidence MUST prove checksum and runner artifact manifest metadata propagation from XPLAT-004 runtime artifact outputs to checked-in source metadata paths, generated Claude payload metadata paths, generated Codex payload metadata paths, and final cutover evidence. Missing, stale, or unequal metadata across those locations MUST fail public cutover and release-claim readiness.
- **FR-031**: Consumer-local checksum guidance MUST define a computed-versus-published checksum mismatch as a closed verification failure. The guidance MUST tell consumers not to rely on the artifact for native-runner claims, MUST require recording the artifact path, platform, runner identity or preflight output, checksum metadata source, expected checksum, computed checksum, plugin version or release boundary, and reporting path, and MUST NOT instruct consumers to repair the failure through source checkout, package restoration, network fetches, Bash, `jq`, or runner self-verification alone.
- **FR-032**: Release-readiness evidence and public-claim audit evidence MUST retain durable, non-sensitive summaries beyond vulnerability scan summaries and exception records. These records MUST include release boundary, control or claim IDs, evidence references, pass/fail/blocked status, timestamp or source revision, owner surface, known gaps, and approval/status, while raw logs and large generated artifacts MUST NOT be committed by default.
- **FR-033**: Public cutover and release claims MUST be evaluated per claimed artifact and platform. If any claimed artifact is missing, stale, mismatched, unpublished, or lacks required checksum, manifest, runtime-info/preflight, native UAT, source-to-dist, scan, exception, release-automation, or claim-audit evidence, that artifact/platform MUST be excluded from claims or the claim set MUST remain blocked; one passing platform MUST NOT imply Windows/macOS/Linux support for other platforms.

### Reviewability Notes *(if applicable)*

- XPLAT-003 is a decision spike. It may create or update specification artifacts and downstream handoff language, but it does not change runtime behavior, generated payloads, runner source, release automation, or public docs.
- Any later implementation PR that crosses more than one owner surface must carry its own reviewability budget and traceability back to the XPLAT-003 control map.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: N/A
- **Projected reviewable LOC**: 0 production LOC; 0-140 decision-record/documentation LOC
- **Projected production files**: 0
- **Projected total files**: 2-5
- **Budget result**: within budget
- **Split decision**: This remains one decision-spike spec because it records one security/trust model and assigns downstream controls without implementation changes.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Security Control Decision**: A trust or verification control evaluated by XPLAT-003, including first-release or deferred classification, rationale, owner surface, and evidence requirement.
- **First-Release Baseline**: The minimum set of controls that must be implemented and verified before public release claims can rely on the native runner.
- **Runner Artifact Manifest**: A payload-relative JSON record that identifies runner artifacts, platform dimensions, source revision, checksums, and the checksum file used for verification.
- **Deferred Hardening Item**: A control intentionally not required for first release, with rationale and a future condition that can promote it into a release gate.
- **Owner Assignment**: The downstream spec or release surface responsible for implementing and verifying a selected control.
- **Verification Exception**: A documented exception for a non-actionable vulnerability finding or control gap, including scan provenance, affected artifact, actionability classification, rationale, approval, and review condition.
- **Public Claim Boundary**: A rule that identifies which supply-chain and native support statements may appear in public docs or release notes.
- **Release-Readiness Evidence**: Durable non-sensitive evidence that a required control passed, was excepted, or is not yet claimable for a specific release boundary.
- **Pinned Release Input Evidence**: A downstream record of the exact Go toolchain, dependency snapshot, build inputs, source revision, target matrix, artifact paths, and checksums used to produce first-release runner artifacts.
- **Consumer Verification Guidance**: A downstream XPLAT-007 record of platform-specific checksum command shapes, metadata lookup behavior, unsupported states, and no-network/no-source-checkout verification constraints.
- **Artifact Claim Readiness**: A per-artifact and per-platform release-claim
  record showing whether a packaged runner artifact is claimable, blocked,
  deferred, excluded, or unpublished for a release boundary.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of evaluated supply-chain controls are classified as first-release, deferred hardening, or out of scope.
- **SC-002**: 100% of first-release controls have a named downstream owner surface before XPLAT-004 planning begins.
- **SC-003**: 100% of consumer-facing verification claims map to an implemented control requirement and a verification evidence expectation.
- **SC-004**: The first-release baseline can be reviewed without unresolved clarification markers.
- **SC-005**: A downstream XPLAT-004 planner can identify all runner/source/artifact controls in under 10 minutes using this specification.
- **SC-006**: A downstream XPLAT-007 planner can identify all generated-payload, docs, release-note, consumer verification, and native support claim gates in under 10 minutes using this specification.
- **SC-007**: Public wording review rejects 100% of signing, provenance, reproducible-build, audit, or native support claims that lack implementation and verification evidence.
- **SC-008**: Vulnerability-scan release readiness fails for 100% of actionable high or critical findings unless a documented exception record exists.
- **SC-009**: The decision record leaves 0 first-release controls without an owner or acceptance gate.
- **SC-010**: 100% of vulnerability exceptions include expiry or re-approval conditions tied to public release boundaries and changed evidence inputs.
- **SC-011**: 100% of raw scanner output retention rules avoid committed raw logs by default and identify the CI artifact retention period once automation exists.
- **SC-012**: Reviewers can determine whether XPLAT-004 or XPLAT-007 readiness is blocked by stale scan evidence without relying on narrative judgment.
- **SC-013**: Reviewers can verify that XPLAT-004 pinned-input evidence covers the Go toolchain, dependency snapshot, build inputs, source revision, target matrix, artifact paths, and checksums before runner artifacts are accepted.
- **SC-014**: Reviewers can verify that XPLAT-007 checksum guidance covers Windows, macOS, and Linux command shapes and metadata lookup behavior without Bash, `jq`, source checkout paths, package restoration, post-cache network access, or pre-UAT native support claims.
- **SC-015**: Reviewers can verify that consumer-facing checksum mismatch guidance fails closed and identifies the exact facts consumers must record/report without relying on source checkout, package restoration, network repair, Bash, `jq`, or runner self-verification alone.
- **SC-016**: 100% of release-readiness and public-claim audit evidence needed for public claims has a durable non-sensitive retention location and evidence reference.
- **SC-017**: 100% of claimed artifacts and platforms have per-artifact readiness status, and partial artifact readiness cannot imply unsupported platform claims.

## Assumptions

- XPLAT-002 is complete enough for XPLAT-003 to treat the Go native binary runner and `speckit-pro-runner` contract as settled source truth.
- The first public release can rely on published checksums and manual consumer-local checksum verification even if the plugin marketplace does not enforce checksum verification automatically.
- Signatures, SBOMs, provenance attestations, reproducible builds, and formal third-party audit improve trust but are not required for the first release unless this decision record explicitly promotes them.
- Generated Claude and Codex payloads remain source-derived artifacts, so their integrity gate must compare source inputs and generated outputs before public release.
- Native Windows/macOS/Linux support claims remain blocked until XPLAT-007 implements cutover and captures UAT evidence.
- XPLAT-003 records the model and acceptance gates; XPLAT-004, XPLAT-007, and release automation surfaces implement the selected controls.
