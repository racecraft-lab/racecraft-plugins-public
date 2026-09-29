Priority: major

## Summary

Claude Code enforces agent contracts structurally: agent frontmatter limits tools, and skills load shared references through ${CLAUDE_PLUGIN_ROOT}. Codex restates the same contracts in hand-kept TOML prose (`developer_instructions`) and in `*-codex.md` overlay mirrors, so the two hosts drift. The parity validators check that each twin file exists and that model, effort and sandbox fields match, not that the content agrees, so the drift below reached main unnoticed. This issue replaces hand-kept mirrors with generated output and structural limits, and it closes the drift findings listed under Evidence.

## Evidence

- The audit's seam review confirmed the roster itself is coherent: frontmatter model, effort and memory match `speckit-pro/speckit_pro_runner/agent_inventory.json` for all 15 Claude agents, and TOML model, effort and sandbox match for all 13 Codex agents (`tests/speckit-pro/layer1-structural/validate-skill-contracts.py:836`, `:877-885`). The drift is all in content that no check compares.
- Each drift finding has the same shape: a Claude file carries a rule, count or step, and its Codex twin (TOML `developer_instructions` or a `*-codex.md` overlay) carries a different or missing version. Two review corrections show how hard hand comparison is: the Codex Post list has 13 rows, not the 14 its own SKILL.md claims, and the Codex reference does run the mutation hardener, only in a different place.

Claude/Codex drift findings this issue closes:

- **functional-evals-1-001** (major): Codex eval 31 says Codex keeps "all 14 Post items", and the Codex SKILL.md says "14 mandatory rows". Eval 7, the canonical list and post-implementation-codex.md all define 13 distinct rows.
  - `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json:420`, `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json:86`, `speckit-pro/codex-skills/speckit-autopilot/SKILL.md:543`, `speckit-pro/codex-skills/speckit-autopilot/references/task-list-canonical-codex.md:55-67`
- **functional-evals-1-002** (major): The Post plan is 11 rows on Claude and 13 on Codex (Codex adds Final Reviewability Backstop and PR Packet/Body Generation). legacy-selection.json records this as an unresolved gap: shared eval requirements cannot assert one sequence, so eval 7 and 25 are split by host.
  - `tests/speckit-pro/evals/fixtures/functional/legacy-selection.json:5800`, `tests/speckit-pro/evals/fixtures/functional/legacy-selection.json:5958`, `speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md:38-48`, `speckit-pro/codex-skills/speckit-autopilot/references/task-list-canonical-codex.md:55-67`
- **coach-and-formal-009** (minor): The shared workflow template says the Post closeout has 11 items. The Codex canonical list (task-list-canonical-codex.md:55-67) has 13 rows, adding Final Reviewability Backstop and PR Packet/Body Generation. The template's Post table carries neither row, so a Codex workflow starts with a checklist that disagrees with its own canonical plan.
  - `speckit-pro/skills/speckit-coach/templates/workflow-template.md:43`, `speckit-pro/skills/speckit-coach/templates/workflow-template.md:581`, `speckit-pro/codex-skills/speckit-autopilot/references/task-list-canonical-codex.md:56`
- **autopilot-and-agents-001** (minor, adjusted from major in review): The Claude Phase 7 reference runs the once-per-spec mutation hardener in Final Verification, between the MUTATION run and its block decision. The Codex reference runs it in Post row 14 (post-implementation-codex.md:45) instead. The remaining drift is placement, and hardener-delegation.md:17 and :29 anchor on 'Step 4 of Phase 7', a step the Codex reference lacks.
  - `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md:1503`, `speckit-pro/skills/speckit-autopilot/references/phase-execution.md:3123`, `speckit-pro/skills/speckit-autopilot/references/hardener-delegation.md:8`, `speckit-pro/codex-skills/speckit-autopilot/SKILL.md:815`
- **autopilot-and-agents-002** (minor): Claude states that a status summary is not a stopping point and that a turn must not end with tasks pending and nothing dispatched. Codex has no equivalent rule, and the bookkeeping-guard test asserts the rule only for the Claude side.
  - `speckit-pro/skills/speckit-autopilot/SKILL.md:66-73`, `speckit-pro/skills/speckit-autopilot/references/phase-execution.md:2783`, `speckit-pro/codex-skills/speckit-autopilot/SKILL.md:103`, `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:678`
