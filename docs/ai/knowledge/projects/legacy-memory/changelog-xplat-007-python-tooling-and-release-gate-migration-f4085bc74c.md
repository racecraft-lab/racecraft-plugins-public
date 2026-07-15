---
type: "speckit-legacy-memory-record"
title: "XPLAT-007 Python Tooling and Release-Gate Migration"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-f4085bc74c58926b"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-007 Python Tooling and Release-Gate Migration

### Provenance

| Spec | PR | Title | Merged at | Merge commit |
|------|----|-------|-----------|--------------|
| XPLAT-007 | #284 | `feat(XPLAT-007): Add gate dispatch foundation` | 2026-07-05T17:16:16Z | `6c0af6cf6cd53e1569bcb03c9a56d939360a4b24` |
| XPLAT-007 | #285 | `feat(XPLAT-007): Update Python repo-local gate runner` | 2026-07-05T18:08:14Z | `cb1697290b8f7cb289d0740e59c899285dc95c33` |
| XPLAT-007 | #286 | `feat(XPLAT-007): Update payload install release gates` | 2026-07-05T18:34:53Z | `a0d2dd015f0a33e85634256061926e5274fdb69a` |
| XPLAT-007 | #287 | `feat(speckit-pro): Update Review Active No-Shell Guardrails` | 2026-07-05T18:57:01Z | `0ff2d8d731698cde02b334cdc3b2a377216b5d45` |

### Summary

XPLAT-007 shipped Python-authoritative repo-local suite, payload,
install-verification, release-readiness, and active-path guard gates through
the existing `speckit_pro_runner` JSON envelope. The implementation added the
gate package, runner dispatch, CI dispatch updates, maintainer command updates,
promotion records, request fixtures, case fixtures, active no-shell guard
coverage, runner metadata refreshes, and focused Layer 4 gate tests.

The feature deliberately did not switch installed Claude Code or Codex runtime
surfaces, publish generated release payloads, run native installed-plugin UAT,
or make public platform/update/autoheal claims. XPLAT-008 owns those final
release gates.

### Canonical Artifacts

- `speckit-pro/speckit_pro_runner/gates/`
- `speckit-pro/speckit_pro_runner/runtime.py`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `.github/workflows/pr-checks.yml`
- `.github/workflows/release.yml`
- `CLAUDE.md`
- `docs-site/src/content/docs/contribute-and-release.md`
- `docs-site/src/content/docs/reference/tests.md`
- `tests/speckit-pro/run-all.sh`
- `tests/speckit-pro/layer1-structural/validate-pr-checks-sentinel.sh`
- `tests/speckit-pro/layer1-structural/validate-release-workflow.sh`
- `tests/speckit-pro/unit/test-speckit-pro-gates.py`
- `tests/speckit-pro/unit/fixtures/runner-gates/`
- `docs/ai/specs/.process/XPLAT-007-workflow.md`
- `docs/ai/specs/.process/XPLAT-007-design-concept.md`

### Recovery Commands

```text
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/spec.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/plan.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/tasks.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/research.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/data-model.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/quickstart.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/migrated-gate-request.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/migrated-gate-result.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/promotion-record.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/payload-evidence.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/install-verification-result.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/release-readiness-result.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/active-path-guard-result.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:docs/ai/specs/.process/XPLAT-007-workflow.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:docs/ai/specs/.process/XPLAT-007-design-concept.md
git checkout 0ff2d8d731698cde02b334cdc3b2a377216b5d45 -- specs/xplat-007-python-tooling-and-release-gate-migration
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-07-05-xplat-007-post-merge-hygiene.md`.

---
