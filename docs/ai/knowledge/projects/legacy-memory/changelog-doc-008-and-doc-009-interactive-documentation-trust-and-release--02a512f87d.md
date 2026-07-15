---
type: "speckit-legacy-memory-record"
title: "DOC-008 and DOC-009 Interactive Documentation Trust and Release Workflow"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-02a512f87dad5569"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# DOC-008 and DOC-009 Interactive Documentation Trust and Release Workflow

[Source: .specify/memory/archive-reports/2026-06-18-doc-008-009-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-18
- **Cleanup branch**: `codex/doc-specs-post-merge-hygiene`
- **Cleanup command**: `git rm -r specs/doc-008-troubleshooting-security-trust-update-rollback specs/doc-009-maintainer-contributor-release-workflow`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**:
  - `specs/doc-008-troubleshooting-security-trust-update-rollback`
  - `specs/doc-009-maintainer-contributor-release-workflow`

### Provenance

| Spec | PR | Title | Merge commit | Tree reference |
|------|----|-------|--------------|----------------|
| DOC-008 | #220 | `docs(DOC-008): Add troubleshooting, Security, Trust, Update, and Rollback` | `a27fc5dcb2b295fd7ea2d3250d2df58692a7408b` | `0ec6e8b0dd3fecdc39233208bf0623d6d63c2954` |
| DOC-009 | #219 | `docs(DOC-009): document maintainer contributor release workflow` | `2686caa2a12dbaf460c33f37f054f40765fb2b35` | `4175b9ee51fd256943945ffb157f22c97faa7496` |

### Summary

DOC-008 shipped source-backed troubleshooting, security/trust, and
update/rollback documentation for Claude Code and Codex install, cache,
permission, version, CLI, custom-agent, managed-policy, stale-payload, and
rollback cases. DOC-009 shipped the release workflow guide for contributors and
maintainers, covering source/generated boundaries, release-readiness commands,
payload rebuilds, marketplace sync, version ownership, PR Checks behavior,
release automation, Conventional Commit titles, public-readable PR bodies, and
the DOC-010 handoff.

The cleanup also hardened `generate-spec-index.sh` and its generated Claude and
Codex payload copies for the zero-active-spec state exposed after removing the
last DOC active spec folders, so roadmap-MOC generated indexes clear
deterministically when only `specs/.gitkeep` remains.

### Canonical Artifacts

- `docs-site/src/content/docs/troubleshooting.md`
- `docs-site/src/content/docs/security-and-trust.md`
- `docs-site/src/content/docs/update-and-rollback.md`
- `docs-site/src/content/docs/install/claude-code.md`
- `docs-site/src/content/docs/install/codex.md`
- `docs-site/src/content/docs/reference.md`
- `docs-site/src/content/docs/contribute-and-release.md`

### Recovery Commands

```text
git show a27fc5dcb2b295fd7ea2d3250d2df58692a7408b:specs/doc-008-troubleshooting-security-trust-update-rollback/spec.md
git show a27fc5dcb2b295fd7ea2d3250d2df58692a7408b:specs/doc-008-troubleshooting-security-trust-update-rollback/plan.md
git show a27fc5dcb2b295fd7ea2d3250d2df58692a7408b:specs/doc-008-troubleshooting-security-trust-update-rollback/tasks.md
git show a27fc5dcb2b295fd7ea2d3250d2df58692a7408b:specs/doc-008-troubleshooting-security-trust-update-rollback/SPEC-MOC.md
git checkout a27fc5dcb2b295fd7ea2d3250d2df58692a7408b -- specs/doc-008-troubleshooting-security-trust-update-rollback

git show 2686caa2a12dbaf460c33f37f054f40765fb2b35:specs/doc-009-maintainer-contributor-release-workflow/spec.md
git show 2686caa2a12dbaf460c33f37f054f40765fb2b35:specs/doc-009-maintainer-contributor-release-workflow/plan.md
git show 2686caa2a12dbaf460c33f37f054f40765fb2b35:specs/doc-009-maintainer-contributor-release-workflow/tasks.md
git show 2686caa2a12dbaf460c33f37f054f40765fb2b35:specs/doc-009-maintainer-contributor-release-workflow/SPEC-MOC.md
git checkout 2686caa2a12dbaf460c33f37f054f40765fb2b35 -- specs/doc-009-maintainer-contributor-release-workflow
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-06-18-doc-008-009-post-merge-hygiene.md`.
