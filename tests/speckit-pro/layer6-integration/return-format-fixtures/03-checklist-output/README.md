# Fixture 03 — Checklist-executor cross-agent parsing

Verifies that `checklist-executor`'s output format includes the
sections the orchestrator depends on (domain + gap state) so the
orchestrator can decide whether to advance to the next gate. This is
the Layer 6 cross-agent parsing test for the checklist phase.
