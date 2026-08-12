# Implementation Plan: Phase-Guard Enforcement Repair

**Branch**: `art-014-phase-guard-enforcement-repair` | **Date**: 2026-08-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/art-014-phase-guard-enforcement-repair/spec.md`

## Summary

Two independent defects keep a documented safety check inert. The
workflow-identity comparison sits behind two preconditions the autopilot never
supplies, so it never runs; and the key it reports under is absent from the
`status-evidence` rule tuple, so even on the path where it does run it cannot
move the exit code. Both halves are required, and each is independently
testable.

The repair adds one unconditional helper at the top of
`_authorized_workflow_text`, routes its findings to a new
`workflow_authority_errors` problem key, and registers that single key in the
`status-evidence` tuple. A `PROBLEM_KEY_INTENT` map with a completeness test
turns every remaining advisory key from an accident into a recorded verdict.
Shipped documentation on both platforms is corrected to describe what the guard
actually does, including the one thing it does not yet do on the Claude side.

## Technical Context

**Language/Version**: Python 3.11+, standard library only (constitution II)

**Primary Dependencies**: None. No third-party imports. No new Bash or `jq`
dependency, active or otherwise.

**Storage**: N/A. The guard reads a workflow file and a state file and writes a
JSON report to stdout.

**Testing**: `unittest`, Layer 4, under `tests/speckit-pro/unit/`, declared in
`tests/speckit-pro/suite-manifest.json`. Full gate:
`python3 tests/speckit-pro/run-all.py`.

**Target Platform**: macOS locally and Linux in continuous integration. Both
filesystems matter here, which is why FR-004b mandates a byte-exact comparison
rather than one that folds case.

**Project Type**: CLI validation script shipped inside a Claude Code and Codex
plugin.

**Performance Goals**: N/A. The added work is one path resolution and one string
comparison per run.

**Constraints**: The comparison must run on the invocation the autopilot issues
(`--rule status-evidence`, no commit flags, no marker-plan schema). The existing
gated pull-request-head byte comparison must keep its current preconditions,
semantics, and reporting key. Exactly one problem key may be armed.

**Scale/Scope**: One authored guard of 4116 lines, six authored files, four
generated copies refreshed by repository tooling.

**Reviewability Budget**: Primary surface harness/adapter, secondary surface
docs/process; 337 projected reviewable LOC; 5 production files; 10 total files;
within budget. Re-declared during Tasks, from 235 LOC across 4 production files
and 9 total, when the Declared File Operations below gained its sixth entry and
the estimator was re-run on the grown requirement set. See spec.md's Reviewability
Budget revision note. Every verdict is unchanged: one slice, within budget, no
typed exception.

## Declared File Operations

- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py
- MODIFIED speckit-pro/skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/workflow-file-protocol-codex.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/SKILL.md
- MODIFIED tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py

The Codex `SKILL.md` entry was added during Tasks. FR-013c requires the
references index amended "on both platforms", and the only references-index entry
naming the protocol document on the Codex side lives in that file, so the
requirement could not be satisfied within the five entries this list originally
carried. Dropping the requirement would have violated the specification and
editing the file silently would have violated the declaration, so the declaration
was corrected instead and the estimator re-run. T021 performs the edit.

Four further tracked copies of the guard are **generated, never hand-edited**:
`dist/claude`, `dist/codex`, and the two installed-cache proofs under
`tests/speckit-pro/unit/fixtures/plugin-bash-confinement/`. They are refreshed by
`python3 scripts/refresh-release-artifacts.py` (see D7) and are deliberately
absent from the list above, both because they are not authored and because
listing them would inflate the reviewable-LOC estimate: the estimator excludes
`dist/` automatically but does not exclude the fixture path.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|---|---|---|
| I. Plugin Structure Compliance | PASS | No new plugin component. The guard stays at its existing `skills/speckit-autopilot/scripts/` path; tests stay under repository-only `tests/speckit-pro/unit/`. |
| II. Cross-Platform Runtime & Script Safety | PASS | Standard library only: `pathlib`, `json`, `re`. No `shell=True`, no `jq`, no new Bash. Path handling uses `PurePosixPath` and `Path.relative_to`, both platform-safe. |
| III. Semantic Versioning | PASS | No manual version edit. release-please owns the bump. |
| IV. Test Coverage Before Merge | PASS | New Layer 4 coverage in the existing bookkeeping-guard test file: two controlled exit-code tests plus the classification completeness test. Layer membership is already declared; the new class is registered with `build_suite()`. |
| V. Conventional Commits | PASS | Handled at commit and PR-title time, outside this plan. |
| VI. KISS, Simplicity & YAGNI | PASS | One helper function, one dict entry, one tuple entry, one classification map. No abstraction layer, no new rule name, no new CLI flag. The out-of-boundary branch is not speculative: once FR-001's unconditional resolution exists, `Path.relative_to()` raises `ValueError` on any non-subpath by ordinary Python semantics, so the branch is mechanically reachable and the only alternative to handling it is an unhandled exception. |

No violations. The Complexity Tracking table below stays empty.

## Project Structure

### Documentation (this feature)

```text
specs/art-014-phase-guard-enforcement-repair/
├── spec.md              # Feature specification (already complete)
├── plan.md              # This file
├── research.md          # Phase 0 output — the two decisions the inputs left open
├── quickstart.md        # Phase 1 output — runnable validation scenarios
├── checklists/          # Phase 4 output (not created by /speckit-plan)
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

