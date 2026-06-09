# Phase 0 Research: Atomicity-test router (PRSG-007)

All decisions below are resolved from the finalized spec (clarified through Clarify) and
the project constitution. **No `NEEDS CLARIFICATION` markers remain.** Each entry follows
Decision / Rationale / Alternatives considered.

---

## D1 — CLI shape and exit-status contract

**Decision**: Single positional CLI: `atomicity-route.sh <feature-dir>`, where
`<feature-dir>` holds `tasks.md` / `plan.md` / `spec.md`. Emit one JSON object to stdout.
Exit `0` on any completed classification (including `out-of-scope`); exit `2` on usage
error or an unreadable/absent feature directory, emitting `{"error": <string>}`. Never
exit `1` (no "blocked"/threshold outcome — the classifier is advisory-only, FR-012).

**Rationale**: Mirrors the existing `reviewability-gate.sh tasks <feature-dir>` sibling
(same script family, same `{"error":...}` error convention, same `exit 2` for
usage/unreadable input) so the autopilot calls it the same way. FR-011/FR-012 forbid a
blocking exit code, which is why `1` is unused here even though the gate uses `1` for its
block path.

**Alternatives considered**: (a) Three explicit path args (`tasks plan spec`) — rejected:
heavier interface, diverges from the gate's `<feature-dir>` convention. (b) Reusing the
gate's `tasks` sub-mode — rejected by FR-015 (no internal call to / edit of the gate).

---

## D2 — JSON output contract (FR-011a / FR-011b)

**Decision**: One flat-top-level JSON object on success with keys: `route` (string, one of
the five-value enum), `releasable` (boolean), `signals` (array of strings — decisive
detector findings), `hints` (array of strings — advisory-probe output), `warnings` (array
of strings — canonical CI-green sentences). The error path emits a top-level
`{"error": <string>}` with **no** `route`. The `route` enum and field names are a STABLE
CONTRACT for PRSG-008. The full schema is captured in `contracts/routing-decision.schema.json`.

**Rationale**: FR-011a fixes the field set and names; FR-011b fixes the controlled
`signals[]` vocabulary. Flat top-level string-array shape follows the established
`reviewability-gate.sh` conventions (the gate emits flat top-level keys + string arrays).
Keeping `signals` (decisive) distinct from `hints` (advisory) is mandated by FR-010/FR-011b
so PRSG-008 can trust `signals[]` as decisive without filtering advisory noise.

**Alternatives considered**: A nested `{decision:{...}}` envelope or a separate
`change_class` field — both rejected: the spec's Out of Scope explicitly forbids a separate
`change_class` field (it is recoverable from `route` + `signals`), and nesting diverges from
the gate's flat convention.

---

## D3 — Precedence / detector order (FR-003)

**Decision**: Total, ordered precedence:
1. **Input shape first** — missing or empty `tasks.md` → emit `out-of-scope` and STOP
   before any detector runs (including the hard-atomic override).
2. **Hard-atomic override** — any hard-atomic signature → `single-atomic-PR`, overriding
   any split signal.
3. **Proven additive multi-seam** → `split-PR`.
4. **Otherwise abstain** → `one-navigable-PR`.

The five detectors run in the FR-003 order: (1) `tasks.md` shape, (2) additive-vs-modify,
(3) flag-system probe, (4) release cadence, (5) consumer locality. Releasability
(`releasable` + `warnings[]`) is computed INDEPENDENTLY of the route (FR-008): a
`single-atomic-PR` destructive migration is both single-atomic AND not releasable.

**Rationale**: Directly encodes FR-003 and the spec's "Conflicting signals / precedence"
edge case. Input-shape-first guarantees an empty feature dir never spuriously trips the
hard-atomic grep. Over-inclusive tuning means a false positive only refuses a split (the
safe direction); a false negative is the dangerous one (FR-007, FR-008).

**Alternatives considered**: Running the hard-atomic grep before the empty-tasks check —
rejected by FR-003 (input shape must short-circuit first).

---

## D4 — FR-007a detection hygiene (LOAD-BEARING)

