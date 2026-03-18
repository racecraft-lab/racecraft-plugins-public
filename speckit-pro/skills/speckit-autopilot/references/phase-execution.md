# Phase Execution Reference

How each SDD phase's prompt is constructed and executed by the autopilot. Each phase follows a pattern: gather context → construct prompt → spawn sub-agent → validate gate → update workflow → commit.

## Context Sources

Every phase draws from some combination of these sources:

| Source | How to Gather |
|--------|--------------|
| **Workflow file** | Read the workflow file's phase-specific prompt section |
| **Master plan** | Read the master plan file for this spec's scope description |
| **CLAUDE.md** | Read CLAUDE.md for tech stack, constraints, conventions |
| **Constitution** | Read `.specify/memory/constitution.md` for project principles |
| **RepoPrompt scan** | Use `mcp__RepoPrompt__context_builder` for codebase analysis |
| **Prior specs** | Read `specs/*/spec.md` and `specs/*/plan.md` for precedent |
| **Settings** | Read `.claude/speckit-pro.local.md` for configuration |

## Branch/Worktree Detection

Before executing any phase, detect the current branch context:

```bash
# Detect current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")

# Check if in a worktree
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
GIT_COMMON=$(git rev-parse --git-common-dir 2>/dev/null)
IS_WORKTREE=$( [ "$GIT_DIR" != "$GIT_COMMON" ] && echo "true" || echo "false" )

# Set SPECIFY_FEATURE if on a feature branch
if [[ "$CURRENT_BRANCH" =~ ^[0-9]{3}- ]]; then
  export SPECIFY_FEATURE="$CURRENT_BRANCH"
fi
```

Verify the detected branch matches the workflow file's `Branch` field. If they don't match, STOP and ask the user.

## Phase-by-Phase Execution

### Phase 0: Prerequisites (Constitution Validation)

**Context sources:** Constitution + CLAUDE.md + current codebase state

**Purpose:** Validate that the codebase satisfies all constitution principles before starting the workflow. Records baselines (test count, file count) in the workflow file's Prerequisites table so the Implement phase can measure delta.

**Execution strategy:** Runs directly in the main session (no sub-agent needed).

**Procedure:**

1. Read `.specify/memory/constitution.md` — extract all numbered principles
2. For each principle, determine the verification type and run it:
   - **Automated** (`pnpm typecheck`, `pnpm test`, `pnpm build`, `pnpm lint`) — run and check exit code
   - **Structural** (definitions/primitives split, contract dirs) — use Glob to count matching files
   - **Review-only** (KISS, YAGNI, SOLID) — mark as `✅ Verified` (validated during implementation)
3. Record baseline numbers from command output (e.g., test count, file count)
4. Update the workflow file's Prerequisites → Constitution Validation table with results
5. Set the "Constitution Check" summary line

**Gate:** G0 — all automated checks must pass. If any fail, STOP immediately.

**Workflow updates:**
- Prerequisites → Constitution Validation table: principle, requirement, verification, status
- Constitution Check summary: `✅ Verified <date> — Constitution v<version>, all principles satisfied`

**Commit:** No commit for prerequisites (no code changed).

### Phase 1: Specify

**Context sources:** Master plan scope + CLAUDE.md tech stack + constitution + RepoPrompt codebase scan

**Prompt construction:**

```
Compose a detailed /speckit.specify prompt from:
1. The workflow file's "Specify Prompt" section (user-written scope description)
2. Master plan's scope section for this spec (detailed deliverables, constraints)
3. CLAUDE.md tech stack section (languages, frameworks, versions)
4. Constitution principles summary (for the agent to respect)
5. RepoPrompt context_builder output (existing code patterns, related files)
6. Prior specs' scope sections (for cross-spec consistency)
```

**Execution:** Spawn a foreground sub-agent with the composed prompt. The sub-agent runs the equivalent of `/speckit.specify` with the enriched prompt.

