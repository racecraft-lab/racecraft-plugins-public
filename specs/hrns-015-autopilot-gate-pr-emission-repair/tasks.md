# Tasks: Autopilot, Gate, and PR-Emission Repair

**Input**: Current spec, approved Plan/research/model/contracts/quickstart, ratified design concept and exact workflow Tasks prompt. The owner approved the eighteen-part direction and exact FR-024 byte-for-byte fixture requirement. Fourteen stories, 26 active FRs (29 historical IDs), 37 acceptance scenarios and eleven success criteria remain covered.

**Execution contract**: Small complete behavioral units; no wall-clock run limit. Preserve the existing execution-control run, archived consumed correction history and current owner-approved re-plan epoch; only the approved `begin-replan-epoch` action establishes a fresh correction allowance. The parent records the ordinary G6 timing correction in that allowance. Checkpoint completed work every 45 minutes. Every new behavior begins with a failing fixture, records RED, makes the minimum fix and records GREEN. Already-shipped #694/#698/#676 behavior is compatibility baseline; do not manufacture a RED claim for it. No implementation checkbox is complete.

**Reviewability**: ≤4 production and ≤24 total changed paths per PR, both hosts and generated outputs included. The exact candidate ledger is [slice-inventory.md](.process/slice-inventory.md); candidate sizes are 14–24 paths, 0–2 production, except C2b2 is sixteen after six shipped link-only exclusions from its conservative twenty-two estimate. No actual implementation diff, LOC qualification, marker emission or G6 pass is claimed. Historical Q11 four and subsequent five groups are provenance; eighteen is current owner authority. Supplied #676 supports sequential path reuse. Planning G6 validates requirement coverage, task consistency, candidate budgets and a current planned marker record. After Tasks, the parent authors `pr-marker-plan.v1` with every `implementation_checkpoint` exactly `{"status": "pending"}` and no commit or evidence fields. Actual per-PR diffs, reviewable LOC and passing checkpoint evidence remain mandatory before PR emission; the planned record supplies no implementation proof.

**Test and source rules**: Tests live only under tests/speckit-pro/, with historical prose frozen under their own fixtures; never open an active specs/<feature>/ file at test runtime. Source tooling stays Python3.11+ standard library. Both host variants ship in the same increment. No manual generated edits, force-add/ignore changes or new dependency installation.

## Approved review increments and marker boundaries

One story per increment. US1, US10 and US13 use uniquely named sequential story parts; B2b is now the unsplit US6 marker. At each closing task: regenerate exact dist/reference/trust/index candidates, run targeted acceptance and quick suite, check host parity, measure exact base/head paths and LOC, validate current markers/fingerprints and PR policy. A new path or limit breach blocks publication and requires reallocation. Candidate counts do not satisfy these gates.

| Increment | Marker ID | One story | Tasks | Production | Total | Qualification |
| --- | --- | --- | --- | ---: | ---: | --- |
| A1a | `us1-part1` | US1 | T003–T004 | 2 | 24 | Candidate only; actual diff/LOC unmeasured |
| A1b | `us1-part2` | US1 | T005 | 2 | 24 | Candidate only; actual diff/LOC unmeasured |
| A2 | `us2` | US2 | T006–T007 | 1 | 24 | Candidate only; actual diff/LOC unmeasured |
| A3 | `us3` | US3 | T008–T009 | 2 | 24 | Candidate only; actual diff/LOC unmeasured |
| B1a | `us4` | US4 | T010 | 1 | 22 | Candidate only; actual diff/LOC unmeasured |
| B1b | `us5` | US5 | T011 | 2 | 23 | Candidate only; actual diff/LOC unmeasured |
| B2b | `us6` | US6 | T012–T013 | 1 | 23 | Candidate only; actual diff/LOC unmeasured |
| B3a | `us7` | US7 | T014 | 1 | 18 | Candidate only; actual diff/LOC unmeasured |
| B3b | `us8` | US8 | T015–T016 | 2 | 22 | Candidate only; actual diff/LOC unmeasured |
| C1a1 | `us9` | US9 | T017 | 1 | 24 | Candidate only; actual diff/LOC unmeasured |
| C1a2 | `us10-part1` | US10 | T018 | 1 | 21 | Candidate only; actual diff/LOC unmeasured |
| C1b1 | `us10-part2` | US10 | T019 | 2 | 21 | Candidate only; actual diff/LOC unmeasured |
| C1b2 | `us10-part3` | US10 | T020–T021 | 2 | 21 | Candidate only; actual diff/LOC unmeasured |
| C2a1 | `us11` | US11 | T022–T023 | 0 | 14 | Candidate only; actual diff/LOC unmeasured |
| C2a2 | `us12` | US12 | T024 | 0 | 14 | Candidate only; actual diff/LOC unmeasured |
| C2a3 | `us13-part1` | US13 | T025 | 0 | 14 | Candidate only; actual diff/LOC unmeasured |
| C2b1 | `us13-part2` | US13 | T026–T027 | 0 | 21 | Candidate only; actual diff/LOC unmeasured |
| C2b2 | `us14` | US14 | T028–T030 | 0 | 16 | Candidate only; actual diff/LOC unmeasured |

