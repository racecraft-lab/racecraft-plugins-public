# Feature Specification: Claude/Codex Cutover and Universal Install Release Gate

**Feature Branch**: `codex/xplat-008-claude-codex-cutover-universal-install-release-gate`

**Created**: 2026-07-05

**Status**: Draft

**Input**: User description: "Cut over installed Claude and Codex SpecKit Pro surfaces to the cross-platform runner, rebuild and verify generated payloads, document the implemented trust model, prove native Windows/macOS/Linux install-to-first-use/update/repair journeys, and block public release when proof is incomplete."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install and run first use without shell prerequisites (Priority: P1)

As a Claude Code or Codex user on native Windows, macOS, or Linux, I can install SpecKit Pro and complete the first-use scaffold/status/autopilot-dry-run journey without needing Bash, Git Bash, WSL, PowerShell-specific command language, `jq`, shell interpolation, or Unix-only path assumptions.

**Why this priority**: This is the core public-release blocker. The plugin cannot claim native cross-platform installed-runtime support until the actual installed user journey works on all target platforms.

**Independent Test**: Can be tested by installing the Claude and Codex plugin payloads on each native platform and completing the documented first-use journey from the installed plugin cache.

**Acceptance Scenarios**:

1. **Given** a native Windows machine with only the supported runtime prerequisites installed, **When** a user installs SpecKit Pro and runs scaffold, status, and autopilot dry-run, **Then** each journey completes without requiring WSL, Git Bash, Bash, `jq`, or PowerShell-specific command language.
2. **Given** a native macOS or Linux machine with the supported runtime prerequisites installed, **When** a user follows the same installed-plugin first-use journey, **Then** the outcome matches the Windows journey and does not depend on Unix-only helper scripts.
3. **Given** an active Claude or Codex skill, agent, hook, or install guide, **When** it launches installed runtime behavior, **Then** it invokes the approved runner path and not shell-only helpers.

---

### User Story 2 - Verify generated release payload completeness (Priority: P2)

As a release maintainer, I can rebuild generated Claude and Codex payloads from source and verify that each payload contains the expected release metadata, bundled agents, hooks, runner files, and XPLAT-003 manifest/checksum records before publication.

**Why this priority**: Users install generated payloads, not only source-checkout files. Release readiness requires proving the shipped payloads match the cutover path and trust model.

**Independent Test**: Can be tested by rebuilding both generated payloads and running payload-completeness and release-readiness checks against the rebuilt artifacts.

**Acceptance Scenarios**:

1. **Given** the source plugin tree, **When** the maintainer rebuilds Claude and Codex payloads, **Then** both generated payloads contain all expected skills, bundled agents, hooks, runner files, release metadata, and trust metadata.
2. **Given** a generated payload missing a bundled agent, hook, runner file, manifest, checksum record, or current version metadata, **When** the payload gate runs, **Then** it fails and identifies the missing or stale item.
3. **Given** generated payloads that pass all completeness checks, **When** release-readiness checks run, **Then** payload completeness is accepted as evidence for the public release gate.

---

### User Story 3 - Update and repair installed plugins safely (Priority: P3)

As a maintainer or installed-plugin user, I can run doctor, update, and autoheal checks that detect stale or incomplete installs, safely repair trusted gaps, and print exact manual remediation for unsafe gaps.

**Why this priority**: Public release readiness depends on ongoing install health, not only first install success.

**Independent Test**: Can be tested by intentionally creating stale, missing, and unsafe install-cache states, then verifying that trusted gaps are repaired and unsafe gaps produce manual remediation without broad reinstall behavior.

**Acceptance Scenarios**:

1. **Given** an installed plugin missing a trusted generated artifact whose source checksum matches, **When** doctor/autoheal runs, **Then** the missing artifact is refreshed and the user sees a clear repair result.
2. **Given** an installed plugin with an unsafe or untrusted gap, **When** doctor/autoheal runs, **Then** no broad automatic reinstall occurs and the user receives exact manual remediation steps.
3. **Given** a previously installed plugin version, **When** the user updates to the latest tagged release, **Then** first-use scaffold/status/autopilot-dry-run behavior still passes on the target platform.

---

### User Story 4 - Review public evidence and trust claims (Priority: P4)

As a reviewer, I can inspect filled native UAT runbooks, public docs, release notes, and traceability evidence that match the implemented support and consumer-trust model.

**Why this priority**: Reviewers need release-reviewable proof that XPLAT-003, XPLAT-006, and XPLAT-007 handoffs are enforced in the installed plugin path.

**Independent Test**: Can be tested by reviewing the feature-local evidence packet, UAT runbooks, public docs, release notes, and release-readiness output without relying on private context.

