#!/usr/bin/env bash
# Layer 8 — Parity Fixtures Runner
#
# Verifies that two code paths (Agent Teams path vs parallel-subagents
# fallback) produce equivalent outcomes for the same workflow input.
#
# Modes:
#   --dry-run (default): validates fixture structure only; no claude -p
#   --live:              actually runs claude -p twice per fixture and
#                        compares outcomes. COSTS LLM TOKENS.
#
# Usage:
#   bash tests/layer8-parity/run-parity-fixtures.sh [--dry-run|--live]
#                                                    [--fixture <name>]
#                                                    [--budget-usd <N>]
#
# Environment:
#   L8_FIXTURE_BUDGET_USD  Per-fixture-pair budget cap (default: 20)
#   CLAUDE_BIN             claude executable (default: claude)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../../../speckit-pro" && pwd)"

# shellcheck source=lib/extractors.sh
source "$SCRIPT_DIR/lib/extractors.sh"
# shellcheck source=lib/judge.sh
source "$SCRIPT_DIR/lib/judge.sh"

# Defaults
MODE="dry-run"
FIXTURE_FILTER=""
L8_FIXTURE_BUDGET_USD="${L8_FIXTURE_BUDGET_USD:-20}"
CLAUDE_BIN="${CLAUDE_BIN:-claude}"

# Colors
if [ -t 1 ]; then
  RED='\033[31m'
  GREEN='\033[32m'
  YELLOW='\033[33m'
  RESET='\033[0m'
else
  RED='' GREEN='' YELLOW='' RESET=''
fi

# Parse args
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) MODE="dry-run"; shift ;;
    --live) MODE="live"; shift ;;
    --fixture) FIXTURE_FILTER="$2"; shift 2 ;;
    --budget-usd) L8_FIXTURE_BUDGET_USD="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,20p' "$0"
      exit 0
      ;;
    *) echo "Unknown flag: $1" >&2; exit 2 ;;
  esac
done

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

_pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf "  ${GREEN}PASS${RESET} %s\n" "$1"; }
_fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf "  ${RED}FAIL${RESET} %s\n    ${RED}%s${RESET}\n" "$1" "${2:-}"; }
_skip() { SKIP_COUNT=$((SKIP_COUNT + 1)); printf "  ${YELLOW}SKIP${RESET} %s\n    ${YELLOW}%s${RESET}\n" "$1" "${2:-}"; }

# ---------------------------------------------------------------------------
# Dry-run validation: every fixture must have these files
# ---------------------------------------------------------------------------
validate_fixture_structure() {
  local fixture_dir="$1"
  local fixture_id
  fixture_id="$(basename "$fixture_dir")"
  local ok=true

  for required in README.md workflow.md env-fallback.sh env-teams.sh tolerance.json expected-equivalence.json; do
    if [ ! -f "$fixture_dir/$required" ]; then
      _fail "$fixture_id: missing $required" "every parity fixture must provide $required"
      ok=false
    fi
  done

  if [ "$ok" = "true" ]; then
    _pass "$fixture_id: fixture structure complete"
  fi

  # Validate tolerance.json + expected-equivalence.json are well-formed JSON
  if [ -f "$fixture_dir/tolerance.json" ]; then
    if jq empty "$fixture_dir/tolerance.json" 2>/dev/null; then
      _pass "$fixture_id: tolerance.json parses"
    else
      _fail "$fixture_id: tolerance.json invalid JSON"
    fi
  fi
  if [ -f "$fixture_dir/expected-equivalence.json" ]; then
    if jq empty "$fixture_dir/expected-equivalence.json" 2>/dev/null; then
      _pass "$fixture_id: expected-equivalence.json parses"
    else
      _fail "$fixture_id: expected-equivalence.json invalid JSON"
    fi
  fi
}

