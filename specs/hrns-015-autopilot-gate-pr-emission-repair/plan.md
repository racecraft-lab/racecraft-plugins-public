# Implementation Plan: Autopilot, Gate, and PR-Emission Repair

**Branch**: `hrns-015-autopilot-gate-pr-emission-repair` | **Date**: 2026-09-25 | **Spec**: [spec.md](spec.md)

**Input**: The complete Phase 3 Plan Prompt in docs/ai/specs/.process/HRNS-015-workflow.md, the clarified spec, and the HRNS-015 design concept.

## Summary

Repair the observed packet, gate, Post, resolve-pr, and scaffold defects in five ordered review slices: A → B → C1a → C1b → C2. Each behavior starts with a failing fixture and reaches Claude Code and Codex in the same slice. The runner stays Python 3.11+ standard library; plugin host surfaces remain their existing Markdown/TOML formats. Source changes are refreshed into dist and generated reference pages rather than edited in generated output.

The whole feature exceeds one reviewable PR. The design concept's **preliminary four-slice** sum, **1,442 LOC** (282 + 410 + 335 + 415), is historical after the user ratified C1a/C1b. It is not a five-slice or refactor-inclusive estimate. The design concept's **1,362 LOC** was a separate whole-feature advisory estimate before C was split; its inputs and per-slice counts are not additive or directly comparable. The 80-LOC arithmetic difference is not evidence for a refactor weight or two extra files. The Plan-phase sizing check and its limitation are recorded below. Actual authored and generated diff counts are measured at each slice boundary. A/B/C2 already exceed the 24-path limit on task-derived lower bounds, so the five-slice allocation is blocked until another owner-ratified scope allocation meets the cap. C1a/C1b remain unmeasured and cannot absorb an unlisted path without reallocation.

## Technical Context

- **Language/Version**: Python 3.11+ for runner, validation, and repository tools; Markdown skills for Claude Code and Codex; Codex agent TOML.
- **Primary Dependencies**: Python standard library, Git, existing `gh` CLI integration, existing SpecKit runner and test harness. No new runtime package.
- **Storage**: Git-tracked roadmap/spec/workflow Markdown, `.specify/quality-gates.json`, PR packet JSON/Markdown, and local `autopilot-state.json`.
- **Testing**: Failing-first Layer 4 unit and Layer 1 structural fixtures, Layer 5 scoping when host tool prose changes, existing quick and CI suites, generated-artifact check, docs reference validation, ruff F and mypy ratchet.
- **Target Platform**: Claude Code and Codex plugin hosts on supported desktop/CI environments; GitHub PR API via the existing `gh api graphql` route.
- **Project Type**: Plugin skills and deterministic Python runner/repository tools.
- **Performance Goals**: No fixed blind-spot analyst deadline; bounded page size with complete cursor traversal; no regression to deterministic local gates.
- **Constraints**: No active Bash or jq dependency, no hand-edited generated payload/reference pages, no runtime test read of a temporary feature spec path, no new exception class, no draft release-note fence.
- **Scale/Scope**: 29 functional requirements, 14 user stories, 11 success criteria, five ordered review slices. HRNS-019 owns the broad helper-envelope sweep; HRNS-017 owns the unknown Codex child-lifetime behavior.
- **Primary review surface**: harness/adapter. Secondary surfaces: schema/config and docs/process.

### Reviewability budget and slice decision

The table is an authored-file projection, including host instructions, schemas/config, tests, and expected documentation changes. Generated dist/reference/index files count in the actual final diff gate; the projected total is provisional until those outputs are refreshed. “Production” here means changed Python code, schema, or active config; both host instruction files count toward total files. The stricter delivery limits are **at most four production files and fewer than 25 total files per slice**.

