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

For every phase, also append its `knowledge_use_receipt` as JSON that validates
against `knowledge-use-receipt.schema.json`: `receipt_version`, snapshot ID,
bounded query, selected concept paths/IDs/hashes, verified source paths/hashes,
producer skill and actual agent when applicable, purpose, and the decision or
output that consumed them. Never write `none`. For an absent bundle, append
this complete shape (replace phase-specific values as appropriate):

```json
{
  "receipt_version": "1.0",
  "snapshot_id": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "query": "current spec and phase decision",
  "selected_concepts": [],
  "verified_sources": [],
  "producer": { "skill": "speckit-autopilot", "agent": "phase-executor" },
  "purpose": "Ground the phase decision in reviewed project knowledge.",
  "result": "No reviewed project knowledge selected."
}
```

When a present bundle returns no selections, keep both arrays empty but record
its actual snapshot rather than the empty-bundle snapshot.

Candidate summaries may be linked from the workflow, but staged candidate
packets and the canonical knowledge bundle are not workflow state authorities.

## Constitution + Consensus Log

Also update the **Constitution Validation table** after Specify (initial) and
Implement (final).

If consensus was used during a phase, add entries to the **Consensus
Resolution Log** with `Round`, `Routed Categories`, `Outcome`, and
`Analysts Used` columns.
