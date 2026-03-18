---
description: Check the progress of SpecKit workflows. Shows phase completion across all specs or a specific spec. Parses workflow files and presents a summary dashboard.
allowed-tools:
  - Read
  - Glob
  - Grep
argument-hint: "[SPEC-ID or 'all']"
---

# SpecKit Status Dashboard

Check the progress of SpecKit workflows across all specs.

## Invocation

```
/speckit-pro:status          # Show all specs
/speckit-pro:status all      # Same as above
/speckit-pro:status SPEC-013 # Show specific spec
```

## What to Do

### 1. Find All Workflow Files

Search for workflow files in the project:

```
Glob pattern: **/*-workflow.md
Also check: docs/ai/specs/*-workflow.md
```

### 2. Parse Each Workflow File

For each workflow file, extract:
- **Spec ID and Name** from the header
- **Phase statuses** from the "Workflow Overview" table (look for ⏳, 🔄, ✅, ⚠️)
- **Current phase** (the first ⏳ or 🔄 phase)
- **Branch** from the "Specification Context" table

### 3. Present Dashboard

Format as a summary table:

```markdown
# SpecKit Workflow Status

| Spec | Name | Branch | Specify | Clarify | Plan | Check | Tasks | Analyze | Impl | Next |
|------|------|--------|---------|---------|------|-------|-------|---------|------|------|
| SPEC-013 | Task Status | 013-task-status | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Done |
| SPEC-020 | Batch Ops | 020-batch-ops | ✅ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | Clarify |
```

### 4. If Specific Spec Requested

Show detailed information:
- All phase statuses with notes
- Gate results
- Key artifacts produced
- Current blockers (if any)
- Files generated

### 5. If No Workflow Files Found

Tell the user:
- No workflow files found in the project
- Guide them to create one: `/speckit-pro:coach help me create a workflow`
- Or point to the template: `skills/speckit-coach/templates/workflow-template.md`
