# Implementation Notes: ART-007

### T001

**Deviations/Edge cases/Surprises:** None. `python3 tests/speckit-pro/run-all.py`
finished green at 7399/7399 (L1 1447, L4 5766, L5 186), which matches the G0
baseline recorded at Phase 0 exactly. No drift diagnostic is owed. The recorded
baseline is preserved rather than recaptured, per the autopilot's Step 0.6e rule:
a baseline recaptured after planning would already contain whatever this run
adds, making the G7 comparison vacuous.

### T002

**Deviations/Edge cases/Surprises:** Already satisfied, so nothing was run.
`docs-site/node_modules` is present and populated (`.pnpm` store plus the six
direct dependencies and three dev dependencies `docs-site/package.json`
declares). Node resolves to v24.11.1, above the ≥22.12 floor the docs-site
toolchain needs. The worktree was bootstrapped during the plan stage and the
install survives into this stage.

### T003

**Deviations/Edge cases/Surprises:** Already satisfied, so nothing was run.
`git config --get merge.generated.name` returns
`keep ours; regenerate after merge` and `merge.generated.driver` returns
`exit 0`. The driver is per-clone configuration that cannot be committed, so
verifying it rather than assuming it is the point of the task.

### T004

**Deviations/Edge cases/Surprises:** None. The verdict below is restated from
plan.md, not recomputed — recomputing it is the failure mode the task exists to
prevent, because a fresh hand count of 11 production files would trip a naive
block reading the plan already ratified against.

**Ratified reviewability verdict, carried forward unchanged:**

| Signal | Value |
|---|---|
| `estimate-reviewable-loc` | 0 projected, against 400/800 thresholds — 0 by its own production-file definition on a Markdown/JSON/stdlib-Python surface |
| `estimate-spec-size` at the spec's 10 projected production files | `{"estimated_loc": 335, "suggested_slices": 1, "status": "ok"}` |
| `estimate-spec-size` at the plan's 11 | `{"estimated_loc": 355, "suggested_slices": 1, "status": "ok"}` |
| Hand count | 16 total files (11 under `speckit-pro/`, 5 under `tests/speckit-pro/`) |
| Against the file lines | one above the 15-file warn line, well under the 25-file block line |
| Primary surfaces | one (harness/adapter), so the multi-surface rule holds |
| **Split decision** | **no split** |

The two design corrections recorded in the workflow file as DC-1 and DC-2 add no
file and change no surface, so this verdict stands unamended.

### T005

**Deviations/Edge cases/Surprises:** The capture was widened past what the task
originally asked for. A pass/fail capture cannot see an SC-008 regression in
which a fixture still fails but for a newly different reason, and the `else` arm
this feature introduces is exactly the kind of edit that can cause one. So the
baseline records each fixture's **failure rule strings**. Captured outside the
repository, in terminal output only; no file was added.

| Fixture | Status | Mode | Failure rules |
|---|---|---|---|
| `valid-single.json` | passed | single | — |
| `valid-split.json` | passed | split | — |
| `invalid-malformed-json.json` | failed | null | `input.error` |
| `invalid-missing-evidence.json` | failed | single | `body.protected_fingerprint`, `body.title`, `evidence.scope.changed_files`, `evidence.verification`, `packet.schema.const`, `packet.schema.min_items`, `packet.schema.min_length`, `packet.schema.required` |
| `invalid-no-feature-dir.json` | failed | single | `evidence.scope.changed_files`, `evidence.verification`, `input.path.validation_result_path`, `packet.schema.required` |
| `invalid-protected-edit.json` | failed | single | `body.protected_fingerprint`, `body.title` |
| `invalid-schema-with-feature-dir.json` | failed | single | `evidence.scope.changed_files`, `evidence.verification`, `input.path.validation_result_path`, `packet.schema.required` |
| `invalid-title-token.json` | failed | single | `body.protected_fingerprint`, `body.title` |
| `split-partial-failure-state.json` | failed | null | `evidence.scope.changed_files`, `evidence.verification`, `input.path.validation_result_path`, `packet.schema.additional_properties`, `packet.schema.required` |

