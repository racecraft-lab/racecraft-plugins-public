---
name: speckit-autopilot
description: >
  Autonomous SpecKit workflow executor. Reads a populated workflow
  file and runs all 7 SDD phases (specify → clarify → plan →
  checklist → tasks → analyze → implement) with programmatic gate
  validation, multi-agent consensus resolution, and auto-commits.
  Use when the user says "run autopilot", "execute workflow",
  "autonomous speckit", "autonomous execution", "kick off autopilot",
  "start the autonomous pipeline", "drive it through all the SDD
  phases", "run the whole thing autonomously", "full end-to-end
  speckit run", or hands over a populated SPEC-NNN-workflow.md file
  for end-to-end execution. Requires SpecKit CLI installed,
  constitution created, and a populated workflow file. Not for SDD
  methodology questions ($speckit-coach), pre-spec scoping
  ($grill-me), new-spec setup ($speckit-scaffold-spec), status
  checks ($speckit-status), or PR comment resolution
  ($speckit-resolve-pr).
---

# SpecKit Autopilot — Autonomous Execution Engine

## Installed Runtime Contract

Installed Claude and Codex surfaces resolve Python 3.11 or newer, invoke
`[resolved_python, "-m", "speckit_pro_runner"]`, send one JSON request on
stdin, read one JSON response from stdout, and surface stderr diagnostics.
Do not add a shell fallback, `jq` parsing path, Git Bash, WSL, or
PowerShell-specific command-language requirement for installed workflows.

## Scope

This skill handles autonomous workflow EXECUTION. For methodology
questions, SDD philosophy, or learning how SpecKit works, redirect
the user to `$speckit-coach` — the coaching skill is the right
resource for methodology guidance.

Your context window will be automatically compacted as it
approaches its limit, allowing you to continue working
indefinitely. Do not stop tasks early. Always be as persistent
and autonomous as possible and complete all 7 phases fully.

You are an **orchestrator** for SpecKit workflows. You read
prompts from the workflow file and delegate each phase to a
**subagent** that runs the appropriate SpecKit command. You never
run the commands yourself — you spawn, collect results, validate
gates, and advance.

## Architectural Constraint — Main Agent Is The Orchestrator

This skill loads into the **main Codex session agent** when the user
invokes `$speckit-autopilot`. Only the main agent can spawn subagents
through `spawn_agent` — Codex enforces this at the runtime level via
`agents.max_depth = 1` in `config.toml`. The Orchestrator-Direct pattern
this skill uses works because *the skill IS the main agent at execution
time*; "spawn_agent for each phase" is a flat fan-out, never nested.

**If this skill is ever loaded inside a subagent context** (for example a
phase-executor mistakenly tries to invoke `$speckit-autopilot`), it MUST
refuse and surface the violation rather than attempt to orchestrate. None
of the bundled custom-agent TOML files (`phase-executor`, `clarify-executor`,
`checklist-executor`, `analyze-executor`, `implement-executor`,
`codebase-analyst`, `spec-context-analyst`, `domain-researcher`,
`autopilot-fast-helper`) instruct their agents to call `spawn_agent` —
this constraint is enforced by the Codex runtime depth limit, not just by
convention. Consensus synthesis and gate validation are intentionally
handled in this orchestrator session rather than in dedicated subagents.

## Codex Runtime Contract

This Codex variant is a concrete tool contract, not advisory prose.
Bind the workflow to actual Codex primitives:

- `update_plan` is REQUIRED before Phase 1 and after every phase transition.
  If the call fails or is skipped, STOP.
