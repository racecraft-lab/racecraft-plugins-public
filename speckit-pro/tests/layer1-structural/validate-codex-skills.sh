#!/usr/bin/env bash
# validate-codex-skills.sh — Structural validation for Codex skill directories
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

CODEX_SKILLS_DIR="$PLUGIN_ROOT/codex-skills"
SKILLS=(speckit-autopilot speckit-coach speckit-setup speckit-status speckit-resolve-pr)

# Claude Code-only frontmatter keys that must NOT appear in Codex skills
CC_ONLY_KEYS=(user-invokable license argument-hint)

for skill in "${SKILLS[@]}"; do
  SKILL_DIR="$CODEX_SKILLS_DIR/$skill"
  SKILL_FILE="$SKILL_DIR/SKILL.md"

  section "codex-skills/${skill}/SKILL.md"

  set_test "${skill}: SKILL.md exists"
  assert_file_exists "$SKILL_FILE"

  if [ ! -f "$SKILL_FILE" ]; then
    continue
  fi

  first_line=$(head -n1 "$SKILL_FILE")

  set_test "${skill}: YAML frontmatter present (starts with ---)"
  assert_eq "---" "$first_line" "first line must be ---"

  set_test "${skill}: has closing ---"
  fence_count=$(grep -c '^---$' "$SKILL_FILE") || fence_count=0
  if [ "$fence_count" -ge 2 ]; then
    _pass
  else
    _fail "expected at least 2 '---' lines, found $fence_count"
  fi

  # Extract frontmatter (between first and second ---)
  frontmatter=$(awk '/^---$/{n++; if(n==1){next} if(n==2){exit}} n==1{print}' "$SKILL_FILE")

  set_test "${skill}: has name: field"
  assert_contains "$frontmatter" "name:"

  set_test "${skill}: has description: field"
  assert_contains "$frontmatter" "description:"

  set_test "${skill}: no Claude Code-only frontmatter keys"
  bad_keys=""
  for key in "${CC_ONLY_KEYS[@]}"; do
    if echo "$frontmatter" | grep -qE "^${key}:"; then
      bad_keys="$bad_keys $key"
    fi
  done
  if [ -z "$bad_keys" ]; then
    _pass
  else
    _fail "Claude Code-only keys found:$bad_keys"
  fi

  set_test "${skill}: agents/openai.yaml sidecar exists"
  assert_file_exists "$SKILL_DIR/agents/openai.yaml"

  set_test "${skill}: body word count between 500 and 8000"
  body=$(awk 'BEGIN{n=0} /^---$/{n++; if(n==2){found=1; next}} found{print}' "$SKILL_FILE")
  word_count=$(echo "$body" | wc -w | tr -d ' ')
  if [ "$word_count" -ge 500 ] && [ "$word_count" -le 8000 ]; then
    _pass
  else
    _fail "body is $word_count words (need 500-8000)"
  fi

  set_test "${skill}: corresponding source artifact exists"
  case "$skill" in
    speckit-autopilot|speckit-coach)
      if [ -f "$PLUGIN_ROOT/skills/$skill/SKILL.md" ]; then
        _pass
      else
        _fail "corresponding Claude skill not found at skills/$skill/SKILL.md"
      fi
      ;;
    speckit-setup)
      if [ -f "$PLUGIN_ROOT/commands/setup.md" ]; then
        _pass
      else
        _fail "corresponding Claude command not found at commands/setup.md"
      fi
      ;;
    speckit-status)
      if [ -f "$PLUGIN_ROOT/commands/status.md" ]; then
        _pass
      else
        _fail "corresponding Claude command not found at commands/status.md"
      fi
      ;;
    speckit-resolve-pr)
      if [ -f "$PLUGIN_ROOT/commands/resolve-pr.md" ]; then
        _pass
      else
        _fail "corresponding Claude command not found at commands/resolve-pr.md"
      fi
      ;;
    *)
      _fail "no corresponding source artifact mapping defined for skill '$skill'; update validate-codex-skills.sh"
      ;;
  esac
done

test_summary
