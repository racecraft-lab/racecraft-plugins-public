# Feature Specification: Read-Only Helper Port

**Feature Branch**: `codex/xplat-005-read-only-helper-port`

**Created**: 2026-07-02

**Status**: Draft

**Input**: User description: "Read-only and advisory helper behavior must move from Bash helper scripts onto the XPLAT Python runner foundation with fixture parity, stable tests, and no active Claude Code or Codex cutover."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run Read-Only Helpers Through The Runner (Priority: P1)

As a maintainer, I can run Python runner equivalents for prerequisite, detection, marker, validation, confidence, index, topology, and planning helpers and receive the same JSON, diagnostic, and exit semantics as the current helper surface.

**Why this priority**: Maintainers need proof that the read-only gates can work without Bash, `jq`, shell parsing, process substitution, or Unix-path assumptions before any mutation helper or active plugin cutover proceeds.

**Independent Test**: Run the Slice 1 helper ports against deterministic fixtures and source-checkout Bash references; verify stdout JSON, stderr diagnostics, and exit codes match for accepted cases.

**Acceptance Scenarios**:

1. **Given** a source checkout with existing prerequisite, detection, marker, validation, and confidence helper behavior, **When** the maintainer invokes the Python runner equivalents for the same fixture cases, **Then** the Python outputs preserve the current stdout JSON schemas, stderr diagnostics, and documented exit codes.
2. **Given** invalid inputs, missing files, or unsupported feature-directory states, **When** a ported read-only helper runs through the Python runner, **Then** it reports the same failure class and exit semantics as the current helper without requiring Bash, `jq`, `grep`, `sed`, Node, PowerShell, Go, Rust, Zig, package install, or virtualenv restore.
3. **Given** Windows-style paths, spaces in paths, and source-checkout relative paths represented in fixtures, **When** a ported helper evaluates them, **Then** the result is deterministic and does not depend on Unix-only parsing behavior.

---

### User Story 2 - Add Helper Ports Through A Small Registry Pattern (Priority: P2)

As a helper-port implementer, I can add a read-only helper through a small registry plus per-helper module pattern and prove parity through golden fixtures and Bash-reference comparisons.

**Why this priority**: XPLAT-006 needs a reusable extension point for later mutation helper ports, but XPLAT-005 must keep the abstraction small and bounded to read-only behavior.

**Independent Test**: Add or inspect a representative ported helper module, dispatch it through the registry, and verify its fixture parity tests are isolated from other helpers.

**Acceptance Scenarios**:

1. **Given** a ported helper registered with the runner dispatch surface, **When** the helper name and arguments are submitted to the runner, **Then** dispatch reaches the intended per-helper module and returns the documented result envelope.
2. **Given** a helper fixture with expected stdout, stderr, and exit code, **When** the Python helper output is compared with the golden fixture and the current Bash reference, **Then** differences are reported in a way that identifies the field, stream, or exit behavior that drifted.
3. **Given** a helper whose current Bash output includes environment-sensitive values, **When** parity tests run, **Then** the accepted normalization rules are explicit, deterministic, and limited to those environment-sensitive fields.

---

### User Story 3 - Review Release-Gate Promotion And Scope Boundaries (Priority: P3)

As a release reviewer, I can see which helpers have been promoted to Python release gates, which Bash helpers remain temporary references, and why no active Claude Code, Codex, install, or public platform support claim happened in XPLAT-005.

**Why this priority**: Reviewers need clear migration evidence without mistaking helper parity for installed-plugin or native-platform support.

**Independent Test**: Inspect the internal evidence, release-gate status, and PR review packet for a helper-by-helper promotion record plus explicit non-goal coverage.

**Acceptance Scenarios**:

1. **Given** a helper has accepted fixture and Bash-reference parity, **When** release-gate status is reviewed, **Then** the Python standard-library test is identified as authoritative for that helper while the Bash helper remains only as a temporary reference until XPLAT-007 cutover.
2. **Given** unported or not-yet-promoted helpers remain, **When** release-gate status is reviewed, **Then** those helpers are clearly identified as still using the current Bash reference path and not counted as Python-promoted.
3. **Given** XPLAT-005 has completed, **When** the scope is audited, **Then** there are no active Claude Code or Codex skill, hook, generated payload, install, public documentation, PR-emission, split-state, restack, or repository/user-local mutation cutovers, except for bounded PR-review packet rendering remediation that does not add runner mutation behavior.
4. **Given** local macOS source-checkout smoke evidence exists, **When** a reviewer reads it, **Then** it proves the accepted source-checkout runner path only and does not claim installed-cache launch proof or full native Windows/macOS/Linux matrix support.

### Edge Cases

