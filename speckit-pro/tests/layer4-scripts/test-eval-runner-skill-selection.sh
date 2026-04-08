#!/usr/bin/env bash
# test-eval-runner-skill-selection.sh — Regression tests for Claude/Codex eval runners

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
FUNCTIONAL_SCRIPT="$PLUGIN_ROOT/tests/layer3-functional/run-functional-evals.sh"
TRIGGER_SCRIPT="$PLUGIN_ROOT/tests/layer2-trigger/run-trigger-evals.sh"
CODEX_FUNCTIONAL_SCRIPT="$PLUGIN_ROOT/tests/layer3-functional/run-functional-evals-codex.sh"
CODEX_TRIGGER_SCRIPT="$PLUGIN_ROOT/tests/layer2-trigger/run-trigger-evals-codex.sh"

FAKE_SKILL_CREATOR=$(mktemp -d)
trap 'rm -rf "$FAKE_SKILL_CREATOR"' EXIT
mkdir -p "$FAKE_SKILL_CREATOR/scripts"
printf '' > "$FAKE_SKILL_CREATOR/scripts/__init__.py"
cat > "$FAKE_SKILL_CREATOR/scripts/run_eval.py" <<'PY'
import sys

print("fake run_eval invoked")
print("args:", " ".join(sys.argv[1:]))
PY

# ─────────────────────────────────────────
section "Functional eval runner"
# ─────────────────────────────────────────

set_test "Functional runner uses Claude skill for speckit-coach"
output=$(bash "$FUNCTIONAL_SCRIPT" speckit-coach)
assert_contains "$output" "Skill path: $PLUGIN_ROOT/skills/speckit-coach"

# ─────────────────────────────────────────
section "Trigger eval runner"
# ─────────────────────────────────────────

set_test "Trigger runner uses Claude skill for speckit-coach"
result=0
output=$(SKILL_CREATOR_ROOT="$FAKE_SKILL_CREATOR" bash "$TRIGGER_SCRIPT" speckit-coach 2>&1) || result=$?
assert_eq "0" "$result" "exit code"
assert_contains "$output" "Skill path: $PLUGIN_ROOT/skills/speckit-coach"

# ─────────────────────────────────────────
section "Codex eval runner"
# ─────────────────────────────────────────

set_test "Codex functional runner uses codex skill for speckit-coach"
output=$(bash "$CODEX_FUNCTIONAL_SCRIPT" speckit-coach)
assert_contains "$output" "Skill path: $PLUGIN_ROOT/codex-skills/speckit-coach"

set_test "Codex trigger runner uses codex skill for speckit-coach"
output=$(bash "$CODEX_TRIGGER_SCRIPT" speckit-coach)
assert_contains "$output" "Skill path: $PLUGIN_ROOT/codex-skills/speckit-coach"

test_summary
