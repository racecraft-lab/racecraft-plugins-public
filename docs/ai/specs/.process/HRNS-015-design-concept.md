---
topic: "Autopilot, Gate, and PR-Emission Repair"
slug: "hrns-015-autopilot-gate-pr-emission-repair"
date: "2026-09-24"
mode: "setup"
spec_id: "HRNS-015"
source_input:
  type: "file"
  ref: "docs/ai/specs/harness-engineering-uplift-technical-roadmap.md § HRNS-015"
question_count: 11
stop_reason: "natural"
---

# Design Concept: Autopilot, Gate, and PR-Emission Repair

> **Source:** `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md` § HRNS-015, and PRD `docs/prd-harness-engineering-uplift.md` §3.16 (AC-16.1 to AC-16.10)
> **Date:** 2026-09-24
> **Questions asked:** 11
> **Stop reason:** natural. Every scope bullet is decided by a question or by cited evidence, and the slice split is accepted.
> **Blind-spot pass:** did not run — wait deadline expired

## Goals

HRNS-015 ships as **four slices** (Q11), each at most 4 production files and
under the 25-total-file block line. Stack order: A, B, C1, C2. Slice A goes
first because HRNS-016 depends on its packet repairs.

**Slice A: PR emission** (estimate 282 LOC, about 10 files)

