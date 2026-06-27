#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGIN_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"
SOURCE_DIR="$PLUGIN_ROOT/codex-agents"
DEST_DIR="${CODEX_AGENTS_DEST:-$HOME/.codex/agents}"
TARGET_MODEL="${SPECKIT_CODEX_MODEL:-gpt-5.5}"

# Codex 0.125.x quirk: `codex plugin marketplace upgrade` refreshes the
# marketplace tmp root but does NOT re-sync the active install at
# ~/.codex/plugins/<name>/. As of v1.10.x we work around this by syncing
# the active install from the marketplace tmp root before copying agents
# to the runtime registry. This makes the install skill the single
# canonical "make my Codex match the latest published plugin" command.
#
# Disable with SPECKIT_SKIP_PLUGIN_SYNC=1 if you need the prior behavior
# (e.g., when developing the plugin against a local checkout you don't
# want overwritten).
MARKETPLACE_TMP_ROOT="${SPECKIT_MARKETPLACE_TMP_ROOT:-}"
SKIP_PLUGIN_SYNC="${SPECKIT_SKIP_PLUGIN_SYNC:-0}"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --model)
      if [ "$#" -lt 2 ]; then
        printf 'ERROR: --model requires a value\n' >&2
        exit 2
      fi
      TARGET_MODEL="$2"
      shift 2
      ;;
    --model=*)
      TARGET_MODEL="${1#--model=}"
      shift
      ;;
    -*)
      printf 'ERROR: unknown option: %s\n' "$1" >&2
      exit 2
      ;;
    *)
      DEST_DIR="$1"
      shift
      ;;
  esac
done

case "$TARGET_MODEL" in
  gpt-5.5|gpt-5.4) ;;
  *)
    printf 'ERROR: unsupported SpecKit Codex model: %s\n' "$TARGET_MODEL" >&2
    printf 'Supported values: gpt-5.5, gpt-5.4\n' >&2
    exit 2
    ;;
esac

if [ -z "$MARKETPLACE_TMP_ROOT" ]; then
  for candidate in \
    "$HOME/.codex/.tmp/marketplaces/racecraft-plugins-public/dist/codex/speckit-pro" \
    "$HOME/.codex/.tmp/marketplaces/racecraft-plugins-public/speckit-pro"; do
    if [ -f "$candidate/.codex-plugin/plugin.json" ]; then
      MARKETPLACE_TMP_ROOT="$candidate"
      break
    fi
  done
fi

