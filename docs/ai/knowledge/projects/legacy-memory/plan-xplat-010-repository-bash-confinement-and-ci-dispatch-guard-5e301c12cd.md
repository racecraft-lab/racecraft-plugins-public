---
type: "speckit-legacy-memory-record"
title: "XPLAT-010 Repository Bash Confinement and CI Dispatch Guard"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-5e301c12cd7b3b81"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-010 Repository Bash Confinement and CI Dispatch Guard

### Technical Approach

XPLAT-010 used a manifest-driven Python 3.11+ standard-library architecture for
repository-only validation. `tests/speckit-pro/suite-manifest.json` defines the
layers and Python dispatch; shared test-result and baseline helpers preserve
per-check identities; runner gates enumerate tracked files and structurally
inspect executable surfaces; subprocesses use argv arrays and `shell=False`;
and workflow shell remains bounded dispatch glue.

The implementation also added a Docker/QEMU-backed Linux amd64/arm64 preflight
path, direct hosted Windows advisory smoke, stable always-reporting Linux
sentinels, deterministic release-note parsing/composition, immutable release
audit evidence, and the restored `estimate-spec-size` helper operation. The
review topology was an 18-PR no-gap stack with frozen adjacent packets and a
bounded publication tail.

### Testing Strategy

- Preserve exact Bash-to-Python outcome names and counts in purpose-based
  parity baselines and a cumulative count ledger.
- Run focused Python unit/contract suites for each port before the default
  deterministic Layers 1, 4, and 5 suite.
- Run the default suite with Bash and `jq` absent from PATH; final result:
  `2512/2512` (`1373`, `953`, `186`).
- Prove repository confinement with tracked-file enumeration, fixed vendored
  allowlist checks, release-readiness composition, and seeded regressions.
- Prove hosted preflight behavior with relevant-path, docs-only,
  failure-propagation, manual-main, and all four owned PR-trigger canaries.
- Keep Windows preflight explicitly advisory and retain XPLAT-008 operator UAT
  as the only native-platform release-claim gate.
- Validate every adjacent review slice and audit the final merged tree against
  the verified stack tip.

### Cleanup Notes

PRs #311-#328 merged on 2026-07-11, ending at
`ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29`. Live test dependencies were
decoupled into purpose-based fixtures before removing the active XPLAT-010 spec
folder. Process evidence remains under `docs/ai/specs/.process/XPLAT-010-*`,
and raw spec artifacts remain recoverable from the final merge commit. The
separate constitution amendment completed through PR #331 at
`b537e3b43ca20d8f6e8b6e9430d797444462f2e9` before archive cleanup. Public native
claims remain blocked by the XPLAT-008 UAT matrix.