**Decision**: The keyword-based conceptual classes that have **no path signal** —
exported-symbol rename, global version pin, and auth/payment/mutual-exclusion primitive —
MUST:
- (a) match on **word boundaries or a structural task-/story-line shape**, NOT bare
  substrings. Concretely, short collision-prone stems use `grep -E` with `\b`/`[^a-z]`
  guards so `lock` never fires on "block", `acl` never fires on "oracle", etc.
- (b) read these keyword classes from **`tasks.md` + `plan.md` ONLY** (the work
  description), NOT from `spec.md` (which may merely enumerate the class names as
  vocabulary).

The path-signalled classes — `destructive-migration` and the additive-vs-modify reading —
continue to read all three artifacts (`tasks.md` + `plan.md` + `spec.md`), because their
signal is a file path / SQL verb, not a definitional keyword.

**Two distinct failure modes the keyword detectors MUST survive** (this distinction is
load-bearing for the self-check):
- **Substring collision** (e.g. `lock`→"block", `acl`→"oracle", `cas`→"because"): solved by
  the word-boundary guards in (a) / D5.
- **Whole-word vocabulary collision** (the harder one): PRSG-007's OWN `tasks.md`/`plan.md`
  legitimately contain the trigger words *as whole words in matchable positions* — the work
  IS building detectors named after these classes, so phrases like "the rename detector",
  the fixture dir `hard-atomic-rename`, "exported-symbol rename", "mutual-exclusion /
  locking", and "auth / payment" appear. A naive `\brename\b` matcher fires inside
  `hard-atomic-rename` (the `-` is a word boundary) and would yield a spurious
  `single-atomic-PR` — failing the mandated self-check. Word boundaries alone do NOT save
  this case.

**Resolution — match a described ACTION/INTENT, not a topic mention.** The keyword
detectors MUST fire only on a *described action being performed by the change* — "rename
exported symbol `foo` → `bar`", an actual version/runtime bump being made, an auth /
mutual-exclusion primitive being introduced — NOT on a topic being discussed. PRSG-007
*renames nothing, pins no version, introduces no auth primitive*; it only discusses those
classes. The detector patterns therefore key on action-shaped phrasing (a rename arrow /
"rename … to …", "bump … to vN", "introduce/add … lock/mutex/auth") rather than the bare
class noun, and read from `tasks.md` + `plan.md` only (b). Contrast the path-signalled
classes: `destructive-migration` is safe *structurally* — it requires a
`surface_for_path` → `schema/migration` path (a `.sql`/migration file), and PRSG-007 has no
such file, so it cannot fire regardless of prose. That structural safety is exactly why the
path-signalled classes read all three artifacts while the keyword classes must use the
narrower action-intent + `tasks.md`+`plan.md`-only discipline.

**Implement-phase coupling (inherited constraint):** the dogfood self-check holds only if
EITHER (i) the keyword detectors use tight action-intent patterns as above, OR (ii)
PRSG-007's own `tasks.md` (authored in the Tasks phase) describes the work without leaving
bare hard-atomic trigger tokens in matchable action positions. The implement/test phase
MUST verify the self-check empirically (run the classifier on `specs/prsg-007-atomicity-router/`
and assert the route is NOT `single-atomic-PR`) — see D10. This is the single property most
likely to bite at implement time.

**Rationale**: FR-007a is explicit that the self-check (classifier on PRSG-007's own dir →
NOT `single-atomic-PR`) is the property the hygiene rules exist to guarantee. The
action-intent discipline plus the `tasks.md`+`plan.md`-only read (not `spec.md`, which
enumerates the class names as vocabulary) is what makes it hold.

**Alternatives considered**: Reading all three artifacts for every class (simpler) —
rejected: it breaks the dogfood self-check and the spec forbids it. Bare-substring
`grep -i` (simpler) — rejected by FR-007a(a). Word-boundary matching on the bare class
noun (e.g. `\brename\b`) — rejected: it survives substring collisions but NOT the whole-word
vocabulary collision in PRSG-007's own artifacts (the failure mode above).

---

## D5 — Expanded keyword sets per change class (from consensus)

