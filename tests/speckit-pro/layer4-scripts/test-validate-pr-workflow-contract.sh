#!/usr/bin/env bash
# test-validate-pr-workflow-contract.sh - PR title/split workflow contract tests.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

TEST_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$TEST_DIR/../../.." && pwd)"
SCRIPT="$REPO_ROOT/speckit-pro/skills/speckit-autopilot/scripts/validate-pr-workflow-contract.sh"

SANDBOX=$(mktemp -d)
trap 'rm -rf "$SANDBOX"' EXIT

run_contract() {
  local out_var="$1" err_var="$2"
  shift 2
  local stdout_file="$SANDBOX/stdout.$RANDOM"
  local stderr_file="$SANDBOX/stderr.$RANDOM"
  local rc=0
  "$SCRIPT" --repo-root "$SANDBOX/repo" "$@" >"$stdout_file" 2>"$stderr_file" || rc=$?
  printf -v "$out_var" '%s' "$(cat "$stdout_file")"
  printf -v "$err_var" '%s' "$(cat "$stderr_file")"
  return "$rc"
}

write_changed_files() {
  local target="$1"
  shift
  mkdir -p "$(dirname "$target")"
  printf '%s\n' "$@" > "$target"
}

json_check() {
  local json="$1" expr="$2" msg="$3"
  local file="$SANDBOX/json-check.$RANDOM.json"
  printf '%s' "$json" > "$file"
  if python3 - "$file" "$expr" >/dev/null 2>&1 <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as fh:
    data = json.load(fh)

safe_builtins = {"any": any, "all": all, "len": len}
if not eval(sys.argv[2], {"__builtins__": safe_builtins}, {"data": data}):
    raise SystemExit(1)
PY
  then
    _pass
  else
    _fail "$msg"
  fi
}

section "script presence"

set_test "validate-pr-workflow-contract.sh exists"
assert_file_exists "$SCRIPT"

set_test "validate-pr-workflow-contract.sh is executable"
assert_file_executable "$SCRIPT"

mkdir -p "$SANDBOX/repo"

section "spec-scoped title validation"

doc004_changed="$SANDBOX/doc004-changed.txt"
write_changed_files "$doc004_changed" \
  "specs/doc-004-codex-marketplace-installation-path/spec.md" \
  "docs-site/src/content/docs/install/codex.md"

set_test "DOC implementation accepts docs(DOC-004) title"
result=0
run_contract output stderr_output --title "docs(DOC-004): add codex marketplace installation path" --changed-files "$doc004_changed" || result=$?
assert_eq "0" "$result" "exit code"

set_test "DOC implementation success emits passed JSON"
json_check "$output" "data['status'] == 'passed'" "expected passed JSON"

set_test "DOC implementation rejects plugin-scoped feature title"
result=0
run_contract output stderr_output --title "feat(speckit-pro): Add codex marketplace installation path" --changed-files "$doc004_changed" || result=$?
assert_eq "1" "$result" "exit code"

set_test "DOC implementation plugin-scope failure reports spec scope rule"
json_check "$output" "any(f['rule'] == 'title.spec_scope' for f in data['failures'])" \
  "expected title.spec_scope failure"

set_test "DOC implementation rejects non-docs title type"
result=0
run_contract output stderr_output --title "feat(DOC-004): add codex marketplace installation path" --changed-files "$doc004_changed" || result=$?
assert_eq "1" "$result" "exit code"

set_test "DOC implementation non-docs type reports doc type rule"
json_check "$output" "any(f['rule'] == 'title.doc_type' for f in data['failures'])" \
  "expected title.doc_type failure"

prsg_changed="$SANDBOX/prsg-changed.txt"
write_changed_files "$prsg_changed" \
  "specs/prsg-012-reviewer-ready-pr-packet-contract/spec.md" \
  "speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh"

set_test "PRSG implementation accepts PRSG-scoped feature title"
result=0
run_contract output stderr_output --title "feat(PRSG-012): add reviewer-ready PR packets" --changed-files "$prsg_changed" || result=$?
assert_eq "0" "$result" "exit code"

