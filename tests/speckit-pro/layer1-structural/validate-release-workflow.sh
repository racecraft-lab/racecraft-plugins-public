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

set_test "release workflow rebuilds plugin payloads"
assert_contains "$CONTENT" "bash scripts/build-plugin-payloads.sh"

set_test "release workflow syncs marketplace versions"
assert_contains "$CONTENT" "bash scripts/sync-marketplace-versions.sh"

set_test "release workflow opens or updates a sync PR"
if [[ "$CONTENT" == *"Open payload and marketplace sync PR"* \
  && "$CONTENT" == *"gh pr list"* \
  && "$CONTENT" == *"gh pr create --base main"* \
  && "$CONTENT" == *"gh pr edit"* ]]; then
  _pass
else
  _fail "expected release workflow to create or update a payload/marketplace sync PR"
fi

set_test "release workflow uses a versioned sync branch"
if [[ "$CONTENT" == *'sync_branch="release/sync-speckit-pro-v${version}"'* \
  && "$CONTENT" == *'git push --force origin "HEAD:${sync_branch}"'* ]]; then
  _pass
else
  _fail "expected release workflow to push a versioned release/sync-speckit-pro-vX.Y.Z branch"
fi

set_test "release workflow sync PR title is conventional"
assert_contains "$CONTENT" 'sync_title="chore: sync plugin payloads and marketplace versions"'

set_test "release workflow sync commit does not skip required PR checks"
assert_not_contains "$CONTENT" '[skip ci]'

set_test "release workflow does not direct-push generated sync changes to main"
if grep -Eq '^[[:space:]]*git push[[:space:]]*$|git push origin main|HEAD:main' "$WORKFLOW_FILE"; then
  _fail "release workflow must not push generated sync changes directly to main"
else
  _pass
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
