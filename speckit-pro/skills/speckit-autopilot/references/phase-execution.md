# Phase Execution Reference

**RULES (from SKILL.md — repeated here for clarity):**

1. **SUBAGENT PER PHASE** — Spawn a foreground subagent for
   each phase via the Agent tool. The subagent runs the
   `/speckit.*` command and returns a summary. The parent
   receives the result as a tool response, keeping the agent
   loop alive.
2. **MULTI-PROMPT** — Clarify and Checklist have multiple
   prompts. Spawn a separate subagent for each prompt.
3. **TWO-LAYER RESOLUTION** — After executor subagents
   return, the main session parses "Unresolved for
   consensus" items and spawns 3 consensus agents in
   parallel (codebase-analyst, spec-context-analyst,
   domain-researcher) for each unresolved item.
4. **TASK LIST DRIVES EXECUTION** — Check the task list
   after each subagent returns to know what's next.

---

How each SDD phase is executed by the autopilot. Each phase
is delegated to a **foreground subagent** that runs the real
`/speckit.*` command via the `Skill` tool. The subagent
operates in its own context — the command's noise (template
reads, file exploration, completion reports) stays there and
never touches the parent. The parent receives only a summary.

## SpecKit Infrastructure

The autopilot relies on the project's installed SpecKit
commands and scripts:

| Component | Location | Purpose |
| ----------- | ---------------------------------------- | --------------------------------------------------------- |
| **Commands** | `.claude/commands/speckit.*.md` | Slash commands that orchestrate each SDD phase |
| **Scripts** | `.specify/scripts/bash/` | Shell scripts for branch creation, path resolution, prerequisite checking |
| **Templates** | `.specify/templates/` | Spec, plan, tasks, checklist, and agent file templates |
| **Constitution** | `.specify/memory/constitution.md` | Project principles for gate validation |

### Key Scripts

| Script | Used By | What It Does |
| -------- | --------- | ----------- |
| `common.sh` | All scripts | Branch detection (`get_current_branch`), feature path resolution (`get_feature_paths`, `find_feature_dir_by_prefix`) |
| `create-new-feature.sh` | `/speckit.specify` | Creates git branch, `specs/` dir, copies spec template. Supports `--json`, `--short-name`, `--number` |
| `setup-plan.sh` | `/speckit.plan` | Copies plan template to feature dir. Outputs `FEATURE_SPEC`, `IMPL_PLAN`, `SPECS_DIR`, `BRANCH` |
| `check-prerequisites.sh` | `/speckit.clarify`, `.checklist`, `.tasks`, `.analyze`, `.implement` | Validates feature dir + required files exist. Supports `--json`, `--require-tasks`, `--include-tasks`, `--paths-only` |
| `update-agent-context.sh` | `/speckit.plan` | Updates CLAUDE.md with tech stack extracted from plan.md |

## Subagent Delegation

Each phase is executed by spawning a foreground subagent via
the Agent tool. The subagent:

1. Loads the `/speckit.*` command via `Skill()`
2. Runs the command in its own context
3. Returns a concise summary to the parent

The parent receives the summary as a tool result, which keeps
the parent's agent loop alive. The parent then validates the
gate and spawns the next subagent.

### Subagent Prompt Template

Use the `phase-executor` agent type for every phase. This
agent is pre-configured with rules to run the command and
return only a structured summary.

```text
Agent(
  subagent_type: "phase-executor",
  description: "SPEC-XXX <phase>",
  prompt: """
    Run the /speckit.<phase> command.
    Use: Skill("speckit.<phase>", args: "<workflow prompt>")

    <branch prefix if ON_FEATURE_BRANCH>

    Workflow prompt:
    ---
    <exact prompt from workflow file>
    ---
  """
)
```

The phase-executor handles summary formatting and the
"no recommendations" constraint automatically.

## Branch/Worktree Detection

Before executing any phase, detect the current branch context:

```bash
# Detect current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")

# Check if in a worktree
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
GIT_COMMON=$(git rev-parse --git-common-dir 2>/dev/null)
IS_WORKTREE=$( [ "$GIT_DIR" != "$GIT_COMMON" ] && echo "true" || echo "false" )
```

Record two facts:

- **`ON_FEATURE_BRANCH`**: `true` if `CURRENT_BRANCH` matches
  `^[0-9]{3}-`
