Priority: major

## Summary

README.md and the Codex install page tell users to verify ten installer-copied Codex TOML files, but the installer ships 13 roles. The install page also omits the typesafe-jev prerequisite. The speckit-pro README skill map misses three shipped skills, uses a pre-.process workflow path, and gives a payload-rebuild procedure that disagrees with AGENTS.md.

## Evidence

- **docs-001** (major): README.md tells users to verify ten installer-copied Codex TOML files. The installer requires every file in codex-agents/ (13 roles: 12 required plus the optional fast helper), so artifact-author, consensus-synthesizer and formal-model-author are missing from the list. A user who checks only the listed ten would miss three installed agents. The same ten-file list is repeated in docs-site/src/content/docs/install/codex.md (other lane).
  - `README.md:95-105`, `speckit-pro/speckit_pro_runner/agent_inventory.json:40`, `speckit-pro/speckit_pro_runner/agent_inventory.json:68`, `speckit-pro/speckit_pro_runner/agent_inventory.json:75`, `speckit-pro/speckit_pro_runner/helpers/install.py:40`
- **lifecycle-skills-001** (major): The Codex install page lists 10 expected TOML files. The bundled set is 13: artifact-author, formal-model-author and consensus-synthesizer are missing from the list. The page also never says speckit-pro needs the typesafe-jev plugin, which the install and upgrade skills require and tell Codex users to add by hand.
  - `docs-site/src/content/docs/install/codex.md:183-194`, `speckit-pro/codex-skills/install/SKILL.md:51`, `speckit-pro/codex-agents/artifact-author.toml:1`
- **docs-004** (minor): Two contributor procedures state how to rebuild generated payloads. Both READMEs give the payload-completeness-apply runner request, while AGENTS.md names python3 scripts/refresh-release-artifacts.py (payloads, marketplace version sync, runner trust metadata) as the regeneration step. Their validation steps 3 and 4 are placeholders that name no command ("Use the repository default validation suite documented in the contributor guide").
  - `README.md:159-176`, `speckit-pro/README.md:317-338`, `AGENTS.md:117-125`
- **docs-012** (minor): The README's autopilot example uses docs/ai/specs/SPEC-001-workflow.md, but scaffold writes workflow files under docs/ai/specs/.process/. The docs-site first-run page already uses the .process path.
  - `speckit-pro/README.md:191`, `speckit-pro/skills/speckit-scaffold-spec/SKILL.md:43-45`
- **docs-013** (minor): The Skill Map and skill-forms tables list eight skills plus install. speckit-install, speckit-upgrade and speckit-archive-cleanup ship in both skills/ and codex-skills/ but appear nowhere in the README.
  - `speckit-pro/README.md:217-227`, `speckit-pro/skills/speckit-install/SKILL.md:1`, `speckit-pro/skills/speckit-upgrade/SKILL.md:1`, `speckit-pro/skills/speckit-archive-cleanup/SKILL.md:1`

## Proposed fix

- docs-001: Derive the expected-file list from agent_inventory.json (or point to the generated agents reference) instead of a hand-copied list, and update the count and names in README.md and the Codex install page.
- lifecycle-skills-001: Derive the expected file list from the runner agent inventory (or link the generated agents reference) and add the typesafe-jev prerequisite step to the Codex install page. PR 851 grows the roster further, so a hand-kept list will drift again.
- docs-004: Pick one regeneration command as the source of truth, link the others to it, and replace the placeholder steps with the actual run-all.py commands or a link to the contribute-and-release page.
- docs-012: Change the example to docs/ai/specs/.process/SPEC-001-workflow.md.
- docs-013: Add the three skills to the Skill Map and the Claude Code and Codex forms table.

## Acceptance

- [ ] The Codex agent list in README.md and docs-site/src/content/docs/install/codex.md is derived from agent_inventory.json or links the generated agents reference.
- [ ] The Codex install page states the typesafe-jev prerequisite.
- [ ] The skill map and forms table list speckit-install, speckit-upgrade and speckit-archive-cleanup.
- [ ] One regeneration command is named, and the placeholder validation steps name real commands.
- [ ] Docs validation passes: pnpm --dir docs-site validate:quality.

## Related

- Overlaps files changed by the open stop-policy stack: #844. Land after that stack merges.

Found by the 2026-09 coherence audit.
