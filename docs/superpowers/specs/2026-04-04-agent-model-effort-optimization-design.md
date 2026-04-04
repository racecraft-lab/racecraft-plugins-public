# Agent Model & Effort Optimization — Design Spec

**Goal:** Maximize cost efficiency with the highest possible quality across all speckit-pro agents and skills by assigning the right model and thinking effort to each component, restructuring the agent roster where beneficial, and building an automated eval framework to validate the changes.

**Approach:** Expert analysis of each component's role and complexity, validated by a new Layer 6 (Agent Efficiency) automated benchmark suite.

**Scope:** 8 existing agents, 2 skills, plus potential new agents identified during the roster audit.

---

## Table of Contents

1. [Current State & Audit](#current-state--audit)
2. [Model/Effort Assignments](#modeleffort-assignments)
3. [Roster Restructuring](#roster-restructuring)
4. [Layer 6 — Agent Efficiency Eval Framework](#layer-6--agent-efficiency-eval-framework)
5. [Implementation Strategy](#implementation-strategy)
6. [Out of Scope](#out-of-scope)

---

## Current State & Audit

### Current Configuration (10 components)

| Component | Type | Model | Effort | Other | Role |
|-----------|------|-------|--------|-------|------|
| `analyze-executor` | Agent | opus | high | maxTurns: 100 | Run /speckit.analyze, remediate ALL findings |
| `checklist-executor` | Agent | opus | high | maxTurns: 100 | Run /speckit.checklist domain, remediate gaps |
| `clarify-executor` | Agent | opus | high | maxTurns: 75 | Research + answer clarification questions |
| `implement-executor` | Agent | opus | max | maxTurns: 50, memory: project | TDD implementation of a single task |
| `codebase-analyst` | Agent | sonnet | medium | maxTurns: 25, background: true | Read-only codebase pattern analysis (consensus) |
| `domain-researcher` | Agent | sonnet | medium | maxTurns: 25, background: true | Web research for consensus resolution |
| `spec-context-analyst` | Agent | sonnet | medium | maxTurns: 25, background: true | Read-only spec/constitution analysis (consensus) |
| `phase-executor` | Agent | sonnet | medium | maxTurns: 50 | Run simple SpecKit phases via Skill tool |
| `speckit-autopilot` | Skill | *inherited* | *inherited* | — | Orchestrate 7-phase workflow, gate validation, consensus synthesis |
| `speckit-coach` | Skill | *inherited* | *inherited* | — | SDD methodology coaching, interactive Q&A |

### Problems Identified

1. **`phase-executor` effort too high** — it runs at `effort: medium` but its task is mechanical (run a Skill command, summarize output). Should be `low` to save tokens across 5+ phase runs per autopilot.
2. **Autopilot skill inherits user's model** — if a user runs autopilot on haiku or sonnet, the orchestrator makes gate/consensus decisions on a weaker model while spawning opus subagents. The orchestrator is arguably the *most* important component to get right. Skills cannot set `model`/`effort` in frontmatter (they run in the caller's context), so a runtime guard is needed.
3. **No cost delegation** — gate validation and consensus synthesis are done inline by the opus orchestrator. Gate validation is purely mechanical (run a bash script, parse JSON output) and could be delegated to a haiku agent. Consensus synthesis is structured comparison that sonnet handles well.
4. **No efficiency benchmarks** — there is no automated way to measure whether the current model/effort assignments are optimal or to detect regressions after changes.

---

## Model/Effort Assignments

### Decision Criteria

**Model selection:**
- **opus** — Tasks requiring creative reasoning, complex synthesis, or high-quality code output
- **sonnet** — Structured analysis, research aggregation, mechanical execution
- **haiku** — Pure lookup/validation tasks with well-defined inputs and outputs

**Effort selection:**
- **high** — Multi-step reasoning, code generation, remediation across files
- **medium** — Structured research/analysis with synthesis
- **low** — Mechanical execution, running commands, parsing output

### Recommended Changes

| Component | Current | Target | Change | Rationale |
|-----------|---------|--------|--------|-----------|
| `phase-executor` | sonnet/medium | sonnet/low | effort: medium → low | Mechanical — runs a Skill command and summarizes output. Low thinking needed |
| `speckit-autopilot` | *inherited* | opus/high (guarded) | +runtime model guard | Skills can't set model in frontmatter. Add a prerequisite check that stops execution if model < opus |
| All other agents | — | — | *no change* | Already correctly configured (verified against decision criteria) |

### Validated Assignments (no changes needed)

| Component | Model | Effort | Rationale |
|-----------|-------|--------|-----------|
| `analyze-executor` | opus | high | Remediates findings across multiple artifacts — correct |
| `checklist-executor` | opus | high | Gap remediation requires understanding spec intent — correct |
| `clarify-executor` | opus | high | Synthesizes research from multiple sources — correct |
| `implement-executor` | opus | max | TDD code generation is the highest-stakes agent — `max` exceeds the `high` baseline, correctly so |
| `codebase-analyst` | sonnet | medium | Read-only analysis for consensus — correct |
| `domain-researcher` | sonnet | medium | Structured web research for consensus — correct |
| `spec-context-analyst` | sonnet | medium | Read-only spec analysis for consensus — correct |
| `speckit-coach` | *inherited* | *inherited* | Conversational — should match user's session — correct |

### Cost Impact Estimate

- **Savings (effort tuning):** `phase-executor` drops from medium to low effort — ~30-40% fewer thinking tokens per phase run (5 phases per autopilot = meaningful)
- **Savings (delegation):** Gate validation moves from opus orchestrator inline to haiku/low agent. Consensus synthesis moves from opus inline to sonnet/high agent. See Roster Restructuring section.
- **New cost:** Autopilot model guard may require users to switch to opus before running — documented as a prerequisite, not a hidden cost
- **Net:** Meaningful cost reduction from delegation + phase-executor tuning, with no quality regression

---

## Roster Restructuring

### Splits Considered (Not Recommended)

**`clarify-executor` → researcher + synthesizer:**
The clarify session is interactive — the agent needs context from its own research to formulate answers. Splitting would require passing full research context between agents, adding latency and losing coherence for marginal savings.

**`checklist-executor` → runner + remediator:**
When a checklist domain passes clean (no gaps), opus tokens are wasted just running the command. But the remediation logic is tightly coupled to the checklist output — splitting would require the runner to serialize all gap context for the remediator. Flag for future consideration if checklists frequently pass clean.

### Merges Considered (Not Recommended)

**`codebase-analyst` + `spec-context-analyst` → single analyst:**
They have different tool sets (RepoPrompt vs basic file tools) and are spawned in **parallel** for consensus. Merging would serialize them, adding latency to every consensus round. The parallel benefit outweighs the overhead.

### New Agents

**1. `gate-validator`**
- **Model:** haiku | **Effort:** low
- **Role:** Runs gate validation scripts (marker checks, metric thresholds) and returns pass/fail with structured evidence
- **Why:** Currently the autopilot orchestrator runs gate checks inline, consuming opus tokens for purely mechanical work — parsing script output and checking thresholds. A haiku/low agent handles this for a fraction of the cost.
- **Tools:** Bash, Read, Grep
- **Estimated savings:** Gates run after every phase. 7 phases × opus→haiku delta = significant per autopilot run

**2. `consensus-synthesizer`**
- **Model:** sonnet | **Effort:** high
- **Role:** Takes the 3 consensus analyst outputs and synthesizes a single actionable answer with confidence assessment
- **Why:** Currently the autopilot orchestrator does this synthesis itself on opus. The synthesis is important (needs high effort) but structured enough for sonnet — it's comparing 3 answers and finding agreement, not generating novel reasoning. Offloading this frees the orchestrator's context window.
- **Tools:** Read (to read analyst outputs)
- **Estimated savings:** Moves synthesis from opus to sonnet. 3 consensus rounds per clarify/checklist/analyze phase.

### Final Roster (12 components)

| Agent | Status | Model | Effort |
|-------|--------|-------|--------|
| `analyze-executor` | Existing (verified) | opus | high |
| `checklist-executor` | Existing (verified) | opus | high |
| `clarify-executor` | Existing (verified) | opus | high |
| `implement-executor` | Existing (verified) | opus | max |
| `codebase-analyst` | Existing (verified) | sonnet | medium |
| `domain-researcher` | Existing (verified) | sonnet | medium |
| `spec-context-analyst` | Existing (verified) | sonnet | medium |
| `phase-executor` | Existing (tuned) | sonnet | low |
| `gate-validator` | **New** | haiku | low |
| `consensus-synthesizer` | **New** | sonnet | high |
| `speckit-autopilot` (skill) | Existing (guarded) | opus | high |
| `speckit-coach` (skill) | Existing (no change) | *inherited* | *inherited* |

---

## Layer 6 — Agent Efficiency Eval Framework

### Purpose

Measure whether each agent's model/effort configuration delivers the best quality-to-cost ratio. Layer 6 answers: "Is this agent doing its job well, and are we paying the right amount for it?"

### Metrics

Two dimensions per agent:

**Cost metrics (objective):**
- Input tokens consumed
- Output tokens consumed
- Thinking tokens consumed
- Wall-clock time
- Total estimated cost (using published per-token pricing)

**Quality metrics (per agent type):**

| Agent Category | Quality Signal |
|----------------|---------------|
| Executor agents (analyze, checklist, clarify, implement) | Task completion rate, marker remediation rate, test pass rate |
| Consensus analysts (codebase, domain, spec-context) | Answer relevance score (does the synthesizer use this answer?), evidence citation count |
| Gate validator | Accuracy vs manual gate check (false pass / false fail rate) |
| Consensus synthesizer | Agreement with majority analyst position, actionability of output |
| Phase executor | Phase completion rate, output completeness (files created, metrics reported) |

### Structure

```
speckit-pro/tests/layer6-efficiency/
├── run-efficiency-evals.sh          ← Entry point
├── fixtures/                        ← Standardized inputs per agent
│   ├── analyze-executor/
│   │   ├── input-prompt.md          ← Representative task prompt
│   │   └── expected-output.md       ← Quality baseline (human-validated)
│   ├── gate-validator/
│   └── ...
├── lib/
│   ├── token-counter.sh             ← Parse API usage from claude output
│   └── quality-scorer.sh            ← Compare output against baseline
└── results/                         ← Timestamped run results (gitignored)
    └── 2026-04-04T12:00:00.json
```

### Test Flow Per Agent

1. Load the agent's fixture (standardized input prompt that exercises its core capability)
2. Run the agent via `claude -p` with the agent's configured model/effort
3. Capture token usage from the API response metadata
4. Score output quality against the human-validated baseline
5. Record cost + quality in a structured JSON result

### Comparative Sweep Mode

To evaluate whether a different model/effort would be better, run the same fixture at multiple configurations:

```bash
# Is checklist-executor better at sonnet/high vs opus/high?
bash run-efficiency-evals.sh --agent checklist-executor --sweep
```

Sweep mode runs the fixture at every reasonable model/effort combination (opus/high, opus/medium, sonnet/high, sonnet/medium, haiku/high, haiku/medium) and produces a cost-vs-quality comparison table.

### Integration with Existing Test Suite

```bash
# Default: Layers 1, 4, 5 (unchanged)
bash tests/run-all.sh

# Efficiency evals only
bash tests/run-all.sh --layer 6

# Full comparative sweep
bash tests/run-all.sh --layer 6 --sweep
```

Layer 6 is **never** run in CI — it's a developer-local benchmarking tool, same category as Layers 2/3.

### Success Criteria

- Every agent's quality score meets or exceeds its current baseline (no regressions)
- Total cost per full autopilot run decreases (measured via sweep at current vs new config)
- New agents (`gate-validator`, `consensus-synthesizer`) meet quality baselines at their assigned model/effort

---

## Implementation Strategy

Three phases, ordered by risk:

### Phase 1: Effort Tuning + Model Guard (low risk)
Change `phase-executor` effort from medium to low. Add a runtime model guard to `speckit-autopilot` SKILL.md that checks the current model and stops with a clear message if the orchestrator is running on anything weaker than opus. Most agents are already correctly configured — this phase is small.

### Phase 2: New Agents + Orchestration Delegation (medium risk)
Create `gate-validator` (haiku/low) and `consensus-synthesizer` (sonnet/high) agent definitions. Update the autopilot skill's orchestration logic to delegate gate validation checks and consensus synthesis to these new agents instead of performing them inline. Add Layer 1 structural tests and Layer 5 tool-scoping tests for both new agents.

### Phase 3: Layer 6 Framework (independent)
Build the eval framework, create fixtures for all 12 components (10 existing + 2 new), establish quality baselines at current config, then validate the Phase 1-2 changes produce equal-or-better quality at lower cost.

---

## Out of Scope

- Changes to existing agent prompt/body content (only frontmatter fields). The autopilot skill body *is* modified in Phase 2 to delegate gate validation and consensus synthesis to the new agents — this is orchestration wiring, not content rewriting.
- Layer 2/3 trigger eval changes (covered by SPEC-005)
- Skill description optimization (covered by SPEC-005)
- Adding Layer 6 to CI (developer-local only)
- Changes to `speckit-coach` model/effort (conversational skill — inherits user session)

---

## Key Files

### Modified
- `speckit-pro/agents/phase-executor.md` — Change effort: medium → low
- `speckit-pro/skills/speckit-autopilot/SKILL.md` — Add runtime model guard (prerequisite check)
- `speckit-pro/tests/layer1-structural/validate-agents.sh` — Add structural tests for new agents
- `speckit-pro/tests/layer5-tool-scoping/validate-tool-scoping.sh` — Add tool scoping tests for new agents
- `speckit-pro/tests/run-all.sh` — Add Layer 6 integration

### New
- `speckit-pro/agents/gate-validator.md` — New agent (haiku/low)
- `speckit-pro/agents/consensus-synthesizer.md` — New agent (sonnet/high)
- `speckit-pro/tests/layer6-efficiency/run-efficiency-evals.sh` — Eval entry point
- `speckit-pro/tests/layer6-efficiency/fixtures/` — Per-agent test fixtures
- `speckit-pro/tests/layer6-efficiency/lib/token-counter.sh` — Token usage parser
- `speckit-pro/tests/layer6-efficiency/lib/quality-scorer.sh` — Output quality scorer

### Verified (no changes needed)
- `speckit-pro/agents/analyze-executor.md` — opus/high ✓
- `speckit-pro/agents/checklist-executor.md` — opus/high ✓
- `speckit-pro/agents/clarify-executor.md` — opus/high ✓
- `speckit-pro/agents/implement-executor.md` — opus/max ✓
- `speckit-pro/agents/codebase-analyst.md` — sonnet/medium ✓
- `speckit-pro/agents/domain-researcher.md` — sonnet/medium ✓
- `speckit-pro/agents/spec-context-analyst.md` — sonnet/medium ✓
- `speckit-pro/skills/speckit-coach/SKILL.md` — Inherits user session (by design) ✓
