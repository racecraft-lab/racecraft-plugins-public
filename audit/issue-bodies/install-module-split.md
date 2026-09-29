Priority: major

## Summary

helpers/install.py is a 5,700-line module whose docstring says 'install inventory doctor and repair', yet it also holds Windows file handling, route-policy validation, Codex capability probing, interpreter resolution and the runner-invocation gate. The gates package depends on it, and payloads.py reads the same install inventory with a looser second loader. Fixture-only doctor helpers and fake inventory data ship in the runner package.

## Evidence

- **lifecycle-skills-003** (major): The module docstring says 'Install inventory doctor and repair helpers', but the 5.7k-line file also holds Windows ctypes file handling, anchored-directory no-clobber installs, route-policy manifest validation, Codex capability probing, Python interpreter resolution and the runner-invocation gate. One file carries five unrelated jobs, so a change to any of them ripples through a single module.
  - `speckit-pro/speckit_pro_runner/helpers/install.py:1`, `speckit-pro/speckit_pro_runner/helpers/install.py:114-234`, `speckit-pro/speckit_pro_runner/helpers/install.py:2586-2728`, `speckit-pro/speckit_pro_runner/helpers/install.py:5114-5309`
- **lifecycle-skills-004** (minor): AnchoredAgentDir.previous_state and codex_agent_previous_state_at are near-identical (about 0.98 similarity): same stat, open, inode check and read loop, differing only in where the directory fd comes from.
  - `speckit-pro/speckit_pro_runner/helpers/install.py:627-660`, `speckit-pro/speckit_pro_runner/helpers/install.py:4877-4910`
- **lifecycle-skills-006** (minor): Two loaders read the same install_inventory.json with different validation. install.inventory_from_inputs rejects non-object records, traversal paths and non-string content. payloads.load_install_inventory silently skips non-object records, coerces fields with str(), and never checks paths. One file, two contracts.
  - `speckit-pro/speckit_pro_runner/helpers/install.py:5608-5645`, `speckit-pro/speckit_pro_runner/gates/payloads.py:901-920`
- **lifecycle-skills-007** (minor): doctor-preflight and doctor-repair are golden_only fixture operations. install_root must sit inside the repo fixture tree, and the default inventory lists three fake files (agents/speckit-autopilot.md and others that do not exist) labelled fixture-safe-source-checkout. No skill, agent or docs page invokes either helper. Fixture-only code and data ship in the runner package.
  - `speckit-pro/speckit_pro_runner/install_inventory.json:3`, `speckit-pro/speckit_pro_runner/helpers/registry.py:480-499`, `speckit-pro/speckit_pro_runner/helpers/install.py:1977-2050`
- **runner-core-007** (minor): gates/registry.py dispatches the runner-invocation gate to a function that lives in helpers/install.py, a 5714-line install-helper module, so gates depend on helpers. suite.py says the suite manifest is the single source of truth for layers but hard-codes CANONICAL_LAYER_KEYS as a second copy.
  - `speckit-pro/speckit_pro_runner/gates/registry.py:12`, `speckit-pro/speckit_pro_runner/helpers/install.py:1944`, `speckit-pro/speckit_pro_runner/gates/suite.py:22-24`, `speckit-pro/speckit_pro_runner/gates/suite.py:36`

## Proposed fix

- lifecycle-skills-003: Split into modules by job (codex agent install and filesystem safety, route policy, capability probe, interpreter resolution, doctor inventory) and fix the docstring.
- lifecycle-skills-004: Have the method call the module function with self.directory_fd.
- lifecycle-skills-006: Have payloads.py call the install.py loader (or move one validated loader to a shared module).
- lifecycle-skills-007: Move the inventory to the test fixtures and retire or mark the two helpers until a real install cutover uses them.
- runner-core-007: Move run_runner_invocation_gate into gates/, and derive the canonical key set from the manifest or keep it only in the manifest schema.

## Acceptance

- [ ] install.py is split by job, with a correct docstring; run_runner_invocation_gate lives under gates/.
- [ ] One validated install-inventory loader; a regression test shows a traversal path is rejected on the payloads path.
- [ ] Fixture-only inventory data moves to test fixtures.
- [ ] Runner trust metadata and dist/ are regenerated; both suites pass.

## Related

- Depends on: runner-primitive-dups (issue number added after filing)

Found by the 2026-09 coherence audit.
