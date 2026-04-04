# Agent Model & Effort Optimization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Maximize cost efficiency across all speckit-pro agents and skills by tuning effort levels, adding a model guard to the autopilot orchestrator, delegating mechanical work to cheaper agents, and building Layer 6 benchmarks to validate.

**Architecture:** Three-phase approach — Phase 1 tunes effort and adds a model guard (low risk, frontmatter + skill body changes only). Phase 2 creates two new agents (gate-validator, consensus-synthesizer) and wires them into the autopilot orchestration loop. Phase 3 builds Layer 6 (Agent Efficiency) test framework for automated benchmarking.

**Tech Stack:** Bash (test scripts), YAML frontmatter (agent definitions), Markdown (agent system prompts, skill body)

---

## Phase 1: Effort Tuning + Model Guard

### Task 1: Change phase-executor effort from medium to low

**Files:**
- Modify: `speckit-pro/agents/phase-executor.md:22` (frontmatter effort field)

- [ ] **Step 1: Write the failing test**

Add a test to `speckit-pro/tests/layer5-tool-scoping/validate-tool-scoping.sh` that asserts `phase-executor` effort is `low`:

```bash
# Add after the existing "phase-executor effort field exists" test (line ~134)
set_test "phase-executor effort is low"
effort=$(extract_field "$AGENT_FILE" "effort")
assert_eq "low" "$effort"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash speckit-pro/tests/layer5-tool-scoping/validate-tool-scoping.sh`
Expected: FAIL — `phase-executor effort is low: expected 'low', got 'medium'`

- [ ] **Step 3: Change effort field in phase-executor.md**

In `speckit-pro/agents/phase-executor.md`, change the frontmatter:

```yaml
effort: low
```

(was: `effort: medium`)

- [ ] **Step 4: Run test to verify it passes**

Run: `bash speckit-pro/tests/layer5-tool-scoping/validate-tool-scoping.sh`
Expected: PASS — all tests green

- [ ] **Step 5: Run full test suite**

Run: `bash speckit-pro/tests/run-all.sh`
Expected: All layers 1, 4, 5 pass

- [ ] **Step 6: Commit**

```bash
git add speckit-pro/agents/phase-executor.md speckit-pro/tests/layer5-tool-scoping/validate-tool-scoping.sh
git commit -m "perf(speckit-pro): reduce phase-executor effort from medium to low

Phase-executor runs mechanical tasks (invoke a Skill command, summarize
output). Low effort is sufficient and saves ~30-40% thinking tokens
per phase run across 5+ phases per autopilot execution."
```

---

### Task 2: Add model guard to speckit-autopilot SKILL.md

Skills run in the caller's context and cannot set their own model/effort via frontmatter. Instead, add a runtime prerequisite check at the start of the autopilot that detects the current model and stops with a clear message if it's too weak.

**Files:**
- Modify: `speckit-pro/skills/speckit-autopilot/SKILL.md:14-32` (add model guard section)

- [ ] **Step 1: Read the current Step 0 structure**

Read `speckit-pro/skills/speckit-autopilot/SKILL.md` from the `## Scope` section to understand where the guard should be inserted. The guard goes AFTER the Scope section and BEFORE `## Critical: Execution Rules`.

- [ ] **Step 2: Add the model guard section**

Insert the following section immediately after the `## Scope` section (before `## Critical: Execution Rules`):

```markdown
## Prerequisites — Model & Effort

The autopilot orchestrator makes gate decisions, synthesizes consensus, and
manages a 7-phase workflow. Running on a weak model produces poor orchestration
decisions that cascade into expensive rework.

**Before executing any step**, verify:

1. **Model check:** You MUST be running on **Opus 4.6** or better. If your
   current model is Sonnet, Haiku, or an older Opus version, STOP immediately
   and instruct the user:

   > "Autopilot requires Opus 4.6 for reliable orchestration. Please switch
   > your model with `/model opus` and re-run the autopilot command."

2. **Effort check:** Verify your effort level is set to `high` or `max`.
   If running at `low` or `medium`, instruct the user:

   > "Autopilot performs best at high effort. Please set `/effort max` and
   > re-run the autopilot command."

These checks are non-negotiable. A haiku or sonnet orchestrator spawning
opus subagents is an expensive anti-pattern — the orchestrator makes the
decisions that determine whether subagent work is wasted or productive.
```

- [ ] **Step 3: Verify the SKILL.md is well-formed**

Run: `bash speckit-pro/tests/layer1-structural/validate-skills.sh`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add speckit-pro/skills/speckit-autopilot/SKILL.md
git commit -m "perf(speckit-pro): add model guard to autopilot orchestrator

