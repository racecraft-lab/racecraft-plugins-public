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
