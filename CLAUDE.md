# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. Shared agent guidance — including the four working rules — lives in [AGENTS.md](AGENTS.md) and is imported below; this file adds the Claude-Code-specific depth.

@AGENTS.md

<!-- SPECKIT START -->
No active SpecKit implementation plan is selected. XPLAT-010 merged through PRs #311-#328 and is archived in `.specify/memory/archive-reports/2026-07-11-xplat-010-post-merge-hygiene.md`. Repository validation is Python 3.11+ and manifest-driven; Bash is confined to bounded GitHub workflow dispatch glue and the fixed release-excluded vendored `.specify/**` allowlist. T108/T117 hosted evidence is complete. Public native Windows/macOS/Linux claims remain blocked by the preserved XPLAT-008 operator UAT matrix.
<!-- SPECKIT END -->

## Start Here

- **Marketplace registry:** `.claude-plugin/marketplace.json` (must be updated when adding a plugin)
- **Release config:** `release-please-config.json` + `.release-please-manifest.json` (kept in sync; see "Adding a New Plugin to Release Automation" below)
- **Pipeline verification runbook:** `docs/ai/specs/cicd-release-pipeline-verification.md` (authoritative for branch-protection, release-please, and docs deploy setup)
- **Per-plugin entry:** `<plugin>/.claude-plugin/plugin.json` (name, version, description)
- **Repo-local gate runner:** `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/run-default-suite.json` (see "Running Tests")

## What This Repo Is

A **Claude Code plugin marketplace** containing public plugins for spec-driven development. Plugins are installed via:
```bash
/plugin marketplace add racecraft-lab/racecraft-plugins-public
/plugin install speckit-pro@racecraft-plugins-public
```

Changes land through a squash-merged PR (`main` is protected), and release-please publishes the release. Consumers then update with:
```bash
# In Claude Code:
/plugin marketplace update racecraft-plugins-public
```

## Plugin Architecture

Each plugin lives in its own top-level directory with this structure:
```
plugin-name/
├── .claude-plugin/plugin.json   ← Manifest (name, version, description, author)
├── agents/                      ← Subagent definitions (.md files)
├── commands/                    ← Slash commands (.md files with YAML frontmatter)
├── hooks/hooks.json             ← Event hooks (SessionStart, etc.)
└── skills/                      ← Skills with SKILL.md + optional references/ and scripts/
```

The marketplace registry is at `.claude-plugin/marketplace.json`. Adding a new plugin requires updating this file.

**The test suite is NOT inside the plugin directory.** Plugin install (both Claude
Code and Codex) copies the entire plugin directory to every consumer, and neither
supports a file-exclusion mechanism — so anything under `<plugin>/` ships. To keep
the test suite out of consumers' installs, it lives at the repo root in
`tests/<plugin>/` (e.g. `tests/speckit-pro/`), a sibling of the plugin. The
`validate-plugin-payload` Layer-1 check fails if `tests/`, `specs/`, or `.process/`
ever reappear under the plugin dir.

### Command File Format
Commands must have YAML frontmatter (`---`) with `description:` and `allowed-tools:` fields, followed by body content. No frontmatter = test failure.

### Skill Structure
Skills live under `skills/<skill-name>/` with a `SKILL.md` entry point. Supporting reference docs go in `references/` and helper scripts (Python — shipped payloads carry no Bash) in `scripts/`.

## Running Tests

The repo-local gate entrypoints use the Python 3.11+ standard-library runner.
Run from the repository root:

```bash
# Default deterministic suite gate
python3 tests/speckit-pro/run-all.py

# Toolchain preflight
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/run-toolchain-preflight.json

# Single deterministic layer
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/run-layer.json

# Active no-shell/no-jq guard
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/active-path-guard.json

# Payload/install/release readiness fixture gates
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/test-payload-evidence.json
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/install-verification.json
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/release-readiness.json
```

Historical Bash behavior is preserved as data-only baselines and git history,
not executable repository tooling. Tracked `.sh` files are limited to the fixed
vendored `.specify/**` allowlist and are excluded from release readiness.

