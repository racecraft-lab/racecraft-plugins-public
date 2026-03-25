# CI/CD, Versioning & Release Pipeline Design

**Date:** 2026-03-24
**Status:** Approved
**Author:** Fredrick Gabelmann + Claude Code

## Problem

The racecraft-plugins-public marketplace repo has no CI/CD pipeline, no automated versioning, no changelog generation, and no release workflow. All testing is manual, versions are hardcoded, and releases are done by pushing directly to main. As the marketplace grows from 1 to 2-4 plugins, this workflow will not scale for a solo maintainer.

Additionally, the repo currently sets `version` in both `plugin.json` and `marketplace.json`, which Anthropic warns against — `plugin.json` always wins silently, making the marketplace version misleading.

## Constraints

- Solo maintainer — automation must be maximized
- 2-4 plugins expected within 6 months, all maintained by one person
- Must align with Anthropic's official plugin documentation (semver, version-driven cache invalidation, `plugin.json` as version authority)
- Existing 5-layer test suite must be preserved and integrated
- Layers 2/3 (AI evals) are expensive — local only, not in CI
- GitHub Copilot Pro+ available for free code review on PRs

## Design

### 1. Branching & Commit Strategy

**Trunk-based development with short-lived feature branches.**

- `main` is the protected release branch — always releasable
- All changes arrive via PR with squash merge
- Each squash merge produces one clean conventional commit from the PR title
- Branch naming convention: `feat/`, `fix/`, `chore/`, `docs/` prefixes

**Conventional Commit scoping for multi-plugin:**

```text
feat(speckit-pro): add new checklist domain
fix(future-plugin): handle edge case in validation
chore: update CI workflow
```

The `(scope)` maps to the plugin directory name. release-please uses this to determine which plugin's version to bump.

**Branch protection on `main`:**

- Require PR before merging
- Require CI status checks to pass (`validate-plugins`, `validate-pr-title`)
- Require Copilot code review
- Allow only squash merges
- No direct pushes

### 2. CI Pipeline — PR Workflow

**Trigger:** Every PR targeting `main`.

**Jobs (run in parallel):**

1. **validate-plugins**
   - Detect which plugin directories were modified (`git diff`)
   - Run Layer 1 (structural validation) for changed plugins
   - Run Layer 4 (script unit tests) for changed plugins
   - Run Layer 5 (tool scoping) for changed plugins
   - Skip if no plugin directories changed (e.g., README-only)

2. **validate-pr-title**
   - Check PR title matches Conventional Commits format
   - Pattern: `(feat|fix|chore|docs|refactor|test)(\(.+\))?!?: .+`
   - Required for release-please to parse commits correctly
   - **Note:** The regex does not validate that the scope matches an actual plugin directory. A typo like `feat(spekit-pro):` would pass but release-please would ignore it. Double-check scopes before merging.

3. **copilot-review** (automatic)
   - GitHub Copilot reviews the diff
   - Configured in GitHub repo settings, not in the workflow file

**What is NOT in CI:**

- Layers 2/3 (AI evals) — local only, run manually before merge when desired
- Build/compile steps — plugins are markdown + shell, nothing to compile

### 3. Release Automation