## Phase 1: Setup

**Goal**: Reconcile exact candidate ownership before implementation. **Independent check**: eighteen distinct candidate tables account for repeated authored, generated, fixture and process paths; actual diff/LOC remain explicit.

- [x] T001 Verify every authored, fixture, shared, generated, trust, index, and process/evidence candidate path in `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md`; reconcile the eighteen approved sets, production classification and distinct refactors against the first actual implementation checkpoint (FR-026).

## Phase 2: Foundational reviewability checkpoint

**Goal**: Preserve the approved architecture and strict per-PR limits. **Independent check**: every candidate set is within caps; current marker validation and actual implementation qualifications are explicit pending evidence. This phase blocks all behavior units.

- [x] T002 Verify the eighteen one-story candidate sets in `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` against four production and twenty-four total paths per PR; preserve Q11/five-group provenance and shipped #676 reuse support. Validate current planned marker/fingerprint evidence under the current planning schema, preserving every checkpoint as pending without commit or evidence fields; block emission until actual per-increment diff, LOC and checkpoint gates pass (FR-026).

## Phase 3: User Story 1 — final release note (P1, A1a then A1b)

**Goal**: A final packet accepts one valid optional note. **Independent test**: the emitted body passes the feature-PR release-note policy; invalid note and draft cases fail or omit as specified (FR-001–003, FR-026).

- [x] T003 [US1] Add failing-first valid, blank, non-string, fence-breaking, absent, and draft `release_note` cases to the existing registered `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`; assert nonblank unfenced Markdown-string input, exactly one renderer-created final fence, and zero draft editable fields; use inline cases and record RED before renderer/schema edits (FR-001, FR-003).
- [x] T004 [US1] Implement optional note input/rendering as prefilled protected content in `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`, `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json`, and `speckit-pro/skills/speckit-autopilot/SKILL.md` and `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`; leave the fourth editable marker pair for A1b; prove T003 GREEN, refresh A1a outputs, run targeted and quick suites, then record A1a path/production/LOC, host parity, and marker checkpoint before T005 (FR-001, FR-003, FR-026).
- [x] T005 [US1] Add failing-first protected-heading, balanced-fence, editable-content, and policy cases in the existing registered `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py`; then add the fourth editable marker pair in `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`, update `speckit-pro/speckit_pro_runner/helpers/read_only.py` so only enclosed note content is elided while heading, markers, and fence structure stay protected, and update paired Claude/Codex autopilot skills. Prove the release-note validator passes. Prove GREEN, refresh A1b outputs, run targeted and quick suites, and record A1b path/production/LOC, host parity, and marker checkpoint before T006 (FR-002, FR-026).

## Phase 4: User Story 2 — packet-only untracked files (P1, Increment A2)

**Goal**: The current packet's three untracked files do not block its own mutation. **Independent test**: validate and refresh pass for only canonical packet files; second packet, unrelated file, tracked edit, and unreadable status block (FR-004–005, FR-026).

