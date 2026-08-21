# Feature Specification: Feedback Sweep, slice 1 of 2 — the checkpoint

**Feature Branch**: `art-008-feedback-sweep`

**Created**: 2026-08-20

**Status**: Draft

**Input**: User description: "ART-008 slice 1 of 2, the checkpoint. The plan stage ends at an open draft pull request whose body indexes the planning artifacts, and the gallery's draft-stage pages export a reader's objections as markdown meant to be pasted into a pull-request comment. Nothing reads those comments back, so an implement-stage run starts task work without looking at the pull request and the checkpoint is decoration. Make the implement stage open with a feedback sweep that reads unresolved review threads and pull-request conversation comments, acts only on write-capable authors, recognizes exported markdown blocks by their lead sentence, classifies each comment as amended, answered, deferred, or no action, routes amendments through the existing consensus machinery, records every handled comment in a Feedback Sweep Log in the workflow file, replies once per comment, and then stops for re-review when anything was amended or proceeds into task work when nothing was. Artifact regeneration, stale-page detection, and the draft-description refresh belong to slice 2."

## Clarifications

### Session 1 — Feedback Sweep Log and commit protocol (2026-08-20)

- **Q: One commit per amendment or one per run, and where does the log write
  go?** → One commit per amendment. The Feedback Sweep Log and Consensus
  Resolution Log writes ride a separate bookkeeping commit, one per amendment,
  staging the workflow file alone under a `chore:` subject. A row that names
  its commit cannot exist until that commit's sha does, so the separation is
  forced rather than stylistic. Recorded as FR-012 and FR-012a.
- **Q: Which Consensus Resolution Log type value marks a sweep amendment, and
  how does the escape-rate metric treat it?** → `Sweep`, a fourth value beside
  `Clarify`, `Gap`, and `Finding`. Sweep rows count toward the Round-2
  escape-rate metric rather than being excluded from it. They come from the
  same category-routed protocol and can be mis-routed the same way, and the
  dispositions that would have distorted the metric never reach the log,
  because FR-011 keeps answered, deferred, and no-action items out of
  consensus. Recorded as FR-014.
- **Q: One class per comment, or one item per recognized objection?** → One
  class per comment. FR-015's one-reply-per-comment rule and FR-009's
  comment-id skip key both take the comment as the unit, and splitting a
  comment into several classified items would leave both undefined. When one
  comment's objections diverge, `amended` dominates and the non-dominant
  objections are named in the disposition and the reply. Recorded as FR-010.
- **Q: What is the Feedback Sweep Log's exact shape and placement?** → Header
  `| # | Comment ID | Surface | Author | Class | Disposition | Commit | CRL # |`
  under its own `### Feedback Sweep Log` heading, immediately after
  `### Consensus Resolution Log`. Placement is additive-safe: the phase-coverage
  guard's table reader is heading-anchored, breaks on any line starting with
  `#`, and carries no reference to the Consensus Resolution Log at all.
  Recorded as FR-013.
- **Q: What does a re-run read to skip, and what happens to an amendment whose
  log row never landed?** → The skip key is the log's comment-id column alone.
  An amendment that was pushed before its bookkeeping commit landed is
  re-processed on the next run, because the log is the only record and FR-006
  bars the sweep's own reply from serving as a fallback marker.
  Per-amendment bookkeeping bounds that window to one item. Recorded as
  FR-009, FR-012a, and an edge case.

**Correction carried into this session.** The design concept's rationale for
keeping the sweep record out of the Consensus Resolution Log leaned on an
aggregator script. That script does not exist: it was removed by an earlier
shipped-Bash purge and nothing replaced it. The decision it justified still
holds on its own terms, and the reasoning above is restated without the tool.

**Four sub-items went to consensus and all four resolved in Round 1**, with no
escalation, no human-review flag, and no escape-hatch keyword. Each is recorded
in the workflow file's Consensus Resolution Log.

- **Escape-rate inclusion.** Confirmed: sweep rows count. Two analysts agreed
  from independent directions. The project-decisions view found no record tying
  the 10% threshold to any phase-specific calibration, so the case for
  excluding sweep rows had no basis in this repository's history. The
  external-practice view reached the same place through control-limit design
  and selection bias, and added that a mixed population is answered by
  stratifying rather than excluding. That refinement needs no new field: the
  `Type` column already is the discriminator.
- **Divergent-objection dominance.** Confirmed. The rule turns out not to be
  invented: the roadmap's 2026-07-28 decision fixed that amendments always stop
  for re-review three weeks before the four-class vocabulary existed, and
  FR-003's cross-platform determinism requirement rules out any tie-break that
  is not a fixed explicit rule. Amended-dominance is the only rule satisfying
  both.
- **Log-to-log link.** Confirmed, and made bidirectional. Neither Markdown
  table reader in the codebase is anchored near these two tables, so a new
  table and a new column are invisible to both. Keying the reverse direction on
  the comment id rather than on a row position alone costs nothing and follows
  the idiom the codebase already uses for durable pointers.
- **Interrupt window.** Confirmed: per-amendment cadence, and the window is
  accepted rather than closed. The `Draft PR` repair rule does not port,
  because repair needs a live witness independent of the record and every
  candidate witness here is closed by FR-006, FR-012, or FR-016. Consensus also
  found three defects in this session's own first-pass text, all now fixed:
  FR-012a's rationale over-claimed (the ordering is forced, the cadence is a
  separate choice), the borrowed `Draft PR` write rules silently dropped the
  `repair` rule, and a run with zero amendments but handled comments had no
  commit to carry its rows.

### Session 2 — helper envelope and hidden coupling (2026-08-20)

This session also carried the unknown-unknowns search the scaffold's blind-spot
pass never ran. It changed the spec more than any other pass. The findings that
became requirements are recorded at FR-004a, FR-004b, FR-005, FR-007, FR-007a,
FR-008, FR-008a, FR-013, SC-005, and SC-008; the ones that became assumptions
are in the Assumptions section. Three sub-items went to consensus.

- **Q: Should the registry recognize the "Copy as Prompt" imperative
  variants?** → Yes, with the entry recording its kind, and recognition alone
  never forcing a class. Two of three analysts. The deciding argument inverts
  the intuition: leaving them unregistered is the *worse* posture, because the
  imperative text then reaches the analysts as unlabelled free text and the
  security-keyword routing matches none of that phrasing. Recorded as FR-007c
  and FR-007d.
- **Q: How does the sweep recognize its own reply?** → An anchored HTML-comment
  marker at the start of the body, **and** an author match, both required.
  Unanimous on the marker; the author half is an added filter that costs
  nothing and blocks another account from spoofing it. Matching the author
  alone was rejected because the sweep authenticates as the operator, who is
  the reviewer the checkpoint exists for. A visible sentence was rejected
  because a reviewer quoting a reply to disagree with it would copy that
  sentence and be silently skipped. Recorded as FR-006, FR-006a, FR-015, and
  FR-015a.
