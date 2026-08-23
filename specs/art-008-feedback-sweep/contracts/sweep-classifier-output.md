# Contract: `sweep-classifier` and `sweep-analyst` structured records

**Feature**: `art-008-feedback-sweep` | **Date**: 2026-08-22

The records the sweep's two scoped agents return. Neither agent is a runner
operation: no `helper_id`, no registration, no dispatch-table entry. These are
the prompt-and-response shapes between the orchestrator and two definitions
shipped in `agents/` and `codex-agents/` and dispatched only by the sweep.

**Producers**: `speckit-pro:sweep-classifier` and `speckit-pro:sweep-analyst`,
harness-scoped on both platforms — a pinned Claude `tools:` allowlist and Codex
`sandbox_mode = "read-only"`, with the orchestration set and `Skill` denied.
**Consumer**: the orchestrator. **Transport**: the agent response; nothing here
is written to disk, and where a run needs a file it lives under FR-004d's
directory and is removed with it.

**They read reviewer text and return enums.** Every field below is a closed
enum, a bounded string, or null, and the fields the orchestrator branches on
carry no reviewer bytes at all. That is the design: the agents that read
attacker-controllable text hold no tool that can act on it, and what crosses
back cannot widen what the sweep may reach.

---

## 1. Classifier record

One dispatch per candidate, one record back, with the one exception below. This
replaces the orchestrator's own read of a comment body — after this contract it
observes no body at all, because the observation is piped into the runner and
what returns to the orchestrator is the parse envelope and one shaped block per
candidate. The sibling contract's "classification is orchestrator judgment over
this envelope" is re-pointed here: the judgment moves into a scoped agent, and
the helper still assigns no class.

**An `empty`-kind candidate is never dispatched.** FR-007a forces `no action`
for that kind from the parse alone, so there is no judgment to make; the
orchestrator takes the class from the export record without a body, and no block
is produced. Dispatching an agent to re-decide a forced class would reopen what
FR-007a closed.

### What the classifier receives

```json
{
  "comment_id": "IC_kwDO...",
  "block": "<the analyst-payload leg's returned block, verbatim>",
  "export": {
    "template_id": "implementation-plan",
    "template_ambiguous": false,
    "kind": "markdown",
    "matched_lines": [4],
    "anchors": ["phase-2"]
  },
  "classes": ["amended", "answered", "deferred", "no action"],
  "targets": ["spec.md", "plan.md", "tasks.md"]
}
```

`block` is the sanitized, delimited text FR-007g's `analyst_payload` leg
returns, passed through unchanged. `export` is the parse's own record for that
comment, `null` for an ordinary one — FR-007e's two-part assembly, handed to a
classifier rather than to an analyst. The two vocabularies are restated in the
prompt so the record's enums have a stated source rather than a remembered one.

**That leg's population widens here, deliberately.** FR-007g shaped the bodies
forwarded to a consensus analyst; every dispatched candidate now gets a block,
because classification now happens in an agent. No unshaped body reaches any
model on any path, which is the point. The leg runs inside the piped parse
invocation, once per candidate, because the runner is stateless and the piped
observation is the only place a raw body exists.

### Response

```json
{
  "comment_id": "IC_kwDO...",
  "class": "amended",
  "target": "plan.md",
  "reason": "Asks that the export registry cover every template that declares an export, and names the plan's Phase / Registry section."
}
```

### Field rules

| Field | Required | Rules |
|---|---|---|
| `comment_id` | Yes | Echoed. A value other than the one dispatched is malformed: the class would attach to the wrong row. |
| `class` | Yes | Exactly one of `amended`, `answered`, `deferred`, `no action` (FR-010). Note the space — `no action` is the spelling this feature's vocabulary carries everywhere. |
| `target` | Yes | `spec.md`, `plan.md`, `tasks.md`, or `null`. Non-null **when and only when** `class` is `amended`. |
| `reason` | Yes | Non-empty string, at most **512 bytes** as UTF-8, carrying neither pipe nor newline. Reviewer-derived prose. |

