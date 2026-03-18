# Phase Execution Reference

How each SDD phase is executed by the autopilot. Each phase **invokes the real `/speckit.*` command** via the `Skill` tool, passing the **workflow file's prompt directly** as the command argument. The workflow prompts are pre-populated by the user with all necessary context — the autopilot does not enrich or supplement them. The commands handle their own infrastructure (branch creation, template copying, prerequisite validation) via `.specify/scripts/bash/`.

## SpecKit Infrastructure

The autopilot relies on the project's installed SpecKit commands and scripts:

| Component | Location | Purpose |
|-----------|----------|---------|
| **Commands** | `.claude/commands/speckit.*.md` | Slash commands that orchestrate each SDD phase |
| **Scripts** | `.specify/scripts/bash/` | Shell scripts for branch creation, path resolution, prerequisite checking |
| **Templates** | `.specify/templates/` | Spec, plan, tasks, checklist, and agent file templates |
| **Constitution** | `.specify/memory/constitution.md` | Project principles for gate validation |

### Key Scripts

| Script | Used By | What It Does |
|--------|---------|-------------|
| `common.sh` | All scripts | Branch detection (`get_current_branch`), feature path resolution (`get_feature_paths`, `find_feature_dir_by_prefix`) |
| `create-new-feature.sh` | `/speckit.specify` | Creates git branch, `specs/` dir, copies spec template. Supports `--json`, `--short-name`, `--number` |
| `setup-plan.sh` | `/speckit.plan` | Copies plan template to feature dir. Outputs `FEATURE_SPEC`, `IMPL_PLAN`, `SPECS_DIR`, `BRANCH` |
| `check-prerequisites.sh` | `/speckit.clarify`, `.checklist`, `.tasks`, `.analyze`, `.implement` | Validates feature dir + required files exist. Supports `--json`, `--require-tasks`, `--include-tasks`, `--paths-only` |
| `update-agent-context.sh` | `/speckit.plan` | Updates CLAUDE.md with tech stack extracted from plan.md |

## Prompt Passthrough

The workflow file contains a pre-populated prompt for each phase (e.g., "Specify Prompt", "Plan Prompt", "Checklist Prompts"). The autopilot reads the prompt and passes it directly to the `/speckit.*` command as the argument. **No enrichment or supplementation is performed** — the workflow prompt is the complete input.

The commands themselves handle context gathering internally:
- `/speckit.specify` reads the spec template
- `/speckit.plan` reads spec.md, constitution, runs research
- `/speckit.checklist` reads spec.md + plan.md + available design docs
- `/speckit.implement` reads tasks.md + plan.md + all design docs

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

**Execution strategy:** Runs directly in the main session (no sub-agent needed). Does NOT invoke a `/speckit.*` command — this is autopilot-specific pre-flight.

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

**Invokes:** `/speckit.specify` via the `Skill` tool — **with branch-aware handling**

**What the command does internally:**
1. Calls `create-new-feature.sh --json --short-name "<name>" --number <N>` to create branch + `specs/` directory + copy spec template
2. Reads the spec template and generates the specification from the feature description
3. Outputs `spec.md` and optionally `checklists/requirements.md`

**Problem:** The command ALWAYS calls `create-new-feature.sh`, which runs `git checkout -b`. On a worktree or existing feature branch, this would fail or create a wrong nested branch.

**Autopilot execution (branch-aware):**

```text
1. Read the workflow file's "Specify Prompt" section — this is the complete prompt
2. Check ON_FEATURE_BRANCH (detected in Step 0.7):

   IF ON_FEATURE_BRANCH is true:
     — Already on a feature branch (e.g., worktree 009-search-database)
     — Do NOT invoke Skill("speckit.specify") — it would try to create a new branch
     — Instead:
       a. Run: .specify/scripts/bash/check-prerequisites.sh --json --paths-only
          to get FEATURE_DIR and FEATURE_SPEC paths for the existing branch
       b. Ensure specs/<branch-name>/ directory exists (mkdir -p if needed)
       c. Copy spec template if spec.md doesn't exist yet:
          cp .specify/templates/spec-template.md <FEATURE_SPEC>
       d. Execute the content generation portion of specify:
          - Read the spec template structure
          - Use the workflow prompt as the feature description
          - Write spec.md to the existing feature directory
          - Generate checklists/requirements.md quality checklist
       e. This is the same work the command does AFTER branch creation —
          we skip only the create-new-feature.sh step

   IF ON_FEATURE_BRANCH is false:
     — On main/develop, starting a fresh spec
     — Invoke normally: Skill("speckit.specify", args: "<workflow prompt>")
     — The command creates the branch and directory via create-new-feature.sh

3. Validate G1 gate
```

