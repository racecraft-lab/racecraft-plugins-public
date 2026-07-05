# Tasks: Claude/Codex Cutover and Universal Install Release Gate

**Input**: `docs/ai/specs/.process/XPLAT-008-design-concept.md`, `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and `checklists/`

**Feature dir**: `specs/xplat-008-claude-codex-cutover-universal-install-release-gate`

**Non-goals preserved**: no child specs during setup, no installed-runtime shell wrapper transition path, no repo-wide historical shell-word purge, no future-facing public claims before evidence, no smoke-only UAT for native platform support, no broad reinstall or wipe-copy repair behavior, and no manual plugin version edits outside the established release mechanism.

**Task format**: `- [ ] T### [P] [Slice] [US#, FR-###] Task`. `[P]` means the task has independent file ownership and can run in parallel after its dependencies are met.

**Slice dependencies**: Slice 1 before Slice 2 before Slice 3. Within each slice, fixtures/tests and deterministic verification precede active runtime, payload, docs, release, UAT, update, or repair changes.

## Phase 1: Slice 1 - Active Installed-Runtime Surface Cutover

**Goal**: Installed Claude and Codex runtime surfaces resolve Python `>=3.11` and invoke `[resolved_python, "-m", "speckit_pro_runner"]` without Bash, Git Bash, WSL, PowerShell-specific command language, shell parsing, shell redirection, Unix-only path assumptions, or `jq`.

- [x] T001 [S1] [US1, FR-001, FR-005] Create `specs/xplat-008-claude-codex-cutover-universal-install-release-gate/.process/active-runtime-inventory.md` classifying Claude/Codex skills, agents, hooks, install guidance, generated payload paths, release gates, archive/provenance text, CI dispatch glue, upstream helpers, tests/fixtures, and docs prose by active installed-runtime scope.
- [x] T002 [P] [S1] [US1, FR-002, FR-003] Add runner invocation request/case fixtures under `tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/` covering Windows `py -V:3`, `py -3`, `python`, `python3`; macOS/Linux `python3`, `python`; Python `>=3.11` acceptance; failure diagnostics; and argv-only `-m speckit_pro_runner` invocation.
- [x] T003 [P] [S1] [US1, FR-003, FR-004, FR-005] Add active-runtime no-shell/no-jq guard fixtures under `tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/` that fail prohibited active-surface shell behavior and allow archive/provenance, tests/fixtures, minimal Python-only CI dispatch glue, and upstream `.specify/scripts/bash/` helpers.
- [x] T004 [S1] [US1, FR-002, FR-003] Extend `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py` to assert runner invocation records include attempted candidates, resolved executable or failure, version, platform/cache context, stdin JSON, stdout JSON, stderr diagnostics, and no shell fallback.
- [x] T005 [S1] [US1, FR-003, FR-004, FR-005] Extend `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py` to assert the active-path guard blocks prohibited active runtime terms while preserving the explicit exception classes.
- [x] T006 [S1] [US1, FR-002, FR-003, FR-015] Implement installed-cache interpreter discovery and argv-style runner invocation in `speckit-pro/speckit_pro_runner/helpers/install.py`, returning structured diagnostics before meaningful workflow execution continues.
- [x] T007 [S1] [US1, FR-001, FR-003, FR-004, FR-005] Update `speckit-pro/speckit_pro_runner/gates/active_path_guard.py` to use the active-runtime inventory categories and fail active source paths, generated payloads, install guidance, and release gates when prohibited shell-only behavior returns.
- [x] T008 [S1] [US1, FR-002, FR-003, FR-022] Register the XPLAT-008 runner invocation and active guard operations in `speckit-pro/speckit_pro_runner/gates/registry.py` and refresh runner manifest/checksum metadata.
- [x] T009 [S1] [US1, FR-002, FR-003, FR-022] Update Claude active skill surfaces in `speckit-pro/skills/` so scaffold, status, autopilot, install, and related installed-runtime guidance use direct Python runner invocation and no shell-only installed path.
- [x] T010 [S1] [US1, FR-002, FR-003, FR-022] Update Codex active skill surfaces in `speckit-pro/codex-skills/` so scaffold, status, autopilot, install, and related installed-runtime guidance use direct Python runner invocation and no shell-only installed path.
- [x] T011 [S1] [US1, FR-002, FR-003, FR-022] Update Claude/Codex bundled agents and hooks in `speckit-pro/agents/`, `speckit-pro/codex-agents/`, `speckit-pro/hooks/hooks.json`, and `speckit-pro/codex-hooks.json` to preserve the same runner invocation contract.
- [x] T012 [S1] [US1, FR-002, FR-003, FR-004] Run Slice 1 verification with the XPLAT-008 runner invocation request, active-path guard request, and focused Layer 4 gate tests before starting generated payload or docs changes.