# ---------------------------------------------------------------------------
# Live mode: run claude -p twice (Path A teams / Path B fallback) and
# compare outcomes per expected-equivalence.json + tolerance.json.
#
# Output schema per fixture pair: results land in
#   $L8_OUT/$fixture_id/{pathA,pathB}/  — full workdir snapshot per path
#   $L8_OUT/$fixture_id/diff-report.txt — field-level diff summary
# ---------------------------------------------------------------------------
run_path() {
  # Run a single autopilot path (A or B) and capture its workdir.
  # Args: <fixture_dir> <env_script> <out_dir>
  local fixture_dir="$1" env_script="$2" out_dir="$3"
  mkdir -p "$out_dir"
  cp "$fixture_dir/workflow.md" "$out_dir/workflow.md"
  (
    cd "$out_dir"
    # shellcheck disable=SC1090
    source "$env_script"
    "$CLAUDE_BIN" -p --max-budget-usd "$L8_FIXTURE_BUDGET_USD" \
      "/speckit-pro:autopilot workflow.md" \
      >"$out_dir/.claude-stdout.log" 2>"$out_dir/.claude-stderr.log"
    echo $? >"$out_dir/.claude-exit-code"
  )
}

compare_field() {
  # Compare one field across two path outputs per its tolerance rule.
  # Args: <fixture_id> <pathA_dir> <pathB_dir> <field_json> <tolerance_json>
  # Returns 0 on match, non-zero on mismatch (and prints diff).
  local fixture_id="$1" pa="$2" pb="$3" field_json="$4" tolerance_json="$5"

  local field_name source_path tolerance_key tolerance_type
  field_name=$(echo "$field_json" | jq -r '.field')
  source_path=$(echo "$field_json" | jq -r '.source')
  tolerance_key=$(echo "$field_json" | jq -r '.tolerance_key')
  tolerance_type=$(echo "$tolerance_json" | jq -r ".fields[\"$tolerance_key\"].tolerance // \"unknown\"")

  local file_a="$pa/$source_path" file_b="$pb/$source_path"
  if [ ! -f "$file_a" ] || [ ! -f "$file_b" ]; then
    _fail "$fixture_id:$field_name" "missing artifact on one or both paths ($source_path)"
    return 1
  fi

  case "$tolerance_type" in
    byte-identical)
      if cmp -s "$file_a" "$file_b"; then
        _pass "$fixture_id:$field_name (byte-identical)"
      else
        _fail "$fixture_id:$field_name" "byte-identical tolerance failed — see diff in report"
        diff -u "$file_a" "$file_b" | head -50 >>"$pa/../diff-report.txt"
        return 1
      fi
      ;;
    exact|tolerance-1)
      local section extractor
      section=$(echo "$field_json" | jq -r '.section_selector // ""')
      extractor=$(echo "$field_json" | jq -r '.extractor // ""')

      # Strip leading "## " from section_selector if present, so callers can
      # write either "## Foo" (matching the header line) or "Foo".
      section="${section##\#\# }"

      if [ -z "$section" ] || [ -z "$extractor" ]; then
        # No extractor specified — fall back to whole-file equality.
        if cmp -s "$file_a" "$file_b"; then
          _pass "$fixture_id:$field_name ($tolerance_type, whole-file)"
        else
          _fail "$fixture_id:$field_name" "$tolerance_type tolerance failed (no extractor configured, whole-file diff)"
          diff -u "$file_a" "$file_b" | head -50 >>"$pa/../diff-report.txt"
          return 1
        fi
        return 0
      fi

      local value_a value_b extract_rc=0
      case "$extractor" in
        table_row_count)
          value_a=$(extract_table_row_count "$file_a" "$section") || extract_rc=$?
          value_b=$(extract_table_row_count "$file_b" "$section") || extract_rc=$?
          ;;
        table_column:*)
          local column="${extractor#table_column:}"
          value_a=$(extract_table_column "$file_a" "$section" "$column") || extract_rc=$?
          value_b=$(extract_table_column "$file_b" "$section" "$column") || extract_rc=$?
          ;;
        *)
          _fail "$fixture_id:$field_name" "unknown extractor '$extractor'"
          return 1
          ;;
      esac

      if [ "$extract_rc" -ne 0 ]; then
        _fail "$fixture_id:$field_name" "extractor '$extractor' failed for section '## $section' on one or both paths"
        return 1
      fi

      if [ "$tolerance_type" = "tolerance-1" ]; then
        # tolerance-1 is only meaningful for numeric extractors (row_count).
        if ! [[ "$value_a" =~ ^[0-9]+$ ]] || ! [[ "$value_b" =~ ^[0-9]+$ ]]; then
          _fail "$fixture_id:$field_name" "tolerance-1 requires numeric extractor; got A='$value_a' B='$value_b'"
          return 1
        fi
        local diff_abs=$((value_a > value_b ? value_a - value_b : value_b - value_a))
        if [ "$diff_abs" -le 1 ]; then
          _pass "$fixture_id:$field_name (tolerance-1, |$value_a - $value_b|=$diff_abs)"
        else
          _fail "$fixture_id:$field_name" "tolerance-1 exceeded: |$value_a - $value_b|=$diff_abs"
          printf 'Field %s: A=%s B=%s diff=%s (tolerance-1)\n' "$field_name" "$value_a" "$value_b" "$diff_abs" \
            >>"$pa/../diff-report.txt"
          return 1
        fi
      else
        # exact
        if [ "$value_a" = "$value_b" ]; then
          _pass "$fixture_id:$field_name (exact, extractor=$extractor)"
        else
          _fail "$fixture_id:$field_name" "exact tolerance failed — extracted values differ"
          {
            printf '\n--- %s (extractor=%s) ---\n' "$field_name" "$extractor"
            diff -u <(printf '%s\n' "$value_a") <(printf '%s\n' "$value_b") | head -50
          } >>"$pa/../diff-report.txt"
          return 1
        fi
      fi
      ;;
    semantic-equivalent)
      local section extractor
      section=$(echo "$field_json" | jq -r '.section_selector // ""')
      extractor=$(echo "$field_json" | jq -r '.extractor // ""')
      section="${section##\#\# }"

      if [ -z "$section" ] || [ -z "$extractor" ]; then
        _fail "$fixture_id:$field_name" "semantic-equivalent requires section_selector + extractor in expected-equivalence.json"
        return 1
      fi

      local value_a value_b extract_rc=0
      case "$extractor" in
        table_column:*)
          local column="${extractor#table_column:}"
          value_a=$(extract_table_column "$file_a" "$section" "$column") || extract_rc=$?
          value_b=$(extract_table_column "$file_b" "$section" "$column") || extract_rc=$?
          ;;
        *)
          _fail "$fixture_id:$field_name" "semantic-equivalent supports table_column:<Name> extractor; got '$extractor'"
          return 1
          ;;
      esac
      if [ "$extract_rc" -ne 0 ]; then
        _fail "$fixture_id:$field_name" "extractor '$extractor' failed on one or both paths"
        return 1
      fi

      # If the extracted values are byte-identical, skip the judge (cheap
      # short-circuit; the judge is the expensive path).
      if [ "$value_a" = "$value_b" ]; then
        _pass "$fixture_id:$field_name (semantic-equivalent, bytes match — judge skipped)"
        return 0
      fi

      local rationale
      rationale=$(echo "$tolerance_json" | jq -r ".fields[\"$tolerance_key\"].rationale // \"Values must be semantically equivalent.\"")

      local judge_json
      if ! judge_json=$(semantic_equivalent_judge "$value_a" "$value_b" "$rationale"); then
        _fail "$fixture_id:$field_name" "semantic-equivalent judge failed (subprocess error, timeout, or malformed JSON)"
        printf '\n--- %s (judge subprocess failed) ---\nA=%s\nB=%s\n' \
          "$field_name" "$value_a" "$value_b" >>"$pa/../diff-report.txt"
        return 1
      fi

      local verdict reason
      verdict=$(echo "$judge_json" | jq -r '.verdict')
      reason=$(echo "$judge_json" | jq -r '.reason')

      # Audit-log every verdict to the diff report — cheap insurance
      # against flaky / surprising LLM judgments.
      {
        printf '\n--- %s (semantic-equivalent verdict) ---\n' "$field_name"
        printf 'verdict: %s\nreason:  %s\n' "$verdict" "$reason"
        printf 'VALUE A:\n%s\n' "$value_a"
        printf 'VALUE B:\n%s\n' "$value_b"
      } >>"$pa/../diff-report.txt"

      if [ "$verdict" = "EQUIVALENT" ]; then
        _pass "$fixture_id:$field_name (semantic-equivalent: $reason)"
      else
        _fail "$fixture_id:$field_name" "semantic-equivalent verdict NOT_EQUIVALENT: $reason"
        return 1
      fi
      ;;
    *)
      _fail "$fixture_id:$field_name" "unknown tolerance type '$tolerance_type'"
      return 1
      ;;
  esac
}

