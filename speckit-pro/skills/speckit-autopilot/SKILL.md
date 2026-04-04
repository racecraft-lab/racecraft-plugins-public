---
name: speckit-autopilot
description: >
  Autonomous SpecKit workflow executor. Reads a populated workflow file
  and executes all 7 SDD phases (specify → clarify → plan → checklist →
  tasks → analyze → implement) with programmatic gate validation,
  multi-agent consensus resolution, and auto-commits. Use when the user
  says "run autopilot", "execute workflow", "autonomous speckit",
  or has a workflow file ready for execution.
user-invokable: false
license: MIT
---

# SpecKit Autopilot — Autonomous Execution Engine

## Scope

This skill handles autonomous workflow EXECUTION. For methodology
questions, SDD philosophy, or learning how SpecKit works, redirect
the user to `/speckit-pro:coach` — the coaching skill is the right
resource for methodology guidance.

Your context window will be automatically compacted as it
approaches its limit, allowing you to continue working
indefinitely. Do not stop tasks early. Always be as persistent
and autonomous as possible and complete all 7 phases fully.

You are an **orchestrator** for SpecKit workflows. You read
prompts from the workflow file and delegate each phase to a
**subagent** that runs the `/speckit.*` command. You never run
the commands yourself — you spawn, collect results, validate
gates, and advance.

## Critical: Execution Rules

These rules are non-negotiable. Follow them exactly.

### 1. Subagent per phase

For each phase, spawn a **foreground subagent** via the Agent
tool. The subagent runs the `/speckit.*` command and returns a
summary. You (the parent) receive the result as a tool call
response, which keeps your agent loop alive.

**Why:** Claude Code's agent loop terminates when a response
has no tool calls. If you run a Skill directly, the loaded
command's "report completion" instruction causes you to output
plain text, killing the loop. With subagents, the command runs
in an isolated context and its completion behavior is harmless
— the result returns to you as a tool response, and your loop
continues.

**What this looks like:**

```text
CORRECT:
  1. Read workflow file's "### Specify Prompt" section
  2. Agent(prompt: "Run /speckit.specify with: <prompt>")
  3. Subagent runs command, returns summary   ← TOOL RESULT
  4. TaskUpdate: Specify → completed          ← TOOL CALL
  5. Grep for [NEEDS CLARIFICATION] markers   ← TOOL CALL
  6. Agent(prompt: "Run /speckit.clarify...") ← TOOL CALL
  ...every step is a tool call — loop never dies...

WRONG:
  1. Skill("speckit.specify", args: "<prompt>")
  2. Command loads into YOUR context
  3. You output: "The spec is ready for /speckit.plan"
     ↑ plain text, no tool call → loop terminates
```

### 2. Use phase-specific executor agents

Each phase type has its own specialized executor agent:

| Phase | Agent | Why specialized |
| ----- | ----- | --------------- |
| Specify, Plan, Tasks | `phase-executor` | Simple: run command, return summary |
| Clarify | `clarify-executor` | Interactive: must research and answer questions |
| Checklist | `checklist-executor` | Must run checklist AND remediate gaps with research |
| Analyze | `analyze-executor` | Must run analysis AND remediate ALL findings with research |
| Implement | per-task routing | Task-level dispatch: routes each task to best-fit agent with TDD protocol |

```text
Agent(
  subagent_type: "<agent for this phase>",
  description: "SPEC-XXX <phase>",
  prompt: """
    <phase-specific prefix if needed>

    Workflow prompt:
    ---
    <paste the prompt from the workflow file>
    ---
  """
)
```

Each agent loads the Skill in its own context, runs the
command (and any post-execution work like gap remediation),
and returns a structured summary. All noise stays in the
subagent's context.

### 3. Task list first

Before executing any phase, create a granular task list using
TaskCreate. The task list drives the loop — after each subagent
returns, check it to know what's next. See Step 1.1 for the
full naming pattern and rules.

### 4. Multi-prompt phases

Clarify and Checklist have multiple prompts in the workflow
file. Spawn a **separate subagent for each prompt**.

**What this looks like:**

