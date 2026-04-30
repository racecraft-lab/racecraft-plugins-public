# Consensus Protocol Reference

The consensus protocol is the second layer of the autopilot's
two-layer resolution system, used by 3 phases: Clarify,
Checklist, and Analyze.

## Two-Layer Resolution Architecture

**Layer 1 — Executor agent (first pass):** Each phase has a
specialized executor agent (clarify-executor,
checklist-executor, analyze-executor) that runs the
`/speckit.*` command AND does direct research using web search,
library docs, and codebase exploration (MCP tools when available,
built-in fallbacks otherwise). The executor
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

## Category-Routed Dispatch (Tier A, 2026-04-30)

Each item in the executor's "Unresolved for consensus" section
MUST carry a category prefix. The orchestrator parses the prefix
and dispatches to only the relevant analyst(s). This replaces
the legacy "always 3 analysts" rule.

### Category tags

| Tag | Meaning | Routes to |
|-----|---------|-----------|
| `[codebase]` | Resolution depends on existing patterns/conventions in this repo's code | `codebase-analyst` only |
| `[spec]` | Resolution depends on project decisions in spec/plan/constitution/roadmap | `spec-context-analyst` only |
| `[domain]` | Resolution depends on external standards, RFCs, library docs, or community best practice | `domain-researcher` only |
| `[security]` | Item contains security keywords (auth, token, secret, encryption, PII, credential, permission, password, session, cookie, jwt, api-key, access-control) | All 3 (defense-in-depth, never single-routed) |
| `[ambiguous]` | Executor uncertain which perspective applies | All 3 (safe default) |
| *(missing/unparseable prefix)* | Treated as `[ambiguous]` | All 3 (safe default) |

**Multi-category tags** are valid: `[codebase, domain]` dispatches
both `codebase-analyst` and `domain-researcher`. The orchestrator
parses comma-separated category lists inside the bracket and
spawns the union.

### Two-round protocol with escape hatch

```text
ROUND 1 — category-routed
  Parse the category prefix on the unresolved item.
  Spawn N analysts (1 ≤ N ≤ 3) per the routing table.
  consensus-synthesizer always runs (becomes "edit-applier" in 1-analyst case).

  IF synthesizer flags confidence: high
     AND no analyst response contains escape-hatch keywords
     ("insufficient context", "not in this codebase", "no precedent",
      "outside my scope", "cannot answer from this perspective"):
       APPLY edit, log result, done.

  ELSE (low confidence OR escape-hatch keyword detected):
       fall through to ROUND 2.

ROUND 2 — full fan-out (legacy path)
  Spawn the remaining (3 - N) analysts.
  Re-invoke consensus-synthesizer with all 3 responses.
  Apply the multi-analyst rules below.
  APPLY edit OR flag [HUMAN REVIEW NEEDED].
```

The escape hatch is the asymmetry that keeps routing cheap when
right and safe when wrong. A `[codebase]` tag that should have
been `[domain]` triggers Round 2 the moment `codebase-analyst`
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

These are the legacy multi-analyst rules, unchanged.

### Re-evaluation trigger

If the Round-2 escape-hatch rate exceeds **10%** of consensus
items across any 30-day window of autopilot runs, revert to
always-3 dispatch and treat category tags as advisory rather
than authoritative. The threshold is documented here; the
metric is tracked via the Consensus Resolution Log
(see "Logging" below — the `Round` column is the data source).

### Deterministic helpers

Two scripts under `skills/speckit-autopilot/scripts/` are the
single source of truth for the rules above. The orchestrator
prose mirrors them; if the prose drifts the Layer 4 tests catch
it.

| Script | Purpose |
|--------|---------|
| `parse-consensus-categories.sh "<line>"` | Parses the leading `[<categories>]` prefix, returns JSON listing the analysts to spawn and the dispatch reason. Implements every routing rule in the table above (security override, ambiguous safe default, unknown-tag safe default, multi-tag union, untagged → all 3). |
| `aggregate-crl.sh <workflow_file>` | Parses the Consensus Resolution Log table, computes total items / Round 1 / Round 2 / escape-hatch counts, returns escape-rate percent and `exceeds_threshold` boolean against `THRESHOLD_PERCENT` (default 10). |

The orchestrator MAY call these scripts directly during dispatch
or use them out-of-band for the 30-day review. Either way, they
define what "Tier A routing works" means in code, not prose.

## Three-Analyst Consensus Rules (Round 2 / N=3)

### Moderate Mode (Default)

## The 3 Perspective Agents

