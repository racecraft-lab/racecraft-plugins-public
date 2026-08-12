# Contract: The Export Payload

Four templates in the gallery carry export controls, each with its own copy of
the code that builds them. There is no shared runtime, so this document is the
shared thing: the strings are pinned here once, and every implementation and the
acceptance runbook check against this file rather than against each other.

The strings below are **literal**. They are stated here rather than left to the
implementation because an approximation of "this is not an approval" is not the
same sentence, and the whole point of the wording is that a reader cannot misread
it.

Which kinds an artifact carries is declared by its routing catalog entry, never
chosen by the author:

| Template | `exports` | Controls |
|---|---|---|
| `implementation-plan` | `["prompt","markdown"]` | Copy as prompt, Copy as Markdown |
| `module-map` | `["prompt","markdown"]` | Copy as prompt, Copy as Markdown |
| `code-approaches` | `["prompt","markdown"]` | Copy as prompt, Copy as Markdown |
| `pr-writeup` | `["prompt","markdown"]` | Copy as prompt, Copy as Markdown |
| `spec-explainer` | `[]` | **none**, and no reader-input field of any kind |

Exactly one control per declared kind, labelled by destination — "Copy as
prompt", "Copy as Markdown" — never by mechanism.

## Why this document exists here

ART-002 authored the original of this contract, and all three templates it
shipped name it in a source comment. That copy was deleted when ART-002 was
archived, so every shipped template now carries a pinning reference that resolves
nowhere in the tree. This document restores the pinned literals under ART-003 and
adds `pr-writeup`'s.

Two honest consequences, recorded rather than left to be discovered:

- Nothing compares the copies of the failure message across the four templates.
  This slice does **not** add that comparison, because FR-039a fixes its change to
  shared validation at three literals. Verified by hand instead: the message is
  byte-identical in all three shipped templates as of 2026-08-12.
- **This document will dangle the same way when ART-003 is archived.** Naming the
  problem is not solving it. A durable home for the pinned literals is a change to
  shared foundation files and belongs to a spec that owns them.

---

## What every export carries

- **The reader's conclusion, not the document's content.** A prompt export from a
  write-up review says what the reviewer wants answered; it does not restate the
  write-up.
- **Enough context to act on alone.** The person pasting it has left the artifact
  behind. Every export names the feature and the artifact it came from, in a
  header line, in every state including the empty one.
- **Only what the reader produced.** An export lists only the items the reader
  recorded against. No line, no placeholder, and no count for an item left empty.
- **Nothing the reader could not see.** No inline data the artifact was built
  from but did not display.
- **Live state.** Read at the moment of invocation, never a value written into
  the file when it was authored.

## The header line

Every export opens with the same two lines, in every state including the empty
one, both read from live state:

```text
Artifact: <artifact title>
Feature: <feature id> <feature name>
```

Pinned because four templates emit this from four separate copies of the code,
and a form left to each of them is a form that drifts. The artifact title is the
one its catalog entry carries. The feature identifier is what lets a reader who
has left the document find the spec again, which is the obligation
`SPA-CONTRACT.md` states as naming "the artifact, the spec, and the location the
conclusion attaches to".

**Recorded gap.** Pasted into a pull-request comment, these two lines render as
one paragraph. That is cosmetic for the automated reader, which reads the raw
comment body where the line structure survives, and visible only to a human. It
is not a defect this slice fixes.

### When a fill deletes what the header line reads

The `Feature:` line is read from live state, and the elements it reads sit
**inside** the `feature-header` region — necessarily, because the export may
carry nothing the reader could not see and a template may not hold
feature-specific content outside a slot. The authoring agent is therefore obliged
to preserve `id="feature-id"` and `id="feature-name"` when it fills that region,
and that obligation is recorded where the agent will actually read it: the
artifact's own slot inventory.

A template MUST NOT assume the obligation was met. If the identifiers are gone it
falls back to the document's single top-level heading, and only if that is absent
too does the line read:

```text
Feature: not named in this document
```

**The fallback is a backstop for a violated obligation, not a licence to violate
it** — a heading is not guaranteed to carry the feature's identifier, so a fill
that drops the ids still loses information. What the fallback prevents is the
silent form: a hollow `Feature:  ` that names nothing while reading exactly like a
line that named something.

## The item reference line

Each item an export carries is named by four coordinates read from live state —
the feature, the artifact, the slot, and the item's visible label — plus the
item's anchor in a fragment-usable form. The feature and the artifact are in the
header; the per-item line carries the rest:

