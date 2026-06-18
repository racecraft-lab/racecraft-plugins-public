# DOC-009 Design Concept: Maintainer and contributor release workflow

## Source Inputs

- Roadmap entry: `docs/ai/specs/interactive-documentation-technical-roadmap.md`
- PRD requirements: `docs/prd-interactive-documentation.md` DOC-FR-009 / AC-9.1 through AC-9.6
- Traceability row: `docs/traceability-interactive-documentation.md` DOC-FR-009
- Existing route shell: `docs-site/src/content/docs/contribute-and-release.md`
- Repository guidance: `AGENTS.md`, `CLAUDE.md`
- CI and release workflows: `.github/workflows/pr-checks.yml`, `.github/workflows/release.yml`
- Release scripts: `scripts/build-plugin-payloads.sh`, `scripts/sync-marketplace-versions.sh`
- Validation surface: `tests/speckit-pro/run-all.sh`, `docs-site/package.json`

## Roadmap Seed

DOC-009 is a P1 documentation-product slice that depends on DOC-007 and enables
DOC-010. The goal is to give contributors a release-ready checklist for
docs/plugin changes.

Reviewability budget at setup:

- Primary surface: docs/process
- Projected reviewable LOC: 380
- Production files: 0
- Total files: about 6
- Setup gate result: pass, with 395 reviewable LOC, 0 production files, 6 total files, no warnings, and no blockers

## Goals

- Expand the existing `/contribute-and-release` route into a full, source-backed
  playbook for maintainers and contributors.
- Explain the end-to-end path for docs changes, plugin source changes, generated
  payload changes, marketplace sync, CI, release-please, Conventional Commits,
  public-readable PR titles/bodies, and release readiness.
- Give docs-only PRs a separate lighter path while still naming the checks that
  prove the PR is ready.
- Make the release checklist actionable: source/dist parity, Claude/Codex
  marketplace parity, manifest version consistency, generated payload
  validation, full deterministic test suite expectation, and docs-site validation
  where relevant.
- Keep current docs-site CI as a handoff note to DOC-010 instead of promising
  checks that do not exist yet.

## Non-goals

- Do not change CI workflows, release automation behavior, release-please config,
  plugin manifests, marketplace files, generated payloads, scripts, or tests as
  part of DOC-009 unless a downstream implementation task finds a broken source
  citation that cannot be documented honestly.
- Do not duplicate all of `CLAUDE.md` or `AGENTS.md`; explain the workflow inline
  and link/source-cite the deeper repository guidance.
- Do not implement future docs-site CI hardening. Record the current gap and hand
  it to DOC-010.
- Do not turn generated reference pages into hand-authored documentation unless
  the generator contract explicitly requires it.

## Grill Me Q&A Log

| Question | Selected answer | Design effect |
|---|---|---|
| Who should the release workflow optimize for first? | Balanced | Write for maintainers and contributors together, with role-specific checkpoints rather than a maintainer-only page. |
| How deep should the release workflow content go? | Full playbook | Include the complete operational path in the page, not only a brief orientation shell. |
| What release/change scope should DOC-009 cover? | Docs and plugins | Cover docs changes, plugin source changes, generated payloads, marketplaces, tests, CI, commits, PRs, and release automation. |
| Where should the full-playbook duplication boundary sit? | Guide plus links | Explain the full workflow inline, but keep detailed repo internals in `AGENTS.md`, `CLAUDE.md`, workflow files, and generated references. |
| What validation policy should the release workflow teach? | Full suite always | Present `bash tests/speckit-pro/run-all.sh` as the release-readiness expectation, with docs-site validation added when docs-site files change. |
| How should DOC-009 describe release automation? | Observable handoff | Explain what maintainers see from release-please, payload sync, marketplace sync, and PR checks without documenting hidden implementation internals as user obligations. |
| What page shape should DOC-009 target? | Single route | Deepen `docs-site/src/content/docs/contribute-and-release.md`; do not create a new route. |
| How should docs-only PR behavior be handled? | Separate path | Add a distinct docs-only path that names lighter changed-file behavior while preserving release-readiness checks. |
| How should future docs-site CI be described? | Handoff note | State current checks and hand off required CI hardening to DOC-010. |

