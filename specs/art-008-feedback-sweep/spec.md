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
range at the time was 325 to 485, which Plan later corrected upward to 515 to
745 by re-measuring against the right precedents. The Plan estimator is
structurally blind to either figure, because
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
- A consensus round on an amended item that reaches no agreement: it produces no
  edit and no class, writes a Consensus Resolution Log row and no sweep row, and
  stops the run under FR-011a. Because no sweep row exists, the comment is a
  candidate again once a human has resolved the disagreement.
- One comment surface reads cleanly and the other fails, or pagination fails on
  page three of five: the whole observation is discarded and the run stops under
  FR-004c. Nothing was written, so nothing is unwound, and the report says
  reading had begun so the operator can tell this from a gate failure.
- An amendment committed locally whose push failed: the run stops before that
  amendment's bookkeeping commit, so no row and no reply exist, and the local
  commit stands. The next run treats the comment as a candidate again, which is
  the interrupt window FR-012a already bounds, reached by a different route.
- A reply that posts on the review-thread surface and fails on the conversation
  surface: each affected comment keeps its log row and is owed a reply, which
  FR-015b's reconciliation posts on the next run rather than the failure being
  permanent.
- An analyst that dies mid-round, which happened during this specification's own
  consensus: after the shipped protocol's single retry it becomes a human-review
  outcome and takes the FR-011a path, while the other items in the batch
  complete.
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
- **FR-004c**: The two reads are **one observation, taken all or nothing**. It
  succeeds only when both surfaces have been read to exhaustion; any read error
  at any point fails the whole observation. This covers the case FR-019 does
  not: FR-019's statuses are observed at the gate, **before** these reads begin,
  so a pull request that corroborated `match` can still fail once reading
  starts. Three failures fall under this rule — one surface readable and the
  other not, a page of either surface failing partway through pagination, and a
  read that returns output that cannot be parsed.

  **A failed observation is discarded rather than swept.** The partial data MUST
  NOT reach classification. The run writes no Feedback Sweep Log rows, posts no
  replies, takes no commit, and stops with the FR-020 report. Nothing needs
  unwinding, because every read precedes every write.

  The reason is FR-019a's principle applied one step later. At the gate,
  treating "could not observe" as "observed nothing" would make the checkpoint
  silently optional; here, sweeping the half that was read would make it
  silently partial, and a half-swept pull request that reported success is worse
  than one that reported failure, because only the second gets re-run.
  SC-001's claim that every trusted, unrecorded comment carries a disposition
  cannot be evaluated against a candidate set that is missing an unknown number
  of comments, so a partial set has no verifiable relationship to the criterion
  the sweep exists to satisfy.

  **The report distinguishes this from the gate stop.** Both draw on the same
  four causes FR-019b names — absent, unauthenticated, rate-limited, or
  unparseable output — so the report MUST also name that reading had begun, and
  which surface failed. An operator who cannot tell a gate failure from a
  mid-read failure cannot tell whether the pull request was ever reachable. The
  resume path is FR-019b's: fix the tool and re-run. The observation is retaken
  fresh on every invocation, so a re-run needs no repair step.

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
- **FR-006b**: FR-006's author half depends on an input — the account this run
  authenticated as — and that input has two failure modes the requirement must
  name, because both silently disable the exclusion FR-006a says the loop
  depends on.

  **Provenance.** The orchestrator MUST read that account from the live
  authenticated session at call time, the same way FR-004a requires the
  author-association field be read fresh rather than assumed. It MUST NOT come
  from configuration or a remembered value. This is the same shape of
  dependency FR-004a already names, and it needs saying because no shipped
  reference in this repository documents how the orchestrator learns its own
  login, so nothing today guarantees the value arrives correct.

  **Validation.** The value MUST be a non-empty string after surrounding
  whitespace is stripped. Absent, empty, or whitespace-only MUST return an input
  error rather than proceed. The deterministic parse cannot go further than
  presence: its contract forbids it from reaching the network, so it has no
  second, independently sourced value to compare against, and verification is
  therefore the orchestrator's job through provenance rather than the parse's
  through checking.

  That input error **stops the run**, and it stops it with the FR-020 report
  like every other stop rather than as a bare error return. The condition named
  is the missing authenticated account, and the resume path is to supply it from
  the live session and re-run. Naming it as a stop matters because the parse
  returning an error and the run halting are two different events, and only the
  first was stated: an orchestrator reading this requirement alone could log the
  error and continue, which is the exact outcome FR-006a says the loop cannot
  survive. The stop occurs before any read, so nothing has landed and the
  report's what-landed line is empty.

  **What actually breaks, stated correctly.** An empty value does not reduce the
  test to its marker half. Comparison is exact, so an empty account matches no
  real comment author, the author condition is permanently false, and the whole
  conjunction is therefore always false — meaning **no comment is ever excluded
  as a self-reply**, including the sweep's own. The endless-reply outcome
  FR-006a describes follows, by disabling the rule rather than by narrowing it.
  The distinction matters because the two failures have opposite shapes and a
  reader who expects the wrong one would test for the wrong thing.

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
  instruction.

  **Delimiting is the boundary; removal is defence in depth.** The two are not
  equals and the spec says which is which, because a later reader deciding what
  to cut under pressure must cut the right one. Delimiting is the control that
  works against text the registry has never seen, which is every adversarial
  case; removal only ever handles the fixed strings this product itself ships.
  Removal is nonetheless worth keeping, because recognition already computes the
  match span, so stripping it reuses work already paid for. **If cost ever
  forces one of the two out, removal goes and delimiting stays.**
- **FR-007f**: Removal MUST cover **every** matched registered line, not the
  first. This is not a hypothetical: the registry holds each template's markdown
  and prompt leads as separate entries, so a reviewer who pastes both copy
  outputs from one page into one comment — an ordinary workflow this feature's
  own design invites — produces two matches in the same window. Removing only
  the first leaves the second sitting inside the delimited block, which is the
  first-match sanitization failure that recurs across input-validation defects.
  The helper's export record therefore reports **all** matched line numbers in
  ascending order rather than a single one.

  One implementation constraint, because getting it wrong silently corrupts the
  body: removal indexes the line-ending-normalized **original** lines, never the
  trailing-whitespace-stripped copies matching uses for comparison. The two
  differ, and indexing the wrong one misaligns the reconstructed remainder.
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
  self-reply marker, and one carrying the marker with a **different** comment
  id after its fixed prefix, asserting the FR-006 anchor still matches and
  FR-015b's reconciliation reads the id rather than the prefix; a body carrying
  **two** registered lines, asserting both are reported and both removed; an
  empty and a whitespace-only authenticated account, each returning an input
  error; and the ordinary-comment path.

  The failure paths MUST be pinned too, or the requirements grow while the
  corpus stays where the happy path left it: a read that fails on the second
  surface and one that fails mid-pagination, both asserting zero rows, zero
  replies, and zero commits; a corroboration value outside the six; a push
  failure after an amendment commit, asserting no row and no reply followed it;
  a reply that fails on one surface, asserting the comment is owed a reply and
  that a re-run posts exactly one; a comment already carrying a sweep reply,
  asserting no second one; and a human-review consensus outcome, asserting a
  Consensus Resolution Log row, no Feedback Sweep Log row, and a stop. Each of
  these is a stop or a recovery whose whole value is that it behaves correctly
  when something else has already gone wrong, which is exactly the condition a
  hand-run check never reaches.

  A separate test MUST derive the expected
  set from the gallery manifest and the templates themselves — every template
  the manifest says exports, in every kind it declares — and assert the
  registry matches. Deriving rather than hardcoding is what keeps the registry
  correct as the gallery grows: a template that changes its wording, or a new
  exporting template, fails a test rather than silently disabling recognition.
  It also makes the registry's size a data question rather than a design one,
  so covering ten templates costs the same machinery as covering three. That
  test reads the templates and edits none of them, so it does not cross the
  no-template-edits boundary and triggers no payload regeneration.
