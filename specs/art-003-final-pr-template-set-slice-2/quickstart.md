# Quickstart: Validating the Annotated Diff Artifact

How to prove this slice works. Two halves: what the repository suite checks, and
what only a human opening the file can check. The second half is not optional —
the suite is Python-standard-library-only and cannot assert browser behaviour, so
the manual render is the acceptance evidence FR-046 requires.

Run everything from the worktree root. All paths are repository-relative.

---

## Prerequisites

Once per worktree:

```text
pnpm --dir docs-site install --frozen-lockfile
```

Only `docs-site/` has dependencies. The test suite needs no bootstrap.

Also once per clone, so generated paths stop text-merging:

```text
git config merge.generated.name "keep ours; regenerate after merge"
git config merge.generated.driver "exit 0"
```

---

## Read this before the first suite run

**The suite is not read-only.** `validate-plugin-payload.py` runs the real
payload builder, so **every** suite run rewrites `dist/**`. Two consequences:

- Never `git add -A` after a suite run. Stage paths by name.
- Restore a rewritten generated path with
  `git show HEAD:<path> > <path>`, not by hand-editing it.

**`--layer 4` alone overcounts.** Running Layer 4 by itself reports more failures
than the same tree reports under a full run. Judge a red against
`python3 tests/speckit-pro/run-all.py`, never against the layer alone.

**`refresh-release-artifacts.py --check` exits 1 on a correct uncommitted
regeneration.** It compares against the committed tree. That exit is not a
failure and must not be chased; it resolves on commit.

---

## Part 1 — The automated gate

### The baseline

The G0 baseline for this run is **7379 passing** (Layer 1 1447, Layer 4 5746,
Layer 5 186) — slice 1's shipped state, which is this branch's starting point. It
is recorded, not recomputed. The closeout verifies an increase against that
number, so recomputing it at a later stage destroys the comparison.

```text
python3 tests/speckit-pro/run-all.py
```

### The two layers that bind this artifact

```text
python3 tests/speckit-pro/run-all.py --layer 1
python3 tests/speckit-pro/run-all.py --layer 4
```

Layer 4 carries the two checks that matter:

- **The gallery scanner** — the single-file rule, the two canonical blocks
  byte-for-byte with their markers, the attribution header's five exact labels
  and its agreement with the catalog entry, the prohibited constructs, and the
  external-reference scan.
- **The fill-region validation** — the region rules over `feature-header` and
  `hunks`, the inventory, and `hunks`'s item anchors.

### Expect an intermediate red, and know its shape

From the moment `annotated-diff.html` exists until **both** the catalog flip and
the payload regeneration have landed, the suite is red on purpose. On slice 1
that was three families and eight failures, not one. Expect the same families
here:

| Family | Cause | Cleared by |
|---|---|---|
| Orphan artifact | the file exists while its entry still reads `planned`; the contract binds them in both directions | the catalog flip |
| Payload drift | the gallery ships inside the plugin payload, so a new template changes shipped bytes on both platforms | `python3 scripts/refresh-release-artifacts.py` |
| Stale docs reference | `test-artifact-fill-regions.py` is a tracked `.py` file under `tests/speckit-pro/` | `pnpm --dir docs-site reference:generate` |

Record the actual count the first time it is observed, and treat it as the known
set for the rest of the run. **Anything outside these families is a real failure**
and must be read rather than waited out.

### Prove the validation is not passing vacuously

This is the one result a green suite can hide. The module resolves its
per-template universe by intersecting the catalog with its floor, so a shipped
template the floor does not name is never parsed at all — a port with no regions
and no inventory would pass every check green.

```text
python3 -c '
import importlib.util, pathlib
p = pathlib.Path("tests/speckit-pro/unit/test-artifact-fill-regions.py")
spec = importlib.util.spec_from_file_location("fr", p)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print("FLOOR keys         :", sorted(m.FLOOR))
print("annotated-diff floor:", m.FLOOR.get("annotated-diff"))
print("annotated-diff lists:", m.LIST_SLOTS.get("annotated-diff"))
print("source set         :", m.SOURCE_ARTIFACTS)
'
```

