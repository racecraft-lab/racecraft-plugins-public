#!/usr/bin/env bash
# extractors.sh — Layer 8 section/table extractors for parity comparison.
#
# Functions:
#   extract_section <file> <h2_header>
#     Emit the body of the markdown section whose H2 header matches
#     <h2_header> (without the leading "## "). Bounds: the line after the
#     H2 header through the line before the next H2 (or EOF). H3 and below
#     are part of the section body.
#
#   extract_table_row_count <file> <h2_header>
#     Emit the number of data rows in the first markdown table inside the
#     named section. Data rows are pipe-delimited lines that are NOT the
#     header row and NOT the |---|---| separator row.
#
#   extract_table_column <file> <h2_header> <column_name>
#     Emit one value per data row from the named column, newline-separated.
#     Column is matched by case-sensitive header text (trimmed). Values are
#     trimmed of surrounding whitespace.
#
# All functions write to stdout. Exit code 0 on success, 1 if the section
# or column cannot be located.

extract_section() {
  local file="$1" header="$2"
  awk -v hdr="## $header" '
    $0 == hdr        { inside = 1; next }
    inside && /^## / { inside = 0 }
    inside           { print }
  ' "$file"
}

# Helper: emit the lines of the first markdown table inside an extracted
# section body. A table is the contiguous block of pipe-prefixed lines
# starting at the first line that begins with "|".
_first_table() {
  awk '
    /^\|/ { in_t = 1; print; next }
    in_t  { exit }
  '
}

extract_table_row_count() {
  local file="$1" header="$2"
  local table
  table=$(extract_section "$file" "$header" | _first_table)
  if [ -z "$table" ]; then
    return 1
  fi
  # Total table lines minus 2 (header + separator).
  local total
  total=$(printf '%s\n' "$table" | grep -c '^|')
  if [ "$total" -lt 2 ]; then
    echo 0
    return 0
  fi
  echo $((total - 2))
}

extract_table_column() {
  local file="$1" header="$2" column="$3"
  local table
  table=$(extract_section "$file" "$header" | _first_table)
  if [ -z "$table" ]; then
    return 1
  fi
  printf '%s\n' "$table" | awk -F'|' -v col="$column" '
    function trim(s) { sub(/^[[:space:]]+/, "", s); sub(/[[:space:]]+$/, "", s); return s }
    NR == 1 {
      for (i = 2; i < NF; i++) {
        if (trim($i) == col) { idx = i; break }
      }
      if (!idx) { exit 1 }
      next
    }
    NR == 2 { next }   # separator |---|---|
    NF >= idx + 1 { print trim($idx) }
  '
}

# Allow this file to be sourced (functions only) or executed for one-off CLI use.
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  cmd="${1:-}"
  shift || true
  case "$cmd" in
    section)      extract_section "$@" ;;
    row-count)    extract_table_row_count "$@" ;;
    column)       extract_table_column "$@" ;;
    *)
      echo "Usage: $(basename "$0") {section|row-count|column} <file> <h2_header> [<column_name>]" >&2
      exit 2
      ;;
  esac
fi