- **`IS_WORKTREE`**: `true` if `GIT_DIR != GIT_COMMON`

When `ON_FEATURE_BRANCH` is true, the Specify subagent gets
a "skip branch creation" prefix in its prompt. Do NOT use
`export SPECIFY_FEATURE` — env vars do not persist across
tool invocations.

## Phase-by-Phase Execution

Each phase follows the same pattern: read prompt → spawn
subagent → receive summary → validate gate → advance.

### Progress Task List

Before executing phases, create a **granular** task list
(visible in the CLI, survives context compaction):

- One task per single-prompt phase (Specify, Plan, Tasks,
  Analyze, Implement)
- One task **per prompt** for multi-prompt phases (each
  Clarify session, each Checklist domain)
- One task for consensus/remediation after multi-prompt
  phases (only runs if needed)
- Parse the workflow file to get session/domain names

Update tasks as each subagent returns.

### Phase 0: Prerequisites (Constitution Validation)

**No subagent.** This runs directly in the main session —
it does NOT invoke a `/speckit.*` command.

1. Read `.specify/memory/constitution.md` — extract all
   numbered principles
2. Run automated checks using PROJECT_COMMANDS from Step
   0.10 (BUILD, TYPECHECK, LINT, UNIT_TEST, INTEGRATION_TEST)
3. Verify structural patterns documented in CLAUDE.md
   (e.g., source code organization, module boundaries)
4. Record baselines in the workflow file's Prerequisites
   table
5. Set the "Constitution Check" summary line

**Gate:** G0 — all automated checks must pass. If any
fail, STOP.

**Doctor Health Check (ALWAYS — plugin skill):**
After G0 passes, run `/speckit.doctor` for a full
project diagnostic (structure, agents, features, scripts,
extensions, git). Log the report in the workflow file.

```text
TaskUpdate: "Phase 0: Doctor Health Check" → in_progress
Agent(
  subagent_type: "general-purpose",
  description: "SPEC-XXX doctor health check",
  prompt: "Run /speckit.doctor for this project.
    Return the diagnostic report summary."
)
TaskUpdate: → completed
```

⚠️ Use Agent() subagent, NOT Skill() directly — Skill() loads
the command into your context and can kill the agent loop.

### Phase 1: Specify

Read the workflow file's `### Specify Prompt` section.
Spawn a subagent:

```text
Agent(description: "SPEC-XXX specify", prompt: "...")
```

**Branch-aware:** If `ON_FEATURE_BRANCH` is true, add
prefix: "Already on feature branch `<branch>`. Do NOT run
`create-new-feature.sh`. Skip to spec content generation."

**Gate:** G1 — check subagent summary for
`[NEEDS CLARIFICATION]` markers (routing decision)

**Commit:**
`git add specs/ && git commit -m "feat(SPEC-XXX): complete specify phase"`

### Phase 2: Clarify (Conditional)

Only runs if G1 detected `[NEEDS CLARIFICATION]` markers.

Spawn a **separate subagent for each clarify session**.
The clarify-executor invokes `/speckit.clarify` and answers
questions autonomously using its research tools.

```text
For each clarify session in the workflow file:
  1. TaskUpdate: session task → in_progress
  2. Agent(subagent_type: "clarify-executor",
          prompt: """
            Run /speckit.clarify with: <session prompt>
          """)
  3. Parse executor's "Unresolved for consensus" section
  4. If unresolved items exist:
     a. TaskUpdate: "<session> Consensus" → in_progress
     b. For each item → spawn 3 consensus agents in parallel:
        - Agent(subagent_type: "codebase-analyst", run_in_background: true, ...)
        - Agent(subagent_type: "spec-context-analyst", run_in_background: true, ...)
        - Agent(subagent_type: "domain-researcher", run_in_background: true, ...)
     c. Wait for all 3 → apply consensus rules
     d. Edit spec.md with consensus answer, remove markers
     e. TaskUpdate: "<session> Consensus" → completed
  5. TaskUpdate: session task → completed
  6. Proceed to next session
```

**Layer 1 (executor):** The clarify-executor researches
each question using Tavily (API docs), Context7 (library
docs), RepoPrompt (codebase patterns), and Read/Grep
(constitution, prior specs). It resolves most questions
directly.

