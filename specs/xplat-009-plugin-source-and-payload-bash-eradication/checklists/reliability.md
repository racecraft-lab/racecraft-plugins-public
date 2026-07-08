# Reliability Checklist: Plugin Source and Payload Bash Eradication

**Purpose**: Validate that reliability requirements for guard failures,
allowlist handling, payload rebuilds, installed-cache proof, and two-slice
rollback are complete, deterministic, and testable before tasks begin.
**Created**: 2026-07-07
**Feature**: [spec.md](../spec.md)

**Note**: This checklist was generated from the Phase 4 reliability prompt in
`docs/ai/specs/.process/XPLAT-009-workflow.md`.

## Guard Failure Determinism

- [x] REL001 [Spec FR-010, SC-005; Plan Guard Architecture] Are all prohibited
  reliability categories explicitly covered by requirement and guard language:
  `.sh` files, Bash guidance, `jq` requirements, shell interpolation, Git
  Bash, WSL, PowerShell-specific command language, and Unix-only assumptions?
- [x] REL002 [Spec Clarifications; Plan Guard Architecture;
  contracts/zero-bash-guard-result.schema.json] Is the guard failure shape
  specified with objective fields: `status`, `blocking_count`,
  `classified_counts`, bounded `findings`, diagnostics, and per-finding
  surface/path/line/category/pattern/reason/classification/active-role/
  remediation?
- [x] REL003 [Spec Clarifications; Plan Guard Architecture;
  contracts/zero-bash-guard-request.schema.json] Are required scan inputs
  complete enough to avoid false negatives across `speckit-pro/`, both
  generated payload roots, and installed-cache proof records or roots?
- [x] REL004 [Spec Edge Cases, SC-005; Plan Guard Architecture] Are seeded
  regression expectations defined for reintroduced `.sh` files, active Bash
  guidance, active `jq` requirements, shell interpolation guidance, and
  Unix-only active assumptions in in-scope surfaces?
- [x] REL005 [Plan Performance Goals; Data Model: Zero-Bash Guard Result] Are
  guard scans required to be deterministic and bounded while still reporting
  full blocking and classified counts?
- [x] REL006 [Spec Clarifications; Research: Decision 5] Is changed-files-only
  or independent shell checking rejected as sufficient release-readiness proof?

## Historical Allowlist and Release Readiness

- [x] REL007 [Spec FR-009, SC-007; Data Model: Historical Allowlist Entry;
  contracts/historical-allowlist-entry.schema.json] Are historical/archive
  allowlist entries required to include path, reason, scope, category, owner,
  and release-readiness exclusion?
- [x] REL008 [Spec Edge Cases, SC-007; Plan Guard Architecture] Is it explicit
  that historical/archive allowlist entries cannot satisfy release readiness or
  count as active behavior?
- [x] REL009 [Spec Clarifications; Plan Non-goals] Are runnable examples,
  active `.sh` paths, active `jq` requirements, shell interpolation guidance,
  Git Bash, WSL, PowerShell-specific command language, and Unix-only active
  guidance excluded from the historical allowlist?
- [x] REL010 [Spec FR-009, FR-012; Plan Rollback and Safety] Does release
  readiness block on allowlist misuse instead of treating allowlisted
  historical prose as proof?

## Payload and Installed-Cache Proof Reliability

- [x] REL011 [Spec FR-006, FR-007; Plan Slice 2; Data Model: Payload Rebuild
  Record] Are payload rebuild requirements source-derived and measurable beyond
  zero `.sh` counts, including tree hashes and payload-completeness checks for
  missing, extra, mismatched, or path-leaking files?
- [x] REL012 [Spec FR-008; Data Model: Installed Cache Proof Record;
  contracts/installed-cache-proof.schema.json] Is installed-cache proof required
  to be bounded, source-derived, non-mutable-user-cache evidence with file
  inventory, source payload hash, zero script-file count, active-guidance
  findings, and allowlist exclusion state?
- [x] REL013 [Spec Clarifications; Quickstart §3] Is mutable real user-cache
  evidence explicitly barred from satisfying required release-readiness proof?
- [x] REL014 [Spec Edge Cases; Plan Slice 2; Quickstart §4] Does missing
  installed-cache proof remain a blocking reliability failure even when source
  and generated payload checks are clean?

## Slice Independence and Recovery

- [x] REL015 [Spec Reviewability Budget; Plan Implementation Strategy;
  Quickstart §§1-2] Do the two planned slices have independent verification
  boundaries: source cleanup first, then payload/cache proof and release guard
  integration?
- [x] REL016 [Plan Rollback and Safety; Research: Decision 1] Are rollback
  points clear for both slices: revert source/registry/guidance before payload
  rebuild, or revert generated payload/proof/release-readiness guard changes
  after rebuild?
- [x] REL017 [Plan Constitution Check; Plan Slice 1] Is source script deletion
  gated by passing tests or delete-only proof so partial removal does not become
  the reliability path?
- [x] REL018 [Spec PR Review Packet Requirements; Plan PR review packet source]
  Is the review packet required to trace functional requirements and success
  criteria to changed files, deterministic evidence, known gaps, and rollback
  notes?
- [x] REL019 [Spec Assumptions; Plan Non-goals] Is XPLAT-008 native operator
  UAT preserved as separate known release context so XPLAT-009 cannot overclaim
  public native-platform readiness?

## Result

- Items checked: 19
- Gaps found: 0
- Recommended parent artifact edits: None
