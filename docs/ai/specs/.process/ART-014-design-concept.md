---
topic: "Phase-guard enforcement repair"
slug: "art-014-phase-guard-enforcement-repair"
date: "2026-08-12"
mode: "setup"
spec_id: "ART-014"
source_input:
  type: "topic"
  ref: "docs/ai/specs/html-artifacts-technical-roadmap.md ART-014 scope"
question_count: 11
stop_reason: "natural"
---

# Design Concept: Phase-Guard Enforcement Repair

> **Source:** `docs/ai/specs/html-artifacts-technical-roadmap.md`, ART-014 section
> **Date:** 2026-08-12
> **Questions asked:** 11
> **Stop reason:** natural

The Q&A log below runs to Q12. Q1 through Q11 were interview questions. Q12 is
the mandatory slice-sizing branch, which the estimator answered without asking.

## Evidence Base

Every claim below was verified against the working tree at commit `3af4764e`
during the interview. The roadmap's line numbers had drifted; the content had
not. Three corrections to the roadmap text:

1. The problem-key count is **20, of which 12 are advisory**, not "11 of 19".
   ART-006 added `stage_mirror_errors`, which the roadmap entry predates.
2. The workflow corpus under `docs/ai/specs/.process/*-workflow.md` is
   **54 files**, not 55.
3. `RULE_PROBLEM_KEYS` now sits at `:239-254`, `_authorized_workflow_text` at
   `:1298`, its early returns at `:1306-1312`, the fold into
   `workflow_checkpoint_errors` at `:4031`, and the exit-code scoping at
   `:4106-4112`.

### The defect, reproduced three ways

Supplied workflow `docs/ai/specs/.process/ART-006-workflow.md` against a state
whose `workflow_file` names `docs/ai/specs/.process/CAR-001-workflow.md`:

| Invocation | `workflow_checkpoint_errors` | Exit |
| --- | --- | --- |
| plain state, `--rule status-evidence` (what autopilot issues) | `[]`, the comparison never ran | **0** |
| state with `pr-marker-plan.v2` + `--expected-head-commit`, `--rule status-evidence` | the documented message | **0** |
| same, `--rule` dropped | the documented message | 1 |

Both defects are independently real. The documented message is reachable only
on a path the autopilot never takes, and even there it cannot move the exit
code under the rule the autopilot selects.

### Regression baseline

All **54 of 54** workflow files exit `0` under `--rule status-evidence` when the
state names the matching workflow. That is the contract the repair must
preserve.

### Two tracked state files disagree on the field's existence

| Tracked state file | `workflow_file` |
| --- | --- |
| `.specify/autopilot-state.json` | absent |
| `docs/ai/specs/.process/autopilot-state.json` | `docs/ai/specs/.process/ART-012-workflow.md` |

This is why Q3 matters: the existing gated code treats a missing field as an
error, and arming that verbatim would fail a tracked legacy state.

### Distribution shape

There is exactly one authored copy of the guard, at
`speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`.
`speckit-pro/codex-skills/speckit-autopilot/scripts/` does not exist; the Codex
distribution ships the same `skills/` path. The four other tracked copies are
generated (`dist/claude`, `dist/codex`, and two installed-cache proofs) and are
all byte-identical today.

The authority claim `autopilot-state.json.workflow_file is the authority` appears
in exactly two files: `speckit-pro/skills/speckit-autopilot/SKILL.md` and the
guard itself. No Codex-side document mentions it.

## Goals

- Make the workflow-identity comparison run on the invocation the autopilot
  actually issues, so the failure message `SKILL.md` already quotes becomes
  reachable.
- Report that failure under a problem key the `status-evidence` rule consults,
  so a mismatch moves the exit code.
- Preserve the measured baseline: 54 of 54 corpus workflow files still exit `0`
  under `--rule status-evidence` after the change.
- Ship a negative control that did not exist before: a state naming a different
  specification must exit non-zero.
- Record, per problem key, whether advisory status is deliberate, in a form a
  test enforces rather than a table that can drift.
