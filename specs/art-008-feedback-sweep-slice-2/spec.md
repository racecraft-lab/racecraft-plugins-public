# Feature Specification: ART-008 slice 2 — Artifact Freshness

**Feature Branch**: `art-008-feedback-sweep-slice-2`

**Created**: 2026-08-24

**Status**: Draft

**Input**: User description: "ART-008 slice 2 — Artifact Freshness. Slice 1 sweeps draft-PR feedback and amends planning artifacts through consensus, but the draft artifact pages and the draft pull-request description still describe the pre-amendment plan. Its stop report apologizes with a promise: 'draft artifact pages regenerate once slice 2 lands'. This slice replaces that promise: the re-reviewer at the checkpoint must read pages that match the amendments beside them."

## Clarifications

### Session 2026-08-24 — autopilot Clarify, sessions 1-2

- **Q: Does the freshness helper read the workflow file itself, or does the
  orchestrator parse the `Feedback Sweep Log` rows and pass them as data?** →
  The helper reads the file, through the same heading-anchored table read the
  sweep already ships. Only facts the helper cannot derive from that one file
  — git ancestry and artifacts-directory state — arrive as supplied data. This
  completes the mirror of the shipped sweep helper (path input, in-helper
  table read, network-sourced observation as data) and lets FR-031's fixture
  reuse mandate apply literally. Recorded as FR-004 (revised); FR-004a
  unchanged.
- **Q: What does `undeterminable` do?** → Reports loudly, acts never; FR-005a
  carries the non-convergence rationale.
- **Q: What page set does the helper return?** → The pre-regeneration on-disk
  inventory it was given, echoed; selection stays with the emission machinery
  (FR-004), and the FR-012a removal diff is a second named surface of the same
  helper registration.
- **Q: Refresh-failure semantics, `Draft PR` cell carrier, artifacts-commit
  push** → settled in session 1 as FR-033 through FR-039 and FR-019a.
- **Q: Where do the outcome lines land?** → In the single run report every leg
  already emits: page outcomes in the what-already-landed part (its closed
  enumeration extended once, in the shared report-shape section), manual
  resume paths in the resume-path part. There is no separate proceed report,
  and at this call site the three-sink table's second sink is the run report.
- **Q: What query shape and classifier serve FR-033's fresh observation?** →
  The entry gate's own `--state all` five-field query, classified through the
  same six-status logic reused verbatim (FR-033a); the two shipped
  single-observation sentences get an entry-gate scoping (FR-033b). Which
  registration hosts the reused logic is Plan's decision.
- **Q: Which codex-skills/ files must change for parity?** → None for the
  parity validator, which compares file-level structure only; the real
  constraints are the Claude-only-vocabulary regex over the concatenated
  Codex runtime docs and three pinned helper strings in the phase-execution
  mirror (FR-029). Both promise passages (clause and meta-paragraph) come out
  on both surfaces (FR-027).

## User Scenarios & Testing *(mandatory)*

Slice 1 of ART-008 (merged) gave the autopilot run a pull-request feedback
sweep. The sweep reads draft-PR comments, filters them for trust, classifies
them, amends the planning artifacts through consensus, records one row per
handled comment in the workflow file's `Feedback Sweep Log`, posts replies, and
then either stops for re-review or proceeds.

What slice 1 does not do is refresh what the reviewer actually looks at. The
draft artifact pages under `specs/<feature>/artifacts/` and the draft
pull-request description were both authored before the amendments, so the
reviewer arriving at the re-review stop reads pages describing a plan that no
longer exists. Slice 1 handles this by confessing: its stop report states that
the draft artifact pages regenerate once slice 2 lands. That sentence is an
interface slice 2 replaces.

This slice replaces it. After the sweep amends, the run regenerates the draft
page set and refreshes the description before it stops, so the pages beside the
amendments describe the amendments.

### User Story 1 - Amended sweep leaves current pages (Priority: P1)

An autopilot run sweeps the draft pull request, and at least one comment is
classified `amended`: consensus changed the spec, the plan, or the tasks. Before
the run stops for re-review, it regenerates the whole draft page set against the
amended planning record and refreshes the pull-request description. The operator
who opens the pull request at the re-review stop reads pages and a description
that describe the amended plan, not the plan that was amended away.

**Why this priority**: This is the slice. Every other story is a recovery path
or a reporting obligation attached to this one. Without it the re-review stop
shows the reviewer stale pages, which is the defect slice 1 documented rather
than fixed.

**Independent Test**: Run the sweep on a draft pull request carrying a comment
that consensus resolves to an amendment. Confirm the run regenerates the pages
and refreshes the description before it emits the stop report, and confirm the
regenerated pages carry the amended content.

**Acceptance Scenarios**:

1. **Given** a draft pull request whose sweep produced at least one
   `Feedback Sweep Log` row with class `amended`, **When** the sweep finishes
   amending, **Then** the run regenerates the draft page set, refreshes the
   pull-request description, and only then emits the stop report.
2. **Given** the regeneration and refresh have run, **When** the operator opens
   any regenerated page, **Then** the page reflects the amended planning
   record rather than the record as it stood before the sweep.
3. **Given** the amendment commits landed before regeneration, **When** the
   regeneration commit is written, **Then** it is newer than every `Commit`
   named by an `amended` row, so the freshness join reads the pages as current.
4. **Given** an amended sweep, **When** the run stops for re-review, **Then**
   the stop report does not carry the slice-1 promise sentence stating that
   pages regenerate once slice 2 lands.

---

### User Story 2 - Clean sweep repairs pages a prior run left stale (Priority: P2)

A previous run amended the planning artifacts and then died before it could
regenerate the pages: the machine lost power, the session was interrupted, the
budget ran out. The next run sweeps and finds nothing new to amend, because
every comment it can see is already recorded in the log. On that clean sweep the
run still notices that the pages on disk are older than the recorded
amendments, regenerates them, refreshes the description, and proceeds into task
execution without stopping. Nothing new was amended, so there is nothing new to
re-review.

**Why this priority**: This is the recovery path, not the primary path. It
matters because without it a single interrupted run leaves the pages
permanently stale: no later run would ever have a reason to look at them again,
and the pull request would carry pre-amendment pages until a human noticed.

**Independent Test**: Leave the artifacts directory at a commit older than an
`amended` row's commit, then run a sweep that handles nothing new. Confirm the
run detects the staleness, regenerates, refreshes, and proceeds without
stopping.

**Acceptance Scenarios**:

1. **Given** the `Feedback Sweep Log` carries an `amended` row whose `Commit` is
   newer than the last commit touching the feature's artifacts directory,
   **When** a sweep handles no comment or handles comments without amending,
   **Then** the run evaluates the pages as stale, regenerates them, and
   refreshes the description.
