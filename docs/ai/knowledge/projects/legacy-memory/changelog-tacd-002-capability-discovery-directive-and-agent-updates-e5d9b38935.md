---
type: "speckit-legacy-memory-record"
title: "TACD-002 Capability Discovery Directive and Agent Updates"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-e5d9b38935a8336c"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# TACD-002 Capability Discovery Directive and Agent Updates

[Source: .specify/memory/archive-reports/2026-06-18-tacd-002-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-18
- **Cleanup branch**: `codex/tacd-002-post-merge-hygiene`
- **Cleanup command**: `git rm -r specs/tacd-002-capability-discovery-directive-and-agent-updates`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/tacd-002-capability-discovery-directive-and-agent-updates`

### Provenance

| PR | Title | Merge commit | Tree reference |
|----|-------|--------------|----------------|
| #221 | `feat(TACD-002): Add capability discovery foundation` | `b63dfc95525eb64f9f221d7f2513c9ab9c36b314` | `46e1c2b3f1a7d83b06815c7b34f1dc7531df53cf` |
| #222 | `feat(TACD-002): Update agent capability selection` | `da9a7c5cd6ba567f1530e396cfc69527948bf7a7` | `8c2005f42f187542de7a20c10707759b436d0777` |
| #223 | `feat(TACD-002): Document fallback evidence behavior` | `2060789358cdf4cd946d423238ee2be1f7f90675` | `a93e16d3ae648c5c13a8cc305a7c783d7119321d` |
| #224 | `feat(TACD-002): Align Claude and Codex guidance` | `4203e1011a1d67220e0e82115108759446fa04cf` | `55cb7f67ac1c8aa0e4e127bc65e6f382a8c61194` |
| #225 | `feat(TACD-002): Refresh generated capability payloads` | `12ff3667a36906552bb47ee11b7b53239d42f391` | `0e35350187cd7196412a8ab14287a492e1cd1984` |
| #226 | `feat(TACD-002): Emit ordered slice PRs` | `130abd2b6329e774207c84ab798cfb5b6dab7131` | `0ec46aa6307a8cc8f4f63d729b2a729123c2a62e` |

### Summary

TACD-002 completed the active runtime guidance tier for tool-agnostic
capability discovery. The canonical shipped artifacts include the shared
capability directive, scoped Claude and Codex agent guidance, generated Claude
and Codex payload copies, marker-emission hardening, and focused regression
tests. TACD-003 is now unblocked for prerequisite and user-facing documentation
messaging.

### Canonical Artifacts

- `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`
- `speckit-pro/agents/*.md`
- `speckit-pro/codex-agents/*.toml`
- `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh`
- `tests/speckit-pro/unit/test-multi-pr-emission.sh`
- `tests/speckit-pro/unit/test-reviewability-marker-guidance.sh`
- `dist/claude/speckit-pro/`
- `dist/codex/speckit-pro/`

### Recovery Commands

```text
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/spec.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/plan.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/tasks.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/SPEC-MOC.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/research.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/data-model.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/quickstart.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:speckit-pro/skills/speckit-autopilot/references/capability-discovery.md
git checkout 130abd2b6329e774207c84ab798cfb5b6dab7131 -- specs/tacd-002-capability-discovery-directive-and-agent-updates
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-06-18-tacd-002-post-merge-hygiene.md`.
