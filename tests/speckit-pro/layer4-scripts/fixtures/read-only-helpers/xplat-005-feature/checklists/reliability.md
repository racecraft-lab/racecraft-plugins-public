# Reliability Checklist: Read-Only Helper Port

**Purpose**: Validate that XPLAT-005 reliability requirements are complete, deterministic, repeatable, and isolated from network, installed-cache, and mutable user-local state before Tasks.
**Created**: 2026-07-02
**Feature**: [spec.md](../spec.md)

## Deterministic Parity Evidence

- [x] CHK001 Golden fixture coverage is required for every Python-promoted helper. [Spec FR-011; Plan Helper Promotion Matrix Plan]
- [x] CHK002 Bash-backed helper promotion requires source-checkout Bash-reference comparison before acceptance. [Spec FR-012; Plan Constraints]
- [x] CHK003 JSON stdout comparison is specified as semantic rather than byte-order dependent. [Spec FR-013; Data Model Helper Invocation Result]
- [x] CHK004 Stderr diagnostics and exit-code behavior are required to remain exact except where an explicit normalization rule applies. [Spec FR-007, FR-008, FR-013; Data Model Helper Invocation Result]
- [x] CHK005 Drift diagnostics must identify the field, stream, or exit behavior that changed. [Spec User Story 2 Acceptance Scenario 2; Data Model Bash Reference Comparison]

## Promotion Gates

- [x] CHK006 Python tests become authoritative per helper only after accepted fixture parity and Bash-reference comparison. [Spec FR-015; Plan Helper Promotion Matrix Plan]
- [x] CHK007 The promotion matrix gives every in-scope helper fixture ids, Bash comparison ids when Bash-backed, normalized fields, status, and an authoritative test command. [Spec Phase 2 Clarifications; Plan Helper Promotion Matrix Plan]
- [x] CHK008 Unported helpers, golden-only cases, and out-of-scope helpers have explicit status boundaries instead of ambiguous release-gate status. [Spec FR-016, FR-017; Data Model Promotion Record]
- [x] CHK009 Golden-only promotion is limited to runner envelope, registry dispatch, malformed request, typed-path/subprocess safety, synthetic no-Bash/path, and normalization unit cases. [Spec Phase 2 Clarifications; Plan Helper Promotion Matrix Plan]

## Source-Checkout Smoke Repeatability

- [x] CHK010 The local macOS smoke command is specified exactly and runs the source-checkout runner through stdin JSON. [Spec Local Source-Checkout Smoke Boundary; Plan Verification Plan]
- [x] CHK011 Smoke evidence is bounded to `runtime-info`, `status: ok`, `source_vs_installed_context: source_checkout`, and runtime/plugin metadata assertions. [Spec Local Source-Checkout Smoke Boundary; Quickstart Run The Source-Checkout Runner Smoke]
- [x] CHK012 The smoke command avoids repository writes, user-local writes, package restore, generated-payload propagation, installed-cache launch claims, and native matrix claims, making repeated local execution non-mutating. [Spec FR-018, FR-019; Data Model Source-Checkout Smoke Evidence]
- [x] CHK013 Runtime-info smoke is separated from helper parity proof so a passing smoke cannot be mistaken for per-helper promotion. [Spec Local Source-Checkout Smoke Boundary; Quickstart Run The Source-Checkout Runner Smoke]

## Environment Isolation

- [x] CHK014 Promoted Python helper execution must not require network access, package installation, virtualenv restore, `jq`, Bash, PowerShell, Node, Go, Rust, or Zig. [Spec FR-009, FR-010; Plan Performance Goals]
- [x] CHK015 Parity inputs are limited to deterministic fixtures and source-checkout Bash references, not installed-cache or mutable user-local state. [Spec Edge Cases; Plan Primary Dependencies]
- [x] CHK016 Environment-sensitive normalization is allowlisted and limited to repo/worktree paths, temp paths, non-fixture-controlled executable paths or versions, platform/runtime identity, and intentional git metadata. [Spec Phase 2 Clarifications; Data Model Normalization Rule]
- [x] CHK017 Counts, booleans, statuses, diagnostic codes, public text, stderr diagnostics, and exit codes remain protected from broad normalization. [Spec Phase 2 Clarifications; Data Model Normalization Rule]

## Regression Boundaries

- [x] CHK018 Verification requires the focused helper parity test, Layer 4 script tests, default deterministic gate, and scope audit before PR handoff. [Plan Verification Plan; Quickstart]
- [x] CHK019 Scope audit must find zero active Claude Code or Codex skill, hook, generated payload, install, marketplace/public docs, mutation-helper, PR-emission, split-state, restack, relocation, install repair, or autoheal cutover edits. [Spec SC-005; Data Model Scope Audit Record]
- [x] CHK020 Known gaps in the PR review packet must distinguish unpromoted Bash-reference helpers from out-of-scope mutation or active-cutover helpers. [Spec PR Review Packet Requirements; Spec Scope Boundaries]
