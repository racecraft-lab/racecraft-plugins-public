# Feature Specification: Plugin Source and Payload Bash Eradication

**Feature Branch**: `codex/xplat-009-plugin-source-and-payload-bash-eradication`

**Created**: 2026-07-07

**Status**: Draft

**Input**: User description: "Plugin Source and Payload Bash Eradication"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Clean Plugin Source Substrate (Priority: P1)

As a maintainer, I can run source-level checks and see that the live
`speckit-pro/` plugin source no longer contains Bash scripts or active
Bash-oriented guidance.

**Why this priority**: XPLAT-009 cannot unblock the next runtime cleanup phase
until the plugin source itself matches the Python-only installed-runtime
contract established by XPLAT-008.

**Independent Test**: Can be fully tested by completing the source cleanup slice,
running the source-level no-shell checks, and reviewing the active instruction
scan for zero unallowlisted Bash, `.sh`, `jq`, shell interpolation, or
Unix-only guidance hits.

**Acceptance Scenarios**:

1. **Given** the current plugin source contains live Bash scripts, **When** the
   source cleanup slice is complete, **Then** `speckit-pro/` contains zero live
   `.sh` files and no Python wrapper remains around a live shell script.
2. **Given** active skill, agent, command, helper, gate, and release guidance
   surfaces are scanned, **When** historical/archive paths are excluded through
   the documented allowlist, **Then** no active instruction tells a maintainer
   or plugin user to rely on Bash, `.sh`, `jq`, shell interpolation, Git Bash,
   WSL, PowerShell-specific command language, or Unix-only assumptions.

---

### User Story 2 - Prove Payload and Installed Cache Are Clean (Priority: P2)

As a Claude or Codex plugin user, the generated and installed plugin payloads
contain no Bash scripts and active guidance points only at the direct Python
runner behavior.

**Why this priority**: Source cleanup is not sufficient unless the release
payloads and installed-cache artifacts built from that source also remain clean.

**Independent Test**: Can be fully tested by rebuilding the Claude and Codex
payloads from the cleaned source, producing an installed-cache proof artifact,
and running payload/cache no-shell checks with zero unallowlisted findings.

**Acceptance Scenarios**:

1. **Given** the source cleanup slice has passed, **When** Claude and Codex
   payloads are rebuilt, **Then** the generated payloads contain zero `.sh`
   files and no active Bash or `jq` runtime guidance.
2. **Given** an installed-cache artifact is produced from rebuilt payloads,
   **When** the payload/cache proof guard runs, **Then** it reports zero `.sh`
   files, zero Bash fallback guidance, and zero `jq` requirements.

---

### User Story 3 - Reviewable Historical Allowlist and Regression Guards (Priority: P3)

As a reviewer, I can inspect a narrow historical/archive allowlist and
deterministic guard evidence proving active release behavior does not depend on
Bash, `.sh`, `jq`, shell interpolation, or Unix-only assumptions.

**Why this priority**: Some historical prose may remain valid, but it must not
mask active release behavior or satisfy release readiness.

**Independent Test**: Can be fully tested by inspecting the allowlist and guard
evidence, including seeded regression cases that fail when Bash scripts,
Bash-oriented active guidance, or `jq` requirements are reintroduced.

**Acceptance Scenarios**:

1. **Given** historical or archived prose still references legacy Bash behavior,
   **When** a reviewer inspects the allowlist, **Then** each allowed entry is
   documented as historical/archive-only and cannot count as release-readiness
   evidence.
2. **Given** a `.sh` file, active Bash reference, or active `jq` requirement is
   reintroduced into an in-scope source, generated payload, or installed-cache
   surface, **When** the guard suite runs, **Then** the regression fails with an
   actionable location and reason.

---

### Edge Cases

- A remaining Bash reference appears only in historical/archive prose: the
  guard must allow it only when the path and reason are documented in the
  allowlist, and the entry must not satisfy release-readiness proof.
