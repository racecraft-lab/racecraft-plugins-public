# Research: Generated index/PRs/backlinks + status integration + phase-gate regen

Phase 0 output for PRSG-003. Each decision below resolves a Technical-Context
question or a design-concept-routed deferral. Zero open clarification markers
remain across the plan artifacts.

## R1 — Reuse the existing ID normalizer; do not reinvent it (FR-004)

**Decision:** Source `speckit-pro/tests/lib/moc-id-normalize.sh` and call
`moc_normalize` / `moc_id_match` for every cross-spec identifier match and sort
key. The generator computes its canonical sort key from `moc_normalize`'s
`"<namespace> <number-suffix>"` output.

**Rationale:** PRSG-002 already shipped this as the single canonical normalizer
(grammar in `specs/prsg-002-moc-templates/contracts/id-normalization-grammar.md`),
it is `set -euo pipefail`-clean, side-effect-free on source, and already has a
Layer 4 unit test (`test-moc-id-normalize.sh`). FR-004 forbids a second
normalization implementation. Constitution VI (YAGNI) forbids re-deriving it.

**Alternatives considered:**
- Inline a fresh namespace/number parse in the generator — rejected: duplicates
  load-bearing logic, two sources of truth drift, violates FR-004.
- Sort by raw directory name lexicographically — rejected: interleaves `prsg-`
  and `spec-` namespaces oddly and is not the canonical key PRSG-002 defined
  (design concept Q8).

**Implementation note:** The lints also use `moc-frontmatter.sh`
(`moc_is_gated`, `moc_frontmatter_field`). The generator reuses these too for
version-gating discovery and frontmatter reads, so version-gating is byte-for-byte
consistent with the lints (same `structureVersion >= 1` bare-integer gate).

## R2 — PRS data source: a per-spec committed JSON manifest (FR-010, FR-011, D3)

**Decision:** The PRS zone renders from
`specs/<branch>/.process/prs.json`, a committed JSON manifest:

```json
{ "schemaVersion": 1, "records": [ { "slice": "PRSG-003", "pr": 117, "merged_sha": "abc1234" } ] }
```

Parsed with `jq`. Absent file or `records: []` → empty-but-valid (link-free) PRS
zone (FR-011). Rows render as plain text, ordered by normalized `slice` then `pr`.

**Rationale:** The generator must be a pure function of committed files
(FR-003/FR-010), deterministic and offline (SC-008), and fixture-testable. A
committed JSON manifest is trivially fixture-able, `jq`-parseable (constitution VI
mandates `jq` over `sed`/`awk` for JSON), and decouples the *renderer* (PRSG-003)
from the *writer* (PRSG-009). Per-spec scoping (under the spec's own `.process/`)
keeps enumeration single-tree (R5) and means the manifest is itself a BACKLINKS
reachability entry when present.

**Alternatives considered:**
- Live `gh` API at generation time — rejected: non-deterministic, needs network +
  auth, breaks offline CI and the determinism/fixture requirement (design
  concept Q3, FR-010, SC-008).
- Parse `git log` merge commits for PR#/SHA — rejected: brittle (PR# parsing from
  squash subjects couples to commit-message conventions), and still a git call at
  generation time (design concept Q3).
- Carry the data inline in the spec-MOC body — rejected: the body is exactly what
  the generator rewrites; storing source data inside the rewritten region is
  circular and fragile.

**Schema-version note:** `schemaVersion: 1` is carried so PRSG-009 can evolve the
writer without silently breaking the PRSG-003 renderer; the renderer reads
`schemaVersion` and treats an unknown/missing version conservatively (renders the
records it understands; on a malformed file it fails safe per FR-016).

## R3 — Whole-zone replacement via sentinel splice, never `sed`-patch (FR-002)

**Decision:** Parse the target file into three parts around each zone's
fixed-string `START`/`END` lines, replace the entire inter-sentinel body with the
freshly rendered body, and re-emit. A file missing a given pair skips that one
zone (FR-009). Sentinels are matched by **full-line string equality** against the
constants, not a regex over substrings.

