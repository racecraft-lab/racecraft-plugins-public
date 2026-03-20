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

### 2. Use phase-specific executor agents

Each phase type has its own specialized executor agent:

| Phase | Agent | Why specialized |
| ----- | ----- | --------------- |
| Specify, Plan, Tasks | `phase-executor` | Simple: run command, return summary |
| Clarify | `clarify-executor` | Interactive: must research and answer questions |
| Checklist | `checklist-executor` | Must run checklist AND remediate gaps with research |
| Analyze | `analyze-executor` | Must run analysis AND remediate ALL findings with research |
| Implement | `implement-executor` | Enforces strict TDD red-green-refactor + mandatory integration tests |

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
  2. Agent(subagent_type: "clarify-executor",
          prompt: "<interactive prefix> + <session 1 prompt>")
     The clarify-executor researches and answers all questions
  3. Grep spec.md for [NEEDS CLARIFICATION] markers
  4. If markers remain → use context_builder to resolve
  5. TaskUpdate: "Clarify - Session 1" → completed
  6. TaskUpdate: "Clarify - Session 2" → in_progress
  7. Agent(subagent_type: "clarify-executor",
          prompt: "<interactive prefix> + <session 2 prompt>")
  8. Grep spec.md for [NEEDS CLARIFICATION] markers
  9. If markers remain → use context_builder to resolve
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
`clarify-executor` agent is purpose-built for this — it
researches each question using Tavily, Context7, RepoPrompt,
and codebase search, then provides evidence-grounded answers.

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

1. **Executor (first pass):** The clarify-executor researches
   and answers questions using Tavily (API docs), Context7
   (library docs), RepoPrompt (codebase patterns), and
   Read/Grep (constitution, prior specs). This handles most
   questions. Items it can't resolve with high confidence are
   flagged in its "Unresolved for consensus" summary section.
2. **Main session + consensus agents (second pass):** For
   each unresolved item, spawn 3 consensus agents IN PARALLEL
   (codebase-analyst, spec-context-analyst,
   domain-researcher). Apply consensus rules: 2/3 agree →
   use majority, all disagree → flag for human. Security-
   keyword questions ALWAYS go to consensus regardless of
   what the executor answered.

### 6. Two-layer resolution with consensus agents

After EACH executor subagent returns for a consensus phase
(Clarify, Checklist, Analyze), run a two-layer resolution
process BEFORE spawning the next subagent.

**Layer 1 — Executor does direct research:** The executor
agent (clarify-executor, checklist-executor,
analyze-executor) researches using Tavily, Context7,
RepoPrompt, and codebase search. It resolves most items
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

**Why two layers:** Most items are straightforward — the
executor handles ~80% directly. Consensus provides distinct
perspectives (codebase patterns vs. project decisions vs.
best practices) for genuinely ambiguous items.

**Why after each prompt:** Session 2 may depend on Session
1's resolved questions. Checklist Domain 2 may depend on
Domain 1's gap fixes.

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
   | Type safety | Run TYPECHECK command (from Step 0.10) |
   | Test suite | Run UNIT_TEST + INTEGRATION_TEST commands — record count as baseline |
   | Build discipline | Run BUILD command |
   | Lint/format | Run LINT command |
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
| I. Type-First Development | All functions typed, Zod contracts | TYPECHECK command | ✅ Pass |
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

### 0.10 Project Command Discovery

Discover how this project builds, lints, typechecks, and
tests. This makes the plugin work with ANY tech stack —
not just Node.js/pnpm projects.

**Discovery order (first match wins for each command):**

1. **CLAUDE.md** — Look for a "Build Commands" table or
   similar section listing project commands. This is the
   most authoritative source.
2. **package.json** (Node.js) — Parse `scripts` for
   `build`, `test`, `lint`, `typecheck`, `test:integration`,
   `test:e2e` keys. Detect package manager from lockfile:
   `pnpm-lock.yaml` → pnpm, `yarn.lock` → yarn,
   `package-lock.json` → npm, `bun.lockb` → bun.
3. **Makefile** — Look for `build`, `test`, `lint`,
   `integration` targets
4. **pyproject.toml / setup.cfg** (Python) — Look for
   pytest config, ruff/flake8 config, mypy config
5. **Cargo.toml** (Rust) — `cargo build`, `cargo test`,
   `cargo clippy`
6. **go.mod** (Go) — `go build`, `go test`, `go vet`,
   `golangci-lint`

**Record these commands:**

```text
PROJECT_COMMANDS:
  BUILD:              <e.g., pnpm build, cargo build, go build>
  TYPECHECK:          <e.g., pnpm typecheck, mypy ., tsc --noEmit>
  LINT:               <e.g., pnpm lint, ruff check, cargo clippy>
  LINT_FIX:           <e.g., pnpm lint:fix, ruff check --fix>
  UNIT_TEST:          <e.g., pnpm test, pytest, cargo test, go test ./...>
  INTEGRATION_TEST:   <e.g., pnpm test:integration, pytest tests/integration>
  SINGLE_FILE_TEST:   <e.g., pnpm test <file>, pytest <file>, go test <file>>
  SINGLE_FILE_INTEGRATION: <e.g., pnpm test:integration:file <file>>
  FULL_VERIFY:        <BUILD && TYPECHECK && LINT && UNIT_TEST && INTEGRATION_TEST>
```