| Slice | Primary production files | Production count | Projected reviewable LOC | Projected total files | Budget result |
| --- | --- | ---: | ---: | ---: | --- |
| A — packet and PR emission | `pr_emission.py`, `read_only.py`, `mutation.py`, PR packet schema | 4 | 282 historical | ≥31 required paths | Blocks 24-path cap; full inventory/LOC missing |
| B — gates and counters | `read_only.py`, `registry.py`, `refresh-release-artifacts.py`, quality-gates config | 4 | 410 historical | ≥28 required paths | Blocks 24-path cap; full inventory/LOC missing |
| C1a — Post list and completion | phase coverage guard | 1 | 520 legacy advisory (`warn`) | 24 reserved paths | Planned cap met; actual LOC/diff unmeasured |
| C1b — executor teardown | four Codex agent TOML configs; four Claude agent instructions also counted in total paths | 4 | 460 legacy advisory (`warn`) | 22 reserved paths | Planned cap met; actual LOC/diff unmeasured |
| C2 — resolve-pr and scaffold | no Python/schema/config production file planned; paired host skills and roadmap template | 0 provisional | 415 historical | ≥30 required paths | Blocks 24-path cap; full inventory/LOC missing |

Design-concept revision note: Q11 originally ratified four slices, but the post-Tasks inventory proved at least 29 C1 paths against the 24-path maximum. The user subsequently ratified five PRs, splitting C1 into Post completion (C1a) and executor teardown (C1b). [slice-inventory.md](.process/slice-inventory.md) gives complete planned path operations: C1a reserves 10 authored, 12 dist, and 2 reference paths; C1b reserves 11 authored, 10 dist, and 1 reference path. This revises delivery allocation only; FR-017–019 retain their outcomes. Both 520/460 LOC figures are outputs of the installed legacy `estimate-spec-size` on 24/22 planned paths (`modify`, C1a 2 story signals/2 FR signals, C1b 1/1); each is `warn` with two suggested slices and excludes unmeasured required refactors. Neither is an actual LOC pass. The old A/B/C2 totals of 16/19/18 omitted generated fan-out and are superseded by task-derived **lower bounds** of at least 31/28/30 required paths, detailed in the inventory. A/B/C2 remain blocked: their fixture-directory contents, generated reference changes, distinct refactor files, and actual LOC are not yet enumerated or measured. The ten-name Slice A subset below is historical and is not a complete estimator input. Every eventual diff, including generated output, determines the gate. Every slice has one primary surface; secondary schema/config and docs/process changes support that surface. The five PRs are ordered A, B, C1a, C1b, C2 using a current `pr_marker_plan` after source/hazard validation; the advisory `one-navigable-PR` classifier is retained. Deferred scope is recorded against HRNS-019 and HRNS-017.

### Plan-phase size check

On 2026-09-25, the current `estimate_spec_size` helper was called with `user_stories=14`, `frs=29`, `files=77` (the **sum of superseded provisional slice file-touch projections** 16+19+24+18, including repeat touches), `new_vs_modify=modify`, and no spike. It returned `estimated_loc=1932`, `suggested_slices=5`, `status=warn`. Passing `required_refactor_files=1` returned the **same** result, confirming that this installed helper does not yet represent the specified refactor input. The 77 touch count is not a unique-file inventory and this legacy output is a sizing stress check, not a refactor-inclusive budget or a replacement for the preliminary 1,442 LOC. **Full Plan-phase re-estimate including required refactors: not estimated** because the current helper ignores that input and the distinct required-refactor file count is unmeasured. During Tasks, identify actual files and distinct required-refactor work, then run the updated estimator and recalculate each slice; before each PR, measure the actual LOC and file diff. If the stricter slice limits fail, split or rescope before implementation completion.

## Module and Interface Deltas

### Slice A

- `speckit-pro/speckit_pro_runner/helpers/pr_emission.py` — changed: optional `release_note` input, one final-body editable section, and protected current Phase 6.5 verdict under Verification.
- `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json` — changed: one optional note property and fourth final editable field, preserving `additionalProperties: false` and zero draft fields.
- `speckit-pro/speckit_pro_runner/helpers/read_only.py` — changed: body structure and protected fingerprint accept only the specified final release-note section.
- `speckit-pro/speckit_pro_runner/helpers/mutation.py` — changed: both packet mutation paths exempt exactly the current packet's three canonical untracked files.
- Claude/Codex autopilot PR packet and Post guidance — changed together: validated packet body is the PR source; no instruction to commit ignored packet files or add ignore rules.
- `docs/prd-harness-engineering-uplift.md` and `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md` — changed: AC-16.2/16.5/16.8/16.10, **both the HRNS-015 and HRNS-019 roadmap entries** (five-slice ownership and deferred envelope sweep), Slice A, and the stale #642 status.

