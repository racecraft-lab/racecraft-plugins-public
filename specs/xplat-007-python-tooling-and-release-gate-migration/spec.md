# Feature Specification: Python Tooling and Release-Gate Migration

**Feature Branch**: `codex/xplat-007-python-tooling-and-release-gate-migration`

**Created**: 2026-07-04

**Status**: Draft

**Input**: User description: "Replace active repo-local Bash-backed tests, evals, payload builders, install-verification scripts, release checks, release-readiness gates, and helper tooling with Python 3.11+ standard-library commands before XPLAT-008 switches Claude/Codex surfaces or makes public cross-platform claims."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run Repo-Local Gates Through Python (Priority: P1)

Maintainers can run the active repo-local test and eval suite through Python 3.11+ standard-library commands and receive the same pass/fail meaning as the current active Bash gates.

**Why this priority**: This is the verification base for every later XPLAT-007 slice. Payload, release, and guard work should not become authoritative until the repo-local gates that validate them no longer depend on Bash, `jq`, Git Bash, WSL, or PowerShell helper scripts.

**Independent Test**: From a source checkout, run the migrated repo-local verification commands and confirm the top-level runner, Layer 1 structural checks, Layer 4 helper tests, AI-eval runners, tool-scoping checks, integration suites, and parity suites execute through Python-only active entrypoints with equivalent outcomes.

**Acceptance Scenarios**:

1. **Given** a source checkout with the current active repo-local verification suite, **When** a maintainer runs the documented migrated verification entrypoint, **Then** the active suite executes through Python 3.11+ standard-library commands and reports the expected pass/fail result without requiring Bash, `.sh` scripts, `jq`, Git Bash, WSL, or PowerShell helper scripts.
2. **Given** a migrated gate that still has a temporary Bash reference comparison, **When** the Python gate is evaluated for promotion, **Then** golden fixture and source-checkout comparison evidence proves equivalent exit status, stdout, stderr, and artifact behavior before the Python gate becomes authoritative.

---

### User Story 2 - Run Payload, Install, And Release Checks Through Python (Priority: P2)

Release maintainers can build test payloads, refresh local plugin fixtures, check marketplace/version sync, verify install completeness, and run release-readiness checks through Python commands without relying on Bash or `jq`.

**Why this priority**: XPLAT-008 needs Python-authoritative release gates before it can safely switch active Claude/Codex invocation paths, rebuild release payloads, run native installed-plugin UAT, or make public cross-platform claims.

**Independent Test**: Run the migrated payload, local refresh, marketplace/version sync, install-verification, and release-readiness commands against deterministic source-checkout fixtures and confirm they produce the expected results without shell-specific dependencies.

**Acceptance Scenarios**:

1. **Given** source-controlled test payload inputs, **When** a release maintainer runs the migrated payload builder, **Then** test payload evidence is regenerated through Python commands and no release payload selection or public cutover occurs.
2. **Given** local plugin fixture and install-verification inputs, **When** a release maintainer runs the migrated refresh and install checks, **Then** the checks verify expected plugin files, bundled-agent inventory, and version consistency without Bash or `jq`.
3. **Given** release-readiness inputs for marketplace/version sync and shipped-behavior validation, **When** the migrated release checks run, **Then** they block stale or inconsistent evidence using Python-only active command paths.

---

### User Story 3 - Review Active No-Shell Guardrails (Priority: P3)

Reviewers can inspect deterministic guard output that fails if active build, test, eval, payload, install-verification, repository-helper, or release-readiness gates still use Bash, `.sh`, `jq`, shell interpolation, or shell-only parsing.

**Why this priority**: Reviewers need an enforceable boundary that separates real active command paths from archive/provenance text, temporary parity evidence, vendored consumer helpers, GitHub dispatch glue, and XPLAT-008 cutover surfaces.

**Independent Test**: Introduce representative forbidden active-path references in guard fixtures and confirm the guard fails with specific file/category findings; confirm historical/archive and allowed dispatch examples do not fail.

**Acceptance Scenarios**:

1. **Given** an active repo-local gate that invokes Bash, a `.sh` helper, `jq`, shell interpolation, or shell-only parsing, **When** the active-path guard runs, **Then** it fails with the path, category, and reason that must be remediated before release-readiness can pass.
2. **Given** archive/provenance text, temporary inactive parity evidence, GitHub Spec Kit generated consumer helpers, or GitHub CI/CD dispatch glue that only invokes Python gates, **When** the active-path guard runs, **Then** those references are classified without weakening enforcement for active repo-local gates.