# Sync active install from marketplace tmp root if it carries a newer
# version. Runs BEFORE the agent template copy so the cp loop sees the
# refreshed templates. Skipped when SPECKIT_SKIP_PLUGIN_SYNC=1 or the
# tmp root is absent (plugin installed via a non-marketplace path).
PLUGIN_SYNCED=0
if [ "$SKIP_PLUGIN_SYNC" != "1" ] \
   && [ -d "$MARKETPLACE_TMP_ROOT" ] \
   && [ "$MARKETPLACE_TMP_ROOT" != "$PLUGIN_ROOT" ] \
   && command -v jq >/dev/null 2>&1; then
  TMP_VERSION=$(jq -r '.version // empty' "$MARKETPLACE_TMP_ROOT/.codex-plugin/plugin.json" 2>/dev/null || true)
  ACTIVE_VERSION=$(jq -r '.version // empty' "$PLUGIN_ROOT/.codex-plugin/plugin.json" 2>/dev/null || true)
  # Only sync when the marketplace carries a STRICTLY NEWER version (per
  # `sort -V`, which handles semver-style 1.10.2 > 1.9.10 correctly). A
  # naive `!=` check would let an older marketplace ref clobber a newer
  # active install — never what the user wants.
  if [ -n "$TMP_VERSION" ] && [ -n "$ACTIVE_VERSION" ] && [ "$TMP_VERSION" != "$ACTIVE_VERSION" ]; then
    NEWER=$(printf '%s\n%s\n' "$TMP_VERSION" "$ACTIVE_VERSION" | sort -V | tail -n1)
    if [ "$NEWER" = "$TMP_VERSION" ]; then
      printf 'Plugin install is stale (active=%s, marketplace=%s). Syncing...\n' \
        "$ACTIVE_VERSION" "$TMP_VERSION"
      if command -v rsync >/dev/null 2>&1; then
        # --delete: the active install must MIRROR the marketplace
        # snapshot. Without it, files removed upstream (e.g., a renamed
        # skill directory) linger in the active install and Codex loads
        # both the old and new skill ids on restart, producing
        # duplicate-skill collisions. The active plugin install is
        # plugin-owned territory; user files do not belong here. Use the
        # SPECKIT_SKIP_PLUGIN_SYNC=1 escape hatch for plugin-developer
        # workflows against a local checkout.
        rsync -a --delete "$MARKETPLACE_TMP_ROOT/" "$PLUGIN_ROOT/"
      else
        # cp -R cannot delete orphan files, so wipe the active install
        # first and then copy. Removing $PLUGIN_ROOT here is safe even
        # though this script lives inside it: bash already has the
        # script open, so the kernel keeps the inode alive until the
        # script exits even after the directory entry is unlinked.
        rm -rf "$PLUGIN_ROOT"
        mkdir -p "$PLUGIN_ROOT"
        cp -R "$MARKETPLACE_TMP_ROOT/." "$PLUGIN_ROOT/"
      fi
      PLUGIN_SYNCED=1
      printf 'Synced active plugin install to %s.\n' "$TMP_VERSION"
    fi
  fi
fi

if [ ! -d "$SOURCE_DIR" ]; then
  printf 'ERROR: source directory not found: %s\n' "$SOURCE_DIR" >&2
  exit 1
fi

EXPECTED_AGENTS=()
while IFS= read -r agent; do
  EXPECTED_AGENTS+=("$agent")
done < <(
  find "$SOURCE_DIR" -maxdepth 1 -type f -name '*.toml' -print \
    | sed 's#^.*/##' \
    | sort
)

if [ "${#EXPECTED_AGENTS[@]}" -eq 0 ]; then
  printf 'ERROR: no bundled agent templates found in %s\n' "$SOURCE_DIR" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"

for agent in "${EXPECTED_AGENTS[@]}"; do
  cp -f "$SOURCE_DIR/$agent" "$DEST_DIR/$agent"
done

if [ "$TARGET_MODEL" != "gpt-5.5" ]; then
  for agent in "${EXPECTED_AGENTS[@]}"; do
    if grep -Eq '^model = "gpt-5\.5"$' "$DEST_DIR/$agent"; then
      perl -0pi -e 's/^model = "gpt-5\.5"$/model = "'"$TARGET_MODEL"'"/m' "$DEST_DIR/$agent"
    fi
  done
fi

printf 'Installed %d SpecKit Pro Codex subagents.\n' "${#EXPECTED_AGENTS[@]}"
printf 'Source: %s\n' "$SOURCE_DIR"
printf 'Destination: %s\n' "$DEST_DIR"
printf 'Executor/consensus model: %s\n' "$TARGET_MODEL"
printf 'Files:\n'
for agent in "${EXPECTED_AGENTS[@]}"; do
  printf '  - %s\n' "$agent"
done
printf 'Model policy: %s for every executor and consensus agent (phase-executor included); Spark helper optional on gpt-5.3-codex-spark.\n' "$TARGET_MODEL"
if [ "$TARGET_MODEL" = "gpt-5.4" ]; then
  printf 'Fallback mode: installed templates were rewritten for GPT-5.4 compatibility.\n'
fi
if [ "$PLUGIN_SYNCED" = "1" ]; then
  printf 'Active plugin install was refreshed from the marketplace tmp root.\n'
fi
printf 'Restart Codex now so the custom subagents reload.\n'
