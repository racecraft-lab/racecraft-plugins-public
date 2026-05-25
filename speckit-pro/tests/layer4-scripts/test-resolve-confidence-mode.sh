#!/usr/bin/env bash
# test-resolve-confidence-mode.sh — Unit tests for resolve-confidence-mode.sh
#
# Covers precedence: per-invocation flag > local config > default.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$PLUGIN_ROOT/skills/speckit-autopilot/scripts/resolve-confidence-mode.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

# Helpers
write_config() {
  printf '%s\n' "$2" > "$1"
}

# ─────────────────────────────────────────
section "Default (no flag, no config)"
# ─────────────────────────────────────────

set_test "No args, no config file → advisory"
mode=$("$SCRIPT" --config "$FIXTURE_DIR/none.md")
assert_eq "advisory" "$mode"

set_test "Some args, no flags, no config → advisory"
mode=$("$SCRIPT" --config "$FIXTURE_DIR/none.md" docs/workflow.md --from-phase plan --spec SPEC-013)
assert_eq "advisory" "$mode"

# ─────────────────────────────────────────
section "Per-invocation flag — no config"
# ─────────────────────────────────────────

set_test "--strict alone → strict"
mode=$("$SCRIPT" --config "$FIXTURE_DIR/none.md" --strict)
assert_eq "strict" "$mode"

set_test "--advisory alone → advisory"
mode=$("$SCRIPT" --config "$FIXTURE_DIR/none.md" --advisory)
assert_eq "advisory" "$mode"

set_test "--strict mixed with other args → strict"
mode=$("$SCRIPT" --config "$FIXTURE_DIR/none.md" docs/workflow.md --strict --from-phase plan)
assert_eq "strict" "$mode"

set_test "--advisory mixed with other args → advisory"
mode=$("$SCRIPT" --config "$FIXTURE_DIR/none.md" docs/workflow.md --advisory --spec SPEC-013)
assert_eq "advisory" "$mode"

# ─────────────────────────────────────────
section "Flag conflict — both --strict and --advisory"
# ─────────────────────────────────────────

set_test "Both flags → exit 2"
result=0
"$SCRIPT" --config "$FIXTURE_DIR/none.md" --strict --advisory >/dev/null 2>&1 || result=$?
assert_eq "2" "$result" "exit code"

set_test "Conflict message on stderr"
err=$("$SCRIPT" --config "$FIXTURE_DIR/none.md" --strict --advisory 2>&1 >/dev/null || true)
assert_contains "$err" "mutually exclusive"

set_test "Reverse order, both flags → still exit 2"
result=0
"$SCRIPT" --config "$FIXTURE_DIR/none.md" --advisory --strict >/dev/null 2>&1 || result=$?
assert_eq "2" "$result" "exit code"

# ─────────────────────────────────────────
section "Local config — no per-invocation flag"
# ─────────────────────────────────────────

set_test "config=strict → strict"
write_config "$FIXTURE_DIR/strict.md" "confidence_gate_mode: strict"
mode=$("$SCRIPT" --config "$FIXTURE_DIR/strict.md")
assert_eq "strict" "$mode"

set_test "config=advisory → advisory"
write_config "$FIXTURE_DIR/adv.md" "confidence_gate_mode: advisory"
mode=$("$SCRIPT" --config "$FIXTURE_DIR/adv.md")
assert_eq "advisory" "$mode"

set_test "Config with surrounding markdown → still parses"
cat > "$FIXTURE_DIR/wrapped.md" <<'EOF'
# speckit-pro local config

Some commentary here.

confidence_gate_mode: strict

More commentary.
EOF
mode=$("$SCRIPT" --config "$FIXTURE_DIR/wrapped.md")
assert_eq "strict" "$mode"

set_test "Indented config value → still parses"
printf '  confidence_gate_mode: strict\n' > "$FIXTURE_DIR/indented.md"
mode=$("$SCRIPT" --config "$FIXTURE_DIR/indented.md")
assert_eq "strict" "$mode"

