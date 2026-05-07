#!/usr/bin/env bash
# test-ensure-reviewability-preset.sh — Unit tests for reviewability preset installer

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$PLUGIN_ROOT/skills/speckit-coach/scripts/ensure-reviewability-preset.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

section "ensure-reviewability-preset"

repo="$FIXTURE_DIR/repo"
mkdir -p "$repo/.specify/templates"
cat > "$repo/.specify/templates/spec-template.md" <<'EOF'
# Feature Specification: [FEATURE NAME]

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST do something.

### Key Entities *(include if feature involves data)*
EOF
cat > "$repo/.specify/templates/plan-template.md" <<'EOF'
# Implementation Plan: [FEATURE]

## Technical Context

**Scale/Scope**: [domain-specific]

## Constitution Check

[Gates determined based on constitution file]

## Project Structure
EOF
cat > "$repo/.specify/templates/tasks-template.md" <<'EOF'
# Tasks: [FEATURE NAME]

**Tests**: Tests are optional.

**Organization**: Tasks are grouped by user story.

- [ ] T009 Setup environment configuration management
- [ ] TXXX Run quickstart.md validation

## Notes

- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
EOF

set_test "Installer succeeds"
result=0
output=$("$SCRIPT" "$repo" "$PLUGIN_ROOT" speckit-pro-reviewability) || result=$?
assert_eq "0" "$result" "exit code"

set_test "Installer reports installed"
assert_json_field "$output" "status" "installed"

set_test "Preset manifest exists"
assert_file_exists "$repo/.specify/presets/speckit-pro-reviewability/preset.yml"

set_test "Registry contains preset"
assert_contains "$(cat "$repo/.specify/presets/.registry")" '"speckit-pro-reviewability"'

set_test "Spec template contains reviewability section"
assert_contains "$(cat "$repo/.specify/presets/speckit-pro-reviewability/templates/spec-template.md")" "Reviewability Budget"

set_test "Plan template contains reviewability budget"
assert_contains "$(cat "$repo/.specify/presets/speckit-pro-reviewability/templates/plan-template.md")" "Reviewability Budget"

set_test "Tasks template contains checkpoint task"
assert_contains "$(cat "$repo/.specify/presets/speckit-pro-reviewability/templates/tasks-template.md")" "T009A Verify reviewability budget"

set_test "Second run is idempotent"
result=0
output=$("$SCRIPT" "$repo" "$PLUGIN_ROOT" speckit-pro-reviewability) || result=$?
assert_eq "0" "$result" "exit code"

set_test "Second run reports present"
assert_json_field "$output" "status" "present"

test_summary
