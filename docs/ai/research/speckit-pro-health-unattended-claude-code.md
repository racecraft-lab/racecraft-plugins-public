# What pauses an unattended Claude Code run

Ticket: #1018. Map: #1006. Checked against Claude Code 2.1.287 and Codex CLI 0.156.0 (local `--help`), the Claude Code docs, the Codex docs, and the openai/codex source (shallow clone, commit b707714).

## Answer first

1. **Four things can stop a run, but only two wait on a human.** Permission prompts and the question tools (`AskUserQuestion`, `ExitPlanMode`) wait for a person. A subagent `maxTurns` limit and context compaction do not wait: the first returns partial output, the second runs on its own.
2. **A plugin cannot ship the configuration that removes a permission wait.** Plugin `settings.json` honors only `agent` and `subagentStatusLine`. Allow rules, `defaultMode` and `--permission-mode` belong to the user, project or managed settings, or to the launch command. A plugin can only detect the gap (run-start probe) and print the rule to add. Plugin subagents also ignore `permissionMode`, `hooks` and `mcpServers` frontmatter.
3. **No mode skips `AskUserQuestion`.** `bypassPermissions` does not approve it. `dontAsk` denies it. Auto mode does not answer it. Only these remove it: `--permission-prompts none` (print mode), a `PreToolUse` hook that denies it, a `--disallowedTools AskUserQuestion` rule, or the opt-in `askUserQuestionTimeout` setting.
4. **Yes, a plugin-shipped `PreToolUse` hook can deny `AskUserQuestion`** on Claude Code, per the docs (not live-tested). Matcher is `AskUserQuestion`. The deny reason is shown to the model. Subagents never receive `AskUserQuestion`, so the hook only matters on the main thread. In `-p` the tool is offered only when a permission host exists, so the hook matters there only in that case. The "19 questions in 8 calls" fits the tool schema (1 to 4 questions per call), so every call was a main-thread call that prose did not stop.
5. **Codex has two layers.** Config `[tools.experimental_request_user_input] enabled = false` removes the tool from the model. A plugin-bundled `PreToolUse` hook with matcher `request_user_input` can deny it, but this rests on docs and source reading, not a live run. `codex exec` already rejects the request instead of waiting, and the tool is Plan-mode only by default.

## Pause sources

| Pause source | Trigger | Ahead-of-time detection | Config that removes the wait | Source |
| :- | :- | :- | :- | :- |
| Permission prompt (manual or default mode) | Tool call not covered by an allow rule or mode | No "would this prompt" query exists. Run the call once at start (speckit-pro Step -2 probe does this for the runner and `git status`). Hook input carries `permission_mode`. A `PermissionRequest` hook fires when a prompt is about to show. A `Notification` hook with type `permission_prompt` fires after about 6 s. | `permissions.allow` rules in user, project or local settings. `--allowedTools`. `--permission-mode acceptEdits`, `auto` or `bypassPermissions`. In `-p`, anything that would prompt is auto-denied (no wait, but a failed call). A plugin cannot set any of these. | hooks, permissions, permission-modes, headless |
| Permission prompt in `-p` with a host | `-p` run with Agent SDK `canUseTool` or `--permission-prompt-tool` | Run has a host flag at launch. | `--permission-prompts none` (v2.1.259+) denies instead of asking the host. | headless |
| Auto mode fallback | Classifier blocks 3 in a row or 20 total | Not detectable ahead of time. Counters are fixed and not configurable. `permission_denials` in `stream-json` results after the fact. | Interactive: prompts resume. `-p` without host: the action is skipped and the run continues. Reduce blocks with trusted-infrastructure config. | permission-modes |
| Auto mode unavailable | Model, plan, org policy or server flag | Session starts in Manual instead. Check `permission_mode` in a hook input at start. | Pass `--permission-mode` explicitly. `auto` and `bypassPermissions` from project or local settings do not take effect. Set them in user or managed settings or on the command line. | permission-modes, settings |
| Hook `ask` or hook denial | A hook returns `permissionDecision: "ask"` or exit 2 / `"deny"` | Read the hook files (static). Deny is not a pause: the model sees the reason and continues. `"ask"` forces a prompt, even in auto mode. | Do not return `ask` in unattended paths. Return `deny` with a reason. Deny and ask rules are evaluated even when a hook returns `allow`. | hooks |
| `AskUserQuestion` | Model calls it on the main thread | Static: grep skills for the tool name. Runtime: a `PreToolUse` hook sees every call. | See the next section. `bypassPermissions` does not help. `dontAsk` denies it. | hooks, permission-modes, tools-reference |
| `ExitPlanMode` | Plan mode approval | `permission_mode` is `plan` in hook input. | Do not start in `plan`. A `PreToolUse` `allow` needs `updatedInput`. | hooks |
| Subagent `maxTurns` | Agent frontmatter limit reached (speckit-pro agents: 10 to 100) | Static: read `maxTurns` in `agents/*.md`. A `SubagentStop` hook sees the stop. | Raise or remove `maxTurns` (default when omitted: unconfirmed). Output returns marked partial (v2.1.246+); the parent can resume the subagent. In `-p`, `--max-turns` is off by default and exits with an error at the limit. | sub-agents, cli-reference |
| Context compaction | Context reaches the auto-compact window, or `/compact` | `PreCompact` and `PostCompact` hooks. `SessionStart` with source `compact`. | No human wait. Move the window with the auto-compact window setting. A `PreCompact` block can skip compaction, or fail the request if the API already returned a context-limit error. Re-inject state from a `SessionStart` `compact` hook. | hooks, model-config, context-window |

