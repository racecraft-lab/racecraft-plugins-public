# Implementation Plan: Generated index/PRs/backlinks + status integration + phase-gate regen

**Branch**: `prsg-003-spec-index` | **Date**: 2026-06-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/prsg-003-spec-index/spec.md`

## Summary

PRSG-002 shipped the MOC navigation layer as **static** Markdown shapes
(templates, a scaffold-time skeleton, version-gated orphan/stale-index lints).
Static Markdown has no engine, so any "generated" block silently lies the moment
the source tree moves — the #1 risk in the PR-size-governance roadmap. PRSG-003
adds the engine: a single deterministic shell generator,
`generate-spec-index.sh`, that rebuilds three independently sentinel-bounded
zones (INDEX, PRS, BACKLINKS) inside each version-marked `SPEC-MOC.md` from the
committed source tree. It reuses PRSG-002's `moc-id-normalize.sh` for every ID
join, always replaces the **whole** zone (never `sed`-patches a partial zone),
and orders deterministically. It is wired into `speckit-status` as a read-only
`--check` (regenerate in memory, diff, report staleness, write nothing) and into
`speckit-autopilot` as an idempotent phase-gate rebuild that folds into the
existing checkpoint commit only on a non-empty diff. The roadmap-level INDEX path
is built and fixture-tested but **dormant** here (it activates when PRSG-004
supplies the home note); the PRS zone renders from a **repo-local committed
source only** (never `gh`). This closes PRSG-002's deferred "non-MOC docs become
reachable via the MOC down-index" loop, dogfooded on `prsg-002` and `prsg-003`.

**Technical approach:** `bash` + `jq` only, no new dependency. Pure-function
zone renderers feed a whole-zone splice. Sentinel constants defined once.
Inject-if-missing and the template share one byte-exact anchor + zone order so a
template-born map and an injection-migrated map are byte-identical. Behavior
changes to the two consumer skills are mirrored into `codex-skills/` at the L1
structural parity bar; the script itself is one shared copy referenced by path.

## Technical Context

**Language/Version**: Bash (macOS/Linux, bash 3.2-safe — the repo's existing
lints are bash-3.2-safe) + `jq` for the PRS manifest parse. No new dependency
(constitution II; CLAUDE.md rule 2).

**Primary Dependencies**: Reuses `speckit-pro/tests/lib/moc-id-normalize.sh`
(`moc_normalize` / `moc_id_match`) for every ID join; reuses
`speckit-pro/tests/lib/moc-frontmatter.sh` (`moc_is_gated`,
`moc_frontmatter_field`) for version-gating and frontmatter reads. No second
normalizer is introduced (FR-004). Reusing this join inherits its opaque
whole-segment number-suffix comparison — the number-suffix segment is compared
byte-for-byte as a whole (e.g. `013a1` is never truncated to `013a`), with no
`[0-9]+[a-z]*` sub-parse — so cross-spec ID joins cannot silently collide
distinct slices. This correctness property is owned by the reused library (and its
own Layer-4 test), not re-derived here.

**Storage**: Committed repo files only. The generator is a pure function of:
(a) each spec's `SPEC-MOC.md`, (b) the files under each in-scope `specs/<branch>/**`
tree, and (c) an optional per-spec PRS manifest at
`specs/<branch>/.process/prs.json`. No network, no `gh`, no git calls at
generation time (FR-010, SC-008).

**Testing**: Shell test suite via `bash tests/run-all.sh` (run from the
`speckit-pro/` directory). New Layer 1 determinism fixture wired beside the
existing `validate-moc-*` lints; new Layer 4 unit test for the generator's pure
functions and `--check` path. Verification: `shellcheck`, `bash -n`, and
`bash tests/run-all.sh` (Layers 1, 4, 5).

**Target Platform**: Claude Code plugin runtime + Codex CLI plugin runtime
(the two coding-agent runtimes the plugin ships for). The script is
runtime-agnostic; only the two SKILL.md behavior descriptions are mirrored.

**Project Type**: Plugin tooling — one shared shell script plus plugin-skill
behavior edits and their tests. No end-user product code.

**Performance Goals**: Not latency-sensitive. Regen runs at autopilot phase
boundaries and on a `speckit-status` read. Whole-repo regen over the handful of
version-marked specs completes well within a phase-boundary checkpoint; no
performance target beyond "finishes promptly and offline."

**Constraints**: Deterministic — identical committed inputs MUST produce
byte-identical output, and a re-run with no source change MUST produce a
zero-byte diff (FR-003, SC-001, SC-009). The enumeration-independence required by
SC-009 is achieved concretely by sorting every discovered file/spec list under
`LC_ALL=C sort` before rendering, so `find`/glob enumeration order can never leak
into the output. `--check` writes nothing, ever, even on error paths (FR-012). The
PRS zone never contacts the network (FR-010). The roadmap INDEX path stays dormant
(FR-019). Stay within ~350 production LOC.

**Scale/Scope**: Repository-wide over version-marked specs (currently `prsg-002`
and, after its later-phase MOC artifact lands, `prsg-003`). Three zones; two
consumer skills + their Codex mirrors; one template edit.

**Reviewability Budget**: Primary surface — harness/adapter (one new shell
generator script plus its determinism + unit fixtures). Secondary surfaces —
docs/process (the spec-MOC template's added zones; the two skill behavior
descriptions and their Codex mirrors; the autopilot phase-execution reference
edit). Projected reviewable LOC ~350 production (shell + jq) plus fixtures.
Projected production files ~5 (one new script; edits to the template, two skill
descriptions/references, and their mirrors). Projected total files ~10 (production
+ determinism fixture + unit tests). Budget result: **within budget** (under the
400 LOC / 6 production-file / 15 total-file / single-primary-surface warn
thresholds). Split decision: **remains one spec** — the generator and its two
consumers are one cohesive engine; the INDEX-population and PRS-population paths
that would enlarge it are deferred to PRSG-004 / PRSG-009 / PRSG-011.

### Plan-Finalized Decisions (the four Plan-deferred items from spec.md Assumptions)

These four were routed to Plan by the design concept / Clarify. Each is pinned to
a concrete value here; downstream phases treat these as settled.

**D1 — Exact sentinel marker spelling (one definition, invisible when rendered).**
Three independent HTML-comment `START`/`END` pairs, defined once as shell
constants at the top of `generate-spec-index.sh` (and documented in
`contracts/sentinel-grammar.md`). The exact bytes:

```text
<!-- GENERATED:INDEX:START (do not edit; regenerated by generate-spec-index.sh) -->
<!-- GENERATED:INDEX:END -->
<!-- GENERATED:PRS:START (do not edit; regenerated by generate-spec-index.sh) -->
<!-- GENERATED:PRS:END -->
<!-- GENERATED:BACKLINKS:START (do not edit; regenerated by generate-spec-index.sh) -->
<!-- GENERATED:BACKLINKS:END -->
```

HTML comments are invisible in rendered Markdown, greppable, and independently
positionable. The `START` line carries the `(do not edit…)` note; the `END` line
is bare. The START/END text is matched by **fixed full-line string equality**
(not a loose regex) so a stray `GENERATED:` token in prose can never be mistaken
for a sentinel.

**D2 — Zone anchor position + fixed zone order (byte-identical template vs
inject-if-missing).** One canonical anchor, one fixed order, used identically by
the template (FR-017) and inject-if-missing (FR-008). **Anchor:** end of the
map-note body, i.e. appended after the existing intro paragraph. **Order:**
INDEX → PRS → BACKLINKS. **Exact byte framing** (this is the determinism trap,
not the position — pin it precisely):

- Exactly one blank line separates the end of the existing body from the first
  sentinel (`GENERATED:INDEX:START`).
- Each zone is the `START` line, then the rendered body (or nothing when empty —
  see D3 / FR-011), then the `END` line.
- Exactly one blank line separates one zone's `END` line from the next zone's
  `START` line.
- The file ends with the `GENERATED:BACKLINKS:END` line followed by a single
  trailing newline (one `\n`, no extra blank line).
- An **empty zone** is the two sentinel lines on consecutive lines with **no
  blank line and no body between them** (so empty == link-free, satisfying the
  stale-index lint — see "Cross-cutting G7 guarantee" below).

The injector reproduces this framing exactly; `assemble_zone_block()` is the
single function that emits the three-zone block for both the template-fill path
and the inject path, so they cannot drift.

**D3 — PRS data-source shape (deterministic, fixture-testable, never `gh`).** A
per-spec committed JSON manifest at `specs/<branch>/.process/prs.json`. Shape
(see `contracts/prs-manifest.schema.md`):

```json
{
  "schemaVersion": 1,
  "records": [
    { "slice": "PRSG-003", "pr": 117, "merged_sha": "abc1234" }
  ]
}
```

Parsed with `jq`. **Absent file OR `records: []` → render an empty-but-valid
(link-free) PRS zone, not an error** (FR-011). A manifest that is present but
malformed/unreadable is the distinct error case: fail safe with exit 2 and no
partial write (FR-016), never conflated with the absent/empty path. An unknown
`schemaVersion` is handled conservatively — render the records the renderer
understands, and fall back to the FR-016 fail-safe only when the structure is
unparseable (full rule in `contracts/prs-manifest.schema.md`). Records render in a
fixed order: by normalized `slice` ID ascending (via `moc_normalize`), then by
`pr` ascending.
The PRS rows render as plain text — the canonical example string is
`PRSG-003 · PR#117 · abc1234` (the exact form pinned in
`contracts/prs-manifest.schema.md` and `data-model.md` E4) — **not** as
`[](...)` markdown links, so they introduce no link the stale-index lint must
resolve, and so the dormant-vs-empty zone stays lint-clean. *Who writes* this
manifest when a slice merges is PRSG-009; PRSG-003 ships only the renderer + the
input contract + the fixture. When present, `prs.json` lives under `.process/`
and is therefore itself one of the BACKLINKS reachability entries (intended; it
resolves fine).

**D4 — Fixed commit-message wording for the autopilot's commit-on-non-empty-diff
rebuild step.** FR-014 folds the rebuilt maps into the autopilot's **existing**
checkpoint commit (SC-005: "exactly one rebuild **contribution to** the
checkpoint commit"). The existing checkpoint subjects are
`feat(SPEC-XXX): complete <phase> phase` / `feat(SPEC-XXX): implement phase`
(phase-execution.md). When the phase-boundary rebuild is the **only** change
(no other staged work), the autopilot uses this fixed, public-readable,
conventional-commits subject:

```text
docs(speckit-pro): regenerate spec-MOC navigation zones
```

`docs(speckit-pro)` because regenerating generated documentation zones is a
docs-scope change, it reads cleanly as a public squash subject (CLAUDE.md
PR-title rules — plain English, keeps the conventional-commits prefix, no
internal IDs), and `docs:` does not trigger a release-please version bump (the
generated zones are not a shipped feature). When the rebuild rides **alongside**
other staged phase work, it is folded into that phase's existing checkpoint
commit and no separate commit is made (FR-014 / SC-005). This wording is a fixed
constant in the autopilot phase-execution reference, not computed per-run.

### Error-handling discipline (the 3-way enum, internal-error trap, atomic write)

These pin the *mechanism* behind the error-result requirements (FR-015/FR-016/
FR-021/FR-022, SC-012). The authoritative exit-code/result contract is
`contracts/generator-cli.md` (the 3-way enum `0` current / `1` stale / `2` error;
`--check` writes nothing on any path incl. error; `set -E` + ERR trap mapping an
unexpected `set -e` failure to exit 2 on stderr, same pattern as the PRSG-002
lints). This block adds only the points not already nailed there:

**D5 — Internal-error trap, never conflated with stale (FR-021/FR-015).** The
generator follows the PRSG-002 lint's trap shape exactly (the grounding precedent
is `speckit-pro/tests/layer1-structural/validate-moc-orphan.sh`: `set -E` after the
`source` lines, an `_on_err` trap that prints an actionable stderr line and
`exit 2`, with `errtrace` so the trap propagates into shell functions). The
load-bearing rule the contract does not spell out: **the ERR/EXIT trap is disarmed
(`trap - ERR EXIT`) immediately before any deliberate non-zero exit** — i.e. before
the `--check` stale `exit 1` — so a legitimate stale result is never remapped to
the error `exit 2`. An unexpected internal failure (a fault not explicitly handled)
therefore lands on `exit 2` (error), and the benign content-difference path lands on
`exit 1` (stale); the two are structurally prevented from being conflated.

**D6 — Atomic whole-file write (no half-written map note; FR-016/FR-002).** Write
mode never edits a map note in place. For each map note that changed, the generator
writes the full new file body to a sibling temp file via `mktemp` (the established
plugin idiom — see `generate-pr-body.sh`), then `mv`-renames it over the target.
`mv` within one filesystem is atomic, so a target is observed as either the old or
the new whole file — never a half-written or corrupted note, even if the process
dies mid-write. The temp file is per target, so a failure writing one spec's map
note cannot leave any other spec's note half-written (FR-016 per-target atomicity).
A failed temp write or rename trips the D5 error path (`exit 2`, no partial result).
Because `--check` writes nothing at all (FR-012), atomicity is purely a write-mode
concern; the `--check` path only diffs the in-memory rebuild and never opens the
target for writing, even on its own error paths.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Assessment |
|-----------|-------------|------------|
| **I. Plugin Structure Compliance** | New script under an existing skill's `scripts/`; SKILL.md edits keep frontmatter valid; Codex mirrors stay 1:1 with CC skills (`validate-codex-skills.sh` + `validate-codex-parity.sh`) | **PASS** — `generate-spec-index.sh` goes under `skills/speckit-autopilot/scripts/` (sibling of `reviewability-gate.sh`); no new plugin, no new skill dir; behavior edits to `speckit-status` + `speckit-autopilot` are mirrored into `codex-skills/` (mirrors already exist, so coverage stays 1:1) |
| **II. Script Safety** | `#!/usr/bin/env bash`, `set -euo pipefail` first executable line, quoted vars, checked results, `chmod +x`, `bash -n` clean, `shellcheck` clean | **PASS (planned)** — generator follows the same script-safety shape as the PRSG-002 lints; a Layer 4 test plus `shellcheck`/`bash -n` enforce it before merge |
| **IV. Test Coverage Before Merge** | New bash script MUST have a Layer 4 unit test; new components pass Layer 1; `bash tests/run-all.sh` zero failures; tests use `assertions.sh` and `test-<script>.sh` naming | **PASS (planned)** — `tests/layer4-scripts/test-generate-spec-index.sh` (pure functions + `--check`) and `tests/layer1-structural/validate-spec-index-determinism.sh` (byte-stable fixture) wired into `run-all.sh`; both use `assertions.sh` |
| **V. Conventional Commits** | Public-readable `feat(speckit-pro): …` PR title; fixed regen commit subject is conventional-commits valid and internal-ID-free | **PASS** — PR title `feat(speckit-pro): generate spec map navigation zones …`; D4 regen subject `docs(speckit-pro): regenerate spec-MOC navigation zones` |
| **VI. KISS, Simplicity & YAGNI** | Simplest approach; no speculative features; no code for data that does not exist yet | **PASS** — INDEX-population, live PR/SHA writing, legacy backfill, and cross-spec citation graph are all explicitly NOT built (deferred to PRSG-004/009/011); the dormant INDEX path is the minimum needed so PRSG-004 needs no PRSG-003 change |

**Reviewability gate (plan-level):** Primary surface = harness/adapter (single
new script). Secondary = docs/process (template + two skill descriptions/refs +
mirrors). All metrics under warn thresholds (≤400 LOC, ≤6 production files, ≤15
total files, one primary surface). No split required. **No constitution
violations — Complexity Tracking left empty.**

**PR review packet source** (per FR/PR-Review-Packet requirements): the plan's
Summary (what/why), the Non-goals list below (non-goals), the "Review order"
note in `quickstart.md` (review order), this Reviewability Budget block (scope
budget), `contracts/` + `data-model.md` (traceability of FR → zone/contract),
the determinism fixture + Layer 4 test (verification evidence), the "Known gaps"
list below (known gaps), and "Rollback/flags" below.

**Non-goals (bound by design concept):** roadmap-level INDEX population against a
real home note (PRSG-004); live slice→PR#→SHA population (PRSG-009); backfilling
zones into legacy specs without a `SPEC-MOC.md` (PRSG-011); an inbound cross-spec
citation graph (`related:` empty in v1); `speckit-status` writing any file;
linking the cross-tree roadmap-level `.process/` exhaust from a spec-MOC.

**Known gaps:** the INDEX zone renders nothing live in this repo (no roadmap home
note yet — dormant by design, fixture-exercised); the PRS zone typically renders
empty in this pre-PRSG-009 repo (no manifest writer yet).

**Rollback/flags:** No feature flag. Rollback is a pure revert of the new script
+ the skill/template edits; because `speckit-status` is read-only and the
autopilot only commits on a non-empty diff, reverting leaves no orphaned state.
The generated zones are bounded by sentinels, so a revert simply stops
regenerating them; existing committed zone content remains valid Markdown.

## Cross-cutting G7 guarantee (PRSG-002 lints stay green on the dogfooded MOCs)

PRSG-002's `validate-moc-stale-index.sh` greps **every** body `[](...)` link in a
gated `SPEC-MOC.md` and requires each to resolve to a regular readable file
relative to the MOC's own directory; `validate-moc-orphan.sh` requires a
well-formed relative `up:`. The generator MUST therefore preserve both lints on
the real `prsg-002` and `prsg-003` MOCs at G7. Three rules make this hold:

1. **BACKLINKS links are emitted relative to the SPEC-MOC's own directory** (e.g.
   `[spec.md](spec.md)`, `[research](research.md)`, `[prs manifest](.process/prs.json)`),
   so every emitted link resolves from `specs/<branch>/` and the stale-index lint
   stays green. Only files that exist on disk are enumerated, so no dangling link
   is ever emitted.
2. **Empty PRS zone and dormant INDEX zone are link-free** — "empty-but-valid"
   means the two sentinel lines with no `[](...)` between them. The HTML-comment
   sentinels themselves contain no link pattern, so they are invisible to the
   lint's `[](...)` grep.
3. **The injector never touches `up:` or frontmatter** — it only appends/refreshes
   the sentinel-bounded body block, so the orphan lint's `up:` check is unaffected.

This guarantee is asserted at G7 by running the two PRSG-002 lints (which already
dogfood-scan the real trees) after the generator writes the dogfooded MOCs.

## Project Structure

### Documentation (this feature)

```text
specs/prsg-003-spec-index/
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 output — reuse-vs-reinvent, PRS-source, anchor framing
├── data-model.md        # Phase 1 output — zone schemas, ordering keys, manifest entity
├── quickstart.md        # Phase 1 output — run the generator, read a staleness report
├── contracts/           # Phase 1 output — sentinel grammar, CLI contract, PRS schema
│   ├── generator-cli.md         # --check vs write, exit-code enum, args
│   ├── sentinel-grammar.md      # the six sentinel lines + framing rules (D1/D2)
│   └── prs-manifest.schema.md   # repo-local PRS manifest shape (D3)
├── SPEC-MOC.md          # Created in a LATER phase (Implement), NOT here — see note
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

> **Note on `SPEC-MOC.md`:** This spec's own version-marked `SPEC-MOC.md`
> (with valid relative `up:`, `spec_id: "PRSG-003"`, `structureVersion: 1`, and
> the three empty GENERATED zones at the canonical anchor) is an **artifact this
> feature produces**, created during Implement (after the generator exists, so it
> can dogfood on it and PRSG-002's lints stay green at G7). It is intentionally
> NOT created during Plan (spec.md Assumptions). It is planned as a task.

### Source Code (repository root)

```text
speckit-pro/
├── skills/
│   ├── speckit-autopilot/
│   │   ├── scripts/
│   │   │   └── generate-spec-index.sh          # NEW — the shared generator (bash+jq)
│   │   └── references/
│   │       └── phase-execution.md              # EDIT — idempotent regen-and-commit-on-diff step (Claude side)
│   ├── speckit-status/
│   │   └── SKILL.md                            # EDIT — invoke generator --check, surface staleness read-only
│   └── speckit-coach/
│       └── templates/
│           └── spec-moc-template.md            # EDIT — three empty GENERATED zones at the canonical anchor
├── codex-skills/
│   ├── speckit-status/
│   │   └── SKILL.md                            # MIRROR — --check behavior, Codex-native
│   └── speckit-autopilot/
│       ├── SKILL.md                            # MIRROR — phase-gate regen behavior, Codex-native
│       └── references/
│           └── phase-execution-codex.md        # MIRROR — Codex-native regen step (validate-codex-skills.sh asserts this path)
└── tests/
    ├── lib/
    │   ├── moc-id-normalize.sh                 # REUSE (PRSG-002) — moc_normalize / moc_id_match
    │   └── moc-frontmatter.sh                  # REUSE (PRSG-002) — moc_is_gated / moc_frontmatter_field
    ├── layer1-structural/
    │   ├── validate-spec-index-determinism.sh  # NEW — re-run = zero diff fixture
    │   └── fixtures/spec-index/                # NEW — committed fixture spec trees
    └── layer4-scripts/
        └── test-generate-spec-index.sh         # NEW — pure functions + --check path
```

**Structure Decision:** Single shared script under
`skills/speckit-autopilot/scripts/` (the autopilot owns the authoritative write
path, matching ownership; `reviewability-gate.sh` already lives here and is
referenced cross-skill by absolute path). Both `speckit-status` and
`speckit-autopilot` — and their Codex mirrors — invoke this one copy by absolute
plugin path; the script is **not** duplicated into `codex-skills/` (FR-020,
design concept Q9). Tests follow the PRSG-002 layout: an L1 determinism lint
beside `validate-moc-*` (wired into `run-all.sh`), an L4 unit test beside
`test-moc-*`. The `data-model.md`, `contracts/`, and `quickstart.md` artifacts
are documentation, not source — they live under the feature dir.

## Complexity Tracking

> No constitution violations. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | | |
