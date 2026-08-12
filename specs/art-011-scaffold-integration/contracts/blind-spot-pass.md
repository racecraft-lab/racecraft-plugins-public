# Contract: Blind-Spot Pass

**Documentation only.** This contract ships no code. It fixes the exact text and
the exact decision boundaries the two `SKILL.md` variants must carry, so the
implementation is a transcription rather than an interpretation, and so a
reviewer can diff prose against a specification.

Scope: FR-001 through FR-011. Consumed by `tasks.md` and by the UAT runbook.

## 1. Placement and mandate

The pass runs **inside the worktree, immediately before the grill-me interview**,
on every invocation (Q15, FR-001).

| Platform | Anchor | New section |
|---|---|---|
| Claude | between `### 3.5. Bootstrap the Worktree (IN the Worktree)` and `### 4. Run Grill Me Interview (IN the Worktree)` | `### 3.6 Blind-Spot Pass (IN the Worktree)` |
| Codex | between `### 3.5. Bootstrap the worktree (in the worktree)` and `### 4. Run the Grill Me interview (in the worktree)` | `### 3.6 Blind-spot pass (in the worktree)` |

Steps 4 through 8 are **not** renumbered on either platform.

**Mandatory, mirroring the interview's own hard constraint** (Q17, FR-001):
no skip flag, no skip argument, no documented path that reaches the interview
without attempting the pass. The prose must state this as a constraint, not a
default, in the same register the grill-me step already uses ("There is no
`--no-grill` flag and no skip path").

## 2. Engine and dispatch

**Engine**: the already-shipped read-only `codebase-analyst`, unmodified, on both
platforms (Q2, FR-002).

**Prohibitions that are part of this contract** (FR-002, SC-012):

- No agent definition is added or edited on either platform. This is what keeps the Layer 6 sha256 corpus chain in `tests/speckit-pro/layer6-efficiency/fixtures-codex/` unstaled.
- Scaffold's `allowed-tools` stays exactly `Read Edit Write Skill Agent ToolSearch`. No Grep, no Glob, no Bash.

**Dispatch identifier and await discipline**, copied from the house consensus
pattern rather than invented (research.md R3):

| Platform | Identifier | Dispatch and await |
|---|---|---|
| Claude | `speckit-pro:codebase-analyst` | `Agent(subagent_type: "speckit-pro:codebase-analyst", run_in_background: true, ...)`, then **await completion before the interview begins** |
| Codex | `codebase-analyst` | `spawn_agent`, then a bounded `wait_agent` loop until the actual summary is delivered — a status update or a timeout alone is **not** the result — then `close_agent` only when that action is exposed |

The await is normative (FR-002a). The Claude agent definition carries
`background: true`, so a dispatch that is not awaited returns an identifier
rather than findings, and FR-001, FR-002, and FR-011 all become unsatisfiable at
once.

**The bound, stated. A poll is not the deadline.** The shipped Codex rule is that
"a `wait_agent` timeout is one bounded mailbox poll, not proof that an agent is
stuck" (`speckit-pro/codex-skills/speckit-autopilot/SKILL.md`), and that a status
update, an unrelated mailbox wake, or a terminal status without a delivered
result is likewise not the result. So the loop keeps polling across those.
Abandonment is governed by **one execution deadline for the whole pass**:

| Bound | Value | On expiry |
|---|---|---|
| Per-poll `wait_agent` timeout | whatever the surface provides | keep polling; **not** a verdict |
| Pass execution deadline | **5 minutes from dispatch** (Codex checks this via consecutive expired `wait_agent` polls; the poll count is not an independent trigger, and no Claude-side poll construct exists). Stipulated, not precedented — tunable through UAT, and lengthen rather than shorten | abandon the wait; record the §5 **did not run** outcome with reason `wait deadline expired` |

This gives "no reply at all" exactly one observation point on each platform: the
await returned without a summary, or the deadline expired. It is never inferred
from a dispatch still running. A summary arriving after the deadline does **not**
retroactively change the recorded outcome, because the interview has already
started and FR-011 forbids interrupting it.

## 3. Seed

| Seed element | Status | Behaviour when absent |
|---|---|---|
| The roadmap entry's Scope text | **required** | Present in every entry of all eleven roadmaps |
| Each spec named in `Depends On` | **required** | Present in every entry of all eleven roadmaps |
| The `Key Files` section | **optional hint** | Degrade to the required seed and continue. Never report a gap, never skip (Q12, FR-003) |

`Key Files` is optional because the heading is not standardized: html-artifacts
uses `**Key Files:**`, cross-platform-plugin-runtime uses `**Key Files To Audit:**`
and `**Key Files Likely To Change:**`, harness-engineering-uplift carries it on 9
of 15 entries, and pr-size-governance has none at all across its 14 entries.

**Archived-dependency chase (FR-004)**: the dispatch instructions must require
chasing each `Depends On` spec into git history when its artifacts are not in the
working tree, rather than reporting the artifact absent. This spec is the live
example — its own normative contract exists only at
`git show 5e184e33:specs/art-006-autopilot-staging/contracts/scaffold-autopilot-chain.md`.

The chase is executable on both platforms, verified at research.md R2: the Claude
agent does not disallow `Bash`, and the Codex mirror runs
`sandbox_mode = "read-only"`, which permits reads.

## 4. The dispatch block — identical on both platforms, carried verbatim

Reproduced from spec.md FR-005. It must be **byte-identical** in both variants,
because the shipped `codebase-analyst` description frames the agent for autopilot
consensus resolution rather than for this technique, so the block is carrying the
whole framing.

```text
You are running a blindspot pass for <SPEC-ID>: surface the unknown unknowns
in this roadmap entry before its scoping interview.

The operator has read this roadmap entry and its scope. They have not
necessarily read the affected code area, or the archived artifacts of its
dependencies.

Seed (required): the Scope text below, and each spec named in Depends On.
Seed (optional hint, may be absent): the Key Files section.
For each Depends On spec whose artifacts are not in the working tree, chase
it into git history rather than reporting it absent.

Return at most 5 findings, ranked by impact then surprise. Each finding:
N. **<Title>** - 1-3 sentences, plus a repo-relative file or path pointer.
   Impact: <what requirement or design decision this would change if true>
   Surprise: <why the roadmap entry's own text does not already say this>
Then state how many findings you set aside, including when that number is 0.
If you find nothing, reply exactly: The blindspot pass raised no unknown unknowns.
```

Two properties of this block are load-bearing and must not be paraphrased:

- The literal Field Guide words **"blindspot pass"** and **"unknown unknowns"** (Q14, FR-005).
- The operator's structural position, stated as fact rather than asked. Scaffold **must not** ask the operator about their familiarity before the pass (Q14, FR-005).

### 4.1 Payload assembly — what follows the block, in what order

The block is the whole of the framing. The §3 seed material is appended **below**
it, in this order and under these literal labels (FR-005):

```text
Scope:
<the roadmap entry's Scope text>

Depends On:
<the roadmap entry's Depends On chain>

Key Files:
<the Key Files section — this label and its text are omitted entirely when the entry has none>
```

The block's own words "the Scope text below" refer to exactly this appended
material, so the order is part of the contract rather than a formatting
preference. **Nothing else is appended**: no operator commentary, no prior
findings, no spec text.

## 5. Reply classification — three disjoint outcomes, no judgement call

A reply is **usable** when it contains at least one finding in the fixed shape,
**or** the literal sentence `The blindspot pass raised no unknown unknowns.`

| Outcome | Test | Operator status line (§6) | Header line (§9) |
|---|---|---|---|
| **Ran** | a finding **or** the sentinel came back | one of the three set-aside shapes | `ran — N findings surfaced, M set aside` |
| **Returned nothing usable** | a reply came back carrying neither | the "returned nothing usable" shape | `returned nothing usable — <reason>` |
| **Did not run** | no reply at all — dispatch error, empty return, or the §2 **execution deadline** expiring | the "did not run" shape | `did not run — <reason>` |

**A single expired `wait_agent` poll is not the third outcome.** §2 fixes that
boundary: a poll expiring is a cue to keep polling; only the pass execution
deadline expiring abandons the wait.

**"A finding in the fixed shape"** means a numbered item carrying a title and at
least one of the two rationale lines. A numbered title with neither rationale
line does not satisfy the test, because §6's reviewability property *is* the
rationale and a bare title gives the operator nothing to check against the
roadmap entry.

Requiring the sentinel is what makes a silent empty reply impossible to mistake
for a clean pass. The three tests are disjoint and mechanical, and each maps to
exactly one operator string and exactly one header line — the mapping above is
the single place that correspondence is stated, so §6 and §9 cannot disagree
with it.

## 6. Cap, ranking, and the set-aside count

**Cap**: at most five findings. **Not operator-configurable** (Q13, FR-006).

**Scaffold enforces the cap on what it renders.** The dispatch block asks for at
most five, but the reply is model output and cannot be relied on to obey. When
more than five come back, scaffold shows the first five **in the analyst's own
order**, counts the remainder, and states that count through the truncation
string below. Scaffold must **not** re-rank, merge, or rewrite findings to fit:
the ranking is the analyst's, and FR-023 forbids the machinery a re-rank would
need.

**Ranking is reviewable, not deterministic** (FR-006). Each finding carries one
line of impact rationale and one line of surprise rationale, ordered by impact
with surprise as the tiebreak. **No numeric score** is assigned: FR-023 forbids
new executable machinery, so a scoring scheme would be unenforceable, and
identical output across two runs is not a property an LLM pass can promise.
Reviewable means a reader can check each rationale against the roadmap text.

**The set-aside count is always stated, including when it is zero** (FR-006), in
one of these three shapes. Exact strings are confirmed through the UAT runbook:

```text
Showing the 5 highest-impact findings; N more were set aside
Showing all N findings; none were set aside
The blindspot pass raised no unknown unknowns.
```

The third of these is the **sentinel echoed verbatim**. It is one string doing
two jobs — the analyst's signal to scaffold and scaffold's line to the operator —
and that is deliberate, so no second wording for "found nothing" can be invented.

A truncation the operator cannot see reads as "that was everything", so the count
is part of the contract rather than a nicety.

**The two degraded outcomes get one status line each** (FR-006), so §8's block
placeholder resolves in all three outcomes rather than only the first:

```text
The blind-spot pass returned nothing usable; continuing without findings. Reason: <reason>
The blind-spot pass did not run; continuing without findings. Reason: <reason>
```

`<reason>` is one short clause naming what was observed — `reply carried neither
a finding nor the sentinel`, `dispatch error: <message>`, `empty return`, or
`wait deadline expired`. **Exactly one of the five status lines is emitted per
run**, and the same `<reason>` clause is reused verbatim in the §9 header line so
the printed record and the durable record cannot give different reasons.

## 7. Fail-open

The pass **must fail open** (Q18, FR-007). If the dispatch fails or returns
nothing usable, scaffold continues into the interview with nothing seeded and
records the gap and its reason in **both** the operator output and the design
concept.

Scaffold must **not** treat the dispatch outcome as a gate, and must **not**
retry-then-halt.

**Critical clarification, and the reason FR-007 needed one.** "Nothing seeded"
means no *findings* are seeded. It does **not** mean the labelled block is
omitted. The block still travels in all three outcomes, carrying only its status
line in the two degraded ones.

The reasoning is worth preserving because it is easy to re-break: FR-008 makes
the labelled block the sole channel into the interview, and FR-010 has the
interview write the header-blockquote record *because the block asked it to*.
Omitting the block in the degraded path would leave the "did not run" record with
no mechanism to be written at all — the one case where the record matters most
would be the one case that could not produce it.

## 8. The seeded scope block — one shape, two appearances

Findings reach the interview by being appended as a labelled block to the `scope`
argument scaffold **already** passes (Q3, FR-008). No new interview argument. No
change to what the interview produces. No edit to grill-me on either platform.

The block uses **one shape in both places it appears** — the operator output and
the seeded `scope` string — so the two records cannot drift:

```text
--- BLIND-SPOT PASS FINDINGS ---
<the numbered findings, or the FR-006 status line for the outcome>
<the set-aside line>
Record the Blind-spot pass line in the design concept's header blockquote.
Treat each finding as a candidate question; any finding not reached becomes an Open Question.
--- END BLIND-SPOT PASS FINDINGS ---
```

**Platform note (research.md R6)**: on Codex this edit lands in the same step as
five strings pinned by
`tests/speckit-pro/layer1-structural/validate-codex-skills.py` — `picker-first
HITL guard`, `request_user_input`, `default_mode_request_user_input`, `Do not ask
the Grill Me question as a normal assistant`, and `` If `request_user_input` is
absent ``. All five must survive verbatim.

## 9. The design-concept record

One line in the design concept's **existing** header blockquote, under the key
`**Blind-spot pass:**`, recording exactly one of the three §5 outcomes (Q19,
FR-010).

**One shape per outcome, fixed.** SC-004 requires a reader to tell the outcomes
apart from the header alone, which free-form prose cannot guarantee:

```text
> **Blind-spot pass:** ran — N findings surfaced, M set aside
> **Blind-spot pass:** returned nothing usable — <reason>
> **Blind-spot pass:** did not run — <reason>
```

The word immediately after the key is the discriminator, drawn from the closed
set `ran`, `returned nothing usable`, `did not run`. `<reason>` is the same
clause §6's status line carried. A pass that ran and raised nothing is the first
shape with `N` and `M` both zero — which is exactly what distinguishes it from a
pass that never ran, and is the distinction SC-004 exists to preserve.

**Prohibitions** (FR-010, Q8):

- No new section in the design concept.
- No separate findings artifact. Specifically **not** `.process/<SPEC-ID>-blind-spots.md`. The design concept is the only home for findings.
- No change to grill-me's output schema.

Adding the key needs no schema change: the blockquote already tolerates keys
beyond the four its reference documents, as this feature's own design concept
demonstrates by carrying a size-estimate line that nothing rejected.

**Disposition of every finding** (FR-009, SC-003): a finding the interview
resolves becomes an entry in the existing question-and-answer record; a finding
it does not reach becomes an Open Question. **No finding may be dropped
silently.**

## 10. Presentation is informational

The run flows straight from the findings into the first interview question. **No
confirmation, no curation step, no continue/abort prompt** between the two (Q16,
FR-011).

This is what keeps scaffold at exactly one confirmation outside the interview —
the chain — which is the seam that separates interactive from autonomous.
