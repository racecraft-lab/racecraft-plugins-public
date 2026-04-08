# Codex CLI Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add OpenAI Codex CLI compatibility to speckit-pro so the same GitHub repo works as both a Claude Code and Codex CLI plugin marketplace.

**Architecture:** Dual-manifest plugin with parallel `codex-*` directories for platform-specific files. Shared assets (scripts, references, templates) stay in place. Each task is independently testable and committable.

**Tech Stack:** Bash test scripts, JSON manifests, YAML frontmatter, Markdown agent/skill definitions

**Spec:** `docs/superpowers/specs/2026-04-07-codex-cli-compatibility-design.md`

---

## File Map

### New Files (Create)

| File | Purpose |
|---|---|
| `speckit-pro/.codex-plugin/plugin.json` | Codex plugin manifest |
| `.agents/plugins/marketplace.json` | Codex marketplace registry (repo root) |
| `speckit-pro/codex-hooks.json` | Codex SessionStart hook |
| `speckit-pro/codex-agents/openai.yaml` | Plugin-level Codex agent metadata |
| `speckit-pro/codex-agents/clarify-executor.md` | Codex agent definition |
| `speckit-pro/codex-agents/checklist-executor.md` | Codex agent definition |
| `speckit-pro/codex-agents/analyze-executor.md` | Codex agent definition |
| `speckit-pro/codex-agents/implement-executor.md` | Codex agent definition |
| `speckit-pro/codex-agents/phase-executor.md` | Codex agent definition |
| `speckit-pro/codex-agents/codebase-analyst.md` | Codex agent definition |
| `speckit-pro/codex-agents/spec-context-analyst.md` | Codex agent definition |
| `speckit-pro/codex-agents/domain-researcher.md` | Codex agent definition |
| `speckit-pro/codex-skills/speckit-coach/SKILL.md` | Codex coach skill |
| `speckit-pro/codex-skills/speckit-coach/agents/openai.yaml` | Coach skill Codex metadata |
| `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` | Codex autopilot skill |
| `speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml` | Autopilot skill Codex metadata |
| `speckit-pro/tests/layer1-structural/validate-codex-plugin.sh` | Codex manifest validation |
| `speckit-pro/tests/layer1-structural/validate-codex-agents.sh` | Codex agent validation |
| `speckit-pro/tests/layer1-structural/validate-codex-skills.sh` | Codex skill validation |
| `speckit-pro/tests/layer1-structural/validate-codex-hooks.sh` | Codex hooks validation |
| `speckit-pro/tests/layer1-structural/validate-codex-marketplace.sh` | Codex marketplace validation |
| `speckit-pro/tests/layer1-structural/validate-codex-parity.sh` | Cross-platform parity checks |

### Modified Files

| File | Change |
|---|---|
| `release-please-config.json` | Add `.codex-plugin/plugin.json` to `extra-files` |
| `speckit-pro/tests/run-all.sh` | Add `--codex` flag and wire in new test scripts |

---

### Task 1: Codex Plugin Manifest & Marketplace Registry

**Files:**
- Create: `speckit-pro/.codex-plugin/plugin.json`
- Create: `.agents/plugins/marketplace.json`

- [ ] **Step 1: Create Codex plugin manifest**

```bash
mkdir -p speckit-pro/.codex-plugin
```

Write `speckit-pro/.codex-plugin/plugin.json`:

```json
{
  "name": "speckit-pro",
  "version": "1.1.0",
  "description": "Autonomous Spec-Driven Development powered by GitHub SpecKit. Includes SDD coaching, multi-spec project management, and a fully autonomous workflow executor with multi-agent clarification consensus.",
  "author": {
    "name": "Fredrick Gabelmann",
    "url": "https://github.com/racecraft-lab"
  },
  "repository": "https://github.com/racecraft-lab/racecraft-plugins-public",
  "license": "MIT",
  "keywords": ["speckit", "sdd", "spec-driven-development", "specification", "planning", "autopilot", "autonomous", "workflow"],
  "skills": "./codex-skills/",
  "interface": {
    "displayName": "SpecKit Pro",
    "shortDescription": "Spec-Driven Development with autonomous workflow execution",
    "longDescription": "Autonomous SDD powered by GitHub SpecKit. Includes methodology coaching, multi-spec project management, and a fully autonomous 7-phase workflow executor with multi-agent clarification consensus.",
    "developerName": "Racecraft Lab",
    "category": "Coding",
    "capabilities": ["Interactive", "Read", "Write"],
    "websiteURL": "https://github.com/racecraft-lab/racecraft-plugins-public",
    "defaultPrompt": "Use SpecKit Pro to coach me through Spec-Driven Development, set up a new spec, or run an autonomous SDD workflow",
    "brandColor": "#6366F1"
  }
}
```

- [ ] **Step 2: Create Codex marketplace registry**

```bash
mkdir -p .agents/plugins
```

Write `.agents/plugins/marketplace.json`:

```json
{
  "name": "racecraft-public-plugins",
  "interface": {
    "displayName": "Racecraft Public Plugins"
  },
  "plugins": [
    {
      "name": "speckit-pro",
      "source": {
        "source": "local",
        "path": "./speckit-pro"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Coding"
    }
  ]
}
```

- [ ] **Step 3: Verify JSON validity**

Run: `python3 -m json.tool speckit-pro/.codex-plugin/plugin.json > /dev/null && echo OK`
Expected: `OK`

Run: `python3 -m json.tool .agents/plugins/marketplace.json > /dev/null && echo OK`
Expected: `OK`

- [ ] **Step 4: Verify version matches Claude Code manifest**