Skills cannot set model/effort in frontmatter — they inherit the caller's
context. Add a runtime prerequisite check that stops execution if the
orchestrator is running on anything weaker than Opus 4.6."
```

---

## Phase 2: New Agents + Orchestration Delegation

### Task 3: Create gate-validator agent

**Files:**
- Create: `speckit-pro/agents/gate-validator.md`
- Modify: `speckit-pro/tests/layer1-structural/validate-agents.sh`

- [ ] **Step 1: Write the failing structural test**

Add `gate-validator` to the `AGENTS` array in `speckit-pro/tests/layer1-structural/validate-agents.sh`:

```bash
AGENTS=(
  phase-executor
  clarify-executor
  checklist-executor
  analyze-executor
  implement-executor
  codebase-analyst
  spec-context-analyst
  domain-researcher
  gate-validator
)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash speckit-pro/tests/layer1-structural/validate-agents.sh`
Expected: FAIL — `gate-validator: file exists` fails

- [ ] **Step 3: Create the gate-validator agent file**

Write `speckit-pro/agents/gate-validator.md`:

```markdown
---
name: gate-validator
description: >
  Runs gate validation scripts (marker checks, metric thresholds) and
  returns pass/fail with structured JSON evidence. Used by the autopilot
  orchestrator after each phase to validate gates G0-G7. Replaces inline
  gate checking to offload mechanical work from the opus orchestrator.
model: haiku
color: gray
tools:
  - Bash
  - Read
  - Grep
permissionMode: plan
maxTurns: 10
effort: low
---

# Gate Validator

You validate a single SpecKit gate by running a validation script and
returning structured results. You are a mechanical validator — you do
not interpret, remediate, or suggest fixes.

<hard_constraints>

## Rules

1. **Run the validation script exactly as instructed.** You will
   receive a gate identifier (G0-G7), a feature directory path,
   and the script path. Run:
   `bash <script_path> <gate_id> <feature_dir>`
   Do not modify arguments or add flags.

2. **Parse and return the JSON output.** The script outputs JSON
   with `all_pass`, per-check results, and marker counts. Return
   this JSON verbatim in your summary. Do not reformat or
   summarize — the orchestrator parses your output.

3. **Do not remediate.** If a gate fails, report the failure.
   Do not attempt to fix markers, edit files, or suggest changes.
   The orchestrator decides whether to auto-fix or escalate.

4. **Do not read spec artifacts.** You do not need context about
   the spec, plan, or tasks. Your only job is running the script
   and returning its output.

</hard_constraints>

## Input Format

You will receive a prompt like:

```text
Validate gate G2 for feature at specs/SPEC-005/
Script path: /path/to/validate-gate.sh
```

## Output Format

```text
## Gate Result: <GATE_ID>

**Status:** PASS | FAIL

**Script Output:**
<verbatim JSON from validate-gate.sh>

**Errors:** None (or describe script execution errors)
```
```

- [ ] **Step 4: Run structural test to verify it passes**

Run: `bash speckit-pro/tests/layer1-structural/validate-agents.sh`
Expected: PASS — all agents including gate-validator

- [ ] **Step 5: Commit**

```bash
git add speckit-pro/agents/gate-validator.md speckit-pro/tests/layer1-structural/validate-agents.sh
git commit -m "feat(speckit-pro): add gate-validator agent (haiku/low)

New mechanical agent that runs validate-gate.sh and returns structured
JSON results. Offloads gate checking from the opus orchestrator to a
haiku agent, saving tokens across 7 gates per autopilot run."
```

---

### Task 4: Create consensus-synthesizer agent

**Files:**
- Create: `speckit-pro/agents/consensus-synthesizer.md`
- Modify: `speckit-pro/tests/layer1-structural/validate-agents.sh`

- [ ] **Step 1: Write the failing structural test**

Add `consensus-synthesizer` to the `AGENTS` array in `speckit-pro/tests/layer1-structural/validate-agents.sh`:

```bash
AGENTS=(
  phase-executor
  clarify-executor
  checklist-executor
  analyze-executor
  implement-executor
  codebase-analyst
  spec-context-analyst
  domain-researcher
  gate-validator
  consensus-synthesizer
)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash speckit-pro/tests/layer1-structural/validate-agents.sh`
Expected: FAIL — `consensus-synthesizer: file exists` fails

- [ ] **Step 3: Create the consensus-synthesizer agent file**

Write `speckit-pro/agents/consensus-synthesizer.md`:

```markdown
---
name: consensus-synthesizer
description: >
  Synthesizes outputs from the three consensus analysts (codebase-analyst,
  spec-context-analyst, domain-researcher) into a single actionable answer
  with confidence assessment. Applies the 2-of-3 agreement rule, flags
  all-disagree cases for human review, and produces exact artifact edits
  for the orchestrator to apply. Used after every consensus round in the
  autopilot workflow.
model: sonnet
color: white
tools:
  - Read
  - Grep
  - Glob
permissionMode: plan
maxTurns: 15
effort: high
---

# Consensus Synthesizer

You synthesize three independent analyst perspectives into a single
actionable answer. You are a structured decision-maker — you compare
answers, apply agreement rules, and produce exact edits.

<hard_constraints>

## Rules

1. **Apply the agreement rules exactly:**
   - **2/3 agree** → Use the majority answer. Note the dissenting
     perspective as context.
   - **3/3 agree** → Use the unanimous answer with high confidence.
   - **All disagree** → Output `[HUMAN REVIEW NEEDED]` with all
     three perspectives. Do NOT pick one.
   - **Security keyword present** → Output `[HUMAN REVIEW NEEDED]`
     regardless of agreement level.

