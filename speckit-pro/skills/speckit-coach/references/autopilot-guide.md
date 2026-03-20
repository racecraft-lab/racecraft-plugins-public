# Autopilot Guide

Comprehensive guide to the speckit-pro autonomous workflow
executor. Use this when coaching developers on how to set up,
configure, run, and troubleshoot the autopilot.

**Related commands:**
- `/speckit-pro:setup <SPEC-ID>` — create worktree + workflow file
- `/speckit-pro:autopilot <workflow.md>` — run the autopilot
- `/speckit-pro:status` — check progress across all specs
- `/speckit-pro:resolve-pr <PR>` — fix review comments post-PR
- `/speckit-pro:coach` — get help with any of the above

---

## Prerequisites

Before running the autopilot, the following must be in place:

### 1. SpecKit CLI Installed

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
specify check  # Verify installation
```

### 2. SpecKit Initialized in the Project

```bash
specify init --ai claude  # or: --ai copilot, --ai cursor
```

This creates `.specify/`, templates, and slash commands.

### 3. Constitution Created

```bash
/speckit.constitution
```

The constitution must exist at
`.specify/memory/constitution.md`. Without it, the autopilot
cannot validate constitutional gates during the Plan phase.

**Note:** The autopilot also validates each constitution
principle against the current codebase before starting Phase 1
(Specify). It discovers the project's build, typecheck, lint,
and test commands (Step 0.10) and runs them all to record
baselines (test count, file count). It fills in the workflow
file's Prerequisites → Constitution Validation table. If any
check fails, the autopilot stops — the codebase must be healthy
before starting a new spec.

### 4. Master Plan Exists (Recommended)

For multi-spec projects, create a master plan first:

```text
/speckit-pro:coach help me create a master plan
```

The master plan provides scope descriptions that drive the
Specify phase.

### 5. Workflow File Populated

Copy the workflow template and fill in the prompts:

```bash
cp skills/speckit-coach/templates/workflow-template.md docs/ai/specs/SPEC-XXX-workflow.md
```

**Critical:** The workflow file must have:

- All placeholder values replaced (SPEC_ID, SPEC_NAME,
  BRANCH_NAME)
- Phase prompts populated with project-specific details (tech
  stack, constraints, checklist domains)
- Success criteria defined

The more detail in the workflow file's prompts, the better the
autopilot's output.

---

## How Autopilot Works

### The Orchestrator-Direct Pattern

The autopilot skill runs **in the main session** so it can
spawn sub-agents directly. This avoids the subagent nesting
limitation (sub-agents cannot spawn their own sub-agents).

Each phase **invokes the real `/speckit.*` command** via the
`Skill` tool, passing the **workflow file's prompt directly**
as the argument. The autopilot does not enrich, supplement, or
modify the prompts — it passes them as-is, like a human would
copy-paste the prompt into Claude Code. The commands handle
their own infrastructure (branch creation, template copying,
prerequisite validation via `.specify/scripts/bash/`).

```text
Main session (speckit-autopilot skill loaded)
    │
    ├── Simple phases → pass workflow prompt to /speckit.* via Skill
    │   ├── Specify → Skill("speckit.specify", args: "<workflow prompt>")
    │   ├── Plan    → Skill("speckit.plan", args: "<workflow prompt>")
    │   └── Tasks   → Skill("speckit.tasks", args: "<workflow prompt>")
    │
    ├── Multi-prompt phases → one Skill() per session/domain
    │   ├── Clarify   → Skill("speckit.clarify") per session + consensus
    │   ├── Checklist  → Skill("speckit.checklist") per domain + consensus
    │   └── Analyze    → Skill("speckit.analyze") + consensus per finding
    │
    └── Implement → Skill("speckit.implement") or project-specific agent
        └── Parallel sub-agents with worktree isolation for [P] tasks
