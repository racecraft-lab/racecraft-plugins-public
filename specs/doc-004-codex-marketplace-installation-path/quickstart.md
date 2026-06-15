# Quickstart: Validate DOC-004 planning and implementation

This guide defines the validation path for the DOC-004 Codex install docs. It
does not execute a real marketplace install or write to a user's Codex config.

## Prerequisites

- Work from the DOC-004 checkout:
  `doc-004-codex-marketplace-installation-path`
- Keep implementation edits documentation-only unless a separate approved plan
  revision records a narrow source correction.
- Do not change Codex manifests, generated payloads, installer behavior, custom
  agent TOML templates, hooks, marketplace behavior, release automation, or
  runtime behavior.

## Manual Content Review

1. Open `docs-site/src/content/docs/install/codex.md`.
2. Confirm it starts with the Codex user's install decision, not marketing copy.
3. Confirm headings are semantic and task-oriented enough for screen-reader
   navigation: install decision, source/payload/cache distinction, install
   paths, custom-agent registration, verification, safety, and source evidence.
4. Confirm link text describes the destination or purpose without relying on
   surrounding prose alone.
5. Confirm command snippets are grouped or labeled by Codex platform, install
   scope, and source-of-truth context.
6. Confirm safety warnings are visible in text and not conveyed only through
   callout color, icons, or styling.
7. Confirm any install path matrix has clear headers/caption context and, if
   dense, a compact list/card alternative for mobile and screen-reader users.
8. Confirm the page distinguishes:
   - `.agents/plugins/marketplace.json`
   - `speckit-pro/.codex-plugin/plugin.json`
   - `dist/codex/speckit-pro/.codex-plugin/plugin.json`
   - `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/`
9. Confirm personal/local guidance points at `dist/codex/speckit-pro/` or a
   copy/sync of that payload, not `speckit-pro/`.
10. Confirm repo, personal/local, and CLI install contexts are visibly separate.
11. Confirm the custom-agent checklist includes:
   - `@SpecKit Pro -> install`
   - `$install`
   - default `~/.codex/agents/`
   - optional project-scoped `.codex/agents/`
   - rerun `$install` after plugin updates that change bundled custom-agent
     TOML files
   - restart requirement
   - the nine installer-copied TOML filenames
12. Confirm `uat-runbook-author.toml` is not listed as an expected installed file.
13. Confirm the bounded stale-after-update checkpoint names:
   - symptoms such as old skill text, old plugin metadata, unchanged
     custom-agent behavior, stale copied personal payload, or source/payload
     mismatch
   - surfaces to inspect: marketplace source or copied payload, generated
     payload, installed plugin cache, selected custom-agent destination, and
     restart state
   - next links to DOC-008 for deeper troubleshooting/update/remove/rollback
     and DOC-007 for reference details
14. Confirm the stale-after-update checkpoint does not become a troubleshooting
   matrix, cache forensics guide, rollback procedure, or instruction to edit the
   installed plugin cache.
15. Confirm the install-safety block is limited to first-install sandbox,
   approval, network, outside-workspace write, installed cache/source, bundled
   lifecycle hook configuration, and external app/MCP authentication
   expectations.
16. Confirm bundled lifecycle hooks are identified as plugin payload
   configuration when present, with hook trust analysis, policy tuning, and
   lifecycle security deferred to DOC-008.
17. Confirm deeper reference/troubleshooting/security lifecycle topics are
   deferred to DOC-007 or DOC-008.

## README Consistency Review

1. Compare `README.md`, `speckit-pro/README.md`, and
   `docs-site/src/content/docs/install/codex.md`.
2. Confirm all three agree on:
   - repo marketplace file
   - generated Codex payload target
   - installed plugin cache behavior
   - install skill invocation
   - stale-after-update checkpoint
   - restart requirement
   - custom-agent verification list
   - bounded safety wording
3. Confirm README surfaces are allowed to be concise but contain no contradictory
   Codex path, command, cache, or verification statements.

## Command-Snippet Source Review

For every changed Codex command or path snippet, record source evidence from:

- Official OpenAI Codex docs:
  - https://developers.openai.com/codex/plugins
  - https://developers.openai.com/codex/plugins/build
  - https://developers.openai.com/codex/skills
  - https://developers.openai.com/codex/subagents
  - https://developers.openai.com/codex/permissions
  - https://developers.openai.com/codex/agent-approvals-security
- Local CLI help:
  - `codex plugin marketplace add --help`
- Checked-in source files:
  - `.agents/plugins/marketplace.json`
  - `speckit-pro/.codex-plugin/plugin.json`
  - `dist/codex/speckit-pro/.codex-plugin/plugin.json`
  - `speckit-pro/codex-skills/install/SKILL.md`
  - `speckit-pro/codex-skills/install/scripts/install-codex-agents.sh`
  - `speckit-pro/codex-agents/*.toml`
  - `speckit-pro/codex-hooks.json`

For hook-related snippets or safety claims, confirm the docs cite the Codex
plugin manifest `hooks` field or `speckit-pro/codex-hooks.json` as local source
evidence and do not imply hook execution bypasses Codex sandbox, approval, or
configured policy controls.

At minimum, cover the snippets listed in
`contracts/codex-install-content-contract.md`.

For accessibility, also record whether each changed command block is labeled by
Codex platform, install scope, and source-of-truth context, and whether nearby
links use descriptive link text.

## Automated Validation

Run from the repository root unless a command specifies another directory.

```bash
cd docs-site && pnpm validate
```

Expected result: Astro check and production build pass.

```bash
cd docs-site && pnpm validate:links
```

Expected result: the current DOC-002 link-validation hook passes. At planning
time this aliases `pnpm build`; DOC-004 must not change that script.

```bash
bash tests/speckit-pro/run-all.sh
```

Expected result: the default deterministic SpecKit Pro suite passes.

## PR Readiness Evidence

The implementation PR should include:

- Summary of the three documentation entry points changed.
- Non-goals stating no manifests, generated payloads, installer behavior, TOML
  templates, hooks, marketplace behavior, release automation, or runtime behavior
  changed.
- Review order: docs-site Codex page first, then README alignment.
- Scope budget from `plan.md`.
- Traceability from FR-001 through FR-019 or SC-001 through SC-007 to changed
  files and validation evidence.
- The manual command-snippet source review.
- Automated validation command output summaries.
- Known gaps deferred to DOC-007 or DOC-008.
- Rollback note: revert documentation changes only; no feature flag is involved.
