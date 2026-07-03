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
- The install inventory is malformed, source truth has a checksum mismatch, installed metadata is newer than selected inventory, or source/dist/marketplace versions disagree.
- A repair request targets the real home, real plugin cache, or repository state without explicit approval, or attempts to repair outside fake/plugin-owned boundaries.
- A live PR-emission, restack, migration, or relocation request supplies only a boolean approval flag or CLI switch instead of auditable approval evidence tied to prior dry-run output.
- An autopilot workflow or `autopilot-state.json` plan omits Phase 6.5, collapses later phase families, or drops canonical Post items while a run is still incomplete.
- A live mutation path is requested without prior dry-run evidence and explicit operator approval.
- A proposed implementation touches active skill text, hook configuration, generated payloads, public docs, release gates, or native installed-cache claims that are out of scope for XPLAT-006.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The runner MUST support mutation-capable helper dispatch separately from the XPLAT-005 `read_only` helper mode.
- **FR-002**: The runner MUST accept explicit `dry_run` and `apply` modes for mutation-capable helpers and MUST reject unsupported mode/helper/operation combinations before helper execution.
- **FR-003**: The implementation MUST publish a helper and mode matrix classifying each requested helper or mode as Slice 1, Slice 2, Slice 3, deferred, out of scope, or already accepted by XPLAT-005.
- **FR-004**: Mutation helper requests MUST include helper id, operation, mode, inputs, trust-boundary context, and optional approval evidence in a deterministic request shape; live mutation approval evidence MUST include approval id, approver, timestamp, channel, dry-run result id, dry-run hash, allowed boundaries, allowed operations, and optional expiration.
- **FR-005**: Mutation helper results MUST keep the runner envelope stable and place mutation details under `data.mutation`, including `mode`, `mutation_status`, planned operations, applied operations, skipped or no-op operations, planned paths, touched paths, dirty-worktree state, failure operation, rollback notes, and manual remediation actions where applicable.
- **FR-006**: Dry-run mode MUST NOT mutate repository, user-local, plugin-cache, network, or GitHub state and MUST report every planned write, delete, copy, command, PR action, or repair operation.
- **FR-007**: Apply mode MUST mutate only after explicit apply selection, valid inputs, satisfied trust-boundary checks, and any required prior dry-run or approval evidence.
- **FR-008**: Live repository, user-local, plugin-cache, network, or GitHub mutation MUST remain blocked unless an operator explicitly approves it after dry-run evidence exists; boolean flags or mode names alone MUST NOT satisfy approval.
- **FR-009**: Repo-mutating apply requests MUST block on `git status --porcelain=v1 --untracked-files=all` output unless the helper is explicitly declared dirty-safe and covered by fixtures; dry-run MAY report dirty state, and apply no-op MUST return success with no applied operations or touched paths.
- **FR-010**: File writes MUST generate complete content before opening the target, write to a same-directory temporary file, validate and flush/fsync the temporary file, then replace the target with `os.replace`; multi-operation helpers MUST preflight the batch before the first write and report partial failure instead of promising all-or-nothing rollback.
- **FR-011**: Helpers that currently provide backup, rollback, or manual recovery guidance MUST preserve that guidance in the Python result and diagnostics.
- **FR-012**: Filesystem inputs and outputs MUST be resolved inside declared repo, plugin, fake-home, fake-cache, or temporary fixture boundaries before reads or writes occur, and write targets MUST reject symlinks, directories, devices, external absolute paths, and traversal paths.
- **FR-013**: Path and encoding handling MUST cover Windows-style separators, spaces, relative components, symlinks, line-ending differences, and traversal attempts through deterministic fixtures; generated JSON and Markdown MUST be UTF-8 LF with one final newline, while targeted host-file edits MUST preserve existing line endings or explicitly report LF normalization.
- **FR-014**: Promoted Python helper behavior MUST preserve current stdout JSON schemas, stderr diagnostics, human-readable remediation, and documented exit codes.
- **FR-015**: Each in-scope helper or mode MUST include deterministic fixtures for success, no-op, dry-run, apply, invalid input, missing prerequisite, malformed JSON, dirty worktree, path escape, write failure, and partial failure where that class applies.
- **FR-016**: Every promoted Bash-backed helper MUST pass golden fixture comparison and source-checkout Bash-reference comparison before the Python implementation is marked authoritative.
- **FR-017**: Bash-reference comparisons MUST use explicit argv-list subprocess calls, bounded inputs, fake repositories or fake CLIs by default, and documented normalization for environment-sensitive fields.
- **FR-018**: Promotion records MUST state fixture ids, Bash comparison ids, normalized fields, authoritative Python command, promotion status, rollback guidance, and deferred follow-up.
- **FR-019**: Python helper tests MUST become authoritative per helper only after the corresponding promotion record shows accepted fixture parity and Bash-reference comparison.
- **FR-020**: The install doctor/preflight contract MUST verify expected Claude agents, Codex agents, runner files, generated payload files, release/version metadata, marketplace version metadata, and runner manifest/checksum metadata from a committed generated install inventory under `speckit-pro/speckit_pro_runner/`.
- **FR-021**: Doctor/preflight MUST be read-only by default and classify missing or stale install state as complete, safe repair, unsafe manual remediation, blocked, stale release, downgrade refusal, malformed inventory, or source-truth checksum mismatch with deterministic remediation text; repair MUST be a separate apply-mode operation.
- **FR-022**: Install and repair fixtures MUST use fake Claude homes, fake Codex homes, fake plugin caches, fake `gh`, and fake `specify` by default and MUST NOT write the real user home; safe repair is allowed only inside fake or explicitly approved declared boundaries and MUST preserve unrelated files.
- **FR-023**: The `install-codex-agents` port MUST preserve bundled-agent completeness checks, supported model fallback behavior, marketplace snapshot sync semantics, and stale install diagnostics.
- **FR-024**: The `install-curated-set` port MUST preserve check/install/upgrade modes, pinned release or tag resolution behavior, provenance logging, and fake `gh`/`specify` fixture coverage.
- **FR-025**: Coach and preset write helpers MUST preserve audit/apply behavior, generated preset files, registry updates, and remediation text while using mutation-safe file operations.
- **FR-026**: PR-body, UAT-skeleton, final-reviewability-backstop, PR-packet, and workflow-contract output helpers MUST write generated artifacts atomically and preserve existing packet/body content contracts.
- **FR-027**: Multi-PR emission, restack, split-PR state, migration, and relocation helpers MUST use fake repositories and fake `gh` by default; `candidate-dir` behavior MUST remain dry-run command capture, `pr-fixture` behavior MAY exercise fake apply, live PR or restack mutation MUST remain exceptional marker-aware apply after clean-worktree checks and approval, and migration or relocation apply fixtures MUST run only in fake repos unless live repo apply is explicitly approved.
- **FR-028**: Mixed-mode helpers MUST port only deferred write/apply behavior in XPLAT-006 and MUST NOT re-port accepted XPLAT-005 read-only modes.
- **FR-029**: New runner helper logic MUST use Python 3.11+ standard library only, with no new runtime dependency, package install, virtualenv restore, `jq`, Bash, PowerShell, Node, Go, Rust, or Zig for promoted helper execution.
- **FR-030**: New Python subprocess usage MUST avoid `shell=True`, shell-command strings, shell interpolation, and `os.system`; unavoidable subprocess calls MUST use explicit argv sequences and captured stdout/stderr.
- **FR-031**: The implementation MUST update runner manifest/checksum metadata for new or changed runner-owned Python files before claiming preflight readiness.
- **FR-032**: XPLAT-006 MUST NOT change active Claude Code or Codex skill invocation paths, hooks, generated payloads, install guidance, public documentation claims, repo-local release-readiness gates, or native platform UAT evidence.
- **FR-033**: The final scope audit MUST prove zero forbidden active-cutover surfaces changed, or else record a gate failure before implementation can be accepted.
- **FR-034**: The PR review packet MUST map each major helper group and success criterion to changed files, fixture evidence, Bash-reference evidence, promotion status, known gaps, and rollback or manual remediation notes.
- **FR-035**: The implementation MUST harden the Codex autopilot phase-coverage audit with a Python standard-library validator that fails when the workflow or `autopilot-state.json` omits Phase 6.5, collapses later canonical phase families, drops canonical Post items, contains duplicate plan steps, has multiple `in_progress` items, or orders phase checkpoints incorrectly.
- **FR-036**: The phase-coverage hardening MUST be proven by deterministic tests or evals, including at least one passing complete workflow/state fixture and failing fixtures for missing Phase 6.5, missing Post items, collapsed later phases, and malformed state JSON.

