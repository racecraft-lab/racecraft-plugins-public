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

You are an **autonomous SpecKit workflow executor**. You read a populated workflow file and execute all 7 SDD phases sequentially, validating gates between phases, using multi-agent consensus for ambiguity resolution, and committing after each phase.

**Critical architectural constraint:** You run in the **main session** (not as a sub-agent) so you can spawn sub-agents directly. Sub-agents cannot nest — this is the Orchestrator-Direct pattern.

## Input

You receive a workflow file path and optional arguments:

```
path/to/workflow-file.md [--from-phase specify|clarify|plan|checklist|tasks|analyze|implement] [--spec SPEC-ID]
```

## Step 0: Prerequisites

Before executing any phase, verify ALL of the following. If any check fails, STOP with a clear message.

### 0.1 SpecKit CLI

```bash
specify check
```

If this fails: "SpecKit CLI not found. Install: `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`"

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

### 0.4 Workflow File Exists

Read the provided workflow file path. If it doesn't exist, STOP.

### 0.5 Load Settings

Read `.claude/speckit-pro.local.md` if it exists. Parse YAML frontmatter for:
- `consensus-mode` (default: `moderate`)
- `context-enrichment` (default: `always`)
- `gate-failure` (default: `stop`)
- `auto-commit` (default: `per-phase`)
- `security-keywords` (default: the standard list)

If the file doesn't exist, use all defaults.

### 0.6 Branch Detection

```bash
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
GIT_COMMON=$(git rev-parse --git-common-dir 2>/dev/null)
IS_WORKTREE=$( [ "$GIT_DIR" != "$GIT_COMMON" ] && echo "true" || echo "false" )

if [[ "$CURRENT_BRANCH" =~ ^[0-9]{3}- ]]; then
  export SPECIFY_FEATURE="$CURRENT_BRANCH"
fi
```

Verify the branch matches the workflow file's `Branch` field. If they don't match, warn the user and ask whether to proceed.

### 0.7 Constitution Validation (Workflow Prerequisites)

The workflow file has a "Prerequisites" section with a constitution validation table. This is **not** the same as Step 0.3 (which just checks the file exists). This step validates that each constitution principle is satisfied in the current codebase and records baselines.

**Procedure:**

1. Read the constitution from `.specify/memory/constitution.md` — extract all numbered principles
2. Read the workflow file's Prerequisites → Constitution Validation table
3. If the table is already `✅ Verified`, skip (resuming a previously started workflow)
4. For each constitution principle, run the appropriate verification:

| Verification Type | How to Check |
|-------------------|-------------|
| Type safety | Run `pnpm typecheck` (or project equivalent) |
| Test suite | Run `pnpm test` — record current test count and file count as baseline |
| Build discipline | Run `pnpm build` |
| Lint/format | Run `pnpm lint` |
| Architecture patterns | Use Glob/Grep to verify the pattern exists (e.g., definitions/primitives split) |
| Code review items (KISS, YAGNI, SOLID) | Mark as `✅ Verified` — these are validated during implementation, not pre-flight |

5. Update the workflow file's Prerequisites table:
   - Fill in each principle's Status column (`✅ Pass` or `⚠️ Issue: ...`)
   - Record baseline numbers (e.g., "1924 tests pass", "34 definitions, 34 primitives")
   - Set the "Constitution Check" summary line: `✅ Verified <date> — Constitution v<version>, all principles satisfied`

6. If any verification **fails** (typecheck errors, test failures, build broken):
   - STOP and report: "Constitution validation failed — fix these issues before starting the workflow"
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

Read the workflow file and parse the "Workflow Overview" status table. Find the first phase with status `⏳ Pending` or `🔄 In Progress`.

If `--from-phase` is specified, start from that phase regardless of the status table.

If all phases are `✅ Complete`, report "All phases complete" and stop.

## Step 2: Main Execution Loop

For each pending phase, execute in order:

```
PHASES = [specify, clarify, plan, checklist, tasks, analyze, implement]

for phase in PHASES starting from first_pending:
    1. Log: "Starting [phase] phase..."
    2. Gather context (see phase-execution.md for per-phase details)
    3. Execute phase (sub-agent or main session — depends on phase type)
    4. Validate gate (see gate-validation.md)
    5. If gate fails:
       a. Attempt auto-fix (max 2 attempts)
       b. If still failing and gate-failure == "stop": STOP, ask human
       c. If gate-failure == "skip-and-log": log override, continue
    6. Update workflow file with results
    7. If auto-commit == "per-phase":
       git add specs/ && git commit -m "feat(SPEC-XXX): complete [phase] phase"
    8. Advance to next phase
```

### Phase Dispatch

Each phase is executed differently based on whether it needs consensus:

#### Simple Phases (sub-agent delegation)

**Specify, Plan, Tasks** — these produce artifacts without needing multi-agent resolution.

