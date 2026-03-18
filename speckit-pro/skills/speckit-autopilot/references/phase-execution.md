# Phase Execution Reference

**RULES (from SKILL.md — repeated here for clarity):**

1. **COPY-PASTE ONLY** — Read the workflow prompt, pass it to
   `Skill("speckit.<phase>")`. Do NOT read the master plan,
   prior specs, or explore the codebase.
2. **NEVER STOP** — After a phase completes, immediately
   advance. Only stop for gate failure, failed consensus,
   security keywords, or missing prerequisites.
3. **MULTI-PROMPT** — Clarify and Checklist have multiple
   prompts. Execute EACH as a separate `Skill()` invocation.
4. **COMMANDS ARE SELF-CONTAINED** — After invoking a Skill,
   follow only the command's instructions. Do not supplement.

---

How each SDD phase is executed by the autopilot. Each phase
**invokes the real `/speckit.*` command** via the `Skill` tool,
passing the **workflow file's prompt directly** as the command
argument. The workflow prompts are pre-populated by the user
with all necessary context — the autopilot does not enrich or
supplement them. The commands handle their own infrastructure
(branch creation, template copying, prerequisite validation)
via `.specify/scripts/bash/`.

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

## Prompt Passthrough

Read the workflow prompt. Pass it to the Skill. Wait. That's
it. (See Rules 1 and 5 above for the full rationale.)

The commands handle their own context gathering internally:

- `/speckit.specify` reads the spec template
- `/speckit.plan` reads spec.md, constitution, runs research
- `/speckit.checklist` reads spec.md + plan.md + available
  design docs
- `/speckit.implement` reads tasks.md + plan.md + all
  design docs

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

When `ON_FEATURE_BRANCH` is true, the Specify phase prefixes
the workflow prompt with a "skip branch creation" instruction
(see Phase 1 below). Do NOT use `export SPECIFY_FEATURE` —
env vars do not persist across Skill tool invocations.

Verify the detected branch matches the workflow file's
`Branch` field. If they don't match, STOP and ask the user.

## Phase-by-Phase Execution

The workflow file contains a prompt for each phase. Each
prompt is a complete, self-contained instruction that starts
with the `/speckit.*` command to run. The autopilot reads
each prompt and executes it — the same way a human would
copy-paste the prompt into Claude Code and press enter.

**NEVER STOP between phases unless:**

- Gate failure after 2 auto-fix attempts
- Failed consensus (all 3 agents disagree)
- Security keyword triggers mandatory human review
- Missing prerequisite that blocks execution

**If a phase completes and its gate passes, IMMEDIATELY
advance to the next phase.** Do not stop to summarize, ask
for confirmation, or recommend next steps.

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

Update tasks dynamically as each prompt completes. If
execution produces unexpected work (new questions, extra
remediation loops), create additional tasks via TaskCreate
to keep the list accurate.

### Phase 0: Prerequisites (Constitution Validation)

**No workflow prompt.** This is autopilot-specific
pre-flight — it does NOT invoke a `/speckit.*` command.

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
Execute it via
`Skill("speckit.specify", args: "<the prompt>")`.

**Branch-aware exception:** If `ON_FEATURE_BRANCH` is true,
prefix the prompt with: "Already on feature branch
`<branch>`. Do NOT run `create-new-feature.sh`. Skip to
spec content generation."

**Gate:** G1 — check for `[NEEDS CLARIFICATION]` markers
(routing decision)

**Commit:**
`git add specs/ && git commit -m "feat(SPEC-XXX): complete specify phase"`

### Phase 2: Clarify (Conditional)

Only runs if G1 detected `[NEEDS CLARIFICATION]` markers.

The workflow file may define **multiple clarify sessions**
(e.g., "Session 1: OmniJS API", "Session 2: UX"). Execute
**EACH session as a separate Skill invocation**:

```text
For each clarify session in the workflow file:
  1. Read the session prompt
  2. Skill("speckit.clarify", args: "<that session prompt>")
  3. Log the session results (questions surfaced, answers given)
  4. Proceed to the next session
```

**Post-execution (after ALL sessions):** Check for
`[NEEDS CLARIFICATION]` markers remaining in spec.md. For
each question — check for security keywords, spawn 3
consensus agents in parallel (codebase-analyst,
spec-context-analyst, domain-researcher). Apply consensus
rules. If no consensus, flag `[HUMAN REVIEW NEEDED]`.

**If no questions remain after all sessions, the phase is
complete — advance immediately to Plan. Do NOT stop.**

**Gate:** G2 — verify 0 markers remain

**Commit:**
`git add specs/ && git commit -m "feat(SPEC-XXX): complete clarify phase"`

### Phase 3: Plan

Read the workflow file's `### Plan Prompt` section.
Execute it via
`Skill("speckit.plan", args: "<the prompt>")`.

**Gate:** G3 — verify plan.md, research.md, data-model.md
exist

**Commit:**
`git add specs/ && git commit -m "feat(SPEC-XXX): complete plan phase"`

### Phase 4: Checklist

The workflow file defines **multiple domain prompts**
(e.g., api-workaround, type-safety, requirements). Execute
**EACH domain as a separate Skill invocation**:

```text
For each checklist domain in the workflow file:
  1. Read the domain prompt
  2. Skill("speckit.checklist", args: "<that domain prompt>")
  3. Log the domain results
  4. Proceed to the next domain
```

**Post-execution (after ALL domains):** Parse `[Gap]`
markers across all checklists. If gaps found, run the
Checklist Remediation Loop with consensus agents (max 2
loops). If no gaps, advance immediately.

**Gate:** G4 — verify 0 `[Gap]` markers

**Commit:**
`git add specs/ && git commit -m "feat(SPEC-XXX): complete checklist phase"`

### Phase 5: Tasks

Read the workflow file's `### Tasks Prompt` section.
Execute it via
`Skill("speckit.tasks", args: "<the prompt>")`.

**Gate:** G5 — cross-reference every FR in spec.md with
tasks.md

**Commit:**
`git add specs/ && git commit -m "feat(SPEC-XXX): complete tasks phase"`

### Phase 6: Analyze

Read the workflow file's `### Analyze Prompt` section.
Execute it via
`Skill("speckit.analyze", args: "<the prompt>")`.

**Post-execution:** Parse findings by severity. For
CRITICAL/HIGH findings, run the Analyze Remediation Loop
with consensus agents (max 2 loops).

**Gate:** G6 — verify 0 CRITICAL findings

**Commit:**
`git add specs/ && git commit -m "feat(SPEC-XXX): complete analyze phase"`

### Phase 7: Implement

Read the workflow file's `### Implement Prompt` section.
Execute it via
`Skill("speckit.implement", args: "<the prompt>")`.

If the project has a specialized implementation agent in
CLAUDE.md (e.g., "omnifocus-developer"), delegate to that
agent instead. For `[P]` tasks, spawn parallel sub-agents
with worktree isolation.

**Gate:** G7 — full verification suite
(build + typecheck + lint + test)

**Commit:**
`git add . && git commit -m "feat(SPEC-XXX): implement phase N"`

**After G7 passes:** Execute PR Creation Protocol
(see below).

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

The PR body is auto-generated from:

- spec.md Summary section
- Implementation results from the workflow file
- Verification results (test counts, build status)
- Test plan checklist

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
