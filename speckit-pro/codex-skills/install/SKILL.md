---
name: install
description: >
  Install or refresh the bundled SpecKit Pro Codex custom subagents.
  Copies the plugin's TOML agent templates into ~/.codex/agents/ by
  default, verifies the installed files, and tells the user to restart
  Codex so the new subagents load.
---

# SpecKit Install

## Scope

Use this skill when the user wants to install, refresh, repair, or
verify the **Codex custom subagents** that ship with this plugin.
This skill exists only for the Codex runtime. It does **not** manage
Claude Code agents, Claude marketplace metadata, or Claude commands.

It also does not initialize or migrate a project's knowledge bundle. The agents
installed here honor the SpecKit knowledge contract: read-only analysts may
return `knowledge_candidates`, evidence-only agents may not, and no worker
writes candidate or canonical knowledge files. Use `$speckit-install` for a new
project bundle or `$speckit-upgrade` for reviewed migration of an existing
project.

The bundled source of truth lives in the plugin at:

- `codex-agents/*.toml`

The default user-scope Codex destination is:

- `~/.codex/agents/`

If the user explicitly asks for project scope, use `.codex/agents/` in the
current project. Arbitrary destinations are rejected. Otherwise install to the
default user-scope path above.

## What This Skill Installs

This skill installs the bundled TOML subagent templates that the
Codex autopilot expects to exist as real custom subagents:

- `autopilot-fast-helper.toml`
- `phase-executor.toml`
- `clarify-executor.toml`
- `checklist-executor.toml`
- `analyze-executor.toml`
- `implement-executor.toml`
- `codebase-analyst.toml`
- `spec-context-analyst.toml`
- `domain-researcher.toml`
- `uat-runbook-author.toml`

`autopilot-fast-helper.toml` is optional at runtime. The main
autopilot may use it for tiny advisory text-only prep work when
`gpt-5.3-codex-spark` is available, but autopilot must continue
without it if that model is unavailable in the current Codex
environment.

These files follow the official Codex subagent format: one standalone
TOML file per custom agent, with required `name`, `description`, and
`developer_instructions` fields plus Codex config such as `model`,
`model_reasoning_effort`, and `sandbox_mode`.

Operator note: on Codex, `sandbox_mode = "read-only"` does **not** sandbox
MCP server processes. The agent TOML cannot restrict tools, so to keep a
read-only agent provably unable to cause writes via MCP, the operator must
curate write-capable MCP servers OUT at the profile/config level (`enabled =
false`, or `enabled_tools`/`disabled_tools`).

The bundled model policy runs every execution and consensus agent on
`gpt-5.5`. Reasoning effort remains exactly as declared by each bundled TOML.
`autopilot-fast-helper` is the only model exception: it stays on
`gpt-5.3-codex-spark` for tiny advisory text-only prep, never for SDD reasoning.

If `gpt-5.5` is not available in the current Codex environment, set the
helper's `model` input to `gpt-5.4` (or set
`SPECKIT_CODEX_MODEL=gpt-5.4`); the installer rewrites only destination
copies.

## Plugin Upgrade and Agent Refresh Boundary

Codex plugin marketplace updates refresh the plugin cache but do **not** update
the separately registered files under `~/.codex/agents/`. Run this skill after
every SpecKit Pro upgrade, then restart Codex:

```
codex plugin marketplace upgrade racecraft-plugins-public
@SpecKit Pro -> install     (or `$install`)
# Restart Codex
```

The runner resolves `codex-agents/` from the currently executing installed
plugin. It does not mutate plugin caches or marketplace directories. Its
`dry_run` is content-aware: same-named destination files whose rendered content
differs are planned for refresh, while current files are reported as no-ops.

## Hard Constraints

- Never touch `.claude/agents/`, `.claude-plugin/`, `commands/`, or any
  Claude marketplace file.
- Never move or rename the bundled files in `codex-agents/`. They are the
  plugin's packaged templates and must stay on Codex-only paths.
