# Feature Specification: Repository Bash Confinement and CI Dispatch Guard

**Feature Branch**: `xplat-010-repository-bash-confinement`

**Created**: 2026-07-08

**Status**: Draft

**Input**: User description: "Confine repository-local Bash to GitHub CI/CD workflow dispatch glue only. XPLAT-009 removed Bash from the shipped plugin and its payloads, but the repository around it still runs on Bash: the test harness (~101 `.sh` files), top-level helper scripts, `.claude/hooks`, and one residual CI test-dispatch step. Port every active repo-local surface to Python 3.11+ standard library, prove zero check regressions per port, add a guard that fails any new Bash outside the workflow boundary, add container/runner preflight CI, make GitHub Releases readable by the public, and restore the deleted `estimate-spec-size` scoping estimator."

## Clarifications

### Session 2026-07-08 (Session 1 — suite manifest and count parity)

- Q: What is the per-layer/per-script field schema of `suite-manifest.json`, and what is the "expected-count source"? → A: JSON Schema 2020-12 contract. Top level `{schema_version, layers[]}`. Per layer: `{id, label, default (bool), execution ("execute"|"print-commands"), live_only (bool), integration (bool), counted_in_total (bool), dispatch ("python-module"|"internal-check"|"shell-legacy-transitional"), scripts[]}`. Per script: `{path (repo-relative), label, baseline (repo-relative pointer to the committed count-parity baseline file, or null)}`. The toolchain preflight is a layer with `counted_in_total: false`. The expected-count source is the **baseline pointer, not an inline integer** — the baseline file is the single count of record, eliminating manifest-vs-baseline drift. Composition changes are manifest-only edits; shipped-runner bytes change only when dispatch behavior changes.
- Q: What exactly must the dual-run diff in each port PR body contain? → A: A fixed block with six required items: (1) the exact bash capture command (`VERBOSE=true <script>`) and the port-run command; (2) the committed baseline path; (3) a unified diff of the ordered canonical check-name inventory, or the literal line "no differences — 1:1 preserved"; (4) the explicit count equality (`bash: N == python: N`); (5) an intentional-change statement (must be "none" for a clean port; any rename/drop flags the PR as a regression); (6) the count-ledger delta line appended to the running ledger.
- Q: At what granularity is "runtime count" measured for count parity (FR-010/FR-011/SC-003), and how must a ported unittest module's `{passed}/{total}` headline be computed? → A: Granularity is per individual assertion execution — every former `assert_*`/`_pass`/`_fail` call — not per former `set_test`; this covers both loop-generated repetitions and non-loop multi-assertion groupings within a single former `set_test`, not merely loop iterations. `{total}` MUST equal `(test methods not wrapped in a subTest loop/group) + (subTest units actually executed)`; bare `result.testsRun` MUST NOT stand in for `{total}` on any module with looping or grouped former assertions, since stdlib `subTest` execution never increments `testsRun` (only `addSubTest` fires per subTest). Ported modules MUST compute `{total}`/`{passed}` via a shared `unittest.TestResult` subclass overriding `addSubTest` (new shared utility under `tests/speckit-pro/lib/`). Five pre-existing modules print bare `result.testsRun` (`test-speckit-pro-read-only-helpers.py`, `test-speckit-pro-mutation-helpers.py`, `test-autopilot-phase-coverage.py`, `test-speckit-pro-runner.py`, `test-speckit-pro-gates.py`) and are exempt from retrofit: they were born pure-Python under XPLAT-005/006/007 (no bash predecessor) and are governed by the archived XPLAT-007 spec's FR-003, which required only pass/fail-meaning preservation, not numeric count parity — superseded precedent under an older contract, not a defect, and out of scope for a KISS/YAGNI-respecting rewrite. This exemption is retrospective and covers only those five: new ports and every other module MUST NOT copy the bare-`result.testsRun` pattern.
- Q: Does the shipped suite gate (`speckit-pro/speckit_pro_runner/gates/suite.py`) retire its native internal implementations of Layers 5/7/8 (`check_layer5`/`check_layer7`/`check_layer8`) when those layers are ported to manifest-named Python modules, or keep them behind a permanent equivalence test — and how is manifest/gate drift prevented? → A: Retire each native check at its own port-PR boundary (PR 5 for L5, PRs 7a/7b for L7, PR 8 for L8); no permanent equivalence shim is kept. The natives are not faithful baselines worth preserving: `check_layer5` is vacuously true (asserts on a `tools:` field none of the checked agents use), `check_layer7` validates an orphaned fixture directory no real Layer-7 runner reads, and `check_layer8` covers only 3 of the 6 files the real validator requires. Drift is prevented going forward by FR-007's fail-closed manifest-derived roster plus a deterministic drift-guard test asserting the gate's advertised roster and dispatch kinds match the manifest exactly; per-layer dispatch-kind assignment (`internal-check` vs. `python-module`) is deferred to the Plan phase.
- Q: What is the exact format of the committed count-parity baseline file (`tests/speckit-pro/parity/xplat-010/<script>-baseline.txt`), and how are bash `set_test` names reconciled 1:1 with the Python port's check names? → A: Format is frozen: one line per executed `_pass`/`_fail` call in execution order (`NNN <canonical-name>`; grouped checks legitimately repeat the same name on consecutive lines — up to 11 observed), then a trailing `TOTAL: <N>` line where `N = PASS_COUNT + FAIL_COUNT`. Names are captured VERBATIM from runtime `VERBOSE=true` PASS/FAIL output (parsed only from lines matching `^\s*(.+?)\s\.\.\.\s(PASS|FAIL)$`), never reconstructed from source literals. A full census of all 14 active Layer-4 scripts and 7 Layer-1 validators found zero un-named `_pass`/`_fail` executions, so no positional `check-NNN` fallback naming is needed. Reconciliation with the Python port uses `unittest`'s `subTest` message parameter to reproduce each bash check name 1:1 (shipped precedent: `test-speckit-pro-read-only-helpers.py`, the XPLAT-005 port). Five normalization rules govern capture: (1) one line per outcome, names may repeat; (2) capture environment is pinned and recorded (non-root, matching CI); (3) one baseline file per (script, invocation-mode) pair for dual-mode scripts; (4) regeneration triggers include enumerated data files the script reads, not just script source; (5) never grep `assert_`-prefixed text for inventories — capture is always dynamic execution.

