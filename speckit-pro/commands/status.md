---
description: Check the progress of SpecKit workflows and the full project roadmap. Shows phase completion for active specs, plus all remaining specs from the master plan. Parses workflow files and master plan progress tables to present a unified dashboard.
allowed-tools:
  - Read
  - Glob
  - Grep
argument-hint: "[SPEC-ID or 'all']"
---

# SpecKit Status Dashboard

Show the full project roadmap: completed specs, in-progress specs, and specs that haven't started yet.

## Invocation

```
/speckit-pro:status          # Show full roadmap + active specs
/speckit-pro:status all      # Same as above
/speckit-pro:status SPEC-013 # Show specific spec detail
```

## What to Do

### 1. Find All Data Sources

Search for **both** workflow files and master plan files:

```
Workflow files:  **/*-workflow.md  (active/completed specs with phase detail)
Master plans:    **/*master-plan*.md  OR  **/*-plan.md  (full roadmap with all specs)
Also check:      docs/ai/specs/*-workflow.md
                 docs/ai/*master*.md
```

### 2. Parse the Master Plan (Full Roadmap)

If a master plan file exists, extract the **Progress Tracking** table. This contains ALL specs in the project — including those that haven't started the SpecKit workflow yet.

For each spec in the progress table, extract:
- **Spec ID** (e.g., SPEC-006)
- **Name** (e.g., Notifications)
- **Tools** count
- **Status** (✅ Complete, 🔄 In Progress, ⏳ Pending, ⚠️ Blocked)
- **Next Phase** or blocker info

Also extract the **Dependency Graph** or tier information to show which specs can run in parallel and which are blocked.

### 3. Parse Workflow Files (Phase Detail)

For each workflow file found, extract:
- **Spec ID and Name** from the header
- **Phase statuses** from the "Workflow Overview" table (look for ⏳, 🔄, ✅, ⚠️)
- **Current phase** (the first ⏳ or 🔄 phase)
- **Branch** from the "Specification Context" table

### 4. Present Unified Dashboard

Combine master plan and workflow data into a single report with three sections:

```markdown
# SpecKit Project Status

## Summary
- **Total specs:** 14
- **Complete:** 3 (SPEC-006, SPEC-007, SPEC-013)
- **In progress:** 0
- **Remaining:** 11
- **Tools:** 16 of 59 new tools implemented (28 existing → 44 current → 87 target)

## Completed Specs

| Spec | Name | Tools | PR | Notes |
|------|------|-------|----|-------|
| SPEC-006 | Notifications | 5 | #40 | 240 tests |
| SPEC-007 | Repetition | 5 | #38 | 292 tests |
| SPEC-013 | Task Status | 6 | #39 | 367 tests |

## Ready to Start (No Blockers)

These specs have no dependencies beyond the completed foundation and can start now:

| Spec | Name | Tools | Tier | Notes |
|------|------|-------|------|-------|
| SPEC-008 | Perspectives | 5 | 2 | 2 legacy tools to enhance |
| SPEC-009 | Search & Database | 10 | 2 | Largest spec |
| SPEC-011 | Attachments | 5 | 2 | |
| SPEC-010 | Bulk Operations | 6 | 3 | |
| ... | ... | ... | ... | ... |

## Blocked

| Spec | Name | Blocked By | Reason |
|------|------|------------|--------|
| SPEC-020 | Server Optimization | All above | Must know final tool set |
| SPEC-021 | Plugin & Skills | SPEC-020 | Packages the optimized server |

## Active Workflows (Phase Detail)

If any spec has a workflow file with phases in progress, show the phase-level table:

| Spec | Name | Specify | Clarify | Plan | Check | Tasks | Analyze | Impl | Next |
|------|------|---------|---------|------|-------|-------|---------|------|------|
| SPEC-XXX | Feature | ✅ | ✅ | 🔄 | ⏳ | ⏳ | ⏳ | ⏳ | Plan |
```

### 5. If Specific Spec Requested

Show detailed information for that spec:
- All phase statuses with notes (from workflow file, if exists)
- Master plan scope description
- Dependencies and what it enables
- Gate results and key artifacts produced
- Current blockers (if any)
- Files generated

If no workflow file exists for the requested spec, show the master plan scope and suggest creating a workflow file:
```
SPEC-008 (Perspectives) — ⏳ Not Started
No workflow file found. To begin:
1. Create workflow: cp templates/workflow-template.md docs/ai/specs/SPEC-008-workflow.md
2. Run autopilot: /speckit-pro:autopilot docs/ai/specs/SPEC-008-workflow.md
```

### 6. If No Master Plan or Workflow Files Found

Tell the user:
- No master plan or workflow files found in the project
- Guide them to create a master plan: `/speckit-pro:coach help me create a master plan`
- Or create a single workflow: copy `skills/speckit-coach/templates/workflow-template.md`
