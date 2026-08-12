# UAT Results: Implementation-Notes Capture (ART-012)

**Run:** 2026-08-11, by hand, on branch `art-012-implementation-notes-capture`
after merging `origin/main` (PR #427).
**Runbook:** `specs/art-012-implementation-notes-capture/quickstart.md`

Every number below was produced by running the command, not predicted.

## Verdict

**Pass.** All five quickstart scenarios, path hygiene, and a behavioural
walkthrough of the record lifecycle. The behavioural section is the part that
matters, because it is the only evidence that the shipped prose can actually be
followed; the automated suite proves the words are present and consistent, never
that an orchestrator obeys them.

## Scenario results

| Scenario | Expected | Measured | |
|---|---|---|---|
| 1 — reporting field, four touchpoints | 1, 1, 2 per file | 1, 1, 2 | pass |
| 1 — authored Task Result templates | exactly 3 | 3 | pass |
| 2 — both platforms describe the record | 8 rules each | 8/8 both | pass |
| 3 — automated contract check | pass | **83/83**, exit 0 | pass |
| 4 — generated payloads match source | consistent | "already consistent; no changes" | pass |
| 4 — modified payload copies | 4 claude / 5 codex | 4 / 5 | pass |
| 5 — docs reference current | test listed | 5 mentions | pass |
| Path hygiene | no output | no absolute home paths | pass |
| Full gate | zero failures, above 7226 | **7378/7378** | pass |

The full-gate total is higher than the 7309 recorded in the quickstart because
ART-002 merged 69 further tests into `main` in between. Higher with zero
failures is added coverage, not a regression, which is the distinction the
quickstart's Full gate preamble draws.

## Two probes of mine were wrong, and neither indicates a defect

Recorded because a reader re-running this should not be misled by repeating them.

1. **`create-if-absent` read MISSING in both platform documents.** My grep used
   the hyphenated form; both documents write **"Create if absent"** with spaces,
   at `phase-execution.md:829` and `phase-execution-codex.md:544`. The shipped
   test's regex allows either. My probe was wrong, the documents are correct.
2. **The first prefix-preservation check was tautological**, comparing a value
   against itself. Redone against an independent snapshot taken before the
   append: 367 bytes, byte-for-byte identical afterwards.

## Behavioural walkthrough

The documented Phase 7 rules, followed literally by hand against a scratch
feature directory, to test whether the prose is executable.

| Step | Rule under test | Result |
|---|---|---|
| 1 | Create `.process/` if absent, then the file with its header | Record created, header only |
| 2 | Interrupt before any task completes | Header-only record, 0 entries — the correct terminal state |
| 3 | A parallel-run member reports first; append on that arrival | **1 entry while two tasks were still working** |
| 4 | A worker goes idle with no summary; never append | Still 1 entry — no empty entry written |
| 5 | That worker then sends its summary; append on the report | 2 entries |
| 6 | Serial re-run after regression | 2 entries under `T003`, earlier one untouched |
| 7 | Resume in a fresh session | 1 header, prefix preserved, appended after |

Steps 3 and 4 are the pair the whole amendment exists for. Step 3 shows an entry
written while the rest of the run is still in flight, which the superseded
batched cadence would not have produced. Step 4 shows the idle signal correctly
producing nothing.

Step 5 also demonstrates a property worth stating plainly for reviewers:
**document order is arrival order, not task order.** The record ends `T002`
before `T001` because `T002` reported first. The contract makes position the
only ordering signal, so this is correct and intentional.

## The record this run produced

`specs/art-012-implementation-notes-capture/.process/implementation-notes.md`
is the feature's own output, produced by the run that built it.

| Property | Value |
|---|---|
| Entries | 14, one per task |
| Compound headings | 0 |
| Headers | 1 |
| Entries reading `None` | 9 |

Nine `None` entries is correct, not a gap. Under the contract's route table,
every orchestrator-direct and research task records `None`, and so does any
executor whose reported field could not be read. Two of the nine are the latter:
one executor was stopped before it delivered its summary, which the contract
handles by writing `None` rather than inventing content.

## What this does not prove

The suite and this UAT both exercise documents, not a live orchestrator run. The
strongest available evidence that the instructions drive behaviour is the record
above, which a real run produced while following them. A reviewer wanting more
should run autopilot's implement phase on another spec and read its record.
