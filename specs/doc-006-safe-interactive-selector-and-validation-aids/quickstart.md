# Quickstart: Safe Interactive Selector and Validation Aids

## Focused Validation

Run the DOC-006 focused fixture or metadata/rendering test:

```bash
node docs-site/scripts/validate-doc006-safe-aids.mjs
```

The focused check must cover:

- Required selector fields for every path.
- Unsupported or ambiguous selector-state handling with supported static guidance still reachable.
- Claude Code and Codex command-surface separation.
- Manifest checker `pass`, `mismatch`, and `unavailable` states.
- No pasted-JSON or local user diagnostic UI.
- Lightweight handoff links.
- First-run checkpoint coverage.
- Drift between manifest-backed rendered values and the six checked-in JSON/manifest files.

## Build Validation

```bash
pnpm --dir docs-site validate
```

## Link Validation

```bash
pnpm --dir docs-site validate:links
```

## Full Verify

```bash
pnpm --dir docs-site validate && pnpm --dir docs-site validate:links
```

## Manual Review Checklist

- Open the `choose-your-path` page and confirm all supported paths are visible in static fallback content.
- Disable JavaScript or inspect static HTML and confirm selector paths, checker rows, payload diagram content, and first-run checkpoints remain readable.
- Keyboard through selector, checker, diagram, and checklist controls in reading order.
- Confirm commands are visible guidance only and no browser behavior runs local commands or reads local files.
- Confirm checker comparisons show values, expected consistency rules, and lightweight handoffs for mismatch or unavailable states.
