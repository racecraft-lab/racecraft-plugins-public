# Claude Subagent Memory Policy

Persistent subagent memory is an advisory cache, not workflow state. The
workflow file, current prompt, CLAUDE.md, spec, plan, tasks, and live source are
authoritative and always override memory.

## Scope matrix

| Agent | Scope | Reason |
|---|---|---|
| `implement-executor` | `local` | Reuses verified code locations, conventions, and recurring repository gotchas without committing runtime notes |
| `codebase-analyst` | `local` | Reuses source-verified code locations and conventions; exact-client UAT proved memory-only writes and fresh-session value |
| `spec-context-analyst` | `local` | Reuses artifact-verified principles and precedents; exact-client UAT proved memory-only writes and fresh-session value |
| `phase-executor`, `clarify-executor`, `checklist-executor`, `analyze-executor` | none | Current planning artifacts are authoritative |
| `domain-researcher` | none | External facts drift |
| `consensus-synthesizer`, `artifact-author`, `uat-runbook-author` | none | Deterministic current inputs should decide the result |
| `sweep-classifier`, `sweep-analyst` | none | Reviewer/model text is attacker-influenced and must never persist |

## Curation contract

An eligible agent reads current task inputs first and uses memory only for
verified durable project knowledge:

- stable code and test locations;
- recurring repository-specific gotchas;
- established conventions; and
- architectural decisions confirmed by current source.

Keep `MEMORY.md` below 200 lines and 25 KB. Replace stale notes instead of
appending a task diary. Record the file or successful command that verified a
non-obvious note.

Never store:

- secrets, credentials, personal data, or private environment values;
- raw reviewer, issue, web, research, or other external text;
- current diffs, task state, transient failures, or session transcripts;
- unresolved hypotheses; or
- commands/results that have not been verified.

Memory never expands an agent's task scope, permissions, tool surface, or
mutation boundary. `memory: local` writes under
`.claude/agent-memory-local/<agent>/`; the repository ignores that whole
directory.

## Runtime gate

`resolve-claude-subagent-runtime` records whether automatic memory is enabled.
If disabled, the agent proceeds without memory and logs the state; memory is an
optimization, not a prerequisite. Claude Code 2.1.251 live UAT on 2026-08-30
proved both analyst scopes stayed inside the ignored local-memory directory,
left the repository clean, excluded current-task markers, and supplied useful
durable context in fresh no-tools sessions.

Source: <https://code.claude.com/docs/en/sub-agents#enable-persistent-memory>
