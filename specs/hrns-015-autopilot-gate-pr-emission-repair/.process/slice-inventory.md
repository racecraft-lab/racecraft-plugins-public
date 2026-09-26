# HRNS-015 proposed review-increment path inventory

This is a conservative **per-PR candidate ledger** after the user directed repair of the original A/B/C2 budget breaches while retaining all 29 FRs. Q11’s four-slice estimate and the later five-slice C1a/C1b decision are historical; this 19-increment revision keeps those behavior boundaries and gives every marker exactly one user-story identity. It is not an emitted or validated marker plan. Actual changed files, reviewable LOC, fingerprints, and RED/GREEN results remain unmeasured.

## Counting contract and recurring paths

- Each increment includes the six tracked workflow/process/evidence candidates listed in every table: `HRNS-015-workflow.md`, `autopilot-state.json`, `tasks.md`, `task-execution.json`, `slice-inventory.md`, and HRNS-015 `SPEC-MOC.md`. The last is a conservative generated PR/index candidate; any proven no-diff path can fall out of the actual gate, while a new path must be added and re-budgeted before publication. The parent owns workflow/state updates during this Analyze dispatch.
- A path is counted once per PR, including repeated helper, trust, manifest, and host paths in later PRs. Limits are ≤4 production paths and ≤24 total changed paths. Dist and reference rows are candidates requiring exact refresh/diff measurement. Packet files ignored by this repository are local process outputs, not committed PR diff candidates.
- A1a emits a prefilled note as protected content; A1b adds the fourth editable marker pair and its fingerprint/structure rules in both `pr_emission.py` and `read_only.py`. Existing registered test modules are reused where needed to keep the vertical behavior slices inside the cap: A1a/A1b use the packet mutation/read-only tests, B2a/B2b use the read-only helper tests, and C1a1/C1a2 use the phase-coverage tests. New acceptance cases are inline in those modules; tests still begin RED. Adding a fixture/module or changing a generated page beyond this ledger requires re-inventory and reallocation.
- Each increment has its own passing RED → fix → GREEN checkpoint, host parity check, generated refresh, exact changed-path and reviewable-LOC measurement, and title/release-note gate before PR emission. Production paths count source Python, schema, active config, and Codex agent TOMLs; Claude agent Markdown is host guidance. The refactor-inclusive estimate is still `not_estimated`; no implementation diff has been measured.
- The current `pr_marker_plan` validator rejects legitimate sequential reuse of declared paths. Do not persist a marker plan or claim G6/PR emission until that product contract is repaired and its independent gate passes. The advisory `atomicity-route=one-navigable-PR` is retained as an advisory result.

## Exact candidate counts

The current marker contract uses `kind=user_story`, `id=usN` for an unsplit story, and `kind=user_story_part`, `id=usN-partK`, `parent_marker_id=usN` for sequential parts of one story. Each ID below is unique and names only its own story.

| Increment | Marker ID | One story | Tasks | Production | Total | Qualification |
| --- | --- | --- | --- | ---: | ---: | --- |
| A1a | `us1-part1` | US1 | T003–T004 | 2 | 24 | Candidate only; actual diff/LOC unmeasured |
| A1b | `us1-part2` | US1 | T005 | 2 | 24 | Candidate only; actual diff/LOC unmeasured |
| A2 | `us2` | US2 | T006–T007 | 1 | 24 | Candidate only; actual diff/LOC unmeasured |
| A3 | `us3` | US3 | T008–T009 | 2 | 24 | Candidate only; actual diff/LOC unmeasured |
| B1a | `us4` | US4 | T010 | 1 | 22 | Candidate only; actual diff/LOC unmeasured |
| B1b | `us5` | US5 | T011 | 2 | 23 | Candidate only; actual diff/LOC unmeasured |
| B2a | `us6-part1` | US6 | T012–T013 | 2 | 22 | Candidate only; actual diff/LOC unmeasured |
| B2b | `us6-part2` | US6 | T014–T015 | 1 | 23 | Candidate only; actual diff/LOC unmeasured |
| B3a | `us7` | US7 | T016 | 1 | 18 | Candidate only; actual diff/LOC unmeasured |
| B3b | `us8` | US8 | T017–T018 | 2 | 22 | Candidate only; actual diff/LOC unmeasured |
| C1a1 | `us9` | US9 | T019 | 1 | 24 | Candidate only; actual diff/LOC unmeasured |
| C1a2 | `us10-part1` | US10 | T020 | 1 | 21 | Candidate only; actual diff/LOC unmeasured |
| C1b1 | `us10-part2` | US10 | T021 | 2 | 21 | Candidate only; actual diff/LOC unmeasured |
| C1b2 | `us10-part3` | US10 | T022–T023 | 2 | 21 | Candidate only; actual diff/LOC unmeasured |
| C2a1 | `us11` | US11 | T024–T025 | 0 | 14 | Candidate only; actual diff/LOC unmeasured |
| C2a2 | `us12` | US12 | T026 | 0 | 14 | Candidate only; actual diff/LOC unmeasured |
| C2a3 | `us13-part1` | US13 | T027 | 0 | 14 | Candidate only; actual diff/LOC unmeasured |
| C2b1 | `us13-part2` | US13 | T028–T029 | 0 | 21 | Candidate only; actual diff/LOC unmeasured |
| C2b2 | `us14` | US14 | T030–T032 | 0 | 22 | Candidate only; actual diff/LOC unmeasured |

