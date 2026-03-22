#!/usr/bin/env bash
# assertions.sh — Shared test utilities for speckit-pro plugin test suite
#
# Usage: source this file from any test script
#   source "$(dirname "$0")/../lib/assertions.sh"
#
# Provides: assert_eq, assert_contains, assert_not_contains,
#   assert_exit_code, assert_json_field, assert_file_exists,
#   assert_file_not_exists, test_summary
#
# Counters: PASS_COUNT, FAIL_COUNT, TEST_NAME

set -euo pipefail

PASS_COUNT=0
FAIL_COUNT=0
TEST_NAME=""
VERBOSE="${VERBOSE:-false}"

# Colors (disabled if not a terminal)
if [ -t 1 ]; then
  GREEN='\033[0;32m'
  RED='\033[0;31m'
  YELLOW='\033[0;33m'
  BOLD='\033[1m'
  RESET='\033[0m'
else
  GREEN='' RED='' YELLOW='' BOLD='' RESET=''
fi

# Set the current test name for reporting
set_test() {
  TEST_NAME="$1"
  if [ "$VERBOSE" = "true" ]; then
    printf "  %s ... " "$TEST_NAME"
  fi
}

_pass() {
  (( PASS_COUNT += 1 ))
  if [ "$VERBOSE" = "true" ]; then
    printf "${GREEN}PASS${RESET}\n"
  fi
}

_fail() {
  local msg="${1:-}"
  (( FAIL_COUNT += 1 ))
  if [ "$VERBOSE" = "true" ]; then
    printf "${RED}FAIL${RESET}\n"
    [ -n "$msg" ] && printf "    ${RED}%s${RESET}\n" "$msg"
  else
    printf "${RED}FAIL${RESET}: %s\n" "$TEST_NAME"
    [ -n "$msg" ] && printf "  ${RED}%s${RESET}\n" "$msg"
  fi
}

# assert_eq <expected> <actual> [message]
assert_eq() {
  local expected="$1" actual="$2" msg="${3:-}"
  if [ "$expected" = "$actual" ]; then
    _pass
  else
    _fail "${msg:+$msg: }expected '$expected', got '$actual'"
  fi
}

# assert_contains <haystack> <needle> [message]
assert_contains() {
  local haystack="$1" needle="$2" msg="${3:-}"
  if [[ "$haystack" == *"$needle"* ]]; then
    _pass
  else
    _fail "${msg:+$msg: }expected to contain '$needle'"
  fi
}

# assert_not_contains <haystack> <needle> [message]
assert_not_contains() {
  local haystack="$1" needle="$2" msg="${3:-}"
  if [[ "$haystack" != *"$needle"* ]]; then
    _pass
  else
    _fail "${msg:+$msg: }expected NOT to contain '$needle'"
  fi
}

# assert_exit_code <expected_code> <command...>
# Runs the command and checks the exit code
assert_exit_code() {
  local expected="$1"
  shift
  local actual=0
  "$@" >/dev/null 2>&1 || actual=$?
  if [ "$expected" -eq "$actual" ]; then
    _pass
  else
    _fail "expected exit code $expected, got $actual"
  fi
}

# assert_exit_code_capture <expected_code> <var_name> <command...>
# Runs the command, checks exit code, and captures stdout into var_name
assert_exit_code_capture() {
  local expected="$1" var_name="$2"
  shift 2
  local actual=0 output
  output=$("$@" 2>/dev/null) || actual=$?
  eval "$var_name=\$output"
  if [ "$expected" -eq "$actual" ]; then
    _pass
  else
    _fail "expected exit code $expected, got $actual"
  fi
}

# assert_json_field <json_string> <field> <expected_value> [message]
# Uses python3 for JSON parsing (available on macOS)
assert_json_field() {
  local json="$1" field="$2" expected="$3" msg="${4:-}"
  local actual
  actual=$(printf '%s' "$json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
keys = '$field'.split('.')
val = data
for k in keys:
    val = val[k]
print(val)
" 2>/dev/null) || {
    _fail "${msg:+$msg: }failed to parse JSON field '$field'"
    return
  }
  if [ "$expected" = "$actual" ]; then
    _pass
  else
    _fail "${msg:+$msg: }field '$field': expected '$expected', got '$actual'"
  fi
}

# assert_json_field_exists <json_string> <field> [message]
assert_json_field_exists() {
  local json="$1" field="$2" msg="${3:-}"
  printf '%s' "$json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
keys = '$field'.split('.')
val = data
for k in keys:
    val = val[k]
" 2>/dev/null
  if [ $? -eq 0 ]; then
    _pass
  else
    _fail "${msg:+$msg: }JSON field '$field' does not exist"
  fi
}

# assert_file_exists <path> [message]
assert_file_exists() {
  local path="$1" msg="${2:-}"
  if [ -f "$path" ]; then
    _pass
  else
    _fail "${msg:+$msg: }file not found: $path"
  fi
}

# assert_file_not_exists <path> [message]
assert_file_not_exists() {
  local path="$1" msg="${2:-}"
  if [ ! -f "$path" ]; then
    _pass
  else
    _fail "${msg:+$msg: }file should not exist: $path"
  fi
}

# assert_file_executable <path> [message]
assert_file_executable() {
  local path="$1" msg="${2:-}"
  if [ -x "$path" ]; then
    _pass
  else
    _fail "${msg:+$msg: }file not executable: $path"
  fi
}

# assert_match <string> <regex> [message]
assert_match() {
  local string="$1" regex="$2" msg="${3:-}"
  if [[ "$string" =~ $regex ]]; then
    _pass
  else
    _fail "${msg:+$msg: }expected to match regex '$regex'"
  fi
}

# assert_gt <actual> <threshold> [message]
# Assert actual > threshold (numeric)
assert_gt() {
  local actual="$1" threshold="$2" msg="${3:-}"
  if [ "$actual" -gt "$threshold" ]; then
    _pass
  else
    _fail "${msg:+$msg: }expected $actual > $threshold"
  fi
}

# Print section header
section() {
  printf "\n${BOLD}%s${RESET}\n" "$1"
}

# Print test summary and exit with appropriate code
test_summary() {
  local total=$((PASS_COUNT + FAIL_COUNT))
  local script_name
  script_name=$(basename "${BASH_SOURCE[1]:-$0}" .sh)

  printf "\n${BOLD}%s${RESET}: " "$script_name"
  if [ "$FAIL_COUNT" -eq 0 ]; then
    printf "${GREEN}%d/%d passed${RESET}\n" "$PASS_COUNT" "$total"
  else
    printf "${RED}%d/%d passed (%d failed)${RESET}\n" \
      "$PASS_COUNT" "$total" "$FAIL_COUNT"
  fi

  [ "$FAIL_COUNT" -eq 0 ]
}
