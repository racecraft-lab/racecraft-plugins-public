# Integration Checklist: XPLAT-006 Mutation, Install, and PR-Emission Helper Port

**Purpose**: Validate that XPLAT-006 integrates with the existing runner, helper registry, install inventory, PR-emission, and scope-audit surfaces without active cutover.
**Created**: 2026-07-03
**Feature**: [spec.md](../spec.md)

## Runner And Helper Contracts

- [x] INT001 Plan reuses the XPLAT-004 runner envelope, diagnostics, typed path, source metadata, and preflight primitives.
- [x] INT002 Plan extends the XPLAT-005 helper registry pattern without forcing mutation behavior through read-only helper modes.
- [x] INT003 Mutation request/result contracts define read-only/dry-run/apply mode, planned operations, applied operations, diagnostics, deferred live-mutation status, and rollback/manual-remediation notes.
- [x] INT004 Helper promotion records preserve golden-only, Bash-compared, Python-authoritative, deferred, and out-of-scope states.

## Helper Matrix Coverage

- [x] INT005 Slice 1 owns shared mutation primitives only and does not prematurely promote named helper behavior.
- [x] INT006 Slice 2 covers install/doctor/preflight helpers, coach/preset write helpers, fake Claude/Codex homes, fake plugin caches, and safe repair boundaries.
- [x] INT007 Slice 3 covers PR-emission, UAT skeleton, final-reviewability, split PR, restack, migration, relocation, generated-output write modes, and handoff evidence.
- [x] INT008 XPLAT-005 read-only/advisory helper modes remain accepted and are not re-ported.

## Install And Scope Boundaries

- [x] INT009 Install completeness checks include expected Claude agents, Codex agents, runner files, generated payload files, version metadata, marketplace metadata, manifest metadata, and checksums.
- [x] INT010 Doctor/preflight remains read-only by default, with repair modeled as a separate fixture-bound apply-mode operation.
- [x] INT011 The scope audit forbids active Claude/Codex invocation behavior, hook changes, generated-payload selection/cutover, install guidance, public docs, release gates, native UAT, and public platform claims.
- [x] INT012 The allowed phase-coverage hardening source/generated mirror is explicitly named in spec, plan, research, data model, quickstart, workflow, and scope-audit test evidence.

## Notes

- Gaps: None.
- Consensus: Skipped because all integration checks are satisfied by current spec, plan, contracts, workflow, and focused hardening evidence.