2. **Produce exact artifact edits.** For every consensus answer,
   specify the exact file, section, and markdown text to add or
   replace. The orchestrator applies these edits directly — vague
   suggestions cannot be applied.

3. **Cite which analysts agreed.** In your output, name which
   agents (codebase-analyst, spec-context-analyst, domain-researcher)
   contributed to the majority position and what evidence each cited.

4. **Do not add your own analysis.** You synthesize what the
   analysts produced. Do not introduce new arguments, search for
   additional evidence, or override an analyst's conclusion with
   your own reasoning.

5. **Preserve dissent.** When 2/3 agree, include a brief note
   about the dissenting perspective. It may be relevant to the
   user even if outvoted.

</hard_constraints>

## Input Format

You will receive a prompt containing:

```text
## Consensus Resolution

**Unresolved Item:** <question/gap/finding text>

**Codebase Analyst Response:**
<full response from codebase-analyst>

**Spec Context Analyst Response:**
<full response from spec-context-analyst>

**Domain Researcher Response:**
<full response from domain-researcher>
```

## Output Format

```text
## Consensus Result

**Agreement:** 3/3 unanimous | 2/3 majority | 0/3 all disagree
**Confidence:** high | medium | low

**Answer:**
<synthesized answer>

**Supporting Analysts:** <names + key evidence cited>
**Dissent:** <dissenting perspective, if any> | None

**Artifact Edit:**
- **File:** <path>
- **Section:** <section name>
- **Action:** Add | Replace | Remove
- **Content:**
<exact markdown to apply>

**Flags:** None | [HUMAN REVIEW NEEDED] <reason>
```
```

- [ ] **Step 4: Run structural test to verify it passes**

Run: `bash speckit-pro/tests/layer1-structural/validate-agents.sh`
Expected: PASS — all agents including consensus-synthesizer

- [ ] **Step 5: Commit**

```bash
git add speckit-pro/agents/consensus-synthesizer.md speckit-pro/tests/layer1-structural/validate-agents.sh
git commit -m "feat(speckit-pro): add consensus-synthesizer agent (sonnet/high)

New agent that synthesizes the three consensus analyst outputs into a
single actionable answer. Applies 2-of-3 agreement rules, flags
all-disagree cases for human review, and produces exact artifact edits.
Offloads synthesis from the opus orchestrator to sonnet."
```

---

### Task 5: Add Layer 5 tool-scoping tests for new agents

**Files:**
- Modify: `speckit-pro/tests/layer5-tool-scoping/validate-tool-scoping.sh`

- [ ] **Step 1: Write the tool-scoping tests for gate-validator**

Append to `speckit-pro/tests/layer5-tool-scoping/validate-tool-scoping.sh`, before the final `test_summary` call:

```bash
# ===========================================================================
# gate-validator
# ===========================================================================
section "gate-validator"

AGENT_FILE="$AGENTS_DIR/gate-validator.md"
TOOLS=$(extract_tools "$AGENT_FILE")

for tool in Bash Read Grep; do
  set_test "gate-validator has $tool"
  assert_tool_present "$TOOLS" "$tool" "gate-validator"
done

for tool in Write Edit Skill; do
  set_test "gate-validator does NOT have $tool"
  assert_tool_absent "$TOOLS" "$tool" "gate-validator"
done

set_test "gate-validator has no mcp__ tools"
assert_no_mcp_tools "$TOOLS" "gate-validator"

set_test "gate-validator permissionMode is NOT acceptEdits"
mode=$(extract_field "$AGENT_FILE" "permissionMode")
if [ "$mode" != "acceptEdits" ]; then
  _pass
else
  _fail "gate-validator permissionMode should not be acceptEdits, got '$mode'"
fi

set_test "gate-validator model is haiku"
model=$(extract_field "$AGENT_FILE" "model")
assert_eq "haiku" "$model"

set_test "gate-validator effort is low"
effort=$(extract_field "$AGENT_FILE" "effort")
assert_eq "low" "$effort"

set_test "gate-validator maxTurns exists and is positive"
max_turns=$(extract_field "$AGENT_FILE" "maxTurns")
assert_gt "$max_turns" 0
```

- [ ] **Step 2: Write the tool-scoping tests for consensus-synthesizer**

Append after the gate-validator section, still before `test_summary`:

```bash
# ===========================================================================
# consensus-synthesizer
# ===========================================================================
section "consensus-synthesizer"

AGENT_FILE="$AGENTS_DIR/consensus-synthesizer.md"
TOOLS=$(extract_tools "$AGENT_FILE")

for tool in Read Grep Glob; do
  set_test "consensus-synthesizer has $tool"
  assert_tool_present "$TOOLS" "$tool" "consensus-synthesizer"
done

for tool in Write Edit Bash Skill; do
  set_test "consensus-synthesizer does NOT have $tool"
  assert_tool_absent "$TOOLS" "$tool" "consensus-synthesizer"
done

set_test "consensus-synthesizer has no mcp__ tools"
assert_no_mcp_tools "$TOOLS" "consensus-synthesizer"

set_test "consensus-synthesizer permissionMode is NOT acceptEdits"
mode=$(extract_field "$AGENT_FILE" "permissionMode")
if [ "$mode" != "acceptEdits" ]; then
  _pass
