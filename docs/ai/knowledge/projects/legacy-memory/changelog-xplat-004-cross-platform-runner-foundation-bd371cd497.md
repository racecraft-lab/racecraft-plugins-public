---
type: "speckit-legacy-memory-record"
title: "XPLAT-004 Cross-Platform Runner Foundation"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-bd371cd497fd1e5b"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-004 Cross-Platform Runner Foundation

### Provenance

| Spec | PR | Title | Merged at | Merge commit |
|------|----|-------|-----------|--------------|
| XPLAT-004 | #274 | `feat(XPLAT-004): Add cross-platform runner foundation` | 2026-07-01T22:13:40Z | `cef3ed260dabf73833d3de82f82cacdb2c7758fa` |

### Summary

XPLAT-004 shipped the source-checkout Python 3.11+ standard-library runner
foundation for SpecKit Pro. The implementation added the `speckit_pro_runner`
package, module-style runner invocation, JSON envelope validation,
runtime-info/preflight operations, deterministic diagnostics, typed path and
subprocess fixture primitives, source manifest/checksum metadata, and focused
Layer 4 runner tests.

The feature deliberately did not switch active Claude Code or Codex skills,
hooks, generated payloads, install behavior, or public documentation claims to
the runner. XPLAT-005 owns read-only helper parity, XPLAT-006 owns mutation and
install helper ports, and XPLAT-007 owns active cutover plus native
Windows/macOS/Linux installed-plugin UAT.

### Canonical Artifacts

- `speckit-pro/speckit_pro_runner/__init__.py`
- `speckit-pro/speckit_pro_runner/__main__.py`
- `speckit-pro/speckit_pro_runner/envelope.py`
- `speckit-pro/speckit_pro_runner/runtime.py`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `tests/speckit-pro/unit/test-speckit-pro-runner.py`
- `tests/speckit-pro/unit/test-speckit-pro-runner.sh`
- `tests/speckit-pro/unit/fixtures/speckit-pro-runner/contract-fixtures.json`
- `tests/speckit-pro/unit/fixtures/speckit-pro-runner/runner-foundation-changed-files.txt`
- `tests/speckit-pro/unit/fixtures/speckit-pro-runner/platform-runbook-fixtures.md`
- `docs/ai/specs/.process/XPLAT-004-workflow.md`
- `docs/ai/specs/.process/XPLAT-004-design-concept.md`

### Recovery Commands

```text
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/spec.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/plan.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/tasks.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/research.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/data-model.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/quickstart.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/contracts/platform-runbook-fixtures.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:docs/ai/specs/.process/XPLAT-004-workflow.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:docs/ai/specs/.process/XPLAT-004-design-concept.md
git checkout cef3ed260dabf73833d3de82f82cacdb2c7758fa -- specs/xplat-004-cross-platform-runner-foundation
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-07-01-xplat-004-post-merge-hygiene.md`.

---
