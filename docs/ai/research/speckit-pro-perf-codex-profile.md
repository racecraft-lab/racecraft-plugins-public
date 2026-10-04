# speckit-pro on Codex: what the canary transcripts show about plan-stage cost

> Status: research complete for ticket #1149, part of map #1144. Dated
> record: it describes plugin 2.39.2 and 2.40.0 on Codex CLI 0.160.0 as of
> 2026-10-04. Source files are local canary run folders that are not
> published. This note carries numbers only, no fixture content.

## Short answer

The Codex baseline transcript has no plan stage. It is an 88.5 s scaffold run
that stopped at a prerequisite check, with 8 tool calls and 397K tokens. The
plan stage never started. The 2.40.0 Codex smoke is the only run that touched
the plan stage, and it stopped after 30.6 s and 117,849 tokens. Its first
action was an `update_plan` call that the session could not run (issue #1079).

So there is no Codex plan-stage profile. What the two runs do give:

- A measured Codex scaffold: 450.7 s and 2.06M tokens for the orchestrator,
  plus one sub-agent that the receipt does not count (171K tokens).
- The first look at `spawn_agent` and `wait_agent` in practice: one agent, five
  polls of 10 s each, four of them timed out, and the parent worked in
  parallel with the child.
- A token accounting gap: the canary receipt counts only the root thread.
  Child agent tokens are missing, which matters for the 15M-token target.
- A reliable view of the shipped Codex model and effort per agent.

## Sources and method

| Source | What it is |
| --- | --- |
| Baseline Codex run, plugin 2.39.2 | `receipt.json`, one `codex exec --json` event stream, one rollout file (scaffold only) |
| 2.40.0 Codex smoke, missing-guard variant | `receipt.json`, event streams for scaffold and plan, four rollout files (root scaffold, one child agent, root plan) |
| Smoke log | Validator output for the 2.40.0 smoke |
| Plugin source on main at f7c97c1af | `speckit-pro/skills/speckit-autopilot/SKILL.md`, `speckit-pro/skills/speckit-scaffold-spec/SKILL.md`, `speckit-pro/codex-agents/*.toml`, `speckit-pro/codex-hooks.json`, `speckit-pro/.codex-plugin/` |

Method. The `codex exec --json` stream shows commands and agent messages. The
rollout files add per-request token counts (`token_count` events), the model
per turn (`turn_context`), tool calls (`spawn_agent`, `wait_agent`, `exec`) and
task durations (`task_complete`). Every figure below was derived from those
files. Token figures follow the receipt's convention: `total_tokens`, which
counts cached input as input. Wall times for tools come from the
`Wall time` line of each tool output.

The Claude Code profile in map #1144 used the same sources in the same shape
(receipt first, then transcript). Where a row has a Claude Code twin, it is
given in the comparison table.

## How far each run got

| Run | Plugin | Reached | Stopped by | Plan stage |
| --- | --- | --- | --- | --- |
| Baseline | 2.39.2 | Scaffold prerequisites only. No worktree, no files written | The scaffold skill stops when `install-codex-agents` reports a stale or missing agent file. The dry run flagged one file (the UAT runbook author) | Not run |
| 2.40.0 smoke | 2.40.0 | Scaffold passed (worktree, design concept, workflow file, push). Plan started and stopped in its first action | Autopilot requires `update_plan`; `codex exec` does not expose it (`TypeError: tools.update_plan is not a function`), and the skill says to stop on a failed call | Stopped at 30.6 s, no phase work |

Notes on the baseline stop. The helper compared against an agent folder in the
real user home, not the run's isolated Codex home, and the run's own home held
all 14 agent files identical to the plugin's. I read this as a harness
mismatch, not a plugin defect, but I could not confirm the root cause (see
Unconfirmed).

## Per-stage wall clock and tokens (from receipts)

| Stage | Baseline (2.39.2) | 2.40.0 smoke |
| --- | --- | --- |
| Scaffold | 88.5 s, 396,892 tokens | 450.7 s, 2,064,093 tokens |
| Plan | not run | 30.6 s, 117,849 tokens |
| Plan review | not run | not run |
| Implement | not run | not run |

Both receipts' token figures equal the root thread's final cumulative
`total_tokens` exactly (2,054,969 input plus 9,124 output for the smoke
scaffold; 117,474 plus 375 for the plan). They do not include the child
agent's 171,122 tokens. Adding it, the smoke scaffold is 2,235,215 tokens, 8.3%
more than the receipt shows.

## Orchestrator turns and context size

A turn here is one model request. Each `token_count` event is one request.

| Thread | Requests | First request input | Median input | Peak input | Cached share | Output tokens (reasoning) |
| --- | --- | --- | --- | --- | --- | --- |
| Baseline scaffold root | 9 | 35.2K | 45.0K | 49.5K | 88.9% | 2,023 (19) |
| Smoke scaffold root | 34 | 35.6K | 64.6K | 76.1K | 96.0% | 9,124 (200) |
| Smoke plan root | 3 | 38.3K | 39.5K | 39.6K | 39.6% | 375 (16) |
| Smoke scaffold child | 5 | 27.4K | 30.9K | 39.5K | 78.4% | 9,389 (7,790) |

- The model context window reported by the host is 258,400 tokens. The root
  stayed under 30% of it in the scaffold.
- The root ran on `gpt-6.1-sol` with no reasoning effort set. Reasoning tokens
  were 200 of 9,124 output tokens.
- Mean time per root request in the smoke scaffold was 13.2 s (449.6 s over 34
  requests). Tool time was 11.4 s of that (2.5%), so about 97% of the wall
  clock is model latency and waiting. The longest single step was 71 s, the
  model writing the workflow file script.
- The first-request input is about 36K to 38K before any work. The autopilot
  skill alone expands to roughly 18K tokens (the `cat` of it reported 17,871
  tokens before truncation) and it was injected into context by the skill
  mention and then read again with `cat`. The plan root re-read it once, with
  the output capped at 1,000 tokens.
- Claude Code's orchestrator median in the plan stage is 171K to 200K (map
  #1144). The Codex scaffold root is far below that, but a scaffold is not a
  plan stage. Do not read this as a Codex advantage until a plan stage runs.

## Agent rows

Only one agent ran in either run.

| Agent | Spawns | Wall | Model | Effort | Tokens | Requests | Tool calls |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `blindspot` (type `codebase-analyst`) | 1 | 179.0 s (task duration) | `gpt-6-luna` | max | 171,122 (161,733 input, 9,389 output, 7,790 reasoning) | 5 | 4 `exec` calls (one ran several commands in parallel inside a script) |

- The model and effort match `codebase-analyst.toml` (luna, max). So spawn by
  `agent_type` did apply the agent file's model and effort for this agent.
  Whether it does for the `gpt-6-sol` / `xhigh` agents is unconfirmed.
- Tool time inside the child was 1.0 s. The last request, writing the answer at
  effort max, took 89 s of the 179 s. Reasoning was 83% of the child's output
  tokens.
- The child was spawned with `fork_turns: "none"` and a task package, as the
  scaffold skill requires. It did not inherit the parent's context.

## spawn_agent and wait_agent pattern

Smoke scaffold root, in order:

| Time (UTC) | Event | Note |
| --- | --- | --- |
| 15:47:25 | `spawn_agent` (`blindspot`, `codebase-analyst`, `fork_turns: none`) | 1 call; returns task name at once |
| 15:47:47 | `wait_agent` 10,000 ms | timed out |
| 15:48:10 | `wait_agent` 10,000 ms | timed out |
| 15:48:31 | `wait_agent` 10,000 ms | timed out |
| 15:48:54 | `wait_agent` 10,000 ms | timed out |
| 15:50:24 | `wait_agent` 10,000 ms | completed in 0.3 s; the child's `FINAL_ANSWER` arrived as an agent message |

What this shows:

- Parallelism between parent and child is real. The parent made six other
  `exec` calls and wrote the workflow file during the child's 179 s. When the
  parent finished its own work at 15:50:21, the child was done 3 s later, so
  the parent was almost never blocked.
- Each poll is a full model request. The five requests that issued
  `wait_agent` read 64.6K to 70.3K tokens of context each, 336,744 tokens in
  total. That is 16.3% of the root thread's 2.06M tokens, nearly all cache
  reads. The polls also did no useful work themselves; the parent's real work
  went into the other 29 requests.
- The per-wait timeout was 10 s. The scaffold skill says per-wait timeout is
  "whatever the surface provides", with a 5-minute pass deadline. Why 10 s was
  chosen is unconfirmed.
- `spawn_agent` and `wait_agent` must be direct tool calls, not called inside
  the `exec` JavaScript tool (stated in the runtime's own role prompt). So
  every wait costs one request; they cannot be batched into a script.
- Only one agent ran, so whether Codex launches several at once is not
  observed. The autopilot skill says to dispatch in waves of at most
  `subagent_slots`, with `subagent_slots = 1` when the session exposes no
  count (`speckit-pro/skills/speckit-autopilot/SKILL.md:197-203`). The host
  also adds a developer message that forbids spawning agents unless a skill
  or AGENTS.md explicitly asks for it.
- The `codex exec --json` event stream records the five waits as
  `collab_tool_call` items but does not record the `spawn_agent` call or the
  child's work. Only the rollout files show the child. A profile built from
  event streams alone would miss every agent.

## Repeated reads

Heuristic: count shell calls that name a file path in the root rollouts.

| Run | Finding |
| --- | --- |
| Smoke scaffold root (27 `exec` calls, 31 shell commands) | Roadmap reads: one `cat`, one `sed` range, and one more in the child (`nl -ba`). The other mentions of the roadmap path are gate helpers and a write. The workflow template, the install helper and the constitution were each named in two calls. `capability-discovery.md` and `grounding.md` once each. |
| Baseline root (8 `exec` calls) | The install helper source was named in 3 of 8 calls while the model debugged a helper call (`helper_operation_mismatch`, then `invalid_destination`). The agent file `codebase-analyst.toml` was named in 2. |
| Smoke plan root | The autopilot `SKILL.md` was read once with `cat` even though the skill mention had already expanded it into context. |

Repeated reads are minor in these runs: at most 2 or 3 per file, against
Claude Code plan-stage counts of 8 to 21 per file. The counts are a path-mention
heuristic, not a tool-result audit. Nothing here says what the plan stage reads.

## Research broker

Zero research-broker calls in any Codex transcript. The broker is declared for
Codex (`speckit-pro/.codex-plugin/sweep-mcp.json`), and `domain-researcher`
is told to use only `research_search` and `docs_query`. The scaffold analyst
is a `codebase-analyst` and does not use it. In Claude Code the broker failed
on every call (24 of 24 in the baseline, 27 of 27 in the smoke, per the
Claude profile). Whether it fails on Codex is unknown.

## Codex model and effort as shipped

From `speckit-pro/codex-agents/*.toml` at 2.40.0. The installed copies in both
runs are byte-identical to these. The root orchestrator is not a custom
agent; it ran `gpt-6.1-sol` with no effort set.

| Agent | Model | Effort | Sandbox |
| --- | --- | --- | --- |
| phase-executor | gpt-6-sol | xhigh | workspace-write |
| clarify-executor | gpt-6-sol | xhigh | read-only |
| checklist-executor | gpt-6-sol | xhigh | workspace-write |
| analyze-executor | gpt-6-sol | xhigh | workspace-write |
| implement-executor | gpt-6-sol | xhigh | workspace-write |
| artifact-author | gpt-6-sol | xhigh | workspace-write |
| uat-runbook-author | gpt-6-sol | xhigh | workspace-write |
| formal-model-author | gpt-6-sol | xhigh | read-only |
| consensus-synthesizer | gpt-6-sol | medium | read-only |
| consensus-tiebreaker | gpt-6-sol | max | read-only |
| codebase-analyst | gpt-6-luna | max | read-only |
| spec-context-analyst | gpt-6-luna | max | read-only |
| domain-researcher | gpt-6-luna | max | read-only |
| autopilot-fast-helper | gpt-6-luna | low | read-only |

Counts: 10 agents on sol (8 at xhigh, one medium, one max), 4 on luna (3 at
max, one low). Compare Claude Code in the map: executors on Opus at high,
consensus analysts on Sonnet at max. Every plan-stage executor on Codex is at
the highest routine effort tier.

Hooks (`speckit-pro/codex-hooks.json`): a `PreToolUse` guard on `Bash`
(5 s timeout), a `PreToolUse` policy hook on `apply_patch|mcp__.*` (5 s) and a
`Stop` hook (15 s). The runs used `--dangerously-bypass-hook-trust`. No hook
events appear in the transcripts, so hook cost and whether the `Bash` matcher
fires on `exec_command` inside the `exec` tool are both unobserved.

## Comparison with the Claude Code profile (map #1144)

| Quantity | Claude Code baseline | Claude Code 2.40.0 smoke | Codex baseline | Codex 2.40.0 smoke |
| --- | --- | --- | --- | --- |
| Scaffold wall | 540 s | 452 s | 88.5 s (stopped early) | 450.7 s |
| Scaffold tokens (receipt) | 4.13M | 2.77M | 0.40M | 2.06M (2.24M with the child) |
| Plan wall | 94 min | 120 min | not run | 30.6 s (stopped) |
| Plan tokens | 38.9M | 64.6M | not run | 0.12M (stopped) |
| Orchestrator context, median / peak | 171K / 279K | 200K / 324K | 45K / 50K (scaffold) | 65K / 76K (scaffold) |
| Cached share | about 94% | about 95% | 88.9% | 96.0% (scaffold) |
| Research broker | 24 of 24 failed | 27 of 27 failed | no calls | no calls |

The Claude Code columns are copied from the Claude profile summarized in
#1144. The Codex plan figures say nothing about the 30-minute and 15M-token
target.

## What a Codex plan-stage profile still needs

| # | Fact | Why it matters | Run that supplies it |
| --- | --- | --- | --- |
| 1 | Per-phase wall and tokens for specify, clarify, plan, checklist, tasks, analyze, artifacts, in order | The target is a plan-stage total on each host | Full plan stage on Codex with the `update_plan` stop removed |
| 2 | Per-agent time, tokens, tool counts for the executors (sol, xhigh) and the 7 consensus analysts (luna, max) | The Claude profile found consensus (30 to 36 min) and the artifact author (23 to 38 min) dominate | Same run; read the child rollout files, not the event stream |
| 3 | Whether Codex starts several agents at once, and the `subagent_slots` the session exposes | Decides if consensus and checklist fan-out can help on Codex | Same run; count `spawn_agent` calls per request and concurrent child spans |
| 4 | Child-agent tokens in the receipt | The 15M target is read from the receipt, which today omits them | Harness change: sum child rollouts into the stage total. Check the smoke's 171K gap closes |
| 5 | Poll cost over a long run | One scaffold had 5 polls and 16.3% of root tokens. A plan stage with about 25 agents could be far higher | Same run; count `wait_agent` requests and their input size |
| 6 | Root context growth and any compaction over the plan stage | Window is 258,400; Claude's median is 171K to 200K | Same run; track `last_token_usage` per request and compaction events |
| 7 | Model and effort actually applied for `gpt-6-sol` / `xhigh` agents | Confirmed only for luna / max | Same run; check each child's `turn_context` |
| 8 | Research broker reachability and rate-limit behaviour on Codex | Failed 100% on Claude Code | Same run, at the first domain-researcher |
| 9 | Hook cost per tool call and whether the `Bash` matcher fires | Unobserved | Same run with hook output captured; or a short targeted probe |
| 10 | Cache-hit behaviour across spawned agents (the child was 78% cached; the root 96%) | Drives cost per token | Same run |
| 11 | Run-to-run variance | Both Claude runs differed by 66% in tokens on different fixture tags | At least two plan-stage runs on the same fixture tag |

Which run to do:

1. **Scratch-clone run with a local patch (recommended, no new ticket
   dependency).** Clone the plugin to scratch, and in the autopilot skill's
   `skills/` source remove the `update_plan` stop (the Codex Runtime Contract
   at `SKILL.md:147` and the 43 lines that mention `update_plan` across 6 files:
   `SKILL.md` 11, `phase-execution.md` 20, `error-recovery.md` 3,
   `task-list-canonical.md` 5, `prerequisites.md` 2, `post-implementation.md`
   2), regenerate the Codex payload (the generated agent files name
   `scripts/refresh-release-artifacts.py`), point the canary at the scratch
   marketplace, and run the base variant through the plan stage. The canary
   already uses a scratch marketplace for the plugin. This answers facts 1 to
   10. The patch must also keep the progress block as the
   only progress record; #1079 says that is the intended end state.
2. **Wait for #1079.** It deletes the `update_plan` requirement on both hosts
   and is blocked by #1078. It is the clean route, but it is in phase 3 of the
   health plan and opens after phase 2 closes. The map's "fix performance
   before the next full canary run" decision argues against waiting.
3. Either way, first fix the receipt (fact 4), or sum the child rollouts by
   hand, or the token total will read low by the child share.

## Unconfirmed, and where I looked

- **Why the baseline stopped.** The helper reported a stale or missing UAT
  runbook author file, but the run's own agent folder holds all 14 files,
  identical to the plugin's. I read the dry-run output and the final message.
  I did not find where the helper decided the destination. Treat it as a
  harness mismatch, not proven.
- **Whether the 2.40.0 smoke's Codex agents install matches the baseline's.**
  Both agent folders have 14 matching files. Install timing was not checked.
- **Why the per-wait timeout was 10 s.** The skills say "whatever the surface
  provides". I did not find the host's default.
- **Hooks.** No hook events in the event streams or rollouts (searched for
  hook event types). Cost and matcher behaviour unknown.
- **Whether `update_plan` exists on any Codex surface.** In `codex exec`
  0.160.0 the tool list had no match. I did not test the interactive CLI or
  the hosted surface. `codex features list` shows `multi_agent` stable and
  on, and no plan-related stable flag.
- **Claude Code figures.** Taken from the Claude profile summarized in map
  #1144. I did not re-derive them here.
- **Spawn concurrency.** One `spawn_agent` call was observed in total.
- **Receipt token rule.** I confirmed the receipt equals the root thread's
  cumulative total in all three comparable cases. I did not read the canary
  harness code, so whether the omission of child tokens is intended is
  unconfirmed.
