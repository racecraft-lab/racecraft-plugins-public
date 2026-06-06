# Project Memory: Implementation Plans

Durable, distilled record of merged feature implementation plans — dependencies,
structure, configuration, and test strategy. Appended per archived feature.

---

## Artifact relocation — tiering, .process/, collapse

[Source: specs/007-artifact-relocation]
**Branch**: `007-artifact-relocation` · **Status**: Completed · **Archived**: 2026-06-05

### Dependencies & Versions

- **Language/Runtime**: Bash (macOS/Linux) + `jq` for JSON. Python 3 only where
  `ensure-reviewability-preset.sh` already uses it (its heredoc). No compiled
  runtime — this is a Claude Code plugin marketplace, not an application.
- **Primary dependencies**: `git` (linguist reads repo-root `.gitattributes`),
  `jq`, GitHub linguist (`linguist-generated` collapse mechanism). No package
  manager, no Node/Rust/Go build.
- **Storage**: Files on disk. No database, no persisted state. Relocated exhaust
  lives under `docs/ai/specs/.process/` and `specs/<NNN>/.process/`.

### Architecture / Approach

- **US1 (redirect)**: path-string edits in markdown skill files plus identical
  mirrors in the Codex skill counterparts — no new abstraction layer.
- **US2 (collapse + gate + lint)**: one new repo-root `.gitattributes` rule
  (`**/.process/** linguist-generated=true`), one idempotent append into the
  consuming project's `.gitattributes` (folded into the existing scaffold-time
  `ensure-reviewability-preset.sh`, NOT a new script), one new `case` arm in the
  gate's `is_excluded_generated()`, and one new Layer-1 structural lint proving
  every `linguist-generated` rule is scoped to `.process/`.
- US2 is inert until US1 writes under `.process/`, so US1 sequences first.

### Files Touched (production)

- `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` + Codex mirror
  `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md` — redirect scaffold
  exhaust to `docs/ai/specs/.process/`.
- `speckit-pro/skills/speckit-coach/templates/workflow-template.md` — self-ref
  redirects.
- `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh` — repoint UAT
  read path + link to `specs/<NNN>/.process/`; keep `## UAT Runbook` rendering.
- `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` —
  UAT generator output path + git add → `.process/`.
- `.gitattributes` (NEW repo root) — single `**/.process/** linguist-generated=true`
  rule.
- `speckit-pro/skills/speckit-coach/scripts/ensure-reviewability-preset.sh` —
  idempotent safe-write append of the rule to the consumer's `.gitattributes`.
- `speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh` — one new
  `is_excluded_generated()` arm for `/.process/`.

### Configuration Changes

- New repository-root `.gitattributes` collapse rule (linguist-generated, NOT
  `-diff`). Mirrored idempotently into consumer repos by the scaffold ensure-step.

### Consumer `.gitattributes` Safe-Write (consensus-pinned)

The consumer ensure-step MUST:
1. Detect presence with `grep -qxF "$rule" "$file"` — fixed-string (`-F`, the rule
   contains `*` glob metacharacters), whole-line (`-x`) match; short-circuit if
   already present.
2. Normalize the trailing newline before appending (if last byte ≠ `\n`, add one)
   so the rule never silently concatenates onto the last existing line.
3. Write atomically: copy existing content into a SAME-DIRECTORY temp file
   (`mktemp "${file}.XXXXXX"` — same dir keeps `mv` atomic on macOS), append the
   rule, then `mv` over the target; `trap 'rm -f "$tmp"' EXIT` to avoid orphans.

~10 LOC, matches the repo's temp-then-rename convention, adds no new
script/abstraction (constitution Principle VI).

### Test Strategy

- Shell-script test layers via `bash speckit-pro/tests/run-all.sh`. CI runs
  Layers 1 (structural), 4 (script unit), 5 (tool scoping).
- NEW Layer-1 lint: `tests/layer1-structural/validate-process-gitattributes.sh`
  (modeled on `validate-pr-checks-sentinel.sh`), registered in the run-all.sh L1
  array — proves SC-005.
- EXTENDED `tests/layer4-scripts/test-reviewability-gate.sh` — diff-mode:
  `.process/` excluded, spec counted (SC-003).
- EXTENDED `tests/layer4-scripts/test-ensure-reviewability-preset.sh` —
  idempotency + safe-write of the consumer append (SC-004).
- Codex parity covered by the existing `validate-codex-skills.sh` + Layer-8 parity
  fixtures (SC-006).

### Constitution Compliance

PASS on all core principles (I–VI). One declared **split exception** for the
reviewability surface budget: the gate's `surface_for_path()` heuristic computes
≥2 primary surfaces purely from filenames (`workflow-template.md` → false
"scheduler/runtime"; `*.md` → "docs/process"; `.sh`/`.gitattributes` → "other"),
tripping the ">1 primary surface" blocker. This is one logical surface (the
speckit-pro PR-exhaust pathway) artificially sharded by filename patterns;
splitting US1/US2 would not lower the count (each half still touches `.sh` + `.md`).
The constitution-sanctioned `split exception` was ratified in plan.md (grepped by
the gate to clear the block). Not a core-principle violation.

### Known Gaps / Notes

- A pre-existing dead-code arm in the gate (`docs/ai/workflows/*/exports/*`, a
  directory that does not exist) was left untouched per the surgical-edit rule
  (mention, do not delete).
- `data-model.md`, `contracts/`, and `quickstart.md` were correctly N/A (no data
  model, no API, no user-facing runtime).
- Authoritative design rationale lived at `docs/ai/specs/PRSG-001-design-concept.md`
  (four-agent grounding pass + Q&A log); `research.md` was a thin pointer to it.
