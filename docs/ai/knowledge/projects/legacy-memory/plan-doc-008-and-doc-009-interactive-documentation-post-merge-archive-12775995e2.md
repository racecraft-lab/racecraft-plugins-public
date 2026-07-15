---
type: "speckit-legacy-memory-record"
title: "DOC-008 and DOC-009 Interactive Documentation Post-Merge Archive Hygiene"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-12775995e23cfd07"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# DOC-008 and DOC-009 Interactive Documentation Post-Merge Archive Hygiene

[Source: .specify/memory/archive-reports/2026-06-18-doc-008-009-post-merge-hygiene.md]
**Branch**: `codex/doc-specs-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-18

### Scope

DOC-008 and DOC-009 completed the remaining trust and maintenance content tier
for the interactive documentation roadmap. DOC-008 owns troubleshooting,
security/trust, update, and rollback guidance. DOC-009 owns the maintainer and
contributor release workflow route. DOC-010 is the next ready docs hardening
slice after these content specs are archived.

### Architecture / Approach

- Keep the cleanup post-merge and archive-only: preserve process evidence under
  `docs/ai/specs/.process/`, remove only the completed active `specs/**`
  folders, and record recovery commands against the merge commits.
- Treat docs-site pages as the canonical shipped artifacts:
  `troubleshooting.md`, `security-and-trust.md`, `update-and-rollback.md`,
  install/reference routes, and `contribute-and-release.md`.
- Update roadmap and traceability state so DOC-008 and DOC-009 are completed
  and DOC-010 is ready to scaffold.
- Regenerate SpecKit indexes after active spec removal so roadmap MOCs no
  longer link to archived spec folders.
- Harden the spec-index generator and generated payload copies for the
  zero-active-spec cleanup state, where `specs/**` contains only
  `specs/.gitkeep` and roadmap-MOC generated zones must clear
  deterministically.

### Test Strategy

- Confirm PR #220 and PR #219 merged to `main`.
- Validate JSON state after replacing archive state.
- Regenerate and check SpecKit generated indexes after active spec removal.
- Verify active `specs/**` contains only `specs/.gitkeep` after cleanup.
- Run focused generator regression coverage for zero active spec directories.
- Run `git diff --check` and the deterministic SpecKit test suite.

### Cleanup Notes

`specs/doc-008-troubleshooting-security-trust-update-rollback` and
`specs/doc-009-maintainer-contributor-release-workflow` were removed from active
`specs/**` cleanup after their docs-site content landed through PR #220 and PR
#219. Recovery commands and provenance are recorded in the DOC-008/DOC-009
archive report.
