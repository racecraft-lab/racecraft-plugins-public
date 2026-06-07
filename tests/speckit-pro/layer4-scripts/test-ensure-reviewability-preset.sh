#!/usr/bin/env bash
# test-ensure-reviewability-preset.sh — Unit tests for reviewability preset installer

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"
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

section "consumer .gitattributes collapse rule (FR-009/AC-2.3/SC-004)"

PROCESS_RULE='**/.process/** linguist-generated=true'

# Minimal .specify/templates so the preset installer reaches exit 0 in each
# consumer-repo fixture (the .gitattributes ensure-step is independent of the
# preset machinery, but the script must still complete cleanly).
seed_specify_templates() {
  local root="$1"
  mkdir -p "$root/.specify/templates"
  cat > "$root/.specify/templates/spec-template.md" <<'EOF'
# Feature Specification: [FEATURE NAME]

### Key Entities *(include if feature involves data)*
EOF
  cat > "$root/.specify/templates/plan-template.md" <<'EOF'
# Implementation Plan: [FEATURE]

**Scale/Scope**: [domain-specific]

## Project Structure
EOF
  cat > "$root/.specify/templates/tasks-template.md" <<'EOF'
# Tasks: [FEATURE NAME]

**Organization**: Tasks are grouped by user story.

- [ ] T009 Setup environment configuration management
- [ ] TXXX Run quickstart.md validation

- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
EOF
}

# (a) create branch — no repo-root .gitattributes → ensure-step CREATES it with the rule.
create_repo="$FIXTURE_DIR/ga-create"
seed_specify_templates "$create_repo"
"$SCRIPT" "$create_repo" "$PLUGIN_ROOT" speckit-pro-reviewability >/dev/null

set_test "Create branch: .gitattributes is created"
assert_file_exists "$create_repo/.gitattributes"

set_test "Create branch: file contains exactly the collapse rule"
assert_eq "1" "$(grep -cxF "$PROCESS_RULE" "$create_repo/.gitattributes")" "rule line count"

# (b) append branch — pre-existing .gitattributes WITHOUT the rule → append one copy,
# preserve pre-existing lines byte-for-byte.
append_repo="$FIXTURE_DIR/ga-append"
seed_specify_templates "$append_repo"
printf '*.png binary\n# pre-existing comment\n' > "$append_repo/.gitattributes"
preexisting_before="$(cat "$append_repo/.gitattributes")"
"$SCRIPT" "$append_repo" "$PLUGIN_ROOT" speckit-pro-reviewability >/dev/null

set_test "Append branch: rule appended exactly once"
assert_eq "1" "$(grep -cxF "$PROCESS_RULE" "$append_repo/.gitattributes")" "rule line count"

set_test "Append branch: pre-existing lines preserved byte-for-byte"
assert_contains "$(cat "$append_repo/.gitattributes")" "$preexisting_before"

# (c) idempotency — running twice leaves exactly one copy, including when the rule
# is already present surrounded by differing blank lines (whole-line match).
set_test "Idempotency: second run does not duplicate the rule"
"$SCRIPT" "$append_repo" "$PLUGIN_ROOT" speckit-pro-reviewability >/dev/null
assert_eq "1" "$(grep -cxF "$PROCESS_RULE" "$append_repo/.gitattributes")" "rule line count after 2nd run"

blank_repo="$FIXTURE_DIR/ga-blanks"
seed_specify_templates "$blank_repo"
printf '*.bin binary\n\n%s\n\n# trailer\n' "$PROCESS_RULE" > "$blank_repo/.gitattributes"
"$SCRIPT" "$blank_repo" "$PLUGIN_ROOT" speckit-pro-reviewability >/dev/null

set_test "Idempotency: rule already present amid blank lines is not re-appended"
assert_eq "1" "$(grep -cxF "$PROCESS_RULE" "$blank_repo/.gitattributes")" "rule line count"

# (d) no-trailing-newline — a pre-existing file whose last byte is NOT \n must NOT
# get the rule concatenated onto the final line (newline normalized first).
nonl_repo="$FIXTURE_DIR/ga-nonl"
seed_specify_templates "$nonl_repo"
printf '*.jpg binary' > "$nonl_repo/.gitattributes"  # no trailing newline
"$SCRIPT" "$nonl_repo" "$PLUGIN_ROOT" speckit-pro-reviewability >/dev/null

set_test "No-trailing-newline: rule lands on its own whole line"
assert_eq "1" "$(grep -cxF "$PROCESS_RULE" "$nonl_repo/.gitattributes")" "rule line count"

set_test "No-trailing-newline: pre-existing final line is not concatenated"
assert_eq "1" "$(grep -cxF '*.jpg binary' "$nonl_repo/.gitattributes")" "original line preserved whole"

# (e) both branches converge on the single-rule end state.
set_test "Convergence: create branch ends with exactly one rule"
assert_eq "1" "$(grep -cxF "$PROCESS_RULE" "$create_repo/.gitattributes")" "create end state"

set_test "Convergence: append branch ends with exactly one rule"
assert_eq "1" "$(grep -cxF "$PROCESS_RULE" "$append_repo/.gitattributes")" "append end state"

test_summary