**Gate:** G1 — check for `[NEEDS CLARIFICATION]` markers (routing decision)

**Workflow updates:**
- Status table: `⏳ Pending` → `✅ Complete` with summary (e.g., "6 stories, 12 FRs, 8 SCs")
- Specify Results table: FR count, US count, acceptance criteria, edge cases
- Files Generated checkboxes

**Commit:** `git add specs/ && git commit -m "feat(SPEC-XXX): complete specify phase"`

### Phase 2: Clarify (Conditional)

**Trigger:** Only runs if G1 detected `[NEEDS CLARIFICATION]` markers.

**Context sources:** spec.md + constitution + master plan + codebase patterns

**Execution strategy:** This phase runs in the MAIN SESSION (not a sub-agent) because it needs to spawn consensus agents.

```
For each clarify session defined in the workflow file:
1. Identify questions/ambiguities in spec.md
2. For each question:
   a. Check for security keywords → if found, flag for human
   b. Spawn 3 consensus agents IN PARALLEL (background)
   c. Wait for all 3 to complete
   d. Apply consensus rules (see consensus-protocol.md)
   e. If consensus → integrate answer into spec.md
   f. If no consensus → flag for human review
```

**Gate:** G2 — verify 0 `[NEEDS CLARIFICATION]` and 0 `[HUMAN REVIEW NEEDED]` markers

**Workflow updates:**
- Status table updated
- Clarify Results table: session focus, questions, key outcomes

**Commit:** `git add specs/ && git commit -m "feat(SPEC-XXX): complete clarify phase"`

### Phase 3: Plan

**Context sources:** spec.md + CLAUDE.md tech stack + constitution + prior specs' plans

**Prompt construction:**

```
Compose a /speckit.plan prompt from:
1. The workflow file's "Plan Prompt" section (tech stack, constraints)
2. CLAUDE.md tech stack section (auto-injected so user doesn't have to repeat it)
3. Constitution principles (for gate checking)
4. Prior specs' plan.md files (for architectural consistency)
5. RepoPrompt codebase scan (existing architecture patterns)
```

**Execution:** Spawn a foreground sub-agent with the composed prompt.

**Gate:** G3 — verify plan.md, research.md, data-model.md exist; check constitutional gates

**Workflow updates:**
- Status table updated
- Plan Results table: artifact status for each generated file

**Commit:** `git add specs/ && git commit -m "feat(SPEC-XXX): complete plan phase"`

### Phase 4: Checklist

**Context sources:** spec.md + plan.md + signal extraction from checklist-domains-guide

**Execution strategy:** This phase runs in the MAIN SESSION because it may need consensus agents for gap remediation.

```
Step 1: Read ALL checklist prompts from the workflow file
Step 2: For each domain prompt, spawn a sub-agent to run /speckit.checklist
Step 3: Collect results, parse [Gap] markers across all checklists
Step 4: If gaps found → run Checklist Remediation Loop (see gate-validation.md)
Step 5: Re-run checklists to verify gaps closed
```

**Gate:** G4 — verify 0 `[Gap]` markers across all checklist files

**Workflow updates:**
- Status table updated
- Checklist Results table: per-domain items count, gaps count, spec references
- Addressing Gaps section if gaps were remediated

**Commit:** `git add specs/ && git commit -m "feat(SPEC-XXX): complete checklist phase"`

### Phase 5: Tasks

**Context sources:** spec.md + plan.md + CLAUDE.md file layout + prior specs' task patterns

**Prompt construction:**

```
Compose a /speckit.tasks prompt from:
1. The workflow file's "Tasks Prompt" section (task structure constraints)
2. CLAUDE.md file layout conventions (where tests go, where source goes)
3. Prior specs' tasks.md files (for consistent task structure)
4. Project directory structure (via ls or RepoPrompt get_file_tree)
```

**Execution:** Spawn a foreground sub-agent with the composed prompt.

**Gate:** G5 — cross-reference every FR-XXX in spec.md with tasks.md

