#!/usr/bin/env bash
# validate-release-workflow.sh — Verifies release sync uses a PR path.
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
WORKFLOW_FILE="$REPO_ROOT/.github/workflows/release.yml"

section "release.yml — Payload and Marketplace Sync"

set_test "release.yml exists"
assert_file_exists "$WORKFLOW_FILE"

CONTENT=$(cat "$WORKFLOW_FILE")

set_test "release workflow uses release-please"
assert_contains "$CONTENT" "googleapis/release-please-action@v5"

set_test "release workflow pins checkout actions"
# Count any SHA-pinned actions/checkout (version-agnostic) so routine
# dependabot checkout bumps don't break this structural assertion.
checkout_count=$(grep -Ec 'actions/checkout@[0-9a-f]{40}' "$WORKFLOW_FILE")
assert_eq "2" "$checkout_count" "release workflow pinned checkout count"

set_test "release workflow can dispatch PR checks"
if grep -Fq "actions: write" "$WORKFLOW_FILE" \
  && grep -Fq '"gh",' "$WORKFLOW_FILE" \
  && grep -Fq '"workflow",' "$WORKFLOW_FILE" \
  && grep -Fq '"run",' "$WORKFLOW_FILE" \
  && grep -Fq '"pr-checks.yml",' "$WORKFLOW_FILE" \
  && grep -Fq '"--ref",' "$WORKFLOW_FILE" \
  && grep -Fq '"pr_number=" + number' "$WORKFLOW_FILE" \
  && grep -Fq '"pr_title=" + title' "$WORKFLOW_FILE" \
  && grep -Fq '"base_ref=main"' "$WORKFLOW_FILE"; then
  _pass
else
  _fail "expected release workflow to dispatch PR Checks for release-please PR branches"
fi

set_test "release workflow uses release-please PR output for payload sync"
if grep -Fq 'RELEASE_PRS: ${{ steps.release.outputs.prs }}' "$WORKFLOW_FILE" \
  && grep -Fq 'json.loads(os.environ.get("RELEASE_PRS") or "[]")' "$WORKFLOW_FILE" \
  && grep -Fq 'release_pr.get("headBranchName") or release_pr.get("headRefName") or ""' "$WORKFLOW_FILE" \
  && grep -Fq 'prs_created=true but returned no PR metadata' "$WORKFLOW_FILE"; then
  _pass
else
  _fail "expected release workflow to use release-please prs output instead of querying just-created PR labels"
fi

set_test "release workflow does not depend on pending release labels for payload sync"
if grep -Fq -- '--label "autorelease: pending"' "$WORKFLOW_FILE"; then
  _fail "release PR payload sync must not depend on a just-created label query"
else
  _pass
fi

set_test "release workflow validates release PR readiness before dispatch"
if [[ "$CONTENT" == *"Validate release PR readiness"* \
  && "$CONTENT" == *"steps.release.outputs.prs_created == 'true'"* \
  && "$CONTENT" == *'RELEASE_PRS: ${{ steps.release.outputs.prs }}'* \
  && "$CONTENT" == *"release-readiness.json"* \
  && "$CONTENT" == *"Dispatch PR Checks for release PRs"* ]]; then
  _pass
else
  _fail "expected release workflow to validate release PR readiness before dispatching PR Checks"
fi

set_test "release workflow verifies generated test payload evidence"
assert_contains "$CONTENT" "test-payload-evidence.json"

set_test "release workflow syncs generated artifacts on the release PR"
if [[ "$CONTENT" == *"scripts/refresh-release-artifacts.py"* \
  && "$CONTENT" == *"Sync generated artifacts onto the release PR"* \
  && "$CONTENT" != *"bash scripts/sync-marketplace-versions.sh"* ]]; then
  _pass
else
  _fail "expected release workflow to refresh generated artifacts via the Python refresh script on the release PR"
fi