## User Scenarios & Testing *(mandatory)*

<!--
  User stories carry the workflow prompt's US1–US7 identifiers so traceability
  is 1:1. They are prioritized as independently testable slices; delivering any
  single one leaves a viable increment of value.
-->

### User Story 1 - Cross-Platform Python Suite Orchestrator (US1) (Priority: P1)

As a plugin maintainer, I can run the full deterministic test suite through a Python orchestrator that behaves exactly like the previous Bash runner — same flags, same headline output, same exit codes — on any operating system that has Python 3.11+, without needing Bash or `jq`.

**Why this priority**: This is the foundation the entire confinement effort rests on. Until the suite runs from Python, no port can be validated cross-platform and contributors on native Windows cannot run the repo's own gates. It delivers standalone value even before the rest of the stack lands.

**Independent Test**: On a machine with only Python 3.11+ (no Bash, no `jq`), run the orchestrator with `--all`, a single `--layer N`, and the toolchain preflight; confirm the `X/Y passed` headline, layer selection, and exit codes match the recorded Bash-runner behavior.

**Acceptance Scenarios**:

1. **Given** a machine with Python 3.11+ and no Bash available, **When** the maintainer runs the orchestrator with `--all`, **Then** every deterministic layer executes and the run ends with the same `X/Y passed` headline and exit code the Bash runner produced.
2. **Given** the orchestrator, **When** the maintainer passes `--layer N`, `--live`, or the toolchain preflight flag, **Then** each flag selects the same scope the Bash runner selected for that flag.
3. **Given** the shipped runner's suite gate, **When** it resolves which layers exist, **Then** it reads the repo-side suite manifest rather than parsing any Bash runner script, and its existing envelope contract is unchanged.

