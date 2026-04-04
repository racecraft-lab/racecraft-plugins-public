# CI/CD Release Pipeline Verification Checklist

**Document type**: Manual walkthrough — execute in a single session after SPEC-004 implementation.
**Spec refs**: FR-007, FR-008, FR-005 (auditability)
**Audience**: Repository maintainer (Fredrick Gabelmann)
**Estimated session duration**: 1–3 hours

This document is the authoritative verification protocol for the end-to-end CI/CD pipeline. Each stage has a checkbox, action, expected output, and a diagnostic note. Complete stages in order. You may pause at Stage 5 while waiting for GitHub Actions to run.

---

## Stage 1: Branch Protection and Repository Setup

**Action**: Apply repository merge method settings and branch protection to `main` using the `gh` CLI. These commands are the Infrastructure-as-Code record for the configuration (FR-005 — Auditability).

### Step 1.1 — Configure repository merge methods

```bash
gh api \
  --method PATCH \
  /repos/racecraft-lab/racecraft-plugins-public \
  --field allow_squash_merge=true \
  --field allow_merge_commit=false \
  --field allow_rebase_merge=false
```

**Expected output**: HTTP 200 with repository JSON showing `"allow_squash_merge": true`, `"allow_merge_commit": false`, `"allow_rebase_merge": false`.

**Diagnostic**: If the command fails with 404 or 403, confirm `gh auth status` shows the `racecraft-lab` account with admin scope. Run `gh auth login` if needed.

---

### Step 1.2 — Apply branch protection to `main`

Run the following full-overwrite `PUT` command. All four required fields (`required_status_checks`, `enforce_admins`, `required_pull_request_reviews`, `restrictions`) must be present in every call — omitting any field results in a 422 error.

```bash
gh api \
  --method PUT \
  /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection \
  --field 'required_status_checks[strict]=false' \
  --field 'required_status_checks[contexts][]=validate-plugins' \
  --field 'required_status_checks[contexts][]=validate-pr-title' \
  --field 'enforce_admins=false' \
  --field 'required_pull_request_reviews=null' \
  --field 'restrictions=null' \
  --field 'allow_force_pushes=false' \
  --field 'allow_deletions=false'
```

**Expected output**: HTTP 200 with branch protection JSON.

**Diagnostic**: If the command returns 422 "Validation Failed", ensure all four required payload fields are present. If it returns 403 "Must have admin rights", verify `gh auth status` shows admin scope for `racecraft-lab/racecraft-plugins-public`.

---

### Step 1.3 — Read-back verification

Immediately after applying protection, confirm the configuration is correct:

```bash
gh api /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection \
  | jq '{contexts: .required_status_checks.contexts, enforce_admins: .enforce_admins.enabled}'
```

**Expected output**:

```json
{
  "contexts": ["validate-plugins", "validate-pr-title"],
  "enforce_admins": false
}
```

**Diagnostic**: If `contexts` is missing one or both check names, or if `enforce_admins` is `true`, the `PUT` request did not apply correctly. Re-run Step 1.2 with all fields included. If `enforce_admins` shows `true`, the marketplace sync `git push` will be blocked — this must be corrected before proceeding. A `true` value here means someone has enabled "Do not allow bypassing the above settings" in the GitHub UI (Settings → Branches → Edit protection rule).

- [ ] Step 1.1 complete — merge methods set
- [ ] Step 1.2 complete — branch protection applied
- [ ] Step 1.3 complete — read-back confirmed correct

---

## Stage 2: PR Submission and CI Check Execution

**Action**: Create a test feature branch with a releasable conventional commit, push it, and open a PR against `main`. Observe that all CI checks run and pass.

```bash
git checkout -b test/verify-pipeline
echo "# Verification test" >> speckit-pro/CHANGELOG.md
git add speckit-pro/CHANGELOG.md
git commit -m "fix: verify pipeline end-to-end"
git push origin test/verify-pipeline
gh pr create \
  --title "fix: verify pipeline end-to-end" \
  --body "Verification run per cicd-release-pipeline-verification.md" \
  --base main
```

**Expected CI checks and behavior**:

The pr-checks.yml workflow runs four jobs:

