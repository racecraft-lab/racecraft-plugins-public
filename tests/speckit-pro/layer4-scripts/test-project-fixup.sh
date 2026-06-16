#!/usr/bin/env bash
# test-project-fixup.sh — Unit tests for speckit-coach project fixup helper

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"
SCRIPT="$PLUGIN_ROOT/skills/speckit-coach/scripts/project-fixup.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

section "project-fixup usage"

set_test "Invalid mode exits 2"
result=0
output=$("$SCRIPT" nope "$FIXTURE_DIR" 2>/dev/null) || result=$?
assert_eq "2" "$result" "exit code"

set_test "Missing project root exits 2 with JSON"
missing_root="$FIXTURE_DIR/missing-project"
result=0
output=$("$SCRIPT" audit "$missing_root") || result=$?
assert_eq "2" "$result" "exit code"

set_test "Missing project root reports structured error"
assert_json_field "$output" "error" "project root not accessible"

section "audit mode"

repo="$FIXTURE_DIR/repo"
mkdir -p "$repo/.specify/templates" "$repo/.github"
cat > "$repo/.specify/templates/spec-template.md" <<'EOF'
# Spec Template

### Reviewability Budget

PR Review Packet Requirements
EOF
cat > "$repo/.specify/templates/plan-template.md" <<'EOF'
# Plan Template
EOF
cat > "$repo/.specify/templates/tasks-template.md" <<'EOF'
# Tasks Template
EOF
cat > "$repo/.github/pull_request_template.md" <<'EOF'
## What
EOF

set_test "Audit warns on direct core reviewability edits"
result=0
output=$("$SCRIPT" audit "$repo" demo-reviewability) || result=$?
assert_eq "0" "$result" "exit code"

set_test "Audit status is warn"
assert_json_field "$output" "status" "warn"

set_test "Audit detects spec template"
assert_contains "$output" '"spec-template"'

set_test "Audit resolves templates with specify in HOME/.local/bin when PATH omits it"
fake_home="$FIXTURE_DIR/home-local-specify"
mkdir -p "$fake_home/.local/bin"
cat > "$fake_home/.local/bin/specify" <<'SH'
#!/usr/bin/env bash
if [ "${1:-}" = "preset" ] && [ "${2:-}" = "resolve" ]; then
  printf 'resolved-%s\n' "${3:-unknown}"
  exit 0
fi
exit 0
SH
chmod +x "$fake_home/.local/bin/specify"
limited_path="/usr/bin:/bin:/usr/sbin:/sbin"
result=0
output=$(HOME="$fake_home" PATH="$limited_path" "$SCRIPT" audit "$repo" demo-reviewability) || result=$?
assert_eq "0" "$result" "exit code"
assert_contains "$output" "resolved-spec-template"

section "apply mode"

set_test "Apply creates preset and registry"
result=0
output=$("$SCRIPT" apply "$repo" demo-reviewability) || result=$?
assert_eq "0" "$result" "exit code"

set_test "Preset template copied"
assert_file_exists "$repo/.specify/presets/demo-reviewability/templates/spec-template.md"

set_test "Preset manifest created"
assert_file_exists "$repo/.specify/presets/demo-reviewability/preset.yml"

set_test "Preset registry updated"
assert_contains "$(cat "$repo/.specify/presets/.registry")" '"demo-reviewability"'

set_test "Apply reports registry"
assert_json_field "$output" "preset_registered" "True"

test_summary