2. **Given** that clean-sweep repair completes, **When** the run reaches the
   stop-or-proceed decision, **Then** it proceeds into task execution without
   stopping, because nothing was amended on this run.
3. **Given** a clean sweep where the artifacts directory's last commit is
   already newer than every `amended` row's commit, **When** the run evaluates
   freshness, **Then** it regenerates nothing, refreshes nothing, and proceeds.
4. **Given** a run that repaired stale pages, **When** a further run sweeps
   afterward, **Then** that run evaluates the pages as current and does no
   regeneration work, so the repair is not repeated.

---

### User Story 3 - One honest report of what the pages now are (Priority: P3)

Whatever the run did to the pages, the operator reads one account of it: what
each page came out as, where the regeneration landed, and whether the
description refresh worked. When the sweep was clean and the pages were already
current, that account is a single line naming the commit the pages are current
as of. The operator never has to open git history to learn whether the pages in
front of them are trustworthy.

**Why this priority**: The report is how the freshness guarantee becomes visible.
A run that silently regenerates gives the reviewer no way to distinguish a page
that was rebuilt from one that was skipped, and a page that failed to rebuild
looks exactly like one that succeeded.

**Independent Test**: Run each of the three cases (amended-and-regenerated,
clean-and-repaired, clean-and-already-current) and confirm the report in each
case names the per-page outcomes, the regeneration commit, and the refresh
result, with the already-current case collapsing to one line.

**Acceptance Scenarios**:

1. **Given** a run that regenerated pages, **When** the report is emitted,
   **Then** it carries one outcome line per page, each reading `generated`,
   `gap`, or `removed`, and each gap names what was missing and why.
2. **Given** a run that regenerated pages, **When** the report is emitted,
   **Then** it names the regeneration commit's short sha and the outcome of the
   description refresh.
3. **Given** a run that removed a page the manifest no longer selects, **When**
   the report is emitted, **Then** the removal is named as its own outcome and
   is never silent.
4. **Given** a clean sweep whose pages were already current, **When** the report
   is emitted, **Then** it carries a single line stating the pages are current
   as of the named commit, with no per-page outcome list.
5. **Given** any run reaching the report, **When** the operator reads it,
   **Then** the report states what the pages are rather than promising what a
   future slice will do to them.

---

### Edge Cases

- **No artifacts directory exists.** A run blocked in strict mode never reaches
  draft-PR emission, so it writes no pages and no `Draft PR` row. The freshness
  evaluation must treat a missing artifacts directory as "no pages to judge" and
  do nothing, rather than reading the absent directory as maximally stale and
  attempting a regeneration with no pull request to attach it to.
- **Pages on disk, no commit ever touched the directory.** The emission
  machinery wrote and verified pages and the run died before the dedicated
  commit. These are real pages describing the pre-amendment plan, not an empty
  directory: the evaluation reads them as stale when a joinable `amended` row
  exists, and one regeneration converges.
- **An `amended` row carries an empty or unreadable `Commit` cell.** A row that
  names no commit cannot be joined against history. The evaluation must treat
  such a row as unable to prove freshness either way and report it, rather than
  silently skipping the row (which would read the pages as current) or silently
  failing the whole evaluation.
- **An `amended` row names a commit that is not reachable.** History can be
  rewritten between runs. An unresolvable sha is the same class of problem as an
  empty cell and takes the same treatment.
- **The newest `amended` commit and the last artifacts commit are the same
  commit.** Equal is not newer. The pages are current.
- **The manifest no longer selects a page that exists on disk.** Re-selection
  runs against the amended record, and a signal the amendment removed can
  deselect a page. That page is removed from disk and the removal is reported.
- **Re-selection selects a page whose template is missing or unreadable.** That
  page is a gap for that page; the rest of the set still regenerates.
- **Every page fails to regenerate.** The run carries a whole-set gap and still
  completes its stop-or-proceed decision. No shortfall in page generation
  changes whether the run stops.
- **No draft pull request exists at sweep time.** There is nothing to refresh.
  The evaluation reports that and does not treat it as a page failure.
- **The entry gate stops the sweep.** Four corroboration statuses stop before
  the sweep reads anything, so the freshness evaluation is never reached and
  pages a prior run left stale stay stale. That is not a lost repair: the join
  reads the same `amended` rows on the next `match` run.
- **The description refresh fails while regeneration succeeded.** The pages are
  still committed and the refresh failure is reported as its own outcome. One
  half working is reported as one half working. The failure does not
  self-repair on a later run: once the regeneration commit lands, FR-001's
  join reads the pages as current and no later sweep re-attempts the refresh,
  so FR-036 governs what the report must say.
- **Multiple `amended` rows across several prior runs.** The join compares the
  artifacts directory against the newest of them, not against each in turn.

## Requirements *(mandatory)*

### Functional Requirements

#### The freshness decision

- **FR-001**: The system MUST decide page freshness by a git-history join:
  pages are stale when any `Feedback Sweep Log` row whose `Class` is `amended`
  names a `Commit` that is newer than the last commit touching the feature's
  `specs/<feature>/artifacts/` directory.
- **FR-002**: The system MUST NOT decide freshness by hashing or comparing page
  content. The pages are agent-authored prose, so identical inputs produce
  different bytes and a content comparison would report every page stale on
  every run.
- **FR-003**: The system MUST read the `Feedback Sweep Log` as the sole record
  of what was amended, and MUST NOT introduce any additional bookkeeping store,
  state file, or mirror to track page freshness.
- **FR-004**: The freshness decision MUST be implemented as a runner helper that
  is read-only and deterministic: it reads the `amended` rows from the workflow
  file it is given, through the same heading-anchored `Feedback Sweep Log`
  table read the sweep already ships rather than a second independent parser of
  that table, takes every git fact and the pre-regeneration Artifact page set
  as supplied request data, and returns a verdict over that set as output. The
  helper MUST NOT select which pages to regenerate; manifest-driven page
  selection remains FR-010's, unchanged inside the reused ART-007 emission
  machinery. The workflow file is the only path the helper reads; it MUST NOT
  invoke git and MUST NOT reach the network.
- **FR-004a**: Commit recency MUST be encoded in the observation as ancestry,
  never as a timestamp comparison and never as a sha string comparison. For
  each `amended` row the orchestrator supplies one record keyed by that row's
  `Commit` cell text verbatim, carrying whether the cell resolved to a commit
  and, when it resolved, whether that commit is an ancestor of the last commit
  touching the artifacts directory. A row whose cell text matches no supplied
  record is undeterminable under FR-006. The observation MUST carry an
  explicit success flag as a literal true to be read at all, following the
  shape the sweep's pull-request observation already uses; any other value is
  an unusable observation and returns the undeterminable verdict rather than
  an input error, because FR-023 forbids a failed gather from blocking the
  run.
