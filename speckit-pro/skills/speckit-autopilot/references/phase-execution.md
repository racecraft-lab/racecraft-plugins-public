# Phase Execution Reference

**RULES (from SKILL.md — repeated here for clarity):**

1. **SUBAGENT PER PHASE** — Spawn a foreground subagent for
   each phase via the Agent tool. The subagent runs the
   `/speckit.*` command and returns a summary. The parent
   receives the result as a tool response, keeping the agent
   loop alive.
2. **MULTI-PROMPT** — Clarify and Checklist have multiple
   prompts. Spawn a separate subagent for each prompt.
3. **RESOLUTION IN MAIN SESSION** — After subagents return,
   the main session checks for markers and resolves them
   using RepoPrompt `context_builder` and `chat_send`.
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
2. Run automated checks (`pnpm typecheck`, `pnpm test`,
   `pnpm build`, `pnpm lint`)
3. Verify structural patterns (e.g., definitions/primitives
   split)
4. Record baselines in the workflow file's Prerequisites
   table
5. Set the "Constitution Check" summary line

**Gate:** G0 — all automated checks must pass. If any
fail, STOP.

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
Each subagent gets the **interactive prefix** telling it
to research and answer every question the command surfaces.

```text
For each clarify session in the workflow file:
  1. TaskUpdate: session task → in_progress
  2. Agent(subagent_type: "phase-executor",
          prompt: """
            <interactive prefix — see SKILL.md Clarify prefix>

            Run /speckit.clarify with: <session prompt>
          """)
  3. Grep spec.md for [NEEDS CLARIFICATION] markers
  4. If markers remain → use context_builder(response_type:
     "question") to investigate and resolve each marker
  5. TaskUpdate: session task → completed
  6. Proceed to next session
```

**The interactive prefix tells the subagent:** research
each question using Tavily (API docs), Context7 (library
docs), RepoPrompt (codebase patterns), and Read/Grep
(constitution, prior specs). Pick the best-supported answer
for each question. Answer ALL questions before completing.

**Why after each session:** Session 2 may depend on
Session 1's resolved questions. Resolution updates the
spec before the next session runs.

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
with gap remediation **after each domain**:

```text
For each checklist domain in the workflow file:
  1. TaskUpdate: domain task → in_progress
  2. Agent(subagent_type: "phase-executor",
          prompt: "Run /speckit.checklist with: <domain prompt>")
  3. Grep checklists for [Gap] markers
  4. For each gap:
     a. context_builder(response_type: "question") —
        investigate codebase patterns
     b. Tavily search — API docs, standards, best practices
     c. Read constitution + prior specs for precedent
     d. Determine and apply fix to spec.md or plan.md
  5. Re-run domain checklist to verify (max 2 loops)
  6. TaskUpdate: domain task → completed
  7. Proceed to next domain
```

**Why after each domain:** Domain 2 may depend on Domain
1's gap fixes. Remediation updates the spec/plan before
the next domain runs.

**Gate:** G4 — verify 0 `[Gap]` markers

**Commit:**
`git add specs/ && git commit -m "feat(SPEC-XXX): complete checklist phase"`

### Phase 5: Tasks

Read the workflow file's `### Tasks Prompt` section.
Spawn a subagent.

**Gate:** G5 — cross-reference every FR in spec.md with
tasks.md

**Commit:**
`git add specs/ && git commit -m "feat(SPEC-XXX): complete tasks phase"`

### Phase 6: Analyze

Read the workflow file's `### Analyze Prompt` section.
Spawn a subagent.

**Post-execution (main session):** Parse ALL findings at
every severity level (CRITICAL, HIGH, MEDIUM, LOW). For
EACH finding:

1. `context_builder(response_type: "question")` —
   investigate codebase patterns for the finding
2. `mcp__tavily-mcp__tavily-search` — search for API
   docs, standards, or best practices relevant to finding
3. Read constitution + prior specs for precedent
4. Determine and apply fix to tasks.md, spec.md, or plan.md

Re-run analyze to verify 0 findings remain (max 2 loops).
If 0 findings from the start, advance immediately.

**Gate:** G6 — verify 0 CRITICAL findings

**Commit:**
`git add specs/ && git commit -m "feat(SPEC-XXX): complete analyze phase"`

### Phase 7: Implement

Read the workflow file's `### Implement Prompt` section.

Use the implementation agent detected in Step 0.9:

```text
If PROJECT_IMPLEMENTATION_AGENT was detected:
  Agent(
    subagent_type: "<detected agent name>",
    prompt: "Implement tasks from tasks.md for SPEC-XXX.
            Follow the plan in plan.md. Use TDD.
            <workflow implement prompt>"
  )

If no project agent found (fallback):
  Agent(
    subagent_type: "phase-executor",
    prompt: "Run /speckit.implement with: <workflow prompt>"
  )
```

**Why:** Project agents have domain-specific knowledge
(OmniJS patterns, TDD workflows, architecture conventions)
that a generic phase-executor lacks. The autopilot detects
the right agent at startup (Step 0.9) by scanning
`.claude/agents/` for implementation keywords.

For `[P]` tasks, spawn parallel sub-agents (same agent
type) with worktree isolation.

**Gate:** G7 — full verification suite
(build + typecheck + lint + test)

**Commit:**
`git add . && git commit -m "feat(SPEC-XXX): implement phase N"`

**After G7 passes:** Run Integration/E2E Test Verification,
then execute PR Creation Protocol (see below).

## Integration / E2E Test Verification

Before creating a PR, check whether the project has
integration or e2e tests. If it does, implement spec-specific
tests and run the **full** integration/e2e suite.

1. Detect: `Glob("tests/integration/**" or "tests/e2e/**")`
2. If project has integration tests:
   a. Check for spec-specific tests
   b. If missing → create them following existing patterns
   c. Run the FULL integration suite (not just new tests)
   d. Fix failures (max 2 attempts)
3. If no integration tests in the project → skip

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

After PR creation, monitor for review comments:

```text
Poll every 5 minutes (max 1 hour / 12 iterations):
1. Check for pending review comments via gh api
2. Filter to unresolved comments
3. For each:
   - Code fix needed → edit file, run verify suite, commit, push
   - Style/format → pnpm lint:fix, commit, push
   - Question → reply with design rationale
   - False positive → reply explaining why no change needed
4. If 0 unresolved → exit loop
5. After 1 hour → exit, notify user of remaining comments
```

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
