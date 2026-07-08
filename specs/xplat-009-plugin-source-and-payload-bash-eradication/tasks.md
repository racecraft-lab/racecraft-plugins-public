---
description: "Task list for XPLAT-009 implementation"
---

# Tasks: Plugin Source and Payload Bash Eradication

**Input**: Design documents from `specs/xplat-009-plugin-source-and-payload-bash-eradication/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, and completed `checklists/`

**Tests**: Required by `spec.md`, `plan.md`, and the integration/reliability/security checklists. Test and guard tasks are ordered before source script deletion, active guidance changes, payload rebuilds, and release-readiness tightening.

**Task-generation rationale**: This task list follows `docs/ai/specs/.process/XPLAT-009-design-concept.md`, `spec.md`, and `plan.md`: one workflow, two vertical PR-ready slices, source cleanup first, payload/cache proof second. Non-goals remain excluded: XPLAT-010 repository-wide Bash cleanup, XPLAT-008 native UAT completion, live Bash fallback paths, and historical/archive prose rewrites solely to erase legacy wording.

**Organization**: Tasks are grouped by the accepted two slices, not by broad technical layer. Every task names the user story and functional requirements it covers.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because file ownership and dependencies are independent.
- **[Story]**: User story from `spec.md` (`US1`, `US2`, `US3`).
- Each task includes repo-relative file paths and functional requirement references.

---

## Phase 1: Slice 1 - Active Plugin-Source Bash Removal

**Goal**: `speckit-pro/` source has zero live `.sh` files, no Python wrapper around live shell scripts, and no active Bash/`.sh`/`jq`/shell-oriented guidance.

**Independent Test**: Run source-level inventory, focused helper/gate tests, active guidance scan, and `find speckit-pro -type f -name '*.sh'` after source cleanup. Expected result: zero live `.sh` files and zero unallowlisted active source guidance findings.

### Tests and Source Ownership Proof Before Source Changes

- [x] T001 [US1,US3] Capture the active source inventory in `docs/ai/specs/.process/XPLAT-009-source-inventory.md`, including all 35 current `speckit-pro/**/*.sh` paths, hashes, active Bash/`.sh`/`jq` guidance hits, classification, and delete criteria. Covers FR-001, FR-009, FR-011.
- [x] T002 [US1,US3] Add Python ownership mapping to `docs/ai/specs/.process/XPLAT-009-source-inventory.md` for every retained active behavior, naming helper/gate IDs, operation IDs, modules, prior script paths as inactive provenance, and required tests. Covers FR-001, FR-002, FR-004, FR-009, FR-011.
- [x] T003 [P] [US1] Add focused regression coverage for read-only helper ownership and registry output cleanup in `tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py`, proving active outputs expose Python operation IDs instead of runnable `.sh` paths. Covers FR-002, FR-004, FR-005.
- [x] T004 [P] [US1] Add focused regression coverage for mutation, install, PR-emission, and command-plan helper ownership in `tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py`, including delete-only proof for obsolete shell behavior. Covers FR-002, FR-003, FR-004.
- [x] T005 [P] [US1,US3] Add source zero-Bash guard fixtures and seeded regression cases in `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/allowlist.json`, `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/zero-bash-guard-cases.json`, and `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py` before deleting scripts or editing active guidance. Covers FR-005, FR-009, FR-010.

### Python Ownership and Guard Implementation Before Deletion

- [x] T006 [US1] Update `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `speckit-pro/speckit_pro_runner/helpers/registry.py` so read-only helper records are Python-authoritative and active output records no longer expose runnable `.sh` paths. Covers FR-002, FR-004, FR-005.
- [x] T007 [US1] Update `speckit-pro/speckit_pro_runner/helpers/install.py`, `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`, and `speckit-pro/speckit_pro_runner/helpers/registry.py` so mutation/install/PR-emission behavior is Python-owned or explicitly inactive/delete-only before source script removal. Covers FR-002, FR-003, FR-004.
- [x] T008 [US1,US3] Implement source-scope no-shell/no-`jq` classification and historical allowlist handling in `speckit-pro/speckit_pro_runner/gates/active_path_guard.py` and register `active-path-guard/zero-bash-guard` in `speckit-pro/speckit_pro_runner/gates/registry.py`. Covers FR-005, FR-009, FR-010.
- [x] T009 [US1] Refresh runner metadata in `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` and `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` after Python helper/gate ownership changes. Covers FR-002, FR-004, FR-012.
- [x] T010 [US1,US3] Run the focused helper/gate tests from T003-T005 and record pre-deletion pass/fail evidence in `docs/ai/specs/.process/XPLAT-009-source-inventory.md`; do not delete `.sh` files or edit active guidance until these checks pass. Covers FR-002, FR-003, FR-004, FR-010, FR-011.