- **FR-005**: The helper MUST return exactly one verdict from a closed set of
  four — `no_pages`, `stale`, `undeterminable`, `current` — evaluated in that
  precedence order: a missing or empty artifacts directory reads `no_pages`
  regardless of the log (FR-007, FR-007a); failing that, any `amended` row
  that resolves to a commit and is not an ancestor of the last artifacts
  commit reads `stale` (FR-008, FR-009) regardless of any other row's
  condition; failing that, any `amended` row that is missing, empty,
  unresolvable, or matches no supplied observation record (FR-004a, FR-006)
  reads `undeterminable`, and the verdict MUST name each such row's `#` (the
  log's existing 1-based row number) and its reason; only when neither `stale`
  nor `undeterminable` applies to any row is the verdict `current`.
- **FR-005a**: An `undeterminable` verdict MUST NOT by itself trigger
  regeneration, the description refresh, or any commit, and MUST NOT change
  the run's stop-or-proceed decision in either direction: it does not force a
  stop, and on a sweep that amended something this run, FR-015's stop still
  fires on that independent ground. The run report MUST name the verdict, each
  affected row's `#` and reason, and the operator's manual resume path — the
  same shape FR-036 names for an unrecoverable refresh failure — through the
  run report alone; FR-021's three sinks do not apply, since no regeneration
  occurred to produce a shortfall for them to carry. This slice never writes a
  `Feedback Sweep Log` row and FR-003 forbids any second store, so nothing in
  scope can ever clear the condition that produced `undeterminable`; an action
  keyed to it would repeat on every later clean sweep without end, the same
  non-convergence slice 1's self-reply exclusion exists to prevent. Because
  `stale` is evaluated before `undeterminable`, any row that actually proves
  staleness already regenerates through the ordinary stale path, so no
  genuinely stale page stands behind only a report line.
- **FR-006**: The helper MUST treat an `amended` row with a missing, empty, or
  unresolvable `Commit` as undeterminable for that row, and MUST surface it
  rather than dropping it.
- **FR-007**: The helper MUST treat a missing or empty artifacts directory as
  "no pages to judge" and return a verdict that triggers no regeneration.
- **FR-007a**: A feature whose artifacts directory holds pages but whose
  history shows no commit touching that directory MUST read as `stale` when at
  least one joinable `amended` row exists. FR-007's "no pages to judge" is
  reserved for a directory that is absent or empty. Pages written and never
  committed are the interrupted run FR-038 repairs; they converge in exactly
  one regeneration, and reading them as current would leave the pre-amendment
  plan in front of the re-reviewer, which SC-001 forbids.
- **FR-007b**: A row is *joinable* when its `Commit` cell text matched a
  supplied ancestry record and that record carries `resolved` as true. A row
  that matched no record, or matched one that did not resolve, is not joinable
  and is undeterminable under FR-006. FR-007a's stale reading therefore
  requires at least one row that actually resolved: the other reading would let
  an unresolvable row prove staleness, which FR-006 forbids by making that same
  row unable to prove freshness either way. When `last_artifacts_commit` is
  null, every resolved row's ancestry MUST be supplied as not-an-ancestor,
  because there is no commit for it to be an ancestor of and an unstated value
  in the one case FR-007a exists to govern would leave FR-031's fixtures
  nothing to pin. Under that encoding FR-005's stale test already decides the
  FR-007a case on its own terms, so the null-commit disjunct is a restatement
  of the rule rather than a second, independently-implementable one.
- **FR-008**: The helper MUST treat an `amended` commit equal to the last
  artifacts commit as not newer, so the pages read as current. The helper MUST
  NOT implement this by comparing sha strings. The `Commit` cell may hold an
  abbreviated sha while the artifacts commit is supplied in full, so string
  equality would report a matching commit as stale. Under FR-004a's encoding
  the rule needs no separate test: a commit is its own ancestor, so an equal
  commit already reads as not newer.
- **FR-009**: The helper MUST read the pages as stale when any `amended` row's
  commit is not an ancestor of the last artifacts commit, and MUST NOT require
  the rows to be ordered against one another. On the linear branch history
  this join runs against, that disjunction is the comparison against the
  newest `amended` commit: a row older than the artifacts commit contributes
  nothing to the verdict, and one newer decides it alone. What FR-009 forbids
  is a rule that requires every row to be older before reading the pages as
  current.

#### Regeneration

- **FR-010**: When the verdict is stale, the system MUST re-select the page set
  from the shipped gallery manifest evaluated against the amended planning
  record, rather than regenerating the page list the previous run happened to
  produce.
- **FR-011**: The system MUST author every selected page fresh. It MUST NOT
  attempt to patch, diff, or partially update an existing page.
- **FR-012**: The system MUST remove from disk any page that re-selection no
  longer selects, and MUST report each removal as its own outcome. A removal
  MUST never be silent.
- **FR-012a**: The removal set FR-012 acts on MUST be computed by a second
  named surface of the same freshness-helper registration, read-only and
  deterministic: given the pre-regeneration Artifact page set FR-004 observed
  and the manifest re-selection's page-id list — both `generated` and `gap`
  outcomes, since a gapped page is still selected and MUST NOT be removed for
  that reason alone — it returns the set present in the former and absent from
  the latter, matched by the manifest entry id kept as the filename stem. The
  surface MUST NOT delete a file; the system performs the deletion, stages it
  in the FR-018 commit, and reports each removal as its own outcome per
  FR-012.
- **FR-012b**: A selected page whose regeneration returns a `gap` of its own,
  in a run that produced at least one `generated` page, MUST have any
  pre-existing file at its path removed from disk, and that removal MUST be
  reported inside the page's own `gap` outcome rather than as a separate
  `removed` outcome, which FR-012 reserves for deselection. FR-012a keeps a
  gapped page out of the removal set because the page is still selected; that
  rule governs the deselection diff alone and MUST NOT be read as licence to
  leave the page's pre-amendment file in the tree. The reused emission
  machinery already deletes a page that fails its on-disk verification, on the
  stated ground that a plausible-looking document about a plan that is not this
  one is worse than no document at all. A page the author declined to rewrite
  is that same hazard one degree sharper: it is about the right feature and the
  wrong, superseded plan. Leaving it would also put the two sinks FR-021
  requires into direct disagreement, the description's gap row saying the page
  is missing while a complete-looking page sits beside it on disk.
  The whole-set gap FR-037 governs is deliberately excluded: there the run
  learned nothing about any individual page, FR-038 leaves the join reading
  `stale`, and the next sweep leg regenerates the set again, so the stale pages
  are the best available account of the plan for the one leg they survive, and
  deleting them would strand the pull request with no pages at all on the
  strength of a dispatch that never reported. That exclusion is also what keeps
  FR-012b from moving the artifacts directory on a run that must stay
  retryable.