**Rationale:** A half-updated zone is the exact failure mode being eliminated
(FR-002, spec US1). Whole-zone replace is the only mechanism that guarantees no
stale partial content survives. Full-line equality avoids a `GENERATED:` token in
prose being mistaken for a sentinel. The approach mirrors how the PRSG-002
stale-index lint already strips/reads regions with `awk`/string matching (proven
bash-3.2-safe in this repo).

**Alternatives considered:**
- `sed -i` range substitution between markers — rejected: in-place partial edit,
  fragile to special chars in rendered content, and conceptually the patching the
  spec forbids.
- Regex sentinel match (`grep -E 'GENERATED:.*START'`) — rejected: a loose match
  risks catching documentation that mentions the sentinel format.

## R4 — Anchor + byte framing: shared by template and inject-if-missing (FR-008, FR-017, D2)

**Decision:** One `assemble_zone_block()` emits the three-zone block (order
INDEX → PRS → BACKLINKS) with exact framing: one blank line before the first
`START`, one blank line between each `END`→next-`START`, empty zones as two
consecutive sentinel lines with nothing between, file ends with the BACKLINKS
`END` + a single trailing `\n`. The template (FR-017) and the injector (FR-008)
both call this same emitter, appended at the end of the body (after the intro
paragraph).

**Rationale:** FR-008 and FR-017 require a template-born map and an
injection-migrated map to be **byte-identical** (SC-001/SC-009). The only robust
way to guarantee byte-identity across two code paths is to make them call one
emitter. The byte framing (blank-line placement, trailing newline) is the real
determinism trap — two visually identical files can differ by a trailing newline
— so it is pinned exactly and asserted by the determinism fixture.

**Alternatives considered:**
- Template hand-writes the zones; injector independently writes them — rejected:
  two code paths drift; a one-byte framing difference fails the byte-identity
  requirement silently.
- Anchor at the top of the body (after frontmatter, before intro) — rejected: the
  spec Assumption fixes the default at the end of the body after the intro
  paragraph; placing generated content after the human intro reads better and
  keeps the human-authored lead paragraph first.

## R5 — Enumeration bounded to the spec's own tree; canonical ordering (FR-005, FR-018, D2)

**Decision:** BACKLINKS enumerates only `specs/<branch>/**` (including its
`.process/`), never another tree (FR-018). Within a spec, order by fixed artifact
precedence — `spec.md` → `plan.md` → `tasks.md` → `data-model.*` → `research.*`
→ `contracts/**` → `checklists/**` → `.process/**` — then lexicographic path
inside each precedence bucket. Cross-spec lists (INDEX) order by `moc_normalize`
key ascending.

**Rationale:** Single-tree enumeration keeps relative links short/stable and
avoids cross-tree ID matching (design concept Q11). Fixed precedence + lexicographic
tie-break is deterministic and independent of `find`/glob enumeration order
(SC-009), and is human-sensible (canonical artifacts first). Enumeration uses a
sorted file list (e.g. `find … | LC_ALL=C sort`) so machine locale/enumeration
order cannot perturb output.

**Alternatives considered:**
- Include the roadmap-level `docs/ai/specs/.process/` design-concept + workflow —
  rejected: that exhaust is roadmap-scoped and owned by the roadmap-MOC / PRSG-004
  (design concept Q11); pulling it in couples the generator to a second tree.
- Pure lexicographic over all paths — rejected: buries canonical artifacts among
  alphabetical noise (design concept Q8).
- Order by frontmatter `rank` — rejected: `rank` is unenforced/empty in v1, so
  ordering would be undefined (design concept Q8).

## R6 — Three-outcome result contract: current / stale / error (FR-012, FR-015, FR-016)

**Decision:** The generator exposes a distinguishable result for each of the
three outcomes via **exit code**, mirroring the PRSG-002 lints' proven 3-way enum:
`0` = current/clean (write mode wrote or `--check` found no drift), `1` = stale
(`--check` found a non-empty diff against committed), `2` = error
(malformed/unreadable target or operational failure) on stderr. `--check` writes
nothing on any path including error (FR-012). `speckit-status` maps exit 1 →
"index stale — run regen"; the autopilot maps a non-empty write-mode diff → fold
into the checkpoint commit.

