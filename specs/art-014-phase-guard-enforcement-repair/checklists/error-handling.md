# Error-Handling Checklist: Phase-Guard Enforcement Repair

**Purpose**: Validate that the requirements describing this guard's error
behavior are complete, unambiguous, internally consistent, and objectively
verifiable — before implementation begins. This is a unit test suite for the
English, not for the code.

**Created**: 2026-08-12

**Feature**: [spec.md](../spec.md)

**Depth**: Formal gate. The subject is a safety check that shipped inert for
several releases, so the bar is that every branch's outcome, message, and exit
consequence is written down rather than inferable.

**Audience**: Reviewer, at pull-request time.

**Scope note**: Items evaluate the requirements in `spec.md`, `plan.md`, and
`research.md`. Decisions listed as settled in the domain brief are not
reopened; where an item touches one, it is recorded as closed by prior
decision with the citation.

## Branch Coverage — Requirement Completeness

- [x] CHK001 Does the requirement set assign a stated outcome to every branch of
  the skip-versus-fail truth table: absent field, unresolvable repository root,
  non-string value, explicit null, empty string, whitespace-only string,
  non-normalized path, out-of-boundary resolution, mismatch, and match?
  [Completeness, Spec §FR-003, §FR-004, §FR-004c, §FR-005, §FR-006, Plan §D1]
- [x] CHK002 Is the skip verdict for an absent `workflow_file` separated from the
  fail verdict for an explicitly null one, with the distinguishing test named
  rather than left to the reader? [Clarity, Spec §FR-003 + Edge Cases, Plan §D1,
  Research §R2]
- [x] CHK003 Is the whitespace-only case required to carry its own explicit
  check, with the measured evidence that makes delegation to the existing
  normalized-path helper unsafe? [Completeness, Spec §FR-005]
- [x] CHK004 Are the out-of-boundary condition and the unresolvable-root
  condition distinguished as two different facts carrying opposite verdicts,
  with the reason for the asymmetry stated? [Clarity, Spec §FR-004c vs §FR-006]
- [x] CHK005 Is the matching-path outcome stated as its own branch rather than
  left implicit as the absence of a failure? [Completeness, Spec §FR-012,
  Plan §D1]
- [x] CHK006 Is it stated which of the two supplied inputs the repository root is
  derived from, given that the choice decides whether the comparison runs at
  all? [Clarity, Spec §PR Review Packet Requirements, Plan §D1, §D8]

## Branch Ordering — Requirement Clarity

- [x] CHK007 Is the evaluation order stated as a requirement, together with the
  reason that an earlier skip must win over a later failure? [Clarity,
  Spec §FR-004d]
- [x] CHK008 Is the plan's branch table consistent with the ordered branch list
  the specification fixes, with any additional rows readable as a refinement
  rather than a divergence? [Consistency, Spec §FR-004d, Plan §D1]
- [x] CHK009 Is the ordering's observable effect bounded — that is, do the stated
  reasons cover every pair of conditions that can hold at once and produce
  different verdicts? [Coverage, Spec §FR-004d]

## Failure Messages — Requirement Precision

- [x] CHK010 Is the identity-mismatch message prefix stated in the specification
  itself, to the same precision the out-of-boundary sentence is stated, so that
  the string a test must assert is readable without opening shipped
  documentation? [Resolved, Clarity, Spec §FR-009 vs §FR-004c, §FR-012]
  - Resolution: FR-009 now quotes the sentence verbatim, matching the guard's
    own text. Previously it referred to the sentence only indirectly while
    FR-004c quoted its own sentence, and FR-012 asked a test to assert a prefix
    the specification never stated.
- [x] CHK011 Is the out-of-boundary message assigned explicitly and fenced off
  from the identity-mismatch prefix? [Consistency, Spec §FR-004c, Plan §D1]
- [x] CHK012 Is a message specified for the malformed-value branches, distinct
  from the identity message? [Completeness, Spec §FR-005, Plan §D1]
- [x] CHK013 Is it stated that the two skip branches emit no message and no
  error entry at all? [Clarity, Spec §FR-003, §FR-006]
- [x] CHK014 Is it stated that after this change the guard carries two identity
  messages whose text differs, the untouched gated one and the new prefixed one,
  so that a reader does not take FR-009 to have rewritten the gated message?
  [Resolved, Ambiguity, Spec §FR-002, §FR-009, Plan §D2]
  - Resolution: FR-009 is now scoped to the message reported under
    `workflow_authority_errors` and states that the gated message keeps the bare
    sentence. Plan §D2's accepted-consequence paragraph names the divergence and
    cites the committed test that makes the gated text load-bearing. As written
    before, FR-009 read as a blanket instruction that would have contradicted
    FR-002.
- [x] CHK015 Is the message required to name both compared values, so the
  operator can identify the disagreement without opening either file?
  [Measurability, Spec §FR-009, §SC-003]

## Exit-Code Semantics — Requirement Completeness

- [x] CHK016 Is it stated, where the skip branches are defined, that a skipped
  comparison and a satisfied comparison are indistinguishable from the exit
  code, and that this is accepted rather than overlooked? [Resolved,
  Completeness, Spec §FR-003, §FR-006]
  - Resolution: FR-006 now records the equivalence for both skip branches and
    names the compensating evidence. The property was previously stated only
    inside test-fixture rationale (FR-012) and corpus-evidence rationale
    (Plan §D8), so a reader of the skip requirements themselves would not meet
    it.