- **autopilot-and-agents-003** (major): Every Codex reader agent declares that it 'mirrors' grounding.md and capability-discovery.md, but inlines only the evidence-note line and an abstain sentence. G1 (ground every claim), G3 (mark inference, no high confidence without grounding) and the Claude 'Read Reference dir' directive are absent. No test compares the mirror to its source; the terminal-contract test only forbids other speckit-pro/ paths.
  - `speckit-pro/codex-agents/codebase-analyst.toml:10`, `speckit-pro/codex-agents/codebase-analyst.toml:69`, `speckit-pro/skills/speckit-autopilot/references/grounding.md:19`, `tests/speckit-pro/unit/test-agent-terminal-contracts.py:184`
- **artifact-gallery-004** (minor): artifact-review.md is the shared Claude/Codex contract but says the observer has only the Artifact tool and the broker verdict tool. The Codex observer has no Artifact tool, only the broker verdict tool, and its normal verdict is unavailable.
  - `speckit-pro/skills/speckit-autopilot/references/artifact-review.md:3`, `speckit-pro/skills/speckit-autopilot/references/artifact-review.md:82-84`, `speckit-pro/codex-skills/speckit-autopilot/references/preview-prompts/observer.md:7-11`
- **coach-and-formal-001** (major): The shared contract says both platforms dispatch the author with a parent-minted broker capability and that every file change goes through the author-broker write tool. Only the Claude agent carries that rule. The Codex TOML never mentions the capability or the broker tool, runs with workspace-write, and states the output-path limit as prose only.
  - `speckit-pro/codex-agents/formal-model-author.toml:23`, `speckit-pro/agents/formal-model-author.md:37`, `speckit-pro/skills/speckit-autopilot/references/formal-methods.md:36`
- **lifecycle-skills-002** (major): The Claude status skill advertises finding active worktrees and the spec each belongs to, but its data-source step only globs the current tree and never inspects git worktrees. The Codex overlay does run git worktree list and reads attached worktrees. Conversely the Claude skill adds a Design Concept (DC) column and design-concept discovery that the Codex overlay lacks. The two hosts therefore produce different dashboards for the same repository.
  - `speckit-pro/skills/speckit-status/SKILL.md:3`, `speckit-pro/skills/speckit-status/SKILL.md:44-64`, `speckit-pro/codex-skills/speckit-status/SKILL.md:49-70`
- **lifecycle-skills-009** (minor): The Codex grill-me description says SPEC setup and worktree creation belong to scaffold-spec and a setup request alone is not an interview delegation. The Claude description lacks that boundary, so Claude may select grill-me for scaffold requests.
  - `speckit-pro/skills/grill-me/SKILL.md:3`, `speckit-pro/codex-skills/grill-me/SKILL.md:3`
- **lifecycle-skills-010** (minor): The Claude scaffold skill only warns when the roadmap status is In Progress or Complete. The Codex overlay stops on a complete spec and reuses the existing worktree for an in-progress one. Same roadmap state, different behavior per host.
  - `speckit-pro/skills/speckit-scaffold-spec/SKILL.md:186-187`, `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md:216-218`
- **lifecycle-skills-012** (minor): The Claude skill runs the lint directly by shebang (${CLAUDE_PLUGIN_ROOT}/scripts/ubiquitous-language-lint.py). The Codex overlay uses resolved_python, and speckit-install runs its sibling script agent-memory-ignore.py through resolved_python. Direct execution depends on the exec bit and on python3 being on PATH, which the installed runtime contract avoids.
  - `speckit-pro/skills/ubiquitous-language/SKILL.md:61`, `speckit-pro/codex-skills/ubiquitous-language/SKILL.md:56`, `speckit-pro/skills/speckit-install/SKILL.md:105`
- **pr-emission-and-stack-2-005** (minor): The agreement-branch, escape-phrase, result-contract and Analyze-confidence tests read only the Codex TOML (instructions()). The Claude agent is unchecked for them. The two already differ: Codex omits Artifact Edit whenever Flags is not None, Claude only for ESCAPE_TO_ROUND_2 or HUMAN REVIEW, and only Codex forbids a second confidence block.
  - `tests/speckit-pro/unit/test-consensus-synthesizer-regressions.py:80`, `tests/speckit-pro/unit/test-consensus-synthesizer-regressions.py:273`, `tests/speckit-pro/unit/test-consensus-synthesizer-regressions.py:285`, `tests/speckit-pro/unit/test-consensus-synthesizer-regressions.py:321`, `speckit-pro/agents/consensus-synthesizer.md:178`

Drift findings kept as separate issues because they are behavioral bugs to fix before this redesign lands, or fall outside generated content:

- brokers-and-verification-012: Behavioral bug today: the Codex lockfile hook fires on every tool call. A one-line matcher fix in codex-hooks.json should not wait for the redesign.
- seam-002: Behavioral bug today: four links are dead in the installed Codex payload. The fix is a path change plus a validator fix and should land before the redesign.
- functional-evals-2-007: Eval coverage gap, not generated content: Claude and Codex eval corpora are authored per host, so generating agents and overlays would not close it.

## Proposed fix

Direction, based on the official Codex documentation. The design will be settled in a grill-me session before implementation.

- **Enforce limits in config, not prose.** A custom Codex agent TOML accepts any `config.toml` key. Use `sandbox_mode` and `mcp_servers.<id>.enabled_tools` / `disabled_tools` so broker-only roles (for example the formal-model author) and read-only roles are confined structurally, the way Claude frontmatter confines them.
- **Generate agent instructions from one source.** Codex has no instruction-file include for agents (`developer_instructions` is inline). Generate each TOML's `developer_instructions` from the Claude agent body at build time through the generated-artifact refresh (`scripts/refresh-release-artifacts.py`), with clearly marked host-specific sections.
- **Shrink skill overlays to host deltas.** Both hosts use the open Agent Skills format, so `speckit-pro/codex-skills/` should hold only the files and sections that genuinely differ by host, not full mirrors of `speckit-pro/skills/`.
- **Make parity checks compare content.** Replace file-existence parity with a check that regenerates the Codex output and compares it to the committed copy, so any hand edit or stale mirror fails.

Per-finding fixes the design must cover:

- functional-evals-1-001: Change the count to 13 in eval 31 and in codex-skills/speckit-autopilot/SKILL.md (lines 543 and 791), then regenerate dependent fixtures.
- functional-evals-1-002: Reconcile the Post-plan contract across both hosts, or add host-scoped expected values so the evals stop carrying the divergence.
- coach-and-formal-009: Give the Codex scaffold path a documented row set, or add the two rows to the template with a note on which host uses them.
- autopilot-and-agents-001: Add a Codex Final Verification step (quality-gate order, hardener trigger, Hardener line) to phase-execution-codex.md, or state in SKILL.md and hardener-delegation.md that Codex does not run the hardener.
- autopilot-and-agents-002: Add a Codex counterpart phrased for the wait_agent loop and assert it in the same test.
- autopilot-and-agents-003: Inline G1 to G5 (or generate the TOML section from grounding.md) and add a test that the Codex text carries each rule.
- artifact-gallery-004: Split step 3 by host: Claude observer with Artifact plus the broker tool; Codex isolated launcher with the broker tool only.
- coach-and-formal-001: Add the capability input and the broker-only write rule to the Codex TOML, or state in formal-methods.md that Codex confinement is prose-only and record the reason in agent_inventory.json.
- lifecycle-skills-002: Bring both variants to one data-source contract: add worktree discovery to the Claude skill (or drop the claim from its description) and add design-concept discovery and the DC column to the Codex overlay, or record the difference as intentional.
- lifecycle-skills-009: Add the same boundary sentence to the Claude description.
- lifecycle-skills-010: Align both variants on stop-on-complete and reuse-on-in-progress.
- lifecycle-skills-012: Invoke the lint through resolved_python in the Claude variant, as the other scripts do.
- pr-emission-and-stack-2-005: Run each of these checks over both agent files, and align the Artifact Edit omission rule and the one-block rule in the Claude agent.

## Acceptance

- [ ] A design record, settled in a grill-me session before implementation, covers the generator, the host-specific section markers, the overlay delta rule and the config keys per role.
- [ ] Codex agent TOMLs carry `sandbox_mode` and MCP tool allow or deny lists that enforce broker-only and read-only roles. A structural test fails if a broker-only role can write outside its broker.
- [ ] `developer_instructions` is generated from the Claude agent bodies by the artifact refresh; `refresh-release-artifacts.py --check` fails on a hand edit.
- [ ] `codex-skills/` overlays hold only host deltas; each drift finding listed above is resolved by the generated output, with evals and fixtures (Layer 3 codex-evals, legacy-selection.json, bookkeeping-guard and consensus-synthesizer tests) updated to the single contract.
- [ ] Parity validators compare generated output to source instead of checking file existence.
- [ ] Both suites and the generated-artifact check pass.

## Related

- Overlaps files changed by the open stop-policy stack: #837, #838, #843, #844, #845, #847, #848, #849, #850, #851, #852. Land after that stack merges.
- Overlaps files changed by open PR #685.
- Overlaps files changed by the in-progress fix for #832.
- Depends on: unregistered-unit-tests (issue number added after filing)
- Depends on: codex-skill-dead-links (issue number added after filing)

Found by the 2026-09 coherence audit.