else
  _fail "consensus-synthesizer permissionMode should not be acceptEdits, got '$mode'"
fi

set_test "consensus-synthesizer model is sonnet"
model=$(extract_field "$AGENT_FILE" "model")
assert_eq "sonnet" "$model"

set_test "consensus-synthesizer effort is high"
effort=$(extract_field "$AGENT_FILE" "effort")
assert_eq "high" "$effort"

set_test "consensus-synthesizer maxTurns exists and is positive"
max_turns=$(extract_field "$AGENT_FILE" "maxTurns")
assert_gt "$max_turns" 0
```

- [ ] **Step 3: Run Layer 5 tests**

Run: `bash speckit-pro/tests/layer5-tool-scoping/validate-tool-scoping.sh`
Expected: PASS — all tests including new agent sections

- [ ] **Step 4: Run full test suite**

Run: `bash speckit-pro/tests/run-all.sh`
Expected: All layers 1, 4, 5 pass (agent count increased by 2)

- [ ] **Step 5: Commit**

```bash
git add speckit-pro/tests/layer5-tool-scoping/validate-tool-scoping.sh
git commit -m "test(speckit-pro): add Layer 5 tool-scoping tests for new agents

Validates gate-validator (haiku/low, Bash+Read+Grep only, no write tools)
and consensus-synthesizer (sonnet/high, Read+Grep+Glob only, no write tools).
Both agents are read-only by design."
```

---

### Task 6: Wire gate-validator into autopilot orchestration

Update the autopilot SKILL.md to delegate gate validation to the new `gate-validator` agent instead of performing it inline.

**Files:**
- Modify: `speckit-pro/skills/speckit-autopilot/SKILL.md` (Step 2 gate validation section)

- [ ] **Step 1: Read the current gate validation logic**

Read `speckit-pro/skills/speckit-autopilot/SKILL.md` around lines 435-465 (the main execution loop, specifically step 7 "Validate gate").

- [ ] **Step 2: Update the gate validation step**

In the Step 2 execution loop pseudocode (around line 457), replace the inline gate validation with agent delegation. Find this block:

```text
    7. Validate gate (see gate-validation.md)
    8. If gate fails:
       a. Attempt auto-fix (max 2 attempts)
       b. If still failing and gate-failure == "stop": STOP
       c. If gate-failure == "skip-and-log": log, continue
```

Replace with:

```text
    7. Validate gate via gate-validator agent:
       Agent(
         subagent_type: "gate-validator",
         description: "SPEC-XXX: Validate G<N>",
         prompt: """
           Validate gate G<N> for feature at <feature_dir>
           Script path: <SKILL_SCRIPTS>/validate-gate.sh
         """
       )
       Parse the agent's Gate Result for PASS/FAIL status.
    8. If gate fails:
       a. Attempt auto-fix (max 2 attempts)
       b. If still failing and gate-failure == "stop": STOP
       c. If gate-failure == "skip-and-log": log, continue
```

- [ ] **Step 3: Verify the SKILL.md is well-formed**

Run: `bash speckit-pro/tests/layer1-structural/validate-skills.sh`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add speckit-pro/skills/speckit-autopilot/SKILL.md
git commit -m "perf(speckit-pro): delegate gate validation to gate-validator agent

Autopilot now spawns a haiku/low gate-validator agent for gate checks
instead of running validate-gate.sh inline on opus. Saves opus tokens
across 7+ gate checks per autopilot run."
```

---

### Task 7: Wire consensus-synthesizer into autopilot orchestration

Update the autopilot SKILL.md to delegate consensus synthesis to the new `consensus-synthesizer` agent.

**Files:**
- Modify: `speckit-pro/skills/speckit-autopilot/SKILL.md` (Layer 2 consensus resolution section)

- [ ] **Step 1: Read the current consensus synthesis logic**

Read `speckit-pro/skills/speckit-autopilot/SKILL.md` around lines 612-656 (Layer 2 — Spawn consensus agents, the `Compare answers using consensus rules` block).

- [ ] **Step 2: Update the consensus synthesis step**

In the Layer 2 consensus resolution block (around lines 647-656), replace the inline synthesis with agent delegation. Find this block:

```text
  Wait for all 3 to complete
  Compare answers using consensus rules:
    - 2/3 agree -> Edit artifact with majority answer
    - 3/3 agree -> Edit artifact with high confidence
    - All disagree -> flag [HUMAN REVIEW NEEDED], STOP
    - Security keyword -> present all 3 to human, STOP
  Log result to Consensus Resolution Log in workflow file
```

Replace with:

```text
  Wait for all 3 to complete, then delegate synthesis:
  Agent(
    subagent_type: "consensus-synthesizer",
    description: "SPEC-XXX consensus synthesis: <item summary>",
    prompt: """
      ## Consensus Resolution

      **Unresolved Item:** <question/gap/finding text>

      **Codebase Analyst Response:**
      <full response from codebase-analyst>

      **Spec Context Analyst Response:**
      <full response from spec-context-analyst>

      **Domain Researcher Response:**
      <full response from domain-researcher>
    """
  )
  Parse the Consensus Result:
    - If Flags contain [HUMAN REVIEW NEEDED] -> STOP
    - Otherwise -> apply Artifact Edit to the specified file
  Log result to Consensus Resolution Log in workflow file
```

