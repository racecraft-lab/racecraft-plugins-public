# Phase 0 Research: Feedback Sweep, slice 1 of 2

**Feature**: `art-008-feedback-sweep` | **Date**: 2026-08-20

Every unknown the Technical Context could have carried is resolved here, and
`plan.md` ships with no open clarification markers.

The spec arrived after three Clarify sessions and seven recorded consensus
resolutions. **Those are settled and are not reopened here.** This document
records Plan-phase decisions, plus five findings from reading the shipped code
that the spec's prose did not have.

---

## Decision 1 — One read-only helper, `sweep-pr-feedback`, that reports and never decides

**Decision.** Register one read-only runner operation named
`sweep-pr-feedback`, modeled on `resolve-autopilot-stage`. It takes the raw
`gh` observation the orchestrator supplies as `inputs.pr_observation`, applies
the author-association allowlist, matches the export registry, and returns a
closed-vocabulary envelope. It never runs `gh`, never touches the network, and
never assigns a class.

**Rationale.** This is the split the repository already proved. `read_only.py`
lines 1403–1453 classify a recorded `Draft PR` row against one supplied
observation and document the reason in the docstring: "Reports; never decides."
Keeping the network at the orchestrator and the classification in Python is what
makes the behavior deterministic and offline-testable, which is exactly what
FR-008 and SC-005 require. It also puts the FR-005 trust boundary inside a
fixture-pinned surface, so SC-004 is provable by golden fixture rather than by
inspection.

Assigning the class must stay orchestrator judgment, because `amended` is what
routes an item into consensus (FR-011), and consensus is an agent protocol the
runner cannot invoke.

**Alternatives considered.**

- *Two helpers, one to normalize and one to match the registry.* Rejected on
  constitution VI. They share the ten-line window, the truncation budget, and
  the normalization rules; splitting them would put that shared state in a third
  place.
- *A mutation-mode helper that also writes the log rows.* Rejected. The runner's
  command-plan apply mode is deferred by design and returns an expected failure,
  which the spec's Assumptions already record. The log writes and the replies
  are orchestrator work.

---

## Decision 2 — One recognition mechanism covers both export families

**Decision.** Recognition is a single mechanism: **registered whole-line strings
matched against the comment's first ten lines**, after normalizing line endings
and stripping trailing whitespace. Only the registered strings differ per
template. There is no second code path.

**Rationale.** Reading the shipped templates shows two payload shapes, and it is
tempting to read them as needing two rules. They do not.

*The note-payload family* — 7 templates: `annotated-diff`, `code-approaches`,
`component-variants`, `implementation-plan`, `module-map`, `pr-writeup`,
`visual-designs`. Each builds `Artifact: <title>`, a feature line, a blank line,
then the lead. The lead lands on **line four**, exactly as FR-007 states. Five
declare the lead as named constants (`PROMPT_LEAD`, `MARKDOWN_LEAD`);
`visual-designs` and `component-variants` inline the same fixed strings in a
ternary. Both forms are fixed strings, so both register identically.

*The serialization family* — 3 templates: `feature-flags`, `prompt-tuner`,
`triage-board`. These emit no lead sentence. Their identity lives in fixed
header lines instead: `Artifact: triage-board` and `Export kind: markdown`.
Those are whole lines within the first ten, so the same matcher recognizes them.

**Consequence, recorded rather than hidden.** For the serialization family the
registered line **is** the header. FR-008a requires a header-trimmed fixture per
registered sentence, and trimming the header from a serialization export removes
its identity, so a header-trimmed serialization paste is **not recognizable** and
falls through to the ordinary-comment path.

That degradation is accepted rather than engineered around, for three reasons.
It is honest — FR-007d already forbids recognition from forcing a class, so an
unrecognized paste still gets classified on its merits and nothing is dropped.
It is narrow — the trim case exists because a reviewer strips the header, and a
reviewer stripping the header of a board serialization has removed the only
thing identifying it. And engineering around it would mean matching on body
structure, which is exactly the non-deterministic guessing FR-008 forbids.

**Alternatives considered.**

- *A second header-based recognition rule.* Rejected. It is the same matcher
  over different strings; a separate rule would inflate the surface and amend a
  design the spec settled.
- *Registering a fixed post-header line for the serialization family.* Rejected
  for now. Their post-header content is data (column headings, flag rows), not
  fixed text, so there is no stable string to register.

---

## Decision 3 — Golden fixtures pin the registry; the derive test guards it

**Decision.** The registry is hardcoded data in `read_only.py`. A separate test
derives the expected set from `speckit-pro/artifact-gallery/manifest.json` and
the template files themselves, and asserts the registry matches.

