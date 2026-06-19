#!/usr/bin/env bash
# test-check-prerequisites.sh — Unit tests for check-prerequisites.sh
#
# Tests prerequisite checking with synthetic fixtures for failure modes.
# Optional --live flag runs against a live SpecKit project (set PROJECT_ROOT).

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"
SCRIPT="$PLUGIN_ROOT/skills/speckit-autopilot/scripts/check-prerequisites.sh"
LIVE=false
[ "${1:-}" = "--live" ] && LIVE=true

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

# Helper: create a minimal SpecKit project fixture
make_project() {
  local dir="$FIXTURE_DIR/$1"
  mkdir -p "$dir/.specify/memory"
  printf '# Constitution\n' > "$dir/.specify/memory/constitution.md"
  # SpecKit v0.8.13+ installs the core phases as skills (.claude/skills/<cmd>/SKILL.md)
  for cmd in speckit-specify speckit-plan speckit-tasks speckit-implement; do
    mkdir -p "$dir/.claude/skills/${cmd}"
    printf -- '---\ndescription: test\n---\n# Test\n' > "$dir/.claude/skills/${cmd}/SKILL.md"
  done
  # Create a dummy workflow file
  printf '# Workflow\n' > "$dir/workflow.md"
  # Init git (configure user for CI where no global git config exists)
  (cd "$dir" && git init -q && git config user.email "test@test" && git config user.name "test" && git config commit.gpgsign false && git add -A && git commit -q -m "init" 2>/dev/null) || true
  echo "$dir"
}

install_fake_specify() {
  local dir="$1"
  local fake_home="$dir/home"
  mkdir -p "$fake_home/.local/bin"
  cat > "$fake_home/.local/bin/specify" <<'SH'
#!/usr/bin/env bash
if [ "${1:-}" = "--version" ]; then
  printf 'specify 9.9.9-test\n'
  exit 0
fi
exit 0
SH
  chmod +x "$fake_home/.local/bin/specify"
  echo "$fake_home"
}

# ─────────────────────────────────────────
section "Missing prerequisites"
# ─────────────────────────────────────────

set_test "No workflow file arg → all_pass false"
dir=$(make_project "no-workflow-arg")
result=0
output=$(cd "$dir" && bash "$SCRIPT" 2>/dev/null) || result=$?
assert_eq "1" "$result" "exit code"
assert_json_field "$output" "all_pass" "False"

set_test "Nonexistent workflow file → all_pass false"
dir=$(make_project "bad-workflow")
result=0
output=$(cd "$dir" && bash "$SCRIPT" "/nonexistent/workflow.md" 2>/dev/null) || result=$?
assert_eq "1" "$result" "exit code"

set_test "No .specify dir → project_init false"
dir="$FIXTURE_DIR/no-specify"
mkdir -p "$dir"
(cd "$dir" && git init -q 2>/dev/null) || true
result=0
output=$(cd "$dir" && bash "$SCRIPT" 2>/dev/null) || result=$?
assert_eq "1" "$result" "exit code"

set_test "No constitution → constitution false"
dir=$(make_project "no-constitution")
rm -f "$dir/.specify/memory/constitution.md"
result=0
output=$(cd "$dir" && bash "$SCRIPT" "$dir/workflow.md" 2>/dev/null) || result=$?
assert_eq "1" "$result" "exit code"

set_test "Missing commands → commands false"
dir=$(make_project "missing-cmds")
rm -rf "$dir/.claude/skills/speckit-plan"
result=0
output=$(cd "$dir" && bash "$SCRIPT" "$dir/workflow.md" 2>/dev/null) || result=$?
assert_eq "1" "$result" "exit code"
assert_contains "$output" "speckit-plan"

set_test "Codex skills install → commands detected"
# Autopilot shares this script under Codex; phase skills live at .codex/skills/.
dir=$(make_project "codex-skills")
rm -rf "$dir/.claude/skills"
for cmd in speckit-specify speckit-plan speckit-tasks speckit-implement; do
  mkdir -p "$dir/.codex/skills/${cmd}"
  printf -- '---\ndescription: test\n---\n# Test\n' > "$dir/.codex/skills/${cmd}/SKILL.md"
done
output=$(cd "$dir" && bash "$SCRIPT" "$dir/workflow.md" 2>/dev/null) || true
assert_contains "$output" "All SpecKit commands installed"

set_test "Agents-dir skills install → commands detected"
# Current spec-kit (github/spec-kit#1906) installs Codex phase skills natively at
# .agents/skills/<cmd>/SKILL.md. The gate must accept this layout so projects don't
# need .codex/skills compatibility shims to pass preflight.
dir=$(make_project "agents-skills")
rm -rf "$dir/.claude/skills"
for cmd in speckit-specify speckit-plan speckit-tasks speckit-implement; do
  mkdir -p "$dir/.agents/skills/${cmd}"
  printf -- '---\ndescription: test\n---\n# Test\n' > "$dir/.agents/skills/${cmd}/SKILL.md"
