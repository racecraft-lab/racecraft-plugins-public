# Tasks: Feedback Sweep, slice 1 of 2 — the checkpoint

**Input**: Design documents from `specs/art-008-feedback-sweep/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Required. The spec asks for TDD explicitly (FR-008a, FR-008b pin a
golden-fixture corpus), so every helper branch and every fixture path gets its
failing test before its implementation.

**Reviewability**: The plan's hand-derived budget is **~630 reviewable LOC
(515–830), 7 production files, 14 authored files, 1 primary surface**. That is
**WARN on reviewable LOC** (630 against 400) and **WARN on production files**
(7 against 6). The high end, after the error-handling pass, reaches **810–830
and crosses the 800 block while the midpoint stays under it.** T014 is the
mandatory checkpoint that forces the operator decision before implementation
starts. No task below expands the file set past the plan's Declared File
Operations block.

**Organization**: Tasks are grouped by user story so each story can be
implemented and tested independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: `[US1]`, `[US2]`, `[US3]` — user-story phases only
- Every path is repository-relative

## Path Conventions

Plugin source under `speckit-pro/`, repository-only validation under
`tests/speckit-pro/`, planning artifacts under
`specs/art-008-feedback-sweep/`. No new directories under plugin source; one
new fixture directory, `tests/speckit-pro/unit/fixtures/feedback-sweep/`.

## Two hard boundaries

1. **Neither `SKILL.md` may be edited.** The Codex autopilot skill body is
   **7997 words against a hard 8000-word Layer 1 cap — three words of
   headroom** (plan, "Two files deliberately absent from this block"). No task
   below adds a line to `speckit-pro/skills/speckit-autopilot/SKILL.md` or
   `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`, and none may be
   added. An implement-phase agent that "helpfully" registers the new helper in
   either skill index fails Layer 1.
2. **The eight generated paths are regenerated, never hand-edited.** The four
   `dist/` copies, the runner `.sha256` and `.manifest.json`, and the two
   installed-cache copies are covered by T074 and T075 alone. No authoring task
   below names any of them.

---

## Phase 1: Setup (design-artifact corrections)

**Purpose**: Three settled decisions changed what gets built and the contract
still shows the pre-decision shape. Correcting the artifacts first means the
implementation tasks read off a correct interface rather than carrying the
correction in prose.

- [ ] T001 [P] Change the export record from the singular `export.matched_line` to `export.matched_lines`, a list of 1-based integers in ascending order, in the Response block and the Recognition section of `specs/art-008-feedback-sweep/contracts/sweep-pr-feedback.md`. Acceptance: FR-007f's "reports **all** matched line numbers in ascending order rather than a single one" is satisfied by the contract, and the security checklist's CHK049 conflict is closed. A body carrying two registered leads is an ordinary workflow this feature's own design invites, not an adversarial edge case.
- [ ] T002 [P] Change `export.matched_line` to `export.matched_lines` (array of integers, ascending) in the swept-comment field table at `specs/art-008-feedback-sweep/data-model.md`. Acceptance: data-model and contract agree; no artifact still describes a single matched line (FR-007f).
- [ ] T003 Add the `self_login` non-empty rule to "Preconditions the helper validates" in `specs/art-008-feedback-sweep/contracts/sweep-pr-feedback.md`: the value MUST be a non-empty string **after surrounding whitespace is stripped**; absent, empty, or whitespace-only returns `invalid_input`. Add the matching Diagnostics row. Acceptance: FR-006b's validation half is itemized rather than implied by the Input-rules "Required: Yes" column. Depends on T001 (same file).
- [ ] T004 Add `feature_dir` to the request's `inputs` block and its Input-rules row in `specs/art-008-feedback-sweep/contracts/sweep-pr-feedback.md`, recording that it **arrives as an explicit input and is never inferred**, because the one inference mechanism available keys off a branch-name pattern this feature's own branch (`art-008-feedback-sweep`) does not match. Record the FR-012b rule-2 write-point check as a named surface of this operation. Acceptance: FR-012c's explicit-input requirement is on the interface, not only in the spec. Depends on T003 (same file). **Scope note**: the contract as shipped carries neither the input nor the check; see the Known Interface Gap section below before starting.
- [ ] T005 [P] Register `tests/speckit-pro/unit/test-feedback-sweep-parse.py` in `tests/speckit-pro/suite-manifest.json` with `baseline: null`, matching the shape of the existing `test-speckit-pro-read-only-helpers` entry. Acceptance: the new test is selected by `python3 tests/speckit-pro/run-all.py`.
- [ ] T006 [P] Create `tests/speckit-pro/unit/fixtures/feedback-sweep/comment-corpus.json` and `tests/speckit-pro/unit/fixtures/feedback-sweep/expected-envelopes.json` as empty, well-formed skeletons keyed by case name. Acceptance: the directory is named for durable behavior, never for the spec id; both files parse as JSON.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The helper must exist, be registered on all seven touch points,
and be reachable by the harness before any story branch can be tested.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T007 Append `"sweep-pr-feedback"` to `EXPECTED_HELPERS` (line 55) and to `NO_BASH_ANCESTOR` (line 83) in `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py`. Acceptance: the test now FAILS on the missing registry entry and the missing fixture record — that failure is the red state the rest of this phase turns green. The helper is new behavior with no Bash ancestor, so `registry.py` records `None` for the script and `python_only` as the comparison mode.
- [ ] T008 Insert one record for `sweep-pr-feedback` into `tests/speckit-pro/unit/fixtures/read-only-helpers/fixture-manifest.json` **at the array position matching its position in `EXPECTED_HELPERS`**. Acceptance: both sibling assertions pass — `fixture_ids == EXPECTED_HELPERS` compares **in order** (line 361) while the registry-dispatch assertion compares against `sorted(EXPECTED_HELPERS)` (line 238). The two differ deliberately; satisfy both. Depends on T007.
- [ ] T009 [P] Create the canonical request fixture `tests/speckit-pro/unit/fixtures/read-only-helpers/requests/sweep-pr-feedback.json` carrying `schema_version`, `request_id`, `helper_id`, `operation`, `mode: read_only`, and the four inputs `workflow_file`, `self_login`, `feature_dir`, `pr_observation`. Acceptance: `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/read-only-helpers/requests/sweep-pr-feedback.json` reaches the helper. Use `PYTHONPATH=speckit-pro`, never the installed plugin cache — a run through the cache reports a tree that is not the one you edited.
- [ ] T010 Add the `sweep_pr_feedback(inputs, repo_root)` skeleton to `speckit-pro/speckit_pro_runner/helpers/read_only.py`, modeled on `resolve_autopilot_stage` (line 1472): takes an orchestrator-supplied observation, classifies it offline, reports without deciding. Acceptance: returns a `stdout_json` envelope with `tool`, `surfaces_read`, `counts`, `candidates`, `excluded`. It runs no `gh`, touches no network, writes no file, and assigns no class.
- [ ] T011 Add the three registration touch points in `speckit-pro/speckit_pro_runner/helpers/read_only.py`: the allowed-inputs map entry `{"workflow_file", "self_login", "feature_dir", "pr_observation"}` beside line 256, the argument-derivation branch beside the `resolve-autopilot-stage` branch at line 341, and the dispatch-table entry beside line 4466. Acceptance: contract Registration-checklist rows 2, 3, and 4 are satisfied. Depends on T010 (same file).
- [ ] T012 [P] Add one `HelperEntry` for `sweep-pr-feedback` to `speckit-pro/speckit_pro_runner/helpers/registry.py`, matching the `resolve-autopilot-stage` shape at lines 181–188, with `None` for the script and `python_only` as the comparison mode. Acceptance: contract Registration-checklist row 5; the registry-dispatch assertion passes.
- [ ] T013 Write the harness manifest diagnostics text for the helper in `tests/speckit-pro/unit/fixtures/read-only-helpers/fixture-manifest.json`. Acceptance: **no remediation or rollback string contains the substring `bash` in any casing** — the harness manifest rejects it. Depends on T008.
- [ ] T014 **Reviewability checkpoint — operator decision required before Phase 3.** Record in the workflow file which lever was taken against the plan's budget: midpoint **~630 reviewable LOC**, high end **810–830 which crosses the 800 block**, production files **7 against a warn of 6 and a block of 8**. The three levers the plan names and deliberately does not choose among are (a) defer the serialization-family registry rows — `feature-flags`, `prompt-tuner`, `triage-board` — saving an estimated 15 to 30 lines at the cost of FR-007b's "every shipped template that declares an export", (b) accept the block explicitly with a ratified exception, or (c) re-slice. Acceptance: one lever is recorded with its reasoning; the plan's rejected split (read-path-only 1a) is not silently revived, because it produces a checkpoint that reads feedback and acts on none of it.

**Checkpoint**: Helper registered on all seven touch points, harness green on
registration, budget decision recorded. Story work can begin.

---

## Phase 3: User Story 1 — The sweep reads and classifies draft-PR feedback (Priority: P1) 🎯 MVP

**Goal**: Read both comment surfaces, keep only write-capable authors,
recognize artifact exports by registered lead sentence, skip already-logged and
self-reply comments, and give every survivor exactly one class.

**Independent Test**: Point the sweep at a draft pull request carrying a
trusted plain comment, a trusted exported markdown block, an untrusted comment,
a comment already recorded from a prior run, and a resolved thread. Confirm the
run reports exactly the trusted, unrecorded, unresolved items as classified
candidates and names every excluded comment with its exclusion reason.

### Tests for User Story 1 ⚠️

> **Write these FIRST and confirm they FAIL before implementing.**

- [ ] T015 [US1] Create `tests/speckit-pro/unit/test-feedback-sweep-parse.py` with the golden-fixture harness: load `comment-corpus.json`, run each case through the helper, compare against `expected-envelopes.json`. Acceptance: the file runs standalone as `python3 tests/speckit-pro/unit/test-feedback-sweep-parse.py`; it is named for durable capability, never for the spec id.
- [ ] T016 [US1] Add corpus cases pinning **every registered sentence in both shapes** to `tests/speckit-pro/unit/fixtures/feedback-sweep/comment-corpus.json`: the verbatim payload shape with the lead on line four behind `Artifact: <title>`, a feature line, and a blank line; and the same paste header-trimmed. Acceptance: FR-007, FR-008a. Depends on T015.
- [ ] T017 [US1] Add corpus cases for normalization and truncation: a body delimited with carriage returns, a body at the 8192-byte budget with `truncated` true, and a body **over** budget expecting `invalid_input` naming the offending comment id. Acceptance: FR-008, FR-008a; the helper validates rather than silently re-truncating, because the runner's `BOUNDED_TEXT_INPUT_BYTES` rejects the whole request rather than the offending string. Depends on T016.
- [ ] T018 [US1] Add one corpus case per excluded author-association value — CONTRIBUTOR, FIRST_TIMER, FIRST_TIME_CONTRIBUTOR, MANNEQUIN, NONE — each expecting `untrusted_author`, plus a ninth-value case expecting `invalid_input` as a malformed observation rather than an untrusted author. Add one **admitted** case per allowed value too — OWNER, MEMBER, COLLABORATOR — each expecting a candidate rather than an exclusion, so all eight values of the closed enum are pinned in the direction the filter actually decides them. FR-008a names the five excluded values as a minimum; without the three admitted cases an allowlist that wrongly rejected `MEMBER` would pass every fixture here, because nothing else in the corpus varies the association across the trusted set. Acceptance: FR-005, SC-004, FR-008a's "each of the five excluded association values". Depends on T017.
- [ ] T019 [US1] Add the self-reply corpus cases: the marker at position 0 with a matching author expecting `self_reply`; the same marker with a **different** author expecting a candidate; a **quoted** reply whose marker is not at position 0 expecting a candidate; and the marker carrying a **different comment id** after its fixed prefix, asserting the FR-006 anchor still matches on the prefix. Acceptance: FR-006, FR-006a, FR-008a; anchoring is what keeps a reviewer who quotes a sweep reply to disagree with it visible. Depends on T018.
- [ ] T020 [US1] Add the `self_login` validation cases: empty string and whitespace-only, each expecting `invalid_input`. Acceptance: FR-006b's validation half; an empty account matches **no** real comment author, so the author condition is permanently false and **no comment is ever excluded as a self-reply** — the rule is disabled, not narrowed to its marker half. Depends on T019.
- [ ] T021 [US1] Add the recognition-edge corpus cases: a shared empty-export sentence expecting `template_ambiguous` true and `template_id` null; one recognized export on **each** of the two surfaces; a body carrying **two** registered lines asserting both appear in `matched_lines` in ascending order; a comment whose author cannot be resolved; and a comment carrying no registered sentence expecting `export` null. Add one case per **serialization-family** template — `triage-board`, `feature-flags`, `prompt-tuner` — because those three carry **no lead sentence at all** and so are reached by a recognition path none of the cases above exercises. Their paste opens with a three-line header block, `# <Name> Export` / `Artifact: <template-id>` / `Export kind: markdown`, and the template id is read from the second line rather than inferred from a sentence. Assert each resolves its own `template_id` with `template_ambiguous` false, and that a body carrying the header lines in the wrong order is **not** recognized. Acceptance: FR-007a, FR-007b, FR-007f, FR-008a. Depends on T020.
- [ ] T022 [US1] Add the already-logged cases: a comment id present in the Feedback Sweep Log expecting `already_logged`, a resolved thread expecting `thread_resolved`, and a workflow file carrying **no** Feedback Sweep Log expecting an empty skip set (the first-sweep case). Add a log row whose comment-id cell cannot be read, expecting a stop. Acceptance: FR-009, FR-009a. Depends on T021.
- [ ] T023 [US1] Add the derive-from-manifest registry test to `tests/speckit-pro/unit/test-feedback-sweep-parse.py`: read `speckit-pro/artifact-gallery/manifest.json` and the template sources, derive every template the manifest says exports in every kind it declares, and assert the registry matches. Pin the skip list as exactly `["uat-walkthrough"]`, which the manifest declares as exporting both kinds but which has **no template file**. **Skip only on both conditions — named AND file still absent.** A template that goes missing is not on the list, so it fails; and if `uat-walkthrough` later ships its file it stops being skipped and must be derived, because it declares a `prompt` kind and a name-only skip would leave that imperative lead unregistered (FR-007c). Acceptance: FR-008a; a reworded lead or a new exporting page fails this test instead of silently disabling recognition. **The test reads templates and edits none**, so it crosses no non-goal and triggers no payload regeneration.
- [ ] T024 [US1] Add the two trust-boundary assertions to `tests/speckit-pro/unit/test-feedback-sweep-parse.py`. First: **no comment body appears anywhere in the helper's output** — assert the records carry id, surface, author, association, truncation flag, and export metadata and **no body field at all**, so a later field addition cannot quietly reintroduce the leak. Second: an excluded comment's body and every registered line **never appear in an assembled analyst payload**, asserted against a captured payload. Store the captured payloads and captured commands as sibling top-level keys inside `expected-envelopes.json` rather than creating an undeclared fixture file. Acceptance: FR-008b. Depends on T022.

