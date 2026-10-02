# SpecKit Pro

The language of the speckit-pro plugin's workflow: how a SPEC is scaffolded, planned, built and handed to a human for acceptance, on Claude Code and Codex alike. User-facing terms are also explained for plugin users in `docs-site/src/content/docs/glossary.md`.

## Language

**Host**:
A coding-agent product that runs the plugin: Claude Code or Codex.

**Host parity**:
The rule that a run gives the same outcomes and the same run experience (prompts, progress block, stop points) on every host. Only one-time host setup may differ. A release needs a green canary on both hosts.
_Avoid_: cross-platform support, Codex support

**Progress block**:
The fixed summary of an autopilot run's phases and tasks that the runner renders from autopilot state at every phase transition. It is the only place a run shows its progress.
_Avoid_: task list, todo list, checklist