**Exactly four fields.** A record carrying a fifth is malformed whatever it
holds. This is what keeps a body from riding back: a producer that echoed the
block, quoted a span of it, or attached notes of its own fails the key-set
assertion instead of passing unnoticed into a log row.

### `target` is an enum, never a path

The classifier cannot express a path, so it cannot request one. FR-012b rule 1
refuses a change outside the three artifacts by taking `deferred` and naming the
refused target — that name goes **in `reason`, as prose**, which is why the enum
never widens to hold a path the sweep will not write. FR-012c's resolved
equality still runs at the write point: a closed enum upstream is a decision,
not a check at the point of use, and FR-012b already says which of the two
survives a future caller.

### `reason` is reviewer-derived and is treated as such

It reaches an artifact only through FR-012f — the Feedback Sweep Log
`Disposition` cell on the `log_row` leg, and the reply body on the `reply` leg.
**No new leg and no new call**: that cell was already one `log_row` call and
that body already one `reply` call.

**It is also the only channel FR-010's dominance rule has left.** A mixed
comment takes `amended` and every non-dominant objection MUST still be named in
the disposition and the reply — and since the orchestrator now reads no body,
`reason` MUST carry those names or nothing does.

**The orchestrator writes the surface's output, never the field.** The raw
`reason` is an input to the surface and reaches nothing else — not the row, not
the reply, not the run report. SC-014's method measures it: a deny-set span
seeded inside a `reason` is absent from every captured output, with the
placeholder naming the rule in its place.

**Over budget is a stop, not a cut.** A `reason` past 512 bytes is malformed and
stops the run under FR-020 naming the comment id. Cutting would be the kinder
rule for verbosity and the wrong one for safety: a cut lands anywhere, and a cut
inside a token-shaped run can leave the run under the twenty characters the
deny-set requires, so nineteen bytes of a secret would publish behind a `bearer`
trigger whose rule no longer fires. One rule for every malformed field, one
outcome, and the byte-identity below stays exact. The dominance naming is not
lost to a cut either, because there is no cut: an item whose objections cannot
be named inside the budget stops and a human reads them.

**The residual.** Up to 512 bytes of reviewer-derived prose does cross, and the
redaction surface's known misses are its misses here too. What the scoping buys
is not that no text crosses; it is that the agent which read the text held no
`Bash`, no network, and no MCP, and that what crossed is bounded, structured,
redacted, and read by a human at the checkpoint.

---

## 2. Analyst perspective record

Three dispatches per `amended` item, one record each, the perspective given in
the prompt — so the shared analysts and the consensus routing table are
untouched. FR-011 gains a caller, not a protocol.

```json
{
  "comment_id": "IC_kwDO...",
  "perspective": "codebase",
  "finding": "The registry is declared once per template, so covering every exporting template is a data change rather than a code change.",
  "evidence": ["specs/art-008-feedback-sweep/plan.md:218"],
  "escape_hatch": false
}
```

| Field | Required | Rules |
|---|---|---|
| `comment_id` | Yes | Echoed. |
| `perspective` | Yes | `codebase`, `spec-context`, or `domain`. Echoed from the prompt, so a record answering the wrong perspective is visible. |
| `finding` | Yes | Non-empty prose. |
| `evidence` | Yes | Array of repo-relative citations, possibly empty. Never an absolute path. |
| `escape_hatch` | Yes | Boolean. The shipped protocol's Round-1 escape signal as a field, rather than a keyword the synthesis has to find in prose. |

**The whole record is at most 8192 bytes** as UTF-8, the one text budget this
feature carries. Past it, the record is malformed.

**The domain perspective runs without web access.** `sweep-analyst` holds
`Read`, `Grep`, and `Glob` and nothing else. That is a real loss of reach
against the shipped domain role, and it is accepted: a web-capable agent reading
reviewer text is the finding this scoping closes.

---

## 3. Analyst synthesis record

