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
export PATH=/Users/fredrickgabelmann/.local/share/uv/tools/specify-cli/bin:$PATH
```

## Scenario 1: Single-PR packet passes validation

1. Render a single-PR packet for `specs/prsg-012-reviewer-ready-pr-packet-contract`.
2. Validate the packet before PR creation.
3. Confirm validation writes:
   `specs/prsg-012-reviewer-ready-pr-packet-contract/.process/pr-packets/<packet_id>/validation.json`.

Expected outcome:

- The title renders as `feat(speckit-pro): <plain-English action phrase>`.
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
- No `gh pr create` command is attempted.

## Scenario 4: Missing body evidence blocks before PR creation

1. Render or seed a body missing verification evidence, scope evidence, source markers, or a required heading.
2. Run packet validation.

Expected outcome:

- Validation status is `failed`.
- The failure names the missing section or field.
- The validation JSON includes the body path and remediation evidence.
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

## Verification Commands

```bash
bash tests/speckit-pro/run-all.sh --layer 1
bash tests/speckit-pro/run-all.sh --layer 4
bash tests/speckit-pro/run-all.sh
```

Expected outcome:

- Layer 1 passes structural validation.
- Layer 4 passes validator, PR body, and multi-PR emission fixture tests.
- The default deterministic suite passes without requiring AI-eval layers.

## Contract References

- Packet shape: [contracts/pr-packet.schema.json](contracts/pr-packet.schema.json)
- Entity model: [data-model.md](data-model.md)
