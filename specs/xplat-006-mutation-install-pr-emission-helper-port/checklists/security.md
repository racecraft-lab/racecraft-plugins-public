# Security Checklist: XPLAT-006 Mutation, Install, and PR-Emission Helper Port

**Purpose**: Validate that XPLAT-006 defines safe mutation, subprocess, path, install, and active-cutover boundaries.
**Created**: 2026-07-03
**Feature**: [spec.md](../spec.md)

## Subprocess And Runtime Boundary

- [x] SEC001 Promoted helper execution is Python 3.11+ standard library only.
- [x] SEC002 New promoted helper paths forbid `shell=True`, shell command strings, command-string interpolation, `os.system`, and unbounded subprocess input.
- [x] SEC003 No new package install, runtime dependency, virtualenv restore, `jq`, Bash, PowerShell, Node, Go, Rust, or Zig is allowed for promoted helper execution.
- [x] SEC004 Existing Bash helpers remain temporary source-checkout references until XPLAT-007 removes or archives them from active release gates.

## Path And Write Safety

- [x] SEC005 Path resolution rejects external absolute paths, traversal, symlinks, directories where a file is required, devices, and writes outside declared boundaries.
- [x] SEC006 Mutation apply mode requires explicit mode selection, valid inputs, clean-worktree checks where required, boundary checks, and approval evidence for live mutation.
- [x] SEC007 Atomic-write behavior, partial-failure reporting, and rollback/manual-remediation notes are required before helper promotion.
- [x] SEC008 Fake homes, fake caches, and fake CLIs are the default test boundary for install, doctor, PR, restack, migration, and relocation behavior.

## Cutover And Public-Claim Safety

- [x] SEC009 XPLAT-006 forbids active Claude/Codex invocation behavior changes, hook changes, generated-payload selection/cutover, install-guidance cutover, public docs claims, release-gate migration, native matrix UAT, and public platform support claims.
- [x] SEC010 Allowed phase-coverage hardening source/generated mirror changes are separately identified and constrained to autopilot phase tracking.
- [x] SEC011 The scope-audit test permits only exact known hardening paths and still fails any other forbidden `dist/`, skill, hook, plugin manifest, or docs-site public-claim surface.

## Notes

- Gaps: None.
- Consensus: Skipped because all security checks are satisfied by current spec, plan, contracts, workflow, and focused hardening evidence.
