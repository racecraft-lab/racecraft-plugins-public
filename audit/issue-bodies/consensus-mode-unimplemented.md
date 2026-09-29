Priority: major

## Summary

Both hosts load consensus-mode and security-keywords at Step 0.6, and the README offers conservative, moderate and aggressive modes. Neither setting reaches anything that decides: the synthesizer applies only moderate rules and parse-consensus-categories reads a fixed keyword list. Eval 4 asserts aggressive-mode behavior that the protocol does not define, and six executor copies of the keyword list omit two runner keywords.

## Evidence

- **seam-004** (major): Both hosts load consensus-mode and security-keywords at Step 0.6, and the README offers conservative, moderate and aggressive modes. Neither setting reaches anything that decides. The synthesizer dispatch template carries no mode line, both synthesizer definitions apply only the moderate rules, and Stage 3 applies any 2-of-3 edit. parse-consensus-categories reads only inputs.line and a fixed keyword list. Conservative and aggressive modes and a custom keyword list therefore change nothing, although functional-evals-2-002's eval and the README describe their effects.
  - `speckit-pro/skills/speckit-autopilot/references/prerequisites.md:257-260`, `speckit-pro/codex-skills/speckit-autopilot/references/prerequisites-codex.md:263-265`, `speckit-pro/README.md:257-265`, `speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md:225-236`, `speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md:329-345`, `speckit-pro/agents/consensus-synthesizer.md:40-61`, `speckit-pro/codex-agents/consensus-synthesizer.toml:20-26`, `speckit-pro/speckit_pro_runner/helpers/read_only.py:5047-5051`
- **functional-evals-2-002** (major): Eval 4 says aggressive mode auto-accepts single-agent answers with a lower agreement threshold. The protocol keeps the 2/3 threshold in aggressive mode and only differs by synthesizing an answer when all analysts disagree and by stopping only on security items. The Codex twin repeats the same wording.
  - `tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json:43`, `tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json:48`, `speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md:336-345`
- **autopilot-and-agents-004** (minor): The security keyword list exists in the runner (15 words) and consensus-protocol.md (15) but six executor copies list 13 and omit 'authentication' and 'authorization'. No test compares the copies.
  - `speckit-pro/agents/clarify-executor.md:80-82`, `speckit-pro/agents/checklist-executor.md:82-84`, `speckit-pro/agents/analyze-executor.md:84-86`, `speckit-pro/codex-agents/clarify-executor.toml:66-68`, `speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md:351`, `speckit-pro/speckit_pro_runner/helpers/read_only.py:4981`

## Proposed fix

- seam-004: Either pass the resolved mode and keyword list into the synthesizer prompt and the parse-consensus-categories request and implement the mode rules there, or remove the two settings from prerequisites, README and consensus-protocol.md.
- functional-evals-2-002: Rewrite the expected_output and the aggressive expectation to match consensus-protocol.md (2/3 auto-answers, all-disagree still proceeds, only unresolved security items stop). Apply the same edit to codex-evals/speckit-autopilot-evals.json:43-48.
- autopilot-and-agents-004: Point executors at the helper or the protocol list, or add a test deriving all copies from CONSENSUS_SECURITY_KEYWORDS.

## Acceptance

- [ ] Either the resolved mode and keyword list reach the synthesizer prompt and parse-consensus-categories, with tests per mode, or both settings are removed from prerequisites, the README and consensus-protocol.md.
- [ ] Eval 4 (Claude and Codex twins) matches consensus-protocol.md.
- [ ] A test derives every executor keyword copy from CONSENSUS_SECURITY_KEYWORDS and fails on the current 13-word copies.
- [ ] Layer 3 eval fixtures and codex-evals are updated with the behavior.

## Related

- Overlaps files changed by the open stop-policy stack: #844, #845, #849, #850, #851, #852. Land after that stack merges.
- Overlaps files changed by open PR #685.
- Overlaps files changed by the in-progress fix for #832.
- Depends on #882

Found by the 2026-09 coherence audit.