- **Q: Does corroboration status `skipped` stop or proceed?** → Stop. Both
  analysts, high confidence, and it turned out to be a vocabulary gap rather
  than an open question: User Story 3 and SC-006 already counted the
  unreachable-tool case as a fourth stop condition, while FR-019 named only
  three by token. The distinction that carries it: `no_record` means the gate
  does not apply, `skipped` means the gate applies and evaluation failed.
  Recorded as FR-019, FR-019a, and FR-019b.

**Dissent worth preserving.** On the prompt variants, the third analyst argued
for neutralizing rather than labelling — excluding a recognized prompt-variant
comment from the automated amend path and routing it to human review — on the
grounds that a tag nothing consumes changes nothing about what reaches the
agent. That objection is answered inside the chosen option rather than
dismissed: FR-007c requires the registered lead to be carried as matched
metadata rather than passed through as free text, which is the substance of
what marking is for. The remaining difference is only whether a recognized
prompt paste should additionally be barred from amending, and the majority
judged that too costly against honest mis-clicks.

**A scope correction the search produced.** The spec had said three templates
export. Ten do, and seven of those export a prompt kind as well. FR-007b widens
the registry to all of them and FR-008a derives the expected set from the
manifest, which makes the count a data question rather than a design one.

### Session 3 — settled-decision verification (2026-08-20)

Verification, not fresh design. **All eight settled interview decisions came
back encoded**, none partial and none missing, each traced to the requirement
carrying it. The spec did not drift from the interview across two sessions of
heavy editing. No sub-item needed consensus.

- **Q: Do exported blocks inside review threads need their own acceptance
  scenario?** → Extend the existing one rather than add a new one. The behavior
  is surface-independent by construction, so a standalone scenario would assert
  nothing FR-007 does not already force. But leaving it entirely to prose was
  wrong: no scenario named a surface for an export, the fixture list named
  shapes and paths but never a surface, and the promise rested on an assumption
  pointing at a runbook that does not exist yet. US1 Scenario 3 now carries the
  review-thread placement, and FR-008a pins a fixture on each surface.

**Fifteen consistency defects, all fixed.** The two that mattered most were
contradictions the spec had grown into:

- **FR-015 required every reply to name an artifact, a section, and a commit,
  across all four classes.** Only `amended` has any of those, so three of the
  four templates it mandates were unsatisfiable. Now scoped.
- **FR-015's "exactly one reply" had no qualifier**, while SC-002 and SC-003
  gained one in session 1 for exactly the same edge case. The requirement and
  the criterion measuring it disagreed. Now aligned.

Six requirements had no criterion or scenario reaching them. Two of those gaps
were serious enough to earn new criteria rather than a note: **FR-004b**, the
no-shell-argument injection boundary, had no verification anywhere despite
being the security boundary of the whole feature and being stated as a
correction to shipped precedent; and **FR-013's** pipe-escaping and
unresolvable-author rules, both found-and-fixed defects, had no test. Those are
now SC-009 and SC-010. FR-019b's four-cause reporting is now covered by SC-006.

One more stale count fell out: three shipped templates declare the identical
empty-export sentence, not two. Two figures were verified correct and left
alone: ten exporting templates with seven carrying a prompt kind, and the
six-value corroboration vocabulary, which matches the shipped classifier's six
returns exactly.

**The budget verdict is the finding to read.** See the Reviewability Budget
section: the slice no longer fits the ~330 it was scoped against, the honest
range is 325 to 485, and the Plan estimator is structurally blind to it because
none of this slice's paths satisfy its production-file test. It will report zero
and pass. Plan sizes this by hand.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The sweep reads and classifies draft-PR feedback (Priority: P1)

The implement stage opens. Before any task work, the orchestrator looks at the
draft pull request the plan stage left behind. It collects every review thread
still marked unresolved and every comment in the pull-request conversation. It
keeps only the comments written by accounts with write access to the
repository, and it sets the rest aside as untrusted rather than acting on them.
Among the kept comments it recognizes the ones that are artifact exports, by
finding one of a fixed set of known sentences among the comment's opening
lines. It ignores anything it already handled on a previous run, and it ignores
its own replies. What is left gets a single label each: amended, answered,
deferred, or no action.

**Why this priority**: Nothing else in the sweep can happen until the feedback
is read, filtered for trust, and sorted. This story alone converts the
checkpoint from decoration into an inventory the operator can see, and it is
the story that carries the security boundary.

**Independent Test**: Point the sweep at a draft pull request carrying a mix of
comments — a trusted plain comment, a trusted exported markdown block, an
untrusted comment, a comment already recorded from a prior run, and a resolved
thread. Confirm the run reports exactly the trusted, unrecorded, unresolved
items as classified candidates and names every excluded comment with its
exclusion reason.

**Acceptance Scenarios**:

1. **Given** a draft pull request with two unresolved review threads and one
   conversation comment, all from write-capable authors, **When** the sweep
   runs, **Then** all three appear as candidates, each carrying its surface and
   exactly one class from the closed set.
2. **Given** a conversation comment from an account with no write access,
   **When** the sweep runs, **Then** that comment is reported as "not swept:
   untrusted author", is not passed to the consensus protocol, and produces no
   artifact edit.
3. **Given** a verbatim export paste, whose registered sentence sits on line
   four behind the artifact header, **When** the sweep runs, **Then** the
   comment is recognized as an artifact export; **Given** the same paste with
   that header trimmed off, **Then** it is still recognized; **Given** the same
   recognized paste posted into a review thread rather than into the
   conversation, **Then** it is recognized identically and its row records the
   review-thread surface; and **Given** a comment carrying no registered
   sentence in its opening lines, **Then** it is treated as an ordinary
   comment.
4. **Given** a comment id that already appears in the Feedback Sweep Log, and a
   reply the sweep itself posted on an earlier run, **When** the sweep runs
   again, **Then** neither becomes a candidate and no duplicate record or reply
   is produced.

---

### User Story 2 - Amendments run through consensus, get recorded, and stop for re-review (Priority: P2)

For every comment the sweep labelled amended, it hands the item to the existing
category-routed consensus machinery, applies the agreed edit to the
specification, the plan, or the task list, and commits and pushes that change.
It then writes the durable record: one Feedback Sweep Log row for the comment,
plus a Consensus Resolution Log row for the amendment. It posts one reply on
the comment saying what class it got, which artifact and section moved, and
which commit carries it. Once every item is handled, the run stops and asks the
reviewer to look again. If nothing was amended, the sweep still writes its rows
and posts its replies, then walks straight into task work.