Run: `diff <(jq -r '.version' speckit-pro/.claude-plugin/plugin.json) <(jq -r '.version' speckit-pro/.codex-plugin/plugin.json)`
Expected: No output (versions match)

- [ ] **Step 5: Commit**

```bash
git add speckit-pro/.codex-plugin/plugin.json .agents/plugins/marketplace.json
git commit -m "feat(speckit-pro): add Codex CLI plugin manifest and marketplace registry"
```

---

### Task 2: Codex Hooks

**Files:**
- Create: `speckit-pro/codex-hooks.json`

- [ ] **Step 1: Create Codex hooks file**

Write `speckit-pro/codex-hooks.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "command -v specify >/dev/null 2>&1 || echo 'speckit-pro: WARNING — SpecKit CLI not found. Install: uv tool install specify-cli --from git+https://github.com/github/spec-kit.git'",
            "statusMessage": "Checking SpecKit CLI availability"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Verify JSON validity**

Run: `python3 -m json.tool speckit-pro/codex-hooks.json > /dev/null && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add speckit-pro/codex-hooks.json
git commit -m "feat(speckit-pro): add Codex CLI SessionStart hook"
```

---

### Task 3: Codex Agent Definitions

**Files:**
- Create: `speckit-pro/codex-agents/openai.yaml`
- Create: `speckit-pro/codex-agents/{all 8 agents}.md`

The Codex agents have simplified frontmatter (only `name`, `description`, `model`, `model_reasoning_effort`, `sandbox_mode`) and adapted system prompt bodies (Codex tool names, `$skill-name` sigil invocation, natural language agent spawning).

- [ ] **Step 1: Create codex-agents directory and openai.yaml**

```bash
mkdir -p speckit-pro/codex-agents
```

Write `speckit-pro/codex-agents/openai.yaml`:

```yaml
interface:
  display_name: "SpecKit Pro"
  short_description: "SDD agents for autonomous workflow execution"
```

- [ ] **Step 2: Create clarify-executor.md**

Write `speckit-pro/codex-agents/clarify-executor.md`. Use the same system prompt body as `speckit-pro/agents/clarify-executor.md` with these adaptations:

Frontmatter:
```yaml
---
name: clarify-executor
description: >
  Executes a single /speckit.clarify session. The clarify command
  is interactive — it surfaces clarification questions about the
  spec and expects researched, evidence-grounded answers. This
  agent researches each question using web search, library docs,
  codebase exploration, and local file analysis, then provides
  the best-supported answer. Use for every clarify session in
  the autopilot workflow.
model: gpt-5.4-pro
model_reasoning_effort: high
sandbox_mode: workspace-write
---
```

Body adaptations from Claude Code version:
- Replace `Skill` tool references with `$speckit-clarify` sigil
- Replace `mcp__tavily-mcp__tavily-search` → `tavily-search` (Codex MCP naming)
- Replace `mcp__tavily-mcp__tavily-extract` → `tavily-extract`
- Replace `mcp__context7__resolve-library-id` → `resolve-library-id`
- Replace `mcp__context7__get-library-docs` → `get-library-docs`
- Replace `mcp__RepoPrompt__context_builder` → `context_builder`
- Replace `mcp__RepoPrompt__file_search` → `file_search`
- Replace references to `Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob` tools with generic filesystem operation language (Codex doesn't use those tool names)
- Keep all behavioral rules, search strategies, output format, and hard constraints intact

- [ ] **Step 3: Create checklist-executor.md**

Same adaptation pattern as Step 2. Frontmatter:
```yaml
---
name: checklist-executor
description: >
  Executes a single /speckit.checklist domain and remediates any
  [Gap] markers found. After running the checklist, this agent
  researches each gap using web search, library docs, codebase
  exploration, and local file analysis to determine evidence-grounded
  fixes, then applies them to spec.md or plan.md. Use for every
  checklist domain in the autopilot workflow.
model: gpt-5.4-pro
model_reasoning_effort: high
sandbox_mode: workspace-write
---
```

Read `speckit-pro/agents/checklist-executor.md` for the full body. Apply the same tool name adaptations as Step 2.

- [ ] **Step 4: Create analyze-executor.md**

Frontmatter:
```yaml
---
name: analyze-executor
description: >
  Executes /speckit.analyze and remediates ALL findings at every
  severity level (CRITICAL, HIGH, MEDIUM, LOW). After running the
  analysis, this agent researches each finding using web search,
  library docs, codebase exploration, and local file analysis to
  determine evidence-grounded fixes, then applies them to the
  relevant artifacts. Use for the analyze phase in the autopilot
  workflow.
model: gpt-5.4-pro
model_reasoning_effort: high
sandbox_mode: workspace-write
---
```

Read `speckit-pro/agents/analyze-executor.md` for the full body. Apply same tool name adaptations.

- [ ] **Step 5: Create implement-executor.md**

Frontmatter:
```yaml
---
name: implement-executor
description: >
  Executes a SINGLE implementation task using strict TDD
  red-green-refactor. Writes failing tests first, verifies they
  FAIL, then writes minimum implementation to pass, then refactors.
  Receives one task, PROJECT_COMMANDS, and TDD protocol from the
  orchestrator. Returns structured TDD evidence. Use for individual
  tasks in the autopilot implement phase.