## Phase 2: Slice 2 - Payload, Release, and Public Docs Gates

**Goal**: Rebuild Claude and Codex generated payloads from source, verify payload completeness and release readiness, and align public docs and release-note guidance with implemented controls only.

- [x] T013 [P] [S2] [US2, FR-006, FR-007, FR-008] Add source-derived payload completeness cases and runner request fixtures under `tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/`, including read-only and apply-mode requests for rebuilding/staging Claude and Codex payloads from source.
- [x] T014 [P] [S2] [US2, US4, FR-011, FR-014, FR-019, FR-020] Add release-readiness cases and runner request fixtures under `tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/` for active shell dependencies, incomplete payloads, missing bundled agents/hooks/runner files, stale metadata, unsafe public claims, incomplete UAT evidence, unsafe repair claims, missing traceability, and nondeterministic `dist/**` output.
- [x] T015 [S2] [US2, US4, FR-006, FR-007, FR-008, FR-019] Extend `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py` so payload completeness and release-readiness negative cases fail before production gate behavior is changed.
- [x] T016 [S2] [US2, FR-006, FR-007, FR-008, FR-021] Implement the source-derived release payload inventory, transform handling, SHA-256/file-tree comparison, stale/extra/path-leak detection, and apply-mode rebuild behavior in `speckit-pro/speckit_pro_runner/gates/payloads.py`.
- [x] T017 [S2] [US2, FR-006, FR-007, FR-008, FR-021] Register XPLAT-008 payload completeness operations and request fixtures in `speckit-pro/speckit_pro_runner/gates/registry.py`.
- [x] T018 [S2] [US2, US4, FR-008, FR-011, FR-014, FR-019, FR-020] Implement the aggregate release-readiness blocker contract in `speckit-pro/speckit_pro_runner/gates/release.py`, including payload results, UAT rows, repair actions, public claim results, blocking counts, and traceability.
- [x] T019 [S2] [US2, US4, FR-007, FR-011, FR-021, FR-022] Refresh `speckit-pro/speckit_pro_runner/install_inventory.json`, `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`, and `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` for new gate, payload, version, and trust metadata surfaces.
- [x] T020 [S2] [US2, FR-006, FR-007, FR-008] Run the XPLAT-008 payload completeness read-only request and confirm seeded missing, stale, extra, path-leaking, transform, and metadata blocker cases fail before touching committed `dist/**`.
- [x] T021 [S2] [US2, FR-006, FR-007, FR-008, FR-021] Rebuild `dist/claude/speckit-pro/**` and `dist/codex/speckit-pro/**` only through the XPLAT-008 payload completeness apply-mode runner request; do not hand-edit generated payload files.
- [x] T022 [S2] [US2, FR-007, FR-008, FR-019] Run payload completeness against committed `dist/**` and run release-readiness seeded blocker checks before changing public install, docs, README, or release-note guidance.
- [x] T023 [P] [S2] [US4, FR-009, FR-010, FR-011] Update `README.md` and `speckit-pro/README.md` so install/update/trust guidance names Python 3.11+ as the installed runtime prerequisite and avoids required Bash, Git Bash, WSL, PowerShell-specific command language, or `jq`.
- [x] T024 [P] [S2] [US4, FR-009, FR-010, FR-011] Update `docs-site/src/content/docs/install/claude-code.md` and `docs-site/src/content/docs/install/codex.md` to match the implemented installed-runtime path and UAT-backed support boundary.
- [x] T025 [P] [S2] [US4, FR-009, FR-010, FR-011] Update `docs-site/src/content/docs/first-run.md`, `docs-site/src/content/docs/troubleshooting.md`, `docs-site/src/content/docs/security-and-trust.md`, `docs-site/src/content/docs/update-and-rollback.md`, and `docs-site/src/content/docs/contribute-and-release.md` so public claims describe only implemented runner, payload, trust, update, repair, and release-note controls.
- [x] T026 [S2] [US4, FR-009, FR-010, FR-011, FR-019] Run docs validation and the public-claim release-readiness check to prove docs contain no unsupported native-platform or cryptographic trust claims.
- [x] T027 [S2] [US2, US4, FR-006, FR-007, FR-008, FR-019] Run focused Layer 4 gate tests plus the XPLAT-008 payload completeness and release-readiness runner requests before starting native UAT/update/repair work.