### Edge Cases

- Remaining GitHub workflow shell snippets are allowed only when they dispatch directly to Python gates and contain no validation, packaging, install, release, or runtime logic.
- Historical/archive files may mention Bash, `.sh`, `jq`, or Unix paths when they are not used by active repo-local gates and are not release-readiness evidence.
- GitHub Spec Kit's generated `.specify/scripts/bash/` helpers in consumer repositories are explicitly outside the XPLAT-007 migration scope.
- Temporary Bash-reference comparisons may exist only as migration evidence until each gate is promoted; after promotion they must leave active release gates or be reclassified as inactive historical/parity evidence.
- Windows-style paths, spaces in paths, line-ending differences, missing prerequisites, stale generated files, and local macOS source-checkout smoke must produce deterministic results.
- Any accidental active Claude/Codex invocation cutover, generated release payload cutover, public docs/release-note update, native installed-plugin UAT, update path, autoheal path, or public support claim is out of scope and must be deferred to XPLAT-008.

## Clarifications

### Session 1: Active Gate Inventory And Ownership

- **Test Inventory Rule**: Classify active runner scripts as gates, including
  `tests/speckit-pro/run-all.sh`, `check-toolchain.sh`, runner-invoked Layer
  1/4/5 scripts, and opt-in Layer 2/3/6/7/8 runner scripts. Classify
  `fixtures/**`, eval JSON, expected-output files, and test docs as temporary
  parity fixtures or inactive evidence unless a runner directly executes them.
- **Payload/Release Inventory Rule**: Classify
  `scripts/build-plugin-payloads.sh`, `scripts/sync-marketplace-versions.sh`,
  and `scripts/refresh-local-plugin.sh` as active payload/release/helper
  commands for XPLAT-007. Release payload selection or cutover remains
  XPLAT-008; XPLAT-007 may rebuild test payload evidence only.
- **Helper Surface Inventory Rule**: Classify direct executable helpers under
  `speckit-pro/skills/**/scripts/**`, `speckit-pro/codex-skills/**/scripts/**`,
  and `speckit-pro/scripts/**` as active helper commands when reachable from a
  skill, test, runner, workflow, or registry. Classify `lib/*.sh` as active
  helper dependencies when imported by active helpers. Classify
  `bash-reference-manifest.json` and request fixtures as temporary parity
  evidence unless promoted into an active gate.
- **CI Workflow Inventory Rule**: Classify `.github/workflows/pr-checks.yml`
  and `.github/workflows/release.yml` jobs as active release-readiness or
  release gates when they validate, test, package, verify versions, or check
  artifact drift. Allowlist workflow shell only when it dispatches directly to
  Python gates and contains no validation, packaging, install, release, or
  runtime logic. Treat docs deploy validation as out of plugin release-gate
  scope except for dispatch allowlist review.
- **Inactive/XPLAT-008 Boundary Rule**: Classify generated payload mirrors,
  public docs, archive/history, and installed Claude/Codex invocation surfaces,
  but do not port or rewrite them unless they are active repo-local gate
  evidence. Record them as XPLAT-008 cutover surfaces or inactive historical
  evidence.

### Session 2: Command Taxonomy And Promotion Rules

- **Runner Operation Rule**: Make active release and gate surfaces
  `python -m speckit_pro_runner` operations wherever practical, including the
  suite runner, toolchain preflight, Layer 1/4/5/7/8 gates, Layer 2/3 eval
  dispatch, payload test build, local fixture refresh, marketplace/version sync,
  install verification, release-readiness, and active-path guard. Standalone
  Python commands are allowed only for unit/eval test harnesses or a narrowly
  justified ergonomic wrapper that reuses the same implementation and is not
  the authoritative release contract.
- **Runner Stream And Exit Contract**: Promoted runner operations preserve the
  existing runner envelope: one JSON response on stdout, line-delimited JSON
  diagnostics on stderr, and status-based exits `ok=0`,
  `expected_failure=1`, `input_error=2`, `missing_prerequisite=3`,
  `subprocess_failure=4`, and `internal_failure=5`. During parity, compare
  legacy exit status/stdout/stderr exactly unless a fixture declares semantic
  JSON stdout comparison; after promotion, legacy process output belongs in
  structured response data rather than mixed process streams.
- **Promotion Record Rule**: Each promoted gate needs a promotion record naming
  the prior Bash gate, Python operation, request fixture, failure classes,
  path/artifact coverage, comparison mode, exact or semantic stdout/stderr rule,
  exit-code result, artifact hash/diff result, rollback path, and Bash-reference
  retirement classification. Promotion is complete only when the active-path
  guard proves no active gate still invokes the Bash reference.
