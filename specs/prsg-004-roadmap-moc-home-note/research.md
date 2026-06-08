# Phase 0 Research: Roadmap-MOC home note + render_index activation

All open "how" details from the design concept and Clarify are resolved here. No
`NEEDS CLARIFICATION` markers remain in the Technical Context.

---

## Decision 1 — render_index activation is context-scoped, and the signal originates at discovery

**Decision**: Activate the dormant `render_index()` so it emits repo-wide INDEX rows **only
when the target is the roadmap-MOC home note**, and continues to render empty for every
spec-MOC. The "is this the home note?" signal is **originated in `main()` at discovery time**
(the `specs/` scan vs the `docs/ai/specs/*-roadmap-MOC.md` glob already disambiguates the
target) and **threaded as an explicit, defaulted parameter** down to `render_index` — never
re-derived later by sniffing the file path or name.

**Why this is correct (and why FR-018 demands it)**: `render_index()` is **not** truly
dormant at the call graph level — it is already invoked today. Trace it:

- Every spec-MOC carries the `GENERATED:INDEX:START/END` pair (PRSG-003 sentinel-grammar
  worked example, `specs/prsg-003-spec-index/contracts/sentinel-grammar.md` lines 61-62).
- In `rebuild_map` (generate-spec-index.sh line 341), `if [ "$st_index" = present ]; then
  idx_body="$(render_index "$spec_dir")"; fi`. Because the INDEX pair is present on every
  spec-MOC, `render_index` runs for every spec-MOC on every regeneration — it just returns
  the empty body today (lines 121-123), so the rendered zone is link-free.

Therefore a naive "give render_index a real body" would immediately start emitting rows into
**every spec-MOC's** INDEX zone — breaking the PRSG-003 byte-for-byte contracts (FR-018 /
SC-005). The activation MUST branch on target type. The cleanest, least-fragile branch keys
on a signal that is **unambiguous exactly once** — at discovery in `main()` — rather than
re-inferring target type deep in the renderer.

**Mechanism**: the signal threads through TWO call frames —
`main() → rebuild_map → render_index` — because `render_index` is called by `rebuild_map`,
which is called by `main()`. **Both** signatures gain a parameter defaulting to `0`:
`rebuild_map` gains a 4th arg (`local is_home="${4:-0}"`) and `render_index` gains a 2nd
(`local is_home="${2:-0}"`). The home-note signal originates in `main()` at discovery (it
knows the target came from the `docs/ai/specs/*-roadmap-MOC.md` glob, not the `specs/` scan)
and is passed as `is_home=1` only on the home-note regeneration call; `rebuild_map` forwards
it to `render_index`. When `is_home=0` (the spec-MOC call site, which passes neither extra
arg — `rebuild_map "$moc" "$d" "$branch"` stays a 3-arg call), `render_index` returns empty —
**byte-identical to today's behavior** (`idx_body=""` → the present INDEX zone renders
`START\nEND` on consecutive lines, link-free). When `is_home=1`, `render_index` renders the
repo-wide INDEX. The single invariant that makes SC-005 provable: *the spec-MOC code path's
bytes change only insofar as `render_index` gains a parameter whose default reproduces
today's empty output, and the 3-arg spec-MOC `rebuild_map` call is unchanged.* Do NOT set
`is_home` via a global or re-derive it by path-sniffing — thread it explicitly through both
frames. The PRSG-003 L4 fixtures re-run unchanged as the regression guard.

