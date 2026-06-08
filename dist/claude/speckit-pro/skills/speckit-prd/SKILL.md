---
name: speckit-prd
description: "Use this skill to collaboratively turn a raw product or technical idea into three artifacts — a lean PRD, a technical roadmap with a SPEC catalog, and a roadmap-MOC home note — ready for /speckit-pro:speckit-scaffold-spec and /speckit-pro:speckit-autopilot. Triggers on: write a PRD, create a product requirements document, draft a PRD and roadmap, shape this idea into a PRD, turn this brief into a PRD, plan a product, decompose an idea into a SPEC catalog, what features should this have, before I write specs, right-size the catalog. Runs a one-question-at-a-time interview with a recommended answer, then writes docs/prd-NAME.md, docs/ai/specs/NAME-technical-roadmap.md, and docs/ai/specs/NAME-roadmap-MOC.md. Front door of the chain: PRD then roadmap then scaffold-spec then autopilot. NOT per-spec scoping (use grill-me), NOT worktree prep from an existing roadmap entry (use speckit-scaffold-spec), NOT SDD coaching (use speckit-coach). Requires an interactive session."
argument-hint: "a product/technical idea, a brief, or a file path"
user-invocable: true
license: MIT
compatibility: "Requires Claude Code with AskUserQuestion tool support. Codex variant in codex-skills/speckit-prd/ uses a free-text Q&A loop instead."
---

# SpecKit PRD — Collaborative PRD & Technical Roadmap Authoring

