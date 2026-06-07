#!/usr/bin/env bash
# moc-frontmatter.sh — Shared, total/safe frontmatter reader + version gate.
#
# Sourced by the version-gated MOC lints (validate-moc-orphan.sh and, in the
# next group, validate-moc-stale-index.sh — 2 callers, justified). Implements
# the version-gate and frontmatter-field rules from
# specs/prsg-002-moc-templates/contracts/lint-behavior-contract.md and
# data-model.md. Covers FR-013, FR-021 (no-fence / unparseable / malformed),
# FR-023 (exempt-before-content invariant).
#
# This file defines functions only — sourcing it has no side effects.
#
# Safety (constitution II): all reads are TOTAL — a garbled / fenceless /
# unreadable marker never crashes a caller; it simply reports "not gated"
# (SKIP). The version-gate read MUST be evaluated by a caller BEFORE any read
# of a spec's body content (exempt-before-content invariant, FR-023).
#
# bash 3.2 compatible: no mapfile/readarray, no ${var,,}; quoted vars; grep/sed
# no-match guarded so set -euo pipefail in a caller never trips.

set -euo pipefail

# _moc_fm_block <file>
# Print the lines BETWEEN the first `---` fence (which MUST be the very first
# line) and the next `---` line. Prints nothing (and returns 0) when the file
# is unreadable, missing, or has no opening `---` on line 1. TOTAL — never errors.
_moc_fm_block() {
  local file="$1"
  [ -r "$file" ] || return 0
  # awk: only treat as frontmatter when line 1 is exactly `---`. Emit lines
  # until the closing `---`. If no opening fence on line 1, emit nothing.
  awk '
    NR == 1 { if ($0 == "---") { infm = 1; next } else { exit } }
    infm && $0 == "---" { exit }
    infm { print }
  ' "$file" 2>/dev/null || true
}

# moc_frontmatter_field <file> <field>
# Print the scalar value of <field> from the file's frontmatter block, with a
# matched pair of surrounding quotes stripped and a trailing inline ` #...`
# YAML comment stripped (whitespace-then-hash to end of line; a `#` with no
# preceding whitespace — e.g. an anchor like foo.md#x — is preserved).
# Exit 0 if the field line is present (value may be empty), 1 if absent.
# TOTAL/safe under set -e.
moc_frontmatter_field() {
  local file="$1" field="$2"
  local block line value
  block="$(_moc_fm_block "$file")"
  # First matching `^<field>:` line (leading spaces allowed). grep guarded.
  line="$(printf '%s\n' "$block" | grep -m1 -E "^[[:space:]]*${field}:" 2>/dev/null || true)"
  [ -n "$line" ] || return 1

  # Strip the `key:` prefix (up to and including the first colon).
  value="${line#*:}"
  # Trim leading whitespace.
  value="${value#"${value%%[![:space:]]*}"}"
  # Strip a trailing inline comment: a run of whitespace followed by '#' to EOL.
  # sed guarded with || true so a no-op match never trips set -e.
  value="$(printf '%s' "$value" | sed -E 's/[[:space:]]+#.*$//' 2>/dev/null || true)"
  # Trim trailing whitespace (left after comment strip or as-is).
  value="${value%"${value##*[![:space:]]}"}"
  # Strip a single matched pair of surrounding quotes (double or single).
  case "$value" in
    \"*\") value="${value#\"}"; value="${value%\"}" ;;
    \'*\') value="${value#\'}"; value="${value%\'}" ;;
  esac
  printf '%s' "$value"
}

# moc_is_gated <file>
# Return 0 (GATED) iff <file> is a readable marker whose frontmatter carries a
# `structureVersion` that is an UNAMBIGUOUS bare integer >= 1. Every other case
# — missing/unreadable file, no `---` fence, no structureVersion, < 1, or a
# non-bare-integer value (quoted "1", decimal 1.0, text) — returns 1 (SKIP).
# TOTAL: never crashes. The gate literal 1 is hardcoded here.
#
# Gate literal — KEEP IN SYNC with the scaffold template's stamped
# `structureVersion: 1` and each lint's hardcoded gate. No shared version file.
moc_is_gated() {
  local file="$1" version
  [ -r "$file" ] || return 1
  version="$(moc_frontmatter_field "$file" structureVersion)" || return 1
  # Bare integer only: digits, no quotes (already stripped), no decimal point,
  # no trailing text. A quoted "1" loses its quotes above but then equals 1 —
  # guard that by re-reading the RAW line to reject any quoting/decimal/text.
  case "$version" in
    ''|*[!0-9]*) return 1 ;;   # empty or any non-digit char -> not a bare int
  esac
  # Reject values whose RAW frontmatter form was quoted or decimal: re-extract
  # the raw line and require the post-`:`-trimmed token to be digits-only too.
  local raw_line raw_token
  raw_line="$(_moc_fm_block "$file" | grep -m1 -E '^[[:space:]]*structureVersion:' 2>/dev/null || true)"
  raw_token="${raw_line#*:}"
  raw_token="${raw_token#"${raw_token%%[![:space:]]*}"}"            # ltrim
  raw_token="$(printf '%s' "$raw_token" | sed -E 's/[[:space:]]+#.*$//' 2>/dev/null || true)"  # drop inline comment
  raw_token="${raw_token%"${raw_token##*[![:space:]]}"}"           # rtrim
  case "$raw_token" in
    ''|*[!0-9]*) return 1 ;;   # quoted "1", 1.0, or text -> reject
  esac
  # Numeric >= 1.
  [ "$version" -ge 1 ] 2>/dev/null || return 1
  return 0
}

# Guard: do nothing when sourced. No main/demo on direct execution.
# Use :- defaults so the guard is safe under set -u even when sourced in a
# context where BASH_SOURCE[0] is unset.
if [[ "${BASH_SOURCE[0]:-}" == "${0:-}" ]]; then
  :
fi