Two observations that constrain the T010 validator guard. Four fixtures already
emit `evidence.verification` and `evidence.scope.changed_files`, so the guard
must be `mode != "draft"` rather than `mode == "single"` — two of those four
carry a null `mode`, and a `mode == "single"` guard would silently drop their
failures. And `mode` is absent on `invalid-malformed-json.json` and
`split-partial-failure-state.json`, so the guard must tolerate `None` without
raising.

### T006

**Deviations/Edge cases/Surprises:** None material. Fixture pair authored
together; `protected_body_fingerprint.value` is
`123e87cba04eb6e71c34eca6b75939be17db1a5c5bf164e5afad3f612e03c172`, computed by
calling the shipped `protected_body_sha256` rather than reimplementing the
normalisation. Title carries a lowercase scope per SC-007 and research D4.
Before authoring, the executor grepped every test `.py` for a glob or `iterdir`
sweep over `fixtures/pr-packet/`, because a sweep expecting every `valid-*.json`
to pass would have been broken by adding a fixture that is invalid until T008.
None exists, so the addition is safe.

Validated bare against the un-relaxed schema, the fixture produces eleven
failures, all of them draft-mode rejections and **none** of them a `body.*` rule.
That is the evidence the pair itself is structurally sound and the fingerprint
matches: the only thing rejecting it is the relaxation T008 and T009 have not
landed yet.

### T007

**Deviations/Edge cases/Surprises:** Three worth recording.

**Six of the eight fail, not eight.** Tests 5 and 8 pass before and after by
design — they are SC-008 behaviour-preservation guards, and a guard that changes
its answer when the implementation lands would not be preserving anything. They
are armed instead by asserting **exact rule-set equality** rather than
membership: if T009 drops the top-level strictness without adding the `else` arm,
test 8's expected set collapses and it fails. Making them artificially red would
have been gaming the RED bar rather than meeting it.

That equality choice applies to the negative tests generally. Membership
assertions would all have passed today, since the current failure set is a strict
superset of every expected set, and would have tested nothing.

**A gap in the contract's own test-obligation table, now closed.** Contract §1.1
requires the `mode` enum to be widened at **two** sites and explains why — a
passing draft packet's own validation record is otherwise unrepresentable — but
§6 lists no obligation covering the second site. An implementation widening only
`properties.mode` would have passed all eight tests as originally specified. The
executor closed it inside test 1 by asserting the emitted payload validates clean
against `$defs/validation_result`, and confirmed the assertion discriminates:
today it yields `packet.schema.enum validation_result.mode`, and after the
second-site edit it yields nothing. No test and no fixture was added to close it.

**A third file changed, by repo rule rather than by the task.**
`docs-site/src/content/docs/reference/tests.md` is generated from the test tree
and enumerates fixture `.md` files by path, so adding `bodies/valid-draft.md`
staled it. Regenerated with `pnpm --dir docs-site reference:generate`; the diff is
5 insertions and 3 deletions, every changed line naming only `valid-draft.md`.
T049 re-runs this at the end of the phase; running it now keeps every
intermediate commit `validate-docs`-clean rather than leaving CI red across the
whole implementation.

### T008

**Deviations/Edge cases/Surprises:** None. Both enum sites widened, the
`$defs.validation_result` copy included. Test 1's added assertion against
`$defs/validation_result` confirms the second site landed: it emitted
`packet.schema.enum validation_result.mode` before and emits nothing now.

### T009

**Deviations/Edge cases/Surprises:** None. Contract §1.2.2 applied verbatim, with
only whitespace expanded to the surrounding house style. The `split_slice` branch
and its `else` arm are byte-identical to before. Five top-level bounds loosened
plus `uat_runbook_heading` demoted from `const` to `{"type": "string"}`;
`scope_evidence.non_goals` untouched at `minItems: 1`.

The §1.2.1 note that `prefixItems` constrains only the positions that exist is
what makes `editable_fields: []` validate while the three `prefixItems` entries
stay at the top level and keep binding `single` and `split`.

### T010

**Deviations/Edge cases/Surprises:** None. The guard is
`if data.get("mode") != "draft":` at `read_only.py:2872`, with the two existing
assertions indented under it and unchanged in content. `.get()` returns `None`
for an absent `mode` and `None != "draft"` is true, so the two null-mode fixtures
keep emitting both rules — which is what holds their baseline rule sets.

### T011

**Deviations/Edge cases/Surprises:** Two, and the second is a measurement trap
worth carrying forward.

**The layer-4 total was not the right bar mid-phase.** The dispatch set
5774/5774 as the acceptance bar, which was unreachable inside T008-T010's scope:
editing shipped source under `speckit-pro/` stales `dist/`, the runner trust
manifest, and the installed-cache proofs, and regenerating those is T048's job.
Seven failures remained, all generated-artifact staleness. Running
`scripts/refresh-release-artifacts.py` cleared every one and took the full suite
to **7407/7407** — 8 above the 7399 G0 baseline, exactly the eight new test
methods. That is the proof the residual failures were staleness and not
regressions. T048 still runs at the end of the phase; the generator is
idempotent, and regenerating here keeps the intermediate commits CI-clean and
keeps later agents from measuring a contaminated baseline.

**A validator sweep must run against the worktree source, not the plugin cache.**
The first SC-008 re-sweep reported `valid-draft.json` as still failing, which
contradicted a green 76/76 on the test file. The cause was `PYTHONPATH` pointing
at the installed plugin cache rather than `speckit-pro/` in this worktree. The
cache still holds the un-relaxed schema, so it was faithfully reporting a tree
that is not the tree under test. The T005 baseline was taken the same way, but
was valid then because source and cache still agreed; they diverge the moment a
shipped file is edited. Re-run against `PYTHONPATH=speckit-pro`,
`valid-draft.json` passes with zero failures.

**SC-008 verified by machine diff, not by eye.** All nine pre-existing fixtures
reproduce their exact failure rule sets — no drift.

### T017

**Deviations/Edge cases/Surprises:** Landed early, out of task order. T017 is a
User Story 1 task, but it is pure protocol prose describing the `Draft PR` row
grammar and has no dependency on the packet schema Phase 2 relaxes, so nothing
about it could be invalidated by the Phase 2 outcome. Written by the orchestrator
while the Phase 2 GREEN agent was working, on a file that agent was not touching.

That had one cost worth recording: editing a shipped file mid-measurement staled
`dist/` and contaminated the GREEN agent's own baseline reading, which it spent
effort diagnosing before correctly attributing it. A concurrent edit to shipped
source is invisible to an agent measuring the suite, and surfaces only as an
opaque `AssertionError: 1 != 0` in the gate tests. Future overlapping work should
either stay off `speckit-pro/` or tell the agent which failures to expect.

### T012

