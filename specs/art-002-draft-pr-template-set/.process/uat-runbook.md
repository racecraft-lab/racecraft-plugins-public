# Acceptance Runbook: Draft-PR Template Set (ART-002)

The manual half of this feature's verification. Everything Python can check is
checked by `tests/speckit-pro/unit/test-artifact-fill-regions.py` and
`tests/speckit-pro/unit/test-artifact-gallery.py`; what follows is what only a
browser and a person can confirm. No automated browser is introduced (FR-038).

**All four templates are covered.** Sets A and B ship in slice 1
(`implementation-plan`, `spec-explainer`); Sets C and D in slice 2
(`code-approaches`, `module-map`).

## Before you start

Open each file **directly from the filesystem** — no server, no install. Have the
developer console visible from the first load, because step 1 is the only step
that can catch an error thrown during parsing.

| Template | Path |
|---|---|
| Implementation Plan | `speckit-pro/artifact-gallery/templates/implementation-plan.html` |
| Spec Explainer | `speckit-pro/artifact-gallery/templates/spec-explainer.html` |
| Code Approaches | `speckit-pro/artifact-gallery/templates/code-approaches.html` |
| Module Map | `speckit-pro/artifact-gallery/templates/module-map.html` |

Both ship worked-example content describing one invented feature,
**`NIMBUS-101` — Offline Draft Sync**. That identifier appears in no roadmap this
repository uses, which is how you confirm the content is sample content by
reading rather than by judging tone.

**Target:** one template's pass completes in under ten minutes.

---

## Set A — Implementation Plan

### A1. Open the file with the console visible

**Do:** open `implementation-plan.html` from the filesystem.

**Expect:** every section renders — the header, the at-a-glance strip, the
phases, the data-flow drawing, the mockups, the risk register, and the task
inventory. The console is **empty**: no error, no failed load, no missing
content. A single font request may appear; nothing else may.

### A2. Reload with the network disconnected

**Do:** disconnect the network. Reload.

**Expect:** the document is still complete and every control still works. The
**only** visible difference is the typeface. If any content, control, or layout
changes, that is a failure — the artifact is required to be self-contained.

### A3. Use the theme control, then reload

**Do:** activate the theme control. Reload.

**Expect:** the theme changes on activation. After reload the choice persists —
**or**, if the browser refused storage for a local file, the control still works
for the session and reports no error. Persistence is what may degrade here; the
control itself may not.

### A4. Tab from the top of the document to the bottom

**Do:** press Tab repeatedly from the top, using no pointer at all.

**Expect:** focus reaches the theme control, every phase's objection disclosure,
every objection field, and both export controls. Each shows a **visible focus
indicator**. Focus never jumps out of the document's normal reading order, and
each disclosure's control is reached immediately after its own phase — not
collected at the end.

### A5. Read the sample content in every region

**Do:** read each of the seven regions.

**Expect:** every one shows worked-example content. No region is an empty frame.

### A5a. Confirm the content announces itself as sample

**Do:** read the header.

**Expect:** the identifier `NIMBUS-101` is visible, and the header says **in the
rendered document** that what follows is sample content awaiting a fill. The
slot inventory is an HTML comment a browsing reader never sees, so this
statement is the only one that reaches them.

### A5b. Read the text beside the export controls

**Do:** look at the two lines next to "Copy as prompt" and "Copy as Markdown".

**Expect:** one line says what each export is for — the prompt for pasting into a
coding agent, the Markdown for a pull-request comment. One line says recorded
input is **not saved** and is lost on reload. Both must be present; the labels
alone name a format, not a destination.

### A6. Record an objection, then collapse the disclosure

**Do:** open the disclosure on one phase, type an objection, collapse it again.

**Expect:** the disclosure's own control now states **in text** that the item
carries a note, without being opened.

**Also check:** type only spaces into a second phase's field. Its control must
**not** report a note — whitespace alone is not an objection.

### A7. Open a second disclosure

**Do:** with the first still open, open a second phase's disclosure.

**Expect:** the first stays open and its text is intact. Opening one must never
close another. This is the upstream accordion behaviour the port deliberately
does not carry.

