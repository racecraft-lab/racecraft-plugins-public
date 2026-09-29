# Codex custom-agent enforcement probe

**Verdict:** under `codex-cli 0.156.0`, a custom agent file enforces neither
limit. Both limits fall back to prose.

- `sandbox_mode = "read-only"` is not applied. The spawned child ran with the
  parent's `workspace-write` sandbox, and its shell write succeeded.
- No `enabled_tools` form hides a plugin-provided broker tool from the child:
  - `mcp_servers.research-broker.enabled_tools` with no transport makes Codex
    reject the whole agent file ("invalid transport"). The agent can then not
    be spawned at all.
  - `plugins."speckit-pro@racecraft-plugins-public".mcp_servers.research-broker.enabled_tools`
    is accepted and ignored: `research_search` stays callable.
  - A complete agent-local `[mcp_servers.research-broker]` stdio definition
    with `enabled_tools` is accepted and ignored: the plugin's own server
    still supplies both tools.

The same files did reach the child. `developer_instructions` (the nonce) and
`model_reasoning_effort = "medium"` (the parent ran at `low`) both applied, so
the agent file loaded and only the two limit keys were dropped. The parent passed
`-c model_reasoning_effort="low"` on the command line, and the file's
`medium` still won; the file's `sandbox_mode` did not. So the file overrides
a command-line effort but not the parent's sandbox.

## Conditions

- Date: 2026-09-29. `codex-cli 0.156.0`, `codex exec --json`, model
  `gpt-6-luna`.
- Throwaway project outside the repository, trusted only by a `-c
  projects."<probe-project>".trust_level="trusted"` override. No user config
  file was written.
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

## Cases

Each case wrote one agent file under `<probe-project>/.codex/agents/` and ran
one parent that spawned it with `fork_turns = "none"`. The baseline ran on an
earlier script revision: its child was a fork of the parent's context (its
rollout carries `forked_from_id`), and its agent file set effort `low`. Evidence comes from the child's own rollout:
`session_meta.thread_source = "subagent"`, its `agent_role`, and its
`turn_context`.

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

## Consequence for the generator

- The generator still derives `sandbox_mode` from the Claude allowlist. The
  key is harmless, the inventory's `codex.sandbox` checks it, and it may take
  effect when a parent does not override the sandbox. It is not an enforced
  limit, so read-only roles keep their prose rule.
- The generator derives the per-server broker allowlist as data, but emits no
  `enabled_tools` key: the top-level form breaks the agent file, and the
  plugin form is silently ignored. Broker-only roles keep their prose rule
  naming the allowed broker tools.

## Files

- `rollout-excerpts.json`: the minimal redacted excerpts per case: parent
  errors, the child's role, `turn_context` effort and sandbox, tool calls and
  outputs, and final messages. Session ids, account ids, home and temp paths,
  and the encrypted spawn messages are replaced with placeholders.
- `run-probe.py`: the opt-in rerun script. It is Python standard library, is
  not in any suite, and bills the operator's Codex account.