---

### User Story 2 - Runtime Count-Parity Proof Per Port (US2) (Priority: P2)

As a reviewer, every port PR shows me a runtime count-parity diff against a committed baseline that proves check names and check counts are preserved 1:1 — so I can trust that porting a layer from Bash to Python lost no coverage.

**Why this priority**: Trust in the migration depends on provable non-regression. Without name-and-count parity a dropped check can hide behind a gained one. This makes each port reviewable in isolation.

**Independent Test**: Take one ported layer, run the committed baseline capture and the new Python module, and confirm the recorded dual-run diff shows an identical ordered check-name inventory and identical runtime count.

**Acceptance Scenarios**:

1. **Given** a port PR, **When** the reviewer reads the PR body, **Then** it contains a dual-run diff comparing the committed baseline (ordered check-name inventory plus runtime count) against the ported module, showing 1:1 preservation.
2. **Given** a port that silently renames or drops a check, **When** the parity comparison runs, **Then** the diff is non-empty and the PR is flagged as a regression rather than passing on an unchanged total count.
3. **Given** the full stack of port PRs, **When** the final parity artifact is produced, **Then** a running count ledger and a suite-parity result record cumulative name-and-count preservation across every ported layer.

---

### User Story 3 - Repository Bash Confinement Guard (US3) (Priority: P1)

As CI, I fail any PR that introduces a `.sh` file, a Bash-shebang executable, or an active `bash`/`jq` invocation anywhere outside `.github/workflows/`, with a fail-closed allowlist that covers only the vendored upstream `.specify/**` helper files.

**Why this priority**: This is the headline policy of the whole spec. It is the mechanism that makes "repository Bash confined to CI dispatch glue" enforceable and durable rather than a one-time cleanup that erodes over time.

**Independent Test**: Feed the guard three trees — one clean, one with a stray new `.sh` outside the workflow boundary, and one with a non-allowlisted Bash file under `.specify/**` — and confirm it passes the first and fails the other two.

**Acceptance Scenarios**:

1. **Given** a PR that adds a new `.sh` file or an active `bash`/`jq` invocation outside `.github/workflows/`, **When** the confinement guard runs, **Then** the guard fails and the PR is blocked.
2. **Given** the vendored upstream `.specify/**` helpers, **When** the guard runs, **Then** each of the allowlisted files is accepted, marked release-readiness-excluded, and any Bash file appearing under `.specify/**` that is not on the allowlist causes a fail-closed failure.
3. **Given** the release-readiness gate, **When** it evaluates the Bash-free claim, **Then** allowlisted vendored files are excluded from the evidence so they can never satisfy release readiness, and the guard is composed into both CI and the release-readiness gate.

---

### User Story 4 - Container and Runner Preflight CI (US4) (Priority: P3)

As a maintainer, Linux amd64/arm64 container preflight jobs and Windows x64/ARM64 direct-runner smoke jobs run when runner or gate paths change, Linux results gate merges and Windows results are advisory, and every job uploads an evidence artifact.

**Why this priority**: Preflight raises early confidence that the ported runner behaves across platforms, but it is advisory infrastructure that never substitutes for native operator UAT, so it ranks below the core port and guard.

**Independent Test**: Trigger the preflight workflow via manual dispatch and via a path-filtered change to a runner/gate path; confirm Linux jobs report as required checks, Windows jobs run continue-on-error, and each uploads an availability/smoke evidence artifact.

**Acceptance Scenarios**:

1. **Given** a pull request that changes a runner, gate, or workflow path, **When** CI runs, **Then** the container/runner preflight workflow triggers; a docs-only PR that touches none of those paths does not trigger it.
2. **Given** the preflight jobs, **When** they complete, **Then** the Linux amd64 and arm64 container jobs act as required (gating) checks and the Windows x64/ARM64 smoke jobs run continue-on-error and never block a merge.
3. **Given** a Windows runner label that is unavailable or in public preview, **When** the smoke job runs, **Then** its availability is recorded in the uploaded evidence artifact and no merge is blocked.

---

### User Story 5 - Public-Readable GitHub Release Highlights (US5) (Priority: P2)

As a plugin consumer or evaluator, each GitHub Release opens with plain-English Highlights composed from the release-note blocks that PR authors wrote for consumers, with the raw conventional-commit list preserved below as an appendix — so I can understand what a release actually changed.

**Why this priority**: This closes the deferred "public release notes" scope item and directly serves the marketplace audience, but it is independent of the Bash-confinement mechanics and can land on its own track.

**Independent Test**: Run the composer against a set of commits since a prior tag whose PR bodies contain Release note blocks; confirm the rewritten Release body opens with a plain-English Highlights section and retains the conventional-commit list as an appendix.

**Acceptance Scenarios**:

1. **Given** a set of feat/fix commits since the last release tag whose PR bodies carry Release note blocks, **When** the release is published, **Then** the GitHub Release body opens with a plain-English Highlights section composed from those blocks.
2. **Given** the same release, **When** a reader scrolls past the Highlights, **Then** the original conventional-commit list is preserved below as an appendix and CHANGELOG.md remains the machine-generated ledger.
3. **Given** the composer, **When** it runs inside the release process, **Then** it uses only deterministic standard-library logic with no LLM calls and no new secrets.

---

### User Story 6 - Release-Note Enforcement Check (US6) (Priority: P2)

As a PR author, a required check tells me when a feat/fix PR is missing its Release note block, and a `release-note/skip` label lets me exempt a change that has no consumer-visible effect.

**Why this priority**: Enforcement is what keeps US5 durable — an advisory-only convention decays and the composer degrades back to raw commit subjects within a few releases. It is a thin wrapper on US5, so it ranks just after it.

**Independent Test**: Open one feat PR without a Release note block (expect the check to fail), add the block (expect pass), and open another labeled `release-note/skip` (expect pass without a block).

**Acceptance Scenarios**:

1. **Given** a feat or fix PR with no Release note block in its body, **When** the release-note check runs, **Then** the check fails and reports the missing block.
2. **Given** a feat or fix PR that carries a Release note block, **When** the check runs, **Then** it passes.
3. **Given** a PR with no consumer-visible effect labeled `release-note/skip`, **When** the check runs, **Then** it passes without requiring a block.

---

### User Story 7 - Restored Spec-Size Estimator (US7) (Priority: P2)

As a maintainer scoping a future spec, the `estimate-spec-size` runner operation returns `{estimated_loc, suggested_slices, status}` from the size signals the grill-me and speckit-prd skills send it, restoring the scoping estimator whose Bash predecessor was deleted during XPLAT-009 without a Python port.

**Why this priority**: An operator directive requires remediating this defect inside this spec rather than deferring it. It is a self-contained fix independent of the confinement mechanics, so it can land early on its own track.

**Independent Test**: Send the estimator the size signals grill-me/speckit-prd emit and confirm the response is a populated `{estimated_loc, suggested_slices, status}` object.

**Acceptance Scenarios**:

1. **Given** the size signals the grill-me skill sends, **When** the `estimate-spec-size` operation is invoked, **Then** it returns a populated `{estimated_loc, suggested_slices, status}` result.
2. **Given** the size signals the speckit-prd skill sends, **When** the operation is invoked, **Then** it returns the same shaped result and the scoping estimator behaves as it did before XPLAT-009 deleted its Bash predecessor.

---

### Edge Cases

