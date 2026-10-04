# The runner briefs each planning phase; prose no longer drives dispatch

Status: accepted

Decision ticket: [Orchestrator weight on the plan stage: digests and plan-only references](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1151), part of [Wayfinder: speckit-pro planning performance](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1144).

On the plan stage, the runner hands the orchestrator a phase brief for the current planning phase: the agent to dispatch, its inputs, the files it may read, and the gate to check afterward. The orchestrator follows the brief instead of re-reading `phase-execution.md` to learn each phase. Executors get only the reference slices their phase needs, placed in their dispatch prompt by the runner, instead of being told to read the four shared references (1,726 lines per spawn).

The measured cost drove this. On the canary fixture, the orchestrator's median context was 171K to 200K tokens across 96 to 132 turns, and about 94% of all plan-stage tokens were cache re-reads. The orchestrator read `phase-execution.md` 6 times, and subagents re-read the same references again and again. A brief is the same on Claude Code and Codex, so it also serves host parity (ADR 0003), and it moves behavior into runner code the tests can see.

## Considered Options

- **Split the prose by stage only.** Rejected as the main fix: the orchestrator would still read prose to learn each phase, so the context cut is limited. A plan-only reference set falls out of the brief anyway.
- **Do the prose split first, then the brief.** Rejected: the split is churn that the brief replaces.
- **Fix only the executors' reads.** Rejected: it leaves the orchestrator's context, the largest token driver, in place.

## Consequences

- The phase 5 prose tickets cut what the brief makes redundant. Trimming `phase-execution.md` (#1091) waits on the brief.
- Concurrency (which agents a brief launches together) is decided separately in [Parallel dispatch on the plan stage](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1158).
- The brief carries policy facts only. The runner still owns the stop policy (ADR 0010), and the brief never stands in for a gate check.
