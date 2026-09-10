# Selective formal methods

Start with the question the developer needs answered. A model is useful when a
small description of behavior can expose costly mistakes that ordinary tests,
contracts, transactions, or database constraints do not address adequately.
Installation and a matching keyword are not reasons to enroll a feature.

## Choose the amount of verification

Ask what can go wrong, how costly that is, what ordinary checks already cover,
and what the smallest useful model would cost to write and maintain. Ground the
recommendation in the actual design and code; a retry or concurrency signal is
an invitation to inspect, not a decision.

| Recommendation | Example and reason |
|---|---|
| No model | A text-only settings change has no state protocol; a rendered UI check covers the risk. Record `none` and the reason. |
| Focused model | Lease renewal can race with cancellation across workers. Model ownership and cancellation, shared by related stories, after explaining the uncovered risk. |
| Deeper verification | Recovery must eventually release resources under explicit fairness assumptions. Discuss finite bounds, temporal support, induction obligations, and the cost of reviewing assumptions. |

For undecided scope, record `deferred` with the missing decision and return to
the existing Clarify/consensus flow in autopilot. Grill Me remains interactive.
Never turn deferral into consent. Experts can supply properties, assumptions,
types, bounds, fairness, and complete induction obligations directly.

## First useful check

For a beginner, explain a model as a small set of allowed states and moves. Use
the [counter example](../examples/formal/counter/Counter.tla): start at
zero, increment up to two, then stay there. The rule is “the count stays between
zero and two.” Its [configuration](../examples/formal/counter/Counter.cfg)
sets the bound and names the rule. No TLA+ background is needed to identify what
the check is supposed to establish.

1. Explain the initial state, allowed move, rule, and bound in those words.
2. Inspect available checkers with `formal-doctor` when that helper is available.
   Follow the selected checker's official installation guidance only with
   operator authorization. Ordinary workflows require neither Java nor Docker.
3. Preview the selected command and confirm its scope, then run the model check.
   Record the actual verdict and bounds; do not equate a successful type check
   with a successful model check.
4. In a separate example copy, change the rule to `count < Limit`. The legal
   sequence `0 → 1 → 2` now violates it. Walk through that counterexample: the
   model allows reaching two, while the intentionally changed rule forbids it.
   Restore the original rule and rerun. Do not weaken a real requirement.
5. Replace the example with the smallest behavior from the developer's design.
   Map each property to a requirement and make environmental assumptions visible.

Intermediate users can adapt an existing model and classify a failure as a
model error, property violation, unsupported feature, or insufficient budget.
Ask whether the counterexample reveals a design defect before repairing syntax.

## Choose a checker and interpret the result

Apalache provides symbolic bounded checking and documented inductive and temporal
workflows within its supported language and configuration. TLC explores an
explicit finite state space and supports temporal properties. Choose from the
model's requirements and the exact installed version, not the application's
programming language. Apalache 0.62.2 and TLC 1.7.4 are qualification targets;
only an execution-tested profile may be advertised as compatible.

- A bounded pass means no violation was found within the recorded search bounds.
- Completed finite-state exploration establishes the checked properties of that
  finite model, under its assumptions and fairness settings.
- Inductive evidence requires every declared base and step obligation. One
  completed obligation or type-check-only output is insufficient.
- Implementation-trace conformance concerns the observed runs projected through
  a tested adapter. It needs legal transitions as well as valid states. A passing
  model or replayed model counterexample alone says nothing about all code runs.

## Record explicit selection

The workflow contains one `## Formal Methods` section with one JSON block:

```json
{
  "schema_version": "1.0",
  "status": "enabled",
  "rationale": "Lease renewal and cancellation may race across workers.",
  "models": [
    {
      "id": "lease-owner",
      "behavior": "At most one current lease owner",
      "origin": "new",
      "evidence": "model"
    }
  ]
}
```

Use `origin: existing` for a maintained model and `evidence: model_and_trace`
only when implementation traces are requested. `none` has an empty model list;
`deferred` may retain candidates but activates no checks. A legacy workflow
without the section is disabled. A malformed section is an error.

The versioned `.specify/formal-methods.json` catalog describes reusable models;
it does not select them. Keep new models in `formal/<model>/`, outside archived
feature folders. Model checking can be required with `evidence: model` before any
implementation exists. Raw output and checkpoint results are not model inputs.

## Official references

- [Apalache capabilities](https://apalache-mc.org/docs/apalache/features.html)
- [Apalache installation](https://apalache-mc.org/docs/apalache/installation/index.html)
  (official distribution preferred; containers optional; document version-specific
  Java and memory requirements, verify download checksums and image digests)
- [Apalache configuration](https://apalache-mc.org/docs/apalache/config.html)
- [TLC release 1.7.4](https://github.com/tlaplus/tlaplus/releases/tag/v1.7.4)

Do not combine flags from TLC releases and nightly builds. Installation is a
separate authorized operation; the doctor and ordinary checks never acquire tools.
