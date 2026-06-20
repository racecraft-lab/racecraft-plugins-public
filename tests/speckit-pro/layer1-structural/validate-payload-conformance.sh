#!/usr/bin/env bash
# validate-payload-conformance.sh — Layer 1 format conformance for BUILT payloads.
#
# Asserts that the BUILT `dist/claude/speckit-pro` and `dist/codex/speckit-pro`
# payloads conform to each runtime's documented plugin/skill FORMAT. This is
# distinct from — and complementary to — the existing checks:
#   - validate-skills / validate-plugin / validate-codex-*  → validate the SOURCE
#     authoring tree (speckit-pro/), not the shipped payloads.
#   - validate-payload-completeness                         → built Claude body
#     truncation only.
# Nothing else asserts that the BUILT, shipped payloads match each runtime's
# manifest + skill format. That gap is what this check closes.
#
# Grounding — official documentation, captured 2026-06-20:
#   Claude — https://code.claude.com/docs/en/plugins-reference
#     • Manifest at `.claude-plugin/plugin.json`; quote: "If you include a
#       manifest, `name` is the only required field." `version` is an optional
#       string.
#     • Skills live at `skills/<name>/SKILL.md`.
#     • SKILL.md YAML frontmatter requires `name` and `description`.
#   Codex — https://developers.openai.com/codex/plugins/build
#     • Manifest at `.codex-plugin/plugin.json` requires `name` (kebab-case),
#       `version` (semver), and `description`.
#     • Quote: "Only `plugin.json` belongs in `.codex-plugin/`. Keep `skills/`,
#       `hooks/`, `assets/`, `.mcp.json`, and `.app.json` at the plugin root."
#     • Skills live at `skills/<name>/SKILL.md`; frontmatter has `name` +
#       `description`. (`agents/openai.yaml` is an OPTIONAL MCP-dependency
#       sidecar — not required by the format — so it is NOT asserted here.)
#
# Fail-closed (FR-012): a missing built payload, an empty skills glob, malformed
# JSON, or an unreadable file is a FAILURE, never a vacuous pass.
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

CLAUDE_ROOT="$REPO_ROOT/dist/claude/speckit-pro"
CODEX_ROOT="$REPO_ROOT/dist/codex/speckit-pro"

# Skill/plugin name charset shared by both runtimes (lowercase kebab-case).
NAME_RE='^[a-z0-9][a-z0-9-]*$'

if ! command -v jq >/dev/null 2>&1; then
  echo "validate-payload-conformance.sh: jq is required" >&2
  exit 2
fi

# fm_value <skill-file> <key>
# Print the scalar value of a TOP-LEVEL YAML frontmatter key (line begins with
# `<key>:`), read only from the leading `---` … `---` block. Surrounding quotes
# are stripped in the caller. A block scalar (`>` / `|`) prints the sentinel
# `__BLOCK__` (value lives on following lines — treated as present + non-empty).
# Empty output means the key is absent. TOTAL — never errors.
fm_value() {
  awk -v key="$2" '
    NR == 1 { if ($0 == "---") { infm = 1; next } else { exit } }
    infm && $0 == "---" { exit }
    infm && index($0, key ":") == 1 {
      val = substr($0, length(key) + 2)
      sub(/^[ \t]+/, "", val)
      sub(/[ \t]+$/, "", val)
      if (val ~ /^[>|][-+]?[0-9]*$/) { print "__BLOCK__"; exit }
      print val
      exit
    }
  ' "$1" 2>/dev/null || true
}

