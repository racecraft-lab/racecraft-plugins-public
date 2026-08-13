# Research: Phase-Guard Enforcement Repair

**Feature**: `art-014-phase-guard-enforcement-repair` | **Date**: 2026-08-12

## Scope of this document

The Technical Context in [plan.md](./plan.md) carries **zero** `NEEDS
CLARIFICATION` markers, and the specification carries zero open markers. Three
Clarify sessions plus a three-item consensus panel settled the technology, the
comparison semantics, the reporting contract, the branch order, and the
documentation wording, and those settled decisions are not reopened here.

What remains are three points the settled inputs did not determine, each found by
reading the code during planning rather than inherited from the interview. Each
is recorded with the alternative that was rejected and why, because each one is a
place where the obvious implementation is wrong in a way that would still pass a
casual review.

---

## R1. Return shape of `_authorized_workflow_text`

**Decision**: Widen the return to a 3-tuple, `(text, checkpoint_errors,
authority_errors)`. The helper's findings occupy the new third element on every
return path. The second element keeps carrying exactly what it carries today and
keeps folding into `workflow_checkpoint_errors`.

**Rationale**: The settled constraint says the two early returns stop returning
`[]` and start returning the helper's errors, and that the gated pull-request-head
byte comparison below them is untouched. It does not say what happens to the
errors the **gated** path produces on the fall-through, and that gap has a wrong
answer that is easy to reach.

Today `build_report` folds the function's single error list into
`workflow_checkpoint_errors`. That list is not only the identity error. Below the
two early returns the same function produces `workflow repository root is
unavailable`, the `expected_head_commit` authority error, `workflow file is
outside the authorized repository`, the non-normalized reference error, `workflow
is absent from the authorized PR head`, and `workflow at the authorized PR head is
not UTF-8`.

The design-concept Q2 wording is the tiebreaker: "The **identity** errors stop
being folded into `workflow_checkpoint_errors`." Identity errors only. A 3-tuple
routes exactly those to the new key and leaves everything else where it is.

**Alternative considered and rejected**: Re-key the function's whole error return
to `workflow_authority_errors`. This is a one-line change and it is wrong twice
over. It changes the reporting key of the gated comparison, which FR-002 forbids
("MUST keep its current preconditions and semantics unchanged"). And because the
new key is registered in `status-evidence`, it would newly arm every gated-path
error for the Codex flow that genuinely supplies live commit values, which is
precisely the unmeasured blast radius FR-008 exists to prevent. FR-008 blocks that
outcome by one route; this alternative reaches the same outcome by another.

**Accepted consequence**: on the gated path only, a mismatch is reported under
both keys, because the untouched identity check runs again below the early
returns. Removing the second occurrence would change gated-path semantics and
would also remove the early return that currently short-circuits the byte
comparison. The duplication is the price of FR-002 and is recorded so it is not
later mistaken for a defect.

---

## R2. Distinguishing an absent `workflow_file` from an explicitly null one

**Decision**: Branch 1 tests key membership, `"workflow_file" not in state`.

**Rationale**: FR-003 skips when the state "carries no `workflow_file`", while the
edge cases classify a non-string value "such as a number, a list, or **null**" as
malformed, which fails. Those are two different states of the same field and the
requirements assign them opposite verdicts.

The natural idiom, `state.get("workflow_file") is None`, cannot tell them apart:
it returns `None` both for a missing key and for a key explicitly set to JSON
`null`. Using it would make an explicitly nulled field skip the comparison
silently. That is the exact failure mode FR-005 was written to close, in the exact
words the specification uses for it: "an emptied field cannot become a silent
opt-out."

The distinction is reachable in practice, not theoretical. Both tracked state
slots are machine-written, and a writer that emits a key with a null value is an
ordinary serialization outcome.

**Alternative considered and rejected**: a sentinel default,
`state.get("workflow_file", _MISSING)`. It is correct and it works. Membership
testing was preferred because it needs no module-level sentinel object, reads as
the question being asked, and satisfies constitution VI's preference for explicit
over implicit.

---

## R3. The existing `RuleScopingTests` fixture newly flows through the helper

**Decision**: Keep the helper as specified and re-run the existing tests as a
verification step. If any turns red, repair the fixture, never the helper.

**Rationale**: `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py`
already builds a state whose `workflow_file` is an **absolute** path, in a
temporary root with no repository marker. Today that value is never read, because
the comparison never runs on the plain invocation. After this change all three
`RuleScopingTests` methods flow through the new helper.

They stay green, but for a reason worth stating rather than assuming: branch 2
skips first. `_repository_root` walks parents looking for `.git`, and no `.git`
resolves above a system temporary directory on either macOS or Linux. Branch 4,
which would reject the absolute path as malformed, is never reached.

That is a real dependency on environment rather than on intent, so it is a
verification step rather than a claim. It also explains why FR-012 requires the
**new** fixture to write a repository-root marker: without one, the new controls
land in the same skip and both pass vacuously, proving nothing. The old fixture's
accidental skip and the new fixture's deliberate marker are two sides of the same
mechanism.

**Alternative considered and rejected**: pre-emptively rewrite the existing
fixture to use a repository-relative `workflow_file`. Rejected as scope growth
under constitution VI and the repo's surgical-changes rule. The three tests are
not this specification's subject, they pass, and touching them would add diff
that traces to no requirement. If the re-run disagrees, the repair becomes
necessary and is then justified by evidence.

---

## Measurements taken during planning

Recorded because the specification's Assumptions section states that a
re-measurement which disagrees is drift to report, not a number to quietly
change. Both agree.

| Fact | Spec claim | Measured during planning | Method |
|---|---|---|---|
| Emitted problem keys | 20 | 20 | Ran the guard and counted report keys minus the four metadata keys |
| Keys reachable by a named rule | 8 | 8 | `status-evidence` 3 + `coverage` 5 in `RULE_PROBLEM_KEYS` |
| Advisory keys | 12 | 12 | 20 − 8 |
| One authored guard copy | 1 | 1 | No `codex-skills/speckit-autopilot/scripts/` directory exists |

Also confirmed: a single report emits every problem key regardless of state
content, because each per-check function always returns its keys. One real report
is therefore sufficient input for the FR-011 completeness test.

Line references confirmed against the working tree, since the design concept
recorded that the roadmap's line numbers had drifted once already:
`_authorized_workflow_text` at `:1298`, its two early returns at `:1310` and
`:1312`, the out-of-boundary sentence at `:1325`, the malformed sentence at
`:1331`, the identity sentence at `:1335`, `RULE_PROBLEM_KEYS` at `:239-254`,
the fold into `workflow_checkpoint_errors` at `:4031-4033`, the `problems` merge
at `:4050-4059`, and the exit-code scoping at `:4111-4114`.

Verified that `build_report` is the **only** consumer of
`_authorized_workflow_text`: the sole references in the guard are the definition
at `:1298` and the single unpacking call at `:4022`. Widening the return to a
3-tuple therefore touches exactly one call site, which is what makes R1's
decision a two-line change rather than a refactor.
