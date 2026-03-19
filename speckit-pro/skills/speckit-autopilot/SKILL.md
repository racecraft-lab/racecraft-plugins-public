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

Your context window will be automatically compacted as it
approaches its limit, allowing you to continue working
indefinitely. Do not stop tasks early. Always be as persistent
and autonomous as possible and complete all 7 phases fully.

You are an **orchestrator** for SpecKit workflows. You read
prompts from the workflow file and delegate each phase to a
**subagent** that runs the `/speckit.*` command. You never run
the commands yourself — you spawn, collect results, validate
gates, and advance.

<hard_constraints>

## Execution Rules

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

### 2. Use the phase-executor agent

Every phase subagent uses the `phase-executor` agent type.
This agent is pre-configured with rules to run the command
and return only a summary.

```text
Agent(
  subagent_type: "phase-executor",
  description: "SPEC-XXX <phase>",
  prompt: """
    Run the /speckit.<phase> command.
    Use: Skill("speckit.<phase>", args: "<workflow prompt>")

    <any branch-aware prefix if needed>

    Workflow prompt:
    ---
    <paste the prompt from the workflow file>
    ---
  """
)
```

The phase-executor loads the Skill in its own context, runs
the command, and returns only a structured summary. All the
command's noise (template reads, file exploration, completion
reports) stays in the subagent's context and never touches
yours.

### 3. Task list first

Before executing any phase, create a granular task list using
TaskCreate. Parse the workflow file's Clarify and Checklist
sections to determine the exact number of sessions/domains.

**Why:** The task list drives your execution loop. After each
subagent returns, check the task list to know what's next.

**Example for a spec with 2 clarify sessions and 3 checklist
domains:**

```text
TaskCreate:
  "Phase 0: Prerequisites"
  "Phase 1: Specify"
  "Phase 2: Clarify - Session 1: Search Behavior"
  "Phase 2: Clarify - Session 2: Database Operations"
  "Phase 2: Clarify - Consensus Resolution"
  "Phase 3: Plan"
  "Phase 4: Checklist - Domain 1: api-workaround"
  "Phase 4: Checklist - Domain 2: type-safety"
  "Phase 4: Checklist - Domain 3: requirements"
  "Phase 4: Checklist - Gap Remediation"
  "Phase 5: Tasks"
  "Phase 6: Analyze"
  "Phase 6: Analyze - Finding Remediation"
  "Phase 7: Implement"
  "Post: PR Creation"
```

Set each task to `in_progress` when starting and `completed`
when done. Add tasks dynamically if unexpected work arises.

### 4. Multi-prompt phases

Clarify and Checklist have multiple prompts in the workflow
file. Spawn a **separate subagent for each prompt**.

**What this looks like:**

```text
CORRECT (Clarify with 2 sessions):
  1. TaskUpdate: "Clarify - Session 1" → in_progress
  2. Agent(subagent_type: "phase-executor", prompt: "Run /speckit.clarify with: <session 1>")
  3. Grep spec.md for [NEEDS CLARIFICATION] markers
  4. If markers → spawn 3 consensus agents, resolve
  5. TaskUpdate: "Clarify - Session 1" → completed
  6. TaskUpdate: "Clarify - Session 2" → in_progress
  7. Agent(subagent_type: "phase-executor", prompt: "Run /speckit.clarify with: <session 2>")
  8. Grep spec.md for [NEEDS CLARIFICATION] markers
  9. If markers → spawn 3 consensus agents, resolve
  10. TaskUpdate: "Clarify - Session 2" → completed
  11. Validate G2 gate (0 markers remaining)
  12. Advance to Plan

WRONG:
  1. Run all sessions, then check for markers at the end
  2. Or skip sessions and do your own analysis
```

### 5. Clarify is interactive — research and answer

The `/speckit.clarify` command is inherently interactive. It
surfaces clarification questions and expects answers. The
phase-executor subagent acts as the answerer — it uses
research tools to find evidence-grounded answers for each
question the command surfaces.

After the subagent returns, YOU (the main session) check for
any remaining `[NEEDS CLARIFICATION]` markers. If markers
remain, use RepoPrompt to investigate and resolve them:

1. **`context_builder`** with `response_type: "question"` —
   ask the question and let RepoPrompt autonomously explore
   the codebase, build context, and provide an answer
