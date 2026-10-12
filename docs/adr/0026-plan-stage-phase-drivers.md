# Run each planning phase in a phase driver

Status: accepted

For [#1308](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1308)
and [#1317](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1317),
the plan stage must meet the [#1177](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1177)
target on each host: 15M tokens and 1,800 s, counting the root thread and every
subagent together. Canary round 2 measured 55.5M on Claude Code (35.1M root,
18.9M subagents) and 27.4M on Codex (18.1M root, 9.3M children). The root's
context averaged 211K tokens and peaked at 439K, and the plan stage's final
steps alone cost 9.4M over 34 root calls at that peak. Cost scales with root
calls times average context, so prose changes cannot close the gap.

We decided five things.

1. **The runner owns the terminal sequence.** One mutation helper builds the
   artifact pages and the packet, opens the draft PR, records the preview as
   unavailable on a headless run, writes `plan/completed` and returns the stop
   label. A model writes only the page prose, through one artifact-author
   dispatch ([ADR 0019](0019-runner-builds-artifact-pages.md)). A model
   can no longer skip the draft PR, and about 30 root calls become about 3.
2. **Helper answers are compact.** Every runner helper returns a status and the
   next action to the root, under a size cap a test enforces. Skill text never
   tells the root to read planning artifacts or runner source.
3. **Each planning phase runs in a phase driver.** `phase-executor` becomes the
   phase driver. For specify, plan and tasks it runs the SpecKit skill itself.
   For clarify, checklist and analyze it dispatches the existing executors and
   consensus agents one level down. The root keeps only briefs and envelopes,
   so its context resets between phases. The agent count stays at 12 on both
   hosts.
4. **The driver returns a fixed envelope.** A runner-owned JSON contract holds
   the phase, its status, the next action, changed artifact paths, gate ids with
   their results, counts, a capped blocker line and a usage receipt. A test
   enforces the schema and a byte cap. The root then calls one runner helper
   that re-verifies the phase from disk. Missing or unparseable evidence fails
   the phase; a driver's claim never passes a gate.
5. **Flat mode is the fallback.** A preflight reads the host's subagent depth.
   Below 2, the root dispatches executors directly under the compact-answer
   contract, and the receipt records `mode=flat`. Codex defaults to
   `agents.max_depth = 1`, so flat mode is what most Codex installs run.
   Prerequisites tell the user that a depth of 2 enables the phase reset. Depth
   never fails a run.

Proof comes in two parts. Repo tests fail first: the terminal helper finishes
in one call, each helper answer and envelope stays under its cap, and skill
text names no root reads. Each canary receipt adds, per segment, the root call
count and the average and peak context, so a regression names its phase. Gate
8 stays the final acceptance: three green runs per host, with Codex run in both
flat and nested mode and Claude Code run nested.

We rejected relying on host auto-compaction: neither host lets a plugin trigger
it, and a compaction mid-phase can drop state the run needs. We rejected one
headless session per phase, which breaks the single interactive run users get
today. We rejected a new 13th agent wrapping `phase-executor`: it adds a
nesting level and a dispatch to the three single-command phases. We rejected
trusting the envelope's gate results, which would let a model's claim decide a
phase. We rejected failing closed on depth below 2, which would block default
Codex installs.