### Implementation for User Story 1

- [ ] T025 [US1] Implement request validation in `sweep_pr_feedback()` in `speckit-pro/speckit_pro_runner/helpers/read_only.py`: `pr_observation.ok` must be the JSON literal `true` (a truthy non-`true` value is not a successful read, per the `observation_pull_requests` precedent); `surface` closed to `review_thread` and `pr_conversation`; `author_association` closed to the eight GitHub values; every body at most 8192 bytes as UTF-8; `workflow_file` readable. Acceptance: T017 and T018 go green; each failure returns `invalid_input` naming the offending comment id. Depends on T014.
- [ ] T026 [US1] Implement `self_login` validation in the same helper: non-empty after stripping surrounding whitespace, otherwise `invalid_input`. Acceptance: T020 goes green. The helper cannot go further than presence — its contract forbids reaching the network, so it has no second independently sourced value to compare against; verification is the orchestrator's job through provenance, not the parse's through checking (FR-006b). Depends on T025 (same file).
- [ ] T027 [US1] Implement the workflow-file skip-set read: parse the Feedback Sweep Log's comment-id column and nothing else. A file with no such table yields an empty skip set. **A row whose comment-id cell cannot be read stops the run** rather than being guessed at, because an unreadable key is indistinguishable from an absent one and the two guesses fail in opposite directions — reading it as absent re-processes a handled comment, reading it as present skips an unhandled one. Acceptance: T022 goes green; FR-009, FR-009a. Depends on T026 (same file).
- [ ] T028 [US1] Implement line-ending normalization (CRLF and CR to LF) and per-comment truncation reporting. Acceptance: the same observed comment data always yields the same candidate set; T017 goes green; FR-008, SC-005. Depends on T027 (same file).
- [ ] T029 [US1] Implement the author-association allowlist — OWNER, MEMBER, COLLABORATOR — **ahead of everything else in the helper**, and return `excluded` records carrying `reason: untrusted_author`. Acceptance: candidate records carry id, surface, author, association, truncation flag, and export metadata and **no body**, so an untrusted comment's text is absent from the helper's output by construction rather than by an orchestrator remembering to drop it (plan, Trust Boundary mechanism 1). The allowlist is a **proxy** for write access, not a permissions check. T018 goes green; FR-005, FR-008b. Depends on T028 (same file).
- [ ] T030 [US1] Implement the two-condition self-reply test: the fixed HTML-comment prefix `<!-- speckit-pro:feedback-sweep -->` matched **anchored at position 0**, AND an exact match between the comment author and `self_login`. Both conditions are required. Every self-reply exclusion is reported in `excluded` with `reason: self_reply`, so a marker collision drops a candidate **visibly**. Acceptance: T019 goes green; FR-006, FR-006a. Depends on T029 (same file).
- [ ] T031 [US1] Build the export lead registry in `speckit-pro/speckit_pro_runner/helpers/read_only.py`: 14 lead sentences (7 note-payload templates × 2 kinds), the 6 distinct empty-export sentences, and header identities for the 3 serialization-family templates, each entry carrying template id and kind. Cover **every shipped template that declares an export, in every kind it declares**. Acceptance: T023 goes green; FR-007a, FR-007b. **No shipped gallery template or payload copy is edited** — recognition is by registry, not by template change. Depends on T030 (same file).
- [ ] T032 [US1] Implement recognition: match registered sentences as **whole-line exact matches against the body's first ten lines**, after normalizing line endings and stripping trailing whitespace. The lead is not the first line — a verbatim paste puts it on line four — and the ten-line window survives a reviewer trimming the header and a template later adding one. Report `template_id` null with `template_ambiguous` true when the matched sentence is declared by more than one template. Acceptance: T016 and T021 go green; FR-007, FR-007a. Depends on T031 (same file).
- [ ] T033 [US1] Implement `matched_lines`: report **every** matched registered line number in ascending order, never the first alone. Acceptance: T021's two-lead case goes green; FR-007f. Removing only the first would leave the second sitting inside the delimited block, which is the first-match sanitization failure that recurs across input-validation defects. Depends on T032 (same file).
- [ ] T034 [US1] Assemble the response envelope and assert the invariant **`counts.observed == len(candidates) + len(excluded)`**. `candidates` are trusted, unrecorded, non-self-reply comments in the order observed, with `export` null when no registered line matched. `excluded` carries exactly one reason per comment from the closed set `untrusted_author`, `self_reply`, `already_logged`, `thread_resolved`. Ordering follows the observation; no set iteration reaches the output. Acceptance: nothing is dropped without appearing on one of the two lists, which is what backs SC-001; FR-008, SC-005. Depends on T033 (same file).
- [ ] T035 [US1] Add the Phase 7 setup sweep sequence to `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`, inserted **ahead of** "Phase 7 Setup: Open the Implementation-Notes Record" (line 1210). Acceptance: FR-001. The sweep **adds no row to the Workflow Overview table** and changes neither the phase-coverage guard's governed phase-id list, the stage-to-phase map, nor the workflow template (FR-002). Hold the reference to the sequence rather than restating the spec's rationale in it — the budget depends on it.
- [ ] T036 [P] [US1] Mirror the sweep sequence into `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`, inserted **ahead of** the line "**Open the implementation-notes record before the first task is dispatched.**" (line 933). Acceptance: FR-001, FR-003 — identical behavior for the same input, at roughly 70% of the Claude reference's length, which is the measured ratio between the two reference sets. Different file from T035, so parallel-safe.
- [ ] T037 [US1] Document the two `gh` reads in both phase-execution references: **every review thread whose resolved flag is false and every pull-request conversation comment**, never review summary bodies; both **paginated to exhaustion**; both requesting the `authorAssociation` field explicitly, because no shipped query requests it today and FR-005's filter has no input unless this read supplies it. **No comment text reaches a shell argument in either direction** — reads pass their query by file or by structured argument. Acceptance: FR-004, FR-004a, FR-004b, SC-009. This corrects the nearest shipped precedent, which caps at a fixed page with no pagination and interpolates comment text into a command string. Depends on T035 and T036.
- [ ] T038 [US1] Document the all-or-nothing observation rule in both phase-execution references: the two reads are **one observation**, succeeding only when both surfaces are read to exhaustion. Three failures fall under it — one surface readable and the other not, a page failing partway through pagination, and output that cannot be parsed. **A failed observation is discarded rather than swept**: zero rows, zero replies, zero commits, and a stop. Nothing needs unwinding because every read precedes every write. Acceptance: FR-004c, SC-011. Depends on T037.
- [ ] T039 [US1] Document `self_login` provenance in both phase-execution references: the orchestrator reads the account from the **live authenticated session at call time**, never from configuration or a remembered value, the same way FR-004a requires the author-association field be read fresh. Acceptance: FR-006b's provenance half; no shipped reference documents how the orchestrator learns its own login, so nothing today guarantees the value arrives correct. Depends on T038.
- [ ] T040 [US1] Document the classification loop in both phase-execution references: it iterates **`candidates` and nothing else**, and a body is read out of the captured observation **only for an id present in that array**. No path enumerates the observation directly. Acceptance: plan Trust Boundary mechanism 2 — without this, mechanism 1 filters an envelope while the orchestrator reads around it, leaving the filter real and bypassed at the same time. FR-008b's second assertion is the fixture that checks it. Depends on T039.
- [ ] T041 [US1] Document the four-value classification rule in both phase-execution references: every trusted, unrecorded comment takes **exactly one** class from the closed set amended, answered, deferred, no action. The **comment** is the unit, so a recognized export carrying several distinct objections still yields one class, one row, one reply. When one comment's objections warrant different classes, **`amended` wins**, and every non-dominant objection is named in the disposition and in the reply so nothing is silently dropped. **Recognition never forces a class**, the one exception being the empty-export form, which carries no objections and takes `no action`. Acceptance: FR-010, FR-007d. The tie-break is fixed rather than stylistic because FR-003 rules out any non-fixed tie-break. Depends on T040.
- [ ] T042 [US1] Document the recognized-export analyst payload in both phase-execution references: for a recognized comment the payload is the helper's export record — template id, kind, anchors — **plus the body with every line named in `matched_lines` removed**, the metadata standing where the removed line was. The remainder is **delimited and labelled as reviewer-supplied data**, never concatenated into the prompt as instruction. **One implementation constraint, because getting it wrong silently corrupts the body: removal indexes the line-ending-normalized original lines, never the trailing-whitespace-stripped copies used for comparison.** The two differ, and indexing the wrong one misaligns the reconstructed remainder. Acceptance: FR-007c, FR-007e, FR-007f. A registry entry that only tags the comment while the raw body still reaches the analyst does **not** satisfy FR-007c. **Delimiting is the boundary; removal is defence in depth — if cost ever forces one out, removal goes and delimiting stays.** Depends on T041.
- [ ] T043 [US1] Document the convergence invariant in both phase-execution references and add its fixture assertion to `tests/speckit-pro/unit/test-feedback-sweep-parse.py`: a run's **work set** is the comments that pass the trust filter, are absent from the log, and are not excluded as self-replies. **Every run either shrinks that set or leaves it unchanged; no run may grow it.** Any future rule that writes to either comment surface must be tested against this. Name the one path that does not shrink: a comment whose consensus round returns a human-review outcome takes no class and writes no row, so it is in the set again next run and stops that run too — bounded by a human rather than by a counter, and **no attempt counter is introduced** because a per-comment counter would need the state-file mirror FR-013 forbids. Acceptance: FR-006a, FR-006c, SC-013. Depends on T042.

