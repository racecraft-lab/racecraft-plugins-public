# Task-list tool availability on Claude Code and Codex

Research for wayfinder ticket #1016 (map #1006). Dated 2026-10-01. Claude Code 2.1.287 and Codex CLI 0.156.0 were the local versions used for checks.

## Answer

**Claude Code.** The task-list tools are model-gated, not mode-gated. Since v2.1.268, `TaskCreate`, `TaskGet`, `TaskUpdate`, `TaskList` and `TodoWrite` exist by default only on Claude 3.x, Opus 4 through 4.7, Sonnet 4 through 4.6 and Haiku 4.5. On every other model, and on any model ID Claude Code does not recognize, the tools are left out entirely. They are absent, not deferred. A session on Sonnet 5 or Opus 5 therefore has no task-list tool unless the launcher opts in. This is the most likely cause of the two autopilot runs with no tools (the model of those runs is not confirmed; see Unconfirmed). Local check: a headless run on `claude-sonnet-5-5` lists no `Task*` list tools in its init message, and the same run with `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` lists all four.

**Opt-in.** `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` (v2.1.233 or later), `--allowedTools TaskCreate`, or `--tools` naming them. `CLAUDE_CODE_ENABLE_TASKS=0` swaps the four Task tools for `TodoWrite`. Background and cloud sessions always get them. Subagents get them only when the parent session has them.

**Codex.** `update_plan` is opt-in. Since openai/codex PR #41744 (merged 2026-08-31), `tools.update_plan.enabled` defaults to `false`, and the tool is not registered unless it is set to `true`. It is also rejected in Plan mode. Local 0.156.0 source behaves the same. A bare Codex install therefore has no `update_plan`, and the current Codex block ("invoke it directly, STOP only if the call fails") hides a missing tool until the call is attempted.

**Detection.** No hook, env var or script can read the model's tool inventory directly. Reliable options: (1) a runner check on the stream-json init message (`tools` array) for headless runs; (2) a prose instruction that tells the model to check its own tool list, and to try `ToolSearch select:TaskCreate` only when `ToolSearch` itself exists, before the first create; (3) a launcher that sets the opt-in so the tools exist. See "Detection recipe".

## Claude Code

### Which tools exist and when

