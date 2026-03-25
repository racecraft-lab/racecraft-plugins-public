#!/usr/bin/env bash
# test-sync-marketplace-versions.sh — Unit tests for sync-marketplace-versions.sh
#
# Tests version syncing from plugin.json to marketplace.json:
# mismatch correction, no-op, missing files, multi-plugin,
# malformed JSON, missing jq, wrong cwd, non-relative source,
# missing version field, invalid semver, error output routing,
# exit codes, and edge cases.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REPO_ROOT="$(cd "$PLUGIN_ROOT/.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/sync-marketplace-versions.sh"

# Temp fixture dir with cleanup
FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

# ─────────────────────────────────────────
# Helper functions for creating test fixtures
# ─────────────────────────────────────────

# Create a minimal marketplace.json in a fixture directory
# Usage: create_marketplace <fixture_dir> <json_content>
create_marketplace() {
  local dir="$1" content="$2"
  mkdir -p "$dir/.claude-plugin"
  printf '%s\n' "$content" > "$dir/.claude-plugin/marketplace.json"
}

# Create a plugin.json for a plugin in a fixture directory
# Usage: create_plugin <fixture_dir> <plugin_name> <version>
create_plugin() {
  local dir="$1" name="$2" version="$3"
  mkdir -p "$dir/$name/.claude-plugin"
  cat > "$dir/$name/.claude-plugin/plugin.json" <<EOF
{
  "name": "$name",
  "description": "Test plugin",
  "version": "$version"
}
EOF
}

# Run the sync script from a given fixture directory
# Usage: run_sync <fixture_dir>
# Returns: stdout in $stdout_output, stderr in $stderr_output, exit code in $exit_code
run_sync() {
  local dir="$1"
  exit_code=0
  stdout_output=""
  stderr_output=""
  stdout_output=$(cd "$dir" && bash "$SCRIPT" 2>"$FIXTURE_DIR/_stderr") || exit_code=$?
  stderr_output=$(cat "$FIXTURE_DIR/_stderr")
}

# Read the marketplace.json version for a given plugin index
# Usage: read_marketplace_version <fixture_dir> <index>
read_marketplace_version() {
  local dir="$1" idx="$2"
  jq -r ".plugins[$idx].version // empty" "$dir/.claude-plugin/marketplace.json"
}

# ─────────────────────────────────────────
section "T011: Version mismatch correction"
# ─────────────────────────────────────────

set_test "Version mismatch — plugin.json=0.6.0, marketplace=0.5.0 -> updated to 0.6.0"
dir="$FIXTURE_DIR/t011"
create_marketplace "$dir" '{
  "name": "test-marketplace",
  "plugins": [
    { "name": "my-plugin", "source": "./my-plugin", "description": "Test", "version": "0.5.0" }
  ]
}'
create_plugin "$dir" "my-plugin" "0.6.0"
run_sync "$dir"
assert_eq "0" "$exit_code" "exit code"

set_test "Version mismatch — marketplace.json updated to 0.6.0"
result_version=$(read_marketplace_version "$dir" 0)
assert_eq "0.6.0" "$result_version" "synced version"

set_test "Version mismatch — stdout reports the change"
assert_contains "$stdout_output" "0.6.0" "stdout should mention new version"

# ─────────────────────────────────────────
section "T012: Already-matching versions (no-op)"
# ─────────────────────────────────────────

set_test "Matching versions — both at 1.0.0, exit 0"
dir="$FIXTURE_DIR/t012"
create_marketplace "$dir" '{
  "name": "test-marketplace",
  "plugins": [
    { "name": "my-plugin", "source": "./my-plugin", "description": "Test", "version": "1.0.0" }
  ]
}'
create_plugin "$dir" "my-plugin" "1.0.0"
run_sync "$dir"
assert_eq "0" "$exit_code" "exit code"

set_test "Matching versions — no stdout output"
assert_eq "" "$stdout_output" "stdout should be empty for no-op"

set_test "Matching versions — marketplace.json unchanged"
result_version=$(read_marketplace_version "$dir" 0)
assert_eq "1.0.0" "$result_version" "version unchanged"

# ─────────────────────────────────────────
section "T013: Missing plugin.json"
# ─────────────────────────────────────────

set_test "Missing plugin.json — exit 1"
dir="$FIXTURE_DIR/t013"
create_marketplace "$dir" '{
  "name": "test-marketplace",
  "plugins": [
    { "name": "ghost-plugin", "source": "./ghost-plugin", "description": "No plugin.json" }
  ]
}'
# Deliberately do NOT create plugin.json
run_sync "$dir"
assert_eq "1" "$exit_code" "exit code"

set_test "Missing plugin.json — stderr has error message"
assert_contains "$stderr_output" "not found" "stderr should mention file not found"

# ─────────────────────────────────────────
section "T014: Multi-plugin sync"
# ─────────────────────────────────────────

