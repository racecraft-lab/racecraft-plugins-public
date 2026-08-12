# Feature Specification: Phase-Guard Enforcement Repair

**Feature Branch**: `art-014-phase-guard-enforcement-repair`

**Created**: 2026-08-12

**Status**: Draft

**Input**: User description: "Phase-Guard Enforcement Repair. The autopilot phase guard documents `autopilot-state.json.workflow_file` as authoritative and quotes the failure message a mismatch produces, but that message cannot be produced by the invocation the autopilot actually issues, and even when produced it cannot move the exit code. Repair both defects, arm exactly one new problem key, and record per-key advisory intent in a form a test enforces."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A mismatched workflow halts the run (Priority: P1)

A maintainer resumes autopilot in the wrong worktree, or against a state slot
left over from an earlier specification. The state file names one workflow; the
maintainer supplies another. Today the run proceeds against the wrong
specification and reports pass. After this change the run stops, and the message
names both files so the maintainer can tell which one to repair.

**Why this priority**: This is the defect the specification exists to fix. It is
the only story that changes runtime behavior, and the other two describe records
about that behavior. Shipped alone it delivers the whole safety benefit.

**Independent Test**: Point the guard at a workflow file while the state names a
different one, using the exact invocation the autopilot issues
(`--rule status-evidence`, no commit flags, no marker-plan schema). The run must
exit non-zero and print a message containing both paths. Re-point the state at
the matching workflow and the same invocation must exit zero.

**Acceptance Scenarios**:

1. **Given** a state file whose `workflow_file` names a different specification's
   workflow, **When** the guard runs with `--rule status-evidence` and no commit
   flags, **Then** it exits non-zero and reports the mismatch under
   `workflow_authority_errors`.
2. **Given** a state file whose `workflow_file` names the supplied workflow,
   **When** the guard runs with `--rule status-evidence`, **Then** it exits zero
   and reports no authority error.
3. **Given** a state file with no `workflow_file` field at all, **When** the
   guard runs, **Then** it exits zero on that account, because a state that names
   no workflow asserts no authority.
4. **Given** a state file whose `workflow_file` holds a malformed value, **When**
   the guard runs, **Then** it exits non-zero, so a garbage value cannot silently
   disable the check.
5. **Given** a state file that sits outside any repository, **When** the guard
   runs, **Then** the comparison is skipped and no authority error is
   manufactured.
6. **Given** the mismatch is detected, **When** the message is read, **Then** it
   opens with the sentence the shipped documentation already quotes and appends
   both compared paths after it.

---

### User Story 2 - Advisory status is a recorded decision, not an accident (Priority: P2)

A maintainer reading the guard wants to know, for any problem key, whether that
key can fail a run or is deliberately advisory, and why. Today nothing separates
keys that are advisory on purpose from keys that drifted into being inert. That
absence is how the defect in User Story 1 survived.

**Why this priority**: It does not fix a live failure, so it ranks below User
Story 1. It ranks above User Story 3 because it is the durable control that stops
the same class of defect recurring, and it is enforced by a test rather than by
prose.

**Independent Test**: Read the classification record and confirm every problem key
the guard can emit carries a verdict and a reason. Then add a throwaway key to the
report without adding it to the record and confirm the test fails.

**Acceptance Scenarios**:

1. **Given** the guard's report, **When** the classification record is compared
   against it, **Then** every emitted problem key appears in the record with a
   verdict drawn from the closed three-value vocabulary FR-010 fixes (`gated`,
   `advisory-deliberate`, or `advisory-accidental`) and a one-line reason.
2. **Given** a new problem key added to the report but not to the record,
   **When** the test suite runs, **Then** it fails and names the missing key.
3. **Given** the classification record, **When** the counts are read, **Then**
   they agree with the post-change split of 21 emitted keys, of which 9 are
   reachable by a named rule and 12 are advisory, measured against the pre-change
   split of 20 keys, 8 reachable and 12 advisory.

---

### User Story 3 - Every documented claim about this guard is true on the platform it appears on (Priority: P3)

A maintainer on either platform reads the shipped documentation for this guard.
Whatever it says about enforcement either happens, or the document says plainly
that it does not happen yet and names what will make it happen.

**Why this priority**: Lowest because no run behaves differently as a result. It
is still in scope because a document promising enforcement that does not occur is
the same failure this specification exists to correct, one layer up.

**Independent Test**: Read each shipped statement about this guard on both
platforms and confirm each one either describes behavior the guard performs or
labels itself as not yet wired.

