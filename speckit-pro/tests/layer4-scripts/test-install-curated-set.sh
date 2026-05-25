#!/usr/bin/env bash
# test-install-curated-set.sh — Unit tests for install-curated-set.sh
#
# Mocks specify, gh, and the .specify/extensions/.registry + .specify/presets/
# layout. Verifies resolution chain (release → tag → fail), --accept filtering,
# install/upgrade/check modes, and provenance log structure.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$PLUGIN_ROOT/scripts/install-curated-set.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

# Build a minimal manifest for tests so we are not coupled to the real one.
MANIFEST="$FIXTURE_DIR/curated-set.json"
cat > "$MANIFEST" <<'JSON'
{
  "version": 1,
  "entries": [
    {"id": "review", "kind": "extension", "repo": "alpha/review", "recommended_default": true, "description": "...", "min_speckit_version": "0.8.0"},
    {"id": "verify-tasks", "kind": "extension", "repo": "alpha/verify-tasks", "recommended_default": true, "description": "...", "min_speckit_version": "0.1.0"},
    {"id": "claude-ask-questions", "kind": "preset", "repo": "alpha/preset", "recommended_default": true, "description": "...", "min_speckit_version": "0.8.0"},
    {"id": "orphaned", "kind": "extension", "repo": "alpha/orphaned", "recommended_default": true, "description": "...", "min_speckit_version": "0.8.0"}
  ]
}
JSON

# Mock shim directory — first in PATH so it shadows real `gh` and `specify`.
SHIM_DIR="$FIXTURE_DIR/shim"
mkdir -p "$SHIM_DIR"

