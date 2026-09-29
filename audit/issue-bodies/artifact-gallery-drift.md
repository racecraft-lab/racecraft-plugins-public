Priority: major

## Summary

SPA-CONTRACT.md says repository tests enforce its bans, but the required static test checks only CSP position, canonical blocks and attribution. The author broker maps one error to the wrong code and has an unreachable code. The preview step number, the author prompts' handling of planned manifest entries, and the UAT template comment also disagree with the code.

## Evidence

- **artifact-gallery-001** (major): SPA-CONTRACT says repository tests validate its contracts, but the required static test (162 lines after #530) checks only CSP head position, canonical blocks and attribution. Nothing asserts the banned elements and attributes (base, iframe, object, embed, on*, srcdoc, ping, scheme-relative URLs, non-image/font data: URIs), the slot inventory comment, or button type. The browser suite that covers exports, scrollers and network is in validate-docs, which is not a required check.
  - `speckit-pro/artifact-gallery/SPA-CONTRACT.md:3-4`, `tests/speckit-pro/unit/test-artifact-gallery.py:142-150`, `docs-site/package.json:18`
- **artifact-gallery-002** (minor): _error_code checks the substring 'session' before 'preview artifact', so 'preview artifact changed after session creation' reports receipt_violation instead of preview_mismatch. No message contains 'kind', so unsupported_kind is unreachable. The BROKER_ERROR_CODES tuple has no reader, and no test asserts an error code.
  - `speckit-pro/speckit_pro_runner/author_broker.py:33-40`, `speckit-pro/speckit_pro_runner/author_broker.py:439-452`
- **artifact-gallery-003** (minor): The launcher docstring and the Codex phase-execution text say step 7 dispatches artifact-preview-observer. In the same document step 7 is the bookkeeping commit and step 8 is the observer dispatch.
  - `speckit-pro/speckit_pro_runner/preview_launcher.py:3`, `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md:148`
- **artifact-gallery-005** (minor): Both author prompts select every draft-pr entry whose trigger fires and never mention manifest status. The planned architecture-viewer row (draft-pr, brownfield_change) has no template, so every brownfield run is guaranteed a gap. The roadmap calls this designed, but neither prompt nor contract says to expect or skip it.
  - `speckit-pro/agents/artifact-author.md:47-58`, `speckit-pro/codex-agents/artifact-author.toml:41-52`, `speckit-pro/artifact-gallery/SPA-CONTRACT.md:66-67`, `docs/ai/specs/html-artifacts-technical-roadmap.md:1603-1605`
- **artifact-gallery-009** (minor): The template comment says it emits eight section headers and that a '## UAT Runbook' embed depends on the order. The file has one H1 and six H2 sections, and no UAT Runbook heading.
  - `speckit-pro/skills/speckit-autopilot/templates/uat-runbook-template.md:3-6`

## Proposed fix

- artifact-gallery-001: Add a static test that scans every shipped template for the contract's banned constructs and checks that the slot inventory matches the FILL marker pairs. Either make the gallery browser suite required or reword the contract to say which suite enforces which rule.
- artifact-gallery-002: Check the preview_mismatch phrases first, drop unsupported_kind or raise it explicitly, delete or use BROKER_ERROR_CODES, and add a test per code.
- artifact-gallery-003: Change both references to step 8.
- artifact-gallery-005: State in both author prompts and in the contract how planned entries are handled: skip them silently, or record them as an expected gap.
- artifact-gallery-009: Correct the count and drop the embed claim, or name where the embed lives.

## Acceptance

- [ ] A static test that fails before the fix scans every shipped template for the banned constructs and checks the slot inventory.
- [ ] One test per broker error code; preview_mismatch is reported for a changed preview artifact.
- [ ] Step references say step 8; author prompts and the contract say how planned entries are handled; the UAT template comment is correct.
- [ ] Runner trust metadata and dist/ are regenerated.

## Related

- Overlaps files changed by the open stop-policy stack: #837, #838, #844, #847, #848, #849, #850, #851. Land after that stack merges.
- Overlaps files changed by the in-progress fix for #832.
- Depends on: single-source-host-parity (issue number added after filing)

Found by the 2026-09 coherence audit.
