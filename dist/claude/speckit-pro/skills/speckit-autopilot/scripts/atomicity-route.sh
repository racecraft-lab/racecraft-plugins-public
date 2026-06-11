#!/usr/bin/env bash
# atomicity-route.sh — Read-only atomicity classifier for PR-Size Governance (PRSG-007).
#
# Given a feature directory holding tasks.md/plan.md/spec.md, emit ONE machine-readable
# routing decision (a single flat JSON object) to stdout. It changes nothing and blocks
# nothing — it classifies (`route`), flags release risk (`releasable`), and emits a
# controlled `signals[]` vocabulary, advisory `hints[]`, and canonical `warnings[]`.
# The speckit-autopilot SKILL (not this script) records the decision into the workflow
# file's "## Atomicity Route" section after the Tasks phase / gate G5 (FR-013).
#
# Usage:
#   atomicity-route.sh <feature-dir>
#
# Exit:
#   0 = any completed classification (including out-of-scope) — NEVER blocks (FR-012)
#   2 = usage error, or unreadable/absent feature dir, or a present-but-unreadable
#       tasks.md/plan.md/spec.md (FR-011a error path)
#
# JSON contract (FR-011a, contracts/routing-decision.schema.json):
#   success = flat top-level {route, releasable, signals[], hints[], warnings[]}
#   error   = {"error": <string>} only, exit 2  (no route key)
# Both objects are built with jq (never string concat).

set -euo pipefail

# ---------------------------------------------------------------------------
# Decision state (globals). Detectors in later phases set these flags; the
# routing dispatch and the emitter read them. Defaults encode the abstain
# floor (FR-006): no decisive signal → one-navigable-PR, releasable, no tokens.
# ---------------------------------------------------------------------------
ROUTE="one-navigable-PR"
RELEASABLE=true
SIGNALS=()
HINTS=()
WARNINGS=()

# ---------------------------------------------------------------------------
# Canonical CI-green warning sentences (data-model.md Entity 3) — the ONLY two
# strings permitted in warnings[]. Defined here so the releasability pass
# (added by a later task) appends them verbatim.
# ---------------------------------------------------------------------------
WARN_DESTRUCTIVE_MIGRATION="destructive migration: a passing CI run does not prove this change is releasable (CI-green ≠ releasable)"
WARN_CONCURRENCY="concurrency-sensitive change: a passing CI run does not prove this change is releasable (CI-green ≠ releasable)"

# ---------------------------------------------------------------------------
# JSON helpers (FR-011a). Build with jq, never string concat.
# ---------------------------------------------------------------------------

# json_array — turn a bash array passed on stdin (one element per line) into a
# JSON string array, rendering an empty array as [] (not [""]). The `:-` guard
# at the call site keeps `set -u` happy for empty arrays.
json_array() {
  sed '/^$/d' | jq -R . | jq -s .
}

