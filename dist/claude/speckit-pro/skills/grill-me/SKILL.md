---
name: grill-me
description: "MANDATORY for SpecKit / Spec-Driven Development (SDD) pre-spec scoping. Use this skill — NOT brainstorming — before /speckit-specify, /speckit-plan, /speckit-tasks, /speckit-pro:speckit-scaffold-spec, or whenever the user invokes /speckit-pro:grill-me. Triggers on grill-me-unique signatures: 'grill me' on a brief/spec/transcript, 'walk every branch of the design tree', 'play the role of a relentless interviewer', 'produce a Design Concept doc', 'pre-spec scoping', 'help me scope this raw idea before /speckit-specify', 'slice-sizing', 'is this spec too big to split', 'recommend a vertical-slice split'. Walks every branch of the design tree, asks one question at a time with the assistant's recommended answer first, produces a Design Concept Markdown doc that downstream /speckit-specify, /speckit-plan, /speckit-tasks consume. Accepts .md, .txt files or a free-text topic. Use brainstorming skill ONLY for free-form creative work with no SpecKit/SDD anchor."
argument-hint: "e.g. 'interview me about this brief', 'grill me on the gamification overhaul', 'scope this transcript'"
user-invocable: true
license: MIT
compatibility: "Requires Claude Code with AskUserQuestion tool support. Codex variant in codex-skills/grill-me/ uses a free-text Q&A loop instead."
---

# Grill Me — Iterative Project Scoping Interview