- Copy only `*.toml` files from `codex-agents/`.
- Do not delete unrelated user subagents already present in the target
  directory.
- Overwrite only same-named SpecKit Pro agent files in the target directory.
- If the source bundle is missing or incomplete, STOP and report the exact
  missing files.
- After an applied change, always finish by telling the user to restart Codex.
  A no-op verification does not require another restart.

## Procedure

### 1. Resolve explicit Codex-only paths

Resolve all paths before mutating anything:

1. Determine the plugin root from the current skill location.
2. Resolve the source directory at `../../codex-agents/` relative to this
   skill.
3. Resolve the destination directory:
   - default: `~/.codex/agents/`
   - explicit project scope: `.codex/agents/` in the current project
4. Resolve the executor/consensus model:
   - default: `gpt-5.5`
   - fallback: `gpt-5.4` via the helper's `model` input or
     `SPECKIT_CODEX_MODEL=gpt-5.4`

Do not infer a Claude path from a vague request. If the user says only
"install the agents", use `~/.codex/agents/`.

### 2. Validate the bundled source set

Before copying:

1. Verify the source directory exists.
2. Verify all expected `*.toml` files are present.
3. Verify there are no legacy `.md` Codex agent files in the source bundle.

If any required file is missing, stop immediately. Do not partially install.

### 3. Run the bundled installer helper

Use the deterministic installed-runtime helper for `install-codex-agents`
with the selected destination. Run it first in `dry_run` mode, then in
`apply` mode after the plan matches the requested destination and model
override. Use `gpt-5.4` only when fallback mode was requested.

The structured request inputs are:

- `destination`: omit for `~/.codex/agents/`, or set to `.codex/agents/` for
  current-project scope
- `model`: `gpt-5.5` or `gpt-5.4`

The helper must be the only mechanism used for copying files. Do not
re-implement the copy loop inline unless the helper itself is broken and
you have already reported that failure.

When fallback mode is requested, verify every destination copy whose bundled
source model is `gpt-5.5` uses `model = "gpt-5.4"`. The Spark helper remains
unchanged, and all bundled source templates remain byte-identical.

### 4. Verify the installed destination

After the helper completes:

1. Verify the destination directory exists.
2. Verify every expected TOML file now exists in the destination.
3. Verify the copied files are the same filenames as the bundled source set.
4. For `gpt-5.5`, verify every destination file is byte-identical to its
   bundled source. For `gpt-5.4`, verify only the supported model assignment
   was rewritten in destination copies.
5. Preserve any unrelated user files in the destination.
6. Require the helper's verification status to be `verified` before reporting
   success.

If verification fails, report the mismatch clearly and stop.

### 5. Report restart requirement

When the helper applied changes, your closing output must explicitly tell the
user:

- where the files were installed
- which files were copied or refreshed
- the effective executor/consensus model
- that they must restart Codex now

When the helper reports `no_op`, report that verification succeeded and no
additional restart is required.

Do not continue into autopilot setup or workflow execution in the same skill.
Installation ends once the files are copied, verified, and the user has been
told to restart Codex.

## Output

Return a concise installation report like:

```text
## SpecKit Codex Subagents Installed

**Source:** /absolute/path/to/plugin/codex-agents
**Destination:** <HOME>/.codex/agents

**Installed files:**
- autopilot-fast-helper.toml
- phase-executor.toml
- clarify-executor.toml
- checklist-executor.toml
- analyze-executor.toml
- implement-executor.toml
- codebase-analyst.toml
- spec-context-analyst.toml
- domain-researcher.toml
- uat-runbook-author.toml

**Next step:** Restart Codex now so the custom subagents are loaded.
```

## Failure Handling

Stop instead of improvising when:

- the bundled `codex-agents/` directory is missing
- any required TOML file is missing
- the installer helper fails or rolls back
- the destination cannot be created
- post-copy verification does not match the bundled source set

If the install partially succeeded, report exactly what copied and what still
needs repair. Do not silently continue.
