# Fixture 01 — Synthesizer reads analyst markdown

## What this fixture proves

The Tier A consensus protocol depends on a contract between agents:
analysts emit markdown with findings + recommendation + confidence; the
synthesizer reads those outputs and produces a structured decision.
Layer 3 functional evals test each agent in isolation. Layer 7 catches
**cross-agent parsing drift** — when one agent's output format changes
in a way that breaks another agent's parsing.

This fixture provides hand-crafted analyst outputs (codebase + domain)
and asserts that the synthesizer can read them and emit a decision
artifact that references the cited options and includes the standard
sections.

## Assertions

- `consensus-synthesizer` is dispatched
- Synthesizer's response references at least one of `bcrypt` or `argon2`
- Synthesizer's response includes "decision" and "rationale" keywords
- No subagent spawns another `Agent()`
