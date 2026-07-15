# Docs Site Instructions

This directory owns the Astro/Starlight documentation site.

## Local Rules

- Run docs commands from the repository root with `pnpm --dir docs-site <script>`.
- Use Node >= 22.12 and the pinned pnpm version from this package.
- Do not hand-edit `src/content/docs/reference/**`; change the source or
  generator, then regenerate.
- Preserve deterministic ordering in reference generation.
- If test files under `tests/speckit-pro/` change, regenerate or check the test
  reference page before finishing.
