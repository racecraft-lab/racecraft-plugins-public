# speckit-pro Agent & Skill Orchestration Audit

**Author:** Maintainer (Fredrick Gabelmann) + Claude Code research agents
**Date:** 2026-04-30
**Branch:** `racecraft/grill-me-skill` (PR #26)
**Scope:** End-to-end audit of the speckit-pro plugin's orchestration architecture across both Claude Code and OpenAI Codex ecosystems — every skill, every subagent, every model/effort decision — grounded in primary-source documentation.

---

## TL;DR

The plugin's orchestration is **architecturally sound** in its core decision: a single main-thread orchestrator (the `speckit-autopilot` skill) fans out to focused leaf subagents and never nests them. This is the correct shape for both ecosystems, since Claude Code's runtime forbids nested subagent spawning (verbatim) and Codex's runtime defaults to `agents.max_depth = 1`.

Within that sound shape, the audit found **seven concrete gaps**:

1. **Tier 1 (ship now):** Claude `implement-executor` lacks research tools (`WebSearch`, `WebFetch`, `tavily`, `context7`, `RepoPrompt`). Tasks that need to look up library APIs, RFCs, or external docs have no way to do so.
2. **Tier 1 (ship now):** Codex `implement-executor` developer_instructions don't mention research tool availability — the agent inherits the workspace's tool surface but doesn't know to use it.
3. **Tier 1 (ship now):** A stale comment in Claude `implement-executor.md` says `effort: max` "requires Opus 4.6" — Opus 4.7 also supports `max`, and is the current default.
4. **Tier 2 (needs evals):** `phase-executor` runs three different cognitive workloads (Specify, Plan, Tasks) on a single model/effort tier (`sonnet`/`low`); Plan in particular is a complex architecture-decision task that may be under-provisioned.
5. **Tier 2 (needs evals):** All Claude executors with research duties (`clarify-executor`, `checklist-executor`, `analyze-executor`) declare `effort: high`, which is **below** the Opus 4.7 default of `xhigh`. This may be a deliberate cost trade-off, but it's undocumented as such.
6. **Tier 3 (defer / document):** No "trivial task" tier — every implementation task routes to `implement-executor` (Opus/`max`), even mechanical renames or one-line edits where Haiku would suffice. Adding a Haiku tier requires a task-complexity classifier and Layer 6 efficiency benchmarks.
7. **Documented but kept:** All 10 Claude plugin agents declare `permissionMode`, `hooks`, or both. Per Anthropic's Plugins doc these fields are **silently ignored** in plugin scope. We keep them in the source files to document intent (and so users who copy the agent into `~/.claude/agents/` get the right behavior), but the audit makes the silent-ignore behavior explicit so the maintainer doesn't expect them to take effect at plugin runtime.

This document ships **only Tier 1**. Tiers 2 and 3 require eval coverage (Layer 3 functional, Layer 6 efficiency) that runs `claude -p` outside this session and should be authored as a separate change with measurement-backed decisions.

---

## 1. Methodology and Sources

### 1.1 Primary documentation consulted

All quotes are verbatim from the URL listed; access date 2026-04-30 throughout.

| Source | Used for |
| :----- | :------- |
| https://code.claude.com/docs/en/sub-agents | Claude subagent depth, frontmatter spec, tool inheritance, plugin restrictions |
| https://code.claude.com/docs/en/skills | Skill frontmatter, body interpretation, triggering, token budgets, slash command merger |
| https://code.claude.com/docs/en/plugins | Plugin manifest, allowed directories, agent restrictions, settings.json honored keys |
| https://code.claude.com/docs/en/model-config | Effort levels per model, default effort, fallback rules |
| https://developers.openai.com/codex/config-reference | `[agents]` block, `max_depth`, `model_reasoning_effort` enum, `sandbox_mode` |
| https://developers.openai.com/codex/subagents | Codex TOML format, `developer_instructions` semantics |
| `docs/ai/research/codex-parity-research-2026-04-30.md` (this repo) | Pre-existing Codex parity research; reused, not redone |

The full primary-source pull is at `/tmp/agent-audit-docs-2026-04-30.md` (this session) and the orchestration inventory is at `/tmp/agent-orchestration-inventory-2026-04-30.md`. Both were authored by research subagents during this audit.

### 1.2 What we audited

- All **19 agent definition files** (10 Claude `agents/*.md` + 9 Codex `codex-agents/*.toml`)
- All **10 skill SKILL.md files** (3 Claude `skills/*/SKILL.md` + 7 Codex `codex-skills/*/SKILL.md`) plus every `references/` document each one cites
- All **6 slash commands** (`commands/*.md`)
- The full **autopilot phase routing** in `skills/speckit-autopilot/references/phase-execution.md`
- All **structural and tool-scoping tests** (`tests/layer1-structural/`, `tests/layer5-tool-scoping/`)

---

## 2. Primary-Source Findings (What the Docs Actually Say)

### 2.1 Subagent depth — the most load-bearing constraint

**Claude Code (Anthropic) — verbatim, repeated three times in `/en/sub-agents`:**

> "This prevents infinite nesting (subagents cannot spawn other subagents) while still gathering necessary context."

> "Subagents cannot spawn other subagents. If your workflow requires nested delegation, use [Skills](/en/skills) or [chain subagents](#chain-subagents) from the main conversation."

> "If `Agent` is omitted from the `tools` list entirely, the agent cannot spawn any subagents. … `Agent(agent_type)` has no effect in subagent definitions."

**Codex (OpenAI) — `agents.max_depth = 1` default**, configurable up to an unspecified ceiling. From the Codex parity research (Q5):

> `agents.max_threads = 6`, `agents.max_depth = 1`, `agents.job_max_runtime_seconds = 1800`

**Implication for speckit-pro:** orchestration MUST happen from the main thread (the autopilot skill's running session). Any subagent that calls `Agent(...)` is silently a no-op on Claude. This is why the autopilot architecture is correct: a single orchestrator fans out to focused leaf agents and synthesizes the results itself.

### 2.2 Plugin agent frontmatter restrictions — verbatim

From `/en/sub-agents`, *Choose the subagent scope*, in a `<Note>` block:

> "For security reasons, plugin subagents do not support the `hooks`, `mcpServers`, or `permissionMode` frontmatter fields. These fields are ignored when loading agents from a plugin."

This means:

- **`permissionMode`** declared in any of our 10 plugin agents (`agents/*.md`) is silently dropped at load time.
- **`hooks`** and **`mcpServers`** likewise.
- All other documented frontmatter — `tools`, `disallowedTools`, `model`, `effort`, `skills`, `memory`, `background`, `maxTurns`, `isolation`, `color`, `initialPrompt` — IS honored.

The remediation path per docs is to copy the agent file to `~/.claude/agents/` (user scope) where the fields are honored. That's not appropriate for a plugin, so we accept the silent-ignore. We keep `permissionMode` declarations in our source files because they (a) document author intent, (b) provide correct behavior if the file is copied to user scope, (c) are tested by Layer 5 to prevent accidental drift.

### 2.3 Effort levels — per-model support matrix

From `/en/model-config`, *Adjust effort level*, verbatim:

> "Effort is supported on Opus 4.7, Opus 4.6, and Sonnet 4.6. The available levels depend on the model:"

| Model                   | Levels                                  |
| :---------------------- | :-------------------------------------- |
| Opus 4.7                | `low`, `medium`, `high`, `xhigh`, `max` |
| Opus 4.6 and Sonnet 4.6 | `low`, `medium`, `high`, `max`          |

> "If you set a level the active model does not support, Claude Code falls back to the highest supported level at or below the one you set. For example, `xhigh` runs as `high` on Opus 4.6."

> "As of v2.1.117, the default effort is `xhigh` on Opus 4.7 and `high` on Opus 4.6 and Sonnet 4.6."

**Crucial nuance — Haiku has no documented effort support.** The doc lists effort for Opus 4.7 / Opus 4.6 / Sonnet 4.6 only. By absence, Haiku does not honor `effort`. Our `gate-validator` declares `effort: low` on Haiku — this is undocumented behavior and is most likely silently ignored.

**Codex effort enum** (https://developers.openai.com/codex/config-reference): `minimal | low | medium | high | xhigh`. There is **no `max`** level on Codex, asymmetric with Claude.

### 2.4 Tool inheritance — defaults for sub-agents

From `/en/sub-agents`, *Available tools*, verbatim:

> "Subagents can use any of Claude Code's internal tools. **By default, subagents inherit all tools from the main conversation, including MCP tools.**"

> "To restrict tools, use either the `tools` field (allowlist) or the `disallowedTools` field (denylist)."

> "If both are set, `disallowedTools` is applied first, then `tools` is resolved against the remaining pool. A tool listed in both is removed."

**Implication:** when we declare a `tools:` allowlist, we lock the subagent to only those tools — research tools must be enumerated explicitly. This is what bites `implement-executor` in Gap 1: the allowlist excludes research tools, so the agent cannot fall back to inherited MCP tools.

### 2.5 Slash commands have been merged into skills

From `/en/skills`, verbatim:

> "**Custom commands have been merged into skills.** A file at `.claude/commands/deploy.md` and a skill at `.claude/skills/deploy/SKILL.md` both create `/deploy` and work the same way. Your existing `.claude/commands/` files keep working. Skills add optional features: a directory for supporting files, frontmatter to control whether you or Claude invokes them, and the ability for Claude to load them automatically when relevant."

So our `commands/*.md` files use the same frontmatter shape as `skills/<name>/SKILL.md`, but lack a directory for supporting files. New code should use `skills/`.

### 2.6 Skill description budget

From `/en/skills`, *Skill descriptions are cut short*, verbatim:

> "All skill names are always included, but if you have many skills, descriptions are shortened to fit the character budget … **The budget scales dynamically at 1% of the context window, with a fallback of 8,000 characters.**"

> "each entry's combined text is **capped at 1,536 characters regardless of budget**."

For speckit-pro: with 3 Claude skills + 6 commands + 7 Codex skills, we are nowhere near the budget. But every skill should still front-load its key use case in the first 100–200 chars so trigger matching works under tight budgets.

### 2.7 Codex deltas (from existing parity research)

The full Codex specifics are in `docs/ai/research/codex-parity-research-2026-04-30.md`. Load-bearing facts for orchestration:

- **`agents.max_depth = 1`** by default (configurable).
- **Custom slash commands are deprecated** in Codex; skills replace them.
- **Codex skills require `name` + `description`** frontmatter; `allow_implicit_invocation` lives in `agents/openai.yaml` sidecar (default `true`).
- **Codex hooks** canonical bundled location is `<plugin>/hooks/hooks.json`. The repo currently has `speckit-pro/codex-hooks.json` at the plugin root, which is **not loaded** without an explicit `"hooks": "./codex-hooks.json"` field in `.codex-plugin/plugin.json` — confirm this is wired (cross-reference Q6 of codex-parity-research).
- **`gpt-5.4-mini` and `gpt-5.4`** are under-documented in OpenAI's public Codex docs; they appear in changelogs but not in a canonical "supported models" table. Our local validation regex allows them. Mark as a watch-item.

---

## 3. Plugin Architecture Overview

### 3.1 Two ecosystems, one shared shape

| Aspect             | Claude Code                       | OpenAI Codex                                   |
| :----------------- | :-------------------------------- | :--------------------------------------------- |
| Subagent files     | `agents/*.md` (10)                | `codex-agents/*.toml` (9)                      |
| Skill files        | `skills/<name>/SKILL.md` (3)      | `codex-skills/<name>/SKILL.md` (7)             |
| Slash commands     | `commands/*.md` (6)               | None (deprecated; skills replace them)         |
| Subagent depth     | Hard 0 (cannot nest)              | Default 1, configurable                        |
| Effort enum        | `low/medium/high/xhigh/max`       | `minimal/low/medium/high/xhigh`                |
| Sandbox/perm       | `permissionMode` (silently ignored in plugin) | `sandbox_mode: read-only / workspace-write` |
| Consensus          | Separate `consensus-synthesizer` agent | Inlined into orchestrator session         |
| Gate validation    | Separate `gate-validator` agent   | Inlined into orchestrator session              |

### 3.2 The "Orchestrator-Direct" pattern

Both ecosystems implement the same pattern: a single main-thread skill (`speckit-autopilot`) is the orchestrator. It dispatches focused leaf subagents one at a time (or in parallel for consensus), collects results, and never spawns further nesting. This is enforced by:

1. **Anthropic's runtime constraint** — subagents cannot spawn other subagents.
2. **Codex's `max_depth = 1` default** — same effect at depth 2+.
3. **Tool scoping** — every leaf agent's `tools:` allowlist excludes the `Agent` tool.
4. **Agent frontmatter** — every leaf agent's body explicitly states "do not invoke other agents/skills" where relevant (e.g., `grill-me` HITL guards).

The audit confirms this pattern is implemented correctly. The architectural preamble added in commit `0e10bac` makes it explicit in both `speckit-autopilot/SKILL.md` files.

---

## 4. Agent Catalog

### 4.1 Claude Code agents (10)

| Agent | Model | Effort | Tools (count + key research signal) | maxTurns | Role |
| :---- | :---- | :----- | :---------------------------------- | :------- | :--- |
| `implement-executor` | opus | max | 6 — **NO research tools** | 50 | Single-task TDD executor |
| `phase-executor` | sonnet | low | 7 — Skill, no research | 50 | Specify / Plan / Tasks runner |
| `clarify-executor` | opus | high | 15 — full research kit | 75 | Clarify session + research |
| `checklist-executor` | opus | high | 15 — full research kit | 100 | Checklist + gap remediation |
| `analyze-executor` | opus | high | 14 — full research kit (no tavily-extract) | 100 | Analyze + finding remediation |
| `codebase-analyst` | sonnet | medium | 7 — RepoPrompt + Read/Glob/Grep | 25 | Consensus: codebase perspective |
| `spec-context-analyst` | sonnet | medium | 3 — Read/Glob/Grep | 25 | Consensus: project decisions |
| `domain-researcher` | sonnet | medium | 7 — tavily/context7/Web/Read | 25 | Consensus: external best practices |
| `consensus-synthesizer` | sonnet | high | 3 — Read/Grep/Glob | 15 | 2-of-3 synthesis + edits |
| `gate-validator` | haiku | low | 3 — Bash/Read/Grep | 10 | Mechanical script runner |

### 4.2 Codex agents (9)

| Agent | Model | Effort | Sandbox | Role |
| :---- | :---- | :----- | :------ | :--- |
| `phase-executor` | gpt-5.4-mini | low | workspace-write | Specify / Plan / Tasks runner |
| `clarify-executor` | gpt-5.5 | high | workspace-write | Clarify + research |
| `checklist-executor` | gpt-5.5 | high | workspace-write | Checklist + remediation |
| `analyze-executor` | gpt-5.5 | high | workspace-write | Analyze + remediation |
| `implement-executor` | gpt-5.5 | high | workspace-write | TDD executor (effort bumped from `medium` in commit `0e10bac`) |
| `codebase-analyst` | gpt-5.5 | medium | read-only | Consensus: codebase perspective |
| `spec-context-analyst` | gpt-5.5 | medium | read-only | Consensus: project decisions |
| `domain-researcher` | gpt-5.5 | medium | read-only | Consensus: external best practices |
| `autopilot-fast-helper` | gpt-5.3-codex-spark | low | read-only | OPTIONAL leaf triage / compression |

**Note:** Codex has no `consensus-synthesizer` or `gate-validator` agent — both are inlined into the orchestrator session because Codex's `max_depth = 1` makes nested dispatch impractical when the orchestrator is itself a phase agent.

---

## 5. Skill-by-Skill Orchestration Map

### 5.1 `speckit-autopilot` (Claude + Codex)

**Mission:** End-to-end autonomous SDD execution. Orchestrates 7 phases (Specify → Clarify → Plan → Checklist → Tasks → Analyze → Implement) with gate validation between each.

**Plan / todo / progress tracking:**

- **Claude variant** uses `TaskCreate` / `TaskUpdate` to materialize the 7-phase work into the host session's task list, plus per-phase sub-tasks for consensus rounds and per-task implement dispatches. Status updates flow live to the user.
- **Codex variant** uses Codex's native `update_plan` primitive, persisted to `autopilot-state.json` so the orchestrator can resume cleanly after interrupts. The plan is rewritten before Phase 1 begins and after every phase transition.

Both variants converge on the same dispatch graph; only the persistence primitive differs.

**Pattern:** Main-thread orchestrator. Per phase:

| Phase     | Dispatched agent (Claude) | Model/Effort | Consensus on flagged items? |
| :-------- | :------------------------ | :----------- | :--------------------------- |
| Specify   | `phase-executor`          | sonnet/low   | No                           |
| Clarify   | `clarify-executor`        | opus/high    | Yes (if items unresolved)    |
| Plan      | `phase-executor`          | sonnet/low   | No                           |
| Checklist | `checklist-executor`      | opus/high    | Yes (if gaps remain)         |
| Tasks     | `phase-executor`          | sonnet/low   | No                           |
| Analyze   | `analyze-executor`        | opus/high    | Yes (if findings remain)     |
| Implement | per-task routing          | opus/max default | No (TDD enforced)         |

After every phase, dispatches `gate-validator` (haiku/low) to count markers and verify pass thresholds. After every phase that flags items, dispatches the three consensus analysts in parallel, then `consensus-synthesizer` (sonnet/high) to produce edits.

**Cognitive fit:**
- Specify, Plan, Tasks → `phase-executor` (sonnet/low). **Plan is the weakest fit.** Plan involves architecture decisions, data model design, and Phase 0 research; sonnet/low may be under-provisioned for complex specs.
- Clarify, Checklist, Analyze → opus/high. Below Opus 4.7 default of `xhigh`; deliberate cost trade-off but undocumented.
- Implement → opus/`max` default for all tasks. No tier for trivial mechanical work.

### 5.2 `speckit-coach` (Claude + Codex)

**Mission:** Methodology Q&A — explains SDD, presets, extensions, checklist domains, technical roadmap creation.

**Pattern:** Self-contained. **No subagents dispatched.** All coaching is provided directly from `references/*.md` documents loaded into the main session. Reads `.specify/presets/` and `.specify/extensions/` to tailor advice.

**Cognitive fit:** Appropriate. Coaching is conversational Q&A; it benefits from full context and shouldn't fan out.

### 5.3 `grill-me` (Claude + Codex)

**Mission:** Pre-spec interview. Walks design tree, one question at a time, recommends an answer, produces Design Concept doc.

**Pattern:** Self-contained, **strictly human-in-the-loop**. Hard-blocked from invocation inside autopilot via three layers of defense:
1. Negative constraints in autopilot SKILL.md and every phase agent's body
2. `disable-model-invocation` policy (Codex-side equivalent: `policy.allow_implicit_invocation: false`)
3. Skill-level self-check at activation (verifies `AskUserQuestion` is available on Claude; TTY check on Codex)

**Cognitive fit:** Correct. The skill MUST run in the main thread because it interacts with the user via `AskUserQuestion`. If forked into a subagent it would lose interactivity.

### 5.4 `speckit-setup` (Codex skill; Claude command)

**Mission:** Bootstrap a spec for autopilot — create branch, run grill-me, generate workflow file, commit.

**Pattern:**
- Claude: command file (`commands/setup.md`) executes inline in main session, invokes `grill-me` as a `Skill('grill-me')` call.
- Codex: skill (`codex-skills/speckit-setup/SKILL.md`) does the same flow.

**No other subagents dispatched.** All file operations and grill-me invocation happen in the main thread.

**Cognitive fit:** Correct. Setup is sequential (worktree → grill-me → workflow file) and depends on grill-me's interactive output, so it must stay in main.

### 5.5 `speckit-status` (Codex only)

**Mission:** Read-only project dashboard. Shows roadmap, active specs, blocked work.

**Pattern:** Self-contained, no subagents. Reads roadmap + workflow files + git worktree state.

**Cognitive fit:** Correct. Pure reporting; no need to fan out.

### 5.6 `speckit-resolve-pr` (Codex only)

**Mission:** Address PR review feedback, push fixes, resolve threads.

**Pattern:** Self-contained, no subagents. Uses `gh api` for GitHub interactions.

**Cognitive fit:** Correct for current scope. Could potentially benefit from delegating a "verify fix didn't break tests" subagent in future, but not urgent.

### 5.7 `install` (Codex only)

**Mission:** Copy bundled `codex-agents/*.toml` into `~/.codex/agents/`.

**Pattern:** File-copying utility. No subagents.

**Cognitive fit:** Correct. Mechanical operation.

### 5.8 Cross-skill summary

| Skill                | Spawns subagents? | Consensus? | Gate validation? | Self-contained? |
| :------------------- | :---------------- | :--------- | :--------------- | :-------------- |
| `speckit-autopilot`  | Yes (per-phase + 3 analysts + synthesizer + validator) | Yes | Yes | No (orchestrator) |
| `speckit-coach`      | No                | No         | No               | Yes             |
| `grill-me`           | No                | No         | No               | Yes (HITL)      |
| `speckit-setup`      | No (only invokes `grill-me` skill) | No | No | Yes |
| `speckit-status`     | No                | No         | No               | Yes             |
| `speckit-resolve-pr` | No                | No         | No               | Yes             |
| `install`            | No                | No         | No               | Yes             |

**Observation:** Only `speckit-autopilot` is a true orchestrator. Every other skill runs in a single thread. This is the right shape — orchestration overhead is only justified when the work decomposes into 7+ distinct phases with gates between them.

---

## 6. Architectural Gaps

### 6.1 Gap 1 (Tier 1) — `implement-executor` lacks research tools

**Current state (`agents/implement-executor.md`, lines 12–18):**

```yaml
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
```

**Problem:** Tasks that require looking up an external API, RFC, library version, or integration pattern have no way to do so. The agent must infer from codebase + TDD protocol + the task description alone. For tasks like "integrate OAuth via Okta" or "use the new OpenAI Responses API," this can result in hallucinated API surfaces or stale patterns.

**Why it happens:** The original design assumed implement-executor only writes code based on the spec/plan/tasks artifacts (which already capture decisions). But Phase 7 Implement is the only phase where research tools are systematically absent — every other research-capable phase (Clarify, Checklist, Analyze) has the full kit. The asymmetry is unintentional.

**Codex equivalent (`codex-agents/implement-executor.toml`):** No tool allowlist concept (Codex inherits the workspace tool surface), but `developer_instructions` doesn't mention research-tool availability, so the agent doesn't know to reach for `tavily-search`, `context7`, etc. when needed.

**Fix (Tier 1):**
- Claude: add `WebSearch`, `WebFetch`, `mcp__tavily-mcp__tavily-search`, `mcp__context7__resolve-library-id`, `mcp__context7__get-library-docs`, `mcp__RepoPrompt__file_search`, `mcp__RepoPrompt__context_builder` to the tool allowlist.
- Codex: update `developer_instructions` to enumerate research tools available in the Codex workspace and when to use them (mirroring the pattern in `codex-agents/clarify-executor.toml`).

**Risk:** Additive change — agent gains capabilities, default behavior unchanged. Worst case: agent over-researches simple tasks. Mitigated by the existing `<hard_constraints>` block that scopes the agent to one task at a time.

**Test impact:**
- **Layer 5** (`tests/layer5-tool-scoping/validate-tool-scoping.sh`): existing assertions check Read/Write/Edit/Bash/Grep/Glob are present and Skill is absent. Need to ADD assertions for the new research tools.
- **Layer 1** (`tests/layer1-structural/`): no tool-count pinning to update.

### 6.2 Gap 2 (Tier 1) — Stale Opus 4.6 comment

**Current state (`agents/implement-executor.md`, lines 31–32):**

```markdown
> **Note:** This agent uses `effort: max` which requires Opus 4.6.
> The parent session must use Opus 4.6 or this setting is ignored.
```

**Problem:** Per `/en/model-config`, Opus 4.7 supports `low/medium/high/xhigh/max` — `max` is supported on both 4.6 AND 4.7. The note understates the supported model range and may confuse users running 4.7.

**Fix:** Update note to mention both Opus 4.6 and 4.7 support `max`, and that `max` is session-only effort that overrides the session default.

### 6.3 Gap 3 (Tier 2) — `phase-executor` runs three different cognitive workloads

**Current state:** `phase-executor` (sonnet/low) is dispatched for Specify, Plan, AND Tasks phases. These are three different cognitive workloads:

| Phase   | Cognitive work                              | Typical artifact size |
| :------ | :------------------------------------------ | :-------------------- |
| Specify | Structured requirements writing             | 5k–20k tokens         |
| Plan    | Architecture decisions + data model + research | 20k–50k+ tokens   |
| Tasks   | Task decomposition from user stories        | 10k–30k tokens        |

**Problem:** sonnet/low is arguably under-provisioned for Plan, which involves Phase 0 research and architecture decisions. If plan.md is weak, downstream gates (G2, G3, G5) fail more often and trigger expensive remediation loops on opus/high agents.

**Why we don't ship this:** Cost-vs-quality is unverifiable from frontmatter alone. The fix could be:
- (a) Promote `phase-executor` to sonnet/medium globally (cheap, marginal quality change)
- (b) Promote to opus/low for Plan only (adds a new agent or per-phase override)
- (c) Promote to sonnet/medium for Plan only (per-phase override)

Without **Layer 6 efficiency benchmarks** measuring G2 pass rate at each model/effort, we can't pick. The advisor's prior guidance applies: model/effort changes need eval-backed decisions.

**Recommended next step:** Author 3 representative complex specs, run them through Plan phase at sonnet/low, sonnet/medium, opus/low. Measure G2 pass rate, downstream remediation loop count, and total token cost. Pick the Pareto-optimal point.

### 6.4 Gap 4 (Tier 2) — Effort below default on Opus 4.7

**Current state:** `clarify-executor`, `checklist-executor`, `analyze-executor` declare `effort: high`. Per docs, Opus 4.7's default is `xhigh`. So these agents are explicitly DOWNGRADING from the session default.

**Problem:** Either this is deliberate (cost trade-off) or accidental (the file pre-dates Opus 4.7). The frontmatter doesn't say which.

**Why we don't ship this:** Same reason as Gap 3 — the trade-off is real (xhigh costs more), and we need eval data to make the call. Gap-remediation loops on these agents are already the most expensive operations in autopilot; bumping effort could make them disproportionately more expensive without proportional quality gains.

**Recommended next step:** Run Layer 6 efficiency benchmarks on a representative spec at `effort: high` vs `effort: xhigh` for these three agents. Measure: gate pass rate, total tokens, total wall time, total dollar cost. Decide based on quality-per-dollar.

### 6.5 Gap 5 (Tier 3) — No trivial-task tier

**Current state:** Every task in Phase 7 Implement routes to `implement-executor` (opus/`max`). There is no tier for tasks that are:

- One-line variable renames
- File moves
- Boilerplate generation
- Mechanical refactors with TDD-locked behavior

**Problem:** opus/`max` for a 5-line rename is over-provisioned by 1–2 orders of magnitude in cost. But adding a Haiku tier requires:

1. A task-complexity classifier (likely upstream in the orchestrator) that decides "trivial" vs "complex"
2. A new `haiku-executor` agent with a stripped-down TDD protocol (Haiku doesn't have documented effort levels — see §2.3 — so the `effort:` on it is undocumented behavior)
3. Layer 6 benchmarks proving the classifier doesn't mis-route complex tasks to Haiku
4. Layer 3 functional evals that exercise both paths

**Why we don't ship this:** Significant new architecture. Defer until we have data showing meaningful percentage of tasks are trivial AND a measurement infrastructure to safely evaluate the classifier.

### 6.6 Gap 6 (Documented, Not Fixed) — Plugin agent fields silently ignored

**Current state:** All 10 Claude plugin agents declare `permissionMode`. Per `/en/sub-agents` (verbatim, §2.2 above), plugin agents silently drop `permissionMode`, `hooks`, and `mcpServers`.

**Why we keep them anyway:**
1. They document author intent — a future maintainer reading the file knows the agent was designed for `acceptEdits`-style auto-execution.
2. They take effect if a user copies the agent to `~/.claude/agents/`.
3. The Layer 5 test asserts these values, preventing accidental drift.

**Why this is OK:** No user-visible behavior change either way. The audit makes the silent-ignore explicit so future readers don't assume the field is enforcing anything at runtime.

### 6.7 Gap 7 (Watch) — Codex `gpt-5.4-mini` under-documented

**Current state:** `codex-agents/phase-executor.toml` uses `model = "gpt-5.4-mini"`. The Codex parity research (Q5) found this model in changelog references but not in a canonical OpenAI "supported models" table.

**Risk:** If OpenAI deprecates or renames the model, our autopilot Codex side breaks silently. The local validation regex permits it, but that's defensive against the validation script — not against actual API behavior.

**Recommended action:** File an OpenAI issue requesting a canonical "supported models" page for Codex agent TOMLs. Track in TODO.

---

## 7. Recommendations

### 7.1 Tier 1 — Ship in this PR

| Change | File | Risk | Test impact |
| :----- | :--- | :--- | :----------- |
| Add 7 research tools to `implement-executor` allowlist | `agents/implement-executor.md` | Additive; no behavior change without research need | Layer 5 update |
| Add research-tool guidance to `developer_instructions` | `codex-agents/implement-executor.toml` | Additive; agent inherits tools regardless | None (Codex test only checks model/effort/sandbox) |
| Fix stale "Opus 4.6 only" note | `agents/implement-executor.md` | Documentation only | None |
| Document silent-ignore of plugin `permissionMode` in audit | This doc | Documentation only | None |

**Eval coverage:** Layer 5 tool-scoping assertions are added in this PR. Functional behavior of the new research tools is naturally exercised when tasks need research; no new Layer 3 eval is required because the change is additive (agent gains capability without behavior shift on existing tasks).

### 7.2 Tier 2 — Author Layer 6 benchmarks, decide based on data

Before shipping, run efficiency benchmarks on:

1. **`phase-executor` Plan phase**: sonnet/low vs sonnet/medium vs opus/low. Metric: G2 pass rate × downstream remediation loops × total tokens. Pick Pareto-optimal point.
2. **`clarify-executor` / `checklist-executor` / `analyze-executor`**: effort `high` vs `xhigh` on Opus 4.7. Metric: gate pass rate × total tokens × total cost. Pick best quality-per-dollar.
3. **Codex consensus analysts**: gpt-5.5/medium baseline; benchmark inter-analyst agreement vs Claude's sonnet/medium. If Codex agreement > Claude agreement materially, promote Claude analysts to opus/medium.

These are author-and-defer items. Open a follow-up issue in the speckit-pro tracker.

### 7.3 Tier 3 — Defer or document only

1. **Haiku-tier executor for trivial tasks** — significant new architecture; defer until Phase 7 task-volume data shows ≥20% trivial tasks. Document the absence as an intentional choice (all tasks get high-quality reasoning by default).
2. **Codex `consensus-synthesizer` / `gate-validator` consolidation** — Codex inlines these into the orchestrator session. This is a runtime constraint (`max_depth = 1`), not a design weakness. Document the divergence and don't try to force parity.
3. **`speckit-resolve-pr` "verify" subagent** — current self-contained pattern works. Add subagent dispatch only when token usage on PR-resolve operations exceeds 100k consistently.

---

## 8. Eval Coverage Plan

### 8.1 What ships with this PR

- **Layer 5** (`tests/layer5-tool-scoping/validate-tool-scoping.sh`): new assertions that `implement-executor` has `WebSearch`, `WebFetch`, `mcp__tavily-mcp__tavily-search`, `mcp__context7__resolve-library-id`, `mcp__context7__get-library-docs`, `mcp__RepoPrompt__file_search`, `mcp__RepoPrompt__context_builder`.
- **Layer 1** (`tests/layer1-structural/validate-claude-agents.sh`): no change required — current assertions only check frontmatter validity, not specific tool counts.
- **Layer 4** (`tests/layer4-script-unit/`): no change required — no scripts modified.

### 8.2 What's deferred to follow-up

- **Layer 6 efficiency benchmarks** for Tier 2 questions:
  - `phase-executor` Plan phase model comparison
  - `clarify/checklist/analyze` effort comparison (high vs xhigh)
  - Codex vs Claude consensus agreement comparison
- **Layer 3 functional eval** for `implement-executor` research-tool usage:
  - A representative task that requires looking up an external API (e.g., "implement OAuth callback per RFC 6749 §4.1")
  - Expectation: agent uses at least one of `WebSearch`/`tavily-search`/`context7` before writing code
  - This eval is optional and additive; current functional tests don't exercise this code path

### 8.3 Why Layer 3 isn't required for Tier 1 ship

Tier 1 is a **capability addition**, not a behavior change. Existing tasks don't suddenly require research. The agent gains the ability to research when needed — exercising that capability is a forward-looking concern best validated via Layer 6 benchmarks (which compare with-research-tools vs without-research-tools at the cost/quality boundary), not via Layer 3 (which validates skill-level golden-path behavior).

---

## 9. What's Still Uncertain

The docs do not authoritatively answer these questions; treat as risks:

1. **Plugin skill restrictions.** The Plugins doc enumerates restricted **agent** frontmatter (`hooks`, `mcpServers`, `permissionMode`) but is silent on whether `hooks` declared in plugin **skill** frontmatter are honored. Empirical test required.
2. **Effort behavior on Haiku.** The model-config doc lists effort support for Opus 4.7 / 4.6 / Sonnet 4.6 only. By absence, Haiku does not honor effort. Behavior on `effort: low` declared on a Haiku-routed agent is unspecified — silently ignored vs. fall-through. Test before relying on it.
3. **Codex `max_depth >= 2` behavior.** Codex's `agents.max_depth` defaults to 1 but the docs do not specify the upper bound. Behavior at depth >2 is unspecified.
4. **Codex subagent canonical model list.** No public "supported models" table on developers.openai.com. Local regex allowing `gpt-5.4` and `gpt-5.4-mini` is plausible-but-undocumented.
5. **`Agent(...)` from a plugin agent run as `--agent` main thread.** The doc says spawn-restrictions apply when an agent runs as the main thread via `claude --agent`. It doesn't specify whether a plugin-bundled agent can be promoted to main thread (`claude --agent <plugin>:<name>`) and then spawn subagents.
6. **`CLAUDE_CODE_SUBAGENT_MODEL` precedence.** The env var overrides all subagent `model:` frontmatter at runtime. Users setting this env var will see all speckit-pro agents routed to the same model. No way for a plugin to opt out.

These uncertainties are flagged for future investigation; none block the Tier 1 ship.

---

## 10. Action Plan for This PR

**Shipping in commit `<next>`:**

1. Add research tools to `agents/implement-executor.md`
2. Update `codex-agents/implement-executor.toml` developer_instructions to mention research tool availability and when to use it
3. Fix stale "Opus 4.6 only" note in `agents/implement-executor.md`
4. Update `tests/layer5-tool-scoping/validate-tool-scoping.sh` with new tool assertions
5. Commit this audit doc to `docs/ai/research/agent-architecture-audit-2026-04-30.md`

**Verification:**

- Run `bash tests/run-all.sh` from `speckit-pro/` (Layers 1, 4, 5).
- Confirm 100% pass rate (target: same as `main`'s baseline + new Layer 5 assertions).

**Deferred to follow-up issues (to be filed):**

- Tier 2: Author Layer 6 benchmarks for `phase-executor` Plan phase, executor effort recalibration, consensus model comparison.
- Tier 3: Document the Haiku-tier deferral. Track if/when task-volume data justifies the new architecture.
- Watch: File OpenAI issue for canonical Codex supported-models list.

---

## References

**Primary-source pulls (this session):**
- `/tmp/agent-audit-docs-2026-04-30.md` — full Anthropic + OpenAI Codex doc quotes
- `/tmp/agent-orchestration-inventory-2026-04-30.md` — full orchestration inventory across all 10 skills

**Companion repo docs:**
- `docs/ai/research/codex-parity-research-2026-04-30.md` — pre-existing Codex parity research

**Anthropic Claude Code primary docs (all accessed 2026-04-30):**
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/plugins
- https://code.claude.com/docs/en/model-config

**OpenAI Codex primary docs (all accessed 2026-04-30):**
- https://developers.openai.com/codex/subagents
- https://developers.openai.com/codex/config-reference
- https://developers.openai.com/codex/skills
- https://developers.openai.com/codex/hooks

**Codex source (loader constants):**
- https://github.com/openai/codex/blob/main/codex-rs/core-plugins/src/loader.rs
