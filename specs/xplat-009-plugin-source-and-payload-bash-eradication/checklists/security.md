# Security Checklist: Plugin Source and Payload Bash Eradication

**Purpose**: Validate that the specification and plan define security-relevant
runtime, trust-claim, payload, installed-cache, allowlist, and release-readiness
requirements before implementation.
**Created**: 2026-07-07
**Feature**: [spec.md](../spec.md)
**Domain Prompt**: `$speckit-checklist security`

## Runtime Guidance and Fallbacks

- [x] [Spec FR-004; Plan Constraints] The requirements prohibit Python wrappers,
  fallback paths, or active guidance that continue to invoke live `.sh` files.
- [x] [Spec FR-005; Workflow Phase 4 Security Prompt] The prohibited current
  guidance set includes Bash, `.sh`, `jq`, shell interpolation, Git Bash, WSL,
  PowerShell-specific command language, and Unix-only assumptions.
- [x] [Spec FR-012; Plan Summary] The XPLAT-008 installed-runtime contract is
  preserved as direct Python 3.11+ `speckit_pro_runner` invocation with no Bash,
  Git Bash, WSL, PowerShell-specific command language, or `jq` requirement.
- [x] [Spec Edge Cases; Plan Guard Architecture] The active guidance scan must
  fail guidance that avoids the word "Bash" but still points users at `.sh`,
  `jq`, shell interpolation, or platform-specific shell behavior.

## Public Trust and Support Claims

- [x] [Spec PR Review Packet Requirements] The PR packet requirements preserve
  the XPLAT-008 native operator UAT status and forbid claims that XPLAT-009
  completes native platform release readiness.
- [x] [Plan Non-goals; Research Decision 8] Completing native operator UAT rows
  or changing public native-platform release claims is explicitly out of scope.
- [x] [Spec FR-011; Plan PR Review Packet Source] Security-relevant claims must
  trace to changed files and deterministic evidence in the review packet.
- [x] [Spec SC-006] The success criteria require 100% mapping from functional
  requirements and success criteria to changed files and verification evidence.

## Payload and Installed-Cache Proof

- [x] [Spec FR-006; Spec FR-007] Rebuilt Claude and Codex payloads must be
  source-derived and contain zero `.sh` files, active Bash fallback guidance, or
  active `jq` requirements.
- [x] [Spec FR-008; Spec Clarifications] Installed-cache proof must come from
  rebuilt payloads and report zero `.sh` files plus zero unallowlisted Bash or
  `jq` active guidance.
- [x] [Data Model Installed Cache Proof Record; Contract
  installed-cache-proof.schema.json] Required proof fields include product,
  installed root, source payload root/hash, file inventory, `source_derived:
  true`, `mutable_user_cache: false`, script count `0`, active guidance
  findings, and allowlist exclusion state.
- [x] [Plan Storage; Research Decision 7] Mutable real user-cache evidence is
  supplemental only and cannot satisfy release readiness.

## Historical Allowlist Boundaries

- [x] [Spec FR-009; Spec SC-007] Historical/archive allowlist entries must carry
  path, reason, scope, and release-readiness exclusion, and cannot be used as
  release-readiness proof.
- [x] [Plan Guard Architecture; Contract historical-allowlist-entry.schema.json]
  Allowlist categories are bounded to historical/archive, negative-policy, or
  inactive-provenance references with `release_readiness_excluded: true`.
- [x] [Spec Edge Cases; Research Decision 5] Historical/archive references may
  remain only when explicitly allowlisted and must not mask active behavior or
  satisfy proof.

## Guard and Release-Readiness Behavior

- [x] [Spec FR-010; Spec SC-005] Regression coverage must fail reintroduced
  `.sh` files, active Bash guidance, active `jq` requirements, shell
  interpolation guidance, and active Unix-only assumptions in in-scope surfaces.
- [x] [Plan Guard Architecture; Contract zero-bash-guard-result.schema.json] The
  guard result shape defines `status`, `blocking_count`, `classified_counts`,
  bounded findings, scan roots, allowlist entries, and the
  `zero_bash_guard_blocked` diagnostic.
- [x] [Plan Slice 2; Quickstart Release Readiness] Release readiness blocks when
  scan roots are missing, installed-cache proof is missing, blocking findings
  exist, or allowlist entries are counted as release-ready proof.

## Scope and Review Safety

- [x] [Spec Assumptions; Plan Scale/Scope] XPLAT-010 owns repository-wide Bash
  cleanup outside plugin source, generated payload, and installed-cache proof
  scope.
- [x] [Spec Reviewability Notes; Plan Rollback and Safety] The two planned
  slices have independent verification boundaries and normal git-revert
  rollback paths.

## Result

- Security checklist passed with no shared-artifact edits required.
- Report-only parent artifact recommendations: none.
