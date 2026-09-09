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

The fixture represents a SPEC-908 split-PR route with three ordered
reviewable slices. Live parity runs must consume that layer plan as the
only ordering and membership source before multi-PR emission.

## Multi-PR Emission Evidence

(Empty — autopilot populates this section during the post-impl run.
Layer 8 compares row count, status, review order, branch bases, and the
durable schemaVersion 2 PRS manifest across Path A and Path B runs.)

## PR Packet Validation Evidence

The fixture intentionally starts with no current packet. Autopilot updates this
row after `pr-packet-output` emits or refreshes the packet, then validates it
before PR creation.

| Status | Packet Path | Validator Result | Writes State | Blocker |
|--------|-------------|------------------|--------------|---------|
| pending | `specs/parity-01-post-impl/.process/pr-packets/<packet-id>.json` | not_run | false | packet emission pending |

## Required Invariants

| Invariant | Value |
|-----------|-------|
| shared_packet_schema | speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json |
| shared_packet_validator_helper_id | validate-pr-packet-read-only |
| required_packet_path | specs/<feature>/.process/pr-packets/<packet-id>.json |
| packet_emission_promotion_status | golden_only |
| validation_result_source | data.stdout_json |
| validation_writes_state | false |
| validation_artifact_written | false |
| generate_pr_body_inputs | output_path, title, sections |
| generate_pr_body_output | one_markdown_body |
| runner_invocation | [resolved_python, -m, speckit_pro_runner] with one JSON request on stdin |
| codex_duplicate_schema_or_validator | false |
| requires_explicit_pr_create_args | --base, --head, --title, --body-file |
| missing_packet_blocks_pr_create | true |
| post_create_packet_repair_fallback | false |

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
record the documented deferred outcome before PR side effects. Packet emission
uses the active `pr-packet-output` helper. Because this fixture starts with no
current schema-valid packet at the feature-local path, both routes must emit or
refresh that packet before `validate-pr-packet-read-only`,
`validate-pr-workflow-contract`, or `gh pr create`. `generate-pr-body` remains a
body-only operation accepting `output_path`, `title`, and `sections`; it cannot
fill the packet gap. Split routes may use `multi-pr-emission` only for
`golden_only` command-plan capture after packets exist, never for packet or live
PR emission. Parity requires equivalent deferred outcomes across the two paths.