**If a command type is not found** (e.g., no typecheck for
a Python project without mypy), set it to `"N/A"` — it
will be skipped during verification.

**If integration tests use a separate config** (e.g.,
`vitest.integration.config.ts`), the default test command
may EXCLUDE them. Discover both commands and record them
separately.

**Record in the workflow file** under the Prerequisites
section so the commands persist across context compactions.
Pass these commands to every subagent prompt that needs
to run builds or tests.

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
  - "Phase 2: Clarify - Session 1 Consensus"
  - "Phase 2: Clarify - Session 2: Database Operations"
  - "Phase 2: Clarify - Session 2 Consensus"
  - "Phase 3: Plan"
  - "Phase 4: Checklist - Domain 1: api-workaround"
  - "Phase 4: Checklist - Domain 1 Consensus"
  - "Phase 4: Checklist - Domain 2: type-safety"
  - "Phase 4: Checklist - Domain 2 Consensus"
  - "Phase 4: Checklist - Domain 3: requirements"
  - "Phase 4: Checklist - Domain 3 Consensus"
  - "Phase 5: Tasks"
  - "Phase 6: Analyze"
  - "Phase 6: Analyze - Consensus"
  - "Phase 7: Implement"
  - "Post: Full Integration/E2E Suite Verification"
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
    4. Run consensus in main session if needed:
       Parse executor's "Unresolved for consensus" section.
       For each item → spawn 3 consensus agents in parallel
       (codebase-analyst, spec-context-analyst, domain-researcher)
       → apply consensus rules → edit artifacts
    5. Validate gate (see gate-validation.md)
    6. If gate fails:
       a. Attempt auto-fix (max 2 attempts)
       b. If still failing and gate-failure == "stop": STOP
       c. If gate-failure == "skip-and-log": log, continue
    7. Update workflow file with results
    8. If auto-commit == "per-phase":
       Bash: git add specs/ && git commit
    9. Advance to next phase (next iteration of loop)

POST-IMPLEMENTATION (after all 7 phases complete):
    These are tasks in your task list — execute them in order:

    10. TaskUpdate: "Post: Full Integration/E2E Suite Verification" → in_progress
        Execute Step 3.1 (detect, create, run full suite)
        TaskUpdate: → completed

    11. TaskUpdate: "Post: PR Creation" → in_progress
        Execute Step 3.2 (verify, push, gh pr create)
        TaskUpdate: → completed

    12. TaskUpdate: "Post: PR Review Remediation Loop" → in_progress
        Execute Step 3.3 (Skill("loop", args: "5m ..."))
        TaskUpdate: → completed
        THIS IS THE FINAL STEP — autopilot is done.
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
| Implement | `implement-executor` | Project agent context (if detected in 0.9) |

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

#### Implement — TDD Enforcement via implement-executor

The Implement phase ALWAYS uses the `implement-executor`
agent. This agent has TDD red-green-refactor as
`<hard_constraints>` — tests are written and verified
FAILING before any implementation code. This is
NON-NEGOTIABLE.

**If a project implementation agent was detected (Step 0.9),**
include its domain-specific context in the prompt so the
implement-executor knows the project's patterns (OmniJS,
definitions/primitives split, etc.). The project agent's
patterns govern WHAT gets built; the implement-executor's
TDD constraints govern HOW it gets built.

**Execution:**

```text
Agent(
  subagent_type: "implement-executor",
  description: "SPEC-XXX implement",
  prompt: """
    Implement tasks from tasks.md for SPEC-XXX.
    Follow the plan in plan.md.

    PROJECT_COMMANDS (from Step 0.10):
      BUILD: <discovered build command>
      TYPECHECK: <discovered typecheck command>
      LINT: <discovered lint command>
      LINT_FIX: <discovered lint fix command>
      UNIT_TEST: <discovered unit test command>
      INTEGRATION_TEST: <discovered integration test command>
      SINGLE_FILE_TEST: <discovered single file test command>
      SINGLE_FILE_INTEGRATION: <discovered single file integration command>

    <if PROJECT_IMPLEMENTATION_AGENT was detected>
    PROJECT CONTEXT: This project uses the
    "<detected agent name>" patterns. Read its agent
    definition at .claude/agents/<agent>.md for
    domain-specific conventions (architecture, file
    layout, naming, API patterns). Follow those
    patterns for WHAT you build.
    </if>

    Integration tests are MANDATORY — create spec-specific
    integration tests alongside unit and contract tests.

    Workflow prompt:
    ---
    <workflow implement prompt>
    ---
  """
)
```

