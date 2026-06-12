# Quickstart: Reviewer-ready PR packet contract

## Purpose

Use this guide during implementation to prove that autopilot creates only validated, reviewer-ready PR packets before `gh pr create`.

## Prerequisites

- Bash 4+
- `jq`
- `git`
- `gh`
- `specify` available on PATH when running SpecKit commands:

```bash
export PATH="${SPECIFY_CLI_BIN:-$HOME/.local/share/uv/tools/specify-cli/bin}:$PATH"
```

## Scenario 1: Single-PR packet passes validation

1. Render a single-PR packet for `specs/prsg-012-reviewer-ready-pr-packet-contract`.
2. Validate the packet before PR creation.
3. Confirm validation writes:
   `specs/prsg-012-reviewer-ready-pr-packet-contract/.process/pr-packets/<packet_id>/validation.json`.

Expected outcome:

- The title renders as `feat(PRSG-012): <plain-English action phrase>` for this spec. Future spec-backed packets use their own derived spec scope, and non-spec plugin packets may fall back to `feat(speckit-pro):`.
- The body contains `Summary`, `What Changed`, `Why It Matters`, `How To Review`, `How To UAT`, `Verification`, `Scope`, and `Known Gaps`.
- The body still contains the literal `## UAT Runbook` heading.
- Validation status is `passed`.
- PR creation uses `gh pr create --base "$base_branch" --head "$head_branch" --title "$title" --body-file "$body_file"`.

## Scenario 2: Split-PR packets validate independently

1. Render split packets from marker mode.
2. Validate each packet separately.
3. Inspect each packet's validation result path.

Expected outcome:

- Each split title description comes from `source_boundary.section`.
- Slice IDs and branch names remain metadata only.
- One invalid packet blocks only its own PR creation attempt and records packet-specific remediation evidence.

## Scenario 3: Invalid title blocks before PR creation

1. Seed a packet title description containing an internal token such as a PRSG ID, slice ID, stale placeholder, unexpanded variable, or banned label.
2. Run packet validation.

Expected outcome:

- Validation status is `failed`.
- `pr_blocked` is `true`.
- Remediation evidence names the title rule, packet target, and rejected text.
- Workflow evidence is appended to `docs/ai/specs/.process/PRSG-012-workflow.md` with the packet id, validation result path, deterministic stderr line, remediation summary, and resume boundary.
- No `gh pr create` command is attempted.

## Scenario 4: Missing body evidence blocks before PR creation

1. Render or seed a body missing verification evidence, scope evidence, source markers, or a required heading.
2. Run packet validation.

Expected outcome:

- Validation status is `failed`.
- The failure names the missing section or field.
- The validation JSON includes the body path and remediation evidence.
- Workflow evidence is appended to `docs/ai/specs/.process/PRSG-012-workflow.md` with a deterministic event id that can be superseded on retry.
- PR creation is blocked before any networked GitHub action.

## Scenario 5: Safe prose refinement is allowed

1. Edit only the content between exact full-line editable markers under `Summary`, `What Changed`, or `Why It Matters`.
2. Re-run validation.

Expected outcome:

- The protected-body fingerprint still matches after editable blocks are elided.
- Validation status is `passed`.

## Scenario 6: Protected body changes are rejected

1. Remove or change a source marker, UAT content, scope evidence, verification evidence, known-gap text, or generated governance section.
2. Re-run validation.

Expected outcome:

- The protected-body fingerprint check fails.
- Validation status is `failed`.
- Remediation evidence points to the protected invariant that changed.

## Scenario 7: Missing or malformed packet input is an input error

1. Run validation with a missing packet path, unreadable packet path, invalid JSON file, and schema-invalid packet file.
2. Inspect stdout, stderr, and any validation result path created under `.process/pr-packets/_input-error-<stable-hash>/validation.json`.

Expected outcome:

- The validator exits `2`.
- The validation result uses `error_class: input_error`, `exit_code: 2`, and `pr_blocked: true`.
- Stderr is one deterministic line in the documented `validate-pr-packet.sh: input_error: ...` shape.
- Workflow evidence uses the synthetic input-error identity and records either the input-error validation result path or `no-path`.
- No `gh pr create` command is attempted.

## Scenario 8: Split-PR resume preserves earlier opened PRs

1. Seed a split run where packet 1 has already opened a PR and packet 2 fails validation.
2. Confirm state before fixing packet 2.
3. Fix packet 2 and rerun validation/emission from the failed packet.

Expected outcome:

- Packet 2 writes failed validation JSON with resume evidence pointing to packet 2.
- Existing packet 1 PR evidence remains in `.process/prs.json`, the Spec MOC PRS table, `docs/ai/specs/.process/PRSG-012-workflow.md`, and `autopilot-state.json`.
- Resume reconciles the existing packet 1 PR before retrying packet 2.
- No duplicate `gh pr create` command is attempted for packet 1.

## Default Verification Commands

```bash
bash tests/speckit-pro/run-all.sh --layer 1
bash tests/speckit-pro/run-all.sh --layer 4
bash tests/speckit-pro/run-all.sh
```

Expected outcome:

- Layer 1 passes structural validation.
- Layer 4 passes validator, PR body, input-error, resume, and multi-PR emission fixture tests.
- The default deterministic suite passes without requiring AI-eval layers.

## Extended Evidence Commands

```bash
bash tests/speckit-pro/layer3-functional/run-functional-evals.sh speckit-autopilot
bash tests/speckit-pro/layer3-functional/run-functional-evals-codex.sh speckit-autopilot
bash tests/speckit-pro/layer7-integration/run-dispatch-fixtures.sh 18-post-impl-parallel-subagents
bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run --fixture 01-post-impl-parity
```

Expected outcome:

- Layer 3 Claude Code and Codex eval expectations include packet generation, validation before PR creation, `--base`/`--head`/`--title`/`--body-file` usage, deterministic blocked evidence, and no post-create repair fallback.
- Layer 7 replay evidence covers post-implementation ordering: render packet, validate packet, append workflow event on failure, and call `gh pr create` only after a passing validation result.
- Layer 8 dry-run validates the post-implementation parity fixture structure; live parity remains developer-local and opt-in because it runs full autopilot paths.

## Contract References

- Packet shape: [contracts/pr-packet.schema.json](contracts/pr-packet.schema.json)
- Entity model: [data-model.md](data-model.md)