```

### Phase-by-Phase Execution

The autopilot reads the workflow file and executes phases
sequentially:

1. **Parse workflow state** — Find the next `⏳ Pending`
   phase
2. **Create task list** — One task per prompt (granular
   tracking for multi-prompt phases like Clarify/Checklist)
3. **Read the workflow prompt** — Copy the phase's prompt
   from the workflow file
4. **Invoke command** —
   `Skill("speckit.<phase>", args: "<the prompt>")` —
   the command handles its own context gathering internally
5. **Orchestrate consensus** — For clarify/checklist/analyze
   phases, spawn 3 agents per question/gap/finding
6. **Validate gate** — Run programmatic gate checks
7. **Handle failure** — Auto-fix (max 2 attempts), then
   escalate to human
8. **Update workflow file** — Mark phase complete with results
9. **Commit** —
   `git add specs/ && git commit -m "feat(SPEC-XXX): complete [phase] phase"`
10. **Advance** — Immediately start next phase (never stop)

### Gate Validation

Each phase has a programmatic gate that validates its output:

| Gate | After | What It Checks | Auto-Fix |
| ---- | ----- | -------------- | -------- |
| G0 | Prerequisites | Typecheck, test, build, lint all pass | None (user must fix) |
| G1 | Specify | `[NEEDS CLARIFICATION]` markers | Routing (not pass/fail) |
| G2 | Clarify | 0 markers + 0 human review flags | Re-run clarify |
| G3 | Plan | Artifacts exist, gates pass | Re-run plan |
| G4 | Checklist | 0 `[Gap]` markers | Consensus remediation loop |
| G5 | Tasks | All FRs mapped to tasks | Generate missing tasks |
| G6 | Analyze | 0 CRITICAL findings | Consensus remediation loop |
| G7 | Implement | Build+type+lint+test pass | Fix errors |

If auto-fix fails after 2 attempts, the autopilot **STOPS**
and presents the failure to the human with context and all
agent perspectives.

---

## Consensus Protocol

The consensus protocol is the core autonomy mechanism. Three
perspective agents provide multi-viewpoint resolution for
questions, gaps, and findings.

### The 3 Perspective Agents

| Agent | Perspective | What It Does |
| ----- | ----------- | ------------ |
| **codebase-analyst** | What does the code show? | Searches existing code via RepoPrompt for established patterns, types, naming conventions |
| **spec-context-analyst** | What do decisions say? | Reads constitution, master plan, prior specs for established principles and precedent |
| **domain-researcher** | What do best practices say? | Searches Tavily/Context7 for official docs, standards, community patterns |

### Consensus Modes

| Mode | 2/3 Agree | 3/3 Agree | All Disagree | Security Keywords |
| ---- | --------- | --------- | ------------ | ----------------- |
| **Conservative** | Flag for human (with recommendation) | Auto-answer | Flag for human | Always flag |
| **Moderate** (default) | Auto-answer | Auto-answer | Flag for human | Always flag |
| **Aggressive** | Auto-answer | Auto-answer | Attempt synthesis | Always flag |

**When to choose each mode:**

| Mode | Best For |
|------|----------|
| **Conservative** | Security-sensitive projects, regulated industries, first-time autopilot users. Stops more often for human review — slower but safer. |
| **Moderate** | Most projects. Balances autonomy with safety. Auto-answers when 2/3 agents agree, stops when all disagree. |
| **Aggressive** | Well-established projects with strong constitutions and experienced users. Attempts to synthesize even when agents disagree. Only stops for security keywords. |

Configure in `.claude/speckit-pro.local.md`:

```yaml
consensus-mode: moderate
```

### Security Keywords

These words in any question/gap/finding trigger **mandatory
human review** regardless of consensus mode:

```text
auth, token, secret, encryption, PII, credential, permission,
password, authentication, authorization, session, cookie, jwt,
api-key, access-control
```

### When Consensus Is Used

| Phase | Input to Consensus | Output |
| ----- | ------------------ | ------ |
| **Clarify** | Each clarification question | Answer integrated into spec.md |
| **Checklist** | Each `[Gap]` marker | Spec/plan edit to close the gap |
| **Analyze** | Each CRITICAL/HIGH finding | Artifact edit to fix the finding |

### Real-World Example (SPEC-013)

From the completed SPEC-013 workflow:

- **Clarify**: 6 questions resolved via domain-researcher
  (OmniJS API docs), 0 needed human input
- **Checklist**: 9 gaps remediated — 4 via codebase-analyst
  (existing patterns), 2 via domain-researcher (Tavily), 2
  via spec-context-analyst (spec edits), 1 via disambiguation
- **Analyze**: 5 findings remediated — added tasks, amended
  coverage, removed markers

---

## Workflow File as Checklist

The autopilot treats the workflow file as both input (prompts)
and output (results). After each phase, it updates:

| Section | What Gets Updated |
| ------- | ----------------- |
| **Status table** | `⏳ Pending` → `✅ Complete` with summary notes |
| **Phase results** | Metrics (FR count, task count, gap count, etc.) |
| **Files generated** | Checkboxes for produced artifacts |
| **Consensus log** | Which questions/gaps/findings were resolved and how |
| **Implementation progress** | Per-phase task completion |
| **Post-implementation checklist** | Build/test/lint/typecheck results |

This makes the workflow file a complete, auditable record of
the autonomous execution.

---

## Branch/Worktree Support

The autopilot supports three branch scenarios:

| Scenario | Detection | Behavior |
| -------- | --------- | -------- |
| **New spec on main** | On main/develop branch | Specify creates the feature branch via `create-new-feature.sh` |
| **Existing feature branch** | Branch matches `NNN-feature-name` | Specify skips branch creation, uses existing `specs/` directory |
| **Git worktree** | `git-dir` ≠ `git-common-dir` | Same as existing feature branch — branch already exists |

Before executing any phase, the autopilot detects the branch
and records two flags:

- `ON_FEATURE_BRANCH`: `true` if the branch matches
  `^[0-9]{3}-`
- `IS_WORKTREE`: `true` if git-dir differs from
  git-common-dir

It also verifies the detected branch matches the workflow
file's `Branch` field.

### Why Specify Needs Special Handling

The `/speckit.specify` command normally calls
`create-new-feature.sh` to create a branch. On a worktree or
existing feature branch, this must be skipped.

When `ON_FEATURE_BRANCH` is `true`, the autopilot prefixes
the workflow prompt with an instruction telling the command to
skip branch creation, then invokes `Skill("speckit.specify")`
normally. The command's LLM reads the prefix and proceeds
directly to spec content generation.

The other 6 commands (clarify, plan, checklist, tasks,
analyze, implement) all use `check-prerequisites.sh` →
`get_current_branch()`, which reads the git branch directly.
On a worktree, `git rev-parse --abbrev-ref HEAD` returns the
worktree branch automatically — no special handling needed.

---

## Configuration

Create `.claude/speckit-pro.local.md` for per-project
settings:

```yaml
---
consensus-mode: moderate    # conservative | moderate | aggressive
gate-failure: stop          # stop | skip-and-log
auto-commit: per-phase      # per-phase | batch | none
security-keywords:
  - auth
  - token
  - secret
  - encryption
  - PII
  - credential
  - permission
  - password
