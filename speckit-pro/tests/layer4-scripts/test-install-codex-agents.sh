#!/usr/bin/env bash
# test-install-codex-agents.sh — Regression tests for the Codex subagent installer
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$PLUGIN_ROOT/codex-skills/install/scripts/install-codex-agents.sh"

EXPECTED_AGENTS=(
  autopilot-fast-helper.toml
  phase-executor.toml
  clarify-executor.toml
  checklist-executor.toml
  analyze-executor.toml
  implement-executor.toml
  codebase-analyst.toml
  spec-context-analyst.toml
  domain-researcher.toml
)

GPT55_AGENTS=(
  clarify-executor.toml
  checklist-executor.toml
  analyze-executor.toml
  implement-executor.toml
  codebase-analyst.toml
  spec-context-analyst.toml
  domain-researcher.toml
)

TMP_ROOT=$(mktemp -d)
trap 'rm -rf "$TMP_ROOT"' EXIT

DEST_DIR="$TMP_ROOT/codex-agents-dest"

section "Installer script shape"

set_test "installer script exists"
assert_file_exists "$SCRIPT"

set_test "installer script is executable"
assert_file_executable "$SCRIPT"

section "Fresh install"

set_test "installer succeeds on empty destination"
result=0
output=$("$SCRIPT" "$DEST_DIR" 2>&1) || result=$?
assert_eq "0" "$result" "exit code"

set_test "installer output reports destination"
assert_contains "$output" "Destination: $DEST_DIR"

set_test "installer output requests Codex restart"
assert_contains "$output" "Restart Codex now"

set_test "installer output reports gpt-5.5 tiered model policy"
assert_contains "$output" "Model policy: gpt-5.5"

set_test "installer output reports effective default model"
assert_contains "$output" "Executor/consensus model: gpt-5.5"

for agent in "${EXPECTED_AGENTS[@]}"; do
  set_test "fresh install copied ${agent}"
  assert_file_exists "$DEST_DIR/$agent"
done

section "Refresh install"

printf 'stale\n' > "$DEST_DIR/analyze-executor.toml"
printf 'unrelated\n' > "$DEST_DIR/custom-user-agent.toml"

set_test "refresh install succeeds on existing destination"
result=0
output=$("$SCRIPT" "$DEST_DIR" 2>&1) || result=$?
assert_eq "0" "$result" "exit code"

refreshed_content=$(cat "$DEST_DIR/analyze-executor.toml")
set_test "refresh install overwrites same-named SpecKit files"
assert_contains "$refreshed_content" 'name = "analyze-executor"'

set_test "refresh install preserves unrelated user files"
assert_file_exists "$DEST_DIR/custom-user-agent.toml"

section "Fallback install"

FALLBACK_DEST_DIR="$TMP_ROOT/codex-agents-fallback"

set_test "fallback install succeeds with --model gpt-5.4"
result=0
output=$("$SCRIPT" "$FALLBACK_DEST_DIR" --model gpt-5.4 2>&1) || result=$?
assert_eq "0" "$result" "exit code"

set_test "fallback install reports gpt-5.4 model"
assert_contains "$output" "Executor/consensus model: gpt-5.4"

set_test "fallback install reports rewritten templates"
assert_contains "$output" "Fallback mode: installed templates were rewritten"

for agent in "${GPT55_AGENTS[@]}"; do
  content=$(cat "$FALLBACK_DEST_DIR/$agent")
  set_test "fallback install rewrites ${agent} to gpt-5.4"
  assert_contains "$content" 'model = "gpt-5.4"'
done

phase_content=$(cat "$FALLBACK_DEST_DIR/phase-executor.toml")
set_test "fallback install rewrites phase-executor to gpt-5.4"
assert_contains "$phase_content" 'model = "gpt-5.4"'

spark_content=$(cat "$FALLBACK_DEST_DIR/autopilot-fast-helper.toml")
set_test "fallback install preserves Spark helper model"
assert_contains "$spark_content" 'model = "gpt-5.3-codex-spark"'

set_test "installer rejects unsupported model"
result=0
output=$("$SCRIPT" "$TMP_ROOT/bad-model" --model gpt-5.5-pro 2>&1) || result=$?
assert_eq "2" "$result" "exit code"

