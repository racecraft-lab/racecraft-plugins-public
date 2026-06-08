# Prerequisites Reference

The autopilot's pre-flight sequence. Run these before Step 1 (Parse Workflow State) and before any phase work. If any check fails, STOP with the error message from the script's JSON output.

## Contents

- [Step -1: Archive Sweep Startup](#step--1-archive-sweep-startup) — archive previously merged specs before workflow execution
- [Step 0.0: Resolve Script Paths](#step-00-resolve-script-paths) — extract `SKILL_SCRIPTS` from the skill header (plugin path)
- [Step 0.1–0.7: Environment Checks](#step-01-07-environment-checks) — `check-prerequisites.sh` JSON parsing, branch detection
- [Step 0.6: Load Settings](#step-06-load-settings) — `.claude/speckit-pro.local.md` YAML frontmatter
- [Step 0.8: MCP Server & Plugin Limitation Check](#step-08-mcp-server--plugin-limitation-check) — informational MCP report + plugin-agent caveats
- [Step 0.9: Constitution Validation](#step-09-constitution-validation) — principle checks against current codebase
- [Step 0.10: Implementation Agent Detection](#step-010-implementation-agent-detection) — discover `PROJECT_IMPLEMENTATION_AGENT`
- [Step 0.11: Project Command Discovery](#step-011-project-command-discovery) — `detect-commands.sh` → `PROJECT_COMMANDS`
- [Step 0.12: Preset and Extension Detection](#step-012-preset-and-extension-detection) — `detect-presets.sh` → `PRESET_CONVENTIONS`

## Step -1: Archive Sweep Startup

Before Step 0 and before any requested spec phase work, run Archive Sweep
to archive previously merged specs.

1. Determine the current target spec from the workflow file's `Spec Directory`
   field, the `--spec` override, or the active `specs/**` path in the workflow.
2. Detect archive extension state from `.specify/extensions.yml`,
   `.specify/extensions/.registry`, and `.specify/extensions/archive/extension.yml`.
3. If the archive extension is installed, determine the sweep mode from the
   current branch:

   **Feature / spec worktree branch** (normal autopilot case — run with actual
   cleanup):
   ```text
   /speckit-archive-run --sweep --current-target <current-spec-dir>
   ```

   **`main`, a release branch, or any protected integration branch** (dry-run
   only — do not delete spec folders on the integration branch):
   ```text
   /speckit-archive-run --sweep --current-target <current-spec-dir> --dry-run
   ```

4. Archive Sweep may archive/clean up only previously merged specs. It MUST
   exclude the current target spec until a later run sees that spec as merged.
5. Record sweep output in the workflow notes: eligible previous specs, excluded
   current spec, archive extension installed state, cleanup mode, and
   `safeToApplyCleanup`.
6. Add an `Archive Sweep: previously merged specs archived` task before Phase 0
   in the visible task list.

If the archive extension is missing, record `archive_extension_installed=false`,
keep cleanup disabled, and continue only after warning that the project should
install or vendor `racecraft-lab/spec-kit-archive` for archive-aware cleanup.

## Step 0.0: Resolve Script Paths

The autopilot's bash scripts ship with the **plugin**, not the
project. Before running any script, resolve the absolute path
to the scripts directory from the skill's base directory.

When this skill is loaded, Claude Code prints:
`Base directory for this skill: /path/to/...`

Extract that path and append `/scripts` to get the scripts dir.
Store the result as `SKILL_SCRIPTS` for all subsequent commands:

```text
SKILL_SCRIPTS="<base directory from skill header>/scripts"
```

For example, if the header says:
`Base directory for this skill: <HOME>/.claude/plugins/cache/racecraft-plugins-public/speckit-pro/1.1.0/skills/speckit-autopilot`

Then:
```text
SKILL_SCRIPTS="<HOME>/.claude/plugins/cache/racecraft-plugins-public/speckit-pro/1.1.0/skills/speckit-autopilot/scripts"
```

Verify the directory exists:

```text
Bash("ls '<SKILL_SCRIPTS>/'")
```

If it doesn't exist, STOP: "Plugin scripts not found. Reinstall
the speckit-pro plugin."

**All script invocations below use the resolved `SKILL_SCRIPTS`
path as prefix.** Never run these scripts from
`.specify/scripts/bash/` — that directory contains project-level
SpecKit scripts (create-new-feature, setup-plan, etc.), which are
different from the autopilot scripts.

**WARNING:** `CLAUDE_PLUGIN_ROOT` is NOT available in Bash tool
invocations — it only exists inside agent subprocesses. Always use
the literal path extracted from the skill header.

## Step 0.1–0.7: Environment Checks

```text
Bash("bash '<SKILL_SCRIPTS>/check-prerequisites.sh' <workflow_file_path>")
```

Parse the JSON result:
- `all_pass`: if `false`, report each failed check's `message` and STOP
- `branch`: current git branch name
- `on_feature_branch`: if `true`, Specify must skip branch creation
- `is_worktree`: if `true`, already in an isolated worktree

If `on_feature_branch` is `true`, verify the branch matches the
workflow file's `Branch` field. Warn if they don't match.

**Important:** Environment variables set in Bash do NOT persist to
Skill tool invocations. The autopilot handles branch context by
adjusting how it invokes each phase (see Phase Dispatch).

## Step 0.6: Load Settings + Detect Agent Teams Capability

### Settings file

Read `.claude/speckit-pro.local.md` if it exists. Parse YAML
frontmatter for: `consensus-mode` (default: `moderate`),
`gate-failure` (default: `stop`), `auto-commit` (default:
`per-phase`), `security-keywords` (default: standard list).
If the file doesn't exist, use all defaults.

### Agent Teams capability probe

Agent Teams is a **capability**, not a user setting. The autopilot
probes for it at startup and routes anywhere-it's-beneficial work to
teams when available, otherwise falls back to highly-parallel
subagent dispatch. Users do not opt-in — if Anthropic has enabled
Agent Teams on this machine, speckit-pro uses it.

Probe two conditions:

```text
Bash("test \"${CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS}\" = \"1\"")
Bash("claude --version | awk '{print $1}' | sort -V -C 2.1.32")
```

1. **Env var:** `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set
   (per [Anthropic's Agent Teams docs](https://code.claude.com/docs/en/agent-teams))
2. **Version:** `claude --version` returns ≥ `2.1.32`

Record the result as `AGENT_TEAMS_AVAILABLE = true|false` in the
workflow file's Notes section. Pass this flag to dispatch decisions
downstream — it is not user-tunable.

When `AGENT_TEAMS_AVAILABLE` is `false`, log to the workflow file:

> Agent Teams not detected (env var unset OR Claude Code < 2.1.32).
> Using parallel-subagents dispatch for post-impl. To enable Agent
> Teams (which adds inter-teammate messaging and shared task lists),
> set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` and upgrade Claude
> Code to ≥ 2.1.32, then re-run.

**Do not STOP** — both code paths complete the autopilot correctly.
Agent Teams is a quality-and-coordination enhancement, not a
dependency. The subagents fallback is itself parallel (background
dispatch in one tool call) so wall-clock is comparable.

Dispatch details for both code paths live in
[`post-implementation.md`](./post-implementation.md) §Post-Implementation Parallel Group.
The full **use-site map** (post-impl, consensus, Phase 7 `[P]` tasks,
parallel checklist/analyze) and lifecycle policy live in
[`agent-teams-integration.md`](./agent-teams-integration.md).

## Step 0.8: MCP Server & Plugin Limitation Check

The prerequisite script now reports MCP server availability.
This is **informational, not blocking** — all agents include
built-in fallbacks. Parse the `mcp_servers` check from the
JSON output and report which servers are available vs. missing.

**Plugin agent limitations:** Because these agents run from a
plugin, Claude Code silently ignores `permissionMode`, `hooks`,
and `mcpServers` frontmatter fields. All agents inherit the
parent session's permission mode. Ensure the parent session
runs in `acceptEdits` or `bypassPermissions` mode for smooth
autopilot execution. See `references/plugin-limitations.md`
for details and workarounds.

## Step 0.9: Constitution Validation

Read the workflow file's Prerequisites table. If already
`Verified`, skip (resuming a workflow). Otherwise:

1. Read constitution from `.specify/memory/constitution.md`
2. For each principle, run the appropriate PROJECT_COMMANDS
   check (typecheck, test suite, build, lint). For code
   review items (KISS, YAGNI, SOLID), mark `Verified` —
   these are validated during implementation.
3. Update the workflow file's table with results and baselines
4. If any check fails, STOP — do not proceed to Phase 1

## Step 0.10: Implementation Agent Detection

Detect whether the project has a specialized implementation
agent for the Implement phase. This avoids hardcoding agent
names and makes the plugin work with any project.

```text
1. Glob(".claude/agents/*.md") to find all project agents
2. For each agent file, read the YAML frontmatter
3. Check the description for implementation keywords:
   "implement", "TDD", "development", "developer",
   "coding", "build", "test-first"
4. If exactly one match → record its name as
   PROJECT_IMPLEMENTATION_AGENT
5. If multiple matches → pick the one with the most
   specific description (or ask the user)
6. If no matches → set PROJECT_IMPLEMENTATION_AGENT to
   "phase-executor" (fallback)
```

Also check CLAUDE.md for references to a specific
implementation agent (e.g., "my-project-developer" or
"use the X agent for implementation").

**Record the result** for use in Step 2's Implement phase.

## Step 0.11: Project Command Discovery

```text
Bash("bash '<SKILL_SCRIPTS>/detect-commands.sh'")
```

Parse the JSON result for `commands` object containing:
BUILD, TYPECHECK, LINT, LINT_FIX, UNIT_TEST,
INTEGRATION_TEST, SINGLE_FILE_TEST, SINGLE_FILE_INTEGRATION,
FULL_VERIFY. Commands set to `"N/A"` are skipped during
verification. The script auto-detects Node.js, Rust, Go,
Python, and Makefile projects.

**Also check CLAUDE.md** for a "Build Commands" table — it's
the most authoritative source and may override script results.

Record PROJECT_COMMANDS in the workflow file so they persist
across context compactions. Pass them to every subagent.

## Step 0.12: Preset and Extension Detection

```text
Bash("bash '<SKILL_SCRIPTS>/detect-presets.sh'")
```

Parse the JSON result for: `has_presets`, `presets` (names +
templates they override), `extensions`, `hooks`, and
`templates` (resolved paths for tasks/spec/plan templates).

If `has_presets` is `true`:
1. Read each preset's overridden templates to understand
   the conventions it enforces (TDD, architecture, etc.)
2. Record as PRESET_CONVENTIONS for subagent prompts
3. Include PRESET_CONVENTIONS in ALL subagent prompts —
   presets affect every phase, not just implement

If no presets AND no extensions, skip this step.
