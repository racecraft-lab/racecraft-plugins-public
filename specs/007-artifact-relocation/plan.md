# Implementation Plan: Artifact relocation — tiering, .process/, collapse

**Branch**: `007-artifact-relocation` | **Date**: 2026-06-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/007-artifact-relocation/spec.md`

## Summary

Tier every speckit-pro-authored spec artifact into CONTRACT (review-visible) vs
EXHAUST (scaffolding), redirect the three EXHAUST artifacts speckit-pro itself
authors — the design-concept doc, the workflow file, and the UAT runbook — into a
`.process/` directory, collapse `.process/` out of the review diff via a repo-root
`.gitattributes` `linguist-generated=true` rule, and align the reviewability gate's
diff-mode LOC accounting so relocated exhaust drops out of the reviewable count.
No artifact is deleted; every relocated file stays on disk at its new `.process/`
location and remains diffable on demand.

Technical approach: the redirect (US1) is path-string edits in markdown skill files
(plus identical mirrors in the Codex skill counterparts) — no new abstraction layer.
The collapse + gate alignment + lint (US2) is one new repo-root `.gitattributes`
rule, one idempotent append into the consuming project's `.gitattributes` (folded
into the existing scaffold-time `ensure-reviewability-preset.sh`, not a new script),
one new `case` arm in the gate's `is_excluded_generated()`, and one new Layer-1
structural lint that proves every `linguist-generated` rule is scoped to `.process/`.
US2 is inert until US1 actually writes under `.process/`, so US1 sequences first.

## Technical Context

**Language/Version**: Bash (macOS/Linux), `jq` for JSON; Python 3 only where the
existing `ensure-reviewability-preset.sh` already uses it (its heredoc). This is a
Claude Code plugin marketplace, NOT an application — there is no compiled runtime.

**Primary Dependencies**: `git` (linguist reads repo-root `.gitattributes`), `jq`,
GitHub linguist (`linguist-generated` collapse mechanism). No package manager, no
Node/Rust/Go build.

**Storage**: Files on disk. Relocated exhaust lives under two `.process/` trees:
`docs/ai/specs/.process/` (scaffold-time exhaust) and `specs/<NNN>/.process/`
(per-feature exhaust). N/A — no database, no persisted state.

**Testing**: Shell-script test layers run via `bash speckit-pro/tests/run-all.sh`.
CI runs Layers 1 (structural), 4 (script unit), and 5 (tool scoping). This feature
adds one Layer-1 lint and extends two existing Layer-4 tests. Layer-8 (Codex parity)
fixtures already cover the mirrored skills.

**Target Platform**: Developer workstations and CI runners (bash + GitHub Actions).

**Project Type**: Claude Code plugin (single plugin, `speckit-pro`). Not
library/web/mobile. PROJECT_COMMANDS BUILD / TYPECHECK / LINT / UNIT_TEST are N/A;
the only build-equivalent is the shell test runner above.

**Performance Goals**: N/A (no runtime hot path). The gate already runs once per PR.

**Constraints** (locked; carried verbatim into Tasks so they are not re-litigated):
- **Collapse mechanism: `linguist-generated=true` ONLY.** NO `-diff` — relocated
  artifacts stay diffable and loadable on demand (FR-008).
- **New-specs-only.** MUST NOT migrate, move, or mutate any existing
  `specs/<NNN>/` directory; legacy relocation is a separate later spec (FR-013).
- **The gate hardcodes the `.process/` glob.** The gate MUST NOT parse
  `.gitattributes`; the duplication between the gate and the collapse config is
  intentional and guarded by a cross-file lint (FR-011). `bash case` cannot
  faithfully express gitattributes `**` anyway.
- **bash + `jq` only.** No new dependency, no new abstraction layer, and no new
  flags/options "for future flexibility" for a single call site (constitution
  Principle VI; CLAUDE.md rules 2–3).
- **Codex parity.** Every prose edit redirecting exhaust in a Claude skill MUST be
  mirrored identically into its Codex counterpart in the SAME PR (FR-006).

**Scale/Scope**: ~250 reviewable LOC as a planning target (not a ceiling). Roughly:
US1 prose path-string edits + Codex mirrors; US2 = gate arm (~1 line) +
`.gitattributes` (1 rule) + consumer ensure append (~10–20 lines into an existing
script) + new L1 lint (~40 lines) + L4 test extension (~30 lines).

**Reviewability Budget**: primary surface — the speckit-pro PR-exhaust handling
pathway; projected reviewable LOC ≈ 250 (under 400 warn / 800 block); production
files ≈ 0 (the gate's `is_production_file()` matches paths that *start* with
`scripts/`/`src/`/`app/`/`lib/` or carry a JS/TS/SQL extension — every touched
`.sh` is at `speckit-pro/skills/.../scripts/…` which does NOT start with `scripts/`,
and `.sh` is not an extension match, so it counts zero production files — under 6
warn / 8 block); total files ≈ 12–14 changed (under 25 block; may touch the 15 warn
line — warn only, not a blocker); **budget result: PASS via a declared split
exception** — the gate's `surface_for_path()` heuristic mechanically computes ≥2
primary surfaces from filenames (see Constitution Check), which trips the
">1 primary surface" blocker; this plan ratifies a **split exception** (the gate's
sanctioned escape hatch) because the change is one logical surface artificially
sharded by filename patterns.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution v1.1.0 principles evaluated:

- **I. Plugin Structure Compliance** — PASS. No new plugin directory; edits stay
  inside `speckit-pro/` and its existing `skills/`, `codex-skills/`, `tests/` layout.
  New L1 lint is added to the existing `tests/layer1-structural/` array.
- **II. Script Safety** — PASS (obligation). The one-arm gate edit, the consumer
  ensure append, and the new L1 lint MUST keep `#!/usr/bin/env bash` +
  `set -euo pipefail`, quote all variables, and pass `bash -n` / `validate-scripts.sh`.
