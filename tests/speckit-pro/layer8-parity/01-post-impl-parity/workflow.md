# SPEC-PARITY-01 Workflow — Post-Impl Parity Test

## Overview

Tiny synthetic workflow used by Layer 8 parity fixture 01. All 7
phases pre-populated as `✅ Complete` so autopilot runs only the
post-impl parallel group (tasks 10-14) and the serial tail (15-20)
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
Path A (teams) and Path B (parallel subagents) dispatch the same 3
tracks (Doctor / Code Review / Verify-chain) and apply the serial tail
(15 Cleanup → 16 Reviewability → 17 PR Body → 18 PR Create → 19 Loop
→ 20 Retrospective). The serial tail runs the final reviewability
backstop before packet generation, renders `.git/speckit-pr-packet.json`
and `.git/speckit-pr-body.md`, validates the current packet with the
shared `validate-pr-packet.sh`, then creates PRs only with explicit
`gh pr create --base --head --title --body-file` packet fields. PR
creation emits N ordered Style B slice PRs from the PRSG-008 layer plan,
with no legacy flattened-PR fallback, no new slicing heuristics, and no
post-create packet repair fallback. Parity requires equivalent outputs
across the two paths.
