---
name: speckit-autopilot
<!-- host:claude: Claude reads a trigger-phrase description and Claude-only frontmatter keys -->
description: >
  Autonomous SpecKit workflow executor. Reads a populated workflow file
  and executes all 7 SDD phases (specify → clarify → plan → checklist →
  tasks → analyze → implement) with programmatic gate validation,
  multi-agent consensus resolution, and auto-commits. Use when the user
  says "run autopilot", "execute workflow", "autonomous speckit",
  or has a workflow file ready for execution.
user-invocable: true
disable-model-invocation: true
allowed-tools: Read Edit Write Glob Grep Skill Agent ToolSearch
license: MIT
<!-- /host -->
<!-- host:codex: Codex keeps its own selection description and names skills with a dollar sign -->
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
  methodology questions ($speckit-pro:speckit-coach), pre-spec scoping
  ($speckit-pro:grill-me), new-spec setup ($speckit-pro:speckit-scaffold-spec), status
  checks ($speckit-pro:speckit-status), or PR comment resolution
  ($speckit-pro:speckit-resolve-pr).
<!-- /host -->
---

# SpecKit Autopilot — Autonomous Execution Engine

<!-- host:claude: Claude loads an invoked skill through the Skill tool, which a redundant call can reinvoke -->
## Explicit Invocation Boundary

When `/speckit-pro:speckit-autopilot` loads this file, the skill is already
active. Do not invoke the `Skill` tool for `speckit-pro:speckit-autopilot`
again; start with these instructions. A rejected redundant `Skill` call is not
a prerequisite failure and does not authorize stopping the workflow.

<!-- /host -->
## Installed Runtime Contract

Installed Claude and Codex surfaces resolve Python 3.11 or newer, invoke
`[resolved_python, "-m", "speckit_pro_runner"]`, send one JSON request on
stdin, read one JSON response from stdout, and surface stderr diagnostics.
Do not add a shell fallback, `jq` parsing path, Git Bash, WSL, or
PowerShell-specific command-language requirement for installed workflows.

## Scope

This skill handles autonomous workflow EXECUTION. For methodology
questions, SDD philosophy, comparisons, design rationale, deep dives, or
learning how SpecKit works, redirect the user to
<!-- host:claude: Claude names skills with a slash -->
`/speckit-pro:speckit-coach`
<!-- /host -->
<!-- host:codex: Codex names skills with a dollar sign -->
`$speckit-pro:speckit-coach`
<!-- /host -->
when the user is asking for explanation rather than execution. Do not redirect a real
implementation request merely because it asks for detailed progress or uses
the word "implement": when the user supplies or identifies a populated
workflow and asks to run, resume, or implement it, this remains an autopilot
execution request.

You are an **orchestrator** for SpecKit workflows: read prompts from
the workflow file and delegate each phase to a **subagent** that runs
the phase's SpecKit command. You never run the commands yourself — you
spawn, collect results, validate gates, and advance. Your context
window auto-compacts, which is not a stopping point: complete every
phase in the **resolved stage's** range (`AUTOPILOT_STAGE`, set at Step
0.6c). A `--stage plan` run finishes its work after the confidence gate.
A `full` run completes all 7 phases.

When a run may involve a human, and which reasons count, is set by the shared
[Autopilot Stop Policy](./references/stop-policy.md).