`data-model.md` and `contracts/` are deliberately not produced. See
"Skipped design artifacts" below.

### Source Code (repository root)

```text
speckit-pro/
├── skills/speckit-autopilot/
│   ├── SKILL.md                                     # authority block corrected
│   ├── references/
│   │   └── workflow-file-protocol.md                # new authority section
│   └── scripts/
│       └── validate-autopilot-phase-coverage.py     # the one authored guard
└── codex-skills/speckit-autopilot/
    └── references/
        └── workflow-file-protocol-codex.md          # condensed mirror

tests/speckit-pro/
├── suite-manifest.json                              # already declares Layer 4
└── unit/
    └── test-autopilot-bookkeeping-guard.py          # new test class

dist/claude/, dist/codex/                            # generated copies
tests/speckit-pro/unit/fixtures/plugin-bash-confinement/  # generated proofs
```

**Structure Decision**: No new directory and no new file. Every change lands in
a file that already exists. There is exactly one authored copy of the guard;
`speckit-pro/codex-skills/speckit-autopilot/scripts/` does not exist, because the
Codex distribution ships the same `skills/` path. Both platforms therefore
inherit the repair and the new failure from a single edit, and no separate
Codex-side guard change is needed.

### Skipped design artifacts

| Artifact | Decision | Reason |
|---|---|---|
| `data-model.md` | Skipped | The spec's Key Entities are conceptual vocabulary (problem key, rule, state record), not persisted structures. This change adds no field to `autopilot-state.json`, alters no schema under `speckit-pro/skills/speckit-autopilot/contracts/`, and introduces no entity with fields, relationships, or state transitions. The one new construct, `PROBLEM_KEY_INTENT`, is a source-level constant fully specified in D4 below; a separate document would restate it and then drift from it. |
| `contracts/` | Skipped | No external interface changes. No new CLI flag, no new `--rule` value, no change to the argument grammar, no schema file touched. The report gains one key, which is an additive change to an already-unversioned stdout payload, and the classification map plus the FR-011 completeness test are the enforced record of it. |

Both skips match the workflow file's own Plan Results table, which pre-marked
each "Likely N/A" at scaffold time.

## Design

### D1. The authority helper

Add one module-level helper next to `_authorized_workflow_text`, taking the
supplied workflow path, the state path, and the state dict, and returning a list
of errors. It performs no I/O beyond the repository-root walk that
`_repository_root` already does.

Branch order is fixed by FR-004d, because an earlier skip must win over a later
failure. The table below has seven rows where FR-004d names five branches, which
is one order counted at two levels rather than a disagreement: FR-004d names the
branches carrying a requirement-level verdict, and the implementation refines them
by splitting malformed into rows 3 and 4, which must be separate for the reason
given below the table, and by making the pass explicit as row 7. D6.2 and D6.3
have the documentation carry FR-004d's five; the code carries all seven.

