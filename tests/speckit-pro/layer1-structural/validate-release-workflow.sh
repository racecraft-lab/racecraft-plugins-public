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
  && grep -Fq "gh workflow run pr-checks.yml" "$WORKFLOW_FILE" \
  && grep -Fq -- '--ref "$branch"' "$WORKFLOW_FILE" \
  && grep -Fq -- '-f pr_number="$pr_number"' "$WORKFLOW_FILE" \
  && grep -Fq -- '-f pr_title="$title"' "$WORKFLOW_FILE" \
  && grep -Fq -- '-f base_ref="main"' "$WORKFLOW_FILE"; then
  _pass
else
  _fail "expected release workflow to dispatch PR Checks for release-please PR branches"
fi

set_test "release workflow uses release-please PR output for payload sync"
if grep -Fq 'RELEASE_PRS: ${{ steps.release.outputs.prs }}' "$WORKFLOW_FILE" \
  && grep -Fq 'release_prs="${RELEASE_PRS:-[]}"' "$WORKFLOW_FILE" \
  && grep -Fq 'headBranchName // .headRefName // empty' "$WORKFLOW_FILE" \
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

set_test "release workflow syncs release PR payloads before release merge"
if [[ "$CONTENT" == *"Sync release PR payloads"* \
  && "$CONTENT" == *"steps.release.outputs.prs_created == 'true'"* \
  && "$CONTENT" == *'RELEASE_PRS: ${{ steps.release.outputs.prs }}'* \
  && "$CONTENT" == *"bash scripts/build-plugin-payloads.sh"* \
  && "$CONTENT" == *'git push origin "HEAD:${branch}"'* ]]; then
  _pass
else
  _fail "expected release workflow to rebuild and push dist payloads on release-please PRs"
fi

set_test "release workflow rebuilds plugin payloads"
assert_contains "$CONTENT" "bash scripts/build-plugin-payloads.sh"

set_test "release workflow syncs marketplace versions"
assert_contains "$CONTENT" "bash scripts/sync-marketplace-versions.sh"

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

test_summary