- **Mutable Command Mode Rule**: Payload, install, and release helper operations
  use explicit `read_only`, `dry_run`, and `apply` modes. In XPLAT-007, `apply`
  may write only source-checkout test evidence, temporary fixtures, or
  explicitly scoped repo-local verification metadata. It must not select,
  publish, or cut over generated release payloads.
- **Bash Retirement Rule**: Remove Bash-reference manifests and `.sh` files from
  active release gates and active runner/workflow paths after promotion. Keep
  them only as inactive historical or parity evidence when provenance requires
  it, with active-path guard allowlist classification. Thin Bash wrappers are
  not allowed as active transition entrypoints.

### Session 3: No-Shell Guard And Legacy Cleanup

- **Guard Scope Rule**: The active-path guard discovers shell-specific evidence
  across tracked text and classifies findings, but fails only for active
  repo-local gate or release paths. Blocking scope includes
  `tests/speckit-pro/**` runner-invoked gates, `scripts/*` release helpers,
  reachable `speckit-pro/**/scripts/**`, and plugin release/test workflows.
- **Forbidden Pattern Rule**: Blocking findings in active paths include
  Bash/shebangs, `.sh` executable calls, `jq` command use, Git Bash, WSL,
  PowerShell helper dependency, shell-only parsing such as `grep`/`sed`/`awk`
  pipelines, command substitution, `shell=True`, `os.system`, and command-string
  subprocess calls.
- **False Positive Rule**: Prose, archived code blocks, fixture text, GitHub
  `${{ }}` expressions, and non-executed classification examples are not
  blocking unless they are reachable from an active XPLAT-007 gate.
- **CI Dispatch Allowlist Rule**: Workflow shell is allowed only as dispatch
  glue when a `run:` step directly invokes `python -m speckit_pro_runner` or
  non-plugin docs tooling. Workflow shell must not contain plugin validation,
  packaging, install, release, `jq`, loop, or parsing logic. Existing plugin
  `pr-checks.yml` and `release.yml` Bash/`jq` logic remains blocking until
  migrated.
- **Nonblocking Classification Rule**: Classify archive/provenance text,
  vendored Spec Kit consumer helpers, parity fixtures, generated payload
  mirrors, and XPLAT-008 cutover surfaces as `archive_provenance`,
  `consumer_spec_kit_helper`, `temporary_parity_evidence`,
  `xplat_008_cutover_surface`, or `docs_out_of_scope` unless reachable from an
  active gate. Do not rewrite `.specify/memory/**`, `.specify/scripts/bash/**`,
  generated payload mirrors, or parity fixtures solely to remove Bash wording.
- **Guard Output Contract**: The guard is a `python -m speckit_pro_runner`
  JSON-envelope operation. Blocking findings emit `status: "expected_failure"`,
  exit `1`, and `data.blocking_count` plus `data.findings[]` entries with
  `path`, `line`, `category`, `pattern`, `reason`, `active_role`,
  `classification`, and `remediation`. Stderr emits line-delimited diagnostics
  with the same finding codes. A clean run emits `status: "ok"`, exit `0`, and
  classified nonblocking counts.

### Session 4: Payload, Install, Release, And Platform Proof

- **Test Payload Evidence Rule**: Rebuild isolated Claude and Codex test
  payload evidence only, using fixture or temporary output roots plus file-tree
  and fingerprint assertions. XPLAT-007 must not select, publish, or cut over
  generated release payloads.
- **Local Refresh And Install Verification Rule**: Test local plugin refresh and
  install verification through runner operations in `read_only` or `dry_run`
  mode against fixture roots and stubbed Claude/Codex CLIs. Verify command
  plans, marketplace-source validation, version consistency, bundled-agent
  inventory, and fake-home doctor checks. Do not mutate real HOME directories
  or real installed plugin caches.
- **Release-Readiness Migration Rule**: Move plugin release gates to
  `python -m speckit_pro_runner`, including changed-plugin detection, suite
  dispatch/result aggregation, PR-title and workflow-contract validation,
  payload evidence checks, marketplace/version sync, release-PR payload-sync
  parsing, and post-release drift checks. Leave docs-site Node/pnpm validation
  as docs tooling, with workflow shell only as direct dispatch glue.