model: gpt-5.4-pro
model_reasoning_effort: x_high
sandbox_mode: workspace-write
---
```

Read `speckit-pro/agents/implement-executor.md` for the full body. This agent has NO MCP tool references — it only uses filesystem and shell. Adaptations:
- Remove references to `Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob` tool names
- Replace with generic language ("read the file", "write the implementation", "run the test command")
- Remove the `> **Note:** This agent uses effort: max which requires Opus 4.6` note — replace with Codex-appropriate note about `model_reasoning_effort: x_high`
- Keep all TDD rules, PROJECT_COMMANDS format, and output format intact

- [ ] **Step 6: Create phase-executor.md**

Frontmatter:
```yaml
---
name: phase-executor
description: >
  Executes a single SpecKit phase by running the /speckit.* command
  via the skill system. Use when the autopilot needs to run Specify,
  Plan, or Tasks phases — simple phases that don't require research,
  consensus, or iterative remediation. Returns a concise summary of
  files created, metrics, markers found, and errors.
model: gpt-5.4
model_reasoning_effort: medium
sandbox_mode: workspace-write
---
```

Read `speckit-pro/agents/phase-executor.md` for the full body. Adaptations:
- Replace `Skill` tool invocations with `$speckit-*` sigil syntax
- Replace `Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob` references with generic filesystem language

- [ ] **Step 7: Create codebase-analyst.md**

Frontmatter:
```yaml
---
name: codebase-analyst
description: >
  Analyzes the existing codebase to resolve questions from the perspective
  of established code patterns and conventions. Used by speckit-autopilot
  during consensus resolution for Clarify (answering questions), Checklist
  (remediating gaps), and Analyze (fixing findings). Spawned with a specific
  question, gap description, or finding — returns a structured answer with
  file-level evidence from the codebase.
model: gpt-5.4
model_reasoning_effort: medium
sandbox_mode: read-only
---
```

Read `speckit-pro/agents/codebase-analyst.md` for the full body. This is a read-only analyst. Adaptations:
- Replace `mcp__RepoPrompt__*` tool names with short names (`context_builder`, `file_search`, `get_code_structure`, `read_file`)
- Replace `Read`, `Glob`, `Grep` references with generic language
- `sandbox_mode: read-only` enforces the read-only constraint that Claude Code achieves via `permissionMode: plan` + restricted tool list

- [ ] **Step 8: Create spec-context-analyst.md**

Frontmatter:
```yaml
---
name: spec-context-analyst
description: >
  Analyzes project constitution, technical roadmap, and prior spec artifacts
  to resolve questions from the perspective of established project
  decisions and principles. Used across Clarify, Checklist, and Analyze
  consensus phases. Spawned with a specific question, gap, or finding —
  returns an answer grounded in project decisions and specifications.
model: gpt-5.4
model_reasoning_effort: medium
sandbox_mode: read-only
---
```

Read `speckit-pro/agents/spec-context-analyst.md` for the full body. Simplest adaptation — this agent uses only `Read`, `Glob`, `Grep`. Replace with generic filesystem language.

- [ ] **Step 9: Create domain-researcher.md**

Frontmatter:
```yaml
---
name: domain-researcher
description: >
  Researches industry best practices and official documentation to
  resolve questions with evidence-based recommendations. Used across
  Clarify, Checklist, and Analyze consensus phases. Spawned with a
  specific question, gap, or finding — returns an answer backed by
  external documentation and community best practices.