**Decision**: Use these grep keyword sets, applying word-boundary discipline to short
collision-prone stems (D4):
- **destructive-migration** (releasability + hard-atomic): the migration SQL verbs
  (`DROP`, `TRUNCATE`, `DELETE`, `ALTER TABLE`) plus `purge`, `backfill`, `irreversible`,
  `data-migration`, `rewrite`.
- **concurrency** (releasability): `deadlock`, `mutex`, `semaphore`, `data-race`,
  `isolation`, `CAS`.
- **auth/payment/mutual-exclusion** (hard-atomic, ONE coarse class): `mutex`, `semaphore`,
  `password`, `mfa`, `otp`, `saml`, `oauth`, `rbac`, `acl`, `secret`, `kms`, `nonce`,
  `idempotency`, `refund`, `payout`, `settlement`, `chargeback`, plus auth/payment/lock/
  leader-election intent words.

Short stems (`acl`, `cas`, `otp`, `kms`, `mfa`, `lock`, `mutex`) get `\b`/`[^a-z0-9]`
boundary guards so they do not fire inside larger words.

**Rationale**: These expanded sets come directly from the consensus decisions captured in
the spec (FR-007/FR-008 token lists + the over-inclusive tuning intent). Over-inclusive on
purpose: a false positive only refuses a split; a false negative risks an unsafe split or
an "CI-green" release of an unreleasable change.

**Alternatives considered**: Minimal keyword sets matching only the FR token names —
rejected: under-inclusive, and the spec mandates over-inclusive tuning in the safe
direction.

---

## D6 — Stack-agnostic detection: DUPLICATE two matchers (FR-014 / FR-015)

**Decision**: For the path-signalled surfaces (migration / API contract), DUPLICATE the
two matchers the router actually needs from `reviewability-gate.sh`:
- `surface_for_path()` (maps a path to `schema/migration`, `API`, etc.), and
- `is_excluded_generated()` (skips lockfiles / generated / vendored paths).

The duplicated block carries a `# KEEP IN SYNC with reviewability-gate.sh` comment marker
(the repo's established anti-drift convention, already used between the gate and
`estimate-reviewable-loc.sh`). The router makes **no** internal call to the gate and does
**not** edit it. For conceptual classes with no path signal (rename, version pin,
auth/payment, concurrency), use over-inclusive natural-language intent-greps (D4/D5).

**Note on `is_production_file`**: the verbatim workflow prompt mentioned duplicating
"`surface_for_path` / `is_production_file`," but spec FR-014 and FR-015 name
`surface_for_path` / **`is_excluded_generated`**. `is_production_file` exists in the gate
only to feed its LOC/production-file budget; this classifier computes NO LOC/sizing metric
(FR-002), so `is_production_file` would have no caller and would be dead code (constitution
VI / YAGNI). Decision: duplicate `surface_for_path` + `is_excluded_generated`; treat the
prompt's `is_production_file` as a transcription slip.

**Rationale**: FR-014 mandates exactly this dual mechanism (duplicated path matchers +
intent-greps) and the `KEEP IN SYNC` marker; FR-015 forbids a shared lib or any gate
call/edit. Constitution VI prefers "three similar lines" to a premature abstraction, so
duplication is the sanctioned choice here.

**Alternatives considered**: (a) Extract a shared `lib/surface-taxonomy.sh` used by both —
rejected by FR-015 (no shared-library extraction) and the no-edit-to-the-gate rule. (b)
`source` the gate and call its functions — rejected by FR-015 (no internal call).

---

## D7 — Splittability is structural seams, not LOC (FR-002 / FR-004)

**Decision**: The `tasks.md`-shape detector counts **independent additive capabilities /
surfaces** (structural seams) by reading `tasks.md` structure (task groupings / distinct
additive surfaces). Multiple independent additive seams + additive-dominant reading →
`split-PR`. A single indivisible additive capability → a single-PR-style route. NO
LOC/sizing metric is computed or consulted anywhere in the script.

**Rationale**: FR-002 forbids any LOC/sizing reliance; FR-004 requires a full `tasks.md`-
shape detector; SC-002 requires that a large-but-single-seam change is NOT routed to
`split-PR`. The autopilot separately combines this route with `reviewability-gate.sh`
sizing to decide whether to ACT on a split — that combination is the autopilot's job, not
the classifier's (FR-015, spec Assumptions).

