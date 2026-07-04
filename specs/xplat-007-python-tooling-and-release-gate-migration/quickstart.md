# Quickstart: Python Tooling and Release-Gate Migration

## Prerequisites

- Python 3.11+ available as the interpreter used for the runner.
- Run commands from the repository root.
- Do not install new packages, restore a virtualenv, use `jq`, or invoke Bash
  helper scripts for promoted gates.

## 1. Source-Checkout Runner Smoke

Use the existing runner smoke request to prove the source-checkout runner
launches and emits the JSON envelope:

```bash
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/smoke-runtime-info-request.json
```

Then run preflight after any runner manifest/checksum update:

```bash
printf '%s\n' '{"schema_version":"1.0","request_id":"xplat-007-preflight-smoke","helper_id":"runner","operation":"preflight","mode":"read_only","inputs":{}}' | PYTHONPATH=speckit-pro python3 -m speckit_pro_runner
```

Expected outcome:

- stdout is one JSON response
- `status` is `ok`
- `data.report.source_vs_installed_context` is `source_checkout`
- preflight validates runner source metadata, including manifest/checksum
  consistency
- no installed-cache or native UAT claim is made

## 2. Run Python Test/Eval Gates

After Slice 1 implementation, run the migrated default suite through the runner:

```bash
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-default-suite.json
```

Expected outcome:

- active test/eval gate result is reported in the runner response
- legacy Bash output is represented only as parity evidence until promotion
- promoted gates have matching promotion records

## 3. Run The Active No-Shell Guard

After Slice 3 implementation, run:

```bash
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/active-path-guard.json
```

Expected clean outcome:

- `status` is `ok`
- `data.blocking_count` is `0`
- nonblocking findings are classified as archive/provenance, temporary parity
  evidence, consumer Spec Kit helper, generated payload mirror, docs out of
  scope, CI dispatch glue, or XPLAT-008 cutover surface

Expected failure fixture outcome:

- `status` is `expected_failure`
- exit code is `1`
- `data.findings[]` includes `path`, `line`, `category`, `pattern`, `reason`,
  `active_role`, `classification`, and `remediation`

## 4. Rebuild Test Payload Evidence Only

After Slice 2 implementation, run:

```bash
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/test-payload-evidence.json
```

Expected outcome:

- Claude/Codex test payload evidence is written only to fixture or temporary
  output roots
- fingerprints and file-tree evidence are recorded
- `release_payload_cutover` remains `false`

## 5. Verify Install And Release Readiness

Use runner operations for fixture-bound install verification and release checks.
Requests should use fake-home roots and stubbed CLIs:

```bash
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/install-verification.json
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/release-readiness.json
```

Expected outcome:

- no real `HOME` or installed plugin cache is mutated
- bundled-agent inventory and version consistency are checked from fixtures
- stale marketplace/version, payload evidence, release-PR payload-sync, or
  post-release drift evidence blocks release readiness

## XPLAT-008 Exclusions

Do not use XPLAT-007 commands as proof of:

- active Claude/Codex skill, hook, agent, or install invocation cutover
- generated release payload selection or publication
- public install/runtime docs or release notes
- native Windows/macOS/Linux installed-plugin UAT
- update, safe repair, autoheal, or public release readiness

Those are XPLAT-008 responsibilities.
