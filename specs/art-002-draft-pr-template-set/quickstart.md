# Quickstart: Validating the Draft-PR Template Set (ART-002)

How to prove this feature works, end to end, per slice. Every command below is
run from the repository root. No implementation detail lives here — that belongs
in `tasks.md` and the templates themselves.

## Prerequisites

- Python 3.11 or newer on the path. The repository suite needs no bootstrap; run
  it directly.
- `pnpm --dir docs-site install --frozen-lockfile` once per worktree, before any
  docs command. `docs-site/` is the only surface with dependencies.
- Network access for the read-only upstream fetch during implementation. It is
  not needed to validate a finished slice.

## The commands

| Purpose | Command |
|---|---|
| Structural validation | `python3 tests/speckit-pro/run-all.py --layer 1` |
| Unit tests, including both gallery modules | `python3 tests/speckit-pro/run-all.py --layer 4` |
| Full gate (layers 1, 4, 5) | `python3 tests/speckit-pro/run-all.py` |
| The fill-region module alone, while iterating | `python3 tests/speckit-pro/unit/test-artifact-fill-regions.py` |
| The gallery scanner alone | `python3 tests/speckit-pro/unit/test-artifact-gallery.py` |
| Docs reference regeneration | `pnpm --dir docs-site reference:generate` |
| Payload and proof refresh | `python3 scripts/refresh-release-artifacts.py` |

Baseline before this feature: **7226/7226 passed** (Layer 1 1447, Layer 4 5593,
Layer 5 186). Every count below is expected to grow, never to shrink.

---

## Scenario 1 — The Layer 4 module fails before it should pass

Run at the point where the fixture cases exist and the checks do not.

```bash
python3 tests/speckit-pro/unit/test-artifact-fill-regions.py
```

**Expected**: a non-zero exit and failures naming each synthetic fixture — a
missing floor slot, an inventory entry with no marker pair, a marker pair absent
from the inventory, a malformed inventory line, a repeated item with no anchor, a
duplicated anchor. This is the RED, and it does not depend on any template
existing yet.

Then, once the checks are implemented and before any template lands:

**Expected**: a clean pass. The synthetic cases assert real detections; the
real-gallery cases report nothing, because no catalog entry reads `shipped` yet.
That silence is correct and temporary — it ends at Scenario 2.

## Scenario 2 — A template and its catalog flip land together

After a template file is authored and its entry is flipped in the same change:

```bash
python3 tests/speckit-pro/run-all.py --layer 4
```

**Expected**: green, with the fill-region module's real-gallery cases now binding
on that template — its roadmap floor satisfied, its inventory and markers agreeing
both ways, and every repeated item in its list slot carrying an anchor. The
gallery scanner's checks bind on the same file for canonical blocks, attribution,
prohibited constructs, and external references.

**The two failures worth deliberately provoking once**, to confirm the guard is
real rather than assumed:

- Flip a `status` to `shipped` without adding the file → the gallery scanner
  fails on a missing artifact.
- Add the file without flipping the `status` → it fails as an orphan.

Restore both before continuing.

## Scenario 3 — The full gate, per slice

```bash
python3 tests/speckit-pro/run-all.py
```

**Expected**: zero failures, with the total above the 7226 baseline by the
fill-region module's own unit count. Layer 1 must stay green throughout: it is
what proves the new `templates/` subdirectory did not disturb the plugin layout
or stale the generated spec index.

## Scenario 4 — Generated artifacts are refreshed, not hand-edited

```bash
python3 scripts/refresh-release-artifacts.py
git status --short
```

**Expected**: the payload copies under `dist/`, the installed-cache mirrors, and
the proof snapshots appear as changes. Two things must **not** appear:
`speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` and its
`.sha256`. This feature edits no runner source, so either of those turning up
dirty means something outside this plan changed.

Run it a second time. **Expected**: no further changes — the refresh is
idempotent, which is what distinguishes a clean regeneration from a partial one.

## Scenario 5 — The docs reference stays in step

```bash
pnpm --dir docs-site reference:generate
git status --short docs-site/
```

**Expected in slice 1**: `docs-site/src/content/docs/reference/tests.md` changes,
because slice 1 adds a tracked `.py` file under the test tree. Commit it.

**Expected in slice 2**: no change. Slice 2 touches no tracked `.md`, `.py`, or
`.sh` file there. Run the command anyway and confirm the empty result rather than
assuming it.

---

## Manual acceptance, per template

These are the checks a browser has to do and Python cannot. They become numbered
steps in the feature's acceptance runbook, one set per template, each with an
observable result the operator can confirm or reject without help (FR-038). No
automated browser is introduced.

Open the template file **directly from the filesystem** — not through a server.

| # | Step | Observable result |
|---|---|---|
| 1 | Open the file with the developer console visible | Every section renders. The console is empty: no error, no failed load, no missing content. |
| 2 | Disconnect the network and reload | The document is still complete and every control still works. The **only** visible difference is the typeface. |
| 3 | Activate the theme control, then reload | The theme changes. After reload the choice persists, or — if the browser refused storage for a local file — the control still works for the session and reports no error. |
| 4 | Tab from the top of the document to the bottom | Focus reaches every capture control and every export control, each shows a visible focus indicator, and focus never jumps out of the document's normal reading order. |
| 5 | Read the sample content in every slot | Each slot shows worked example content that reads as obviously fictional. No slot is an empty frame. |
| 5a | Look for the invented feature's identifier, and read the feature header | Every slot's content names the one invented feature the sample set uses, and the header says in the rendered document that what follows is sample content awaiting a fill. |
| 5b | *(implementation-plan, code-approaches, module-map)* Read the text beside the export controls | One line says what each export is for — prompt for a coding agent, Markdown for a pull-request comment — and one line says recorded input is not saved and is lost on reload. |
| 6 | *(implementation-plan, module-map)* Open one item's disclosure, type an objection, then collapse it | The disclosure's own control now states in text that the item carries a note, without being opened. |
| 7 | *(implementation-plan, module-map)* Open a second item's disclosure | The first item's disclosure stays open and its text is intact. |
| 8 | *(code-approaches)* Move through the choice control by keyboard and commit a selection | The selection can be made without a pointer and the chosen approach is reported in text. Choosing a second replaces the first. |
| 9 | Invoke each export the entry declares, with something recorded | The produced text carries only what was recorded, names the feature, the artifact, the slot, and the item's visible label, and carries the item's anchor. The status region names what the text actually carries. |
| 10 | Reload, record nothing, invoke each export | The text states that nothing was recorded **and** that the record is not an approval, in the wording pinned in `contracts/export-payload-contract.md`. It names no item. |
| 11 | Provoke a clipboard refusal and invoke an export | The same text appears in a selectable field that receives focus, the failure message asserts no cause, and no success is reported. |
| 12 | *(spec-explainer)* Inspect the whole document | No export control, no copy affordance, no field that records reader input, and no script of its own. |
| 13 | *(spec-explainer)* Expand and re-collapse the acceptance criteria using the keyboard alone | The control reports its own state in text and the criteria show and hide accordingly. |
| 14 | Ask the operating system for reduced motion, then expand a folded section and switch the theme | Nothing animates and nothing transitions. |
| 15 | *(module-map)* View or print the document without colour | The distinguished path is still identifiable, because a boundary weight and a visible text tag carry that meaning as well as colour does. |
| 16 | *(implementation-plan, module-map)* Read each drawing with assistive technology | The drawing has an accessible name, and the information it conveys is also available as text outside it. |

Target: an operator completes one template's pass in under ten minutes, and can
carry a recorded conclusion out of the document in a single action in under thirty
seconds without retyping any of it.
