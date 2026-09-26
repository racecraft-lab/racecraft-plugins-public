# Implementation Plan: Autopilot, Gate, and PR-Emission Repair

**Branch**: `hrns-015-autopilot-gate-pr-emission-repair` | **Date**: 2026-09-25 | **Spec**: [spec.md](spec.md)

**Input**: The complete Phase 3 Plan Prompt in docs/ai/specs/.process/HRNS-015-workflow.md, the clarified spec, and the HRNS-015 design concept.

## Summary

Repair the observed packet, gate, Post, resolve-pr, and scaffold defects in 19 ordered, single-story candidate review increments: A1a → A1b → A2 → A3 → B1a → B1b → B2a → B2b → B3a → B3b → C1a1 → C1a2 → C1b1 → C1b2 → C2a1 → C2a2 → C2a3 → C2b1 → C2b2. Repeated story identities represent sequential vertical behavior checkpoints. Every behavior starts with a failing acceptance case and reaches Claude Code and Codex in the same increment. The runner stays Python 3.11+ standard library; generated dist and reference pages follow their source changes.

The design concept’s preliminary four-slice 1,442-LOC sum and later five-slice C1a/C1b decision are historical planning evidence. The earlier eleven-increment allocation omitted recurring tracked workflow, state, task, evidence, and index paths and mixed story identities. The revised path ledger includes six recurring candidates in each increment. Its 14–24 candidate paths and 0–2 production paths per increment fit the planned cap; actual reviewable LOC, final diffs, marker fingerprints, and G6 are unqualified. The installed marker validator still rejects legitimate repeated paths across sequential markers, so no valid marker plan or PR emission is claimed.

## Technical Context

- **Language/Version**: Python 3.11+ for runner, validation, and repository tools; Markdown skills for Claude Code and Codex; Codex agent TOML.
- **Primary Dependencies**: Python standard library, Git, existing `gh` CLI integration, existing SpecKit runner and test harness. No new runtime package.
- **Storage**: Git-tracked roadmap/spec/workflow Markdown, `.specify/quality-gates.json`, PR packet JSON/Markdown, and local `autopilot-state.json`.
- **Testing**: Failing-first Layer 4 unit and Layer 1 structural fixtures, Layer 5 scoping when host tool prose changes, existing quick and CI suites, generated-artifact check, docs reference validation, ruff F and mypy ratchet.
- **Target Platform**: Claude Code and Codex plugin hosts on supported desktop/CI environments; GitHub PR API via the existing `gh api graphql` route.
- **Project Type**: Plugin skills and deterministic Python runner/repository tools.
- **Performance Goals**: No fixed blind-spot analyst deadline; bounded page size with complete cursor traversal; no regression to deterministic local gates.
- **Constraints**: No active Bash or jq dependency, no hand-edited generated payload/reference pages, no runtime test read of a temporary feature spec path, no new exception class, no draft release-note fence.
- **Scale/Scope**: 29 functional requirements, 14 user stories, 11 success criteria, 19 proposed review increments. HRNS-019 owns the broad helper-envelope sweep; HRNS-017 owns the unknown Codex child-lifetime behavior.
- **Primary review surface**: harness/adapter. Secondary surfaces: schema/config and docs/process.

### Reviewability budget and slice decision

For repeated stories, the current marker contract uses unique `usN-partK` IDs with `kind=user_story_part` and `parent_marker_id=usN`; unsplit stories use `kind=user_story` and `id=usN`. The proposed 19-increment allocation supersedes the original four/five-slice and eleven-increment candidates after counting all generated fan-out, six recurring tracked process/evidence paths, and one user-story identity per marker. The user’s directive preserves all 29 FRs, all 14 stories, the C1a/C1b distinction, and both host variants. [slice-inventory.md](.process/slice-inventory.md) is the path-by-path authority. The recurring paths are workflow, `autopilot-state.json`, `tasks.md`, `task-execution.json`, the slice inventory, and the HRNS-015 generated `SPEC-MOC.md` PR/index candidate. Reused registered unit modules keep A1, B2, and C1a within the cap while retaining RED/GREEN cases. The following are conservative candidates, not actual diff or reviewable-LOC passes.

