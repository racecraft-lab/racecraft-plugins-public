# Phase 1 Data Model: ART-008 slice 2 — Artifact Freshness

**Input**: `specs/art-008-feedback-sweep-slice-2/spec.md` §Key Entities,
`specs/art-008-feedback-sweep-slice-2/plan.md` §Architecture

This slice introduces no persistent store. Every entity below is either read
from a file that already exists, supplied as request data, or returned in a
response envelope. FR-003 forbids any additional bookkeeping store, state file,
or mirror, and nothing here is one.

---

## 1. Feedback Sweep Log row (read; never written by this slice)

The sole record of what a sweep handled, shipped by slice 1 and documented in
`speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md`
§The Feedback Sweep Log. One row per handled comment.

Header, fixed by slice 1:

```text
| # | Comment ID | Surface | Author | Class | Disposition | Commit | CRL # |
```

**Cells this slice reads — two, and only two:**

| Cell | Anchor | Type | Read rule |
|---|---|---|---|
| `Class` | header index from the **left** | closed token | Matched casefolded against the literal `amended`. Rows of any other class are ignored entirely. |
| `Commit` | **`-2`** from the row's end | free text | Taken **verbatim**, including whitespace-stripping only. It is the join key into the supplied ancestry records and is never parsed, normalized, abbreviated, or expanded. |

**Cells this slice reads for reporting only:**

| Cell | Anchor | Use |
|---|---|---|
| `#` | header index from the **left** | Names an undeterminable row in the verdict (FR-005). The cell's own value is the authority, because slice 1's numbering continues across runs and never restarts. An empty `#` cell is itself a reportable condition. |

**Cells this slice never reads**: `Comment ID`, `Surface`, `Author`,
`Disposition`, `CRL #`.

### The dual-anchoring rule is part of the data model, not an implementation detail

`Disposition` is free prose. Slice 1 requires it to escape a pipe as `\|`, but
the shipped row splitter (`read_only.py:1594`) splits on the bare pipe with no
unescaping, so an escaped pipe **still splits**. A row whose disposition carries
one pipe has nine cells, not eight.

- Columns at or before `Disposition` keep their left-hand header index.
- Columns after it are addressed by negative offset from the row's end.
- Both offsets are derived from the header row, never hard-coded.

**Validation:**

| Condition | Result |
|---|---|
| row has fewer cells than the header | malformed; `Commit` unreadable; row is undeterminable (FR-006) |
| row has more cells than the header | ordinary pipe-in-disposition case; right-anchored cells are correct; **not** an error |
| `Commit` cell empty or whitespace | row is undeterminable (FR-006) |
| `Class` cell missing or unreadable | row is not `amended` and contributes nothing |
| header carries no `Commit` column | the `-2` anchor is underivable; every `amended` row is undeterminable with reason `missing_commit_cell`. The header row is therefore located by `Class`, never by `Commit`. |
| no `Feedback Sweep Log` heading in the file | zero `amended` rows; the verdict is decided by the directory state alone |

---

## 2. Artifacts observation (supplied request data)

Everything the helper cannot derive from the workflow file. Supplied by the
orchestrator, which is the only party that runs `git` (FR-004, FR-004a).

```json
{
  "ok": true,
  "artifacts_dir_state": "present",
  "last_artifacts_commit": "9f2c1ab8d4e5f60718293a4b5c6d7e8f90123456",
  "pages": ["implementation-plan", "spec-explainer"],
  "amended_commits": [
    {"cell": "a1b2c3d", "resolved": true, "is_ancestor_of_artifacts_commit": true},
    {"cell": "e4f5a6b", "resolved": true, "is_ancestor_of_artifacts_commit": false},
    {"cell": "deadbee", "resolved": false, "is_ancestor_of_artifacts_commit": null}
  ]
}
```