Expected: `annotated-diff` present in `FLOOR` with `("hunks",)`;
`LIST_SLOTS["annotated-diff"]` equal to `("hunks",)`; and `git-diff` a member of
`SOURCE_ARTIFACTS`.

A deliberate negative check, run and then reverted: flip the catalog entry back
to `planned` with the file still present. The suite must fail as an orphan. That
proves the contract's both-directions binding is live rather than assumed.

### The title comparison no test performs

Nothing in the suite compares an artifact's displayed title against its catalog
entry's `title`. Slice 1 shipped a mismatch in case, every export opened with a
value the catalog did not carry, and the whole suite passed green. FR-010a and
SC-008 require a **comparison, not a reading**:

```text
python3 -c '
import json, pathlib, re
cat = json.loads(pathlib.Path("speckit-pro/artifact-gallery/manifest.json").read_text(encoding="utf-8"))
entry = next(t for t in cat["templates"] if t["id"] == "annotated-diff")
html = pathlib.Path("speckit-pro/artifact-gallery/templates/annotated-diff.html").read_text(encoding="utf-8")
shown = re.search(r"id=\"artifact-title\"[^>]*>([^<]*)<", html).group(1)
print("catalog :", repr(entry["title"]))
print("artifact:", repr(shown))
print("EQUAL" if shown == entry["title"] else "MISMATCH")
'
```

Record the result with the acceptance evidence. `MISMATCH` is a stop.

### Payload and docs regeneration

```text
python3 scripts/refresh-release-artifacts.py
pnpm --dir docs-site reference:generate
```

`refresh-release-artifacts.py` does **not** cover the docs reference; its own help
text says so. Then re-run the full suite. CI's `artifact-consistency` job fails
the pull request if either regeneration was skipped.

### The size measurement

Four checkpoints, each a hard gate. Full rationale in `plan.md`. The instrument
is slice 1's, reused rather than rewritten, pointed at this slice's artifact:

```text
python3 -c '
import sys,pathlib
L=pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
def sp(a,b):
    s=next(i for i,l in enumerate(L) if a in l); e=next(i for i,l in enumerate(L) if b in l); return set(range(s,e+1))
canon=sp("BRAND-KIT:START","BRAND-KIT:END")|sp("GALLERY-HEAD:START","GALLERY-HEAD:END")
n={"css":0,"js":0,"markup":0}; sty=scr=False
for i,l in enumerate(L):
    a=b=False
    if "<style" in l and "</style>" not in l: sty=True; a=True
    if "<script" in l and "</script>" not in l: scr=True; b=True
    if i not in canon: n["css" if (sty and not a) else "js" if (scr and not b) else "markup"]+=1
    if "</style>" in l: sty=False
    if "</script>" in l: scr=False
print("authored",len(L)-len(canon),"| css",n["css"],"| js",n["js"],"| markup",n["markup"])
' speckit-pro/artifact-gallery/templates/annotated-diff.html
```

| Checkpoint | Run it after | Passes when |
|---|---|---|
| **M1** | the page chrome and the diff CSS are written, **before any objection or export CSS** | `css` ≤ 150 |
| **M2** | the objection and export CSS is written | `css` ≤ 275 |
| **M3** | the export routine is written, before the sample markup | `js` ≤ 345 |
| **M4** | all markup is written, before the pull request | `authored` ≤ 750 |

On a miss: **stop**. Do not proceed to the next checkpoint. Apply the reduction
levers in `plan.md` in order, and re-measure. Above 800 authored, escalate rather
than trim.

Record all four numbers in the pull-request body with the checkpoint each was
taken at, so a reviewer reads a measurement rather than a claim.

Sanity-check the instrument against the predecessor any time you doubt it:

```text
# substitute pr-writeup.html in the command above; expect
# authored 735 | css 227 | js 334 | markup 174
```

### The declaration parser, verified by running it

The gate takes the **last** match of each phrase in a file and the first digits
within forty **non-digit** characters of it, and unions **every**
`Primary surface:` match. Verify by execution, not by eye — the trap fired three
times on slice 1:

```text
python3 -c '
import re, pathlib
d = "specs/art-003-final-pr-template-set-slice-2"
for name in ("spec.md", "plan.md"):
    t = pathlib.Path(f"{d}/{name}").read_text(encoding="utf-8")
    loc = re.findall(r"(?:projected reviewable loc|reviewable loc)[^0-9]{0,40}([0-9]+)", t, re.I)
    prod = re.findall(r"(?:projected production files|production files)[^0-9]{0,40}([0-9]+)", t, re.I)
    tot = re.findall(r"(?:projected total files|total files)[^0-9]{0,40}([0-9]+)", t, re.I)
    surf = re.findall(r"(?:primary surface|primary surfaces)[^:\n]*:\s*([A-Za-z/ ,_-]+)", t, re.I)
    print(name, "loc", loc, "prod", prod, "total", tot, "surfaces", surf)
'
```

Expected, both files: exactly one match per phrase — loc `750`, production `1`,
total `13`, one surface `docs/process`. **More than one match is a warning even
when the last one is right**, because the ordering is all that saves it.

---

## Part 2 — The manual render, which no test can replace

The artifact's whole claim is that it opens from a filesystem with no server, no
install, and nothing in the console. Only a person can check that.

### Setup

1. Open `speckit-pro/artifact-gallery/templates/annotated-diff.html` **directly in
   a browser from the filesystem**. Do not serve it. Do not use a preview pane —
   preview panes have their own policies and are not what the contract describes.
2. Open the browser's developer console **before** loading, so nothing is missed.
3. Put the browser in offline mode, or disconnect the network.

### Scenario A — read the diff with the review attached (US1)

| Step | Expected |
|---|---|
| 1. Load the file. | The page renders in full. The console reports **nothing** — no error, no warning, no failed load. |
| 2. Look at the header. | The artifact title reads `Annotated Diff`. The page says in words that the content is invented and names the invented change. |
| 3. Count the hunks. | **Two.** One carries at least one annotation; one carries none. Each has a heading with its file path and new-file line range. |
| 4. Read the clean hunk. | It **says in words** that it carries no annotation. It reads as deliberately clean, not as broken, unfinished, or awaiting content. |
| 5. Read the annotation. | It opens by naming in words the row or rows it comments on. If it is a finding it states a severity as one of `blocking`, `major`, `minor`, preceded by a fixed label naming it as a severity. |
| 6. Find an explanatory annotation. | It carries no severity, and the absence does not read as a fourth level below `minor`. |
| 7. Read the standing sentence naming the three markers. | Present, above the hunks, outside every fill region. |
| 8. Follow a jump link. | **Focus** moves to the target, not only the scroll position. Press Tab: the next stop is the one after the target, not the one after the link. |
| 9. Tab through the page. | Every interactive element is reachable in normal focus order with a visible focus indicator. Each hunk's scroll container is itself a tab stop, and arrow keys scroll it. No element is skipped and focus is never trapped. |
| 10. Narrow the window until a diff line is wider than it. | The **page** never scrolls horizontally. The overflow is contained inside the hunk's own scroll container. |
| 11. Switch the theme. | Both themes render every region legibly. No meaning is lost either way. |
| 12. Screenshot in greyscale, or print to greyscale. | Added, removed, and context rows are still tellable apart, because the state is a character in a fixed position. Every severity still reads as a word. Nothing the artifact draws is lost. |
| 13. **Select and copy one added, one removed, and one context row. Paste them into a plain-text editor.** | Each pastes as a valid unified-diff line: the marker is present and the line number is not. Repeat on the paste-and-match path — Chrome carries unselectable text there, which is why this is a paste rather than an assertion. |

Step 13 is the one FR-019c names explicitly. The state marker must be literal
text, never CSS generated content, and this is the only way to find out.

### Scenario B — hand the objections back (US2)