- **FR-013**: Regeneration MUST reuse the existing ART-007 draft-artifact
  emission machinery, including its per-page `generated` or `gap` outcomes and
  its on-disk verification of written pages. This slice MUST NOT introduce a
  second, parallel page-authoring path.
- **FR-014**: After regenerating, the system MUST refresh the draft
  pull-request description through the ART-007 create-or-refresh machinery the
  plan stage already uses, invoked from a new call site inside the Phase 7
  sweep. Slice 1 makes no write to the pull-request description, so this slice
  is that machinery's first caller from Phase 7, not a reuse of a slice-1 path.

#### Ordering and commit shape

- **FR-015**: On a sweep that amended, the system MUST run the sequence amend,
  then regenerate, then refresh, then stop. The regeneration and the refresh
  MUST both complete before the run emits its stop report.
- **FR-015a**: The regeneration sequence MUST run after the sweep's reply
  point, never before it. Slice 1 posts every reply a run owes once, at the end
  of the run, after every bookkeeping commit that run takes has landed; neither
  FR-018's artifacts commit nor FR-039's record commit is a bookkeeping commit
  (FR-020), so the shipped rule places neither of them and an unstated order
  would decide by accident whether a reviewer whose comment was amended is
  answered at all when regeneration later fails. Running after the reply point
  is what keeps this slice's Assumption that slice 1's reply behavior is
  unchanged literally true: every reply is already posted before this slice's
  first new failure point is reached, so no new failure can swallow one.
- **FR-015b**: FR-019a adds a second push to a sequence whose shipped prose
  names only one, and the two closed enumerations that name a failed push MUST
  each be scoped by an added sentence on both platform reference surfaces, in
  the manner FR-033b already uses rather than by rewriting or deleting shipped
  text. First, the enumeration naming the stops that abort before the reply
  point and post no reply — whose members include a failed push — MUST be
  scoped to the amendment push slice 1 owns, so FR-019a's artifacts push, which
  occurs after the reply point under FR-015a, is not read into it. Excluding it
  from that member is not sufficient on its own, because the sentence is an
  exhaustive dichotomy: three named stops are said to occur after the reply
  point and *every other stop* to abort before it. The added sentence MUST
  therefore also place FR-019a's amended-leg stop on the after-reply-point side,
  stating that a run reaching it has already posted every reply it owes. That is
  a statement of where the new stop falls, not an edit to either list's
  membership, so it leaves both enumerations as shipped. Second, the
  enumeration of the conditions that end a run in this sequence MUST be scoped
  where it names a failed push, because FR-017 makes the artifacts push
  non-run-ending on the leg that amended nothing, while the shipped list names
  a failed push unconditionally. Neither edit may add to or remove from the
  members those enumerations already carry.
- **FR-015d**: On the leg FR-017 governs, where at least one comment was
  handled and nothing was classified `amended`, the regeneration sequence
  MUST reach its own terminal outcome, in FR-023's fail-open sense, before
  slice 1's post-publication redaction stop evaluates whether to fire. This
  adds no stop condition and changes no decision Out of Scope reserves to
  slice 1: the stop still fires on exactly the ground slice 1 fixed, one or
  more redaction events on this leg, with the same report shape and the same
  resume path. What this requirement fixes is where slice 1's own trigger,
  "once every write the run owes has landed," is measured from, because
  FR-017 has already, uncontested, inserted the dedicated artifacts commit,
  its push, and the description refresh into what this leg owes before it
  reaches the proceed transition. Evaluating the redaction stop from the
  reply point alone, ahead of those writes, would falsify the shipped
  sentence "this stop replaces the proceed at that same point": FR-017 has
  already moved that point later, so the stop must move with it to remain at
  the same point rather than an earlier one. It would also turn a stop slice
  1 defines as notification after publication, never prevention, into the
  opposite: a gate that blocks writes this leg now owes on the strength of an
  unrelated redaction event. Terminal outcome carries FR-023's meaning, not
  success: a per-page gap, a whole-set gap, or a failed artifacts push under
  FR-019a each end the sequence at their own reported outcome without
  blocking the run, and the redaction stop's evaluation follows immediately
  once any of them is reached. Where FR-019a's push failure leaves the
  artifacts commit local, the redaction stop still fires on this leg's
  coincident redaction event, and its report carries FR-019a's own manual
  resume path beside the redaction report. Both platform reference surfaces
  MUST scope the shipped "stop once every commit is pushed and every reply is
  posted" sentence by an added sentence stating that the writes this leg owes
  now include the regeneration sequence's terminal outcome, in the manner
  FR-015b already uses, rather than rewriting or deleting shipped text. On
  the leg that amended something, no separate rule is needed: FR-015 already
  forces regenerate-then-refresh before any stop that leg emits,
  unconditionally, so a coincident redaction event coalesces into that stop
  under the shipped coalescing rule. On the leg that handled no comment at
  all, this requirement is vacuous: the redaction surface fires only on this
  run's amendment, log-row, and reply writes, none of which exist when
  nothing was handled. The redaction stop is not a fourth sweep leg: a run on
  which it fires is still a run FR-016 requires the freshness evaluation on.
- **FR-016**: The system MUST evaluate freshness on every sweep leg it reaches,
  including the leg that amends nothing and the leg that handles no comment at
  all, because the recovery case in User Story 2 surfaces only on those legs.
  The evaluation runs inside the sweep, so it is reached only when the entry
  gate's corroboration status is `match`. On `no_record` the sweep does not
  run and there is no pull request to refresh; on the four statuses that stop
  the sweep, no evaluation occurs and stale pages stay stale. The FR-001 join
  is durable, so the repair happens on the first `match` run after the operator
  resolves the gate.
- **FR-017**: On a leg that amended nothing, the system MUST regenerate and
  refresh when the verdict is stale, and MUST then proceed without stopping.
  Repairing stale pages MUST NOT convert a proceed into a stop.