```text
<slot> / <item label>  (#<anchor>)
```

Two spaces precede the parenthesis.

**The anchor's value differs by capture granularity, and this is the one place
`pr-writeup` departs from its three predecessors.**

| Template | Capture attaches to | Anchor value | Label |
|---|---|---|---|
| `implementation-plan`, `module-map`, `code-approaches` | a repeated **item** | `<slot>-<item-slug>` | the item's own heading |
| `pr-writeup` | a whole **section** | `sec-<slot>` | the section heading |

`sec-<slot>` is not a new convention. It is the id each section heading already
carries for its `aria-labelledby`, reused rather than invented.

The departure buys a property no shipped template has. Because every heading sits
**outside** its marker pair, no exported coordinate other than the feature-header
identifiers can be deleted by a fill. In the three shipped templates the item
anchors sit *inside* a fill region, so a careless fill can strand them.

## Where the capture control is mounted

**A named divergence from the original contract, with its reason.** The ART-002
document required that each capture control be "mounted onto its item's anchor
and inserted immediately after it, so tab order and reading order follow the
visible order".

`pr-writeup` appends its control to the **end of its section** instead. This
honours that rule's stated rationale while departing from its letter, and the
difference is that the anchor's role changed:

- In the three shipped templates the anchor is a **list item**, so "immediately
  after it" places the control after the content being questioned. Reading order
  is preserved.
- In `pr-writeup` the anchor is the section **heading**, so "immediately after
  it" would place the control **between the heading and the content the reader
  has not read yet** — breaking the very reading-order rationale the rule exists
  to serve.

The governing principle is therefore restated once, so a future template can
apply it without re-litigating placement: **the capture control follows the
content it questions.** Where that lands depends on what the anchor is.

## Empty-state bodies

The header lines naming the feature and the artifact are still emitted. Only the
body differs.

| Template | Kind | Body |
|---|---|---|
| `implementation-plan`, `module-map` | `prompt` | `No objection was recorded. There is nothing here to act on. Do not treat this as approval.` |
| `implementation-plan`, `module-map` | `markdown` | `No objection was recorded. This record is not an approval.` |
| `code-approaches` | `prompt` | `No approach was chosen. There is nothing here to act on. Do not treat this as approval of any approach.` |
| `code-approaches` | `markdown` | `No approach was chosen. This record is not an approval of any approach.` |
| `pr-writeup` | `prompt` | `No question was recorded. There is nothing here to act on. Do not treat this as approval.` |
| `pr-writeup` | `markdown` | `No question was recorded. This record is not an approval.` |

**Why the denial is part of the text.** The realistic misreading of an empty
export is approval. A reader who pastes "nothing recorded" into a pull-request
comment has produced something that looks like a sign-off unless the text says it
is not one.

**Why `pr-writeup` varies the noun.** The shipped templates already vary it
between "objection" and "approach", so writing the artifact's own noun is the
recorded per-template pattern rather than a divergence. The sentence structure and
the denial clause are unchanged.

## The lead line

When something was recorded, one line names the kind. The header lines and the
item reference lines are identical across both kinds; this is the only line that
differs.

| Template | Kind | Lead |
|---|---|---|
| `pr-writeup` | `prompt` | `Act on each question recorded below. The value in parentheses is the anchor of the section it attaches to.` |
| `pr-writeup` | `markdown` | `Questions recorded while reading this pull-request write-up.` |

**Neither kind emits markdown syntax.** The `markdown` kind names its
**destination, not its encoding**. The downstream feedback sweep reads the raw
comment body, where the line structure survives, and adding markdown syntax would
break the one-parser property across four templates.

## Feedback

One `role="status"` region per artifact, present from load, beside the export
controls and outside every fill region. Success is reported in **text**, never by
colour or motion alone, and it names what the produced text actually carries so it
cannot imply a conclusion the text does not contain.

| State | Message |
|---|---|
| n questions, n > 1 | `Copied. 2 questions are on the clipboard.` |
| exactly one question | `Copied. 1 question is on the clipboard.` |
| no question recorded | `Copied. The text says no question was recorded.` |
| n objections, n > 1 | `Copied. 2 objections are on the clipboard.` |
| exactly one objection | `Copied. 1 objection is on the clipboard.` |
| no objection recorded | `Copied. The text says no objection was recorded.` |
| approach chosen | `Copied. Your chosen approach is on the clipboard.` |
| no approach chosen | `Copied. The text says no approach was chosen.` |
| **any failure** | `Copy failed. The text is in the field below. Select it and copy it by hand.` |

