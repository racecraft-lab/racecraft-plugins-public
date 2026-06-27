# Prerequisites Reference — Codex

The Codex autopilot's pre-flight sequence. Run these before Step 1 (Parse Workflow State) and before any phase work. If any check fails, STOP with the error message from the script's JSON output.

This is the Codex-specific mirror of `../../skills/speckit-autopilot/references/prerequisites.md`. Same checks, Codex-specific primitives (`update_plan`, `autopilot-state.json`, `spawn_agent`, `.codex/agents/`).

## Contents

- [Step -1: Archive Sweep Startup](#step--1-archive-sweep-startup) — archive previously merged specs before workflow execution
- [Step 0.0: Resolve Script Paths](#step-00-resolve-script-paths) — locate the plugin's `SKILL_SCRIPTS` directory
- [Step 0.1–0.7: Environment Checks](#step-01-07-environment-checks) — `check-prerequisites.sh` JSON parsing, branch detection
- [Step 0.6: Load Settings](#step-06-load-settings) — project settings YAML frontmatter
- [Step 0.8: Capability Coverage & Plugin Limitation Check](#step-08-capability-coverage--plugin-limitation-check) — informational research/context advisory
- [Step 0.9: Constitution Validation](#step-09-constitution-validation) — principle checks against current codebase
- [Step 0.10: Codex Agent Availability Check](#step-010-codex-agent-availability-check) — verify and autoheal installed custom agents under `.codex/agents/`
- [Step 0.10b: Implementation Agent Detection](#step-010b-implementation-agent-detection) — discover `PROJECT_IMPLEMENTATION_AGENT`
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
   archive command: --sweep --current-target <current-spec-dir>
   ```

   **`main`, a release branch, or any protected integration branch** (dry-run
   only — do not delete spec folders on the integration branch):
   ```text
   archive command: --sweep --current-target <current-spec-dir> --dry-run
   ```

4. Archive Sweep may archive/clean up only previously merged specs. It MUST
   exclude the current target spec until a later run sees that spec as merged.
5. Persist sweep output into `autopilot-state.json` under `archive_sweep`,
   including eligible previous specs, excluded current spec, archive extension
   installed state, cleanup mode, and `safeToApplyCleanup`.
6. Add/update an `Archive Sweep: previously merged specs archived` plan item
   before Phase 0 in both `update_plan` and `autopilot-state.json`.

If the archive extension is missing, record `archive_extension_installed=false`,
keep cleanup disabled, and continue only after warning that the project should
install or vendor `racecraft-lab/spec-kit-archive` for archive-aware cleanup.

## Step 0: Prerequisites

Run the prerequisite scripts to verify the environment. If any
check fails, STOP with the error message from the JSON output.

### 0.0 Resolve Script Paths

The autopilot's bash scripts ship with the **plugin**, not the
project. Before running any script, resolve the absolute path
to the scripts directory. The shared scripts live at:

```text
../../skills/speckit-autopilot/scripts/
```

Resolve this to an absolute path relative to the skill's location
and store it as `SKILL_SCRIPTS` for all subsequent commands.

Verify the directory exists by listing its contents. If it does
not exist, STOP: "Plugin scripts not found. Reinstall the
speckit-pro plugin."

**All script invocations below use the resolved `SKILL_SCRIPTS`
path as prefix.** Never run these scripts from
`.specify/scripts/bash/` — that directory contains project-level
SpecKit scripts (create-new-feature, setup-plan, etc.), which are
different from the autopilot scripts.

### 0.1–0.7 Environment Checks

Run the prerequisites check script:

```bash
bash '<SKILL_SCRIPTS>/check-prerequisites.sh' <workflow_file_path>
```

Parse the JSON result:
- `all_pass`: if `false`, report each failed check's `message` and STOP
- `branch`: current git branch name
- `on_feature_branch`: if `true`, Specify must skip branch creation
- `is_worktree`: if `true`, already in an isolated worktree

If `on_feature_branch` is `true`, verify the branch matches the
workflow file's `Branch` field. Warn if they don't match.

### 0.6 Load Settings

Read the project-level settings file if it exists (`.claude/speckit-pro.local.md` for Claude Code, or the equivalent Codex project config). Parse YAML
frontmatter for: `consensus-mode` (default: `moderate`),
`gate-failure` (default: `stop`), `auto-commit` (default:
`per-phase`), `security-keywords` (default: standard list).
If the file doesn't exist, use all defaults.

### 0.8 Capability Coverage & Plugin Limitation Check

The prerequisite script reports one `capability_coverage` advisory. This is
**informational, not blocking** — agents discover available capabilities at
runtime and use acceptable fallbacks when coverage is lighter. Parse the
`capability_coverage` check from the JSON output and report the setup-facing
categories: codebase context, library documentation, web/domain research, and
source extraction.

Missing optional research/context coverage can lower confidence or require
fallback evidence notes. It does not fail setup by itself. Escalate only when
no acceptable evidence path exists after fallback attempts or when a true
prerequisite/gate fails.

### 0.9 Constitution Validation

Read the workflow file's Prerequisites table. If already
`Verified`, skip (resuming a workflow). Otherwise:

1. Read constitution from `.specify/memory/constitution.md`
2. For each principle, run the appropriate PROJECT_COMMANDS
   check (typecheck, test suite, build, lint). For code review
   items (KISS, YAGNI, SOLID), mark `Verified` — these are
   validated during implementation.
3. Update the workflow file's table with results and baselines
4. If any check fails, STOP — do not proceed to Phase 1

### 0.10 Codex Agent Availability Check

Before phase execution, validate that every bundled SpecKit Pro Codex custom
agent is installed on official Codex runtime paths. Run the shared validator
with autoheal:

```bash
bash '<SKILL_SCRIPTS>/validate-agent-install.sh' --surface codex --autoheal
```

The validator checks the bundled `codex-agents/*.toml` contract and verifies
the installed runtime files on:

1. `.codex/agents/<agent>.toml`
2. `~/.codex/agents/<agent>.toml`

Bundled agents:

- `phase-executor`
- `clarify-executor`
- `checklist-executor`
- `analyze-executor`
- `implement-executor`
- `codebase-analyst`
- `spec-context-analyst`
- `domain-researcher`
- `autopilot-fast-helper`
- `uat-runbook-author`

If the validator succeeds after autoheal, continue and record that Codex
subagents were refreshed. If it still fails, STOP with its error message and
tell the user to run `$install`, approve the expected local write, then restart
Codex. A restart is required whenever autoheal copied or refreshed agent TOML
files.

### 0.10b Implementation Agent Detection

Detect whether the project has a specialized implementation
agent for the Implement phase:

```text
1. Search for all Codex custom-agent TOML files in the project's `.codex/agents/`
   directory and the user's `~/.codex/agents/` directory.
2. Read `name`, `description`, and any model fields from those TOML files.
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

Also check CLAUDE.md for references to a specific implementation
agent as advisory context only. Do not set PROJECT_IMPLEMENTATION_AGENT
from CLAUDE.md or `.claude/agents/` unless a same-named installed Codex
TOML agent exists in `.codex/agents/` or `~/.codex/agents/`. A Claude
Markdown/YAML agent is not spawnable by Codex.

### 0.11 Project Command Discovery

Run the command detection script:

```bash
bash '<SKILL_SCRIPTS>/detect-commands.sh'
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

### 0.12 Preset and Extension Detection

Run the preset detection script:

```bash
bash '<SKILL_SCRIPTS>/detect-presets.sh'
```

Parse the JSON result for: `has_presets`, `presets` (names +
templates they override), `extensions`, `hooks`, and `templates`
(resolved paths for tasks/spec/plan templates).

If `has_presets` is `true`:
1. Read each preset's overridden templates to understand the
   conventions it enforces (TDD, architecture, etc.)
2. Record as PRESET_CONVENTIONS for subagent prompts
3. Include PRESET_CONVENTIONS in ALL subagent prompts —
   presets affect every phase, not just implement

If no presets AND no extensions, skip this step.