**Deviations/Edge cases/Surprises:** Five test methods, 22 counted units (the
suite's `run_counted` counts subTests individually). All 22 error on one cause,
`AttributeError: module 'speckit_pro_runner.helpers.read_only' has no attribute
'workflow_draft_pr_row'` — zero assertion failures and exactly one distinct
exception type, which is the evidence the RED is the missing reader rather than
a defect in the test code.

**The executor found four real ambiguities in `contracts/draft-pr-row.md`, all
now closed in the contract rather than left to T016's judgement:**

1. **§5 gave no types.** It named `{number, url, gap_note}` and stopped, so an
   implementer reading only the contract could reasonably ship `number` as a
   string. `data-model.md` settles it as an integer, and the consequence of
   getting it wrong is not cosmetic: FR-011 compares the recorded number against
   what a `--json` query returns, so a string would silently never match and
   produce a permanent `identity_mismatch` on a perfectly healthy pull request.
   §5 now states the signature, the per-case return shape, and that reasoning.
2. **The em dash separator was never stated as excluded** from the gap note. It
   was only inferable from where the template puts the placeholder boundary. §2
   now says it outright, and says that hyphen, en dash, and no-separator forms
   are undefined rather than tacitly accepted.
3. **The link target's character class is load-bearing** and was unstated. A gap
   note may legally contain parentheses or a second Markdown link, so a reader
   capturing the target greedily swallows the note and **corrupts the identity**
   rather than merely losing the note. That is the bug class most likely to reach
   production here, so §2 now states the constraint and names the failure.
4. **§5's "three near-duplicate lines"** is not literally achievable —
   `workflow_recorded_stage` is four lines and does no regex, while this reader
   needs a match plus a record build. It now reads explicitly as an
   anti-abstraction instruction rather than a line budget, so T016 does not
   contort to hit a number.

**One obligation is pinned by prose rather than by a failing test, and that is
recorded rather than hidden.** Contract §7's "a commented-out row is not read as
present" is a property of the call path: the reader receives lines the caller has
already blanked with `HTML_COMMENT_RE`. A redundant second blanking inside the
reader is undetectable, because blanking blanked text is a no-op. The test locks
in the shipped constant by calling `read_only.HTML_COMMENT_RE` rather than
re-deriving it, which is as far as a test can reach.

**One malformed case was added beyond the contract's list:** an empty link
target, `[#438]()`, which a naive lazy capture accepts and reports as
`url == ""`. Kept, and §2 now names it malformed.

**A dispatch error, twice now.** The dispatch told this executor the file does
not use `run_counted`. It does, from `tests/speckit-pro/lib/test_result.py`. The
orchestrator had generalised from a sibling test file that genuinely does not.
Both executors correctly followed the file over the prompt. `run_counted` also
prints no tracebacks — it writes to a throwaway sink and emits only a count — so
verbatim RED evidence needs a verbose runner invoked outside the repository.

### T013

**Deviations/Edge cases/Surprises:** Three tests, all failing inside the
producer: two assertion failures and one `TypeError` on the not-yet-existing
`mode` parameter of `required_headings()`. The `TypeError` is legitimate RED — it
names the exact producer function T015 must change.

**The headline finding: contract §2 named two producer edits and there are six.**
The two it omitted are the ones that fire *first*, so a draft packet dies in
input normalisation before the mode gate is ever reached. This is demonstrated
rather than reasoned: the emission test fails at
`scope_evidence.changed_files must be a non-empty string array`, which is
`normalize_scope_evidence`, not the gate.

- `normalize_scope_evidence` (~586-625) rejects an empty `changed_files` in
  **both** its dict and non-dict branches.
- `normalize_evidence_list` (~629-641) rejects `[]` because
  `isinstance(raw, list) and raw` is false for an empty list, so it falls through
  to the "at least one item" error.
- The `uat` object (~305-308) hardcodes fallback prose for `how_to_uat` as well
  as the heading. A draft must emit `""` for both.

**And an ordering defect the contract never mentioned.** `mode` is read at line
298, *after* `normalize_scope_evidence` (281) and `normalize_evidence_list` (285)
have already run and returned their diagnostics. Neither receives `mode`, so
sites 5 and 6 cannot become mode-aware where they stand. Verified independently
by the orchestrator against the source before amending: nothing between the
target check and line 298 consults `mode`, and none of the four normalizers in
that span takes it, so hoisting the mode resolution above both calls is safe and
minimal. Contract §2.4 added; T014 and T015 amended.

**The unknown-mode test would have passed silently** had it asserted only the
diagnostic code rather than §2.1's exact message string. Asserting the literal is
what makes it RED, and it means a differently-worded message in T015 is a real
contract deviation the test will catch rather than absorb.

**Before writing a line of test code the executor probed a hand-built draft
packet through `validate-pr-packet-read-only`** and confirmed it passes with
`status=passed`, `pr_blocked=false`, `failures=[]`. That is what establishes the
target shape is reachable, so the RED that follows is about the producer and not
about an impossible contract.

**Cross-check between the two parallel RED agents.** Each independently measured
layer 4 at 5774/5799 with 25 failures and each attributed exactly its own share —
22 for T012, 3 for T013 — with the *passed* count holding at 5774 in both runs.
Two independent agents agreeing on the split, and on nothing having regressed, is
better evidence than either one alone.

**The docs-site test reference did not stale.** Both tasks modified existing
`.py` files and added none, and the generated page lists files by path, so the
inventory is unchanged. Confirmed by running `reference:generate` and observing
an empty diff rather than by assuming it.
