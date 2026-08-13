# UAT Runbook: ART-003 Slice 1 — Pull Request Write-up Template

## What you're testing

This change adds one new file to the project: a self-contained web page that
serves as a template for writing up a finished pull request. It is a
**template**, not a real write-up — every section is filled with invented
sample content about a made-up feature called "NIMBUS-101 Offline Draft
Sync," so a reader can see exactly what the finished shape looks like before
anyone writes real content into it. The page also lets a reader attach a
question to any section and copy every question they wrote out in one go,
either as an instruction for a coding agent or as a pull-request comment.

This is slice 1 of 3. The other two templates are separate, later changes.

The project's automated checks already confirmed the file has no syntax
errors, that two required blocks of shared code were copied in byte-for-byte,
and that the page's structure matches a machine-readable inventory. What no
script can confirm is what actually happens when a real browser opens the
file: whether it renders, whether it stays usable with no internet
connection, whether it reads correctly in both light and dark themes and in
plain black-and-white, whether every control can be reached and used from a
keyboard alone, and whether copying text to the clipboard — including the
one case every earlier template in this project gets wrong — actually works.
That is what this runbook walks through.

## What you need

- A web browser. Chrome, Firefox, Edge, and Safari all work; a couple of
  steps below note where the exact behavior depends on which one you use.
- Access to the browser's developer console (usually **F12** on
  Windows/Linux, **Cmd+Option+I** on a Mac, or right-click anywhere on the
  page and choose **Inspect**, then open the **Console** tab).
- A way to take your browser offline: turning off Wi-Fi, switching on
  airplane mode, or using the developer tools' network panel and setting it
  to **Offline**.
- Somewhere outside the browser to paste text into and read it back — a
  plain text editor, a notes app, or a blank email draft all work fine.
- (Optional, for one step) Your operating system's grayscale display mode,
  or your browser's built-in color-vision simulator.

## Before you start

In your checkout of this repository, the file under test is at:

```text
speckit-pro/artifact-gallery/templates/pr-writeup.html
```

Do not start a local server for it. Do not open it in an editor's built-in
preview pane. Both apply their own rules, and this test is specifically
about what happens when the file is opened the plain way — straight from
disk.

## Setup (do this once, then keep the same browser tab open for the whole runbook)

1. Open your browser's developer console **first**, before opening the file,
   so nothing that happens while the page loads is missed.
2. Take your network offline (Wi-Fi off, airplane mode, or the browser's
   offline network setting).
3. Open `pr-writeup.html` directly in the browser — use **File > Open File**,
   or drag the file onto an open browser window.

---

## Part A — Reading the finished write-up

### Step 1 — Load the page and check the console

**Do this:** With the console panel visible and the network still off, look
at the console panel first, then read the page from top to bottom.

**You should see:**