- **FR-018**: The system MUST write the regenerated pages in one dedicated
  commit that stages `specs/<feature>/artifacts/` and nothing else, using the
  `docs` conventional-commit type. The commit is taken only when the run's
  final, post-verification outcome set contains at least one `generated` page;
  a run whose verified count is zero — whether reached through a self-reported
  whole-set gap or through the shipped on-disk verification converting every
  written page to a per-page gap — takes no commit and leaves the artifacts
  directory unmoved, because a commit there records nothing generated and
  would move the FR-001 join past pages the run failed to produce.
- **FR-018a**: A run that takes no FR-018 commit MUST leave the artifacts
  directory's working-tree content as the pre-regeneration inventory FR-004
  observed — the same set FR-012a takes as its observed page input — and
  MUST report any restoration it performed. That report is a run-level line
  in the what-already-landed part, beside the commit sha FR-025 already
  requires there; it is NOT a fourth member of FR-024's closed page-outcome
  vocabulary, which stays the three it names. A restored page's own outcome
  is the `gap` that describes why it was not regenerated. FR-018 and FR-037
  both promise the directory is left unmoved, but they promise it of the
  commit, and by the time that promise is evaluated the reused emission
  machinery has already moved the working tree: it writes each page directly
  into `specs/<feature>/artifacts/` and deletes every written page that
  fails its on-disk verification, and FR-011 makes those writes whole-file,
  so a pre-existing page is overwritten and then deleted before the commit
  decision is reached. Both zero-generated paths are covered — the whole-set
  gap of FR-037, and the run whose every written page the verification
  converted to a per-page gap — and FR-037's withheld deselection removal is
  the whole-set instance of this rule rather than a separate one. Without it
  a run can empty the very directory it promised not to move, and FR-005's
  precedence then reads `no_pages` on the next join, which FR-007 says
  triggers nothing: the retry FR-038 promises never fires, and the pages are
  gone rather than stale. From the sweep onward, FR-018's dedicated commit
  MUST also be the only commit that stages any path under
  `specs/<feature>/artifacts/`. The scope is deliberate and does not reach
  backward: the shipped plan-stage boundary commit legitimately carries the
  first artifact generation through its own `specs/` path set, and that
  sequence is untouched. What the rule governs is the phase that hosts the
  sweep, which ends in a commit that stages the whole worktree, so any
  change the sweep left uncommitted under that directory would ride into a
  commit touching it, move the FR-001 join, and mark as current a set the
  run never produced. Both platform reference surfaces MUST scope that
  terminal commit by an added sentence, in the manner FR-015b already uses
  rather than by rewriting or deleting shipped text, stating that the sweep
  leaves nothing uncommitted under the artifacts directory for it to stage.
  How the working tree is restored is a Plan-phase decision, and it is not
  free: on the FR-007a history, where no commit has ever touched the
  directory, git holds no copy to restore from, so the mechanism MUST NOT
  assume one.
- **FR-019**: That commit MUST be separate from the sweep's bookkeeping commit.
  Keeping the artifacts directory in a commit of its own is what makes the
  FR-001 join exact, because any other staged path would move the directory's
  last-touched commit for reasons unrelated to page content.
- **FR-019a**: The push MUST be part of the regeneration step, not a step
  after it: the dedicated artifacts commit is not complete until it is on the
  remote. A push that fails MUST end the emission sequence at that point: the
  refresh step MUST NOT run against pages the remote does not yet show, the
  same sequencing the reused ART-007 emission machinery already applies
  between its own push and its create-or-refresh step. Because refresh never
  ran, the shortfall reaches the run report alone, naming the unpushed
  commit's sha, exactly as the reused machinery's own unreached-sink rule
  already treats a failed branch push. On a sweep that amended (FR-015), this
  MUST stop the run immediately, because SC-001 requires the pages the
  re-review stop's pull request shows to already be current. On a leg that
  amended nothing (FR-017), this MUST NOT convert the proceed into a stop;
  the local commit stands and rides up with the branch's next push.
  On either leg the commit is local and complete, so the FR-001 join reads the
  artifacts directory as current on the next run and no later sweep regenerates
  or attempts the refresh this failure skipped. The run report MUST therefore
  carry the same non-repair statement and manual resume path FR-036 requires of
  a refresh that ran and failed, naming both steps the operator owes: push the
  branch, then refresh the pull-request description directly, outside the
  automated sequence.
- **FR-020**: The dedicated artifacts commit MUST NOT be read as the
  bookkeeping commit that slice 1 declines to write on the leg where no comment
  was handled. Slice 1's rule that the no-comment leg writes no bookkeeping
  commit MUST remain unchanged.

#### Reporting

- **FR-021**: Every shortfall produced by regeneration MUST be reported through
  the same three sinks the ART-007 emission machinery already owns: the
  description's gap rows, the `Draft PR` row's note, and the run report. At
  this Phase 7 call site the third sink is the run report every leg already
  emits — the plan-stage stop report the shipped sink table names does not
  exist here, and the run report takes its place on both the stop and proceed
  legs.
- **FR-022**: The sweep MUST NOT write the workflow file's `Draft PR` row. That
  row has exactly one writer, the emission machinery, and this slice MUST NOT
  add a second. The emission machinery remains the row's sole writer; this
  slice supplies only the commit that carries what the machinery wrote.
- **FR-023**: Page generation MUST be fail-open. No page shortfall, no
  whole-set gap, and no description-refresh failure may block the run, change
  its stop-or-proceed decision, or prevent a regeneration commit that has
  content from landing.
- **FR-024**: The run report MUST carry one outcome line per page, each reading
  `generated`, `gap`, or `removed`, with every gap naming what was missing and
  why. The page outcome lines land in the report's what-already-landed part,
  extending that closed enumeration once in the shared report-shape section so
  every sweep leg inherits them.
- **FR-025**: The run report MUST name the regeneration commit's sha and the
  outcome of the description refresh, in the what-already-landed part; a
  failure's manual resume path (FR-036, FR-005a) belongs in the resume-path
  part.
- **FR-026**: On a sweep that amended nothing and found the pages already
  current, the freshness contribution to the run report MUST collapse to a
  single line stating that the pages are current as of the named commit. The
  report's other mandatory parts are unchanged; this scopes the freshness
  lines, not the report.
- **FR-027**: Both slice-1 promise passages MUST be removed on both platform
  reference surfaces: the stop-report clause stating that draft artifact pages
  regenerate once slice 2 lands, and the meta-paragraph calling that sentence
  an interface slice 2 replaces. The outcome lines above replace them, landing
  once in the shared report-shape section rather than in the amended-leg
  bullet, because FR-016 runs the evaluation on every leg.

#### Platform and packaging

- **FR-028**: Runner code MUST use only the Python 3.11+ standard library, and
  MUST NOT add a Bash or `jq` dependency.
