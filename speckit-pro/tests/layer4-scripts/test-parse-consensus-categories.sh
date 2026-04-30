#!/usr/bin/env bash
# test-parse-consensus-categories.sh — Unit tests for the Tier A
# consensus-routing category parser.
#
# Validates that parse-consensus-categories.sh implements the routing
# rules from `references/consensus-protocol.md` deterministically.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$PLUGIN_ROOT/skills/speckit-autopilot/scripts/parse-consensus-categories.sh"

# Helper: parse a line and return the JSON output.
parse() { bash "$SCRIPT" "$1"; }

# Helper: extract a specific JSON field for assertions.
field() { printf '%s' "$1" | jq -r "$2"; }

# ─────────────────────────────────────────
section "Single-category routing (Round 1, N=1)"
# ─────────────────────────────────────────

set_test "[codebase] → codebase-analyst only"
out=$(parse "[codebase] Q1: error handler choice")
assert_eq '["codebase-analyst"]' "$(field "$out" '.analysts | tostring')"

set_test "[codebase] → reason=category-routed"
assert_eq "category-routed" "$(field "$out" '.reason')"

set_test "[codebase] → categories=[codebase]"
assert_eq '["codebase"]' "$(field "$out" '.categories | tostring')"

set_test "[spec] → spec-context-analyst only"
out=$(parse "[spec] Q2: which preset takes precedence?")
assert_eq '["spec-context-analyst"]' "$(field "$out" '.analysts | tostring')"

set_test "[domain] → domain-researcher only"
out=$(parse "[domain] Q3: RFC 6265bis SameSite default")
assert_eq '["domain-researcher"]' "$(field "$out" '.analysts | tostring')"

# ─────────────────────────────────────────
section "Multi-category routing (Round 1, N=2)"
# ─────────────────────────────────────────

set_test "[codebase, domain] → both analysts"
out=$(parse "[codebase, domain] Q4: bcrypt vs argon2")
assert_eq '["codebase-analyst","domain-researcher"]' "$(field "$out" '.analysts | tostring')"

set_test "[codebase, domain] → reason=category-routed"
assert_eq "category-routed" "$(field "$out" '.reason')"

set_test "[codebase,spec] (no space) → both analysts"
out=$(parse "[codebase,spec] Q5: which session-store TTL")
assert_eq '["codebase-analyst","spec-context-analyst"]' "$(field "$out" '.analysts | tostring')"

set_test "[spec, domain] → both analysts (deterministic order)"
out=$(parse "[spec, domain] Finding 6 [HIGH]: cookie policy")
assert_eq '["spec-context-analyst","domain-researcher"]' "$(field "$out" '.analysts | tostring')"

# ─────────────────────────────────────────
section "All-3 routing (Round 1, N=3 by tag)"
# ─────────────────────────────────────────

set_test "[codebase, spec, domain] → all 3 analysts"
out=$(parse "[codebase, spec, domain] Q7: hard one")
assert_eq '["codebase-analyst","spec-context-analyst","domain-researcher"]' \
  "$(field "$out" '.analysts | tostring')"

set_test "[codebase, spec, domain] → reason=all-categories-routed"
assert_eq "all-categories-routed" "$(field "$out" '.reason')"

# ─────────────────────────────────────────
section "Security defense-in-depth"
# ─────────────────────────────────────────

set_test "[security] → all 3 analysts"
out=$(parse "[security] Q8: hash and rotate API keys")
assert_eq '["codebase-analyst","spec-context-analyst","domain-researcher"]' \
  "$(field "$out" '.analysts | tostring')"

set_test "[security] → reason=security-defense-in-depth"
assert_eq "security-defense-in-depth" "$(field "$out" '.reason')"

set_test "[security, codebase] → still all 3 (security overrides co-tag)"
out=$(parse "[security, codebase] Q9: multi with security")
assert_eq '["codebase-analyst","spec-context-analyst","domain-researcher"]' \
  "$(field "$out" '.analysts | tostring')"

set_test "[security, codebase] → reason=security-defense-in-depth"
assert_eq "security-defense-in-depth" "$(field "$out" '.reason')"

# ─────────────────────────────────────────
section "Ambiguous and untagged safe defaults"
# ─────────────────────────────────────────

set_test "[ambiguous] → all 3 analysts"
out=$(parse "[ambiguous] Q10: error budget for the rate limiter")
assert_eq '["codebase-analyst","spec-context-analyst","domain-researcher"]' \
  "$(field "$out" '.analysts | tostring')"

set_test "[ambiguous] → reason=ambiguous-safe-default"
assert_eq "ambiguous-safe-default" "$(field "$out" '.reason')"

set_test "Untagged item → all 3 analysts"
out=$(parse "Q11: no prefix at all")
assert_eq '["codebase-analyst","spec-context-analyst","domain-researcher"]' \
  "$(field "$out" '.analysts | tostring')"