For the home-note path, `main()` must also supply a sensible `in_branch` label (e.g. the home
note's basename) for the PASS-2 status line; the `spec_dir`/`$2` arg into `rebuild_map` is
unused by the home-note render (PRS/BACKLINKS are absent, so only `render_index` runs, and it
re-scans `$SPECS_DIR` itself rather than reading `spec_dir`).

**Alternatives considered**:
- *Give render_index an unconditional real body* — rejected: emits rows into every spec-MOC
  INDEX, breaks the pinned PRSG-003 contracts (the explicit FR-018 anti-pattern).
- *Re-derive "is home note?" inside render_index by matching the file path against
  `*-roadmap-MOC.md`* — rejected: fragile (couples the renderer to the filename convention,
  duplicates the discovery logic, and would mis-fire if a spec dir were ever named to
  collide). The signal is already known at discovery; thread it, don't re-compute it.
- *A separate `render_home_index()` function* — rejected as marginally cleaner but more LOC
  and a second function to keep framing-consistent; a defaulted param on the existing function
  is the smaller, KISS change and keeps the zone-renderer family symmetric.

---

## Decision 2 — home-note discovery is a filename glob, gated, disjoint from the specs/ scan

**Decision**: `main()` discovers the home note via the filename glob
`docs/ai/specs/*-roadmap-MOC.md` (0..N matches), gates each match with the existing
`moc_is_gated` (the `structureVersion` bare-integer version gate), and processes them **in
addition to and disjoint from** the existing repo-root `specs/*/SPEC-MOC.md` scan. Discovered
home notes are appended to the SAME `in_moc` / `in_new` / `in_branch` arrays in PASS 1.

**Why**: 
- The two trees do not overlap (`docs/ai/specs/` vs repo-root `specs/`), so there is no
  double-processing and a clean no-op when zero home notes exist — consistent with the
  existing "no `specs/` directory → clean no-op" driver behavior (generate-spec-index.sh
  lines 421-425, SC-012).
- Gating on `moc_is_gated` reuses the exact mechanism the spec-MOC path already uses
  (line 456). It is **one mechanism, not a separate field** — the `structureVersion: 1`
  bare-int gate in `lib/moc-frontmatter.sh` (`moc_is_gated`, lines 80-104). An ungated /
  legacy / fenceless home note is simply skipped, never an error (total/safe reads).
- Appending to the same PASS-1/PASS-2 arrays is the **KISS win**: PASS 2's body-vs-body diff,
  the per-target atomic write (`_atomic_write`, mktemp+rename), `--check` staleness reporting,
  and the zero-byte second-run idempotence (SC-004 / FR-019) all cover the home note with
  **zero new code**. Only PASS 1's regeneration call needs to pass `is_home=1` for a
  home-note target.

**The repo-wide INDEX render (the genuinely new logic)**: when `render_index` runs for the
home note it re-scans `$SPECS_DIR` (`find … -mindepth 1 -maxdepth 1 -type d | LC_ALL=C
sort`), applies `moc_is_gated` to each `specs/<dir>/SPEC-MOC.md`, reads `spec_id` and `status`
via `moc_frontmatter_field`, orders by `moc_normalize(spec_id)` ascending (emitting the raw
`spec_id` as the link text, sorting on the normalized form), and constructs the cross-tree
relative link `../../../specs/<dir>/SPEC-MOC.md` where `<dir>` is the directory basename. The
`LC_ALL=C sort` of the directory scan keeps enumeration order from leaking across machines
(SC-009 discipline). Everything except the cross-tree link construction and the row format is
reused infrastructure.

**Alternatives considered**:
- *Discover by frontmatter type marker instead of filename glob* — rejected: no such marker
  exists in the PRSG-002 template; the filename convention (`<slug>-roadmap-MOC.md`) IS the
  agreed instance convention (design Q2), and the glob is the obvious, low-fragility default
  (design concept Open Question, resolved here).
- *Fold the home note into the existing `specs/` scan* — rejected: a roadmap-level note does
  not live under the per-feature `specs/` tree (layering mismatch, design Q2); the two scans
  must stay disjoint.

---

## Decision 3 — the prd → generator sentinel seam: the template carries the empty INDEX pair (design (b))

**Decision**: The empty `GENERATED:INDEX:START/END` sentinel pair is added to the PRSG-002
`roadmap-moc-template.md`. `speckit-prd` emits the home note **from that template** (curated
epics zone filled around the pre-existing empty INDEX pair), then invokes the generator to
fill the INDEX. `speckit-prd` does NOT prose-author the sentinel bytes.

**Why (the fork and its resolution)**: The roadmap-moc-template as shipped today carries only
frontmatter + an intro paragraph — **no** generated sentinels. So the INDEX sentinel bytes
must originate somewhere. Two designs:

- **(a)** `speckit-prd` prose-authors the `GENERATED:INDEX:START/END` lines into the emitted
  file.
- **(b)** the template gains the empty INDEX pair; prd copies the template verbatim, so the
  sentinels come along.

Discriminator run during planning: `grep -rn "roadmap-moc-template" tests/speckit-pro/`
returns **nothing** — no L1 or PRSG-002 test pins the template's content. This unblocks (b):
the template can change freely. (b) is chosen because:

1. **It makes the byte-exact sentinel framing a tested contract artifact** rather than
   fragile AI-authored prose. The sentinels must byte-match the generator's constants
   (`INDEX_START` / `INDEX_END`, generate-spec-index.sh lines 37-38) exactly, or the
   generator silently takes a wrong path and never fills the INDEX. A committed template is a
   deterministic, greppable artifact; prose in a SKILL.md is only AI-tested (L3).
2. **The template already anticipates it**: its intro literally says "The generated down-link
   index and the PRD-derived home note are owned by later specs (PRSG-003 / PRSG-004)." Adding
   the empty INDEX pair here is exactly that ownership landing.
3. **It keeps FR-002 satisfied precisely**: the template carries **only** the INDEX pair (not
   the PRS or BACKLINKS pairs). Trace through `rebuild_map`: a home note with `st_index=present,
   st_prs=absent, st_backlinks=absent` fails the inject-if-missing guard (line 347 requires
   **all three** absent), so it takes the `_rewrite_present_zones` path — fills INDEX, leaves
   PRS/BACKLINKS untouched (they are absent, so their `present` guards are false and
   `render_prs`/`render_backlinks` never run; **no `prs.json` is needed**). This is exactly the
   FR-002 behavior, achieved *through* the existing machinery — which is the justification for
   "additive, not a rewrite."

**Consequence for file operations**: `roadmap-moc-template.md` is a MODIFIED production file
(reflected in Declared File Operations).

**Residual risk (recorded for tasks/implementation)**: prd's emitted sentinels (now sourced
from the template) MUST byte-match the generator constants. The L4 fixture's home note must
carry the **exact** sentinel bytes; a contract doc pins them; and the template change must use
the same literal strings. A drift here is silent (INDEX simply never fills) — so the contract
+ L4 fixture are the guard. (Optional belt-and-suspenders for a future task: an L1 assertion
that the template's INDEX sentinel bytes equal the generator's `INDEX_START`/`INDEX_END`
constants; not required, since L4 already fails if they mismatch — the INDEX would not fill.)

