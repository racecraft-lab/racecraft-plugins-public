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
