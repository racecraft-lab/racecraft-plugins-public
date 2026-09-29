# Fixture 01 — Synthesizer reads analyst markdown

## What this fixture proves

The Tier A consensus protocol depends on a contract between agents:
analysts emit markdown with findings + recommendation + confidence; the
synthesizer reads those outputs and produces a structured decision.
Layer 3 functional evals test each agent in isolation. Layer 6 catches
**cross-agent parsing drift** — when one agent's output format changes
in a way that breaks another agent's parsing.

This fixture sends the synthesizer the consensus protocol's Stage 2
input: the `Protocol`, `Unresolved Item`, `Routed Categories`, and
`Security Route` lines, then two disagreeing analyst responses
(codebase + domain) in the analysts' own output format, each ending
with its `security_relevant` answer. It asserts that the synthesizer
reads them and returns a Consensus Result that references the cited
options and includes the standard sections.

The item's `Security Route` is `none`. On that route a
`security_relevant: true` answer does not raise the bar to unanimity,
so the two-analyst disagreement escapes to Round 2 rather than going
straight to the Round 3 tiebreak.

## Assertions

- `consensus-synthesizer` is dispatched
- Synthesizer's response references at least one of `bcrypt` or `argon2`
- Synthesizer's response includes "agreement" and "confidence" keywords
- No subagent spawns another `Agent()`
