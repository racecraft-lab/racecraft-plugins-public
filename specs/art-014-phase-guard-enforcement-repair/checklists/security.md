# Security Checklist: Phase-Guard Enforcement Repair

**Purpose**: Validate that the requirements governing this guard's *security*
posture are complete, unambiguous, internally consistent, and objectively
verifiable — before implementation begins. The subject is a check that can be
silently disabled: a skipped comparison and a satisfied one produce the same
exit code, so every input that can reach a skip is security-relevant. This is a
unit test suite for the English, not for the code.

**Created**: 2026-08-12

**Feature**: [spec.md](../spec.md)

**Depth**: Formal gate. Matching the sibling error-handling and data-integrity
domains. The subject is a safety check that shipped inert for several releases,
so the bar is that every way the check can be turned off is written down and
either closed or accepted with a reason.

**Audience**: Reviewer, at pull-request time.

**Scope note**: Items evaluate the requirements in `spec.md`, `plan.md`, and
`research.md`. Decisions listed as settled in the domain brief are not reopened;
where an item touches one, it is recorded as closed by prior decision with the
citation. Where an item states a measured fact, the measurement was taken
against the working tree during this checklist run.

## Threat Model & Trust Boundary — Requirement Completeness

- [x] CHK001 Is the failure the guard exists to catch characterized concretely
  enough that a reader can tell operator error from adversarial input?
  [Clarity, Spec §US1]
- [x] CHK002 Is the trust boundary stated — which of the guard's inputs are
  caller-controlled and which, if any, are treated as untrusted — so that the
  accepted verdicts on the two skip branches rest on a stated model rather than
  on the reader's judgment? [Resolved, Security, Completeness, Spec §FR-006,
  §FR-006a]
  - Resolution: the artifacts accepted the skip and named compensating evidence,
    but never said who the guard defends against, so "accepted" rested on the
    reader's judgment rather than on a model. New Spec §FR-006a states the
    boundary: every input that can induce a skip is chosen by the invoking
    caller, who also selects `--rule` and decides whether to run the guard at
    all, so reaching a skip grants no capability that caller lacked. The threat
    is the User Story 1 mistake, the residual exposure is operator error rather
    than an adversary, and the honest consequence is stated plainly, that a
    caller who invokes the guard incorrectly gets a silent pass.
- [x] CHK003 Is the equivalence between a skipped comparison and a satisfied one
  recorded as accepted rather than overlooked, at the place the skip branches are
  defined? [Completeness, Spec §FR-006]
- [x] CHK004 Are compensating controls named for that equivalence, so a clean
  result cannot be mistaken for proof the comparison ran? [Coverage,
  Spec §FR-006, §FR-012, Plan §D8]

## Silent-Disable Resistance — Requirement Completeness

- [x] CHK005 Does every shape the state's `workflow_file` value can take carry a
  stated verdict, so no value is left to the implementer's discretion?
  [Completeness, Spec §FR-003, §FR-004, §FR-005, Plan §D1]
- [x] CHK006 Is the whitespace-only value required to be rejected by an explicit
  check, with the measured evidence that the existing normalized-path helper
  accepts it? [Measurability, Spec §FR-005]
  - Independently re-measured during this run: the helper's accept rule returns
    true for both a single space and a run of spaces, confirming FR-005's stated
    measurement. Without the explicit check such a value reaches the mismatch
    branch and is reported with the wrong error class.
- [x] CHK007 Is an explicitly null value separated from an absent one, with the
  distinguishing test named, so an emptied field cannot become a silent opt-out?
  [Clarity, Spec §FR-003 + Edge Cases, Plan §D1, Research §R2]
- [x] CHK008 Are the rules that make a value "normalized" written down, so the
  malformed branch's scope is readable without opening the source? [Clarity,
  Plan §D1]

## Path Boundary Enforcement — Requirement Clarity

- [x] CHK009 Is a supplied workflow resolving outside the repository root
  assigned a failure rather than a skip, with the reason it is a different fact
  from an unresolvable root? [Clarity, Spec §FR-004c vs §FR-006]
- [x] CHK010 Is the out-of-boundary failure required to be reported under a key
  that can move the exit code, rather than under an advisory key? [Completeness,
  Spec §FR-004c]