**Layer 2 (consensus):** For items the executor flagged
(low confidence, conflicting sources, security keywords),
the main session spawns 3 consensus agents to get distinct
perspectives and applies consensus rules.

**Why after each session:** Session 2 may depend on
Session 1's resolved questions. Both layers complete
before the next session runs.

**Gate:** G2 — verify 0 markers remain

**Commit:**
`git add specs/ && git commit -m "feat(SPEC-XXX): complete clarify phase"`

### Phase 3: Plan

Read the workflow file's `### Plan Prompt` section.
Spawn a subagent.

**Gate:** G3 — verify plan.md, research.md, data-model.md
exist

**Commit:**
`git add specs/ && git commit -m "feat(SPEC-XXX): complete plan phase"`

### Phase 4: Checklist

Spawn a **separate subagent for each checklist domain**,
with two-layer resolution **after each domain**:

```text
For each checklist domain in the workflow file:
  1. TaskUpdate: domain task → in_progress
  2. Agent(subagent_type: "checklist-executor",
          prompt: "Run /speckit.checklist with: <domain prompt>")
     The checklist-executor runs the checklist, researches
     gaps, applies fixes, and re-runs to verify (Layer 1)
  3. Parse executor's "Unresolved for consensus" section
  4. If unresolved gaps exist:
     a. TaskUpdate: "<domain> Consensus" → in_progress
     b. For each gap → spawn 3 consensus agents in parallel:
        - Agent(subagent_type: "codebase-analyst", run_in_background: true, ...)
        - Agent(subagent_type: "spec-context-analyst", run_in_background: true, ...)
        - Agent(subagent_type: "domain-researcher", run_in_background: true, ...)
     c. Wait for all 3 → apply consensus rules
     d. Edit spec.md or plan.md with consensus fix
     e. Re-run domain checklist to verify gap closed
     f. TaskUpdate: "<domain> Consensus" → completed
  5. TaskUpdate: domain task → completed
  6. Proceed to next domain
```

**Layer 1 (executor):** The checklist-executor handles
gap research and remediation internally using Tavily,
RepoPrompt, Context7, and codebase search.

**Layer 2 (consensus):** For gaps the executor couldn't
resolve (remained after 2 loops, low confidence, security
keywords), the main session spawns 3 consensus agents.

**Why after each domain:** Domain 2 may depend on Domain
1's gap fixes. Both layers complete before the next
domain runs.

**Gate:** G4 — verify 0 `[Gap]` markers

**Commit:**
`git add specs/ && git commit -m "feat(SPEC-XXX): complete checklist phase"`

### Phase 5: Tasks

Read the workflow file's `### Tasks Prompt` section.
Spawn a subagent.

**Gate:** G5 — cross-reference every FR in spec.md with
tasks.md

**Verify Tasks (ALWAYS — plugin skill):**
After G5 passes, run `/speckit.verify-tasks` to detect
phantom completions — tasks marked `[X]` that have no real
implementation. This catches tasks that were incorrectly
marked complete during previous iterations.

```text
TaskUpdate: "Phase 5: Verify Tasks" → in_progress
Agent(
  subagent_type: "general-purpose",
  description: "SPEC-XXX verify tasks",
  prompt: "Run /speckit.verify-tasks for SPEC-XXX.
    Check for phantom completions — tasks marked [X]
    that have no real implementation. Return findings."
)
TaskUpdate: → completed
```

⚠️ Use Agent() subagent, NOT Skill() directly.

**Optional: Tasks to GitHub Issues:**
If the project uses GitHub Issues for tracking and the GitHub
MCP server is available, export tasks to issues:

```text
TaskUpdate: "Phase 5: Tasks to Issues" → in_progress
Agent(
  subagent_type: "general-purpose",
  description: "SPEC-XXX tasks to issues",
  prompt: "Run /speckit.taskstoissues for SPEC-XXX."
)
TaskUpdate: → completed
```

Skip if GitHub MCP is not configured or the project uses a
different tracker (Jira, Azure DevOps, etc. — those have
their own extensions).

**Commit:**
`git add specs/ && git commit -m "feat(SPEC-XXX): complete tasks phase"`

### Phase 6: Analyze

Read the workflow file's `### Analyze Prompt` section.
Spawn the analyze-executor subagent.