### Helper And Mode Matrix

| Slice | Helper or mode group | Required classification |
| --- | --- | --- |
| Slice 1 | Mutation request/result model, mode taxonomy, registry extension, atomic write primitives, path-boundary checks, dirty-worktree guard, fake fixture harness, deterministic failure classes, promotion records | In scope as shared mutation safety foundation only; no named helper port is promoted from Slice 1 alone |
| Slice 2 | `install-curated-set` `check`/`install`/`upgrade`, `install-codex-agents`, `validate-agent-install`/doctor install-completeness checks and safe repair, `project-fixup apply`, `ensure-reviewability-preset` | In scope as install, doctor, coach, and preset write behavior; fake Claude/Codex homes and fake plugin caches are required by default |
| Slice 3 | `generate-pr-body`, `generate-uat-skeleton`, `final-reviewability-backstop`, PR-packet output, workflow-contract output, `multi-pr-emission`, `restack`, `migrate-structure`, `relocate-process-artifacts`, generated-index write/regenerate modes, `plan-layers` marker-plan output, `validate-pr-packet` persistence/workflow-event upserts, `validate-pr-workflow-contract` workflow-event write mode | In scope as PR-emission, restack, migration, relocation, generated-output, and deferred mixed write behavior. Candidate PR emission is dry-run command capture, fake PR fixtures may exercise apply paths, and live GitHub/repo mutation remains exceptional approved apply |
| Slice 3 support | `detect-stack-manager` `detect`/`link`/`sync`/`restack` command-plan and evidence-persistence behavior | In scope as mutation-adjacent support for emission and restack using fake `gh`; the detector emits decisions and command plans only, and actual mutating command execution remains owned by `multi-pr-emission` and `restack` apply paths |
| XPLAT-005 read-only modes | Accepted read-only/advisory helper modes such as prerequisite, detection, marker counting, validation, planning, topology, atomicity routing, and read-only PR-packet validation | Already accepted by XPLAT-005; do not re-port in XPLAT-006 |
| Later specs | Active repo-local gate migration, generated payload cutover, active Claude/Codex invocation cutover, installed-cache native UAT, release-readiness migration, update/autoheal proof, public support claims | Out of scope for XPLAT-006; XPLAT-007 owns active repo-local Python gate migration and XPLAT-008 owns active Claude/Codex cutover plus native installed-plugin proof |

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
- Known gaps MUST separate unpromoted in-scope helpers, deferred XPLAT-007/XPLAT-008 active cutover work, and live-coverage limits; generic "no known gaps" text is not acceptable unless all three categories are explicitly empty.
- The PR packet MUST state that active Claude/Codex invocation cutover, generated payload cutover, repo-local release-gate migration, native matrix UAT, and public native-platform support claims are not delivered by XPLAT-006.

