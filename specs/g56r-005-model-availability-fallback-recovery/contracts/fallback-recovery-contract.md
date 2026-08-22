# Contract: G56R-005 Fallback Recovery Simulation

## Inputs

The replay harness accepts one fixture case with:

- a `FixturePolicy`
- local capability evidence
- exact invocation and treatment probe outcomes
- optional service reroute evidence
- helper availability and no-helper continuation evidence
- fake-home seed state
- harness budgets

## Processing Contract

1. Reject incompatible strict override before fallback evaluation or writes.
2. Walk the preferred route, then fallbacks in fixture order.
3. Detect loops only when the walk reaches a previously attempted route.
4. For each reached route, emit applicable plugin reasons in the fixed Resolution Ordering Contract order.
5. Keep service reroute attribution outside the plugin reason sequence.
6. Apply fake-home writes only beneath a harness-created `<fake_home_root>/.codex/agents`.
7. After managed files are touched, cancellation or failure triggers rollback and bounded cleanup.
8. Emit exactly one terminal outcome last.

## Output Contract

The route report is canonical JSON with sorted keys and deterministic arrays. It contains:

- policy and case identifiers
- ordered plugin diagnostics
- service reroute attribution
- route qualification result
- scoring eligibility result
- optional-helper counters
- budget counters
- terminal outcome
- optional Recovery Record

The output must exclude absolute temporary roots, mtimes, inodes, timestamps, and host-specific paths.

## Non-Goals

- No production resolver wiring
- No real Codex agent installation
- No payload, version, release, checkpoint, or resume behavior changes
- No live model or service availability claim
- No Claude fallback behavior rewrite or shared resolver extraction
