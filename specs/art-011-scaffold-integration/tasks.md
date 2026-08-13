# Tasks: Scaffold Integration — blind-spot pass and autopilot chain

**Input**: Design documents from `specs/art-011-scaffold-integration/`

**Prerequisites**: plan.md (required), spec.md (required for user stories),
research.md, `contracts/blind-spot-pass.md`, `contracts/chain-handoff.md`,
`docs/ai/specs/.process/ART-011-design-concept.md` including its two Revision
Notes.

**Tests**: No new test tasks beyond the two Layer 2 fixture edits FR-021b
requires. Nothing this feature adds is executable, so there is no Layer 4
fixture to write (Q21, plan Technical Context). See Notes.

**Reviewability**: 47 tasks against a measured budget of **322 reviewable LOC**,
**2 production files**, 9 changed files of which 4 are generated, one primary
surface (harness/adapter), **one slice, no split** (plan.md § Reviewability
Budget). The task count is high because these are prose insertions into two
existing files at 16 named anchors, not new-code tasks. A `tasks × 40` heuristic
is **not** the anchor here; the plan's measured `estimate-spec-size` figure of
322 is, and it is under the 400 warn ceiling. Do not split on task count alone.

**Organization**: Tasks are grouped by user story. Phase 7 mirrors all four
stories into the Codex variant in one pass, by explicit ordering constraint, so
each of its tasks still carries its `[USn]` label.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact repo-relative file paths in descriptions

## Path Conventions

Every path in this file is **repo-relative**, rooted at the repository root.
Never write an absolute filesystem path into an authored artifact; the tree-wide
privacy scan fails on paths rooted at a user's home directory.

- Production surface (exactly two files, FR-022):
  - `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` (Claude, 7 sites)
  - `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md` (Codex, 9 sites)
- Test fixtures: `tests/speckit-pro/layer2-trigger/evals/` and `.../codex-evals/`
- Roadmap: `docs/ai/specs/html-artifacts-technical-roadmap.md`

## Transcription rule — read before starting

The two files under `specs/art-011-scaffold-integration/contracts/` fix **exact
text**. A task below that says *transcribe* means: **copy the named contract
section verbatim. Do not paraphrase, do not reword, do not normalise spelling.**
The most damaging paraphrase is spelled out at `contracts/blind-spot-pass.md`
§6: the sentinel `The blindspot pass raised no unknown unknowns.` uses the
one-word spelling and is matched literally, while scaffold's own voice uses the
hyphenated `blind-spot`. Normalising either breaks the usable-reply test
silently, on exactly the runs where the pass worked.

## Boundaries — no task below crosses one

Checked against the eight boundaries this feature declares. **Zero crossings.**

- No task creates or edits an agent definition on either platform (FR-002). This is what keeps the Layer 6 sha256 corpus chain in `tests/speckit-pro/layer6-efficiency/fixtures-codex/` unstaled; that chain has no regeneration script.
- No task edits any file under `speckit-pro/skills/grill-me/` or `speckit-pro/codex-skills/grill-me/` (FR-008, Q3, Q19).
- No task adds a third production file (FR-022).
- No task adds a script, runner helper, or any executable machinery (FR-023).
- No task adds Grep, Glob, or Bash to scaffold's `allowed-tools`, which stays exactly `Read Edit Write Skill Agent ToolSearch` (FR-002).
- No task edits a roadmap other than the ART-011 reviewability declaration (T038).
- No task creates a `references/` directory under either scaffold skill (FR-022).
- No task places text between `## Codex Skill-Selection Guard` and the next `## ` heading in the Claude file; the payload build strips that region and text there ships to nobody (research.md R9).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm every anchor the plan names still exists, and capture the
baselines the verification phase measures against. All three tasks are
read-only; nothing is written.

- [X] T001 Confirm all 16 anchors from plan.md § Execution Flow still exist verbatim, by reading `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` (anchors: frontmatter `description`; `### 3.5. Bootstrap the Worktree (IN the Worktree)`; `### 4. Run Grill Me Interview (IN the Worktree)`; `Must contain Goals, Non-goals, Design Tree (Q&A log), and Open Questions.`; `**Ready to run:**`; `**Review both files first**`; `**NEVER push to main.**`) and `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md` (anchors: frontmatter `description`; `Do not run the autopilot at the end.`; `### 3.5. Bootstrap the worktree (in the worktree)`; `### 4. Run the Grill Me interview (in the worktree)`; the `If grill-me aborts` paragraph; `the exact next step: start a new Codex task rooted at that worktree`; `Never hand off only the inner workflow path from the parent checkout.`; `see openai/codex#7480`; `## Failure Handling`). Stop and report if any anchor is missing or non-unique.
- [X] T002 [P] Record baselines for the verification phase: the `description` character count in both `SKILL.md` frontmatter blocks (expected 975 each, byte-identical), the Codex body word count (expected ~3250, cap 8000), and the entry count in both files named at `tests/speckit-pro/layer2-trigger/evals/speckit-scaffold-spec-trigger.json` and `tests/speckit-pro/layer2-trigger/codex-evals/speckit-scaffold-spec-trigger.json` (expected 16 each, 8 positive and 8 negative)
- [X] T003 [P] Recover the normative ART-006 chain contract into the session, read-only, with `git show 5e184e33:specs/art-006-autopilot-staging/contracts/scaffold-autopilot-chain.md` and `git show 5e184e33:specs/art-006-autopilot-staging/contracts/stage-invocation.md` (research.md R1). Do not check out, copy, or relocate either file; relocation is a named deferral

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the new Claude `### 3.6` section and place the one block
every other pass task positions itself against. Nothing in US1 or US2 can land
until the section exists and the dispatch block is sited inside it.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 In `speckit-pro/skills/speckit-scaffold-spec/SKILL.md`, insert a new `### 3.6 Blind-Spot Pass (IN the Worktree)` section between the closing paragraph of `### 3.5. Bootstrap the Worktree (IN the Worktree)` and the `### 4. Run Grill Me Interview (IN the Worktree)` heading. **Do not renumber Steps 4 through 8.** Write only the section heading and the placement-and-mandate prose from `contracts/blind-spot-pass.md` §1: the pass runs inside the worktree immediately before the interview, on every invocation, with no skip flag, no skip argument, and no documented path that reaches the interview without attempting it — stated as a constraint in the same register the existing grill-me step uses ("There is no `--no-grill` flag and no skip path"). Acceptance: FR-001 satisfied; the `### 4` heading and its number are untouched
- [X] T005 In the same file, **transcribe verbatim** the dispatch block from `contracts/blind-spot-pass.md` §4 into `### 3.6`, as a fenced `text` block. It is byte-identical across both platforms, so copy it; do not paraphrase, and do not normalise the one-word `blindspot pass` or the phrase `unknown unknowns` (FR-005). Leave insertion room above it for T007 and T008 and below it for T009. Acceptance: the block matches §4 character for character, including the `N. **<Title>** - 1-3 sentences` shape and the closing sentinel line
- [X] T006 Verify the reviewability budget against the planned task and file scope before implementation continues, and record the decision in this file's header: 322 measured reviewable LOC, 2 production files, 9 changed files of which 4 are generated, one primary surface — **within budget, one slice, no split** (plan.md § Reviewability Budget, spec.md § Reviewability Budget). If the count is challenged by a `tasks × 40` heuristic, the plan's measured `estimate-spec-size` figure is the anchor

