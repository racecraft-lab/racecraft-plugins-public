# Quickstart: Validate DOC-003 Implementation

This guide validates the DOC-003 docs-only implementation after tasks are generated and implemented.

## Prerequisites

- Work from branch `doc-003-claude-code-marketplace-installation-path`.
- Do not regenerate `dist/**`, bump versions, change plugin behavior, or alter release automation.
- Use pnpm from `docs-site/package.json`.

## Scenario 1: Planning artifacts exist

```bash
test -f specs/doc-003-claude-code-marketplace-installation-path/plan.md
test -f specs/doc-003-claude-code-marketplace-installation-path/research.md
test -f specs/doc-003-claude-code-marketplace-installation-path/data-model.md
test -f specs/doc-003-claude-code-marketplace-installation-path/quickstart.md
test ! -d specs/doc-003-claude-code-marketplace-installation-path/contracts
```

Expected result: all commands exit 0. `contracts/` is intentionally absent because DOC-003 has no external software interface.

## Scenario 2: Canonical Claude route contains required install surface

```bash
rg -n "/plugin marketplace add|/plugin install|/reload-plugins|/plugin|/speckit-pro:speckit-status|/speckit-pro:speckit-coach" docs-site/src/content/docs/install/claude-code.md
```

Expected result: the Claude install page includes the sequential install commands, reload command, plugin manager check, and both namespaced skill checks.

## Scenario 3: Lifecycle guidance is complete and bounded

```bash
rg -n "update|uninstall|remove|reinstall|Codex" docs-site/src/content/docs/install/claude-code.md
```

Expected result: lifecycle maintenance covers update, uninstall, marketplace removal, and reinstall. Codex appears only as a cross-link to `/install/codex/`, not as Claude-page install instructions.

## Scenario 4: Trust inventory is source-backed

```bash
rg -n "skills|agents|hooks|settings|generated|dist/claude|marketplace.json|plugin.json" docs-site/src/content/docs/install/claude-code.md
```

Expected result: the page identifies skills, agents, hooks, settings/MCP implications, source manifests, and generated Claude payloads without conflating source paths with generated paths.

## Scenario 5: Install-relevant terminology uses skills language

```bash
rg -n "command-folder|command folder|deprecated command|commands/" README.md AGENTS.md speckit-pro/README.md docs-site/src/content/docs/install/claude-code.md
```

Expected result: any matches are either source-path references that are not install-relevant, historical migration context, or wording that explicitly directs users to current skills terminology. There should be no user-facing install instruction that tells Claude Code users to invoke deprecated command-folder behavior.

## Scenario 6: Docs site validates

```bash
pnpm --dir docs-site validate
```

Expected result: validation completes successfully.

## Scenario 7: Runtime and release surfaces remain untouched

```bash
git diff --name-only | rg '^(dist/|speckit-pro/(skills|agents|hooks|scripts|\.claude-plugin)/|release-please-config\.json|\.release-please-manifest\.json|\.github/workflows/)'
```

Expected result: no output. If this command reports a file, either remove the unintended change or add `bash tests/speckit-pro/run-all.sh --layer 1` to verification only if the scope change is approved.
