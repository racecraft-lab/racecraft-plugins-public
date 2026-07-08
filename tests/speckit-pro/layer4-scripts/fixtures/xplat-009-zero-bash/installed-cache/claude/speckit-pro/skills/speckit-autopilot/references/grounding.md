# Grounding Contract

Shared source contract:
`speckit-pro/skills/speckit-autopilot/references/grounding.md`

Companion to [`capability-discovery.md`](./capability-discovery.md). Discovery
decides *which* capability to use; grounding guarantees that every fact an answer
asserts actually *came from* a capability result, not from model memory. Open
discovery is only safe when paired with grounding: widening what a component can
reach must not widen what it can fabricate.

Applies to every component that emits external free-text facts — all subagents
that assert findings, and the orchestrator's own decision and PR-body output.
Mechanical components whose output is an exit code or a verbatim aggregation of
already-grounded inputs are exempt (see `capability-discovery.md` §Capability
Boundaries by Role).

## G1 — Ground every external claim

Every claim about the world outside the model's own reasoning — library
behavior, API shapes, file contents, command output, project state, third-party
facts — must trace to a result returned by an actually-invoked capability
(a tool call, an MCP result, an installed skill's output, or a read of a
repository file). The unit is the individual claim, not the answer as a whole.

A claim with no invoked-capability result behind it must not be asserted as fact.

## G2 — Abstain when nothing grounds it

When no available capability can ground a needed claim, say so instead of
asserting it. Reuse the `capability-discovery.md` fallback-disclosure block and
state plainly that the information is not available. "I could not confirm X" is a
correct, valuable answer; a confident unverifiable X is a defect.

## G3 — Separate grounded fact from inference

Distinguish a grounded fact from a model-prior inference in the output. Mark
inferred or unverified statements explicitly (e.g. a leading `[inference]`),
and never assign `high` confidence to a claim that is not grounded in an invoked
result. High confidence requires grounding.

## G4 — Cite in the evidence note

Extend — do not duplicate — the `capability-discovery.md` Evidence Output note.
Its `Evidence:` segment enumerates the per-claim citations: each external claim
names the capability result and a locator (URL, `file:line`, command, or
returned record) that a reader or an automated check can map back to a real
invocation.

## G5 — The orchestrator grounds its own output

The orchestrator binds itself, not only the subagents it dispatches. Facts in
its gate decisions, consensus synthesis, and generated PR bodies obey G1–G4. A
subagent's returned summary counts as a capability result the orchestrator
received and may cite; a fact the orchestrator introduces on its own must have
its own grounding.

## Verifiability

The contract is written to be checkable from a run transcript: every cited claim
must map to a real capability invocation in that transcript, and a cited result
that has no corresponding invocation is a grounding failure, not a pass. This is
the contract a Layer-7 integration fixture is meant to assert for both subagent
and orchestrator output — a fixture that cites a capability with no matching
invocation must be reported ungrounded (the executable proof, including that
negative control, ships in the companion change that adds the grounding-fixture
class).