```text
CORRECT (Clarify with 2 sessions):
  1. TaskUpdate: "Clarify - Session 1" → in_progress
  2. Agent(subagent_type: "clarify-executor",
          prompt: "<session 1 prompt>")
     The clarify-executor researches and answers all questions
  3. Grep spec.md for [NEEDS CLARIFICATION] markers
  4. If markers remain → use context_builder to resolve
  5. TaskUpdate: "Clarify - Session 1" → completed
  6. TaskUpdate: "Clarify - Session 2" → in_progress
  7. Agent(subagent_type: "clarify-executor",
          prompt: "<session 2 prompt>")
  8. Grep spec.md for [NEEDS CLARIFICATION] markers
  9. If markers remain → use context_builder to resolve
  10. TaskUpdate: "Clarify - Session 2" → completed
  11. Validate G2 gate (0 markers remaining)
  12. Advance to Plan

WRONG:
  1. Run all sessions, then check for markers at the end
  2. Or skip sessions and do your own analysis
```

### 5. Clarify — executor answers autonomously

The `clarify-executor` invokes `/speckit.clarify` and answers
all questions itself using research tools (web search, library docs,
codebase exploration — uses Tavily, Context7, RepoPrompt when
available, falls back to built-in WebSearch, WebFetch, Grep/Glob/Read).
After it returns, check for
remaining `[NEEDS CLARIFICATION]` markers and resolve via
consensus if needed (see Rule 6).

### 6. Two-layer resolution with consensus agents

After EACH executor subagent returns for a consensus phase
(Clarify, Checklist, Analyze), run a two-layer resolution
process BEFORE spawning the next subagent.

**Layer 1 — Executor does direct research:** The executor
agent (clarify-executor, checklist-executor,
analyze-executor) researches using web search, library docs,
and codebase exploration (Tavily, Context7, RepoPrompt when
available, built-in WebSearch, WebFetch, Grep/Glob/Read
otherwise). It resolves most items
directly and applies fixes to artifacts. Items it can't
resolve are flagged in its "Unresolved for consensus"
summary section.

**Layer 2 — Consensus agents for unresolved items:** For
EACH unresolved item from the executor's summary, spawn 3
consensus agents IN PARALLEL:

```text
For each unresolved item:
  Agent(subagent_type: "codebase-analyst",
        run_in_background: true,
        prompt: "<consensus prompt>")     ← TOOL CALL
  Agent(subagent_type: "spec-context-analyst",
        run_in_background: true,
        prompt: "<consensus prompt>")     ← TOOL CALL
  Agent(subagent_type: "domain-researcher",
        run_in_background: true,
        prompt: "<consensus prompt>")     ← TOOL CALL
  Wait for all 3 to complete              ← TOOL CALLS
  Apply consensus rules                   ← decision
  Edit artifact with consensus answer     ← TOOL CALL
```

**Consensus rules (see consensus-protocol.md):**
- 2/3 agree → use majority answer
- 3/3 agree → use with high confidence
- All disagree → flag `[HUMAN REVIEW NEEDED]`, STOP
- Security keyword → always flag for human

**Why two layers:** Executor handles ~80% directly. Consensus
provides distinct perspectives for genuinely ambiguous items.

**Why after each prompt:** Later sessions may depend on
earlier resolved questions/gaps.

**Stop conditions:** Gate failure after 2 auto-fix attempts,
failed consensus (all disagree), security keyword, or
missing prerequisite.

You run in the **main session** (not as a sub-agent) so you can
spawn sub-agents directly. Sub-agents cannot nest — this is the
Orchestrator-Direct pattern.

## Input

You receive a workflow file path and optional arguments:

```text
path/to/workflow-file.md [--from-phase specify|clarify|plan|checklist|tasks|analyze|implement] [--spec SPEC-ID]
```

## Step 0: Prerequisites

Run the prerequisite scripts to verify the environment. If any
check fails, STOP with the error message from the JSON output.

### 0.1-0.7 Environment Checks

