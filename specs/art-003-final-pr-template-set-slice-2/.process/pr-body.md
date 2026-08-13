## Release note

```release-note
The artifact gallery now ships an Annotated Diff template. A reviewer opens it
from the filesystem and reads the diff hunk by hunk with the review's own findings
attached, each finding's severity stated as a word rather than a colour, and jump
links between them. They can attach an objection to any hunk and copy every
objection out of the page, either as a pull-request comment or as an instruction
for a coding agent.
```

## What changed

ART-003 slice 2 ships `annotated-diff`, the second of three final-PR templates.
**This PR is stacked on slice 1 (#435) and bases on that branch, not `main`.**

| Surface | File | Change |
|---|---|---|
| The artifact | `speckit-pro/artifact-gallery/templates/annotated-diff.html` | new, 812 lines (724 authored, 458 canonical) |
| The catalog | `speckit-pro/artifact-gallery/manifest.json` | exactly one value: this entry's `status`, `planned` → `shipped` |
| Shared validation | `tests/speckit-pro/unit/test-artifact-fill-regions.py` | three literals: a floor row, a list-slot row, and one closed-set member |

Everything else in the diff is generator output.

## Review order

Authored markup and diff CSS first, then the export routine, then the validation
and catalog changes. The 458 canonical lines are byte-verified copies of
`brand-kit.css` and `theme-toggle.html`, identical across all six templates.

## Three things worth a reviewer's attention

**The diff carries no colour.** A unified diff is conventionally rendered with
hue alone — added green, removed red. This one cannot. Row state rides on a
literal `+`, `-`, or space in a fixed cell, present as **text in the document**
rather than as CSS generated content, because generated content reaches the
clipboard in some engines and not others; a pasted row would silently lose its
state in Firefox. The line-number cell alone is unselectable, so a copied row
pastes as a valid unified-diff line. Severity is one style rule with **no
selector branching on which word it is** — a branch is exactly where colour
re-enters as the ranking carrier, which is what upstream does.

**Both scroll containers are keyboard-scrollable, and none of the five already
shipped is.** Every existing `overflow-x: auto` container in this gallery lacks
`tabindex="0"`, so none is scrollable by keyboard in Safari and every one is
flagged by axe's `scrollable-region-focusable`. This is the first that carries
the attribute, a role, and an accessible name. Repairing the other five is not in
this PR.

**The currency guard was proved by breaking it.** The export routine is a
deliberate hybrid: slice 1's shell and its four-site guard, `module-map`'s
live-anchor item derivation, and explicitly **not** `module-map`'s settle path,
which carries no token. With all four guard sites neutered, the harness fails in
both directions — a superseded failure reveals the other kind's payload and
steals focus, and a slow success overwrites a later failure message. Restored, 33
assertions pass against the shipped bytes.

## Scope budget

**724 reviewable production lines against a declared 750 and an 800 block** — 26
under its own declaration. Decomposed 259 CSS, 344 JS, 121 markup.

Four checkpoints, each with a stop rule. The two CSS checkpoints fired before any
export work; **M1 missed twice** (167, then 151 against 150) and both misses were
comment prose running past the enumerated block sizes, not design — holding
comments to the enumeration closed the whole gap with no requirement weakened.
**M3 is a JavaScript checkpoint slice 1 did not have**, added because slice 1
declared its routine at 288 calling that "a floor rather than an estimate" and
shipped 334, a 16% overrun absorbed only because CSS and markup came in under
together. M3 landed at 344 against 345 — inside the gate with one line to spare.

## Verification

- Full suite **7380/7380**, one above the 7379 baseline.
- Regeneration touched **24 paths** — both payload mirrors, three payload proofs,
  and every cache fixture — which is the generator's signature, not a test-suite
  side effect. All eight copies `cmp`-identical to source.
- Both canonical blocks byte-identical, drift 0.
- The fill-region checks bind this template and return nothing. Proved
  non-vacuous both ways: with the entry `planned` the negative check fails by
  name; flipped, it passes.
- The artifact title was compared to its catalog entry by a **run, not a reading**
  — `Annotated Diff` on both sides, zero characters of difference. Slice 1 shipped
  this wrong in sentence case and nothing asserts it.

## Known gaps

1. **Nine acceptance items need a person at a browser** and are not verified here:
   console silence on load, the actual paste of an added, removed and context row
   on both clipboard paths, fragment navigation moving focus, tab order and focus
   indicator, no horizontal page scroll, both themes, greyscale legibility,
   scripting-disabled degradation, and the screenshots. Chrome automation refuses
   `file://` navigation, and serving over `http://` would be a false pass because
   it changes the clipboard permission model so the failure path never fires.
2. **One concurrency assertion cannot discriminate.** Checking only the status
   text passes even with the guard removed, because both settles carry the same
   delay and the later write lands last regardless. Only the fallback reveal and
   the focus move detect a missing guard. A reviewer testing status text alone
   would get a false pass.
3. **The five shipped scroll containers remain keyboard-inaccessible.**
4. **No check asserts an artifact's title matches its catalog entry**, which is
   how slice 1's defect reached review with a green suite.
5. **No check reads a catalog entry's `exports` against the artifact.**
6. **The shipped payload documents no fill-region grammar.**
7. **`git-diff` is the first non-filename member of the closed source set.** It
   was added over a recorded dissent: all six existing members are filenames, and
   `git-diff` matches the slot-name grammar while none of them does. Resolved
   toward honesty because no filename is honest here — no file exists, and
   `diff.patch` would name one no phase writes.

## Non-goals

- `flowchart`. Slice 3, a separate branch and PR.
- Generation and authoring logic, and the ready flip. That is ART-010.
- Fixing the currency defect or the scroll-container gap in the shipped templates.
- Any change to the contract document, the brand kit, the head block, or any
  catalog value other than this entry's own `status`.

## Rollback

Revert the commit range. The catalog value and the artifact file must move
together — the contract binds status and file presence in both directions.
