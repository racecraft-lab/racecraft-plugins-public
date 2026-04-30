# Plugin Agent Limitations

## Important: Security restrictions for plugin subagents

Claude Code silently ignores certain frontmatter fields when
loading agents from a plugin. This is a security measure
documented in the official Anthropic docs.

### Ignored fields (set in agent files but not applied)

| Field | Set To | Effect |
|-------|--------|--------|
| `permissionMode` | `acceptEdits` / `plan` | **Ignored.** Agents inherit the parent session's permission mode instead. |
| `hooks` | (any) | **Ignored.** Plugin agents cannot define lifecycle hooks. |
| `mcpServers` | (any) | **Ignored.** Plugin agents cannot declare their own MCP server connections. |

### What this means for the autopilot

1. **Permission mode inheritance:** All agents inherit the
   parent session's permission mode. If the parent runs in
   `default` mode, every agent will prompt for permission
   on every edit — making the autopilot impractical.

   **Required:** Run the parent session in `acceptEdits` or
   `bypassPermissions` mode before launching the autopilot:
   ```
   claude --permission-mode acceptEdits
   ```

2. **MCP tool availability:** Agents that reference MCP tools
   (`mcp__tavily-mcp__*`, `mcp__context7__*`,
   `mcp__RepoPrompt__*`) can only use them if the parent
   session has those MCP servers configured and connected.

   The agents define fallback tool chains (e.g.,
   `mcp__tavily-mcp__tavily-search` falls back to
   `WebSearch`), so the autopilot functions without MCP —
   but with reduced research quality.

3. **Consensus agents are not read-only:** The consensus
   agents (`codebase-analyst`, `spec-context-analyst`,
   `domain-researcher`) set `permissionMode: plan` to
   enforce read-only operation. Since this is ignored in
   plugins, they inherit the parent's mode. In practice,
   their instructions and tool lists (`Read`, `Grep`, `Glob`)
   constrain them to read-only behavior, but the system-level
   enforcement is absent.

### Workaround: Copy agents to local scope

To get full frontmatter support, copy agents from the plugin
to your project or user agent directory:

```bash
# Copy to project scope
cp -r ~/.claude/plugins/marketplaces/*/plugins/speckit-pro/agents/*.md .claude/agents/

# Or copy to user scope
cp -r ~/.claude/plugins/marketplaces/*/plugins/speckit-pro/agents/*.md ~/.claude/agents/
```

Agents in `.claude/agents/` or `~/.claude/agents/` have full
frontmatter support including `permissionMode`, `hooks`, and
`mcpServers`.

## MCP Server Prerequisites

The following MCP servers enhance agent capabilities. All are
optional — agents include built-in fallbacks.

| MCP Server | Used By | Fallback |
|------------|---------|----------|
| `tavily-mcp` | analyze-executor, checklist-executor, clarify-executor, domain-researcher | `WebSearch` + `WebFetch` |
| `context7` | analyze-executor, checklist-executor, clarify-executor, domain-researcher | `WebSearch` for "[library] docs" |
| `RepoPrompt` | analyze-executor, checklist-executor, clarify-executor, codebase-analyst | `Grep` + `Glob` + `Read` |

### Verifying MCP connectivity

Before running the autopilot, verify connected MCP servers:
```
/mcp
```

If a required server is not connected, the agent will
automatically fall back to built-in tools. Functionality
is preserved but research quality may be reduced.

## Skills the autopilot must not invoke

Some skills in this plugin are deliberately scoped to interactive,
human-in-the-loop usage and **must never be invoked from inside
autopilot or any of its phase agents**. Calling them would either
block the autonomous loop waiting on user input or produce
low-quality automated output that defeats the skill's purpose.

| Skill | Why it's forbidden inside autopilot |
|-------|------------------------------------|
| `grill-me` | Uses `AskUserQuestion` to interview a real human one question at a time. Inside autopilot there is no user to answer. Autopilot's Clarify phase uses `/speckit.clarify` with the consensus protocol instead — that is the only sanctioned clarification mechanism in the autonomous loop. If a phase hits ambiguity that consensus can't resolve, fail the gate and surface to the user; never escalate to grill-me. |

The hard constraint is enforced in three independent layers:

1. The autopilot orchestrator's `<hard_constraints>` block (in
   `../SKILL.md` under "Critical: Execution Rules → 0. Forbidden
   skill invocations").
2. A negative constraint in each phase-executor agent's system
   prompt under `agents/` and `codex-agents/`.
3. A self-check inside the `grill-me` skill that aborts if it
   detects a non-interactive or agent context.
