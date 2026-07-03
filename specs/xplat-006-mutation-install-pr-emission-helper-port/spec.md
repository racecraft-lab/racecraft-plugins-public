# Feature Specification: Mutation, Install, and PR-Emission Helper Port

**Feature Branch**: `codex/xplat-006-mutation-install-pr-emission-helper-port`

**Created**: 2026-07-03

**Status**: Draft

**Input**: User description: "Port SpecKit Pro state-mutating, install, and PR-emission helpers to the Python 3.11+ standard-library runner with dry-run/apply safety, manifest-driven install completeness, deterministic parity evidence, and no active Claude/Codex cutover."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run Mutation Helpers Safely (Priority: P1)

As a maintainer, I can invoke Python runner equivalents for mutation-capable helpers and receive the same observable JSON, diagnostics, exit-code, dry-run, apply, no-op, dirty-worktree, and partial-failure semantics that the shipped Bash helpers provide today.

**Why this priority**: This is the core blocker for XPLAT-007. Active repo-local gates cannot move away from Bash until mutation behavior is ported with the same failure and safety semantics.

**Independent Test**: Run mutation-helper fixture cases through the runner in fake repositories and compare accepted Bash-reference outputs for each promoted helper or mode.

**Acceptance Scenarios**:

1. **Given** a fake repository and a valid dry-run request for a state-writing helper, **When** the runner handles the request, **Then** it returns planned operations without changing repository, user-home, or GitHub state.
2. **Given** the same fixture and an explicit apply request, **When** the runner handles the request, **Then** it performs only the approved operations, reports applied operations and touched paths, and preserves the current helper's stdout, stderr, and exit-code behavior.
3. **Given** a repo-mutating apply request and a dirty worktree, **When** the helper requires a clean tree, **Then** the runner blocks before writing, returns the existing failure class and remediation, and leaves state unchanged.
4. **Given** a helper failure after one or more planned operations are attempted, **When** the runner exits, **Then** the result identifies partial failure state, rollback or manual remediation notes, and the operation that failed.

---

### User Story 2 - Verify Install Completeness And Safe Repair (Priority: P1)

As an install maintainer, I can run a manifest-driven doctor/preflight check that detects stale releases, missing bundled agents, missing runner files, missing generated payload files, and safe versus unsafe repair cases for Claude and Codex installs.

**Why this priority**: Install completeness and repair classification are needed before XPLAT-007 migrates gates and before XPLAT-008 claims native Claude/Codex cutover readiness.

**Independent Test**: Run doctor/preflight fixtures against fake Claude homes, fake Codex homes, fake plugin caches, fake `gh`, and fake `specify` commands without writing to the real user environment.

**Acceptance Scenarios**:

1. **Given** a fake complete install matching the source manifest, **When** doctor/preflight runs, **Then** it reports complete bundled agents, runner files, generated payload files, and version metadata.
2. **Given** a fake stale or incomplete install, **When** doctor/preflight runs, **Then** it classifies the issue as safe auto-repair, unsafe manual remediation, or blocked with deterministic remediation text.
3. **Given** a repairable fake install and explicit apply approval, **When** the repair helper runs, **Then** it writes only inside the fake home or fake cache boundary and records the repaired files.
4. **Given** a repair request that would touch real `HOME`, a live plugin cache, or a live repository without approval, **When** the helper runs, **Then** it refuses before mutation and reports the required dry-run and approval evidence.

---

### User Story 3 - Review Deterministic Parity Evidence (Priority: P2)

As a release reviewer, I can inspect deterministic fixtures, promotion records, and Bash-reference comparisons proving mutation helper parity without requiring live GitHub mutation, real user-home writes, or active Claude/Codex cutover.

**Why this priority**: The PR must be reviewable despite crossing mutation, install, and PR-emission surfaces. Reviewers need traceable proof for each promoted helper and an explicit boundary around deferred cutover work.

**Independent Test**: Inspect the helper promotion matrix and run the focused Python helper tests plus source-checkout Bash-reference comparisons for the promoted helper set.

**Acceptance Scenarios**:

1. **Given** a promoted Bash-backed helper, **When** a reviewer opens its promotion record, **Then** the record names fixture ids, Bash comparison ids, normalized fields, authoritative Python test command, current status, and deferred follow-up if any.
2. **Given** a helper that performs PR-body, UAT, split-PR, restack, migration, or relocation work, **When** parity tests run, **Then** fake CLIs and fake repositories cover success, no-op, dry-run, invalid input, write failure, and partial-failure cases where applicable.
3. **Given** the final PR review packet, **When** a reviewer reads the known gaps and non-goals, **Then** active Claude/Codex invocation cutover, generated payload cutover, repo-local release-gate migration, native matrix UAT, and public support claims are clearly deferred to XPLAT-007 or XPLAT-008.