# Mock gh — looks up per-repo canned responses from $MOCK_GH_FIXTURES.
cat > "$SHIM_DIR/gh" <<'SH'
#!/usr/bin/env bash
if [[ "$1 $2" == "release list" ]]; then
  shift 2
  repo=""
  while [[ $# -gt 0 ]]; do
    if [[ "$1" == "--repo" ]]; then repo="$2"; fi
    shift
  done
  slug="${repo//\//_}"
  f="$MOCK_GH_FIXTURES/release-list/$slug.txt"
  [[ -f "$f" ]] && cat "$f" || echo ""
  exit 0
fi
if [[ "$1" == "api" ]]; then
  endpoint="$2"
  if [[ "$endpoint" == repos/*/tags ]]; then
    repo="${endpoint#repos/}"; repo="${repo%/tags}"
    slug="${repo//\//_}"
    f="$MOCK_GH_FIXTURES/api-tags/$slug.txt"
    [[ -f "$f" ]] && cat "$f" || echo ""
    exit 0
  fi
fi
echo "mock-gh: unhandled args: $*" >&2
exit 1
SH

# Mock specify — records `extension add` / `preset add` invocations.
cat > "$SHIM_DIR/specify" <<'SH'
#!/usr/bin/env bash
case "$1 $2" in
  "extension add"|"preset add")
    echo "$*" >> "$MOCK_SPECIFY_LOG"
    exit 0
    ;;
  "extension remove"|"preset remove")
    echo "$*" >> "$MOCK_SPECIFY_LOG"
    exit 0
    ;;
  *)
    echo "mock-specify: unhandled $*" >&2
    exit 1
    ;;
esac
SH

chmod +x "$SHIM_DIR/gh" "$SHIM_DIR/specify"

# Helper: prepare a fresh per-test environment under $FIXTURE_DIR/<name>.
new_env() {
  local name="$1"
  local d="$FIXTURE_DIR/$name"
  mkdir -p "$d/.specify/extensions" "$d/.specify/presets"
  echo '{"extensions": {}}' > "$d/.specify/extensions/.registry"
  mkdir -p "$d/gh-fixtures/release-list" "$d/gh-fixtures/api-tags"
  echo "$d"
}

# Helper: run the script inside an env, with controlled mocks.
run_script() {
  local env_dir="$1"; shift
  (
    cd "$env_dir"
    PATH="$SHIM_DIR:$PATH" \
    MOCK_GH_FIXTURES="$env_dir/gh-fixtures" \
    MOCK_SPECIFY_LOG="$env_dir/specify.log" \
    bash "$SCRIPT" --manifest="$MANIFEST" "$@"
  )
}

# ─────────────────────────────────────────
section "Script shape"
# ─────────────────────────────────────────

set_test "script exists"
assert_file_exists "$SCRIPT"

set_test "script syntax is valid"
bash -n "$SCRIPT" && _pass || _fail "bash -n failed"

# ─────────────────────────────────────────
section "check mode — nothing installed yet"
# ─────────────────────────────────────────

env1=$(new_env "empty-check")
echo "v1.0.1" > "$env1/gh-fixtures/release-list/alpha_review.txt"
echo "v1.0.0" > "$env1/gh-fixtures/release-list/alpha_preset.txt"
# verify-tasks has no release but has a tag
: > "$env1/gh-fixtures/release-list/alpha_verify-tasks.txt"
echo "v1.0.0" > "$env1/gh-fixtures/api-tags/alpha_verify-tasks.txt"
# orphaned has neither — should be silently skipped
: > "$env1/gh-fixtures/release-list/alpha_orphaned.txt"
: > "$env1/gh-fixtures/api-tags/alpha_orphaned.txt"

result=0
output=$(run_script "$env1" --mode=check 2>&1) || result=$?

set_test "check mode exits 2 when work is pending"
assert_eq "2" "$result" "exit code"

set_test "check mode reports review as would-install"
assert_contains "$output" "[review] would install"

set_test "check mode resolves verify-tasks via tag fallback"
assert_contains "$output" "[verify-tasks] would install extension at tag:v1.0.0"

set_test "check mode resolves claude-ask-questions as would-install"
assert_contains "$output" "[claude-ask-questions] would install preset"

set_test "check mode warns when neither release nor tag exists"
assert_contains "$output" "[orphaned] no GitHub Release and no git tag"

set_test "check mode does NOT call specify add"
assert_file_not_exists "$env1/specify.log"

# ─────────────────────────────────────────
section "check mode — everything current"
# ─────────────────────────────────────────

env2=$(new_env "current")
cat > "$env2/.specify/extensions/.registry" <<'JSON'
{"extensions": {"review": {"version": "1.0.1"}, "verify-tasks": {"version": "1.0.0"}}}
JSON
mkdir -p "$env2/.specify/presets/claude-ask-questions"
echo 'version: "1.0.0"' > "$env2/.specify/presets/claude-ask-questions/preset.yml"

echo "v1.0.1" > "$env2/gh-fixtures/release-list/alpha_review.txt"
echo "v1.0.0" > "$env2/gh-fixtures/release-list/alpha_preset.txt"
: > "$env2/gh-fixtures/release-list/alpha_verify-tasks.txt"
echo "v1.0.0" > "$env2/gh-fixtures/api-tags/alpha_verify-tasks.txt"
: > "$env2/gh-fixtures/release-list/alpha_orphaned.txt"
: > "$env2/gh-fixtures/api-tags/alpha_orphaned.txt"

# Limit accept to entries with resolvable refs so 'orphaned' doesn't pollute.
result=0
output=$(run_script "$env2" --mode=check --accept=review,verify-tasks,claude-ask-questions 2>&1) || result=$?

set_test "check mode exits 0 when all installed at latest"
assert_eq "0" "$result" "exit code"

set_test "check mode produces no 'would' lines when current"
assert_not_contains "$output" "would install"
assert_not_contains "$output" "would upgrade"

# ─────────────────────────────────────────
section "install mode — installs missing entries"
# ─────────────────────────────────────────

env3=$(new_env "install")
echo "v1.0.1" > "$env3/gh-fixtures/release-list/alpha_review.txt"
echo "v1.0.0" > "$env3/gh-fixtures/release-list/alpha_preset.txt"
: > "$env3/gh-fixtures/release-list/alpha_verify-tasks.txt"
echo "v1.0.0" > "$env3/gh-fixtures/api-tags/alpha_verify-tasks.txt"
: > "$env3/gh-fixtures/release-list/alpha_orphaned.txt"
: > "$env3/gh-fixtures/api-tags/alpha_orphaned.txt"

result=0
output=$(run_script "$env3" --mode=install --accept=review,claude-ask-questions 2>&1) || result=$?

set_test "install mode succeeds"
assert_eq "0" "$result" "exit code"

set_test "install mode invoked specify extension add for review"
specify_calls=$(cat "$env3/specify.log" 2>/dev/null || echo "")
assert_contains "$specify_calls" "extension add --from https://github.com/alpha/review/archive/refs/tags/v1.0.1.zip"

set_test "install mode invoked specify preset add for claude-ask-questions"
assert_contains "$specify_calls" "preset add --from https://github.com/alpha/preset/archive/refs/tags/v1.0.0.zip"

set_test "install mode did NOT touch verify-tasks (filtered by --accept)"
assert_not_contains "$specify_calls" "verify-tasks"

set_test "install mode wrote provenance log"
assert_file_exists "$env3/.specify/curated-install.json"

set_test "provenance log has valid JSON history"
provenance=$(cat "$env3/.specify/curated-install.json")
assert_contains "$provenance" '"history"'
assert_contains "$provenance" '"mode": "install"'
assert_contains "$provenance" '"ref_tag": "v1.0.1"'

# ─────────────────────────────────────────
section "install mode — skips already-installed"
# ─────────────────────────────────────────

env4=$(new_env "install-skip")
cat > "$env4/.specify/extensions/.registry" <<'JSON'
{"extensions": {"review": {"version": "1.0.1"}}}
JSON
echo "v1.0.1" > "$env4/gh-fixtures/release-list/alpha_review.txt"

result=0
output=$(run_script "$env4" --mode=install --accept=review 2>&1) || result=$?

set_test "install mode exits 0 even when nothing to install"
assert_eq "0" "$result" "exit code"

set_test "install mode reports 'already installed'"
assert_contains "$output" "[review] already installed"

set_test "install mode did NOT call specify add"
assert_file_not_exists "$env4/specify.log"

# ─────────────────────────────────────────
section "upgrade mode — bumps out-of-date entries"
# ─────────────────────────────────────────

env5=$(new_env "upgrade")
cat > "$env5/.specify/extensions/.registry" <<'JSON'
{"extensions": {"review": {"version": "1.0.0"}}}
JSON
echo "v1.0.1" > "$env5/gh-fixtures/release-list/alpha_review.txt"

result=0
output=$(run_script "$env5" --mode=upgrade --accept=review 2>&1) || result=$?

set_test "upgrade mode succeeds"
assert_eq "0" "$result" "exit code"

set_test "upgrade mode reports upgrade direction"
assert_contains "$output" "upgrading 1.0.0"

set_test "upgrade mode invoked remove then add"
upgrade_calls=$(cat "$env5/specify.log")
assert_contains "$upgrade_calls" "extension remove review"
assert_contains "$upgrade_calls" "extension add --from https://github.com/alpha/review/archive/refs/tags/v1.0.1.zip"

# ─────────────────────────────────────────
section "invalid arguments"
# ─────────────────────────────────────────

set_test "invalid --mode rejected"
result=0
PATH="$SHIM_DIR:$PATH" bash "$SCRIPT" --manifest="$MANIFEST" --mode=bogus 2>/dev/null || result=$?
assert_eq "1" "$result" "exit code"

set_test "missing manifest rejected"
result=0
PATH="$SHIM_DIR:$PATH" bash "$SCRIPT" --manifest="/no/such/file.json" --mode=check 2>/dev/null || result=$?
assert_eq "1" "$result" "exit code"

test_summary