- Make every documentation claim about this guard true on the platform it
  appears on, including the flags the Claude flow does not yet supply.
- One vertical slice. Estimator: 235 reviewable LOC, 1 suggested slice,
  status `ok` (signals: 3 user stories, 5 files, 13 FRs, modify-weighted).

## Non-goals

- Arming any advisory key other than the new identity key. Anything the audit
  finds accidentally advisory becomes a roadmap follow-up with its evidence
  attached, not work in this slice. Answered in Q6.
- Changing what the coverage lists check, or re-litigating the `--rule` scoping
  mechanism. Both are out of scope per the roadmap and neither was reopened.
- Wiring the Claude autopilot to fetch live PR `baseRefOid` / `headRefOid`. The
  gap is documented here and in the shipped docs, but the runtime work is its
  own spec. Answered in Q7 and Q8.
- A committed test that walks the live `docs/ai/specs/.process/` corpus. An
  in-flight spec mid-repair should fail the guard, and a committed walk would
  then turn CI red on unrelated pull requests. Answered in Q10.
- Making `workflow_file` a mandatory state field. That is a migration, not a
  repair, and the declared budget does not carry it. Answered in Q3.

## Design Tree (Q&A log)

### Q1. Where should the plain workflow-identity comparison run inside `_authorized_workflow_text`?

**Branch:** Control flow / enforcement placement

**Recommended answer:** Separate unconditional block, before the marker-plan and
head-commit gate, leaving the existing gated PR-head byte comparison untouched.

> The identity comparison needs only `state.workflow_file` and the resolved
> workflow path. Neither precondition is required for it. The gated path is
> genuinely load-bearing for a second caller:
> `speckit-pro/codex-skills/speckit-autopilot/SKILL.md:674` instructs appending
> `--expected-base-commit` and `--expected-head-commit` from live PR metadata
> when `pr-marker-plan.v2` declares a changed-file manifest, and the same
> instruction repeats in `references/phase-execution-codex.md:734` and
> `references/task-list-canonical-codex.md:88`.

**Alternatives offered:**
- Hoist the preconditions so the whole block runs unconditionally: makes
  `_repository_root` and `_git_file_at_commit` mandatory on every run, so a run
  without a head commit needs a new skip path further down anyway.
- Only fix the key registration: leaves defect 1 alive, since the normal
  invocation carries neither precondition and the comparison still never runs.

**User's answer:** Separate unconditional block (Recommended)

---

### Q2. Under which problem key should the identity failure be reported so the `status-evidence` rule can move the exit code?

**Branch:** Reporting contract / blast radius

**Recommended answer:** A new `workflow_authority_errors` key, added to the
`status-evidence` tuple. The identity errors stop being folded into
`workflow_checkpoint_errors`.

> `workflow_checkpoint_errors` is produced at four other sites by
> `validate_workflow_checkpoint_bindings` (`:489`, `:492`, `:516`, `:618`), all
> of which check PR Marker Plan Evidence table bindings: commit-sha binding,
> superseded-sha binding, and exactly-one-row-per-marker. Widening that key into
> `status-evidence` arms every one of those against a 54-file corpus that has
> never had to satisfy them. A dedicated key arms the identity comparison and
> nothing else, and leaves the invocation in both `SKILL.md` files unchanged.

**Alternatives offered:**
- Widen `workflow_checkpoint_errors` into `status-evidence`: one line, but an
  unmeasured blast radius across four sibling checks.
- Add a third named rule `workflow-authority`: semantically cleanest, but the
  autopilot invocation in both `SKILL.md` files plus three references and the
  installed-cache fixtures must change, and any caller still passing only
  `--rule status-evidence` silently opts out.

**User's answer:** New `workflow_authority_errors` key (Recommended)

---

### Q3. When `state.workflow_file` is absent or malformed, should the newly-armed identity check fail or stay silent?

**Branch:** Back-compatibility / legacy state shapes

**Recommended answer:** Absent skips, present-and-wrong fails, present-and-
malformed fails.

