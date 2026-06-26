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
O5SCAN_ROOT="$FIX/o5-flat-scan"
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
MPE_FIX="$HERE/fixtures/multi-pr-emission"
PRSV1_ROOT="$MPE_FIX/prs-manifests/schema-v1-root"; PRSV1_MOC="specs/prsg-920-prs-v1/SPEC-MOC.md"
PRSV2_ROOT="$MPE_FIX/prs-manifests/schema-v2-root"; PRSV2_MOC="specs/prsg-921-prs-v2/SPEC-MOC.md"
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

# Roadmap-MOC home-note fixtures (PRSG-004). The home note lives at
# docs/ai/specs/<slug>-roadmap-MOC.md and is processed disjoint from the specs/
# scan. roadmap-moc/ exercises the home-scoped INDEX fill + every per-spec INDEX
# staying empty/byte-identical; roadmap-moc-no-index/ exercises the FR-017a
# fail-safe (a gated home note missing its INDEX pair -> exit 2, no write).
RMOC_ROOT="$FIX/roadmap-moc"
RMOC_HOME="docs/ai/specs/myproject-roadmap-MOC.md"
RMOC_OTHER_HOME="docs/ai/specs/otherproject-roadmap-MOC.md"
RMOC_SPEC1="specs/prsg-001-foo/SPEC-MOC.md"     # gated, status=complete  -> indexed
RMOC_SPEC2="specs/prsg-002-bar/SPEC-MOC.md"     # gated, status=""        -> indexed (blank status)
RMOC_SPEC10="specs/prsg-010-baz/SPEC-MOC.md"    # gated, status=in-progress -> indexed
RMOC_FLAT_OWNED="specs/prsg-011-flat-owned/spec.md" # ungated flat fallback, owned by myproject
RMOC_FLAT_UNOWNED="specs/prsg-099-flat/spec.md" # ungated flat fallback, no roadmap owner -> skipped
RMOC_NOID="specs/prsg-003-noid/SPEC-MOC.md"     # gated, spec_id=""        -> SKIPPED (FR-015a)
RMOC_OTHER_SPEC="specs/prsg-004-other/SPEC-MOC.md" # gated, points to other roadmap -> indexed only there
RMOC_LEGACY="specs/legacy-thing/SPEC-MOC.md"    # NOT gated                -> SKIPPED (FR-016)
RMOCNI_ROOT="$FIX/roadmap-moc-no-index"
RMOCNI_HOME="docs/ai/specs/broken-roadmap-MOC.md"
RMOCNI_SPEC1="specs/prsg-001-foo/SPEC-MOC.md"
RMOCNIP_ROOT="$FIX/roadmap-moc-no-index-partial"
RMOCNIP_HOME="docs/ai/specs/partial-roadmap-MOC.md"
RMOCNIP_SPEC1="specs/prsg-001-foo/SPEC-MOC.md"
RMOCEZ_ROOT="$FIX/roadmap-moc-extra-zones"
RMOCEZ_HOME="docs/ai/specs/extra-zones-roadmap-MOC.md"
RMOCEZ_SPEC1="specs/prsg-001-foo/SPEC-MOC.md"

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

set_test "--check on O5 flat parent/child maps ignores nested child dirs"
run_gen out_o5 0 --check "$O5SCAN_ROOT"

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

copy_g_v1="$(fresh_copy "$PRSV1_ROOT")"
set_test "schemaVersion 1 prs.json remains backward-compatible"
rc_gv1=0; "$GEN" "$copy_g_v1" >/dev/null 2>&1 || rc_gv1=$?
assert_eq "0" "$rc_gv1" "schemaVersion 1 manifest must render"
moc_g_v1="$(cat "$copy_g_v1/$PRSV1_MOC" 2>/dev/null || true)"
set_test "schemaVersion 1 row keeps legacy plain-text format"
assert_contains "$moc_g_v1" "PRSG-920 ${PRS_SEP} PR#220 ${PRS_SEP} v1abcde" "legacy v1 row"