**Why this priority**: This is the roadmap's "sweep, amend, re-review" decision
made real. It is what makes the checkpoint worth stopping for, and it depends
on Story 1 having produced a trustworthy classified list.

**Independent Test**: Give the sweep one trusted comment that clearly warrants
a plan change and one that does not. Confirm exactly one amendment commit
lands, both comments get a reply and a log row, only the amendment gets a
Consensus Resolution Log row, and the run stops with a re-review report. Re-run
with no new comments and confirm it proceeds into task work instead.

**Acceptance Scenarios**:

1. **Given** one comment classified amended, **When** the sweep processes it,
   **Then** the consensus protocol resolves it, the edit lands in one of the
   three planning artifacts, and the change is committed and pushed.
2. **Given** a completed amendment, **When** the records are written, **Then**
   the Feedback Sweep Log holds a row with the comment id, surface, author,
   class, disposition, and commit, and a linked Consensus Resolution Log row
   exists; no state file outside the workflow file is written.
3. **Given** four handled comments across all four classes, **When** the sweep
   finishes, **Then** each comment carries exactly one reply naming its class,
   **and Given** the one classified `amended`, **Then** its reply additionally
   names the artifact, the section, and the commit, while the other three name
   none of those because none exists; and no review thread has been resolved by
   the sweep.
4. **Given** at least one amendment, **When** the sweep completes, **Then** the
   run stops before task work with a re-review report that names the comments
   swept, the amendments made, the commit range, and states that draft pages
   regenerate once slice 2 lands; **Given** zero amendments, **Then** the run
   proceeds directly into task execution.

---

### User Story 3 - An unreadable draft pull request stops the stage (Priority: P3)

The workflow file says a draft pull request was opened, but the sweep cannot
read it: the GitHub CLI is unreachable, or the recorded pull request turns out
to be closed, missing, or pointing at something other than this feature. The
run does not guess and does not quietly continue. It stops before any task work
and reports which of those situations it hit and exactly what the operator must
do to resume. The one case that proceeds is the absence of a draft pull request
record at all, because then no checkpoint was ever opened and there is nothing
to sweep.

**Why this priority**: This is the integrity guard. Without it, a flaky tool or
a stale record silently downgrades the checkpoint to optional, which is the
failure this whole feature exists to remove. It is P3 only because the happy
paths must work first.

**Independent Test**: Run the sweep four times, once per unreadable condition,
and confirm each stops before task work with a report naming that condition and
a resume path. Then run it with no draft pull request record and confirm it
proceeds.

**Acceptance Scenarios**:

1. **Given** a Draft PR row is present and the GitHub CLI is unreachable,
   **When** the sweep runs, **Then** the stage stops before any task work with
   a report naming the failure and the resume path.
2. **Given** a Draft PR row is present and corroboration reports the pull
   request closed, missing, or belonging to another feature, **When** the sweep
   runs, **Then** the stage stops with a report naming that status and the
   resume path.
3. **Given** the workflow file carries no Draft PR row, **When** the sweep
   runs, **Then** it proceeds into task work without stopping and without
   reporting an error.

---

### Edge Cases

- An export pasted from a page where nothing was recorded: it carries no lead
  sentence at all, because the builder returns before pushing one, and instead
  carries a different sentence saying nothing was recorded and that the record
  is not an approval. FR-007a registers those sentences so the comment is
  recognized rather than mistaken for reviewer feedback, and it takes the class
  `no action`. Two templates ship the identical sentence, so the template id is
  reported as ambiguous.
- An export pasted with a body large enough to exceed the truncation budget:
  recognition still works, because the registered sentence sits in the opening
  lines, and the record carries the truncation flag so a reader knows the tail
  was not examined.
- A reply the sweep itself posted on an earlier run: the author is
  write-capable and the comment id is new, so the trust filter and the
  already-logged check both pass it. It must still be excluded, or every run
  sweeps the previous run's output.
- A review thread whose author is trusted but whose thread is already resolved:
  skipped, because only unresolved threads are read.
- A comment already recorded in the Feedback Sweep Log that the reviewer has
  since edited: the id is unchanged, so the sweep skips it and the edit is not
  seen until the reviewer posts a new comment.
- A recognized export block pasted into a review thread rather than the
  pull-request conversation: recognition is by lead sentence, so it must work
  identically on either surface.
- The Feedback Sweep Log table does not yet exist in the workflow file, because
  this is the first sweep on this feature.
- The pull request is readable and carries zero comments: a clean sweep with no
  rows written, which proceeds into task work.
- A consensus round on an amended item that reaches no agreement.
- A trusted comment posted after the sweep read the pull request but before the
  run stops: it is not in this run's candidate set and is picked up on the next
  run.
- One comment carrying objections that pull in different directions, for
  example one worth amending and one worth deferring: it takes the single class
  `amended`, and the deferred objection is named in the disposition text and in
  the reply rather than dropped.
- An amendment committed and pushed whose bookkeeping commit never landed: the
  log has no row, so the skip key does not see it and the comment is a
  candidate again on the next run. Per-amendment bookkeeping bounds this to
  one item, and the sweep's own reply cannot serve as a fallback marker
  because FR-006 excludes it from the candidate set. The fresh consensus round
  then either recognizes the artifact already carries the edit and classifies
  the comment answered or no action — one new log row, one new reply, no
  second edit — or amends again, in which case FR-017 stops the run for
  re-review before any task work, the same as a first-time amendment. Neither
  path lets a duplicate edit reach task work unreviewed; this is why the
  window is accepted rather than closed with new detection machinery.

## Requirements *(mandatory)*

### Functional Requirements

**Placement and parity**

- **FR-001**: The feedback sweep MUST run as the first setup step of the
  implement stage's task-execution phase, ahead of opening the
  Implementation-Notes Record, in both the Claude and the Codex phase-execution
  references.
- **FR-002**: The sweep MUST NOT add a row to the Workflow Overview table, and
  MUST NOT change the phase-coverage guard's governed phase-id list, the
  stage-to-phase map, or the workflow template.
- **FR-003**: The sweep MUST produce identical behavior in both platform
  variants for the same input.

**Reading the pull request**

- **FR-004**: When the workflow file carries a Draft PR row whose corroboration
  status is `match`, the sweep MUST read every review thread whose resolved
  flag is false and every pull-request conversation comment on that pull
  request. It MUST NOT read review summary bodies.
- **FR-004a**: Both reads MUST be **paginated to exhaustion**. The nearest
  shipped precedent caps its query at a fixed page of threads and a fixed page
  of comments per thread, with no pagination, and silent truncation at those
  caps would contradict SC-001's claim that every trusted, unrecorded comment
  carries a disposition. The reads MUST also request the author-association
  field explicitly; no shipped query requests it today, so FR-005's filter has
  no input unless this read supplies it.
