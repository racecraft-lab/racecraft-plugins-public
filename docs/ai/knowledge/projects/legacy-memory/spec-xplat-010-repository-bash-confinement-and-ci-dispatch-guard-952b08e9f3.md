---
type: "speckit-legacy-memory-record"
title: "XPLAT-010 Repository Bash Confinement and CI Dispatch Guard"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-952b08e9f3de62d2"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-010 Repository Bash Confinement and CI Dispatch Guard

[Source: specs/xplat-010-repository-bash-confinement]

XPLAT-010 completed the repository-wide Bash backstop after XPLAT-009 removed
plugin-source and generated-payload Bash. It migrated active repository tests,
validators, helpers, hooks, eval runners, and release tooling to Python 3.11+
standard-library paths; made the suite manifest authoritative; added a strict
repository-confinement gate; restored spec-size estimation; added hosted Linux
and advisory Windows preflight; and added deterministic consumer release-note
validation and release Highlights composition.

### Requirements Preserved

- Tracked Bash is confined to bounded GitHub workflow dispatch glue and the
  fixed vendored `.specify/**` allowlist, whose entries cannot satisfy release
  readiness.
- Active repository validation, packaging, install, helper, hook, payload,
  release, and test/eval behavior runs through Python without Bash or `jq`.
- `tests/speckit-pro/suite-manifest.json` remains the source of truth for layer
  membership, dispatch, execution mode, and default selection.
- Frozen `bash-to-python` baselines and the count ledger preserve port names and
  counts without treating historical Bash as an active runtime.
- Linux amd64/arm64 container jobs gate through stable sentinels; Windows x64
  and ARM64 smokes remain advisory and cannot substitute for native UAT.
- Feat/fix PRs require a valid consumer release-note block or the explicit skip
  label, and release Highlights are composed deterministically.
- The XPLAT-008 native UAT matrix remains the only release-satisfying evidence
  for complete native installed-plugin journeys.

### Success Criteria

XPLAT-010 is successful because PRs #311-#328 merged the exact reviewed stack,
the final `main` tree matches the verified stack tip, the neutral-PATH default
suite passed `2512/2512`, all 18 packet validations passed, and all review
branches were deleted. T108 completed with hosted relevant, docs-only,
failure-propagation, manual-main, and trigger-canary evidence. T117 completed
with exactly five non-strict required GitHub Actions checks on `main`.

### Cleanup Note

Archived into project memory on 2026-07-11 using final stack merge commit
`ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29`. The active
`specs/xplat-010-repository-bash-confinement/` folder was removed after live
schema and planner inputs were preserved under purpose-based test fixtures.
Process evidence remains under `docs/ai/specs/.process/XPLAT-010-*`; exact
provenance and recovery commands are recorded in
`.specify/memory/archive-reports/2026-07-11-xplat-010-post-merge-hygiene.md`.