| Claim | Source |
| --- | --- |
| The task tools are `TaskCreate`, `TaskGet`, `TaskList`, `TaskUpdate`. `TodoWrite` is the legacy checklist, "disabled by default in favor of" them. | [Tools reference](https://code.claude.com/docs/en/tools-reference) |
| Defaults apply "in Claude Code v2.1.268 and later": the tools are available by default only on Claude 3.x, Opus 4 through 4.7, Sonnet 4 through 4.6, Haiku 4.5. | [Tools reference, Task tool availability](https://code.claude.com/docs/en/tools-reference#task-tool-availability); [Agent SDK, Track todos](https://code.claude.com/docs/en/agent-sdk/todo-tracking#model-availability) |
| "On every other model, Claude Code leaves the tools out unless you opt in. The same applies to a model ID Claude Code doesn't recognize, such as a custom model name served through an LLM gateway." | Tools reference, Task tool availability |
| Rationale given: newer models track multi-step work without a written checklist, and the tool definitions cost context. | Tools reference, Task tool availability |
| `CLAUDE_CODE_ENABLE_TASKS`: default provides the four Task tools; `0` gives `TodoWrite` instead. | [Environment variables](https://code.claude.com/docs/en/env-vars) |
| `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` gives the tools on every model. Requires v2.1.233 or later. `CLAUDE_CODE_ENABLE_TASKS` still picks Task tools versus `TodoWrite`. | Environment variables |
| Other opt-ins: name a tool in `--allowedTools` (for example `claude --allowedTools TaskCreate`), or list tools in `--tools`. SDK equivalents are `allowedTools` and `tools` options. | Tools reference, Task tool availability |
| An allow rule in a settings file is not listed as an opt-in. Only the flags, SDK options and env var are. | Tools reference, Task tool availability (absence from the list; not tested) |
| In background sessions and cloud sessions the tools are provided "on every model, listed or not". | Tools reference, Task tool availability |

### Entrypoints and modes

| Surface | Result | Source |
| --- | --- | --- |
| Interactive terminal | Model rule above applies. | Tools reference |
| `-p` headless | Same model rule. No special exclusion documented. Local check confirms the model rule (see Local checks). | Tools reference; local run |
| Agent SDK (TypeScript, Python) | Same model rule. The SDK applies defaults through the bundled Claude Code binary. A custom `pathToClaudeCodeExecutable` or `cli_path` gets that install's own defaults. Without the tools, no `tool_use` blocks for them appear in the stream. | [Agent SDK, Track todos](https://code.claude.com/docs/en/agent-sdk/todo-tracking#model-availability) |
| Background sessions, cloud sessions | Always provided. | Tools reference |
| Subagents | "Claude Code gives a subagent the tools only when your session has them, even when the subagent runs a different model." A subagent on an old model under a parent on a new model still gets none. v2.1.285 fixed foreground subagents sometimes missing the tools in sessions that have them. | Tools reference; [Changelog 2.1.285](https://code.claude.com/docs/en/changelog) |
| Agent-team teammates | In-process teammates follow the parent session. A split-pane teammate is a separate process, so its own model decides. | Tools reference |
| Desktop app, IDE extension panel, GitHub Actions | Not documented for these tools. Not confirmed. | Not found |

### Settings and permissions

- Permission rules and hooks can name these tools (tool names are used in permission rules, subagent tool lists and hook matchers). A `deny` rule or `--disallowedTools` entry would remove them; the docs do not describe this for the task tools specifically. Not confirmed for task tools. Source for the general mechanism: [Tools reference](https://code.claude.com/docs/en/tools-reference).
- `--tools ""` disables all built-in tools; `--tools "default"` uses all. Source: local `claude --help`.
- `--bare` shrinks the init tool list to three tools in a local run. Source: local run.

### Can they be deferred behind ToolSearch?

- `ToolSearch` "searches for and loads deferred tools when tool search is enabled". The docs tie tool search to MCP tools and list configurations without it (custom `ANTHROPIC_BASE_URL`, `ENABLE_TOOL_SEARCH=false`, models earlier than Claude 4.5). Sources: [Tools reference](https://code.claude.com/docs/en/tools-reference), [MCP docs](https://code.claude.com/docs/en/mcp) (the section body was truncated in my fetch; only these cross-references were read).
- No page I read says the Task tools or `TodoWrite` are deferred. The model-gating page says they are "left out". Treat absence as absence, not as "load with ToolSearch". Not confirmed either way beyond that wording.
- Local check: in a normal headless run on `claude-sonnet-5-5` the init `tools` array contained `ToolSearch` and no `TaskCreate`. Whether the init array includes deferred tool names is not confirmed.

### TodoWrite versus Task tools

- Wherever the tools exist, you get the four Task tools, or `TodoWrite` alone when `CLAUDE_CODE_ENABLE_TASKS=0`. They do not coexist. Local check with both `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` and `CLAUDE_CODE_ENABLE_TASKS=0`: init list had `TodoWrite` and no `TaskCreate`. Source: local run; [Environment variables](https://code.claude.com/docs/en/env-vars).
- So a skill that says "create with TaskCreate" breaks on a `CLAUDE_CODE_ENABLE_TASKS=0` host even when a task tool exists. A capability check must accept either name.

### Local checks (Claude Code 2.1.287, headless, `--output-format stream-json --verbose --max-turns 1`, model `claude-sonnet-5-5`)

| Env | init `tools` entries matching Task/Todo/ToolSearch |
| --- | --- |
| none (plain `CLAUDE_CODE_ENABLE_TODO_TOOLS=0`) | `Task` (subagent launcher), `TaskStop`, `ToolSearch` |
| `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` | `Task`, `TaskCreate`, `TaskGet`, `TaskList`, `TaskStop`, `TaskUpdate`, `ToolSearch` |
| `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` and `CLAUDE_CODE_ENABLE_TASKS=0` | `Task`, `TaskStop`, `TodoWrite` |

`Task` here is the subagent launcher and `TaskStop` stops background work. Neither is a list tool. The skill text already treats them correctly (it separates launcher availability from list availability). The init message also carries `model`, `capabilities`, `skills`, `plugins` and `mcp_servers`.

### Version notes

- v2.1.233: `CLAUDE_CODE_ENABLE_TODO_TOOLS` introduced (per the env-var page's "Requires Claude Code v2.1.233 or later").
- v2.1.268: current model-based default set.
- v2.1.285: fix for foreground subagents missing the tools (changelog). The changelog fetch was summarized by a small model; other entries about these tools may exist that I did not see.

## Codex

### When `update_plan` exists

| Claim | Source |
| --- | --- |
| The tool is registered only when `update_plan_enabled` is true (`if turn_context.config.update_plan_enabled { registry.add(PlanHandler); }`). | openai/codex `codex-rs/core/src/tools/spec_plan.rs`, `add_core_utility_tools` (main at b707714, 2026-10-01) |
| `update_plan_enabled` resolves from `[tools.update_plan] enabled`, and is true only when the config sets it true (`is_some_and(|config| config.enabled)`); the field default is `false`. | `codex-rs/core/src/config/mod.rs` `resolve_update_plan_enabled`; `codex-rs/config/src/config_toml.rs` `UpdatePlanToolConfig` |
| The same resolver is present at tag `rust-v0.156.0`. | `codex-rs/core/src/config/mod.rs` at tag rust-v0.156.0 |
| History: #35054 (merged 2026-07-24) added a default-on switch to disable the tool. #41744 (merged 2026-08-31) "Make the update_plan tool opt-in": default `false`, and the bundled `update_plan` guidance is stripped from prompts when disabled. | [#35054](https://github.com/openai/codex/pull/35054), [#41744](https://github.com/openai/codex/pull/41744) |
| First release containing #41744 is probably 0.152.0 (2026-09-01; 0.151.0 shipped 2026-08-29). Inferred from dates, not checked against the tag. | [Releases](https://github.com/openai/codex/releases) |
| In Plan collaboration mode the handler rejects the call: "update_plan is a TODO/checklist tool and is not allowed in Plan mode". | `codex-rs/core/src/tools/handlers/plan.rs` |
| Config key and CLI override: `tools.update_plan.enabled` in `config.toml`, or `-c tools.update_plan.enabled=true` (the `-c, --config <key=value>` flag exists on `codex exec`). | `codex-rs/core/config.schema.json` (`ToolsToml.update_plan`); local `codex exec --help` |
| This repository's own Codex eval adapter already passes `--config tools.update_plan.enabled=true`. | `tests/speckit-pro/lib/native_eval_codex_adapter.py` |
| The Codex TUI's internal structured-request helper forces the tool off for its own requests. | `codex-rs/tui/src/temporary_structured_request.rs` |
| The public config reference page did not list `tools.update_plan.enabled` when I fetched it. The source schema is the authority. | [Config reference](https://learn.chatgpt.com/docs/config-file/config-reference) |

### exec versus TUI

I found no code path that registers the tool differently for `codex exec` than for the TUI. The gate is the shared config field above. Not confirmed by running both; the source search found only the config gate and the Plan-mode rejection.

### Subagents

The multi-agent code builds usage hints from the parent or child config's `update_plan_enabled` flag, which implies child threads derive the flag from config (and subagent spawn reuses the resolved config). Whether a spawned worker always inherits the parent's setting is not confirmed.

### Why the current skill text fails

The Codex block says to call `update_plan` directly and "do not infer that it is unavailable from tool summaries", then STOP if the call fails. With the default now `false`, the model may not have the tool at all, so the first call is not a valid probe: a model can answer by hallucinating success or by falling back silently. The skill relies on a call that the host may not define.

## Detection recipe

Use more than one layer. None of them alone covers every surface.

1. **Launcher guarantees the tools (preferred).** Document and, where the plugin owns the launch, set:
   - Claude Code: `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` (and leave `CLAUDE_CODE_ENABLE_TASKS` unset). For SDK or `-p` runs, set it in the `env` option or the process environment.
   - Codex: `-c tools.update_plan.enabled=true`, or `[tools.update_plan] enabled = true` in `config.toml`.
   This turns the capability from "detected" into "ensured", but a user launching by hand can still miss it, so layers 2 and 3 stay.

2. **Runner check on the init message (headless, SDK, stream-json).** Read the `system` message with `subtype: "init"` and test the `tools` array. Pass when it contains `TaskCreate` and `TaskUpdate` (Task set) or `TodoWrite` (legacy set). Verified locally on 2.1.287 (see Local checks). Caveat: whether deferred tool names appear in this array is unconfirmed. For Codex there is no equivalent init tool listing that I confirmed; the Codex runner should read the resolved config (`tools.update_plan.enabled`) instead, for example by checking the effective `-c` overrides and `config.toml`.

3. **Prose instruction to the model (interactive, where no runner sees the stream).** Replace "create with TaskCreate" with a check-first rule:
   - Before the first list action, inspect your own tool inventory for `TaskCreate` and `TaskUpdate`, or `TodoWrite`. Names that are only deferred count only if `ToolSearch` exists and `select:TaskCreate` returns them.
   - If none exist, record `task_list_tool: none` in the readiness record and switch to the runner-rendered progress block. Do not mirror silently into `autopilot-state.json`.
   - On Codex, check for `update_plan` in the tool list before Phase 1. If absent, record `plan_tool: none`. Do not treat a failed call as the first signal.
   - Accept either tool family on Claude Code; never hard-code `TaskCreate` alone.
   A prose check is model-judged, so it is the weakest layer. Pair it with an assertion the runner can verify, such as requiring the model to write the detected tool names into the readiness record that the runner validates.

4. **Hook (limited).** A `SessionStart` hook receives `model` (optional, may be absent after `/clear` or recovery) and no tool list ([Hooks reference](https://code.claude.com/docs/en/hooks)). A hook can therefore only apply the model rule as a heuristic (model not in the listed families implies no tools unless opted in), and it cannot see env opt-ins or `--allowedTools` unless it reads its own environment (hook environment inheritance not confirmed). `PreToolUse` matchers can match tool names, but fire only when the model calls a tool, so they cannot prove absence. Use a hook for an early warning, not as the gate.

5. **Fallback behavior (needed regardless).** When no list tool exists, the phase 3 progress block rendered by the runner is the visible plan. The state file stays the durable record, not a silent substitute for a missing declared capability.

## Unconfirmed

- The model of the two autopilot runs that had no task tools. The model rule explains the symptom, but no run metadata was available here.
- Whether the Task tools or `TodoWrite` can ever appear as deferred tools behind `ToolSearch`. Docs say "left out"; the MCP tool-search section was not fully read.
- Whether the init message `tools` array includes deferred tool names.
- Behavior of the desktop app, VS Code panel and GitHub Actions for these tools (docs silent).
- Whether `deny` rules or `--disallowedTools` remove the task tools (general mechanism only).
- Whether hook processes inherit `CLAUDE_CODE_ENABLE_TODO_TOOLS`.
- Codex: the exact first release with the opt-in default (inferred 0.152.0), exec versus TUI parity by execution, and subagent inheritance of the flag.
- The Claude changelog was read through a summarizing fetch; entries on these tools between 2.1.213 and 2.1.287 other than 2.1.285 may be missing.

## Sources

- Claude Code docs: [Tools reference](https://code.claude.com/docs/en/tools-reference), [Environment variables](https://code.claude.com/docs/en/env-vars), [Interactive mode, Task list](https://code.claude.com/docs/en/interactive-mode#task-list), [Agent SDK, Track todos](https://code.claude.com/docs/en/agent-sdk/todo-tracking), [Hooks reference](https://code.claude.com/docs/en/hooks), [MCP](https://code.claude.com/docs/en/mcp), [Changelog](https://code.claude.com/docs/en/changelog).
- Codex: openai/codex source at main commit b707714 (2026-10-01) and tags `rust-v0.156.0`; PRs [#35054](https://github.com/openai/codex/pull/35054) and [#41744](https://github.com/openai/codex/pull/41744); [config reference](https://learn.chatgpt.com/docs/config-file/config-reference).
- Local: `claude --help`, `codex exec --help`, headless init-message runs (Claude Code 2.1.287, Codex CLI 0.156.0).
- Repository: autopilot skill text in `speckit-pro/skills/speckit-autopilot/SKILL.md` (Claude block "Before executing any phase, create a granular task list using TaskCreate"; Codex block "Runtime Contract") and `references/post-implementation.md`; Codex eval adapter `tests/speckit-pro/lib/native_eval_codex_adapter.py`.