**Checkpoint**: US1 is independently testable — the helper classifies a mixed
corpus deterministically and both references carry the read, the filter, and
the classification rules.

---

## Phase 4: User Story 2 — Amendments run through consensus, get recorded, and stop for re-review (Priority: P2)

**Goal**: Route only `amended` through consensus, apply and commit each edit,
write the durable records, reply once per handled comment, then stop or
proceed.

**Independent Test**: Give the sweep one trusted comment that clearly warrants
a plan change and one that does not. Confirm exactly one amendment commit
lands, both comments get a reply and a log row, only the amendment gets a
Consensus Resolution Log row, and the run stops with a re-review report. Re-run
with no new comments and confirm it proceeds into task work.

### Tests for User Story 2 ⚠️

- [ ] T044 [US2] Add the failure-path corpus cases to `tests/speckit-pro/unit/fixtures/feedback-sweep/comment-corpus.json`: a read that fails on the second surface and one that fails mid-pagination, both asserting **zero rows, zero replies, zero commits**; a push failure after an amendment commit, asserting **no row and no reply followed it**; a reply that fails on one surface, asserting the comment is owed a reply and that a re-run posts **exactly one**; a comment already carrying a sweep reply, asserting **no second one**; and a human-review consensus outcome, asserting a Consensus Resolution Log row, **no** Feedback Sweep Log row, and a stop. Acceptance: FR-008a's failure-path half. Each of these is a stop or a recovery whose whole value is behaving correctly when something else has already gone wrong, which is exactly the condition a hand-run check never reaches. Depends on T024.
- [ ] T045 [US2] Add the composed-interrupt case to the corpus: a run that records two amendments and fails to push a third, asserting **two rows written, zero replies posted, one local unpushed commit**, and that the next run posts both owed replies and re-enters consensus on the third. Acceptance: SC-013's composed case, FR-015c. Depends on T044.
- [ ] T046 [US2] Add the log-shape cases to the corpus: a disposition cell containing **a pipe and a newline**, asserting every later column including `CRL #` stays readable in its own position; and a comment whose author cannot be resolved, asserting a complete row with the `Author` cell saying so explicitly rather than sitting blank. Acceptance: FR-013, SC-010 — both are found-and-fixed defects, not hypotheticals. Depends on T045.
- [ ] T047 [US2] Add the captured-command reply assertions to `tests/speckit-pro/unit/test-feedback-sweep-parse.py`: exactly one reply per handled comment with no handled comment at zero and none at two; every reply opening with the marker at position 0; the `amended` reply naming artifact, section, and commit while the other three name none of those; **every body passed by file path** with no comment or reply text in any command string; and a conversation reply naming the comment it answers. Acceptance: FR-015, FR-015a, SC-002, SC-008, SC-009. Replies sit outside the runner's determinism guarantees, so they are proved against captured commands, not against a golden helper response. Depends on T046.