- [x] CHK011 Is the precondition the out-of-boundary failure depends on drawn
  out — that it is reachable only when a repository root resolved, so a supplied
  workflow outside the repository escapes it entirely whenever the state path
  resolves no root either? [Resolved, Security, Coverage, Spec §FR-004c,
  §FR-004d, §FR-006a]
  - Resolution: FR-004c's own wording, "outside a **successfully resolved**
    repository root", already encodes the precondition, and FR-004d already
    orders the skip ahead of the failure. What no artifact drew out was the
    consequence: when the state path resolves no root, the run reaches FR-006's
    skip and produces no error at all, so the out-of-boundary failure is
    unreachable in that combination. Spec §FR-006a now records it, deliberately
    as an added record rather than an edit to FR-004c or FR-004d, because the
    branch order is settled and this changes neither verdict.

## Skip-Branch Inducibility — Requirement Coverage

- [x] CHK012 Is it stated which of the two supplied inputs the repository root is
  derived from, given that the choice decides whether the comparison runs at all?
  [Clarity, Plan §D1, §D8]
- [x] CHK013 Is the absent-field skip stated to depend only on the state's
  content, so it cannot be induced by a party who controls only the supplied
  workflow path? [Coverage, Spec §FR-003]
- [x] CHK014 Is it stated that the repository-root walk operates on the state
  path as supplied rather than on a resolved form, so that a relative state
  argument issued from a working directory other than the repository root
  resolves no root and skips while the state file itself sits untouched inside
  the repository? [Resolved, Security, Completeness, Spec §FR-006, §FR-006a,
  Plan §D8]
  - Resolution: the artifacts treated the skip as a fact about *where the state
    file lives*, which is only one of the ways to reach it. Measured during this
    run: the walk reads the state path as supplied, so a relative state argument
    has a parents chain terminating at the working directory, and from any
    working directory other than the repository root it resolves no root even
    though the state file is a tracked file inside the tree. Nothing moves; only
    the spelling of the argument changes. Spec §FR-006a now enumerates all three
    inducing inputs, and records that the documented invocation is safe because
    it runs from the repository or worktree root, which is a condition of that
    invocation rather than a property of the guard.
- [x] CHK015 Is the corpus-evidence condition sufficient as written, given that
  requiring the state to be written to a path inside the repository does not by
  itself guarantee a root resolves from the path as passed to the guard?
  [Resolved, Security, Measurability, Spec §PR Review Packet Requirements,
  Plan §D8]
  - Resolution: it was necessary but not sufficient, and the insufficiency is
    silent in exactly the direction the evidence is meant to rule out. A harness
    that writes the state inside the repository and then names it relatively from
    a subdirectory resolves no root, and reports the same 54 vacuous passes the
    condition exists to prevent. Both the PR packet requirement and Plan §D8 now
    carry the second condition: pass the state path absolute, or relative with
    the working directory at the repository root, and record which was used. The
    canary still catches this if it is got wrong, which is why the finding is a
    completeness gap in the evidence protocol rather than a hole in the proof.
- [x] CHK016 Is the fixture condition that would otherwise make both controls
  pass vacuously stated as a requirement rather than left to the implementer, so
  a harness-induced skip fails loudly? [Coverage, Spec §FR-012, Plan §D5]

## Exit-Code Reachability — Requirement Completeness

- [x] CHK017 Is the new key required to be registered in the rule the autopilot
  actually selects, so a detected mismatch can move the exit code? [Completeness,
  Spec §FR-007]
- [x] CHK018 Is the blast radius of the rejected wider registration stated, so
  arming exactly one key is a reasoned choice rather than an assertion?
  [Consistency, Spec §FR-008, Research §R1]
- [x] CHK019 Is it stated whether a caller selecting a different rule bypasses the
  new key, and if it can be bypassed, that the bypass is accepted and why?
  [Resolved, Security, Coverage, Spec §FR-007, §Assumptions]
  - Resolution: it can be bypassed, and the artifacts said only that the `--rule`
    mechanism was not being changed, which is a different claim. Measured during
    this run against the pre-change guard, using an existing `status-evidence`
    key as the stand-in because the new key does not exist yet: one report exits
    non-zero under `--rule status-evidence` and zero under `--rule coverage`
    while its own printed status reads `fail`. The Assumptions bullet now states
    the bypass, accepts it on the FR-006a basis, and bounds it with the two
    properties that make it tolerable, that the full report prints on every
    invocation and that omitting `--rule` gates on every emitted key.