- [x] T006 [US2] First add failing packet-only/unrelated/second-packet/tracked/unreadable-status cases in the existing registered `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` and `tests/speckit-pro/unit/fixtures/pr-packet-repair/packet-only-untracked.json`; record RED, then repair `speckit-pro/speckit_pro_runner/helpers/mutation.py` and the exact paired post-implementation references in the A2 inventory; prove GREEN for only current packet metadata/body/validation canonical untracked paths; tracked packet edits, another packet and Git-status failure still block, without force-add or ignore-rule changes (FR-004, FR-005, FR-026).
- [x] T007 [US2] Amend AC-16.2/16.5/16.8/16.10 and the HRNS-015/HRNS-019 scope in `docs/prd-harness-engineering-uplift.md` and `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md`; record the approved eighteen-part direction and deferred ownership, remove stale #642 status, then refresh A2 outputs, run its cases and quick suite, and record its path/production/LOC, parity and checkpoint evidence (FR-026, FR-027).

## Phase 5: User Story 3 — current confidence verdict (P1, Increment A3)

**Goal**: Final body reflects current G6.5 Verdict. **Independent test**: first emission and refresh show current protected verdict; missing/invalid verdict blocks, with no overview fallback (FR-006, FR-026).

- [x] T008 [US3] Add failing-first first-emission, stale-body refresh, and missing/invalid-verdict cases inline in the existing registered `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`; then repair `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`, `speckit-pro/speckit_pro_runner/helpers/read_only.py`, and paired autopilot skills; prove the protected current Phase 6.5 Verdict (proceed/remediate/stop) under Verification on emission and supplied-body refresh GREEN without overview fallback (FR-006, FR-026).
- [x] T009 [US3] Refresh A3 outputs from `speckit-pro/speckit_pro_runner/helpers/pr_emission.py` and the exact A3 inventory, run its verdict cases and quick suite plus title/release-note checks, measure all actual changed paths and LOC, and record A3 RED/GREEN, host parity, and marker checkpoint in the slice inventory; stop before publication on any limit or failed gate (FR-006, FR-026).

## Phase 6: User Story 4 — visible marker counts (P1, Increment B1a)

**Goal**: G1–G4 and count-markers agree on visible Gap and clarification markers. **Independent test**: exact comma-token tags, two per line, visible prose, and inline/fenced/indented code have expected counts and details (FR-007–008, FR-026).

- [x] T010 [US4] First add failing cases in `tests/speckit-pro/unit/test-marker-visibility.py` for exact case-sensitive comma-separated Gap tokens in single-line nonnested tags, trimmed spaces/tabs, one count per tag, compound tags, two tags per line, and visible versus inline/fenced/indented code; record RED, then repair `speckit-pro/speckit_pro_runner/helpers/read_only.py` and shared gate guidance, verify both host payloads, and prove GREEN. Register the new test, refresh B1a outputs, run targeted/quick suites, and record B1a budget/marker checkpoint (FR-007, FR-008, FR-026).

## Phase 7: User Story 5 — tracked spec index (P1, Increment B1b)

**Goal**: Required artifact consistency detects stale tracked spec indexes. **Independent test**: stale check fails, refresh repairs, untracked nested candidate stays absent, staged addition stays eligible (FR-009–010).

- [x] T011 [US5] Freeze historical stale-index prose under `tests/speckit-pro/unit/fixtures/spec-index-freshness/historical-stale-index.md` in `tests/speckit-pro/unit/test-spec-index-freshness.py` and add RED tracked/untracked/staged cases; repair `speckit-pro/speckit_pro_runner/helpers/read_only.py`, `scripts/refresh-release-artifacts.py`, and root `AGENTS.md`, regenerate `specs/formal-001-selective-formal-methods/SPEC-MOC.md`, and prove isolated --check names stale tracked paths, plain refresh repairs them and the existing artifact-consistency job remains unchanged; prove GREEN. Register the new test, refresh B1b outputs, run targeted/quick suites, and record B1b budget/marker checkpoint (FR-009, FR-010, FR-026).

## Phase 8: User Story 6 — slice budgets and greenfield allowance (P1, B2b)

**Goal**: The named-entry #694 baseline stays GREEN while complete split and greenfield LOC-only behavior is repaired. **Independent test**: baseline `multi`, `pragma`, `nobudget` cases stay GREEN and new greenfield, aggregate and malformed-slice cases pass pass (FR-014, FR-028–029).

