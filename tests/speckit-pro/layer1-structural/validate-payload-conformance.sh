#!/usr/bin/env bash
# validate-payload-conformance.sh — Layer 1 format conformance for BUILT payloads.
#
# Asserts that the BUILT `dist/claude/speckit-pro` and `dist/codex/speckit-pro`
# payloads conform to each runtime's documented PLUGIN + skill format. This is
# distinct from — and complementary to — the existing checks:
#   - validate-skills / validate-plugin / validate-agents / validate-hooks /
#     validate-codex-*  → validate the SOURCE authoring tree (speckit-pro/), not
#     the shipped payloads.
#   - validate-payload-completeness  → built Claude skill body truncation only.
# Nothing else asserts that the BUILT, shipped payloads match each runtime's
# manifest + component format. That gap is what this check closes — across the
# WHOLE plugin (manifest, skills, agents, hooks), for both runtimes.
#
# Grounding — official documentation, captured 2026-06-20:
#   Claude — https://code.claude.com/docs/en/plugins-reference
#     • Manifest `.claude-plugin/plugin.json`; quote: "If you include a manifest,
#       `name` is the only required field." `version` optional string. Component
#       pointers (`agents`, `hooks`, `mcpServers`, …) are optional string|array.
#     • Skills: `skills/<name>/SKILL.md`; frontmatter requires `name` +
#       `description`.
#     • Agents: `agents/` directory of `.md` files with frontmatter (`name`,
#       `description`, `model`, `effort`, `tools`, …).
#     • Hooks: `hooks/hooks.json`; JSON with a top-level `hooks` object.
#   Codex — https://developers.openai.com/codex/plugins/build
#     • Manifest `.codex-plugin/plugin.json` requires `name` (kebab-case),
#       `version` (semver), `description`. Quote: "Only `plugin.json` belongs in
#       `.codex-plugin/`." Component pointers (`skills`, `hooks`, …) are paths.
#     • Skills: `skills/<name>/SKILL.md`; frontmatter `name` + `description`.
#     • Agents: bundled as `codex-agents/*.toml` (name/description/model/…); the
#       builder path-rewrites these, so the BUILT copies are verified here.
#     • Hooks: `codex-hooks.json`; JSON with a top-level `hooks` object.
#   (`agents/openai.yaml` is an OPTIONAL MCP-dependency sidecar — not a required
#    format element — so it is NOT asserted here.)
#
# Fail-closed (FR-012): a missing built payload, an empty component glob,
# malformed JSON, or an unreadable file is a FAILURE, never a vacuous pass.
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

CLAUDE_ROOT="$REPO_ROOT/dist/claude/speckit-pro"
CODEX_ROOT="$REPO_ROOT/dist/codex/speckit-pro"

# Skill/agent/plugin name charset shared by both runtimes (lowercase kebab-case).
NAME_RE='^[a-z0-9][a-z0-9-]*$'

# Documented manifest keys that, when set to a string, point at a bundled
# component file/dir and therefore must resolve inside the payload.
POINTER_KEYS="skills hooks mcpServers apps agents commands lsp"

if ! command -v jq >/dev/null 2>&1; then
  echo "validate-payload-conformance.sh: jq is required" >&2
  exit 2
fi

# fm_value <md-file> <key> — print a TOP-LEVEL YAML frontmatter scalar (line
# begins with `<key>:`), read only from the leading `---` … `---` block. A block
# scalar (`>` / `|`) prints the sentinel `__BLOCK__` (value on following lines —
# treated as present + non-empty). Empty output = key absent. TOTAL.
fm_value() {
  awk -v key="$2" '
    NR == 1 { if ($0 == "---") { infm = 1; next } else { exit } }
    infm && $0 == "---" { exit }
    infm && index($0, key ":") == 1 {
      val = substr($0, length(key) + 2)
      sub(/^[ \t]+/, "", val); sub(/[ \t]+$/, "", val)
      if (val ~ /^[>|][-+]?[0-9]*$/) { print "__BLOCK__"; exit }
      print val; exit
    }
  ' "$1" 2>/dev/null || true
}

