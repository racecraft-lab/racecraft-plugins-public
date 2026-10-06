# Consensus Protocol Reference

The consensus protocol is the second layer of the autopilot's
two-layer resolution system, used by 3 phases: Clarify,
Checklist, and Analyze.

Consensus dispatch runs as batched ordinary subagents; see
[agent-teams-integration.md](./agent-teams-integration.md) use site 5.

## Contents

- [Two-Layer Resolution Architecture](#two-layer-resolution-architecture) — executor first-pass then consensus second-pass
- [Plan-Stage Tiers](#plan-stage-tiers) — security, low-confidence and recommendation routing (ADR 0022)
- [Category-Routed Dispatch (Tier A)](#category-routed-dispatch-tier-a) — `[codebase|spec|domain|security|ambiguous]` routing rules + escape-hatch
- [Batched Dispatch](#batched-dispatch) — multi-item fan-out in ONE tool turn
- [Three-Analyst Consensus Rules (Round 2 / N=3)](#three-analyst-consensus-rules-round-2--n3) — security agreement rules
- [The 3 Perspective Agents](#the-3-perspective-agents) — codebase-analyst / spec-context-analyst / domain-researcher
- [Consensus Rules](#consensus-rules) — three-analyst agreement and tiebreak rules
- [Security Keywords](#security-keywords) — always-all-3 trigger words
- [Round 3 Tiebreak](#round-3-tiebreak) — a fresh analyst plus a max-effort `consensus-tiebreaker` resolve what Rounds 1 and 2 could not; nothing asks a human or stops
- [Phase-Specific Consensus Flows](#phase-specific-consensus-flows) — Clarify, Checklist, Analyze patterns + per-phase prompt templates ("Specification Context" / "Question" / "Your Task" sub-sections appear inside each flow)
- [Pre-Implement Confidence Emit (end of Phase 6 Analyze)](#pre-implement-confidence-emit-end-of-phase-6-analyze) — synthesizer emits `📊 Confidence: X.XX` + 5-criterion breakdown for the optional Confidence Gate at G6.5
- [Determining Agreement](#determining-agreement) — how the synthesizer scores responses
- [Logging](#logging) — Consensus Resolution Log row schema + Re-evaluation trigger (referenced from SKILL.md)

## Two-Layer Resolution Architecture

**Layer 1 — Executor agent (first pass):** Each phase has a
specialized executor agent (clarify-executor,
checklist-executor, analyze-executor) that runs the
`/speckit-*` command AND does direct research using capability-first
discovery for codebase context, spec context, library documentation,
web or domain research, source extraction, installed skills/plugins,
and repo-local helpers. Follow
`speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`
([capability-discovery.md](./capability-discovery.md)) for selection,
fallback, evidence, inventory, and metadata rules. The executor
resolves most items directly (~80%) and applies fixes to
artifacts. Items it doubts, and items that carry a security tag or
keyword, are flagged in its "Unresolved for consensus" summary
section with a category prefix and a `Confidence: low|high` line
(see "Category-Routed Dispatch" below). Every other item takes the
executor's recommendation.

**Layer 2 — Consensus agents (second pass):** The main
session (not the executor) runs `parse-consensus-categories` on
each flagged item and follows the `tier` it returns (see
[Plan-Stage Tiers](#plan-stage-tiers)).

**Why two layers:** Single-agent research handles
straightforward items efficiently. Consensus spends model effort
only where a second opinion pays: all three analysts on security
items, one analyst on items the executor doubts.

**When consensus is triggered:**
- Item carries a `[security]` tag or a security keyword (all-three consensus, every round)
- Executor marked the item `Confidence: low` (one analyst, no synthesizer)

Sources that disagree and items left over after the executor's fix pass
trigger nothing: the executor states a confidence and a recommendation.

## Plan-Stage Tiers

ADR 0022. `parse-consensus-categories` takes the item `line` and the
executor's `confidence` (`low` or `high`; a missing value counts as
`low`) and returns one `tier`. Dispatch exactly the analysts it returns.

| `tier` | Items | Analysts | Resolution |
|--------|-------|----------|------------|
| `security` | `[security]` tag or a [Security Keyword](#security-keywords), at any confidence | All 3 | Rounds, synthesizer and tiebreak as below |
| `low_confidence` | Everything else the executor marked `low` | One: the first tag that names a perspective, else `speckit-pro:domain-researcher` | Follow the helper's `answer_source` after the analyst returns (see [Single-analyst confidence rule](#single-analyst-confidence-rule-n1)) |
| `recommendation` | Everything else | None | The executor's recommendation stands |

Record every `low_confidence` and `recommendation` outcome in the
decisions list. Use kind `low_confidence_answer` for a `low_confidence`
item: the list renders those entries before all others. The plan stage
makes no decision-model call (ADR 0020).

## Category-Routed Dispatch (Tier A)

Each item in the executor's "Unresolved for consensus" section
MUST carry a category prefix and a `Confidence: low|high` line. The
orchestrator calls the `parse-consensus-categories` runner helper on
the item line and the confidence, and dispatches exactly the analysts
it returns. The table below states
what that helper implements; it is not a procedure to run by hand.

### Category tags

| Tag | Meaning | Routes to |
|-----|---------|-----------|
| `[codebase]` | Resolution depends on existing patterns/conventions in this repo's code | `speckit-pro:codebase-analyst` |
| `[spec]` | Resolution depends on project decisions in spec/plan/constitution/roadmap | `speckit-pro:spec-context-analyst` |
| `[domain]` | Resolution depends on external standards, RFCs, library docs, or community best practice | `speckit-pro:domain-researcher` |
| `[security]` | Item's substance is about security (credentials, access control, secrets, personal data). A [Security Keyword](#security-keywords) alone needs no tag: the helper widens it | All 3 (defense-in-depth, never single-routed) |
| `[ambiguous]`, unknown, or missing/unparseable prefix | Executor uncertain which perspective applies | `speckit-pro:domain-researcher` (the generic domain) |

The Routes-to column applies to a `low` confidence item. A `high` item
that is not security needs no analyst.

**Multi-category tags** are valid: `parse-consensus-categories` reads
the comma-separated category list inside the bracket and routes the
first tag that names a perspective, so `[codebase, domain]` dispatches
`speckit-pro:codebase-analyst` alone.

### Two-round protocol with escape hatch

Only the `security` tier runs these rounds, and its Round 1 already
dispatches all three analysts, so Round 2 fires only for a failed or
escaped analyst. A `low_confidence` item stops after its one analyst.

```text
ROUND 1 — security (all three)
  Call parse-consensus-categories with the unresolved item line and confidence.
  Enter these rounds only when its tier is security.
  Spawn all three analysts it returns and await their responses.

  IF an analyst failed (no valid response):
       queue only that analyst for ROUND 2; the item is not synthesized yet.

  ELSE:
       Run consensus-synthesizer with all three responses.
       IF its Flags include [ESCAPE_TO_ROUND_2] (a response carried an escape
          phrase such as "insufficient context", "not in this codebase",
          "no precedent", "outside my scope", or
          "cannot answer from this perspective"):
            queue only the escaped analysts for ROUND 2.
       ELSE apply the Consensus Rules below: APPLY edit and log, OR flag [ROUND_3_TIEBREAK].
       Low synthesizer confidence goes to ROUND 3, not another analyst fan-out.

ROUND 2 — retry failed or escaped analysts
  Retry only the failed or escaped analysts, once, with the missing context.
  Keep the successful Round-1 responses from the other perspectives.
  If a retry fails or escapes again, follow the fresh-analyst replacement in §Round 3 Tiebreak.
  Once all three responses are valid, run consensus-synthesizer with them.
  Apply the Consensus Rules below.
  APPLY edit OR flag [ROUND_3_TIEBREAK].

ROUND 3 — agent tiebreak (only after a [ROUND_3_TIEBREAK] flag)
  Run §Round 3 Tiebreak. Its result is applied like any other edit.
```

### Single-analyst confidence rule (N=1)

For a `low_confidence` item, call `parse-consensus-categories` again with
its original `line` and executor `confidence`, plus `analyst_confidence`
from the completed analyst response. Follow the returned `answer_source`:

| `answer_source` | Action |
|-----------------|--------|
| `analyst` | Apply the analyst answer; record the executor recommendation as the rejected alternative |
| `executor` | Keep the executor recommendation |

Missing or malformed analyst confidence keeps the executor recommendation.
Record the outcome as `low_confidence_answer` and finish the item after this
one analyst. No synthesizer or later analyst round runs for this tier.

### Three-analyst rules (N=3)

See Consensus Rules below.

### Re-evaluation trigger

If the Round-2 escape-hatch rate exceeds **10%** of consensus
items across any 30-day window of autopilot runs, revert to
always-3 dispatch and treat category tags as advisory rather
than authoritative. The threshold is documented here; the
metric is tracked via the Consensus Resolution Log
(see "Logging" below — the `Round` column is the data source).

### Deterministic helpers (runner)

Two runner helpers own the rules above. This prose mirrors them.
The helpers are what executes.

| Helper | Purpose |
|--------|---------|
| `parse-consensus-categories` | Reads one unresolved-item `line` plus the executor's `confidence` and optional `analyst_confidence`; returns `answer_source` (`analyst` or `executor` for nonsecurity items, `null` for security), `tags`, the `tier`, the `analysts` to spawn, the dispatch `reason`, and `security_route` (`tag` for an explicit `[security]` tag, `keyword` for a keyword alone, `null` otherwise). Implements every routing rule in [Plan-Stage Tiers](#plan-stage-tiers). It reads the whole line, not just the bracket, so a [Security Keyword](#security-keywords) anywhere in the item text widens to all 3 even when the executor tagged the item narrowly or marked it `high`. |
| `aggregate-crl` | Reads the Consensus Resolution Log table out of a workflow file and returns `total_items`, `round1`, `round2`, `escape_hatch`, `escape_rate_percent`, the `threshold_percent` it was given (default 10), and `exceeds_threshold`. |

**Call `parse-consensus-categories` for every unresolved item and
dispatch exactly the analysts it returns.** Do not route by reading
the table yourself. The helper is the only place the tier rules run:
a security keyword in the item text widens to all three analysts
whatever the executor put in the bracket or wrote as its confidence,
and a tag it does not recognize routes to the generic domain analyst.

```text
resolved_python -m speckit_pro_runner < request.json

request.json:
{
  "schema_version": "1.0",
  "request_id": "consensus-route-I1",
  "helper_id": "parse-consensus-categories",
  "operation": "parse-consensus-categories",
  "mode": "read_only",
  "inputs": { "line": "[codebase, domain] Q3: bcrypt or argon2?", "confidence": "low" }
}
```

`resolved_python` is the Python 3.11+ interpreter resolved by the
installed runtime contract, not a hardcoded interpreter name.

Call `aggregate-crl` out of band for the 30-day review, passing
`workflow_file` and an optional `threshold_percent`. Its
`exceeds_threshold` is the re-evaluation trigger above, computed
from the log rather than eyeballed.

## Batched Dispatch

When a consensus phase (Clarify, Checklist, Analyze) produces N
unresolved items, the orchestrator dispatches them in a **batched
fan-out across items**, not per-item serially. This applies to every
per-phase consensus invocation.

### Why batched

Each item's analysts work in isolation and return text; the
synthesizer then proposes an Artifact Edit. Across items the
analysts have no race (different perspectives on different items) —
so dispatching all `N items × |routed analysts per item|` calls in
ONE assistant message captures the full parallelism win without
risking consistency. Only the final Edit application needs to be
serial (write contention on spec.md / plan.md / tasks.md).

### Stages

```text
Stage 1 — All routed analysts, as the brief's waves (one turn each):
  Request the phase brief with `items` (each unresolved item's line and confidence)
  and `max_agents` (the host's concurrent-agent limit).
  Its security wave holds the three analysts of every security item; its
  low-confidence wave holds the one routed analyst of every low-confidence item.
  A wave over the limit arrives as consecutive waves of at most `max_agents`.
  (A recommendation item has no entry: apply the recommendation, no dispatch.)
  For each entry of a wave, all in ONE turn:
      Agent(subagent_type: "speckit-pro:" + <entry.agent>,
            run_in_background: true,
            description: "SPEC-XXX consensus R1 [I<entry.inputs.item>]: <item>",
            prompt: <consensus prompt for entry.inputs.item from that analyst's perspective>)
  Total dispatches across the two waves: Σ |Sx|
  Each analyst prompt ends with the `Reference dir:` line, built from the
  `plugin_root` that `validate-agent-install` returned.
  ↓
  Await ALL analysts of a wave before the next wave; the security wave's
  synthesizers (Stage 2) need only the security wave.

Stage 2 — All synthesizers, ONE assistant message:
  A low_confidence item follows the Single-analyst confidence rule above and
  finishes before this stage.
  For each security item Ix:
    Agent(subagent_type: "speckit-pro:consensus-synthesizer",
          run_in_background: true,
          description: "SPEC-XXX consensus synthesis (R1) [I<x>]",
          prompt: """
            ## Consensus Resolution
            **Protocol:** <plugin_root>/skills/speckit-autopilot/references/consensus-protocol.md
            **Unresolved Item:** <item Ix text>
            **Routed Categories:** [<categories from prefix>]
            **Security Route:** <security_route from parse-consensus-categories: tag | keyword | none; write JSON null as none>
            **Round:** 1
            **<Analyst> Response:** <response> | NOT SPAWNED (not routed)
            ... (one row per analyst, NOT SPAWNED if not in Sx)
          """)
  Total dispatches in one message: N
  ↓
  Await ALL synthesizers.

  Runtime name mapping: Claude Code dispatches
  `speckit-pro:consensus-synthesizer`; Codex dispatches the installed
  `consensus-synthesizer` with
  `spawn_agent(agent_type="consensus-synthesizer", ...)`.
  Omitting `agent_type` and accepting the default role is a failed dispatch.
  The parent never performs this synthesis itself.

  `Protocol:` is the absolute path of this file in the loaded plugin, built
  from the `plugin_root` that `validate-agent-install` returned. The
  synthesizer reads that path but reports only its plugin-relative form,
  because its result reaches committed records. A result
  whose reported `**Protocol:**` value is not the plugin-relative
  `skills/speckit-autopilot/references/consensus-protocol.md` is malformed,
  and so is any absolute or home path in that field.

Stage 3 — Apply Artifact Edits SERIALLY (orchestrator's own Edit calls):
  ROUND_2_QUEUE = []
  For each synthesizer result, in item order:
    IF Flags = None AND Confidence = high AND agreement meets the Consensus Rules:
      Apply Artifact Edit to spec.md / plan.md / tasks.md
      Write a CRL row: Round=1, Routed Categories=Sx, Outcome=<outcome>, Analysts Used=Sx
    IF Flags includes [ESCAPE_TO_ROUND_2]:
      Push (Ix, failed or escaped analysts) onto ROUND_2_QUEUE
    ELSE IF Flags includes [ROUND_3_TIEBREAK] OR low confidence: run the Round 3 tiebreak per
      §Round 3 Tiebreak after this batch's other edits are applied; the
      flag is the Round 3 trigger and never a question or a stop

If ROUND_2_QUEUE non-empty:
  Stage 4 — Retry only each queued item's failed or escaped analysts in ONE message;
            retain successful Round-1 responses from the other perspectives
  Stage 5 — All Round-2 synthesizers in ONE message
  Stage 6 — Apply accepted Round-2 edits serially; unresolved items go to Round 3.
            A repeated escape exhausts the retry; use the fresh replacement below,
            then Round 3 if it also fails or escapes. No item re-enters Round 2.
```

### What stays serial — and why

Stage 3 / Stage 6 (Artifact Edit application) MUST be serial. The
`Edit` tool modifies spec.md / plan.md / tasks.md; concurrent edits
to the same file via concurrent Edit calls race.

### Logging requirement

Every synthesizer result writes exactly one row to the Consensus
Resolution Log in the workflow file. Rows are written in item-encounter
order so the `#` column reflects the order items appeared in the
executor's "Unresolved for consensus" summary, NOT the order
synthesizers happened to return. This keeps the log human-readable
even when batched dispatch returns results out of order.

### Failure semantics

If an analyst in Stage 1 errors, others continue (background pattern
semantics). After Stage 1's await completes, Stage 2 synthesizes only
items where all required analysts succeeded; failed items get
re-queued for a single retry. If retry also fails, the failed analyst
is replaced by a fresh analyst, never by a human (see
[Round 3 Tiebreak](#round-3-tiebreak)); do NOT block the rest of
the batch.

If a synthesizer dispatch fails or returns a missing or malformed result, the
parent applies no edit, writes no completed Consensus Resolution Log row, and
does not mark the item complete. The parent may retry the same named
synthesizer once with the same analyst responses. A second invalid result is not a stop: the
parent runs the Round 3 tiebreak with one `consensus-tiebreaker`. If that
result is invalid too, the item is deferred to the
end-of-run request as in [Round 3 Tiebreak](#round-3-tiebreak) and the run
continues; the parent must never replace it with parent-authored synthesis.

## Three-Analyst Consensus Rules (Round 2 / N=3)

## The 3 Perspective Agents

| Agent | Perspective | Primary Tools | Strength |
|-------|------------|---------------|----------|
| `speckit-pro:codebase-analyst` | What does the existing code show? | codebase context capability selected through [capability-discovery.md](./capability-discovery.md) | Finding established patterns, types, naming conventions, error handling |
| `speckit-pro:spec-context-analyst` | What do project decisions say? | Read (constitution, technical roadmap, prior specs, CLAUDE.md) | Grounding answers in established principles and prior decisions |
| `speckit-pro:domain-researcher` | What do best practices recommend? | web or domain research, library documentation, or source extraction capability selected through [capability-discovery.md](./capability-discovery.md) | External evidence — API docs, standards, community patterns |

## Consensus Rules

One rule set applies to every run; no setting changes it.

| Scenario | Action |
|----------|--------|
| **2/3 agree** | Use the majority answer. Log the dissenting perspective for context. |
| **3/3 agree** | Use the answer with high confidence. |
| **All 3 disagree** | Flag as `[ROUND_3_TIEBREAK]` with all 3 perspectives, which starts the [Round 3 Tiebreak](#round-3-tiebreak). |
| **Security item** (`[security]` tag, or keyword with any analyst returning `security_relevant: true` or omitting the field) | Apply only on 3/3 agreement. A 2/3 majority or all-disagree flags `[ROUND_3_TIEBREAK]` and starts the Round 3 tiebreak. |
| **Keyword-only item** (every routed analyst returns `security_relevant: false`) | Use the ordinary rules above: a 2/3 majority applies. |

## Security Keywords

These keywords in the question, gap, or finding text route the item to all three analysts. The item's bar rises to **unanimous agreement** unless every routed analyst returns `security_relevant: false`:

```
auth, token, secret, encryption, PII, credential, permission, password,
authentication, authorization, session, cookie, jwt, api-key, access-control
```

Case does not matter and the plural counts: `Tokens` and
`credentials` are the same keyword as `token` and `credential`. A
keyword buried inside a longer word is not a keyword, so `tokenizer`
and `authored` do not trigger the rule.

When a security keyword is detected:
1. Still spawn all 3 agents to gather perspectives. `parse-consensus-categories` already returns all 3 for these keywords, so dispatching exactly what it returns satisfies this step
2. Pass the helper's `security_route` to the synthesizer as its `Security Route` line
3. When every routed analyst returns `security_relevant: false`, the keyword was used in another sense (for example `tokens` counting LLM usage), so apply the ordinary agreement rule for the item: a 2/3 majority applies at N = 3
4. An explicit `[security]` tag, or, on a keyword route, any analyst returning `security_relevant: true`, keeps unanimity: when all 3 agree, apply the answer like any other item and continue. A keyword alone never stops autopilot
5. When a unanimity item's analysts do not all agree, flag `[ROUND_3_TIEBREAK]` and run the [Round 3 Tiebreak](#round-3-tiebreak) on all 3 answers
6. Continue the run with the Round 3 result

## Round 3 Tiebreak

Consensus that cannot agree is resolved by agents, never by a question or a
stop. A synthesizer result flagged `[ROUND_3_TIEBREAK]` is the Round 3
trigger; it asks no human. Three situations raise it:

- all three analysts disagreeing, in Round 1 or after a Round 2 retry,
- a security item without 3/3 agreement, and
- an analyst that fails or escapes its retry and whose fresh replacement
  also fails or escapes (see below).

The parent orchestrator, never an executor, analyst, or synthesizer, runs
Round 3 after the batch's other edits are applied. An interactive run and an
unattended run behave the same: the parent asks no question and stops nowhere.

**Round 3 dispatch.** Two agents, in two waves:

1. Wave one: dispatch one fresh `spec-context-analyst` (Claude Code
   `speckit-pro:spec-context-analyst`; Codex
   `spawn_agent(agent_type="spec-context-analyst", ...)`), a new instance with
   no memory of the earlier rounds. Its prompt carries the item, all prior
   analyst answers, the constitution, and the technical roadmap, and asks for
   the single most conservative option that satisfies the spec.
2. Wave two, after that analyst returns: dispatch a `consensus-tiebreaker` at
   max effort (Claude Code `speckit-pro:consensus-tiebreaker`; Codex
   `spawn_agent(agent_type="consensus-tiebreaker", ...)`; omitting `agent_type`
   is a failed dispatch). The agent ships pinned at max (Claude Code
   `effort: max`, Codex `model_reasoning_effort = "max"`) with the
   synthesizer's read-only tool set, while `consensus-synthesizer` keeps its
   default effort for Rounds 1 and 2. Its prompt sets `**Round:** 3` and
   carries every earlier analyst response plus the fresh analyst's response
   as `**Tiebreak Analyst Response:**`. Round 3 uses no other synthesizer, and
   the parent never performs this synthesis itself.

The tiebreaker returns the most conservative option that satisfies the spec
among the supplied positions, with the Artifact Edit, an `**Assumption:**` line,
and every position it did not choose under `**Dissent:**`. Round 3 never
returns `[ROUND_3_TIEBREAK]` or `[ESCAPE_TO_ROUND_2]`.

**Apply and record.** Apply the edit exactly as an accepted consensus answer.
Then:

- Write the Consensus Resolution Log row with Outcome `[ROUND 3]` and a
  Resolution cell of `assumption: <chosen option>; dissent: <positions not
  chosen>`. A Clarify item also records the answer in Clarify Results,
  labeled as an assumption.
- The choice is recorded as an assumption and the dissent is logged in that
  row. Both go to `pr-packet-output` as `known_gaps`, one line per Round 3
  item naming the item, the assumption, and the dissent, so the PR body lists
  them under `## Known Gaps`.

An analyst that fails or escapes its retry is replaced by a fresh analyst, never by a
human: dispatch one new instance of the same perspective with the same prompt.
If it returns a valid answer without escape keywords, the item continues under
the ordinary rules with that answer.
If the replacement fails or escapes, raise the flag and run Round 3 on the answers in
hand.

**Product scope is the one deferral.** When the tiebreaker finds that the
choice changes product scope the spec and the roadmap do not settle, it adds
`[SCOPE_DEFERRED] <reason>` to a result that still carries the most
conservative (narrowest) edit. Apply that edit provisionally so gates keep
passing, log the row as `[ROUND 3]` with `scope deferred` in the Resolution
cell, and add a record to the `unresolved_deferrals` input of `finalize-run`
so the item appears in the one end-of-run consolidated request. That deferral
is never a mid-run stop and never a question; nothing else in consensus
defers.

Never ask through free text or `grill-me`, and never wait on a question no one
can answer.

The pull-request feedback sweep runs its own isolated Round 3 through a fresh
`sweep-analyst`; see the sweep section of
[phase-execution.md](./phase-execution.md). This section covers Clarify,
Checklist, and Analyze consensus.

## Phase-Specific Consensus Flows

Each flow follows the same pattern: executor handles Layer 1,
main session handles Layer 2 (consensus) for unresolved items.

> **Note on the diagrams below.** Security items start Round 1 with
> all three analysts; Round 2 retries only failed or escaped analysts. A
> `low_confidence` item spawns the one analyst
> `parse-consensus-categories` returns and no synthesizer. The
> synthesizer runs only for `security` items — see
> "Plan-Stage Tiers" above for the routing rules.

### Clarify Consensus

```
clarify-executor prepares read-only Clarify Question Set
    │
    ├── Layer 1: Executor researches questions and recommendations
    │   using capability-first discovery per capability-discovery.md
    │
    ├── Executor returns summary with:
    │   ├── Questions for parent (with recommendations and citations)
    │   └── "Unresolved for consensus" section
    │
    ├── Parent orchestrator answers questions and applies accepted edits
    │
    └── Main session Layer 2 (BATCHED across all unresolved items —
        see §Batched Dispatch above for the canonical 3-stage flow):
        │
        ├── Stage 1: spawn all routed analysts for all items in ONE
        │   assistant message (background). Per-item routing comes
        │   from parse-consensus-categories (Category-Routed Dispatch).
        │   Recommendation items finish with the executor answer;
        │   low_confidence items finish via answer_source and the decisions list.
        │
        ├── Stage 2: spawn all consensus-synthesizers in ONE message
        │   (one synthesizer per security item).
        │
        ├── Stage 3: apply Artifact Edits SERIALLY in item order:
        │   ├── Security tier → follow Consensus Rules; otherwise Round 3 tiebreak
        │   ├── Accepted consensus
        │   │   → Edit spec.md with the consensus answer, remove marker
        │   ├── [ESCAPE_TO_ROUND_2] → enqueue for Round 2 batch
        │   └── All disagree → [ROUND_3_TIEBREAK] → Round 3 tiebreak
```

The diagram above is per-item educational. The actual dispatch is
**batched across N items per Phase 2 invocation** — see
§Batched Dispatch for stages, await semantics, and failure modes.

**Prompt template for consensus agents during Clarify:**

```
You are participating in a consensus resolution for a SpecKit
clarification question that the executor could not resolve
with high confidence.

## Specification Context
[Insert relevant spec.md excerpt]

## Question
[Insert the clarify question]

## Executor's Attempt
[Insert the executor's answer and why it was flagged —
low confidence or security keyword]

## Your Task
Propose the best answer to this question from your
perspective. Be specific and actionable. If you agree with
the executor's answer, say so and explain why from your
perspective. If you disagree, explain why and propose an
alternative.

Follow your agent instructions for output format
(Answer, Evidence/References/Citations, Confidence).

Reference dir: <plugin_root>/skills/speckit-autopilot/references/
```

### Checklist Gap Consensus

```
checklist-executor runs /speckit-checklist domain
    │
    ├── Layer 1: Executor runs checklist, researches each gap,
    │   applies fixes, re-runs once to verify
    │
    ├── Executor returns summary with:
    │   ├── Gaps fixed (with citations)
    │   └── "Unresolved for consensus" section
    │
    └── Main session Layer 2 (BATCHED across all unresolved gaps —
        see §Batched Dispatch above for the canonical 3-stage flow):
        │
        ├── Stage 1: spawn all routed analysts for all gaps in ONE
        │   message (background). Per-gap routing from parse-consensus-categories.
        │   Recommendation gaps finish with the executor answer;
        │   low_confidence gaps finish via answer_source and the decisions list.
        │
        ├── Stage 2: spawn all consensus-synthesizers in ONE message
        │   (one synthesizer per security gap).
        │
        ├── Stage 3: apply Artifact Edits SERIALLY in gap order:
        │   ├── Security tier → follow Consensus Rules; otherwise Round 3 tiebreak
        │   ├── Accepted consensus
        │   │   → Apply edit to spec.md or plan.md, log to workflow
        │   ├── [ESCAPE_TO_ROUND_2] → enqueue for Round 2 batch
        │   └── All disagree → [ROUND_3_TIEBREAK] → Round 3 tiebreak
```

The diagram above is per-gap educational. Actual dispatch is
**batched across N gaps from the whole checklist domain wave** — see §Batched Dispatch.

**Prompt template for consensus agents during Gap Remediation:**

```
You are participating in a consensus resolution for a SpecKit
checklist gap that the executor could not resolve with high
confidence.

## Specification Context
[Insert relevant spec.md and plan.md excerpts]

## Gap Description
[Insert the [Gap] marker text and surrounding checklist context]

## Executor's Attempt
[Insert what the executor tried, if anything, and why it
was flagged — low confidence or security keyword]

## Your Task
Propose how to close this gap. Specifically:
1. Which artifact should be edited? (spec.md, plan.md, or both)
2. What exact text should be added or modified?
3. Where in the artifact should the edit go? (section name)

Follow your agent instructions for output format.

Reference dir: <plugin_root>/skills/speckit-autopilot/references/
```

### Analyze Finding Consensus

```
analyze-executor runs /speckit-analyze
    │
    ├── Layer 1: Executor runs analysis, researches each finding,
    │   applies fixes, re-runs once to verify
    │
    ├── Executor returns summary with:
    │   ├── Findings fixed (with citations)
    │   └── "Unresolved for consensus" section
    │
    └── Main session Layer 2 (BATCHED across all unresolved findings —
        see §Batched Dispatch above for the canonical 3-stage flow):
        │
        ├── Stage 1: spawn all routed analysts for all findings in ONE
        │   message (background). Per-finding routing from parse-consensus-categories.
        │   Recommendation findings finish with the executor answer;
        │   low_confidence findings finish via answer_source and the decisions list.
        │
        ├── Stage 2: spawn all consensus-synthesizers in ONE message
        │   (one synthesizer per security finding).
        │
        ├── Stage 3: apply Artifact Edits SERIALLY in finding order:
        │   ├── Security tier → follow Consensus Rules; otherwise Round 3 tiebreak
        │   ├── Accepted consensus
        │   │   → Apply fix to tasks.md / spec.md / plan.md, log to workflow
        │   ├── [ESCAPE_TO_ROUND_2] → enqueue for Round 2 batch
        │   └── All disagree → [ROUND_3_TIEBREAK] → Round 3 tiebreak
```

The diagram above is per-finding educational. Actual dispatch is
**batched across N findings per Phase 6 invocation** — see §Batched Dispatch.

**Prompt template for consensus agents during Finding Remediation:**

```
You are participating in a consensus resolution for a SpecKit
analysis finding that the executor could not resolve with high
confidence.

## Artifact Context
[Insert relevant excerpts from spec.md, plan.md, and tasks.md]

## Finding
Severity: [CRITICAL/HIGH/MEDIUM/LOW]
Description: [Insert finding text]

## Executor's Attempt
[Insert what the executor tried, if anything, and why it
was flagged — low confidence or security keyword]

## Your Task
Propose how to fix this finding. Specifically:
1. Which artifact(s) should be edited? (tasks.md, spec.md, plan.md)
2. What exact changes should be made?
3. Does this fix introduce any new concerns?

Follow your agent instructions for output format.

Reference dir: <plugin_root>/skills/speckit-autopilot/references/
```

### Pre-Implement Confidence Emit (end of Phase 6 Analyze)

After all finding-remediation consensus rounds for Phase 6 are
applied (or immediately, on a clean Analyze pass with zero
unresolved findings), the **consensus-synthesizer emits a final
"Pre-Implement Confidence" block** to the workflow log. This is
the data source for the optional Confidence Gate (G6.5) that runs
between Phase 6 and Phase 7. The same emit fires whether the
gate is configured advisory or strict — the gate is opt-in;
the emit is not.

The parent performs one dedicated final Analyze dispatch to the named
consensus-synthesizer after remediation, even when there were zero findings.
It validates that the returned block has all five criterion lines, then
persists that block exactly once for the current Analyze pass. A missing,
failed, malformed, or duplicate confidence block does not complete Analyze and
cannot be reconstructed by the parent. This dispatch, and the G6.5 re-emit,
carry no consensus item: the synthesizer returns the block alone, no
`Consensus Result` and no `Artifact Edit`, and the parent applies nothing from
it.

**Format (canonical, regex-parseable):**

```text
📊 Confidence: 0.92

- Task understanding: 0.95
- Approach clarity: 0.90
- Requirements alignment: 0.92
- Risk assessment: 0.88
- Completeness: 0.95
```

The five criterion lines are the canonical signal. The
`confidence-gate` helper parses them with
`^- <Label>: ([01]\.[0-9]{2})$` and computes the composite
itself: the arithmetic mean of the five, rounded to two
decimals, then 0.30 off for each open `CRITICAL` and 0.10 off
for each open `HIGH` finding, floored at 0.00. It reads those
findings from the most recent Analysis Results table in the
workflow file (`| ID | Severity | Issue | Resolution |`), and a
row counts as open only while its `Resolution` cell is empty.
That table is the one place the log records a finding with an
open-or-closed discriminator. Bare `[CRITICAL]` and `[HIGH]`
text in the body cannot serve: the log is append-only, so the
same bracket text appears in findings the run already
remediated and in prose asserting zero markers. A log whose
latest table has no unresolved `CRITICAL` or `HIGH` row takes
no deduction.

The first line is a courtesy for human readers. The helper
matches it with `^📊 Confidence: ([01]\.[0-9]{2})$` and falls
back to it only when the five criterion lines are absent. When
both are present and the stated number disagrees with the
criterion mean, the helper reports the computed composite and
names the disagreement in its `reason`. A stated number that
matches the mean but not the post-deduction composite is not a
disagreement. The JSON records which
source it used in `composite_source`, the pre-deduction mean in
`criteria_mean`, and the deduction in `deductions`.

**The five criteria (each 0.00–1.00):**

| Criterion | What it scores |
|-----------|----------------|
| Task understanding | Does `spec.md` convey what's being built clearly enough that a competent engineer could begin implementing without further questions? Penalize ambiguity in user stories and acceptance criteria. |
| Approach clarity | Does `plan.md` lay out a coherent implementation strategy — chosen libraries, data model, contract surface — without unresolved decisions? Penalize "TBD" markers and design holes. |
| Requirements alignment | Do `tasks.md` items trace back to specific requirements in `spec.md`? Penalize tasks without a clear "this implements requirement X" mapping. |
| Risk assessment | How well are the residual risks in this feature understood and bounded: unknowns named, mitigations planned, blast radius stated? Score the judgment only. Do not deduct for open `CRITICAL` or `HIGH` findings here — the helper applies those deductions to the composite, so deducting twice would double-count them. |
| Completeness | Are all expected artifacts present and non-empty: `spec.md`, `plan.md`, `tasks.md`, `data-model.md` (if planned), `contracts/` (if planned)? Penalize missing or empty artifacts. |

The synthesizer emits this block exactly once per Phase 6 invocation,
on its own line(s) in the workflow log, immediately after the
"Consensus Resolution Log" table (or after the "No findings"
notice, if the executor's Analyze pass was clean). If multiple
Analyze passes occur within a single autopilot run (e.g., the
confidence gate triggered remediation and re-invoked Phase 6),
each pass emits its own block; the gate script reads the most
recent one.

**Why the helper does the arithmetic:** the gate is meant to be
cheap and deterministic, and an agent's stated aggregate is
neither. Scoring five dimensions is judgment, which is the
synthesizer's job; averaging them and subtracting for open
findings is arithmetic, which code does the same way every run.
The breakdown still serves human reviewers and remediation
prompts — it tells you *which* dimension is low so the
iteration loop knows what to fix.

**Synthesizer prompt addition:** the consensus-synthesizer's
agent body must include this directive verbatim:

> At the very end of every Phase 6 Analyze synthesis (whether
> findings were resolved or the pass was clean), emit a block in
> the exact format above. Score each criterion against the
> rubric. The first line is a courtesy; the confidence-gate
> helper recomputes the composite from your five criterion
> lines. Do not omit this block — the downstream Confidence
> Gate depends on it.

## Determining Agreement

Two agents "agree" when their proposed answers converge on the same approach, even if worded differently. Evaluate agreement based on:

1. **Same conclusion** — both recommend the same action (add task, edit spec section, use specific API)
2. **Compatible evidence** — evidence from different sources pointing to the same answer
3. **No contradiction** — answers don't conflict in their recommendations

Two agents "disagree" when:
1. **Different conclusions** — they recommend incompatible actions
2. **Contradictory evidence** — their evidence points in different directions
3. **Different scope** — one says "add to spec" while another says "not needed"

When evaluating agreement, consider the **substance** of the answer, not the exact wording. A codebase-analyst saying "use the existing BatchResult pattern" and a spec-context-analyst saying "follow the Phase 5 batch pattern" are agreeing if they point to the same pattern.

## Logging

After each consensus resolution, log the result in the workflow
file. The `Round` and `Categories` columns are required so the
re-evaluation trigger (10% Round-2 escape rate) is computable
from the log alone.

```markdown
### Consensus Resolution Log

| # | Type    | Question/Gap/Finding         | Categories         | Round | Outcome        | Resolution                 | Analysts Used                          |
|---|---------|------------------------------|--------------------|-------|----------------|----------------------------|----------------------------------------|
| 1 | Clarify | Session token format?        | [security]         | 1     | 3/3            | JWT with 24h expiry        | codebase-analyst, spec-context-analyst, domain-researcher |
| 2 | Gap     | Token budget per request     | [domain]           | 1     | 2/3            | Added to spec §4.2         | All (keyword `token`; every analyst `security_relevant: false`) |
| 3 | Finding | Password reset rate limit    | [codebase]         | 2     | 3/3            | Added task T050            | All (keyword `password`); domain-researcher failed in Round 1 and answered on its Round 2 retry |
| 4 | Clarify | Bcrypt vs argon2?            | [security]         | 1→2   | escape-hatch   | Argon2 (NIST SP 800-63B)   | All; codebase-analyst escaped in Round 1 and answered on its Round 2 retry |
| 5 | Finding | OAuth callback URL handling  | [security]         | 1→3   | [ROUND 3]      | assumption: reject unknown callback URLs; dissent: allow-list per tenant | All (security tag → all-3; not unanimous) + fresh spec-context-analyst |
```

**`Type` values:** `Clarify`, `Gap`, and `Finding` name the phase that produced
the item. `Sweep` names the pull-request feedback sweep, which writes one row
per amended item. A `Sweep` row's item cell names the comment id, and the
Feedback Sweep Log row's `CRL #` names this row's number, so the link runs both
ways at no extra column. On the scope-deferred path the sweep writes this row and
no Feedback Sweep Log row, so the link degrades to one direction, by design.

**Sweep rows count toward the Round-2 escape-rate metric.** They are produced by
the same round structure and the same agreement rule and can escape the same
way, so excluding them would blind the 10% trigger precisely where the input is
least controlled. Inclusion costs no attribution: the `Type` column is itself
the source discriminator, so a breach of the threshold can be attributed to
sweep rows or to phase rows without either being excluded from the rate.

**Outcome values:**
- `3/3`, `2/3` — the three-analyst agreement count, in Round 1 or after a Round 2 retry (a 2/3 row is a keyword-only item whose analysts all returned `security_relevant: false`)
- `escape-hatch` — an analyst escaped in Round 1 and was retried in Round 2 (count this in the 10% trigger metric)
- `[ROUND 3]` — the item took the Round 3 tiebreak (all three disagree, a security item without 3/3, or a failed analyst). The Resolution cell reads `assumption: <chosen option>; dissent: <positions not chosen>`, or adds `scope deferred` when the synthesizer flagged `[SCOPE_DEFERRED]`. Count it in the 10% trigger metric like an escape