### Active Guidance Cleanup and Source Script Deletion

- [x] T011 [US1] Update every active source guidance file identified by T001/T005/T008 under `speckit-pro/skills/**`, `speckit-pro/codex-skills/**`, `speckit-pro/agents/**`, `speckit-pro/codex-agents/**`, `speckit-pro/hooks/**`, `speckit-pro/codex-hooks.json`, `speckit-pro/scripts/**`, `speckit-pro/README.md`, `README.md`, and current plugin/root install guidance so active instructions reference Python runner/helper/gate operation IDs with no active Bash, `.sh`, `jq`, shell interpolation, Git Bash, WSL, PowerShell-specific command-language, or Unix-only path. Covers FR-004, FR-005, FR-012.
- [x] T012 [US1] Delete install source scripts `speckit-pro/codex-skills/install/scripts/install-codex-agents.sh` and `speckit-pro/scripts/install-curated-set.sh` only after T006-T011 prove Python ownership or delete-only status. Covers FR-002, FR-003, FR-004.
- [x] T013 [US1] Delete read-only/advisory autopilot source scripts `speckit-pro/skills/speckit-autopilot/scripts/validate-agent-install.sh`, `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh`, `speckit-pro/skills/speckit-autopilot/scripts/detect-commands.sh`, `speckit-pro/skills/speckit-autopilot/scripts/count-markers.sh`, `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-workflow-contract.sh`, `speckit-pro/skills/speckit-autopilot/scripts/validate-gate.sh`, `speckit-pro/skills/speckit-autopilot/scripts/resolve-confidence-mode.sh`, `speckit-pro/skills/speckit-autopilot/scripts/confidence-gate.sh`, `speckit-pro/skills/speckit-autopilot/scripts/estimate-reviewable-loc.sh`, `speckit-pro/skills/speckit-autopilot/scripts/detect-presets.sh`, `speckit-pro/skills/speckit-autopilot/scripts/detect-stack-manager.sh`, `speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh`, `speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh`, `speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh`, `speckit-pro/skills/speckit-autopilot/scripts/o5-topology.sh`, and `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh` only after replacement behavior tests pass. Covers FR-002, FR-003, FR-004.
- [x] T014 [US1] Delete mutation/process autopilot source scripts `speckit-pro/skills/speckit-autopilot/scripts/aggregate-crl.sh`, `speckit-pro/skills/speckit-autopilot/scripts/final-reviewability-backstop.sh`, `speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh`, `speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh`, `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh`, `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh`, `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh`, `speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh`, `speckit-pro/skills/speckit-autopilot/scripts/validate-uat-runbook.sh`, `speckit-pro/skills/speckit-autopilot/scripts/parse-consensus-categories.sh`, and `speckit-pro/skills/speckit-autopilot/scripts/restack.sh` only after retained behavior is Python-owned or confirmed obsolete. Covers FR-002, FR-003, FR-004.
- [x] T015 [US1] Delete shell library scripts `speckit-pro/skills/speckit-autopilot/scripts/lib/moc-frontmatter.sh`, `speckit-pro/skills/speckit-autopilot/scripts/lib/specify-cli.sh`, and `speckit-pro/skills/speckit-autopilot/scripts/lib/moc-id-normalize.sh` after dependent active scripts are ported or deleted. Covers FR-002, FR-003, FR-004.
- [x] T016 [US1] Delete coach helper scripts `speckit-pro/skills/speckit-coach/scripts/project-fixup.sh`, `speckit-pro/skills/speckit-coach/scripts/ensure-reviewability-preset.sh`, and `speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh` after active guidance and ownership checks prove they are no longer live Bash entrypoints. Covers FR-002, FR-003, FR-004.
- [x] T017 [US1,US3] Run source-slice verification and update `docs/ai/specs/.process/XPLAT-009-source-inventory.md`: `find speckit-pro -type f -name '*.sh'` returns zero, active source guidance has zero unallowlisted findings, focused Layer 4 helper/gate checks pass, and no Python wrapper invokes a live `.sh` file. Covers FR-001, FR-003, FR-004, FR-005, FR-010, FR-011.

