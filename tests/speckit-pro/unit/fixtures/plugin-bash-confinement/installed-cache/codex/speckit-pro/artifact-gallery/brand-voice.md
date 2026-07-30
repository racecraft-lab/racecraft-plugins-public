# Brand Voice for Artifact Copy

Write like an engineer reporting work: answer first, concrete words, no sales
register. This page is the part of the Racecraft content rules that a
single-file artifact needs — voice and tone, the vocabulary to avoid and the
vocabulary to reach for, answer-first structure, and how to label a button.
Read it before writing artifact copy; it is short enough to read in full.

It is a deliberate subset. The last two sections name the website-only rules
it leaves out and the reason each one is gone.

## Voice and tone

Write as a practitioner reporting work, not as a vendor selling it.

- **Be concrete.** Name the file, the number, the decision. A sentence that
  stays true when its subject is swapped for any other project is carrying no
  information.
- **Claim only what the artifact shows.** The evidence sits on the same page,
  so an unsupported claim fails in the same glance that reads it.
- **Prefer the plain word to the impressive one.** Shorter, more common, more
  specific.
- **Active voice, named actor.** "The check compares the marked region" beats
  "the marked region is compared".
- **Stay neutral about the work.** Report the finding and let the reader judge
  it. Praise inside the copy reads as a substitute for evidence.
- **One idea per sentence.** A reader skimming a review artifact does not
  reread.
- **Address the reader as "you"** when telling them what to do.

## Vocabulary

### Words to cut

| Do not write | Why | Write instead |
|---|---|---|
| `seamless` | Rates an experience rather than stating a fact the reader can check | Name what does not break: "no rebuild step", "no manual sync" |
| `cutting-edge` | Dates the moment it is written and says nothing about the work | The version or capability: "runs on Python 3.11 with no dependencies" |
| `revolutionary` | Claims an impact a single artifact cannot support | The measured change: "review time went from 40 minutes to 12" |
| `we help companies` | Sales register, aimed at a buyer instead of a reader | What the thing does: "this check names the artifact and the block that drifted" |

Four entries, not a complete list. The rule behind them: **if a phrase rates
the work instead of describing it, cut it.** Words like best-in-class,
game-changing, and effortless fail the same test and go the same way.

### Words to reach for

Concrete verbs that name an activity carry the register — **testing**,
**documenting**, **building**, **learning**. They say what someone did, which
a reader can check, in place of saying how impressive it was, which they
cannot.

Nouns work the same way. Name the artifact, the check, the file, the stage.

## Lead with the answer

State the answer, then support it. A reader who stops after two lines should
still leave with the finding.

- **The summary at the top states the finding, decision, or next step** — not
  what the document contains. "Three of the 21 templates drift from the brand
  block" beats "This artifact reviews template drift".
- **Every section repeats the shape** at its own scale: conclusion first,
  evidence after.
- **Recommendation before reasoning.** A reader who accepts the
  recommendation stops there; one who does not reads on for why.
- **Headings state the finding, not the topic.** "Sequential writes cost 40
  seconds" beats "Performance". Where a section carries no finding — a
  reference list, a glossary, the page you are reading — name the thing a
  reader looks it up by.
- **If the answer will not fit in one sentence, the analysis is not
  finished.** Finish it, then write the copy.

## Calls to action and button labels

In an artifact a call to action is a control: a button, a copy affordance, a
link out to the run log. Keep the count low and the labels literal.

- **One primary action per section.** Two primaries make the reader choose
  before they have read enough to choose well. Everything else stays visually
  secondary.
- **Label the action, not the gesture.** "Copy the block", "Open the run log",
  "Show the full diff" — never "Click here", "Submit", or "Learn more". The
  label has to make sense read on its own, because that is how a screen reader
  and a keyboard user meet it.
- **Sentence case.** First word and proper nouns capitalized, nothing else.
- **The label matches what happens.** A control labeled "Copy" copies and does
  not also navigate. If activating it leaves the page, the label says where it
  goes.
- **Two to four words.** Longer labels are usually a sentence that belongs
  beside the control instead.

## What this page leaves out, and why

This page drops three parts of the source rules on purpose:

- **Structured-data markup** — machine-readable metadata that tells a search
  engine what a page is.
- **Question-and-answer section minimums** — how many question-and-answer
  blocks a page has to carry.
- **Site navigation chrome** — headers, footers, breadcrumbs, and links to
  sibling pages.

All three assume a website around the document. An artifact is one file a
reader opens from the filesystem, often with no network and no site around it.
Applied here they would add markup nothing reads and navigation pointing at
pages that do not exist.

**Their absence is a decision, not an oversight.** Do not restore them from
the source. If the copy you are writing is for the documentation site rather
than an artifact, this is the wrong subset — go to the full source rules
below.

## Where these rules come from

- Repository: `racecraft-lab/racecraft` (private)
- File: `.claude/rules/content.md`
- Revision: `30237cceaeb398e9fc08d8570714f24ff661c867`
- Captured: 2026-07-04

That source is private and this repository is public, so this page reproduces
none of its prose. It states every rule above in its own words, at the level a
writer needs, and the four lines above are the whole of the record:
repository, path, revision, date.

Keeping this page in step with that revision is a manual human action.
Nothing compares the two automatically, so a change upstream reaches this file
only when a person re-reads the source and updates it, moving the revision and
date above along with the rules.
