# Native Spec Kit v1.1.0 capabilities the plan stage can adopt

> Status: research complete for ticket #1147 (map #1144). Research only. No plugin behavior changes.
> Snapshot: 2026-10-04. speckit-pro 2.40.0 (main at f7c97c1af). Upstream github/spec-kit tag v1.1.0, commit f1d3a4f8337ebbd3ae22760a9c12e3352b93a175.
> Upstream citations are `path:line` in that tag. speckit-pro citations are `path:line` on main at the snapshot.

## Short answer

Nothing in v1.1.0 gives the plan stage a large speed-up on its own. The plan stage is dominated by consensus waits, serial executors and artifact authoring (prior measurement, below), and none of those are upstream features.

| Capability | Composes today | Verdict for the plan stage |
| --- | --- | --- |
| `lean` preset | Installs cleanly, but its plan command ignores the reviewability plan template and drops hooks, the setup script, `research.md` and `data-model.md` | Do not adopt as shipped. Saves almost no prompt tokens. Not behavior-equivalent (upstream maintainer says so) |
| `specify workflow run` | Runs on Claude Code and Codex through a headless CLI per step, with fan-out, `max_concurrency`, pause and resume (all measured) | Can coexist with ADR 0010 only as a thin inner executor under a runner-owned loop. Adds no stop-policy primitive. Not worth adopting for plan-stage speed |
| Hook dispatch | Orchestrator and upstream command both dispatch hooks by design | Double dispatch is structural. Not observed at runtime, because the canary fixture registers no hooks. Cheap to fix |
| Pin the `specify` CLI | Upstream supports tag pins | Adopt. No speed effect. Removes version drift |
| Prior art (#1401, token-budget, token-economy, schedule) | Optional hooks only | None moves plan-stage time. token-budget adds LLM runs. schedule and token-economy target later stages |

## Baseline this research builds on

Measured in the prior performance digest (private notes, not in the repo), not re-measured here except where marked:

- Baseline Claude Code plan run on a 120-line change: 93.8 min wall, 38.9M tokens, 23 agents, about 94% of tokens are cache reads.
- The three `phase-executor` spawns (specify, plan, tasks) took 13.7 min total (14.6% of wall) and 253,830 `totalTokens` (13% of the 1.96M agent total, which excludes cache reads).
- Consensus waits about 29.7 min. Artifact author 22.6 min. Checklist domains run serially, 8.6 min.
- 2.40.0 smoke on a different fixture: 120.4 min and 64.6M tokens. Not a controlled A/B.

Anything below that says "estimated" is an inference from those numbers. Nothing here was run end to end on a model.

## 1. The `lean` preset

### What it is

- A bundled preset that replaces five core commands: `speckit.specify`, `plan`, `tasks`, `implement`, `constitution` (`presets/lean/preset.yml:15-45`). Each entry is `type: "command"` with `replaces:` and no `strategy`, so each uses the default replace strategy.
- The five files total 116 lines (33, 22, 19, 23, 19) against 1,136 lines for the five core command templates (`templates/commands/{constitution,specify,plan,tasks,implement}.md`: 179, 345, 170, 220, 222). Counted with `wc -l`.
- `presets/lean/README.md:21` says the commands are "self-contained prompts that produce each artifact directly, no separate template files involved."
- The lean plan command (`presets/lean/commands/speckit.plan.md:13-19`) reads `.specify/feature.json`, loads the constitution and `spec.md`, and writes `plan.md`. That is all. It does not run `setup-plan.sh`, does not load any plan template, has no hook sections, and does not create `research.md`, `data-model.md`, `contracts/` or `quickstart.md`.
- The lean specify command (`presets/lean/commands/speckit.specify.md:13`) says "Ask the user for the feature directory path ... Do not proceed until provided."

### Does it compose with the required reviewability preset

Install-time: yes, with no conflict. Presets resolve each file name independently (`docs/reference/presets.md:198`). Lean owns command names. The reviewability preset owns template names (`.specify/presets/speckit-pro-reviewability/preset.yml:16-31`: `spec-template`, `plan-template`, `tasks-template`, all `type: "template"`, all `replaces:`). The two sets do not overlap. In the dogfood registry the reviewability preset has priority 5 (`.specify/presets/.registry:7`) and `specify preset add` defaults to 10 (`docs/reference/presets.md:28`).

Behavior: they do not compose, because lean's replace-strategy plan command never reads the plan template. Strategy by strategy:

| Strategy | What it does here (`docs/reference/presets.md:202`, `src/specify_cli/presets/_resolver.py:735-830`) | Result |
| --- | --- | --- |
| replace (what lean uses) | Top layer wins entirely | Lean plan command wins; reviewability template is resolved but unused |
| prepend, append | Preset text goes before or after lower-priority text | A speckit-pro command layer at higher precedence could append "load plan-template and fill the reviewability sections" onto lean's body. Composition is recursive and a preset layer can be the base (`_resolver.py:766-830`). Read in source only, not run |
| wrap | Replaces `{CORE_TEMPLATE}` with the lower layer | Same idea, more control |

### What the plan stage would lose with stock lean

From the reviewability plan template (`.specify/presets/speckit-pro-reviewability/templates/plan-template.md:38,54-60`) and gate G3 (`speckit-pro/skills/speckit-autopilot/references/gate-validation.md:74-87`):

- The Reviewability Budget line, the Module and Interface Deltas section and the Declared File Operations block that `estimate-reviewable-loc.sh` parses. The estimator degrades to `not_estimated` (template text, line 54 onward). Advisory under ADR 0006, but the signal is gone.
- `research.md` and `data-model.md`. G3 requires `research.md` and, when the spec has entities, `data-model.md` (`gate-validation.md:77-78`). Stock lean fails G3.
- Hook dispatch inside the command. Lean has no hook sections (`grep` of lean commands for hook and `extensions.yml`: no matches). The upstream maintainer says the same: lean "omit[s] some core scripts and hooks, so it is not a behavior-equivalent replacement" (issue #1401, closing comment, 2026-09-24).
- The `before_specify` branch-creating hook (dogfood `.specify/extensions.yml` registers `speckit.git.feature` as a mandatory hook) and the question-free flow. Lean specify asks the user for a directory, which contradicts ADR 0010 (no stops for questions).
- Constitution Check gate evaluation and the "ERROR on unresolved clarification" rules of `templates/commands/plan.md:66-72,161-164`.

### Claude Code and Codex blockers

- Preset commands are written only to the active integration's directory (`docs/reference/presets.md:200`). The dogfood project has both Claude and Codex installed (`.specify/integration.json`), so a lean install reaches only the default host until `specify integration use <key>` rescaffolds. This is a Codex parity risk, not a Claude one.
- `specify preset update` is destructive and has no rollback (`docs/reference/presets.md:34-70`). An upgrade path for a speckit-pro override layer needs care.
- Lean requires `speckit_version >=0.6.0` (`preset.yml:12-13`). Not a blocker.

### Expected effect

Estimated, not measured.

- Prompt tokens: the core plan command is about 1,635 tokens by the author's count in upstream issue #2943 (o200k tokenizer, third-party measurement). Lean plan is 19 lines, so the saving is roughly 1.4K tokens per plan invocation. Against 38.9M tokens that is noise.
- Wall clock: the only lever is output. The three phase-executor spawns cost 13.7 min. If lean removed half of that by skipping research, data model, contracts and quickstart, the ceiling is about 7 min of 93.8 (7%). That ceiling is also what breaks G3 and starves the checklist, analyze and artifact-author steps that read those files. A realistic gain is lower.
- A third-party extension reports a 46.8% token cut for lean on a toy "add greeting feature" scenario (`token-analyzer` v0.1.0 README, lines 7-18 and 120-131). Single run, old model, no method published beyond the README. Treat it as anecdote. It does not transfer to a consensus-dominated run.

Recommendation: do not install stock lean. If a smaller prompt is wanted, write a speckit-pro command layer with `append` or `wrap` over core, and canary it. That is a separate ticket.

## 2. `specify workflow run`

### What it is

- Engine commands: `run`, `resume`, `status`, `--json` output (`docs/reference/workflows.md:5-88`). Step types: command, prompt, shell, init, slot, gate, if, switch, while, do-while, fan-out, fan-in (`workflows.md:566-581`).
- State lives under `.specify/workflows/runs/<run_id>/` as `state.json`, `inputs.json`, `log.jsonl` (`workflows.md:835-843`). Run states: created, running, completed, paused, failed, aborted (`workflows.md:88`).
- Bundled workflow `speckit`: specify, review-spec gate, plan, review-plan gate, tasks, implement (`workflows/speckit/workflow.yml:39-70`). Its `requires.integrations.any` list omits Codex, but the file calls the list "an advisory, non-exhaustive compatibility hint ... NOT a closed set" (`workflow.yml:14-21`).
- `max_concurrency` is documented only in `workflows/README.md:290-299` (its prose still says "sequential"), not in `docs/reference/workflows.md`. Added in 0.12.2 (`CHANGELOG.md:1094`).

### How a command step runs (read in source, then measured)

- `command` steps shell out to the host CLI: `CommandStep._try_dispatch` finds the integration, requires the CLI on PATH, and calls `dispatch_command` (`src/specify_cli/workflows/step/command/__init__.py:201-268`). By default it streams to the terminal with no timeout and returns only `exit_code`; stdout and stderr are empty strings (`src/specify_cli/integrations/base.py:461-480`; docstring `command/__init__.py:21-26`).
- Claude Code: `claude -p "<prompt>"` (`base.py:1657-1672`, skills integrations). Codex: `codex exec "<prompt>"` (`src/specify_cli/integrations/codex/__init__.py:47-67`).
- Operators add flags only through `SPECKIT_INTEGRATION_<KEY>_EXTRA_ARGS` and override the binary with `SPECKIT_INTEGRATION_<KEY>_EXECUTABLE` (`base.py:293-345`). There is no built-in permission or sandbox flag for either host.

Measured with the v1.1.0 CLI built from the tag (stub executables, no model calls, scratch directory outside the repo):

- Claude step argv: `-p "/speckit-plan SPEC-001 plan stage" --permission-mode acceptEdits` (the last two tokens came from the EXTRA_ARGS env var). Stdin was not a TTY.
- Codex step argv: `exec "$speckit-plan SPEC-001 plan stage"`.
- A shell-only workflow with `fan-out` at `max_concurrency: 3` over three 1-second steps started all three within 4 ms and finished in about 1.03 s total. The `fan-in` completed.
- A `gate` step with no TTY paused the run (`status: paused`, `gate` object in `workflow status --json`). `workflow resume <id> --input verdict=approve` completed it. This matches `gate/__init__.py:174-175` and `workflows.md:845-901`.
- Fan-out runs the same step template per item on a thread pool (`src/specify_cli/workflows/engine.py:1471-1658`). Fan-in only aggregates already-finished outputs (`step/fan_in/__init__.py:11-18`). The shell step default timeout is 300 s (`step/shell/__init__.py:36`).

### Can it host the plan stage

Mechanically yes on both hosts, for the `phase-executor` legs: specify, plan, tasks, and the checklist domains as a fan-out. Not confirmed: whether `codex exec` resolves a `$speckit-plan` skill token in the prompt (needs a real model run), and whether an unapproved `claude -p` child can use Bash, Write, Agent and MCP tools without a permission flag (needs a real run).

The consensus protocol, clarify answering and gate repair loops are orchestrator judgment, not command steps. They would need `prompt` steps or stay in an outer session. The engine does not remove that work.

### Can a runner-owned stop policy (ADR 0010) coexist with it

Yes, but only if the runner stays the outer owner and the engine is an inner executor. The engine has no concept of ADR 0010's closed registry (`speckit-pro/speckit_pro_runner/stop_policy.py:25-44`), terminal states or harm halts. Conditions:

1. **The runner decides when the run ends, never the engine.** Engine statuses `paused`, `failed` and `aborted` are stops with no registered reason. Under ADR 0010 each is an `unregistered_stop` that climbs the retry ladder. The runner would call `specify workflow run --json`, read the status, and treat `workflow resume` as the retry rung (`workflows.md:59-76` says resume re-runs the blocked step).
2. **No unbound gates.** A `gate` step without a supplied verdict pauses the process (`gate/__init__.py:174-175`). Either omit gates or bind `verdict_input` to a runner-supplied value (`workflows.md:845-901`). Upstream's bundled `review-spec` and `review-plan` gates are exactly the human stops ADR 0010 removes. Upstream's own `on_reject: abort` would end the run outside the registry.
3. **Stop hook scoping.** ADR 0010 puts a Stop hook on both hosts that asks the runner whether the run may end. Each engine step is a separate `claude -p` or `codex exec` child, and every child's turn end would ask that question while the run is not terminal. The runner would need a step-scoped answer ("a child finished; the owner is the engine step"), or the hook would block every child. The existing plugin Stop hook already blocks turn end when commits are unpushed during an active run (`speckit-pro/hooks/hooks.json:59-68`, `speckit-pro/scripts/workflow-guard-hook.py:283-298`); it would fire in each child too. Whether plugin hooks load inside `claude -p` children is documented ambiguously (see Unconfirmed). Codex hooks need persisted trust, or `--dangerously-bypass-hook-trust` for one invocation (Codex hooks documentation, and the flag is present in local `codex exec --help`, codex-cli 0.160.0).
4. **Single writer.** `max_concurrency > 1` starts concurrent children. The runner ledger lock fails closed on contention (`speckit_pro_runner/execution_control.py:193-203`), and ADR 0010 maps a live owner to a `concurrent_writer` harm halt. Fan-out items that call the runner would trip it. Keep runner-calling steps at concurrency 1, or give the runner a multi-writer rule first. Checklist remediation also edits shared `spec.md` and `plan.md`, so domains cannot safely write in parallel without an ownership rule.
5. **Two state stores.** Engine state (`state.json`) and the runner ledger plus `autopilot-state.json` would both claim progress. ADR 0010 makes the runner's decisions list "the single source". The engine state must be a cache that the runner reconciles, not an authority.
6. **Output channel.** A command step returns only an exit code (`base.py:461-480`). The runner must read artifacts and its own ledger, not step output. Shell steps that call the runner need a `timeout` above 300 s.

Net: coexistence is possible, but the engine adds no stop-policy primitive and adds a second ledger to reconcile. It does not meet ADR 0010 on its own.

### Expected effect

Estimated, not measured.

- Parallel checklist domains: 8.6 min serial (11.8 min in the smoke) could fall toward the longest single domain, about 4.8 min. Saves roughly 4 to 7 min if remediation edits are serialized. The same gain is available without the engine by launching executors as background agents; the baseline shows the orchestrator launching foreground executors one per turn.
- Fresh child per step would shrink the orchestrator's 171K median context, but that context also carries consensus and gate state. Effect unknown.
- Each child pays its own startup, skill load and cache write. Net token effect unknown.

Recommendation: do not adopt for plan-stage speed. Revisit only if a later ADR wants one sequencer shared across hosts, and then spike the runner-outer, engine-inner shape with the six conditions above.

## 3. Hook dispatch: does a hook run twice

### What upstream does

- Hooks are prose inside each command template. `templates/commands/plan.md:25-58` (before) and `:74-106` (after) tell the running agent to read `.specify/extensions.yml`, filter, and for `optional: false` hooks emit `EXECUTE_COMMAND:` and actually invoke them. The installed skill in this repo carries the same text (`.claude/skills/speckit-plan/SKILL.md:25-56,76-...`).
- The engine does not fire hooks: no hook handling in `src/specify_cli/workflows/`. `auto_execute_hooks` is "currently reserved and is not consulted" (`docs/reference/extensions.md:309`). Hooks surface in YAML order, not by priority (`extensions.md:319`). Conditions are not evaluated by command templates (`extensions.md:322`).

### What speckit-pro does

- The orchestrator loop checks `before_<phase>` hooks before each phase and `after_<phase>` after, runs accepted ones with `Skill()` and says "skip duplicates" (`speckit-pro/skills/speckit-autopilot/references/phase-execution.md:389-390,416-417,4787-4853`; the SKILL.md loop repeats it at lines 1104-1115).
- The `phase-executor` then runs the upstream command through the Skill tool, "exactly as specified", and must "follow only the loaded command's instructions" (`speckit-pro/agents/phase-executor.md:36-50`). The loaded command contains the hook sections above, so the subagent dispatches them too.
- The only dedupe is the sentence "skip duplicates". There is no shared marker or ledger entry for a dispatched hook.

So for any phase run through the upstream command, a registered hook is eligible for dispatch twice: once by the orchestrator, once by the subagent. `clarify` is the exception: the clarify executor never runs the upstream command (`phase-execution.md:549-560`), so only the orchestrator can fire clarify hooks.

Dogfood configuration (`.specify/extensions.yml`): `before_plan` has `speckit.git.commit`; `after_plan` has `speckit.speckit-utils.validate` and `speckit.git.commit`. That is 3 hook commands per plan phase and 6 if doubled. Each is a skill invocation, which is an LLM turn. The git auto-commit script is disabled by default (`.specify/extensions/git/git-config.yml`, `default: false`), so the duplicate commit is a no-op, but the validate hook does real work.

### Runtime evidence

Measured on the two Claude plan transcripts (private canary runs, baseline and 2.40.0 smoke):

- The fixture has no `.specify/extensions.yml`, so no hook fired in either run.
- The main thread issued 0 tool calls that read `extensions.yml`, the extension registry or mention hooks (baseline and smoke).
- Subagents issued 6 such calls in the baseline and 8 in the smoke. Each was a cheap `ls` or `cat` bundled with the command's setup script, and each reported "no hooks ran."

Conclusion: double dispatch is structural but unobserved. It cannot be shown or ruled out until a canary variant registers at least one non-destructive hook. Orchestrator detection goes through the `detect-presets` helper (`speckit_pro_runner/helpers/read_only.py:1904-1915`), not a transcript-visible read.

### Fix options (not decisions)

- Single dispatcher in the subagent: drop the orchestrator's hook steps for phases that run the upstream command. Keep them for clarify.
- Single dispatcher in the orchestrator: tell the executor to skip hook sections. Upstream text has no skip switch, and the executor rule "do not modify the prompt" blocks a silent change.
- Stock lean removes hooks from specify, plan and tasks, which would make the orchestrator the only dispatcher by accident. Not a reason to adopt lean.

Expected effect: removes up to 3 redundant skill turns per plan phase when hooks are registered. Estimated at under 1 minute per phase, unmeasured. No effect on projects with no hooks.

## 4. Pinning the `specify` CLI

Today:

- The install path is `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git` with no ref (`speckit-pro/skills/speckit-install/SKILL.md:85-90`, `speckit-pro/README.md:67`, `speckit-pro/skills/speckit-scaffold-spec/SKILL.md:267`, `speckit-pro/skills/speckit-upgrade/SKILL.md:118`). That tracks the default branch.
- The runner reports "version not checked" (`speckit-pro/speckit_pro_runner/helpers/read_only.py:1444`).
- Drift is real. The dogfood project files record 1.0.1 (`.specify/init-options.json:8`, `.specify/integration.json:2`) while a developer machine measured CLI 1.0.12 on 2026-10-04. PyPI's latest was 1.0.13 and had no 1.1.0 at query time (PyPI JSON API, 2026-10-04).
- CI already pins by commit with a tag comment, now three minors stale: `.github/workflows/container-preflight.yml:21` (`@b2314680fce898e0a9151b37ad2535d810c93eef # v0.8.13`).

Upstream support:

- Tag pin from source, called the recommended route: `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z` (`docs/installation.md:18-29`; `docs/upgrade.md:13`).
- PyPI pin: `uv tool install specify-cli==X.Y.Z` (`docs/installation.md:53`, `docs/install/pypi.md:25`). Version 1.1.0 was not on PyPI when checked, so a 1.1.0 pin has to use the git tag today.
- `specify self upgrade --tag vX.Y.Z` pins a tag; branch names and hash refs are rejected (`docs/upgrade.md:12,42-44`).
- Projects record the CLI version and presets can declare `requires.speckit_version` (`presets/lean/preset.yml:12-13`; reviewability preset requires `>=0.5.1`).

Notes:

- `v1.1.0` is an annotated tag. The shallow clone warned that the tag object `9c36536645f1346deed9362378df0d24bbb6f51c` is not a commit; it dereferences to f1d3a4f. A tag can be moved. A commit SHA cannot. Use the tag for `self upgrade`, and the SHA in `uv tool install --from git+...@<sha>` where immutability matters (as CI already does).
- Both hosts share one CLI, so there is no Claude or Codex split. The Codex and Claude skill files come from `specify init` and `integration` commands, so a pin also pins the generated skill text (including the hook sections in Q3).

Blockers: none technical. Work needed: a pinned-version constant, install and upgrade text, a version check in `check_prerequisites` (today it only checks presence), and recording the CLI version in canary receipts (not confirmed whether receipts record it).

Expected effect: none on time or tokens. It removes a variable from every canary comparison. Directly relevant, because the 2.40.0 vs baseline comparison already mixes fixture versions.

## 5. Prior art

### Upstream issue #1401 (token optimization)

- Opened 2025-12-29, closed 2026-09-24. Reported commands cost about 18.6k tokens in context on every session (plan command listed at 690 tokens).
- The maintainer's replies (2026-08-31 and 2026-09-24) say skills mode (default for Claude, Codex and Copilot) loads only skill metadata until invoked, so the standing cost no longer applies. The remaining costs are per-invocation instructions and artifacts re-read by later phases. They asked for measurements of three categories: skill-discovery metadata per session, instructions per invocation, artifacts re-read per phase.
- On lean, same closing comment: it "shortens five core workflows when invoked", does not reduce standing cost, and "omit[s] some core scripts and hooks, so it is not a behavior-equivalent replacement".
- Related: issue #2943 (compress command templates about 23%, closed 2026-06-16) was redirected by the maintainer to a community preset. The author published one (`command-density`, pointed to in #2943 comment of 2026-06-16; not read here, not evaluated).
- What it means here: speckit-pro already runs in skills mode, so #1401's headline cost does not apply. Our cost is artifacts and subagent re-reads, which the digest measured (spec.md read 21 times, four reference files re-read per executor).

### Community extensions, pinned

All four are `verified: false` in `extensions/catalog.community.json` (catalog updated 2026-10-02). I cloned each tag and read the manifest, commands and README.

| Extension | Pin | Hooks | Plan-stage fit |
| --- | --- | --- | --- |
| `token-budget` 1.0.1 (tinesoft/spec-kit-token-budget) | tag v1.0.1, commit f0ee9744fc8f9d925daccb82d6c16df59f9af3b5 | optional `after_specify`, `after_plan`, `after_tasks` compact; `before_plan`, `before_tasks`, `before_implement` scope (`extension.yml:63-98`) | Rewrites artifacts in place and keeps `<file>.full.md` backups (`commands/compact.md:1-50`). The `aggressive` level drops Rationale and Alternatives sections (`token-budget-config.template.yml:9-12`). Each hook is an extra LLM run inside the plan stage. Savings land downstream (tasks, implement). The README's -50% example is labeled "real numbers from a small SDD project" with no method (`README.md:90-97`). Also leaves `.full.md` files in `specs/`, which G3 and the artifact author would see |
| `token-economy` 1.0.0 (formin/spec-kit-token-economy) | tag v1.0.0, commit f536e567d28679204ab99c729dc7d9ff0ffe908b | optional `after_tasks` audit, `after_implement` report only (`extension.yml:46-56`) | No plan-stage hook that saves time. Reporting and routing, built on optional external tools (rtk, headroom, token-router, ollama). Reports "measured" savings only for those tools |
| `schedule` 0.7.4 (jfranc38/spec-kit-schedule) | tag v0.7.4, commit d3b9058695e82b552c8b98f77e2b78862153151e | optional `after_tasks`, `after_converge` (`extension.yml:47-58`) | Implement-stage tool: turns `tasks.md` into parallel subagent rounds (CP-SAT) and runs them. Needs Python `>=3.10,<3.13` and a private env bootstrap of about a minute on first run (`README.md:22-24`, `extension.yml:16-21`). The plan-stage `after_tasks` hook would only add a run. Overlaps speckit-pro's own `task_partition.py` |
| `token-analyzer` 0.1.0 (coderandhiker/spec-kit-token-analyzer), extra | tag v0.1.0, commit d55d678564fb7ec7c303f691b25bf4eefe3bb66d | optional `after_specify`, `after_plan`, `after_tasks`, `after_implement` baseline capture | Measurement helper. Token counts come from the agent and a chars/4 heuristic, not provider usage. Not better than the transcript receipts we already have |

Nobody in this set measured a consensus-heavy, multi-agent run. All hooks are `optional: true`, so under speckit-pro's autopilot rule (auto-accept eligible optional hooks, `phase-execution.md:4845-4851`) they would fire automatically and add runs.

Expected effect on plan-stage time or tokens: token-budget, token-economy, token-analyzer and schedule are estimated to add time during the plan stage (extra LLM runs) and to save tokens only in later stages. No measurement exists for any of them against speckit-pro.

## Summary table

| # | Question | Composes today | Claude Code blocker | Codex blocker | Plan-stage effect |
| --- | --- | --- | --- | --- | --- |
| 1 | lean preset | Install yes; behavior no | Drops reviewability template, hooks, `research.md`, `data-model.md`; G3 fails; specify asks the user | Same, plus preset commands reach only the active integration (`presets.md:200`) | Estimated: about 1.4K tokens per plan call; wall ceiling about 7 min, realistic less |
| 2 | `workflow run` | Runs on both hosts (measured with stubs) | Permission flags only via env var; Stop hook scoping; ledger lock vs concurrency | `$skill` token in `codex exec` unconfirmed; hook trust; same ledger issues | Estimated: parallel checklist domains 4 to 7 min, available without the engine |
| 3 | Hook double dispatch | Structural, unobserved | Needs a canary variant with a registered hook | Not profiled | Estimated: up to 3 redundant skill turns per phase when hooks exist |
| 4 | Pin CLI | Supported upstream | None | None | None; removes drift |
| 5 | Prior art | Optional hooks only | Extra runs in plan stage | Same | Estimated: no plan-stage saving |

## Unconfirmed, and where I looked

- **`codex exec` resolving `$speckit-plan`.** Looked at: the Codex integration source (`codex/__init__.py`) and the measured argv. A real model run would be needed. Not done.
- **Headless `claude -p` tool permissions for a full plan stage.** Looked at: the integration source and docs fetch. No full run was made. The docs page summary for hooks in print mode was ambiguous (Stop hooks "not specifically disabled"). Plugin hook loading in `claude -p` children is therefore unconfirmed.
- **Codex Stop hook under `codex exec`.** Looked at: Codex hooks documentation. It states trust requirements and the bypass flag but says nothing explicit about `codex exec` and Stop. Unconfirmed.
- **Hook double dispatch at runtime.** Looked at: both Claude canary plan transcripts (no hooks registered) and the Codex baseline (transcript file not present in the cache at check time). Needs a canary variant with a registered hook.
- **Lean timing.** No run with lean was made. The 7-minute ceiling is arithmetic on the prior digest, not a measurement.
- **Quality effect of lean or token-budget.** Not measured. The prior digest already says canary variants are needed before any speed-up is trusted.
- **How a fresh project gets the reviewability preset.** The README names `ensure-reviewability-preset.sh`, but I found no such script under `speckit-pro/scripts/` or the runner. Same gap the prior digest flagged. Unconfirmed.
- **Whether canary receipts record the `specify` version.** Receipts are private and I did not inspect their schema for this.
- **Community preset `command-density`.** Named in #2943 only. Not read.
- **Third-party extension claims** (token-budget -50%, token-analyzer -46.8%, schedule 2.6x). Taken from READMEs. Not reproduced.
- **PyPI availability of 1.1.0.** Checked once on 2026-10-04 and it was absent. This can change.

## Sources

Upstream, tag v1.1.0 (`https://github.com/github/spec-kit/blob/v1.1.0/<path>`): `presets/lean/`, `docs/reference/{presets,workflows,extensions,artifacts,bundles,agentic-sdd}.md`, `docs/concepts/complex-features.md`, `docs/quickstart.md`, `docs/installation.md`, `docs/upgrade.md`, `docs/install/pypi.md`, `workflows/speckit/workflow.yml`, `workflows/README.md`, `templates/commands/plan.md`, `src/specify_cli/workflows/` (engine, steps), `src/specify_cli/integrations/{base.py,codex,claude}`, `src/specify_cli/presets/_resolver.py`, `CHANGELOG.md`, `extensions/catalog.community.json`. Issues: github/spec-kit #1401, #2687, #2943.

Community extensions at pinned commits: tinesoft/spec-kit-token-budget v1.0.1, formin/spec-kit-token-economy v1.0.0, jfranc38/spec-kit-schedule v0.7.4, coderandhiker/spec-kit-token-analyzer v0.1.0.

This repo: `docs/adr/0010-stop-policy-enforcement.md`, `.specify/presets/speckit-pro-reviewability/`, `.specify/extensions.yml`, `.specify/init-options.json`, `speckit-pro/skills/speckit-autopilot/references/{phase-execution,gate-validation}.md`, `speckit-pro/agents/phase-executor.md`, `speckit-pro/hooks/hooks.json`, `speckit-pro/scripts/workflow-guard-hook.py`, `speckit-pro/speckit_pro_runner/{stop_policy,execution_control}.py`, `speckit-pro/speckit_pro_runner/helpers/read_only.py`, `speckit-pro/skills/speckit-install/SKILL.md`, `.github/workflows/container-preflight.yml`.
