# Research: Integration & Verification

**Branch**: `004-integration-verification` | **Date**: 2026-04-03
**Phase**: 0 — All NEEDS CLARIFICATION items resolved via Clarify session

---

## Topic 1: GitHub Branch Protection API — Legacy vs. Rulesets

**Decision**: Legacy branch protection API (`PUT /repos/{owner}/{repo}/branches/{branch}/protection`)

**Rationale**: The legacy API is sufficient for a solo-maintainer personal repository. It supports required status checks, squash-only enforcement, and `enforce_admins: false`. Rulesets add complexity (organization-level concepts, bypass actor configuration) with no added benefit at this scale.

**Alternatives considered**: GitHub repository rulesets (newer API). Rejected because: rulesets bypass actor configuration (`bypass_pull_request_allowances.apps`) is an organization-only feature unavailable on personal repos. Legacy API is simpler and fully supported.

**Key API shape**:
```json
PUT /repos/{owner}/{repo}/branches/{branch}/protection
{
  "required_status_checks": {
    "strict": false,
    "contexts": ["validate-plugins", "validate-pr-title"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_squash_merge": true,
  "allow_merge_commit": false,
  "allow_rebase_merge": false
}
```

Note: `allow_squash_merge`, `allow_merge_commit`, and `allow_rebase_merge` are repository-level settings (PATCH `/repos/{owner}/{repo}`), not part of the branch protection payload. Two `gh api` calls are required: one for branch protection, one for repository merge method settings.

---

## Topic 2: GitHub Actions Bot Bypass on Personal Repositories

**Decision**: Use `enforce_admins: false` (default) — no explicit bypass actor configuration

**Rationale**: On a personal repository, `GITHUB_TOKEN` from the repo owner's workflows has admin-equivalent permissions. When `enforce_admins: false`, admin-context pushes bypass branch protection. The SPEC-003 `release.yml` marketplace sync push uses `GITHUB_TOKEN` from the repo owner context, so it succeeds without requiring a PR.

**Alternatives considered**: `bypass_pull_request_allowances.apps` (org-only, unavailable). Rulesets bypass actor (org-only). Custom GitHub App as bypass actor (unnecessary complexity — full solution for org migration only).

**Future path**: If repo migrates to an organization, upgrade to custom GitHub App + rulesets bypass actor. Document in plan.

---

## Topic 3: Required Status Check Names

**Decision**: `validate-plugins` (new sentinel job) + `validate-pr-title` (existing job)

**Rationale**: The matrix job `test (speckit-pro)` has a dynamic name and cannot be registered as a stable required check (it would need to be registered as `test (speckit-pro)` specifically and would break when new plugins are added). A sentinel aggregator job named `validate-plugins` provides a stable static check name that generalizes as new plugins are added to the matrix.

**Sentinel job behavior**:
- Runs `if: always()` — always executes regardless of matrix job result
- Depends on `[detect, test]`
- Passes if `test` result is `success` or `skipped` (docs-only PR scenario)
- Fails if `test` result is `failure` or `cancelled`

**Shell expression for sentinel**:
```bash
if [[ "${{ needs.test.result }}" == "success" || "${{ needs.test.result }}" == "skipped" ]]; then
  echo "All plugin tests passed or were skipped."
  exit 0
else
  echo "::error::Plugin tests failed or were cancelled."
  exit 1
fi
```

---

## Topic 4: Docs-Only PR — Skipped Matrix Job Behavior

**Decision**: Job-level `if:` conditionals produce `skipped` status (not `pending`) — does not block merges

**Rationale**: The `test` job uses a job-level `if: needs.detect.result == 'success' && needs.detect.outputs.plugins != '[]'`. When this evaluates to false, the job is skipped. GitHub reports skipped jobs as passing (not pending), so docs-only PRs are not blocked. The sentinel `validate-plugins` must explicitly handle `skipped` as a passing condition.

**Alternatives considered**: Workflow-level path filters. Rejected because they would leave the check in `pending` state, blocking docs-only PRs.

---

## Topic 5: Copilot Code Review Configuration

**Decision**: GitHub UI only — repository Settings → Rules → Rulesets → New branch ruleset

**Rationale**: There is no GitHub REST API endpoint for enabling Copilot automatic code review. It is exclusively configured via the repository ruleset UI. Copilot posts advisory inline comments but cannot issue "Request changes" or act as a required status check.

**Configuration steps** (UI-only):
1. Repository Settings → Rules → Rulesets → New branch ruleset
2. Target: default branch (`main`)
3. Enable "Automatically request Copilot code review"
4. Enable "Review new pushes" (optional — re-reviews on each push)
5. Save ruleset

**Requirements**: Copilot Pro or Pro+ subscription on the maintainer account. Not an organization plan requirement.

---

## Topic 6: Verification Checklist Format

**Decision**: Manual markdown walkthrough document at `docs/ai/specs/cicd-release-pipeline-verification.md`

**Rationale**: The pipeline involves GitHub UI actions (merging PRs, Copilot review triggering), release-please PR creation (non-deterministic timing), and GitHub Actions execution that cannot be reliably automated in a shell script. A manual checklist with expected outputs and diagnostic notes is the correct artifact format.

**Format per stage**:
```markdown
### Stage N: [Stage Name]
**Action**: [What to do]
**Expected output**: [What success looks like]
**Diagnostic**: [What to check if the expected output is not observed]
```

---

## Topic 7: CLAUDE.md New Sections

**Decision**: Five additive sections appended after existing content, no modifications to existing sections

**New sections**:
1. `## Contributing & Branching Strategy` — branch naming (`NNN-feature-name`), PR requirements (conventional commits, squash only)
2. `## CI/CD Workflow` — overview of pr-checks.yml jobs (`detect`, `test`, `validate-plugins`, `validate-pr-title`)
3. `## Release Process` — release-please flow, GitHub Release, marketplace sync, user update path
4. `## Adding a New Plugin to Release Automation` — instructions for updating `release-please-config.json` and `.release-please-manifest.json`
5. `## Recovery & Rollback Procedures` — copy-pasteable `gh workflow run`, `Release-As:` footer, `fix:` commit

---

## Topic 8: Recovery Procedure Command Specificity

**Decision**: Exact copy-pasteable commands with only `<owner>/<repo>` substitution required

**Required content**:
- Re-trigger marketplace sync: `gh workflow run release.yml --repo <owner>/<repo>`
- Force version via commit footer: `Release-As: X.Y.Z` (git commit trailer, not a `gh` command)
- Patch-forward bad release: `fix(<plugin>): patch bad release` commit example

**Rationale**: SC-006 requires resolution in under 15 minutes without external documentation. Conceptual descriptions do not meet this bar.

---

## All NEEDS CLARIFICATION Items: RESOLVED

All clarifications were resolved in the Clarify phase (2026-04-03). No open unknowns remain. Plan proceeds to Phase 1.