**Acceptance Scenarios**:

1. **Given** the Claude autopilot skill document, **When** the workflow authority
   failure is described, **Then** it quotes the message prefix rather than
   claiming an exact full string.
2. **Given** the Claude autopilot skill document, **When** the expected-commit
   flags are described, **Then** it states the same append contract the Codex
   document carries and states plainly that the Claude flow does not yet fetch
   those values, naming the follow-up that will wire it.
3. **Given** either platform's workflow-file protocol reference, **When** state
   authority is described, **Then** the `workflow_file` authority claim appears
   beside the related precedence rules on both platforms.

---

### Edge Cases

- **State names a workflow that does not exist on disk.** The named path and the
  supplied path still differ, so the comparison reports a mismatch. Absence of the
  named file is not a separate error class in this change.
- **State and supplied path point at the same file through different spellings**,
  such as a relative path against an absolute one, or a path traversing a symlink.
  The comparison must treat these as matching, because a maintainer supplying the
  correct workflow by a different spelling has not made a mistake.
- **The guard runs inside a git worktree**, where the repository marker is a file
  rather than a directory. Root resolution must succeed there, because every
  autopilot run for this repository happens in a worktree.
- **`workflow_file` holds a non-string value**, such as a number, a list, or null.
  This is the malformed case and fails.
- **`workflow_file` holds an empty or whitespace-only string.** Treated as
  malformed rather than absent, so an emptied field cannot become a silent opt-out.
- **Two tracked state slots disagree about whether the field exists at all.**
  `.specify/autopilot-state.json` carries no `workflow_file`;
  `docs/ai/specs/.process/autopilot-state.json` names a workflow. This change MUST
  add no new failure to either, which is a narrower and truer claim than both
  remaining valid. Measured before the change: the older slot already exits with
  the input-error code on any invocation, because it carries no `plan` array and
  that rejection lands before any report is printed. Its comparison verdict is
  therefore never observable, and FR-003's absent-field skip adds nothing to that
  outcome either way. The current-run slot exits zero, and its `workflow_file`
  names the supplied workflow, so the comparison newly runs against it and
  matches.
- **A workflow file in the corpus is mid-repair and legitimately failing.** The
  regression proof must not be wired into the committed suite, or unrelated pull
  requests turn red.
- **The supplied path or the state value differs only in letter case.** Treated as
  a mismatch on every platform. A mis-cased state value fails the comparison
  identically everywhere. A mis-cased supplied path fails as a mismatch on a
  case-insensitive filesystem and as an unreadable file on a case-sensitive one.
  Both are non-zero exits, so the halt is platform-independent even though the
  error class is not.
- **The supplied workflow file does not exist on disk.** The guard already exits
  with the input-error code before any identity comparison, because reading the
  supplied workflow is the first statement of the function that hosts the
  comparison. No authority error is produced and this change adds no path for one.
  This is the supplied side; the first bullet above covers the file the state
  names.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The workflow-identity comparison MUST run unconditionally, in its
  own block, placed before the marker-plan and expected-commit gate, so it
  executes on the invocation the autopilot actually issues.
- **FR-002**: The existing gated pull-request-head byte comparison MUST keep its
  current preconditions and semantics unchanged, because the Codex flow genuinely
  supplies those commit values from live pull-request metadata.
- **FR-003**: When the state carries no `workflow_file`, the guard MUST skip the
  comparison and report no authority error.
- **FR-004**: When the state carries a `workflow_file` naming a different workflow
  than the supplied one, the guard MUST report an authority error.
- **FR-004a**: The comparison MUST derive the supplied workflow's
  repository-relative reference by resolving it against the repository root, so a
  correct workflow supplied under a different spelling, including one traversing a
  symlink, still matches. The `workflow_file` value the state carries MUST be
  compared as the literal string it holds, without filesystem resolution, because
  it is machine-written and already constrained to a normalized
  repository-relative form. The asymmetry is deliberate: only the supplied side
  has spelling freedom.
- **FR-004c**: When the supplied workflow resolves to a location outside a
  successfully resolved repository root, the guard MUST report an authority error
  rather than skip. This is a different fact from FR-006: there the repository
  could not be found at all, whereas here it was found and the supplied path does
  not live under it. A completed evaluation with an out-of-boundary result is the
  case the check exists to catch, not an absence of information. The error MUST
  reuse the sentence the same file already emits for this condition, "workflow
  file is outside the authorized repository", rather than the FR-009 prefix, which
  governs the identity-mismatch message only. It MUST be reported under
  `workflow_authority_errors` so it can move the exit code.
