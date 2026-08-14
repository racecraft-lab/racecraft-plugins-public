## Release note

```release-note
The artifact gallery now ships a Flowchart template, completing the final-PR set.
A reviewer opens it from the filesystem and reads the operational flow a change
affects — as a drawing and as prose that says the same thing — then selects any
step to see what it does and how it fails. It is a read-only artifact: it produces
nothing to carry away, and it ships no export control, because its catalog entry
declares none.
```

## What changed

ART-003 slice 3 ships `flowchart`, the last of three final-PR templates.
**This PR is stacked on slice 2 (#436) and bases on that branch, not `main`.**

| Surface | File | Change |
|---|---|---|
| The artifact | `speckit-pro/artifact-gallery/templates/flowchart.html` | new, 866 lines (408 authored, 458 canonical) |
| The catalog | `speckit-pro/artifact-gallery/manifest.json` | exactly one value: this entry's `status`, `planned` → `shipped` |
| Shared validation | `tests/speckit-pro/unit/test-artifact-fill-regions.py` | two literals: a floor row and a list-slot row. **No new source member** |

## The thing worth reviewing: it has no script

**Authored script: 0.** The whole disclosure is native. Each drawn node is a link
to its own entry; the entries form one **exclusive** disclosure group, so exactly
one is open at a time and "which node is open" is the element's own state rather
than a mark on the drawing. That removes ~80 lines the budget had provisioned and
matches `spec-explainer`'s zero rather than approaching it.

**Both zeros are proved by a negative control, not asserted.** The same search
reports 1 script block and 12 export affordances on `annotated-diff`, so a zero
here means the search binds rather than that it found nothing.

| Template | authored script | export/input affordances |
|---|---|---|
| `flowchart` | **0** | **0** |
| `spec-explainer` (comparator) | 0 | 0 |
| `annotated-diff` (control) | 1 | 12 |

The entry declares `exports: []`, which is the deliberate way to say the reader
produces nothing durable. Every other template in this gallery has an export
control, so copying by habit was the realistic failure here — and with 392 lines
of headroom, nothing would have caught it.

## Nothing carries meaning by colour

A diagram is where meaning hides most easily. Three distinctions, three
non-colour carriers:

- **Node role** — shape (rectangle, diamond, stadium) plus a written word.
- **Node state** — the disclosure's own expanded state, which is programmatic and
  singular within the group.
- **Edge kind** — stroke pattern plus a word: ordinary solid unlabelled,
  affirmative solid labelled, failure dashed labelled. Upstream dashes its failure
  edge but distinguishes its affirmative edge by hue alone; that does not survive.

One arrowhead marker with a token fill, against upstream's three with hard-coded
colours. The legend is words, carries no meaning-bearing swatch, and is
deliberately **not** a fill region — a legend a fill could rewrite could disagree
with the drawing it explains.

**The drawing carries no `role="img"`, and that is a correctness decision.** The
role makes every descendant presentational, which would remove the interactive
nodes from the accessibility tree entirely. It is named through its own `<title>`
via `aria-labelledby`, as the gallery's other diagram does.

## The list-slot row, and why

`nodes` gets a list-slot row for a **stronger** reason than the other two slices
had. The design concept left this open because nothing durable is produced, so no
export anchors to a node — true, and not the deciding fact. The check asserts that
a **fragment resolves**, and this artifact's entire disclosure is fragment
resolution. A later fill emitting a node without its anchor would silently break
the drawing's links. Seven links, zero unresolved, verified.

## Scope budget

**408 reviewable production lines against a declared 460 and an 800 block** — 392
under the block. Decomposed 209 CSS, **0 script**, 199 markup.

The CSS checkpoint earned its place: the first measurement came in at **296**
against a 210 ceiling, an 86-line overrun caught with 200 lines written rather
than 460. Three rounds of cuts reached 209 — comment prose halved, two rules
merged, a caret replacement dropped for the native marker. The ceiling is
reachable but only by spending nothing on decoration.

## Verification

- Full suite **7381/7381**, one above the 7380 baseline. The increase is the
  list-slot check binding this template for the first time.
- `refresh-release-artifacts.py --check` — generated artifacts match the source
  tree.
- Both canonical blocks byte-identical.
- Title compared to the catalog entry by a **run, not a reading** — `Flowchart` on
  both sides.
- Seven in-document node links, zero unresolved.
- The **manual render ran** against the shipped bytes on a real `file://` URL in
  Chrome 151: **51/51**, including the fragment reveal on all seven nodes, which
  is the property this slice refused to claim without one.

## Known gaps

1. **Chrome only.** The manual render has now been run, against the shipped bytes
   on a real `file://` URL: **51 of 51 checks pass**, covering console silence,
   both themes, network unavailable, storage refused, scripting unavailable, the
   monochrome rendering, the sixteen-stop tab order with a visible indicator at
   every stop, and zero clipboard calls across every activation. It ran on Chrome
   151 only, and `<details name>` exclusive grouping is exactly the kind of
   behaviour that differs between engines, so Firefox and WebKit are unverified.
2. **The fragment reveal is confirmed, on Chrome.** Activating each of the seven
   node links by keyboard opens that node's closed `<details>`, leaves exactly one
   open, sets `:target`, and scrolls it into view — seven for seven. The
   zero-script property therefore holds in practice and not only on paper. The
   caveat in gap 1 applies: this is one engine. **Worst case elsewhere it degrades
   rather than breaks** — the link still lands the reader on the right node's
   summary and one keystroke opens it.
3. **No check asserts an artifact's title matches its catalog entry** — how slice
   1's defect reached review with a green suite.
4. **No check reads a catalog entry's `exports` against the artifact**, which is
   what makes this slice's two zeros worth proving by control.
5. **The five shipped scroll containers remain keyboard-inaccessible** (slice 2's
   finding; this artifact adds none).
6. **The shipped payload documents no fill-region grammar.**

## Non-goals

- Generation and authoring logic, and the ready flip. That is ART-010.
- Any export affordance whatsoever — the entry declares none.
- Fixing the currency defect or the scroll-container gap in earlier templates.
- Any change to the contract document, the brand kit, the head block, or any
  catalog value other than this entry's own `status`.

## Rollback

Revert the commit range. The catalog value and the artifact file must move
together — the contract binds status and file presence in both directions.
