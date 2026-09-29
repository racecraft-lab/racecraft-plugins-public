Priority: major

## Summary

The runner integrity manifest covers only agent_inventory.json among data files, so runtime-loaded JSON (including a table whose commands run in the operator's session) can change while preflight reports verified. The local plugin refresh skips the trust recompute. The Claude payload build uses an optional copier for required directories, so a missing source yields a passing empty payload, and the runner-invocation schema allows operations the envelope rejects.

## Evidence

- **runner-core-003** (major): The runner integrity list (RUNNER_DATA_FILES plus *.py) is hand-copied in runtime.py and in the refresh script, and covers only agent_inventory.json. gate_discovery_table.json (its commands run in the operator's session), install_inventory.json and contracts/*.schema.json are loaded at runtime but sit outside the manifest and checksum, so preflight reports verified while they change.
  - `speckit-pro/speckit_pro_runner/runtime.py:27`, `speckit-pro/speckit_pro_runner/runtime.py:304-311`, `scripts/refresh-release-artifacts.py:37`, `scripts/refresh-release-artifacts.py:288`, `speckit-pro/speckit_pro_runner/gate_discovery.py:41`
- **release-tooling-003** (major): refresh-local-plugin.py rebuilds dist through build-plugin-payloads.py only. That skips the runner trust-metadata recompute (refresh step 1) and the marketplace sync (step 3), so after a runner edit the local dist carries stale trust hashes. build-plugin-payloads.py is a second entry point to step 2 of refresh-release-artifacts.py and has no other caller.
  - `scripts/refresh-local-plugin.py:219`, `scripts/build-plugin-payloads.py:18`, `scripts/refresh-release-artifacts.py:88`
- **release-tooling-012** (minor): Runner-invocation evidence and its schema allow operations (scaffold, status, autopilot-dry-run, doctor, update, autoheal) that envelope.py rejects. The runner accepts only preflight and runtime-info, and runtime-info is absent from the schema. The live-host case is named runtime-info but records status.
  - `speckit-pro/speckit_pro_runner/gates/release.py:35`, `speckit-pro/speckit_pro_runner/envelope.py:23`, `tests/speckit-pro/unit/fixtures/installed-plugin-release/contracts/runner-invocation.schema.json:45`
- **release-tooling-013** (minor): The Claude payload copies .claude-plugin, skills, agents, hooks and speckit_pro_runner with the optional copier, so a missing source directory yields a passing empty payload. The Codex side uses the required copier for skills. AGENTS.md says gates fail closed.
  - `speckit-pro/speckit_pro_runner/gates/payloads.py:300`, `speckit-pro/speckit_pro_runner/gates/payloads.py:360`

## Proposed fix

- runner-core-003: Define the file roster once (import it in the refresh script or derive both from the manifest) and include the runtime-loaded JSON data files, or document why they are excluded.
- release-tooling-003: Have refresh-local-plugin.py call scripts/refresh-release-artifacts.py and delete build-plugin-payloads.py, or document that the local refresh needs a prior artifact refresh.
- release-tooling-012: Align the enum with the envelope vocabulary or document that the field names skill operations, not runner operations.
- release-tooling-013: Use copy_required_installed_plugin for the directories the payload cannot ship without.

## Acceptance

- [ ] The integrity roster is defined once and includes the runtime-loaded JSON data files; a test fails before the fix when one changes without a manifest update.
- [ ] refresh-local-plugin.py runs the full artifact refresh.
- [ ] A regression test that fails before the fix: a missing required source directory fails the Claude payload build.
- [ ] The runner-invocation schema matches the envelope vocabulary.
- [ ] refresh-release-artifacts.py --check passes.

## Related

- None.

Found by the 2026-09 coherence audit.