```text
Bash("bash scripts/check-prerequisites.sh <workflow_file_path>")
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

### 0.6 Load Settings

Read `.claude/speckit-pro.local.md` if it exists. Parse YAML
frontmatter for: `consensus-mode` (default: `moderate`),
`gate-failure` (default: `stop`), `auto-commit` (default:
`per-phase`), `security-keywords` (default: standard list).
If the file doesn't exist, use all defaults.

### 0.8 MCP Server & Plugin Limitation Check

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

### 0.9 Constitution Validation

Read the workflow file's Prerequisites table. If already
`Verified`, skip (resuming a workflow). Otherwise:

1. Read constitution from `.specify/memory/constitution.md`
2. For each principle, run the appropriate PROJECT_COMMANDS
   check (typecheck, test suite, build, lint). For code
   review items (KISS, YAGNI, SOLID), mark `Verified` —
   these are validated during implementation.
3. Update the workflow file's table with results and baselines
4. If any check fails, STOP — do not proceed to Phase 1

### 0.10 Implementation Agent Detection

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

### 0.11 Project Command Discovery

```text
Bash("bash scripts/detect-commands.sh")
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

```text
Bash("bash scripts/detect-presets.sh")
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

## Step 1: Parse Workflow State

Read the workflow file and parse the "Workflow Overview" status
table. Find the first phase with status `⏳ Pending` or
`🔄 In Progress`.

If `--from-phase` is specified, start from that phase regardless of
the status table.

If all phases are `✅ Complete`, report "All phases complete" and
stop.

### 1.1 Create Progress Task List

After parsing the workflow state, create a **granular** task list.
For multi-prompt phases (Clarify, Checklist), create one task per
prompt/session so the autopilot knows exactly what to execute next.

**Task naming pattern** (parse from workflow file):

```text
  "Phase 0: Prerequisites"
  "Phase 1: Specify"
  "Phase 2: Clarify - <Session Name>"           ← one per session
  "Phase 2: Clarify - <Session Name> Consensus" ← MANDATORY after each session
  "Phase 3: Plan"
  "Phase 4: Checklist - <Domain>"               ← one per domain
  "Phase 4: Checklist - <Domain> Consensus"     ← MANDATORY after each domain
  "Phase 5: Tasks"
  "Phase 6: Analyze"
  "Phase 6: Analyze - Consensus"                ← MANDATORY after analyze
  "Phase 7: <Group> (<task IDs>)"               ← parsed from tasks.md
  "Post: <task name>"                           ← from post-impl table
```

**CRITICAL — Consensus tasks are MANDATORY:**

Every Clarify session, every Checklist domain, and the Analyze
phase MUST have a corresponding Consensus task immediately after
it. The consensus task runs the two-layer resolution process
(Rule 6) — skipped only if the executor reports zero unresolved
items. **Never omit consensus tasks from the task list.**

**Other rules:**
- Phase 7 decomposed into groups after tasks.md is created
  (test/impl/verify per phase, see `references/phase-execution.md`)
- Extension tasks (doctor, verify-tasks, verify, review,
  cleanup, retrospective): add if extension is in .registry
  with enabled: true, or if extension directory exists via Glob
- Mark completed phases immediately; first pending as in_progress

## Step 2: Main Execution Loop

For each pending phase, spawn a subagent, collect the result,
validate the gate, and advance. Every step is a tool call.

```text
PHASES = [specify, clarify, plan, checklist, tasks, analyze, implement]

for phase in PHASES starting from first_pending:
    1. TaskUpdate: set phase task to "in_progress"
    2. Check .specify/extensions.yml for before_<phase> hooks
       → run accepted hooks (non-destructive), skip duplicates
    3. Read the workflow file's prompt(s) for this phase
    4. For EACH prompt in the phase:
       a. Agent(prompt: "Run /speckit.<phase> with: <prompt>")
       b. Receive subagent summary (tool result)
       c. TaskUpdate: set this prompt's task to "completed"
    5. Run consensus in main session if needed:
       Parse executor's "Unresolved for consensus" section.
       For each item → spawn 3 consensus agents in parallel
       (codebase-analyst, spec-context-analyst, domain-researcher)
       → apply consensus rules → edit artifacts
    6. Check .specify/extensions.yml for after_<phase> hooks
       → run accepted hooks (non-destructive), skip duplicates
    7. Validate gate (see gate-validation.md)
    8. If gate fails:
       a. Attempt auto-fix (max 2 attempts)
       b. If still failing and gate-failure == "stop": STOP
       c. If gate-failure == "skip-and-log": log, continue
    9. Update workflow file with results
   10. If auto-commit == "per-phase":
       For phases 1-6: Bash: git add specs/ && git commit
       For phase 7 (implement): Bash: git add -A && git commit
       (implementation changes include src/, tests/, etc.)
   11. Advance to next phase (next iteration of loop)

