# SPEC-PARITY-01 Workflow — Post-Impl Parity Test

## Overview

Tiny synthetic workflow used by Layer 8 parity fixture 01. All 7
phases pre-populated as `✅ Complete` so autopilot runs only the
post-impl parallel group (tasks 10-14) and the serial tail (15-19)
for parity comparison.

| Field | Value |
|-------|-------|
| Spec Directory | specs/parity-01-post-impl |
| Branch | parity-01-post-impl |
| Status | Phase 7 ✅; Post-impl pending |

## Workflow Overview

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Specify | ✅ Complete | synthetic spec |
| Phase 2: Clarify | ✅ Complete | no clarifications needed |
| Phase 3: Plan | ✅ Complete | synthetic plan |
| Phase 4: Checklist | ✅ Complete | no gaps |
| Phase 5: Tasks | ✅ Complete | synthetic tasks.md |
| Phase 6: Analyze | ✅ Complete | no findings |
| Phase 7: Implement | ✅ Complete | synthetic impl, G7 passes |

## Post-Implementation Checklist

(Empty — autopilot populates this section during the post-impl run.
The parity diff compares this section across Path A and Path B runs.)

## Layer Plan

The fixture represents a PRSG-008 split-PR route with three ordered
reviewable slices. Live parity runs must consume that layer plan as the
only ordering and membership source before multi-PR emission.

## Multi-PR Emission Evidence

(Empty — autopilot populates this section during the post-impl run.
Layer 8 compares row count, status, review order, branch bases, and the
durable schemaVersion 2 PRS manifest across Path A and Path B runs.)

## PR Packet Validation Evidence

(Empty — autopilot populates this section during the post-impl run.
Layer 8 compares the generated PR packet, shared validator result, and
pre-create ordering across Path A and Path B runs.)

## Notes

This file is the test input for `tests/layer8-parity/01-post-impl-parity/`.
It is NOT a real spec — it's the smallest viable workflow that exercises
the post-impl parallel group + serial tail plus ordered multi-PR emission.

The `--from-phase post` flag (or equivalent) skips phases 1-7. Both
Path A (teams) and Path B (parallel subagents) dispatch the same Doctor /
Code Review / Verify-chain tracks, then complete Integration Suite,
Reviewability Diff Gate, Self-Review, UAT Runbook Generation, PR Body
Generation, PR Creation, Review Remediation, and Retrospective. The
`generate-uat-skeleton` and `final-reviewability-backstop` helpers are
deferred: reuse committed UAT and reviewability evidence when current, or
record the documented deferred outcome before PR side effects. Packet
generation uses runner helper `generate-pr-body`; current packet and title/scope
checks use `validate-pr-packet-read-only` and
`validate-pr-workflow-contract`. PR creation uses only explicit
`gh pr create --base --head --title --body-file` packet fields. Split routes
use `multi-pr-emission` dry-run command planning before explicit live `gh`
commands, with no flattened-PR fallback, new slicing heuristics, or post-create
packet repair. Parity requires equivalent outputs across the two paths.
