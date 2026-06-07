#!/usr/bin/env bash
# test-generate-spec-index.sh — Layer 4 unit test for the spec-index generator.
#
# Sibling of test-moc-id-normalize.sh: source assertions.sh, resolve the
# generator path into GEN, drive it through assert_exit_code* / captured runs,
# end with test_summary. This test does NOT reproduce the lint's ERR-trap /
# exit-2 scaffolding — that 3-way-exit machinery is the GENERATOR's job (T008),
# exercised here as observable behavior, not re-implemented in the test.
#
# Covers the nine T006 assertion groups (a)-(i):
#   (a) 3-way exit enum: --check returns 0 current, 1 stale, 2 error; stale (1)
#       is structurally distinct from error (2)                         [FR-015]
#   (b) --check writes nothing on every path, including the error path  [FR-012]
#   (c) the ERR/EXIT trap is disarmed before the deliberate --check exit 1, so a
#       stale result is never remapped to error exit 2              [D5/FR-021]
#   (d) FR-009 missing marker pair -> that one zone skipped, other present zones
#       still rebuilt                                                   [FR-009]
#   (e) FR-022 unbalanced/duplicated/out-of-order pair -> fail-safe exit 2, no
#       partial write                                                   [FR-022]
#   (f) atomic whole-file write via mktemp+rename, per-target, so a failure on
#       one map cannot half-write another                   [D6/FR-016/FR-002]
#   (g) PRS empty/absent -> empty-but-valid link-free zone [FR-011] vs malformed
#       -> exit 2 [FR-016], never conflated
#   (h) a template-born three-zone block and an inject-if-missing block are
#       byte-identical                              [FR-008/FR-017, assemble_zone_block]
#   (i) canonical ordering: normalized-ID across specs, fixed artifact precedence
#       then path within a spec                                         [FR-005]
#
# TDD RED: the generator does not exist yet. The FIRST assertion is a clean guard
# (generator present + executable); every group below pairs its real-behavior
# gate with an exit-code/content assertion so NO group is vacuously green while
# the generator is absent. The test reports tidy assertion failures via
# assertions.sh and a non-zero exit — never a raw bash "command not found" crash.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../lib/assertions.sh
source "$HERE/../lib/assertions.sh"
# The canonical normalizer ships inside the plugin (FR-004); the test tree does not
# ship, so source it from its shipped home, not from this test tree's lib/.
# shellcheck source=../../../speckit-pro/skills/speckit-autopilot/scripts/lib/moc-id-normalize.sh
source "$HERE/../../../speckit-pro/skills/speckit-autopilot/scripts/lib/moc-id-normalize.sh"

# The single shared generator under test (sibling of reviewability-gate.sh). It
# lives in the shipped plugin tree; this test tree is a repo-root sibling of the
# plugin, so reach up to the repo root (../../../) and back into speckit-pro/.
GEN="$HERE/../../../speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh"

# Committed fixture spec trees (inputs only). The generator discovers spec dirs
# under `<REPO_ROOT>/specs/*/` (T009, data-model Discovery), so each fixture CASE
# is its own mini REPO_ROOT carrying a `specs/<branch>/` layer. We hand the case
# dir to the generator as REPO_ROOT and read its single map at the nested path.
# Write-mode cases run on a disposable copy so a GREEN run never dirties the
# committed fixtures.
FIX="$HERE/../layer1-structural/fixtures/spec-index"