- **FR-004d**: The branches MUST be evaluated in this order, because an earlier
  skip must win over a later failure: absent `workflow_file` skips (FR-003), then
  an unresolvable repository root skips (FR-006), then a malformed value fails
  (FR-005), then an out-of-boundary resolution fails (FR-004c), then a mismatch
  fails (FR-004).
- **FR-004b**: The comparison MUST be a byte-exact comparison of the two POSIX
  references, with no case folding and no filesystem identity test such as
  `samefile`. Byte-exact is the only rule that returns the same verdict on a
  case-insensitive filesystem and a case-sensitive one, which this repository
  requires because it runs on macOS locally and Linux in continuous integration.
- **FR-005**: When the state carries a malformed `workflow_file`, including a
  non-string value or an empty or whitespace-only string, the guard MUST report an
  authority error. The whitespace-only case MUST be rejected by an explicit check
  rather than delegated to the existing normalized-path helper, because that
  helper accepts a whitespace-only string as a valid path part. Verified:
  `_is_normalized_repo_path("  ")` and `_is_normalized_repo_path(" ")` both return
  `True`, so without an explicit check such a value falls through to the mismatch
  branch and is reported with the identity message instead of the malformed one.
- **FR-006**: When the repository root cannot be resolved, the guard MUST skip the
  comparison rather than report an error, matching the precedent the same file
  already sets for an extracted copy. Both skip branches, this one and FR-003,
  leave the run indistinguishable from one that ran the comparison and passed it,
  because a skip and a satisfied comparison both report no authority error and
  both exit zero. That equivalence is accepted rather than overlooked: the exit
  code carries the verdict, not whether the verdict was computed. The
  compensating evidence is the FR-012 negative control and the deliberately
  mismatched corpus canary, each of which fails if the comparison silently
  stopped running.
- **FR-007**: The guard MUST report identity failures under a new
  `workflow_authority_errors` problem key, and that key MUST be the only key added
  to the `status-evidence` rule tuple.
- **FR-008**: `workflow_checkpoint_errors` MUST NOT be added to the
  `status-evidence` rule tuple, because it is produced at four other sites by the
  checkpoint-binding validation and widening it would arm every PR Marker Plan
  Evidence binding check at once.
- **FR-009**: The identity failure message reported under
  `workflow_authority_errors` MUST open with the sentence the shipped
  documentation already quotes, unmodified (`supplied workflow does not match
  autopilot state workflow_file authority`), and MUST append both compared paths
  after it. This governs the new key only. The identity message the gated
  pull-request-head path already emits under `workflow_checkpoint_errors` keeps
  the bare sentence, because FR-002 freezes that path and a committed test
  asserts that exact list element. After this change the guard therefore carries
  two identity messages whose text differs, which follows from FR-002 rather than
  being an oversight.
- **FR-010**: The guard MUST carry a classification record naming every problem key
  it can emit, using a closed three-value vocabulary: `gated`,
  `advisory-deliberate`, or `advisory-accidental`. Two values are insufficient,
  because the audit found a key that is advisory by accident rather than by
  design (see FR-010b).
- **FR-010a**: Each classification entry MUST carry a reason that states why the
  verdict holds. Restating the key name is not a reason. An
  `advisory-deliberate` entry MUST say what makes advisory status correct for
  that key; an `advisory-accidental` entry MUST name the follow-up roadmap entry
  that will arm it.
- **FR-010b**: The classification record MUST mark `in_progress_errors`,
  `duplicate_state_steps`, and `state_order_errors` as `advisory-accidental`. The
  shipped justification for advisory status is that the existing workflow corpus
  predates the checks, which is true of the coverage lists but false of these
  three: they are invariants of the state file the current run just wrote, so no
  legacy artifact can violate them. This specification records the verdict and
  does not arm them.
- **FR-011**: The test suite MUST fail when the guard's report emits a problem key
  absent from that classification record. The test MUST derive the emitted key set
  from a real report rather than from a second hardcoded list, because a parallel
  list can drift out of step exactly as the classification record itself could.
