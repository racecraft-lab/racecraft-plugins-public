Priority: minor

## Summary

The quality-gates schema and guide say complexity and CRAP thresholds apply per changed function, while the gates judge every function in each changed file. The gate-tooling decision record states a threshold, fallback, slot set and TypeScript toolchain that the code no longer uses. The egress detector misses govulncheck and the hyphenated cargo-audit, which the shipped dependency-audit table uses.

## Evidence

- **brokers-and-verification-010** (minor): The schema descriptions and the guide's field table say the complexity and CRAP thresholds apply 'per changed function', but the same guide says the gates judge every function in each changed file, and crap-score.py checks every function in the paths it is given.
  - `speckit-pro/speckit_pro_runner/contracts/quality-gates.schema.json:28`, `speckit-pro/skills/speckit-coach/references/quality-gates-guide.md:25-26`, `speckit-pro/skills/speckit-coach/references/quality-gates-guide.md:79-83`, `speckit-pro/scripts/crap-score.py:1-30`
- **runner-core-002** (minor, adjusted from major in review): The decision record states a raw complexity ceiling of 8, Bob's 6 as the no-code fallback, three slots, ESLint plus c8 for TypeScript, and 'gate wiring is the next layer'. The shipped code and coach guide use 10 (NIST) as the default and fallback (gate_discovery.py DEFAULT_THRESHOLDS, quality_gates.py recommend), a fourth DEPENDENCY_AUDIT slot with Go and Rust rows, and oxlint plus Bun for TypeScript.
  - `docs/ai/specs/gate-tooling-decision.md:14-15`, `docs/ai/specs/gate-tooling-decision.md:106-114`, `docs/ai/specs/gate-tooling-decision.md:131`, `docs/ai/specs/gate-tooling-decision.md:260`, `speckit-pro/speckit_pro_runner/gate_discovery.py:47-52`, `speckit-pro/speckit_pro_runner/gate_discovery_table.json:44`
- **runner-core-011** (minor): EGRESS_COMMAND recognizes npm, pnpm, bun, yarn, pip-audit, cargo audit and bundle audit, but the shipped DEPENDENCY_AUDIT table also has a Go row (govulncheck), which sends module data to vuln.go.dev. A repo that declares govulncheck as a pre-PR command is not flagged as an egress need, and cargo-audit in its hyphen form is missed.
  - `speckit-pro/speckit_pro_runner/helpers/gate_preflight_coverage.py:31-32`, `speckit-pro/speckit_pro_runner/gate_discovery_table.json:152-155`

## Proposed fix

- brokers-and-verification-010: Reword the schema descriptions and table rows to 'per function in each changed file'.
- runner-core-002: Update the record's threshold table, fallback sentence, slot enum and TypeScript pick to match the code, or mark it superseded and point to gate_discovery.py, quality_gates.py and the quality-gates guide as the source.
- runner-core-011: Add govulncheck and cargo-audit to the pattern, and add a test that every DEPENDENCY_AUDIT row command in the table is matched by it.

## Acceptance

- [ ] Schema descriptions and the guide say 'per function in each changed file'.
- [ ] The decision record is updated or marked superseded with pointers to the code.
- [ ] A regression test that fails before the fix: every DEPENDENCY_AUDIT command in gate_discovery_table.json is matched by the egress pattern.
- [ ] Runner trust metadata and dist/ are regenerated.

## Related

- Overlaps files changed by the open stop-policy stack: #849, #850. Land after that stack merges.

Found by the 2026-09 coherence audit.
