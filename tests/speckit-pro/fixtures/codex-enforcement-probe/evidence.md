# Codex custom-agent enforcement probe

**Verdict:** under `codex-cli 0.156.0`, a custom agent file enforces neither
limit, but a project `PreToolUse` hook can enforce both for one agent type.

- **Agent file `sandbox_mode = "read-only"`: advisory only.** The spawned
  child ran with the parent's `workspace-write` sandbox, and its shell write
  succeeded.
- **Agent file `enabled_tools`: no form works.**
  - `mcp_servers.research-broker.enabled_tools` with no transport makes Codex
    reject the whole agent file ("invalid transport"). The agent can then not
    be spawned at all.
  - `plugins."speckit-pro@racecraft-plugins-public".mcp_servers.research-broker.enabled_tools`
    is accepted and ignored: `research_search` stays callable.
  - A complete agent-local `[mcp_servers.research-broker]` stdio definition
    with `enabled_tools` is accepted and ignored: the plugin's own server
    still supplies both tools.
- **Project hook: enforces per role.** Every `PreToolUse` payload for a call
  made by the spawned agent carries `agent_type` (the custom agent's `name`)
  and `agent_id`. Payloads for the parent's own calls carry neither. A hook in
  the project's `.codex/hooks.json` that denies by `agent_type` blocked the
  child's shell write, its `apply_patch` file creation, and its
  `research_search` call, while the parent's shell write in the same run
  succeeded. The Codex hooks guide lists `agent_type` only for
  `SubagentStart`, so this field is observed, not documented.
- **Hook inside the agent file: ignored.** An inline `[[hooks.PreToolUse]]`
  table in the agent file never ran; the child's write and `research_search`
  both succeeded.

The agent files did reach the child. `developer_instructions` (the nonce) and
`model_reasoning_effort = "medium"` (the parent ran at `low`) both applied.
The parent passed `-c model_reasoning_effort="low"` on the command line and
the file's `medium` still won; the file's `sandbox_mode` did not. So the file
overrides a command-line effort but not the parent's sandbox.

## Limits of the hook result

- A hook cannot tell a shell write from a shell read in general. The probe
  hook matched `>` in the command, which is a test device, not a policy. A
  read-only role's shell writes therefore stay a prose rule; its
  `apply_patch` edits and its MCP calls can be denied by hook.
- Hooks are guardrails, not a boundary: the guide says some specialized tool
  paths can opt out of the hook path. Every call in this probe, including
  calls wrapped in the child's code-mode `exec` script, did reach the hook.
- Non-managed hooks run only after the operator trusts them. The probe used
  `--dangerously-bypass-hook-trust`, so no hook trust was recorded.

## Conditions

- Date: 2026-09-29. `codex-cli 0.156.0`, `codex exec --json`, model
  `gpt-6-luna`. Eight counted runs: five agent-file cases and three hook
  cases.
- Throwaway projects outside the repository, trusted by a `-c
  projects."<probe-project>".trust_level="trusted"` override. Codex persisted
  that override: it appended a `[projects."<probe-project>"] trust_level =
  "trusted"` entry per probe project to the operator's `~/.codex/config.toml`.
  The probe wrote no other user config, and no hook trust.
- The parent's sandbox came from the operator's user config
  (`sandbox_mode = "workspace-write"`, `approval_policy = "on-request"`). The
  probe passed no sandbox or approval flag.
- `speckit-pro@racecraft-plugins-public` 2.38.2 was installed and enabled.
  Nothing was installed or refreshed for the probe.
- The Codex subagent documentation says the parent's live sandbox and approval
  overrides are reapplied to a child "even if the selected custom agent file
  sets different defaults". The readonly result matches that rule for a
  parent whose sandbox comes from config. The probe did not test a parent that
  itself runs read-only.

## Agent-file cases (`run-probe.py`)

Each case wrote one agent file under `<probe-project>/.codex/agents/` and ran
one parent that spawned it with `fork_turns = "none"`. The baseline ran on an
earlier script revision: its child was a fork of the parent's context (its
rollout carries `forked_from_id`), and its agent file set effort `low`.
Evidence comes from the child's own rollout: `session_meta.thread_source =
"subagent"`, its `agent_role`, and its `turn_context`.

| Case | Agent file limit | Child effort | Child sandbox | Result |
| --- | --- | --- | --- | --- |
| baseline | none | low | workspace-write | Write exit 0; `docs_query` and `research_search` both listed; `research_search` dispatched (`broker_error:invalid_request`) |
| readonly | `sandbox_mode = "read-only"` | medium | workspace-write | `printf ok > readonly-write.txt` exit 0; the file exists |
| mcp-top | `[mcp_servers.research-broker] enabled_tools = ["docs_query"]` | n/a | n/a | Agent file rejected: "failed to deserialize agent role file ...: invalid transport"; spawn failed |
| mcp-plugin | `[plugins."speckit-pro@racecraft-plugins-public".mcp_servers.research-broker] enabled_tools = ["docs_query"]` | medium | workspace-write | `research_search` listed and dispatched (`broker_error:invalid_request`) |
| mcp-top-full | `[mcp_servers.research-broker]` with `command`, `args`, `cwd` = installed plugin root, `enabled_tools = ["docs_query"]` | medium | workspace-write | Both tools listed as "part of plugin `SpecKit Pro`"; `research_search` dispatched |

`research_search` was called with a query of one space. The broker rejects that
as `invalid_request` before any network call, so a dispatched call proves the
tool is reachable without billing a search. The first readonly run is not
counted: the parent forked its whole context, and the model declined the write
on its own after reading the case name, so the sandbox was never exercised.
Its rollout also showed `sandbox_policy = workspace-write`.

## Hook cases (`run-hook-probe.py`)

In each case the parent first ran `printf ok > parent-write.txt` itself, then
spawned `probe_hook_child`. The hook script logged every payload it received.

| Case | Hook location and policy | Parent write | Child calls |
| --- | --- | --- | --- |
| hook-project | project `.codex/hooks.json`; deny when `agent_type` is `probe_hook_child` | exit 0, not denied | shell write denied ("Command blocked by PreToolUse hook"), `research_search` denied ("Tool call blocked by PreToolUse hook"); no `child-write.txt` |
| hook-project-patch | same hook; the child writes with `apply_patch` | exit 0, not denied | `apply_patch` denied; no `child-patch.txt` |
| hook-agent | inline `[[hooks.PreToolUse]]` in the agent file; deny unconditionally | exit 0 | hook never ran; shell write exit 0, `research_search` dispatched |

The hook log (`hook_log` in the excerpts) shows the payload keys. The parent's
`PreToolUse` payloads hold `cwd`, `hook_event_name`, `model`,
`permission_mode`, `session_id`, `tool_input`, `tool_name`, `tool_use_id`,
`transcript_path` and `turn_id`. The child's payloads hold the same keys plus
`agent_id` and `agent_type`.

## Consequence for the generator

- `sandbox_mode` is derived and emitted only as an advisory key
  (`advisory_config_keys`). No check or doc may call it enforced.
- No `enabled_tools` key is emitted.
- `derive_codex_hook_policy` states the per-role hook policy that this probe
  shows Codex enforces: deny `apply_patch` for read-only roles, and deny
  every MCP tool outside a role's broker allowlist. It is a library function
  in this slice; no shipped hook changes.
- A read-only role's shell writes stay a prose rule.

## Files

- `rollout-excerpts.json`: one JSON line of redacted excerpts per case: parent
  errors, the child's role, `turn_context` effort and sandbox, tool calls and
  outputs, final messages, and, for hook cases, the hook log. Session ids,
  account ids, home and temp paths, and the encrypted spawn messages are
  replaced with placeholders.
- `run-probe.py` and `run-hook-probe.py`: the opt-in rerun scripts. They are
  Python standard library, are not in any suite, and bill the operator's Codex
  account.
