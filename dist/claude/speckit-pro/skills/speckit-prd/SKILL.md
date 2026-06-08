---
name: speckit-prd
description: "Use this skill to collaboratively turn a raw product or technical idea into two artifacts — a lean PRD and a technical roadmap with a SPEC catalog — ready for /speckit-pro:speckit-scaffold-spec and /speckit-pro:speckit-autopilot. Triggers on: write a PRD, create a product requirements document, draft a PRD and roadmap, shape this idea into a PRD, turn this brief into a PRD, plan a product, decompose an idea into a SPEC catalog, what features should this have, before I write specs, right-size the catalog. Runs a one-question-at-a-time interview with a recommended answer on every question, then writes docs/prd-NAME.md and docs/ai/specs/NAME-technical-roadmap.md. This is the front door of the chain: PRD then roadmap then scaffold-spec then autopilot. NOT per-spec scoping for a single spec already in the roadmap (use grill-me), NOT preparing a worktree from an existing roadmap entry (use speckit-scaffold-spec), NOT SDD methodology coaching (use speckit-coach). Requires an interactive session."
argument-hint: "a product/technical idea, a brief, or a file path"
user-invocable: true
license: MIT
compatibility: "Requires Claude Code with AskUserQuestion tool support. Codex variant in codex-skills/speckit-prd/ uses a free-text Q&A loop instead."
---

# SpecKit PRD — Collaborative PRD & Technical Roadmap Authoring

