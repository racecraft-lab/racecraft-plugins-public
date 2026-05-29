# Implementation Plan: Deterministic UAT Runbook Skeleton + PR Body Integration

**Branch**: `006a-uat-skeleton` | **Date**: 2026-05-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006a-uat-skeleton/spec.md`

**Design Concept**: `docs/ai/specs/SPEC-006a-design-concept.md` (source of truth for the four locked decisions Q1-Q4)

## Summary

Add the deterministic infrastructure half of a UAT artifact for the speckit-pro autopilot: a heading-driven `uat-runbook.md` generated from `spec.md`, committed to the spec directory, and embedded in (or linked from) the PR body. Three production artifacts plus one Layer 4 test:

1. A new strict-mode bash script `generate-uat-skeleton.sh` that parses `### User Story`, `### Functional Requirements`, `### Measurable Outcomes`, and `### Edge Cases` from `spec.md` and renders a runbook against a new template.
2. A new `uat-runbook-template.md` with a fixed eight-section order.
3. A surgical edit to the existing `generate-pr-body.sh` adding a size-aware `## UAT Runbook` section.
4. A new Layer 4 unit test with five fixtures (one vendored full-spec snapshot + four synthetic inline).

LLM-authored narrative test prose and author agents are deferred to SPEC-006b. The technical approach reuses the existing `extract_heading_section()` awk helper and matches the established speckit-autopilot script conventions; no new dependencies are introduced.

## Technical Context

**Language/Version**: Bash (macOS/Linux), POSIX-compatible. Strict mode `set -euo pipefail`, `#!/usr/bin/env bash` shebang per constitution Principle II.

**Primary Dependencies**: `jq` (already a hard prerequisite for the autopilot), `awk`, `head`, `wc` (coreutils). No new dependencies.

**Storage**: Filesystem only — reads `spec.md`, writes `uat-runbook.md`. No persistent data model, no database. (research.md and data-model.md are **N/A** — see Phase 0/1 below.)

**Testing**: Layer 4 unit test (`tests/layer4-scripts/test-generate-uat-skeleton.sh`) using the shared `tests/lib/assertions.sh` harness (`assert_eq`, `assert_contains`, `assert_file_exists`, `assert_exit_code`, `test_summary`) and the `mktemp -d` + `trap` fixture pattern from `test-ensure-reviewability-preset.sh`. Auto-discovered by `tests/run-all.sh --layer 4`.

**Target Platform**: Developer machines + GitHub Actions CI (`pr-checks.yml` matrix). The script runs inside the autopilot post-implementation phase and standalone.

**Project Type**: CLI script + Markdown template within the speckit-pro plugin (a Claude Code plugin marketplace). Not a library/web-service.

**Performance Goals**: N/A — single-pass `awk`/`jq` over one spec file (kilobytes); runtime is negligible.

**Constraints**: Strict-mode bash; shellcheck-clean (existing CI gate); no new agent files (Layer 1 Codex parity invariant); Codex variant edited in lockstep; KISS/YAGNI (no flags for hypothetical callers).

**Scale/Scope**: One new script (~220 LOC), one new template (~90 LOC), one surgical `generate-pr-body.sh` edit (~25 LOC), one Layer 4 test (~180 LOC). Plus a vendored fixture (data, not counted as code) and lockstep Codex/reference documentation edits.