**Rationale.** This is FR-008a, and it is what makes the registry's size a data
question rather than a design one. A template that reworders a lead, or a new
exporting template, fails a test instead of silently disabling recognition. The
test reads templates and edits none, so it does not cross the no-template-edits
boundary and triggers no payload regeneration.

**Registry contents, counted from the shipped templates.**

| Kind | Count | Detail |
|---|---:|---|
| Lead sentences | 14 | 7 note-payload templates × 2 kinds (`prompt`, `markdown`) |
| Empty-export sentences | 6 | 3 distinct `EMPTY_MARKDOWN` + 3 distinct `EMPTY_PROMPT` |
| Serialization headers | 3 | `feature-flags`, `prompt-tuner`, `triage-board` |

**FR-007a's ambiguity rule is confirmed correct against the shipped source.**
The sentence `No objection was recorded. This record is not an approval.` is
declared identically by **three** templates — `annotated-diff`,
`implementation-plan`, `module-map` — and its `EMPTY_PROMPT` companion is shared
by the same three. So an empty export matching either MUST report its template
id as ambiguous, exactly as FR-007a requires. The spec's "three, not two" count
is right.

---

## Decision 4 — The `uat-walkthrough` manifest entry has no template file

**Finding.** `speckit-pro/artifact-gallery/manifest.json` declares 21 templates.
The templates directory holds 20 `.html` files. The missing one is
**`uat-walkthrough`**, and it is declared as exporting both `prompt` and
`markdown`.

**Why this matters here.** FR-008a's derive test reads the manifest and then the
templates. Pointed at `uat-walkthrough` it would try to read a file that does
not exist, and fail on its first run for a reason that has nothing to do with
the registry being wrong.

**Decision.** The derive test **skips a manifest entry with no template file,
and asserts the skip list is exactly `["uat-walkthrough"]`.** Not a silent
`continue`, and not a soft warning.

**Rationale.** A bare skip would let a genuinely deleted template disappear from
registry coverage without anyone noticing, which is the failure FR-008a exists
to prevent. Pinning the skip list inverts it: the day `uat-walkthrough` gains a
file, or any other template loses one, the assertion fails and a human decides.
The registry stays derived from reality while the known gap stays visible.

**Explicitly not done.** The manifest is not edited and no template is created.
Both are outside this slice — the spec's Non-Goals bar edits to any shipped
gallery template, and a manifest edit would trigger payload regeneration for a
reason unrelated to the sweep. The gap is reported to the operator in the
implementation notes.

**This resolves the count question in the spec's favor.** FR-007b says the
gallery ships **ten** exporting templates and **seven** export a `prompt` kind.
Counted against template files that exist, that is exactly right: 10 exporting
templates on disk, 7 with a prompt kind. The manifest's 11-and-8 figures include
the phantom entry. The spec describes reality; the manifest carries one stale
row.

---

## Decision 5 — Registering the helper touches seven places

**Decision.** Follow the `resolve-autopilot-stage` precedent exactly, and treat
the three failure-prone places as checklist items rather than discoveries.

| # | File | Change | Failure if missed |
|---|---|---|---|
| 1 | `helpers/read_only.py` | The `sweep_pr_feedback` function | — |
| 2 | `helpers/read_only.py` | Allowed-inputs map entry (near line 256) | Input rejected as unknown |
| 3 | `helpers/read_only.py` | Argument-derivation branch (near line 341) | Rejected for adding no explicit entry |
| 4 | `helpers/read_only.py` | Dispatch-table entry (near line 4466) | Operation not found |
| 5 | `helpers/registry.py` | One `HelperEntry` (pattern at lines 181–188) | Not registered |
| 6 | `tests/.../test-speckit-pro-read-only-helpers.py` | Append to `EXPECTED_HELPERS`; add to `NO_BASH_ANCESTOR` | See below |
| 7 | `tests/.../fixtures/read-only-helpers/fixture-manifest.json` | One ~29-line record | See below |

**The three that fail obscurely**, per the spec's Assumptions and confirmed by
reading the tests:

- `fixture_ids == EXPECTED_HELPERS` compares **in order, not sorted**
  (`test-speckit-pro-read-only-helpers.py` line 360). The new fixture-manifest
  record must sit at the same position as the new `EXPECTED_HELPERS` entry.
  Note the sibling assertion at line 238 compares the registry-dispatch view
  against `sorted(EXPECTED_HELPERS)`, so the two differ deliberately.
- `bash_ids == [h for h in EXPECTED_HELPERS if h not in NO_BASH_ANCESTOR]`
  (line 361). A helper not added to `NO_BASH_ANCESTOR` is required to name a
  shell script that no longer exists. `sweep-pr-feedback` is new behavior with
  no `.sh` predecessor, so it takes `NO_BASH_ANCESTOR` and `registry.py` records
  `None` for the script with `python_only` as the comparison mode, exactly as
  `resolve-autopilot-stage` does.
