# Quickstart: XPLAT-005 Read-Only Helper Port

## Prerequisites

- Source checkout of `racecraft-plugins-public`
- Python 3.11+
- Existing Bash helper scripts available only for source-checkout parity comparisons
- No package install, virtualenv restore, network access, `jq`, Node, PowerShell, Go, Rust, or Zig required by promoted Python helper execution

## 1. Run The Source-Checkout Runner Smoke

```bash
printf '%s\n' '{"schema_version":"1.0","request_id":"xplat-005-smoke","helper_id":"runner","operation":"runtime-info","mode":"read_only","inputs":{}}' | PYTHONPATH=speckit-pro python3 -m speckit_pro_runner
```

Expected result:

- One JSON stdout response
- `status` is `ok`
- `source_vs_installed_context` is `source_checkout`
- Runtime and plugin-relative metadata are present

This smoke does not prove installed-cache launch, active Claude/Codex invocation, generated payload propagation, helper parity, mutation-helper safety, or full native Windows/macOS/Linux support.

## 2. Run Helper Parity Tests

```bash
python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py
```

Expected result:

- Every promoted helper passes its golden fixtures
- Every promoted Bash-backed helper passes source-checkout Bash-reference comparison
- Every applicable rejected-input failure class has a fixture with expected stdout schema when machine-readable output exists, deterministic remediation content when diagnostics are emitted, and exact nonzero exit mapping
- JSON stdout is compared semantically
- Stderr diagnostics and exit codes match exactly unless an explicit normalization rule applies

## 3. Run Focused Layer 4

```bash
bash tests/speckit-pro/run-all.sh --layer 4
```

Expected result:

- Existing runner tests still pass
- Read-only helper parity tests pass
- No mutation-helper or active cutover tests are required for XPLAT-005

## 4. Run The Default Deterministic Gate

```bash
bash tests/speckit-pro/run-all.sh
```

Expected result:

- Layers 1, 4, and 5 pass
- Plugin structure remains valid
- No new Bash script safety surface is introduced

## 5. Confirm Scope Boundaries

Review the implementation diff and confirm:

- No active Claude Code or Codex skill, hook, generated payload, install, marketplace, or public-doc cutover edits
- No mutation-helper ports for PR body generation, PR emission, split state, restack, relocation, install repair, autoheal, or repository/user-local writes
- `generate-spec-index` is covered only in `--check` mode
- `plan-layers` excludes marker-plan output
- `validate-pr-packet` covers read-only validation output, diagnostics, and exit codes only
- Python helper ports and Bash-reference harnesses use argv-list subprocess calls only and do not use `shell=True`, shell-command strings, `os.system`, or shell interpolation
- Filesystem inputs resolve relative components and symlinks against repo/plugin trust boundaries and reject traversal or symlink escapes before reading

## 6. Review Promotion Evidence

Use the promotion matrix in `plan.md` and the schema in `contracts/helper-promotion-record.schema.json`.

Expected result:

- Every XPLAT-005 helper is listed as `python_authoritative`, `bash_reference_only`, or `out_of_scope`
- `python_authoritative` helpers have fixture ids, Bash comparison ids when Bash-backed, failure-class mappings, normalized fields, subprocess/path-boundary policies, an authoritative test command, and deferred follow-up notes
- Out-of-scope helpers point to XPLAT-006 or XPLAT-007 as appropriate