**Reviewability Budget**: Primary surface = docs/process (UAT template + skeleton script + autopilot SKILL/reference edits). Secondary surface = harness/adapter (one Layer 4 test + vendored fixture) plus a surgical modification to `generate-pr-body.sh`. Projected reviewable LOC ~670 (excludes the vendored `spec-full-snapshot.md`, which is fixture data). Projected production files = 4 (template, script, modified `generate-pr-body.sh`, Layer 4 test). Projected total files = **11** (counting the leaves enumerated in the Project Structure tree: 6 CC files + 3 Codex `-codex.md`/SKILL.md doc twins + 2 test files incl. the vendored fixture). The spec estimated 9; reconciling against the verified `-codex.md` doc twins adds 2, still under the 15-file warn threshold and well under the 25-file block threshold. **Budget result: within budget** (under the 800 LOC / 8 production-file / 25 total-file block thresholds; LOC and production-file counts are unchanged). Split decision: remains one spec; the LLM-authored test prose + author agents are the natural split point, deferred to SPEC-006b.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | This Plan's Compliance |
|-----------|-------------|------------------------|
| I. Plugin Structure | Standard plugin layout; new script under `skills/<skill>/scripts/`, new template under `skills/<skill>/templates/` | New files land under `speckit-pro/skills/speckit-autopilot/scripts/` and `.../templates/` — existing dirs. No structural changes. **Gate:** `run-all.sh --layer 1`. |
| II. Script Safety | `#!/usr/bin/env bash` + `set -euo pipefail`; quoted vars; checked results; executable; `bash -n` clean | New script uses strict mode, quoted vars, `local`-scoped functions, `[[ ]]` over `[ ]`, matching `generate-pr-body.sh`. Verified via `bash -n` + shellcheck. |
| III. Semantic Versioning | `plugin.json` is source of truth; manual edits prohibited (release-please automates) | **No version edit in this PR** — script + template additions only. release-please bumps on merge of the `feat:` commit. |
| IV. Test Coverage | New bash scripts MUST have Layer 4 tests using `assertions.sh`; naming `test-<script>.sh` | New `test-generate-uat-skeleton.sh` (FR-015) covers five fixtures. **Gate:** `run-all.sh` (L1+L4+L5) zero failures. |
| V. Conventional Commits | `type(scope): description`; scope = plugin dir | Commits prefixed `feat(speckit-pro):` / `test(speckit-pro):` / `docs(speckit-pro):`. PR title plain-English public-readable per CLAUDE.md. |
| VI. KISS / YAGNI | Simplest approach; no speculative abstractions; no wrappers for one call site | Copy `extract_heading_section()` verbatim (no source-time side effects — see Decision 1); no `--force` flag (deterministic overwrite); no standalone regenerate skill. Three production files + one test, no new layers. |

**Review surfaces:** Primary = docs/process (template + script + autopilot SKILL/reference edits). Secondary = harness/adapter (Layer 4 test + vendored fixture) + surgical `generate-pr-body.sh` edit. Within the one-primary-surface rule.

**Reviewability budget:** Within budget (see Technical Context). No split exception required.

**PR review packet source:** what changed (new UAT skeleton script + template + PR-body wiring + Layer 4 test), why (reviewers lack a story-by-story acceptance artifact), non-goals (LLM test prose / author agents → SPEC-006b), review order (template → script → PR-body edit → Layer 4 test → Codex/reference lockstep), scope budget (~670 LOC / 4 prod / 11 total, within budget), traceability (FR-001..FR-015 + SC-001..SC-005 mapped below), verification (`run-all.sh --layer 4`, `--layer 1`, standalone smoke), known gaps (none expected), rollback (`git revert <SHA>`; script + template additions are self-contained, no migration).

**Constitution Check result: PASS** — no violations. Complexity Tracking table is empty (no justified violations).

## Plan-Phase Decisions (the spec delegated these here)

Four points the finalized spec explicitly defers to Plan. Decisions 1-2 were the two the Clarify phase flagged; Decisions 3-4 are the additional Plan-delegated points in the FR text (FR-005 detection pattern, FR-010 anchor mechanism).


### Decision 1 — FR-002: copy `extract_heading_section()` verbatim (NOT source)

**Decision: Copy the function verbatim** (lines 45-65 of `generate-pr-body.sh`) into `generate-uat-skeleton.sh` with a provenance comment, rather than `source`-ing `generate-pr-body.sh`.

**Pinned source line range:** `extract_heading_section()` is defined at **`generate-pr-body.sh` lines 45-65** (opening `extract_heading_section() {` at line 45 through the closing `}` at line 65). The pre-implementation step (workflow Phase 7) must re-verify this range still holds before copying.

**Evidence (decisive):** `generate-pr-body.sh` has **no source guard** — there is no `if [[ "${BASH_SOURCE[0]}" == "${0}" ]]` wrapper. Verified by `grep -n 'BASH_SOURCE' generate-pr-body.sh` → zero matches. The file runs top-level logic at source time: it reads positional argv and `exit 2`s on missing args (lines 9-17), invokes `reviewability-gate.sh` (lines 86-91), calls `mktemp` and registers `trap 'rm -f "$review_packet"' EXIT` (lines 106-107), and writes `$OUTPUT_FILE` (line 158). Sourcing it from the new script would execute all of that — including the `exit 2` (which would abort the sourcing script) and an EXIT trap that fights the new script's own cleanup. Copying the 21-line awk function is the KISS-correct, side-effect-free choice and satisfies FR-002's "sourced or copied verbatim, not reimplemented." The copy carries a provenance comment: `# Copied verbatim from generate-pr-body.sh lines 45-65 (FR-002). Keep in sync if that helper changes.`

