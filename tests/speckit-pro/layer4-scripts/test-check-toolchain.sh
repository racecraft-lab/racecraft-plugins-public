#!/usr/bin/env bash
# Tests for the speckit-pro toolchain preflight.
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
CHECKER="$REPO_ROOT/tests/speckit-pro/check-toolchain.sh"
BASH_BIN="${BASH:-$(command -v bash)}"
TMP_DIR="$(mktemp -d)"
LAST_OUTPUT=""
LAST_EXIT=0

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

run_checker() {
  LAST_EXIT=0
  LAST_OUTPUT="$(bash "$CHECKER" "$@" 2>&1)" || LAST_EXIT=$?
}

run_checker_with_path() {
  local fixture_path="$1"
  shift
  LAST_EXIT=0
  LAST_OUTPUT="$(PATH="$fixture_path" "$BASH_BIN" "$CHECKER" "$@" 2>&1)" || LAST_EXIT=$?
}

make_path_fixture() {
  local name="$1" omit="${2:-}" bin_dir cmd path
  bin_dir="$TMP_DIR/$name"
  mkdir -p "$bin_dir"

  for cmd in awk sed grep sort find mktemp wc head tail cut dirname basename git python3 jq sha256sum shasum ruby; do
    [ "$cmd" = "$omit" ] && continue
    path="$(command -v "$cmd" 2>/dev/null || true)"
    if [ -n "$path" ] && [ "$path" != "$cmd" ]; then
      ln -s "$path" "$bin_dir/$cmd"
    fi
  done

  printf '%s\n' "$bin_dir"
}

write_fake_python_without_yaml() {
  local bin_dir="$1"
  cat > "$bin_dir/python3" <<'SH'
#!/bin/sh
if [ "${1:-}" = "-c" ]; then
  case "${2:-}" in
    *"import yaml"*) exit 1 ;;
  esac
fi
exit 0
SH
  chmod 0755 "$bin_dir/python3"
}

write_fake_jq() {
  local bin_dir="$1" version="$2" expression_exit="${3:-0}"
  cat > "$bin_dir/jq" <<SH
#!/bin/sh
if [ "\${1:-}" = "--version" ]; then
  printf '%s\n' "$version"
  exit 0
fi
exit "$expression_exit"
SH
  chmod 0755 "$bin_dir/jq"
}

section "check-toolchain.sh"

set_test "toolchain checker exists"
assert_file_exists "$CHECKER"

set_test "toolchain checker is executable"
assert_file_executable "$CHECKER"

set_test "help exits 0"
run_checker --help
assert_eq "0" "$LAST_EXIT"

set_test "help lists supported modes"
assert_contains "$LAST_OUTPUT" "--mode all"

set_test "help does not include shell code"
assert_not_contains "$LAST_OUTPUT" "set -euo pipefail"

set_test "default tests mode exits 0"
run_checker
assert_eq "0" "$LAST_EXIT"

set_test "default tests mode prints summary"
assert_contains "$LAST_OUTPUT" "check-toolchain:"

set_test "shell mode exits 0"
run_checker --mode shell
assert_eq "0" "$LAST_EXIT"

set_test "shell mode labels output"
assert_contains "$LAST_OUTPUT" "speckit-pro toolchain check (shell)"

set_test "missing --mode value exits 2"
run_checker --mode
assert_eq "2" "$LAST_EXIT"

set_test "missing --mode value prints a diagnostic"
assert_contains "$LAST_OUTPUT" "Missing value for --mode"

set_test "invalid --mode value exits 2"
run_checker --mode invalid
assert_eq "2" "$LAST_EXIT"

set_test "invalid --mode value prints a diagnostic"
assert_contains "$LAST_OUTPUT" "Invalid --mode: invalid"

set_test "unknown argument exits 2"
run_checker --bogus
assert_eq "2" "$LAST_EXIT"

set_test "missing jq exits 1"
missing_jq_path="$(make_path_fixture missing-jq jq)"
run_checker_with_path "$missing_jq_path"
assert_eq "1" "$LAST_EXIT"

set_test "missing jq prints diagnostic"
assert_contains "$LAST_OUTPUT" "required command not found: jq"

set_test "missing jq still prints summary"
assert_contains "$LAST_OUTPUT" "check-toolchain:"

set_test "broken jq expression exits 1"
broken_jq_path="$(make_path_fixture broken-jq jq)"
write_fake_jq "$broken_jq_path" "jq-1.7" "2"
run_checker_with_path "$broken_jq_path"
assert_eq "1" "$LAST_EXIT"

set_test "broken jq expression prints diagnostic"
assert_contains "$LAST_OUTPUT" "jq expression"

set_test "too-old jq exits 1"
old_jq_path="$(make_path_fixture old-jq jq)"
write_fake_jq "$old_jq_path" "jq-1.5" "0"
run_checker_with_path "$old_jq_path"
assert_eq "1" "$LAST_EXIT"

set_test "too-old jq prints diagnostic"
assert_contains "$LAST_OUTPUT" "install jq 1.6 or newer"

set_test "missing python3 exits 1"
missing_python_path="$(make_path_fixture missing-python python3)"
run_checker_with_path "$missing_python_path"
assert_eq "1" "$LAST_EXIT"

set_test "missing python3 prints diagnostic"
assert_contains "$LAST_OUTPUT" "required command not found: python3"

set_test "tests mode fails without YAML validator"
missing_yaml_path="$(make_path_fixture missing-yaml python3)"
rm -f "$missing_yaml_path/ruby"
write_fake_python_without_yaml "$missing_yaml_path"
run_checker_with_path "$missing_yaml_path" --mode tests
assert_eq "1" "$LAST_EXIT"

set_test "tests mode reports missing YAML validator"
assert_contains "$LAST_OUTPUT" "yaml validator"

set_test "shell mode does not require YAML validator"
run_checker_with_path "$missing_yaml_path" --mode shell
assert_eq "0" "$LAST_EXIT"

test_summary
