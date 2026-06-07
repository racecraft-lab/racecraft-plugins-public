#!/usr/bin/env bash
# validate-process-gitattributes.sh — Verifies the repo-root .gitattributes
# collapse rule is scoped to .process/ ONLY (FR-012 / AC-2.4 / SC-005).
#
# Every `linguist-generated` rule MUST target a path carrying the `.process/`
# segment. A rule broadened to a path that could include a CONTRACT artifact
# (spec.md / plan.md / tasks.md / research.md / data-model.md / contracts/** /
# checklists/** / SPEC-MOC.md / *-technical-roadmap.md) MUST fail the lint.
#
# This lint validates the STATIC file only — it does NOT make the reviewability
# gate parse .gitattributes (the gate stays self-contained per FR-011; the
# intentional duplication between the gate's hardcoded glob and this rule is
# exactly what this lint guards against drift).
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

# layer1-structural -> tests -> speckit-pro -> repo root (where .gitattributes lives).
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
GITATTRIBUTES="$REPO_ROOT/.gitattributes"

# Pure predicate: returns 0 if EVERY linguist-generated line in the file is
# scoped to a `.process/` path segment, 1 if any such line is broadened beyond
# `.process/`. Returns 0 for a file with no linguist-generated lines (nothing to
# broaden). Kept side-effect-free so the negative fixture below is a PASS, not a
# polluted FAIL_COUNT.
rules_scoped() {
  local file="$1" rc=0 line
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      \#*|'') continue ;;          # skip comments and blank lines
    esac
    case "$line" in
      *linguist-generated*)
        case "$line" in
          */.process/*|.process/*) ;;  # scoped to the /.process/ segment — ok
          *) rc=1 ;;               # broadened beyond .process/ (e.g. foo.process/) — fail
        esac
        ;;
    esac
  done < "$file"
  return "$rc"
}

section ".gitattributes — Collapse Rule Scope"

# Load-bearing RED trigger: fails until the repo-root .gitattributes exists
# (T004). Unconditional so a missing file is a real assertion failure.
set_test "repo-root .gitattributes exists"
assert_file_exists "$GITATTRIBUTES"

# Guard the file-reading scope check so a missing file produces the single clean
# failure above rather than a set -e crash.
if [ -f "$GITATTRIBUTES" ]; then
  set_test "at least one linguist-generated rule is present"
  if grep -q 'linguist-generated' "$GITATTRIBUTES"; then
    _pass
  else
    _fail "no linguist-generated rule found in repo-root .gitattributes"
  fi

  set_test "every linguist-generated rule is scoped to .process/"
  if rules_scoped "$GITATTRIBUTES"; then
    _pass
  else
    _fail "a linguist-generated rule is broadened beyond .process/ (could match a CONTRACT artifact)"
  fi
fi

section ".gitattributes — Scope Predicate (SC-005 positive + negative)"

good_fixture="$(mktemp)"
bad_fixture="$(mktemp)"
trap 'rm -f "$good_fixture" "$bad_fixture"' EXIT

# Positive case: a .process/-scoped rule passes.
printf '%s\n' '**/.process/** linguist-generated=true' > "$good_fixture"
# Negative case: a broadened rule that would match CONTRACT artifacts fails.
printf '%s\n' '**/* linguist-generated=true' > "$bad_fixture"

set_test "scoped rule passes (SC-005 positive case)"
assert_exit_code 0 rules_scoped "$good_fixture"

set_test "broadened rule fails (SC-005 negative case)"
assert_exit_code 1 rules_scoped "$bad_fixture"

# Regression guard (PR #111 review): a rule targeting a directory that merely
# ENDS in ".process" (foo.process/) is NOT the dedicated .process/ exhaust dir
# and MUST fail — the earlier *.process/* predicate wrongly accepted it.
ends_in_process_fixture="$(mktemp)"
printf '%s\n' '**/foo.process/** linguist-generated=true' > "$ends_in_process_fixture"
set_test "rule for a dir ending in .process (foo.process/) fails — not the .process/ dir"
assert_exit_code 1 rules_scoped "$ends_in_process_fixture"
rm -f "$ends_in_process_fixture"

test_summary
