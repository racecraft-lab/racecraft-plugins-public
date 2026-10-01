# Implementation Plan: Autopilot, Gate, and PR-Emission Repair

**Branch**: `hrns-015-autopilot-gate-pr-emission-repair` | **Date**: 2026-09-27 | **Spec**: [spec.md](spec.md)

**Input**: The exact Phase 3 Plan Prompt in [HRNS-015-workflow.md](../../docs/ai/specs/.process/HRNS-015-workflow.md), the current spec, the design concept Q&A, the historical owner decision splitting C1 into C1a/C1b, and the subsequent explicit approval of eighteen delivery increments and the FR-024 sentence.

**Design status**: Plan artifacts reconciled together to the approved eighteen increments and installed 2.37.1 baseline. Planning G6 checks requirement coverage, task consistency, candidate budgets and a current planned marker record. The parent records the gate results; this document does not claim implementation or a gate pass.

## Summary

Design the remaining packet, gate, Post, executor, review-feedback, and scaffold repairs using the existing Python runner and paired Claude Code/Codex surfaces. Preserve 14 stories, 26 active functional requirements (29 historical IDs, with FR-011–FR-013 removed), 37 acceptance scenarios, and 11 success criteria. Every remaining behavior change begins with a failing fixture, and generated outputs follow their source in the same PR.

The owner has explicitly approved the **eighteen-part delivery direction**, preserving every active requirement and the strict per-PR budgets: **A1a → A1b → A2 → A3 → B1a → B1b → B2b → B3a → B3b → C1a1 → C1a2 → C1b1 → C1b2 → C2a1 → C2a2 → C2a3 → C2b1 → C2b2**. Original Q11's four slices and the later five-PR C1 split remain historical provenance; the new approval supersedes the delivery count. A/B/C1a/C1b/C2 remain scope families, with each approved increment a separate review PR. Already-shipped B2a leaves the former nineteen-part inventory. Candidate path arithmetic, including C2's six shipped link-only exclusions, remains planning evidence rather than measured implementation scope.

### Authority and rescope

| Record | Meaning at this Plan pass |
| --- | --- |
| Design Q11: "Four slices: A, B, C1, C2" | Original owner decision; retain its provenance. |
| Owner: split C1 into two PRs | Historical five-PR order A → B → C1a → C1b → C2; retained as provenance. |
| Previous nineteen increments | An unratified candidate allocation, not permission to change the approved PR count. |
| 2026-09-26 rescope | FR-011–FR-013/#637 are satisfied by #694; new-template links/#638 by #698; sequential repeated-path marker support by #676. These are explicit rescope inputs, not new behavior qualifications in this pass. |
| Current eighteen increments | Explicitly owner-approved direction omitting B2a and unnecessary new-template/README link repair; all active requirements and strict budgets preserved. |
| FR-024 contract sentence | Explicitly owner-approved: Each documented inline request envelope must match a passing fixture byte for byte. |

Installed runtime 2.37.1 is the owner-confirmed execution baseline, with `main` merged at `48264ea0d`. Current owner instructions establish #740 and #733 as resolved own-run blockers and authorize a fresh correction allowance through `execution-control` action `begin-replan-epoch`, preserving the existing run and ledger history. Historical claims that every own-run hazard persists, the marker validator still rejects sequential reuse, or the plugin must remain pre-fix are obsolete. Current native setup passed; the documentation broker remains rate-limited as recorded in [research.md](research.md). This reconciliation is not independent runtime qualification of all feature behavior.

## Technical Context