- **FR-008b**: Two assertions pin the trust boundary itself rather than any one
  behavior, because both guard a leak that would otherwise be invisible.

  First, **no comment body appears anywhere in the parse's own output**. The
  records it returns carry the id, the surface, the author and association, the
  truncation flag, and the export metadata, and no body field at all. That is
  already how the contract is shaped; a fixture asserting it turns an implicit
  shape into a tested invariant, so a later field addition cannot quietly
  reintroduce the most dangerous leak path.

  Second, **an excluded comment's body and every registered line never appear in
  an assembled analyst payload**, asserted against a captured payload the way
  SC-009's boundary is asserted against captured commands. This is the half that
  cannot be made structural: the orchestrator retains its own raw observation
  and legitimately reads candidate bodies to build payloads, so what must be
  proven is that it never reads one for an id the parse excluded. That is
  judgment checked against a fixture rather than a type the runner can enforce,
  and saying so is more honest than implying a guarantee that does not exist.

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
- **FR-011a**: Consensus does not always return an answer, and the three ways it
  fails to MUST all land on one specified behavior. The shipped protocol
  produces `[HUMAN REVIEW NEEDED]` from each of them: all three analysts
  disagreeing after Round 2, a Round-1 escape whose Round 2 still cannot
  resolve, and an analyst that fails its single retry. Behavior does not branch
  on which occurred; only the report names it. The third is not hypothetical —
  an analyst died mid-round during this specification's own consensus.

  **No edit, no class, no sweep row.** A human-review outcome MUST NOT produce
  an artifact edit, and the comment MUST NOT be given a class. `amended` is
  wrong because no edit was resolved, and the other three are wrong because each
  asserts a disposition nobody reached. The closed set of four stands unchanged;
  this outcome does not mint a fifth. The comment therefore gets **no Feedback
  Sweep Log row**, and that is the load-bearing consequence: FR-009's skip key is
  that log's comment-id column and nothing else, so writing no row is what makes
  the comment a candidate again on the next run, after a human has resolved it.
  A row here would record the sweep's failure as its disposition and make the
  outcome permanent.

  **It surfaces in the Consensus Resolution Log instead**, one row, `Type`
  `Sweep`, its item cell naming the comment id the way FR-014 requires, its
  disposition naming the human-review outcome and which of the three ways
  produced it. The two logs differ in what they key: the Consensus Resolution
  Log is the record of consensus rounds and feeds no skip key, so a row there
  costs no idempotency. FR-014's bidirectional link degrades to one direction
  here, by design — the comment id still names the item, and there is no sweep
  row for the `CRL #` to point back from, because none was written. The row
  COUNTS toward the Round-2 escape-rate metric, for FR-014's stated reason: it
  is exactly the escape the metric exists to measure.

  **It stops the run, whether or not anything was amended.** This is the part
  that would otherwise go wrong. FR-018 proceeds when no comment was classified
  `amended`, and a human-review item takes no class at all, so a run whose only
  unresolved item was this one would read as nothing-to-act-on and walk into task
  work — the proceed-versus-stop collapse this feature forecloses everywhere
  else. A human-review outcome stops the run under FR-020, naming every affected
  comment id. When other items amended in the same run, FR-017's stop and this
  one are the same stop and produce one report, not two.

  **Other items in the batch still complete.** The shipped protocol's
  do-not-block-the-batch rule holds: items that resolved are edited, committed,
  recorded, **and replied to** normally, and the run stops after that.
  Discarding resolved work because a sibling item failed would waste consensus
  rounds that already succeeded, and the stop happens either way.

  **The stop sits exactly where FR-017's does** — after this run's rows and
  replies for every handled comment, before any task work. Saying so is what
  makes "the same stop, one report" literally true rather than approximately
  true, and it settles the sibling replies: they post. When nothing was amended,
  this stop replaces FR-018's proceed at that same point, which is the whole of
  FR-011a's effect on a run that would otherwise have continued.

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
  ordinary case is handled gracefully and the defect case fails closed. Of the
  two, **rule 2 is the enforcement boundary and rule 1 is disposition**: a
  decision made once upstream is not a check made at the point of use, and only
  the check at the point of use survives a future caller that skips the
  classifier.

  This is the least-privilege half of the trust boundary: FR-005 governs
  **whose** text is acted on, and FR-012b governs **what that text can reach**.
  The repository security policy treats a write grant broader than the job
  requires as a finding in its own right, so an amendment step able to write any
  path would be one even if FR-005 never failed.
