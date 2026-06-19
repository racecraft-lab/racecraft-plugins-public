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

2. **Research/context capability coverage:** Agents can only use evidence
   capabilities that are available in the parent session. This includes
   codebase context, library documentation, web/domain research, and source
   extraction.

   When a stronger capability is unavailable, agents use their built-in
   fallback paths and record any confidence impact in the relevant workflow
   evidence. Missing optional coverage is advisory; it becomes blocking only
   when no acceptable evidence path remains or a true prerequisite/gate fails.

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

## Research/Context Capability Coverage

The following capabilities improve evidence quality. All are optional when an
acceptable fallback path exists:

| Capability | Used By | Fallback behavior |
|------------|---------|-------------------|
| Codebase context | analyze-executor, checklist-executor, clarify-executor, codebase-analyst | Use local repository reads and searches |
| Library documentation | analyze-executor, checklist-executor, clarify-executor, domain-researcher | Use available docs evidence or cite the fallback confidence limit |
| Web/domain research | analyze-executor, checklist-executor, clarify-executor, domain-researcher | Use available public-source evidence or mark reduced confidence |
| Source extraction | analyze-executor, checklist-executor, clarify-executor, domain-researcher | Use accessible source text or request escalation when no acceptable evidence path remains |

The prerequisite check reports this as a single `capability_coverage`
advisory. It does not ask users to install a fixed optional provider set.

## Skills the autopilot must not invoke

Some skills in this plugin are deliberately scoped to interactive,
human-in-the-loop usage and **must never be invoked from inside
autopilot or any of its phase agents**. Calling them would either
block the autonomous loop waiting on user input or produce
low-quality automated output that defeats the skill's purpose.

| Skill | Why it's forbidden inside autopilot |
|-------|------------------------------------|
| `grill-me` | Uses `AskUserQuestion` to interview a real human one question at a time. Inside autopilot there is no user to answer. Autopilot's Clarify phase uses `/speckit-clarify` with the consensus protocol instead — that is the only sanctioned clarification mechanism in the autonomous loop. If a phase hits ambiguity that consensus can't resolve, fail the gate and surface to the user; never escalate to grill-me. |

The hard constraint is enforced in three independent layers:

1. The autopilot orchestrator's `<hard_constraints>` block (in
   `../SKILL.md` under "Critical: Execution Rules → 0. Forbidden
   skill invocations").
2. A negative constraint in each phase-executor agent's system
   prompt under `agents/` and `codex-agents/`.
3. A self-check inside the `grill-me` skill that aborts if it
   detects a non-interactive or agent context.