**Neither is a status summary a stopping point.** Reporting progress to the
operator is not a step in the workflow: when a phase still has work, the next
<!-- host:claude: Claude dispatches through its native subagent tool -->
dispatch goes in the same turn as the report. Ending a turn with no dispatch
running and tasks still pending leaves nothing to wake the run, which stops the
<!-- /host -->
<!-- host:codex: Codex dispatches and collects agents with spawn_agent and wait_agent -->
`spawn_agent` or `wait_agent` call goes in the same turn as the report. Ending a
turn with no agent in flight and tasks still pending leaves nothing to resume
the run, which stops the
<!-- /host -->
stage short of its terminal step. See
[Phase Execution §Never Yield With Nothing In Flight](./references/phase-execution.md#never-yield-with-nothing-in-flight).

## Architectural Constraint — Main Agent Is The Orchestrator

This skill loads into the **main session agent**, which owns all phase and
lifecycle dispatch. EVERY workflow dispatch decision — parallel subagents vs
sequential, model routing, and lifecycle sequencing — happens HERE. Phase
executors are terminal workers; they don't dispatch workflow phases or
orchestrate later phases. **If this skill is ever loaded inside a subagent
context**, it MUST refuse and surface the violation rather than orchestrate.

<!-- host:claude: Claude agent frontmatter and Agent Teams carry this invariant -->
Current Claude Code can nest subagents, but this workflow deliberately keeps
one orchestration owner: the main session. Phase executors don't branch on
`AGENT_TEAMS_AVAILABLE` or create teams.

Runtime enforcement is two-tier (Layer 5 verifies both): the
hyper-focused single-purpose workers (the consensus analysts,
clarify-executor, uat-runbook-author) explicitly deny
`Agent`/`SendMessage` via `disallowedTools` so they stay
on their one job; the open workhorse executors (phase-, analyze-,
checklist-, implement-executor) keep the operator's full surface —
including orchestration tools — and the invariant there is carried by
this skill owning all PHASE dispatch plus each executor's
terminal-worker prompt, never by a capability block. Full invariant +
implications for new workstreams in
[`references/agent-teams-integration.md`](./references/agent-teams-integration.md)
§Single orchestrator invariant.

The no-allowlist rule is about **agent definitions**: Claude agents must omit
`tools:` so they inherit the operator's installed surface. This skill's
frontmatter may still declare Claude `allowed-tools` to authorize the
orchestrator's core primitives; that declaration is not an MCP/vendor
availability list and does not replace runtime capability discovery.

Skill `allowed-tools` pre-approves the listed core primitives; it is not
capability discovery. Runner calls still follow the session's permissions, so
the Step -2 run-start permission probe checks them once, before any phase work,
and stops with the exact allow rule if a call prompts or is denied. See the
plugin agent caveat in Step 0 and
[`references/plugin-limitations.md`](./references/plugin-limitations.md).
<!-- /host -->
<!-- host:codex: Codex exposes collaboration actions that vary by surface -->
Discover the current host's actual collaboration capabilities below; do not
infer architecture from a universal nesting limit.

## Codex Runtime Contract

This Codex variant is a concrete tool contract, not advisory prose.
Bind the workflow to actual Codex primitives:

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
  delivered result, use its one read-only reconciliation to drain the mailbox
  and inspect effects; checkpoint if unknown, never automatically re-spawn.
- Every custom-agent dispatch MUST pass
  `agent_type="<installed-agent-name>"` to `spawn_agent`. Never omit
  `agent_type` or accept a `default` or general-purpose worker as equivalent to
  the installed role.
- When `close_agent` is exposed, call it promptly after consuming the result.
  Cleanup policy is best-effort: if the surface reports the agent already gone,
  log it and continue without retry-looping. When `close_agent` is absent,
  consume the result and leave the inspectable thread to the host; optionally
  reuse it with the available follow-up action.
- On resume, never assume an older agent still exists. If `list_agents` is
  available, match returned current-tree entries to the workflow target and
  current incomplete plan item's canonical task name/prompt; manage or reuse
  only agents confirmed present and owned by this autopilot run. Without
  inspection, treat prior-session effects as unknown and checkpoint; never
  treat a stale reference as permission to spawn fresh.
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
  context and is not closure. Reconcile the interrupted item's retained result
  and effects; unknown outcomes checkpoint, never authorize replacement work.
- Before reporting the run complete, use `list_agents` when exposed; otherwise
  audit the tracked dispatch IDs and consumed results. Every required dispatch
  must have a consumed result. Close remaining current-run threads best-effort
  only when `close_agent` is exposed. Hosted completed threads are host-managed
  and do not block completion.
- `autopilot-fast-helper` is OPTIONAL. Only the main autopilot may invoke it,
  and only for tiny text-only compression, triage, or query-drafting work.
  Never route edits, gate decisions, or consensus votes through it.
- Use the current surface's exposed read, search, command, and edit equivalents
  for workflow parsing, validation, and artifact mutation.
- Persist orchestration state to `autopilot-state.json` in the same directory
  as the workflow file. It mirrors the active run: on resume, read it and
  reconcile it with the workflow file, which wins for the Workflow Overview and
  `Stage` (Step 0.6e and the Workflow File Update Protocol below).
- This skill owns `./agents/openai.yaml` as Codex skill metadata for UI
  appearance and invocation policy. Optional research/context capabilities are
  discovered at runtime, so the sidecar MUST NOT declare Tavily, Context7, or
  any other optional capability as a required tool dependency. Do not treat
  that sidecar as a custom-agent manifest.
- SpecKit Pro also ships bundled custom-agent templates under
  `../../codex-agents/`. Those bundled TOML files are package assets, not
  runtime registrations.
- Custom executor and consensus agents must be installed as real Codex
  subagents under `.codex/agents/` (project scope) or `$CODEX_HOME/agents/`
  (user scope; default `~/.codex/agents/`). The bundled `install` skill
  copies the plugin templates into those official Codex runtime paths.

Do not translate this skill into Claude-only primitives such as legacy
Claude agent/shell placeholders. Do not read the
bundled TOML templates and inline them as ad hoc prompts. Validate that the
required custom subagents are installed, then spawn them by agent name. Before
any phase work, at setup or run start, if any required SpecKit Pro subagent is
missing, STOP and instruct the user to run `$speckit-pro:install` from the SpecKit Pro
plugin, then restart Codex. After phase work has begun, a plugin update or agent
refresh is never a stop: follow §Plugin Update Mid-Run: Record, Re-resolve,
Continue in [phase-execution.md](./references/phase-execution.md).
<!-- /host -->

## Prerequisites — Model

For every research-agent dispatch, pass **Research run id:** from the genuine
execution-control `result.data.ledger.run_id`; use it as broker `run_id`.
Copy **Research provider decisions** into the workflow's decisions list once per `id`,
preserving the broker's decision, alternative, provider, and reason. Cached failures
add no rows; continue independent work and record any research left unverified.

The orchestrator makes gate decisions, coordinates consensus synthesis, and
manages a 7-phase workflow. After every analyst round it dispatches the named
synthesizer (`speckit-pro:consensus-synthesizer` on Claude Code,
`consensus-synthesizer` on Codex), awaits it, and consumes its actual returned
result. The parent never substitutes its own synthesis. In both hosts, the
parent owns artifact application and gates. Weak-model orchestration cascades
into expensive rework.

**Before executing any step**, verify:

<!-- host:claude: Claude model tiers are named by the operator's session -->
1. **Model:** run on the operator's strongest available tier. If the
   session does not report the strongest tier, warn the operator once and route gate and consensus dispatches to the strongest available tier.
<!-- /host -->
<!-- host:codex: Codex names its model tiers -->
1. **Model:** run on the highest-capability Codex model tier available. Prefer
   `gpt-6-sol` when it is available in the Codex model picker; `gpt-6-astra`
   is also acceptable. If the session is on a mini, fast, Luna, or otherwise
   reduced-capability tier, warn the operator once and route gate and consensus
   dispatches to the strongest available tier. `$speckit-pro:install` owns bundled-agent
   installation and fallback configuration.
<!-- /host -->

**Reasoning effort is inherited, never checked.** Run at whatever the
operator has set for the session and do not stop, warn, or ask them to
change it. The bundled subagents carry their own pins: judgment roles
ship at a measured high effort (`high`, `xhigh`, or `max` on Claude;
`medium`, `high`, `xhigh`, or `max` on Codex), and bounded rule-applying
roles that only apply rules to inputs already in their prompt ship at
the documented default.
<!-- host:codex: only Codex ships the optional Luna helper -->
The optional `autopilot-fast-helper` is pinned to low effort on gpt-6-luna
for latency-sensitive prep.
<!-- /host -->
A pin sets that worker's effort regardless of
the session and never refuses to run.
The operator owns the session setting; the plugin does not veto it.

## Execution Rules

At kickoff/resume, read [Bounded Execution and Verification](./references/execution-efficiency.md).
Initialize/recover its durable execution-control ledger before phase dispatch.
It owns task metadata, native batching, proof reuse, the shared repair
ceilings, and the honest checkpoint rules across every phase, nested worker,
and Post step. Agent replacement never resets budgets. A run has no
wall-clock limit.

When a bounded request supplies an exact native command together with an
invocation count or order, that command is the authority. Execute each listed
command exactly once and in order, with no interpreter preflight, shell
variable, wrapper, replay, capture redirection, or substituted command unless
the request explicitly permits it. Consume the direct native result; do not
rerun a helper merely to make its output easier to parse. The native tool result
is the captured result: preserve that direct response for later artifacts. Do
not issue a second invocation to obtain a file, exit code, stdout, or stderr.

<!-- host:claude: Claude discovers its native worker actions from the active tool surface -->
### Claude native worker lifecycle

- Discover the current native worker, follow-up, wait/result, inspection,
  interruption, and cleanup actions before dispatch. Do not infer a capability
  from a tool name mentioned in prose.
- Derive the usable worker count from the active surface. When no count is
  exposed, use one worker as the safe fallback unless a narrower workflow
  contract explicitly owns a bounded parallel group **and** the active native
  surface can execute that group within its exposed limit. Work wider than the
  usable count proceeds in waves; a named parallel group never overrides the
  host's actual cap.
- Use a separately discovered native worker action for follow-up, wait, and
  result consumption. If only a foreground worker call is available, its direct return is the final
  report and each later call is a new attempt, not reuse.
- Every asynchronous dispatch follows launch, bounded wait or polling, and
  consumption of that worker's actual final report. A launch receipt, ordinary
  message, timeout, or terminal status is not the required result.
- A single timeout is only a poll boundary. Interrupt or cancel only a
  confirmed stuck running turn after the separate execution deadline. An
  interruption is neither closure nor a result.
- After interruption or a missing result, reconcile the tracked dispatch and
  owned effects once, then checkpoint unknown state. Never automatically
  respawn work until the original attempt is proven unable to return.
- Cleanup is best-effort when the host exposes it; do not retry-loop an
  already-gone worker. When cleanup is absent, leave the completed inspectable
  worker to the host. Before completion, audit every tracked worker and consume
  every required final report.

<!-- /host -->
### 0. Forbidden skill invocations

<hard_constraints>

**Do not invoke `grill-me` from any autopilot phase, subagent, or consensus step — ever.**

<!-- host:claude: Claude grill-me interviews through AskUserQuestion -->
`grill-me` is human-in-the-loop only — it uses `AskUserQuestion` to
interview a real user one question at a time. Autopilot may run
unattended, with no user available; calling it would block indefinitely or produce
low-value automated output that defeats its purpose.
<!-- /host -->
<!-- host:codex: Codex grill-me probes request_user_input and a TTY -->
Grill-me is a strictly human-in-the-loop, pre-workflow scoping interview. Its
runtime guard probes for `request_user_input` then a TTY before asking any
question; if invoked from autopilot's autonomous loop it will refuse and write
nothing — but the autopilot must not even attempt the call.
<!-- /host -->

If a phase encounters ambiguity that feels like it needs grill-me, the correct
response is one of:

<!-- host:claude: Claude names skills with a slash -->
- Run `/speckit-clarify` (Phase 2) with the multi-agent consensus protocol —
  that is autopilot's only clarification mechanism.
- Route the ambiguity to Clarify consensus, and defer it when consensus cannot settle it. Pre-workflow interviews
  belong in `/speckit-pro:speckit-scaffold-spec` or `/speckit-pro:grill-me`, not autopilot.
<!-- /host -->
<!-- host:codex: Codex names skills with a dollar sign -->
- Run the `$speckit-clarify` skill (Phase 2) with the multi-agent consensus
  protocol — that is autopilot's only clarification mechanism.
- Route the ambiguity to Clarify consensus, and defer it when consensus cannot settle it. Pre-workflow interviews
  belong in `$speckit-pro:speckit-scaffold-spec`, not autopilot.
<!-- /host -->

This rule applies to: the orchestrator, every phase subagent
(`phase-executor`, `clarify-executor`, `checklist-executor`,
`analyze-executor`, `implement-executor`), every consensus analyst
(`codebase-analyst`, `spec-context-analyst`, `domain-researcher`), and
`consensus-synthesizer`.

</hard_constraints>

### 1. Subagent per phase

<!-- host:claude: Claude launches subagents with its Agent or Task tool -->
For each phase, spawn a **foreground subagent** via the native subagent tool
(`Agent` when exposed, otherwise its renamed `Task` equivalent) with
`run_in_background: false`. If `Task` is listed but deferred,
load it with `ToolSearch` query `select:Task`. The subagent runs the
`/speckit-*` command and returns a summary. You (the parent) receive
the result as a tool call response, which keeps your agent loop alive.
Treat async-launch metadata as launch acknowledgement only; collect the
actual terminal summary through the native result handling before validating
the gate or advancing the phase. The foreground request is not a host-level
guarantee.
<!-- /host -->
<!-- host:codex: Codex launches and collects subagents with spawn_agent and wait_agent -->
For each phase, spawn a **foreground subagent** with `spawn_agent`,
wait for it with `wait_agent`, and keep orchestration in the parent.
The subagent runs the SpecKit command and returns a summary.
<!-- /host -->

**Why:** If you invoke a skill directly in your own context, the command's
completion behavior causes your loop to output plain text and terminate.
With subagents, the command runs in an isolated context and its completion
is harmless — the result returns to you and your loop continues.

<!-- host:claude: Claude invokes an installed skill through Skill() -->
**Third-party skills:** the same hazard applies when capability discovery
selects an *installed* skill you invoke via `Skill()` — its completion text
can end your loop. Capture the skill's result as evidence and continue with a
follow-up tool call; never treat a third-party skill's completion text as your
own terminal output.
<!-- /host -->
<!-- host:codex: Codex invokes an installed skill with a dollar sign -->
**Third-party skills:** when capability discovery selects an installed skill you
$-invoke, its completion text can likewise end the loop. Capture the skill's
result as durable state/evidence and continue; never treat a third-party skill's
completion text as your own terminal output.
<!-- /host -->

### 2. Use phase-specific executor agents

Each phase type has its own specialized executor agent. All noise
stays in the subagent's context; the parent receives only a summary.
For planning, use the runner's phase brief in Step 2 as the dispatch authority.

<!-- host:claude: Claude resolves bundled agents by their speckit-pro: namespaced id -->
| Phase | Agent | Why specialized |
| ----- | ----- | --------------- |
| Specify, Plan, Tasks | `speckit-pro:phase-executor` | Heavy reasoning (Specify, Plan); mechanical for Tasks. Single skill invocation, single summary. |
| Clarify | `speckit-pro:clarify-executor` | Read-only question set; parent answers and edits |
| Checklist | `speckit-pro:checklist-executor` | Must run checklist AND remediate gaps with research |
| Analyze | `speckit-pro:analyze-executor` | Resolve required defects at every severity using relevant evidence and the shared repair reservation |
| Implement | per-task routing | Route tasks with TDD; dispatch validated capability batches or legacy singletons |

The per-dispatch context lines (`Workflow root:` and the Specify branch
prefix) live in [`references/phase-execution.md`](./references/phase-execution.md)
§Subagent Delegation; implementation dispatch lives in its §Phase 7: Implement.

**Agent-type namespacing (required):** the prefix requirement applies to every
speckit-pro **bundled agent id** used as a `subagent_type` value — the
executors above and the analysts in the routing tables below dispatch with
their `speckit-pro:` prefix (`speckit-pro:phase-executor`,
`speckit-pro:clarify-executor`, …). The runtime resolves plugin agents by their
namespaced id, so a bare `subagent_type: "phase-executor"` fails immediately
with `Agent type 'phase-executor' not found`. Identifiers that take **no**
prefix: `general-purpose` (a built-in agent), and entries in the tables that are
not bundled agent ids — the `PROJECT_IMPLEMENTATION_AGENT` variable (resolved to
a host-project agent, with `speckit-pro:phase-executor` as its fallback value)
and `orchestrator-direct` (the orchestrator acting directly, not a subagent).
<!-- /host -->
<!-- host:codex: Codex resolves installed agents by their bare name from .codex/agents -->
| Phase | Agent | Why specialized |
| ----- | ----- | --------------- |
| Specify, Plan, Tasks | `phase-executor` | Heavy reasoning (Specify, Plan); mechanical for Tasks. Single skill invocation, single summary. |
| Clarify | `clarify-executor` | Read-only question set; parent answers and edits |
| Checklist | `checklist-executor` | Must run checklist AND remediate gaps with research |
| Analyze | `analyze-executor` | Resolve required defects at every severity using relevant evidence and the shared repair reservation |
| Implement | `implement-executor` | Strict TDD with validated capability batches of up to four sequential tasks; parallel waves must respect metadata ownership/dependencies and derived `subagent_slots`. Consume each actual per-task result before marking completion. Legacy workflows use singleton execution. |
| Read-only consensus | analyst agents | Read-heavy code/spec/domain analysis |

Concrete Codex mapping:

- `./agents/openai.yaml` is skill metadata only. It does not register custom
  agents for Codex.
- Resolve the installed agent from `.codex/agents/<agent>.toml` first, then
  `$CODEX_HOME/agents/<agent>.toml` (default `~/.codex/agents/`)
- If the installed agent is missing at setup or run start, STOP and tell the
  user to run `$speckit-pro:install`, then restart Codex. Mid-run, follow §Plugin Update
  Mid-Run: Record, Re-resolve, Continue instead
- Build the phase prompt in the parent session
- Call `spawn_agent` with `agent_type="<installed-agent-name>"` plus the
  workflow prompt
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
<!-- /host -->

### 3. Canonical plan first

The canonical execution order is:

```text
PHASES = [specify, clarify, plan, checklist, tasks, analyze, implement]
```

Before phase work starts, the parent session MUST persist a granular progress
plan in `autopilot-state.json`. After each subagent returns, read that plan
to select the next item.
The plan accounts for every phase in that list plus prerequisites and
post-implementation verification. Execution starts and stops within the stage
resolved at Step 0.6c; phases outside that stage stay visible but are not
started. `--from-phase` changes the starting index only within the resolved
stage. It does not remove plan entries from `autopilot-state.json`.
See Step 1.1 for the full naming pattern and rules.

### 4. Multi-prompt phases

Clarify and Checklist have multiple prompts in the workflow file.
Spawn a **separate subagent for each prompt**, consume its result, and run the
two-layer resolution (Rule 6) after each one BEFORE spawning the next — later
sessions/domains may depend on earlier resolved items. Do not batch
all sessions and check for markers only at the end.

Per-phase flow templates (per-session for Clarify, per-domain for
Checklist) live in
[`references/phase-execution.md`](./references/phase-execution.md)
<!-- host:claude: the Claude phase reference groups the flows per phase -->
§Phase-by-Phase Execution.
<!-- /host -->
<!-- host:codex: the Codex phase reference keeps the flows in its main loop -->
§Main Execution Loop.
<!-- /host -->

### 5. Clarify — executor returns questions to parent

The `clarify-executor` is read-only. It does not invoke
<!-- host:claude: Claude names skills with a slash -->
`/speckit-clarify`,
<!-- /host -->
<!-- host:codex: Codex names skills with a dollar sign -->
`$speckit-clarify`,
<!-- /host -->
does not wait on a user, and does not edit
artifacts. It inspects the workflow prompt, feature spec, and repo
evidence, then returns a `Clarify Question Set` containing up to 5
prioritized questions, recommended answers, evidence, and suggested
artifact updates.

The parent orchestrator answers the returned questions in the main
session, applies the spec/workflow/state edits, then checks for
remaining `[NEEDS CLARIFICATION]` markers and resolves unresolved
items via consensus if needed (see Rule 6).

### 6. Two-layer resolution with category-routed consensus

After EACH Clarify, Checklist, or Analyze executor returns, complete consensus
before the next prompt. The parent applies accepted Clarify edits; all three
executors surface remaining items with category tags. For every such item,
call `parse-consensus-categories`, dispatch exactly the routed analysts in
host-bounded batches, and consume their actual results. After every analyst
round — including a round with one or two analysts — dispatch the runtime's
named `consensus-synthesizer`, await it, validate and consume its actual returned
result, then apply accepted artifact edits serially and run gates in the parent.
The parent MUST NOT synthesize directly or silently replace a missing, failed,
or malformed synthesizer result. Such a result authorizes no edit and cannot
mark consensus complete. Append the Consensus Resolution Log only from a valid
consumed result.
<!-- host:codex: Codex dispatches the installed synthesizer by agent_type -->
Follow the mandatory Codex dispatch form `spawn_agent` with
`agent_type="consensus-synthesizer"`.
A default or general-purpose worker is not the named synthesizer; its result is
invalid.
<!-- /host -->
Follow the mandatory Round 2, Round 3 tiebreak, stop,
re-evaluation, and Phase 6 confidence-emit contracts in
[`references/consensus-protocol.md`](./references/consensus-protocol.md)
§Category-Routed Dispatch, §Batched Dispatch, §Round 3 Tiebreak,
§Phase-Specific Consensus Flows, and §Logging.

### 6a. Plan ambiguity uses provenance, not consensus

If G3 fails because Plan contains unresolved requirement wording, the parent
orchestrator MUST follow
[`references/gate-validation.md`](./references/gate-validation.md)
§Plan ambiguity provenance repair before escalation. Trace the wording to its
original source, assign the required provenance class, write the conditional
Plan Ambiguity Repair Log, and give the same Plan executor at most 2 repairs,
re-running G3 after each. This is separate from Rule 6 consensus: repeated
agent agreement cannot make an inferred premise user-ratified.

<!-- host:codex: only Codex ships the optional Luna helper -->
### 7. Optional Luna helper is advisory only

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
- If the helper spawn fails because `gpt-6-luna` is unavailable,
  log the failure briefly and continue without it

This helper is a latency optimization, not a dependency.

<!-- /host -->
## Input

You receive a workflow file path and optional arguments:

```text
path/to/workflow-file.md [--from-phase specify|clarify|plan|checklist|tasks|analyze|implement] [--spec SPEC-ID] [--stage plan|implement|full] [--strict | --advisory]
```

`--stage` selects which range of phases this invocation runs; omit it and
Step 0.6c resolves the stage from the workflow file's own status table.
Argument order is presentation only — every argument is read by name.

<!-- host:claude: Claude settles the session's permission settings with one probe -->
Before anything else, run the Step -2 run-start permission probe in
[`references/prerequisites.md`](./references/prerequisites.md#step--2-run-start-permission-probe):
one no-op runner request and one `git status`. If either prompts or is denied,
print the exact allow rule and stop once, before any phase work.

Before Step -1, use the read-only `resolve-workflow-binding` runner helper to
verify that Claude Code's live checkout already owns the workflow. Continue
only for `binding_status=resolved` with `relation=same`. If scaffold was run
from a parent checkout, follow the printed `/cd <absolute-worktree-root>` and
then retry the relative autopilot command. Never run Archive Sweep or mutate
the workflow's worktree from the parent checkout.
<!-- /host -->
<!-- host:codex: Codex binds each command's workdir to the workflow root and settles egress in a run-start authorization -->
Before anything else, run the Step -2 run-start authorization in
[`references/prerequisites.md`](./references/prerequisites.md#step--2-run-start-authorization):
before Archive Sweep and any phase work, probe each egress class, an external
workflow root, and the private autonomy-record write, and make the one
run-start request ([run-start grants](./references/stop-policy.md#run-start-grants)).

Before Step -1, use the `resolve-workflow-binding` runner helper exactly as
specified in `prerequisites.md`. That reference owns the executable-root
invariant and fail-closed recovery.
<!-- /host -->

## Step -1 + Step 0: Pre-flight (Archive Sweep + Prerequisites)

Run the pre-flight sequence before any phase work. A failure goes to the owning agent for repair; only an exhausted repair defers.

1. **Use runner helper operation IDs**. Invoke read-only helper behavior through
   `resolved_python -m speckit_pro_runner` with one JSON request on stdin; do not rely on
   plugin-local script files.
<!-- host:claude: Claude runs the archive extension's generated slash command -->
2. **Archive Sweep** — run helper `list-archive-candidates` with the current
   spec directory, then on feature/spec branches run
   `/speckit-archive-run specs/<merged-spec-dir> --spec-only --plan-only --changelog-only` once per
   `archive_order` entry, in order. The three scope modifiers keep the run out
   of agent context files (stock extension step 5.3). On `main`, release, or any protected integration branch,
   record the helper report as a dry run and archive nothing. Skip if the
   archive extension is absent. Excludes the current target spec. Distinguish
   an absent extension from a broken installation: if the extension is present
   but `/speckit-archive-run` is missing or unregistered, defer the Archive
   Sweep with that discovery evidence and continue to Phase 0, listing the
   repair/install guidance under "Decisions for you". A failed archive run is
   retried once, then deferred the same way. Never silently treat a missing
   archive command as an absent extension.
<!-- /host -->
<!-- host:codex: Codex executes the archive extension's project-local command contract directly -->
2. **Archive Sweep** — list merged prior specs with helper
   `list-archive-candidates`, then execute the installed archive extension's
   project-local command contract directly in Codex once per `archive_order`
   entry (`archive command: specs/<merged-spec-dir> --spec-only --plan-only --changelog-only`, which keeps
   agent context files out of scope; none on `main` or a protected branch), use the Codex-native worktree binding for path
   prerequisites, and fail closed on a broken installed extension: defer the
   Archive Sweep with the exact failed path or operation and continue to Phase 0.
<!-- /host -->
3. **Run the G0 setup seam** — call runner helper `g0-setup` in `read_only`
   mode once per `inputs.probe`, in order: `prerequisites`, `commands`,
   `presets`. Each call carries `inputs.workflow_file` and `inputs.surface`.
<!-- host:claude: Claude's G0 stop message names a slash-command skill -->
   Set `G0_SURFACE` and `inputs.surface` to `claude`.
<!-- /host -->
<!-- host:codex: Codex's G0 stop message names a dollar-sign skill -->
   Set `G0_SURFACE` and `inputs.surface` to `codex`.
<!-- /host -->
   Read each unchanged probe report from `data.result.stdout_json`, its exit
   code from `data.result.exit_code`, and its error from `data.result.stderr`.
   Consume `data.quality_gate` only at Step 0.11, after the earlier setup work.
   Record `on_feature_branch`, `PROJECT_COMMANDS` (including the
   quality-gate slots and their `gates` metadata, per
   `references/prerequisites.md` Step 0.11, and the missing-tool default: the
   recorded install hint, then `skip (spec)`),
   `PRESET_CONVENTIONS`, and MCP availability into the workflow file. Pass
   `WORKFLOW_ROOT`, `PROJECT_COMMANDS`, and `PRESET_CONVENTIONS` to every
   subagent prompt. If any check fails, report the error message from the
   script's JSON output and route the failure to its owner for repair: the
   orchestrator repairs a fixable environment check, and the implement-executor
   repairs a failing project check. Run the repair loop within its allowance,
   then defer per the Failure Escalation Protocol.
4. **Constitution validation** — for each principle in
   `.specify/memory/constitution.md`, verify it against the codebase by
   reading (the project baseline belongs to implement entry, step 6e). Update the workflow's
   Prerequisites table. On a failing quality-gate slot, route the failing gate to the implement-executor,
   which repairs it; run the repair loop within its allowance, then defer per the Failure Escalation Protocol
   with `stop_reason:all_tiers_failed` only when repair fails.
<!-- host:claude: Claude discovers project agents under .claude/agents and CLAUDE.md -->
5. **Implementation agent detection** — Glob `.claude/agents/*.md`,
   match descriptions against implementation keywords; set
   `PROJECT_IMPLEMENTATION_AGENT` (fallback: `speckit-pro:phase-executor`). Also
   check CLAUDE.md for an explicit agent reference.
6. **Load settings + Claude subagent runtime record** — read
   `.claude/speckit-pro.local.md` (`gate-failure`, `auto-commit`), observe the bounded Claude CLI/runtime
   inputs, and call runner helper `resolve-claude-subagent-runtime`. Persist its
   record and take `AGENT_TEAMS_AVAILABLE`, `SUBAGENT_WAVE_SIZE`, and resume
   behavior from it (see prerequisites.md §Step 0.6).
<!-- /host -->
<!-- host:codex: Codex discovers installed agents under .codex/agents and reads Codex settings -->
5. **Codex agent availability and implementation agent detection** — run the
   promoted `install-codex-agents` helper in `dry_run` mode against the selected
   project or user destination and its installed model and Luna fallback
   choice. This check runs at setup or run start, before any phase work. If any
   required file is missing or stale, STOP and instruct the user to run
   `$speckit-pro:install`, approve the expected local write, and restart Codex. Do not apply
   the repair inside autopilot: Codex fixes its list of custom agents when the
   session starts. Once phase work has begun, a stale or refreshed agent file is
   recorded, never a stop: see §Plugin Update Mid-Run: Record, Re-resolve,
   Continue. Then discover `PROJECT_IMPLEMENTATION_AGENT` from `.codex/agents/`.
6. **Load settings** — read `gate-failure` and `auto-commit` from
   `.claude/speckit-pro.local.md` or
   `.codex/speckit-pro.local.md` (see prerequisites.md §Step 0.6).
<!-- /host -->
6b. **Resolve pre-Implement confidence gate mode** — run runner helper
   `resolve-confidence-mode` with the invocation argv to resolve
   the mode for G6.5 (precedence: `--strict` / `--advisory` flag
   in argv > `confidence_gate_mode` in `.claude/speckit-pro.local.md`
   or `.codex/speckit-pro.local.md` (the helper checks both default
   paths, and `.claude/` wins when both exist) > default
   `advisory`). If the script exits 2 (both flags passed), STOP
   the autopilot before Phase 0 with the conflict message — fail
   fast on usage errors. Record the resolved value as
   `CONFIDENCE_GATE_MODE` for use at G6.5. **Do not re-run the
   resolver at G6.5; G6.5 reads `CONFIDENCE_GATE_MODE` directly.**
   See [Gate Validation §G6.5](./references/gate-validation.md#g65--pre-implement-confidence-gate-between-analyze-and-implement).
6c. **Resolve the stage** — run runner helper `resolve-autopilot-stage`
   with the invocation argv and the workflow file path. It returns one
   JSON envelope; record `stage` as `AUTOPILOT_STAGE` and keep `source`,
   `basis`, `recorded_stage`, `planning_complete`, and
   `confidence_gate_status` for the phase loop. The committed
   `autopilot-state.json` stores only those decision fields: never the raw
   envelope, its `argv`, an absolute path, or an external task or session id,
   such as a delegation `task_id` (a digest or short redacted reference is fine). The Step 1.1 guard fails on
   them as `state_privacy_errors`. Store a native or operator event id, such as
   an approval event id, as `sha256:<digest>`: the hex SHA-256 of the raw value.
   The same rule covers every external task, session, thread, or event id cited in a committed record
   (marker checkpoints, verification reports, the workflow file, implementation notes, and PR bodies):
   write it as `sha256:<digest>` or omit it. The guard fails on a raw id in marker checkpoint or
   verification evidence as `marker_evidence_privacy_errors`, naming the file and field; those records
   are bound by their checkpoint digests, so write the digest before the checkpoint is recorded. Keep optional `artifact_review` for
   terminal-step routing and print every unverified preview disposition, including
   terminal `unavailable` pages, with its blocker and manual-review link. Follow
   the runner's `resume_action`; `none` completes preview work without asserting
   verified delivery. A pending
   handoff can auto-resolve `plan` even when `planning_complete` is true; explicit
   stages still win and started implementation is never routed backward. An explicit `--stage`
   always wins; with none given the stage is resolved from the workflow
   file's `## Workflow Overview` table. If the operation exits 2
   (unrecognised stage, `--stage` repeated with different values,
   `--from-phase` outside an explicitly named stage's range, `--stage`
   with no value, or an unreadable/unparseable workflow file), STOP the
   autopilot before Phase 0 with that one-line message — the same
   fail-fast shape 0.6b uses. **Print the resolved stage and its basis
   before any phase work begins** — before Phase 0, before the Step 1
   coverage guard, and before the first subagent dispatch. Emit one line,
   `Stage: <stage> (<source>) — <basis>`, using the envelope's `basis`
   verbatim. For an auto-detected stage that basis names the first
   non-terminal planning phase and its status, which is the row the operator
   has to act on; `plan` after a strict-mode gate stop reads
   `the first non-terminal planning phase is Confidence Gate, which is
   ⚠️ Blocked` rather than an unexplained stage token.
   Open CRITICAL/HIGH rows in the workflow's Analysis Results table also keep
   planning incomplete, even when every row reads Complete; the basis then names
   the open-finding count.
   If Step 0.6d reclaimed the slot, append
   `reclaimed the state slot from <prior workflow file> (prior status:
   <prior_run_note>)` to the same report. A `prior_run_note` of
   `in_progress` is the only available signal that a second run may still be
   live — the state file records no pid, heartbeat, or lease — so it is
   **reported, never blocking**. The stage bounds which phases this
   run may start: see
   [Phase Execution §Stage-Bounded Phase Selection](./references/phase-execution.md#stage-bounded-phase-selection).
   - **Corroborate the recorded draft pull request — one read-only observation
     per run, taken only when the workflow file's `Draft PR` row is present.**
     Read the row first. When it is absent, take no observation at all and send
     no `pr_observation`. When it is present, take exactly one observation,
     scoped to the feature's head branch:

     ```text
     gh pr list --head <branch> --state all --json number,url,state,isDraft,headRefName
     ```

     `--state all` is load-bearing: returning pull requests in every state is
     what makes a closed one distinguishable from an absent one.
     That observation is Step 0.6c's own — one at this step per run, not a
     cap on every corroboration read a run may take. The create-or-refresh
     terminal step and the Phase 7 feedback sweep's description refresh each
     take their own later live read.
   - **The trigger is the row's presence, not the stage.** Any invocation
     carrying a `Draft PR` row takes this observation — including one whose
     stage came from an explicit `--stage` argument, and one that resolves a
     stage other than `plan`. A run with no emission terminal step still reports
     the status and still records a discrepancy durably.
   - **Pass the result to `resolve-autopilot-stage` as `inputs.pr_observation`,
     and let the helper classify it.** Set `ok` to the JSON literal `true` —
     never `1`, never `"true"` — only when the query exited zero *and* its output
     parsed, and carry the parsed array in `pull_requests`. Otherwise send
     `ok: false` with a short `reason`. **You take the observation; the helper
     never does.** It never runs the tool and never touches the network, which
     is what keeps classification deterministic and offline-testable. Anything
     short of `ok: true` with a parseable array yields `skipped`, because a tool
     that was absent, unauthenticated, rate-limited, or unparseable is not
     evidence that a recorded pull request is gone.
   - **Print one line beside the `Stage:` line this step already prints, on
     every run**, naming `corroboration.status` from the envelope. The object is
     always present, so all six statuses print — `match`, `no_record`,
     `skipped`, `pr_closed`, `pr_missing`, `identity_mismatch` — and a run that
     could not check stays distinguishable from one that checked and agreed:

     ```text
     Stage: plan (argv) — explicit --stage plan
     Draft PR: match — #438 recorded, #438 observed
     ```

     ```text
     Draft PR: skipped — gh not authenticated
     Draft PR: pr_closed — #438 recorded, closed (merged: false)
     ```
   - **Record that same line durably in this step's workflow-file record for the
     three discrepancy statuses only** — `pr_closed`, `pr_missing`, and
     `identity_mismatch`. Write it in the **same edit turn as the `Stage` row**
     so it lands in the same commit, the write cadence `Stage` already follows.
     `match`, `no_record`, and `skipped` write nothing durable, and the scaffold
     workflow template ships no placeholder line.
   - **Corroboration reports; it never decides.** It never changes the resolved
     stage, never blocks stage resolution, and never stops the run at this
     step. It is computed after the stage is decided and only ever appended to
     the envelope. Every consequence of a discrepancy belongs to the terminal
     step and the Phase 7 corroboration gate, in
     [Phase Execution](./references/phase-execution.md), and both read one
     policy. When exactly one open pull request answers for the branch, the
     envelope's `corroboration.repair` names it, and the `Draft PR` row is
     repaired instead of stopping. `pr_closed` stops with
     `stop_reason:reopen_closed_pr`, because reopening a closed pull request
     stays a human call. A `pr_missing`, or an `identity_mismatch` with no
     repair, stops with `stop_reason:ambiguous_pr_record`.
   - **Retry the observation before it counts as failed.** A rate limit, a
     timeout, or output that cannot be parsed retakes it with backoff (2, 8,
     and 30 seconds, four attempts), then `gh auth status` runs. Only an absent
     `gh` or failed authentication stops a run, with
     `stop_reason:tool_unavailable`. A rate limit or unparseable answer that
     outlasts the retries is sent as `ok: false` with that reason. It reads as
     `skipped` and does not stop the run.
6d. **Reclaim the state slot if it names another workflow** — `autopilot-state.json`
   holds exactly one run. When this invocation targets a workflow file the state
   file does not currently name, **re-initialise the slot from the target
   workflow file before continuing**: rewrite `workflow_file`, `spec_id`,
   `feature_dir`, `branch`, `status`, `stage`, and `plan`. Reclaiming is normal
   operation — one slot, many specs — and is **not** an error.
   - **This runs before the Step 1 coverage guard, not after.** The guard's
     workflow-identity check fails a run whose state names a different
     specification, so ordering re-initialisation after the guard would turn
     every legitimate reclaim into a guard halt — the run stops at Step 1.1
     before the slot is rewritten. Reclaiming first rewrites `workflow_file`
     from the target, and the guard then compares two references that agree.
   - The trigger is **unscoped by stage**. Any stage can be the one that finds a
     foreign slot, and the ordering holds for all of them.
   - Record the reclaimed run's `status` **verbatim** in `prior_run_note` before
     overwriting it, so `in_progress` stays distinguishable from `completed` or
     `completed_archived`. Surface it in the Step 0.6c report.
   - **It MUST NOT block.** The state file carries no liveness evidence — no pid,
     no heartbeat, no lease — so `in_progress` cannot distinguish a live run from
     one abandoned to a crash or a closed terminal. Blocking on it would strand
     every run that followed an interrupted one. Report it and proceed.
6e. **Defer the project baseline to implement entry, and record it once** — Phase 7 Setup
   (`references/phase-execution.md`, Project Baseline) runs typecheck, test,
   build, and lint through `g0-setup`'s `data.baseline.implement_entry`. On a red check, route each failing check to the
   implement-executor within the repair allowance. If the workflow file already
   records the test-count baseline, **keep it.** The
   count is a diagnostic, not a test-growth acceptance requirement (see
   [Gate Validation §G7](./references/gate-validation.md#g7--after-implement)).
   Recapturing it loses the original health evidence. Require
   meaningful behavioral coverage instead of adding tests to increase a count.
   - If a newly observed count differs from the recorded baseline, record it as a
     **non-blocking drift diagnostic** naming both numbers. Do **not** replace the
     baseline with it. Drift means the tree moved underneath the spec, which the
     operator should see; it is not grounds to stop.
   - **Resume protocol (both distributions).** A run that resumes in a fresh
     session, or in a different working copy, reconstructs its context from the
     **workflow file**, which is durable and survives archiving of `specs/<id>/`:
     the `## Workflow Overview` status table, the `Stage` row, the recorded
     `Confidence Gate` verdict, and the project baseline. `autopilot-state.json` is a
     mirror of the active run and may be absent, stale, or naming another spec —
     each is recoverable, and none is an error. A **missing** state file is
     rebuilt from the workflow file; a state file naming **another** workflow is
     reclaimed per Step 0.6d. The one carve-out is the pull-request marker plan,
     which keeps its own stricter stop-rather-than-infer rule and is **not**
     relaxed to satisfy this resume path.
7. **Capability enumeration, grounding & feed-down** — you are the only
   component that discovers openly. Before relying on any capability, enumerate
   what this session actually exposes:
<!-- host:claude: Claude surfaces deferred MCP tools with ToolSearch -->
   surface deferred MCP tools with `ToolSearch`, and treat the available-skills
   list as the installed-skill registry.
<!-- /host -->
<!-- host:codex: Codex lists its tools and installed skills directly -->
   the tools and installed skills this session exposes.
<!-- /host -->
   Select best-fit per
   [`references/capability-discovery.md`](./references/capability-discovery.md) —
   do not assume a fixed set; the user may have installed anything. Your phase
   and consensus subagents inherit the operator's full installed surface and
   follow the same directive — read-only roles select only read/research
   capabilities, and the roles that read untrusted input pin closed allowlists.
   The Step 0.8 capability coverage check is informational: agents have
   fallbacks. Still pass the
   discovered evidence and capability context a subagent needs directly in its
   prompt: shared context beats re-discovery. Ground your OWN output
   (gate decisions, consensus synthesis, generated PR bodies) per
   [`references/grounding.md`](./references/grounding.md): every external fact
   you assert must cite a real tool/skill/file result, and you abstain when
   nothing grounds it.
<!-- host:codex: only Codex records a Phase 6.5 autonomy boundary for its sandbox -->
8. **Resumed Autonomy Boundary Preflight** — when `plan.md` and
   `tasks.md` already exist and the resolved stage can enter Implement, validate
   the durable `autonomy_boundary` record (a public receipt of a private
   record kept outside the repository) before the first Phase 7 dispatch.
   Missing or stale evidence re-enters the full Phase 6.5 Autonomy Boundary
   Preflight. Exact explicit user authorization remains valid while its recorded
   action scope and execution boundary still match and no later instruction
   revokes or narrows it; an older run outcome alone grants nothing. When a
   persisted `autonomy_boundary` receipt exists, at any stage, probe it against
   the live boundary before the Step 1.1 coverage guard; a new thread's writable
   roots make it stale, so rerun the preflight up front, as
   [prerequisites.md](./references/prerequisites.md) describes. A
   covered inventory asks no question, including a planning-to-implementation
   stage change.
<!-- /host -->

<!-- host:claude: Claude plugin agents ignore these frontmatter keys -->
**Plugin agent caveat:** `permissionMode`, `hooks`, and `mcpServers`
frontmatter are silently ignored on plugin agents. Run the parent
session in `acceptEdits` or `bypassPermissions` for smooth execution.
See `references/plugin-limitations.md`.

<!-- /host -->
**Full per-step details, JSON schemas, capability fallback behavior, and
failure-escalation rules:** see [`references/prerequisites.md`](./references/prerequisites.md).

## Step 1: Parse Workflow State

Read the workflow file and apply
[`references/phase-execution.md`](./references/phase-execution.md)
§Stage-Bounded Phase Selection. Filter Workflow Overview rows to
`AUTOPILOT_STAGE`, start at the first non-terminal row (`Complete` and
`Skipped` variants are terminal), and accept `--from-phase` only within that
stage. If no candidate row remains, execute the stage's terminal instruction
and STOP; do not scan into a later stage. For `implement` and `full`, rebuild
and finish incomplete canonical Post work before reporting completion.

### 1.1 Create Progress Plan

After parsing the workflow state, create a **granular** progress plan.
Persist it in `<workflow directory>/autopilot-state.json` before Phase 1.
The initial plan must include every canonical phase family even when its
detailed items will be discovered later. For multi-prompt phases (Clarify,
Checklist), create one item per prompt/session when known; otherwise create the
phase discovery placeholder. **Every Clarify session, every Checklist domain,
and the Analyze phase MUST have a paired Consensus task** immediately
after. A zero-unresolved Clarify or Checklist task may be skipped; the Analyze
task still dispatches the synthesizer once for the final five-criterion
confidence block, including a clean pass with zero findings, so the block is
emitted and persisted exactly once for that Analyze pass. **Never omit
consensus items.**

<!-- host:claude: Claude shows 11 Post rows -->
The full **11-entry Post-Implementation task list** and the task
naming pattern live in
[`references/task-list-canonical.md`](./references/task-list-canonical.md).
<!-- /host -->
<!-- host:codex: Codex shows 13 Post rows, two of them supporting rows after UAT -->
**Item naming + combined post-impl list (13 mandatory rows including
`Post: Doctor Extension Check` ... `Post: Retrospective` as the FINAL
STEP) + reference `autopilot-state.json` schema:** see
[task-list-canonical.md](./references/task-list-canonical.md).
<!-- /host -->
Every entry there MUST appear in `autopilot-state.json` before
Phase 1 starts — when an extension is absent, the task still appears
marked `skipped: <ext-name> not installed`; never silently drop the item.

**Phase family coverage is mandatory.** Before any subagent is spawned, verify
that the plan includes at least one item whose name starts with each of these
exact prefixes: `Archive Sweep:`, `Phase 0:`, `Phase 1:`, `Phase 2:`,
`Phase 3:`, `Phase 4:`, `Phase 5:`, `Phase 6:`, `Phase 6.5:`, `Phase 7:`,
`Post:`. Count the prescribed entries (every Phase, every Consensus, every
`Post:`). If any is missing from `autopilot-state.json`,
repair the state file, print the corrected checklist summary, and repeat this
coverage audit before advancing. A complete workflow plan is required even
when `--from-phase` starts execution in the middle of the workflow.

**Then run the deterministic coverage guard and repair on a nonzero exit.**
Both hosts run the same guard, so both distributions share one enforcement
path instead of two prose descriptions of one:

<!-- host:claude: Claude records no Phase 6.5 autonomy boundary -->
```text
Command("<resolved_python> '<plugin-root>/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py' --workflow <workflow-file-path> --state <workflow-directory>/autopilot-state.json --rule status-evidence")
```
<!-- /host -->
<!-- host:codex: Codex requires its Phase 6.5 autonomy boundary against the live sandbox -->
```text
resolved_python "<plugin-root>/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py" --workflow "$WORKFLOW_FILE" --state "$WORKFLOW_DIR/autopilot-state.json" --require-autonomy-boundary --current-execution-environment "<live-execution-environment>" --current-sandbox-mode "<live-sandbox-mode>" --current-approval-reviewer "<live-approval-reviewer>" --current-writable-root "<live-writable-root>" --rule status-evidence
```
<!-- /host -->

`--rule status-evidence` gates the **exit code** on the nine workflow/state
status-evidence checks (`workflow_status_evidence_errors`,
`state_status_errors`, `autonomy_boundary_errors`, `stage_mirror_errors`,
`workflow_authority_errors`, `state_privacy_errors`,
`marker_evidence_privacy_errors`, `formal_checkpoint_errors`,
`artifact_review_errors`) and
the three current-run state-plan invariants (`in_progress_errors`,
`duplicate_state_steps`, `state_order_errors`). The full report is still
printed; structural coverage checks and every advisory key are visible but
never block. Drop `--rule` to gate on every check.

On a nonzero exit, route the report's `repair` record to the orchestrator: it
names the owner and the `failing_keys`, and the orchestrator owns both files.
Repair the workflow status table and the state file, then rerun the guard. For
`state_privacy_errors`, each error names the field and its remedy
(`sha256:<digest>` of the raw value, or removing a raw `argv`). For any other
failing gated key, correct the file the key names. Run the repair loop within its allowance, then defer per the Failure Escalation Protocol;
advance to Phase 1 only on exit 0.

`<resolved_python>` is the Python 3.11+ interpreter resolved by the
Installed Runtime Contract, not a hardcoded interpreter name; `<plugin-root>`
is the directory that owns `skills/speckit-autopilot/`. Exit 0 is required to
advance; exit 1 reports the failing checks as JSON on stdout; exit 2 is an
input error. The guard also fails when a Workflow Overview status row
contradicts a gate verdict recorded elsewhere in the same file, which is what
keeps the status table honest across compactions and manual phase runs.
<!-- host:codex: Codex supplies its live sandbox boundary and PR authority to the guard -->
Replace every `<live-...>` value from the current system/developer execution
context, never from the workflow, state, repository, or a prior run. Repeat
`--current-writable-root` once for each current writable root; the validator
sorts this live set before comparing it with the persisted boundary digest.

When `pr-marker-plan.v2` declares a changed-file manifest, append
`--expected-base-commit <live-baseRefOid> --expected-head-commit <live-headRefOid>`.
Fetch both OIDs from live PR metadata immediately before every validation;
never source either authority from the workflow, state, or manifest itself.
Missing, stale, or mismatched external PR authority is blocking.
<!-- /host -->

### 1.2 Validate Plan State Before Phase 1

Before Phase 1 starts, validate all of the following or repair it through the owning agent:

- `autopilot-state.json` exists and its plan matches the workflow-derived ordered step list
- Exactly one plan item is `in_progress`
- Every canonical phase family prefix from Phase 0 through Phase 7 plus
  Phase 6.5 and Post appears in `autopilot-state.json`, with the Archive Sweep item recorded before Phase 0
- `validate-autopilot-phase-coverage.py` exits 0 for the workflow/state pair
- Every Clarify session, Checklist domain, and Analyze phase has its
  mandatory Consensus item
- The checklist summary was printed so progress is visible to the user

## Step 2: Main Execution Loop

For each planning phase, request
`helper_id=phase-brief operation=phase-brief mode=read_only` with inputs
`phase` (Specify, Clarify, Plan, Checklist, Tasks or Analyze),
`workflow_file=WORKFLOW_FILE` and `feature_dir=<feature-dir>`.
Use the successful response's data as `brief`: dispatch `brief.agent`,
read the exact workflow prompt(s) under `brief.inputs.prompt_section`, and
prefix each with `brief.inputs.instruction`. Pass `brief.inputs` and
`brief.readable_files` in the executor prompt, alongside the per-dispatch
context lines: `Workflow root:`, the Specify branch prefix when
`ON_FEATURE_BRANCH` is true, and the corrective reservation. Insert each
entry of `brief.slices` verbatim, in order, after those lines under a
`Reference slices:` line. Clarify, Checklist and Analyze executors take their
discovery, grounding and routing rules from the slices, so the prompt carries
no `Protocol:` or `Reference dir:` line for them.
Run `validate-gate` with `brief.gate` afterward; the brief is not gate evidence.
Clarify still runs only when G1 found `[NEEDS CLARIFICATION]` markers.
Use the brief for phase dispatch facts instead of re-reading `phase-execution.md`
for each planning phase. Keep the existing remediation and bookkeeping steps.
Implement retains its existing agent, inputs and gate; it never requests a
planning brief. A failed helper request goes through runner error recovery,
not a guessed dispatch or stop decision.

### Phase brief contract

The successful response data has `schema_version: phase-brief/v1` and these
stable fields, shared by both hosts:

| Field | Meaning |
| --- | --- |
| `phase` | Requested title-case planning phase |
| `agent` | Host-neutral installed executor role |
| `inputs` | `workflow_file`, `feature_dir`, `instruction`, `skill` (the loaded command's skill name; null for Clarify), and `prompt_section` (including its session/domain prompts) |
| `readable_files` | The paths the phase may read when present, including extension configuration; relative to the bound workflow root unless absolute; trailing slash includes directory contents |
| `gate` | Gate id for the parent's `validate-gate` request |
| `slices` | Ordered, structurally validated reference sections copied verbatim for the dispatch prompt; empty for Specify, Plan and Tasks |
| `waves` | Empty list, reserved for dispatch waves (#1183) |
| `model` | `claude` and `codex` entries, each with `model` and `effort`, for this dispatch. Claude Code passes `model` per call and keeps effort in the agent file; Codex passes both per spawn |
| `hooks` | Empty list, reserved for optional hooks (#1188) |

Loaded commands still read their own instructions, templates and scripts.
The phase-brief helper validates each sliced reference before dispatch: use
ATX headings and `***` separators in those references. Comment blocks and
fenced code retain their original text in a slice.
Empty reserved fields add no behavior; existing hook handling and sequential
session/domain dispatch remain. Runner stop policy remains authoritative.

For each pending phase, spawn a subagent, collect the result, validate
the gate, advance. Every step is a tool call.

```text
PHASES = [specify, clarify, plan, checklist, tasks, analyze, implement]

for phase in PHASES starting from first_pending:
    0. Re-run the Step 1.1 coverage guard against the workflow file and
       autopilot-state.json. Exit 0 is required; on nonzero, repair the plan
       and the workflow status table, then repeat before executing this phase.
    1. autopilot-state.json: phase item → in_progress
<!-- host:claude: Claude dispatches with Agent -->
    2. Run before_<phase> hooks from .specify/extensions.yml
    3. For each workflow prompt in this phase:
         Planning:
         Agent(subagent_type: "speckit-pro:" + brief.agent, model: brief.model.claude.model,
               run_in_background: false, prompt: <brief.inputs.instruction + workflow prompt + brief context + brief.slices>)
         Implement: use the implementation executor and task-specific TDD prompt.
<!-- /host -->
<!-- host:codex: Codex dispatches with spawn_agent -->
    2. Run before_<phase> hooks from .specify/extensions.yml
    3. For each workflow prompt in this phase:
         Planning:
         spawn_agent(agent_type=brief.agent, model=brief.model.codex.model,
                     reasoning_effort=brief.model.codex.effort, fork_turns="none",
                     message=<"$" + brief.inputs.skill (omitted when null) + newline +
                              brief.inputs.instruction + workflow prompt + brief context + brief.slices>) then wait_agent
         Implement: use the implementation executor and task-specific TDD prompt.
<!-- /host -->
    4. Run consensus (Clarify/Checklist/Analyze only) — see Rule 6
    5. Run after_<phase> hooks
    6. Validate the gate (G1-G7): run runner helper
       `helper_id=validate-gate operation=validate-gate mode=read_only`
       with `gate=brief.gate` for planning (`G7` for Implement), `feature_dir=<feature-dir>`, and
       `workflow_file=<workflow-file>`, then branch on the JSON `pass` field
       On FAIL: reserve a corrective cycle through execution-control;
       honor its shared family/spec budget and checkpoint disposition
    7. Update workflow file; auto-commit if configured
         phases 1-6: git add specs/ <workflow-file-path> <workflow-dir>/autopilot-state.json && git commit
         phase 7:    git add -A && git commit
    7b. After Plan (G3 pass, plan.md exists), run the plan-phase
        reviewability budget with runner helper `estimate-reviewable-loc`,
        guarded against errexit. Branch on JSON `status`
        (pass / over_budget / not_estimated) or the exit code.
        ADVISORY — never blocks, prompts mid-autonomous-run, or
        crashes the run.
    8. After Tasks (G5 pass), apply the tasks-phase reviewability
       boundary. Runner helper `reviewability-gate` supports setup mode
       only on the installed runner — tasks mode is deferred, so do not
       invoke it as an active helper. Record the deferred-mode
       diagnostics (helper ID, requested mode, deferral reason) in the
       workflow file, then continue on the fallback evidence chain: the
       setup-mode gate result recorded at scaffold, the plan-phase
       `estimate-reviewable-loc` verdict from step 7b, and any
       ratified split decision (autopilot or operator) in the workflow file.
       When the per-PR path budget forces a split of the approved PR
       order, run runner helper `ratify-pr-split` before asking anyone
       and record its `data.record` (see Budget-driven split
       ratification in `references/phase-execution.md`).
       In that committed evidence, `pass`, `warn`, honored exception,
       and valid current size-only `block` are marker-planning inputs.
       A valid current size-only block continues into marker planning
       and marker emission; it is not a manual re-slicing stop.
       Preserve correctness stops for malformed/stale marker state,
       failed verification, invalid packet, unsafe output, unusable
       gate evidence, invalid JSON, missing status/mode, stale
       fingerprints, and non-size safety findings.
    8c. After Tasks (G5 pass), run runner helper `atomicity-route`
        with both `inputs.feature_dir` and the actual bound
        `inputs.workflow_file` (the complete request is in
        `references/phase-execution.md`)
        and record the emitted JSON decision into the workflow
        file's "## Atomicity Route" section. READ-ONLY + ADVISORY —
        the script writes nothing and never blocks; the SKILL is
        what records it.
        The workflow path excludes that exact workflow file and its
        sibling `autopilot-state.json` from change classification.
        For an existing generated workflow with the old positional
        instruction, replace only that instruction; preserve phase
        status and operator-authored content.
        The Phase 7 placeholder is invalid after G5. Parse `tasks.md` and
        replace that placeholder in `autopilot-state.json` with concrete
        task-group items and task IDs;
        Analyze and Implement remain blocked until the state file is repaired.
    8d. After recording the atomicity route, run the layer planner only
        when route is exactly `split-PR`, and always before Analyze or
        Implement can continue:
        - non-split routes: record `layer_plan.status=skipped` in
          `autopilot-state.json` and the workflow "## Layer Plan" section,
          then continue with route context.
        - split route: run helper operation `plan-layers-feature-dir` for
          `<feature-dir>` and capture stdout, stderr, and exit code.
        - exit 0: parse stdout as the full versioned layer-plan envelope,
          persist it under `layer_plan` in `autopilot-state.json`, write a
          concise workflow "## Layer Plan" summary, carry warnings into the
          implementation context, then continue.
        - exit 1 (`invalid_plan`): hold implementation and route the planner's `repair` record to the phase-executor, which fixes
          `tasks.md` from the planner diagnostics in stdout/stderr. Then rerun `plan-layers-feature-dir`;
          run the repair loop within its allowance, then defer per the Failure Escalation Protocol.
        - exit 2 (`input_error`): hold implementation and route by `repair.owner`. A missing `tasks.md`
          (`tasks_file_missing`) reruns the Tasks phase through the phase-executor; a bad feature
          directory or permission is corrected by the orchestrator. Rerun the planner, and defer the
          same way when repair fails. Analyze and Implement do not begin before the planner exits 0.
        This wires NO PR emission or branch creation; the multi-PR emission
        phase owns those effects.
    8e. Persist marker planning state when reviewability evidence requires it:
        top-level `pr_marker_plan` in `autopilot-state.json`, mirrored
        workflow evidence, and repo-relative evidence paths. Do not treat
        `tasks.md` as authoritative marker state.
    9. Advance
```

Planning dispatch facts come from the phase brief above. Consult
[`references/phase-execution.md`](./references/phase-execution.md) for
remediation, formal checkpoints, hook events and implementation dispatch.
Before performing the post-G5 steps (8 through 8e), read
[`references/phase-execution.md`](./references/phase-execution.md)
§Phase 5: Tasks for the authoritative placeholder, reviewability, marker
state, and no-side-effect boundaries.

**Plan-phase reviewability budget (advisory):** After the Plan phase
(G3 pass, `plan.md` exists), the parent runs
runner helper `estimate-reviewable-loc`, capturing
the exit code so a non-zero exit can never abort the run. Branch on the
JSON `status` (`pass` / `over_budget` / `not_estimated`) or the exit
code, recording the outcome to the workflow file and
`autopilot-state.json`. This is preventive sizing and **advisory only**
— no outcome blocks, prompts mid-autonomous-run, or crashes the run
(hard blocking and re-slicing are a separate step). Full status branch in
[`references/phase-execution.md`](./references/phase-execution.md).

<!-- host:codex: only Codex records a Phase 6.5 autonomy boundary for its sandbox -->
Before the confidence gate, stage-boundary commit, or first Phase 7 dispatch,
run the phase reference's **Autonomy Boundary Preflight**. It inventories
predictable writes beyond current writable roots, privileged commands,
interactive authentication, externally visible side effects, and data egress
to a model service or other third party (including live model evaluations);
proves each
is runnable or already authorized; and records the result durably. The
operator's invocation and the ratified plan authorize the ordinary actions in
the repository's standing policy, which the operator installs once at setup
(runner helper `render-egress-authorization` with `scope=standing`). Before
Phase 1, the Step -2 run-start authorization derives the policy classes from
`check-gate-preflight-coverage`, probes each egress class, an external workflow
root, and the private autonomy-record write, and makes a missing standing
policy the one up-front ask. When every action is covered, the preflight asks
no question. An uncovered action the ratified plan newly names, including a
boundary-file edit, is deferred to the one end-of-run request, never an
up-front question that stops the run. For uncovered plan-derived data egress,
the preflight shows a paste-ready authorization message and asks the operator
to send it as a normal chat message, never as a goal edit, without waiting for
it; the end-of-run request repeats it with a proposed `auto_review.extra_policy`
fragment, both rendered by the same helper. The plugin never writes either one.
Bypassing a reviewer veto stays human authority (`stop_reason:veto_bypass`).

<!-- /host -->
Once autopilot is running, human input is for exceptional cases only. Once Phase 7 runs, one
blocked action never stops the run: take the task's own fallback, or defer that
task and keep executing independent work, then ask once at the end. Follow
§Blocked Actions Mid-Run: Fall Back or Defer, Never Stop in
[`references/phase-execution.md`](./references/phase-execution.md#blocked-actions-mid-run-fall-back-or-defer-never-stop).

After all 7 phases pass G7, execute the post-implementation task list.
The Post tasks, detailed prompts, and extension routing live in
[`references/post-implementation.md`](./references/post-implementation.md);
the canonical name list is in
[`references/task-list-canonical.md`](./references/task-list-canonical.md).

<!-- host:claude: Claude's Skill tool loads a command into the orchestrator's own context -->
**⚠️ Use `Agent()` subagents for ALL post-implementation tasks — NEVER
`Skill()` directly.** Rule 1 applies: a `Skill()` call loads the
command into YOUR context and the command's completion text can kill
the agent loop, preventing subsequent tasks from running.
<!-- /host -->
<!-- host:codex: Codex dispatches Post work with spawn_agent -->
**Use `spawn_agent` subagents for ALL post-implementation tasks — never invoke
the skill directly in the parent.** Rule 1 applies: a direct skill call runs
the command in YOUR context, and its completion text can end the loop before
later tasks run.
<!-- /host -->

**Extension availability**: Step 0.12 records which extensions are
installed in `.registry`. If an extension is missing, log a warning
and mark its task `skipped: <ext> not installed` — do NOT fail the
autopilot. Recommend `specify extension add <name>` in the warning.

**Dynamic task updates:** If consensus reveals new questions or
remediation adds loops, add the items to `autopilot-state.json`.

### Phase Dispatch

Before each corresponding dispatch, read the mandatory
[`references/phase-execution.md`](./references/phase-execution.md) sections
<!-- host:claude: the Claude phase reference names its dispatch sections this way -->
§Subagent Delegation, §Phase-by-Phase Execution, and §Phase 7 Step 3. They own
<!-- /host -->
<!-- host:codex: the Codex phase reference names its dispatch sections this way -->
§Agent Mapping, §Main Execution Loop, §Phase 5: Tasks, and §Phase 7: Implement. They own
<!-- /host -->
the exact workflow-prompt envelope, preset/project-command feed-down,
branch-aware prefixes, Clarify and Checklist sequencing, namespaced agent
routing, validated capability batches, TDD injection, and localized repair. Pass
the exact workflow prompt plus `WORKFLOW_ROOT`, `PRESET_CONVENTIONS`, and
`PROJECT_COMMANDS` already resolved above. When already on the feature branch,
tell Specify to use that branch and existing spec directory rather than create
another. Rule 6 and the consensus reference own resolution between prompts. Do
not reconstruct those contracts from this entrypoint.

## Step 3: Post-Implementation

After Phase 7 passes G7, read and execute
[`references/post-implementation.md`](./references/post-implementation.md)
in canonical order. It owns the parallel group, full integration suite,
mandatory UAT runbook, current reviewability evidence and continuation,
packet dry-run/apply and current read-only/persisted validation,
packet-owned base/head/title/body, single- versus split-PR emission, review
remediation, retrospective, and final summary. Do not start PR side effects
without the reference's current evidence and packet contracts, and never report
completion while its continuation or canonical Post work remains incomplete.

The first Post action is to resolve the host-native subagent launcher and
dispatch exactly three workers for the Doctor, Code Review, and Verify tracks.
The parent MUST NOT perform any track-owned Task 10-14 action itself. It may
continue only after it has consumed all three terminal worker reports.

### 3.4 Pre-final completion audit

Before sending any final user-facing response, re-read
`autopilot-state.json` and the workflow file, reconcile them,
and audit the canonical Post list. A completion response is
forbidden if any `Post:` item is `pending`, `in_progress`, or missing.
For the first Post
parallel group, mark Doctor, Code Review, Verify Implementation, Verify Tasks
Phantom Check, and Integration Suite in progress before dispatching the three
workers. Later serial items advance one at a time.
Exception: `execution_control.disposition=checkpoint_required` permits an
honest checkpoint response stating the run is **not complete**, remaining Post
work, consumed budget, unknown effects, and the operator decision required.
An unknown dispatch outcome alone is not that decision: settle it with
`execution-control action=reconcile-unit` (a read-only reconciler over the
unit's owned paths, runner-classified from git state) and keep dispatching
independent units; pass `tdd_units` on each implementation reserve.
A `checkpoint_required` whose `reasons` is only `unknown_dispatch_blocks_unit`
is not a stop: run `reconcile-unit` for each id in `blocked_by`. On
`unit_classification_mismatch`, re-inspect the owned paths and call once more
with the class the paths show; never cycle the three values. Read
`unknown_dispatch_ids` from `status` before each wave so a blocked unit is
seldom reserved.

Issue capped approvals yourself when the runner proves them, instead of asking
the operator. Pass `agent_authorized: true` and no `native_observation` to
`authorize-corrective-retry` (a lost worker's failed corrective dispatch with
a recorded native failure event; one per run), to `begin-replan-epoch` (a
deferral is open, the spec is unchanged, the Tasks rerun changed the plan or
task fingerprints the stage epoch recorded, and every dispatch is settled; two
per run), or to `authorize-corrective-continuation` with `spec_file` (the
metadata-only proof holds). A refusal means the proof does not hold or the cap
is spent; only then does the request go to the operator. Scope changes and
forged events stay operator-only.
Keep pending rows and current status; never mark them completed to stop.
A failing gate or test is remediated, not deferred: keep remediating while
each round converges, dispatching each diagnosed fix through the executor and
rerunning verification. The ledger admits every correction whose predecessor
shrank the runner-recorded failing set, or moved it with every earlier failure
passing, with no operator event. `execution_control.disposition=defer`
(`disposition=defer` in the ledger response) is the non-convergence fallback
and not a stop: it defers one blocked unit whose
correction made no measurable progress and whose allowance is spent, and the
run keeps executing independent work.
When every runnable item has finished, whether or not deferred items remain, the
read-only `finalize-run` runner helper decides the end under §Blocked Actions
Mid-Run: Fall Back or Defer, Never Stop in
[`phase-execution.md`](./references/phase-execution.md#blocked-actions-mid-run-fall-back-or-defer-never-stop).
Human UAT is the
only gate a run may defer, and every required gate must be green at every PR
head as the runner's own verification record shows it. With every required gate
green, the run finalizes: mark the stack ready for review (never merge) and open
the top PR body with its `Deferred / not verified` section.
<!-- host:codex: a Codex thread carries a goal the run marks complete -->
Mark the thread goal complete.
<!-- /host -->
Human UAT, a ledger
`deferred` unit that failed every escalation tier, and an unresolved task never
keep the stack in draft: they reach the owner as items in the end-of-run
request, the units and tasks under "Decisions for you". A failed unit climbs two
escalation tiers first (a fresh agent guided by a consensus diagnosis, then the
strongest model at max effort), and only a required gate still red, missing, or
blocked by a harness error after that is one human stop, and the stack stays in draft. The run never pauses to ask.
Print the final report as plain text on `outcome=complete` with nothing deferred, and ask no question.
Otherwise print `end_of_run_request` as plain text in the final message. It is the handoff, listing every fallback taken and every
deferred item, including each entry of the ledger's `deferred` list.
If the audit finds incomplete Post work, set the first
incomplete item to `in_progress` in `autopilot-state.json` and continue the
autopilot loop instead of summarizing. `Post: Retrospective` is the final
Post item; it must be completed or explicitly skipped before the
autopilot can report completion.

The same audit must reconcile every started native command, tool, and agent
with its terminal result. Give each final local gate one owner, run each gate
once as a separately attributable foreground command, and wait on that exact
native handle before starting the next gate. Never launch an overlapping copy
of pending work. If time or budget prevents terminal reconciliation, preserve
the unresolved identities and report an incomplete checkpoint instead of a
completion response.

Only after every Post item is completed or explicitly skipped, and the
PR URL is known, the autopilot is DONE. Report the final summary with
PR URL.

## Workflow File Update Protocol

After every phase, apply
[`references/workflow-file-protocol.md`](./references/workflow-file-protocol.md)
to update the durable workflow status/results, constitution evidence, and any
Consensus Resolution Log rows. Workflow Overview and `Stage` are
workflow-file-wins and repair their one-run state mirrors. Only active
`workflow_file` and `pr_marker_plan.status` are state-authoritative and repair
the workflow in the opposite direction. The coverage guard enforces these
directions; do not infer a broader precedence rule.

## Error Recovery

<!-- host:claude: Claude names skills with a slash -->
- **Resume:** `/speckit-pro:speckit-autopilot workflow.md --from-phase
  <next-pending-phase>` — the workflow file persists all state.
<!-- /host -->
<!-- host:codex: Codex names skills with a dollar sign -->
- **Resume:** `$speckit-pro:speckit-autopilot workflow.md --from-phase
  <next-pending-phase>` — the workflow file persists all state.
<!-- /host -->
- **A gate or test fails: keep remediating while each round converges.**
  Diagnose the failure with the consensus agents, dispatch the fix through the
  executor, and rerun verification. While each correction shrinks the
  runner-recorded failing set, or moves it with every earlier failure passing,
  the ledger admits the next correction in that family with no operator event
  and no count limit (see
  [`execution-efficiency.md`](./references/execution-efficiency.md)).
- **Non-convergence: defer and continue.** When a correction makes no
  measurable progress (the same, a larger, an earlier, or an unparsed failing
  set) or a spec change breaks the chain, the fixed allowances apply, and an
  exhausted one returns `disposition=defer`: the ledger refuses that dispatch
  and records the blocked unit in its `deferred` list. Record the deferred item with the
  exact gate output, keep executing every independent task, increment, and
  gate, and list it in the one end-of-run consolidated request. It is never a
  mid-run question and never a stop; no phase or nested worker has an
  independent retry budget. `authorize-corrective-exception` (one
  operator-approved application correction; a class-scoped exception covers
  later same-class fixes through `reserve-class-correction`) and
  `begin-replan-epoch` are end-of-run tools that act on the operator's answer
  to that request. An explicit `--stage implement` opens the implement stage's
  own allowance through `begin-stage-epoch`. A task-verb fix that only
  reroutes a task to verification reserves with `metadata_only: true`; the
  runner proves it against the committed baseline and spends no cycle. Never
  reset or bypass the ledger otherwise; `checkpoint_required` and ledger integrity errors still stop.
- **Consensus cannot agree** (Round 2 all-disagree, a security item without
  3/3, or an analyst that fails its retry): run the Round 3
  agent tiebreak, a fresh analyst plus a max-effort `consensus-tiebreaker`,
  record the most conservative option that satisfies the spec as an assumption
  with the dissent logged, and continue. Only a choice that changes product
  scope the spec and roadmap do not settle is deferred to the one end-of-run
  request; nothing stops the run and nothing asks mid-run. See
  [consensus-protocol.md §Round 3 Tiebreak](./references/consensus-protocol.md#round-3-tiebreak).
- **Research/context capability unavailable:** use the next acceptable
  evidence path, record any confidence impact, and escalate only when no
  acceptable evidence path remains or a true gate fails.
- **Context window pressure:** keep subagent summaries concise; the
  workflow file is the durable record (re-read after compaction).

Full details, additional failure modes, and recovery playbooks live
in [`references/error-recovery.md`](./references/error-recovery.md).

## References

- [Stop Policy](./references/stop-policy.md) — The one contract for when a run may involve a human; stop reasons and their classes
- [Prerequisites](./references/prerequisites.md) — Archive Sweep + Step 0.x environment, settings, constitution, agent detection, command/preset discovery
- [Phase Execution](./references/phase-execution.md) — Per-phase prompt construction, dispatch templates, branch-aware/Clarify/Multi-prompt prefixes
- [Consensus Protocol](./references/consensus-protocol.md) — Category-routed dispatch, Round 1/2/3, per-phase flows, Logging schema
- [Gate Validation](./references/gate-validation.md) — Programmatic gate checks (G0–G7), auto-fix loops, escalation
<!-- host:claude: Claude shows 11 Post rows -->
- [Post-Implementation](./references/post-implementation.md) — 11-task post-impl sequence (incl. UAT runbook), integration suite, PR creation, review loop
- [Task List Canonical](./references/task-list-canonical.md) — Task naming pattern + canonical post-implementation entries
<!-- /host -->
<!-- host:codex: Codex shows 13 Post rows -->
- [Post-Implementation](./references/post-implementation.md) — Post items plus supporting-row mapping, parallel group dispatch (Doctor/Code Review/Verify-chain), extension availability rules
- [Task List Canonical](./references/task-list-canonical.md) — checklist naming pattern, 13 mandatory Post rows, item-naming rules, reference `autopilot-state.json` schema
<!-- /host -->
<!-- host:claude: Claude runs the hardener in Phase 7 Final Verification -->
- [Hardener Delegation](./references/hardener-delegation.md) — Once-per-spec tests-only mutation hardening loop: gateway delegation with candidate inspection, primary-model fallback, stop rule, record
<!-- /host -->
<!-- host:codex: Codex runs the hardener inside Post item 14 -->
- [Hardener Delegation](./references/hardener-delegation.md) — Once-per-spec tests-only mutation hardening loop with gateway delegation, candidate inspection, primary-model fallback, stop rule, and record. Codex runs it inside Post item 14 (Integration Suite), between the MUTATION run and its block decision, not in a Phase 7 Final Verification step
<!-- /host -->
- [Workflow File Protocol](./references/workflow-file-protocol.md) — Per-phase update table + `workflow_file` state authority (branch order, verdicts) + Consensus Resolution Log column schema
- [Error Recovery](./references/error-recovery.md) — Resume, common issues, context-window management
- [TDD Protocol](./references/tdd-protocol.md) — Red-green-refactor rules injected into implementation agent prompts
- [Plugin Limitations](./references/plugin-limitations.md) — permissionMode/hooks/mcpServers caveats and capability fallback behavior
<!-- host:claude: Agent Teams exist only on Claude Code -->
- [Agent Teams Integration](./references/agent-teams-integration.md) — Use-site map of current sites, capability detection, lifecycle policy
<!-- /host -->
- [Token Discipline](./references/token-discipline.md) — Opt-in compressed vocabulary for inter-agent transcripts (off by default; never applied to PR bodies, logs, or artifacts)

Active runner operations are named at their use sites and in the targeted
references above; the runner registry is their deterministic authority.
Registry-deferred or out-of-scope operations are unavailable and MUST NOT be
invoked, promoted, or inferred from use-site prose.