- [x] CHK017 Is a compensating control named for that indistinguishability, so
  a clean corpus result cannot be mistaken for proof the comparison ran?
  [Coverage, Spec §PR Review Packet Requirements, Plan §D8]
- [x] CHK018 Is the input-error exit path distinguished from the
  rule-violation exit path, so a control asserting only "non-zero" cannot be
  satisfied by an unrelated input failure? [Clarity, Spec §Edge Cases, §FR-012]
- [x] CHK019 Is it stated that a state lacking the fields the guard requires
  before reporting exits as an input error regardless of the comparison's
  verdict, so the evidence harness must supply them? [Coverage, Spec §PR Review
  Packet Requirements]
- [x] CHK020 Is the new problem key required to appear in the report on skip and
  on pass, rather than only when it carries an error? [Completeness,
  Spec §FR-011, §FR-012, Plan §D3]

## Exception Safety — Requirement Coverage

- [x] CHK021 Is it stated that every branch of the new comparison returns an
  error rather than raising, and is that claim discharged for each operation the
  comparison performs, including the path resolution that FR-004a explicitly
  requires to tolerate symlink traversal? [Resolved, Coverage, Spec §FR-004a,
  Plan §D1, §Constitution Check VI]
  - Resolution: Plan §D1 gains a no-raise section discharging the claim per
    operation against invoked results. The material finding: `Path.resolve()`
    raised `RuntimeError` on a symlink loop under Python 3.11.0, which the
    artifacts had not accounted for even though FR-004a blesses symlink
    traversal. Reading the supplied workflow first makes that path unreachable,
    which is why the call order in §D2 is load-bearing.
- [x] CHK022 Is the non-subpath failure accounted for as a handled branch rather
  than an unhandled exception? [Coverage, Plan §Constitution Check VI, §D1]
- [x] CHK023 Is the state argument established as a mapping before membership is
  tested, so the absent-field branch cannot itself raise? [Coverage,
  Plan §D1, Research §R2]

## Consistency With The Untouched Gated Path

- [x] CHK024 Do the specification and the plan agree on where the comparison is
  invoked relative to reading the supplied workflow, given that the
  specification's account of the missing-file case depends on that order?
  [Resolved, Conflict, Spec §Edge Cases, Plan §D2]
  - Resolution: Plan §D2 said the helper is called "on the first line", which
    would have placed it before `read_text(workflow)` and made the
    specification's stated mechanism false. §D2 now pins the call immediately
    after that read and before the gate, satisfying FR-001 unchanged. The
    specification was not edited, because it was already correct.
- [x] CHK025 Are the gated path's error paths enumerated somewhere, so that
  "preconditions and semantics unchanged" is a verifiable claim rather than an
  assurance? [Measurability, Spec §FR-002, Research §R1, Plan §D2]
- [x] CHK026 Is the gated path's reporting key stated to be unchanged, and is the
  rejected alternative that would have changed it recorded with its blast
  radius? [Consistency, Spec §FR-002, §FR-008, Research §R1]
- [x] CHK027 Is the double report on the gated path recorded as accepted, so a
  later reviewer does not read it as a defect? [Assumption, Plan §D2,
  Research §R1]
- [x] CHK028 Is the report's schema surface accounted for, so that adding a
  problem key is known not to break an existing contract? [Dependency,
  Plan §Skipped design artifacts]

## Verification Requirements

- [x] CHK029 Does the plan identify every existing test path that newly flows
  through the now-unconditional comparison, rather than only the ones in the
  file the change edits? [Resolved, Coverage, Plan §D5, Research §R3]
  - Resolution: Plan §D5 covered only `RuleScopingTests`, reasoning that no
    repository marker resolves above a temporary directory. That reasoning does
    not hold for `tests/speckit-pro/unit/test-autopilot-phase-coverage.py`,
    which git-initialises its temporary root so the gated path can run, and
    which owns the only committed coverage of the FR-002 error paths. §D5 now
    names it, states why branch 2 does not skip there, and records why it stays
    green.
- [x] CHK030 Are the negative and positive controls required to differ in exactly
  one input, so each failure names its own claim? [Measurability, Spec §FR-012]
- [x] CHK031 Is the fixture condition that would otherwise make both controls
  pass vacuously stated as a requirement rather than left to the implementer?
  [Coverage, Spec §FR-012, Plan §D5]
- [x] CHK032 Is the completeness test required to derive the emitted key set from
  a real report rather than a parallel list, so the record cannot drift?
  [Measurability, Spec §FR-011]

## Closed By Prior Decision

Recorded so a reader does not reopen them. No artifact edit is warranted for
any item in this section.

- Which branch skips and which fails: settled in the design concept Q3 and Q4,
  and carried into Spec §FR-003, §FR-004c, §FR-005, §FR-006.
- The dedicated `workflow_authority_errors` key and arming only that key:
  settled in design concept Q2 and Q6, carried into Spec §FR-007, §FR-008.
- Byte-exact comparison with no case folding and no filesystem identity test:
  Spec §FR-004b.
- The asymmetry between resolving the supplied side and taking the state side
  literally: Spec §FR-004a.
- Keeping the documented sentence as a prefix rather than rewriting it: design
  concept Q9, carried into Spec §FR-009.
- The corpus proof staying a one-time recorded run rather than a committed
  test: design concept Q10, carried into Spec §Assumptions and Plan §D8.

## Notes

- Items carrying a gap marker are findings to remediate in `spec.md` or
  `plan.md`.
- Items without a gap marker were evaluated and found satisfied; the bracketed
  reference names where the requirement already lives.
