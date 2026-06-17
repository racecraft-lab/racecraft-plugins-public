# Contract: Reference Generator CLI

## Commands

### Generate

```bash
pnpm --dir docs-site reference:generate
```

- Runs `node scripts/generate-reference-pages.mjs`.
- Writes exactly seven generated Markdown subpages under `docs-site/src/content/docs/reference/`.
- Uses only checked-in allowlisted local source files as evidence.
- Prints a concise success summary listing generated pages.
- Exits `0` when generation completes.
- Exits `2` for source, parsing, or internal errors.

### Check

```bash
pnpm --dir docs-site reference:check
```

- Runs `node scripts/generate-reference-pages.mjs --check`.
- Renders expected Markdown in memory and compares it with committed generated output.
- Does not create, rewrite, delete, or format generated files.
- Exits `0` when generated output is current.
- Exits `1` when output is stale, prints stale repo-relative page paths on stdout, and prints `pnpm --dir docs-site reference:generate` as the fix command.
- Exits `2` when source/parsing/internal errors prevent a trustworthy comparison and names the source path on stderr where possible.

## Output Pages

The generator owns these committed files:

- `docs-site/src/content/docs/reference/skills.md`
- `docs-site/src/content/docs/reference/agents.md`
- `docs-site/src/content/docs/reference/manifests.md`
- `docs-site/src/content/docs/reference/hooks.md`
- `docs-site/src/content/docs/reference/scripts.md`
- `docs-site/src/content/docs/reference/tests.md`
- `docs-site/src/content/docs/reference/source-vs-dist.md`

## Content Contract

Each generated page includes:

- Starlight Markdown frontmatter with a stable title.
- A visible generated notice naming `docs-site/scripts/generate-reference-pages.mjs`, `pnpm --dir docs-site reference:generate`, and `pnpm --dir docs-site reference:check`.
- Stable section-per-record Markdown.
- Visible `Sources` fields for source facts.
- Visible `Inferred notes` fields for inferred notes, with `Based on:` source paths.
- Public source citation links using `https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/<path>`.

## Boundaries

- The generator does not read generated reference pages as source evidence.
- The generator does not inspect `.git`, `.worktrees`, `node_modules`, user-local plugin installs, network resources, or pasted JSON.
- The generator does not change plugin behavior, manifests, payload content, marketplace behavior, install flow, hook semantics, release automation, or GitHub Actions.