### Implementation for User Story 2

- [ ] T048 [US2] Document consensus routing in both phase-execution references: **only `amended`** routes through the category-routed consensus protocol; `answered`, `deferred`, and `no action` never invoke consensus. Acceptance: FR-011. Depends on T043.
- [ ] T049 [US2] Document the human-review outcome in both phase-execution references. All three ways consensus fails to answer — all three analysts disagreeing after Round 2, a Round-1 escape whose Round 2 still cannot resolve, and an analyst that fails its single retry — land on one behavior; only the report names which occurred. **No edit, no class, no sweep row**: writing no row is what makes the comment a candidate again once a human has resolved it, because the skip key is the log's comment-id column and nothing else. It surfaces as one Consensus Resolution Log row instead, `Type` `Sweep`, its item cell naming the comment id, and it **COUNTS** toward the Round-2 escape-rate metric. **It stops the run whether or not anything was amended**, and when other items amended in the same run it is the same stop and one report, not two. **Other items in the batch still complete** — resolved items are edited, committed, recorded, and replied to normally. Acceptance: FR-011a. Depends on T048.
- [ ] T050 [US2] Document the amendment commit protocol in both phase-execution references: **one commit per amendment**, never a single run-wide blob, because a row names its commit, a reply names the amending commit, and the stop reports a commit range — none of which survive collapsing. Each amendment commit **stages exactly the one artifact path it amended, never a directory.** Flag the specific hazard: the sweep is a **Phase 7 setup step, and Phase 7 is the one phase whose existing commit path uses `git add -A`**; an amendment commit that inherits that pattern would stage the entire worktree and defeat the edit-surface allowlist at the last step. Acceptance: FR-012, FR-012b's staging rule. Depends on T049.
- [ ] T051 [US2] Implement the FR-012b rule-2 edit-surface check in `speckit-pro/speckit_pro_runner/helpers/read_only.py` and document rule 1 in both phase-execution references. **Rule 1, at classification**: a comment whose requested change lies outside `spec.md`, `plan.md`, and `tasks.md` in the feature directory takes `deferred`, with the refused target named in the disposition and the reply; word it as recorded and not acted on, and **it must not imply future action**, because the request is declined, not scheduled. **Rule 2, at the write**: the resolved target path is checked in code before any write. **The comparison is exact membership over resolved paths, never containment** — resolve the candidate and all three allowed paths, then test for equality against that three-member set. A containment or prefix test would admit anything beneath the feature directory, its checklists and contracts included, and prefix comparison against an unresolved path is a recurring traversal defect in its own right. **Reject a target that is a symbolic link, and reject one any of whose parents up to the feature directory is** — reuse the *shape* of `validate_target_path()` at `speckit-pro/speckit_pro_runner/helpers/mutation.py:1179`, which checks repository boundary and traversal safety but **not** job-scoped file identity, so this reuses its shape rather than its predicate. **The feature directory arrives as the explicit `feature_dir` input, never inferred** — the one inference mechanism available keys off a branch-name pattern this feature's own branch does not match, so inference would resolve to the wrong specification or to nothing. Acceptance: FR-012b, FR-012c. Rule 1 alone would be prose a mis-routed item walks past; rule 2 alone would turn an ordinary out-of-scope request into a stopped run. **Rule 2 is the enforcement boundary and rule 1 is disposition.** Depends on T050 and T034.
- [ ] T052 [US2] Document the write-point stop in both phase-execution references: it reports under the FR-020 contract, naming the refused target path, the comment id it came from, and the resume path, which is to fix the classification and re-run. Reaching this check means classification already failed, so it is a defect report rather than a routine path — which is why it stops rather than downgrading quietly. Acceptance: FR-012d. Depends on T051.
- [ ] T053 [US2] Document the push-failure outcome in both phase-execution references: the push is part of the amendment step, not a step after it. A commit that succeeded whose push failed **stops the run immediately, before that amendment's bookkeeping commit**, naming the unpushed commit's sha and the comment id. **The local commit stands and is not unwound** — the edit is correct work consensus resolved. No row means the skip key does not see the comment, so it is a candidate again next run. **A bookkeeping commit whose push fails stops the run the same way**, differing in one consequence: its row is already in the local workflow file which the sweep reads locally, so the skip key **does** see the comment and the reply is what would otherwise be lost, recovered by the reconciliation rule. **No automatic retry** — retrying inside the run would multiply the window the per-amendment cadence exists to bound. Acceptance: FR-012e, T044's push-failure case. Depends on T052.
- [ ] T054 [US2] Document the bookkeeping commit in both phase-execution references: log writes ride a **separate** commit and are never folded into an amendment commit, because a row that names its commit cannot exist until that commit's sha does. It stages the **workflow file path alone, never the directory**, and takes a `chore:` subject. **The trigger is rows, not handled comments**: a run takes one when it wrote at least one row to **either** log and takes none when it wrote none. Three consequences follow — a run with zero amendments but at least one handled comment takes exactly one; a run that handles no comment but must write Consensus Resolution Log rows also takes exactly one; a run that wrote no row to either log takes none, and an empty commit there would record nothing. One bookkeeping commit per amendment, not per run, which bounds the pushed-but-unrecorded window to a single item. Acceptance: FR-012a. Depends on T053.
- [ ] T055 [US2] Add the Feedback Sweep Log entry to `speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md`, modeled on the `Draft PR` entry at lines 62–120. Header: `| # | Comment ID | Surface | Author | Class | Disposition | Commit | CRL # |`, one row per **handled** comment — a comment assigned a class, which excludes one the trust filter or the self-reply rule dropped and one whose consensus round returned no answer. **The `Disposition` cell escapes any pipe as `\|` and any newline as a line break**, because the table readers in this codebase split rows on the bare pipe with no escape handling and one unescaped pipe would shift `CRL #` out of position. When the author cannot be resolved the `Author` cell records that explicitly rather than sitting blank. **The workflow file is the sole store; no state-file mirror may be written.** Acceptance: FR-013, SC-010, T046 goes green. Depends on T054.
- [ ] T056 [P] [US2] Mirror the Feedback Sweep Log entry into `speckit-pro/codex-skills/speckit-autopilot/references/workflow-file-protocol-codex.md`, compressed to that file's far tighter entry style — the entire Codex protocol file is 90 lines. Acceptance: FR-003, SC-007; the eight-column header and the escaping rule are identical. Different file from T055, so parallel-safe.
- [ ] T057 [US2] Document the log's creation and placement in both workflow-file-protocol files. **The sweep creates it** when the workflow file carries none, writing the heading and the header row itself — it cannot come from the workflow template, because FR-002 forbids changing that template. **Creation and the first rows are one write in one bookkeeping commit**, never a commit of their own ahead of it, because a commit carrying an empty table is read as "nothing has been handled", indistinguishable from a genuine clean first run. **Placement matches the anchor's level rather than assuming one**: match `Consensus Resolution Log` by heading text at any level and write `Feedback Sweep Log` at the **same** level so the two are siblings; when no anchor exists, append `## Feedback Sweep Log` at the end. Of 69 committed workflow files, 33 carry no such heading, 31 write it at `###`, and 5 at `##` — including this feature's own. **Rows number sequentially and continue across runs**, each new row taking one more than the highest already present. Acceptance: FR-013a, SC-012. Depends on T055 and T056.
- [ ] T058 [US2] Add the fourth `Type` value `Sweep` to the Consensus Resolution Log row schema at `speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md` line 617, beside the shipped `Clarify`, `Gap`, and `Finding`, plus the sweep-row escape-rate note. The link is **bidirectional and costs no extra column**: the sweep row's `CRL #` names the consensus row, and that row's item cell names the **comment id**, keying the reverse direction on an immutable value. Sweep rows **COUNT** toward the Round-2 escape-rate metric, and the `Type` column is itself the source discriminator so a breach can be attributed without excluding anything. On the human-review path the link degrades to one direction, by design. Acceptance: FR-014. Depends on T057.
- [ ] T059 [US2] Document the reply templates in both phase-execution references: **exactly one reply per handled comment**, following a run whose bookkeeping commits all landed. Every reply names its class. **Only an `amended` reply names an artifact, a section, and a commit** — requiring those of all four would make three of the four templates unsatisfiable. One fixed template per class, plain public-readable English. **Every template opens with the HTML comment whose prefix is the same fixed string in every reply**, `<!-- speckit-pro:feedback-sweep -->`, which renders as nothing and is what the self-reply rule anchors on. A marker rather than a visible sentence, because a visible sentence is exactly what a reviewer quotes when they disagree. Acceptance: FR-015, T047 goes green. Depends on T058.
- [ ] T060 [US2] Document the two write paths in both phase-execution references: a review-thread reply posts **into its thread**; the pull-request conversation has no threading, so a reply there is a **new top-level comment that names the comment it answers**. **Every body is passed by file path, never inline.** Acceptance: FR-015a, FR-004b, SC-009. Neither shipped reply-writer in this repository posts to the conversation surface, so that write is new work with no prior art to copy. Depends on T059.
- [ ] T061 [US2] Document reply reconciliation in both phase-execution references: **replies are reconciled against the pull request, not assumed from the log.** A comment is owed a reply when it is **present in this run's observation**, has a log row, and carries no sweep reply answering it. The observation qualifier is load-bearing — keying on log rows alone would post a second reply into a thread someone deliberately resolved, turning a recovery rule into a duplicate-reply generator. **The fixed marker carries the answered comment's id** after its unchanged fixed prefix, inside the same HTML comment, so a thread carrying more than one comment still says which one a reply answered. **A failed reply is reported and does not by itself stop the run** — it appears in the run report naming the comment id and the surface. Acceptance: FR-015b, SC-002. An observation that failed means the work never happened; a reply that failed means the work landed and only the notification did not. Depends on T060.
- [ ] T062 [US2] Fix the reply timing in both phase-execution references: **replies post once, at the end of the run, after every bookkeeping commit this run takes has landed. No reply is posted before that point.** Two orders are defensible and FR-003 forbids two. Under the run-scoped rule the composed interrupt case is exact rather than ambiguous — two rows written, **zero** replies posted, one local unpushed commit. **Name which stops post replies**: the re-review stop and the human-review stop occur **after** the reply point so a run reaching either has already posted every reply it owes; **every other stop aborts before it and posts none** — an invalid authenticated account, a corroboration failure, a failed observation, an unreadable log row, a refused edit target, and a failed push. A blanket "a stopping run first posts what it owes" would contradict this directly. Acceptance: FR-015c, T045 goes green. Depends on T061.
- [ ] T063 [US2] Record in both phase-execution references that **the sweep never resolves a review thread**. Acceptance: FR-016; the no-thread-resolution non-goal is stated in the reference rather than left to be inferred. Depends on T062.
- [ ] T064 [US2] Document stop-or-proceed in both phase-execution references. **One or more `amended`**: stop for re-review before any task work, with a report shaped like the plan-stage stop report naming the comments swept, the amendments made, the commit range, and **stating that draft pages regenerate once slice 2 lands**. **No `amended` but at least one handled**: write the records, post the replies, proceed directly into task execution without stopping. **No comment handled at all**: no rows, no replies, **no bookkeeping commit**, proceed. The last two are separated so the first does not read as requiring an empty commit on a pull request that carried no comments. Acceptance: FR-017, FR-018. The regeneration sentence is an interface slice 2 replaces — until it does, it is the only thing telling a reviewer why the pages they are looking at are older than the amendments. Depends on T063.
- [ ] T065 [US2] Document the universal run report in both phase-execution references: it exists on **every** path the sweep takes, not only the stopping one, because the proceed path is exactly where a run that swept nothing but untrusted comments lands. Every run reports **each observed comment's disposition, candidates and exclusions alike, with every exclusion naming its reason** — "not swept: untrusted author" for the trust filter, and every self-reply exclusion named the same way. A run that observed no comments at all reports that, which is a one-line report rather than an absent one. Acceptance: FR-005's reporting half, FR-018a, FR-006's visibility rule. Depends on T064.