| Field | Type | Rule |
|---|---|---|
| `ok` | boolean | MUST be the JSON literal `true` to be read at all. Any other value — including truthy `1` or `"true"` — is an unusable observation and yields the `undeterminable` verdict rather than an input error, because FR-023 forbids a failed gather from blocking the run. This follows `observation_pull_requests` (`read_only.py:1353-1409`) exactly. |
| `artifacts_dir_state` | closed token | `absent`, `empty`, or `present`. `absent` and `empty` both read as `no_pages` (FR-007). `present` with no `last_artifacts_commit` is the FR-007a case. |
| `last_artifacts_commit` | string or null | The last commit touching `specs/<feature>/artifacts/`, in whatever form the orchestrator resolved it. Reported back for the operator; **never compared as a string** (FR-008). `null` means no commit has ever touched the directory. |
| `pages` | array of strings | The pre-regeneration on-disk inventory, by filename stem. The helper **echoes** this; it never selects (FR-004). A value that is not an array of strings, on an observation whose `ok` is the literal `true`, is an input error rather than an echo: a bare string splats into one page per character and reports an inventory nobody supplied. |
| `amended_commits` | array of records | One per `amended` row, keyed by that row's `Commit` cell text **verbatim**. Not an array, or carrying a non-object, is an input error on an observation that reported success. |

**Every type in this table is enforced, not merely declared.** Once `ok` is the
literal `true`, the helper checks each field against the type above and returns
an input error on a violation. The asymmetry with `ok` is the contract's own: a
failed gather is a fact about the world FR-023 forbids from blocking the run,
while a gather that reported success and then handed over the wrong shape is the
caller's defect. Unchecked, the echo raises a `TypeError` the runner reports as
an internal failure, which is not a verdict either.

### Ancestry record

| Field | Type | Rule |
|---|---|---|
| `cell` | string | The row's `Commit` cell text verbatim. This is the join key. |
| `resolved` | boolean | Whether the cell resolved to a commit in this history. |
| `is_ancestor_of_artifacts_commit` | boolean or null | Whether that commit is an ancestor of `last_artifacts_commit`. `null` when `resolved` is false. **`false` when `resolved` is true and `last_artifacts_commit` is null** (FR-007b): there is no commit to be an ancestor of, and the FR-007a case needs a pinned value for its fixtures to assert. Both halves are refused as input errors when violated — a record that resolved without a boolean here, and an unresolved record carrying a non-null one. |

**FR-007b is enforced rather than written down.** The stale test is for the
literal `false`, so a resolved record leaving this field null reads as *not
stale* and leaves the pre-amendment plan in front of the re-reviewer, which is
the FR-007a interrupted-run case exactly. The orchestrator prose states the
obligation and the helper refuses the request that breaks it, because a rule
only one side knows is a rule no run enforces.

**Why ancestry and not a comparison.** The `Commit` cell may hold an abbreviated
sha while `last_artifacts_commit` is full, so string equality would report a
matching commit as stale (FR-008). A timestamp comparison would be wrong across
a rebase (FR-004a). A commit is its own ancestor, so equality needs no separate
rule and cannot be written wrong.

**Unmatched rows.** A row whose `Commit` cell text matches no supplied `cell` is
undeterminable (FR-004a). It is never silently skipped, because skipping would
read the pages as current.

**Joinable, defined.** A row is *joinable* when its cell matched a supplied
record **and** that record carries `resolved` as true (FR-007b). A matched but
unresolved row is not joinable: FR-006 already makes it unable to prove
freshness either way, so letting it prove staleness instead would contradict
that rule. This is the term FR-007a's stale reading turns on.

---

## 3. Freshness verdict (response)

The verdict surface's output. Exactly one of four, evaluated in this precedence
order (FR-005):

| # | Verdict | Condition | Effect |
|---:|---|---|---|
| 1 | `no_pages` | `artifacts_dir_state` is `absent` or `empty` | Nothing to judge. No regeneration, no refresh, no commit (FR-007). Wins regardless of the log. |
| 2 | `stale` | any `amended` row with `resolved: true` and `is_ancestor_of_artifacts_commit: false`, **or** `last_artifacts_commit` is null with at least one joinable row | Regenerate, remove, commit, push, refresh (FR-008, FR-009, FR-007a). One such row decides it alone. |
| 3 | `undeterminable` | any `amended` row missing, empty, unresolvable, or unmatched | Report only. No action of any kind (FR-005a, FR-006). |
| 4 | `current` | none of the above | Regenerate nothing, refresh nothing, proceed. |

```json
{
  "tool": "check-artifact-freshness",
  "named_surface": "verdict",
  "verdict": "stale",
  "reason": null,
  "last_artifacts_commit": "9f2c1ab8d4e5f60718293a4b5c6d7e8f90123456",
  "amended_rows_read": 3,
  "deciding_rows": [{"row": "2", "cell": "e4f5a6b"}],
  "undeterminable_rows": [{"row": "3", "cell": "deadbee", "reason": "unresolvable_commit"}],
  "pages": ["implementation-plan", "spec-explainer"]
}
```