| # | Condition | Verdict | Requirement |
|---|---|---|---|
| 1 | `"workflow_file"` is not a key of the state | skip, return `[]` | FR-003 |
| 2 | `_repository_root(state_path)` returns `None` | skip, return `[]` | FR-006 |
| 3 | value is not a `str`, or is empty, or is whitespace-only | fail, malformed | FR-005 |
| 4 | value is not a normalized repository-relative path | fail, malformed | FR-005 |
| 5 | supplied workflow resolves outside the repository root | fail, out-of-boundary | FR-004c |
| 6 | the two references differ | fail, identity mismatch | FR-004, FR-004b |
| 7 | otherwise | pass, return `[]` | — |

Six details are load-bearing and each has a specific failure mode if got wrong:

**Branch 1 tests key membership, not value.** Use `"workflow_file" not in state`,
never `state.get("workflow_file") is None`. The spec's edge cases classify an
explicit `null` as **malformed** ("a non-string value, such as a number, a list,
or null"), while an absent key **skips**. A `.get()` test collapses the two and
lets an explicitly nulled field become the silent opt-out FR-005 exists to
prevent.

**Branch 3 must be explicit, and must precede branch 4.** Verified during
Clarify: `_is_normalized_repo_path("  ")` and `_is_normalized_repo_path(" ")`
both return `True`, because a run of spaces is a valid POSIX path part. Without
its own check, a whitespace-only value falls through to branch 6 and is reported
as an identity mismatch with a blank path, which is the wrong error class and an
unreadable message.

**Branch 4's rule is the existing helper's, and it is stricter than "looks like a
path".** `_is_normalized_repo_path` accepts a value only when it is a non-empty
`str`, contains no backslash anywhere, does not begin with `/`, does not begin
with a Windows drive prefix matching `^[A-Za-z]:`, round-trips through
`PurePosixPath` unchanged, and has no path part equal to `""`, `"."`, or `".."`.
Measured against the working tree, each of these is therefore malformed: a
Windows-style `docs\ai\x-workflow.md`, a drive-absolute `C:/repo/x.md`, a
POSIX-absolute `/repo/docs/x-workflow.md`, a traversing `../x-workflow.md`, a
same-directory `./x-workflow.md`, a doubled-separator `docs//x-workflow.md`, and
a trailing-separator `docs/x/`. A repository-relative
`docs/ai/specs/.process/ART-014-workflow.md` is accepted. Case is not folded, so
`A/B.MD` is accepted too, which is what keeps branch 4 consistent with FR-004b
rather than quietly normalizing a mis-cased value into a match. This is the rule
FR-004a means when it says the state value is already constrained to a normalized
repository-relative form; branch 4 is where that constraint is enforced on read.

**Resolution is asymmetric, by FR-004a.** The **supplied** side is resolved
against the repository root and rendered as POSIX
(`workflow.resolve().relative_to(repo_root.resolve()).as_posix()`), which is what
lets a correct workflow supplied through a symlink or as a relative path still
match. The **state** side is compared as the literal string it holds, with no
filesystem resolution, because it is machine-written and already constrained to a
normalized repository-relative form. Only the supplied side has spelling freedom.

**Comparison is byte-exact.** A plain `!=` between the two strings. No
`str.lower()`, no `os.path.samefile`, no `Path.samefile`. Byte-exact is the only
rule that returns the same verdict on the case-insensitive filesystem this
repository is developed on and the case-sensitive one it is tested on.

**No branch raises; every outcome is a return.** The helper must report through
its return value and never by propagating an exception, because `build_report`
has no handler for one and an uncaught exception prints a traceback instead of
the JSON report the autopilot parses. Each operation the helper performs was
checked against an invoked result rather than assumed:

- `"workflow_file" not in state` cannot raise. `load_state` rejects a non-object
  state with `ValidationError` at `validate-autopilot-phase-coverage.py:324`,
  before `build_report` reaches the helper, so the argument is always a mapping.
- `_repository_root` walks parents calling `Path.exists()`, which returns `False`
  rather than raising even on a pathological path. Measured: `Path.exists()` on a
  symlink loop returned `False`.
- `Path.resolve()` is the one operation that can raise. Measured on Python
  3.11.0: resolving a path through a symlink loop raised `RuntimeError`, while
  resolving a merely nonexistent path did not raise. The design must not depend
  on that staying true across interpreter versions, and it does not have to.
  `read_text(workflow)` runs first, and a path that was read successfully was
  traversable, so by the time the helper resolves the supplied workflow the loop
  case has already exited with the input-error code. Measured: reading through
  the same symlink loop raised `OSError` (`ELOOP`), which `read_text` converts to
  `ValidationError`. `repo_root.resolve()` is safe for the same reason, because
  `load_state` already read a file beneath that root. This is why the call order
  fixed in D2 is load-bearing rather than cosmetic, and it is what keeps the
  specification's symlink-traversal allowance in FR-004a free of a crash path.
- `relative_to()` raises `ValueError` for a non-subpath, which is branch 5 by
  design rather than an escape.
- `_is_normalized_repo_path` accepts any object and returns `False` for a
  non-string, so branch 4 cannot raise on a malformed value.

Messages:

- Branch 5 reuses the sentence the same file already emits at
  `validate-autopilot-phase-coverage.py:1325`, `workflow file is outside the
  authorized repository`. The FR-009 prefix governs the identity-mismatch
  message only; an out-of-boundary path has no repository-relative form to print
  in a mismatch message, so a distinct sentence tells the maintainer what is
  actually wrong.
- Branches 3 and 4 reuse the sentence already at `:1331`, `autopilot state
  workflow_file is not a normalized repository-relative path`.
- Branch 6 opens with the exact documented sentence, unmodified, and appends both
  compared paths after it (FR-009):

  ```text
  supplied workflow does not match autopilot state workflow_file authority: supplied <resolved-supplied-ref>, state names <literal-state-value>
  ```

  Tests assert the prefix, never the full string, so path formatting can change
  without breaking them.

### D2. Return shape, and why the gated path keeps its own key

This is the one place the settled constraints underdetermine the code, so it is
pinned here. Full rationale and the rejected alternative are in
[research.md](./research.md) (R1).

`_authorized_workflow_text` currently returns `tuple[str, list[str]]`, and
`build_report` folds that single list into `workflow_checkpoint_errors` at
`:4031-4033`. Verified that `build_report` is the **only** consumer: the sole
references in the guard are the definition at `:1298` and the single unpacking
call at `:4022`, so widening the return touches exactly one call site. Widen it
to a **3-tuple**, `(text, checkpoint_errors, authority_errors)`:

- The helper is called unconditionally, immediately after the existing
  `read_text(workflow)` call and before the marker-plan and expected-commit gate,
  and its result becomes the third element on every return path, including the
  two early returns. That satisfies FR-001's placement and the settled constraint
  that the two early returns stop returning `[]` and start returning the helper's
  errors. Keeping `read_text` first is deliberate. It is what makes the
  specification's missing-supplied-workflow edge case true as written: reading
  the supplied workflow stays the first statement of the function, so a supplied
  path that cannot be read raises `ValidationError` and the run exits with the
  input-error code before the comparison is reached. The observable outcome is
  the same under either order, because that exception propagates out of
  `build_report` before any report prints, but only this order matches what the
  specification says happens, and only this order discharges the no-raise
  argument in D1.
- The **second** element keeps carrying exactly what it carries today, and keeps
  folding into `workflow_checkpoint_errors`.

Re-keying the function's whole error return to `workflow_authority_errors` is the
smaller diff and is wrong. The gated path produces its own errors below the early
returns (`workflow repository root is unavailable`, the `expected_head_commit`
authority error, `workflow is absent from the authorized PR head`, `workflow at
the authorized PR head is not UTF-8`, and the byte mismatch). Moving those to the
new key would change the reporting semantics of the gated comparison, which FR-002
forbids, and would newly arm all of them under `status-evidence` for the Codex
flow that does supply live commit values, which is exactly the blast radius FR-008
exists to prevent.

**Accepted consequence.** On the gated path only, a mismatch is reported twice:
once by the helper under `workflow_authority_errors`, and once by the untouched
identity check at `:1333-1336` under `workflow_checkpoint_errors`. The two are
not the same string. The helper's message carries the FR-009 prefix followed by
both compared paths; the untouched check keeps the bare sentence, because
`test_changed_file_manifest_must_match_base_to_head` in
`tests/speckit-pro/unit/test-autopilot-phase-coverage.py` asserts that exact list
element in `workflow_checkpoint_errors`. The gated text is therefore load-bearing
and FR-002 freezes it, which is why FR-009 is scoped to the new key. This is
deliberate. Removing the second occurrence would change gated-path semantics and
would also remove the early return that currently short-circuits the PR-head byte
comparison. Duplication is the price of FR-002 and is recorded here so it is not
mistaken for a defect during Analyze or review.

### D3. Report assembly and rule registration

Both halves are required; neither alone repairs the defect.

1. In `build_report`, delete the
   `workflow_checkpoint_result["workflow_checkpoint_errors"].extend(...)` fold
   and give the new key its **own** dict in the `problems` merge, alongside the
   eight per-check dicts already merged there. An `extend` into an existing dict
   would put the errors under an existing key and arm nothing new.
2. In `RULE_PROBLEM_KEYS`, add `"workflow_authority_errors"` to the
   `status-evidence` tuple, and to nothing else. Do **not** add
   `workflow_checkpoint_errors`: it is produced at four other sites by
   `validate_workflow_checkpoint_bindings`, all of which check PR Marker Plan
   Evidence table bindings, and widening it would arm every one of them at once
   against a corpus that has never had to satisfy them.

Post-change arithmetic, which SC-006 pins: emitted keys 20 → 21; keys reachable
by a named rule 8 → 9 (`status-evidence` 3 → 4, `coverage` unchanged at 5);
advisory keys stay at 12; no existing key changes reachability.

### D4. The classification record

Add a module-level `PROBLEM_KEY_INTENT` mapping every emitted key to a verdict
from the closed three-value vocabulary and a reason. Two values are insufficient,
because the Clarify audit found keys that are advisory by accident rather than by
design.

| Verdict | Count | Keys |
|---|---|---|
| `gated` | 9 | `workflow_status_evidence_errors`, `state_status_errors`, `stage_mirror_errors`, `workflow_authority_errors`, `missing_workflow_sections`, `missing_workflow_tokens`, `missing_workflow_post_items`, `missing_state_prefixes`, `missing_state_post_items` |
| `advisory-accidental` | 3 | `in_progress_errors`, `duplicate_state_steps`, `state_order_errors` |
| `advisory-deliberate` | 9 | `changed_file_manifest_errors`, `checkpoint_evidence_errors`, `checkpoint_file_errors`, `checkpoint_source_fingerprint_errors`, `completed_phase_pending_fields`, `emission_mapping_errors`, `marker_plan_status_errors`, `projection_status_errors`, `workflow_checkpoint_errors` |

The three `advisory-accidental` verdicts are required by FR-010b and each reason
must name **ART-017** as the follow-up that will arm them. The shipped
justification for advisory status is that the existing workflow corpus predates
the checks, which is true of the coverage lists and false of these three: they
are invariants of the state file the current run just wrote, so no legacy
artifact can violate them. This specification records the verdict and does not
arm them.

FR-010a governs reason quality: restating the key name is not a reason. An
`advisory-deliberate` reason must say what makes advisory status correct for that
key; an `advisory-accidental` reason must name the follow-up.

### D5. Tests

One new test case class in the existing file, registered with `build_suite()`,
which enumerates its classes explicitly and will otherwise silently skip it.

**Shared fixture builder (FR-012).** One builder parameterized by exactly one
value, the state's `workflow_file`, so the pair is a controlled comparison. It
must:

- create a temporary root and write a repository-root marker there **as a file,
  not a directory**. `_repository_root` tests `(candidate / ".git").exists()`,
  which is satisfied by either, and writing it as a file also exercises the
  worktree case that every real autopilot run for this repository takes. Without
  the marker, branch 2 skips and **both controls pass vacuously**, which is the
  precise trap Clarify session 2 recorded;
- write the workflow under a repository-relative subpath of that root, and the
  state beside it;
- set the state's `workflow_file` to a repository-relative path against that root,
  never an absolute one, which branch 4 would reject as malformed;
- invoke the guard by subprocess with the autopilot's own invocation:
  `--rule status-evidence`, no commit flags, no marker-plan schema;
- return the exit code and the parsed report.

**Negative control**: state names a different workflow. Assert a non-zero exit, a
non-empty `workflow_authority_errors`, and that the message starts with the FR-009
prefix.

**Positive control**: state names the matching workflow. Assert exit zero and an
empty `workflow_authority_errors`.

Two separate methods, so each failure names its own claim.

**Absent-field skip (FR-003).** Neither control exercises branch 1, because both
set `workflow_file` and differ only in its value; the existing `RuleScopingTests`
sets it too and reaches branch 2 rather than branch 1. Add a third method,
deliberately outside the FR-012 controlled pair so that pair keeps differing in
exactly one value, asserting that a state carrying no `workflow_file` key at all
exits zero with an empty `workflow_authority_errors` against the same
repository-marked fixture root. Branch 1 is the branch that keeps a tracked state
slot carrying no `workflow_file` working, and it is the one skip the corpus
evidence cannot demonstrate, because every synthesized corpus state sets the
field. Without this method the absent-field guarantee rests on reading the code.

**Completeness test (FR-011)**: build a **real** report, subtract the four
metadata keys (`status`, `workflow_file`, `state_file`, `plan_step_count`), and
assert the remaining key set is covered by `PROBLEM_KEY_INTENT`, naming any key
that is missing. Deriving the set from a second hardcoded list is forbidden,
because a parallel list drifts exactly as the classification record itself could.
Also assert every verdict is drawn from the closed vocabulary and every reason is
non-empty.

**The invariant that single report depends on, and its limit.** One report
suffices only because every per-check function returns its full key set on every
return path, including its early returns, so a key is never conditionally absent
from the report. That is what makes the derived set the complete set rather than
a sample. It was verified during planning and re-verified during Checklist two
ways: by comparing the report key sets produced by a thin synthesized state and
by the tracked current-run state, which are identical at 24 keys, 20 problem plus
4 metadata; and by reading every problem-key return in the guard, all of which
are uniform per function. Record it here because it is a property of the code the
test relies on rather than a property the test checks. The limit follows
directly: a key added by a future specification is caught only if it is emitted
the same unconditional way. A future key emitted only under some state shapes
would be absent from this fixture's report and would pass unclassified, and the
correct response then is to extend the fixture to a state shape that emits it,
never to relax the assertion.

**Latent regression to verify, not to paper over.** The existing
`RuleScopingTests._run` writes an **absolute** path into the state's
`workflow_file` and creates no repository marker in its temporary root. Today
that is inert. After this change those three tests newly flow through the helper
and stay green only because branch 2 skips: no `.git` resolves above a system
temporary directory on either platform. Re-run them. If any turns red, the
correct fix is to make that fixture's `workflow_file` repository-relative against
a root it controls, never to weaken the helper.

A second file needs the same re-run, and for the opposite reason.
`tests/speckit-pro/unit/test-autopilot-phase-coverage.py` owns the only committed
coverage of the gated pull-request-head error paths FR-002 freezes, and its
`test_changed_file_manifest_must_match_base_to_head` runs `git init` on its
temporary root so the gated path can work at all. Branch 2 therefore does **not**
skip there. Every validator run inside that fixture resolves a repository root
and newly flows through branches 3 to 6 for real. It stays green by
construction, because the fixture sets the state's `workflow_file` to
`workflow.md` and writes the supplied workflow at that same repository-relative
path, so the comparison matches and the runs that assert exit zero keep
asserting it. That is a fixture detail rather than an intent, which is why it is
recorded as a verification step on the same terms as the paragraph above. Re-run
the file, expect green, and if it turns red repair the fixture rather than the
helper. The file is verified rather than modified, so it stays out of the
Declared File Operations list.

### D6. Documentation

Apply the prose staged verbatim in the workflow file's "Session 3 Staged
Documentation Prose" section. Clarify settled the wording; Implement applies it
without redrafting.

1. Replace the Claude `SKILL.md` authority block, correcting the three statements
   FR-013a names: the unqualified "the authority" claim, the exact-full-string
   claim, and the lead-in's repair claim, which moves into the marker-evidence
   bullet where it is still true. Preserve the FR-004a asymmetry through the
   compression: "malformed **state** value" is the state side, "supplied workflow
   that resolves outside the repository" is the supplied side. Do not blur them
   into one phrase about values.
2. Add a `## workflow_file State Authority` section to
   `references/workflow-file-protocol.md`, placed after the `Stage` section and
   before PR Marker Plan Evidence, carrying the five ordered branches, the
   asymmetry, and the byte-exact rule.
3. Append a condensed mirror of that section to
   `codex-skills/speckit-autopilot/references/workflow-file-protocol-codex.md`.
4. Add the Claude-side expected-commit paragraph directly after the guard
   invocation block, mirroring where Codex carries it, stating the same append
   contract **and** that the Claude flow does not yet fetch those values, citing
   **ART-016**.
5. Amend the references index descriptor on both platforms (FR-013c), so the new
   content is reachable from the index rather than only by full-text search.

The division of labour is fixed by FR-013b: the skill document keeps the
quotable sentence and names both skip conditions, because an operator whose run
halts greps the skill body for the sentence they just saw; the protocol reference
owns the branch order and the reason behind each verdict. The skill document must
not become a second copy of the truth table, and must not be reduced to a bare
pointer that removes the quotable sentence.

**Explicitly out of scope**: no new Layer 1 assertion and no
`CODEX-PARITY-NOTES.md` entry. That file's stated scope is recording where the
two variants are deliberately *not* mirrors and listing the strings the validator
pins. This change is parity-restoring and pins nothing, so an entry would make
that ledger wrong.

### D7. Generated artifacts

Editing the guard restales four tracked copies. Run
`python3 scripts/refresh-release-artifacts.py` and commit the result. CI's
`artifact-consistency` job fails the pull request if this is skipped, so a stale
payload cannot land.

Because a `.md` and `.py` file under `tests/speckit-pro/` changes, also
regenerate the committed docs-site test reference page, per that directory's
scoped rule. `docs-site/` is the only surface needing a bootstrap in a fresh
worktree.

The Layer 6 Codex qualification corpus is **not** affected: it binds a digest
chain over agent definition source bytes, and no agent definition changes here.

### D8. Corpus regression, after-half

The before-half is already measured and recorded in the workflow file: 54 of 54
exit 0, and the canary exits 0. Reuse that exact harness so the pair is
comparable:

- denominator pinned to the baseline commit `3af4764e`, whose file list is
  produced by `git ls-tree -r --name-only 3af4764e -- docs/ai/specs/.process/`
  filtered to names ending `-workflow.md`, and which returns 54. Recording the
  commit here rather than only in the workflow file is what makes the denominator
  reproducible from the authored artifacts alone. It cannot drift as new
  specifications land, and this specification's own in-flight workflow is
  excluded by construction because it is not in the baseline tree;
- the same synthesized state shape, including the `plan` array and a
  repository-relative `workflow_file`;
- the state written to a path **inside** the repository. This is load-bearing:
  the repository root is derived from the **state** path, so a state in a scratch
  directory outside the tree resolves no root, every comparison skips under
  FR-006, and all 54 files report a pass while proving nothing;
- the state path **passed in a form the root walk can resolve from**, which is a
  second condition rather than a restatement of the first. When the before-half
  was measured the walk read the state path as supplied, not a resolved form, so
  a relative state argument had a parents chain terminating at the working
  directory: writing the file inside the repository and then naming it relatively
  from a subdirectory resolved no root and produced the same 54 vacuous passes.
  FR-006b closes that in the repaired guard, so the after-half does not depend on
  the spelling. Keep the condition for both halves regardless. Reusing the
  identical harness is what makes the pair comparable, and recording the form
  used is what lets a reader distinguish a genuine after-half pass from one the
  old walk would also have produced. Pass it absolute, or relative with the
  working directory at the repository root, and record which was used;
- the same invocation;
- the deliberately mismatched canary in the same harness.

Expected after: 54 of 54 still exit 0, and the canary flips from 0 to **1** with
a non-empty `workflow_authority_errors`. The canary is the whole point. Fifty-four
passes prove nothing alone, because a skipped comparison and a satisfied
comparison both exit 0. If the canary still exits 0, the repair did not take
regardless of what the other 54 report.

This proof stays a one-time recorded run and must **not** be wired into the
committed suite: the process directory holds live data, an in-flight
specification mid-repair can legitimately fail the guard, and a committed corpus
walk would turn CI red on unrelated pull requests.

### Implementation order

Each step is independently verifiable, and the order keeps the two halves of the
defect separable for review.

1. D1 helper plus D2 return shape. The comparison now runs and reports, but under
   an unarmed key, so the exit code does not move yet.
2. D3 report assembly and rule registration. The negative control now fails the
   run. This is the step that makes SC-001 true.
3. D5 controls and the completeness test.
4. D4 classification map, sized against the completeness test until it passes.
5. D6 documentation.
6. D7 artifact regeneration.
7. D8 after-half evidence run, recorded in the workflow file and the PR body.
8. `python3 tests/speckit-pro/run-all.py`, zero failures (SC-008).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. No entries.
