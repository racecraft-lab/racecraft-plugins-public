#!/usr/bin/env bash
# validate-plugin-payload.sh — Guard: shipped platform payloads must be clean.
#
# speckit-pro/ is the rich authoring source tree and may contain Claude and
# Codex variants side by side. The marketplaces must install generated payloads
# under dist/ so each platform sees only its own manifest, skills, agents, hooks,
# and copied support files.
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SOURCE_ROOT="$REPO_ROOT/speckit-pro"
BUILDER="$REPO_ROOT/scripts/build-plugin-payloads.sh"
CLAUDE_PAYLOAD="$REPO_ROOT/dist/claude/speckit-pro"
CODEX_PAYLOAD="$REPO_ROOT/dist/codex/speckit-pro"

count_skill_entrypoints() {
  local root="$1"
  find "$root" -mindepth 2 -maxdepth 2 -type f -name 'SKILL.md' | wc -l | tr -d ' '
}

skill_entrypoint_set() {
  local root="$1"
  (cd "$root" && find . -mindepth 2 -maxdepth 2 -type f -name 'SKILL.md' | LC_ALL=C sort)
}

payload_fingerprint() {
  find "$CLAUDE_PAYLOAD" "$CODEX_PAYLOAD" -type f -print \
    | LC_ALL=C sort \
    | while IFS= read -r file; do
        shasum -a 256 "$file"
      done
}

section "plugin payload — generated platform payloads are clean"

set_test "payload builder exists"
assert_file_exists "$BUILDER"

set_test "payload builder rebuilds from scratch"
builder_output=""
if builder_output=$(cd "$REPO_ROOT" && bash "$BUILDER" 2>&1); then
  _pass
else
  _fail "$builder_output"
fi

set_test "Claude payload directory exists"
if [ -d "$CLAUDE_PAYLOAD" ]; then _pass; else _fail "missing $CLAUDE_PAYLOAD"; fi

set_test "Codex payload directory exists"
if [ -d "$CODEX_PAYLOAD" ]; then _pass; else _fail "missing $CODEX_PAYLOAD"; fi

set_test "Claude marketplace installs the Claude dist payload"
claude_source=$(cd "$REPO_ROOT" && python3 -c 'import json; print(json.load(open(".claude-plugin/marketplace.json"))["plugins"][0]["source"])')
assert_eq "./dist/claude/speckit-pro" "$claude_source" "Claude marketplace source"

set_test "Codex marketplace installs the Codex dist payload"
codex_source=$(cd "$REPO_ROOT" && python3 -c 'import json; print(json.load(open(".agents/plugins/marketplace.json"))["plugins"][0]["source"]["path"])')
assert_eq "./dist/codex/speckit-pro" "$codex_source" "Codex marketplace source.path"

set_test "Claude marketplace path resolves to a payload"
if [ -d "$REPO_ROOT/${claude_source#./}" ]; then _pass; else _fail "missing $REPO_ROOT/${claude_source#./}"; fi

set_test "Codex marketplace path resolves to a payload"
if [ -d "$REPO_ROOT/${codex_source#./}" ]; then _pass; else _fail "missing $REPO_ROOT/${codex_source#./}"; fi

for forbidden in .codex-plugin codex-skills codex-agents codex-hooks.json; do
  set_test "Claude payload excludes $forbidden"
  if [ -e "$CLAUDE_PAYLOAD/$forbidden" ]; then
    _fail "$forbidden exists in the Claude payload"
  else
    _pass
  fi
done

for forbidden in .claude-plugin codex-skills agents; do
  set_test "Codex payload excludes $forbidden"
  if [ -e "$CODEX_PAYLOAD/$forbidden" ]; then
    _fail "$forbidden exists in the Codex payload"
  else
    _pass
  fi
done

set_test "Claude payload keeps the Claude skill set"
expected_claude_count=$(count_skill_entrypoints "$SOURCE_ROOT/skills")
actual_claude_count=$(count_skill_entrypoints "$CLAUDE_PAYLOAD/skills")
assert_eq "$expected_claude_count" "$actual_claude_count" "Claude skill count"

set_test "Codex payload keeps exactly the Codex skill set"
expected_codex_set=$(skill_entrypoint_set "$SOURCE_ROOT/codex-skills")
actual_codex_set=$(skill_entrypoint_set "$CODEX_PAYLOAD/skills")
assert_eq "$expected_codex_set" "$actual_codex_set" "Codex skill entrypoints"

set_test "Codex payload manifest exposes skills at ./skills/"
codex_manifest_skills=$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["skills"])' "$CODEX_PAYLOAD/.codex-plugin/plugin.json")
assert_eq "./skills/" "$codex_manifest_skills" "Codex manifest skills"

set_test "Codex payload has no duplicate nested skill entrypoints"
nested_codex_skills=$(find "$CODEX_PAYLOAD/skills" -mindepth 3 -type f -name 'SKILL.md' | wc -l | tr -d ' ')
assert_eq "0" "$nested_codex_skills" "nested Codex SKILL.md count"

set_test "Payload files do not reference source-tree skill paths"
path_escape_matches=$(rg -n '\.\./\.\./(?:skills|codex-skills)/|\.\./\.\./\.\./(?:skills|codex-skills)/' "$CLAUDE_PAYLOAD" "$CODEX_PAYLOAD" || true)
assert_eq "" "$path_escape_matches" "source-tree path references"

set_test "Payload rebuild is deterministic"
first_fingerprint=$(payload_fingerprint)
if rebuild_output=$(cd "$REPO_ROOT" && bash "$BUILDER" 2>&1); then
  second_fingerprint=$(payload_fingerprint)
  assert_eq "$first_fingerprint" "$second_fingerprint" "payload fingerprint"
else
  _fail "$rebuild_output"
fi

set_test "release-please extra-files stay inside package paths"
release_please_bad_paths=$(cd "$REPO_ROOT" && python3 -c '
import json
data = json.load(open("release-please-config.json"))
bad = []
for package, config in data.get("packages", {}).items():
    for extra in config.get("extra-files", []):
        path = extra.get("path", "")
        if path.startswith("../") or "/../" in path or path == "..":
            bad.append(f"{package}: {path}")
print("\n".join(bad))
')
assert_eq "" "$release_please_bad_paths" "release-please illegal pathing characters"

set_test "CI committed payload files are current"
if [ "${GITHUB_ACTIONS:-}" = "true" ]; then
  if diff_output=$(git -C "$REPO_ROOT" diff --exit-code -- dist .claude-plugin/marketplace.json .agents/plugins/marketplace.json release-please-config.json 2>&1); then
    _pass
  else
    _fail "$diff_output"
  fi
else
  _pass
fi

test_summary