run_fixture_live() {
  local fixture_dir="$1"
  local fixture_id
  fixture_id="$(basename "$fixture_dir")"

  if ! command -v "$CLAUDE_BIN" >/dev/null 2>&1; then
    _skip "$fixture_id: live mode" "$CLAUDE_BIN not on PATH"
    return
  fi

  local out_root="${L8_OUT:-/tmp/l8-parity-$$}/$fixture_id"
  local pa="$out_root/pathA" pb="$out_root/pathB"
  mkdir -p "$out_root"
  : >"$out_root/diff-report.txt"

  printf "  ${YELLOW}LIVE${RESET} %s: running Path A (env-teams.sh)\n" "$fixture_id"
  run_path "$fixture_dir" "$fixture_dir/env-teams.sh" "$pa"
  local rcA
  rcA=$(cat "$pa/.claude-exit-code")
  printf "  ${YELLOW}LIVE${RESET} %s: running Path B (env-fallback.sh)\n" "$fixture_id"
  run_path "$fixture_dir" "$fixture_dir/env-fallback.sh" "$pb"
  local rcB
  rcB=$(cat "$pb/.claude-exit-code")

  if [ "$rcA" != "0" ] || [ "$rcB" != "0" ]; then
    _fail "$fixture_id: claude -p" "Path A exit=$rcA / Path B exit=$rcB. See $out_root/{pathA,pathB}/.claude-stderr.log"
    return
  fi

  # Run each compare field through the tolerance check.
  local expected="$fixture_dir/expected-equivalence.json"
  local tolerance="$fixture_dir/tolerance.json"
  local fail_fast
  fail_fast=$(jq -r '.fail_fast // false' "$expected")
  local count
  count=$(jq '.compare | length' "$expected")
  local i=0
  while [ "$i" -lt "$count" ]; do
    local field_json
    field_json=$(jq -c ".compare[$i]" "$expected")
    if ! compare_field "$fixture_id" "$pa" "$pb" "$field_json" "$(cat "$tolerance")"; then
      if [ "$fail_fast" = "true" ]; then
        return
      fi
    fi
    i=$((i + 1))
  done

  printf "  ${GREEN}LIVE${RESET} %s: results in %s\n" "$fixture_id" "$out_root"
}

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
printf "Layer 8: Parity Fixtures (mode=%s)\n" "$MODE"
printf "%s\n" "────────────────────────────────────────"

shopt -s nullglob
for fixture_dir in "$SCRIPT_DIR"/*/; do
  fixture_dir="${fixture_dir%/}"
  fixture_id="$(basename "$fixture_dir")"

  # Skip helper dirs (lib, etc.) — they don't have README.md OR they're not parity fixtures
  if [ ! -f "$fixture_dir/README.md" ]; then
    continue
  fi

  if [ -n "$FIXTURE_FILTER" ] && [ "$fixture_id" != "$FIXTURE_FILTER" ]; then
    continue
  fi

  printf "\n%s\n" "$fixture_id"
  validate_fixture_structure "$fixture_dir"
  if [ "$MODE" = "live" ]; then
    run_fixture_live "$fixture_dir"
  fi
done

printf "\n%s\n" "════════════════════════════════════════"
printf "Layer 8 (parity): %d passed, %d failed, %d skipped\n" \
  "$PASS_COUNT" "$FAIL_COUNT" "$SKIP_COUNT"

if [ "$FAIL_COUNT" -gt 0 ]; then
  exit 1
fi
exit 0
