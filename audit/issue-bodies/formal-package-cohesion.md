Priority: minor

## Summary

The formal package holds autopilot policy (resume guards, gate ids, Post step names), and other modules import shared parsing helpers from it. Its modules import each other lazily to hide cycles. Tool versions and checksums are hand-copied into several files with no agreement test, and the example catalogs disagree with the setup script.

## Evidence

- **artifact-gallery-006** (minor): artifact_review imports its parsing helpers (next_fence, require_fields, require_text, unique_object) from the formal package. Four other non-formal modules import the same module, so a shared utility lives in a feature package.
  - `speckit-pro/speckit_pro_runner/artifact_review.py:13`
- **coach-and-formal-008** (minor): The formal package holds autopilot policy: apply_resume_guard edits resume parse and signal dicts, gate_checkpoint knows gate ids G3 to G7, and required_checkpoints hardcodes autopilot Post step names. Modules also import each other lazily (helper and lifecycle, catalog and traces or native_config) to hide cycles.
  - `speckit-pro/speckit_pro_runner/formal/helper.py:69`, `speckit-pro/speckit_pro_runner/formal/helper.py:84`, `speckit-pro/speckit_pro_runner/formal/lifecycle.py:145`, `speckit-pro/speckit_pro_runner/formal/lifecycle.py:160`, `speckit-pro/speckit_pro_runner/formal/catalog.py:153`
- **coach-and-formal-002** (minor): Tool versions and checksums are hand-copied into engine.py, setup-formal-tools.py, catalog.py, quint.py, the JSON schema, package.json and several docs. No test asserts that setup TOOLS agree with engine CHECKER_SHA256 or catalog VERSIONS. The values agree today, so a version bump can drift silently.
  - `speckit-pro/speckit_pro_runner/formal/engine.py:20`, `speckit-pro/skills/speckit-coach/scripts/setup-formal-tools.py:27`, `speckit-pro/speckit_pro_runner/formal/catalog.py:17`, `speckit-pro/speckit_pro_runner/formal/quint.py:17`, `speckit-pro/speckit_pro_runner/contracts/formal-methods.schema.json:15`
- **coach-and-formal-003** (minor): formal-setup.md says the example catalogs default heap_mb to 4096, but the TLC example sets 1024. Example catalogs point at .specify/tools/apalache-0.62.2/lib/apalache.jar and .specify/tools/tla2tools-1.7.4.jar, while the setup script installs under .specify/tools/formal/<tool>-<version>/. The Quint catalog snippet copies to formal/counter, the directory the TLA counter step already uses, and counter-quint ships no catalog.
  - `speckit-pro/skills/speckit-coach/references/formal-setup.md:56`, `speckit-pro/skills/speckit-coach/examples/formal/counter-tlc/catalog.json:10`, `speckit-pro/skills/speckit-coach/examples/formal/counter/catalog.json:6`, `speckit-pro/skills/speckit-coach/scripts/setup-formal-tools.py:82`, `speckit-pro/skills/speckit-coach/references/quint-guide.md:70`

## Proposed fix

- artifact-gallery-006: Move the helpers to a neutral runner module and import from there.
- coach-and-formal-008: Move resume, gate and step-name policy next to resolve-autopilot-stage or validate-gate and have it call a small formal API. Give catalog validators a leaf module so the imports stop cycling.
- coach-and-formal-002: Make one module the pin source and import it in setup-formal-tools.py and engine.py, or add one test that compares all copies including the schema consts.
- coach-and-formal-003: Align the example catalog paths and heap values with the setup script output, correct the 4096 claim, and give the Quint example its own catalog and model directory name.

## Acceptance

- [ ] Autopilot policy moves next to the stage and gate code; shared parsing helpers sit in a neutral module.
- [ ] One pin source, or a test that fails when setup TOOLS, engine CHECKER_SHA256 and catalog VERSIONS disagree.
- [ ] Example catalogs match setup-formal-tools.py paths and heap values; the Quint example has its own catalog.
- [ ] Runner trust metadata and dist/ are regenerated; both suites pass.

## Related

- None.

Found by the 2026-09 coherence audit.
