# Fixture 16 — Gate validation → gate-validator

Verifies that gate validation between phases dispatches the dedicated
`gate-validator` agent, not a phase-executor. This is the agent that
runs the structural marker checks and metric thresholds described in
`references/gate-validation.md`.