- A script file is retained as a fixture, generated artifact, or transitional
  wrapper under `speckit-pro/`: the source-level check must fail because the
  feature target is zero live `.sh` files in plugin source.
- An active instruction avoids the word "Bash" but still tells users to run a
  `.sh` file, use `jq`, depend on shell interpolation, or rely on Git Bash,
  WSL, PowerShell-specific command language, or Unix-only behavior: the active
  guidance scan must treat it as an unallowlisted failure.
- A generated payload is clean but the installed-cache proof is missing: the
  feature is incomplete because payload cleanliness must be demonstrated through
  cache proof as well.
- A native operator UAT row from XPLAT-008 remains incomplete: XPLAT-009 must
  preserve that known gap and must not overclaim public native-platform
  readiness.

## Clarifications

### Session 2026-07-07

- Q: What is the authoritative plugin-source shell baseline? A: The live
  worktree scan is authoritative and currently reports 35 `.sh` files under
  `speckit-pro/`; scaffold-time counts are historical setup evidence only.
- Q: How are retained, deferred, or unmapped shell helpers handled? A: Any
  retained active behavior must have explicit Python runner, helper, or gate
  ownership before its shell script is removed; delete-only classification is
  allowed only when no active skill, runtime, test, registry, or workflow owner
  remains.
- Q: Can active registries keep `.sh` path strings after the files are removed?
  A: No. Active registry and active output records must expose Python operation
  IDs. Legacy script names may remain only as inactive provenance or historical
  allowlist entries that are excluded from release-readiness evidence.
- Q: Which guard surfaces must XPLAT-009 tighten? A: XPLAT-009 must add or
  tighten Python-backed source, generated-payload, and installed-cache guards
  for no-shell and no-`jq` proof without adding a shell fallback path.
- Q: What may remain in the historical allowlist? A: Only historical, archive,
  or negative-policy references with path, reason, scope, and
  release-readiness exclusion; runnable examples, active `.sh` paths, `jq`
  requirements, shell interpolation guidance, Git Bash, WSL,
  PowerShell-specific command language, and Unix-only active guidance must fail.
- Q: What is the authoritative zero-Bash guard input set? A: One Python runner
  guard request covers explicit roots for `speckit-pro/`,
  `dist/claude/speckit-pro`, `dist/codex/speckit-pro`, and installed-cache
  proof roots or evidence records; changed-files-only scans and independent
  shell checks are insufficient.
- Q: Which instruction surfaces are active scope? A: Active scan scope includes
  installed, user-facing, and maintainer-facing source plus generated mirrors:
  plugin skills, Codex skills, agents, Codex agents, hooks, `codex-hooks.json`,
  `speckit-pro/scripts/**`, plugin/root current install guidance, and generated
  Claude/Codex payloads.
- Q: What is the guard failure shape? A: The guard uses the runner JSON envelope
  with `status`, `blocking_count`, `classified_counts`, bounded `findings`, and
  a diagnostic such as `zero_bash_guard_blocked`; each finding names surface,
  path, line, category, pattern, reason, classification, active role, and
  remediation.
- Q: How does XPLAT-009 plug into release readiness? A: A registered Python
  runner gate feeds release readiness in-process, and release readiness blocks
  on missing scan roots, missing installed-cache proof, blocking findings, or
  allowlist entries being counted as release-ready evidence.
- Q: What is sufficient installed-cache proof? A: A bounded evidence record must
  include product or surface, installed root, source payload tree or hash, file
  inventory, `.sh` count, active-guidance findings, `source_derived: true`, and
  allowlist exclusion state; clean generated payloads alone are necessary but
  not sufficient, and native operator UAT remains separate.
- Q: What is the source-to-dist rebuild path after source cleanup? A: Use the
  Python runner `payload-gate` / `payload-completeness` operation in apply mode
  with committed `dist/**` as the output target; legacy shell rebuild commands
  and manual edits under `dist/**` are not authoritative.
