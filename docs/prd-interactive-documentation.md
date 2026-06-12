# PRD: Racecraft Interactive Documentation

**Date:** 2026-06-12  
**Owner:** Racecraft maintainers  
**Status:** Ready for SPEC decomposition  
**Target repository:** https://github.com/racecraft-lab/racecraft-plugins-public  
**Target surfaces:** Claude Code marketplace, Codex marketplace, `speckit-pro` plugin docs, static documentation site

---

## 1. Executive Summary

Racecraft's public plugin marketplace and `speckit-pro` have enough working machinery to be useful, but the documentation asks users to decode platform differences, install scopes, generated payloads, trust boundaries, and Spec Kit lifecycle details from a small number of dense Markdown files. The intended experience is a static docs site with safe interactive aids that routes a user to the correct Claude Code or Codex path, helps them complete a first successful `speckit-pro` run, and gives maintainers verifiable release/update workflows. The measurable outcome is higher install-to-first-run completion, fewer marketplace/path/version support issues, and a docs CI surface that catches drift before release.

## 2. Evidence and Source Map

| Source | What it says | Product implication | Confidence | Bias / limitation |
|---|---|---|---|---|
| [OpenAI Codex build plugins](https://developers.openai.com/codex/plugins/build) | Codex plugins require `.codex-plugin/plugin.json`; repo marketplaces live at `$REPO_ROOT/.agents/plugins/marketplace.json`; installed plugins load from the Codex cache; plugin paths should be relative to plugin root. | Codex install docs must distinguish marketplace source, generated payload, cache location, and plugin authoring tree. | High | Official vendor docs; authoritative for intended behavior, may omit edge cases. |
| [OpenAI Codex skills](https://developers.openai.com/codex/skills) | Skills are reusable workflow packages with `SKILL.md`, optional scripts/references/assets, progressive disclosure, and explicit `$skill` invocation. | `speckit-pro` Codex docs must explain skills separately from Claude slash-command names and from custom agents. | High | Official vendor docs; biased toward recommended workflows. |
| [OpenAI Codex subagents](https://developers.openai.com/codex/subagents) | Custom agents are standalone TOML files under `.codex/agents/` or `~/.codex/agents/`; subagents inherit sandbox and approval policy. | Codex docs must explain why the `install` skill copies `codex-agents/*.toml` and why restart/approval behavior matters. | High | Official vendor docs; current behavior may evolve. |
| [OpenAI Codex approvals and security](https://developers.openai.com/codex/agent-approvals-security) | Codex defaults to no network access; local sandboxing limits writes; approvals are required for network/out-of-workspace/destructive actions. | Security docs need a plain trust/approval model and must avoid promising silent autonomous access. | High | Official vendor docs; exact UI labels can change. |
| [Claude Code create plugins](https://code.claude.com/docs/en/plugins) | Claude Code plugins package skills, agents, hooks, MCP, etc.; plugin skills are namespaced, e.g. `/plugin-name:skill`; `skills/` is preferred for new plugins while `commands/` is still a supported root-level directory. | Claude docs must use `/speckit-pro:*` names, explain namespacing, and clarify why this repo is skill-first even if older instructions mention commands. | High | Official vendor docs; current as published. |
| [Claude Code marketplace docs](https://code.claude.com/docs/en/plugin-marketplaces) | Claude marketplace entries can use `./` relative paths resolved from the marketplace root; Git/GitHub/npm/subdir sources can be pinned. | Marketplace docs need exact path-resolution language for this repo's `./dist/claude/speckit-pro` entry. | High | Official vendor docs; distribution modes vary. |
| [Claude Code settings](https://code.claude.com/docs/en/settings) | Managed settings can restrict marketplaces and plugin-only customization (`strictKnownMarketplaces`, `strictPluginOnlyCustomization`). | Team/evaluator docs need a managed-marketplace section, not just consumer install commands. | High | Official vendor docs; applies mainly to managed environments. |
| [GitHub Spec Kit](https://github.com/github/spec-kit) | Spec-Driven Development emphasizes specifying the "what" before the "how"; the flow establishes constitution, specify, plan, tasks, and implement artifacts; `specify init` supports Codex integration options. | First-run docs must teach the lifecycle and should validate Claude vs Codex initialization commands separately. | High | Official project README; behavior may track CLI releases. |
| [Diataxis](https://diataxis.fr/) | Documentation should be organized around four user needs: tutorials, how-to guides, reference, and explanation. | The docs IA should be task/user-need oriented rather than mirroring repo folders. | High | Authoritative framework; not a tool mandate. |
| [Docusaurus docs](https://docusaurus.io/docs/docs-introduction) and [MDX/React support](https://docusaurus.io/docs/markdown-features/react) | Docusaurus organizes docs via pages, sidebars, versions, and plugin instances; MDX supports React components in Markdown. | Docusaurus/MDX is a strong candidate for the static site, but the user chose a framework spike before commitment. | Medium | Framework docs; authoritative for Docusaurus, not proof it is the best choice. |
| [W3C WAI accessibility principles](https://www.w3.org/WAI/fundamentals/accessibility-principles/) | Accessible web content should be perceivable, operable, understandable, and robust; dynamic UI needs text alternatives, keyboard support, and predictable behavior. | Interactive docs must be keyboard accessible, copyable without JavaScript, and screen-reader understandable. | High | Standards source; implementation details remain project-specific. |
| `README.md` | The repo documents source vs `dist/claude` vs `dist/codex`, both marketplace files, Claude install commands, Codex repo/personal install notes, and cautions against installing the mixed source tree directly. | The site should promote the generated payload distinction as a first-class concept. | High | Repository evidence; may drift from official docs. |
| `speckit-pro/README.md` | The plugin README explains the SDD flow, command matrix, install paths, prerequisites, troubleshooting, Codex agent install step, and architecture notes. | This should be decomposed into discoverable tutorials/reference pages rather than kept as one dense entry point. | High | Repository evidence; long page may hide critical tasks. |
| `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, source/dist manifests | All checked version fields currently agree at `2.12.0`. | Version consistency is a validated strength and should become a visible validation concept, not a silent assumption. | High | Snapshot from this worktree on 2026-06-12. |
| `scripts/build-plugin-payloads.sh` | The build script emits isolated Claude and Codex install roots because the authoring tree mixes platform variants. | Docs must explain source tree vs generated payloads and require validation after source changes. | High | Repository script behavior; not user-facing unless surfaced. |
| `tests/speckit-pro/layer1-structural/*` and `tests/speckit-pro/layer4-scripts/*` | The repo already has structural and script validation for manifests, payloads, marketplace files, Codex parity, hooks, and scripts. | Docs validation should reuse and surface existing tests before adding new site checks. | High | Repository evidence; test coverage may not include future docs site yet. |
| `AGENTS.md` vs repository tree | `AGENTS.md` says `commands/` contains slash-command docs, but `speckit-pro/commands` is absent in this checkout and the README says Codex ships skills only. | The docs must explicitly describe current skill-first packaging and flag command-folder references as legacy or platform-dependent. | Medium | Local evidence plus inference; needs maintainer confirmation before changing repo guidance. |

## 3. Problem Statement

Users can install and use `speckit-pro`, but the current documentation makes them resolve several high-risk distinctions themselves:

- Claude Code and Codex setup paths look similar but use different marketplace files, invocation syntax, custom-agent registration, and approval models.
- Marketplace setup, plugin install, generated payload install, and source-tree development are easy to conflate.
- The full `speckit-pro` lifecycle is explained, but not as a guided install-to-first-success tutorial with validation checkpoints.
- Trust boundaries are scattered across install warnings, Codex approval behavior, Claude permission/settings behavior, hooks, generated payloads, MCP/agent notes, and update/rollback paths.
- Contributors must know which marketplace, manifest, payload, tests, and release files stay in sync, but the docs do not turn that into a dedicated release-readiness workflow.
- There is no static docs-site toolchain yet, so interactive docs require a bounded framework/tooling decision before implementation.

## 4. Target Users and Jobs-to-be-Done

| User segment | Job | Trigger | Success signal | Current friction |
|---|---|---|---|---|
| First-time user | Understand Racecraft plugins, install `speckit-pro`, and complete one guided workflow. | Finds the repo or marketplace link. | Installs correctly and runs the first `speckit-pro` flow without asking which platform path applies. | Dense README, platform differences require manual comparison. |
| Existing Claude Code user | Add the Claude marketplace and use namespaced plugin skills safely. | Wants `/speckit-pro:*` workflows. | Marketplace added, plugin installed/updated, first command succeeds, trust implications understood. | Commands, skills, agents, hooks, scopes, and managed settings are not separated into task pages. |
| Existing Codex user | Add or use the Codex marketplace, install the plugin, install custom agents, and restart correctly. | Wants `$speckit-*` skills or Codex app plugin use. | Plugin appears, `install` skill copies custom agents, restart loads agents, first workflow succeeds. | Cache, repo/personal scope, `.agents/plugins`, `.codex-plugin`, and `.codex/agents` are easy to mix up. |
| Maintainer/contributor | Update plugin source, rebuild payloads, keep both marketplaces consistent, and run tests. | Opens a docs/plugin/release PR. | Release-readiness checklist passes and the changed files are predictable. | Validation exists but is not expressed as a public contributor workflow. |
| Security/platform evaluator | Decide whether this marketplace/plugin is acceptable for their machine or team. | Reviewing plugin before install or managed rollout. | Understands install sources, generated payloads, hooks/MCP/agent behavior, approvals, updates, rollback, and managed restrictions. | Trust model exists only as scattered warnings and platform docs. |

## 5. Scope

### In scope

- A static documentation site for Racecraft Public Plugins and `speckit-pro`.
- A framework/tooling spike before selecting the static-site stack.
- User-need IA using Diataxis categories.
- Separate Claude Code and Codex install/update/remove paths.
- First successful `speckit-pro` guided workflow tutorial.
- Safe interactive aids: platform/path selector, copyable commands, manifest/version checker, generated payload diagram, troubleshooting decision tree, release-readiness checklist, Spec Kit lifecycle visualizer.
- Reference pages for marketplaces, manifests, skills, agents/subagents, hooks, generated payloads, tests, and release scripts.
- Accessibility, search, deep links, responsive UX, and docs validation requirements.
- Contributor/release workflow for keeping source, `dist/**`, marketplaces, versions, tests, and release automation in sync.

### Out of scope

- Implementing the docs site in this PRD task.
- Auto-modifying a user's Claude/Codex configuration from the browser.
- Executing `speckit-pro` or marketplace installs inside the browser.
- Full analytics instrumentation before a hosting/tooling decision exists.
- Changing plugin behavior, manifests, marketplace files, generated payloads, or release automation.
- Rewriting all existing README content before the site IA and framework are selected.

### Explicit non-goals

- No generic marketing microsite detached from task success.
- No one-size-fits-all install page that hides Claude/Codex differences.
- No undocumented assumptions about current official marketplace behavior.
- No speculative docs framework commitment before the framework spike.

## 6. Product Requirements

### DOC-FR-001: Static docs framework and IA spike

- **User need:** Maintainers need a low-risk framework decision before committing the repo to a docs-site toolchain.
- **Required behavior:** Produce a timeboxed comparison of Docusaurus/MDX, VitePress, Astro/Starlight, and a repo-native fallback against Racecraft's needs: static hosting, MDX or equivalent interactive components, search, versioning, docs-as-code, link checking, accessibility testing, low maintenance, and GitHub Pages or similar deploy path.
- **Acceptance criteria:**
  - **AC-1.1:** The spike records the recommended site stack, rejected alternatives, and exact reason each was accepted or rejected.
  - **AC-1.2:** The spike includes a proposed IA skeleton organized by user tasks and Diataxis mode.
  - **AC-1.3:** The spike identifies the minimum package manager/build/test commands needed for the chosen stack.
  - **AC-1.4:** The spike does not modify product/plugin behavior.
- **Priority:** Must
- **Source rationale:** User selected "static site now" and "framework spike first"; repo has no existing docs-site toolchain.

### DOC-FR-002: Unified landing page and IA shell

- **User need:** Users need to immediately understand what Racecraft Public Plugins and `speckit-pro` are, then choose the correct next path.
- **Required behavior:** Provide a docs-site landing page, top navigation, glossary entry points, and clear routing to Claude Code, Codex, first-run, security, and maintainer workflows.
- **Acceptance criteria:**
  - **AC-2.1:** The landing page states the marketplace purpose, current plugin, primary value, and supported platforms in one screen.
  - **AC-2.2:** The IA exposes Tutorials, How-to, Reference, and Explanation sections.
  - **AC-2.3:** Claude Code and Codex paths are selectable from the first interaction.
  - **AC-2.4:** The docs distinguish authoring source (`speckit-pro/`) from generated install payloads (`dist/claude/**`, `dist/codex/**`).
  - **AC-2.5:** Every top-level nav label has a stated purpose and success criterion.
- **Priority:** Must
- **Source rationale:** Current README explains the concepts but does not provide task-first navigation.

### DOC-FR-003: Claude Code marketplace installation path

- **User need:** Claude Code users need exact add/install/update/remove instructions and plugin-surface expectations.
- **Required behavior:** Provide a Claude-specific tutorial and how-to pages for adding the Racecraft marketplace, installing/updating/removing `speckit-pro`, invoking namespaced skills, understanding agents/hooks/MCP/settings, and validating install success.
- **Acceptance criteria:**
  - **AC-3.1:** The Claude install path uses `/plugin marketplace add racecraft-lab/racecraft-plugins-public` and `/plugin install speckit-pro@racecraft-plugins-public`.
  - **AC-3.2:** The docs explain namespaced invocation such as `/speckit-pro:speckit-prd` and current skill-first packaging.
  - **AC-3.3:** The docs explain trust boundaries for plugin sources, hooks, agents, MCP, settings, and managed marketplace restrictions.
  - **AC-3.4:** The docs include update/remove/troubleshooting checkpoints without mixing Codex commands into the Claude path.
  - **AC-3.5:** The docs flag any legacy `commands/` references as platform/era-specific if the current repo lacks that directory.
- **Priority:** Must
- **Source rationale:** Claude Code docs and current repo README both use marketplace and namespaced plugin concepts.

### DOC-FR-004: Codex marketplace installation path

- **User need:** Codex users need exact repo-scoped and personal install paths, including custom-agent registration.
- **Required behavior:** Provide Codex-specific install/update/remove pages covering `.agents/plugins/marketplace.json`, `.codex-plugin/plugin.json`, generated Codex payloads, cache behavior, `@SpecKit Pro -> install` / `$install`, `.codex/agents` vs `~/.codex/agents`, restart requirements, sandbox/approvals, and verification.
- **Acceptance criteria:**
  - **AC-4.1:** The Codex path explains repo marketplace, personal marketplace, and `codex plugin marketplace add` options using official terminology.
  - **AC-4.2:** The docs state that Codex loads installed plugins from cache and that users should update the payload directory/marketplace source before expecting changes.
  - **AC-4.3:** The docs explain why `speckit-pro` has a Codex-only `install` skill for custom-agent TOML templates.
  - **AC-4.4:** The docs separate Codex skill metadata sidecars from custom-agent registration.
  - **AC-4.5:** The docs include sandbox, approval, and network-access implications for `speckit-pro` workflows.
  - **AC-4.6:** The docs call out a validation task to confirm the current README personal-marketplace path wording against official Codex path-resolution behavior.
- **Priority:** Must
- **Source rationale:** Codex plugin/skills/subagent/security docs plus repo README and plugin README.

### DOC-FR-005: First successful `speckit-pro` workflow tutorial and lifecycle explainer

- **User need:** Users need one guided path from install to a successful SDD outcome.
- **Required behavior:** Provide tutorials for first PRD/roadmap run, first scaffolded spec, and first autopilot run, with platform-specific commands and visible checkpoints for Spec Kit prerequisites.
- **Acceptance criteria:**
  - **AC-5.1:** The tutorial shows the lifecycle from idea to PRD to technical roadmap to scaffolded spec to autopilot run.
  - **AC-5.2:** The docs explain specify, clarify, plan, checklist, tasks, analyze, and implement in user-facing language.
  - **AC-5.3:** The docs distinguish raw `grill-me`, `$speckit-prd`, `$speckit-scaffold-spec`, and `$speckit-autopilot` roles.
  - **AC-5.4:** The tutorial includes prerequisite checks for Spec Kit CLI, constitution, GitHub CLI, and `jq`.
  - **AC-5.5:** The docs validate whether Codex first-run should use `specify init --integration codex --integration-options="--skills"` rather than copying Claude initialization wording.
  - **AC-5.6:** The lifecycle visualizer has a static fallback diagram and does not require executing plugins.
- **Priority:** Must
- **Source rationale:** Spec Kit official flow and `speckit-pro/README.md` lifecycle.

### DOC-FR-006: Safe interactive platform/path selector and validation aids

- **User need:** Users need help picking the correct commands and checking copied snippets without unsafe browser execution.
- **Required behavior:** Provide safe interactive components: platform selector, install-scope selector, copyable command blocks, manifest/version consistency checker, generated payload diagram, troubleshooting decision tree, and first-run checklist.
- **Acceptance criteria:**
  - **AC-6.1:** The platform/path selector outputs only documentation guidance and copyable commands; it does not edit user config.
  - **AC-6.2:** Command blocks include platform labels, prerequisites, expected success signals, and fallback if JavaScript is unavailable.
  - **AC-6.3:** The manifest/version checker can compare displayed repo metadata from checked-in JSON examples and explain what must stay in sync.
  - **AC-6.4:** The payload diagram shows source tree, Claude dist, Codex dist, marketplace entries, and Codex cache as distinct nodes.
  - **AC-6.5:** All interactive components remain usable by keyboard and degrade to static Markdown tables.
  - **AC-6.6:** The first-run checklist includes checkpoints but never runs shell commands from the browser.
- **Priority:** Must
- **Source rationale:** User selected safe selectors/checkers; W3C accessibility principles constrain interaction design.

### DOC-FR-007: Command, workflow, manifest, and file-layout reference

- **User need:** Users and agents need precise reference material without re-reading long README sections.
- **Required behavior:** Provide reference pages for commands/skills, Claude agents, Codex custom agents, hooks, MCP/config surfaces, manifest schemas, marketplace files, generated payloads, scripts, tests, and repo file layout.
- **Acceptance criteria:**
  - **AC-7.1:** The command/skill matrix shows Claude invocation, Codex invocation, purpose, prerequisites, and expected output artifact.
  - **AC-7.2:** Manifest references list required and optional fields for Claude and Codex separately.
  - **AC-7.3:** The file-layout reference identifies source-only, dist-only, test-only, and generated files.
  - **AC-7.4:** The docs explain which files are authoritative for version and marketplace sync.
  - **AC-7.5:** The reference cites official docs for platform behavior and repo files for current implementation.
  - **AC-7.6:** Every reference page has deep links suitable for support replies and autopilot context.
- **Priority:** Should
- **Source rationale:** Prompt requires discoverability of commands, skills, agents, hooks, manifests, payloads, and permissions.

### DOC-FR-008: Troubleshooting, security, trust, update, and rollback model

- **User need:** Users need to diagnose failed installs and assess plugin trust before granting access.
- **Required behavior:** Provide troubleshooting and security docs covering common install/path/cache/version/permission failures, update/rollback, marketplace trust boundaries, hooks/MCP/agent behavior, approvals, and managed-policy controls.
- **Acceptance criteria:**
  - **AC-8.1:** Troubleshooting entries include symptom, likely cause, diagnostic command or file to inspect, and recommended fix.
  - **AC-8.2:** Security docs explain what a plugin can package on Claude and Codex: skills, agents/subagents, hooks, MCP config, settings/assets where applicable.
  - **AC-8.3:** The trust model distinguishes repository source, generated payloads, installed cache, user/project agents, and managed-policy controls.
  - **AC-8.4:** Update/rollback docs cover marketplace refresh, payload rebuild, version sync, and stale install/cache cases.
  - **AC-8.5:** The docs explicitly state that browser docs do not grant permissions or run local plugin workflows.
  - **AC-8.6:** Security/evaluator pages cite official vendor docs and label repository-derived behavior separately.
- **Priority:** Must
- **Source rationale:** Current README warns to trust plugins; official Codex and Claude docs emphasize sandbox/approval/managed controls.

### DOC-FR-009: Maintainer and contributor release workflow

- **User need:** Maintainers need a reproducible path for changing plugins and keeping generated artifacts consistent.
- **Required behavior:** Provide contributor docs for source edits, payload rebuilds, both marketplace files, version sync, tests, release-please, PR title/body expectations, and release readiness.
- **Acceptance criteria:**
  - **AC-9.1:** The workflow lists required checks for docs-only, plugin source, dist payload, marketplace, and release automation changes.
  - **AC-9.2:** The docs explain `bash scripts/build-plugin-payloads.sh`, `bash scripts/sync-marketplace-versions.sh`, and `bash tests/speckit-pro/run-all.sh`.
  - **AC-9.3:** The docs state which changes should or should not manually edit version fields.
  - **AC-9.4:** The release checklist covers source/dist parity, Claude/Codex marketplace parity, manifest version consistency, and generated payload validation.
  - **AC-9.5:** Contributor docs include Conventional Commit and public-readable PR title/body expectations.
  - **AC-9.6:** The workflow explains docs-only CI behavior and adds a future docs-site CI requirement once the site exists.
- **Priority:** Must
- **Source rationale:** Repo scripts, CI workflows, release process, and constitution already encode these rules.

### DOC-FR-010: Search, accessibility, deep links, responsive UX, and docs validation

- **User need:** The docs site must be findable, accessible, stable for support links, and protected against drift.
- **Required behavior:** Provide search/navigation/glossary requirements, responsive layout, keyboard/screen-reader accessible interactive components, stable deep links, markdown/link validation, command snippet validation where safe, manifest consistency checks, site build checks, and accessibility checks.
- **Acceptance criteria:**
  - **AC-10.1:** The site includes search or a documented search plan, a glossary, and stable URL/deep-link conventions.
  - **AC-10.2:** Interactive controls meet keyboard, focus, label, contrast, and static-fallback requirements.
  - **AC-10.3:** Docs CI runs site build, markdown lint, link check, marketplace/manifest validation, payload consistency checks, and safe command-snippet checks.
  - **AC-10.4:** The validation strategy avoids networked or destructive commands unless explicitly marked manual.
  - **AC-10.5:** The site has responsive layouts for mobile and desktop install workflows.
  - **AC-10.6:** Docs pages include source-update guidance so official doc changes become maintenance tasks rather than stale assertions.
  - **AC-10.7:** Visual regression or screenshot checks are required once the static site exists.
- **Priority:** Should
- **Source rationale:** Prompt requires testable docs, search/navigation, accessibility, deep links, responsive UX, and validation.

## 7. Candidate Requirement Evaluation

The prompt's 15 candidate groups are all represented, but several are merged to keep the SPEC catalog reviewable:

| Prompt candidate | Decision | Lands in |
|---|---|---|
| Unified landing page and value proposition | Keep | DOC-FR-002 |
| Claude Code marketplace installation path | Keep | DOC-FR-003 |
| Codex marketplace installation path | Keep | DOC-FR-004 |
| `speckit-pro` first-run tutorial | Keep | DOC-FR-005 |
| Interactive platform/path selector | Keep | DOC-FR-006 |
| Command and workflow reference | Merge | DOC-FR-007 |
| Manifest and marketplace reference | Merge | DOC-FR-007 |
| Troubleshooting and diagnostics | Merge | DOC-FR-008 |
| Security, permissions, trust, update model | Merge | DOC-FR-008 |
| Maintainer/contributor release workflow | Merge | DOC-FR-009 |
| Version consistency/generated payload validation | Merge | DOC-FR-009 and DOC-FR-010 |
| Search, navigation, glossary, IA | Split | DOC-FR-002 and DOC-FR-010 |
| Accessibility, copyability, deep links, responsive UX | Keep | DOC-FR-010 |
| Docs validation in CI | Keep | DOC-FR-010 |
| Visual/interactive Spec Kit lifecycle explainers | Merge | DOC-FR-005 and DOC-FR-006 |

No candidate is cut entirely. The main leanness choice is merging related references and safety/diagnostics so the roadmap stays at 10 vertical SPECs.

## 8. Information Architecture

| Nav label | Diataxis mode | Page purpose | Primary user | Success criterion |
|---|---|---|---|---|
| Start | Tutorial | Explain Racecraft Public Plugins, platform choice, and first next step. | First-time user | User chooses Claude Code or Codex path within one screen. |
| Install: Claude Code | Tutorial / how-to | Add marketplace, install/update/remove plugin, verify namespaced commands. | Claude Code user | User reaches a working `/speckit-pro:*` command. |
| Install: Codex | Tutorial / how-to | Add/select marketplace, install plugin, run install skill, restart, verify custom agents. | Codex user | User reaches a working `$speckit-*` flow with agents loaded. |
| First Run | Tutorial | Complete one PRD/roadmap or scaffold/autopilot workflow with checkpoints. | New plugin user | User produces or runs the expected first artifact. |
| Choose Your Path | Interactive how-to | Platform/scope selector, copyable commands, first-run checklist. | New and returning users | User gets only commands relevant to their selected platform/scope. |
| Reference | Reference | Commands/skills, manifests, marketplace files, hooks, agents, payloads, tests, file layout. | Users, agents, maintainers | Each surface has a stable deep link and source citation. |
| Troubleshooting | How-to | Symptom-driven diagnostics for install/path/cache/permission/version issues. | Users/support | User can identify cause and next command/file to inspect. |
| Security & Trust | Explanation | Marketplace trust, sandbox/approval, hooks/MCP/agents, managed controls, update/rollback. | Security/platform evaluator | Evaluator can approve, reject, or ask a concrete follow-up. |
| Contribute & Release | How-to / reference | Source edits, payload rebuilds, marketplace sync, tests, release-please, PR conventions. | Maintainer/contributor | Maintainer can complete a release-readiness checklist. |
| Spec Kit Lifecycle | Explanation | Visual/static explanation of PRD -> roadmap -> scaffold -> autopilot phases. | User/evaluator | User can explain what each phase produces and validates. |
| Glossary | Reference | Terms like marketplace, payload, source tree, skill, agent, hook, cache, constitution. | All | Support answers can link to exact definitions. |

## 9. Interactive Documentation Concepts

| Concept | User problem | Interaction | Data/source required | Fallback | Acceptance criteria | Priority |
|---|---|---|---|---|---|---|
| Platform/path selector | Users mix Claude and Codex commands. | Choose platform, install scope, and goal; receive command sequence and checks. | Official docs + repo marketplace paths. | Static matrix with all paths. | Outputs only relevant commands; no config writes. | Must |
| Copyable command blocks | Users mistype commands and cannot tell expected output. | Copy button, platform badge, prerequisite notes, expected success signal. | Curated command metadata. | Plain fenced code blocks. | Every command block has platform/scope label. | Must |
| Manifest/version checker | Users and maintainers miss version drift. | Display checked-in JSON values and compare expected version equality. | Marketplace and manifest JSON files. | Static checklist with file paths. | Flags mismatch as docs/release task; no writes. | Must |
| Generated payload diagram | Users install source tree instead of generated payload. | Visual diagram of source -> dist -> marketplace -> install/cache. | Repo tree, build script, marketplace entries. | Mermaid/static image. | Shows Claude and Codex payloads separately. | Must |
| First-run checklist | Users do not know whether prerequisites are complete. | Checkbox flow by platform and workflow goal. | Prerequisite list and command matrix. | Markdown checklist. | Includes Spec Kit CLI, constitution, `gh`, `jq`, restart where needed. | Must |
| Troubleshooting decision tree | Users cannot map symptom to cause. | Select symptom and platform to see diagnosis/fix. | Known failure modes from README and official docs. | Table by symptom. | Includes cache/path/permission/version/CLI-not-found cases. | Should |
| Spec Kit lifecycle visualizer | Users cannot see how PRD, roadmap, workflow, and phases connect. | Stepper or diagram with phase artifacts and gates. | `speckit-pro` README and Spec Kit docs. | Mermaid/static diagram. | Distinguishes product requirements from implementation phases. | Should |
| Release readiness checklist | Contributors miss build/test/sync steps. | Checklist grouped by changed file class. | CI workflow, scripts, AGENTS/CLAUDE guidance. | Markdown checklist. | Maps each changed surface to validation command. | Must |
| Glossary popovers | Terms overload new users. | Hover/focus glossary definitions. | Glossary source file. | Linked glossary page. | Keyboard accessible; deep-linkable definitions. | Could |

## 10. Success Metrics

| Metric type | Metric | Target direction |
|---|---|---|
| Activation | First install completion rate for Claude and Codex paths. | Increase |
| Activation | First successful `speckit-pro` workflow completion. | Increase |
| Task completion | Time from landing page to correct platform command sequence. | Decrease |
| Support friction | Install/path/cache/version-related issues or repeated questions. | Decrease |
| Docs quality | Site build, markdown lint, link check, and manifest/payload validation pass rate. | Maintain at 100% on protected branches |
| Maintenance | Marketplace/manifest/version drift incidents. | Decrease |
| Trust | Users can identify plugin source, payload, hooks/agents, permissions, and rollback/update path in evaluator review. | Increase via checklist completion |
| Accessibility | Keyboard navigation and automated accessibility checks for interactive components. | Pass required checks |

Analytics implementation is out of scope until the docs stack and hosting path are selected.

## 11. Risks, Assumptions, and Open Questions

### Validated facts

- Claude and Codex marketplace/source/dist manifest versions agree at `2.12.0` in this worktree.
- The repo has generated Claude and Codex payloads under `dist/**`.
- There is no existing docs-site package/config/lockfile found at depth 3.
- The current plugin README already contains many required facts, but as a long single document.
- `speckit-pro/commands` is absent in this checkout even though AGENTS-style guidance mentions command docs.

### Assumptions

- Static docs should be hosted from this repository, not a separate marketing repo.
- Docusaurus/MDX is a leading candidate, but not selected until DOC-SPEC-001 completes.
- Safe interactive docs are acceptable if every interaction degrades to static content.
- Detailed implementation tasks belong in later Spec Kit phases, not this PRD.

### Maintainer decisions still required

- Final static-site framework and package manager.
- Hosting target and deployment policy.
- Whether existing README content becomes source content, generated excerpts, or redirects into the site.
- Whether docs CI should run on docs-only PRs immediately or after the site foundation exists.
- Exact treatment of legacy `commands/` wording in AGENTS/README style guidance.
- Whether personal Codex marketplace path examples need correction after official-doc validation.

### Risks requiring mitigation

- Official OpenAI/Anthropic plugin docs are moving targets; docs must include source-update reminders.
- A static site adds a new dependency surface to a Bash/Markdown-heavy repo.
- Interactive widgets can obscure critical commands if static fallbacks are weak.
- Duplicating roadmap files for prompt and SpecKit compatibility can create drift; one canonical owner should be chosen after initial handoff.
- If docs validation is added too late, site drift can ship silently.

## 12. Leanness Test

A PRD section earns its place only if it:

- Changes a requirement.
- Resolves a downstream ambiguity.
- Defines a user-visible success condition.
- Constrains scope.
- Provides evidence for a decision.
- Creates a testable acceptance criterion.

Cut sections that only restate background, duplicate another artifact, or describe implementation details that belong in the roadmap/spec phases.

## 13. SPEC Catalog Crosswalk

| Feature | Acceptance criteria | SPEC | Depends on | Priority |
|---|---|---|---|---|
| DOC-FR-001 Static docs framework and IA spike | AC-1.* | DOC-SPEC-001 | None | P1 |
| DOC-FR-002 Unified landing page and IA shell | AC-2.* | DOC-SPEC-002 | DOC-SPEC-001 | P1 |
| DOC-FR-003 Claude Code marketplace installation path | AC-3.* | DOC-SPEC-003 | DOC-SPEC-002 | P1 |
| DOC-FR-004 Codex marketplace installation path | AC-4.* | DOC-SPEC-004 | DOC-SPEC-002 | P1 |
| DOC-FR-005 First successful workflow tutorial | AC-5.* | DOC-SPEC-005 | DOC-SPEC-003, DOC-SPEC-004 | P1 |
| DOC-FR-006 Safe interactive selector and validation aids | AC-6.* | DOC-SPEC-006 | DOC-SPEC-002, DOC-SPEC-003, DOC-SPEC-004 | P1 |
| DOC-FR-007 Command, workflow, manifest, and file-layout reference | AC-7.* | DOC-SPEC-007 | DOC-SPEC-003, DOC-SPEC-004 | P2 |
| DOC-FR-008 Troubleshooting, security, trust, update, rollback | AC-8.* | DOC-SPEC-008 | DOC-SPEC-003, DOC-SPEC-004, DOC-SPEC-007 | P1 |
| DOC-FR-009 Maintainer and contributor release workflow | AC-9.* | DOC-SPEC-009 | DOC-SPEC-007 | P1 |
| DOC-FR-010 Search, accessibility, deep links, docs validation | AC-10.* | DOC-SPEC-010 | DOC-SPEC-001, DOC-SPEC-002, DOC-SPEC-006 | P2 |
