# Research: G56R-004 Policy Controls and Adaptive Comparators

## Decision: Use CAR-004 twin handoff as the mirror authority

**Rationale**: The design answer selected: "Apply CAR-004's complete twin
handoff against the current frozen G56R-003/CAR-003 bindings." This keeps
decision semantics and enforcement guards in scope while leaving existing
evaluation-contract reconciliation to G56R-012.

**Alternatives considered**: Reading CAR-003 directly would omit CAR-004's newer
decision and guard categories. Reopening frozen contracts would violate the
feature boundary and constitution simplicity rules.

## Decision: Author additive Codex-local registry and comparison schemas

**Rationale**: The selected answer says: "Create Codex-local standalone
contracts with Codex IDs." The planned schemas use
`https://racecraft.dev/schemas/g56r-004/` `$id` values and mirror CAR-004's
record shapes, required members, closed enums, frozen numerics, decision
semantics, and guards.

**Alternatives considered**: Extending frozen G56R-003/CAR-003 schemas would
make the freeze mutable. Python-only validation would lose the schema and digest
surface reviewers need.

## Decision: Keep exactly three Codex controls

**Rationale**: The selected control-set answer says: "Freeze unpinned,
adaptive, and justified-high-effort; treat automatically spawned child work as a
modifier." The sole sanctioned divergence is the category-3 `control_kind` enum
value `justified_high_effort` replacing CAR-004 `orchestration_changing`.

**Alternatives considered**: A topology-changing Codex arm contradicts the
G56R-004 roadmap. Four controls violate the closed-at-three guard.

## Decision: Bind frozen G56R-003/CAR-003 evidence by ID and digest

**Rationale**: The plan binds the already-qualified high-effort route
`g56r-003-route-phase-executor` at model `gpt-5.5`, effort `xhigh`, successor
freeze `sha256:734672cea5a83e5b8f296ee604f7cb8d93e0a5296a3f864b873fe78bfe518f1e`,
and route-evidence digest
`sha256:f01ff64ca3d17b40db8ca802dd6501e62d91c4c161d01a94879c156f90eb09e4`.
Every frozen binding must be recomputed from committed bytes.

**Alternatives considered**: Copying route names without digest binding would not
prove the exact frozen evidence. Editing frozen artifacts to restore agreement
is forbidden.

## Decision: Re-derive mirror categories 1-6 and execute categories 7-8

**Rationale**: The CAR-004 handoff states that "Categories 1 through 6 are
derived, never transcribed." G56R-004 therefore derives those categories from
committed Codex schemas, frozen instances, and partition entries, then compares
both directions. The 19 category-7 decisions and 2 category-8 guards are
covered by executable Layer 4 checks instead of prose.

**Alternatives considered**: Prose-only parity or warning-only parity would let
the handoff drift silently.

## Decision: Implement adaptive semantics as a deterministic replay engine

**Rationale**: Adaptive behavior binds to frozen observed members: terminal
state, failure plane, failure code, retry count, and raw-token/duration budget
thresholds. Replay must prove total response maps, precedence
`failure_code > failure_plane > retry_count > budget_threshold > terminal_state`,
plane/code consistency, terminal/code consistency, ordered no-wrap movement,
three-clean-pass de-escalation, bound breach outcomes, and service-reroute
non-scorability.

**Alternatives considered**: Runtime route discovery would make the control
identity unstable. Copying Claude route literals would not prove a Codex
treatment.

## Decision: Mirror comparison semantics exactly

**Rationale**: The design answer says: "Keep the same gate-first order, eight
dimensions, direction rules, confidence method, 10% relative margins, and
inconclusive/no-verdict handling." G56R-004 uses eligibility floors before any
dominance verdict, environment-independent Pareto comparison, materiality
margin only on input tokens, cached input tokens, output tokens, and duration,
and no weights or scalar score.

**Alternatives considered**: Codex-specific margins would break platform
comparability. Weighted scores reopen the settled no-weights decision.

## Decision: Register reserved G56R-011 partition now

**Rationale**: The selected answer says: "Create a content-addressed reserved
partition entry owned by G56R-004 and fail any replay or smoke row that consumes
one of its objectives." The same guard runs at deterministic replay admission
and at smoke plan/seal time.

**Alternatives considered**: A prose reservation depends on reviewers catching
mistakes. Deferring the partition lets post-outcome selection influence the
final comparison.

## Decision: Use replay plus operator-only smoke sealing

**Rationale**: Deterministic replay is the automated gate. Each control has one
bounded, non-scored ChatGPT-sign-in smoke requirement, but live execution
requires explicit operator authorization and cannot be replaced by API-key
execution. Produced evidence, not dispatch intent, proves exact treatment.

**Alternatives considered**: Replay-only moves integration risk downstream.
Scored campaigns would produce outcome-bearing evidence before G56R-011.

## Decision: Reuse existing Layer 4 test owners

**Rationale**: `suite-manifest.json` already owns durable Layer 4 tests for
policy control contracts, control-comparison dominance, and twin-handoff
completeness. Updating those owners keeps the suite manifest authoritative and
avoids spec-ID-coupled filenames.

**Alternatives considered**: Adding G56R-004-named tests would violate the
repository filename guidance. A separate live smoke test owner would incorrectly
pull operator-only work into the default suite.

## Decision: Keep one reviewable vertical slice

**Rationale**: The roadmap and design concept start from `estimated_loc: 235`,
`suggested_slices: 1`, and `status: ok`. The concrete plan keeps the work in 12
declared file operations with three logical Python helper modules and no
install-facing runtime surface.

**Alternatives considered**: Splitting before the concrete estimator would
separate mutually dependent contract, replay, comparison, and guard semantics.
If the estimator returns over budget, split vertically by capability before
`tasks.md`.
