# Autopilot progress never uses host task-list tools

Status: accepted

Both hosts have made their task-list tools optional. Claude Code ships TaskCreate, TaskGet, TaskUpdate, TaskList and TodoWrite by default only on older models, because newer models track multi-step work without a checklist and the tool definitions cost context. Codex made `update_plan` opt-in. Autopilot required these tools, so on current models it either silently fell back to its state file or treated a missing tool as a stop. We treat that requirement as a bug on both hosts: speckit-pro never requires, prompts for, opts into or calls a task-list tool, even when the host exposes one. Visible progress comes only from the **progress block**, rendered by the runner from autopilot state at every phase transition.

## Considered Options

- **Opt the host into the tools** (environment variable or flag set by a launcher). Rejected: it brings back the context cost the hosts removed on purpose, and a user launching by hand still misses it.
- **Use the tools when present, the progress block otherwise.** Rejected: two progress paths to test on two hosts, and output that differs by model.

## Consequences

- Skill prose and tests that demand the tools are deleted, not softened. A structural test asserts that skill text does not name them.
- The readiness record does not need to check for a task-list tool.
- The canary's "no task tools" variant is the normal case on current models, not an edge case.