- **III. Semantic Versioning** — PASS. No manual `plugin.json` version edit;
  release-please handles the bump from the `feat(speckit-pro):` commit.
- **IV. Test Coverage Before Merge** — PASS by design. SC-003 (gate exclusion) is
  covered by extending the already-wired `tests/layer4-scripts/test-reviewability-gate.sh`.
  SC-004 (consumer ensure-step idempotency) is covered by extending the already-wired
  `tests/layer4-scripts/test-ensure-reviewability-preset.sh` — because the consumer
  `.gitattributes` append folds into the existing `ensure-reviewability-preset.sh`
  rather than a new script, no new Layer-4 test file is owed. SC-005 (collapse-scope
  lint) is the new `tests/layer1-structural/validate-process-gitattributes.sh` itself,
  which by repo convention (no existing L1 validator carries its own L4 test) does not
  owe a dedicated L4 test. SC-006 (Codex parity) is covered by the existing
  `validate-codex-skills.sh` + Layer-8 parity fixtures.
- **V. Conventional Commits** — PASS. Single squash commit
  `feat(speckit-pro): <plain-English>` (orchestrator owns the commit).
- **VI. KISS, Simplicity & YAGNI** — PASS. The redirect is path-string edits, not a
  helper layer. The consumer ensure-step reuses an existing script and an existing
  test rather than introducing a one-call-site script + test. The gate change is a
  single `case` arm. Master-plan entry exists: PRSG-001 in the PR-size governance
  roadmap + PRD §3.1.

**Reviewability budget declaration** (required by the active preset):

- **Primary review surface**: the speckit-pro PR-exhaust handling pathway. This is
  one logical surface even though the files span three skills (scaffold-spec, coach,
  autopilot), the repo root, and tests — they are the single coordinated change set
  that redirects-and-collapses authored exhaust.
