# Contract: The Export Payload

Three templates carry export controls, each with its own copy of the code that
builds them. There is no shared runtime, so this table is the shared thing: the
strings are pinned here once, and every implementation and the acceptance runbook
check against this file rather than against each other.

The strings below are **literal**. They are stated here rather than left to the
implementation because an approximation of "this is not an approval" is not the
same sentence, and the whole point of the wording is that a reader cannot
misread it.

Which kinds an artifact carries is declared by its routing catalog entry, never
chosen by the author:

| Template | `exports` | Controls |
|---|---|---|
| implementation-plan | `["prompt","markdown"]` | Copy as prompt, Copy as Markdown |
| module-map | `["prompt","markdown"]` | Copy as prompt, Copy as Markdown |
| code-approaches | `["prompt","markdown"]` | Copy as prompt, Copy as Markdown |
| spec-explainer | `[]` | **none**, and no reader-input field of any kind |

Exactly one control per declared kind, labelled by destination — "Copy as prompt",
"Copy as Markdown" — never by mechanism.

---

## What every export carries

- **The reader's conclusion, not the document's content.** A prompt export from a
  plan review says which phase to reorder and why; it does not restate the plan.
- **Enough context to act on alone.** The person pasting it has left the artifact
  behind. Every export names the feature and the artifact it came from, in a
  header line, in every state including the empty one.
- **Only what the reader produced.** An export lists only the items the reader
  recorded against. No line, no placeholder, and no count for an item left empty.
- **Nothing the reader could not see.** No inline data the artifact was built from
  but did not display.
- **Live state.** Read at the moment of invocation, never a value written into the
  file when it was authored.

## The header line

Every export opens with the same two lines, in every state including the empty
one, both read from live state:

```text
Artifact: <artifact title>
Feature: <feature id> <feature name>
```

Pinned for the same reason the empty-state bodies are: three templates emit this
from three separate copies of the code, so a form left to each of them is a form
that drifts. The artifact title is the one its catalog entry carries. The feature
identifier is what lets a reader who has left the document find the spec again,
which is the obligation `SPA-CONTRACT.md` states as naming "the artifact, the
spec, and the location the conclusion attaches to".

## The item reference line

Each item an export carries is named by four coordinates read from live state —
the feature, the artifact, the slot, and the item's visible label — plus the
item's anchor in a fragment-usable form. The feature and the artifact are in the
header; the per-item line carries the rest:

```text
<slot> / <item label>  (#<anchor>)
```

The anchor is valued `<slot>-<item-slug>`. Two spaces precede the parenthesis.

## Empty-state bodies

The header lines naming the feature and the artifact are still emitted. Only the
body differs.

| Template | Kind | Body |
|---|---|---|
| implementation-plan, module-map | `prompt` | `No objection was recorded. There is nothing here to act on. Do not treat this as approval.` |
| implementation-plan, module-map | `markdown` | `No objection was recorded. This record is not an approval.` |
| code-approaches | `prompt` | `No approach was chosen. There is nothing here to act on. Do not treat this as approval of any approach.` |
| code-approaches | `markdown` | `No approach was chosen. This record is not an approval of any approach.` |

**Why the denial is part of the text.** The realistic misreading of an empty
export is approval. A reader who pastes "nothing recorded" into a pull-request
comment has produced something that looks like a sign-off unless the text says it
is not one.

## The absent reason

`code-approaches` has an optional reason field. When an approach is chosen and no
reason is given, the reason line reads:

```text
Reason: none given.
```

Named rather than omitted. Omitting the line would leave a reader unable to tell a
missing reason from a missing field, and requiring a reason would either strand
the reader's real conclusion or pressure filler text — there is no submission to
enforce it against.

## Feedback

One `role="status"` region per artifact, present from load, beside the export
controls and outside every fill region. Success is reported in **text**, never by
colour or motion alone, and it names what the produced text actually carries so it
cannot imply a conclusion the text does not contain.

| State | Message |
|---|---|
| n objections, n > 1 | `Copied. 2 objections are on the clipboard.` |
| exactly one objection | `Copied. 1 objection is on the clipboard.` |
| no objection recorded | `Copied. The text says no objection was recorded.` |
| approach chosen | `Copied. Your chosen approach is on the clipboard.` |
| no approach chosen | `Copied. The text says no approach was chosen.` |
| **any failure** | `Copy failed. The text is in the field below. Select it and copy it by hand.` |

The plural row shows `2` as an illustration; the count is the live number.

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
- Controls serving the same function across the items of one list are identified
  consistently — same structure, same labelling, same exposed state — which
  follows from building them all from one routine rather than emitting each
  separately.
- Each capture control is mounted onto its item's anchor and inserted immediately
  after it, so tab order and reading order follow the visible order.

## Capture shapes

**Objection (implementation-plan, module-map).** A native disclosure, closed on
load, whose own control is keyboard-operable and **states in text whether that
item currently carries a note** — so a recorded objection is visible without
opening it. Inside, one labelled field.

Always-revealed fields are rejected: a list of five or six items would turn a
document meant to be read into a form, against the reviewing operator's actual
job.

**Selection (code-approaches).** A native single-choice control, grouped by a
native grouping element carrying a visible group label as its accessible name,
plus one optional labelled reason field. Selecting a second approach replaces the
first, and an export carries only the current selection.

**A trap this port must avoid.** Upstream `04-code-understanding.html` runs an
accordion script that force-closes every other `details.snippet` when one opens.
That behavior must not reach the objection disclosures — it would close a reader's
in-progress field the moment they opened another. Scope it by class, or drop it.