**Rationale:** Reusing the PRSG-002 lints' 3-way exit enum (documented in those
scripts as FR-020/FR-024) gives `speckit-status` and the autopilot an unambiguous,
already-battle-tested contract (FR-015). Separating stale (1) from error (2) means
a malformed file never reads as "stale" and never as "clean." `set -E` + an ERR
trap → exit 2 is the same internal-error discipline the lints use.

**Alternatives considered:**
- Single boolean exit (0/nonzero) — rejected: cannot distinguish stale from error,
  so `speckit-status` could report "stale" on a genuinely broken file (FR-015).
- Parse stdout strings for the outcome — rejected: brittle; exit codes are the
  stable machine contract the two consumers need.

## R7 — Single shared script + Codex parity at the L1 structural bar (FR-020, SC-010, D-parity)

**Decision:** `generate-spec-index.sh` is ONE copy at
`speckit-pro/skills/speckit-autopilot/scripts/`, referenced by absolute plugin
path from `speckit-status`, `speckit-autopilot`, and their Codex mirrors — never
duplicated into `codex-skills/`. The behavior-description changes to
`speckit-status/SKILL.md` and `speckit-autopilot/SKILL.md` are mirrored into
`codex-skills/{speckit-status,speckit-autopilot}/SKILL.md` in Codex-native framing.
Parity is verified by the **L1** structural checks
(`validate-codex-skills.sh` + `validate-codex-parity.sh`) — NOT an L8 fixture.

**Rationale:** Co-locating with `reviewability-gate.sh` (already referenced
cross-skill by absolute path) matches the autopilot's ownership of the write path
(design concept Q9). One script means there is no second execution path to compare,
so the teams-vs-subagents L8 parity harness does not apply (spec Assumptions,
settled in Clarify). The L1 bar is concrete and enforced today:
`validate-codex-skills.sh` forbids Claude-only frontmatter keys
(`user-invocable`, `disable-model-invocation`, `license`, `argument-hint`),
requires `name:`/`description:` and a 500–8000-word body and an
`agents/openai.yaml` sidecar with the right `allow_implicit_invocation` policy
(`speckit-status` read-only → `true`; `speckit-autopilot` mutating → `false`);
`validate-codex-parity.sh` enforces CC↔Codex skill coverage 1:1.

**Alternatives considered:**
- Duplicate the script into `codex-skills/` — rejected: two copies drift; FR-020
  mandates a single shared implementation referenced by path.
- Build an L8 parity fixture for this spec — rejected: L8 compares two *execution*
  paths (Agent Teams vs parallel subagents); there is only one shared script here,
  so there is nothing to compare (spec Assumptions; the roadmap's parity-harness
  entry for this spec does not apply and is deferred to the multi-path spec).

## R8 — Fixed regen commit subject against the checkpoint-commit convention (FR-014, SC-005, D4)

**Decision:** When the phase-boundary rebuild is the only staged change, the
autopilot commits `docs(speckit-pro): regenerate spec-MOC navigation zones`. When
the rebuild rides alongside other staged phase work, it folds into that phase's
existing checkpoint commit (`feat(SPEC-XXX): complete <phase> phase`) with no
separate commit.

**Rationale:** FR-014 says "folded into its existing checkpoint commit" and SC-005
says "exactly one rebuild contribution to the checkpoint commit" — so the common
case is no standalone commit. The standalone subject (for the rare boundary where
only the regen changed) is `docs(...)` because regenerating generated doc zones is
a docs change; it reads cleanly as a public squash subject (CLAUDE.md PR-title
rules), carries no internal IDs, and `docs:` does not trip a release-please version
bump (the zones are not a shipped feature). The existing checkpoint subjects use
`feat(SPEC-XXX): … phase`, so this wording sits cleanly beside them.

**Alternatives considered:**
- `chore(speckit-pro): …` — viable, but `docs:` is the more accurate scope for
  regenerated documentation zones and equally release-neutral.
- A `feat:` subject — rejected: would imply a shipped feature and could trigger a
  minor version bump for a pure doc regeneration.
- Compute the subject per-run from the changed spec list — rejected: non-deterministic
  subject text, harder to review, and the spec wants a *fixed* message.