- A helper currently reads optional files that may not exist in older or partially scaffolded feature directories.
- A helper currently emits duplicate or repeated markers, warnings, or advisory findings that must remain stable for downstream gates.
- A helper currently accepts paths with spaces, symlinks, relative components, or Windows-style separators.
- A fixture includes JSON object field ordering that must be compared semantically, while stream text and exit codes remain exact unless an explicit normalization rule applies.
- A helper's current Bash reference depends on source-checkout state; installed-cache and user-local state are not used as parity inputs in XPLAT-005.
- Late `validate-pr-packet` coverage must remain read-only validation only; PR body generation, PR emission, split PR state, and restack behavior are excluded.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST expose a Python runner helper registry/dispatch surface for read-only and advisory helpers.
- **FR-002**: The system MUST organize each ported helper behind a per-helper module convention that XPLAT-006 can reuse without introducing a generic framework.
- **FR-003**: Slice 1 MUST include registry/dispatch plus prerequisite, detection, marker, validation, and confidence helper ports.
- **FR-004**: Slice 2 MUST include read-only/advisory ports for spec-index behavior, topology checks, atomicity routing, layer-planning analysis, workflow-contract validation, and late `validate-pr-packet` validation.
- **FR-005**: The system MUST NOT port or invoke mutation helpers that write PR packets, generate PR bodies, emit split PR state, perform restack changes, relocate artifacts, install agents, modify generated payloads, or mutate repository or user-local state.
- **FR-006**: Each ported helper MUST preserve the current helper's stdout JSON schema for equivalent accepted inputs.
- **FR-007**: Each ported helper MUST preserve the current helper's stderr diagnostics for equivalent accepted and rejected inputs, except for explicitly documented deterministic normalization.
- **FR-008**: Each ported helper MUST preserve the current helper's documented exit-code semantics for success, advisory, usage, missing-input, and validation-failure cases.
- **FR-009**: New runner/helper logic MUST use Python 3.11+ standard library only.
- **FR-010**: New runner/helper logic MUST NOT require `jq`, Bash, PowerShell, Node, Go, Rust, Zig, package installation, virtualenv restore, or network access.
- **FR-011**: The parity suite MUST include deterministic golden fixtures for each promoted helper.
- **FR-012**: The parity suite MUST compare Python helper output with the current source-checkout Bash reference before a helper is accepted as promoted.
- **FR-013**: The parity suite MUST compare JSON stdout semantically and MUST compare stderr diagnostics and exit codes according to each helper's documented behavior.
- **FR-014**: Environment-sensitive output normalization MUST be explicit, deterministic, and limited to fields that cannot be stable across source checkouts.
- **FR-015**: Python tests MUST become authoritative release gates per helper only after that helper's fixture parity and Bash-reference comparison are accepted.
- **FR-016**: Bash helpers MUST remain available as temporary reference implementations for unported helpers and for ported helpers until active cutover in XPLAT-007.
- **FR-017**: The implementation evidence MUST record, per helper, whether it is Python-promoted, Bash-reference-only, or intentionally out of XPLAT-005 scope.
- **FR-018**: The implementation evidence MUST separate source-checkout parity from installed-plugin launch proof and public native-platform support claims.
- **FR-019**: The local macOS smoke MUST run against the source checkout and MUST avoid claims about installed-cache execution or full native Windows/macOS/Linux support.
- **FR-020**: The feature MUST preserve the accepted two-slice strategy: Slice 1 for foundational registry/dispatch and prerequisite/status helpers; Slice 2 for index/topology/planning validators and late read-only PR-packet validation.
- **FR-021**: The feature MUST NOT update active Claude Code or Codex skill files, hook configuration, generated payloads, installer behavior, marketplace/public documentation, or install-facing invocation paths, except for bounded PR-review packet generator/validator remediation required to make the XPLAT-005 review packet describe the actual feature scope.
- **FR-022**: The PR review packet MUST identify non-goals, helper promotion status, Bash-reference retention, verification evidence, known gaps, rollback expectations, and the review order for the two slices.
- **FR-023**: For helpers that currently emit machine-readable failure output, rejected-input fixtures MUST define the expected stdout JSON schema, stderr diagnostics, diagnostic/remediation content where present, and exact nonzero exit class.
- **FR-024**: The parity plan MUST map each applicable helper failure class to an exact nonzero exit code for invalid input, missing input, malformed JSON, missing file, unsupported path, prerequisite failure, validation failure, and subprocess/preflight failure.
- **FR-025**: Each applicable helper MUST include fixture coverage for every rejected-input scenario class it supports, rather than relying on one generic rejected fixture per helper.
- **FR-026**: New Python helper ports and Bash-reference comparison harnesses MUST NOT use `shell=True`, shell-command strings, `os.system`, shell interpolation, or unbounded subprocess input; unavoidable subprocess calls MUST use explicit argv sequences.
- **FR-027**: Filesystem inputs MUST be resolved against the repo or plugin trust boundary before reading, including symlinks and relative components, and helpers MUST reject traversal or symlink escapes.
- **FR-028**: Runner source manifest and checksum metadata MUST include every new or modified XPLAT-005 runner source file and MUST remain source-checkout metadata only, with generated-payload propagation deferred to XPLAT-007.