- Q: How is source-derived payload proof demonstrated? A: Payload evidence must
  include source root/path records, transform records, file-tree hashes, and
  read-only `payload-completeness` results with no missing, extra, mismatched,
  or path-leaking files; zero `.sh` file count alone is not enough.
- Q: What counts as installed-cache zero-Bash proof? A: Per-surface proof is
  created by extracting or copying rebuilt payloads into a bounded fixture or
  temporary installed-cache root, then scanning that source-derived root with
  the zero-Bash guard.
- Q: Which XPLAT-008 evidence remains out of scope? A: Completing the six real
  native UAT rows and public native-platform release claims remains out of
  scope; XPLAT-009 updates source, payload, cache, active-instruction, release
  readiness, and PR packet known-gap evidence only.
- Q: Can mutable real user-cache evidence satisfy XPLAT-009 release readiness?
  A: No. Release readiness must fail when installed-cache proof comes only from
  a mutable real user cache. Real cache evidence may be supplemental UAT context,
  but required proof must be bounded, freshly source-derived from rebuilt
  payloads, and recorded with inventory, hashes or source tree, `.sh` count,
  active-guidance findings, `source_derived: true`, and allowlist exclusion
  state.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The workflow MUST inventory all live `.sh` files and active
  Bash-oriented guidance under `speckit-pro/` before source deletion begins.
- **FR-002**: Active behavior previously owned by plugin-source Bash scripts
  MUST be ported to the established Python runner, helper, or gate behavior
  before the source scripts are removed.
- **FR-003**: The workflow MUST remove every live `.sh` file under
  `speckit-pro/` after the corresponding active behavior is ported or confirmed
  obsolete.
- **FR-004**: The workflow MUST NOT leave Python wrappers, fallback paths, or
  active guidance that continues to invoke live `.sh` files.
- **FR-005**: Active source instructions MUST NOT direct maintainers or plugin
  users to use Bash, `.sh` scripts, `jq`, shell interpolation, Git Bash, WSL,
  PowerShell-specific command language, or Unix-only command assumptions.
- **FR-006**: The workflow MUST rebuild Claude and Codex plugin payloads from
  the cleaned source and prove those generated payloads contain no `.sh` files.
- **FR-007**: The rebuilt Claude and Codex payloads MUST contain no active Bash
  fallback guidance, no active `jq` requirement, and no active guidance that
  conflicts with direct Python runner behavior.
- **FR-008**: The workflow MUST produce installed-cache proof from rebuilt
  payloads showing zero `.sh` files and zero unallowlisted Bash or `jq` active
  guidance.
- **FR-009**: The workflow MUST define and enforce a narrow historical/archive
  allowlist for remaining Bash-related prose, with each allowed entry carrying a
  path, reason, and release-readiness exclusion.
- **FR-010**: Guard evidence MUST fail reintroduced `.sh` files, active Bash
  guidance, active `jq` requirements, shell interpolation guidance, and Unix-only
  active assumptions in in-scope source, generated payload, and installed-cache
  surfaces.
- **FR-011**: The review packet MUST trace each major requirement and success
  criterion to the changed files and deterministic evidence used to validate it.
- **FR-012**: The workflow MUST preserve XPLAT-008 installed-runtime behavior:
  Python 3.11+ direct `speckit_pro_runner` invocation, no Bash fallback, no
  Git Bash or WSL requirement, no `jq` requirement, and no public native-platform
  readiness overclaim.

### Reviewability Notes *(if applicable)*

- The expected review shape is one workflow with two vertical slices:
  source cleanup first, then payload/cache proof and guards.
- Historical/archive prose may remain only through the documented allowlist and
  cannot be used as release-readiness evidence.
- XPLAT-010 owns repository-wide Bash confinement outside this plugin-source and
  payload/cache scope.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: docs/process, seed/config, scheduler/runtime
