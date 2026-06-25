#!/usr/bin/env bash
# run-grounding-fixtures.sh — Layer 7 Class 4 fixture runner
#
# Proves the GROUNDING contract is verifiable from a run transcript:
#   - every grounded claim cites a capability that was ACTUALLY invoked
#     (a tool_use exists for it), and
#   - a fabricated citation (cited tool with no matching tool_use) is DETECTED.
#
# The negative-control fixture (02-fabricated-citation) declares
# expect_grounding_verdict="ungrounded": the suite stays green only because the
# check correctly flags the fabrication. If the grounding check ever rubber-
# stamps that fixture as "grounded", this runner fails — which is the point.
#
# These are hand-authored parser fixtures (deterministic transcript logic), so
# --replay and --live both evaluate the committed parser-fixture.jsonl; there is
# no live capture step for this class.
#
# Usage:
#   bash run-grounding-fixtures.sh                      # all fixtures
#   bash run-grounding-fixtures.sh 02-fabricated-citation
#   bash run-grounding-fixtures.sh --replay | --live    # both use parser fixtures

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LIB="$SCRIPT_DIR/lib/transcript-helpers.sh"
FIXTURES_DIR="$SCRIPT_DIR/grounding-fixtures"

# shellcheck disable=SC1091
source "$TESTS_ROOT/lib/assertions.sh"
# shellcheck disable=SC1090
source "$LIB"

SELECTED=""
while [ $# -gt 0 ]; do
  case "$1" in
    --replay|--live) shift ;;        # both modes use the committed parser fixture
    -h|--help) sed -n '2,20p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) SELECTED="$1"; shift ;;
  esac
done

collect_fixtures() {
  if [ -n "$SELECTED" ]; then
    if [ -d "$FIXTURES_DIR/$SELECTED" ]; then
      printf '%s\n' "$FIXTURES_DIR/$SELECTED"
    else
      printf "ERROR: fixture not found: %s\n" "$SELECTED" >&2
      exit 2
    fi
  else
    find "$FIXTURES_DIR" -mindepth 1 -maxdepth 1 -type d | sort
  fi
}

assert_fixture() {
  local fixture_dir="$1"
  local fixture_id
  fixture_id=$(basename "$fixture_dir")
  local expected="$fixture_dir/expected.json"
  local transcript="$fixture_dir/parser-fixture.jsonl"

  set_test "$fixture_id: expected.json present"
  if [ -f "$expected" ]; then _pass; else _fail "missing $expected"; return; fi

  set_test "$fixture_id: parser-fixture.jsonl present"
  if [ -f "$transcript" ]; then _pass; else _fail "missing $transcript"; return; fi

  # Grounding verdict matches the declared expectation (incl. the negative
  # control, which must be flagged 'ungrounded').
  if jq -e '.expect_grounding_verdict' "$expected" >/dev/null 2>&1; then
    local want got
    want=$(jq -r '.expect_grounding_verdict' "$expected")
    got=$(grounding_verdict "$transcript")
    set_test "$fixture_id: grounding verdict is '$want' (got '$got')"
    if [ "$got" = "$want" ]; then _pass; else
      _fail "expected grounding verdict '$want', got '$got'"
    fi
  fi

  # Distinct cited-capability count. extract_capability_citations is `sort -u`,
  # so this counts UNIQUE capability tokens the answer cites, not total
  # occurrences (citing the same tool twice still counts once).
  if jq -e '.expect_citation_count' "$expected" >/dev/null 2>&1; then
    local want_n got_n
    want_n=$(jq -r '.expect_citation_count' "$expected")
    got_n=$(extract_capability_citations "$transcript" | grep -c . || true)
    set_test "$fixture_id: distinct cited-capability count == $want_n (got $got_n)"
    if [ "$got_n" -eq "$want_n" ]; then _pass; else
      _fail "expected $want_n distinct capability citations, got $got_n"
    fi
  fi

  # Tools that MUST have a real tool_use (proves discovery + actual use).
  while read -r tool; do
    [ -z "$tool" ] && continue
    set_test "$fixture_id: tool actually invoked: $tool"
    if tool_invoked "$transcript" "$tool"; then _pass; else
      _fail "expected a real tool_use for '$tool', none found"
    fi
  done < <(jq -r '.must_invoke_tools[]? // empty' "$expected")

  # Tools that MUST NOT appear as a tool_use (e.g. the fabricated citation's tool).
  while read -r tool; do
    [ -z "$tool" ] && continue
    set_test "$fixture_id: tool never invoked: $tool"
    if tool_invoked "$transcript" "$tool"; then
      _fail "'$tool' was invoked but should not have been"
    else
      _pass
    fi
  done < <(jq -r '.must_not_invoke_tools[]? // empty' "$expected")

  # Literal-term assertions (reused from the shared helpers).
  while read -r term; do
    [ -z "$term" ] && continue
    set_test "$fixture_id: transcript includes term: $term"
    if assert_transcript_contains_term "$transcript" "$term"; then _pass; else
      _fail "expected transcript to include literal term '$term'"
    fi
  done < <(jq -r '.must_include_terms[]? // empty' "$expected")

  while read -r term; do
    [ -z "$term" ] && continue
    set_test "$fixture_id: transcript excludes term: $term"
    if assert_transcript_not_contains_term "$transcript" "$term"; then _pass; else
      _fail "transcript included forbidden literal term '$term'"
    fi
  done < <(jq -r '.must_not_include_terms[]? // empty' "$expected")
}

section "Layer 7 Class 4: Grounding Fixtures (replay)"

while read -r fixture_dir; do
  [ -z "$fixture_dir" ] && continue
  fixture_id=$(basename "$fixture_dir")
  printf "\n${BOLD}Fixture: %s${RESET}\n" "$fixture_id"
  assert_fixture "$fixture_dir"
done < <(collect_fixtures)

test_summary
