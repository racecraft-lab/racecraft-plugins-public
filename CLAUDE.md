# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A **Claude Code plugin marketplace** containing public plugins for spec-driven development. Plugins are installed via:
```bash
/plugin marketplace add racecraft-lab/racecraft-plugins-public
/plugin install speckit-pro@racecraft-public-plugins
```

After making changes, publish with:
```bash
git add . && git commit -m "Description" && git push
# Then in Claude Code:
/plugin marketplace update racecraft-public-plugins
```

## Plugin Architecture

Each plugin lives in its own top-level directory with this structure:
```
plugin-name/
├── .claude-plugin/plugin.json   ← Manifest (name, version, description, author)
├── agents/                      ← Subagent definitions (.md files)
├── commands/                    ← Slash commands (.md files with YAML frontmatter)
├── hooks/hooks.json             ← Event hooks (SessionStart, etc.)
├── skills/                      ← Skills with SKILL.md + optional references/ and scripts/
└── tests/                       ← 5-layer test suite
```

The marketplace registry is at `.claude-plugin/marketplace.json`. Adding a new plugin requires updating this file.

### Command File Format
Commands must have YAML frontmatter (`---`) with `description:` and `allowed-tools:` fields, followed by body content. No frontmatter = test failure.

### Skill Structure
Skills live under `skills/<skill-name>/` with a `SKILL.md` entry point. Supporting reference docs go in `references/` and shell scripts in `scripts/`.

## Running Tests

All tests are shell scripts. Run from the `speckit-pro/` directory:

```bash
# Default: Layers 1, 4, 5 (fast, deterministic)
bash tests/run-all.sh

# With live SpecKit project tests
bash tests/run-all.sh --live

# Single layer
bash tests/run-all.sh --layer 1   # Structural validation
bash tests/run-all.sh --layer 4   # Script unit tests
bash tests/run-all.sh --layer 5   # Agent tool scoping

# Layers 2 & 3 (AI evals — require skill-creator plugin and claude -p)
bash tests/layer2-trigger/run-trigger-evals.sh speckit-coach
bash tests/layer2-trigger/run-trigger-evals.sh speckit-autopilot
```

### Test Layers
| Layer | What it tests | Cost |
|-------|---------------|------|
| 1 – Structural | File existence, JSON validity, frontmatter format | Fast |
| 2 – Trigger | Skill trigger accuracy via eval harness | Slow (AI) |
| 3 – Functional | End-to-end skill behavior evals | Slow (AI) |
| 4 – Script unit | Shell script logic (validate-gate, detect-commands, etc.) | Fast |
| 5 – Tool scoping | Agent tool list restrictions | Fast |
| 6 – Efficiency | Agent model/effort cost-quality benchmarks | Slow (AI) |

Layer 2/3 evals require `skill-creator` plugin at `$SKILL_CREATOR_ROOT` (default: `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator`). Layers 2, 3, and 6 all require `claude -p` and are developer-local only.

Layer 6 evals use `speckit-pro/tests/layer6-efficiency/run-efficiency-benchmarks.sh` and require `claude -p`.

## speckit-pro Plugin