**Checkpoint**: US1 and US2 both work independently — the sweep amends,
records, replies, and stops or proceeds.

---

## Phase 5: User Story 3 — An unreadable draft pull request stops the stage (Priority: P3)

**Goal**: Every corroboration status that is not `match` or `no_record` stops
the stage before task work with a report naming the condition and a resume
path; `no_record` passes through.

**Independent Test**: Run the sweep once per unreadable condition and confirm
each stops before task work with a report naming that condition and a resume
path. Then run it with no draft pull request record and confirm it proceeds.

### Tests for User Story 3 ⚠️

- [ ] T066 [US3] Add one corroboration case per status to `tests/speckit-pro/unit/fixtures/feedback-sweep/comment-corpus.json`: `match` sweeps, `no_record` proceeds, and `skipped`, `pr_closed`, `pr_missing`, `identity_mismatch` each stop. Add a **seventh case carrying a value outside the six**, asserting a stop reported as a malformed record rather than mapped onto one of the six. Acceptance: FR-019, SC-006, FR-008a's "a corroboration value outside the six". Depends on T047.

### Implementation for User Story 3

- [ ] T067 [US3] Document the corroboration gate in both phase-execution references: **the six statuses are exhaustive and each maps to exactly one behavior.** Four stop by name — `skipped`, `pr_closed`, `pr_missing`, `identity_mismatch` — `no_record` proceeds, and `match` sweeps. **Each stopping status names its own resume path**, because the four have different fixes: `skipped`, fix the tool and re-run; `pr_closed`, reopen the pull request or clear the `Draft PR` row if the checkpoint is genuinely abandoned, then re-run; `pr_missing`, clear the row, the one status where its absence would match reality; `identity_mismatch`, correct the row to name the right pull request, then re-run. **The sweep never writes the `Draft PR` row on any path**, including these stops — a run that repaired the record it had just failed to corroborate would destroy the evidence of the discrepancy. **A value outside the six is a malformed record and stops**, because exactly one status proceeds and a default that proceeded would make a corrupted record the cheapest way past the checkpoint. Acceptance: FR-019, SC-006, T066 goes green. Depends on T065.
- [ ] T068 [US3] Document the `skipped`-versus-`no_record` distinction in both phase-execution references: `no_record` means the gate does not apply, because no checkpoint was ever opened; `skipped` means the gate applies and the observation failed. Treating "could not observe" as "observed nothing" would make the checkpoint silently optional exactly when the tool is unreliable, which is when unread feedback is most likely. Acceptance: FR-019a. Depends on T067.
- [ ] T069 [US3] Document the four-cause `skipped` report in both phase-execution references: it **must read differently from the three discrepancy stops** and **must name which cause occurred** — the tool was absent, unauthenticated, rate-limited, or returned output that could not be parsed. Behavior does not branch on the cause; only the report does. **Clearing the `Draft PR` row is not a resume path here** — that belongs to `pr_missing`, and reusing it would erase a probably-true record to manufacture a `no_record` reading. Acceptance: FR-019b, SC-006. Depends on T068.
- [ ] T070 [US3] Document the mid-read failure report in both phase-execution references, distinguishing it from the gate stop. Both draw on the same four causes, so the mid-read report **must also name that reading had begun, and which surface failed** — an operator who cannot tell a gate failure from a mid-read failure cannot tell whether the pull request was ever reachable. The resume path is the same: fix the tool and re-run, since the observation is retaken fresh on every invocation and needs no repair step. Acceptance: FR-004c's report half, SC-011. Depends on T069.