- The manifest's remediation and rollback text **may not contain the substring
  `bash` in any casing.**

---

## Decision 6 — Insertion point in the phase-execution references

**Decision.** Insert a new `#### Phase 7 Setup: Feedback Sweep` section
**immediately before** `#### Phase 7 Setup: Open the Implementation-Notes
Record` (`phase-execution.md` line 1210), and the mirror in the Codex file.

**Rationale.** FR-001 requires the sweep to be the first setup step of the
task-execution phase, ahead of the notes record.

**The constraint that makes this safe, verified rather than assumed.**
`tests/speckit-pro/unit/test-implementation-notes-record.py` pins content in
both phase-execution files through `_phase_execution_checks`. Those are
presence assertions — `contains` and `regex` over a whitespace-normalized whole
document — so inserting a section ahead of the notes record removes nothing they
match.

Two of them are adjacency-sensitive **inside** the notes block: the reporting
field must directly follow the `**Errors:**` line, and must be the last field
before the closing fence. So the rule for implementation is narrow and firm:
**insert before the block, never interleave content inside it.**

---

## Decision 7 — Reply writes, and the surface with no prior art

**Decision.** Replies are orchestrator writes via `gh`, with the body passed
**by file path**, never inline. One fixed template per class, each opening with
the same anchored HTML-comment marker.

**Rationale.** FR-004b forbids comment text in a shell argument in either
direction, and FR-015 requires the marker that FR-006 matches on. Passing by
file is also what makes SC-009 provable by inspecting the issued commands.

**The gap FR-015a names is real.** A review-thread reply posts into its thread,
which the remediation loop already does. The pull-request conversation has no
threading, so a reply there is a new top-level comment that must name the
comment it answers. Neither shipped reply-writer posts to the conversation
surface, so that write is new work with no prior art to copy.

**Testing consequence.** The spec's Assumptions already record that reply
behavior sits outside the runner's determinism guarantees, so SC-002 is provable
only against a **captured-command fixture** — asserting the commands the sweep
would issue — rather than against a golden helper response. The plan adopts that
as the verification method rather than inventing a second one.

---

## Decision 8 — The `Sweep` type value in the Consensus Resolution Log

**Decision.** Add `Sweep` as a fourth `Type` value beside `Clarify`, `Gap`, and
`Finding` in the row schema at `consensus-protocol.md` line 617, with a short
note that sweep rows count toward the Round-2 escape-rate metric.

**Rationale.** FR-014, already settled in consensus. The `Type` column doubles
as the source discriminator, so including sweep rows in the rate does not lose
attribution.

---

## Findings the spec did not have

Four are recorded above (Decisions 2, 4, 5, 6). Two more, both stale references
in files this slice touches. **Neither is fixed here** — both are outside the
request, and the repository's own working rules say to name orphaned prose
rather than clean it up in passing.

1. **`consensus-protocol.md` line 167 still documents `aggregate-crl
   <workflow_file>`** as though it were callable. It is not. The name survives
   only in `gates/active_path_guard.py` line 5029, which is the purged-script
   list. The spec's Clarifications already corrected the reasoning that leaned
   on this tool; the reference in the shipped file was not corrected with it.
   Worth a follow-up, and worth knowing before anyone tries to compute the
   escape rate with it.
2. **Five templates cite `contracts/export-payload-contract.md`** in source
   comments as the place the export wording is pinned. That file does not exist
   anywhere in the repository. The wording is pinned only by the template
   sources themselves, which is precisely why FR-008a's derive-from-templates
   test is the right mechanism and a doc-driven registry would not have been.

## Unknowns resolved

| Unknown | Resolution |
|---|---|
| Helper name and field list | `sweep-pr-feedback`; envelope in `contracts/sweep-pr-feedback.md` |
| One helper or two | One (Decision 1) |
| How the two export families are recognized | One mechanism, registered whole lines (Decision 2) |
| Registry size and contents | 14 leads + 6 empty + 3 headers (Decision 3) |
| Manifest entry with no template file | Skip with a pinned skip list (Decision 4) |
| Where the helper registers | Seven places (Decision 5) |
| Where the sequence goes in the references | Before the notes record, never inside it (Decision 6) |
| How replies are written and proved | By file path; captured-command fixture (Decision 7) |
| Reply template wording | Fixed per class; drafted in `contracts/sweep-pr-feedback.md` |
| Byte budget for truncation | 8 KiB per comment body (Decision in the contract doc) |
