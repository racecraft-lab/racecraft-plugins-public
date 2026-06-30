# Platform Runbook Fixture Contract

## Purpose

Define the deterministic Windows/Linux runbook fixture evidence XPLAT-004 may
produce without claiming installed-cache readiness, native matrix UAT, release
readiness, or public platform support.

## Required Fields

Each fixture row MUST include:

- `fixture_id`: Stable identifier for the runbook fixture.
- `platform_family`: `windows` or `linux`.
- `evidence_context`: `source_checkout` for XPLAT-004.
- `launcher_command_family`: Launcher family under test, such as
  `py -3.11`/`python`/`python3` on Windows or `python3`/`python` on Linux.
- `request_kind`: `runtime-info` or `preflight`.
- `expected_status`: Expected runner status when a runner response exists.
- `expected_exit_code`: Expected process exit code when the runner starts, or
  `null` for host-level Python launcher failure before runner stdout exists.
- `expected_diagnostic_codes`: Stable diagnostic codes expected from the
  fixture, including `python_launcher_unavailable` when no Python 3.11+
  launcher can start the runner.
- `metadata_verification_status`: Expected metadata state: `verified`,
  `mismatch`, `missing_metadata`, `incomplete_metadata`, or `not_checked`.
- `non_claim_statement`: Required text stating the fixture is source-checkout
  guidance only and does not prove installed-cache launch, full native UAT,
  release-readiness, or public platform support.

## Rules

- Fixtures MUST label `source_checkout` context explicitly.
- Fixtures MUST NOT use `installed_cache` context in XPLAT-004.
- Fixture prose MUST NOT say or imply native Windows/Linux support is ready for
  public claims.
- Host-level Python launcher failures MUST NOT claim a runner stdout response;
  they are recorded as discovery/runbook evidence with deterministic
  remediation.
- XPLAT-007 owns installed-cache launch proof, generated payload propagation,
  native Windows/macOS/Linux UAT, release-readiness, and public claim audit.