- [x] T012 [US6] Add failing-first complete/incomplete/duplicate/extra/non-numeric/over-line slice-row and greenfield LOC-only cases inline in the `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py`; retain #694 multi/pragma/nobudget baseline cases GREEN; record RED for new row-sum top-level aggregates, ordered `slice_results`, and blocked rows (FR-014, FR-028, FR-029).
- [x] T013 [US6] Implement exact case-sensitive ordered Slices IDs with one unique complete nonnegative-integer row per ID (Slice/Estimated LOC/Production files/Total files), reject missing/extra/duplicate/malformed/at-block rows with pass:false and exit1, preserve no-split response shape, and apply 1.5x allowance only to LOC in `speckit-pro/speckit_pro_runner/helpers/read_only.py`; update paired gate guidance and `speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md`; prove T012 GREEN without a new exception class, refresh B2b outputs, run targeted/quick suites, and record B2b budget/marker checkpoint (FR-014, FR-026, FR-028, FR-029).

## Phase 9: User Story 7 — refactor-aware estimate (P2, Increment B3a)

**Goal**: Required distinct refactor files change estimate and slice count. **Independent test**: refactor signal adds 40 LOC per distinct extra file after baseline/modify logic, missing or invalid signal leaves baseline, spike precedence holds (FR-015).

- [ ] T014 [US7] Add failing-first required_refactor_files additional-distinct-path cases (integer/integer-string normalization, missing/invalid zero, existing modify discount first, +40 LOC per extra distinct file, spike precedence and ceil(total/400) slice count), then update `speckit-pro/speckit_pro_runner/helpers/read_only.py` and `tests/speckit-pro/unit/test-size-estimate-refactors.py`; prove GREEN, confirm distinct refactor paths against the inventory, register the test, refresh B3a outputs, run targeted/quick suites, and record B3a budget/marker checkpoint (FR-015, FR-026).

## Phase 10: User Story 8 — declared quality commands (P1, Increment B3b)

**Goal**: The four approved quality slots accept explicit commands with provenance. **Independent test**: declared precedence, undeclared detection, malformed/unknown command G0 failure, and unchanged thresholds/basis (FR-016, FR-026).

- [ ] T015 [US8] Add failing-first declared-command precedence, undeclared detection, malformed/unknown G0 failure cases; then implement commands object keys only COMPLEXITY/MUTATION/DEPENDENCY_RULES/DEPENDENCY_AUDIT with nonblank strings, per-slot overrides and additive command_sources/gate source=declared; preserve thresholds15/30/60 and basis, reject invalid object/key/value at G0 with no green fallback, then update `speckit-pro/speckit_pro_runner/helpers/read_only.py`, `.specify/quality-gates.json`, `tests/speckit-pro/unit/test-declared-quality-commands.py`, and paired gate guidance; prove GREEN without parsing agent-document tables (FR-016, FR-026).
- [ ] T016 [US8] Register the new B3b test in `tests/speckit-pro/suite-manifest.json`, regenerate B3b dist/reference/trust outputs, run targeted/quick suites, and record RED/GREEN, actual file/LOC count, host parity, and marker checkpoint in the slice inventory; stop on any over-limit or incomplete inventory (FR-016, FR-026).

## Phase 11: User Story 9 — 13 canonical Post rows (P1, Increment C1a1)

**Goal**: Claude, Codex, and workflow template show the same 13 names. **Independent test**: exact once/order/count match and legacy 11-row resume preserves only unique exact-name statuses (FR-017–018, FR-026).

- [ ] T017 [US9] Add RED 11-versus-13 canonical Post and legacy-resume cases inline in the existing registered `tests/speckit-pro/unit/test-autopilot-phase-coverage.py`; then align `POST_STEPS` in `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`, both host skill/list guidance, and `speckit-pro/skills/speckit-coach/templates/workflow-template.md`. Prove GREEN, refresh C1a1 outputs, run targeted/quick suites, and record C1a1 path/production/LOC, host parity, and marker checkpoint (FR-017, FR-026).

## Phase 12: User Story 10 — complete Post and teams (P1, C1a2 then C1b1/C1b2)