- [x] CHK020 Is the input-error exit path distinguished from the rule-violation
  exit path, so a control asserting only "non-zero" cannot be satisfied by an
  unrelated input failure? [Clarity, Spec §Edge Cases, §FR-012]

## Untrusted Value Handling — Requirement Coverage

- [x] CHK021 Is the state side stated to undergo no filesystem resolution, so the
  literal comparison cannot itself become a traversal vector? [Coverage,
  Spec §FR-004a]
- [x] CHK022 Are traversal-shaped state values required to be rejected before any
  comparison happens? [Completeness, Spec §FR-005, Plan §D1]
  - Re-measured during this run against the helper's accept rule: a leading
    slash, a `..` part, a backslash anywhere, and a Windows drive prefix are all
    rejected, so no state value can name a location outside the tree.
- [x] CHK023 Is the risk bounded that this change newly echoes an operator-
  supplied value into the guard's output, given FR-009 requires both compared
  paths to be appended to the message? [Coverage, Spec §FR-009]
  - Measured during this run, because the accept rule does **not** screen this:
    a value carrying terminal control sequences is accepted as normalized and
    therefore reaches the mismatch message. The output is safe regardless,
    because the whole report is emitted through a single JSON serialization that
    escapes control characters and non-ASCII to `\uXXXX`. The protection comes
    from the serializer rather than from the validator, which is why the
    requirement needs no change.

## Classification Record Durability — Requirement Measurability

- [x] CHK024 Is the completeness test required to derive the emitted key set from
  a real report rather than from a parallel list, so the record cannot drift out
  of step with the code? [Measurability, Spec §FR-011]
- [x] CHK025 Is the verdict vocabulary closed, so an unclassified key cannot be
  admitted under a novel verdict string? [Completeness, Spec §FR-010, Plan §D5]
- [x] CHK026 Is the record required to cover every key the guard can emit, with
  the test naming any key that is missing? [Completeness, Spec §FR-010, §FR-011,
  Plan §D5]
- [x] CHK027 Is the invariant the single-report derivation depends on stated —
  that every emitted key appears in every report regardless of state content — so
  that a key added by a future specification and emitted only under some state
  shapes cannot pass the completeness test unclassified? [Resolved, Security,
  Coverage, Spec §FR-011, Plan §D5, Research §Measurements]
  - Resolution: research recorded that one report emits all keys, but as a
    measurement rather than as the named property the test depends on, and the
    limit was nowhere. Re-verified two ways during this run: a thin synthesized
    state and the tracked current-run state produce identical report key sets at
    24 keys, 20 problem plus 4 metadata; and every problem-key return in the
    guard is uniform per function, including the early returns, so no key is ever
    conditionally absent. Plan §D5 now names the invariant and its limit, that a
    future key emitted only under some state shapes would pass unclassified, and
    fixes the response as extending the fixture rather than relaxing the
    assertion.

## Closed By Prior Decision

Recorded so a reader does not reopen them. No artifact edit is warranted for any
item in this section.

- The out-of-boundary FAIL verdict: settled by unanimous three-lens consensus
  grounded in CWE-706, CWE-22, CWE-59, OWASP fail-securely, CWE-636, Zip Slip,
  and PEP 706, and carried into Spec §FR-004c. Cited, not re-litigated.
- The full skip-versus-fail truth table and its branch ordering: Spec §FR-003,
  §FR-004, §FR-004c, §FR-004d, §FR-005, §FR-006, Plan §D1.
- The resolution asymmetry, resolving the supplied side against the repository
  root while taking the state side as the literal string it holds:
  Spec §FR-004a.
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
- The documentation homes and wording: Spec §FR-013, §FR-013a, §FR-013b,
  §FR-013c, Plan §D6.

## Notes

- Items carrying a gap marker are findings to remediate in `spec.md` or
  `plan.md`.
- Items without a gap marker were evaluated and found satisfied; the bracketed
  reference names where the requirement already lives.
- Three items record a measurement taken during this run. Each was taken because
  the artifacts asserted a property that only an invoked result could confirm,
  and each agrees with what the artifacts claim.