# Per-case REPO_ROOTs (the dir handed to the generator) and the nested map path
# under specs/<branch>/SPEC-MOC.md the assertions read after a run.
CUR_ROOT="$FIX/current-empty";       CUR_MOC="specs/prsg-900-current/SPEC-MOC.md"
STALE_ROOT="$FIX/stale-fill";        STALE_MOC="specs/prsg-901-stale/SPEC-MOC.md"
INJECT_ROOT="$FIX/inject-missing-all"; INJECT_MOC="specs/prsg-902-inject/SPEC-MOC.md"
TPL_ROOT="$FIX/template-born";       TPL_MOC="specs/prsg-902-template/SPEC-MOC.md"
SKIP1_ROOT="$FIX/skip-one-missing";  SKIP1_MOC="specs/prsg-903-skipone/SPEC-MOC.md"
UNBAL_ROOT="$FIX/unbalanced-marker"; UNBAL_MOC="specs/prsg-904-unbalanced/SPEC-MOC.md"
PRSPOP_ROOT="$FIX/prs-populated";    PRSPOP_MOC="specs/prsg-905-prs-populated/SPEC-MOC.md"
PRSEMP_ROOT="$FIX/prs-empty";        PRSEMP_MOC="specs/prsg-906-prs-empty/SPEC-MOC.md"
PRSABS_ROOT="$FIX/prs-absent";       PRSABS_MOC="specs/prsg-907-prs-absent/SPEC-MOC.md"
PRSMAL_ROOT="$FIX/prs-malformed";    PRSMAL_MOC="specs/prsg-908-prs-malformed/SPEC-MOC.md"
# Type-violation manifests: a `pr` that is a string ("abc") or a non-integer number
# (117.5). Both pass a presence-only guard but violate the schema (pr: integer), so
# the renderer must fail safe (exit 2), distinct from absent/empty (FR-016, D3).
PRSBADSTR_ROOT="$FIX/prs-bad-pr-string";  PRSBADSTR_MOC="specs/prsg-916-prs-bad-string/SPEC-MOC.md"
PRSBADFLT_ROOT="$FIX/prs-bad-pr-float";   PRSBADFLT_MOC="specs/prsg-917-prs-bad-float/SPEC-MOC.md"
# Symlinked-MOC fixture: a version-marked spec dir whose SPEC-MOC.md is built as a
# symlink (to moc-target.md) at runtime. The generator must reject the non-regular
# target (exit 2) and NOT replace the symlink (FR-016).
SYMLINK_ROOT="$FIX/symlinked-moc"
SYMLINK_MOC="specs/prsg-918-symlink/SPEC-MOC.md"
SYMLINK_TARGET="specs/prsg-918-symlink/moc-target.md"
# A dedicated multi-spec root for (f) atomicity: a good map + an out-of-scope
# legacy map + a poison (unbalanced) map share one REPO_ROOT.
ATOM_ROOT="$FIX/atomicity"
ATOM_LEGACY_MOC="specs/b-prsg-914-legacy/SPEC-MOC.md"

# The middle dot in a PRS row is U+00B7 (· — two bytes 0xC2 0xB7), NOT an ASCII
# dot. Pin the exact bytes the renderer must emit (D3 worked example).
PRS_SEP=$'\xc2\xb7'

# run_gen <var> <expected_exit> [args...]
# Run the generator, capture combined stdout+stderr into <var>, and assert the
# exit code. NEVER invokes GEN bare under set -e — an absent file would abort the
# script (the raw crash the contract forbids). In RED the generator is absent so
# the captured exec error yields 127 -> a clean assert_exit_code FAIL, not a crash.
run_gen() {
  local __var="$1" __want="$2"; shift 2
  local __out __rc=0
  __out="$("$GEN" "$@" 2>&1)" || __rc=$?
  eval "$__var=\$__out"
  assert_eq "$__want" "$__rc" "exit code for: generate-spec-index.sh $*"
}

