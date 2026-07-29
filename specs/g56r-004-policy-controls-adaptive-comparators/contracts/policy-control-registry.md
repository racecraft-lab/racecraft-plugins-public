# Contract: Policy Control Registry

## Scope

The implementation publishes a Codex-local JSON Schema and fixture pair:

- `tests/speckit-pro/layer6-efficiency/contracts-codex-specification/policy-control-registry.schema.json`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/policy-control-registry.json`

The schema `$id` is
`https://racecraft.dev/schemas/g56r-004/policy-control-registry.schema.json`.
The registry ID is `g56r-004-policy-control-registry`.

## Required Control Set

The registry must contain exactly:

- `g56r-004-unpinned-control` with `control_kind: unpinned`
- `g56r-004-adaptive-control` with `control_kind: adaptive`
- `g56r-004-justified-high-effort-control` with
  `control_kind: justified_high_effort`

The registry rejects any fourth control, duplicate `control_kind`, missing
control, topology-changing Codex arm, or second sanctioned divergence.

## Digest Contract

Every control and the registry itself use SHA-256 over canonical JSON:

- sorted object keys
- minimal JSON separators
- UTF-8
- no NaN
- declared array order preserved
- the record's own digest member removed
- `frozen_at` included as a `Z`-suffixed UTC instant

Any hash-relevant change produces a new digest and therefore a new frozen
version.

## Frozen Bindings

Each binding to G56R-003/CAR-003 authority carries `id` and committed-bytes
`digest`. Validation recomputes the digest from the committed file and fails
closed on mismatch. The implementation may not edit frozen contracts, fixtures,
traces, score bundles, partitions, or evidence records.

## Adaptive Control Contract

The adaptive control admits only declared G56R-003 successor routes from the
bound successor freeze. The ladder is ordered and hash-relevant. The response
maps are total over `escalate`, `hold`, and `non_scorable`, using precedence:

```text
failure_code > failure_plane > retry_count > budget_threshold > terminal_state
```

Replay must cover totality, precedence, failure-plane/code consistency,
terminal-state/code consistency, no-wrap route movement, one escalation per
objective, exactly three clean passes before de-escalation, bound breach
results, and `service_reroute` non-scorability.

## Smoke Bounds

Every smoke bound declares value, unit, direction, and parent-plus-children
scope. The frozen bounds are:

- 5 non-reserved objective attempts
- 1 candidate/repetition
- 0 confirmation entries
- 1,800 seconds elapsed wall clock
- 1,000,000 raw tokens = 800,000 input + 150,000 cached input + 50,000 output
- 1,200,000 cache-read tokens
- 160,000 five-minute cache-write tokens
- 40,000 one-hour cache-write tokens

Reasoning output tokens may be reported, but do not enter the dominance or
raw-token ceiling calculation.
