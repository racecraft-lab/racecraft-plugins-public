# Dynamic Workflows Authoring Guide (SpecKit-Pro)

**How to write Claude Code Dynamic Workflow scripts — grounded in the first-party Workflow tool specification and validated by empirical probe runs, not preview-grade community sources.**

This is the source material for the Dynamic Workflows Adoption roadmap. It exists because the official documentation is *deliberately silent* on the authoring DSL (Claude normally writes workflow scripts from a prompt), which leaves the "how do I actually write one" question unanswered for a plugin that needs to **author workflows deterministically inside a skill**.

> **Relationship to the roadmap:** SPEC-007 in `dynamic-workflows-adoption-technical-roadmap.md` ships the plugin-runtime version of this content at `speckit-pro/skills/speckit-autopilot/references/workflows-integration.md` (with Layer 1/4 coverage). This doc is the planning/research artifact that feeds it — kept in `docs/ai/specs/` so the plugin tree stays untouched until the spec process moves it.

> **Provenance & maturity:** Every behavior below is tagged **[spec]** (from the first-party Workflow tool definition available in-session) or **[verified]** (observed in a probe run this session). Probe runs: `wf_3687ca2f-bd2` (Skill-tool availability) and `wf_d0743c15-87a` (primitives + environment). Dynamic Workflows are a **research preview** (Claude Code ≥ v2.1.154); treat unverified spec details as subject to change and re-probe before depending on them.

---

## 1. Mental model

A dynamic workflow is a **JavaScript orchestration script** that runs in the background in an isolated runtime. The script — not the model's turn-by-turn judgment — holds the loop, the branching, and the intermediate results. Subagents spawned by the script run in fresh, isolated contexts; their verbose output stays in *script variables*, and only the script's final `return` value comes back to the conversation. **[spec]**

Why this matters for SpecKit-Pro: today the autopilot's dispatch logic (phase order, gate-retry, consensus batching) lives as prose in `SKILL.md` that the model re-interprets every run. As a workflow it becomes literal control flow — a `while` loop for gate-retry, a `pipeline()` for consensus, a `parallel()` for `[P]` tasks — that runs the same way every time and keeps analyst/phase output out of the orchestrator's context window.