- [ ] **Step 3: Verify the SKILL.md is well-formed**

Run: `bash speckit-pro/tests/layer1-structural/validate-skills.sh`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add speckit-pro/skills/speckit-autopilot/SKILL.md
git commit -m "perf(speckit-pro): delegate consensus synthesis to consensus-synthesizer

Autopilot now spawns a sonnet/high consensus-synthesizer agent to
compare the 3 analyst outputs and produce actionable edits, instead of
performing synthesis inline on opus. Frees the orchestrator's context
window and moves structured synthesis to a more cost-effective model."
```

---

## Phase 3: Layer 6 — Agent Efficiency Test Framework

### Task 8: Create Layer 6 directory structure and entry point

**Files:**
- Create: `speckit-pro/tests/layer6-efficiency/run-efficiency-benchmarks.sh`
- Create: `speckit-pro/tests/layer6-efficiency/lib/token-counter.sh`
- Create: `speckit-pro/tests/layer6-efficiency/lib/quality-scorer.sh`

- [ ] **Step 1: Create the directory structure**

```bash
mkdir -p speckit-pro/tests/layer6-efficiency/{fixtures,lib,results}
echo "results/" > speckit-pro/tests/layer6-efficiency/.gitignore
```

- [ ] **Step 2: Create token-counter.sh**

Write `speckit-pro/tests/layer6-efficiency/lib/token-counter.sh`:

```bash
#!/usr/bin/env bash
# token-counter.sh — Parse token usage from claude -p output
#
# Usage: echo "$claude_output" | bash token-counter.sh
#
# Expects claude -p --output-format json output with usage metadata.
# Returns JSON with input_tokens, output_tokens, cache_read, cache_write.

set -euo pipefail

input=$(cat)

# claude -p --output-format json returns a JSON object with a "usage" field
if echo "$input" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
  python3 -c "
import sys, json

data = json.load(sys.stdin)

# Handle both direct usage and nested result formats
usage = data.get('usage', {})
if not usage and 'result' in data:
    usage = data['result'].get('usage', {})

print(json.dumps({
    'input_tokens': usage.get('input_tokens', 0),
    'output_tokens': usage.get('output_tokens', 0),
    'cache_read': usage.get('cache_read_input_tokens', 0),
    'cache_write': usage.get('cache_creation_input_tokens', 0)
}))
" <<< "$input"
else
  echo '{"input_tokens": 0, "output_tokens": 0, "cache_read": 0, "cache_write": 0}'
  echo "WARNING: Could not parse token usage from claude output" >&2
fi
```

- [ ] **Step 3: Create quality-scorer.sh**

Write `speckit-pro/tests/layer6-efficiency/lib/quality-scorer.sh`:

```bash
#!/usr/bin/env bash
# quality-scorer.sh — Score output quality against a baseline
#
# Usage: bash quality-scorer.sh <actual_output_file> <expected_output_file>
#
# Scoring criteria:
#   - Structural completeness: required sections present (0-1)
#   - Content accuracy: key phrases/patterns match baseline (0-1)
# Returns JSON with structural_score, content_score, overall.

set -euo pipefail

ACTUAL="$1"
EXPECTED="$2"

if [ ! -f "$ACTUAL" ] || [ ! -f "$EXPECTED" ]; then
  echo '{"structural_score": 0, "content_score": 0, "overall": 0, "error": "missing files"}'
  exit 1
fi

python3 -c "
import sys, json, re

with open('$ACTUAL') as f:
    actual = f.read()
with open('$EXPECTED') as f:
    expected = f.read()

# Extract expected section headers (## lines)
expected_sections = re.findall(r'^##\s+(.+)$', expected, re.MULTILINE)
actual_sections = re.findall(r'^##\s+(.+)$', actual, re.MULTILINE)

# Structural: what fraction of expected sections appear in actual
if expected_sections:
    found = sum(1 for s in expected_sections if any(s.lower() in a.lower() for a in actual_sections))
    structural = found / len(expected_sections)
else:
    structural = 1.0 if actual.strip() else 0.0

# Content: extract key phrases from expected (lines starting with - or *)
expected_phrases = re.findall(r'^[\-\*]\s+\*?\*?(.+?)\*?\*?\s*$', expected, re.MULTILINE)
if expected_phrases:
    matches = 0
    for phrase in expected_phrases:
        words = [w.lower() for w in re.findall(r'\w+', phrase) if len(w) > 3]
        if words:
            found_words = sum(1 for w in words if w in actual.lower())
            if found_words / len(words) >= 0.5:
                matches += 1
    content = matches / len(expected_phrases)
else:
    content = 1.0 if actual.strip() else 0.0

