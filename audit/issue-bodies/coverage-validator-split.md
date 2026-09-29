Priority: major

## Summary

validate-autopilot-phase-coverage.py is a 5,334-line script with one 1,860-line function, and it carries its own copy of the runner's JSON Schema validator with fewer keywords. Other runner modules also hand-roll their schemas, and the architecture-graph schema documents less than its validator enforces. A test imports another test file and the validator's private helpers, so its 'independent' oracle is not independent.

## Evidence

- **autopilot-and-agents-008** (major): validate_projection_integrity is one function of about 1,860 lines inside a 5,334-line script that also does schema validation, git history checks, path sandboxing, privacy scanning and autonomy authorization. It is one caller (build_report) and untestable in parts.
  - `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:2543-4409`, `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:5165`
- **pr-emission-and-stack-2-009** (minor): The test imports another test file (test-autopilot-phase-coverage.py) as a library and calls the validator's private _canonical_json_sha256 and _sha256_bytes. Its 'private_record_matches' oracle then uses the same function the validator uses, so the docstring's 'recomputes independently' is not true.
  - `tests/speckit-pro/unit/test-autonomy-boundary-receipt-replay.py:36`, `tests/speckit-pro/unit/test-autonomy-boundary-receipt-replay.py:48`, `tests/speckit-pro/unit/test-autonomy-boundary-receipt-replay.py:50`, `tests/speckit-pro/unit/test-autonomy-boundary-receipt-replay.py:141`
- **autopilot-and-agents-007** (minor): The shipped validator carries verbatim copies of three JSON-schema helpers that also live in the runner's read_only.py. The two copies can drift, and the validator's docstring calls it a Codex-only script although both hosts run it.
  - `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:1398`, `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:1406`, `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:1423`, `speckit-pro/speckit_pro_runner/helpers/read_only.py:7004`, `speckit-pro/speckit_pro_runner/helpers/read_only.py:7016`, `speckit-pro/speckit_pro_runner/helpers/read_only.py:7030`
- **runner-core-004** (minor): Two hand-written JSON Schema validators exist. The runner's supports patternProperties, propertyNames, maxLength, maximum, exclusiveMinimum, prefixItems, dependentRequired and maxProperties; the autopilot script's copy supports none of these. The type and equality helpers are byte-level clones, so the copies can drift silently.
  - `speckit-pro/speckit_pro_runner/helpers/read_only.py:6778-7016`, `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:1439-1610`
- **runner-core-005** (minor): architecture_graph.py, gate_discovery.py and quality_gates.py each re-implement their JSON schema by hand instead of using the generic validator. The arch-graph schema documents less than the validator enforces: kind=pr requires base and a non-empty touched list, and kind=repository forbids them, but the schema declares only kind as required. A graph valid per the schema fails validation. The parity tests compare enums and required lists only.
  - `speckit-pro/speckit_pro_runner/contracts/architecture-graph.schema.json:12-17`, `speckit-pro/speckit_pro_runner/architecture_graph.py:63-71`, `speckit-pro/speckit_pro_runner/gate_discovery.py:1-6`

## Proposed fix

- autopilot-and-agents-008: Split the function by checkpoint kind and move schema, git and path helpers into separate modules.
- pr-emission-and-stack-2-009: Move the shared builders to tests/speckit-pro/lib, and compute the digest in the test with hashlib over the documented canonical form.
- autopilot-and-agents-007: Share one stdlib module under plugin scripts/lib (per the shared-lib rule) or record why the copy is intentional and add a drift test.
- runner-core-004: Have the script import the runner validator (both ship in the plugin), or document the intentionally smaller keyword subset and test that both agree on it.
- runner-core-005: Add if/then rules to the schema for kind=pr and kind=repository, and extend the parity test to run schema and validator over the same good and bad fixtures.

## Acceptance

- [ ] validate_projection_integrity is split by checkpoint kind; schema, git and path helpers live in their own modules.
- [ ] The script uses the runner validator (or one shared module in plugin scripts/lib).
- [ ] The architecture-graph schema encodes the kind=pr and kind=repository rules; a parity test runs schema and validator over the same fixtures.
- [ ] The receipt-replay test computes its digest independently.
- [ ] Runner trust metadata and dist/ are regenerated; both suites pass.

## Related

- Overlaps files changed by the open stop-policy stack: #850, #852. Land after that stack merges.
- Overlaps files changed by open PR #685.
- Depends on #874

Found by the 2026-09 coherence audit.