**Checkpoint**: All three user stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T071 Consolidate every stop onto **one report builder** in both phase-execution references, with three parts: the **condition** that stopped the run, **what already landed** before it did, and the **resume path**. The what-landed part names the commits pushed, the log rows written, and the replies posted so far, and **is explicitly empty on stops that occur before any write** rather than left for the reader to infer. The complete set of stop conditions is: an invalid authenticated account, a corroboration status that is not `match` or `no_record` or one outside the six, a failed observation, an unreadable Feedback Sweep Log row, a consensus outcome requiring human review, a resolved edit target outside the three artifacts, a failed push, and one or more amendments requiring re-review — the last being the only one that is not a failure. **The human-review stop needs more than the shared contract**: it must name **both** operator actions, resolve the substance and re-run **or** resolve the thread, because it is the only stop whose resume path is not satisfied by re-running. **Two stops must not produce two reports** — a run where several conditions hold emits one report naming every condition, with the per-comment dispositions inside it, so every run produces exactly one report on every path. Acceptance: FR-020, SC-011. Depends on T070.
- [ ] T072 Verify FR-002 by inspection across both platform variants: no row was added to the Workflow Overview table, and the phase-coverage guard's governed phase-id list, the stage-to-phase map, and the workflow template are all unchanged. Acceptance: FR-002; `git diff --name-only` names no template or guard file. Depends on T071.
- [ ] T073 Verify cross-platform parity: `python3 tests/speckit-pro/run-all.py --layer 1`, with `validate-codex-skills` and `validate-codex-parity` passing. Both phase-execution references and both workflow-file-protocol files describe the same sequence. Acceptance: FR-003, SC-007. **Confirm neither `SKILL.md` was touched** — the Codex body's three-word headroom means any addition fails the 8000-word cap. Depends on T072.
- [ ] T074 Regenerate the payload: `python3 scripts/refresh-release-artifacts.py`. This covers the four `dist/` copies of `read_only.py` and `registry.py`, the runner `.sha256`, and the runner `.manifest.json`, and it regenerates the reference `.md` files into both distributions. Acceptance: the six generated paths are byte-identical copies of the source tree; CI's `artifact-consistency` job fails the pull request if this was skipped. **Regenerate — never hand-edit.** Depends on T073.
- [ ] T075 Regenerate the two installed-cache copies of `read_only.py` under `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/` and `.../codex/`. Adding a read-only helper restales them. Acceptance: the plugin-bash-confinement fixtures match the source. **Regenerate — never hand-edit.** Depends on T074.
- [ ] T076 Regenerate the docs-site reference pages: `pnpm --dir docs-site install --frozen-lockfile` once for this worktree, then `pnpm --dir docs-site reference:generate`. The test tree changed — one new test file and a `suite-manifest.json` entry — so this fires. Acceptance: `validate-docs` is not stale. Depends on T075.
- [ ] T077 Run the full gate: `python3 tests/speckit-pro/run-all.py`, zero failures, expecting Layers 1, 4, and 5. Acceptance: constitution IV. While iterating, gate on the changed test file instead — a concurrent `speckit-pro/` edit stales the generated payload and reds roughly six unrelated tests with an opaque `AssertionError: 1 != 0`, which is noise, not signal. Depends on T076.
- [ ] T078 [P] Generate the PR review packet from `spec.md`'s PR Review Packet Requirements section and the traceability table in `quickstart.md`: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback notes. Traceability maps each major requirement or success criterion to changed files and verification evidence. **Deferred work names its follow-up spec** — slice 2 for artifact freshness, ART-010 for the ready flip, and the four items the Non-Goals section records as owned by no spec yet. Record the T014 budget decision in the scope-budget section.
- [ ] T079 Run the `quickstart.md` validation: all seven scenarios, plus the five-step "Before calling the work done" tail. Acceptance: every scenario's expectations hold; the traceability table's evidence column is true. Depends on T077.
- [ ] T080 Pin the clean-re-run convergence case in `tests/speckit-pro/unit/fixtures/feedback-sweep/comment-corpus.json` and its expected envelope: replay a corpus whose every comment already carries a Feedback Sweep Log row and a posted sweep reply, and assert the second run produces **zero new log rows, zero new replies, zero amendments, and proceeds into task work**. Then assert the qualifier holds in the other direction: replay the interrupted case, where a prior amendment was pushed but its bookkeeping commit never landed, and assert that run's handling of that one item is the documented edge case rather than a violation. Acceptance: SC-003. This is the convergence claim itself, and it was the only success criterion no task cited — the fixture corpus covers the no-second-reply half at T044, but nothing pinned the whole-run assertion or its qualifier. Depends on T044 and T063.