The plural rows show `2` as an illustration; the count is the live number.

## The failure path

One message for every failure mode, asserting **no cause**. The artifact cannot
distinguish a refused permission from an unfocused document from a browser policy
from an absent interface, so naming one would be a guess presented as a diagnosis.

On failure the artifact:

1. reveals the same text in a field the reader can select,
2. keeps that field **focusable and not disabled**, and moves focus to it,
3. reports the failure message above, and
4. does **not** report success.

**No deprecated second copy attempt.** Its result is ambiguous, and reporting an
uncertain success is exactly what this contract forbids.

## Invocation currency

**New under ART-003, and a correction to the three shipped implementations.**

When two exports are invoked before the first completes, the artifact reports the
outcome of the **later** invocation only. Each invocation carries a token compared
against the current one when its copy settles. A settle belonging to a superseded
invocation changes no status text, reveals no fallback text, and moves no focus.

**Both settle paths are guarded**, not only the rejection path. A slow success
resolving after a fast failure is the mirror case: it would overwrite the failure
message with "Copied" while the fallback field still holds the other kind's text.

The synchronous refusal path and the no-clipboard-interface path stay unguarded,
and an implementation must **say why**: both run inside the same synchronous turn
that issued the token, so neither can be stale.

All three templates ART-002 shipped run the same unguarded settle and none carries
a currency check. Without the guard, a rejected first copy announces a failure
that did not happen and places the first kind's payload in the fallback field
after the second kind copied successfully. `pr-writeup` MUST NOT reproduce it.

## Wording that must not name a scheme

Feedback text says "opened from a filesystem" rather than naming the local-file
scheme. The gallery scanner's URL-shaped pattern treats a script string literal
beginning with a scheme followed by a colon as an external reference and fails it.
The clipboard call itself is not a scanned call site; the wording is.

---

## Keyboard and focus

- Every export control is reachable and operable by keyboard alone, and carries
  the kit's focus-visible treatment.
- No positive tab index anywhere, and no focus trap.
- Controls serving the same function across the sections of one document are
  identified consistently — same structure, same labelling, same exposed state —
  which follows from building them all from one routine rather than emitting each
  separately.
- The capture control follows the content it questions. See **Where the capture
  control is mounted** above for what that means per capture granularity.

## Capture shapes

**Objection (`implementation-plan`, `module-map`).** A native disclosure, closed
on load, whose own control is keyboard-operable and **states in text whether that
item currently carries a note** — so a recorded objection is visible without
opening it. Inside, one labelled field.

**Question (`pr-writeup`).** The same shape, one per reader-facing section, with
the noun changed. A native disclosure, closed on load, stating in text whether
that section currently carries a question, containing one labelled field. No new
interaction is invented: a reviewer meets one interaction across the gallery.

Always-revealed fields are rejected for both: a document of six sections would
turn a thing meant to be read into a form, against the reviewing operator's actual
job.

**Selection (`code-approaches`).** A native single-choice control, grouped by a
native grouping element carrying a visible group label as its accessible name,
plus one optional labelled reason field. Selecting a second approach replaces the
first, and an export carries only the current selection.

### The absent reason

`code-approaches` has an optional reason field. When an approach is chosen and no
reason is given, the reason line reads:

```text
Reason: none given.
```

Named rather than omitted. Omitting the line would leave a reader unable to tell a
missing reason from a missing field, and requiring a reason would either strand
the reader's real conclusion or pressure filler text — there is no submission to
enforce it against.

---

## A trap that does not reach this port

The ART-002 contract closed with a warning: upstream `04-code-understanding.html`
runs an accordion script that force-closes every other `details.snippet` when one
opens, and that behaviour must not reach the capture disclosures, because it would
close a reader's in-progress field the moment they opened another.

**Considered and inapplicable here.** Upstream `17-pr-writeup.html` ships zero
`<script>` tags — six `<details>` disclosures and nothing else — so there is no
accordion behaviour to port, nothing to scope by class, and nothing to drop. It is
recorded rather than omitted so a later reader does not think it was missed.

The underlying rule still binds `pr-writeup` and is stated positively: **nothing
in the file closes a disclosure it did not open.**
