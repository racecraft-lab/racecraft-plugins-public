# Fixture 14 — Analyze phase → analyze-executor

Verifies that the Analyze phase routes to `analyze-executor` (not
`phase-executor`). Analyze is a remediation-loop phase per the
autopilot phase mapping — it must run the analysis AND fix every
finding, which differs from a simple "run command, return summary"
dispatch.