---

## Known Interface Gap

**Recorded rather than resolved, because resolving it is a design decision this
phase may not take.** FR-012b rule 2 requires the write-point path check to run
"in code rather than in judgment", and the plan's Declared File Operations
block lists exactly two Python production files — `read_only.py` and
`registry.py`. The contract as shipped in `contracts/sweep-pr-feedback.md`
carries neither a `feature_dir` input nor any target-validation surface, and
the helper is called once, before classification, when no resolved edit target
exists yet.

T004 adds the input to the contract and T051 implements the check in
`read_only.py`, which is the only declared code file that can host it. What
T004 must settle is **how the orchestrator invokes that check at the write** —
a second call to `sweep-pr-feedback` carrying the resolved target, a separate
named surface of the same operation, or something else. No task below invents
an unregistered second helper operation, because that would add an eighth
registration touch point and a second contract the plan does not budget for.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — corrects the design artifacts the rest reads from
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational. **MVP.**
- **User Story 2 (Phase 4)**: Depends on US1 — consensus routing consumes US1's classified candidate list
- **User Story 3 (Phase 5)**: Depends on Foundational; independently testable against US1 and US2, and sequenced after them only because the happy paths must work first
- **Polish (Phase 6)**: Depends on all three stories

### The one dependency that is not conventional

