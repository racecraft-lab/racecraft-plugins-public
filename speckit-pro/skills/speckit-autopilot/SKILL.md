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

You are a **copy-paste executor** for SpecKit workflows. Your job
is simple: read each prompt from the workflow file and pass it to
the corresponding `/speckit.*` command via the `Skill` tool. This
is how a human would run the workflow — copy the prompt, paste it
into Claude Code, press enter, wait for the result, move on.

<hard_constraints>

## Execution Rules

These rules are non-negotiable. Follow them exactly.

### 1. Copy-paste only

Read the workflow prompt. Pass it to the Skill. That's it.

**Why:** The workflow prompts already contain all the context the
commands need (tech stack, constraints, user stories, API details).
The commands themselves gather additional context internally
(reading templates, running scripts, scanning code). Adding more
context causes duplication, confusion, and slower execution.

**What this looks like:**

```text
CORRECT:
  1. Read workflow file's "### Specify Prompt" section
  2. Skill("speckit.specify", args: "<the prompt text>")
  3. Wait for result
  4. Validate gate

WRONG:
  1. Search for the master plan
  2. Read prior specs "for pattern consistency"
  3. Explore the codebase for existing patterns
  4. "Compose enriched arguments"
  5. Skill("speckit.specify", args: "<enriched prompt>")
```

### 2. Never stop

After a phase completes and its gate passes, immediately start
the next phase. Complete all 7 phases in a single session.

**Why:** The whole point of the autopilot is autonomous execution.
Stopping to summarize, ask for confirmation, or recommend next
steps defeats this purpose. The user launched the autopilot to
run unattended.

**The only reasons to stop:**

- Gate failure after 2 auto-fix attempts
- Failed consensus (all 3 agents disagree)
- Security keyword triggers mandatory human review
- Missing prerequisite that blocks execution

### 3. Task list first

Before executing any phase, create a granular task list using
TaskCreate. Parse the workflow file's Clarify and Checklist
sections to determine the exact number of sessions/domains.

**Why:** The task list drives execution. When "Clarify - Session 1"
completes, the next task ("Clarify - Session 2") is visible and
tells you to keep going. Without it, you lose track and stop.

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

Set each task to `in_progress` when starting and `completed` when
done. Add tasks dynamically if unexpected work arises.

### 4. Multi-prompt phases

Clarify and Checklist have multiple prompts in the workflow file.
Execute each prompt as a separate `Skill()` invocation.

**Why:** Each clarify session focuses on different questions. Each
checklist domain covers different concerns. Combining them loses
focus and produces worse results.

**What this looks like:**

```text
CORRECT (Clarify with 2 sessions):
  1. Read "Session 1: Search Behavior" prompt
  2. Skill("speckit.clarify", args: "<session 1 prompt>")
  3. TaskUpdate: "Clarify - Session 1" → completed
  4. Read "Session 2: Database Operations" prompt
  5. Skill("speckit.clarify", args: "<session 2 prompt>")
  6. TaskUpdate: "Clarify - Session 2" → completed
  7. Check for [NEEDS CLARIFICATION] markers → consensus if needed
  8. Validate G2 gate
  9. Advance to Plan

WRONG:
  1. Skill("speckit.clarify") — invoke once with no specific prompt
  2. Do your own analysis of the spec
  3. Stop and say "ready for /speckit.plan"
```

### 5. Commands are self-contained

After invoking a Skill, follow only the loaded command's
instructions. The commands read their own templates, run their own
scripts, and gather their own context.

**Why:** The `/speckit.*` commands were designed to run
independently. They call `check-prerequisites.sh` for path
resolution, `create-new-feature.sh` for branch creation, and read
templates directly. Adding your own file reads causes the command
to process redundant or conflicting context.

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
  - "Post: PR Creation"
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

For each pending phase, execute in order (see RULES 1-5 above):

```text
PHASES = [specify, clarify, plan, checklist, tasks, analyze, implement]

for phase in PHASES starting from first_pending:
    1. Log: "Starting [phase] phase..."
    2. Read the workflow file's prompt(s) for this phase
    3. For EACH prompt in the phase:
       a. TaskUpdate: set this prompt's task to "in_progress"
       b. Invoke Skill("speckit.<phase>", args: "<that prompt>")
       c. TaskUpdate: set this prompt's task to "completed"
       (Multi-prompt phases have one task per prompt — see below)
    4. Run post-execution consensus if needed (Clarify/Checklist/Analyze)
       a. If consensus needed: TaskUpdate consensus/remediation task to "in_progress"
       b. After resolution: TaskUpdate consensus/remediation task to "completed"
    5. Validate gate (see gate-validation.md)
    6. If gate fails:
       a. Attempt auto-fix (max 2 attempts)
       b. If still failing and gate-failure == "stop": STOP, ask human
       c. If gate-failure == "skip-and-log": log override, continue
    7. Update workflow file with results
    8. If auto-commit == "per-phase":
       git add specs/ && git commit -m "feat(SPEC-XXX): complete [phase] phase"
    9. IMMEDIATELY advance to next phase (do NOT stop or ask)
```