set_test "Untagged → reason=untagged-safe-default"
assert_eq "untagged-safe-default" "$(field "$out" '.reason')"

set_test "Untagged → raw_prefix is empty string"
assert_eq "" "$(field "$out" '.raw_prefix')"

set_test "Empty brackets [] → all 3 analysts"
out=$(parse "[] Q12: empty bracket")
assert_eq '["codebase-analyst","spec-context-analyst","domain-researcher"]' \
  "$(field "$out" '.analysts | tostring')"

set_test "Empty brackets → reason=empty-prefix-safe-default"
assert_eq "empty-prefix-safe-default" "$(field "$out" '.reason')"

set_test "Whitespace-only brackets [ ] → all 3 analysts"
out=$(parse "[ ] Q13: whitespace bracket")
assert_eq '["codebase-analyst","spec-context-analyst","domain-researcher"]' \
  "$(field "$out" '.analysts | tostring')"

set_test "Commas-only brackets [,,] → all 3 analysts"
out=$(parse "[,,] Q14: commas-only bracket")
assert_eq '["codebase-analyst","spec-context-analyst","domain-researcher"]' \
  "$(field "$out" '.analysts | tostring')"

# ─────────────────────────────────────────
section "Unknown tags safe default"
# ─────────────────────────────────────────

set_test "[bogus] → all 3 analysts"
out=$(parse "[bogus] Q15: typo'd tag")
assert_eq '["codebase-analyst","spec-context-analyst","domain-researcher"]' \
  "$(field "$out" '.analysts | tostring')"

set_test "[bogus] → reason=unknown-tag-safe-default"
assert_eq "unknown-tag-safe-default" "$(field "$out" '.reason')"

set_test "[codebase, bogus] → all 3 (one unknown poisons routing)"
out=$(parse "[codebase, bogus] Q16: partly-known tag")
assert_eq '["codebase-analyst","spec-context-analyst","domain-researcher"]' \
  "$(field "$out" '.analysts | tostring')"

set_test "[codebase, bogus] → reason=unknown-tag-safe-default"
assert_eq "unknown-tag-safe-default" "$(field "$out" '.reason')"

# ─────────────────────────────────────────
section "Markdown bullet and whitespace tolerance"
# ─────────────────────────────────────────

set_test "Leading whitespace + bullet '- [codebase] ...' → codebase-analyst"
out=$(parse "  - [codebase] Q17: indented bullet item")
assert_eq '["codebase-analyst"]' "$(field "$out" '.analysts | tostring')"

set_test "'* [domain] ...' bullet → domain-researcher"
out=$(parse "* [domain] Q18: asterisk bullet")
assert_eq '["domain-researcher"]' "$(field "$out" '.analysts | tostring')"

set_test "'+ [spec] ...' bullet → spec-context-analyst"
out=$(parse "+ [spec] Q19: plus bullet")
assert_eq '["spec-context-analyst"]' "$(field "$out" '.analysts | tostring')"

# ─────────────────────────────────────────
section "Case insensitivity"
# ─────────────────────────────────────────

set_test "[CODEBASE] → codebase-analyst (uppercase normalised)"
out=$(parse "[CODEBASE] Q20: shouty tag")
assert_eq '["codebase-analyst"]' "$(field "$out" '.analysts | tostring')"

set_test "[CodeBase, Domain] → both analysts (mixed case normalised)"
out=$(parse "[CodeBase, Domain] Q21: TitleCase tag")
assert_eq '["codebase-analyst","domain-researcher"]' "$(field "$out" '.analysts | tostring')"

# ─────────────────────────────────────────
section "Output schema"
# ─────────────────────────────────────────

set_test "Output has categories field"
out=$(parse "[codebase] Q22: schema check")
assert_json_field_exists "$out" "categories"

set_test "Output has analysts field"
assert_json_field_exists "$out" "analysts"

set_test "Output has round field"
assert_json_field_exists "$out" "round"

set_test "Output has raw_prefix field"
assert_json_field_exists "$out" "raw_prefix"

set_test "Output has reason field"
assert_json_field_exists "$out" "reason"

set_test "round is always 1 (Round 2 is orchestrator's decision)"
assert_eq "1" "$(field "$out" '.round')"

set_test "raw_prefix preserves original spacing"
out=$(parse "[codebase, domain] Q23: spaced multi-tag")
assert_eq "[codebase, domain]" "$(field "$out" '.raw_prefix')"

# ─────────────────────────────────────────
section "Usage errors"
# ─────────────────────────────────────────

set_test "No arguments → exit code 2"
assert_exit_code 2 bash "$SCRIPT"

# ─────────────────────────────────────────
test_summary