### A8. Invoke each export with two objections recorded

**Do:** with objections on two different phases, invoke "Copy as prompt", then
"Copy as Markdown". Paste each somewhere you can read it.

**Expect:** the text opens with two header lines naming the artifact
(`Implementation Plan`) and the feature (`NIMBUS-101 Offline Draft Sync`). It
carries **one line per recorded objection** and no line, placeholder, or count
for any phase left empty. Each line reads
`phases / <the phase's visible label>  (#phases-<slug>)`, with two spaces before
the parenthesis, and the anchor visibly derives from the label you can see. The
status region says `Copied. 2 objections are on the clipboard.`

### A9. Reload, record nothing, invoke each export — **timed, SC-005**

**Do:** reload. Record nothing. Invoke each export.

**Expect, verbatim:**

- prompt → `No objection was recorded. There is nothing here to act on. Do not treat this as approval.`
- Markdown → `No objection was recorded. This record is not an approval.`

Both still name the artifact and the feature. Neither names any phase. **Neither
states a conclusion, and neither shows a value you could not see in the rendered
document.** That last sentence is SC-005; judge it and record pass or fail
explicitly rather than skimming.

### A10. Carry a conclusion out in one action — **timed, SC-002**

**Do:** with an objection recorded, invoke each export the entry declares and
paste it into its destination. Time it.

**Expect:** under **thirty seconds**, in **every** destination the entry declares,
with **nothing retyped**. If you find yourself retyping any part of the
objection, that is a failure regardless of the elapsed time.

### A11. Provoke a clipboard refusal

**Do:** deny clipboard permission, or open the file in a context where the
browser refuses it, then invoke an export.

**Expect:** the message `Copy failed. The text is in the field below. Select it
and copy it by hand.` — asserting **no cause**. The same text appears in a
selectable field that **receives focus** and is not disabled. No success is
reported. The field's own label says what it holds.

### A12. Reload and confirm nothing was kept

**Do:** reload after recording an objection.

**Expect:** the objection is gone and every disclosure is closed. This is
intended — the line from A5b is what warns the reader in advance.

### A13. Ask for reduced motion

**Do:** turn on the operating system's reduced-motion setting. Expand a
disclosure and switch the theme.

**Expect:** nothing animates and nothing transitions.

### A14. Read the data-flow drawing with assistive technology

**Do:** inspect the drawing with a screen reader, or with the accessibility
inspector.

**Expect:** the drawing has an **accessible name**, and the information it
conveys is **also available as text outside the drawing** and inside the same
region. The dashed edge's caption states its convention in words.

### A15. View the document without colour

**Do:** print to greyscale, or apply a monochrome filter.

**Expect:** the risk register's severity is still readable — carried by text,
shape, or position, not by hue alone. The inverted persistence node in the
drawing is still distinguishable from its siblings.

### A16. Confirm the heading outline

**Do:** navigate by heading.

**Expect:** exactly one top-level heading, and no skipped rank. The outline you
navigate matches the document you see.

---

## Set B — Spec Explainer

This template is **read-only by construction**. Several steps below are
deliberately checks for *absence*; a control appearing where one is not expected
is a failure, not a bonus.

### B1. Open the file with the console visible

**Expect:** every section renders — header, TL;DR, goals, non-goals, acceptance
criteria, and the clarification FAQ. Console empty.

### B2. Reload with the network disconnected

**Expect:** complete document, working controls, typeface the only difference.

### B3. Use the theme control, then reload

**Expect:** as A3. The theme control is the only interactive control this
document carries besides the acceptance-criteria folds.

### B4. Tab from top to bottom

**Expect:** focus reaches the theme control and each acceptance-criteria
disclosure, each with a visible focus indicator, in reading order. **Focus
reaches no field, no button, and no copy affordance**, because there are none.

### B5. Read the sample content in every region

**Expect:** all six regions carry worked-example content. None is an empty frame.

### B5a. Confirm the content announces itself as sample

**Expect:** `NIMBUS-101` is visible and the header says in the rendered document
that what follows is sample content awaiting a fill.

### B6. Expand and re-collapse the acceptance criteria by keyboard alone