| Proposed increment | Primary surface | Production paths | Candidate total | Budget evidence |
| --- | --- | ---: | ---: | --- |
| A1a | US1 optional note render/schema | 2 | 24 | Candidate only; actual LOC/diff unmeasured |
| A1b | US1 protected note validation | 2 | 24 | Candidate only; actual LOC/diff unmeasured |
| A2 | US2 packet guard and scope prose | 1 | 24 | Candidate only; actual LOC/diff unmeasured |
| A3 | US3 current verdict | 2 | 24 | Candidate only; actual LOC/diff unmeasured |
| B1a | US4 visible markers | 1 | 22 | Candidate only; actual LOC/diff unmeasured |
| B1b | US5 tracked spec index | 2 | 23 | Candidate only; actual LOC/diff unmeasured |
| B2a | US6 named entry/exception | 2 | 22 | Candidate only; actual LOC/diff unmeasured |
| B2b | US6 slice/greenfield budgets | 1 | 23 | Candidate only; actual LOC/diff unmeasured |
| B3a | US7 refactor estimate | 1 | 18 | Candidate only; actual LOC/diff unmeasured |
| B3b | US8 declared commands | 2 | 22 | Candidate only; actual LOC/diff unmeasured |
| C1a1 | US9 Post list | 1 | 24 | Candidate only; actual LOC/diff unmeasured |
| C1a2 | US10 completion boundary | 1 | 21 | Candidate only; actual LOC/diff unmeasured |
| C1b1 | US10 phase/analyze teardown | 2 | 21 | Candidate only; actual LOC/diff unmeasured |
| C1b2 | US10 checklist/implement teardown | 2 | 21 | Candidate only; actual LOC/diff unmeasured |
| C2a1 | US11 review feedback | 0 | 14 | Candidate only; actual LOC/diff unmeasured |
| C2a2 | US12 blind spot | 0 | 14 | Candidate only; actual LOC/diff unmeasured |
| C2a3 | US13 status envelopes | 0 | 14 | Candidate only; actual LOC/diff unmeasured |
| C2b1 | US13 scaffold/phase envelopes | 0 | 21 | Candidate only; actual LOC/diff unmeasured |
| C2b2 | US14 workflow links | 0 | 22 | Candidate only; actual LOC/diff unmeasured |

A1a emits a prefilled release note as protected content; A1b introduces the fourth editable marker pair and changes both renderer and fingerprint/structure validator. This preserves a passing intermediate packet without claiming the final editable contract early.

The per-PR limits remain at most four production Python/schema/active-config files and fewer than 25 changed paths, including generated output and process evidence. Q11’s 1,442/1,932-LOC totals are historical and not comparable to per-increment actual diffs. The installed estimator still ignores required-refactor input, so the full refactor-inclusive estimate is `not_estimated`; no distinct extra refactor path is presently named, and T016 confirms that during implementation. The advisory `atomicity-route=one-navigable-PR` is retained. The marker validator rejects legitimate repeated declarations; no current valid `pr_marker_plan`, G6 pass, or PR emission is claimed. If an actual changed path is missing or an increment reaches 25 paths, exceeds four production paths, or fails the LOC gate, stop and reallocate before its PR.

### Plan-phase size check

On 2026-09-25, the current `estimate_spec_size` helper was called with `user_stories=14`, `frs=29`, `files=77` (the **sum of superseded provisional slice file-touch projections** 16+19+24+18, including repeat touches), `new_vs_modify=modify`, and no spike. It returned `estimated_loc=1932`, `suggested_slices=5`, `status=warn`. Passing `required_refactor_files=1` returned the **same** result, confirming that this installed helper does not yet represent the specified refactor input. The 77 touch count is not a unique-file inventory and this legacy output is a sizing stress check, not a refactor-inclusive budget or a replacement for the preliminary 1,442 LOC. **Full Plan-phase re-estimate including required refactors: not estimated** because the current helper ignores that input and the distinct required-refactor file count is unmeasured. The named Tasks inventory identifies planned files and zero extra distinct refactor paths; T016 must confirm this after the helper repair. Before each PR, measure the actual LOC and file diff. If the stricter slice limits fail, split or rescope before implementation completion.

## Module and Interface Deltas

### Slice A1a/A1b/A2/A3

- `speckit-pro/speckit_pro_runner/helpers/pr_emission.py` — changed: optional `release_note` input, one final-body editable section, and protected current Phase 6.5 verdict under Verification.
- `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json` — changed: one optional note property and fourth final editable field, preserving `additionalProperties: false` and zero draft fields. The design concept names a runner/contracts location, but this is the verified repository source path; this is a path correction with no scope change.
- `speckit-pro/speckit_pro_runner/helpers/read_only.py` — changed: body structure and protected fingerprint accept only the specified final release-note section.
- `speckit-pro/speckit_pro_runner/helpers/mutation.py` — changed: both packet mutation paths exempt exactly the current packet's three canonical untracked files.
- Claude/Codex autopilot PR packet and Post guidance — changed together: validated packet body is the PR source; no instruction to commit ignored packet files or add ignore rules.
- `docs/prd-harness-engineering-uplift.md` and `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md` — changed: AC-16.2/16.5/16.8/16.10, **both the HRNS-015 and HRNS-019 roadmap entries** (19-increment proposal and deferred envelope sweep), A2, and the stale #642 status.