POST-IMPLEMENTATION (after all 7 phases complete):
    These are tasks in your task list — execute them in order.

    ⚠️ HOW EXTENSION COMMANDS BECOME AVAILABLE:
    Commands like speckit.verify, speckit.review, speckit.cleanup,
    speckit.doctor, speckit.retrospective.analyze are INSTALLED by
    `specify extension add <name>`. The CLI creates command files
    in .claude/commands/ (or equivalent for other agents). These
    commands then appear as invocable skills.

    If Step 0.12 detected the extension in .registry as enabled,
    its commands ARE available — run the task.
    If an extension is NOT in .registry and NOT in Glob results,
    log a warning and skip that specific task (do NOT fail the
    entire autopilot). Recommend: `specify extension add <name>`.

    ⚠️ CRITICAL: Use Agent() subagents for ALL post-implementation
    tasks — NEVER use Skill() directly. Rule #1 applies here too:
    a Skill() call loads the command into YOUR context, and the
    command's completion text can kill the agent loop, preventing
    subsequent tasks from running.

    Post-implementation tasks (execute in order):

    | # | Task | Requires | Command |
    |---|------|----------|---------|
    | 10 | Verify Implementation | verify ext | /speckit.verify |
    | 11 | Code Review | review ext | /speckit.review |
    | 12 | Integration Suite | (none) | Step 3.1 direct |
    | 13 | Cleanup | cleanup ext | /speckit.cleanup |
    | 14 | PR Creation | (none) | Step 3.2 direct |
    | 15 | Review Remediation | (none) | Step 3.3 /loop |
    | 16 | Retrospective | retrospective ext | /speckit.retrospective.analyze |

    Extension tasks: Agent(subagent_type: "general-purpose",
      prompt: "Run /<command> for SPEC-XXX. Return summary.")
    Non-extension tasks (12, 14, 15): execute directly per Step 3.
    Missing extension: log warning and skip (don't fail).
    See references/post-implementation.md for detailed prompts.
    Task 16 is the FINAL STEP.
```

**Dynamic task updates:** If consensus reveals new questions or
remediation adds loops, create additional tasks via TaskCreate.

### Phase Dispatch

For each phase: read the prompt, spawn a subagent, validate.

#### Subagent Prompt Construction

Use the phase-specific executor agent:

```text
Agent(
  subagent_type: "<agent for this phase>",
  description: "SPEC-XXX <phase>",
  prompt: """
    <phase-specific prefix if needed>

    [IF presets detected in Step 0.12]
    PRESET_CONVENTIONS:
      Preset: <name> (priority <N>)
      Overrides: <templates this preset replaces>
      Enforces: <conventions from preset templates>
    [/IF]

    [IF PROJECT_COMMANDS discovered in Step 0.11]
    PROJECT_COMMANDS:
      BUILD: <cmd>  TYPECHECK: <cmd>  LINT: <cmd>
      UNIT_TEST: <cmd>  INTEGRATION_TEST: <cmd>
    [/IF]

    Workflow prompt:
    ---
    <paste the exact prompt from the workflow file>
    ---
  """
)
```

**Agent selection:**

| Phase | subagent_type | Prefix |
| ----- | ------------- | ------ |
| Specify | `phase-executor` | Branch-aware (if ON_FEATURE_BRANCH) |
| Clarify | `clarify-executor` | Interactive (ALWAYS) |
| Plan | `phase-executor` | None |
| Checklist | `checklist-executor` | None |
| Tasks | `phase-executor` | None |
| Analyze | `analyze-executor` | None |
| Implement | per-task routing | TDD protocol + COMPLETED_TASKS context (see "Implement — Task-Level Dispatch") |

#### Specify — Branch-Aware Prefix

When `ON_FEATURE_BRANCH` is true (Step 0.7), add this prefix
to the subagent prompt before the workflow prompt:

```text
IMPORTANT: Already on feature branch `<CURRENT_BRANCH>`.
Do NOT run `create-new-feature.sh` or create a new branch.
The branch and `specs/<CURRENT_BRANCH>/` directory already
exist. Skip directly to spec content generation.
```

All other phases use `check-prerequisites.sh` →
`get_current_branch()` which detects the worktree branch
automatically. No prefix needed.

#### Clarify — Autonomous Answering Prefix

The `/speckit.clarify` command is interactive — it surfaces
questions and expects answers. The clarify-executor invokes
the command and answers autonomously. Its agent definition
contains strong override instructions telling it to research
and answer every question immediately without waiting for
human input. No additional prefix needed in the prompt —
just pass the session prompt from the workflow file.

#### Multi-Prompt Phases

Clarify and Checklist have multiple prompts. Spawn a
**separate subagent for each prompt**:

- **Clarify:** One subagent per session (e.g., "Session 1:
  Search Behavior", "Session 2: Database Operations")
- **Checklist:** One subagent per domain (e.g.,
  api-workaround, type-safety, requirements)

#### Resolution — After Each Prompt (Main Session)

After EACH executor subagent returns, run the two-layer
resolution process BEFORE spawning the next subagent.

**Layer 1 — Check executor results:**

Parse the executor's summary for:
- Remaining markers (`[NEEDS CLARIFICATION]`, `[Gap]`)
- Items in the "Unresolved for consensus" section
- Security keyword items (always go to consensus)

If no unresolved items → skip to next prompt/gate.

**Layer 2 — Spawn consensus agents:**

For each unresolved item, spawn 3 consensus agents in
parallel:

```text
TaskUpdate: "<Phase> - <Prompt> Consensus" → in_progress

For each unresolved item from executor summary:
  Agent(
    subagent_type: "codebase-analyst",
    run_in_background: true,
    description: "SPEC-XXX consensus: <item summary>",
    prompt: """
      You are participating in consensus resolution.
      Context: <spec/plan/tasks excerpts relevant to item>
      Item: <unresolved question/gap/finding text>
      Executor's attempt: <what the executor tried>
      Your task: Propose the best answer from your
      perspective (existing codebase patterns).
    """
  )                                        ← TOOL CALL
  Agent(
    subagent_type: "spec-context-analyst",
    run_in_background: true,
    description: "SPEC-XXX consensus: <item summary>",
    prompt: "...<same item, your perspective>..."
  )                                        ← TOOL CALL
  Agent(
    subagent_type: "domain-researcher",
    run_in_background: true,
    description: "SPEC-XXX consensus: <item summary>",
    prompt: "...<same item, your perspective>..."
  )                                        ← TOOL CALL

  Wait for all 3 to complete
  Compare answers using consensus rules:
    - 2/3 agree → Edit artifact with majority answer
    - 3/3 agree → Edit artifact with high confidence
    - All disagree → flag [HUMAN REVIEW NEEDED], STOP
    - Security keyword → present all 3 to human, STOP
  Log result to Consensus Resolution Log in workflow file

TaskUpdate: "<Phase> - <Prompt> Consensus" → completed
```

**Per-phase specifics:**

- **Clarify:** After each session → grep spec.md for
  `[NEEDS CLARIFICATION]`. Parse executor's "Unresolved
  for consensus" section. Run consensus for each. Apply
  consensus answers to spec.md, remove markers. Proceed
  to next session.
- **Checklist:** After each domain → parse executor's
  "Unresolved for consensus" section. Run consensus for
  each unresolved gap. Apply consensus fixes to spec.md
  or plan.md. Re-run domain checklist to verify if any
  gaps were fixed by consensus. Proceed to next domain.
- **Analyze:** After analysis → parse executor's
  "Unresolved for consensus" section. Run consensus for
  each unresolved finding. Apply consensus fixes to
  tasks.md, spec.md, or plan.md. Re-run analyze to verify
  if findings were fixed by consensus.

#### Implement — Task-Level Dispatch

Phase 7 dispatches each task to the best-fit agent instead of
one monolithic executor. Subagents can't nest — task-level
routing solves this with flat orchestrator-worker.

**Agent routing:**

| Task Type | Agent | TDD? |
|-----------|-------|------|
| Tests (contract/unit/integration) | `implement-executor` | Yes |
| Domain implementation | PROJECT_IMPLEMENTATION_AGENT | Yes |
| Research / API investigation | `domain-researcher` | No |
| Verification (build, lint) | orchestrator-direct | No |

Every implementation agent receives the TDD protocol from
`references/tdd-protocol.md`. Agent selection is about domain
expertise — all follow identical RED-GREEN-REFACTOR discipline.

**Full algorithm** (parse tasks, route, dispatch, accumulate
context, verify): see `references/phase-execution.md` —
"Phase 7: Implement (Task-Level Dispatch)".

## Step 3: Post-Implementation

After all 7 phases complete and G7 passes, follow the
detailed procedures in `references/post-implementation.md`:

1. **3.1 Integration Suite** — verify spec-specific tests
   exist, run FULL suite to catch regressions, fix failures
2. **3.2 PR Creation** — final verification, push, create PR
   with auto-generated summary, update workflow file
3. **3.3 Review Remediation** — schedule `/loop` to monitor
   and resolve Copilot/human review comments every 5 minutes

After scheduling the loop, the autopilot is DONE. Report
the final summary with PR URL.

## Workflow File Update Protocol

After EVERY phase, update these sections in the workflow file:

| Phase | Sections to Update |
| --- | --- |
| **All** | Status table: `⏳` → `✅` with summary notes |
| **Specify** | Specify Results table, Files Generated checkboxes |
| **Clarify** | Clarify Results table (session focus, questions, outcomes) |
| **Plan** | Plan Results table (artifact status) |
| **Checklist** | Checklist Results table, Addressing Gaps section |
| **Tasks** | Tasks Results table (total, phases, parallel, coverage) |
| **Analyze** | Analysis Results table (ID, severity, issue, resolution) |
| **Implement** | Implementation Progress, Post-Implementation Checklist, Success Criteria |

Also update the Constitution Validation table after Specify (initial)
and Implement (final).

If consensus was used, add entries to the Consensus Resolution Log.

## Error Recovery

### Resuming After Interruption

The workflow file persists all state. To resume:

```text
/speckit-pro:autopilot workflow.md --from-phase <next-pending-phase>
```

The autopilot reads prior artifacts from disk and continues from
the specified phase.

### Common Issues

- **Subagent returns empty/incomplete summary:** Re-spawn with
  the same prompt. If it fails again, run the command directly
  via Bash and parse the output.
- **Gate fails after 2 auto-fix attempts:** If `gate-failure`
  setting is `stop`, STOP and report. Show the gate script
  output so the user can diagnose.
- **Consensus agents all disagree:** Flag `[HUMAN REVIEW NEEDED]`
  and STOP. Present all 3 perspectives to the user.
- **MCP tool unavailable:** Skip research that depends on it.
  Use Read/Grep fallback for codebase analysis. Log warning.

### Context Window Management

For large specs, the context window may fill across 7 phases.
Mitigations:

- Keep sub-agent results concise (summaries, not full artifacts)
- The workflow file is the persistent record — read it rather than
  relying on conversation memory
- Auto-compaction preserves CLAUDE.md and system instructions
- If compacted, re-read the workflow file to restore state

## References

- [Phase Execution](./references/phase-execution.md) — Per-phase
  prompt construction and execution details
- [Consensus Protocol](./references/consensus-protocol.md) —
  Multi-agent resolution rules and flows
- [Gate Validation](./references/gate-validation.md) — Programmatic
  gate checks and remediation loops
- [Post-Implementation](./references/post-implementation.md) —
  Integration suite, PR creation, review remediation loop
- [TDD Protocol](./references/tdd-protocol.md) — Red-green-refactor
  rules injected into implementation agent prompts
- [Plugin Limitations](./references/plugin-limitations.md) —
  permissionMode, hooks, mcpServers restrictions for plugin agents;
  MCP server prerequisites and fallback behavior

## Scripts

Deterministic bash scripts for prerequisite checks and validation:

- `scripts/check-prerequisites.sh <workflow_file>` — Verify CLI,
  project init, constitution, commands, branch detection (JSON)
- `scripts/validate-gate.sh <G1-G7> <feature_dir>` — Validate
  any gate with marker counts and details (JSON)
- `scripts/detect-commands.sh` — Auto-detect build/test/lint
  commands for Node.js, Rust, Go, Python, Makefile (JSON)
- `scripts/detect-presets.sh` — Find installed presets,
  extensions, hooks, template resolution (JSON)
- `scripts/count-markers.sh <type> <feature_dir>` — Deterministic
  marker counting (gaps, findings, clarifications, all) for agent
  validation. Used by analyze-executor and checklist-executor (JSON)