set_test "non-spec plugin PR still accepts plugin scope"
plugin_changed="$SANDBOX/plugin-changed.txt"
write_changed_files "$plugin_changed" \
  "speckit-pro/skills/speckit-coach/SKILL.md"
result=0
run_contract output stderr_output --title "feat(speckit-pro): improve coaching guidance" --changed-files "$plugin_changed" || result=$?
assert_eq "0" "$result" "exit code"

section "split candidate aggregate blocking"

split_changed="$SANDBOX/split-changed.txt"
split_commands_rel="specs/doc-003-claude-code-marketplace-installation-path/.process/emission/candidate/commands.candidate.json"
split_commands="$SANDBOX/repo/$split_commands_rel"
mkdir -p "$(dirname "$split_commands")"
cat > "$split_commands" <<'EOF'
{
  "schema_version": 1,
  "dry_run": true,
  "operations": [
    {"action": "gh_pr_create", "slice_id": "foundation", "title": "docs(DOC-003): add claude install foundation"},
    {"action": "gh_pr_create", "slice_id": "us1", "title": "docs(DOC-003): document claude install path"}
  ]
}
EOF
write_changed_files "$split_changed" \
  "specs/doc-003-claude-code-marketplace-installation-path/spec.md" \
  "$split_commands_rel"

set_test "aggregate PR with multi-PR candidate commands is blocked"
result=0
run_contract output stderr_output --title "docs(DOC-003): add Claude Code install route" --changed-files "$split_changed" || result=$?
assert_eq "1" "$result" "exit code"

set_test "aggregate candidate block reports split rule"
json_check "$output" "any(f['rule'] == 'split.aggregate_candidate' for f in data['failures'])" \
  "expected split.aggregate_candidate failure"

single_split_changed="$SANDBOX/single-split-changed.txt"
single_commands_rel="specs/doc-003-claude-code-marketplace-installation-path/.process/emission/candidate/single/commands.candidate.json"
single_commands="$SANDBOX/repo/$single_commands_rel"
mkdir -p "$(dirname "$single_commands")"
cat > "$single_commands" <<'EOF'
{
  "schema_version": 1,
  "dry_run": true,
  "operations": [
    {"action": "gh_pr_create", "slice_id": "full-spec", "title": "docs(DOC-003): add Claude Code install route"}
  ]
}
EOF
write_changed_files "$single_split_changed" \
  "specs/doc-003-claude-code-marketplace-installation-path/spec.md" \
  "$single_commands_rel"

set_test "single planned PR candidate is allowed"
result=0
run_contract output stderr_output --title "docs(DOC-003): add Claude Code install route" --changed-files "$single_split_changed" || result=$?
assert_eq "0" "$result" "exit code"

marker_result_changed="$SANDBOX/marker-result-changed.txt"
marker_result_rel="specs/doc-003-claude-code-marketplace-installation-path/.process/final-reviewability/final-marker-split-result.json"
marker_result="$SANDBOX/repo/$marker_result_rel"
mkdir -p "$(dirname "$marker_result")"
cat > "$marker_result" <<'EOF'
{
  "status": "proceed",
  "outcome": "marker_split",
  "emission": {
    "route": "marker_split",
    "markers": [
      {"id": "foundation"},
      {"id": "us1"}
    ]
  }
}
EOF
write_changed_files "$marker_result_changed" \
  "specs/doc-003-claude-code-marketplace-installation-path/spec.md" \
  "$marker_result_rel"

set_test "aggregate PR with multi-marker split result is blocked"
result=0
run_contract output stderr_output --title "docs(DOC-003): add Claude Code install route" --changed-files "$marker_result_changed" || result=$?
assert_eq "1" "$result" "exit code"

set_test "multi-marker split result block reports split rule"
json_check "$output" "any(f['rule'] == 'split.marker_result' for f in data['failures'])" \
  "expected split.marker_result failure"

test_summary
