Priority: major

## Summary

Four Codex skills link the shared grounding.md and capability-discovery.md contracts by a repo-root path (speckit-pro/skills/...). The payload builder rewrites only ../ links, so every copy of these links in the built Codex payload is dead. The pointer validator strips the speckit-pro/ prefix before checking existence, so it locks the unreachable form in.

## Evidence

- **seam-002** (major): Four Codex skills point at the shared grounding.md and capability-discovery.md contracts with a repo-root path (speckit-pro/skills/...). The Claude twins use ${CLAUDE_PLUGIN_ROOT}, and other Codex links use ../ paths that the payload builder rewrites; its regex (payloads.py:409) matches only ../ prefixes, so these four stay unresolvable in the built Codex payload (confirmed: every dist/codex copy of the link is dead). The pointer validator accepts the speckit-pro/ form and strips it before checking existence, so it locks the unreachable form in.
  - `speckit-pro/codex-skills/grill-me/SKILL.md:15-16`, `speckit-pro/codex-skills/speckit-prd/SKILL.md:15-16`, `speckit-pro/codex-skills/ubiquitous-language/SKILL.md:17-18`, `speckit-pro/codex-skills/speckit-coach/SKILL.md:12`, `speckit-pro/skills/grill-me/SKILL.md:19-20`, `speckit-pro/speckit_pro_runner/gates/payloads.py:409`, `tests/speckit-pro/layer1-structural/validate-skill-contracts.py:688-689`

## Proposed fix

This is Claude/Codex drift kept out of the host-parity redesign because it is a live defect in the shipped Codex payload.

- seam-002: Write the four Codex pointers as ../../skills/speckit-autopilot/references/<file>.md (the form the payload rewrite repairs), and make the pointer validator resolve each link from the SKILL.md in the built payload instead of from the plugin root.

## Acceptance

- [ ] The four pointers use the relative form the payload rewrite repairs.
- [ ] A regression test that fails before the fix: the pointer validator resolves each link from the SKILL.md inside the built payload.
- [ ] dist/ is regenerated and refresh-release-artifacts.py --check passes.

## Related

- Overlaps files changed by the open stop-policy stack: #845, #851. Land after that stack merges.
- Overlaps files changed by the in-progress fix for #832.

Found by the 2026-09 coherence audit.