---

# Project-specific notes for speckit-pro autopilot
(Optional markdown content for project-specific autopilot guidance)
```

### Settings Explained

| Setting | Description |
| ------- | ----------- |
| `consensus-mode` | How strict the consensus protocol is (see Consensus Modes above) |
| `gate-failure` | Whether to stop or log-and-skip when a gate fails after max fix attempts |
| `auto-commit` | When to commit — after each phase, all at once, or never |
| `security-keywords` | Additional keywords that trigger mandatory human review |

If the file doesn't exist, defaults are used (moderate, stop,
per-phase).

---

## PR Creation & Review Loop

After all 7 phases complete and G7 passes:

### PR Creation

1. Run final verification suite (build + typecheck + lint +
   test)
2. Detect remote name via `git remote -v`
3. Push branch: `git push -u <remote> <branch>`
4. Create PR via `gh pr create` with auto-generated body
5. Update workflow file with PR URL
6. Final commit

### Copilot Review Remediation

After PR creation, the autopilot monitors for review
comments:

1. Poll every 5 minutes (max 1 hour) via `gh api`
2. For each unresolved comment:
   - Code change needed → fix, verify, commit, push
   - Style/formatting → auto-fix with lint
   - Question → post reply explaining the design decision
   - False positive → post reply explaining why no change
     needed
3. Each fix gets its own commit for traceability
4. Exit when no unresolved comments remain or after 1 hour

**Requires:** `gh` CLI installed and authenticated. If not
available, the autopilot pushes the branch and instructs the
user to create the PR manually.

---

## Troubleshooting

### Gate Failure After Max Attempts

**Symptom:** Autopilot stops with "Gate GN failed after 2
auto-fix attempts"

**What to do:**

1. Read the failure context — the autopilot presents what
   failed and what was tried
2. Provide guidance: "Fix X, then continue" or "Proceed
   anyway" or "Stop"
3. The autopilot resumes from the failed phase after your
   input

### Consensus Can't Resolve

**Symptom:** All 3 agents disagree on a
question/gap/finding

**What to do:**

1. Review all 3 perspectives presented by the autopilot
2. Choose the best answer or provide your own
3. The autopilot integrates your answer and continues

### Autopilot Stops Unexpectedly

**Common causes:**

- Missing prerequisite (no constitution, no workflow file)
- Security keyword detected (mandatory human review)
- Context window filling up (too many phases in one session)

**Recovery:**

1. Run `/speckit-pro:status` to see where the autopilot
   stopped
2. Fix the issue
3. Re-run
   `/speckit-pro:autopilot workflow.md --from-phase <failed-phase>`

### Context Window Limits

For large specs with many phases, the context window may fill
up. The autopilot uses the workflow file as persistent state,
so it can be resumed:

```text
/speckit-pro:autopilot workflow.md --from-phase checklist
```

This starts from the checklist phase, reading prior artifacts
from disk.

### Resuming After Any Interruption

The workflow file persists all state. To resume from any point:

```text
# 1. Check where you left off
/speckit-pro:status