### Phase 2 Clarifications

#### Helper And Mode Matrix

| Scope | Helper or Mode | XPLAT-005 Decision |
|---|---|---|
| Slice 1 | Helper registry/dispatch | In scope as the small runner extension point for read-only/advisory helpers |
| Slice 1 | `check-prerequisites`, `detect-commands`, `detect-presets` | In scope as prerequisite and detection helper ports |
| Slice 1 | `count-markers`, `validate-gate`, `reviewability-gate`, `estimate-reviewable-loc` | In scope as marker, validation, and reviewability helper ports |
| Slice 1 | `resolve-confidence-mode`, `confidence-gate` | In scope as confidence helper ports |
| Slice 2 | `generate-spec-index --check` | In scope as read-only stale-index validation parity |
| Slice 2 | `o5-topology`, `atomicity-route`, `plan-layers <feature-dir>` | In scope as read-only topology, atomicity, and layer-planning analysis |
| Slice 2 | `validate-pr-workflow-contract` | In scope as read-only workflow-contract validation |
| Slice 2 | `validate-pr-packet` | In scope only for read-only validation output, stderr diagnostics, and exit-code parity |
| Out of scope | `detect-stack-manager` | Deferred to XPLAT-006 because it is tied to PR emission/restack behavior and persistence |
| Out of scope | `generate-spec-index` default write/regenerate mode | Deferred because it mutates `SPEC-MOC.md` artifacts |
| Out of scope | `plan-layers marker-plan ... <output>` | Deferred because it writes marker-plan output files |
| Out of scope | `validate-pr-packet` validation-result persistence and workflow-event upserts | Deferred because they mutate repository artifacts |

#### Parity And Promotion Rules

- Every promoted Bash-backed read-only/advisory helper MUST pass both golden fixture parity and source-checkout Bash-reference comparison before it can be marked Python-promoted.
- Golden-only fixtures are limited to runner envelope/registry dispatch behavior, typed-path and subprocess safety, malformed runner request cases, synthetic Windows/no-Bash/path fixtures, and normalization unit tests.
- JSON stdout MUST be compared semantically. Stderr diagnostics, diagnostic codes, statuses, booleans, counts, route/status enums, public text, and exit codes MUST remain exact unless a field is explicitly listed as normalized.
- Normalization MAY apply only to repo/worktree absolute paths converted to repo-relative values, temp paths, timestamps, executable paths or versions when not fixture-controlled, platform/architecture/runtime identity fields, and branch/worktree metadata when the test intentionally uses live git state.
- Rejected-input parity MUST cover helper-specific failure classes, stdout JSON for helpers that emit it, stderr diagnostics, deterministic remediation text or runner diagnostic remediation actions where present, and exact nonzero exit-code mapping.
- Helper implementations and Bash-reference comparison harnesses MUST use argv-list subprocess calls only when subprocess execution is unavoidable; shell invocation and shell interpolation are out of scope for promoted Python helper logic.
- Helper path handling MUST canonicalize file inputs through repo/plugin trust-boundary checks and reject path traversal or symlink escapes before reading.
- The helper promotion record MUST include helper id, slice, Bash script path, runner operation/module, fixture ids, Bash comparison ids, normalized fields, status (`python_authoritative`, `bash_reference_only`, or `out_of_scope`), authoritative test command, and deferred follow-up.

#### Local Source-Checkout Smoke Boundary

The smallest local macOS source-checkout smoke command is:

```bash
printf '%s\n' '{"schema_version":"1.0","request_id":"xplat-005-smoke","helper_id":"runner","operation":"runtime-info","mode":"read_only","inputs":{}}' | PYTHONPATH=speckit-pro python3 -m speckit_pro_runner
```

This smoke proves only that the source-checkout Python runner launches locally,
accepts the JSON envelope through stdin, emits one JSON stdout response, reports
`status: ok`, reports `source_vs_installed_context: source_checkout`, and exposes
platform/runtime/plugin-relative metadata. It does not prove installed-cache
launch, generated payload propagation, active Claude/Codex invocation, helper
parity, mutation-helper safety, or full native Windows/macOS/Linux support.

### Reviewability Notes *(if applicable)*