**Invocation:** a workflow is launched via the Workflow tool. The supported plugin vehicle is **in-skill inline authoring** — the skill instructs Claude to author and run the script (the Workflow tool's opt-in rules explicitly include "a skill whose instructions tell you to call Workflow"). The tool returns immediately with a `runId`; a notification arrives on completion. **[spec]**

---

## 2. Script skeleton & the `meta` block

Every script **must begin** with `export const meta = {…}`, a **pure literal** — no variables, function calls, spreads, or interpolation. Required: `name`, `description`. Optional: `whenToUse`, `phases`, per-phase `model`. **[spec]**

```js
export const meta = {
  name: 'consensus-fanout',
  description: 'Resolve unresolved consensus items via routed analysts + synthesizer',
  phases: [                                   // titles must match phase() calls exactly
    { title: 'Consensus' },
    { title: 'Apply' },
  ],
}
// script body starts here — async context, use await directly
phase('Consensus')
const resolved = await pipeline(items, /* … */)
return resolved
```

Notes:
- The body runs in an **async context** — `await` directly, no wrapping function. **[spec]**
- Standard JS built-ins are available **except** `Date.now()`, `Math.random()`, and argless `new Date()` — they throw (they would break resume determinism). Pass timestamps via `args`; vary by index for pseudo-randomness. **[spec]**
- **No filesystem/Node APIs** in the script body itself. (Subagents spawned with `agent()` *do* get tools like `Bash`/`Read`/`Write` — see §5.) **[spec]**
- Scripts are plain JavaScript, **not TypeScript** — no type annotations, interfaces, or generics. **[spec]**
- Script size limit: **524 KB**. **[spec]**

---

## 3. The five primitives

### `agent(prompt, opts?) → Promise<string | object>`
Spawns a fresh-context subagent.
- Without `schema`: returns the agent's final text as a **string**. **[verified — returned `"PING"`, type `string`]**
- With `schema` (a JSON Schema): the agent is forced to call a structured-output tool and `agent()` returns the **validated object** — no parsing, the runtime retries the agent on schema mismatch. **[verified — returned `{n:42}`, type `object`]**
- Returns `null` if the user skips the agent mid-run — filter with `.filter(Boolean)`. **[spec]**

`opts`: `{ label?, phase?, schema?, model?, isolation?, agentType?, run_in_background? }` — see §5.

### `parallel(thunks) → Promise<any[]>`
Runs an array of `() => Promise` thunks concurrently and **awaits all** — it is a **barrier**. Use only when you genuinely need every result together (dedup/merge across the full set, early-exit on total count, cross-item comparison). **[spec]**
- A thunk whose **agent errors / async-rejects** resolves to `null` in the array; `.filter(Boolean)` before use. **[spec]**
- ⚠️ **[verified gotcha]** A **synchronous `throw` in a thunk body** does *not* degrade to `null` — it propagated and **rejected the whole `parallel()` call**, and later thunks never dispatched (the probe ran 7 agents instead of 8). **Practical rule: never throw synchronously inside a thunk.** Let fallible work happen inside `agent()` or an `async` function so failures arrive as rejections (→ `null`), not synchronous throws.

### `pipeline(items, stage1, stage2, …) → Promise<any[]>`
Runs each item through all stages **independently, with NO barrier between stages** — item A can be in stage 3 while item B is still in stage 1. This is the **default** for multi-stage work; wall-clock = slowest single-item chain, not sum-of-slowest-per-stage. **[spec]**
- Every stage callback receives **`(prevResult, originalItem, index)`**. **[verified — stage 2 saw `original:"x"`, `index:0`, and stage 1's return]**
- A stage that **throws drops that item to `null`** and skips its remaining stages; **other items continue**. The dropped item is surfaced in the run's `failures`. **[verified — item `"y"` → `null` + `failures: pipeline[1] failed: Error: drop-y`, item `"x"` completed normally]**

**Barrier decision rule:** default to `pipeline()`. Reach for `parallel()` only when stage N needs cross-item context from *all* of stage N-1 (dedup before expensive verify, early-exit on zero, "compare against the other findings"). A middle transform that just flattens/maps/filters does **not** justify a barrier — do it inside a pipeline stage.

### `phase(title) → void`
Starts a named progress group; subsequent `agent()` calls are grouped under it in the live display. Inside `pipeline()`/`parallel()` stages, prefer the explicit `{phase: 'Title'}` option on `agent()` to avoid races on the global `phase()` state. **[spec]**

### `log(message) → void`
Emits a narrator line above the progress tree — use for human-visible progress (`log(\`${found}/10 found\`)`). **[spec]**

Also available: `workflow(nameOrRef, args?)` to run another workflow inline as a sub-step (one level of nesting only). **[spec]**

---

## 4. Verified environment & limits

| Fact | Value | Source |
|---|---|---|
| Default subagent tools | `Bash, Edit, Read, Skill, ToolSearch, Write, StructuredOutput, advisor` | **[verified]** |
| `Skill` tool works in workflow agents | `Skill({skill:"speckit.speckit-utils.doctor"})` resolved + injected (instruction-injection, not a returned result) | **[verified — `wf_3687ca2f-bd2`]** |
| MCP / `WebSearch` / `Task*` etc. | Deferred — reachable per-agent via `ToolSearch` (`"select:<name>"`) | **[spec]** |
| `agentType` (built-in) | `'Explore'` resolved with its read-only persona | **[verified]** |
| `agentType` (plugin-namespaced) | `'speckit-pro:codebase-analyst'` resolved with the plugin agent's exact system prompt | **[verified]** — validates "reuse existing agent defs" |
| `isolation:'worktree'` | agent ran in `.claude/worktrees/<runId>-<n>` with shared `.git` common dir | **[verified]** |
| Concurrency cap | `min(16, cores-2)` concurrent; excess queues | [spec] (not stress-tested) |
| Lifetime cap | **1,000** `agent()` calls per run | [spec] |
| `budget.total` | `null` when no `+Nk` directive; a **hard ceiling** when set (further `agent()` throw once `spent()` reaches it) | `total:null` **[verified]**; hard-ceiling [spec] |
| `budget.spent()` | live, cumulative, **shared** across main loop + all workflows this turn (384k→393k during the probe) | **[verified]** |
| Resume | `resumeFromRunId` replays cached completed calls; cache keyed on `(prompt, schema, model, isolation, agentType)`; **session-scoped** (exit Claude Code → next session starts fresh) | [spec] (not probed) |
| No mid-run user input | only agent permission prompts pause a run; for sign-off, run each stage as its own workflow | [spec] |

**Plugin-agent caveat:** agents loaded from a plugin ignore `hooks`/`mcpServers`/`permissionMode` frontmatter. SpecKit-Pro's agents don't use those, so `agentType:'speckit-pro:<agent>'` reuse is safe; any workflow agent needing MCP reaches it via `ToolSearch`, not frontmatter. **[spec + repo MEMORY]**

---

## 5. `agent()` options reference

| Option | Effect | Guidance |
|---|---|---|
| `schema` | Force structured output; return validated object | Use for every agent whose result the script branches on |
| `agentType` | Use a named subagent (built-in like `Explore`, or `speckit-pro:<agent>`) instead of the default | **The reuse mechanism** — pass existing plugin agents as teammate types; composes with `schema` |
| `isolation: 'worktree'` | Run in a fresh git worktree (~200-500ms + disk; auto-removed if unchanged) | **Only** when agents mutate files in parallel and would conflict (SPEC-010/011) |
| `label` | Override the display label | Label by file/item so the progress tree is legible |
| `phase` | Assign to a progress group explicitly | Use inside `pipeline`/`parallel` stages instead of global `phase()` |
| `model` | Override the model for this agent | Omit by default (inherits session model); set only when confident a tier fits |

---

## 6. SpecKit-Pro patterns (worked examples)

These are the concrete fan-out shapes the roadmap's specs adopt. Each reuses existing plugin agents via `agentType` (verified working).

### SPEC-008 — Consensus fan-out (`pipeline`, no barrier)
Each unresolved item streams through "routed analysts → synthesizer" independently; analyst output stays in script variables. The orchestrator applies edits serially from the returned array.

```js
phase('Consensus')
const resolved = await pipeline(unresolvedItems,
  // stage 1: fan analysts for THIS item (inner parallel is a small barrier per item)
  (item) => parallel(routeAnalysts(item).map(a =>
    () => agent(analystPrompt(item, a), { agentType: a, phase: 'Consensus', schema: ANALYST }))),
  // stage 2: synthesize this item's analyst responses
  (responses, item) => agent(synthPrompt(item, responses.filter(Boolean)),
    { agentType: 'speckit-pro:consensus-synthesizer', phase: 'Consensus', schema: VERDICT })
)
// orchestrator applies artifact edits serially from `resolved` — unchanged from today
```
`routeAnalysts(item)` returns the namespaced agent ids (`'speckit-pro:codebase-analyst'`, `'speckit-pro:spec-context-analyst'`, `'speckit-pro:domain-researcher'`) per the `[category]` prefix.

### SPEC-009 — The full hook-bracketed main loop (not just 7 phases)
A real autopilot phase is `before_<phase>` hooks → executor → consensus → `after_<phase>` hooks → gate-retry → commit. Pre-flight context (commands, presets, hook map, flags) arrives in `args` — the script never re-detects. Gate-retry, the prose "auto-fix ≤2 attempts then honor the gate-failure setting," becomes a literal loop:

```js
// args = { PROJECT_COMMANDS, PRESET_CONVENTIONS, hooks, extensionRegistry,
//          CONFIDENCE_GATE_MODE, GATE_FAILURE, ... }  ← from the SPEC-007 pre-flight contract

// Hooks have no Bash in the script body, so run each accepted hook THROUGH an agent:
async function runHooks(event) {                       // event = 'before_specify', 'after_plan', …
  for (const hook of (args.hooks?.[event] ?? []).filter(h => h.accepted)) {
    await agent(`Run the project hook \`${hook.command}\` and report results.`,
                { agentType: 'speckit-pro:gate-validator', label: `hook:${event}`, phase: 'Hooks' })
  }
}

