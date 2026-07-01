#!/usr/bin/env bash
# check-toolchain.sh - Report and validate local tools used by speckit-pro checks.
#
# Usage:
#   bash tests/speckit-pro/check-toolchain.sh --mode tests
#   bash tests/speckit-pro/check-toolchain.sh --mode shell
#   bash tests/speckit-pro/check-toolchain.sh --mode docs
#   bash tests/speckit-pro/check-toolchain.sh --mode all

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MODE="tests"

print_help() {
  cat <<'EOF'
check-toolchain.sh - Report and validate local tools used by speckit-pro checks.

Usage:
  bash tests/speckit-pro/check-toolchain.sh --mode tests
  bash tests/speckit-pro/check-toolchain.sh --mode shell
  bash tests/speckit-pro/check-toolchain.sh --mode docs
  bash tests/speckit-pro/check-toolchain.sh --mode all
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --mode)
      if [ "$#" -lt 2 ] || [ -z "${2:-}" ]; then
        printf 'Missing value for --mode\n' >&2
        exit 2
      fi
      MODE="${2:-}"
      shift 2
      ;;
    --mode=*)
      MODE="${1#--mode=}"
      shift
      ;;
    -h|--help)
      print_help
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 2
      ;;
  esac
done

case "$MODE" in
  tests|shell|docs|all) ;;
  *)
    printf 'Invalid --mode: %s\n' "$MODE" >&2
    exit 2
    ;;
esac

PASS_COUNT=0
FAIL_COUNT=0

pass() {
  printf 'PASS %-28s %s\n' "$1" "${2:-}"
  PASS_COUNT=$((PASS_COUNT + 1))
}

fail() {
  printf 'FAIL %-28s %s\n' "$1" "${2:-}"
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

warn() {
  printf 'WARN %-28s %s\n' "$1" "${2:-}"
}

# Optional tools that happen to be present are reported but NOT scored, so the
# pass/total count is identical across machines regardless of which optional
# tools are installed. Scoring them would make the number environment-dependent.
info() {
  printf 'INFO %-28s %s\n' "$1" "${2:-}"
}

cmd_path() {
  command -v "$1" 2>/dev/null || true
}

require_cmd() {
  local label="$1" cmd="$2" path
  path="$(cmd_path "$cmd")"
  if [ -n "$path" ]; then
    pass "$label" "$path"
  else
    fail "$label" "required command not found: $cmd"
  fi
}

optional_cmd() {
  local label="$1" cmd="$2" note="$3" path
  path="$(cmd_path "$cmd")"
  if [ -n "$path" ]; then
    info "$label" "$path"
  else
    warn "$label" "not found; required only for $note"
  fi
}

version_at_least() {
  local version="$1" min_major="$2" min_minor="$3" major minor
  IFS=. read -r major minor _rest <<EOF
$version
EOF
  major="${major:-0}"
  minor="${minor:-0}"
  case "$major" in *[!0-9]*|'') return 1 ;; esac
  case "$minor" in *[!0-9]*|'') minor=0 ;; esac
  [ "$major" -gt "$min_major" ] || { [ "$major" -eq "$min_major" ] && [ "$minor" -ge "$min_minor" ]; }
}

check_bash() {
  local version="${BASH_VERSION:-unknown}"
  local major="${BASH_VERSINFO[0]:-0}"
  local minor="${BASH_VERSINFO[1]:-0}"
  if [ "$major" -gt 4 ] || { [ "$major" -eq 4 ] && [ "$minor" -ge 3 ]; }; then
    pass "bash >= 4.3" "$version"
  else
    fail "bash >= 4.3" "$version; install a newer Bash before running the shell suite"
  fi
}

check_jq() {
  local path version numeric
  path="$(cmd_path jq)"
  if [ -z "$path" ]; then
    fail "jq >= 1.6" "required command not found: jq"
    return
  fi

  version="$(jq --version 2>/dev/null || true)"
  numeric="$(printf '%s\n' "$version" | sed -E 's/^jq-?//; s/[^0-9.].*$//')"
  if ! version_at_least "$numeric" 1 6; then
    fail "jq >= 1.6" "${version:-unknown}; install jq 1.6 or newer"
    return
  fi

  if printf '{"ok":true}\n' | jq -e '.ok == true' >/dev/null 2>&1; then
    pass "jq >= 1.6" "$version ($path)"
  else
    fail "jq expression" "jq --version succeeded but a minimal expression failed"
  fi
}

check_sort_version_semantics() {
  local newest
  if ! printf '%s\n%s\n' "1.10.2" "1.9.10" | sort -V >/dev/null 2>&1; then
    fail "sort -V" "version sort is required for semver-style plugin sync checks"
    return
  fi

  newest="$(printf '%s\n%s\n' "1.10.2" "1.9.10" | sort -V | tail -n 1)"
  if [ "$newest" = "1.10.2" ]; then
    pass "sort -V" "semver ordering available"
  else
    fail "sort -V" "expected 1.10.2 > 1.9.10, got $newest"
  fi
}

