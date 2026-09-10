# Check observed implementation traces

Select `evidence: model_and_trace` only when the modeled behavior needs this
additional evidence. Keep ordinary unit, integration, type, and concurrency tests.
Put that selection on the model entry in the workflow's `## Formal Methods`
section, not in `.specify/formal-methods.json`. The catalog defines the reusable
trace contract below; it does not enroll the feature.
A passing finite trace proves that those observed actions and states form a
possible execution of the selected model. It does not prove every implementation
run, unobserved behavior, or implementation liveness.

## Contract and test ordering

During Plan, the bounded author and parent agree on the observable state fields,
named actions, hidden state, atomic capture points, and requirement mapping.
Tasks includes the implementation, emitter, adapter tests, and final/Post checks.
Declare the source, configuration, producing tests, and adapter in
`implementation_inputs`. The trace contract contains:

```json
{
  "format": "itf",
  "paths": [".specify/formal-traces/counter/observed.itf.json"],
  "projection": {"count": "count"},
  "actions": {"increment": "Increment", "hold": "Hold"},
  "init": "Init",
  "next": "Next",
  "adapter_test": "tests/counter_trace_test.py",
  "max_states": 20
}
```

Projection keys are native model variables; values are ITF variables. Action
keys are observed event names; values are native action operators. Init and Next
must be the selected model's predicates. A reviewed TLC SPECIFICATION may include
fairness; the trace's Init/Next still describes its finite observed transitions.
For Quint use its native action names, such as `init` and `step`.

The producing test captures a binding **before** executing the implementation,
then validates and stamps its actual ITF output. Both operations use the same
installed runner package, available on `PYTHONPATH` from the plugin root:

```python
from pathlib import Path
from speckit_pro_runner.formal.traces import binding, write_trace

root = Path(WORKFLOW_ROOT).resolve()
before = binding(root, "counter")
observed = exercise_real_counter_and_capture_itf()
write_trace(root, "counter", ".specify/formal-traces/counter/observed.itf.json",
            observed, before)
```

The example function represents the application's real test, not a model replay.
The test must fail if execution or adapter assertions fail. `write_trace` validates
ITF shape and rejects inputs changed during capture. Subsequent source, model, or
projection changes invalidate the trace. Run these tests in the project's existing
test slots, then run `formal-check` for `final` or `post`. A preview reports each
trace query and rejects missing or stale input without writing state.

Raw traces and checker output are ignored. Commit the model/configuration,
implementation and adapter changes, plus compact evidence and workflow bookkeeping.
A fresh checkout regenerates traces by running its tests before checking them.

## Lossless data and concurrency

The qualified format follows Apalache/Quint ITF. Encode every integer as
`{"#bigint":"9007199254740993"}`; never pass it through a JavaScript `number`.
Booleans, printable strings, lists/tuples, sets, maps, and nonempty records have
explicit supported encodings. Floating point, null, unsupported tags/variants,
duplicate JSON keys, missing variables, unknown actions, and loop traces cannot
pass. Normalize application-specific values only through an explicitly reviewed
projection. Do not silently round values or discard events.

Each state has `#meta.index`, consecutive from zero. The initial state has no
action; later states name the action that produced them. Capture the event and
resulting state atomically. Preserve actual ordering across concurrent operations;
wall-clock sorting cannot invent a legal sequence. A Swift actor must capture
both without an intervening `await`, because actors can reenter across suspension.

## Three executable examples

`examples/formal/counter-traces/` contains a shared model and real implementations:

| Language | Producer | Existing toolchain integration |
|---|---|---|
| Python | `counter.py` | Run with Python 3.11+; JSON uses strict encoding and decimal integer strings. |
| TypeScript | `counter.mts` | Run the project's TypeScript type checker, then Node.js 24 with erasable syntax. Runtime stripping does not typecheck. |
| Swift | `CounterTrace.swift` | Compile using Swift 6 with strict concurrency; the qualified test executes the source with `swift`. Actor snapshots use Codable decimal strings. |

All three produce `0, 1, 2, 2`. The qualification changes the real increment from
one to two, producing `0, 2, 2, 2`. Every state still satisfies the bound, while
the full transition check must reject the jump. It also exercises integers beyond
JavaScript's exact-number range, malformed/stale receipts, and a model where
checking adjacent states separately would lose the consistency of hidden state.

The runner first checks the original selected properties. It then asks the native
checker whether the **entire** observed sequence is reachable through original
Init, original Next, the declared action, and the projected states. Only a complete
witness becomes a conformance pass. Timeouts, partial witnesses, empty initial
states, unsupported models, or ordinary typechecking do not qualify.

Sources: [ITF ADR-015](https://apalache-mc.org/docs/adr/015adr-trace.html),
[Python JSON](https://docs.python.org/3.11/library/json.html),
[Node.js TypeScript execution](https://nodejs.org/docs/latest-v24.x/api/typescript.html),
and [Swift concurrency](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/).