done
output=$(cd "$dir" && bash "$SCRIPT" "$dir/workflow.md" 2>/dev/null) || true
assert_contains "$output" "All SpecKit commands installed"

set_test "SpecKit CLI in HOME/.local/bin → detected when PATH omits it"
dir=$(make_project "home-local-specify")
fake_home=$(install_fake_specify "$dir")
limited_path="/usr/bin:/bin:/usr/sbin:/sbin"
output=$(cd "$dir" && HOME="$fake_home" PATH="$limited_path" bash "$SCRIPT" "$dir/workflow.md" 2>/dev/null) || true
assert_contains "$output" "specify 9.9.9-test"

# ─────────────────────────────────────────
section "Branch detection"
# ─────────────────────────────────────────

set_test "Main branch → on_feature_branch false"
dir=$(make_project "main-branch")
result=0
output=$(cd "$dir" && bash "$SCRIPT" "$dir/workflow.md" 2>/dev/null) || result=$?
# May fail on speckit_cli check but branch detection should work
assert_contains "$output" "on_feature_branch"

set_test "Feature branch → detected correctly"
dir=$(make_project "feature-branch")
(cd "$dir" && git checkout -q -b 009-search-database 2>/dev/null) || true
result=0
output=$(cd "$dir" && bash "$SCRIPT" "$dir/workflow.md" 2>/dev/null) || result=$?
assert_contains "$output" "009-search-database"

set_test "Letter-suffixed slice branch → on_feature_branch true"
# Roadmaps decompose specs into letter-suffixed slices (006a-, 013b-).
dir=$(make_project "slice-branch")
(cd "$dir" && git checkout -q -b 013b-spec-index 2>/dev/null) || true
output=$(cd "$dir" && bash "$SCRIPT" "$dir/workflow.md" 2>/dev/null) || true
assert_json_field "$output" "on_feature_branch" "True"

# ─────────────────────────────────────────
section "Output format"
# ─────────────────────────────────────────

set_test "Output is valid JSON"
dir=$(make_project "json-check")
output=$(cd "$dir" && bash "$SCRIPT" "$dir/workflow.md" 2>/dev/null) || true
printf '%s' "$output" | python3 -m json.tool >/dev/null 2>&1
assert_eq "0" "$?" "JSON parse"

set_test "Output has checks array"
assert_json_field_exists "$output" "checks"

set_test "Output has branch field"
assert_json_field_exists "$output" "branch"

set_test "Output exposes stable top-level context fields"
dir=$(make_project "stable-top-level")
fake_home=$(install_fake_specify "$dir")
output=$(cd "$dir" && HOME="$fake_home" PATH="/usr/bin:/bin:/usr/sbin:/sbin" bash "$SCRIPT" "$dir/workflow.md" 2>/dev/null) || true
stable_fields=$(printf '%s' "$output" | jq -r 'has("all_pass") and has("branch") and has("is_worktree") and has("on_feature_branch") and has("checks")')
assert_eq "true" "$stable_fields" "stable top-level fields"
printf '%s' "$output" | python3 -m json.tool >/dev/null 2>&1
assert_eq "0" "$?" "single JSON document"

set_test "Capability coverage advisory present exactly once and passes"
capability_count=$(printf '%s' "$output" | jq -r '[.checks[] | select(.check == "capability_coverage")] | length')
assert_eq "1" "$capability_count" "capability_coverage count"
capability_pass=$(printf '%s' "$output" | jq -r '.checks[] | select(.check == "capability_coverage") | .pass')
assert_eq "true" "$capability_pass" "capability_coverage pass"
capability_fields=$(printf '%s' "$output" | jq -r '.checks[] | select(.check == "capability_coverage") | has("check") and has("pass") and has("message") and has("detail")')
assert_eq "true" "$capability_fields" "capability_coverage stable fields"

set_test "Missing optional capability coverage remains non-blocking"
assert_json_field "$output" "all_pass" "True"
capability_text=$(printf '%s' "$output" | jq -r '.checks[] | select(.check == "capability_coverage") | .message + " " + .detail')
assert_contains "$capability_text" "codebase context"
assert_contains "$capability_text" "library documentation"
assert_contains "$capability_text" "web/domain research"
assert_contains "$capability_text" "source extraction"
assert_contains "$capability_text" "confidence"
assert_contains "$capability_text" "fallback"

