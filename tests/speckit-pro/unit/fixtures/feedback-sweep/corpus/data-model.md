# Phase 1 Data Model: Feedback Sweep, slice 1 of 2

**Feature**: `spec-808-feedback-sweep` | **Date**: 2026-08-20

Entities are drawn from the spec's Key Entities section. Field names and
validation rules are fixed here; the wire shape of the helper envelope is in
`contracts/sweep-pr-feedback.md`.

---

## 1. Observed comment (helper input)

One pull-request comment as the orchestrator observed it, before any filtering.
The orchestrator builds these from two `gh` reads and passes them as data.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Required, non-empty. The immutable GitHub comment id. The FR-009 skip key and the FR-014 reverse join both key on this. |
| `surface` | enum | Required. `review_thread` or `pr_conversation`. Closed set. |
| `author` | string \| null | Nullable. Null when the account was deleted. FR-013 requires the log to say so explicitly rather than leave the cell blank. |
| `author_association` | enum | Required, non-null. The eight-value GitHub vocabulary. Nullable `author` beside a non-null association is the deleted-account case. |
| `body` | string | Required. Already truncated to the byte budget (see below). |
| `truncated` | boolean | Required. True when the orchestrator cut the body at the budget. |
| `thread_resolved` | boolean | Required for `review_thread`, absent for `pr_conversation`. FR-004's "only unresolved threads are read" is the orchestrator's query filter; if a resolved thread reaches the helper anyway it is **excluded with reason `thread_resolved`**, not rejected. Excluding visibly is what the `observed == candidates + excluded` invariant requires. |

### The eight-value author association

`OWNER`, `MEMBER`, `COLLABORATOR`, `CONTRIBUTOR`, `FIRST_TIMER`,
`FIRST_TIME_CONTRIBUTOR`, `MANNEQUIN`, `NONE`. Closed enum; a ninth value is a
malformed observation, not an untrusted author.

**Allowlist**: `OWNER`, `MEMBER`, `COLLABORATOR`. Every other value is excluded
with reason `untrusted_author` (FR-005). Each of the five excluded values
carries its own fixture (FR-008a).

The allowlist is a **proxy** for write access, not a statement of it.
`COLLABORATOR` can be a read-only invitation and `MEMBER` is organization
membership. FR-005 fixes the allowlist as stated and names the proxy so no later
reader mistakes it for a permissions check.

### Body truncation, and why the orchestrator does it

**Budget: 8192 bytes (8 KiB) per body, measured as UTF-8.**

The runner enforces `BOUNDED_TEXT_INPUT_BYTES = 32 * 1024` per string, and
`iter_input_strings` recurses fully through nested dicts and lists. Every
comment body inside the observation is therefore checked individually, and one
oversized body returns an `invalid_input` diagnostic that **rejects the entire
request before the helper runs**. That is the failure FR-008 exists to prevent:
one 40 KiB comment would otherwise fail a whole sweep rather than degrading that
one item.

Because the rejection happens at the boundary, **the helper cannot be the thing
that truncates** — it never receives a body that breaks the limit. So:

- The **orchestrator truncates** each body to 8192 bytes when it builds the
  observation, and sets `truncated` per comment.
- The **helper validates** the precondition and returns a diagnostic naming the
  offending comment id if a body exceeds the budget. It does not silently
  re-truncate.

Validating rather than transforming means an orchestrator bug fails loudly with
a comment id attached, instead of failing opaquely at the bounded-input boundary
with only a field path. 8 KiB is far below the 32 KiB limit and far above any
real review comment, and the ten-line recognition window sits in the first few
hundred bytes, so truncation never affects recognition (an explicit spec edge
case).

---

## 2. Swept comment (helper output)

One observed comment after filtering and recognition. The helper reports these;
it assigns no class.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Echoed from the observation. |
| `surface` | enum | Echoed. |
| `author` | string \| null | Echoed. Null is preserved, never coerced to a blank. |
| `author_association` | enum | Echoed. |
| `truncated` | boolean | Echoed. |
| `export` | object \| null | Null when no registered line matched. |
| `export.template_id` | string \| null | Null when the matched sentence is shared and the template cannot be determined. |
| `export.template_ambiguous` | boolean | True when the matched sentence is declared by more than one template (FR-007a). |
| `export.kind` | enum | `prompt`, `markdown`, or `empty`. |
| `export.matched_lines` | array of integer | Every matched registered line, as 1-based line numbers within the ten-line window, in ascending order, for evidence (FR-007f). |
| `export.anchors` | array of string | Anchors parsed from the body, carried as detail on the row (FR-010). Each entry is the run after the `#` of a value whose whole matches `#[a-z0-9-]{1,64}`; at most sixty-four entries, the first sixty-four in body order (FR-007e). Empty for the `empty` kind. |
| `export.anchors_dropped` | integer | Count of anchors dropped, whether non-conforming or conforming past the sixty-fourth (FR-007e). |

