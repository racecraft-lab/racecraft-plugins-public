# Contract: Branch Protection Configuration

**Type**: GitHub REST API call sequence
**Spec ref**: FR-001, FR-002, FR-003, FR-004, FR-005

---

## Step 1: Add `validate-plugins` sentinel job to pr-checks.yml

This MUST be done before applying branch protection. The check must exist in a merged workflow before it can be registered as a required check.

**File**: `.github/workflows/pr-checks.yml`
**Change**: Add the following job after the `validate-pr-title` job:

```yaml
  # ───────────────────────────────────────────────────────────────────
  # Job 4: Sentinel aggregator — provides stable check name for branch
  #         protection. Passes if test matrix passed or was skipped.
  # ───────────────────────────────────────────────────────────────────
  validate-plugins:
    name: validate-plugins
    runs-on: ubuntu-latest
    if: always()
    needs: [detect, test]
    permissions: {}

    steps:
      - name: Check test matrix result
        run: |
          set -euo pipefail
          result="${{ needs.test.result }}"
          if [[ "$result" == "success" || "$result" == "skipped" ]]; then
            echo "Plugin tests passed or were skipped (result: ${result})."
            exit 0
          else
            echo "::error::Plugin tests failed or were cancelled (result: ${result})."
            exit 1
          fi
```

---

## Step 2: Configure Repository Merge Methods

```bash
gh api \
  --method PATCH \
  /repos/racecraft-lab/racecraft-plugins-public \
  --field allow_squash_merge=true \
  --field allow_merge_commit=false \
  --field allow_rebase_merge=false
```

**Expected response**: HTTP 200 with updated repository object showing `"allow_squash_merge": true`, `"allow_merge_commit": false`, `"allow_rebase_merge": false`.

---

## Step 3: Apply Branch Protection to `main`

```bash
gh api \
  --method PUT \
  /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection \
  --field 'required_status_checks[strict]=false' \
  --field 'required_status_checks[contexts][]=validate-plugins' \
  --field 'required_status_checks[contexts][]=validate-pr-title' \
  --field 'enforce_admins=false' \
  --field 'required_pull_request_reviews=null' \
  --field 'restrictions=null'
```

**Expected response**: HTTP 200 with branch protection object. Confirm:
- `required_status_checks.contexts` = `["validate-plugins", "validate-pr-title"]`
- `enforce_admins.enabled` = `false`

---

## Verify Protection is Active

```bash
gh api /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection
```

Expected output includes `required_status_checks` with both check names, and `enforce_admins.enabled: false`.

---

## Remove Branch Protection (if needed for rollback)

```bash
gh api \
  --method DELETE \
  /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection
```