---

### Edge Cases

- A request names an unknown helper id, mismatched operation, unsupported mode, or a mixed-mode helper whose read-only behavior was already accepted in XPLAT-005.
- A dry-run request would plan no operations because the target output is already current.
- An apply request targets a repository with a dirty worktree, missing Git metadata, missing fake CLI, malformed fixture JSON, or stale expected manifest.
- A helper input path contains Windows-style separators, spaces, relative components, symlinks, or attempts to escape the repo, plugin, fake-home, or fake-cache boundary.
- Atomic write setup fails because the target directory is missing, unwritable, cross-device, or already contains an incompatible file type.
- A generated output is partially written, a backup cannot be created, or a rollback cannot be completed automatically.
- Fake `gh`, fake `git`, or fake `specify` returns a conflict, network-like error, malformed JSON, or an unexpected success shape.
- The install doctor finds complete source bundles but incomplete generated payload files or mismatched runner manifest/checksum metadata.
- A live mutation path is requested without prior dry-run evidence and explicit operator approval.
- A proposed implementation touches active skill text, hook configuration, generated payloads, public docs, release gates, or native installed-cache claims that are out of scope for XPLAT-006.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The runner MUST support mutation-capable helper dispatch separately from the XPLAT-005 `read_only` helper mode.
- **FR-002**: The runner MUST accept explicit `dry_run` and `apply` modes for mutation-capable helpers and MUST reject unsupported mode/helper/operation combinations before helper execution.
- **FR-003**: The implementation MUST publish a helper and mode matrix classifying each requested helper or mode as Slice 1, Slice 2, Slice 3, deferred, out of scope, or already accepted by XPLAT-005.
- **FR-004**: Mutation helper requests MUST include helper id, operation, mode, inputs, trust-boundary context, and optional approval evidence in a deterministic request shape.
- **FR-005**: Mutation helper results MUST include status, planned operations, applied operations, skipped or no-op operations, touched paths, diagnostics, exit class, rollback notes, and manual remediation actions where applicable.
- **FR-006**: Dry-run mode MUST NOT mutate repository, user-local, plugin-cache, network, or GitHub state and MUST report every planned write, delete, copy, command, PR action, or repair operation.
- **FR-007**: Apply mode MUST mutate only after explicit apply selection, valid inputs, satisfied trust-boundary checks, and any required prior dry-run or approval evidence.
- **FR-008**: Live repository, user-local, plugin-cache, or GitHub mutation MUST remain blocked unless an operator explicitly approves it after dry-run evidence exists.
- **FR-009**: Repo-mutating apply requests MUST block on dirty worktrees unless the helper's behavior is explicitly safe for dirty state and covered by fixtures.
- **FR-010**: File writes MUST use safe atomic behavior for helpers that write or rewrite files, including same-directory temporary files, complete content generation before replacement, and no partially replaced target on failure.
- **FR-011**: Helpers that currently provide backup, rollback, or manual recovery guidance MUST preserve that guidance in the Python result and diagnostics.
- **FR-012**: Filesystem inputs and outputs MUST be resolved inside declared repo, plugin, fake-home, fake-cache, or temporary fixture boundaries before reads or writes occur.
- **FR-013**: Path handling MUST cover Windows-style separators, spaces, relative components, symlinks, line-ending differences, and traversal attempts through deterministic fixtures.
- **FR-014**: Promoted Python helper behavior MUST preserve current stdout JSON schemas, stderr diagnostics, human-readable remediation, and documented exit codes.
- **FR-015**: Each in-scope helper or mode MUST include deterministic fixtures for success, no-op, dry-run, apply, invalid input, missing prerequisite, malformed JSON, dirty worktree, path escape, write failure, and partial failure where that class applies.
- **FR-016**: Every promoted Bash-backed helper MUST pass golden fixture comparison and source-checkout Bash-reference comparison before the Python implementation is marked authoritative.
- **FR-017**: Bash-reference comparisons MUST use explicit argv-list subprocess calls, bounded inputs, fake repositories or fake CLIs by default, and documented normalization for environment-sensitive fields.
- **FR-018**: Promotion records MUST state fixture ids, Bash comparison ids, normalized fields, authoritative Python command, promotion status, rollback guidance, and deferred follow-up.
- **FR-019**: Python helper tests MUST become authoritative per helper only after the corresponding promotion record shows accepted fixture parity and Bash-reference comparison.
- **FR-020**: The install doctor/preflight contract MUST verify expected Claude agents, Codex agents, runner files, generated payload files, release/version metadata, and runner manifest/checksum metadata from source-controlled truth.
- **FR-021**: Doctor/preflight MUST classify missing or stale install state as complete, safe repair, unsafe manual remediation, blocked, or stale release with deterministic remediation text.
- **FR-022**: Install and repair fixtures MUST use fake Claude homes, fake Codex homes, fake plugin caches, fake `gh`, and fake `specify` by default and MUST NOT write the real user home.
- **FR-023**: The `install-codex-agents` port MUST preserve bundled-agent completeness checks, supported model fallback behavior, marketplace snapshot sync semantics, and stale install diagnostics.
- **FR-024**: The `install-curated-set` port MUST preserve check/install/upgrade modes, pinned release or tag resolution behavior, provenance logging, and fake `gh`/`specify` fixture coverage.
- **FR-025**: Coach and preset write helpers MUST preserve audit/apply behavior, generated preset files, registry updates, and remediation text while using mutation-safe file operations.
- **FR-026**: PR-body, UAT-skeleton, final-reviewability-backstop, PR-packet, and workflow-contract output helpers MUST write generated artifacts atomically and preserve existing packet/body content contracts.
- **FR-027**: Multi-PR emission, restack, split-PR state, migration, and relocation helpers MUST use fake repositories and fake `gh` by default, and live mode MUST require clean worktree checks plus explicit approval.
- **FR-028**: Mixed-mode helpers MUST port only deferred write/apply behavior in XPLAT-006 and MUST NOT re-port accepted XPLAT-005 read-only modes.
- **FR-029**: New runner helper logic MUST use Python 3.11+ standard library only, with no new runtime dependency, package install, virtualenv restore, `jq`, Bash, PowerShell, Node, Go, Rust, or Zig for promoted helper execution.
- **FR-030**: New Python subprocess usage MUST avoid `shell=True`, shell-command strings, shell interpolation, and `os.system`; unavoidable subprocess calls MUST use explicit argv sequences and captured stdout/stderr.
- **FR-031**: The implementation MUST update runner manifest/checksum metadata for new or changed runner-owned Python files before claiming preflight readiness.
- **FR-032**: XPLAT-006 MUST NOT change active Claude Code or Codex skill invocation paths, hooks, generated payloads, install guidance, public documentation claims, repo-local release-readiness gates, or native platform UAT evidence.
- **FR-033**: The final scope audit MUST prove zero forbidden active-cutover surfaces changed, or else record a gate failure before implementation can be accepted.
- **FR-034**: The PR review packet MUST map each major helper group and success criterion to changed files, fixture evidence, Bash-reference evidence, promotion status, known gaps, and rollback or manual remediation notes.