async function runPhase({ name, executorType, gateId, hasConsensus }) {
  phase(name)
  await runHooks(`before_${name}`)
  await agent(phasePrompt(name, args.PRESET_CONVENTIONS),       // executor invokes /speckit.* via Skill;
              { agentType: executorType })                      // preset conventions injected into the prompt
  if (hasConsensus) await runConsensus(name)                    // nests the SPEC-008 pipeline
  await runHooks(`after_${name}`)
  let attempts = 0, verdict
  do {
    verdict = await agent(gatePrompt(gateId), { agentType: 'speckit-pro:gate-validator', schema: GATE })
    if (verdict.pass) break
    await agent(autoFixPrompt(gateId, verdict), { agentType: executorType })
  } while (++attempts < 2)
  if (!verdict.pass && args.GATE_FAILURE === 'stop') throw new Error(`${gateId} failed`)
  return verdict
}

// G6.5 confidence gate after Analyze — iterate ≤3×, advisory/strict:
async function confidenceGate() {
  for (let i = 0; i < 3; i++) {
    const c = await agent(confidencePrompt(args.CONFIDENCE_GATE_MODE), { agentType: 'speckit-pro:gate-validator', schema: CONFIDENCE })
    if (c.pass || c.noData) return c
    await runConsensus(c.lowestCriterion)                       // focused remediation round
  }
  if (args.CONFIDENCE_GATE_MODE === 'strict') throw new Error('G6.5 below threshold after 3 iterations')
}
```
Phases are data-dependent → sequential `await runPhase(...)`. Hooks fire **between** phases inside the loop — that's why they live in the workflow, not the surrounding session.

### SPEC-012 — Post-implementation lifecycle (`parallel` barrier → serial tail + graceful skip)
```js
phase('Post: parallel group')
const skip = (ext) => !args.extensionRegistry?.[ext]?.enabled        // graceful extension skip
const [doctor, review, verifyChain] = await parallel([
  () => skip('doctor')      ? 'skipped: doctor not installed'  : agent(doctorPrompt, { agentType: 'speckit-pro:gate-validator', schema: REPORT }),   // 10
  () => skip('review')      ? 'skipped: review not installed'  : agent(reviewPrompt, { agentType: REVIEW_AGENT, schema: REPORT }),                   // 13
  () => runVerifyChain(),   // 11 → 12 → 14 chained inside one thunk (shared fixtures); always-run task 14 anchors it
])
// BARRIER — serial tail operates on the unified tree (hard dependency chain):
phase('Post: serial tail')
await cleanup(); await reviewabilityGate(); await selfReview()
await prBody(); await createPR()
await scheduleReviewLoop()   // schedules /loop in fresh recurring context — NOT a workflow agent
await retrospective()        // FINAL (skip-gracefully if retrospective ext absent)
```

### SPEC-010 — Parallel `[P]` implementation tasks (`parallel` + worktree)
`[P]`-tagged tasks mutate files concurrently without conflict via worktree isolation (verified: each gets `.claude/worktrees/<runId>-<n>`):

```js
phase('Implement')
const results = await parallel(parallelSafeTasks.map(t =>
  () => agent(implementPrompt(t), { agentType: 'speckit-pro:implement-executor', isolation: 'worktree', schema: TDD })
))
const done = results.filter(Boolean)          // failed tasks degrade to null
// non-[P] tasks run sequentially before/after; then merge-back per SPEC-010's resolution
```

### SPEC-011 — Resolve-PR partition fan-out (`parallel` barrier → serial tail)
The barrier is genuinely required here: verify/commit/push/resolve operate on the unified tree and must wait for every partition.

```js
const partitions = partitionThreadsByFile(unresolvedThreads)   // cross-file threads → serial tail
phase('Remediate')
const fixed = await parallel(partitions.map(p =>
  () => agent(remediatePrompt(p), { agentType: REMEDIATION_EXECUTOR, isolation: 'worktree', schema: FIX })
))
// BARRIER reached — serial tail on the unified tree:
phase('Finalize')
await runVerification()
await commitAndPush(fixed.filter(Boolean))
for (const thread of allThreads) await replyAndResolve(thread)  // gh reply + resolve
```

---

## 7. Gotchas (the non-obvious rules)

1. **Never `throw` synchronously in a `parallel()` thunk** — it rejects the whole call and orphans later thunks. Model fallible work as `agent()` calls or `async` functions so failures become `null`. **[verified]**
2. **`pipeline()` is the default; `parallel()` is the exception.** A barrier is only justified by a genuine cross-item dependency, not by "I need to flatten/map first." **[spec]**
3. **`Date.now()`/`Math.random()`/argless `new Date()` throw.** Pass time via `args`; vary by index. **[spec]**
4. **Skill invocation is instruction-injection, not a function call** — an agent that invokes `speckit-plan` *receives the instructions and must execute them*, exactly like today's `phase-executor`. It does not return a computed result from the skill. **[verified]**
5. **Resume is session-scoped, not crash recovery.** A multi-hour autopilot must keep per-phase `speckit.checkpoint.commit` for durability; workflow resume only helps within the same Claude Code session. **[spec]**
6. **`budget.total` is `null` unless the user set a `+Nk` target** — guard loops with `while (budget.total && budget.remaining() > N)`, or an unguarded loop runs to the 1,000-agent cap. **[verified `total:null` + spec]**
7. **Iterate via `scriptPath`, not by resending the script.** Every invocation persists its script to a returned path; edit that file and re-invoke with `{scriptPath}` (and `resumeFromRunId` to reuse cached agent results). **[spec]**
8. **The script body has no Bash/filesystem — detection and hooks happen elsewhere.** Pre-flight detection (commands, presets, the hook map, capability flags) runs in the *main session* and is passed in via `args`; the script never re-detects. User-installed extension hooks can't run from the script body either — dispatch each through an `agent()` (agents have `Bash`+`Skill`). This is the separation that lets a deterministic script honor dynamic, user-installed behavior. **[spec — `args` is the documented input channel; default-agent toolset verified]**

---

## 8. Open / unverified (probe before depending)

- **Resume/journaling** (`resumeFromRunId`, cache-key tuple) — documented, not yet probed. Verify before relying on it for SPEC-009 re-runs.
- **Concurrency cap** `min(16, cores-2)` and queueing — documented, not stress-tested.
- **`budget.total` hard-ceiling throw** — documented; not exercised (no `+Nk` directive was set during probing).
- **Worktree merge-back** — the runtime creates `.claude/worktrees/<runId>-<n>` (verified), but the merge-back/cleanup contract for SPEC-010/011 needs its own probe (how do parallel worktree edits reach the main tree?).

---

## 9. References

- **First-party Workflow tool specification** — the authoritative DSL source (in-session tool definition); supersedes community reverse-engineering for all API specifics.
- **Probe runs (this session):** `wf_3687ca2f-bd2` (Skill-tool availability), `wf_d0743c15-87a` (primitives + environment) — raw results in the run transcripts.
- **Official docs (model & limits, silent on DSL):** https://code.claude.com/docs/en/workflows · https://claude.com/blog/introducing-dynamic-workflows-in-claude-code · https://code.claude.com/docs/en/sub-agents
- **Roadmap:** `docs/ai/specs/dynamic-workflows-adoption-technical-roadmap.md` (SPEC-007 ships the plugin version of this guide).
- **Existing dual-path design:** `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md`.