**Goal**: Full completion has a verified Post state and no active executor team. **Independent test**: both persisted records reject missing/duplicate/pending/in-progress/mismatch/unjustified skips; only validated extension absence permits identical skip, and each team-capable executor proves cleanup (FR-018–019, FR-026).

- [ ] T018 [US10] Add RED persisted workflow/state completion cases in the `tests/speckit-pro/unit/test-autopilot-phase-coverage.py` for missing/duplicate/pending/in-progress/mismatch/skips/legacy resume; require exactly thirteen matching canonical rows (workflow Complete/state completed); only identical reason-coded skips for optional extensions absent from supported registries and directories qualify; preserve unique exact-name legacy progress, initialize missing/renamed rows pending, staged returns never claim full Post completion; then repair the guard and both host completion call sites and post references. Prove GREEN, refresh C1a2 outputs, run targeted/quick suites, and record C1a2 budget/marker checkpoint before T019 (FR-018, FR-026).
- [ ] T019 [US10] Add failing RED structural/result cases in `tests/speckit-pro/layer1-structural/test-phase-analyze-teardown.py` for Claude and Codex `phase-executor` and `analyze-executor`; require child result or supported stop, graceful shutdown, no-active-child, and completed-cleanup evidence in those four exact agent definitions plus shared agent-team reference. Register the structural test, prove GREEN, refresh C1b1 outputs, run targeted/quick suites, and record C1b1 budget/marker checkpoint (FR-019, FR-026).
- [ ] T020 [US10] Add failing RED structural/result cases in `tests/speckit-pro/layer1-structural/test-checklist-implement-teardown.py` for Claude and Codex `checklist-executor` and `implement-executor`; apply the same teardown result contract to those four exact definitions and shared agent-team reference. Register this distinct structural test, prove GREEN without claiming runtime child-lifetime/cleanup qualification (HRNS-017); review the formal lifecycle Post subset read-only and re-inventory before any new lifecycle edit (FR-019, FR-026).
- [ ] T021 [US10] Refresh C1b2 outputs from `speckit-pro/codex-agents/checklist-executor.toml`, its paired host definition and the exact C1b2 inventory, run its structural cases and quick suite, and record all eight definitions’ GREEN evidence plus C1b2 actual paths/LOC, host parity, and marker checkpoint; stop before PR emission on any new path or failed gate (FR-019, FR-026).

## Phase 13: User Story 11 — complete review feedback after push (P1, Increment C2a1)

**Goal**: Resolve-pr exhausts pages and acts only on a verified matching remote head. **Independent test**: >100 threads/comments, failed page/cursor, failed verify/push/head match, and serial confirmed resolution cases (FR-020–021, FR-026).

- [ ] T022 [US11] Add RED multi-page thread/comment and failed-page/cursor cases, then specify independent complete GraphQL reviewThreads and each comments cursor traversal; failed requests/incomplete connections/missing continuation cursors block mutations in both resolve-pr host skills and `tests/speckit-pro/unit/test-resolve-pr-protocol.py`; prove GREEN (FR-020, FR-026).
- [ ] T023 [US11] Add RED verification, push, fresh `headRefOid`, retry, serial reply/resolve, and resolved-readback cases, then enforce verify → commit → push → fresh remote SHA match → serial reply/resolve with readback; failed verify prevents push, failed push/query/mismatch leaves threads pending and identifies retained local commit; retry verifies again before publication in both resolve-pr host skills and the same test; prove GREEN, register the test, refresh C2a1 outputs, run targeted/quick suites, and record C2a1 budget/marker checkpoint (FR-021, FR-026).

## Phase 14: User Story 12 — wait for blind-spot result (P1, Increment C2a2)

**Goal**: A late nonempty analyst result is used. **Independent test**: >5-minute result is `ran`; dispatch error, empty return, and explicit operator abandonment record distinct matching header/status reasons (FR-022–023, FR-026).

- [ ] T024 [US12] Add RED late-result and three no-findings cases (dispatch error/empty return/explicit operator abandonment; elapsed silence is not abandonment), then remove the fixed blind-spot wait and persist matching distinct **Blind-spot pass:** header/operator-status reasons; any late nonempty summary is recorded as ran; update both scaffold host skills and `tests/speckit-pro/unit/test-scaffold-blindspot.py`; prove GREEN, register the test, refresh C2a2 outputs, run targeted/quick suites, and record C2a2 budget/marker checkpoint (FR-022, FR-023, FR-026).

