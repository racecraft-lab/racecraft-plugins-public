# Codex Commands Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `codex-commands/` directory with 5 Codex-native command files matching the existing CC `commands/`, plus structural tests and parity validation.

**Architecture:** Create plain-markdown command files (no YAML frontmatter) following the Figma plugin pattern (`# /command-name` heading + body). Each command adapts CC tool references to Codex equivalents (`$skill` sigils, shell commands instead of `Glob`/`Grep`). Add a structural test and extend the parity test.

**Tech Stack:** Markdown, Bash (tests), jq

---

### Task 1: Create `codex-commands/setup.md`

**Files:**
- Create: `speckit-pro/codex-commands/setup.md`

- [ ] **Step 1: Create the command file**

```markdown
# /setup

Prepare a spec from the technical roadmap for autonomous execution.
Creates the worktree, branch, and workflow file — ready for `$speckit-autopilot`.

## Arguments

- `spec_id` (required): The SPEC-ID from your technical roadmap (e.g., SPEC-009)

## Workflow

1. **Find the Technical Roadmap** — search for `*technical*roadmap*` or `docs/ai/*roadmap*.md`.
   If not found, stop: "No technical roadmap found. Ask `$speckit-coach` for help creating one."

2. **Find the Spec** — read the roadmap section for the requested SPEC-ID. Extract: spec name,
   short name (for branch), spec number, tool count/names, priority, dependencies, scope
   description, status. Must be ⏳ Pending.

3. **Create Git Worktree** — never commit to main. All work happens in the worktree:
   ```bash
   git remote -v                                       # detect remote name
   git worktree add .worktrees/<NNN>-<short-name> -b <NNN>-<short-name>
   cd .worktrees/<NNN>-<short-name>
   git push -u <remote> <NNN>-<short-name>
   git rev-parse --abbrev-ref HEAD                     # verify branch
   ```

4. **Copy & Populate Workflow Template** — read the template from
   `skills/speckit-coach/templates/workflow-template.md` (shared asset), write it to
   `.worktrees/<NNN>-<short-name>/docs/ai/specs/SPEC-<ID>-workflow.md`, and replace all
   placeholders (`SPEC_ID`, `SPEC_NAME`, `BRANCH_NAME`, `TOOL_COUNT`, `TOOL_NAMES`).
   Populate phase prompts from the roadmap scope description.

5. **Commit and Verify** — stage, commit, and push from the worktree branch (never main):
   ```bash
   cd .worktrees/<NNN>-<short-name>
   git add docs/ai/specs/SPEC-<ID>-workflow.md
   git commit -m "chore(SPEC-XXX): set up workflow for autopilot"
   git push
   ```

6. **Update Technical Roadmap** — mark the spec as 🔄 In Progress in the worktree copy.
   Commit and push.

## Output

Report the spec name, branch, worktree path, workflow file path, and the command to run next:
`$speckit-autopilot docs/ai/specs/SPEC-<ID>-workflow.md`
```

- [ ] **Step 2: Verify file exists and has content**

Run: `test -f speckit-pro/codex-commands/setup.md && wc -w speckit-pro/codex-commands/setup.md`
Expected: file exists, word count > 100

### Task 2: Create `codex-commands/status.md`

**Files:**
- Create: `speckit-pro/codex-commands/status.md`

- [ ] **Step 1: Create the command file**

```markdown
# /status

Show the full project roadmap: completed specs, in-progress specs, specs that
haven't started yet, and a recommendation for what to work on next.

## Arguments

- `spec_id` (optional): Show detail for a specific spec. Default: show full roadmap.

## Workflow

1. **Find Data Sources** — search for workflow files (`**/*-workflow.md`) and technical
   roadmap files (`**/*technical-roadmap*.md`, `docs/ai/*roadmap*.md`).

2. **Parse Technical Roadmap** — extract the Progress Tracking table with all specs:
   Spec ID, Name, Tools count, Status (✅ Complete, 🔄 In Progress, ⏳ Pending, ⚠️ Blocked),
   Priority (P1/P2/P3), Dependencies.

3. **Parse Workflow Files** — for each active workflow, extract phase statuses from the
   Workflow Overview table (⏳, 🔄, ✅, ⚠️), current phase, and branch name.

4. **Present Unified Dashboard** — combine roadmap and workflow data:
   - Summary (total specs, complete, in progress, remaining)
   - Completed Specs table
   - Ready to Start table (unblocked, sorted by priority)
   - Blocked table
   - Active Workflows phase detail

5. **Recommend Next Spec** — from unblocked pending specs, sort by Priority → roadmap order.
   Show top recommendation with setup command: `$speckit-setup SPEC-XXX`.
   List 1-2 alternatives.

6. **If Specific Spec Requested** — show phase statuses, scope description, dependencies,
   gate results, blockers. If no workflow exists, suggest: `$speckit-setup SPEC-XXX`.
```

- [ ] **Step 2: Verify file exists and has content**

Run: `test -f speckit-pro/codex-commands/status.md && wc -w speckit-pro/codex-commands/status.md`
Expected: file exists, word count > 100

### Task 3: Create `codex-commands/autopilot.md`

**Files:**
- Create: `speckit-pro/codex-commands/autopilot.md`

- [ ] **Step 1: Create the command file**

```markdown
# /autopilot

Execute a SpecKit workflow autonomously from a populated workflow file.

## Arguments

- `path` (required): Path to the populated workflow file
- `--from-phase` (optional): Start from a specific phase (specify|clarify|plan|checklist|tasks|analyze|implement)
- `--spec` (optional): Override spec ID detection

## Workflow

1. **Verify Prerequisites**:
   - Workflow file exists at the provided path
   - SpecKit CLI installed: `specify check`
   - `.specify/` directory exists with `scripts/bash/` and `templates/`
   - `.specify/memory/constitution.md` exists

2. **Load the speckit-autopilot skill** — invoke `$speckit-autopilot` with the workflow file
   path and any arguments. The skill contains the full orchestration logic.

The autopilot skill reads each phase's prompt from the workflow file and delegates
to subagents that run the corresponding SpecKit commands. It does not modify the
prompts — it passes them as-is.

## SpecKit Commands Used

| Phase | Command | Key Script |
|-------|---------|------------|
| Specify | `$speckit-specify` | `create-new-feature.sh` |
| Clarify | `$speckit-clarify` | `check-prerequisites.sh` |
| Plan | `$speckit-plan` | `setup-plan.sh`, `update-agent-context.sh` |
| Checklist | `$speckit-checklist` | `check-prerequisites.sh` |
| Tasks | `$speckit-tasks` | `check-prerequisites.sh` |
| Analyze | `$speckit-analyze` | `check-prerequisites.sh` |
| Implement | `$speckit-implement` | `check-prerequisites.sh` |
```

- [ ] **Step 2: Verify file exists and has content**

Run: `test -f speckit-pro/codex-commands/autopilot.md && wc -w speckit-pro/codex-commands/autopilot.md`
Expected: file exists, word count > 50

### Task 4: Create `codex-commands/coach.md`

**Files:**
- Create: `speckit-pro/codex-commands/coach.md`

- [ ] **Step 1: Create the command file**

```markdown
# /coach

Get SDD coaching and SpecKit guidance. Ask about methodology, commands,
troubleshooting, technical roadmaps, workflow tracking, or the speckit-pro
plugin itself.

## Arguments

- `question` (required): Your question about SDD or SpecKit
  Examples: "walk me through SDD", "help with clarify", "which checklists",
  "how does autopilot work", "consensus protocol"

## Workflow

1. **Load the speckit-coach skill** — invoke `$speckit-coach` with the user's question.
2. The skill contains routing tables and reference material — follow it exactly.

## No Prerequisites

The coach skill works without SpecKit installed — it provides guidance on setup too.
```

- [ ] **Step 2: Verify file exists and has content**

Run: `test -f speckit-pro/codex-commands/coach.md && wc -w speckit-pro/codex-commands/coach.md`
Expected: file exists, word count > 30

### Task 5: Create `codex-commands/resolve-pr.md`

**Files:**
- Create: `speckit-pro/codex-commands/resolve-pr.md`

- [ ] **Step 1: Create the command file**

```markdown
# /resolve-pr

Address all unresolved review comments on a pull request, fix the code,
and mark each thread resolved.

## Arguments

- `pr` (required): PR URL or number
  Examples: `https://github.com/owner/repo/pull/46`, `46`

## Workflow

1. **Parse Input** — extract OWNER, REPO, PR_NUMBER from the URL. If just a number,
   detect repo from `git remote -v`.

2. **Discover Project Commands** — read CLAUDE.md / AGENTS.md and package.json to find
   build, typecheck, lint, test commands.

3. **Fetch Unresolved Review Threads** — use `gh api graphql` to get all unresolved
   threads with thread IDs, file paths, line numbers, and comment bodies.

4. **Process Each Comment**:
   - Read the referenced file at the specified line
   - Determine action: code fix, style fix, question reply, or false positive
   - For code fixes: edit file, run verification (`build && typecheck && test`),
     commit with `git commit -m "fix: address review - <summary>"`
   - For style fixes: run lint fix, commit
   - For questions/false positives: prepare a reply

5. **Reply and Resolve** — for each comment, reply via `gh api` and resolve the
   thread via GraphQL `resolveReviewThread` mutation.

6. **Push** — `git push` all commits.

7. **Report Summary** — comments processed (code fixes, style fixes, replies),
   commits pushed, threads resolved, any remaining unresolved.
```

- [ ] **Step 2: Verify file exists and has content**

Run: `test -f speckit-pro/codex-commands/resolve-pr.md && wc -w speckit-pro/codex-commands/resolve-pr.md`
Expected: file exists, word count > 50

### Task 6: Create structural test `validate-codex-commands.sh`

**Files:**
- Create: `speckit-pro/tests/layer1-structural/validate-codex-commands.sh`

- [ ] **Step 1: Write the test script**

```bash
#!/usr/bin/env bash
# validate-codex-commands.sh — Structural validation for Codex command files
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

CODEX_COMMANDS_DIR="$PLUGIN_ROOT/codex-commands"
COMMANDS=(autopilot coach setup status resolve-pr)

# Claude Code-only frontmatter keys that must NOT appear in Codex commands
CC_ONLY_KEYS=(allowed-tools argument-hint)

section "codex-commands/ directory"

set_test "codex-commands/ directory exists"
if [ -d "$CODEX_COMMANDS_DIR" ]; then
  _pass
else
  _fail "codex-commands/ directory not found"
  test_summary
fi

for cmd in "${COMMANDS[@]}"; do
  CMD_FILE="$CODEX_COMMANDS_DIR/${cmd}.md"

  section "codex-commands/${cmd}.md"

  set_test "${cmd}: file exists"
  assert_file_exists "$CMD_FILE"

  if [ ! -f "$CMD_FILE" ]; then
    continue
  fi

  content=$(cat "$CMD_FILE")
  first_line=$(head -n1 "$CMD_FILE")

  set_test "${cmd}: starts with # (markdown heading, no YAML frontmatter)"
  if [[ "$first_line" == "# "* ]]; then
    _pass
  else
    _fail "first line must start with '# ', got: $first_line"
  fi

  set_test "${cmd}: no YAML frontmatter delimiters"
  fence_count=$(grep -c '^---$' "$CMD_FILE") || fence_count=0
  if [ "$fence_count" -eq 0 ]; then
    _pass
  else
    _fail "Codex commands must not have YAML frontmatter (found $fence_count '---' lines)"
  fi

  set_test "${cmd}: no Claude Code-only frontmatter keys"
  bad_keys=""
  for key in "${CC_ONLY_KEYS[@]}"; do
    if echo "$content" | grep -qE "^${key}:" ; then
      bad_keys="$bad_keys $key"
    fi
  done
  if [ -z "$bad_keys" ]; then
    _pass
  else
    _fail "Claude Code-only keys found:$bad_keys"
  fi

  set_test "${cmd}: has ## Arguments section"
  assert_contains "$content" "## Arguments"

  set_test "${cmd}: has ## Workflow section"
  assert_contains "$content" "## Workflow"

  set_test "${cmd}: body word count at least 30"
  word_count=$(wc -w < "$CMD_FILE" | tr -d ' ')
  if [ "$word_count" -ge 30 ]; then
    _pass
  else
    _fail "body is $word_count words (need at least 30)"
  fi

  set_test "${cmd}: no CC-specific tool references (Skill(), Agent())"
  if echo "$content" | grep -qE 'Skill\(|Agent\(\{'; then
    _fail "found Claude Code-specific tool references (Skill() or Agent())"
  else
    _pass
  fi
done

test_summary
```

- [ ] **Step 2: Make executable**

Run: `chmod +x speckit-pro/tests/layer1-structural/validate-codex-commands.sh`

- [ ] **Step 3: Run and verify it passes**

Run: `bash speckit-pro/tests/layer1-structural/validate-codex-commands.sh`
Expected: all tests pass

### Task 7: Add command parity to `validate-codex-parity.sh`

**Files:**
- Modify: `speckit-pro/tests/layer1-structural/validate-codex-parity.sh`

- [ ] **Step 1: Add command parity section**

After the "Skill Parity" section (before the "Shared Reference Integrity" section), add:

```bash
# ===========================================================================
# Command Parity — CC commands → Codex commands
# ===========================================================================
section "Command Parity (CC → Codex)"

COMMANDS_DIR="$PLUGIN_ROOT/commands"
CODEX_COMMANDS_DIR="$PLUGIN_ROOT/codex-commands"

if [ -d "$COMMANDS_DIR" ] && [ -d "$CODEX_COMMANDS_DIR" ]; then
  for cc_cmd_file in "$COMMANDS_DIR"/*.md; do
    [ -f "$cc_cmd_file" ] || continue
    cmd_name=$(basename "$cc_cmd_file" .md)
    set_test "codex-commands/${cmd_name}.md exists for CC command"
    assert_file_exists "$CODEX_COMMANDS_DIR/${cmd_name}.md"
  done
else
  set_test "commands/ and codex-commands/ directories exist"
  _fail "one or both command directories missing (CC: $COMMANDS_DIR, Codex: $CODEX_COMMANDS_DIR)"
fi

# ===========================================================================
# Command Parity — Codex commands → CC commands
# ===========================================================================
section "Command Parity (Codex → CC)"

if [ -d "$COMMANDS_DIR" ] && [ -d "$CODEX_COMMANDS_DIR" ]; then
  for codex_cmd_file in "$CODEX_COMMANDS_DIR"/*.md; do
    [ -f "$codex_cmd_file" ] || continue
    cmd_name=$(basename "$codex_cmd_file" .md)
    set_test "commands/${cmd_name}.md exists for Codex command"
    assert_file_exists "$COMMANDS_DIR/${cmd_name}.md"
  done
fi
```

- [ ] **Step 2: Run parity test and verify it passes**

Run: `bash speckit-pro/tests/layer1-structural/validate-codex-parity.sh`
Expected: all tests pass (including new command parity checks)

### Task 8: Wire test into `run-all.sh`

**Files:**
- Modify: `speckit-pro/tests/run-all.sh`

- [ ] **Step 1: Add codex commands test to the Codex structural validation block**

In the Codex structural tests block (after `validate-codex-hooks.sh` and before `validate-codex-parity.sh`), add:

```bash
      "$TESTS_DIR/layer1-structural/validate-codex-commands.sh" \
```

- [ ] **Step 2: Run the full Codex test suite**

Run: `bash speckit-pro/tests/run-all.sh --codex`
Expected: all layers pass, including new codex commands tests

### Task 9: Commit

**Files:** all new and modified files

- [ ] **Step 1: Stage and commit**

```bash
git add speckit-pro/codex-commands/ speckit-pro/tests/layer1-structural/validate-codex-commands.sh speckit-pro/tests/layer1-structural/validate-codex-parity.sh speckit-pro/tests/run-all.sh
git commit -m "feat(speckit-pro): add Codex CLI commands for all 5 entry points

Create codex-commands/ directory with plain-markdown command files
matching the Figma plugin pattern (no YAML frontmatter). Adapts all
CC commands (setup, status, autopilot, coach, resolve-pr) to Codex
tool references. Adds structural test and command parity validation."
```

- [ ] **Step 2: Verify clean state**

Run: `git status`
Expected: clean working tree