# strip_quotes <value> — remove a single matched pair of surrounding quotes.
strip_quotes() {
  local v="$1"
  case "$v" in
    \"*\") v="${v#\"}"; v="${v%\"}" ;;
    \'*\') v="${v#\'}"; v="${v%\'}" ;;
  esac
  printf '%s' "$v"
}

# assert_skill_frontmatter <runtime-label> <skill-file>
# Assert the SKILL.md opens with a `---` frontmatter fence and carries non-empty
# `name` and `description` keys; `name` must match the kebab-case charset.
assert_skill_frontmatter() {
  local label="$1" file="$2" name desc
  local sk; sk="$(basename "$(dirname "$file")")"

  set_test "[$label/$sk] SKILL.md opens with a '---' frontmatter fence"
  if [ "$(head -1 "$file" 2>/dev/null)" = "---" ]; then _pass; else
    _fail "$file does not begin with a YAML frontmatter fence"; return
  fi

  name="$(strip_quotes "$(fm_value "$file" name)")"
  set_test "[$label/$sk] frontmatter has a non-empty 'name' (required)"
  if [ -n "$name" ]; then _pass; else _fail "$file frontmatter is missing 'name'"; fi

  set_test "[$label/$sk] frontmatter 'name' is kebab-case ('$name')"
  if printf '%s' "$name" | grep -Eq "$NAME_RE"; then _pass; else
    _fail "$file 'name' ('$name') is not lowercase kebab-case ($NAME_RE)"; fi

  desc="$(fm_value "$file" description)"
  set_test "[$label/$sk] frontmatter has a non-empty 'description' (required)"
  if [ -n "$desc" ]; then _pass; else _fail "$file frontmatter is missing 'description'"; fi
}

# collect_skills <skills-dir> — emit each `<skills-dir>/*/SKILL.md` that exists.
collect_skills() {
  local d="$1" f
  for f in "$d"/*/SKILL.md; do [ -f "$f" ] && printf '%s\n' "$f"; done
}

# ===========================================================================
# Claude payload — code.claude.com/docs/en/plugins-reference
# ===========================================================================
section "Claude payload conformance (dist/claude/speckit-pro)"

set_test "[claude] built payload root exists ($CLAUDE_ROOT)"
if [ -d "$CLAUDE_ROOT" ]; then _pass; else
  _fail "Claude payload missing — run scripts/build-plugin-payloads.sh"; test_summary; exit $?
fi

CLAUDE_MANIFEST="$CLAUDE_ROOT/.claude-plugin/plugin.json"
set_test "[claude] manifest exists at .claude-plugin/plugin.json"
if [ -f "$CLAUDE_MANIFEST" ]; then _pass; else _fail "missing $CLAUDE_MANIFEST"; fi

set_test "[claude] manifest is valid JSON"
if jq -e . "$CLAUDE_MANIFEST" >/dev/null 2>&1; then _pass; else _fail "invalid JSON: $CLAUDE_MANIFEST"; fi

# Doc: `name` is the ONLY required manifest field.
set_test "[claude] manifest has the required 'name' (string, non-empty)"
cname="$(jq -r 'if (.name|type)=="string" then .name else empty end' "$CLAUDE_MANIFEST" 2>/dev/null || true)"
if [ -n "$cname" ]; then _pass; else _fail "manifest 'name' missing or not a string"; fi

# Doc: `version`, if present, is a string.
set_test "[claude] manifest 'version', if present, is a string"
if jq -e 'has("version")|not' "$CLAUDE_MANIFEST" >/dev/null 2>&1 \
   || jq -e '(.version|type)=="string"' "$CLAUDE_MANIFEST" >/dev/null 2>&1; then _pass; else
  _fail "manifest 'version' present but not a string"; fi

set_test "[claude] skills/ directory exists in the payload"
if [ -d "$CLAUDE_ROOT/skills" ]; then _pass; else _fail "missing $CLAUDE_ROOT/skills"; fi

# Fail-closed: at least one built skill.
claude_skills=()
while IFS= read -r f; do claude_skills+=("$f"); done < <(collect_skills "$CLAUDE_ROOT/skills")
set_test "[claude] at least one skills/*/SKILL.md is present"
if [ "${#claude_skills[@]}" -gt 0 ]; then _pass; else
  _fail "no SKILL.md under $CLAUDE_ROOT/skills/*/ — refusing to pass vacuously"; test_summary; exit $?
fi

for f in "${claude_skills[@]}"; do assert_skill_frontmatter "claude" "$f"; done

# ===========================================================================
# Codex payload — developers.openai.com/codex/plugins/build
# ===========================================================================
section "Codex payload conformance (dist/codex/speckit-pro)"

set_test "[codex] built payload root exists ($CODEX_ROOT)"
if [ -d "$CODEX_ROOT" ]; then _pass; else
  _fail "Codex payload missing — run scripts/build-plugin-payloads.sh"; test_summary; exit $?
fi

CODEX_MANIFEST="$CODEX_ROOT/.codex-plugin/plugin.json"
set_test "[codex] manifest exists at .codex-plugin/plugin.json"
if [ -f "$CODEX_MANIFEST" ]; then _pass; else _fail "missing $CODEX_MANIFEST"; fi

set_test "[codex] manifest is valid JSON"
if jq -e . "$CODEX_MANIFEST" >/dev/null 2>&1; then _pass; else _fail "invalid JSON: $CODEX_MANIFEST"; fi

# Doc: name (kebab-case) + version + description are all REQUIRED.
set_test "[codex] manifest 'name' is present, a string, and kebab-case"
xname="$(jq -r 'if (.name|type)=="string" then .name else empty end' "$CODEX_MANIFEST" 2>/dev/null || true)"
if [ -n "$xname" ] && printf '%s' "$xname" | grep -Eq "$NAME_RE"; then _pass; else
  _fail "manifest 'name' missing/not-a-string/not-kebab-case ('$xname')"; fi

set_test "[codex] manifest 'version' is present and non-empty (semver)"
xver="$(jq -r 'if (.version|type)=="string" then .version else empty end' "$CODEX_MANIFEST" 2>/dev/null || true)"
if [ -n "$xver" ]; then _pass; else _fail "manifest 'version' missing or not a string"; fi

set_test "[codex] manifest 'description' is present and non-empty"
xdesc="$(jq -r 'if (.description|type)=="string" and (.description|length)>0 then .description else empty end' "$CODEX_MANIFEST" 2>/dev/null || true)"
if [ -n "$xdesc" ]; then _pass; else _fail "manifest 'description' missing or empty"; fi

# Doc: "Only plugin.json belongs in .codex-plugin/".
set_test "[codex] .codex-plugin/ contains ONLY plugin.json"
extra="$(find "$CODEX_ROOT/.codex-plugin" -mindepth 1 -not -name plugin.json 2>/dev/null || true)"
if [ -z "$extra" ]; then _pass; else
  _fail ".codex-plugin/ must contain only plugin.json; found also: $(printf '%s' "$extra" | tr '\n' ' ')"; fi

# Doc: skills/ lives at the plugin ROOT; the manifest 'skills' pointer (if set)
# must resolve to it.
set_test "[codex] skills/ directory exists at the plugin root"
if [ -d "$CODEX_ROOT/skills" ]; then _pass; else _fail "missing $CODEX_ROOT/skills"; fi

set_test "[codex] manifest 'skills' pointer, if set, resolves to a real directory"
skills_ptr="$(jq -r '.skills // empty' "$CODEX_MANIFEST" 2>/dev/null || true)"
if [ -z "$skills_ptr" ]; then
  _pass   # optional pointer absent — acceptable
else
  rel="${skills_ptr#./}"; rel="${rel%/}"
  if [ -d "$CODEX_ROOT/$rel" ]; then _pass; else
    _fail "manifest 'skills' ('$skills_ptr') does not resolve to a directory under the payload"; fi
fi

codex_skills=()
while IFS= read -r f; do codex_skills+=("$f"); done < <(collect_skills "$CODEX_ROOT/skills")
set_test "[codex] at least one skills/*/SKILL.md is present"
if [ "${#codex_skills[@]}" -gt 0 ]; then _pass; else
  _fail "no SKILL.md under $CODEX_ROOT/skills/*/ — refusing to pass vacuously"; test_summary; exit $?
fi

for f in "${codex_skills[@]}"; do assert_skill_frontmatter "codex" "$f"; done

test_summary
