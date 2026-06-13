# Racecraft Interactive Documentation Technical Roadmap

**Target PRD:** [docs/prd-interactive-documentation.md](prd-interactive-documentation.md)  
**Date:** 2026-06-12  
**Status:** DOC-002 ready for SPEC decomposition
**Intended downstream consumer:** Spec-Driven Development autopilot  
**SpecKit compatibility copy:** [docs/ai/specs/interactive-documentation-technical-roadmap.md](ai/specs/interactive-documentation-technical-roadmap.md)

---

## 1. Autopilot-Ready Property

Every user-visible PRD feature group has exactly one roadmap SPEC with stable IDs, explicit acceptance criteria, likely source files, validation steps, dependencies, risks, and no unresolved product decision that blocks scoping. Open questions are scoped to the SPEC that should resolve them.

## 2. Roadmap Overview

The work is decomposed into 10 vertical SPECs across 6 dependency tiers.

| Tier | Specs | Purpose | Parallelization |
|---|---|---|---|
| 1 | DOC-001 | Choose site stack and IA foundation | Sequential |
| 2 | DOC-002 | Build docs IA/landing shell | Sequential after DOC-001 |
| 3 | DOC-003, DOC-004 | Platform-specific install paths | Parallel |
| 4 | DOC-005, DOC-006 | First-run tutorial and safe interactive aids | Parallel after platform paths |
| 5 | DOC-007, DOC-008, DOC-009 | Reference, troubleshooting/trust, maintainer workflow | Parallel with shared source evidence |
| 6 | DOC-010 | Search/accessibility/deep links/docs CI | Sequential hardening after site and interactive aids |

**Execution order:** DOC-001 -> DOC-002 -> DOC-003/DOC-004 -> DOC-005/DOC-006 -> DOC-007/DOC-008/DOC-009 -> DOC-010

## 3. Dependency Graph

```text
DOC-001 Static docs framework and IA spike
  |
  v
DOC-002 Landing page and IA shell
  |                         |
  v                         v
DOC-003 Claude path    DOC-004 Codex path
  |             \           /      |
  |              v         v       |
  |         DOC-005 First run |
  |              |         |       |
  |              v         v       |
  +--------> DOC-006 Interactive aids
                   |
                   v
DOC-007 Reference -> DOC-008 Troubleshooting/trust
          \             /
           v           v
       DOC-009 Maintainer workflow
                   |
                   v
       DOC-010 Search/a11y/docs validation
```

## 4. SPEC Catalog

### DOC-001: Static docs framework and IA spike

- **Status:** Completed and archived after PR #163. Canonical decision record: `docs/ai/research/interactive-documentation-framework-spike.md`.
- **Maps from PRD:** DOC-FR-001
- **User outcome:** Maintainers can select the static docs-site stack with evidence and start implementation without re-researching core tradeoffs.
- **Scope:** Timeboxed research-only spike comparing Docusaurus/MDX, VitePress, Astro/Starlight, and a repo-native fallback. Produce a decision record, package/build/test implications, hosting options, and Diataxis IA skeleton. This is a Spike, sized by timebox rather than LOC.
- **Vertical-slice rationale:** Delivers one decision artifact that unblocks the site foundation without modifying product code.
- **Non-goals:** Building the site; migrating README content; deploying hosting; adding analytics.
- **Source files likely affected:** `docs/prd-interactive-documentation.md`, `docs/roadmap-interactive-documentation.md`, optional `docs/ai/research/interactive-documentation-framework-spike.md`.
- **New files likely needed:** `docs/ai/research/interactive-documentation-framework-spike.md`.
- **Dependencies:** None.
- **Acceptance criteria:** AC-1.1, AC-1.2, AC-1.3, AC-1.4.
- **Validation plan:** Review cited official docs; confirm absence/presence of existing site toolchain; record decision; no build or prototype is expected in DOC-001.
- **Reviewability Budget:** Primary surface: docs/process | Projected reviewable LOC: 0 | Production files: 0 | Total files: 1-2 | Budget result: spike, LOC not applicable
- **Risks:** Spike could balloon into implementation; framework docs may change.
- **Open questions:** None for DOC-001 after the decision record; DOC-002 owns concrete Astro/Starlight GitHub Pages configuration.
- **Suggested implementation notes:** Keep this as a research artifact plus explicit recommendation; do not create `package.json`, lockfiles, site config, CI, runtime files, or prototypes until DOC-002.

### DOC-002: Unified landing page and IA shell

- **Maps from PRD:** DOC-FR-002
- **User outcome:** A visitor immediately understands the marketplace, current plugin, supported platforms, and where to go next.
- **Scope:** Create the chosen Astro/Starlight site foundation from the DOC-001 stack and IA contract, landing page, nav/sidebar IA, and initial static pages for all 11 DOC-001 route labels: Start, Install: Claude Code, Install: Codex, First Run, Choose Your Path, Reference, Troubleshooting, Security & Trust, Contribute & Release, Spec Kit Lifecycle, and Glossary. Content can be skeletal where later SPECs own full detail.
- **Vertical-slice rationale:** Cuts through site setup, navigation, and first visible content shell as one usable docs-site increment.
- **Non-goals:** Full platform content, interactive widgets, docs CI hardening beyond basic build.
- **Source files likely affected:** `README.md`, `speckit-pro/README.md` for source extraction only if chosen; DOC-001 provides the stack and IA contract, while DOC-002 chooses concrete site config and docs content paths.
- **New files likely needed:** site config, docs content directory, landing page, sidebar/nav config, glossary seed.
- **Dependencies:** DOC-001 completed and archived; consume the Astro/Starlight recommendation and 11-route IA skeleton from `docs/ai/research/interactive-documentation-framework-spike.md`.
- **Acceptance criteria:** AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5.
- **Validation plan:** Site build; inspect navigation; check all top-level pages route; verify landing page platform choice and source/dist explanation.
- **Reviewability Budget:** Primary surface: docs/process | Projected reviewable LOC: 325 | Production files: 0 | Total files: about 5 | Budget result: within budget
- **Risks:** New site toolchain may expand too far; content skeleton can feel empty.
- **Open questions:** Should README become a short redirect to the site once the site exists?
- **Suggested implementation notes:** Keep pages thin and link back to canonical README sections until later SPECs fill details.

### DOC-003: Claude Code marketplace installation path

- **Maps from PRD:** DOC-FR-003
- **User outcome:** Claude Code users can add the marketplace, install/update/remove `speckit-pro`, verify the install, and understand namespaced plugin surfaces.
- **Scope:** Claude-specific tutorial/how-to/reference content: `/plugin marketplace add`, `/plugin install`, update/remove path, `/speckit-pro:*` invocation, `skills/`, `agents/`, `hooks/`, MCP/settings references, trust and managed-marketplace notes. Include current repo path evidence and legacy/current command-folder clarification.
- **Vertical-slice rationale:** Delivers one complete end-to-end install capability for one platform.
- **Non-goals:** Codex install instructions; full troubleshooting matrix; full command reference.
- **Source files likely affected:** `README.md`, `speckit-pro/README.md`, `.claude-plugin/marketplace.json`, `speckit-pro/.claude-plugin/plugin.json`, `dist/claude/speckit-pro/.claude-plugin/plugin.json`, `speckit-pro/agents/*`, `speckit-pro/hooks/hooks.json`.
- **New files likely needed:** Claude install docs page(s), Claude quick-check partial/component, source-evidence notes.
- **Dependencies:** DOC-002.
- **Acceptance criteria:** AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5.
- **Validation plan:** Verify commands against official docs and repo README; link check official and local references; manually review page for no Codex command leakage.
- **Reviewability Budget:** Primary surface: docs/process | Projected reviewable LOC: 285 | Production files: 0 | Total files: about 4 | Budget result: within budget
- **Risks:** Claude Code docs and marketplace behavior may change; AGENTS/README wording may remain inconsistent until a later docs-hygiene change.
- **Open questions:** Should docs update AGENTS/README command-folder wording in the same implementation PR or leave it as a flagged source note?
- **Suggested implementation notes:** Use tabs sparingly; prefer separate Claude and Codex pages with cross-links.

