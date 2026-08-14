# ART-003 Acceptance Results

The manual acceptance for all three ART-003 templates, executed against the
shipped bytes on `file://`. **176 checks, 176 passed.**

| Slice | Template | Checks | Result | Driver | Verdicts |
|---|---|---|---|---|---|
| 1 (#435) | `pr-writeup.html` | 58 | all pass | `ART-003-uat-harness/uat_prwriteup.py` | `slice1-results.json` |
| 2 (#436) | `annotated-diff.html` | 65 | all pass | `ART-003-uat-harness/uat_annotated_diff.py` | `slice2-results.json` |
| 3 (#439) | `flowchart.html` | 53 | all pass | `ART-003-uat-harness/uat_flowchart.py` | `slice3-results.json` |

## What these verdicts describe

The committed JSON files were produced by re-running all three drivers against
**`main` at `bb3f425e`**, which is the tree that carries the merged templates.
They are not a transcription of the pre-merge run; they are a fresh execution
that reproduces it.

The original execution ran before each slice merged, against the same bytes in
their feature worktrees: slice 1 at `ad6cab53`, slice 2 at `6a1518c3`, slice 3 at
`780a6724`. Those worktrees no longer exist, which is why the drivers now resolve
the repository root from their own location rather than a pinned path.

Each row is `{step, claim, ok, detail}`. `step` names the requirement or success
criterion the check binds to. A few steps carry coined identifiers rather than
`FR-`/`SC-` ones (`COPY-SUCCESS`, `PASTE`, `RENDER`, `COINED-TAB-ORDER`,
`COINED-SCROLL-KEYBOARD`); those are properties the runbook asserts in prose
without giving them a numbered requirement.

Slice 2's and slice 3's `FR-`/`SC-` identifiers dereference to `spec.md` files
that exist only at their merge commits, because the archive in PR #442 removed the
spec folders. Recover them with the commands in
`.specify/memory/archive-reports/2026-08-14-art-003-post-merge-hygiene.md`.

## How to re-run

**Start Chrome yourself first.** The harness never launches a browser, and that
is a deliberate constraint rather than an omission: see *Why the harness does not
launch Chrome* below. Any Chrome or Chromium works, and it does not have to be
headless.

```text
<your chrome> --headless=new --remote-debugging-port=9222 \
              --user-data-dir=<a scratch directory> \
              --no-first-run --no-default-browser-check about:blank
```

Then, from anywhere:

```text
cd docs/ai/specs/.process/ART-003-uat-harness
python3 uat_prwriteup.py
python3 uat_annotated_diff.py
python3 uat_flowchart.py
```

Each driver rewrites its own `slice<N>-results.json` beside itself and prints a
`passed/total` summary. Four environment variables change what it points at, and
every one of them has a working default:

| Variable | Effect | Default |
|---|---|---|
| `CDP_ENDPOINT` | the browser to drive | `http://127.0.0.1:9222` |
| `ART003_ROOT` | run against a different checkout | resolved from the harness's own location |
| `UAT_URL` | replace the artifact URL outright | built from `ART003_ROOT` |
| `ART003_SHOTS` | where screenshots are written | a temp directory |

`cdp.py` is standard library only, including its WebSocket client, so the harness
adds no package dependency and contains no path to anything outside the
repository.

## Why the harness does not launch Chrome

Two independent reasons, either sufficient.

**No committed path to a browser is correct for more than one contributor.**
macOS, Linux and Windows disagree, and so do Chrome, Chromium, Chrome Beta and
every distribution's packaging of them. A hard-coded path in a shared repository
is wrong for most of the people who read it.

**The repository's Bash-confinement guard cannot prove a computed executable is
Bash-free**, and it is right not to try. `subprocess` with a runtime-resolved
binary reports as `<dynamic executable>` and blocks the release-readiness gate.
Satisfying that guard with a literal would have meant reintroducing exactly the
hard-coded path the first reason rules out. The two constraints point the same
way: the launcher is the operator's business, and the harness's business is the
protocol and the assertions.

The cost is one extra command before a run. What it buys is a file with no
`subprocess` call, no platform assumption, and no path to defend.

Each `Chrome()` instance takes its **own browser context** inside whatever
browser it finds, which is what preserves the isolation the stages depend on: one
stage's emulation state, storage and HTTP cache stay out of the next stage's. The
cache is not incidental. An offline reload in a reused context serves the brand
webfont from cache, and the offline assertions then pass for the wrong reason.

Two details of that isolation are worth knowing before editing the harness,
because each produced a wrong result first:

- **`Browser.grantPermissions` needs the `browserContextId`.** Without it the
  grant lands on the default context, the page never sees it, and `readText`
  fails with `NotAllowedError` while every non-clipboard assertion still passes.
  `Chrome.grant()` exists so no call site can forget.
- **Do not pin the target's window size at creation.** The width sweeps re-apply
  `Emulation.setDeviceMetricsOverride` per breakpoint, and a target created with
  explicit `width`/`height` stalls the renderer on the second override.

## What the harness is, and why it exists

The runbook's steps cannot be executed by ordinary browser automation, because the
tooling refuses `file://` at its own URL validation layer. Chrome does not. The
harness launches Chrome with a debugging port and drives the DevTools Protocol
directly, which makes every step executable on the real scheme.

Serving the artifacts over `http://` is not an equivalent substitute and the
runbook forbids it: it changes the clipboard permission model, so the failure
paths the runbook exists to exercise never fire.

Capabilities the steps depend on:

| Capability | Mechanism |
|---|---|
| genuine console capture | `Log.entryAdded` + `Runtime.consoleAPICalled` + `Runtime.exceptionThrown` |
| offline behaviour | `Network.emulateNetworkConditions` |
| colour-independence | `Emulation.setEmulatedVisionDeficiency` (achromatopsia) |
| the no-script pass | `Emulation.setScriptExecutionDisabled` |
| real keyboard traversal | `Input.dispatchKeyEvent` |
| real clipboard reads | `Browser.grantPermissions` + `Emulation.setFocusEmulationEnabled` |

The focus emulation is not optional: `readText` throws "Document is not focused"
in headless without it.

## Stability, stated because a green run is not a reliable run

**A clean sweep needs a retry sometimes.** Over two consecutive full sweeps of all
three drivers, the first produced 58/58, 64/64 with one stage raising, and 50/53;
the second produced 58/58, 65/65 and 53/53. The committed JSON records the second.

Two distinct causes, both understood, neither an artifact defect:

- **A shared browser makes stages interfere.** Every stage opens its own context
  in one browser, so a stage that starts while the previous one is still tearing
  down can find the endpoint briefly unresponsive, or can stall a renderer. The
  connect retry and `Chrome.viewport()` reduce this a great deal but do not
  eliminate it. This is the price of not launching a browser per stage, and it is
  the right price: see *Why the harness does not launch Chrome*.
- **One check depends on a live third party.** "With the network back, the console
  is completely silent" fails whenever `fonts.gstatic.com` returns anything other
  than the woff2 it is asked for. It was observed returning **404** for a
  `spacegrotesk` woff2 during this work. Nothing in the artifact changed, and
  nothing in the artifact can fix it: the assertion reaches outside the
  repository by construction.

Treat a single failing run as inconclusive and re-run before believing it. A
failure that reproduces across runs is real; one that does not is one of the two
above. Restarting the browser between drivers removes most of the first cause.

## Scope limits, stated because "176 passing" reads broader than it is

- **One engine.** Every check ran on Chrome. Nothing here says anything about
  Firefox or WebKit, and at least one finding the run produced is engine-specific
  by nature: plain-text copy serialization differs between engines.
- **No check binds an artifact's title to its catalog entry.** A template whose
  `<title>` drifted from its `manifest.json` row would pass every one of these 176
  checks.
- **No check reads a template's declared `exports` back against the affordances it
  actually offers.** That binding is asserted by
  `tests/speckit-pro/unit/test-artifact-gallery.py`, not here.
- **The harness proxies perceptibility, it does not judge it.** "A visible focus
  indicator exists" is measured as a computed style delta. Whether a person can
  see it is not something this can answer.

## What the run found

Two defects, both fixed before merge:

1. **A copied diff hunk was not a valid patch fragment** (slice 2). `.diff-row`
   was `display: grid`; grid blockifies its items, and a plain-text copy emits a
   newline between block-level boxes, so every row copied as two lines. Fixed by
   making the row a block with inline-block cells. Proved with a real clipboard
   read, headless and headful, with causation isolated: `display: block` on the row
   fixes it, `display: inline` on the children does not, because grid
   blockification overrides child display.
2. **Activating a flowchart node link left focus on the link** (slice 3). Against
   pre-fix bytes, focus landed on `BODY`. Fixed with `tabindex="-1"` on the seven
   node bodies and by pointing each link at `#nodes-<slug>-detail`, since a browser
   opens a closed disclosure only when the fragment names something inside it.

**The second was found by code review, not by this harness.** The drivers checked
`:target` and scroll position and never `activeElement`. Two checks were added
afterward, taking slice 3 from 51 to 53. That is the honest limit of what a
harness catches: it verifies the properties someone thought to assert.

One requirement was **corrected rather than satisfied**. Step 1 of the runbook
demanded a completely silent console on an offline reload. That is unsatisfiable
while the shared head requests a webfont, because a failed `@font-face` fetch logs
identically to a failed `<link>`. Embedded woff2 was already considered and
rejected in a dated Key Decision on 2026-07-28, on the same cost grounds, so the
step now names the one expected line instead.

## A false result worth recording

The clipboard-fallback probe initially used `delete navigator.clipboard`. That is
a **no-op**: `clipboard` is an accessor on `Navigator.prototype`, not an own
property. The page appeared to report success with no clipboard present and was
one step from being reported as a serious defect. Reading the template's own
source is what caught it. `Object.defineProperty` is the working form.

Other corrections the harness needed before it produced true results, each of
which produced a false one first: SVG `tagName` is lowercase; reduced motion
collapses durations to `1e-05s` rather than `0s`, so the comparison needs an
epsilon; a same-instance offline reload serves the webfont from cache, so the
offline pass needs a fresh browser; `blur()` does not reset the sequential focus
navigation starting point, and neither does a reload that leaves a fragment in the
URL.