strip_quotes() {
  local v="$1"
  case "$v" in
    \"*\") v="${v#\"}"; v="${v%\"}" ;;
    \'*\') v="${v#\'}"; v="${v%\'}" ;;
  esac
  printf '%s' "$v"
}

# fm_has_key <md-file> <key> — exit 0 iff the leading frontmatter declares a
# top-level `<key>:` line (presence test, value-agnostic).
fm_has_key() {
  awk -v key="$2" '
    NR == 1 { if ($0 == "---") { infm = 1; next } else { exit } }
    infm && $0 == "---" { exit }
    infm && index($0, key ":") == 1 { found = 1; exit }
    END { exit(found ? 0 : 1) }
  ' "$1" 2>/dev/null
}

# assert_md_frontmatter <label> <item> <md-file>
# A Markdown component (skill or agent) must open with a `---` fence and carry a
# non-empty kebab-case `name` + non-empty `description` — the identity fields
# both Claude skills and Claude agents require.
assert_md_frontmatter() {
  local label="$1" item="$2" file="$3" name desc

  set_test "[$label/$item] opens with a '---' frontmatter fence"
  if [ "$(head -1 "$file" 2>/dev/null)" = "---" ]; then _pass; else
    _fail "$file does not begin with a YAML frontmatter fence"; return; fi

  name="$(strip_quotes "$(fm_value "$file" name)")"
  set_test "[$label/$item] frontmatter has a non-empty 'name' (required)"
  if [ -n "$name" ]; then _pass; else _fail "$file frontmatter is missing 'name'"; fi

  set_test "[$label/$item] frontmatter 'name' is kebab-case ('$name')"
  if printf '%s' "$name" | grep -Eq "$NAME_RE"; then _pass; else
    _fail "$file 'name' ('$name') is not lowercase kebab-case"; fi

  desc="$(fm_value "$file" description)"
  set_test "[$label/$item] frontmatter has a non-empty 'description' (required)"
  if [ -n "$desc" ]; then _pass; else _fail "$file frontmatter is missing 'description'"; fi
}

# assert_no_forbidden_agent_fields <label> <item> <md-file>
# plugins-reference: "For security reasons, `hooks`, `mcpServers`, and
# `permissionMode` are not supported for plugin-shipped agents." A built plugin
# agent must therefore NOT declare any of these top-level frontmatter keys.
assert_no_forbidden_agent_fields() {
  local label="$1" item="$2" file="$3" k
  for k in permissionMode hooks mcpServers; do
    set_test "[$label/$item] does NOT declare plugin-unsupported '$k' (plugins-reference)"
    if fm_has_key "$file" "$k"; then
      _fail "$file declares '$k' — not supported for plugin-shipped agents per official docs"
    else _pass; fi
  done
}

# assert_toml_agent <label> <toml-file> — a built Codex agent must remain a
# readable TOML carrying its identity (`name = ` + `description = `) after the
# builder's path rewrite. Light by design: the full TOML schema is pinned by the
# SOURCE validator (validate-codex-agents); here we assert the BUILT copy did not
# lose its identity.
assert_toml_agent() {
  local label="$1" file="$2" item; item="$(basename "$file" .toml)"
  set_test "[$label/$item] built agent .toml has a 'name =' key"
  if grep -Eq '^name[[:space:]]*=' "$file" 2>/dev/null; then _pass; else
    _fail "$file is missing a top-level 'name =' key"; fi
  set_test "[$label/$item] built agent .toml has a 'description =' key"
  if grep -Eq '^description[[:space:]]*=' "$file" 2>/dev/null; then _pass; else
    _fail "$file is missing a top-level 'description =' key"; fi
}

# assert_hooks_json <label> <hooks-file> — present, valid JSON, top-level `hooks`.
assert_hooks_json() {
  local label="$1" file="$2"
  set_test "[$label] hooks file exists ($file)"
  if [ -f "$file" ]; then _pass; else _fail "missing hooks file: $file"; return; fi
  set_test "[$label] hooks file is valid JSON"
  if jq -e . "$file" >/dev/null 2>&1; then _pass; else _fail "invalid JSON: $file"; return; fi
  set_test "[$label] hooks file has a top-level 'hooks' object"
  if jq -e '(.hooks|type)=="object"' "$file" >/dev/null 2>&1; then _pass; else
    _fail "$file has no top-level 'hooks' object"; fi
}

# assert_pointers_resolve <label> <manifest> <payload-root>
# Every documented manifest key that is a STRING path must resolve to a file or
# directory inside the payload. (Array-form pointers are rare and not used here;
# they are skipped with the count unaffected.)
assert_pointers_resolve() {
  local label="$1" manifest="$2" root="$3" key val rel
  for key in $POINTER_KEYS; do
    val="$(jq -r --arg k "$key" 'if (.[$k]|type)=="string" then .[$k] else empty end' "$manifest" 2>/dev/null || true)"
    [ -n "$val" ] || continue
    rel="${val#./}"; rel="${rel%/}"
    set_test "[$label] manifest '$key' pointer resolves in payload ('$val')"
    if [ -e "$root/$rel" ]; then _pass; else
      _fail "manifest '$key' ('$val') does not resolve to a path under the payload"; fi
  done
}

# ===========================================================================
# Claude payload — code.claude.com/docs/en/plugins-reference
# ===========================================================================
section "Claude payload conformance (dist/claude/speckit-pro)"

set_test "[claude] built payload root exists ($CLAUDE_ROOT)"
if [ -d "$CLAUDE_ROOT" ]; then _pass; else
  _fail "Claude payload missing — run scripts/build-plugin-payloads.sh"; test_summary; exit $?; fi

CLAUDE_MANIFEST="$CLAUDE_ROOT/.claude-plugin/plugin.json"
set_test "[claude] manifest exists at .claude-plugin/plugin.json"
if [ -f "$CLAUDE_MANIFEST" ]; then _pass; else _fail "missing $CLAUDE_MANIFEST"; fi

set_test "[claude] manifest is valid JSON"
if jq -e . "$CLAUDE_MANIFEST" >/dev/null 2>&1; then _pass; else _fail "invalid JSON: $CLAUDE_MANIFEST"; fi

set_test "[claude] manifest has the required 'name' (string, non-empty)"
cname="$(jq -r 'if (.name|type)=="string" then .name else empty end' "$CLAUDE_MANIFEST" 2>/dev/null || true)"
if [ -n "$cname" ]; then _pass; else _fail "manifest 'name' missing or not a string"; fi

set_test "[claude] manifest 'version', if present, is a string"
if jq -e 'has("version")|not' "$CLAUDE_MANIFEST" >/dev/null 2>&1 \
   || jq -e '(.version|type)=="string"' "$CLAUDE_MANIFEST" >/dev/null 2>&1; then _pass; else
  _fail "manifest 'version' present but not a string"; fi

assert_pointers_resolve "claude" "$CLAUDE_MANIFEST" "$CLAUDE_ROOT"

# Skills
set_test "[claude] skills/ directory exists in the payload"
if [ -d "$CLAUDE_ROOT/skills" ]; then _pass; else _fail "missing $CLAUDE_ROOT/skills"; fi
claude_skills=()
for f in "$CLAUDE_ROOT"/skills/*/SKILL.md; do [ -f "$f" ] && claude_skills+=("$f"); done
set_test "[claude] at least one skills/*/SKILL.md is present"
if [ "${#claude_skills[@]}" -gt 0 ]; then _pass; else
  _fail "no SKILL.md under $CLAUDE_ROOT/skills/*/ — refusing to pass vacuously"; test_summary; exit $?; fi
for f in "${claude_skills[@]}"; do
  assert_md_frontmatter "claude-skill" "$(basename "$(dirname "$f")")" "$f"
done

# Agents
set_test "[claude] agents/ directory exists in the payload"
if [ -d "$CLAUDE_ROOT/agents" ]; then _pass; else _fail "missing $CLAUDE_ROOT/agents"; fi
claude_agents=()
for f in "$CLAUDE_ROOT"/agents/*.md; do [ -f "$f" ] && claude_agents+=("$f"); done
set_test "[claude] at least one agents/*.md is present"
if [ "${#claude_agents[@]}" -gt 0 ]; then _pass; else
  _fail "no agents/*.md under $CLAUDE_ROOT/agents — refusing to pass vacuously"; test_summary; exit $?; fi
for f in "${claude_agents[@]}"; do
  ag="$(basename "$f" .md)"
  assert_md_frontmatter "claude-agent" "$ag" "$f"
  assert_no_forbidden_agent_fields "claude-agent" "$ag" "$f"
done

# Hooks
assert_hooks_json "claude" "$CLAUDE_ROOT/hooks/hooks.json"

# ===========================================================================
# Codex payload — developers.openai.com/codex/plugins/build
# ===========================================================================
section "Codex payload conformance (dist/codex/speckit-pro)"

set_test "[codex] built payload root exists ($CODEX_ROOT)"
if [ -d "$CODEX_ROOT" ]; then _pass; else
  _fail "Codex payload missing — run scripts/build-plugin-payloads.sh"; test_summary; exit $?; fi

CODEX_MANIFEST="$CODEX_ROOT/.codex-plugin/plugin.json"
set_test "[codex] manifest exists at .codex-plugin/plugin.json"
if [ -f "$CODEX_MANIFEST" ]; then _pass; else _fail "missing $CODEX_MANIFEST"; fi

set_test "[codex] manifest is valid JSON"
if jq -e . "$CODEX_MANIFEST" >/dev/null 2>&1; then _pass; else _fail "invalid JSON: $CODEX_MANIFEST"; fi

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

assert_pointers_resolve "codex" "$CODEX_MANIFEST" "$CODEX_ROOT"

# Skills
set_test "[codex] skills/ directory exists at the plugin root"
if [ -d "$CODEX_ROOT/skills" ]; then _pass; else _fail "missing $CODEX_ROOT/skills"; fi
codex_skills=()
for f in "$CODEX_ROOT"/skills/*/SKILL.md; do [ -f "$f" ] && codex_skills+=("$f"); done
set_test "[codex] at least one skills/*/SKILL.md is present"
if [ "${#codex_skills[@]}" -gt 0 ]; then _pass; else
  _fail "no SKILL.md under $CODEX_ROOT/skills/*/ — refusing to pass vacuously"; test_summary; exit $?; fi
for f in "${codex_skills[@]}"; do
  assert_md_frontmatter "codex-skill" "$(basename "$(dirname "$f")")" "$f"
done

# Agents (codex-agents/*.toml) — verified post-path-rewrite.
set_test "[codex] codex-agents/ directory exists at the plugin root"
if [ -d "$CODEX_ROOT/codex-agents" ]; then _pass; else _fail "missing $CODEX_ROOT/codex-agents"; fi
codex_agents=()
for f in "$CODEX_ROOT"/codex-agents/*.toml; do [ -f "$f" ] && codex_agents+=("$f"); done
set_test "[codex] at least one codex-agents/*.toml is present"
if [ "${#codex_agents[@]}" -gt 0 ]; then _pass; else
  _fail "no codex-agents/*.toml under $CODEX_ROOT/codex-agents — refusing to pass vacuously"; test_summary; exit $?; fi
for f in "${codex_agents[@]}"; do assert_toml_agent "codex-agent" "$f"; done

# Hooks
assert_hooks_json "codex" "$CODEX_ROOT/codex-hooks.json"

test_summary
