# Implementation Notes: ART-008

Appended by the orchestrator as each Phase 7 task returns. One entry per task
that reported something; a task that reported nothing gets no entry.

### T001

**Deviations/Edge cases/Surprises:** One deviation, accepted. The task scoped
`anchors_dropped` to the Response block; the worker also named the field in the
new Recognition prose, because a drop-and-count rule is meaningless without
saying where the count lands. The field's shape stays declared in the Response
block alone.

Two edge cases, both worth carrying forward. First, FR-007e specifies two
different anchor representations that differ by one character, and conflating
them breaks the parse in either direction. The grammar `#[a-z0-9-]{1,64}`
includes the leading `#` and validates the parenthesised value as pasted,
`(#phase-2)`. The record stores the run after the `#`, `["phase-2"]`. Validating
the stored form against the grammar drops every conforming anchor; storing the
validated form breaks the fixture. Whoever implements the anchor parse (T031,
T032) and whoever fixtures it (T021) must read the contract's Recognition
paragraph rather than infer the shape. Second, sixty-four appears twice with
different meanings, the maximum anchor length and the maximum anchor count.
Both are in the contract and distinctly worded, but they read as one rule when
skimmed.

### T002

**Deviations/Edge cases/Surprises:** One cosmetic deviation: an em dash was
written and then removed to match the repository writing style.

One edge case, since acted on. FR-007e also fixes *which* sixty-four anchors
survive the cap, "the first sixty-four in body order", and T021 asserts exactly
that. The worker encoded the grammar and the count only, correctly scoping
itself to the task text, and flagged the rest. The orchestrator added the
body-order clause to `data-model.md`; the contract needs the same clause.

The worker also flagged that CHK049 in `checklists/security.md` still read as an
open conflict quoting the superseded singular `matched_line`, and that no task
in the T001-T006/T094 setup block owned closing it. The orchestrator reached the
same conclusion independently and closed it. See the entry below.

### T005

**Deviations/Edge cases/Surprises:** Report not returned; the worker went idle
before sending one. The edit was verified by the orchestrator against the task
acceptance and the sibling manifest entry. Nothing anomalous observed.

The red state this task creates is expected and must not be papered over: the
manifest now names `tests/speckit-pro/unit/test-feedback-sweep-parse.py`, which
T015 has not yet created, so the suite stays red until US1 tests land.

### T006

**Deviations/Edge cases/Surprises:** Report not returned; the worker went idle
before sending one, twice, including after an explicit request.

One deviation the orchestrator corrected. The worker produced
`{"schema_version": "1.0"}` for both fixture files, matching the sibling's
version key but supplying no container. The task called for skeletons "keyed by
case name", and tasks T015 through T093 fill them, so each would have invented
its own container. Both files now carry `cases: {}`.

### CHK049 (orchestrator, not a task)

**Deviations/Edge cases/Surprises:** CHK049 was recorded during the security
checklist as deliberately *not* closed, on the stated ground that resolving it
changes either a requirement or the helper contract and the contract sat outside
that remediation's edit surface. T001 owns the contract, so the deferral expired
when T001 landed. The orchestrator ticked the item, retagged it `[Resolved,
Contract §Recognition]`, and rewrote the deferral note to record where and why it
actually closed. The Remediation Record table was left alone, because CHK049 was
never one of the nine items that table counts.

### T003

**Deviations/Edge cases/Surprises:** No deviations.

One edge case, checked and closed by the orchestrator. FR-006b's validation half
continues into a paragraph stating that the input error stops the run, and stops
it with the FR-020 report (`spec.md:611-622`). The worker deliberately did not
mirror that into the contract and grepped to justify it: the contract carries no
run-stop, FR-020, or halt language for any diagnostic, so adding it for one row
would invent a shape, and the stop is orchestrator behavior rather than
something the helper validates. The obligation is owned downstream, by T052 (the
write-point stop reporting under the FR-020 contract) and T071 (consolidating
every stop onto one report builder). No gap.

The worker also confirmed its two hunks are disjoint from T001's, hunk by hunk,
with nothing reverted or restyled. That was the concurrency risk on this file.

### T004

**Deviations/Edge cases/Surprises:** Four deviations, all justified and declared.
(1) The `check_target` surface received full Request, Response, and Diagnostics
blocks though the task named only the redaction surface, because the Known
Interface Gap says T004 settles "the request and response shape of that check at
the write" and the narrower reading would leave T051 with prose. (2) Registration
row 2 was updated to the four-input entry and a "seven rows" note added, because
T011's acceptance names that entry and leaving row 2 at three would make T011
contradict the contract it cites. (3) A transport-cut paragraph on the `lines`
rule, without which the 8192-byte bound and the runner's 32 KiB per-string limit
read as unreconciled and T084's 33 KiB case has no stated cause. (4) One
diagnostic beyond the four listed: an outbound field sent on the analyst-payload
leg, or the reverse, is `invalid_input`, derived from FR-012f's "anything else
returns `invalid_input`".

Three edge cases.

First, **this contract sits inside the blast radius of its own examples.**
`spec.md:1144-1148` names seven feature documents, the contract among them, that
FR-008a's corpus-scan case sends through the `amendment` leg asserting zero
redaction events. A realistic `bearer <token>` example in any of them fires
`bearer_token` and turns that fixture red. The worker elided the value and said
so in the document so a later editor does not innocently restore it. T084's
author needs this: the same constraint binds `spec.md`, `plan.md`, `tasks.md`,
`data-model.md`, `quickstart.md`, and `research.md`.

Second, **the spec's own node-id example was one character short of its own
stated floor.** FR-012f (`spec.md:2205-2208`) called `IC_kwDOKQ7tDs5vXkZ9` a
token-shaped run of "twenty-plus characters"; the literal was nineteen. The
marker-line negative case still asserted zero events, but for a different reason
than stated, "not a run at all" rather than "a run with no trigger before it".
The orchestrator fixed the literal rather than weakening the case: the id is now
`IC_kwDOKQ7tDs5vXkZ9Aq`, twenty-one characters, replaced across `spec.md` (1),
`tasks.md` (2), and the contract (9). Zero occurrences of the short form remain.

Third, **em dashes.** The file's existing prose uses them heavily, so "match
local style" and the repository's no-em-dash rule pull opposite ways. The worker
checked the diff, found T001 and T003 had added zero, and followed that
precedent. The result is a visible inconsistency between the new sections' bullet
lead-ins and the neighbouring ones. Deliberate.

### Stray artifact (orchestrator, not a task)

**Deviations/Edge cases/Surprises:** T004 flagged an untracked
`tests/speckit-pro/unit/fixtures/read-only-helpers/tmpl81hwyb5/unknown-mode.json`
as a stray temp directory rather than intended output. Confirmed and removed. An
untracked path under a scanned tree is not harmless here: the spec-index
generator walks the filesystem rather than the git index, so a stray file can
become a committed dangling backlink that passes locally and fails on a clean
checkout.