- **Projected reviewable LOC**: 527-700 excluding generated payload artifacts
  and declared evidence snapshots
- **Projected production files**: 20
- **Projected total files**: 30
- **Budget result**: warning accepted
- **Split decision**: Keep one XPLAT-009 workflow with two vertical slices.
  Slice 1 removes active plugin-source Bash behavior and guidance. Slice 2
  rebuilds payloads, proves installed-cache cleanliness, and tightens guards. If
  planning evidence shows either slice cannot remain reviewable, the workflow
  must record the split decision before implementation proceeds.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.
- The review order MUST identify the two vertical slices and call out generated
  payload or installed-cache proof artifacts separately from hand-authored source
  changes.
- Known gaps MUST preserve the XPLAT-008 native operator UAT status and MUST NOT
  claim that XPLAT-009 completes native platform release readiness.

### Key Entities *(include if feature involves data)*

- **Source Bash Inventory**: A record of live `.sh` files and active guidance
  references under `speckit-pro/`, including classification as port, delete, or
  historical/archive-only.
- **Active Guidance Reference**: A current instruction surface that could affect
  maintainer, reviewer, Claude user, Codex user, release, or install behavior.
- **Historical Allowlist Entry**: A documented exception for historical/archive
  prose, including path, reason, scope, and release-readiness exclusion.
- **Generated Payload Artifact**: A rebuilt Claude or Codex plugin payload that
  must be checked for `.sh` files and active Bash or `jq` guidance.
- **Installed Cache Proof**: Evidence produced from rebuilt payloads showing the
  installed artifact remains Bash-free and aligned with direct Python runner
  behavior.
- **Zero-Bash Guard Result**: Deterministic evidence that in-scope source,
  generated payload, and installed-cache surfaces pass no-shell/no-`jq` checks
  and fail seeded regressions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Source-level checks report 0 live `.sh` files under
  `speckit-pro/`.
- **SC-002**: Active source guidance scans report 0 unallowlisted Bash, `.sh`,
  `jq`, shell interpolation, Git Bash, WSL, PowerShell-specific command
  language, or Unix-only guidance hits.
- **SC-003**: Rebuilt Claude and Codex payload checks each report 0 `.sh` files
  and 0 unallowlisted active Bash or `jq` guidance hits.
- **SC-004**: Installed-cache proof reports 0 `.sh` files, 0 Bash fallback
  guidance hits, and 0 `jq` requirement hits.
- **SC-005**: Guard coverage fails 100% of seeded regression cases for
  reintroduced `.sh` files, active Bash guidance, active `jq` requirements, and
  active Unix-only assumptions in in-scope surfaces.
- **SC-006**: The review packet maps 100% of functional requirements and success
  criteria to changed files and verification evidence.
- **SC-007**: 100% of historical/archive allowlist entries include path, reason,
  scope, and release-readiness exclusion, and 0 allowlist entries are usable as
  release-readiness proof.

## Assumptions

- XPLAT-008 installed-runtime behavior is the baseline and remains in force:
  direct Python 3.11+ `speckit_pro_runner` invocation without Bash, Git Bash,
  WSL, PowerShell-specific command language, or `jq` requirements.
- `speckit-pro/` is the in-scope plugin package source and payload generation
  surface for XPLAT-009. Repository-wide cleanup under top-level `tests/**`,
  top-level `scripts/**`, hooks outside the plugin package, `.specify/**`, and
  GitHub Actions dispatch glue belongs to XPLAT-010.
- Full native operator UAT remains owned by XPLAT-008. XPLAT-009 needs rebuilt
  payload and installed-cache zero-Bash proof, not new native UAT completion.
- Historical/archive prose does not need to be rewritten solely to erase legacy
  Bash wording when it is documented in the allowlist and excluded from release
  readiness.
- The workflow starts as one feature with two planned vertical slices; no child
  specs are created unless later planning or task evidence proves the accepted
  two-slice route cannot stay reviewable.
