# Phase Execution for Codex

Codex autopilot orchestration runs in the parent session. Phase work runs in
installed custom subagents through `spawn_agent` and `wait_agent`.

## Contents

- [Canonical Order](#canonical-order) — `PHASES = [...]` + `--from-phase` semantics
- [Stage-Bounded Execution](#stage-bounded-execution) — which phases the resolved stage may start, its terminal step, and the resume protocol
- [Agent Mapping](#agent-mapping) — per-phase executor + prompt prefix table
- [Main Execution Loop](#main-execution-loop) — full 11-step per-phase pseudocode
- [Phase 3: Plan — Reviewability Budget](#phase-3-plan--reviewability-budget-advisory) — advisory plan-phase production-LOC estimate
- [Phase 7: Implement](#phase-7-implement) — task decomposition + placeholder replacement + reviewability gate
- [PR Body Generation](#pr-body-generation) — script invocation order pre-PR
- [Coverage Audit](#coverage-audit) — all-phase prefix audit run before/during/on-resume

## Canonical Order

```text
PHASES = [specify, clarify, plan, checklist, tasks, analyze, implement]
```

`--from-phase` changes the first phase to execute, not the required plan
coverage. `update_plan` and `autopilot-state.json` must still contain Phase 0,
all seven SDD phases, and Post before any subagent is spawned.

## Stage-Bounded Execution

`AUTOPILOT_STAGE` is resolved once at Step 0.6c. It bounds which phases this
invocation may run:

| Stage | Phase range | Terminal step |
| --- | --- | --- |
| `plan` | Specify, Clarify, Plan, Checklist, Tasks, Analyze | G6.5 confidence gate, then the stage-boundary commit |
| `implement` | Implement, then the post-implementation steps | `Post: Retrospective` |
| `full` | All seven phases end to end | `Post: Retrospective` |

The stage bounds which phases may **start**. It never truncates the canonical
plan: `update_plan` and `autopilot-state.json` still contain Phase 0, all seven
SDD phases, and Post before any subagent is spawned, and entries outside the
range are marked per
[task-list-canonical-codex.md](./task-list-canonical-codex.md#out-of-stage-entries).

**A resolved stage MUST NOT start a phase outside its own range.** Apply the
range *before* the first-pending scan picks a row, not after:

```text
candidate_rows = Workflow Overview rows whose phase is in AUTOPILOT_STAGE's range
start = first candidate row whose status is NOT terminal
        (terminal = Complete / ✅ Complete / Skipped / ✅ Skipped / ⏭ Skipped)
if no such row  → the stage's work is already done; run its terminal step, then STOP
```

Select on **"not terminal"**, not on "pending or in progress". This is the
difference that matters. The unbounded scan takes the first row reading
`⏳ Pending` or `🔄 In Progress`, and a `⚠ Blocked` row matches **neither**
arm. After a strict-mode G6.5 stop the six planning rows are terminal and the
`Confidence Gate` row is **blocked**, so the unbounded scan skips straight past
it and lands on the implementation row — starting the very phase the gate just
refused, while the resolved stage still reads `plan`. Both halves look correct
in isolation; only the pair is wrong.

Two consequences follow directly:

- **A non-terminal `Confidence Gate` row makes the planning stage re-enter at
  the confidence gate**, because that row is inside the plan stage's range and
  is the first non-terminal row in it.
- **Crossing that boundary requires an explicit `--stage implement`.** A bare
  invocation re-resolves `plan` (the row is in the planning-complete predicate),
  and the crossing is reported rather than silent.

`--from-phase` still moves the starting point *within* the resolved stage's
range; a value outside an explicitly named stage's range is rejected at Step
0.6c before any phase work begins.

### Plan Stage: G6.5 Is The Terminal Step

G6.5 runs *after Phase 6 commits and before Phase 7 begins*, so on a
`--stage plan` run it is the last work the stage does. The run takes the
stage-boundary commit below and then **STOPs** — it does not advance to Phase 7,
in any mode. In advisory mode the gate passes or warns and the stage still ends
here; in strict mode the STOP **is** the gate resolving, and the boundary commit
is still taken so the failing verdict reaches version history.

On a strict-mode stop, write the `Confidence Gate` row to a **non-terminal**
blocked status — never to a terminal one. The row must advance off its pending
state (so the boundary commit is non-empty) while leaving the planning-complete
predicate unsatisfied (so a later bare invocation re-resolves `plan` rather than
crossing the boundary the gate refused). Record the failing verdict in a form
the gate-record matcher does **not** read as a pass: a non-terminal row sitting
beside a record that scans as a passing G6.5 is exactly the
status-versus-evidence contradiction that the Step 1.1 coverage guard and the
tree-wide CI gate both fail on.

#### Stage-boundary commit (plan stage only)

After the gate resolves — pass, warn, or strict stop — take **one distinct
commit**. It is not a renamed analyze-phase commit: that commit was already
taken before the gate ran, so renaming it would leave the verdict uncommitted.

```text
git add specs/ <workflow-file-path> <workflow-dir>/autopilot-state.json \
  && git commit -m "chore(SPEC-XXX): close the plan stage boundary"
```

Three properties, each load-bearing:

- **The message names the stage boundary, not a phase**, so the boundary is
  identifiable in version history.
- **The staged path set is the same enumeration as the per-phase bookkeeping
  commits** — the specification directory, the workflow file, and the state
  file. Never the workflow *directory*, which also holds untracked run
  byproducts that a directory-wide add would sweep in.
- **The commit is non-empty regardless of whether the `Stage` row changed**,
  because the `Confidence Gate` row always advances off its pending state — so
  the conditional second `Stage` write needs no empty-commit escape hatch.

`chore:` because a planning-stage boundary ships no runtime change and must not
trigger a release-please version bump, the same reasoning the spec-MOC
regeneration commit uses for its `docs:` subject.

#### Draft-PR emission: the terminal-step sequence (plan stage only)

Once the final gate resolves **pass or warn**, the plan stage's terminal step
does not end at the boundary commit above. It runs this sequence, in this order:

```text
1. Generate the artifacts into specs/<feature>/artifacts/.
2. Take the stage-boundary commit above.
3. Push the branch.
4. Create or refresh the draft pull request.
5. Write the `Draft PR` record to the workflow file.
6. Take a separate bookkeeping commit carrying that record, and push it.
```

**Generation runs first** because the pages land under
`specs/<feature>/artifacts/`, which the boundary commit's existing `specs/` path
already stages. The order is what lets that commit carry the artifacts with its
staged path set unchanged.

**Step 2 is the boundary commit above, not a second one.** Its message
(`chore(SPEC-XXX): close the plan stage boundary`), its staged path set, and its
non-emptiness are exactly as that subsection states them. The `Draft PR` record
is never folded into it — the record does not exist yet at step 2, and writing it
there would put a pull-request identity in the commit that closes the boundary
rather than in the commit that records the hand-off.

**The push at step 3 is load-bearing.** No earlier plan-stage step pushes the
branch, so without it creation has no remote head to open against and fails on
every run. Resolve the remote name from the checkout rather than assuming it is
named `origin`.

**The bookkeeping commit at step 6 stages the workflow file** — the only file
this step writes. Never the workflow *directory*, which also holds untracked run
byproducts that a directory-wide add would sweep in. Its message follows the
repository's conventional-commit shape, and `chore:` for the same reason the
boundary commit uses it: recording an identity ships no runtime change.

```text
git add <workflow-file-path> \
  && git commit -m "chore(SPEC-XXX): record the draft pull request"
```

**Each step is a precondition for the next, and no step is retried
automatically.** The operator re-run is the recovery path, and the two-way
existence test below is what makes that re-run safe. A failed step stops the
sequence where it failed and reports through the stop-report shape for that step.

**A re-run reaching a step whose content is already committed has nothing left to
stage there.** Such a commit is a no-op, not a failed step: the sequence
continues past the nothing-to-commit condition rather than reading it as a
failure, and it needs no empty-commit escape hatch. This does not weaken the
boundary commit's non-emptiness above, which describes what a first pass
produces — that pass's `Confidence Gate` row advances off its pending state, and
a re-run of an already-resolved stage does not repeat that advance. Treating the
resulting empty stage as a failure would strand the operator re-run that is the
only recovery path.

#### Artifact generation: the `artifact-author` dispatch

**Revalidate the established workflow binding immediately before dispatch.**
Re-run the read-only `resolve-workflow-binding` runner helper with the canonical
`WORKFLOW_FILE` established at pre-flight, invoking the helper from
`WORKFLOW_ROOT`. Require `binding_status=resolved`; require the returned
`task_root` and `workflow_root` both to equal the established `WORKFLOW_ROOT`;
require the returned `workflow_file` to equal the established `WORKFLOW_FILE`;
and require `relation=same`. Keep the original `TASK_ROOT` as immutable
discovery context, but do not compare it with the helper's cwd-derived
`task_root` during this revalidation.

Registration drift, path drift, ambiguity, external reclassification, and
sandbox denial are **not artifact-content gaps**. They are broken write-capable
handoffs, so STOP before artifact generation or pull-request refresh, write no
gap sink, and do not dispatch the author, commit, push, or mutate the pull
request. This revalidation is in addition to the startup guard: a resumed
session or operator-directed continuation must not turn a stale or bypassed
binding into a normal fail-open page outcome.

Step 1 is a single `spawn_agent` call on the installed `artifact-author` agent,
followed by a bounded `wait_agent` loop that runs until its outcome list
arrives. The agent receives the feature's planning record and the shipped
gallery, and answers with one outcome per page it wrote or could not write:

```text
spawn_agent("artifact-author", prompt="""
  WORKFLOW_ROOT: <canonical absolute worktree root>
  Use WORKFLOW_ROOT as the workdir for every shell call and as the base for
  every filesystem path. Write and return paths only inside WORKFLOW_ROOT.

  Author this feature's draft-stage gallery pages and write them into
  specs/<feature>/artifacts/.

  Inputs, all read-only:
  - Specification: specs/<feature>/spec.md
  - Plan: specs/<feature>/plan.md
  - Tasks: specs/<feature>/tasks.md
  - Design concept: docs/ai/specs/.process/<SPEC-ID>-design-concept.md
  - Gallery manifest: speckit-pro/artifact-gallery/manifest.json
  - Templates: speckit-pro/artifact-gallery/templates/<entry-id>.html

  Select, fill, and report per your agent instructions. Return one outcome
  per selected page.
""")
wait_agent(...)
```

Name the agent by its bare installed name. Codex resolves it from the installed
agent bundle, so it carries no namespace prefix.

**The orchestrator supplies no page list — the agent selects from the
manifest.** It reads `speckit-pro/artifact-gallery/manifest.json`, discards
every entry whose `stage` is not `draft-pr`, and evaluates the `trigger` on each
entry that survives. `{"always": true}` selects unconditionally.
`{"any_of": [...]}` selects only when the feature carries one or more of the
signals that entry lists.

Against today's manifest that yields the implementation-plan and spec-explainer
pages on every run, the code-approaches page under the `competing_approaches`
signal, and the module-map page under the `brownfield_change` signal. **That
sentence describes the manifest; it does not stand in for it. The manifest is
read at run time and its content governs.** The gallery grows, so a
draft-stage entry shipped later must begin routing at once, with nothing
changed here.

**Nothing is ever written into `speckit-pro/artifact-gallery/`.** The manifest
and the templates are shipped inputs, and a write into that directory is a
defect. The filled pages go to `specs/<feature>/artifacts/`, one file per
selected entry, named for that entry's manifest `id`.

**The result is a list of `generated` and `gap` outcomes**, one per selected
page, each gap naming the missing page and the reason it is missing. **A page
with any unfilled slot is a gap for that page, not a partial success** — a
partially filled page is never counted as generated. Pass the list to the three
sinks defined under fail-open below, which decide where each outcome is recorded
and which runs record it. This step supplies the outcomes and nothing more.

**A dispatch that never delivers a readable result is a whole-set gap rather
than a failed step.** An agent that errors, a bounded `wait_agent` loop that
exhausts without a result, and a reply that cannot be read as an outcome list
all land the same way: zero generated pages, and one whole-set gap carrying that
reason. The precondition rule above governs the steps that halt the sequence,
and generation is not among them, because fail-open below converts every
shortfall this step can produce into an outcome. This applies only after the
workflow-binding precondition passed; a drifted or non-executable binding never
reaches the dispatch and cannot be downgraded to a whole-set gap. Step 2 runs
regardless of content-generation outcomes.

**A truncated reply is not a clean one.** An agent that exhausts its budget
mid-summary returns a fragment, and a fragment carrying fewer than one outcome
per selected page is precisely the "cannot be read as an outcome list" case
above: it takes the whole-set gap rather than being read as far as it reached. A
partial summary is missing information, never evidence of success, and a gap
count read off one is not a measurement.

**Reconcile current-run ownership before trusting any artifact file.** Read the
manifest's `draft-pr` entry IDs after the dispatch. A complete outcome list owns
only the IDs it reports as `generated`; an error, timeout, truncated result, or
unreadable list owns none. Delete every draft-stage final `.html` whose ID lacks
a complete current-run `generated` outcome, and delete every sibling
`.artifact-author-*.tmp` file. This cleanup removes stale results from prior
runs as well as interrupted writes. After deletion, re-read the artifact
directory and require that every remaining draft-stage final ID is owned by the
complete current-run `generated` set and that no `.artifact-author-*.tmp` file
remains. A successfully removed page is ordinary fail-open gap handling. A
failed deletion or an ownership postcondition that cannot be established is an
artifact-integrity failure: STOP before staging, the boundary commit, push, or
pull-request creation or refresh, because fail-open cannot safely preserve an
unowned file.

#### The written pages are verified on disk, not taken on report

**Each outcome above asserts something about a file, and this step reads the
file.** The agent reports what it believes it wrote; a dispatch that dies partway
can leave a page on disk its own reply never named. Perform this check once the
dispatch returns and **before the boundary commit**, so nothing failing it
reaches a commit.

Two positive tests per page under `specs/<feature>/artifacts/`:

| Test | The page fails when |
| --- | --- |
| it is not its own template | the bytes match `speckit-pro/artifact-gallery/templates/<entry-id>.html` exactly |
| it is not still sample content | the body carries a sample-banner element: `class="sample-notice"`, `class="notice"`, or `class="note"` |

**The banner test reaches only templates that carry a banner.** Seven shipped
templates mark theirs, under three separate class names; the remainder carry
none. For those, byte-identity stands alone and a single byte of drift defeats
it. Neither test replaces reading the page when the outcome is in doubt.

**Failing either test makes that page a gap regardless of what the agent
reported, and the file is deleted.** Deletion is the point. Each shipped template
is a finished worked example about an invented feature, so an unfilled page is
neither empty nor visibly broken — it is a credible document describing something
else entirely. Left in place it gets committed, pushed, and linked from the
pull-request body as genuine.

After every verification-driven deletion, re-read that path and require it to
be absent. If an invalid or sample page cannot be removed, STOP before staging,
the boundary commit, push, or pull-request creation or refresh. Demoting the
outcome remains fail-open only when the invalid file is verifiably gone; a
surviving invalid file is the same artifact-integrity failure as a surviving
unowned file.

**An emptiness check cannot replace these two.** Asking whether every marked
region holds content returns yes for a page never touched, because the shipped
region content is finished prose. Both tests above are positive: they ask what
the page *is*, not what it lacks.

**Outcomes are converted here, never blocked.** A page demoted to a gap reports
through the same three sinks as any other gap, and a run where every page fails
still opens the pull request with a whole-set gap. Fail-open is untouched; what
changes is that a page indistinguishable from a template stops counting as
generated.

#### Strict-mode block: the return happens before generation

On a strict-mode block the run never enters the sequence above. The blocked-stop
contract from the two subsections above is preserved exactly: the boundary
commit is still taken, the `Confidence Gate` row is written to a **non-terminal**
blocked status, and the stage STOPs. That commit belongs to the blocked-stop
contract in its own right; it is the rest of the sequence — generation, push,
create-or-refresh, the record, the bookkeeping commit — that does not run.

**The return is placed before generation, not around it.** A blocked stage
therefore generates no artifact pages at all, pushes nothing, opens no pull
request, and writes no `Draft PR` row. Emission is not something the blocked path
fails open through; it is something the blocked path never reaches. The re-run
that resolves pass or warn is the run that emits.

#### Create or refresh: the two-way existence test

Exactly one draft pull request exists per feature branch. Before creating one,
test for an existing one **two ways**:

| Test | Source |
| --- | --- |
| the recorded identity | the workflow file's `Draft PR` row |
| the live identity | one read-only query for an **open** pull request on the head branch |

**Either positive proves one exists.** Neither test alone is sufficient, because
the record is written only after creation succeeds: a run interrupted between the
two leaves a pull request with no record, which the record test alone would read
as "none exists" and answer by opening a second one.

Take the live test as one read-only query that returns structured output, and
read the fields with a structured parser:

```text
gh pr list --head <branch> --state open --json number,url,title
```

**When either positive fires, the run refreshes rather than creates.** Refresh
the pull request's description; refresh its title as well when the title changed;
write or repair the workflow file's `Draft PR` row; and report that existing URL
as the emission outcome. Never open a second pull request for the branch.

```text
gh pr edit <number> --body-file <packet.body_file> [--title <packet.generated_title.value>]
```

**Create only when neither positive fires**, and create in draft state:

```text
gh pr create --draft --base <packet.target.base_branch> --head <packet.target.head_branch> \
  --title <packet.generated_title.value> --body-file <packet.body_file>
```

A recorded pull request that is closed or merged is a discrepancy, not grounds to
open a second one.

**A live query that cannot answer is not proof that nothing exists.** When the
query tool is absent, unauthenticated, rate-limited, or returns output that
cannot be parsed, and no `Draft PR` row is recorded either, the run has no basis
for creation. It refuses to create and reports through the could-not-be-opened
shape below, rather than risking a duplicate pull request on a branch it could
not observe.

**Self-validate the title before creation.** The title is final-shape at
creation and is not re-derived at the later ready flip:

`<type>(<lowercase-scope>): <plain English description>`

`type` is one of `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, and the
scope is **lowercase**. Validate the exact string through the release-readiness
gate's `validate-pr-title` operation before creating. The packet schema alone
would also accept an uppercase ticket-style scope; the release-readiness shape
would not, so the lowercase form is the binding one. Do **not** substitute the
`validate-pr-workflow-contract` operation that the PR packet boundary below runs
on a ready title: its scope rule upper-cases `prsg-`, `spec-`, `doc-`, and
`xplat-` slugs, so on those spec families it would demand an uppercase scope that
this lowercase requirement can never satisfy. Draft-mode title validation checks
the conventional shape only — it does not ask the description to reference
verification or evidence a draft has not produced.

**On a title that fails its self-validation, do not create the pull request.**
Report through the could-not-be-opened shape below rather than opening one whose
title a human would have to repair.

#### The draft description: exactly two blocks

The description carries exactly two blocks and nothing else:

```text
## Artifacts

| Artifact | Purpose | Open |
| --- | --- | --- |
| Implementation Plan | Lay out the phases of the planned change | `open specs/<feature>/artifacts/implementation-plan.html` |
| Spec Explainer | Explain what the feature does and why | `open specs/<feature>/artifacts/spec-explainer.html` |

## Resume

Stage: plan — stopped at the plan-stage boundary for review.
Resume with: `$speckit-autopilot <workflow-file> --stage implement`
```

- **The artifacts index** is a table of three columns: the artifact, its purpose
  in one line, and a copy-paste command that opens it locally.
- **The resume/status block** names the stage the run stopped at and the exact
  command that resumes it, in this distribution's own invocation form.

**Forbidden in a draft description**: a release-note fence, any verification
section, any scope or UAT section, and any placeholder final-writeup content. The
pull request sits in draft state, so the repository's PR checks do not run
against it — no release-note fence is needed or wanted, and a placeholder section
would read as evidence that does not exist.

**The parent session composes both blocks itself.** Emit the packet with runner
helper `pr-packet-output` in `draft` mode and pass the finished Markdown as
`inputs.body`; the producer uses that string verbatim. The `build_packet_body`
fallback stays single/split-shaped and is never reached in draft mode.

#### Fail-open: three sinks, and the runs that reach them

Artifact generation fails open. A generation failure of any size — one page,
several, or the whole set — still opens the pull request. Emission is the review
hand-off, and no generation shortfall may withhold it.

The shortfall is recorded in three sinks, so the same fact is legible wherever a
reader looks:

| Sink | What it carries |
| --- | --- |
| the artifacts index in the description | a gap-marked row in place of the artifact row |
| the plan-stage stop report | a note naming the shortfall |
| the workflow file's `Draft PR` row | the gap note that follows the link in the same cell |

**Every gap-marked row names what is missing and why** — the individual page when
a page failed, or the whole set as a single row when selection itself could not
run. A page whose marked fill regions are not all populated is a gap for that
page rather than a partial success.

**A run that produced zero artifacts still opens the pull request.** Its index
table is present under its heading and carries only gap rows. The table is never
omitted, and never left as a heading with no rows under it.

**The sink-reachability rule.** Each sink binds only the runs that reach it. A
run that stops at create-or-refresh because the recorded and live identities
disagree, or stops before creation because a step of the sequence failed, writes
no pull-request description and no `Draft PR` row — its shortfall reaches the
stop report alone. A run whose bookkeeping commit failed after creation has
written the description but not the record. In each case the unwritten sinks are
a consequence of the run not getting there, and are **not** a fail-open
violation. The stop report is the one sink every such run reaches, so it carries
the shortfall on all of them.

#### The plan-stage stop report

The stop report is what an operator reads to decide what to do next, so every
failure shape names the step that failed, the state it left behind, and the
resume path — one line of substance each, in the style Step 0.6c already uses, so
the report alone is enough to hand off.

- **Emission ran.** Carry the pull request URL, the artifact index, and the
  resume instructions.
- **The gate blocked.** Name the blocked gate in place of a URL, and say that no
  pull request was opened.
- **The pull request could not be opened.** Say so and name the step that
  refused — title self-validation, an existence query that could not answer, or
  creation itself. Note that the artifacts and the boundary commit are already
  committed on the branch, so no planning work is lost, and name the resume path.
- **The branch push failed.** Name the failed push, state that no pull request
  was opened and no `Draft PR` row was written, and name the resume path. The
  artifacts and the boundary commit sit on the local branch and nothing reached
  the remote.
- **The bookkeeping commit or its push failed after create-or-refresh.** Carry
  the pull request URL, say the `Draft PR` record did not reach the remote, and
  name the resume path. The pull request is neither closed nor recreated and the
  record is not discarded: the re-run finds the open pull request through the
  two-way existence test and repairs the record instead of opening a second one.
- **The recorded and live identities disagree.** Name which disagreement it is —
  the recorded pull request is closed or merged, it could not be found at all, or
  a different pull request is open on the branch. State that nothing was created,
  refreshed, or recorded and that the row was left exactly as found, and name the
  manual resume path for that case: reopen it yourself and re-run, or correct or
  clear the row and re-run. Carry both identities when they differ. The artifacts
  and the boundary commit are already committed and pushed, so no planning work
  is lost.

That is six shapes, and the set is closed. Every one names the step that failed,
the state it left behind, and the resume path, so an operator can act on the
report without reading the run's logs.

#### The `Draft PR` row

The pull request's identity is recorded as one scalar row keyed `Draft PR` in the
workflow file's `### Basic Information` table — the same table that carries
`Branch` and the `Stage` entry documented under
[Resume Protocol](#resume-protocol) below. The key is matched the way `Stage`
already is, and the value begins with one Markdown link whose text is the pull
request number and whose target is its URL, with an optional gap note following
in the same cell. What the emission sequence owes it:

- **Written only after creation or refresh succeeds.** Before that there is
  nothing to record. An absent row is information — it means no pull request has
  been opened for this feature — and is never reported as an error.
- **Carried by the bookkeeping commit**, never folded into the stage-boundary
  commit.
- **Repaired, not skipped.** When a pull request exists but the row is missing or
  wrong, write or repair it. That is what a run interrupted between creation and
  the record leaves behind for the next run to fix.
- **Rewritten whole from the current run's outcome, every time.** A refresh whose
  shortfall differs from the recorded one replaces the note; a refresh that
  generated every selected page leaves the cell carrying the link alone. A note
  describing an earlier run's shortfall never survives a later refresh that no
  longer fell short.
- **Left exactly as found** whenever the recorded and live identities disagree —
  the recorded pull request is closed, is unobservable, or a different pull
  request is open on the branch. A run that creates nothing and refreshes nothing
  records nothing.

**The workflow file is the only place this identity is stored — there is no
state-file mirror.** That is why this row behaves differently from the `Stage`
row that shares its table. `Stage` is workflow-file-wins over a state-file
mirror, and therefore has a write cadence and a same-edit-turn rule to keep the
two in step. Writing the `Draft PR` row neither counts against nor re-triggers
that cadence, and needs no state-file write at all: the two rows are matched by
key, so neither writer disturbs the other's value, and this identity has no
mirror to keep in step. A second sink would introduce exactly the
status-versus-evidence drift the Step 1.1 coverage guard and the tree-wide CI
gate already fail on.

#### What each corroboration status means at the terminal step

Step 0.6c classifies the recorded `Draft PR` row against one live observation and
reports one of six statuses — three ordinary, three discrepancies. Here is what
each means at create-or-refresh:

| Status | Terminal-step behaviour |
| --- | --- |
| `match` | refresh the recorded pull request's description, and its title if the title changed; report that URL |
| `no_record` | fall through to the live by-branch existence test, then create or refresh |
| `skipped` | **never create.** The present row is already a positive under the two-way existence test, so a run that could not reach the tool has not learned that no pull request exists. Refresh when the tool can be reached; otherwise report through the could-not-be-opened path |
| `pr_closed` | do not reopen, do not open a second one, leave the row as found. The stop report names the number, the URL, that **the operator** may reopen it with `gh pr reopen <number>`, and that a re-run then proceeds normally |
| `pr_missing` | do not create, do not rewrite the row. The stop report names the recorded identity and says to correct or clear the row, then re-run |
| `identity_mismatch` | do not create. The stop report names **both** identities — recorded and observed — and the manual resume path |

**`gh pr reopen` belongs to the operator, never to this sequence.** It appears
here only as prose inside a resume path. Nothing in the flow runs it, and the
stop report mentioning it grants no permission to.

**No second pull request is opened in any discrepancy class.** That invariant is
what makes each discrepancy row a stop rather than a fall-through to creation.

**All three discrepancies end the attempt at create-or-refresh** — after
generation, after the stage-boundary commit, and after the push, never earlier.
The durable discrepancy line is written at stage resolution and reaches version
history only inside a commit this stage goes on to take, so a run that stopped
before its own boundary commit would discard the record of why it stopped.

**This is fail-open.** A discrepancy does not invoke the strict-mode
blocked-stop contract, does not mark the gate blocked, and does not change the
resolved stage.

**The two reads are separate.** The observation taken at Step 0.6c and the
existence query taken before creating are different reads with the whole stage
between them. The emission-time query is the current evidence; a pull request can
be opened, closed, or replaced while the stage runs.

#### When reviewability later splits the work

A draft pull request opened here is not a throwaway. When the final reviewability
boundary later requires the work to land as more than one pull request, this
draft becomes the **first slice** of that stack rather than being closed or
superseded.

The reason is the review thread. By then the draft may already carry comments,
and replacing it would discard that conversation and make reviewers repeat
themselves. The packet identity is stable across the transition, and that
stability is what preserves the thread.

Nothing in this sequence closes, supersedes, or recreates the draft pull request.
Refresh is the only mutation it performs on an existing one.

### Implementation Stage: Read The Recorded Verdict, Do Not Re-Run The Gate

G6.5 is the **plan** stage's terminal step, so it is outside the implementation
stage's range. An `implement` invocation **MUST NOT re-run the pre-implement
confidence gate.** Re-running it would score a planning result the operator
already accepted, against artifacts that have not changed since the plan stage
committed — and under `--strict` it could refuse a boundary that was already
resolved.

Instead, read the **recorded verdict**: the `confidence_gate_status` field of
the Step 0.6c `resolve-autopilot-stage` envelope, which echoes the
`Confidence Gate` status row verbatim. Do not read it from the
`## Phase 6.5: Confidence Gate` prose record — that record's field name varies
across workflow files (`Verdict`, `Decision`, `Result`), and a bare composite
score is not a verdict at all: the same score proceeds under advisory mode and
stops under strict, so identical prose accompanies both outcomes. `null` means
no row is recorded, which is legal and is not a verdict.

**The confidence-mode flags stay accepted.** `--strict` and `--advisory` are
advertised unconditionally by both distributions' synopses, so an
implementation-stage invocation **MUST NOT reject them** — rejecting would be a
subtractive change to a shipped surface. It must instead make the flag's
inertness explicit, so an accepted flag never silently does nothing. When
`--strict` or `--advisory` is present on an `implement` invocation, emit:

```text
Stage `implement`: the pre-implement confidence gate (G6.5) belongs to the plan
stage and is not run here, so `<flag>` selects no mode for this invocation. The
recorded verdict is read from the `Confidence Gate` row instead: `<verdict>`.
```

Substitute `<flag>` with the flag as given and `<verdict>` with
`confidence_gate_status` verbatim, or the words `none recorded` when it is
`null`.

**When the recorded verdict is non-terminal, the same diagnostic names it and
says the boundary is being crossed.** A non-terminal verdict — `⚠️ Blocked`, or
any status outside the terminal set — is the state a strict-mode stop leaves
behind. Append:

```text
That verdict is non-terminal: the gate refused this boundary, and `--stage
implement` is proceeding past it.
```

Emit that sentence on **every** implementation-stage run past a non-terminal
verdict, flag or no flag. Naming the implementation stage explicitly remains
sufficient to proceed — the operator is not blocked, and no confirmation is
required. Crossing *silently* is the only thing forbidden.

### Resume Protocol

Resuming is the same protocol on both distributions, because both read the same
durable store through the same Step 0.6c operation.

**The `Stage` entry is workflow-file-wins.** The `Stage` row in the workflow
file's `### Basic Information` table is the authoritative durable store of the
resolved stage; `autopilot-state.json.stage` mirrors it for the active run only
and is never authoritative. On disagreement the workflow file wins and the
mirror is repaired from it. Absence on either side is legal — it means no run
yet, and resolves through Step 0.6c auto-detection. A two-sided disagreement is
reported by the Step 1.1 coverage guard as `stage_mirror_errors`, which is
registered in the `status-evidence` rule and so fails the guard rather than
merely printing.

Three resume forms, in order of preference:

- **Bare re-invocation** — pass the workflow file and nothing else. Step 0.6c
  re-resolves the stage from the workflow file's own status table and prints the
  basis. After a plan-stage boundary this re-resolves `plan` whenever the
  `Confidence Gate` row is non-terminal, so a refused boundary is never crossed
  by accident.
- **`--stage implement`** — the explicit crossing. Required after a strict-mode
  stop, and it reports the recorded verdict it is proceeding past rather than
  re-running the gate.
- **`--from-phase <phase>`** — moves the starting point within the resolved
  stage's range. The older `--from-phase implement` form keeps working and is
  not rejected against an auto-detected stage.

## Agent Mapping

| Phase | Agent | Prompt prefix |
| ----- | ----- | ------------- |
| Specify | `phase-executor` | `Run $speckit-specify with:` |
| Clarify | `clarify-executor` | `Prepare a Clarify Question Set for:` |
| Plan | `phase-executor` | `Run $speckit-plan with:` |
| Checklist | `checklist-executor` | `Run $speckit-checklist with:` |
| Tasks | `phase-executor` | `Run $speckit-tasks with:` |
| Analyze | `analyze-executor` | `Run $speckit-analyze with:` |
| Implement | `implement-executor` or project implementation agent | Task-specific TDD prompt |

Consensus uses `codebase-analyst`, `spec-context-analyst`, and
`domain-researcher`. `autopilot-fast-helper` is optional and never votes.

## Main Execution Loop

For each pending phase, spawn a subagent, collect the result, validate the
gate, and advance.

Every step in this loop executes against the pre-flight `WORKFLOW_ROOT`, even
when the Codex task was invoked from its parent checkout. Set that root as the
`workdir` for every shell call; invoke helpers from it; resolve every direct
read, write, state, and Git path against it; and include the exact root plus the
same directive in every executor and consensus prompt. Validate agent-returned
paths against `WORKFLOW_ROOT` before applying them. Never infer the execution
root from the task's default checkout.

```text
for phase in PHASES starting from first_pending:
    0. Re-run the all-phase coverage audit against update_plan and
       autopilot-state.json. If Archive Sweep or any canonical phase family
       is missing, STOP and repair the plan before executing this phase.
    1. update_plan: mark the current phase item as "in_progress"
       and mirror the same status change into autopilot-state.json
    2. Check .specify/extensions.yml for before_<phase> hooks
       → run accepted hooks (non-destructive), skip duplicates
    3. Read the workflow file's prompt(s) for this phase
    4. For EACH prompt in the phase:
       a. Resolve <executor>:
          use the matching installed SpecKit custom agent
       b. spawn_agent the resolved <executor>:
          "Run $speckit-<phase> with: <prompt>"
       c. Loop bounded wait_agent calls until this executor's actual summary is
          delivered; a status update or timeout alone is not the result. Record
          the summary, then close_agent only when that action is exposed. On
          hosted Responses, the host retains the inspectable completed thread.
       d. update_plan: mark this prompt's item as "completed"
       e. Write the same transition to autopilot-state.json
    5. Run consensus in main session if needed:
       Parse executor's "Unresolved for consensus" section.
       For each item → spawn the category-routed analysts (codebase-analyst,
       spec-context-analyst, domain-researcher) per Rule 7 via
       spawn_agent → bounded wait_agent loop → consume each analyst result,
       calling close_agent only when exposed and never exceeding the derived
       subagent_slots limit (dispatch in waves when items × analysts exceeds
       the cap) → apply consensus rules → edit
       artifacts → mark the corresponding Consensus item complete in both stores
    6. Check .specify/extensions.yml for after_<phase> hooks
       → run accepted hooks (non-destructive), skip duplicates
    7. Validate gate directly in the main session:
       Run 'runner helper validate-gate' for gate G<N>
       against <feature_dir> from the orchestrator using the
       resolved scripts path for this skill.
       Parse the script output for PASS/FAIL status.
    8. If gate fails:
       a. Attempt auto-fix (max 2 attempts)
       b. If still failing and gate-failure == "stop": STOP
       c. If gate-failure == "skip-and-log": log, continue
    9. Update workflow file with results and print the current checklist summary
   10. If auto-commit == "per-phase":
       For phases 1–6: run: git add specs/ <workflow-file-path> <workflow-dir>/autopilot-state.json && git commit
       (the workflow file and state file live outside specs/, so a phase that
       does not stage them by path leaves its bookkeeping uncommitted)
       For phase 7 (implement): run: git add -A && git commit
       (implementation changes include src/, tests/, etc.)
   11. Advance to next phase (next iteration of loop) and write the new
       in_progress item to both update_plan and autopilot-state.json.
       Never mark the run complete while a later phase family still has
       pending items.
```

After all 7 phases complete, proceed to the post-implementation parallel
group (see [post-implementation-codex.md](./post-implementation-codex.md)).

## Static Tier-2 Relocation Suggestion

During pre-flight, the parent may inspect the active workflow target and nearby
legacy spec candidates for Tier-2 PROCESS relocation. This is static
inspection/reporting only. The `relocate-process-artifacts` runner operation is
deferred, has no authoritative request, and is unavailable.

Report relocation candidates only for thawed in-scope legacy specs with
relocatable PROCESS artifacts. For each eligible spec, print:

```text
Tier-2 relocation candidate: specs/<spec-dir>.
Deferred: relocate-process-artifacts is unavailable; no runner command may be executed.
```

Do not advertise or invoke either runner mode and do not invent a replacement
helper. The parent must suppress the candidate report for
`frozen/in-flight`, invalid active-feature, already-current, already-normalized,
no-candidate, `non_speckit_namespace`, and `date_named_legacy_namespace`
cases. Record any surfaced suggestion or suppression note in the workflow log
before Phase 1 continues.

## Phase 3: Plan — Reviewability Budget (advisory)

After the Plan phase executor returns and `plan.md` exists (G3 pass), run the
standalone plan-phase estimator to project each slice's production-LOC footprint
from `plan.md`'s declared file structure. This is preventive sizing — it catches
an oversized slice at plan time, before any code is written. It is **advisory
only**: no outcome blocks, prompts mid-autonomous-run, or aborts the run (hard
blocking / re-slicing is PRSG-010, explicitly out of scope here).

Invoke runner helper `estimate-reviewable-loc` from the parent session with
`exec_command` and **capture the response status** rather than letting a
non-zero tool result propagate and abort the run:

```text
plan = "specs/<feature>/plan.md"
resolved_python -m speckit_pro_runner < request.json

request.json:
{
  "schema_version": "1.0",
  "request_id": "plan-reviewability-budget",
  "helper_id": "estimate-reviewable-loc",
  "operation": "estimate-reviewable-loc",
  "mode": "read_only",
  "inputs": {"plan_file": "specs/<feature>/plan.md"}
}
```

`resolved_python` is the Python 3.11+ interpreter resolved by the installed
runtime contract, not a hardcoded interpreter name.

The three budget statuses (`pass`, `over_budget`, `not_estimated`) all return
runner status `ok` with the verdict in the helper stdout JSON `status` field;
`input_error` is the error path for usage errors or an absent/unreadable
`plan.md`. Branch on the helper stdout JSON `status` when the runner response is
`ok`, and on diagnostics otherwise:

- **`pass`** → record "within budget" in the workflow/plan record and
  `autopilot-state.json` (silent — no prompt, no block).
- **`over_budget`, autonomous run** → record an over-budget note in the
  workflow/plan record and **CONTINUE** (advisory, non-blocking — FR-004,
  SC-002). Never block the run or trigger re-slicing.
- **`over_budget`, interactive use** → surface the over-budget result to the
  human as a decision (FR-005).
- **`not_estimated`** (`projected: null` — `plan.md` has no parseable declared
  production-file structure) → record "not estimated (no declared production
  files)" and continue. Never treat this as a within-budget pass.
- **diagnostic response** → record "estimator could not run" with the diagnostic code and
  continue the autonomous run.

This mirrors the Codex gate-handling pattern: read the structured runner
response and branch on it rather than aborting.
Advisory-and-never-crash is the invariant for every outcome — under-budget,
over-budget, unmeasured, or errored — none may block, prompt
mid-autonomous-run, or crash the run. If the helper is unavailable on an older
plugin build, record the diagnostic note and continue, same as any other error
path.

## Phase-Gate: Spec-MOC Navigation Regeneration

At **every phase boundary** — for all seven phases — regenerate the spec map
navigation zones and fold any change into that phase's existing checkpoint
commit. This runs as an **idempotent** step **immediately before step 10's
commit** in the Main Execution Loop above (the scoped `git add` for
phases 1–6, `git add -A && git commit` for phase 7), so the rebuilt maps are
swept into that same commit. A boundary that changes nothing contributes
nothing — no extra `update_plan` item and no `autopilot-state.json` transition
are recorded for this step.

**Why before step 10:** step 10's `git add … && git commit` is what folds the
rebuilt maps into the one checkpoint commit. Running the rebuild *after* the
commit would force a second commit on every map-affecting boundary — the
failure this ordering avoids.

**Step (run at each boundary, before step 10):**

```text
# Write mode (NO --check): regenerate over the autopilot's target repo.
# Pass "$PWD" explicitly — do NOT rely on the generator's default REPO_ROOT.
# In a cached-plugin run the default resolves to the plugin cache's parent, not
# the user's project, so the explicit arg is required.
runner helper generate-spec-index-write with repo root "$PWD" and mode apply
```

**Act on the result:**

- **Exit 2 (error)** → a map is malformed/unbalanced or a PRS manifest is
  unreadable. **Surface the actionable stderr line and STOP.** Do NOT commit a
  broken regen and do NOT advance the phase.
- **Exit 0 (clean)** → the generator wrote any stale maps and returned success.
  **The commit decision is diff-driven, not exit-code-driven** (write mode
  returns `0` whether or not it changed a file; the stale `exit 1` is
  `--check`-only and is never reached here). Inspect the working tree:
  - `git diff` (plus `git status` for newly-injected zones) is **empty** →
    nothing was regenerated. This is the idempotent no-op: contribute nothing,
    proceed to step 10's normal commit.
  - `git diff` is **non-empty** and the rebuild rides **alongside** other
    staged phase work → it is folded into that phase's existing checkpoint
    commit (`feat(SPEC-XXX): complete <phase> phase` / `feat(SPEC-XXX):
    implement phase`). No separate commit is made.
  - `git diff` is **non-empty** and the regenerated maps are the **only**
    staged change → make a standalone commit with this fixed, public-readable
    subject:

    ```text
    docs(speckit-pro): regenerate spec-MOC navigation zones
    ```

This subject is a fixed constant (it is NOT computed per run): `docs:` because
regenerating generated documentation zones is a docs-scope change and does not
trigger a release-please version bump. The regeneration is a pure function of
committed files, so re-running it on an unchanged tree yields a zero-byte diff
and no commit — exactly one rebuild contribution to the checkpoint commit on a
map-affecting boundary, and none on a no-op boundary.

## Phase 6.5: Pre-Implement Confidence Gate

After Phase 6 (Analyze) commits and before Phase 7 begins, run the optional
Pre-Implement Confidence Gate (G6.5). The synthesizer's final emit on the
workflow file (see [consensus-protocol.md §Pre-Implement Confidence Emit](../../skills/speckit-autopilot/references/consensus-protocol.md#pre-implement-confidence-emit-end-of-phase-6-analyze))
provides the data; the gate script reads it and decides whether to proceed,
surface a remediation hint, or stop.

```text
1. Read mode from `CONFIDENCE_GATE_MODE` (set at Step 0.6b in
   the autopilot SKILL.md by `resolve-confidence-mode`). The
   resolver runs once at autopilot start so `--strict --advisory`
   conflicts and unknown values fail fast before any phase work
   begins, instead of surfacing 6 phases in.

2. Resolve threshold (`confidence_threshold: 0.90`). Default: 0.90.

3. On entry, print the /goal tip:
   - Codex interactive mode: "Tip: run `/goal achieve confidence ≥<T> on
     the pre-Implement gate` to get the goal-mode iteration."
     (Requires `features.goals = true` in `~/.codex/config.toml`.)
   - Codex `codex exec` headless: "/goal is not first-class in headless
     mode per openai/codex#21764 — the 3-iteration cap is your safety
     bound."

4. Run the gate:
     'runner helper confidence-gate' \
       <workflow-file> --threshold <T> --mode <M>

5. Parse exit code + JSON:
   - exit 0 (PASS): update_plan G6.5 → completed. Advance to Phase 7.
   - exit 1 (NO_DATA): log a warning, treat as plugin regression to
     report. update_plan G6.5 → completed with `no_data: true`.
     Advance to Phase 7.
   - exit 2 (FAIL):
       a. Read JSON `criteria` object; find the lowest-scoring criterion.
       b. If iteration_count < 3:
            - spawn_agent on the appropriate analyst for the lowest
              criterion (e.g., "task_understanding" lowest →
              clarify-executor re-pass on spec.md; "risk_assessment"
              → analyze-executor re-pass on open findings;
              "completeness" → verify artifact presence).
            - spawn_agent consensus-synthesizer to re-emit the
              pre-Implement Confidence block to the workflow file.
            - Re-run confidence-gate.
            - Increment iteration_count.
       c. After max iterations OR exit 0:
            - mode=advisory: log + advance to Phase 7.
            - mode=strict: STOP. Operator may resume with
              --from-phase implement if they accept the lower score.
```

The iteration cap of 3 is the only safety bound in Codex `codex exec`
headless mode. In Codex interactive TUI with `features.goals = true`,
an operator-set `/goal` provides an additional turn-based check
layered on top of the cap.

**Why this gate is opt-in for blocking:** Clarify (G2) and Analyze
(G6) already filter most pre-Implement shakiness. Advisory mode
surfaces the score and a remediation hint without blocking; strict
opt-in via local config for operators who want a fail-closed posture.

**update_plan**: at autopilot start, after the G6 task, create a
G6.5 task `Confidence gate (pre-Implement)`. Transition through
`in_progress` → `completed` regardless of advisory vs strict outcome
(strict only differs in whether Phase 7 runs).

## Phase 7: Implement

Before `tasks.md` exists, the plan contains:

```text
Phase 7: Implement - Pending task decomposition
```

After Tasks completes, replace that placeholder with concrete task-group items
from `tasks.md`. Each implement item must include the task IDs, dependencies,
TDD protocol, `PROJECT_COMMANDS`, and `COMPLETED_TASKS` context accumulated from
earlier work.

After G5 passes, the placeholder is invalid. Before Analyze or Implement can
run, audit `update_plan` and `autopilot-state.json`, then apply the
tasks-phase reviewability boundary. Runner helper `reviewability-gate`
supports setup mode only on the installed runner — tasks mode is deferred, so
do not invoke it as an active helper. Record the deferred-mode diagnostics
(helper ID, requested mode, deferral reason) in the workflow file, then
evaluate the fallback evidence chain: the setup-mode gate result recorded at
scaffold, the plan-phase `estimate-reviewable-loc` verdict, and any
operator-ratified split decision in the workflow file. If that committed
evidence shows `pass`, `warn`, or an honored typed exception, continue. If it
shows a valid current size-only `status=block`, continue into marker
planning and later marker emission; it is not a manual re-slicing stop.
Correctness stops remain blocking: malformed/stale marker state, failed
verification, invalid packet, unsafe output, unusable gate evidence, invalid
JSON, unreadable artifacts, missing reviewability status/mode, stale
fingerprints, or any non-size safety finding.

- no `Phase 7: Implement - Pending task decomposition` item remains
- one or more concrete `Phase 7:` items exist
- each concrete item names one or more task IDs parsed from `tasks.md`

If any check fails, repair both state stores and print the corrected checklist
summary before continuing.

When reviewability evidence is marker-planning input, persist top-level
`pr_marker_plan` in `autopilot-state.json` and mirror the same schema version,
source fingerprint, fingerprint status, ordered marker IDs, review order,
checkpoints, warnings, final marker_split placeholder, packet validation
placeholder, and PR mappings placeholder in the workflow evidence. `tasks.md`
stays the task source; it is not authoritative marker state. Use repo-relative
evidence paths.

On resume, validate the marker-plan fingerprint against the current spec,
plan-declared file/test scope, tasks, reviewability evidence, and hazard route.
Missing, malformed, stale, or fingerprint-mismatched marker plans are
correctness stops at marker-required boundaries.

**Run the pull-request feedback sweep first**, ahead of the byproduct directory
below and ahead of the implementation-notes record. It reads, classifies,
records, and answers reviewer feedback on that pull request before the first
task is dispatched. It runs only when the workflow file carries a Draft PR row
whose corroboration status is `match`, **adds no row to the Workflow Overview
table**, and changes neither the phase-coverage guard's governed phase-id list,
the stage-to-phase map, nor the workflow template.

**Every path ends in the run report, and every run builds exactly one.**
Stopping or proceeding, the sweep finishes by building the report described
here, and everything below names only what its own condition contributes to it
rather than restating the shape. A run where several stopping conditions hold
builds **one** report naming every one of them, never one report per
condition. **Three parts, in this order**: the **condition**, meaning what
stopped the run or that it proceeded; **what already landed** before that,
meaning the commits pushed, the log rows written, and the replies posted so
far; and the **resume path**, one line of substance. **What already landed is
written as empty, never left out**, on a stop that happens before any write,
because an absent part reads as an oversight while "no commit, no row, no
reply" reads as a fact an operator can act on.

**The what-already-landed part also carries one outcome line per page**, each
reading `generated`, `gap`, or `removed`, with every gap naming what was
missing and why. These lines extend that part's enumeration once, here in the
shared shape rather than in the amended leg of the stop-or-proceed rule below,
because the freshness evaluation runs on every leg and an extension made there
alone would miss the recovery leg entirely.

**Two run-level lines sit beside them**: the regeneration commit's short sha,
and the outcome of the description refresh. A failure's manual resume path
belongs to the resume path part instead, never to these lines. Any restoration
the run performed is a further run-level line beside the commit sha, and is not
a fourth page outcome.

**On a sweep that amended nothing and found the pages already current, the
freshness contribution collapses to a single line** naming the commit the pages
are current as of, with no per-page outcome list. That collapse scopes the
freshness lines alone; the report's other mandatory parts are unchanged.

**When the verdict is `current` and `last_artifacts_commit` is null, the same
line names no commit** and instead says the pages are current with no artifacts
commit and no `amended` row to join against. A present directory that no commit
has ever touched reaches `current` legitimately whenever the log carries no
`amended` row, and a line required to name a commit would have to invent one.

**Every shortfall regeneration produces still reaches the reused machinery's
three sinks**: the description's gap rows, the `Draft PR` row's note, and the
run report. One substitution is named explicitly. At this Phase 7 call site the
third sink is the **run report**, on both the stop and the proceed legs,
because the plan-stage stop report the shipped sink table names does not exist
here.

**The two gap shapes are reported apart, because they differ in repairability
rather than in severity.**

| Shortfall | The directory | The commit | The next leg |
| --- | --- | --- | --- |
| per-page gap beside a generated page | moved | taken | does not retry; the gap is the operator's |
| whole-set gap | unmoved | not taken | regenerates the set again |
| deselection removal landing alone | moved | taken | does not retry; the report names the removal as the reason |

A report calling the first two both "gap" and stopping there would leave an
operator unable to tell work that will be retried from work that will not.

**Every removal is named, and none is silent.** A deselection removal is named
as its own `removed` outcome; the superseded file behind a per-page gap is
named inside that page's own `gap` outcome, as step 3b below requires.

**A failed description refresh is its own outcome**, distinct from the
regeneration outcome. The report states in as many words that once the
regeneration commit has landed, a re-run does **not** retry the failed refresh:
the join then reads the artifacts directory as current, so a later sweep
regenerates nothing and refreshes nothing. It names the operator's manual
resume path, and the resume path part below names which one.

**An `undeterminable` verdict is reported and acted on nowhere else.** It
triggers no regeneration, no refresh, and no commit, and it moves the
stop-or-proceed decision in neither direction — on a sweep that amended, the
re-review stop still fires on its own independent ground. The report names the
verdict, each affected row's `#` and its reason, and the operator's manual
resume path, through the run report **alone**: the three sinks do not apply,
because no regeneration occurred to produce a shortfall for them to carry.
Nothing in scope can ever clear the condition, since this slice writes no log
row and permits no second store, so an action keyed to it would repeat on every
later clean sweep without end.

**A failed record commit, or a failed push of it, is reported through the
refresh outcome and never blocks the run.** The report **must not** claim the
row repairs itself on a later sweep. The machinery's repair rule recovers an
unwritten row only on a later refresh that reaches that step, and no later
sweep reaches it once the regeneration commit has landed. Its resume path is
named the way a failed refresh's is: the pull request is correct on the remote
and only the record is unwritten, so the row is repaired by hand, or by a later
run reaching the plan-stage create-or-refresh step, which this slice never
schedules.

**The per-comment dispositions sit inside that one report.** Report each
observed comment, candidate and exclusion alike, and name a reason on every
exclusion: the trust filter reports `not swept: untrusted author`, and every
self-reply exclusion is named the same way. The proceed path is exactly where
a run that swept nothing but untrusted comments lands, and a silent proceed
there would leave an operator no way to tell it from a run that saw nothing.
**A run that observed no comment at all reports that**, as a one-line report
rather than an absent one. **Every redaction event goes in, on every path,
stopping or proceeding**: per affected comment the comment id, the leg, the
rule, and the count, and nothing else about the match. **The report names the
sweep's byproduct directory as removed, on every path**, and it **goes to the
operator's sink**, the one the plan-stage stop report reaches, and never to
the pull request.

**That one-line characterization belongs to the per-comment dispositions that
paragraph is about**: a run seeing no comment still says so in one line instead
of omitting the part. The freshness evaluation contributes its own lines to the
what-already-landed part on that same leg, so a report there is one line of
dispositions plus however many lines the freshness outcome requires. Reading
the shipped sentence as a promise about the whole report would also conflict
with the restoration line above, which lands in that same part on a leg that
generated nothing. This adds no member to either enumeration and changes no
report part's contents.

**The conditions that end a run in this sequence** are an invalid
authenticated account, a corroboration status that is neither `match` nor
`no_record` or one outside the six, a failed observation, an unreadable
Feedback Sweep Log row, a malformed classifier or analyst record, a resolved
edit target outside the three artifacts, a failed push, a consensus outcome
requiring human review, one or more amendments requiring re-review, and one or
more redaction events reported once every write landed, the last two being the
only ones that are not failures. **One condition needs more than the shared
shape**: the human-review stop's resume path names **both** operator actions,
resolve the substance and re-run **or** resolve the thread, because it is the
only stop whose resume path a re-run alone does not satisfy.

**The failed push in that list is the amendment push above.** The regeneration
sequence's own artifacts push ends the run only on the leg that amended; on the
leg that amended nothing it is reported and the run proceeds, so it is not
among the conditions this list names. Which push the member means is all that
is settled here, and the members themselves stand as written.

**A failed description refresh names its resume path per stopping status**, one
line per status rather than one shared line, for the reason the corroboration
gate below already gives: the stopping statuses have different fixes, and one
shared path would send an operator to the wrong repair. `skipped` names fixing
the tool. `pr_closed` names reopening the pull request. `pr_missing` names
correcting or clearing the `Draft PR` row. A refresh that failed against a
reachable pull request names refreshing the description directly, outside the
automated sequence. Neither `pr_closed` nor `pr_missing` is repaired by
refreshing a description, which is why the generic path may not stand in for
them. Where the failure traces to the recorded and live identities disagreeing,
the report names **both** identities, the one recorded and the one observed.

**The six corroboration statuses are exhaustive, and each maps to exactly one
outcome.** Step 0.6c classifies the recorded `Draft PR` row and reports one of
them, and the sweep reads that report rather than taking an observation of its
own. No status falls to a default, and no two share a behaviour by accident.

**That reading scopes the entry gate's sweep-or-not decision alone**, the one
decision Step 0.6c's pre-phase observation was taken for. It does not forbid
the refresh's own live observation deeper inside Phase 7, which is taken only
after this gate has passed and the run has reached the refresh step of the
regeneration sequence below. **That condition is the sequence, not the
classifications.** The stale-recovery leg reaches the same refresh having
amended nothing, so scoping the observation to a leg that amended would let an
orchestrator skip it on exactly the runs the recovery path exists for. Nor is
that a new kind of observation: the create-or-refresh terminal step above already takes a
second live read distinct from Step 0.6c's, on the documented principle that
the two reads are separate and the later one is the current evidence.

| Status | What the sweep does | Resume path |
| --- | --- | --- |
| `match` | sweep | none, the run proceeds |
| `no_record` | proceed without sweeping | none, the run proceeds |
| `skipped` | stop | fix the tool, then re-run |
| `pr_closed` | stop | reopen the pull request, or clear the `Draft PR` row if the checkpoint is genuinely abandoned, then re-run |
| `pr_missing` | stop | clear the row, then re-run |
| `identity_mismatch` | stop | correct the row to name the right pull request, then re-run |

**Each stopping status names its own resume path**, because the four have
different fixes and one shared path would send an operator to the wrong repair.
**Clearing the row belongs to `pr_missing` alone**: it is the one status where
the row's absence would match reality. **The sweep never writes the `Draft PR`
row on any path**, these four stops included, because a run that repaired the
record it had just failed to corroborate would destroy the evidence of the
discrepancy and leave the next reader a healthy row where a stop had been. **A
value outside the six is a malformed record and stops**, never mapped onto one
of the six and never read as absence: exactly one status proceeds, so a default
that proceeded would make a corrupted record the cheapest way past the
checkpoint.

**That invariant is about the sweep's own writes.** The description refresh
below changes the `Draft PR` cell through the emission machinery, which keeps
exactly one writer; this slice supplies only the trigger and the timing, and
the commit carrying that change is the machinery's own record commit. Its
ground stands unchanged: the sentence exists so a run cannot repair a record it
just failed to corroborate, and the refresh is reached only after an entry-gate
`match`.

**`skipped` and `no_record` are different readings and never interchangeable.**
`no_record` means the gate **does not apply**: no draft pull request was ever
opened, so there is no checkpoint to carry unread feedback, and the run
proceeds. `skipped` means the gate **applies and could not be evaluated**: a row
is recorded and the observation behind it failed, so the run stops. Treating
"could not observe" as "observed nothing" would make the checkpoint silently
optional exactly when the tool is unreliable, which is when unread feedback is
most likely to be sitting on the pull request. **A tool that was absent,
unauthenticated, rate-limited, or that returned output which could not be parsed
is not evidence that a recorded pull request is gone**: those four are the
causes of a `skipped`, and not one of them observed anything about the pull
request.

**The `skipped` report must read differently from the three discrepancy stops,
and must name which of the four causes occurred**: the tool was absent, the tool
was unauthenticated, the tool was rate-limited, or the tool returned output that
could not be parsed. Those three stops observed something and this one observed
nothing, so a report that read the same would tell an operator the record is
wrong when the record may be perfectly correct. **Behaviour does not branch on
the cause; only the report does**, so all four take the same stop and the same
resume path. **Clearing the `Draft PR` row is not a resume path here**: that
belongs to `pr_missing`, and reusing it for a `skipped` would erase a
probably-true record to manufacture a `no_record` reading on the next run.

**Every one of these paths reports.** A gate stop's condition is the status
and, for `skipped`, its cause. Nothing landed, because the gate is evaluated
ahead of the first read and therefore ahead of every write. The resume path is
the one the table above gives.

**Read the authenticated account from the live session, at call time.** The
sweep excludes the replies it posted itself, and that rule's author half
compares against the account this run authenticated as, which is the parse's
`self_login` input. Read it from the live authenticated session at the moment
of the call: never from configuration, a project setting, or a value remembered
earlier in the run. That is the same freshness the author-association field
below requires.

**Two reads, and only two**, both `gh api` reads. Read **every review thread
whose resolved flag is false** and **every pull-request conversation comment**,
never review summary bodies. **Paginate both to exhaustion**, following the
cursor until the surface reports no further page, and request the
**`authorAssociation`** field explicitly on both. **No comment text reaches a
shell argument in either direction**: a read passes its query by file or by
structured argument, a write passes its body by file path.

**Pipe the observation straight into the runner.** The reads' output reaches
`sweep-pr-feedback` on stdin, `gh ... | resolved_python -m speckit_pro_runner`,
the request envelope wrapped around the read rather than around a file, so **no
unredacted body is written to disk at any point**. Where a byproduct file is
unavoidable it goes under `specs/<feature>/.process/feedback-sweep/` and
nowhere else, the directory the next paragraph describes, where the reply
bodies already live.

**The two reads are one observation, taken all or nothing**, succeeding only
when both surfaces have been read to exhaustion. Three failures fall under the
rule: one surface readable and the other not, a page failing partway through
pagination, and output that cannot be parsed. **A failed observation is
discarded rather than swept**: the partial data does not reach classification,
the run writes zero log rows, posts zero replies, takes zero commits, and
stops. Nothing needs unwinding, because every read precedes every write.

**The mid-read failure report is not the gate stop, and must not read like
it.** It draws on the same four causes the gate's `skipped` draws on: the tool
was absent, the tool was unauthenticated, the tool was rate-limited, or the tool
returned output that could not be parsed. So the report **also names that
reading had begun** and **which surface failed**, because an operator who cannot
tell a gate failure from a mid-read failure cannot tell whether the pull request
was ever reachable. Nothing landed, for the same reason nothing landed at the
gate: every read precedes every write. The resume path is the same as the
gate's `skipped`, fix the tool and re-run, and needs no repair step first,
because the observation is retaken fresh on every invocation.

**One classifier per candidate, and no body read.** The parse returns
`candidates` and `excluded`; a candidate record carries the comment id,
surface, author, association, truncation flag, and export metadata, and **no
body**. Iterate `candidates` and nothing else, so no path enumerates the
observation directly. For each candidate whose export kind is not `empty`, make
**exactly one** `spawn_agent` call on `sweep-classifier`, handed the sanitized
delimited block the piped call already returned for that candidate, the closed
class vocabulary, the three-file target set, and nothing else. An `empty`
export kind is never dispatched: that form carries no objections and takes `no
action` from the parse alone.

**The parent session reads no comment body on any path.** It is a conduit for a
block, handing each one to the classifier unchanged and, for an amended item,
to the analysts. It keeps its shell and could run the read for itself, so the
control is that a body is never handed to it: construction rather than
enforcement. What comes back is the structured record
`contracts/sweep-classifier-output.md` fixes: the echoed comment id, the class,
the target, and a bounded reason. Consume those and nothing else. Pass the
reason through the redaction surface's `log_row` leg **before** it reaches a
cell, a reply, or the run report, and carry the string that leg returns rather
than the parent session's own copy. A record carrying a class outside the set,
a target outside the three artifacts, or a missing field is **malformed**: stop
the run naming that comment id, no coercion onto a class and no re-prompt.

**The dispatch lives here, not in the routing table.** It emits no category
tag, produces no `Unresolved for consensus` item, and never consults
`consensus-protocol.md`'s Category-Routed Dispatch table or the three
phase-specific flows under it, which leaves Clarify, Checklist, and Analyze
exactly as they were.

**The vocabulary the dispatch hands over** is the closed class set `amended`,
`answered`, `deferred`, and `no action`, and the classifier returns exactly one
of the four. The **comment** is the unit, so a recognized export carrying
several distinct objections still yields one class, one log row, and one reply.
Recognition never forces a class; the empty-export form above is the one
exception. The rules for choosing among the four, including the tie-break and
the naming of every non-dominant objection, are stated once in the classifier's
own definition, which this reference points at rather than restating, so the
two cannot drift.

**A target outside the three artifacts takes `deferred` at classification**,
which is rule 1, the disposition half of a pair. A comment whose requested
change lies outside `spec.md`, `plan.md`, and `tasks.md` in the feature
directory is declined, so its class is `deferred` and its bounded reason
**names the refused target**, which is what carries that name into the
disposition cell and into the reply. The refused path travels in the reason and
never in the record's `target` field, which the malformed-record rule above
confines to the three artifacts. Word the disposition and the reply as
**recorded and not acted on**, and let neither **imply future action**: the
class name reads like a queue, and the request is declined rather than
scheduled. The rule for choosing among the four classes stays in the
classifier's own definition; what this sequence fixes is what a `deferred`
reached this way has to carry. **Rule 1 is disposition and rule 2, at the write
point below, is the enforcement boundary**, and neither substitutes for the
other: rule 1 alone would be prose a mis-routed item walks past, and rule 2
alone would turn an ordinary out-of-scope request into a stopped run when
declining it in a reply is the whole of the correct response.

**The recognized-export payload** is two parts side by side: the helper's
export record, carrying the template id, the kind, and the anchors, and the
block, the body with every line the parse named in `matched_lines` replaced in
place by `[registered export lead removed]`. The record stands **beside** the
block, never inside it; the remainder is delimited and labelled as
reviewer-supplied data, never concatenated into the prompt as instruction. A
registry entry that only tags the comment while the raw body still reaches the
agent does not satisfy this. **The removal is the redaction surface's work, not
this reference's**: hand the surface the parse's `matched_lines` for that
comment and forward the block it returns **unchanged**. Delimiting is the
strongest layer available inside a prompt and removal is defence in depth; both
are model-layer controls, nothing deterministic stands behind them on the
forward path, so neither relaxes the author-association filter, and if cost
forces one out, removal goes and delimiting stays.

**The work set shrinks or holds, and never grows.** A run's **work set** is the
comments that pass the trust filter, are absent from the Feedback Sweep Log,
and are not excluded as the sweep's own replies. Every run either shrinks that
set or leaves it unchanged; **no run may grow it**, which is what makes the
loop terminate, and any future rule that writes to either comment surface has
to be tested against it, because a rule that adds an unexcluded comment breaks
convergence however reasonable it looks on its own. One path does not shrink
the set: a comment whose consensus round returns a human-review outcome takes
no class and writes no row, so it is in the set again on the next run and stops
that run too. The set does not grow, so this is not divergence. That path is
bounded by a human rather than by a counter, and **no attempt counter is
introduced**: a per-comment counter would need the state-file mirror the log
rules forbid.

**Only `amended` routes into consensus.** `answered`, `deferred`, and `no
action` never invoke it: those three are complete at classification, and a
consensus round on any of them would spend four calls confirming a disposition
already reached. **The sweep runs its own consensus.** Per amended item make
**three** `spawn_agent` calls on `sweep-analyst`, the perspective (codebase,
spec-context, domain) given **in the prompt rather than by role**, then **one
more** `sweep-analyst` call in a synthesis prompt: four calls per item, all to
the same definition. **Await all three before the synthesis call**, which
reasons over the three answers together, and **apply the one structured edit
it returns** by the amendment path below.

**Synthesis is not `consensus-synthesizer`.** That agent declares no `tools:`
allowlist, so it inherits a shell, web fetch, web search, and every installed
MCP server; routing sanitized reviewer text into it would reopen, one hop
downstream, the exposure the classifier call above exists to close.
`sweep-analyst` carries a closed read-only allowlist instead, which is also why
**the domain perspective runs without web access**: it reasons from the
repository and the handed block, never from the network.

**What stays untouched is the routing table, not the file that holds it.** The
sweep emits no category-tagged `Unresolved for consensus` item, so the routing
table and the three phase-specific flows under it are never reached and
Clarify, Checklist, and Analyze keep the shared analysts and those flows
unchanged. This slice does edit `consensus-protocol.md`, to add the `Sweep`
row type and the note that its rows count toward the escape-rate metric, and
those two are the only edits this feature makes to that file, so say routing
table untouched and never say that file untouched.

**When consensus does not answer, the item goes to human review.** Three ways
lead there: all three analysts disagreeing after Round 2, a Round-1 escape
whose Round 2 still cannot resolve, and an analyst that fails its single retry.
All three land on one behavior; only the report names which occurred. **No
edit, no class, no sweep row**: `amended` would assert an edit nobody resolved
and the other three a disposition nobody reached. Writing no Feedback Sweep Log
row is the load-bearing part, because the skip key is that log's comment-id
column and nothing else, so the absent row is what makes the comment a
candidate again once a human has resolved it; a row here would record the
sweep's own failure as the comment's disposition and make it permanent.

**It surfaces as one Consensus Resolution Log row instead**, `Type` `Sweep`,
its item cell naming the comment id, and that row **counts** toward the Round-2
escape-rate metric. That log feeds no skip key, so a row there costs no
idempotency. **It stops the run whether or not anything was amended**, because
a run whose only unresolved item took no class would otherwise read as nothing
to act on and walk into task work; when other items amended in the same run,
the re-review stop and this one are the same stop and one report, not two.
**Other items in the batch still complete**: items that resolved are edited,
committed, recorded, and replied to normally, and the run stops after that.

**One commit per amendment, never one run-wide commit.** A log row names its
commit, an `amended` reply names the amending commit, and the re-review stop
reports a commit range, and none of the three survives collapsing every
amendment into a single blob. **Each amendment commit stages exactly the one
artifact path it amended, never a directory**, so no stray file rides along.
The subject is fixed in shape and carries no body:

```text
docs(<feature-id>): amend <artifact> for <comment-id>
```

The scope is the feature's roadmap id in lowercase, `<artifact>` is one of the
three artifacts, and `<comment-id>` is the observation's id for the comment
being amended. Every slot is an id or an enum, so no byte from a comment or
from a resolution reaches `git log`, and the subject is **not a redaction
leg**; the shape also satisfies the release-readiness title regex. **The hazard
to watch: this is a Phase 7 setup step, and Phase 7 is the one phase whose
existing commit path uses `git add -A`.** An amendment commit that inherited
that pattern would stage the whole worktree and defeat the edit-surface
allowlist at the last step, so name the one path.

**What the synthesis returns is a record, not a patch.** An analyst answers
with `{file, anchor, replacement}` and nothing else: never a diff, never a
patch, and never prose the parent session retypes into the artifact. `file` is
one of the three allowed names, and `replacement` sits inside the contract's
cap. An edit whose `file` falls outside those three names, or whose shape is
not that record, **stops the run naming the comment id**, the same way a
malformed classifier record does. **The order of the three steps is fixed:
allowlist check, redaction, write.** Check the resolved target first, pass
`replacement` through the redaction surface's `amendment` leg second, write
what the surface returned third, then stage that one path, commit, and push.
The order is not a preference: redacting after the write leaves reviewer bytes
in a commit, and checking the target after the write is not a check.

**The write point checks the resolved target before any amendment write**, as a
named surface of the one registered helper operation and never a second
registered operation. **A refusal is a verdict, not a diagnostic**:
`allowed: false` is a successful read of that surface rather than an error from
it, the surface answers and the stop belongs to the parent session, and the
answer carries a `reason` that is either null or one of `outside_set`,
`symlink_target`, and `symlink_parent`. **A refused target stops the run**: its
condition names the **refused target path** and the **comment id it came
from**, and its resume path is to fix the classification and re-run.
**Reaching this check means classification already failed**, so it is a defect
report and not a routine path, which is why it stops rather than downgrading
the item quietly.

**The amendment leg runs between the check and the write.** Once consensus has
resolved the edit and the target check has passed, the text the edit
**introduces**, meaning the replacement or the inserted lines, goes through the
redaction surface's `amendment` leg: never the file around it, and never a diff
read back off disk. The parent session then writes back **exactly what the leg
returned**, stages the one artifact path, commits, and pushes. No staged path
list is read back afterwards, so single-path staging and the `git add -A`
hazard named above stay the controls on what an amendment commit stages. **Cut
each line for transport at the first character boundary at or past byte 8193.**
The surface answers a line longer than 8192 bytes with the whole-line
placeholder whatever lies past that boundary, so sending the tail buys nothing;
cutting there is outcome-equivalent, keeps every string the call carries under
the runner's 32 KiB limit, and **never splits a line**, because the cut falls
on a character boundary and one line in stays one line out.

**The push is part of the amendment step, not a step after it**: an amendment
is not finished until its commit is on the remote. **A commit that succeeded
whose push failed stops the run immediately, before that amendment's
bookkeeping commit**, naming the unpushed commit's sha and the comment id.
Ordering does the work: the bookkeeping commit already comes after the
amendment's own commit, so stopping between them writes no log row, and because
replies wait on bookkeeping commits landing, it posts no reply. **The local
commit stands and is not unwound**, because the edit is correct work that
consensus resolved; with no row written the skip key does not see the comment,
so it is a candidate again on the next run. **A bookkeeping commit whose push
fails stops the run the same way**, differing in one consequence: its row is
already in the local workflow file which the sweep reads locally, so the skip
key **does** see the comment, and the reply is what would otherwise be lost,
recovered by reply reconciliation against the pull request. **No automatic
retry on either push**, because retrying inside the run would multiply the
window the per-amendment cadence exists to bound.

**Log writes ride a separate bookkeeping commit and are never folded into an
amendment commit.** The ordering is forced rather than stylistic: a row that
names its commit cannot exist until that commit's sha does. The bookkeeping
commit **stages the workflow file path alone, never the directory, and takes a
`chore:` subject**. **The trigger is rows, not handled comments**: a run takes
one when it wrote at least one row to **either** log, and takes none when it
wrote none. Three consequences follow.

- A run with zero amendments but at least one handled comment takes exactly
  one, carrying every `answered`, `deferred`, and `no action` row.
- A run that handles no comment but must write Consensus Resolution Log rows
  also takes exactly one, carrying every such row.
- A run that wrote no row to either log takes none. An empty commit there would
  record nothing.

**One bookkeeping commit per amendment, not per run**, which bounds the window
in which an amendment is pushed but unrecorded to a single item.

**The redaction surface has four legs and the set is closed at four**:
`amendment`, `log_row`, and `reply` outbound, and `analyst_payload` inbound.
Anything outside the four returns `invalid_input`. A fifth leg is code this
feature does not budget for.

**The `log_row` leg runs over every cell the sweep fills with prose** rather
than with an id, an enum, a sha, or a count: the Feedback Sweep Log
`Disposition` cell, the disposition text of the Consensus Resolution Log rows
the sweep writes, and those rows' item cell, which names the comment id and
then summarizes the item in prose the way every shipped row does. **One call
per cell**, so an amended item makes three calls on this leg, a human-review
item two, and any other class one. The classifier's bounded reason, which is
what becomes the disposition, is capped at 512 bytes and carries neither a pipe
nor a newline, because the readers of these tables split cells on the bare
pipe. **The `log_row` call comes before the pipe and newline escaping, never
after**, and the placeholder the surface writes contains neither character, so
escaping never splits a placeholder and `CRL #` stays in its column.

**Capture each `log_row` response at the call, before escaping.** Captured
after escaping, the identity assertion downstream compares the wrong pair and
passes on a run report the parent session built from its own pre-call copy. The
order is: call the leg, capture what it returned, then escape the captured
string on its way into the cell.

**The `reply` leg runs over the filled reply body, marker included**, before
that body is written to the file the reply write passes by path. The marker
stands alone on line 1, no rule's trigger appears on that line, and neither
line-granularity rule reaches a line ahead of its own: the bound replaces only
the line it measured, and the key-header span runs forward from its own header
line. The self-reply anchor therefore survives, and an over-bound disposition
costs line 2 onward and never the marker.

**Never the matched line**, an excerpt of it, a redacted or truncated copy, or
any encoded form, whether in the report, a log row, a reply, or the surface's
own response. The report carries an event exactly as the builder above names
it, and nothing more. The disposition it carries per comment is the `log_row`
response for that comment's `Disposition` cell, before escaping, never the
parent session's copy from before the call.

**Redaction never refuses a write and never discards a row.** A run with no
amendment batches every row it wrote into one bookkeeping commit, so a refused
commit would discard them all, and the next run would regenerate the same
disposition and refuse again: a livelock on ordinary reviewer input. **A run
with any event stops once every write has landed**, after the last push and the
last reply, with resume path re-run; the next run finds the rows and the
replies already in place, fires no event, and proceeds.

**Exactly one reply per handled comment**, posted after a run's bookkeeping
commits have all landed, and **every reply names its class**. Only an `amended`
reply names an artifact, a section, and a commit: requiring those three of all
four classes would leave three of the four templates unsatisfiable, because
`answered`, `deferred`, and `no action` amend nothing. **One fixed template per
class, in plain public-readable English**, fixed in shape so a reviewer reading
two replies on one pull request can tell the classes apart at a glance.

**Every template opens with an HTML comment whose prefix is the same fixed
string in every reply**, `<!-- speckit-pro:feedback-sweep`, followed by the
answered comment's id and the closing `-->`. It renders as nothing and is what
the self-reply exclusion anchors on: a marker rather than a visible sentence,
because a visible sentence is exactly what a reviewer quotes back when they
disagree. **The marker is the whole of line 1, alone, and the disposition
starts on line 2**, and nothing else shares that line, which is what keeps the
per-line redaction rules off it, as the reply leg above already relies on.

**One more fixed-shape line is the last line of every template**, present only
when the parse reported the comment `truncated` or its analyst-payload report
carries `spans_withheld` above zero:

```text
Body truncated at 8192 bytes; N spans withheld.
```

`N` is that count, and nothing else appears in the line. This is the channel
that tells a reviewer their fence or their tail was never read: the pull
request is where a reviewer learns what happened to their comment, and the
disposition cell lives in a file they need not open.

**Two write paths, one per surface.** A reply to a review-thread comment posts
**into its thread**; the pull-request conversation has no threading, so a reply
there is a **new top-level comment that names the comment it answers**. **Every
reply body is passed by file path, never inline**, on both paths.

**Replies post once, at the end of the run, after every bookkeeping commit this
run takes has landed**, and no reply is posted before that point. Two orders
are defensible and only one may be written down, so this is the one: a reply
asserts that the record behind it is durable. The rule also makes the composed
interrupt case exact rather than ambiguous, in that a run interrupted after two
rows were written, with one amendment commit local and unpushed, has posted
**zero** replies. **Which stops post replies is named rather than inferred**:
the re-review stop, the human-review stop, and the post-publication redaction
stop all occur **after** the reply point, so a run that reaches any of them has
already posted every reply it owes, and **every other stop aborts before the
reply point and posts none**, those being an invalid authenticated account, a
corroboration failure, a failed observation, an unreadable log row, a refused
edit target, and a failed push. Never write a blanket rule that a stopping run
first posts what it owes, which would contradict all six.

**The failed push named among those six is the amendment push above.** The
regeneration sequence's artifacts push is not one of them, because it happens
after the reply point, and its own stop belongs on the after-reply-point side
beside the three named there: a run that reaches it has already posted every
reply it owes. Saying where that stop falls settles nothing about either list's
membership, which stands as written.

**The sweep never resolves a review thread.** Not on any class, not on any
path, and not after a reply: resolution is the reviewer's, and a swept thread
stays open until they close it.

**Replies are reconciled against the pull request, not assumed from the log.**
A comment is owed a reply when three things hold together: it is **present in
this run's observation**, it has a log row, and it carries no sweep reply
answering it. **The observation qualifier is load-bearing**, because keying on
log rows alone would post a second reply into a thread someone had deliberately
resolved, which turns a recovery rule into a duplicate-reply generator. **The
marker carries the answered comment's id** after its unchanged fixed prefix,
inside the same HTML comment, so a thread carrying more than one comment still
says which one a reply answered; matching the prefix alone would find a reply
and lose the question. **A failed reply is reported and does not by itself stop
the run**, appearing in the run report with the comment id and the surface. The
asymmetry with a failed observation is deliberate: an observation that failed
means the work never happened, while a reply that failed means the work landed
and only the notification did not.

**Evaluate the freshness verdict before deciding anything else here.** Ask the
`check-artifact-freshness` runner helper's `verdict` surface for one verdict
over the feature's pages, its request reaching `resolved_python -m
speckit_pro_runner` on stdin the way every helper call in this sweep already
does. Supply the workflow file and the artifacts observation the parent
session gathered: the directory state, the last commit touching
`specs/<feature>/artifacts/`, the on-disk page inventory by filename stem, and
one ancestry record per `amended` row, keyed by that row's `Commit` cell text
verbatim. **The verdict joins on those supplied records, never on page bytes.**
The pages are agent-authored prose, so identical inputs produce different bytes
and a content comparison would read every page as stale on every run.

**When the artifacts directory has never been committed, pin the ancestry field
to `false` rather than leaving it null.** With `last_artifacts_commit` null
there is no commit for an amended row to be an ancestor of, so every row that
resolved is supplied as
`{"resolved": true, "is_ancestor_of_artifacts_commit": false}`. The helper
tests that field for the literal `false` and has no branch of its own for this
case, so a `null` or an omitted field reads as *not stale* and the run leaves
the pages alone. That is the interrupted-run case exactly — pages written and
never committed — and getting it wrong puts the pre-amendment plan back in
front of the re-reviewer, which is the outcome this whole sequence exists to
prevent.

**The helper now refuses that mistake rather than acting on it**, and refuses
the rest of the observation's declared shapes with it: `pages` that is not an
array of strings, a non-array `amended_commits`, a record whose `cell` is not a
string or whose `resolved` is not a boolean, a resolved record without a boolean
ancestry field, and an unresolved record carrying a non-null one. Each returns
exit 2 with a one-line diagnostic naming the offending field. **That refusal is
scoped to an observation that reported success**, so nothing here weakens the
rule below it: an observation whose `ok` is short of the literal `true` is a
failed gather, still yields `undeterminable`, and still never blocks the run.
Treat an exit 2 here as the orchestrator's own defect and fix the gather; do not
retry it and do not route it into the report as a freshness outcome.

**On `stale`, regenerate through the installed `artifact-author` agent**, and
run the rest of the sequence:

```text
0. The reply point above: every reply this run owes is already posted.
1. Evaluate freshness through the `verdict` surface.
2. On `stale`, one `spawn_agent` call on `artifact-author` against the amended
   planning record, then a bounded `wait_agent` loop until its outcome list
   arrives.
3. Compute the removal set through the `removal_diff` surface, and delete
   those files.
3b. Delete the superseded file behind each per-page gap. Skipped entirely on
    a whole-set gap.
4. Verify the written pages on disk, through the two positive tests above.
5. Commit specs/<feature>/artifacts/ alone, with the docs type.
6. Push. A failed push ends the sequence there.
7. Take the refresh call site's own live observation, and classify it.
8. Refresh the description through create or refresh.
9. When the `Draft PR` cell actually changed, take the record commit.
```

**Name the agent by its bare installed name**, exactly as the plan-stage
dispatch above does, and hand it the same inputs: the feature's planning
record and the shipped gallery. Codex resolves it from the installed agent
bundle, so it carries no namespace prefix.

**Step 0 is a placement, not a new step.** The whole sequence runs after the
reply point above, so every reply the run owes is already posted before step 6,
this sequence's first new failure point. That is what leaves the reply
behaviour above literally unchanged. The placement had to be chosen rather than
inherited: neither commit this sequence takes is a bookkeeping commit, so the
reply point's own rule places neither of them.

**Re-selection reads the shipped gallery manifest against the amended record**,
never the page list the previous run happened to produce. A run that
regenerates decides its page set the same way a first generation does.

**Every selected page is authored fresh.** No page is patched, diffed, or
partially updated, and this slice introduces no second page-authoring path: the
dispatch, its per-page `generated` and `gap` outcomes, and its on-disk
verification are the ones the draft-PR emission sequence above already
describes.

**Freshness is evaluated on every sweep leg the run reaches**, including the
leg that amends nothing and the leg that handles no comment at all, because the
recovery case — pages a previous run left stale — surfaces only on those legs,
and an evaluation reached on the amended leg alone would never repair them.
**The entry gate scopes it**, since the evaluation runs inside the sweep: it is
reached only on corroboration status `match`; on `no_record` the sweep does not
run and there is no pull request to refresh; on the four statuses that stop the
sweep no evaluation occurs and stale pages stay stale. **That is a deferral,
not a lost repair**, because the join is durable and reads the same `amended`
rows on the first `match` run after the operator resolves the gate.

**On a `stale` verdict the leg that amended nothing regenerates, refreshes, and
then proceeds without stopping.** Repairing stale pages never converts a
proceed into a stop: nothing new was amended, so there is nothing new to
re-review.

**A selected page whose regeneration returns a `gap` of its own, in a run that
produced at least one `generated` page, has any pre-existing file at its path
removed from disk.** That is step 3b. The removal is reported **inside that
page's own `gap` outcome**, never as a separate `removed` outcome, which is
reserved for a page re-selection no longer selects. **The ground is the one the
on-disk verification above already gives** for deleting a page that fails its
two tests: a plausible-looking document about a plan that is not this one is
worse than no document at all. A page the author declined to rewrite is that
same hazard one degree sharper, because it is about the right feature and the
wrong, superseded plan. **The exclusion is explicit: a whole-set gap deletes
nothing**, step 3b is skipped in its entirety there, and the directory is left
unmoved. **The removal set keeps a gapped page out**, because the page is still
selected; that rule governs the deselection diff alone and is never licence to
leave the superseded file in the tree.

**Three commit shapes, kept apart.**

| Commit | Stages | Type | When it is taken |
| --- | --- | --- | --- |
| Regeneration | `specs/<feature>/artifacts/` and nothing else | `docs` | the run's final post-verification outcome set carries at least one `generated` page **or** at least one deselection `removed` |
| Record | the workflow file path alone | `chore` | the refresh actually changed the `Draft PR` cell |
| Bookkeeping | the workflow file path alone | `chore` | unchanged, exactly as the sweep already takes it above |

**No commit absorbs another.** The regeneration commit stages the artifacts
directory alone because that is what keeps the freshness join exact: any other
staged path would move the directory's last-touched commit for reasons
unrelated to page content. **An empty regeneration commit is never taken**, it
records nothing and cannot move the join, which is why the gate above is the
outcome set rather than the fact that the step ran. **The gate counts removals
because a removal is a change to the directory**: a run whose re-selection
dropped a page and whose authoring produced nothing still leaves the directory
one page lighter, and the shortfall table above already says that removal lands
and takes a commit. A gate reading `generated` alone would refuse the commit on
exactly that leg, leaving the directory changed and uncommitted while the report
said the removal landed, which is a false report and an uncommitted change the
next Phase 7 whole-worktree commit would sweep into a commit touching the
artifacts directory for unrelated reasons. **The record commit is the
plan-stage terminal step's own commit, reused verbatim** rather than redefined
here: the refresh changes the `Draft PR` cell through the emission machinery
and this commit carries that change, while the sweep still writes no row of its
own. **Writing the regeneration commit on the no-comment leg contradicts
nothing**, because the rule that a run handling no comment takes no commit
governs the bookkeeping commit, and the regeneration commit is not it.

**From the sweep onward, the regeneration commit is the only commit that
stages any path under `specs/<feature>/artifacts/`** — not merely a commit
that stages nothing else. Phase 7 ends in a whole-worktree commit, which runs
on the proceed leg after the sweep, so anything the sweep left uncommitted
under that directory would ride into a commit touching it and move the join.
**The rule does not reach backward to the stage-boundary commit**, which
legitimately carries the first generation through its own `specs/` path set.

**The other half binds the working tree, not the commit.** The reused machinery
writes each page directly into that directory and deletes every written page
failing its verification **before** the commit decision exists, so a run can
end having changed, or emptied, a directory it took no commit for. An emptied
directory reads `no_pages` on the next join, which outranks `stale`, so the
retry that would otherwise repair it never fires.

**The mechanism is snapshot and replay.** Snapshot the artifacts directory's
bytes immediately after the artifacts observation above and before the author
dispatch, and replay that snapshot only when the run's final verified
`generated` count is zero — the regeneration commit's own gate, never a proxy
such as whether a commit landed.

**The replay restores the snapshot minus every page the removal set names.** A
deselection removal is not damage the replay exists to undo: the manifest
re-selection no longer justifies that page, and Q5 forbids carrying a page the
manifest no longer justifies. Restoring it would undo the one piece of work the
run completed and repeat that undoing on every later run, because the
deselection is durable and the authoring failure may not be. So the two
decisions are read apart: the `generated` count decides *whether* to replay, and
the removal set decides *what the replay leaves out*.

**The two shortfall rows follow from that, and do not contradict the gate.** A
whole-set gap with no removal replays the whole snapshot, leaves the directory
unmoved, and takes no commit. A whole-set gap beside a deselection removal
replays every selected page, leaves the directory lighter by exactly that
removal, and takes the commit the gate above now allows. Both match what the
shortfall table already told the operator to expect.

**A git-restore path is rejected**: the
history this case arises on is one where no commit has ever touched the
directory, so git holds no copy to restore from.

**The snapshot goes under `specs/<feature>/.process/feedback-sweep/`**, the
sweep's byproduct directory below, because that rule already places every file
the sweep writes for its own transport there and nowhere else, and names any
scratch the run needs among them. It is run-scoped, ignored through that
directory's self-ignoring `.gitignore`, always removed, and its removal
reported. It is transport, not a store, so it adds no second bookkeeping
record. **It never lives under `specs/<feature>/artifacts/`**: the observation
would read it as a page, and the stem-matched removal diff would then compute
it as a deselection removal, deleting the restore copy. The exclusivity rule
above forbids it there independently.

**The replay decision completes before the byproduct directory is removed.**
The removal below runs before the run proceeds into task work or stops, and
this sequence now sits before that point. Ordered the other way, the removal
destroys the bytes the replay exists to restore, on exactly the zero-generated
path it was written for. The removal itself is unchanged and still runs on
every path. **Any restoration performed is reported as a run-level line beside
the commit sha**, and is not a fourth page outcome: a restored page's own
outcome is the `gap` explaining why it was not regenerated.

**A whole-set regeneration failure still runs the description refresh**, which
carries the whole-set gap as a single row through the same three-sink contract
every other outcome uses, and leaves the stop-or-proceed decision below
unchanged. **It leaves the artifacts directory entirely unmoved**: no page is
deleted, step 3b's per-page deletion is excluded, and step 3's deselection
removal is withheld as well, even though the removal set is otherwise
computable. **Withholding that removal is what keeps the commit from being
taken**, and the untaken commit is the only thing keeping the join reading
`stale` so the next leg retries. A removal landing alone here would move the
directory, mark the whole set current, and strand every gapped page permanently
stale for the sake of deleting one file. **Nothing is lost by waiting**:
re-selection reads the manifest again on the retry, so the same deselection is
recomputed and the removal lands in the run that also regenerates.

**The join repairs an interrupted run, never a gapped one.** Any commit
touching the artifacts directory marks the set current on the next join,
including a commit carrying only removals and a commit carrying only a subset
of the selected pages, so per-page gaps inside a run that took that commit are
the operator's to act on from the report and no later run re-attempts them.
**What decides whether a later leg retries is whether the artifacts commit was
taken, never the shape of the shortfall**: a whole-set gap generated nothing,
takes no commit, moves nothing, and is retried by the next sweep leg, while a
per-page gap beside at least one generated page rides a commit that marks the
whole set current and is retried by nothing. **Recovery takes exactly one
subsequent run and the repair is never repeated**, because after a `stale` run
regenerates and commits, the directory's last commit is newer than every
`amended` row that existed, so the next join reads the set as current.

**The push at step 6 is part of that step, not a step after it.** The dedicated
commit is not complete until it is on the remote, and a failed push **ends the
emission sequence there**: the refresh must not run against pages the remote
does not show. That is the same sequencing the reused machinery already applies
between its own push and its create-or-refresh step, and the same sequencing
the amendment step above applies to its own push. **The leg decides what
happens next.**

- **On a sweep that amended**, a failed push **stops the run immediately**. The
  re-review stop's pull request has to already show current pages, and it does
  not.
- **On a leg that amended nothing**, a failed push does **not** convert the
  proceed into a stop. The local commit stands and rides up with the branch's
  next push.

**On both legs the condition is unrecoverable inside this slice, and the report
says so.** The commit is local and complete, so the join reads the directory as
current on the next run: no later sweep regenerates, and none re-attempts the
refresh this failure skipped. **The manual resume path names both steps the
operator owes**: push the branch, then refresh the description directly.

**Step 7 takes its own live read-only observation at the moment of the
refresh, rather than reusing the entry gate's.** A pull request can be closed or
replaced while the sweep runs, and the later read is the current evidence. This
is the principle the terminal step's two separate reads above already apply.
The query shape is the entry gate's:

```text
gh pr list --head <branch> --state all --json number,url,state,isDraft,headRefName
```

**`--state all` is load-bearing.** It is what makes a closed pull request
distinguishable from an absent one, a distinction the two-way existence test
above cannot produce.

**The classification is the same six-status logic, reused verbatim** — the
`corroborate_refresh` surface of the same helper registration — so each status
takes the behaviour the create-or-refresh table above already assigns it at its
terminal step: `match` refreshes the recorded pull request's description;
`pr_closed`, `pr_missing`, and `identity_mismatch` each end the refresh
attempt, create nothing, and leave the `Draft PR` row exactly as found. **No
status opens a second pull request.**

**`no_record` is unreachable at this call site.** It means an absent `Draft PR`
row, but the sweep is reached only on an entry-gate `match`, which requires the
row, and the sweep is forbidden from writing it, so nothing between the gate
and the refresh can clear it. This matters because the shipped row's behaviour
falls through to creation, and this slice creates on no path.

**`skipped` has one live branch here, not two.** Its shipped row carries a
conditional: refresh when the tool can be reached, report through the
could-not-be-opened path when it cannot. At this call site the classifier's own
input is the observation just taken, so a `skipped` classification is itself the
evidence the tool could not be reached. The reachable branch is dead by
construction.

**Neither is implemented as a fallthrough to creation.** Should either classify
despite the above, the attempt ends with nothing created and the `Draft PR` row
left exactly as found, and a caught `no_record` is reported as a parent-session
invariant violation rather than as an operator-fixable pull-request state.

**Where this call site diverges from the terminal step**: a discrepancy or an
unreachable tool here ends the refresh attempt **only**. It does not change the
stop-or-proceed decision below, does not unwind a regeneration commit that
already landed, and is never reported as a page failure. The terminal step sits
at a stage boundary the run stops at regardless, while the sweep may proceed
into task work.

**On the leg that handled at least one comment and classified nothing
`amended`, the regeneration sequence reaches its own terminal outcome before
the redaction stop below evaluates whether to fire.** Terminal outcome carries
the fail-open meaning used throughout this sequence rather than success: a
per-page gap, a whole-set gap, or a failed artifacts push each end the sequence
at their own reported outcome, and the stop's evaluation follows immediately
once any of them is reached. **This adds no stop condition and changes no
decision**: the stop still fires on the same ground, one or more redaction
events on this leg, with the same report shape and the same resume path.

**The reason is the trigger's own wording.** The stop fires once every write
the run owes has landed, and this leg now owes the artifacts commit, its push,
and the description refresh, so evaluating from the reply point alone, ahead of
those writes, would falsify the sentence that this stop replaces the proceed at
that same point: the proceed already moved later and the stop has to move with
it to stay at the same point. It would also turn a stop defined as notification
after publication into a gate blocking writes this leg owes, on the strength of
an unrelated redaction event. **Where the push failed and left the artifacts
commit local**, the stop still fires on this leg's coincident redaction event,
and its report carries the manual resume path above beside the redaction
report.

**The leg that amended needs no separate rule**, because the sequence already
runs before any stop that leg emits, so a coincident redaction event coalesces
into that stop under the coalescing rule below. **The leg that handled no
comment at all is vacuous here**: the redaction surface fires only on this
run's amendment, log-row, and reply writes, and none of those exists when
nothing was handled. **A run the redaction stop fires on is still a run the
freshness evaluation is required on**, since that stop is not a fourth sweep
leg.

**Stop or proceed, by what the run did.** **One or more `amended`: stop for
re-review before any task work**, its what-landed part naming the comments
swept, the amendments made, and the commit range. **No `amended` but at least
one comment handled: write the records, post the replies, and proceed directly
into task execution** without stopping, because nothing was amended and there
is nothing to re-review. **No comment handled at all: no rows, no replies, no
bookkeeping commit, proceed.** The last two are
stated apart so the first cannot be read as requiring an empty commit on a pull
request that carried no comments. **Any redaction event, on any leg: stop once
every commit is pushed and every reply is posted**, with resume path re-run;
where nothing was amended this stop replaces the proceed at that same point,
and where the re-review stop or the human-review stop also holds it is the
same stop and one report.

**On the leg that handled a comment and amended nothing, the writes this run
owes include the regeneration sequence's terminal outcome**, so that stop is
evaluated once the sequence above has ended at its own reported outcome, rather
than from the reply point alone.

**The feedback sweep's byproduct directory ignores itself.** The sweep writes
its own transport files under `specs/<feature>/.process/feedback-sweep/`, and
the first write into that
directory, before any byproduct, is a `.gitignore` inside it whose whole content
is a single `*` line. Create the directory and write that ignore file in one
step: a byproduct that lands first has already been exposed, so the order is
part of the rule. Git honors that file in whatever repository the worktree
belongs to, and `*` matches the ignore file itself as well as every byproduct
beside it, so Phase 7's `git add -A` can stage neither, by construction rather
than by care, in a consumer repository whose root ignore file this project never
wrote. This repository's own root `.gitignore` carries
`specs/*/.process/feedback-sweep/`, committed so a fresh clone carries it, which
ignores the directory here even before the sweep has written into it and covers
this repository only.

**Every file the sweep writes for its own transport goes there and nowhere
else**: the helper request the runner reads on stdin, each reply body file the
reply write passes by path, the captured commands, and any scratch the run
needs. **The request cannot be redacted instead.** The parse filters over the
comment bodies, so that file has to carry them, and keeping the directory
ignored is what stops Phase 7's `git add -A` from staging a request holding
every observed body. **The sweep removes the directory before it proceeds into
task work or stops, on every path**, neither conditional on the run having
succeeded nor deferred to a later phase, because the spec-index generator scans
the worktree rather than the index and a live byproduct left behind would
contaminate a regeneration even though nothing staged it. **The run report
names the directory as removed.**

**Open the implementation-notes record before the first task is dispatched.**
This is parent-session work, not delegated work, and it runs ahead of the first
`spawn_agent` call rather than lazily on the first append: a phase interrupted
before any task completes, and a spec carrying no implementation tasks at all,
must both still leave a header-only record behind. The record is one file per
spec at `<FEATURE_DIR>/.process/implementation-notes.md`, beside the rest of the
feature's autopilot exhaust. Its first line is the header, written exactly once:

```text
# Implementation Notes: <SPEC_ID>
```

- **Create if absent**: create the `.process/` directory too when that directory
  is also absent, then create the file with the header as its only content. An
  absent directory is a thing to create, never a failure to report.
- **Never truncate**: when the record is already there, leave every existing
  byte as found and append after the existing content. Do not write a second
  header. This is the resumed-phase case, and the entries already in the file
  are the whole point of the record.
- **Check the record's own path** in the working copy this run executes in,
  never a state file, an index, or anything carried over from the session that
  wrote the record, so a resume in a fresh session behaves exactly like a resume
  in the session that started the run.
- **Fail-open**: when creation fails, record a gap in
  `docs/ai/specs/.process/<SPEC_ID>-workflow.md` naming this setup step and the
  operation that failed, do not retry, and carry on into dispatch. Task and
  phase outcomes are exactly what they would have been had the write succeeded.

Use `implement-executor` for test and implementation tasks unless Step 0.11
found a more specific project implementation agent. The parent session dispatches
all workers directly; subagents do not spawn nested agents.

Every attempt the parent session dispatched gets one entry in that record,
appended after everything already in the file:

```text
### <TASK_ID>

**Deviations/Edge cases/Surprises:** <reported text, or None>
```

`<TASK_ID>` is the task's ID exactly as the task list writes it, and one blank
line separates the entry from the content before it.

**One entry per task, even when several tasks share one dispatch.** Batching
related tasks into a single worker is a sensible dispatch choice and does not
change the record: each task named in the task list gets its own entry under its
own ID. Never write a compound heading such as `### T007+T008+T009`, because a
reader cannot recover three task IDs from one heading. Split the worker's
reported text across those entries, or repeat the shared text under each.

**Per-arrival cadence, one rule for every dispatch shape.** Append on the turn
that attempt's own result reaches the parent session, before dispatching further
work. The bounded `wait_agent` loop already delivers each worker's summary
individually, so a member of a cap-bounded `[P]` wave does not wait for the rest
of its wave: its entry is written when that summary is consumed, not when the
wave reaches its TYPECHECK and UNIT_TEST safety net. Never batched to phase end,
and never deferred to a wave boundary. Where several summaries are consumed on
the same turn, each still gets its own entry on that turn, in the order they are
presented.

**Never append on a bare idle or liveness signal.** A status update, a
`wait_agent` timeout, or a worker that stops without delivering its task summary
is not a result: it is a cue to keep polling, or to ask for the summary, and not
a cue to write an entry. Appending on one writes an empty entry, then
double-counts the attempt once that worker's real summary arrives.

**Additive only.** No entry already written is rewritten, reordered, or removed,
and the record is never read back to update a counter or to find a previous
entry. The serial re-run after a regression appends a further entry under the
same task ID and leaves the earlier one exactly as written; two entries sharing
a task ID are correct history, not a defect. Document order is append order, so
position is the record's only ordering signal, and where two entries share a
task ID the earlier-positioned one is the earlier attempt.

**Fail-open on an append too.** A failed append is recorded as a gap in the
run's workflow file, never in the implementation-notes record that just failed,
and the gap names the attempt and the operation that failed so a reader can tell
which write was lost. The write is not retried: one attempt, then the gap. The
fallback is exactly one level deep, so when the workflow file is itself the
unwritable path, surface that second failure in the run's own output and carry
on, with no third destination and no recursion. The blast radius is one entry:
every other attempt in the same wave is still appended as its own result
arrives, and the next dispatch still happens. A reporting-content problem is not
a write failure, so a missing or unreadable field produces a `None` entry rather
than a gap.

**Three append call sites in the routing, not one.** The routing branch decides
what an entry carries, which is a different axis from the dispatch shape that
decides when it is written:

| Route | Task-result block? | Entry value |
| ----- | ------------------ | ----------- |
| `implement-executor` or project implementation agent | Yes | Reported text, or `None` |
| Research routed to `domain-researcher` | No | `None` |
| Verification run orchestrator-direct | No | `None` |

Appending only on the executor branch leaves research and verification attempts
silently missing from the record.

**The literal `None`** is the single value for every nothing-to-report case: the
executor reported `None`, the executor omitted the field, the field cannot be
read out of the summary it returned, or the route emits no task-result block at
all. No distinct marker and no route field, because a second value would make
the record unreadable as a count of what was reported the moment a wave contains
one research task.

When a current `pr_marker_plan` is available, execute, checkpoint, and record
Phase 7 evidence in marker order. Run each marker's tasks according to
`markers[].review_order`; keep normal task dependency and `[P]` parallel rules
inside a marker. After each marker completes, record marker ID, ordered task IDs,
verification evidence path, fingerprint status, checkpoint commit SHA
(`implementation_checkpoint.head_sha` or `implementation_checkpoint.commit_sha`),
warnings, and any blocked/fixed tasks. The marker checkpoint SHA is the source
commit for later live marker PR branches. Do not infer a new marker order from
changed files or reviewability warnings.

## PR Packet and Body Boundary

Before creating or updating a PR after G7, the parent session applies this
fail-closed sequence:

```text
final-reviewability boundary: use current committed reviewability evidence; if none is current, stop before PR side effects
emit or refresh specs/<feature>/.process/pr-packets/<packet-id>.json with pr-packet-output dry_run then apply
run validate-pr-packet-read-only for that packet and consume response data.stdout_json in memory/state
require data.stdout_json.status=passed, data.stdout_json.pr_blocked=false, and response data.writes_state=false
checkpoint packet/body artifacts so validate-pr-packet-write runs from a clean worktree
run validate-pr-packet-write; apply mode reruns read-only validation before persisting validation_result_path
run validate-pr-workflow-contract with the packet title
create only with packet-owned --base, --head, --title, and --body-file values
```

Continue only after current committed reviewability evidence shows `pass`,
`warn`, honored typed exception, or final `marker_split` with a current
`pr_marker_plan`. When a current `pr_marker_plan` exists, PR preparation
continues through marker emission even if the final full-diff result is only
`pass` or `warn`. A full-diff size block with current marker evidence also
proceeds to marker emission and is not a manual re-slicing stop. In the current
committed evidence, exit 1 is `reslicing_required` only for unexcepted
correctness or missing-marker cases:
do not generate a PR body, invoke any `gh pr create` variant, or run
`multi-pr-emission` yet. This blocks only PR side effects. It is not a final
response condition: read `autopilot_continuation`, the packet's
`operator_steps`, and `resume.resume_from`; continue inside the same autopilot
run through the named PRSG-007/008/009 phase until a valid slice PR stack is
emitted or a typed exception is committed. Never report completion while
`autopilot_continuation.required=true`. Recorded exit 2 is a gate error: state is
written, no packet is valid, and the run stops for operator repair.

For marker-aware PR preparation, record gate status/mode/exit/evidence path,
fingerprint status, ordered marker IDs, checkpoints, warnings, final
marker_split or marker-plan-ready handoff, packet validation, and PR mappings
before PR side effects.

Use `pr-packet-output` to emit or refresh the feature-local packet and
packet-owned body before `gh pr create`. If the packet or body is missing,
stale, malformed, or invalid, rerun packet output with current title, target,
changed-file, verification, UAT, non-goal, and known-gap evidence. The
read-only validator returns its result in `data.stdout_json` and does not
persist state. If any required packet is absent or invalid, stop before PR
creation with the validator diagnostics. Checkpoint packet/body artifacts so
`validate-pr-packet-write` runs from a clean worktree; apply mode reruns
read-only validation before persisting `validation_result_path`.

`generate-pr-body` is a body-only `golden_only` operation. Its complete input
contract is `output_path`, `title`, and `sections`, and it writes one Markdown
body. It does not create or update packet JSON, packet metadata, template
markers, validation evidence, or PR commands. Its output alone never authorizes
PR creation.

## Coverage Audit

Run the all-phase coverage audit before Phase 1, after every phase transition,
and on resume. If any of these prefixes is absent from either durable state
store, repair the plan before continuing:

```text
Phase 0:
Phase 1:
Phase 2:
Phase 3:
Phase 4:
Phase 5:
Phase 6:
Phase 6.5:
Phase 7:
Post:
```

Then run the deterministic guard against the workflow/state pair:

```text
resolved_python "<plugin-root>/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py" --workflow "$WORKFLOW_FILE" --state "$WORKFLOW_DIR/autopilot-state.json" --rule status-evidence
```

`resolved_python` is the Python 3.11+ interpreter resolved by the installed
runtime contract, not a hardcoded interpreter name; `<plugin-root>` is the
directory that owns `skills/speckit-autopilot/`. `--rule status-evidence`
scopes the exit code to the bookkeeping rule, matching the Claude variant.

For `pr-marker-plan.v2` state with a changed-file manifest, append
`--expected-base-commit <live-baseRefOid> --expected-head-commit <live-headRefOid>`
using OIDs fetched from live PR metadata immediately before the run. Do not
reuse values declared by the workflow, state, or manifest as external PR
authority.
