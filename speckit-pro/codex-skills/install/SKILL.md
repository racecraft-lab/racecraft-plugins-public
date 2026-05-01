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

The bundled source of truth lives in the plugin at:

- `codex-agents/*.toml`

The default user-scope Codex destination is:

- `~/.codex/agents/`

If the user explicitly asks for a different Codex-compatible agent
directory, honor that override. Otherwise install to the default
user-scope path above.

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

`autopilot-fast-helper.toml` is optional at runtime. The main
autopilot may use it for tiny advisory text-only prep work when
`gpt-5.3-codex-spark` is available, but autopilot must continue
without it if that model is unavailable in the current Codex
environment.

These files follow the official Codex subagent format: one standalone
TOML file per custom agent, with required `name`, `description`, and
`developer_instructions` fields plus Codex config such as `model`,
`model_reasoning_effort`, and `sandbox_mode`.

The bundled model policy: every execution and consensus agent runs
on `gpt-5.5`. Reasoning effort is tuned per role — `high` for the
phases the official GitHub SpecKit docs flag as heavy (Specify, Plan,
Clarify, Checklist remediation, Analyze, Implement) and `medium` for
the read-heavy consensus analysts. `phase-executor` runs at `high`
effort because it owns Specify and Plan, which the SpecKit docs
describe as heavy architectural reasoning. `autopilot-fast-helper`
is the only exception: it stays on `gpt-5.3-codex-spark` at `low`
effort for tiny advisory text-only prep, never for SDD reasoning.

If `gpt-5.5` is not available in the current Codex environment,
install with `--model gpt-5.4` or set `SPECKIT_CODEX_MODEL=gpt-5.4`;
the installer rewrites only the executor and consensus agent copies
in the destination directory.

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
- Always finish by telling the user to restart Codex. A restart is required
  for newly installed custom subagents to be picked up reliably.

## Procedure

### 1. Resolve explicit Codex-only paths

Resolve all paths before mutating anything:

1. Determine the plugin root from the current skill location.
2. Resolve the source directory at `../../codex-agents/` relative to this
   skill.
3. Resolve the destination directory:
   - default: `~/.codex/agents/`
   - override: a user-provided Codex agent directory path
4. Resolve the executor/consensus model:
   - default: `gpt-5.5`
   - fallback: `gpt-5.4` via `--model gpt-5.4` or
     `SPECKIT_CODEX_MODEL=gpt-5.4`

Do not infer a Claude path from a vague request. If the user says only
"install the agents", use `~/.codex/agents/`.

### 2. Validate the bundled source set

Before copying:

1. Verify the source directory exists.
2. Verify all expected `*.toml` files are present.
3. Verify there are no legacy `.md` Codex agent files in the source bundle.

If any required file is missing, stop immediately. Do not partially install.

### 3. Run the bundled installer script

Use the deterministic installer script that ships with this skill:

```bash
bash "<skill-dir>/scripts/install-codex-agents.sh" "<destination>"
bash "<skill-dir>/scripts/install-codex-agents.sh" "<destination>" --model gpt-5.4
```

The script must be the only mechanism used for copying files. Do not
re-implement the copy loop inline unless the script itself is broken and
you have already reported that failure.

When fallback mode is requested, verify the destination copies of
`clarify-executor`, `checklist-executor`, `analyze-executor`,
`implement-executor`, and the three consensus analysts use
`model = "gpt-5.4"`. The bundled source templates stay on `gpt-5.5`.

### 4. Verify the installed destination

After the script completes:

1. Verify the destination directory exists.
2. Verify every expected TOML file now exists in the destination.
3. Verify the copied files are the same filenames as the bundled source set.
4. Preserve any unrelated user files in the destination.

If verification fails, report the mismatch clearly and stop.

### 5. Report restart requirement

Your closing output must explicitly tell the user:

- where the files were installed
- which files were copied or refreshed
- the effective executor/consensus model
- that they must restart Codex now

Do not continue into autopilot setup or workflow execution in the same skill.
Installation ends once the files are copied, verified, and the user has been
told to restart Codex.

## Output

Return a concise installation report like:

```text
## SpecKit Codex Subagents Installed

**Source:** /absolute/path/to/plugin/codex-agents
**Destination:** /Users/<user>/.codex/agents

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

**Next step:** Restart Codex now so the custom subagents are loaded.
```

## Failure Handling

Stop instead of improvising when:

- the bundled `codex-agents/` directory is missing
- any required TOML file is missing
- the installer script fails
- the destination cannot be created
- post-copy verification does not match the bundled source set

If the install partially succeeded, report exactly what copied and what still
needs repair. Do not silently continue.
