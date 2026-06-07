#!/usr/bin/env bash
# test-moc-lint-exit-codes.sh — Layer-4 subprocess driver for the 3-way exit-code
# contract of the two version-gated MOC lints (validate-moc-orphan.sh and
# validate-moc-stale-index.sh). Mirrors test-validate-gate.sh's house pattern:
# invoke each lint as a SUBPROCESS with a scan-root arg and assert exit codes +
# stdout/stderr routing across the process boundary (a script cannot assert its
# own trap-driven exit from inside itself, FR-020/FR-022/FR-023/FR-024).
#
# Cases:
#   (a) FR-020      trap -> 2: a PATH-stubbed scan-path command (awk/grep/sed/
#                   basename/dirname) that exits nonzero forces an internal
#                   error; the ERR trap maps it to exit 2 (AND 2 != 1).
#   (b) FR-021      unreadable marker: a chmod-000 SPEC-MOC.md is SKIPPED (no
#                   content violation) with a stderr WARNING. Skipped when run
#                   as root (000 read-bits are bypassed).
#   (c) FR-022      a nonexistent scan root AND an empty/markerless tree -> 0.
#   (d) FR-023      a marker-less tree with deliberately broken body content ->
#                   0 (skipped before any body read).
#   (e) FR-024      a content violation routes path+rule to STDOUT with exit 1,
#                   while an internal error routes to STDERR with exit 2 — the
#                   two classes are never conflated.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"
ORPHAN="$PLUGIN_ROOT/../tests/speckit-pro/layer1-structural/validate-moc-orphan.sh"
STALE="$PLUGIN_ROOT/../tests/speckit-pro/layer1-structural/validate-moc-stale-index.sh"

# Temp workspace with cleanup (restore any chmod-000 before rm so cleanup works).
WORK="$(mktemp -d)"
# The Mode-B internal-error case (section (f)) drives the stale lint with NO arg,
# which creates a runtime broken-symlink fixture in the REAL working tree (outside
# $WORK). Belt-and-suspenders: ensure that symlink never survives this driver even
# if a case fails mid-run, so the orchestrator's final suite pass starts clean.
STALE_RUNTIME_SYMLINK="$PLUGIN_ROOT/../tests/speckit-pro/layer1-structural/fixtures/moc/stale/stale-broken-symlink/broken-link.md"
cleanup() {
  # Restore permissions on anything we chmod-000'd so rm -rf can remove it.
  find "$WORK" -type f -exec chmod u+rwx {} + 2>/dev/null || true
  rm -rf "$WORK"
  rm -f "$STALE_RUNTIME_SYMLINK"
}
trap cleanup EXIT

# ─────────────────────────────────────────
# Fixture builders
# ─────────────────────────────────────────

# make_gated_spec <root> <dirname> — a gated marker whose links all resolve
# (so the scan reaches the dirname/basename calls in the scan loop). Returns 0.
make_gated_spec() {
  local root="$1" name="$2" dir
  dir="$root/$name"
  mkdir -p "$dir"
  cat > "$dir/SPEC-MOC.md" <<EOF
---
up: "[parent](roadmap.md)"
related: []
status: ""
rank:
spec_id: "$name"
structureVersion: 1
---
# $name
EOF
  printf '# roadmap\n' > "$dir/roadmap.md"
}

# make_violation_spec <root> <dirname> — a gated marker with a DANGLING up:
# link (orphan: ill-formed? no, well-formed but unresolved -> stale violation;
# for orphan we also break spec_id so it violates). Used for the stdout/exit-1
# class. Returns 0.
make_dangling_spec() {
  local root="$1" name="$2" dir
  dir="$root/$name"
  mkdir -p "$dir"
  cat > "$dir/SPEC-MOC.md" <<EOF
---
up: "[parent](no-such-roadmap.md)"
related: []
status: ""
rank:
spec_id: "$name"
structureVersion: 1
---
# $name — dangling up: link
EOF
}

# make_orphan_violation_spec <root> <dirname> — a gated marker with NO up:
# (orphan violation -> stdout + exit 1).
make_orphan_violation_spec() {
  local root="$1" name="$2" dir
  dir="$root/$name"
  mkdir -p "$dir"
  cat > "$dir/SPEC-MOC.md" <<EOF
---
related: []
status: ""
rank:
spec_id: "$name"
structureVersion: 1
---
# $name — missing up:
EOF
}

