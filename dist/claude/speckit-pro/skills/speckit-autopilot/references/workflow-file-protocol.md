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
| 4 | The supplied workflow resolves outside the repository root | **fail** — `workflow file is outside the authorized repository` | The root was found and the supplied path does not live under it. That is a completed evaluation with an out-of-boundary result, which is the case the check exists to catch — a different fact from branch 2, where the repository could not be found at all |
| 5 | The two references differ | **fail** — `supplied workflow does not match autopilot state workflow_file authority`, with both compared paths appended | This is a run resuming the wrong specification. Both paths are printed because the maintainer cannot otherwise tell which side to repair: re-point the run, or reclaim the state slot and let the next invocation rewrite it |

Anything reaching the end passes and reports no authority error. Both skips leave
the run indistinguishable from one that ran the comparison and passed it, because
a skip and a satisfied comparison both report no error and both exit zero. The
exit code carries the verdict, not whether the verdict was computed.

**Resolution is asymmetric.** The **supplied** workflow is resolved against the
repository root and rendered POSIX, so the right file named under a different
spelling — including one traversing a symlink — still matches. The **state**
value is compared as the literal string it holds, with no filesystem resolution,
because it is machine-written and branch 3 has already constrained its shape.
Only the supplied side has spelling freedom.

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
