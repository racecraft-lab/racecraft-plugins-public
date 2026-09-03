# Prompt Audit: Effort Policy and Consensus Analyst Roster

**Status:** Decided
**Audit date:** 2026-09-02
**Scope:** the 14 bundled Claude Code subagents under `speckit-pro/agents/` and
their Codex TOML mirrors under `speckit-pro/codex-agents/`

A prompt audit of the shipped agent roster raised two questions that the audit
report could not settle on its own. F1 asked whether every agent should keep the
uniform `effort: max` pin that PR #67 set by directive. M6 asked whether
`codebase-analyst`, `spec-context-analyst`, and `domain-researcher` should fold
into one `consensus-analyst` taking a perspective parameter. Both were routed to
a research run rather than decided in the report, because both turn on evidence
the report did not hold: what the vendors' current effort guidance says, what the
repository has already measured, and what the plugin's own contracts bind.

Each question ran through the same method. First a fetch pass gathered current
official documentation and the in-repo evidence, including the Layer 6 Codex
efficiency results and the git history of every pin. Then three judges scored the
options through three separate lenses: output quality, runtime cost, and
maintenance burden. Then three refuters attacked the leading option, each from a
different angle, to see whether it survived contact. A synthesis pass reconciled
the judges and refuters into one record per question, listing the evidence, the
rejected options, the strongest surviving objection, and an implementation table.
The outcome on F1 was lower-mechanical-only: `consensus-synthesizer` drops to the
documented default and every other Claude agent keeps `max`. The outcome on M6
was keep-three-with-fixes: the three analysts stay three definitions, and the
undeclared Phase 7 research dispatch on `domain-researcher` is declared in that
agent's own Input contract. Both records are reproduced below verbatim. Each
opens with its own `##` heading, so a record's title reads as a sibling of the
section heading above it rather than as a child; the records are not rewrapped or
re-leveled, because their line-level citations are what makes them auditable.

## Effort policy (F1)

## Decision record: effort policy for the 14 bundled Claude Code subagents (F1)

**Question.** Every agent under `speckit-pro/agents/*.md` ships `effort: max`, set by PR #67 (git 45147ad15, 2026-05-24: "we never want to use less than max thinking regardless of model", "Cost is a non-goal"). The Codex TOML mirrors accept only `low` or `xhigh`, and two of them already run `low`. Keep max everywhere, adopt the audit's per-agent table (F1), or lower only the mechanical roles?

**Decision: lower-mechanical-only, with the roster fixed by a mechanism test, not a label.**

A role is mechanical for this record only when both hold:

1. its body forbids the work that effort above the default buys (interpretation, evidence gathering, its own analysis);
2. its output is a fixed shape a program parses, so extra prose is a defect rather than a contribution.

Two agents pass, and they are also the two with the smallest turn budgets (10 and 15), where the extra tool calls that higher effort produces compete hardest with the deliverable. `gate-validator` drops to `low`. `consensus-synthesizer` drops to `high`, the documented default. Every other Claude agent stays at `max`. No Codex TOML changes. The three judges scored three different rosters under this option's name; this record fixes one and names the others as rejected sub-rosters below.

### Roster

| Agent | Claude effort | Codex effort | Reason |
|---|---|---|---|
| analyze-executor | max | xhigh | Opus executor that runs `/speckit-analyze`, researches every finding at every severity, and edits spec/plan/tasks (`speckit-pro/agents/analyze-executor.md:4-10,36-47`). Quality-critical cohort; CAR-007 owns any change. |
| artifact-author | max | xhigh | Authors PR-facing gallery pages from the planning record under a grounding requirement (`artifact-author.md:21-24,43-44`). Fail-open, but the pages are deliverables. Structured-work cohort; CAR-008. |
| checklist-executor | max | xhigh | Runs a checklist domain and researches and fixes every `[Gap]` in spec.md or plan.md (`checklist-executor.md:4-9,36-47`). Quality-critical work on the spec text. |
| clarify-executor | max | xhigh | Its up-to-five questions "materially affect architecture, data modeling, task decomposition" (`clarify-executor.md:50-53`). Spec quality depends on it directly. |
| codebase-analyst | max | low | Claude side unmeasured: a 50-turn research role whose value is file-cited evidence (`codebase-analyst.md:13-15`). Codex `low` is L6-validated at quality 1.0 and test-admitted; Anthropic says not to carry effort across models, so the asymmetry is evidence-gated, not drift. |
| consensus-synthesizer | high | n/a | Rule 5 forbids its own analysis and any evidence search (`consensus-synthesizer.md:87-90`); the G6.5 block is regex-parsed (`:156-179`); 15 turns (`:13`). Recorded 15/15 turn-burn at max. `high`, not `medium`: it writes the applied edit text (`:75-80`) and its pre-#67 value was `high`. |
| domain-researcher | max | xhigh | Claude unmeasured. Codex L6 never reached quality 1.0 at any level (0.62 to 0.69), so it fails the plugin's own carve-out rule and stays `xhigh`. |
| gate-validator | low | n/a | "You are a mechanical validator" that must not interpret, remediate, read spec artifacts, or reformat the JSON the orchestrator parses (`gate-validator.md:17-19,31-34,40-42`); 10 turns. Designed as haiku/low on 2026-04-04. Moot once WP4 deletes the agent. |
| implement-executor | max | xhigh | Single-task TDD executor (`implement-executor.md:4-9`). Long-horizon coding is where Anthropic's data shows effort buys accuracy. |
| phase-executor | max | xhigh | Its own description pins "maximum reasoning effort" for Specify and Plan (`phase-executor.md:6-10`, working tree). PR #33 reverted a prior "mechanical" misread of this role. |
| spec-context-analyst | max | low | Same reasoning as codebase-analyst: Claude unmeasured, Codex `low` L6-validated at 1.0 and test-admitted. |
| sweep-analyst | max | n/a | Performs a perspective analysis or a three-record synthesis with cited evidence and an exact edit (`sweep-analyst.md:34-99`); a judgment role behind a receipt-only wrapper. No Codex TOML by design. CAR-009. |
| sweep-classifier | max | n/a | Fails the criterion: it reads snapshot evidence at its own discretion (`sweep-classifier.md:30-32`) and must judge whether artifacts "already settle the objection" on attacker-controlled text (`:17-19,38-41`). A wrong `answered` is silent. No Codex TOML by design. CAR-009. |
| uat-runbook-author | max | xhigh | Rewrites the UAT skeleton into an executable runbook from spec, plan, and diff (`uat-runbook-author.md:22-26,44-50`). Authoring, not relaying. Structured-work cohort; CAR-008. |

