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

This skill installs the bundled TOML subagent templates that the
Codex autopilot expects to exist as real custom subagents:

- `analyze-executor.toml`
- `artifact-author.toml`
- `autopilot-fast-helper.toml`
- `checklist-executor.toml`
- `clarify-executor.toml`
- `codebase-analyst.toml`
- `domain-researcher.toml`
- `implement-executor.toml`
- `phase-executor.toml`
- `spec-context-analyst.toml`
- `sweep-analyst.toml`
- `sweep-classifier.toml`
- `uat-runbook-author.toml`

The bundled source inventory is strict: all 13 TOML files must be present
before the installer plans either static or route-aware destination changes.
In route-aware planning, 12 files are required destination agents and
`autopilot-fast-helper.toml` is the only optional helper. The main autopilot
may use that helper for tiny advisory text-only prep work when
`gpt-5.3-codex-spark` is available, but autopilot must continue without it if
the helper is unavailable and no-helper continuation validates.

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

## Static and Route-aware Modes

The default install path is static compatibility mode. If the request does not
include `route_policy_manifest`, the helper preserves the existing 13-file
route-agnostic copy/verify behavior:

- `data.routing` is absent.
- No capability discovery, bounded probe, route-policy evaluation, optional
  helper omission/removal/preservation, or strict override validation runs.
- Existing mechanical response fields remain authoritative for the copy:
  `agent_files`, `model`, `source`, `destination`, `mutation`,
  `verification`, `writes_state`, and `restart_required`.

Route-aware mode activates only when the request supplies an explicit
`route_policy_manifest` path. Inline policy objects, inferred bundled defaults,
or a vague "use routing" request must not activate route-aware mode. The
manifest must be a supported, closed, repository-local document that binds the
current 13-TOML source roster, declares exactly 12 required policies, declares
the `autopilot-fast-helper` policy/no-helper state, and admits every route
candidate and bounded probe used by the run. Every required policy's declared
non-route contract digest must exactly match canonical materialization of its
trusted current source TOML. Required-policy objects are closed-schema records,
and `required_capabilities` must be a duplicate-free list of non-empty strings.
The optional helper's `no_helper` record is also closed: `allowed` is strictly
boolean and `reason` is a non-empty string. String truthiness never authorizes
helper omission.

Route-aware mode returns `data.routing` with:

- one runtime capability snapshot for the whole invocation, with child probe
  evidence when native discovery is unavailable
- required-agent resolution records in canonical 12-agent order
- optional-helper decision evidence
- strict-override evidence when requested
- recovery-or-mutation evidence for planned/applied writes, removals, rollback,
  restart requirement, and manual remediation

G56R-006 route-aware evidence is deterministic framework evidence only. It uses
injected discovery/probe fixtures and fake-home or temporary project
destinations for acceptance. Do not use route-aware G56R-006 acceptance to write
the operator's real `~/.codex/agents/`, and do not describe the result as live
UAT or production route qualification. Production route qualification is owned
by later G56R work.

### Strict override behavior

If `strict_model_override` is supplied in route-aware mode, required agents
evaluate exactly one override-derived tuple per required agent. The run does not
walk preferred or fallback routes after an override miss. Required-agent
incompatibility fails before mutation after all 12 required diagnostics are
complete.

The optional helper follows the override only when a compatible helper tuple
exists. If the helper tuple is incompatible and no-helper continuation
validates, the helper is omitted or the existing same-named helper is handled by
the ownership rules below. If no-helper continuation does not validate, the
route-aware batch fails before mutation.

### Optional helper outcomes

Route-aware optional-helper outcomes are:

- `installed`: a manifest-admitted helper route resolves and materializes
- `omitted`: no helper route is available, no existing helper file is present,
  and no-helper continuation validates
- `removed`: an existing helper is removed only when its bytes exactly match a
  known rendered helper derived from the trusted current source and manifest
- `preserved`: an existing same-named helper lacks managed ownership proof and
  is left in place with bounded manual-remediation evidence
- `unresolved`: neither a compatible helper nor validated no-helper
  continuation is available, so the batch fails before mutation

Filename, location, syntactic TOML validity, parsed equivalence, and normalized
content do not prove helper ownership.
Caller-supplied provenance is not an ownership authority and cannot authorize
helper removal.

### Recovery evidence

Route-aware apply plans all required writes and managed-helper removals as one
rollback-backed batch. Before mutation, it captures prior bytes and file modes
for each planned destination action. It rechecks bytes, mode, and file identity
immediately before each mutation and before rollback, preserving concurrent
external edits and reporting uncertain state instead of overwriting them. On
failure:

- recovery distinguishes staged actions from actions actually applied and
  rolled back, reports the exact failed write or removal, and records real
  destination-directory cleanup outcomes
- successful rollback reports `rollback_outcome=restored`,
  `writes_state=false`, `restart_required=false`, and no verification success
- failed or uncertain rollback reports every unrestored action and error,
  `writes_state=true` or uncertain state, `restart_required=true`, bounded
  manual remediation, and no verification success
- required-route pre-mutation failures report zero planned/applied writes and
  removals, `writes_state=false`, and `restart_required=false`

Bounded probe declarations use the closed manifest schema `probe_id`,
`candidate_route_id`, `purpose`, `bounds`, and `expected_result_shape`. Each
declaration must be keyed by its exact probe ID and bind to an admitted route
that declares the same probe; aliases and partial records are rejected before
capability discovery.

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
- Do not use the operator's real home directory for G56R-006 route-aware
  acceptance evidence. Use a fake HOME/USERPROFILE or a temporary project
  `.codex/agents/` destination.
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

For static compatibility mode, omit `route_policy_manifest`. The structured
request inputs are:

- `destination`: omit for `~/.codex/agents/`, or set to `.codex/agents/` for
  current-project scope
- `model`: `gpt-5.5` or `gpt-5.4`

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
- analyze-executor.toml
- artifact-author.toml
- autopilot-fast-helper.toml
- checklist-executor.toml
- clarify-executor.toml
- codebase-analyst.toml
- domain-researcher.toml
- implement-executor.toml
- phase-executor.toml
- spec-context-analyst.toml
- sweep-analyst.toml
- sweep-classifier.toml
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

If the install partially succeeded or rollback is uncertain, report the
structured recovery evidence: staged actions, applied actions, rolled-back
actions, cleanup actions/errors, failed actions, unrestored actions, restart
requirement, and bounded manual-remediation guidance. Do not silently continue
or claim verification success.