**Checkpoint**: Slice 1 is complete when `speckit-pro/` source has zero live `.sh` files, active source guidance points only at Python runner/helper/gate behavior, and source-level guard evidence is recorded.

---

## Phase 2: Slice 2 - Payload Rebuild and Zero-Bash Proof

**Goal**: Rebuilt Claude/Codex payloads and bounded installed-cache proof are source-derived, contain zero `.sh` files, contain no active Bash/`jq` guidance, and feed release readiness through a Python-backed guard.

**Independent Test**: Rebuild payloads via Python runner apply mode, run payload completeness read-only checks, produce bounded installed-cache proof from rebuilt payloads, run the zero-Bash guard across source/payload/cache roots, and run release-readiness integration. Expected result: zero blocking findings and preserved XPLAT-008 native UAT known gap.

### Tests and Guard Fixtures Before Payload Rebuild or Release Tightening

- [x] T018 [US2,US3] Add payload rebuild/apply and read-only completeness fixtures in `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/requests/payload-completeness-apply.json` and regression coverage in `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py` for source roots, transform records, file-tree hashes, missing/extra/mismatched/path-leaking files, and zero generated `.sh` files. Covers FR-006, FR-007, FR-010.
- [x] T019 [US2,US3] Add bounded installed-cache proof fixture coverage in `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache-proof.json` and `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py`, rejecting mutable real user cache evidence as required proof. Covers FR-008, FR-010, FR-012.
- [x] T020 [US2,US3] Add release-readiness regression coverage in `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py` for missing scan roots, missing installed-cache proof, blocking zero-Bash findings, and allowlist entries being counted as release-ready evidence. Covers FR-009, FR-010, FR-012.

### Payload, Cache, and Release Guard Implementation

- [x] T021 [P] [US2] Extend `speckit-pro/speckit_pro_runner/gates/payloads.py` so `payload-gate/payload-completeness` apply/read-only records include source roots, transform records, file-tree hashes, missing/extra/mismatched/path-leaking files, and `script_file_count`. Covers FR-006, FR-007.
- [x] T022 [P] [US2,US3] Extend `speckit-pro/speckit_pro_runner/gates/active_path_guard.py` so `active-path-guard/zero-bash-guard` scans `speckit-pro/`, `dist/claude/speckit-pro`, `dist/codex/speckit-pro`, and installed-cache proof roots or records with bounded findings. Covers FR-008, FR-009, FR-010.
- [x] T023 [US2,US3] Wire zero-Bash guard output into release readiness in `speckit-pro/speckit_pro_runner/gates/release.py` and `speckit-pro/speckit_pro_runner/gates/registry.py`, blocking on missing roots, missing installed-cache proof, blocking findings, or allowlist evidence misuse. Covers FR-008, FR-009, FR-010, FR-012.
- [x] T024 [US2] Refresh runner metadata in `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` and `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` after payload, cache, and release guard changes. Covers FR-006, FR-008, FR-010, FR-012.

### Source-Derived Payload and Installed-Cache Proof

