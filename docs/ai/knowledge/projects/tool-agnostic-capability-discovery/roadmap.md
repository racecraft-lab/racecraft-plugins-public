---
type: "speckit-project-map"
title: "Roadmap - Map of Content"
description: "Durable project map for Roadmap - Map of Content."
resource: "docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md"
tags: ["project-map","speckit"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "tool-agnostic-capability-discovery"
x-speckit-project: "tool-agnostic-capability-discovery"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-legacy-status: "TACD-004 complete"
x-speckit-sources: ["docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md|114fd00c0e8f512d93164e67208294c58957b7a3f87669655ae7656b3aa60229"]
x-speckit-migration-sources: ["docs/ai/specs/tool-agnostic-capability-discovery-roadmap-MOC.md|0a73186ac4a8254316ca1618d8bcfcb2b383f6710a77784c3455f076c7740ff2"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
x-speckit-legacy-view: "docs/ai/specs/tool-agnostic-capability-discovery-roadmap-MOC.md"
x-speckit-legacy-up: "[Tool-Agnostic Capability Discovery Roadmap](tool-agnostic-capability-discovery-technical-roadmap.md)"
x-speckit-legacy-related: ["[Tool-Agnostic Capability Discovery PRD](../../prd-tool-agnostic-capability-discovery.md)"]
---
# Roadmap - Map of Content

Source of truth: `docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md`.

## Curated map

Navigation map for the Tool-Agnostic Capability Discovery roadmap.

## Epics (curated)

### Platform Mechanics

Why: Verify runtime mechanics and testability before changing shipped behavior.

- [TACD-001 Platform Mechanics Spike report](../../../research/tool-agnostic-capability-discovery-spike.md) - archived after PRs #211-#214 and #216

### Agent Behavior

Why: Move active Claude and Codex agents from named optional tools to capability-first discovery.

- [TACD-002 Capability Discovery Directive and Agent Updates archive](../../../../../.specify/memory/archive-reports/2026-06-18-tacd-002-post-merge-hygiene.md) - archived after PRs #221-#226

### User-Facing Messaging

Why: Align prerequisites and docs with the implemented vendor-neutral behavior.

- [TACD-003 Prerequisite and Documentation Messaging archive](../../../../../.specify/memory/archive-reports/2026-06-19-tacd-003-post-merge-hygiene.md) - archived after PR #230

### Verification

Why: Lock the vendor-neutral contract with deterministic checks and eval coverage.

- [TACD-004 Verification Coverage archive](../../../../../.specify/memory/archive-reports/2026-06-22-tacd-004-post-merge-hygiene.md) - archived after PR #240