# fresh_copy <src-root> — copy ONE fixture REPO_ROOT into a disposable, UNIQUE
# directory and echo the copy's REPO_ROOT path (the dir that contains `specs/`).
# Write-mode mutates SPEC-MOC.md files, so each write case operates on its own copy
# of just that case's root (never the whole fixture tree — distinct cases must not
# share a run). All copies live under TMP_ROOT, trap-cleaned at EOF.
#
# fresh_copy is invoked via `copy="$(fresh_copy …)"`, i.e. inside a command
# substitution subshell, so a parent-scope counter would never increment (every
# call would collide on the same name and `cp -R` would nest the second copy inside
# the first). `mktemp -d` per call gives a guaranteed-unique parent regardless of
# subshell scoping; the fixture is copied into `<unique>/root` so the returned path
# keeps the `<repo-root>/specs/<branch>/…` layout the assertions read.
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/spec-index-l4.XXXXXX")"
trap 'rm -rf "$TMP_ROOT"' EXIT
fresh_copy() {
  # No-arg calls (groups h/i) copy the WHOLE fixture tree ($FIX) and index into a
  # case subdir; single-arg calls copy just one case REPO_ROOT. Default under set -u.
  local src="${1:-$FIX}"
  local parent dest
  parent="$(mktemp -d "$TMP_ROOT/copy.XXXXXX")"
  dest="$parent/root"
  cp -R "$src" "$dest"
  printf '%s' "$dest"
}

# ───────────────────────────────────────────────────────────────────────────
section "RED guard — the generator must exist and be executable"
# ───────────────────────────────────────────────────────────────────────────
# First assertion fails cleanly with an interpretable message when the generator
# is absent (the TDD RED state), instead of letting later asserts crash.
set_test "generator script exists at the contracted path"
assert_file_exists "$GEN" "FAIL: generator not found at $GEN"

set_test "generator script is executable"
assert_file_executable "$GEN" "FAIL: generator not executable at $GEN"

# ───────────────────────────────────────────────────────────────────────────
section "(a) 3-way exit enum — current(0) / stale(1) / error(2), stale != error"
# ───────────────────────────────────────────────────────────────────────────
# current: an in-scope MOC with present-but-empty zones and NO sibling artifacts
# regenerates to all-empty -> zero diff -> --check exit 0.
set_test "--check on a current map -> exit 0"
run_gen out_cur 0 --check "$CUR_ROOT"

# stale: an in-scope MOC with empty zones but stub artifacts + populated prs.json
# regenerates to NON-empty BACKLINKS/PRS -> --check exit 1.
set_test "--check on a stale map -> exit 1 (content drift)"
run_gen out_stale 1 --check "$STALE_ROOT"

# error: a malformed PRS manifest -> --check exit 2.
set_test "--check on a malformed-PRS map -> exit 2 (error)"
run_gen out_err 2 --check "$PRSMAL_ROOT"

# The stale(1) and error(2) outcomes must be STRUCTURALLY distinct, never
# conflated: their exit codes differ. Drive both and require different codes.
# (In RED both yield 127, so this fails honestly — it is NOT a vacuous pass; in
# GREEN it becomes the real "stale never equals error" gate, FR-015/FR-021.)
rc_stale=0; "$GEN" --check "$STALE_ROOT" >/dev/null 2>&1 || rc_stale=$?
rc_err=0;   "$GEN" --check "$PRSMAL_ROOT" >/dev/null 2>&1 || rc_err=$?
set_test "stale exit code differs from error exit code (1 != 2)"
if [ "$rc_stale" -ne "$rc_err" ]; then _pass; else _fail "stale ($rc_stale) and error ($rc_err) must differ (FR-015/FR-021)"; fi

# ───────────────────────────────────────────────────────────────────────────
section "(b) --check writes nothing on every path, including the error path"
# ───────────────────────────────────────────────────────────────────────────
# Snapshot the committed fixtures, run --check across current/stale/error, then
# assert nothing on disk changed. --check must open nothing for writing (FR-012).
before_b="$(cd "$FIX" && find . -type f -exec shasum {} + | LC_ALL=C sort)"
set_test "--check on a stale map exits 1 (read-only path)"
run_gen _b1 1 --check "$STALE_ROOT"
set_test "--check on a malformed map exits 2 (error path, still read-only)"
run_gen _b2 2 --check "$PRSMAL_ROOT"
after_b="$(cd "$FIX" && find . -type f -exec shasum {} + | LC_ALL=C sort)"
set_test "--check modified zero committed fixture files (incl. error path)"
assert_eq "$before_b" "$after_b" "--check must write nothing on any path (FR-012)"

# ───────────────────────────────────────────────────────────────────────────
section "(c) trap disarmed before the deliberate --check exit 1 (stale != error)"
# ───────────────────────────────────────────────────────────────────────────
# Observable contract for D5/FR-021: a stale result surfaces as exit 1 on a CLEAN
# run, not remapped to 2 by an over-eager ERR trap. We assert the stale exit is
# exactly 1 (not 2) AND that the stale report goes to stdout while errors go to
# stderr — the two streams the consumers disambiguate on.
set_test "stale result is exit 1 (NOT remapped to error 2)"
rc_c=0; "$GEN" --check "$STALE_ROOT" >/dev/null 2>&1 || rc_c=$?
assert_eq "1" "$rc_c" "a clean stale run must exit 1, never 2 (D5/FR-021)"

# The stale report names the drifted spec; under specs/<branch>/ that token is the
# branch dir. The error message names the offending manifest's spec dir likewise.
set_test "stale detail is on stdout (consumer reads staleness from stdout)"
stale_stdout="$("$GEN" --check "$STALE_ROOT" 2>/dev/null || true)"
assert_contains "$stale_stdout" "prsg-901-stale" "stale report must name the drifted map on stdout"

set_test "error detail is on stderr (never conflated with the stale stdout)"
err_stderr="$("$GEN" --check "$PRSMAL_ROOT" 2>&1 >/dev/null || true)"
assert_contains "$err_stderr" "prs.json" "error message must name the offending file on stderr (FR-016)"

# ───────────────────────────────────────────────────────────────────────────
section "(d) FR-009 — a missing marker pair skips that zone, rebuilds the others"
# ───────────────────────────────────────────────────────────────────────────
# skip-one-missing/ has the PRS pair absent but INDEX + BACKLINKS present and a
# stub spec.md. A write run must: (1) succeed, (2) leave NO PRS sentinels (the
# absent zone stays absent — not injected), (3) fill BACKLINKS (present zone is
# still rebuilt).
copy_d="$(fresh_copy "$SKIP1_ROOT")"
set_test "write run over a skip-one map succeeds (exit 0)"
rc_d=0; "$GEN" "$copy_d" >/dev/null 2>&1 || rc_d=$?
assert_eq "0" "$rc_d" "missing-one-pair must not be an error (FR-009)"
moc_d="$(cat "$copy_d/$SKIP1_MOC" 2>/dev/null || true)"
set_test "the absent PRS zone is NOT injected (stays skipped)"
assert_not_contains "$moc_d" "GENERATED:PRS:START" "FR-009: a missing pair is skipped, never injected"
set_test "the present BACKLINKS zone is still rebuilt (spec.md link emitted)"
assert_contains "$moc_d" "(spec.md)" "FR-009: other present zones are still rebuilt"

# ───────────────────────────────────────────────────────────────────────────
section "(e) FR-022 — unbalanced/duplicated pair -> fail-safe exit 2, no write"
# ───────────────────────────────────────────────────────────────────────────
copy_e="$(fresh_copy "$UNBAL_ROOT")"
before_e="$(shasum "$copy_e/$UNBAL_MOC" | awk '{print $1}')"
set_test "write run over an unbalanced-marker map -> exit 2"
rc_e=0; "$GEN" "$copy_e" >/dev/null 2>&1 || rc_e=$?
assert_eq "2" "$rc_e" "unbalanced/duplicated marker pair must fail safe (FR-022)"
after_e="$(shasum "$copy_e/$UNBAL_MOC" | awk '{print $1}')"
set_test "the unbalanced-marker map is left wholly unmodified (no partial write)"
assert_eq "$before_e" "$after_e" "FR-022/FR-016: no partial write on the fail-safe path"

