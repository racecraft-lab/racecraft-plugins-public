---
name: speckit-status
description: "Use when the user wants to read SpecKit project status, see the full roadmap dashboard, check which specs are complete, in-progress, blocked, or ready to start, see phase-level progress for active specs, find which active worktrees exist and what spec each belongs to, check the status or current phase of a specific SPEC-ID, identify what is blocking a spec and why, get a recommendation for the next spec to implement, or summarize overall project health and next steps. Triggers on: show roadmap, project status, active workflows, blockers, dashboard, all specs, phases complete, next phase, list worktrees, which spec should I start, what is next, SpecKit progress, project health, check SPEC-XXX, is SPEC-XXX done, is SPEC-XXX blocked. Read-only: never creates files, branches, or worktrees. Do NOT use to set up or scaffold a spec (use speckit-scaffold-spec), execute a workflow autonomously (use speckit-autopilot), fix PR review comments (use speckit-resolve-pr), or ask about SDD methodology (use speckit-coach)."
argument-hint: "[SPEC-ID or 'all']"
user-invocable: true
allowed-tools: Bash Read Glob Grep
license: MIT
---

# SpecKit Status Dashboard