**Recognition** matches registered whole lines against the body's **first ten
lines**, after normalizing CRLF and CR to LF and stripping trailing whitespace.
The lead is not the first line: the shipped builders emit `Artifact: <title>`,
a feature line, and a blank line ahead of it, so a verbatim paste puts the lead
on line four. The ten-line window also survives a reviewer trimming that header
and a template later adding one.

Recognition never forces a class (FR-007d). The single exception is the `empty`
kind, which carries no objections and takes `no action` (FR-007a).

---

## 3. Excluded comment (helper output)

Every comment the helper set aside, each naming why. An exclusion is always
reported, never silent — that is what makes a marker collision visible rather
than a dropped candidate (FR-006).

| Field | Type | Rules |
|---|---|---|
| `id` | string | The excluded comment's id. |
| `surface` | enum | Echoed. |
| `reason` | enum | Closed set of four, below. |

| Reason | Meaning |
|---|---|
| `untrusted_author` | Association outside the allowlist (FR-005). Reported as "not swept: untrusted author". |
| `self_reply` | The sweep's own earlier reply (FR-006). |
| `already_logged` | The id already appears in the Feedback Sweep Log (FR-009). |
| `thread_resolved` | The review thread is resolved. FR-004's query filter means one normally never reaches the helper; this reason covers the one that does, so it is excluded visibly rather than dropped. See the `thread_resolved` field row above. |

### The self-reply test needs both halves

A comment is the sweep's own reply when **both** hold: the body begins with the
fixed HTML-comment marker, matched **anchored at the start** rather than
anywhere in the body, **and** the author matches the account this run
authenticated as.

Both are required, and neither alone works. The marker alone would silently skip
a reviewer who quoted a sweep reply while disagreeing with it, because a quote
copies the raw body — anchoring is what defeats that, since a quote prefixes the
copied text. The author alone would skip that account's every genuine comment,
because the sweep authenticates as the operator, who is the reviewer the
checkpoint exists for.

Without this exclusion the loop cannot converge (FR-006a): each run's reply is a
new comment with a new id that the FR-009 skip key never matches, so it becomes
the next run's candidate and produces another reply without end.

---

## 4. Classification

The closed four-value vocabulary assigned by the **orchestrator**, not the
helper: `amended`, `answered`, `deferred`, `no action`. No other value permitted.

**The comment is the unit.** One comment yields exactly one class, one log row,
and one reply, however many objections it carries. Recognized export anchors ride
as detail on that row.

**Dominance**: when one comment's objections would warrant different classes,
`amended` wins over the other three, and every non-dominant objection is named
in the row's disposition text and in the reply. The rule is forced, not
stylistic: the roadmap's "sweep, amend, re-review" decision rejected leaving
re-run responsibility to manual judgment, and a classifier that let a mixed
comment escape `amended` would recreate that rejected path one layer down.
FR-003's cross-platform determinism rules out any non-fixed tie-break.

Dominance ranks `amended` above the other three and stops there. It does not
order `answered`, `deferred`, and `no action` against each other, because those
three are behaviorally identical at both points classification controls: none
route through consensus and none stop the run.

**Routing**: only `amended` enters the category-routed consensus protocol
(FR-011).

---

## 5. Feedback Sweep Log

The durable table in the workflow file, one row per handled comment. The sole
record of what the sweep has already handled and the basis for skipping on
re-runs. No state-file mirror may be written (FR-013).

**Placement**: under its own `### Feedback Sweep Log` heading, immediately after
`### Consensus Resolution Log`. Additive-safe — the phase-coverage guard's table
reader is heading-anchored, breaks on any line starting with `#`, and carries no
reference to the Consensus Resolution Log at all.

**Header**: `| # | Comment ID | Surface | Author | Class | Disposition | Commit | CRL # |`