| Job | Trigger condition | Expected result |
|-----|-------------------|-----------------|
| `detect` | Always runs | Detects `speckit-pro` as changed plugin; outputs non-empty `plugins` array |
| `test (speckit-pro)` | Runs when `detect.outputs.plugins != '[]'` | Runs `bash tests/run-all.sh`; all 369 tests pass |
| `validate-plugins` | `if: always()`, depends on `detect` and `test` | Passes because `test` result is `success` |
| `validate-pr-title` | Always runs | Passes because PR title follows conventional commit format (`fix: ...`) |

All four checks must appear as green in the PR status panel before proceeding.

**Diagnostic**: If `validate-plugins` fails but `test (speckit-pro)` passed, the sentinel job logic is incorrect — inspect the `validate-plugins` step log in the Actions tab. If `validate-pr-title` fails, the PR title does not conform to conventional commit format (`type: description`) — edit the PR title. If `test (speckit-pro)` fails, the plugin tests are broken — run `bash speckit-pro/tests/run-all.sh` locally to diagnose.

- [ ] PR opened with `fix:` title
- [ ] `validate-plugins` check: green
- [ ] `validate-pr-title` check: green
- [ ] Merge button is **enabled** (all required checks passing)

---

## Stage 3: Copilot Review Trigger Confirmation

**Action**: After opening the PR (Stage 2), wait up to 2 minutes for Copilot to appear as an automatic reviewer and post its review.

**Expected output**: Copilot appears in the "Reviewers" panel of the PR. Within a few minutes, Copilot posts inline comments on the diff (or a summary if no issues are found). Copilot's review is advisory only — it posts comments but cannot issue "Request changes" verdicts and does not affect the merge button state.

Note: Copilot review may trigger on push rather than at PR open, depending on the "Review new pushes" ruleset setting.

**Diagnostic**: If Copilot review does not appear within 2 minutes: navigate to repository Settings → Rules → Rulesets and confirm a branch ruleset exists targeting the default branch with "Automatically request Copilot code review" enabled. If no such ruleset exists, create one (see SPEC-004 quickstart.md, Step 6). If the ruleset exists but review is not triggered, confirm that the maintainer's GitHub account has an active Copilot Pro or Copilot Pro+ subscription (the feature requires an individual subscription, not an organization plan).

If Copilot review is absent, the CI checks (`validate-plugins`, `validate-pr-title`) are unaffected — they are completely separate from Copilot review. The PR can proceed to merge regardless. Copilot review absence is a configuration issue, not a blocking failure.

- [ ] Copilot appears as a reviewer on the PR (or diagnostic noted above documented)

---

## Stage 4: PR Merge (Squash)

**Action**: Merge the PR using squash merge. In the GitHub UI, click the dropdown arrow next to "Squash and merge" and confirm only "Squash and merge" is available (the "Create a merge commit" and "Rebase and merge" options must be absent or greyed out).

```bash
# Verify only squash merge is available via API before merging
gh api /repos/racecraft-lab/racecraft-plugins-public \
  --jq '{squash: .allow_squash_merge, merge_commit: .allow_merge_commit, rebase: .allow_rebase_merge}'
```

Expected API output:

```json
{
  "squash": true,
  "merge_commit": false,
  "rebase": false
}
```

Then merge:

```bash
gh pr merge --squash --delete-branch
```

**Expected output**: The PR shows as "Merged". The `main` branch receives exactly one squash commit. The feature branch is deleted. GitHub Actions begins the Release workflow triggered by the push to `main`.

**Diagnostic**: If merge is blocked despite all required checks passing, run the read-back command from Stage 1, Step 1.3 to confirm branch protection is still configured correctly. A blocked merge with passing checks indicates `enforce_admins` may have been set to `true` after Stage 1. Re-run Step 1.2 to restore `enforce_admins: false`.

If non-squash merge options are available in the GitHub UI (merge commit or rebase), re-run Step 1.1 to re-apply the merge method restrictions.

- [ ] Only "Squash and merge" is available in the GitHub UI
- [ ] PR merged successfully as a squash commit
- [ ] Feature branch deleted

---

## Stage 5: Release-Please PR Creation

**Action**: After the PR merges to `main`, the Release workflow is triggered. Wait for the release-please job to complete (typically 1–3 minutes). Navigate to the GitHub Actions tab and find the most recent "Release Please" workflow run.

