# Data Model: Integration & Verification

**Branch**: `004-integration-verification` | **Date**: 2026-04-03
**Note**: This spec has no persistent data model or database schema. All "entities" are GitHub API configuration payloads and documentation artifacts.

---

## Key Entities

### 1. Branch Protection Rule (GitHub API payload)

Applied via `PUT /repos/{owner}/{repo}/branches/{branch}/protection`.

| Field | Value | Notes |
|-------|-------|-------|
| `required_status_checks.strict` | `false` | Do not require branch to be up-to-date before merge |
| `required_status_checks.contexts` | `["validate-plugins", "validate-pr-title"]` | Exact job names from pr-checks.yml |
| `enforce_admins` | `false` | Allows GITHUB_TOKEN admin pushes to bypass protection |
| `required_pull_request_reviews` | `null` | No human review count required (Copilot review is advisory, not enforced here) |
| `restrictions` | `null` | No push restrictions object (personal repo — bypass via enforce_admins=false) |

### 2. Repository Merge Settings (GitHub API payload)

Applied via `PATCH /repos/{owner}/{repo}` (separate from branch protection).

| Field | Value | Notes |
|-------|-------|-------|
| `allow_squash_merge` | `true` | Required merge method |
| `allow_merge_commit` | `false` | Disabled |
| `allow_rebase_merge` | `false` | Disabled |

### 3. Sentinel Job (`validate-plugins`) — pr-checks.yml addition

| Attribute | Value |
|-----------|-------|
| Job name | `validate-plugins` |
| `needs` | `[detect, test]` |
| `if` | `always()` |
| Pass condition | `needs.test.result == 'success' \|\| needs.test.result == 'skipped'` |
| Fail condition | `needs.test.result == 'failure' \|\| needs.test.result == 'cancelled'` |
| Permissions | `{}` (none needed) |

### 4. Copilot Ruleset (UI-only configuration)

| Setting | Value |
|---------|-------|
| Ruleset type | Branch ruleset |
| Target | Default branch (`main`) |
| "Automatically request Copilot code review" | Enabled |
| "Review new pushes" | Enabled (recommended) |
| Merge blocking | None (advisory only) |

### 5. Documentation Artifacts

| Artifact | Path | Purpose |
|----------|------|---------|
| Verification checklist | `docs/ai/specs/cicd-release-pipeline-verification.md` | Manual end-to-end pipeline walkthrough |
| CLAUDE.md sections | `CLAUDE.md` (appended) | 5 new CI/CD sections for contributors |

---

## State Transitions (Branch Protection Lifecycle)

```text
[Unprotected main]
    → gh api PUT branch protection → [Protected: checks required, squash-only]
    → gh api PATCH repo merge settings → [Squash-only enforced in UI]
    → GitHub UI: Copilot ruleset → [Copilot auto-review active]
    → Verification checklist executed → [Pipeline verified end-to-end]
```

## Validation Rules

- `required_status_checks.contexts` MUST contain both `validate-plugins` and `validate-pr-title` — these are the exact job IDs in pr-checks.yml
- `validate-plugins` sentinel job MUST exist in pr-checks.yml BEFORE branch protection is applied (check must exist to be required)
- `enforce_admins: false` MUST be explicit in the API call (it is the default but must be confirmed, not assumed)
- `allow_squash_merge: true`, `allow_merge_commit: false`, `allow_rebase_merge: false` are applied via the repository endpoint, not the branch protection endpoint