- **FR-012c**: Rule 2's comparison MUST be exact membership over resolved
  paths, never containment. Resolve the candidate target and all three allowed
  paths, then test the candidate for equality against that three-member set. A
  containment or prefix test would admit anything beneath the feature
  directory — its checklists, its contracts — which is not the stated surface,
  and prefix comparison against an unresolved path is a recurring traversal
  defect in its own right. The check MUST also reject a target that is a
  symbolic link, and reject one whose every parent up to the feature directory
  is not, following the hardening the repository's existing pre-write path
  validator already performs; that validator checks repository boundary and
  traversal safety but not job-scoped file identity, so this reuses its shape
  rather than its predicate. The feature directory MUST arrive as an explicit
  input rather than being inferred: the one inference mechanism available keys
  off a branch-name pattern that **this feature's own branch does not match**,
  so inference would resolve to the wrong specification or to nothing.
- **FR-012d**: The write-point stop MUST report under the FR-020 contract,
  naming the defect — the refused target and the comment id — and the resume
  path, which is to fix the classification and re-run. Every stop this document
  defines names a report; one that halted without one would read as a bare
  failure beside them.

  The `deferred` reply for rule 1 MUST NOT imply future action. This document
  elsewhere requires deferred work to name a follow-up owner, and rule 1 has
  none: the request is declined, not scheduled. Word it as recorded and not
  acted on, with the target outside the sweep's edit surface.
- **FR-012e**: The push is part of the amendment step, not a step after it, so
  an amendment whose commit succeeded and whose push failed MUST have a
  specified outcome. It is a different failure from the one under Edge Cases:
  there, the amendment reached the remote and its bookkeeping never did; here,
  the amendment never reached the remote at all, and the local branch carries a
  commit the pull request has never seen.

  **The run stops immediately, before that amendment's bookkeeping commit is
  taken**, under FR-020, naming the unpushed commit's sha and the comment id.
  Ordering does the work: FR-012a already fixes the bookkeeping commit after the
  amendment's own commit, so stopping between them means no log row is written
  and — because FR-015 gates replies on bookkeeping commits having landed — no
  reply is posted.

  **The local commit stands and MUST NOT be unwound.** The edit is correct work
  that consensus resolved; discarding it would throw away a completed round to
  tidy a state that is already recoverable. Recovery follows the path Edge Cases
  already accepts, reached by a different route: no row means FR-009's skip key
  does not see the comment, so it is a candidate again next run, and the fresh
  consensus round either recognizes the artifact already carries the edit and
  classifies it `answered` or `no action`, or amends again and stops for
  re-review under FR-017. Per-amendment cadence bounds the exposure to one item,
  exactly as FR-012a intends it to. No new detection machinery is defined, for
  the reason FR-012a gives: there is no witness independent of the record to
  corroborate against.

  **A bookkeeping commit whose push fails stops the run the same way**, and
  differs in one consequence worth stating. Its row is already in the local
  workflow file, and the sweep reads that file locally, so FR-009's skip key
  **does** see the comment on the next run and skips it. The reply is what would
  otherwise be lost, and FR-015b's reconciliation rule is what recovers it.

  **No automatic retry.** A failed push stops and the operator re-runs, matching
  the resume path FR-019b fixes for a tool that could not be reached. Retrying
  inside the run would multiply the window in which an amendment is pushed but
  unrecorded, which is the window FR-012a's cadence exists to bound.