### Slice B1a/B1b/B2a/B2b/B3a/B3b

- `speckit-pro/speckit_pro_runner/helpers/read_only.py` — changed: exact comma-token Gap parser, shared Markdown code-visibility filter for Gap and clarification counts/details, tracked-only spec index, section-scoped reviewability, declared commands, and refactor-aware estimate.
- `speckit-pro/speckit_pro_runner/helpers/registry.py` — changed if required: `reviewability-gate` setup request requires `spec_id`; missing input is a request error.
- `scripts/refresh-release-artifacts.py` — changed: named spec-index refresh/check step after other generated metadata/payload/marketplace steps; check names drifted tracked index paths.
- `.specify/quality-gates.json` — changed: optional `commands` map limited to the four existing quality-gate slots, preserving approved thresholds and basis.
- `speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md` — changed: ordered Slices and Slice Budgets placeholders, without a literal exception pragma example.
- Both hosts' gate-validation/prerequisites instructions, root `AGENTS.md`, PRD and roadmap entry — changed to describe the actual counters, command precedence, and required artifact check.
- `specs/formal-001-selective-formal-methods/SPEC-MOC.md` — regenerated by the spec-index source step, never hand-edited.

### Slice C1a1/C1a2

- The existing phase-coverage guard gains 13 canonical `POST_STEPS` and a completion-boundary rule against persisted workflow and `autopilot-state.json`; `status-evidence` alone remains insufficient.
- Claude and Codex autopilot SKILL, task-list-canonical, and post-implementation instructions, plus the workflow template, are updated together. Gate-validation, phase-execution, and agent-teams-integration references are reviewed but not edited in C1a; any newly required edit must first fit a remeasured cap.
- The existing registered `test-autopilot-phase-coverage.py` gains inline RED/GREEN cases. C1a1 owns 24 conservative candidate paths for the list, and C1a2 owns 21 for the persisted completion boundary, each including the six process/evidence paths.

### Slice C1b1/C1b2

- Four Claude Markdown and four Codex TOML executor definitions gain child result/stop and verified teardown obligations. The shared agent-teams-integration source is updated for both payloads.
- One new Layer 1 structural test covers all eight definitions. C1b1 owns the Claude/Codex phase and analyze pairs; C1b2 owns checklist and implement pairs. Each has 21 conservative candidate paths, including generated agent/test references and six process/evidence paths. `formal/lifecycle.py` is reviewed read-only; editing it requires a fresh inventory.

### Slice C2a1/C2a2/C2a3/C2b1/C2b2

- `speckit-pro/skills/speckit-resolve-pr/SKILL.md` and its Codex mirror — changed: full thread and per-thread comment pagination, then verify → commit → push → fresh remote PR head comparison → serial reply and confirmed resolution.
- `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` and its Codex mirror — changed: await the analyst without a fixed timeout, record the durable Design Concept `Blind-spot pass` outcome/reason, pass `inputs.spec_id`, use full request envelopes, and preserve verified existing workflow links.
- `speckit-pro/skills/speckit-status/SKILL.md` and its Codex mirror — changed: complete `generate-spec-index-check` and `o5-topology` request envelopes.
- Both hosts' autopilot phase index-writing examples — changed with a tested full envelope.
- `speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md` — changed: new links target `docs/ai/specs/.process/<SPEC-ID>-workflow.md`; existing legacy links survive only when their actual target exists.
- `speckit-pro/README.md` — changed: workflow path guidance matches scaffold output.

For every slice, the affected test fixture envelopes live under `tests/speckit-pro/unit/fixtures/`, structural checks under `tests/speckit-pro/`, and generated `dist/**` plus `docs-site/src/content/docs/reference/**` follow their source changes. `.github/workflows/pr-checks.yml` is unchanged: the existing required artifact-consistency job runs the refreshed check. Packet schema properties besides the optional note, draft emission, and multi-pr emission remain unchanged.

## Historical Slice A File Operations (superseded; not estimator input)

These ten named operations were the initial A subset before generated fan-out was counted. The complete A1a/A1b/A2/A3 named candidate inventory is now in [slice-inventory.md](.process/slice-inventory.md). This historical list is not a declaration for the estimator or a passing budget.
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

