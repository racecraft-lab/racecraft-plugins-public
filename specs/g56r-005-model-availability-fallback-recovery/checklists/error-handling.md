# Error Handling Checklist: G56R-005 Model Availability, Fallback, and Recovery Simulation

**Purpose**: Validate fail-closed diagnostics, terminal outcomes, and recovery error reporting.
**Created**: 2026-08-22
**Feature**: [spec.md](../spec.md)

## Route Failure Semantics

- [x] CHK001 Preferred model absence, unsupported effort, discovery unavailability, availability probe failure, treatment probe failure, and non-route treatment mutation each have distinct diagnostics.
- [x] CHK002 Diagnostics are ordered by the Resolution Ordering Contract before the terminal outcome.
- [x] CHK003 Fallback exhaustion is represented as evidence or terminal details under `no_safe_route`, not as a second terminal outcome.
- [x] CHK004 Incompatible strict override rejects before fallback evaluation or writes.
- [x] CHK005 Loop detection occurs only when the sequential walk reaches an already attempted route.

## Harness Bounds

- [x] CHK006 Retry, time, fan-out, context, cancellation, and escalation breaches terminate deterministically.
- [x] CHK007 Cancellation after managed-file mutation triggers only bounded recovery before terminal reporting.
- [x] CHK008 Human-in-the-loop escalation and recursive agent execution are rejected in simulation.

## Recovery Errors

- [x] CHK009 Atomic no-write is reported only when no managed file was touched.
- [x] CHK010 Rollback failure reports `writes_state=true` and deterministic manual remediation.
- [x] CHK011 Cleanup errors are sorted and cannot mask rollback or terminal outcome.