- Discover the callable collaboration actions before dispatch and select the
  semantic equivalents that the current Codex surface actually exposes.
  `spawn_agent` plus `wait_agent` and delivery of the agent's result are the
  REQUIRED common contract. Hosted Responses Multi-agent provides
  `spawn_agent`, `send_message`, `followup_task`, `wait_agent`,
  `interrupt_agent`, and `list_agents`; it does not expose `close_agent`.
  Other Codex surfaces can expose equivalents such as `send_input`,
  `resume_agent`, or `close_agent`. On hosted Responses, `send_message` queues
  context and `followup_task` assigns work and starts the next turn. On a
  surface with `send_input`, use it to deliver follow-up work to an open agent;
  if that agent was explicitly closed, call `resume_agent` first and then
  `send_input`. Inspection, interruption, and explicit closure are optional
  actions used only when present. Hard-stop only if spawning or receiving the
  required result is unavailable — absence of `close_agent` is NOT a
  prerequisite failure. See the official [Responses Multi-agent action
  contract](https://developers.openai.com/api/docs/guides/responses-multi-agent#how-multi-agent-works)
  and [Codex subagent orchestration
  guidance](https://learn.chatgpt.com/docs/agent-configuration/subagents#orchestration-and-thread-controls),
  plus the local [configuration
  reference](https://learn.chatgpt.com/docs/config-file/config-reference#configtoml).
- The REQUIRED lifecycle on every surface is `spawn_agent` → bounded
  `wait_agent` loop → consume the dispatched agent's actual final result. A
  hosted `wait_agent` call can wake for an ordinary message, unrelated mailbox
  update, timeout, or steering event, so associate updates with the dispatched
  sender/task and keep waiting until its `FINAL_ANSWER` or equivalent summary
  is consumed. A terminal status is corroboration or recovery evidence only;
  it never replaces the required result. If an agent is terminal without a
  delivered result, drain the mailbox and then re-spawn or fail that item.
- When `close_agent` is exposed, call it promptly after consuming the result.
  Cleanup policy is best-effort: if the surface reports the agent already gone,
  log it and continue without retry-looping. When `close_agent` is absent,
  consume the result and leave the inspectable thread to the host; optionally
  reuse it with the available follow-up action.
- On resume, never assume an older agent still exists. If `list_agents` is
  available, match returned current-tree entries to the workflow target and
  current incomplete plan item's canonical task name/prompt; manage or reuse
  only agents confirmed present and owned by this autopilot run. Without
  inspection, treat prior-session agent references as stale and spawn fresh.
  Apply explicit closure only to run-owned agents confirmed present, including
  a reconciled agent that was spawned before the interruption.
- Derive `subagent_slots` from the current session without mixing surface
  conventions: use explicit `max_concurrent_subagents` when provided; when the
  host advertises total active agents including `/root`, subtract one; when a
  local surface advertises an open-thread cap, follow that surface's stated
  semantics. If no count is exposed, set `subagent_slots = 1` as the safe
  fallback. For wider fan-out, dispatch in waves of at most `subagent_slots`,
  consume each required result, perform optional closure when exposed, then
  start the next queued item. Never hard-code one surface's default as
  another surface's cap.
- A `wait_agent` timeout is one bounded mailbox poll, not proof that an agent is
  stuck. Continue bounded waits and inspect status/progress when possible. Use
  `interrupt_agent` only after a separate execution deadline or confirmed
  no-progress condition, and only to cancel a still-running turn; it preserves
  context and is not closure. Any interrupted required item must be re-spawned
  and return a real result before its plan item can complete.
- Before reporting the run complete, use `list_agents` when exposed; otherwise
  audit the tracked dispatch IDs and consumed results. Every required dispatch
  must have a consumed result. Close remaining current-run threads best-effort
  only when `close_agent` is exposed. Hosted completed threads are host-managed
  and do not block completion.
- `autopilot-fast-helper` is OPTIONAL. Only the main autopilot may invoke it,
  and only for tiny text-only compression, triage, or query-drafting work.
  Never route edits, gate decisions, or consensus votes through it.
- `read_file`, `file_search`, `exec_command`, and `apply_patch` are the
  concrete Codex tools for workflow parsing, shell validation, and artifact
  mutation.
- Persist orchestration state to `autopilot-state.json` in the same directory
  as the workflow file. Resume reads that file first, then reconciles with the
  workflow file.
- This skill owns `./agents/openai.yaml` as Codex skill metadata for UI
  appearance and invocation policy. Optional research/context capabilities are
  discovered at runtime, so the sidecar MUST NOT declare Tavily, Context7, or
  any other optional capability as a required tool dependency. Do not treat
  that sidecar as a custom-agent manifest.
- SpecKit Pro also ships bundled custom-agent templates under
  `../../codex-agents/`. Those bundled TOML files are package assets, not
  runtime registrations.
- Custom executor and consensus agents must be installed as real Codex
  subagents under `.codex/agents/` (project scope) or `~/.codex/agents/`
  (user scope). The bundled `install` skill copies the plugin templates into
  those official Codex runtime paths.

Do not translate this skill into Claude-only primitives such as legacy
task-list tools or legacy Claude agent/shell placeholders. Do not read the
bundled TOML templates and inline them as ad hoc prompts. Validate that the
required custom subagents are installed, then spawn them by agent name. If any
required SpecKit Pro subagent is missing, STOP and instruct the user to run
`$install` from the SpecKit Pro plugin, then restart Codex.

## Prerequisites — Model & Effort

The autopilot orchestrator makes gate decisions, synthesizes consensus, and
manages a 7-phase workflow. Running on a weak model produces poor orchestration
decisions that cascade into expensive rework.

**Before executing any step**, verify:

1. **Model check:** You MUST be running on the highest-capability Codex model
   tier available in this environment. Prefer `gpt-5.5` when it is available
   in the Codex model picker. `gpt-5.4` is an acceptable documented fallback
   during rollout or when the environment uses API-key authentication. If the
   session is explicitly on a mini, fast, Spark, or otherwise reduced-capability
   tier, STOP and instruct the user to relaunch the autopilot on a stronger
   model. If `gpt-5.5` is unavailable, also verify the installed SpecKit Pro
   executor and consensus subagents were installed with `--model gpt-5.4`
   or `SPECKIT_CODEX_MODEL=gpt-5.4`; changing only the parent session model
   does not rewrite hard-pinned custom-agent TOML files.

2. **Effort check:** Verify `model_reasoning_effort` is set to `xhigh`
   for the session. If the session is locked to a lower tier
   (`low`, `medium`, `high`), STOP and instruct the user to relaunch
   with `xhigh` reasoning. The plugin's policy is **xhigh thinking on
   every Codex agent, regardless of model tier** — every bundled
   custom subagent ships with `model_reasoning_effort = "xhigh"`
   (including `autopilot-fast-helper` on gpt-5.3-codex-spark). Quality
   is the only optimization axis.

These checks are non-negotiable. A sub-xhigh orchestrator spawning
xhigh subagents wastes the subagents' reasoning — the orchestrator's
decisions determine whether subagent work is productive or wasted.

## Critical: Execution Rules

These rules are non-negotiable. Follow them exactly.

### 0. Forbidden skill invocations

**Never invoke `$grill-me` from any phase, subagent, or consensus step.**
Grill-me is a strictly human-in-the-loop, pre-workflow scoping interview. Its
runtime guard probes for `request_user_input` then a TTY before asking any
question; if invoked from autopilot's autonomous loop it will refuse and write
nothing — but the autopilot must not even attempt the call.

If a phase encounters ambiguity that feels like it needs grill-me, the correct
response is one of:

- Run the `$speckit-clarify` skill (Phase 2) with the multi-agent consensus
  protocol — that is autopilot's only clarification mechanism.
- Fail the gate, surface the ambiguity, and stop. Pre-workflow interviews
  belong in `$speckit-scaffold-spec`, not autopilot.

This rule applies to: the orchestrator, every phase subagent
(`phase-executor`, `clarify-executor`, `checklist-executor`,
`analyze-executor`, `implement-executor`), every consensus analyst
(`codebase-analyst`, `spec-context-analyst`, `domain-researcher`), and
`consensus-synthesizer`.

### 0.5 Static Tier-2 relocation suggestions only

Autopilot may surface Tier-2 PROCESS relocation guidance for thawed legacy
specs, but it must never execute the relocation codemod. Do not invoke
relocation mutation from any autopilot phase, subagent, or
post-implementation step.

At startup and when evaluating the active workflow target, inspect candidate
state directly. Suggest relocation only for a thawed in-scope legacy spec that
has root PROCESS allow-list artifacts or matching docs-side scaffold artifacts.

For an eligible candidate, print the concrete `specs/<spec-dir>` value and say
that relocation remains manual operator work outside autopilot. Describe any
write as a follow-up after review and a clean worktree.
Suppress the suggestion and report the reason for:

- `frozen/in-flight` specs named by `.specify/feature.json`
- invalid active-feature state
- already-current specs with `SPEC-MOC.md` `structureVersion: 1`
- already-normalized specs whose PROCESS artifacts are under `.process/`
- candidates with no relocatable PROCESS artifacts
- out-of-scope `non_speckit_namespace` and `date_named_legacy_namespace`
  candidates

### 1. All phases are mandatory

The canonical execution order is:

```text
PHASES = [specify, clarify, plan, checklist, tasks, analyze, implement]
```

Before any phase work starts, the parent session MUST create a durable
progress plan that accounts for every phase in that list plus prerequisites
and post-implementation verification. Do not collapse phases, drop later
phases from the plan, or stop after a planning artifact is produced.

`--from-phase` changes only the starting index for execution. It does not
remove earlier completed phases or later pending phases from `update_plan`
or `autopilot-state.json`.

Forbidden shortcuts:

- Ending after Specify because `spec.md` exists
- Ending after Plan because implementation details are available
- Ending after Tasks because `tasks.md` looks complete
- Skipping Analyze because no findings are expected
- Skipping Implement because tasks appear already marked complete
- Combining Specify, Plan, and Tasks into one execution item

### 2. Subagent per phase

For each phase, spawn a **foreground subagent** with `spawn_agent`,
wait for it with `wait_agent`, and keep orchestration in the parent.
The subagent runs the SpecKit command and returns a summary.

**Why:** If you invoke a skill directly in your own context, the command's
completion behavior causes your loop to output plain text and terminate.
With subagents, the command runs in an isolated context and its completion
is harmless — the result returns to you and your loop continues.

**What this looks like:**

```text
CORRECT:
  1. Read workflow file's "### Specify Prompt" section
  2. Resolve the phase runner:
     verify `phase-executor` exists in `.codex/agents/` or `~/.codex/agents/`
  3. spawn_agent the resolved phase runner with:
     "Run $speckit-specify with: <prompt>"
  4. wait_agent(...)
  5. update_plan(...) and write autopilot-state.json
  6. Search spec.md for [NEEDS CLARIFICATION] markers
  7. Resolve the clarify runner:
     verify `clarify-executor` exists in `.codex/agents/` or `~/.codex/agents/`
  8. spawn_agent the resolved clarify runner with:
     "Prepare a Clarify Question Set for: ..."
  ...every step produces durable state and the loop never dies...

WRONG:
  1. Invoke $speckit-specify directly in your context
  2. Command loads into YOUR context
  3. You output: "The spec is ready" with no further tool calls
     → loop terminates
```

**Third-party skills:** when capability discovery selects an installed skill you
$-invoke, its completion text can likewise end the loop. Capture the skill's
result as durable state/evidence and continue; never treat a third-party skill's
completion text as your own terminal output.

### 3. Use phase-specific executor agents

Each phase type has its own specialized executor agent:

| Phase | Agent | Why specialized |
| ----- | ----- | --------------- |
| Specify, Plan, Tasks | `phase-executor` | Heavy reasoning (Specify, Plan); mechanical for Tasks. Single skill invocation, single summary. |
| Clarify | `clarify-executor` | Read-only question set; parent answers and edits |
| Checklist | `checklist-executor` | Must run checklist AND remediate gaps with research |
| Analyze | `analyze-executor` | Must run analysis AND remediate ALL findings with research |
| Implement | `implement-executor` | Task-level dispatch with strict TDD. **Honor `[P]` markers within derived `subagent_slots`** — dispatch consecutive `[P]`-tagged tasks of the same agent type in cap-bounded waves. As each actual result arrives through the bounded `wait_agent` loop, record it, call `close_agent` only when exposed, and start the next `[P]` task. Do NOT spawn every `[P]` task in ONE turn when the run is wider than the cap. Non-`[P]` tasks dispatch one at a time. After each wave, run TYPECHECK + UNIT_TEST in the lead; on regression, fall back to serial re-run. |
| Read-only consensus | analyst agents | Read-heavy code/spec/domain analysis |

Concrete Codex mapping:

- `./agents/openai.yaml` is skill metadata only. It does not register custom
  agents for Codex.
- Resolve the installed agent from `.codex/agents/<agent>.toml` first, then
  `~/.codex/agents/<agent>.toml`
- If the installed agent is missing, STOP and tell the user to run `$install`,
  then restart Codex
- Build the phase prompt in the parent session
- Call `spawn_agent` using the installed custom agent by its `name`
  plus the workflow prompt
- Call `wait_agent` for completion
- Persist the returned summary into the workflow file and `autopilot-state.json`

Spawn each agent with phase-specific prefix where needed, followed by:

```text
Workflow prompt:
---
<paste the exact prompt from the workflow file>
---
```

Each agent runs the command (and any post-execution work like gap
remediation) in isolation and returns a structured summary.

### 4. Progress state is mandatory

Before executing any phase, call `update_plan` with the full granular
checklist and mirror the same state into `autopilot-state.json`.
For multi-prompt phases (Clarify, Checklist), create one item per
prompt/session so you know exactly what to execute next. Missing
`update_plan` is a hard stop. See Step 1.1.

### 5. Multi-prompt phases

Clarify and Checklist have multiple prompts in the workflow file.
Spawn a **separate subagent for each prompt**.

**What this looks like:**

```text
CORRECT (Clarify with 2 sessions):
  1. update_plan: "Phase 2: Clarify - Session 1" -> in_progress
  2. Write the same status to autopilot-state.json
  3. Spawn the clarify-executor agent: "<session 1 prompt>"
     The clarify-executor returns questions and recommendations
  4. Parent answers returned questions and applies accepted edits
  5. Search spec.md for [NEEDS CLARIFICATION] markers
  6. If markers remain -> use consensus routing to resolve
  7. update_plan: "Phase 2: Clarify - Session 1" -> completed
  8. update_plan: "Phase 2: Clarify - Session 2" -> in_progress
  9. Write both transitions to autopilot-state.json
  10. Spawn the clarify-executor agent: "<session 2 prompt>"
  11. Parent answers returned questions and applies accepted edits
  12. Search spec.md for [NEEDS CLARIFICATION] markers
  13. If markers remain -> use consensus routing to resolve
  14. update_plan: "Phase 2: Clarify - Session 2" -> completed
  15. Validate G2 gate (0 markers remaining)
  16. Advance to Plan

WRONG:
  1. Run all sessions, then check for markers at the end
  2. Or skip sessions and do your own analysis
```

### 6. Clarify — executor returns questions to parent

The `clarify-executor` is read-only. It does not invoke
`$speckit-clarify`, does not wait on a user, and does not edit
artifacts. It inspects the workflow prompt, feature spec, and repo
evidence, then returns a `Clarify Question Set` containing up to 5
prioritized questions, recommended answers, evidence, and suggested
artifact updates.

The parent orchestrator answers the returned questions in the main
session, applies the spec/workflow/state edits, then checks for
remaining `[NEEDS CLARIFICATION]` markers and resolves unresolved
items via consensus if needed (see Rule 7).

### 7. Two-layer resolution with category-routed consensus

After EACH executor subagent returns for a consensus phase
(Clarify, Checklist, Analyze), run a two-layer resolution process
BEFORE spawning the next subagent.

**Layer 1 — Executor prepares evidence:** Clarify is different from
Checklist and Analyze. The `clarify-executor` returns questions and
recommendations to the parent; the parent answers and applies accepted
edits. `checklist-executor` and `analyze-executor` still resolve most
items directly and apply fixes to artifacts. Any item that needs
further resolution is flagged in an "Unresolved for consensus" summary
section, **each prefixed with one or more category tags**
(`[codebase]`, `[spec]`, `[domain]`, `[security]`, `[ambiguous]`).

**Layer 2 — Category-routed consensus** (Tier A, see
[consensus-protocol.md](references/consensus-protocol.md)):
For ALL unresolved items in the phase, **batch-dispatch the union
of routed analysts via `spawn_agent` in ONE tool turn**, then
batch synthesizers, then apply Artifact Edits serially. Two rounds:

```text
ROUND 1 — Category-routed, BATCHED across items
  For each unresolved item Ix, parse the [<categories>] prefix to
  determine the routed analyst set Sx per the routing table:
    [codebase]            → codebase-analyst only
    [spec]                → spec-context-analyst only
    [domain]              → domain-researcher only
    [security]            → ALL 3 (defense-in-depth)
    [ambiguous] or empty  → ALL 3 (safe default)
    [a, b]                → union of named analysts

  Stage 1: spawn_agent for every (item, analyst) pair in ONE turn
           (Σ |Sx| total calls). wait_agent on ALL handles.
  Stage 2: spawn_agent the consensus-synthesizer for every item in
           ONE turn (N total calls). wait_agent on ALL handles.
  Stage 3: apply each synthesizer's Artifact Edit SERIALLY via
           apply_patch (avoids write contention on spec.md/plan.md/
           tasks.md). Log a CRL row per item.

  IF any synthesizer flags [ESCAPE_TO_ROUND_2] or low confidence:
    enqueue (Ix, Sx) for Round 2.
  IF any synthesizer flags [HUMAN REVIEW NEEDED]:
    log + STOP autopilot after applying remaining safe edits.

ROUND 2 — Fan-out across queued items, capped by the current session
  Stage 4: spawn_agent the (3 - |Sx|) analysts that did not run in
           Round 1 across the queued items, but never exceed derived
           subagent_slots. Dispatch in waves: loop bounded wait_agent calls
           until each analyst result is consumed, record it, close_agent only
           when that action is exposed, and start the next queued
           (item, analyst).
  Stage 5: spawn_agent the Round-2 synthesizers under subagent_slots;
           apply the same capability-aware completion lifecycle to each.
  Stage 6: apply Round-2 Artifact Edits serially.
           Apply edit OR flag [HUMAN REVIEW NEEDED] and STOP.
```

**Phase 6 (Analyze) synthesizer dispatch — additional duty.** When
spawning the consensus-synthesizer for Phase 6 specifically
(including the clean-pass case with zero unresolved findings),
include in the spawn_agent prompt the directive from
[consensus-protocol.md §Pre-Implement Confidence Emit](references/consensus-protocol.md#pre-implement-confidence-emit-end-of-phase-6-analyze):
after all per-finding `Consensus Result` blocks (or immediately
on a clean pass), the synthesizer MUST emit the
`📊 Confidence: 0.XX` block plus the five criterion lines on
their own lines in its output, so the orchestrator's post-Analyze
write to the workflow log captures it. This is the data source
for the optional Pre-Implement Confidence Gate (G6.5). On
Clarify and Checklist synthesis the synthesizer must NOT emit
this block.

**Why batched.** Per-item serial dispatch wastes wall-clock: 5
items × 3 analysts = 15 sequential turns vs. one batched turn.
Analysts have no cross-item race (they only read); synthesizers
have no race (they propose patches); only Stage 3 edit application
needs serial ordering (write contention).

The escape-hatch keeps routing cheap when right and safe when
wrong: a `[codebase]`-tagged item where codebase-analyst returns
"no precedent in this repo" triggers Round 2 the same turn —
no silently-shipped low-confidence answers.

**Logging requirement:** Every resolution writes a row to the
Consensus Resolution Log in the workflow file with `Round`,
`Routed Categories`, `Outcome`, and `Analysts Used` columns.
The 10% Round-2 escape-rate re-evaluation trigger is computed
from this log (see consensus-protocol.md §"Re-evaluation trigger").

**Consensus rules summary** (full rules in
[consensus-protocol.md](references/consensus-protocol.md)):
- N=1 high-confidence → use answer
- N=2 both-agree → use answer
- N=3 2/3 or 3/3 agree → use majority/unanimous
- Any escape-hatch keyword OR low confidence → fall through to Round 2
- All disagree (Round 2) → flag `[HUMAN REVIEW NEEDED]`, STOP
- Security keyword → always Round 2 with all 3, never single-routed

**Why two layers:** Executor handles ~80% directly. Category-routed
consensus spends model effort on the perspective(s) the executor
identified as relevant.

**Why after each prompt:** Later sessions may depend on earlier
resolved questions/gaps.

**Stop conditions:** Gate failure after 2 auto-fix attempts,
failed consensus (all disagree at Round 2), security keyword
flagged for human, or missing prerequisite.

### 8. Optional Spark helper is advisory only

The main autopilot may optionally spawn `autopilot-fast-helper`
for one of these narrow tasks:

- compress a long executor result into a compact brief
- triage an unresolved item into `codebase`, `spec-context`,
  `domain-research`, or `mixed`
- draft short search queries for a stronger agent to execute

Guardrails:

- Only the parent orchestrator may call this helper
- Executor or consensus subagents must never spawn it
- Use it only for text-only prep work before a real decision
- Never use it to edit artifacts, vote in consensus, or decide gates
- If the helper spawn fails because `gpt-5.3-codex-spark` is unavailable,
  log the failure briefly and continue without it

This helper is a latency optimization, not a dependency.

You run in the **main session** (not as a subagent) so you can
spawn subagents directly. Subagents cannot nest — this is the
Orchestrator-Direct pattern.

## Input

You receive a workflow file path and optional arguments:

```text
path/to/workflow-file.md [--from-phase specify|clarify|plan|checklist|tasks|analyze|implement] [--spec SPEC-ID] [--strict | --advisory]
```

Before Step -1, bind the workflow to the current worktree. If the supplied
path is missing from the current checkout, follow the read-only worktree
resolution contract in `prerequisites-codex.md`. Never read a workflow from
one worktree while running phases or mutations against another checkout.

`--strict` and `--advisory` override the pre-Implement confidence
gate (G6.5) mode for this invocation. They beat
`confidence_gate_mode` in `.claude/speckit-pro.local.md` (or
`.codex/speckit-pro.local.md`). Passing both is a usage error;
STOP before Phase 0 with the conflict message from
the runner helper operation `resolve-confidence-mode`. See [Gate Validation §G6.5](references/gate-validation.md#g65--pre-implement-confidence-gate-between-analyze-and-implement)
and the precedence rule documented there.

## Step -1 + Step 0: Pre-flight (Archive Sweep + Prerequisites)

See [prerequisites-codex.md](./references/prerequisites-codex.md) for the full pre-flight sequence:

- **Step -1: Archive Sweep Startup** — execute the installed archive
  extension's project-local command contract directly in Codex, use the
  Codex-native worktree binding for path prerequisites, and fail closed on a
  broken installed extension
- **Step 0.0: Use Runner Operations** — invoke `speckit_pro_runner` helper IDs with one JSON request on stdin
- **Step 0.1–0.7: Environment Checks** — `check-prerequisites` JSON parsing, branch detection
- **Step 0.6: Load Settings** — `consensus-mode`, `gate-failure`, `auto-commit`, `security-keywords`
- **Step 0.6b: Resolve Pre-Implement Confidence Gate Mode** — run helper
  operation `resolve-confidence-mode` to resolve
  `CONFIDENCE_GATE_MODE` for G6.5. Precedence: `--strict`/`--advisory`
  flag > `confidence_gate_mode` in `.claude/speckit-pro.local.md`
  (or `.codex/speckit-pro.local.md` — the script checks both
  default paths, with `.claude/` winning when both exist) > default
  `advisory`. If the script exits 2 (both flags passed), STOP
  before Phase 0 with the conflict message. **Do not re-run the
  script at G6.5; the gate reads `CONFIDENCE_GATE_MODE` directly.**
- **Step 0.8: Capability Coverage Check** — informational research/context advisory (agents have fallbacks)
- **Step 0.8b: Capability Enumeration, Grounding & Feed-down** — you are the only component that discovers openly. Enumerate the tools and installed skills this session actually exposes and select best-fit per the capability-discovery directive (speckit-pro/skills/speckit-autopilot/references/capability-discovery.md); assume no fixed set — the user may have installed anything. Subagents inherit the operator's full installed surface and follow the same directive — read-only roles select only read/research capabilities (their mutation built-ins are denied). Still pass the discovered evidence a subagent needs directly in each prompt: shared context beats re-discovery. Ground your OWN output (gate decisions, consensus synthesis, PR bodies) per the grounding contract (speckit-pro/skills/speckit-autopilot/references/grounding.md): cite a real tool/skill/file result for every external fact, and abstain when none grounds it.
- **Step 0.9: Constitution Validation** — principle checks against current codebase
- **Step 0.10: Codex Agent Availability Check** — Run the promoted
  `install-codex-agents` helper in `dry_run` mode against the selected project or
  user destination and its installed model choice. If any required file is
  missing or stale, STOP and instruct the user to run `$install`, approve the
  expected local write, and restart Codex. Do not apply the repair inside
  autopilot: the current process cannot reload changed custom agents safely.
- **Step 0.10b: Implementation Agent Detection** — discover `PROJECT_IMPLEMENTATION_AGENT` from `.codex/agents/`
- **Step 0.11: Project Command Discovery** — runner helper `detect-commands` → `PROJECT_COMMANDS`
- **Step 0.12: Preset and Extension Detection** — runner helper `detect-presets` → `PRESET_CONVENTIONS`

If any check fails, STOP with the error message from the script's JSON output. Pass `PROJECT_COMMANDS` and `PRESET_CONVENTIONS` to every subagent prompt.

## Step 1: Parse Workflow State

Read the workflow file and parse the "Workflow Overview" status
table. Find the first phase with status `Pending` or `In Progress`.

If `--from-phase` is specified, start from that phase regardless
of the status table.

If all seven SDD phases are complete, check Post state before stopping.
If every required Post item is complete or explicitly skipped, report
"All phases and post-implementation items complete" and stop. If Post
items are missing, pending, or in progress, continue into Step 1.1 to create
or rebuild the Post plan items, then execute Step 3.

### 1.1 Create Durable Progress Plan

After parsing the workflow state, create a **granular** progress plan
and immediately materialize it in TWO places:

1. `update_plan` with the full checklist
2. `<workflow directory>/autopilot-state.json` with the same items

Do both before Phase 1 or STOP. The initial plan must include every
canonical phase family even when its detailed items will be discovered
later. For multi-prompt phases (Clarify, Checklist), create one item
per prompt/session when known; otherwise create the phase discovery
placeholder.

**Item naming + combined post-impl list (14 mandatory rows including
`Post: Doctor Extension Check` ... `Post: Retrospective` as the FINAL
STEP) + reference `autopilot-state.json` schema:** see
[task-list-canonical-codex.md](./references/task-list-canonical-codex.md).
Mark missing extensions as `skipped: <ext-name> not installed`; never
silently drop the item.

**CRITICAL — phase family coverage is mandatory:**

Before any subagent is spawned, verify that the plan includes at least
one item whose name starts with each of these exact prefixes:
`Archive Sweep:`, `Phase 0:`, `Phase 1:`, `Phase 2:`, `Phase 3:`,
`Phase 4:`, `Phase 5:`, `Phase 6:`, `Phase 6.5:`, `Phase 7:`,
`Post:`.

If any prefix is missing from `update_plan` or `autopilot-state.json`,
STOP, repair both stores, print the corrected checklist summary, and
repeat this coverage audit. A complete workflow plan is required even
when `--from-phase` starts execution in the middle of the workflow.

After writing or repairing `autopilot-state.json`, run the deterministic
coverage guard and STOP on nonzero exit:

```text
python3 "runner helper validate-autopilot-phase-coverage.py" --workflow "$WORKFLOW_FILE" --state "$WORKFLOW_DIR/autopilot-state.json"
```

When `pr-marker-plan.v2` declares a changed-file manifest, append
`--expected-base-commit <live-baseRefOid> --expected-head-commit <live-headRefOid>`.
Fetch both OIDs from live PR metadata immediately before every validation;
never source either authority from the workflow, state, or manifest itself.
Missing, stale, or mismatched external PR authority is blocking.

**CRITICAL — Consensus items are MANDATORY:**

Every Clarify session, every Checklist domain, and the Analyze
phase MUST have a corresponding Consensus item immediately after
it. The consensus item runs the two-layer resolution process
(Rule 6) — skipped only if the executor reports zero unresolved
items. **Never omit consensus items.**

### 1.2 Validate Plan State Before Phase 1

Before Phase 1 starts, validate all of the following or STOP:

- `update_plan` succeeded and the active plan matches the workflow-derived checklist
- `autopilot-state.json` exists and contains the same ordered step list
- Exactly one plan item is `in_progress`
- Every canonical phase family prefix from Phase 0 through Phase 7 plus
  Phase 6.5 and Post appears in both `update_plan` and
  `autopilot-state.json`, with the Archive Sweep item recorded before Phase 0
- `validate-autopilot-phase-coverage.py` exits 0 for the workflow/state pair
- Every Clarify session, Checklist domain, and Analyze phase has its
  mandatory Consensus item
- The checklist summary was printed so progress is visible to the user

## Step 2: Main Execution Loop

For each pending phase the parent orchestrator does six things in
order: pre-phase hooks → spawn executor → consensus resolution →
post-phase hooks → gate validation → auto-commit + advance. Full
11-step pseudocode (including the `PHASES = [...]` canonical order
and `--from-phase` semantics) lives in
[phase-execution-codex.md §Main Execution Loop](./references/phase-execution-codex.md#main-execution-loop).

**Plan-phase reviewability budget (advisory):** After the Plan phase
(G3 pass, `plan.md` exists), the parent runs
runner helper `estimate-reviewable-loc` via `exec_command`, capturing
the exit code so a non-zero exit can never abort the run. Branch on the
JSON `status` (`pass` / `over_budget` / `not_estimated`) or the exit
code, recording the outcome to the workflow file and
`autopilot-state.json`. This is preventive sizing and **advisory only**
— no outcome blocks, prompts mid-autonomous-run, or crashes the run
(hard block / re-slicing is PRSG-010). Full status branch in
[phase-execution-codex.md §Phase 3: Plan — Reviewability Budget](./references/phase-execution-codex.md#phase-3-plan--reviewability-budget-advisory).

**Phase 7 task-list reconciliation (body-pinned invariants):**
After the Tasks phase and G5 pass, parse `tasks.md` and replace
the `Phase 7: Implement - Pending task decomposition` placeholder
with concrete Phase 7 task-group items in both `update_plan` and
`autopilot-state.json`. Before Analyze or Implement can run, validate:

- the placeholder no longer exists in either state store
- at least one concrete Phase 7 item exists
- each concrete Phase 7 item names task IDs from tasks.md
- the tasks-phase reviewability evidence contains no unexpected
  correctness block. Runner helper `reviewability-gate` supports setup mode
  only on the installed runner — tasks mode is deferred, so do not invoke it
  as an active helper. Record the deferred-mode diagnostics (helper ID,
  requested mode, deferral reason), then evaluate the fallback evidence
  chain: the setup-mode gate result recorded at scaffold, the plan-phase
  `estimate-reviewable-loc` verdict, and any operator-ratified split
  decision in the workflow file. A valid current size-only `block` in that
  evidence continues into marker planning and marker emission; it is not a
  manual re-slicing stop.

If any check fails, STOP and repair the plan/state before advancing.

Persist marker planning state when reviewability evidence requires it:
top-level `pr_marker_plan` in `autopilot-state.json`, mirrored workflow
evidence, and repo-relative evidence paths. `tasks.md` is not authoritative
marker state. Preserve correctness stops for malformed/stale marker state,
failed verification, invalid packet, unsafe output, unusable gate evidence,
invalid JSON, missing status/mode, stale fingerprints, and non-size safety
findings.

**Atomicity Route (post-G5 — read-only, advisory, records the route):**
After the Tasks phase and G5 pass, run the read-only atomicity classifier
over the feature directory to decide whether the change can be split into
multiple small PRs safely. Splittability is judged by structural seams
(independent additive capabilities), not lines of code. Run it with
`exec_command` and capture the exit code so a non-zero exit can never
abort the run:

```text
out = exec_command("resolved_python -m speckit_pro_runner < atomicity-route request for specs/<feature>")
# stdout is one decision object: {route, releasable, signals[], hints[],
# warnings[]} on success, or {"error": <string>} with exit 2.
```

The classifier writes no file of its own — **the orchestrator records the
decision** by editing the workflow file's `## Atomicity Route` section with
`apply_patch`, surfacing the four fields `route`, `releasable`, `signals`,
and `warnings`. Route values: `split-PR` (proven additive multi-seam),
`one-navigable-PR` (default / abstain, or modify-heavy), `single-atomic-PR`
(a hard-atomic signature overrides any split), or `out-of-scope`
(empty/missing `tasks.md`). `releasable: false` carries a canonical
"CI-green ≠ releasable" warning for a destructive-migration or
concurrency-sensitive change. It is advisory-only — no outcome blocks the
run, and it never edits or calls the reviewability gate.

**FLAG — this wires NO PR emission and NO branch creation.** Recording the
route here only hands a decision to the downstream layer-planner (PRSG-008)
and multi-PR emission (PRSG-009) work; actually emitting multiple PRs or
creating branches is out of scope for this step. The route is recorded ONLY
in the workflow file — never in the spec map.

**Layer Plan (post-route, pre-Analyze/pre-Implement):**
Immediately after recording the atomicity route, decide whether the
PRSG-008 layer planner is required:

- If `route != "split-PR"`, do not run the planner. Record
  `layer_plan.status="skipped"` with the route reason in
  `autopilot-state.json` and the workflow `## Layer Plan` section, then
  continue.
- If `route == "split-PR"`, run
  runner helper `plan-layers-feature-dir` with `exec_command`,
  capturing stdout, stderr, and exit code before Analyze or Implement
  can continue.
- Exit `0`: parse stdout as the full versioned layer-plan envelope,
  persist that full envelope under `layer_plan` in `autopilot-state.json`,
  write a concise workflow `## Layer Plan` summary, carry any planner
  warnings into implementation context, and continue.
- Exit `1`: STOP before implementation and print exactly:
  `STOP: Layer planner returned invalid_plan (exit 1) for <feature-dir>; implementation has not started. Fix tasks.md using the planner diagnostics below, then rerun autopilot from the Layer Plan step.`
  Then show planner diagnostics from stdout/stderr.
- Exit `2`: STOP before implementation with a distinct `input_error`
  message and include planner diagnostics from stdout/stderr.

The planner is read-only. It creates no branches, PR bodies, stacked PR
topology, or commits; PRSG-009 owns multi-PR emission.

**Post-implementation (after all 7 phases complete + G7 passes):**
Items 10-19 are part of the same durable plan (Step 1.1's Canonical
Post-Implementation Item List — `Post: Doctor Extension Check`
through `Post: Retrospective` as the FINAL STEP). Items 10-14
(Doctor / Verify / Verify-Tasks / Code Review / Integration) form
a parallel group; the serial tail (15-19) handles Reviewability → PR
creation → Review Remediation → Retrospective.

Codex also keeps four supporting rows visible beside the numbered tail:
`Post: Reviewability Diff Gate`, `Post: Self-Review`,
`Post: UAT Runbook Generation`, and `Post: PR Body Generation`. Together with
the numbered gates this is the 14-row combined durable plan. The supporting
rows feed Posts 15/16 and never replace them.

Codex CLI does not have Agent Teams primitives — Codex always uses
the parallel `spawn_agent` pattern (3 tracks fanned out in one tool
turn: Doctor / Code Review / Verify-chain where 11→12→14 chain due
to shared fixtures, then `wait_agent` on all three). The Claude
Code variant capability-detects Anthropic's Agent Teams and routes
to a team when available; the 3-track structure is identical across
all paths.

Per-item runtime + command table, parallel-group dispatch detail,
and extension-availability rules: see
[post-implementation-codex.md](./references/post-implementation-codex.md).

**Dynamic updates:** If consensus reveals new questions or
remediation adds loops, add additional items to your checklist.

### Phase Dispatch

For each phase: read the prompt, spawn a subagent, validate.

#### Subagent Prompt Construction

Use the phase-specific executor agent with this structure:

```text
[IF presets detected in Step 0.12]
PRESET_CONVENTIONS:
  Preset: <name> (priority <N>)
  Overrides: <templates this preset replaces>
  Enforces: <conventions from preset templates>
[/IF]

[IF PROJECT_COMMANDS discovered in Step 0.11]
PROJECT_COMMANDS:
  BUILD: <cmd>  TYPECHECK: <cmd>  LINT: <cmd>
  UNIT_TEST: <cmd>  INTEGRATION_TEST: <cmd>
[/IF]

Workflow prompt:
---
<paste the exact prompt from the workflow file>
---
```

**Agent selection:**

| Phase | Agent | Prefix |
| ----- | ----- | ------ |
| Specify | `phase-executor` | Branch-aware (if ON_FEATURE_BRANCH) |
| Clarify | `clarify-executor` | Parent answers question set |
| Plan | `phase-executor` | None |
| Checklist | `checklist-executor` | None |
| Tasks | `phase-executor` | None |
| Analyze | `analyze-executor` | None |
| Implement | per-task routing | TDD protocol + COMPLETED_TASKS context |

#### Specify — Branch-Aware Prefix

When `ON_FEATURE_BRANCH` is true (Step 0.7), add this prefix to
the subagent prompt before the workflow prompt:

```text
IMPORTANT: Already on feature branch `<CURRENT_BRANCH>`.
Do NOT create a new feature branch.
The branch and `specs/<CURRENT_BRANCH>/` directory already
exist. Skip directly to spec content generation.
```

#### Multi-Prompt Phases + Resolution After Each Prompt

Clarify and Checklist have multiple prompts (one subagent per session
or domain — see Rule 5). After EACH executor subagent returns, run
the two-layer resolution process from Rule 7 BEFORE spawning the next
subagent: parse the executor's "Unresolved for consensus" section,
dispatch the category-routed analysts (Round 1) via `spawn_agent` in
parallel, synthesize, escape to Round 2 if needed, apply edits, log to
the Consensus Resolution Log. The Clarify executor is read-only —
the parent answers returned questions and applies edits (Rule 6).

Per-phase artifact targets after consensus:
- **Clarify:** Apply consensus answers to spec.md, remove `[NEEDS CLARIFICATION]` markers
- **Checklist:** Apply consensus fixes to spec.md or plan.md, re-run domain checklist to verify
- **Analyze:** Apply consensus fixes to tasks.md / spec.md / plan.md, re-run analyze to verify

#### Implement — Task-Level Dispatch

Phase 7 dispatches each task to the best-fit agent instead of one
monolithic executor. Subagents cannot nest — task-level routing
solves this with flat orchestrator-worker.

**Agent routing:**

| Task Type | Agent | TDD? |
|-----------|-------|------|
| Tests (contract/unit/integration) | `implement-executor` | Yes |
| Domain implementation | PROJECT_IMPLEMENTATION_AGENT | Yes |
| Research / API investigation | `domain-researcher` | No |
| Verification (build, lint) | orchestrator-direct | No |

Every implementation agent receives the TDD protocol from
[tdd-protocol.md](references/tdd-protocol.md).
Agent selection is about domain expertise — all follow identical
RED-GREEN-REFACTOR discipline.

**Full algorithm** (parse tasks, route, dispatch, accumulate
context, verify): see [phase-execution-codex.md](./references/phase-execution-codex.md) —
"Phase 7: Implement (Task-Level Dispatch)".

## Step 3: Post-Implementation

After all 7 phases complete and G7 passes, follow the detailed
procedures in [post-implementation-codex.md](./references/post-implementation-codex.md):

1. **3.1 Integration Suite** — verify spec-specific tests exist,
   run FULL suite to catch regressions, fix failures
2. **Self-Review** — mandatory 4-question audit between Integration
   Suite and the PR body; findings are recorded in the workflow log and
   reproduced in the PR body. Reporting step — never gates the PR.
3. **UAT Runbook Generation** — mandatory between Self-Review and the
   PR body. The runner helper `generate-uat-skeleton` is registered as
   deferred, so do not invoke it as an active helper. Reuse a committed
   source-derived runbook when present; otherwise record the UAT skeleton as
   skipped with deferred-helper evidence, then `spawn_agent` the
   `uat-runbook-author` agent only when a skeleton exists. This is fail-open
   and must be logged.
4. **3.2 PR Creation** — final verification, then apply the final
   reviewability boundary. The runner helper `final-reviewability-backstop` is
   registered as deferred, so do not invoke it as an active helper; use current
   committed reviewability evidence or stop before PR side effects if no
   current evidence exists. Only
   `pass`, `warn`, honored typed-exception outcomes, or final `marker_split`
   with a valid current `pr_marker_plan` may continue. A full-diff size block
   with current marker evidence proceeds to marker-based PR emission; it is not
   a manual re-slicing stop. An unexcepted correctness block writes
   `final_reviewability_gate` state plus a `reslicing_required` packet and
   stops only the unsafe PR side effects. It is not a final answer or operator
   handoff: read `autopilot_continuation`, `operator_steps`, and
   `resume.resume_from`, then continue internally through PRSG-007/008/009
   until a valid slice PR stack is emitted or a typed exception is committed.
   Never report completion while `autopilot_continuation.required=true`; a gate
   error writes state and stops without a packet. After a proceed result,
   emit or refresh the feature-local packet at
   `specs/<feature>/.process/pr-packets/<packet-id>.json` with
   `pr-packet-output`. Run it in `dry_run` first, then `apply` only after the
   packet path, body path, base/head target, title, changed-file scope,
   verification evidence, UAT text, non-goals, and known gaps are current.
   `pr-packet-output` writes the packet JSON and packet-owned body file, and
   declares the validation-result path; `generate-pr-body` remains body-only and is not a
   packet substitute. Run `validate-pr-packet-read-only` against the emitted
   packet and consume only the current response `data.stdout_json` in memory
   and durable state. Continue only when it reports `status=passed`,
   `pr_blocked=false`, and the response reports `writes_state=false`. Commit or
   otherwise checkpoint the packet/body artifacts so the worktree is clean, then
   run `validate-pr-packet-write`; apply mode reruns read-only validation before
   persisting the packet's `validation_result_path`. Open
   the PR with packet fields through
   `gh pr create --base --head --title --body-file`; never derive the title
   from the branch, write the body from scratch, pass inline `--body`, reuse
   prior validation evidence, or repair invalid packets after creation. Before
   any single-PR create attempt, run runner helper
   `validate-pr-workflow-contract` with the packet title and changed-file
   list; a nonzero result blocks the aggregate PR path. If the changed files
   include multi-PR candidate commands or final marker-split evidence for more
   than one PR, the single-PR path is forbidden. `multi-pr-emission` may capture
   a `golden_only` command plan, but it does not emit packets or execute PRs.
   Continue only when every required feature-local packet has been emitted or
   refreshed through `pr-packet-output`, passes the same read-only validation,
   and has current persisted validation evidence. For
   split-PR or marker emission, `detect-stack-manager-plan` is registered as
   out of scope, so do not invoke it as an active helper. Use the explicit
   `gh pr create/edit` fallback before any stack-manager mutation. Push,
   create PR, update workflow file.
   Required evidence prompts: gate status/mode/exit/evidence path,
   fingerprint status, ordered marker IDs, checkpoints, warnings, final
   marker_split, packet validation, and PR mappings.
5. **3.3 Review Remediation** — schedule a polling loop to monitor
   and resolve Copilot/human review comments every 5 minutes

After scheduling the loop, run `Post: Retrospective` as the final
canonical Post item, then perform the pre-final completion audit below.

### 3.4 Pre-final completion audit

Before sending any final user-facing response, re-read
`autopilot-state.json` and the workflow file, reconcile them with
`update_plan`, and audit the canonical Post list. You MUST NOT send a
final response if any `Post:` item is `pending`, `in_progress`, or
missing; equivalently, if any Post item is pending, in_progress, or
missing. If the audit finds incomplete Post work, set the first
incomplete item to `in_progress` in both state stores and continue the
autopilot loop instead of summarizing. `Post: Retrospective` is the final
Post item; it must be completed or explicitly skipped before the
autopilot can report completion.

Audit invariant: any Post item is pending, in_progress, or missing means
the autopilot is not complete.

Only after every Post item is completed or explicitly skipped, and the
PR URL is known, the autopilot is DONE. Report the final summary with
PR URL.

## Workflow File Update Protocol + Error Recovery

- **Per-phase workflow-file section updates** (Specify Results table,
  Clarify Results, Plan Results, Checklist Results + Addressing Gaps,
  Tasks Results, Analysis Results, Implementation Progress + Post-Impl
  Checklist + Success Criteria) — see
  [workflow-file-protocol-codex.md](./references/workflow-file-protocol-codex.md).
  Also: Constitution Validation table after Specify (initial) + Implement
  (final), and Consensus Resolution Log entries when consensus was used.
- **Resume protocol** (`autopilot-state.json` reconciliation, missing-state
  reconstruction, `--from-phase` semantics), **common issues** (subagent
  retry, gate failure, consensus all-disagree, MCP unavailable), and
  **context window management** — see
  [error-recovery-codex.md](./references/error-recovery-codex.md).

## References

**Codex-specific (lifted from this SKILL.md body):**
- [Prerequisites for Codex](./references/prerequisites-codex.md) — Step -1
  Archive Sweep + Step 0.0-0.12 (scripts path, env checks, settings,
  MCP, constitution, Codex agent availability, implementation agent
  detection, command discovery, preset detection)
- [Canonical Task List for Codex](./references/task-list-canonical-codex.md) —
  Step 1.1 checklist naming pattern, 14 mandatory Post rows, item-naming
  rules, reference `autopilot-state.json` schema
- [Phase Execution for Codex](./references/phase-execution-codex.md) —
  PHASES order, agent mapping, main execution loop (11-step per-phase
  pseudocode), Phase 7 implement detail, PR body generation, coverage audit
- [Post-Implementation for Codex](./references/post-implementation-codex.md) —
  Items 10-19 table plus supporting-row mapping, parallel group dispatch (Doctor/Code Review/Verify-chain),
  extension availability rules
- [Workflow File Update Protocol for Codex](./references/workflow-file-protocol-codex.md) —
  Per-phase section updates + Constitution + Consensus Log
- [Error Recovery for Codex](./references/error-recovery-codex.md) — Resume
  protocol, common issues, context window management

**Shared CC references (still applicable to Codex):**
- [Consensus Protocol](references/consensus-protocol.md) —
  Multi-agent resolution rules and flows
- [Gate Validation](references/gate-validation.md) —
  Programmatic gate checks and remediation loops
- [TDD Protocol](references/tdd-protocol.md) —
  Red-green-refactor rules injected into implementation agent prompts
- [Plugin Limitations](references/plugin-limitations.md) —
  permissionMode, hooks, mcpServers restrictions for plugin agents;
  research/context capability coverage and fallback behavior
- [Token Discipline](references/token-discipline.md) —
  Opt-in compressed vocabulary for inter-agent transcripts
  (off by default; never applied to PR bodies, logs, or artifacts)

## Runner Operations

Deterministic prerequisite checks, validation, reviewability, routing, payload,
and PR-preparation behavior is owned by `speckit_pro_runner`. Invoke
`resolved_python -m speckit_pro_runner` with one JSON request on stdin and use the
registered helper or gate operation IDs below.

- `check-prerequisites` — Verify CLI, project init, constitution, commands,
  branch detection, and workflow file readiness (JSON).
- `validate-gate` — Validate G1-G7 with marker counts and details (JSON).
- `confidence-gate` — Read the synthesizer's `📊 Confidence: X.XX`
  pre-Implement emit and decide whether Phase 7 may begin.
- `resolve-confidence-mode` — Resolve the pre-Implement confidence mode from
  invocation flags, local config, or the advisory default.
- `reviewability-gate` — Enforce the setup-mode reviewability budget. Tasks
  and pre-PR modes are deferred for installed workflows; record the deferral
  and use committed fallback evidence per the guidance above instead of
  invoking them.
- `atomicity-route` — Classify whether a feature should remain one PR or split.
- `plan-layers-feature-dir` — Emit a versioned layer-plan envelope for split
  routes before implementation.
- `estimate-reviewable-loc` — Project production reviewable LOC from declared
  file operations.
- `generate-pr-body` — `golden_only` body writer accepting exactly
  `output_path`, `title`, and `sections`; it writes one Markdown body and does
  not emit packet JSON, metadata, markers, validation evidence, or PR commands.
- `pr-packet-output` — `golden_only` packet emitter accepting structured
  packet fields; it writes the feature-local packet JSON, packet-owned body
  file, and declared validation-result path used before PR creation.
- `validate-pr-packet-read-only` — Validate an existing feature-local packet and
  return the result in `data.stdout_json` with `writes_state=false`; it does not
  persist validation state.
- `validate-pr-packet-write` — Rerun read-only packet validation in apply mode,
  then persist that current passing result to the packet's
  `validation_result_path`; do not use caller-supplied or stale validation
  results.
- `validate-pr-workflow-contract` — Validate PR title and changed-file scope.
- `detect-commands`, `detect-presets`, and `count-markers` — Provide
  deterministic command, preset, and marker evidence through runner-owned
  operation IDs.
- `install-codex-agents` — Content-aware Codex agent refresh used in `dry_run`
  mode during preflight; apply only through `$install`, followed by a Codex
  restart.
- `generate-uat-skeleton`, `final-reviewability-backstop`, and
  `detect-stack-manager-plan` — Registered
  but not active helper calls for installed workflows; follow the deferred or
  out-of-scope guidance above instead of invoking them.
- `relocate-process-artifacts` and `restack` — Registered but deferred with no
  active invocation contract. Do not invoke them or infer capability from
  generic runner plumbing.
