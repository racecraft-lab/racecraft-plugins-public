# Workflow File Update Protocol

After EVERY phase, the autopilot updates these sections in the
workflow file so the file remains the durable source of truth
across context compactions and `--from-phase` resumes.

## Per-Phase Update Table

| Phase | Sections to Update |
| --- | --- |
| **All** | Status table: `⏳` → `✅` with summary notes |
| **Specify** | Specify Results table, Files Generated checkboxes |
| **Clarify** | Clarify Results table (session focus, questions, outcomes) |
| **Plan** | Plan Results table (artifact status) |
| **Checklist** | Checklist Results table, Addressing Gaps section |
| **Tasks** | Tasks Results table (total, phases, parallel, coverage) |
| **Analyze** | Analysis Results table (ID, severity, issue, resolution) |
| **Implement** | Implementation Progress, Post-Implementation Checklist, Success Criteria |

## Additional Updates

- **Constitution Validation table** — update after Specify (initial)
  and Implement (final).
- **Consensus Resolution Log** — if consensus was used, add a row per
  resolution. Mandatory columns: `Round`, `Routed Categories`,
  `Outcome`, `Analysts Used`. See
  [`consensus-protocol.md`](./consensus-protocol.md) §Logging for the
  canonical column set and the 10% Round-2 escape-rate re-evaluation
  trigger computed from these rows.

## The `Stage` Entry

The resolved stage is recorded as a row in the workflow file's
`### Basic Information` table — the same scalar `| Field | Value |` table that
already carries `Branch`:

```text
| **Stage** | plan |
```

The value is one of `plan`, `implement`, `full`. It records the last **resolved**
stage of the most recent run, not stage completion — within-stage progress stays
derived from the Workflow Overview status table. A workflow file carrying **no**
`Stage` row means "no run yet": that is legal, is not an error, and resolves
through ordinary auto-detection.

**Write cadence — at most twice per run.** The `Stage` row is *not* refreshed on
phase transitions:

1. **At resolution**, during opening preparation (Step 0.6c), write the row once.
2. **At the plan stage's terminal commit only**, write it again **only if** the
   resolved stage changed. No other write happens.

**Both stores are written in the same edit turn and land in the same commit.**
The workflow file's `Stage` row is authoritative and `autopilot-state.json.stage`
is its mirror; writing them together is what guarantees an interrupted run
cannot leave a *committed* disagreement between the two. Never write one, run a
phase, and write the other later. On disagreement the workflow file wins and the
mirror is repaired from it — the Step 1.1 coverage guard reports a two-sided
mismatch as `stage_mirror_errors` and fails.

## The `Draft PR` Entry

The draft pull request the plan stage opens is recorded as a row in the same
`### Basic Information` table that carries `Branch` and `Stage`:

```text
| **Draft PR** | [#438](https://github.com/owner/repo/pull/438) |
| **Draft PR** | [#438](https://github.com/owner/repo/pull/438) — 2 of 4 artifacts missing |
```

It does **not** go in `## Workflow Overview`. That table's rows are phase status
records with `Phase | Command | Status | Notes` columns. A pull-request identity
is neither a phase nor a status, and putting it there would break every reader
that treats those rows as phase records.

**Grammar.** The key is `Draft PR`, matched case-insensitively after stripping
`*`, backticks, and spaces — the same normalization `Stage` already uses. The
value begins with one Markdown link whose text is `#<number>` and whose target is
the pull request URL. The number and the URL are one linked reference, not two
columns: readers take the number from the link text and the URL from the link
target. An optional gap note may follow the link in the same cell.

**Two states, both legal.** A row that is absent means no pull request has been
opened for this feature. That is information, never a fault, and it is the same
shape `Stage` already uses for "no run yet". A row that is present means a pull
request exists at that identity.

The scaffold workflow template ships **no placeholder row**, following the
`Stage` precedent exactly. A commented-out example would not help either: HTML
comments are blanked before the table is parsed, so it could never be read as
evidence.

**Write rules.**

| Rule | Detail |
| --- | --- |
| when | only after creation or refresh succeeds |
| which commit | the separate bookkeeping commit, never the stage-boundary commit |
| repair | when a pull request exists but the row is missing or wrong, write or repair it |
| whole value | every write rewrites the whole cell from the current run's outcome, so a stale gap note never survives a refresh that no longer fell short |
| leave alone | whenever the recorded and live identities disagree — the recorded pull request is closed, is unobservable, or a different pull request is open on the branch — leave the row exactly as found |
| sole store | this row is the only place the identity is stored — there is **no state-file mirror** |

That last rule is deliberate, and it is why this entry reads differently from
`Stage` directly above. `Stage` has a mirror and therefore a write cadence and a
same-edit-turn rule to keep the two in step. This identity has no mirror, so
writing this row neither counts against nor re-triggers the `Stage` row's own
cadence, and needs no state-file write at all. A second sink would introduce
exactly the status-versus-evidence drift the Step 1.1 coverage guard and the
tree-wide CI gate already fail on.

