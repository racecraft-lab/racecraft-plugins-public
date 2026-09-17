# Quickstart: DOC-008 Validation

This guide validates the DOC-008 implementation after the user-facing pages are edited.

## Prerequisites

- Work from the DOC-008 worktree.
- Keep implementation docs-only unless a later approved change expands scope.
- Recheck official platform docs before final platform-behavior wording ships.

## Expected Files

The implementation should change these docs-site files:

```text
docs-site/src/content/docs/troubleshooting.md
docs-site/src/content/docs/security-and-trust.md
docs-site/src/content/docs/update-and-rollback.md
docs-site/src/content/docs/install/claude-code.md
docs-site/src/content/docs/install/codex.md
docs-site/astro.config.mjs
```

No plugin behavior, manifest, hook, generated payload, marketplace registry, release automation, CI workflow, or browser diagnostic command should change.

## Manual Content Checks

1. Open `troubleshooting.md`.
   - Expected: every matrix row has symptom, platform label, likely cause, read-only inspect command/file, recommended fix, follow-up link, and source citation.
   - Expected: inspect cells do not include mutating actions.

2. Open `security-and-trust.md`.
   - Expected: claims are grouped as official vendor behavior, repository facts, and recommended practice.
   - Expected: the page says DOC-008 is not a security audit, certification, formal threat model, or control attestation.

3. Open `update-and-rollback.md`.
   - Expected: update, refresh, reinstall, remove, rollback, stale payload, stale cache, and version sync are defined.
   - Expected: each recovery case has checkpoint, manual action, side effect, reload/restart expectation, and source citation.

4. Open `docs-site/astro.config.mjs`.
   - Expected: `update-and-rollback` is exposed in the Starlight sidebar, preferably in the existing How-to group near `troubleshooting`.

5. Review the implementation diff.
   - Expected: changed files remain docs/process surfaces.
   - Expected: generated `docs-site/src/content/docs/reference/*.md` pages are not hand-edited.

## Required Validation Commands

```bash
pnpm --dir docs-site reference:check
pnpm --dir docs-site validate
pnpm --dir docs-site validate:links
pnpm --dir docs-site validate && pnpm --dir docs-site validate:links
```

Expected result: all commands pass.

## Conditional Plugin Validation

Run this only if implementation touches plugin/spec surfaces, manifests, scripts, hooks, or generated payload paths:

```bash
bash tests/speckit-pro/run-all.sh --layer 1
```

Expected result when applicable: Layer 1 passes with zero failures.

## Rollback Check

DOC-008 has no runtime feature flag. Rollback is a docs-site revert:

```bash
git diff --name-only
```

Expected result: reverting the DOC-008 docs-site content and sidebar/link changes removes the user-facing feature without affecting plugin runtime behavior.