- **FR-029**: The Claude autopilot references and their Codex mirrors MUST
  describe the same behavior and stay in step with each other. New Codex
  mirror prose MUST avoid the Claude-only runtime vocabulary the structural
  validator rejects across the concatenated runtime documents, and edits to
  the Codex phase-execution mirror MUST NOT disturb its three pinned helper
  strings.
- **FR-030**: New behavior MUST land in the autopilot `references/` files rather
  than in the Codex autopilot `SKILL.md` body, measured at 7998 of its
  8000-word cap. Adding to that body is permitted only after words are freed
  first.
- **FR-031**: The freshness helper MUST carry Layer 4 unit coverage driven by
  fixtures, following the pattern the existing pull-request feedback sweep
  helper established, and MUST be declared in the test suite manifest.
- **FR-032**: Any change to shipped plugin source MUST be followed by
  regeneration of the generated payload and proof artifacts before the work is
  considered complete.

#### Failure semantics

- **FR-033**: The refresh MUST take its own live read-only observation of the
  pull request at the moment of the refresh, and MUST NOT reuse the
  corroboration observation the sweep's entry gate read. A pull request can be
  closed or replaced while the sweep runs, and the later read is the current
  evidence.
- **FR-033a**: The refresh call site's observation MUST take the same query
  shape Step 0.6c's entry-gate observation already takes — a `gh pr list`
  scoped to the feature's head branch with `--state all`, returning
  `number,url,state,isDraft,headRefName` — because `--state all` is what makes
  a closed pull request distinguishable from an absent one, and the reused
  create-or-refresh machinery's own existence test alone cannot produce that
  distinction. The refresh call site MUST classify that observation through
  the same closed six-status vocabulary and precedence rules the entry gate
  already applies, reused verbatim rather than re-implemented: FR-034 requires
  the refresh call site to take the exact behavior the ART-007 contract already
  assigns each status, and that guarantee holds only when the same
  classification logic decides it in both places. The classification MUST stay
  read-only and deterministic, taking the observation as supplied data under
  the same explicit `ok: true` literal-success shape the entry gate's
  observation already requires, and MUST carry Layer 4 fixture coverage.
  Which runner-helper registration exposes this reused logic to the new call
  site is a Plan-phase decision; this requirement pins only that the
  vocabulary, precedence rules, and observation-as-data contract are shared,
  never re-derived.
- **FR-033b**: The existing sentence stating that the sweep reads Step 0.6c's
  report "rather than taking an observation of its own", under "Phase 7
  Setup: The Corroboration Gate" on both platform reference surfaces, MUST be
  scoped by an added sentence to the entry gate's sweep-or-not decision alone
  — the one decision Step 0.6c's pre-phase observation was taken for. It MUST
  NOT be read as forbidding the refresh call site FR-033a adds deeper inside
  Phase 7, which runs only after the entry gate has already passed and the
  sweep has already amended. The neighboring "one read-only observation per
  run" wording in the same skill file MUST receive the same scoping, to
  Step 0.6c's own step rather than every corroboration read a run may take.
  Neither edit contradicts ART-007's own precedent: its create-or-refresh
  terminal step already takes a second live read distinct from Step 0.6c's,
  on the documented principle that the two reads are separate and the later
  one is the current evidence. FR-033 extends that same, already-shipped
  principle to a third read; it does not introduce a new kind of observation.
- **FR-034**: Each corroboration status at the refresh call site MUST take the
  behavior the ART-007 create-or-refresh contract already assigns it at its
  terminal step: `match` refreshes; `no_record` falls through to the live
  by-branch existence test; `skipped` never creates and reports through the
  could-not-be-opened shape, naming which of the four causes occurred;
  `pr_closed`, `pr_missing`, and `identity_mismatch` each end the refresh
  attempt, create nothing, and leave the `Draft PR` row exactly as found. No
  status opens a second pull request.
- **FR-034a**: One of FR-034's six statuses cannot classify at the refresh
  call site, and one classifies with only a single live branch; FR-034 MUST
  say so rather than leave a create-capable branch importable into Phase 7. `no_record` requires an absent `Draft PR` row, but
  FR-016 reaches the sweep only on an entry-gate `match`, which requires the
  row to be present, and FR-022 forbids the sweep writing that row, so no step
  between the gate and the refresh can clear it. `skipped` is the shipped
  contract's two-branch status — it refreshes the recorded pull request when
  the tool can be reached, and reports through the could-not-be-opened shape
  when it cannot — and only the second branch is live here, because at this
  call site the classification's own input is the observation FR-033a takes at
  that moment, so a `skipped` classification is itself the evidence the tool
  could not be reached. FR-034's single stated behavior for `skipped` is
  therefore the whole of the contract as it applies here, not a narrowing of
  it. Neither status may be implemented as a fallthrough to creation. Should
  either classify despite this reasoning, the refresh attempt MUST end with
  nothing created and the `Draft PR` row left as found, because FR-014
  authorizes a refresh and this slice opens no pull request on any path. A
  defensively-caught `no_record` here indicates an orchestrator invariant
  violation, not an operator-fixable pull-request state, and the report MUST
  say so rather than offer a `Draft PR` row repair as the resume path.
- **FR-035**: A discrepancy or an unreachable tool at the refresh call site MUST
  end the refresh attempt only. It MUST NOT change the run's stop-or-proceed
  decision, MUST NOT unwind a regeneration commit that already landed, and MUST
  NOT be reported as a page failure. This is where slice 2 diverges from
  ART-007: ART-007's terminal step sits at a stage boundary the run stops at
  regardless, while the sweep may proceed into task work.
- **FR-036**: When the description refresh fails, the run report MUST name
  that failure as its own outcome, distinct from the regeneration outcome.
  The report MUST state that once the regeneration commit has landed, a
  re-run does NOT retry the failed refresh: the FR-001 join then reads the
  artifacts directory as current, so a later sweep regenerates nothing and
  refreshes nothing. The report MUST name the operator's manual resume path,
  and MUST name the one belonging to the status that ended the attempt rather
  than a single path shared across them, for the reason the shipped
  corroboration gate already gives: the stopping statuses have different fixes,
  and one shared path would send an operator to the wrong repair. Refreshing
  the pull-request description directly, outside the automated sequence, is the
  path when a reachable pull request's refresh failed. A `skipped` failure
  names fixing the tool; a `pr_closed` failure names reopening the pull
  request; a `pr_missing` failure names correcting or clearing the `Draft PR`
  row. Neither of the last two is repaired by refreshing a description, which
  is why the generic path may not stand in for them. When the failure traces to
  the recorded and live pull-request identities disagreeing, the report MUST
  name both identities, the one recorded and the one observed.
