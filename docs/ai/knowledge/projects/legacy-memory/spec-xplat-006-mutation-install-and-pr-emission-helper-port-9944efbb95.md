---
type: "speckit-legacy-memory-record"
title: "XPLAT-006 Mutation, Install, and PR-Emission Helper Port"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-9944efbb95bbbc0a"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-006 Mutation, Install, and PR-Emission Helper Port

[Source: specs/xplat-006-mutation-install-pr-emission-helper-port]

XPLAT-006 shipped the mutation-capable helper substrate on the Python 3.11+
standard-library runner. It added runner-side mutation request/result handling,
atomic write primitives, fail-closed dirty-worktree checks, path-boundary and
fake-home repair guards, install inventory and doctor/preflight proof,
generated PR-body output fixtures, command-plan evidence for PR emission, and
deferred live-mutation diagnostics for helpers that still require later active
cutover approval semantics.

The feature also hardened the Codex autopilot process with a Python
standard-library phase-coverage validator and Layer 4 regression tests so
missing Phase 6.5, missing Post items, duplicate or malformed state, and
collapsed later phases fail deterministically before future autopilot runs can
advance. XPLAT-006 intentionally did not switch active Claude Code or Codex
invocation paths, generated-payload selection, public platform claims, native
installed-cache UAT, or repo-local Bash release gates. XPLAT-007 owns active
repo-local gate migration; XPLAT-008 owns Claude/Codex cutover and public
release readiness.

### Requirements Preserved

- Mutation requests and results preserve the runner envelope and expose
  mutation-specific planned/applied/skipped/no-op operation records under
  `data.mutation`.
- Apply-mode file writes use generated content, same-directory temporary files,
  `fsync`, and `os.replace`, while dirty worktrees and unsupported live command
  plans fail closed before mutation.
- Install doctor/preflight uses a committed install inventory and fake Claude,
  Codex, plugin-cache, `gh`, and `specify` fixtures by default.
- Promotion records, contract schemas, fixture manifests, and request fixtures
  are preserved under the Layer 4 mutation-helper fixture tree.
- Active Bash-backed repo-local gates, evals, payload builders, install
  verification scripts, release-readiness checks, and CI dispatch allowlist
  migration remain downstream XPLAT-007 work.

### Success Criteria

XPLAT-006 is successful because PR #281 added the mutation helper modules,
install helper module, PR-emission helper module, promotion records, install
inventory, autopilot phase-coverage validator, generated payload mirrors,
contract fixtures, focused Python tests, and full-suite verification without
touching active Claude/Codex invocation cutover or public native-platform
claims. XPLAT-007 is now unblocked for active Python tooling and release-gate
migration.

### Cleanup Note

Archived into project memory on 2026-07-04 after PR #281 merged at
`85e79cd4b5ccc0116a2c5cdd0f04ce274294075f`. The active
`specs/xplat-006-mutation-install-pr-emission-helper-port/` folder was removed
from `specs/**` in post-merge cleanup after preserving contract fixtures under
`tests/speckit-pro/unit/fixtures/mutation-helpers/contracts/`.
Recovery commands and provenance are recorded in
`.specify/memory/archive-reports/2026-07-04-xplat-006-post-merge-hygiene.md`.