- A `.sh` file or Bash invocation that lives **inside** `.github/workflows/` is the sanctioned dispatch glue and MUST pass the guard.
- A Bash file that appears under `.specify/**` but is **not** on the fail-closed allowlist MUST fail the guard (fail-closed, not fail-open).
- A port that keeps the same total check count but swaps one check name for another MUST be caught by name-level parity, not masked by the unchanged total.
- A layer whose checks are generated in a loop MUST be measured by **runtime** count, not a static grep, so loop-generated checks are counted correctly.
- A feat/fix PR with genuinely no consumer-visible effect MUST be exemptible via `release-note/skip` rather than forced to invent a Release note.
- A release with no PR-authored Release note blocks since the last tag MUST still produce a well-formed Release body (Highlights degrade gracefully; the commit-list appendix is always present).
- A Windows ARM64 runner that is unavailable or in public preview MUST NOT block any merge; its unavailability is recorded as evidence.
- A ported `.claude/hooks` handler MUST preserve the stdin-JSON / exit-0-or-2 contract even for malformed input, matching its Bash predecessor's behavior.

## Requirements *(mandatory)*

### Functional Requirements

#### Confinement policy and guard

- **FR-001**: The repository MUST contain zero `.sh` files and zero Bash-shebang executables outside `.github/workflows/`, except for an explicit fail-closed allowlist of vendored upstream files.
- **FR-002**: A repository-Bash-confinement guard MUST fail any change that introduces a new `.sh` file, a new Bash-shebang executable, or an active `bash`/`jq` invocation outside `.github/workflows/`.
- **FR-003**: The guard MUST maintain a fail-closed allowlist covering exactly the 10 vendored `.specify/**` upstream Spec Kit helper files, each marked `release_readiness_excluded: true`, and MUST fail if any Bash file appears under `.specify/**` that is not on that allowlist.
- **FR-004**: Allowlisted vendored files MUST be excluded from release-readiness evidence so they can never satisfy the Bash-free release claim.
- **FR-005**: The guard MUST be composed into both the release-readiness gate and CI so the policy is enforced on every pull request.

#### Cross-platform suite orchestration

- **FR-006**: Maintainers MUST be able to run the full deterministic suite via a Python orchestrator that preserves the prior runner's flags (`--layer N`, `--live`, `--all`, toolchain preflight), the `X/Y passed` headline output, and exit codes, on any operating system with Python 3.11+ and without Bash or `jq`.
- **FR-007**: The suite composition MUST be defined by a single repo-side manifest that is the one source of truth per layer, which both the orchestrator and the shipped runner's suite gate read instead of parsing the former Bash runner. Post-PR-2, the shipped gate's advertised layer roster (`DEFAULT_SUITE`, `EXTENDED_SUITE`, `ALLOWED_LAYERS`) MUST be derived solely from the manifest, failing closed when the manifest is absent or unreadable; a deterministic drift-guard test MUST assert the gate's advertised roster and dispatch kinds match the manifest exactly.
- **FR-008**: The shipped runner's suite gate MUST continue to honor its existing envelope contract while sourcing layer composition from the manifest; any change to shipped-runner bytes MUST follow the payload/proof regeneration ritual. Each layer's native internal gate implementation (for example `check_layer5`, `check_layer7`, `check_layer8`) MUST be retired at the PR that ports the corresponding layer to a manifest-named Python module, so each layer has exactly one implementation of record, named by the manifest; a permanent equivalence shim between a retired native check and its ported replacement MUST NOT be kept.

#### Port fidelity and count parity

