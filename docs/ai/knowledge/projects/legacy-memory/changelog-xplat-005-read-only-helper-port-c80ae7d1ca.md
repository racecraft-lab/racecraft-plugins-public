---
type: "speckit-legacy-memory-record"
title: "XPLAT-005 Read-Only Helper Port"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-c80ae7d1ca6e4e0f"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-005 Read-Only Helper Port

### Provenance

| Spec | PR | Title | Merged at | Merge commit |
|------|----|-------|-----------|--------------|
| XPLAT-005 | #276 | `feat(XPLAT-005): Add read-only helper port` | 2026-07-03T03:16:56Z | `c4642f50ae99172170798a49f0c8fd990891c0f9` |

### Summary

XPLAT-005 shipped read-only/advisory helper ports on top of the XPLAT-004
Python standard-library runner. The implementation added the helper registry,
read-only helper module, envelope/runtime integration, Python-authoritative
promotion records, request fixtures, source-checkout Bash-reference
comparisons, synthetic path and malformed-input coverage, runner metadata
refresh, and Layer 4 helper test entrypoint.

The feature deliberately did not switch active Claude Code or Codex skills,
hooks, generated payloads, install behavior, mutation helper behavior, or public
documentation claims to the runner. XPLAT-006 owns mutation, install, restack,
state-writing, and PR-emission helper ports. XPLAT-007 owns active cutover,
generated payload proof, installed-cache proof, native Windows/macOS/Linux UAT,
update/autoheal proof, and public release claims.

### Canonical Artifacts

- `speckit-pro/speckit_pro_runner/helpers/__init__.py`
- `speckit-pro/speckit_pro_runner/helpers/registry.py`
- `speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `speckit-pro/speckit_pro_runner/envelope.py`
- `speckit-pro/speckit_pro_runner/runtime.py`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py`
- `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.sh`
- `tests/speckit-pro/unit/fixtures/read-only-helpers/`
- `tests/speckit-pro/unit/fixtures/read-only-helpers/read-only-helper-feature/`
- `docs/ai/specs/.process/XPLAT-005-workflow.md`
- `docs/ai/specs/.process/XPLAT-005-design-concept.md`

### Recovery Commands

```text
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/spec.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/plan.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/tasks.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/research.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/data-model.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/quickstart.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/contracts/read-only-helper-request.schema.json
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/contracts/helper-promotion-record.schema.json
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/.process/uat-runbook.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/SPEC-MOC.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:docs/ai/specs/.process/XPLAT-005-workflow.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:docs/ai/specs/.process/XPLAT-005-design-concept.md
git checkout c4642f50ae99172170798a49f0c8fd990891c0f9 -- specs/xplat-005-read-only-helper-port
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-07-03-xplat-005-post-merge-hygiene.md`.

---