**Before Phase 0 — planned path allocation revised; marker contract and measured gates remain blocked.** Existing plugin structure and manifest versioning remain intact; repository Python stays standard-library and no active Bash/jq is added; new deterministic helper behavior receives Layer 4 fixtures and host components Layer 1/5 coverage; conventional commit/PR-title gates apply at delivery; no new abstraction or plugin is introduced. The former five-slice order was user-ratified but A/B/C2 exceeded the 24-path cap. T001/T002 now document 19 named candidate sets within the cap; actual LOC/diff remains unmeasured and the marker validator cannot yet represent repeated shared paths. No marker emits until that contract and current per-increment gates pass. Typed `Reviewability-Exception` classes remain `refactor`, `infra`, and `upgrade`, with no automatic split exception.

**After Phase 1 design — conditional on the Tasks sizing checkpoint and per-slice diff gate.** The data model and contracts below preserve existing request/result envelopes and host parity. The API pagination behavior and explicit operator signal are pinned in [research.md](research.md); Codex post-parent child lifetime is deliberately outside scope and does not weaken the teardown result contract. The refactor-inclusive size estimate remains explicitly `not_estimated` on the installed helper; T001/T002 now provide 19 complete named candidate inventories; the current marker validator still rejects legitimate repeated paths, and each actual marker diff must close the remaining evidence gap before any budget is qualified. Before each PR, count actual authored and generated changed paths and reviewable LOC; if any increment reaches 25 total files, exceeds four production files, or crosses a block threshold, split/rescope before implementation completion.

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
3. **C1a — Post and completion.** Freeze 13-row template/host mismatch and persisted workflow/state cases with missing, duplicate, pending, in-progress, mismatched, and unjustifiably skipped rows, including a legacy 11-row record whose new or renamed rows stay pending while unique exact-name statuses are preserved. Assert the workflow `✅ Complete` to state `completed` mapping and the sole optional-extension skip: both records use identical `skipped: <extension> not installed` only for a canonical extension-dependent row, and supported registry plus directory checks confirm absence. An out-of-stage skip reactivates as pending when its stage resumes. Build the new completion rule from `POST_STEPS` and call it on both hosts immediately before successful full-run return after Post; a staged-run return does not invoke the full Post completion boundary. Existing `status-evidence` remains a separate audit and cannot prove Post completion. C1a1 checkpoints after T019, and C1a2 checkpoints after T020; each runs its unit test, registered suite, generated refresh/reference check, host parity, and actual LOC/path gate before C1b begins.
4. **C1b — executor teardown.** Freeze child result/stop and teardown evidence for all eight executor definitions; their clean completion requires confirmed cleanup. Review formal lifecycle's Post subset without an assumed edit. Run its structural test, registered suite, generated refresh/reference check, host parity, and actual LOC/path gate at the C1b1 and C1b2 marker checkpoints.
5. **C2 — feedback, scaffold, envelopes, links.** Freeze >100 thread, >100 comment, missing cursor, failed page, verification failure, push failure, mismatched fresh `headRefOid`, serial reply/resolve, and resolved-state confirmation. Use the existing GraphQL route and query the PR head again after push. Freeze late nonempty analyst and all three explicit no-findings reasons, with the existing Design Concept header line as durable record. Freeze full request envelopes at only the named failure sites. Reproduce issue #638's broken template link and test new `.process/` output, verified legacy target preservation, and broken legacy repair.

Each increment follows red fixture → minimal repair → targeted green test → quick suite → generated source refresh/check → applicable docs/lint/CI suite. PR packet traceability maps every story and success criterion to source, fixture, and result. The post-Tasks advisory `atomicity-route` result remains `one-navigable-PR` (`change-shape:modify-heavy`, `releasable: true`); the layer planner remains skipped because the classifier did not emit `split-PR`. The later user-ratified five-PR order and the eleven-increment candidate are historical. The proposed order is A1a → A1b → A2 → A3 → B1a → B1b → B2a → B2b → B3a → B3b → C1a1 → C1a2 → C1b1 → C1b2 → C2a1 → C2a2 → C2a3 → C2b1 → C2b2. A top-level `pr_marker_plan` would be derived from these task boundaries, file/test scopes, reviewability evidence, and hazard route, then checked for fingerprints, membership/order, checkpoint evidence, and unsafe folds. The current validator rejects repeated shared paths, so no valid marker plan or PR emission is claimed.

## PR review packet source

Each slice PR body is generated from its validated packet and records: changed behavior and cause, explicit non-goals, review order in the proposed 19-increment sequence, actual LOC/production/total-file budget, requirement-to-file and failing-first-fixture traceability, verification commands/results, known gaps (including unavailable external-doc lookup if still relevant), and rollback/flags. A1a/A1b supply the release-note fence through the packet input. The Phase 6.5 Verdict is a protected generated value from the workflow table, not the overview row or editable body. PR title and release-note policy are checked against the final exact title/body.

## Complexity Tracking

No constitution violation is approved. A slice that exceeds its actual gate is split or rescoped rather than explained away.