copy_g_v2="$(fresh_copy "$PRSV2_ROOT")"
set_test "schemaVersion 2 prs.json renders successfully"
rc_gv2=0; "$GEN" "$copy_g_v2" >/dev/null 2>&1 || rc_gv2=$?
assert_eq "0" "$rc_gv2" "schemaVersion 2 manifest must render"
moc_g_v2="$(cat "$copy_g_v2/$PRSV2_MOC" 2>/dev/null || true)"
set_test "schemaVersion 2 emits the reviewer table columns"
assert_contains "$moc_g_v2" "| Order | Slice | PR | Status | Branch | Base | SHA | Scope | Verification |"
set_test "schemaVersion 2 documents PR evidence SHA snapshot semantics"
assert_contains "$moc_g_v2" 'Note: for open PR rows, `SHA` records the PR evidence snapshot head commit; for merged rows, `SHA` records the merged commit.' "v2 PR rows must clarify open and merged SHA semantics"
set_test "schemaVersion 2 open row displays head_sha"
assert_contains "$moc_g_v2" "| 1 | foundation | PR#201 | opened | prsg-009-multi-pr-emission/01-foundation | main | headabc1 | docs/foundation.md, speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh | specs/prsg-009-multi-pr-emission/.process/emission/foundation/layer4.log |"
set_test "schemaVersion 2 merged row prefers merged_sha"
assert_contains "$moc_g_v2" "| 2 | us1 | PR#202 | merged | prsg-009-multi-pr-emission/02-us1 | prsg-009-multi-pr-emission/01-foundation | mergeabc2 | docs/us1.md | specs/prsg-009-multi-pr-emission/.process/emission/us1/layer4.log |"
set_test "schemaVersion 2 PRS zone remains link-free"
prs_zone_gv2="${moc_g_v2#*GENERATED:PRS:START}"; prs_zone_gv2="${prs_zone_gv2%%GENERATED:PRS:END*}"
assert_not_contains "$prs_zone_gv2" "](" "v2 PRS rows are plain text/table cells, never markdown links"

copy_g_v2str="$(fresh_copy "$PRSV2_ROOT")"
tmp_v2str="$copy_g_v2str/specs/prsg-921-prs-v2/.process/prs.json.tmp"
jq '.schemaVersion = "2"' "$copy_g_v2str/specs/prsg-921-prs-v2/.process/prs.json" > "$tmp_v2str"
mv "$tmp_v2str" "$copy_g_v2str/specs/prsg-921-prs-v2/.process/prs.json"
set_test "schemaVersion 2 manifests require numeric schemaVersion"
rc_gv2str=0; "$GEN" "$copy_g_v2str" >/dev/null 2>&1 || rc_gv2str=$?
assert_eq "2" "$rc_gv2str" "schemaVersion must be numeric 2, not string \"2\""

copy_g_v2_open_merge="$(fresh_copy "$PRSV2_ROOT")"
tmp_v2om="$copy_g_v2_open_merge/specs/prsg-921-prs-v2/.process/prs.json.tmp"
jq '(.records[] | select(.slice_id == "foundation") | .merged_sha) = "openmerge-sha"' \
  "$copy_g_v2_open_merge/specs/prsg-921-prs-v2/.process/prs.json" > "$tmp_v2om"
mv "$tmp_v2om" "$copy_g_v2_open_merge/specs/prsg-921-prs-v2/.process/prs.json"
set_test "schemaVersion 2 open rows ignore merged_sha and display head_sha"
rc_gv2om=0; "$GEN" "$copy_g_v2_open_merge" >/dev/null 2>&1 || rc_gv2om=$?
assert_eq "0" "$rc_gv2om" "open row with merged_sha should still render from head_sha"
moc_g_v2om="$(cat "$copy_g_v2_open_merge/$PRSV2_MOC" 2>/dev/null || true)"
set_test "schemaVersion 2 open row does not leak merged_sha"
assert_not_contains "$moc_g_v2om" "openmerge-sha"

copy_g_v2_missing_merge="$(fresh_copy "$PRSV2_ROOT")"
tmp_v2mm="$copy_g_v2_missing_merge/specs/prsg-921-prs-v2/.process/prs.json.tmp"
jq '(.records[] | select(.slice_id == "us1")) |= del(.merged_sha)' \
  "$copy_g_v2_missing_merge/specs/prsg-921-prs-v2/.process/prs.json" > "$tmp_v2mm"