# ───────────────────────────────────────────────────────────────────────────
section "(f) atomic per-target write — a failure on one map cannot half-write others"
# ───────────────────────────────────────────────────────────────────────────
# Observable invariant (atomicity is not truly unit-testable without fault
# injection): run write mode over the dedicated atomicity REPO_ROOT, which holds a
# good map + an out-of-scope legacy map + a poison (unbalanced) map under one
# specs/ tree. The run must fail (exit 2) AND leave no leftover mktemp turd beside
# any target AND leave the out-of-scope legacy spec byte-for-byte untouched.
copy_f="$(fresh_copy "$ATOM_ROOT")"
legacy_before_f="$(shasum "$copy_f/$ATOM_LEGACY_MOC" | awk '{print $1}')"
set_test "write run over a root containing a poison map -> exit 2"
rc_f=0; "$GEN" "$copy_f" >/dev/null 2>&1 || rc_f=$?
assert_eq "2" "$rc_f" "a malformed/unbalanced target in the batch fails safe (FR-016)"
set_test "no leftover mktemp temp files beside any target after the failed run"
turds_f="$(find "$copy_f" \( -name 'SPEC-MOC.md.*' -o -name '*.tmp.*' \) 2>/dev/null | LC_ALL=C sort || true)"
assert_eq "" "$turds_f" "atomic write must not leave a sibling temp file behind (D6)"
legacy_after_f="$(shasum "$copy_f/$ATOM_LEGACY_MOC" | awk '{print $1}')"
set_test "an out-of-scope legacy map is untouched even when the batch errors"
assert_eq "$legacy_before_f" "$legacy_after_f" "per-target atomicity (FR-016)"

# ───────────────────────────────────────────────────────────────────────────
section "(g) PRS empty/absent -> empty-but-valid; malformed -> exit 2 (distinct)"
# ───────────────────────────────────────────────────────────────────────────
# absent prs.json: empty-but-valid link-free PRS zone, not an error.
copy_g_abs="$(fresh_copy "$PRSABS_ROOT")"
set_test "absent prs.json -> write run succeeds (exit 0, FR-011)"
rc_g1=0; "$GEN" "$copy_g_abs" >/dev/null 2>&1 || rc_g1=$?
assert_eq "0" "$rc_g1" "absent prs.json is empty-but-valid, not an error (FR-011)"
moc_g_absent="$(cat "$copy_g_abs/$PRSABS_MOC" 2>/dev/null || true)"
set_test "absent-PRS map keeps an empty, link-free PRS zone (consecutive markers)"
assert_contains "$moc_g_absent" $'GENERATED:PRS:START (do not edit; regenerated by generate-spec-index.sh) -->\n<!-- GENERATED:PRS:END -->' "empty PRS zone = consecutive START/END, no body (D2/FR-011)"

# empty records: []: same empty-but-valid behavior.
copy_g_emp="$(fresh_copy "$PRSEMP_ROOT")"
set_test "records:[] -> write run succeeds (exit 0, FR-011)"
rc_g2=0; "$GEN" "$copy_g_emp" >/dev/null 2>&1 || rc_g2=$?
assert_eq "0" "$rc_g2" "records:[] is empty-but-valid, not an error (FR-011)"

# populated: renders plain-text rows (NOT links), ordered by normalized slice then
# pr ascending. Fixture records are out of pr order (142 before 117) -> 117 first.
copy_g_pop="$(fresh_copy "$PRSPOP_ROOT")"
set_test "populated prs.json -> write run succeeds (exit 0)"
rc_g3=0; "$GEN" "$copy_g_pop" >/dev/null 2>&1 || rc_g3=$?
assert_eq "0" "$rc_g3" "a populated manifest renders without error"
moc_g_pop="$(cat "$copy_g_pop/$PRSPOP_MOC" 2>/dev/null || true)"
set_test "populated PRS row is plain text with the U+00B7 separator (not a link)"
assert_contains "$moc_g_pop" "PRSG-905 ${PRS_SEP} PR#117 ${PRS_SEP} abc1234" "D3 plain-text row, exact bytes"
set_test "PRS rows are ordered by pr ascending (117 before 142)"
# Byte offset of the pr#117 row must precede the pr#142 row in the rendered zone.
idx_117="${moc_g_pop%%PR#117*}"; idx_142="${moc_g_pop%%PR#142*}"
if [ "${#idx_117}" -lt "${#idx_142}" ]; then _pass; else _fail "PRS ordering: pr#117 must precede pr#142 (D3)"; fi
set_test "the PRS zone is link-free (no []() introduced by a record)"
prs_zone_g="${moc_g_pop#*GENERATED:PRS:START}"; prs_zone_g="${prs_zone_g%%GENERATED:PRS:END*}"
assert_not_contains "$prs_zone_g" "](" "PRS rows are plain text, never []() links (D3)"

# malformed: fail-safe exit 2, distinct from the absent/empty case above.
copy_g_mal="$(fresh_copy "$PRSMAL_ROOT")"
set_test "malformed prs.json -> exit 2 (error, distinct from absent/empty)"
rc_g4=0; "$GEN" "$copy_g_mal" >/dev/null 2>&1 || rc_g4=$?
assert_eq "2" "$rc_g4" "malformed manifest fails safe (FR-016), never empty-but-valid"

# type violation — a `pr` that is a STRING ("abc"): the schema requires an integer,
# so this is the malformed case (exit 2), NOT a silently-corrupt exit-0 row. A
# presence-only guard would let "abc" through and only blow up later (printf invalid
# number) while exiting 0; the renderer must type-check and fail safe (FR-016, D3).
copy_g_bstr="$(fresh_copy "$PRSBADSTR_ROOT")"
str_before="$(shasum "$copy_g_bstr/$PRSBADSTR_MOC" | awk '{print $1}')"
set_test "string pr (\"abc\") -> write run exits 2 (type violation, FR-016)"
rc_g5=0; gstr_err="$("$GEN" "$copy_g_bstr" 2>&1 >/dev/null)" || rc_g5=$?
assert_eq "2" "$rc_g5" "a non-integer pr is malformed, never a silent exit-0 corrupt row (D3/FR-016)"
set_test "string-pr manifest is distinct from absent/empty (exit 2 != exit 0)"
if [ "$rc_g5" -ne "$rc_g1" ]; then _pass; else _fail "type violation ($rc_g5) must differ from absent/empty ($rc_g1) (FR-011 vs FR-016)"; fi
set_test "string-pr write leaves the map byte-for-byte unchanged (no partial write)"
str_after="$(shasum "$copy_g_bstr/$PRSBADSTR_MOC" | awk '{print $1}')"
assert_eq "$str_before" "$str_after" "fail-safe path must not write (FR-016)"
set_test "string-pr error message names prs.json on stderr (not stdout)"
assert_contains "$gstr_err" "prs.json" "actionable error must name the offending manifest (FR-016)"
# A malformed manifest must surface EXACTLY ONE stderr line (the precise one from
# render_prs naming prs.json) — never a duplicate from a second `|| err` at the call
# site. speckit-status surfaces "the generator's stderr line" (singular).
set_test "string-pr emits exactly ONE stderr line (no duplicate fail-safe message)"
gstr_lines="$("$GEN" "$copy_g_bstr" 2>&1 >/dev/null | grep -c . || true)"
assert_eq "1" "$gstr_lines" "malformed manifest must surface a single, precise stderr line"
set_test "string-pr --check also exits 2 (read-only error path)"
rc_g5c=0; "$GEN" --check "$PRSBADSTR_ROOT" >/dev/null 2>&1 || rc_g5c=$?
assert_eq "2" "$rc_g5c" "--check on a type-violation manifest is exit 2, never exit 1 stale (FR-012/FR-016)"

# type violation — a `pr` that is a NON-INTEGER number (117.5): also rejected, since
# the schema requires an integer PR number. floor != value => malformed (exit 2).
copy_g_bflt="$(fresh_copy "$PRSBADFLT_ROOT")"
flt_before="$(shasum "$copy_g_bflt/$PRSBADFLT_MOC" | awk '{print $1}')"
set_test "non-integer pr (117.5) -> write run exits 2 (type violation, FR-016)"
rc_g6=0; "$GEN" "$copy_g_bflt" >/dev/null 2>&1 || rc_g6=$?
assert_eq "2" "$rc_g6" "a fractional pr is malformed, never a silent exit-0 row (D3/FR-016)"
set_test "non-integer-pr write leaves the map byte-for-byte unchanged (no partial write)"
flt_after="$(shasum "$copy_g_bflt/$PRSBADFLT_MOC" | awk '{print $1}')"
assert_eq "$flt_before" "$flt_after" "fail-safe path must not write (FR-016)"

# ───────────────────────────────────────────────────────────────────────────
section "(h) template-born block == inject-if-missing block (byte-identical)"
# ───────────────────────────────────────────────────────────────────────────
# inject-missing-all/ (no zones) and template-born/ (zones present from template)
# share the same pre-anchor body, spec_id, and a single spec.md artifact. After a
# write run, both files must be BYTE-IDENTICAL: the injected three-zone block
# equals the template-born one (shared assemble_zone_block, FR-008/FR-017).
copy_h="$(fresh_copy)"
set_test "inject-if-missing write run succeeds (exit 0)"
rc_h1=0; "$GEN" "$copy_h/inject-missing-all" >/dev/null 2>&1 || rc_h1=$?
assert_eq "0" "$rc_h1" "inject-if-missing must succeed"
set_test "template-born write run succeeds (exit 0)"
rc_h2=0; "$GEN" "$copy_h/template-born" >/dev/null 2>&1 || rc_h2=$?
assert_eq "0" "$rc_h2" "template-born fill must succeed"
# Read each map at its real nested path (specs/<branch>/SPEC-MOC.md) via the
# per-case constants defined above — the case dir is the REPO_ROOT, not the MOC dir.
inj_h="$(cat "$copy_h/inject-missing-all/$INJECT_MOC" 2>/dev/null || true)"
tpl_h="$(cat "$copy_h/template-born/$TPL_MOC" 2>/dev/null || true)"
set_test "the injected map is byte-identical to the template-born map"
assert_eq "$tpl_h" "$inj_h" "FR-008/FR-017: inject-if-missing and template-born are byte-identical"
set_test "the inject-if-missing map actually gained the three zones"
assert_contains "$inj_h" "GENERATED:BACKLINKS:END" "inject must add the zone block (guards a vacuous empty==empty pass)"

# ───────────────────────────────────────────────────────────────────────────
section "(i) canonical ordering — fixed artifact precedence, then path order"
# ───────────────────────────────────────────────────────────────────────────
# stale-fill/ has spec.md, plan.md, contracts/sample.md, .process/prs.json. The
# BACKLINKS zone must order by the fixed precedence spec -> plan -> ... ->
# contracts -> ... -> .process, independent of filesystem enumeration order.
copy_i="$(fresh_copy)"
set_test "write run over the ordering fixture succeeds (exit 0)"
rc_i=0; "$GEN" "$copy_i/stale-fill" >/dev/null 2>&1 || rc_i=$?
assert_eq "0" "$rc_i" "the ordering fixture must render without error"
# Read the map at its real nested path (specs/<branch>/SPEC-MOC.md) via $STALE_MOC.
moc_i="$(cat "$copy_i/stale-fill/$STALE_MOC" 2>/dev/null || true)"
bz_i="${moc_i#*GENERATED:BACKLINKS:START}"; bz_i="${bz_i%%GENERATED:BACKLINKS:END*}"
set_test "spec.md precedes plan.md in BACKLINKS (fixed precedence)"
i_spec="${bz_i%%(spec.md)*}"; i_plan="${bz_i%%(plan.md)*}"
if [ "${#i_spec}" -lt "${#i_plan}" ]; then _pass; else _fail "ordering: spec.md must precede plan.md (FR-005)"; fi
set_test "plan.md precedes contracts/ in BACKLINKS (fixed precedence)"
i_contract="${bz_i%%contracts/*}"
if [ "${#i_plan}" -lt "${#i_contract}" ]; then _pass; else _fail "ordering: plan.md must precede contracts/** (FR-005)"; fi
set_test "contracts/ precedes .process/ in BACKLINKS (fixed precedence)"
i_proc="${bz_i%%.process/*}"
if [ "${#i_contract}" -lt "${#i_proc}" ]; then _pass; else _fail "ordering: contracts/** must precede .process/** (FR-005)"; fi

# ───────────────────────────────────────────────────────────────────────────
section "(j) a symlinked SPEC-MOC.md is rejected (exit 2), never followed + rewritten"
# ───────────────────────────────────────────────────────────────────────────
# A non-regular-file target where a MOC is expected — here a SYMLINK to a regular
# file — must fail safe (exit 2, FR-016) and must NOT be replaced by a regular file
# (a naive `mv -f` over a followed symlink would silently clobber the link). The
# symlink is constructed at runtime: copy the fixture, then point SPEC-MOC.md at its
# committed regular-file target moc-target.md.
copy_j="$(fresh_copy "$SYMLINK_ROOT")"
ln -sf "moc-target.md" "$copy_j/$SYMLINK_MOC"
set_test "the test set up SPEC-MOC.md as a symlink (precondition)"
if [ -L "$copy_j/$SYMLINK_MOC" ]; then _pass; else _fail "fixture setup failed: SPEC-MOC.md is not a symlink"; fi
set_test "write run over a symlinked-MOC spec -> exit 2 (non-regular target, FR-016)"
rc_j=0; jerr="$("$GEN" "$copy_j" 2>&1 >/dev/null)" || rc_j=$?
assert_eq "2" "$rc_j" "a symlinked SPEC-MOC.md must be rejected, not followed (FR-016)"
set_test "SPEC-MOC.md is STILL a symlink after the failed run (not clobbered to a file)"
if [ -L "$copy_j/$SYMLINK_MOC" ]; then _pass; else _fail "FR-016: the symlink was replaced by a regular file (mv -f followed the link)"; fi
set_test "the symlink's target file is itself unchanged (no write-through)"
# Resolve the link target relative to the spec dir and confirm it was not rewritten.
tgt_before="$(shasum "$copy_j/$SYMLINK_TARGET" | awk '{print $1}')"
assert_contains "$jerr" "SPEC-MOC.md" "error must name the offending target on stderr (FR-016)"
set_test "the symlink target was not written through the link"
# moc-target.md is version-marked but is NOT named SPEC-MOC.md, so discovery never
# treats it as a map; its bytes must be identical to the committed fixture target.
tgt_committed="$(shasum "$SYMLINK_ROOT/$SYMLINK_TARGET" | awk '{print $1}')"
assert_eq "$tgt_committed" "$tgt_before" "FR-016: nothing was written through the symlink"
set_test "symlinked-MOC --check also exits 2 (read-only error path)"
rc_jc=0; "$GEN" --check "$copy_j" >/dev/null 2>&1 || rc_jc=$?
assert_eq "2" "$rc_jc" "--check on a symlinked target is exit 2, never exit 1 stale (FR-012/FR-016)"

test_summary
