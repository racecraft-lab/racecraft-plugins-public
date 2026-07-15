# Prerequisites Reference — Codex

The Codex autopilot's pre-flight sequence. Run these before Step 1 (Parse Workflow State) and before any phase work. If any check fails, STOP with the error message from the script's JSON output.

This is the Codex-specific mirror of `../../skills/speckit-autopilot/references/prerequisites.md`. Same checks, Codex-specific primitives (`update_plan`, `autopilot-state.json`, `spawn_agent`, `.codex/agents/`).

## Contents

- [Workflow Worktree Binding](#workflow-worktree-binding) — fail closed when the workflow belongs to a different checkout
- [Step -1: Archive Sweep Startup](#step--1-archive-sweep-startup) — archive previously merged specs before workflow execution
- [Step 0.0: Resolve Script Paths](#step-00-resolve-script-paths) — locate the plugin's `SKILL_SCRIPTS` directory
- [Step 0.1–0.7: Environment Checks](#step-01-07-environment-checks) — `check-prerequisites` JSON parsing, branch detection
- [Step 0.6: Load Settings](#step-06-load-settings) — project settings YAML frontmatter
- [Step 0.8: Capability Coverage & Plugin Limitation Check](#step-08-capability-coverage--plugin-limitation-check) — informational research/context advisory
- [Step 0.9: Constitution Validation](#step-09-constitution-validation) — principle checks against current codebase
- [Step 0.10: Codex Agent Availability Check](#step-010-codex-agent-availability-check) — verify installed custom agents without mutating them
- [Step 0.10b: Implementation Agent Detection](#step-010b-implementation-agent-detection) — discover `PROJECT_IMPLEMENTATION_AGENT`
- [Step 0.11: Project Command Discovery](#step-011-project-command-discovery) — `detect-commands` → `PROJECT_COMMANDS`
- [Step 0.12: Preset and Extension Detection](#step-012-preset-and-extension-detection) — `detect-presets` → `PRESET_CONVENTIONS`

## Workflow Worktree Binding

Run this read-only guard before Step -1, before reading workflow content, and
before any repository mutation:

1. Resolve the current checkout with `git rev-parse --show-toplevel`.
2. If the supplied workflow path exists inside that checkout, continue.
3. If a relative workflow path is missing, parse `git worktree list
   --porcelain` and test that same relative path under each registered
   worktree. Do not search commits, branches, or arbitrary filesystem roots.
4. If exactly one other worktree contains the workflow, STOP before Archive
   Sweep and report:

   ```text
   STOP: Workflow file is not in the current checkout. Start a new Codex task rooted at <worktree>, then run $speckit-autopilot <relative-workflow-path>.
   ```

5. If multiple worktrees contain it, STOP and list the candidate worktree
   roots. If none contains it, report the original missing path and STOP.
6. Treat an absolute workflow path outside the current checkout the same way:
   identify its registered worktree, then require a task rooted there.

Never copy, move, check out, rebase, or reconstruct the workflow to make the
current checkout pass. Never execute a workflow from one worktree while phase
commands, agents, gates, or commits target another.

## Step -1: Archive Sweep Startup

Before Step 0 and before any requested spec phase work, run Archive Sweep
to archive previously merged specs.

1. Determine the current target spec from the workflow file's `Spec Directory`
   field, the `--spec` override, or the active `specs/**` path in the workflow.
2. Detect archive extension state from `.specify/extensions.yml`,
   `.specify/extensions/.registry`, and `.specify/extensions/archive/extension.yml`.
3. When the archive extension is installed and enabled, use its project-local
   command contract as the Codex invocation path:

   - Read `provides.commands` in the extension manifest, resolve the
     `speckit.archive.run` file relative to the archive extension directory,
     and verify that file exists before treating the extension as executable.
   - Read and follow that command contract directly from this Codex skill. Do
     not require a generated `$speckit-archive-run` skill, a slash command, or
     any file under `.claude/`; project extension registration may belong to a
     different integration.
   - Treat integration-specific frontmatter entries and manifest requirements
     as renderer metadata for the project's installed integration. Do not
     resolve or execute those entries from the Codex plugin.
   - Use the already-validated worktree root and current target to derive
     absolute `REPO_ROOT`, `FEATURE_DIR`, `MEMORY_DIR`, and `TEMPLATES_DIR`.
     Step 0's runner checks own the Codex environment validation. Record
     `prerequisite_mode=codex_native_worktree_binding` and
     `prerequisite_available=true`.

   This direct contract adapter is the Codex execution path even when the
   extension registry lists only another integration under
   `registered_commands`.

4. If the manifest command file is missing or unreadable, the direct contract
   fails, or the Codex-native worktree binding cannot provide the required
   paths, treat the installed extension as broken. Record `status=blocked`,
   `invocation_available=false` or `prerequisite_available=false` as
   applicable, and `safeToApplyCleanup=false` under `archive_sweep`. Then STOP
   before Phase 0 with the exact failed path or operation. Do not substitute a
   manual `specs/` inventory, mark the Archive Sweep plan item completed, or
   advance Phase 0.

5. After the command and prerequisite pass, determine the sweep mode from the
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

6. Archive Sweep may archive/clean up only previously merged specs. It MUST
   exclude the current target spec until a later run sees that spec as merged.
   Before cleanup, apply the knowledge `archive` plan for each eligible
   canonical spec map. Cleanup may remove its other active artifacts but must
   retain, or immediately regenerate, the archived `SPEC-MOC.md` compatibility
   stub. Stub removal requires a separate reviewed deprecation.
7. Persist sweep output into `autopilot-state.json` under `archive_sweep`,
   including `status`, `execution_path=extension_contract`,
   `invocation_available`, `prerequisite_available`, `prerequisite_mode`,
   eligible previous specs, excluded current spec, archive extension installed
   state, cleanup mode, and `safeToApplyCleanup`.
8. When the executed sweep finds no prior candidates, record
   `status=no_candidates`, empty eligible previous specs, the excluded current
   spec, and `safeToApplyCleanup=false`. This is a successful no-op and may
   complete the Archive Sweep plan item. It is not a fallback for a broken or
   unexecuted command path.
9. Add/update the canonical `Archive Sweep: previously merged specs
   dry-run/apply eligibility` plan item before Phase 0 in both `update_plan`
   and `autopilot-state.json`. Complete it only after the direct contract run
   succeeds or the extension is confirmed absent.

If the archive extension is missing, record `archive_extension_installed=false`,
keep cleanup disabled, and continue only after warning that the project should
install or vendor `racecraft-lab/spec-kit-archive` for archive-aware cleanup.

## Step 0: Prerequisites

Run the prerequisite scripts to verify the environment. If any
check fails, STOP with the error message from the JSON output.

### 0.0 Resolve Script Paths

The autopilot's shell scripts ship with the **plugin**, not the
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
`.specify/scripts/<type>/` — that directory contains project-level
SpecKit scripts (create-new-feature, setup-plan, etc.), which are
different from the autopilot scripts.

### 0.1–0.7 Environment Checks

Run the prerequisites check script:

```text
'runner helper check-prerequisites' <workflow_file_path>
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
agent is current on the selected official Codex runtime path. Run the promoted
`install-codex-agents` runner helper in `dry_run` mode, using the same
destination and model that `$install` would use:

```text
'runner helper install-codex-agents' mode=dry_run inputs={destination?, model?}
```

The helper validates the bundled `codex-agents/*.toml` contract and compares
the rendered files with either selected runtime path:

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

Continue only when the helper returns `ok` with mutation status `no_op`. If it
reports planned files, fails validation, or cannot inspect the selected path,
STOP with its diagnostics. Tell the user to run `$install`, approve the expected
local write, restart Codex, and then retry autopilot. This pre-flight is
read-only: never apply or autoheal agent files from inside autopilot because the
current Codex process cannot load refreshed custom-agent definitions safely.

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

```text
'runner helper detect-commands'
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

```text
'runner helper detect-presets'
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