### Slice B

- `speckit-pro/speckit_pro_runner/helpers/read_only.py` — changed: exact comma-token Gap parser, shared Markdown code-visibility filter for Gap and clarification counts/details, tracked-only spec index, section-scoped reviewability, declared commands, and refactor-aware estimate.
- `speckit-pro/speckit_pro_runner/helpers/registry.py` — changed if required: `reviewability-gate` setup request requires `spec_id`; missing input is a request error.
- `scripts/refresh-release-artifacts.py` — changed: named spec-index refresh/check step after other generated metadata/payload/marketplace steps; check names drifted tracked index paths.
- `.specify/quality-gates.json` — changed: optional `commands` map limited to the four existing quality-gate slots, preserving approved thresholds and basis.
- `speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md` — changed: ordered Slices and Slice Budgets placeholders, without a literal exception pragma example.
- Both hosts' gate-validation/prerequisites instructions, root `AGENTS.md`, PRD and roadmap entry — changed to describe the actual counters, command precedence, and required artifact check.
- `specs/formal-001-selective-formal-methods/SPEC-MOC.md` — regenerated by the spec-index source step, never hand-edited.

### Slice C1a

- The existing phase-coverage guard gains 13 canonical `POST_STEPS` and a completion-boundary rule against persisted workflow and `autopilot-state.json`; `status-evidence` alone remains insufficient.
- Claude and Codex autopilot SKILL, task-list-canonical, and post-implementation instructions, plus the workflow template, are updated together. Gate-validation, phase-execution, and agent-teams-integration references are reviewed but not edited in C1a; any newly required edit must first fit a remeasured cap.
- One new Layer 4 unit module contains the failing-first cases without a separate fixture path; the suite manifest, both dist copies where applicable, and reserved generated `skills.md`/`scripts.md` reference pages are in the 24-path inventory.

### Slice C1b

- Four Claude Markdown and four Codex TOML executor definitions gain child result/stop and verified teardown obligations. The shared agent-teams-integration source is updated for both payloads.
- One new Layer 1 structural test contains the eight-definition cases without separate fixture paths. The suite manifest, eight executor payload paths, two shared-guidance payload paths, and reserved `agents.md` reference page are in the 22-path inventory. `formal/lifecycle.py` is reviewed read-only; editing it requires a fresh inventory.

### Slice C2

- `speckit-pro/skills/speckit-resolve-pr/SKILL.md` and its Codex mirror — changed: full thread and per-thread comment pagination, then verify → commit → push → fresh remote PR head comparison → serial reply and confirmed resolution.
- `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` and its Codex mirror — changed: await the analyst without a fixed timeout, record the durable Design Concept `Blind-spot pass` outcome/reason, pass `inputs.spec_id`, use full request envelopes, and preserve verified existing workflow links.
- `speckit-pro/skills/speckit-status/SKILL.md` and its Codex mirror — changed: complete `generate-spec-index-check` and `o5-topology` request envelopes.
- Both hosts' autopilot phase index-writing examples — changed with a tested full envelope.
- `speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md` — changed: new links target `docs/ai/specs/.process/<SPEC-ID>-workflow.md`; existing legacy links survive only when their actual target exists.
- `speckit-pro/README.md` — changed: workflow path guidance matches scaffold output.

For every slice, the affected test fixture envelopes live under `tests/speckit-pro/unit/fixtures/`, structural checks under `tests/speckit-pro/`, and generated `dist/**` plus `docs-site/src/content/docs/reference/**` follow their source changes. `.github/workflows/pr-checks.yml` is unchanged: the existing required artifact-consistency job runs the refreshed check. Packet schema properties besides the optional note, draft emission, and multi-pr emission remain unchanged.

