---
type: "speckit-legacy-memory-record"
title: "DOC-003 and DOC-004 Platform Install Paths"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-d4161c341024aba7"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# DOC-003 and DOC-004 Platform Install Paths

[Source: .specify/memory/archive-reports/2026-06-15-doc-003-004-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-15
- **Cleanup branch**: `codex/doc-003-004-post-merge-hygiene`
- **Cleanup command**: `git rm -r specs/doc-003-claude-code-marketplace-installation-path specs/doc-004-codex-marketplace-installation-path`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**:
  - `specs/doc-003-claude-code-marketplace-installation-path`
  - `specs/doc-004-codex-marketplace-installation-path`

### Provenance

| Spec | PR | Title | Merge commit | Tree reference | Task completion |
|------|----|-------|--------------|----------------|-----------------|
| DOC-003 | #187 | `docs(DOC-003): add Claude Code install route` | `afc197a278001c7b8c2ffeb973c359971676d597` | `ef3e4eb22c286bafa1657e78c5461b774e8da1e6` | 39 / 39 |
| DOC-004 | #186 | `docs(DOC-004): add Codex marketplace installation path` | `bc48441c494d34a7df9876c3bdebabc4db8408a5` | `31c75c95d787ea2661216e29e6ec8b0a8ab19625` | 20 / 20 |

### Summary

DOC-003 and DOC-004 completed the platform-specific install tier of the
interactive documentation roadmap. The canonical shipped docs are:

- `docs-site/src/content/docs/install/claude-code.md`
- `docs-site/src/content/docs/install/codex.md`

### Recovery Commands

```text
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/spec.md
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/plan.md
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/tasks.md
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/SPEC-MOC.md
git checkout afc197a278001c7b8c2ffeb973c359971676d597 -- specs/doc-003-claude-code-marketplace-installation-path

git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/spec.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/plan.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/tasks.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/SPEC-MOC.md
git checkout bc48441c494d34a7df9876c3bdebabc4db8408a5 -- specs/doc-004-codex-marketplace-installation-path
```

The detailed per-file `git show` recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-15-doc-003-004-post-merge-hygiene.md`.

---
