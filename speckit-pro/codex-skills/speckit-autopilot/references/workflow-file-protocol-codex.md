# Workflow File Update Protocol — Codex

After every phase, the parent session updates designated sections in the
workflow file so the workflow file stays the authoritative record. This is
the Codex-specific mirror of `../../skills/speckit-autopilot/references/workflow-file-protocol.md` — same protocol, Codex-specific commit primitives (parent session direct `apply_patch`).

## Per-Phase Section Updates

After EVERY phase, update these sections in the workflow file:

| Phase | Sections to Update |
| --- | --- |
| **All** | Status table: Pending → Complete with summary notes |
| **Specify** | Specify Results table, Files Generated checkboxes |
| **Clarify** | Clarify Results table (session focus, questions, outcomes) |
| **Plan** | Plan Results table (artifact status) |
| **Checklist** | Checklist Results table, Addressing Gaps section |
| **Tasks** | Tasks Results table (total, phases, parallel, coverage) |
| **Analyze** | Analysis Results table (ID, severity, issue, resolution) |
| **Implement** | Implementation Progress, Post-Implementation Checklist, Success Criteria |

## Constitution + Consensus Log

Also update the **Constitution Validation table** after Specify (initial) and
Implement (final).

If consensus was used during a phase, add entries to the **Consensus
Resolution Log** with `Round`, `Routed Categories`, `Outcome`, and
`Analysts Used` columns.

## Feedback Sweep Log

The pull-request feedback sweep keeps its own table in the workflow file, under
a `Feedback Sweep Log` heading, with this header:

```text
| # | Comment ID | Surface | Author | Class | Disposition | Commit | CRL # |
```

One row per **handled** comment, meaning one that was assigned a class. A
comment the trust filter dropped, one the self-reply rule dropped, and one whose
consensus round returned no answer each take no class, so none of them gets a
row. The row carries the comment id, the surface it was read from, its author,
its class, its disposition, and the commit that answered it.

The `Disposition` cell escapes any pipe as `\|` and any newline as a line break.
Table readers here split rows on the bare pipe with no escape handling, so one
unescaped pipe would shift `CRL #` out of its column and make the consensus link
read the wrong cell; the comment id sits ahead of the disposition, so the skip
key survives whatever that prose contains. What fills the cell is the
classifier's `reason`, at most 512 bytes as UTF-8 and carrying neither a pipe
nor a newline, after it crosses the redaction surface's `log_row` leg: the
leg's output is the only form that reaches the cell, and the escaping is
applied last, to that output. An author that cannot be resolved is recorded
explicitly rather than left blank, because a blank cell is indistinguishable
from a cell nobody wrote.

Every amendment additionally produces a Consensus Resolution Log row, and
`CRL #` names it by number. The link runs both ways at no extra column, because
that row's item cell names the comment id; see
[`consensus-protocol.md`](../../skills/speckit-autopilot/references/consensus-protocol.md)
§Logging for the `Sweep` row type.

**The sweep creates the table** when the workflow file carries none, writing the
heading and the header row itself. The scaffold workflow template ships neither
and is not changed to ship them. **Creation and that run's first rows are one
write in one bookkeeping commit**, never a commit of their own ahead of it: a
commit carrying an empty table reads as "nothing has been handled", which is
indistinguishable from a genuine clean first run, and that is the one direction
the skip key cannot tolerate.

**Placement matches the anchor's level rather than assuming one**, because the
anchor is neither guaranteed to exist nor guaranteed to sit at `###`. Match
`Consensus Resolution Log` by its heading text at any level and write
`Feedback Sweep Log` at the **same** level, so the two are siblings; with no
anchor, append `## Feedback Sweep Log` at the end of the file. Of the 69
workflow files committed in this repository, 33 carry no Consensus Resolution
Log heading at all; of the 36 that do, 31 write it at `###` and 5 at `##`. A
fixed `###` under a `##` anchor would nest the sweep log inside the consensus
section, which reads as subordinate to it and is not what the `CRL #`
cross-reference describes.

**Rows number sequentially.** The leading `#` column starts at 1 and each new
row takes one more than the highest number already in the table, so numbering
continues across runs and never restarts.

**This table is the sole store, with no state-file mirror**, deliberately,
following the `Draft PR` row's rule in the [Claude protocol
reference](../../skills/speckit-autopilot/references/workflow-file-protocol.md).
A second sink would introduce exactly the status-versus-evidence drift the Step
1.1 coverage guard and the tree-wide CI gate already fail on. It is also what
makes the record durable across archiving, and what lets a re-run read its own
skip set back: the sweep skips any comment id that already carries a row here,
and it reads that set from this table and nowhere else.

## `workflow_file` State Authority

`autopilot-state.json.workflow_file` names the workflow a run is authorized
against. The Step 1.1 coverage guard compares the supplied workflow to that value
and reports a disagreement as `workflow_authority_errors`, which is registered in
the `status-evidence` rule and so fails the guard rather than merely printing.
This one is **state-file-wins**, the opposite direction from the workflow-file
precedence that governs the Workflow Overview status table.

Five branches, in this order, because an earlier skip must win over a later
failure:

1. **No `workflow_file` key in the state** — skip. A state naming no workflow
   asserts no authority. Key membership decides this rather than a null test, so
   an explicitly nulled field stays malformed instead of becoming a silent
   opt-out.
2. **No repository root resolves from the state file's location** — skip. Without
   a root there is no boundary to resolve the supplied workflow against.
3. **Malformed value** — not a string, empty, whitespace-only, or not a
   normalized repository-relative path. Fails with `autopilot state
   workflow_file is not a normalized repository-relative path`. The value is
   machine-written, so a shape it should never take means the state is
   untrustworthy. Whitespace-only is checked explicitly, because a run of spaces
   is a valid POSIX path part.
4. **Supplied workflow resolved against the repository root** — two outcomes.
   Outside the root fails with `workflow file is outside the authorized
   repository`; the root was found and the path does not live under it, which is
   a different fact from branch 2. A path resolution cannot traverse at all, such
   as a symlink loop, skips instead: that is an absence of information, not an
   out-of-boundary result. Through this guard's own call path that outcome is
   defensive rather than reachable, because the supplied workflow is read before
   the comparison and an untraversable path has already raised there. It exists
   so the helper cannot raise for a caller that reads in a different order.
5. **The two references differ** — fails with `supplied workflow does not match
   autopilot state workflow_file authority`, both compared paths appended, so the
   maintainer can tell which side to repair.

Anything reaching the end passes. All three skips — branches 1 and 2, and the
unresolvable-path outcome inside branch 4 — are indistinguishable from a pass at
the exit code, which carries the verdict rather than whether it was computed.

When reading corpus evidence, note that the report always carries
`workflow_authority_errors`. An empty value proves only that the repaired guard
is running, never that the comparison ran; presence separates repaired code from
unrepaired code, where the key is absent entirely. To prove a comparison ran,
vary an input and show the verdict change.

Resolution is **asymmetric**: the supplied workflow is resolved against the
repository root and rendered POSIX, so the right file named absolutely or
relatively from any working directory still matches, while the state value is
compared as the literal string it holds. Resolution follows symlinks, so what is
compared is where the supplied path **lands**, not how it was spelled: a workflow
named through a symlink reports a branch 5 mismatch against its target even when
the state names the link, and a link resolving outside the repository reaches
branch 4. Keep workflow files and the state that names them as real paths inside
one repository.

The comparison itself is **byte-exact**, with no case folding and no `samefile`,
because byte-exact is the only rule returning the same verdict on a
case-insensitive filesystem and a case-sensitive one.
