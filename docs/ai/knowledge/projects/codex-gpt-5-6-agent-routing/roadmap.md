---
type: "speckit-project-map"
title: "Codex Agent Model Routing and Graceful Fallback - Map of Content"
description: "Durable project map for Codex Agent Model Routing and Graceful Fallback - Map of Content."
resource: "docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md"
tags: ["project-map","speckit"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "codex-gpt-5-6-agent-routing"
x-speckit-project: "codex-gpt-5-6-agent-routing"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-legacy-status: "Draft; G56R-001 ready to scaffold"
x-speckit-sources: ["docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md|0d2b7feb13367b077c3cc54966e15a7ad669119bd64ef36ada7a7dfba9039f40"]
x-speckit-migration-sources: ["docs/ai/specs/codex-gpt-5-6-agent-routing-roadmap-MOC.md|0e6be00119a4fc9c8e914a81b6fc10e571ab5974ea33dc552dcc6b124f40b5f0"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
x-speckit-legacy-view: "docs/ai/specs/codex-gpt-5-6-agent-routing-roadmap-MOC.md"
x-speckit-legacy-up: "[Codex Agent Model Routing and Graceful Fallback Implementation Roadmap](codex-gpt-5-6-agent-routing-technical-roadmap.md)"
x-speckit-legacy-related: ["[Codex Agent Model Routing and Graceful Fallback PRD](../../prd-codex-gpt-5-6-agent-routing.md)"]
---
# Codex Agent Model Routing and Graceful Fallback - Map of Content

Source of truth: `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md`.

## Curated map

Navigation map for evidence-backed per-agent model routing and graceful fallback.

## Epics (curated)

### Candidate and Role Contracts

Why: Establish candidate model and effort routes plus the immutable safety,
tool, mutation, and output contracts for every named agent.

- [G56R-001 Candidate Route Baseline and Role Contracts](../../../specs/codex-gpt-5-6-agent-routing-technical-roadmap.md#g56r-001-candidate-route-baseline-and-role-contracts)

### Capability and Treatment Evidence

Why: Discover model and effort capabilities, prove exact treatment, and define
the telemetry needed for reproducible route evaluation.

- [G56R-002 Capability Discovery, Telemetry Profile, and Exact-Treatment Contract](../../../specs/codex-gpt-5-6-agent-routing-technical-roadmap.md#g56r-002-capability-discovery-telemetry-profile-and-exact-treatment-contract)

### Evaluation Runner

Why: Run exact materialized agent policies against governed fixtures and make
quality, reliability, and resource qualification statistically reproducible.

- [G56R-003 Evaluation Runner, Fixtures, Scoring, and Statistical Analysis](../../../specs/codex-gpt-5-6-agent-routing-technical-roadmap.md#g56r-003-evaluation-runner-fixtures-scoring-and-statistical-analysis)

### Policy Controls

Why: Freeze unpinned and adaptive comparators that test whether static routing
remains justified without changing the named-agent contract.

- [G56R-004 Policy Controls and Adaptive Comparators](../../../specs/codex-gpt-5-6-agent-routing-technical-roadmap.md#g56r-004-policy-controls-and-adaptive-comparators)

### Fallback and Recovery

Why: Prove model absence, unsupported effort, treatment failure, bounded
fallback, atomic no-write, rollback, and no-safe-route behavior.

- [G56R-005 Model Availability, Fallback, and Recovery Simulation](../../../specs/codex-gpt-5-6-agent-routing-technical-roadmap.md#g56r-005-model-availability-fallback-and-recovery-simulation)

### Resolution and Installation

Why: Resolve the first qualified compatible route, materialize an explicit
agent policy, install the full matrix atomically, and keep overrides strict.

- [G56R-006 Capability-aware Resolver, Materializer, Installer, and Strict Override](../../../specs/codex-gpt-5-6-agent-routing-technical-roadmap.md#g56r-006-capability-aware-resolver-materializer-installer-and-strict-override)

### Role Cohorts

Why: Select one preferred route and ordered qualified fallbacks for each core
agent and the optional helper after shared contracts stabilize.

- [G56R-007 Quality-critical Executor Routing](../../../specs/codex-gpt-5-6-agent-routing-technical-roadmap.md#g56r-007-quality-critical-executor-routing)
- [G56R-008 Structured-work Agent Routing](../../../specs/codex-gpt-5-6-agent-routing-technical-roadmap.md#g56r-008-structured-work-agent-routing)
- [G56R-009 Read-only Reasoning and Orchestration-support Agent Routing](../../../specs/codex-gpt-5-6-agent-routing-technical-roadmap.md#g56r-009-read-only-reasoning-and-orchestration-support-agent-routing)
- [G56R-010 Optional Helper Routing and No-helper Path](../../../specs/codex-gpt-5-6-agent-routing-technical-roadmap.md#g56r-010-optional-helper-routing-and-no-helper-path)

### Release Integration

Why: Reconcile payloads, prove installed skills spawn and consume results from
the named agents, verify fallback and no-helper behavior, and publish rollback
evidence before releasing defaults.

- [G56R-011 Payload, Installed Skill UAT, Fallback Proof, and Release Integration](../../../specs/codex-gpt-5-6-agent-routing-technical-roadmap.md#g56r-011-payload-installed-skill-uat-fallback-proof-and-release-integration)