## Exact path operations

### A1a — US1 optional note render/schema

Tasks: T003–T004. Requirements: FR-001, FR-003, FR-026. **24 candidate paths; 2 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/pr_emission.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/pr_emission.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/pr_emission.py` | source payload |
| production | modify | `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md` | Claude payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md` | Codex overlay |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | changed source or new test inventory candidate |
| test/manifest | modify | `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` | existing registered packet test; inline cases |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### A1b — US1 protected note validation

Tasks: T005. Requirements: FR-002, FR-026. **24 candidate paths; 2 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/pr_emission.py` | fourth editable field and note markers |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/pr_emission.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/pr_emission.py` | source payload |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/read_only.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md` | Claude payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md` | Codex overlay |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | changed source or new test inventory candidate |
| test/manifest | modify | `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` | existing registered helper test; inline cases |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### A2 — US2 packet-only guard and approved scope prose

Tasks: T006–T007. Requirements: FR-004, FR-005, FR-027, FR-026. **24 candidate paths; 1 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/mutation.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/mutation.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/mutation.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/post-implementation.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/post-implementation.md` | source payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/post-implementation-codex.md` | Codex overlay |
| test/manifest | modify | `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` | task |
| test/manifest | add | `tests/speckit-pro/unit/fixtures/pr-packet-repair/packet-only-untracked.json` | task |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| host/support | modify | `docs/prd-harness-engineering-uplift.md` | task |
| host/support | modify | `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md` | task |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### A3 — US3 current verdict

Tasks: T008–T009. Requirements: FR-006, FR-026. **24 candidate paths; 2 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/pr_emission.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/pr_emission.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/pr_emission.py` | source payload |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/read_only.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md` | Claude payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md` | Codex overlay |
| test/manifest | modify | `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` | task |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | changed source or new test inventory candidate |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### B1a — US4 visible marker counts

Tasks: T010. Requirements: FR-007, FR-008, FR-026. **22 candidate paths; 1 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/read_only.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | source payload |
| test/manifest | add | `tests/speckit-pro/unit/test-marker-visibility.py` | task |
| test/manifest | add | `tests/speckit-pro/unit/fixtures/marker-visibility/cases.json` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | changed source or new test inventory candidate |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### B1b — US5 tracked spec index

Tasks: T011. Requirements: FR-009, FR-010, FR-026. **23 candidate paths; 2 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/read_only.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| production | modify | `scripts/refresh-release-artifacts.py` | task |
| generated index | regenerate | `specs/formal-001-selective-formal-methods/SPEC-MOC.md` | task |
| host/support | modify | `AGENTS.md` | task |
| test/manifest | add | `tests/speckit-pro/unit/test-spec-index-freshness.py` | task |
| test/manifest | add | `tests/speckit-pro/unit/fixtures/spec-index-freshness/historical-stale-index.md` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | changed source or new test inventory candidate |
| generated reference | regenerate | `docs-site/src/content/docs/reference/scripts.md` | changed skill/script inventory candidate |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### B2a — US6 named entry and typed exception

Tasks: T012–T013. Requirements: FR-011–FR-013, FR-026. **22 candidate paths; 2 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/read_only.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/registry.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/registry.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/registry.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | source payload |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| test/manifest | modify | `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` | existing registered helper test; inline cases |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### B2b — US6 complete slice and greenfield budgets

Tasks: T014–T015. Requirements: FR-014, FR-028, FR-029, FR-026. **23 candidate paths; 1 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/read_only.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md` | source payload |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| test/manifest | modify | `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` | existing registered helper test; inline cases |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | changed source or new test inventory candidate |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### B3a — US7 required-refactor estimate

Tasks: T016. Requirements: FR-015, FR-026. **18 candidate paths; 1 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/read_only.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| test/manifest | add | `tests/speckit-pro/unit/test-size-estimate-refactors.py` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | changed source or new test inventory candidate |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### B3b — US8 declared quality commands

Tasks: T017–T018. Requirements: FR-016, FR-026. **22 candidate paths; 2 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/read_only.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | source payload |
| production | modify | `.specify/quality-gates.json` | task |
| test/manifest | add | `tests/speckit-pro/unit/test-declared-quality-commands.py` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | changed source or new test inventory candidate |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### C1a1 — US9 canonical Post list

Tasks: T019. Requirements: FR-017, FR-026. **24 candidate paths; 1 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md` | Claude payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md` | Codex overlay |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md` | source payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-autopilot/references/task-list-canonical-codex.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/task-list-canonical-codex.md` | Codex overlay |
| host/support | modify | `speckit-pro/skills/speckit-coach/templates/workflow-template.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-coach/templates/workflow-template.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-coach/templates/workflow-template.md` | source payload |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | changed source or new test inventory candidate |
| generated reference | regenerate | `docs-site/src/content/docs/reference/scripts.md` | changed skill/script inventory candidate |
| test/manifest | modify | `tests/speckit-pro/unit/test-autopilot-phase-coverage.py` | existing registered Post/guard test; inline cases |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### C1a2 — US10 persisted completion boundary

Tasks: T020. Requirements: FR-018, FR-026. **21 candidate paths; 1 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md` | Claude payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md` | Codex overlay |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/post-implementation.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/post-implementation.md` | source payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/post-implementation-codex.md` | Codex overlay |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | changed source or new test inventory candidate |
| generated reference | regenerate | `docs-site/src/content/docs/reference/scripts.md` | changed skill/script inventory candidate |
| test/manifest | modify | `tests/speckit-pro/unit/test-autopilot-phase-coverage.py` | existing registered Post/guard test; inline cases |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### C1b1 — US10 phase/analyze team teardown

Tasks: T021. Requirements: FR-019, FR-026. **21 candidate paths; 2 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| host/support | modify | `speckit-pro/agents/phase-executor.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/agents/phase-executor.md` | Claude agent |
| production | modify | `speckit-pro/codex-agents/phase-executor.toml` | task |
| generated | regenerate | `dist/codex/speckit-pro/codex-agents/phase-executor.toml` | Codex agent |
| host/support | modify | `speckit-pro/agents/analyze-executor.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/agents/analyze-executor.md` | Claude agent |
| production | modify | `speckit-pro/codex-agents/analyze-executor.toml` | task |
| generated | regenerate | `dist/codex/speckit-pro/codex-agents/analyze-executor.toml` | Codex agent |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` | source payload |
| test/manifest | add | `tests/speckit-pro/layer1-structural/test-team-teardown.py` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated reference | regenerate | `docs-site/src/content/docs/reference/agents.md` | agent frontmatter might change |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | changed source or new test inventory candidate |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### C1b2 — US10 checklist/implement team teardown

Tasks: T022–T023. Requirements: FR-019, FR-026. **21 candidate paths; 2 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| host/support | modify | `speckit-pro/agents/checklist-executor.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/agents/checklist-executor.md` | Claude agent |
| production | modify | `speckit-pro/codex-agents/checklist-executor.toml` | task |
| generated | regenerate | `dist/codex/speckit-pro/codex-agents/checklist-executor.toml` | Codex agent |
| host/support | modify | `speckit-pro/agents/implement-executor.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/agents/implement-executor.md` | Claude agent |
| production | modify | `speckit-pro/codex-agents/implement-executor.toml` | task |
| generated | regenerate | `dist/codex/speckit-pro/codex-agents/implement-executor.toml` | Codex agent |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` | source payload |
| test/manifest | add | `tests/speckit-pro/layer1-structural/test-team-teardown.py` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated reference | regenerate | `docs-site/src/content/docs/reference/agents.md` | agent frontmatter might change |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | changed source or new test inventory candidate |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### C2a1 — US11 complete review feedback after verified push