**Reader.** `workflow_draft_pr_row(lines)` sits beside `workflow_recorded_stage`
and reuses `workflow_table_rows` and `AUTOPILOT_BASIC_INFO_HEADING` unchanged. It
returns the parsed number, URL, and gap note, or nothing when the row is absent.
The two readers differ only in the key they match, which is three near-duplicate
lines rather than a generic scalar-row abstraction — the trade the constitution's
KISS and YAGNI principle asks for until a third caller exists.

## The Feedback Sweep Log

The pull-request feedback sweep records what it handled in a table of its own,
under a `Feedback Sweep Log` heading in the workflow file:

```text
### Feedback Sweep Log

| # | Comment ID | Surface | Author | Class | Disposition | Commit | CRL # |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | IC_kwDOAAAAAA5vXkZ9Aq | review thread | octocat | amended | Tightened the retry bound in spec.md §4.2 | a1b2c3d | 7 |
| 2 | IC_kwDOAAAAAA5vXkaB2c | conversation | author unresolved | answered | Answered in the reply; no artifact change |  |  |
```

**One row per handled comment.** A comment is handled once it has been assigned
a class. A comment the trust filter dropped, one the self-reply rule dropped,
and one whose consensus round returned no answer each take no class, so none of
them gets a row. The row carries the comment id, the surface it was read from,
its author, its class, its disposition, and the commit that answered it.

**The `Disposition` cell escapes any pipe as `\|` and any newline as a line
break.** The table readers in this codebase split rows on the bare pipe with no
escape handling, so one unescaped pipe would shift `CRL #` out of its column
and make the consensus link read the wrong cell. The comment id sits ahead of
the disposition, so the skip key survives whatever that prose contains.

**What fills that cell.** The classifier returns a `reason` of at most 512
bytes as UTF-8, carrying neither a pipe nor a newline. That string crosses the
redaction surface's `log_row` leg before any use, and what the leg returns is
the only form that reaches the cell. The escaping above is applied last, to the
leg's output.

**An author that cannot be resolved is recorded explicitly** rather than left
blank, because a blank cell is indistinguishable from a cell nobody wrote.

**Every amendment additionally produces a Consensus Resolution Log row**, and
`CRL #` names it by number. The link runs both ways at no extra column: that
consensus row's item cell names the comment id. See
[`consensus-protocol.md`](./consensus-protocol.md) §Logging for the `Sweep` row
type.

**Creation and placement rules.**

| Rule | Detail |
| --- | --- |
| who creates it | the sweep, when the workflow file carries no Feedback Sweep Log: it writes the heading and the header row itself. The scaffold workflow template ships neither and is not changed to ship them |
| one write | the heading, the header row, and every row that run writes land together in the single bookkeeping commit, never in a commit of their own ahead of it |
| placement | match `Consensus Resolution Log` by its heading text at any level, and write `Feedback Sweep Log` at the **same** level, so the two are siblings |
| no anchor | append `## Feedback Sweep Log` at the end of the file |
| numbering | the leading `#` column starts at 1 and each new row takes one more than the highest number already in the table, so numbering continues across runs and never restarts |
| sole store | this table is the only place the sweep record is kept; there is **no state-file mirror** |

Creation is not a write of its own because that would put a commit carrying the
heading and no rows into history. An empty table reads as "nothing has been
handled", which is indistinguishable from a genuine clean first run, and that
is the one direction the skip key cannot tolerate.

Placement matches the anchor's level rather than assuming one, because the
anchor is neither guaranteed to exist nor guaranteed to sit at `###`. Of the 69
workflow files committed in this repository, 33 carry no Consensus Resolution
Log heading at all; of the 36 that do, 31 write it at `###` and 5 at `##`. A
fixed `###` written under a `##` anchor would nest the sweep log inside the
consensus section, which reads as subordinate to it and is not what the
`CRL #` cross-reference describes.

**Sole store, deliberately**, following the `Draft PR` rule directly above.
A second sink would introduce exactly the status-versus-evidence drift the Step
1.1 coverage guard and the tree-wide CI gate already fail on. It is also what makes the record durable across
archiving, and what lets a re-run read its own skip set back: the sweep skips
any comment id that already carries a row here, and it reads that set from this
table and nowhere else.

## `workflow_file` State Authority

`autopilot-state.json.workflow_file` names the workflow a run is authorized
against. The Step 1.1 coverage guard compares the supplied `--workflow` against
that value and reports a disagreement as `workflow_authority_errors`, which is
registered in the `status-evidence` rule and so fails the guard rather than
merely printing. This is **state-file-wins**, the opposite direction from the
`Stage` rule above, which is why the two sit adjacent here.

**Five branches, in this order.** The order is load-bearing: an earlier skip must
win over a later failure.