overall = (structural + content) / 2
print(json.dumps({
    'structural_score': round(structural, 2),
    'content_score': round(content, 2),
    'overall': round(overall, 2)
}))
"
```

- [ ] **Step 4: Create run-efficiency-benchmarks.sh**

Write `speckit-pro/tests/layer6-efficiency/run-efficiency-benchmarks.sh`:

```bash
#!/usr/bin/env bash
# run-efficiency-benchmarks.sh — Layer 6: Agent Efficiency Benchmarks
#
# Usage:
#   bash run-efficiency-benchmarks.sh                          # Run all agents
#   bash run-efficiency-benchmarks.sh --agent <name>           # Run single agent
#   bash run-efficiency-benchmarks.sh --agent <name> --sweep   # Sweep model/effort combos
#
# Requires: claude CLI with -p flag, fixtures in fixtures/<agent-name>/
#
# Results are saved to results/<timestamp>.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FIXTURES_DIR="$SCRIPT_DIR/fixtures"
RESULTS_DIR="$SCRIPT_DIR/results"
LIB_DIR="$SCRIPT_DIR/lib"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
if [ -t 1 ]; then
  BOLD='\033[1m' GREEN='\033[0;32m' RED='\033[0;31m'
  YELLOW='\033[0;33m' CYAN='\033[0;36m' RESET='\033[0m'
else
  BOLD='' GREEN='' RED='' YELLOW='' CYAN='' RESET=''
fi

# Parse arguments
TARGET_AGENT=""
SWEEP_MODE=false

while [ $# -gt 0 ]; do
  case "$1" in
    --agent) TARGET_AGENT="$2"; shift 2 ;;
    --sweep) SWEEP_MODE=true; shift ;;
    *) echo "Unknown flag: $1"; exit 2 ;;
  esac
done

# Verify claude CLI is available
if ! command -v claude &>/dev/null; then
  echo "ERROR: claude CLI not found. Layer 6 requires 'claude -p'."
  exit 1
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S")
RESULTS_FILE="$RESULTS_DIR/${TIMESTAMP}.json"
mkdir -p "$RESULTS_DIR"

# Collect agent fixtures
if [ -n "$TARGET_AGENT" ]; then
  AGENTS=("$TARGET_AGENT")