set_test "release workflow sync checks out the release PR branch with the release token"
if grep -Fq 'token: ${{ secrets.RELEASE_PLEASE_TOKEN || github.token }}' "$WORKFLOW_FILE" \
  && grep -Fq 'git checkout -B "$branch" FETCH_HEAD' "$WORKFLOW_FILE"; then
  _pass
else
  _fail "expected release workflow to check out the release PR branch using the release token"
fi

set_test "release workflow guards the artifact sync commit with a dirty check"
if grep -Fq 'git status --porcelain' "$WORKFLOW_FILE" \
  && grep -Fq 'chore(release): sync generated artifacts for release' "$WORKFLOW_FILE"; then
  _pass
else
  _fail "expected release workflow to commit the artifact sync only when the tree is dirty"
fi

set_test "release workflow regenerates the docs reference on sync"
assert_contains "$CONTENT" "pnpm --dir docs-site reference:generate"

set_test "release workflow verifies release artifacts are consistent after publishing"
if [[ "$CONTENT" == *"Verify release artifacts are consistent"* ]]; then
  _pass
else
  _fail "expected release workflow to verify dist/marketplace/docs-reference consistency after a release"
fi

set_test "release workflow opens NO follow-up payload/marketplace sync PR"
if [[ "$CONTENT" == *"gh pr create --base main"* || "$CONTENT" == *"release/sync-speckit-pro-v"* ]]; then
  _fail "release workflow must NOT open a follow-up sync PR; the release PR's payload-sync step already commits dist, marketplace versions, and the docs reference"
else
  _pass
fi

set_test "release workflow sync commit does not skip required PR checks"
assert_not_contains "$CONTENT" '[skip ci]'

set_test "release workflow does not direct-push generated sync changes to main"
main_push_regex="^[[:space:]]*git push([[:space:]]|$).*([[:space:]\"':/])main([[:space:]\"':]|$)"
if grep -Eq "$main_push_regex" "$WORKFLOW_FILE"; then
  _fail "release workflow must not push generated sync changes directly to main"
else
  _pass
fi

set_test "release workflow main-push regex catches common protected-branch pushes"
missed_main_pushes=$(printf '%s\n' \
  'git push origin main' \
  'git push origin HEAD:main' \
  'git push --force origin HEAD:main' \
  'git push origin refs/heads/main' \
  | grep -Ev "$main_push_regex" || true)
if [ -z "$missed_main_pushes" ]; then
  _pass
else
  _fail "main-push regex missed: $missed_main_pushes"
fi

section "release.yml — YAML Syntax"

set_test "release.yml is valid YAML"
if python3 -c "import yaml, sys; yaml.safe_load(sys.stdin)" < "$WORKFLOW_FILE" 2>/dev/null; then
  _pass
elif ruby -e "require 'yaml'; YAML.load_file(ARGV.fetch(0))" "$WORKFLOW_FILE" >/dev/null 2>&1; then
  _pass
else
  _fail "release.yml failed YAML syntax validation"
fi

section "release-please-config.json — extra-files scope"

RELEASE_CONFIG_FILE="$REPO_ROOT/release-please-config.json"

set_test "release-please-config.json exists"
assert_file_exists "$RELEASE_CONFIG_FILE"

RELEASE_CONFIG_CONTENT=$(cat "$RELEASE_CONFIG_FILE")

set_test "release-please extra-files never pre-bump proof-covered trees"
# The refresh script's proof-snapshot heuristic assumes it is the ONLY
# mutator of dist/** and the installed-cache fixtures. If release-please
# pre-bumps those trees, the snapshot misreads the live proof rows as
# deliberate test sentinels, leaves them stale, and the zero-bash gate
# blocks the release sync (see the release.yml sync-step comment).
if [[ "$RELEASE_CONFIG_CONTENT" != *'"path": "/dist/'* \
  && "$RELEASE_CONFIG_CONTENT" != *'installed-cache'* ]]; then
  _pass
else
  _fail "release-please extra-files must not target dist/** payloads or installed-cache fixtures; scripts/refresh-release-artifacts.py owns those trees"
fi

test_summary