One further `sweep-analyst` dispatch per `amended` item, in a synthesis prompt
over the three perspective records. **Synthesis is not `consensus-synthesizer`**,
which declares no `tools:` allowlist and so inherits `Bash`, the network, and
every installed MCP server; routing sweep text through it would reopen the
finding one hop downstream.

```json
{
  "comment_id": "IC_kwDO...",
  "outcome": "resolved",
  "agreement": "3/3",
  "basis": null,
  "edit": {
    "file": "plan.md",
    "anchor": "The registry holds each template's markdown and prompt leads as separate entries",
    "replacement": "The registry holds each template's markdown and prompt leads as separate entries, and the manifest is the source of which templates export at all"
  }
}
```

A human-review outcome carries the same envelope with `edit` null:

```json
{
  "comment_id": "IC_kwDO...",
  "outcome": "human_review",
  "agreement": null,
  "basis": "analyst_failed",
  "edit": null
}
```

| Field | Required | Rules |
|---|---|---|
| `outcome` | Yes | `resolved` or `human_review`. |
| `agreement` | Yes | `3/3` or `2/3` when `resolved`, `null` when `human_review`. The values are the Consensus Resolution Log's own, so the row fills without a translation table and `[HUMAN REVIEW]` is what that cell carries for the other outcome. |
| `basis` | Yes | `null` when `resolved`. Otherwise one of `all_disagree`, `escape_unresolved`, `analyst_failed` — the three ways FR-011a names. Behavior does not branch on it; only the report names it. |
| `edit` | Yes | The object above when `resolved`; `null` when `human_review`, which is FR-011a's no edit, no class, no sweep row. |
| `edit.file` | Yes | `spec.md`, `plan.md`, `tasks.md`. An enum, never a path: the orchestrator joins it to the current feature directory, and FR-012b rule 2 still resolves and compares at the write point. |
| `edit.anchor` | Yes | A verbatim excerpt of the target file's current bytes, at most **512 bytes**. |
| `edit.replacement` | Yes | The text replacing the anchor span, at most **8192 bytes**. May be empty. |

### The anchor matches exactly once, or the run stops

It MUST occur **exactly once** in the target file as it stands when the edit is
applied. Zero occurrences and two are both stops, before any write. No fuzzy
match and no first-match fallback: taking the first of two is the defect FR-007f
names on the sanitization side, landing here on a planning artifact a human is
about to review as amended.

**Two different things are called an anchor in this feature.** FR-007e's
`anchors` are the parenthesised values ending a registered export line, produced
by the parse and carried as detail on a row. This one is an edit locator,
produced by an analyst and consumed by a write. Each keeps the natural word in
its own document, and the collision is stated once so a reader does not resolve
it the wrong way.

**An empty `replacement` is a deletion**, and MUST be named as a deletion in the
row's disposition. A deletion recorded as an ordinary amendment hides what the
sweep did from the human the checkpoint exists for.

**Only `replacement` passes FR-012f's `amendment` leg.** The anchor introduces
nothing — it is compared against bytes already committed, and redacting it would
guarantee it matched nothing.

---

## Validation

| Code | Condition | Effect |
|---|---|---|
| `malformed_record` | Unknown `class`, `target`, `perspective`, `outcome`, or `basis`; missing field; extra field; non-string prose field; `comment_id` mismatch; `target` non-null on a class other than `amended` or null on `amended`; `edit` present on `human_review` or absent on `resolved`; a `reason`, a perspective record, or a `replacement` past its budget. | Stop under FR-020 naming the comment id. No retry, no coercion, and no default: the four classes route differently, so there is no safe guess between them — the fail-closed reasoning FR-019 gives for a corroboration value outside its six. |
| `anchor_not_unique` | The anchor occurs zero times, or more than once. | Stop before any write, naming the comment id and the count. |
| — | `edit.file` resolves outside the three-member set. | FR-012b rule 2's stop, unchanged. Reaching it means classification already failed, so it is a defect report rather than a routine path. |

