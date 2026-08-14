# Quickstart: Validating the PR Write-up Artifact

How to prove this slice works. Two halves: what the repository suite checks, and
what only a human opening the file can check. The second half is not optional —
the suite is Python-standard-library-only and cannot assert browser behaviour, so
the manual render is the acceptance evidence FR-042 requires.

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

## Part 1 — The automated gate

### Baseline before you start

```text
python3 tests/speckit-pro/run-all.py
```

The G0 baseline for this run is **7378 passing** (Layer 1 1447, Layer 4 5745,
Layer 5 186). Do not recompute it at a later stage; the closeout verifies an
increase against that number.

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
- **The fill-region validation** — R1 through R7 over the seven regions, the
  inventory, and `file-by-file`'s item anchors.

### Prove the validation is not passing vacuously

This is the one result a green suite can hide. The module resolves its
per-template universe by intersecting the catalog with its floor, so a shipped
template the floor does not name is never parsed at all — a port with no regions
and no inventory would pass every check green.

Confirm the floor row is present and the template is actually being asserted
about:

```text
python3 -c '
import importlib.util, pathlib
p = pathlib.Path("tests/speckit-pro/unit/test-artifact-fill-regions.py")
spec = importlib.util.spec_from_file_location("fr", p)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print("FLOOR keys      :", sorted(m.FLOOR))
print("pr-writeup floor:", m.FLOOR.get("pr-writeup"))
print("pr-writeup lists:", m.LIST_SLOTS.get("pr-writeup"))
print("source set      :", m.SOURCE_ARTIFACTS)
'
```

Expected: `pr-writeup` present in `FLOOR` with the roadmap's four
(`motivation`, `before-after`, `file-by-file`, `implementation-notes`);
`LIST_SLOTS["pr-writeup"]` equal to `("file-by-file",)`; and
`implementation-notes.md` a member of `SOURCE_ARTIFACTS`.

A deliberate negative check, run and then reverted: flip the catalog entry back
to `planned` with the file still present. The suite must fail as an orphan. That
proves the contract's both-directions binding is live rather than assumed.

### Payload and docs regeneration

The gallery ships inside the plugin payload, so a new template changes shipped
bytes on both platforms:

```text
python3 scripts/refresh-release-artifacts.py
```

`test-artifact-fill-regions.py` is a tracked `.py` file under
`tests/speckit-pro/`, so its change restales the generated docs reference. That
surface is **not** covered by the script above:

```text
pnpm --dir docs-site reference:generate
```

Then re-run the full suite. CI's `artifact-consistency` job fails the pull
request if either regeneration was skipped.

### The size measurement

