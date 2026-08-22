# Contract: G56R-005 Fallback Recovery Simulation

## Inputs

The replay harness accepts one fixture case with:

- a `FixturePolicy`
- a canonical bundled-source roster and its bound identity
- local capability evidence
- exact invocation and treatment probe outcomes
- optional service reroute evidence
- helper availability and no-helper continuation evidence
- fake-home seed state
- harness budgets

## Processing Contract

1. Canonicalize the current bundled-source roster, classify `autopilot-fast-helper.toml` as the sole optional-helper definition, and fail closed if its identity differs from the reviewed fixture binding.
2. Reject incompatible strict override before fallback evaluation or writes.
3. Walk the preferred route, then fallbacks in fixture order.
4. Detect loops only when the walk reaches a previously attempted route.
5. For each reached route, emit applicable plugin reasons in the fixed Resolution Ordering Contract order.
6. Keep service reroute attribution outside the plugin reason sequence.
7. Apply fake-home writes only beneath a harness-created `<fake_home_root>/.codex/agents`.
8. After managed files are touched, cancellation or failure triggers rollback and bounded cleanup.
9. Emit exactly one terminal outcome last.

## Output Contract

The route report is canonical JSON with sorted keys and deterministic arrays. It contains:

- policy and case identifiers
- source-roster identity and required/optional classification
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