- **Secondary surfaces**: none.
- **Mechanical-gate reality (traced in code, not assumed)**: the gate builds
  `surfaces_text` from ALL changed/declared files (reviewability-gate.sh:192 tasks-mode,
  :237 diff-mode), then runs `surface_for_path()` over each. That heuristic shards
  this change by filename into ≥2 buckets — `workflow-template.md` trips the
  `*workflow*` arm → "scheduler/runtime" (a false positive: it is a template doc,
  not runtime code); the `*.md`/`docs/*`/`specs/*` edits → "docs/process"; the `.sh`
  and `.gitattributes` files → "other". So `surface_count ≥ 2`, which adds the
  ">1 primary surface" blocker (reviewability-gate.sh:97) and would set `status=block`
  (exit 1).
- **Split exception (ratified here)**: the gate clears that block when an in-scope
  changed `.md` contains the phrase the gate greps for — `transition exception`,
  `split exception`, or `ratified exception` (reviewability-gate.sh:101 rewrites
  `status=block` → `status=exception`, and `exception` counts as a pass). This plan
  RATIFIES A SPLIT EXCEPTION: the multi-surface count is a filename-heuristic
  artifact, not a genuine multi-surface change — the human-meaningful review surface
  is single, so a `split exception` is the honest, constitution-sanctioned response
  (constitution: ">1 primary surface … unless a ratified split exception exists").
  No actual US1/US2 split is warranted, because splitting would not lower the count
  (each half still touches `.sh` + `.md`, tripping multiple buckets).
- **Budget result**: **PASS via the ratified split exception above.** reviewable LOC
  ≈ 250 (< 400 warn), production files ≈ 0 (< 6 warn), total files ≈ 12–14 (at/near
  the 15 warn line — warn only). The only blocker is the heuristic surface count,
  cleared by the declared split exception. Without the exception the mechanical gate
  would emit `block`; this is reported transparently rather than presented as a clean
  mechanical pass.
- **Split decision**: no code split — declared `split exception` instead, scoped to
  this single-logical-surface change. No follow-up spec/issue IDs are deferred by
  this decision (US1→US2 sequencing is internal ordering, not a scope split).
- **PR review packet source** (what the generated PR body must carry):
  - *What changed*: redirect of three authored exhaust artifacts into `.process/`;
    repo-root + consumer `.gitattributes` collapse rule; gate diff-mode exclusion;
    collapse-scope lint.
  - *Why*: ~32% of a feature PR is exhaust that buries the contract artifacts.
  - *Non-goals*: extension-authored exhaust (owned by the `archive` extension
    post-merge), `-diff`, legacy migration, moving the CONTRACT set.
  - *Review order*: US1 (redirect) before US2 (collapse/gate/lint) — US2 is inert
    until US1 writes under `.process/`.
  - *Scope budget*: as above (PASS).
  - *Traceability*: FR-001…FR-015 → tasks; SC-001…SC-007 → tests.
  - *Verification*: `bash speckit-pro/tests/run-all.sh` (Layers 1/4/5) green;
    new L1 lint + extended L4 tests pass.
  - *Known gaps*: pre-existing dead-code arm in the gate
    (`docs/ai/workflows/*/exports/*`, that dir does not exist) is left untouched
    (CLAUDE.md rule 3 — mention, do not delete).
  - *Rollback/flags*: no feature flag; revert is the single squash commit. The
    consumer `.gitattributes` append is additive + idempotent (re-running is safe).

**Result: Constitution Check PASS, contingent on one declared split exception** for
the reviewability surface budget (the mechanical gate computes ≥2 surfaces from
filenames; cleared via the ratified `split exception` documented above and in the
Complexity Tracking table). No core-principle (I–VI) violation. (Re-checked
post-Phase 1: unchanged — no new entities, contracts, or abstractions were
introduced in design; the surface-count exception is a filename-heuristic artifact,
not a design-complexity addition.)

## Project Structure

### Documentation (this feature)