# 2. Look at the workflow file for the last completed phase
cat docs/ai/specs/SPEC-XXX-workflow.md | grep "✅\|⏳\|🔄"

# 3. Resume from the next pending phase
/speckit-pro:autopilot docs/ai/specs/SPEC-XXX-workflow.md --from-phase <next>
```

**Safe to re-run:** Phases are idempotent — re-running a
completed phase overwrites its artifacts but doesn't corrupt
state. If you're unsure where you left off, it's safe to
re-run from an earlier phase.

---

## Running Autopilot — Step by Step

### 1. Prepare

```bash
# Install SpecKit (if not already)
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
specify init --ai claude

# Create constitution (if not already)
/speckit.constitution

# Create master plan (for multi-spec projects)
/speckit-pro:coach help me create a master plan

# Create and populate workflow file
cp skills/speckit-coach/templates/workflow-template.md docs/ai/specs/SPEC-XXX-workflow.md
# Edit the workflow file — fill in ALL prompts with project-specific details
```

### 2. Configure (Optional)

Create `.claude/speckit-pro.local.md` if you want non-default
settings.

### 3. Run

```bash
# Start Claude with skip-permissions for fully autonomous execution
claude --dangerously-skip-permissions

# Launch autopilot
/speckit-pro:autopilot docs/ai/specs/SPEC-XXX-workflow.md
```

### 4. Monitor

The autopilot provides status updates at each phase boundary.
It will stop and ask for input when:

- A gate fails after 2 auto-fix attempts
- Consensus agents all disagree
- A security keyword triggers mandatory review
- The workflow is complete (PR created)

### 5. Review

After the autopilot creates a PR:

- Review the spec artifacts in `specs/<number>-<name>/`
- Review the code changes
- Verify OmniJS scripts in Script Editor (if applicable)
- Merge when satisfied

---

## v0.3.2 Capabilities

### `/speckit.doctor` — Project Health Diagnostics

The autopilot can use the doctor extension at any point to
check project health across structure, agents, features,
scripts, extensions, and git. This is useful for:

- Logging progress in the workflow file
- Verifying phase completion after gates pass
- Resuming after interruption

### Preset and Extension Awareness

The autopilot detects installed presets and extensions at
startup (Step 0.11). This matters because:

**Presets** may modify template content. If a preset overrides
`tasks-template.md` (e.g., to enforce TDD or add extra
sections), the `/speckit.tasks` command will generate tasks
with different structure. The autopilot's task parsing should
handle any template variant.

**Extensions** may register hook events. For example:
- `after_tasks` → verify-tasks extension prompts to check
  task completeness
- `after_implement` → verify extension validates against spec,
  retrospective extension scores spec adherence

The autopilot handles extension hooks by:
1. Accepting optional, non-destructive hooks automatically
2. Skipping hooks that duplicate its own verification
3. Documenting hook decisions in the workflow file

### Template Resolution

When presets are installed, template resolution follows a
4-tier priority stack:

1. Project overrides (`.specify/templates/overrides/`)
2. Installed presets (by priority number)
3. Extension templates
4. Core templates

The autopilot doesn't need to know the resolution order — it
just invokes `/speckit.*` commands and the template system
handles resolution. But awareness helps with debugging if
generated artifacts have unexpected structure.
