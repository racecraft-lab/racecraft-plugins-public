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

If the user explicitly asks for project scope, use `.codex/agents/` in the
current project. Arbitrary destinations are rejected. Otherwise install to the
default user-scope path above.

## What This Skill Installs

The runner-owned catalog determines which bundled agents are required or
optional. The response field `data.agent_files` supplies the concrete
filenames for the invocation. The installer fails before planning when required
source templates are missing, and route-aware mode may omit the optional helper
only when no-helper continuation validates.

These files follow the official Codex subagent format: one standalone
TOML file per custom agent, with required `name`, `description`, and
`developer_instructions` fields plus Codex config such as `sandbox_mode`.

Operator note: on Codex, `sandbox_mode = "read-only"` does **not** sandbox
MCP server processes. The agent TOML cannot restrict tools, so to keep a
read-only agent provably unable to cause writes via MCP, the operator must
curate write-capable MCP servers OUT at the profile/config level (`enabled =
false`, or `enabled_tools`/`disabled_tools`).

The runner-owned policy defines each bundled agent's model and reasoning effort.
An explicit route manifest materializes its selected model-and-effort tuple. The optional
`autopilot-fast-helper` remains pinned to `gpt-5.6-luna` at low effort for tiny
advisory text-only prep, never for SDD reasoning.

If `gpt-5.6-sol` is not available in the current Codex environment, set the
installer's `model` input to `gpt-5.5` or `gpt-5.4` (or set
`SPECKIT_CODEX_MODEL` to the selected fallback); the installer rewrites only
destination copies.

## Plugin Refresh and Route-aware Modes

After the plugin is upgraded through its maintained plugin path, run `$install`;
restart Codex only if the helper applied changes. The helper resolves the
installed plugin's `codex-agents/` source and does not mutate plugin caches.

Static mode omits `route_policy_manifest` and uses the helper's normal
copy/verify result. Route-aware mode activates only for an explicit trusted
repository-local `route_policy_manifest`; inline policy, inferred defaults, or
a vague routing request do not activate it. A strict override does not fall
through after a required route misses. Helper omission is allowed only when the
helper returns its validated no-helper result. Any unresolved required route or
uncertain rollback stops and reports the helper response, including mutation,
verification, recovery, `writes_state`, and `restart_required`.

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
- Route-aware fixture evidence is not live UAT. Use a fake HOME/USERPROFILE or
  a temporary project `.codex/agents/` destination, never the operator's real
  home directory.
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
4. Resolve the request-level fallback model for pinned bundled agents:
   - default: `gpt-5.6-sol`
   - fallback: `gpt-5.5` or `gpt-5.4` via the installer `model` input or
     `SPECKIT_CODEX_MODEL`

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
override. Use `gpt-5.5` or `gpt-5.4` only when fallback mode was requested.

For static compatibility mode, omit `route_policy_manifest`. The structured
request inputs are:

- `destination`: omit for `~/.codex/agents/`, or set to `.codex/agents/` for
  current-project scope
- `model`: `gpt-5.6-sol`, `gpt-5.5`, or `gpt-5.4`

For route-aware mode, use only an explicit trusted manifest path:

- `destination`: omit for `~/.codex/agents/`, or set to `.codex/agents/` for
  current-project scope
- `route_policy_manifest`: repository-local manifest path
- `strict_model_override`: optional model string for strict route validation

Do not mix static `model` fallback semantics with route-aware manifest
activation. Route-aware destination bytes come from the selected manifest
routes and materialization proof.

The helper must be the only mechanism used for copying files. Do not
re-implement the copy loop inline unless the helper itself is broken and
you have already reported that failure.

When fallback mode is requested, verify every destination copy whose bundled
source model is `gpt-5.6-sol` uses the requested legacy model. The Luna helper
remains unchanged, and all bundled source templates remain byte-identical.

### 4. Verify the installed destination

After the helper completes:

1. Verify the destination directory exists.
2. Verify every expected TOML file now exists in the destination.
3. Verify the copied files are the same filenames as the bundled source set.
4. For `gpt-5.6-sol`, verify every destination file is byte-identical to its
   bundled source. For `gpt-5.5` or `gpt-5.4`, verify only bundled
   `gpt-5.6-sol` assignments were rewritten.
5. Preserve any unrelated user files in the destination.
6. Require the helper's verification status to be `verified` before reporting
   success.

If verification fails, report the mismatch clearly and stop.

### 5. Report restart requirement

When the helper applied changes, your closing output must explicitly tell the
user:

- where the files were installed
- which files were copied or refreshed
- the request-level fallback model
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

**Installed files:** <render `data.agent_files`>

**Next step:** Restart Codex now so the custom subagents are loaded.
```

## Failure Handling

Stop instead of improvising when:

- the bundled `codex-agents/` directory is missing
- any required TOML file is missing
- the installer helper fails or rolls back
- the destination cannot be created
- post-copy verification does not match the bundled source set

Feedback-sweep classifier and analyst prompts are trusted launcher resources,
not installable Codex agents. Never recreate them under `.codex/agents/`; the
autopilot runs them only through the isolated `codex exec` launcher.

If the install partially succeeded or rollback is uncertain, report the
structured recovery evidence: staged actions, applied actions, rolled-back
actions, cleanup actions/errors, failed actions, unrestored actions, restart
requirement, and bounded manual-remediation guidance. Do not silently continue
or claim verification success.
