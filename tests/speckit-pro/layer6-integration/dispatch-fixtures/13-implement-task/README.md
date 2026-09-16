# Fixture 13 — Implement phase → implement-executor (per task)

Verifies that the Implement phase routes individual tasks to
`implement-executor` rather than to `phase-executor`. The autopilot
phase mapping calls this out as task-level dispatch with the TDD
red-green-refactor protocol.
