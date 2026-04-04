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

| Component | Type | Model | Effort | Role |
|-----------|------|-------|--------|------|
| `analyze-executor` | Agent | opus | *none* | Run /speckit.analyze, remediate ALL findings |
| `checklist-executor` | Agent | opus | *none* | Run /speckit.checklist domain, remediate gaps |
| `clarify-executor` | Agent | opus | *none* | Research + answer clarification questions |
| `implement-executor` | Agent | opus | *none* | TDD implementation of a single task |
| `codebase-analyst` | Agent | sonnet | *none* | Read-only codebase pattern analysis (consensus) |
| `domain-researcher` | Agent | sonnet | *none* | Web research for consensus resolution |
| `spec-context-analyst` | Agent | sonnet | medium | Read-only spec/constitution analysis (consensus) |
| `phase-executor` | Agent | sonnet | *none* | Run simple SpecKit phases via Skill tool |
| `speckit-autopilot` | Skill | *inherited* | *inherited* | Orchestrate 7-phase workflow, gate validation, consensus synthesis |
| `speckit-coach` | Skill | *inherited* | *inherited* | SDD methodology coaching, interactive Q&A |

### Problems Identified

1. **7 of 8 agents have no `effort` setting** — they run at the platform default, wasting tokens on agents that don't need deep thinking and potentially under-thinking on agents that do.
2. **Skills inherit user's model** — if a user runs autopilot on haiku, the orchestrator makes gate/consensus decisions on haiku while spawning opus subagents. The orchestrator is arguably the *most* important component to get right.
3. **No cost signal** — without effort tuning, every opus agent burns the same token budget regardless of whether it's writing production code or running a mechanical phase command.
4. **Consensus analysts are uneven** — `spec-context-analyst` has `effort: medium` but the other two consensus agents (`codebase-analyst`, `domain-researcher`) don't, creating inconsistent quality across the consensus triad.

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

### Recommended Assignments

| Component | Model | Effort | Change | Rationale |
|-----------|-------|--------|--------|-----------|
| `analyze-executor` | opus | high | +effort | Remediates findings across multiple artifacts — needs deep reasoning |
| `checklist-executor` | opus | high | +effort | Gap remediation requires understanding spec intent + writing fixes |
| `clarify-executor` | opus | high | +effort | Synthesizes research from multiple sources into coherent answers |
| `implement-executor` | opus | high | +effort | TDD code generation is the highest-stakes agent — opus/high justified |
| `codebase-analyst` | sonnet | medium | +effort | Read-only but needs quality analysis for consensus. Aligns with spec-context-analyst |
| `domain-researcher` | sonnet | medium | +effort | Same tier as other consensus analysts. Structured web research |
| `spec-context-analyst` | sonnet | medium | *no change* | Already correctly configured |
| `phase-executor` | sonnet | low | +effort | Mechanical — runs a Skill command and summarizes output. Low thinking needed |
| `speckit-autopilot` | opus | high | +model, +effort | **Critical fix.** Orchestrator makes gate decisions, synthesizes consensus, manages 7-phase flow. Must not inherit a weak model from the user's session |
| `speckit-coach` | *inherited* | *inherited* | *no change* | Conversational — should match user's session. Forcing opus on a quick question wastes money |

### Cost Impact Estimate

- **Savings:** `phase-executor` drops from default to low effort — ~30-40% fewer thinking tokens per phase run (5 phases per autopilot = meaningful)
- **Neutral:** The 4 opus agents get explicit `high` effort, which is likely close to what they were doing by default, but now intentional
- **New cost:** `speckit-autopilot` now forces opus even if user is on sonnet. This is the right trade-off — a bad orchestration decision costs far more than the model difference
- **Net:** Slight cost reduction from phase-executor + consensus agent tuning, with reliability improvement from pinning the orchestrator

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
| `analyze-executor` | Existing (tuned) | opus | high |
| `checklist-executor` | Existing (tuned) | opus | high |
| `clarify-executor` | Existing (tuned) | opus | high |
| `implement-executor` | Existing (tuned) | opus | high |
| `codebase-analyst` | Existing (tuned) | sonnet | medium |
| `domain-researcher` | Existing (tuned) | sonnet | medium |
| `spec-context-analyst` | Existing (no change) | sonnet | medium |
| `phase-executor` | Existing (tuned) | sonnet | low |
| `gate-validator` | **New** | haiku | low |
| `consensus-synthesizer` | **New** | sonnet | high |
| `speckit-autopilot` (skill) | Existing (tuned) | opus | high |
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

### Phase 1: Model/Effort Tuning (low risk)
Add `effort` fields to the 7 agents missing them. Add `model` and `effort` to `speckit-autopilot` SKILL.md frontmatter. No behavioral changes — just making existing implicit defaults explicit.

### Phase 2: New Agents (medium risk)
Create `gate-validator` and `consensus-synthesizer` agent definitions. Update the autopilot skill's orchestration logic to delegate gate checks and consensus synthesis to these new agents instead of doing them inline.

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
- `speckit-pro/agents/analyze-executor.md` — Add effort: high
- `speckit-pro/agents/checklist-executor.md` — Add effort: high
- `speckit-pro/agents/clarify-executor.md` — Add effort: high
- `speckit-pro/agents/implement-executor.md` — Add effort: high
- `speckit-pro/agents/codebase-analyst.md` — Add effort: medium
- `speckit-pro/agents/domain-researcher.md` — Add effort: medium
- `speckit-pro/agents/phase-executor.md` — Add effort: low
- `speckit-pro/skills/speckit-autopilot/SKILL.md` — Add model: opus, effort: high

### New
- `speckit-pro/agents/gate-validator.md` — New agent (haiku/low)
- `speckit-pro/agents/consensus-synthesizer.md` — New agent (sonnet/high)
- `speckit-pro/tests/layer6-efficiency/run-efficiency-evals.sh` — Eval entry point
- `speckit-pro/tests/layer6-efficiency/fixtures/` — Per-agent test fixtures
- `speckit-pro/tests/layer6-efficiency/lib/token-counter.sh` — Token usage parser
- `speckit-pro/tests/layer6-efficiency/lib/quality-scorer.sh` — Output quality scorer

### Unchanged
- `speckit-pro/agents/spec-context-analyst.md` — Already configured correctly
- `speckit-pro/skills/speckit-coach/SKILL.md` — Inherits user session (by design)