| Field | Rule |
|---|---|
| `verdict` | One of the four literals. The set is closed. |
| `reason` | Present on every verdict, `null` unless the observation was unusable, where it is `unusable_observation`. That token names a fact about the request rather than about a row, so it has no home in `undeterminable_rows`. Every key is present on every response, `null` where a verdict has nothing to say, following `corroboration_record`'s shipped rule. |
| `deciding_rows` | Present on `stale`; every row that proved it, so the operator sees the evidence rather than a bare token. |
| `undeterminable_rows` | Each carries the row's `#` cell value and a reason from a closed set: `missing_commit_cell`, `empty_commit_cell`, `unresolvable_commit`, `no_matching_observation_record`, `malformed_row`. Present on any verdict, because FR-006 requires surfacing such a row even when `stale` already decided the verdict — `no_pages` included, where `deciding_rows` is empty because nothing was judged but the rows the join could not read were still read. Empty on the unusable-observation verdict alone, where the log was never joined. |
| `pages` | The supplied inventory, echoed. Never a selection. |

**An unusable observation echoes nothing.** §2 requires `ok` to be the literal
`true` "to be read at all", which governs the echo rule above: a response that
read nothing cannot echo it. On that verdict `pages` is `[]`,
`last_artifacts_commit` is `null`, and `amended_rows_read` is `0`.

**The `undeterminable` verdict is reported and acted on never.** It triggers no
regeneration, no refresh, and no commit, and it moves the stop-or-proceed
decision in neither direction (FR-005a). Nothing in this slice's scope can clear
the condition that produced it, so an action keyed to it would repeat on every
later clean sweep without end.

---

## 4. Removal set (response of the second surface)

Input: the pre-regeneration inventory the verdict surface observed, and the
manifest re-selection's page-id list — **both `generated` and `gap` outcomes**,
because a gapped page is still selected and must not be removed for that reason
alone (FR-012a).

```json
{
  "tool": "check-artifact-freshness",
  "named_surface": "removal_diff",
  "removals": ["module-map"],
  "observed": ["implementation-plan", "spec-explainer", "module-map"],
  "reselected": ["implementation-plan", "spec-explainer"]
}
```

| Rule | Detail |
|---|---|
| Matching | By the manifest entry id kept as the filename stem, which is the naming the emission machinery already uses. |
| Direction | Present in `observed`, absent from `reselected`. Never the reverse: a page in `reselected` and not in `observed` is a new page, which the author dispatch writes. |
| Authority | The surface **MUST NOT delete a file**. The system performs the deletion, stages it in the FR-018 commit, and reports each removal as its own outcome. |
| Echo | Both inputs are echoed so a reviewer can check the difference without re-deriving it. |

---

## 5. Refresh corroboration (response of the third surface)

The entry gate's own five-field observation, taken fresh at the refresh call
site (FR-033, FR-033a) and classified through the shipped six-status logic
reused verbatim.

Input observation, same shape as Step 0.6c's:

```json
{"ok": true, "pull_requests": [{"number": 471, "url": "…", "state": "open",
                                "isDraft": true, "headRefName": "…"}]}
```

Response:

```json
{
  "tool": "check-artifact-freshness",
  "named_surface": "corroborate_refresh",
  "corroboration": {"status": "match", "recorded": {"number": 471, "url": "…"},
                    "observed": {"number": 471, "url": "…", "state": "open"},
                    "merged": null, "reason": null}
}
```

| Rule | Detail |
|---|---|
| Vocabulary | The closed six: `match`, `no_record`, `skipped`, `pr_closed`, `pr_missing`, `identity_mismatch`. Reused, never re-derived. |
| Record shape | All five keys on every status, in the order the shipped builder writes them. What a status has nothing to say about is `null` rather than omitted. |
| Row source | `workflow_draft_pr_row` over the workflow file with HTML comment spans blanked first, so a commented-out row can never become evidence. |
| `ok` | Literal `true` only, exactly as the entry gate requires. Anything less yields `skipped`. |
| Scope | Read-only and deterministic. The surface runs no tool and touches no network. |

**Per-status behavior at the refresh call site** (FR-034; the classification
reports, the orchestrator acts):