The implement-executor agent enforces:
- RED: Write tests first, verify they FAIL
- GREEN: Write minimum code, verify tests PASS
- REFACTOR: Clean up, verify tests STAY GREEN
- Integration tests created for every spec
- Full verification suite after each task phase

For `[P]` tasks, spawn parallel implement-executor agents
with worktree isolation. Each parallel agent follows the
same TDD cycle independently.

## Step 3: Post-Implementation

After all 7 phases complete and G7 passes:

### 3.1 Full Integration / E2E Suite Verification

Integration tests for the spec are created DURING the
Implement phase (the implement-executor agent creates them
as part of TDD). This step runs the FULL suite to catch
regressions from other specs.

**Step 1 — Verify spec-specific tests exist:**

```text
Glob("tests/integration/*<spec-name>*")  ← TOOL CALL
Glob("tests/e2e/*<spec-name>*")          ← TOOL CALL
```

If no spec-specific tests exist, the implement-executor
failed to create them. Spawn it again to fix:

```text
Agent(
  subagent_type: "implement-executor",
  description: "SPEC-XXX missing integration tests",
  prompt: """
    The implementation phase did not create integration
    tests for SPEC-XXX. This is NON-NEGOTIABLE.

    1. Read existing integration tests to understand the
       pattern (test structure, setup, teardown)
    2. Create spec-specific integration tests covering
       the P1 user stories from spec.md
    3. Follow TDD: write tests → verify FAIL → write
       implementation stubs if needed → verify PASS

    Spec: specs/<number>-<name>/spec.md
    Plan: specs/<number>-<name>/plan.md
  """
)
```

**Step 2 — Run the FULL suite:** Run ALL integration tests,
not just the new ones:

```text
Bash("<INTEGRATION_TEST command>")     ← TOOL CALL
```

If any fail → fix and re-run (max 2 attempts). Commit
fixes before proceeding.

**Step 3 — Record results** in the workflow file:
integration test count, pass/fail, regressions found.

**Why:** Existing integration tests may break due to new
tool registration, shared infrastructure changes, or side
effects. The full suite catches regressions before the PR.

### 3.2 PR Creation

```text
1. Run final verification (BOTH test suites):
   <BUILD> && <TYPECHECK> && <LINT> && <UNIT_TEST> && <INTEGRATION_TEST>
   (use PROJECT_COMMANDS discovered in Step 0.10)
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

**Before invoking `/loop`, extract these values:**

```text
PR_NUMBER = <from gh pr create output>       ← TOOL CALL
REPO = <owner/name from git remote -v>       ← TOOL CALL
BRANCH = <current branch name>               ← TOOL CALL
```

**Execute this immediately after PR creation:**

```text
Skill("loop", args: "5m
  Check PR #<PR_NUMBER> in <REPO> for unresolved review
  comments and resolve them.

  Step 1 — Fetch comments:
  Bash('gh api repos/<REPO>/pulls/<PR_NUMBER>/reviews
    --jq \".[] | select(.state == \\\"CHANGES_REQUESTED\\\"
    or .state == \\\"COMMENTED\\\") | {id, state, body}\"')

  Bash('gh api repos/<REPO>/pulls/<PR_NUMBER>/comments
    --jq \".[] | select(.in_reply_to_id == null) | {id,
    path, line, body, created_at}\"')

  Step 2 — If 0 unresolved comments, report 'No unresolved
  comments on PR #<PR_NUMBER>' and stop.

  Step 3 — For each unresolved comment:
  a. Read the comment body and the file it references
  b. If code fix needed:
     - Edit the file
     - Bash('<BUILD> && <TYPECHECK> && <UNIT_TEST> && <INTEGRATION_TEST>')
     - Bash('git add <file> && git commit -m
       \"fix(SPEC-XXX): address review - <summary>\"')
     - Bash('git push')
     - Reply: Bash('gh api
       repos/<REPO>/pulls/<PR_NUMBER>/comments
       -f body=\"Fixed in $(git rev-parse --short HEAD).
       <explanation>\"
       -f in_reply_to=<comment_id>')
     - Resolve: Bash('gh api graphql -f query=\"mutation {
       minimizeComment(input:{subjectId:\\\"<comment_node_id>\\\",
       classifier:RESOLVED}) { minimizedComment { isMinimized }
       }}\"')
  c. If style/format:
     - Bash('<LINT_FIX>')
     - Commit, push, reply, resolve
  d. If question or false positive:
     - Reply with explanation via gh api, then resolve

  Step 4 — After addressing all comments, report summary.
")
```

**Why `/loop`:** The loop runs every 5 minutes in the
background, checking for new review comments from GitHub
Copilot or human reviewers. It automatically expires after
3 days (Claude Code's built-in safety limit). The autopilot
doesn't need to wait — it schedules the loop and reports
completion.

**Critical:** The loop prompt must be **self-contained** —
each cron fire runs in a fresh context with no memory of
prior iterations. All values (PR number, repo, branch) must
be hardcoded in the prompt, not referenced as variables.

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