Tasks: T024–T025. Requirements: FR-020, FR-021, FR-026. **14 candidate paths; 0 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| host/support | modify | `speckit-pro/skills/speckit-resolve-pr/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-resolve-pr/SKILL.md` | Claude payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-resolve-pr/SKILL.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-resolve-pr/SKILL.md` | Codex overlay |
| test/manifest | add | `tests/speckit-pro/unit/test-resolve-pr-protocol.py` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | changed source or new test inventory candidate |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | changed source or new test inventory candidate |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### C2a2 — US12 await blind-spot result

Tasks: T026. Requirements: FR-022, FR-023, FR-026. **14 candidate paths; 0 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| host/support | modify | `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | Claude payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | Codex overlay |
| test/manifest | add | `tests/speckit-pro/unit/test-scaffold-blindspot.py` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | changed source or new test inventory candidate |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | changed source or new test inventory candidate |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### C2a3 — US13 status request envelopes

Tasks: T027. Requirements: FR-024, FR-026. **14 candidate paths; 0 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| host/support | modify | `speckit-pro/skills/speckit-status/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-status/SKILL.md` | Claude payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-status/SKILL.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-status/SKILL.md` | Codex overlay |
| test/manifest | add | `tests/speckit-pro/unit/test-status-envelope-contract.py` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | changed source or new test inventory candidate |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | changed source or new test inventory candidate |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### C2b1 — US13 scaffold/phase request envelopes

Tasks: T028–T029. Requirements: FR-024, FR-026. **21 candidate paths; 0 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| host/support | modify | `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | Claude payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | Codex overlay |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/phase-execution.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/phase-execution.md` | source payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/phase-execution-codex.md` | Codex overlay |
| test/manifest | add | `tests/speckit-pro/unit/test-scaffold-envelope-contract.py` | task |
| test/manifest | add | `tests/speckit-pro/unit/test-phase-envelope-contract.py` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | changed source or new test inventory candidate |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | changed source or new test inventory candidate |
| generated reference | regenerate | `docs-site/src/content/docs/reference/source-vs-dist.md` | changed source or new test inventory candidate |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### C2b2 — US14 workflow links

Tasks: T030–T032. Requirements: FR-025, FR-026. **22 candidate paths; 0 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| host/support | modify | `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | Claude payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | Codex overlay |
| host/support | modify | `speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md` | source payload |
| host/support | modify | `speckit-pro/README.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/README.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/README.md` | source payload |
| test/manifest | add | `tests/speckit-pro/unit/test-roadmap-workflow-links.py` | task |
| test/manifest | add | `tests/speckit-pro/unit/fixtures/roadmap-workflow-links/cases.json` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | changed source or new test inventory candidate |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | changed source or new test inventory candidate |
| generated reference | regenerate | `docs-site/src/content/docs/reference/source-vs-dist.md` | changed source or new test inventory candidate |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

## Qualification and stop conditions

The tables are complete named candidates under the present task design, not measured final diffs. Regenerate `dist`, runner trust outputs, spec indexes, and reference pages at each owning checkpoint; compare against the exact marker base/head. If an output changes outside this ledger, a fixture needs another child, a refactor adds a path, production exceeds four, total reaches 25, or LOC crosses a block line, stop and reallocate before that PR. T033 records full cross-feature verification. No implementation checkbox is complete.

The installed changed-file-manifest validator treats a repeated path as globally owned by one marker. This conflicts with sequential reuse of the runner, suite manifest, host guidance, process evidence, and trust outputs here. Do not remove repeated declarations to satisfy it; repair and test the product contract before persisting markers. Actual changed paths, LOC, and G6 remain unqualified.
