#!/usr/bin/env bash
# test-post-implementation-reference.sh - PRSG-009 reference contract checks.

set -euo pipefail

TEST_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$TEST_DIR/../../.." && pwd)"

# shellcheck source=../lib/assertions.sh
source "$TEST_DIR/../lib/assertions.sh"

CLAUDE_REF="$REPO_ROOT/speckit-pro/skills/speckit-autopilot/references/post-implementation.md"
CODEX_REF="$REPO_ROOT/speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md"
CLAUDE_DIST="$REPO_ROOT/dist/claude/speckit-pro/skills/speckit-autopilot/references/post-implementation.md"
CODEX_DIST="$REPO_ROOT/dist/codex/speckit-pro/skills/speckit-autopilot/references/post-implementation-codex.md"

claude_body="$(cat "$CLAUDE_REF")"
codex_body="$(cat "$CODEX_REF")"
codex_dist_body="$(cat "$CODEX_DIST")"

section "PRSG-009 post-implementation reference contract"

set_test "Claude reference routes split-PR post-impl through multi-pr-emission.sh"
assert_contains "$claude_body" "multi-pr-emission.sh" "Claude reference must name the shared emitter"

set_test "Claude reference consumes the PRSG-008 layer plan without new slicing heuristics"
assert_contains "$claude_body" "plan-layers.sh"
assert_contains "$claude_body" "MUST NOT infer, reroute, or re-slice"

set_test "Claude reference records durable PRS rows and resume state"
assert_contains "$claude_body" "schemaVersion: 2"
assert_contains "$claude_body" "multi_pr_emission"

set_test "Claude reference blocks failed slices before PR creation"
assert_contains "$claude_body" 'stop before `gh pr create`'
assert_contains "$claude_body" "next_slice_id"

set_test "Claude reference requires reslicing continuation before final response"
assert_contains "$claude_body" "autopilot_continuation"
assert_contains "$claude_body" "Never end the run or report completion while"

set_test "Claude reference documents explicit stack PR creation and restack"
assert_contains "$claude_body" "gh pr create --base <base> --head <head> --body-file <body-file>"
assert_contains "$claude_body" "restack.sh"

set_test "Claude reference keeps scoped CI as evidence, not workflow YAML changes"
assert_contains "$claude_body" 'MUST NOT modify `.github/workflows/pr-checks.yml`'

set_test "Codex mirror carries equivalent multi-PR emission behavior"
assert_contains "$codex_body" "multi-pr-emission.sh"
assert_contains "$codex_body" "plan-layers.sh"
assert_contains "$codex_body" "MUST NOT infer, reroute, or re-slice"
assert_contains "$codex_body" "schemaVersion: 2"
assert_contains "$codex_body" "multi_pr_emission"
assert_contains "$codex_body" 'stop before `gh pr create`'
assert_contains "$codex_body" "autopilot_continuation"
assert_contains "$codex_body" "Never report completion while"
assert_contains "$codex_body" "gh pr create --base <base> --head <head> --body-file <body-file>"
assert_contains "$codex_body" "restack.sh"
assert_contains "$codex_body" 'MUST NOT modify `.github/workflows/pr-checks.yml`'

set_test "Claude dist reference mirrors source"
assert_eq "$(shasum -a 256 "$CLAUDE_REF" | awk '{print $1}')" \
  "$(shasum -a 256 "$CLAUDE_DIST" | awk '{print $1}')" \
  "dist/claude post-implementation reference"

set_test "Codex dist reference carries multi-PR contract"
assert_contains "$codex_dist_body" "multi-pr-emission.sh"
assert_contains "$codex_dist_body" "MUST NOT infer, reroute, or re-slice"
assert_contains "$codex_dist_body" "schemaVersion: 2"
assert_contains "$codex_dist_body" "autopilot_continuation"
assert_contains "$codex_dist_body" 'MUST NOT modify `.github/workflows/pr-checks.yml`'

test_summary