model: gpt-5.4
model_reasoning_effort: medium
sandbox_mode: read-only
---
```

Read `speckit-pro/agents/domain-researcher.md` for the full body. Adaptations:
- Replace `mcp__tavily-mcp__tavily-search` → `tavily-search`
- Replace `mcp__tavily-mcp__tavily-extract` → `tavily-extract`
- Replace `mcp__context7__*` → short names
- Replace `WebSearch`, `WebFetch` → "web search" / "fetch the page" generic language
- Replace `Read` → generic language

- [ ] **Step 10: Verify all 8 agents have frontmatter and body**

Run:
```bash
for f in speckit-pro/codex-agents/*.md; do
  echo "=== $(basename $f) ==="
  head -5 "$f"
  echo "---"
  wc -l "$f"
done
```

Expected: Each file starts with `---`, has `name:` field, and has >20 lines.

- [ ] **Step 11: Commit**

```bash
git add speckit-pro/codex-agents/
git commit -m "feat(speckit-pro): add Codex CLI agent definitions with model mapping"
```

---

### Task 4: Codex Coach Skill

**Files:**
- Create: `speckit-pro/codex-skills/speckit-coach/SKILL.md`
- Create: `speckit-pro/codex-skills/speckit-coach/agents/openai.yaml`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p speckit-pro/codex-skills/speckit-coach/agents
```

- [ ] **Step 2: Create openai.yaml sidecar**

Write `speckit-pro/codex-skills/speckit-coach/agents/openai.yaml`:

```yaml
interface:
  display_name: "SpecKit Coach"
  short_description: "SDD methodology coaching and SpecKit guidance"
  default_prompt: "Coach me through Spec-Driven Development, help with a SpecKit command, or explain SDD methodology"

policy:
  allow_implicit_invocation: true
```

- [ ] **Step 3: Create Codex coach SKILL.md**

Write `speckit-pro/codex-skills/speckit-coach/SKILL.md`. Start from `speckit-pro/skills/speckit-coach/SKILL.md` (read it first).

Frontmatter (Codex only needs `name` and `description`):
```yaml
---
name: speckit-coach
description: >
  Coaches developers through Spec-Driven Development using the
  official SpecKit CLI and the speckit-pro plugin. Provides SDD
  methodology guidance, per-command coaching, phase gate validation,
  multi-spec technical roadmap creation, and workflow tracking.
---
```

Body adaptations:
- Replace all `Skill("speckit.X")` with `$speckit-X` sigil syntax
- Replace `Read`, `Glob`, `Grep` tool references with generic language ("search for files", "read the file")
- Replace references to `CLAUDE.md` with `AGENTS.md` where the instruction refers to the project instruction file
- Update reference paths to point to shared references: `../../skills/speckit-coach/references/command-guide.md` etc.
- Keep all coaching logic, command descriptions, methodology content intact
- Remove `user-invokable`, `license`, `argument-hint` from frontmatter (Codex doesn't use these)

- [ ] **Step 4: Verify reference paths resolve**

Run:
```bash
grep -oE '\.\./\.\./skills/speckit-coach/references/[^ )]+' speckit-pro/codex-skills/speckit-coach/SKILL.md | while read -r ref; do
  full="speckit-pro/codex-skills/speckit-coach/$ref"
  [ -f "$full" ] && echo "OK: $ref" || echo "MISSING: $ref"
done
```

Expected: All paths show `OK`

- [ ] **Step 5: Verify word count is in range**

Run:
```bash
body=$(awk 'BEGIN{n=0} /^---$/{n++; if(n==2){found=1; next}} found{print}' speckit-pro/codex-skills/speckit-coach/SKILL.md)
echo "$body" | wc -w
```

Expected: Between 500 and 8000 words

- [ ] **Step 6: Commit**

```bash
git add speckit-pro/codex-skills/speckit-coach/
git commit -m "feat(speckit-pro): add Codex CLI coach skill with shared references"
```

---

### Task 5: Codex Autopilot Skill

**Files:**
- Create: `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`
- Create: `speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p speckit-pro/codex-skills/speckit-autopilot/agents
```

- [ ] **Step 2: Create openai.yaml sidecar**

Write `speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml`:

```yaml
interface:
  display_name: "SpecKit Autopilot"
  short_description: "Autonomous 7-phase SDD workflow executor"
  default_prompt: "Run a SpecKit autopilot workflow from a populated workflow file"

policy:
  allow_implicit_invocation: false

dependencies:
  tools:
    - type: mcp
      value: tavily
      description: "Web search for consensus research"
    - type: mcp
      value: context7
      description: "Library documentation lookup"
```

- [ ] **Step 3: Create Codex autopilot SKILL.md**

Write `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`. Start from `speckit-pro/skills/speckit-autopilot/SKILL.md` (read it first — it's ~30KB).

Frontmatter:
```yaml
---
name: speckit-autopilot
description: >
  Autonomous SpecKit workflow executor. Reads a populated workflow
  file and runs all 7 SDD phases with programmatic gate validation,
  multi-agent consensus resolution, and auto-commits. Requires
  SpecKit CLI installed, constitution created, and a populated
  workflow file.
---
```

Body adaptations (this is the most complex file):
- Replace all `Skill("speckit.X")` with `$speckit-X` sigil syntax
- Replace `Agent({ subagent_type: "clarify-executor", prompt: "..." })` with natural language: "Spawn the clarify-executor agent with the following instructions: ..."
- Replace parallel `Agent()` calls (e.g., spawning 3 consensus analysts) with: "Spawn these three agents in parallel: codebase-analyst, spec-context-analyst, domain-researcher. Each receives the following question: ..."
- Replace `SendMessage` references with: "Send a message to the running agent"
- Replace `TaskCreate`/`TaskUpdate` with generic progress tracking language
- Replace all CC tool names with generic language
- Replace MCP tool names with short names (drop `mcp__server__` prefix)
- Update reference paths: `../../skills/speckit-autopilot/references/consensus-protocol.md` etc.
- Update script paths: `../../skills/speckit-autopilot/scripts/validate-gate.sh` etc.
- Remove `user-invokable`, `license` from frontmatter

- [ ] **Step 4: Verify reference paths resolve**

Run:
```bash
grep -oE '\.\./\.\./skills/speckit-autopilot/(references|scripts)/[^ )]+' speckit-pro/codex-skills/speckit-autopilot/SKILL.md | while read -r ref; do
  full="speckit-pro/codex-skills/speckit-autopilot/$ref"
  [ -f "$full" ] && echo "OK: $ref" || echo "MISSING: $ref"
done
```

Expected: All paths show `OK`

- [ ] **Step 5: Verify word count is in range**

Run:
```bash
body=$(awk 'BEGIN{n=0} /^---$/{n++; if(n==2){found=1; next}} found{print}' speckit-pro/codex-skills/speckit-autopilot/SKILL.md)
echo "$body" | wc -w
```

Expected: Between 500 and 8000 words

- [ ] **Step 6: Commit**

```bash
git add speckit-pro/codex-skills/speckit-autopilot/
git commit -m "feat(speckit-pro): add Codex CLI autopilot skill with shared references and scripts"
```

---

### Task 6: Structural Tests — Codex Plugin & Marketplace

**Files:**
- Create: `speckit-pro/tests/layer1-structural/validate-codex-plugin.sh`
- Create: `speckit-pro/tests/layer1-structural/validate-codex-marketplace.sh`

- [ ] **Step 1: Create validate-codex-plugin.sh**

Write `speckit-pro/tests/layer1-structural/validate-codex-plugin.sh`:

```bash
#!/usr/bin/env bash
# validate-codex-plugin.sh — Structural validation for .codex-plugin/plugin.json
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

PLUGIN_JSON="$PLUGIN_ROOT/.codex-plugin/plugin.json"

section ".codex-plugin/plugin.json — File Existence"

set_test "codex plugin.json exists"
assert_file_exists "$PLUGIN_JSON"

section ".codex-plugin/plugin.json — Valid JSON"

set_test "codex plugin.json is valid JSON"
if python3 -m json.tool "$PLUGIN_JSON" >/dev/null 2>&1; then
  _pass
else
  _fail "codex plugin.json is not valid JSON"
fi

CONTENT=$(cat "$PLUGIN_JSON")

section ".codex-plugin/plugin.json — Required Fields"

set_test "name field exists and matches speckit-pro"
assert_json_field "$CONTENT" "name" "speckit-pro"

set_test "version field exists and is semver"
version_val=$(printf '%s' "$CONTENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])" 2>/dev/null)
assert_match "$version_val" '^[0-9]+\.[0-9]+\.[0-9]+$' "version must be X.Y.Z"

set_test "description field exists and is non-empty"
desc_val=$(printf '%s' "$CONTENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['description'])" 2>/dev/null)
if [ -n "$desc_val" ]; then _pass; else _fail "description is empty"; fi

set_test "skills field points to ./codex-skills/"
assert_json_field "$CONTENT" "skills" "./codex-skills/"

set_test "codex-skills directory exists"
if [ -d "$PLUGIN_ROOT/codex-skills" ]; then _pass; else _fail "codex-skills/ directory not found"; fi

section ".codex-plugin/plugin.json — Interface Block"

set_test "interface.displayName exists"
assert_json_field_exists "$CONTENT" "interface.displayName"

set_test "interface.category exists"
assert_json_field_exists "$CONTENT" "interface.category"

section ".codex-plugin/plugin.json — Version Sync"

set_test "version matches .claude-plugin/plugin.json"
cc_version=$(jq -r '.version' "$PLUGIN_ROOT/.claude-plugin/plugin.json" 2>/dev/null)
codex_version=$(printf '%s' "$CONTENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])" 2>/dev/null)
assert_eq "$cc_version" "$codex_version" "Claude Code and Codex versions must match"

test_summary
```

- [ ] **Step 2: Create validate-codex-marketplace.sh**

Write `speckit-pro/tests/layer1-structural/validate-codex-marketplace.sh`:

```bash
#!/usr/bin/env bash
# validate-codex-marketplace.sh — Structural validation for .agents/plugins/marketplace.json
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REPO_ROOT="$(cd "$PLUGIN_ROOT/.." && pwd)"

MARKETPLACE="$REPO_ROOT/.agents/plugins/marketplace.json"

section "Codex marketplace.json — File Existence"

set_test "codex marketplace.json exists"
assert_file_exists "$MARKETPLACE"

section "Codex marketplace.json — Valid JSON"

set_test "codex marketplace.json is valid JSON"
if python3 -m json.tool "$MARKETPLACE" >/dev/null 2>&1; then
  _pass
else
  _fail "codex marketplace.json is not valid JSON"
fi

CONTENT=$(cat "$MARKETPLACE")

section "Codex marketplace.json — Structure"

set_test "has name field"
assert_json_field_exists "$CONTENT" "name"

set_test "has plugins array"
assert_json_field_exists "$CONTENT" "plugins"

set_test "first plugin name is speckit-pro"
plugin_name=$(printf '%s' "$CONTENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['plugins'][0]['name'])" 2>/dev/null)
assert_eq "speckit-pro" "$plugin_name"

set_test "source.path resolves to existing directory"
source_path=$(printf '%s' "$CONTENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['plugins'][0]['source']['path'])" 2>/dev/null)
resolved="$REPO_ROOT/$source_path"
if [ -d "$resolved" ]; then _pass; else _fail "source.path '$source_path' does not resolve to a directory"; fi

set_test "plugin has policy.installation field"
assert_json_field_exists "$CONTENT" "plugins.0.policy.installation"

test_summary
```

- [ ] **Step 3: Make scripts executable and run them**

Run:
```bash
chmod +x speckit-pro/tests/layer1-structural/validate-codex-plugin.sh
chmod +x speckit-pro/tests/layer1-structural/validate-codex-marketplace.sh
bash speckit-pro/tests/layer1-structural/validate-codex-plugin.sh
bash speckit-pro/tests/layer1-structural/validate-codex-marketplace.sh
```

Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add speckit-pro/tests/layer1-structural/validate-codex-plugin.sh \
        speckit-pro/tests/layer1-structural/validate-codex-marketplace.sh
git commit -m "test(speckit-pro): add Codex plugin and marketplace structural validation"
```

---

### Task 7: Structural Tests — Codex Agents, Skills, Hooks

**Files:**
- Create: `speckit-pro/tests/layer1-structural/validate-codex-agents.sh`
- Create: `speckit-pro/tests/layer1-structural/validate-codex-skills.sh`
- Create: `speckit-pro/tests/layer1-structural/validate-codex-hooks.sh`

- [ ] **Step 1: Create validate-codex-agents.sh**

Write `speckit-pro/tests/layer1-structural/validate-codex-agents.sh`:

```bash
#!/usr/bin/env bash
# validate-codex-agents.sh — Structural validation for Codex agent definitions
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

AGENTS_DIR="$PLUGIN_ROOT/codex-agents"
AGENTS=(
  clarify-executor
  checklist-executor
  analyze-executor
  implement-executor
  phase-executor
  codebase-analyst
  spec-context-analyst
  domain-researcher
)

section "codex-agents/openai.yaml"

set_test "openai.yaml exists"
assert_file_exists "$AGENTS_DIR/openai.yaml"

for agent in "${AGENTS[@]}"; do
  AGENT_FILE="$AGENTS_DIR/${agent}.md"

  section "codex-agents/${agent}.md"

  set_test "${agent}: file exists"
  assert_file_exists "$AGENT_FILE"

  if [ ! -f "$AGENT_FILE" ]; then continue; fi

  first_line=$(head -n1 "$AGENT_FILE")

  set_test "${agent}: starts with --- (YAML frontmatter)"
  assert_eq "---" "$first_line"

  set_test "${agent}: has closing ---"
  fence_count=$(grep -c '^---$' "$AGENT_FILE") || fence_count=0
  if [ "$fence_count" -ge 2 ]; then _pass; else _fail "expected at least 2 '---' lines, found $fence_count"; fi

  frontmatter=$(awk '/^---$/{n++; if(n==1){next} if(n==2){exit}} n==1{print}' "$AGENT_FILE")

  set_test "${agent}: has name: field"
  assert_contains "$frontmatter" "name:"

  set_test "${agent}: has description: field"
  assert_contains "$frontmatter" "description:"

  set_test "${agent}: has model: field with OpenAI model"
  model_val=$(echo "$frontmatter" | grep -m1 '^model:' | sed 's/^model:[[:space:]]*//' | tr -d '"' | tr -d "'")
  assert_match "$model_val" '^gpt-' "model must start with gpt-"

  set_test "${agent}: has sandbox_mode: field"
  assert_contains "$frontmatter" "sandbox_mode:"

  set_test "${agent}: no Claude Code fields (tools:, permissionMode:, color:, maxTurns:)"
  for bad_field in "tools:" "permissionMode:" "color:" "maxTurns:" "background:"; do
    if echo "$frontmatter" | grep -q "^${bad_field}"; then
      _fail "Codex agent must not have Claude Code field '${bad_field}'"
      break
    fi
  done
  # If we didn't fail on any, pass
  if ! echo "$frontmatter" | grep -qE '^(tools|permissionMode|color|maxTurns|background):'; then
    _pass
  fi

  set_test "${agent}: system prompt body exists"
  body=$(awk 'BEGIN{n=0} /^---$/{n++; if(n==2){found=1; next}} found{print}' "$AGENT_FILE")
  body_trimmed=$(echo "$body" | sed '/^[[:space:]]*$/d')
  if [ -n "$body_trimmed" ]; then _pass; else _fail "no system prompt body after frontmatter"; fi
