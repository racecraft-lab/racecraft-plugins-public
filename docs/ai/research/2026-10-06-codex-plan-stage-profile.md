# Codex plan stage profile

> Status: measured, one new canary run plus one earlier run on the same build line.
> Dated record: counts, versions and file names describe the tree on 2026-10-06.
> Ticket: [PF-21, profile the Codex plan stage](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1198), part of
> [Spec addendum: speckit-pro planning performance](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1177).
> Compares against [ADR 0018](../../adr/0018-runner-phase-brief.md).

## Answer first

The Codex plan stage runs its waves concurrently, but the orchestrator launches each wave one agent per model response instead of all agents in one turn, and it polls with 10 second waits that cost about a third of its input tokens.

| Finding | Evidence |
| --- | --- |
| Concurrent dispatch works on Codex | Three checklist executors overlapped (peak 3 live children). The wave took 200 s; the same three agents run end to end sum to 558 s. |
| Wave launch is serial, against the skill text | Each wave entry was its own `spawn_agent` call in its own model response, 9 to 13 s apart. The skill says to issue one `spawn_agent` per entry "in one turn". |
| Polling is a large cost | 50 `wait_agent` calls with `timeout_ms` 10000. 37 timed out. They re-read 9.2M input tokens (about 36% of the orchestrator's input) and blocked 411 s (26% of wall time). |
| The orchestrator is the token driver | The orchestrator spent 25.8M of 36.1M plan-stage tokens (71%). Cache reads are 99% of its input. Its context peaked at 228K of a 258K window and was compacted once. |
| The plan target is half met | Wall time 1,584 s is under the 1,800 s limit. Tokens 36.1M are 2.4 times the 15M limit. |

Follow-up [#1286](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1286) covers the two wave defects (serial launch, short polls).

## Method

- Host: Codex CLI 0.160.0. Orchestrator model `gpt-6.1-sol`; executors `gpt-6-sol` (one `gpt-6-luna` analyst in the earlier run). Plugin `speckit-pro` 2.40.0 at the commit that merged the scaffold preset upgrade (#1283), with plan-stage waves (#1277) in place.
- Harness: the canary harness (`canary/harness.py`, fixture tag `fixture-v6`), `--host codex --variant base`, one run, in an isolated Codex home with the plugin's standing autopilot policy installed. The stages ran as separate invocations: scaffold, plan, plan review, implement.
- Source of numbers: the run's rollout files. One file per agent (the orchestrator and each child). Timestamps give start, end and wall time. `token_usage_record` events give tokens per model response. Tool calls come from the response items. A throwaway script (not committed) summed them per agent, per phase and per wave.
- Cross-check: the sum of the rollouts equals the receipt. Plan-stage tokens in the receipt are 36,107,790 (orchestrator 25,770,871 plus ten child rollouts 10,336,919). The rollout-level orchestrator total is 26,003,297. The 232,426 difference is one context-compaction request that the headline `turn.completed` usage does not count.
- "Run B" below is the new run. "Run A" is the earlier run (plan stage 1,619 s, 30.6M tokens, 11 child rollouts). Run A's plan stage ended without a state boundary, because the sandbox denied Git's index lock in the linked worktree; the harness has since been fixed. Its profile numbers stand, and its handoff failure is outside this profile.
- Orchestrator reasoning effort is not recorded in the rollouts, so it is not reported.

## Plan stage totals

| Measure | Run B | Run A |
| --- | --- | --- |
| Plan-stage wall time | 1,584 s | 1,619 s |
| Plan-stage tokens | 36,107,790 | 30,560,122 |
| Orchestrator tokens | 25,770,871 (71%) | 20,537,981 (67%) |
| Child tokens (sum) | 10,336,919 (29%) | 10,022,141 (33%) |
| Child rollouts | 10 | 11 |
| Orchestrator model responses | 175 | 136 |
| Orchestrator context at the first response / 75% of responses / peak | 41K / 215K / 228K | 41K / 187K / 224K |
| Context compactions | 1 (at 1,507 s) | 0 |
| Cache reads, share of orchestrator input | 99% | 99% |
| Plan target (1,800 s, 15M tokens) | wall met, tokens not met (2.4x) | wall met, tokens not met (2.0x) |

Scaffold for Run B took 280 s and 2.66M tokens; implement took 142 s and 1.85M tokens. Neither is in the plan-stage figures.

## Per phase

A phase window runs from one dispatch to the next. "Orchestrator only" is window time with no child alive: the orchestrator reading, running runner requests, or deciding.

Run B:

| Window | Start s | End s | Orch. responses | Orch. tokens | Child tokens | Children s | Orchestrator only s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Orient (before first dispatch) | 0 | 155 | 23 | 1,679,477 | 0 | 0 | 155 |
| Specify | 155 | 257 | 12 | 1,337,544 | 482,840 | 67 | 35 |
| Clarify | 257 | 332 | 8 | 1,036,383 | 284,891 | 46 | 29 |
| Plan | 332 | 447 | 13 | 1,893,644 | 395,005 | 69 | 46 |
| Checklist (3 domains, verify wave) | 447 | 680 | 30 | 4,930,386 | 3,508,029 | 200 | 33 |
| Tasks | 680 | 937 | 26 | 4,836,588 | 2,025,767 | 198 | 59 |
| Analyze | 937 | 1,096 | 15 | 3,097,422 | 2,368,805 | 136 | 23 |
| Confidence | 1,096 | 1,171 | 6 | 1,284,424 | 110,744 | 13 | 63 |
| Artifacts and finish | 1,171 | 1,583 | 42 | 5,907,429 | 1,160,838 | 226 | 186 |

The Artifacts and finish window includes the compaction request. Orchestrator-only time totals 629 s (40% of wall time). The last 185 s after the artifact author returned went to the orchestrator's own draft-PR packet, validation and workflow edits.

Run A has the same shape: orchestrator-only time 632 s (39%), checklist wave 284 s, tasks 147 s, artifacts 144 s.

## Per agent (Run B)

All executors run `gpt-6-sol`. Recorded effort: `low` for specify, plan and tasks, `medium` for the rest. Every executor's only tools were `exec` (shell and file reads and writes through the exec wrapper) and `send_message` back to the orchestrator.

| Agent | Start s | Wall s | Turns | Model responses | Tokens | Cache read | Output | Peak context | Exec calls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Orchestrator | 0 | 1,583 | 1 | 175 | 26,003,297 | 99% | 45,340 | 228,222 | 98 |
| specify | 155 | 67 | 1 | 13 | 482,840 | 91% | 5,622 | 42,224 | 12 |
| clarify | 257 | 46 | 1 | 7 | 284,891 | 84% | 2,439 | 51,586 | 6 |
| plan | 332 | 69 | 1 | 11 | 395,005 | 96% | 6,010 | 41,759 | 10 |
| api check | 447 | 192 | 2 | 27 | 1,607,855 | 96% | 7,987 | 73,028 | 23 |
| testing check | 457 | 189 | 3 | 18 | 1,016,152 | 96% | 7,762 | 68,180 | 15 |
| data check | 470 | 177 | 3 | 18 | 884,022 | 96% | 6,296 | 58,738 | 15 |
| tasks | 680 | 198 | 2 | 39 | 2,025,767 | 98% | 10,651 | 64,483 | 37 |
| analyze | 937 | 136 | 1 | 34 | 2,368,805 | 97% | 9,952 | 89,972 | 32 |
| confidence | 1,096 | 13 | 1 | 3 | 110,744 | 73% | 960 | 43,234 | 2 |
| artifacts | 1,171 | 226 | 1 | 19 | 1,160,838 | 94% | 10,350 | 78,401 | 16 |

Context window is 258,400 tokens for every agent. The largest executor context is 90K (analyze). Every executor is far below the orchestrator's 228K. Turns above 1 are the verify wave and send-back follow-ups.

Run A per-agent rows are in the same range: checklist domains 805K to 1.50M tokens and 254 to 268 s, tasks 2.02M, analyze 1.13M, artifacts 1.31M, plus a `gpt-6-luna` spec-context analyst (468K tokens, 35 s). One run A executor turn ended with a `server_overloaded` model error and the run continued.

## Wave concurrency

- Checklist domain wave (Run B). Spawns at 447, 456 and 469 s. The three executors ran together until 639 to 647 s. Peak live children: 3. Wave wall time 200 s; per-agent wall times sum to 558 s, a 2.8 times speed-up over serial. Run A: 284 s against 786 s, 2.8 times.
- Verify wave (Run B). The three domains were re-run with `followup_task` at 606, 610 and 614 s and overlapped.
- Consensus waves. Neither run raised a consensus round that needed several analysts. Run B recorded zero consensus rounds. Run A routed one low-confidence item to one analyst. The multi-analyst waves in ADR 0018 are not exercised by this fixture and stay unconfirmed.
- Launch shape. The brief returned the waves (`waves: [[api, testing, data-integrity], [verify x3]]`, `max_agents` 3). The orchestrator then issued one `spawn_agent` per model response. The tool calls sit in three consecutive responses, each about 600 output tokens (the dispatch message), each re-reading the full orchestrator context. The third executor started 22 s after the first. In Run A every one of the 11 spawns was its own response too. The rollouts show what happened, not why. The Codex collaboration tools are direct tool calls only, not callable from the exec wrapper, which may push the model toward one call per response; not confirmed.

## Poll cost

| Measure | Run B | Run A |
| --- | --- | --- |
| `wait_agent` calls | 50 | 33 |
| Timed out (10 s with no result) | 37 (74%) | 18 (55%) |
| Orchestrator input tokens spent on poll responses | 9,218,503 | 5,296,694 |
| Share of orchestrator input | 36% | 26% |
| Output tokens on poll responses | 3,711 | 2,182 |
| Wall time blocked in `wait_agent` | 411 s (26%) | 556 s (34%) |
| `list_agents`, `send_message`, `followup_task` calls | 3, 6, 6 | 2, 2, 4 |

Every poll response re-reads about 184K cached tokens to emit a call of under 100 tokens. The plugin text says to "bound each `wait_agent` poll with `timeout_ms`" and gives no value. The orchestrator chose 10000 on every call. The Codex subagent documentation does not state a default or minimum for `timeout_ms` that I could find; the value was not confirmed against a vendor source. Whether a longer timeout returns early when a child finishes, and so cuts polls without adding latency, was not tested.

## Child-token sums

Per-agent and per-phase sums match the receipt. Children: 10,336,919 tokens across 10 rollouts (Run B), 10,022,141 across 11 (Run A). Executors average 1.0M tokens each, and cache reads are 73% to 98% of their input. The three checklist domains, tasks and analyze are 7.9M of the 10.3M (76%): checklist 3,508,029, tasks 2,025,767, analyze 2,368,805.

## What this confirms or corrects in ADR 0018

Confirms:

- The measured cost. ADR 0018 reports an orchestrator median context of 171K to 200K tokens over 96 to 132 turns and about 94% cache re-reads on Claude Code. On Codex the orchestrator peaks at 224K to 228K over 136 to 175 responses, with 99% cache re-reads. The orchestrator, not the executors, is the largest token driver on both hosts.
- Concurrent dispatch on Codex. The open item ("The first Codex plan-stage profile must confirm concurrent dispatch") is closed for the checklist domain and verify waves: peak 3 live children and a 2.8 times speed-up.
- The brief carries the waves and the model per entry. The orchestrator followed the brief's wave grouping and model choice.

Corrects:

- "Several `spawn_agent` calls and one wait." Observed: one `spawn_agent` per response, then many waits. The wave still runs in parallel, but it costs one orchestrator response per agent and staggers starts.
- "One wait." Observed: a loop of 33 to 50 ten-second waits per plan stage, most of them timeouts.
- Verify wave launch is `followup_task` to existing threads, not `spawn_agent`. The ADR names only `spawn_agent`.
- Still unmeasured: multi-analyst consensus waves (this fixture raises none), and any wave larger than `max_agents` 3.

## Canary run outcome (context only)

The plan stage reached its boundary and opened a draft pull request in the fixture repository. The run's overall verdict is fail, on assertions outside this profile: `install_probe.skill_expansion`, `plan.updated_at_in_window`, `plan.elapsed_seconds_matches_wall` (no execution-control ledger window), `plan_review.unavailable`, `implement_end` (`stop_reason:tool_unavailable`), `uat_runbook`, `unregistered_stops`, one open clarification and the planted-catch checks. The profile above does not depend on them.

## Limits

- One new run and one earlier run, one fixture, one host version. Figures vary run to run: the two plan stages differ by 2% in wall time and 18% in tokens.
- Per-phase orchestrator tokens are attributed by the time window of each model response, so a phase boundary is approximate to one response.
- The fixture is small (a word-frequency feature). Larger specs raise executor tokens; the orchestrator's context and poll costs scale with run length rather than spec size.
