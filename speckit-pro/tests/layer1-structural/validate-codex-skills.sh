#!/usr/bin/env bash
# validate-codex-skills.sh — Structural validation for Codex skill directories
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

CODEX_SKILLS_DIR="$PLUGIN_ROOT/codex-skills"
# Canonical skill list — keep in sync with the case block in the
# "corresponding source artifact exists" test below.
SKILLS=(speckit-autopilot speckit-coach speckit-setup speckit-status speckit-resolve-pr install)

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

  if [ "$skill" = "speckit-autopilot" ]; then
    set_test "speckit-autopilot: requires update_plan as the progress contract"
    assert_contains "$body" "update_plan"

    set_test "speckit-autopilot: requires durable autopilot-state.json persistence"
    assert_contains "$body" "autopilot-state.json"

    set_test "speckit-autopilot: names Codex-native delegation tools"
    if [[ "$body" == *"spawn_agent"* && "$body" == *"wait_agent"* ]]; then
      _pass
    else
      _fail "expected both spawn_agent and wait_agent in the Codex autopilot skill"
    fi

    set_test "speckit-autopilot: validates a single in_progress item before phase execution"
    assert_contains "$body" 'Exactly one plan item is `in_progress`'

    set_test "speckit-autopilot: validates installed Codex subagent paths"
    if [[ "$body" == *".codex/agents/"* && "$body" == *"~/.codex/agents/"* ]]; then
      _pass
    else
      _fail "expected both project and user Codex subagent paths in the autopilot skill"
    fi

    set_test "speckit-autopilot: fails closed to the install skill when subagents are missing"
    assert_contains "$body" '$speckit-pro:install'

    set_test "speckit-autopilot: documents the optional Spark helper"
    assert_contains "$body" 'autopilot-fast-helper'

    set_test "speckit-autopilot: keeps the Spark helper advisory and parent-only"
    if [[ "$body" == *"Only the parent orchestrator may call this helper"* && "$body" == *"latency optimization, not a dependency"* ]]; then
      _pass
    else
      _fail "expected parent-only and optional guardrails for autopilot-fast-helper"
    fi

    set_test "speckit-autopilot: excludes Claude-only runtime primitives"
    if echo "$body" | grep -qE 'TaskCreate|TaskUpdate|Agent\(|Bash\(|Opus-class|Opus 4\.6|/model opus|/effort max'; then
      _fail "found Claude-only primitive or runtime guidance in Codex autopilot skill"
    else
      _pass
    fi
  fi

  set_test "${skill}: agents/openai.yaml allow_implicit_invocation policy"
  if [ -f "$SKILL_DIR/agents/openai.yaml" ]; then
    yaml_content=$(cat "$SKILL_DIR/agents/openai.yaml")
    case "$skill" in
      speckit-setup|speckit-autopilot|speckit-resolve-pr|install)
        if echo "$yaml_content" | grep -q 'allow_implicit_invocation: false'; then
          _pass
        else
          _fail "mutation-heavy skill must have allow_implicit_invocation: false"
        fi
        ;;
      speckit-coach|speckit-status)
        if echo "$yaml_content" | grep -q 'allow_implicit_invocation: true'; then
          _pass
        else
          _fail "read-only skill must have allow_implicit_invocation: true"
        fi
        ;;
      *)
        _fail "no implicit-invocation policy expectation defined for '$skill'; update validate-codex-skills.sh"
        ;;
    esac
  else
    _fail "agents/openai.yaml not found; skipping policy check"
  fi

  # Map each Codex skill to its Claude Code source artifact.
  # When adding a new skill to the SKILLS array above, add a case branch here.
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
    install)
      _pass
      ;;
    *)
      _fail "no corresponding source artifact mapping defined for skill '$skill'; update validate-codex-skills.sh"
      ;;
  esac

  # speckit-setup hard-codes a reference to the shared workflow template —
  # verify the file it points to actually exists.
  if [ "$skill" = "speckit-setup" ]; then
    set_test "speckit-setup: referenced workflow template exists (skills/speckit-coach/templates/workflow-template.md)"
    assert_file_exists "$PLUGIN_ROOT/skills/speckit-coach/templates/workflow-template.md"
  fi

  if [ "$skill" = "install" ]; then
    set_test "install: installer script exists"
    assert_file_exists "$SKILL_DIR/scripts/install-codex-agents.sh"
  fi
done

test_summary
