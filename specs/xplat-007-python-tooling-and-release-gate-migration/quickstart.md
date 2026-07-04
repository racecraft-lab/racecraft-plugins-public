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

US1 suite gates are runner-envelope operations. The default request covers the
toolchain preflight plus Layers 1, 4, 5, 7, and 8:

```bash
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-default-suite.json
```

Focused suite requests are also available:

```bash
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-toolchain-preflight.json
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-layer.json
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-ai-evals.json
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-integration-suite.json
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-parity-suite.json
```

Expected outcome:

- stdout is one JSON runner response
- stderr contains only line-delimited runner diagnostics when a gate is not
  green
- command stdout, stderr, argv, exit code, and duration are captured under
  `data.suite.results[]`
- Layer 2, Layer 3, and Layer 6 eval dispatch reports stable
  `missing_prerequisite` diagnostics when local eval runners are unavailable
- retained Bash references are recorded as inactive parity evidence in
  `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/promotion-records.json`

US1 does not:

- migrate payload, install, marketplace/version, release, or release-readiness
  helper behavior
- clean up workflow shell or active-path guard findings
- cut over Claude/Codex installed invocation paths
- rebuild or publish generated release payloads
- claim native installed-plugin UAT or public platform support

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

The checked-in request runs `build-test-payload-evidence` in `read_only` mode
against `payload-evidence-cases.json`. Focused test coverage also exercises
`dry_run` and fixture-scoped `apply` output roots; `apply` is limited to
`tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/` or OS temp roots.

Expected outcome:

- Claude/Codex test payload evidence is written only to fixture or temporary
  output roots
- fingerprints and file-tree evidence are recorded
- `release_payload_cutover` remains `false`

Non-goals:

- selecting generated release payloads
- publishing marketplace payloads
- changing active Claude/Codex installed invocation paths

## 5. Verify Install And Release Readiness

Use runner operations for fixture-bound install verification and release checks.
Requests should use fake-home roots and stubbed CLIs:

```bash
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/install-verification.json
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/release-readiness.json
```

The install request runs `verify-install` against
`install-verification-cases.json`. Unit coverage also exercises
`refresh-local-plugin-fixture` in `dry_run` mode for safe repair plans, Windows
style paths, spaces, traversal rejection, and line-ending normalization.

The release request runs the `release-readiness` aggregate against
`release-readiness-cases.json`. The aggregate covers:

- `detect-changed-plugin`
- `aggregate-suite-results`
- `check-marketplace-version-sync`
- `validate-pr-title`
- `validate-workflow-contract`
- `check-payload-evidence`
- `parse-release-pr-payload-sync`
- `check-post-release-drift`
- `release-readiness`

Expected outcome:

- no real `HOME` or installed plugin cache is mutated
- bundled-agent inventory and version consistency are checked from fixtures
- stale marketplace/version, payload evidence, release-PR payload-sync, or
  post-release drift evidence blocks release readiness

Non-goals:

- native installed-plugin UAT
- real installed-cache repair
- generated release payload cutover
- public release readiness claims

## XPLAT-008 Exclusions

Do not use XPLAT-007 commands as proof of:

- active Claude/Codex skill, hook, agent, or install invocation cutover
- generated release payload selection or publication
- public install/runtime docs or release notes
- native Windows/macOS/Linux installed-plugin UAT
- update, safe repair, autoheal, or public release readiness

Those are XPLAT-008 responsibilities.