**Acceptance Scenarios**:

1. **Given** native UAT runbooks for Claude and Codex on Windows, macOS, and Linux, **When** a reviewer inspects them, **Then** every platform/product row is filled with install, bundled-agent verification, scaffold/status, autopilot dry-run, update, and repair evidence.
2. **Given** public install, first-run, troubleshooting, trust, and release-note content, **When** a reviewer checks support claims, **Then** the docs claim only implemented and UAT-proven support and do not overstate cryptographic guarantees.
3. **Given** the PR review packet, **When** a reviewer traces requirements to evidence, **Then** each major requirement maps to changed files and verification proof.

---

### Edge Cases

- Active runtime text mentions Bash, `.sh`, `jq`, WSL, Git Bash, PowerShell-specific command language, shell interpolation, or Unix-only paths as required behavior.
- Historical archive/provenance text, CI dispatch glue, or upstream Spec Kit generated helper references contain shell terms that are out of active installed-runtime scope.
- A generated payload rebuild omits a file that exists in source, includes stale version metadata, or lacks XPLAT-003 manifest/checksum records.
- Native UAT evidence is missing a platform/product row, contains placeholder PR fields, raw HTML anchors, empty expected-result sections, or smoke-only results.
- The installed plugin can launch a first-use journey but update or repair fails on one platform.
- Autoheal sees a gap that cannot be tied to trusted source metadata.
- Public docs are edited before UAT passes and accidentally imply support that has not been proven.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature MUST classify Claude and Codex skills, agents, hooks, install guidance, generated payload files, release gates, public docs, archive/provenance text, CI dispatch glue, and upstream Spec Kit helpers by whether they are active installed-runtime surfaces.
- **FR-002**: Active installed-runtime Claude and Codex surfaces MUST invoke the Python 3.11+ standard-library runner behavior as the installed runtime substrate.
- **FR-003**: Active installed-runtime surfaces MUST NOT require Bash, `.sh` helpers, `jq`, shell interpolation, Git Bash, WSL, PowerShell-specific command language, or Unix-only path assumptions.
- **FR-004**: No-shell/no-jq guards MUST fail active installed-runtime source paths, generated payloads, install guidance, and release gates when prohibited shell-only runtime behavior is reintroduced.
- **FR-005**: No-shell/no-jq guards MUST allow explicitly scoped archive/provenance text, minimal CI dispatch glue that only invokes Python gates, and upstream GitHub Spec Kit generated `.specify/scripts/bash/` helpers in consumer projects.
- **FR-006**: Generated Claude and Codex payloads MUST be rebuilt from source for this release-readiness path.
- **FR-007**: Generated payload verification MUST prove release version metadata, bundled agents, hooks, required runner files, and XPLAT-003 manifest/checksum metadata are complete for both Claude and Codex payloads.
- **FR-008**: Release-readiness checks MUST fail when generated payloads are incomplete, stale, missing bundled agents, missing hooks, missing runner files, or missing required trust metadata.
- **FR-009**: Public install and first-run docs MUST describe the supported installed-plugin prerequisites and MUST NOT describe Bash, Git Bash, WSL, PowerShell-specific command language, or `jq` as required for installed plugin workflows.
- **FR-010**: Public docs MAY describe WSL or shell availability only as optional or out-of-scope context, never as the required native installed-plugin path.
- **FR-011**: Public trust documentation and release notes MUST describe the implemented XPLAT-003 consumer-trust controls without claiming unimplemented cryptographic guarantees.
- **FR-012**: Native UAT evidence MUST cover Claude and Codex on Windows, macOS, and Linux.
- **FR-013**: Native UAT evidence MUST cover install, bundled-agent verification, first use, scaffold/status, autopilot dry-run, update to the latest tagged release, and safe repair of an intentionally incomplete install.
- **FR-014**: Release-readiness checks MUST block publication when any required native UAT row is missing, placeholder-only, smoke-only, or failing.
- **FR-015**: Doctor/update/autoheal checks MUST detect stale or incomplete installed plugin artifacts before meaningful workflow execution continues.
- **FR-016**: Safe autoheal MUST be limited to trusted missing or stale artifacts whose source identity and integrity can be verified.
- **FR-017**: Unsafe install gaps MUST NOT trigger broad automatic reinstall behavior and MUST print exact manual remediation steps.
- **FR-018**: Update proof MUST show that installed Claude and Codex payloads can update to the latest tagged release and rerun first-use journeys successfully.
- **FR-019**: The release gate MUST block public release on active shell runtime dependencies, incomplete generated payloads, missing bundled agents, stale version metadata, unsafe public claims, or incomplete UAT evidence.
- **FR-020**: The PR review packet MUST trace each major requirement and success criterion to changed files and verification evidence.
- **FR-021**: Version handling MUST respect the existing release process and MUST NOT require manual plugin version edits except through the established release mechanism.
- **FR-022**: The feature MUST preserve the XPLAT-006 and XPLAT-007 handoff boundaries: existing Python helper and gate substrates remain authoritative, while XPLAT-008 proves the installed Claude/Codex release path.