**Checkpoint**: The `### 3.6` section exists with its mandate and its verbatim dispatch block. User story implementation can begin.

---

## Phase 3: User Story 1 - Unknown unknowns surfaced before the interview (Priority: P1) 🎯 MVP

**Goal**: Scaffold dispatches the shipped read-only `codebase-analyst`, awaits
its summary, and prints at most five ranked findings with an explicit set-aside
count, before the first interview question, on every run.

**Independent Test**: Scaffold any roadmap entry and confirm that, before the
first interview question, the run shows a ranked findings list of at most five
items with an explicit count of what was set aside, and that no invocation path
reaches the interview without having attempted the pass.

All five tasks edit the one new `### 3.6` section in
`speckit-pro/skills/speckit-scaffold-spec/SKILL.md`, so none is `[P]`. Each
names where its prose lands relative to the T005 dispatch block, so the section
assembles in the contract's own order.

- [X] T007 [US1] **Above the T005 dispatch block**: write the engine, dispatch, and await discipline from `contracts/blind-spot-pass.md` §2. Name the engine as the already-shipped read-only `codebase-analyst`, consumed unmodified; state the two prohibitions (no agent definition added or edited; `allowed-tools` stays exactly `Read Edit Write Skill Agent ToolSearch`, no Grep, no Glob, no Bash). Give the Claude dispatch identifier `speckit-pro:codebase-analyst` and the form `Agent(subagent_type: "speckit-pro:codebase-analyst", run_in_background: true, ...)` followed by an await of completion **before the interview begins**. Transcribe the §2 bound table: a per-poll timeout is **not** a verdict, and abandonment is governed by one **pass execution deadline of five minutes from dispatch**, recorded on expiry as the `did not run` outcome with reason `wait deadline expired`. State that a summary arriving after the deadline does not retroactively change the recorded outcome. Acceptance: FR-002, FR-002a; SC-012's "no new tool grant" is visibly restated in the prose
- [X] T008 [US1] **Between T007 and the dispatch block**: write the seed rules and the payload-assembly order from `contracts/blind-spot-pass.md` §3 and §4.1. Scope text is required and is read as text rather than by matching a `**Scope:**` heading. The dependency chain is required **when the entry declares one under any heading**, including renamed variants such as `**Deps:**`; only when no declaration exists in any spelling is the `Depends On:` label appended with the literal `none`. `Key Files` is an optional hint whose label is **omitted entirely** when absent — never a reported gap, never a skip. Transcribe the §4.1 appended-material template verbatim (`Scope:` then `Depends On:` then `Key Files:`, in that order, below the block) and state that **nothing else is appended**: no operator commentary, no prior findings, no spec text. Include the FR-004 archived-dependency chase: each `Depends On` spec whose artifacts are not in the working tree is chased into git history rather than reported absent. Acceptance: FR-003, FR-004; the two absent-field behaviours differ exactly as §3 requires
- [X] T009 [US1] **Immediately below the dispatch block**: write the reply-classification rules from `contracts/blind-spot-pass.md` §5. Transcribe the three-outcome table's tests: **ran** (a finding in the fixed shape **or** the literal sentinel came back), **returned nothing usable** (a reply carrying neither), **did not run** (no reply at all — dispatch error, empty return, or the execution deadline expiring). Define "a finding in the fixed shape" as a numbered item carrying a title and at least one of the two rationale lines. State explicitly that a single expired poll is **not** the third outcome. Acceptance: FR-006's three disjoint outcomes are decidable with no judgement call
- [X] T010 [US1] **Below T009**: write cap enforcement, ranking, and the operator status lines from `contracts/blind-spot-pass.md` §6. **Scaffold enforces the cap on what it renders**: on more than five findings, show the first five **in the analyst's own order**, count the remainder, and state that count — never re-rank, merge, or rewrite. The cap is not operator-configurable. No numeric score is assigned. **Transcribe all five status strings verbatim**: the three set-aside shapes (`Showing the 5 highest-impact findings; N more were set aside`, `Showing all N findings; none were set aside`, and the sentinel echoed unchanged) and the two degraded lines (`The blind-spot pass returned nothing usable; continuing without findings. Reason: <reason>` and `The blind-spot pass did not run; continuing without findings. Reason: <reason>`). Fix the `<reason>` clause vocabulary: `reply carried neither a finding nor the sentinel`, `dispatch error: <message>`, `empty return`, `wait deadline expired`. State that **exactly one** of the five is emitted per run, and carry §6's warning that the sentinel's one-word spelling must not be normalised. Acceptance: FR-006; SC-002
- [X] T011 [US1] **Closing the section**: write fail-open and the informational flow from `contracts/blind-spot-pass.md` §7 and §10. Scaffold must not treat the dispatch outcome as a gate and must not retry-then-halt. Transcribe §7's critical clarification: **"nothing seeded" means no findings are seeded, not that the labelled block is omitted** — the block still travels in all three outcomes, carrying only its status line in the degraded two. Record the gap and its reason in **both** sinks: the operator status line (scaffold prints it) and the design-concept header line (T016 verifies it). Close with §10: the run flows straight into the first interview question with **no confirmation, no curation step, no continue/abort prompt**. Acceptance: FR-007, FR-011; SC-001