> A state that does not name a workflow asserts no authority, so there is
> nothing to contradict. A state that names the wrong one is the exact defect
> being repaired. Keeping the malformed case failing stops a garbage value from
> silently disabling the check. The same file already sets this precedent:
> `validate_state_status` "does not mandate the field, so a legacy state that
> predates `status` still validates". The tracked `.specify/autopilot-state.json`
> has no `workflow_file` at all, so the alternative would newly fail a file
> already in the tree.

**Alternatives offered:**
- Absence fails too, making the field mandatory: honest, but turns the spec into
  a migration and makes any resumed pre-field run unresumable until repaired.
- Absent and malformed both skip: maximally back-compatible, but a malformed
  value becomes a silent opt-out, which is a quieter version of the bug being
  fixed.

**User's answer:** Absent skips, present-and-wrong fails (Recommended)

---

### Q4. When the guard cannot resolve a repository root, should the newly-armed identity check fail or skip?

**Branch:** Environment tolerance

**Recommended answer:** Skip. No root means no comparison.

> `_repository_root` returns `None` whenever the state file sits outside a git
> repository, which is the extracted-copy case `SKILL.md` explicitly
> contemplates. `validate_state_status` already sets the precedent in the same
> file: skip rather than fail "so an extracted copy cannot manufacture a false
> violation". Verified during the interview that a worktree resolves correctly
> despite `.git` being a file there, and that a path outside any repository
> returns `None`.

**Alternatives offered:**
- Reuse the existing "workflow repository root is unavailable" error: smallest
  diff, but once armed it converts an environment fact into a spec verdict.
- Compare path suffixes and drop the git dependency: false-passes across two
  clones sharing a relative path, and false-fails at a different prefix depth.

**User's answer:** Skip, no root means no comparison (Recommended)

---

### Q5. What form should the per-key advisory audit take, and where should the record live?

**Branch:** Audit deliverable / drift resistance

**Recommended answer:** A `PROBLEM_KEY_INTENT` classification map in the guard,
naming every emitted key as gated or deliberately advisory with a one-line
reason, plus a test asserting the report emits no key missing from the map.

> ART-014 exists because a key drifted into being inert with nobody noticing. A
> documentation table can drift the same way; a test cannot. Roughly 25 LOC plus
> one test, inside the declared budget. Measured split to classify: 8 gateable
> keys, 12 advisory.

**Alternatives offered:**
- A table in `SKILL.md` beside the `--rule` docs: zero production code, reads
  well, but nothing enforces it, which is precisely how the current defect
  survived. Also needs mirroring.
- Record the audit in `spec.md` only: smallest diff, but the knowledge lives in
  an archived spec and leaves no in-tree signal beside the code.

**User's answer:** Classification map in the guard, test-enforced (Recommended)

---

### Q6. If the audit finds an advisory key that is advisory by accident rather than by design, should ART-014 arm it?

**Branch:** Scope control

**Recommended answer:** Arm only `workflow_authority_errors`. Every other key
gets a verdict string in the classification map, and anything judged accidental
becomes a new roadmap entry.

> Each armed key needs its own negative control and its own corpus proof, so
> each one is its own slice. The roadmap already states that the audit's job is
> to separate deliberate from accidental, not to arm everything.

**Alternatives offered:**
- Also arm any accidental key the corpus proves clean: a probe run during the
  interview reported all 12 advisory keys clean across 54 files, but that number
  cannot be trusted. A thin synthesized state makes
  `validate_workflow_checkpoint_bindings` and the manifest and projection checks
  return early, so "clean" there means "never executed". Arming honestly would
  need realistic per-key state fixtures and a corpus re-run under each.
- Arm every key the audit judges accidental: diff size is unknown until the
  audit runs during implementation, so the spec would be committing to work it
  cannot size at scoping time.

**User's answer:** Arm only the identity key; file the rest (Recommended)

---

### Q7. The `--expected-head-commit` instruction exists only in the Codex SKILL.md, never in the Claude one. Is closing that gap part of ART-014?

**Branch:** Cross-platform parity

