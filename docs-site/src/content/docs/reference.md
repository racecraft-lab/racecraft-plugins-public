---
title: "Reference"
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

## Source Evidence

- [docs/prd-interactive-documentation.md](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/docs/prd-interactive-documentation.md)
- [docs/roadmap-interactive-documentation.md](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/docs/roadmap-interactive-documentation.md)
- [README.md](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/README.md)
- [speckit-pro/README.md](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/speckit-pro/README.md)

## Deferred Boundary

Full detail is deferred to DOC-007. This DOC-002 shell intentionally stops before command catalogs, hook matrices, agent inventories, payload manifests, test inventories, or deep source citations.

## Next Step

[Open the contributor and release shell](/racecraft-plugins-public/contribute-and-release/) if you need maintainer workflow orientation.