## Phase 15: User Story 13 — complete named helper requests (P2, C2a3 then C2b1)

**Goal**: Five named failure sites carry accepted full envelopes on both hosts. **Independent test**: status index/topology, scaffold reviewability/placement, and phase index-write examples all pass registry validation (FR-024, FR-026).

- [ ] T025 [US13] Add RED status index/topology envelope cases, then provide complete accepted examples in both status host skills and `tests/speckit-pro/unit/test-status-envelope-contract.py`; require each documented inline request envelope to match a passing fixture byte for byte; prove GREEN, register the test, refresh C2a3 outputs, run targeted/quick suites, and record C2a3 budget/marker checkpoint (FR-024, FR-026).
- [ ] T026 [US13] Add RED scaffold reviewability/placement envelope cases, then repair both scaffold host examples and `tests/speckit-pro/unit/test-scaffold-envelope-contract.py`; require each documented inline request envelope to match a passing fixture byte for byte; prove GREEN (FR-024, FR-026).
- [ ] T027 [US13] Add RED phase index-write envelope cases, then repair both phase-execution host references and `tests/speckit-pro/unit/test-phase-envelope-contract.py`; require each documented inline request envelope to match a passing fixture byte for byte; prove GREEN, register both tests, refresh C2b1 outputs, run targeted/quick suites, and record C2b1 budget/marker checkpoint (FR-024, FR-026).

## Phase 16: User Story 14 — real workflow links (P2, Increment C2b2)

**Goal**: Issue #638's generated link reaches scaffold output while valid legacy links survive. **Independent test**: new template, verified legacy target, and broken legacy target cases all resolve to real workflow files (FR-025–026).

- [ ] T028 [US14] Retain the #698 new-template links as GREEN compatibility baseline; add failing verified-legacy-target preservation and broken-target repair cases in `tests/speckit-pro/unit/test-roadmap-workflow-links.py` and `tests/speckit-pro/unit/fixtures/roadmap-workflow-links/cases.json`, freezing existing-roadmap prose under that fixture, and record RED for only the remaining legacy behavior (FR-025).
- [ ] T029 [US14] Repair broken existing links to the actual scaffold workflow output directory and preserve legacy links only when their targets exist in `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` and `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`; prove T028 GREEN without redoing the shipped new-template/README link fix, then qualify the sixteen-candidate C2b2 set (FR-025, FR-026).
- [ ] T030 [US14] Register `tests/speckit-pro/unit/test-roadmap-workflow-links.py` in `tests/speckit-pro/suite-manifest.json`, regenerate C2b2 dist/reference outputs, run targeted/quick suites, and record C2b2 actual path/LOC, host parity, and marker checkpoint in the slice inventory; stop on incomplete or over-limit diff (FR-025, FR-026).

## Phase 17: Polish and cross-cutting validation

**Goal**: Reconcile all eighteen increments with observable acceptance and required checks. **Independent check**: the active requirement/scenario/SC matrix names every result, including failures and unavailable evidence.

- [ ] T031 Run final acceptance, full CI, artifact, applicable docs/lint and exact title/release-note checks; reconcile all eighteen increment checkpoints in `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/slice-inventory.md` and `specs/hrns-015-autopilot-gate-pr-emission-repair/.process/task-execution.json`, covering 26 active FRs (FR-001–010, FR-014–029), all 37 scenarios and SC-001–011, host parity, strict budgets and non-goals/deferred HRNS-019/017. Record each unavailable or failed gate explicitly; no future diff is assumed (FR-026, FR-027).

## Dependencies and closed TDD units

T001 → T002 blocks every story. Approved order: A1a → A1b → A2 → A3 → B1a → B1b → B2b → B3a → B3b → C1a1 → C1a2 → C1b1 → C1b2 → C2a1 → C2a2 → C2a3 → C2b1 → C2b2; final T031 follows all increments. Every task depends on its immediate predecessor. Every increment is one adjacent closed TDD unit (one to three tasks), sharing its phase and capability group; setup/foundation/final validation are separate units. Do not dispatch a partial RED-only unit. The metadata sidecar declares exact candidate paths, including shared fixtures, generated inputs and process evidence; no broad dist or reference directory ownership is used.