| Step | Expected |
|---|---|
| 1. Using the keyboard alone, open one hunk's objection control. | A labelled text field appears and receives typing. The label is a real label, not a placeholder — it stays visible once typing starts. |
| 2. Type an objection into one hunk; leave the other empty. | The disclosure's own control now states **in text** that its hunk carries an objection. It updated as you typed, not when you next toggled it. |
| 3. Close the disclosure and scan the page. | You can tell which hunk carries an objection without opening either one. |
| 4. Invoke **Copy as prompt**. | The text carries exactly the one objection written, on a reference line of the form `hunks / <file path and range>  (#hunks-<slug>-l<start>)` with **two spaces** before the parenthesis. No placeholder and no entry for the empty hunk. |
| 5. Read the exported text away from the artifact. | It names the artifact, the change, and the hunk the objection attaches to, so it can be acted on alone. |
| 6. Invoke **Copy as Markdown**. | Identical to the prompt export except for the single lead line. **No markdown syntax is emitted.** |
| 7. Edit the objection, then export immediately. | The export carries the edited text. It is derived from live state at the moment of invocation. |
| 8. Clear the field and export. | The text says in words that nothing was recorded, and **denies that this is approval**. It does not produce an empty or invented document. |
| 9. Let the clipboard be refused — common from a filesystem. | The full text appears in a selectable field, the field is focusable and not disabled and carries an accessible name, focus moves to it, and the status says the copy failed. **Nothing reports success.** The console stays silent. |
| 10. Read the failure message. | One message, covering every failure mode, asserting **no cause**. It does not name the local-file scheme. |
| 11. Read the two control labels. | "Copy as prompt" and "Copy as Markdown" — each names its destination, not its mechanism. |
| 12. Invoke both exports in quick succession. | Only the **later** invocation's outcome is reported. The earlier one changes no status text, reveals no fallback text, and moves no focus. |
| 13. Force a failure, then immediately invoke a successful export. | The success does not leave the failure's payload on screen beside a success message. The fallback field is re-hidden before each attempt. |

Steps 12 and 13 are the two with no precedent to compare against: all three
templates shipped before slice 1 fail them in both directions. They are the check
that proves the four-site currency guard survived the transplant.

### Scenario C — scripting unavailable

| Step | Expected |
|---|---|
| 1. Disable JavaScript and reload. | Both hunks, their diff rows, their annotations, the severity words, and the standing sentence are all still readable. US1 survives whole. |
| 2. Look for the export controls. | **Absent.** The export region ships hidden and the routine reveals it, so no control appears offering an action nothing can perform. |
| 3. Look for the objection controls. | Absent, because they are built at load. This is the accepted degradation, not a defect: US1 is P1 and delivers its value alone. |

### Recording the evidence

FR-046 requires the render recorded as acceptance evidence **in both themes and
with the network unavailable**, including a monochrome rendering. Capture, for
each theme:

- a screenshot of the full page,
- a screenshot of the console showing it empty,
- the exported text from a one-objection run,
- the greyscale rendering from Scenario A step 12,
- the pasted rows from Scenario A step 13.

Record alongside them, per FR-031a, the list of foreground and background
pairings the artifact actually uses, each traced to the audited row that clears
it and to the role that row permits — body text, large text, or meaningful
non-text. The audit lives in a header that does not ship and the artifact carries
only token names, so without the list FR-031 is a claim a reviewer can only take
on trust.

And record the title comparison from Part 1. It is one line, and it is the check
that caught nothing on slice 1 because nobody ran it.

---

## What a failure means

| Symptom | Almost certainly |
|---|---|
| The suite names the artifact and a block | A character of drift in an embedded canonical block. Re-copy it from its source file with its markers; never hand-edit the copy inside the artifact. |
| A fill-region check reports a region that does not exist | The inventory and the body disagree. They are bound in both directions. |
| A region reports as nested when it is not | An item without an end tag. The parser performs no implied closing. |
| An anchor reports as resolving to two items | A duplicate id. Check the slug derivation: it is the **whole** path, not the file stem, and the **start** line, not the range. |
| The suite passes but nothing was asserted about this template | The floor row is missing. Run the non-vacuity check above. |
| The gallery scanner reports an external reference in the script | A string literal named the local-file scheme. Feedback text says "opened from a filesystem". |
| CI fails `artifact-consistency` on a green local tree | A regeneration was skipped. Both of them, not just one. |
| A heading falls back to the wrong face | `--rc-font-heading` was written. The token is `--rc-font-display`, and an undefined custom property fails silently. |
| The subtle-border check fails on CSS that does not use the token | A CSS comment named the token to explain its absence. FR-032's check is a search. |
| A wide hunk pushes the page sideways | The `overflow-x: auto` is on the wrong element, or the hunk heading was placed inside the scroll container instead of outside it. |
| The status region is missing after a fill | It was placed inside a fill pair. It must sit outside every one of them. |