2. **`chat_send`** with the Evaluator or Senior-Planner
   model — get a second perspective on ambiguous questions
3. Apply the answer to spec.md and remove the marker

**Two-layer resolution:**

1. **Subagent (first pass):** The phase-executor researches
   and answers questions using Tavily (API docs), Context7
   (library docs), RepoPrompt (codebase patterns), and
   Read/Grep (constitution, prior specs). This handles most
   questions.
2. **Main session (second pass):** For any remaining markers,
   use `context_builder(response_type: "question")` to
   investigate. For security-keyword questions, always use
   this second pass regardless of what the subagent answered.

### 6. Consensus/remediation after each prompt

After EACH subagent returns for a consensus phase, check for
markers and run resolution BEFORE spawning the next subagent.

**Why:** Session 2 may depend on Session 1's resolved
questions. Checklist Domain 2 may depend on Domain 1's gap
fixes. Running resolution after each prompt ensures the spec
is updated before the next prompt runs.

**What this looks like:**

- **Clarify:** After each session subagent → grep for
  `[NEEDS CLARIFICATION]` → consensus via RepoPrompt chat
  if found → next session
- **Checklist:** After each domain subagent → grep for
  `[Gap]` → for each gap: research with `context_builder`
  + Tavily + constitution/prior specs → apply fix → re-run
  domain to verify → next domain
- **Analyze:** Single prompt → parse ALL findings at every
  severity → for each finding: research with
  `context_builder` + Tavily + constitution/prior specs →
  apply fix → re-run analyze to verify 0 findings remain

**The only reasons to stop:**

- Gate failure after 2 auto-fix attempts
- Failed consensus (all 3 agents disagree)
- Security keyword triggers mandatory human review
- Missing prerequisite that blocks execution

</hard_constraints>

You run in the **main session** (not as a sub-agent) so you can
spawn sub-agents directly. Sub-agents cannot nest — this is the
Orchestrator-Direct pattern.

## Input

You receive a workflow file path and optional arguments:

```text
path/to/workflow-file.md [--from-phase specify|clarify|plan|checklist|tasks|analyze|implement] [--spec SPEC-ID]
```

## Step 0: Prerequisites

Before executing any phase, verify ALL of the following. If any check
fails, STOP with a clear message.

### 0.1 SpecKit CLI

```bash
specify check
```

If this fails: "SpecKit CLI not found. Install:
`uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`"

### 0.2 Project Initialized

```bash
ls .specify/
```

If missing: "SpecKit not initialized. Run: `specify init --ai claude`"

### 0.3 Constitution Exists

```bash
cat .specify/memory/constitution.md
```

If missing: "No constitution found. Run: `/speckit.constitution`"

### 0.4 SpecKit Commands Installed

Verify the `/speckit.*` commands exist in `.claude/commands/`:

```bash
ls .claude/commands/speckit.specify.md .claude/commands/speckit.plan.md .claude/commands/speckit.tasks.md .claude/commands/speckit.implement.md
```

If missing: "SpecKit commands not found. Run:
`specify init --ai claude` to install commands."

### 0.5 Workflow File Exists

Read the provided workflow file path. If it doesn't exist, STOP.

### 0.6 Load Settings

Read `.claude/speckit-pro.local.md` if it exists. Parse YAML
frontmatter for:

- `consensus-mode` (default: `moderate`)
- `gate-failure` (default: `stop`)
- `auto-commit` (default: `per-phase`)
- `security-keywords` (default: the standard list)

If the file doesn't exist, use all defaults.

### 0.7 Branch Detection

Detect whether we're already on a feature branch (e.g., in a
worktree). This determines how the Specify phase behaves.

```bash
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
GIT_COMMON=$(git rev-parse --git-common-dir 2>/dev/null)
IS_WORKTREE=$( [ "$GIT_DIR" != "$GIT_COMMON" ] && echo "true" || echo "false" )
```

**Record two facts for later use:**

1. **`ON_FEATURE_BRANCH`**: `true` if `CURRENT_BRANCH` matches
   `^[0-9]{3}-` (e.g., `009-search-database`)
2. **`IS_WORKTREE`**: `true` if `GIT_DIR != GIT_COMMON`

