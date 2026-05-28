# CLI Contract: `generate-uat-skeleton.sh`

The script IS the API surface this spec ships. The autopilot post-implementation
phase (both Claude Code and Codex variants) invokes it by exact name and path;
if this contract drifts, every future autopilot run breaks. No runtime-specific
behavior may leak in — the contract is identical for both variants.

**Path:** `speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh`

## Invocation

```text
generate-uat-skeleton.sh <spec-path> <output-path> [--workflow-file <path>]
```

```bash
# Autopilot (real run): env carries detected commands, workflow file supplied
UAT_PROJECT_COMMANDS="$commands_json" \
  generate-uat-skeleton.sh \
    specs/006a-uat-skeleton/spec.md \
    specs/006a-uat-skeleton/uat-runbook.md \
    --workflow-file docs/ai/specs/SPEC-006a-workflow.md

# Standalone (maintainer): no env, no workflow file — degrades gracefully
generate-uat-skeleton.sh specs/004-integration-verification/spec.md /tmp/runbook.md
```

## Positional arguments (FR-001, Clarify S1)

| Position | Name | Required | Meaning |
|----------|------|----------|---------|
| `argv[1]` | spec path | yes | Path to the source `spec.md` to parse. |
| `argv[2]` | output path | yes | Path to write the runbook. Overwritten deterministically (FR-007). |

- The **feature directory is derived** via `dirname "$argv[1]"`. No `--feature-dir` or `--spec-id` argument exists.
- **No additional positional arguments** are accepted. A third positional (or any unrecognized token that is not the `--workflow-file` flag pair) is a usage error → exit 2.

## Flags (FR-009, Design Concept Q3)

| Flag | Argument | Required | Meaning |
|------|----------|----------|---------|
| `--workflow-file` | `<path>` | optional | Path to the autopilot workflow file. When supplied, the `## Self-Review` block is extracted via the copied `extract_heading_section()` helper and echoed into the runbook's Self-Review Findings section. |

- When the flag is **absent**, or the file is unreadable, or the file lacks a `## Self-Review` heading: the Self-Review Findings section emits the stub line `**Self-Review:** <not available — workflow file not provided>` and the script **still succeeds** (exit 0). The autopilot always supplies the path in real runs; standalone runs degrade gracefully.
- `--force` does **NOT** exist (FR-007 — overwrite is unconditional and deterministic; no skip-if-present, so no force toggle is needed). YAGNI.

## Environment variables (FR-008, Design Concept Q2)

| Variable | Type | Required | Meaning |
|----------|------|----------|---------|
| `UAT_PROJECT_COMMANDS` | JSON string | optional | The same JSON the autopilot discovers via `detect-commands.sh` in its setup step. The Env Setup section is a pure formatter over this JSON. |

**Key schema (FR-008):** the formatter draws from the established key set `detect-commands.sh` produces — `BUILD`, `TYPECHECK`, `LINT`, `LINT_FIX`, `UNIT_TEST`, `INTEGRATION_TEST`, `SINGLE_FILE_INTEGRATION`. Which of these keys surface as Env Setup rows is a formatting detail left to Plan/implementation.

- When **unset** (e.g., standalone invocation), the Env Setup section emits `<unknown — autopilot did not pass PROJECT_COMMANDS>` placeholders rather than failing.
- When **set but malformed** (not parseable by `jq`), the script degrades to the same placeholders rather than crashing (fail-soft). It does not abort.
- When a key is **present with the literal value `N/A`** (detect-commands.sh's sentinel for an undetected command), the Env Setup section renders that command as unavailable for this project — distinct from the unset-variable placeholder above.
- The script does **NOT** re-run `detect-commands.sh` itself (keeps it a pure formatter; keeps Layer 4 tests trivial — a fixture JSON, no shelling out).

## Exit codes (FR-006, Clarify S1)

| Code | Condition |
|------|-----------|
| `0` | Success — the output runbook was written. |
| `2` | Usage error — wrong/missing argv (missing `argv[1]` or `argv[2]`, unknown flag, extra positional). |
| `1` | Unreadable or missing spec at `argv[1]` — **no partial runbook is produced** (the output file is not created/written on this path). |

Exit-code precedence: argv/usage validation (→ 2) happens **before** the spec readability check (→ 1). A missing Self-Review source or unset `UAT_PROJECT_COMMANDS` is **never** an error — those degrade to stubs/placeholders and still exit 0.

## Output streams (FR-006, Clarify S1)

| Stream | Contents |
|--------|----------|
| **stdout** | **Silent on success.** The script writes only the output runbook file and emits nothing to stdout — matching `generate-pr-body.sh`. |
| **stderr** | Diagnostics and warnings only. Warnings are **plain, unprefixed, human-readable** messages (matching `confidence-gate.sh` / `generate-pr-body.sh` stderr style). **No** machine-readable tag prefix (no `[UAT-WARN]`) — Clarify S1 confirmed no consumer greps a tag and no bracket-tag convention exists in the codebase. |

**stderr warning triggers (non-fatal — script continues, exit 0):**
- **FR-004 duplicate FR/SC ID:** emit the first-seen entry only; write a plain stderr line naming the duplicated ID (e.g., `duplicate requirement ID FR-005; keeping first-seen entry`).
- (Clarification markers per FR-005 are propagated **into the runbook** with an annotation, not to stderr.)

## Side effects

- Writes (overwrites) exactly one file: `argv[2]`. Deterministic — two runs against an unchanged spec produce byte-identical output (FR-007, US3). No merge, no append, no skip-if-present.
- Reads: `argv[1]` (spec), optionally the `--workflow-file` path, optionally `plan.md` in the same feature dir as a Rollback fallback (FR-012), and the `UAT_PROJECT_COMMANDS` env var.
- Does not write to stdout, does not modify the spec, does not create a PR, does not touch git.

## Consumer contract (downstream)

- `generate-pr-body.sh` reads `<feature-dir>/uat-runbook.md` and embeds a `## UAT Runbook` (H2) section: full content via `cat` when under 50,000 chars, else `head -60` + a relative link (FR-013). The exact literal heading `## UAT Runbook` is load-bearing — SC-005 greps for it.
- The autopilot invokes this script during post-implementation, **after Self-Review and before PR creation**, supplying both the workflow-file path and `UAT_PROJECT_COMMANDS` in real runs. The PR URL is unknown at this point, so the runbook Header uses a static placeholder (FR-011, Q1) — the autopilot does NOT rewrite the runbook after PR creation.
