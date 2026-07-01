# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

<!-- SPECKIT START -->
No active SpecKit implementation plan is selected. DOC-014 shipped via PR #264 and is archived into `.specify/memory/`; inspect current workflow state under `docs/ai/specs/.process/`, active `specs/**` directories, and `.specify/memory/archive-reports/` before starting new scaffold or cleanup work.
<!-- SPECKIT END -->

## Working in This Repo

Four rules, in priority order. These exist because plugin/marketplace edits have high blast radius (every install consumer gets the change on `/plugin marketplace update`) and most defects here come from doing too much, not too little.

### 1. Surface assumptions before editing
- State them in chat before touching files. If a plugin manifest, release config, or CI workflow change is ambiguous, ask — don't infer.
- If a request has multiple reasonable interpretations (e.g., "fix the release" could mean bump version, re-trigger workflow, or patch the script), list them and let the user pick.
- If a simpler approach exists (e.g., a `chore:` empty commit vs. a code change), say so before implementing the larger one.

### 2. Simplest change that solves it
- No new abstractions for one-call-site code. No new test layers, scripts, or helpers unless a second use exists or is explicitly asked for.
- No flags/options "for future flexibility" — add them when a second caller actually appears.
- For shell scripts under `speckit-pro/scripts/` and `tests/speckit-pro/`, prefer plain `bash` + `jq` over introducing a new dependency.