## Known Slice A File Operations (partial; not estimator input)

These ten named operations are the currently identified source/document subset of Slice A's provisional 16-file total. The other six projected paths (fixtures, generated output, or support documentation) are not named yet, so this is **not** a complete `Declared File Operations` block and must not be used to claim a valid estimator result or a passing file budget. The plan-phase reviewability estimator should report `not_estimated` until Tasks supplies a complete per-slice operation list. Later slices likewise require their own complete inventories before a PR; combining five slices into one operation block would hide the split decision.

- MODIFIED speckit-pro/speckit_pro_runner/helpers/pr_emission.py
- MODIFIED speckit-pro/speckit_pro_runner/helpers/read_only.py
- MODIFIED speckit-pro/speckit_pro_runner/helpers/mutation.py
- MODIFIED speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json
- MODIFIED speckit-pro/skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/post-implementation.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md
- MODIFIED docs/prd-harness-engineering-uplift.md
- MODIFIED docs/ai/specs/harness-engineering-uplift-technical-roadmap.md

## Constitution Check

**Before Phase 0 — BLOCKED pending a further ratified scope allocation.** Existing plugin structure and manifest versioning remain intact; repository Python stays standard-library and no active Bash/jq is added; new deterministic helper behavior receives Layer 4 fixtures and host components Layer 1/5 coverage; conventional commit/PR-title gates apply at delivery; no new abstraction or plugin is introduced. The five-slice order is user-ratified, but A/B/C2 each exceed the 24-path block on known required paths (at least 31/28/30). Their historical LOC projections are not measured passes. No slice proceeds to behavior work until T001/T002 document a complete, compliant, ratified allocation. Typed `Reviewability-Exception` classes remain `refactor`, `infra`, and `upgrade`, with no automatic split exception.

**After Phase 1 design — conditional on the Tasks sizing checkpoint and per-slice diff gate.** The data model and contracts below preserve existing request/result envelopes and host parity. The API pagination behavior and explicit operator signal are pinned in [research.md](research.md); Codex post-parent child lifetime is deliberately outside scope and does not weaken the teardown result contract. The refactor-inclusive size estimate remains explicitly `not_estimated` on the installed helper; T001/T002 must resolve the A/B/C2 over-cap allocations and incomplete inventories, and the actual marker diff must close the remaining evidence gap before treating any budget as qualified. Before each PR, count actual authored and generated changed paths and reviewable LOC; if any slice reaches 25 total files, exceeds four production files, or crosses a block threshold, split/rescope before implementation completion.

## Project Structure

### Documentation for this feature

~~~text
specs/hrns-015-autopilot-gate-pr-emission-repair/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── runner-and-roadmap.md
│   └── workflow-and-pr.md
├── tasks.md                 # generated in the Tasks phase
└── .process/task-execution.json  # task definitions and source fingerprints
~~~

### Source and validation surfaces

~~~text
speckit-pro/
├── speckit_pro_runner/
│   ├── helpers/{pr_emission,read_only,mutation,registry}.py
│   └── formal/lifecycle.py
├── skills/{speckit-autopilot,speckit-resolve-pr,speckit-scaffold-spec,speckit-status,speckit-coach}/
├── codex-skills/{speckit-autopilot,speckit-resolve-pr,speckit-scaffold-spec,speckit-status}/
├── agents/{phase,analyze,checklist,implement}-executor.md
└── codex-agents/{phase,analyze,checklist,implement}-executor.toml
scripts/refresh-release-artifacts.py
tests/speckit-pro/{unit,layer1-structural,layer5-tool-scoping}/
docs/ai/specs/
docs/prd-harness-engineering-uplift.md
~~~

**Structure decision**: Extend the existing runner helpers and host skill mirrors. Keep packet/body parsing in existing helpers, the canonical Post list in its existing guard, and generated output in the existing refresh script. No new runtime package or service.

## Execution design by slice