**Do:** reach a criterion's control by Tab and operate it with the keyboard only.

**Expect:** it expands and re-collapses, and the control reports its own state.
Unlike Set A's disclosures it carries **no note text** — there is nothing here
for a reader to record.

### B7. Inspect the whole document for capture and export surfaces

**Do:** look for any export control, any copy affordance, any field that records
reader input, and any script of the template's own.

**Expect:** **none of them exist.** This is the structural read-only property:
the document is incapable of capturing anything, rather than carrying controls
judged to be harmless. The only script in the file is the shared gallery head
block.

### B8. Ask for reduced motion

**Expect:** nothing animates and nothing transitions when a fold expands or the
theme switches. The upstream source animated its caret; this port carries no
animation at all, so there is nothing to suppress.

### B9. Confirm the heading outline

**Expect:** exactly one top-level heading, no skipped rank.

---

---

## Set C — Code Approaches

The template whose reader produces a **choice** rather than an objection. Its
export carries the current selection only, never a history.

### C1. Open the file with the console visible

**Expect:** every section renders — the header, the approaches compared side by
side with their trade-offs, and the recommendation. Console empty.

### C2. Reload with the network disconnected

**Expect:** complete document, working controls, typeface the only difference.

### C3. Use the theme control, then reload

**Expect:** as A3 — the theme changes, and the choice persists or the control
still works for the session with no error reported.

### C4. Tab from top to bottom

**Expect:** focus reaches the theme control, the choice control for each
approach, the reason field, and both export controls, each with a visible focus
indicator, in reading order. No positive tab order, no trap.

### C5. Read the sample content in every region

**Expect:** all three regions carry worked-example content. None is an empty
frame. `NIMBUS-101` is visible and the header says in the rendered document that
what follows is sample content awaiting a fill.

### C5a. Read the text beside the export controls

**Expect:** one line saying what each export is for, and one saying recorded
input is not saved and is lost on reload.

### C6. Confirm the choice control is grouped and labelled

**Do:** inspect the group of choices with a screen reader, or with the
accessibility inspector.

**Expect:** the choices are a single named group whose accessible name is the
visible legend **Which approach should this change take?** — the *question*, not
a list of the approaches. Each individual choice announces its own approach's
label as well as the shared control text.

### C7. Make a choice by keyboard alone, then change it

**Do:** reach the group by Tab, move through the options with the arrow keys,
and commit a selection without a pointer. Then select a different approach.

**Expect:** the selection can be made with no pointer, the chosen approach is
reported **in text**, and choosing a second **replaces** the first rather than
adding to it.

### C8. Export with an approach chosen and a reason given

**Expect:** the text opens with `Artifact: Code Approaches` and a `Feature:` line
naming `NIMBUS-101 Offline Draft Sync`. It names the chosen approach with its
anchor in the form `approaches / <the approach's visible label>  (#approaches-<slug>)`,
and carries your reason. The status region says
`Copied. Your chosen approach is on the clipboard.`

### C9. Export with an approach chosen and **no** reason

**Expect:** the reason line reads exactly `Reason: none given.` — named rather
than omitted, so you can tell a missing reason from a missing field.

### C10. Reload, choose nothing, invoke each export — **timed, SC-005**

**Expect, verbatim:**

- prompt → `No approach was chosen. There is nothing here to act on. Do not treat this as approval of any approach.`
- Markdown → `No approach was chosen. This record is not an approval of any approach.`

Both still name the artifact and the feature. **Neither names any approach and
neither states a conclusion.** Record this one explicitly as pass or fail.

### C11. Carry a conclusion out in one action — **timed, SC-002**

**Expect:** under **thirty seconds**, in every destination the entry declares,
with **nothing retyped**.

### C12. Provoke a clipboard refusal

**Expect:** `Copy failed. The text is in the field below. Select it and copy it
by hand.` — asserting no cause. The same text in a selectable field that
receives focus. No success reported.

### C13. View the trade-off table without colour

**Do:** print to greyscale, or apply a monochrome filter. Then mentally lift a
single row out of the table.