### 3. Surgical edits
- Touch only what the request requires. Don't reformat adjacent JSON, reorder keys in `plugin.json` / `marketplace.json`, or "clean up" comments you didn't author.
- When editing one plugin's files, don't drift into another plugin's files unless the task explicitly spans them.
- Remove only the imports/blocks your change orphans — leave pre-existing dead code alone (mention it, don't delete it).
- Match existing style in shell scripts, YAML, and Markdown even if you'd write it differently.

### 4. Verifiable success criteria
- Translate every task into a check before coding: "edit X" → "after edit, `bash tests/speckit-pro/run-all.sh --layer 1` passes" or "`gh pr view <N>` shows green".
- For workflow / release changes, the success check is "the next release PR from release-please reflects this" — say that out loud before editing.
- For multi-step work, list the steps + their verification commands up front, then loop on them.

Tradeoff: these bias toward caution over speed. For a one-line `chore:` edit, use judgment.

## Start Here

- **Marketplace registry:** `.claude-plugin/marketplace.json` (must be updated when adding a plugin)
- **Release config:** `release-please-config.json` + `.release-please-manifest.json` (kept in sync; see "Adding a New Plugin to Release Automation" below)
- **Pipeline verification runbook:** `docs/ai/specs/cicd-release-pipeline-verification.md` (authoritative for branch-protection, release-please, and docs deploy setup)
- **Per-plugin entry:** `<plugin>/.claude-plugin/plugin.json` (name, version, description)
- **Test runner:** `tests/<plugin>/run-all.sh` (see "Running Tests") — lives at the repo root, outside the plugin dir, so it is not shipped to consumers

## What This Repo Is

A **Claude Code plugin marketplace** containing public plugins for spec-driven development. Plugins are installed via:
```bash
/plugin marketplace add racecraft-lab/racecraft-plugins-public
/plugin install speckit-pro@racecraft-plugins-public
```

After making changes, publish with:
```bash
git add . && git commit -m "Description" && git push
# Then in Claude Code:
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
the 5-layer suite out of consumers' installs, it lives at the repo root in
`tests/<plugin>/` (e.g. `tests/speckit-pro/`), a sibling of the plugin. The
`validate-plugin-payload` Layer-1 check fails if `tests/`, `specs/`, or `.process/`
ever reappear under the plugin dir.

### Command File Format
Commands must have YAML frontmatter (`---`) with `description:` and `allowed-tools:` fields, followed by body content. No frontmatter = test failure.

### Skill Structure
Skills live under `skills/<skill-name>/` with a `SKILL.md` entry point. Supporting reference docs go in `references/` and shell scripts in `scripts/`.

## Running Tests

All tests are shell scripts. Run from the repository root:

```bash
# Default: Layers 1, 4, 5 (fast, deterministic)
bash tests/speckit-pro/run-all.sh

# With live SpecKit project tests
bash tests/speckit-pro/run-all.sh --live

# Single layer
bash tests/speckit-pro/run-all.sh --layer 1   # Structural validation
bash tests/speckit-pro/run-all.sh --layer 4   # Script unit tests
bash tests/speckit-pro/run-all.sh --layer 5   # Agent tool scoping

# Layers 2 & 3 (AI evals — require skill-creator plugin and claude -p)
bash tests/speckit-pro/layer2-trigger/run-trigger-evals.sh speckit-coach
bash tests/speckit-pro/layer2-trigger/run-trigger-evals.sh speckit-autopilot

# Layer 7 — multi-agent dispatch graph (replay = free, live = $$)
bash tests/speckit-pro/run-all.sh --integration         # all 3 classes, replay
bash tests/speckit-pro/run-all.sh --integration --live  # all 3 classes, live
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
| 7 – Integration | Multi-agent dispatch graph (Class 1 dispatch / Class 2 return-format / Class 3 e2e). Replay mode is free; live mode runs `claude -p` and costs LLM tokens. | Fast (replay) / Slow (live) |

Layer 2/3 evals require `skill-creator` plugin at `$SKILL_CREATOR_ROOT` (default: `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator`). Layers 2, 3, and 6 all require `claude -p` and are developer-local only.

Layer 6 evals use `tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.sh` and require `claude -p`.

Layer 7 fixtures live under `tests/speckit-pro/layer7-integration/`. Replay mode parses committed `transcript.jsonl` files (parser regression test); `--live` mode invokes `claude -p` and captures fresh transcripts (real routing test). See `tests/speckit-pro/layer7-integration/README.md` for fixture format and assertion philosophy.

Layer 8 parity fixtures (`tests/speckit-pro/layer8-parity/`) verify Path A (Agent Teams) vs Path B (parallel-subagents fallback) produce equivalent outcomes. Run modes:
- `bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run` — validates fixture structure only; free.
- `bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --live --budget-usd 25` — invokes `claude -p` twice per fixture (once per env) with budget cap and runs tolerance comparison (`byte-identical`, `exact`, `tolerance-1`). `semantic-equivalent` tolerance currently skips with a warning (needs LLM judge in a follow-up). Cost: ~$10-30 per fixture pair.

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
2. If the skill has a Codex counterpart, mirror it under `speckit-pro/codex-skills/<skill-name>/SKILL.md` and ensure `tests/speckit-pro/layer1-structural/validate-codex-skills.sh` still passes.
3. Run `bash tests/speckit-pro/run-all.sh --layer 1` to confirm structural validation passes.
4. No `marketplace.json` or `release-please-config.json` edits are required for a new skill within an existing plugin — those files track plugins, not skills.
5. Commit as `feat(speckit-pro): add <skill-name> skill` so release-please promotes it on the next release PR.

## Tooling

- **Runtime:** Bash (macOS/Linux), `jq` for JSON
- **Release automation:** `googleapis/release-please-action@v5`
- **CI:** GitHub Actions (`actions/checkout@v4`, inline Bash)
- **PR / repo ops:** GitHub CLI (`gh`) v2+

For per-feature history, see `git log` and `CHANGELOG.md` — don't maintain a duplicate list here.

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

The PR Checks workflow (`.github/workflows/pr-checks.yml`) runs on every non-draft PR and can also be dispatched by release automation for release-please PR branches created with `GITHUB_TOKEN`. It contains five jobs:

| Job | Description |
|-----|-------------|
| `detect` | Detects which plugins changed relative to the base branch — a plugin counts as changed when either its own directory (`<plugin>/`) or its out-of-plugin test suite (`tests/<plugin>/`) changed. Outputs a JSON array of plugin names. |
| `test (<plugin>)` | Runs `bash tests/<plugin>/run-all.sh` for each changed plugin (e.g. `test (speckit-pro)`). The name is dynamic — one job per plugin in the matrix. Skipped only when neither the plugin nor its `tests/<plugin>/` suite changed (e.g. docs-only PRs). |
| `test latest jq (speckit-pro)` | Runs `tests/speckit-pro/run-all.sh` against the latest upstream `jq` release (downloaded and SHA-256-verified against the release API digest) to catch parser/regression drift before the runner image's `jq` updates. Runs only when `speckit-pro` is in `detect`'s output; skipped on docs-only PRs. **Note:** because it downloads from `api.github.com`/`jqlang/jq`, an upstream asset rename, a missing digest, or a network/API outage fails this leg — and, via the sentinel, blocks every speckit-pro PR until resolved (see Recovery → Scenario 7). |
| `validate-plugins` | Sentinel/aggregator job. Always runs. Passes when both the `test` matrix and the `test latest jq` leg passed or were skipped; fails when either failed or was cancelled. Provides the stable check name that branch protection requires. |
| `validate-pr-title` | Validates the PR title against the Conventional Commits pattern. |
| `validate-docs` | Detects docs-site, generated-reference, release metadata, and docs-validation contract changes. Runs full docs validation for rendered docs or docs-contract changes, and reference plus quality validation for generated-reference changes. |

**Why a sentinel job?** The `test` matrix job name is dynamic (`test (speckit-pro)`, `test (other-plugin)`, etc.) and cannot be registered as a stable required check name. The `validate-plugins` sentinel aggregates all matrix results — plus the `test latest jq` leg — into one stable name that branch protection can require.

**Docs-only PRs:** When a PR touches only documentation (no plugin directory and no `tests/<plugin>/` suite), `detect` outputs `[]`, `test` is skipped (job-level `if:` evaluates to false — GitHub treats a skipped job as passing, not pending), and `validate-plugins` also passes. Docs-only PRs are not blocked by the test matrix. If the changed documentation is part of the docs-site, generated-reference, or docs-validation contract surfaces, `validate-docs` runs the matching docs validation mode.

**Release-please PRs:** GitHub suppresses normal `pull_request` workflow runs for PRs created or updated by `GITHUB_TOKEN`, so the Release workflow dispatches `PR Checks` manually after it syncs generated `dist/**` payloads onto the release PR branch. Those dispatched (`workflow_dispatch`) check runs are visible on the PR but live in a check suite that is **not associated with the PR**, so branch protection does not count them — which is why a `GITHUB_TOKEN`-authored release PR shows `BLOCKED` even with everything green. When the optional `RELEASE_PLEASE_TOKEN` secret is configured (see **Release Process → Release token**), the release PR is authored by that identity instead, its `pull_request` checks run un-gated and satisfy branch protection directly, and the manual dispatch becomes a fallback. Without the secret the workflow falls back to `GITHUB_TOKEN` and behaves as before.

**Maintenance warning:** If any job in `pr-checks.yml` is renamed, the corresponding required status check name in branch protection MUST be updated manually — GitHub does NOT automatically track job renames. A stale check name silently degrades protection: the renamed check never reports, the branch protection rule becomes vacuous, and PRs become mergeable without the check passing.

To detect drift, run:
```bash
gh api /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection \
  --jq '[.required_status_checks.contexts[]]'
```

Compare the output against the actual job names in `pr-checks.yml`. Recovery: re-run the Stage 1 branch protection setup command from `docs/ai/specs/cicd-release-pipeline-verification.md` with the corrected check names.

When modifying `.github/workflows/pr-checks.yml` or `.github/workflows/release.yml`, include a note in the PR description confirming whether CLAUDE.md's CI/CD sections require updates.

## Docs Site Deployment

The Deploy Docs workflow (`.github/workflows/deploy-docs.yml`) publishes the Astro/Starlight docs site to GitHub Pages after `pnpm --dir docs-site validate` succeeds. It uses the manual Pages source setting `GitHub Actions`, the `github-pages` environment, least-privilege Pages permissions, and a fixed staging concurrency group. Keep setup, retry, rollback, deployment-history, and DOC-012 staging-versus-launch details in `docs/ai/specs/cicd-release-pipeline-verification.md` rather than duplicating them here.

## Release Process

Releases are fully automated via [release-please](https://github.com/googleapis/release-please) (`googleapis/release-please-action@v5`), triggered by every push to `main`.

**How it works:**

1. **Conventional commit analysis:** After a PR is squash-merged to `main`, the Release workflow (`.github/workflows/release.yml`) runs. release-please scans new conventional commits and determines whether a release is warranted. Only `fix:`, `feat:`, and breaking-change commits trigger a release PR — `chore:` and `docs:` commits alone do not.

2. **Release PR creation:** When releasable commits exist, release-please opens or updates a PR that bumps `CHANGELOG.md` and the version fields in `speckit-pro/.claude-plugin/plugin.json` and `speckit-pro/.codex-plugin/plugin.json`. The Release workflow then checks out the release PR branch, rebuilds generated `dist/**` payload files, syncs the `marketplace.json` versions (`scripts/sync-marketplace-versions.sh`), regenerates the docs reference (`pnpm --dir docs-site reference:generate`), commits them back to that branch when needed, and dispatches `PR Checks` for the branch. This keeps the release PR **fully self-consistent** — source, dist, marketplace, and docs reference all at the new version — so **merging the release PR completes the release with no follow-up sync PR**.

3. **GitHub Release publication:** When the release PR is merged, release-please creates a GitHub Release with a version tag (e.g., `speckit-pro-v1.2.0`).

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

**Also update the marketplace sync script** (`scripts/sync-marketplace-versions.sh`) if it needs to sync the new plugin's version to `.claude-plugin/marketplace.json`. Verify the script handles the new plugin name, then add the plugin to `.claude-plugin/marketplace.json` as well.

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
git commit -m "chore: force speckit-pro version

Release-As: 1.2.0" speckit-pro/.claude-plugin/plugin.json
git push origin <release-as-branch>
gh pr create --base main --head <release-as-branch> --title "chore: force speckit-pro version"
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

**Recovery:** Fix forward — push a sync commit through a normal PR that runs `bash scripts/build-plugin-payloads.sh`, `bash scripts/sync-marketplace-versions.sh`, and `pnpm --dir docs-site reference:generate`, then commits `dist/`, both `marketplace.json` files, and `docs-site/src/content/docs/reference/**`. For future releases the release PR carries this sync automatically; use Scenario 1 to re-sync a release PR before merge.

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
git commit --allow-empty -m "fix: trigger release for speckit-pro"
git push origin <release-trigger-branch>
gh pr create --base main --head <release-trigger-branch> --title "fix: trigger release for speckit-pro"
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
bash scripts/build-plugin-payloads.sh
bash scripts/sync-marketplace-versions.sh
pnpm --dir docs-site reference:generate
git add dist .claude-plugin/marketplace.json .agents/plugins/marketplace.json docs-site/src/content/docs/reference
git commit -m "chore: sync plugin payloads, marketplace versions, and docs reference"
git push origin <sync-branch>
gh pr create --base main --head <sync-branch> --title "chore: sync plugin payloads and marketplace versions"
```

---

### Scenario 7: The `test latest jq` leg blocks PRs for upstream reasons

**Symptom:** Open speckit-pro PRs show `validate-plugins` failing (and a red `test latest jq (speckit-pro)` check) even though the PR's own code is fine. Because the latest-`jq` leg is wired into the `validate-plugins` sentinel, an upstream or infrastructure failure here blocks **every** speckit-pro PR, not just one.

**Detection:**
```bash
gh run view <run-id> --log-failed
```
Look at the `Install latest jq release` step. Common upstream causes:
- `jqlang/jq` renamed or dropped the `jq-linux-amd64` release asset (`latest jq release did not include jq-linux-amd64`).
- The latest release asset has no `digest` field (`latest jq release asset is missing a sha256 digest`).
- `api.github.com` was unreachable or rate-limited at run time.

**Recovery:**
1. **Transient (network/API):** re-run the failed jobs — `gh run rerun <run-id> --failed`. No code change needed.
2. **Upstream asset/digest change:** this is a real workflow fix, not a per-PR fix. Update the `test-latest-jq` job in `.github/workflows/pr-checks.yml` to the new asset name (and the `validate-pr-checks-sentinel.sh` assertions if the digest handling changes), land it through a normal PR, then re-run the blocked PRs' checks.
3. **Emergency unblock:** if a maintainer must merge before the upstream fix lands, temporarily relax the sentinel — drop `test-latest-jq` from `needs:` and the `latest_jq_result` check in `validate-plugins` — or merge via admin override, then restore the gate in a follow-up. Treat this as a stopgap, not a permanent state, so drift between `pr-checks.yml` and the required-check name does not accumulate (see the **Maintenance warning** above).

If this leg proves flaky enough to disrupt the merge queue, consider demoting it to advisory (`continue-on-error: true` and out of the sentinel `needs:`) so it still surfaces `jq` drift without gating merges.

## Active Technologies
- Bash 4+ shell scripts, Markdown skills, YAML manifests, JSON Schema 2020-12 contracts, and `bash`, `jq`, `git`, `gh` at PR-emission boundaries (prsg-010-harden-the-hatch)
- Repository files only: feature artifacts, contract schemas, workflow state JSON, and generated re-slicing packets (prsg-010-harden-the-hatch)
- Bash 4+ shell scripts, Markdown skill guidance, JSON Schema 2020-12 + `bash`, `jq`, `git`, `gh` at PR-emission boundaries, existing SpecKit Pro shell harness (prsg-013-reviewability-markers)
- Repository files only: `autopilot-state.json`, workflow evidence blocks, JSON contract schemas, and generated PR packet artifacts (prsg-013-reviewability-markers)
- Bash scripts with Markdown skill/operator guidance + `bash`, `jq`, `git`, `gh`; optional `gh stack` GitHub CLI extension via `github/gh-stack` (prsg-014-optional-gh-stack-stack-manager-integration)
- JSON evidence under feature `.process/` directories, `.process/prs.json`, `autopilot-state.json`, command logs, PR packet artifacts, and local `gh-stack` metadata outside the repo when the extension is used (prsg-014-optional-gh-stack-stack-manager-integration)
- Markdown/MDX content plus Astro/Starlight docs site metadata + Astro 6.4.6, Starlight 0.40.0, pnpm 10.25.0 (doc-004-codex-marketplace-installation-path)
- Docs-site JavaScript ESM on Node; Astro 6.4.6 and Starlight 0.40.0 for docs rendering; Node built-ins (`node:fs`, `node:path`, `node:url`) plus existing docs-site pnpm scripts and `starlight-links-validator`; no new runtime dependency planned. (doc-007-command-workflow-manifest-and-file-layout-reference)
- Checked-in Markdown files under `docs-site/src/content/docs/reference/`; no database or browser storage. (doc-007-command-workflow-manifest-and-file-layout-reference)
- Markdown runtime guidance, TOML Codex agent templates, YAML metadata, generated payload files, and Bash validation scripts in the existing repository; existing SpecKit Pro plugin structure, payload builder `bash scripts/build-plugin-payloads.sh`, and deterministic verification `bash tests/speckit-pro/run-all.sh`; no new runtime dependency planned. (tacd-002-capability-discovery-directive-and-agent-updates)
- Repository files only. Source guidance under `speckit-pro/`, generated payload copies under `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`, and Plan-phase artifacts under `specs/tacd-002-capability-discovery-directive-and-agent-updates/`. (tacd-002-capability-discovery-directive-and-agent-updates)
- Docs-site JavaScript ESM on Node, with Markdown/MDX content under `docs-site/src/content/docs/` + Astro 6.4.6, Starlight 0.40.0, existing `starlight-links-validator` (doc-008-troubleshooting-security-trust-update-rollback)
- Checked-in Markdown/MDX files only; no database, browser storage, or runtime state (doc-008-troubleshooting-security-trust-update-rollback)
- JavaScript ESM on Node.js for docs-site scripts; Astro 6.4.6 and Starlight 0.40.0 in `docs-site/`; pnpm 10.25.0 scoped with `pnpm --dir docs-site ...` + Existing `astro`, `@astrojs/starlight`, `@astrojs/check`, `starlight-links-validator`; add minimal Playwright dev dependency only for `validate:smoke` (doc-010-search-accessibility-deep-links-docs-validation)
- Checked-in Markdown, Astro components, package scripts, generated reference files, and CI artifacts only; no database or browser storage (doc-010-search-accessibility-deep-links-docs-validation)
- Docs-site JavaScript ESM on Node >=22.12; GitHub Actions YAML; Markdown operator guidance + Astro 6.4.6, Starlight 0.40.0, `@astrojs/check`, `starlight-links-validator`, Playwright 1.61.0, pnpm 10.25.0 via Corepack, standard GitHub Pages Actions (doc-011-github-pages-build-and-deploy-pipeline)
- Checked-in repository files only; GitHub Pages stores the uploaded `docs-site/dist` static artifact outside repository source control (doc-011-github-pages-build-and-deploy-pipeline)

## Recent Changes
- prsg-010-harden-the-hatch: Added PRSG-010 foundation artifacts, contract schemas, workflow state updates, and planning docs for the split PR stack.