- **FR-004b**: No comment text may reach a shell argument, in either direction.
  Reads pass their query by file or by structured argument, and every write
  passes its body by file path rather than inline. This is the constraint the
  nearest shipped precedent violates: it interpolates comment and reply text
  directly into a command string.

**Trust boundary**

- **FR-005**: The sweep MUST act only on comments whose author association is
  OWNER, MEMBER, or COLLABORATOR. Every other comment MUST appear in the run
  report as "not swept: untrusted author", MUST NOT be passed to the consensus
  protocol, and MUST NOT influence any artifact edit. The source vocabulary is
  a closed eight-value enum — OWNER, MEMBER, COLLABORATOR, CONTRIBUTOR,
  FIRST_TIMER, FIRST_TIME_CONTRIBUTOR, MANNEQUIN, NONE — and every one of the
  five excluded values MUST have a fixture. The allowlist is a **proxy** for
  write access rather than a statement of it: COLLABORATOR can be a read-only
  invitation and MEMBER is organization membership, which does not imply write
  on this repository. The allowlist stays exactly as stated; the proxy is named
  here so no later reader mistakes it for a permissions check.
- **FR-006**: The sweep MUST exclude replies it posted itself from the
  candidate set on every run, so a reply written by one sweep never becomes
  input to a later one. A comment is the sweep's own reply when **both** hold:
  its body begins with the fixed HTML-comment marker FR-015 requires, matched
  anchored at the start rather than anywhere in the body, and its author is the
  account this run authenticated as. Both conditions are needed. The marker
  alone would silently skip a reviewer who quoted a sweep reply while
  disagreeing with it, since a quote copies the raw body; the author alone
  would skip that account's every genuine comment, because the sweep
  authenticates as the operator rather than as a bot, and the operator is the
  reviewer this checkpoint exists for. Anchoring defeats the quote case, which
  prefixes the copied text. Every self-reply exclusion MUST be named in the run
  report the way an untrusted-author exclusion is, so a marker collision drops
  a candidate visibly rather than silently.
- **FR-006a**: Without a working self-reply exclusion the loop cannot converge:
  each run's reply is a new comment with a new id, which the FR-009 skip key
  never matches, so it becomes the next run's candidate and produces another
  reply without end. SC-003 would be unreachable rather than merely delayed.
  This is why FR-006 is a requirement and not hygiene.

**Deterministic recognition**

- **FR-007**: The sweep MUST recognize an artifact-exported block by matching
  the registry's sentences against the comment's **first ten lines**, as a
  whole-line exact match after normalizing line endings and stripping trailing
  whitespace. The lead sentence is **not** the comment's first line: the
  shipped builder emits `Artifact: <title>`, a feature line, and a blank line
  ahead of it, so the lead lands on line four of a verbatim paste. The
  ten-line window also survives a reviewer trimming that header, and a
  template later adding one. A comment matching no registered sentence MUST be
  treated as an ordinary comment, and recognition MUST NOT require editing any
  shipped gallery template or its payload copy.
- **FR-007a**: The registry MUST also hold the **empty-export** sentences the
  same builder emits when nothing was recorded. On that path the builder
  returns before the lead is ever pushed, so an empty export carries no
  registered lead and would otherwise reach the sweep as ordinary reviewer
  feedback. A recognized empty export takes the class `no action`. Empty
  sentences are not unique per template — **three** shipped templates declare
  the identical string, and three share its companion — so an empty export MUST
  report its template id as ambiguous whenever the matched sentence is shared,
  rather than guessing between the templates that share it.
- **FR-007b**: The registry MUST cover **every shipped template that declares
  an export**, in every kind it declares, not only the draft-stage pages. The
  gallery ships ten exporting templates today and seven of them export a
  `prompt` kind beside the `markdown` kind. Each recognized entry records its
  template id and its kind.
- **FR-007c**: The `prompt` kind matters for safety, not completeness. Its lead
  is an imperative addressed to a coding agent, and an unregistered one reaches
  the consensus analysts as ordinary free text carrying an instruction. The
  security-keyword routing that would otherwise force a full fan-out matches
  none of that phrasing, so leaving these unregistered hides the pattern from
  the mechanism meant to catch it. Recognition is labelling, not distrust: a
  recognized comment still passes the FR-005 filter first and is still
  classified normally by FR-010. What recognition changes is that a registered
  lead is matched as a known constant and carried as metadata, so it does not
  reach an analyst as free instruction text.
- **FR-007d**: Recognition MUST NOT by itself force a class. A reviewer who
  clicks the wrong copy button still meant their objections, and discarding
  them over a button choice would reproduce the "feedback becomes decoration"
  outcome this feature exists to remove. The one exception is the empty-export
  form in FR-007a, which carries no objections to act on.
- **FR-007e**: FR-007c's "carried as metadata" is a claim about the payload
  handed to a consensus analyst, so the payload MUST be specified rather than
  left to the implementation. For a recognized comment, the orchestrator builds
  that payload from two parts: the helper's export record — template id, kind,
  and anchors — and the comment body **with every registered line the helper
  matched removed**. The metadata stands where the removed line was. The
  registered lead therefore never appears in an analyst prompt as text, which
  is the whole of FR-007c's safety claim.

  **A registry entry that only tags the comment while the raw body still
  reaches the analyst does not satisfy FR-007c.** That arrangement would leave
  the imperative addressed to a coding agent sitting in the analyst prompt
  exactly as it does today, with a label attached that nothing acts on, and the
  security-keyword routing still matches none of its phrasing. Recognition
  would then be bookkeeping rather than a defense. This paragraph exists
  because that reading is available from FR-007c's wording alone, and one
  consensus analyst took it.

  The remainder of the body still reaches the analyst, because FR-007d keeps
  the reviewer's genuine objections in play. It MUST be delimited and labelled
  as reviewer-supplied data rather than concatenated into the prompt as
  instruction, which is the standard control for external content entering a
  model prompt. Removal and labelling are complementary: removal handles the
  strings the registry knows, labelling handles the rest, and neither claims to
  handle the other's share.
- **FR-008**: Candidate filtering, export recognition, and candidate reporting
  MUST be deterministic: the same observed pull-request comment data MUST
  always yield the same candidate set. Determinism requires two normalizations
  stated here rather than left to the implementation: line endings are
  normalized before matching, and each comment body is truncated at a fixed
  byte budget well below the runner's 32 KiB bounded-input limit, with the
  truncation flagged per comment. Truncating is not optional — the limit is
  enforced over every string in a request and rejects the **whole** request, so
  one oversized comment would otherwise fail an entire sweep rather than
  degrading that one item.
