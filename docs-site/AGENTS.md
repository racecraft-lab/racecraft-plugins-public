# docs-site Guidelines

The docs site is the only non-Python toolchain in this repository: Astro 6.4.6 + Starlight 0.40.0, pnpm 10.25.0, JavaScript ESM on Node.

## Commands

Run everything from the repository root with `pnpm --dir docs-site <script>` — do not `cd` into docs-site.

- `pnpm --dir docs-site validate` — full local gate: reference check, type check, link validation, safe-aids, quality, and Playwright smoke.
- `pnpm --dir docs-site reference:generate` — regenerates the committed reference pages under `src/content/docs/reference/`.
- `pnpm --dir docs-site reference:check` — what CI runs; fails if committed reference pages drift from a fresh generation.

## Constraints

- Node >= 22.12 is required. Older Node (for example a default 20.x) fails in non-obvious ways, including a dev server that never serves.
- `src/content/docs/reference/**` is generated output. Never hand-edit it — change the sources or `scripts/generate-reference-pages.mjs`, then regenerate and commit.
- The reference generator sorts with a code-point sort on purpose. Do not switch it to `localeCompare`: locale-dependent ordering differs between macOS and CI Linux and makes `reference:check` fail forever.
- Adding, renaming, or removing any `.sh`/`.py`/`.md` file under `tests/speckit-pro/` changes the generated tests reference page — regenerate and commit it in the same PR.