mv "$tmp_v2mm" "$copy_g_v2_missing_merge/specs/prsg-921-prs-v2/.process/prs.json"
set_test "schemaVersion 2 merged rows require merged_sha"
rc_gv2mm=0; "$GEN" "$copy_g_v2_missing_merge" >/dev/null 2>&1 || rc_gv2mm=$?
assert_eq "2" "$rc_gv2mm" "merged rows must not fall back to head_sha when merged_sha is missing"

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

# ───────────────────────────────────────────────────────────────────────────
section "(k) roadmap-MOC home note — INDEX fills home-scoped rows; every spec-MOC stays empty"
# ───────────────────────────────────────────────────────────────────────────
# The home note at docs/ai/specs/<slug>-roadmap-MOC.md carries ONLY the INDEX
# sentinel pair. A write run must fill its INDEX with one row per gated spec whose
# spec_id is non-empty and whose `up:` target points at that home note or its
# technical roadmap, normalized-ID ascending, each a relative []() link — while
# EVERY per-spec SPEC-MOC INDEX stays empty/byte-identical (FR-018).
copy_k="$(fresh_copy "$RMOC_ROOT")"

# Snapshot every per-spec SPEC-MOC.md BEFORE the run, to prove byte-identity after.
spec1_before_k="$(shasum "$copy_k/$RMOC_SPEC1" | awk '{print $1}')"
spec2_before_k="$(shasum "$copy_k/$RMOC_SPEC2" | awk '{print $1}')"
spec10_before_k="$(shasum "$copy_k/$RMOC_SPEC10" | awk '{print $1}')"
noid_before_k="$(shasum "$copy_k/$RMOC_NOID" | awk '{print $1}')"
other_before_k="$(shasum "$copy_k/$RMOC_OTHER_SPEC" | awk '{print $1}')"
legacy_before_k="$(shasum "$copy_k/$RMOC_LEGACY" | awk '{print $1}')"

set_test "write run over a repo with a roadmap-MOC home note succeeds (exit 0)"
rc_k=0; "$GEN" "$copy_k" >/dev/null 2>&1 || rc_k=$?
assert_eq "0" "$rc_k" "a well-formed home note + gated specs must regenerate without error (FR-011)"

home_k="$(cat "$copy_k/$RMOC_HOME" 2>/dev/null || true)"
other_home_k="$(cat "$copy_k/$RMOC_OTHER_HOME" 2>/dev/null || true)"
# Isolate the home note's INDEX zone body (between the START and END sentinels).
hidx_k="${home_k#*GENERATED:INDEX:START}"; hidx_k="${hidx_k#*$'\n'}"; hidx_k="${hidx_k%%<!-- GENERATED:INDEX:END*}"
ohidx_k="${other_home_k#*GENERATED:INDEX:START}"; ohidx_k="${ohidx_k#*$'\n'}"; ohidx_k="${ohidx_k%%<!-- GENERATED:INDEX:END*}"

