# Contract: Status-Evidence Guard

## Command

```bash
python3 speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py --workflow <workflow> --state <workflow-dir>/autopilot-state.json --rule status-evidence
```

## Inputs

- `--workflow`: Path to the workflow Markdown file being validated.
- `--state`: Path to the adjacent `autopilot-state.json` file for the active run.
- `--rule status-evidence`: Scope the process exit code to the status-evidence rule while preserving the complete JSON report.

## Exit Code Contract

- Exit `0` when no problem key selected by `status-evidence` has findings.
- Exit `1` when any selected `status-evidence` problem key has findings.
- Continue emitting the full JSON report before returning the scoped exit code.

## Required Blocking Keys

The status-evidence rule must include the existing status-evidence keys and exactly these ART-017 additions:

- `in_progress_errors`
- `duplicate_state_steps`
- `state_order_errors`

The rule must not newly include legacy coverage keys such as:

- `missing_state_prefixes`
- `missing_state_post_items`

## Report Shape Contract

The JSON report remains an object with existing metadata fields and list-valued diagnostic fields. ART-017 must not rename, remove, or hide existing problem keys. Scoped rule execution changes only process exit authority and the three updated intent verdicts.

Required metadata fields:

- `status`
- `workflow_file`
- `state_file`
- `plan_step_count`

Required diagnostic behavior:

- All diagnostic keys continue to appear in the report when the validator produces them.
- Non-member diagnostic keys remain report-only under `--rule status-evidence`.
- Each of the three ART-017 keys can independently make the command exit `1`.

## Workflow/State Pair Corpus Contract

A tracked corpus pair is valid only when:

- The workflow file is tracked by git.
- The adjacent `autopilot-state.json` file is tracked by git.
- Both files are in the same directory.
- The state's repo-relative `workflow_file` value exactly equals the workflow repo-relative path.

The corpus regression must exclude workflows with no adjacent tracked state, states that name another workflow, and any synthesized state file.
