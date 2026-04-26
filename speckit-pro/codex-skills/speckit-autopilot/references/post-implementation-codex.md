# Post-Implementation for Codex

Run these items only after all seven SDD phases complete and G7 passes. They
remain part of the same durable plan and must be mirrored in
`autopilot-state.json`.

## Ordered Items

| Item | Runtime | Command |
| ---- | ------- | ------- |
| Verify Implementation | `phase-executor` if verify extension is installed | `$speckit-verify` |
| Code Review | `phase-executor` if review extension is installed | `$speckit-review` |
| Integration Suite | parent session | `PROJECT_COMMANDS.FULL_VERIFY` or detected full test command |
| Cleanup | `phase-executor` if cleanup extension is installed | `$speckit-cleanup` |
| PR Creation | parent session | `git`, verified remote, `gh` where available |
| Review Remediation | parent session loop | inspect PR feedback, dispatch fixes as needed |
| Retrospective | `phase-executor` if retrospective extension is installed | `$speckit-retrospective-analyze` |

## Rules

- Extension commands run in `phase-executor` with the exact `$speckit-*`
  skill sigil and SPEC context.
- Built-in verification, git, push, PR creation, and review polling stay in the
  parent session so the orchestrator owns durable state and final reporting.
- Missing optional extensions are logged and skipped. Do not fail the entire
  autopilot because an optional extension command is unavailable.
- Never mark the workflow complete until every planned Post item is completed or
  explicitly logged as skipped.