- **Language/Version**: Python 3.11+ standard library for runner and repository tooling; Markdown for host skills/Claude agents and TOML for Codex agents.
- **Primary Dependencies**: Existing Git, GitHub CLI integration, runner request contracts and repository test harness. No new runtime dependency or service.
- **Storage**: Existing Git-tracked Markdown/JSON, quality configuration, packet artifacts, and persisted workflow/state. Sensitive live execution records remain private; publish portable receipts only.
- **Testing**: Red-first Layer 4 fixtures, Layer 1 host/schema/template contracts, Layer 5 tool scoping where applicable, Layer 7 parity, quick and CI suites, generated checks, pinned ruff/mypy environment and relevant docs checks.
- **Target Platform**: Claude Code and Codex on the repository's supported desktop/CI environments; existing GitHub GraphQL integration for review feedback.
- **Project Type**: Plugin instruction surfaces plus deterministic runner and repository utilities.
- **Performance Goals**: Await native results without a fixed wall-clock cap; paginate bounded connections completely; preserve deterministic local validation.
- **Constraints**: ≤4 production and ≤24 total changed paths per eventual PR, both hosts together, generated paths counted; no Bash/jq dependency, manual generated edit, new exception class, draft release-note fence, or runtime fixture read of a temporary feature spec.
- **Scale/Scope**: 14 stories / 26 active FRs. HRNS-019 owns the broad envelope sweep; HRNS-017 owns unverified host child-lifetime behavior.
- **Primary review surface**: harness/adapter. Secondary surfaces: schema/config and docs/process. Per-increment surface coherence still requires qualification.
- **Reviewability Budget**: Candidate path evidence below; reviewable LOC and exact base/head diffs are not measured. The preset's ordinary LOC/surface limits also remain in force; this feature's stricter path caps do not replace them.

### Historical five-group budget evidence

The counts below are unique unions of the existing path inventory's candidate rows, omitting B2a. Production is the inventory's code/schema/active-config class, including Codex TOML. Generated payload, runner trust, docs reference and recurring process/evidence paths are included. These are conservative candidate sets, not proven changed-file minimums or measured diff passes.

| Historical group | Production candidates | Total candidates | Projected reviewable LOC | Against ≤4/≤24 paths |
| --- | ---: | ---: | --- | --- |
| A — packet and body | 4 | 39 | Not estimated for current remaining scope | Total over cap by 15 |
| B — gates/index/commands | 3 | 36 | Not estimated for current remaining scope | Total over cap by 12 |
| C1a — Post/completion | 1 | 29 | Not estimated for current remaining scope | Total over cap by 5 |
| C1b — executor teardown | 4 | 30 | Not estimated for current remaining scope | Total over cap by 6 |
| C2 — feedback/scaffold/envelopes/legacy links | 0 | 34 | Not estimated for current remaining scope | Total over cap by 10 |

C2's stored union is 40; removing the six already-shipped link-only README/template source/payload candidates yields 34. The roadmap template remains a B dependency for slice-budget syntax. The inventory itself is stale and must be reconciled to the approved eighteen-part direction during Tasks. The six recurring candidates are the bound workflow, state, tasks, task sidecar, inventory and generated feature SPEC-MOC; their actual changes must be proven in each diff rather than assumed from membership.

**Delivery approval recorded**: The owner approved the eighteen-part direction below and the exact FR-024 sentence. The delivery decision is resolved. This approval does not waive caps, omit a host, hide generated paths, reset execution budgets, drop requirements or qualify actual diff/LOC/marker evidence. This remains a Plan-stage pass.

### Eighteen approved increments — candidate sizing only

| Scope family | Approved increment/story | Production candidates | Stored candidate total |
| --- | --- | ---: | ---: |
| A | A1a / US1 note renderer-schema | 2 | 23 |
| A | A1b / US1 editable note validation | 2 | 23 |
| A | A2 / US2 current-packet guard | 1 | 22 |
| A | A3 / US3 current verdict | 2 | 23 |
| B | B1a / US4 marker visibility | 1 | 22 |
| B | B1b / US5 tracked index-refresh | 2 | 23 |
| B | B2b / US6 split/greenfield budgets | 1 | 23 |
| B | B3a / US7 refactor estimate | 1 | 18 |
| B | B3b / US8 declared commands | 3 | 24 |
| C1a | C1a1 / US9 Post names | 1 | 24 |
| C1a | C1a2 / US10 completion boundary | 1 | 18 |
| C1b | C1b1 / US10 phase/analyze teardown | 2 | 21 |
| C1b | C1b2 / US10 checklist/implement teardown | 2 | 21 |
| C2 | C2a1 / US11 review feedback | 0 | 13 |
| C2 | C2a2 / US12 blind-spot wait | 0 | 13 |
| C2 | C2a3 / US13 status envelopes | 0 | 13 |
| C2 | C2b1 / US13 scaffold/phase envelopes | 0 | 18 |
| C2 | C2b2 / US14 existing legacy links | 0 | 15 |