# make_legacy_spec <root> <dirname> — a NON-gated marker (no structureVersion)
# with deliberately broken body content + a dangling link. Must be skipped
# BEFORE any body read (FR-023) -> exit 0.
make_legacy_spec() {
  local root="$1" name="$2" dir
  dir="$root/$name"
  mkdir -p "$dir"
  cat > "$dir/SPEC-MOC.md" <<EOF
---
up: "[parent](does-not-exist.md)"
spec_id: "$name"
---
# $name — legacy, no version gate

A dangling [body link](also-missing.md) and a [[wikilink]] — both ignored
because this spec is not version-gated (exempt-before-content).
EOF
}

# write_failing_stub <stubdir> <cmd> [match-glob]
# Write an executable <cmd> into <stubdir> that exits 3 (forcing an internal
# error). If <match-glob> is given, the stub fails ONLY when "$*" matches it and
# otherwise execs the real command (so bootstrap calls survive). Returns 0.
write_failing_stub() {
  local stubdir="$1" cmd="$2" match="${3:-}"
  mkdir -p "$stubdir"
  if [ -n "$match" ]; then
    cat > "$stubdir/$cmd" <<EOF
#!/usr/bin/env bash
case "\$*" in
  $match) echo "stub $cmd failure (scan path)" >&2; exit 3 ;;
esac
exec /usr/bin/$cmd "\$@"
EOF
  else
    cat > "$stubdir/$cmd" <<EOF
#!/usr/bin/env bash
echo "stub $cmd failure (scan path)" >&2
exit 3
EOF
  fi
  chmod +x "$stubdir/$cmd"
}

# ─────────────────────────────────────────
section "(a) FR-020: internal error -> exit 2 (trapped), and 2 != 1"
# ─────────────────────────────────────────
# Orphan uses basename ONLY in its scan loop (never at bootstrap) — break it
# globally. Stale uses dirname at bootstrap AND scan; break it ONLY for the
# scan-loop call `dirname <...>/SPEC-MOC.md` so bootstrap survives.

ROOT_A="$WORK/a"
make_gated_spec "$ROOT_A" "gated-spec"

STUB_ORPHAN="$WORK/stub-orphan"
write_failing_stub "$STUB_ORPHAN" "basename"

set_test "orphan: broken scan-path basename -> exit 2"
rc=0
out=$(PATH="$STUB_ORPHAN:$PATH" "$ORPHAN" "$ROOT_A" 2>/dev/null) || rc=$?
assert_eq "2" "$rc" "orphan internal-error exit code"

set_test "orphan: internal-error exit (2) is distinct from content-violation exit (1)"
[ "$rc" -ne 1 ] && _pass || _fail "internal-error exit must not equal 1 (got $rc)"

STUB_STALE="$WORK/stub-stale"
write_failing_stub "$STUB_STALE" "dirname" '*SPEC-MOC.md'

set_test "stale-index: broken scan-path dirname -> exit 2"
rc=0
out=$(PATH="$STUB_STALE:$PATH" "$STALE" "$ROOT_A" 2>/dev/null) || rc=$?
assert_eq "2" "$rc" "stale-index internal-error exit code"

set_test "stale-index: internal-error exit (2) is distinct from content-violation exit (1)"
[ "$rc" -ne 1 ] && _pass || _fail "internal-error exit must not equal 1 (got $rc)"

# ─────────────────────────────────────────
section "(b) FR-021: unreadable marker -> SKIP with stderr warning, no violation"
# ─────────────────────────────────────────

if [ "$(id -u)" -eq 0 ]; then
  set_test "unreadable-marker sub-case SKIPPED (running as root bypasses 000)"
  _pass
else
  ROOT_B="$WORK/b"
  make_gated_spec "$ROOT_B" "unreadable-spec"
  chmod 000 "$ROOT_B/unreadable-spec/SPEC-MOC.md"

  set_test "orphan: unreadable marker -> exit 0 (no content violation)"
  rc=0
  out=$("$ORPHAN" "$ROOT_B" 2>"$WORK/b-orphan.err") || rc=$?
  assert_eq "0" "$rc" "unreadable marker must not be a content violation"

  set_test "orphan: unreadable marker -> stderr carries a warning"
  err=$(cat "$WORK/b-orphan.err")
  assert_contains "$err" "unreadable marker"

  set_test "orphan: unreadable marker -> no VIOLATION on stdout"
  assert_not_contains "$out" "VIOLATION"

  set_test "stale-index: unreadable marker -> exit 0 (no content violation)"
  rc=0
  out=$("$STALE" "$ROOT_B" 2>"$WORK/b-stale.err") || rc=$?
  assert_eq "0" "$rc" "unreadable marker must not be a content violation"

  set_test "stale-index: unreadable marker -> stderr carries a warning"
  err=$(cat "$WORK/b-stale.err")
  assert_contains "$err" "unreadable marker"

  set_test "stale-index: unreadable marker -> no VIOLATION on stdout"
  assert_not_contains "$out" "VIOLATION"

  chmod u+rwx "$ROOT_B/unreadable-spec/SPEC-MOC.md"