- **FR-009**: All active repo-local tooling — test-harness modules, `scripts/**` helpers, `.claude/hooks/**`, and the live-AI eval runners for Layers 2/3/6 — MUST be ported to Python 3.11+ standard library only, with no new runtime dependency.
- **FR-010**: Ported test modules MUST follow the house convention: `unittest`, a custom `__main__` printing `<label>: {passed}/{total} passed`, and one counted Python unit per former assertion execution — not per former `set_test`. The counted unit is every former `assert_*`/`_pass`/`_fail` execution: this covers both loop-generated repetitions and non-loop multi-assertion groupings, not merely loop iterations. Each former assertion execution MUST map to exactly one counted Python unit and count as 1 toward `total`; a non-loop former assertion may be its own test method or a `subTest` unit, while a loop-generated assertion execution MUST be a `subTest`.
- **FR-011**: Each port PR MUST demonstrate 1:1 preservation of check names and runtime counts against a committed baseline (ordered check-name inventory plus runtime count, with names captured verbatim from runtime PASS/FAIL output rather than reconstructed from source literals), with the dual-run diff recorded in the PR body.
- **FR-012**: Each port PR MUST land the port, the manifest update, and the corresponding `.sh` deletion together (same-PR swap) so no layer ever runs with zero coverage.
- **FR-013**: A running count ledger and a final suite-parity result MUST record cumulative name-and-count parity evidence across the PR stack.
- **FR-014**: Ported `.claude/hooks/**` handlers MUST preserve the stdin-JSON / exit-0-or-2 hook contract.
- **FR-015**: Ported live-AI eval runners (Layers 2/3/6) MUST preserve their CLI argument contracts and codex staging semantics.

#### Orphan-test disposition

- **FR-016**: The 34 orphaned Bash test scripts (32 Layer-4 tests of already-deleted scripts plus 2 wrappers) MUST be deleted rather than ported, with a committed disposition ledger recording the rationale for each file.

#### Container and runner preflight CI

- **FR-017**: A container/runner preflight workflow MUST run on path-filtered pull requests (runner, gate, and workflow paths) and on manual dispatch, and MUST NOT run on changes that cannot affect the runner (for example, docs-only PRs).
- **FR-018**: Linux amd64 and arm64 container preflight jobs MUST act as required (gating) checks on the paths that trigger them.
- **FR-019**: Windows x64 and ARM64 direct-runner smoke jobs MUST run as advisory (continue-on-error), never blocking merges, with runner availability recorded per label.
- **FR-020**: The preflight jobs MUST upload evidence artifacts, and their results MUST NOT be treated as native installed-plugin UAT evidence.

#### Public release notes

- **FR-021**: Each feat/fix PR MUST carry a consumer-facing Release note block in its body.
- **FR-022**: A required `validate-release-note` check MUST fail feat/fix PRs missing the Release note block, and a `release-note/skip` label MUST exempt changes with no consumer-visible effect.
- **FR-023**: At release publication, a deterministic Python standard-library composer MUST rewrite the GitHub Release body to open with plain-English Highlights composed from the PR-authored Release note blocks harvested for all commits since the last tag, preserving the conventional-commit list below as an appendix.
- **FR-024**: The release-notes composer MUST make no LLM calls and require no new secrets; CHANGELOG.md MUST remain the machine-generated ledger.

#### Spec-size estimator restoration

- **FR-025**: The runner MUST provide an `estimate-spec-size` operation that returns `{estimated_loc, suggested_slices, status}` computed from the size signals the grill-me and speckit-prd skills send it.

### Reviewability Notes *(if applicable)*

- This spec is a large refactor + infrastructure port. Its review surface is
  intentionally delivered as a typed-split PR stack; the split is an
  operator-ratified transition exception recorded in the workflow file
  (`docs/ai/specs/.process/XPLAT-010-workflow.md`) and in the design concept
  (Q9), not an ad-hoc override.
- Accepted reviewability-exception classes are refactor, infra, and upgrade.
  Generated templates, generated zones, `.process` evidence files, PR bodies,
  and code fences are not valid provenance for the exception; the workflow file
  is.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter (test-harness and runner-tooling port)