**Expect:** the trade-off still reads. The carrier is the persistent column
heading and the fixed column position, not hue — so a row read in isolation is
still unambiguous.

### C14. Ask for reduced motion

**Expect:** nothing animates and nothing transitions.

### C15. Confirm the heading outline

**Expect:** exactly one top-level heading, no skipped rank.

---

## Set D — Module Map

The closest sibling to Set A: same objection capture, same two exports, plus a
drawing whose distinguished path must survive without colour.

### D1. Open the file with the console visible

**Expect:** every section renders — the header, the summary, the module drawing,
the module walkthrough, and the key files. Console empty.

### D2. Reload with the network disconnected

**Expect:** complete document, working controls, typeface the only difference.

### D3. Use the theme control, then reload

**Expect:** as A3.

### D4. Tab from top to bottom

**Expect:** focus reaches the theme control, every module's objection
disclosure, every objection field, and both export controls, each with a visible
focus indicator, each disclosure immediately after its own module rather than
collected at the end.

### D5. Read the sample content in every region

**Expect:** all five regions carry worked-example content. `NIMBUS-101` visible,
and the header says in the rendered document that this is sample content
awaiting a fill.

### D5a. Read the text beside the export controls

**Expect:** the two lines, as A5b.

### D6. Record an objection on one module, then collapse it

**Expect:** the disclosure's own control now states **in text** that the module
carries a note, without being opened. Whitespace alone must **not** count —
type only spaces into a second module's field and confirm its control still
reports no note.

### D7. Open a second module's disclosure — **the accordion check**

**Do:** with an objection typed into one module's disclosure and that disclosure
open, open a second module's disclosure.

**Expect:** the first **stays open and its text is intact.** This is the trap the
port had to remove: upstream's script force-closes every other disclosure when
one opens, which would destroy a reader's in-progress objection. If the first
closes, that behaviour survived the port and this is a failure.

### D8. Invoke each export with two objections recorded

**Expect:** two header lines naming `Module Map` and
`NIMBUS-101 Offline Draft Sync`; one line per recorded objection reading
`modules / <the module's visible label>  (#modules-<slug>)` with two spaces
before the parenthesis; and **no line, placeholder, or count** for any module
left empty. Status region: `Copied. 2 objections are on the clipboard.`

### D9. Reload, record nothing, invoke each export — **timed, SC-005**

**Expect, verbatim:**

- prompt → `No objection was recorded. There is nothing here to act on. Do not treat this as approval.`
- Markdown → `No objection was recorded. This record is not an approval.`

Names no module. States no conclusion. Record explicitly.

### D10. Carry a conclusion out in one action — **timed, SC-002**

**Expect:** under **thirty seconds**, every declared destination, nothing
retyped.

### D11. Provoke a clipboard refusal

**Expect:** the one cause-neutral message, the selectable focused field, no
success reported.

### D12. Read the module drawing with assistive technology

**Expect:** the drawing has an **accessible name**, and the information it
conveys is **also available as text outside the drawing** and inside the same
region. Upstream marked this drawing so assistive technology read it as a single
image, hiding every label inside it — that marking must not have survived, so
confirm the labels are reachable.

### D13. View the drawing without colour — **SC-010, the one that matters most here**

**Do:** print to greyscale, or apply a monochrome filter.

**Expect:** the path the change runs through is **still identifiable**, carried
by a heavier boundary and by the visible `ON PATH` text tag. Colour carries none
of that meaning on its own. If you cannot tell the distinguished path from the
rest in monochrome, this is a failure.

### D14. Ask for reduced motion

**Expect:** nothing animates and nothing transitions when a disclosure opens or
the theme switches.

### D15. Reload and confirm nothing was kept

**Expect:** every objection gone, every disclosure closed. Intended; D5a is the
warning.

### D16. Confirm the heading outline

**Expect:** exactly one top-level heading, no skipped rank.

---

## Recording the result

For each set, record every step as pass or fail with what you actually observed.
A step recorded as "fine" is not a result. The two timed steps (A9 and A10) carry
a number as well as a verdict.

Anything that fails belongs in the pull request as a known gap before merge, not
in a follow-up nobody has filed.