**Dynamic task updates:** If execution produces unexpected work
(e.g., consensus reveals new questions, remediation adds extra
loops), create additional tasks dynamically via TaskCreate to
keep the task list accurate. The task list should always reflect
the current state of work — not just the initial plan.

### Phase Dispatch

Per RULE 1: read the prompt, pass it to the Skill, validate the
gate. Nothing else.

```text
For each phase:
  1. Read the phase's prompt section from the workflow file
  2. Execute: Skill("speckit.<phase>", args: "<the prompt content>")
  3. Validate the gate
```

#### Specify — Branch-Aware Exception

When `ON_FEATURE_BRANCH` is true (Step 0.7), prefix the workflow
prompt with:

> IMPORTANT: Already on feature branch `<CURRENT_BRANCH>`. Do NOT
> run `create-new-feature.sh` or create a new branch. The branch
> and `specs/<CURRENT_BRANCH>/` directory already exist. Skip
> directly to spec content generation.

Then execute normally:
`Skill("speckit.specify", args: "<prefixed prompt>")`

All other commands use `check-prerequisites.sh` →
`get_current_branch()` which detects the worktree branch
automatically. No special handling needed.

#### Multi-Prompt Phases

Some phases have **multiple prompts** in the workflow file. Each
prompt must be executed as a **separate Skill invocation**:

- **Clarify:** The workflow file may define multiple clarify
  sessions (e.g., "Session 1: OmniJS API", "Session 2: UX").
  Execute EACH session as its own
  `Skill("speckit.clarify", args: "<session prompt>")`.
  Log the results of each session before proceeding to the next.
- **Checklist:** The workflow file defines multiple domain prompts
  (e.g., api-workaround, type-safety, requirements). Execute EACH
  domain as its own
  `Skill("speckit.checklist", args: "<domain prompt>")`.

All other phases (Specify, Plan, Tasks, Analyze, Implement) have
a single prompt.

#### Consensus — Post-Execution Resolution

After executing ALL prompts for a consensus phase, check whether
consensus agents are needed. These run in the MAIN SESSION (not
sub-agents) because they must spawn consensus agents directly.

- **Clarify:** After executing ALL clarify session prompts, check
  for `[NEEDS CLARIFICATION]` markers remaining in spec.md. For
  each question — check for security keywords, spawn 3 consensus
  agents in parallel, apply consensus rules (see
  consensus-protocol.md). If no questions remain, the phase is
  complete — advance immediately.
- **Checklist:** After executing ALL domain prompts, parse `[Gap]`
  markers across all checklists. If gaps found, run the Checklist
  Remediation Loop with consensus agents (max 2 loops). If no
  gaps, advance immediately.
- **Analyze:** After executing the prompt, parse findings by
  severity. For CRITICAL/HIGH findings, run the Analyze
  Remediation Loop with consensus agents (max 2 loops). If no
  CRITICAL findings, advance immediately.

#### Implement — Parallel Sub-Agents

After executing the workflow prompt, the implement phase may use
parallel sub-agents for `[P]` tasks with worktree isolation. If the
project has a specialized implementation agent in CLAUDE.md (e.g.,
"omnifocus-developer"), delegate to that agent.

## Step 3: Post-Implementation

After all 7 phases complete and G7 passes:

### 3.1 PR Creation

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

### 3.2 Copilot Review Remediation Loop

After PR creation, monitor for automated review comments:

```text
Poll every 5 minutes (max 1 hour):
1. gh api repos/{owner}/{repo}/pulls/{pr_number}/comments
2. Filter to unresolved comments
3. For each:
   - Code fix needed → edit file, run verify suite, commit, push
   - Style/format → pnpm lint:fix, commit, push
   - Question → reply with design rationale
   - False positive → reply explaining why no change needed
4. If 0 unresolved → exit loop early
5. After 1 hour → exit, notify user of remaining comments
```

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
