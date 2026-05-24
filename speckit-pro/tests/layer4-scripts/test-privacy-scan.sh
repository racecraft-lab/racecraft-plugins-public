#!/usr/bin/env bash
# Layer 4 privacy regression guard for committed and untracked current-tree files.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$TESTS_ROOT/../.." && pwd)"

source "$TESTS_ROOT/lib/assertions.sh"

if ! command -v git >/dev/null 2>&1; then
  echo "test-privacy-scan: git is required" >&2
  exit 2
fi

EMAIL_PATTERN='[[:alnum:]_.%+-]+@[[:alnum:].-]+[.][[:alpha:]]{2,}'
HOME_PATH_PATTERN='/(Users|home)/[[:alnum:]_.-]+'
HYPHENATED_HOME_PATH_PATTERN='-[Uu]sers-[[:alnum:]_.-]+'
PRIVATE_VAR_PATTERN='/private/var/folders/[[:alnum:]_/.-]+'
TMP_TRANSCRIPT_PATTERN='/private/tmp/claude-[0-9]+'
UUID_PATTERN='[[:xdigit:]]{8}-[[:xdigit:]]{4}-[[:xdigit:]]{4}-[[:xdigit:]]{4}-[[:xdigit:]]{12}'

TOOLING_SOURCE_PATHS=(
  "speckit-pro/tests/layer4-scripts/test-privacy-scan.sh"
  "speckit-pro/tests/layer7-integration/scrub-transcript.sh"
)

scan_for() {
  local pattern="$1"
  if command -v rg >/dev/null 2>&1; then
    (
      cd "$REPO_ROOT"
      rg -n --hidden -S -i -g '!/.git' -g '!/.git/**' -- "$pattern" .
    )
  else
    (
      cd "$REPO_ROOT"
      grep -RInE -i --exclude-dir=.git -- "$pattern" .
    )
  fi
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

assert_no_non_allowlisted_email() {
  local label="$1"
  local hits=""

  hits=$(scan_for "$EMAIL_PATTERN" || true)
  hits=$(printf '%s\n' "$hits" | grep -Eiv 'support@openai[.]com|git@github[.]com' || true)
  if [ -n "$hits" ]; then
    _fail "$label leaked into current tree: $(printf '%s\n' "$hits" | head -3 | tr '\n' '; ')"
  else
    _pass
  fi
}

regex_escape() {
  printf '%s' "$1" | sed 's/[][(){}.^$+*?|\\]/\\&/g'
}

is_sensitive_local_term() {
  local term="$1"
  term=$(printf '%s' "$term" | tr '[:upper:]' '[:lower:]')
  [ "${#term}" -ge 5 ] || return 1

  case "$term" in
    actions|admin|build|cache|claude|codex|documents|downloads|github|home|integration|layer4|layer7|local|main|openai|plugins|private|project|projects|public|racecraft|repo|root|runner|speckit|staff|support|tests|users|work|worktrees)
      return 1
      ;;
  esac

  case "$term" in
    racecraft-*|speckit-*|test-*|layer*-*)
      return 1
      ;;
  esac

  return 0
}

emit_sensitive_terms_from_value() {
  local value="$1"
  local part compact lower i

  while IFS= read -r part; do
    lower=$(printf '%s' "$part" | tr '[:upper:]' '[:lower:]')
    lower="${lower#.}"
    if is_sensitive_local_term "$lower"; then
      printf '%s\n' "$lower"
    fi

    compact=$(printf '%s' "$lower" | tr -cd '[:alnum:]')
    if is_sensitive_local_term "$compact"; then
      printf '%s\n' "$compact"
    fi

    case "$compact" in
      *document*|*project*|*racecraft*|*speckit*|*plugin*)
        continue
        ;;
    esac

    if [ "${#compact}" -ge 12 ]; then
      for ((i = 0; i <= ${#compact} - 8; i++)); do
        printf '%s\n' "${compact:i:8}"
      done
    fi
  done < <(printf '%s' "$value" | tr -cs '[:alnum:]_.-' '\n')
}

build_dynamic_local_pattern() {
  local git_name git_email email_local
  git_name=$(git -C "$REPO_ROOT" config --get user.name 2>/dev/null || true)
  git_email=$(git -C "$REPO_ROOT" config --get user.email 2>/dev/null || true)
  email_local="${git_email%@*}"

  {
    emit_sensitive_terms_from_value "${HOME:-}"
    emit_sensitive_terms_from_value "${USER:-}"
    emit_sensitive_terms_from_value "${LOGNAME:-}"
    emit_sensitive_terms_from_value "$git_name"
    emit_sensitive_terms_from_value "$email_local"
    emit_sensitive_terms_from_value "$REPO_ROOT"
  } \
    | while IFS= read -r term; do
        if is_sensitive_local_term "$term"; then
          regex_escape "$term"
          printf '\n'
        fi
      done \
    | sort -u \
    | paste -sd'|' -
}

assert_no_tooling_source_match() {
  local label="$1"
  local pattern="$2"
  local hits=""

  if hits=$(
    cd "$REPO_ROOT"
    if command -v rg >/dev/null 2>&1; then
      rg -n --hidden -S -i -- "$pattern" "${TOOLING_SOURCE_PATHS[@]}"
    else
      grep -nE -i -- "$pattern" "${TOOLING_SOURCE_PATHS[@]}"
    fi
  ); then
    _fail "$label leaked into privacy tooling: $(printf '%s\n' "$hits" | head -3 | tr '\n' '; ')"
  else
    _pass
  fi
}

section "current tree privacy scan"

dynamic_local_pattern="$(build_dynamic_local_pattern)"

set_test "non-allowlisted email addresses absent"
assert_no_non_allowlisted_email "$TEST_NAME"

set_test "absolute local home paths absent"
assert_no_match "$TEST_NAME" "$HOME_PATH_PATTERN"

set_test "hyphenated local home path dumps absent"
assert_no_match "$TEST_NAME" "$HYPHENATED_HOME_PATH_PATTERN"

set_test "specific temp transcript path absent"
assert_no_match "$TEST_NAME" "$TMP_TRANSCRIPT_PATTERN"

set_test "specific macOS temp folder path absent"
assert_no_match "$TEST_NAME" "$PRIVATE_VAR_PATTERN"

set_test "raw UUIDs absent"
assert_no_match "$TEST_NAME" "$UUID_PATTERN"

set_test "dynamic local identity and workspace terms absent"
if [ -n "$dynamic_local_pattern" ]; then
  assert_no_match "$TEST_NAME" "$dynamic_local_pattern"
else
  _pass
fi

set_test "privacy tooling does not encode local identity fragments"
if [ -n "$dynamic_local_pattern" ]; then
  assert_no_tooling_source_match "$TEST_NAME" "$dynamic_local_pattern"
else
  _pass
fi

set_test "Layer 7 replay fixtures do not commit captured raw transcript files"
if git -C "$REPO_ROOT" ls-files 'speckit-pro/tests/layer7-integration/**/transcript.jsonl' | grep -q .; then
  _fail "committed transcript.jsonl fixture found"
else
  _pass
fi

test_summary