| # | Condition | Verdict | Why |
| --- | --- | --- | --- |
| 1 | The state carries no `workflow_file` key | **skip** | A state naming no workflow asserts no authority. Membership of the key decides this, not whether the value is null — an explicitly nulled field is malformed, and folding the two together would make `null` a silent opt-out |
| 2 | No repository root resolves from the state file's location | **skip** | Without a root there is no boundary to resolve the supplied workflow against. This matches the precedent the same guard already sets for an extracted copy |
| 3 | The value is malformed: not a string, empty, whitespace-only, or not a normalized repository-relative path | **fail** — `autopilot state workflow_file is not a normalized repository-relative path` | The value is machine-written, so a shape it should never take means the state is untrustworthy rather than that the workflow is wrong. Whitespace-only is checked explicitly and ahead of the normalized-path helper, because a run of spaces is a valid POSIX path part and would otherwise reach branch 5 and be reported as a mismatch against a blank path |
| 4 | The supplied workflow is resolved against the repository root | **fail** — `workflow file is outside the authorized repository` when it resolves outside; **skip** when it cannot be resolved at all | Outside the root is a completed evaluation with an out-of-boundary result, which is the case the check exists to catch — a different fact from branch 2, where the repository could not be found at all. Resolution itself raises on a path it cannot traverse, such as a symlink loop, and that is an absence of information rather than an out-of-boundary result, so it skips like branch 2 rather than reporting a mismatch it cannot substantiate. Through this guard's own call path that outcome is **defensive rather than reachable**: the supplied workflow is read before the comparison, so an untraversable path has already raised there. It exists so the helper cannot raise for a caller that reads in a different order, and so a future reordering does not turn a skip into a traceback |
| 5 | The two references differ | **fail** — `supplied workflow does not match autopilot state workflow_file authority`, with both compared paths appended | This is a run resuming the wrong specification. Both paths are printed because the maintainer cannot otherwise tell which side to repair: re-point the run, or reclaim the state slot and let the next invocation rewrite it |

Anything reaching the end passes and reports no authority error. **All three
skips** — branch 1, branch 2, and the unresolvable-path outcome inside branch 4 —
leave the run indistinguishable from one that ran the comparison and passed it,
because a skip and a satisfied comparison both report no error and both exit
zero. The exit code carries the verdict, not whether the verdict was computed.

**This is the trap when reading corpus evidence.** The report always carries
`workflow_authority_errors`, so an empty value proves only that the repaired
guard is running, never that the comparison ran. Presence separates repaired code
from unrepaired code, where the key is absent entirely. It does not separate a
satisfied comparison from a skipped one. To prove a comparison ran, vary an input
and show the verdict change.

**Resolution is asymmetric.** The **supplied** workflow is resolved against the
repository root and rendered POSIX, so the right file named absolutely, or
relatively from any working directory, still matches. The **state** value is
compared as the literal string it holds, with no filesystem resolution, because
it is machine-written and branch 3 has already constrained its shape. Only the
supplied side has spelling freedom.

Resolution follows symlinks, so what is compared is where the supplied path
**lands**, not how it was spelled. Name the workflow through a symlink and the
comparison sees the target: a link at `docs/a-workflow.md` pointing at
`docs/b-workflow.md` reports a branch 5 mismatch even when the state names
`docs/a-workflow.md` and the run supplied that same path, and a link whose target
resolves outside the repository reaches branch 4 instead. Keep workflow files and
the state that names them as real paths inside one repository.

**The comparison is byte-exact**, on the two POSIX references, with no case
folding and no filesystem identity test such as `samefile`. Case is deliberately
not folded: byte-exact is the only rule that returns the same verdict on a
case-insensitive filesystem and a case-sensitive one, so the verdict does not
depend on which kind of filesystem the run happens to sit on. Folding case, or
testing filesystem identity, would let a mis-cased state value pass on one and
fail on the other.

## PR Marker Plan Evidence

When reviewability sizing is marker-planning input, persist marker state as
top-level `pr_marker_plan` in `autopilot-state.json` and mirror it into workflow
evidence. The workflow summary is reader-facing evidence, not the authoritative
store. Marker evidence is not authoritative marker state in `tasks.md`; `tasks.md`
continues to define tasks and dependencies only.

The workflow mirror must include the same schema version, source fingerprint,
fingerprint status, ordered marker IDs, review order, marker checkpoints,
warnings, final marker_split status, packet validation, and PR mappings as
`autopilot-state.json`. Evidence paths must be repo-relative paths such as
`specs/<feature>/.process/reviewability/tasks-gate.json`, not absolute runtime
paths under `/tmp`, a local worktree, or a plugin cache.

If the workflow mirror and top-level `pr_marker_plan` disagree, repair the
workflow mirror from `autopilot-state.json`. If `autopilot-state.json` is
missing, malformed, stale, or fingerprint-mismatched at a boundary that requires
marker evidence, stop as malformed/stale marker state instead of guessing from
the workflow prose.