```text
specs/007-artifact-relocation/
├── spec.md              # Feature spec (already complete: 15 FRs, US1/US2, 8 ACs)
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 — minimal pointer (design concept resolved all unknowns)
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

Omitted as N/A (do NOT fabricate):
- `data-model.md` — no data model; the taxonomy (CONTRACT/EXHAUST/`.process/`) is
  prose already captured in spec.md "Key Entities" and the design concept (FR-001
  is satisfied by documentation, not a new artifact file).
- `contracts/` — no API or external machine interface is introduced.
- `quickstart.md` — no user-facing runtime to quickstart; the change is internal to
  speckit-pro's authoring path.

The authoritative design rationale already lives at
`docs/ai/specs/PRSG-001-design-concept.md` (the grounding pass + Q&A log);
`research.md` is a thin pointer to it rather than a duplicate.

### Source Code (repository root)

The implementation touches existing files only (plus one new `.gitattributes` and one
new L1 lint). Bare basenames in the design concept map to these worktree paths:

```text
# US1 — redirect authored exhaust into .process/ (markdown prose; mirror to Codex)
speckit-pro/
├── skills/speckit-scaffold-spec/SKILL.md          # mkdir, grill-me output_path,
│                                                   #   workflow Write target, git add
│                                                   #   → docs/ai/specs/.process/
├── codex-skills/speckit-scaffold-spec/SKILL.md     # identical edits (parity mandate)
├── skills/speckit-coach/templates/workflow-template.md  # design-concept/workflow self-refs
├── skills/speckit-autopilot/scripts/generate-pr-body.sh # repoint read path (L179)
│                                                          #   + ./uat-runbook.md link (L188)
│                                                          #   → specs/<NNN>/.process/;
│                                                          #   keep "## UAT Runbook" rendering
├── skills/speckit-autopilot/references/post-implementation.md  # generator output path (L564)
│                                                                #   + git add (L590) → .process/

# US2 — collapse + gate alignment + lint
.gitattributes                                       # NEW repo-root: one rule
│                                                     #   **/.process/** linguist-generated=true
speckit-pro/
├── skills/speckit-coach/scripts/ensure-reviewability-preset.sh  # FOLD IN: idempotent
│                                                                  #   append of the .process/
│                                                                  #   rule to the consumer's
│                                                                  #   .gitattributes (reuses
│                                                                  #   PROJECT_ROOT=${1:-$PWD})
├── skills/speckit-autopilot/scripts/reviewability-gate.sh        # is_excluded_generated():
│                                                                  #   add one arm
│                                                                  #   */.process/*|*.process/*) return 0
│                                                                  #   (lines 48–57; dead-code
│                                                                  #   arm L54 left untouched)
└── tests/
    ├── layer1-structural/validate-process-gitattributes.sh       # NEW lint (modeled on
    │                                                              #   validate-pr-checks-sentinel.sh);
    │                                                              #   register in run-all.sh L1 array
    ├── layer4-scripts/test-reviewability-gate.sh                 # EXTEND: diff-mode test —
    │                                                              #   .process/ excluded, spec counted
    └── layer4-scripts/test-ensure-reviewability-preset.sh        # EXTEND: idempotency of the
                                                                   #   consumer .gitattributes append
