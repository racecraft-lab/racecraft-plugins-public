---
title: "Reference"
description: "The reference shell for SpecKit Pro repository surfaces and generated payloads — your index into skills, agents, manifests, marketplace files, hooks, scripts, tests, and file layout."
---

Use this route as the stable reference shell for repository surfaces and generated payload orientation.

## Route Shell

- **Audience:** Users, agents, and maintainers
- **Purpose:** Index commands, skills, manifests, marketplace files, hooks, agents, payloads, tests, and file layout.
- **Shell owner DOC:** DOC-002
- **Full-content owner DOC:** DOC-007
- **Success criterion:** Each supported surface has a stable deep link and source citation.
- **Useful now:** Use this page to decide whether you are looking at authoring source, generated payloads, or later reference content.

## Source And Generated Payloads

The authoring source lives in `speckit-pro/`. That tree is where plugin commands, skills, agents, hooks, tests, and related authoring files are maintained.

Generated install payloads live under `dist/claude/**` and `dist/codex/**`. Those payload trees are built for their target platforms, so their layout can differ from `speckit-pro/` and should not be treated as the authoring source.

## Generated Reference Subpages

- [Skills](/racecraft-plugins-public/reference/skills/) lists Claude Code and Codex skill invocations, prerequisites, expected artifacts, and source citations.
- [Agents](/racecraft-plugins-public/reference/agents/) compares Claude Code plugin agents with Codex custom-agent templates.
- [Manifests](/racecraft-plugins-public/reference/manifests/) separates marketplace, plugin, integration, and generated distribution manifests.
- [Hooks](/racecraft-plugins-public/reference/hooks/) documents runtime hook configuration files without changing hook behavior.
- [Scripts](/racecraft-plugins-public/reference/scripts/) inventories repository scripts and SpecKit Pro helper scripts by role.
- [Tests](/racecraft-plugins-public/reference/tests/) inventories the SpecKit Pro validation layers and test-only files.
- [Source vs dist](/racecraft-plugins-public/reference/source-vs-dist/) maps editable source, generated payloads, tests, release files, and docs infrastructure.

## Source Evidence

- [docs/prd-interactive-documentation.md](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/docs/prd-interactive-documentation.md)
- [docs/roadmap-interactive-documentation.md](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/docs/roadmap-interactive-documentation.md)
- [README.md](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/README.md)
- [speckit-pro/README.md](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/speckit-pro/README.md)

## Generated Page Boundary

DOC-007 owns the generated subpages listed above. They are committed Markdown output generated from checked-in repository files. Do not treat generated pages as source evidence for themselves; rerun `pnpm --dir docs-site reference:generate` after source changes, then use `pnpm --dir docs-site reference:check`.

## DOC-008 Support Handoffs

Use these hand-authored handoffs when a reference page identifies the source or
payload surface, but you need diagnosis or recovery guidance:

- [Troubleshooting](/racecraft-plugins-public/troubleshooting/) maps install,
  marketplace, generated payload, cache/runtime, permissions, CLI prerequisite,
  path, version, and Codex custom-agent symptoms to read-only inspection and a
  safe next action.
- [Security & Trust](/racecraft-plugins-public/security-and-trust/) separates
  official platform behavior, Racecraft repository facts, and recommended
  practice for manifests, skills, agents, hooks, MCP/app integrations,
  sandboxing, approvals, managed policy, cache/runtime state, and rollback
  boundaries.
- [Update & Rollback](/racecraft-plugins-public/update-and-rollback/) defines
  update, refresh, reinstall, remove, rollback, stale payload, stale cache, and
  version-sync recovery cases without hand-editing generated payloads or
  installed caches.

## Next Step

[Open the contributor and release shell](/racecraft-plugins-public/contribute-and-release/) if you need maintainer workflow orientation.