### Helper And Mode Matrix Seed

| Slice | Helper or mode group | Required classification |
| --- | --- | --- |
| Slice 1 | Mutation request/result model, registry extension, atomic write primitives, path boundaries, dirty-worktree guard, fake fixture harness, failure classes, promotion records | In scope |
| Slice 2 | `install-curated-set`, `install-codex-agents`, install-completeness doctor/preflight, coach project fixup, reviewability preset write helpers | In scope |
| Slice 3 | `generate-pr-body`, `generate-uat-skeleton`, `final-reviewability-backstop`, PR-packet output, workflow-contract output, `multi-pr-emission`, `restack`, `migrate-structure`, `relocate-process-artifacts`, generated-index write modes, deferred mixed write modes | In scope |
| XPLAT-005 read-only modes | Accepted read-only/advisory helper modes such as prerequisite, detection, marker, validation, planning, topology, and read-only PR-packet validation | Already accepted; do not re-port |
| Later specs | Active repo-local gate migration, generated payload cutover, active Claude/Codex invocation cutover, installed-cache native UAT, release-readiness migration | Out of scope |

### Reviewability Notes *(if applicable)*

- This spec crosses runtime/helper, install, and PR-emission surfaces, so implementation must preserve the accepted three-slice review order and include promotion records before claiming a helper is Python-authoritative.
- Typed reviewability exceptions are not expected for XPLAT-006. If Plan or Tasks proves the work exceeds the warning threshold, the workflow must split helper groups before implementation rather than hiding generated or process files as exceptions.

### Reviewability Budget *(mandatory)*