- **Maintainer Documentation Boundary Rule**: Update only active
  maintainer-facing repo-local instructions required to run XPLAT-007 gates,
  such as `CLAUDE.md`, `docs-site/src/content/docs/contribute-and-release.md`,
  generated reference pages when source-driven, and XPLAT-007 `quickstart.md`.
  Do not update public install/runtime docs, release notes, update/rollback
  docs, or platform support claims except to avoid broken maintainer commands.
- **Platform Proof Rule**: XPLAT-007 requires source-checkout proof only: local
  macOS smoke plus deterministic Windows-style path fixtures covering
  backslashes, spaces, traversal rejection, fake-home install roots, and
  line-ending/path normalization. Installed-cache launch proof, native
  Windows/macOS/Linux installed-plugin UAT, update, autoheal, and public platform
  claims remain XPLAT-008 responsibilities.
- **Legacy Fixture Supersession Rule**: Older XPLAT-004 fixture prose that says
  installed-cache launch proof, native UAT, release-readiness, or public claim
  audit remain XPLAT-007 scope is superseded by the post-PR #280 roadmap split
  and this XPLAT-007 clarification. Update or annotate that fixture if touched
  by XPLAT-007 gate work; do not treat the older wording as an active
  requirement.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The migration MUST classify the active repo-local gate inventory across `tests/speckit-pro/**`, payload/release helper scripts, `speckit-pro/skills/**/scripts/**`, `speckit-pro/codex-skills/**/scripts/**`, `speckit-pro/scripts/**`, and `.github/workflows/**` before promoting replacements.
- **FR-002**: Active plugin build, test, eval, payload, install-verification, repository-helper, and release-readiness commands MUST have Python 3.11+ standard-library entrypoints.
- **FR-003**: The top-level repo-local test runner and active Layer 1, Layer 4, AI-eval, tool-scoping, integration, and parity gates MUST preserve the current pass/fail meaning after migration.
- **FR-004**: Migrated repo-local gates MUST use `python -m speckit_pro_runner` operations where practical, and any standalone Python command MUST have a planning justification.
- **FR-005**: Each migrated gate MUST have golden fixtures and source-checkout Bash-reference comparison evidence before being promoted as Python-authoritative.
- **FR-006**: Each promoted gate MUST record promotion evidence that names the prior active gate, Python replacement, fixture coverage, comparison result, and whether any Bash reference remains only as inactive historical/parity evidence.
- **FR-007**: Payload building, local plugin fixture refresh, marketplace/version sync, install verification, release checks, and release-readiness checks MUST run through Python commands without Bash or `jq`.
- **FR-008**: XPLAT-007 MUST rebuild test payloads only as migration evidence and MUST NOT select, rebuild, publish, or cut over generated release payloads.
- **FR-009**: A deterministic active-path guard MUST fail when active repo-local build, test, eval, payload, install-verification, repository-helper, or release-readiness paths require Bash, `.sh`, `jq`, Git Bash, WSL, PowerShell helper scripts, shell interpolation, or shell-only parsing.
- **FR-010**: The active-path guard MUST distinguish active repo-local command paths from archive/provenance text, inactive parity fixtures, GitHub Spec Kit generated consumer helpers, XPLAT-008 cutover surfaces, and GitHub CI/CD dispatch glue.
- **FR-011**: Any remaining CI shell mechanics MUST be allowlisted only when they dispatch to Python gates and contain no validation, packaging, install, release, or runtime logic.
- **FR-012**: Active maintainer-facing repo-local run instructions that are required to execute XPLAT-007 gates MUST point to the Python commands; public install docs, release notes, and public platform claims remain XPLAT-008 work.
- **FR-013**: Platform proof MUST stay limited to source-checkout fixtures, Windows-style path fixtures, and local macOS smoke, without claiming native installed-plugin UAT.
- **FR-014**: The migration MUST preserve XPLAT-004 runner contracts, XPLAT-005 read-only helper records, and XPLAT-006 mutation/install/PR-emission contracts while replacing only the active repo-local gates that validate or publish shipped behavior.
- **FR-015**: Migrated commands MUST provide deterministic exit codes, stdout/stderr behavior, artifact outputs, path handling, and missing-prerequisite diagnostics suitable for release-readiness review.
- **FR-016**: Install-verification checks MUST use the XPLAT-006 expected bundled-agent and generated-payload inventory boundaries without performing installed-cache native UAT.
- **FR-017**: Thin local Bash wrappers MUST NOT remain as active transition entrypoints for migrated repo-local gates.
- **FR-018**: The PR review packet MUST map major requirements and success criteria to changed files, parity or promotion evidence, guard evidence, known gaps, rollback notes, and explicit XPLAT-008 handoff items.