### Test Layers
| Layer | What it tests | Cost |
|-------|---------------|------|
| 1 – Structural | File existence, JSON validity, frontmatter format | Fast |
| 2 – Trigger | Skill trigger accuracy via eval harness | Slow (AI) |
| 3 – Functional | End-to-end skill behavior evals | Slow (AI) |
| 4 – Unit Tests | Python unit and contract tests for repository helpers, validators, and runner behavior | Fast |
| 5 – Tool scoping | Agent tool list restrictions | Fast |
| 6 – Efficiency | Agent model/effort cost-quality benchmarks | Slow (AI) |
| 7 – Integration | Multi-agent dispatch graph (Class 1 dispatch / Class 2 return-format / Class 3 e2e). Replay mode is free; live mode runs `claude -p` and costs LLM tokens. | Fast (replay) / Slow (live) |

Layer 2/3 evals require `skill-creator` plugin at `$SKILL_CREATOR_ROOT` (default: `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator`). Layers 2, 3, and 6 all require `claude -p` and are developer-local only.

Layer 6 evals use `python3 tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py` and require `claude -p`.

Layer 7 fixtures live under `tests/speckit-pro/layer7-integration/`. Replay mode parses committed `transcript.jsonl` files (parser regression test); `--live` mode invokes `claude -p` and captures fresh transcripts (real routing test). See `tests/speckit-pro/layer7-integration/README.md` for fixture format and assertion philosophy.

Layer 8 parity fixtures (`tests/speckit-pro/layer8-parity/`) verify Path A (Agent Teams) vs Path B (parallel-subagents fallback) produce equivalent outcomes. Run modes:
- `python3 tests/speckit-pro/layer8-parity/run-parity-fixtures.py --dry-run` — validates fixture structure only; free.
- `python3 tests/speckit-pro/layer8-parity/run-parity-fixtures.py --live --budget-usd 25` — invokes `claude -p` twice per fixture (once per env) with budget cap and runs tolerance comparison (`byte-identical`, `exact`, `tolerance-1`). `semantic-equivalent` tolerance currently skips with a warning (needs LLM judge in a follow-up). Cost: ~$10-30 per fixture pair.

## speckit-pro Plugin

