# Error-Handling Requirements Quality Checklist: Draft-PR Emission

**Purpose**: Validate that the error, failure, and degradation requirements for
draft-PR emission are complete, unambiguous, consistent, and measurable before
task generation. These items test the requirements as written in `spec.md` and
`plan.md` — they do not test the implementation.
**Created**: 2026-08-17
**Feature**: [spec.md](../spec.md)
**Domain**: error-handling
**Depth**: Standard (autopilot phase gate; no human interaction available, so
the command's documented defaults were applied instead of clarifying questions)
**Audience / timing**: Plan-phase reviewer, before `/speckit-tasks`
**Focus areas** (from the invoking prompt): fail-open artifact generation;
pull-request creation and push failure; corroboration failure classes; the
strict-mode block short-circuit.
**Status**: 38 items, 15 gaps found on the first pass, 15 closed by direct
remediation of `spec.md` and `plan.md`. See the Gap Remediation Log.

## Requirement Completeness — Fail-Open Artifact Generation

- [x] CHK001 Are fail-open requirements stated for every generation-failure size — partial set, zero-artifact set, and an unreadable or malformed template? [Completeness, Spec §FR-004]
- [x] CHK002 Is "generation failure" defined precisely enough to classify a page whose marked fill regions were only partly populated? [Resolved, Spec §FR-004]
- [x] CHK003 Are the contents of a gap-marked index row specified — which artifact is missing and why? [Resolved, Spec §FR-004]
- [x] CHK004 Are all three shortfall sinks (pull-request body index, stop report, workflow-file row note) named as mandatory for every shortfall class? [Completeness, Spec §FR-004, §SC-003]
- [x] CHK005 Is the shape of the artifacts index specified for a run that generated zero artifacts, given FR-008 requires an index table listing each artifact? [Resolved, Spec §FR-008]
- [x] CHK006 Do the shortfall requirements agree on whether the workflow-row gap note is mandatory or optional? [Resolved, Spec §FR-009]
- [x] CHK007 Is the outcome of a selection-input shortfall (the trait-carrying source absent) determined by the routing requirement rather than left open? [Coverage, Spec §FR-002]
- [x] CHK008 Is it stated that a generation failure never converts into a blocked stage or a withheld pull request? [Consistency, Spec §FR-004, §SC-003]

## Requirement Completeness — Emission-Sequence Failures

- [x] CHK009 Are failure requirements defined for the branch push that the terminal-step sequence places between the boundary commit and pull-request creation? [Resolved, Spec §FR-010, §FR-013]
- [x] CHK010 Does the spec state what durable state remains after a failed branch push — artifacts committed locally, no pull request, no draft-PR record? [Resolved, Spec §FR-013, Edge Cases]
- [x] CHK011 Are failure requirements defined for the bookkeeping commit and its push, which run after the draft-PR record is written? [Resolved, Spec §FR-010, §FR-013, Edge Cases]
- [x] CHK012 Is the stop report's content specified for the case where pull-request creation itself fails? [Completeness, Spec §FR-010]
- [x] CHK013 Is the workflow file's state after a failed creation attempt specified — no draft-PR row written? [Completeness, Spec §FR-009]
- [x] CHK014 Is the outcome specified when the title self-validation check fails before creation? [Resolved, Spec §FR-007]
- [x] CHK015 Are retry or attempt-count requirements stated for the pull-request calls, or is the operator re-run named as the only recovery path? [Resolved, Spec §FR-013]
- [x] CHK016 Do the re-entry requirements guarantee that no mid-sequence failure can produce a second pull request on a later run? [Consistency, Spec §FR-007, §FR-013]
- [x] CHK017 Is the ordering requirement stated strongly enough that a failure cannot fold the draft-PR record into the stage-boundary commit? [Clarity, Spec §FR-013]

## Requirement Completeness — Corroboration Failure Classes

- [x] CHK018 Is the corroboration status vocabulary closed, with its discrepancy and non-discrepancy partitions stated? [Completeness, Spec §FR-011]
- [x] CHK019 Are the success-gating conditions for asserting a discrepancy stated, with every other query outcome collapsed to a skipped status carrying a reason? [Clarity, Spec §FR-011]
- [x] CHK020 Is the terminal-step response specified for the closed-or-merged discrepancy? [Completeness, Spec §FR-011]
- [x] CHK021 Is the terminal-step response specified for the recorded-but-unobservable discrepancy? [Completeness, Spec §FR-011]
- [x] CHK022 Is the terminal-step response specified for the identity-mismatch discrepancy? [Resolved, Spec §FR-011, Edge Cases]
- [x] CHK023 Are the terminal-step consequences of the three non-discrepancy statuses stated in the requirements rather than only in a design contract? [Resolved, Spec §FR-011]
- [x] CHK024 Is it unambiguous that a present draft-PR record under a skipped observation cannot license creating a second pull request? [Resolved, Spec §FR-011; see Open Items note 1]
- [x] CHK025 Are the per-status sink rules stated — always in the resolution result, always one run-report line, durably recorded only for discrepancies? [Completeness, Spec §FR-011]
- [x] CHK026 Is it stated that corroboration never changes the resolved stage, never blocks resolution, and never stops the run? [Consistency, Spec §FR-011]
- [x] CHK027 Is it stated that no discrepancy response mutates the remote pull request or the recorded row? [Completeness, Spec §FR-011]

## Requirement Completeness — Strict-Mode Block Path

- [x] CHK028 Is it specified that no pull request opens when the final gate blocks under strict mode? [Completeness, Spec §FR-006, §SC-004]
- [x] CHK029 Is it specified whether artifact generation runs at all on a strict-mode block, or whether the sequence short-circuits before it? [Resolved, Spec §FR-006]
- [x] CHK030 Is the boundary between a fail-open discrepancy response and the strict-mode blocked stop stated so the two can never be conflated? [Consistency, Spec §FR-011]
- [x] CHK031 Is the stop report's content on a block specified — the blocked gate named in place of a pull-request URL? [Completeness, Spec §FR-010, §SC-004]

## Acceptance Criteria Quality & Measurability

- [x] CHK032 Does the success criterion's non-opening carve-out enumerate every non-opening outcome the requirements permit? [Resolved, Spec §SC-001]
- [x] CHK033 Is the "visible in all three places" criterion objectively checkable given how each sink is defined? [Measurability, Spec §SC-003]
- [x] CHK034 Is the "stop report alone" criterion measurable on the failure branches, including a push failure and a creation failure? [Resolved, Spec §SC-006]

## Dependencies, Assumptions & Ambiguities

- [x] CHK035 Is the assumption that the pull-request command-line tool is installed and reachable stated together with its failure response for both emission and corroboration? [Assumption, Spec §Assumptions]
- [x] CHK036 Is the assumption that no earlier plan-stage step pushes the branch stated together with the obligation it places on the terminal step? [Assumption, Spec §Assumptions]
- [x] CHK037 Are concurrency assumptions stated for two runs of the same stage racing the existence test? [Resolved, Spec §Assumptions]
- [x] CHK038 Is the fail-open posture reconciled with the workflow-file-authoritative rule so neither can be read as licensing a mutation on disagreement? [Consistency, Spec §FR-011]

## Gap Remediation Log

Fifteen items were opened as missing or contradictory requirements on the first
pass. Each was closed by editing the requirement itself; no item was closed by
rewording the question.

| Item | What was missing | Where it was fixed | Evidence it was grounded in |
|---|---|---|---|
| CHK002 | No definition of when a partly-filled page counts as a failure | spec.md FR-004 | `contracts/artifact-author-agent.md` §4 — an unfilled slot is a gap, not a partial success |
| CHK003 | Gap-row contents unspecified | spec.md FR-004 | `contracts/artifact-author-agent.md` §5 — per-entry outcomes carry a reason |
| CHK005 | Index shape for a zero-artifact run unspecified | spec.md FR-008 | `contracts/draft-packet-mode.md` §2.2 — the `Artifacts` heading is required in draft mode |
| CHK006 | FR-004 required the row note, FR-009 made it optional | spec.md FR-009 | FR-004's own MUST; the two now read as one rule |
| CHK009 | No failure semantics for the branch push | spec.md FR-010, FR-013, Edge Cases | `references/post-implementation.md` step 9 — a failing required command stops before PR creation and records the failure |
| CHK010 | Left-behind state after a failed push unstated | spec.md FR-013, Edge Cases | FR-009's write-after-success rule; the boundary commit is local until the push |
| CHK011 | No failure semantics for the bookkeeping commit or its push | spec.md FR-010, FR-013, Edge Cases | FR-007's two-way existence test makes the re-run non-duplicating |
| CHK014 | Outcome of a failed title self-validation unstated | spec.md FR-007 | `contracts/draft-packet-mode.md` §5 — refuse creation, report through the fail-open stop-report path |
| CHK015 | No retry or attempt-count rule | spec.md FR-013 | `contracts/stage-corroboration.md` §2 — the observation is taken exactly once per run |
| CHK022 | No terminal-step response for `identity_mismatch` | spec.md FR-011, Edge Cases | `contracts/stage-corroboration.md` §7; workflow-file Consensus Log rows 2 and 3 — the discrepancy vocabulary stays behaviorally uniform (log, report, no mutation) |
| CHK023 | Terminal-step consequences of `match`, `no_record`, `skipped` lived only in a contract | spec.md FR-011 | `contracts/stage-corroboration.md` §7 |
| CHK024 | Ambiguous whether a standing record under `skipped` permits creation | spec.md FR-011 | FR-007 — either positive proves existence, and creation runs only when no open pull request exists |
| CHK029 | FR-006 forbade the pull request but not the generation step | spec.md FR-006 | plan.md Summary and the workflow file's plan prompt (Q3) — short-circuit before generation |
| CHK032 | SC-001's carve-out omitted identity mismatch and sequence failures | spec.md SC-001 | The new FR-011 and FR-013 paragraphs it must now cover |
| CHK037 | No concurrency assumption behind the existence test | spec.md Assumptions | plan.md Technical Context — the stage is human-paced |

Two consistency edits rode along so the criteria stayed true to the new text:
SC-003's parenthetical now names the FR-013 sequence failures alongside the
FR-011 discrepancies, and SC-006 now covers the sequence-failure branch.
plan.md's Summary gained the matching sentence on no automatic retry.

## Open Items

1. **RESOLVED — design-contract drift, `skipped` row.** Consensus (3-of-3:
   codebase, spec-context, domain) confirmed the FR-011 rule and tightened
   `contracts/stage-corroboration.md` §7's `skipped` row to match it: never
   create; the present row is a positive under FR-007's two-way test; refresh
   when reachable, else report through FR-010. Grounding included a live probe
   showing gh's read path (GraphQL) and create path (REST) sit in independent
   rate-limit pools, so the partial-outage window the rule guards against is
   real. See the ART-007 workflow file's Consensus Resolution Log row 4.

## Notes

- Check items off as resolved: `[x]`
- A resolved marker names the requirement that now answers the question, so the
  audit trail runs from the question to the requirement text.
- Items are numbered sequentially for easy reference.
