# Fixture 03 — Redelegation chain (multi-hop)

## What this fixture proves

This is the core L7 test: the orchestrator must hand off to a subagent,
**regain control when that subagent returns**, then dispatch a different
subagent based on what was returned. Single-hop tests cannot prove this.

Specifically, this fixture exercises:

1. orchestrator → `clarify-executor` (hop 1)
2. clarify-executor returns a read-only Clarify Question Set
3. orchestrator answers/applies accepted clarifications in the main context
4. orchestrator (back in control) → analyst(s) for unresolved tagged items (hop 2)
5. analysts return findings
6. orchestrator (back in control) → `consensus-synthesizer` (hop 3)

If the orchestrator stayed inside the clarify-executor's context (no
return), if clarify-executor tried to edit artifacts itself, or if
clarify-executor itself spawned analysts against the parent-owned
no-nested-Agent policy, the chain is broken. This fixture detects those
failure modes.

For a live capture, `prompt.txt` names the committed `sample-spec.md` next to
this README; it is the required fixture input.
