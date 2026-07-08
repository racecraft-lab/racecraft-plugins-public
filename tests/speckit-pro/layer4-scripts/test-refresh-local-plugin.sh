#!/usr/bin/env bash
# test-refresh-local-plugin.sh -- Unit tests for the local plugin refresh helper
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"
REPO_ROOT="$(cd "$PLUGIN_ROOT/.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/refresh-local-plugin.sh"

TMP_ROOT=$(mktemp -d)
trap 'rm -rf "$TMP_ROOT"' EXIT

section "Script shape"

set_test "refresh helper exists"
assert_file_exists "$SCRIPT"

set_test "refresh helper is executable"
assert_file_executable "$SCRIPT"

set_test "help mentions Codex refresh"
result=0
output=$(bash "$SCRIPT" --help 2>&1) || result=$?
assert_eq "0" "$result" "exit code"
assert_contains "$output" "--codex" "help should document --codex"

section "Dry-run default"

set_test "dry-run default rebuilds, validates, and prints Claude dev command"
result=0
output=$(bash "$SCRIPT" --dry-run 2>&1) || result=$?
assert_eq "0" "$result" "exit code"
assert_contains "$output" "build-plugin-payloads.py" "dry-run should include payload build"
assert_contains "$output" "claude plugin validate" "dry-run should include Claude validation"
assert_contains "$output" "claude --plugin-dir" "dry-run should print local dev command"

set_test "dry-run default refreshes both installed plugin caches"
assert_contains "$output" "plugin uninstall" "default should uninstall Claude plugin"
assert_contains "$output" "codex plugin remove" "default should remove Codex plugin"

set_test "dry-run opt-outs skip installed plugin cache refresh"
result=0
output=$(bash "$SCRIPT" --dry-run --no-codex --no-claude-install 2>&1) || result=$?
assert_eq "0" "$result" "exit code"
assert_not_contains "$output" "plugin uninstall" "--no-claude-install should skip Claude uninstall"
assert_not_contains "$output" "codex plugin remove" "--no-codex should skip Codex remove"

set_test "dry-run does not require generated payloads to exist"
result=0
output=$(SPECKIT_PLUGIN_NAME="plugin-without-payloads" bash "$SCRIPT" --dry-run 2>&1) || result=$?
assert_eq "0" "$result" "exit code"
assert_not_contains "$output" "payload not found" "dry-run should not abort on missing payloads"

set_test "dry-run all prints refresh commands without requiring real CLI state"
FAIL_BIN="$TMP_ROOT/fail-bin"
mkdir -p "$FAIL_BIN"
printf '#!/usr/bin/env bash\nexit 99\n' > "$FAIL_BIN/claude"
printf '#!/usr/bin/env bash\nexit 99\n' > "$FAIL_BIN/codex"
chmod +x "$FAIL_BIN/claude" "$FAIL_BIN/codex"
result=0
output=$(PATH="$FAIL_BIN:$PATH" bash "$SCRIPT" --dry-run --all 2>&1) || result=$?
assert_eq "0" "$result" "exit code"
assert_contains "$output" "claude plugin marketplace list # verify" "should print Claude marketplace verification"
assert_contains "$output" "codex plugin marketplace list # verify" "should print Codex marketplace verification"
assert_contains "$output" "claude plugin install" "should print Claude install command"
assert_contains "$output" "codex plugin add" "should print Codex add command"

section "Stubbed CLI execution"

STUB_BIN="$TMP_ROOT/bin"
CALL_LOG="$TMP_ROOT/calls.log"
mkdir -p "$STUB_BIN"
: > "$CALL_LOG"

cat > "$STUB_BIN/claude" <<EOF
#!/usr/bin/env bash
printf 'claude %s\n' "\$*" >> "$CALL_LOG"
if [ "\$1 \$2 \$3" = "plugin marketplace list" ]; then
  cat <<'LIST'
Configured marketplaces:

  ❯ racecraft-plugins-public
    Source: Directory ($REPO_ROOT)
LIST
fi
exit 0
EOF
chmod +x "$STUB_BIN/claude"

cat > "$STUB_BIN/codex" <<EOF
#!/usr/bin/env bash
printf 'codex %s\n' "\$*" >> "$CALL_LOG"
if [ "\$1 \$2 \$3" = "plugin marketplace list" ]; then
  cat <<'LIST'
MARKETPLACE               ROOT
racecraft-plugins-public  $REPO_ROOT
LIST
fi
exit 0
EOF
chmod +x "$STUB_BIN/codex"