- **FR-037**: A whole-set regeneration failure MUST still run the description
  refresh, which carries the whole-set gap as a single row through the ART-007
  three-sink contract, and MUST leave the stop-or-proceed decision unchanged.
  It MUST also leave the artifacts directory entirely unmoved: no page is
  deleted on this path, FR-012b's per-page deletion is excluded, and FR-012's
  deselection removal is withheld as well, even though the removal set is
  otherwise computable. Withholding it is what keeps FR-018 from taking a
  commit, which is the only thing keeping the FR-001 join reading `stale` so
  the next sweep leg retries. A removal landing alone here would move the
  directory, mark the whole set current, and strand every gapped page
  permanently stale for the sake of deleting one file. Nothing is lost by
  waiting: FR-010 re-selects from the manifest on the retry, so the same
  deselection is recomputed and the removal lands in the run that also
  regenerates.
- **FR-038**: The FR-001 join repairs an interrupted run, never a gapped one.
  Any commit touching the artifacts directory marks the set current on the next
  run's join, including a commit carrying only removals and a commit carrying
  only a subset of the selected pages. Per-page gaps inside a run that took
  that commit are therefore the operator's to act on from the report, and no
  later run re-attempts them. Whether a later leg retries is decided by
  whether the artifacts commit was taken, never by the shape of the shortfall,
  and the spec MUST NOT present the two gap shapes as one outcome. FR-018 takes
  that commit only when something under the directory changed, so a whole-set
  gap — which generated nothing, and which FR-012b excludes from deletion for
  exactly this reason — moves nothing, leaves the join reading `stale`, and is
  retried by the next sweep leg, while a per-page gap beside at least one
  generated page rides a commit that marks the whole set current and is retried
  by nothing. The report MUST state which of the two it is: that the next leg
  retries, or that it does not and the gap is the operator's. A run that
  generated nothing never takes the commit, because FR-037 withholds the
  deselection removal that would otherwise move the directory on that path.
- **FR-039**: When FR-014's refresh actually changes the `Draft PR` row's
  cell, the write MUST ride the emission machinery's own record commit — the
  same separate, workflow-file-path-alone `chore:` commit the plan-stage
  terminal sequence already takes when it records the draft pull request —
  reused verbatim rather than a new commit shape this slice defines. The
  commit is taken only when the cell actually changed; a refresh that leaves
  the cell as found stages nothing and takes no commit, the same no-op the
  machinery already applies whenever a re-run finds nothing left to stage.
  This commit MUST NOT be read as the sweep's bookkeeping commit under
  FR-020, which stands unchanged: a leg that logs no Feedback Sweep Log or
  Consensus Resolution Log row still takes none of those. It MUST NOT be
  folded into the dedicated artifacts commit under FR-018 and FR-019 either.
  A failure of this commit or its push MUST be reported through the refresh
  outcome (FR-025) and MUST NOT block the run (FR-023). The report MUST NOT
  claim the row repairs itself on a later sweep. The emission machinery's
  repair rule recovers an unwritten row only on a later refresh that reaches
  this step, and FR-036 establishes that no later sweep reaches it once the
  regeneration commit has landed, so within this slice the repair path is
  unreachable and saying otherwise would send an operator away from a row that
  stays wrong. The report MUST name the resume path the way FR-036 names its
  own: the pull request itself is correct on the remote and only the record is
  unwritten, so the row is repaired by hand, or by any later run that reaches
  the plan-stage create-or-refresh step, which this slice never schedules.

### Reviewability Notes *(if applicable)*

- No reviewability exception is claimed. This slice is the second half of an
  already-ratified two-slice split of ART-008, and it stays within budget on
  its own.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: docs/process (autopilot reference prose on
  both platforms)
- **Projected reviewable LOC**: ~450 (new freshness helper and its registry
  entry, plus Layer 4 unit tests and fixtures; the reference prose and the
  regenerated payload and proof artifacts are excluded)
- **Projected production files**: 5 (helper module, helper registry, two
  autopilot reference files, test suite manifest)
- **Projected total files**: ~10 (the five above, plus the unit test module and
  its fixture files)
- **Budget result**: within budget
- **Split decision**: This remains one spec. ART-008 was already split into two
  vertical slices before implementation began: slice 1 shipped the sweep itself
  (the checkpoint, reading, trust filtering, classification, consensus
  amendment, logging, replies, and the stop-or-proceed decision) and merged.
  This is slice 2, the artifact freshness half, and splitting it further would
  separate the freshness decision from the regeneration it exists to trigger,
  leaving a helper nothing calls.

#### Superseding note — Plan corrects three of these figures by hand

The bullets above are the spec-time projection. `plan.md`'s "Reviewability
Budget, derived by hand" is the live figure, derived line by line from the
plan's own Declared File Operations block against measured shipped clusters.
Read that section, not these bullets, for the binding number.

The estimator cannot supply one. Run against the plan it returned
`{"status":"pass","projected":0,"declared_files":{"production":0,...,"total_entries":30}}`:
it parsed all thirty entries correctly and recognized **none** of them as
production, because it counts a file as production only under `src/`, `app/`,
`lib/`, or `scripts/`, or by a JavaScript, TypeScript, or SQL extension. Every
production path here is a runner helper under `speckit-pro/speckit_pro_runner/`
or a Markdown reference. That `pass` is an **absent measurement** and MUST NOT
be cited as evidence this slice is within budget.

**Three corrections:**

1. **Projected reviewable LOC**: ~450 is low by roughly a factor of four.
   Corrected to **556 to 825 production-only, midpoint ~690**, and **1350 to
   2345 including tests and fixtures**. Two bases are now stated apart, because
   mixing them makes the figure meaningless: production-only is what the gate's
   estimator scores and what slice 1 recorded against, and it is the binding
   declaration; the with-verification figure is the basis this bullet stated.
   Slice 1's realized density applied to the same file list gives a risk band of
   741 to 1100, recorded in the plan as derivation B.
2. **Budget result**: "within budget" does not survive. Corrected to **WARN on
   reviewable LOC** (690 against a 400 warn), with no block: 5 production files
   against a 6 warn, 12 authored files against a 15 warn, one primary surface.
3. **Projected total files**: ~10 is corrected to **12** — 5 production and 7
   test and fixture.

**Two figures stand.** Production files remain **5**, though the membership
changes: the test suite manifest is verification rather than production, and
`speckit-pro/skills/speckit-autopilot/SKILL.md` takes its place, because
FR-033b's second scoping edit binds the literal phrase "one read-only
observation per run", which occurs exactly once in the tree and occurs there.
Primary surfaces remain **1**.

