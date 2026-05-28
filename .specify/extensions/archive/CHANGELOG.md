# Changelog

All notable changes to the Archive extension will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-04-28

### Added

- Archive Sweep mode for discovering previously merged specs before the next
  SpecKit run starts.
- Current-target exclusion so the active spec is never archived or cleaned up
  in the same run.
- Dry-run/apply separation with `safeToApplyCleanup` and
  `dryRunProvenanceOnly` report fields.
- Cleanup gates requiring explicit `--apply-cleanup`, clean worktree, safe base
  branch, archive success, merge/tree references, and raw recovery commands.
- Provenance fields for PR URLs, merge commits, tree references, CI runs,
  Argos reviews, metadata gates, artifact manifests, screenshot retention, and
  expiration risk.
- Recovery-command reporting using `git show <merge-sha>:specs/<feature>/...`.

### Changed

- Updated the extension manifest to identify the Racecraft fork as the source.
- Expanded the command contract from memory consolidation only to
  provenance-backed archival and gated cleanup.

## [1.0.0] - 2026-03-14

### Added

- Initial release of the Archive extension
- Command: `/speckit.archive.run` — post-merge archival of feature specs into project memory
- Merges user stories, functional requirements, entities, and architecture into `.specify/memory/spec.md`
- Updates dependencies, project structure, and routing in `.specify/memory/plan.md`
- Updates agent knowledge files (GEMINI.md / AGENTS.md / CLAUDE.md)
- Appends to `.specify/memory/changelog.md` with task completion counts
- Constitution compliance enforcement before merging
- Memory directory bootstrapping on first archival
- Feature spec status update (`Draft` → `Completed`)
- Scope modifiers (`--spec-only`, `--plan-only`, `--changelog-only`, `--agent-only`)
- Extension hook support (`before_archive`, `after_archive`)
- Archival Report with absolute paths and traceability tags
