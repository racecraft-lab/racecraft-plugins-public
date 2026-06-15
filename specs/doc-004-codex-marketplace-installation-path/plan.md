# Implementation Plan: Codex marketplace installation path

**Branch**: `doc-004-codex-marketplace-installation-path` | **Date**: 2026-06-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/doc-004-codex-marketplace-installation-path/spec.md`

## Summary

Deliver DOC-004 as a documentation-only Codex install path. Expand the existing
Astro and Starlight Codex install page, then align the root README and SpecKit Pro
README so all three entry points agree on repo-scoped marketplace use, personal
or local payload layout, installed plugin cache behavior, `$install`, restart,
custom-agent verification, and bounded first-install safety including lifecycle
hook payload awareness. Include a shallow stale-after-update checkpoint that
names the surfaces to inspect, when to rerun `$install`, when to restart, and
where to go for deeper DOC-007 and DOC-008 reference and troubleshooting.

No runtime, manifest, generated payload, install script, TOML template, hook,
release automation, or marketplace behavior changes are planned.

## Technical Context

**Language and Version**: Markdown and MDX content plus Astro and Starlight docs site metadata

**Primary Dependencies**: Astro 6.4.6, Starlight 0.40.0, pnpm 10.25.0

**Storage**: Not applicable

**Testing**: `cd docs-site && pnpm validate`, `cd docs-site && pnpm validate:links`, `bash tests/speckit-pro/run-all.sh`, and manual command-snippet review

**Target Platform**: Static docs site plus GitHub-rendered README files

**Project Type**: Documentation site and repository Markdown documentation

**Performance Goals**: Not applicable for runtime performance; docs must remain scannable and task-first

**Constraints**: Consume the DOC-002 docs-site shell; keep one focused Codex install page; keep DOC-004 bounded to first-install safety; defer reference depth to DOC-007 and troubleshooting plus security lifecycle depth to DOC-008

**Accessibility Constraints**: The Codex install page must use semantic headings, lists, table headers and captions where tables remain appropriate, descriptive links, labeled command groups, and text-visible warnings. The install path matrix must stay readable on mobile and for screen-reader users by providing a compact list or card alternative when the table becomes dense.

**Scale and Scope**: Three user-facing documentation entry points plus plan artifacts

**Reviewability Budget**: Primary surface: docs process; projected reviewable LOC: 250-500 documentation LOC; projected production-code files: 0; planned documentation entry points: 3; projected total implementation files: 3; budget result: within budget

## Declared File Operations

- MODIFIED README.md
- MODIFIED speckit-pro/README.md
- MODIFIED docs-site/src/content/docs/install/codex.md

Explicitly out of implementation scope:

- DO NOT MODIFY repo marketplace manifests.
- DO NOT MODIFY source or generated Codex plugin manifests.
- DO NOT MODIFY Codex custom-agent TOML templates.
- DO NOT MODIFY Codex install scripts.
- DO NOT MODIFY Codex hook payload configuration.
- DO NOT MODIFY generated payload behavior, release automation, marketplace behavior, or plugin runtime behavior

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Plugin Structure Compliance | PASS | Planned changes are docs-only and do not alter plugin manifests, plugin layout, hooks, skills, agents, or generated payloads. Existing Layer 1 remains the structural validation command. |
| II. Script Safety | PASS | No scripts are planned. If implementation accidentally touches scripts, stop and re-plan as a narrow source correction before changing behavior. |
| III. Semantic Versioning | PASS | No manifest or release version changes are planned. |
| IV. Test Coverage Before Merge | PASS | Full repo suite remains required by DOC-004 despite docs-only scope: `bash tests/speckit-pro/run-all.sh`. |
| V. Conventional Commits | PASS | PR title must use a conventional commit prefix, likely `docs(speckit-pro): clarify Codex install paths`. |
| VI. KISS, Simplicity & YAGNI | PASS | One focused Codex page plus concise README alignment avoids new components, new docs routes, or broad DOC-007 and DOC-008 material. |

Reviewability gate:

- Primary review surface: docs process.
- Secondary surfaces: none.
- Projected reviewable LOC: 250-500 docs LOC.
- Projected production-code files: 0.
- Planned documentation entry points: 3.
- Projected total implementation files: 3.
- Budget result: within budget; no split exception needed.
- Split decision: keep DOC-004 as one slice. DOC-007 owns deeper reference content. DOC-008 owns troubleshooting, update, remove, rollback, stale-cache forensics, managed policy, and full trust plus security depth.
- PR review packet source: docs changes, why, non-goals, review order, scope budget, traceability from FR and SC markers to files, validation evidence, known gaps, and rollback notes.

## Project Structure

### Documentation (this feature)

```text
specs/doc-004-codex-marketplace-installation-path/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── codex-install-content-contract.md
└── tasks.md              # Created later by /speckit-tasks
```

### Source Documentation

```text
README.md
speckit-pro/README.md
docs-site/
├── package.json
└── src/content/docs/install/codex.md
```

### Source Evidence Read During Planning

```text
docs/ai/specs/.process/DOC-004-workflow.md
docs/ai/specs/.process/DOC-004-design-concept.md
specs/doc-004-codex-marketplace-installation-path/spec.md
docs/prd-interactive-documentation.md
docs/roadmap-interactive-documentation.md
docs/ai/specs/interactive-documentation-technical-roadmap.md
README.md
speckit-pro/README.md
docs-site/src/content/docs/install/codex.md
docs-site/package.json
.agents/plugins/marketplace.json
speckit-pro/.codex-plugin/plugin.json
dist/codex/speckit-pro/.codex-plugin/plugin.json
speckit-pro/codex-skills/install/SKILL.md
speckit-pro/codex-skills/install/scripts/install-codex-agents.sh
speckit-pro/codex-agents/*.toml
speckit-pro/codex-hooks.json
```

**Structure Decision**: Use the existing DOC-002 Astro and Starlight route at
`docs-site/src/content/docs/install/codex.md` as the detailed install guide.
Keep the README surfaces concise and link or summarize the same critical
invariants rather than duplicating the whole guide.

## Phase 0: Research

**Output**: [research.md](research.md)

Research resolved the platform wording and implementation boundaries:

- Official OpenAI Codex docs were refreshed for plugin marketplaces, build
  plugins, skills, subagents, permissions, approvals, and security.
- Local `codex plugin marketplace add --help` was checked for CLI source form
  syntax and `--json`; it emitted a non-blocking PATH-alias warning under the
  sandbox but returned the needed help text.
- Local checked-in files confirm the repo-scoped marketplace points at
  `./dist/codex/speckit-pro`, source and dist manifests share version `2.14.0`,
  and the install skill plus script copy nine TOML custom-agent files.
- Source and package drift is resolved as a documentation decision: user-facing
  verification lists the installer-copied nine TOML files and does not list
  `uat-runbook-author.toml` as expected installed output.
- OpenAI's local plugin guidance and SpecKit Pro's install skill both support a
  bounded stale-update checkpoint: after plugin changes, update the marketplace
  target or copied payload and restart Codex; when bundled custom-agent TOML
  templates change, rerun `$install`, verify the copied files, then restart.

## Phase 1: Design & Contracts

**Outputs**:

- [data-model.md](data-model.md)
- [contracts/codex-install-content-contract.md](contracts/codex-install-content-contract.md)
- [quickstart.md](quickstart.md)

Design decisions:

- Treat the install page as a route-section contract, not an application data
  model.
- Include an install path matrix with repo-scoped marketplace, personal or local
  marketplace, and CLI marketplace source forms.
- Keep the install path matrix accessible: use clear headers plus caption and summary
  context if rendered as a table, and provide a mobile-readable or
  screen-reader-friendly list or card alternative when the matrix would otherwise
  require difficult horizontal scanning.
- Place generated payload guidance near the top: `dist/codex/speckit-pro/` is
  the installable Codex payload; `speckit-pro/` is the mixed authoring source
  tree.
- Include a custom-agent checklist after plugin installation: run
  `@SpecKit Pro -> install` or `$install`, confirm destination, verify the nine
  TOML filenames, restart Codex, then run a simple `$speckit-*` flow.
- Include a bounded stale-update checkpoint after verification: if a plugin
  appears stale, inspect the marketplace source or copied personal payload,
  generated payload, installed plugin cache, selected custom-agent destination,
  and restart state; mention symptoms such as old skill copy, old plugin
  metadata, unchanged custom-agent behavior, or copied payload drift; link to
  DOC-008 for deeper troubleshooting, update, remove, and rollback guidance, and DOC-007 for
  reference depth.
- Keep the safety block limited to sandbox, approvals, network access,
  outside-workspace writes, installed cache and source distinction, bundled
  lifecycle hook configuration, and external app plus MCP authentication as
  first-install expectations, with warning text
  visible in the copy rather than conveyed only by color, icon, or callout
  styling.

## Source-Evidence Notes

Official OpenAI sources refreshed on 2026-06-14:

- Codex plugins
- Building Codex plugins
- Codex skills
- Codex subagents
- Codex permissions
- Codex approvals and security

Local CLI source refreshed on 2026-06-14:

- `codex plugin marketplace add --help`

Local source-evidence files are listed in "Source Evidence Read During
Planning" above.

## Validation Plan

Implementation PR readiness requires:

1. `cd docs-site && pnpm validate`
2. `cd docs-site && pnpm validate:links`
3. `bash tests/speckit-pro/run-all.sh`
4. Manual source-backed command-snippet review covering every changed Codex
   command and path snippet.
5. Manual accessibility review covering semantic headings, lists, and tables,
   descriptive link text, command snippet labels by platform and install scope,
   text-visible warnings, and install path matrix readability on mobile and
   screen readers.

The current DOC-002 `validate:links` script aliases `pnpm build`; DOC-004 will
use it as-is and will not change docs-site validation scripts.

## Complexity Tracking

No constitution violations are planned.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| None | Not applicable | Not applicable |