US2 depends on US1 rather than running beside it. The spec says so directly:
US2 "depends on Story 1 having produced a trustworthy classified list." Only
`amended` routes to consensus, and nothing assigns `amended` until US1's
classification exists.

### Within Each User Story

- Every fixture and failing test precedes its implementation task
- Helper branches before the reference prose that documents them
- Claude reference before its Codex mirror, so the mirror has a source

### Parallel Opportunities

- **T001 and T002** — contract and data-model, different files
- **T005, T006** — suite manifest and the new fixture directory
- **T009 and T012** — request fixture and registry entry, both independent of the `read_only.py` chain
- **T035 and T036**, **T055 and T056** — each Claude reference and its Codex mirror are different files
- **T078** — the PR packet needs no code

### What is NOT parallel-safe

`speckit-pro/speckit_pro_runner/helpers/read_only.py` hosts the parse cluster,
the registry cluster, and three registration touch points: **T010, T011, T025
through T034, and T051 are strictly serial.** The corpus tasks T016 through
T022 and T044 through T046 all edit `comment-corpus.json` and are serial.
**T015, T023, T024, T043, and T047 all edit
`tests/speckit-pro/unit/test-feedback-sweep-parse.py` and are serial.**
T037 through T043 and T048 through T065 and T067 through T071 each edit **both**
phase-execution references and are serial with each other.

---

## Parallel Example: Phase 1

```bash
Task: "T001 Correct matched_line to matched_lines in contracts/sweep-pr-feedback.md"
Task: "T002 Correct export.matched_line in data-model.md"
Task: "T005 Register the new test in tests/speckit-pro/suite-manifest.json"
Task: "T006 Create the feedback-sweep fixture directory skeletons"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1: Setup — correct the three design artifacts
2. Phase 2: Foundational — register the helper, **take the T014 budget decision**
3. Phase 3: User Story 1
4. **STOP and VALIDATE**: quickstart Scenarios 1 and 2 against the fixture corpus

At that point the sweep reads, filters, recognizes, and classifies. It does not
yet amend, so it is an inventory rather than a checkpoint — which is exactly the
slice split the plan **rejected** shipping on its own. MVP here means a
validation milestone, not a shippable increment.

### Incremental Delivery

1. Setup + Foundational → helper registered, budget decision recorded
2. US1 → deterministic classification, both references carry the read
3. US2 → amend, record, reply, stop or proceed
4. US3 → the integrity guard on every corroboration status
5. Polish → regeneration, parity, the full gate

---

## Notes

- `[P]` = different files, no dependencies
- Verify every test FAILS before implementing against it
- Each amendment stages **one path**, never a directory — Phase 7's existing `git add -A` pattern must not be inherited
- **Non-goals bound this list.** No task regenerates the draft page set, detects stale pages, or refreshes the pull-request description (all slice 2); resolves a review thread; adds a Workflow Overview phase row; edits a shipped gallery template or its payload copy; edits a Layer 6 corpus agent definition; or writes a state-file mirror. **No task crosses any of them**, and T023 is the one that comes closest — it reads the gallery templates and edits none, so it stays inside the boundary and triggers no payload regeneration.
- Neither `SKILL.md` may gain a line. Three words of headroom on the Codex cap.