No task is marked [P]: the ratified order and shared helper/test/manifest/generated/process ownership require sequential execution. For US1/US2/US3 the packet/helper fixtures overlap; US4/US5/US6/US7/US8 share read_only/trust and checkpoints; US9/US10 share Post/team references and generated inputs; US11/US12/US13/US14 share suite manifest/generated/process evidence. These are each story’s parallel-execution examples and their concrete ownership conflicts. Independent story tests above remain runnable without marking another story complete.

Historical shipped T012/T013 are retired, and the remaining tasks are renumbered contiguously: old T001–T011 retain IDs, old T014–T033 become current T012–T031. Every current ID has exactly one matching sidecar entry; old B2a has no current implementation task.

## Implementation strategy and acceptance coverage

MVP is US1 (A1a then A1b), after Setup/Foundation. Complete US2/A2 and US3/A3 next for HRNS-016’s packet dependency; continue in the approved order. Story priorities remain the spec’s priorities; P2 stories stay in the ratified chain. Both host versions of every behavior are one task group. Required checks are planned implementation work, not checks executed during Tasks generation.

| Story | Active requirement coverage | Acceptance scenarios | Closing increment |
| --- | --- | ---: | --- |
| US1 | FR-001–003, FR-026 | 3 | A1b |
| US2 | FR-004–005, FR-026–027 | 2 | A2 |
| US3 | FR-006, FR-026 | 3 | A3 |
| US4 | FR-007–008, FR-026 | 3 | B1a |
| US5 | FR-009–010, FR-026 | 3 | B1b |
| US6 | FR-014, FR-026, FR-028–029 | 3 | B2b |
| US7 | FR-015, FR-026 | 2 | B3a |
| US8 | FR-016, FR-026 | 2 | B3b |
| US9 | FR-017, FR-026 | 3 | C1a1 |
| US10 | FR-018–019, FR-026 | 3 | C1b2 |
| US11 | FR-020–021, FR-026 | 3 | C2a1 |
| US12 | FR-022–023, FR-026 | 2 | C2a2 |
| US13 | FR-024, FR-026 | 2 | C2b1 |
| US14 | FR-025, FR-026 | 3 | C2b2 |

Acceptance scenario counts above total 37; preserve each spec scenario in the story’s failing fixture and result mapping. SC-001/SC-011 cover A; SC-002–004 cover B; SC-005–006 cover C1; SC-007–009 cover C2; SC-010 covers every budget/host-parity checkpoint. FR-027 cross-cutting PRD/roadmap edits close in A2 and are reconciled in final T031. Removed FR-011–013 are historical compatibility provenance, not active acceptance scope.

The quick suite is python3 tests/speckit-pro/run-all.py; FULL_VERIFY discovery was mypy . && ruff check && python3 tests/speckit-pro/run-all.py, but the repository’s pinned scripts/run-python-lint.py environment is required for lint/type checks. No arbitrary mypy sweep or tool installation is authorized by this task file. Build/integration and four quality slots are currently N/A; preserve threshold authority15/30/60. Required CI/artifact/docs/PR-title/release-note checks remain explicit final acceptance gates. The formal model is disabled; the lifecycle subset is reviewed read-only, with a new path requiring re-inventory before any edit.

Non-goal checkpoint applies to every unit: stop and flag a 58-site sweep/self-describing-error redesign, agent-doc-table parsing, new exception class, host ignore rules, removal of Agent/SendMessage, draft release-note fence, or packet-schema changes beyond optional release_note. Broad child lifetime qualification remains HRNS-017; broad helper sweep remains HRNS-019. Prose/structural fixtures never claim live runtime cleanup or unperformed official API qualification.

## Execution metadata

The .process/task-execution.json sidecar is schema_version task-execution.v1. Its native validate-task-execution fingerprints bind current spec, Plan and task definitions, excluding completion checkboxes. Entries cover every task exactly, with capability_group, depends_on, exact owns and tdd_unit. Any changed definition requires native fingerprint regeneration and validation before implementation; checked tasks additionally require parent-reconciled completion evidence. No implementation result or completion journal is created by Tasks.