- **FR-008a**: Golden fixtures MUST pin: every registered sentence, in both the
  verbatim payload shape and a header-trimmed paste; a body delimited with
  carriage returns; an oversized body that truncates; the untrusted-author path
  **for each of the five excluded association values**; one recognized export
  on each of the two comment surfaces; a disposition cell containing a pipe and
  a newline; a comment whose author cannot be resolved; a comment carrying the
  self-reply marker; and the ordinary-comment path. A separate test MUST derive the expected
  set from the gallery manifest and the templates themselves — every template
  the manifest says exports, in every kind it declares — and assert the
  registry matches. Deriving rather than hardcoding is what keeps the registry
  correct as the gallery grows: a template that changes its wording, or a new
  exporting template, fails a test rather than silently disabling recognition.
  It also makes the registry's size a data question rather than a design one,
  so covering ten templates costs the same machinery as covering three. That
  test reads the templates and edits none of them, so it does not cross the
  no-template-edits boundary and triggers no payload regeneration.

**Idempotency and classification**

- **FR-009**: The sweep MUST skip any comment whose id already appears in the
  Feedback Sweep Log. The skip key is the log's comment-id column and nothing
  else: the log is the sole source of "already handled", so a comment absent
  from it is a candidate even when a reply to it exists on the pull request.
- **FR-010**: Every trusted, unrecorded comment MUST be assigned exactly one
  class from the closed set: amended, answered, deferred, no action. No other
  value is permitted. The comment is the unit of classification, so a
  recognized export block carrying several distinct objections still yields one
  class, one log row, and one reply; the recognized anchors are carried as
  detail on that row. When one comment's objections would warrant different
  classes, `amended` MUST win over the other three, and every non-dominant
  objection MUST be named in the row's disposition text and in the reply, so
  nothing is silently dropped. This order is forced, not stylistic: the
  roadmap's "sweep, amend, re-review" decision rejected leaving re-run
  responsibility to manual judgment because that lets feedback become
  decoration, and a classifier that let a mixed comment escape `amended`
  would recreate that same rejected path one layer down; FR-003's
  cross-platform determinism requirement rules out any non-fixed tie-break
  as the alternative.
- **FR-011**: Only the `amended` class routes through the category-routed
  consensus protocol. The `answered`, `deferred`, and `no action` classes MUST
  NOT invoke consensus.

**Amendment**

- **FR-012**: For each amended item, the sweep MUST apply the
  consensus-resolved edit to `spec.md`, `plan.md`, or `tasks.md`, then commit
  and push that change as **one commit per amendment**. A single run-wide
  amendment commit is not permitted: FR-013 requires each log row to name its
  commit, FR-015 requires each reply to name the amending commit, and FR-017
  reports a commit range, none of which survive collapsing every amendment into
  one blob.
- **FR-012a**: The Feedback Sweep Log and Consensus Resolution Log writes MUST
  ride a separate bookkeeping commit and MUST NOT be folded into an amendment
  commit. The ordering is forced, not stylistic: a row that names its commit
  cannot exist until that commit's sha does, so an amendment's bookkeeping
  commit MUST land after that amendment's own commit. The bookkeeping commit
  stages the workflow file path alone, never the workflow directory, and takes
  a `chore:` subject, borrowing the `Draft PR` row's staging shape and subject
  convention but not its `repair` rule: repair depends on a live witness
  independent of the record, and none exists here. FR-012 defines no
  commit-message convention that recovers a comment id from `git log`, FR-006
  excludes the sweep's own reply from the candidate set so it cannot serve as
  a fallback marker, and FR-016 forecloses thread resolution as a signal, so
  there is no second leg to corroborate against and no repair rule is
  defined. One bookkeeping commit is taken per amendment, not per run — a
  cadence choice, not a consequence of the ordering rule, justified
  separately: it bounds the window in which an amendment is pushed but
  unrecorded to a single item, which matters because the consensus protocol
  producing the resolved edit is not proven deterministic beyond routing and
  log aggregation, so a comment reprocessed inside that window is not
  guaranteed to resolve the same way twice. A run with zero amendments but at
  least one handled comment MUST still take exactly one bookkeeping commit,
  carrying every `answered`, `deferred`, and `no action` row FR-018 requires;
  a run with no handled comments writes no rows and takes no bookkeeping
  commit.
- **FR-012b**: The three artifacts FR-012 names are the sweep's **whole edit
  surface**, and that MUST be enforced rather than assumed. Two rules, at two
  different points, because they catch different failures:
  1. **At classification.** A comment whose requested change lies outside
     `spec.md`, `plan.md`, and `tasks.md` in the current feature directory MUST
     NOT take `amended`. It takes `deferred`, and the refused target MUST be
     named in the row's disposition and in the reply, so the reviewer learns
     their request was understood and declined rather than silently ignored.
     No new class is introduced: `deferred` already means recorded and not
     acted on now, already routes nowhere, and already stops nothing.
  2. **At the write.** Before any amendment write, the resolved edit's target
     path MUST be checked against that same three-entry set, in code rather
     than in judgment. A target outside it MUST stop the run and MUST NOT be
     written, partially or otherwise. Reaching this check means classification
     already failed, so it is a defect report and not a routine path — which is
     why it stops rather than downgrading quietly.
  Each amendment commit MUST stage exactly the one artifact path it amended,
  never a directory, so a stray file cannot ride along on an amendment. This
  borrows the path-not-directory staging FR-012a already fixes for the
  bookkeeping commit, for the same reason.

  Rule 1 alone would be prose a mis-routed item walks past; rule 2 alone would
  turn an ordinary out-of-scope request into a stopped run. Together the
  ordinary case is handled gracefully and the defect case fails closed. This is
  the least-privilege half of the trust boundary: FR-005 governs **whose** text
  is acted on, and FR-012b governs **what that text can reach**. The repository
  security policy treats a write grant broader than the job requires as a
  finding in its own right, so an amendment step able to write any path would
  be one even if FR-005 never failed.

**Durable record**

- **FR-013**: The sweep MUST write one Feedback Sweep Log row per handled
  comment, carrying comment id, surface, author, class, disposition, and
  commit. The table sits under its own `### Feedback Sweep Log` heading
  immediately after `### Consensus Resolution Log` in the workflow file, with
  the header `| # | Comment ID | Surface | Author | Class | Disposition |
  Commit | CRL # |`. Because FR-010 puts reviewer-derived prose in the
  `Disposition` cell, that cell MUST escape any pipe as `\|` and any newline as
  a line break: the table readers in this codebase split rows on the bare pipe
  with no escape handling, so one unescaped pipe would shift `CRL #` out of
  position and make FR-014's link read the wrong column. The comment-id key
  sits ahead of the disposition and so survives regardless, which keeps FR-009
  safe. When a comment's author cannot be resolved — the account was deleted,
  and the author field is nullable where the association field is not — the
  `Author` cell records that explicitly rather than being left blank. The
  workflow file MUST be the sole store; no state-file mirror of the sweep
  record may be written.