**Recommended answer:** Out of scope. Record the finding and file a follow-up.

> It is a real defect of the same family, but about a different check: the
> changed-file-manifest byte comparison rather than workflow identity. Closing
> it properly means the Claude autopilot must fetch live PR OIDs, which is
> runtime behavior rather than a documentation line.

**Alternatives offered:**
- Make Claude actually supply the OIDs: the complete fix, but it adds a live PR
  metadata fetch, a blocking failure path, and new tests, plausibly 300+ LOC
  across 4+ production files, which the reviewability gate would want split.

**User's answer:** **Other than recommended.** In scope, mirror the instruction
into the Claude docs. The operator accepted the documentation cost in exchange
for closing the prose asymmetry now rather than later. Q8 resolves the tension
this creates.

---

### Q8. How should the Claude SKILL.md word the instruction, given the Claude autopilot has no step that fetches those OIDs?

**Branch:** Cross-platform parity, follow-up to Q7

**Recommended answer:** State the contract and its unwired status together. Write
the same append rule Codex carries, then say plainly that the Claude flow does
not yet fetch the OIDs and name the follow-up that will wire it.

> This was asked because Q7's answer created a direct tension with ART-014's own
> thesis: documentation must not promise enforcement that does not happen. Naming
> the unwired status makes the prose true on both platforms and makes the
> asymmetry legible in the tree rather than only in an archived spec.

**Alternatives offered:**
- Mirror the Codex paragraph verbatim: cleanest parity diff, but the Claude doc
  would then assert a step the Claude flow does not perform, which is the exact
  failure mode ART-014 exists to eliminate.
- Document the flags as guard capability rather than caller duty: accurate
  without a caveat, but Codex's "missing, stale, or mismatched authority is
  blocking" obligation loses its home.

**User's answer:** State the contract plus its unwired status (Recommended)

---

### Q9. Should the identity failure message keep its exact documented wording, or gain the two paths it is comparing?

**Branch:** Operator diagnostics

**Recommended answer:** Keep the documented sentence as a prefix and append both
paths.

> An operator hitting this mid-run needs to know which two files disagree before
> they can repair either one, and the message is the only place they will see
> it. The guard already knows both values at the point it raises. `SKILL.md`
> then quotes the prefix rather than claiming an exact full string, and the test
> asserts the prefix so path formatting can change without breaking it.

**Alternatives offered:**
- Keep it verbatim: smallest documentation diff and full-equality assertions
  stay possible, but the operator has to open both files to find the mismatch.
- Rewrite it to lead with the repair: best for a first-time reader, but it
  orphans the roadmap, the ART-006 retrospective, and the 2026-08-09 archive
  report, two of which are archived and should not be edited.

**User's answer:** Keep the sentence as a prefix, append both paths (Recommended)

---

### Q10. Should the 54-file corpus regression proof be a committed test, or a one-time evidence run?

**Branch:** Verification strategy

**Recommended answer:** A one-time recorded evidence run. Prove it once during
implementation, record before and after in the workflow file and PR body, and
let committed Layer 4 tests carry the ongoing guarantee via synthetic fixtures.

> `docs/ai/specs/.process/` is live data. An in-flight spec mid-repair can
> legitimately fail the guard, which is the guard working, but a committed
> corpus walk would then turn CI red for every unrelated pull request until that
> spec is fixed.

**Alternatives offered:**
- A committed Layer 4 test that walks the live corpus: strongest ongoing
  guarantee and it would have caught this defect class earlier, but it gates the
  suite on other people's in-flight work.
- Committed but marked `live_only` and off by default: the mechanism exists in
  `suite-manifest.json`, but a check nothing runs by default tends to rot, which
  is the same category ART-014 is auditing.

**User's answer:** One-time recorded evidence run (Recommended)

---

### Q11. Where should the Codex-side statement of the `workflow_file` authority live?

**Branch:** Cross-platform parity, documentation home

**Recommended answer:** Add it to `workflow-file-protocol-codex.md`, and to the
Claude `workflow-file-protocol.md` beside it.

