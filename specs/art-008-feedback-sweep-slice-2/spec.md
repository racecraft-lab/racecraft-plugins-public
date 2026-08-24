# Feature Specification: ART-008 slice 2 — Artifact Freshness

**Feature Branch**: `art-008-feedback-sweep-slice-2`

**Created**: 2026-08-24

**Status**: Draft

**Input**: User description: "ART-008 slice 2 — Artifact Freshness. Slice 1 sweeps draft-PR feedback and amends planning artifacts through consensus, but the draft artifact pages and the draft pull-request description still describe the pre-amendment plan. Its stop report apologizes with a promise: 'draft artifact pages regenerate once slice 2 lands'. This slice replaces that promise: the re-reviewer at the checkpoint must read pages that match the amendments beside them."

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
   **Then** it carries one outcome line per page, each reading `generated` or
   `gap`, and each gap names what was missing and why.
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
  is read-only and deterministic: it takes an observation of the log rows and
  the git facts as input, and returns a verdict plus the page set as output,
  without reading the repository or invoking git itself.
- **FR-005**: The helper MUST return a verdict distinguishing at least: pages
  current, pages stale, and freshness undeterminable, and MUST name the reason
  for an undeterminable verdict.
- **FR-006**: The helper MUST treat an `amended` row with a missing, empty, or
  unresolvable `Commit` as undeterminable for that row, and MUST surface it
  rather than dropping it.
- **FR-007**: The helper MUST treat a missing or empty artifacts directory as
  "no pages to judge" and return a verdict that triggers no regeneration.
- **FR-008**: The helper MUST treat an `amended` commit equal to the last
  artifacts commit as not newer, so the pages read as current.
- **FR-009**: The helper MUST compare against the newest `amended` commit when
  several exist, rather than evaluating each row independently.

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
  `docs` conventional-commit type. The commit is taken only when regeneration
  produced a change under that directory; a run that produced no change takes
  no commit, because an empty commit records nothing and cannot move the FR-001
  join.
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
- **FR-020**: The dedicated artifacts commit MUST NOT be read as the
  bookkeeping commit that slice 1 declines to write on the leg where no comment
  was handled. Slice 1's rule that the no-comment leg writes no bookkeeping
  commit MUST remain unchanged.

#### Reporting

- **FR-021**: Every shortfall produced by regeneration MUST be reported through
  the same three sinks the ART-007 emission machinery already owns: the
  description's gap rows, the `Draft PR` row's note, and the run report.
- **FR-022**: The sweep MUST NOT write the workflow file's `Draft PR` row. That
  row has exactly one writer, the emission machinery, and this slice MUST NOT
  add a second. The emission machinery remains the row's sole writer; this
  slice supplies only the commit that carries what the machinery wrote.
- **FR-023**: Page generation MUST be fail-open. No page shortfall, no
  whole-set gap, and no description-refresh failure may block the run, change
  its stop-or-proceed decision, or prevent a regeneration commit that has
  content from landing.
- **FR-024**: The run report MUST carry one outcome line per page, each reading
  `generated` or `gap`, with every gap naming what was missing and why.
- **FR-025**: The run report MUST name the regeneration commit's sha and the
  outcome of the description refresh.
- **FR-026**: On a sweep that amended nothing and found the pages already
  current, the run report MUST collapse to a single line stating that the pages
  are current as of the named commit.
- **FR-027**: The slice-1 sentence stating that draft artifact pages regenerate
  once slice 2 lands MUST be removed and replaced by the outcome lines above, on
  both platform reference surfaces.

#### Platform and packaging

- **FR-028**: Runner code MUST use only the Python 3.11+ standard library, and
  MUST NOT add a Bash or `jq` dependency.
- **FR-029**: The Claude autopilot references and their Codex mirrors MUST
  describe the same behavior and stay in step with each other.
- **FR-030**: New behavior MUST land in the autopilot `references/` files rather
  than in the Codex autopilot `SKILL.md` body, whose word budget is fully
  consumed. Adding to that body is permitted only after words are freed first.
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
- **FR-034**: Each corroboration status at the refresh call site MUST take the
  behavior the ART-007 create-or-refresh contract already assigns it at its
  terminal step: `match` refreshes; `no_record` falls through to the live
  by-branch existence test; `skipped` never creates and reports through the
  could-not-be-opened shape, naming which of the four causes occurred;
  `pr_closed`, `pr_missing`, and `identity_mismatch` each end the refresh
  attempt, create nothing, and leave the `Draft PR` row exactly as found. No
  status opens a second pull request.
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
  refreshes nothing. The report MUST name the operator's manual resume path:
  refresh the pull-request description directly, outside the automated
  sequence. When the failure traces to the recorded and live pull-request
  identities disagreeing, the report MUST name both identities, the one
  recorded and the one observed.
- **FR-037**: A whole-set regeneration failure MUST still run the description
  refresh, which carries the whole-set gap as a single row through the ART-007
  three-sink contract, and MUST leave the stop-or-proceed decision unchanged.
- **FR-038**: The FR-001 join repairs an interrupted run, never a gapped one.
  Any commit touching the artifacts directory marks the set current on the next
  run's join, including a commit carrying only removals and a commit carrying
  only a subset of the selected pages. Per-page gaps are therefore the
  operator's to act on from the report, and no later run re-attempts them.
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
  outcome (FR-025) and MUST NOT block the run (FR-023); the row's existing
  repair rule recovers an unwritten row on the next refresh that reaches this
  step, so the failure is reported, never fatal.

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
- **Freshness verdict**: The helper's output. Names whether the pages are
  current, stale, or undeterminable, the commits the decision rests on, and the
  page set the decision applies to.
- **Regeneration commit**: The one dedicated commit that carries the
  regenerated pages and stages the artifacts directory alone. Its sha is what
  the report names and what the next run's join reads.
- **Page outcome**: One record per page in the report, reading `generated`,
  `gap` with a reason, or `removed`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After a sweep that amends, 100% of the draft artifact pages the
  reviewer opens at the re-review stop describe the amended plan. Zero pages are
  older than the newest amendment.
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
  regeneration work and emits one line about it.
- **SC-007**: No run report anywhere states that pages will regenerate in a
  future slice.
- **SC-008**: The two platform surfaces describe identical behavior, verified by
  the repository's existing platform-parity checks.

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