**Durable record**

- **FR-013**: The sweep MUST write one Feedback Sweep Log row per handled
  comment, carrying comment id, surface, author, class, disposition, and
  commit. A comment is **handled** when it was assigned a class under FR-010,
  which is the definition every "handled" in this document carries. It excludes
  a comment the trust filter or the self-reply rule dropped, and — since FR-011a
  — a comment whose consensus round returned no answer, because that comment
  takes no class. The term was load-bearing before it was defined; stating it
  here keeps FR-018's proceed condition and FR-015's reply count reading off the
  same set. The table sits under its own `### Feedback Sweep Log` heading
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
  without either being excluded from the rate. A human-review outcome under
  FR-011a also writes one row here and no Feedback Sweep Log row, so the
  bidirectional link degrades to one direction on that path alone; FR-011a
  states why.

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
- **FR-015b**: A reply write can fail, and without a rule for it the failure is
  permanent and silent. The sequence is what makes it so: FR-013's row is
  written and its bookkeeping commit lands **before** any reply is posted, and
  FR-009's skip key is that row. A reply that fails after its row landed
  therefore leaves a comment the next run skips as already handled and never
  replies to, and SC-002 becomes unsatisfiable rather than merely violated. The
  failure needs no unusual conditions: FR-015a records that the
  conversation-surface write has no prior art in this repository, so it is the
  least proven write the sweep makes.

  **Replies are reconciled against the pull request, not assumed from the log.**
  Before posting, the sweep MUST determine which handled comments already carry
  one of its replies, and post only to those that do not. A comment is owed a
  reply when it is **present in this run's observation**, has a Feedback Sweep
  Log row, and carries no sweep reply answering it. On the next run this closes
  the gap; within a run it is what makes a retry safe.

  The observation qualifier is load-bearing, not throat-clearing. FR-004 reads
  only unresolved review threads, so a thread a human resolved between runs is
  invisible to the next one — both the comment and the reply inside it. Keying
  the rule on log rows alone would read that invisibility as a missing reply and
  post a second one into a thread someone had deliberately closed, turning a
  recovery rule into a duplicate-reply generator and breaking SC-002 from the
  other direction. A comment the sweep cannot see this run is not owed anything
  this run.

  **The witness is machinery FR-006 already defines.** The sweep identifies its
  own replies by the same two-condition test — the anchored marker and the
  authenticated account — and it already observes every comment on both
  surfaces, so no new read and no new record is needed. To make the
  correspondence exact rather than positional, **the fixed HTML-comment marker
  MUST carry the answered comment's id**. FR-006 continues to anchor on the
  marker's fixed prefix, which is unchanged; the id follows it inside the same
  HTML comment, so it renders as nothing and a reviewer never sees it. Without
  the id, a review thread carrying more than one comment gives no way to tell
  which one a reply answered.

  This deliberately adds no column to the Feedback Sweep Log, whose shape is
  settled, and writes no state mirror, which FR-013 forbids. It also does not
  contradict FR-012a's finding that no witness exists for the bookkeeping
  window: there, the question is which comment an unrecorded amendment belonged
  to, and no reply exists yet to answer it; here, the question is whether a
  reply exists, and the reply is its own direct evidence.

  **A failed reply is reported and does not by itself stop the run.** It MUST
  appear in the FR-018a run report naming the comment id and the surface, so a
  lost reply is visible rather than silent. It does not stop, and the
  distinction from FR-004c is principled rather than convenient: an observation
  that failed means the substantive work never happened, while a reply that
  failed means the work landed and only the notification did not. Stopping task
  work over an undelivered notification that the next run re-sends would let
  flakiness in the least-proven write block a run whose every durable record is
  correct.

  **Per-comment granularity handles the split-surface case.** A run where
  replies post on one surface and fail on the other is many per-comment
  failures, not a distinct condition: each comment is owed a reply or is not,
  and the reconciliation rule reads the same on both surfaces.
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

  **Each stopping status names its own resume path**, because the four have
  different fixes and a shared wording would send the operator to the wrong one.
  `skipped`: fix the tool and re-run, per FR-019b. `pr_closed`: reopen the pull
  request, or clear the `Draft PR` row if the checkpoint is genuinely abandoned,
  then re-run. `pr_missing`: clear the `Draft PR` row, which is the one status
  where the row's absence would match reality. `identity_mismatch`: correct the
  row to name the right pull request, then re-run.

  **The sweep never writes the `Draft PR` row on any path**, including these
  stops. Clearing or correcting it is an operator action named in a resume path,
  never something the run does for itself. A run that repaired the record it had
  just failed to corroborate would destroy the evidence of the discrepancy.

  **A value outside the six is a malformed record and MUST stop**, reported as
  such rather than mapped onto one of the six. The vocabulary being exhaustive
  is a statement about what the preceding spec emits, not a guarantee about what
  this one will read: the row is text in a workflow file that a human edits.
  Fail-closed is forced here rather than chosen: exactly one status proceeds, an
  unrecognized value is not that one, and a default that proceeded would make a
  corrupted record the cheapest way past the checkpoint.
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
- **FR-020**: Every stop uses **one report contract**, with three parts: the
  **condition** that stopped the run, **what already landed** before it did, and
  the **resume path**. Stops accumulated one requirement at a time as this
  specification grew, each naming a report in its own words, and by the end no
  single place said how many there were or what they had in common. This
  requirement is that place.

  The **what-landed** part is the one that has to be stated, because it is the
  part a per-stop wording keeps omitting and the part an operator needs most: it
  names the commits pushed, the log rows written, and the replies posted so far
  in the run, so recovery starts from what is true rather than from a guess. On
  stops that occur before any write it is empty, and saying so explicitly is
  cheaper than leaving the reader to infer it.

  The complete set of stop conditions is: an invalid authenticated account
  (FR-006b), a corroboration status that is not `match` or `no_record`, or one
  outside the six (FR-019), a failed observation (FR-004c), a consensus outcome
  requiring human review (FR-011a), a resolved edit target outside the three
  artifacts (FR-012b rule 2), a failed push (FR-012e), and one or more
  amendments requiring re-review (FR-017). The last of those is the only one
  that is not a failure, and it uses the same contract because an operator
  reading a report should not have to know which kind it is to find the resume
  path.

  Two stops MUST NOT produce two reports. When several conditions hold in one
  run — most commonly a human-review item alongside a completed amendment — the
  run emits one report naming every condition. FR-018a's per-comment
  dispositions appear in that same report rather than in a second one, so every
  run produces exactly one report on every path, stopping or proceeding.

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
- **Projected reviewable LOC**: **515 to 745, midpoint near 630.** This figure
  is Plan's, derived by hand from its Declared File Operations block, and it
  **corrected an earlier estimate in this section upward** rather than
  confirming it. Two anchors in that earlier estimate were measured against the
  wrong precedent: the parse was sized against a 35-line function body when the
  comparable behavior — closed vocabulary, record builder, observation
  validators, classifier — is 162 lines in this codebase's style, and a
  protocol entry was allowed 15 to 25 lines when the only comparable shipped
  entry is 58. The trust-boundary requirements added after that correction move
  the high end toward roughly 775.