Each count comes from the existing [candidate inventory](.process/slice-inventory.md); none is an actual scope/LOC qualification. A1a plans the protected-note checkpoint and A1b completes editable validation; the final FR-002 contract is not claimed at the first checkpoint. Repeated story parts use unique marker IDs and current sequential-reuse rules. Planning records candidate paths and pending checkpoints; actual base/head diffs and required checkpoint evidence are collected before each PR emission. An approved allocation that fits candidate path estimates can still fail actual LOC, surface, checkpoint, fingerprint or hazard validation.

### Estimate reconciliation

Q11's historical whole-feature 1,362 LOC and A 282 + B 410 + C1 335 + C2 415 = 1,442 LOC came from different scopes/signals; the 80-LOC difference is not a measured refactor weight. Later C1a 520 / C1b 460 projections and the old 1,932-LOC output are also historical. The old 77 file-touch input double-counted repeated slice paths and cannot be a current unique inventory. Do not present any of these as a current per-PR LOC pass. The parent runs the current Plan advisory estimator after G3; Tasks then reconciles the inventory and records fresh route/layer decisions. The refactor-inclusive estimate stays explicitly unqualified until the input and implementation contract are validated.

## Planning and PR-Emission Evidence

The approved G6 timing is: **planning validates requirement coverage, task consistency, candidate budgets, and a current planned marker record; actual per-PR diffs, LOC, and checkpoint evidence stay mandatory before PR emission.** All eighteen approved increments and their strict budgets remain in scope.

The pre-implementation record is `pr-marker-plan.v1`. The parent persists and validates its current requirement/task mappings, ordered story-part identities and candidate file/budget records after Tasks. Every `implementation_checkpoint` is exactly `{"status": "pending"}`, with no commit or evidence fields. A pending checkpoint is a planned boundary and supplies no implementation completion proof.

Before each PR emission, existing marker/emission validation requires actual base/head changed paths, reviewable LOC, production/total counts and passing checkpoint evidence. Repeated production paths are measured separately in each actual diff; candidate membership cannot supply that proof. Missing required planning evidence blocks planning; missing required implementation/emission evidence blocks emission.


Current-source reconciliation after the main merge: packet behavior now lives in `helpers/pr_packet.py`; canonical packet path shapes live in `pr_contract.py`. Shared skill host blocks replace removed Codex overlays, and Codex agent TOMLs are regenerated from authored agent Markdown. Current candidate tables below deduplicate those shared sources. Recorded historical source/checkpoint counts and evidence files are preserved; final PR base/head measurements remain required. B3b extends `quality_gates.py` plus its existing read-only adapter and retains the default configuration unchanged. Mechanical merge path reanchoring is recorded separately from the eighteen behavior checkpoints.

## Module and Interface Deltas

### Slice A — packet and body

- `helpers/pr_packet.py` — changed: one optional nonblank unfenced `release_note`, final rendering and a protected current Phase 6.5 Verdict under Verification, including refresh.
- `skills/speckit-autopilot/contracts/pr-packet.schema.json` — changed: optional note and conditional fourth final editable field under the existing closed schema; drafts keep zero fields. This is the repository's packet-schema source path, correcting the old design concept location without changing scope.
- `helpers/read_only.py` — changed: exact release-note structure and protected fingerprint boundaries.
- `helpers/mutation.py` — changed: packet validation/output exempt only the current packet's three canonical untracked paths; tracked or unrelated changes still block.
- Paired autopilot/Post host guidance — changed together with those behaviors. Packet source, host policy and provenance stay consistent.
- PRD and HRNS-015/019 roadmap entries — amend scope, acceptance and deferred ownership to the approved eighteen-part direction; retain genuine evidence limits.

### Slice B — gates, index, estimate and commands

- `helpers/read_only.py` — changed: comma-token Gap matching plus shared code visibility for clarification counts/details; tracked-only spec index; complete split budget aggregation and LOC-only greenfield allowance; required-refactor estimate; quality-slot adapter. `quality_gates.py` owns declaration validation and resolution; default configuration values remain unchanged.
- Named-entry selection, selected pragma and missing-budget blocking — **baseline, not new work** after #694. Keep compatibility fixtures; do not manufacture pre-fix failure for shipped behavior or require a registry edit solely for removed FR-011–FR-013.
- `scripts/refresh-release-artifacts.py` — changed: existing index generator joins plain refresh and isolated check; check names stale tracked index paths. Existing required artifact-consistency job remains the CI owner.
- `quality_gates.py` — validates optional declared commands; the default `.specify/quality-gates.json` stays unchanged; preserve approved complexity15, CRAP30, mutation floor60, thresholds and basis. Do not map general lint commands into unrelated quality slots.
- Roadmap template — changed for ordered Slices/Slice Budgets syntax without literal accepted exception pragmas; its new-template workflow links are already shipped and stay baseline.
- Both hosts' gate/prerequisite guidance and root `AGENTS.md` — align with real counters, command precedence and index refresh. `specs/formal-001-selective-formal-methods/SPEC-MOC.md` is regenerated, not authored by hand.

### Slice C1a — Post list and completion

- Existing phase-coverage script — changed to the requested canonical13 `POST_STEPS` and full completion-boundary rule over persisted workflow/state, distinct from ordinary status-evidence validation.
- Both hosts' autopilot, canonical task list, Post guidance and workflow template — align names/order/counts and invoke the full boundary at actual full-run success.
- `formal/lifecycle.py` — read-only compatibility review required; a discovered necessary edit adds a path and requires remeasurement. No formal model is selected for this run.
- Existing registered phase-coverage test — add red-first completion/list/resume cases; do not infer missing rows completed.

### Slice C1b — executor teardown

- Four Claude executor Markdown definitions and four Codex TOML twins — paired child-result or supported-stop, graceful shutdown, no-active-child/cleanup evidence and unresolved-result reporting obligations.
- Shared agent-team guidance — align with actual host operations. Unsupported teardown confirmation remains unresolved; absence of a close operation must not be replaced by a fabricated cleanup receipt.
- Structural coverage — distinct NEW Layer 1 tests cover the phase/analyze twins in C1b1 and checklist/implement twins in C1b2, retaining all eight definitions across the two increments. Each test file has one owning increment. Runtime lifecycle conclusions require actual host evidence; HRNS-017 retains the separate child-lifetime question.

### Slice C2 — feedback, scaffold, envelopes and legacy links

- Both resolve-pr skills — independently paginate thread and comment connections; fixes → full verify → commit → push → fresh matching PR head → serial reply/resolve/readback. Failures retain local commits and unresolved threads as specified.
- Both scaffold skills — await actual analyst result without a fixed deadline; distinct dispatch-error/empty-return/explicit-abandonment reasons in the existing Design Concept line and operator status.
- Both status skills plus named scaffold/phase examples — complete tested registered request envelopes only at the five specified failure sites; HRNS-019 owns the broader sweep. Each documented inline request envelope must match a passing fixture byte for byte.
- Existing-roadmap updates — preserve verified legacy targets and repair broken ones to actual scaffold output. New-template `.process/` links and README guidance are already baseline from #698; remove their redundant repair operations.

All helper paths above are under `speckit-pro/speckit_pro_runner/`; skill paths are under `speckit-pro/`. Authored source and host twins produce `dist/**`, runner trust files and relevant docs-reference output. Generated paths remain counted and regenerated. `.github/workflows/pr-checks.yml`, unrelated packet fields, draft emission and multi-pr-emission remain unchanged grey boxes.

## Declared File Operations

These authored candidate operations are the estimator input for the remaining behavior design; they are not a final changed-file manifest. Generated fan-out and recurring evidence are counted separately in the inventory/table above. Tasks must reconcile this list to the approved direction and current-source review; a nonexistent planned fixture is not a test already run.

- MODIFIED AGENTS.md
- MODIFIED docs/ai/specs/harness-engineering-uplift-technical-roadmap.md
- MODIFIED docs/prd-harness-engineering-uplift.md
- MODIFIED scripts/refresh-release-artifacts.py
- MODIFIED speckit-pro/agents/analyze-executor.md
- MODIFIED speckit-pro/agents/checklist-executor.md
- MODIFIED speckit-pro/agents/implement-executor.md
- MODIFIED speckit-pro/agents/phase-executor.md
- MODIFIED speckit-pro/skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/phase-execution.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/post-implementation.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md
- MODIFIED speckit-pro/skills/speckit-resolve-pr/SKILL.md
- MODIFIED speckit-pro/skills/speckit-scaffold-spec/SKILL.md
- MODIFIED speckit-pro/skills/speckit-status/SKILL.md
- MODIFIED speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json
- MODIFIED speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/gate-validation.md
- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py
- MODIFIED speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md
- MODIFIED speckit-pro/skills/speckit-coach/templates/workflow-template.md
- MODIFIED speckit-pro/speckit_pro_runner/helpers/mutation.py
- MODIFIED speckit-pro/speckit_pro_runner/helpers/pr_packet.py
- MODIFIED speckit-pro/speckit_pro_runner/pr_contract.py
- MODIFIED speckit-pro/speckit_pro_runner/quality_gates.py
- MODIFIED speckit-pro/speckit_pro_runner/contracts/quality-gates.schema.json
- MODIFIED speckit-pro/speckit_pro_runner/helpers/read_only.py
- NEW tests/speckit-pro/layer1-structural/test-phase-analyze-teardown.py
- NEW tests/speckit-pro/layer1-structural/test-checklist-implement-teardown.py
- MODIFIED tests/speckit-pro/suite-manifest.json
- NEW tests/speckit-pro/unit/fixtures/marker-visibility/cases.json
- NEW tests/speckit-pro/unit/fixtures/pr-packet-repair/packet-only-untracked.json
- NEW tests/speckit-pro/unit/fixtures/roadmap-workflow-links/cases.json
- NEW tests/speckit-pro/unit/fixtures/spec-index-freshness/historical-stale-index.md
- MODIFIED tests/speckit-pro/unit/test-autopilot-phase-coverage.py
- NEW tests/speckit-pro/unit/test-declared-quality-commands.py
- NEW tests/speckit-pro/unit/test-marker-visibility.py
- NEW tests/speckit-pro/unit/test-phase-envelope-contract.py
- NEW tests/speckit-pro/unit/test-resolve-pr-protocol.py
- NEW tests/speckit-pro/unit/test-roadmap-workflow-links.py
- NEW tests/speckit-pro/unit/test-scaffold-blindspot.py
- NEW tests/speckit-pro/unit/test-scaffold-envelope-contract.py
- NEW tests/speckit-pro/unit/test-size-estimate-refactors.py
- NEW tests/speckit-pro/unit/test-spec-index-freshness.py
- MODIFIED tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py
- MODIFIED tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py
- NEW tests/speckit-pro/unit/test-status-envelope-contract.py

## Constitution Check

*Evaluate before research and again after design; the parent owns the programmatic gates.*

| Principle | Before Phase 0 research | After Phase 1 design |
| --- | --- | --- |
| I Plugin structure | Use existing runner/host/agent locations. | No new plugin or source layout. |
| II Runtime safety | Shipped code and default suite remain Python 3.11+ stdlib; vendored setup is not release proof. | Structured request/JSON/path handling; no active Bash/jq dependency added. Pinned dev-only lint environments follow constitution 2.1.0. |
| III Versioning | Release-please owns versions. | No manual version/manifest change planned. |
| IV Coverage | Red-first registered fixtures and full checks required. | Guide identifies existing entrypoints and later fixture work; no tests claimed run. |
| V Commits/PRs | Existing exact-title/release-note gates. | Validated packet is body source; no skip-label workaround. |
| VI Simplicity | Extend existing mechanisms only. | No new runtime framework or speculative abstraction. |
| VII Generated artifacts | Refresh from source, include fan-out. | Generated files counted per eventual diff, never hand-edited. |
| VIII Host parity | Each behavior reaches both hosts in one PR. | Paired skill/agent scopes retained. |
| IX Fail closed | Missing evidence required at the current boundary is failure/unknown. | Delivery authority is approved. Planning checks coverage, task consistency, candidate budgets and the current planned marker record; actual diff/LOC/checkpoint proof is required before emission. |
| X Privacy | Private execution records outside working tree. | Portable receipts only; no local identities in published artifacts. |

**Reviewability exception**: None approved. The historical five-group candidate unions exceeded the strict path cap and motivated the now-approved eighteen-part split. The delivery decision is resolved; the approval preserves the caps. All eighteen candidate sets fit the strict path caps; planning also requires the current planned marker record. Actual per-increment scope/LOC/checkpoint qualification remains pending until implementation and is mandatory before emission. The separately approved FR-024 sentence does not waive any reviewability requirement.

## Project Structure

~~~text
specs/hrns-015-autopilot-gate-pr-emission-repair/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/{runner-and-roadmap,workflow-and-pr}.md
├── tasks.md
└── .process/{slice-inventory.md,task-execution.json}
speckit-pro/
├── speckit_pro_runner/helpers/{pr_packet,read_only,mutation,registry}.py
├── speckit_pro_runner/{pr_contract,quality_gates}.py
├── speckit_pro_runner/formal/lifecycle.py
├── skills/{speckit-autopilot,speckit-resolve-pr,speckit-scaffold-spec,speckit-status,speckit-coach}/
├── agents/{phase,analyze,checklist,implement}-executor.md
└── codex-agents/{phase,analyze,checklist,implement}-executor.toml (generated)
scripts/refresh-release-artifacts.py
tests/speckit-pro/{unit,layer1-structural,layer5-tool-scoping}/
~~~

**Structure decision**: Extend existing helpers, packet contracts and host mirrors. Existing docs generation, suite registration, runner trust and index generation remain the mechanisms used for delivery.

## Execution Design by Slice

1. **A**: Freeze note type/blank/fence-breaking/absence/draft cases, current-verdict creation/refresh failures and exact current-packet/unrelated/tracked/unreadable-status cases. Add optional schema/rendering then editable structure/fingerprint and packet guard. The supplied body's refresh cannot retain a stale protected Verdict. Final release-note policy uses the exact title and body.
2. **B**: Preserve green baseline #637 cases; start red only for split/aggregate/greenfield extensions. Include missing/extra/duplicate/placeholder/at-block rows, ordinary surface limits, multiple visible Gap tags and all code forms, tracked/staged versus untracked index candidates, stale index before/after refresh, per-slot declarations/invalid config and non-double-counted refactor signals. Freeze historical index text in test-owned fixtures.
3. **C1a**: Derive 13 names from POST_STEPS; test both persisted representations for every missing/duplicate/pending/in-progress/mismatch/unjustified skip. Only the same absent-extension reason can substitute for completion of a canonical optional extension row after registry and directory absence proof. Preserve unique exact-name legacy statuses; new/renamed rows start pending. Out-of-stage returns do not claim full Post completion.
4. **C1b**: Test the required return contract across all executor twins; a missing child result or supported stop/teardown confirmation prohibits clean completion. Consume actual child summaries and actual native command exits; host thread retention is not automatically evidence of active work or cleanup completion.
5. **C2**: Exercise >one thread/comment page, missing cursor/page failure, verify/push/head-query/mismatch failures, serial reply/resolve confirmation, late analyst results and all explicit no-findings reasons, complete five-site envelopes and existing verified/broken roadmap targets. Already-shipped link cases remain green compatibility coverage.

With delivery approval recorded, Tasks creates exact boundaries/ownership, reconciles the path inventory and task sidecar, and records fresh atomicity route and conditional layer plan. The parent then persists the current `pr-marker-plan.v1` with pending-only checkpoints. An advisory one-navigable-PR classification cannot override an approved PR split; do not reuse an old route as new proof. Planning G6 checks coverage, task consistency, candidate budgets and that current planned record. Each eventual increment needs targeted red/green, applicable suites/lint/docs/generated checks and actual base/head scope/LOC plus checkpoint evidence before emission. Required gate failures remain blocking; G6.5 advisory confidence is not a waiver of G6. No implementation begins in this `--stage plan` pass.

## PR Review Packet Source

For each approved increment, the validated packet supplies changed behavior/cause, non-goals, approved order, actual budget, requirement/file/fixture traceability, exact verification results, evidence gaps and rollback. Optional release_note rendering and protected current Verdict follow [workflow-and-pr.md](contracts/workflow-and-pr.md). Final title/body pass repository policy; draft or partial CI does not qualify implementation.

## Complexity Tracking

No constitution violation or budget exception is approved. The owner delivery decision is resolved. Constitution 2.1.0 was checked before research and after design; no new violation is introduced. Official documentation and independent source/fixture behavior qualification remain explicit limits; the prior independent artifact audit corroborated the unchanged candidate arithmetic. Actual scope/LOC/checkpoint evidence remains pending until implementation and mandatory before emission. Preserve run identity and consumed repair history; only the owner-approved `begin-replan-epoch` creates the fresh correction allowance, with no other ledger reset.

Operator-approved bounded allocation correction: B3b replaces the three gate-guidance paths with the quality-config schema and its two generated host copies; C1a1 owns the relocated guidance. This keeps the approved eighteen increments and strict 24-path cap. Scope, thresholds, basis, completed definitions and historical checkpoints stay intact.