## Phase 3: Slice 3 - Native UAT, Update, and Safe Repair

**Goal**: Provide release-reviewable native Claude/Codex evidence across Windows, macOS, and Linux, prove latest-tag update behavior, and prove bounded doctor/autoheal repair with exact manual remediation for unsafe gaps.

- [x] T028 [P] [S3] [US4, FR-012, FR-013, FR-014] Add UAT matrix fixture cases and request fixtures under `tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/` covering exactly six product/platform rows, `runner_invocation_ids`, and all required reviewer-readable fields.
- [x] T029 [P] [S3] [US3, FR-015, FR-016, FR-017] Add install health and repair fixture cases and request fixtures under `tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/` covering trusted missing/stale artifacts, unsafe unknown/extra/mismatch/trust-root/out-of-cache drift, digest verification, manual remediation, and broad reinstall rejection.
- [x] T030 [S3] [US3, US4, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017] Extend `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py` so UAT matrix and install-health repair contract failures are deterministic before implementation changes.
- [x] T031 [S3] [US4, FR-012, FR-013, FR-014, FR-019] Implement structured UAT matrix parsing and release-readiness blockers in `speckit-pro/speckit_pro_runner/gates/release.py`, including missing rows, placeholders, smoke-only evidence, failing rows, raw HTML anchors, empty expected/actual fields, missing evidence links, and unsupported public claims.
- [x] T032 [S3] [US3, FR-015, FR-016, FR-017, FR-018] Implement doctor/update/autoheal install-health behavior in `speckit-pro/speckit_pro_runner/helpers/install.py`, limiting autoheal to checksum-backed trusted artifacts and emitting exact manual remediation for unsafe gaps.
- [x] T033 [S3] [US3, US4, FR-015, FR-016, FR-017, FR-022] Register repair/update/UAT release-readiness operations and refresh runner metadata in `speckit-pro/speckit_pro_runner/gates/registry.py`, `install_inventory.json`, `speckit-pro-runner.manifest.json`, and `speckit-pro-runner.sha256`.
- [x] T034 [S3] [US4, FR-012, FR-013, FR-014] Create `specs/xplat-008-claude-codex-cutover-universal-install-release-gate/.process/uat-matrix.md` with the six required product/platform rows, runner invocation ID fields, and all required fields before platform operators fill detailed evidence.
- [ ] T035 [P] [S3] [US1, US3, US4, FR-012, FR-013, FR-018] Fill Claude on Windows native UAT evidence under `.process/uat/` for install, bundled-agent verification, first use, scaffold/status, autopilot dry-run, latest-tag update, incomplete-install repair, expected/actual results, notes, and pass/fail.
- [ ] T036 [P] [S3] [US1, US3, US4, FR-012, FR-013, FR-018] Fill Claude on macOS native UAT evidence under `.process/uat/` for install, bundled-agent verification, first use, scaffold/status, autopilot dry-run, latest-tag update, incomplete-install repair, expected/actual results, notes, and pass/fail.
- [ ] T037 [P] [S3] [US1, US3, US4, FR-012, FR-013, FR-018] Fill Claude on Linux native UAT evidence under `.process/uat/` for install, bundled-agent verification, first use, scaffold/status, autopilot dry-run, latest-tag update, incomplete-install repair, expected/actual results, notes, and pass/fail.
- [ ] T038 [P] [S3] [US1, US3, US4, FR-012, FR-013, FR-018] Fill Codex on Windows native UAT evidence under `.process/uat/` for install, bundled-agent verification, first use, scaffold/status, autopilot dry-run, latest-tag update, incomplete-install repair, expected/actual results, notes, and pass/fail.
- [ ] T039 [P] [S3] [US1, US3, US4, FR-012, FR-013, FR-018] Fill Codex on macOS native UAT evidence under `.process/uat/` for install, bundled-agent verification, first use, scaffold/status, autopilot dry-run, latest-tag update, incomplete-install repair, expected/actual results, notes, and pass/fail.
- [ ] T040 [P] [S3] [US1, US3, US4, FR-012, FR-013, FR-018] Fill Codex on Linux native UAT evidence under `.process/uat/` for install, bundled-agent verification, first use, scaffold/status, autopilot dry-run, latest-tag update, incomplete-install repair, expected/actual results, notes, and pass/fail.
- [ ] T041 [S3] [US4, FR-012, FR-013, FR-014, FR-020] Consolidate the six native UAT evidence files into `.process/uat-matrix.md` with non-placeholder operator/date, host version, plugin version or latest tag, installed cache path, interpreter resolution, runner invocation IDs, evidence link, expected result, actual result, notes, and pass/fail.
- [x] T042 [S3] [US3, US4, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019] Run the XPLAT-008 release-readiness request and confirm it blocks missing/failing UAT rows, unsafe repair claims, broad reinstall behavior, and incomplete update proof.

