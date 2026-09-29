Priority: minor

## Summary

A few autopilot references carry stale pointers: an index line describing planned sites that no longer exist, a link to a docs-site file that is dead in an installed plugin, a line-number citation that points at unrelated text, and a workflow fixture that calls the 11-row Post list a 12-item closeout.

## Evidence

- **integration-layer6-1-007** (minor): SKILL.md indexes the agent-teams reference as a use-site map of current plus planned sites. The reference now lists six current sites and no planned ones.
  - `speckit-pro/skills/speckit-autopilot/SKILL.md:858`, `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md:120-139`
- **autopilot-and-agents-011** (minor): A shipped plugin reference links to docs-site/src/content/docs/contribute-and-release.md by a four-level relative path. That file is outside the plugin payload, so the link is dead in an installed copy.
  - `speckit-pro/skills/speckit-autopilot/references/token-discipline.md:31`
- **autopilot-and-agents-009** (minor): The reference cites the coverage script at 'SKILL.md:662', but line 662 of either SKILL.md is unrelated (script commands are at Codex SKILL.md:567 and 617). The line pointer is stale.
  - `speckit-pro/codex-skills/speckit-autopilot/references/task-list-canonical-codex.md:108`, `speckit-pro/codex-skills/speckit-autopilot/SKILL.md:567`
- **functional-evals-2-003** (minor): The SPEC-009 workflow fixture calls the Post list a canonical 12-item closeout, but it lists 11 rows, the template says 11, and the shipped evals say 11.
  - `tests/speckit-pro/layer3-functional/fixtures/autopilot/SPEC-009/docs/ai/specs/SPEC-009-workflow.md:24`, `tests/speckit-pro/layer3-functional/fixtures/autopilot/SPEC-009/docs/ai/specs/SPEC-009-workflow.md:216-230`, `speckit-pro/skills/speckit-coach/templates/workflow-template.md:43`

## Proposed fix

- integration-layer6-1-007: Drop the word planned from the SKILL.md index line.
- autopilot-and-agents-011: Link the published docs URL or drop the link.
- autopilot-and-agents-009: Cite the section name instead of a line number.
- functional-evals-2-003: Change the fixture note to canonical 11-item closeout (fixture bytes are hashed elsewhere, so regenerate any dependent digest).

## Acceptance

- [ ] Each pointer is corrected or replaced by a section-name citation.
- [ ] The SPEC-009 fixture says 11 items, with any dependent digest regenerated.
- [ ] dist/ is regenerated; both suites pass.

## Related

- Overlaps files changed by the open stop-policy stack: #843, #844, #847, #849, #850, #851. Land after that stack merges.
- Overlaps files changed by open PR #685.
- Overlaps files changed by the in-progress fix for #832.
- Depends on: single-source-host-parity (issue number added after filing)

Found by the 2026-09 coherence audit.