## Question-tool hook on both hosts

### Claude Code

Plugin `hooks/hooks.json`. Same file format speckit-pro already uses for its `Bash` and `Agent` hooks.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "AskUserQuestion",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/question-tool-guard.py deny",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

Hook stdout (exit 0). Exit 2 with the reason on stderr routes the same way.

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Autopilot is unattended. Do not ask. Pick the recommended option, record the assumption, and continue."
  }
}
```

What the docs confirm:

- **Matcher.** `PreToolUse` matches any tool name, and the docs list `AskUserQuestion` and `ExitPlanMode` as matchable names.
- **Model sees the reason.** For `deny`, `permissionDecisionReason` is shown to Claude. For `ask` it is shown only to the user.
- **Precedence.** `deny` beats `defer`, `ask` and `allow`.
- **Plugin hooks run in subagents** and carry `agent_id` and `agent_type`. This is moot for this tool: `AskUserQuestion` is removed from every subagent, even when listed in `tools`.
- **`-p`.** The tool is offered only with a permission host. With `--permission-prompts none` the tool is removed. Without a host, the tool is not offered. The hook is the guard for the host case and for interactive sessions. `--bare` skips hook and plugin discovery, so a bare run has no plugin hook.
- **Do not use `allow` or `defer` here.** `allow` alone does not satisfy the tool; it needs `updatedInput.answers`. `defer` pauses the run for a caller and is for SDK integrations.

Simpler non-hook options, none of which a plugin can set: `claude -p ... --permission-prompts none`, `--disallowedTools AskUserQuestion`, or a `permissions.deny` entry `AskUserQuestion` in user or project settings. The `askUserQuestionTimeout` setting (60s, 5m or 10m; user `settings.json` or `/config`) lets an unanswered question close and tell the model the user may be away. It is a fallback, not a block.

Not confirmed by a live run: that a plugin hook (as opposed to a settings hook) denies `AskUserQuestion` in a real session. The docs say plugin hooks use the same events and that `PreToolUse` matches this tool. Verify with one interactive session before relying on it.

### Codex

Plugin-bundled hooks, default path `hooks/hooks.json` in the plugin root (or a `hooks` entry in `.codex-plugin/plugin.json`). Use the same shape speckit-pro's `codex-hooks.json` already uses.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "request_user_input",
        "hooks": [
          {
            "type": "command",
            "command": "${PLUGIN_ROOT}/scripts/question-tool-guard.py deny",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

Same deny JSON as above (`hookSpecificOutput.permissionDecision: "deny"`). Codex also accepts the older `{"decision":"block","reason":"..."}`.

What the docs and source confirm:

- **Coverage.** The Codex hooks doc says `PreToolUse` covers "other local function tools" by function name. In source, the registry default builds a `PreToolUse` payload for every function-payload tool, and `request_user_input` has no override that opts out. The tool is registered as a plain function tool, so the matcher name is `request_user_input`.
- **Doc caveat.** "Some specialized tool paths can opt out of the default hook path. Treat tool hooks as a useful guardrail, not a complete enforcement boundary."
- **Trust.** Codex skips plugin-bundled hooks until the user reviews and trusts the current definition. `--dangerously-bypass-hook-trust` exists in `codex --help`, so an unattended launch needs the hook trusted first.
- **Config alternative that removes the tool.** In `config.toml`:

```toml
[tools.experimental_request_user_input]
enabled = false
```

  Source: `ToolsToml.experimental_request_user_input`, default enabled; when disabled the handler is never registered. Config belongs to the user, not the plugin.
- **Already limited.** The tool is available only in Plan collaboration mode unless the under-development feature `default_mode_request_user_input` is enabled (default off). Non-root agents get "request_user_input can only be used by the root thread". `codex exec` rejects the server request with "request_user_input is not supported in exec mode".
- **Approvals are a separate axis.** `approval_policy = "never"` (`-a never`) removes command approval waits. It does not govern `request_user_input`.

Not confirmed by a live run: that the `PreToolUse` hook fires for `request_user_input` in Codex 0.156.0. Source reading supports it; one Codex session in Plan mode with the hook would settle it.

## Evidence from real runs (ticket-reported, not re-run here)

- The permission probe prompting or being denied matches the docs: plugin agents inherit the session's permission settings, `acceptEdits` does not cover arbitrary commands, and in `-p` a would-be prompt is a denial.
- The turn-limit stops match frontmatter in this repo: `maxTurns` is 10 (artifact-preview-observer, sweep-classifier), 20 (sweep-analyst), 30 (consensus-tiebreaker, consensus-synthesizer), 35 (clarify-executor), 60 (codebase-analyst), 100 (implement-executor, phase-executor). Partial output is expected behavior, not a crash.
- Two compactions in one run are normal. Nothing waits for a human. The risk is lost state, covered by the `SessionStart` `compact` matcher the plugin already uses for its attest hook.
- Prose forbids the tool in `phase-execution.md`, but nothing enforces it. The question calls were model behavior against text. Only a hook, a deny rule or a removed tool enforces it.

## What speckit-pro has today

- `hooks/hooks.json`: `SessionStart` (startup, resume, clear, compact), `PreToolUse` on `Agent`, the sweep-broker tools and `Bash`, `SubagentStop`, `Stop`. No `AskUserQuestion` matcher.
- `codex-hooks.json`: `PreToolUse` on `Bash` and on `apply_patch|mcp__.*`, plus `Stop`. No `request_user_input` matcher.
- Step -2 run-start permission probe: runs one no-op runner request and one `git status`, prints the allow rules, and stops once.

## Unconfirmed items

- Default `maxTurns` when the frontmatter field is omitted: not stated in the sub-agents page.
- `--max-turns` is documented in the CLI reference but does not appear in local `claude --help` output (2.1.287). Treat it as documented, not locally verified.
- Whether `askUserQuestionTimeout` is honored from project scope: docs name user `settings.json` and `/config` only.
- Both live hook-denial checks above.
- Run evidence (probe prompts, 19 questions, two compactions) comes from the ticket text. I did not read the private run logs.

## Sources

Claude Code docs (fetched as markdown from code.claude.com/docs/en/):
- hooks: PreToolUse input and decision control, AskUserQuestion input, `defer`, PermissionRequest, PreCompact and PostCompact, SessionStart matchers, hooks in subagents.
- permissions and permission-modes: modes, which mode a session starts in, auto mode fallback and thresholds, actions no mode auto-approves, `dontAsk` behavior.
- headless: `--allowedTools`, `--permission-mode`, `--permission-prompts none`.
- cli-reference: `--max-turns`, `--disallowedTools`, `--dangerously-skip-permissions`, `--bare`.
- sub-agents: `maxTurns`, partial output, tools removed from every subagent, plugin subagent field limits.
- plugins-reference and plugins/components: plugin `settings.json` honors only `agent` and `subagentStatusLine`.
- tools-reference: AskUserQuestion tool behavior, `askUserQuestionTimeout`.
- settings: `auto` and `bypassPermissions` `defaultMode` not honored from project or local settings.
- model-config and context-window: auto-compact window.
- Local `claude --help` (2.1.287).

Codex:
- developers.openai.com/codex/hooks.md: tool coverage, PreToolUse deny shapes, plugin-bundled hooks and trust.
- developers.openai.com/codex/config-reference.md: `approval_policy`.
- openai/codex source at commit b707714: `codex-rs/core/src/tools/registry.rs` (default `pre_tool_use_payload`), `codex-rs/core/src/tools/handlers/request_user_input.rs` (root-thread and mode checks), `codex-rs/core/src/tools/spec_plan.rs` (registration gated on config), `codex-rs/core/src/config/mod.rs` (`tools.experimental_request_user_input`), `codex-rs/protocol/src/config_types.rs` (Plan-only mode), `codex-rs/features/src/lib.rs` (`default_mode_request_user_input`), `codex-rs/exec/src/lib.rs` (exec-mode rejection).
- Local `codex --help` and `codex exec --help` (0.156.0).

Repo files read: `speckit-pro/hooks/hooks.json`, `speckit-pro/codex-hooks.json`, `speckit-pro/agents/*.md` (`maxTurns`), `speckit-pro/skills/speckit-autopilot/references/prerequisites.md` (Step -2), `plugin-limitations.md`, `phase-execution.md`.