> Codex runs the same guard and will newly fail on an identity mismatch, but no
> Codex document mentions the authority. Both platforms already carry a paired
> `workflow-file-protocol` reference, and state-versus-workflow authority is
> exactly what that document is for. It keeps the claim beside the related
> precedence rules instead of duplicating a sentence into two `SKILL.md` files
> that nothing asserts agree.

**Alternatives offered:**
- Add it to the Codex `SKILL.md`: most discoverable, but duplicates the sentence
  into two hand-authored files with no parity check over arbitrary prose.
- Leave Codex docs untouched: smallest diff, and the new message is
  self-explaining, but a Codex operator whose run halts has no in-tree
  explanation.

**User's answer:** Add it to `workflow-file-protocol-codex.md` (Recommended)

---

### Q12. Slice sizing

**Branch:** Slice sizing (mandatory branch, advisory)

Run twice, because Q8 and Q11 added authored files after the first run.

| Run | Signals | Result |
| --- | --- | --- |
| Initial | 3 user stories, 3 files, 13 FRs, modify | `estimated_loc 195`, `suggested_slices 1`, `status ok` |
| Final | 3 user stories, 5 files, 13 FRs, modify | `estimated_loc 235`, `suggested_slices 1`, `status ok` |

Under the 400 ceiling, and the work cuts end-to-end through guard logic, error
reporting, rule registration, tests, and documentation rather than by layer. No
split warranted. Recorded as an advisory note, not a decision.

**Budget amendment.** The roadmap declares "~120 reviewable LOC, ~2 production
files, ~5 total files". Q8 and Q11 raised the authored file count. Revised
declaration:

- Production files (4): the guard, `SKILL.md`, `references/workflow-file-protocol.md`,
  `references/workflow-file-protocol-codex.md`
- Test files (1): `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py`
- Generated, not hand-edited (4): `dist/claude`, `dist/codex`, and two
  installed-cache proofs

Production files at 4 remain under the warn threshold of 6, and reviewable LOC
at 235 remains under 400. Still one slice, still within budget.

## Open Questions

- **What:** Whether any of the 12 advisory keys is advisory by accident.
  **Why deferred:** The audit is implementation work, not scoping work. Q6
  settled what happens with the answer, not what the answer is.
  **Suggested next step:** Perform the audit during implementation, record the
  per-key verdict in `PROBLEM_KEY_INTENT`, and open a roadmap entry for anything
  judged accidental.

- **What:** The Claude autopilot never supplies `--expected-base-commit` or
  `--expected-head-commit`, so the PR-head byte comparison is unreachable on
  Claude even though the Codex flow supplies them.
  **Why deferred:** Q7 and Q8. The documentation is corrected in this slice; the
  runtime wiring is a separate spec.
  **Suggested next step:** Open a roadmap entry for the Claude-side live-PR-OID
  fetch, and reference its ID from the note added to `SKILL.md`. The note's
  `ART-0NN` placeholder must be replaced with the real ID before merge.

- **What:** The autopilot state slot appears twice in the tree,
  `.specify/autopilot-state.json` and
  `docs/ai/specs/.process/autopilot-state.json`, and only the second carries
  `workflow_file`.
  **Why deferred:** Q3's answer makes the divergence harmless for this repair.
  Whether two tracked slots should exist at all is a separate question.
  **Suggested next step:** Raise during `/speckit-clarify` if the implementation
  finds the two slots are read by different callers.

## Recommended Next Step

Setup has already run. The next action is
`/speckit-pro:speckit-autopilot docs/ai/specs/.process/ART-014-workflow.md`.

Before that, note two things the implementation must not skip:

1. Editing the guard restales generated payloads. Run
   `python3 scripts/refresh-release-artifacts.py` and account for the
   installed-cache proofs before calling the work done.
2. The negative control belongs in
   `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py`, which already
   describes itself as the negative-fixture suite for the guard's `--rule`
   exit-code scoping. Layer 4 is "Unit Tests" in `suite-manifest.json`.
