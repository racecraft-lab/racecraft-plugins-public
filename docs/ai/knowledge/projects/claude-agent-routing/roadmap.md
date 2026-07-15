---
type: "speckit-project-map"
title: "Claude Code Agent Model Routing and Graceful Fallback - Map of Content"
description: "Durable project map for Claude Code Agent Model Routing and Graceful Fallback - Map of Content."
resource: "docs/ai/specs/claude-agent-routing-technical-roadmap.md"
tags: ["project-map","speckit"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "claude-agent-routing"
x-speckit-project: "claude-agent-routing"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-legacy-status: "Draft; CAR-001 ready to scaffold"
x-speckit-sources: ["docs/ai/specs/claude-agent-routing-technical-roadmap.md|26146ebe4afcdd4aa5d43ebddd448c89fd419304acccb2ffb9543ae54af7cf22"]
x-speckit-migration-sources: ["docs/ai/specs/claude-agent-routing-roadmap-MOC.md|cb1ed2d489dce7f853ff3e72661bfb3f0741f05154ce263cc46917a992032976"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
x-speckit-legacy-view: "docs/ai/specs/claude-agent-routing-roadmap-MOC.md"
x-speckit-legacy-up: "[Claude Code Agent Model Routing and Graceful Fallback Implementation Roadmap](claude-agent-routing-technical-roadmap.md)"
x-speckit-legacy-related: ["[Claude Code Agent Model Routing and Graceful Fallback PRD](../../prd-claude-agent-routing.md)"]
---
# Claude Code Agent Model Routing and Graceful Fallback - Map of Content

Source of truth: `docs/ai/specs/claude-agent-routing-technical-roadmap.md`.

## Curated map

Navigation map for evidence-backed per-agent model routing and graceful
fallback on the Claude side of the shared twelve-agent catalog.

## Epics (curated)

### Candidate and Role Contracts

Why: Establish candidate model and effort routes plus the immutable safety,
tool, mutation, and output contracts for every named agent.

- [CAR-001 Candidate Route Baseline and Role Contracts](../../../specs/claude-agent-routing-technical-roadmap.md#car-001-candidate-route-baseline-and-role-contracts)

### Capability and Treatment Evidence

Why: Probe model and effort capabilities, prove exact treatment, and define
the telemetry needed for reproducible route evaluation.

- [CAR-002 Capability Probing, Telemetry Profile, and Exact-Treatment Contract](../../../specs/claude-agent-routing-technical-roadmap.md#car-002-capability-probing-telemetry-profile-and-exact-treatment-contract)

### Evaluation Runner

Why: Run exact materialized agent policies against governed fixtures and make
quality, reliability, and resource qualification statistically reproducible.

- [CAR-003 Evaluation Runner, Fixtures, Scoring, and Statistical Analysis](../../../specs/claude-agent-routing-technical-roadmap.md#car-003-evaluation-runner-fixtures-scoring-and-statistical-analysis)

### Policy Controls

Why: Freeze unpinned, adaptive, and orchestration-changing comparators that
test whether static routing remains justified without changing the named-agent
contract.

- [CAR-004 Policy Controls and Adaptive Comparators](../../../specs/claude-agent-routing-technical-roadmap.md#car-004-policy-controls-and-adaptive-comparators)

### Fallback and Recovery

Why: Prove model absence, unsupported effort, probe failure, alias
re-pointing, bounded fallback, report-only no-safe-route behavior, and
rollback semantics.

- [CAR-005 Model Availability, Fallback, and Recovery Simulation](../../../specs/claude-agent-routing-technical-roadmap.md#car-005-model-availability-fallback-and-recovery-simulation)

### Route Resolution and Materialization

Why: Resolve the first qualified compatible route at session preflight,
materialize explicit shipped policies through a drift gate, and validate the
global override - without an installer and without mutating shipped files.

- [CAR-006 Route-policy Manifest, Materializer, Preflight, and Strict Override](../../../specs/claude-agent-routing-technical-roadmap.md#car-006-route-policy-manifest-materializer-preflight-and-strict-override)

### Role Cohorts

Why: Select one preferred route and ordered qualified fallbacks for each core
agent and the net-new optional helper after shared contracts stabilize.

- [CAR-007 Quality-critical Executor Routing](../../../specs/claude-agent-routing-technical-roadmap.md#car-007-quality-critical-executor-routing)
- [CAR-008 Structured-work Agent Routing](../../../specs/claude-agent-routing-technical-roadmap.md#car-008-structured-work-agent-routing)
- [CAR-009 Read-only Reasoning and Orchestration-support Agent Routing](../../../specs/claude-agent-routing-technical-roadmap.md#car-009-read-only-reasoning-and-orchestration-support-agent-routing)
- [CAR-010 Optional Latency-first Helper Routing and No-helper Path](../../../specs/claude-agent-routing-technical-roadmap.md#car-010-optional-latency-first-helper-routing-and-no-helper-path)

### Release Integration

Why: Reconcile payloads, prove installed skills spawn and consume results from
the named agents, verify fallback and no-helper behavior, and publish rollback
evidence before releasing defaults.

- [CAR-011 Payload, Installed Skill UAT, Fallback Proof, and Release Integration](../../../specs/claude-agent-routing-technical-roadmap.md#car-011-payload-installed-skill-uat-fallback-proof-and-release-integration)
