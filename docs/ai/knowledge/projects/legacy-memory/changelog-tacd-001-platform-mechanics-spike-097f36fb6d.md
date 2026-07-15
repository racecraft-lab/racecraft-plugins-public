---
type: "speckit-legacy-memory-record"
title: "TACD-001 Platform Mechanics Spike"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-097f36fb6ddccc6f"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# TACD-001 Platform Mechanics Spike

[Source: .specify/memory/archive-reports/2026-06-18-tacd-001-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-18
- **Cleanup branch**: `codex/tacd-001-post-merge-hygiene`
- **Cleanup command**: `git rm -r specs/tacd-001-platform-mechanics-spike`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/tacd-001-platform-mechanics-spike`

### Provenance

| PR | Title | Merge commit | Tree reference |
|----|-------|--------------|----------------|
| #211 | `feat(speckit-pro): Add platform mechanics spike foundation` | `2104432cb8d92c0088b99f02e0922d5ebf433a98` | `ab754c7e7fdd61281c97e8d4ca140a414cec9a85` |
| #212 | `feat(speckit-pro): Document runtime capability mechanics` | `e9d3c08af55658b97452c86c294bae0b340a3bc4` | `7fd0642c4f076ab5a0d0830987c1833e15b6daf1` |
| #213 | `feat(speckit-pro): Classify active and historical references` | `dfa18a20691b86724cc05008c2b3fae93a0d9127` | `60a3970fd64cfbe3c6f1f61421cbe6532ecf56f6` |
| #214 | `feat(speckit-pro): Recommend directive home and handoffs` | `46d01dcf081a8c416c692db497daea5cae11a801` | `61f2a4a2118edc6b8eeca93c285741119a183eac` |
| #216 | `docs(TACD): Adopt platform spike decisions` | `62dc58a46419ed09c1aa506974ef8c7fbab998ee` | `060dd16f5186049ce8455a50c77a88a2e78ed441` |

### Summary

TACD-001 completed the report-only platform mechanics spike for
tool-agnostic capability discovery. The canonical report records active
named-tool reference categories, Claude/Codex capability mechanics, the selected
shared-reference-plus-runtime-pointers directive home, the TACD-004 allowlist,
and downstream handoffs for TACD-002, TACD-003, and TACD-004. PR #216 adopted
those decisions into the PRD and technical roadmap.

### Canonical Artifacts

- `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- `docs/prd-tool-agnostic-capability-discovery.md`
- `docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md`
- `docs/ai/specs/tool-agnostic-capability-discovery-roadmap-MOC.md`

### Recovery Commands

```text
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/spec.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/plan.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/tasks.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/SPEC-MOC.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/research.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/data-model.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/quickstart.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:docs/ai/research/tool-agnostic-capability-discovery-spike.md
git show 62dc58a46419ed09c1aa506974ef8c7fbab998ee:docs/prd-tool-agnostic-capability-discovery.md
git show 62dc58a46419ed09c1aa506974ef8c7fbab998ee:docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md
git checkout 46d01dcf081a8c416c692db497daea5cae11a801 -- specs/tacd-001-platform-mechanics-spike
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-06-18-tacd-001-post-merge-hygiene.md`.
