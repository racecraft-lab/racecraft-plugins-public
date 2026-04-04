---
description: Check the progress of SpecKit workflows and the full project roadmap. Shows phase completion for active specs, plus all remaining specs from the technical roadmap. Recommends the next spec to implement based on priority and dependencies.
allowed-tools:
  - Read
  - Glob
  - Grep
argument-hint: "[SPEC-ID or 'all']"
---

# SpecKit Status Dashboard

Show the full project roadmap: completed specs, in-progress
specs, specs that haven't started yet, and a recommendation for
what to work on next.

## Invocation

```text
/speckit-pro:status          # Show full roadmap + active specs
/speckit-pro:status all      # Same as above
/speckit-pro:status SPEC-013 # Show specific spec detail
```

## What to Do

### 1. Find All Data Sources

Search for **both** workflow files and technical roadmap files:

```text
Workflow files:  **/*-workflow.md  (active/completed specs with phase detail)
Technical roadmaps: **/*technical-roadmap*.md  OR  **/*-roadmap.md  (full roadmap with all specs)
Also check:      docs/ai/specs/*-workflow.md
                 docs/ai/*roadmap*.md
```

### 2. Parse the Technical Roadmap (Full Roadmap)

If a technical roadmap file exists, extract the **Progress Tracking**
table. This contains ALL specs in the project — including those
that haven't started the SpecKit workflow yet.

For each spec in the progress table, extract:

- **Spec ID** (e.g., SPEC-006)
- **Name** (e.g., Notifications)
- **Tools** count
- **Status** (✅ Complete, 🔄 In Progress, ⏳ Pending, ⚠️ Blocked)
- **Next Phase** or blocker info

Also extract:

- The **Dependency Graph** or tier information to show which
  specs can run in parallel and which are blocked
- Each spec's **Priority** (P1/P2/P3) from its section in the
  technical roadmap (line format:
  `**Priority:** P1 | **Depends On:** ...`)

### 3. Parse Workflow Files (Phase Detail)

For each workflow file found, extract:

- **Spec ID and Name** from the header
- **Phase statuses** from the "Workflow Overview" table
  (look for ⏳, 🔄, ✅, ⚠️)
- **Current phase** (the first ⏳ or 🔄 phase)
- **Branch** from the "Specification Context" table

### 4. Present Unified Dashboard

Combine technical roadmap and workflow data into a single report:

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

| Spec | Name | Tools | Tier | Priority | Notes |
|------|------|-------|------|----------|-------|
| SPEC-009 | Search & Database | 10 | 2 | P1 | Largest spec |
| SPEC-008 | Perspectives | 5 | 2 | P2 | 2 legacy tools to enhance |
| SPEC-010 | Bulk Operations | 6 | 3 | P2 | |
| SPEC-012 | TaskPaper | 3 | 3 | P2 | Smallest spec |
| SPEC-011 | Attachments | 5 | 2 | P3 | |
| ... | ... | ... | ... | ... | ... |

## Blocked

| Spec | Name | Blocked By | Reason |
|------|------|------------|--------|
| SPEC-020 | Server Optimization | All above | Must know final tool set |
| SPEC-021 | Plugin & Skills | SPEC-020 | Packages the optimized server |

## Active Workflows (Phase Detail)

If any spec has a workflow file with phases in progress, show the phase-level
table:

| Spec | Name | Specify | Clarify | Plan | Check | Tasks | Analyze | Impl | Next |
|------|------|---------|---------|------|-------|-------|---------|------|------|
| SPEC-XXX | Feature | ✅ | ✅ | 🔄 | ⏳ | ⏳ | ⏳ | ⏳ | Plan |
```

### 5. Recommend Next Spec

After the dashboard tables, add a `## Recommended Next` section
that proposes the next spec to implement.

**Algorithm:**

1. From the technical roadmap, collect all unblocked specs with status
   `⏳ Pending` (not `✅ Complete`, not `🔄 In Progress`, not
   blocked by incomplete specs).
2. For each, read its **Priority** (P1/P2/P3) from the spec's
   section in the technical roadmap.
3. Sort by: Priority (P1 first) → then technical roadmap order
   (preserves tier sequencing).
4. The **top recommendation** is the first spec in the sorted
   list.
5. Also list 1-2 **alternatives** from the same or next priority
   level, especially if they are smaller (fewer tools) for a
   quicker win.

**Output format:**

```markdown
## Recommended Next

**SPEC-009: Search & Database** (10 tools, P1, Tier 2)

This is the highest-priority unblocked spec. It adds full-text search, smart
queries, and database access — the most-requested capabilities for GTD workflows.

To get started:

```text
/speckit-pro:setup SPEC-009
```

This creates the worktree, branch, and populated workflow file.
Then run `/speckit-pro:autopilot` to execute it.

**Alternatives** (if you prefer a smaller spec first):

- SPEC-008: Perspectives (5 tools, P2) — enhances 2 existing legacy tools
- SPEC-010: Bulk Operations (6 tools, P2)
```

**Edge cases:**

- If no unblocked specs remain, say "All unblocked specs are
  complete. Remaining specs are blocked by dependencies."
- If a spec is `🔄 In Progress`, recommend finishing it first:
  "SPEC-XXX is already in progress — finish it before starting
  a new spec."
- If all specs are complete, say "All specs complete — project
  roadmap is finished."

### 6. If Specific Spec Requested

Show detailed information for that spec:

- All phase statuses with notes (from workflow file, if exists)
- Technical roadmap scope description
- Dependencies and what it enables
- Gate results and key artifacts produced
- Current blockers (if any)
- Files generated

If no workflow file exists for the requested spec, show the
technical roadmap scope and suggest creating a workflow file:

```text
SPEC-008 (Perspectives) — ⏳ Not Started
No workflow file found. To begin:
/speckit-pro:setup SPEC-008
```

### 7. If No Technical Roadmap or Workflow Files Found

Tell the user:

- No technical roadmap or workflow files found in the project
- Guide them to create a technical roadmap:
  `/speckit-pro:coach help me create a technical roadmap`
- Or create a single workflow: copy
  `skills/speckit-coach/templates/workflow-template.md`