## Phase 4: Polish and Release Packet

**Goal**: Make the implementation reviewable as one XPLAT-008 packet with traceable requirements, verification evidence, non-goal preservation, and a blocking release-readiness result.

- [ ] T043 [S4] [US4, FR-019, FR-020] Create `specs/xplat-008-claude-codex-cutover-universal-install-release-gate/.process/release-readiness.md` summarizing payload completeness, active guard, docs claim, UAT, update, repair, and release-readiness outputs.
- [ ] T044 [S4] [US1, US2, US3, US4, FR-001, FR-020] Trace every functional requirement and success criterion to changed files and verification evidence in the release-readiness packet.
- [ ] T045 [S4] [US1, US2, US3, US4, FR-001, FR-019, FR-021, FR-022] Audit the diff for preserved non-goals: no child specs, no installed-runtime shell wrapper transition, no repo-wide historical purge, no future-facing claims, no smoke-only UAT support claim, no broad reinstall or wipe-copy repair, and no manual plugin version edits outside release-please.
- [ ] T046 [S4] [US1, US2, US3, US4, FR-004, FR-008, FR-014, FR-019] Run final verification: Layer 1 structural validation, focused Layer 4 gate tests, XPLAT-008 active guard, payload completeness, release-readiness runner requests, and docs-site validation.
- [ ] T047 [S4] [US4, FR-020] Prepare the PR review packet text with what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, rollback notes, and generated payload review guidance.

## Dependencies and Parallel Opportunities

- Slice 1 gates and fixtures (T002-T005) must pass before active runtime surface changes (T006-T011).
- Slice 2 payload/release fixtures and tests (T013-T015) must pass before payload/release gate changes (T016-T019), committed `dist/**` rebuild (T021), or public docs changes (T023-T025).
- Slice 3 UAT/repair fixtures and tests (T028-T030) must pass before repair implementation (T032) and native evidence consolidation (T041).
- Parallel-safe tasks: T002, T003, T013, T014, T023, T024, T025, T028, T029, T035, T036, T037, T038, T039, T040.
- The six native UAT evidence tasks (T035-T040) can run in parallel only when assigned to independent product/platform operators writing separate evidence files; T041 remains serial because it owns the shared matrix.