done

section "codex-agents — Parity with Claude Code agents"

for agent in "${AGENTS[@]}"; do
  set_test "${agent}: has corresponding Claude Code agent"
  assert_file_exists "$PLUGIN_ROOT/agents/${agent}.md"
done

test_summary
```

- [ ] **Step 2: Create validate-codex-skills.sh**

Write `speckit-pro/tests/layer1-structural/validate-codex-skills.sh`:

```bash
#!/usr/bin/env bash
# validate-codex-skills.sh — Structural validation for Codex skill definitions
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

SKILLS_DIR="$PLUGIN_ROOT/codex-skills"
SKILLS=(speckit-autopilot speckit-coach)
ALLOWED_KEYS="name description"

for skill in "${SKILLS[@]}"; do
  SKILL_DIR="$SKILLS_DIR/$skill"
  SKILL_FILE="$SKILL_DIR/SKILL.md"

  section "codex-skills/${skill}/SKILL.md"

  set_test "${skill}: SKILL.md exists"
  assert_file_exists "$SKILL_FILE"

  if [ ! -f "$SKILL_FILE" ]; then continue; fi

  first_line=$(head -n1 "$SKILL_FILE")

  set_test "${skill}: YAML frontmatter present"
  assert_eq "---" "$first_line"

  frontmatter=$(awk '/^---$/{n++; if(n==1){next} if(n==2){exit}} n==1{print}' "$SKILL_FILE")

  set_test "${skill}: has name: field"
  assert_contains "$frontmatter" "name:"

  set_test "${skill}: has description: field"
  assert_contains "$frontmatter" "description:"

  set_test "${skill}: no Claude Code-only fields (user-invokable, license, argument-hint)"
  for bad_field in "user-invokable:" "license:" "argument-hint:"; do
    if echo "$frontmatter" | grep -q "^${bad_field}"; then
      _fail "Codex skill must not have Claude Code field '${bad_field}'"
      break
    fi
  done
  if ! echo "$frontmatter" | grep -qE '^(user-invokable|license|argument-hint):'; then
    _pass
  fi

  set_test "${skill}: agents/openai.yaml sidecar exists"
  assert_file_exists "$SKILL_DIR/agents/openai.yaml"

  set_test "${skill}: body word count between 500 and 8000"
  body=$(awk 'BEGIN{n=0} /^---$/{n++; if(n==2){found=1; next}} found{print}' "$SKILL_FILE")
  word_count=$(echo "$body" | wc -w | tr -d ' ')
  if [ "$word_count" -ge 500 ] && [ "$word_count" -le 8000 ]; then
    _pass
  else
    _fail "body is $word_count words (need 500-8000)"
  fi

  section "codex-skills/${skill} — Parity"

  set_test "${skill}: has corresponding Claude Code skill"
  assert_file_exists "$PLUGIN_ROOT/skills/${skill}/SKILL.md"