| Column | Rules |
|---|---|
| `#` | Row number, 1-based. |
| `Comment ID` | The immutable GitHub id. The FR-009 skip key. |
| `Surface` | `review thread` or `pr conversation`. |
| `Author` | The login, or an explicit unresolvable marker when the account was deleted. Never blank. |
| `Class` | One of the four values. |
| `Disposition` | Reviewer-derived prose. **Escaping is mandatory** — see below. |
| `Commit` | The amendment commit sha. Empty for every class but `amended`. |
| `CRL #` | The linked Consensus Resolution Log row number. Empty for every class but `amended`. |

### Escaping is a correctness rule, not formatting

`Disposition` carries reviewer-derived prose, so it MUST escape any pipe as
`\|` and any newline as a line break. The table readers in this codebase split
rows on the bare pipe with no escape handling, so one unescaped pipe shifts
`CRL #` out of position and makes FR-014's link read the wrong column.

The `Comment ID` key sits **ahead** of `Disposition`, so it survives a bad
escape regardless, which keeps the FR-009 skip key safe even if the link breaks.
Both this and the unresolvable-author rule are found-and-fixed defects, which is
why SC-010 measures them.

---

## 6. Consensus Resolution Log row

The existing record, extended by one `Type` value. Amendments add a row here in
addition to the Feedback Sweep Log row.

**Existing header** (`consensus-protocol.md` line 617):
`| # | Type | Question/Gap/Finding | Categories | Round | Outcome | Resolution | Analysts Used |`

- `Type` takes `Sweep`, a fourth value beside `Clarify`, `Gap`, and `Finding`.
- The item cell — `Question/Gap/Finding` in the canonical header, `Item` or
  `Question` in several committed workflow files — **names the comment id**.

**The link is bidirectional and costs no extra column.** The sweep row's `CRL #`
names this row; this row's item cell names the comment id. Keying the reverse
direction on an immutable GitHub id rather than on a row position alone is what
makes the join survive a renumbered table.

**Sweep rows count toward the Round-2 escape-rate metric.** They come from the
same category-routed protocol and can be mis-routed the same way, so excluding
them would blind the metric precisely where the input is least controlled. The
dispositions that could distort it never reach the log at all, because FR-011
keeps `answered`, `deferred`, and `no action` out of consensus. The `Type`
column is itself the discriminator, so a threshold breach can be attributed to
sweep rows or phase rows without either being excluded from the rate.

---

## 7. Export lead registry

The set of registered whole lines identifying an artifact-exported block. Static
data in `read_only.py`, guarded by a test that derives the expected set from the
gallery manifest and the templates themselves (FR-008a).

| Entry field | Type | Rules |
|---|---|---|
| `line` | string | The exact whole line, matched after normalization. |
| `template_id` | string | The template declaring it. |
| `kind` | enum | `prompt`, `markdown`, or `empty`. |

**Contents** (counted from the shipped templates):

| Group | Entries | Detail |
|---|---:|---|
| Lead sentences | 14 | 7 note-payload templates × 2 kinds |
| Empty-export sentences | 6 | 3 distinct markdown + 3 distinct prompt |
| Serialization headers | 3 | `feature-flags`, `prompt-tuner`, `triage-board` |

**Shared sentences resolve to ambiguous, never to a guess.** Three templates
declare `No objection was recorded. This record is not an approval.` identically,
and the same three share its prompt companion. A match on a shared sentence sets
`template_ambiguous` true and leaves `template_id` null.

**The `prompt` kind matters for safety, not completeness.** Its lead is an
imperative addressed to a coding agent — "Act on each objection recorded below",
"Implement the visual direction named below and no other". An unregistered one
reaches the consensus analysts as ordinary free text carrying an instruction,
and the security-keyword routing that would force a full fan-out matches none of
that phrasing. Registering it means the lead is matched as a known constant and
carried as metadata rather than passed through as free instruction text.

---

## 8. Draft PR row and corroboration status

The existing workflow-file record naming the draft pull request. **The sweep
reads it and never writes it.**

The corroboration vocabulary is six values, and FR-019 assigns exactly one
behavior to each. The six are exhaustive.