### Reviewability Notes *(if applicable)*

- The setup reviewability gate warned because XPLAT-007 spans `harness/adapter` and `docs/process`; the warning is accepted for one workflow with three internal slices.
- Typed reviewability exceptions are not planned. If planning proves the scope exceeds the reviewability budget, split before implementation rather than relying on a broad exception.

### Reviewability Budget *(mandatory)*

- **Primary surface**: `harness/adapter`
- **Secondary surfaces, if any**: `docs/process`
- **Projected reviewable LOC**: 250 from setup gate estimate; reassess during planning because the roadmap allows 400-800 for the implementation lane
- **Projected production files**: 4 from setup gate estimate; reassess during planning against the roadmap's 6-8 implementation expectation
- **Projected total files**: 10 from setup gate estimate; reassess during planning against the roadmap's 12-25 implementation expectation
- **Budget result**: warning accepted
- **Split decision**: Keep one XPLAT-007 spec with three independently reviewable slices: test/eval runner gates first, payload/install/release helpers second, and active-path guardrails/cleanup third. Split into follow-up specs only if Specify, Clarify, Plan, or Tasks proves these slices cannot stay reviewable.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.
- XPLAT-007 PR evidence MUST include per-gate promotion state, parity evidence, no-shell guard evidence, test payload evidence, and a clear XPLAT-008 handoff.

### Key Entities *(include if feature involves data)*

- **Active Gate**: A repo-local command path that validates, builds, tests, evaluates, packages test payloads, verifies installs, or checks release readiness for shipped plugin behavior.
- **Python Gate Entry Point**: The Python-only command surface that replaces an active gate and defines stable invocation, exit-code, output, and artifact behavior.
- **Parity Fixture**: Deterministic input and expected-output evidence used to compare the Python gate against the prior Bash behavior before promotion.
- **Promotion Record**: Review evidence that the Python gate is authoritative and that any Bash reference has been removed from active gates or preserved only as inactive historical/parity evidence.
- **Active-Path Guard Finding**: A deterministic guard result identifying a forbidden shell-specific dependency in active repo-local command paths.
- **Test Payload Evidence**: Source-checkout generated payload fixture output used to prove migration behavior without cutting over release payloads.
- **XPLAT-008 Handoff Item**: Explicit deferred work for active Claude/Codex invocation cutover, generated release payloads, install guidance, public docs, release notes, native installed-plugin UAT, update, autoheal, or public release readiness.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of active repo-local build, test, eval, payload, install-verification, repository-helper, and release-readiness gates in the classified XPLAT-007 inventory have Python 3.11+ standard-library entrypoints.
- **SC-002**: The migrated repo-local verification suite produces equivalent pass/fail results for the accepted golden fixtures before the Python gates are treated as authoritative.
- **SC-003**: The active-path no-shell/no-jq guard exits nonzero for every fixture that places Bash, `.sh`, `jq`, shell interpolation, or shell-only parsing in an active gate, and exits successfully for the final implementation's allowed scope.
- **SC-004**: 100% of promoted gates have promotion records that identify fixture coverage, comparison evidence, and Bash-reference retirement or inactive classification.
- **SC-005**: Test payload rebuild evidence exists, and zero generated release payload cutover, active payload selection, public install/runtime docs, platform-support claim docs, or release-note changes are included.
- **SC-006**: Source-checkout platform proof covers Windows-style paths and local macOS smoke without asserting native installed-plugin UAT.
- **SC-007**: The final PR packet maps every major requirement and success criterion to verification evidence and names all remaining XPLAT-008 release-gate responsibilities.

## Assumptions

- XPLAT-004, XPLAT-005, and XPLAT-006 outputs exist and are the source truth for runner contracts, helper records, install inventory boundaries, mutation-helper contracts, and fixture patterns.
- Python 3.11+ and a working `specify` command are official Spec Kit prerequisites; if unavailable, migrated gates fail with deterministic prerequisite diagnostics rather than falling back to Bash.
- The branch and feature directory already exist; this phase does not create a branch or run feature-creation scripts.
- Clarify may refine the exact file inventory, guard allowlist, and command taxonomy, but it must not expand scope into XPLAT-008 cutover work.
- Historical/archive provenance remains intact unless it is used by an active gate or release-readiness check.
- Generated release payload cutover, active Claude/Codex invocation changes, public install docs, release notes, update, autoheal, native installed-plugin UAT, and public support claims remain deferred to XPLAT-008.
