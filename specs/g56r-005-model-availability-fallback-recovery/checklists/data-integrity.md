# Data Integrity Checklist: G56R-005 Model Availability, Fallback, and Recovery Simulation

**Purpose**: Validate canonical fixtures, attribution, eligibility, and review evidence.
**Created**: 2026-08-22
**Feature**: [spec.md](../spec.md)

## Canonical Records

- [x] CHK001 Route reports and Recovery Records use sorted-key canonical JSON.
- [x] CHK002 Deterministic arrays are sorted where order is not semantically defined.
- [x] CHK003 Replay of the same fixture inputs three consecutive times is byte-identical.
- [x] CHK004 Fixture policies require local model and effort declarations; inherited model or effort is rejected.

## Attribution And Eligibility

- [x] CHK005 Service reroute attribution is stored separately from plugin-authored diagnostics.
- [x] CHK006 Approved service reroutes preserve eligibility only when the final route is otherwise qualified and non-route treatment digest is unchanged.
- [x] CHK007 Unapproved service reroutes are ineligible even if they point at an otherwise valid route.
- [x] CHK008 Optional-helper degradation uses helper counters separate from required-route counters.

## Coverage And Traceability

- [x] CHK009 Each required scenario coverage row maps to at least one fixture or acceptance case.
- [x] CHK010 Each major FR/SC maps to fixture output and review-packet evidence.
- [x] CHK011 PR evidence states live model/service availability was not tested and production routing/payload/version behavior was not modified.
- [x] CHK012 Fixture policy binds a canonical bundled-source roster identity, classifies the helper separately, and fails closed for re-review on roster drift without hard-coding the roadmap's future count.