### Reviewability Notes *(if applicable)*

- XPLAT-008 is intentionally one workflow with three internal slices: active installed-runtime surface cutover; generated payload, release, and public docs gates; and native UAT/update/autoheal evidence.
- The sizing warning is accepted for Specify because the release gate is coherent only when active surfaces, generated payloads, docs, UAT, update, and repair evidence are traceable together.
- Generated payload diffs and feature-local process evidence should be labeled clearly in the PR packet so reviewers can focus on source-of-truth changes first.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: harness/adapter, seed/config
- **Projected reviewable LOC**: 250-500
- **Projected production files**: 4-8
- **Projected total files**: 10-25
- **Budget result**: warning accepted
- **Split decision**: Remain one XPLAT-008 spec with three internal slices. Split only if implementation evidence shows generated payload rebuilds or native UAT artifacts make the review packet too large to review coherently.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.
- The PR packet MUST put active source/runtime changes before generated payloads, docs, UAT evidence, and release-readiness output.

### Key Entities *(include if feature involves data)*

- **Installed Runtime Surface**: A Claude or Codex skill, agent, hook, install guide, or generated payload path that can affect installed user workflow execution.
- **Generated Payload**: A committed Claude or Codex distribution artifact users install, including plugin metadata, skills, bundled agents, hooks, runner files, and release documentation.
- **Release Readiness Gate**: A blocking verification result that determines whether the plugin can be publicly released with native cross-platform claims.
- **Native UAT Runbook**: Human-readable evidence for one platform/product journey, including expected results, actual results, operator notes, and pass/fail status.
- **Install Health Finding**: A stale, missing, incomplete, unsafe, or trusted gap found in an installed plugin cache.
- **Repair Action**: Either a bounded autoheal refresh for trusted artifacts or exact manual remediation for unsafe gaps.
- **Public Claim**: Any public docs or release-note statement about platform support, prerequisites, update, repair, or consumer-trust guarantees.
- **Trust Evidence Record**: Manifest, checksum, version, and completeness evidence that connects installed payload behavior to the implemented XPLAT-003 trust model.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of active Claude and Codex installed-runtime surfaces complete the first-use scaffold/status/autopilot-dry-run journey on native Windows, macOS, and Linux without required Bash, Git Bash, WSL, PowerShell-specific command language, or `jq`.
- **SC-002**: Active-runtime no-shell/no-jq checks report zero prohibited active-runtime dependencies in source surfaces, generated payloads, install guidance, and release gates.
- **SC-003**: Claude and Codex generated payload gates verify 100% of expected release metadata, bundled agents, hooks, runner files, and XPLAT-003 manifest/checksum records.
- **SC-004**: All 6 required platform/product UAT rows are complete, readable, non-placeholder, and passing for install, bundled-agent verification, scaffold/status, autopilot dry-run, update, and repair.
- **SC-005**: Release-readiness checks fail for each seeded blocker class: active shell runtime dependency, incomplete payload, missing bundled agent, stale metadata, unsafe public claim, and incomplete UAT evidence.
- **SC-006**: Doctor/autoheal evidence shows every trusted stale or missing artifact case is safely refreshed, and every unsafe gap produces exact manual remediation without broad automatic reinstall behavior.
- **SC-007**: Public docs and release notes contain zero claims of native platform support or cryptographic guarantees that are not backed by implementation and UAT evidence.
- **SC-008**: Reviewers can trace every functional requirement and success criterion to changed files and verification evidence in the PR packet.

## Assumptions

- XPLAT-006 and XPLAT-007 are complete and archived; their Python helper, install inventory, payload, release-readiness, and active-path guard substrates are available for XPLAT-008.
- The source tree remains the source of truth for generated Claude and Codex payloads.
- Public release readiness requires both Claude and Codex installed-plugin evidence across native Windows, macOS, and Linux.
- Safe autoheal is limited to artifacts whose trusted source identity and integrity can be verified; unsafe install-cache drift remains manual remediation.
- Durable native UAT evidence will live under the XPLAT-008 feature directory so it can be reviewed with the spec implementation packet.
- Exact active-runtime inventory, interpreter discovery order, payload completeness manifest, UAT artifact filenames, and autoheal trust boundary details are consensus items for Clarify and Plan, not blockers for this Specify artifact.