- **Secondary surfaces, if any**: scheduler/runtime (CI workflows), seed/config (suite manifest, guard allowlist, release-note metadata), docs/process (disposition, parity, and count ledgers)
- **Projected reviewable LOC**: 400–800 (roadmap budget; reviewability-gate setup returned a ~400-LOC warn), excluding declared generated/lock/vendor artifacts
- **Projected production files**: ~6–25 (setup estimate ~6; roadmap budget 15–25)
- **Projected total files**: ~15–25
- **Budget result**: transition exception (reviewability-gate warn accepted; typed split ratified)
- **Split decision**: Remains one spec, delivered as a dependency-ordered ~13-PR stack — (1) orphan-test deletion + ledger; (2) suite manifest + `run-all.py` + manifest-reading suite gate; (3a/3b) mechanical Layer-1 validators; (4) MOC lints + codex validators; (5) Layer-5 + toolchain + `pr-checks.yml` dispatch swap; (6) `scripts/**` + `.claude/hooks/**` ports; (7a/7b) Layer-7 replay harness; (8) Layer-8 parity; (9) live-eval runners; (10) confinement guard + final Bash deletion; (11) container-preflight CI; (12) release-notes composer + `validate-release-note` check + release step; plus the `estimate-spec-size` restoration as its own early fix PR. Ordering: PR 1 anytime; PR 2 before 3–10; PR 10 after 3–9; PR 11 last among confinement PRs; PR 12 and the estimator fix independent. Each PR is independently CI-green and within the 400–800 reviewable-LOC budget.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence. For every port PR this includes the
  committed count-parity baseline and the recorded dual-run diff.
- The count-parity dual-run diff block MUST contain (Clarifications Session 1):
  (1) the exact bash capture command (`VERBOSE=true <script>`) and the port-run
  command; (2) the committed baseline path; (3) a unified diff of the ordered
  canonical check-name inventory, or the literal line "no differences — 1:1
  preserved"; (4) the explicit count equality (`bash: N == python: N`);
  (5) an intentional-change statement ("none" for a clean port — any rename or
  drop flags the PR as a regression); (6) the count-ledger delta line appended
  to the running ledger.
- Each feat/fix PR in the stack MUST additionally carry a consumer-facing
  Release note block (FR-021), and deferred work MUST name the follow-up spec
  or issue.

### Key Entities *(include if feature involves data)*