**Expected output**: Release-please opens a new PR against `main` titled something like `chore(main): release speckit-pro X.Y.Z`. The PR body contains a changelog entry for the `fix: verify pipeline end-to-end` commit. The PR is authored by `github-actions[bot]`.

Note: You may pause here. The pipeline resumes when you merge the release-please PR in Stage 6. There is no time constraint on this pause — the release-please PR remains open until manually merged.

**Diagnostic for no release-please PR appearing within 30 minutes**:

Two distinct failure modes share this symptom:

**Case (a) — Release-please ran but found no releasable commits**: Navigate to the Actions tab, find the most recent "Release Please" workflow run, expand the run log, and look for a message indicating no changes were detected. This occurs when no `fix:`, `feat:`, or breaking-change commits have been merged since the last release. A `chore:` commit alone does NOT trigger a release-please PR. Recovery: push a minimal releasable commit to `main`:
```bash
git checkout main && git pull origin main
git commit --allow-empty -m "fix: trigger release for speckit-pro"
git push origin main
```

**Case (b) — The Release-Please workflow job itself failed**: The Actions tab shows a red failure icon for the run. Inspect the workflow log for the specific error and address it, then re-run:
```bash
gh workflow run release.yml --repo racecraft-lab/racecraft-plugins-public
```

- [ ] Release-please PR created by `github-actions[bot]`
- [ ] PR body contains changelog entry for the merged `fix:` commit
- [ ] PR title follows `chore(main): release speckit-pro X.Y.Z` format

---

## Stage 6: Release-Please PR Merge and GitHub Release Publication

**Action**: Review the release-please PR, confirm the version bump and changelog are correct, then merge it using squash merge.

```bash
# List open release-please PRs
gh pr list --author "github-actions[bot]"

# Merge the release PR
gh pr merge <PR_NUMBER> --squash
```

**Expected output**:

1. The release-please PR merges to `main`.
2. GitHub Actions triggers the Release workflow again (push to `main`).
3. Release-please creates a new GitHub Release with a version tag (e.g., `speckit-pro-v1.2.0`).
4. The GitHub Release body contains the formatted changelog.
5. The marketplace sync job in the same Release workflow run updates `.claude-plugin/marketplace.json` with the new version and pushes a `chore: sync marketplace.json versions [skip ci]` commit directly to `main`.

Note: The release-please PR is created by `GITHUB_TOKEN` — GitHub prevents recursive workflow runs from `GITHUB_TOKEN`-created PRs, so `validate-plugins` and `validate-pr-title` checks will NOT run on release-please PRs. The PR will show no required status checks. This is expected behavior — release-please PRs are reviewed manually before merging.

**Diagnostic**: If the GitHub Release is not created within 5 minutes of the PR merge, inspect the Actions tab for the Release workflow run. If the run failed, check the workflow log. If the run succeeded but no Release tag exists, the issue is in release-please configuration — inspect `.release-please-manifest.json` and `release-please-config.json`.

- [ ] Release-please PR merged
- [ ] GitHub Release created with tag `speckit-pro-vX.Y.Z`
- [ ] Release body contains formatted changelog

---

## Stage 7: Marketplace Sync Commit

**Action**: After the Release workflow completes, confirm that the marketplace sync job pushed a commit to `main` updating `.claude-plugin/marketplace.json`.

```bash
# Check the latest commits on main for the sync commit
gh api /repos/racecraft-lab/racecraft-plugins-public/commits?per_page=5 \
  --jq '.[].commit.message'
```

**Expected output**: The most recent commits on `main` include one matching the pattern:

```
chore: sync marketplace.json versions [skip ci]
```

Verify the file content shows the updated version:

```bash
gh api /repos/racecraft-lab/racecraft-plugins-public/contents/.claude-plugin/marketplace.json \
  --jq '.content' | base64 -d | jq '.plugins[] | {name: .name, version: .version}'
```

**Expected output**: The version field for `speckit-pro` matches the GitHub Release tag created in Stage 6 (e.g., `1.2.0`).

**Diagnostic**: If the marketplace sync commit is absent or the version numbers are stale after the Release workflow completes (green):

1. **Detection** — read the live file:
   ```bash
   gh api /repos/racecraft-lab/racecraft-plugins-public/contents/.claude-plugin/marketplace.json \
     --jq '.content' | base64 -d
   ```
   If version strings do not match the Release tags, the sync produced incorrect output.

