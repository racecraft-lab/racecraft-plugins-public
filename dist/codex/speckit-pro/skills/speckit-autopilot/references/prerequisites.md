# Prerequisites Reference

The autopilot's pre-flight sequence. Run these before Step 1 (Parse Workflow State) and before any phase work. If any check fails, STOP with the error message from the script's JSON output.

## Contents

- [Workflow Worktree Binding](#workflow-worktree-binding) — verify Claude's live checkout after `/cd`
- [Step -1: Archive Sweep Startup](#step--1-archive-sweep-startup) — archive previously merged specs before workflow execution
- [Step 0.0: Resolve Script Paths](#step-00-resolve-script-paths) — extract `SKILL_SCRIPTS` from the skill header (plugin path)
- [Step 0.0b: Claude Agent Package Completeness](#step-00b-claude-agent-package-completeness) — verify bundled plugin agents are present
- [Step 0.1–0.7: Environment Checks](#step-01-07-environment-checks) — `check-prerequisites` JSON parsing, branch detection
- [Step 0.6: Load Settings and Resolve Claude Runtime](#step-06-load-settings--resolve-claude-runtime) — local settings plus one versioned subagent-runtime record
- [Step 0.8: Capability Coverage & Plugin Limitation Check](#step-08-capability-coverage--plugin-limitation-check) — informational research/context advisory + plugin-agent caveats
- [Step 0.9: Constitution Validation](#step-09-constitution-validation) — principle checks against current codebase
- [Step 0.10: Implementation Agent Detection](#step-010-implementation-agent-detection) — discover `PROJECT_IMPLEMENTATION_AGENT`
- [Step 0.11: Project Command Discovery](#step-011-project-command-discovery) — `detect-commands` → `PROJECT_COMMANDS`
- [Step 0.12: Preset and Extension Detection](#step-012-preset-and-extension-detection) — `detect-presets` → `PRESET_CONVENTIONS`

## Workflow Worktree Binding

Run this read-only guard before Step -1, before reading workflow content, and
before any repository mutation:

1. Invoke the runner helper `resolve-workflow-binding` with the supplied path as
   `inputs.workflow_file`. Require `binding_status=resolved` and
   `relation=same`, then bind its canonical `task_root`, `workflow_root`, and
   `workflow_file` as `TASK_ROOT`, `WORKFLOW_ROOT`, and `WORKFLOW_FILE`.
2. On `missing`, `ambiguous`, or `invalid`, report the helper's `candidates` and
   `problems` and STOP. Do not search other revisions or arbitrary filesystem
   roots.
3. If the helper resolves `descendant` or `external`, the current Claude Code
   checkout is still the parent or another worktree. STOP before Archive Sweep
   and print this retry, using the helper's canonical paths:

   ```text
   /cd <WORKFLOW_ROOT>
   /speckit-pro:speckit-autopilot <canonical absolute WORKFLOW_FILE> --stage <requested-stage>
   ```

   The operator sends the autopilot command only after `/cd` succeeds. Claude
   Code documents that `/cd` changes the live session's primary directory and
   reloads directory instructions:
   <https://code.claude.com/docs/en/commands>.
4. From the resolved `WORKFLOW_ROOT`, verify the live branch before Archive
   Sweep. STOP on `main`, a detached HEAD, or any protected integration/release
   branch. Never mutate the parent checkout as a fallback.
5. Re-run this guard on resume. Every shell call, helper, filesystem operation,
   state update, Git action, phase prompt, consensus prompt, and write-capable
   agent must target `WORKFLOW_ROOT`; validate returned paths before applying
   edits or committing.

This guard is why the scaffold hand-off is two explicit same-session commands.
Scaffold never invokes `/cd` or autopilot itself.

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

The autopilot's shell scripts ship with the **plugin**, not the
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
Command("ls '<SKILL_SCRIPTS>/'")
```

If it doesn't exist, STOP: "Plugin scripts not found. Reinstall
the speckit-pro plugin."

**All script invocations below use the resolved `SKILL_SCRIPTS`
path as prefix.** Never run these scripts from
`.specify/scripts/<type>/` — that directory contains project-level
SpecKit scripts (create-new-feature, setup-plan, etc.), which are
different from the autopilot scripts.

**WARNING:** `CLAUDE_PLUGIN_ROOT` is NOT available in command tool tool
invocations — it only exists inside agent subprocesses. Always use
the literal path extracted from the skill header.

## Step 0.0b: Claude Agent Package Completeness

Before any phase work, verify the installed Claude Code plugin package includes
every bundled SpecKit Pro agent:

```text
Command("'runner helper validate-agent-install' --surface claude --plugin-root '<plugin-root>'")
```

Use the plugin root that owns `skills/speckit-autopilot/`; this is the directory
above `skills/`, not the host repository root. The validator checks all bundled
`agents/*.md` files, including `uat-runbook-author.md`.

If the check fails, STOP. Claude Code loads plugin agents directly from the
plugin cache, so autopilot cannot safely self-heal a missing Claude agent file.
Tell the user to update/reinstall `speckit-pro`, run `/reload-plugins`, and
retry.

## Step 0.1–0.7: Environment Checks

```text
Command("'runner helper check-prerequisites' <workflow_file_path>")
```

Parse the JSON result:
- `all_pass`: if `false`, report each failed check's `message` and STOP
- `branch`: current git branch name
- `on_feature_branch`: if `true`, Specify must skip branch creation
- `is_worktree`: if `true`, already in an isolated worktree

If `on_feature_branch` is `true`, verify the branch matches the
workflow file's `Branch` field. Warn if they don't match.

**Important:** Environment variables set in command tool do NOT persist to
Skill tool invocations. The autopilot handles branch context by
adjusting how it invokes each phase (see Phase Dispatch).

## Step 0.6: Load Settings + Resolve Claude Runtime

### Settings file

Read `.claude/speckit-pro.local.md` if it exists. Parse YAML
frontmatter for: `consensus-mode` (default: `moderate`),
`gate-failure` (default: `stop`), `auto-commit` (default:
`per-phase`), `security-keywords` (default: the list in the
Security Keywords section of `consensus-protocol.md`).
If the file doesn't exist, use all defaults.

### Versioned subagent-runtime record

Observe only the inputs needed by the registered read-only helper:

```text
client_version: output of `claude --version`
execution_mode: interactive | headless
max_concurrent_subagents: bounded value of CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS, if set
max_subagent_spawn_depth: bounded value of CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH, if set
agent_teams_env_enabled: whether CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
team_contract_verified: whether this client/version passed the maintained live team UAT
auto_memory_enabled: resolved Claude auto-memory setting
```

Pass those fields to runner helper `resolve-claude-subagent-runtime`. Persist
the complete stdout JSON as `claude_subagent_runtime` in
`autopilot-state.json` and in the workflow file's Notes. The workflow file is
the durable record. Set these dispatch values from the result:

```text
AGENT_TEAMS_AVAILABLE = agent_teams.available
SUBAGENT_WAVE_SIZE = concurrency.wave_size
SUBAGENT_RESUME_STRATEGY = partial_resume.strategy
```

The helper applies the current compatibility policy:

- Claude Code 2.1.217+ defaults to 20 concurrent subagents; older supported
  clients use a compatibility default of 5. One slot is reserved for recovery,
  so each deterministic wave uses `max(1, limit - 1)`.
- Invalid concurrency or nesting overrides fail safe to one-at-a-time/depth-one
  operation with a warning.
- Claude Code 2.1.219+ uses the documented default nesting depth of 3. Workflow
  phase dispatch remains flat by design even when the runtime supports nesting.
- Claude Code 2.1.246+ may resume one partial subagent by agent ID; older clients
  get one fresh retry. A second partial result stops the run.
- Claude Code 2.1.247+ native model fallback is recorded as an operator control,
  never silently configured or claimed by this plugin.
- Claude Code 2.1.248+ client cache TTL support is recorded but not adopted for
  plugin agents because the plugin-agent surface does not document that field.

Agent Teams is available only when the environment flag is enabled, the client
is at least 2.1.178, execution is positively interactive, and the live team
contract is verified. `claude -p` always uses ordinary subagents. When any
condition fails, use batched ordinary subagents and log the resolver's reason.
Do not stop: teams are an optional coordination enhancement.

Dispatch details for both code paths live in
[`post-implementation.md`](./post-implementation.md) §Post-Implementation Parallel Group.
The full **use-site map** (post-impl, consensus, Phase 7 `[P]` tasks,
parallel checklist/analyze) and lifecycle policy live in
[`agent-teams-integration.md`](./agent-teams-integration.md).

## Step 0.8: Capability Coverage & Plugin Limitation Check

The prerequisite script reports one `capability_coverage` advisory.
This is **informational, not blocking** — agents discover available
capabilities at runtime and use acceptable fallbacks when coverage is
lighter. Parse the `capability_coverage` check from the JSON output and
report the setup-facing categories: codebase context, library
documentation, web/domain research, and source extraction.

Missing optional research/context coverage can lower confidence or require
fallback evidence notes. It does not fail setup by itself. Escalate only
when no acceptable evidence path exists after fallback attempts or when a
true prerequisite/gate fails.

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
3. Run every populated quality-gate slot from Step 0.11 with an
   empty `{paths}` (only `DEPENDENCY_RULES` does real work here)
   and record the baseline in the Quality Gates table
4. Update the workflow file's table with results and baselines
5. If any check or populated gate fails, STOP — do not proceed
   to Phase 1

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
   specific description
6. If no matches → set PROJECT_IMPLEMENTATION_AGENT to
   "phase-executor" (fallback)
```

Also check CLAUDE.md for references to a specific
implementation agent (e.g., "my-project-developer" or
"use the X agent for implementation").

**Record the result** for use in Step 2's Implement phase.

## Step 0.11: Project Command Discovery

```text
Command("'runner helper detect-commands'")
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

### Quality-gate slots

The same result carries three more slots, `COMPLEXITY`,
`MUTATION`, and `DEPENDENCY_RULES`, plus a `gates` object that
describes each one. The runner fills them from the shipped
discovery table (`speckit_pro_runner/gate_discovery_table.json`),
consulting `.specify/gate-discovery.json` first when that
override validates. A slot is `populated` when one of its signal
files exists in the repository, otherwise `unconfigured` and
`"N/A"`; a slot named in the file's `skips` is `skipped` and
`"N/A"` without a question.

**`.specify/quality-gates.json` is the threshold authority.** The
result's `quality_gates.status` is `present`, `missing`, or
`invalid` (with `problems`). Anything but `present` fails G0
with this message, verbatim, and STOP:

```text
G0 blocked: .specify/quality-gates.json is <missing|invalid: first problem>.
Run `/speckit-pro:speckit-coach quality gates` to create it. Agents never edit this file.
```

With the file missing, the slot commands still show the shipped
defaults (complexity 8, CRAP 30, mutation-score floor 60) so the
operator can see what would run; they are not authoritative and
do not unblock G0.

Two placeholders stay literal in the recorded command and are
filled at every run:

- `{plugin_root}`: `${CLAUDE_PLUGIN_ROOT}`. Never record the
  expanded path in the workflow file.
- `{paths}`: the changed source files of the detected language,
  tests excluded, from `git diff --name-only --diff-filter=AM
  <base>...HEAD`. An empty list checks nothing and passes. At G0
  there is no diff, so `COMPLEXITY` and `MUTATION` pass vacuously
  and only `DEPENDENCY_RULES` runs, against the whole graph.

**A populated slot that fails blocks**, at G0, at every
phase-group verification, and at final verification. It is a
red gate, not a warning to note and move past.

**Missing tool, one question per tool per repository.** For each
populated slot with `tool_present: false`, look for a recorded
answer for that tool: first `skips` in `.specify/quality-gates.json`,
then the workflow file's Quality Gates table, then (only while no
`quality-gates.json` exists yet) a `skip (repo)` row for the same
tool in any other `docs/ai/specs/.process/*-workflow.md`. If none
exists, ask once
with `AskUserQuestion`:

```text
<tool> is not installed, but this repository configures the
<slot> gate (signal: <signal>). Install it, skip it for this
spec, or skip it for this repository?
  1. Install (<install>)   2. Skip this spec   3. Skip this repo
```

Record the answer in the Quality Gates table before continuing:

- `install`: run the install command, re-run `detect-commands`,
  and require `tool_present: true`. If it is still false, STOP.
- `skip (spec)`: the slot is `"N/A"` for this workflow only.
- `skip (repo)`: the durable record is a `skips` entry in
  `.specify/quality-gates.json`, written by the operator through
  the coach flow, never by an agent. Record `skip (repo)` in the
  table, point the operator at the coach flow, and continue with
  the slot as `"N/A"`.

When no interactive runtime is available, record `unanswered`
for the tool, then STOP naming the tool and the three options;
a resume after the operator edits the table proceeds from the
recorded answer.

## Step 0.12: Preset and Extension Detection

```text
Command("'runner helper detect-presets'")
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
