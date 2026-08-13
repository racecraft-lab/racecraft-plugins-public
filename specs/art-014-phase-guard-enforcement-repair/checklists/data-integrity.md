# Data-Integrity Checklist: Phase-Guard Enforcement Repair

**Purpose**: Validate that the requirements governing this guard's *data* are
complete, unambiguous, internally consistent, and objectively verifiable — before
implementation begins. The data in question is the autopilot state record, the
path values it carries, the workflow corpus the change must not regress, and the
counts the specification asserts. This is a unit test suite for the English, not
for the code.

**Created**: 2026-08-12

**Feature**: [spec.md](../spec.md)

**Depth**: Formal gate. Matching the sibling error-handling domain, because the
subject is a safety check that shipped inert and every numeric claim here is a
denominator someone will later re-measure.

**Audience**: Reviewer, at pull-request time.

**Scope note**: Items evaluate the requirements in `spec.md`, `plan.md`, and
`research.md`. Decisions listed as settled in the domain brief are not reopened;
where an item touches one, it is recorded as closed by prior decision with the
citation. Where an item states a measured fact, the measurement was taken against
the working tree during this checklist run.

## State Record Integrity — Requirement Completeness

- [x] CHK001 Is the post-change outcome for each tracked state slot stated as a
  measured fact, given that one of the two does not exit zero today for a reason
  unrelated to this change? [Resolved, Measurability, Spec §Edge Cases,
  §Assumptions]
  - Resolution: the edge case claimed "Both must remain valid after this change",
    which is false as written. Measured during this checklist run:
    `.specify/autopilot-state.json` exits with the input-error code today,
    before any change, reporting that the state must contain a `plan` array. It
    is not valid now and this change cannot make it so. The bullet now states the
    narrower true claim, that the change must add no new failure to either slot,
    and records per slot why that holds: the older slot's comparison verdict is
    never observable because the input error lands before a report prints, and
    the current-run slot's `workflow_file` names the supplied workflow, so the
    comparison newly runs and matches.
- [x] CHK002 Is it stated which of the two slots the autopilot's documented
  invocation actually names, so the back-compatibility claim attaches to the
  right file? [Clarity, Spec §Assumptions]
- [x] CHK003 Are the two slots distinguished by both who writes them and which
  one an invocation reads, so the decision to record rather than converge them
  rests on evidence? [Assumption, Spec §Assumptions]
- [x] CHK004 Is the absent-field skip required to carry verification evidence,
  given it is the branch that keeps a tracked state file working and neither
  control in the FR-012 pair exercises it? [Resolved, Coverage, Spec §FR-003,
  §FR-012, Plan §D5]
  - Resolution: branch 1 was the only branch with no required evidence. Both
    FR-012 controls set `workflow_file` and differ only in its value, and
    `RuleScopingTests` sets it too while reaching branch 2. Plan §D5 now requires
    a third method, placed deliberately outside the FR-012 pair so that pair
    keeps its single-variable framing, asserting that a state with no
    `workflow_file` key exits zero with an empty `workflow_authority_errors`.
    The corpus evidence cannot cover this branch, because every synthesized
    corpus state sets the field.
- [x] CHK005 Is the evidence harness's state shape required to carry the fields
  the guard needs before it can report, so a recorded pass cannot be an input
  error in disguise? [Coverage, Spec §PR Review Packet Requirements]
- [x] CHK006 Is the state file's location required to sit inside the repository,
  given the repository root is derived from the state path and a state outside the
  tree makes every comparison skip? [Measurability, Spec §PR Review Packet
  Requirements, Plan §D8]

## Path Normalization — Requirement Clarity

- [x] CHK007 Are the rules that decide whether the state's `workflow_file` is
  "normalized" written down — specifically how a backslash, an absolute path, and
  a `..` segment are rejected — rather than delegated to a helper name the reader
  must open the source to understand? [Resolved, Clarity, Spec §FR-004a, §FR-005,
  Plan §D1]
  - Resolution: the artifacts fixed the *verdict* for a malformed value but never
    stated what makes a value normalized, so branch 4's scope was readable only
    from the source. Plan §D1 gains a sixth load-bearing detail enumerating the
    accept rule and naming each rejected shape, measured against the working
    tree: backslash anywhere, leading `/`, a `^[A-Za-z]:` Windows drive prefix,
    any `""`, `"."`, or `".."` part, and anything that does not round-trip
    through `PurePosixPath` (which is what rejects `docs//x` and a trailing
    separator). It also records that case is not folded, tying branch 4 to
    FR-004b instead of leaving the two rules to be reconciled by the reader.
- [x] CHK008 Is the whitespace-only value required to carry its own explicit
  check, with the measured evidence that makes delegation to the existing helper
  unsafe? [Completeness, Spec §FR-005]
- [x] CHK009 Is it stated that normalization is the only validity rule applied to
  the state side, since that side is never resolved against the filesystem?
  [Clarity, Spec §FR-004a]
- [x] CHK010 Is the normalization rule consistent with the byte-exact comparison,
  so that a value differing only in letter case is not silently normalized into a
  match? [Consistency, Spec §FR-004b, §Edge Cases]

## Corpus Baseline — Measurability

- [x] CHK011 Is the baseline commit that pins the 54-file denominator identified
  in the specification or the plan, rather than only in the workflow file, so the
  denominator is reproducible from the authored artifacts alone? [Resolved,
  Measurability, Spec §SC-002, §PR Review Packet Requirements, Plan §D8]
  - Resolution: SC-002 and §D8 both pinned the denominator "to the baseline
    commit" without naming it, and the PR packet requirement asked the PR body to
    record a commit the artifacts never stated. Only the workflow file carried
    `3af4764e`. §D8 now names the commit and the literal command, verified during
    this run to return 54.