- **FR-012**: The test suite MUST include a negative control proving that a state
  naming a different specification exits non-zero under the autopilot's own
  invocation, and a matching positive control proving a correct state exits zero.
  The two MUST be separate test methods sharing one fixture builder whose only
  difference is the state's `workflow_file` value, so each failure names its own
  claim and the pair is a controlled comparison. The fixture MUST create a
  repository-root marker in its temporary root, written as a file rather than a
  directory, because without a resolvable root the comparison skips under FR-006
  and both controls pass vacuously; writing the marker as a file also exercises
  the worktree case. The state's `workflow_file` MUST be repository-relative
  against that root. The negative control MUST assert a non-zero exit, a non-empty
  `workflow_authority_errors`, and the FR-009 message prefix. The positive control
  MUST assert a zero exit and an empty `workflow_authority_errors`. Any new test
  case class MUST be registered with the suite builder, which enumerates its
  classes explicitly.
- **FR-013**: The shipped documentation MUST describe this guard truthfully on
  both platforms, which means quoting the message as a prefix, stating the
  expected-commit append contract together with its not-yet-wired status on the
  Claude side, and stating the `workflow_file` authority in the workflow-file
  protocol reference on both platforms.
- **FR-013a**: The Claude skill document's authority bullet MUST be corrected in
  three specific respects, each of which becomes false when this change lands.
  It currently calls the field "the authority" without qualification, but the
  comparison skips on an absent field and on an unresolvable repository root. It
  claims the run "fails with" an exact full string, but FR-009 makes that string
  a prefix with both paths appended. Its lead-in claims repairing the workflow
  file to match is the correct move, which is true of the marker-evidence bullet
  beside it but false of the identity bullet, whose repair re-points the run or
  reclaims the state slot, rewriting the state from the invocation instead.
- **FR-013b**: The division of labour between the skill document and the protocol
  reference MUST be: the skill document keeps the quotable sentence and names
  both skip conditions, because an operator whose run halts greps the skill body
  for the sentence they just saw; the protocol reference owns the branch order
  and the reason behind each verdict. The skill document MUST NOT become a second
  copy of the requirement truth table, and MUST NOT be reduced to a bare pointer
  that removes the quotable sentence.
- **FR-013c**: The references index entry naming the workflow-file protocol MUST
  be updated on both platforms, so the new content is reachable from the index
  rather than only by full-text search.

### Reviewability Notes *(if applicable)*

No typed reviewability exception is claimed. This change stays inside the normal
budget, so it needs no operator override. Four of the nine touched files are
generated artifacts regenerated by the repository's own refresh tooling, never
hand-edited, and excluded from the reviewable count.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: docs/process
- **Projected reviewable LOC**: 235
- **Projected production files**: 4
- **Projected total files**: 9
- **Budget result**: within budget
- **Split decision**: Remains one specification. The slice estimator returned
  `estimated_loc 235`, `suggested_slices 1`, `status ok` against signals of 3 user
  stories, 5 authored files, 13 functional requirements, modify-weighted. That sits
  under the 400 reviewable-LOC ceiling, and production files at 4 sit under the
  warn threshold of 6. The work cuts end-to-end through guard logic, error
  reporting, rule registration, tests, and documentation rather than by layer, so a
  split would produce fragments that cannot be verified on their own. This revises
  the roadmap's earlier declaration of roughly 120 reviewable LOC across 2
  production files, which predates the documentation files added during scoping.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.
- The PR description MUST record the corpus regression evidence as a before and
  after pair, because that proof is a one-time recorded run rather than a
  committed test.
- The recorded corpus evidence MUST be reproducible from the workflow file alone.
  That requires recording the baseline commit and the command that produces the
  54-file list; the exact synthesized state shape, including a `plan` array and a
  repository-relative `workflow_file`; the fact that the state file is written to
  a path **inside** the repository, because the repository root is derived from
  the state path and a state outside the tree makes every comparison skip; the
  exact guard invocation; the before and after counts; and one deliberately
  mismatched canary run inside the same harness that exits non-zero with a
  non-empty `workflow_authority_errors`. The canary is what distinguishes 54
  genuine passes from 54 silent skips. The before count stands as measured,
  because before the change the comparison did not run at all and the state's
  location could not have affected it.

### Key Entities *(include if feature involves data)*

- **Autopilot state record**: The persisted record of an autopilot run. Carries an
  optional `workflow_file` naming the workflow it considers authoritative. Two
  tracked instances exist in this repository and they disagree about whether the
  field is present.
- **Workflow file**: The per-specification record the autopilot executes against.
  The supplied one is compared against the one the state names.