Three checkpoints, each a hard gate. Full rationale in `plan.md`.

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
' speckit-pro/artifact-gallery/templates/pr-writeup.html
```

| Checkpoint | Run it after | Passes when |
|---|---|---|
| **M1** | the six sections' CSS is written, before any question or export CSS | `css` ≤ 150 |
| **M2** | the question and export CSS is written | `css` ≤ 247 |
| **M3** | the export routine and all markup are written | `authored` ≤ 758 |

Record all four numbers in the pull-request body with the checkpoint each was
taken at.

Sanity-check the instrument against the comparator any time you doubt it:

```text
# substitute spec-explainer.html in the command above; expect
# authored 315 | css 169 | js 0 | markup 146
```

---

## Part 2 — The manual render, which no test can replace

The artifact's whole claim is that it opens from a filesystem with no server, no
install, and nothing in the console. Only a person can check that.

### Setup

1. Open `speckit-pro/artifact-gallery/templates/pr-writeup.html` **directly in a
   browser from the filesystem**. Do not serve it. Do not use a preview pane —
   preview panes have their own policies and are not what the contract describes.
2. Open the browser's developer console **before** loading, so nothing is missed.
3. Put the browser in offline mode, or disconnect the network. The contract
   requires the artifact to stay completely readable with every control operable,
   with typeface substitution the only visible difference.

### Scenario A — read the finished change (US1)

| Step | Expected |
|---|---|
| 1. Load the file. | The page renders in full. The console reports **nothing** — no error, no warning, no failed load. |
| 2. Look for the six sections. | `motivation`, `before-after`, `file-by-file`, `non-goals`, `verification`, `implementation-notes` each appear as their own titled section, each carrying representative sample content. The page header says in words that the content is invented and names the invented feature. |
| 3. Read `implementation-notes`. | Each note appears under the task identifier it was recorded against, in append order. Three entries, with the retry pair **non-adjacent**. The standing intro sentence is present above the region, phrased as the region's rule rather than as a claim about the entries below it. |
| 4. Read the retry pair. | Both entries render. Neither is visually grouped with the other and neither carries an attempt ordinal. The second entry says what the re-run changed, so the pair reads as history rather than as a line printed twice. |
| 5. Read `verification`. | Two items, **one passed and one pending**, each state reading as a **word**. Nothing depends on a glyph's fill. |
| 5a. Read `file-by-file`. | Three items — a production file, its test, and a config or manifest value — each carrying its own `file-by-file-<slug>` anchor. |
| 5b. Read `before-after`. | Each panel's statement opens with the word naming it, so which is which survives the stacked narrow-viewport layout and a greyscale print. |
| 6. Switch the theme. | Both themes render every section legibly. No meaning is lost either way. |
| 7. Tab through the page. | Every interactive element is reachable in normal focus order with a visible focus indicator. No element is skipped and focus is never trapped. |
| 8. Screenshot in greyscale, or print to greyscale. | Every distinction the artifact draws survives. Nothing is carried by hue alone. |

### Scenario B — hand the questions back (US2)

| Step | Expected |
|---|---|
| 1. Using the keyboard alone, open one section's question control. | A labelled text field appears and receives typing. The disclosure states in text whether that section currently carries a question. |
| 2. Type a question into exactly two of the six sections; leave four empty. | — |
| 3. Invoke **Copy as prompt**. | The text carries exactly the two questions written, each on a reference line of the form `<slot> / <section heading>  (#sec-<slot>)` with **two spaces** before the parenthesis. No placeholder and no entry for the four empty sections. |
| 4. Read the exported text away from the artifact. | It names the artifact, the feature, and the section each question attaches to, so it can be acted on alone. |
| 5. Invoke **Copy as Markdown**. | Identical to the prompt export except for the single lead line. No markdown syntax is emitted. |
| 6. Edit a question, then export immediately. | The export carries the edited text. It is derived from live state at the moment of invocation. |
| 7. Clear both fields and export. | The text says in words that there is nothing to export, and denies that this is an approval. It does not produce an empty or invented document. |
| 8. Let the clipboard be refused — common from a filesystem. | The full text appears in a selectable field, focus moves to it, and the status says the copy failed. **Nothing reports success.** |
| 9. Read the two control labels. | "Copy as prompt" and "Copy as Markdown" — each names its destination, not its mechanism. |
| 10. Invoke both exports in quick succession. | Only the **later** invocation's outcome is reported. The earlier one changes no status text, reveals no fallback text, and moves no focus. |

Step 10 is the one with no precedent to compare against: all three shipped
export-carrying templates fail it. It is the check that proves FR-026a landed.

### Recording the evidence

FR-042 requires the render recorded as acceptance evidence **in both themes and
with the network unavailable**. Capture, for each theme:

- a screenshot of the full page,
- a screenshot of the console showing it empty,
- the exported text from a two-question run.

---

## What a failure means

| Symptom | Almost certainly |
|---|---|
| The suite names the artifact and a block | A character of drift in an embedded canonical block. Re-copy it from its source file with its markers; never hand-edit the copy inside the artifact. |
| A fill-region check reports a region that does not exist | The inventory and the body disagree. They are bound in both directions. |
| A region reports as nested when it is not | An item without an end tag. The parser performs no implied closing. |
| An anchor reports as resolving to two items | A duplicate id. This is the collision that keeps `implementation-notes` out of the list slots. |
| The suite passes but nothing was asserted about this template | The floor row is missing. Run the non-vacuity check above. |
| CI fails `artifact-consistency` on a green local tree | A regeneration was skipped. Both of them, not just one. |
| Text renders invisibly for a moment | The font request's swap parameter was dropped. It arrives inside the head block and is never edited. |
| A heading falls back to the wrong face | `--rc-font-heading` was written. The token is `--rc-font-display`; an undefined custom property fails silently. |