**Workflow updates:**
- Status table updated
- Tasks Results table: total tasks, phases, parallel opportunities, user stories covered

**Commit:** `git add specs/ && git commit -m "feat(SPEC-XXX): complete tasks phase"`

### Phase 6: Analyze

**Context sources:** spec.md + plan.md + tasks.md + constitution

**Execution strategy:** This phase runs in the MAIN SESSION because it may need consensus agents for finding remediation.

```
Step 1: Spawn sub-agent to run /speckit.analyze
Step 2: Parse findings by severity
Step 3: If CRITICAL or HIGH findings → run Analyze Remediation Loop (see gate-validation.md)
Step 4: Re-run analyze to verify findings resolved
```

**Gate:** G6 — verify 0 CRITICAL findings

**Workflow updates:**
- Status table updated
- Analysis Results table: ID, severity, issue, resolution per finding
- Constitution alignment notes
- FR coverage notes

**Commit:** `git add specs/ && git commit -m "feat(SPEC-XXX): complete analyze phase"`

### Phase 7: Implement

**Context sources:** tasks.md + plan.md + CLAUDE.md + all prior artifacts

**Execution strategy:**

```
Step 1: Read tasks.md and identify phases
Step 2: For each phase:
  a. Identify tasks in this phase
  b. For tasks marked [P] → spawn background sub-agents (one per task)
     - If worktree isolation is available, use isolation: "worktree"
  c. For sequential tasks → spawn one foreground sub-agent at a time
  d. If the project has a specialized implementation agent (e.g., omnifocus-developer),
     delegate to that agent instead
Step 3: After each implementation phase, commit:
     git add . && git commit -m "feat(SPEC-XXX): implement phase N - <description>"
Step 4: After all tasks complete → run G7 verification suite
```

**Gate:** G7 — full verification suite (build + typecheck + lint + test)

**Workflow updates:**
- Status table updated
- Implementation Progress table: per-phase tasks, completed, notes
- Post-Implementation Checklist: lint, typecheck, test, build results
- Success Criteria checkboxes

**After G7 passes:** Execute PR Creation Protocol (see below).

## PR Creation Protocol

After G7 passes:

```
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

The PR body is auto-generated from:
- spec.md Summary section
- Implementation results from the workflow file
- Verification results (test counts, build status)
- Test plan checklist

## Copilot Review Remediation Loop

After PR creation, monitor for review comments:

```
Poll every 5 minutes (max 1 hour / 12 iterations):
1. Check for pending review comments via gh api
2. Filter to unresolved comments
3. For each unresolved comment:
   a. Read comment body + file context
   b. Determine action (code fix, style fix, reply, false positive)
   c. If code changed → verify suite → commit → push
   d. Reply to comment thread
4. If no unresolved comments → exit loop
5. After 1 hour → exit, notify user of remaining comments
```

## Sub-Agent Prompt Template

When spawning a sub-agent for a phase, use this prompt structure:

```
You are executing phase [N] ([Phase Name]) of the SpecKit SDD workflow for [SPEC-ID]: [Spec Name].

## Context
[Gathered context from the sources listed above]

## Your Task
[Phase-specific instructions — what to produce, what format, what constraints]

## Constraints
- Follow the existing project patterns documented in CLAUDE.md
- Respect constitution principles
- Output artifacts to specs/<feature-name>/
- Return a summary of what was produced when complete

## Output
When complete, return:
1. List of files created or modified
2. Summary of key decisions made
3. Any concerns or flags for human review
```

## Workflow File Update Protocol

After each phase completes, update the workflow file with:

1. **Status table**: Change phase status from `⏳ Pending` to `✅ Complete` with summary notes
2. **Phase-specific results table**: Fill in metrics and outcomes
3. **Files Generated checkboxes**: Check off produced artifacts
4. **Consensus Resolution Log** (if applicable): Record consensus decisions

The workflow file serves as both checklist and execution log — the complete auditable record of the autonomous execution.