The analyze-executor runs the analysis, researches ALL
findings at every severity, applies fixes, and re-runs to
verify (Layer 1). Items it can't resolve are flagged in its
"Unresolved for consensus" summary section.

```text
1. TaskUpdate: "Analyze" → in_progress
2. Agent(subagent_type: "analyze-executor",
        prompt: "Run /speckit.analyze with: <prompt>")
   The executor handles research + remediation (Layer 1)
3. Parse executor's "Unresolved for consensus" section
4. If unresolved findings exist:
   a. TaskUpdate: "Analyze - Consensus" → in_progress
   b. For each finding → spawn 3 consensus agents in parallel:
      - Agent(subagent_type: "codebase-analyst", run_in_background: true, ...)
      - Agent(subagent_type: "spec-context-analyst", run_in_background: true, ...)
      - Agent(subagent_type: "domain-researcher", run_in_background: true, ...)
   c. Wait for all 3 → apply consensus rules
   d. Edit tasks.md, spec.md, or plan.md with consensus fix
   e. Re-run analyze to verify finding resolved
   f. TaskUpdate: "Analyze - Consensus" → completed
5. TaskUpdate: "Analyze" → completed
```

If 0 unresolved items from executor, skip consensus and
advance immediately.

**Gate:** G6 — verify 0 CRITICAL findings

**Commit:**
`git add specs/ && git commit -m "feat(SPEC-XXX): complete analyze phase"`

### Phase 7: Implement (Task-Level Dispatch)

Phase 7 uses **task-level dispatch**: the orchestrator parses
tasks.md and dispatches each task (or parallel group) to the
best-fit agent. This replaces the monolithic implement-executor
pattern.

**Why task-level:** Subagents cannot spawn other subagents
(Claude Code platform constraint). The flat orchestrator-worker
pattern — recommended by Anthropic's BrowseComp architecture
and Research system — routes each task to a specialized agent
from the orchestrator level.

#### Step 1: Parse tasks.md

```text
1. Read tasks.md from specs/<feature>/
2. Parse phase groups (## Phase 1: Setup, ## Phase 2: ..., etc.)
3. Within each phase group:
   - Identify [P] (parallel) vs sequential tasks
   - Classify: test-only, implementation, verification
4. Build ordered task list respecting phase dependencies
```

#### Step 2: Load TDD Protocol

```text
Read references/tdd-protocol.md → store as TDD_PROTOCOL
```

This protocol is injected into every implementation agent's
prompt, ensuring identical RED→GREEN→REFACTOR discipline
regardless of which agent executes the task.

#### Step 3: Task-Level Execution Loop

```text
Initialize COMPLETED_TASKS = {}

For each phase group in tasks.md:
  TaskUpdate: "<Phase 7: group name>" → in_progress

  For each task in the group:
    1. ROUTE to agent:
       a. PROJECT_IMPLEMENTATION_AGENT — if task description
          matches keywords from the detected agent (Step 0.9)
       b. implement-executor — if test-only task (keywords:
          "test", "contract test", "unit test", "integration")
       c. domain-researcher — if research task (keywords:
          "research", "investigate", "explore API")
       d. orchestrator-direct — if verification-only (keywords:
          "verify", "run", "check", "build", "lint")
       e. implement-executor — default fallback

    2. BUILD prompt and DISPATCH:
       Agent(
         subagent_type: "<routed agent>",
         isolation: "worktree" (if [P] task in parallel group),
         description: "SPEC-XXX <task-id> <brief>",
         prompt: """
           <tdd_protocol>
           <TDD_PROTOCOL contents>
           </tdd_protocol>

           PROJECT_COMMANDS:
             BUILD: <cmd>  TYPECHECK: <cmd>  LINT: <cmd>
             UNIT_TEST: <cmd>  INTEGRATION_TEST: <cmd>
             SINGLE_FILE_TEST: <cmd>
             SINGLE_FILE_INTEGRATION: <cmd>

           <if PRESET_CONVENTIONS>
           PRESET_CONVENTIONS: ...
           </if>

           COMPLETED_TASKS:
             <structured list of prior task results>

           Your task:
           ---
           <exact task description from tasks.md>
           ---
         """
       )

    3. PARALLEL dispatch for [P] groups:
       Spawn ALL [P] tasks simultaneously — each with
       isolation: "worktree". Collect all results.
       If merge conflicts → fall back to sequential.

    4. SEQUENTIAL dispatch:
       Spawn one agent, await result, pass context to next.

    5. ACCUMULATE context:
       COMPLETED_TASKS[T00X] = {
         files: [paths created/modified],
         tests: N,
         status: "GREEN" | "RED" | "error"
       }

  Phase-group verification (orchestrator-direct):
    Bash(BUILD) && Bash(TYPECHECK) && Bash(LINT) &&
    Bash(UNIT_TEST)
    If any fail → dispatch fix agent, re-run.

  TaskUpdate: "<Phase 7: group name>" → completed
```