- **FR-014**: Each amended item MUST additionally produce a Consensus
  Resolution Log row linked to its Feedback Sweep Log row. The link is
  bidirectional and costs no extra column: the sweep row's `CRL #` names the
  Consensus Resolution Log row, and that row's item cell — the column naming
  what was resolved, `Question/Gap/Finding` in the canonical header and `Item`
  or `Question` in several committed workflow files — names the comment id, the
  way existing rows already name their source label. Naming the id rather than
  only a row position keys the reverse direction on an immutable value. The
  row's `Type`
  value is `Sweep`, a fourth value beside the shipped `Clarify`, `Gap`, and
  `Finding`. Sweep rows COUNT toward the Round-2 escape-rate metric the log is
  the data source for: they are produced by the same category-routed protocol
  and can be mis-routed the same way, so excluding them would blind the metric
  precisely where the input is least controlled. The dispositions that could
  distort that metric — answered, deferred, no action — never reach the log at
  all, because FR-011 keeps them out of consensus. Inclusion is not the same as
  losing attribution: the `Type` column is itself the source discriminator, so
  a breach of the threshold can be attributed to sweep rows or to phase rows
  without either being excluded from the rate.

**Reviewer-facing replies**

- **FR-015**: Following a sweep run whose bookkeeping commits all landed, the
  sweep MUST post exactly one reply per handled comment. The qualifier is the
  same one SC-002 and SC-003 carry and for the same reason: an amendment pushed
  before its bookkeeping commit landed is re-processed, and the edge case that
  documents it produces a second reply on that one comment. Every reply names
  its class. **Only an `amended` reply names an artifact, a section, and a
  commit**, because only `amended` routes through consensus and produces an
  edit; the other three classes have none of those to name, so requiring them
  of all four would make three of the four templates unsatisfiable. Each class
  MUST use one fixed reply template, and reply text MUST be plain,
  public-readable English. Every template MUST open with the same fixed
  HTML-comment marker, which renders as nothing and is what FR-006 matches on.
  A marker rather than a visible sentence, because a visible sentence is
  exactly what a reviewer quotes when they disagree, and quoting it would make
  their genuine objection invisible to the next run. The repository already
  treats HTML-comment markers in author-facing pull-request text as contract
  rather than convenience, so this reuses a shipped idiom under a distinct
  name that no existing reader matches.
- **FR-015a**: The two surfaces need different writes. A review-thread reply is
  posted into its thread. The pull-request conversation has no threading, so a
  reply there is a new top-level comment that MUST name the comment it answers,
  keeping one-reply-per-comment legible to a human reading the conversation in
  order. Neither shipped reply-writer in this repository posts to the
  conversation surface at all, so that write is new work with no prior art to
  copy.
- **FR-016**: The sweep MUST NOT resolve any review thread.

**Stop or proceed**

- **FR-017**: When one or more comments were classified `amended`, the run MUST
  stop for re-review before any task work, with a report shaped like the
  plan-stage stop report that names the comments swept, the amendments made,
  the commit range, and states that draft pages regenerate once slice 2 lands.
- **FR-018**: When no comment was classified `amended` but at least one comment
  was handled, the sweep MUST write its records, post its replies, and proceed
  directly into task execution without stopping. When no comment was handled at
  all, it writes no rows, posts no replies, takes no bookkeeping commit, and
  proceeds. The two cases are separated so the first does not read as requiring
  an empty commit on a pull request that carried no comments.
- **FR-018a**: The run report FR-005 requires exists on **every** path the
  sweep takes, not only the stopping one. FR-017 defines a report for the
  amended path and FR-018 proceeds without stopping, which would otherwise
  leave the proceed path with nowhere for FR-005's "not swept: untrusted
  author" line to appear — and the proceed path is exactly where a run that
  swept nothing but untrusted comments lands. Every run therefore reports each
  observed comment's disposition, candidates and exclusions alike, with every
  exclusion naming its reason. Stopping and proceeding differ in what follows
  the report, never in whether one is produced. A run that observed no comments
  at all reports that, which is a one-line report rather than an absent one.
- **FR-019**: When a Draft PR row is present but the pull request cannot be
  read, the run MUST stop before any task work with a report naming the status
  and the resume path. That covers **four** of the six corroboration statuses
  by name: `skipped`, `pr_closed`, `pr_missing`, and `identity_mismatch`. When
  the workflow file carries no Draft PR row (`no_record`), the sweep MUST
  proceed without stopping, and on `match` it sweeps. The six are exhaustive
  and each maps to exactly one behavior.
- **FR-019a**: `skipped` stops, and the distinction it turns on must be stated
  rather than left to a reader. `no_record` means the gate does not apply,
  because no checkpoint was ever opened; `skipped` means the gate applies and
  the observation failed. Treating "could not observe" as "observed nothing"
  would make the checkpoint silently optional exactly when the tool is
  unreliable, which is when unread feedback is most likely. Nothing in this
  repository treats an unreachable tool as evidence of a clean state.
- **FR-019b**: The `skipped` stop MUST read differently from the three
  discrepancy stops, and MUST name which of its causes occurred — the tool was
  absent, unauthenticated, rate-limited, or returned output that could not be
  parsed. Collapsing it into the discrepancy wording costs the operator the
  ability to tell a broken tool from a real discrepancy, and those have
  different fixes. Behavior does not branch on the cause; only the report does.
  The resume path for `skipped` is to fix the tool and re-run, because the
  observation is retaken fresh on every invocation. Clearing the `Draft PR` row
  is **not** a resume path here: that path exists for `pr_missing`, where the
  row's absence would match reality, and reusing it for `skipped` would erase a
  probably-true record to manufacture a `no_record` reading.

### Reviewability Notes *(if applicable)*

- No typed reviewability exception is claimed for this slice. Typed exceptions
  are rare operator-owned overrides. Accepted classes are refactor, infra, and
  upgrade, but generated templates, generated zones, `.process` files, PR
  bodies, and code fences are not valid provenance.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter — the deterministic comment-parse
  behavior and its unit coverage.
- **Secondary surfaces, if any**: docs/process — both phase-execution
  references and the workflow-file protocol entry for the Feedback Sweep Log.
- **Projected reviewable LOC**: **325 to 485, midpoint near 400.** The earlier
  figure of ~330 was set against 18 requirements and is now stale: Clarify
  added thirteen suffixed requirements, four of them substantial — pagination
  to exhaustion, a registry spanning ten templates in two kinds, the
  conversation-surface reply the spec itself calls work with no prior art, and
  four-cause stop reporting. Estimated bottom-up against the nearest shipped
  analogue: the corroboration classifier is 35 lines for a six-outcome
  classification over one supplied observation, while this parse must also
  normalize line endings, truncate at a byte budget with a per-comment flag,
  whole-line match a ten-line window, filter an eight-value enum, apply the
  anchored-marker-plus-author self-reply test, and emit a reasoned exclusion
  list. That is 110 to 160 lines plus 45 to 60 of registry data, against
  roughly 8 in the registry, 70 to 110 in each phase-execution reference, 15 to
  25 in the workflow-file protocol, and 5 to 10 in the consensus protocol.