### DOC-004: Codex marketplace installation path

- **Maps from PRD:** DOC-FR-004
- **User outcome:** Codex users can install the plugin through repo/personal/CLI marketplace paths, run the install skill, restart, and verify custom agents.
- **Scope:** Codex-specific tutorial/how-to/reference content: `.agents/plugins/marketplace.json`, `.codex-plugin/plugin.json`, `codex plugin marketplace add`, repo-scoped vs personal install, installed cache behavior, generated Codex payload, `$install`, `@SpecKit Pro -> install`, custom-agent TOML registration, restart, sandbox/approvals/network constraints.
- **Vertical-slice rationale:** Delivers one complete end-to-end install capability for one platform.
- **Non-goals:** Claude Code instructions; changing Codex plugin manifests; live doctor command.
- **Source files likely affected:** `README.md`, `speckit-pro/README.md`, `.agents/plugins/marketplace.json`, `speckit-pro/.codex-plugin/plugin.json`, `dist/codex/speckit-pro/.codex-plugin/plugin.json`, `speckit-pro/codex-skills/install/SKILL.md`, `speckit-pro/codex-agents/*.toml`, `speckit-pro/codex-hooks.json`.
- **New files likely needed:** Codex install docs page(s), Codex quick-check partial/component, source-evidence notes.
- **Dependencies:** DOC-002.
- **Acceptance criteria:** AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6.
- **Validation plan:** Verify official Codex path semantics; compare repo README examples; link check; ensure all commands are scoped to Codex.
- **Reviewability Budget:** Primary surface: docs/process | Projected reviewable LOC: 340 | Production files: 0 | Total files: about 5 | Budget result: within budget
- **Risks:** Codex plugin marketplace docs are newer and may change; cache/path wording must be exact.
- **Open questions:** Confirm whether current personal marketplace path examples should be rewritten.
- **Suggested implementation notes:** Include a warning not to install the mixed authoring source tree directly.

### DOC-005: First successful `speckit-pro` workflow tutorial and lifecycle explainer

- **Maps from PRD:** DOC-FR-005
- **User outcome:** A user can complete one guided `speckit-pro` run and understand the artifacts produced.
- **Scope:** First-run tutorial with platform tabs or separate branches, Spec Kit prerequisite checks, lifecycle diagram, PRD/roadmap/scaffold/autopilot explanation, and first-success checkpoints for `$speckit-prd`, `$grill-me`, `$speckit-scaffold-spec`, and `$speckit-autopilot`.
- **Vertical-slice rationale:** Delivers a usable onboarding tutorial from prerequisite check through first workflow.
- **Non-goals:** Full command reference; live plugin execution in browser; all troubleshooting cases.
- **Source files likely affected:** `speckit-pro/README.md`, `speckit-pro/skills/speckit-prd/SKILL.md`, `speckit-pro/skills/grill-me/SKILL.md`, `speckit-pro/skills/speckit-scaffold-spec/SKILL.md`, `speckit-pro/skills/speckit-autopilot/SKILL.md`, Codex skill mirrors.
- **New files likely needed:** First-run tutorial page, lifecycle diagram/component, prerequisite checklist.
- **Dependencies:** DOC-003, DOC-004.
- **Acceptance criteria:** AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6.
- **Validation plan:** Link check; inspect all commands for platform labels; run safe static checks; optionally manual smoke-test commands outside CI.
- **Reviewability Budget:** Primary surface: docs/process | Projected reviewable LOC: 340 | Production files: 0 | Total files: about 5 | Budget result: within budget
- **Risks:** Tutorial may over-promise autonomous behavior; SpecKit CLI command examples may drift.
- **Open questions:** Which first workflow should be the canonical happy path: PRD/roadmap generation or scaffold/autopilot against an existing roadmap?
- **Suggested implementation notes:** Prefer a first PRD/roadmap run because it is less destructive than a full autopilot PR run.