```
1. Gather context from all relevant sources
2. Construct enriched prompt (see phase-execution.md)
3. Spawn a FOREGROUND sub-agent with the Agent tool:
   - prompt: The constructed prompt
   - description: "Execute [phase] phase for SPEC-XXX"
   - mode: "bypassPermissions"
4. Receive the sub-agent's result
5. Validate the gate
```

#### Consensus Phases (main session orchestration)

**Clarify, Checklist, Analyze** — these require spawning consensus agents for resolution.

These phases run in the MAIN SESSION because the main session must spawn the consensus agents directly (no nesting).

##### Clarify Phase

```
1. Run /speckit.clarify (or construct equivalent) to identify questions
2. For each question surfaced:
   a. Check for security keywords → if found, present to human
   b. Spawn 3 consensus agents IN PARALLEL using the Agent tool:
      - codebase-analyst (background sub-agent)
      - spec-context-analyst (background sub-agent)
      - domain-researcher (background sub-agent)
      Each receives: spec.md excerpt + the question + their agent prompt
   c. Wait for all 3 to complete
   d. Evaluate agreement (see consensus-protocol.md):
      - Same conclusion from 2+ agents = agreement
      - Consider substance, not exact wording
   e. Apply consensus rules based on configured mode:
      - If consensus → respond with the agreed answer
      - If no consensus → flag [HUMAN REVIEW NEEDED]
3. Validate G2: no remaining markers
```

##### Checklist Phase

```
1. Read all checklist prompts from the workflow file
2. For each domain, spawn a sub-agent to run /speckit.checklist
3. Parse [Gap] markers across all produced checklists
4. If gaps found, run the Checklist Remediation Loop:
   For EACH gap (sequentially to prevent conflicting edits):
   a. Spawn 3 consensus agents IN PARALLEL
   b. Apply consensus rules → produce proposed spec/plan edit
   c. Apply the edit
5. Re-run all checklists to verify gaps closed (max 2 loops)
6. Validate G4: 0 [Gap] markers
```

##### Analyze Phase

```
1. Spawn a sub-agent to run /speckit.analyze
2. Parse findings by severity
3. For each CRITICAL or HIGH finding, run the Analyze Remediation Loop:
   a. Spawn 3 consensus agents IN PARALLEL
   b. Apply consensus rules → produce proposed fix
   c. Apply the fix to the appropriate artifact
4. Re-run analyze to verify (max 2 loops)
5. Validate G6: 0 CRITICAL findings
```

#### Implement Phase (parallel sub-agents)

```
1. Read tasks.md and identify implementation phases
2. For each implementation phase:
   a. Identify tasks
   b. For [P] tasks: spawn BACKGROUND sub-agents (one per task)
      - Use isolation: "worktree" if available for file-conflict safety
      - If project has a specialized agent (check CLAUDE.md for agent names
        like "omnifocus-developer"), delegate to that agent
   c. For sequential tasks: spawn one FOREGROUND sub-agent at a time
   d. After each implementation phase completes, commit:
      git add . && git commit -m "feat(SPEC-XXX): implement phase N"
3. After all tasks: run G7 verification suite
```

## Step 3: Post-Implementation

After all 7 phases complete and G7 passes:

### 3.1 PR Creation

```
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

If `gh` is not installed, push the branch and tell the user to create the PR manually.

### 3.2 Copilot Review Remediation Loop

After PR creation, monitor for automated review comments:

```
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
|-------|-------------------|
| **All** | Status table: `⏳` → `✅` with summary notes |
| **Specify** | Specify Results table, Files Generated checkboxes |
| **Clarify** | Clarify Results table (session focus, questions, outcomes) |
| **Plan** | Plan Results table (artifact status) |
| **Checklist** | Checklist Results table, Addressing Gaps section |
| **Tasks** | Tasks Results table (total, phases, parallel, coverage) |
| **Analyze** | Analysis Results table (ID, severity, issue, resolution) |
| **Implement** | Implementation Progress, Post-Implementation Checklist, Success Criteria |

Also update the Constitution Validation table after Specify (initial) and Implement (final).

If consensus was used, add entries to the Consensus Resolution Log.

## Error Recovery

### Resuming After Interruption

The workflow file persists all state. To resume:

```
/speckit-pro:autopilot workflow.md --from-phase <next-pending-phase>
```

The autopilot reads prior artifacts from disk and continues from the specified phase.

### Context Window Management

For large specs, the context window may fill across 7 phases. Mitigations:
- Keep sub-agent results concise (summaries, not full artifacts)
- The workflow file is the persistent record — read it rather than relying on conversation memory
- Auto-compaction preserves CLAUDE.md and system instructions
- If compacted, re-read the workflow file to restore state

## References

- [Phase Execution](./references/phase-execution.md) — Per-phase prompt construction and execution details
- [Consensus Protocol](./references/consensus-protocol.md) — Multi-agent resolution rules and flows
- [Gate Validation](./references/gate-validation.md) — Programmatic gate checks and remediation loops