```

**Structure Decision**: No new top-level structure. All production changes live under
the existing `speckit-pro/skills/.../scripts/`, `.../templates/`, `.../references/`,
and `codex-skills/` trees, plus one new repo-root `.gitattributes` and one new file in
the existing `speckit-pro/tests/layer1-structural/` array. This matches the plugin
layout (constitution Principle I) and keeps the change surgical (CLAUDE.md rule 3).

**Consensus resolution — consumer `.gitattributes` safe-write (Checklist/error-handling):**
The consumer ensure-step (folded into `ensure-reviewability-preset.sh`) MUST:
1. Detect presence with `grep -qxF "$rule" "$file"` — fixed-string (`-F`, because the rule
   contains `*` glob metacharacters) whole-line (`-x`) match; short-circuit if already present.
2. Normalize the trailing newline before appending: if the existing file's last byte is not
   `\n`, add one first — otherwise the rule silently concatenates onto the last existing line
   and yields a malformed `.gitattributes` (git-lfs#167). Upholds FR-009(c) "preserve every
   pre-existing line byte-for-byte".
3. Write atomically: copy existing content (if any) into a SAME-DIRECTORY temp file
   `mktemp "${file}.XXXXXX"` (same dir keeps `mv` atomic on macOS, where `/tmp` is a separate
   filesystem and a cross-device `mv` degrades to non-atomic copy), append the rule to the temp,
   then `mv` it over the target; `trap 'rm -f "$tmp"' EXIT` to avoid orphaned temps. Satisfies
   the Edge Case "no partial/truncated file on interruption".

This is ~10 LOC, matches the repo's established temp-then-rename convention
(`install-curated-set.sh`, `generate-uat-skeleton.sh`'s "write once at the end"), and adds no
new script/abstraction (constitution VI). Resolved by 2-analyst consensus (codebase + domain),
both high-confidence on the prerequisites.

## Complexity Tracking

> One row: the reviewability **surface budget** is exceeded by the mechanical gate
> and waived via a ratified split exception. No core principle (I–VI) is violated.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Reviewability surface budget: gate's `surface_for_path()` computes ≥2 primary surfaces (threshold is 1) | The change is one logical surface (the speckit-pro PR-exhaust pathway) but unavoidably touches files whose *names* fall in different heuristic buckets — `workflow-template.md` → "scheduler/runtime" (false positive), `*.md` → "docs/process", `.sh`/`.gitattributes` → "other". Redirecting exhaust AND aligning the gate/collapse cannot be done without touching both markdown skills and a shell script. | Splitting US1/US2 into separate PRs does NOT lower the surface count — each half still touches `.sh` + `.md`, tripping ≥2 buckets. Renaming `workflow-template.md` to dodge the `*workflow*` arm would be a gratuitous rename of an unrelated file (CLAUDE.md rule 3). A genuine single-bucket change is impossible for a cross-cutting redirect+gate feature. Hence the constitution-sanctioned `split exception`, declared in plan.md so the gate (which greps changed `.md` for the phrase) honors it in both setup-mode and diff-mode. |

## Phase 0 — Research

All unknowns were resolved before planning by the four-agent grounding pass recorded
in `docs/ai/specs/PRSG-001-design-concept.md`. There are **zero** open
`[NEEDS CLARIFICATION]` markers. `research.md` is therefore a thin pointer to that
document rather than a re-derivation. Key resolved decisions (each with evidence in
the design concept):

- **Dual `.process/` anchor** (Q1): `docs/ai/specs/.process/` + `specs/<NNN>/.process/`,
  collapsed by one `**/.process/**` rule — because the two scaffold-authored exhaust
  files land in a different tree (`docs/ai/specs/`) than the per-feature runbook.
- **Both repos get the rule** (Q2): static repo-root `.gitattributes` (dogfood + lint
  target) AND a consumer-side idempotent ensure-step, because linguist reads each
  repo's own `.gitattributes`.
- **UAT runbook = EXHAUST** (Q3): move it and repoint `generate-pr-body.sh` so the PR
  body still renders its "## UAT Runbook" section.
- **Scope to authored exhaust** (Q4/Q5): extension-authored exhaust (retrospective,
  verify-tasks-report) stays visible at review; the `archive` extension already owns
  post-merge cleanup, so PRSG-001 does NOT build a `git mv` sweep.

## Phase 1 — Design & Contracts

- **data-model.md**: N/A — no data model. The taxonomy entities (CONTRACT artifact,
  EXHAUST artifact, `.process/` directory, collapse rule) are already documented in
  spec.md "Key Entities"; no further modeling is required.
- **contracts/**: N/A — no API, CLI grammar, or external machine interface is added.
  The one behavioral contract worth naming is internal and already enforced by tests:
  the gate's `.process/` exclusion and the collapse rule must agree, guarded by the new
  cross-file lint (FR-011/SC-005).
- **quickstart.md**: N/A — no user-facing runtime.
- **Agent context update**: `update-agent-context.sh` may run and edit the repo-root
  `CLAUDE.md` between its `<!-- SPECKIT START/END -->` markers. It is allowed to run;
  this plan does not hand-edit `CLAUDE.md`.

Re-evaluation after Phase 1: Constitution Check remains **PASS** — design introduced
no new entities, contracts, abstractions, or surfaces beyond what was scoped.
