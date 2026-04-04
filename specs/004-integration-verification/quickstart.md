# Quickstart: Integration & Verification

**Branch**: `004-integration-verification` | **Date**: 2026-04-03

This guide describes the implementation sequence for SPEC-004. All steps must be executed in order.

---

## Prerequisites

- `gh` CLI authenticated as `racecraft-lab` account with admin access to `racecraft-labs/racecraft-plugins-public`
- Copilot Pro or Copilot Pro+ subscription active on the maintainer's GitHub account
- Working directory: `.worktrees/004-integration-verification/` (the feature branch worktree)
- Existing tests passing: `bash speckit-pro/tests/run-all.sh` (369 tests, must remain green)

---

## Step 1: Add `validate-plugins` Sentinel Job to pr-checks.yml

**Why first**: Branch protection cannot require a check that does not yet exist. The sentinel job must be merged to `main` (or exist in a PR being evaluated) before it can be registered as a required check.

Edit `.github/workflows/pr-checks.yml` to add the `validate-plugins` job after `validate-pr-title`. See `contracts/branch-protection.md` for the exact YAML to add.

**Verify locally**:
```bash
# Confirm YAML is valid (requires yq or python-yaml)
python3 -c "import yaml, sys; yaml.safe_load(sys.stdin)" < .github/workflows/pr-checks.yml && echo "YAML valid"
```

---

## Step 2: Update CLAUDE.md

Add the five new sections to `CLAUDE.md`. Append after the existing "Recent Changes" section. Sections:
1. `## Contributing & Branching Strategy`
2. `## CI/CD Workflow`
3. `## Release Process`
4. `## Adding a New Plugin to Release Automation`
5. `## Recovery & Rollback Procedures`

Content is defined in `data-model.md` (entity 5) and FR-009/FR-010. Each section must be self-contained and include inline troubleshooting one-liners.

---

## Step 3: Create Verification Checklist

Create `docs/ai/specs/cicd-release-pipeline-verification.md` as a manual walkthrough document. See FR-007 and FR-008 for required content. Format each stage with:
- **Action**: what to do
- **Expected output**: what success looks like
- **Diagnostic**: what to check on failure

Pipeline stages to cover:
1. Feature branch creation
2. PR submission and CI check execution
3. Copilot review trigger confirmation
4. PR merge (squash)
5. Release-please PR creation
6. Release-please PR merge and GitHub Release publication
7. Marketplace sync commit
8. End-user `/plugin marketplace update`

---

## Step 4: Apply Repository Merge Method Settings

```bash
gh api \
  --method PATCH \
  /repos/racecraft-lab/racecraft-plugins-public \
  --field allow_squash_merge=true \
  --field allow_merge_commit=false \
  --field allow_rebase_merge=false
```

---

## Step 5: Apply Branch Protection

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

**Verify**:
```bash
gh api /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection \
  | jq '{contexts: .required_status_checks.contexts, enforce_admins: .enforce_admins.enabled}'
```

Expected:
```json
{
  "contexts": ["validate-plugins", "validate-pr-title"],
  "enforce_admins": false
}
```

---

## Step 6: Configure Copilot Code Review (UI)

1. Navigate to: https://github.com/racecraft-lab/racecraft-plugins-public/settings/rules
2. Click **New branch ruleset**
3. Set **Ruleset name**: `Copilot Code Review`
4. **Target branches**: Default branch
5. Enable **Automatically request Copilot code review**
6. Enable **Review new pushes**
7. Click **Create**

No API available for this step. Document this as a manual step in the verification checklist.

---

## Step 7: Run Existing Tests (Regression Check)

```bash
bash speckit-pro/tests/run-all.sh
```

All 369 tests must pass. This confirms that no plugin code was inadvertently modified.

---

## Post-Implementation: Follow Verification Checklist

Execute `docs/ai/specs/cicd-release-pipeline-verification.md` end-to-end to confirm the pipeline works as a system.

---

## Rollback

Remove branch protection if anything goes wrong:
```bash
gh api --method DELETE /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection
```

Re-enable all merge methods if needed:
```bash
gh api \
  --method PATCH \
  /repos/racecraft-lab/racecraft-plugins-public \
  --field allow_squash_merge=true \
  --field allow_merge_commit=true \
  --field allow_rebase_merge=true
```