**Residual risk 2 — generator REPO_ROOT when prd invokes it (recorded for tasks)**: the
generator's default `REPO_ROOT` is `PLUGIN_ROOT/..` (generate-spec-index.sh lines 102-107),
which is correct in THIS plugin-source repo but **wrong in a consumer install**, where
`speckit-pro` lives in the plugin cache (not under the consumer's repo root). So `speckit-prd`,
when it invokes the generator to fill the freshly-emitted home note's INDEX, MUST pass the
**consumer's repo root positionally** (`generate-spec-index.sh "$CONSUMER_REPO_ROOT"`), not
rely on the default. This is a prd-emit-step implementation detail; it does not change the
generator or the plan, but the task that wires the invocation must get the positional arg
right or the INDEX fills against the wrong tree (or no-ops).

**Alternatives considered**:
- *(a) prd prose-authors the sentinels* — rejected: pushes byte-exactness onto AI-authored
  prose, only L3-tested, higher silent-failure risk; offers no benefit now that the template
  is unpinned and free to change.

---

## Decision 4 — INDEX row byte format + the two determinism traps (SC-004)

**Decision**: Each INDEX row is exactly `- [<spec_id>](<rel>) · <status>` where `<rel>` is
`../../../specs/<dir>/SPEC-MOC.md`, the separator is the existing U+00B7 MIDDLE DOT framed as
**space, 0xC2 0xB7, space** (reusing the `PRS_SEP` convention, generate-spec-index.sh line 46),
and `<status>` is the raw `status` frontmatter value (possibly empty). The exact bytes —
including the empty-status case — are pinned in `contracts/roadmap-moc-index.md`.

**Trap 1 — empty-status byte form (FR-015)**: a SPEC-MOC with empty/missing `status` MUST
still produce a row (link + blank status), never dropped. The hazard is trailing whitespace:
`...) · ` with nothing after the separator leaves a trailing space on the line, which is the
classic idempotence breaker (a re-run that trims it would diff). **Resolution**: pin the exact
bytes in the contract and exercise it with a dedicated empty-status fixture spec in the L4
case. (The implementation chooses one form — emit-the-separator-then-empty, matching the
`render_prs` precedent which always emits `<sep>` between fields — and the contract + fixture
freeze whichever byte sequence is chosen so the second run is a zero-byte diff.)

**Trap 2 — separator bytes**: must be the same two bytes (`0xC2 0xB7`) the PRS renderer uses,
not an ASCII dot, so the row is consistent with `render_prs` and survives the byte-equality
diff. Reuse `PRS_SEP`.

**Why frontmatter-only**: `spec_id` and `status` both come from each SPEC-MOC's PRSG-002
frontmatter via `moc_frontmatter_field` — a pure function of committed files, no H1 parsing,
no table, no dashboard (FR-022). This preserves determinism.

---

## Decision 5 — single-roadmap / repo-wide INDEX scope (the one open scoping limitation)

**Decision**: The home-note INDEX is **repo-wide** over all gated specs under
`$SPECS_DIR`. PRSG-004 assumes a **single** roadmap per repo. If multiple
`docs/ai/specs/*-roadmap-MOC.md` home notes ever coexist, each would list **all** gated
specs (every home note gets the same repo-wide INDEX) — per-roadmap INDEX scoping is **out of
scope here and deferred to PRSG-011**.

**Why acceptable for v1**: this repo (and the target use case) has one roadmap. The glob
matching 0..N home notes is for robustness (clean no-op at 0; correct fill at 1); the N>1
multi-roadmap disambiguation is a genuine future concern, explicitly owned by PRSG-011 (which
also owns navigation backfill onto legacy roadmaps). Recording it here keeps the scope
boundary honest and gives the PR's "known gaps" section its content.

---

## Decision 6 — curated epics zone: auto-derived from phases, zero new interview questions

**Decision**: `speckit-prd` derives the curated epics zone from the technical-roadmap's
existing phase/tier grouping — one epic per phase, the phase's spec links, and a one-line
advisory "Why" placeholder per epic — as an editable scaffold. It adds **ZERO** new interview
questions (SC-002). The no-phases fallback (flat catalog) collapses to a single "Specs" epic
listing all specs + an advisory note to group them (FR-004). When the derived scaffold yields
> ~10 epics, prd prints a one-line advisory and still writes the file (FR-005 / SC-003) — the
cap is **advisory only**, never a block, never a CI lint (constitution VI; matches the v1
advisory ethos of PRSG-006/010).

**Why**: the roadmap's phase grouping IS the epic structure; re-interviewing it would
duplicate the decomposition the roadmap already produced and grow the interview against the
"authored once cheaply" goal (design Q5). The generator never touches the curated zone — it
only fills the GENERATED INDEX zone (clean separation of human-edited vs machine-regenerated).

---

## Decision 7 — Codex parity is a constraint, executed by mirroring prose only

**Decision**: The prd emit step (US1) and the coach teaching surface (US2) are mirrored into
`codex-skills/speckit-prd/SKILL.md` and `codex-skills/speckit-coach/SKILL.md`. The generator
stays a **single shared copy** referenced by path — never duplicated into `codex-skills/`
(FR-021). The new coach reference doc is authored **once** under
`skills/speckit-coach/references/`; the Codex coach mirror has no own `references/` and links
to the shared tree (`../../skills/speckit-coach/references/…`), so FR-020 needs no duplicate
doc.

**Why**: the home-note emission is post-interview file writing (runtime-agnostic), so both
prd mirrors get the identical emit step even though the Codex interview uses a free-text Q&A
loop instead of `AskUserQuestion`. The existing `validate-codex-skills.sh` (L1), the L8
parity fixtures, and the `speckit-skill-reviewer` pre-commit gate must stay green (design
concept "Codex parity" note).

---

## Resolved-here summary (maps to spec.md Open Questions / Assumptions)

| Open detail (design concept) | Resolution |
|------------------------------|------------|
| Generator home-note discovery mechanism | Filename glob `docs/ai/specs/*-roadmap-MOC.md`, `moc_is_gated`, disjoint from `specs/` scan (Decision 2) |
| render_index context-scoping | Defaulted `is_home` param threaded from `main()` discovery; spec-MOC path byte-identical (Decision 1) |
| prd → generator sentinel seam | Template carries the empty INDEX pair; prd emits from template (Decision 3) |
| INDEX row format + determinism traps | `- [id](rel) · status`, U+00B7 framing, empty-status pinned (Decision 4) |
| Multi-roadmap INDEX scope | Repo-wide; single-roadmap assumption; per-roadmap scoping → PRSG-011 (Decision 5) |
| No-phases fallback | Single "Specs" epic + advisory (Decision 6) |
| coach teaching location | New `references/roadmap-moc-guide.md`, shared by both mirrors (Decision 7) |
| Codex parity | Mirror prose; generator single-copy (Decision 7) |

**Output**: all NEEDS CLARIFICATION resolved; ready for Phase 1.
