# Reliability Checklist: XPLAT-006 Mutation, Install, and PR-Emission Helper Port

**Purpose**: Validate that XPLAT-006 can be tested repeatably without network, installed-cache state, real user-home writes, or live GitHub mutation.
**Created**: 2026-07-03
**Feature**: [spec.md](../spec.md)

## Deterministic Fixtures

- [x] REL001 Deterministic fake repositories, fake `gh`, fake `specify`, fake Claude homes, fake Codex homes, and fake plugin caches are required by default.
- [x] REL002 Source-checkout tests must not depend on network access, package restore, real GitHub mutation, mutable user-local state, or installed-cache state.
- [x] REL003 Windows-style path fixtures are required for platform-sensitive path handling without native installed-cache UAT.
- [x] REL004 Native Windows/macOS/Linux installed-plugin UAT remains deferred to XPLAT-008.

## Repeatable Promotion Evidence

- [x] REL005 Golden fixtures plus Bash-reference comparisons are required before each Bash-backed helper can be promoted.
- [x] REL006 Promotion records must map helper ids, modes, fixture ids, Bash-reference comparison ids, normalized fields, and authoritative Python test commands.
- [x] REL007 Python helper tests become authoritative only per helper after accepted fixture parity and Bash-reference comparison.

## Durable Outputs

- [x] REL008 Generated JSON and Markdown outputs use UTF-8 LF with one final newline.
- [x] REL009 Host-file edits preserve existing line endings or report explicit LF normalization.
- [x] REL010 Runner manifest/checksum metadata must be updated after runner-owned Python files change.
- [x] REL011 PR packet traceability must map changed files, verification commands, fixture evidence, promotion state, known gaps, approval boundaries, and rollback/manual remediation notes.

## Hardening Reliability

- [x] REL012 Phase-coverage validator checks both workflow Markdown and durable `autopilot-state.json` so visible plan state and persistent state cannot drift silently.
- [x] REL013 Layer 4 includes the phase-coverage regression test, and the current run passed 2141/2141 after the scope-audit test was tightened.

## Notes

- Gaps: None.
- Consensus: Skipped because all reliability checks are satisfied by current spec, plan, contracts, workflow, and focused hardening evidence.