`autopilot-fast-helper` is Codex-only and outside the 14; it stays at `low` on gpt-5.6-luna (`speckit-pro/codex-agents/autopilot-fast-helper.toml:3-4`, enforced by `tests/speckit-pro/layer1-structural/validate-codex-agents.py:161-167`).

### Evidence

**Anthropic's guidance points at the default for bounded structured-output roles and at max only for capability-sensitive coding.**

- Fable 5.1: "Start with `high`, the default. Step up to `xhigh` or `max` for the most capability-sensitive agentic and coding work, and step down to `medium` or `low` for routine or latency-sensitive work once your evals show quality holds." (https://platform.claude.com/docs/en/build-with-claude/effort#recommended-effort-levels-for-claude-fable-5-1)
- `max` "may show diminishing returns and is prone to overthinking. Test before adopting broadly." (https://code.claude.com/docs/en/model-config#choose-an-effort-level). On Opus 4.7: "on some structured-output or less intelligence-sensitive tasks it can lead to overthinking" (https://platform.claude.com/docs/en/build-with-claude/effort#recommended-effort-levels-for-claude-opus-4-7).
- `low` is for "short, scoped, latency-sensitive tasks that are not intelligence-sensitive" (https://code.claude.com/docs/en/model-config#choose-an-effort-level) and its canonical use case is "subagents" (https://platform.claude.com/docs/en/build-with-claude/effort#effort-levels).
- Higher effort "may: Make more tool calls, Explain the plan before taking action, Provide detailed summaries" (https://platform.claude.com/docs/en/build-with-claude/effort#effort-with-tool-use). That is the exact behavior a verbatim-JSON contract and a 15-turn budget cannot absorb.
- Long-horizon coding is where effort measurably buys accuracy (SWE-bench Pro: about 8 points lost at `low`), while research and knowledge-work curves are nearly flat (https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence#tune-effort). That is why the executors keep `max` and the two bounded roles do not.
- "If you carried effort settings over from an earlier model, run a fresh effort sweep on your evals rather than reusing them." (https://platform.claude.com/docs/en/build-with-claude/effort#recommended-effort-levels-for-claude-opus-5). This is why Codex's `low` results do not transfer to the Claude analysts.
- The subagent `effort` field overrides the session level (https://code.claude.com/docs/en/sub-agents#supported-frontmatter-fields), and the third-party guide in evidence reports no per-dispatch override (https://claudefa.st/blog/guide/development/model-vs-effort#override-behavior). Any pin is therefore a fixed decision, which is why this record lowers only roles whose bodies fix the work.

**The two lowered bodies disclaim what max buys.**

- `gate-validator.md:17-19`: "You are a mechanical validator", "you do not interpret, remediate, or suggest fixes". `:31-34`: return the JSON verbatim, "the orchestrator parses your output". `:40-42`: "Do not read spec artifacts." `:11`: `maxTurns: 10`.
- `consensus-synthesizer.md:87-90` (rule 5): "Do not add your own analysis ... Do not introduce new arguments, search for additional evidence". `:156-179`: the `📊 Confidence` block feeds G6.5 through a regex parser (`speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md:527-541`). `:13`: `maxTurns: 15`. The protocol calls it an "edit-applier" in the single-analyst case (`consensus-protocol.md:100`).
- Neither the phase-executor precedent nor the classifier meets the test. `phase-executor.md:6-10` says Specify and Plan are heavy architectural reasoning. `sweep-classifier.md:30-32` grants a discretionary evidence read and `:38-41` demands a judgment between `amended` and `answered`.

**The repo already tried both directions, which is why the criterion is mechanism, not appearance.**

- git eb0f69c (2026-04-04) dropped phase-executor to `low` because it "runs mechanical tasks (invoke a Skill command, summarize output)". git 1995ff0 (#33, 2026-04-30) reverted it: "The 'Simple: run command, return summary' framing ... was a misread" and the regression shipped "quietly" until the user caught it in production. A role that looks like a relay can still be the place the reasoning happens.
- git 1995ff0's own table records the pre-#67 state as "gate-validator (Claude only): haiku + low effort (pure script)" and "consensus-synthesizer (Claude only): sonnet + high effort". The 2026-04-04 design that created gate-validator set "Model: haiku | Effort: low" for "purely mechanical work" (git 92e2e932, design doc "New Agents" section). git 45147ad15 (#67) overrode both by directive and moved gate-validator to sonnet "rather than degrading the thinking tier". This record restores the two reasoned values; it does not invent new ones.
- The pins on the four agents added after #67 were never reasoned: the bodies of git 049e6d972 (#114, the two authors) and git 8db22a420 (#464, the two sweep roles) do not mention effort. Their `max` is inherited policy. That cuts both ways, so this record leaves them where they are pending CAR-008 and CAR-009 rather than treating either value as evidence.

**Documented downsides of max on bounded roles have in-repo instances, though effort was never isolated as the cause.**

- Consensus synthesizer, ART-008 Clarify (2026-08-20): three of four dispatches returned an empty result at exactly 15 of 15 tool calls, one caught running `awk` to measure line widths; an empty Phase 6 result makes G6.5 read NO_DATA (`docs/ai/specs/.process/ART-008-workflow.md:1873-1875`; the 15-of-15 and `awk` details come from the operator's memory note on that run). The recorded cause was a file-reading prompt instruction; the mechanism, verification loops of extra tool calls, is the one Anthropic attributes to higher effort. Lowering to `high` removes one of the two contributing factors; the prompt fix removes the other.
- Analysts ending on an intermediate thought (`docs/ai/specs/.process/XPLAT-010-workflow.md:175`) and truncated author summaries (`ART-008-workflow.md:1653-1656`; `CAR-005-workflow.md:1473-1477`) were fixed by raising `maxTurns` or reordering the return format. Those roles stay at `max` here because they gather evidence, and their fixes did not need effort.
- A gate-validator that returns anything but the verbatim JSON fails its parse (`gate-validator.md:31-34`). No incident is recorded; the risk is docs-derived. It is also the agent whose only dispatch site is `speckit-pro/skills/speckit-autopilot/SKILL.md:588`, which WP4 rewires to call `validate-gate` directly before deleting the agent; the operator's memory notes already bypass it.

**The only in-repo measurement supports the Codex column and does not carry to Claude.**

- `tests/speckit-pro/layer6-efficiency/results-codex/consolidated-smoke-2026-05-25.json` (gpt-5.6-sol, one trial per cell): codebase-analyst quality 1.0 at `xhigh` (793,373 tokens, 150 s) and `low` (188,366 tokens, 40 s); spec-context-analyst 1.0 at `xhigh` (1,517,579 / 149 s) and `low` (824,513 / 77 s); domain-researcher 0.62 at `xhigh`, 0.69 at `low`, never 1.0.
- The Codex carve-out is admitted by `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py:305-315` and `validate-codex-agents.py:193-198` as "L6-validated (low or xhigh)". `speckit-pro/codex-agents/codebase-analyst.toml:4-6` and `spec-context-analyst.toml:4-6` cite the same file.
- No Claude effort sweep exists: `run-efficiency-benchmarks.py:33-34` sweeps `SWEEP_CONFIGS = ("opus", "sonnet", "haiku")` for Claude and effort only for Codex, and `results/` holds one CAR-004 smoke, no effort data. The CAR manifest still marks the Claude `effort` field `runtime_verification_needed: true` (`docs/ai/research/claude-agent-route-candidate-manifest.json:1233-1248`).

**The current state is not "max everywhere" and the repo has already retracted the directive's premise.**

- Three Codex agents run below `xhigh`: the two analysts and `autopilot-fast-helper` (`autopilot-fast-helper.toml:3-4`, exactly `low` enforced by `validate-codex-agents.py:161-167`; set by git 2657ed666, #509, after #67 had bumped it to `xhigh`).
- git f6d6e4f64 (#419, 2026-08-03) removed the orchestrator's max demand because "That is the plugin vetoing an operator's session configuration"; `speckit-pro/skills/speckit-autopilot/SKILL.md:98-103` now says "Reasoning effort is inherited, never checked" for the orchestrator that "makes gate decisions, synthesizes consensus" (`:88-90`).
- The plugin's own written rule already admits lowering: "every agent at `effort: max` (or L6-validated lower effort where quality=1.0)" (`speckit-pro/skills/speckit-coach/SKILL.md:90`). The CAR PRD calls the policy statement superseded: AC-8.2, "The superseded 'max thinking on every agent' policy statement is replaced by the evidence-backed route table" (`docs/prd-claude-agent-routing.md:706-711`).

### Rejected options

**keep-max-everywhere.** Zero blast radius and zero unmeasured risk on producers, but it is not the shipped state (three Codex pins below `xhigh`, one test-enforced), the repo retracted its premise in #419, the PRD calls the statement superseded (AC-8.2), and it leaves `max` on a role whose body forbids every form of judgment while carrying a documented overthinking risk on structured output. The one concrete effect the directive had on a mechanical role was to force a costlier model onto gate-validator (`validate-tool-scoping.py:233`: "haiku does not support max"), an agent now bypassed in practice and scheduled for deletion. Waiting for CAR-009 is waiting indefinitely: CAR-006 is "Ready" with no workflow file, CAR-007 through CAR-010 are "Pending, Blocked by CAR-006" (`docs/ai/specs/claude-agent-routing-technical-roadmap.md:333-337`), and the Claude harness cannot sweep effort at all today.

**lower-per-agent (audit F1: analysts and gate-validator and classifier `low`, synthesizer `medium`, five roles `high`, three executors `xhigh`).** It lowers every producer without a Claude eval, against Anthropic's "step down ... once your evals show quality holds" and against the model-carryover warning. `low` on the analysts is the level reserved for tasks "not intelligence-sensitive", applied to 50-turn research roles whose file-cited evidence is what the synthesizer turns into spec edits. `medium` on the synthesizer trades intelligence on the role that writes the applied edit and scores G6.5; the one third-party measurement in evidence shows medium-to-high still gains about 10 points on structured adjudication (https://www.datacamp.com/tutorial/claude-opus-4-8-api-tutorial#reading-the-results). The `medium` and `high` tiers have no Codex expression, so seven-plus agents would become platform exceptions or the Codex tests would loosen. Thirteen files change, five levels to maintain, and the CHANGELOG shows phase-executor's effort already flipped four times (`speckit-pro/CHANGELOG.md:516,629,644,674`).

**Rejected sub-rosters of the chosen option.**

- *sweep-classifier to `low` (Judge 1 and Judge 3).* The strongest objection in the review, and it stands. The classifier's evidence read is discretionary (`sweep-classifier.md:30-32`) and lower effort "scopes its work to what was asked" with "fewer tool calls" (Anthropic, Opus 4.7 guidance and #effort-with-tool-use). A trimmed read that yields `answered` instead of `amended` silently drops a reviewer objection: "Only `amended` routes into consensus" (`speckit-pro/skills/speckit-autopilot/references/phase-execution.md:1739-1742`) and "The orchestrator is not a conduit. It never receives the ... classifier reason" (`:1672-1675`). The failure the option was meant to prevent, a non-receipt final message, is already loud: the SubagentStop hook exits 2 with a closed reason so the model can correct it (`speckit-pro/hooks/hooks.json:37-46`; `speckit-pro/scripts/sweep-isolation-hook.py:21,32-39,59-61,238-244`), and "A failed launch or non-receipt output stops the run" (`phase-execution.md:1669-1670`). The pin is also the sole effort control on that path, since the launcher loads no settings and passes no `--effort` (`speckit-pro/speckit_pro_runner/sweep_launcher.py:196-227`). Trading a loud failure for a silent one on the adversarial-input role fails the quality lens. The plugin's taxonomy agrees: the classifier is in the "attacker-influenced" row, not the "deterministic current inputs" row (`speckit-pro/skills/speckit-autopilot/references/subagent-memory-policy.md:16-17`), and in the `untrusted-feedback` cohort, not `orchestration-support` (`tests/speckit-pro/layer6-efficiency/fixtures/claude-agent-roster-rebaseline-v2.json`; asserted at `tests/speckit-pro/unit/test-role-corpus-governance.py:371-379`).
- *sweep-classifier to `high`.* Cheaper than `low` on the same risk, but still an unmeasured change to a security role with no fixture on either platform, and it does not pass the criterion. Left to CAR-009, whose scope names it (`roadmap:843-847`).
- *Claude analysts to `low` to match Codex (Judge 2).* Anthropic's carry-over warning applies directly; the Codex numbers are one trial each on a different model. CAR-009 scope.
- *consensus-synthesizer to `medium` (audit F1, Judge 2).* Covered above; `high` keeps the default reasoning on the edit text and the confidence score while removing max's documented overthinking.

### Strongest surviving objection and mitigation

**Objection.** No Claude measurement exists for either lowered agent. The plugin's written admission rule allows lower effort only where "L6-validated ... quality=1.0" (`speckit-coach/SKILL.md:90`), and the CAR roadmap declares "The current uniform `max` pins are the immutable comparator, not the search origin" (`roadmap:158-161`; PRD AC-2.1 `prd:341-342`). The option therefore lowers the two unmeasured agents while keeping the three measured ones at `max`, and it moves the comparator for a search that has not run.

**Mitigation.**

1. *Two admission paths, both written down.* Path A is measurement (L6 quality 1.0), which produced the Codex carve-out. Path B is role-contract exclusion: the body forbids the work effort buys and the output is program-parsed. Path B is the reasoning the 2026-04-04 design used for gate-validator and the reasoning #67 overrode by directive, not by evidence. The prose edit to `speckit-coach/SKILL.md:90` states both paths so the rule and the pins agree again.
2. *The comparator is preserved whatever ships.* `tests/speckit-pro/layer6-efficiency/fixtures/car-003-role-corpus.json` is marked immutable, binds the source digests of the max-pinned agent bytes, and is "never written" by the rebaseline script (`rebaseline-corpus.py`, module docstring; `test-role-corpus-governance.py:355-361` asserts `disposition == "immutable"`). Git 45147ad15 records the uniform-max configuration. CAR-009's Stage A2 starts its search at the documented default (`high`) regardless of the shipped pin and compares against the recorded comparator, exactly as Codex measured `xhigh` cells while shipping `low`.
3. *The change is reversible and small.* Two frontmatter values, one L5 assertion, one baseline line, three prose sites. If CAR-009's sweep shows `max` beats `high` on the synthesizer fixture (`fixtures/consensus-synthesizer/`), the route table restores it and the drift gate (PRD AC-3.4, `prd:594-598`) enforces whatever the manifest says.
4. *The failure modes on the lowered roles stay loud.* A gate-validator that returns non-JSON fails the orchestrator's parse and is treated as a gate failure, and the agent is deleted by WP4 in any case. A synthesizer that returns an empty result makes G6.5 read NO_DATA and logs a plugin-regression warning (`consensus-protocol.md:527-541`), which is the same visibility it has today.
5. *Nothing here pre-empts CAR-009 on the roles it can still learn from.* The classifier, sweep-analyst, and all three analysts keep their comparator value, so the cohort search retains its full baseline on every judgment role.

### Implementation

Line numbers are from the audit-remediation worktree at 422dd843a plus WP1's uncommitted edits; WP2 through WP5 land before WP6, so re-grep before editing. Apply after WP4 (task #5) so the gate-validator rows are already gone. If WP6 lands first, include the bracketed gate-validator steps.

| Step | File | Change |
|---|---|---|
| 1 | `speckit-pro/agents/consensus-synthesizer.md:14` | `effort: max` to `effort: high`. No other frontmatter or body change. |
| 2 | [`speckit-pro/agents/gate-validator.md:12`] | [`effort: max` to `effort: low`. Keep `model: sonnet`; the model is CAR-009 scope. Skip if WP4 has deleted the file.] |
| 3 | `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py:287-288` | `assertEqual("high", ...)`; subtest message becomes `consensus-synthesizer effort is high (bounded rule-applier runs at the documented default)`. Leave `:281-282` (phase-executor `max`), `:275-276` (effort must be non-empty), and `:305-315` (Codex carve-out) untouched. |
| 4 | `tests/speckit-pro/parity/bash-to-python/validate-tool-scoping-baseline.txt:148` | Keep the `148 ` prefix and replace only the message text with the new subtest string from step 3, verbatim. The module header (`validate-tool-scoping.py:6,16`) requires a 1:1 name match with the baseline; `suite-manifest.json:150` binds the pair. |
| 5 | [`validate-tool-scoping.py:233-237` and `baseline.txt:78-79`] | [`:236-237` to `assertEqual("low", ...)` with message `gate-validator effort is low (mechanical validator: runs one command, returns JSON verbatim)`; `:233` message loses "(max-thinking policy: haiku does not support max)". Mirror both strings in the baseline, keeping the `078 ` and `079 ` prefixes. WP4 removes the whole block instead.] |
| 6 | `speckit-pro/skills/speckit-autopilot/SKILL.md:98-103` | Rewrite the pin sentence. It currently says the subagents "ship pinned at `effort: max` (or `xhigh` on Codex)" and "that pin only ever raises a worker's effort", which is false after step 1. New text: judgment roles ship pinned at `max` (`xhigh` on Codex); the two bounded roles that only apply rules to inputs already in their prompt ship at the documented default; a pin sets the worker's effort regardless of the session and never refuses to run. |
| 7 | `speckit-pro/skills/speckit-autopilot/references/token-discipline.md:165` | "every agent at `effort: max`" becomes "judgment agents at `effort: max` and bounded rule-applying agents at the documented default". |
| 8 | `speckit-pro/skills/speckit-coach/SKILL.md:90` | Replace "(or L6-validated lower effort where quality=1.0)" with "(or lower effort admitted by one of two paths: L6-validated quality=1.0, or a role contract that forbids interpretation and evidence gathering and returns a program-parsed shape)" and drop "max-thinking-on-every-agent" from the sizing sentence. |
| 9 | `speckit-pro/codex-skills/speckit-autopilot/SKILL.md:184-190`, `speckit-pro/codex-agents/*.toml`, `validate-codex-agents.py:161-198`, `validate-tool-scoping.py:305-348` | No change. The Codex column is unchanged. |
| 10 | `docs/ai/specs/claude-agent-routing-technical-roadmap.md:158-161` | Add one dated amendment bullet: consensus-synthesizer (and gate-validator until WP4) ship below the comparator under the role-contract path; the comparator remains the immutable `car-003-role-corpus.json` digests and git 45147ad15. Do not rewrite the baseline table at `:84-100`. (Pre-existing drift to note, not fix: that table lists the sweep roles as `opus / max` while the files say `sonnet`.) |
| 11 | Regenerate, in this order | `python3 tests/speckit-pro/layer6-efficiency/rebaseline-corpus.py` (WP1's script; rewrites `fixtures/claude-agent-roster-rebaseline-v2.json` and the `fixtures-codex/consensus-synthesizer/fixture.json` plus `corpus-manifest.json` chain, since `test-codex-qualification-corpus.py:60,146-149` binds `agents/consensus-synthesizer.md` bytes and `test-role-corpus-governance.py:363-369` hashes every `agents/*.md`), then `python3 scripts/refresh-release-artifacts.py` (dist and proofs), then `pnpm --dir docs-site reference:generate` (the generated `docs-site/src/content/docs/reference/agents.md` reports only Codex effort via `generate-reference-pages.mjs:200,296`, but the ritual is unconditional after an agent edit). |
| 12 | Verify | `python3 tests/speckit-pro/run-all.py`. Expected deltas: the L5 subtest at step 3 and the baseline line at step 4, nothing else. Run from a neutral path with `GITHUB_HEAD_REF` set if the privacy scan or `test_no_cutover` false-fires from the worktree. |
| 13 | PR | Title `fix(speckit-pro): pin the consensus synthesizer at the documented default effort` (or `feat` if the policy prose change is judged user-visible); one non-empty release-note fence in the body. |

**Follow-ups outside this change.** (a) CAR-009 needs a Claude effort axis in `run-efficiency-benchmarks.py:33-34` before any further Claude lowering; the classifier, sweep-analyst, and analysts wait on it. (b) When CAR-006's drift gate lands, the route-policy manifest must materialize `high` for consensus-synthesizer or the gate fails on first run. (c) The roadmap baseline table's `opus / max` rows for the sweep roles disagree with the shipped `sonnet` and should be corrected in the CAR-009 scaffold.
## Consensus analyst roster (M6)

## M6: Keep three consensus-analyst definitions, fix in place

**Decision.** Keep `speckit-pro/agents/codebase-analyst.md`, `speckit-pro/agents/spec-context-analyst.md`, and `speckit-pro/agents/domain-researcher.md` as three definitions. Do not fold them into one `consensus-analyst` with a perspective parameter. Apply the in-place fixes in the implementation table below. The fix list drops one item the task context implied: `memory: local` is NOT added to domain-researcher.

Judges: 3 of 3 lenses (output quality 8 vs 5, runtime cost 8 vs 4, maintenance 8 vs 3) chose keep-three. Refutation passes: 0 of 3 refuted it.

### Evidence

**1. The fold cannot carry two per-perspective knobs.** `effort` and `memory` are per-definition frontmatter (https://code.claude.com/docs/en/sub-agents#frontmatter-fields; `tests/speckit-pro/layer1-structural/validate-agents.py:50-63` PLUGIN_AGENT_FIELDS). The only per-invocation override the docs describe is `model`; the dispatch template at `speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md:196-204` passes subagent_type, run_in_background, description, and prompt, nothing else. The audit's fold plan ("keep memory: local conditional on perspective") is therefore unexecutable as written.

**2. The memory asymmetry is policy, keyed by agent name.** `speckit-pro/skills/speckit-autopilot/references/subagent-memory-policy.md:12-15` grants `local` to codebase-analyst and spec-context-analyst on exact-client UAT and sets domain-researcher to none because external facts drift. `:33-36` forbids storing raw web or research text. `:42-44` records that memory writes under `.claude/agent-memory-local/<agent>/`; on disk this worktree holds `.claude/agent-memory-local/speckit-pro-implement-executor`, confirming the directory carries the plugin-prefixed name. Enforcement: `validate-agents.py:73-77` MEMORY_POLICY (exact match) and `tests/speckit-pro/unit/test-role-corpus-governance.py:381-392`. The decision is recorded at `docs/ai/research/claude-subagent-runtime-rebaseline.md:37-39`. Commit e4d9a358e (#517) changed only `disallowedTools` on domain-researcher while adding memory to its two siblings, so the omission was deliberate. One folded name would give three lanes one MEMORY.md and would either persist drifting external facts or strip memory from the two lanes where UAT proved value.

**3. Codex effort is per-role and L6-tuned.** `speckit-pro/codex-agents/codebase-analyst.toml:4-6` and `spec-context-analyst.toml:4-6` pin `low` with L6 rationale comments; `domain-researcher.toml:4` pins `xhigh`. `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py:306-312` asserts that split per agent. `tests/speckit-pro/layer6-efficiency/results-codex/consolidated-smoke-2026-05-25.json` shows codebase-analyst at quality 1.0 with 188,366 tokens/40s at low versus 793,373/150s at xhigh, and spec-context-analyst at quality 1.0 with 824,513/77s at low versus 1,517,579/149s at xhigh (the TOML comments' 76% and 46% figures match these pairs). domain-researcher scores 0.62 to 0.69 at every effort under bare `codex exec` without research tools (`fixtures-codex/README.md:44-50`), so its xhigh setting is unvalidated at low. A single definition flattens this to one value.

**4. Only about a quarter of each body is shared.** The word-for-word shared prose is the Input block (`codebase-analyst.md:46-52`, `spec-context-analyst.md:46-52`, `domain-researcher.md:27-33`), the grounding note (`codebase-analyst.md:115` and twins), and the Terminal Deliverable paragraph (`codebase-analyst.md:117-119` and twins, differing in the section-name triple). The rest is lane-specific and shapes artifact quality: `spec-context-analyst.md:58` (Design Concept Q&A log is authoritative and not re-litigated), `:132-135` (propose exact markdown because the autopilot auto-applies edits), `domain-researcher.md:129-137` (official docs outrank blogs in tie-breaks; state library version), `codebase-analyst.md:138-146` (prefer established patterns; report low confidence when no pattern exists, which is the Round 2 escape trigger at `consensus-protocol.md:102-105`). The docs' own test for consolidation, "the same kind of worker with the same instructions" (https://code.claude.com/docs/en/sub-agents#overview), is not met.

**5. The cited precedent does not transfer.** `speckit-pro/agents/sweep-analyst.md:9` restricts tools to six broker calls, `:27-29` has the broker bind the perspective out of band ("Do not supply or guess raw selectors"), `:36-43` gives each perspective one bullet, and `:42-43` strips web access from the domain lane. `speckit-pro/skills/speckit-autopilot/references/phase-execution.md:1744-1766` explains why: the sweep needed a closed allowlist because consensus-synthesizer inherits shell, web, and MCP, and it states that Clarify, Checklist, and Analyze keep the shared analysts unchanged. The consensus analysts have no broker; a folded perspective would ride on untemplated prompt text (the protocol's prompt field is a placeholder at `consensus-protocol.md:203`).

**6. The protocol, synthesizer, and verification are identity-keyed.** Routing: `consensus-protocol.md:82-84` (tag to named agent), `:89-92` (union spawn), `:111-113` (Round 2 spawns "the remaining (3 - N) analysts"), `:286-288` (perspective table), `:296-298` (2/3, 3/3, all-disagree rules count calls), `:324-326` (security spawns all three). Synthesizer: `speckit-pro/agents/consensus-synthesizer.md:83-85` (name which of the three contributed) and `:113-125` (input rows per named analyst with NOT SPAWNED). Verification: 22 fixtures under `tests/speckit-pro/layer7-integration/dispatch-fixtures/` use must_dispatch_to and must_not_dispatch_to on the three names (`02-clarify-multi-category/expected.json`); after a fold, `[codebase]`-only and `[domain]`-only routing become indistinguishable by name. Roster constants: `speckit-pro/speckit_pro_runner/helpers/install.py:37`, `tests/speckit-pro/layer6-efficiency/lib/qualification_corpus.py:17-30` and `:441` (exactly twelve governed roles), `claude_role_corpus.py:55`, `validate-agents.py:35-49`.

**7. domain-researcher has a second dispatch path.** `phase-execution.md:2527` and `:2657`, `speckit-pro/skills/speckit-autopilot/SKILL.md:724`, and `speckit-pro/codex-skills/speckit-autopilot/SKILL.md:949` route Implement-phase research tasks to it, outside consensus. Its Input block (`domain-researcher.md:27-33`) does not declare that mode. This is a keep-three fix, and it also breaks the fold's premise that the three are pure perspectives of one role.

**8. The three-file design produces real consensus dynamics.** `docs/ai/specs/.process/ART-001-workflow.md:369-372`: item 3 escaped Round 1 and resolved 2/3 in Round 2. `ART-002-workflow.md:36-38` and `:563`: one item escalated to 3/3 at Round 2; a checklist item closed 2/3 with dissent logged. `ART-008-workflow.md:1626-1633`: eight items closed in Round 1 with lane-distinct evidence. Each Round 2 escape costs (3 - N) analyst calls plus a second synthesizer call and a serial stage (`consensus-protocol.md:111-113`), so per-lane prompt depth protects the cheap path.

**9. External guidance points the same way.** Anthropic's routing guidance: "optimizing for one kind of input can hurt performance on other inputs" (https://www.anthropic.com/engineering/building-effective-agents#Workflow: Routing) and "add complexity only when it demonstrably improves outcomes" (#Agents). The multi-agent research write-up credits separation of concerns to "distinct tools, prompts, and exploration trajectories" (https://www.anthropic.com/engineering/multi-agent-research-system#Benefits of a multi-agent system) and warns that small lead-agent changes shift subagent behavior unpredictably (#Conclusion). A-HMAD's ablation reports up to 3.5% loss when specialized agents are replaced with identical ones (https://link.springer.com/article/10.1007/s44443-025-00353-3#ablation). None of these A/B one file against three; they corroborate, they do not decide. Two arguments were dropped as weak on both sides: cross-platform parity already carries exemptions (`tests/speckit-pro/layer1-structural/validate-codex-parity.py:47-54`), and all 14 descriptions total 727 words against the 15,000-token budget (https://code.claude.com/docs/en/sub-agents#description).

**10. Measured blast radius of a fold.** Occurrences excluding `dist/`: 596 (codebase-analyst), 505 (spec-context-analyst), 506 (domain-researcher), across 234/207/218 tracked files. Regenerable: `dist/`, installed-cache proofs, docs-site reference pages. Hand-edit: 6 agent files, 16 skill files, 3 TOMLs, `install.py`, L1/L6 constants, 22 L7 fixtures, unit tests, count-parity baselines. Permanently stale: archived `docs/ai` workflow records.

### Rejected option: fold into one `consensus-analyst`

Rejected for six structural reasons, each repo-verified above: (a) `effort` and `memory` are per-definition, so a fold forces one value on three lanes (evidence 1); (b) one name means one memory directory shared across lanes, against policy that forbids persisting external text (evidence 2); (c) Codex low/low/xhigh flattens to one value and `validate-tool-scoping.py:306-312` must be rewritten (evidence 3); (d) the synthesizer input contract and 22 dispatch fixtures are keyed by name (evidence 6); (e) domain-researcher's Implement-phase research dispatch would need a perspective threaded through a non-consensus path (evidence 7); (f) the sweep-analyst precedent is a broker-bound security boundary, not a parametrization pattern (evidence 5). What the fold would have bought: about 24 lines of shared prose deduplicated, roughly 120 fewer description tokens at session start, and a shared system-prompt prefix cacheable only on non-concurrent Round 2 spawns. Those gains are small against per-call totals of 53k to 2.27M tokens (evidence 3).

### Strongest surviving objection and mitigation

**Objection.** The three files are one logical unit with a recurring sync tax. Git history on the three paths shows 15 commits; 12 touched all three (e4d9a358e, c08662d69, 7bc6be1a9, c9176902d, bb01ef287, b95d721f1, 6ec5cea7f, 45147ad15, 02104a404, 7a90cce4b, ab704d644, efba16361), 2 touched two, 1 touched one. The shared prose has already drifted across platforms: the Terminal Deliverable block added in c08662d69 (#301) reached the three Claude bodies and none of the three Codex TOMLs (measured 0/0/0), and the only prose-sync test today covers implement-executor alone (`tests/speckit-pro/unit/test-implementation-notes-record.py:61`, `:293`).

**Mitigation.** Pay the tax with a guard, not a fold. Add a unit test that asserts the shared blocks are byte-identical across the three Claude bodies (modulo the section-name triple) and that the Input bullets are present in each Codex TOML (measured 1/1/1), and record the Codex Terminal Deliverable omission as accepted in that test's docstring. The three partial-touch commits (da9a7c5cd, 51e7609fd, fbc1fdefb) were lane-specific changes, which is the content a fold would have to gate behind a selector. If the guard proves noisy, the follow-up is to move the shared blocks behind a reference file the way `capability-discovery.md` and `grounding.md` are already referenced from the bodies; that is still keep-three.

### Implementation table

| # | File | Change | Guard |
|---|------|--------|-------|
| 1 | `speckit-pro/agents/domain-researcher.md` frontmatter | No change. Do NOT add `memory: local`. | `validate-agents.py:73-77`; `test-role-corpus-governance.py:381-392`; `subagent-memory-policy.md:15` |
| 2 | `speckit-pro/agents/spec-context-analyst.md:68-70` | M3 capability-neutral wording is already applied in the WP1 working tree. No WP6 edit. | Confirm in the WP1 commit |
| 3 | `speckit-pro/agents/domain-researcher.md:27-33` | Add a fourth Input item, "Research Task", for the Implement-phase research dispatch; change "one of three types" to "one of four types" in this file only. | `phase-execution.md:2527`, `:2657`; `SKILL.md:724` |
| 4 | `speckit-pro/codex-agents/domain-researcher.toml:20` | Mirror change 3 in the Codex Input block. | `codex-skills/speckit-autopilot/SKILL.md:949` |
| 5 | `tests/speckit-pro/unit/test-consensus-analyst-shared-prose.py` (new) | Assert the Input bullets, grounding note, and Terminal Deliverable paragraph match across the three Claude bodies; assert Input bullets exist in the three TOMLs; docstring records the Codex Terminal Deliverable omission as accepted. Register in `tests/speckit-pro/suite-manifest.json`. | Pattern: `test-implementation-notes-record.py:61`, `:293` |
| 6 | Layer 6 corpus | Run `python3 tests/speckit-pro/layer6-efficiency/rebaseline-corpus.py` (WP1) after changes 3 and 4, once, after WP4 and WP6 both land. | `qualification_corpus.py:441` |
| 7 | Generated artifacts | `python3 scripts/refresh-release-artifacts.py`; `pnpm --dir docs-site reference:generate`; `python3 tests/speckit-pro/run-all.py`. | CI `artifact-consistency` |
| 8 | Untouched | `consensus-protocol.md:82-84`, `:89-92`, `:111-113`, `:286-288`; `consensus-synthesizer.md:83-85`, `:113-125`; 22 L7 dispatch fixtures; `install.py:37`; `qualification_corpus.py:17-30`; `validate-agents.py:35-49`; Stay-in-your-lane rules at `codebase-analyst.md:148-151`, `spec-context-analyst.md:137-140`, `domain-researcher.md:139-142`; the three Codex `model_reasoning_effort` values. | This record |
| 9 | `effort:` frontmatter | No change in M6. Separate files keep per-role Claude effort expressible; F1 decides the values. | https://code.claude.com/docs/en/sub-agents#frontmatter-fields |
| 10 | Audit report M6 row | Mark "Declined: keep three with fixes" so the WP7 re-audit does not reopen it. | prompt-audit-report.md:70 |

### Resulting roster

Unchanged at 14 Claude definitions (`speckit-pro/agents/`) and 11 Codex TOMLs (`speckit-pro/codex-agents/`, including the Codex-only `autopilot-fast-helper`). gate-validator's removal belongs to WP4, not M6.