### DOC-006: Safe interactive platform/path selector and validation aids

- **Maps from PRD:** DOC-FR-006
- **User outcome:** Users get the right platform commands and safe consistency checks without browser-side local execution.
- **Scope:** Implement safe interactive components or static equivalents: platform/path selector, install-scope selector, copyable command blocks, manifest/version checker from checked-in JSON, generated payload diagram, first-run checklist, and troubleshooting decision-tree scaffold.
- **Vertical-slice rationale:** Delivers end-to-end interaction through docs UI and static fallback without touching plugin runtime.
- **Non-goals:** Live local doctor command; auto-editing user config; analytics instrumentation.
- **Source files likely affected:** Site component directory, docs pages from DOC-002/003/004/005, `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, source/dist plugin manifests.
- **New files likely needed:** Selector/checker components, command metadata file, payload diagram, interactive fallback tables.
- **Dependencies:** DOC-002, DOC-003, DOC-004.
- **Acceptance criteria:** AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6.
- **Validation plan:** Site build; keyboard smoke test; no network/local command execution; fixture test for metadata-to-command rendering; static fallback review.
- **Reviewability Budget:** Primary surface: docs/process | Projected reviewable LOC: 380 | Production files: 0 | Total files: about 6 | Budget result: within budget
- **Risks:** Component logic can become app-like; keep data small and static.
- **Open questions:** Should command metadata be generated from source files or hand-authored in docs?
- **Suggested implementation notes:** Use checked-in JSON snippets and deterministic rendering; avoid shelling out from the site.

### DOC-007: Command, workflow, manifest, and file-layout reference

- **Maps from PRD:** DOC-FR-007
- **User outcome:** Users, maintainers, and agents can look up exact plugin surfaces and file responsibilities by stable deep link.
- **Scope:** Reference pages for Claude commands/skills, Codex skills, agents/subagents, hooks, MCP/config surfaces, manifests, marketplace files, generated payloads, scripts, tests, CI, release files, and repo structure. Include source facts and inferred notes separately.
- **Vertical-slice rationale:** Delivers one coherent reference library that other pages can deep-link.
- **Non-goals:** Installation tutorials; troubleshooting prose; release process walkthrough.
- **Source files likely affected:** `README.md`, `speckit-pro/README.md`, manifests, `speckit-pro/skills/**/SKILL.md`, `speckit-pro/codex-skills/**/SKILL.md`, `speckit-pro/agents/*`, `speckit-pro/codex-agents/*`, `scripts/*`, `tests/speckit-pro/**`.
- **New files likely needed:** Reference pages and optional generated/static metadata table.
- **Dependencies:** DOC-003, DOC-004.
- **Acceptance criteria:** AC-7.1, AC-7.2, AC-7.3, AC-7.4, AC-7.5, AC-7.6.
- **Validation plan:** Link check; compare manifest/version/source file references; ensure every referenced local file exists; no orphan reference pages.
- **Reviewability Budget:** Primary surface: docs/process | Projected reviewable LOC: 380 | Production files: 0 | Total files: about 6 | Budget result: within budget
- **Risks:** Reference tables can drift; future generation may be needed.
- **Open questions:** Should the command/skill matrix be generated from `SKILL.md` frontmatter in a later SPEC?
- **Suggested implementation notes:** Start hand-authored with source paths and add generation only if drift becomes measurable.

### DOC-008: Troubleshooting, security, trust, update, and rollback model

- **Maps from PRD:** DOC-FR-008
- **User outcome:** Users and evaluators can diagnose failures and decide whether to trust/install/update the plugin.
- **Scope:** Troubleshooting matrix and trust model for Claude and Codex: marketplace source trust, generated payloads, installed cache, hooks/MCP/agents/custom agents, permissions/approvals/sandbox, update/remove/rollback, stale versions, missing Spec Kit CLI, missing custom agents, path errors, and managed restrictions.
- **Vertical-slice rationale:** Delivers one complete safety/diagnostics capability across both platforms.
- **Non-goals:** Live diagnostics command; security audit of plugin code; changing hooks or permissions.
- **Source files likely affected:** `README.md`, `speckit-pro/README.md`, `speckit-pro/codex-hooks.json`, `speckit-pro/hooks/hooks.json`, manifests, install skills, official-source citations.
- **New files likely needed:** Troubleshooting pages, Security & Trust explanation page, update/rollback page.
- **Dependencies:** DOC-003, DOC-004, DOC-007.
- **Acceptance criteria:** AC-8.1, AC-8.2, AC-8.3, AC-8.4, AC-8.5, AC-8.6.
- **Validation plan:** Manual review against official docs; link check; table coverage for known symptoms; no unsupported claims about sandbox bypasses or automatic trust.
- **Reviewability Budget:** Primary surface: docs/process | Projected reviewable LOC: 380 | Production files: 0 | Total files: about 6 | Budget result: within budget
- **Risks:** Security docs can sound like guarantees; keep statements constrained to source facts.
- **Open questions:** Should the docs recommend a minimum Claude Code/Codex version for plugin features?
- **Suggested implementation notes:** Separate "source fact", "repository behavior", and "recommended practice" callouts.

### DOC-009: Maintainer and contributor release workflow

- **Maps from PRD:** DOC-FR-009
- **User outcome:** Contributors can make docs/plugin changes and know the exact build/test/sync/release checks required.
- **Scope:** Contributor workflow for changing plugin source, rebuilding payloads, syncing marketplace versions, validating source/dist/marketplace parity, running shell tests, docs-only PR behavior, release-please expectations, Conventional Commit titles, and public-readable PR bodies.
- **Vertical-slice rationale:** Delivers one maintainer workflow from edit to release readiness.
- **Non-goals:** Changing CI workflows unless needed for docs validation in DOC-010; changing release automation behavior.
- **Source files likely affected:** `AGENTS.md`, `CLAUDE.md`, `README.md`, `.github/workflows/pr-checks.yml`, `.github/workflows/release.yml`, `scripts/build-plugin-payloads.sh`, `scripts/sync-marketplace-versions.sh`, tests.
- **New files likely needed:** Contributor/release docs page, release-readiness checklist.
- **Dependencies:** DOC-007.
- **Acceptance criteria:** AC-9.1, AC-9.2, AC-9.3, AC-9.4, AC-9.5, AC-9.6.
- **Validation plan:** Verify listed commands exist; run docs link checks; optionally run `bash tests/speckit-pro/run-all.sh --layer 1` after docs references are updated.
- **Reviewability Budget:** Primary surface: docs/process | Projected reviewable LOC: 380 | Production files: 0 | Total files: about 6 | Budget result: within budget
- **Risks:** Contributor docs can become a second CLAUDE.md; avoid duplicating full CI internals.
- **Open questions:** Should docs-only PRs trigger new docs-site CI before plugin tests?
- **Suggested implementation notes:** Link to existing CLAUDE/AGENTS guidance; keep the user-facing page action-oriented.

### DOC-010: Search, accessibility, deep links, responsive UX, and docs validation

- **Maps from PRD:** DOC-FR-010
- **User outcome:** The docs site is findable, accessible, linkable, responsive, and protected by CI.
- **Scope:** Search integration or documented local-search plan, glossary/deep-link conventions, responsive checks, accessibility requirements and tests for interactive components, markdown/link validation, site build in CI, manifest/payload consistency validation integration, safe command-snippet validation, and visual/screenshot regression plan if supported.
- **Vertical-slice rationale:** Hardens the full docs product after core content and interactions exist.
- **Non-goals:** Full analytics implementation; broad plugin test rewrite; live install tests in CI.
- **Source files likely affected:** Site config, CI workflow, docs validation scripts/config, interactive components, glossary/reference pages, existing validation scripts.
- **New files likely needed:** Docs CI config, link-check config, accessibility test config, visual regression baseline only if chosen stack supports it.
- **Dependencies:** DOC-001, DOC-002, DOC-006.
- **Acceptance criteria:** AC-10.1, AC-10.2, AC-10.3, AC-10.4, AC-10.5, AC-10.6, AC-10.7.
- **Validation plan:** Site build; markdown lint; link check; accessibility smoke check; responsive screenshots if feasible; verify existing plugin validation still passes or is unaffected.
- **Reviewability Budget:** Primary surface: docs/process | Projected reviewable LOC: 395 | Production files: 0 | Total files: about 6 | Budget result: within budget
- **Risks:** CI can become slow or flaky; link checks against official docs may need allowlists.
- **Open questions:** Which link checker and accessibility tooling should the selected framework use?
- **Suggested implementation notes:** Start with deterministic checks and make external link checks advisory if they prove flaky.

## 5. Sequencing

1. DOC-001: resolves framework/tooling before files proliferate.
2. DOC-002: creates the site shell and IA that all content plugs into.
3. DOC-003 and DOC-004: build platform-specific install paths in parallel.
4. DOC-005: connects install to first successful `speckit-pro` run.
5. DOC-006: adds safe interactive aids once platform content exists.
6. DOC-007: builds the reference library needed by troubleshooting and maintainer docs.
7. DOC-008: adds diagnostics and trust model.
8. DOC-009: adds maintainer/contributor release workflow.
9. DOC-010: hardens search, accessibility, responsive behavior, deep links, and docs CI.

## 6. Validation Strategy

- Markdown linting for all docs content.
- Link checking for local links and official-source links, with an allowlist/retry policy for external flakiness.
- Static site build in CI after DOC-002.
- Command snippet review and safe validation only; no browser-triggered local shell execution.
- Marketplace JSON validity and source-path checks using existing repo validation where possible.
- Plugin manifest consistency checks across source, `dist/claude`, `dist/codex`, and both marketplace files.
- Generated payload consistency checks with `bash scripts/build-plugin-payloads.sh` when source/plugin docs change.
- Existing shell suite: `bash tests/speckit-pro/run-all.sh` for plugin-impacting changes; layer-specific runs for narrow edits.
- Accessibility checks for keyboard focus, labels, contrast, static fallback, and no JS-required critical path.
- Responsive viewport checks after static site exists.
- Manual smoke test for Claude Code install path.
- Manual smoke test for Codex install path.

## 7. Cut List

- Full analytics instrumentation: deferred until hosting/framework is chosen.
- Live browser-based plugin execution: excluded for safety and environment variance.
- Auto-modifying Claude/Codex config from docs: excluded; docs provide commands and checks only.
- Full marketing site beyond the docs landing page: deferred until install-to-first-run is reliable.
- New local doctor command: deferred; v1 uses safe selectors/checkers and existing validation scripts.
- Unconfirmed official behavior: recorded as validation tasks or open questions, not requirements.

## 8. References

- Source PRD: [docs/prd-interactive-documentation.md](prd-interactive-documentation.md)
- Traceability matrix: [docs/traceability-interactive-documentation.md](traceability-interactive-documentation.md)
- SpecKit-compatible roadmap: [docs/ai/specs/interactive-documentation-technical-roadmap.md](ai/specs/interactive-documentation-technical-roadmap.md)
- Roadmap-MOC home note: [docs/ai/specs/interactive-documentation-roadmap-MOC.md](ai/specs/interactive-documentation-roadmap-MOC.md)