### Key Entities *(include if feature involves data)*

- **Mutation Helper Request**: Runner input containing helper id, operation, mode, inputs, trust-boundary context, approval evidence, and request metadata.
- **Mutation Helper Result**: Runner output preserving the envelope fields `schema_version`, `status`, `exit_code`, `legacy_exit_code`, `diagnostics`, and `data`, with mutation-specific status, planned/applied/skipped operation records, path evidence, dirty-worktree state, failure operation, rollback notes, and remediation actions under `data.mutation`.
- **Live Mutation Approval Evidence**: Auditable object for live repo, user-local, plugin-cache, network, or GitHub apply operations, containing approval id, approver, timestamp, channel, dry-run result id, dry-run hash, allowed boundaries, allowed operations, and optional expiration.
- **Planned Operation**: A deterministic dry-run record for a write, delete, copy, command, PR action, install repair, migration, relocation, or generated-output update, including `operation_id`, `kind`, `target`, `boundary`, `mode`, `content_sha256`, `line_ending_policy`, and expected result.
- **Applied Operation**: A completed or failed apply-mode operation with `operation_id`, `kind`, target path or command, boundary, mode, normalized result, failure class, content hash where applicable, line-ending policy, and rollback or manual remediation note.
- **Install Inventory Manifest**: Committed generated inventory under `speckit-pro/speckit_pro_runner/` that records expected Claude agents, Codex agents, runner files, generated payload files, checksums, plugin versions, marketplace versions, runner metadata, and release metadata without live network discovery.
- **Safe Repair Record**: Doctor/preflight classification describing complete, safe repair, unsafe manual remediation, blocked, stale release, downgrade refusal, malformed inventory, or checksum-mismatch status for a fake or explicitly approved install target, plus planned repair operations and required approval evidence.
- **Parity Fixture**: Golden input/output case proving helper behavior for success, no-op, dry-run, apply, rejected input, write failure, or partial failure.
- **Bash Reference Comparison**: Source-checkout comparison between the existing Bash helper and the Python runner helper using fake state and explicit normalization.
- **Helper Promotion Record**: Per-helper evidence record showing whether Python behavior is golden-only, Bash-compared, Python-authoritative, deferred, or out of scope.
- **Scope Audit Record**: Verification artifact proving the implementation did not modify forbidden active-cutover surfaces.
- **Autopilot Phase Coverage Report**: Python validator output proving the workflow file and `autopilot-state.json` contain Phase 6.5, every canonical phase family, every required Post item, valid ordering, no duplicate plan steps, and no more than one `in_progress` item.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100 percent of helpers or modes promoted in XPLAT-006 have promotion records with fixture ids, Bash-reference comparison ids when Bash-backed, normalized fields, and an authoritative Python test command.
- **SC-002**: 100 percent of promoted mutation helpers have deterministic fixture coverage for dry-run and apply behavior, plus no-op, dirty-worktree, invalid-input, path-boundary, write-failure, and partial-failure cases where applicable.
- **SC-003**: Doctor/preflight fixtures detect complete install, missing Codex agent, missing Claude package agent, stale plugin cache, downgrade refusal, orphan plugin-owned file removal, missing runner file, checksum mismatch, missing generated payload file, malformed inventory, path escape or symlink rejection, missing fake `gh` or `specify`, real-home refusal, safe-repair, unsafe-manual-remediation, and blocked states without touching real user-local state.
- **SC-004**: Focused Python mutation-helper tests and Bash-reference comparison tests pass from a source checkout using Python 3.11+ standard library only and no network, package restore, real GitHub mutation, or real user-home writes.
- **SC-005**: Scope audit reports zero active Claude/Codex skill, hook, generated payload, install-guidance, public-doc, release-gate, or native-UAT cutover changes.
- **SC-006**: The PR review packet maps all Slice 1, Slice 2, and Slice 3 helper groups to changed files, verification commands, fixture evidence, promotion status, known gaps, and rollback or manual remediation notes.
- **SC-007**: Phase-coverage hardening tests pass and include regression proof that missing Phase 6.5, missing Post items, collapsed later phases, and malformed `autopilot-state.json` are rejected before an autopilot run can advance.

## Assumptions

- XPLAT-004 runner foundation and XPLAT-005 read-only helper registry are complete and available in the source checkout.
- Existing Bash helpers remain available as temporary source-checkout references until XPLAT-007 removes them from active repo-local gates.
- XPLAT-006 uses local macOS source-checkout proof and synthetic Windows/path fixtures; installed-cache launch proof and native Windows/macOS/Linux UAT remain XPLAT-008.
- Fake repositories, fake homes, fake plugin caches, fake `gh`, and fake `specify` are the default fixture environment.
- Live repo, user-local, plugin-cache, network, or GitHub mutation is exceptional and requires explicit approval after dry-run evidence.
- The Clarify phase will finalize exact helper/mode grouping, mutation envelope field names, doctor inventory source, parity matrix, and approval evidence representation without changing the scope boundaries above.
