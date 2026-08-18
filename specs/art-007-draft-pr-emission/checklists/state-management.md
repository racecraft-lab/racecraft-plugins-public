# State-Management Requirements Quality Checklist: Draft-PR Emission

**Purpose**: Validate that the durable-state requirements for draft-PR emission
are complete, unambiguous, consistent, and measurable before task generation.
These items test the requirements as written in `spec.md` and `plan.md` — they
do not test the implementation.
**Created**: 2026-08-17
**Feature**: [spec.md](../spec.md)
**Domain**: state-management
**Depth**: Standard (autopilot phase gate; no human interaction available, so
the command's documented defaults were applied instead of clarifying questions)
**Audience / timing**: Plan-phase reviewer, before `/speckit-tasks`
**Focus areas** (from the invoking prompt): draft-PR row lifecycle; the
re-entry state machine across every intermediate state an interrupted run can
leave; stage auto-detect interplay and commit ordering; fresh-session resume,
what a later `--stage implement` run reads, and orphaned records.
**Status**: 35 items, 9 gaps found on the first pass, 9 closed by direct
remediation of `spec.md`, `plan.md`, and two design contracts. See the Gap
Remediation Log.

## Requirement Completeness — Draft-PR Row Lifecycle

- [x] CHK001 Is the row's absent state defined as legal with an explicit meaning, rather than left as an unstated default? [Completeness, Spec §FR-009]
- [x] CHK002 Is the write trigger stated precisely enough to exclude any write before creation or refresh succeeds? [Clarity, Spec §FR-009]
- [x] CHK003 Is the row's placement pinned to a named table, with the table it must not go in named too? [Completeness, Spec §FR-009]
- [x] CHK004 Is the row's value grammar specified well enough that a reader recovers both number and URL from one cell? [Clarity, Spec §FR-009]
- [x] CHK005 Is the sole-store rule's scope bounded — does "the only place this identity is stored" still hold after FR-012's split, where the shipped slice manifest also records pull-request identity? [Resolved, Spec §FR-009, §FR-012]
- [x] CHK006 Is it specified whether a refresh run must recompute the row's shortfall note when the artifact outcome changed since the record was first written? [Resolved, Spec §FR-009, §FR-004]
- [x] CHK007 Is the scaffold template's no-placeholder obligation stated as a requirement rather than only as a design note? [Completeness, Spec §FR-009]

## Requirement Completeness — Commit Sequence & Durability

- [x] CHK008 Is the terminal step's order stated as an ordered sequence with each step a precondition for the next? [Completeness, Spec §FR-013]
- [x] CHK009 Is the stage-boundary commit's preserved contract enumerated — message, staged path set, non-emptiness? [Completeness, Spec §FR-013]
- [x] CHK010 Is the bookkeeping commit's own staged path set specified, so a reader can tell which files that commit makes durable? [Resolved, Spec §FR-013]
- [x] CHK011 Is the non-emptiness property of either commit still satisfiable on a re-run where the artifacts, the gate row, and the record are already committed? [Resolved, Spec §FR-013]
- [x] CHK012 Is the prohibition on folding the record into the boundary commit stated unambiguously? [Clarity, Spec §FR-013]
- [x] CHK013 Is the no-automatic-retry rule stated together with the recovery path it implies? [Completeness, Spec §FR-013]
- [x] CHK014 Are the durable consequences of a failed branch push stated — what is committed, what is not written? [Completeness, Spec §FR-013, Edge Cases]
- [x] CHK015 Are the durable consequences of a failed bookkeeping commit or its push stated? [Completeness, Spec §FR-010, §FR-013]

## Requirement Completeness — Re-Entry State Machine

- [x] CHK016 Are requirements defined for every intermediate state an interrupted emission can leave, rather than only for the failure that produced it? [Coverage, Spec §FR-013]
- [x] CHK017 Is the dual existence test stated with its rationale — that the record is written after creation, so a run interrupted between the two leaves a pull request with no record? [Clarity, Spec §FR-007]
- [x] CHK018 Is either positive of the existence test stated as sufficient, so a present row alone blocks creation? [Consistency, Spec §FR-007, §FR-011]
- [x] CHK019 Is the re-entry behavior specified when an open pull request exists — refresh, repair the record, report the existing URL? [Completeness, Spec §FR-007]
- [x] CHK020 Is it stated that no mid-sequence failure can produce a second pull request on any later run? [Consistency, Spec §FR-007, §FR-013]
- [x] CHK021 Is the re-entry path after a strict-mode block specified, so the passing re-run is the run that emits? [Coverage, Spec §FR-006, Edge Cases]
- [x] CHK022 Is it specified at which point in the FR-013 sequence a corroboration discrepancy ends the emission attempt, and whether the boundary commit is still taken so the durably recorded discrepancy reaches version history? [Resolved, Spec §FR-011, §FR-013]

## Requirement Consistency — Stage State Interplay

- [x] CHK023 Is it stated that the `Draft PR` row and the `Stage` row coexist in one table without either one's writer disturbing the other's shipped write cadence or its state-file mirror? [Resolved, Spec §FR-009]
- [x] CHK024 Is the durable discrepancy record's write cadence tied to a named existing write, so it cannot land in a different commit? [Consistency, Spec §FR-011]
- [x] CHK025 Is it stated that corroboration never changes the resolved stage, never blocks resolution, and never stops the run? [Consistency, Spec §FR-011]
- [x] CHK026 Is the workflow-file-authoritative rule stated so that no corroboration outcome can license overwriting the record from live data? [Consistency, Spec §FR-011]
- [x] CHK027 Is the exclusion of the phase-status table stated as a requirement rather than left to the reader? [Consistency, Spec §FR-009]

## Requirement Clarity — The Live Observation

- [x] CHK028 Is it specified whether the corroboration observation and FR-007's emission-time existence query are one read or two, given the whole plan stage runs between them? [Resolved, Spec §FR-007, §FR-011]
- [x] CHK029 Is the observation's precondition stated — attempted only when the row is present? [Clarity, Spec §FR-011]
- [x] CHK030 Is the corroboration limb's scope across invocations specified — does it run when the stage came from an explicit argument rather than auto-detection, and what does a run outside the plan stage do with a discrepancy whose terminal-step consequences it cannot apply? [Resolved, Spec §FR-011]

## Acceptance Criteria Quality — Resume & Record Location

- [x] CHK031 Is the resume criterion measurable from the record alone, without a live query? [Measurability, Spec §SC-005]
- [x] CHK032 Is it stated as an invariant that no ordering can leave the row pointing at a pull request whose branch never reached the remote? [Resolved, Spec §FR-009, §FR-013]
- [x] CHK033 Does the emission success criterion's carve-out cover every non-opening state the re-entry requirements permit? [Consistency, Spec §SC-001]

## Dependencies & Assumptions

- [x] CHK034 Is the single-run-in-flight assumption stated as the reason the existence test needs no locking? [Assumption, Spec §Assumptions]
- [x] CHK035 Is the assumption that no earlier plan-stage step pushes the branch stated with the obligation it places on the terminal step's ordering? [Assumption, Spec §Assumptions]

## Gap Remediation Log

Nine items were opened as missing, unbounded, or contradictory requirements on
the first pass. Each was closed by editing the requirement itself; no item was
closed by rewording the question. None reopens a decision recorded in the
workflow file's Consensus Resolution Log.

| Item | What was missing | Where it was fixed | Evidence it was grounded in |
|---|---|---|---|
| CHK005 | The sole-store rule read as absolute, but the shipped multi-PR path records pull-request identity in its own slice manifest, and FR-012 makes the draft pull request the first slice | spec.md FR-009 | `references/post-implementation.md` step 10 — the slice route persists `specs/<feature>/.process/prs.json` naming each slice's PR URL or number; FR-012's split is a later stage's flow, so the boundary is temporal, not a second store |
| CHK006 | Nothing said whether a refresh recomputes the shortfall note, so a stale note could outlive the shortfall it described | spec.md FR-009 | FR-004's own MUST ties the note to the run's outcome; `contracts/draft-pr-row.md` §4 already required repair when the row is "wrong" |
| CHK010 | The bookkeeping commit's staged path set was unstated while the boundary commit's was fully pinned | spec.md FR-013 | `references/phase-execution.md` §Stage-boundary commit — the staged set is the specification directory, the workflow file, and the state file, and "Never the workflow *directory*, which also holds untracked run byproducts". The record lives only on the workflow file (FR-009), so that is the whole set |
| CHK011 | FR-013 chains each step as a precondition for the next, but a re-run of an already-resolved stage has nothing to stage, so a no-op commit would halt the recovery path FR-013 names | spec.md FR-013 | `references/phase-execution.md` grounds boundary-commit non-emptiness in the `Confidence Gate` row "always advances off its pending state" — true on a first pass only; §Stage-Bounded Phase Selection routes an already-complete stage straight to "run its terminal step, then STOP" |
| CHK022 | The three discrepancy responses said what they are not (no strict-mode block) but never where in the FR-013 sequence they stop, leaving the durable discrepancy record possibly uncommitted | spec.md FR-011; contracts/stage-corroboration.md §7 | FR-011 already requires the discrepancy line to land "in the same commit" as the `Stage` row, and the plan stage's commits are the per-phase and boundary commits; FR-011 equally forbids stopping the run, so only the emission steps can be skipped |
| CHK023 | The new row shares a table with `Stage`, whose shipped protocol pins a write cadence and a state-file mirror, and nothing said the new writer is exempt from both | spec.md FR-009; contracts/draft-pr-row.md §4 | `references/workflow-file-protocol.md` §The `Stage` Entry — "at most twice per run", both stores in one edit turn, `stage_mirror_errors` in the Step 1.1 coverage guard. FR-009's sole-store rule means this identity has no mirror to keep in step |
| CHK028 | "One read-only query" (FR-011) and "a live query" (FR-007) were never related to each other, though the whole stage runs between them | spec.md FR-011; contracts/stage-corroboration.md §2 | `contracts/stage-corroboration.md` §2 takes the observation only when the row is present, while §7's `no_record` row "fall[s] through to the live by-branch existence test" — necessarily a second read, since no observation was taken for that run |
| CHK030 | Corroboration was attached to "stage auto-detect", leaving open whether it runs under an explicit `--stage` and what a non-plan stage does with a discrepancy it cannot act on | spec.md FR-011; contracts/stage-corroboration.md §2 | `contracts/stage-corroboration.md` §3's own request example carries `"autopilot_args": ["--stage", "plan"]` with `source: "argv"`; SKILL.md Step 0.6c runs the resolver on every invocation; `references/phase-execution.md` §Stage-Bounded Phase Selection shows only the plan stage's terminal step emits |
| CHK032 | The orphaned-record impossibility was derivable but never asserted, so SC-005 could not be audited against it | spec.md FR-013 | FR-013's own ordering puts the push before creation, and FR-009 writes the record only after creation succeeds |

Two contract files were edited, and only to keep them consistent with the FR
text changed above: `contracts/stage-corroboration.md` (§2 gained the
two-separate-reads and row-presence-not-stage rules, §7 gained where the three
discrepancy responses stop and what a non-plan-stage run does) and
`contracts/draft-pr-row.md` (§4 gained the whole-value rewrite rule and the
independence from the `Stage` row's cadence). `plan.md`'s Summary gained the
matching sentence on where a discrepancy ends the sequence.

## Tooling Note

`count-markers` in gaps mode matches the regex `\[Gap\]` and nothing else
(`speckit_pro_runner/helpers/read_only.py:825` and `:835`), so it counts only a
bare `Gap` alone in square brackets. The combined form this command's own
instructions also prescribe, a dimension and `Gap` together in one bracket,
never matches, and a checklist written that way reports zero gaps against a page
full of them. Items here therefore carried the bare marker beside their
dimension bracket while they were open, which is what made the first-pass count
of 9 verifiable rather than asserted. Prose naming the literal is counted too,
so this note describes the marker instead of spelling it.

## Notes

- Check items off as resolved: `[x]`
- A resolved marker names the requirement that now answers the question, so the
  audit trail runs from the question to the requirement text.
- Items are numbered sequentially for easy reference.