fi

# ─────────────────────────────────────────
section "(c) FR-022: nonexistent root and empty/markerless tree -> exit 0"
# ─────────────────────────────────────────

NONEXISTENT="$WORK/does-not-exist-root"

set_test "orphan: nonexistent scan root -> exit 0"
rc=0; "$ORPHAN" "$NONEXISTENT" >/dev/null 2>&1 || rc=$?
assert_eq "0" "$rc" "missing root is skipped, not an error"

set_test "stale-index: nonexistent scan root -> exit 0"
rc=0; "$STALE" "$NONEXISTENT" >/dev/null 2>&1 || rc=$?
assert_eq "0" "$rc" "missing root is skipped, not an error"

EMPTY_ROOT="$WORK/empty"
mkdir -p "$EMPTY_ROOT"

set_test "orphan: empty scan root -> exit 0"
rc=0; "$ORPHAN" "$EMPTY_ROOT" >/dev/null 2>&1 || rc=$?
assert_eq "0" "$rc" "empty root: glob stays literal, nothing checked"

set_test "stale-index: empty scan root -> exit 0"
rc=0; "$STALE" "$EMPTY_ROOT" >/dev/null 2>&1 || rc=$?
assert_eq "0" "$rc" "empty root: glob stays literal, nothing checked"

MARKERLESS_ROOT="$WORK/markerless"
mkdir -p "$MARKERLESS_ROOT/spec-without-marker"
printf '# just a readme\n' > "$MARKERLESS_ROOT/spec-without-marker/README.md"

set_test "orphan: markerless tree (no SPEC-MOC.md) -> exit 0"
rc=0; "$ORPHAN" "$MARKERLESS_ROOT" >/dev/null 2>&1 || rc=$?
assert_eq "0" "$rc" "no marker globbed -> nothing checked"

set_test "stale-index: markerless tree (no SPEC-MOC.md) -> exit 0"
rc=0; "$STALE" "$MARKERLESS_ROOT" >/dev/null 2>&1 || rc=$?
assert_eq "0" "$rc" "no marker globbed -> nothing checked"

# ─────────────────────────────────────────
section "(d) FR-023: non-gated marker with broken body content -> exit 0 (exempt-before-content)"
# ─────────────────────────────────────────

ROOT_D="$WORK/d"
make_legacy_spec "$ROOT_D" "legacy-spec"

set_test "orphan: non-gated marker with broken body -> exit 0 (skipped before read)"
rc=0; out=$("$ORPHAN" "$ROOT_D" 2>/dev/null) || rc=$?
assert_eq "0" "$rc" "legacy spec is exempt regardless of body content"
set_test "orphan: non-gated marker -> no VIOLATION emitted"
assert_not_contains "$out" "VIOLATION"

set_test "stale-index: non-gated marker with broken body -> exit 0 (skipped before read)"
rc=0; out=$("$STALE" "$ROOT_D" 2>/dev/null) || rc=$?
assert_eq "0" "$rc" "legacy spec is exempt regardless of body content"
set_test "stale-index: non-gated marker -> no VIOLATION emitted"
assert_not_contains "$out" "VIOLATION"

# ─────────────────────────────────────────
section "(e) FR-024: content violation -> stdout + exit 1; internal error -> stderr + exit 2 (never conflated)"
# ─────────────────────────────────────────

# Orphan content violation: a gated marker with NO up: (orphan rule).
ROOT_E_ORPHAN="$WORK/e-orphan"
make_orphan_violation_spec "$ROOT_E_ORPHAN" "orphan-missing-up"

