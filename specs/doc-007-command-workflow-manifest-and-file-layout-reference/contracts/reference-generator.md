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
- Exits `2` for source, parsing, output-write, or internal errors and prints the error category plus source/output path or generator phase on stderr.

### Check

```bash
pnpm --dir docs-site reference:check
```

- Runs `node scripts/generate-reference-pages.mjs --check`.
- Renders expected Markdown in memory and compares it with committed generated output.
- Does not create, rewrite, delete, format, or update generated files, docs-site package/config files, sidebar configuration, or existing docs links.
- Treats missing or changed visible generated notices, command/skill reference fields, manifest field groupings, source fields, or inferred-note fields as stale generated output.
- Exits `0` when generated output is current.
- Exits `1` when output is stale, prints stale repo-relative page paths on stdout, and prints `pnpm --dir docs-site reference:generate` as the fix command.
- Exits `2` when source/parsing/internal errors prevent a trustworthy comparison and prints the error category plus repo-relative source path or generator phase on stderr.

## Diagnostics

Exit `1` is reserved for stale generated output and writes only stale generated page paths plus the generate command to stdout.

Exit `2` writes diagnostics to stderr with one of these categories:

- `source`: missing/unreadable required source, allowlist violation, or normalized path violation.
- `parse`: malformed JSON, malformed or missing Markdown/frontmatter metadata, or missing required metadata fields.
- `output-write`: generated output write failure in generate mode.
- `internal`: render, comparison, or other generator failure without a more specific source or parse classification.

Each exit-`2` diagnostic includes a concise cause and a repo-relative source/output path when one exists. If no single path applies, the diagnostic names the failing generator phase.

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
- For command or skill records: visible Claude Code invocation, Codex invocation, purpose, prerequisites, and expected output artifact fields when applicable and source-backed.
- For manifest records: visible runtime-specific required and optional field groupings for Claude Code and Codex plugin manifests.

## Boundaries

- The generator does not read generated reference pages as source evidence.
- The generator does not inspect `.git`, `.worktrees`, `node_modules`, user-local plugin installs, network resources, or pasted JSON.
- The generator does not change plugin behavior, manifests, payload content, marketplace behavior, install flow, hook semantics, release automation, or GitHub Actions.