set_test "Multiple config matches → last wins"
cat > "$FIXTURE_DIR/multi.md" <<'EOF'
confidence_gate_mode: advisory
confidence_gate_mode: strict
EOF
mode=$("$SCRIPT" --config "$FIXTURE_DIR/multi.md")
assert_eq "strict" "$mode"

set_test "Garbage config value → falls back to default advisory"
write_config "$FIXTURE_DIR/garbage.md" "confidence_gate_mode: chaos"
mode=$("$SCRIPT" --config "$FIXTURE_DIR/garbage.md")
assert_eq "advisory" "$mode"

# ─────────────────────────────────────────
section "Precedence — flag wins over config"
# ─────────────────────────────────────────

set_test "config=advisory + --strict → strict (flag wins)"
write_config "$FIXTURE_DIR/adv-2.md" "confidence_gate_mode: advisory"
mode=$("$SCRIPT" --config "$FIXTURE_DIR/adv-2.md" --strict)
assert_eq "strict" "$mode"

set_test "config=strict + --advisory → advisory (flag wins)"
write_config "$FIXTURE_DIR/strict-2.md" "confidence_gate_mode: strict"
mode=$("$SCRIPT" --config "$FIXTURE_DIR/strict-2.md" --advisory)
assert_eq "advisory" "$mode"

# ─────────────────────────────────────────
section "Usage errors"
# ─────────────────────────────────────────

set_test "--config without path → exit 1"
result=0
"$SCRIPT" --config 2>/dev/null || result=$?
assert_eq "1" "$result" "exit code"

set_test "Commented-out lines do not match"
cat > "$FIXTURE_DIR/commented.md" <<'EOF'
# confidence_gate_mode: strict
EOF
mode=$("$SCRIPT" --config "$FIXTURE_DIR/commented.md")
assert_eq "advisory" "$mode"

# ─────────────────────────────────────────
section "--config=value form"
# ─────────────────────────────────────────

set_test "--config=path works"
write_config "$FIXTURE_DIR/eq.md" "confidence_gate_mode: strict"
mode=$("$SCRIPT" "--config=$FIXTURE_DIR/eq.md")
assert_eq "strict" "$mode"

# ─────────────────────────────────────────
section "Default config search — .claude/ AND .codex/"
# ─────────────────────────────────────────
#
# When --config is NOT passed, the script searches default candidates
# in priority order: .claude/speckit-pro.local.md first, then
# .codex/speckit-pro.local.md. The cwd determines what is found.

DEFAULT_DIR=$(mktemp -d)

set_test "Default search: neither file exists → advisory"
mode=$(cd "$DEFAULT_DIR" && "$SCRIPT")
assert_eq "advisory" "$mode"

set_test "Default search: .codex/ exists, .claude/ missing → reads .codex/"
mkdir -p "$DEFAULT_DIR/.codex"
write_config "$DEFAULT_DIR/.codex/speckit-pro.local.md" "confidence_gate_mode: strict"
mode=$(cd "$DEFAULT_DIR" && "$SCRIPT")
assert_eq "strict" "$mode"

set_test "Default search: both exist → .claude/ wins (priority order)"
mkdir -p "$DEFAULT_DIR/.claude"
write_config "$DEFAULT_DIR/.claude/speckit-pro.local.md" "confidence_gate_mode: advisory"
# .codex still says strict from previous setup
mode=$(cd "$DEFAULT_DIR" && "$SCRIPT")
assert_eq "advisory" "$mode" ".claude/ takes priority when both files exist"

set_test "Default search: .codex/ matches, .claude/ has no key → reads .codex/"
write_config "$DEFAULT_DIR/.claude/speckit-pro.local.md" "# placeholder, no key here"
mode=$(cd "$DEFAULT_DIR" && "$SCRIPT")
assert_eq "strict" "$mode" "falls through to .codex/ when .claude/ has no key"

rm -rf "$DEFAULT_DIR"

test_summary