set_test "orphan: content violation -> exit 1"
rc=0; out=$("$ORPHAN" "$ROOT_E_ORPHAN" 2>"$WORK/e-orphan.err") || rc=$?
assert_eq "1" "$rc" "content violation is a hard fail (exit 1)"
set_test "orphan: content violation -> path + rule on STDOUT"
assert_contains "$out" "VIOLATION"
set_test "orphan: content violation -> offending path named on STDOUT"
assert_contains "$out" "orphan-missing-up/SPEC-MOC.md"
set_test "orphan: content violation -> nothing on STDERR (no internal-error line)"
err=$(cat "$WORK/e-orphan.err")
assert_not_contains "$err" "internal failure"

# Stale-index content violation: a gated marker with a dangling up: link.
ROOT_E_STALE="$WORK/e-stale"
make_dangling_spec "$ROOT_E_STALE" "stale-dangling"

set_test "stale-index: content violation -> exit 1"
rc=0; out=$("$STALE" "$ROOT_E_STALE" 2>"$WORK/e-stale.err") || rc=$?
assert_eq "1" "$rc" "content violation is a hard fail (exit 1)"
set_test "stale-index: content violation -> path + rule on STDOUT"
assert_contains "$out" "VIOLATION"
set_test "stale-index: content violation -> the unresolved link named on STDOUT"
assert_contains "$out" "no-such-roadmap.md"
set_test "stale-index: content violation -> nothing on STDERR (no internal-error line)"
err=$(cat "$WORK/e-stale.err")
assert_not_contains "$err" "internal failure"

# Internal error: routes to STDERR with exit 2, NOT stdout, NOT exit 1.
ROOT_E_INTERR="$WORK/e-interr"
make_gated_spec "$ROOT_E_INTERR" "gated-spec"

set_test "orphan: internal error -> exit 2 (not 1)"
rc=0; out=$(PATH="$STUB_ORPHAN:$PATH" "$ORPHAN" "$ROOT_E_INTERR" 2>"$WORK/e-interr-orphan.err") || rc=$?
assert_eq "2" "$rc" "internal error is exit 2"
set_test "orphan: internal error -> message on STDERR"
err=$(cat "$WORK/e-interr-orphan.err")
assert_contains "$err" "internal failure"
set_test "orphan: internal error -> NO VIOLATION on STDOUT (classes not conflated)"
assert_not_contains "$out" "VIOLATION"

set_test "stale-index: internal error -> exit 2 (not 1)"
rc=0; out=$(PATH="$STUB_STALE:$PATH" "$STALE" "$ROOT_E_INTERR" 2>"$WORK/e-interr-stale.err") || rc=$?
assert_eq "2" "$rc" "internal error is exit 2"
set_test "stale-index: internal error -> message on STDERR"
err=$(cat "$WORK/e-interr-stale.err")
assert_contains "$err" "internal failure"
set_test "stale-index: internal error -> NO VIOLATION on STDOUT (classes not conflated)"
assert_not_contains "$out" "VIOLATION"

# ─────────────────────────────────────────
section "(f) FR-020: Mode-B internal error AFTER symlink fixture -> exit 2 AND working tree left clean"
# ─────────────────────────────────────────
# Stale's no-arg self-test (Mode B) creates a runtime broken-symlink fixture in
# the real tree and installs an EXIT trap to remove it. Force an internal error
# AFTER that point (the bare scan_root over the committed stale fixtures calls
# `dirname <...>/SPEC-MOC.md`, which the dirname stub fails) so the ERR trap maps
# it to exit 2. The fix must still let the symlink cleanup run on that path; if
# the ERR handler clears the EXIT trap, the broken-link.md symlink is orphaned in
# the working tree. Use `-L` (not `-e`/`-f`): the fixture is a BROKEN symlink, so
# -e/-f dereference and report absent whether or not the entry exists.

rm -f "$STALE_RUNTIME_SYMLINK"   # ensure a clean precondition

set_test "stale-index: Mode-B internal error (no arg) -> exit 2"
rc=0
PATH="$STUB_STALE:$PATH" "$STALE" >/dev/null 2>&1 || rc=$?
assert_eq "2" "$rc" "Mode-B internal error must still exit 2 (3-way contract)"

set_test "stale-index: Mode-B internal error -> runtime broken symlink cleaned up (tree left clean)"
if [ ! -L "$STALE_RUNTIME_SYMLINK" ]; then
  _pass
else
  _fail "broken-link.md symlink leaked into the working tree after an internal error"
  rm -f "$STALE_RUNTIME_SYMLINK"
fi

test_summary
