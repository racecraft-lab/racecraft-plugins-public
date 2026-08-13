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