- **Projected production files**: **7.** Not the 8 or 9 an earlier draft of this
  section carried. The difference is that neither `SKILL.md` is edited at all:
  the Codex variant sits three words below its 8000-word cap, so it cannot take
  a line, and the Claude variant is left alone to keep the two in step.
- **Budget result**: **two warns, zero blocks.** Over the 400 reviewable-LOC
  warn and over the 6 production-file warn; under the 800 LOC block and the
  8-file block, on a single primary surface. The file count matters more than it
  looks: the block fires above 8, so the 7 this slice carries is a warn, while
  the 9 the earlier draft claimed would have been a block. Getting that number
  right was the difference between proceeding and stopping.
- **The warn is accepted rather than re-sliced.** The only split that reaches
  400 while still shipping a working checkpoint does not exist: the parse and
  the two phase-execution references are the irreducible core, and the split
  that would fit — records in one slice, consensus and replies and
  stop-or-proceed in another — ships a checkpoint that reads feedback and acts
  on none of it. Deferring the three serialization-family registry rows saves 15
  to 30 lines and costs FR-007b. Re-slicing remains the operator's call, made
  against real numbers rather than a rounded-down one.
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
  rather than an addition here. No owner is named because none exists, which is
  the honest alternative to assigning it to a spec that has not agreed to it.
  The next spec to touch the sweep inherits the case rather than rediscovering
  it.