**Checkpoint**: User Story 1 is complete on Claude. The pass runs, awaits, classifies, caps, reports, and fails open, and the run flows straight into the interview.

---

## Phase 4: User Story 2 - Findings survive into the interview and the record (Priority: P1)

**Goal**: The findings reach the interview through the `scope` argument grill-me
already consumes, every finding is afterwards traceable in the design concept,
and the design concept's header states whether the pass ran.

**Independent Test**: With a known findings list, confirm the interview receives
it as an identifiable block on the input it already consumes, that every finding
is afterwards traceable in the design concept as a resolved answer or an Open
Question, and that the header states whether the pass ran.

All four tasks edit `speckit-pro/skills/speckit-scaffold-spec/SKILL.md`, so none
is `[P]`.

- [X] T012 [US2] In `### 3.6`, **transcribe verbatim** the labelled seeded-scope block from `contracts/blind-spot-pass.md` §8, as a fenced `text` block, and state that it uses **one shape in both places it appears** — the operator output and the seeded `scope` string — so the two records cannot drift. Mark the second line (the set-aside line) as the **only** conditional one: present in the two shapes that show findings, omitted when the sentinel came back and in both degraded outcomes. The delimiters and the two closing instructions never vary. Carry §8's explicit refusal to resolve the awkwardness by forking the two copies, softening the imperatives in one, or dropping them from the printed half. The block's second closing instruction is FR-009's channel: `Treat each finding as a candidate question; any finding not reached becomes an Open Question.` Acceptance: FR-008, FR-009; SC-003
- [X] T013 [US2] Amend the `scope:` line inside the existing `Skill("grill-me", args: {...})` invocation in `### 4. Run Grill Me Interview (IN the Worktree)` so `scope` carries the roadmap scope text **plus** the T012 labelled block appended to it. **No new interview argument. No change to what the interview produces. No edit to any file under `speckit-pro/skills/grill-me/` or `speckit-pro/codex-skills/grill-me/`.** State that the block travels in all three outcomes (T011). Acceptance: FR-008; the grill-me skill directories are untouched in `git status`
- [X] T014 [US2] In `### 3.6`, **transcribe verbatim** the three design-concept header-line shapes from `contracts/blind-spot-pass.md` §9, under the key `**Blind-spot pass:**` (hyphenated — scaffold's own voice): `ran — N findings surfaced, M set aside`, `returned nothing usable — <reason>`, `did not run — <reason>`. State that the word after the key is the discriminator, drawn from that closed set, that `<reason>` is the **same clause** the T010 status line carried, and that a pass which ran and raised nothing is the first shape with `N` and `M` both zero. Carry §9's prohibitions: no new section in the design concept, **no separate findings artifact — specifically not `.process/<SPEC-ID>-blind-spots.md`**, no change to grill-me's output schema. Acceptance: FR-010; SC-004
- [X] T015 [US2] Extend the existing post-interview assertion in `### 4` — the line reading `Must contain Goals, Non-goals, Design Tree (Q&A log), and Open Questions.` — by one key: verify the design concept carries `**Blind-spot pass:**` in its header blockquote, and when the key is absent, `Edit` the T014 line in from the values already held (the outcome, the `<reason>` clause, and `N` and `M` for the `ran` outcome). Use only `Read` to check and `Edit` to repair — no new tool grant, no new machinery, no new section, no separate artifact, no grill-me edit. State that when the interview does not return, nothing is owed, because the run stops and no design concept exists (`contracts/blind-spot-pass.md` §9.1). Acceptance: FR-010a

**Checkpoint**: User Stories 1 and 2 are complete on Claude. Findings reach the interview and the durable record is verified rather than assumed.

---

## Phase 5: User Story 3 - One confirmation, then planned work or a clean stop (Priority: P1)

**Goal**: After Step 8, scaffold runs one read-only pre-chain check, asks exactly
one structured confirmation, and either chains into the autopilot plan stage or
prints the hand-off command.

**Independent Test**: Complete a scaffold run to the end of the roadmap status
flip, then verify exactly one confirmation is presented, that accepting starts
planning in the same session with the contract-fixed invocation, and that
declining ends the run with a pushed branch and a copy-pasteable resume command.

All six tasks edit `speckit-pro/skills/speckit-scaffold-spec/SKILL.md`, so none
is `[P]`.

- [X] T016 [US3] Amend the two `## Scaffold Complete` report lines (the report is a top-level `##` heading sitting between Step 7 and Step 8; cite the literal strings rather than a step number). Soften `**Review both files first**` to `**Review both files**` so the report and the confirmation stop giving opposite instructions (FR-013). Relabel `**Ready to run:**` to `**If you stop here, run:**` and add the `--stage plan` token to the command beneath it, bringing it into the FR-015c fixed form (`contracts/chain-handoff.md` §4 companion edit and §6.1). **Nothing else in that report changes**; neither line is validator-pinned, only the `## Scaffold Complete` heading is. Acceptance: FR-013, FR-015c
- [X] T017 [US3] Insert a new `### 9. Chain into the Planning Stage` section after Step 8's closing `**NEVER push to main.**` paragraph. **Do not renumber Steps 4 through 8.** Write the placement rationale (`contracts/chain-handoff.md` §1: a chained planning stage that fails must never leave the roadmap claiming the spec is still Ready) and the FR-013a pre-chain check from §2, using **the guard's own words**: (1) resolve the current checkout with `git rev-parse --show-toplevel`; (2) **"If the supplied workflow path exists inside that checkout, continue."** Do not paraphrase step 2 as "resolves inside", "is under", or "belongs to". State explicitly that this is an **existence test on the supplied path, not a comparison of directories**, and that it must not be implemented by canonicalising the path and comparing its parent, repository root, or worktree root. Add test 2: `git status --porcelain` is clean **in the same checkout step 1 resolved**. State what the check must **not** test: the most recent commit, because after Step 8 the newest commit is the roadmap status flip. Acceptance: FR-012, FR-013a; both commands already run at Step 3.5, so FR-023 holds
- [X] T018 [US3] In `### 9`, write the one printed line that precedes the confirmation (`contracts/chain-handoff.md` §4, "One printed line before the question"). It states **three facts and no more**: accepting runs the six planning phases in this same session without further prompts; those phases commit as they go; declining leaves everything already pushed exactly as it is. It is **printed, not asked** — no options — and does not count against the SC-007 budget. Acceptance: FR-013's informational-line requirement
- [X] T019 [US3] In `### 9`, write the confirmation itself from `contracts/chain-handoff.md` §4, using `AskUserQuestion` on Claude. **Transcribe verbatim** the question text `Scaffold is complete and pushed. Start the planning stage now?` and the two mutually exclusive options in this order: `Start planning (Recommended)`, then `Stop here`. State the FR-015b prohibitions: scaffold must **not** fall back to parsing a free-text reply, and must **not** chain by default when confirmation is unavailable. Record the SC-007 budget as counting **what this feature adds** — exactly one when the chain is attempted, none when the FR-013a check fails — and note that Step 3's reuse question and Step 3.5's bootstrap approval are pre-existing, are not counted, and are not removed. Acceptance: FR-013, FR-015b; SC-007
- [X] T020 [US3] In `### 9`, write the accept path from `contracts/chain-handoff.md` §5. On acceptance, **print the invocation verbatim immediately before running it**, then run it: `/speckit-pro:speckit-autopilot <workflow-file> --stage plan`. The stage token is the literal lowercase `plan` from the closed vocabulary `plan`, `implement`, `full` — no aliases, no alternate casing, no long-form spellings. The workflow file path is the **sole** hand-off token; no state file, branch name, feature directory, or environment variable crosses the boundary. Acceptance: FR-014; SC-005
- [X] T021 [US3] In `### 9`, write the three no-chain paths from `contracts/chain-handoff.md` §6 — the operator declines, no structured confirmation mechanism is available, or the FR-013a check fails — and state that in every case **nothing is rolled back**. **Transcribe verbatim** the §6.1 hand-off command table: Claude Code prints `/speckit-pro:speckit-autopilot <workflow-file> --stage plan`; Codex CLI prints `start a new Codex task rooted at the spec worktree, then $speckit-autopilot <workflow-file> --stage plan`, with the rooting instruction as **part of the command, not commentary beside it**. Note that the Claude chain is unconditional beyond FR-013a because Claude's autopilot ships no worktree-binding guard, so a mis-rooted Claude chain would resolve silently against the parent checkout (FR-015b). Acceptance: FR-015, FR-015b, FR-015c; SC-006

**Checkpoint**: User Story 3 is complete on Claude. One confirmation, a contract-fixed chain, and three clean stops.

---

## Phase 6: User Story 4 - One closing report that tells the truth (Priority: P2)

**Goal**: However the run ended, one closing report renders, names what exists
and where, names nothing that does not exist, and ends with one next step.

**Independent Test**: Drive the run to each terminal condition (declined,
chained and complete, chained and interrupted) and confirm one closing report
renders in each, that its artifact list matches the files on disk, that the
draft-PR line is absent with a plain note when no PR exists, and that the
interrupted case names the phases that reached a terminal status.

All five tasks edit `speckit-pro/skills/speckit-scaffold-spec/SKILL.md`, so none
is `[P]`.

- [X] T022 [US4] Insert a new `### 10. Closing Report` section after `### 9`. Name **all four render triggers** from `contracts/chain-handoff.md` §8: after the planning stage on acceptance, and immediately on each of the three no-chain paths (declined, no confirmation mechanism, pre-chain check failed) — the third is the **ordinary** Codex run, which is why a two-item list is insufficient. State that the report is **printed, not written to a file**. **Transcribe verbatim** the four-element layout block (`## <heading>`, `**Outcome:**`, `**Draft PR:**`, `**Artifacts:**`, `**Next step:**`) and the closed three-value heading table: `## Stopped Before Planning`, `## Planning Complete`, `## Planning Incomplete`. State which fields are fixed, conditional, and derived, and that the set-aside findings count **must not** appear here. Carry §8's "what this report adds" bound: no worktree path, no remote line, no bootstrap result — the `## Scaffold Complete` report already gave all three. Acceptance: FR-016, FR-017, FR-018
- [X] T023 [US4] In `### 10`, **transcribe verbatim** the four-row outcome-line table from `contracts/chain-handoff.md` §8.3, one line per no-chain cause: operator declined; no structured confirmation mechanism; rooting test failed; cleanliness test failed. All four close on **"nothing was rolled back"**. Carry §8.3's requirement that the rooting row **reads as an ending, not an apology** — it leads with what is finished, because on Codex it is the ordinary outcome reached by an operator who did nothing wrong — and that this string is **identical on both platforms**, since a platform-forked outcome line would be a fifth divergence outside SC-011's closed list. Acceptance: FR-018; SC-011
- [X] T024 [US4] In `### 10`, write the draft-PR line and the artifact index from `contracts/chain-handoff.md` §8.1 and §8.2. The PR line shows the URL when one exists and otherwise states plainly `Draft PR: none, because draft-PR creation is not part of this release` — never omitted silently, never fabricated or guessed (ART-007 owns creation). **Transcribe the closed candidate set** from §8.2: scaffold-owned (`docs/ai/specs/.process/<SPEC-ID>-design-concept.md`, `docs/ai/specs/.process/<SPEC-ID>-workflow.md`, `specs/<feature>/SPEC-MOC.md`, the pushed branch name) plus planning-stage (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `tasks.md`, each file under `contracts/`, each file under `checklists/`, all relative to `specs/<feature>/`). State that **the existence test is a read of the candidate path and nothing more** — a path that reads is listed, a path that does not read is omitted — because that is the only existence test inside scaffold's declared grant, which FR-002 forbids widening with Grep, Glob, or Bash. For the two directory-valued members the candidate paths are the artifact names the run's own plan and checklist phases recorded. Never infer a path from convention; never list a path that was not tested. Acceptance: FR-018; SC-008, SC-009
- [X] T025 [US4] In `### 10`, write the next-step rule for **all three headings**, so no heading ends on an undefined line. Under `## Stopped Before Planning` the value is the T021 hand-off command (§8.3). Under `## Planning Complete` it is the §5 invocation with the stage token advanced to the literal lowercase `implement` (§8.4) — and state that scaffold must **never chain into the implement stage and never ask a second confirmation to offer it**; the implement stage is named as the operator's next command, never as scaffold's next action. Under `## Planning Incomplete` it is the §9.0 resume command, which **is** the next step rather than a fifth element: the §5 invocation plus `--from-phase <phase>` where `<phase>` is **derived** as the first planning-phase row in `## Workflow Overview` without a terminal status, named in the lowercase vocabulary `specify`, `clarify`, `plan`, `checklist`, `tasks`, `analyze` — and with `--from-phase` **omitted entirely** when all six planning rows are terminal, because `Confidence Gate` is not a planning-phase row and has no token in that vocabulary. Acceptance: FR-018, FR-019; SC-007's "no second confirmation"
- [X] T026 [US4] In `### 10`, write the completion test from `contracts/chain-handoff.md` §9: completion is determined **by reading the workflow file**, with no live session and no state file. Two conditions — (1) every planning-phase row in `## Workflow Overview` carries a terminal status; (2) a `G6.5` verdict is recorded **and** the `Confidence Gate` row does not carry a blocked status. Explain why condition 2 needs the second clause and must not instead demand a PASS (advisory-mode `NO_DATA` soft-skips and `FAIL` proceeds to Phase 7, so a PASS-only test would file the default-mode success as incomplete). Note that the `Stage` row is corroborating, not the test. **Instruct the reader to read the `WORKFLOW_TERMINAL_STATUSES` frozenset from `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`, and do not write the six status literals into this file** — two of the six differ only by a Unicode variation selector and render identically, so a hand copy is both forbidden and easy to get wrong. Acceptance: FR-019, FR-020; SC-010

**Checkpoint**: All four user stories are complete on the Claude variant. This is the settled source Phase 7 mirrors from.

---

## Phase 7: Codex Mirror — one pass, all four stories

**Purpose**: Mirror the settled Claude variant into
`speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`. Layer 8 parity
compares the two, so authoring both from one settled source avoids two rounds of
drift. This phase is ordered after Phases 3–6 by explicit constraint; each task
still carries the story it mirrors.

All eight tasks edit the one Codex file, so none is `[P]`. Every operator-facing
string this feature fixes is **identical on both platforms**; only the invocation
form, the confirmation mechanism name, whether the chain is attempted at all, and
the local documentation idiom may differ (FR-022, SC-011).

- [X] T027 [US1] Mirror `### 3.6 Blind-spot pass (in the worktree)` into the Codex file, between `### 3.5. Bootstrap the worktree (in the worktree)` and `### 4. Run the Grill Me interview (in the worktree)`, carrying the full content of T004, T005, T007–T011 in Codex idiom. **Do not renumber Steps 4 through 8.** The dispatch block must be **byte-identical** to the Claude copy (`contracts/blind-spot-pass.md` §4). Substitute only the platform-forced differences: the identifier is the bare `codebase-analyst`, and the dispatch is `spawn_agent` followed by a bounded `wait_agent` loop until the actual summary is delivered — a status update, an unrelated mailbox wake, or a terminal status without a delivered result is **not** the result — then `close_agent` only when that action is exposed. State that on Codex the consecutive-expired-poll run is the loop's **cue to check the five-minute execution deadline**, not a second independently-triggering bound, and that it has no Claude-side counterpart. Acceptance: FR-001–FR-007, FR-011, FR-002a; SC-011
- [X] T028 [US2] Amend the `Invoke $grill-me ... with a setup-mode marker` bullet list in `### 4. Run the Grill Me interview (in the worktree)` so the scope input carries the T012 labelled block. **Do not disturb the five picker strings pinned by `tests/speckit-pro/layer1-structural/validate-codex-skills.py` that live in this same step**: `picker-first HITL guard`, `request_user_input`, `default_mode_request_user_input`, `Do not ask the Grill Me question as a normal assistant`, and `` If `request_user_input` is absent `` — all five must survive verbatim (research.md R6). No grill-me file is edited. Acceptance: FR-008, FR-009; the five pinned strings still pass Layer 1
- [X] T029 [US2] Insert the post-interview verification and repair after the `If grill-me aborts` paragraph at the close of `### 4`. The Codex variant performs **no** such read today, so this creates one: read the design concept, confirm the `**Blind-spot pass:**` key, and `Edit` the T014 line in when absent, from the values already held. `contracts/blind-spot-pass.md` §9.1 records that this asymmetry is a difference in the two files' **current text**, not a behavioural divergence, so it adds nothing to SC-011's closed list. Acceptance: FR-010, FR-010a
- [X] T030 [US3] Amend the Hard Constraint `Do not run the autopilot at the end. Setup stops once the workflow is ready, committed, and pushed.` to be **conditional on the session's rooting** rather than absolute (`contracts/chain-handoff.md` §7, site 1). This sentence is **not** string-pinned by any validator (research.md R6). Acceptance: FR-022 site 1
- [X] T031 [US3] Amend the `## Output` next-step bullet beginning `the exact next step: start a new Codex task rooted at that worktree, then run` to gain the conditional chain **while keeping its new-task guidance for the ordinary case**. That guidance **is** the Codex hand-off command's rooting precondition, so it must survive as part of the command rather than as commentary beside it (`contracts/chain-handoff.md` §7 site 2, §6.1). Acceptance: FR-022 site 2, FR-015c
- [X] T032 [US3] Preface the two `## Output` prohibition sentences — `Never hand off only the inner workflow path from the parent checkout.` and `Do not suggest running autopilot from main, a detached checkout, or any workspace root other than the generated spec worktree.` — so they apply when the chain does not fire. **Keep both sentences verbatim**; preface, never rewrite. They guard the real hazard FR-022 exists to respect (`contracts/chain-handoff.md` §7, site 3). Acceptance: FR-022 site 3
- [X] T033 [US3] Extend the `## Output` section with the chain, inserting **after the T032 prohibition sentences and before the `## Failure Handling` heading** — the chain and closing report extend `## Output` rather than becoming new numbered steps, so appending at end of file would place them in the wrong section. Carry T017–T021 in Codex idiom: the FR-013a pre-chain check in the guard's own words, the printed what-accepting-does line, the confirmation via `request_user_input` when present, the printed invocation, and the chain as `$speckit-autopilot <workflow-file> --stage plan`. Add the FR-015a condition: **attempt the chain only when the FR-013a check passes; otherwise ask nothing at all and print the hand-off command**, because a Codex task's workspace root is fixed at task start and the ordinary session is rooted at the parent checkout. Record that the `$speckit-autopilot` prefix is a **deviation** from ART-006 §3's table, not a quotation of it (`contracts/chain-handoff.md` §5, spec.md FR-014 Provenance column). Acceptance: FR-012–FR-015c, FR-022; SC-005, SC-006, SC-007
- [X] T034 [US4] Extend the same `## Output` region, still **before `## Failure Handling`**, with the closing report, carrying T022–T026 in Codex idiom: four render triggers, the four-element layout, the closed heading vocabulary, the outcome-line table, the draft-PR line, the artifact index and its read-based existence test, the next-step rule for all three headings, and the completion test. **Same frozenset constraint as T026: instruct the reader to read `WORKFLOW_TERMINAL_STATUSES` from `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`; never write the six status literals here.** Acceptance: FR-016–FR-020; SC-008, SC-009, SC-010

**Checkpoint**: Both platform variants implement one flow. Layer 8 parity and the SC-011 side-by-side read can now be run.

---

## Phase 8: Cross-Cutting — description, fixtures, roadmap

**Purpose**: The reword that both platforms share, the Layer 2 cases that cover
it, and the roadmap amendment the plan reconciled. T037 and T038 touch different
files from each other and from T035/T036, so both are `[P]`.

- [X] T035 In **one edit pass across both** `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` and `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`, replace **sentence 3 only** of the frontmatter `description` with the FR-021 replacement, applying the identical substitution to both so byte-identity holds by construction: `Opens with a blind-spot pass, creates the git worktree, spec branch, Design Concept doc, and populated workflow file, then can chain into planning.` Sentences 1, 2, 4, and 5 stay **byte-identical**; the existing boundary clause naming `/speckit-pro:speckit-autopilot` as the entry point for an existing workflow file stays intact. The result must measure **1015 characters** against the hard 1024 cap, with **no angle brackets**. Acceptance: FR-021; verified by T041 and T042
- [X] T036 Fix the incidental citation defect in `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`: replace `see openai/codex#7480` with the official Codex skills documentation at `https://learn.chatgpt.com/docs/build-skills`, corroborated by `openai/codex#11817` (research.md R11). Keep the surrounding claim and the `$skill-name` placeholder verbatim; change only what the sentence points at. **Do not touch** the same miscitation in `speckit-pro/codex-skills/grill-me/SKILL.md` or `speckit-pro/codex-skills/speckit-coach/SKILL.md` — both are named follow-ups, and editing either would add a production file to a surface FR-022 fixes at two
- [X] T037 [P] Add three cases to **both** `tests/speckit-pro/layer2-trigger/evals/speckit-scaffold-spec-trigger.json` and `tests/speckit-pro/layer2-trigger/codex-evals/speckit-scaffold-spec-trigger.json`, in the existing `{query, should_trigger}` shape, taking each file from 16 to 19 entries (10 positive, 9 negative). The **same three query strings** go in both files and MUST be **ASCII-only**: the two files are not byte-identical today, differing only in whether em dashes are escaped, and an ASCII query keeps each file's own convention intact. Positive 1 exercises the blind-spot capability phrase (scaffold a spec and surface what the roadmap author missed before the interview); positive 2 exercises the chain capability phrase (set up a SPEC-ID and continue straight into planning); the negative is a near-miss stressing "planning" against the preserved boundary — a query about running the plan stage of a workflow file that **already exists**, which must route to autopilot. Write the negative so **precondition contrast** is the deciding signal (scaffold creates a workflow file that does not yet exist; autopilot consumes one that does), not word-avoidance. Do not add cases to any other fixture. Acceptance: FR-021b
- [X] T038 [P] Amend **only** the ART-011 reviewability declaration in `docs/ai/specs/html-artifacts-technical-roadmap.md`, from approximately 4 production files and 162 LOC to **2 production files and 322 LOC** (plan.md § Declared File Operations, "Reconciliation with the roadmap"). Both figures stay under the warn thresholds, so nothing is blocked. **No other roadmap entry and no other roadmap file may be touched**

---

## Phase 9: Verification, Regeneration & Polish

**Purpose**: Regenerate the artifact contract, run the gates, and hand-verify the
three things no automated test covers. T039 must run **after every production
edit**, not only after T035: the `dist/` payloads copy the whole `SKILL.md` body,
so one regeneration covers all four generated copies.

- [X] T039 Run `python3 scripts/refresh-release-artifacts.py` from the repository root, **after T027–T036 have all landed** and **before** the suite. It rebuilds `dist/claude/` and `dist/codex/`, content-syncs the two installed-cache fixtures under `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/`, refreshes the proof-tree hashes, and regenerates the payload-completeness, zero-Bash, and release-readiness evidence. Running the suite against a stale payload produces a false red. **Do not hand-edit any generated file.** The Layer 6 digest chain needs no action, because no agent definition changed (research.md R8)
- [X] T040 Run the full suite from the repository root: `python3 tests/speckit-pro/run-all.py`. It must pass with **zero failures** (constitution IV). The gating checks for this change are Layer 1 structural on both platforms — the 1024-character description cap and the angle-bracket rule in `tests/speckit-pro/layer1-structural/validate-skills.py`, the Codex 8000-word body cap and the five pinned scaffold strings in `tests/speckit-pro/layer1-structural/validate-codex-skills.py` — and **Layer 8 Codex parity** in `tests/speckit-pro/layer1-structural/validate-codex-parity.py`. Layer 2 is `"default": false` in `tests/speckit-pro/suite-manifest.json`, so this run **prints** its commands rather than executing them; T044 is where they run
- [X] T041 Hand-verify the description length on both platforms: measure the final frontmatter `description` value in `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` and `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`. Expect **exactly 1015 characters** on each, 9 under the 1024 cap, with **no angle brackets**. Acceptance: FR-021
- [X] T042 Re-verify that the two frontmatter `description` values are still **byte-identical** after both edits, by diffing them directly rather than inferring identity from the substitution. **No automated test compares them** — `validate-codex-parity.py` asserts version, marketplace, agent, directory, sidecar, and cross-reference parity but never reads a description value (research.md R7) — so this is a required manual step, not an inference. Acceptance: FR-021a
- [X] T043 Hand-verify the Codex body word count in `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md` stayed under the **8000-word** cap. Baseline was ~3250 words; projected additions are 850–1,100 words, so roughly half the cap. Confirm no `references/` directory was created under either scaffold skill (FR-022)
- [ ] T044 Run the **Layer 2 trigger evals as a scheduled manual gate**, after T035 has landed, and record both runs' evidence in the PR: `python3 tests/speckit-pro/layer2-trigger/run-trigger-evals.py speckit-scaffold-spec` and `python3 tests/speckit-pro/layer2-trigger/run-trigger-evals-codex.py speckit-scaffold-spec --run`. Preconditions, each of which makes its runner exit non-zero when absent: the Claude runner needs a `skill-creator` skill directory; the Codex runner needs the `codex` CLI on PATH. **The Claude runner moves the operator's installed skill directory aside and restores it in a `finally` block, so it must never be run from a read-only or background agent.** Re-run the six other fixture files per platform that already carry scaffold-shaped negative cases as regression coverage; they need no new cases, because those skills' descriptions do not change. Acceptance: FR-021b; the "planning" routing risk in plan.md § Residual risks is measured here
- [X] T045 Confirm **no artifact re-declares the terminal-status vocabulary** (FR-020). Read the `WORKFLOW_TERMINAL_STATUSES` frozenset from `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` **at execution time**, then search the two edited `SKILL.md` files and this feature's spec artifacts for its members. The test is whether an artifact **enumerates the vocabulary**, not whether a word from it appears: the set's two bare single-word members are ordinary English that occurs in unrelated prose (report headings such as `## Planning Complete`, and this file's own phase instructions), so those hits are expected and are not re-declarations. The members carrying a leading symbol are the decisive ones — expect **zero** of those, and zero enumerations of the set in any form. Both variants must instead instruct their reader to read that frozenset. This task deliberately does not list the values: writing them here would recreate exactly the copy FR-020 forbids, which is why `contracts/chain-handoff.md` §9.1 omits them too
- [X] T046 Audit the change against SC-012 and the declared boundaries. `git status` and `git diff --stat` must show **9 changed files: 5 hand-edited (2 production `SKILL.md`, 2 Layer 2 fixtures, 1 roadmap) and 4 generated**. Confirm zero new production files; zero new or edited agent definitions under `speckit-pro/agents/` or `speckit-pro/codex-agents/`; zero files touched under `speckit-pro/skills/grill-me/` or `speckit-pro/codex-skills/grill-me/`; zero new scripts or runner helpers; no `references/` directory under either scaffold skill; and scaffold's `allowed-tools` still exactly `Read Edit Write Skill Agent ToolSearch` on both platforms. Acceptance: SC-012, FR-002, FR-022, FR-023
- [ ] T047 Generate the PR review packet from `spec.md` § PR Review Packet Requirements, covering all nine required sections: what changed, why, non-goals, review order, scope budget (322 LOC, 2 production files, 9 changed files of which 4 are generated, within budget, one slice), traceability mapping each requirement group to its edit sites and verification evidence, verification evidence (T040 suite result, T041–T043 hand measurements, T044 Layer 2 evidence, T045 frozenset check), known gaps, and rollback notes. Name both deferrals explicitly: **ART-007** owns draft-PR creation and therefore the closing report's PR URL, and the **archive-hygiene question** of where the ART-006 chain contract should live. Use `feat(speckit-pro): ...` for the PR title and include exactly one non-empty ```release-note fence

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies. All three tasks are read-only.
- **Phase 2 (Foundational)**: Depends on Phase 1. **BLOCKS all user stories** — the `### 3.6` section and its verbatim dispatch block must exist before any pass prose can be positioned against them.
- **Phase 3 (US1)**: Depends on Phase 2.
- **Phase 4 (US2)**: Depends on Phase 3 (T012's block references the T010 status lines; T014's header line reuses the T010 `<reason>` clause).
- **Phase 5 (US3)**: Depends on Phase 2 only in principle, but is sequenced after Phase 4 because all tasks edit the same file.
- **Phase 6 (US4)**: Depends on Phase 5 (T022 inserts `### 10` after `### 9`; T025's decline branch cites T021's hand-off command).
- **Phase 7 (Codex mirror)**: Depends on Phases 3–6 being **complete and settled**. Authoring both variants from one settled source is what avoids two rounds of Layer 8 parity drift.
- **Phase 8 (Cross-cutting)**: T035 and T036 depend on Phase 7 (same files). T037 and T038 depend on nothing in Phases 2–7 and may run at any point after Phase 1.
- **Phase 9 (Verification)**: T039 depends on **every** production edit (T004–T036). T040–T043 and T045–T046 depend on T039. T044 depends on T035 and T037. T047 depends on all of the above.

### User Story Dependencies

- **US1 (P1)**: The MVP. Depends only on the Foundational phase. Independently valuable — findings printed to the operator improve the interview even if nothing else lands.
- **US2 (P1)**: Depends on US1 for the findings and the status-line values it records. AC-11.1 names both halves in one criterion.
- **US3 (P1)**: Independent of US1 and US2 in behaviour; sequenced after them only by same-file ordering.
- **US4 (P2)**: Depends on US3's outcomes to have anything to report.

### Within Each Story

- Prose lands in the contract's own section order, and every task names its position relative to a fixed anchor, so a section never assembles out of order.
- Claude before Codex, always. Layer 8 parity compares the two.
- The description reword lands before the Layer 2 evals run.
- `refresh-release-artifacts.py` runs after every production edit and before the suite.

### Parallel Opportunities

Genuinely parallel work is limited, and the count is reported honestly rather
than inflated. `[P]` requires **different files**, and all 16 edit sites
live in just two files that must be written in a fixed order.

- **T002 and T003** — read-only, no writes, no shared file.
- **T037 and T038** — the two Layer 2 fixtures and the roadmap entry; different files from each other and from every production edit.

**Four `[P]` tasks out of 47.** Everything else is sequential by file or by
explicit ordering constraint.

---

## Parallel Example: Phase 8

```text
# These two touch entirely different files and share no dependency:
Task T037: "Add three ASCII-only cases to both Layer 2 scaffold trigger fixtures"
Task T038: "Amend the ART-011 reviewability declaration in the html-artifacts roadmap"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup — confirm all 16 anchors.
2. Complete Phase 2: Foundational — the `### 3.6` section and its verbatim dispatch block. **CRITICAL, blocks all stories.**
3. Complete Phase 3: User Story 1 on the Claude variant.
4. **STOP and VALIDATE**: scaffold a roadmap entry and confirm at most five ranked findings with an explicit set-aside count print before the first interview question, on every path.

US1 alone is a shippable increment: findings printed to the operator improve the
interview even before the seeding, the chain, or the closing report exist.

### Incremental Delivery

1. Setup + Foundational → the section exists.
2. Add US1 → validate independently → the pass works (MVP).
3. Add US2 → validate independently → findings survive into the interview and the record.
4. Add US3 → validate independently → one confirmation, chain or clean stop.
5. Add US4 → validate independently → one honest closing report.
6. Phase 7 mirrors all four into Codex in one pass.
7. Phase 8 + Phase 9 close the cross-cutting surface and every gate.

### Why the Codex mirror is not parallelised

Two developers writing the two variants concurrently would produce two rounds of
Layer 8 parity drift, because SC-011 requires every operator-facing string this
feature fixes to be identical on both platforms. One settled source, then one
mirror pass, is cheaper than reconciling two independent drafts.

---

## Notes

- `[P]` = different files, no dependencies. All 16 edit sites live in just two files, written in a fixed order, so `[P]` is rare here by construction, not by oversight.
- **There is no Layer 4 fixture to write.** Nothing this feature adds is executable — every change is prose in two `SKILL.md` files (FR-023, Q21) — so no fixture can assert against the two behaviours directly. This is a recorded design decision, not an omitted task.
- **UAT is not a task in this file.** The run is strictly interactive, so UAT happens at UAT time against the runbook. The five ux-domain confirmations plan.md lists (the sentinel's one-word spelling surviving in emitted output, the printed line preceding the confirmation, the one command appearing identically in three places, every heading ending on a defined next step, and the closing report rendering on the Codex ordinary path) belong to the UAT runbook and the PR packet, not here.
- Commit after each task or logical group. Do not merge; PR creation and review are separate.
- The `## Scaffold Complete` report is a top-level `##` heading sitting **between** Steps 7 and 8 in the Claude file, not nested inside Step 7. spec.md FR-016, plan.md § Execution Flow, and `contracts/chain-handoff.md` §1 all now say so; earlier drafts of the plan and the contract said "inside Step 7", which would send an implementer to the wrong anchor. The anchors are still unique, so T016 cites the literal strings rather than a step number.

## Where a task is deliberately under-determined

Three places. Each is a fact fixed without a literal sentence, so the
implementer writes the wording and the reviewer checks it against the fact.

1. **T030's amended Hard Constraint.** `contracts/chain-handoff.md` §7 fixes that `Do not run the autopilot at the end.` becomes *conditional on the session's rooting* but does not fix the replacement sentence. Any wording is acceptable that makes the constraint conditional and leaves FR-015a's behaviour unchanged.
2. **T018's what-accepting-does line.** FR-013 fixes the **three facts** the line states and forbids a fourth, but not the sentence. Any wording carrying exactly those three facts, printed and carrying no options, satisfies it.
3. **T037's three query strings.** FR-021b and plan.md fix each case's *intent* and the ASCII-only rule, and require precondition contrast to be the negative's deciding signal, but no artifact fixes the literal queries. They are authored at implementation time and confirmed by the T044 run.

Two further strings are fixed in shape but confirmed empirically rather than
statically: the five FR-006 operator status lines are transcribed verbatim from
`contracts/blind-spot-pass.md` §6, and the contract itself notes the exact
strings are confirmed through the UAT runbook.

---

## Why two tasks remain unchecked

45 of 47 are complete. The two open ones are deferrals with reasons, not
oversights, and neither may be checked by an agent.

**T044 — the Layer 2 trigger evals.** A scheduled manual gate the operator runs.
Layer 2 is declared `"default": false` in `tests/speckit-pro/suite-manifest.json`,
so the full suite prints its commands rather than running them. The Claude runner
moves the operator's installed skill directory aside and restores it in a
`finally` block, which is not something a background agent should do to a live
environment. Checking this box without the runs would be a phantom completion of
the one gate that can detect the spec's largest residual risk: whether the word
"planning", newly introduced into scaffold's description, pulls prompts away from
the sibling autopilot skill.

**T047 — the PR review packet.** Authored at pull-request creation time from the
committed evidence, which is the post-implementation step that owns it.

## A note on the test count

The full suite reads **7378/7378**, exactly equal to the recorded G0 baseline
rather than above it. That is correct here and is not a missing-tests finding:
FR-023 prohibits new executable machinery, so this spec adds no runnable test by
construction, and the six Layer 2 cases it does add live in `default: false`
fixtures that the suite never executes. The suite result proves no regression,
which is the whole of what it can prove for a prose-only change.