set_test "Multi-plugin — two plugins with different mismatches, exit 0"
dir="$FIXTURE_DIR/t014"
create_marketplace "$dir" '{
  "name": "test-marketplace",
  "plugins": [
    { "name": "plugin-a", "source": "./plugin-a", "description": "A", "version": "1.0.0" },
    { "name": "plugin-b", "source": "./plugin-b", "description": "B", "version": "2.0.0" }
  ]
}'
create_plugin "$dir" "plugin-a" "1.1.0"
create_plugin "$dir" "plugin-b" "2.1.0"
run_sync "$dir"
assert_eq "0" "$exit_code" "exit code"

set_test "Multi-plugin — plugin-a updated to 1.1.0"
result_version=$(read_marketplace_version "$dir" 0)
assert_eq "1.1.0" "$result_version" "plugin-a version"

set_test "Multi-plugin — plugin-b updated to 2.1.0"
result_version=$(read_marketplace_version "$dir" 1)
assert_eq "2.1.0" "$result_version" "plugin-b version"

set_test "Multi-plugin — stdout reports both changes"
assert_contains "$stdout_output" "plugin-a" "stdout should mention plugin-a"

set_test "Multi-plugin — stdout reports plugin-b change"
assert_contains "$stdout_output" "plugin-b" "stdout should mention plugin-b"

# ─────────────────────────────────────────
section "T015: Malformed JSON"
# ─────────────────────────────────────────

set_test "Malformed marketplace.json — exit 1"
dir="$FIXTURE_DIR/t015-marketplace"
create_marketplace "$dir" '{ INVALID JSON !!!'
run_sync "$dir"
assert_eq "1" "$exit_code" "exit code for malformed marketplace"

set_test "Malformed plugin.json — exit 1"
dir="$FIXTURE_DIR/t015-plugin"
create_marketplace "$dir" '{
  "name": "test-marketplace",
  "plugins": [
    { "name": "bad-plugin", "source": "./bad-plugin", "description": "Bad" }
  ]
}'
mkdir -p "$dir/bad-plugin/.claude-plugin"
printf '{ NOT VALID JSON ]\n' > "$dir/bad-plugin/.claude-plugin/plugin.json"
run_sync "$dir"
assert_eq "1" "$exit_code" "exit code for malformed plugin.json"

# ─────────────────────────────────────────
section "T016: Missing jq"
# ─────────────────────────────────────────

set_test "Missing jq — exit 1"
dir="$FIXTURE_DIR/t016"
create_marketplace "$dir" '{
  "name": "test-marketplace",
  "plugins": []
}'
# Build a minimal PATH that has bash and core utils but not jq
# Create a temp bin dir with only bash and essential commands
jq_test_bin="$FIXTURE_DIR/t016-bin"
mkdir -p "$jq_test_bin"
# Symlink bash so the script can run, plus basic commands it needs
for cmd in bash cat test printf echo [ command; do
  cmd_path=$(command -v "$cmd" 2>/dev/null || true)
  if [ -n "$cmd_path" ] && [ -x "$cmd_path" ]; then
    ln -sf "$cmd_path" "$jq_test_bin/$cmd"
  fi
done
# Also need env for the shebang
if [ -x /usr/bin/env ]; then
  ln -sf /usr/bin/env "$jq_test_bin/env"
fi
exit_code=0
stderr_output=""
stderr_output=$(cd "$dir" && PATH="$jq_test_bin" bash "$SCRIPT" 2>&1 >/dev/null) || exit_code=$?
assert_eq "1" "$exit_code" "exit code"

set_test "Missing jq — stderr mentions jq"
assert_contains "$stderr_output" "jq" "stderr should mention jq"

# ─────────────────────────────────────────
section "T017: Wrong working directory"
# ─────────────────────────────────────────

set_test "No marketplace.json in cwd — exit 1"
dir="$FIXTURE_DIR/t017-empty"
mkdir -p "$dir"
run_sync "$dir"
assert_eq "1" "$exit_code" "exit code"

set_test "Wrong cwd — stderr mentions marketplace.json"
assert_contains "$stderr_output" "marketplace.json" "stderr should mention missing file"

# ─────────────────────────────────────────
section "T018: Non-relative source"
# ─────────────────────────────────────────

set_test "External git URL source — skipped without error, exit 0"
dir="$FIXTURE_DIR/t018"
create_marketplace "$dir" '{
  "name": "test-marketplace",
  "plugins": [
    { "name": "ext-plugin", "source": "https://github.com/example/plugin.git", "description": "External" }
  ]
}'
run_sync "$dir"
assert_eq "0" "$exit_code" "exit code"

set_test "Non-relative source — stderr mentions skipping"
assert_contains "$stderr_output" "Skipping" "stderr should mention skipping"

# ─────────────────────────────────────────
section "T019: Missing version field in plugin.json"
# ─────────────────────────────────────────

set_test "No version in plugin.json — exit 1"
dir="$FIXTURE_DIR/t019"
create_marketplace "$dir" '{
  "name": "test-marketplace",
  "plugins": [
    { "name": "noversion", "source": "./noversion", "description": "No version" }
  ]
}'
mkdir -p "$dir/noversion/.claude-plugin"
cat > "$dir/noversion/.claude-plugin/plugin.json" <<'EOF'
{
  "name": "noversion",
  "description": "Plugin without version"
}
EOF
run_sync "$dir"
assert_eq "1" "$exit_code" "exit code"

set_test "No version in plugin.json — stderr mentions version"
assert_contains "$stderr_output" "version" "stderr should mention missing version"

# ─────────────────────────────────────────
section "T020: Invalid semver"
# ─────────────────────────────────────────

set_test "Version '1.0' (two-part) — exit 1"
dir="$FIXTURE_DIR/t020-twopart"
create_marketplace "$dir" '{
  "name": "test-marketplace",
  "plugins": [
    { "name": "twopart", "source": "./twopart", "description": "Two-part version" }
  ]
}'
create_plugin "$dir" "twopart" "1.0"
# Fix: write the version manually since create_plugin writes valid JSON with the literal string
run_sync "$dir"
assert_eq "1" "$exit_code" "exit code for version 1.0"

set_test "Version '1.0' — stderr mentions semver"
assert_contains "$stderr_output" "semver" "stderr should mention invalid semver"

set_test "Version 'abc' — exit 1"
dir="$FIXTURE_DIR/t020-abc"
create_marketplace "$dir" '{
  "name": "test-marketplace",
  "plugins": [
    { "name": "abc-ver", "source": "./abc-ver", "description": "Non-numeric version" }
  ]
}'
create_plugin "$dir" "abc-ver" "abc"
run_sync "$dir"
assert_eq "1" "$exit_code" "exit code for version abc"

set_test "Version 'abc' — stderr mentions semver"
assert_contains "$stderr_output" "semver" "stderr should mention invalid semver"

# ─────────────────────────────────────────
section "T021: Stderr-only error output"
# ─────────────────────────────────────────

set_test "Error scenario (missing plugin.json) — stdout is empty"
dir="$FIXTURE_DIR/t021"
create_marketplace "$dir" '{
  "name": "test-marketplace",
  "plugins": [
    { "name": "missing", "source": "./missing", "description": "Missing" }
  ]
}'
run_sync "$dir"
assert_eq "" "$stdout_output" "stdout should be empty on error"

set_test "Error scenario — stderr has error message"
assert_contains "$stderr_output" "Error" "stderr should contain error message"

# ─────────────────────────────────────────
section "T022: Exit code 1 for all error scenarios"
# ─────────────────────────────────────────

set_test "Missing plugin.json → exit 1"
dir="$FIXTURE_DIR/t022-missing-pj"
create_marketplace "$dir" '{
  "name": "test-marketplace",
  "plugins": [
    { "name": "noplugin", "source": "./noplugin", "description": "No plugin.json" }
  ]
}'
run_sync "$dir"
assert_eq "1" "$exit_code" "exit code"

set_test "Malformed marketplace → exit 1"
dir="$FIXTURE_DIR/t022-bad-market"
create_marketplace "$dir" '{ NOT JSON'
run_sync "$dir"
assert_eq "1" "$exit_code" "exit code"

set_test "No marketplace.json → exit 1"
dir="$FIXTURE_DIR/t022-no-market"
mkdir -p "$dir"
run_sync "$dir"
assert_eq "1" "$exit_code" "exit code"

# ─────────────────────────────────────────
section "T022a: Missing source field"
# ─────────────────────────────────────────

set_test "Entry without source field — exit 1"
dir="$FIXTURE_DIR/t022a"
create_marketplace "$dir" '{
  "name": "test-marketplace",
  "plugins": [
    { "name": "no-source", "description": "No source field" }
  ]
}'
run_sync "$dir"
assert_eq "1" "$exit_code" "exit code"

set_test "Missing source — stderr mentions source"
assert_contains "$stderr_output" "source" "stderr should mention missing source"

# ─────────────────────────────────────────
section "T022b: Empty plugins array"
# ─────────────────────────────────────────

set_test "Empty plugins array — exit 0"
dir="$FIXTURE_DIR/t022b"
create_marketplace "$dir" '{
  "name": "test-marketplace",
  "plugins": []
}'
run_sync "$dir"
assert_eq "0" "$exit_code" "exit code"

set_test "Empty plugins array — stderr has info message"
assert_contains "$stderr_output" "No plugins" "stderr should have info about no plugins"

# ─────────────────────────────────────────
section "T022c: Missing version in marketplace entry"
# ─────────────────────────────────────────

set_test "Marketplace entry without version — sync adds version field, exit 0"
dir="$FIXTURE_DIR/t022c"
create_marketplace "$dir" '{
  "name": "test-marketplace",
  "plugins": [
    { "name": "new-plugin", "source": "./new-plugin", "description": "Brand new, no version yet" }
  ]
}'
create_plugin "$dir" "new-plugin" "1.0.0"
run_sync "$dir"
assert_eq "0" "$exit_code" "exit code"

set_test "Marketplace entry without version — version field added as 1.0.0"
result_version=$(read_marketplace_version "$dir" 0)
assert_eq "1.0.0" "$result_version" "version should be synced from plugin.json"

set_test "Marketplace entry without version — stdout reports the addition"
assert_contains "$stdout_output" "1.0.0" "stdout should mention the version"

test_summary