- The packet accepts an optional `release_note` field. When supplied, the
  producer renders a `## Release note` section holding one ```` ```release-note ````
  fence inside editable markers. A fixture proves the emitted final body passes
  `scripts/compose-release-notes.py --validate-pr` for a `feat` title (Q3).
- `validate-pr-packet-write` apply succeeds when the only untracked files are
  the canonical paths of the packet being validated (`<id>.json`,
  `<id>/body.md`, `<id>/validation.json`). Any other change still blocks. The
  same exemption covers `pr-packet-output` apply when it refreshes that packet.
  A fixture covers a host repository that does not ignore packets (Q7).
- The recorded G6.5 confidence verdict appears in the final PR body. HRNS-025
  is still Pending (Tier 3), so the roadmap's condition resolves to "carry it
  here" (evidence: roadmap Progress Tracking row HRNS-025).
- The PRD (AC-16.2, AC-16.5, AC-16.8, AC-16.10), the HRNS-015 roadmap entry, and
  the HRNS-019 entry are amended to match this design concept (evidence:
  late blind-spot finding 8; Q1, Q2, Q4, Q8, Q9, Q11).

**Slice B: gates and counters** (estimate 410 LOC, about 14 files)

- The gap counter counts any bracket tag whose comma-separated tokens include
  `Gap` (`[Gap]`, `[Gap, <ref>]`, `[Coverage, Gap]`), and ignores markers inside
  inline code spans and fenced blocks. Fixtures cover each form and a quoted
  marker. `gate-validation.md:191` stops instructing a literal `grep -c "\[Gap\]"` (Q4, Q5).
- The spec-index walk excludes untracked files as well as ignored ones, for both
  backlinks and the roadmap-MOC home index.
  `python3 scripts/refresh-release-artifacts.py` regenerates the spec index, and
  `--check` fails on drift, so the required `artifact-consistency` job catches
  it. `specs/formal-001-selective-formal-methods/SPEC-MOC.md` is regenerated so
  `main` starts clean. The AGENTS.md special case for the spec index is removed (Q10).
- `reviewability-gate` setup mode takes `inputs.spec_id`, evaluates only that
  entry's section, fails closed when the section or a budget field is missing,
  honors a line-anchored `Reviewability-Exception: <class>` pragma with status
  `exception`, and counts only that entry's primary surfaces. A spec whose total
  is over the block line passes only when its entry declares a budget for every
  slice and each slice is under the block line (Q6). #637 gets a failing-first fixture.
- `estimate-spec-size` accepts a required-refactor signal (evidence: roadmap
  Slice B bullet 4; PRD AC-16.8).
- `detect-commands` reads an optional per-slot `commands` block from
  `.specify/quality-gates.json`. Declared slots override detected ones and are
  reported with `source: declared`. Phase 0 prose proposes seeding the block
  from the host's AGENTS.md or CLAUDE.md (Q9).

**Slice C1: autopilot Post list and team teardown** (estimate 335 LOC, about 14 files)

- One canonical 13-item Post list on both hosts: Claude gains
  `Post: Final Reviewability Backstop` and `Post: PR Packet/Body Generation`.
  `POST_STEPS` in `validate-autopilot-phase-coverage.py` is the single source;
  every prose count (Claude `SKILL.md:561,688,780`, Codex `SKILL.md:512`, the
  workflow template's "11-item closeout") reads 13 (Q1).
- The existing guard runs again at the completion boundary and refuses
  completion while any Post row is pending, in progress, or missing, on both
  hosts. Fixtures prove the refusal (Q1; late blind-spot finding 6).
- Every executor that can form a team carries a teardown obligation: the four
  Claude open executors (`phase-executor`, `analyze-executor`,
  `checklist-executor`, `implement-executor`) and their four Codex TOML peers.
  A structural test proves every team-capable executor carries it (evidence:
  `validate-tool-scoping.py:40-42`; PRD AC-16.4).

**Slice C2: resolve-pr, scaffold, envelopes, templates** (estimate 415 LOC, about 16 files)

- `speckit-resolve-pr` on both hosts fetches every review-thread and comment
  page (cursor pagination), then verifies, pushes, confirms the pushed SHA
  matches the remote branch head, and only then replies and resolves. Fixtures
  cover pagination and ordering (evidence: Claude `SKILL.md:75-77,184-221`;
  Codex `SKILL.md:78,129,147,156-163`; late blind-spot finding 5).
- The scaffold blind-spot pass has no fixed deadline. Scaffold awaits the
  analyst's summary and fails open only on a dispatch error, an empty return,
  or operator abandonment, each with its own recorded reason (Q2).
- Tested request envelopes appear inline at the live-failure sites:
  `speckit-status` (`generate-spec-index-check`, `o5-topology`), scaffold
  (`reviewability-gate`, `resolve-scaffold-worktree-placement`), and
  `generate-spec-index-write` in phase execution, on both hosts. A structural
  test covers those sites (Q8).
- The roadmap template and `speckit-pro/README.md:178` link workflow files at
  `docs/ai/specs/.process/`. #638 gets a failing-first fixture (evidence: issue
  #638; `technical-roadmap-template.md:86-89`).

## Non-goals

- Redesigning the PR-packet schema beyond the one optional `release_note`
  field, or the post-implementation sequence beyond unifying it at 13 rows (roadmap Out of Scope; Q1, Q3).
- Changing any host repository's release-note policy, or defaulting to the
  `release-note/skip` label (roadmap Out of Scope; Q3).
- A release-note fence in draft PR bodies, which `phase-execution.md:1051-1055`
  forbids and `pr-metadata.yml:69` never checks (evidence).
- Adding the full request envelope to all 58 bare call sites. The sweep moves
  to HRNS-019, which generates request examples from the registry (Q8).
- Self-describing runner errors for malformed requests; that stays HRNS-019's
  "validation error with remediation" item (Q8).
- Parsing AGENTS.md or CLAUDE.md command tables in the runner (Q9).
- A fourth `Reviewability-Exception` class such as `split` (Q6).
- Writing ignore rules into host repositories (Q7).
- Removing `Agent` or `SendMessage` from the open executors, which
  `validate-tool-scoping.py:264-269` requires (evidence).
- Autopilot wall-clock budgets: #642 already removed them. The roadmap's Out of
  Scope line calling that work "in review" is stale and is corrected here (evidence: commit 63a914345).

## Module and Interface Deltas

- `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`: changed. Optional `release_note` input rendered as a fenced section in editable markers; confidence verdict carried into the body (Q3; evidence: HRNS-025 Pending).
- `speckit-pro/speckit_pro_runner/contracts/pr-packet.schema.json`: changed. One optional `release_note` property under `additionalProperties: false` (Q3).
- `speckit-pro/speckit_pro_runner/helpers/read_only.py`: changed. `packet_body_structure_failures` and the protected fingerprint accept the release-note section; gap-token matching with code-span skipping; spec-index untracked exclusion for backlinks and the home index; `reviewability_gate` per-entry scoping, fail-closed fields, pragma, per-slice budgets; `estimate_spec_size` refactor signal; `detect_commands` declared commands (Q3 to Q6, Q9, Q10).
- `speckit-pro/speckit_pro_runner/helpers/mutation.py`: changed. The dirty-worktree guard exempts exactly the canonical paths of the packet under validation (Q7).
- `speckit-pro/speckit_pro_runner/helpers/registry.py`: changed if needed. `reviewability-gate` required args gain `spec_id` (Q6).
- `scripts/refresh-release-artifacts.py`: changed. Regenerates the spec index; `--check` fails on spec-index drift (Q10).
- `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`: changed. `POST_STEPS` becomes 13 items and the single source; a completion-boundary rule refuses pending, in-progress, or missing Post rows (Q1).
- `speckit-pro/speckit_pro_runner/formal/lifecycle.py`: reviewed. Its hardcoded Post-name subset (`:153`) must stay consistent with 13 items (evidence).
- `speckit-pro/skills/speckit-autopilot/SKILL.md`, `references/task-list-canonical.md`, `references/post-implementation.md`, `references/gate-validation.md`, `references/phase-execution.md`, `references/prerequisites.md`, `references/agent-teams-integration.md`, and the Codex mirrors under `speckit-pro/codex-skills/speckit-autopilot/`: changed prose (Q1, Q3, Q4, Q7, Q8, Q9).
- `speckit-pro/agents/{phase,analyze,checklist,implement}-executor.md` and `speckit-pro/codex-agents/{phase,analyze,checklist,implement}-executor.toml`: changed. Teardown obligation (evidence: PRD AC-16.4).
- `speckit-pro/skills/speckit-resolve-pr/SKILL.md` and `speckit-pro/codex-skills/speckit-resolve-pr/SKILL.md`: changed. Pagination; verify, push, confirm SHA, then reply and resolve (evidence).
- `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` and the Codex mirror: changed. Deadline removed; new fail-open reasons; inline envelopes (Q2, Q8).
- `speckit-pro/skills/speckit-status/SKILL.md` and the Codex mirror: changed. Inline envelopes for `generate-spec-index-check` and `o5-topology` (Q8; late blind-spot findings 8 and 10).
- `speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md`: changed. `.process/` workflow links (#638) and the slice-budget syntax (Q6).
- `speckit-pro/skills/speckit-coach/templates/workflow-template.md`: changed. 13-row Post table (Q1).
- `speckit-pro/README.md`: changed. Workflow path at `:178` (evidence: #638).
- `AGENTS.md` (root): changed. The spec index joins the refresh command; the "freshness: no PR check" row goes (Q10).
- `specs/formal-001-selective-formal-methods/SPEC-MOC.md`: regenerated (Q10).
- `docs/prd-harness-engineering-uplift.md` and `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md`: changed. AC and entry amendments (Goals, Slice A).
- `dist/**` and `docs-site/src/content/docs/reference/**`: regenerated, never hand-edited (evidence: AGENTS.md Editing Boundaries).
- `.github/workflows/pr-checks.yml`: unchanged. The check rides the existing required `artifact-consistency` job instead of a new step (Q10; this replaces the roadmap's listed workflow delta).
- The packet schema's other properties, `phase-execution` draft emission, and `multi-pr-emission`: unchanged grey boxes (Q3).

## Terms

| Term | Meaning in this spec | Differs from codebase usage? | Source (Q<n> or evidence) |
| ---- | -------------------- | ---------------------------- | ------------------------- |
| Post list | The 13 canonical `Post:` rows, identical on both hosts, sourced from `POST_STEPS` | Yes. Today Claude and the tests use 11, Codex uses 13, and prose also says 12 and 14 | Q1 |
| Gap marker | A bracket tag with a `Gap` token, outside inline code and fences | Yes. The counter matches the literal `[Gap]` anywhere today | Q4, Q5 |
| Packet files | `<id>.json`, `<id>/body.md`, `<id>/validation.json` under `specs/<feature>/.process/pr-packets/` | No. These are the canonical paths in `pr_emission.py:671-676` | Q7 |
| Slice | One reviewable PR of this spec (A, B, C1, C2) with its own declared budget | Yes. The roadmap entry named three slices | Q6, Q11 |
| Production file | A code or schema file counted against the 8-file block line | Partly. `estimate-spec-size` weights every file 40 LOC regardless of type | Q11; evidence `read_only.py:2231-2254` |
| Declared command | A quality-gate slot command set in the `commands` block of `.specify/quality-gates.json` | New. That file holds only thresholds and skips today | Q9 |
| Fail open (blind-spot pass) | Continue into the interview without findings, only on dispatch error, empty return, or operator abandonment | Yes. Today it also covers the 5-minute deadline | Q2 |

## Verification Gates

- Failing-first fixtures, one per acceptance criterion: release-note fence
  passes the policy validator; untracked packet exemption (and a non-packet file
  still blocks); every gap-marker form plus a quoted marker; untracked-file
  exclusion; refresh `--check` fails on the pre-fix ART-007 `SPEC-MOC.md` (from
  `b12f1bba1^`) and passes with an untracked file present; #637 (`multi`,
  `pragma`, `nobudget`, per-slice) and #638; Post-list refusal with a pending
  row on both hosts; teardown clause on every team-capable executor; resolve-pr
  pagination and ordering on both hosts; declared commands override detection;
  inline envelopes at the named sites (roadmap Done When; Q1 to Q10).
- Quick suite: `python3 tests/speckit-pro/run-all.py` passes (AGENTS.md Commands).
- CI suite: the `run-default-suite.json` runner request passes (AGENTS.md Commands).
- Generated artifacts: `python3 scripts/refresh-release-artifacts.py --check`
  passes, now including the spec index (Q10).
- Docs reference: `pnpm --dir docs-site reference:generate`, then
  `reference:check` and `validate:quality`, after any test-tree or reference-input change (AGENTS.md Commands).
- Python lint: ruff F rules and the mypy ratchet through `scripts/run-python-lint.py` (AGENTS.md Commands).
- PR title and release-note fence gates on every slice PR (AGENTS.md Commands).
- Per-slice reviewability budget: at most 4 production files and under 25 total files per slice (Q6, Q11).
- Formal methods: none. The changes are deterministic parsers, guards, and
  prose; failing-first fixtures are the acceptance contract, and no concurrent
  or stateful protocol here justifies a model (evidence: roadmap Done When).

## Design Tree (Q&A log)

### Q1. What should the single canonical Post list be?
**Branch:** Slice C1, Post list
**Recommended answer:** 13 on both hosts
> Codex tracks `Final Reviewability Backstop` and `PR Packet/Body Generation` as separate rows "for resume safety" and says never to delete them (`post-implementation-codex.md:65-68`). Claude does the same work in `post-implementation.md:388-412` without its own rows. The deterministic guard already exists as `POST_STEPS` (`validate-autopilot-phase-coverage.py:70-82`) but runs only before Phase 1 (late blind-spot findings 4 and 6).
**Alternatives offered:** 11 on both hosts (loses Codex resume points); host-specific lists stated once (keeps the hosts different).
**User's answer:** 13 on both hosts (Recommended)
**Notes:** Research also found Codex `SKILL.md:512` stating 14 and Claude `SKILL.md` stating 11, 12, and 11.

### Q2. How should HRNS-015 handle the blind-spot deadline?
**Branch:** Slice C2, scaffold blind-spot pass
**Recommended answer:** Remove it and await the reply
> In this scaffold the analyst returned 11 findings after 18.1 minutes, against a 5-minute deadline, and the pass was recorded as "did not run". #434's own review called five minutes "merely unprecedented". No test references the deadline, and #642 removed autopilot's wall-clock limits without touching scaffold (late blind-spot finding 9).
**Alternatives offered:** a longer deadline with a distinct "still running" record and late findings as Open Questions; keep 5 minutes and fix only the label.
**User's answer:** Remove it; await the reply (Recommended)

### Q3. How should the packet carry a release note?
**Branch:** Slice A, release-note gate
**Recommended answer:** An optional `release_note` field
> `inputs.body` already replaces the whole body in every mode (`pr_emission.py:562-564`), and the validator accepts extra headings (`read_only.py:6629-6650`). The schema has `additionalProperties: false`. Only the final non-draft PR is checked (`pr-metadata.yml:69`; `release_note_policy.py:486-511`). Step 6f forbids hand-written body content, while root AGENTS.md says to add the fence with `gh pr edit` (late blind-spot finding 7).
**Alternatives offered:** document the `inputs.body` hook (hand-written full body); add the fence with `gh pr edit` (body drifts from the validated packet).
**User's answer:** Optional release_note field (Recommended)

### Q4. Which bracket markers should count as a gap?
**Branch:** Slice B, gap counter
**Recommended answer:** Any tag with a `Gap` token
> The upstream checklist skill emits `[Gap, Exception Flow]`, `[Coverage, Gap]`, `[Dependency, Gap]`, and `[Edge Case, Gap]` (`.claude/skills/speckit-checklist/SKILL.md:217-340`). Archived runs recorded the misses three times, once as 0 of 16 (`ART-008-workflow.md:134-137`, `ART-014-retrospective.md:218-222`, `ART-001-workflow.md:1417-1420`). `gate-validation.md:191` carries a prose copy of the bug (late blind-spot finding 3).
**Alternatives offered:** the `[Gap` prefix only, as AC-16.5 is worded.
**User's answer:** Any tag with a Gap token (Recommended)

### Q5. Should the counter skip code?
**Branch:** Slice B, gap counter
**Recommended answer:** Skip code spans and fences
> `count_pattern` counts matching raw lines (`read_only.py:8278`). HRNS-015's own spec will quote the marker while describing this fix and could fail its own G4 (late blind-spot finding 1).
**Alternatives offered:** count everywhere and rely on a quoting convention.
**User's answer:** Skip code spans and fences (Recommended)

### Q6. What should setup mode do with an over-budget spec planned as several slices?
**Branch:** Slice B, reviewability gate (#637)
**Recommended answer:** Per-slice budgets
> Setup mode reads the last entry's numbers (`read_only.py:2121-2177`) and never parses the pragma. Once scoped per entry, HRNS-015's own 9 production files would block, and "ships as three slices" is not a typed exception class (late blind-spot finding 2). Issue #637 suggests `inputs.spec_id`, fail-closed fields, and the line-anchored pragma.
**Alternatives offered:** a `split` exception class (changes the typed vocabulary, never checks slices); a plain block that forces separate roadmap entries.
**User's answer:** Per-slice budgets (Recommended)
**Notes:** `validate-spec-lifecycle-contracts.py:72-74,88-90` forbids literal pragma examples in the templates, so the slice-budget syntax must not add one.

### Q7. What counts as success when the packet files are untracked?
**Branch:** Slice A, untracked packet
**Recommended answer:** Exempt this packet's own files
> This repo ignores `specs/*/.process/pr-packets/` as "local process exhaust" (`.gitignore:29-32`), so the prose instruction to commit the packet (`post-implementation.md:458`) cannot be followed here without `git add -f`. In a host without that rule, `--untracked-files=all` (`mutation.py:1436-1452`) blocks on the packet, body, and the helper's own `validation.json` (late blind-spot finding 11).
**Alternatives offered:** install an ignore rule in the host; commit the packet, then commit `validation.json` again.
**User's answer:** Exempt this packet's files (Recommended)

### Q8. How much of the request-envelope work should HRNS-015 take on?
**Branch:** Slice C2, helper envelopes
**Recommended answer:** Live-failure sites now, the rest to HRNS-019
> 58 of 66 "runner helper" mentions across 15 skill files show no request. HRNS-019 already plans to generate skill-facing request examples from the registry with a drift check. A tested `generate-spec-index-check` envelope exists at `validate-spec-lifecycle-contracts.py:578` (late blind-spot finding 10).
**Alternatives offered:** all 58 sites inline now; self-describing runner errors.
**User's answer:** Failure sites now, rest to HRNS-019 (Recommended)

### Q9. How should a detected quality-gate command honor the host's documented command?
**Branch:** Slice B, detect-commands
**Recommended answer:** Declared commands in config
> `detect_commands` (`read_only.py:1768`) takes no override and never reads the host's agent docs; any Python root marker yields raw `pytest` (`:1828`). For this repo it produced `FULL_VERIFY: mypy . && ruff check && ...`, which ignores the `mypy.ini` allowlist AGENTS.md prescribes. The only safeguard is prose naming a "Build Commands" table (`prerequisites.md:351`).
**Alternatives offered:** parse AGENTS.md or CLAUDE.md tables; prose only.
**User's answer:** Declared commands in config (Recommended)

### Q10. Where should the real-tree spec-index check run?
**Branch:** Slice B, spec index
**Recommended answer:** Inside `refresh-release-artifacts.py`
> No workflow runs the check (`.github/workflows/*.yml`), and `main` is stale today: the formal-001 map's backlinks miss three tracked files. AGENTS.md names the spec index as the one generated output the refresh script does not cover.
**Alternatives offered:** a separate required CI step; a Layer 1 suite test.
**User's answer:** Inside refresh-release-artifacts (Recommended)

### Q11. How should HRNS-015 be sliced for review?
**Branch:** Slice sizing
**Recommended answer:** Four slices: A, B, C1, C2
> `estimate-spec-size` on the expanded scope: whole 1,362 LOC and 4 suggested slices (14 stories, 25 FRs, 50 files); A 282; B 410; C 750 with about 30 files, over the 25-file block. Splitting C gives C1 335 and C2 415. The 292-LOC roadmap budget went stale during this interview, which is the Slice B refactor-signal defect in action.
**Alternatives offered:** three slices as planned (C over the block); five slices (also split B).
**User's answer:** Four slices: A, B, C1, C2 (Recommended)

### Resolved from evidence (no question asked)

- **resolve-pr (Slice C2):** Neither host paginates (Claude `SKILL.md:75-77` fixes `first: 100` and 10 comments; Codex `SKILL.md:78` gives no page size). Claude replies and resolves (Step 5, `:184-199`) before full verify and push (Step 6, `:210-221`); Codex verifies before resolving (`:129`) but never requires the push first. Both hosts get cursor pagination and the verify, push, confirm-SHA, then reply order (late blind-spot finding 5).
- **Team teardown (Slice C1):** Four Claude executors keep `Agent` and `SendMessage` by design (`validate-tool-scoping.py:40-42,264-269`). The Codex peers grant `spawn_agent` in prose. `agent-teams-integration.md:143-153` states teardown in prose with no test. Each team-capable executor gets the clause, plus a structural test (PRD AC-16.4).
- **Confidence verdict (Slice A):** HRNS-025 is Pending, so HRNS-015 carries the G6.5 verdict into the final body. No code writes it today (`pr_emission.py`; `pr-packet.schema.json`).
- **#638 (Slice C2):** The template links `SPEC-001-workflow.md` at `docs/ai/specs/` (`technical-roadmap-template.md:86-89`) while scaffold writes `.process/`; `README.md:178` shows a third form. The template links `.process/`.
- **Done-When coverage:** Five scope bullets had no Done-When line, and `speckit-status/SKILL.md` was missing from the deltas (late blind-spot finding 8). The Goals above give each one an observable outcome.

## Open Questions

- **What:** Whether `[NEEDS CLARIFICATION]` counting also skips code spans, since it shares `count_pattern`.
  **Why deferred:** Q5 decided the gap counter only; the NEEDS CLARIFICATION regex (`read_only.py:1959`) is otherwise correct.
  **Suggested next step:** Clarify, when the plan picks where the code-span skip lives.
- **What:** The shape and weight of the refactor signal in `estimate-spec-size`.
  **Why deferred:** The interview fixed that the signal exists, not its formula.
  **Suggested next step:** Plan, calibrated against the 292-to-1,362 drift recorded in Q11.
- **What:** The slice-budget syntax in roadmap entries and the template.
  **Why deferred:** Q6 set the policy; the syntax must avoid literal pragma examples (`validate-spec-lifecycle-contracts.py:72-74,88-90`).
  **Suggested next step:** Plan and data-model.
- **What:** How the four slices ship: one autopilot run on the split-PR route (the first live `multi-pr-emission` apply, which HRNS-016 also waits on) or separate runs.
  **Why deferred:** The atomicity route is decided after Tasks.
  **Suggested next step:** Record the route at the Atomicity Route step; stack order A, B, C1, C2.
- **What:** HRNS-015's own run uses the cached, pre-fix plugin, so its own final PRs hit the release-note defect and the stale Post list.
  **Why deferred:** The fixes take effect only after release and a cache refresh.
  **Suggested next step:** Add each slice PR's fence by hand until Slice A is released.
- **What:** Whether Codex `spawn_agent` children can outlive their parent the way a Claude teammate did.
  **Why deferred:** No host evidence in the repository; HRNS-017's host spike observes host behavior.
  **Suggested next step:** Clarify; the teardown clause ships on both hosts regardless.
- **What:** Stale prose found during research: step 6c's reviewer-checklist block and `speckit-pro-review-packet-source` marker (`post-implementation.md:443-449`), the Codex `#pr-body-generation` anchor (`phase-execution-codex.md:23`), and the duplicated `## UAT Runbook` rendering (`pr_emission.py:964-971`).
  **Why deferred:** Not in the roadmap scope.
  **Suggested next step:** Fix 6c in Slice A only if that paragraph changes anyway; otherwise leave for a follow-up.
- **What:** Where the G6.5 verdict renders in the body (the Verification section or its own line).
  **Why deferred:** A plan detail with no user-visible tradeoff.
  **Suggested next step:** Plan.

## Recommended Next Step

Return to `/speckit-pro:speckit-scaffold-spec HRNS-015` to populate the
workflow file from this design concept, then run the planning stage.
