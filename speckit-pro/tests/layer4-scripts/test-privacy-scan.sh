#!/usr/bin/env bash
# Layer 4 privacy regression guard for committed and untracked current-tree files.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$TESTS_ROOT/../.." && pwd)"

source "$TESTS_ROOT/lib/assertions.sh"

if ! command -v rg >/dev/null 2>&1; then
  echo "test-privacy-scan: rg is required" >&2
  exit 2
fi

first="Fre"
first="${first}drick"
last="Gab"
last="${last}elmann"
handle="fgab"
handle="${handle}elmannjr"
home_user="fred"
home_user="${home_user}rick"
home_user="${home_user}gabel"
home_user="${home_user}mann"
home_path="/"
home_path="${home_path}Users/${home_user}"
third_party_local="dave"
third_party_local="${third_party_local}.sharpe"
third_party_domain="datastone"
third_party_domain="${third_party_domain}.ca"
business_docs="Business""_Documents"
business_docs_dash="Business""-Documents"
rse_docs="RSE""_Documents"
rse_docs_dash="RSE""-Documents"
private_var="/private/var/"
private_var="${private_var}folders"
tmp_transcript="/private/tmp/"
tmp_transcript="${tmp_transcript}claude"
uuid_pattern="[[:xdigit:]]{8}-[[:xdigit:]]{4}-[[:xdigit:]]{4}-[[:xdigit:]]{4}-[[:xdigit:]]{12}"
split_home="/fr"
split_home="${split_home}ed"
split_user="rick"
split_user="${split_user}gabel"
split_business="business"
split_business="${split_business}_docum"
split_rse="rse"
split_rse="${split_rse}_docum"
split_path_fragments="${split_home}|${split_user}|${split_business}|${split_rse}"

scan_for() {
  local pattern="$1"
  (
    cd "$REPO_ROOT"
    rg -n --hidden -S -i "$pattern" -g '!/.git' -g '!/.git/**' .
  )
}

assert_no_match() {
  local label="$1"
  local pattern="$2"
  local hits=""

  if hits=$(scan_for "$pattern"); then
    _fail "$label leaked into current tree: $(printf '%s\n' "$hits" | head -3 | tr '\n' '; ')"
  else
    _pass
  fi
}

section "current tree privacy scan"

set_test "personal first name absent"
assert_no_match "$TEST_NAME" "$first"

set_test "personal last name absent"
assert_no_match "$TEST_NAME" "$last"

set_test "personal handle absent"
assert_no_match "$TEST_NAME" "$handle"

set_test "personal work email absent"
assert_no_match "$TEST_NAME" "${handle}@racecraft.co"

set_test "personal noreply email absent"
assert_no_match "$TEST_NAME" "${handle}@users.noreply.github.com"

set_test "third-party personal email absent"
assert_no_match "$TEST_NAME" "${third_party_local}@${third_party_domain}"

set_test "local home path absent"
assert_no_match "$TEST_NAME" "$home_path"

set_test "workspace path fragments absent"
assert_no_match "$TEST_NAME" "${business_docs}|${business_docs_dash}|${rse_docs}|${rse_docs_dash}"

set_test "specific temp transcript path absent"
assert_no_match "$TEST_NAME" "${tmp_transcript}-[0-9]+"

set_test "specific macOS temp folder path absent"
assert_no_match "$TEST_NAME" "$private_var"

set_test "raw UUIDs absent"
assert_no_match "$TEST_NAME" "$uuid_pattern"

set_test "split local path fragments absent"
assert_no_match "$TEST_NAME" "$split_path_fragments"

test_summary