**The split lever, named because the high end reaches 800.** The one clean seam
is deferring the description-refresh half (FR-014, FR-019a's refresh leg, and
FR-033 through FR-039) into a stacked slice 3. It saves 147 to 245 production
lines, taking the midpoint to roughly 495 — still a warn, still above 400. It is
**rejected**: it would ship a pull request whose description describes the plan
that was amended away while linking to pages that describe the plan that
replaced it, and FR-001's join would read the artifacts directory as current the
moment the regeneration commit landed, leaving the deferred refresh with no
trigger to fire on and therefore no repair path. The full derivation and the
second, worse lever are in `plan.md`.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.
- Review order SHOULD read the freshness helper and its fixtures first, since
  the join rule in FR-001 is what every other requirement depends on, then the
  regeneration and reporting prose, then the platform mirror.

### Key Entities *(include if feature involves data)*

- **Feedback Sweep Log row**: The sole record of what a sweep handled, one row
  per handled comment, carrying the comment id, surface, author, class,
  disposition, commit, and consensus round. This slice reads two of its cells:
  `Class`, to find the rows whose value is `amended`, and `Commit`, to date
  them. This slice never writes a row.
- **Artifact page set**: The draft-stage pages under
  `specs/<feature>/artifacts/`, one file per selected gallery entry, named by
  the entry's id. The set's last-touched commit is one side of the freshness
  join.
- **Gallery manifest entry**: A shipped description of one artifact page,
  carrying the stage it belongs to and the trigger that selects it. Re-selection
  reads the draft-stage entries and evaluates each trigger against the amended
  planning record.
- **Freshness verdict**: The helper's output. Names one of the four closed
  verdicts, the commits the decision rests on, and the pre-regeneration
  Artifact page set it was computed over, echoed from the observation rather
  than selected by the helper.
- **Removal set**: The FR-012a surface's output — members of the
  pre-regeneration Artifact page set absent from the manifest re-selection,
  matched by filename stem. Each becomes a `removed` page outcome once the
  system deletes it.
- **Regeneration commit**: The one dedicated commit that carries the
  regenerated pages and stages the artifacts directory alone. Its sha is what
  the report names and what the next run's join reads.
- **Page outcome**: One record per page in the report, reading `generated`,
  `gap` with a reason, or `removed`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After a sweep that amends, 100% of the draft artifact pages the
  reviewer opens at the re-review stop describe the amended plan. Zero pages are
  older than the newest amendment. A page that regeneration could not produce is
  absent rather than stale, because FR-012b removes the superseded file it left
  behind, so a per-page shortfall subtracts from the set the reviewer sees and
  never adds a misleading member to it. The one stated exception is the
  whole-set gap of FR-037, where the run learned nothing about any page and
  FR-012b deliberately leaves the previous set in place: there the pages are
  stale for exactly one leg, the join still reads `stale` under FR-038, and the
  next sweep leg regenerates them.
- **SC-002**: An operator can determine whether the pages in front of them are
  current in under 30 seconds, reading only the run report, without opening git
  history or comparing page content.
- **SC-003**: A run interrupted between amending and regenerating is repaired by
  the next run, with no operator action and no additional command. Recovery
  takes exactly one subsequent run.
- **SC-004**: Zero page shortfalls block a run. Every page that fails to
  regenerate appears in the report with a stated reason, and the run still
  reaches its stop-or-proceed decision.
- **SC-005**: The freshness verdict is reproducible: the same observation
  produces the same verdict every time it is evaluated, so the decision can be
  covered by fixtures rather than by running a live sweep.
- **SC-006**: A sweep that amends nothing and finds the pages current does zero
  regeneration work, and the freshness contribution to its run report is one
  line.
- **SC-007**: No run report anywhere states that pages will regenerate in a
  future slice.
- **SC-008**: The two platform surfaces describe identical behavior. The
  repository's structural parity checks confirm file-level coverage only;
  prose equivalence is verified by review against FR-029's authoring rules.

## Assumptions

- The `Feedback Sweep Log` table shipped by slice 1 is the only record consulted,
  and its `Class` and `Commit` columns carry the values this slice joins on.
- The freshness evaluation runs on every sweep leg the run reaches, including
  the leg that handles no comment at all. That leg is precisely where the
  recovery case in User Story 2 becomes visible, since an interrupted run's
  comments are already in the log and therefore already skipped.
- A `Draft PR` cell change rides the emission machinery's own record commit
  for the same reason the artifacts commit rides one of its own: slice 1's
  bookkeeping commits land per amendment, strictly before the refresh whose
  outcome the cell records, so no existing commit can legally carry it.
- The dedicated artifacts commit is a commit of this slice's own, distinct from
  slice 1's bookkeeping commit. Writing it on a leg where slice 1 writes no
  bookkeeping commit does not contradict slice 1's rule, which governs the
  bookkeeping commit only.
- The ART-007 emission machinery's existing behavior is reused unchanged: its
  manifest-driven selection, its per-page outcomes, its on-disk verification of
  written pages, its three shortfall sinks, and its fail-open posture. This
  slice supplies the trigger and the timing, not a new authoring path.
  The refresh recomposes the description body for the implement stage rather
  than reusing the plan-stage body: a draft description is fully
  fingerprint-protected with no editable region, so the refresh rewrites it
  whole through the same draft-mode packet path.
- The gallery manifest's draft-stage filter and trigger evaluation are not
  modified by this slice. Re-selection differs from first selection only in that
  it reads the amended planning record.
- Removing a deselected page and regenerating the remaining pages both land in
  the same dedicated artifacts commit, since both are changes under the same
  directory.
- Slice 1's sweep behavior is unchanged in every respect: reading, trust
  filtering, classification, consensus amendment, log rows, replies, and the
  stop-or-proceed decision.
- The repository's generated-artifact contract applies, so a change to shipped
  plugin source is followed by payload and proof regeneration before the work is
  called done.

## Out of Scope

- Any change to slice 1's sweep: comment reading, the trust filter,
  classification, consensus amendment, log row writing, reply posting, or the
  stop-or-proceed decision.
- Content-hash staleness detection, in any form.
- Any new bookkeeping store, state file, or mirror beside the
  `Feedback Sweep Log`.
- A second writer of the workflow file's `Draft PR` row.
- Post-implementation review remediation, which the existing recurring-loop
  machinery already covers.
- Changes to the shipped gallery manifest, its templates, or the set of signals
  that drive page selection.
- Regeneration of artifact pages at any stage other than the draft stage.
