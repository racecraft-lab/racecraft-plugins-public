# DOC-002 Polish Evidence

## Route Coverage

- All 11 route shells from `contracts/route-shell-manifest.json` exist under `docs-site/src/content/docs/`.
- `docs-site/astro.config.mjs` includes the four Diataxis sidebar groups: Tutorials, How-to, Reference, and Explanation.
- Each route slug appears in the sidebar exactly once.

## Source And Payload Boundary

- `docs-site/src/content/docs/index.mdx` and `docs-site/src/content/docs/reference.md` both distinguish `speckit-pro/` authoring source from generated install payloads under `dist/claude/**` and `dist/codex/**`.
- `README.md`, `speckit-pro/README.md`, `speckit-pro/**`, `dist/claude/**`, `dist/codex/**`, `.claude-plugin/**`, and `.github/workflows/**` have no diff in this branch.

## Validation Evidence

- `cd docs-site && pnpm install` passed after network escalation and generated `docs-site/pnpm-lock.yaml`.
- `cd docs-site && pnpm check` passed with 0 errors, 0 warnings, and 0 hints.
- `cd docs-site && pnpm build` passed and `starlight-links-validator` reported all internal links valid.
- `cd docs-site && pnpm validate:links` passed and reported all internal links valid.
- `cd docs-site && pnpm validate` passed through `pnpm check && pnpm build`.
- `git diff --check` passed.

## Final Reviewability Backstop

- `bash speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh diff origin/main...HEAD` returned `status=block`.
- Blocker: `total files 36 exceeds block threshold 25`.
- Non-blocking metrics: `reviewable_loc=40`, `production_files=2`.
- Formal backstop persisted:
  - `specs/doc-002-unified-landing-page-and-ia-shell/.process/final-reviewability/gate-state.json`
  - `specs/doc-002-unified-landing-page-and-ia-shell/.process/final-reviewability/reslicing-packet.json`
- The backstop blocked PR body generation, single PR creation, and multi-PR emission until a valid reviewable slice plan exists or an explicit operator-owned typed exception is committed.