- [x] T025 [US2] Rebuild Claude and Codex payloads from cleaned source by running the Python runner `payload-gate/payload-completeness` operation in apply mode with committed outputs under `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`; do not hand-edit `dist/**`. Covers FR-006, FR-007, FR-012.
- [x] T026 [US2] Run `payload-gate/payload-completeness` in read-only mode after rebuild and save source-derived evidence to `docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json`, including source/output roots, hashes, transform records, zero missing/extra/mismatched/path-leaking files, and zero generated `.sh` files. Covers FR-006, FR-007, FR-011.
- [x] T027 [US2] Produce bounded installed-cache proof from rebuilt payloads and save it to `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json`, including product/surface, installed root, source payload root/hash, file inventory, `source_derived: true`, `mutable_user_cache: false`, `script_file_count: 0`, active-guidance findings, and allowlist exclusion state. Covers FR-008, FR-011, FR-012.
- [x] T028 [US2,US3] Run `active-path-guard/zero-bash-guard` across `speckit-pro/`, `dist/claude/speckit-pro/`, `dist/codex/speckit-pro/`, and the bounded installed-cache proof; save the final runner envelope to `docs/ai/specs/.process/XPLAT-009-zero-bash-guard-result.json`. Covers FR-005, FR-007, FR-008, FR-009, FR-010, FR-011.
- [x] T029 [US2,US3] Run release-readiness integration with the zero-Bash result and installed-cache proof, preserving XPLAT-008 native operator UAT as a known gap and avoiding any public native-platform readiness overclaim in `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` or release-readiness evidence. Covers FR-008, FR-010, FR-011, FR-012.
- [x] T030 [US1,US2,US3] Generate or update PR packet traceability so each FR-001 through FR-012 and SC-001 through SC-007 maps to changed files, deterministic evidence, review order by the two slices, non-goals, known XPLAT-008 UAT gap, and rollback notes. Covers FR-011, FR-012.
- [x] T031 [US1,US2,US3] Run final validation: Layer 1 structural validation, focused Layer 4 helper/gate tests, payload completeness read-only proof, installed-cache zero-Bash guard proof, release-readiness integration, and the Python-owned spec-index check established by T014 without invoking a deleted `.sh` path; record commands and evidence paths for the PR packet. Covers FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012.

**Checkpoint**: Slice 2 is complete when generated payloads, bounded installed-cache proof, zero-Bash guard evidence, release-readiness integration, and PR packet traceability all pass without masking the XPLAT-008 native UAT known gap.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Slice 1 - Active Plugin-Source Bash Removal**: Starts immediately and must finish before payload rebuild work.
- **Phase 2: Slice 2 - Payload Rebuild and Zero-Bash Proof**: Depends on Phase 1 source cleanup and active guidance cleanup.

### Critical Ordering

- T001-T002 must complete before any ownership tests or deletion tasks.
- T003-T005 must be added before T006-T011 implementation and guidance edits.
- T010 must pass before T011-T016 delete or change active source guidance.
- T018-T020 must be added before T021-T024 release/payload guard tightening.
- T025 payload rebuild must use Python runner apply mode after source cleanup; `dist/**` is never hand-edited as source of truth.
- T027 installed-cache proof must be bounded and source-derived before T028-T029 can pass.
- T030-T031 close the PR packet and validation loop after both slices are complete.

### Parallel Opportunities

- T003, T004, and T005 can run in parallel after T001-T002 because they edit separate test or fixture ownership areas.
- T021 and T022 can run in parallel after T018-T020 because they edit separate runner gate modules and converge in T023.

## Implementation Strategy

1. Complete Slice 1 tests and ownership mapping.
2. Port active behavior to Python operation IDs and remove active source guidance that points at Bash, `.sh`, or `jq`.
3. Delete source `.sh` files only after focused tests and guard proof pass.
4. Complete Slice 2 tests before rebuilding payloads or tightening release readiness.
5. Rebuild payloads from source through Python runner apply mode, then prove payload and installed-cache cleanliness.
6. Wire guard evidence into release readiness and PR packet traceability while preserving the XPLAT-008 UAT known gap.

## Notes

- `[P]` markers are intentionally narrow and limited to independent file ownership.
- Historical/archive references may remain only through release-readiness-excluded allowlist entries.
- XPLAT-010 owns repository-wide Bash cleanup outside `speckit-pro/`, generated payloads, and bounded installed-cache proof.