- **Suite Manifest**: The single per-layer source of truth for suite composition, read by both the Python orchestrator and the shipped runner's suite gate; replaces regex-parsing of the former Bash runner. Fields (per Clarifications Session 1): top-level `{schema_version, layers[]}`; per layer `{id, label, default, execution, live_only, integration, counted_in_total, dispatch, scripts[]}`; per script `{path, label, baseline}` where `baseline` points at the committed count-parity baseline file (the single count of record — no inline expected-count integers). Toolchain preflight carries `counted_in_total: false`.
- **Confinement Guard Allowlist**: The fail-closed list of the 10 vendored `.specify/**` upstream files, each flagged `release_readiness_excluded: true`.
- **Count-Parity Baseline**: A committed per-script capture at the fixed path `tests/speckit-pro/parity/xplat-010/<script>-baseline.txt` recording the ordered check-name inventory and runtime count used to prove 1:1 preservation on each port. Runtime count (per Clarifications Session 1) is measured per assertion execution — every former `assert_*`/`_pass`/`_fail` call, covering both non-loop multi-assertion grouping and loops — not per former `set_test`. Frozen format: one line per executed `_pass`/`_fail` call in execution order, `NNN <canonical-name>` (grouped checks legitimately repeat the same name on consecutive lines — up to 11 observed in this repo), then a trailing `TOTAL: <N>` line where `N = PASS_COUNT + FAIL_COUNT`. Check names are captured VERBATIM from runtime `VERBOSE=true` PASS/FAIL output — never reconstructed from source literals, since loop- and data-driven names only exist at runtime — via a capture filter that parses only lines matching `^\s*(.+?)\s\.\.\.\s(PASS|FAIL)$` and discards all other subprocess stdout (interleaving is possible mid-line). The capture environment is pinned and recorded (non-root, matching CI — a root-vs-non-root capture of `test-moc-lint-exit-codes.sh` diverges 31 vs. 36 assertions). A script with more than one invocation mode (e.g., `validate-moc-orphan.sh`'s optional scan-root argument, which changes assertion count from 29 to 0) gets one committed baseline file per (script, invocation-mode) pair rather than a single shared file. Regeneration triggers include not only script-source changes but also changes to any data file the script enumerates at runtime (e.g., `validate-curated-set.sh` check names are driven by live `scripts/curated-set.json` content). Capture tooling SHOULD fail loudly on any PASS/FAIL line with an empty or stale name rather than silently falling back to a positional `check-NNN` placeholder (recommended safeguard; the census found zero un-named executions, so a positional-fallback feature itself is not warranted).
- **Count Ledger / Suite-Parity Result**: The running and final cumulative parity evidence across the PR stack.
- **Disposition Ledger**: The committed record of the 34 deleted orphan Bash tests and the rationale for deleting rather than porting each.
- **Release Note Block**: The consumer-facing block each feat/fix PR carries in its body, harvested by the composer at release time.
- **Container-Preflight Evidence Artifact**: The per-platform availability and smoke-result artifact uploaded by the preflight jobs.
- **Spec-Size Estimate**: The `{estimated_loc, suggested_slices, status}` result the restored `estimate-spec-size` operation returns.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A repository-wide scan excluding `.github/workflows/` finds zero `.sh` files and zero Bash-shebang executables outside the documented allowlist.
- **SC-002**: The full deterministic suite runs to completion on Linux, macOS, and native Windows with only Python 3.11+ present (no Bash, no `jq`).
- **SC-003**: Zero checks are lost or silently renamed across the port stack — every port PR shows a name-and-count parity diff proving 1:1 preservation against its committed baseline.
- **SC-004**: A PR that introduces a new Bash script or an active `bash`/`jq` invocation outside the workflow boundary is blocked by CI 100% of the time.
- **SC-005**: Each published GitHub Release opens with a plain-English Highlights section understandable by someone who has never seen the repository, with the conventional-commit list retained as an appendix.
- **SC-006**: 100% of feat/fix PRs either carry a Release note block or are explicitly labeled `release-note/skip` before merge.
- **SC-007**: The `estimate-spec-size` operation returns a populated `{estimated_loc, suggested_slices, status}` for the size signals grill-me and speckit-prd send, restoring pre-XPLAT-009 scoping behavior.
- **SC-008**: Linux container preflight results gate the paths they cover, while Windows smoke results are recorded as advisory evidence and never block an unrelated merge.

## Assumptions

- Python 3.11+ is available in CI and on maintainer machines (already required by the existing runner), so it is the only runtime the ported tooling may depend on.
- `.github/workflows/**` remains the single sanctioned home for Bash dispatch glue, per the cross-platform roadmap policy.
- The 10 vendored `.specify/**` upstream Spec Kit helper files are stable and are not modified or forked by this spec; they are documented-and-guarded, not ported.
- The test suite continues to live at the repository root (`tests/speckit-pro/`), a sibling of the plugin, because plugin install copies the whole plugin directory; this spec does not relocate it.
- GitHub API access is available at release time so the composer can harvest PR bodies for commits since the last tag; when no Release note blocks are found, the Highlights section degrades gracefully and the commit-list appendix is always present.
- Windows runner availability (especially ARM64/`windows-11-arm`) may vary; the advisory, continue-on-error framing accommodates unavailable or public-preview states.
- XPLAT-009 already completed plugin-source and generated-payload Bash removal; XPLAT-008 native operator UAT remains the release-claim gate, and this spec's container/runner preflight is preflight-only evidence that never substitutes for it.
- The `estimate-spec-size` restoration matches the input/output contract the grill-me and speckit-prd skills already expect, since those skills are the callers that lost the estimator when its Bash predecessor was deleted.