The only current plugin. It implements Spec-Driven Development (SDD) powered by [GitHub SpecKit](https://github.com/github/spec-kit).

**Key dependency:** The `specify` CLI must be installed for the plugin to function:
```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

The SessionStart hook warns if `specify` is not found.

**Skills:** All invocations use the skill name directly (e.g., `skills/speckit-install/` → `/speckit-pro:speckit-install`). There are no `commands/` files.

- `speckit-install` — first-time SpecKit setup. Bootstraps the `specify` CLI, runs `specify init` / `specify integration install`, and optionally installs the curated extension set.
- `speckit-upgrade` — safely upgrade an existing install with backup-and-restore. Handles the v0.8.13 slash-command → skills migration.
- `speckit-scaffold-spec` — scaffold a spec from the technical roadmap for autopilot execution.
- `speckit-autopilot` — autonomous 7-phase SDD workflow executor with multi-agent consensus. `user-invocable: true`; references in `references/` cover gate validation, consensus protocol, phase execution, TDD, and post-implementation.
- `speckit-coach` — SDD methodology coaching. References cover command guide, constitution guide, presets/extensions, checklist domains, best practices, and getting-started templates.
- `speckit-status` — roadmap dashboard: completed, in-progress, blocked, and ready-to-start specs with phase-level detail.
- `speckit-resolve-pr` — address all unresolved GitHub review comments, fix code, and mark threads resolved.
- `grill-me` — relentless one-question-at-a-time design interview producing a Design Concept doc (invoked as `/speckit-pro:grill-me`).

### Adding a Skill to speckit-pro

1. Create `speckit-pro/skills/<skill-name>/SKILL.md` with YAML frontmatter (`name`, `description`, `license`). Add `references/` and `scripts/` only if needed.
2. If the skill has a Codex counterpart, mirror it under `speckit-pro/codex-skills/<skill-name>/SKILL.md` and ensure `python3 tests/speckit-pro/layer1-structural/validate-codex-skills.py` still passes.
3. Run `python3 tests/speckit-pro/run-all.py --layer 1` to confirm structural validation passes.
4. No `marketplace.json` or `release-please-config.json` edits are required for a new skill within an existing plugin — those files track plugins, not skills.
5. Commit as `feat(speckit-pro): add <skill-name> skill` so release-please promotes it on the next release PR.

## Tooling

- **Runtime:** Python 3.11+ standard-library runner and manifest-driven repository test tooling; no active Bash or `jq` runtime dependency
- **Release automation:** `googleapis/release-please-action@v5`
- **CI:** GitHub Actions with bounded shell dispatch that invokes Python gates
- **PR / repo ops:** GitHub CLI (`gh`) v2+

For per-feature history, see `git log` and `CHANGELOG.md` — don't maintain a duplicate list here.

## Contributing & Branching Strategy

Feature branches use the naming convention `NNN-feature-name` where `NNN` is a zero-padded three-digit spec number (e.g., `004-integration-verification`).

**PR title requirements:** All PR titles MUST follow the [Conventional Commits](https://www.conventionalcommits.org/) format, with a required scope — the release-readiness gate rejects scope-less titles:

```
<type>(<scope>): <description>
```

Valid types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`. Scopes are lowercase letters, digits, and hyphens.

Examples:
- `feat(speckit-pro): add new coaching command`
- `fix(speckit-pro): resolve session timeout`
- `docs(claude-md): update CI/CD sections`
- `chore(release): sync marketplace.json versions`

The `validate-pr-title` CI check enforces this format and will block the PR if the title does not match.

**Audience: write titles and bodies for the public, not for yourself.** The PR page is the public face of this plugin — anyone evaluating it on the marketplace can read every title and body. Three rules ride alongside the conventional-commits format:

1. **The text after the prefix must be plain English.** Drop internal codes (`B1`, `H4`, `WS-D1`), internal layer numbers (`L4`, `L8`), and internal jargon (`tolerance arm`, `mock-shim`, `consensus-synthesizer`). A reader who has never seen this repo should understand the title at a glance.
2. **Plain English does NOT mean dropping the prefix.** `validate-pr-title` will fail in CI if the conventional-commits prefix is missing. The shape is always `<type>(<scope>): <plain-English description>` — keep the prefix, rewrite only what comes after the colon.
3. **PR bodies follow the same rule.** Internal IDs and codes belong in the issue tracker or commit trailers, not in the body. Lead with what the change does and why anyone should care; put verification details below. If a body references prior internal work, link to it rather than naming it by code.

```
Good:  feat(speckit-pro): teach the parity test to compare specific table cells
Bad:   feat(speckit-pro): WS-D1 / L8 — section-extractor implementation for tolerance arm
Bad:   Teach the parity test to compare specific table cells   ← missing prefix, CI fails
```

If a PR ever lands on `main` with a non-public-readable title (squash merges use the PR title as the commit subject), the recovery is `gh pr edit` on the PR + a CHANGELOG follow-up — not a force-push. Avoid the recovery by writing it right the first time.

**Merge policy:** The repository enforces squash-only merges. Merge commits and rebase merges are disabled. Every PR produces exactly one squash commit on `main`.

**Verification checklist:** Before merging a feature that touches CI workflows or release configuration, follow the end-to-end verification checklist at `docs/ai/specs/cicd-release-pipeline-verification.md` to confirm the pipeline remains functional.

## CI/CD Workflow

The PR Checks workflow (`.github/workflows/pr-checks.yml`) runs on every non-draft PR and can also be dispatched by release automation for release-please PR branches created with `GITHUB_TOKEN`. It contains eight jobs:

| Job | Description |
|-----|-------------|
| `detect` | Emits the current Python-gated plugin matrix. Intentionally fixed to `["speckit-pro"]` for now; selective changed-file matrices are deferred until the Python gate owns that decision. |
| `test (<plugin>)` | Dispatches the Python runner toolchain and default-suite gates for each plugin in the matrix. |
| `validate-plugins` | Sentinel/aggregator job. Always runs. Passes when the plugin test matrix passed or was skipped; fails when it failed or was cancelled. Provides the stable check name that branch protection requires. |
| `validate-pr-title` | Validates the PR title against the Conventional Commits pattern. |
| `validate-release-note` | Requires a valid consumer release-note block for releasable feat/fix PRs unless `release-note/skip` applies. |
| `validate-workflows` | Installs pinned actionlint and validates every GitHub Actions workflow. |
| `validate-docs` | Detects docs-site, generated-reference, release metadata, and docs-validation contract changes. Runs full docs validation for rendered docs or docs-contract changes, and reference plus quality validation for generated-reference changes. |
| `artifact-consistency` | Regenerates release artifacts and fails when the checked-in payload, registry, fixture, or evidence mirrors drift from source. |

**Why a sentinel job?** The `test` matrix job name is dynamic (`test (speckit-pro)`, `test (other-plugin)`, etc.) and cannot be registered as a stable required check name. The `validate-plugins` sentinel aggregates matrix results into one stable name that branch protection can require.

**Docs-only PRs:** `detect` emits `["speckit-pro"]` for every non-draft PR, so docs-only PRs still run the Python-dispatched plugin gate suite. If the changed documentation is part of the docs-site, generated-reference, or docs-validation contract surfaces, `validate-docs` also runs the matching docs validation mode.

**Release-please PRs:** GitHub suppresses normal `pull_request` workflow runs for PRs created or updated by `GITHUB_TOKEN`, so the Release workflow dispatches `PR Checks` manually after it syncs generated `dist/**` payloads onto the release PR branch. Those dispatched (`workflow_dispatch`) check runs are visible on the PR but live in a check suite that is **not associated with the PR**, so branch protection does not count them — which is why a `GITHUB_TOKEN`-authored release PR shows `BLOCKED` even with everything green. When the optional `RELEASE_PLEASE_TOKEN` secret is configured (see **Release Process → Release token**), the release PR is authored by that identity instead, its `pull_request` checks run un-gated and satisfy branch protection directly, and the manual dispatch becomes a fallback. Without the secret the workflow falls back to `GITHUB_TOKEN` and behaves as before.

**Container preflight:** `.github/workflows/container-preflight.yml` starts on every PR and manual dispatch so required contexts are never stranded by workflow-level path filters. A lightweight Ubuntu job limits heavy execution to runner, gate, and workflow changes. The stable `container-preflight-linux-amd64` and `container-preflight-linux-arm64` sentinels report success for intentional no-op runs and fail when their matching heavy container job fails. The official GitHub-hosted runners reference lists `windows-2025` as stable and the ARM64 row containing `windows-11-arm` as Public Preview. Windows smoke remains advisory: x64 defaults enabled, ARM64 defaults disabled, and `XPLAT_WINDOWS_X64_ENABLED` / `XPLAT_WINDOWS_ARM64_ENABLED` or manual inputs provide explicit overrides. Uploaded evidence is diagnostic preflight data, not native installed-plugin UAT.

**Maintenance warning:** If a required job in `pr-checks.yml` or `container-preflight.yml` is renamed, the corresponding required status check name in branch protection MUST be updated manually — GitHub does NOT automatically track job renames. The live non-strict rule requires exactly `validate-plugins`, `validate-pr-title`, `validate-release-note`, `container-preflight-linux-amd64`, and `container-preflight-linux-arm64` from GitHub Actions.

To detect drift, run:
```bash
gh api /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection \
  --jq '[.required_status_checks.contexts[]]'
```

Compare the output against the actual required job names in both workflows. Recovery: re-run the Stage 1 branch protection setup command from `docs/ai/specs/cicd-release-pipeline-verification.md` with the corrected check names.

When modifying `.github/workflows/pr-checks.yml`, `.github/workflows/container-preflight.yml`, or `.github/workflows/release.yml`, include a note in the PR description confirming whether CLAUDE.md's CI/CD sections require updates.

## Docs Site Deployment

The Deploy Docs workflow (`.github/workflows/deploy-docs.yml`) publishes the Astro/Starlight docs site to GitHub Pages after `pnpm --dir docs-site validate` succeeds. It uses the manual Pages source setting `GitHub Actions`, the `github-pages` environment, least-privilege Pages permissions, and a fixed staging concurrency group. Keep setup, retry, rollback, deployment-history, and DOC-012 staging-versus-launch details in `docs/ai/specs/cicd-release-pipeline-verification.md` rather than duplicating them here.

## Release Process

Releases are fully automated via [release-please](https://github.com/googleapis/release-please) (`googleapis/release-please-action@v5`), triggered by every push to `main`.

**How it works:**

1. **Conventional commit analysis:** After a PR is squash-merged to `main`, the Release workflow (`.github/workflows/release.yml`) runs. release-please scans new conventional commits and determines whether a release is warranted. Only `fix:`, `feat:`, and breaking-change commits trigger a release PR — `chore:` and `docs:` commits alone do not.

2. **Release PR creation:** When releasable commits exist, release-please opens or updates a PR that bumps `CHANGELOG.md` and the version fields in `speckit-pro/.claude-plugin/plugin.json` and `speckit-pro/.codex-plugin/plugin.json`. Plugin validation, release-readiness, payload synchronization, install-health checks, and active-path guards dispatch Python runner gates.

3. **GitHub Release publication:** When the release PR is merged, release-please creates a GitHub Release with a version tag (e.g., `speckit-pro-v1.2.0`). The workflow captures the raw body and merged-PR metadata in an immutable artifact, then deterministically rewrites the release with consumer Highlights plus the original commit appendix. `CHANGELOG.md` remains release-please's machine ledger.

4. **Post-release consistency check:** After the release publishes (`steps.release.outputs['speckit-pro--release_created'] == 'true'`), the workflow rebuilds `dist/**`, re-syncs marketplace versions, and regenerates the docs reference, then **verifies** that `main` is already consistent — because the release PR (step 2) carried the full sync. It does **not** open a separate sync PR. If it ever detects drift, it fails the workflow so a maintainer can re-run the Release workflow to re-sync the release PR.

5. **End-user update:** Plugin consumers run the following to receive the updated version:
   ```
   /plugin marketplace update racecraft-plugins-public
   ```

**Why the release PR carries the sync:** `main` is protected and this repository lives under the `racecraft-lab` organization, so Release must not direct-push generated changes to `main`. Rather than a second post-release sync PR, the sync (dist, marketplace versions, docs reference) is committed onto the **release PR branch** itself, which already flows through branch protection before a human merges it. The `permissions: actions: write`, `contents: write`, and `pull-requests: write` declarations in `release.yml` remain required so release-please can open/update the release PR, the workflow can push the sync commit onto that branch, and dispatch PR checks.

### Release token (optional, recommended)

By default the Release workflow authenticates as the built-in `GITHUB_TOKEN`.
GitHub holds the `pull_request` checks on any PR authored by `GITHUB_TOKEN` as
`action_required` (a recursion guard), so the release PR's required checks
(`validate-plugins`, `validate-pr-title`) never report against the PR and it
shows `BLOCKED` — only a repo admin can merge past it. To make release PRs
mergeable normally, add a `RELEASE_PLEASE_TOKEN` Actions secret:

1. Create a **fine-grained PAT** (or a GitHub App installation token) scoped to
   this repository with **Contents: Read and write** and **Pull requests: Read
   and write**.
2. Save it under `Settings → Secrets and variables → Actions` as
   `RELEASE_PLEASE_TOKEN`.

`release.yml` reads it as `${{ secrets.RELEASE_PLEASE_TOKEN || github.token }}`
in both the release-please step and the payload-sync checkout, so the release PR
is opened — and its sync commit pushed — by that actor (the git commit author
stays `github-actions[bot]`; what matters for branch protection is that a
non-`GITHUB_TOKEN` actor performed the PR creation and push), and its
`pull_request` checks run un-gated. The secret is optional: when it is absent
`secrets.RELEASE_PLEASE_TOKEN` is empty, so the `||` resolves the expression to
`github.token` and the workflow behaves exactly as before (release PR shows
`BLOCKED`; an admin merges it).

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

**Also update the marketplace sync script** (`scripts/sync-marketplace-versions.py`) if it needs to sync the new plugin's version to `.claude-plugin/marketplace.json`. Verify the script handles the new plugin name, then add the plugin to `.claude-plugin/marketplace.json` as well.

Note: CI will test the new plugin on PRs (if files changed), but release-please will not create a release entry until the plugin is added to `release-please-config.json`. This gap is silent — there is no automated check that validates alignment between plugin directories and release-please config.

## Recovery & Rollback Procedures

All commands below are written for this repository (`racecraft-lab/racecraft-plugins-public`) and require GitHub CLI v2+.

---

### Scenario 1: Re-sync a release PR (or recover from a post-release drift failure)

If a release PR is missing its payload/marketplace/docs-reference sync (e.g., it predates this workflow, or the sync step failed), or the post-release **Verify release artifacts are consistent** step failed:

```bash
gh workflow run release.yml --repo racecraft-lab/racecraft-plugins-public
```

This manually triggers the Release workflow, which re-runs release-please (idempotent) and re-runs the release-PR payload-sync step (rebuild `dist/**` + sync marketplace versions + regenerate the docs reference, committed onto the release PR branch) so the release PR is self-consistent before merge.

---

### Scenario 2: Force a specific version with `Release-As`

To override release-please's inferred version bump and pin a specific version:

```bash
# Touch a file in the target component to scope the footer to that component,
# then add the Release-As footer to the commit message.
git commit -m "chore(speckit-pro): force version

Release-As: 1.2.0" speckit-pro/.claude-plugin/plugin.json
git push origin <release-as-branch>
gh pr create --base main --head <release-as-branch> --title "chore(speckit-pro): force version"
```

The `Release-As: X.Y.Z` footer MUST appear in the git commit trailer (separated from the subject by a blank line). The commit MUST touch at least one file under `speckit-pro/` — a commit that touches no component files will not target any component. The footer overrides the inferred version in the next release-please PR.

---

### Scenario 3: Patch a bad release (fix forward)

Do not revert git history. Instead, push a fix commit and let release-please create a patch release:

```bash
git commit -m "fix(speckit-pro): correct <description of the issue>"
git push origin <fix-branch>
gh pr create --base main --head <fix-branch> --title "fix(speckit-pro): correct <description of the issue>"
```

release-please will pick up the `fix:` commit and create a patch version bump PR (e.g., `1.1.0` → `1.1.1`). Merge that PR to publish the corrected release.

---

### Scenario 4: Post-release consistency check fails (drift detected)

**Symptom:** The Release workflow publishes a GitHub Release, then the `Verify release artifacts are consistent` step fails — a clean rebuild on `main` differs from what was committed, meaning the release PR was merged without the full sync (dist / marketplace versions / docs reference).

**Detection:**
```bash
gh run view <run-id> --log-failed
```

Look for the `Verify release artifacts are consistent` step; its error prints the drifting paths. This usually means the release-PR payload-sync step did not run on the release PR before it was merged (e.g., a release PR created by an older workflow).

**Recovery:** Fix forward — push a sync commit through a normal PR that runs
`python3 scripts/refresh-release-artifacts.py` and
`pnpm --dir docs-site reference:generate`, then commits the generated payload,
marketplace, proof, evidence, and docs-reference changes. For future releases
the release PR carries this sync automatically; use Scenario 1 to re-sync a
release PR before merge.

---

### Scenario 5: Missing release workflow write permissions block the release-PR sync

**Symptom:** The release-PR payload-sync step rebuilds artifacts in the workflow, but fails when pushing the sync commit onto the release PR branch or dispatching PR checks.

**Detection:**
```bash
gh api /repos/racecraft-lab/racecraft-plugins-public/contents/.github/workflows/release.yml \
  --jq '.content' | base64 -d | grep -A3 'permissions'
```

If `actions: write`, `contents: write`, or `pull-requests: write` is absent from the output, a required workflow token permission was removed from `release.yml`.

**Recovery:** Restore the `permissions:` block to `.github/workflows/release.yml`:
```yaml
permissions:
  actions: write
  contents: write
  pull-requests: write
```

Commit as `chore(release): restore release workflow permissions` and push through a PR. Then re-trigger the Release workflow (Scenario 1).

---

### Scenario 6: No releasable commits — release-please PR never appears / stale marketplace.json

**Symptom A: No release-please PR appears within 30 minutes of a feature PR merge.**

Check whether release-please ran but found no releasable commits: navigate to Actions → Release → most recent run → expand the release-please step. If the log says no changes detected, there are no `fix:`, `feat:`, or breaking-change commits since the last release (`chore:` and `docs:` commits alone do not trigger a release).

**Recovery:**
```bash
git commit --allow-empty -m "fix(speckit-pro): trigger release"
git push origin <release-trigger-branch>
gh pr create --base main --head <release-trigger-branch> --title "fix(speckit-pro): trigger release"
```

This can be combined with `Release-As:` if a specific version is needed (see Scenario 2).

**Symptom B: Release workflow is green but `marketplace.json` still shows old versions.**

**Detection:**
```bash
gh api /repos/racecraft-lab/racecraft-plugins-public/contents/.claude-plugin/marketplace.json \
  --jq '.content' | base64 -d
```

Compare the version values against the GitHub Release tags. If they do not match, re-trigger the sync (Scenario 1). If re-triggering also fails, manually rebuild payloads, sync marketplace files, and open a PR:

```bash
python3 scripts/refresh-release-artifacts.py
pnpm --dir docs-site reference:generate
git add dist .claude-plugin/marketplace.json .agents/plugins/marketplace.json docs-site/src/content/docs/reference
git commit -m "chore(release): sync plugin payloads, marketplace versions, and docs reference"
git push origin <sync-branch>
gh pr create --base main --head <sync-branch> --title "chore(release): sync plugin payloads and marketplace versions"
```

---

### Scenario 7: A required Linux container preflight blocks PRs

**Symptom:** Open speckit-pro PRs show a red
`container-preflight-linux-amd64` or `container-preflight-linux-arm64` required
check. The corresponding heavy job runs the Python toolchain preflight, default
suite, release readiness, and artifact capture inside the pinned container.

**Detection:**
```bash
gh run view <run-id> --log-failed
```
Inspect the failed heavy-job step and its uploaded artifact. Distinguish a
deterministic suite/release-readiness failure from a transient image or Actions
infrastructure failure before changing code.

**Recovery:**
1. **Transient infrastructure failure:** re-run failed jobs with
   `gh run rerun <run-id> --failed`; no source change is needed.
2. **Deterministic suite or readiness failure:** reproduce the named Python
   command locally, fix the source or generated-artifact drift, and land it
   through a normal PR.
3. **Runner-image contract change:** update the pinned container workflow and
   its Python validators together. Do not demote either required sentinel or
   use an admin override as a routine workaround.

## Active Technologies
The entries below are historical spec snapshots. They do not override the
current Python 3.11+ commands and Bash-confinement rules at the top of this file.
- Bash 4+ shell scripts, Markdown skills, YAML manifests, JSON Schema 2020-12 contracts, and `bash`, `jq`, `git`, `gh` at PR-emission boundaries (prsg-010-harden-the-hatch)
- Repository files only: feature artifacts, contract schemas, workflow state JSON, and generated re-slicing packets (prsg-010-harden-the-hatch)
- Bash 4+ shell scripts, Markdown skill guidance, JSON Schema 2020-12 + `bash`, `jq`, `git`, `gh` at PR-emission boundaries, existing SpecKit Pro shell harness (prsg-013-reviewability-markers)
- Repository files only: `autopilot-state.json`, workflow evidence blocks, JSON contract schemas, and generated PR packet artifacts (prsg-013-reviewability-markers)
- Bash scripts with Markdown skill/operator guidance + `bash`, `jq`, `git`, `gh`; optional `gh stack` GitHub CLI extension via `github/gh-stack` (prsg-014-optional-gh-stack-stack-manager-integration)
- JSON evidence under feature `.process/` directories, `.process/prs.json`, `autopilot-state.json`, command logs, PR packet artifacts, and local `gh-stack` metadata outside the repo when the extension is used (prsg-014-optional-gh-stack-stack-manager-integration)
- Markdown/MDX content plus Astro/Starlight docs site metadata + Astro 6.4.6, Starlight 0.40.0, pnpm 10.25.0 (doc-004-codex-marketplace-installation-path)
- Docs-site JavaScript ESM on Node; Astro 6.4.6 and Starlight 0.40.0 for docs rendering; Node built-ins (`node:fs`, `node:path`, `node:url`) plus existing docs-site pnpm scripts and `starlight-links-validator`; no new runtime dependency planned. (doc-007-command-workflow-manifest-and-file-layout-reference)
- Checked-in Markdown files under `docs-site/src/content/docs/reference/`; no database or browser storage. (doc-007-command-workflow-manifest-and-file-layout-reference)
- Historical pre-XPLAT snapshot: Markdown runtime guidance, TOML Codex agent templates, YAML metadata, generated payload files, and the then-current Bash validation and payload tooling. Those commands were retired by XPLAT-009/XPLAT-010. (tacd-002-capability-discovery-directive-and-agent-updates)
- Repository files only. Source guidance under `speckit-pro/`, generated payload copies under `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`, and Plan-phase artifacts under `specs/tacd-002-capability-discovery-directive-and-agent-updates/`. (tacd-002-capability-discovery-directive-and-agent-updates)
- Docs-site JavaScript ESM on Node, with Markdown/MDX content under `docs-site/src/content/docs/` + Astro 6.4.6, Starlight 0.40.0, existing `starlight-links-validator` (doc-008-troubleshooting-security-trust-update-rollback)
- Checked-in Markdown/MDX files only; no database, browser storage, or runtime state (doc-008-troubleshooting-security-trust-update-rollback)
- JavaScript ESM on Node.js for docs-site scripts; Astro 6.4.6 and Starlight 0.40.0 in `docs-site/`; pnpm 10.25.0 scoped with `pnpm --dir docs-site ...` + Existing `astro`, `@astrojs/starlight`, `@astrojs/check`, `starlight-links-validator`; add minimal Playwright dev dependency only for `validate:smoke` (doc-010-search-accessibility-deep-links-docs-validation)
- Checked-in Markdown, Astro components, package scripts, generated reference files, and CI artifacts only; no database or browser storage (doc-010-search-accessibility-deep-links-docs-validation)
- Docs-site JavaScript ESM on Node >=22.12; GitHub Actions YAML; Markdown operator guidance + Astro 6.4.6, Starlight 0.40.0, `@astrojs/check`, `starlight-links-validator`, Playwright 1.61.0, pnpm 10.25.0 via Corepack, standard GitHub Pages Actions (doc-011-github-pages-build-and-deploy-pipeline)
- Checked-in repository files only; GitHub Pages stores the uploaded `docs-site/dist` static artifact outside repository source control (doc-011-github-pages-build-and-deploy-pipeline)
- Python 3.11+ standard library through `speckit-pro/speckit_pro_runner/` + Existing XPLAT-004 runner envelope, diagnostics, typed path, runtime-info, and preflight primitives; current Bash helper scripts remain temporary source-checkout references only (xplat-005-read-only-helper-port)
- Checked-in fixture, contract, and evidence files only; ported helpers must not write repository or user-local state (xplat-005-read-only-helper-port)
- Python 3.11+ standard library through `speckit-pro/speckit_pro_runner/` + Existing runner envelope, diagnostics, typed path, subprocess fixture, helper registry, XPLAT-005 read-only helper records, and XPLAT-006 mutation/install/PR-emission contracts; no new runtime dependency (codex/xplat-007-python-tooling-and-release-gate-migration)
- Checked-in source files, fixtures, JSON schemas, runner metadata, test payload evidence under fixture or temporary output roots; no database (codex/xplat-007-python-tooling-and-release-gate-migration)

## Recent Changes
- prsg-010-harden-the-hatch: Added PRSG-010 foundation artifacts, contract schemas, workflow state updates, and planning docs for the split PR stack.
