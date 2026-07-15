---
type: "speckit-legacy-memory-record"
title: "DOC-008 and DOC-009 Interactive Documentation Trust and Release Workflow"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-a9c99433fb3d6285"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# DOC-008 and DOC-009 Interactive Documentation Trust and Release Workflow

[Source: specs/doc-008-troubleshooting-security-trust-update-rollback; specs/doc-009-maintainer-contributor-release-workflow]
**Branches**: `doc-008-troubleshooting-security-trust-update-rollback`, `doc-009-maintainer-contributor-release-workflow` · **Status**: Completed · **Archived**: 2026-06-18

### Summary

DOC-008 completed the troubleshooting, security/trust, update, and rollback
documentation tier for the interactive documentation roadmap. The shipped docs
expand `docs-site/src/content/docs/troubleshooting.md`, deepen
`docs-site/src/content/docs/security-and-trust.md`, add
`docs-site/src/content/docs/update-and-rollback.md`, and connect the install
and reference routes to those support pages.

DOC-009 completed the maintainer and contributor release workflow tier. The
shipped docs deepen `docs-site/src/content/docs/contribute-and-release.md` with
source-of-truth mapping, change-type routing, release-readiness commands,
payload and marketplace sync guidance, version ownership, public-readable PR
expectations, current PR Checks behavior, release automation observations, and
the DOC-010 handoff.

### User Stories

- **DOC-008 US1 - Diagnose a failure symptom.** Users can inspect symptoms,
  likely causes, read-only diagnostic files or commands, and recommended fixes.
- **DOC-008 US2 - Evaluate security and trust boundaries.** Users can
  distinguish official platform behavior, repository facts, installed runtime
  state, and recommended practice without reading the full repository.
- **DOC-008 US3 - Recover from stale or incorrect installs.** Users can follow
  update, refresh, reinstall, remove, rollback, stale-payload, stale-cache, and
  version-sync guidance for Claude Code and Codex.
- **DOC-009 US1 - Classify the change path.** Contributors can identify whether
  a change is docs-only, plugin source, generated payload, marketplace, or
  release automation work and see the expected evidence.
- **DOC-009 US2 - Complete release readiness.** Maintainers can verify parity,
  manifest/version consistency, generated payloads, release-readiness tests, and
  docs-site validation when relevant.
- **DOC-009 US3 - Review PR metadata and evidence.** Reviewers can evaluate
  Conventional Commit titles, public-readable bodies, review order, scope
  budget, traceability, verification, gaps, and rollback notes.
- **DOC-009 US4 - Understand docs-only CI and DOC-010 handoff.** Docs maintainers
  can distinguish current PR Checks behavior from future docs-site CI hardening.

### Functional Requirements

- Troubleshooting rows include symptom, likely cause, diagnostic file or
  command, recommended fix, platform label, and source links.
- Security and trust docs separate official vendor behavior, repository facts,
  generated payloads, installed cache/runtime state, managed policy, and
  recommended practice.
- Update and rollback docs cover marketplace refresh, plugin reinstall/remove,
  rollback boundaries, stale payloads, stale caches, version sync, and platform
  reload/restart needs.
- Contributor/release docs map authoring source, generated payloads,
  marketplace registries, release scripts, tests, docs-site files, generated
  reference pages, CI behavior, release-please, and PR conventions.
- Release-readiness docs explain `bash scripts/build-plugin-payloads.sh`,
  `bash scripts/sync-marketplace-versions.sh`, `bash tests/speckit-pro/run-all.sh`,
  `pnpm --dir docs-site reference:check`, and `pnpm --dir docs-site validate`
  in context.
- DOC-010 owns future search, accessibility, deep-link, responsive, docs-site
  CI, manifest/payload consistency, and safe command-snippet hardening.

### Success Criteria

- DOC-008 AC-8.1 through AC-8.6 are satisfied by static docs-site pages and
  source-backed support links.
- DOC-009 AC-9.1 through AC-9.6 are satisfied by the existing
  `/contribute-and-release` route and linked reference/source evidence.
- Both specs remained docs-only: no plugin behavior, manifests, hooks, generated
  payload semantics, release automation, or CI behavior changed as part of the
  shipped content.

### Cleanup Note

The active DOC-008 and DOC-009 spec folders were removed from `specs/**`
cleanup after PR #220 and PR #219 merged. Recovery commands and provenance are
recorded in
`.specify/memory/archive-reports/2026-06-18-doc-008-009-post-merge-hygiene.md`.

---