**Why the other commands don't have this problem:** They all use `check-prerequisites.sh` → `get_current_branch()`, which reads the git branch directly (no `SPECIFY_FEATURE` env var needed). On a worktree, `git rev-parse --abbrev-ref HEAD` returns the worktree branch automatically.

**Gate:** G1 — check for `[NEEDS CLARIFICATION]` markers (routing decision)

**Workflow updates:**
- Status table: `⏳ Pending` → `✅ Complete` with summary (e.g., "6 stories, 12 FRs, 8 SCs")
- Specify Results table: FR count, US count, acceptance criteria, edge cases
- Files Generated checkboxes

**Commit:** `git add specs/ && git commit -m "feat(SPEC-XXX): complete specify phase"`

### Phase 2: Clarify (Conditional)

**Invokes:** `/speckit.clarify` via the `Skill` tool (for initial question identification)

**Trigger:** Only runs if G1 detected `[NEEDS CLARIFICATION]` markers.

**What the command does internally:**
1. Calls `check-prerequisites.sh --json --paths-only` to get feature paths
2. Reads spec.md and performs structured ambiguity scan
3. Asks up to 5 clarification questions and encodes answers into spec.md

**Autopilot execution (consensus mode):**

This phase runs in the MAIN SESSION because it needs to spawn consensus agents.

```text
1. Read the workflow file's "Clarify Prompts" section for focus areas
2. For each clarify session defined in the workflow:
   a. Invoke: Skill("speckit.clarify", args: "<focus area from workflow>")
   b. The command surfaces questions about the spec
   c. For each question surfaced:
      i.  Check for security keywords → if found, flag for human
      ii. Spawn 3 consensus agents IN PARALLEL (background):
          - codebase-analyst
          - spec-context-analyst
          - domain-researcher
          Each receives: spec.md excerpt + the question
      iii. Wait for all 3 to complete
      iv.  Apply consensus rules (see consensus-protocol.md)
      v.   If consensus → respond to the clarify command with the agreed answer
      vi.  If no consensus → flag [HUMAN REVIEW NEEDED]
3. Validate G2: no remaining markers
```

**Gate:** G2 — verify 0 `[NEEDS CLARIFICATION]` and 0 `[HUMAN REVIEW NEEDED]` markers

**Workflow updates:**
- Status table updated
- Clarify Results table: session focus, questions, key outcomes

**Commit:** `git add specs/ && git commit -m "feat(SPEC-XXX): complete clarify phase"`

### Phase 3: Plan

**Invokes:** `/speckit.plan` via the `Skill` tool

**What the command does internally:**
1. Calls `setup-plan.sh --json` to copy plan template and get paths
2. Reads spec.md and constitution
3. Fills Technical Context, runs Constitution Check gates
4. Phase 0: Generates `research.md` (resolves unknowns)
5. Phase 1: Generates `data-model.md`, `contracts/`, `quickstart.md`
6. Calls `update-agent-context.sh` to update CLAUDE.md with tech stack

**Autopilot execution:**

```text
1. Read the workflow file's "Plan Prompt" section — this is the complete prompt
2. Invoke: Skill("speckit.plan", args: "<workflow prompt>")
   - The command handles template copying, context gathering, and agent context update
3. Validate G3 gate
```

**Gate:** G3 — verify plan.md, research.md, data-model.md exist; check constitutional gates

**Workflow updates:**
- Status table updated
- Plan Results table: artifact status for each generated file

**Commit:** `git add specs/ && git commit -m "feat(SPEC-XXX): complete plan phase"`

### Phase 4: Checklist

**Invokes:** `/speckit.checklist` via the `Skill` tool (once per domain)

**What the command does internally:**
1. Calls `check-prerequisites.sh --json` to get paths and available docs
2. Reads spec.md + plan.md + available design docs
3. Generates a domain-specific checklist in `checklists/<domain>.md`

**Autopilot execution (consensus mode for gap remediation):**

This phase runs in the MAIN SESSION because it may need consensus agents for gap remediation.

```text
1. Read ALL checklist prompts from the workflow file's checklist section
2. For each domain prompt:
   a. Invoke: Skill("speckit.checklist", args: "<domain prompt from workflow>")
   b. The command generates the checklist with [Gap] markers for issues found
3. Parse [Gap] markers across all produced checklists
4. If gaps found, run the Checklist Remediation Loop:
   For EACH gap (sequentially to prevent conflicting edits):
   a. Spawn 3 consensus agents IN PARALLEL
   b. Apply consensus rules → produce proposed spec/plan edit
   c. Apply the edit
5. Re-run all checklists to verify gaps closed (max 2 loops)
6. Validate G4: 0 [Gap] markers
```

