# Canonical Task List — Codex

Reference for the granular `update_plan` + `autopilot-state.json` checklist
the autopilot materializes in Step 1.1. Codex-specific mirror of
`../../skills/speckit-autopilot/references/task-list-canonical.md` — same
list, Codex-specific persistence primitives.

## Contents

- [Checklist Naming Pattern](#checklist-naming-pattern) — exact item-name templates parsed from the workflow file
- [Canonical Post-Implementation Item List](#canonical-post-implementation-item-list) — 11 mandatory Post items + missing-extension behavior
- [Item Naming Rules](#item-naming-rules) — same names across both stores, completed-then-in_progress sequencing
- [Reference `autopilot-state.json` Schema](#reference-autopilot-statejson-schema) — full example JSON document

## Checklist Naming Pattern

```text
  "Archive Sweep: previously merged specs dry-run/apply eligibility"
  "Phase 0: Prerequisites"
  "Phase 1: Specify"
  "Phase 2: Clarify - <Session Name>"           ← one per session
  "Phase 2: Clarify - <Session Name> Consensus" ← MANDATORY after each session
  "Phase 2: Clarify - Pending session discovery" ← only if no sessions parsed yet
  "Phase 3: Plan"
  "Phase 4: Checklist - <Domain>"               ← one per domain
  "Phase 4: Checklist - <Domain> Consensus"     ← MANDATORY after each domain
  "Phase 4: Checklist - Pending domain discovery" ← only if no domains parsed yet
  "Phase 5: Tasks"
  "Phase 6: Analyze"
  "Phase 6: Analyze - Consensus"                ← MANDATORY after analyze
  "Phase 6.5: Confidence Gate"                  ← MANDATORY after analyze consensus
  "Phase 7: Implement - Pending task decomposition" ← before tasks.md exists
  "Phase 7: <Group> (<task IDs>)"               ← parsed from tasks.md
  "Post: <item name>"                           ← from canonical list below
```

## Canonical Post-Implementation Item List

Every item below MUST appear in `update_plan` and `autopilot-state.json`
unless its required extension is provably absent. **Do NOT omit any of
these, do NOT collapse them, do NOT defer them** — the user expects to
see all of them in the plan panel before Phase 1 starts. When an
extension is missing, still create the item but mark it
`skipped: <extension> not installed`.

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

**Detection rule per extension item:** check `.specify/extensions.yml`
(or `.registry`) for the extension's `enabled: true` flag, OR confirm
the extension directory exists. If neither, the item still appears
in the plan with status `skipped: <ext-name> not installed`. Never
silently drop it.

**Verify item-list completeness before starting Phase 1**: count
the 11 entries above and confirm every single one is present in
both `update_plan` and `autopilot-state.json` (in addition to all
Phase / Consensus items). If any are missing, ADD them before
advancing.

## Item Naming Rules

- Replace `Phase 7: Implement - Pending task decomposition` with concrete
  task-group items immediately after tasks.md is created. Do not leave Phase 7
  as a single placeholder once tasks can be parsed.
- Phase 7 decomposed into groups after tasks.md is created
  (test/impl/verify per phase, see [phase-execution-codex.md](./phase-execution-codex.md))
- Extension items (doctor, verify-tasks, verify, review,
  cleanup, retrospective): add if extension is in `.registry`
  with `enabled: true`, or if extension directory exists
- Mark completed phases immediately; first pending as `in_progress`
- Use EXACTLY the same item names in `update_plan` and `autopilot-state.json`
- Preserve one or more pending items for every later canonical phase when
  resuming from a middle phase
- Immediately print a checklist summary after writing both copies

## Reference `autopilot-state.json` Schema

```json
{
  "workflow_file": "docs/ai/specs/SPEC-013-workflow.md",
  "updated_at": "2026-04-10T18:00:00Z",
  "active_step": "Phase 1: Specify",
  "plan": [
    {"step": "Archive Sweep: previously merged specs dry-run/apply eligibility", "status": "completed"},
    {"step": "Phase 0: Prerequisites", "status": "completed"},
    {"step": "Phase 1: Specify", "status": "in_progress"},
    {"step": "Phase 2: Clarify - UX Focus", "status": "pending"},
    {"step": "Phase 2: Clarify - UX Focus Consensus", "status": "pending"},
    {"step": "Phase 3: Plan", "status": "pending"},
    {"step": "Phase 4: Checklist - Pending domain discovery", "status": "pending"},
    {"step": "Phase 5: Tasks", "status": "pending"},
    {"step": "Phase 6: Analyze", "status": "pending"},
    {"step": "Phase 6: Analyze - Consensus", "status": "pending"},
    {"step": "Phase 6.5: Confidence Gate", "status": "pending"},
    {"step": "Phase 7: Implement - Pending task decomposition", "status": "pending"},
    {"step": "Post: Doctor Extension Check", "status": "pending"},
    {"step": "Post: Verify Implementation", "status": "pending"},
    {"step": "Post: Verify Tasks Phantom Check", "status": "pending"},
    {"step": "Post: Code Review", "status": "pending"},
    {"step": "Post: Integration Suite", "status": "pending"},
    {"step": "Post: Cleanup", "status": "pending"},
    {"step": "Post: Reviewability Diff Gate", "status": "pending"},
    {"step": "Post: PR Body Generation", "status": "pending"},
    {"step": "Post: PR Creation", "status": "pending"},
    {"step": "Post: Review Remediation", "status": "pending"},
    {"step": "Post: Retrospective", "status": "pending"}
  ]
}
```