check_checksum_tool() {
  if command -v sha256sum >/dev/null 2>&1; then
    pass "sha256" "sha256sum ($(cmd_path sha256sum))"
  elif command -v shasum >/dev/null 2>&1; then
    pass "sha256" "shasum ($(cmd_path shasum))"
  else
    fail "sha256" "sha256sum or shasum is required for packet fingerprints"
  fi
}

check_yaml_validator() {
  if python3 -c 'import yaml' >/dev/null 2>&1; then
    pass "yaml validator" "python3 PyYAML"
  elif ruby -e "require 'yaml'" >/dev/null 2>&1; then
    pass "yaml validator" "ruby yaml"
  else
    fail "yaml validator" "python3 with PyYAML or ruby is required for workflow YAML checks"
  fi
}

check_shell_tools() {
  local label="${1:-shell}"
  printf 'speckit-pro toolchain check (%s)\n' "$label"
  check_bash
  check_jq
  require_cmd "git" git
  require_cmd "python3" python3

  for cmd in awk sed grep sort find mktemp wc head tail cut dirname basename pwd; do
    require_cmd "$cmd" "$cmd"
  done

  check_sort_version_semantics
  check_checksum_tool

  optional_cmd "gh" gh "PR creation, review-comment workflows, and live GitHub-backed checks"
  optional_cmd "specify" specify "installed-plugin Spec Kit workflows"
  optional_cmd "claude" claude "Claude live eval and integration fixture modes"
  optional_cmd "codex" codex "Codex trigger, functional, and efficiency eval modes"
}

check_test_tools() {
  check_shell_tools "tests"
  check_yaml_validator
}

check_docs_tools() {
  local node_version node_numeric package_manager pnpm_version
  printf 'speckit-pro toolchain check (docs)\n'
  require_cmd "node" node
  require_cmd "corepack" corepack
  require_cmd "pnpm" pnpm

  if command -v node >/dev/null 2>&1; then
    node_version="$(node --version 2>/dev/null || true)"
    node_numeric="$(printf '%s\n' "$node_version" | sed -E 's/^v//; s/[^0-9.].*$//')"
    if version_at_least "$node_numeric" 22 0; then
      pass "node >= 22" "$node_version"
    else
      fail "node >= 22" "${node_version:-unknown}; expected Node 22 or newer"
    fi
  fi

  if command -v pnpm >/dev/null 2>&1; then
    pnpm_version="$(pnpm --version 2>/dev/null || true)"
    if [ "$pnpm_version" = "10.25.0" ]; then
      pass "pnpm version" "$pnpm_version"
    else
      fail "pnpm version" "${pnpm_version:-unknown}; expected 10.25.0"
    fi
  fi

  if [ -f "$REPO_ROOT/docs-site/package.json" ] && command -v python3 >/dev/null 2>&1; then
    package_manager="$(python3 - "$REPO_ROOT/docs-site/package.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as f:
    print(json.load(f).get("packageManager", ""))
PY
)"
    if [ "$package_manager" = "pnpm@10.25.0" ]; then
      pass "docs packageManager" "$package_manager"
    else
      fail "docs packageManager" "${package_manager:-missing}; expected pnpm@10.25.0"
    fi
  fi

  if command -v pnpm >/dev/null 2>&1 && [ -d "$REPO_ROOT/docs-site/node_modules" ]; then
    if pnpm --dir "$REPO_ROOT/docs-site" exec playwright --version >/dev/null 2>&1; then
      pass "playwright package" "$(pnpm --dir "$REPO_ROOT/docs-site" exec playwright --version 2>/dev/null)"
    else
      fail "playwright package" "run pnpm --dir docs-site install --frozen-lockfile first"
    fi
  else
    fail "docs dependencies" "run pnpm --dir docs-site install --frozen-lockfile first"
  fi
}

cd "$REPO_ROOT"

case "$MODE" in
  tests)
    check_test_tools
    ;;
  shell)
    check_shell_tools "shell"
    ;;
  docs)
    check_docs_tools
    ;;
  all)
    check_test_tools
    check_docs_tools
    ;;
esac

TOTAL_COUNT=$((PASS_COUNT + FAIL_COUNT))
if [ "$FAIL_COUNT" -eq 0 ]; then
  printf '\ncheck-toolchain: %d/%d passed\n' "$PASS_COUNT" "$TOTAL_COUNT"
else
  printf '\ncheck-toolchain: %d/%d passed (%d failed)\n' \
    "$PASS_COUNT" "$TOTAL_COUNT" "$FAIL_COUNT"
  printf 'toolchain check failed: %d issue(s)\n' "$FAIL_COUNT" >&2
  exit 1
fi