- [x] CHK012 Is the command that produces the 54-file list stated to the
  precision a reader needs to reproduce it, naming the tool, the directory, and
  the filename pattern? [Measurability, Spec §SC-002, §PR Review Packet
  Requirements]
- [x] CHK013 Is the denominator protected from drift as new specifications land,
  by a stated mechanism rather than by the number happening to be right today?
  [Coverage, Spec §SC-002, Plan §D8]
- [x] CHK014 Is the working-tree file count distinguished from the pinned
  denominator in a form that stays true if another specification's workflow lands
  before this one merges? [Resolved, Consistency, Spec §SC-002]
  - Resolution: SC-002 asserted "The tracked corpus now holds 55 such files; the
    additional one is this specification's own in-flight workflow" — a
    present-tense snapshot with a definite singular, falsified by any further
    workflow landing before merge. Measured now: 54 at the baseline, 55 tracked,
    the difference being this specification's workflow. The sentence is now
    tensed to when it was written and carries the drift-proof rule instead, that
    anything absent from the baseline tree is excluded by construction. The
    denominator itself was already safe; only the surrounding claim could go
    stale.
- [x] CHK015 Is a compensating control named that separates 54 genuine passes
  from 54 silent skips, so the corpus number cannot be mistaken for proof the
  comparison ran? [Coverage, Spec §PR Review Packet Requirements, Plan §D8]

## Classification Record — Requirement Consistency

- [x] CHK016 Do the emitted-key counts agree everywhere they appear — the
  acceptance scenario, the success criterion, the plan's arithmetic, and the
  plan's verdict table? [Consistency, Spec §US2 AS3, §SC-006, Plan §D3, §D4]
- [x] CHK017 Is the classification record's verdict vocabulary stated
  consistently, given one requirement fixes a closed three-value vocabulary while
  the acceptance scenario and the entity definition each offer two? [Resolved,
  Conflict, Spec §FR-010, §FR-010b, §US2 AS1, §Key Entities]
  - Resolution: a real contradiction, not a wording preference. US2 AS1 required
    every key to carry "a verdict of gated or deliberately advisory", and the Key
    Entities definition repeated the same two values, while FR-010 fixes three
    and FR-010b *mandates* that three named keys be `advisory-accidental`. AS1
    was therefore falsified by FR-010b for exactly those keys, so the acceptance
    scenario could not be satisfied as written. Both now defer to FR-010's closed
    vocabulary, AS1 naming the three tokens explicitly.
- [x] CHK018 Is the pre-change key count in the entity definition marked as
  pre-change, so it does not read as the post-change count the success criterion
  fixes? [Resolved, Consistency, Spec §Key Entities, §SC-006]
  - Resolution: Key Entities stated "Twenty exist. Eight are reachable by a named
    rule" in the present tense, inside a specification whose SC-006 moves those
    counts to 21 and 9. A reader meeting the entity definition first would take
    the pre-change split for the delivered one. The bullet now marks the counts
    as pre-change and points at SC-006 for the post-change split. Measured
    against the working tree: 20 emitted keys, 8 reachable, matching the
    pre-change claim.
- [x] CHK019 Is the record required to cover every key the guard can emit, with
  the covered set derived from a real report rather than a parallel list?
  [Completeness, Spec §FR-010, §FR-011]
- [x] CHK020 Is reason quality specified well enough to be judged, rather than
  left as an instruction to write something? [Measurability, Spec §FR-010a]

## Count Drift & Reader Integrity

- [x] CHK021 Is a protocol stated for what happens when a re-measurement
  disagrees with a recorded count? [Assumption, Spec §Assumptions]
- [x] CHK022 Are the guard's other readers of the state's `workflow_file`
  accounted for, so the new reader is known not to change what they receive?
  [Dependency, Plan §D2, Research §R1]
- [x] CHK023 Is the report's schema surface accounted for, so that adding a
  problem key is known not to break an existing consumer contract? [Dependency,
  Plan §Skipped design artifacts]
- [x] CHK024 Does every count the specification asserts have a stated way to be
  re-derived, so no requirement depends on a number only the author can confirm?
  [Measurability, Spec §Assumptions, §SC-006, Research §Measurements]

## Closed By Prior Decision

Recorded so a reader does not reopen them. No artifact edit is warranted for any
item in this section.

- The resolution asymmetry, resolving the supplied side against the repository
  root while taking the state side as the literal string it holds: Spec §FR-004a.
- Byte-exact comparison with no case folding and no filesystem identity test:
  Spec §FR-004b.
- The dedicated `workflow_authority_errors` key, and arming that key only:
  Spec §FR-007, §FR-008, design concept Q2 and Q6.
- Message assignments across the identity, out-of-boundary, and malformed
  branches: Spec §FR-004c, §FR-005, §FR-009.
- The corpus proof staying a one-time recorded run rather than a committed test:
  design concept Q10, Spec §Assumptions, Plan §D8.
- Recording rather than converging the two tracked state slots: Spec
  §Assumptions, design concept Open Questions.

## Notes

- Items carrying a gap marker are findings to remediate in `spec.md` or
  `plan.md`.
- Items without a gap marker were evaluated and found satisfied; the bracketed
  reference names where the requirement already lives.
