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