done

test_summary
```

- [ ] **Step 3: Create validate-codex-hooks.sh**

Write `speckit-pro/tests/layer1-structural/validate-codex-hooks.sh`:

```bash
#!/usr/bin/env bash
# validate-codex-hooks.sh — Structural validation for codex-hooks.json
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

HOOKS_FILE="$PLUGIN_ROOT/codex-hooks.json"

section "codex-hooks.json — File Existence"

set_test "codex-hooks.json exists"
assert_file_exists "$HOOKS_FILE"

section "codex-hooks.json — Valid JSON"

set_test "codex-hooks.json is valid JSON"
if python3 -m json.tool "$HOOKS_FILE" >/dev/null 2>&1; then
  _pass
else
  _fail "codex-hooks.json is not valid JSON"
fi

CONTENT=$(cat "$HOOKS_FILE")

section "codex-hooks.json — Structure"

set_test "has top-level hooks key"
assert_json_field_exists "$CONTENT" "hooks"

set_test "SessionStart event exists"
assert_json_field_exists "$CONTENT" "hooks.SessionStart"

set_test "hook entry has matcher field"
has_matcher=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
entry = data['hooks']['SessionStart'][0]
print('true' if 'matcher' in entry else 'false')
" 2>/dev/null)
assert_eq "true" "$has_matcher" "Codex hook entry should have matcher field"

