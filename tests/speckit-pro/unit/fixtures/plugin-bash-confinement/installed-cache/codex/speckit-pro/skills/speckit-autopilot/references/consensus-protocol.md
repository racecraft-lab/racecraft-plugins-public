# Consensus Protocol Reference

The consensus protocol is the second layer of the autopilot's
two-layer resolution system, used by 3 phases: Clarify,
Checklist, and Analyze.

Consensus dispatch runs as batched ordinary subagents; see
[agent-teams-integration.md](./agent-teams-integration.md) use site 5.

## Contents

- [Two-Layer Resolution Architecture](#two-layer-resolution-architecture) — executor first-pass then consensus second-pass
- [Category-Routed Dispatch (Tier A)](#category-routed-dispatch-tier-a) — `[codebase|spec|domain|security|ambiguous]` routing rules + escape-hatch
- [Batched Dispatch](#batched-dispatch) — multi-item fan-out in ONE tool turn (the canonical WS-D1 pattern)
- [Three-Analyst Consensus Rules (Round 2 / N=3)](#three-analyst-consensus-rules-round-2--n3) — full fan-out behavior
- [The 3 Perspective Agents](#the-3-perspective-agents) — codebase-analyst / spec-context-analyst / domain-researcher
- [Consensus Rules](#consensus-rules) — N=1, N=2, N=3 agreement rules + escape-hatch + STOP conditions
- [Security Keywords](#security-keywords) — always-all-3 trigger words
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
artifacts. Items it can't resolve with high confidence are
flagged in its "Unresolved for consensus" summary section,
with a category prefix (see "Category-Routed Dispatch" below).

**Layer 2 — Consensus agents (second pass):** The main
session (not the executor) routes each unresolved item to the
relevant analyst(s) based on the executor's category prefix.
Single-analyst paths apply when one perspective is sufficient;
all-three paths apply for security keywords, untagged items,
multi-perspective tags spanning all categories, or when the
single-analyst path returns low confidence.

**Why two layers:** Single-agent research handles
straightforward items efficiently. Category-routed consensus
spends model effort only on the perspective(s) the executor
identified as relevant, with a defense-in-depth fallback to
all-three for ambiguous, security-sensitive, or low-confidence
items.

**When consensus is triggered:**
- Executor flagged the item as low-confidence
- Executor's research sources disagreed
- Item remained unresolved after 2 remediation loops
- Item contains security keywords (always goes to all-three consensus)

## Category-Routed Dispatch (Tier A)

Each item in the executor's "Unresolved for consensus" section
MUST carry a category prefix. The orchestrator calls the
`parse-consensus-categories` runner helper on the item line and
dispatches exactly the analysts it returns. The table below states
what that helper implements; it is not a procedure to run by hand.

### Category tags

| Tag | Meaning | Routes to |
|-----|---------|-----------|
| `[codebase]` | Resolution depends on existing patterns/conventions in this repo's code | `speckit-pro:codebase-analyst` only |
| `[spec]` | Resolution depends on project decisions in spec/plan/constitution/roadmap | `speckit-pro:spec-context-analyst` only |
| `[domain]` | Resolution depends on external standards, RFCs, library docs, or community best practice | `speckit-pro:domain-researcher` only |
| `[security]` | Item contains a security keyword (see [Security Keywords](#security-keywords)) | All 3 (defense-in-depth, never single-routed) |
| `[ambiguous]` | Executor uncertain which perspective applies | All 3 (safe default) |
| *(missing/unparseable prefix)* | Treated as `[ambiguous]` | All 3 (safe default) |

**Multi-category tags** are valid: `[codebase, domain]` dispatches
both `speckit-pro:codebase-analyst` and `speckit-pro:domain-researcher`.
`parse-consensus-categories` reads the comma-separated category list
inside the bracket and returns that union.

### Two-round protocol with escape hatch

```text
ROUND 1 — category-routed
  Call parse-consensus-categories on the unresolved item line.
  Spawn exactly the N analysts (1 ≤ N ≤ 3) it returns.
  consensus-synthesizer always runs (becomes "edit-applier" in 1-analyst case).

  IF synthesizer flags confidence: high
     AND no analyst response contains escape-hatch keywords
     ("insufficient context", "not in this codebase", "no precedent",
      "outside my scope", "cannot answer from this perspective"):
       APPLY edit, log result, done.

  ELSE (low confidence OR escape-hatch keyword detected):
       fall through to ROUND 2.

ROUND 2 — full fan-out
  Spawn the remaining (3 - N) analysts.
  Re-invoke consensus-synthesizer with all 3 responses.
  Apply the multi-analyst rules below.
  APPLY edit OR flag [HUMAN REVIEW NEEDED].
```

The escape hatch is the asymmetry that keeps routing cheap when
right and safe when wrong. A `[codebase]` tag that should have
been `[domain]` triggers Round 2 the moment `speckit-pro:codebase-analyst`
admits "no precedent in this repo" — no silently-shipped
low-confidence answers.

### Single-analyst confidence rule (N=1)

When only one analyst ran in Round 1, the synthesizer's output
includes a `confidence: high | low` field instead of an
agreement count.

| Synthesizer output | Action |
|--------------------|--------|
| `confidence: high` AND no escape-hatch keyword | Apply edit, log, done |
| `confidence: low` | Fall through to Round 2 |
| Escape-hatch keyword in analyst response | Fall through to Round 2 |

### Two-analyst rule (N=2)

| Analysts | Action |
|----------|--------|
| Both agree | Apply edit, log, done |
| Disagree | Fall through to Round 2 (spawn the missing analyst, re-synthesize) |
| Either flagged escape-hatch | Fall through to Round 2 |

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
| `parse-consensus-categories` | Reads one unresolved-item line and returns `tags`, the `analysts` to spawn, and the dispatch `reason`. Implements every routing rule in the table above: security override, ambiguous safe default, unknown-tag safe default, multi-tag union, untagged → all 3. It reads the whole line, not just the bracket, so a [Security Keyword](#security-keywords) anywhere in the item text widens to all 3 even when the executor tagged the item narrowly. |
| `aggregate-crl` | Reads the Consensus Resolution Log table out of a workflow file and returns `total_items`, `round1`, `round2`, `escape_hatch`, `escape_rate_percent`, the `threshold_percent` it was given (default 10), and `exceeds_threshold`. |

**Call `parse-consensus-categories` for every unresolved item and
dispatch exactly the analysts it returns.** Do not route by reading
the table yourself. The helper is the only place the widening rules
run: a tag it does not recognize widens to all three analysts rather
than narrowing to a guess, and so does a security keyword in the item
text, whatever the executor put in the bracket.

```text
resolved_python -m speckit_pro_runner < request.json

request.json:
{
  "schema_version": "1.0",
  "request_id": "consensus-route-I1",
  "helper_id": "parse-consensus-categories",
  "operation": "parse-consensus-categories",
  "mode": "read_only",
  "inputs": { "line": "[codebase, domain] Q3: bcrypt or argon2?" }
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
fan-out across items**, not per-item serially. This is the canonical
WS-D1 pattern and applies to every per-phase consensus invocation.

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
Stage 1 — All routed analysts, ONE assistant message:
  For each unresolved item Ix (x = 1..N):
    Call parse-consensus-categories on the item line → analyst set Sx
    For each analyst a in Sx:
      Agent(subagent_type: <a>,
            run_in_background: true,
            description: "SPEC-XXX consensus R1 [I<x>]: <item>",
            prompt: <consensus prompt for item Ix from a's perspective>)
  Total dispatches in one message: Σ |Sx|
  ↓
  Await ALL spawned analysts to complete.

Stage 2 — All synthesizers, ONE assistant message:
  For each item Ix:
    Agent(subagent_type: "speckit-pro:consensus-synthesizer",
          run_in_background: true,
          description: "SPEC-XXX consensus synthesis (R1) [I<x>]",
          prompt: """
            ## Consensus Resolution
            **Unresolved Item:** <item Ix text>
            **Routed Categories:** [<categories from prefix>]
            **Round:** 1
            **<Analyst> Response:** <response> | NOT SPAWNED (not routed)
            ... (one row per analyst, NOT SPAWNED if not in Sx)
          """)
  Total dispatches in one message: N
  ↓
  Await ALL synthesizers.

Stage 3 — Apply Artifact Edits SERIALLY (orchestrator's own Edit calls):
  ROUND_2_QUEUE = []
  For each synthesizer result, in item order:
    IF Flags = None AND (Confidence = high OR 2-of-3 OR 3-of-3 agree):
      Apply Artifact Edit to spec.md / plan.md / tasks.md
      Write a CRL row: Round=1, Routed Categories=Sx, Outcome=<outcome>, Analysts Used=Sx
    IF Flags includes [ESCAPE_TO_ROUND_2] OR low confidence:
      Push (Ix, Sx) onto ROUND_2_QUEUE
    IF Flags includes [HUMAN REVIEW NEEDED]:
      Write CRL row with Outcome=human-review, STOP autopilot after this batch

If ROUND_2_QUEUE non-empty:
  Stage 4 — All Round-2 analysts (the remaining (3 − |Sx|) per queued item) in ONE message
  Stage 5 — All Round-2 synthesizers in ONE message
  Stage 6 — Apply Round-2 edits serially (same as Stage 3); HUMAN REVIEW STOPs.
```

### What stays serial — and why

Stage 3 / Stage 6 (Artifact Edit application) MUST be serial. The
`Edit` tool modifies spec.md / plan.md / tasks.md; concurrent edits
to the same file via concurrent Edit calls race. Each Edit is
~50-200ms, so serial application across N items costs only a few
seconds — negligible compared to the LLM-bound Stages 1/2/4/5.

### Concurrency observations

- 5 items × 2-3 routed analysts = 10-15 background subagents in
  ONE turn.
- If a future use site approaches the platform limit, partition the
  batch into waves of ≤10 per turn and chain them via additional
  Stage 1' / Stage 2' rounds. The shipped implementation does not
  partition by default — single-batch dispatch is the default.

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
re-queued for a single retry. If retry also fails, surface to user
via `[HUMAN REVIEW NEEDED]` for that item — do NOT block the rest of
the batch.

## Three-Analyst Consensus Rules (Round 2 / N=3)

## The 3 Perspective Agents

| Agent | Perspective | Primary Tools | Strength |
|-------|------------|---------------|----------|
| `speckit-pro:codebase-analyst` | What does the existing code show? | codebase context capability selected through [capability-discovery.md](./capability-discovery.md) | Finding established patterns, types, naming conventions, error handling |
| `speckit-pro:spec-context-analyst` | What do project decisions say? | Read (constitution, technical roadmap, prior specs, CLAUDE.md) | Grounding answers in established principles and prior decisions |
| `speckit-pro:domain-researcher` | What do best practices recommend? | web or domain research, library documentation, or source extraction capability selected through [capability-discovery.md](./capability-discovery.md) | External evidence — API docs, standards, community patterns |

## Consensus Rules

### Moderate Mode (Default)

| Scenario | Action |
|----------|--------|
| **2/3 agree** | Use the majority answer. Log the dissenting perspective for context. |
| **3/3 agree** | Use the answer with high confidence. |
| **All 3 disagree** | Flag as `[HUMAN REVIEW NEEDED]` with all 3 perspectives. STOP autopilot. |
| **Security/data-integrity keyword detected** | Always flag for human regardless of consensus. |

### Conservative Mode

Same as moderate, but:
- Requires 3/3 agreement for auto-answer
- 2/3 agreement flags for human with recommendation
- Any disagreement stops for human review

### Aggressive Mode

Same as moderate, but:
- 2/3 agreement auto-answers (same as moderate)
- Even all-disagree attempts to synthesize best answer and proceed
- Only security keywords stop for human review

## Security Keywords

These keywords in the question, gap, or finding text trigger **mandatory human review** regardless of consensus mode:

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
2. Present all 3 answers to the human
3. Let the human decide which answer to use
4. Resume autopilot after human decision

## Phase-Specific Consensus Flows

Each flow follows the same pattern: executor handles Layer 1,
main session handles Layer 2 (consensus) for unresolved items.

> **Note on the diagrams below.** They depict the **Round 2**
> (full fan-out) path that fires after a Round 1 escape, or
> directly when an item is tagged `[security]`, `[ambiguous]`,
> or untagged. Round 1 follows the same shape but spawns only
> the analyst(s) `parse-consensus-categories` returns for the
> item (1 ≤ N ≤ 3).
> Both rounds invoke `consensus-synthesizer` with whichever
> analyst responses ran — see "Category-Routed Dispatch" above
> for the routing rules.

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
        │
        ├── Stage 2: spawn all consensus-synthesizers in ONE message
        │   (one synthesizer per item).
        │
        ├── Stage 3: apply Artifact Edits SERIALLY in item order:
        │   ├── Check for security keywords → if found, flag for human
        │   ├── N=1 high-confidence | N=2 both-agree | N=3 2/3 or 3/3 agree
        │   │   → Edit spec.md with the consensus answer, remove marker
        │   ├── [ESCAPE_TO_ROUND_2] → enqueue for Round 2 batch
        │   └── All disagree (after Round 2) → [HUMAN REVIEW NEEDED] + STOP
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
conflicting sources, low confidence, or security keyword]

## Your Task
Propose the best answer to this question from your
perspective. Be specific and actionable. If you agree with
the executor's answer, say so and explain why from your
perspective. If you disagree, explain why and propose an
alternative.

Follow your agent instructions for output format
(Answer, Evidence/References/Citations, Confidence).
```

### Checklist Gap Consensus

```
checklist-executor runs /speckit-checklist domain
    │
    ├── Layer 1: Executor runs checklist, researches each gap,
    │   applies fixes, re-runs to verify (max 2 loops)
    │
    ├── Executor returns summary with:
    │   ├── Gaps fixed (with citations)
    │   └── "Unresolved for consensus" section
    │
    └── Main session Layer 2 (BATCHED across all unresolved gaps —
        see §Batched Dispatch above for the canonical 3-stage flow):
        │
        ├── Stage 1: spawn all routed analysts for all gaps in ONE
        │   message (background). Per-gap routing per [<categories>].
        │
        ├── Stage 2: spawn all consensus-synthesizers in ONE message
        │   (one synthesizer per gap).
        │
        ├── Stage 3: apply Artifact Edits SERIALLY in gap order:
        │   ├── Security keyword → flag for human
        │   ├── N=1 high-confidence | N=2 both-agree | N=3 2/3 or 3/3 agree
        │   │   → Apply edit to spec.md or plan.md, log to workflow
        │   ├── [ESCAPE_TO_ROUND_2] → enqueue for Round 2 batch
        │   └── All disagree (after Round 2) → [HUMAN REVIEW NEEDED] + STOP
```

The diagram above is per-gap educational. Actual dispatch is
**batched across N gaps per checklist domain** — see §Batched Dispatch.

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
was flagged — remained after 2 loops, low confidence, or
security keyword]

## Your Task
Propose how to close this gap. Specifically:
1. Which artifact should be edited? (spec.md, plan.md, or both)
2. What exact text should be added or modified?
3. Where in the artifact should the edit go? (section name)

Follow your agent instructions for output format.
```

### Analyze Finding Consensus

```
analyze-executor runs /speckit-analyze
    │
    ├── Layer 1: Executor runs analysis, researches each finding,
    │   applies fixes, re-runs to verify (max 2 loops)
    │
    ├── Executor returns summary with:
    │   ├── Findings fixed (with citations)
    │   └── "Unresolved for consensus" section
    │
    └── Main session Layer 2 (BATCHED across all unresolved findings —
        see §Batched Dispatch above for the canonical 3-stage flow):
        │
        ├── Stage 1: spawn all routed analysts for all findings in ONE
        │   message (background). Per-finding routing per [<categories>].
        │
        ├── Stage 2: spawn all consensus-synthesizers in ONE message
        │   (one synthesizer per finding).
        │
        ├── Stage 3: apply Artifact Edits SERIALLY in finding order:
        │   ├── Security keyword → flag for human
        │   ├── N=1 high-confidence | N=2 both-agree | N=3 2/3 or 3/3 agree
        │   │   → Apply fix to tasks.md / spec.md / plan.md, log to workflow
        │   ├── [ESCAPE_TO_ROUND_2] → enqueue for Round 2 batch
        │   └── All disagree (after Round 2) → [HUMAN REVIEW NEEDED] + STOP
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
was flagged — remained after 2 loops, low confidence, or
security keyword]

## Your Task
Propose how to fix this finding. Specifically:
1. Which artifact(s) should be edited? (tasks.md, spec.md, plan.md)
2. What exact changes should be made?
3. Does this fix introduce any new concerns?

Follow your agent instructions for output format.
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
| 1 | Clarify | Session token format?        | [domain]           | 1     | high-confidence| JWT with 24h expiry        | domain-researcher                      |
| 2 | Gap     | Rate limit thresholds        | [codebase, domain] | 1     | both-agree     | Added to spec §4.2         | codebase-analyst, domain-researcher    |
| 3 | Finding | Missing integration tests    | [ambiguous]        | 2     | 3/3            | Added task T050            | codebase-analyst, spec-context-analyst, domain-researcher |
| 4 | Clarify | Bcrypt vs argon2?            | [codebase]         | 1→2   | escape-hatch   | Argon2 (NIST SP 800-63B)   | codebase-analyst (Round 1) + spec-context-analyst, domain-researcher (Round 2) |
| 5 | Finding | OAuth callback URL handling  | [security]         | 1     | [HUMAN REVIEW] | Surfaced to user           | All (security tag → all-3 mandatory)   |
```

**`Type` values:** `Clarify`, `Gap`, and `Finding` name the phase that produced
the item. `Sweep` names the pull-request feedback sweep, which writes one row
per amended item. A `Sweep` row's item cell names the comment id, and the
Feedback Sweep Log row's `CRL #` names this row's number, so the link runs both
ways at no extra column. On the human-review path the sweep writes this row and
no Feedback Sweep Log row, so the link degrades to one direction, by design.

**Sweep rows count toward the Round-2 escape-rate metric.** They are produced by
the same round structure and the same agreement rule and can escape the same
way, so excluding them would blind the 10% trigger precisely where the input is
least controlled. Inclusion costs no attribution: the `Type` column is itself
the source discriminator, so a breach of the threshold can be attributed to
sweep rows or to phase rows without either being excluded from the rate.

**Outcome values:**
- `high-confidence` — Round 1, single-analyst, synthesizer flagged high
- `both-agree` — Round 1, two-analyst, agreement
- `3/3`, `2/3` — Round 2, classic agreement counts
- `escape-hatch` — Round 1 escaped to Round 2 (count this in the 10% trigger metric)
- `[HUMAN REVIEW]` — Round 2 all-disagree, or a security flag (Round 1, all 3), autopilot stopped