---

## Call counts and identity

FR-008a's captured-call fixture derives these from the corpus expectations
rather than carrying them typed beside it.

- **One `analyst_payload` call per candidate whose export kind is not `empty`.**
  The previous derivation was one per comment routed to consensus; every routed
  comment is such a candidate, so this count subsumes it. The calls run inside
  the piped parse invocation, which is the only place a raw body exists.
- **One block per such candidate, reused by every consumer.** The bytes handed
  to `sweep-classifier` and to each of that comment's four `sweep-analyst`
  dispatches are equal. The surface is deterministic, so a second call would
  return the same bytes; requiring one call and asserting byte-equality is the
  form a fixture can fail.
- **One `sweep-classifier` dispatch per candidate whose export kind is not
  `empty`**, and four `sweep-analyst` dispatches per `amended` item: three
  perspectives, then one synthesis. An `empty`-kind candidate derives zero of
  each and one `log_row` call, like any other unrouted class.
- **No orchestrator read carries a body**, for any id, candidate or excluded.
  The observation is piped into the runner and never written; what the
  orchestrator holds afterwards is the bodiless records and the shaped blocks,
  and it hands each block onward unread.

The orchestrator remains a model holding `Bash`. The control is that it is never
handed a body — by construction, because no path gives it one, rather than by
enforcement — and that residual is stated here and in `plan.md`'s trust-boundary
item rather than left to be inferred from the absence of a rule.

---

## Fixtures

Every rule above has one that can fail. Cases live in
`tests/speckit-pro/unit/fixtures/feedback-sweep/comment-corpus.json` with
expectations under the same case name in
`tests/speckit-pro/unit/fixtures/feedback-sweep/expected-envelopes.json`, driven
by `tests/speckit-pro/unit/test-feedback-sweep-parse.py`. The scoping half is
Layer 5.

| Case | Fails when |
|---|---|
| `classifier-fifth-class`, `classifier-id-mismatch` | A value outside the four is mapped onto one instead of stopping, `no_action` with an underscore is accepted, or a record answering a different comment is filed against the dispatched one. |
| `classifier-target-on-answered`, `classifier-amended-null-target` | The `target` rule is asserted in one direction only. |
| `classifier-refuses-out-of-set-target` | A refusal drops the requested path instead of naming it in the disposition, or takes a class other than `deferred`. |
| `classifier-extra-field` | A record echoing the block passes. |
| `classifier-reason-over-budget` | A 513-byte reason is cut and used instead of stopping the run with zero rows, zero replies, and zero commits. |
| `classifier-reason-seeded-token` | The raw `reason` reaches the row, the reply, or the report instead of the surface's output. |
| `classifier-mixed-comment-dominance` | A non-dominant objection is absent from the disposition or the reply. |
| `classifier-empty-kind-candidate` | An `empty`-kind candidate is dispatched, or gets a block, or takes a class other than `no action`. |
| `analyst-perspective-record-shape`, `analyst-replacement-over-budget` | An unknown `perspective`, a missing `escape_hatch`, a perspective record past 8192 bytes, or a `replacement` past it is accepted. |
| `analyst-anchor-absent`, `analyst-anchor-duplicated`, `analyst-anchor-unique` | A miss or a collision writes anyway, or a clean anchor is refused. |
| `analyst-edit-file-outside-set` | Rule 2 admits a fourth path, or part of the edit is written before the stop. |
| `analyst-empty-replacement-deletion` | A deletion is recorded as an ordinary amendment. |
| `analyst-human-review-record` | `edit` is non-null, a class is assigned, a Feedback Sweep Log row is written, or the run does not stop. |
| The captured-call fixture | A dispatch count is wrong, the block differs between consumers, the `amendment` leg carries anchor bytes, or an orchestrator read carries a body. |
| `validate-tool-scoping.py`, `UNTRUSTED_INPUT_CONSUMERS` | A member gains a tool, loses a denial, or an open executor is added to the tuple. |