| Agent | Perspective | Primary Tools | Strength |
|-------|------------|---------------|----------|
| `codebase-analyst` | What does the existing code show? | RepoPrompt (preferred) or Grep/Glob/Read (fallback) | Finding established patterns, types, naming conventions, error handling |
| `spec-context-analyst` | What do project decisions say? | Read (constitution, technical roadmap, prior specs, CLAUDE.md) | Grounding answers in established principles and prior decisions |
| `domain-researcher` | What do best practices recommend? | Tavily/Context7 (preferred) or WebSearch/WebFetch (fallback) | External evidence — API docs, standards, community patterns |

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

When a security keyword is detected:
1. Still spawn all 3 agents to gather perspectives
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
> the analyst(s) named by the category prefix (1 ≤ N ≤ 3).
> Both rounds invoke `consensus-synthesizer` with whichever
> analyst responses ran — see "Category-Routed Dispatch" above
> for the routing rules.

### Clarify Consensus

```
clarify-executor runs /speckit.clarify session
    │
    ├── Layer 1: Executor researches and answers all questions
    │   using available research tools (MCP preferred, built-in fallbacks)
    │
    ├── Executor returns summary with:
    │   ├── Questions answered (with citations)
    │   └── "Unresolved for consensus" section
    │
    └── Main session Layer 2 (for each unresolved item):
        │
        ├── Spawn 3 agents IN PARALLEL (background):
        │   ├── codebase-analyst: "Given this spec and question, what's the right answer?"
        │   ├── spec-context-analyst: "Given this spec and question, what's the right answer?"
        │   └── domain-researcher: "Given this spec and question, what's the right answer?"
        │
        ├── Wait for all 3 to complete
        │
        ├── Compare answers:
        │   ├── Check for security keywords → if found, flag for human
        │   ├── 2/3 or 3/3 agree → use consensus answer
        │   └── All disagree → flag for human
        │
        ├── If consensus reached:
        │   └── Edit spec.md with the consensus answer, remove marker
        │
        └── If no consensus:
            └── Flag as [HUMAN REVIEW NEEDED] in workflow file, STOP
```

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
checklist-executor runs /speckit.checklist domain
    │
    ├── Layer 1: Executor runs checklist, researches each gap,
    │   applies fixes, re-runs to verify (max 2 loops)
    │
    ├── Executor returns summary with:
    │   ├── Gaps fixed (with citations)
    │   └── "Unresolved for consensus" section
    │
    └── Main session Layer 2 (for each unresolved gap):
        │
        ├── Spawn 3 agents IN PARALLEL (background):
        │   ├── codebase-analyst: "How should we close this gap?"
        │   ├── spec-context-analyst: "How should we close this gap?"
        │   └── domain-researcher: "How should we close this gap?"
        │
        ├── Wait for all 3 to complete
        │
        ├── Compare proposed edits:
        │   ├── Check for security keywords → if found, flag for human
        │   ├── 2/3 or 3/3 agree → apply consensus edit
        │   └── All disagree → flag for human
        │
        ├── If consensus reached:
        │   ├── Apply the edit to spec.md or plan.md
        │   └── Log the edit in the workflow file
        │
        └── If no consensus:
            └── Flag as [HUMAN REVIEW NEEDED] in workflow file, STOP
```

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
analyze-executor runs /speckit.analyze
    │
    ├── Layer 1: Executor runs analysis, researches each finding,
    │   applies fixes, re-runs to verify (max 2 loops)
    │
    ├── Executor returns summary with:
    │   ├── Findings fixed (with citations)
    │   └── "Unresolved for consensus" section
    │
    └── Main session Layer 2 (for each unresolved finding):
        │
        ├── Spawn 3 agents IN PARALLEL (background):
        │   ├── codebase-analyst: "How should we fix this finding?"
        │   ├── spec-context-analyst: "How should we fix this finding?"
        │   └── domain-researcher: "How should we fix this finding?"
        │
        ├── Wait for all 3 to complete
        │
        ├── Compare proposed fixes:
        │   ├── Check for security keywords → if found, flag for human
        │   ├── 2/3 or 3/3 agree → apply fix
        │   └── All disagree → flag for human
        │
        ├── If consensus reached:
        │   ├── Apply the fix to tasks.md, spec.md, or plan.md
        │   └── Log the fix in the workflow file
        │
        └── If no consensus:
            └── Flag as [HUMAN REVIEW NEEDED] in workflow file, STOP
```

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
| 5 | Finding | OAuth callback URL handling  | [security]         | 2     | [HUMAN REVIEW] | Surfaced to user           | All (security tag → all-3 mandatory)   |
```

**Outcome values:**
- `high-confidence` — Round 1, single-analyst, synthesizer flagged high
- `both-agree` — Round 1, two-analyst, agreement
- `3/3`, `2/3` — Round 2, classic agreement counts
- `escape-hatch` — Round 1 escaped to Round 2 (count this in the 10% trigger metric)
- `[HUMAN REVIEW]` — Round 2 all-disagree or security flag, autopilot stopped