corpus_without_code_fences() {
  local file
  for file in "$@"; do
    [ -r "$file" ] || continue
    awk '
      /^[[:space:]]*```/ { fence = !fence; next }
      !fence { print }
    ' "$file"
  done
}

# emit_error <message> — print the error object and exit 2 (FR-011a, FR-012).
# No route key is present on the error path.
emit_error() {
  local msg="$1"
  jq -cn --arg error "$msg" '{error: $error}'
  exit 2
}

# emit_success — print the single flat success object from the decision globals
# and exit 0 (FR-011, FR-011a, SC-001). Exit 0 on any completed classification.
emit_success() {
  local signals_json hints_json warnings_json
  signals_json=$(printf '%s\n' "${SIGNALS[@]:-}" | json_array)
  hints_json=$(printf '%s\n' "${HINTS[@]:-}" | json_array)
  warnings_json=$(printf '%s\n' "${WARNINGS[@]:-}" | json_array)

  jq -cn \
    --arg route "$ROUTE" \
    --argjson releasable "$RELEASABLE" \
    --argjson signals "$signals_json" \
    --argjson hints "$hints_json" \
    --argjson warnings "$warnings_json" \
    '{
      route: $route,
      releasable: $releasable,
      signals: $signals,
      hints: $hints,
      warnings: $warnings
    }'
  exit 0
}

# ---------------------------------------------------------------------------
# Stack-agnostic surface matchers (FR-014).
# KEEP IN SYNC with reviewability-gate.sh
# These two functions are DUPLICATED verbatim-equivalent from
# speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh per the
# mandated no-shared-lib constraint (FR-015). This script MUST NOT call or edit
# that gate. (is_production_file is intentionally NOT duplicated — it has no
# caller here; this classifier computes no LOC/sizing metric, FR-002.)
# ---------------------------------------------------------------------------
surface_for_path() {
  local path="$1"
  case "$path" in
    *.sql|*migrations*|*schema*) echo "schema/migration" ;;
    src/app/api/*|openapi.json|*contracts*) echo "API" ;;
    *.tsx|src/components/*|src/app/*|*.stories.tsx|tests/e2e/*|tests/visual/*) echo "UI" ;;
    *scheduler*|*dispatch*|*runner*|*cron*|*workflow*) echo "scheduler/runtime" ;;
    *adapter*|*harness*|*openclaw*) echo "harness/adapter" ;;
    *seed*|*.json|*.yaml|*.yml|*.toml|*.env*) echo "seed/config" ;;
    docs/*|*.md|.specify/*|specs/*) echo "docs/process" ;;
    *) echo "other" ;;
  esac
}

is_excluded_generated() {
  local path="$1"
  case "$path" in
    pnpm-lock.yaml|*/pnpm-lock.yaml|package-lock.json|*/package-lock.json|npm-shrinkwrap.json|*/npm-shrinkwrap.json|yarn.lock|*/yarn.lock|bun.lock|*/bun.lock|bun.lockb|*/bun.lockb|Cargo.lock|*/Cargo.lock|Gemfile.lock|*/Gemfile.lock|Pipfile.lock|*/Pipfile.lock|poetry.lock|*/poetry.lock|composer.lock|*/composer.lock) return 0 ;;
    *.snap|*.snapshot|__snapshots__/*|snapshots/*) return 0 ;;
    vendor/*|vendors/*|third_party/*|generated/*|dist/*|build/*) return 0 ;;
    */.process/*|.process/*) return 0 ;;
    docs/ai/workflows/*/exports/*) return 0 ;;
    *) return 1 ;;
  esac
}

# ---------------------------------------------------------------------------
# CLI front door + exit-status contract (T004, FR-011a error path, FR-012).
# ---------------------------------------------------------------------------
FEATURE_DIR="${1:-}"

[ -n "$FEATURE_DIR" ] || emit_error "Usage: atomicity-route.sh <feature-dir>"

if [ ! -d "$FEATURE_DIR" ] || [ ! -r "$FEATURE_DIR" ]; then
  emit_error "feature directory not found or unreadable: $FEATURE_DIR"
fi

TASKS="$FEATURE_DIR/tasks.md"
PLAN="$FEATURE_DIR/plan.md"
SPEC="$FEATURE_DIR/spec.md"

# A present-but-unreadable input file is a read failure (exit 2). A merely-absent
# plan.md/spec.md is tolerated (its detector degrades). tasks.md absence/emptiness
# is NOT an error — it short-circuits to out-of-scope below (FR-003).
if [ -e "$TASKS" ] && [ ! -r "$TASKS" ]; then
  emit_error "tasks file present but unreadable: $TASKS"
fi
if [ -e "$PLAN" ] && [ ! -r "$PLAN" ]; then
  emit_error "plan file present but unreadable: $PLAN"
fi
if [ -e "$SPEC" ] && [ ! -r "$SPEC" ]; then
  emit_error "spec file present but unreadable: $SPEC"
fi

# ---------------------------------------------------------------------------
# Input-shape short-circuit (T006, FR-003): a missing OR empty tasks.md means
# there is nothing in scope to classify. Route out-of-scope and stop BEFORE any
# detector or the hard-atomic override runs. (`! -s` is true for both absent and
# zero-byte files.) A missing/empty tasks.md is NOT an error.
# ---------------------------------------------------------------------------
if [ ! -s "$TASKS" ]; then
  ROUTE="out-of-scope"
  RELEASABLE=true
  emit_success
fi

# ---------------------------------------------------------------------------
# Detector pipeline (FR-003 order). The spine is flag-driven so precedence is
# structural, not execution-order-dependent: detectors only SET flags; the
# routing dispatch below resolves precedence. Later tasks fill these in.
#
#   1. tasks.md shape           (T011) → MULTI_SEAM
#   2. additive-vs-modify       (T012) → ADDITIVE_DOMINANT / MODIFY_HEAVY
#   3. flag-system probe        (T015) → HINTS only (advisory, FR-010)
#   4. release-cadence probe    (T015) → HINTS only (advisory, FR-010)
#   5. consumer-locality probe  (T015) → HINTS only (advisory, FR-010)
#   hard-atomic detectors       (T019, T020) → HARD_ATOMIC + hard-atomic:* token
#   releasability pass          (T022) → RELEASABLE=false + releasability:* + warning
# ---------------------------------------------------------------------------

# US1 detector flags (set by the detectors, read by the routing dispatch).
MULTI_SEAM=false
ADDITIVE_DOMINANT=false
MODIFY_HEAVY=false

# <<< DETECTOR INSERTION POINT (US1: tasks-shape, additive-vs-modify, advisory probes) >>>

# --- Detector 1: tasks.md shape (T011, FR-002/FR-004) -----------------------
# Count STRUCTURAL SEAMS = the number of DISTINCT production surfaces the work
# touches, read from each task line's named deliverable path and bucketed with
# the DUPLICATED surface_for_path matcher (FR-014). This is a structural count,
# NOT a LOC/sizing metric (FR-002): two independent additive surfaces are two
# seams whether each is 5 lines or 500. Docs/process and seed/config buckets are
# not production seams, so they do not count toward splittability. ≥2 distinct
# production surfaces ⇒ MULTI_SEAM. (The split branch is additionally gated on
# additive-dominance below, so this count only decides split for already-additive
# changes — FR-005, data-model Entity 4 "proven additive multi-seam".)
if [ -s "$TASKS" ]; then
  # Pull backtick-quoted path-like tokens from task lines AND their indented
  # continuation lines (SpecKit task descriptions wrap, and the named deliverable
  # path frequently lands on the continuation line); bucket each via the
  # duplicated surface_for_path matcher; count DISTINCT production surfaces. The
  # trailing `|| true` is REQUIRED: under `set -o pipefail` a mid-pipe grep that
  # finds no production surface exits non-zero and would otherwise trip `set -e`
  # on a legitimately single-/zero-seam change (the abstain floor).
  seam_lines=$(awk '
    /^[[:space:]]*-[[:space:]]*\[[ xX]?\][[:space:]]*T[0-9]/ { intask=1; print; next }
    intask && /^[[:space:]]+[^[:space:]]/ { print; next }
    { intask=0 }
  ' "$TASKS" 2>/dev/null || true)
  seam_surfaces=$(
    printf '%s\n' "$seam_lines" \
      | grep -oE '`[^`]+`' \
      | tr -d '`' \
      | grep -E '/|\.[A-Za-z0-9]+$' \
      | while IFS= read -r tok; do
          is_excluded_generated "$tok" && continue
          surface_for_path "$tok"
        done \
      | grep -E '^(schema/migration|API|UI|scheduler/runtime|harness/adapter)$' \
      | sort -u | wc -l | tr -d ' '
  ) || true
  if [ "${seam_surfaces:-0}" -ge 2 ]; then
    MULTI_SEAM=true
  fi
fi

# --- Detector 2: additive-vs-modify (T012, FR-005) --------------------------
# Distinguish modify signals (UPDATE/DELETE/DROP/CHECK) from additive signals
# (CREATE TABLE, nullable column additions), read across all three artifacts
# (the path-signalled read, D4). ADDITIVE_DOMINANT is the strict "proven
# additive" gate for split — additive present AND NO modify signal at all — so a
# spec saturated with modify VOCABULARY (e.g. PRSG-007's own artifacts, which
# enumerate UPDATE/DELETE/DROP/CHECK as the detector's keyword list) never reads
# as additive-dominant and never reaches the split branch (dogfood, FR-007a).
# MODIFY_HEAVY = modify signals present (and not additive-dominant).
addmod_corpus=$(cat "$TASKS" ${PLAN:+"$PLAN"} ${SPEC:+"$SPEC"} 2>/dev/null || true)
additive_hits=$(printf '%s' "$addmod_corpus" | grep -ciE 'CREATE[[:space:]]+TABLE|nullable' || true)
modify_hits=$(printf '%s' "$addmod_corpus" | grep -coiE '(^|[^[:alnum:]_])(UPDATE|DELETE|DROP|CHECK)([^[:alnum:]_]|$)' || true)
if [ "${additive_hits:-0}" -gt 0 ] && [ "${modify_hits:-0}" -eq 0 ]; then
  ADDITIVE_DOMINANT=true
elif [ "${modify_hits:-0}" -gt 0 ]; then
  MODIFY_HEAVY=true
fi

# --- Contextual probe corpus (PRSG-010B, FR-017/FR-021) ---------------------
# Contextual probes read tasks.md + plan.md only. The clean corpus removes
# Markdown code fences so copy/paste snippets cannot become decisive evidence;
# the raw corpus is retained only to downgrade code-fence-only mentions into
# closed weak hints.
raw_context_corpus=$(cat "$TASKS" ${PLAN:+"$PLAN"} 2>/dev/null || true)
context_corpus=$(corpus_without_code_fences "$TASKS" ${PLAN:+"$PLAN"} 2>/dev/null || true)
context_non_fixture_corpus=$(printf '%s\n' "$context_corpus" | grep -viE '(^|/)(tests?|fixtures?)(/|$)|fixtures/' || true)

CONTEXT_FLAG_GUARDED=false
CONTEXT_RELEASE_HELD=false
CONTEXT_CONSUMER_BBA=false
CONTEXT_CONSUMER_OUT_OF_TREE=false
CONTEXT_CONFLICT=false

# <<< DETECTOR INSERTION POINT (US2: hard-atomic keyword + path detectors) >>>

# US2 hard-atomic detector flags (set here, read by the routing dispatch and the
# releasability pass). HARD_ATOMIC is the OR of the five class detectors; the route
# dispatch keys the override on it. Each class also pushes its own signals[] token.
HARD_ATOMIC=false
DM_PATH_VERB=false   # destructive-migration class (path + SQL verb) — also drives releasability
CONCURRENCY=false    # concurrency releasability class (keyword, action-shaped)

# --- Keyword corpus (FR-007a (b)): the keyword-based hard-atomic classes AND the
# concurrency releasability class read tasks.md + plan.md ONLY — NEVER spec.md,
# which may merely ENUMERATE the class names as vocabulary (this is the dogfood
# firewall, FR-007a). The path-signalled classes (destructive-migration,
# out-of-tree) read all three artifacts below, because their signal is a file
# path / SQL verb, not a definitional keyword.
kw_corpus=$(cat "$TASKS" ${PLAN:+"$PLAN"} 2>/dev/null || true)

# --- Detector A: keyword hard-atomic classes (T019, FR-007/FR-007a; D4/D5) ------
# FR-007a HYGIENE: each pattern matches a described ACTION/INTENT with a CONCRETE
# operand, NOT a bare class noun / topic mention. The discriminator is concreteness
# — a real backtick identifier, a real version digit, or a concrete object after an
# action verb — implemented as a POSITIVE requirement (not a blacklist of the "…"
# placeholder glyph). PRSG-007's own artifacts phrase these as enumerated vocabulary
# with "…" placeholders ("rename … to …", "introduce/add … lock/mutex", "bump … to
# vN"), so they carry no concrete operand and never fire (dogfood, FR-007a). Short
# stems (lock/mutex/acl/otp/kms/mfa) are word-boundary guarded so `lock` never fires
# on "block"; the `[^.…/`]` operand span additionally forbids a "…"/"/"-separated
# enumeration between the verb and the stem.
#
# PORTABILITY: word boundaries are written as POSIX bracket classes
# `(^|[^[:alnum:]_])` … `([^[:alnum:]_]|$)` — NOT `\b` — because `\b` is a GNU
# extension that is not guaranteed in POSIX ERE (some BSD/busybox greps treat it
# as a literal). Where a boundary sits next to a `{0,N}` operand gap, the leading
# boundary is folded into ONE mandatory separator char drawn from the SAME class
# the gap excludes (so it cannot re-admit a `.`/`/`/backtick the gap forbids), and
# the optional inner gap ends in a non-word char — keeping behavior identical to
# the old `\b` form on both GNU and BSD grep. Do NOT "simplify" these back to `\b`.
#
# exported-symbol rename: rename verb + a backtick identifier + "to"/arrow + a 2nd
# backtick identifier (the concrete from→to operands).
if printf '%s' "$kw_corpus" | grep -qiE '(^|[^[:alnum:]_])renam(e|ing)([^[:alnum:]_.`][^.`]{0,29})?`[^`]+`(([^.`]{0,39}[^[:alnum:]_.`])?to([^[:alnum:]_.`][^.`]{0,19})?|[^.`]{0,40}(->|→)[^.`]{0,20})`[^`]+`'; then
  HARD_ATOMIC=true
  SIGNALS+=("hard-atomic:exported-symbol-rename")
fi
# global version pin: bump/pin/upgrade verb + a real version digit (v20, 1.2.3).
if printf '%s' "$kw_corpus" | grep -qiE '(^|[^[:alnum:]_])(bump|pin|upgrade|upgrading|bumping|pinning)[^[:alnum:]_.]([^.]{0,38}[^[:alnum:]_.])?v?[0-9]+(\.[0-9]+)*([^[:alnum:]_]|$)'; then
  HARD_ATOMIC=true
  SIGNALS+=("hard-atomic:global-version-pin")
fi
# mutual-exclusion / auth / payment primitive (ONE coarse class): an action verb +
# a mutual-exclusion stem + a concrete object (no "…"/"/"-enumeration in between).
if printf '%s' "$kw_corpus" | grep -qiE '(^|[^[:alnum:]_])(introduce|introducing|add|adding|acquire|wrap|enforce|implement|implementing)[^[:alnum:]_.…/`]([^.…/`]{0,23}[^[:alnum:]_.…/`])?(distributed[ -])?(lock|mutex|auth|payment|acl|otp|kms|mfa|leader[ -]election|mutual[ -]exclusion)([^[:alnum:]_]|$)'; then
  HARD_ATOMIC=true
  SIGNALS+=("hard-atomic:mutual-exclusion-primitive")
fi

# --- Detector B: concurrency releasability class (T022 input, FR-007a/FR-008) ---
# Governed by the SAME action-intent discipline as the keyword hard-atomic classes
# (FR-007a(a)): an action verb + a concurrency-only stem + a concrete object. Read
# from tasks.md + plan.md ONLY. The concurrency stems here are DISJOINT from the
# mutual-exclusion stems above on everything but `mutex`, so a "fix a data race"
# change flags concurrency-releasability WITHOUT being mis-read as a hard-atomic
# mutual-exclusion primitive (and vice versa). This is a releasability signal, NOT a
# route signal — the route is decided by the other detectors (data-model Entity 4).
if printf '%s' "$kw_corpus" | grep -qiE '(^|[^[:alnum:]_])(fix|fixing|introduce|resolve|resolving|guard|prevent|eliminate)[^[:alnum:]_.…/`]([^.…/`]{0,23}[^[:alnum:]_.…/`])?(deadlock|mutex|semaphore|data[ -]race|race[ -]condition|isolation[ -]level|CAS|compare[ -]and[ -]swap)([^[:alnum:]_]|$)'; then
  CONCURRENCY=true
fi

# --- Detector C: path-signalled hard-atomic classes (T020, FR-007/FR-014; D5/D6) -
# These read ALL THREE artifacts (their signal is a path / SQL verb, not a keyword).
# Bucketing uses the DUPLICATED surface_for_path / is_excluded_generated matchers
# (T007) so detection stays stack-agnostic and in sync with the gate's taxonomy.
path_corpus=$(cat "$TASKS" ${PLAN:+"$PLAN"} ${SPEC:+"$SPEC"} 2>/dev/null || true)

# destructive-migration: a schema/migration DELIVERABLE path CO-LOCATED on the SAME
# line with a real destructive SQL verb (DROP/DELETE/TRUNCATE). Co-location is the
# discriminator: PRSG-007's artifacts mention migration paths AND (separately)
# destructive verbs as vocabulary, but never both on one line, so the dogfood does
# not fire. Each candidate path token is bucketed via surface_for_path (== schema/
# migration) and screened by is_excluded_generated, keeping the taxonomy shared.
while IFS= read -r line; do
  printf '%s' "$line" | grep -qiE '(^|[^[:alnum:]_])(DROP|DELETE|TRUNCATE)([^[:alnum:]_]|$)' || continue
  # any backtick path token on this line that buckets as schema/migration?
  while IFS= read -r tok; do
    [ -n "$tok" ] || continue
    is_excluded_generated "$tok" && continue
    if [ "$(surface_for_path "$tok")" = "schema/migration" ]; then
      DM_PATH_VERB=true
      break
    fi
  done < <(printf '%s\n' "$line" | grep -oE '`[^`]+`' | tr -d '`' | grep -E '/|\.[A-Za-z0-9]+$' || true)
  [ "$DM_PATH_VERB" = true ] && break
done < <(printf '%s\n' "$path_corpus")
if [ "$DM_PATH_VERB" = true ]; then
  HARD_ATOMIC=true
  SIGNALS+=("hard-atomic:destructive-migration")
fi

# out-of-tree contract break: a REAL versioned public path (/api/v<DIGIT>). The real
# digit is the discriminator — PRSG-007 mentions "/api/vN" (literal N) and bare
# webhook/MCP as vocabulary, none of which carry a real version digit, so the
# dogfood does not fire. (We deliberately do NOT fire on bare webhook/MCP keywords.)
if printf '%s' "$path_corpus" | grep -qiE '/api/v[0-9]+'; then
  HARD_ATOMIC=true
  SIGNALS+=("hard-atomic:out-of-tree-contract-break")
fi

# ---------------------------------------------------------------------------
# Contextual probes (PRSG-010B, FR-017..FR-022). These promote only deterministic
# high-confidence evidence into signals[]. Weak, code-fence-only, fixture-only,
# ambiguous, or conflicting evidence remains route-neutral closed-enum hints.
# ---------------------------------------------------------------------------

# Flag-system guarded cutover: repo-local flag/evaluation evidence + current
# guard task + current guard test task. Test/fixture-only flag mentions do not
# satisfy the repo-local mechanism or guard requirements.
flag_raw=false
flag_mechanism=false
flag_guard=false
flag_test=false
if printf '%s' "$raw_context_corpus" | grep -qiE 'feature[ -]?flag|flag[ -]?system|flag evaluation|LaunchDarkly|toggle|feature_flags|featureFlags|[A-Za-z0-9_]+Flag'; then
  flag_raw=true
fi
if printf '%s' "$context_non_fixture_corpus" | grep -qiE 'repo-local flag|feature[ -]?flag|flag[ -]?system|flag evaluation|LaunchDarkly|toggle|feature_flags|featureFlags|[A-Za-z0-9_]+Flag'; then
  flag_mechanism=true
fi
if printf '%s' "$context_non_fixture_corpus" | grep -qiE '(guard|gate|wrap|protect|behind|evaluate)[^[:cntrl:]]{0,80}(flag|toggle|LaunchDarkly|[A-Za-z0-9_]+Flag)|(flag|toggle|LaunchDarkly|[A-Za-z0-9_]+Flag)[^[:cntrl:]]{0,80}(guard|gate|wrap|protect|behind|evaluate)'; then
  flag_guard=true
fi
if printf '%s' "$context_corpus" | grep -qiE '(test|tests|fixture|assert|coverage)[^[:cntrl:]]{0,80}(flag|guard|toggle|LaunchDarkly|[A-Za-z0-9_]+Flag)|(flag|guard|toggle|LaunchDarkly|[A-Za-z0-9_]+Flag)[^[:cntrl:]]{0,80}(test|tests|fixture|assert|coverage)'; then
  flag_test=true
fi
if [ "$flag_mechanism" = true ] && [ "$flag_guard" = true ] && [ "$flag_test" = true ]; then
  CONTEXT_FLAG_GUARDED=true
  SIGNALS+=("context:flag-system:guarded-cutover")
elif [ "$flag_raw" = true ]; then
  HINTS+=("hint:flag-system:weak")
fi

# Release-held cutover: no decisive flag evidence, concrete cadence + hold +
# cutover evidence. This affects route only; it does not by itself set
# releasable=false.
release_raw=false
release_cadence=false
release_hold=false
release_cutover=false
if printf '%s' "$raw_context_corpus" | grep -qiE 'release[ -]?(cadence|train|window|held|hold)|ship[ -]?cadence|deploy[ -]?cadence|cutover'; then
  release_raw=true
fi
if printf '%s' "$context_corpus" | grep -qiE 'release[ -]?(cadence|train|window)|ship[ -]?cadence|deploy[ -]?cadence'; then
  release_cadence=true
fi
if printf '%s' "$context_corpus" | grep -qiE 'release[ -]?held|release[ -]?hold|hold[^[:cntrl:]]{0,80}release|release[^[:cntrl:]]{0,80}hold|freeze'; then
  release_hold=true
fi
if printf '%s' "$context_corpus" | grep -qiE 'cutover|switch[ -]?over|rollout'; then
  release_cutover=true
fi
if [ "$release_cadence" = true ] && [ "$release_hold" = true ] && [ "$release_cutover" = true ] && [ "$CONTEXT_FLAG_GUARDED" != true ] && [ "$flag_mechanism" != true ]; then
  CONTEXT_RELEASE_HELD=true
  SIGNALS+=("context:release-cadence:release-held-cutover")
elif [ "$release_raw" = true ]; then
  HINTS+=("hint:release-cadence:weak")
fi

# Consumer-locality: branch-by-abstraction requires all affected consumers
# proven in-tree, coexistence behind an abstraction, migration and contract work,
# and no hard-atomic or releasability risk. Proven out-of-tree consumers are
# decisive context but route-conservative. Conflicts never enter signals[].
consumer_raw=false
consumer_all_in_tree=false
consumer_out_of_tree=false
consumer_coexist=false
consumer_migration=false
consumer_contract=false
if printf '%s' "$raw_context_corpus" | grep -qiE 'consumer[ -]?locality|all affected consumers|all consumers|in[ -]?tree consumers|out[ -]?of[ -]?tree consumers|downstream consumers|outside the repo'; then
  consumer_raw=true
fi
if printf '%s' "$context_corpus" | grep -qiE 'all affected consumers (are )?in[ -]?tree|all consumers (are )?in[ -]?tree|in[ -]?tree consumers'; then
  consumer_all_in_tree=true
fi
if printf '%s' "$context_corpus" | grep -qiE 'out[ -]?of[ -]?tree consumers|outside the repo|external consumers|downstream consumers'; then
  consumer_out_of_tree=true
fi
if printf '%s' "$context_corpus" | grep -qiE 'coexist|behind an? abstraction|abstraction layer|branch[ -]?by[ -]?abstraction'; then
  consumer_coexist=true
fi
if printf '%s' "$context_corpus" | grep -qiE 'migration|migrate'; then
  consumer_migration=true
fi
if printf '%s' "$context_corpus" | grep -qiE 'contract'; then
  consumer_contract=true
fi
if [ "$consumer_all_in_tree" = true ] && [ "$consumer_out_of_tree" = true ]; then
  CONTEXT_CONFLICT=true
  HINTS+=("hint:contextual-probe:conflict")
elif [ "$consumer_all_in_tree" = true ] && [ "$consumer_coexist" = true ] && [ "$consumer_migration" = true ] && [ "$consumer_contract" = true ] && [ "$HARD_ATOMIC" != true ] && [ "$DM_PATH_VERB" != true ] && [ "$CONCURRENCY" != true ]; then
  CONTEXT_CONSUMER_BBA=true
  SIGNALS+=("context:consumer-locality:all-in-tree")
  SIGNALS+=("strategy:branch-by-abstraction")
elif [ "$consumer_out_of_tree" = true ]; then
  CONTEXT_CONSUMER_OUT_OF_TREE=true
  SIGNALS+=("context:consumer-locality:out-of-tree")
elif [ "$consumer_raw" = true ]; then
  HINTS+=("hint:consumer-locality:weak")
fi

# ---------------------------------------------------------------------------
# Routing dispatch (precedence, FR-003 / FR-007): hard-atomic override beats the
# additive split signal, which beats the abstain floor. Resolved from flags so a
# later detector cannot break precedence by reordering its own execution.
# US1 (T013) and US2 (T021) wire the branches into this dispatch.
# ---------------------------------------------------------------------------
# <<< ROUTING DISPATCH INSERTION POINT (hard-atomic → additive-multi-seam → abstain) >>>

# Routing dispatch (T013/T014 US1 + T021 US2, FR-003/FR-004/FR-005/FR-006/FR-007/
# FR-011b). ONE if/elif chain so precedence is structural, resolved from the
# detector flags (a later detector cannot break precedence by reordering its own
# execution). Precedence:
#   1. ANY hard-atomic signature → single-atomic-PR  (OVERRIDES split, FR-007/SC-003)
#   2. release-held cutover (no decisive flag)                       → single-atomic-PR
#   3. all-in-tree consumer coexistence                              → branch-by-abstraction
#   4. proven additive multi-seam (multi-seam AND additive-dominant) → split-PR
#   5. guarded cutover or modify-heavy non-hard-atomic               → one-navigable-PR
#   6. abstain (no decisive signal)                                  → one-navigable-PR (default)
# The hard-atomic branch is PREPENDED INTO this chain (not a separate preceding
# if-block) so the US1 split branch cannot re-set the route after the override.
# Each hard-atomic/context class already pushed its own signal token above; the
# dispatch sets only the route. The split branch remains above guarded cutover so
# independent additive multi-seam evidence still proves split (FR-018).
if [ "$HARD_ATOMIC" = true ]; then
  ROUTE="single-atomic-PR"
elif [ "$CONTEXT_RELEASE_HELD" = true ]; then
  ROUTE="single-atomic-PR"
elif [ "$CONTEXT_CONSUMER_BBA" = true ]; then
  ROUTE="branch-by-abstraction"
elif [ "$MULTI_SEAM" = true ] && [ "$ADDITIVE_DOMINANT" = true ]; then
  ROUTE="split-PR"
  SIGNALS+=("change-shape:additive-multi-seam")
elif [ "$CONTEXT_FLAG_GUARDED" = true ]; then
  ROUTE="one-navigable-PR"
elif [ "$MODIFY_HEAVY" = true ]; then
  ROUTE="one-navigable-PR"
  SIGNALS+=("change-shape:modify-heavy")
fi
# else: ROUTE stays the abstain floor (one-navigable-PR) with no change-shape
# token (FR-006) — set by the decision-state defaults at the top of the file.

# ---------------------------------------------------------------------------
# Releasability pass (T022, FR-008/FR-009) — computed INDEPENDENTLY of the route
# (a change MAY be single-atomic-PR AND not releasable; a destructive migration is
# both, data-model Entity 4). For each releasability-risk class: RELEASABLE=false,
# push its releasability:* token, and append its CANONICAL CI-green warning. The two
# warning strings are the verbatim constants defined at the top of the file
# (data-model Entity 3, incl. the "≠" char) — never reconstructed here. Otherwise
# RELEASABLE stays the default true with an empty warnings[] (FR-009).
# <<< RELEASABILITY INSERTION POINT (destructive-migration / concurrency) >>>
if [ "$DM_PATH_VERB" = true ]; then
  RELEASABLE=false
  SIGNALS+=("releasability:destructive-migration")
  WARNINGS+=("$WARN_DESTRUCTIVE_MIGRATION")
fi
if [ "$CONCURRENCY" = true ]; then
  RELEASABLE=false
  SIGNALS+=("releasability:concurrency")
  WARNINGS+=("$WARN_CONCURRENCY")
fi
# ---------------------------------------------------------------------------

emit_success