- XPLAT-005 is accepted as one workflow with two internal slices so the registry pattern and helper parity can be reviewed together while keeping mutation and active cutover work out of scope.
- The setup reviewability gate warned that the planned surfaces span harness/adapter and docs/process concerns; this warning is accepted only for the read-only/advisory helper port scope.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: docs/process; test fixtures
- **Projected reviewable LOC**: 250
- **Projected production files**: 4
- **Projected total files**: 12
- **Budget result**: warning accepted
- **Split decision**: Remain one XPLAT-005 workflow with two internal slices. Split into child specs only if Plan or Tasks proves the helper registry plus read-only parity work cannot stay reviewable.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.
- Review order MUST present Slice 1 registry/status-helper parity before Slice 2 index/topology/planning validator parity.
- Known gaps MUST distinguish unpromoted Bash-reference helpers from out-of-scope mutation or active-cutover helpers.
- The PR packet MUST include the helper promotion record fields listed in Phase 2 Clarifications.

### Scope Boundaries

- XPLAT-005 is limited to read-only and advisory helper ports plus their tests and internal evidence.
- Active Claude Code and Codex skill, hook, generated payload, install, marketplace, and public documentation cutover remain XPLAT-007.
- Bounded PR-review packet rendering remediation may update `generate-pr-body.sh`, `validate-pr-packet.sh`, their generated source copies, and generated reference docs only to keep this PR's reviewer packet truthful; the runner must still not invoke PR body generation or PR emission.
- Mutation helpers for PR packets, PR bodies, split PR state, restack, artifact relocation, installer behavior, and repository/user-local writes remain out of scope for XPLAT-005.
- `generate-spec-index` write/regenerate mode and `validate-pr-packet` validation-result or workflow-event persistence remain out of scope; XPLAT-005 may port only their read-only validation behavior.
- Full native Windows/macOS/Linux installed-plugin UAT remains XPLAT-007.
- Removing Bash helpers globally remains out of scope until XPLAT-007.

### Key Entities *(include if feature involves data)*

- **Helper Registry Entry**: A dispatch record that names a ported helper, its module target, accepted operation shape, and promotion status.
- **Ported Helper Module**: A Python standard-library helper implementation that performs one read-only or advisory operation through the runner.
- **Parity Fixture**: A deterministic input/output case containing expected stdout JSON, stderr diagnostics, exit code, and any explicit normalization rule.
- **Bash Reference Comparison**: A source-checkout comparison that runs or records the current Bash helper behavior as the migration reference for a fixture.
- **Promotion Record**: Per-helper evidence showing whether Python tests are authoritative, Bash remains temporary reference-only, or the helper is out of scope; it includes helper id, slice, Bash script path, runner operation/module, fixture ids, Bash comparison ids, normalized fields, status, authoritative test command, and deferred follow-up.
- **Source-Checkout Smoke Evidence**: Local macOS evidence proving the accepted runner path from the repository checkout without installed-cache or native matrix claims.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every Python-promoted Slice 1 helper, golden fixture comparison and Bash-reference comparison pass with matching JSON semantics, diagnostics, and exit-code behavior.
- **SC-002**: For every Python-promoted Slice 2 helper, golden fixture comparison and Bash-reference comparison pass before the helper is listed as an authoritative Python gate.
- **SC-003**: A helper promotion record identifies every XPLAT-005 helper as Python-promoted, Bash-reference-only, or out of scope, with no ambiguous status entries.
- **SC-004**: Verification evidence includes the local macOS source-checkout `runtime-info` runner smoke for the accepted read-only path and includes no installed-plugin or native-matrix support claim.
- **SC-005**: Scope audit finds zero active Claude Code or Codex skill/hook/generated-payload/install/public-doc cutover edits and zero mutation-helper ports in XPLAT-005, excluding the bounded PR-review packet rendering remediation files explicitly allowed above.
- **SC-006**: The implementation remains reviewable as the accepted two-slice workflow or records a Plan/Tasks split decision before implementation begins.
- **SC-007**: Runner source manifest and checksum metadata validate after the helper runner files are added or modified, without copying metadata into generated payloads or claiming installed-cache proof.

## Assumptions

- XPLAT-004's Python 3.11+ standard-library runner foundation is present and remains the execution substrate for new helper ports.
- Existing Bash helpers remain available in the source checkout as temporary reference implementations during XPLAT-005.
- Fixture parity is sufficient for Windows-style path and no-Bash behavior in XPLAT-005; full native installed-plugin UAT is deferred to XPLAT-007.
- The helper registry should be small and explicit, not a broad plugin framework.
- Source-checkout local macOS smoke evidence is acceptable for this phase because installed-cache launch proof belongs to XPLAT-007.