**Alternatives considered**: Using the gate's `loc × 40` heuristic to gate the split —
rejected: that is a sizing metric, forbidden by FR-002.

---

## D8 — `branch-by-abstraction` is RESERVED, never emitted in the MVP (FR-001 / SC-008)

**Decision**: `branch-by-abstraction` stays in the JSON enum (a stable contract value for
PRSG-008) but the MVP's fully-implemented detectors MUST NEVER emit it. A modify-heavy,
non-hard-atomic change (modify signals present, no hard-atomic signature, no proven
additive seams) abstains to `one-navigable-PR`. One Layer-4 fixture (`modify-heavy/`)
asserts the route is `one-navigable-PR`, `releasable: true`, no CI-green warning.

**Rationale**: `branch-by-abstraction`'s trigger (in-place modification with ALL consumers
in-tree) needs a DECISIVE consumer-locality determination, which FR-010 keeps advisory-only
in this spec. FR-001 explicitly reserves (does not drop) the value; deepening the
consumer-locality probe to decisive — and thus making the route emittable — is owned by
PRSG-010 US3. SC-008 mandates the negative test.

**Alternatives considered**: Dropping the value from the enum — rejected: FR-001 keeps it
reserved so the PRSG-008 contract enum stays stable. Emitting it heuristically now —
rejected: FR-010 keeps the probe advisory-only, and an over-eager emission is unsafe.

---

## D9 — Recording is the SKILL's job, not the script's (FR-011 / FR-013)

**Decision**: The script writes NO files (read-only, FR-011). The speckit-autopilot SKILL
runs the script after the Tasks phase / gate G5 and records the emitted JSON into the
workflow file's `## Atomicity Route` section (FR-013). Documentation parity: document the
post-Tasks router step in `speckit-autopilot/SKILL.md` + `references/phase-execution.md`
AND mirror the prose into `codex-skills/speckit-autopilot/SKILL.md`. The script is SHARED
(single `scripts/` dir); only prose is mirrored. `validate-codex-skills.sh` (L1) must stay
green.

**Rationale**: FR-011 (read-only) and FR-013 (SKILL records, not the classifier) are
explicit. The Codex mirror is required because the autopilot ships both a Claude Code skill
and a Codex skill; the script is shared but the prose lives in two SKILL.md files.
`phase-execution.md` is the right references home because it already documents the per-phase
gate flow that G5 belongs to (vs. `gate-validation.md`, which documents gate mechanics).

**Alternatives considered**: Having the script write the section itself — rejected by
FR-011/FR-013. Putting the prose only in `gate-validation.md` — acceptable but
`phase-execution.md` is the closer fit; either satisfies FR-013/Q13.

---

## D10 — Test strategy: one Layer-4 fixture per change class + dogfood self-check (SC-007 / FR-007a)

**Decision**: `test-atomicity-route.sh` (Layer 4, using `tests/speckit-pro/lib/assertions.sh`)
exercises one fixture directory per change class (additive-multi-seam, single-additive-seam,
each hard-atomic class, concurrency, modify-heavy, out-of-scope-empty), asserting the
expected `route` and `releasable`/`warnings` reading for each. It ADDITIONALLY runs the
classifier against PRSG-007's OWN feature dir (`specs/prsg-007-atomicity-router/`) and
asserts the route is NOT `single-atomic-PR` (the mandated dogfood self-check from FR-007a).
The error path (missing/unreadable dir) is asserted to exit 2 with `{"error":...}`.

**Rationale**: SC-007 requires one fixture per change class confirming route +
releasability; SC-008 requires the `modify-heavy → one-navigable-PR` negative test; FR-007a
mandates the dogfood self-check. Following the existing `test-reviewability-gate.sh` pattern
keeps the test idiomatic and Layer-1/Layer-4 green.

**Alternatives considered**: A single mega-fixture with all classes — rejected: SC-007 says
one fixture per class, and per-class fixtures give clearer failure attribution.