**Boundary semantics (the section's edges).** The helper's awk loop ends a section at the next heading whose level is the same or higher (`if (in_section && level <= section_level) exit`, `generate-pr-body.sh` line 61). The closing boundary therefore **excludes** that next heading line — the extracted block runs from the line after the matched heading up to (but not including) the next same-or-higher-level heading. A deeper sub-heading (higher hash count, lower precedence) stays *inside* the section. This matters in two places: the Self-Review echo (FR-009) extracts the `## Self-Review` block, which ends at the next H2; and any FR/SC/Edge extraction that delegates to the helper inherits the same edge rule. Note the helper also strips blank lines and caps at 40 lines (line 64) — it is a bounded summarizer, not a faithful reader, which is exactly why Decision 2 routes the under-threshold "full content" PR-body path through `cat` instead.

**Path resolution (worktree-safe).** All feature-relative inputs derive from the caller-supplied spec path: the feature directory is `dirname "$argv[1]"`, and the `plan.md` Rollback fallback (FR-012) is read from that derived directory. The script is therefore CWD-independent for its inputs — it does not assume a fixed working directory and does not depend on SpecKit's 3-digit branch-name regex (which the `006a-` name breaks anyway), so a run from `.worktrees/<branch>` with a passed-in spec path resolves correctly. The `--workflow-file` path is caller-supplied (absolute or relative to the caller's CWD), and the output path is exactly `argv[2]` with no implicit relocation into the feature dir. The downstream `generate-pr-body.sh` reads `<feature-dir>/uat-runbook.md` from its own `argv` feature-dir, consistent with the skeleton's `argv[2]` write target when the autopilot passes `<feature-dir>/uat-runbook.md`.

### Decision 2 — FR-013: under-threshold "full content" uses `cat` (NOT `extract_heading_section`)

**Decision: The under-50,000-character path embeds the full runbook via `cat "$FEATURE_DIR/uat-runbook.md"`** (a non-truncating full read).

**Rationale:** `extract_heading_section()` pipes through `sed '/^[[:space:]]*$/d'` (strips ALL blank lines, line 64) and `head -40` (caps at 40 lines, line 64). A sub-50KB runbook that exceeds 40 lines — which any real multi-story runbook will — would be silently truncated, and blank lines that make the Header table and section spacing render would be stripped. `cat` preserves the full content and all blank lines. This matches FR-013's explicit Plan note: "the under-threshold 'full content' path MUST NOT reuse `extract_heading_section` ... Plan selects a non-truncating mechanism such as `cat`."

**Over-threshold path (already resolved in Clarify S2):** when the runbook is at or over 50,000 characters, embed the first 60 lines via `head -60` (blank lines preserved so the Header table and section headings render) followed by a relative link to the committed `uat-runbook.md`. Size is measured with `wc -c < "$FEATURE_DIR/uat-runbook.md"`.

### Decision 3 — FR-005: clarification-marker detection pattern

**Decision: detect the `NEEDS CLARIFICATION` annotation in both its bare and colon-question forms** — i.e., match the literal token `NEEDS CLARIFICATION` whether it appears alone or as `NEEDS CLARIFICATION: <question>` (the two forms FR-005 names). A fixed-string `grep -F 'NEEDS CLARIFICATION'` test per bullet is sufficient and KISS-correct; no regex for bracket variants beyond that token. When a parsed US/FR/SC/Edge bullet contains the marker, the runbook reproduces the bullet and appends an annotation (e.g., `**WARN:** unresolved clarification`) on the same entry rather than dropping it. (FR-005 marks the exact pattern a Plan/implementation decision; this records it.)

### Decision 4 — FR-010: FR Coverage Matrix anchor mechanism

**Decision: explicit, script-emitted anchors** — the spec's stated default. The script emits a deterministic anchor (e.g., an HTML `<a id="us-1">` immediately before each Per-Story section heading, or the GitHub-renderable equivalent) and the FR Coverage Matrix rows link to those explicit anchors. This avoids replicating GitHub's heading-slug algorithm (which would be fragile against title punctuation/casing) and keeps the anchors stable across regenerations. Anchors resolve within the committed `uat-runbook.md`. (FR-010: "the exact anchor mechanism is a Plan decision; default: explicit script-emitted anchors.")