**Tool:** [Google release-please](https://github.com/googleapis/release-please)

**How it works:**

1. release-please watches `main` for conventional commits
2. It opens/updates a Release PR per plugin that has changes:
   - Bumps `version` in the plugin's `.claude-plugin/plugin.json`
   - Generates/updates the plugin's `CHANGELOG.md`
   - PR title: `chore(speckit-pro): release 1.1.0`
3. When the Release PR is merged:
   - Creates a GitHub Release with release notes
   - Creates a git tag per plugin (e.g., `speckit-pro-v1.1.0`)
   - Post-release CI job runs `sync-marketplace-versions.sh`
   - Syncs bumped version into `.claude-plugin/marketplace.json`
   - Commits and pushes the marketplace.json update (CI bot uses `GITHUB_TOKEN` with branch protection bypass configured in repo rulesets)

**Version bump rules:**

| Commit type | Version bump | Example |
| --- | --- | --- |
| `fix(plugin):` | Patch (1.0.0 → 1.0.1) | Bug fix |
| `feat(plugin):` | Minor (1.0.0 → 1.1.0) | New feature |
| `feat(plugin)!:` or `BREAKING CHANGE:` | Major (1.0.0 → 2.0.0) | Breaking change |
| `chore:`, `docs:`, `refactor:` | No release | Maintenance |

**Pre-1.0 behavior:** With `bump-minor-pre-major: true`, breaking changes on a `0.x.y` version bump minor (0.1.0 → 0.2.0) instead of major. This protects new plugins from jumping to 1.0.0 prematurely. Once a plugin reaches 1.0.0, this flag has no effect.

**Multi-plugin behavior:**

- Each plugin versions independently
- A commit scoped to one plugin only triggers a release for that plugin
- Each plugin gets its own `CHANGELOG.md` inside its directory
- Each plugin gets its own git tag: `speckit-pro-v1.1.0`, `future-plugin-v0.2.0`

**Changelog generation:**

Changelogs are generated automatically from squashed commit messages on main. The 100 messy commits on a feature branch are irrelevant — only the clean PR title (used as the squash commit message) appears in the changelog.

### 4. Version Source of Truth

**`plugin.json` is the source of truth.** This aligns with Anthropic's documented behavior where `plugin.json` always takes precedence.

**Version flow:**

```text
Conventional Commit on main
  → release-please bumps plugin.json
    → sync-marketplace-versions.sh reads plugin.json
      → updates marketplace.json plugin entry
```

**marketplace.json does not have its own version.** It is a registry that lists plugins at their individual versions:

```json
{
  "name": "racecraft-public-plugins",
  "owner": { "name": "Fredrick Gabelmann" },
  "plugins": [
    {
      "name": "speckit-pro",
      "source": "./speckit-pro",
      "description": "...",
      "version": "1.1.0"
    },
    {
      "name": "future-plugin",
      "source": "./future-plugin",
      "description": "...",
      "version": "0.2.0"
    }
  ]
}
```

### 5. Local Development Workflow

```text
1. Create feature branch
   $ git checkout -b feat/new-feature

2. Develop and test locally
   $ claude --plugin-dir ./speckit-pro       # test plugin changes live
   $ /reload-plugins                          # pick up changes without restart
   $ bash speckit-pro/tests/run-all.sh        # Layers 1, 4, 5 (fast)
   $ bash speckit-pro/tests/run-all.sh --all  # Layers 2, 3 (AI evals, optional)

3. Push and open PR
   $ git push -u origin feat/new-feature
   $ gh pr create --title "feat(speckit-pro): description"
   → CI runs Layers 1, 4, 5
   → Copilot reviews the diff

4. Squash merge the PR
   → release-please detects the new commit on main
   → Opens/updates a release PR

5. When ready to release
   → Merge the release PR
   → CI tags, generates changelog, syncs marketplace.json
```

**Adding a new plugin:**

1. Create `new-plugin/` directory with `.claude-plugin/plugin.json`
2. Add the plugin entry to `release-please-config.json` and `.release-please-manifest.json`
3. Add the plugin entry to `.claude-plugin/marketplace.json` (version will be managed by sync script after first release)
4. CI auto-discovers the new plugin directory for test scoping

### 6. Repository Configuration Files

**New files:**

```text
racecraft-plugins-public/
├── .github/
│   └── workflows/
│       ├── pr-checks.yml              ← PR validation + tests
│       └── release.yml                ← release-please + marketplace sync
├── scripts/
│   └── sync-marketplace-versions.sh   ← reads plugin.json versions → updates marketplace.json
├── release-please-config.json         ← per-plugin release configuration
└── .release-please-manifest.json      ← current version tracker
```

**release-please-config.json:**

```json
{
  "release-type": "simple",
  "packages": {
    "speckit-pro": {
      "component": "speckit-pro",
      "changelog-path": "CHANGELOG.md",
      "bump-minor-pre-major": true,
      "extra-files": [
        {
          "type": "json",
          "path": ".claude-plugin/plugin.json",
          "jsonpath": "$.version"
        }
      ]
    }
  }
}
```

Note: `extra-files` paths are relative to the package directory (e.g., `speckit-pro/`). The `type: "json"` with `jsonpath` tells release-please how to locate and update the version field inside `plugin.json`.

**.release-please-manifest.json:**

```json
{
  "speckit-pro": "1.0.0"
}
```

**Files modified:**

- `.claude-plugin/marketplace.json` — version field managed by sync script (not manual)
- `speckit-pro/.claude-plugin/plugin.json` — version managed by release-please (not manual)

### 7. User Update Path

When a release is cut, users update via:

```bash
/plugin marketplace update racecraft-public-plugins
# → git pulls the marketplace repo
# → sees new version in marketplace.json for changed plugins
# → re-caches only plugins with bumped versions
```

Auto-update is off by default for third-party marketplaces. Users can enable it per-marketplace in the Claude Code plugin manager.

### 8. Recovery & Rollback

**If the sync script fails after a release tag is created:**

- Re-run the sync workflow manually via `gh workflow run release.yml`
- Or run `bash scripts/sync-marketplace-versions.sh` locally and push

**If a bad version is released:**

- Revert the breaking commit on main via a new PR (`fix(plugin): revert ...`)
- release-please will create a new patch release with the fix
- Do NOT delete git tags — they serve as an audit trail

**To force a specific version:**

- Add `Release-As: 2.0.0` to a commit message or PR body
- release-please will use that version instead of computing from conventional commits

## Out of Scope

- npm publishing — plugins are git-based
- Container/Docker workflows — not a service
- Multi-environment deployments — it's a git repo
- Layer 2/3 AI evals in CI — local only
- Community contribution workflows — solo maintainer
- Stable/latest release channels — single channel for now, can add later via `ref` pinning

## References

- [Anthropic Plugins Reference — Version Management](https://code.claude.com/docs/en/plugins-reference#version-management)
- [Anthropic Plugin Marketplaces — Release Channels](https://code.claude.com/docs/en/plugin-marketplaces)
- [Google release-please](https://github.com/googleapis/release-please)
- [Conventional Commits](https://www.conventionalcommits.org/)