#### Step 4: Final Verification

After all phase groups complete:

```text
Run FULL_VERIFY:
  Bash(BUILD) && Bash(TYPECHECK) && Bash(LINT) &&
  Bash(UNIT_TEST) && Bash(INTEGRATION_TEST)
```

#### Agent Routing Table

| Task Type | Agent | TDD Protocol? |
|-----------|-------|---------------|
| Contract/unit/integration tests | `implement-executor` | Yes |
| Implementation needing project patterns | PROJECT_IMPLEMENTATION_AGENT | Yes |
| Research / API investigation | `domain-researcher` | No |
| Verification (build, lint, typecheck) | orchestrator-direct (Bash) | No |

Every agent receiving implementation work gets the TDD protocol
injected. Agent selection is about DOMAIN EXPERTISE — the
implement-executor is a TDD specialist, the project agent brings
domain knowledge. Both follow identical discipline.

**Gate:** G7 — full verification suite
(build + typecheck + lint + unit tests + integration tests)

**Commit:**
`git add -A && git commit -m "feat(SPEC-XXX): implement phase"`

**After G7 passes:** Run Integration/E2E Test Verification,
then execute PR Creation Protocol (see below).

## Full Integration / E2E Suite Verification

Integration tests are created DURING the Implement phase by
implementation agents (mandatory, not optional). This
post-implementation step runs the FULL suite to catch
regressions from other specs.

1. Verify spec-specific tests exist:
   `Glob("tests/integration/*<spec-name>*")`
2. If missing → spawn implement-executor to create them
   (the Implement phase failed to meet this requirement)
3. Run the FULL integration suite (all specs, not just new):
   `Bash("<INTEGRATION_TEST command>")`
4. Fix any failures (max 2 attempts)
5. Record results in workflow file

## Extension Hook Events

If extension hook events are configured (detected in Step
0.11 via `.specify/extensions/.registry` or Glob fallback),
the autopilot must handle prompts that fire at each phase.
Hooks are configured in `.specify/extensions.yml`.

**Extension detection priority (Step 0.11):**
1. `.specify/extensions/.registry` (JSON) — MOST authoritative.
   Check each extension's `enabled` field.
2. Glob `.specify/extensions/*/extension.yml` — fallback if
   no registry exists.
3. NEVER rely on the `installed` field in `.specify/extensions.yml`
   — it may be stale or empty even when extensions are active.

### All 8 Hook Events in the Autopilot Flow

| Hook Event | When It Fires | Autopilot Behavior |
|------------|--------------|-------------------|
| `before_specify` | Before Phase 1 starts | **Accept** — pre-flight checks are non-destructive |
| `after_specify` | After Phase 1 completes | **Accept** — may sync to external tools |
| `before_plan` | Before Phase 3 starts | **Accept** — validates prerequisites |
| `after_plan` | After Phase 3 completes | **Accept** — may generate additional artifacts |
| `before_tasks` | Before Phase 5 starts | **Accept** — verifies plan completeness |
| `after_tasks` | After Phase 5 completes | **Accept** — e.g., verify-tasks checks for phantom completions |
| `before_implement` | Before Phase 7 starts | **Accept** — checklist pre-checks |
| `after_implement` | After Phase 7 completes | **Accept** — e.g., verify, review, retrospective |

**Where hooks fire in the execution loop:**

```text
for each phase:
  1. Check .specify/extensions.yml for before_<phase> hooks
  2. If hooks exist → run accepted hooks, skip duplicates
  3. Spawn subagent for the phase
  4. Receive result
  5. Check .specify/extensions.yml for after_<phase> hooks
  6. If hooks exist → run accepted hooks, skip duplicates
  7. Validate gate
  8. Advance
```