**Why this matters:** The `/speckit.specify` command always calls
`create-new-feature.sh`, which runs `git checkout -b` to create a
new branch. On a worktree or existing feature branch, this would
fail or create a wrong nested branch. When `ON_FEATURE_BRANCH` is
`true`, the Specify phase must skip branch creation and use the
existing branch/directory instead (see Phase Dispatch → Specify
below).

Verify the branch matches the workflow file's `Branch` field. If
they don't match, warn the user and ask whether to proceed.

**Important:** Do NOT use `export SPECIFY_FEATURE=...` to try to
pass the branch to commands. Environment variables set in one Bash
call do not persist to Skill tool invocations. Instead, the
autopilot handles this by adjusting how it invokes each phase
(see Phase Dispatch).

### 0.8 Constitution Validation (Workflow Prerequisites)

The workflow file has a "Prerequisites" section with a constitution
validation table. This is **not** the same as Step 0.3 (which just
checks the file exists). This step validates that each constitution
principle is satisfied in the current codebase and records baselines.

**Procedure:**

1. Read the constitution from `.specify/memory/constitution.md` —
   extract all numbered principles
2. Read the workflow file's Prerequisites → Constitution Validation
   table
3. If the table is already `✅ Verified`, skip (resuming a previously
   started workflow)
4. For each constitution principle, run the appropriate
   verification:

   | Verification Type | How to Check |
   | --- | --- |
   | Type safety | Run `pnpm typecheck` (or project equivalent) |
   | Test suite | Run `pnpm test` — record current test count and file count as baseline |
   | Build discipline | Run `pnpm build` |
   | Lint/format | Run `pnpm lint` |
   | Architecture patterns | Use Glob/Grep to verify the pattern exists (e.g., definitions/primitives split) |
   | Code review items (KISS, YAGNI, SOLID) | Mark as `✅ Verified` — these are validated during implementation, not pre-flight |

5. Update the workflow file's Prerequisites table:
   - Fill in each principle's Status column
     (`✅ Pass` or `⚠️ Issue: ...`)
   - Record baseline numbers (e.g., "1924 tests pass",
     "34 definitions, 34 primitives")
   - Set the "Constitution Check" summary line:
     `✅ Verified <date> — Constitution v<version>, all principles satisfied`
6. If any verification **fails** (typecheck errors, test failures,
   build broken):
   - STOP and report: "Constitution validation failed — fix these
     issues before starting the workflow"
   - Do NOT proceed to Phase 1

**Example output** (from SPEC-007):

```markdown
| Principle | Requirement | Verification | Status |
|-----------|-------------|--------------|--------|
| I. Type-First Development | All functions typed, Zod contracts | `pnpm typecheck` | ✅ Pass |
| II. Separation of Concerns | definitions/ + primitives/ split | Code review | ✅ 34 definitions, 34 primitives |
| V. Defensive Error Handling | Structured errors, no swallowed exceptions | Unit tests | ✅ 1924 tests pass |

**Constitution Check:** ✅ Verified 2026-03-17 — Constitution v2.0.0 (RATIFIED), all principles satisfied
```

### 0.9 Implementation Agent Detection

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
implementation agent (e.g., "omnifocus-developer" or
"use the X agent for implementation").

**Record the result** for use in Step 2's Implement phase.

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

**Read the workflow file to determine the exact tasks:**

```text
TaskCreate (example for a spec with 2 clarify sessions, 3 checklist domains):
  - "Phase 0: Prerequisites (Constitution Validation)"
  - "Phase 1: Specify"
  - "Phase 2: Clarify - Session 1: Search Behavior"
  - "Phase 2: Clarify - Session 2: Database Operations"
  - "Phase 2: Clarify - Consensus Resolution"
  - "Phase 3: Plan"
  - "Phase 4: Checklist - Domain 1: api-workaround"
  - "Phase 4: Checklist - Domain 2: type-safety"
  - "Phase 4: Checklist - Domain 3: requirements"
  - "Phase 4: Checklist - Gap Remediation"
  - "Phase 5: Tasks"
  - "Phase 6: Analyze"
  - "Phase 6: Analyze - Finding Remediation"
  - "Phase 7: Implement"
  - "Post: Integration/E2E Test Suite"
  - "Post: PR Creation"
  - "Post: PR Review Remediation Loop"
```

