# Quickstart: Command, workflow, manifest, and file-layout reference

## Prerequisites

- Use the DOC-007 worktree on branch `doc-007-command-workflow-manifest-and-file-layout-reference`.
- Keep `.github/workflows/*`, plugin manifests, generated payload content, marketplace files, install flow, hook semantics, and release automation out of scope.
- Ensure docs-site dependencies are available from `docs-site/pnpm-lock.yaml`.

## Generate Reference Pages

```bash
pnpm --dir docs-site reference:generate
```

Expected result:

- Seven Markdown files exist under `docs-site/src/content/docs/reference/`.
- Output is deterministic for unchanged checked-in source files.
- Each generated page includes the generated notice, visible `Sources`, and visible `Inferred notes`.
- Skill or command records show runtime invocation forms, purpose, prerequisites, and expected output artifacts; manifest records separate required and optional fields for Claude Code and Codex.

## Check Reference Freshness

```bash
pnpm --dir docs-site reference:check
```

Expected result:

- Exit `0` when generated pages are current.
- Exit `1` when generated pages are stale, with stale page paths and the generate command printed.
- Exit `2` for source, parsing, or internal errors.
- Working tree remains unchanged in check mode.

## Validate Docs Site

```bash
pnpm --dir docs-site validate
```

Expected result:

- Runs `reference:check` before the existing Astro check/build sequence.
- Fails if generated references are stale.

## Validate Links

```bash
pnpm --dir docs-site validate:links
```

Expected result:

- Builds the docs site with the existing Starlight link validator.
- Public reference links use `/racecraft-plugins-public/reference/<slug>/`.

## Scope Review

```bash
git diff --name-only
```

Expected result:

- Diff is limited to docs-site generator/scripts/config/reference content and DOC-007 planning artifacts.
- No `.github/workflows/*` files changed.
- No plugin behavior, manifest semantics, generated payload content, marketplace behavior, install flow, hook semantics, or release automation changed.

## Optional Plugin Safety Check

Run this only if implementation touches plugin/spec surfaces beyond docs-site reference generation:

```bash
bash tests/speckit-pro/run-all.sh --layer 1
```

Expected result:

- Layer 1 structural validation passes with zero failures.
