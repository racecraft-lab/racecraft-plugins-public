# Feature Specification: Supply-Chain Security and Consumer Trust Model

**Feature Branch**: `codex/xplat-003-supply-chain-security-and-consumer-trust-model`

**Created**: 2026-06-27

**Status**: Draft

**Input**: User description: "Choose the practical first-release security baseline and deferred hardening backlog for the XPLAT Go native runner before XPLAT-004 builds the runner and before XPLAT-007 makes public release claims."

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
- Generated Claude and Codex payloads drift from their source inputs after the runner or verification metadata changes.
- Published checksum metadata is missing, stale, or does not match a packaged runner artifact.
- Public release wording is prepared before XPLAT-007 native-platform UAT or before the selected controls are implemented.
- A downstream implementation attempts to add signing, SBOM, provenance, reproducible-build, or audit language without corresponding implementation evidence.
- A marketplace install path does not automatically enforce checksums, so consumer-local verification must remain manual and clearly documented.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The specification MUST record XPLAT-002's selected native runner model as the runtime context and MUST NOT reopen runtime selection.
- **FR-002**: The specification MUST define the first-release control baseline as pinned release inputs, vulnerability scanning, generated-payload integrity, published checksums, consumer-local verification, and truthful public claims.
- **FR-003**: The specification MUST require generated Claude and Codex payload integrity to include a source-to-dist gate that detects drift between source inputs and generated payload outputs.
- **FR-004**: The specification MUST require first-release binary artifact integrity to include published checksums for packaged runner artifacts.
- **FR-005**: The specification MUST require consumer-local verification guidance that lets a consumer confirm runner version or preflight output and compare packaged artifact checksums against the published checksum source.
- **FR-006**: The specification MUST require vulnerability scans for the native runner source, dependencies, and release artifacts where applicable before public release.
- **FR-007**: The vulnerability policy MUST fail release readiness on actionable high or critical findings.
- **FR-008**: The vulnerability policy MUST define exception handling for non-actionable findings, including the finding, rationale, expiry or review condition, and approving maintainer.
- **FR-009**: The specification MUST classify signatures, provenance or attestations, reproducible builds, SBOMs, formal audit, and cryptographic trust-chain verification as deferred hardening unless an explicit first-release requirement overrides that classification.
- **FR-010**: The specification MUST assign runner source, dependency, artifact, preflight/version, checksum, and applicable vulnerability controls to XPLAT-004.
- **FR-011**: The specification MUST assign generated-payload source-to-dist integrity, public docs or release-note claim boundaries, consumer-facing verification guidance, and native support claim readiness to XPLAT-007.
- **FR-012**: The specification MUST identify any release-automation-owned controls and assign them to the earliest downstream spec or release surface that can implement and verify them before public release.
- **FR-013**: Public docs and release notes MUST claim only controls that are implemented and verified.
- **FR-014**: Public docs and release notes MUST NOT claim signing, provenance, reproducible builds, audit, or native Windows/macOS/Linux support before those guarantees have implementation and verification evidence.
- **FR-015**: The specification MUST document the deferred hardening backlog with rationale and the condition that would move each item into a future release gate.
- **FR-016**: The specification MUST preserve XPLAT-001 supply-chain rubric traceability for dependency policy, lockfile discipline, generated payload integrity, vulnerability scanning, provenance, checksums or signatures, SBOM feasibility, consumer-local verification, and release-claim truthfulness.
- **FR-017**: The specification MUST preserve XPLAT-002 handoff traceability for native runner artifact assumptions, Go module and release input policy, artifact origin evidence, build environment inputs, and installed-cache verification gaps.
- **FR-018**: The specification MUST exclude runner implementation, helper porting, active invocation path changes, generated payload rebuilds, release automation changes, and public native support claims from XPLAT-003 implementation scope.

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
- **Deferred Hardening Item**: A control intentionally not required for first release, with rationale and a future condition that can promote it into a release gate.
- **Owner Assignment**: The downstream spec or release surface responsible for implementing and verifying a selected control.
- **Verification Exception**: A documented exception for a non-actionable vulnerability finding or control gap, including rationale, approval, and review condition.
- **Public Claim Boundary**: A rule that identifies which supply-chain and native support statements may appear in public docs or release notes.

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

## Assumptions

- XPLAT-002 is complete enough for XPLAT-003 to treat the Go native binary runner and `speckit-pro-runner` contract as settled source truth.
- The first public release can rely on published checksums and manual consumer-local checksum verification even if the plugin marketplace does not enforce checksum verification automatically.
- Signatures, SBOMs, provenance attestations, reproducible builds, and formal third-party audit improve trust but are not required for the first release unless this decision record explicitly promotes them.
- Generated Claude and Codex payloads remain source-derived artifacts, so their integrity gate must compare source inputs and generated outputs before public release.
- Native Windows/macOS/Linux support claims remain blocked until XPLAT-007 implements cutover and captures UAT evidence.
- XPLAT-003 records the model and acceptance gates; XPLAT-004, XPLAT-007, and release automation surfaces implement the selected controls.
