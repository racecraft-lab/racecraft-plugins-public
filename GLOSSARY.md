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

**Retry ladder**:
The fixed sequence of three repair attempts a failing check gets in an autopilot run, each with a stronger agent, before the work it covers is marked blocked. It is the only way a run responds to a failure; a check's count never resets within the run.
_Avoid_: corrective budget, corrective cycle, replan epoch, escalation tier

**Reviewability report**:
An advisory assessment of how much work a SPEC or one of its declared slices asks a human to review. It includes the size evidence and any unresolved uncertainty.
_Avoid_: reviewability block, size gate