## Proposed Content Model

Target file:

- `docs-site/src/content/docs/contribute-and-release.md`

Recommended page sections:

1. Purpose and role split
2. Source of truth map: authoring source, generated payloads, marketplaces,
   release scripts, tests, docs-site content, and generated reference pages
3. Change-type decision matrix:
   - Docs-only
   - Plugin source
   - Generated payload/dist
   - Marketplace registry
   - Release automation
4. Contributor path:
   - Pick the smallest source surface
   - Avoid editing generated payloads unless the change is a generated sync
   - Use Conventional Commits and public-readable PR titles/bodies
   - Include verification commands in the PR body
5. Maintainer release-readiness path:
   - Confirm source/dist parity
   - Rebuild payloads with `bash scripts/build-plugin-payloads.sh`
   - Sync marketplace versions with `bash scripts/sync-marketplace-versions.sh`
   - Run `bash tests/speckit-pro/run-all.sh`
   - For docs-site changes, run `pnpm --dir docs-site validate`
   - Review CI behavior for docs-only and plugin-changing PRs
6. Version field guidance:
   - Do not manually edit generated marketplace version fields as a default
   - Let release-please own release version bumps
   - Use sync scripts when release automation or maintainer workflow requires
     generated payload/marketplace parity
7. Release automation handoff:
   - Explain release-please PR creation from `main`
   - Explain generated payload sync PR behavior at a user-observable level
   - Name the PR checks and stable sentinel behavior
8. Final release-readiness checklist
9. DOC-010 handoff for docs-site CI, search, accessibility, deep links, and
   validation hardening

## Acceptance Criteria Mapping

- AC-9.1: The change-type matrix lists required checks for docs-only, plugin
  source, dist payload, marketplace, and release automation changes.
- AC-9.2: The maintainer path explains `bash scripts/build-plugin-payloads.sh`,
  `bash scripts/sync-marketplace-versions.sh`, and
  `bash tests/speckit-pro/run-all.sh`.
- AC-9.3: Version guidance states which version fields are release-please-owned,
  generated, or manually reviewed.
- AC-9.4: The final checklist covers source/dist parity, Claude/Codex
  marketplace parity, manifest version consistency, and generated payload
  validation.
- AC-9.5: Contributor guidance includes Conventional Commit and public-readable
  PR title/body expectations.
- AC-9.6: Docs-only CI behavior is explained from `.github/workflows/pr-checks.yml`;
  future docs-site CI is explicitly handed to DOC-010.

## Planning Constraints

- Use source-backed statements only. Verify every workflow or command claim
  against checked-in files before writing it into the docs page.
- Keep generated reference pages generated. If `docs-site/src/content/docs/reference/*.md`
  needs to change, update the generator or rerun the generator according to its
  existing contract.
- Avoid broad release-policy rewrites. DOC-009 is documentation, not a release
  automation change.
- Keep the public docs tone practical and scannable; do not expose internal
  SpecKit task IDs in the published page except when linking source artifacts.

## Open Questions for Clarify

- Should the final page include a compact command block for each change type, or
  one consolidated release-readiness command block with explanatory text above
  it?
- Should generated reference pages be linked from every release section, or only
  from the source-of-truth map and final checklist?
- Should the docs-only path require `pnpm --dir docs-site validate` for every
  docs-site edit, or reserve it for changes under `docs-site/` while non-site
  Markdown uses the repository shell tests and source review?

## Suggested Validation

- `pnpm --dir docs-site reference:check`
- `pnpm --dir docs-site validate`
- `bash tests/speckit-pro/run-all.sh`