**Gate:** G4 — verify 0 `[Gap]` markers across all checklist files

**Workflow updates:**
- Status table updated
- Checklist Results table: per-domain items count, gaps count, spec references
- Addressing Gaps section if gaps were remediated

**Commit:** `git add specs/ && git commit -m "feat(SPEC-XXX): complete checklist phase"`

### Phase 5: Tasks

**Invokes:** `/speckit.tasks` via the `Skill` tool

**What the command does internally:**
1. Calls `check-prerequisites.sh --json` to get paths and available docs
2. Reads plan.md (tech stack, structure), spec.md (user stories), and optional docs
3. Generates `tasks.md` organized by user story with dependency ordering

**Autopilot execution:**

```text
1. Read the workflow file's "Tasks Prompt" section — this is the complete prompt
2. Invoke: Skill("speckit.tasks", args: "<workflow prompt>")
   - The command handles prerequisite validation and doc discovery
3. Validate G5 gate
```

**Gate:** G5 — cross-reference every FR-XXX in spec.md with tasks.md

**Workflow updates:**
- Status table updated
- Tasks Results table: total tasks, phases, parallel opportunities, user stories covered

**Commit:** `git add specs/ && git commit -m "feat(SPEC-XXX): complete tasks phase"`

### Phase 6: Analyze

**Invokes:** `/speckit.analyze` via the `Skill` tool

**What the command does internally:**
1. Calls `check-prerequisites.sh --json --require-tasks --include-tasks` to validate all artifacts
2. Reads spec.md + plan.md + tasks.md + constitution
3. Performs cross-artifact consistency analysis (READ-ONLY — does not modify files)
4. Outputs findings by severity (CRITICAL, HIGH, MEDIUM, LOW)

**Autopilot execution (consensus mode for finding remediation):**

This phase runs in the MAIN SESSION because it may need consensus agents for finding remediation.

```text
1. Read the workflow file's "Analyze Prompt" section — this is the complete prompt
2. Invoke: Skill("speckit.analyze", args: "<workflow prompt>")
   - The command validates prerequisites and runs the analysis
   - It is READ-ONLY — it only reports findings, does not modify files
3. Parse findings by severity
4. For each CRITICAL or HIGH finding, run the Analyze Remediation Loop:
   a. Spawn 3 consensus agents IN PARALLEL
   b. Apply consensus rules → produce proposed fix
   c. Apply the fix to the appropriate artifact (spec.md, plan.md, or tasks.md)
5. Re-run analyze to verify (max 2 loops)
6. Validate G6: 0 CRITICAL findings
```

**Gate:** G6 — verify 0 CRITICAL findings

**Workflow updates:**
- Status table updated
- Analysis Results table: ID, severity, issue, resolution per finding
- Constitution alignment notes
- FR coverage notes

**Commit:** `git add specs/ && git commit -m "feat(SPEC-XXX): complete analyze phase"`

### Phase 7: Implement

**Invokes:** `/speckit.implement` via the `Skill` tool (or delegates to project-specific implementation agent)

**What the command does internally:**
1. Calls `check-prerequisites.sh --json --require-tasks --include-tasks` to validate all artifacts
2. Checks checklist completion status — if incomplete, warns (autopilot proceeds since checklists already passed G4)
3. Reads tasks.md for the task list, plan.md for architecture, and all optional docs
4. Executes tasks following TDD Red-Green-Refactor cycle

**Autopilot execution:**

```text
1. Read the workflow file's "Implement Prompt" section — this is the complete prompt
2. Check if the project has a specialized implementation agent:
   - Look in CLAUDE.md for agent references (e.g., "omnifocus-developer")
   - If found, delegate to that agent instead of /speckit.implement
3. Invoke: Skill("speckit.implement", args: "<workflow prompt>")
   - The command handles prerequisite validation, checklist checks, and doc loading
4. For implementation, read tasks.md and identify phases:
   a. For tasks marked [P] → spawn background sub-agents (one per task)
      - Use isolation: "worktree" if available for file-conflict safety
   b. For sequential tasks → spawn one foreground sub-agent at a time
   c. After each implementation phase completes:
      git add . && git commit -m "feat(SPEC-XXX): implement phase N - <description>"
5. After all tasks: run G7 verification suite
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

1. **Status table**: Change phase status from `⏳ Pending` to `✅ Complete` with summary notes
2. **Phase-specific results table**: Fill in metrics and outcomes
3. **Files Generated checkboxes**: Check off produced artifacts
4. **Consensus Resolution Log** (if applicable): Record consensus decisions

The workflow file serves as both checklist and execution log — the complete auditable record of the autonomous execution.