| Status | Behavior |
|---|---|
| `match` | Sweep. |
| `no_record` | Proceed with a one-line note. The gate does not apply — no checkpoint was ever opened. |
| `skipped` | **Stop.** The gate applies and the observation failed. |
| `pr_closed` | Stop. |
| `pr_missing` | Stop. |
| `identity_mismatch` | Stop. |

**`skipped` stops, and the distinction matters.** `no_record` means the gate
does not apply; `skipped` means it applies and evaluation failed. Treating
"could not observe" as "observed nothing" would make the checkpoint silently
optional exactly when the tool is unreliable, which is when unread feedback is
most likely. Nothing in this repository treats an unreachable tool as evidence
of a clean state.

**The `skipped` report reads differently from the three discrepancy stops** and
names which of its four causes occurred: the tool was absent, unauthenticated,
rate-limited, or returned unparseable output. Behavior does not branch on the
cause; only the report does. Collapsing it into the discrepancy wording would
cost the operator the ability to tell a broken tool from a real discrepancy, and
those have different fixes.

**Resume paths differ.** For `skipped`, fix the tool and re-run — the
observation is retaken fresh on every invocation. Clearing the `Draft PR` row is
**not** a resume path here: that belongs to `pr_missing`, where the row's absence
would match reality, and reusing it for `skipped` would erase a probably-true
record to manufacture a `no_record` reading.

---

## State transitions

One sweep run, in order:

```text
validate self_login ─ invalid ─────────────────────────► STOP (FR-006b)
  └─ read corroboration status
       ├─ no_record ────────────────────► proceed to task work (one-line note)
       ├─ skipped | pr_closed | pr_missing | identity_mismatch ─► STOP, per-status resume path
       ├─ outside the six ──────────────► STOP, malformed record (FR-019)
       └─ match
            └─ observe both surfaces (paginated to exhaustion, authorAssociation requested)
                 ├─ any read fails ─► discard whole observation ─► STOP (FR-004c)
                 └─ both exhausted
                      └─ truncate bodies to 8 KiB, flag each
                           └─ helper: filter, recognize, report envelope
                                └─ orchestrator: assign one class per candidate
                                     ├─ amended ─► consensus
                                     │    ├─ no answer ─► CRL row, no sweep row, no class
                                     │    │                 (siblings finish; STOP below)
                                     │    └─ resolved ─► target check ─┬─ outside ─► STOP (FR-012b.2)
                                     │                                 └─ ok ─► edit ─► commit
                                     │                                      ├─ push fails ─► STOP (FR-012e)
                                     │                                      └─► bookkeeping commit
                                     └─ answered | deferred | no action ─► rows only
                                          └─ reconcile, then reply to each unanswered handled comment
                                               ├─ a reply fails ─► report it; owed next run (FR-015b)
                                               ├─ any human-review item ─► STOP (FR-011a)
                                               ├─ any amended ─► STOP for re-review
                                               ├─ none amended, ≥1 handled ─► proceed
                                               └─ none handled ─► no rows, no commit, proceed
```

The FR-011a stop sits at the same point as FR-017's, after this run's rows and
replies, so sibling items that resolved are fully processed and the two stops
emit one report rather than two.

Every STOP above emits the one FR-020 report: condition, what already landed,
resume path. Reads precede writes throughout, which is why the only stop needing
no unwind reasoning is the read failure — at that point nothing has been
written.

**Commit ordering is forced, not stylistic.** A row that names its commit cannot
exist until that commit's sha does, so an amendment's bookkeeping commit must
land after the amendment's own commit. The bookkeeping commit stages the
workflow file path alone, never the directory, and takes a `chore:` subject.

**Per-amendment cadence is a separate choice**, justified separately: it bounds
the window in which an amendment is pushed but unrecorded to a single item. That
matters because the consensus protocol producing the resolved edit is not proven
deterministic beyond routing and log aggregation, so a comment reprocessed
inside that window is not guaranteed to resolve the same way twice.

**The interrupt window is accepted, not closed.** An amendment whose bookkeeping
commit never landed leaves no row, so the skip key does not see it and the
comment is a candidate again next run. No repair rule is defined because repair
needs a live witness independent of the record, and every candidate witness here
is closed: FR-006 excludes the sweep's own reply, FR-012 defines no commit
convention recovering a comment id, and FR-016 forecloses thread resolution.
Neither outcome is unsafe — the fresh round either recognizes the edit already
landed and classifies `answered` or `no action`, or amends again and stops for
re-review the same as a first-time amendment.