section "Marketplace tmp-root sync (Codex 0.125.x quirk workaround)"

# Build a fake "active install" by copying the real plugin and stamping
# an old version on it. Build a fake "marketplace tmp root" by copying
# the real plugin and stamping a newer version. Run the installer from
# the active install and verify it pulls the newer version on top.
ACTIVE_INSTALL="$TMP_ROOT/active-install"
TMP_MARKETPLACE_ROOT="$TMP_ROOT/tmp-marketplace"
SYNC_DEST_DIR="$TMP_ROOT/codex-agents-sync"

cp -R "$PLUGIN_ROOT/." "$ACTIVE_INSTALL/"
mkdir -p "$ACTIVE_INSTALL/.codex-plugin"
printf '{"version":"0.0.1"}\n' > "$ACTIVE_INSTALL/.codex-plugin/plugin.json"

cp -R "$PLUGIN_ROOT/." "$TMP_MARKETPLACE_ROOT/"
mkdir -p "$TMP_MARKETPLACE_ROOT/.codex-plugin"
printf '{"version":"99.0.0"}\n' > "$TMP_MARKETPLACE_ROOT/.codex-plugin/plugin.json"

set_test "tmp-root sync triggers when marketplace version differs"
result=0
output=$( \
  SPECKIT_MARKETPLACE_TMP_ROOT="$TMP_MARKETPLACE_ROOT" \
  "$ACTIVE_INSTALL/codex-skills/install/scripts/install-codex-agents.sh" \
    "$SYNC_DEST_DIR" 2>&1 \
) || result=$?
assert_eq "0" "$result" "exit code"

set_test "tmp-root sync output reports stale install"
assert_contains "$output" "Plugin install is stale"

set_test "tmp-root sync output reports new version"
assert_contains "$output" "Synced active plugin install to 99.0.0"

set_test "tmp-root sync output flags refresh in trailer"
assert_contains "$output" "Active plugin install was refreshed"

set_test "tmp-root sync overwrites active install version"
synced_version=$(jq -r '.version' "$ACTIVE_INSTALL/.codex-plugin/plugin.json")
assert_eq "99.0.0" "$synced_version" "active install version after sync"

# Now versions match — running again should be a no-op for the sync step.
set_test "tmp-root sync skips when versions match"
output=$( \
  SPECKIT_MARKETPLACE_TMP_ROOT="$TMP_MARKETPLACE_ROOT" \
  "$ACTIVE_INSTALL/codex-skills/install/scripts/install-codex-agents.sh" \
    "$SYNC_DEST_DIR" 2>&1 \
)
assert_not_contains "Plugin install is stale" "$output" "no stale-install message"

set_test "tmp-root sync skips with SPECKIT_SKIP_PLUGIN_SYNC=1"
# Bump active install BACK to old version so a sync would trigger if not skipped.
printf '{"version":"0.0.1"}\n' > "$ACTIVE_INSTALL/.codex-plugin/plugin.json"
output=$( \
  SPECKIT_MARKETPLACE_TMP_ROOT="$TMP_MARKETPLACE_ROOT" \
  SPECKIT_SKIP_PLUGIN_SYNC=1 \
  "$ACTIVE_INSTALL/codex-skills/install/scripts/install-codex-agents.sh" \
    "$SYNC_DEST_DIR" 2>&1 \
)
assert_not_contains "Plugin install is stale" "$output" "no stale-install message when skipped"
unsynced_version=$(jq -r '.version' "$ACTIVE_INSTALL/.codex-plugin/plugin.json")
set_test "active install is not modified when sync is skipped"
assert_eq "0.0.1" "$unsynced_version" "active install version preserved"

set_test "tmp-root sync skips when tmp root is absent"
NO_ROOT="$TMP_ROOT/does-not-exist"
output=$( \
  SPECKIT_MARKETPLACE_TMP_ROOT="$NO_ROOT" \
  "$SCRIPT" "$TMP_ROOT/codex-agents-norott" 2>&1 \
)
assert_not_contains "Plugin install is stale" "$output" "no stale-install message when tmp root missing"

test_summary