set_test "hook has type: command"
hook_type=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
h = data['hooks']['SessionStart'][0]['hooks'][0]
print(h.get('type', ''))
" 2>/dev/null)
assert_eq "command" "$hook_type"

set_test "command field is non-empty"
cmd_val=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
h = data['hooks']['SessionStart'][0]['hooks'][0]
print(h.get('command', ''))
" 2>/dev/null)
if [ -n "$cmd_val" ]; then _pass; else _fail "command field is empty"; fi

set_test "has statusMessage field"
has_status=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
h = data['hooks']['SessionStart'][0]['hooks'][0]
print('true' if 'statusMessage' in h else 'false')
" 2>/dev/null)
assert_eq "true" "$has_status" "Codex hook should have statusMessage"

test_summary
```

- [ ] **Step 4: Make scripts executable and run them**

Run:
```bash
chmod +x speckit-pro/tests/layer1-structural/validate-codex-agents.sh
chmod +x speckit-pro/tests/layer1-structural/validate-codex-skills.sh
chmod +x speckit-pro/tests/layer1-structural/validate-codex-hooks.sh
bash speckit-pro/tests/layer1-structural/validate-codex-agents.sh
bash speckit-pro/tests/layer1-structural/validate-codex-skills.sh
bash speckit-pro/tests/layer1-structural/validate-codex-hooks.sh
```

Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add speckit-pro/tests/layer1-structural/validate-codex-agents.sh \
        speckit-pro/tests/layer1-structural/validate-codex-skills.sh \
        speckit-pro/tests/layer1-structural/validate-codex-hooks.sh
git commit -m "test(speckit-pro): add Codex agent, skill, and hooks structural validation"
```

---

### Task 8: Parity Test & Layer 5 Codex Tool Scoping

**Files:**
- Create: `speckit-pro/tests/layer1-structural/validate-codex-parity.sh`
- Modify: `speckit-pro/tests/layer5-tool-scoping/validate-tool-scoping.sh` (add Codex section)

- [ ] **Step 1: Create validate-codex-parity.sh**

Write `speckit-pro/tests/layer1-structural/validate-codex-parity.sh`:

```bash
#!/usr/bin/env bash
# validate-codex-parity.sh — Cross-platform parity checks
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

section "Version Parity"

set_test "Claude Code and Codex plugin.json versions match"
cc_ver=$(jq -r '.version' "$PLUGIN_ROOT/.claude-plugin/plugin.json" 2>/dev/null)
codex_ver=$(jq -r '.version' "$PLUGIN_ROOT/.codex-plugin/plugin.json" 2>/dev/null)
assert_eq "$cc_ver" "$codex_ver" "versions must match"

section "Agent Parity"

CC_AGENTS_DIR="$PLUGIN_ROOT/agents"
CODEX_AGENTS_DIR="$PLUGIN_ROOT/codex-agents"

for agent_file in "$CC_AGENTS_DIR"/*.md; do
  agent_name=$(basename "$agent_file")
  set_test "codex-agents/${agent_name} exists"
  assert_file_exists "$CODEX_AGENTS_DIR/$agent_name"
done

for agent_file in "$CODEX_AGENTS_DIR"/*.md; do
  agent_name=$(basename "$agent_file")
  set_test "agents/${agent_name} exists (reverse parity)"
  assert_file_exists "$CC_AGENTS_DIR/$agent_name"
done

section "Skill Parity"

for skill_dir in "$PLUGIN_ROOT"/skills/*/; do
  skill_name=$(basename "$skill_dir")
  set_test "codex-skills/${skill_name}/SKILL.md exists"
  assert_file_exists "$PLUGIN_ROOT/codex-skills/$skill_name/SKILL.md"
done

section "Shared Reference Integrity"

for codex_skill_dir in "$PLUGIN_ROOT"/codex-skills/*/; do
  skill_name=$(basename "$codex_skill_dir")
  cc_refs="$PLUGIN_ROOT/skills/$skill_name/references"
  if [ -d "$cc_refs" ]; then
    for ref_file in "$cc_refs"/*; do
      ref_name=$(basename "$ref_file")
      set_test "${skill_name}: shared reference ${ref_name} exists"
      assert_file_exists "$ref_file"
    done
  fi
done

test_summary
```

- [ ] **Step 2: Add Codex sandbox_mode validation to Layer 5**

Append to `speckit-pro/tests/layer5-tool-scoping/validate-tool-scoping.sh`, after the existing Claude Code sections and before `test_summary`. Read the file first to find the insertion point, then add:

```bash
# ─────────────────────────────────────────
# Codex Agent Sandbox Mode Validation
# ─────────────────────────────────────────

CODEX_AGENTS_DIR="$PLUGIN_ROOT/codex-agents"

if [ -d "$CODEX_AGENTS_DIR" ]; then

  section "Codex Agent Sandbox Mode Scoping"

  # Read-only analysts must have sandbox_mode: read-only
  for agent in codebase-analyst spec-context-analyst domain-researcher; do
    AGENT_FILE="$CODEX_AGENTS_DIR/${agent}.md"
    if [ -f "$AGENT_FILE" ]; then
      sandbox=$(extract_field "$AGENT_FILE" "sandbox_mode")
      set_test "codex ${agent}: sandbox_mode is read-only"
      assert_eq "read-only" "$sandbox" "${agent} must be read-only"
    fi
  done

  # Write agents must have sandbox_mode: workspace-write
  for agent in clarify-executor checklist-executor analyze-executor implement-executor phase-executor; do
    AGENT_FILE="$CODEX_AGENTS_DIR/${agent}.md"
    if [ -f "$AGENT_FILE" ]; then
      sandbox=$(extract_field "$AGENT_FILE" "sandbox_mode")
      set_test "codex ${agent}: sandbox_mode is workspace-write"
      assert_eq "workspace-write" "$sandbox" "${agent} must be workspace-write"
    fi
  done

fi
```

- [ ] **Step 3: Make parity script executable and run both**

Run:
```bash
chmod +x speckit-pro/tests/layer1-structural/validate-codex-parity.sh
bash speckit-pro/tests/layer1-structural/validate-codex-parity.sh
bash speckit-pro/tests/layer5-tool-scoping/validate-tool-scoping.sh
```

Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add speckit-pro/tests/layer1-structural/validate-codex-parity.sh \
        speckit-pro/tests/layer5-tool-scoping/validate-tool-scoping.sh
git commit -m "test(speckit-pro): add cross-platform parity and Codex sandbox scoping tests"
```

---

### Task 9: Wire Tests into run-all.sh

**Files:**
- Modify: `speckit-pro/tests/run-all.sh`

- [ ] **Step 1: Add --codex flag parsing**

In `speckit-pro/tests/run-all.sh`, add to the `while` loop after the `--ci` case:

```bash
    --codex) RUN_CODEX=true; shift ;;
```

And add the variable initialization after `CI_MODE=false`:

```bash
RUN_CODEX=false
```

- [ ] **Step 2: Add Codex tests to Layer 1 section**

In the Layer 1 section, after the existing `validate-pr-checks-sentinel.sh` entry, add a conditional block:

```bash
  # Codex structural tests (run with --codex or --all)
  if [ "$RUN_CODEX" = "true" ] || [ "$RUN_ALL" = "true" ]; then
    run_layer 1 "Codex Structural Validation" \
      "$TESTS_DIR/layer1-structural/validate-codex-plugin.sh" \
      "$TESTS_DIR/layer1-structural/validate-codex-marketplace.sh" \
      "$TESTS_DIR/layer1-structural/validate-codex-agents.sh" \
      "$TESTS_DIR/layer1-structural/validate-codex-skills.sh" \
      "$TESTS_DIR/layer1-structural/validate-codex-hooks.sh" \
      "$TESTS_DIR/layer1-structural/validate-codex-parity.sh"
  fi
```

- [ ] **Step 3: Run full suite with --codex**

Run: `bash speckit-pro/tests/run-all.sh --codex`

Expected: All Layer 1, 4, 5 tests pass including all new Codex tests.

- [ ] **Step 4: Run default mode (backward compatible)**

Run: `bash speckit-pro/tests/run-all.sh`

Expected: Only existing CC tests run. No Codex tests. Same pass count as before.

- [ ] **Step 5: Commit**

```bash
git add speckit-pro/tests/run-all.sh
git commit -m "test(speckit-pro): wire Codex structural tests into run-all.sh with --codex flag"
```

---

### Task 10: Release Automation

**Files:**
- Modify: `release-please-config.json`

- [ ] **Step 1: Add Codex plugin.json to extra-files**

Read `release-please-config.json` and add the Codex manifest to the `extra-files` array:

```json
{
  "packages": {
    "speckit-pro": {
      "release-type": "simple",
      "component": "speckit-pro",
      "changelog-path": "CHANGELOG.md",
      "bump-minor-pre-major": true,
      "extra-files": [
        {
          "type": "json",
          "path": ".claude-plugin/plugin.json",
          "jsonpath": "$.version"
        },
        {
          "type": "json",
          "path": ".codex-plugin/plugin.json",
          "jsonpath": "$.version"
        }
      ]
    }
  }
}
```

- [ ] **Step 2: Verify JSON validity**

Run: `python3 -m json.tool release-please-config.json > /dev/null && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add release-please-config.json
git commit -m "chore: add Codex plugin.json to release-please version sync"
```

---

### Task 11: Final Verification

- [ ] **Step 1: Run full test suite**

Run: `bash speckit-pro/tests/run-all.sh --codex`

Expected: All tests pass. Zero failures.

- [ ] **Step 2: Run default test suite (backward compatibility)**

Run: `bash speckit-pro/tests/run-all.sh`

Expected: Same pass count as before this feature branch. No regressions.

- [ ] **Step 3: Verify directory structure matches spec**

Run:
```bash
echo "=== Codex Plugin ==="
ls -la speckit-pro/.codex-plugin/
echo "=== Codex Agents ==="
ls speckit-pro/codex-agents/
echo "=== Codex Skills ==="
find speckit-pro/codex-skills -type f
echo "=== Codex Hooks ==="
ls speckit-pro/codex-hooks.json
echo "=== Codex Marketplace ==="
ls .agents/plugins/marketplace.json
echo "=== New Tests ==="
ls speckit-pro/tests/layer1-structural/validate-codex-*
```

Expected: All files present matching the spec's repository structure diagram.

- [ ] **Step 4: Verify git status is clean**

Run: `git status`
Expected: Clean working tree with all changes committed.