- **Projected production files**: **8 or 9**, not 7. `consensus-protocol.md`
  must change for the fourth `Type` value, and both `SKILL.md` files carry
  helper names today.
- **Budget result**: **at or over the 400 warn line, and under the 800 block.**
  Stated plainly rather than rounded down. The slice is still one primary
  surface and does not approach the block threshold, so it proceeds; but it no
  longer fits the number this spec was scoped against, and Plan owns the
  decision of whether to accept the warn or re-slice.
- **The Plan estimator cannot check this, and must not be read as if it had.**
  `estimate-reviewable-loc` projects from production files only, and it counts
  a file as production only when its path sits under `src/`, `app/`, `lib/`, or
  `scripts/`, or when it ends in a JavaScript, TypeScript, or SQL extension.
  Every path this slice touches — the runner helpers under
  `speckit-pro/speckit_pro_runner/`, both phase-execution references, both
  protocol references — matches none of those. The estimator will return a
  projection of zero and a status of `pass` no matter how large the real diff
  is. Plan MUST size this slice by hand from its Declared File Operations block
  and record that hand figure, treating the helper's verdict as an absent
  measurement rather than a passing one.
- **Split decision**: ART-008 is split into two stacked vertical slices along a
  Path seam. This spec is slice 1, the checkpoint: the comment-driven path. It
  is followed by slice 2, artifact freshness, specified separately on a branch
  stacked on this one. The estimator's `suggested_slices` was 2, and each slice
  cuts end to end through both platform variants.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Swept comment**: one pull-request comment the sweep considered. Carries its
  id, the surface it came from (review thread or pull-request conversation),
  its author association and, where resolvable, its author, whether it was
  recognized as an artifact export together with that export's form and
  template id, whether its body was truncated before matching, and its assigned
  class.
- **Feedback Sweep Log**: the durable table in the workflow file holding one
  row per handled comment. Header: `| # | Comment ID | Surface | Author |
  Class | Disposition | Commit | CRL # |`. It sits under its own
  `### Feedback Sweep Log` heading immediately after the Consensus Resolution
  Log. `CRL #` carries the linked Consensus Resolution Log row number and is
  empty for every class but `amended`. The table is the sole record of what the
  sweep has already handled and the basis for skipping on re-runs.
- **Export lead registry**: the set of sentences that identify an
  artifact-exported block, matched as a whole line within the comment's opening
  lines rather than against its first line. It covers every shipped template
  the manifest says exports, in every kind it declares, plus the empty-export
  sentences the same builder emits when nothing was recorded. Each entry
  carries its template id and kind. The set is derived from the manifest and
  the templates by a test rather than hand-maintained, so a new exporting page
  or a reworded lead fails that test instead of silently disabling
  recognition.
- **Classification**: the closed four-value vocabulary — amended, answered,
  deferred, no action — assigned to every trusted, unrecorded comment. Exactly
  one value per comment, with `amended` dominant when a single comment's
  objections would warrant different values.
- **Consensus Resolution Log row**: the existing record that already governs
  consensus outcomes. Amendments add a row here in addition to the Feedback
  Sweep Log row. The two are linked both ways: the sweep row's `CRL #` names
  this row, and this row's item text names the comment id, so the join works
  from either side and is keyed on an immutable GitHub id rather than on a
  table position alone. Sweep rows take `Sweep` as their `Type`, which doubles
  as the source discriminator for the escape-rate metric.
- **Draft PR row**: the existing workflow-file record naming the draft pull
  request, together with its corroboration status. The sweep reads it and never
  writes it.

## Non-Goals

Named owners, so none of these is a silent omission.

- **Owned by ART-008 slice 2 (artifact freshness, stacked on this branch)**:
  regenerating the whole draft page set after amendments; detecting stale pages
  from git history on a clean sweep; and refreshing the draft pull-request
  description, including the Resume block wording. Slice 1's stop report states
  that draft pages regenerate once slice 2 lands.
- **Owned by ART-010**: flipping the draft pull request to ready, and the final
  writeup.
- **Owned by the existing post-implementation loop**: remediating review
  comments left after implementation. That machinery is unchanged.
- **Deliberately not built**: resolving review threads; reading review summary
  bodies; a state-file mirror of the sweep record; a new Workflow Overview
  phase row; edits to any shipped gallery template; and edits to any of the
  twelve governed Layer 6 corpus agent definitions.
- **Owned by no spec yet, and deliberately so**: an operator flag to skip the
  sweep. Clarify surfaced the case that was missing at scoping — a fail-closed
  gate on a mandatory path normally ships with a documented override, and
  FR-019 is one. The case is real but the flag stays out of this slice: the
  resume path for every stop is to repair the tool or the record and re-run,
  the observation is retaken on every invocation, and a skip flag on a
  checkpoint whose whole purpose is to be unskippable deserves its own scoping
  rather than an addition here. No owner is named because none exists: this is
  the one entry in this section without one, and saying so is the honest
  alternative to assigning it to a spec that has not agreed to it. The next
  spec to touch the sweep inherits the case rather than rediscovering it.
- **Owned by no spec yet, pending a concrete case**: which class heads the log
  row and reply when a single comment mixes only `answered` and `deferred`
  points, with nothing amend-worthy present. Neither class routes to consensus
  or changes stop-or-proceed, so the choice has no behavioral consequence and
  no owner is assigned.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a draft pull request carrying reviewer feedback, task work
  never begins until 100% of trusted, unrecorded comments carry a recorded
  disposition.
- **SC-002**: Following a sweep run whose bookkeeping commits all landed, every
  handled comment receives exactly one reply. Across the fixture corpus, no
  handled comment has zero replies and none has two.
- **SC-003**: Following a sweep run whose bookkeeping commits all landed,
  re-running the sweep with no new comments produces zero new log rows, zero
  new replies, and zero amendments, and proceeds into task work. When a prior
  run's amendment was pushed but its bookkeeping commit did not land, the next
  run's handling of that one item is the edge case documented under Edge
  Cases, not a violation of this criterion.
- **SC-004**: Zero artifact edits across the fixture corpus are attributable to
  an author outside the write-capable set.
- **SC-005**: The same observed comment data yields the same candidate set on
  every run, demonstrated by golden fixtures covering every registered
  sentence in both the verbatim and header-trimmed shapes, a carriage-return
  body, an oversized body that truncates, every excluded author-association
  value, and the ordinary-comment path.