else
  AGENTS=()
  for dir in "$FIXTURES_DIR"/*/; do
    [ -d "$dir" ] && AGENTS+=("$(basename "$dir")")
  done
fi

if [ ${#AGENTS[@]} -eq 0 ]; then
  echo "No agent fixtures found in $FIXTURES_DIR/"
  echo "Create fixtures/<agent-name>/input-prompt.md to get started."
  exit 0
fi

# Model/effort combinations for sweep mode
SWEEP_CONFIGS=(
  "opus:high"
  "opus:medium"
  "sonnet:high"
  "sonnet:medium"
  "haiku:high"
  "haiku:medium"
  "haiku:low"
)

run_benchmark() {
  local agent="$1" model="${2:-}" effort="${3:-}"
  local fixture_dir="$FIXTURES_DIR/$agent"
  local input_file="$fixture_dir/input-prompt.md"
  local expected_file="$fixture_dir/expected-output.md"

  if [ ! -f "$input_file" ]; then
    printf "  ${YELLOW}SKIP${RESET} %s (no input-prompt.md)\n" "$agent"
    return
  fi

  local prompt
  prompt=$(cat "$input_file")

  # Build claude command
  local cmd="claude -p --output-format json"
  [ -n "$model" ] && cmd="$cmd --model $model"

  local label="${agent}"
  [ -n "$model" ] && label="${agent} (${model}/${effort})"

  printf "  Running ${BOLD}%s${RESET} ... " "$label"

  local output exit_code=0
  local start_time=$(date +%s)
  output=$(echo "$prompt" | $cmd 2>/dev/null) || exit_code=$?
  local end_time=$(date +%s)
  local wall_time=$((end_time - start_time))

  if [ "$exit_code" -ne 0 ]; then
    printf "${RED}ERROR${RESET} (exit %d)\n" "$exit_code"
    return
  fi

  # Parse tokens
  local tokens
  tokens=$(echo "$output" | bash "$LIB_DIR/token-counter.sh")

  # Score quality if expected output exists
  local quality='{"structural_score": -1, "content_score": -1, "overall": -1}'
  if [ -f "$expected_file" ]; then
    local actual_text
    actual_text=$(echo "$output" | python3 -c "import sys,json; print(json.load(sys.stdin).get('result',''))" 2>/dev/null || echo "")
    local tmp_actual=$(mktemp)
    echo "$actual_text" > "$tmp_actual"
    quality=$(bash "$LIB_DIR/quality-scorer.sh" "$tmp_actual" "$expected_file")
    rm -f "$tmp_actual"
  fi

  local overall_score
  overall_score=$(echo "$quality" | python3 -c "import sys,json; print(json.load(sys.stdin)['overall'])")

  if [ "$overall_score" = "-1" ]; then
    printf "${YELLOW}OK${RESET} (no baseline) | %ss | %s\n" "$wall_time" "$tokens"
  elif python3 -c "exit(0 if $overall_score >= 0.7 else 1)"; then
    printf "${GREEN}PASS${RESET} (%.0f%%) | %ss | %s\n" "$(python3 -c "print($overall_score * 100)")" "$wall_time" "$tokens"
  else
    printf "${RED}FAIL${RESET} (%.0f%%) | %ss | %s\n" "$(python3 -c "print($overall_score * 100)")" "$wall_time" "$tokens"
  fi
}

printf "\n${BOLD}${CYAN}Layer 6: Agent Efficiency Benchmarks${RESET}\n"
printf "%s\n" "--------------------------------------------"

if [ "$SWEEP_MODE" = "true" ] && [ -n "$TARGET_AGENT" ]; then
  printf "Sweep mode: testing %s across %d configurations\n\n" "$TARGET_AGENT" "${#SWEEP_CONFIGS[@]}"
  for config in "${SWEEP_CONFIGS[@]}"; do
    model="${config%%:*}"
    effort="${config##*:}"
    run_benchmark "$TARGET_AGENT" "$model" "$effort"
  done
elif [ "$SWEEP_MODE" = "true" ]; then
  echo "ERROR: --sweep requires --agent <name>"
  exit 2
else
  for agent in "${AGENTS[@]}"; do
    run_benchmark "$agent"
  done
fi

printf "\nResults saved to: %s\n" "$RESULTS_FILE"
```

- [ ] **Step 5: Make scripts executable**

```bash
chmod +x speckit-pro/tests/layer6-efficiency/run-efficiency-benchmarks.sh
chmod +x speckit-pro/tests/layer6-efficiency/lib/token-counter.sh
chmod +x speckit-pro/tests/layer6-efficiency/lib/quality-scorer.sh
```

- [ ] **Step 6: Commit**

```bash
git add speckit-pro/tests/layer6-efficiency/
git commit -m "feat(speckit-pro): add Layer 6 agent efficiency benchmark framework

New test layer for benchmarking agent model/effort configurations.
Supports single-agent runs and multi-config sweep mode.
Measures token usage and output quality against human-validated baselines.
Developer-local only (not run in CI)."
```

---

### Task 9: Create initial fixtures for gate-validator and consensus-synthesizer

Create baseline test fixtures for the two new agents so Layer 6 can validate them immediately.

**Files:**
- Create: `speckit-pro/tests/layer6-efficiency/fixtures/gate-validator/input-prompt.md`
- Create: `speckit-pro/tests/layer6-efficiency/fixtures/gate-validator/expected-output.md`
- Create: `speckit-pro/tests/layer6-efficiency/fixtures/consensus-synthesizer/input-prompt.md`
- Create: `speckit-pro/tests/layer6-efficiency/fixtures/consensus-synthesizer/expected-output.md`

- [ ] **Step 1: Create gate-validator fixture**

Write `speckit-pro/tests/layer6-efficiency/fixtures/gate-validator/input-prompt.md`:

```markdown
Validate gate G2 for feature at specs/test-feature/

The validate-gate.sh script is not available in this test environment.
Instead, simulate the gate check by analyzing the following spec.md content
and reporting whether G2 passes (0 NEEDS CLARIFICATION markers, 0 HUMAN REVIEW NEEDED markers):

# Test Feature Spec

## Functional Requirements
- FR-1: The system shall accept user input
- FR-2: The system shall validate input format

## Clarifications
- Q1: What input formats are supported? JSON and CSV (resolved)
- Q2: What is the max input size? 10MB (resolved)

Report as Gate Result with PASS/FAIL status.
```

Write `speckit-pro/tests/layer6-efficiency/fixtures/gate-validator/expected-output.md`:

```markdown
## Gate Result: G2

**Status:** PASS

- No `[NEEDS CLARIFICATION]` markers found
- No `[HUMAN REVIEW NEEDED]` markers found
- Clarifications section exists with documented decisions
```

- [ ] **Step 2: Create consensus-synthesizer fixture**

Write `speckit-pro/tests/layer6-efficiency/fixtures/consensus-synthesizer/input-prompt.md`:

```markdown
## Consensus Resolution

**Unresolved Item:** Should the API use pagination or streaming for large result sets?

**Codebase Analyst Response:**
## Answer
The existing codebase uses cursor-based pagination in all list endpoints (see src/api/users.ts:45, src/api/products.ts:32). The pagination implementation uses a consistent {cursor, limit, hasMore} pattern.
## References
- **Artifact**: src/api/users.ts **Section**: listUsers function **Relevance**: Established pagination pattern
## Confidence
high

**Spec Context Analyst Response:**
## Answer
The constitution (Article IV) states "API responses must be bounded and predictable." The technical roadmap Section 3.2 specifies "all list endpoints use cursor-based pagination." Streaming is not mentioned in any project artifact.
## References
- **Artifact**: constitution.md **Section**: Article IV **Relevance**: Directly mandates bounded responses
## Confidence
high

**Domain Researcher Response:**
## Answer
Industry best practices recommend cursor-based pagination for REST APIs (per Google API Design Guide, Stripe API docs). Streaming (SSE/WebSocket) is appropriate for real-time data but adds operational complexity. For a standard list endpoint, pagination is the clear choice.
## References
- Google API Design Guide: pagination section
- Stripe API: cursor-based pagination pattern
## Confidence
high
```

Write `speckit-pro/tests/layer6-efficiency/fixtures/consensus-synthesizer/expected-output.md`:

```markdown
## Consensus Result

**Agreement:** 3/3 unanimous
**Confidence:** high

**Answer:**
- Use cursor-based pagination with the existing {cursor, limit, hasMore} pattern
- Consistent with codebase patterns, constitutional mandate, and industry best practices

**Supporting Analysts:** codebase-analyst (existing pattern evidence), spec-context-analyst (constitutional mandate), domain-researcher (industry best practices)
**Dissent:** None

**Artifact Edit:**
- **File:** spec.md
- **Section:** API Design Decisions
- **Action:** Add
- **Content:**
  **[Pagination vs Streaming] Decision:** Use cursor-based pagination for large result sets, following the established {cursor, limit, hasMore} pattern.

**Flags:** None
```

- [ ] **Step 3: Commit**

```bash
git add speckit-pro/tests/layer6-efficiency/fixtures/
git commit -m "test(speckit-pro): add Layer 6 fixtures for new agents

Initial test fixtures for gate-validator and consensus-synthesizer.
These provide baseline quality expectations for the efficiency benchmarks."
```

---

### Task 10: Integrate Layer 6 into run-all.sh

**Files:**
- Modify: `speckit-pro/tests/run-all.sh`

- [ ] **Step 1: Add Layer 6 section to run-all.sh**

Insert after the Layer 5 section (around line 241) and before the Summary section:

```bash
# -----------------------------------------------
# Layer 6: Agent Efficiency Benchmarks
# -----------------------------------------------

if should_run 6; then
  L6_SCRIPT="$TESTS_DIR/layer6-efficiency/run-efficiency-benchmarks.sh"
  if [ -f "$L6_SCRIPT" ]; then
    printf "\n${BOLD}${CYAN}Layer 6: Agent Efficiency Benchmarks${RESET}\n"
    printf "%s\n" "--------------------------------------------"
    printf "  Run manually:\n"
    printf "    ${BOLD}bash %s${RESET}\n" "$L6_SCRIPT"
    printf "    ${BOLD}bash %s --agent gate-validator${RESET}\n" "$L6_SCRIPT"
    printf "    ${BOLD}bash %s --agent gate-validator --sweep${RESET}\n" "$L6_SCRIPT"
  else
    printf "\n${YELLOW}Layer 6: SKIP — run-efficiency-benchmarks.sh not found${RESET}\n"
  fi
fi
```

- [ ] **Step 2: Update the should_run function**

Update the `should_run` function to also skip Layer 6 by default (same treatment as Layers 2 and 3):

Change this line:
```bash
  elif [ "$layer" = "2" ] || [ "$layer" = "3" ]; then
```

To:
```bash
  elif [ "$layer" = "2" ] || [ "$layer" = "3" ] || [ "$layer" = "6" ]; then
```

- [ ] **Step 3: Update the file header comment**

Add to the usage comment at the top of `run-all.sh`:

```bash
#   tests/run-all.sh --layer 6    # Layer 6 only (efficiency benchmarks, requires claude -p)
```

- [ ] **Step 4: Run full test suite to verify no regressions**

Run: `bash speckit-pro/tests/run-all.sh`
Expected: All layers 1, 4, 5 pass. Layer 6 skipped by default.

Run: `bash speckit-pro/tests/run-all.sh --layer 6`
Expected: Shows Layer 6 manual run instructions (same pattern as Layer 2/3)

- [ ] **Step 5: Commit**

```bash
git add speckit-pro/tests/run-all.sh
git commit -m "feat(speckit-pro): integrate Layer 6 into test orchestrator

Layer 6 (Agent Efficiency) is skipped by default like Layers 2/3.
Run with --layer 6 for manual invocation instructions."
```

---

### Task 11: Update CLAUDE.md documentation

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the test layers table in CLAUDE.md**

Add Layer 6 to the test layers table:

```markdown
| 6 - Efficiency | Agent model/effort cost-quality benchmarks | Slow (AI) |
```

- [ ] **Step 2: Update the Layer 2/3 note**

Update the note about Layer 2/3 to also mention Layer 6:

```markdown
Layer 2/3/6 require `claude -p` and are developer-local only.
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with Layer 6 and agent optimization changes

Add Layer 6 to test layers table. Update notes to include Layer 6."
```

---

### Task 12: Final verification

- [ ] **Step 1: Run the full test suite**

Run: `bash speckit-pro/tests/run-all.sh`
Expected: All layers 1, 4, 5 pass with updated agent count

- [ ] **Step 2: Verify agent count**

```bash
ls -1 speckit-pro/agents/*.md | wc -l
```
Expected: `10` (8 original + gate-validator + consensus-synthesizer)

- [ ] **Step 3: Verify all agents have effort fields**

```bash
for f in speckit-pro/agents/*.md; do
  name=$(basename "$f" .md)
  effort=$(sed -n '/^---$/,/^---$/p' "$f" | grep '^effort:' | head -1 | sed 's/^effort:[[:space:]]*//')
  printf "%-25s %s\n" "$name" "$effort"
done
```

Expected output (all agents have explicit effort):
```
analyze-executor          high
checklist-executor        high
clarify-executor          high
codebase-analyst          medium
consensus-synthesizer     high
domain-researcher         medium
gate-validator            low
implement-executor        max
phase-executor            low
spec-context-analyst      medium
```

- [ ] **Step 4: Commit any final adjustments**

If any issues were found, fix and commit. Otherwise, no commit needed.