**Rules:**

- Parse the workflow file's Clarify and Checklist sections to
  extract session/domain names and counts
- Create one task per clarify session and one per checklist domain
- Add a "Consensus Resolution" or "Gap Remediation" task after
  each multi-prompt phase (only runs if needed)
- Single-prompt phases (Specify, Plan, Tasks, Analyze, Implement)
  get one task each
- Mark already-completed phases as `completed` immediately
- Mark the first pending task as `in_progress`

**Why granular:** When "Clarify - Session 1" completes, the next
task ("Clarify - Session 2") is visible and in_progress — the
autopilot knows to keep going instead of stopping.

## Step 2: Main Execution Loop

For each pending phase, spawn a subagent, collect the result,
validate the gate, and advance. Every step is a tool call.

```text
PHASES = [specify, clarify, plan, checklist, tasks, analyze, implement]

for phase in PHASES starting from first_pending:
    1. TaskUpdate: set phase task to "in_progress"
    2. Read the workflow file's prompt(s) for this phase
    3. For EACH prompt in the phase:
       a. Agent(prompt: "Run /speckit.<phase> with: <prompt>")
       b. Receive subagent summary (tool result)
       c. TaskUpdate: set this prompt's task to "completed"
    4. Run consensus in main session if needed
       (Clarify/Checklist/Analyze — see below)
    5. Validate gate (see gate-validation.md)
    6. If gate fails:
       a. Attempt auto-fix (max 2 attempts)
       b. If still failing and gate-failure == "stop": STOP
       c. If gate-failure == "skip-and-log": log, continue
    7. Update workflow file with results
    8. If auto-commit == "per-phase":
       Bash: git add specs/ && git commit
    9. Advance to next phase (next iteration of loop)
```

**Dynamic task updates:** If consensus reveals new questions or
remediation adds loops, create additional tasks via TaskCreate.

### Phase Dispatch

For each phase: read the prompt, spawn a subagent, validate.

#### Subagent Prompt Construction

Use the `phase-executor` agent type for every phase:

```text
Agent(
  subagent_type: "phase-executor",
  description: "SPEC-XXX <phase>",
  prompt: """
    Run the /speckit.<phase> command.
    Use: Skill("speckit.<phase>", args: "<workflow prompt below>")

    <phase-specific prefix — see below>
    - Specify: branch-aware prefix (if ON_FEATURE_BRANCH)
    - Clarify: interactive prefix (ALWAYS for clarify)
    - All others: no prefix needed

    Workflow prompt:
    ---
    <paste the exact prompt from the workflow file>
    ---
  """
)
```

The phase-executor agent handles summary formatting and
the "no recommendations" constraint automatically. The
phase-specific prefixes handle Specify's branch skipping
and Clarify's interactive question-answering behavior.

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

#### Clarify — Interactive Prefix

The `/speckit.clarify` command is interactive — it surfaces
questions and expects YOU to answer them. Always add this
prefix to clarify subagent prompts:

```text
IMPORTANT: The clarify command will surface clarification
questions about the spec. You MUST answer every question
it asks. Do NOT respond with "done" or end the session
without answering all questions.

For each question the command surfaces:
1. Research the answer using these tools:
   - mcp__tavily-mcp__tavily-search (API docs, standards)
   - mcp__context7__resolve-library-id + get-library-docs
     (library documentation)
   - mcp__RepoPrompt__context_builder (codebase patterns)
   - mcp__RepoPrompt__file_search (find existing code)
   - Read/Grep (constitution, prior specs, CLAUDE.md)
2. Pick the best-supported answer (or use "Custom" with
   your researched answer if the offered options are wrong)
3. Provide the answer to the command

Answer ALL questions before completing. Cite your sources
in the summary you return.
```

#### Multi-Prompt Phases

Clarify and Checklist have multiple prompts. Spawn a
**separate subagent for each prompt**:

- **Clarify:** One subagent per session (e.g., "Session 1:
  Search Behavior", "Session 2: Database Operations")
- **Checklist:** One subagent per domain (e.g.,
  api-workaround, type-safety, requirements)

#### Resolution — After Each Prompt (Main Session)

After EACH subagent returns, check for markers and resolve
BEFORE spawning the next subagent.

**Resolution tools (RepoPrompt MCP):**

- `context_builder(response_type: "question")` — ask the
  question, let RepoPrompt explore the codebase and answer
- `chat_send(mode: "chat", model: "Evaluator")` — get a
  second perspective for ambiguous questions
- `manage_selection` + `chat_send(mode: "plan")` — curate
  specific file context and get targeted analysis

**Per-phase resolution:**

- **Clarify:** After each session subagent → grep spec.md
  for `[NEEDS CLARIFICATION]`. Use `context_builder` with
  `response_type: "question"` to investigate each marker.
  Check security keywords (see consensus-protocol.md).
  Apply answer to spec.md, remove marker, proceed to next
  session.
- **Checklist:** After each domain subagent → grep
  checklists for `[Gap]`. For each gap:
  1. `context_builder(response_type: "question")` —
     investigate codebase patterns for the gap
  2. `mcp__tavily-mcp__tavily-search` — search for API
     docs, standards, or best practices relevant to gap
  3. Read constitution + prior specs for precedent
  4. Determine fix (which artifact, what text, where)
  5. Apply fix, re-run domain to verify (max 2 loops)
  Proceed to next domain.
- **Analyze:** Single prompt. After subagent → parse ALL
  findings at every severity (CRITICAL, HIGH, MEDIUM, LOW).
  For EACH finding:
  1. `context_builder(response_type: "question")` —
     investigate codebase patterns for the finding
  2. `mcp__tavily-mcp__tavily-search` — search for API
     docs, standards, or best practices relevant to finding
  3. Read constitution + prior specs for precedent
  4. Determine and apply fix to tasks.md, spec.md, or
     plan.md
  Re-run analyze to verify 0 findings remain (max 2 loops).

#### Implement — Project Agent Detection

The Implement phase uses the project's own implementation
agent if one exists, falling back to phase-executor if not.

**Detection (done during Step 0 — see 0.9 below):**

```text
1. Glob(".claude/agents/*.md") to find all project agents
2. Read each agent file's description field
3. Look for keywords: "implement", "TDD", "development",
   "developer", "coding", "build"
4. If found → record agent name (e.g., "omnifocus-developer")
5. If not found → use "phase-executor" as fallback
```

**Why project agent over phase-executor:** Project agents
have domain-specific knowledge — OmniJS patterns, TDD
workflows, architecture conventions, API references — that
a generic phase-executor lacks. The project team designed
their agent for exactly this purpose.

**Execution:**

```text
If PROJECT_IMPLEMENTATION_AGENT was detected:
  Agent(
    subagent_type: "<detected agent name>",
    prompt: """
      Implement tasks from tasks.md for SPEC-XXX.
      Follow the plan in plan.md.

      MANDATORY: Use strict TDD red-green-refactor for
      EVERY task:

      1. RED — Write failing tests FIRST:
         - Contract tests for input/output schemas
         - Unit tests for business logic
         - Run tests → verify they FAIL
         - Do NOT write implementation code yet

      2. GREEN — Write MINIMUM code to pass:
         - Implement only what's needed to make tests green
         - Run tests → verify they PASS
         - Do NOT optimize or refactor yet

      3. REFACTOR — Clean up while green:
         - Improve code quality, remove duplication
         - Run tests → verify they STAY GREEN
         - Optimize only if needed

      After each task completes all 3 phases, run the full
      verification suite (build + typecheck + lint + test)
      before moving to the next task.

      <workflow implement prompt>
    """
  )

If no project agent found:
  Agent(
    subagent_type: "phase-executor",
    prompt: """
      Run /speckit.implement with the workflow prompt below.

      MANDATORY: Use strict TDD red-green-refactor for
      EVERY task:
      1. RED — Write failing tests first (contract + unit)
      2. GREEN — Write minimum code to pass tests
      3. REFACTOR — Clean up while tests stay green

      Workflow prompt:
      ---
      <workflow implement prompt>
      ---
    """
  )
```

For `[P]` tasks, spawn parallel sub-agents (using the same
detected agent type) with worktree isolation. Each parallel
agent follows the same TDD cycle independently.

## Step 3: Post-Implementation

After all 7 phases complete and G7 passes:

### 3.1 Integration / E2E Test Verification

**This step is MANDATORY before PR creation.** Execute
these tool calls in sequence:

**Step 1 — Detect:** Check if the project has integration
or e2e tests:

```text
Glob("tests/integration/**")  ← TOOL CALL
Glob("tests/e2e/**")          ← TOOL CALL
```

If BOTH return empty, skip to 3.2 PR Creation.

**Step 2 — Check for spec-specific tests:**

```text
Glob("tests/integration/*<spec-name>*")  ← TOOL CALL
```

**Step 3 — Create if missing:** If no spec-specific tests
exist, spawn the implementation agent (detected in 0.9)
to create them:

```text
Agent(
  subagent_type: PROJECT_IMPLEMENTATION_AGENT or "phase-executor",
  description: "SPEC-XXX integration tests",
  prompt: """
    Create integration tests for SPEC-XXX (<spec name>).

    1. Read existing integration tests to understand the
       pattern (test structure, setup, teardown)
    2. Create spec-specific integration tests covering
       the P1 user stories
    3. Each test should verify end-to-end behavior
    4. Follow existing test patterns exactly

    Spec: specs/<number>-<name>/spec.md
    Plan: specs/<number>-<name>/plan.md
  """
)
```

**Step 4 — Run the FULL suite:** Run ALL integration tests,
not just the new ones:

```text
Bash("pnpm test tests/integration/")  ← TOOL CALL
```

If any fail → fix and re-run (max 2 attempts). Commit
fixes before proceeding.

**Step 5 — Record results** in the workflow file:
integration tests created, total count, pass/fail.

**Why:** Existing integration tests may break due to new
tool registration, shared infrastructure changes, or side
effects. The full suite catches regressions before the PR.

### 3.2 PR Creation

```text
1. Run final verification: pnpm build && pnpm typecheck && pnpm lint && pnpm test
   (or project-equivalent commands from CLAUDE.md)
2. Detect remote: git remote -v
3. Push: git push -u <remote> <branch>
4. Create PR:
   gh pr create \
     --title "feat(SPEC-XXX): <Spec Name>" \
     --body "$(cat <<'EOF'
   ## Summary
   <Auto-generated from spec.md Summary section>

   ## Spec Artifacts
   - spec.md — Requirements and user stories
   - plan.md — Technical architecture
   - tasks.md — Implementation task breakdown

   ## Implementation
   - <N> tasks completed across <M> phases
   - <X> new tests (<Y> unit + <Z> contract + <W> integration)
   - All gates passed (G1-G7)

   ## Verification
   - [x] Build passes
   - [x] Type check passes
   - [x] Lint passes
   - [x] Tests pass (<total> tests)

   ## Test Plan
   - [ ] Review spec artifacts in specs/<number>-<name>/
   - [ ] Verify scripts in Script Editor (manual)
   - [ ] Manual verification (manual)
   EOF
   )"
5. Update workflow file with PR URL
6. Commit: "feat(SPEC-XXX): open PR for review"
```

If `gh` is not installed, push the branch and tell the user to
create the PR manually.

### 3.3 Copilot Review Remediation Loop

**This step is MANDATORY after PR creation.** Use the `/loop`
command to schedule recurring review comment monitoring.

**Execute this immediately after PR creation:**

```text
Skill("loop", args: "5m Check PR #<number> for review
  comments. For each unresolved comment:
  - If code fix needed → edit file, run pnpm build &&
    pnpm typecheck && pnpm test, commit, push
  - If style/format → pnpm lint:fix, commit, push
  - If question → reply via gh api with design rationale
  - If false positive → reply explaining why no change
  Exit when 0 unresolved comments remain.")
```

**Why `/loop`:** The loop runs every 5 minutes in the
background, checking for new review comments from GitHub
Copilot or human reviewers. It automatically expires after
3 days (Claude Code's built-in safety limit). The autopilot
doesn't need to wait — it schedules the loop and reports
completion.

**How to construct the loop prompt:**

1. Extract the PR number from the `gh pr create` output
2. Extract the repo owner/name from `git remote -v`
3. Build the loop prompt with the specific PR number and
   repo path for `gh api` calls

**After scheduling the loop, the autopilot is DONE.** Report
the final summary with PR URL and note that review
remediation is running in the background via `/loop`.

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