## FR-013 Wiring (the trap — wire precisely)

The workflow hint "add to the heading list at line 171" is **misleading and must not be followed literally**. Line 171's `for heading in ...` loop routes every heading through `append_missing_section()` → `extract_heading_section()` (the truncating path rejected in Decision 2), and emits `# <heading>` at H1. The `## UAT Runbook` section must instead be a **dedicated, size-aware block appended on its own**, explicitly NOT routed through `append_missing_section`/`extract_heading_section`:

- Emit the literal heading `## UAT Runbook` at **H2** (two hashes). SC-005 greps for that exact string, and the existing review-packet sections use `#` (H1) — do not pattern-match or reuse them.
- Read `"$FEATURE_DIR/uat-runbook.md"`. If the file is absent (standalone `generate-pr-body.sh` run with no runbook generated), emit a one-line stub note under the heading and continue (fail-open; never abort PR-body generation).
- If present: `size=$(wc -c < "$FEATURE_DIR/uat-runbook.md")`. When `size -lt 50000`, `cat` the full file under the heading (Decision 2). Otherwise emit `head -60` of the file plus a relative link `[Full runbook](./uat-runbook.md)` (Decision 2 over-threshold path, FR-013).
- Append this block after the existing `for heading in ...` loop (around line 173) and before the trailing HTML comment block (lines 175-182), so it lands once in the body.

**Autopilot-level fail-open (the composed guarantee).** The post-implementation step invokes `generate-uat-skeleton.sh` *fail-open*: a nonzero exit from the skeleton generator (e.g., exit 1 on an unreadable spec) is logged to the autopilot log but MUST NOT abort the run or block PR creation. The mechanism is compositional, not a new code path: FR-006 guarantees that on exit 1 **no partial `uat-runbook.md` is written**, so the `generate-pr-body.sh` absent-file path above fires — emitting the `## UAT Runbook` heading plus the one-line stub note, then continuing. The heading is therefore always present in the PR body regardless of whether the skeleton generator succeeded, failed, or was never run. The absent-file stub is intentionally generic (it cannot distinguish "generator failed" from "generator never ran"); the failure detail lives in the autopilot log, not in the runbook artifact. This wiring lands in `references/post-implementation.md` and its `-codex.md` twin during Implement; the contract it must honor is recorded here.

## Project Structure

### Documentation (this feature)

```text
specs/006a-uat-skeleton/
├── plan.md              # This file (/speckit-plan output)
├── spec.md              # Input (finalized; FR-001..FR-015, SC-001..SC-005)
├── research.md          # N/A — see note below
├── data-model.md        # N/A — see note below
├── quickstart.md        # Phase 1 output — standalone-run example
├── contracts/
│   └── generate-uat-skeleton-cli.md   # Phase 1 output — script CLI contract
├── checklists/          # /speckit-checklist output (later phase)
└── tasks.md             # /speckit-tasks output (NOT created here)
```

**research.md: N/A.** All technology choices and the two deferred decisions are resolved by the design concept (Q1-Q4) plus disk verification recorded above. There are no open NEEDS CLARIFICATION items and no novel technology to investigate (bash + jq + awk are established repo conventions). No `research.md` is generated.

**data-model.md: N/A.** This feature has no persistent data model — no entities, no schema, no state machine. The script is a stateless formatter: it reads `spec.md`, optionally reads a workflow file and a `UAT_PROJECT_COMMANDS` JSON string, and writes `uat-runbook.md` deterministically (overwrite, no merge). No `data-model.md` is generated.

### Source Code (repository root)

