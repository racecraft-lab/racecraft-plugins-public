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

As a reviewer, I can inspect filled native UAT runbooks, public docs, README guidance, release notes, and traceability evidence that match the implemented support and consumer-trust model.

**Why this priority**: Reviewers need release-reviewable proof that XPLAT-003, XPLAT-006, and XPLAT-007 handoffs are enforced in the installed plugin path.

**Independent Test**: Can be tested by reviewing the feature-local evidence packet, UAT runbooks, public docs, README guidance, release notes, and release-readiness output without relying on private context.

**Acceptance Scenarios**:

1. **Given** native UAT runbooks for Claude and Codex on Windows, macOS, and Linux, **When** a reviewer inspects them, **Then** every platform/product row is filled with install, bundled-agent verification, scaffold/status, autopilot dry-run, update, and repair evidence.
2. **Given** public install, first-run, troubleshooting, trust, README, and release-note content, **When** a reviewer checks support claims, **Then** the docs claim only implemented and UAT-proven support and do not overstate cryptographic guarantees.
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
- **FR-002**: Active installed-runtime Claude and Codex surfaces MUST invoke the Python 3.11+ standard-library runner behavior as the installed runtime substrate by launching an argv-style command that resolves a supported interpreter and runs `-m speckit_pro_runner`.
- **FR-003**: Active installed-runtime surfaces MUST NOT require Bash, `.sh` helpers, `jq`, shell interpolation, shell redirection, Git Bash, WSL, PowerShell-specific command language, or Unix-only path assumptions.
- **FR-004**: No-shell/no-jq guards MUST fail active installed-runtime source paths, generated payloads, install guidance, and release gates when prohibited shell-only runtime behavior is reintroduced.
- **FR-005**: No-shell/no-jq guards MUST allow explicitly scoped archive/provenance text, minimal CI dispatch glue that only invokes Python gates, and upstream GitHub Spec Kit generated `.specify/scripts/bash/` helpers in consumer projects.
- **FR-006**: Generated Claude and Codex payloads MUST be rebuilt from source for this release-readiness path.
- **FR-007**: Generated payload verification MUST prove release version metadata, bundled agents, hooks, required runner files, and XPLAT-003 manifest/checksum metadata are complete for both Claude and Codex payloads.
- **FR-008**: Release-readiness checks MUST fail when generated payloads are incomplete, stale, missing bundled agents, missing hooks, missing runner files, or missing required trust metadata.
- **FR-009**: Public install and first-run docs, including `README.md` and `speckit-pro/README.md` when they carry install or update guidance, MUST describe the supported installed-plugin prerequisites and MUST NOT describe Bash, Git Bash, WSL, PowerShell-specific command language, or `jq` as required for installed plugin workflows.
- **FR-010**: Public docs MAY describe WSL or shell availability only as optional or out-of-scope context, never as the required native installed-plugin path.
- **FR-011**: Public trust documentation, README guidance, and release notes MUST describe the implemented XPLAT-003 consumer-trust controls without claiming unimplemented cryptographic guarantees.
- **FR-012**: Native UAT evidence MUST cover Claude and Codex on Windows, macOS, and Linux.
- **FR-013**: Native UAT evidence MUST cover install, bundled-agent verification, first use, scaffold/status, autopilot dry-run, update to the latest tagged release, and safe repair of an intentionally incomplete install.
- **FR-014**: Release-readiness checks MUST block publication when any required native UAT row is missing, placeholder-only, smoke-only, or failing.
- **FR-015**: Doctor/update/autoheal checks MUST detect stale or incomplete installed plugin artifacts before meaningful workflow execution continues.
- **FR-016**: Safe autoheal MUST be limited to trusted missing or stale artifacts whose expected path, source identity, version or release channel, and checksum-backed integrity can be verified.
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
- **Projected total files**: 10-30
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
- **Interpreter Resolution Record**: The detected Python launcher, resolved executable path, version, platform, attempted candidates, and failure diagnostics for installed runner invocation.
- **Public Claim**: Any public docs, README, or release-note statement about platform support, prerequisites, update, repair, or consumer-trust guarantees.
- **Trust Evidence Record**: Manifest, checksum, version, and completeness evidence that connects installed payload behavior to the implemented XPLAT-003 trust model.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of active Claude and Codex installed-runtime surfaces complete the first-use scaffold/status/autopilot-dry-run journey on native Windows, macOS, and Linux without required Bash, Git Bash, WSL, PowerShell-specific command language, or `jq`.
- **SC-002**: Active-runtime no-shell/no-jq checks report zero prohibited active-runtime dependencies in source surfaces, generated payloads, install guidance, and release gates.
- **SC-003**: Claude and Codex generated payload gates verify 100% of expected release metadata, bundled agents, hooks, runner files, and XPLAT-003 manifest/checksum records.
- **SC-004**: All 6 required platform/product UAT rows are complete, readable, non-placeholder, and passing for install, bundled-agent verification, scaffold/status, autopilot dry-run, update, and repair.
- **SC-005**: Release-readiness checks fail for each seeded blocker class: active shell runtime dependency, incomplete payload, missing bundled agent, stale metadata, unsafe public claim, and incomplete UAT evidence.
- **SC-006**: Doctor/autoheal evidence shows every trusted stale or missing artifact case is safely refreshed, and every unsafe gap produces exact manual remediation without broad automatic reinstall behavior.
- **SC-007**: Public docs, README guidance, and release notes contain zero claims of native platform support or cryptographic guarantees that are not backed by implementation and UAT evidence.
- **SC-008**: Reviewers can trace every functional requirement and success criterion to changed files and verification evidence in the PR packet.

## Assumptions

- XPLAT-006 and XPLAT-007 are complete and archived; their Python helper, install inventory, payload, release-readiness, and active-path guard substrates are available for XPLAT-008.
- The source tree remains the source of truth for generated Claude and Codex payloads.
- Public release readiness requires both Claude and Codex installed-plugin evidence across native Windows, macOS, and Linux.
- Safe autoheal is limited to artifacts whose trusted source identity and integrity can be verified; unsafe install-cache drift remains manual remediation.
- Durable native UAT evidence will live under the XPLAT-008 feature directory so it can be reviewed with the spec implementation packet.
- Durable UAT evidence uses a feature-local `.process/uat-matrix.md` with six required platform/product rows, plus optional detailed evidence files under `.process/uat/`.
- Exact active-runtime inventory, payload completeness manifest, UAT artifact filenames, and autoheal trust boundary details are consensus items for Clarify and Plan, not blockers for this Specify artifact.

## Clarifications

### Session 1 - Active Surface Inventory

- Active-runtime guard scope blocks prohibited shell-only behavior in active Claude/Codex skills, agents, hooks, install guidance, generated runtime payloads, and release gates. It explicitly allows archive/provenance text, tests/fixtures, generated changelog or README prose that is not active runtime instruction, minimal CI dispatch glue that only invokes Python gates, and upstream GitHub Spec Kit generated `.specify/scripts/bash/` helpers in consumer projects.
- Active installed surfaces must launch the runner without shell parsing: discover a Python `>=3.11` interpreter, invoke argv as `[resolved_python, "-m", "speckit_pro_runner"]`, send one JSON request on stdin, parse JSON stdout, and surface stderr diagnostics without requiring `jq` or shell redirection.
- Interpreter discovery order is Windows `py -V:3`, then `py -3`, then `python`, then `python3`; macOS and Linux use `python3`, then `python`. Each candidate must be version-probed and accepted only when it resolves to Python `>=3.11`. Preflight evidence must record the resolved executable path and version.
- Generated payload completeness is source-derived, not inferred from the current `dist/**` tree. The expected manifest covers Claude and Codex plugin manifests, skills, bundled agents, hooks, runner package files, runner manifest/checksum files, version metadata, and XPLAT-003 trust records.
- Doctor/autoheal may automatically refresh only bounded generated payload files, bundled Codex TOML agents, hooks, runner files, and manifest/checksum metadata whose expected path, source identity, release channel, and digest verify. Unknown files, trust-root changes, marketplace source changes, traversal/out-of-cache paths, missing trust metadata, unverified mismatches, and broad reinstall/wipe-copy behavior must stop with exact manual remediation.

### Session 2 - Payload, Release, and Trust Contract