- **Problem key**: A named bucket of findings the guard emits. Twenty exist before
  this change. Eight are reachable by a named rule and can move the exit code;
  twelve are advisory. SC-006 fixes the post-change split.
- **Rule**: A named selection of problem keys that scopes the exit code. The
  autopilot always selects `status-evidence`.
- **Problem-key classification record**: The new per-key verdict, drawn from the
  closed three-value vocabulary FR-010 fixes, with a reason, enforced by a test
  rather than by prose.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A run whose state names a different specification stops instead of
  proceeding. Measured as a non-zero exit under the autopilot's own invocation,
  where the same scenario exits zero today.
- **SC-002**: All 54 workflow files that `git ls-tree` lists under the process
  directory as `*-workflow.md` at the baseline commit still exit zero under the
  autopilot's own invocation when the state names the matching workflow. The
  before and after counts are both 54 of 54. The denominator is pinned to the
  baseline commit so it cannot drift as new specifications land. The tracked
  corpus held 55 such files when this criterion was written, the one addition
  being this specification's own in-flight workflow, which is named as excluded.
  Any file absent from the baseline tree is excluded by construction, so a
  further specification landing before this one merges moves the working-tree
  count without moving the denominator or falsifying this criterion.
- **SC-003**: A maintainer who hits the failure can identify both disagreeing
  files from the message alone, without opening either file.
- **SC-004**: Every problem key the guard emits carries a recorded verdict, so the
  count of keys with an unexplained advisory status falls to zero from twelve.
- **SC-005**: Adding a problem key without recording a verdict fails the test
  suite, so the record cannot drift out of step with the code.
- **SC-006**: Exactly one new problem key is armed. The count of emitted keys moves
  from 20 to 21 and the count reachable by a named rule moves from 8 to 9, while
  the 12 advisory keys stay advisory and no existing key's reachability changes.
- **SC-007**: Every shipped statement about this guard on either platform either
  describes behavior that occurs or names itself as not yet wired. The count of
  statements promising unperformed enforcement falls to zero.
- **SC-008**: The full repository suite passes with zero failures after the change,
  including the regenerated artifacts that editing the guard restales.

## Assumptions

- The measured facts recorded during scoping hold: the guard emits 20 problem
  keys, 8 reachable by a named rule and 12 advisory; the process corpus is 54
  workflow files at the baseline commit; and all 54 exit zero under the
  autopilot's own invocation when the state names the matching workflow. A
  re-measurement that disagrees is drift to report, not a number to quietly
  change.
- There is exactly one authored copy of the guard. The other tracked copies are
  generated and byte-identical, and are refreshed by the repository's existing
  artifact tooling rather than hand-edited.
- The Codex distribution ships the same skills path, so both platforms inherit
  the repair and both inherit the new failure. No separate Codex-side guard
  change is needed.
- Path comparison can rely on resolving both paths against the repository root.
  Runs happen inside a git worktree where the repository marker is a file, and
  root resolution is assumed to succeed there.
- The `--rule` scoping mechanism is deliberate and stays as it is. This change
  registers a key within that mechanism rather than altering it.
- Making `workflow_file` a mandatory state field is a migration rather than a
  repair, so absence stays permitted. The tracked state file that lacks the field
  must keep validating.
- The corpus regression proof is a one-time recorded run, not a committed test,
  because the process directory holds live data and an in-flight specification
  mid-repair can legitimately fail the guard.
- Wiring the Claude flow to fetch live pull-request commit values is a separate
  specification. This change documents the gap rather than closing it. Resolved
  during Clarify: the follow-up is **ART-016, Claude-Side Live PR Commit
  Authority**, created in the technical roadmap by this change so the note added
  to the shipped documentation cites an entry that exists. A shipped document
  naming an identifier that does not exist would repeat the defect class this
  specification repairs.
- The two tracked autopilot state slots both remain. Resolved during Clarify by
  evidence rather than judgment: they are written by different callers, so
  converging them is not this change's business and no follow-up entry is needed.
  `docs/ai/specs/.process/autopilot-state.json` is the current autopilot run
  slot, which every documented invocation names as
  `<workflow-dir>/autopilot-state.json`. `.specify/autopilot-state.json` is the
  older slot, still tracked and still rewritten by post-merge archive hygiene:
  four archive reports list it among the files they update, and the CAR-003
  workflow recorded its marker plan there. This change records the finding only.
  It also confirms FR-003 rather than complicating it, because the older slot
  legitimately carries no `workflow_file`, which is exactly why skipping on
  absence is required rather than merely convenient.