```text
speckit-pro/
├── skills/speckit-autopilot/
│   ├── SKILL.md                              # MODIFIED: Step 3 / script inventory mentions generate-uat-skeleton.sh
│   ├── scripts/
│   │   ├── generate-pr-body.sh               # MODIFIED: dedicated size-aware ## UAT Runbook block (see FR-013 Wiring)
│   │   └── generate-uat-skeleton.sh          # NEW: the skeleton generator
│   ├── templates/
│   │   └── uat-runbook-template.md           # NEW: fixed 8-section runbook template
│   └── references/
│       ├── post-implementation.md            # MODIFIED: new UAT-generation step before PR-body generation
│       └── task-list-canonical.md            # MODIFIED: task-count entry (12 → 13)
├── codex-skills/speckit-autopilot/           # LOCKSTEP (see Codex Parity below)
│   ├── SKILL.md                              # MODIFIED: mirror of CC SKILL.md script-inventory edit
│   └── references/
│       ├── post-implementation-codex.md      # MODIFIED: mirror of CC post-implementation UAT step
│       └── task-list-canonical-codex.md      # MODIFIED: mirror of task-count entry
└── tests/layer4-scripts/
    ├── test-generate-uat-skeleton.sh         # NEW: Layer 4 unit test, 5 fixtures
    └── fixtures/
        └── spec-full-snapshot.md             # NEW: vendored frozen snapshot of specs/004 spec.md (fixture data)
```

**Structure Decision:** The new script and template are **single-copy under `skills/speckit-autopilot/`** — there is NO Codex copy of the script or template. See Codex Parity below for why this satisfies FR-014.

## Codex Parity (FR-014) — reconciliation, not deviation

FR-014 requires the Claude Code and Codex autopilot variants to be edited "in lockstep." The workflow's Project Structure (line 535) reads as if every file gets a 1:1 Codex twin, but the **actual lockstep surface is narrower**, and this plan reconciles the requirement to the verified repository reality so the Analyze phase (G6) reads it as correct interpretation rather than a contradiction:

**Verified facts (disk-checked during Plan orientation):**
1. `speckit-pro/codex-skills/speckit-autopilot/` has only `SKILL.md`, `references/`, and `agents/` — **no `scripts/` dir and no `templates/` dir**. (`ls speckit-pro/codex-skills/speckit-autopilot/` → no scripts/templates.)
2. `validate-codex-parity.sh` (lines 120-151) requires: every CC skill dir has a Codex `SKILL.md` + `agents/openai.yaml` sidecar, and CC `references/` cross-links from the Codex SKILL.md resolve. It does **NOT** require Codex copies of `scripts/` or `templates/`, and does **NOT** require Codex `references/` to mirror CC reference filenames.
3. The Codex variant **invokes the shared CC script by path**: `post-implementation-codex.md` lines 113-117 and `SKILL.md` lines 781/805 call `skills/speckit-autopilot/scripts/generate-pr-body.sh` (the single shared copy). There is one script copy; both variants reference it via `../../skills/speckit-autopilot/scripts/`.
4. Codex reference files are **`-codex.md` suffixed standalone copies**, not filename-identical twins (e.g., `post-implementation-codex.md`, `task-list-canonical-codex.md`). The workflow's claim of a Codex `post-implementation.md` is inaccurate.

**Resulting lockstep surface for this spec:**
- `generate-uat-skeleton.sh` and `uat-runbook-template.md` are **single-copy under `skills/`**; the Codex variant will invoke the same shared script by its `skills/...` path, exactly as it already does for `generate-pr-body.sh`. **No Codex script/template files are created.**
- The `generate-pr-body.sh` edit is single-copy (one shared script); no Codex script edit exists to make.
- Documentation edits ARE mirrored: `SKILL.md` (both variants), the post-implementation step (`post-implementation.md` + its twin `post-implementation-codex.md`), and the task-count entry (`task-list-canonical.md` + `task-list-canonical-codex.md`).

This brings the total-file count to 11 (the 3 lockstep doc edits are the `-codex.md` twins + Codex `SKILL.md`, NOT new script/template files) and keeps the Layer 1 parity test green at every commit (no new agent files; no orphaned Codex cross-links).

## Traceability (requirement → file → verification)