set_test "Codex refresh removes and adds installed plugin"
: > "$CALL_LOG"
result=0
output=$(PATH="$STUB_BIN:$PATH" bash "$SCRIPT" --no-build --no-validate --codex 2>&1) || result=$?
assert_eq "0" "$result" "exit code"
calls=$(cat "$CALL_LOG")
assert_contains "$calls" "codex plugin marketplace list" "should inspect Codex marketplace"
assert_contains "$calls" "codex plugin remove speckit-pro@racecraft-plugins-public" "should remove stale Codex plugin"
assert_contains "$calls" "codex plugin add speckit-pro@racecraft-plugins-public" "should reinstall Codex plugin"
assert_contains "$output" "Start a new Codex thread" "should report restart guidance"

set_test "Claude install refresh honors requested scope"
: > "$CALL_LOG"
result=0
output=$(PATH="$STUB_BIN:$PATH" bash "$SCRIPT" --no-build --no-validate --claude-install --scope local 2>&1) || result=$?
assert_eq "0" "$result" "exit code"
calls=$(cat "$CALL_LOG")
assert_contains "$calls" "claude plugin marketplace list" "should inspect Claude marketplace"
assert_contains "$calls" "claude plugin uninstall speckit-pro@racecraft-plugins-public --scope local -y" "should remove stale Claude plugin"
assert_contains "$calls" "claude plugin install speckit-pro@racecraft-plugins-public --scope local" "should install at requested scope"
assert_contains "$output" "/reload-plugins" "should report Claude reload guidance"

set_test "Claude launch uses generated Claude payload"
: > "$CALL_LOG"
result=0
output=$(PATH="$STUB_BIN:$PATH" bash "$SCRIPT" --no-build --no-validate --launch-claude 2>&1) || result=$?
assert_eq "0" "$result" "exit code"
calls=$(cat "$CALL_LOG")
assert_contains "$calls" "claude --plugin-dir $REPO_ROOT/dist/claude/speckit-pro" "should launch with dist Claude payload"

section "Cache-refresh failure handling"

# Env-driven stubs so each case can configure marketplace state and the exit
# code / message of uninstall / remove. The stubs read CALL_LOG, STUB_REPO_ROOT,
# and the per-case MKT_MODE / *_RC / *_MSG variables from the environment, which
# the script passes through to its child CLI processes.
FSTUB="$TMP_ROOT/fail-stub"
mkdir -p "$FSTUB"

cat > "$FSTUB/claude" <<'STUB'
#!/usr/bin/env bash
printf 'claude %s\n' "$*" >> "$CALL_LOG"
if [ "$1 $2 $3" = "plugin marketplace list" ]; then
  n="${MKT_NAME:-racecraft-plugins-public}"
  case "${MKT_MODE:-local}" in
    local)     printf 'Configured marketplaces:\n\n  ❯ %s\n    Source: Directory (%s)\n' "$n" "$STUB_REPO_ROOT" ;;
    github)    printf 'Configured marketplaces:\n\n  ❯ %s\n    Source: GitHub (racecraft-lab/%s)\n' "$n" "$n" ;;
    elsewhere) printf 'Configured marketplaces:\n\n  ❯ %s\n    Source: Directory (/some/other/checkout)\n' "$n" ;;
    absent)    printf 'Configured marketplaces:\n\n  ❯ other-marketplace\n    Source: GitHub (a/b)\n' ;;
    listfail)  echo "boom" >&2; exit 7 ;;
  esac
  exit 0
fi
if [ "$1 $2" = "plugin uninstall" ]; then
  [ -n "${UNINSTALL_MSG:-}" ] && printf '%s\n' "$UNINSTALL_MSG" >&2
  exit "${UNINSTALL_RC:-0}"
fi
exit 0
STUB
chmod +x "$FSTUB/claude"

cat > "$FSTUB/codex" <<'STUB'
#!/usr/bin/env bash
printf 'codex %s\n' "$*" >> "$CALL_LOG"
if [ "$1 $2 $3" = "plugin marketplace list" ]; then
  printf 'MARKETPLACE               ROOT\nracecraft-plugins-public  %s\n' "$STUB_REPO_ROOT"
  exit 0
fi
if [ "$1 $2" = "plugin remove" ]; then
  [ -n "${REMOVE_MSG:-}" ] && printf '%s\n' "$REMOVE_MSG" >&2
  exit "${REMOVE_RC:-0}"
fi
exit 0
STUB
chmod +x "$FSTUB/codex"

run_claude_refresh() { # extra env passed as VAR=val args; runs claude-only refresh
  env "$@" CALL_LOG="$CALL_LOG" STUB_REPO_ROOT="$REPO_ROOT" PATH="$FSTUB:$PATH" \
    bash "$SCRIPT" --no-build --no-validate --no-codex --claude-install 2>&1
}

set_test "benign 'not found' uninstall still proceeds to install"
: > "$CALL_LOG"
result=0
output=$(run_claude_refresh UNINSTALL_RC=1 UNINSTALL_MSG='Plugin "speckit-pro@racecraft-plugins-public" not found in installed plugins') || result=$?
assert_eq "0" "$result" "exit code"
assert_contains "$output" "/reload-plugins" "benign uninstall failure should not abort"
calls=$(cat "$CALL_LOG")
assert_contains "$calls" "claude plugin install speckit-pro@racecraft-plugins-public" "should still install after benign uninstall failure"

set_test "non-benign uninstall failure aborts with its output"
: > "$CALL_LOG"
result=0
output=$(run_claude_refresh UNINSTALL_RC=1 UNINSTALL_MSG='Error: permission denied writing plugin cache') || result=$?
assert_eq "1" "$result" "exit code"
assert_contains "$output" "permission denied writing plugin cache" "should echo the captured CLI error"
assert_contains "$output" "failed to uninstall" "should abort on a non-benign uninstall failure"

set_test "marketplace present as a non-local source aborts clearly"
: > "$CALL_LOG"
result=0
output=$(run_claude_refresh MKT_MODE=github) || result=$?
assert_eq "1" "$result" "exit code"
assert_contains "$output" "not a local Directory source" "should explain the non-local marketplace"

set_test "marketplace pointing at another checkout aborts"
: > "$CALL_LOG"
result=0
output=$(run_claude_refresh MKT_MODE=elsewhere) || result=$?
assert_eq "1" "$result" "exit code"
assert_contains "$output" "points at '/some/other/checkout'" "should report the unexpected root"

set_test "absent marketplace is added"
: > "$CALL_LOG"
result=0
output=$(run_claude_refresh MKT_MODE=absent) || result=$?
assert_eq "0" "$result" "exit code"
calls=$(cat "$CALL_LOG")
assert_contains "$calls" "claude plugin marketplace add" "absent marketplace should be added"

set_test "marketplace inspection failure aborts"
: > "$CALL_LOG"
result=0
output=$(run_claude_refresh MKT_MODE=listfail) || result=$?
assert_eq "1" "$result" "exit code"
assert_contains "$output" "failed to inspect" "list failure should abort before mutating state"

set_test "non-benign Codex remove failure aborts"
: > "$CALL_LOG"
result=0
output=$(env REMOVE_RC=1 REMOVE_MSG='Error: disk failure' CALL_LOG="$CALL_LOG" STUB_REPO_ROOT="$REPO_ROOT" PATH="$FSTUB:$PATH" \
  bash "$SCRIPT" --no-build --no-validate --codex --no-claude-install 2>&1) || result=$?
assert_eq "1" "$result" "exit code"
assert_contains "$output" "failed to remove" "non-benign Codex remove failure should abort"

set_test "marketplace name with regex metacharacters matches its row literally"
: > "$CALL_LOG"
result=0
output=$(env SPECKIT_MARKETPLACE='my+plug-mkt' MKT_NAME='my+plug-mkt' \
  CALL_LOG="$CALL_LOG" STUB_REPO_ROOT="$REPO_ROOT" PATH="$FSTUB:$PATH" \
  bash "$SCRIPT" --no-build --no-validate --no-codex --claude-install 2>&1) || result=$?
assert_eq "0" "$result" "exit code"
assert_not_contains "$output" "Adding Claude marketplace" "metachar name should match its existing local row, not look absent"
calls=$(cat "$CALL_LOG")
assert_contains "$calls" "speckit-pro@my+plug-mkt" "should act on the metachar-named selector"

set_test "missing claude skips validation instead of aborting a Codex-only run"
: > "$CALL_LOG"
CODEX_ONLY="$TMP_ROOT/codex-only"
mkdir -p "$CODEX_ONLY"
cp "$FSTUB/codex" "$CODEX_ONLY/codex"
result=0
# PATH excludes the real claude binary but retains coreutils (awk, bash, ...).
output=$(CALL_LOG="$CALL_LOG" STUB_REPO_ROOT="$REPO_ROOT" PATH="$CODEX_ONLY:/usr/bin:/bin" \
  bash "$SCRIPT" --no-build --codex --no-claude-install 2>&1) || result=$?
assert_eq "0" "$result" "exit code"
assert_contains "$output" "skipping Claude payload validation" "missing claude should skip validation with a warning"
calls=$(cat "$CALL_LOG")
assert_contains "$calls" "codex plugin add speckit-pro@racecraft-plugins-public" "Codex refresh should still run without claude"

section "Argument validation"

set_test "invalid scope exits with usage error"
result=0
output=$(bash "$SCRIPT" --scope managed 2>&1) || result=$?
assert_eq "2" "$result" "exit code"
assert_contains "$output" "--scope must be one of" "should explain valid scopes"

set_test "unknown option exits with usage error"
result=0
output=$(bash "$SCRIPT" --wat 2>&1) || result=$?
assert_eq "2" "$result" "exit code"
assert_contains "$output" "unknown option" "should explain unknown option"

test_summary
