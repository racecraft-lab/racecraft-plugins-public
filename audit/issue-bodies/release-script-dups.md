Priority: minor

## Summary

Release and preflight scripts restate shared constants and contracts: the container sentinel predicate, the exit-code table, architecture probing, the release PR fallback title, the pnpm pin, release-note snapshot constants and the docs path set. The copies already disagree in places, for example 'amd64' against 'x64' and a speckit-pro-only fallback title that is wrong for a typesafe-jev release.

## Evidence

- **release-tooling-001** (minor, adjusted from major in review): The CI-contract validator asserts a private copy of the container sentinel predicate, not the shipped one. The copy passes any run_preflight value when the heavy job was skipped; the shipped predicate requires exactly 'false'. Its seven cases never touch run-container-preflight.py.
  - `tests/speckit-pro/layer1-structural/validate-ci-release-contracts.py:230`, `tests/speckit-pro/layer1-structural/validate-ci-release-contracts.py:481`, `tests/speckit-pro/run-container-preflight.py:778`
- **release-tooling-005** (minor): The status-to-exit-code table and required response fields are restated in the Windows preflight helper and in test-speckit-pro-gates.py, with no equality check against envelope.py.
  - `tests/speckit-pro/run-hosted-windows-preflight.py:27`, `speckit-pro/speckit_pro_runner/envelope.py:12`, `tests/speckit-pro/unit/test-speckit-pro-gates.py:51`
- **release-tooling-006** (minor): Two scripts hold the same architecture-normalizing function and the same Windows interpreter and architecture probing. The container script names x86-64 'amd64' where the Windows helper names it 'x64', so evidence for one role uses two vocabularies. run-container-preflight.py (865 lines) also mixes change detection, Linux gates, Windows probing and the sentinel.
  - `tests/speckit-pro/run-container-preflight.py:152`, `tests/speckit-pro/run-hosted-windows-preflight.py:139`, `tests/speckit-pro/run-container-preflight.py:36`, `tests/speckit-pro/run-hosted-windows-preflight.py:43`
- **release-tooling-007** (minor): The fallback release title 'chore(release): release speckit-pro' is a literal in two scripts and is wrong for a typesafe-jev release PR. The dispatcher also hardcodes base_ref=main while every sibling honors BASE_REF, and it re-validates PR metadata instead of reusing resolve_release_prs.normalize_release_pr.
  - `scripts/dispatch-release-pr-checks.py:13`, `scripts/dispatch-release-pr-checks.py:106`, `scripts/resolve_release_prs.py:64`
- **release-tooling-008** (minor): The pnpm pin is restated in sync_release_pr.py, check-toolchain.py, docs-site/package.json, release.yml and the docs page, with no single source.
  - `scripts/sync_release_pr.py:244`, `tests/speckit-pro/check-toolchain.py:186`, `docs-site/package.json:6`
- **release-tooling-009** (minor): The snapshot key set, the schema version literal 1 and FAILURE_OUTCOME are duplicated between the audit script and the composer. The composer keeps SNAPSHOT_SCHEMA_VERSION; the audit hardcodes 1.
  - `scripts/audit-release-notes.py:117`, `scripts/audit-release-notes.py:130`, `scripts/audit-release-notes.py:19`, `scripts/compose-release-notes.py:492`, `scripts/compose-release-notes.py:43`
- **release-tooling-010** (minor): The composer re-exports underscore-private names (_label_names, _validation_inputs_from_environment) from the policy module and leaves them out of __all__. The policy module also owns CLI environment parsing.
  - `scripts/compose-release-notes.py:33`, `scripts/compose-release-notes.py:34`, `scripts/release_note_policy.py:514`
- **release-tooling-014** (minor): The docs-affecting path set lives in classify-docs-validation.py and again in deploy-docs.yml paths. The classifier counts any tests/speckit-pro change (fixtures included) as reference-affecting; the deploy trigger excludes fixtures. Version Fields also says the Claude marketplace entry omits version, which is true only for speckit-pro (typesafe-jev's carries 0.9.2).
  - `scripts/classify-docs-validation.py:102`, `.github/workflows/deploy-docs.yml:6`, `docs-site/src/content/docs/contribute-and-release.md:117`

## Proposed fix

Severity note: the sentinel-predicate copy (release-tooling-001) was lowered to minor in review because the shipped predicate is already covered elsewhere.

- release-tooling-001: Import the shipped _required_sentinel_passes (the way test-hosted-windows-preflight.py:590 does) and assert against it, or delete the copy and its case list.
- release-tooling-005: Import the table from speckit_pro_runner.envelope (the helper already puts the runner on sys.path) or add a drift test.
- release-tooling-006: Share one probe module for both, pick one family vocabulary, and split the Windows probing out of the container script.
- release-tooling-007: Define the fallback once in resolve_release_prs.py, derive it from the component, and pass BASE_REF through.
- release-tooling-008: Read packageManager from docs-site/package.json in sync_release_pr.py and check-toolchain.py, or add a test that ties the literals together.
- release-tooling-009: Share the snapshot schema and outcome constants in release_note_policy.py or a small module both scripts import.
- release-tooling-010: Make both helpers public in release_note_policy.py, add them to __all__, and move the PR_* environment reader to the composer.
- release-tooling-014: State the path set once, or add a test comparing the two lists. Scope the Version Fields sentence to speckit-pro.

## Acceptance

- [ ] Each constant has one source that the other scripts import, or a test ties the copies together.
- [ ] A regression test that fails before the fix: the fallback release title for a typesafe-jev release names typesafe-jev.
- [ ] The CI-contract validator asserts the shipped sentinel predicate, not a private copy.
- [ ] actionlint passes if a workflow changes.

## Related

- None.

Found by the 2026-09 coherence audit.
