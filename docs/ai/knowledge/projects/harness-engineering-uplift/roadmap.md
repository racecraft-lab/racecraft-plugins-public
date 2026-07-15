---
type: "speckit-project-map"
title: "Roadmap - Map of Content"
description: "Durable project map for Roadmap - Map of Content."
resource: "docs/ai/specs/harness-engineering-uplift-technical-roadmap.md"
tags: ["project-map","speckit"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "harness-engineering-uplift"
x-speckit-project: "harness-engineering-uplift"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-legacy-status: "Draft; HRNS-001 ready to scaffold after maintainer acceptance"
x-speckit-sources: ["docs/ai/specs/harness-engineering-uplift-technical-roadmap.md|58a59010aedec2fb306c428947e8178e6cb8f632dfb1a9ece0ff8e5cda4c3270"]
x-speckit-migration-sources: ["docs/ai/specs/harness-engineering-uplift-roadmap-MOC.md|8234fa9f58ef7ea6eaa998c594ccba3f1e2853881b580240ee6c49ff16273f5b"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
x-speckit-legacy-view: "docs/ai/specs/harness-engineering-uplift-roadmap-MOC.md"
x-speckit-legacy-up: "[SpecKit Pro Harness Engineering Uplift Roadmap](harness-engineering-uplift-technical-roadmap.md)"
x-speckit-legacy-related: ["[SpecKit Pro Harness Engineering Uplift PRD](../../prd-harness-engineering-uplift.md)"]
---
# Roadmap - Map of Content

Source of truth: `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md`.

## Curated map

Navigation map for the SpecKit Pro harness-engineering uplift lane.

## Epics (curated)

### Durable Knowledge Layer (cross-cutting)

Why: SpecKit Pro already maintains roadmap/SPEC MOCs, Design Concepts,
workflow lessons, archive memory, and evidence packets. The uplift ports their
reusable meaning into one reviewed OKF v0.1 bundle instead of adding another
editable memory system. Source documents and operational state retain their
authority; legacy MOCs become generated compatibility views.

- HRNS-001 inventories and classifies every existing knowledge-like surface.
- HRNS-002 defines the OKF bundle, MOC/memory port, and authority model.
- HRNS-003 adds deterministic health, search, plan, apply, and compatibility
  rendering contracts.
- HRNS-004 through HRNS-008 protect, verify, trace, consume, maintain, archive,
  and prove actual skill-driven use of the layer.

### Harness Taxonomy

Why: Before implementation starts, SpecKit Pro needs one durable inventory of
harness surfaces and gaps so future specs use the same workflow boundaries.

- HRNS-001 Harness Surface Inventory and Gap Taxonomy

### Context and Tool Foundations

Why: Reliable agent work starts with concise repo-grounded context and explicit
tool/helper contracts. These two specs can proceed in parallel after HRNS-001
because they touch separable surfaces. Together they establish the canonical
OKF profile and the runner operations that replace independent MOC/memory
maintenance.

- HRNS-002 Progressive Context and Durable State Contract
- HRNS-003 Helper, Tool, and Capability Contract

### Controls and Sensors

Why: Once helper/tool contracts exist, SpecKit Pro can add pre-action controls
and verification sensors without guessing which operations are read-only,
mutating, networked, credential-bearing, or approval-required.

- HRNS-004 Permission, Sandbox, and Pre-action Authorization Controls
- HRNS-005 Feedback Sensors and Eval Readiness Ladder

### Evidence Packets

Why: Permissions and evals need compact, local, replay-friendly evidence. Trace
and debug packets make helper runs, workflow failures, review packets, and
delegated-agent work inspectable without dumping raw logs into PRs.

- HRNS-006 Trace, Debug, and Review Evidence Packets

### Long-running Work

Why: Long-horizon scaffold/autopilot/status/resolve-pr work needs resumable
state, file ownership, stop conditions, and planner/evaluator separation before
larger autonomous runs are safe.

- HRNS-007 Long-horizon Orchestration and Resumption Controls

### Harness Maintenance

Why: Harnesses drift. Prompts, docs, helper registries, generated payloads,
examples, sensors, knowledge source hashes, superseded concepts, frozen legacy
memory, and generated MOC views need bounded garbage collection that cites
concrete repo evidence and avoids speculative cleanup.

- HRNS-008 Harness Drift, Garbage Collection, and Self-healing Remediation