| Requirement | Changed file(s) | Verification |
|---|---|---|
| FR-001 (parse US/FR/SC/Edge; argv[1]=spec, argv[2]=output; nested bullets verbatim) | `generate-uat-skeleton.sh` | Layer 4 full-spec + zero-stories fixtures; SC-001 |
| FR-002 (reuse `extract_heading_section`, copied verbatim) | `generate-uat-skeleton.sh` | Code review (provenance comment); Layer 4 heading extraction |
| FR-003 (zero-stories → FR/SC keying + header note, never skip) | `generate-uat-skeleton.sh` | Layer 4 zero-stories fixture; SC-002 |
| FR-004 (duplicate IDs → first-seen + plain stderr warning) | `generate-uat-skeleton.sh` | Layer 4 duplicate-FR fixture (assert stderr) |
| FR-005 (propagate clarification markers w/ annotation) | `generate-uat-skeleton.sh` | Layer 4 clarification-marker fixture |
| FR-006 (exit 0/2/1; silent stdout; stderr diagnostics) | `generate-uat-skeleton.sh` | Layer 4 missing-spec + usage-error fixtures (assert exit codes + empty stdout) |
| FR-007 (deterministic overwrite, no merge) | `generate-uat-skeleton.sh` | Layer 4 run-twice byte-identical assertion |
| FR-008 (`UAT_PROJECT_COMMANDS` env; placeholder when unset) | `generate-uat-skeleton.sh`, `uat-runbook-template.md` | Layer 4 fixtures with/without env set |
| FR-009 (`--workflow-file` flag; Self-Review echo via helper; stub when absent) | `generate-uat-skeleton.sh` | Layer 4 with/without `--workflow-file` |
| FR-010 (template 8-section fixed order; absent Edge Cases → header+stub; matrix anchors) | `uat-runbook-template.md`, `generate-uat-skeleton.sh` | Layer 4 section-presence assertions |
| FR-011 (static PR placeholder; no post-PR rewrite) | `uat-runbook-template.md` | Code review; Layer 4 header assertion |
| FR-012 (Rollback from `## Rollback` in spec/plan, else synthesized stanza) | `generate-uat-skeleton.sh`, `uat-runbook-template.md` | Layer 4 (spec with/without Rollback heading) |
| FR-013 (`## UAT Runbook` in PR body; `cat` under 50k, `head -60`+link otherwise) | `generate-pr-body.sh` | Code review of FR-013 Wiring block; SC-005 |
| FR-014 (CC + Codex lockstep; no new agent files) | `SKILL.md` (both), `post-implementation*.md` (both), `task-list-canonical*.md` (both) | SC-004 (`run-all.sh --layer 1`) |
| FR-015 (Layer 4 test, 5 fixtures incl. vendored snapshot) | `test-generate-uat-skeleton.sh`, `fixtures/spec-full-snapshot.md` | SC-003 (`run-all.sh --layer 4`) |
| SC-001 (run vs specs/004 → all stories present) | `generate-uat-skeleton.sh` | `grep -c '^### User Story'` parity (uses vendored snapshot in tests) |
| SC-002 (zero-stories → fallback note + FR/SC sections) | `generate-uat-skeleton.sh` | Layer 4 zero-stories fixture |
| SC-003 (`run-all.sh --layer 4` exits 0) | `test-generate-uat-skeleton.sh` | CI `pr-checks.yml` matrix |
| SC-004 (`run-all.sh --layer 1` exits 0; Codex parity) | all lockstep doc edits | CI `pr-checks.yml` matrix |
| SC-005 (`## UAT Runbook` in autopilot PR body + committed runbook) | `generate-pr-body.sh`, autopilot wiring | Post-merge autopilot smoke |

## Testing & Verification Strategy (PROJECT_COMMANDS — bash harness)

This repo is a bash harness; `detect-commands.sh` returns N/A. Use these commands:

| Purpose | Command |
|---|---|
| Unit / Layer 4 (the new test) | `cd speckit-pro && bash tests/run-all.sh --layer 4` |
| Parity / Layer 1 (Codex parity, no new agents) | `cd speckit-pro && bash tests/run-all.sh --layer 1` |
| Full verify (default L1+L4+L5) | `cd speckit-pro && bash tests/run-all.sh` |
| Script syntax (constitution II) | `bash -n speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh` + shellcheck if available |
| Standalone smoke (SC-001) | `UAT_PROJECT_COMMANDS='{"BUILD":"make","UNIT_TEST":"make test"}' bash speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh specs/004-integration-verification/spec.md /tmp/smoke-runbook.md` |

**TDD-first (bash flavor):** for each script behavior — add the failing Layer 4 assertion (RED), implement the minimum script logic (GREEN), tidy while green (REFACTOR), then smoke against the vendored fixture (VERIFY). Layer 4 fixtures: one vendored `spec-full-snapshot.md` (read from `fixtures/`, never live) + four inline `mktemp` specs (zero-stories, duplicate-FR, clarification-marker, missing-spec).

## Complexity Tracking

> No constitution violations. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |
