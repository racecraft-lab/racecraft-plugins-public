---
name: speckit-scaffold-spec
description: "Use this skill when the user wants to set up, scaffold, bootstrap, prep, initialize, or prepare a SPEC-ID from the technical roadmap for autonomous execution. Triggers on: set up SPEC-XXX, scaffold SPEC-XXX, bootstrap SPEC-XXX for development, prep SPEC-XXX, initialize the workspace for SPEC-XXX, prepare SPEC-XXX for the autonomous run, create a spec branch and workflow for SPEC-XXX, generate the workflow file for SPEC-XXX, I need a workflow file generated for SPEC-XXX, fill the prompts from the roadmap, pre-fill the workflow template, start working on SPEC-XXX, populate the workflow file for SPEC-XXX. Creates the git worktree, spec branch, Design Concept doc, and populated workflow file ready for autopilot. Strictly interactive — requires a human to answer the grill-me questions. Not for checking roadmap status (use /speckit-pro:speckit-status), running a populated workflow (use /speckit-pro:speckit-autopilot), or SDD coaching (use /speckit-pro:speckit-coach)."
argument-hint: "SPEC-ID (e.g., SPEC-009)"
user-invocable: true
allowed-tools: Bash Read Edit Write Skill Agent
license: MIT
---

# SpecKit Scaffold Spec