set_test "Capability advisory has no per-tool inventory"
tool_inventory_count=$(printf '%s' "$output" | jq -r '[.checks[] | select(.check == "mcp_servers" or .check == "optional_mcp_servers")] | length')
assert_eq "0" "$tool_inventory_count" "legacy optional-tool checks"
assert_not_contains "$output" "tavily-mcp"
assert_not_contains "$output" "context7"
assert_not_contains "$output" "RepoPrompt"

set_test "True prerequisite blocker remains actionable"
dir=$(make_project "true-blocker-actionable")
fake_home=$(install_fake_specify "$dir")
rm -rf "$dir/.claude/skills/speckit-plan"
result=0
output=$(cd "$dir" && HOME="$fake_home" PATH="/usr/bin:/bin:/usr/sbin:/sbin" bash "$SCRIPT" "$dir/workflow.md" 2>/dev/null) || result=$?
assert_eq "1" "$result" "exit code"
blocker_pass=$(printf '%s' "$output" | jq -r '.all_pass')
assert_eq "false" "$blocker_pass" "all_pass for true blocker"
commands_message=$(printf '%s' "$output" | jq -r '.checks[] | select(.check == "commands") | .message')
assert_contains "$commands_message" "Missing commands: speckit-plan"
assert_contains "$commands_message" "Run: specify integration install"

# ─────────────────────────────────────────
section "Active guidance assertions"
# ─────────────────────────────────────────

claude_prereq="$PLUGIN_ROOT/skills/speckit-autopilot/references/prerequisites.md"
codex_prereq="$PLUGIN_ROOT/codex-skills/speckit-autopilot/references/prerequisites-codex.md"
limitations="$PLUGIN_ROOT/skills/speckit-autopilot/references/plugin-limitations.md"
coach="$PLUGIN_ROOT/skills/speckit-coach/references/autopilot-guide.md"
claude_skill="$PLUGIN_ROOT/skills/speckit-autopilot/SKILL.md"
codex_skill="$PLUGIN_ROOT/codex-skills/speckit-autopilot/SKILL.md"

set_test "Prerequisite docs describe capability coverage"
prereq_body="$(cat "$claude_prereq" "$codex_prereq")"
assert_contains "$prereq_body" "capability_coverage"
assert_contains "$prereq_body" "codebase context"
assert_contains "$prereq_body" "library documentation"
assert_contains "$prereq_body" "web/domain research"
assert_contains "$prereq_body" "source extraction"
assert_not_contains "$prereq_body" "mcp_servers"

set_test "Guidance docs avoid fixed optional provider contract"
guidance_body="$(cat "$claude_prereq" "$codex_prereq" "$limitations" "$coach")"
assert_contains "$guidance_body" "Missing optional research/context coverage"
assert_contains "$guidance_body" "Research/Context Capability Coverage"
assert_not_contains "$guidance_body" "tavily-mcp"
assert_not_contains "$guidance_body" "RepoPrompt"
assert_not_contains "$guidance_body" "mcp__"
assert_not_contains "$guidance_body" "MCP Server Prerequisites"

set_test "Autopilot skill summaries use capability wording"
skill_body="$(cat "$claude_skill" "$codex_skill")"
assert_contains "$skill_body" "Capability Coverage Check"
assert_contains "$skill_body" "capability fallback behavior"
assert_not_contains "$skill_body" "MCP Server Check"

# ─────────────────────────────────────────
# Live project tests (optional)
# ─────────────────────────────────────────

if [ "$LIVE" = "true" ]; then
  section "Live: check-prerequisites on live project"

  PROJECT_ROOT="${PROJECT_ROOT:-$(git -C "$PLUGIN_ROOT" rev-parse --show-toplevel 2>/dev/null || echo "")}"
  if [ -n "$PROJECT_ROOT" ]; then
    # Use a real workflow file
    # Guard with || true: find exits 1 on missing directory; with pipefail the pipeline
    # would abort the script before test_summary is reached.
    WORKFLOW=$(find "$PROJECT_ROOT/docs/ai/specs" -name "*-workflow.md" -type f 2>/dev/null | head -1) || true
    if [ -n "$WORKFLOW" ]; then
      set_test "Live project — output is valid JSON"
      output=$(cd "$PROJECT_ROOT" && bash "$SCRIPT" "$WORKFLOW" 2>/dev/null) || true
      printf '%s' "$output" | python3 -m json.tool >/dev/null 2>&1
      assert_eq "0" "$?" "JSON parse"

      set_test "Live project — project_init passes"
      assert_contains "$output" '"project_init"'
    else
      printf "  ${YELLOW}SKIP${RESET}: No workflow file found\n"
    fi
  else
    printf "  ${YELLOW}SKIP${RESET}: PROJECT_ROOT not detected\n"
  fi
fi

test_summary