### Hook Handling Rules

1. **Accept non-destructive hooks** — read-only verification,
   reports, and analysis hooks are safe to run automatically
2. **Skip hooks that duplicate autopilot verification** — if
   the autopilot already runs the same check (e.g., cleanup
   vs the autopilot's own lint/test verification), skip to
   avoid redundancy
3. **Document decisions in workflow file** — log which hooks
   were accepted, skipped, and why
4. **Check ALL 8 events** — don't assume only after_tasks
   and after_implement have hooks. Extensions may register
   hooks for any event. Read `.specify/extensions.yml` to
   know which events have hooks configured.

**Hook `optional` field behavior:**
- `optional: true` — In interactive mode, the CLI prompts the user
  before running. The autopilot runs NON-INTERACTIVELY, so it
  must decide automatically: **auto-accept** hooks that match the
  acceptance rules above (non-destructive, no duplication).
  The autopilot does NOT literally respond to a prompt — it
  invokes the hook's command directly via `Skill()`.
- `optional: false` — The hook auto-executes without prompting.
  The autopilot should always run these.
- `enabled: false` — The hook is disabled. Skip it entirely.

### Preset-Aware Phase Execution

If presets are installed (detected in Step 0.11), the autopilot
should understand what the presets enforce:

1. **Read preset templates** at startup (Step 0.11) to learn
   what conventions the project uses (TDD mandates, architecture
   patterns, test requirements, etc.)
2. **Pass conventions to subagents** — include PRESET_CONVENTIONS
   in the implement-executor and other subagent prompts so they
   follow the project's patterns without hardcoding
3. **Expect different artifact structure** — if a preset overrides
   `tasks-template.md`, the generated tasks will have different
   sections than core defaults. The autopilot's task parsing
   should handle any structure.
4. **Debug with `specify preset resolve`** — if artifacts have
   unexpected structure, run `specify preset resolve <template>`
   to see which file the `/speckit.*` command actually used

## PR Creation Protocol

After G7 passes:

```text
Step 1: Run final verification suite (build, typecheck, lint, test)
Step 2: Detect remote name: git remote -v
Step 3: Push branch: git push -u <remote> <branch>
Step 4: Create PR via gh CLI:
  gh pr create \
    --title "feat(SPEC-XXX): <Spec Name>" \
    --body "<auto-generated from spec artifacts>"
Step 5: Update workflow file with PR URL
Step 6: Final commit: "feat(SPEC-XXX): open PR for review"
```

## Copilot Review Remediation Loop

After PR creation, use `/loop` to schedule recurring review
comment monitoring. The loop prompt must be **self-contained**
— each cron fire runs in a fresh context with no memory.

**Before invoking `/loop`:**
1. Extract PR number from `gh pr create` output
2. Extract repo owner/name from `git remote -v`
3. Hardcode both values in the loop prompt

**Prompt structure for `/loop`:**

```text
Skill("loop", args: "5m
  Check PR #<PR_NUMBER> in <REPO> for unresolved review
  comments and resolve them.

  Step 1 — Fetch reviews and comments:
  Bash('gh api repos/<REPO>/pulls/<PR_NUMBER>/reviews ...')
  Bash('gh api repos/<REPO>/pulls/<PR_NUMBER>/comments ...')

  Step 2 — If 0 unresolved, report and stop.

  Step 3 — For each unresolved comment:
  a. Code fix → edit, verify suite, commit, push, reply, resolve
  b. Style → lint:fix, commit, push, reply, resolve
  c. Question/FP → reply via gh api, then resolve

  Step 4 — Report summary.
")
```

**Critical:** All values (PR number, repo, branch) must be
hardcoded strings in the prompt. Variables and references to
conversation context will not resolve — the cron fires in a
clean session.

The loop auto-expires after 3 days (Claude Code limit).

## Workflow File Update Protocol

After each phase completes, update the workflow file with:

1. **Status table**: Change phase status from
   `⏳ Pending` to `✅ Complete` with summary notes
2. **Phase-specific results table**: Fill in metrics
   and outcomes
3. **Files Generated checkboxes**: Check off produced
   artifacts
4. **Consensus Resolution Log** (if applicable): Record
   consensus decisions

The workflow file serves as both checklist and execution
log — the complete auditable record of the autonomous
execution.