2. **Root cause** — view the sync workflow step log in Actions → Release → marketplace-sync job → "Update marketplace.json" step to identify whether `jq` produced an unexpected value.

3. **Automated re-try**:
   ```bash
   gh workflow run release.yml --repo racecraft-lab/racecraft-plugins-public
   ```

4. **Manual last-resort** — if re-triggering fails, manually edit `.claude-plugin/marketplace.json` and push:
   ```bash
   git checkout main && git pull origin main
   # Edit .claude-plugin/marketplace.json to set correct version strings
   git add .claude-plugin/marketplace.json
   git commit -m "chore: sync marketplace.json versions [skip ci]"
   git push origin main
   ```
   The `[skip ci]` suffix prevents triggering a new release cycle.

If the sync commit push fails with a 403 "Protected branch" error:

- Run: `gh api /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection --jq '.enforce_admins.enabled'`
  - If output is `true`: `enforce_admins` was accidentally re-enabled. Re-run Step 1.2 from Stage 1 to restore `enforce_admins: false`.
  - If output is `false`: the `permissions: contents: write` block may have been removed from `release.yml`. Inspect:
    ```bash
    gh api /repos/racecraft-lab/racecraft-plugins-public/contents/.github/workflows/release.yml \
      --jq '.content' | base64 -d | grep -A3 'permissions'
    ```
    If the `permissions` block is absent, restore `permissions: contents: write` and `permissions: pull-requests: write` in `release.yml`, merge as a `fix:` commit, and re-run the Release workflow.

- [ ] Sync commit exists on `main` matching pattern `chore: sync marketplace.json versions [skip ci]`
- [ ] `.claude-plugin/marketplace.json` shows version matching GitHub Release tag

---

## Stage 8: End-User Plugin Update

**Action**: As a plugin consumer, run the plugin update command to confirm the marketplace registry reflects the new version.

In Claude Code (or have a test consumer run):

```
/plugin marketplace update racecraft-public-plugins
```

**Expected output**: Claude Code reports that the plugin registry has been refreshed. If `speckit-pro` was previously installed, Claude Code may indicate a new version is available. The maintainer can independently confirm by reading the live `marketplace.json`:

```bash
gh api /repos/racecraft-lab/racecraft-plugins-public/contents/.claude-plugin/marketplace.json \
  --jq '.content' | base64 -d | jq '.plugins[] | select(.name == "speckit-pro") | .version'
```

**Expected output**: The version printed matches the GitHub Release tag from Stage 6.

**Diagnostic**: If `/plugin marketplace update` does not reflect the new version, check that Stage 7 completed correctly and `.claude-plugin/marketplace.json` on `main` shows the updated version. The plugin marketplace command reads directly from the repository file — if the file is correct, the command should reflect it. If the file is correct but the command still shows old data, there may be a client-side cache — re-running the command should clear it.

- [ ] `/plugin marketplace update` executed
- [ ] `marketplace.json` version confirmed to match GitHub Release tag

---

## Pipeline Verification Complete

All 8 stages passed. The CI/CD pipeline is functioning end-to-end:

- Branch protection enforces required CI checks and squash-only merges.
- Copilot code review posts advisory feedback on PRs.
- Release-please automates version management and changelog generation.
- The marketplace sync commit propagates version updates to plugin consumers.

Record the completion date and the verified plugin version here:

**Verified on**: ___________
**speckit-pro version verified**: ___________

---

## Periodic Health Check

Run this command periodically (after any rename of a workflow job in `pr-checks.yml`) to detect status-check name drift. GitHub does NOT automatically update branch protection when a workflow job is renamed — a stale required check name silently degrades protection.

```bash
gh api /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection \
  --jq '[.required_status_checks.contexts[]]'
```

**Expected output**:

```json
["validate-plugins", "validate-pr-title"]
```

Compare this output against the actual job names in `.github/workflows/pr-checks.yml`. If any name in branch protection no longer matches a job name in the workflow file, the protection is stale. Recovery: re-run Step 1.2 from Stage 1 with the corrected check names in the payload (the `PUT` endpoint is a full overwrite — include all fields).

**Symptom of stale required check names**: PRs become mergeable without the renamed check passing — the check simply does not appear in the PR status panel rather than showing as failed.