- **SC-006**: All four unreadable draft-pull-request conditions stop the run
  before any task work, each with a report naming the condition and a resume
  path, and the could-not-observe stop is distinguishable in that report from
  the three discrepancy stops **and names which of its four causes occurred**;
  the no-record condition proceeds. Every one of the six corroboration statuses
  has exactly one specified behavior, with none left to prose alone.
- **SC-007**: Both platform variants produce the same sweep outcome for the
  same input, with no behavioral difference between them.
- **SC-008**: After an amendment run stops, a reviewer can tell from the pull
  request alone what changed and where, without opening the workflow file.
  This rests entirely on the FR-015 replies, and deliberately so: slice 1 makes
  no write to the pull-request description, and a draft description is fully
  fingerprint-protected with no editable region, so there is nowhere safe to
  put an amendment summary there. Slice 2 owns the description refresh and MUST
  NOT weaken the replies on the assumption that the description carries this.

- **SC-009**: No comment text reaches a shell argument on any path, read or
  write, demonstrated by inspecting every command the sweep issues. This is the
  injection boundary for a feature that carries public pull-request text into
  agents that edit the planning artifacts, and it is stated as a correction to
  shipped precedent rather than a restatement of it, so it needs evidence of
  its own rather than inheriting anyone else's.
- **SC-010**: The Feedback Sweep Log survives reviewer-derived prose:
  a disposition containing a pipe and a newline leaves every later column,
  including `CRL #`, readable in its own position, and a comment whose author
  cannot be resolved still produces a complete row. Both are found-and-fixed
  defects rather than hypotheticals, which is why they carry a criterion.
## Assumptions

- The Draft PR row and its corroboration vocabulary already ship from the
  preceding spec. That vocabulary is **six** values, not five: `match`,
  `no_record`, `skipped`, `pr_closed`, `pr_missing`, and `identity_mismatch`.
  This slice reads that record and reuses the whole vocabulary rather than
  defining its own, and FR-019 assigns a behavior to every one of the six.
- SC-004's phrase "write-capable set" is shorthand for the author-association
  allowlist FR-005 defines. The association is a proxy for write access rather
  than a permissions check, as FR-005 states.
- **The unit of trust is the comment, not the text inside it.** FR-005 is
  evaluated once per comment, against that comment's author association. A
  trusted author who quotes, pastes, or forwards text from an untrusted source
  is treated as endorsing it, and the sweep makes no attempt to attribute
  quoted spans inside a trusted body. This is an accepted residual rather than
  an oversight, and naming it is what keeps it accepted: it bounds the
  untrusted-input surface to social engineering of a write-capable account,
  which is the same bound the platform's own agent controls draw when they
  ignore events from users without write access. The residual is why FR-012b
  constrains the edit surface and why FR-007c keeps a registered imperative out
  of an analyst prompt — neither defense assumes the body is clean, only that
  the account vouching for it is write-capable.
- A fail-closed gate on a mandatory path is normally expected to ship with a
  documented override, and this slice ships none. That is recorded as a gap
  under Non-Goals rather than resolved here, and it is explicitly **not** a
  reason to weaken FR-019: the fix for a stopped run is to repair the tool, and
  the observation is retaken on every invocation.
- The category-routed consensus machinery and its four existing roles are
  reused unchanged. This slice adds a caller, not a new protocol.
- The registered sentences are stable strings on the shipped pages. Recognition
  depends on them, so a page that changes one needs its registry entry updated
  in the same change; FR-008a's parity test is what makes that failure loud
  instead of silent.
- The replies FR-015 requires are an orchestrator write, not a runner one. The
  runner's command-plan apply mode is deferred by design and returns an
  expected failure, so no part of the reply path may be built on it. That also
  means the reply behavior sits outside the runner's determinism guarantees, so
  SC-002 is provable only against a captured-command fixture rather than a
  golden helper response.
- Adding a read-only helper restales the byte-identical installed-cache copies
  of the runner sources under the test fixtures. Regenerating them is a
  required step, not an optional one, and the plan counts those copies as
  generated rather than authored.
- Recognized export blocks may arrive on either comment surface. The acceptance
  runbook exercises both placements: one export pasted as a conversation
  comment, one pasted into a review thread.
- One class per comment is settled, not a working default. Recognized export
  anchors are carried as detail on that comment's record.
- The dominance rule ranks `amended` above the other three and stops there. It
  does not order `answered`, `deferred`, and `no action` against each other,
  because those three are behaviorally identical at both points classification
  controls: none route through consensus and none stop the run. The one case
  that leaves open is recorded under Non-Goals as deferred pending a concrete
  case, beside the operator-flag deferral it resembles.
- No aggregator script computes the Round-2 escape rate. The tool the design
  concept named was removed by an earlier shipped-Bash purge, and nothing
  replaced it, so the Consensus Resolution Log table is the metric's only data
  source and a reader computes it from the `Round` column and the
  `escape-hatch` outcome value.
- The deterministic parse is one read-only runner operation registered the way
  the stage resolver already is. Its exact name and field list stay a
  Plan-phase decision, but Clarify has grounded the shape: it reports the
  surfaces read, trusted and untrusted counts, per-comment candidates carrying
  the export form and its anchors, and an explicit exclusion list naming each
  excluded comment's reason. It **reports and never decides**, mirroring the
  corroboration helper: assigning a class stays orchestrator judgment, because
  `amended` is what routes an item into consensus.
- Registering a read-only operation touches seven places, three of which fail
  in ways that name a digest or a JSON blob rather than the mistake: the
  argument-derivation branch rejects a helper that adds no explicit entry, the
  harness manifest compares its helper list in order rather than sorted, and a
  helper not declared as having no shell ancestor is required to name a shell
  script that no longer exists. The remediation and rollback text in that
  manifest also may not contain the substring `bash` in any casing. Plan
  accounts for these; they are recorded here so a later reader does not
  rediscover them by failing.
- One fixed reply template per class, with the exact wording settled at Plan.
- The scoping interview's blind-spot pass did not run. Clarify session 2 did
  that search instead and it changed the spec: it found that the export lead
  does not sit on a comment's first line, that an empty export carries no lead
  at all, that the runner rejects an entire request over one oversized string,
  that a draft description has no editable region, that the runner cannot post
  the replies, and that an unescaped pipe in the disposition text would break
  the log-to-log link. Those are recorded as requirements above rather than
  left as an unsearched gap.
- Reviewers inside the write-capable set act in good faith. The author-
  association filter is the security boundary; it is not a judgement about any
  individual reviewer's intent.
- Slice 2 is stacked on this branch, so this slice's records and report wording
  are the interface slice 2 builds on.
