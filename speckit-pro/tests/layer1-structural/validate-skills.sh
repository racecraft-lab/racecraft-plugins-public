#!/usr/bin/env bash
# validate-skills.sh — Structural validation for all skill directories
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

SKILLS_DIR="$PLUGIN_ROOT/skills"
SKILLS=(speckit-autopilot speckit-coach)
ALLOWED_KEYS="name description license allowed-tools metadata compatibility user-invokable argument-hint"

for skill in "${SKILLS[@]}"; do
  SKILL_DIR="$SKILLS_DIR/$skill"
  SKILL_FILE="$SKILL_DIR/SKILL.md"

  section "skills/${skill}/SKILL.md"

  set_test "${skill}: SKILL.md exists"
  assert_file_exists "$SKILL_FILE"

  if [ ! -f "$SKILL_FILE" ]; then
    continue
  fi

  content=$(cat "$SKILL_FILE")
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

  # Extract frontmatter
  frontmatter=$(awk '/^---$/{n++; if(n==1){next} if(n==2){exit}} n==1{print}' "$SKILL_FILE")

  # Extract name value (handle multiline YAML — name is always a simple key)
  name_val=$(echo "$frontmatter" | grep -m1 '^name:' | sed 's/^name:[[:space:]]*//' | tr -d '"' | tr -d "'")

  set_test "${skill}: name: field exists and is kebab-case"
  if [ -z "$name_val" ]; then
    _fail "name field is missing"
  else
    assert_match "$name_val" '^[a-z][a-z0-9]*(-[a-z0-9]+)*$' "name must be kebab-case"
  fi

  set_test "${skill}: name max 64 chars"
  name_len=${#name_val}
  if [ "$name_len" -le 64 ]; then
    _pass
  else
    _fail "name is $name_len chars (max 64)"
  fi

  set_test "${skill}: description: field exists"
  assert_contains "$frontmatter" "description:"

  # Extract description value (may be a YAML block scalar with > or |)
  desc_val=$(echo "$frontmatter" | python3 -c "
import sys, re
text = sys.stdin.read()
# Find description value — handles inline, quoted, and block scalar (> or |)
m = re.search(r'description:\s*([>\|])\s*\n((?:\s+.*\n?)*)', text)
if m:
    # Block scalar: join continuation lines, strip leading whitespace
    lines = m.group(2).split('\n')
    print(' '.join(l.strip() for l in lines if l.strip()))
else:
    m = re.search(r'description:\s*\"([^\"]*)\"|description:\s*(.+)', text)
    if m:
        print((m.group(1) or m.group(2) or '').strip())
    else:
        print('')
" 2>/dev/null)

  set_test "${skill}: description max 1024 chars"
  desc_len=${#desc_val}
  if [ "$desc_len" -le 1024 ]; then
    _pass
  else
    _fail "description is $desc_len chars (max 1024)"
  fi

  set_test "${skill}: description has no angle brackets"
  if echo "$desc_val" | grep -q '[<>]'; then
    _fail "description contains angle brackets"
  else
    _pass
  fi

  set_test "${skill}: only allowed frontmatter keys"
  # Extract top-level keys from frontmatter (lines starting at col 0 with a colon)
  found_keys=$(echo "$frontmatter" | grep -oE '^[a-zA-Z][a-zA-Z0-9_-]*:' | sed 's/:$//')
  bad_keys=""
  for key in $found_keys; do
    is_allowed=false
    for allowed in $ALLOWED_KEYS; do
      if [ "$key" = "$allowed" ]; then
        is_allowed=true
        break
      fi
    done
    if [ "$is_allowed" = "false" ]; then
      bad_keys="$bad_keys $key"
    fi
  done
  if [ -z "$bad_keys" ]; then
    _pass
  else
    _fail "disallowed frontmatter keys:$bad_keys"
  fi

  set_test "${skill}: body content exists and is > 100 chars"
  body=$(awk 'BEGIN{n=0} /^---$/{n++; if(n==2){found=1; next}} found{print}' "$SKILL_FILE")
  body_trimmed=$(echo "$body" | sed '/^[[:space:]]*$/d')
  body_len=${#body_trimmed}
  if [ "$body_len" -gt 100 ]; then
    _pass
  else
    _fail "body is only $body_len chars (need > 100)"
  fi

  set_test "${skill}: body word count between 500 and 8000"
  word_count=$(echo "$body" | wc -w | tr -d ' ')
  if [ "$word_count" -ge 500 ] && [ "$word_count" -le 8000 ]; then
    _pass
  else
    _fail "body is $word_count words (need 500-8000)"
  fi

  set_test "${skill}: references directory exists if present"
  if [ -d "$SKILL_DIR/references" ]; then
    _pass
  else
    # Check if skill likely needs references (both skills have them)
    _fail "references directory not found at $SKILL_DIR/references"
  fi
done

test_summary
