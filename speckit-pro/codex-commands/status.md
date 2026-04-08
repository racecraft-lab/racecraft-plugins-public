# /status

Show the full project roadmap: completed specs, in-progress specs, specs that
haven't started yet, and a recommendation for what to work on next.

## Arguments

- `spec_id` (optional): Show detail for a specific spec. Default: show full roadmap.

## Workflow

1. **Find Data Sources** — search for workflow files (`**/*-workflow.md`) and technical
   roadmap files (`**/*technical-roadmap*.md`, `docs/ai/*roadmap*.md`).

2. **Parse Technical Roadmap** — extract the Progress Tracking table with all specs:
   Spec ID, Name, Tools count, Status (✅ Complete, 🔄 In Progress, ⏳ Pending, ⚠️ Blocked),
   Priority (P1/P2/P3), Dependencies.

3. **Parse Workflow Files** — for each active workflow, extract phase statuses from the
   Workflow Overview table (⏳, 🔄, ✅, ⚠️), current phase, and branch name.

4. **Present Unified Dashboard** — combine roadmap and workflow data:
   - Summary (total specs, complete, in progress, remaining)
   - Completed Specs table
   - Ready to Start table (unblocked, sorted by priority)
   - Blocked table
   - Active Workflows phase detail

5. **Recommend Next Spec** — from unblocked pending specs, sort by Priority → roadmap order.
   Show top recommendation with setup command: `/setup SPEC-XXX`.
   List 1-2 alternatives.

6. **If Specific Spec Requested** — show phase statuses, scope description, dependencies,
   gate results, blockers. If no workflow exists, suggest: `/setup SPEC-XXX`.