| Status | Behavior |
|---|---|
| `match` | refresh the recorded pull request's description |
| `no_record` | fall through to the live by-branch existence test, then create or refresh |
| `skipped` | never create; report through the could-not-be-opened shape, naming which of the four causes occurred |
| `pr_closed` | end the refresh attempt, create nothing, leave the row exactly as found |
| `pr_missing` | end the refresh attempt, create nothing, leave the row exactly as found |
| `identity_mismatch` | end the refresh attempt, create nothing, leave the row exactly as found; name **both** identities |

**No status opens a second pull request.**

---

## 6. Page outcome (report record, not a helper output)

One record per page in the run report (FR-024).

| Field | Values |
|---|---|
| `page` | the manifest entry id / filename stem |
| `outcome` | `generated`, `gap`, or `removed` |
| `reason` | required on `gap`: what was missing and why. Absent on the other two. |

`generated` and `gap` come from the ART-007 author dispatch unchanged, after its
two on-disk verification tests convert a page that is byte-identical to its
template, or that still carries a sample banner, into a `gap` with the file
deleted. `removed` comes from the removal set and is **never silent** (FR-012).

---

## 7. Commit shapes (three, kept apart)

| Commit | Stages | Type | Taken when | Requirement |
|---|---|---|---|---|
| Regeneration | `specs/<feature>/artifacts/` and nothing else | `docs` | regeneration produced a change under that directory | FR-018, FR-019 |
| Record | the workflow file path alone | `chore` | the refresh actually changed the `Draft PR` cell | FR-039 |
| Slice-1 bookkeeping | the workflow file path alone | `chore` | a `Feedback Sweep Log` or `Consensus Resolution Log` row was written | FR-020, unchanged |

**No commit absorbs another.** The regeneration commit stages the artifacts
directory alone because any other staged path would move the directory's
last-touched commit for reasons unrelated to page content, which is what makes
FR-001's join exact. An empty regeneration commit is never taken, because it
records nothing and cannot move the join.

**And no other commit stages the directory** (FR-018a). Exclusivity has to run
in both directions: the phase hosting the sweep ends in a commit that stages the
whole worktree, so anything the sweep leaves uncommitted under
`specs/<feature>/artifacts/` would ride into a commit touching it and move the
join just as surely. That is why the working tree, not only the commit, carries
the "unmoved" obligation on every path that takes no regeneration commit — the
emission machinery writes pages into the directory and deletes the ones that
fail verification before the commit decision is ever reached, so a run can empty
a directory it promised not to move. Such a directory reads `no_pages` on the
next join, which outranks `stale`, and the retry FR-038 promises never fires.

**The push is part of the regeneration step, not a step after it** (FR-019a).
The commit is not complete until it is on the remote, and a failed push ends the
emission sequence there — the refresh must not run against pages the remote does
not show. On a sweep that amended, that stops the run; on a leg that amended
nothing, the local commit stands and rides up with the branch's next push.

---

## State transitions

The one state this slice reasons about is the relationship between the
`Feedback Sweep Log` and the artifacts directory's last commit. It has no
storage of its own; it is recomputed from scratch on every sweep leg.

```text
                    ┌─────────────┐
   no artifacts ───▶│  no_pages   │──▶ nothing happens; proceed
                    └─────────────┘

   pages, and an amended row newer than the last artifacts commit
                    ┌─────────────┐   regenerate → remove → verify →
              ─────▶│    stale    │──▶ commit → push → refresh → record
                    └─────────────┘   ──▶ amended leg stops; clean leg proceeds

   pages, and a row that cannot be joined
                    ┌─────────────┐
              ─────▶│undeterminable│──▶ report only; decision unchanged
                    └─────────────┘

   pages, every amended row an ancestor
                    ┌─────────────┐
              ─────▶│   current   │──▶ one report line; proceed
                    └─────────────┘
```

**Convergence, stated as a property rather than assumed.** After a `stale` run
regenerates and commits, the artifacts directory's last commit is newer than
every `amended` row that existed, so the next run's join reads `current` and
does no work. Recovery from an interrupted run therefore takes exactly one
subsequent run (SC-003), and the repair is never repeated.

**The one non-convergent path is deliberate and is why `undeterminable` acts on
nothing.** This slice writes no `Feedback Sweep Log` row and FR-003 forbids a
second store, so nothing in scope can clear an unresolvable `Commit` cell. An
action keyed to that verdict would fire on every later clean sweep forever.