- **Owned by no spec yet**: hardening the shared consensus prompt templates so
  every caller delimits external text as reviewer-supplied data. All three of
  those templates interpolate their content raw today, with no delimiter and no
  treat-as-data instruction, and all three analyst roles describe their input by
  source rather than by trust level. FR-007e supplies that control **locally**,
  in how this slice builds its own payload, and deliberately does not rewrite
  the shared template that three other callers also use. Recorded so this
  slice's local fix is not mistaken for having closed the general case.
- **Owned by no spec yet**: a job-scoped edit-target guard on the shared
  consensus write path. The component that proposes an edit emits a free-form
  file path and nothing validates it; the three-file enumeration in the shared
  protocol turns out to be justified by write contention rather than by scope
  safety. FR-012b guards only the sweep's own caller into that path. The general
  surface predates this slice and stays open.
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
  handled comment has zero replies and none has two. When a reply write itself
  failed, that comment is owed a reply the next run posts under FR-015b's
  reconciliation rule, and the criterion is met across the pair of runs rather
  than within the first — the same shape of qualifier SC-003 carries, and for
  the same reason.
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
- **SC-011**: No failure leaves the sweep having acted on part of the feedback
  while reporting success. Across the fixture corpus, a run that failed to read
  either surface completely writes zero rows, posts zero replies, and takes zero
  commits; every stop carries a report naming the condition, what already
  landed, and a resume path; and no path reaches task work after a stop
  condition held. This is the criterion the whole error-handling surface exists
  to satisfy, and it is stated separately from SC-006 because SC-006 covers only
  the four conditions observable at the gate, before any work has been done.
## Assumptions

- The Draft PR row and its corroboration vocabulary already ship from the
  preceding spec. That vocabulary is **six** values, not five: `match`,
  `no_record`, `skipped`, `pr_closed`, `pr_missing`, and `identity_mismatch`.
  This slice reads that record and reuses the whole vocabulary rather than
  defining its own, and FR-019 assigns a behavior to every one of the six.
- SC-004's phrase "write-capable set" is shorthand for the author-association
  allowlist FR-005 defines. The association is a proxy for write access rather
  than a permissions check, as FR-005 states.
- The author allowlist and the content controls answer two different questions
  and neither substitutes for the other. FR-005 is an **authorization** gate: it
  decides who may cause the sweep to act at all, and gating elevated processing
  on the poster's standing is ordinary practice. FR-007e is a **content** control
  and stays in force regardless of who posted. Letting the first silently
  upgrade the second — treating a trusted author's relayed text as vetted
  because the relayer is trusted — is the documented failure mode behind
  real-world indirect-injection incidents, so the spec keeps the two axes
  separate on purpose.
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
