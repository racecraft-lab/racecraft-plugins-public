# HRNS-015 approved delivery candidate path inventory

This is the conservative **per-PR candidate ledger** for the owner-approved eighteen-increment delivery direction. It preserves fourteen stories and 26 active functional requirements (29 historical IDs; FR-011–FR-013 are removed by the supplied #694 rescope). Q11’s four-slice estimate and the later five-group C1a/C1b split are historical provenance. Actual changed paths, reviewable LOC and RED/GREEN results remain unmeasured. These candidate tables supply the parent’s planned marker record; they are not emission or implementation evidence.

## Counting contract and recurring paths

- Each increment includes the six tracked workflow/process/evidence candidates listed in every table: `HRNS-015-workflow.md`, `autopilot-state.json`, `tasks.md`, `task-execution.json`, `slice-inventory.md`, and HRNS-015 `SPEC-MOC.md`. The last is a conservative generated PR/index candidate; any proven no-diff path can fall out of the actual gate, while a new path must be added and re-budgeted before publication. The parent owns workflow/state updates during this Tasks phase.
- A path is counted once per PR, including repeated helper, trust, manifest, and host paths in later PRs. Limits are ≤4 production paths and ≤24 total changed paths. Dist and reference rows are candidates requiring exact refresh/diff measurement. Packet files ignored by this repository are local process outputs, not committed PR diff candidates.
- A1a emits a prefilled note as protected content; A1b adds the fourth editable marker pair and its fingerprint/structure rules in both `pr_packet.py` and `read_only.py`. Existing registered test modules are reused where needed to keep the vertical behavior slices inside the cap: A1a/A1b use the packet mutation/read-only tests, B2b use the read-only helper tests, and C1a1/C1a2 use the phase-coverage tests. New acceptance cases are inline in those modules; tests still begin RED. Adding a fixture/module or changing a generated page beyond this ledger requires re-inventory and reallocation.
- Each increment has its own passing RED → fix → GREEN checkpoint, host parity check, generated refresh, exact changed-path and reviewable-LOC measurement, and title/release-note gate before PR emission. Production paths count source Python, schema, active config, and Codex agent TOMLs; Claude agent Markdown is host guidance. The refactor-inclusive estimate is still `not_estimated`; no implementation diff has been measured.
- Supplied #676 establishes sequential repeated-path marker support as baseline. Planning G6 requires coverage, task consistency, candidate budgets and a current planned marker record; the parent persists `pr-marker-plan.v1` after Tasks, with every `implementation_checkpoint` exactly `{"status": "pending"}` and no commit or evidence fields. Preserve the supplied `atomicity-route=one-navigable-PR` advisory without treating it as approval. Actual per-PR base/head paths, reviewable LOC and passing checkpoint evidence remain mandatory before PR emission. No planning gate pass or future diff is claimed here.

C1b1 and C1b2 create distinct structural test files for phase/analyze and checklist/implement executor twins respectively. Each NEW path belongs to one increment only; both retain all four host-definition checks, the shared modified guidance, and their 21-total/2-production candidate budgets.


Current-source reconciliation after the main merge: packet behavior now lives in `helpers/pr_packet.py`; canonical packet path shapes live in `pr_contract.py`. Shared skill host blocks replace removed Codex overlays, and Codex agent TOMLs are regenerated from authored agent Markdown. Current candidate tables below deduplicate those shared sources. Recorded historical source/checkpoint counts and evidence files are preserved; final PR base/head measurements remain required. B3b extends `quality_gates.py` plus its existing read-only adapter and retains the default configuration unchanged. Mechanical merge path reanchoring is recorded separately from the eighteen behavior checkpoints.

## Exact candidate counts

The current marker contract uses `kind=user_story`, `id=usN` for an unsplit story, and `kind=user_story_part`, `id=usN-partK`, `parent_marker_id=usN` for sequential parts of one story. Each ID below is unique and names only its own story.

| Increment | Marker ID | One story | Tasks | Production | Total | Qualification |
| --- | --- | --- | --- | ---: | ---: | --- |
| A1a | `us1-part1` | US1 | T003–T004 | 2 | 23 | Candidate only; actual diff/LOC unmeasured |
| A1b | `us1-part2` | US1 | T005 | 2 | 23 | Candidate only; actual diff/LOC unmeasured |
| A2 | `us2` | US2 | T006–T007 | 1 | 22 | Candidate only; actual diff/LOC unmeasured |
| A3 | `us3` | US3 | T008–T009 | 2 | 23 | Source delta: 18 paths; 22 with four tracked process paths; 204 authored non-process changed lines; final PR base/head diff and LOC pending |
| B1a | `us4` | US4 | T010 | 1 | 22 | Source delta: 18 paths; 22 with four tracked process paths; 497 authored non-process changed lines; final PR base/head diff and LOC pending |
| B1b | `us5` | US5 | T011 | 2 | 23 | Source delta: 19 paths; 23 with four tracked process paths; 481 authored non-process changed lines; final PR base/head diff and LOC pending |
| B2b | `us6` | US6 | T012–T013 | 1 | 23 | Source delta: 16 paths; 21 with four tracked process paths and index; 266 authored non-process changed lines; final PR base/head diff and LOC pending |
| B3a | `us7` | US7 | T014 | 1 | 18 | Candidate only; actual diff/LOC unmeasured |
| B3b | `us8` | US8 | T015–T016 | 3 | 24 | Candidate only; actual diff/LOC unmeasured |
| C1a1 | `us9` | US9 | T017 | 1 | 24 | Candidate only; actual diff/LOC unmeasured |
| C1a2 | `us10-part1` | US10 | T018 | 1 | 18 | Candidate only; actual diff/LOC unmeasured |
| C1b1 | `us10-part2` | US10 | T019 | 2 | 21 | Candidate only; actual diff/LOC unmeasured |
| C1b2 | `us10-part3` | US10 | T020–T021 | 2 | 21 | Candidate only; actual diff/LOC unmeasured |
| C2a1 | `us11` | US11 | T022–T023 | 0 | 13 | Candidate only; actual diff/LOC unmeasured |
| C2a2 | `us12` | US12 | T024 | 0 | 13 | Candidate only; actual diff/LOC unmeasured |
| C2a3 | `us13-part1` | US13 | T025 | 0 | 13 | Candidate only; actual diff/LOC unmeasured |
| C2b1 | `us13-part2` | US13 | T026–T027 | 0 | 18 | Candidate only; actual diff/LOC unmeasured |
| C2b2 | `us14` | US14 | T028–T030 | 0 | 15 | Candidate only; actual diff/LOC unmeasured |


### Shipped-scope exclusions and count provenance

The B2a implementation increment and historical T012/T013 are retired: #694 supplies named-entry scoping, exact selected pragma and missing-budget blocking. Keep those fixtures GREEN as compatibility evidence in B2b; new aggregate and greenfield behavior still starts RED.

C2b2 excludes these six shipped link-only candidates, leaving sixteen exact candidates below. The approved Plan/spec retain the conservative twenty-two-before-exclusions figure; this Tasks ledger performs the explicit removal rather than claiming new scope approval. The roadmap template remains owned by B2b for new slice-budget syntax.

- `dist/claude/speckit-pro/README.md`
- `dist/claude/speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md`
- `dist/codex/speckit-pro/README.md`
- `dist/codex/speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md`
- `speckit-pro/README.md`
- `speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md`

Candidate group unions are A: 39 total/4 production; B: 36/3; C1a: 29/1; C1b: 30/4; C2: 34/0 after these exclusions. Only the eighteen per-PR sets are within the strict caps; the group unions do not qualify as individual PRs.

## Exact path operations

### A1a — US1 optional note render/schema

Tasks: T003–T004. Requirements: FR-001, FR-003, FR-026. **23 candidate paths; 2 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/pr_packet.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/pr_packet.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/pr_packet.py` | source payload |
| production | modify | `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md` | Claude payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md` | Codex overlay |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | changed source or new test inventory candidate |
| test/manifest | modify | `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` | existing registered packet test; inline cases |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### A1b — US1 protected note validation

Tasks: T005. Requirements: FR-002, FR-026. **23 candidate paths; 2 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/pr_packet.py` | fourth editable field and note markers |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/pr_packet.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/pr_packet.py` | source payload |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/read_only.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md` | Claude payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md` | Codex overlay |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | changed source or new test inventory candidate |
| test/manifest | modify | `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` | existing registered helper test; inline cases |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### A2 — US2 packet-only guard and approved scope prose

Tasks: T006–T007. Requirements: FR-004, FR-005, FR-027, FR-026. **22 candidate paths; 1 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/mutation.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/mutation.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/mutation.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/post-implementation.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/post-implementation.md` | source payload |
| test/manifest | modify | `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` | task |
| test/manifest | add | `tests/speckit-pro/unit/fixtures/pr-packet-repair/packet-only-untracked.json` | task |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| host/support | modify | `docs/prd-harness-engineering-uplift.md` | task |
| host/support | modify | `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md` | task |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### A3 — US3 current verdict

Tasks: T008–T009. Requirements: FR-006, FR-026. **23 candidate paths; 2 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/pr_packet.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/pr_packet.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/pr_packet.py` | source payload |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/read_only.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md` | Claude payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md` | Codex overlay |
| test/manifest | modify | `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` | task |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | changed source or new test inventory candidate |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

A3 source checkpoint `c60a3398b1e07412ec3cbb4468f3ca8a16a4687d` (`e68785cd3..c60a3398`) changes 18 tracked paths, including 2 production paths. The four tracked process updates (workflow, state, tasks, inventory) bring the marker to 22 budget-counted paths; checkpoint and verification evidence are outside the path budget. Authored non-process changes total 204 lines. `test-finalize-run.py` is a necessary fixture adaptation outside the candidate list; the unused reference and index candidates were not changed. Observed RED exposed six stale-label variants, followed by GREEN and refactor; the 10,111/10,111 quick suite, 6/6 CI dispatches, generated-artifact check, docs reference/quality, pinned Python lint, privacy scan and independent critical/high review passed. Final emitted PR base/head diff and reviewable LOC remain mandatory.

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
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | changed source or new test inventory candidate |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

The B1a source checkpoint `a1aa6bd265aa15d4a7005b5c0f0be77af786cb04` changes 18 tracked paths, including one production path. Four tracked process updates (workflow, state, tasks, inventory) bring the marker to the 22-path cap; checkpoint and verification reports are outside that budget. Authored non-process changes total 497 lines, above the 400-line review warning and below the 800-line block. The native functional catalog and read-only helper test expectation updates are necessary fixture adaptations; the unused task-execution and spec-index candidates have no diff. RED/GREEN/refactor marker tests, 10,118/10,118 quick suite, 6/6 CI dispatches, generated-artifact check, full docs validation, pinned Python lint, privacy 14/14, host parity and bounded independent review passed. Unclosed fences count markers conservatively, so an ambiguous construct may overcount; this cannot hide a visible marker. Final emitted PR base/head diff and reviewable LOC remain mandatory.

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
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | changed source or new test inventory candidate |
| generated reference | regenerate | `docs-site/src/content/docs/reference/scripts.md` | changed skill/script inventory candidate |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

The B1b source checkpoint `4c7ec9ec41d9592b8444370b9012e577b1b8288d` changes 19 tracked paths, including two production paths. Four tracked process updates (workflow, state, tasks, inventory) bring the marker to its 23-path cap; checkpoint and verification reports are outside that budget. Authored non-process changes total 481 lines, above the 400-line review warning and below the 800-line block. The existing index-generation, release-refresh, and read-only helper tests were necessary fixture adaptations; the unused FORMAL-001 index, scripts reference, and task-execution sidecar candidates have no diff. RED/GREEN/refactor freshness cases, quick suite 10,261/10,261, CI suite 6/6, generated-artifact check, full docs validation, pinned Python lint, privacy 14/14, host parity, and independent review passed. Final emitted PR base/head diff and reviewable LOC remain mandatory.

### B2b — US6 complete slice and greenfield budgets

Tasks: T012–T013. Requirements: FR-014, FR-028, FR-029, FR-026. **23 candidate paths; 1 production.**

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
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| test/manifest | modify | `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` | existing registered helper test; inline cases |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | changed source or new test inventory candidate |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

The B2b source checkpoint `ac06e2d512c48b2c3b9bb31aa0cac480c187f84d` changes 16 tracked paths, including one production path. Four tracked process updates (workflow, state, tasks, inventory) and the HRNS-015 index bring the marker to 21 budget-counted paths, below its 23-path cap; checkpoint and verification reports are outside that budget. Authored non-process changes total 266 lines. The unused task-execution sidecar and docs reference candidate have no diff. RED/GREEN/refactor helper cases, quick suite 10,266/10,266, CI suite 6/6, generated-artifact check, full docs validation, pinned Python lint, privacy 14/14, host parity and independent review passed. Independent review's two fail-open cases were repaired red-first and rechecked clean. Final emitted PR base/head diff and reviewable LOC remain mandatory.

### B3a — US7 required-refactor estimate

Tasks: T014. Requirements: FR-015, FR-026. **18 candidate paths; 1 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/read_only.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| test/manifest | add | `tests/speckit-pro/unit/test-size-estimate-refactors.py` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | changed source or new test inventory candidate |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### B3b — US8 declared quality commands

Tasks: T015–T016. Requirements: FR-016, FR-026. **24 candidate paths; 3 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/read_only.py` | task |
| production | modify | `speckit-pro/speckit_pro_runner/quality_gates.py` | existing quality configuration owner |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/quality_gates.py` | existing quality configuration owner |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/quality_gates.py` | existing quality configuration owner |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| production | modify | `speckit-pro/speckit_pro_runner/contracts/quality-gates.schema.json` | canonical declared-command contract |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/contracts/quality-gates.schema.json` | canonical declared-command contract |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/contracts/quality-gates.schema.json` | canonical declared-command contract |
| test/manifest | add | `tests/speckit-pro/unit/test-declared-quality-commands.py` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | runner source edited |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | changed source or new test inventory candidate |
| process/evidence | modify | `docs/ai/specs/.process/HRNS-015-workflow.md` | per-marker workflow checkpoint |
| process/evidence | modify | `docs/ai/specs/.process/autopilot-state.json` | per-marker persisted state |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md` | task completion checkboxes |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json` | tasks source fingerprint |
| process/evidence | modify | `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` | RED/GREEN and measured budget evidence |
| generated index | regenerate | `specs/hrns-015-autopilot-gate-pr-emission-repair/SPEC-MOC.md` | PR/index refresh candidate |

### C1a1 — US9 canonical Post list

Tasks: T017. Requirements: FR-017, FR-026. **24 candidate paths; 1 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md` | Claude payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md` | Codex overlay |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md` | source payload |
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
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | source payload |

### C1a2 — US10 persisted completion boundary

Tasks: T018. Requirements: FR-018, FR-026. **18 candidate paths; 1 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md` | Claude payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md` | Codex overlay |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/post-implementation.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/post-implementation.md` | source payload |
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

Tasks: T019. Requirements: FR-019, FR-026. **21 candidate paths; 2 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| host/support | modify | `speckit-pro/agents/phase-executor.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/agents/phase-executor.md` | Claude agent |
| production | regenerate | `speckit-pro/codex-agents/phase-executor.toml` | generated from the authored agent host blocks |
| generated | regenerate | `dist/codex/speckit-pro/codex-agents/phase-executor.toml` | Codex agent |
| host/support | modify | `speckit-pro/agents/analyze-executor.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/agents/analyze-executor.md` | Claude agent |
| production | regenerate | `speckit-pro/codex-agents/analyze-executor.toml` | generated from the authored agent host blocks |
| generated | regenerate | `dist/codex/speckit-pro/codex-agents/analyze-executor.toml` | Codex agent |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` | source payload |
| test/manifest | add | `tests/speckit-pro/layer1-structural/test-phase-analyze-teardown.py` | task |
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

Tasks: T020–T021. Requirements: FR-019, FR-026. **21 candidate paths; 2 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| host/support | modify | `speckit-pro/agents/checklist-executor.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/agents/checklist-executor.md` | Claude agent |
| production | regenerate | `speckit-pro/codex-agents/checklist-executor.toml` | generated from the authored agent host blocks |
| generated | regenerate | `dist/codex/speckit-pro/codex-agents/checklist-executor.toml` | Codex agent |
| host/support | modify | `speckit-pro/agents/implement-executor.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/agents/implement-executor.md` | Claude agent |
| production | regenerate | `speckit-pro/codex-agents/implement-executor.toml` | generated from the authored agent host blocks |
| generated | regenerate | `dist/codex/speckit-pro/codex-agents/implement-executor.toml` | Codex agent |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` | source payload |
| test/manifest | add | `tests/speckit-pro/layer1-structural/test-checklist-implement-teardown.py` | task |
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

Tasks: T022–T023. Requirements: FR-020, FR-021, FR-026. **13 candidate paths; 0 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| host/support | modify | `speckit-pro/skills/speckit-resolve-pr/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-resolve-pr/SKILL.md` | Claude payload |
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

Tasks: T024. Requirements: FR-022, FR-023, FR-026. **13 candidate paths; 0 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| host/support | modify | `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | Claude payload |
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

Tasks: T025. Requirements: FR-024, FR-026. **13 candidate paths; 0 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| host/support | modify | `speckit-pro/skills/speckit-status/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-status/SKILL.md` | Claude payload |
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

Tasks: T026–T027. Requirements: FR-024, FR-026. **18 candidate paths; 0 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| host/support | modify | `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | Claude payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | Codex overlay |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/phase-execution.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/phase-execution.md` | source payload |
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

### C2b2 — US14 existing legacy workflow links

Tasks: T028–T030. Requirements: FR-025, FR-026. **15 candidate paths; 0 production.**

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| host/support | modify | `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | Claude payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | Codex overlay |
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

The tables are complete named candidates under the present task design, not measured final diffs. Regenerate `dist`, runner trust outputs, spec indexes, and reference pages at each owning checkpoint; compare against the exact marker base/head. If an output changes outside this ledger, a fixture needs another child, a refactor adds a path, production exceeds four, total reaches 25, or LOC crosses a block line, stop and reallocate before that PR. T031 records full cross-feature verification. No implementation checkbox is complete.

Sequential repeated-path support is supplied as shipped in #676; do not remove honest repeated declarations. Actual changed paths, LOC and implementation checkpoint evidence remain unqualified. The parent validates the current planned marker record and planning G6 after Tasks; no future implementation diff is fabricated to satisfy that gate.

### B3a implementation measurement

T014: RED ten assertion failures; GREEN and refactor 28/28; existing estimator 31/31. The delta from the prior checkpoint contains 16 owned paths, 1 production paths and 76 authored non-process changed lines. Generated payload and trust files are refreshed; the new test is registered. All paths are within the native task ownership and candidate inventory. The us7 marker stays pending for final broad qualification.