- **Primary surface**: scheduler/runtime
- **Secondary surfaces, if any**: harness/adapter; seed/config; docs/process
- **Projected reviewable LOC**: 1,800-2,600 excluding deterministic fixture payloads, generated manifest/checksum records, and copied Bash-reference evidence
- **Projected production files**: 12-18
- **Projected total files**: 35-60
- **Budget result**: warning accepted
- **Split decision**: Keep one XPLAT-006 workflow with three internal slices because the accepted design concept keeps mutation safety, install/doctor, and PR-emission/restack/relocation review order explicit. Split into child specs before implementation if Plan or Tasks shows the helper matrix cannot stay reviewable within this structure.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.
- Helper promotion evidence MUST list each promoted helper, mode, fixture ids, Bash-reference comparison ids, normalized fields, authoritative Python test command, and rollback or manual remediation note.
- Known gaps MUST separate unpromoted helpers from explicitly out-of-scope XPLAT-007 and XPLAT-008 work.
- The PR packet MUST state that active Claude/Codex invocation cutover, generated payload cutover, repo-local release-gate migration, native matrix UAT, and public native-platform support claims are not delivered by XPLAT-006.

### Key Entities *(include if feature involves data)*

- **Mutation Helper Request**: Runner input containing helper id, operation, mode, inputs, trust-boundary context, approval evidence, and request metadata.
- **Mutation Helper Result**: Runner output containing status, stdout-equivalent JSON, stderr diagnostics, planned operations, applied operations, touched paths, exit class, rollback notes, and remediation actions.
- **Planned Operation**: A deterministic dry-run record for a write, delete, copy, command, PR action, install repair, migration, relocation, or generated-output update.
- **Applied Operation**: A completed or failed apply-mode operation with target path or command, normalized result, failure class, and rollback or manual remediation note.
- **Install Inventory Manifest**: Source-controlled truth for expected Claude agents, Codex agents, runner files, generated payload files, checksums, versions, and release metadata.
- **Safe Repair Record**: Doctor/preflight classification describing complete, safe repair, unsafe manual remediation, blocked, or stale release status for a fake or approved install target.
- **Parity Fixture**: Golden input/output case proving helper behavior for success, no-op, dry-run, apply, rejected input, write failure, or partial failure.
- **Bash Reference Comparison**: Source-checkout comparison between the existing Bash helper and the Python runner helper using fake state and explicit normalization.
- **Helper Promotion Record**: Per-helper evidence record showing whether Python behavior is golden-only, Bash-compared, Python-authoritative, deferred, or out of scope.
- **Scope Audit Record**: Verification artifact proving the implementation did not modify forbidden active-cutover surfaces.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100 percent of helpers or modes promoted in XPLAT-006 have promotion records with fixture ids, Bash-reference comparison ids when Bash-backed, normalized fields, and an authoritative Python test command.
- **SC-002**: 100 percent of promoted mutation helpers have deterministic fixture coverage for dry-run and apply behavior, plus no-op, dirty-worktree, invalid-input, path-boundary, write-failure, and partial-failure cases where applicable.
- **SC-003**: Doctor/preflight fixtures detect complete, stale, missing-agent, missing-runner-file, missing-generated-payload, checksum mismatch, safe-repair, unsafe-manual-remediation, and blocked states without touching real user-local state.
- **SC-004**: Focused Python mutation-helper tests and Bash-reference comparison tests pass from a source checkout using Python 3.11+ standard library only and no network, package restore, real GitHub mutation, or real user-home writes.
- **SC-005**: Scope audit reports zero active Claude/Codex skill, hook, generated payload, install-guidance, public-doc, release-gate, or native-UAT cutover changes.
- **SC-006**: The PR review packet maps all Slice 1, Slice 2, and Slice 3 helper groups to changed files, verification commands, fixture evidence, promotion status, known gaps, and rollback or manual remediation notes.

## Assumptions

- XPLAT-004 runner foundation and XPLAT-005 read-only helper registry are complete and available in the source checkout.
- Existing Bash helpers remain available as temporary source-checkout references until XPLAT-007 removes them from active repo-local gates.
- XPLAT-006 uses local macOS source-checkout proof and synthetic Windows/path fixtures; installed-cache launch proof and native Windows/macOS/Linux UAT remain XPLAT-008.
- Fake repositories, fake homes, fake plugin caches, fake `gh`, and fake `specify` are the default fixture environment.
- Live repo, user-local, plugin-cache, network, or GitHub mutation is exceptional and requires explicit approval after dry-run evidence.
- The Clarify phase will finalize exact helper/mode grouping, mutation envelope field names, doctor inventory source, parity matrix, and approval evidence representation without changing the scope boundaries above.