- Expected payload inventory is source-derived, not copied from the current `dist/**` tree. Claude payloads include `.claude-plugin/plugin.json`, Claude skills, Claude agents, hooks, install guidance, the full `speckit_pro_runner` package, runner manifest/checksum metadata, release/version metadata, and XPLAT-003 trust records. Codex payloads include `.codex-plugin/plugin.json`, Codex-normalized skills, Codex agents, `codex-hooks.json`, install guidance, the full runner package, runner manifest/checksum metadata, release/version metadata, and XPLAT-003 trust records. Opposite-platform source-only files are excluded from each payload.
- Release-readiness gates rebuild payloads to a temporary or staging location, compute the expected source inventory plus per-file SHA-256 or file-tree hashes, and compare the result against committed `dist/claude/speckit-pro/**` and `dist/codex/speckit-pro/**`. The gates must account for explicit transforms, including Claude guard stripping, Codex skill overlays or path rewrites, and manifest path normalization.
- Release-readiness must fail on missing, extra, changed, path-leaking, or non-deterministic generated files; active shell runtime dependencies; incomplete payload inventory; stale generated payloads; stale version metadata; missing or mismatched runner manifest/checksum/trust records; unsupported public claims; incomplete UAT/update/repair evidence; or unsafe autoheal claims beyond bounded manifest/checksum refreshes.
- Version consistency is blocking across source plugin manifests, generated dist manifests, Claude and Codex marketplace indexes, `.release-please-manifest.json`, runner manifest `plugin_version`, and generated release evidence. `runner_version` is independent but must be present and covered by runner manifest/checksum verification. Manual plugin version edits remain out of scope; release-please owns version bumps.
- Public docs, README guidance, and release notes may claim only implemented and verified controls: Python 3.11+ standard-library runner as the installed runtime, source-built generated payloads with completeness/version/SHA-256 manifest gates, runner preflight or doctor verification of plugin root/prerequisites/metadata/integrity records, local verification and bounded repair paths with manual remediation for unsafe drift, and native Claude/Codex support only for platform/product rows with completed UAT.
- Public docs, README guidance, and release notes must not claim signing, SBOMs, SLSA or in-toto provenance attestations, reproducible-build guarantees, formal audit or certification, vulnerability-free status, marketplace-enforced verification, or cryptographic trust-chain verification unless those controls are separately implemented and evidenced.

### Session 3 - UAT, Update, and Autoheal

- Durable native UAT evidence uses `specs/xplat-008-claude-codex-cutover-universal-install-release-gate/.process/uat-matrix.md`, with optional detailed evidence files under `.process/uat/`. The existing generic `.process/uat-runbook.md` remains useful for reviewer instructions but is not sufficient by itself for XPLAT-008 release readiness.
- The UAT matrix must contain six required product/platform rows: Claude on Windows, Claude on macOS, Claude on Linux, Codex on Windows, Codex on macOS, and Codex on Linux. Each row must include platform, product, operator/date, host version, plugin version or latest tag, installed cache path, interpreter resolution, runner invocation IDs, install result, bundled-agent verification, first use, scaffold/status, autopilot dry-run, latest-tag update, incomplete-install repair, expected result, actual result, evidence link, operator notes, and pass/fail.
- Release-readiness must parse the XPLAT-008 UAT matrix as a structured contract, not rely only on generic UAT runbook placeholder validation. It must fail on missing rows, placeholder-only rows, smoke-only evidence, failing rows, empty expected or actual result fields, raw HTML anchors, missing evidence links, or public support claims not backed by passing rows.
- Installed-cache interpreter evidence uses the prior consensus order and diagnostics: Windows probes `py -V:3`, then `py -3`, then `python`, then `python3`; macOS and Linux probe `python3`, then `python`; only Python `>=3.11` is accepted. Failure records must include attempted candidates, resolved executable when present, version, platform, cache root, failure code, stderr or diagnostic text, and exact remediation without shell fallback.
- Safe autoheal may repair only installed-cache artifacts with verified expected path, source identity, release channel or latest tag, and SHA-256 or file-tree digest. Candidate artifacts are bounded to generated payload files, bundled agents, hooks, runner files, and manifest/checksum metadata inside the trusted installed plugin cache.
- Manual remediation is mandatory for unknown files, extra or untracked files, path traversal or out-of-cache targets, missing trust metadata, digest or source mismatch, trust-root changes, marketplace-source drift, unsupported platform claims, real-home mutation before the active cutover boundary is implemented, and any broad reinstall or wipe-copy behavior. Checksum-backed repair supports integrity/completeness repair only and must not be described as signing, provenance, SLSA compliance, or a cryptographic trust chain.