- The console shows **nothing at all** — no red error lines, no yellow
  warning lines, not even one mentioning the font address the page tries to
  reach. (If a line *does* appear, mentioning `fonts.googleapis.com` or a
  blocked/failed network request, write down its exact wording — that is a
  real finding worth flagging, not something to wave off. The requirement is
  that the console stays silent even though the page cannot actually reach
  that font while you're offline.)
- The browser tab title reads "Pull Request Write-up — NIMBUS-101 Offline
  Draft Sync."
- The page itself, top to bottom, shows: a small logo mark; the words "Pull
  Request Write-up" in small print; "NIMBUS-101" in small print; "Offline
  Draft Sync" as the large page heading; and a sentence explaining the
  content is invented sample material built on that made-up feature.
- Below that, six titled sections appear, in this order: "Why this change
  was made," "How it behaved, and how it behaves now," "What each changed
  file does," "What this change deliberately leaves out," "How it was
  checked," and "What happened while it was built." Each one has real
  sentences under it — nothing is blank, and nothing shows a broken-image
  icon or placeholder text.
- Under "What happened while it was built," one sentence sits above the
  list explaining that only tasks with something to report appear, in the
  order they were recorded, and that a retried task can appear twice. Below
  it, three entries appear in this order: one labeled **T007**, one labeled
  **T009**, then another labeled **T007**. The two T007 entries are not
  next to each other — T009 sits between them — and the second T007 entry
  describes what changed on the retry.
- At the very bottom, a panel titled "Take your questions with you" appears,
  explaining that "Copy as prompt" hands your questions to a coding agent
  and "Copy as Markdown" drops them into a pull-request comment, followed by
  two buttons reading exactly **"Copy as prompt"** and **"Copy as
  Markdown."** Notice neither label is a generic word like "Copy" — each
  names where the text is going, not how it gets there.

*Why this matters: this is the only way to confirm the page actually
renders complete and silent when opened the plain way, which is the whole
reason the template can be trusted to work for anyone who opens it later.*

### Step 2 — Confirm the page still works with no network, and see what changes

**Do this:** Still offline, look closely at the lettering (the headings and
body text), then click open the arrow-shaped control under "What this
change deliberately leaves out" (do not type anything in the box that
appears), and close it again by clicking the same arrow.

**You should see:** The lettering looks like a plain, generic typeface —
not a distinctive designed one — because the custom brand font could not be
downloaded. That is the **only** thing that should look different from
being online. Nothing is missing, cut off, or unreadable. The arrow control
you clicked opens to reveal a text box and closes again normally, proving
the page's controls still work with no network connection at all.

*Why this matters: the whole point of this template is that it works for
someone reviewing code with a bad connection or no connection — this proves
that promise is real, not just a claim.*

### Step 3 — Switch themes

**Do this:** Find the button in the top-right corner labeled "Dark theme"
and click it. Read through the six sections again. Click it a second time
to go back.

**You should see:** The whole page switches between a light background with
dark text and a dark background with light text. (The button's own label
stays "Dark theme" the whole time — that names what the button does, not
which theme is currently active, so don't expect the text itself to
change.) In **both** themes: every heading and every line of body text
stays easy to read, with no washed-out or low-contrast text anywhere; the
two boxes under "How it behaved, and how it behaves now" stay clearly
outlined and separated from the page background; and nothing visible in one
theme disappears or becomes unreadable in the other.

*Why this matters: this page has to work for whichever theme a reader
already has set, not just the one it was designed against.*

### Step 4 — Check it in black-and-white

**Do this:** View the page with color removed. The most precise way: open
developer tools, then in Chrome or Edge find **More tools > Rendering**
(via the **⋮** menu inside the developer tools panel) and set **"Emulate
vision deficiencies"** to **Achromatopsia**; in Firefox, open the
**Accessibility** panel and use its **Simulate** dropdown, also offering an
achromatopsia option. If your browser doesn't offer this, use your
operating system's grayscale display mode instead (on a Mac: **System
Settings > Accessibility > Display > Color Filters > Grayscale**; on
Windows: **Settings > Accessibility > Color filters > Grayscale**), or take
a full-page screenshot and desaturate it in any image editor. (Exact menu
wording can shift slightly between browser versions — look for "vision
deficiency," "color simulation," or "grayscale.")

**You should see, specifically:**

- Under "How it behaved, and how it behaves now," you can still tell which
  box is "before" and which is "after," because each one's text starts with
  the bold word **"Before."** or **"After."** — not because of a color
  difference between the two boxes.
- Under "How it was checked," you can still tell which item passed and
  which is pending, because each starts with the bold word **"Passed."** or
  **"Pending."** — not a colored checkmark or dot.
- Under "What happened while it was built," the repeated **T007** label is
  still legible both times, and you can tell it's the same task both times
  because the bold text reads identically — not because of any color
  highlight marking it as a repeat.

Nothing on the page should become ambiguous or lose its meaning with color
removed. Turn color back on when you're done.

*Why this matters: a reader who is colorblind, or printing the page, or
looking at a black-and-white screenshot, has to be able to understand
everything on it just as well as anyone else.*

### Step 5 — Tab through the whole page

**Do this:** Click once on the page background (not the console, not the
address bar) so the page itself has focus. Then press **Tab** repeatedly,
once per press, and watch where the highlighted outline lands each time.
When you reach the end, press **Shift+Tab** a few times to go backward.

**You should see** the outline land, once per press, on these controls in
this exact order:

1. The "Dark theme" button, top-right.
2. A small arrow control under "Why this change was made."
3. A small arrow control under "How it behaved, and how it behaves now."
4. Three small arrow controls, one per item, under "What each changed file
   does" (they list three files).
5. A fourth arrow control under that same section — its own question
   control, after the three file items.
6. A small arrow control under "What this change deliberately leaves out."
7. A small arrow control under "How it was checked."
8. A small arrow control under "What happened while it was built."
9. The "Copy as prompt" button.
10. The "Copy as Markdown" button.

At **every single stop**, a visible outline or highlight box appears around
the control — you should never see the highlight vanish or jump somewhere
you can't see it. Pressing Tab enough times eventually moves focus **off**
the page entirely (to your browser's own address bar or tab list) rather
than looping back to the start. Pressing Shift+Tab retraces the same list
in reverse, in the same order, with nothing skipped and nothing landing on
the same control twice.

*Why this matters: a reviewer who cannot use a mouse — because of a
disability, a broken trackpad, or just preference — needs to reach and use
every part of this page exactly like anyone else.*

---

## Part B — Attaching and exporting questions

### Step 6 — Open a question control with the keyboard alone, and type into it

**Do this:** Using **only your keyboard** (no mouse or trackpad), tab until
focus reaches the arrow control under "Why this change was made" (the
second stop in the list from Step 5). Before pressing anything, read its
label.

**You should see:** The label reads exactly:

```text
Question on Why this change was made: no question recorded
```

**Do this next:** Press **Enter** or the **Space bar** to open it, then
press **Tab** once more.

**You should see:** A text box appears, labeled "Your question about Why
this change was made," and your keyboard focus is now inside it — anything
you type appears in the box immediately.

**Do this next:** Type this exact sentence:

```text
Why not queue on the server side instead?
```

Without clicking anything, press **Shift+Tab** once to move focus back onto
the arrow control, and read its label again.

**You should see:** The label now reads exactly:

```text
Question on Why this change was made: question recorded
```

It updated the instant you typed — not only because you closed or reopened
the control.

**Do this next:** Keep tabbing forward (you'll pass the other five
sections' question controls, and the three file-item entries, without
opening any of them) until focus reaches the **"Copy as prompt"** button.
Press **Enter** or the **Space bar** to invoke it.

**You should see:** One of two things happens, and either is a correct
result at this point:

- The status line under the buttons reads exactly `Copied. 1 question is
  on the clipboard.` — in which case, paste the clipboard contents
  somewhere outside the browser (a text editor or notes app) and confirm
  it reads exactly:

  ```text
  Artifact: Pull Request Write-up
  Feature: NIMBUS-101 Offline Draft Sync

  Act on each question recorded below. The value in parentheses is the anchor of the section it attaches to.

  motivation / Why this change was made  (#sec-motivation)
  Why not queue on the server side instead?
  ```

- Or the status line reads `Copy failed. The text is in the field below.
  Select it and copy it by hand.`, a text box appears below the buttons
  with the exact same text shown above already inside it, and your
  keyboard focus lands inside that box. (Some browsers refuse clipboard
  access for a page opened straight from a file — that's expected and is
  tested properly in Step 11. Either way, check that the text itself
  matches exactly what's shown above.)

Check the reference line carefully: there are **two spaces** between "Why
this change was made" and the opening parenthesis.

*Why this matters: this proves the whole loop — reading a section,
attaching a question to it, and exporting it — works from a keyboard alone,
start to finish, with no mouse involved at any point.*

### Step 7 — Add a second question and export as a prompt

**Do this:** Using either the mouse or the keyboard, open the question
control under "How it was checked" and type this exact sentence:

```text
What is the plan if the staging soak fails?
```

Leave the other four sections' question controls untouched — don't even
open them. Click **"Copy as prompt."**

**You should see:** The status line reads exactly `Copied. 2 questions are
on the clipboard.` (or, if your browser refuses the copy, the same wording
appears in the revealed box instead — see Step 6's note). Read the text,
either pasted somewhere outside the browser or from the revealed box. It
should read exactly:

```text
Artifact: Pull Request Write-up
Feature: NIMBUS-101 Offline Draft Sync

Act on each question recorded below. The value in parentheses is the anchor of the section it attaches to.

motivation / Why this change was made  (#sec-motivation)
Why not queue on the server side instead?

verification / How it was checked  (#sec-verification)
What is the plan if the staging soak fails?
```

Confirm specifically: there are **exactly two** questions, nothing at all
appears for the other four sections you left empty (no blank heading, no
placeholder line), and both reference lines carry two spaces before their
parenthesis. Notice the text also names the artifact and the feature at
the top — that's what lets someone act on this later without ever having
opened the page themselves.

*Why this matters: an export that picked up an empty section, or dropped
one you filled in, would silently misrepresent what you actually asked.*

### Step 8 — Export the same two questions as Markdown

**Do this:** Without changing anything, click **"Copy as Markdown."**

**You should see:** The text is identical to Step 7's, **except** the line
after the blank line reads:

```text
Questions recorded while reading this pull-request write-up.
```

instead of "Act on each question recorded below...". Everything else — the
header, both reference lines, both questions — matches exactly. No markdown
symbols (no `#`, `**`, `-`, backticks) appear anywhere in the text; despite
the name, it is not formatted as markdown, because it is meant to be pasted
as a plain comment.

*Why this matters: the two export buttons are supposed to differ in
exactly one line and nothing else — proving that keeps them predictable for
whatever reads them next.*

### Step 9 — Edit a question and export again immediately

**Do this:** Click back into the question box under "Why this change was
made" and add a few words to the end of it — for example, type ` — and is
it too late to change that?` right after the question mark. Don't click
anywhere else. Click **"Copy as prompt"** again right away.

**You should see:** The exported text now includes your added words in the
first question — it reflects exactly what's in the box **right now**. If
you saw the old wording without your addition, something would be wrong:
an export is only allowed to show what's currently typed, never an earlier
snapshot from before you edited it.

*Why this matters: a reviewer who tweaks a question just before exporting
has to trust that the tweak actually went out, not a stale version.*

### Step 10 — Export with nothing written

**Do this:** Select all the text in both question boxes you filled in
(motivation and verification) and delete it, so both are empty again —
leave all six sections with nothing typed. Click **"Copy as prompt."**

**You should see:** The status line reads exactly `Copied. The text says no
question was recorded.` The text itself reads exactly:

```text
Artifact: Pull Request Write-up
Feature: NIMBUS-101 Offline Draft Sync

No question was recorded. There is nothing here to act on. Do not treat this as approval.
```

**Do this next:** Click **"Copy as Markdown"** too.

**You should see:** The last line instead reads:

```text
No question was recorded. This record is not an approval.
```

Everything else is the same. Neither version invents a question or comes
back blank — both explicitly say in words that this is **not** an
approval.

*Why this matters: a blank export, with no wording at all, could easily be
mistaken for silent agreement. Spelling out "this is not an approval" is
what prevents that misreading.*

### Step 11 — Force a clipboard refusal and confirm the fallback

Some browsers refuse clipboard access altogether for a page opened straight
from a file — common enough that this page has to handle it visibly rather
than fail silently. To test it reliably regardless of what your particular
browser would normally do, force the refusal yourself.

**Do this:** Click into the developer console on the page you already have
open. Paste the following exactly as written, and press **Enter**:

```javascript
if (navigator.clipboard) {
  navigator.clipboard.writeText = function () {
    return Promise.reject(new Error('simulated refusal'));
  };
  console.log('Every copy on this page will now fail until you reload it.');
} else {
  console.log('This browser has no clipboard object at all, so every copy already falls back automatically.');
}
```

(If this line throws an error instead of printing one of those two
messages, your browser doesn't allow this particular override — note that
and, if you can, try the same steps below in a different browser instead.)

Retype your two questions if you cleared them in Step 10 (motivation:
`Why not queue on the server side instead?`; verification: `What is the
plan if the staging soak fails?`). Now click **"Copy as prompt."**

**You should see:**

1. The status line does **not** say "Copied" anything. It reads exactly:
   `Copy failed. The text is in the field below. Select it and copy it by
   hand.`
2. A labeled box titled "The export text, ready to select and copy by
   hand" appears below the buttons, already containing the **full** export
   text — the same header, lead line, and two questions checked in Step 7.
3. Within about a second, your keyboard focus lands inside that box on its
   own — confirm by pressing an arrow key or typing a character; it should
   land inside the box, not on the page behind it.
4. Select all the text in the box (Ctrl+A or Cmd+A) and confirm it matches
   a normal successful export exactly.

**Do this next:** Click **"Copy as Markdown"** too, with the refusal still
in effect.

**You should see:** The same failure message, the same four behaviors
above, and the box now shows the Markdown-lead version instead.

*Optional, out of curiosity:* open the same file fresh in a different
browser — Firefox in particular often refuses clipboard writes for a page
opened straight from a file, with no override needed. If it copies
successfully instead, that's not a problem — browsers vary, and the
override above tests the identical failure-handling code regardless of
which real-world cause would normally trigger it.

*Why this matters: a reviewer who believes they copied their questions,
when nothing actually reached the clipboard, would lose their feedback
without knowing it. This is the one outcome that must never be allowed to
look like success.*

### Step 12 — Invoke both exports in quick succession

This is the check with no earlier precedent in this project: every other
template that ships these two export buttons gets this exact case wrong.

Two questions should still be typed in from Step 11. You do **not** need
to reload the page — continue in the same tab.

**Do this:** Paste the following into the console and press **Enter**:

```javascript
if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
  var raceCalls = 0;
  navigator.clipboard.writeText = function () {
    raceCalls += 1;
    var isFirst = (raceCalls === 1);
    return new Promise(function (resolve, reject) {
      window.setTimeout(function () {
        if (isFirst) { reject(new Error('simulated slow refusal')); } else { resolve(); }
      }, isFirst ? 1000 : 0);
    });
  };
  console.log('The first copy you click now takes about a second and then fails. Every copy after that succeeds instantly.');
} else {
  console.log('This browser has no working clipboard.writeText to time this test against — skip this specific check here.');
}
```

This replaces Step 11's override with a new one: the very next copy you
click will wait about a second and then fail, and every copy after that
succeeds right away. It exists to force the exact situation this check
needs, on a schedule a person can actually click against, rather than
depending on inhuman timing.

**Do this next:** Click **"Copy as prompt."** Then, well within the next
second, click **"Copy as Markdown."**

**You should see, almost immediately after the second click:** the status
line reads exactly `Copied. 2 questions are on the clipboard.` No fallback
box appears.

**Do this next:** Wait at least two or three seconds without clicking
anything else, watching the status line and the area below the buttons the
whole time.

**You should see:** Nothing changes. The status line still reads `Copied. 2
questions are on the clipboard.` — it does **not** flip to `Copy failed...`
even though the *first* click you made was engineered to fail a second
later. No fallback box ever appears, and focus never jumps anywhere. This
proves the page correctly ignores the outcome of the stale, superseded
first click and reports only the most recent one.

If instead you see the message change after the fact, or a fallback box
appear with the first (prompt) question's wording after the Markdown click
already reported success, that is a real defect — write down exactly what
you saw and when.

*A limitation worth stating plainly:* the reverse situation — a copy that
would have **succeeded** landing slowly, after a faster one has already
**failed** — is protected by this exact same mechanism and is not
separately reproduced here. Constructing that specific timing by hand would
need a second, differently-tuned console script to test a guard that
already shares its logic with the one just proven above.

*Why this matters: without this protection, clicking one export and then
quickly changing your mind and clicking the other can make the page lie
about which one actually worked, or show you the wrong questions in the
fallback box. Every earlier template in this project has that bug. This
one should not.*

When you're done, reload the page (or close the tab) — this clears the
console overrides from Steps 11 and 12 and returns the page to normal.

---

## Coverage map

Each row names the step(s) that prove it, and the spec's own words for what
must be true. (Full wording lives in `spec.md` under "Success Criteria" and
the per-story "Acceptance Scenarios," if you want to check the source
directly.)

| Step(s) | Proves | Spec reference |
|---|---|---|
| 1 | Opens fully from a filesystem with nothing missing and the console silent | SC-001 |
| 1, 2 | Stays fully readable and every control stays usable with no network; only the typeface changes | SC-002 |
| 1 | Each of the six sections appears as its own titled section with real sample content, and the implementation notes render in the record's own order with a non-adjacent retried entry | US1 Acceptance Scenarios 3 and 5 |
| 1 | The two export buttons are labeled by destination, not mechanism | US2 Acceptance Scenario 7 |
| 3 | Both themes stay legible with no meaning lost | US1 Acceptance Scenario 4 |
| 4 | Every distinction on the page survives with color removed | SC-006 |
| 5 | Every control is keyboard-reachable in reading order with a visible focus outline, and nothing traps focus | US1 Acceptance Scenario 6 |
| 6 | A question control is fully operable by keyboard alone, states in words whether it holds a question, and updates that wording the instant you type | US2 Acceptance Scenario 1; the full read-attach-export loop by keyboard alone is SC-003 |
| 7, 8 | An export carries exactly the questions written, names the section and feature each belongs to, and the two export kinds differ only in their opening line | SC-004 |
| 7 | A successful copy is confirmed in text, not by color or animation | US2 Acceptance Scenario 6 |
| 9 | An export always reflects what's typed right now, never an earlier snapshot | US2 Acceptance Scenario 4 |
| 10 | With nothing written, an export says so in words and explicitly denies being an approval | Edge case "no questions at all"; SC-004's converse |
| 11 | A refused clipboard reveals the text, moves focus to it, and reports failure in words — never success | SC-005 |
| 12 | Two exports invoked close together report only the later one's outcome, with the earlier one changing no status text, revealing no fallback text, and moving no focus | The invocation-currency requirement (FR-026a) — the one behavior every earlier template in this gallery gets wrong |

Not covered here, because they are not things a person can check by
looking at a browser: whether the two embedded blocks of shared code are
byte-identical to their source, whether the automated test suite passes,
whether exactly one catalog value changed, whether the file's line count
was measured rather than estimated, and whether the machine-readable
inventory alone tells an automated reader everything it needs. Those are
the automated half of this feature's verification, already covered before
this runbook was written.

## A closing note

If every step above matched what's described, the page is doing what it
promises: it opens on its own, stays readable and usable offline, holds up
in both themes and in black-and-white, works fully from a keyboard, and
handles copying — including failing gracefully and never lying about a
failed copy — correctly. If any step didn't match, write down exactly what
you saw, which step it was, and which browser and operating system you were
using; that's precise enough for someone to reproduce and fix it.