# (1) home-scoped fill: one row per gated, non-empty-spec_id spec owned by that
# roadmap, exact bytes incl. the U+00B7 separator framing (FR-012/FR-014/SC-006).
# The link is the relative ../../../specs/<dir>/SPEC-MOC.md target — never a
# [[wikilink]].
set_test "home INDEX has the PRSG-001 row with exact bytes (relative link + U+00B7 + status)"
assert_contains "$home_k" "- [PRSG-001](../../../specs/prsg-001-foo/SPEC-MOC.md) ${PRS_SEP} complete" "FR-012/FR-014 exact row bytes"
set_test "home INDEX has the PRSG-010 row with exact bytes"
assert_contains "$home_k" "- [PRSG-010](../../../specs/prsg-010-baz/SPEC-MOC.md) ${PRS_SEP} in-progress" "FR-012/FR-014 exact row bytes"
set_test "home INDEX excludes specs owned by another roadmap-MOC"
assert_not_contains "$hidx_k" "prsg-004-other" "home INDEX must be scoped by SPEC-MOC up target"
set_test "other roadmap home INDEX includes its own technical-roadmap-owned spec"
assert_contains "$other_home_k" "- [PRSG-004](../../../specs/prsg-004-other/SPEC-MOC.md) ${PRS_SEP} review" "home_up target also owns specs pointing at the technical roadmap"
set_test "other roadmap home INDEX excludes myproject specs"
assert_not_contains "$ohidx_k" "prsg-001-foo" "other home INDEX must not be repo-wide"
set_test "home INDEX includes an owned flat fallback spec"
assert_contains "$home_k" $'- [PRSG-011-FLAT-OWNED](../../../specs/prsg-011-flat-owned/spec.md) \xc2\xb7\n' "structure-version fallback rows require roadmap ownership"
set_test "other roadmap home INDEX excludes flat fallback specs owned by myproject"
assert_not_contains "$ohidx_k" "prsg-011-flat-owned" "flat fallback rows must be scoped to their roadmap owner"
set_test "home INDEX excludes unowned flat fallback specs"
assert_not_contains "$hidx_k" "prsg-099-flat" "unowned flat fallback rows must not leak into roadmap home INDEX"
set_test "other roadmap home INDEX excludes unowned flat fallback specs"
assert_not_contains "$ohidx_k" "prsg-099-flat" "unowned flat fallback rows must not leak into any roadmap home INDEX"
set_test "home INDEX excludes memory fallback headings without roadmap ownership"
assert_not_contains "$hidx_k" "PRSG-098" "memory fallback rows have no ownership metadata and must not enter scoped home INDEX"
set_test "other roadmap home INDEX excludes memory fallback headings without roadmap ownership"
assert_not_contains "$ohidx_k" "PRSG-098" "memory fallback rows have no ownership metadata and must not enter scoped home INDEX"
# (3) empty-status spec STILL emits a row, separator present + blank status — pin the
# frozen byte form (separator, no trailing whitespace, end of line) (FR-015, SC-004).
set_test "empty-status spec still emits a row without trailing whitespace (FR-015)"
assert_contains "$home_k" $'- [PRSG-002](../../../specs/prsg-002-bar/SPEC-MOC.md) \xc2\xb7\n' "FR-015 blank-status row: separator without trailing whitespace, row not dropped"

# (2) every INDEX link is a relative []() target, NEVER a [[wikilink]] (FR-014/SC-006).
set_test "the home INDEX zone contains no [[wikilink]] targets (relative links only)"
assert_not_contains "$hidx_k" "[[" "FR-014/SC-006: INDEX links are relative []() targets, never [[wikilinks]]"
set_test "the home INDEX zone links into ../../../specs/ (reachable from docs/ai/specs/)"
assert_contains "$hidx_k" "](../../../specs/" "FR-014: relative target resolves docs/ai/specs -> repo-root specs"

# (4) absent/empty-spec_id gated spec is SKIPPED — no row (FR-015a). Its dir basename
# (prsg-003-noid) and its blank status value must not appear as an INDEX row.
set_test "the absent-spec_id gated spec is SKIPPED — no row in the home INDEX (FR-015a)"
assert_not_contains "$hidx_k" "prsg-003-noid" "FR-015a: a gated spec with empty spec_id is not fabricated into a zero-width row"
# (5) legacy non-gated dir is skipped (FR-016).
set_test "the legacy non-gated dir is SKIPPED — no row in the home INDEX (FR-016)"
assert_not_contains "$hidx_k" "legacy-thing" "FR-016: only version-marked specs are indexed"
set_test "the home INDEX has no LEGACY-THING link text either (legacy fully skipped)"
assert_not_contains "$hidx_k" "LEGACY-THING" "FR-016: legacy spec_id never appears as a row"

# (FR-013) ordering: PRSG-001 row precedes PRSG-002 precedes PRSG-010, normalized-ID
# ascending. Compare byte offsets via each row's UNIQUE link path (no glob
# metacharacters — a [PRSG-00N] pattern would be a bracket character class, not a
# literal, so anchor on the relative SPEC-MOC.md target instead).
set_test "home INDEX rows are normalized-ID ascending (001 < 002 < 010)"
off1_k="${home_k%%specs/prsg-001-foo/*}"
off2_k="${home_k%%specs/prsg-002-bar/*}"
off10_k="${home_k%%specs/prsg-010-baz/*}"
if [ "${#off1_k}" -lt "${#off2_k}" ] && [ "${#off2_k}" -lt "${#off10_k}" ]; then _pass; else _fail "FR-013: INDEX rows must be normalized-ID ascending"; fi

# (2nd half of the context-scoping invariant) — every per-spec SPEC-MOC INDEX stays
# empty/byte-identical after the run (FR-018/SC-005). Each per-spec file must be
# unchanged AND its own INDEX zone must remain consecutive START/END (link-free).
set_test "per-spec PRSG-001 SPEC-MOC.md is byte-identical after the run (FR-018)"
assert_eq "$spec1_before_k" "$(shasum "$copy_k/$RMOC_SPEC1" | awk '{print $1}')" "FR-018: spec-MOC path is byte-identical (INDEX stays empty)"
set_test "per-spec PRSG-002 SPEC-MOC.md is byte-identical after the run (FR-018)"
assert_eq "$spec2_before_k" "$(shasum "$copy_k/$RMOC_SPEC2" | awk '{print $1}')" "FR-018: spec-MOC path is byte-identical"
set_test "per-spec PRSG-010 SPEC-MOC.md is byte-identical after the run (FR-018)"
assert_eq "$spec10_before_k" "$(shasum "$copy_k/$RMOC_SPEC10" | awk '{print $1}')" "FR-018: spec-MOC path is byte-identical"
set_test "per-spec absent-spec_id SPEC-MOC.md is byte-identical after the run (FR-018)"
assert_eq "$noid_before_k" "$(shasum "$copy_k/$RMOC_NOID" | awk '{print $1}')" "FR-018: a skipped-from-INDEX spec-MOC is still byte-identical"
set_test "per-spec other-roadmap SPEC-MOC.md is byte-identical after the run (FR-018)"
assert_eq "$other_before_k" "$(shasum "$copy_k/$RMOC_OTHER_SPEC" | awk '{print $1}')" "FR-018: other-roadmap spec-MOC path is byte-identical"
set_test "the legacy non-gated SPEC-MOC.md is byte-identical after the run (FR-016)"
assert_eq "$legacy_before_k" "$(shasum "$copy_k/$RMOC_LEGACY" | awk '{print $1}')" "FR-016: legacy spec-MOC left untouched"
set_test "the per-spec PRSG-001 INDEX zone is still empty (consecutive START/END, link-free)"
spec1_body_k="$(cat "$copy_k/$RMOC_SPEC1" 2>/dev/null || true)"
assert_contains "$spec1_body_k" $'GENERATED:INDEX:START (do not edit; regenerated by generate-spec-index.sh) -->\n<!-- GENERATED:INDEX:END -->' "FR-018: spec-MOC INDEX stays empty even while the home note fills"

# (7) idempotence — a SECOND consecutive run over the now-filled home note is a
# zero-byte diff (SC-004/FR-019). After the first write the home note is up to date,
# so --check must report current (exit 0) and a second write must change nothing.
set_test "after the fill, --check reports the home note current (exit 0, idempotent)"
rc_kc=0; "$GEN" --check "$copy_k" >/dev/null 2>&1 || rc_kc=$?
assert_eq "0" "$rc_kc" "SC-004/FR-019: a regenerated home note is idempotent (no drift on re-check)"
home_k_first="$(shasum "$copy_k/$RMOC_HOME" | awk '{print $1}')"
set_test "a second write run leaves the home note byte-identical (zero-byte diff)"
rc_k2=0; "$GEN" "$copy_k" >/dev/null 2>&1 || rc_k2=$?
assert_eq "0" "$rc_k2" "second write run must succeed"
assert_eq "$home_k_first" "$(shasum "$copy_k/$RMOC_HOME" | awk '{print $1}')" "SC-004/FR-019: second run is a zero-byte diff on the home note"

# (no-home-note no-op) a repo with NO home note still processes specs/ unaffected —
# implicitly covered by every other group (none carry a home note) and asserted by
# the unchanged PRSG-003 cases; no extra fixture needed here.

# ───────────────────────────────────────────────────────────────────────────
section "(k2) roadmap-MOC home note — zero active spec dirs clears INDEX"
# ───────────────────────────────────────────────────────────────────────────
# Archive cleanup can leave specs/ containing only .gitkeep while a roadmap-MOC
# home note remains. The generator must still process the home note and render an
# empty INDEX zone instead of failing under set -u on an empty Bash array.
copy_k2="$(fresh_copy "$RMOC_ROOT")"
find "$copy_k2/specs" -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} +

set_test "write run over a repo with zero active spec dirs and a roadmap-MOC home note succeeds"
rc_k2=0; "$GEN" "$copy_k2" >/dev/null 2>&1 || rc_k2=$?
assert_eq "0" "$rc_k2" "empty specs/ with a gated roadmap-MOC home note must regenerate without error"
home_k2="$(cat "$copy_k2/$RMOC_HOME" 2>/dev/null || true)"
set_test "home INDEX is empty after zero-active-spec regeneration"
assert_contains "$home_k2" $'GENERATED:INDEX:START (do not edit; regenerated by generate-spec-index.sh) -->\n<!-- GENERATED:INDEX:END -->' "zero active specs renders an empty home INDEX zone"
set_test "after zero-active-spec regeneration, --check reports current"
rc_k2c=0; "$GEN" --check "$copy_k2" >/dev/null 2>&1 || rc_k2c=$?
assert_eq "0" "$rc_k2c" "empty home INDEX is idempotent after regeneration"

# ───────────────────────────────────────────────────────────────────────────
section "(l) FR-017a — a gated home note missing its INDEX pair fails safe (exit 2, no write)"
# ───────────────────────────────────────────────────────────────────────────
# roadmap-moc-no-index/ has a version-gated home note carrying NONE of the three
# GENERATED pairs. For a home-note target the generator MUST fail safe (exit 2, no
# write, actionable stderr naming the offending home note) — it MUST NOT take the
# inject-if-missing path (which would inject all three zones and render PRS/BACKLINKS
# against docs/ai/specs/, contradicting FR-002). Fails RED today: main() does not yet
# discover home notes, so the malformed home note is silently ignored (exit 0).
copy_l="$(fresh_copy "$RMOCNI_ROOT")"
home_before_l="$(shasum "$copy_l/$RMOCNI_HOME" | awk '{print $1}')"
spec_before_l="$(shasum "$copy_l/$RMOCNI_SPEC1" | awk '{print $1}')"
set_test "write run over a gated home note missing its INDEX pair -> exit 2 (FR-017a)"
rc_l=0; lerr="$("$GEN" "$copy_l" 2>&1 >/dev/null)" || rc_l=$?
assert_eq "2" "$rc_l" "FR-017a: a gated home note without its INDEX zone must fail safe, never inject-if-missing"
set_test "the malformed home note is left wholly unmodified (no write, NOT injected)"
assert_eq "$home_before_l" "$(shasum "$copy_l/$RMOCNI_HOME" | awk '{print $1}')" "FR-017a: no write on the fail-safe path"
set_test "the malformed home note did NOT gain any injected GENERATED zones"
home_after_l="$(cat "$copy_l/$RMOCNI_HOME" 2>/dev/null || true)"
assert_not_contains "$home_after_l" "GENERATED:INDEX:START" "FR-017a: inject-if-missing must NOT fire for a home-note target"
assert_not_contains "$home_after_l" "GENERATED:PRS:START" "FR-017a: PRS/BACKLINKS must never be rendered against docs/ai/specs/"
set_test "the sibling gated spec-MOC is also untouched (whole batch aborted, no partial write)"
assert_eq "$spec_before_l" "$(shasum "$copy_l/$RMOCNI_SPEC1" | awk '{print $1}')" "FR-017a: fail-safe aborts the batch before any write"
set_test "the FR-017a error message names the offending home note on stderr (actionable)"
assert_contains "$lerr" "broken-roadmap-MOC.md" "FR-017a: stderr must name the malformed home note"
set_test "FR-017a --check also fails safe (exit 2, read-only error path)"
rc_lc=0; "$GEN" --check "$RMOCNI_ROOT" >/dev/null 2>&1 || rc_lc=$?
assert_eq "2" "$rc_lc" "FR-017a: --check on a malformed home note is exit 2, never exit 0/1"

# ───────────────────────────────────────────────────────────────────────────
section "(l2) FR-017a — a gated home note missing INDEX fails safe even with other pairs"
# ───────────────────────────────────────────────────────────────────────────
# roadmap-moc-no-index-partial/ has a version-gated home note with PRS and
# BACKLINKS pairs, but no INDEX pair. Home notes are only supported through INDEX,
# so this must take the same fail-safe as the all-absent malformed home note.
copy_l2="$(fresh_copy "$RMOCNIP_ROOT")"
home_before_l2="$(shasum "$copy_l2/$RMOCNIP_HOME" | awk '{print $1}')"
spec_before_l2="$(shasum "$copy_l2/$RMOCNIP_SPEC1" | awk '{print $1}')"
set_test "write run over a gated home note missing INDEX but carrying PRS/BACKLINKS -> exit 2"
rc_l2=0; l2err="$("$GEN" "$copy_l2" 2>&1 >/dev/null)" || rc_l2=$?
assert_eq "2" "$rc_l2" "FR-017a: a gated home note without INDEX must fail safe even when other generated pairs exist"
set_test "the partial malformed home note is left wholly unmodified"
assert_eq "$home_before_l2" "$(shasum "$copy_l2/$RMOCNIP_HOME" | awk '{print $1}')" "FR-017a: no write on partial home-note fail-safe path"
set_test "the partial malformed home note did NOT gain an injected INDEX zone"
home_after_l2="$(cat "$copy_l2/$RMOCNIP_HOME" 2>/dev/null || true)"
assert_not_contains "$home_after_l2" "GENERATED:INDEX:START" "FR-017a: inject-if-missing must NOT fire when INDEX alone is absent"
set_test "the sibling gated spec-MOC is untouched after the partial-home fail-safe"
assert_eq "$spec_before_l2" "$(shasum "$copy_l2/$RMOCNIP_SPEC1" | awk '{print $1}')" "FR-017a: partial-home fail-safe aborts the batch before any write"
set_test "the partial FR-017a error message names the offending home note on stderr"
assert_contains "$l2err" "partial-roadmap-MOC.md" "FR-017a: stderr must name the malformed partial home note"
set_test "partial FR-017a --check also fails safe (exit 2, read-only error path)"
rc_l2c=0; "$GEN" --check "$RMOCNIP_ROOT" >/dev/null 2>&1 || rc_l2c=$?
assert_eq "2" "$rc_l2c" "FR-017a: --check on a partial malformed home note is exit 2"

# ───────────────────────────────────────────────────────────────────────────
section "(l3) FR-017a — a gated home note with INDEX plus PRS/BACKLINKS fails safe"
# ───────────────────────────────────────────────────────────────────────────
# roadmap-moc-extra-zones/ has a version-gated home note with its required INDEX
# pair plus unsupported PRS/BACKLINKS pairs. Home notes are INDEX-only surfaces;
# rendering PRS/BACKLINKS against docs/ai/specs/ would fabricate unrelated links.
copy_l3="$(fresh_copy "$RMOCEZ_ROOT")"
home_before_l3="$(shasum "$copy_l3/$RMOCEZ_HOME" | awk '{print $1}')"
spec_before_l3="$(shasum "$copy_l3/$RMOCEZ_SPEC1" | awk '{print $1}')"
set_test "write run over a gated home note with INDEX plus PRS/BACKLINKS -> exit 2"
rc_l3=0; l3err="$("$GEN" "$copy_l3" 2>&1 >/dev/null)" || rc_l3=$?
assert_eq "2" "$rc_l3" "FR-017a: home notes must fail safe when unsupported PRS/BACKLINKS zones are present"
set_test "the extra-zones malformed home note is left wholly unmodified"
assert_eq "$home_before_l3" "$(shasum "$copy_l3/$RMOCEZ_HOME" | awk '{print $1}')" "FR-017a: no write on extra-zone home-note fail-safe path"
set_test "the sibling gated spec-MOC is untouched after the extra-zone fail-safe"
assert_eq "$spec_before_l3" "$(shasum "$copy_l3/$RMOCEZ_SPEC1" | awk '{print $1}')" "FR-017a: extra-zone fail-safe aborts the batch before any write"
set_test "the extra-zone FR-017a error message names the offending home note on stderr"
assert_contains "$l3err" "extra-zones-roadmap-MOC.md" "FR-017a: stderr must name the malformed extra-zone home note"
set_test "extra-zone FR-017a --check also fails safe (exit 2, read-only error path)"
rc_l3c=0; "$GEN" --check "$RMOCEZ_ROOT" >/dev/null 2>&1 || rc_l3c=$?
assert_eq "2" "$rc_l3c" "FR-017a: --check on an extra-zone malformed home note is exit 2"

test_summary