The only current plugin. It implements Spec-Driven Development (SDD) powered by [GitHub SpecKit](https://github.com/github/spec-kit).

**Key dependency:** The `specify` CLI must be installed for the plugin to function:
```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

The SessionStart hook warns if `specify` is not found.

**Commands:** `setup`, `autopilot`, `coach`, `status`, `resolve-pr`

**Skills:**
- `speckit-autopilot` — Autonomous 7-phase SDD workflow executor with multi-agent consensus. References in `references/` cover gate validation, consensus protocol, phase execution, TDD protocol, and post-implementation steps.
- `speckit-coach` — SDD methodology coaching. References cover command guide, constitution guide, presets/extensions, checklist domains, best practices, and getting-started templates.

## Active Technologies
- Bash (macOS/Linux) + jq (JSON processing), release-please (Google, version automation) (001-repository-foundation)
- YAML (GitHub Actions workflow) + Bash (inline scripts) + GitHub Actions (`actions/checkout`), no external dependencies (002-pr-checks-workflow)
- YAML (GitHub Actions workflow syntax) + Bash (inline sync step) + `googleapis/release-please-action@v4`, `actions/checkout@v4`, `jq` (pre-installed on `ubuntu-latest`) (003-release-automation)
- Bash (gh CLI v2+), Markdown (GitHub-Flavored) + GitHub CLI (`gh`), GitHub Actions (existing YAML workflows) (004-integration-verification)

## Recent Changes
- 001-repository-foundation: Added Bash (macOS/Linux) + jq (JSON processing), release-please (Google, version automation)

## Contributing & Branching Strategy

Feature branches use the naming convention `NNN-feature-name` where `NNN` is a zero-padded three-digit spec number (e.g., `004-integration-verification`).

**PR title requirements:** All PR titles MUST follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<optional scope>): <description>
```

Valid types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`

Examples:
- `feat(speckit-pro): add new coaching command`
- `fix: resolve session timeout`
- `docs: update CLAUDE.md CI/CD sections`
- `chore: sync marketplace.json versions`

The `validate-pr-title` CI check enforces this format and will block the PR if the title does not match.

**Merge policy:** The repository enforces squash-only merges. Merge commits and rebase merges are disabled. Every PR produces exactly one squash commit on `main`.

**Verification checklist:** Before merging a feature that touches CI workflows or release configuration, follow the end-to-end verification checklist at `docs/ai/specs/cicd-release-pipeline-verification.md` to confirm the pipeline remains functional.

## CI/CD Workflow

The PR Checks workflow (`.github/workflows/pr-checks.yml`) runs on every non-draft PR and contains four jobs:

| Job | Description |
|-----|-------------|
| `detect` | Detects which plugin directories changed relative to the base branch. Outputs a JSON array of plugin names. |
| `test (<plugin>)` | Runs `bash tests/run-all.sh` for each changed plugin (e.g. `test (speckit-pro)`). The name is dynamic — one job per plugin in the matrix. Skipped entirely when no plugin files changed (docs-only PRs). |
| `validate-plugins` | Sentinel/aggregator job. Always runs. Passes when all `test` matrix jobs passed or were skipped; fails when any matrix job failed or was cancelled. Provides the stable check name that branch protection requires. |
| `validate-pr-title` | Validates the PR title against the Conventional Commits pattern. |

**Why a sentinel job?** The `test` matrix job name is dynamic (`test (speckit-pro)`, `test (other-plugin)`, etc.) and cannot be registered as a stable required check name. The `validate-plugins` sentinel aggregates all matrix results into one stable name that branch protection can require.

**Docs-only PRs:** When a PR touches only documentation (no plugin directories), `detect` outputs `[]`, `test` is skipped (job-level `if:` evaluates to false — GitHub treats a skipped job as passing, not pending), and `validate-plugins` also passes. Docs-only PRs are not blocked by the test matrix.

**Maintenance warning:** If any job in `pr-checks.yml` is renamed, the corresponding required status check name in branch protection MUST be updated manually — GitHub does NOT automatically track job renames. A stale check name silently degrades protection: the renamed check never reports, the branch protection rule becomes vacuous, and PRs become mergeable without the check passing.

To detect drift, run:
```bash
gh api /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection \
  --jq '[.required_status_checks.contexts[]]'
```

Compare the output against the actual job names in `pr-checks.yml`. Recovery: re-run the Stage 1 branch protection setup command from `docs/ai/specs/cicd-release-pipeline-verification.md` with the corrected check names.

When modifying `.github/workflows/pr-checks.yml` or `.github/workflows/release.yml`, include a note in the PR description confirming whether CLAUDE.md's CI/CD sections require updates.

## Release Process

Releases are fully automated via [release-please](https://github.com/googleapis/release-please) (`googleapis/release-please-action@v4`), triggered by every push to `main`.

**How it works:**

1. **Conventional commit analysis:** After a PR is squash-merged to `main`, the Release workflow (`.github/workflows/release.yml`) runs. release-please scans new conventional commits and determines whether a release is warranted. Only `fix:`, `feat:`, and breaking-change commits trigger a release PR — `chore:` and `docs:` commits alone do not.

2. **Release PR creation:** When releasable commits exist, release-please opens a PR updating `CHANGELOG.md` and the version fields in `speckit-pro/.claude-plugin/plugin.json`. This PR accumulates further releasable commits until the maintainer merges it.

3. **GitHub Release publication:** When the release PR is merged, release-please creates a GitHub Release with a version tag (e.g., `speckit-pro-v1.2.0`).

4. **Marketplace sync:** The Release workflow detects the new release (via `steps.release.outputs['speckit-pro--release_created'] == 'true'`) and runs `scripts/sync-marketplace-versions.sh`. If `marketplace.json` changed, the workflow commits and pushes `chore: sync marketplace.json versions [skip ci]` directly to `main` as the `github-actions[bot]`. The `[skip ci]` trailer prevents a recursive Release workflow run.

5. **End-user update:** Plugin consumers run the following to receive the updated version:
   ```
   /plugin marketplace update racecraft-public-plugins
   ```

**Why the bot can push directly to `main`:** Branch protection is configured with `enforce_admins: false` (the default). On a personal repository, `GITHUB_TOKEN` has admin-equivalent permissions and bypasses the direct-push restriction when admin enforcement is disabled. The `permissions: contents: write` declaration in `release.yml` is also required — without it, `GITHUB_TOKEN` defaults to read-only and the push fails with 403. These are two independent controls: `enforce_admins: false` determines whether the push is permitted past branch protection; `permissions: contents: write` determines whether the token has write scope at all.

## Adding a New Plugin to Release Automation

When a new plugin directory is added to the repository, two files must be updated so release-please tracks and versions it.

**1. Add the package to `release-please-config.json`:**

```json
{
  "packages": {
    "speckit-pro": {
      "release-type": "simple",
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
    },
    "new-plugin-name": {
      "release-type": "simple",
      "component": "new-plugin-name",
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

**2. Add the initial version to `.release-please-manifest.json`:**

```json
{
  "speckit-pro": "1.1.0",
  "new-plugin-name": "0.1.0"
}
```

The key in `.release-please-manifest.json` MUST match the key in `release-please-config.json` exactly. The initial version is typically `0.1.0` for a new plugin.

**Also update the marketplace sync script** (`scripts/sync-marketplace-versions.sh`) if it needs to sync the new plugin's version to `.claude-plugin/marketplace.json`. Verify the script handles the new plugin name, then add the plugin to `.claude-plugin/marketplace.json` as well.

Note: CI will test the new plugin on PRs (if files changed), but release-please will not create a release entry until the plugin is added to `release-please-config.json`. This gap is silent — there is no automated check that validates alignment between plugin directories and release-please config.

## Recovery & Rollback Procedures

All commands below are written for this repository (`racecraft-lab/racecraft-plugins-public`) and require GitHub CLI v2+.

---

### Scenario 1: Re-trigger marketplace sync after a failed or missing sync

If the Release workflow ran but the marketplace sync did not complete (e.g., Actions runner error, push rejected):

```bash
gh workflow run release.yml --repo racecraft-lab/racecraft-plugins-public
```

This manually triggers the Release workflow, which will re-run release-please (idempotent) and the marketplace sync step if `speckit-pro--release_created` is still true.

---

### Scenario 2: Force a specific version with `Release-As`

To override release-please's inferred version bump and pin a specific version:

```bash
# Touch a file in the target component to scope the footer to that component,
# then add the Release-As footer to the commit message.
git commit -m "chore: force speckit-pro version

Release-As: 1.2.0" speckit-pro/.claude-plugin/plugin.json
git push origin main
```

The `Release-As: X.Y.Z` footer MUST appear in the git commit trailer (separated from the subject by a blank line). The commit MUST touch at least one file under `speckit-pro/` — a commit that touches no component files will not target any component. The footer overrides the inferred version in the next release-please PR.

---

### Scenario 3: Patch a bad release (fix forward)

Do not revert git history. Instead, push a fix commit and let release-please create a patch release:

```bash
git commit -m "fix(speckit-pro): correct <description of the issue>"
git push origin main
```

release-please will pick up the `fix:` commit and create a patch version bump PR (e.g., `1.1.0` → `1.1.1`). Merge that PR to publish the corrected release.

---

### Scenario 4: `enforce_admins` drift blocks marketplace sync push

**Symptom:** The marketplace sync `git push` in the Release workflow fails with a 403 "Protected branch" error, even though `GITHUB_TOKEN` has `contents: write` permissions in `release.yml`.

**Detection:**
```bash
gh api /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection \
  --jq '.enforce_admins.enabled'
```

If the output is `true`, `enforce_admins` was accidentally enabled via the GitHub UI (Settings → Branches → Edit protection rule → "Do not allow bypassing the above settings").

**Recovery:** Re-run the Stage 1 branch protection setup command from `docs/ai/specs/cicd-release-pipeline-verification.md`. The `PUT` endpoint is a full overwrite and resets `enforce_admins: false`. Then re-trigger the Release workflow (Scenario 1).

---

### Scenario 5: Missing `permissions: contents: write` blocks marketplace sync push

**Symptom:** The marketplace sync `git push` fails with 403, AND `enforce_admins.enabled` is confirmed `false` (Scenario 4 detection returns `false`).

**Detection:**
```bash
gh api /repos/racecraft-lab/racecraft-plugins-public/contents/.github/workflows/release.yml \
  --jq '.content' | base64 -d | grep -A3 'permissions'
```

If the `permissions: contents: write` block is absent from the output, the write scope was removed from `release.yml`.

**Recovery:** Restore the `permissions:` block to `.github/workflows/release.yml`:
```yaml
permissions:
  contents: write
  pull-requests: write
```

Commit as `fix: restore contents write permission in release workflow` and push. Then re-trigger the Release workflow (Scenario 1).

---

### Scenario 6: No releasable commits — release-please PR never appears / stale marketplace.json

**Symptom A: No release-please PR appears within 30 minutes of a feature PR merge.**

Check whether release-please ran but found no releasable commits: navigate to Actions → Release → most recent run → expand the release-please step. If the log says no changes detected, there are no `fix:`, `feat:`, or breaking-change commits since the last release (`chore:` and `docs:` commits alone do not trigger a release).

**Recovery:**
```bash
git commit --allow-empty -m "fix: trigger release for speckit-pro"
git push origin main
```

This can be combined with `Release-As:` if a specific version is needed (see Scenario 2).

**Symptom B: Release workflow is green but `marketplace.json` still shows old versions.**

**Detection:**
```bash
gh api /repos/racecraft-lab/racecraft-plugins-public/contents/.claude-plugin/marketplace.json \
  --jq '.content' | base64 -d
```

Compare the version values against the GitHub Release tags. If they do not match, re-trigger the sync (Scenario 1). If re-triggering also fails, manually edit `.claude-plugin/marketplace.json` and push directly to `main`:

```bash
# Edit .claude-plugin/marketplace.json to set correct versions, then:
git add .claude-plugin/marketplace.json
git commit -m "chore: sync marketplace.json versions [skip ci]"
git push origin main
```
