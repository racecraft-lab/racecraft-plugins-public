Priority: minor

## Summary

Lifecycle skill references, evals and templates disagree with the shipped skills. The grill-me output reference states a pre-.process Design Concept path, and the Claude status skill's allowed-tools cannot run the helpers its body calls. PRD evals number the crosswalk section wrongly, the Claude eval set covers fewer install, upgrade, status and resolve-pr behaviors than Codex, and the workflow template lists 12 checklist domains where the guide lists 15.

## Evidence

- **lifecycle-skills-008** (minor): output-formats.md says a setup Design Concept conventionally ends docs/ai/specs/<SPEC-ID>-design-concept.md. Scaffold writes to docs/ai/specs/.process/SPEC-<ID>-design-concept.md, and the status skill's explicit path glob also omits .process/. The reference states the wrong convention.
  - `speckit-pro/skills/grill-me/references/output-formats.md:7-11`, `speckit-pro/skills/speckit-scaffold-spec/SKILL.md:123`, `speckit-pro/skills/speckit-status/SKILL.md:53`
- **lifecycle-skills-013** (minor): The Claude status skill declares allowed-tools Read Glob Grep, yet its body tells the agent to run the runner through resolved_python and helpers generate-spec-index-check and o5-topology, which needs shell execution. The frontmatter and the body disagree on tool scope.
  - `speckit-pro/skills/speckit-status/SKILL.md:6`, `speckit-pro/skills/speckit-status/SKILL.md:15-17`, `speckit-pro/skills/speckit-status/SKILL.md:176`
- **functional-evals-2-004** (minor): PRD eval 3 checks the crosswalk at section 7, but the template puts it at section 8 after the required Module and Interface Deltas. Eval 1 lists the PRD sections without Module and Interface Deltas or the crosswalk, and omits the required roadmap-MOC artifact. The Codex twin repeats both.
  - `tests/speckit-pro/layer3-functional/evals/speckit-prd-evals.json:12`, `tests/speckit-pro/layer3-functional/evals/speckit-prd-evals.json:36`, `speckit-pro/skills/speckit-coach/templates/prd-template.md:149`, `speckit-pro/skills/speckit-prd/SKILL.md:63-69`
- **functional-evals-2-007** (minor): Claude Layer 3 evals cover only 1 of the 5 Codex speckit-upgrade behaviors (snapshot, --force restore, legacy dedupe, missing .specify), and 2 of 3 install cases. The Claude evals directory has no speckit-status, speckit-resolve-pr or speckit-archive-cleanup file, while Codex has status and resolve-pr.
  - `tests/speckit-pro/layer3-functional/evals/speckit-upgrade-evals.json:1-17`, `tests/speckit-pro/layer3-functional/codex-evals/speckit-upgrade-evals.json:1-65`, `tests/speckit-pro/layer3-functional/evals/speckit-install-evals.json:1-30`, `tests/speckit-pro/layer3-functional/codex-evals/speckit-install-evals.json:1`
- **coach-and-formal-010** (minor): The workflow template's domain signal table lists 12 domains. The checklist guide lists 15 (it adds integration, mobile-ux and reliability), so the two disagree on what to recommend. Separately, SPEC-MOC.md sets status to in-progress (hyphen), while the MOC guide names in_progress as the canonical value; normalize_status accepts both.
  - `speckit-pro/skills/speckit-coach/templates/workflow-template.md:296`, `speckit-pro/skills/speckit-coach/references/checklist-domains-guide.md:43`, `specs/formal-001-selective-formal-methods/SPEC-MOC.md:4`, `speckit-pro/skills/speckit-coach/references/roadmap-moc-guide.md:58`

## Proposed fix

- lifecycle-skills-008: Change the setup path in output-formats.md to the .process/ location and update the status glob.
- lifecycle-skills-013: Add the execution tool to allowed-tools, or state that the helper call is not pre-approved.
- functional-evals-2-004: Drop the section numbers or use 8, and align eval 1's section list and artifact list with the PRD output contract. Mirror in codex-evals/speckit-prd-evals.json:12,36.
- functional-evals-2-007: Port the missing upgrade, install, status and resolve-pr cases to the Claude evals directory, or record the intentional gap in the functional audit.
- coach-and-formal-010: Make the guide the single domain list and have the template point to it. Change the SPEC-MOC status to in_progress.

## Acceptance

- [ ] output-formats.md and the status glob use the .process/ path.
- [ ] Status allowed-tools matches the body.
- [ ] PRD evals (both hosts) match the template's sections and required artifacts.
- [ ] The missing Claude eval cases are ported, or the gap is recorded as intentional in the functional audit.
- [ ] The checklist guide is the one domain list; SPEC-MOC status uses in_progress.
- [ ] dist/ is regenerated; both suites pass.

## Related

- Overlaps files changed by the open stop-policy stack: #850. Land after that stack merges.
- Overlaps files changed by open PR #685.
- Depends on: single-source-host-parity (issue number added after filing)

Found by the 2026-09 coherence audit.