1. **A — packet acceptance first.** Freeze failing cases for final note/fence/host policy, missing verdict, refresh of a stale supplied body, draft absence, packet-only untracked files, another packet, tracked modification, and unreadable Git status. Extend packet input/schema and renderer, then body structure/fingerprint and current-packet dirty guard. Keep the eight existing required headings, single UAT heading, and protected generated Verdict line. Update both host packet instructions together.
2. **B — gates and counters.** Freeze issue #637's original `multi`, `pragma`, and `nobudget` reproductions plus missing `spec_id`, selected authored section only, primary surfaces, greenfield LOC-only, complete ordered slices, and aggregate reporting. Add gap/clarification visibility cases, including two tags on a line and inline/fenced/indented code. Freeze untracked-in-tracked-directory and staged spec-index cases; regenerate ART-007 historical text under test fixtures, not from an active spec at runtime. Add declared-command precedence and refactor-signal cases. Change runner and refresh source, then both host instructions.
3. **C1a — Post and completion.** Freeze 13-row template/host mismatch and persisted workflow/state cases with missing, duplicate, pending, in-progress, mismatched, and unjustifiably skipped rows, including a legacy 11-row record whose new or renamed rows stay pending while unique exact-name statuses are preserved. Assert the workflow `✅ Complete` to state `completed` mapping and the sole optional-extension skip: both records use identical `skipped: <extension> not installed` only for a canonical extension-dependent row, and supported registry plus directory checks confirm absence. An out-of-stage skip reactivates as pending when its stage resumes. Build the new completion rule from `POST_STEPS` and call it on both hosts immediately before successful full-run return after Post; a staged-run return does not invoke the full Post completion boundary. Existing `status-evidence` remains a separate audit and cannot prove Post completion. The C1a marker checkpoint runs its unit test, registered suite, generated refresh/reference check, host parity, and actual LOC/path gate before C1b begins.
4. **C1b — executor teardown.** Freeze child result/stop and teardown evidence for all eight executor definitions; their clean completion requires confirmed cleanup. Review formal lifecycle's Post subset without an assumed edit. Run its structural test, registered suite, generated refresh/reference check, host parity, and actual LOC/path gate at the C1b marker checkpoint.
5. **C2 — feedback, scaffold, envelopes, links.** Freeze >100 thread, >100 comment, missing cursor, failed page, verification failure, push failure, mismatched fresh `headRefOid`, serial reply/resolve, and resolved-state confirmation. Use the existing GraphQL route and query the PR head again after push. Freeze late nonempty analyst and all three explicit no-findings reasons, with the existing Design Concept header line as durable record. Freeze full request envelopes at only the named failure sites. Reproduce issue #638's broken template link and test new `.process/` output, verified legacy target preservation, and broken legacy repair.

Each slice follows red fixture → minimal repair → targeted green test → quick suite → generated source refresh/check → applicable docs/lint/CI suite. PR packet traceability maps every story and success criterion to source, fixture, and result. The post-Tasks advisory `atomicity-route` result remains `one-navigable-PR` (`change-shape:modify-heavy`, `releasable: true`); the layer planner remains skipped because the classifier did not emit `split-PR`. The later user-ratified five-PR order is A→B→C1a→C1b→C2. The current supported multi-PR path is a top-level `pr_marker_plan` derived from these task boundaries, planned file/test scopes, reviewability evidence, and the recorded hazard route; it is mirrored in workflow/state and checked for source fingerprints, marker membership/order, checkpoint evidence, and unsafe folds before `multi-pr-emission`. Planning this route does not itself assert that marker state or five PRs have been emitted.

## PR review packet source

Each slice PR body is generated from its validated packet and records: changed behavior and cause, explicit non-goals, review order in the five-PR sequence, actual LOC/production/total-file budget, requirement-to-file and failing-first-fixture traceability, verification commands/results, known gaps (including unavailable external-doc lookup if still relevant), and rollback/flags. Slice A supplies the release-note fence through the packet input. The Phase 6.5 Verdict is a protected generated value from the workflow table, not the overview row or editable body. PR title and release-note policy are checked against the final exact title/body.

## Complexity Tracking

No constitution violation is approved. A slice that exceeds its actual gate is split or rescoped rather than explained away.
