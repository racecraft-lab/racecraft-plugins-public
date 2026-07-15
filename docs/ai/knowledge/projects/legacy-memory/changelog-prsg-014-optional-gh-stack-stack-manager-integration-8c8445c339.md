---
type: "speckit-legacy-memory-record"
title: "PRSG-014 Optional gh-stack Stack Manager Integration"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-8c8445c33952d884"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# PRSG-014 Optional gh-stack Stack Manager Integration

[Source: .specify/memory/archive-reports/2026-06-14-prsg-014-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-14
- **Cleanup branch**: `codex/post-merge-archive-hygiene`
- **Cleanup command**: `git rm -r specs/prsg-014-optional-gh-stack-stack-manager-integration`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/prsg-014-optional-gh-stack-stack-manager-integration`

### Provenance

| PR | Title | Merge commit | Tree reference |
|----|-------|--------------|----------------|
| #181 | `feat(speckit-pro): Add optional gh-stack stack manager integration` | `4b8342f42db3223db6955a1390b30949b8caea8c` | `ca39ded7975c93fc93217144121237b3295abce3` |

### Summary

PRSG-014 added optional `gh-stack` support detection and stack-aware
create/sync/restack evidence while preserving explicit GitHub base/head PR
operations as the fallback. Missing, unsupported, ambiguous, unsafe, or
topology-incompatible `gh stack` environments fall back before mutation.
Partial or unknown `gh-stack` mutations block with recoverable state instead of
switching managers.

### Recovery Commands

```text
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/spec.md
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/plan.md
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/tasks.md
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/SPEC-MOC.md
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/contracts/stack-manager-decision.schema.json
git checkout 4b8342f42db3223db6955a1390b30949b8caea8c -- specs/prsg-014-optional-gh-stack-stack-manager-integration
```

The detailed per-file `git show` recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-14-prsg-014-post-merge-hygiene.md`.

---
