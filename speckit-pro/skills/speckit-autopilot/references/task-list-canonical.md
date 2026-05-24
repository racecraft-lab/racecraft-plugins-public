# Canonical Task List Reference

The complete, prescribed task list the autopilot creates via `TaskCreate` at Step 1.1. Every entry below MUST appear in the visible progress panel before Phase 1 starts. Do NOT omit, collapse, or defer entries — when a required extension is absent, the task still appears, marked as `skipped: <extension> not installed`.

## Contents

- [Task Naming Pattern](#task-naming-pattern) — phase + post-impl naming conventions
- [Canonical Post-Implementation Task List](#canonical-post-implementation-task-list) — the 11-entry post-impl set
- [Extension Detection Rule](#extension-detection-rule) — `.specify/extensions.yml` / `.registry` / Glob fallback
- [Consensus Tasks Are Mandatory](#consensus-tasks-are-mandatory) — every Clarify session, Checklist domain, and Analyze gets a paired Consensus task
- [Other Rules](#other-rules) — Phase 7 group decomposition, completion order, completeness verification

## Task Naming Pattern

Parsed from the workflow file:

```text
  "Archive Sweep: previously merged specs dry-run/apply eligibility"
  "Phase 0: Prerequisites"
  "Phase 1: Specify"
  "Phase 2: Clarify - <Session Name>"           ← one per session
  "Phase 2: Clarify - <Session Name> Consensus" ← MANDATORY after each session
  "Phase 3: Plan"
  "Phase 4: Checklist - <Domain>"               ← one per domain
  "Phase 4: Checklist - <Domain> Consensus"     ← MANDATORY after each domain
  "Phase 5: Tasks"
  "Phase 6: Analyze"
  "Phase 6: Analyze - Consensus"                ← MANDATORY after analyze
  "Phase 7: <Group> (<task IDs>)"               ← parsed from tasks.md
  "Post: <task name>"                           ← from the canonical list below
```

## Canonical Post-Implementation Task List

```text
  "Post: Doctor Extension Check"        ← doctor / speckit-utils ext
  "Post: Verify Implementation"         ← verify ext
  "Post: Verify Tasks Phantom Check"    ← verify-tasks ext
  "Post: Code Review"                   ← review ext
  "Post: Integration Suite"             ← always required (no ext)
  "Post: Cleanup"                       ← cleanup ext
  "Post: Reviewability Diff Gate"       ← always required (no ext)
  "Post: PR Body Generation"            ← always required (no ext)
  "Post: PR Creation"                   ← always required (no ext)
  "Post: Review Remediation"            ← always required (no ext)
  "Post: Retrospective"                 ← retrospective ext (FINAL STEP)
```

## Extension Detection Rule

For each extension-dependent task: check `.specify/extensions.yml`
(or `.specify/extensions/.registry`) for the extension's `enabled: true` flag,
OR confirm the extension directory exists via `Glob`. If neither, the task
still appears in the task list with status `skipped: <ext-name> not installed`.
Never silently drop a task.

## Consensus Tasks Are Mandatory

Every Clarify session, every Checklist domain, and the Analyze phase MUST
have a corresponding Consensus task immediately after it. The consensus task
runs the two-layer resolution process (Rule 6 in SKILL.md / `references/consensus-protocol.md`).
A Consensus task may be skipped ONLY if the executor reports zero unresolved
items. Never omit consensus tasks from the task list at creation time.

## Other Rules

- Phase 7 decomposes into groups after `tasks.md` is created
  (test / impl / verify per phase — see [`phase-execution.md`](./phase-execution.md))
- Mark completed phases immediately; first pending phase as `in_progress`
- **Verify task-list completeness before starting Phase 1**: count the
  prescribed entries (every Phase, every Consensus, every `Post:` task) and
  confirm each is present. If the count differs, ADD the missing entries
  before advancing.
