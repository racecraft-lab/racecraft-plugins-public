# Data Model: G56R-005

## FixturePolicy

- `schema_version`: constant `1.0.0`
- `policy_id`: stable fixture identifier
- `agent`: role identity and role class
- `preferred_route`: first RouteCandidate
- `fallback_routes`: ordered list of RouteCandidate
- `strict_override`: absent, compatible, or incompatible override evidence
- `service_reroute`: optional ServiceRerouteEvidence
- `helper_state`: required/optional helper availability and optional no-helper continuation evidence
- `fake_home`: seed state and harness-created temporary root requirement
- `budgets`: HarnessBudget

## RouteCandidate

- `route_id`, `model`, `effort`
- local capability evidence
- exact invocation availability probe outcome
- treatment probe outcome
- non-route treatment digest
- explicit declaration source; inherited values are invalid

## DiagnosticReason

Closed Codex-local reason vocabulary ordered per spec:

1. `model_absent`
2. `unsupported_effort`
3. `capability_discovery_unavailable`
4. `availability_probe_failed`
5. `treatment_probe_failed`
6. `non_route_treatment_mutation`

Additional fail-closed diagnostics include loop, unqualified-adjacent route, generic substitution, inherited model, inherited effort, optional-helper degradation, fallback exhaustion details, and budget breach evidence.

## TerminalOutcome

Exactly one terminal outcome is emitted last:

- `qualified_route`
- `strict_override_rejected`
- `bounded_retry_exhausted`
- `time_budget_exhausted`
- `fanout_budget_rejected`
- `context_budget_rejected`
- `cancellation_observed`
- `escalation_rejected`
- `no_safe_route`

Fallback exhaustion is represented as evidence/details under `no_safe_route`.

## ServiceRerouteEvidence

- `origin`: constant `service`
- `observed_target_route`
- `approval`: `approved` or `unapproved`
- `approval_evidence`
- `scoring_effect`

Approved evidence must target a declared route or declared model/effort-only mutation and preserve the non-route treatment digest.

## FakeHomeState

- `state_id`: SHA-256 over canonical manifest bytes
- `manifest`: sorted fake-home-relative path records
- each record: `path`, `sha256`, `mode`, `role_classification`

Excluded from identity: absolute temp roots, mtimes, inodes, timestamps, and host-specific paths.

## RecoveryRecord

Closed canonical JSON evidence:

- `pre_state_id`, `final_state_id`
- sorted `staged_actions`, `applied_actions`, `rolled_back_actions`, `cleanup_actions`
- sorted `cleanup_errors`
- `rollback_outcome`
- `writes_state`
- `manual_remediation`
- `terminal_outcome`

`writes_state=false` is allowed only when the exact pre-state is restored or no managed file was touched.

## HarnessBudget

- `max_retries`
- `max_elapsed_units`
- `max_fanout`
- `max_context_units`
- `cancellation_point`
- `max_escalations`

The harness records deterministic counters rather than host wall-clock metadata.
